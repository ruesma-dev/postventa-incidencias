# services/postventa-api/infrastructure/sigrid/escrituras.py
"""El batch de **escritura** del cierre: las dos sentencias, o ninguna.

Módulo **puro**: devuelve el cuerpo que se le manda a `POST /api/sql/write` y
no abre nada. Es la decisión que hace testeable la feature entera sin red
(`design.md` §3), y aquí importa más que en ningún otro sitio del proyecto: lo
que se construye en este fichero es lo único que va a modificar el **ERP de
producción**, y se comprueba carácter a carácter en un test unitario.

## Las dos sentencias, y por qué van juntas

`sql/write` ejecuta **todo el batch en una transacción** (`sigrid_api.md`
§7.3). Si la segunda falla, la primera se revierte con ella. Mandarlas en dos
llamadas dejaría la puerta abierta a una reclamación cerrada sin ningún rastro
en el log — que es exactamente lo que un `UPDATE` a mano se dejaría por el
camino, y la otra mitad del proceso que replicamos.

## Las cuatro decisiones del `INSERT`, y ninguna es cosmética

1. **El `ide` se reserva dentro de la propia sentencia** (R26), con
   `UPDLOCK, HOLDLOCK`: `log.ide` no es IDENTITY, es la clave primaria única de
   una tabla de 8,4 millones de filas asignadas por `MAX(ide)+1`, y
   `sigrid_api.md` §7.5 avisa de que `sql/write` **no** protege esa reserva.
2. **Y si aun así colisiona, falla en seguro**: la clave única rechaza el
   `INSERT`, la pasarela revierte el batch entero y el ERP queda **sin ningún
   cambio**. El reintento lo decide una persona, no el código (R27).
3. **El `FROM` es `dbo.con` filtrado por el estado DESTINO**, ya aplicado por
   la primera sentencia dentro de la misma transacción. Si el `UPDATE` no hizo
   nada, este `SELECT` no devuelve filas y no se inserta ningún log.
   El filtro **tiene que ir en el `FROM`, no en un `WHERE EXISTS`**: un agregado
   sin `GROUP BY` devuelve una fila aunque no case nada, y
   `ISNULL(MAX(ide),0)+1` valdría **1**, una colisión garantizada contra la fila
   más antigua de la tabla.
4. **`emp`, `tip`, `cod` y `res` se copian de la reclamación en el propio SQL**,
   no se envían calculados desde Python (D1). Hoy todas las reclamaciones son
   de la misma empresa, pero eso es un dato de esta instalación, exactamente
   igual que el número del estado.

## Lo que NO son estados de la reclamación

Tres valores fijos viajan en la fila de auditoría —su origen, su tipo de
operación y su marca de realizado—, medidos homogéneos sobre las 6.843 filas de
«Cerrar parte». **Son columnas del registro de log**, no el estado de ningún
concepto: `sigrid_tablas.md` llama a esa última columna «Estado/Realizado» del
propio log. Aun así van como **parámetros** y no pegados al texto, para que el
control negativo de R3 no necesite ninguna excepción para este fichero.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from domain.models.cierre import (
    LONGITUD_MAXIMA_LOGIN,
    TEXTO_LOG_CIERRE,
    PlanDeCierre,
)
from domain.models.errores import CierreFallido

__all__ = [
    "LOG_OPERACION_PROCESO",
    "LOG_ORIGEN",
    "LOG_REALIZADO",
    "LOG_TABLA",
    "MAXIMO_FILAS_AFECTADAS",
    "SQL_INSERT_LOG",
    "SQL_UPDATE_ESTADO",
    "batch_de_cierre",
    "fecha_y_hora_de_sigrid",
]

#: Las columnas de `dbo.log` que se rellenan, en el orden del `INSERT`.
COLUMNAS_LOG: tuple[str, ...] = (
    "ide",
    "emp",
    "ori",
    "ope",
    "fec",
    "hor",
    "usu",
    "tab",
    "tip",
    "cod",
    "res",
    "tex",
    "est",
)

#: `log.tab`: sobre qué tabla se registró el proceso. Medido: siempre `con`.
LOG_TABLA = "con"

#: `log.ori`: el origen del registro. Medido homogéneo en las 6.843 filas.
LOG_ORIGEN = 0

#: `log.ope`: el tipo de operación, «proceso ejecutado».
#:
#: Los códigos observados para reclamaciones son alta, baja, modificación de
#: campo, **proceso**, acción y DESHACER proceso. El nuestro es el de proceso,
#: que es lo que «Cerrar parte» es.
LOG_OPERACION_PROCESO = 5

#: `log.est`: la marca «Estado/Realizado» **del propio registro de log**.
#:
#: No es el estado de la reclamación y no tiene nada que ver con `conest`: es
#: una columna de la tabla de log, y su valor está medido homogéneo en las
#: 6.843 filas de «Cerrar parte».
LOG_REALIZADO = 1

#: Tope acumulado de filas afectadas por el batch entero (R23).
#:
#: Es la red de seguridad de `sigrid_api.md` §7.3 contra un `WHERE` mal
#: escrito: si se supera, la pasarela hace ROLLBACK de todo. Dos es exactamente
#: lo que afecta un cierre correcto — una fila de `con` y una de `log`—, así que
#: cualquier cosa que tocara más ya sería un accidente.
MAXIMO_FILAS_AFECTADAS = 2

#: Sentencia 1 · el estado de la reclamación (`design.md` §7.3).
#:
#: El `WHERE` es obligatorio en la pasarela (`REQUIRE_WHERE_ON_UPDATE_DELETE`),
#: pero lo decisivo no es que esté: es que lleve el **estado de origen leído en
#: el dry-run**. Eso es el control optimista de R11, y es la respuesta al
#: hallazgo de F-008 §2.4 —los cierres se deshacen, 81 veces—: no se puede
#: asumir que lo leído siga ahí. Si alguien movió la reclamación entretanto,
#: esto afecta a 0 filas y no pisa nada.
SQL_UPDATE_ESTADO = "UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = ? AND est = ?"

#: Sentencia 2 · la fila de auditoría (`design.md` §7.3).
SQL_INSERT_LOG = (
    f"INSERT INTO dbo.log ({', '.join(COLUMNAS_LOG)})\n"
    "SELECT (SELECT ISNULL(MAX(l.ide), 0) + 1 FROM dbo.log l WITH (UPDLOCK, HOLDLOCK)),\n"
    f"       c.emp, ?, ?, ?, ?, ?, '{LOG_TABLA}', c.tip, c.cod, c.res, ?, ?\n"
    "FROM dbo.con c\n"
    "WHERE c.ide = ? AND c.tip = ? AND c.est = ?"
)


def batch_de_cierre(
    *, plan: PlanDeCierre, ahora: datetime, base_datos: str
) -> dict[str, Any]:
    """El cuerpo de `POST /api/sql/write` que cierra la incidencia.

    `ahora` entra por parámetro y aquí no se consulta ningún reloj: un módulo
    que mirase la hora no se podría probar dos veces con el mismo resultado, y
    lo que produce acaba escrito en un ERP de producción. Se formatea **tal y
    como llega**; quien decide en qué huso está ese instante es el adaptador,
    que es quien conoce la configuración.

    Levanta `CierreFallido` **antes de componer nada** si el plan no es
    cerrable (R10) o si el login no vale (R28, R35). Son redes de seguridad: el
    camino normal ya lo impide antes, en `paso_cierre`. Pero componer las
    piezas de otra manera —un script suelto, un `python -c`— no puede producir
    una escritura que nadie autorizó ni una fila de log sin firma.
    """
    _exigir_plan_cerrable(plan)
    login = _login_admisible(plan.login_sigrid)

    reclamacion = plan.reclamacion
    fecha, hora = fecha_y_hora_de_sigrid(ahora)

    return {
        "database": base_datos,
        "statements": [
            {
                "sql": SQL_UPDATE_ESTADO,
                "parameters": [
                    reclamacion.estado_destino_est,
                    reclamacion.ide,
                    reclamacion.tip,
                    reclamacion.est,
                ],
            },
            {
                "sql": SQL_INSERT_LOG,
                "parameters": [
                    LOG_ORIGEN,
                    LOG_OPERACION_PROCESO,
                    fecha,
                    hora,
                    login,
                    TEXTO_LOG_CIERRE,
                    LOG_REALIZADO,
                    reclamacion.ide,
                    reclamacion.tip,
                    reclamacion.estado_destino_est,
                ],
            },
        ],
        "max_affected_rows": MAXIMO_FILAS_AFECTADAS,
    }


def fecha_y_hora_de_sigrid(instante: datetime) -> tuple[int, int]:
    """`fec` y `hor` en los formatos enteros del ERP (R24).

    `AAAAMMDD` y `HHMMSS`, los dos como enteros y **no** como texto: así los
    escribe Sigrid, y `sigrid_tablas.md` los declara «Entero tipo fecha» y
    hora. Los ceros a la izquierda no existen en un entero, y no hacen falta:
    lo que importa es que el número sea el correcto.

    El instante se formatea con el **huso que traiga puesto**. No se convierte
    aquí a propósito: este módulo es puro y no lee configuración; quien decide
    en qué hora local se registra el cierre es el adaptador.
    """
    return (
        instante.year * 10_000 + instante.month * 100 + instante.day,
        instante.hour * 10_000 + instante.minute * 100 + instante.second,
    )


def _exigir_plan_cerrable(plan: PlanDeCierre) -> None:
    """R10 · sin un plan que diga que se cierra, no se compone ninguna escritura."""
    if not plan.cerrable:
        raise CierreFallido(
            f"el plan de cierre de la reclamación {plan.reclamacion.codigo} no "
            f"es cerrable, así que no se compone ninguna escritura: "
            f"{plan.motivo or 'sin motivo declarado'}"
        )


def _login_admisible(login: str) -> str:
    """El login con el que se firma, comprobado (R28, R35).

    Dos rechazos, y ninguno de los dos se arregla «apañándolo»:

    - **vacío**: firmaría el cierre a nombre de nadie;
    - **más largo que el campo del ERP**: un login truncado es **otro login**,
      y lo que quedaría escrito es que cerró la incidencia alguien que no
      existe. Se rechaza en vez de truncar.

    El motivo **no lleva el login** (R45): estos mensajes acaban en un log que
    lee cualquiera que abra Application Insights.
    """
    limpio = (login or "").strip()
    if not limpio:
        raise CierreFallido(
            "no hay login de Sigrid con el que firmar el cierre: la fila de "
            "auditoría del ERP no puede quedarse sin firma"
        )
    if len(limpio) > LONGITUD_MAXIMA_LOGIN:
        raise CierreFallido(
            f"el login de Sigrid no cabe en el campo del ERP, que admite "
            f"{LONGITUD_MAXIMA_LOGIN} caracteres: no se trunca, porque un "
            f"login truncado es otro login"
        )
    return limpio
