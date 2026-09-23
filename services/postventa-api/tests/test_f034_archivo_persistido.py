# services/postventa-api/tests/test_f034_archivo_persistido.py
"""«Consta archivado» se lee de lo guardado, no del cuerpo (F-034, mitad A).

Hasta F-034, `POST /api/adjuntar` fabricaba una `TrazaArchivo` con el
`estado_archivo` del formulario y la puerta del paso la miraba a ella. El front
manda ese campo **fijo** (`js/pipeline.js`, constante `ESTADO_ARCHIVADO`), así
que un parte aprobado y **sin archivar** llegaba al ERP de producción con solo
mandar la cadena `archivado` (`requirements.md` §0.1).

Aquí se prueba:

- **la puerta compartida** `exigir_parte_archivado` (`puerta_de_estado.py`,
  `design.md` §3.3): lee `ctx.situacion.archivo` —la traza de
  `postventa.archivos` que F-033 trajo a la consulta de situación— y **nunca**
  `ctx.archivo` (R1, R5);
- **desde `POST /api/adjuntar`**, con los cinco puertos inyectados: el cuerpo
  que dice `archivado` sobre un parte sin traza guardada da **409 y cero
  llamadas al ERP** (R3), el cuerpo que se queda corto no molesta (R7), el
  borde deja de fabricar la traza (R4) y `estado_archivo` sigue siendo
  obligatorio y validado (R6). Sin una sola consulta más (R2).

`POST /api/cerrar` es el Bloque 3 (T8–T10) y crece aquí entonces.

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37).
"""

from __future__ import annotations

import json

import pytest
from application.pipelines import paso_grafico as modulo_paso_grafico
from application.pipelines import puerta_de_estado
from application.pipelines.contexto_parte import ContextoParte
from domain.models.errores import CuerpoDeGraficoInvalido, ParteNoArchivado
from domain.models.estado import SituacionParte
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from domain.models.remesa import ModoDeteccion, ParteTroceado

from tests.utiles_circuito import (
    PDF,
    MundoDelAdjuntar,
    formulario,
    situacion_guardada,
)

HASH = "f034a0a0a0a0"
OBRA = "0626"
INCIDENCIA = "RS26.08/0123"

#: La cola que el gráfico pone al mensaje de la puerta. Es, byte a byte, la de
#: `paso_grafico._exigir_archivado` antes de F-034.
COLA_DEL_GRAFICO = "no se adjunta a la reclamación: primero el documento, después el ERP"

#: Los estados guardados que **no** abren la puerta, con cómo los nombra el
#: mensaje: `None` es «no hay traza» (el `LEFT JOIN` que no casa).
ESTADOS_QUE_NO_ABREN = [
    (None, "ninguno"),
    (EstadoArchivo.PENDIENTE, "pendiente"),
    (EstadoArchivo.ERROR, "error"),
]


def _contexto(
    *,
    archivo_guardado: EstadoArchivo | None,
    archivo_del_cuerpo: EstadoArchivo | None = None,
    con_situacion: bool = True,
) -> ContextoParte:
    """Un contexto con las **dos** fuentes separadas, a propósito.

    `archivo_guardado` va a `ctx.situacion.archivo` (lo que diría la base) y
    `archivo_del_cuerpo` a `ctx.archivo` (lo que fabricaba el borde con el
    formulario). Que puedan contradecirse es lo único que hace que estos tests
    vean el defecto.
    """
    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=PDF,
        ),
        archivo=(
            TrazaArchivo(hash_parte=HASH, estado=archivo_del_cuerpo)
            if archivo_del_cuerpo is not None
            else None
        ),
        situacion=(
            SituacionParte(
                archivo=(
                    TrazaArchivo(hash_parte=HASH, estado=archivo_guardado)
                    if archivo_guardado is not None
                    else None
                )
            )
            if con_situacion
            else None
        ),
    )


# --------------------------------------------------------------------------
# T5 · la puerta compartida, en `puerta_de_estado.py`
# --------------------------------------------------------------------------


def test_f034_r1_puerta_pasa_con_la_traza_guardada_en_archivado():
    """R1 · lo que decide es la traza **guardada**, y con ella la puerta abre.

    `ctx.archivo` va vacío a propósito: desde F-034 el borde ya no lo rellena,
    y la puerta no lo echa de menos.
    """
    ctx = _contexto(archivo_guardado=EstadoArchivo.ARCHIVADO)

    puerta_de_estado.exigir_parte_archivado(ctx, y_por_eso=COLA_DEL_GRAFICO)


@pytest.mark.parametrize(("guardado", "nombre"), ESTADOS_QUE_NO_ABREN)
def test_f034_r3_puerta_sin_archivado_guardado_no_pasa(guardado, nombre):
    """R3 · sin traza guardada, o con ella en `pendiente` o `error`: 409.

    El mensaje nombra el estado **guardado** —que es el que hay que arreglar
    archivando— y lleva la cola de quien llama, que es lo que dice qué se ha
    quedado sin hacer.
    """
    ctx = _contexto(archivo_guardado=guardado)

    with pytest.raises(ParteNoArchivado) as fallo:
        puerta_de_estado.exigir_parte_archivado(ctx, y_por_eso=COLA_DEL_GRAFICO)

    assert fallo.value.motivo == (
        f"este parte no consta archivado (estado del archivo: {nombre}), "
        f"así que {COLA_DEL_GRAFICO}"
    )


@pytest.mark.parametrize(("guardado", "_nombre"), ESTADOS_QUE_NO_ABREN)
def test_f034_r5_puerta_lo_que_diga_el_cuerpo_no_la_abre(guardado, _nombre):
    """R5 · **el corazón de la mitad A**: `ctx.archivo` en `archivado` no abre.

    Es exactamente el mundo del defecto: el formulario dice `archivado` y la
    base dice otra cosa. Antes de F-034 esto pasaba.
    """
    ctx = _contexto(
        archivo_guardado=guardado, archivo_del_cuerpo=EstadoArchivo.ARCHIVADO
    )

    with pytest.raises(ParteNoArchivado):
        puerta_de_estado.exigir_parte_archivado(ctx, y_por_eso=COLA_DEL_GRAFICO)


@pytest.mark.parametrize(
    "del_cuerpo", [None, EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR]
)
def test_f034_r7_puerta_lo_que_diga_el_cuerpo_tampoco_la_cierra(del_cuerpo):
    """R7 · manda lo guardado: un cuerpo que se queda corto no es un conflicto."""
    ctx = _contexto(
        archivo_guardado=EstadoArchivo.ARCHIVADO, archivo_del_cuerpo=del_cuerpo
    )

    puerta_de_estado.exigir_parte_archivado(ctx, y_por_eso=COLA_DEL_GRAFICO)


def test_f034_r1_puerta_sin_situacion_leida_no_pasa():
    """R1 · sin situación no hay traza guardada, y eso es «ninguno», no un pase.

    La puerta de aptitud va antes en los dos pasos y siempre deja la situación
    puesta, así que esto no ocurre en el circuito. Pero si algún día alguien la
    llamara fuera de ese orden, lo que tiene que pasar es un 409, no un
    `AttributeError` —un 500— ni, peor, dejar pasar.
    """
    ctx = _contexto(archivo_guardado=None, con_situacion=False)

    with pytest.raises(ParteNoArchivado) as fallo:
        puerta_de_estado.exigir_parte_archivado(ctx, y_por_eso=COLA_DEL_GRAFICO)

    assert "(estado del archivo: ninguno)" in fallo.value.motivo


def test_f034_r1_puerta_el_modulo_la_publica_y_dice_de_donde_lee():
    """R1 · vive junto a `exigir_parte_aprobado`, con su enmienda fechada.

    Quien llegue a `puerta_de_estado.py` dentro de seis meses tiene que leer
    ahí que la puerta de archivo existe, que es de F-034 y que lee lo guardado.
    """
    assert "exigir_parte_archivado" in puerta_de_estado.__all__
    cabecera = puerta_de_estado.__doc__ or ""
    assert "F-034" in cabecera
    assert "ctx.situacion.archivo" in cabecera


def test_f034_r1_puerta_el_grafico_usa_la_compartida_y_no_su_copia():
    """R1, D-6 · una regla, un sitio: la copia privada del gráfico desaparece.

    Dos copias de la regla **que esta feature acaba de cambiar** divergerían el
    día que alguien corrigiera una sola (la cabecera de `puerta_de_estado.py`).
    """
    assert not hasattr(modulo_paso_grafico, "_exigir_archivado")
    assert (
        modulo_paso_grafico.exigir_parte_archivado
        is puerta_de_estado.exigir_parte_archivado
    )


# --------------------------------------------------------------------------
# T4 · desde `POST /api/adjuntar`, con los puertos inyectados
# --------------------------------------------------------------------------


def _mundo(estado_archivo: EstadoArchivo | None) -> MundoDelAdjuntar:
    """Parte apto con sus dos códigos guardados y el archivo que pida el caso."""
    return MundoDelAdjuntar(
        situacion_guardada(
            hash_parte=HASH,
            codigo_obra=OBRA,
            numero_incidencia=INCIDENCIA,
            estado_archivo=estado_archivo,
        )
    )


def _cuerpo(**cambios: str) -> dict[str, str]:
    """Lo declarado: los mismos códigos que los guardados, salvo que se diga."""
    return formulario(
        hash_parte=HASH, codigo_obra=OBRA, numero_incidencia=INCIDENCIA, **cambios
    )


def test_f034_r3_control_positivo_el_mismo_mundo_con_archivo_si_adjunta():
    """El control de los casos de abajo: con la traza guardada, **pasa**.

    Sin este caso, un 409 de abajo podría salir por cualquier otra cosa del
    mundo —un veredicto que no llega, un código que no cuadra— y parecería la
    puerta de archivo. Mismo mundo, mismo cuerpo, solo cambia lo guardado.
    """
    mundo = _mundo(EstadoArchivo.ARCHIVADO)

    respuesta = mundo.adjuntar(_cuerpo(commit="true", confirmado="true"))

    assert respuesta["estado"] == "adjuntado"
    assert mundo.graficos.orden == [False, True]


@pytest.mark.parametrize("commit", ["", "true"], ids=["dry_run", "commit"])
@pytest.mark.parametrize(("guardado", "nombre"), ESTADOS_QUE_NO_ABREN)
def test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp(
    guardado, nombre, commit
):
    """R3, R5 · **caso central**: el cuerpo dice `archivado` y la base no.

    409 con el `ParteNoArchivado` de siempre, nombrando el estado **guardado**,
    y **cero** llamadas: ni al ERP, ni a la pasarela, ni una traza. También en
    dry-run: enseñar el plan de un parte sin archivar es enseñar algo que no va
    a poder pasar.
    """
    mundo = _mundo(guardado)

    with pytest.raises(ParteNoArchivado) as fallo:
        mundo.adjuntar(
            _cuerpo(estado_archivo="archivado", commit=commit, confirmado="true")
        )

    assert f"(estado del archivo: {nombre})" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r3_adjuntar_por_la_ruta_es_409_con_el_motivo_y_nada_mas(monkeypatch):
    """R3, R27 · lo mismo, recorriendo la ruta HTTP de verdad.

    El handler es el de verdad y los puertos van inyectados, así que el 409
    sale del `except` real de `function_app.py` y no de un error fabricado.
    """
    mundo = _mundo(None)

    respuesta = mundo.por_la_ruta(monkeypatch, _cuerpo(estado_archivo="archivado"))

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.get_body())
    assert set(cuerpo) == {"error"}
    assert "(estado del archivo: ninguno)" in cuerpo["error"]
    assert mundo.nada_ha_tocado_el_erp()


@pytest.mark.parametrize("del_cuerpo", ["pendiente", "error"])
def test_f034_r7_adjuntar_cuerpo_corto_con_archivo_guardado_pasa(del_cuerpo):
    """R7 · **manda lo guardado**: si la base dice `archivado`, se adjunta.

    Un 409 aquí sería un error nuevo sin ninguna escritura que evitar: el
    cliente se ha quedado corto en su afirmación y la base sabe más que él.
    Antes de F-034 esto **no** pasaba, porque decidía el cuerpo.
    """
    mundo = _mundo(EstadoArchivo.ARCHIVADO)

    respuesta = mundo.adjuntar(_cuerpo(estado_archivo=del_cuerpo))

    assert respuesta["estado"] == "dry_run_ok"
    assert mundo.graficos.orden == [False]


@pytest.mark.parametrize("valor", ["", "archivadisimo"])
def test_f034_r6_adjuntar_estado_archivo_sigue_siendo_obligatorio_y_validado(valor):
    """R6, R17, R18 · el contrato HTTP no cambia: falta o no existe → 400.

    Deja de decidir, pero no deja de ser un campo del contrato: un cliente
    viejo que lo mande sigue funcionando y uno que no lo mande sigue recibiendo
    el mismo 400 de siempre.
    """
    mundo = _mundo(EstadoArchivo.ARCHIVADO)

    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        mundo.adjuntar(_cuerpo(estado_archivo=valor))

    assert "estado_archivo" in fallo.value.motivo
    assert mundo.nada_ha_tocado_el_erp()


def test_f034_r4_adjuntar_el_borde_ya_no_fabrica_la_traza_de_archivo(monkeypatch):
    """R4 · **la segunda fuente desaparece, no se tapa**.

    Se sustituye el paso por un espía y se mira el contexto que le llega: sin
    `TrazaArchivo`. Si el borde la volviera a fabricar, la puerta seguiría sin
    mirarla —la protege R5—, pero volvería a haber un objeto con un estado que
    no ha salido de ninguna lectura, esperando a que alguien lo use.
    """
    from interface_adapters.api import adjuntar as modulo_adjuntar

    recibidos: list[ContextoParte] = []

    def espia(ctx, *_puertos, **_opciones):
        recibidos.append(ctx)
        raise ParteNoArchivado("parado por el espía del test")

    monkeypatch.setattr(modulo_adjuntar, "paso_grafico", espia)

    with pytest.raises(ParteNoArchivado):
        _mundo(EstadoArchivo.ARCHIVADO).adjuntar(_cuerpo(estado_archivo="archivado"))

    assert len(recibidos) == 1
    assert recibidos[0].archivo is None


def test_f034_r2_adjuntar_la_traza_guardada_no_cuesta_ninguna_consulta_mas():
    """R2 · la traza viaja en la consulta de situación que la puerta ya hacía.

    Una sola consulta de situación por petición, la de la puerta de aptitud.
    El contador exacto por paso, antes y después, es de T12.
    """
    mundo = _mundo(EstadoArchivo.ARCHIVADO)

    mundo.adjuntar(_cuerpo())

    assert mundo.repositorio.situaciones_consultadas == [HASH]


def test_f034_r6_adjuntar_el_modulo_dice_que_estado_archivo_ya_no_decide():
    """R6 · la enmienda fechada en el docstring del endpoint, como F-030.

    El campo se queda en el contrato y **no decide nada**. Si eso no está
    escrito al lado del código, el siguiente que lo lea supondrá que decide.
    """
    from interface_adapters.api import adjuntar as modulo_adjuntar

    cabecera = modulo_adjuntar.__doc__ or ""
    assert "F-034" in cabecera
    assert "estado_archivo" in cabecera
