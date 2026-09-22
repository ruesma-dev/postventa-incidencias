# services/postventa-api/tests/test_f031_cotejo_de_codigos.py
"""Lo declarado tiene que ser lo guardado, o no se archiva (F-031 R3–R6, R9–R11).

Se prueba casi todo **desde `POST /api/archivar`**, con la petición
`multipart/form-data` construida a mano y los dos puertos sustituidos por
dobles, igual que `test_f006_archivar_http.py`: así se ejercita el borde
entero —parseo, códigos de estado, JSON— y por debajo corre el paso de verdad.
**SharePoint no aparece por ninguna parte** y no se abre ni un socket (R28).

La excepción es el **caso central de R3 y R5**, que se ejercita además
directamente sobre `paso_archivo`: lo que ahí se afirma no es un código HTTP,
es que ninguno de los dos puertos llegó a recibir una sola llamada, y eso se
lee mejor sin el borde por medio.

## Qué separa este fichero de `test_f031_nombrado_persistido.py`

Aquél vigila **de dónde sale el nombre**; éste, **qué pasa cuando el cuerpo
dice otra cosa**. Son las dos mitades del mismo requisito y se rompen por
sitios distintos: el primero se rompería nombrando con el cuerpo, el segundo
dejando pasar una divergencia.

Y lo que de verdad importa de casi todos los casos de aquí no es el código
HTTP: es que **no se haya escrito ni subido nada**. Por eso los dobles cuentan
escrituras y llamadas, y no se limitan a devolver lo que el test esperaba.

**Ni un dato real.** El «PDF» lleva un DNI inventado —`00000000T` no es
válido— justamente para comprobar que no se cuela en ningún mensaje de error.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime

import azure.functions as func
import pytest
from application.pipelines.paso_archivo import CodigosDelParte, paso_archivo
from domain.models.errores import (
    CodigosNoCoinciden,
    NombradoImposible,
    ParteNoApto,
)
from domain.models.estado import SituacionParte
from interface_adapters.api.archivar import archivar_parte

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
)
from tests.utiles_validacion import veredicto_apto

_FRONTERA = "frontera-sintetica-de-test-f031"

#: El contrato de la respuesta (F-006 R30, conservado por F-031 R26).
CLAVES_DE_LA_RESPUESTA = {
    "hash_parte",
    "nombre_fichero",
    "carpeta",
    "estado",
    "web_url",
    "avisos",
}

#: Un PDF de mentira con algo que parece un dato personal.
PDF_CON_DATOS = b"%PDF-1.4 Fdo. Cliente Inventado DNI 00000000T"

HASH = "9f2b0011aabb"

#: Un instante fijo: el paso no consulta el reloj, la hora entra por parámetro.
AHORA = datetime(2026, 9, 22, 10, 0, tzinfo=UTC)

#: Lo que consta **guardado** de este parte. Inventado.
OBRA_GUARDADA = "0677"
INCIDENCIA_GUARDADA = "RS26.08/0123"
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"
CARPETA_ESPERADA = "Postventa/0677"


def formulario(
    codigo_obra: str = OBRA_GUARDADA,
    numero_incidencia: str = INCIDENCIA_GUARDADA,
    **cambios: str,
) -> tuple[tuple[str, str], ...]:
    """Los cinco campos del cuerpo, con los dos códigos que pida el caso.

    `veredicto` y `destino` siguen siendo obligatorios y siguen validándose
    contra las enumeraciones de F-004 (R6, R10): esta feature no toca el
    contrato HTTP, solo cambia **para qué sirven** dos de los cinco.
    """
    campos = {
        "hash": HASH,
        "codigo_obra": codigo_obra,
        "numero_incidencia": numero_incidencia,
        "veredicto": "apto",
        "destino": "archivo_y_cierre",
    }
    campos.update(cambios)
    return tuple(campos.items())


def situacion_guardada(
    codigo_obra: str = OBRA_GUARDADA, numero_incidencia: str = INCIDENCIA_GUARDADA
) -> SituacionParte:
    """La situación que devolvería la base: veredicto apto con **esos** códigos.

    Los códigos se pisan con `replace` sobre un veredicto que sale de
    `validar_parte`, por lo mismo que en `test_f031_nombrado_persistido.py`:
    un código vacío no es legible y F-004 no declararía apto ese parte.
    """
    return SituacionParte(
        validacion=replace(
            veredicto_apto(hash_parte=HASH),
            codigo_obra=codigo_obra,
            numero_incidencia=numero_incidencia,
        )
    )


def _peticion(campos: Sequence[tuple[str, str]]) -> func.HttpRequest:
    """Petición `multipart/form-data` con un parte y esos campos."""
    cuerpo = (
        f"--{_FRONTERA}\r\n"
        f'Content-Disposition: form-data; name="fichero"; filename="parte.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + PDF_CON_DATOS + b"\r\n"
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
    """La ruta de verdad, con los dos puertos sustituidos por dobles.

    Se sustituye lo que `function_app` tiene importado y no el handler: así se
    ejercita el borde entero —parseo del multipart, traducción a códigos HTTP,
    JSON— y por debajo corre `archivar_parte`, que es quien compone los
    códigos declarados y se los pasa al paso.
    """
    import function_app

    def envoltura(contenido: bytes, **datos):
        return archivar_parte(
            contenido, archivador=archivador, repositorio=repositorio, **datos
        )

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)


def _archivar(campos: Sequence[tuple[str, str]]) -> func.HttpResponse:
    import function_app

    return function_app.archivar(_peticion(campos))


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())

# --------------------------------------------------------------------------
# El error de dominio (T3) · por qué es propio y no `ParteNoApto` reutilizado
# --------------------------------------------------------------------------


def test_f031_errores_codigos_no_coinciden_lleva_su_motivo():
    """El `motivo` viaja en el objeto, como en sus hermanas.

    El borde lo lee para componer el cuerpo del 409, igual que hace con
    `ParteNoApto` y con `NombradoImposible`. Sin él, el error saldría como un
    409 mudo y quien lo recibiera tendría que ir a mirar la base a mano.
    """
    error = CodigosNoCoinciden("el código de obra de la petición no es el guardado")

    assert isinstance(error, Exception)
    assert error.motivo == "el código de obra de la petición no es el guardado"
    assert str(error) == error.motivo


def test_f031_errores_no_es_parte_no_apto_ni_nombrado_imposible():
    """Excepción propia, y la distinción **no es cosmética**.

    Los tres son 409, pero llevan a acciones **opuestas**: `ParteNoApto` se
    arregla decidiendo sobre el parte, `NombradoImposible` mandándolo a
    revisión manual, y esto **guardando la corrección** y volviendo a
    intentarlo. Si heredara de cualquiera de las otras dos, el `except` que ya
    existe en el borde se la tragaría y el mensaje que le llega a una persona
    sería el que no es.
    """
    assert not issubclass(CodigosNoCoinciden, ParteNoApto)
    assert not issubclass(CodigosNoCoinciden, NombradoImposible)
    assert not issubclass(ParteNoApto, CodigosNoCoinciden)
    assert not issubclass(NombradoImposible, CodigosNoCoinciden)


def test_f031_errores_el_docstring_dice_en_que_se_diferencia_de_sus_hermanas():
    """El porqué vive al lado del error, no solo en la spec.

    Es lo que ya hacen `ParteNoArchivado`, `ArchivoSinTraza` y
    `ReferenciaNoConsta`, cada una con su docstring diciendo por qué tiene
    nombre propio. Quien se encuentre este error dentro de seis meses lee el
    módulo, no `specs/F-031-nombrado-persistido/design.md`.
    """
    documentacion = CodigosNoCoinciden.__doc__ or ""

    assert "ParteNoApto" in documentacion
    assert "NombradoImposible" in documentacion
    assert "F-031" in documentacion


# --------------------------------------------------------------------------
# R3, R5 · el caso central, sobre el paso y sin el borde por medio
# --------------------------------------------------------------------------


def test_f031_r3_un_cuerpo_que_dice_otra_obra_no_sube_nada():
    """R3, R5 · `codigo_obra=0677` guardado, `0999` declarado: **cero llamadas**.

    Es el caso que sostiene la feature. No es que se archive con el guardado y
    se avise: **no se archiva**. Con L1 de F-033 cortando por `hash` + estado y
    sin forma de forzar el re-archivo, un PDF subido a la carpeta equivocada no
    se arregla desde el circuito (`design.md` §7.4): el coste de equivocarse
    aquí es permanente, y por eso el cotejo va antes que todo lo que deja
    rastro.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso(situacion=situacion_guardada())

    with pytest.raises(CodigosNoCoinciden):
        paso_archivo(
            contexto_apto(hash_parte=HASH),
            archivador,
            repositorio,
            carpeta_base=CARPETA_BASE,
            ahora=AHORA,
            codigos_declarados=CodigosDelParte(
                codigo_obra="0999", numero_incidencia=INCIDENCIA_GUARDADA
            ),
        )

    assert archivador.llamadas == []
    assert biblioteca.subidas == 0
    assert biblioteca.carpetas == set()
    assert repositorio.llamadas_guardar_archivo == 0


# --------------------------------------------------------------------------
# R3 · un cuerpo que no dice lo que consta guardado es un 409
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "campos", "que_no_cuadra", "declarado"),
    (
        (
            "otra obra",
            formulario(codigo_obra="0999"),
            "código de obra",
            "0999",
        ),
        (
            "otra incidencia",
            formulario(numero_incidencia="RS26.09/0999"),
            "nº de incidencia",
            "RS26.09/0999",
        ),
        (
            "la obra sin sus ceros",
            formulario(codigo_obra="677"),
            "código de obra",
            "677",
        ),
        (
            "las dos: manda la primera que falla",
            formulario(codigo_obra="0999", numero_incidencia="RS26.09/0999"),
            "código de obra",
            "0999",
        ),
    ),
)
def test_f031_r3_un_cuerpo_que_miente_responde_409_diciendo_cual(
    monkeypatch, caso, campos, que_no_cuadra, declarado
):
    """R3 · 409, y el mensaje dice **cuál** de los dos y qué hay que hacer.

    Un 409 que no lo dijera obligaría a mirar la base a mano para entender por
    qué no se archiva un parte que en la pantalla se ve bien. Y la acción
    concreta importa tanto como el diagnóstico: esto **no** se arregla
    reintentando, se arregla guardando la corrección.
    """
    biblioteca = BibliotecaFalsa()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(biblioteca),
        RepositorioFalso(situacion=situacion_guardada()),
    )

    respuesta = _archivar(campos)

    assert respuesta.status_code == 409, caso
    motivo = _cuerpo(respuesta)["error"]
    assert que_no_cuadra in motivo, caso
    assert declarado in motivo, caso
    assert "/api/parte" in motivo, caso
    assert biblioteca.subidas == 0


def test_f031_r3_el_409_nombra_tambien_el_valor_guardado(monkeypatch):
    """R3 · los dos valores, el declarado y el guardado.

    Sin el guardado, quien lee el error sabe que su código no cuadra pero no
    con qué; y lo que tiene que hacer es decidir si corrige el papel o si lo
    que hay en la base está mal. Los dos códigos identifican una obra y una
    reclamación, no a una persona, así que pueden salir (R25).
    """
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(),
        RepositorioFalso(situacion=situacion_guardada()),
    )

    respuesta = _archivar(formulario(codigo_obra="0999"))

    motivo = _cuerpo(respuesta)["error"]
    assert OBRA_GUARDADA in motivo
    assert "0999" in motivo


def test_f031_r25_el_409_no_lleva_ningun_dato_del_papel(monkeypatch):
    """R25 · ni el DNI, ni las observaciones, ni los bytes del parte.

    Un mensaje de error es lo que más se copia y se pega en un ticket, y este
    lo va a ver una persona en la pantalla del front.
    """
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(),
        RepositorioFalso(situacion=situacion_guardada()),
    )

    respuesta = _archivar(formulario(codigo_obra="0999"))

    texto = respuesta.get_body().decode()
    assert "00000000T" not in texto
    assert "%PDF" not in texto
    assert "drive" not in texto.lower()


# --------------------------------------------------------------------------
# R5 · y antes de la traza previa y de tocar el puerto
# --------------------------------------------------------------------------


def test_f031_r5_ante_una_divergencia_no_se_escribe_ni_se_llama_a_nadie(monkeypatch):
    """R5 · ni carpeta, ni búsqueda, ni bytes, ni fila en `postventa.archivos`.

    Es el requisito que fija **dónde** va el cotejo, y no es cosmético: a
    partir de la traza previa ya hay una fila escrita, y a partir de
    `asegurar_carpeta` ya se ha hablado con SharePoint. Un cotejo que fallara
    después dejaría rastro de un archivado que nunca debió intentarse — y con
    L1 de F-033, una traza que además corta para siempre el reintento.
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioFalso(situacion=situacion_guardada())
    _con_dobles(monkeypatch, archivador, repositorio)

    respuesta = _archivar(formulario(codigo_obra="0999"))

    assert respuesta.status_code == 409
    # El repositorio: **ninguna** escritura, ni siquiera la previa.
    assert repositorio.llamadas_guardar_archivo == 0
    assert repositorio.archivos == []
    assert repositorio.registro == []
    # SharePoint: **ninguna** llamada de ningún tipo.
    assert archivador.llamadas == []
    assert biblioteca.carpetas == set()
    assert biblioteca.elementos == {}
    assert biblioteca.creaciones_de_carpeta == 0


# --------------------------------------------------------------------------
# R4 · el mismo código escrito de dos maneras **no** es un 409
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "guardado_obra", "guardado_incidencia", "campos"),
    (
        (
            "el espacio dentro del primer tramo (2026-09-17)",
            "0626",
            "RS26.09/0178",
            formulario(codigo_obra="0626", numero_incidencia="RS 26.09/0178"),
        ),
        (
            "el espacio dentro del código de obra",
            "0626",
            "RS26.09/0178",
            formulario(codigo_obra="06 26", numero_incidencia="RS26.09/0178"),
        ),
        (
            "el guion largo del escaneo",
            "0626",
            "RS26.09-0178",
            formulario(codigo_obra="0626", numero_incidencia="RS26.09 – 0178"),
        ),
        (
            "y al revés: la base con el espacio y el cuerpo limpio",
            "06 26",
            "RS 26.09/0178",
            formulario(codigo_obra="0626", numero_incidencia="RS26.09/0178"),
        ),
    ),
)
def test_f031_r4_el_mismo_codigo_escrito_de_dos_maneras_archiva(
    monkeypatch, caso, guardado_obra, guardado_incidencia, campos
):
    """R4 · lo que F-032 declaró equivalente no puede convertirse en un error.

    El front manda lo que devuelve `valorDeCampo`, que solo hace `trim()`; la
    base guarda lo que F-032 saneó al leerlo. Un cotejo literal habría
    convertido el caso del **2026-09-17** —el que costó un cierre a mano— en un
    409 diario.
    """
    biblioteca = BibliotecaFalsa()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(biblioteca),
        RepositorioFalso(
            situacion=situacion_guardada(guardado_obra, guardado_incidencia)
        ),
    )

    respuesta = _archivar(campos)

    assert respuesta.status_code == 200, caso
    assert biblioteca.nombres == ["0626 - RS26.09 - 0178 PARTE FIRMADO.pdf"], caso
    assert biblioteca.carpetas == {"Postventa/0626"}, caso


def test_f031_r10_el_camino_bueno_sigue_devolviendo_las_seis_claves(monkeypatch):
    """R10, R26 · el contrato HTTP no cambia: mismos campos, un 409 más.

    Ni una clave nueva en la respuesta, ni un código de estado nuevo. Lo único
    que cambia es **para qué sirven** dos de los cinco campos del cuerpo.
    """
    biblioteca = BibliotecaFalsa()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(biblioteca),
        RepositorioFalso(situacion=situacion_guardada()),
    )

    respuesta = _archivar(formulario())

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["nombre_fichero"] == NOMBRE_ESPERADO
    assert cuerpo["carpeta"] == CARPETA_ESPERADA
    assert biblioteca.nombres == [NOMBRE_ESPERADO]


# --------------------------------------------------------------------------
# R6, R10 · una petición mal formada sigue siendo 400, no 409
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "campos"),
    (
        ("sin hash", (("codigo_obra", OBRA_GUARDADA), ("veredicto", "apto"))),
        ("sin código de obra", formulario(codigo_obra="")),
        ("sin nº de incidencia", formulario(numero_incidencia="")),
        ("código de obra de solo blancos", formulario(codigo_obra="   ")),
        ("veredicto que no existe", formulario(veredicto="regular")),
        ("destino que no existe", formulario(destino="a_la_papelera")),
    ),
)
def test_f031_r6_una_peticion_mal_formada_es_400_y_no_el_409_nuevo(
    monkeypatch, caso, campos
):
    """R6, R10 · un cuerpo incompleto no es un conflicto de estado (F-030 R19).

    La distinción no es cosmética y aquí menos que nunca: un 409 mandaría a
    guardar una corrección a quien tiene que arreglar su petición, y los dos
    campos **siguen siendo obligatorios** (R10) precisamente porque sin lo
    declarado no hay con qué cotejar.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=situacion_guardada())
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), repositorio)

    respuesta = _archivar(campos)

    assert respuesta.status_code == 400, caso
    assert biblioteca.subidas == 0
    assert repositorio.llamadas_guardar_archivo == 0


# --------------------------------------------------------------------------
# R9 · un parte que no consta validado ni llega a nombrarse
# --------------------------------------------------------------------------


def test_f031_r9_un_parte_que_no_consta_validado_responde_409_de_la_puerta(
    monkeypatch,
):
    """R9 · el 409 es el de siempre, el de la puerta de estado, y va **antes**.

    Esta feature no lo cambia; se escribe porque la ficha pregunta por él. Lo
    que sí afirma el caso es el **orden**: la puerta corre antes que el cotejo
    y antes que el nombrado, así que un parte del que nadie ha emitido
    veredicto no llega ni a que se le comparen los códigos.
    """
    biblioteca = BibliotecaFalsa()
    repositorio = RepositorioFalso(situacion=SituacionParte())
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), repositorio)

    respuesta = _archivar(formulario(codigo_obra="0999"))

    assert respuesta.status_code == 409
    assert "no consta que este parte haya pasado la validación" in (
        _cuerpo(respuesta)["error"]
    )
    assert biblioteca.subidas == 0
    assert repositorio.llamadas_guardar_archivo == 0


# --------------------------------------------------------------------------
# R11 · ningún valor del cuerpo puede decidir dónde acaba el PDF
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "campos"),
    (
        ("otra obra entera", formulario(codigo_obra="0999")),
        ("una obra que existe de verdad", formulario(codigo_obra="0626")),
        ("la obra sin ceros", formulario(codigo_obra="677")),
        ("una ruta dentro de la obra", formulario(codigo_obra="0677/oculto")),
    ),
)
def test_f031_r11_nada_del_cuerpo_abre_ni_mueve_la_puerta(monkeypatch, caso, campos):
    """R11 · lo declarado solo puede **cerrar** la puerta, nunca abrirla ni moverla.

    Ninguno de estos cuerpos consigue que el PDF acabe en otro sitio: o coteja
    y archiva donde dice la base, o no coteja y no se archiva nada. La carpeta
    que pide el cuerpo **no se crea en ningún caso**, que es lo que de verdad
    se está afirmando.
    """
    biblioteca = BibliotecaFalsa()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(biblioteca),
        RepositorioFalso(situacion=situacion_guardada()),
    )

    respuesta = _archivar(campos)

    assert respuesta.status_code == 409, caso
    assert biblioteca.carpetas == set(), caso
    assert biblioteca.elementos == {}, caso
