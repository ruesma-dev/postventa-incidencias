# services/postventa-api/tests/utiles_plantilla.py
"""Utilidades de los tests del Excel de F-036 (T10, T11).

Un catálogo **inventado** de la obra 0677 —los nombres de proveedor son de
ejemplo, nunca de Sigrid—, las opciones de `Oficio` y `Proveedor` calculadas
como lo hará la aplicación y un atajo para generar la plantilla y reabrirla
**en memoria**: ningún test escribe ni lee un `.xlsx` de disco (R59).
"""

from __future__ import annotations

import io
import warnings
from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook

from domain.models.equivalencias import (
    MISMO,
    PERFILES,
    Candidato,
    Catalogo,
    DecisionPar,
    grupos_de_proveedor,
    grupos_vigentes,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    OpcionOficio,
    OpcionProveedor,
    ProveedorEnObra,
    UnidadPosventa,
    opciones_de_oficio,
    opciones_de_proveedor,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos.excel_openpyxl import GeneradorPlantillaOpenpyxl
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml

INSTANTE = datetime(2026, 9, 29, 8, 30, tzinfo=UTC)
# Construido desde un entero: un GUID literal no entra en el repositorio (F-006 R26).
IMPORTACION = UUID(int=0x1234)

UNIDADES = (
    UnidadPosventa("0677.03VILLA 1.", "Viviendas Bloque Villa 1"),
    UnidadPosventa("0677.03VILLA 2.", "Viviendas Bloque Villa 2"),
    UnidadPosventa("0677.03VILLA 3.", "Viviendas Bloque Villa 3"),
)
OFICIOS = (
    OficioObra("0046", "Carpintería de madera"),
    OficioObra("0085", "Mamparas"),
    OficioObra("0133", "Albañilería"),
    OficioObra("0166", "Mampara"),
)
FILAS_OBROFC = (
    ProveedorEnObra("0046", "P001", "Carpinterías Ejemplo S.L."),
    ProveedorEnObra("0085", "P002", "Mamparas Ejemplo S.A."),
    ProveedorEnObra("0166", "P002", "Mamparas Ejemplo S.A."),
    ProveedorEnObra("0046", "P003", "Juan Ejemplo Ejemplo"),
    ProveedorEnObra("0133", None, None),
)


def catalogo(
    *,
    unidades: tuple[UnidadPosventa, ...] = UNIDADES,
    oficios: tuple[OficioObra, ...] = OFICIOS,
    filas: tuple[ProveedorEnObra, ...] = FILAS_OBROFC,
    obra_nombre: str | None = "Obra Ejemplo",
) -> CatalogoObra:
    return CatalogoObra(
        obra_codigo="0677",
        obra_nombre=obra_nombre,
        unidades=unidades,
        oficios=oficios,
        proveedores=filas,
    )


def mismo(a: str, b: str) -> DecisionPar:
    return DecisionPar(
        catalogo=Catalogo.OFICIO,
        codigo_a=a,
        codigo_b=b,
        decision=MISMO,
        motivos=frozenset(),
        obra_codigo="0677",
        decidido_por="oid-de-prueba",
        decidido_at_utc=INSTANTE,
    )


def opciones(
    cat: CatalogoObra, decisiones: tuple[DecisionPar, ...] = ()
) -> tuple[tuple[OpcionOficio, ...], tuple[OpcionProveedor, ...]]:
    """Las opciones de `Oficio` y `Proveedor`, como las calculará la aplicación."""
    uso = Counter(f.oficio_codigo for f in cat.proveedores)
    grupos_oficio = grupos_vigentes(
        (Candidato(o.codigo, o.nombre) for o in cat.oficios),
        decisiones,
        PERFILES[Catalogo.OFICIO],
        uso,
    )
    grupos_proveedor = grupos_de_proveedor(
        Candidato(f.proveedor_codigo, f.proveedor_nombre)
        for f in cat.proveedores
        if f.proveedor_codigo is not None
    )
    oficios = opciones_de_oficio(cat, grupos_oficio)
    return oficios, opciones_de_proveedor(cat, grupos_proveedor, oficios)


def configuracion():
    return cargar_plantilla_yaml()


def generar(
    cat: CatalogoObra | None = None,
    *,
    decisiones: tuple[DecisionPar, ...] = (),
    filas: tuple[FilaPlantilla, ...] = (),
    importacion_origen: UUID | None = None,
    generada_at: datetime = INSTANTE,
) -> bytes:
    cat = cat or catalogo()
    oficios, pares = opciones(cat, decisiones)
    config = configuracion()
    return GeneradorPlantillaOpenpyxl().generar(
        catalogo=cat,
        opciones_oficio=oficios,
        opciones_proveedor=pares,
        listas=config.listas,
        textos=config.textos,
        generada_at=generada_at,
        filas=filas,
        importacion_origen=importacion_origen,
    )


def abrir(contenido: bytes) -> Workbook:
    """Reabre en memoria, sin los avisos de `openpyxl` sobre extensiones."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return load_workbook(io.BytesIO(contenido))
