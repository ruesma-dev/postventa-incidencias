# services/postventa-api/tests/test_f036_catalogo_aplicacion.py
"""Leer el catálogo de una obra: las decisiones de la aplicación (F-036 T13).

`application/pipelines/catalogo_obra.py`, según
`specs/F-036-importar-excel/design.md` §7.1: lee las unidades y decide

- techo alcanzado → `CatalogoSinVerificar` (R10, 409), sin leer los oficios;
- cero filas → `ObraSinUnidades` (R10, 404);
- más de una obra distinta → `ObraAmbigua` (R10, 409), sin leer los oficios;

y con **la** obra lee sus oficios (techo → `CatalogoSinVerificar`) y compone el
`CatalogoObra`. Una obra sin oficios da un catálogo sin oficios (R12): la
plantilla se genera igual. Los fallos de Sigrid (`CatalogoNoDisponible`, R11)
suben tal cual. Un código de obra inadmisible es R9: sin llamar a Sigrid.

Con un doble del puerto en memoria: la aplicación no sabe que debajo hay una
pasarela. Al final, dos pruebas de punta a punta con el adaptador real sobre
el `ClienteFalso`. Ni un dato real: la referencia de obra y los nombres son
inventados.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest

from application.pipelines import catalogo_obra as modulo
from application.pipelines.catalogo_obra import leer_catalogo
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    CodigoDeObraInvalido,
    ObraAmbigua,
    ObraSinUnidades,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    ProveedorEnObra,
    UnidadPosventa,
    etiquetas_de_unidades,
)
from domain.ports.catalogo_obra import (
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from infrastructure.sigrid.catalogo_obra import AdaptadorCatalogoSigridApi
from tests.utiles_plantilla import opciones
from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

SERVICIO = Path(__file__).resolve().parents[1]
MODULO = SERVICIO / "application" / "pipelines" / "catalogo_obra.py"

#: Referencias de obra (`upv.obride`) **inventadas**, que se buscan en los logs.
OBRA_REF = "987654321"
OTRA_OBRA_REF = "123456789"

#: Textos **inventados** que no pueden salir en un log (R47).
UNIDAD_LIBRE = "Villa 5 - llamar a Fulanita de Tal"
PROVEEDOR = "Juan Ejemplo Ejemplo"
CODIGO_PROVEEDOR = "P0042-EJEMPLO"


#: «Sin decir»: el código de unidad por defecto (`None` y `""` son casos).
_POR_DEFECTO = object()


def _unidad(
    n: int, *, obra_ref: str = OBRA_REF, codigo=_POR_DEFECTO, nombre=None
) -> FilaUnidadCatalogo:
    return FilaUnidadCatalogo(
        obra_ref=obra_ref,
        obra_codigo="0677",
        obra_nombre="OBRA EJEMPLO",
        unidad_codigo=f"0677.03VILLA {n}." if codigo is _POR_DEFECTO else codigo,
        unidad_nombre=f"Villa {n}" if nombre is None else nombre,
    )


OFICIOS_0677 = (
    FilaOficioCatalogo("0101", "CARPINTERÍA", "P0001", "Carpinterías Ejemplo S.L."),
    FilaOficioCatalogo("0101", "CARPINTERÍA", "P0002", "Mamparas Ejemplo S.A."),
    FilaOficioCatalogo("0102", "FONTANERÍA", "P0003", PROVEEDOR),
    FilaOficioCatalogo("0133", "PINTURA", None, None),
)


class CatalogoEnMemoria:
    """Un `CatalogoObraPort` de mentira que recuerda lo que le pidieron."""

    def __init__(
        self,
        unidades: tuple = (),
        oficios: tuple = OFICIOS_0677,
        *,
        unidades_al_techo: bool = False,
        oficios_al_techo: bool = False,
        fallo_unidades: Exception | None = None,
        fallo_oficios: Exception | None = None,
    ) -> None:
        self._unidades = LecturaCatalogo(tuple(unidades), unidades_al_techo)
        self._oficios = LecturaCatalogo(tuple(oficios), oficios_al_techo)
        self._fallo_unidades = fallo_unidades
        self._fallo_oficios = fallo_oficios
        self.llamadas: list[tuple[str, str]] = []

    def leer_unidades(self, *, codigo_obra: str):
        self.llamadas.append(("unidades", codigo_obra))
        if self._fallo_unidades:
            raise self._fallo_unidades
        return self._unidades

    def leer_oficios(self, *, obra_ref: str):
        self.llamadas.append(("oficios", obra_ref))
        if self._fallo_oficios:
            raise self._fallo_oficios
        return self._oficios


def _obra_0677(**kwargs) -> CatalogoEnMemoria:
    return CatalogoEnMemoria(tuple(_unidad(n) for n in range(1, 16)), **kwargs)


@pytest.fixture
def registros():
    """Todo lo que se registre en cualquier logger, en texto, a nivel DEBUG."""
    lineas: list[str] = []
    manejador = logging.Handler(level=logging.DEBUG)
    manejador.emit = lambda registro: lineas.append(  # type: ignore[method-assign]
        f"{registro.name} {registro.getMessage()}"
    )
    raiz = logging.getLogger()
    nivel = raiz.level
    raiz.addHandler(manejador)
    raiz.setLevel(logging.DEBUG)
    try:
        yield lineas
    finally:
        raiz.setLevel(nivel)
        raiz.removeHandler(manejador)


# ==========================================================================
# El camino bueno: una obra, sus unidades, sus oficios y sus proveedores
# ==========================================================================


def test_f036_t13_la_0677_compone_su_catalogo():
    puerto = _obra_0677()

    catalogo = leer_catalogo(puerto, "0677")

    assert catalogo == CatalogoObra(
        obra_codigo="0677",
        obra_nombre="OBRA EJEMPLO",
        unidades=tuple(
            UnidadPosventa(f"0677.03VILLA {n}.", f"Villa {n}") for n in range(1, 16)
        ),
        oficios=(
            OficioObra("0101", "CARPINTERÍA"),
            OficioObra("0102", "FONTANERÍA"),
            OficioObra("0133", "PINTURA"),
        ),
        proveedores=(
            ProveedorEnObra("0101", "P0001", "Carpinterías Ejemplo S.L."),
            ProveedorEnObra("0101", "P0002", "Mamparas Ejemplo S.A."),
            ProveedorEnObra("0102", "P0003", PROVEEDOR),
            ProveedorEnObra("0133", None, None),
        ),
    )


def test_f036_t13_los_oficios_se_piden_con_la_referencia_de_la_unica_obra():
    """La segunda lectura necesita **la** obra (§5.1): la que dio la primera."""
    puerto = _obra_0677()

    leer_catalogo(puerto, "0677")

    assert puerto.llamadas == [("unidades", "0677"), ("oficios", OBRA_REF)]


def test_f036_r9_el_codigo_se_normaliza_antes_de_llamar_a_sigrid():
    """Sin espacios, como los demás códigos del proyecto (F-032). Y es el que
    queda en el catálogo: el que casa, literal, con `o.cod`."""
    puerto = _obra_0677()

    catalogo = leer_catalogo(puerto, " 06 77 ")

    assert puerto.llamadas[0] == ("unidades", "0677")
    assert catalogo.obra_codigo == "0677"


@pytest.mark.parametrize("codigo", ("", "   ", "0677/1", "X" * 25, None), ids=repr)
def test_f036_r9_un_codigo_inadmisible_no_llama_a_sigrid(codigo):
    puerto = _obra_0677()

    with pytest.raises(CodigoDeObraInvalido):
        leer_catalogo(puerto, codigo)

    assert puerto.llamadas == []


def test_f036_t13_los_oficios_salen_distintos_y_por_codigo():
    """El `DISTINCT` de oficios es de la aplicación (§6.3 enmendado): una fila
    de `obrofc` por proveedor, un oficio por código, ordenados (R8)."""
    oficios = (
        FilaOficioCatalogo("0166", "VIDRIO", None, None),
        FilaOficioCatalogo("0101", "CARPINTERÍA", "P0002", "B"),
        FilaOficioCatalogo("0102", "FONTANERÍA", "P0003", "C"),
        FilaOficioCatalogo("0101", "CARPINTERÍA", "P0001", "A"),
    )

    catalogo = leer_catalogo(_obra_0677(oficios=oficios), "0677")

    assert catalogo.oficios == (
        OficioObra("0101", "CARPINTERÍA"),
        OficioObra("0102", "FONTANERÍA"),
        OficioObra("0166", "VIDRIO"),
    )


def test_f036_t13_con_dos_nombres_para_un_codigo_se_queda_el_primero():
    """No debería pasar (un `auxofc` por código), pero el resultado no puede
    depender de nada más que del orden de la lectura."""
    oficios = (
        FilaOficioCatalogo("0101", "CARPINTERÍA", "P0001", "A"),
        FilaOficioCatalogo("0101", "CARPINTERIA", "P0002", "B"),
    )

    catalogo = leer_catalogo(_obra_0677(oficios=oficios), "0677")

    assert catalogo.oficios == (OficioObra("0101", "CARPINTERÍA"),)


def test_f036_t13_los_proveedores_son_las_filas_de_obrofc_tal_cual_y_en_orden():
    """Una por fila, también las que no tienen proveedor (la costura de R71 y
    R93 está en el dominio, que ya las descarta al componer los pares)."""
    catalogo = leer_catalogo(_obra_0677(), "0677")

    assert catalogo.proveedores == tuple(
        ProveedorEnObra(f.oficio_codigo, f.proveedor_codigo, f.proveedor_nombre)
        for f in OFICIOS_0677
    )


def test_f036_t13_el_nombre_de_la_obra_es_el_de_sus_unidades():
    unidades = (
        FilaUnidadCatalogo(OBRA_REF, "0677", "LA OBRA", "U1", "Villa 1"),
        FilaUnidadCatalogo(OBRA_REF, "0677", "LA OBRA", "U2", "Villa 2"),
    )

    catalogo = leer_catalogo(CatalogoEnMemoria(unidades), "0677")

    assert catalogo.obra_nombre == "LA OBRA"


def test_f036_t13_las_unidades_quedan_con_su_codigo_y_su_nombre_tal_cual():
    """Las etiquetas las compone el dominio (R8), y el código de la unidad es
    el que acabará en Sigrid: ni se recorta ni se toca."""
    unidades = (
        FilaUnidadCatalogo(OBRA_REF, "0677", None, "0677.03VILLA 5. ", "  Villa 5 "),
        FilaUnidadCatalogo(OBRA_REF, "0677", None, "U2", None),
    )

    catalogo = leer_catalogo(CatalogoEnMemoria(unidades), "0677")

    assert catalogo.obra_nombre is None
    assert catalogo.unidades == (
        UnidadPosventa("0677.03VILLA 5. ", "  Villa 5 "),
        UnidadPosventa("U2", None),
    )


@pytest.mark.parametrize("codigo", (None, "", "   "), ids=("nulo", "vacio", "blancos"))
def test_f036_t13_una_unidad_sin_codigo_no_entra_en_el_catalogo(codigo):
    """No se puede ofrecer en el desplegable ni crear nada en ella en Sigrid:
    se deja fuera y se cuenta en el log."""
    unidades = (_unidad(1), _unidad(2, codigo=codigo), _unidad(3))

    catalogo = leer_catalogo(CatalogoEnMemoria(unidades), "0677")

    assert [u.codigo for u in catalogo.unidades] == [
        "0677.03VILLA 1.",
        "0677.03VILLA 3.",
    ]


def test_f036_t13_el_catalogo_sirve_al_dominio_de_la_plantilla():
    """Lo que compone la aplicación es lo que esperan las etiquetas (R8) y el
    desplegable de oficios (R92)."""
    catalogo = leer_catalogo(_obra_0677(), "0677")
    oficios, pares = opciones(catalogo)

    assert len(etiquetas_de_unidades(catalogo.unidades)) == 15
    assert [o.codigos_en_obra for o in oficios] == [("0101",), ("0102",), ("0133",)]
    assert [p.filas_en_obra for p in pares] == [
        (("0101", "P0001"),),
        (("0101", "P0002"),),
        (("0102", "P0003"),),
    ]


# ==========================================================================
# R12 · una obra sin oficios: el catálogo sale igual, sin oficios
# ==========================================================================


def test_f036_r12_una_obra_sin_oficios_da_un_catalogo_sin_oficios():
    catalogo = leer_catalogo(_obra_0677(oficios=()), "0677")

    assert catalogo.oficios == ()
    assert catalogo.proveedores == ()
    assert len(catalogo.unidades) == 15


# ==========================================================================
# R10 · cero obras, varias obras, techo
# ==========================================================================


def test_f036_r10_sin_unidades_es_obra_sin_unidades_y_no_se_leen_los_oficios():
    puerto = CatalogoEnMemoria(())

    with pytest.raises(ObraSinUnidades) as fallo:
        leer_catalogo(puerto, "9999")

    assert "«9999»" in fallo.value.motivo
    assert puerto.llamadas == [("unidades", "9999")]


def test_f036_r10_si_ninguna_unidad_tiene_codigo_tampoco_hay_unidades():
    puerto = CatalogoEnMemoria((_unidad(1, codigo=None), _unidad(2, codigo=" ")))

    with pytest.raises(ObraSinUnidades):
        leer_catalogo(puerto, "0677")

    assert puerto.llamadas == [("unidades", "0677")]


def test_f036_r10_dos_obras_con_el_mismo_codigo_son_obra_ambigua():
    """En el maestro hay códigos repetidos (la 0677 tiene dos filas). El
    sistema no elige."""
    unidades = (_unidad(1), _unidad(2, obra_ref=OTRA_OBRA_REF), _unidad(3))
    puerto = CatalogoEnMemoria(unidades)

    with pytest.raises(ObraAmbigua) as fallo:
        leer_catalogo(puerto, "0677")

    assert "«0677»" in fallo.value.motivo
    assert "2 obras" in fallo.value.motivo
    assert OBRA_REF not in fallo.value.motivo
    assert OTRA_OBRA_REF not in fallo.value.motivo
    assert puerto.llamadas == [("unidades", "0677")]


def test_f036_r10_la_obra_ambigua_se_decide_antes_de_quitar_unidades_sin_codigo():
    """Una segunda obra cuyas unidades no tienen código sigue siendo otra obra."""
    unidades = (_unidad(1), _unidad(2, obra_ref=OTRA_OBRA_REF, codigo=None))

    with pytest.raises(ObraAmbigua):
        leer_catalogo(CatalogoEnMemoria(unidades), "0677")


def test_f036_r10_unidades_al_techo_son_catalogo_sin_verificar():
    """Con el techo alcanzado puede faltar una obra o una unidad: ni se cuenta
    ni se leen los oficios."""
    puerto = _obra_0677(unidades_al_techo=True)

    with pytest.raises(CatalogoSinVerificar) as fallo:
        leer_catalogo(puerto, "0677")

    assert "«0677»" in fallo.value.motivo
    assert "unidades" in fallo.value.motivo
    assert puerto.llamadas == [("unidades", "0677")]


def test_f036_r10_el_techo_va_antes_que_la_obra_ambigua():
    unidades = (_unidad(1), _unidad(2, obra_ref=OTRA_OBRA_REF))

    with pytest.raises(CatalogoSinVerificar):
        leer_catalogo(CatalogoEnMemoria(unidades, unidades_al_techo=True), "0677")


def test_f036_r10_oficios_al_techo_son_catalogo_sin_verificar():
    puerto = _obra_0677(oficios_al_techo=True)

    with pytest.raises(CatalogoSinVerificar) as fallo:
        leer_catalogo(puerto, "0677")

    assert "«0677»" in fallo.value.motivo
    assert "oficios" in fallo.value.motivo
    assert puerto.llamadas == [("unidades", "0677"), ("oficios", OBRA_REF)]


# ==========================================================================
# R11 · los fallos de Sigrid suben tal cual
# ==========================================================================


@pytest.mark.parametrize("donde", ("unidades", "oficios"))
def test_f036_r11_un_fallo_de_sigrid_sube_sin_catalogo_a_medias(donde):
    fallo = CatalogoNoDisponible("no se ha podido leer: la pasarela respondió 503")
    puerto = _obra_0677(**{f"fallo_{donde}": fallo})

    with pytest.raises(CatalogoNoDisponible) as capturado:
        leer_catalogo(puerto, "0677")

    assert capturado.value is fallo


# ==========================================================================
# R47 · el log: la obra y recuentos; ni obra_ref ni nombres ni proveedores
# ==========================================================================


def test_f036_r47_el_log_lleva_la_obra_y_los_recuentos(registros):
    unidades = (_unidad(1), _unidad(2, codigo=None), _unidad(3))

    leer_catalogo(CatalogoEnMemoria(unidades), "0677")

    de_la_aplicacion = [
        linea for linea in registros if linea.startswith(modulo.__name__)
    ]
    assert de_la_aplicacion == [
        (
            f"{modulo.__name__} F-036 catálogo de la obra leído de Sigrid: obra=0677 "
            "unidades=2 unidades_sin_codigo=1 oficios=3 filas_obrofc=4"
        )
    ]


def test_f036_r47_ni_obra_ref_ni_nombres_ni_proveedores_en_los_logs(registros):
    unidades = (_unidad(1, nombre=UNIDAD_LIBRE), _unidad(2))
    oficios = (FilaOficioCatalogo("0101", "CARPINTERÍA", CODIGO_PROVEEDOR, PROVEEDOR),)

    leer_catalogo(CatalogoEnMemoria(unidades, oficios), "0677")
    for puerto in (
        CatalogoEnMemoria(()),
        CatalogoEnMemoria((_unidad(1), _unidad(2, obra_ref=OTRA_OBRA_REF))),
        _obra_0677(oficios_al_techo=True),
    ):
        with pytest.raises((ObraSinUnidades, ObraAmbigua, CatalogoSinVerificar)):
            leer_catalogo(puerto, "0677")

    texto = "\n".join(registros)
    assert registros
    for prohibido in (
        OBRA_REF,
        OTRA_OBRA_REF,
        UNIDAD_LIBRE,
        "Fulanita",
        PROVEEDOR,
        CODIGO_PROVEEDOR,
        "OBRA EJEMPLO",
    ):
        assert prohibido not in texto


# ==========================================================================
# Hexagonal: la aplicación conoce el puerto, no el adaptador
# ==========================================================================


def test_f036_t13_la_aplicacion_no_importa_infraestructura():
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))
    importados = {
        nodo.module
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom) and nodo.module
    } | {
        alias.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Import)
        for alias in nodo.names
    }

    for nombre in importados:
        assert not nombre.startswith(("infrastructure", "httpx", "tenacity"))
    assert "domain.ports.catalogo_obra" in importados


# ==========================================================================
# De punta a punta con el adaptador (sobre el ClienteFalso)
# ==========================================================================


def _adaptador(*respuestas) -> tuple[AdaptadorCatalogoSigridApi, ClienteFalso]:
    cliente = ClienteFalso(list(respuestas))
    adaptador = AdaptadorCatalogoSigridApi(
        entorno="dev",
        base_url="https://ejemplo.invalido",
        api_key="clave-de-mentira-para-el-test",
        base_datos="labase",
        timeout_s=35,
        reintentos=1,
        espera_inicial_s=0.0,
        cliente=cliente,
    )
    return adaptador, cliente


def _respuesta(filas) -> RespuestaFalsa:
    return RespuestaFalsa(200, cuerpo_de_lectura(("c",) * len(filas[0]), filas))


def test_f036_t13_de_punta_a_punta_la_referencia_de_la_obra_vuelve_como_llego():
    """El `obride` que da la primera lectura es el parámetro de la segunda."""
    adaptador, cliente = _adaptador(
        _respuesta([[987654321, "0677", "OBRA", "U1", "Villa 1"]]),
        _respuesta([["0101", "CARPINTERÍA", "P0001", "A"]]),
    )

    catalogo = leer_catalogo(adaptador, "0677")

    assert cliente.peticiones[1].json["parameters"] == ["987654321"]
    assert catalogo.unidades == (UnidadPosventa("U1", "Villa 1"),)
    assert catalogo.proveedores == (ProveedorEnObra("0101", "P0001", "A"),)


def test_f036_r10_de_punta_a_punta_mil_unidades_son_catalogo_sin_verificar():
    filas = [[987654321, "0677", "OBRA", f"U{n}", None] for n in range(1000)]
    adaptador, cliente = _adaptador(_respuesta(filas))

    with pytest.raises(CatalogoSinVerificar):
        leer_catalogo(adaptador, "0677")

    assert len(cliente.peticiones) == 1


def test_f036_t13_los_grupos_vigentes_no_son_cosa_de_esta_lectura():
    """§7.1: los grupos de oficio se leen aparte (`EquivalenciasPort`, T15)."""
    texto = MODULO.read_text(encoding="utf-8")

    for ajeno in ("GruposVigentes", "grupos_vigentes", "EquivalenciasPort"):
        assert ajeno not in texto
