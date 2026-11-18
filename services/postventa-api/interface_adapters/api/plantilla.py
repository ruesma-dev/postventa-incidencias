# services/postventa-api/interface_adapters/api/plantilla.py
"""Handler de `GET /api/plantilla?obra=`: la plantilla de una obra (F-036).

`specs/F-036-importar-excel/design.md` §7.2 y §8; F-071 §6.1. Aquí se
**componen los adaptadores** —catálogo de Sigrid, la fuente de las ubicaciones
válidas de cada unidad (Sigrid), generador y el YAML de la plantilla— y se
llama a `application/pipelines/plantilla.py`, como
manda `docs/CONVENTIONS.md`. Los puertos inyectables son la costura de test:
con ellos la suite prueba el borde entero sin Sigrid ni base.

## En este orden

1. **El código de obra** (R9): si no es admisible, `CodigoDeObraInvalido`
   (→ 400) **sin construir nada** y, por tanto, sin llamar a Sigrid.
2. **Los adaptadores**: el catálogo exige `ENTORNO` en `dev` o `pro` y la
   configuración de `sigrid-api` (R48, R11 → 503); después, la fuente de las
   ubicaciones, la **misma** que la importación y la revisión
   (`construir_fuente_de_ubicaciones` de `interface_adapters/api/revision.py`).
   Ninguna base: desde F-071 la plantilla no lee las decisiones de
   equivalencia (R2). Y, la última, la fuente de los tipos de reclamación
   (F-072, `construir_tipos_reclamacion`, con la misma puerta de entorno).
3. **La plantilla**: el catálogo, las ubicaciones y los tipos se leen de Sigrid
   en ese momento (R1; F-072 R1); `ObraSinUnidades` (→ 404), `ObraAmbigua` y
   `CatalogoSinVerificar` (→ 409, también la lectura de ubicaciones o la de
   tipos al techo) suben sin fichero (F-071 R3; F-072 R3, R4).

Solo lee: ni escribe en Sigrid (R46) ni depende de ninguna ventana de
escritura del servicio.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import cache
from typing import Any

from application.pipelines.plantilla import (
    FuenteUbicacionesValidas,
    generar_plantilla,
)
from application.pipelines.tipos_reclamacion import (
    FuenteTiposReclamacion,
    fuente_de_tipos,
)
from config.settings import obtener_ajustes
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.hoja_calculo import GeneradorPlantillaPort
from infrastructure.documentos.plantilla_yaml import (
    ConfiguracionPlantilla,
    cargar_plantilla_yaml,
)
from infrastructure.sigrid.fabrica import (
    construir_catalogo_obra,
    construir_tipos_reclamacion,
)

__all__ = ["configuracion_de_la_plantilla", "descargar_plantilla"]


@cache
def configuracion_de_la_plantilla() -> ConfiguracionPlantilla:
    """El YAML de la plantilla, leído y validado **una vez** por proceso.

    Un YAML roto levanta `ConfiguracionPlantillaInvalida` en la primera
    petición que lo necesite; el resto del servicio sigue en pie.
    """
    return cargar_plantilla_yaml()


def descargar_plantilla(
    obra: Any,
    *,
    catalogo_obra: CatalogoObraPort | None = None,
    ubicaciones: FuenteUbicacionesValidas | None = None,
    tipos: FuenteTiposReclamacion | None = None,
    generador: GeneradorPlantillaPort | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
    ahora: datetime | None = None,
) -> tuple[str, bytes]:
    """El nombre del fichero y los bytes de la plantilla de la obra (R1)."""
    codigo = normalizar_codigo_obra(obra)
    # Sigrid primero: su puerta de entorno no abre ninguna conexión.
    if catalogo_obra is None:
        catalogo_obra = construir_catalogo_obra(obtener_ajustes())
    if ubicaciones is None:
        # Importación diferida: `interface_adapters/api/revision.py` importa
        # este módulo (`configuracion_de_la_plantilla`); arriba haría un ciclo.
        from interface_adapters.api import revision

        ubicaciones = revision.construir_fuente_de_ubicaciones(obtener_ajustes())
    if tipos is None:
        tipos = fuente_de_tipos(construir_tipos_reclamacion(obtener_ajustes()))
    config = (
        configuracion if configuracion is not None else configuracion_de_la_plantilla()
    )
    # Importación diferida (F-060 M-3): importar `function_app.py` no carga
    # `openpyxl`, que el listado de la revisión no usa.
    from infrastructure.documentos.excel_openpyxl import GeneradorPlantillaOpenpyxl

    return generar_plantilla(
        codigo,
        catalogo_obra=catalogo_obra,
        ubicaciones=ubicaciones,
        tipos=tipos,
        generador=generador if generador is not None else GeneradorPlantillaOpenpyxl(),
        listas=config.listas,
        textos=config.textos,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
