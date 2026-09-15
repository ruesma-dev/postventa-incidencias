# services/postventa-api/interface_adapters/api/estado.py
"""Handler de `POST /api/estado`: la decisión humana sobre un parte (F-028).

**Sustituye a `POST /api/aprobar`**, no convive con él (`design.md` §5): dos
endpoints que escriben la misma decisión son dos caminos que divergen. Y hace
lo que aquel no podía —y era medio encargo de la feature—: **rechazar un parte
que la máquina había dado por bueno**. `/api/aprobar` contestaba 409 a
cualquier parte apto porque «no hay nada que aprobar»; aquí se registra la
decisión y el parte deja de archivarse, de adjuntarse y de cerrar su
incidencia.

## Endpoint propio, y no una clave más en `/api/parte` (R27)

Guardar ocurre en **cada revalidación**; decidir es un acto de una persona.
Colgar el cambio de estado de `/api/parte` lo convertiría en un efecto de
guardar, y el día que el autoguardado escriba se estaría rechazando solo. Una
petición, una decisión, una fila de auditoría.

## Y sin embargo guarda el parte (`design.md` §5)

Hace **las dos cosas en una sola llamada**: guarda el parte con su veredicto
—reutilizando `paso_persistencia`, que es idempotente— y escribe la decisión
con la huella de *ese mismo* veredicto.

Hacerlo en dos llamadas dejaría una ventana entre «lo que se guardó» y «lo que
se decidió», y lo que quedaría en la base sería una decisión sobre un veredicto
que no está escrito. Así, la huella apuntada es por construcción la del
veredicto que acaba de escribirse, que es lo que hace que R19 —una aprobación
vale para el veredicto sobre el que se tomó— pueda comparar algo.

## El veredicto se recalcula. Siempre (R28)

**Nunca** se acepta un veredicto ya hecho en el cuerpo, igual que en
`/api/parte` (R8 de F-019) y que en el endpoint al que este releva. Si llegara
hecho, quien llama elegiría la huella que se apunta y con ella decidiría cuándo
caduca su propia aprobación.

## Qué se guarda de la persona: el `oid`, y nada más (R15)

El `oid` opaco de Entra ID. Nunca el correo, nunca el nombre, nunca el login de
Sigrid. Es el mismo tratamiento que ya reciben `cierres.confirmado_por` y
`graficos.confirmado_por`. Y **no sale en la respuesta** (R42), como tampoco
sale el motivo: lo escribe una persona en texto libre y puede llevar dentro el
nombre de un cliente. Quien audite los lee en la base.

## No mira `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO` (R32)

Esas ventanas protegen SharePoint y el ERP, que son sistemas ajenos. Decidir
escribe en el esquema propio del proyecto, y atarlo dejaría sin poder registrar
el trabajo de revisión justo cuando las ventanas de escritura están cerradas,
que es como se despliega el entorno.

Y por lo mismo **no toca SharePoint ni Sigrid** (R37): cambiar de estado no
borra, no mueve y no renombra nada.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_persistencia import paso_persistencia
from config.settings import obtener_ajustes
from domain.models.aprobacion import huella_de_veredicto
from domain.models.errores import CambioDeEstadoInvalido, ParteCerrado
from domain.models.estado import (
    ESTADOS_DE_CIERRE_EN_FIRME,
    LIMITE_MOTIVO,
    DecisionEstado,
    EstadoParte,
    decision_en_firme,
)
from domain.models.validacion import validar_parte
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio
from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    CLAVES_DEL_PARTE,
    a_extraccion,
    a_lectura_de_firma,
    a_parte_troceado,
    a_remesa_id,
    bloque,
)
from interface_adapters.api.estado_serializado import bloque_de_estado
from interface_adapters.api.parte import AnotaLosResultados

__all__ = ["ESTADOS_MANUALES", "cambiar_estado_http"]

#: Los dos únicos destinos que una persona puede pedir (R10).
#:
#: A `pendiente` no se vuelve a mano —quien quiera volver a mirarlo lo tiene en
#: el histórico— y a `cerrado` solo se llega cerrando la incidencia en el ERP,
#: que es un hecho de otro sistema y no una opinión nuestra.
ESTADOS_MANUALES: tuple[EstadoParte, ...] = (
    EstadoParte.APROBADO,
    EstadoParte.RECHAZADO,
)

#: Lo que se responde en `resultado_estado` según lo que haya pasado.
CAMBIADO = "cambiado"
SIN_CAMBIOS = "sin_cambios"


def cambiar_estado_http(
    cuerpo: Any,
    *,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Registra que una persona mueve este parte, y devuelve qué pasó (R9).

    Levanta `CambioDeEstadoInvalido`, `PeticionDePersistenciaInvalida` y
    `CuerpoDeValidacionInvalido` (→ 400) diciendo **qué** falta, `ParteCerrado`
    (→ 409) diciendo que de ahí no se sale, y deja subir sin traducir
    `ReferenciaNoConsta` (→ 409), `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503): convertir eso en códigos HTTP es
    trabajo del borde.

    **En todos los rechazos no se ha escrito nada** (R31), y el orden del
    cuerpo de esta función es lo que lo sostiene: las cuatro claves propias se
    miran antes que nada, y la puerta del parte cerrado va **antes** de
    `paso_persistencia`. Comprobarla después dejaría filas a su paso —la ficha
    del parte, su veredicto y quizá una fila de constancia— antes de decirle
    que no a quien preguntaba.

    Dos resultados posibles y los dos son **200**: `cambiado` cuando se escribe
    la fila, y `sin_cambios` cuando el parte ya estaba en ese estado **por la
    misma decisión humana**. Dos pulsaciones seguidas son un dedo, no un error,
    y el estado final es el que se pedía; una segunda fila idéntica solo
    llenaría el histórico de renglones que no cuentan nada.

    Ojo con qué cuenta como «la misma decisión»: la constancia automática de un
    parte verde **no** cuenta (R26), y una aprobación tomada sobre otro
    veredicto tampoco (R19). En los dos casos sí se escribe la fila, y en el
    primero es lo que permite que la pantalla distinga lo que aprobó una
    persona de lo que dio por bueno la máquina (R39).
    """
    if not isinstance(cuerpo, Mapping):
        raise CambioDeEstadoInvalido(
            "el cuerpo tiene que ser un objeto JSON con 'remesa_id', 'parte', "
            "'extraccion', 'firma', 'estado', 'usuario_oid' y 'confirmado'"
        )

    # Lo propio de este endpoint va primero, y no es orden caprichoso: es lo
    # que decide si esto llega a escribirse a nombre de una persona.
    estado_pedido = _estado_pedido(cuerpo.get("estado"))
    usuario_oid = _usuario_oid(cuerpo.get("usuario_oid"))
    _exigir_confirmacion(cuerpo.get("confirmado"))
    motivo = _motivo(cuerpo.get("motivo"), estado_pedido)

    remesa_id = a_remesa_id(cuerpo.get("remesa_id"))
    parte = a_parte_troceado(bloque(cuerpo, "parte", CLAVES_DEL_PARTE))
    extraccion = a_extraccion(bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION))
    lectura = a_lectura_de_firma(bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA))

    # R28: el veredicto se emite AQUÍ, con las reglas de F-004. Lo que venga
    # en el cuerpo no se mira.
    validacion = validar_parte(extraccion, lectura)

    almacen = AnotaLosResultados(
        repositorio
        if repositorio is not None
        else construir_repositorio(obtener_ajustes())
    )
    momento = ahora if ahora is not None else datetime.now(UTC)

    _exigir_que_no_este_cerrado(almacen, parte.hash)

    contexto = ContextoParte(
        parte=parte,
        extraccion=extraccion,
        lectura_firma=lectura,
        validacion=validacion,
    )
    paso_persistencia(contexto, almacen, remesa_id=remesa_id, ahora=momento)

    # **Después** de guardar, y el orden es el requisito: `paso_persistencia`
    # puede haber añadido la fila de constancia del estado derivado (R23), y
    # leer antes daría un `estado_anterior` que la propia llamada ya ha movido.
    situacion = almacen.consultar_situacion(hash_parte=parte.hash)
    en_firme = decision_en_firme(
        validacion, situacion.decision_humana, situacion.estado_cierre
    )
    if en_firme is not None and en_firme.estado is estado_pedido:
        return _respuesta(contexto, almacen, SIN_CAMBIOS, estado_pedido, en_firme)

    fila = DecisionEstado(
        hash_parte=parte.hash,
        estado=estado_pedido,
        decidido_at_utc=momento,
        estado_anterior=situacion.ultimo_estado_registrado,
        decidido_por=usuario_oid,
        motivo=motivo,
        huella_veredicto=huella_de_veredicto(validacion),
    )
    almacen.registrar_decision(decision=fila)
    return _respuesta(contexto, almacen, CAMBIADO, estado_pedido, fila)


def _respuesta(
    contexto: ContextoParte,
    almacen: AnotaLosResultados,
    resultado_estado: str,
    estado: EstadoParte,
    decision: DecisionEstado,
) -> dict[str, Any]:
    """El contrato de la respuesta, compuesto en un solo sitio.

    Los dos caminos —se escribió fila o no— devuelven exactamente las mismas
    seis claves: quien llama no tiene que mirar `resultado_estado` para saber
    qué campos hay, solo para saber qué pasó.
    """
    return {
        "hash_parte": contexto.parte.hash,
        "resultado_parte": almacen.resultado_parte,
        "resultado_validacion": almacen.resultado_validacion,
        "resultado_estado": resultado_estado,
        "estado": bloque_de_estado(estado, decision),
        "avisos": list(contexto.avisos),
    }


def _estado_pedido(crudo: Any) -> EstadoParte:
    """A dónde se quiere mover el parte. **Uno de los dos manuales** (R10).

    Se rechaza lo desconocido en vez de interpretarlo, que es la misma regla
    que ya escribió `CuerpoDeArchivoInvalido`: un estado que no se entiende
    tratado «como si fuera rechazado» dejaría un parte fuera de la tanda sin
    que nadie lo hubiera decidido, y tratado al revés lo metería en el circuito
    que cierra una reclamación en el ERP de producción.

    Y se compara contra el literal exacto, sin arreglar mayúsculas: los cuatro
    nombres son un vocabulario cerrado que publica el dominio y que el front
    copia tal cual. Aceptar variantes aquí sería inventarse un quinto.
    """
    valor = crudo.strip() if isinstance(crudo, str) else ""
    for estado in ESTADOS_MANUALES:
        if valor == estado.value:
            return estado

    admitidos = ", ".join(estado.value for estado in ESTADOS_MANUALES)
    raise CambioDeEstadoInvalido(
        f"el cuerpo no trae un 'estado' que se pueda pedir a mano: los dos "
        f"posibles son {admitidos}. A «pendiente» no se vuelve a mano, y a "
        f"«cerrado» solo se llega cerrando la incidencia en el ERP"
    )


def _usuario_oid(crudo: Any) -> str:
    """Quién decide. Obligatorio, y el `oid` opaco (R14, R15).

    Sin él **no se registra nada**: lo que esta feature guarda es justamente
    que una persona concreta se hizo responsable de que este parte entre —o
    deje de entrar— en el circuito que cierra la incidencia. Una decisión
    anónima no es una decisión, es un permiso.
    """
    valor = crudo.strip() if isinstance(crudo, str) else ""
    if not valor:
        raise CambioDeEstadoInvalido(
            "el cuerpo no trae 'usuario_oid': sin saber quién decide no se "
            "puede registrar la decisión, y cambiar el estado de un parte es "
            "hacerse responsable de que entre o no en el circuito que cierra "
            "la incidencia"
        )
    return valor


def _exigir_confirmacion(crudo: Any) -> None:
    """Decidir es un **acto explícito** (R29): el booleano de JSON, no otra cosa.

    Se exige `true` de verdad y no un valor «que parezca verdadero»: la cadena
    `"true"` o un `1` son un cliente que serializa mal, y tratarlos como
    confirmación convierte un fallo de programación en un parte rechazado a
    nombre de una persona que no lo rechazó — y ese parte deja de archivarse y
    de cerrar su incidencia sin que nadie se entere.

    No hay segunda pantalla de confirmación (R29): el botón **es** el acto, y
    la confirmación única de F-025 sigue siendo la del cierre y solo la del
    cierre.
    """
    if crudo is not True:
        raise CambioDeEstadoInvalido(
            "el cuerpo no trae 'confirmado': true — cambiar el estado de un "
            "parte es un acto explícito, y se confirma con el booleano de JSON"
        )


def _motivo(crudo: Any, estado: EstadoParte) -> str | None:
    """Por qué. **Obligatorio al rechazar** (R11) y opcional al aprobar (R12).

    La asimetría tiene motivo operativo: al parte rechazado hay que volver, y
    quien vuelva —que puede ser otra persona, o la misma dentro de un mes—
    necesita saber qué había que arreglar. «Rechazado» a secas obliga a mirar
    otra vez el papel entero. Aprobar, en cambio, no deja nada pendiente.

    Se recorta por los extremos y se acota a `LIMITE_MOTIVO` (R13), que es un
    número del dominio y no de aquí: el borde lo aplica, pero quien compone la
    fila tiene que poder leerlo también. Pasarse **se rechaza** en vez de
    recortarse en silencio, que guardaría media frase y haría creer a quien la
    escribió que se guardó entera.

    Es texto de **quien revisa**, no del papel (R13): ni el DNI, ni las
    observaciones manuscritas, ni la descripción. Eso no se puede comprobar
    aquí —es texto libre—, y por eso el motivo no sale ni en la respuesta ni en
    el log (R42, R52, R53): si alguien escribe ahí el nombre de un cliente, se
    queda en la base.
    """
    valor = crudo.strip() if isinstance(crudo, str) else ""
    if not valor:
        if estado is EstadoParte.RECHAZADO:
            raise CambioDeEstadoInvalido(
                "el cuerpo no trae 'motivo': rechazar un parte sin decir por "
                "qué deja a quien vuelva a mirarlo sin saber qué hay que "
                "arreglar"
            )
        return None
    if len(valor) > LIMITE_MOTIVO:
        raise CambioDeEstadoInvalido(
            f"el 'motivo' no puede pasar de {LIMITE_MOTIVO} caracteres: es "
            f"para explicar la decisión, no para copiar ahí el parte"
        )
    return valor


def _exigir_que_no_este_cerrado(
    repositorio: RepositorioPartesPort, hash_parte: str
) -> None:
    """`cerrado` es **terminal**: de ahí no sale ninguna flecha (R7).

    Lo escrito en Sigrid y en SharePoint no se deshace desde aquí, y cambiar el
    estado solo conseguiría que nuestra base dijera algo distinto del ERP: la
    incidencia seguiría cerrada y el parte figuraría como rechazado.

    Se pregunta **a la traza de cierre** y a ningún otro sitio (R18), que es de
    donde sale ese estado, y se pregunta **antes de escribir nada**: es lo que
    hace honesto el 409. Si esto fuera después de `paso_persistencia`, un parte
    cerrado dejaría su ficha, su veredicto y quizá una fila de constancia
    escritos antes de que le dijéramos que no.

    En la pantalla no llega a levantarse casi nunca, porque la web ya no ofrece
    ningún gesto sobre un parte cerrado y lo **explica** en vez de fallar (R41).
    Esto es la puerta de atrás: quien llame al endpoint directamente se lleva
    el 409.
    """
    if repositorio.consultar_estado_cierre(hash_parte=hash_parte) in (
        ESTADOS_DE_CIERRE_EN_FIRME
    ):
        raise ParteCerrado(
            "este parte está cerrado: su incidencia ya consta cerrada en el "
            "ERP y «cerrado» es terminal, así que su estado no se puede "
            "cambiar desde aquí"
        )
