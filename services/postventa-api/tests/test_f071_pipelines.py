# services/postventa-api/tests/test_f071_pipelines.py
"""La aplicación de la plantilla v2 y de su importación (F-071 T7).

`specs/F-071-plantilla-desde-sigrid/design.md` §6, sobre
`application/pipelines/plantilla.py` y `application/pipelines/paso_importacion.py`,
con dobles que anotan en una lista común (sin red, sin base, sin Sigrid):

| Caso | Requisito |
|---|---|
| plantilla: catálogo → ubicaciones (una vez, con el catálogo leído) → generador | R1 |
| plantilla: sin `EquivalenciasPort` en la firma; las listas, de lo leído | R2 |
| plantilla: lectura al techo → 409 y fallo → 503, sin fichero | R3 |
| importación: catálogo → ubicaciones, una vez, sin equivalencias | R24 |
| importación: con `ya_importado`, ni catálogo ni ubicaciones | R24 |
| importación: lectura al techo o fallo sube sin registrar nada | R25 |
| Excel de errores con las mismas ubicaciones, sin otra lectura | R40 |
| logs: solo recuentos, ni ubicaciones ni nombres | R44 |

Datos ficticios: obra `9901`, «Vivienda N», «Estancia A-NN», «Oficio ficticio
N», «Proveedor ficticio N».
"""

from __future__ import annotations

import inspect
import logging
from datetime import UTC, datetime
from uuid import UUID

import pytest
from application.pipelines import paso_importacion
from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.contexto_importacion import ContextoImportacion
from application.pipelines.paso_importacion import (
    paso_catalogo,
    paso_excel_errores,
    paso_huella,
    paso_reconocimiento,
    paso_registro,
    paso_validacion,
)
from application.pipelines.plantilla import generar_plantilla
from domain.models.errores import CatalogoNoDisponible, CatalogoSinVerificar
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    UbicacionesPorUnidad,
    oficios_del_desplegable,
    pares_del_desplegable,
    ubicaciones_de_la_plantilla,
)
from domain.ports.catalogo_obra import (
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos.excel_openpyxl import (
    GeneradorPlantillaOpenpyxl,
    LectorPlantillaOpenpyxl,
)

from tests.utiles_importacion import BandejaEnMemoria, TiposEnMemoria
from tests.utiles_plantilla import configuracion

AHORA = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)
OBRA = "9901"
OBRA_REF = "990100001"  # `upv.obride` inventado
U1, U2, U3 = "9901.0001", "9901.0002", "9901.0003"
NOMBRES = {U1: "Vivienda 1", U2: "Vivienda 2", U3: "Vivienda 3"}

#: Vivienda 3 sin ubicaciones (R7).
MAPA: UbicacionesPorUnidad = {
    U1: ("Estancia A-01", "Estancia A-02"),
    U2: ("Estancia A-03",),
    U3: (),
}

#: Lo que nunca puede ir a un log (R44): ubicaciones y nombres.
SECRETOS = (
    "Estancia A-0",
    "Vivienda",
    "Oficio ficticio",
    "Proveedor ficticio",
)


class Catalogo:
    """Un `CatalogoObraPort` de la obra 9901, anotando cada lectura."""

    def __init__(self, llamadas: list[str]) -> None:
        self.llamadas = llamadas

    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]:
        self.llamadas.append("catalogo.leer_unidades")
        return LecturaCatalogo(
            tuple(
                FilaUnidadCatalogo(
                    obra_ref=OBRA_REF,
                    obra_codigo=OBRA,
                    obra_nombre="Obra ficticia",
                    unidad_codigo=codigo,
                    unidad_nombre=nombre,
                )
                for codigo, nombre in NOMBRES.items()
            ),
            False,
        )

    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]:
        self.llamadas.append("catalogo.leer_oficios")
        return LecturaCatalogo(
            (
                FilaOficioCatalogo("0001", "Oficio ficticio 1", "P001", "Proveedor ficticio 1"),
                FilaOficioCatalogo("0002", "Oficio ficticio 2", None, None),
            ),
            False,
        )


class Ubicaciones:
    """La fuente de las ubicaciones válidas: anota cada lectura y su catálogo."""

    def __init__(
        self,
        llamadas: list[str],
        mapa: UbicacionesPorUnidad = MAPA,
        *,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self.mapa = mapa
        self.fallo = fallo
        self.catalogos: list[CatalogoObra] = []

    def __call__(self, catalogo: CatalogoObra) -> UbicacionesPorUnidad:
        self.llamadas.append("ubicaciones")
        self.catalogos.append(catalogo)
        if self.fallo is not None:
            raise self.fallo
        return self.mapa


class Generador:
    """El generador de verdad, anotando cada llamada y sus argumentos."""

    def __init__(self, llamadas: list[str]) -> None:
        self.llamadas = llamadas
        self.argumentos: list[dict[str, object]] = []

    def generar(self, **argumentos: object) -> bytes:
        self.llamadas.append("generador.generar")
        self.argumentos.append(argumentos)
        return GeneradorPlantillaOpenpyxl().generar(**argumentos)  # type: ignore[arg-type]


def _plantilla(llamadas: list[str], ubicaciones: Ubicaciones) -> tuple[str, bytes]:
    config = configuracion()
    return generar_plantilla(
        OBRA,
        catalogo_obra=Catalogo(llamadas),
        ubicaciones=ubicaciones,
        tipos=TiposEnMemoria(),  # F-072 R1
        generador=Generador(llamadas),
        listas=config.listas,
        textos=config.textos,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R1–R3 · la plantilla
# --------------------------------------------------------------------------


def test_f071_r1_catalogo_y_despues_una_lectura_de_ubicaciones() -> None:
    llamadas: list[str] = []
    ubicaciones = Ubicaciones(llamadas)
    generador = Generador(llamadas)
    config = configuracion()
    nombre, contenido = generar_plantilla(
        OBRA,
        catalogo_obra=Catalogo(llamadas),
        ubicaciones=ubicaciones,
        tipos=TiposEnMemoria(),  # F-072 R1
        generador=generador,
        listas=config.listas,
        textos=config.textos,
        ahora=AHORA,
    )
    assert llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "generador.generar",
    ]
    (catalogo,) = ubicaciones.catalogos
    assert catalogo.obra_codigo == OBRA
    assert [u.codigo for u in catalogo.unidades] == [U1, U2, U3]
    (argumentos,) = generador.argumentos
    assert argumentos["catalogo"] is catalogo
    assert argumentos["ubicaciones"] == ubicaciones_de_la_plantilla(catalogo.unidades, MAPA)
    assert nombre == "plantilla_incidencias_9901_20261106.xlsx"
    assert LectorPlantillaOpenpyxl().leer(contenido=contenido).version == 2


def test_f071_r2_la_plantilla_no_lee_equivalencias() -> None:
    parametros = inspect.signature(generar_plantilla).parameters
    assert "equivalencias" not in parametros
    assert "ubicaciones" in parametros
    llamadas: list[str] = []
    generador = Generador(llamadas)
    config = configuracion()
    generar_plantilla(
        OBRA,
        catalogo_obra=Catalogo(llamadas),
        ubicaciones=Ubicaciones(llamadas),
        tipos=TiposEnMemoria(),  # F-072 R1
        generador=generador,
        listas=config.listas,
        textos=config.textos,
        ahora=AHORA,
    )
    (argumentos,) = generador.argumentos
    assert [o.etiqueta for o in argumentos["oficios"]] == [
        "Oficio ficticio 1 (0001)",
        "Oficio ficticio 2 (0002)",
    ]
    assert [p.etiqueta for p in argumentos["pares"]] == [
        "Oficio ficticio 1 (0001) · Proveedor ficticio 1 (P001)"
    ]


@pytest.mark.parametrize(
    "fallo",
    [CatalogoSinVerificar("al techo de prueba"), CatalogoNoDisponible("caído de prueba")],
    ids=["techo_409", "fallo_503"],
)
def test_f071_r3_la_lectura_de_ubicaciones_que_falla_no_da_fichero(fallo) -> None:
    llamadas: list[str] = []
    with pytest.raises(type(fallo)):
        _plantilla(llamadas, Ubicaciones(llamadas, fallo=fallo))
    assert "generador.generar" not in llamadas
    assert llamadas.count("ubicaciones") == 1


def test_f071_r44_el_log_de_la_plantilla_solo_lleva_recuentos(caplog) -> None:
    llamadas: list[str] = []
    with caplog.at_level(logging.INFO):
        _plantilla(llamadas, Ubicaciones(llamadas))
    (linea,) = [r.getMessage() for r in caplog.records if "plantilla generada" in r.getMessage()]
    assert "listas_ubicaciones=2" in linea
    assert "unidades_sin_ubicaciones=1" in linea
    assert "oficios=2" in linea
    assert "pares=1" in linea
    for registro in caplog.records:
        for secreto in SECRETOS:
            assert secreto not in registro.getMessage(), registro.getMessage()


# --------------------------------------------------------------------------
# R24, R25, R40 · la importación
# --------------------------------------------------------------------------


def _fichero(*filas: FilaPlantilla) -> bytes:
    """Una plantilla v2 de la 9901, con las ubicaciones de `MAPA`."""
    llamadas: list[str] = []
    config = configuracion()
    catalogo = leer_catalogo(Catalogo(llamadas), OBRA)
    oficios = oficios_del_desplegable(catalogo)
    return GeneradorPlantillaOpenpyxl().generar(
        catalogo=catalogo,
        oficios=oficios,
        pares=pares_del_desplegable(catalogo, oficios),
        ubicaciones=ubicaciones_de_la_plantilla(catalogo.unidades, MAPA),
        listas=config.listas,
        textos=config.textos,
        generada_at=AHORA,
        filas=filas,
    )


BUENA = FilaPlantilla(
    valores={
        "Unidad": "Vivienda 1",
        "Ubicación": "Estancia A-01",
        "Descripción corta": "Defecto ficticio 1",
        "Oficio": "Oficio ficticio 1 (0001)",
    }
)
#: La ubicación es de otra unidad (R29): va al Excel de errores.
MALA = FilaPlantilla(
    valores={
        "Unidad": "Vivienda 2",
        "Ubicación": "Estancia A-01",
        "Descripción corta": "Defecto ficticio 2",
    }
)


def _hasta_el_catalogo(
    contenido: bytes, llamadas: list[str], bandeja: BandejaEnMemoria
) -> ContextoImportacion:
    contexto = ContextoImportacion(
        contenido=contenido,
        nombre_fichero="ficticio.xlsx",
        usuario_oid="oid-ficticio",
        ahora=AHORA,
    )
    contexto = paso_huella(contexto, bandeja)
    return paso_reconocimiento(contexto, LectorPlantillaOpenpyxl())


def test_f071_r24_paso_catalogo_lee_el_catalogo_y_una_vez_las_ubicaciones() -> None:
    parametros = list(inspect.signature(paso_catalogo).parameters)
    # F-072 R11: el paso lee además los tipos de reclamación, tras las ubicaciones.
    assert parametros == ["contexto", "catalogo_obra", "ubicaciones", "tipos"]
    llamadas: list[str] = []
    contexto = _hasta_el_catalogo(_fichero(BUENA), llamadas, BandejaEnMemoria([]))
    ubicaciones = Ubicaciones(llamadas)
    contexto = paso_catalogo(contexto, Catalogo(llamadas), ubicaciones, TiposEnMemoria())
    assert llamadas == ["catalogo.leer_unidades", "catalogo.leer_oficios", "ubicaciones"]
    assert ubicaciones.catalogos == [contexto.catalogo]
    assert contexto.ubicaciones_por_unidad == MAPA
    assert [o.etiqueta for o in contexto.oficios] == [
        "Oficio ficticio 1 (0001)",
        "Oficio ficticio 2 (0002)",
    ]
    # Sin los grupos de equivalencia (D-14): el contexto ya no los guarda.
    for campo in ("grupos_oficio", "grupos_proveedor", "opciones_oficio", "opciones_proveedor"):
        assert not hasattr(contexto, campo), campo
    assert not hasattr(paso_importacion, "opciones_de_la_obra")


def test_f071_r24_con_ya_importado_ni_catalogo_ni_ubicaciones() -> None:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria([])
    contenido = _fichero(BUENA)
    # Una primera importación completa deja el atajo de R39.
    primero = _hasta_el_catalogo(contenido, [], bandeja)
    primero = paso_catalogo(primero, Catalogo([]), Ubicaciones([]), TiposEnMemoria())
    primero = paso_validacion(primero, configuracion().listas)
    paso_registro(primero, bandeja, nuevo_id=lambda: UUID(int=1))

    segundo = _hasta_el_catalogo(contenido, llamadas, bandeja)
    assert segundo.ya_importado
    paso_catalogo(segundo, Catalogo(llamadas), Ubicaciones(llamadas), TiposEnMemoria())
    assert llamadas == []


@pytest.mark.parametrize(
    "fallo",
    [CatalogoSinVerificar("al techo de prueba"), CatalogoNoDisponible("caído de prueba")],
    ids=["techo_409", "fallo_503"],
)
def test_f071_r25_la_lectura_de_ubicaciones_que_falla_no_deja_validar_ni_registrar(
    fallo,
) -> None:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria(llamadas)
    contexto = _hasta_el_catalogo(_fichero(BUENA, MALA), llamadas, bandeja)
    with pytest.raises(type(fallo)):
        paso_catalogo(contexto, Catalogo(llamadas), Ubicaciones(llamadas, fallo=fallo), TiposEnMemoria())
    assert contexto.validas is None
    assert bandeja.registradas == []


def test_f071_r40_el_excel_de_errores_usa_las_ubicaciones_ya_leidas() -> None:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria(llamadas)
    config = configuracion()
    contexto = _hasta_el_catalogo(_fichero(BUENA, MALA), llamadas, bandeja)
    ubicaciones = Ubicaciones(llamadas)
    contexto = paso_catalogo(contexto, Catalogo(llamadas), ubicaciones, TiposEnMemoria())
    contexto = paso_validacion(contexto, config.listas)
    assert [v.fila for v in contexto.validas] == [2]
    assert [f.fila.numero for f in contexto.con_error] == [3]
    contexto = paso_registro(contexto, bandeja, nuevo_id=lambda: UUID(int=2))
    generador = Generador(llamadas)
    contexto = paso_excel_errores(contexto, generador, config.listas, config.textos)
    assert llamadas.count("ubicaciones") == 1
    (argumentos,) = generador.argumentos
    assert argumentos["ubicaciones"] == ubicaciones_de_la_plantilla(
        contexto.catalogo.unidades, MAPA
    )
    assert argumentos["oficios"] == contexto.oficios
    assert argumentos["pares"] == contexto.pares
    libro = LectorPlantillaOpenpyxl().leer(contenido=contexto.excel_errores.contenido)
    assert libro.version == 2
    (fila,) = libro.filas
    assert fila.celdas["Ubicación"].texto_original == "Estancia A-01"
    assert fila.celdas["Unidad"].texto_original == "Vivienda 2"


def test_f071_r44_el_log_de_la_importacion_solo_lleva_recuentos(caplog) -> None:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria(llamadas)
    config = configuracion()
    with caplog.at_level(logging.INFO):
        contexto = _hasta_el_catalogo(_fichero(BUENA, MALA), llamadas, bandeja)
        contexto = paso_catalogo(contexto, Catalogo(llamadas), Ubicaciones(llamadas), TiposEnMemoria())
        contexto = paso_validacion(contexto, config.listas)
        contexto = paso_registro(contexto, bandeja, nuevo_id=lambda: UUID(int=3))
        paso_excel_errores(contexto, Generador(llamadas), config.listas, config.textos)
    (linea,) = [r.getMessage() for r in caplog.records if "catálogo leído" in r.getMessage()]
    assert "listas_ubicaciones=2" in linea
    assert "unidades_sin_ubicaciones=1" in linea
    assert "oficios=2" in linea
    assert "pares=1" in linea
    for registro in caplog.records:
        for secreto in SECRETOS:
            assert secreto not in registro.getMessage(), registro.getMessage()
