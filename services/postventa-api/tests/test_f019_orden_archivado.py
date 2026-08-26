# services/postventa-api/tests/test_f019_orden_archivado.py
"""El corazón de F-019: no se sube nada de un parte que no conste (R19–R24).

## Qué se arregla aquí, y por qué no bastaban tres endpoints

El 2026-08-25, verificando T18 de F-010 contra el entorno real, `POST
/api/archivar` **subió el PDF a SharePoint y después falló** al escribir la
traza: `postventa.archivos.hash_parte` tiene una clave ajena contra
`postventa.partes` y nada había insertado el parte. Resultado: un fichero en
la biblioteca de Posventa del que el sistema no sabe nada. Ni se puede saber
si está archivado, ni la idempotencia de F-006 lo ve, ni el día del cierre en
Sigrid nadie lo relaciona con su incidencia.

Tres endpoints nuevos no matan ese defecto: sólo lo evitan **mientras el
llamante haga las cosas en orden**. Vuelve en cuanto alguien llame a
`/api/archivar` por su cuenta, que es exactamente lo que se hizo aquel día.

## El mecanismo, en una frase

`paso_archivo` escribe la traza del archivo en estado `pendiente` **antes** de
llamar al puerto de archivo. Si el parte no consta en `postventa.partes`, esa
escritura no puede hacerse: la rechaza **la misma clave ajena** que hoy
produce el defecto. No se añade una comprobación paralela que pueda divergir
de la restricción real; se usa la restricción, y así falla **antes** de subir
en vez de después.

## Dónde está la aserción que importa

En `registro`: una lista **compartida** por el doble del archivador y el del
repositorio (`tests/utiles_sharepoint.py`). Lo que R19 exige no es que cada
doble recibiera lo suyo, es **el orden entre los dos**, y eso no se puede
afirmar mirándolos por separado.

**Ni una subida, ni una conexión, ni un dato real.**
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import azure.functions as func
import pytest
from application.pipelines.paso_archivo import AVISO_YA_ARCHIVADO, paso_archivo
from domain.models.errores import (
    ArchivoFallido,
    ArchivoSinTraza,
    PersistenciaNoDisponible,
    ReferenciaNoConsta,
)
from domain.models.persistencia import EstadoArchivo, TrazaArchivo

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
)

AHORA = datetime(2026, 8, 26, 9, 30, tzinfo=UTC)

CARPETA_ESPERADA = "Postventa/0677"
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"

#: Lo que la traza previa apunta en el registro compartido.
TRAZA_PREVIA = "repositorio.guardar_archivo(pendiente)"

#: La primera cosa que se le pide al archivador en el camino feliz.
PRIMER_TOQUE_AL_ARCHIVADOR = "archivador.asegurar_carpeta"

_FRONTERA = "frontera-sintetica-de-test-f019"

PDF_DE_MENTIRA = b"%PDF-1.4 de mentira"

#: Los campos del formulario de un parte apto, todos **inventados**.
FORMULARIO_APTO = (
    ("hash", "9f2b0011aabb"),
    ("codigo_obra", "0677"),
    ("numero_incidencia", "RS26.08/0123"),
    ("veredicto", "apto"),
    ("destino", "archivo_y_cierre"),
)


def _dobles(**extra):
    """El archivador y el repositorio, **compartiendo el mismo registro**."""
    registro: list[str] = []
    archivador = ArchivoPortFalso(registro=registro, **extra.pop("archivador", {}))
    repositorio = RepositorioFalso(registro=registro, **extra.pop("repositorio", {}))
    return archivador, repositorio, registro


def _archivar(ctx, archivador, repositorio, **extra):
    """El paso con la carpeta base y la hora de siempre."""
    return paso_archivo(
        ctx,
        archivador,
        repositorio,
        carpeta_base=CARPETA_BASE,
        ahora=AHORA,
        **extra,
    )


# --------------------------------------------------------------------------
# R19 · La traza previa, antes de tocar el archivador
# --------------------------------------------------------------------------


def test_f019_r19_la_traza_previa_se_escribe_antes_de_tocar_el_archivador():
    """R19 · **el requisito de la feature**, escrito como orden observable.

    En el camino feliz `guardar_archivo` se llama **dos** veces, la primera en
    `pendiente`, y esa primera va **antes** de la primera llamada al
    archivador. Si el orden se invirtiera —o si la traza previa desapareciera—
    volvería el fichero subido sin constancia.
    """
    archivador, repositorio, registro = _dobles()

    _archivar(contexto_apto(), archivador, repositorio)

    assert repositorio.llamadas_guardar_archivo == 2
    assert registro.index(TRAZA_PREVIA) < registro.index(PRIMER_TOQUE_AL_ARCHIVADOR)
    assert registro[0] == TRAZA_PREVIA


def test_f019_r19_las_dos_trazas_van_en_orden_pendiente_luego_archivado():
    """R19 + R22 · `pendiente` primero, `archivado` al final. Y sólo esas dos.

    No es lo mismo que contar llamadas: una implementación que escribiera dos
    veces `archivado` también daría dos, y no garantizaría nada.
    """
    archivador, repositorio, _ = _dobles()

    _archivar(contexto_apto(), archivador, repositorio)

    assert repositorio.estados == ["pendiente", "archivado"]


def test_f019_r19_la_traza_previa_lleva_el_nombre_y_la_carpeta_que_se_van_a_usar():
    """R19 · la fila `pendiente` describe **lo que se va a intentar**.

    Sin nombre ni carpeta, una traza que se quede en `pendiente` —porque el
    proceso se cayó entre medias— no dice dónde había que mirar.
    """
    archivador, repositorio, _ = _dobles()

    _archivar(contexto_apto(), archivador, repositorio)
    previa = repositorio.archivos[0]

    assert previa.estado == EstadoArchivo.PENDIENTE
    assert previa.nombre_fichero == NOMBRE_ESPERADO
    assert previa.carpeta == CARPETA_ESPERADA
    assert previa.hash_parte == contexto_apto().parte.hash


def test_f019_r19_la_traza_previa_no_lleva_fecha_de_archivado():
    """R19 · todavía no se ha archivado nada, así que no hay cuándo.

    Una fecha puesta «por si acaso» convertiría la fila en una mentira: diría
    que el parte se archivó a una hora en la que ni se había llamado al
    proveedor.
    """
    archivador, repositorio, _ = _dobles()

    _archivar(contexto_apto(), archivador, repositorio)

    assert repositorio.archivos[0].archivado_at_utc is None
    assert repositorio.archivos[0].web_url is None


# --------------------------------------------------------------------------
# R20 · Si el parte no consta, no se sube nada
# --------------------------------------------------------------------------


def test_f019_r20_si_el_parte_no_consta_el_archivador_no_recibe_nada():
    """R20 · **ni carpeta, ni búsqueda, ni subida**. Cero llamadas.

    Es la mitad que de verdad importa del requisito: el 409 sin esto sería un
    mensaje bonito encima del mismo fichero huérfano.
    """
    archivador, repositorio, registro = _dobles(
        repositorio={"fallo": ReferenciaNoConsta("el parte no consta guardado")}
    )

    with pytest.raises(ReferenciaNoConsta):
        _archivar(contexto_apto(), archivador, repositorio)

    assert archivador.llamadas == []
    assert archivador.biblioteca.subidas == 0
    assert archivador.biblioteca.carpetas == set()
    assert registro == [TRAZA_PREVIA]


def test_f019_r21_si_la_base_no_responde_tampoco_se_sube_nada():
    """R21 · el otro fallo de la traza previa, con el mismo efecto.

    Se comprueba aparte de R20 porque el borde los traduce a códigos
    **distintos** —409 y 503— y esas dos respuestas llevan a acciones
    opuestas: guardar el parte, o esperar y reintentar.
    """
    archivador, repositorio, registro = _dobles(
        repositorio={"fallo": PersistenciaNoDisponible("corte inventado")}
    )

    with pytest.raises(PersistenciaNoDisponible):
        _archivar(contexto_apto(), archivador, repositorio)

    assert archivador.llamadas == []
    assert registro == [TRAZA_PREVIA]


# --------------------------------------------------------------------------
# R22 · Lo que F-006 ya hacía, que **no cambia**
# --------------------------------------------------------------------------


def test_f019_r22_la_traza_final_de_exito_sigue_completa():
    """R22 · la traza previa **precede** a la de F-006; no la sustituye.

    Si la previa se quedara como única fila, el parte constaría para siempre
    en `pendiente` y la idempotencia de F-006 dejaría de cortar los reintentos.
    """
    archivador, repositorio, _ = _dobles()

    ctx = _archivar(contexto_apto(), archivador, repositorio)
    final = repositorio.ultima_traza

    assert final is ctx.archivo
    assert final.estado == EstadoArchivo.ARCHIVADO
    assert final.archivado_at_utc == AHORA
    assert final.web_url.startswith("https://")
    assert final.item_id == "item-0001"


def test_f019_r22_un_fallo_del_proveedor_deja_pendiente_y_luego_error():
    """R22 · la traza de error de F-006 sigue escribiéndose, **después**.

    El estado final tiene que ser `error` y no `pendiente`: `pendiente` no
    dice por qué no salió, y el motivo es lo que evita que alguien reintente a
    ciegas.
    """
    archivador, repositorio, _ = _dobles(
        archivador={"fallo": ArchivoFallido("el proveedor no respondió")}
    )

    with pytest.raises(ArchivoFallido):
        _archivar(contexto_apto(), archivador, repositorio)

    assert repositorio.estados == ["pendiente", "error"]
    assert repositorio.ultima_traza.motivo


def test_f019_r22_el_500_de_archivo_sin_traza_sigue_existiendo():
    """R22 · el fichero arriba y la traza final imposible: sigue siendo 500.

    Pasa a ser casi imposible —cuando se llega aquí la fila ya existe, así que
    el `INSERT ... ON CONFLICT` final no puede violar ninguna clave ajena—,
    pero **no se retira**: sigue siendo la única forma honesta de contar que
    el PDF sí se subió. Sólo lo levantaría una caída de la base **entre** la
    traza previa y la final.
    """
    archivador, repositorio, _ = _dobles(
        repositorio={"fallos": {2: PersistenciaNoDisponible("caída entre medias")}}
    )

    with pytest.raises(ArchivoSinTraza):
        _archivar(contexto_apto(), archivador, repositorio)

    assert archivador.biblioteca.subidas == 1


# --------------------------------------------------------------------------
# R24 · La idempotencia va ANTES que la traza previa
# --------------------------------------------------------------------------


def test_f019_r24_con_el_parte_ya_archivado_no_se_escribe_la_traza_previa():
    """R24 · escribirla degradaría a `pendiente` un parte ya archivado.

    Y eso no es cosmético: `pendiente` no corta el reintento (R14 de F-006),
    así que el siguiente intento volvería a subir el fichero. La capa barata
    de idempotencia tiene que ir **antes** que la escritura previa.
    """
    archivador, repositorio, registro = _dobles()
    ctx_entrada = contexto_apto()
    ya_archivada = TrazaArchivo(
        hash_parte=ctx_entrada.parte.hash,
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=NOMBRE_ESPERADO,
        carpeta=CARPETA_ESPERADA,
    )

    ctx = _archivar(
        ctx_entrada, archivador, repositorio, traza_previa=ya_archivada
    )

    assert registro == []
    assert repositorio.llamadas_guardar_archivo == 0
    assert archivador.llamadas == []
    assert AVISO_YA_ARCHIVADO in ctx.avisos


@pytest.mark.parametrize("estado", (EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR))
def test_f019_r24_una_traza_pendiente_o_de_error_si_deja_reintentar(estado):
    """R24 · sólo `archivado` corta, y eso no lo cambia F-019.

    Es lo que permite reintentar después de un fallo. Si la traza previa en
    `pendiente` empezara a cortar, el primer intento fallido dejaría el parte
    atascado para siempre.
    """
    archivador, repositorio, _ = _dobles()
    ctx_entrada = contexto_apto()
    previa = TrazaArchivo(hash_parte=ctx_entrada.parte.hash, estado=estado)

    _archivar(ctx_entrada, archivador, repositorio, traza_previa=previa)

    assert repositorio.estados == ["pendiente", "archivado"]
    assert archivador.biblioteca.subidas == 1


def test_f019_r19_un_parte_no_apto_no_escribe_ni_la_traza_previa():
    """R19 + R17 de F-006 · la puerta de aptitud sigue siendo la primera.

    Un parte que F-004 no declaró apto no tiene que dejar rastro de archivo:
    una fila `pendiente` diría que se intentó archivarlo, y no se intentó.
    """
    from domain.models.errores import ParteNoApto

    from tests.utiles_sharepoint import contexto_no_apto

    archivador, repositorio, registro = _dobles()

    with pytest.raises(ParteNoApto):
        _archivar(
            contexto_no_apto(observaciones="algo escrito a mano"),
            archivador,
            repositorio,
        )

    assert registro == []
    assert repositorio.archivos == []


# ==========================================================================
# El borde: qué código HTTP sale de cada uno de estos casos
# ==========================================================================


def _peticion(campos: Sequence[tuple[str, str]] = FORMULARIO_APTO):
    """Petición `multipart/form-data` de `POST /api/archivar`."""
    cuerpo = (
        f"--{_FRONTERA}\r\n"
        f'Content-Disposition: form-data; name="fichero"; '
        f'filename="parte.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + PDF_DE_MENTIRA + b"\r\n"
    for nombre, valor in campos:
        cuerpo += (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'
        ).encode()
    cuerpo += f"--{_FRONTERA}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/archivar",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _con_dobles(monkeypatch, archivador, repositorio) -> None:
    import function_app
    from interface_adapters.api.archivar import archivar_parte

    def envoltura(contenido: bytes, **datos):
        return archivar_parte(
            contenido, archivador=archivador, repositorio=repositorio, **datos
        )

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)


def _json(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def test_f019_r20_el_borde_responde_409_diciendo_que_hay_que_guardar_el_parte(
    monkeypatch,
):
    """R20 · **409**, y el mensaje dice qué hacer: `POST /api/parte` primero.

    No es un 503. Un 503 promete que reintentar puede funcionar, y aquí
    reintentar no arregla nada por mucho que se insista: fue exactamente la
    lectura equivocada que costó media hora el 2026-08-25.
    """
    import function_app

    archivador, repositorio, _ = _dobles(
        repositorio={"fallo": ReferenciaNoConsta("el parte no consta guardado")}
    )
    _con_dobles(monkeypatch, archivador, repositorio)

    respuesta = function_app.archivar(_peticion())

    assert respuesta.status_code == 409
    error = _json(respuesta)["error"]
    assert "/api/parte" in error
    assert archivador.biblioteca.subidas == 0


def test_f019_r20_el_409_promete_que_no_se_ha_subido_nada(monkeypatch):
    """R20 · y lo dice, porque quien lo lee tiene que saber si ir a mirar.

    La diferencia entre «no se ha subido nada» y «el fichero está arriba» es
    la que separa reintentar de ir a la biblioteca a limpiar a mano.
    """
    import function_app

    archivador, repositorio, _ = _dobles(
        repositorio={"fallo": ReferenciaNoConsta("el parte no consta guardado")}
    )
    _con_dobles(monkeypatch, archivador, repositorio)

    error = _json(function_app.archivar(_peticion()))["error"]

    assert "no se ha subido nada" in error.lower()


def test_f019_r21_el_borde_responde_503_diciendo_que_se_puede_reintentar(
    monkeypatch,
):
    """R21 · **503**, «no se ha subido nada y se puede reintentar».

    Es el mensaje que ya escribía F-010 al arreglar el defecto 14; lo que
    cambia con F-019 es que ahora es **verdad siempre**, porque el fallo
    ocurre antes de tocar SharePoint.
    """
    import function_app

    archivador, repositorio, _ = _dobles(
        repositorio={"fallo": PersistenciaNoDisponible("corte inventado")}
    )
    _con_dobles(monkeypatch, archivador, repositorio)

    respuesta = function_app.archivar(_peticion())
    error = _json(respuesta)["error"]

    assert respuesta.status_code == 503
    assert "no se ha" in error.lower()
    assert "reintentar" in error.lower()
    assert archivador.biblioteca.subidas == 0


def test_f019_r23_con_la_ventana_cerrada_el_repositorio_no_recibe_nada(
    monkeypatch,
):
    """R23 · la puerta de entorno corta **antes** de que la base se entere.

    Hoy eso pasa por el orden de evaluación de los argumentos en
    `archivar.py`: el archivador se construye antes que el repositorio, y con
    `ENTORNO=test` su fábrica se niega. **Ahora está fijado por un test**,
    porque con F-019 hay una escritura previa que sí importa que no ocurra:
    una fila `pendiente` escrita en un entorno que no puede archivar dejaría
    partes que parecen en curso y no lo están.

    Se inyecta el repositorio y **no** el archivador a propósito: es la única
    forma de que la fábrica de verdad se tope con la puerta.
    """
    import function_app
    from interface_adapters.api.archivar import archivar_parte

    repositorio = RepositorioFalso()

    def envoltura(contenido: bytes, **datos):
        return archivar_parte(contenido, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)

    respuesta = function_app.archivar(_peticion())

    assert respuesta.status_code == 503
    assert repositorio.llamadas_guardar_archivo == 0
    assert repositorio.archivos == []


def test_f019_r19_el_camino_feliz_del_borde_sigue_devolviendo_200(monkeypatch):
    """R19 · la garantía de orden **no rompe** lo que ya funcionaba.

    Control positivo del bloque: sin él, todos los tests de arriba estarían en
    verde si la traza previa hiciera fallar el camino bueno.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    archivador, repositorio, registro = _dobles(
        archivador={"biblioteca": biblioteca}
    )
    _con_dobles(monkeypatch, archivador, repositorio)

    respuesta = function_app.archivar(_peticion())

    assert respuesta.status_code == 200
    assert _json(respuesta)["estado"] == "archivado"
    assert biblioteca.nombres == [NOMBRE_ESPERADO]
    assert registro[0] == TRAZA_PREVIA
