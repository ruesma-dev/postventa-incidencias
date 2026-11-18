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


def _nombre_de_la_importacion() -> str | None:
    """El nombre que guarda la importación: el del par del desplegable."""
    (par,) = pares_del_desplegable(CATALOGO, oficios_del_desplegable(CATALOGO))
    return par.proveedor_nombre


def _importada() -> IncidenciaEnBandeja:
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
        proveedor_nombre=_nombre_de_la_importacion(),
        proveedor_ambiguo=False,
        urgencia=None,
        listado=None,
        duplicada_de=None,
        creada_at_utc=datetime(2026, 11, 1, 8, 0, tzinfo=UTC),
    )


def _editar_sin_tocar_el_proveedor() -> tuple[ValoresIncidencia, ValoresIncidencia]:
    vigentes = valores_importados(_importada())
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
        catalogo=CATALOGO,
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
