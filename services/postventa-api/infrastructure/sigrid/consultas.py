# services/postventa-api/infrastructure/sigrid/consultas.py
"""El SQL de **lectura** del cierre: texto y parámetros, sin abrir nada.

Módulo **puro**, igual que `infrastructure/persistencia/sentencias.py` y por el
mismo motivo: el SQL más delicado del servicio se comprueba carácter a carácter
en un test unitario, no contra el ERP de producción. Aquí no hay `httpx`, no
hay red y no se escribe nada.

**Ningún valor se interpola nunca en el texto**: todo viaja como marcador `?`,
como exige `azure-apps/sigrid_api.md` §5.2. Ni el tipo de concepto, ni el
código de la reclamación, ni el código del estado de cierre.

## Una sola consulta para el dry-run

Trae la reclamación, su estado de origen ya traducido a `cod` / `res` y el
estado de destino **resuelto contra `dbo.conest` por su código** (R1), todo de
una vez. Es lo que recomendó F-008 §6.4.6: una segunda llamada para traducir un
número a `PTE / PENDIENTE` sería otro viaje al ERP por cada dry-run.

## Lo que esta consulta NO hace, y es deliberado

**No cuenta gráficos** (R20). Tras la decisión del humano del 2026-08-26 el
orden es validar → cerrar → subir el PDF, y la precondición del cierre es
**propia**: parte apto (R16) y archivado (R17). Un `COUNT` aquí habría dejado a
F-009 sin poder cerrar prácticamente nada — el 98,7 % de las reclamaciones
abiertas no tiene gráfico, porque subirlo y cerrar son el mismo gesto en el
flujo manual—. Un control negativo de `test_f009_consultas.py` comprueba que
este texto no nombra ninguna de las dos tablas de gráficos del ERP.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.models.cierre import CODIGO_ESTADO_CIERRE, Reclamacion
from domain.models.errores import (
    EstadoDeCierreNoResoluble,
    ReclamacionNoLocalizada,
)

__all__ = [
    "COLUMNAS_RECLAMACION",
    "SQL_RECLAMACION",
    "SQL_USUARIO",
    "fila_a_reclamacion",
    "reclamacion_unica",
    "select_reclamacion",
    "select_usuario",
]

#: Las once columnas del `SELECT`, en el orden en que vuelven.
#:
#: Es **la misma lista** que recorre `fila_a_reclamacion`: dos listas del mismo
#: concepto divergen siempre, y aquí divergir significa leer el estado de
#: origen donde está la empresa.
COLUMNAS_RECLAMACION: tuple[str, ...] = (
    "c.ide",
    "c.emp",
    "c.tip",
    "c.est",
    "c.cod",
    "c.res",
    "eo.cod",
    "eo.res",
    "ed.est",
    "ed.cod",
    "ed.res",
)

#: La consulta del dry-run (`design.md` §7.1).
#:
#: Los dos `LEFT JOIN` son a la misma tabla de estados con dos alias: `eo` es
#: el estado de **origen** —el que tiene hoy la reclamación— y `ed` el de
#: **destino**, resuelto por código. Son `LEFT` y no `INNER` a propósito: si no
#: casaran, un `INNER JOIN` devolvería cero filas y el error saldría como «esa
#: reclamación no existe», que manda a buscar donde no es.
SQL_RECLAMACION = (
    f"SELECT {', '.join(COLUMNAS_RECLAMACION)}\n"
    "FROM dbo.con c\n"
    "LEFT JOIN dbo.conest eo ON eo.tip = c.tip AND eo.est = c.est\n"
    "LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?\n"
    "WHERE c.tip = ? AND c.cod = ?"
)

#: La verificación del login contra el maestro de usuarios (R30, §7.2).
#:
#: Va aparte de la anterior porque su fallo tiene motivo propio y mensaje
#: propio: quien lo recibe tiene que saber que lo que toca es dar de alta la
#: correspondencia a mano, no reintentar.
SQL_USUARIO = "SELECT COUNT(*) FROM dbo.usu WHERE cod = ?"


def select_reclamacion(
    *, tip: int, codigo: str, codigo_estado_cierre: str
) -> tuple[str, tuple]:
    """La consulta del dry-run, con sus tres parámetros (R1, R4, R5).

    El orden de los parámetros es el de los `?` en el texto, y el primero es el
    del `JOIN`, no el del `WHERE`: el estado de destino se resuelve **dentro**
    de la propia consulta.

    `tip` entra por parámetro y no está pegado al SQL por lo mismo que el
    estado: es configuración de la instalación, y cambiar de instalación no
    puede exigir tocar una sentencia.
    """
    return SQL_RECLAMACION, (codigo_estado_cierre, tip, codigo)


def select_usuario(*, login: str) -> tuple[str, tuple]:
    """¿Cuántas veces existe ese login en `dbo.usu`? (R30, R31).

    Tiene que devolver exactamente 1. Cero es «ese login no existe» y más de
    uno es una ambigüedad; las dos cosas acaban igual —no se cierra— y ninguna
    autoriza a firmar en el log del ERP.
    """
    return SQL_USUARIO, (login,)


def reclamacion_unica(
    filas: Sequence[Sequence[Any]], *, codigo: str
) -> Reclamacion | None:
    """La reclamación de la consulta, o el motivo por el que no se cierra.

    Tres salidas, y las tres son **lecturas**: aquí no se ha escrito nada y no
    se va a escribir nada.

    1. **Cero filas** → `None`. Ese código no está en el ERP. No se levanta
       aquí porque quien decide qué hacer con «no está» es el paso, y el
       mensaje que necesita el usuario lo compone el borde.
    2. **Varias filas** → se distingue **cuál de los dos fallos** es, porque se
       arreglan de formas opuestas:
       - si todas son la **misma** reclamación (mismo `ide`), lo que está
         duplicado es el estado en `conest`: es R2, y suponer cuál vale sería
         escribir un estado que nadie eligió;
       - si son reclamaciones distintas, el código no es único dentro del tipo:
         es R7, y elegir una sería cerrar la incidencia equivocada en
         producción.
    3. **Una fila sin estado de destino** → R2 otra vez: el `LEFT JOIN` no
       casó, `conest` no tiene el código de cierre y el número **no está en el
       código a propósito** (C3), así que no se supone.
    """
    if not filas:
        return None

    if len(filas) > 1:
        identificadores = {fila[0] for fila in filas}
        if len(identificadores) == 1:
            raise EstadoDeCierreNoResoluble(
                f"el maestro de estados devuelve {len(filas)} filas para el "
                f"estado de cierre de la reclamación {codigo}: no se puede "
                f"elegir una por nuestra cuenta y no se escribe nada"
            )
        raise ReclamacionNoLocalizada(
            f"la búsqueda del código {codigo} ha devuelto {len(filas)} "
            f"reclamaciones distintas dentro del mismo tipo y se esperaba una: "
            f"no se cierra ninguna"
        )

    reclamacion = fila_a_reclamacion(filas[0])
    if not reclamacion.estado_destino_cod or reclamacion.estado_destino_est is None:
        raise EstadoDeCierreNoResoluble(
            f"el maestro de estados no resuelve el código de cierre "
            f"«{CODIGO_ESTADO_CIERRE}» para la reclamación {codigo}: sin él no "
            f"se cierra, y el número no se escribe a mano"
        )
    return reclamacion


def fila_a_reclamacion(fila: Sequence[Any]) -> Reclamacion:
    """Una fila de `SQL_RECLAMACION`, de vuelta al dominio.

    Dos decisiones que no son cosméticas:

    - **Los códigos son texto y siguen siéndolo.** Misma regla que el código de
      obra en F-006: `int()` sobre un código es un bug, no una normalización.
    - **Un `NULL` del `LEFT JOIN` de origen sale como cadena vacía**, no
      revienta. Quien decide qué hacer con un estado ilegible es el dominio
      (R19): un estado que no se puede leer no es cerrable, y ese es su
      trabajo, no el de este mapeo.
    """
    (
        ide,
        emp,
        tip,
        est,
        codigo,
        descripcion,
        origen_cod,
        origen_res,
        destino_est,
        destino_cod,
        destino_res,
    ) = fila

    return Reclamacion(
        ide=int(ide),
        emp=int(emp),
        tip=int(tip),
        est=int(est),
        codigo=str(codigo),
        descripcion=str(descripcion or ""),
        estado_origen_cod=str(origen_cod or ""),
        estado_origen_res=str(origen_res or ""),
        estado_destino_est=None if destino_est is None else int(destino_est),
        estado_destino_cod=str(destino_cod or ""),
        estado_destino_res=str(destino_res or ""),
    )
