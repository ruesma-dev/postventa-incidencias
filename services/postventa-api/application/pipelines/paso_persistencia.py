# services/postventa-api/application/pipelines/paso_persistencia.py
"""Paso 5 del pipeline: dejar escrito lo que le ha pasado al parte (F-005).

Habla con el **puerto**, jamás con el adaptador (R30, R31): este módulo no
sabe que debajo hay PostgreSQL, y por eso se prueba entero con un doble en
memoria. Es lo mismo que hace `paso_extraccion` con `ExtractorPort`.

Lo que este paso **no** decide es *cuándo* se guarda ni de dónde sale
`remesa_id`: eso lo compone el punto de entrada (F-006/F-007), como manda
`docs/CONVENTIONS.md`. Aquí solo hay orquestación de una llamada al puerto y,
si el parte ya trae veredicto, de las que dejan escrito ese veredicto y **la
constancia de en qué estado queda el parte** (F-028, R23).

Esa constancia es el histórico de estado, y su regla vive en `constancia.py`
porque la comparte con `paso_cierre`: se añade fila **solo si el estado
derivado cambió**. Sin esa condición, el autoguardado de F-026 —que reprocesa
los 22 partes de una remesa cada vez que alguien recarga la pantalla— llenaría
la tabla de renglones idénticos y el histórico dejaría de contar la película
para contar el ruido.

`ahora` entra por parámetro y no se lee del reloj aquí: un paso que consulta la
hora no se puede probar dos veces con el mismo resultado, y R15 —conservar la
fecha de primera vez y refrescar la de actualización— es precisamente sobre
fechas.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.errores import ErrorDePersistencia
from domain.models.estado import estado_del_parte
from domain.models.persistencia import ResultadoGuardado
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.constancia import anotar_estado
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
        _dejar_constancia_del_estado(ctx, repositorio, ahora=ahora)

    return ctx


def _dejar_constancia_del_estado(
    ctx: ContextoParte, repositorio: RepositorioPartesPort, *, ahora: datetime
) -> None:
    """Apunta en el histórico el estado del parte, si cambió (F-028, R23).

    Va **detrás** de guardar el veredicto, y el orden es medio requisito: al
    revés, un fallo al guardar la validación dejaría escrito un estado derivado
    de un veredicto que no está en la base, y el parte tendría un renglón que no
    se corresponde con nada.

    Lo que se apunta es el **estado del parte** —`estado_del_parte`, con los
    tres hechos— y no lo que dijo la máquina. La diferencia importa en el caso
    más común de todos: un parte no apto que alguien aprobó está `aprobado`
    (R9), así que reprocesarlo no puede escribir un `aprobado → pendiente` que
    nunca ocurrió. Con el estado derivado eso sale gratis; con el veredicto
    suelto, el histórico contaría una degradación falsa cada vez que alguien
    recarga la pantalla.

    **Solo si hay veredicto**, que es el disparador que fija `design.md` §4.
    F-003 y F-004 son independientes: un parte extraído al que todavía no se le
    ha mirado la firma no tiene estado que contar, y abrirle el histórico con un
    `→ pendiente` diría que algo ya se pronunció sobre él. De paso se ahorra la
    consulta en el único camino donde no puede aportar nada.

    **Una sola consulta por parte** (`consultar_situacion`), y del repositorio y
    nunca del cuerpo de la petición (R33): si el estado anterior viniera de
    fuera, quien llama podría afirmar que un parte estaba aprobado.

    Si la base falla aquí, el error **sube**: no se ha escrito nada en ningún
    sistema externo, el borde lo traduce a su 503 honesto y el reintento es
    inocuo — guardar el parte y el veredicto son idempotentes y la propia regla
    de constancia impide que el reintento duplique la fila. Es justo lo
    contrario de lo que hace `paso_cierre`, y por el motivo contrario.
    """
    situacion = repositorio.consultar_situacion(hash_parte=ctx.parte.hash)
    anotar_estado(
        repositorio,
        situacion,
        hash_parte=ctx.parte.hash,
        estado=estado_del_parte(
            ctx.validacion, situacion.decision_humana, situacion.estado_cierre
        ),
        ahora=ahora,
    )
