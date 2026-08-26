# services/postventa-api/domain/ports/erp.py
"""El puerto del ERP: lo que el dominio necesita de Sigrid (F-009).

Aquí no hay HTTP, ni SQL, ni `sigrid-api`, ni clave de función. El dominio sabe
que existe **un sitio donde vive la reclamación y donde se puede cerrar**, y
nada más. Quien sabe que debajo hay una pasarela es
`infrastructure/sigrid/`, y esa es la única pieza que hay que reescribir si
mañana el acceso al ERP cambia de forma.

## Tres operaciones, y ninguna decide si se cierra

Es deliberado, y es lo que hace probable a la feature más peligrosa del
proyecto: **toda** la decisión vive en `domain/models/cierre.py` y en
`application/pipelines/paso_cierre.py`, que son puros y se ejercitan enteros
con dobles en memoria. El adaptador es mecánico —lee, comprueba y escribe lo
que le den— porque es el único sitio del servicio que no se puede ejercitar sin
tocar el ERP de producción.

Lo que sí está cerrado aquí dentro: `cerrar` recibe un `PlanDeCierre`, no una
reclamación suelta ni un número de estado. No hay forma de pedirle «cierra esto
y ya» sin haber pasado antes por el dry-run que produjo el plan (R8, R10). La
manera de que no se escriba sin dry-run no es acordarse de hacerlo: es que el
argumento no exista.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from domain.models.cierre import PlanDeCierre, Reclamacion

__all__ = ["ErpPort"]


@runtime_checkable
class ErpPort(Protocol):
    """El ERP donde vive la reclamación, sea quien sea quien lo implemente."""

    def leer_reclamacion(
        self, *, codigo: str, codigo_estado_cierre: str
    ) -> Reclamacion | None:
        """La reclamación con ese código, con sus dos estados ya legibles.

        Es **la consulta del dry-run** (R8) y no escribe nada. Resuelve el
        estado de destino contra `conest` por su **código** (R1) y trae el de
        origen legible, de una sola vez.

        Devuelve `None` si no hay ninguna reclamación con ese código.

        Levanta `ReclamacionNoLocalizada` si hay más de una (R7) y
        `EstadoDeCierreNoResoluble` si el estado de cierre no se resuelve a
        exactamente una fila (R2). En los dos casos, **sin haber escrito
        nada**: son lecturas.
        """
        ...

    def existe_usuario(self, *, login: str) -> bool:
        """¿Ese login existe **exactamente una vez** en el ERP? (R30).

        Es una lectura, y va aparte de la anterior porque su fallo tiene motivo
        propio y mensaje propio: quien lo recibe tiene que saber que lo que hay
        que hacer es dar de alta la correspondencia a mano, no reintentar.

        `False` significa «no existe, o hay ambigüedad»: las dos cosas acaban
        igual —no se cierra (R31)— y ninguna de las dos autoriza a escribir un
        login en el log del ERP (R32).
        """
        ...

    def cerrar(self, *, plan: PlanDeCierre, ahora: datetime) -> int:
        """Ejecuta el cierre y devuelve **cuántas filas** se han tocado.

        Las dos sentencias —el `UPDATE` de `con.est` y el `INSERT` de
        `dbo.log`— van en **un solo batch transaccional** (R22) con un tope de
        filas afectadas que no puede pasar de las dos esperadas (R23). Un
        cierre real devuelve `2`; cualquier otra cosa es un error con su
        motivo, nunca un cierre dado por bueno.

        Levanta `CierreDeshabilitado` si aquí no se escribe,
        `EstadoCambiadoDesdeElDryRun` si la reclamación se movió entre el
        dry-run y la escritura (R11) y `CierreFallido` en lo demás. **No
        reintenta el cierre por su cuenta** (R27): reintentar contra un ERP de
        producción sin que nadie mire es cómo se cierran dos veces las cosas.

        Ningún mensaje lleva el cuerpo crudo del error, ni la clave de
        función, ni ningún dato del parte (R46, R50): acaban en un log.
        """
        ...
