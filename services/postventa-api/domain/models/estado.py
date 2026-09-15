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

from domain.models.aprobacion import huella_de_veredicto
from domain.models.persistencia import EstadoCierre
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto

__all__ = [
    "ESTADOS_DE_CIERRE_EN_FIRME",
    "LIMITE_MOTIVO",
    "DecisionEstado",
    "EstadoParte",
    "SituacionParte",
    "decision_en_firme",
    "estado_de_la_maquina",
    "estado_del_parte",
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


def estado_de_la_maquina(validacion: ResultadoValidacion | None) -> EstadoParte:
    """En qué estado deja la **máquina** un parte, sin que nadie decida nada.

    Dos casos y solo dos (R3, R4):

    - **apto con destino `archivo_y_cierre`** → `aprobado`. El verde nace
      aprobado, y eso es lo que hace que el trabajo diario de Posventa no
      cambie: los verdes se siguen archivando en bloque, sin que nadie tenga
      que aprobar 22 partes a mano. Lo que F-028 añade no es un permiso más:
      es poder **rechazar** uno antes de que se archive.
    - **cualquier otra cosa** → `pendiente`, incluido no tener veredicto.

    Las **dos** condiciones hacen falta, y no es redundante: hoy F-004 no
    produce un apto con otro destino, pero el día que alguien añada un destino
    nuevo, lo que decide si un parte entra en el circuito que escribe en el ERP
    de producción no puede ser solo el color del veredicto. Es exactamente la
    pareja que ya exigía `admite_circuito` en F-026.

    No confundir `pendiente` con «no hay veredicto»: son lo mismo **aquí** y
    cosas distintas en las tres puertas, que siguen teniendo su error propio
    para el segundo caso porque se arregla revalidando, no decidiendo.
    """
    if validacion is None:
        return EstadoParte.PENDIENTE
    if (
        validacion.veredicto == Veredicto.APTO
        and validacion.destino == Destino.ARCHIVO_Y_CIERRE
    ):
        return EstadoParte.APROBADO
    return EstadoParte.PENDIENTE


def estado_del_parte(
    validacion: ResultadoValidacion | None,
    decision_humana: DecisionEstado | None,
    estado_cierre: str | None,
) -> EstadoParte:
    """En qué estado está un parte. **Esta es la única respuesta** (R2, R17).

    Tres hechos entran —lo que dijo la máquina, la última decisión de una
    persona y lo que dice la traza de cierre— y sale uno de los cuatro
    estados. Ni el borde, ni la aplicación, ni el front, ni una vista SQL
    tienen su propia copia de este criterio: se descartó a propósito una vista
    `postventa.v_estado_parte` que lo calculara en SQL, porque sería un segundo
    criterio escrito en otro lenguaje y divergiría a la primera corrección
    (`design.md` §3).

    **El orden en que resuelve es todo el criterio**, y va de lo que menos se
    puede discutir a lo que más:

    1. **el cierre gana a todo** (R18). Si la traza dice `cerrado` o
       `ya_cerrada`, el parte está `cerrado` y no hay más que hablar: eso no es
       una opinión nuestra, es un hecho del ERP que nosotros **leemos**.
       `cerrado` es además **terminal** (R7), así que de aquí no sale ninguna
       flecha: lo escrito en Sigrid y en SharePoint no se deshace desde aquí, y
       cambiar el estado solo conseguiría que nuestra base dijera algo distinto
       del ERP. La web lo explica en vez de fallar (R41).
    2. **la última decisión humana manda** sobre la máquina (R9), y las dos
       direcciones **no son simétricas**:
       - **`rechazado` → `rechazado`, sin caducidad.** Ni aunque el veredicto
         cambie, ni aunque pase a apto, ni aunque no haya huella con la que
         contrastar. Lo automático puede **retirar** un permiso; no puede
         concederlo. Si el rechazo caducara al cambiar el veredicto, bastaría
         con reprocesar la remesa para que un parte que alguien miró y rechazó
         volviera a entrar en la tanda.
       - **`aprobado` → `aprobado` solo si su huella es la del veredicto
         guardado ahora** (R19, que es F-026 R30 conservada). Si no lo es, se
         cae al punto 3 y **decide la máquina**: que una aprobación deje de
         contar no es que alguien haya rechazado el parte, y la pantalla los
         distingue (R43).
    3. **la máquina**: `estado_de_la_maquina` (R3, R4).

    Y solo cuentan las decisiones **de una persona** (R26): una fila de máquina
    del histórico es constancia, nunca criterio. Si contara, un parte que fue
    verde y dejó de serlo seguiría aprobado por una anotación, y el histórico
    se habría convertido en la segunda fuente de verdad que R16 evita.

    Una decisión humana a `pendiente` o a `cerrado` **no mueve nada**: no se
    puede pedir por el borde (R10), pero si una fila así llegara —de una
    migración, de una semilla mal hecha— lo que tiene que pasar es que decida
    la máquina, no que el parte quede colgado en un estado que nadie pidió.

    > **Consecuencia que se declara porque se ve rara y es correcta**: si el
    > veredicto cambia bajo una aprobación humana y **luego vuelve a ser el de
    > antes** —alguien corrige un campo y deshace la corrección—, la aprobación
    > **vuelve a contar**. Es lo que dice F-026: se aprobó *ese* veredicto, y
    > este es exactamente *ese* veredicto (su R32). Con el estado derivado sale
    > gratis; con el estado guardado habría que decidir a mano qué hacer.

    Función **pura**: mismas entradas, misma salida, sin consultas y sin
    reloj. Quien la llama trae los tres datos del repositorio de una sola vez
    (`SituacionParte`), y nunca del cuerpo de la petición (R33).
    """
    if estado_cierre in ESTADOS_DE_CIERRE_EN_FIRME:
        return EstadoParte.CERRADO

    if decision_humana is not None and decision_humana.por_persona:
        if decision_humana.estado is EstadoParte.RECHAZADO:
            return EstadoParte.RECHAZADO
        if decision_humana.estado is EstadoParte.APROBADO and _aprueba_lo_que_hay(
            decision_humana, validacion
        ):
            return EstadoParte.APROBADO

    return estado_de_la_maquina(validacion)


def _aprueba_lo_que_hay(
    decision: DecisionEstado, validacion: ResultadoValidacion | None
) -> bool:
    """¿La aprobación se tomó sobre **este** veredicto? (R19, R20).

    Se compara la huella que quedó apuntada con la del veredicto que hay
    guardado ahora. Volver a guardar el mismo veredicto da la misma huella y
    **no invalida nada** (R20, F-026 R32 conservada), que no es un detalle
    teórico: al recargar la pantalla hay que volver a subir la remesa, y eso
    reprocesa cada parte. Si eso caducara la aprobación, el trabajo de
    revisión se perdería cada vez que alguien pulsa F5.

    Los dos huecos van hacia el lado seguro: sin veredicto guardado no hay con
    qué comparar, y sin huella apuntada no se sabe sobre qué se decidió. En
    los dos casos la aprobación **no cuenta**, porque el precio de equivocarse
    hacia el otro lado es una incidencia cerrada en el ERP de producción que
    no tocaba.

    `huella_de_veredicto` es de F-026 y **no se toca** (D9): ni su criterio de
    normalización ni su valor cambian en esta feature, y hay tres controles
    negativos que lo vigilan (`design.md` §10).
    """
    if validacion is None or decision.huella_veredicto is None:
        return False
    return decision.huella_veredicto == huella_de_veredicto(validacion)


def decision_en_firme(
    validacion: ResultadoValidacion | None,
    decision_humana: DecisionEstado | None,
    estado_cierre: str | None,
) -> DecisionEstado | None:
    """**Quién** sostiene el estado de ahora: la persona, o nadie (R39, R43).

    `estado_del_parte` responde en qué estado está el parte. La pantalla
    necesita además saber si ahí lo puso una persona —para el anillo de R39 y
    para el «aprobado por una persona · <fecha>» de R43— o si el parte está
    donde está porque lo dijo la máquina o porque el ERP cerró la incidencia.

    Devuelve la decisión humana que **está en vigor**, o `None` si el estado
    actual no lo sostiene ninguna persona. Tres formas de que sea `None`, y las
    tres importan:

    - **no hay decisión humana**, o la única fila del histórico es de máquina
      (R26): una constancia no firma nada, y devolverla pondría la marca de
      «lo aprobó alguien» a los 22 partes verdes de una remesa que nadie ha
      mirado;
    - **el parte está `cerrado`**: ahí lo puso el ERP y gana a todo (R18),
      incluso a un rechazo humano registrado antes;
    - **la decisión ya no cuenta**: o pedía un estado que no manda —`pendiente`
      o `cerrado`, que R10 no ofrece pero una semilla podría dejar—, o es una
      aprobación tomada sobre **otro** veredicto (R19).

    Ese último caso es el que obliga a que esto viva en el dominio y no en el
    borde. Un parte **apto** con una aprobación humana caducada está
    `aprobado`, pero lo dice la máquina: quien se limitara a comparar «el
    estado derivado» con «el estado de la fila» los vería coincidir y la
    pantalla anunciaría «aprobado por una persona» con la fecha de una decisión
    que R19 ya había tumbado — que es justo la distinción que R43 pide
    enseñar.

    **No hay aquí una segunda copia del criterio** (R17): el estado se pide a
    `estado_del_parte` y la vigencia de una aprobación a `_aprueba_lo_que_hay`,
    que son los dos únicos sitios donde están escritas. Si mañana cambiara el
    orden de precedencia, cambia allí y esta respuesta se mueve con él.

    Función **pura**, como sus dos vecinas: los tres datos los trae quien llama
    del repositorio (`SituacionParte`), y nunca del cuerpo de la petición (R33).
    """
    if decision_humana is None or not decision_humana.por_persona:
        return None

    estado = estado_del_parte(validacion, decision_humana, estado_cierre)
    if estado is EstadoParte.CERRADO or decision_humana.estado is not estado:
        return None
    if estado is EstadoParte.APROBADO and not _aprueba_lo_que_hay(
        decision_humana, validacion
    ):
        return None
    return decision_humana
