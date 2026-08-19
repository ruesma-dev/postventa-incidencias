# services/postventa-api/application/pipelines/paso_persistencia.py
"""Paso 5 del pipeline: dejar escrito lo que le ha pasado al parte (F-005).

Habla con el **puerto**, jamás con el adaptador (R30, R31): este módulo no
sabe que debajo hay PostgreSQL, y por eso se prueba entero con un doble en
memoria. Es lo mismo que hace `paso_extraccion` con `ExtractorPort`.

Lo que este paso **no** decide es *cuándo* se guarda ni de dónde sale
`remesa_id`: eso lo compone el punto de entrada (F-006/F-007), como manda
`docs/CONVENTIONS.md`. Aquí solo hay orquestación de una llamada al puerto y,
si el parte ya trae veredicto, de la segunda.

`ahora` entra por parámetro y no se lee del reloj aquí: un paso que consulta la
hora no se puede probar dos veces con el mismo resultado, y R15 —conservar la
fecha de primera vez y refrescar la de actualización— es precisamente sobre
fechas.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.errores import ErrorDePersistencia
from domain.models.persistencia import ResultadoGuardado
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.contexto_parte import ContextoParte


def paso_persistencia(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    *,
    remesa_id: str,
    ahora: datetime,
) -> ContextoParte:
    """Guarda el parte y, si lo hay, su veredicto.

    Levanta `ErrorDePersistencia` si falta la extracción: guardar un parte del
    que no se ha leído nada dejaría una fila sin ninguno de los nueve campos,
    que es peor que no tenerla — parecería un parte ilegible cuando en realidad
    nadie lo miró.
    """
    if ctx.extraccion is None:
        raise ErrorDePersistencia(
            "no se puede guardar el parte: falta la extracción de sus campos"
        )

    resultado = repositorio.guardar_parte(
        parte=ctx.parte,
        extraccion=ctx.extraccion,
        remesa_id=remesa_id,
        ahora=ahora,
    )
    if resultado == ResultadoGuardado.ACTUALIZADO:
        ctx.avisos.append(
            "este parte ya se había procesado antes: se ha actualizado su ficha"
        )

    if ctx.validacion is not None:
        repositorio.guardar_validacion(resultado=ctx.validacion, ahora=ahora)

    return ctx
