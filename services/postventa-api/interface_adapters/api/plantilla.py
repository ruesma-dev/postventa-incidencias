# services/postventa-api/interface_adapters/api/plantilla.py
"""Handler de `GET /api/plantilla?obra=`: la plantilla de una obra (F-036).

`specs/F-036-importar-excel/design.md` §7.2 y §8. Aquí se **componen los
adaptadores** —catálogo de Sigrid, decisiones de equivalencia, generador y el
YAML de la plantilla— y se llama a `application/pipelines/plantilla.py`, como
manda `docs/CONVENTIONS.md`. Los puertos inyectables son la costura de test:
con ellos la suite prueba el borde entero sin Sigrid ni base.

## En este orden

1. **El código de obra** (R9): si no es admisible, `CodigoDeObraInvalido`
   (→ 400) **sin construir nada** y, por tanto, sin llamar a Sigrid.
2. **Los adaptadores**: el catálogo exige `ENTORNO` en `dev` o `pro` y la
   configuración de `sigrid-api` (R48, R11 → 503); las decisiones, la de
   PostgreSQL (→ 503).
3. **La plantilla**: el catálogo se lee de Sigrid en ese momento (R1), con los
   grupos de oficio confirmados; `ObraSinUnidades` (→ 404), `ObraAmbigua` y
   `CatalogoSinVerificar` (→ 409) suben sin fichero.

Solo lee: ni escribe en Sigrid (R46) ni depende de ninguna ventana de
escritura del servicio.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import cache
from typing import Any

from application.pipelines.plantilla import generar_plantilla
from config.settings import obtener_ajustes
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.hoja_calculo import GeneradorPlantillaPort
from infrastructure.documentos.excel_openpyxl import GeneradorPlantillaOpenpyxl
from infrastructure.documentos.plantilla_yaml import (
    ConfiguracionPlantilla,
    cargar_plantilla_yaml,
)
from infrastructure.persistencia.fabrica import construir_equivalencias
from infrastructure.sigrid.fabrica import construir_catalogo_obra

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
    equivalencias: EquivalenciasPort | None = None,
    generador: GeneradorPlantillaPort | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
    ahora: datetime | None = None,
) -> tuple[str, bytes]:
    """El nombre del fichero y los bytes de la plantilla de la obra (R1)."""
    codigo = normalizar_codigo_obra(obra)
    # Sigrid primero: su puerta de entorno no abre ninguna conexión.
    if catalogo_obra is None:
        catalogo_obra = construir_catalogo_obra(obtener_ajustes())
    if equivalencias is None:
        equivalencias = construir_equivalencias(obtener_ajustes())
    config = (
        configuracion if configuracion is not None else configuracion_de_la_plantilla()
    )
    return generar_plantilla(
        codigo,
        catalogo_obra=catalogo_obra,
        equivalencias=equivalencias,
        generador=generador if generador is not None else GeneradorPlantillaOpenpyxl(),
        listas=config.listas,
        textos=config.textos,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
