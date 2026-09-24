# services/postventa-api/application/pipelines/paso_archivo.py
"""Paso 6 del pipeline: archivar el parte en su sitio (F-006).

Habla con **puertos**, jamás con adaptadores: este módulo no sabe que debajo
hay SharePoint ni que hay PostgreSQL, y por eso se prueba entero con dobles en
memoria, sin red y sin subir nada. Es lo mismo que hace `paso_extraccion` con
`ExtractorPort` y `paso_persistencia` con `RepositorioPartesPort`.

`ahora` entra por parámetro y no se lee del reloj aquí, por lo mismo que en
F-005: un paso que consulta la hora no se puede probar dos veces con el mismo
resultado, y la traza que produce lleva fecha.

`paso_archivo` **no construye adaptadores**: la composición vive en el punto de
entrada (`docs/CONVENTIONS.md`). Aquí no se puede ni intentar subir desde
local, porque aquí no hay nada que sepa cómo hacerlo.

## Las tres capas de idempotencia, y qué tapa cada una

Reprocesar una remesa es lo normal, no la excepción: alguien corrige un campo
en el front y vuelve a lanzar. El `acceptance` de F-006 dice que eso no puede
producir un duplicado, y hacen falta tres capas porque cada una ve una cosa
que las otras no:

| Capa | Qué evita | Cómo |
|---|---|---|
| **L1 · traza** | Volver a subir el mismo parte | La traza en estado `archivado` corta **antes de llamar a nadie**: ni token, ni red, ni bytes. Desde F-033 sale **del almacén** —de la situación que ya leyó la puerta— y nunca del llamante |
| **L2 · reemplazo** | El `fichero (1).pdf` | La subida reemplaza siempre el homónimo; el puerto no ofrece otra opción |
| **L3 · carpeta** | Dos carpetas para la misma obra | `asegurar_carpeta` trata «ya existe» como éxito |

## Y la garantía de orden de F-019, que no es idempotencia sino precedencia

Antes de tocar el puerto de archivo se escribe la traza en estado
`pendiente`. Como `postventa.archivos.hash_parte` referencia a
`postventa.partes`, esa escritura **sólo puede hacerse si el parte ya consta
guardado**: es la misma restricción que el 2026-08-25 hizo fallar el proceso
*después* de subir el fichero, puesta a fallar *antes*. Ver
`_dejar_constancia_previa`.

«El mismo parte» es **el `hash` del parte troceado** que produce F-002 y que
F-005 usa como clave primaria de la tabla `archivos`. F-006 no define ningún
criterio propio: ni por nombre, ni por incidencia, ni por bytes. Dos criterios
del mismo concepto divergen siempre.

## Enmienda del 2026-09-18 (F-033) · de dónde sale la traza de L1

Hasta hoy la tabla de arriba decía «la traza en estado `archivado` corta», y
era verdad **solo en los tests**: el paso la recibía por un parámetro opcional,
`traza_previa`, y `POST /api/archivar` no se la pasaba nunca. L1 estaba inerte
desde el borde y cada re-archivo volvía a subir el PDF; lo tapaba L2 mientras
el nombre y la carpeta no cambiaran.

Desde F-033:

- la traza viaja **dentro de la situación** (`SituacionParte.archivo`), en la
  misma consulta que ya hace la puerta de estado: L1 no cuesta ninguna
  sentencia más (R3, R8);
- `traza_previa` **desaparece** de la firma (R7, D-2): dos fuentes para la
  misma decisión divergen, y la del parámetro es la que dejó L1 inerte;
- L1 corta por `hash` + estado **y por nada más** (R13, D-1). Si la traza
  apunta a otro destino —otro nombre, otra carpeta u otra biblioteca que la
  vigente—, se corta igual y se avisa (`AVISO_ARCHIVADO_EN_OTRO_DESTINO`): lo
  archivado se queda donde está (R16);
- la base ya no pisa una traza `archivado` (R17), así que una carrera entre
  dos peticiones del mismo parte se ve como `SIN_CAMBIOS` en la traza previa,
  y entonces **no se sube** (R18, D-7);
- no hay ninguna forma de forzar el re-archivo del mismo parte desde el
  circuito (R21, D-4). Un escaneo nuevo es otro `hash`, y otro parte.

## Enmienda del 2026-09-22 (F-031) · de dónde salen el nombre y la carpeta

Hasta hoy este paso nombraba el fichero con `_campo(ctx, "codigo_obra")` y
`_campo(ctx, "numero_incidencia")`, es decir, con lo que trajera **el cuerpo
de la petición** metido en una `ExtraccionParte` de pega por el borde. Desde
F-030 la puerta de aptitud, en cambio, aprobaba los códigos **guardados**, que
entran en la huella del veredicto.

Esa asimetría es lo que cierra F-031: la puerta aprobaba **unos** valores y el
fichero se nombraba con **otros**. Coincidían porque el front mandaba lo que
había leído, y eso no es una garantía, es una costumbre — la misma frase que
F-030 escribió sobre el veredicto.

Qué cambia, y qué no:

- el nombre y la carpeta salen de `ctx.situacion.validacion`, o sea de la
  consulta de situación que la puerta ya hacía: **ni una sentencia más**, ni
  una columna, ni un método nuevo del puerto (R1, R2, R17; decisión D-1);
- los dos códigos del cuerpo llegan **explícitos**, en `codigos_declarados`, y
  dejan de nombrar para pasar a **cotejar** (R10, D-2). Si no cuadran con lo
  guardado, sale `CodigosNoCoinciden` en el punto **1 bis** —antes de la traza
  previa y antes de tocar el puerto— y no se archiva nada (R3, R5, D-3);
- el cotejo normaliza los dos lados con el criterio de F-032, así que
  `RS 26.09/0178` y `RS26.09/0178` **no** son un conflicto (R4, D-7);
- `_campo` **desaparece**: era el único consumidor de `ctx.extraccion` aquí, y
  dejarlo sería dejar viva la segunda fuente que la feature viene a cerrar. Es
  la misma decisión que F-033 tomó con `traza_previa` (su D-2);
- las cuatro reglas del nombrado, las tres capas de idempotencia y la garantía
  de orden de F-019 **no se mueven** (R12, R14, R15): cambia de dónde salen
  las entradas, no qué se hace con ellas.

## Enmienda del 2026-09-23 (F-034) · dónde vive el cotejo

`CodigosDelParte` y los dos privados de F-031 —`_codigos_guardados` y
`_exigir_codigos_declarados`— se mueven a `codigos_del_parte.py`, porque desde
F-034 los aplican también el gráfico y el cierre, y dos copias de una regla
divergen (decisión D-2, aprobada por el humano el 2026-09-22). **Ninguna regla
de este paso cambia** (F-034 R26): mismo orden, mismo criterio normalizado y el
mismo mensaje byte a byte, que aquí se completa con `_Y_POR_ESO_NO_SE_ARCHIVA`.
`CodigosDelParte` se sigue exportando desde este módulo, porque es el tipo de
su parámetro `codigos_declarados`.

## Enmienda del 2026-09-24 (F-013) · la biblioteca de Posventa

Con `SHAREPOINT_ESTRUCTURA=posventa` la carpeta ya no se **compone**: se
**resuelve** contra Sigrid y contra las carpetas que Posventa tiene
(`application/pipelines/destino_archivo.py`). El paso gana un único parámetro,
`resolver_destino`, y sin él hace **exactamente** lo de antes (R2).

- El resolutor entra **entre L1 y el aviso del intento anterior** (R22): un
  parte no aprobado, uno cuyo cuerpo no cuadra y uno que ya consta archivado
  —los 133 de IT, por ejemplo— no provocan ni la lectura de Sigrid ni un
  listado (R45). Y va antes de la traza previa: un destino no resuelto no deja
  un `pendiente` colgado, sino una traza `error` con el **código** del motivo
  (R18).
- Recibe los códigos **guardados** como dos cadenas y el nombre ya compuesto;
  nunca el contexto (`design.md` §5 enmendado).
- L1 decide «otro destino» **sin carpeta** (R45): la de hoy no se conoce sin
  resolver, así que se compara la traza con su propia carpeta y deciden el
  nombre y la biblioteca. La firma de `_en_otro_destino` no cambia.
- Las carpetas que falten las crea **este paso**, después de la traza previa,
  en orden y un nivel por llamada, con el **mismo** archivador —que en
  `posventa` implementa también `ExploradorBibliotecaPort`— y **nunca** con
  `asegurar_carpeta` (R15). Cada una deja un aviso y una línea de log (R40).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from domain.models.destino_posventa import unir_ruta
from domain.models.errores import (
    ArchivoFallido,
    ArchivoSinTraza,
    DestinoNoResuelto,
    ErrorDePersistencia,
    PersistenciaNoDisponible,
)
from domain.models.nombrado import DestinoArchivo, componer_destino, nombre_de_archivo
from domain.models.persistencia import EstadoArchivo, ResultadoGuardado, TrazaArchivo
from domain.ports.archivo import ArchivoPort, ItemArchivado
from domain.ports.biblioteca import ExploradorBibliotecaPort
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.codigos_del_parte import (
    CodigosDelParte,
    codigos_guardados,
    exigir_codigos_declarados,
)
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.destino_archivo import DestinoResuelto
from application.pipelines.puerta_de_estado import (
    exigir_parte_aprobado,
    situacion_leida,
)

__all__ = [
    "AVISO_ARCHIVADO_EN_OTRO_DESTINO",
    "AVISO_CARPETA_CREADA",
    "AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA",
    "AVISO_REEMPLAZADO",
    "AVISO_YA_ARCHIVADO",
    "MIME_PDF",
    "CodigosDelParte",
    "paso_archivo",
]

log = logging.getLogger(__name__)


#: F-031 R3 · la cola del 409 de códigos que no coinciden, **tal cual la
#: escribió F-031**: desde F-034 el cotejo vive en `codigos_del_parte.py`, que
#: pone la parte fija («<cuál> de la petición («…») no es el que consta
#: guardado para este parte («…»), así que ») y esto la completa. El mensaje
#: resultante es byte a byte el de antes (F-034 R26), y lo vigila
#: `tests/test_f034_codigos_en_el_erp.py`.
_Y_POR_ESO_NO_SE_ARCHIVA = (
    "**no se ha archivado nada**: el nombre y la carpeta salen de lo "
    "guardado. Hay que guardar la corrección con POST /api/parte y volver a "
    "archivar"
)

#: Lo que se sube siempre: el PDF del parte troceado.
MIME_PDF = "application/pdf"

#: El parte ya constaba archivado y no se ha vuelto a subir (R14).
AVISO_YA_ARCHIVADO = (
    "este parte ya estaba archivado: se devuelve el destino que ya tenía y no "
    "se ha vuelto a subir"
)

#: Había un fichero con ese nombre y se ha pisado (R16).
#:
#: Aparece **solo** cuando de verdad había uno: un aviso que sale siempre es
#: un aviso que nadie lee, y este tiene que llamar la atención de quien revise
#: el archivo, porque significa que hubo una versión anterior del parte
#: conformado y ya no está.
AVISO_REEMPLAZADO = (
    "en la carpeta ya había un fichero con este nombre y se ha reemplazado por "
    "esta versión: si eran dos escaneos distintos, el anterior ya no está"
)

#: F-033 R14 · L1 ha cortado y la traza guardada **no** es el destino de hoy.
#:
#: Va **además** de `AVISO_YA_ARCHIVADO`, nunca en su lugar. Sin él, quien lee
#: la respuesta vería una carpeta y un nombre distintos de los que acaba de
#: pedir y no sabría si el fichero está en los dos sitios. No lleva ningún
#: identificador de biblioteca (R15, R24).
AVISO_ARCHIVADO_EN_OTRO_DESTINO = (
    "este parte se archivó en otra ruta o en otra biblioteca y sigue allí: no "
    "se ha vuelto a subir al destino actual, y la carpeta y el nombre que "
    "devuelve esta respuesta son los de entonces"
)

#: F-033 R20 · la traza guardada estaba en `pendiente` con **otra** ruta.
#:
#: `pendiente` puede ser un fichero **subido sin traza final**
#: (`ArchivoSinTraza`), y la traza previa que se va a escribir ahora la pisa:
#: este aviso, y la línea de log que lo acompaña, son el rastro que queda.
#: Lleva carpeta y nombre, que son códigos de obra e incidencia y no datos del
#: papel; ningún identificador de biblioteca.
AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA = (
    "hubo un intento anterior de archivar este parte en «{carpeta}/{nombre}» "
    "que no llegó a confirmarse: si aquel fichero llegó a subirse, sigue allí "
    "y conviene revisarlo"
)

#: F-013 R40 · el sistema ha creado una carpeta en la biblioteca de Posventa.
#:
#: Una línea **por carpeta**, con su ruta: quien archiva tiene que ver que ha
#: aparecido algo nuevo en la biblioteca de otro departamento, y si el nombre no
#: les sirve se deshace a mano (R43). La ruta son nombres de carpeta, que son de
#: negocio (R23); ningún identificador de biblioteca.
AVISO_CARPETA_CREADA = (
    "se ha creado la carpeta «{ruta}» en la biblioteca de Posventa: no había "
    "ninguna para este parte ni ninguna parecida"
)

#: F-013 · lo que el borde pasa como `resolver_destino`: el resolutor de
#: `destino_archivo.py` con todo fijado menos los códigos y el nombre
#: (`functools.partial`, `design.md` §5 enmendado).
ResolverDestino = Callable[..., DestinoResuelto]


def paso_archivo(
    ctx: ContextoParte,
    archivador: ArchivoPort,
    repositorio: RepositorioPartesPort,
    *,
    carpeta_base: str,
    ahora: datetime,
    drive_id_vigente: str | None = None,
    codigos_declarados: CodigosDelParte | None = None,
    resolver_destino: ResolverDestino | None = None,
) -> ContextoParte:
    """Archiva el parte y deja constancia de lo que pasó.

    Los pasos, **en este orden**, y el orden es la mitad del requisito:

    1. **Puerta de aptitud** (R17, R18; F-026 R23). Antes de nombrar y antes
       de tocar el puerto: un parte que no es apto **ni consta aprobado** no
       crea ni la carpeta.
    1 bis. **Cotejo de los códigos declarados** (F-031 R3, R5). Va aquí y no
       más abajo, y eso es un requisito: a partir del paso 4 ya hay una fila
       escrita en `postventa.archivos`, y a partir del 5 ya se ha hablado con
       SharePoint.
    2. **Nombrado** (R1–R9), desde los códigos **guardados** (F-031 R1).
       `NombradoImposible` sale sin haber tocado nada. Con `resolver_destino`,
       solo el nombre: la carpeta aún no se conoce (F-013 R5).
    3. **Idempotencia por traza** (R14). La capa barata. Desde F-033 la traza
       sale de la situación que leyó la puerta en el paso 1
       (`ctx.situacion.archivo`), sin ninguna consulta más; si apunta a otro
       destino, se corta igual y se avisa (F-033 R13–R15). Si estaba en
       `pendiente` con **otra** ruta, no corta, pero deja aviso y log antes
       de pisarla (F-033 R20).
    3 bis. **Resolver el destino** (F-013), solo con `resolver_destino`. Aquí
       y no antes, para que lo ya archivado no lea Sigrid ni liste nada (F-013
       R45); y no después, para que el aviso de F-033 R20 compare con la
       carpeta resuelta y un destino no resuelto no deje `pendiente` (F-013
       R22). `DestinoNoResuelto` deja la traza `error` con su código (R18) y
       se relanza.
    4. **Traza previa en `pendiente`** (F-019, R19). La garantía de orden: si
       el parte no consta guardado, la clave ajena la rechaza y el archivado
       se aborta **sin haber llamado a nadie**. Si vuelve `SIN_CAMBIOS`, otra
       petición lo archivó por medio: se relee una vez y **no se sube**
       (F-033 R18).
    5. `asegurar_carpeta` (R11, R12); con `resolver_destino`, en su lugar,
       `crear_subcarpeta` por cada carpeta que falta, en orden (F-013 R15).
    6. `buscar` el homónimo, para poder avisar del reemplazo (R16).
    7. `subir`, reemplazando (R15).
    8. **Traza final** (R23, R24), que se persiste tanto si fue bien como si
       no. Un `SIN_CAMBIOS` aquí se registra y no es fallo (F-033 R19).

    `drive_id_vigente` es la biblioteca de la configuración y sirve **solo**
    para decir si la traza guardada está en otra (F-033 R14, R15). Es opcional
    para que los casos que no hablan de bibliotecas no tengan que inventarse
    una; el borde lo pasa siempre. No aparece en ningún log ni aviso.

    `codigos_declarados` es **lo que afirma quien llama**, y sirve solo para
    el cotejo de F-031 R3: no decide nada, no puede mover el destino y no
    entra en el nombrado (R11). Es opcional para que los casos que no hablan
    de cuerpos no tengan que inventarse uno; el borde lo pasa siempre. Cuando
    es `None` no hay nada que cotejar y el nombrado usa lo guardado igual, que
    es la mitad silenciosa del requisito: **el camino sin cotejo tampoco puede
    archivar con otros códigos**.

    No hay ningún parámetro para forzar el re-archivo de un parte que ya
    consta archivado, a propósito (F-033 R21, D-4).

    `resolver_destino` es la estrategia `posventa` de F-013: el resolutor de
    `destino_archivo.py` ya configurado por el borde. Sin él, el paso hace
    **exactamente** lo de F-006 (F-013 R2). Con él, el `archivador` tiene que
    ser también `ExploradorBibliotecaPort` —el adaptador de Graph lo es, y el
    borde pasa la misma instancia a los dos lados (`design.md` §3.2)—: si no
    lo es, `TypeError` **antes de nada**, porque es un error de composición y
    no del parte. No abre ninguna puerta a re-archivar: L1 corta antes de
    llamarlo (F-013 R45).

    Levanta `ParteNoApto`, —desde F-031— `CodigosNoCoinciden`,
    `NombradoImposible`, `ArchivoFallido`,
    —desde F-019— `ReferenciaNoConsta` y `PersistenciaNoDisponible` de la
    traza previa, —si la subida salió bien y la traza final no se pudo
    escribir— `ArchivoSinTraza`, y —desde F-013— `DestinoNoResuelto` y, sin
    traducirlos, los fallos de lectura de Sigrid (R41). Los traduce a HTTP el
    borde; aquí no se sabe de códigos de estado.
    """
    if resolver_destino is not None and not isinstance(
        archivador, ExploradorBibliotecaPort
    ):
        raise TypeError(
            "con resolver_destino, el archivador tiene que saber también "
            "listar_carpetas y crear_subcarpeta (ExploradorBibliotecaPort): el "
            "borde pasa la misma instancia a los dos lados"
        )

    _exigir_admitido(ctx, repositorio)

    # F-031 · los dos códigos, resueltos **una vez** y desde lo guardado (R1).
    guardados = codigos_guardados(ctx)
    exigir_codigos_declarados(
        codigos_declarados, guardados, y_por_eso=_Y_POR_ESO_NO_SE_ARCHIVA
    )

    if resolver_destino is None:
        destino = componer_destino(
            carpeta_base=carpeta_base,
            codigo_obra=guardados.codigo_obra,
            numero_incidencia=guardados.numero_incidencia,
        )
    else:
        # F-013 R5 · el mismo nombre; la carpeta, hasta resolver, no se sabe.
        nombre = nombre_de_archivo(
            codigo_obra=guardados.codigo_obra,
            numero_incidencia=guardados.numero_incidencia,
        )

    # L1 · del almacén: la situación que ya leyó la puerta (F-033 R7, R8).
    guardada = situacion_leida(ctx, repositorio).archivo
    if _ya_archivado(ctx, guardada):
        if resolver_destino is not None:
            destino = _sin_resolver(guardada, nombre)
        return _devolver_la_guardada(ctx, guardada, destino, drive_id_vigente)

    carpetas_por_crear: tuple[tuple[str, str], ...] | None = None
    if resolver_destino is not None:
        resuelto = _resolver(
            ctx, repositorio, guardada, resolver_destino,
            codigo_obra=guardados.codigo_obra,
            numero_incidencia=guardados.numero_incidencia,
            nombre_fichero=nombre,
        )
        destino = resuelto.destino
        carpetas_por_crear = resuelto.carpetas_por_crear

    _avisar_del_intento_anterior(ctx, guardada, destino)

    previa = _dejar_constancia_previa(repositorio, ctx, destino)
    if previa is ResultadoGuardado.SIN_CAMBIOS:
        return _tomar_la_de_la_otra_peticion(
            ctx, repositorio, destino, drive_id_vigente
        )

    try:
        if carpetas_por_crear is None:
            archivador.asegurar_carpeta(carpeta=destino.carpeta)
        else:
            _crear_las_que_faltan(ctx, archivador, carpetas_por_crear)
        item = _subir(ctx, archivador, destino)
    except ArchivoFallido as fallo:
        ctx.archivo = _traza_de_error(ctx, destino, motivo=fallo.motivo)
        _registrar_si_no_se_aplico(
            ctx, repositorio.guardar_archivo(traza=ctx.archivo)
        )
        raise

    ctx.archivo = _traza_de_exito(ctx, item, ahora=ahora)
    _dejar_constancia(repositorio, ctx)
    return ctx


def _devolver_la_guardada(
    ctx: ContextoParte,
    guardada: TrazaArchivo,
    destino: DestinoArchivo,
    drive_id_vigente: str | None,
) -> ContextoParte:
    """El corte de L1: la traza guardada **tal cual**, y sus avisos (F-033 R10, R14).

    No se rehace ni se completa nada: la carpeta, el nombre y el `web_url` que
    devuelve la respuesta son los de la traza, porque es donde **está** el
    fichero. Si no coinciden con el destino de hoy, el segundo aviso lo dice.
    """
    ctx.avisos.append(AVISO_YA_ARCHIVADO)
    if _en_otro_destino(guardada, destino, drive_id_vigente):
        ctx.avisos.append(AVISO_ARCHIVADO_EN_OTRO_DESTINO)
    ctx.archivo = guardada
    return ctx


def _en_otro_destino(
    traza: TrazaArchivo, destino: DestinoArchivo, drive_id_vigente: str | None
) -> bool:
    """¿La traza guardada apunta a otro sitio que el destino de hoy? (F-033 R14, R15).

    Otro nombre (F-032), otra carpeta, u otra biblioteca que la vigente
    (F-013). La biblioteca solo se compara **cuando se conocen las dos**: sin
    `drive_id` en la configuración o en la traza no se puede afirmar nada, y
    se omite (R15). Un nombre o una carpeta a `None` en la traza **sí** cuenta
    como distinto: no se puede afirmar que sea la misma ruta.

    Vive en el paso y no en el dominio: compara una traza de persistencia con
    configuración, y el dominio no sabe de bibliotecas.
    """
    return (
        traza.nombre_fichero != destino.nombre_fichero
        or traza.carpeta != destino.carpeta
        or (
            drive_id_vigente is not None
            and traza.drive_id is not None
            and traza.drive_id != drive_id_vigente
        )
    )


def _avisar_del_intento_anterior(
    ctx: ContextoParte, guardada: TrazaArchivo | None, destino: DestinoArchivo
) -> None:
    """Una traza `pendiente` de **este** parte con otra ruta: aviso y log (F-033 R20).

    Va **antes** de la traza previa, que la pisa: después ya no quedaría
    rastro de la ruta anterior. No corta (D-5): `pendiente` no distingue una
    subida huérfana de un fallo que no dejó nada, y cortar bloquearía también
    el caso común. El log lleva `hash`, carpeta y nombre, y nada de la
    biblioteca.

    Solo `pendiente`: una traza en `error` es una subida que falló, y no deja
    fichero que buscar.
    """
    if (
        guardada is None
        or guardada.hash_parte != ctx.parte.hash
        or guardada.estado is not EstadoArchivo.PENDIENTE
    ):
        return
    if (
        guardada.carpeta == destino.carpeta
        and guardada.nombre_fichero == destino.nombre_fichero
    ):
        return
    ctx.avisos.append(
        AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA.format(
            carpeta=guardada.carpeta, nombre=guardada.nombre_fichero
        )
    )
    log.warning(
        "archivar: parte=%s tenía un intento anterior sin confirmar en "
        "carpeta=%s fichero=%s; se archiva en la ruta de hoy",
        ctx.parte.hash,
        guardada.carpeta,
        guardada.nombre_fichero,
    )


def _tomar_la_de_la_otra_peticion(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    destino: DestinoArchivo,
    drive_id_vigente: str | None,
) -> ContextoParte:
    """La carrera de F-033 R18 (D-7): otra petición archivó el parte por medio.

    La traza previa volvió `SIN_CAMBIOS`, y con el `WHERE` de R17 eso solo
    pasa si la fila ya está en `archivado`. Se relee la situación **una vez**
    —la única lectura adicional de F-033, y solo en este camino— y se responde
    como L1. Se pregunta al repositorio y no a `situacion_leida`, que
    devolvería la de la puerta: la de antes de la carrera.

    Si la relectura no trae `archivado` —imposible salvo un borrado manual por
    medio—, se levanta **sin subir**: ante la duda, no se sube.
    """
    ctx.situacion = repositorio.consultar_situacion(hash_parte=ctx.parte.hash)
    guardada = ctx.situacion.archivo
    if not _ya_archivado(ctx, guardada):
        raise PersistenciaNoDisponible(
            "la traza de archivo de este parte no admitió el estado "
            "«pendiente» y, al releerla, no consta archivado: no se ha subido "
            "nada a SharePoint; conviene revisar la traza antes de reintentar"
        )
    return _devolver_la_guardada(ctx, guardada, destino, drive_id_vigente)


def _registrar_si_no_se_aplico(
    ctx: ContextoParte, resultado: ResultadoGuardado
) -> None:
    """F-033 R19 · la traza final o la de error no se aplicó: se dice, y se sigue.

    Solo es alcanzable en una carrera entre dos peticiones del mismo parte
    (`design.md` §8): la otra ya dejó la traza en `archivado` y el `WHERE` de
    R17 la protege. No es un fallo —la subida de esta petición ocurrió, o su
    error ya sube—, pero tiene que quedar en el log. Solo `hash`, estado de la
    traza que no entró y resultado: nada de la biblioteca.
    """
    if resultado is not ResultadoGuardado.SIN_CAMBIOS:
        return
    log.warning(
        "archivar: parte=%s la traza %s no se aplicó (%s): otra petición ya la "
        "había dejado en archivado",
        ctx.parte.hash,
        ctx.archivo.estado.value,
        resultado.value,
    )


def _dejar_constancia_previa(
    repositorio: RepositorioPartesPort, ctx: ContextoParte, destino: DestinoArchivo
) -> ResultadoGuardado:
    """Escribe la traza en `pendiente` **antes de tocar el puerto** (F-019, R19).

    Es la garantía de orden de F-019, y **el orden es el requisito**: no se
    sube un byte a SharePoint de un parte que no conste guardado.

    Cómo funciona, y por qué así: `postventa.archivos.hash_parte` tiene una
    clave ajena contra `postventa.partes`. Si el parte no consta, esta
    escritura **no puede hacerse**, el error sube y el archivado se aborta sin
    haber llamado a nadie —ni carpeta, ni búsqueda, ni subida—. Es decir: la
    misma restricción que hasta el 2026-08-25 hacía fallar el proceso
    **después** de subir el fichero pasa a hacerlo fallar **antes**.

    No se añade una comprobación paralela (`consta_parte`) que pueda divergir
    de la restricción real: se usa la restricción. Entre una consulta previa y
    la escritura cabe todo —otro proceso borrando el parte por medio—, y
    además habría que tocar `RepositorioPartesPort`, que es de F-005.

    Va **después** de la idempotencia de F-006 a propósito: escribirla con el
    parte ya archivado lo degradaría a `pendiente`, y `pendiente` no corta el
    reintento (R14), así que el siguiente intento volvería a subir el fichero.

    Los errores suben **sin traducir**: el borde distingue `ReferenciaNoConsta`
    (→ 409 «guarda el parte primero») de `PersistenciaNoDisponible` (→ 503
    «no se ha subido nada, se puede reintentar»), y esas dos respuestas llevan
    a acciones opuestas. Aquí no se sabe de códigos de estado.

    Desde F-033 devuelve lo que contestó el repositorio: un `SIN_CAMBIOS` es
    la carrera de R18, y quien llama no sube.
    """
    ctx.archivo = TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.PENDIENTE,
        nombre_fichero=destino.nombre_fichero,
        carpeta=destino.carpeta,
    )
    return repositorio.guardar_archivo(traza=ctx.archivo)


def _dejar_constancia(repositorio: RepositorioPartesPort, ctx: ContextoParte) -> None:
    """Guarda la traza del parte **ya subido**, o dice que se quedó sin ella.

    Aquí arriba la subida ya ocurrió, y eso es lo que hace falta contar. Dejar
    salir el error de la persistencia tal cual —que es lo que pasaba hasta el
    defecto 14 de F-010— produce el mismo `PersistenciaNoDisponible` que sale
    cuando la base no responde y **no se ha subido nada**, y las dos lecturas
    llevan a acciones opuestas: reintentar, o ir a mirar la carpeta.

    Por eso se renombra a `ArchivoSinTraza`: no se traga el fallo —el llamante
    se entera y el motivo viaja entero— pero sí dice **en qué punto** ocurrió,
    que es lo único que el borde no puede deducir.

    El bloque `except ArchivoFallido` de arriba NO hace esto a propósito: allí
    la subida falló, así que su `PersistenciaNoDisponible` sí significa «no hay
    nada arriba» y el borde lo traduce como tal.
    """
    try:
        resultado = repositorio.guardar_archivo(traza=ctx.archivo)
    except ErrorDePersistencia as sin_traza:
        raise ArchivoSinTraza(sin_traza.motivo) from sin_traza
    _registrar_si_no_se_aplico(ctx, resultado)


def _exigir_admitido(ctx: ContextoParte, repositorio: RepositorioPartesPort) -> None:
    """Solo se archiva el parte que está **`aprobado`** (F-028 R33).

    Hasta F-026 esta puerta miraba el veredicto y, si no bastaba, una
    aprobación suelta. Desde F-028 mira **el estado del parte**, que es lo que
    combina los tres hechos —el veredicto, la última decisión de una persona y
    la traza de cierre— con un criterio escrito una sola vez
    (`domain/models/estado.py`).

    Lo que eso cambia aquí, y es medio encargo de la feature: **desaparece el
    atajo del apto**. Hasta ahora el parte verde pasaba sin consultar nada, y
    mientras eso fuera así un parte apto rechazado por una persona se habría
    archivado igual (`design.md` §0.5 y §6). El coste —una consulta por parte
    y paso— está declarado y aceptado.

    Lo demás no se mueve: «no hay veredicto» sigue siendo un motivo propio y
    va primero, y la situación **se lee del repositorio y nunca del cuerpo**
    (R33). La explicación larga está en `puerta_de_estado.py`.
    """
    exigir_parte_aprobado(
        ctx,
        repositorio,
        sin_veredicto=(
            "no consta que este parte haya pasado la validación: no se "
            "archiva un parte del que nadie ha emitido veredicto"
        ),
        y_por_eso="no se archiva",
    )


def _ya_archivado(ctx: ContextoParte, traza: TrazaArchivo | None) -> bool:
    """¿Consta ya archivado **este** parte? (R13, R14).

    Las dos condiciones hacen falta: que la traza sea de este `hash` —la de
    otro parte no dice nada de este— y que su estado sea `archivado`.
    `pendiente` y `error` **no** cortan: es lo que hace posible reintentar
    después de un fallo sin que el parte quede atascado para siempre.
    """
    return (
        traza is not None
        and traza.hash_parte == ctx.parte.hash
        and traza.estado == EstadoArchivo.ARCHIVADO
    )


def _sin_resolver(guardada: TrazaArchivo, nombre: str) -> DestinoArchivo:
    """F-013 R45 · el destino con el que L1 compara en `posventa`, sin resolver.

    La carpeta de hoy no se conoce sin leer Sigrid y listar la biblioteca, que
    es justo lo que L1 evita. Se toma **la de la propia traza**: así la carpeta
    no puede discrepar, y `_en_otro_destino` —cuya firma fijan los tests de
    F-033— decide con el nombre y la biblioteca. Consecuencia aceptada en R45:
    un parte archivado en Posventa cuya carpeta se renombró después no recibe
    el aviso de «otro destino».
    """
    return DestinoArchivo(carpeta=guardada.carpeta, nombre_fichero=nombre)


def _resolver(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    guardada: TrazaArchivo | None,
    resolver_destino: ResolverDestino,
    *,
    codigo_obra: str,
    numero_incidencia: str,
    nombre_fichero: str,
) -> DestinoResuelto:
    """F-013 · la carpeta de Posventa; si no se resuelve, traza `error` y se relanza.

    Recibe los códigos **guardados** como dos cadenas, nunca el contexto
    (`design.md` §5 enmendado): el resolutor no puede leer lo que no le llega.

    `DestinoNoResuelto` (R18): antes de nada, el rastro de R47 si la traza
    guardada de este parte estaba en `pendiente`; luego la traza `error` con el
    **código** del motivo —sin el texto, que es para una persona, y sin
    carpeta, que no se ha resuelto—; y se relanza para que el borde responda
    409. Si esa traza no se aplica (una carrera, F-033 R19), se dice en el log
    y se relanza igual.

    Lo demás —Sigrid caída (R41), la biblioteca que no responde— sube **tal
    cual y sin traza**: todavía no se ha escrito ninguna, y una `error` con un
    motivo inventado diría menos que el 503 o el 502 del borde.
    """
    try:
        return resolver_destino(
            codigo_obra=codigo_obra,
            numero_incidencia=numero_incidencia,
            nombre_fichero=nombre_fichero,
        )
    except DestinoNoResuelto as sin_destino:
        motivo = str(sin_destino.motivo)
        _dejar_rastro_del_intento_pendiente(ctx, guardada, motivo)
        ctx.archivo = TrazaArchivo(
            hash_parte=ctx.parte.hash,
            estado=EstadoArchivo.ERROR,
            nombre_fichero=nombre_fichero,
            carpeta=None,
            motivo=motivo,
        )
        _registrar_si_no_se_aplico(
            ctx, repositorio.guardar_archivo(traza=ctx.archivo)
        )
        raise


def _dejar_rastro_del_intento_pendiente(
    ctx: ContextoParte, guardada: TrazaArchivo | None, motivo: str
) -> None:
    """F-013 R47 · un `pendiente` de este parte, al log antes de que lo pise `error`.

    Es lo mismo que F-033 R20 hace antes de la traza previa: `pendiente` puede
    ser un fichero **subido sin traza final**, y la traza `error` que se va a
    escribir borra su único rastro. Carpeta y nombre de aquel intento, el
    `hash` y el código del motivo; nada de la biblioteca.
    """
    if (
        guardada is None
        or guardada.hash_parte != ctx.parte.hash
        or guardada.estado is not EstadoArchivo.PENDIENTE
    ):
        return
    log.warning(
        "archivar: parte=%s el destino no se resuelve (%s) y tenía un intento "
        "anterior sin confirmar en carpeta=%s fichero=%s; la traza error lo pisa",
        ctx.parte.hash,
        motivo,
        guardada.carpeta,
        guardada.nombre_fichero,
    )


def _crear_las_que_faltan(
    ctx: ContextoParte,
    explorador: ExploradorBibliotecaPort,
    carpetas_por_crear: tuple[tuple[str, str], ...],
) -> None:
    """F-013 R15, R40 · las carpetas de la resolución, una a una y en orden.

    Cada `(padre, nombre)` es un nivel dentro de un padre que ya existe o que
    se acaba de crear en la vuelta anterior: `crear_subcarpeta` no crea
    intermedias, así que el orden es el requisito. Se llega aquí solo tras una
    resolución **completa** y después de la traza previa (R22, R38): ningún
    409 deja una carpeta a medias, y no se crea nada de un parte que no consta
    guardado.

    Por cada una, un aviso en la respuesta y una línea de log (R40). Un fallo
    sube como `ArchivoFallido` y lo recoge el paso como cualquier otro del
    proveedor; el reintento vuelve a resolver y encuentra lo ya creado (R39).
    """
    for padre, nombre in carpetas_por_crear:
        explorador.crear_subcarpeta(padre=padre, nombre=nombre)
        ruta = unir_ruta(padre, nombre)
        ctx.avisos.append(AVISO_CARPETA_CREADA.format(ruta=ruta))
        log.warning("F-013 carpeta creada: %s", ruta)


def _subir(ctx: ContextoParte, archivador: ArchivoPort, destino) -> ItemArchivado:
    """Homónimo y subida, en ese orden.

    La carpeta la prepara quien llama —`asegurar_carpeta` en `por_obra`, las
    creaciones de F-013 en `posventa`— y **antes**: hasta F-013 vivía aquí.
    """
    if (
        archivador.buscar(
            carpeta=destino.carpeta, nombre=destino.nombre_fichero
        )
        is not None
    ):
        ctx.avisos.append(AVISO_REEMPLAZADO)

    return archivador.subir(
        carpeta=destino.carpeta,
        nombre=destino.nombre_fichero,
        contenido=ctx.parte.contenido,
        mime=MIME_PDF,
    )


def _traza_de_exito(
    ctx: ContextoParte, item: ItemArchivado, *, ahora: datetime
) -> TrazaArchivo:
    """La traza de R23: qué se subió, dónde y cuándo."""
    return TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=item.nombre,
        carpeta=item.carpeta,
        drive_id=item.drive_id,
        item_id=item.item_id,
        web_url=item.web_url,
        archivado_at_utc=ahora,
    )


def _traza_de_error(ctx: ContextoParte, destino, *, motivo: str) -> TrazaArchivo:
    """La traza de R24: qué se intentó y por qué no salió.

    Sin `archivado_at_utc` y en estado `error`, que es lo que deja reintentar:
    si quedara como `archivado`, R14 cortaría el reintento y el parte se
    perdería sin que nadie lo notara.

    El `motivo` viene del adaptador y **nunca** lleva los bytes del parte ni
    ningún dato del papel: esto acaba en la base y en un log.
    """
    return TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.ERROR,
        nombre_fichero=destino.nombre_fichero,
        carpeta=destino.carpeta,
        motivo=motivo,
    )
