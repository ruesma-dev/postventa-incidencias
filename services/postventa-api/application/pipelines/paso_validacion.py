# services/postventa-api/application/pipelines/paso_validacion.py
"""Paso 4 del pipeline: decidir qué se hace con el parte (F-004).

El paso más pequeño del servicio, y el único que **no recibe puertos**: no los
necesita. Las reglas son dominio puro —sin red, sin base de datos, sin IA y
sin Sigrid—, así que aquí solo hay composición: coger lo que dejaron los dos
pasos anteriores y llamar a `validar_parte`.

Lo único que decide este módulo es **negarse a inventar**. Un veredicto sobre
datos que no están sería peor que un error: se archivaría —o se cerraría en el
ERP— una incidencia sin haber mirado el parte.
"""

from __future__ import annotations

from domain.models.errores import ValidacionSinDatos
from domain.models.validacion import validar_parte

from application.pipelines.contexto_parte import ContextoParte


def paso_validacion(ctx: ContextoParte) -> ContextoParte:
    """Deja el veredicto del parte en el contexto.

    Levanta `ValidacionSinDatos` si falta la extracción o la lectura de la
    firma (R21), diciendo cuál de las dos: un `AttributeError` sobre un `None`
    a mitad de una remesa de veintidós partes no le sirve a nadie para
    arreglarlo.
    """
    if ctx.extraccion is None:
        raise ValidacionSinDatos(
            "no se puede validar el parte: falta la extracción de sus campos"
        )
    if ctx.lectura_firma is None:
        raise ValidacionSinDatos(
            "no se puede validar el parte: falta la lectura de la firma"
        )

    ctx.validacion = validar_parte(ctx.extraccion, ctx.lectura_firma)
    return ctx
