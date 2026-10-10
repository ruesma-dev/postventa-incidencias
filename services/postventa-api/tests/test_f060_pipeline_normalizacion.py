# services/postventa-api/tests/test_f060_pipeline_normalizacion.py
"""La normalización de una obra en la aplicación (F-060 T9; `design.md` §8).

`normalizar_ubicaciones` de `application/pipelines/revision.py`, con los dobles
de F-056 (`tests/utiles_revision.py`) y `RevisionConLote`
(`tests/utiles_normalizacion.py`), que añade el lote con la semántica del
repositorio. Todos anotan en una lista común, y así se fija **el orden**:

    revision.listar (tope) → [más del tope: revision.contar y error] →
    ubicaciones (una lectura, con el catálogo recibido) → plan →
    [ni ensayo ni plan vacío: revision.registrar_lote]

| Caso | Requisito |
|---|---|
| más de 10.000: `BandejaDemasiadoGrande` con el recuento, sin leer ubicaciones ni escribir; 10.000 justas sí | R17 |
| una lectura de las ubicaciones, con el catálogo que recibe; ninguna lectura del catálogo | R18 |
| el recuento de la obra y su suma | R10, R18 |
| el ensayo no llama al lote y devuelve `normalizadas = conflictos = 0` | R19 |
| la real registra el lote del plan; un conflicto se cuenta y no aborta; `normalizadas + conflictos = normalizables` | R20 |
| un plan vacío no llama al lote | §8 |
| dos ejecuciones: la segunda no tiene nada que normalizar | R21 |
| la fila del listado y el historial, por los handlers de F-056 | R22 |
| ambigua y sin coincidencia siguen fuera de lista, sin revisión; aprobada y descartada intactas | R7, R23 |
| normalizar y aprobar: la candidata lleva el texto de Sigrid | R24 |
| sin normalizar: aprobar 409 y editar con la variante 400 (F-056 sigue exacto) | R25 |
| las listas salen de la fuente de F-056, ya filtradas (de 48 como mucho) | O-3 de las reviews de los Bloques 1 y 2 |
| un fallo de la base o de Sigrid sube tal cual, sin nada escrito | R14, R28 |

Datos ficticios: obra `9901`, ubicaciones «Baño», «Cocina», «Terraza», «Sala
Ejemplo», correos `@ejemplo.invalid`; identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.revision import (
    ResultadoNormalizacion,
    aplicar_accion,
    candidatas_al_volcado,
    fuente_de_ubicaciones,
    normalizar_ubicaciones,
)
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    IncidenciaNoAprobable,
    PersistenciaNoDisponible,
    ValoresNoValidos,
)
from domain.models.normalizacion import (
    QUIEN_SISTEMA,
    TEXTO_SISTEMA,
    Coincidencia,
    RecuentoNormalizacion,
    ubicacion_de_sigrid,
)
from domain.models.revision import (
    MAX_UBICACION,
    TOPE_LECTURA_OBRA,
    AccionRevision,
    PeticionDeAccion,
    Quien,
    ValoresPedidos,
    huella_de_valores,
    valores_importados,
)
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import revision as handlers_de_f056

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_normalizacion import RevisionConLote
from tests.utiles_revision import (
    AHORA,
    CORREO,
    DESCRIPCION,
    LISTAS,
    OBRA,
    OID,
    U1,
    U2,
    U3,
    CatalogoDeLaObra,
    UbicacionesQueCuentan,
    incidencia,
)

A = AccionRevision

#: El instante de la petición de normalizar (distinto del de las sembradas).
AHORA_N = datetime(2026, 10, 10, 7, 0, tzinfo=UTC)

#: La configuración de la plantilla de verdad, para el listado de F-056.
CONFIG = cargar_plantilla_yaml()

QUIEN = Quien(oid=OID, correo=CORREO)


def _diez() -> tuple:
    """Una obra con cada caso de la regla. La lista de U1 es «Baño», «Cocina»,
    «cocina»; la de U2, «Terraza», «Baño»; la de U3, vacía (`UBICACIONES`)."""
    return (
        incidencia(1, ubicacion="baño"),  # normalizable → «Baño»
        incidencia(2, ubicacion="BAÑO"),  # normalizable → «Baño»
        incidencia(3, unidad_codigo=U2, ubicacion="terraza"),  # → «Terraza»
        incidencia(4, ubicacion="COCINA"),  # ambigua: «Cocina» y «cocina»
        incidencia(5, ubicacion="Baño"),  # exacta
        incidencia(6, ubicacion=None),  # sin ubicación
        incidencia(7, ubicacion="Sala Ejemplo"),  # sin coincidencia
        incidencia(8, unidad_codigo=U3, ubicacion="baño"),  # lista vacía
        incidencia(9, ubicacion="baño"),  # aprobada: no editable
        incidencia(10, ubicacion="baño"),  # descartada: no editable
    )


#: El recuento de `_diez()` (R10): 10 examinadas; no exactas, 1, 2, 3, 4, 7, 8,
#: 9 y 10; normalizables 1, 2 y 3; ambigua la 4; sin coincidencia 7 y 8; no
#: editables 9 y 10.
RECUENTO_DE_DIEZ = RecuentoNormalizacion(
    examinadas=10,
    no_exactas=8,
    normalizables=3,
    ambiguas=1,
    sin_coincidencia=2,
    no_editables=2,
)


class Mundo:
    """La bandeja con lote, la fuente de las ubicaciones y el catálogo ya leído."""

    def __init__(self, *incidencias, mapa: dict[str, tuple[str, ...]] | None = None) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionConLote(self.llamadas, incidencias or _diez())
        self.ubicaciones = UbicacionesQueCuentan(self.llamadas, mapa)
        # El catálogo **ya leído**, con su propia lista: sus lecturas no son de
        # la normalización, que lo recibe hecho.
        self.lecturas_del_catalogo: list[str] = []
        self.catalogo = leer_catalogo(CatalogoDeLaObra(self.lecturas_del_catalogo), OBRA)
        if not incidencias:
            self.sembrar(9, A.APROBAR)
            self.sembrar(10, A.DESCARTAR)

    def sembrar(self, n: int, accion: AccionRevision, **cambios: Any) -> int:
        base = valores_importados(self.revision._incidencias[UUID(int=n)])
        return self.revision.sembrar(UUID(int=n), accion, replace(base, **cambios))

    def normalizar(self, *, ensayo: bool, ahora: datetime = AHORA_N) -> ResultadoNormalizacion:
        return normalizar_ubicaciones(
            OBRA,
            revision=self.revision,
            catalogo=self.catalogo,
            ubicaciones=self.ubicaciones,
            ahora=ahora,
            ensayo=ensayo,
        )

    def ultima(self, n: int):
        return self.revision._ultima(UUID(int=n))


def _recuento(resultado: object) -> object:
    return getattr(resultado, "recuento", None)


# --------------------------------------------------------------------------
# R17 · el tope de la bandeja, antes de leer Sigrid
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ensayo", [True, False])
def test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe(ensayo: bool) -> None:
    mundo = Mundo()
    una = mundo.revision.listar(obra_codigo=OBRA, tope=1)[0]
    mundo.llamadas.clear()
    mundo.revision.topes.clear()
    mundo.revision.listar_devuelve = (una,) * (TOPE_LECTURA_OBRA + 1)
    mundo.revision.total_para_contar = 12_345
    antes = list(mundo.revision.guardadas)

    with pytest.raises(BandejaDemasiadoGrande) as exc:
        mundo.normalizar(ensayo=ensayo)

    assert exc.value.total == 12_345
    assert mundo.llamadas == ["revision.listar", "revision.contar"]
    assert mundo.revision.topes == [TOPE_LECTURA_OBRA]
    assert mundo.ubicaciones.catalogos == []
    assert mundo.revision.guardadas == antes


def test_f060_r17_justo_en_el_tope_si_se_normaliza() -> None:
    """10.000 son el máximo admitido, no uno de más (ensayo: el lote no se llama)."""
    mundo = Mundo()
    una = mundo.revision.listar(obra_codigo=OBRA, tope=1)[0]  # la 1, normalizable
    mundo.llamadas.clear()
    mundo.revision.listar_devuelve = (una,) * TOPE_LECTURA_OBRA

    resultado = mundo.normalizar(ensayo=True)

    assert getattr(_recuento(resultado), "examinadas", None) == TOPE_LECTURA_OBRA
    assert getattr(_recuento(resultado), "normalizables", None) == TOPE_LECTURA_OBRA
    assert mundo.llamadas == ["revision.listar", "ubicaciones"]


# --------------------------------------------------------------------------
# R18 · una lectura de las ubicaciones, con el catálogo recibido; el recuento
# --------------------------------------------------------------------------


def test_f060_r18_una_lectura_de_ubicaciones_con_el_catalogo_recibido() -> None:
    mundo = Mundo()

    mundo.normalizar(ensayo=False)

    assert mundo.llamadas == ["revision.listar", "ubicaciones", "revision.registrar_lote"]
    assert len(mundo.ubicaciones.catalogos) == 1
    assert mundo.ubicaciones.catalogos[0] is mundo.catalogo
    assert mundo.revision.topes == [TOPE_LECTURA_OBRA]


@pytest.mark.parametrize("ensayo", [True, False])
def test_f060_r10_r18_el_recuento_de_la_obra_y_su_suma(ensayo: bool) -> None:
    mundo = Mundo()

    recuento = _recuento(mundo.normalizar(ensayo=ensayo))

    assert recuento == RECUENTO_DE_DIEZ
    assert (
        RECUENTO_DE_DIEZ.normalizables
        + RECUENTO_DE_DIEZ.ambiguas
        + RECUENTO_DE_DIEZ.sin_coincidencia
        + RECUENTO_DE_DIEZ.no_editables
        == RECUENTO_DE_DIEZ.no_exactas
    )


def test_f060_r18_mira_la_lista_de_la_fuente_y_no_otra() -> None:
    """Con otra fuente, otro recuento: la lista es la que da la lectura."""
    mundo = Mundo(mapa={U1: ("baño",), U2: (), U3: ()})

    recuento = _recuento(mundo.normalizar(ensayo=True))

    # Con la lista de U1 = («baño»,): la 1, la 9 y la 10 son exactas; la 2 y la
    # 5, normalizables hacia «baño»; la 4 y la 7, sin coincidencia; la 3 (U2
    # vacía) y la 8 (U3 vacía), también sin coincidencia.
    assert recuento == RecuentoNormalizacion(
        examinadas=10,
        no_exactas=6,
        normalizables=2,
        ambiguas=0,
        sin_coincidencia=4,
        no_editables=0,
    )


# --------------------------------------------------------------------------
# R19 · el ensayo
# --------------------------------------------------------------------------


def test_f060_r19_el_ensayo_no_llama_al_lote_ni_escribe() -> None:
    mundo = Mundo()
    antes = list(mundo.revision.guardadas)

    resultado = mundo.normalizar(ensayo=True)

    assert mundo.llamadas == ["revision.listar", "ubicaciones"]
    assert mundo.revision.lotes == []
    assert mundo.revision.guardadas == antes
    assert resultado == ResultadoNormalizacion(
        obra_codigo=OBRA,
        ensayo=True,
        recuento=RECUENTO_DE_DIEZ,
        normalizadas=0,
        conflictos=0,
    )


# --------------------------------------------------------------------------
# R20 · la normalización real
# --------------------------------------------------------------------------


def test_f060_r20_la_real_registra_el_lote_del_plan() -> None:
    mundo = Mundo()
    antes = len(mundo.revision.guardadas)

    resultado = mundo.normalizar(ensayo=False)

    assert resultado == ResultadoNormalizacion(
        obra_codigo=OBRA,
        ensayo=False,
        recuento=RECUENTO_DE_DIEZ,
        normalizadas=3,
        conflictos=0,
    )
    assert len(mundo.revision.lotes) == 1
    revisiones, esperadas = mundo.revision.lotes[0]
    assert [r.incidencia_id for r in revisiones] == [UUID(int=1), UUID(int=2), UUID(int=3)]
    assert [r.valores.ubicacion for r in revisiones] == ["Baño", "Baño", "Terraza"]
    assert {r.accion for r in revisiones} == {A.EDITAR}
    assert {r.quien for r in revisiones} == {QUIEN_SISTEMA}
    assert {r.revisado_at_utc for r in revisiones} == {AHORA_N}
    assert {r.motivo for r in revisiones} == {None}
    assert all(r.huella == huella_de_valores(r.valores) for r in revisiones)
    assert esperadas == {UUID(int=1): None, UUID(int=2): None, UUID(int=3): None}
    nuevas = mundo.revision.guardadas[antes:]
    assert [(g.revision.incidencia_id, g.oid, g.revision.correo) for g in nuevas] == [
        (UUID(int=n), TEXTO_SISTEMA, TEXTO_SISTEMA) for n in (1, 2, 3)
    ]


def test_f060_r9_r20_la_esperada_es_la_ultima_leida() -> None:
    """Una editada antes por una persona: su esperada es esa revisión."""
    mundo = Mundo()
    humana = mundo.sembrar(1, A.EDITAR, descripcion="Otra descripción de ejemplo")

    mundo.normalizar(ensayo=False)

    assert len(mundo.revision.lotes) == 1
    _, esperadas = mundo.revision.lotes[0]
    assert esperadas[UUID(int=1)] == humana
    ultima = mundo.ultima(1)
    assert (ultima.correo, ultima.valores.ubicacion) == (TEXTO_SISTEMA, "Baño")
    assert ultima.valores.descripcion == "Otra descripción de ejemplo"


def test_f060_r13_r20_un_conflicto_se_cuenta_y_no_aborta_las_demas() -> None:
    mundo = Mundo()
    mundo.revision.antes_del_lote = lambda: mundo.sembrar(
        2, A.EDITAR, descripcion="Otra descripción de ejemplo"
    )

    resultado = mundo.normalizar(ensayo=False)

    assert (getattr(resultado, "normalizadas", None), getattr(resultado, "conflictos", None)) == (2, 1)
    recuento = _recuento(resultado)
    assert resultado.normalizadas + resultado.conflictos == getattr(recuento, "normalizables", None)
    assert mundo.ultima(2).correo == CORREO  # la de la persona sigue siendo la última
    assert mundo.ultima(1).correo == TEXTO_SISTEMA
    assert mundo.ultima(3).correo == TEXTO_SISTEMA


def test_f060_r20_un_plan_vacio_no_llama_al_lote() -> None:
    mundo = Mundo(
        incidencia(5, ubicacion="Baño"),
        incidencia(7, ubicacion="Sala Ejemplo"),
        incidencia(4, ubicacion="COCINA"),
    )

    resultado = mundo.normalizar(ensayo=False)

    assert mundo.llamadas == ["revision.listar", "ubicaciones"]
    assert resultado == ResultadoNormalizacion(
        obra_codigo=OBRA,
        ensayo=False,
        recuento=RecuentoNormalizacion(3, 2, 0, 1, 1, 0),
        normalizadas=0,
        conflictos=0,
    )


# --------------------------------------------------------------------------
# R21 · idempotencia
# --------------------------------------------------------------------------


def test_f060_r21_dos_ejecuciones_la_segunda_no_tiene_nada_que_normalizar() -> None:
    mundo = Mundo()
    mundo.normalizar(ensayo=False)
    tras_la_primera = len(mundo.revision.guardadas)
    mundo.llamadas.clear()

    segunda = mundo.normalizar(ensayo=False)

    assert getattr(_recuento(segunda), "normalizables", None) == 0
    assert getattr(_recuento(segunda), "examinadas", None) == 10
    assert getattr(_recuento(segunda), "no_exactas", None) == 5  # 4, 7, 8, 9 y 10
    assert (segunda.normalizadas, segunda.conflictos) == (0, 0)
    assert mundo.llamadas == ["revision.listar", "ubicaciones"]
    assert len(mundo.revision.guardadas) == tras_la_primera
    assert tras_la_primera == 2 + 3


# --------------------------------------------------------------------------
# R22, R23 · cómo lo ve la revisión de F-056 (sus handlers, sin tocarlos)
# --------------------------------------------------------------------------


def _listado(mundo: Mundo) -> dict[str, Any]:
    return handlers_de_f056.listar_revision(
        OBRA,
        "todas",
        revision=mundo.revision,
        catalogo_obra=CatalogoDeLaObra(mundo.llamadas),
        equivalencias=EquivalenciasEnMemoria(mundo.llamadas),
        ubicaciones=mundo.ubicaciones,
        configuracion=CONFIG,
    )


def _fila(listado: dict[str, Any], n: int) -> dict[str, Any]:
    return next(f for f in listado["incidencias"] if f["incidencia_id"] == str(UUID(int=n)))


def test_f060_r22_la_fila_normalizada_en_el_listado_y_su_historial() -> None:
    mundo = Mundo()
    mundo.normalizar(ensayo=False)

    fila = _fila(_listado(mundo), 1)
    historial = handlers_de_f056.historial_revision(str(UUID(int=1)), revision=mundo.revision)

    assert fila["vigentes"]["ubicacion"] == "Baño"
    assert fila["importados"]["ubicacion"] == "baño"
    assert fila["cambios"] == ["ubicacion"]
    assert fila["estado"] == "editada"
    assert fila["revisado_por"] == TEXTO_SISTEMA
    assert fila["revisado_at_utc"] == "2026-10-10T07:00:00.000000+00:00"
    assert "ubicacion_fuera_de_lista" not in fila["motivos_no_aprobable"]
    assert fila["motivos_no_aprobable"] == []
    ultima = historial["revisiones"][-1]
    assert (ultima["accion"], ultima["correo"], ultima["campos_cambiados"]) == (
        "editar",
        TEXTO_SISTEMA,
        ["ubicacion"],
    )
    assert len(historial["revisiones"]) == 1


def test_f060_r22_el_resumen_baja_en_las_normalizadas() -> None:
    mundo = Mundo()
    antes = _listado(mundo)["resumen"]

    resultado = mundo.normalizar(ensayo=False)
    despues = _listado(mundo)["resumen"]

    fuera = "ubicacion_fuera_de_lista"
    assert despues["por_motivo"][fuera] == antes["por_motivo"][fuera] - resultado.normalizadas
    assert despues["por_estado"]["editada"] == antes["por_estado"]["editada"] + 3
    assert despues["por_estado"]["nueva"] == antes["por_estado"]["nueva"] - 3


def test_f060_r7_r23_lo_que_no_se_normaliza_sigue_como_estaba() -> None:
    mundo = Mundo()
    antes = _listado(mundo)

    resultado = mundo.normalizar(ensayo=False)
    despues = _listado(mundo)

    assert getattr(resultado, "normalizadas", None) == 3
    for n in (4, 7, 8):  # ambigua, sin coincidencia, lista vacía
        fila = _fila(despues, n)
        assert (fila["estado"], fila["revision_id"]) == ("nueva", None)
        assert "ubicacion_fuera_de_lista" in fila["motivos_no_aprobable"]
        assert fila == _fila(antes, n)
    for n, estado in ((9, "aprobada"), (10, "descartada")):  # no editables
        fila = _fila(despues, n)
        assert fila["estado"] == estado
        assert fila == _fila(antes, n)
        assert fila["revisado_por"] == CORREO


# --------------------------------------------------------------------------
# R24, R25 · lo aprobado, y la comparación de F-056 que no cambia
# --------------------------------------------------------------------------


def _actuar(mundo: Mundo, accion: AccionRevision, *, previa: int | None, valores=None):
    return aplicar_accion(
        PeticionDeAccion(
            incidencia_id=UUID(int=1),
            accion=accion,
            quien=QUIEN,
            revision_previa=previa,
            valores=valores,
        ),
        revision=mundo.revision,
        catalogo_obra=CatalogoDeLaObra(mundo.llamadas),
        listas=LISTAS,
        ahora=AHORA,
        ubicaciones=mundo.ubicaciones,
    )


def test_f060_r24_normalizar_y_aprobar_da_la_candidata_con_el_texto_de_sigrid() -> None:
    mundo = Mundo()
    resultado = mundo.normalizar(ensayo=False)
    assert getattr(resultado, "normalizadas", None) == 3
    previa = mundo.ultima(1).revision_id

    _actuar(mundo, A.APROBAR, previa=previa)
    candidatas = {
        c.incidencia_id: c for c in candidatas_al_volcado(OBRA, revision=mundo.revision)
    }

    assert UUID(int=1) in candidatas
    assert candidatas[UUID(int=1)].valores.ubicacion == "Baño"
    assert candidatas[UUID(int=1)].huella == huella_de_valores(candidatas[UUID(int=1)].valores)
    aprobacion = mundo.ultima(1)
    assert (aprobacion.accion, aprobacion.correo, aprobacion.valores.ubicacion) == (
        A.APROBAR,
        CORREO,
        "Baño",
    )


def test_f060_r25_sin_normalizar_aprobar_sigue_siendo_409() -> None:
    """Guarda de D-5: aprobar no normaliza al vuelo (pasa también en RED)."""
    mundo = Mundo()

    with pytest.raises(IncidenciaNoAprobable) as exc:
        _actuar(mundo, A.APROBAR, previa=None)

    assert "ubicacion_fuera_de_lista" in exc.value.motivos
    assert mundo.ultima(1) is None


@pytest.mark.parametrize("variante", ["BAÑO", "bAño"])
def test_f060_r25_editar_con_la_variante_sigue_siendo_400(variante: str) -> None:
    """Guarda de D-5: editar no normaliza al vuelo (pasa también en RED).

    Las dos variantes difieren de la importada («baño»), para que el 400 sea
    el de la ubicación y no `sin_cambios`.
    """
    mundo = Mundo()
    pedidos = ValoresPedidos(
        unidad_codigo=U1,
        ubicacion=variante,
        descripcion=DESCRIPCION,
        detalle=None,
        oficio_codigo="0046",
        proveedor_codigo="EJ07",
        urgencia=None,
        listado=None,
    )

    with pytest.raises(ValoresNoValidos) as exc:
        _actuar(mundo, A.EDITAR, previa=None, valores=pedidos)

    assert [campo for campo, _ in exc.value.errores] == ["ubicacion"]


# --------------------------------------------------------------------------
# O-3 (reviews de los Bloques 1 y 2) · las listas, de la fuente de F-056
# --------------------------------------------------------------------------


class PuertoDeUbicaciones:
    """Un `UbicacionesValidasPort`: el `prmtpl.ubica` crudo de cada unidad."""

    def __init__(self, llamadas: list[str], ubica: dict[str, str | None]) -> None:
        self.llamadas = llamadas
        self.ubica = ubica

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        self.llamadas.append("ubicaciones.leer")
        return LecturaCatalogo(
            tuple(FilaUbicacionesUnidad(u, texto) for u, texto in self.ubica.items()), False
        )


def _de_49() -> tuple[str, str]:
    """Un texto de 48 y un valor de Sigrid de 49 con la misma clave («ß» → «ss»)."""
    cola = "x" * (MAX_UBICACION - len("Straße Ejemplo "))
    texto = "Straße Ejemplo " + cola
    valor = "Strasse Ejemplo " + cola
    assert (len(texto), len(valor)) == (MAX_UBICACION, MAX_UBICACION + 1)
    return texto, valor


def test_f060_o3_el_detector_no_es_ciego_sin_filtro_se_propondria_el_de_49() -> None:
    """Control: sin el filtro de F-056, la regla propondría el valor de 49."""
    texto, valor = _de_49()

    clasificada = ubicacion_de_sigrid(texto, (valor,))

    assert (clasificada.coincidencia, clasificada.texto) == (Coincidencia.NORMALIZABLE, valor)


def test_f060_o3_las_listas_salen_de_la_fuente_de_f056_ya_filtradas() -> None:
    """Un valor de más de 48 no llega al plan: no tumba el lote con el `CHECK`."""
    texto, valor = _de_49()
    llamadas: list[str] = []
    revision = RevisionConLote(
        llamadas,
        (incidencia(1, ubicacion=texto), incidencia(2, ubicacion="SALA EJEMPLO")),
    )
    puerto = PuertoDeUbicaciones(llamadas, {U1: f"{valor};Sala Ejemplo", U2: None})
    catalogo = leer_catalogo(CatalogoDeLaObra([]), OBRA)

    resultado = normalizar_ubicaciones(
        OBRA,
        revision=revision,
        catalogo=catalogo,
        ubicaciones=fuente_de_ubicaciones(puerto),
        ahora=AHORA_N,
        ensayo=False,
    )

    assert _recuento(resultado) == RecuentoNormalizacion(2, 2, 1, 0, 1, 0)
    assert llamadas == ["revision.listar", "ubicaciones.leer", "revision.registrar_lote"]
    revisiones, _ = revision.lotes[0]
    assert [(r.incidencia_id, r.valores.ubicacion) for r in revisiones] == [
        (UUID(int=2), "Sala Ejemplo")
    ]
    assert all(len(r.valores.ubicacion) <= MAX_UBICACION for r in revisiones)


# --------------------------------------------------------------------------
# Los fallos suben tal cual, sin nada escrito
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fallo",
    [CatalogoNoDisponible("caída de prueba"), CatalogoSinVerificar("al techo de prueba")],
    ids=["sigrid-caido", "al-techo"],
)
def test_f060_r28_un_fallo_de_las_ubicaciones_sube_sin_escribir(fallo: Exception) -> None:
    mundo = Mundo()
    mundo.ubicaciones._fallo = fallo
    antes = list(mundo.revision.guardadas)

    with pytest.raises(type(fallo)):
        mundo.normalizar(ensayo=False)

    assert mundo.llamadas == ["revision.listar", "ubicaciones"]
    assert mundo.revision.guardadas == antes


def test_f060_r14_un_fallo_de_la_base_en_el_lote_sube_sin_nada_escrito() -> None:
    """O-3 de la review del Bloque 2: un `CHECK` que falla tumba el lote entero."""
    mundo = Mundo()
    mundo.revision.fallo_del_lote = PersistenciaNoDisponible("registrar_lote: CheckViolation")
    antes = list(mundo.revision.guardadas)

    with pytest.raises(PersistenciaNoDisponible):
        mundo.normalizar(ensayo=False)

    assert mundo.llamadas == ["revision.listar", "ubicaciones", "revision.registrar_lote"]
    assert mundo.revision.guardadas == antes


def test_f060_r17_un_fallo_de_la_base_al_listar_sube_sin_leer_sigrid() -> None:
    mundo = Mundo()
    mundo.revision._fallo = PersistenciaNoDisponible("listar: caída de prueba")

    with pytest.raises(PersistenciaNoDisponible):
        mundo.normalizar(ensayo=False)

    assert mundo.llamadas == ["revision.listar"]
    assert mundo.ubicaciones.catalogos == []


# --------------------------------------------------------------------------
# El tipo del resultado
# --------------------------------------------------------------------------


def test_f060_el_resultado_es_inmutable() -> None:
    resultado = Mundo().normalizar(ensayo=True)

    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.normalizadas = 7  # type: ignore[misc]


def test_f060_el_resultado_no_lleva_textos() -> None:
    """Lo que devuelve la aplicación son recuentos: ningún texto ni identificador."""
    resultado = Mundo().normalizar(ensayo=False)

    plano = json.dumps(dataclasses.asdict(resultado), default=str)

    for prohibido_en_el_resultado in ("Baño", "baño", "Terraza", DESCRIPCION, TEXTO_SISTEMA, str(UUID(int=1))):
        assert prohibido_en_el_resultado not in plano
    assert getattr(resultado, "normalizadas", None) == 3
