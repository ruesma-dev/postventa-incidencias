# services/postventa-api/tests/test_fix_proveedor_nombre_recortado.py
"""Arreglo: editar sin tocar el proveedor no lo marca en `cambios`.

Defecto visto en producción (T26 de F-072): Sigrid devuelve el nombre del
proveedor con un espacio final. La importación lo guarda **recortado**
(`pares_del_desplegable`), pero `validar_valores` tomaba el nombre del
catálogo tal cual, y `campos_cambiados` veía `proveedor` distinto aunque nadie
lo hubiera tocado.

Datos ficticios: obra `9901`, proveedor `EJ07`, textos «Ejemplo».
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    ListasCerradas,
    OficioObra,
    Opcion,
    ProveedorEnObra,
    UnidadPosventa,
    oficios_del_desplegable,
    pares_del_desplegable,
)
from domain.models.revision import (
    ValoresIncidencia,
    ValoresPedidos,
    campos_cambiados,
    validar_valores,
    valores_importados,
)
from interface_adapters.api.revision import _pares

U1 = "9901.03VILLA 1."
NOMBRE_DE_SIGRID = "Carpintería Ejemplo, S.L. "  # con el espacio final del ERP
NOMBRE_RECORTADO = "Carpintería Ejemplo, S.L."

CATALOGO = CatalogoObra(
    obra_codigo="9901",
    obra_nombre="Promoción Ejemplo",
    unidades=(UnidadPosventa(codigo=U1, nombre="Villa Ejemplo 1"),),
    oficios=(OficioObra(codigo="0046", nombre="Carpintería de madera"),),
    proveedores=(ProveedorEnObra("0046", "EJ07", NOMBRE_DE_SIGRID),),
)
LISTAS = ListasCerradas(urgencias=(Opcion("Urgente", "urgente"),), listados=())


def _catalogo_con(*proveedores: ProveedorEnObra) -> CatalogoObra:
    """El catálogo de la obra con otras filas de `obrofc` para el par EJ07."""
    return CatalogoObra(
        obra_codigo=CATALOGO.obra_codigo,
        obra_nombre=CATALOGO.obra_nombre,
        unidades=CATALOGO.unidades,
        oficios=CATALOGO.oficios,
        proveedores=proveedores,
    )


def _nombre_de_la_importacion(catalogo: CatalogoObra = CATALOGO) -> str | None:
    """El nombre que guarda la importación: el del par del desplegable."""
    (par,) = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    return par.proveedor_nombre


def _importada(catalogo: CatalogoObra = CATALOGO) -> IncidenciaEnBandeja:
    return IncidenciaEnBandeja(
        incidencia_id=UUID(int=1),
        importacion_id=UUID(int=1000),
        fila_origen=2,
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion="Baño",
        descripcion="Ejemplo de grieta en el techo",
        detalle=None,
        oficio_codigo="0046",
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=False,
        proveedor_codigo="EJ07",
        proveedor_nombre=_nombre_de_la_importacion(catalogo),
        proveedor_ambiguo=False,
        urgencia=None,
        listado=None,
        duplicada_de=None,
        creada_at_utc=datetime(2026, 11, 1, 8, 0, tzinfo=UTC),
    )


def _editar_sin_tocar_el_proveedor(
    catalogo: CatalogoObra = CATALOGO,
) -> tuple[ValoresIncidencia, ValoresIncidencia]:
    vigentes = valores_importados(_importada(catalogo))
    editados = validar_valores(
        ValoresPedidos(
            unidad_codigo=U1,
            ubicacion="Baño",
            descripcion="Ejemplo de grieta en el techo, editada",
            detalle=None,
            oficio_codigo="0046",
            proveedor_codigo="EJ07",
            urgencia=None,
            listado=None,
        ),
        vigentes=vigentes,
        catalogo=catalogo,
        ubicaciones={U1: ("Baño", "Cocina")},
        listas=LISTAS,
    )
    return vigentes, editados


def test_fix_la_importacion_guarda_el_nombre_recortado() -> None:
    assert _nombre_de_la_importacion() == NOMBRE_RECORTADO


def test_fix_editar_sin_tocar_el_proveedor_no_lo_marca_en_cambios() -> None:
    vigentes, editados = _editar_sin_tocar_el_proveedor()
    assert campos_cambiados(vigentes, editados) == ("descripcion",)


def test_fix_la_edicion_guarda_el_nombre_del_proveedor_recortado() -> None:
    _, editados = _editar_sin_tocar_el_proveedor()
    assert editados.proveedor_nombre == NOMBRE_RECORTADO


def test_fix_la_edicion_toma_el_primer_nombre_no_vacio_del_par() -> None:
    """La primera fila de `obrofc` del par trae el nombre vacío; una posterior, no.

    La importación guarda el de la posterior; la edición, también: si ganara la
    primera fila (vacía), `cambios` marcaría `proveedor` sin haberlo tocado.
    """
    catalogo = _catalogo_con(
        ProveedorEnObra("0046", "EJ07", ""),
        ProveedorEnObra("0046", "EJ07", NOMBRE_DE_SIGRID),
    )
    assert _nombre_de_la_importacion(catalogo) == NOMBRE_RECORTADO
    vigentes, editados = _editar_sin_tocar_el_proveedor(catalogo)
    assert campos_cambiados(vigentes, editados) == ("descripcion",)
    assert editados.proveedor_nombre == NOMBRE_RECORTADO


def test_fix_el_nombre_en_blanco_se_guarda_none_como_en_la_importacion() -> None:
    """El único nombre del par está en blanco: la importación guarda `None`.

    La edición guarda lo mismo (`None`, no `""`), y no marca `proveedor`.
    """
    catalogo = _catalogo_con(ProveedorEnObra("0046", "EJ07", "   "))
    assert _nombre_de_la_importacion(catalogo) is None
    vigentes, editados = _editar_sin_tocar_el_proveedor(catalogo)
    assert campos_cambiados(vigentes, editados) == ("descripcion",)
    assert editados.proveedor_nombre is None


@pytest.mark.parametrize(
    "catalogo",
    [
        CATALOGO,
        _catalogo_con(
            ProveedorEnObra("0046", "EJ07", ""),
            ProveedorEnObra("0046", "EJ07", NOMBRE_DE_SIGRID),
        ),
        _catalogo_con(ProveedorEnObra("0046", "EJ07", "   ")),
    ],
    ids=["espacio-final", "primera-fila-vacia", "en-blanco"],
)
def test_fix_lo_que_ofrece_pares_es_lo_que_guarda_la_edicion(
    catalogo: CatalogoObra,
) -> None:
    """El desplegable de la edición (`_pares`) ofrece el nombre que se guarda.

    Segunda corrección del review: `_pares` tomaba el nombre crudo de la
    primera fila; ahora sigue la regla de la importación y de `validar_valores`.
    """
    (ofrecido,) = _pares(catalogo)
    _, editados = _editar_sin_tocar_el_proveedor(catalogo)
    assert ofrecido == {
        "oficio_codigo": "0046",
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": editados.proveedor_nombre,
    }
