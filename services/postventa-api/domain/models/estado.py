# services/postventa-api/domain/models/estado.py
"""El estado de un parte: pendiente, aprobado, rechazado o cerrado (F-028).

**Dominio puro.** Ni red, ni base de datos, ni IA, ni reloj: aquí solo hay
cuatro nombres, tres datos y el criterio que los combina. Eso es lo que permite
probar entera la pieza que decide si un parte llega a archivarse en SharePoint
y a cerrar una incidencia en el ERP de producción.

## Qué problema resuelve este módulo

Hasta F-028, «¿en qué estado está este parte?» no tenía respuesta en ningún
sitio. Había **cuatro hechos en cuatro tablas** —el veredicto de F-004 en
`validaciones`, la aprobación humana de F-026 en `aprobaciones`, la traza de
archivo de F-006 y la de cierre de F-009— y cada consumidor los cruzaba a su
manera: las tres puertas del backend con `admite_circuito`, el semáforo del
front con `aprobacionVale`, el selector de la tanda con otra cosa. Tres
criterios del mismo concepto divergen siempre, y el día que diverjan el
síntoma será una incidencia cerrada que no tocaba.

Aquí se escribe ese criterio **una vez** (R2, R17). Nadie más tiene copia: ni
el front —que pinta el estado que le manda el backend—, ni una vista SQL.

## El estado **se deriva, no se guarda** (R16, `design.md` §3)

No hay ninguna columna `estado` en `postventa.partes` y es deliberado. El
argumento decisivo no es el coste sino de quién es el dato: `cerrado`
**pertenece a otro sistema**, y mantener una copia nuestra de un hecho del ERP
es exactamente la forma de acabar diciendo que un parte está cerrado cuando no
lo está, o al revés. Derivándolo no puede contradecir a nadie: si un camino
falla a medias, el estado se recalcula solo, y los partes que ya estaban en la
base tienen estado desde el primer día sin rellenar nada hacia atrás.

Lo que sí se guarda es el **histórico** de cambios (`postventa.historico_estado`,
append-only): constancia de lo que pasó, **nunca criterio** (R26). Si mañana
faltara una fila, el estado seguiría siendo el correcto y lo único perdido
sería una línea del relato.

## Lo que este módulo **no** hace

No toca el veredicto. Lo que dijo F-004 —el veredicto, el destino y los
motivos— sigue dicho y consultable después de cualquier cambio de estado
(R8): la decisión de una persona se registra **al lado, nunca encima**, que es
la regla que gobernaba F-026 entera y que F-028 conserva.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.models.persistencia import EstadoCierre

__all__ = [
    "ESTADOS_DE_CIERRE_EN_FIRME",
    "LIMITE_MOTIVO",
    "DecisionEstado",
    "EstadoParte",
    "SituacionParte",
]


class EstadoParte(str, Enum):
    """En qué estado está un parte. **Son cuatro y no hay más** (R1, D1).

    La lista es cerrada y la decidió el humano el 2026-09-15. Un quinto estado
    no sería una ampliación inocente: cada consumidor —las tres puertas del
    backend, el semáforo, el selector de la tanda— tendría que decidir qué
    hacer con él, y el que no lo hiciera lo trataría como «aprobado» o como
    «no aprobado» por accidente.

    Qué significa cada uno:

    - **`pendiente`**: la máquina no lo declaró apto y nadie ha decidido
      todavía. Es donde nace todo lo que no es verde (R4).
    - **`aprobado`**: entra en el circuito de archivo, gráfico y cierre. Se
      llega por dos caminos —el veredicto apto con destino `archivo_y_cierre`
      (R3) o la decisión de una persona (R9)— y en pantalla se distinguen
      (R39).
    - **`rechazado`**: alguien lo miró y dijo que no. **No se archiva, no se
      adjunta y no se cierra** (R5), aunque el veredicto sea apto: lo
      automático puede retirar un permiso, nunca concederlo.
    - **`cerrado`**: la incidencia está cerrada en el ERP. Es **terminal**
      (R7): de aquí no sale ninguna flecha, porque lo escrito en Sigrid y en
      SharePoint no se deshace desde aquí y cambiar el estado solo conseguiría
      que nuestra base dijera algo distinto del ERP.

    Hereda de `str` como `EstadoArchivo` y `EstadoCierre`, y por lo mismo: para
    que viaje a JSON y a SQL sin que nadie tenga que acordarse de `.value`.
    """

    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CERRADO = "cerrado"


#: Los estados de la traza de cierre que dejan un parte **`cerrado`** (R18).
#:
#: Salen de `EstadoCierre` y no de dos cadenas escritas a mano: el dueño de lo
#: que puede haber en esa columna es el `CHECK` de `sql/06_cierres.sql`, y
#: `EstadoCierre` es su reflejo en el código. Dos copias del mismo criterio
#: divergen siempre.
#:
#: Son estos dos y no más. `dry_run_ok` es un **ensayo** y no ha escrito nada;
#: `error` es una incidencia que sigue abierta y que hay que poder reintentar;
#: `pendiente` es que ni se ha intentado. Si alguno entrara aquí, el parte se
#: daría por cerrado —estado terminal— sin que nadie hubiera escrito en Sigrid,
#: y no habría forma de volver a intentarlo.
#:
#: `ya_cerrada` **sí** entra, y no es un error: la incidencia estaba cerrada
#: antes de que llegáramos nosotros. El hecho que importa es el mismo —esa
#: reclamación está cerrada en el ERP— y lo que hay que hacer con el parte
#: también.
ESTADOS_DE_CIERRE_EN_FIRME: tuple[str, ...] = (
    EstadoCierre.CERRADO.value,
    EstadoCierre.YA_CERRADA.value,
)

#: Cuántos caracteres admite el motivo de una decisión (R13).
#:
#: El tope vive en el dominio y no en el handler: el borde es quien lo aplica,
#: pero el número es una regla del modelo y tiene que poder leerlo también
#: quien componga la fila. 500 da para explicar por qué se rechaza un parte y
#: no da para pegar ahí dentro media transcripción del papel.
LIMITE_MOTIVO = 500


@dataclass(frozen=True)
class DecisionEstado:
    """Un cambio de estado, con quién lo decidió, cuándo y por qué (R22).

    Es **una fila del histórico append-only** y también el objeto con el que
    viaja la última decisión humana cuando se deriva el estado. Inmutable a
    propósito: una decisión tomada no se reescribe, y lo que impide el
    descuido de leerla, cambiarle el estado y volver a guardarla es que no se
    pueda.

    `decidido_por` es el `oid` **opaco** de Entra ID y nada más (R15): nunca el
    correo, nunca el nombre y **nunca el login del ERP**. Es el mismo trato que
    ya reciben `cierres.confirmado_por` y `graficos.confirmado_por`, y por el
    mismo motivo: para saber que alguien decidió no hace falta saber quién es.

    `decidido_por` a `None` significa que **lo decidió la máquina** (R24), y
    esa es toda la diferencia entre una fila humana y una de constancia.
    Escribir ahí `"sistema"` sería inventarse un autor, y convertiría una
    anotación en una acusación.

    `motivo` es texto de **quien revisa**, no del papel: nunca el DNI, nunca
    las observaciones manuscritas, nunca la descripción (R13, R52). Es
    obligatorio al rechazar y opcional al aprobar (R11, R12), pero eso lo
    exige el borde: aquí no hay nada que impida construir una decisión sin él,
    porque las filas de máquina tampoco lo llevan.

    `huella_veredicto` dice **sobre qué veredicto exacto** se decidió, y es lo
    que hace que una aprobación deje de contar cuando el veredicto cambia
    (R19). Es un `sha256` en hexadecimal: no lleva dentro ni una letra del
    texto manuscrito (F-026 R15).

    `estado_anterior` puede ser `None`, y significa «no había estado
    registrado antes»: es la primera fila de ese parte.
    """

    hash_parte: str
    estado: EstadoParte
    decidido_at_utc: datetime
    estado_anterior: EstadoParte | None = None
    decidido_por: str | None = None
    motivo: str | None = None
    huella_veredicto: str | None = None

    @property
    def por_persona(self) -> bool:
        """¿La tomó una persona, o fue constancia de lo que dijo la máquina?

        Existe para que ni el borde ni el front tengan que acordarse de
        comparar contra `None`: es la marca de R39 —«aprobado por una persona»
        frente a «lo dio por bueno la máquina»— y tiene que salir de un sitio.
        """
        return self.decidido_por is not None


@dataclass(frozen=True)
class SituacionParte:
    """Lo que hay que saber de un parte para derivar su estado. **Tres cosas.**

    Quien pregunta hace **una** llamada al repositorio y recibe esto, que es lo
    que pide R2: no cruzar cuatro tablas ni conocer el veredicto, la
    aprobación, el archivo y el cierre por separado.

    Y son tres y nada más, cada una con su porqué:

    - `decision_humana`: la **última** fila humana del histórico. Manda sobre
      la máquina (R9) y es lo único que puede rechazar un parte apto.
    - `ultimo_estado_registrado`: el estado de la última fila, sea de quien
      sea. **No es criterio de nada** (R26): sirve solo para la regla de
      constancia —si el estado derivado no es este, se añade una fila— y de
      ahí sale que un reproceso que no cambia nada no escriba nada.
    - `estado_cierre`: lo que dice la traza de cierre de F-009. Gana a todo
      (R18), porque `cerrado` es un hecho del ERP y no una opinión nuestra.

    Una cuarta cosa aquí sería una invitación a decidir con ella, y lo que se
    decide se decide en `estado_del_parte`.

    Que los tres huecos vengan vacíos **no es un error**: es el caso normal del
    primer día. Todo parte nace sin decisión, sin fila y sin traza de cierre, y
    de ahí tiene que salir un estado igualmente.

    Esto viene **del repositorio y nunca del cuerpo de la petición** (R33). Es
    el mismo argumento que escribió F-012 para `traza_grafico` y que F-026
    heredó: si viniera del cuerpo, quien llama podría afirmar que alguien
    aprobó lo que nadie aprobó, y con eso se cierra en el ERP de producción una
    reclamación que la validación había rechazado.
    """

    decision_humana: DecisionEstado | None = None
    ultimo_estado_registrado: EstadoParte | None = None
    estado_cierre: str | None = None
