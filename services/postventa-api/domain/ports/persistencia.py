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

from domain.models.estado import DecisionEstado, SituacionParte
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

        **Y nada más**: una sola sentencia.

        > **Enmienda del 2026-09-16 · F-030 T7 (`design.md` §5.1).** Hasta hoy
        > este contrato decía dos cosas que ya no son ciertas, y la segunda es
        > la descripción literal del defecto que F-030 arregla. Decía:
        >
        > *«**Y revoca la aprobación humana cuyo veredicto ya no es este**
        > (F-026, R30), en la misma operación. […] La alternativa —comprobar la
        > vigencia al leer— obligaría a tener delante el veredicto y la
        > aprobación en todos los sitios que miran, incluidos los tres pasos
        > del circuito, cuyo cuerpo de petición no trae ni los motivos ni las
        > observaciones y por tanto **no puede** recomputar la huella.»*
        >
        > **La revocación se retiró en F-028 T15.** La vigencia de una
        > aprobación se resuelve **al derivar**, comparando en
        > `estado.py::_aprueba_lo_que_hay` la huella apuntada en el histórico
        > con la del veredicto de ahora. El adaptador ya llevaba su enmienda;
        > el puerto se había quedado sin ella.
        >
        > **Y la premisa era cierta y dejó de serlo.** Los tres pasos del
        > circuito no recomputan la huella **del cuerpo**: la recomponen del
        > **veredicto guardado**, que viene en `SituacionParte.validacion` y
        > llega con la consulta que ya hacían (F-030 R1, R18). Dejar escrito
        > que «no pueden» era dejar escrito el razonamiento que llevó a
        > fabricar un `ResultadoValidacion` de pega en los tres endpoints, y
        > eso dejó sin archivar un parte que una persona había aprobado
        > (RS26.09/0178).
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

    def consultar_situacion(self, *, hash_parte: str) -> SituacionParte:
        """Lo que hace falta saber de un parte para derivar su estado (F-028).

        **Una sola llamada** y **cuatro** cosas de vuelta (R2): el veredicto
        guardado, la última decisión **humana**, el último estado registrado
        —solo para la regla de constancia— y el estado de la traza de cierre.
        Son los cuatro que consume `estado_del_parte`, y vuelven juntos para
        que quien deriva el estado no pueda mezclar una fuente con otra. Quien
        pregunta no tiene que cruzar cuatro tablas ni saber que el histórico
        existe.

        > **Enmienda del 2026-09-16 · F-030 T7 (`design.md` §5.1).** Eran tres:
        > el veredicto se lo buscaba cada consumidor por su cuenta. Los tres
        > endpoints del circuito —que no reciben la extracción y no la van a
        > recibir nunca, porque pedirla obligaría al front a reenviar el DNI y
        > las observaciones manuscritas del cliente en cada llamada— acabaron
        > **fabricándolo** desde el cuerpo de la petición, y con eso un parte
        > aprobado por una persona dejó de archivarse (RS26.09/0178).
        >
        > El veredicto viaja **dentro de la misma consulta**, así que la cuarta
        > cosa no cuesta ninguna consulta más por parte y por paso (R18).

        Que los cuatro huecos vengan vacíos **no es un error**: es el caso
        normal del primer día. Todo parte nace sin veredicto, sin decisión, sin
        fila y sin traza de cierre, y de ahí tiene que salir un estado
        igualmente (`estado_del_parte` lo resuelve). Y un parte del que no
        consta ni la ficha se comporta igual que uno sin validar: los dos
        huecos, nunca un error de base de datos (F-030 R9).

        La leen las tres puertas del circuito, y la leen **de aquí y nunca del
        cuerpo de la petición** (R33): si viniera del cuerpo, quien llama podría
        afirmar que alguien aprobó lo que nadie aprobó —o que un parte que la
        validación mandó a revisión manual es apto—, y con eso se cierra en el
        ERP de producción una reclamación que la validación había rechazado.

        La decisión que vuelve es la **humana**, no la última fila: las de
        máquina son constancia, nunca criterio (R26).
        """
        ...

    def registrar_decision(self, *, decision: DecisionEstado) -> ResultadoGuardado:
        """Añade una fila al histórico de estado. **Append-only** (F-028, R21).

        Es la única operación de este puerto que **no** es idempotente por
        clave, y es a propósito: el histórico acumula. Ninguna fila se pisa y
        ninguna se borra, porque un ciclo aprobar → rechazar → aprobar tiene
        que dejar las tres y ninguna puede quedar tapada por la siguiente
        (R25). Quien evita las filas repetidas es la **regla de constancia**
        —solo se escribe si el estado derivado cambió—, no la base.

        De quien decide se guarda el `oid` opaco de Entra ID y nada más (R15);
        de la máquina, ningún autor: `decidido_por` a `None` **es** «lo decidió
        la máquina» (R24).
        """
        ...

    def consultar_estado_cierre(self, *, hash_parte: str) -> str | None:
        """El estado de la traza de cierre de ese parte, o `None` (F-028, R18).

        `None` **no es un error**: es que a ese parte no se le ha intentado
        cerrar nada todavía. Vuelve **en crudo**, como cadena: el dueño de lo
        que puede haber ahí es el `CHECK` de `sql/06_cierres.sql`, y la
        derivación lo compara por valor contra `ESTADOS_DE_CIERRE_EN_FIRME`.

        Se lee cada vez en vez de guardar una copia nuestra porque `cerrado`
        **pertenece a otro sistema**: una copia acabaría diciendo que un parte
        está cerrado cuando no lo está, o al revés (`design.md` §3).
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
