# services/postventa-api/application/pipelines/paso_grafico.py
"""Paso 7a del pipeline: adjuntar el parte a la reclamación como gráfico (F-012).

Va **delante** de `paso_cierre` (7b), y ese orden es la mitad de la feature: la
atomicidad entre dos llamadas HTTP no existe, así que se sustituye por **orden
más idempotencia**. Con esto, ninguna reclamación cerrada por este servicio
queda sin su parte dentro de Sigrid — la anomalía que `docs/ARCHITECTURE.md`
describía como riesgo aceptado de F-009.

Habla con **puertos**, jamás con adaptadores: este módulo no sabe que debajo
hay una pasarela HTTP ni que hay PostgreSQL, y por eso se prueba entero con
dobles en memoria, **sin red y sin escribir en el ERP de producción**. `ahora`
entra por parámetro y no se lee del reloj aquí, por lo mismo que en F-005,
F-006 y F-009.

## Lo que este paso NO supone

**No supone que si se adjuntó, se cerró** (R5). Son dos escrituras contra dos
endpoints distintos, con contratos y semánticas de idempotencia distintas, y
entre una y otra puede pasar cualquier cosa. «Adjuntado pero no cerrado» es un
estado real, se representa y se enseña.

## Las tres capas de idempotencia, en orden

1. **La traza local** por `hash` de parte (R24). Si dice `adjuntado`, se
   responde **sin llamar a nadie**: ni al ERP, ni a la pasarela, ni se vuelven
   a mandar los bytes. Cubre el reintento normal y el único caso que la
   pasarela no cubriría: el mismo parte re-troceado con bytes distintos, que
   tendría otro `sha256`.
2. **La pasarela**, por tamaño y `sha256`, comprobado dos veces —al leer y
   otra vez dentro de la transacción, bajo el bloqueo—. Cubre la traza perdida
   y la llamada repetida por un corte de red.
3. **`evaluar`** (R16): una reclamación ya cerrada no recibe un segundo
   gráfico.

## Y una cosa que no se hace, a propósito

**No se recalcula la huella de páginas** del PDF recibido para compararla con
`hash`. F-002 avisa de que esa huella se calcula sobre las páginas de origen y
de que PyMuPDF puede no conservar al reserializar lo que copia, así que la
igualdad no está garantizada por construcción y una comprobación que fallara
sola mandaría partes buenos a un 409. La integridad **del transporte** sí se
comprueba: el `sha256` se calcula aquí y lo coteja la pasarela (R7).

## Enmienda del 2026-09-23 (F-034 T6) · con qué se escribe en el ERP

Hasta hoy este paso escribía en el ERP de producción con **tres datos del
cuerpo** de la petición, que el borde le pasaba tal cual:

- el **estado del archivo**: `_exigir_archivado` miraba `ctx.archivo`, y ese
  objeto lo fabricaba `adjuntar._como_contexto` con el `estado_archivo` del
  formulario, que el front manda fijo a `archivado`. Un parte aprobado y sin
  archivar se adjuntaba con solo decirlo;
- el **número de incidencia**, que elegía **a qué reclamación** se adjunta el
  parte (`_codigo_de_incidencia` → `erp.leer_reclamacion`);
- el **código de obra** y ese mismo número, que componían **el nombre** con el
  que el parte cuelga de la reclamación (`componer_peticion`).

Desde F-034 (`specs/F-034-archivo-persistido-en-erp/`) los tres salen de **lo
guardado**, de la `SituacionParte` que la puerta de aptitud acaba de leer y sin
una consulta más: el archivo, de `ctx.situacion.archivo` con la puerta
compartida `exigir_parte_archivado`; los dos códigos, de
`codigos_guardados(ctx)`. Lo que traiga el cuerpo entra por
`codigos_declarados` y **solo coteja**, en el punto 1 bis y antes de hablar con
nadie: si no es lo guardado, 409 y no se escribe nada, tampoco en dry-run
(R11, R13, R14). Lo declarado puede cerrar la puerta, nunca abrirla ni moverla
(R19). Los dos parámetros `numero_incidencia` y `codigo_obra` desaparecen de la
firma para que el cuerpo de la función no pueda volver a usarlos (D-7).
"""

from __future__ import annotations

import logging
from datetime import datetime

from domain.models.cierre import (
    CODIGO_ESTADO_CIERRE,
    a_codigo_de_sigrid,
    evaluar,
)
from domain.models.errores import (
    CuerpoDeCierreInvalido,
    ErrorDePersistencia,
    EscrituraDocumentalDeshabilitada,
    EstadoNoCerrable,
    GraficoFallido,
    GraficoSinTraza,
    ReclamacionNoLocalizada,
)
from domain.models.grafico import (
    FILAS_ESPERADAS_GRAFICO,
    PlanDeGrafico,
    RespuestaGrafico,
    ResultadoGrafico,
    componer_peticion,
    esta_colgado,
    validar_fichero,
)
from domain.models.persistencia import (
    EstadoGrafico,
    TrazaGrafico,
)
from domain.ports.erp import ErpPort
from domain.ports.grafico import GraficoPort
from domain.ports.persistencia import (
    RepositorioPartesPort,
    RepositorioPreferenciasPort,
)
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort

from application.pipelines.codigos_del_parte import (
    CodigosDelParte,
    codigos_guardados,
    exigir_codigos_completos,
    exigir_codigos_declarados,
)
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import (
    # **Una** regla de autorización para escribir en el ERP, no dos copias que
    # un día divergen: la que se quedara corta sería la que dejara escribir sin
    # que nadie lo confirmara. Es pública desde T12, cuando `paso_cierre` se
    # tocó para exigir el gráfico.
    exigir_autorizacion_para_escribir,
    resolver_login_de_sigrid,
)
from application.pipelines.puerta_de_estado import (
    exigir_parte_aprobado,
    exigir_parte_archivado,
)

__all__ = ["paso_grafico"]

log = logging.getLogger(__name__)

#: Lo que se le dice a quien lee cada 409 de F-034, según por qué no se adjunta.
#: La parte fija del mensaje la pone la pieza compartida; esta es la cola, que
#: es lo que dice **qué se ha quedado sin hacer** y qué hacer.
#:
#: La del archivo es, byte a byte, la del `_exigir_archivado` que sustituye.
_Y_POR_ESO_SIN_ARCHIVAR = (
    "no se adjunta a la reclamación: primero el documento, después el ERP"
)
#: Lo guardado está incompleto: `exigir_codigos_completos` añade la acción
#: (teclear el código y guardarlo), que es la misma en cualquier endpoint.
_Y_POR_ESO_FALTA_UN_CODIGO = "**no se ha adjuntado nada** al ERP"
#: Lo declarado no es lo guardado: la cola lleva la acción entera, como la de
#: `paso_archivo` (decisión del humano del 2026-09-23 sobre el mensaje).
_Y_POR_ESO_NO_COINCIDEN = (
    "**no se ha adjuntado nada** al ERP: la reclamación y el nombre del "
    "fichero salen de lo guardado. Hay que guardar la corrección con "
    "POST /api/parte y volver a adjuntar"
)


def paso_grafico(
    ctx: ContextoParte,
    erp: ErpPort,
    graficos: GraficoPort,
    repositorio: RepositorioPartesPort,
    usuarios: RepositorioUsuariosSigridPort,
    preferencias: RepositorioPreferenciasPort,
    *,
    commit: bool,
    confirmado: bool,
    usuario_oid: str,
    correo: str,
    codigos_declarados: CodigosDelParte | None = None,
    gratipide: int,
    tope_bytes: int,
    ahora: datetime,
) -> ContextoParte:
    """Adjunta el parte a la reclamación y deja constancia de lo que pasó.

    Los pasos, **en este orden**, y el orden es la mitad del requisito:

    1. **Puerta de aptitud** (R14). La misma que el cierre: no se sube al ERP
       el parte de una incidencia que nadie ha validado. Deja la situación
       leída en `ctx.situacion`.

       **1 bis. Los dos códigos** (F-034 R11, R13, R15): los **guardados**
       tienen que estar completos y lo **declarado** en el cuerpo tiene que ser
       lo guardado. Va aquí y no más abajo porque a partir del login ya se
       habla con el ERP y a partir del dry-run ya hay trazas escritas; y va
       antes de la puerta de archivo porque primero se resuelve **sobre qué**
       parte y qué reclamación se opera, y después en qué estado está.

       **Puerta de archivo** (R15): el parte tiene que constar archivado
       **según lo guardado** (F-034 R1), no según el cuerpo.
    2. **El fichero** (R18, R19): tope y firma de PDF. Antes de tocar la base y
       antes de leer nada del ERP, con lo que ya se tiene en la mano.
    3. **La traza local** (R24): si dice `adjuntado`, se acabó. Cero llamadas.
    4. **El login**, resuelto y verificado contra el ERP (R12), con el
       mecanismo de F-009. Va antes del dry-run para que quien no tenga
       correspondencia se entere enseguida.
    5. **La reclamación** y **`evaluar`** (R16, R17): solo se adjunta lo que se
       va a poder cerrar.
    6. **El dry-run** (R20), que es una lectura, y su traza (R42).
    7. Y **solo si `commit`** y hay confirmación o auto-cierre (R23): la
       escritura, la comprobación de R26/R27 y la traza `adjuntado` (R43).

    Levanta sus errores **sin traducir**: convertir eso en códigos HTTP es
    trabajo del borde.

    El log lleva el `hash` del parte, el código de la incidencia, el tamaño y el
    estado. **Nunca** el contenido del PDF, ni el correo, ni el login, ni el
    `oid`, ni el `gra_cod` —que lleva el login del ERP dentro— (R53, R54).
    """
    _exigir_admitido(ctx, repositorio)
    guardados = _codigos_con_los_que_se_escribe(ctx, codigos_declarados)
    exigir_parte_archivado(ctx, y_por_eso=_Y_POR_ESO_SIN_ARCHIVAR)

    bytes_, sha256 = validar_fichero(ctx.parte.contenido, tope_bytes=tope_bytes)

    traza_previa = repositorio.consultar_grafico(hash_parte=ctx.parte.hash)
    if traza_previa is not None and traza_previa.estado == EstadoGrafico.ADJUNTADO:
        return _resolver_desde_la_traza(ctx, traza_previa)

    codigo = _codigo_de_incidencia(guardados.numero_incidencia)
    login = resolver_login_de_sigrid(
        usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
    )

    reclamacion = erp.leer_reclamacion(
        codigo=codigo, codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )
    if reclamacion is None:
        raise ReclamacionNoLocalizada(
            f"no hay ninguna reclamación con el código {codigo} en el tipo de "
            f"posventa del ERP: no se adjunta nada"
        )

    decision = evaluar(reclamacion, login_sigrid=login)
    peticion = componer_peticion(
        reclamacion=reclamacion,
        login=login,
        codigo_obra=guardados.codigo_obra,
        numero_incidencia=guardados.numero_incidencia,
        gratipide=gratipide,
        contenido=ctx.parte.contenido,
        bytes=bytes_,
        sha256=sha256,
    )

    if decision.ya_cerrada:
        return _resolver_ya_cerrada(
            ctx, repositorio, reclamacion, login, peticion, decision.motivo, ahora
        )

    if not decision.cerrable:
        plan = _plan(reclamacion, login, peticion, decision.cerrable, decision.motivo)
        _dejar_constancia(
            repositorio,
            _traza(
                ctx,
                plan,
                estado=EstadoGrafico.ERROR,
                usuario_oid=None,
                motivo=decision.motivo,
                dry_run_at_utc=ahora,
            ),
        )
        raise EstadoNoCerrable(
            decision.motivo or "la reclamación no admite cierre, así que no se "
            "le adjunta el parte"
        )

    previsto = _dry_run(ctx, graficos, repositorio, reclamacion, login, peticion, ahora)
    plan = _plan(
        reclamacion,
        login,
        peticion,
        True,
        None,
        idempotente_previsto=previsto.idempotente,
        cod_previsto=previsto.cod,
        ide_negocio_previsto=previsto.ide_negocio,
        avisos_pasarela=previsto.avisos,
    )
    _dejar_constancia(
        repositorio,
        _traza(
            ctx,
            plan,
            estado=EstadoGrafico.DRY_RUN_OK,
            usuario_oid=None,
            dry_run_at_utc=ahora,
        ),
    )

    ctx.grafico = ResultadoGrafico(
        estado=EstadoGrafico.DRY_RUN_OK, plan=plan, respuesta=previsto
    )
    if not commit:
        log.info(
            "F-012 dry-run del gráfico correcto: parte=%s incidencia=%s "
            "bytes=%d idempotente=%s",
            ctx.parte.hash,
            reclamacion.codigo,
            peticion.bytes,
            previsto.idempotente,
        )
        return ctx

    exigir_autorizacion_para_escribir(
        preferencias, confirmado=confirmado, usuario_oid=usuario_oid
    )
    return _escribir(
        ctx, graficos, repositorio, plan, usuario_oid=usuario_oid, ahora=ahora
    )


# --------------------------------------------------------------------------
# Las puertas
# --------------------------------------------------------------------------


def _exigir_admitido(ctx: ContextoParte, repositorio: RepositorioPartesPort) -> None:
    """Solo se adjunta el parte que está **`aprobado`** (R14; F-028 R33).

    Misma puerta que R16 de F-009, y aquí con el mismo peso: el gráfico es la
    primera mitad del cierre. Subir a Sigrid el parte de una incidencia que
    nadie ha validado deja en el ERP de producción un documento que no ha
    pasado por ninguna revisión — y desde F-028, «que nadie ha validado» quiere
    decir que su **estado** no es `aprobado`, lo mire quien lo mire.

    La situación se lee del repositorio y nunca del cuerpo (R33), y se lee
    **siempre**: el atajo del apto se retira aquí igual que en las otras dos
    puertas, porque una sola que lo conservara dejaría pasar al parte que otra
    acaba de frenar. La explicación larga está en `puerta_de_estado.py`.
    """
    exigir_parte_aprobado(
        ctx,
        repositorio,
        sin_veredicto=(
            "no consta que este parte haya pasado la validación: no se adjunta "
            "a una incidencia del ERP un parte del que nadie ha emitido "
            "veredicto"
        ),
        y_por_eso="no se adjunta a la reclamación",
    )


def _codigos_con_los_que_se_escribe(
    ctx: ContextoParte, declarados: CodigosDelParte | None
) -> CodigosDelParte:
    """1 bis · los dos códigos **guardados**, completos y cotejados (F-034).

    Salen de la situación que la puerta de aptitud acaba de leer —ni una
    consulta más (R10)— y son los que eligen la reclamación y componen el
    nombre del fichero (R8). Antes de devolverlos:

    1. **tienen que estar los dos** (R15): si falta uno, `CodigoNoConsta`
       diciendo cuál, y **no** se rellena con el del cuerpo. Va antes que el
       cotejo a propósito: con un código guardado vacío, lo que hay que hacer
       es teclearlo, y eso es lo que tiene que decir el mensaje aunque el
       cuerpo traiga otro;
    2. **lo declarado tiene que ser lo guardado** (R11, R12), normalizado con
       el criterio de F-032: si no, `CodigosNoCoinciden` diciendo cuál.

    Los dos cortes ocurren **antes** del login, de la lectura de la reclamación
    y de cualquier traza (R13), y también en dry-run (R14). Sin `declarados`
    no hay nada que cotejar y se escribe igual con lo guardado (R19).
    """
    guardados = codigos_guardados(ctx)
    exigir_codigos_completos(guardados, y_por_eso=_Y_POR_ESO_FALTA_UN_CODIGO)
    exigir_codigos_declarados(
        declarados, guardados, y_por_eso=_Y_POR_ESO_NO_COINCIDEN
    )
    return guardados


def _codigo_de_incidencia(numero_incidencia: str) -> str:
    """El código con el que se busca en el ERP, en su formato.

    Sin código no hay a quién adjuntar nada, y preguntar por una cadena vacía
    devolvería lo que devolviera. El borde lo traduce a **400**.

    **Desde F-034 recibe el número guardado** y ya no es el camino del código
    vacío: ese lo corta antes `exigir_codigos_completos` con un 409 que dice
    qué falta (R15). Hasta la decisión **H-4** del 2026-09-23 todavía llegaba
    aquí un número guardado que no está vacío pero **no tiene ningún tramo**
    —solo separadores—, con este 400 que mandaba a mirar el cuerpo; desde
    entonces `exigir_codigos_completos` lo corta también, con el mismo
    `a_codigo_de_sigrid` que usa esta función, y el `if` de abajo es
    inalcanzable por construcción. No se retira (`design.md` §4.2): es la
    última guarda antes de preguntarle al ERP por una cadena vacía.
    """
    codigo = a_codigo_de_sigrid(numero_incidencia)
    if not codigo:
        raise CuerpoDeCierreInvalido(
            "la petición no trae el número de incidencia, que es lo que "
            "identifica la reclamación a la que se adjunta el parte"
        )
    return codigo


# --------------------------------------------------------------------------
# Las salidas que no escriben en el ERP
# --------------------------------------------------------------------------


def _resolver_desde_la_traza(
    ctx: ContextoParte, traza: TrazaGrafico
) -> ContextoParte:
    """R24 · ya está dentro de Sigrid, y no se llama a nadie.

    **No se devuelve un plan**, y no es un descuido: no se ha leído ninguna
    reclamación, así que no hay dry-run que enseñar. Fabricar uno a partir de
    la traza sería inventarse una lectura que no se ha hecho. Lo que se
    devuelve es la traza, que es de donde salió la respuesta.
    """
    ctx.grafico = ResultadoGrafico(
        estado=EstadoGrafico.ADJUNTADO,
        traza=traza,
        adjuntado_at_utc=traza.adjuntado_at_utc,
    )
    log.info(
        "F-012 gráfico ya adjuntado según la traza local: parte=%s incidencia=%s",
        ctx.parte.hash,
        traza.numero_incidencia,
    )
    return ctx


def _dry_run(
    ctx: ContextoParte,
    graficos: GraficoPort,
    repositorio: RepositorioPartesPort,
    reclamacion,
    login: str,
    peticion,
    ahora: datetime,
) -> RespuestaGrafico:
    """El dry-run, con su traza de `error` si la pasarela lo rechaza (R33).

    El dry-run **es una lectura** y no escribe nada en el ERP, pero un rechazo
    aquí sí es información sobre este parte —la clase no está permitida, el
    concepto no existe, el login no vale— y tiene que quedar registrada: es
    exactamente lo que el bloque 9 de `tasks.md` verifica en T31.

    La excepción es `EscrituraDocumentalDeshabilitada` (R32, §7.3): **ninguna
    traza**. No ha pasado nada con este parte; lo que falta es una App Setting
    de otro proyecto, y una traza de `error` diría que el problema es del
    parte.
    """
    try:
        return graficos.adjuntar(peticion=peticion, commit=False)
    except EscrituraDocumentalDeshabilitada:
        raise
    except Exception as fallo:
        motivo = getattr(fallo, "motivo", str(fallo))
        plan = _plan(reclamacion, login, peticion, True, motivo)
        ctx.grafico = ResultadoGrafico(
            estado=EstadoGrafico.ERROR, plan=plan, motivo=motivo
        )
        _dejar_constancia(
            repositorio,
            _traza(
                ctx,
                plan,
                estado=EstadoGrafico.ERROR,
                usuario_oid=None,
                motivo=motivo,
                dry_run_at_utc=ahora,
            ),
        )
        raise


def _resolver_ya_cerrada(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    reclamacion,
    login: str,
    peticion,
    motivo: str | None,
    ahora: datetime,
) -> ContextoParte:
    """R16 · la reclamación ya estaba cerrada, y **eso no es un error**.

    No se le adjunta nada: sería colgar un documento de un expediente cerrado.
    Se registra y se devuelve en verde, porque el caso real es un reintento
    legítimo —una remesa que se vuelve a procesar— y tratarlo como fallo
    mandaría a alguien a mirar el ERP para nada.
    """
    plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=True)
    ctx.grafico = ResultadoGrafico(
        estado=EstadoGrafico.YA_CERRADA, plan=plan, motivo=motivo
    )
    _dejar_constancia(
        repositorio,
        _traza(
            ctx,
            plan,
            estado=EstadoGrafico.YA_CERRADA,
            usuario_oid=None,
            motivo=motivo,
            dry_run_at_utc=ahora,
        ),
    )
    log.info(
        "F-012 reclamación ya cerrada, no se adjunta nada: parte=%s incidencia=%s",
        ctx.parte.hash,
        reclamacion.codigo,
    )
    return ctx


# --------------------------------------------------------------------------
# La escritura
# --------------------------------------------------------------------------


def _escribir(
    ctx: ContextoParte,
    graficos: GraficoPort,
    repositorio: RepositorioPartesPort,
    plan: PlanDeGrafico,
    *,
    usuario_oid: str,
    ahora: datetime,
) -> ContextoParte:
    """El commit, su comprobación y su traza, pase lo que pase (R26–R29, R43).

    Un fallo deja la traza en `error` con su motivo y **sube sin reintentar**:
    aquí reintentar sería inofensivo —el endpoint es idempotente por
    contenido—, pero quien decide volver a intentarlo es quien pulsa el botón.
    Lo que sí hace el motivo es **decir que el reintento es seguro** (R29), que
    es la diferencia con F-009 y lo que permite actuar sin abrir el ERP.

    Y hay un caso que el borde **no puede deducir**: si el gráfico se escribió
    y la traza no se pudo guardar, sale `GraficoSinTraza` y no el
    `PersistenciaNoDisponible` de la base. Aquel dice «no se ha escrito nada,
    reintenta»; aquí **las tres filas ya están en Sigrid**.

    `EscrituraDocumentalDeshabilitada` se deja pasar **sin traza** a propósito
    (R32, §7.3): no ha pasado nada con este parte, falta una App Setting de
    otro proyecto, y una traza de `error` diría que el problema es del parte.
    """
    try:
        respuesta = graficos.adjuntar(peticion=plan.peticion, commit=True)
        _exigir_colgado(respuesta, plan)
    except EscrituraDocumentalDeshabilitada:
        raise
    except Exception as fallo:
        motivo = getattr(fallo, "motivo", str(fallo))
        ctx.grafico = ResultadoGrafico(
            estado=EstadoGrafico.ERROR, plan=plan, motivo=motivo
        )
        _dejar_constancia(
            repositorio,
            _traza(
                ctx,
                plan,
                estado=EstadoGrafico.ERROR,
                usuario_oid=usuario_oid,
                motivo=motivo,
                dry_run_at_utc=ahora,
            ),
        )
        raise

    ctx.grafico = ResultadoGrafico(
        estado=EstadoGrafico.ADJUNTADO,
        plan=plan,
        respuesta=respuesta,
        adjuntado_at_utc=ahora,
    )
    try:
        _dejar_constancia(
            repositorio,
            _traza(
                ctx,
                plan,
                estado=EstadoGrafico.ADJUNTADO,
                usuario_oid=usuario_oid,
                respuesta=respuesta,
                dry_run_at_utc=ahora,
                adjuntado_at_utc=ahora,
            ),
        )
    except ErrorDePersistencia as sin_traza:
        log.error(
            "F-012 gráfico sin traza: el parte %s ESTÁ adjunto a la incidencia "
            "%s en el ERP y no consta en la base",
            ctx.parte.hash,
            plan.reclamacion.codigo,
        )
        raise GraficoSinTraza(
            f"el parte SÍ está adjunto a la reclamación en Sigrid y no se ha "
            f"podido dejar constancia en la base de datos. Volver a pedirlo no "
            f"duplica nada —el endpoint es idempotente y responderá que ya "
            f"estaba—, pero lo que falta es la traza. Motivo: "
            f"{sin_traza.motivo}"
        ) from sin_traza

    log.info(
        "F-012 gráfico adjuntado: parte=%s incidencia=%s bytes=%d filas=%d "
        "idempotente=%s",
        ctx.parte.hash,
        plan.reclamacion.codigo,
        plan.peticion.bytes,
        respuesta.filas_afectadas,
        respuesta.idempotente,
    )
    return ctx


def _exigir_colgado(respuesta: RespuestaGrafico, plan: PlanDeGrafico) -> None:
    """R26, R27 · las dos comprobaciones que impiden dar por adjuntado lo que no.

    - **R26**: `ok and (committed or idempotente)`. La regla vive en el dominio
      (`esta_colgado`) y aquí solo se aplica; decidir por `committed` a solas
      daría por fallido el caso idempotente, que es el que ocurre en cada
      reintento.
    - **R27**: si la pasarela dice que **escribió**, tienen que ser exactamente
      tres filas —documental, negocio y enlace—. Cualquier otro número es un
      gráfico a medias. Solo se exige con `committed`: el caso idempotente trae
      `0` y es un éxito, y exigir tres a secas rompería justo el reintento.
    """
    if not esta_colgado(respuesta):
        raise GraficoFallido(
            f"la pasarela no ha confirmado que el parte quede adjunto a "
            f"{plan.reclamacion.codigo}, así que no se da por adjuntado. El "
            f"reintento es seguro: el endpoint es idempotente por contenido",
            reintento_seguro=True,
        )
    if respuesta.committed and respuesta.filas_afectadas != FILAS_ESPERADAS_GRAFICO:
        raise GraficoFallido(
            f"el gráfico de {plan.reclamacion.codigo} ha afectado a "
            f"{respuesta.filas_afectadas} filas y se esperaban "
            f"{FILAS_ESPERADAS_GRAFICO} (documental, negocio y enlace): no se "
            f"da por adjuntado. El reintento es seguro: el endpoint es "
            f"idempotente por contenido",
            reintento_seguro=True,
        )


# --------------------------------------------------------------------------
# El plan y la traza
# --------------------------------------------------------------------------


def _plan(
    reclamacion,
    login: str,
    peticion,
    cerrable: bool,
    motivo: str | None,
    *,
    ya_cerrada: bool = False,
    idempotente_previsto: bool = False,
    cod_previsto: str | None = None,
    ide_negocio_previsto: int | None = None,
    avisos_pasarela: tuple[str, ...] = (),
) -> PlanDeGrafico:
    """El plan del dry-run, compuesto en un solo sitio.

    Existe por lo mismo que `_plan` en `domain/models/cierre.py`: para que
    ninguna de las salidas se olvide de rellenar algo que quien confirma
    necesita leer.
    """
    return PlanDeGrafico(
        reclamacion=reclamacion,
        login_sigrid=login,
        peticion=peticion,
        cerrable=cerrable,
        ya_cerrada=ya_cerrada,
        motivo=motivo,
        idempotente_previsto=idempotente_previsto,
        cod_previsto=cod_previsto,
        ide_negocio_previsto=ide_negocio_previsto,
        avisos_pasarela=avisos_pasarela,
    )


def _traza(
    ctx: ContextoParte,
    plan: PlanDeGrafico,
    *,
    estado: EstadoGrafico,
    usuario_oid: str | None,
    respuesta: RespuestaGrafico | None = None,
    motivo: str | None = None,
    dry_run_at_utc: datetime | None = None,
    adjuntado_at_utc: datetime | None = None,
) -> TrazaGrafico:
    """La traza local del gráfico (R42, R43, R44, R45).

    Guarda el `oid` **opaco** de quien confirmó y **nunca** su correo, su
    nombre ni su login de Sigrid. La única excepción está declarada y es el
    `gra_cod`, que lleva el login dentro porque es el identificador que genera
    Sigrid y es lo que hace falta para localizar el gráfico.

    Ni un byte del PDF ni un campo manuscrito (R45): identificadores y el
    `sha256`.

    `reclamacion_ide` va **desde el primer dry-run** porque es la clave estable
    del ERP con la que se cruzan nuestras filas (F-024).
    """
    return TrazaGrafico(
        hash_parte=ctx.parte.hash,
        numero_incidencia=plan.reclamacion.codigo,
        estado=estado,
        reclamacion_ide=plan.reclamacion.ide,
        sha256=plan.peticion.sha256,
        bytes=plan.peticion.bytes,
        nombre_fichero=plan.peticion.nom,
        gratipide=plan.peticion.gratipide,
        gra_cod=respuesta.cod if respuesta is not None else None,
        gra_ide_negocio=respuesta.ide_negocio if respuesta is not None else None,
        gra_ide_documental=(
            respuesta.ide_documental if respuesta is not None else None
        ),
        rcg_ide=respuesta.ide_enlace if respuesta is not None else None,
        idempotente=respuesta.idempotente if respuesta is not None else False,
        confirmado_por=usuario_oid,
        motivo=motivo,
        dry_run_at_utc=dry_run_at_utc,
        adjuntado_at_utc=adjuntado_at_utc,
    )


def _dejar_constancia(
    repositorio: RepositorioPartesPort, traza: TrazaGrafico
) -> None:
    """Guarda la traza, tolerando que la fila ya sea terminal (R30).

    `guardar_grafico` devuelve `SIN_CAMBIOS` cuando la fila ya estaba en
    `adjuntado`: no había nada que hacer, que no es lo mismo que no haber
    podido. Aquí no se distingue porque no cambia nada de lo que este paso
    hace; lo que importa es que **no se pisa** la traza de una escritura real.
    """
    repositorio.guardar_grafico(traza=traza)
