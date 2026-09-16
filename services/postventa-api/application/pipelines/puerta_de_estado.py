# services/postventa-api/application/pipelines/puerta_de_estado.py
"""La puerta que abren los tres pasos del circuito, en un solo sitio (F-028).

`design.md` §6 la escribe en una línea: **se archiva, se adjunta y se cierra lo
que está `aprobado`**, y el estado sale de `estado_del_parte` leyendo la
situación **del repositorio** y nunca del cuerpo de la petición (R33).

## Por qué es un módulo y no una función privada en cada paso

La aplican **tres** pasos —`paso_archivo`, `paso_grafico` y `paso_cierre`— y
hasta F-026 cada uno llevaba su copia. Es el mismo caso que `confianza.py` en
F-004 y que `constancia.py` en este bloque 3, y por los dos motivos que
escribió aquella cabecera: dos copias de una regla divergen el día que alguien
la corrija en una sola, y en una campaña de mutación **cada copia se cuenta
aparte**, con lo que la segunda y la tercera se quedan sin tests que las maten.

Aquí pesa más que en ningún otro sitio del proyecto. Esto es lo único que
separa un parte que nadie ha mirado de un PDF con el DNI de un cliente subido a
SharePoint y de una reclamación cerrada en el ERP de producción. Tres copias de
esa decisión son tres sitios donde puede aflojarse, y solo uno de ellos tendría
que aflojarse para que ocurriera.

> `design.md` §8.2 no lista este fichero: lista los tres pasos. Es una
> desviación de forma —la regla es la que dice §6, letra por letra—, declarada
> en `progress/impl_F-028.md` igual que la de `constancia.py`.

## Lo que esta puerta **no** hace (R34)

No relaja ninguna otra: el parte sigue teniendo que constar guardado (F-019),
archivado antes del gráfico y del cierre (F-006, F-012), adjuntado antes del
cierre (F-012 R2), y el cierre sigue exigiendo su dry-run dentro de la misma
llamada, el login verificado contra el ERP y el estado de origen en el `WHERE`
(F-009, F-025). Cada una de esas vive donde vivía.

Y **«no hay veredicto» sigue siendo un motivo propio**, que va el primero: se
arregla revalidando el parte, no decidiendo sobre él, y una decisión no puede
rescatar un parte del que nadie ha emitido veredicto (`design.md` §3, punto 4).

## Enmienda del 2026-09-16 (F-030 T8) · de dónde sale el veredicto

Hasta hoy esta puerta leía el veredicto de **`ctx.validacion`**, es decir, del
contexto que arma quien la llama. Para `POST /api/parte` y `POST /api/estado`
eso era correcto —traen la extracción y emiten el veredicto con las reglas de
F-004 en la propia llamada—, pero los **tres pasos del circuito** no reciben la
extracción y no la van a recibir nunca: pedirla obligaría al front a reenviar
el DNI y las observaciones manuscritas del cliente en cada petición. Sus tres
endpoints fabricaban de todas formas un `ResultadoValidacion` con lo poco que
tenían —el `veredicto` y el `destino` del formulario— y valores fijos para el
resto: sin motivos, firma `humana` y sin observaciones.

Eso rompió el circuito de dos maneras a la vez:

1. la huella recomputada sobre ese objeto **no depende del parte** —es una de
   tres constantes—, así que nunca coincidía con la que apuntó la persona que
   aprobó, la aprobación no contaba y el parte volvía a `pendiente`. La
   incidencia **RS26.09/0178** lleva desde el 2026-09-16 a las 18:09:33
   aprobada por una persona y sin archivarse;
2. y al revés: un cuerpo que dijera `veredicto=apto` pasaba las tres puertas
   sin que nadie hubiera mirado el parte. Lo único que lo impedía era que el
   front mandara la verdad, y eso no es una puerta, es una costumbre.

Desde F-030 la puerta lee **`ctx.situacion.validacion`**, que viene del mismo
`consultar_situacion` que ya se hacía —sin una consulta más (R18)— y por tanto
de `postventa.validaciones`. **`ctx.validacion` no se vuelve a mirar aquí**, y
ese es el blindaje: aunque alguien vuelva a meter un veredicto en el contexto
desde el borde, esta puerta no se entera (R1, `design.md` §5.3).
"""

from __future__ import annotations

from domain.models.errores import ParteNoApto
from domain.models.estado import EstadoParte, SituacionParte, estado_del_parte
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.contexto_parte import ContextoParte

__all__ = ["exigir_parte_aprobado", "situacion_leida"]

#: Lo que se le cuenta a quien lea el error, según por qué no pasa.
#:
#: El motivo importa porque **cada estado se arregla de una forma distinta** y
#: quien lee el error es quien tiene que ir a arreglarlo: el `pendiente` se
#: resuelve mirando el parte y decidiendo, el `rechazado` solo lo deshace otra
#: persona volviendo a decidir, y el `cerrado` no se deshace de ninguna manera
#: desde aquí (R7). Un error único para los tres mandaría a alguien a intentar
#: lo que no se puede.
MOTIVOS: dict[EstadoParte, str] = {
    EstadoParte.PENDIENTE: (
        "este parte está pendiente: la validación lo manda a «{destino}» y no "
        "consta que nadie lo haya aprobado"
    ),
    EstadoParte.RECHAZADO: (
        "este parte está rechazado: una persona lo miró y decidió que no, y "
        "eso no lo deshace un reproceso"
    ),
    EstadoParte.CERRADO: (
        "este parte está cerrado: su incidencia ya consta cerrada en el ERP, y "
        "«cerrado» es terminal"
    ),
}


def exigir_parte_aprobado(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    *,
    sin_veredicto: str,
    y_por_eso: str,
) -> EstadoParte:
    """Deja pasar **solo** al parte `aprobado`, y deja dicho por qué si no.

    De los cuatro estados pasa uno (R33). Los otros tres no, y los tres por su
    motivo:

    - `pendiente`: la máquina no lo declaró apto y nadie ha decidido todavía;
    - `rechazado`: alguien lo miró y dijo que no, **aunque el veredicto sea
      apto** (R5). Este es el caso que la feature viene a hacer posible: hasta
      F-028 la puerta devolvía «pasa» en cuanto el veredicto era apto y no
      consultaba nada, así que el rechazo no tenía por dónde llegar;
    - `cerrado`: la incidencia ya está cerrada en el ERP y volver a recorrer el
      circuito solo podría escribir dos veces lo que ya está escrito (R7).

    La situación se lee **del repositorio y nunca del cuerpo** (R33), y se lee
    **siempre**, también para el parte apto: es la retirada del atajo de
    `design.md` §6, con su coste declarado —una consulta por parte y paso— y su
    porqué, que es que sin ella rechazar un parte verde no funciona.

    Desde F-030 eso vale también para **el veredicto**, que llega dentro de esa
    misma situación (R1). Por eso el orden es consulta primero y «no hay
    veredicto» después: no hay forma de saber si hay veredicto guardado sin
    preguntar, así que un parte sin validar paga la consulta antes de que le
    digan que no. Es el mismo precio que F-028 aceptó al retirar el atajo del
    apto, y lo que **no** cambia es el orden de precedencia de los motivos:
    «no hay veredicto» sigue yendo el primero y sigue siendo el suyo (R8, R17).

    Lo leído se deja en `ctx.situacion` para que nadie vuelva a preguntarlo en
    la misma pasada (`design.md` §11.1). Y se devuelve el estado derivado, que
    es lo que necesita quien quiera contarlo después.

    `sin_veredicto` y `y_por_eso` los pone cada paso porque cada uno le está
    diciendo al lector una cosa distinta —«no se archiva», «no se adjunta a la
    reclamación», «no se cierra la incidencia»—, y ese final es justo la parte
    del mensaje que le dice a quien lo lee qué se ha quedado sin hacer.
    """
    ctx.situacion = repositorio.consultar_situacion(hash_parte=ctx.parte.hash)
    validacion = ctx.situacion.validacion  # ← del almacén, nunca del cuerpo
    if validacion is None:
        raise ParteNoApto(sin_veredicto)

    estado = estado_del_parte(
        validacion, ctx.situacion.decision_humana, ctx.situacion.estado_cierre
    )
    if estado is EstadoParte.APROBADO:
        return estado

    motivo = MOTIVOS[estado].format(destino=validacion.destino.value)
    raise ParteNoApto(f"{motivo}, así que {y_por_eso}")


def situacion_leida(
    ctx: ContextoParte, repositorio: RepositorioPartesPort
) -> SituacionParte:
    """La situación que ya se leyó en la puerta, sin volver a preguntarla.

    La puerta es lo primero que hace cada uno de los tres pasos, así que cuando
    alguien necesita la situación más adelante —la constancia del cierre, R18—
    ya está leída y preguntarla otra vez sería un viaje más por parte a un
    PostgreSQL **compartido** con otros proyectos.

    El camino de la derecha existe para no depender de ese orden: si mañana
    alguien llamara a esto desde un sitio donde la puerta no hubiera pasado,
    lo que tiene que ocurrir es una consulta de más, no un reventón en el punto
    exacto en el que el ERP ya está escrito.
    """
    return ctx.situacion or repositorio.consultar_situacion(hash_parte=ctx.parte.hash)
