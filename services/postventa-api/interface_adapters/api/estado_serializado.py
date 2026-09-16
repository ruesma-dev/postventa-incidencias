# services/postventa-api/interface_adapters/api/estado_serializado.py
"""Cómo viaja el estado de un parte en una respuesta HTTP (F-028, R38, R42).

Un módulo propio para dos funciones cortas, y tiene el mismo motivo que tenía
`aprobacion_serializada.py`, al que releva: **lo comparten dos endpoints**.
`POST /api/estado` lo devuelve porque acaba de escribir la decisión, y
`POST /api/parte` lo devuelve porque la pantalla tiene que saber en qué estado
está cada parte sin preguntarlo uno a uno (son 22 llamadas de más en una remesa
real).

Dos serializaciones del mismo hecho divergirían en la primera corrección, y lo
que divergiría es **qué se publica de una decisión que lleva dentro el `oid` de
una persona y un texto libre escrito por quien revisa**. Así que vive en un
sitio, y ese sitio no puede ser ninguno de los dos handlers: `estado.py` ya
importa de `parte.py` el envoltorio que cuenta los resultados, y devolverle el
favor los volvería mutuamente dependientes.

No es dominio: el dominio no sabe de JSON ni de claves de respuesta. Es la
traducción del borde, que es justo lo que hace `interface_adapters`.

## Lo que este módulo **no** decide

No deriva el estado ni decide quién lo firma: eso lo responden
`estado_del_parte` y `decision_en_firme`, en `domain/models/estado.py`, que son
el único sitio donde está escrito el criterio (R17). Aquí solo se elige **qué
de eso se publica**, que es la otra mitad del trabajo y la que tiene el
requisito de privacidad encima.
"""

from __future__ import annotations

from typing import Any

from domain.models.estado import (
    DecisionEstado,
    EstadoParte,
    SituacionParte,
    decision_en_firme,
    estado_del_parte,
)
from domain.models.validacion import ResultadoValidacion

__all__ = ["bloque_de_estado", "bloque_de_estado_derivado"]


def bloque_de_estado(
    estado: EstadoParte, decision: DecisionEstado | None
) -> dict[str, Any]:
    """El bloque `estado` de la respuesta. **Cuatro claves y ninguna más.**

    `decision` es la decisión **humana en vigor** —la que devuelve
    `decision_en_firme`— o `None` si el parte está donde está porque lo dijo la
    máquina o porque el ERP cerró la incidencia. De ahí salen las tres claves
    que acompañan al estado, y las tres están **siempre**: su valor dice qué
    pasa. Omitirlas obligaría a la pantalla a distinguir «no lo decidió nadie»
    de «esta respuesta la emitió una versión del backend que no sabía de
    estados», que es una distinción que nadie quiere hacer en JavaScript.

    Qué publica cada una:

    - `estado`: uno de los cuatro (R38). Es lo que pinta el semáforo;
    - `decidido_por_persona`: la marca de R39, que separa el parte que aprobó
      alguien del que dio por bueno la máquina;
    - `decidido_at_utc`: la fecha del texto de R43, o `None`;
    - `estado_anterior`: de dónde venía, o `None` si es su primera fila (R22).

    **Ni el `oid`, ni el correo, ni el nombre, ni el motivo** (R42, R52). El
    motivo es el que más tienta —parece informativo— y es el que más peligro
    tiene: lo escribe una persona en texto libre y puede llevar dentro el
    nombre de un cliente. La pantalla no lo necesita —le basta la marca— y
    quien audite lo lee en la base, que es donde sí está.
    """
    return {
        "estado": estado.value,
        "decidido_por_persona": decision is not None,
        "decidido_at_utc": (
            decision.decidido_at_utc.isoformat() if decision is not None else None
        ),
        "estado_anterior": (
            decision.estado_anterior.value
            if decision is not None and decision.estado_anterior is not None
            else None
        ),
    }


def bloque_de_estado_derivado(
    validacion: ResultadoValidacion | None, situacion: SituacionParte
) -> dict[str, Any]:
    """El mismo bloque, derivado de lo que dice el almacén (R2, R33).

    Es la forma que usa `POST /api/parte`: no acaba de escribir ninguna
    decisión, así que el estado y su firma salen de los dos hechos que trae la
    situación —la última decisión humana y la traza de cierre— cruzados con el
    veredicto que se acaba de guardar.

    La situación llega **del repositorio y nunca del cuerpo de la petición**
    (R33): si viniera de fuera, quien llama podría afirmar que un parte lo
    aprobó alguien que no lo aprobó, y con eso se cierra en el ERP de
    producción una reclamación que la validación había rechazado.
    """
    return bloque_de_estado(
        estado_del_parte(validacion, situacion.decision_humana, situacion.estado_cierre),
        decision_en_firme(
            validacion, situacion.decision_humana, situacion.estado_cierre
        ),
    )
