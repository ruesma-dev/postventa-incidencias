# services/postventa-api/domain/ports/persistencia.py
"""Puertos de persistencia: lo que el dominio necesita de un almacén.

Dos puertos y no uno gordo, porque son dos vidas distintas: lo que se guarda
**de un parte** (remesa, extracción, validación, archivo, cierre) y lo que se
guarda **de un usuario** (su preferencia de auto-cierre). El día que las
preferencias se muden a otro sitio —o que las lea el front por su cuenta— el
primero no se entera.

Aquí no hay SQL, ni nombres de tabla, ni `psycopg` (R30, R31): quien los
conoce es `infrastructure/persistencia/`, y esa es la única pieza que hay que
volver a escribir si mañana debajo hay otra cosa.

**Reprocesar no duplica.** Todas las operaciones de guardado son idempotentes
por diseño: la clave es el `hash_parte` que produce F-002, y guardar dos veces
el mismo parte actualiza la misma fila (R14–R17). Por eso devuelven
`ResultadoGuardado` y no `None`: quien llama necesita poder distinguir «se ha
creado» de «ya estaba» sin volver a consultar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    EntradaCola,
    PreferenciasUsuario,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
    TrazaGrafico,
)
from domain.models.remesa import ParteTroceado
from domain.models.validacion import ResultadoValidacion

__all__ = ["RepositorioPartesPort", "RepositorioPreferenciasPort"]


@runtime_checkable
class RepositorioPartesPort(Protocol):
    """El almacén de lo que le pasa a un parte, sea quien sea quien lo
    implemente."""

    def guardar_remesa(self, *, remesa: RegistroRemesa) -> ResultadoGuardado:
        """Deja constancia de una subida.

        Levanta `PersistenciaNoDisponible` si no se puede hablar con el
        almacén, y **nunca** vuelca en el mensaje ni el DSN ni la credencial.
        """
        ...

    def guardar_parte(
        self,
        *,
        parte: ParteTroceado,
        extraccion: ExtraccionParte,
        remesa_id: str,
        ahora: datetime,
    ) -> ResultadoGuardado:
        """Guarda el parte y lo que se leyó de él.

        De `parte` se toman su huella, su origen, sus páginas y el modo de
        detección; **nunca** sus bytes (R12, R40): el PDF lleva el DNI
        manuscrito, vive en SharePoint y el disco de este servidor es
        compartido y solo crece.

        Si el `hash_parte` ya existía, **actualiza** la fila: conserva su
        fecha de primera vez, refresca la de actualización e incrementa el
        contador de reprocesos (R14, R15).
        """
        ...

    def guardar_validacion(
        self, *, resultado: ResultadoValidacion, ahora: datetime
    ) -> ResultadoGuardado:
        """Guarda el veredicto del parte, **sustituyendo** el anterior (R17).

        No guarda la transcripción de las observaciones aunque el resultado la
        transporte: ya está en la fila del parte y una segunda copia de texto
        manuscrito de un cliente dobla la exposición y diverge (R21, R39).
        """
        ...

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        """Registra qué pasó al archivar el parte. Una fila por parte (R23)."""
        ...

    def guardar_cierre(self, *, traza: TrazaCierre) -> ResultadoGuardado:
        """Registra qué pasó al cerrar la incidencia.

        Un parte ya marcado como cerrado **no se pisa**: devuelve
        `SIN_CAMBIOS` y deja la fila intacta (R25). Es la diferencia entre
        registrar un cierre y volver a cerrarlo.
        """
        ...

    def guardar_grafico(self, *, traza: TrazaGrafico) -> ResultadoGuardado:
        """Registra qué pasó al adjuntar el parte como gráfico (F-012, R42, R43).

        Un parte ya marcado como `adjuntado` **no se pisa**: devuelve
        `SIN_CAMBIOS` y deja la fila intacta (R30). Es la diferencia entre
        registrar un gráfico y colgar un segundo.
        """
        ...

    def consultar_grafico(self, *, hash_parte: str) -> TrazaGrafico | None:
        """La traza del gráfico de ese parte, o `None` si no consta (F-012).

        `None` **no es un error**: es que a ese parte todavía no se le ha
        adjuntado nada. La leen dos sitios y por dos motivos distintos:
        `paso_grafico`, como **primera capa de idempotencia** —si dice
        `adjuntado`, no se llama a la pasarela ni se mandan los bytes (R24)—, y
        `paso_cierre`, como **precondición del `commit`**: ninguna reclamación
        se cierra sin que su parte conste dentro de Sigrid (R2, R49).
        """
        ...

    def cola_validacion_humana(self, *, limite: int) -> tuple[EntradaCola, ...]:
        """Los partes que esperan que una persona decida (R22).

        **Solo** los de destino `cola_validacion_humana`: un parte al que le
        faltan los mínimos va a revisión manual, y meterlo aquí haría que
        alguien decidiera sobre una reparación que el cliente ni siquiera dio
        por recibida.
        """
        ...


@runtime_checkable
class RepositorioPreferenciasPort(Protocol):
    """El almacén de lo que un usuario ha decidido sobre el auto-cierre."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        """La preferencia de ese usuario, identificado por su `oid` de Entra.

        Quien no ha decidido nada no tiene auto-cierre: se devuelve la
        preferencia en falso, no un `None`. El auto-cierre escribe en el ERP
        de producción, así que su valor por omisión solo puede ser «no».
        """
        ...

    def guardar_preferencias(
        self, *, preferencias: PreferenciasUsuario
    ) -> ResultadoGuardado:
        """Deja **una sola** fila por usuario (R27).

        Del empleado se guarda el `oid` opaco y nunca su correo ni su nombre:
        para saber si tiene auto-cierre no hace falta saber quién es.
        """
        ...
