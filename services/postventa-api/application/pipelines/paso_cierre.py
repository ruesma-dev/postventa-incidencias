# services/postventa-api/application/pipelines/paso_cierre.py
"""Paso 7 del pipeline: cerrar la incidencia en Sigrid (F-009).

Habla con **puertos**, jamás con adaptadores: este módulo no sabe que debajo
hay una pasarela HTTP ni que hay PostgreSQL, y por eso se prueba entero con
dobles en memoria, **sin red y sin escribir en el ERP de producción**. Es lo
mismo que hace `paso_archivo` con `ArchivoPort`.

`ahora` entra por parámetro y no se lee del reloj aquí, por lo mismo que en
F-005 y F-006: un paso que consulta la hora no se puede probar dos veces con el
mismo resultado, y lo que produce acaba escrito en un ERP de producción.

`paso_cierre` **no construye adaptadores**: la composición vive en el punto de
entrada (`docs/CONVENTIONS.md`). Aquí no se puede ni intentar escribir desde
local, porque aquí no hay nada que sepa cómo hacerlo.

## Quién firma el cierre, que es lo que resuelve este módulo hoy

El mecanismo lo decidió el humano el 2026-08-26 —«el correo manda y el login se
confirma una vez»— sobre un supuesto que **la base no confirma**: `usu.ele`
está vacío en los 228 usuarios del ERP. Así que el supuesto se trata como
supuesto:

1. **Correspondencia confirmada** → se usa, **sin derivar nada** y sin volver a
   preguntarle al ERP (R29). La derivación es la **siembra**, no el mecanismo
   de cada cierre.
2. **Correspondencia sin confirmar** —un alta manual— → **tiene precedencia
   sobre la derivación** (R34), pero se verifica igual antes de escribir (R32).
   Precedencia no es exención.
3. **Sin correspondencia** → se deriva un candidato del correo (R30) y se
   verifica contra el ERP por lectura.
4. **El ERP dice que no** → no se cierra (R31), y el error nombra el correo y
   el login intentado para que se pueda dar de alta a mano.
5. **El ERP dice que sí** → se guarda como confirmada (R33).

Lo que hace seguro apoyarse en un supuesto no confirmado es el paso 3: el
supuesto **propone**, el ERP **dispone**, y solo lo que el ERP confirma se
guarda y se escribe.
"""

from __future__ import annotations

import logging
from datetime import datetime

from domain.models.cierre import (
    CODIGO_ESTADO_CIERRE,
    CorrespondenciaSigrid,
    PlanDeCierre,
    ResultadoCierre,
    a_codigo_de_sigrid,
    derivar_login_candidato,
    evaluar,
)
from domain.models.errores import (
    CierreFallido,
    CierreSinTraza,
    CuerpoDeCierreInvalido,
    ErrorDePersistencia,
    EstadoNoCerrable,
    ParteNoAdjuntado,
    ParteNoArchivado,
    ReclamacionNoLocalizada,
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)
from domain.models.estado import EstadoParte
from domain.models.persistencia import (
    EstadoArchivo,
    EstadoCierre,
    EstadoGrafico,
    TrazaCierre,
)
from domain.ports.erp import ErpPort
from domain.ports.persistencia import (
    RepositorioPartesPort,
    RepositorioPreferenciasPort,
)
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort

from application.pipelines.constancia import anotar_estado
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.puerta_de_estado import (
    exigir_parte_aprobado,
    situacion_leida,
)

__all__ = [
    "FILAS_ESPERADAS",
    "exigir_autorizacion_para_escribir",
    "paso_cierre",
    "resolver_login_de_sigrid",
]

log = logging.getLogger(__name__)

#: Lo que afecta un cierre correcto: la fila del estado y la de auditoría.
#:
#: El adaptador ya lo comprueba, y aquí se vuelve a comprobar. No es
#: redundancia decorativa: dar por cerrado lo que no lo está es el fallo más
#: caro de esta feature, y este paso es el que escribe la traza que dirá para
#: siempre que la incidencia se cerró.
FILAS_ESPERADAS = 2


def paso_cierre(
    ctx: ContextoParte,
    erp: ErpPort,
    repositorio: RepositorioPartesPort,
    usuarios: RepositorioUsuariosSigridPort,
    preferencias: RepositorioPreferenciasPort,
    *,
    commit: bool,
    confirmado: bool,
    usuario_oid: str,
    correo: str,
    numero_incidencia: str,
    ahora: datetime,
) -> ContextoParte:
    """Cierra la incidencia en Sigrid y deja constancia de lo que pasó.

    Los pasos, **en este orden**, y el orden es la mitad del requisito:

    1. **Puerta de aptitud** (R16). Antes de nada: un parte que nadie ha
       validado no cierra una incidencia del ERP.
    2. **Puerta de archivo** (R17). El orden del procedimiento de Posventa:
       primero el documento, después el cierre. Es lo que sostiene el riesgo
       aceptado de `design.md` §2.
    3. **El login**, resuelto y **verificado contra el ERP** (R29–R32). Va
       antes del dry-run para que un usuario sin correspondencia se entere
       enseguida y no después de leer media reclamación.
    4. **El dry-run** (R8), que es una lectura y no escribe nada.
    5. **`evaluar`** (R18, R19), que es dominio puro.
    6. **La traza `dry_run_ok`** (R40).
    7. Y **solo si `commit`** y hay confirmación o auto-cierre (R12, R13): la
       escritura y la traza `cerrado` (R41).
    8. Cuando el cierre **ya consta** —el ERP escrito y su traza guardada, o la
       reclamación que ya estaba cerrada—, la fila `→ cerrado` del histórico de
       estado (F-028, R18). Va la última a propósito: es constancia, y lo que
       no ocurrió no se apunta.

    Levanta `ParteNoApto`, `ParteNoArchivado`, `CuerpoDeCierreInvalido`,
    `UsuarioSigridNoMapeado`, `UsuarioSigridInexistente`,
    `ReclamacionNoLocalizada`, `EstadoDeCierreNoResoluble`, `EstadoNoCerrable`,
    `EstadoCambiadoDesdeElDryRun` y `CierreFallido` **sin traducir**:
    convertir eso en códigos HTTP es trabajo del borde.

    El log lleva el `hash` del parte, el código de la incidencia y los códigos
    de estado. **Nunca** el correo, ni el login, ni el `oid`, ni nada del papel
    (R44, R45): lo lee cualquiera que abra Application Insights.
    """
    _exigir_admitido(ctx, repositorio)
    _exigir_archivado(ctx)

    codigo = _codigo_de_incidencia(numero_incidencia)
    login = resolver_login_de_sigrid(
        usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
    )

    plan = _dry_run(erp, codigo=codigo, login=login)

    if plan.ya_cerrada:
        return _resolver_ya_cerrada(ctx, repositorio, plan, ahora=ahora)

    if not plan.cerrable:
        _dejar_constancia(
            repositorio,
            ctx,
            _traza(
                ctx,
                plan,
                estado=EstadoCierre.ERROR,
                usuario_oid=None,
                motivo=plan.motivo,
                dry_run_at_utc=ahora,
            ),
        )
        raise EstadoNoCerrable(plan.motivo or "la reclamación no admite cierre")

    _dejar_constancia(repositorio, ctx, _traza_de_dry_run(ctx, plan, ahora=ahora))

    # R49 (F-012) · el estado del gráfico se lee **del repositorio**, nunca del
    # cuerpo de la petición: si viniera del cuerpo, quien llama podría afirmar
    # que adjuntó algo que no adjuntó. Se lee también en el dry-run, porque es
    # lo que hay que enseñar antes de confirmar (R50: aquí no se exige nada).
    ctx.traza_grafico = repositorio.consultar_grafico(hash_parte=ctx.parte.hash)

    ctx.cierre = ResultadoCierre(plan=plan, estado=EstadoCierre.DRY_RUN_OK)
    if not commit:
        log.info(
            "F-009 dry-run correcto: parte=%s incidencia=%s origen=%s destino=%s",
            ctx.parte.hash,
            plan.reclamacion.codigo,
            plan.reclamacion.estado_origen_cod,
            plan.reclamacion.estado_destino_cod,
        )
        return ctx

    _exigir_adjuntado(ctx)
    exigir_autorizacion_para_escribir(
        preferencias, confirmado=confirmado, usuario_oid=usuario_oid
    )
    return _escribir(
        ctx, erp, repositorio, plan, usuario_oid=usuario_oid, ahora=ahora
    )


def _exigir_admitido(ctx: ContextoParte, repositorio: RepositorioPartesPort) -> None:
    """Solo se cierra el parte que está **`aprobado`** (R16; F-028 R33).

    Cerrar «por si acaso» una incidencia cuyo parte fue a la cola de validación
    humana la daría por resuelta en el ERP de producción sin que nadie haya
    mirado el papel. Lo que F-028 cambia es que el permiso deja de ser un dato
    suelto y pasa a ser **el estado del parte**: la máquina, o una persona que
    se hizo responsable y quedó registrada, y **ninguna de las dos si otra
    persona lo rechazó** (R5).

    Aquí se gana además una puerta que antes no existía: un parte **`cerrado`**
    no vuelve a pasar (R7). Su reclamación ya consta cerrada en el ERP, y
    recorrer otra vez el circuito solo podría pedir un segundo cierre de lo ya
    cerrado.

    «No hay veredicto» sigue siendo un motivo aparte, y va primero: se arregla
    revalidando el parte, no decidiendo sobre él. La situación se lee del
    repositorio y nunca del cuerpo (R33) —igual que `traza_grafico` más abajo,
    y por el mismo argumento—, y se queda en `ctx.situacion`, que es lo que
    luego reutiliza la constancia del cierre.
    """
    exigir_parte_aprobado(
        ctx,
        repositorio,
        sin_veredicto=(
            "no consta que este parte haya pasado la validación: no se cierra "
            "una incidencia con un parte del que nadie ha emitido veredicto"
        ),
        y_por_eso="no se cierra la incidencia",
    )


def _exigir_archivado(ctx: ContextoParte) -> None:
    """El parte tiene que constar **archivado** (R17).

    `pendiente` y `error` no valen, y son justo los dos estados en los que el
    fichero puede no estar arriba. Si el PDF no está guardado en ninguna parte,
    cerrar la incidencia la da por resuelta sin dejar la prueba en ningún
    sitio — y el riesgo aceptado de `design.md` §2 solo es asumible **porque el
    parte firmado existe**.
    """
    if ctx.archivo is None or ctx.archivo.estado != EstadoArchivo.ARCHIVADO:
        estado = "ninguno" if ctx.archivo is None else ctx.archivo.estado.value
        raise ParteNoArchivado(
            f"este parte no consta archivado (estado del archivo: {estado}), "
            f"así que no se cierra la incidencia: primero el documento, después "
            f"el cierre"
        )


def _exigir_adjuntado(ctx: ContextoParte) -> None:
    """El parte tiene que constar **adjuntado** al ERP (F-012, R2).

    Es la precondición nueva del cierre, simétrica a la de archivo, y es lo que
    **elimina la anomalía** que `docs/ARCHITECTURE.md` describía como riesgo
    aceptado: reclamaciones en `CER` sin ninguna fila de gráfico, algo que no
    había ocurrido ni una vez en los 2.365 cierres de «Cerrar parte» desde
    2023.

    Tres cosas que no son casualidad:

    - **Solo `adjuntado` vale.** Un `dry_run_ok` dice que se miró qué pasaría,
      no que el parte esté dentro de Sigrid.
    - **Solo con `commit`.** El dry-run del cierre no lo exige (R50), para que
      los dos dry-run se puedan enseñar juntos antes de confirmar.
    - **Se lee de la traza propia y no del ERP** (R52). R20 de F-009 sigue
      vigente: este módulo no sabe qué es un gráfico del ERP y no nombra
      ninguna de sus tablas.

    Va **antes** de la autorización a propósito: con `commit`, sin confirmar y
    sin gráfico, lo que falta de verdad es el gráfico. Al revés, quien lo
    recibiera creería que basta con confirmar, confirmaría, y se encontraría el
    mismo 409 una pantalla después.
    """
    traza = ctx.traza_grafico
    if traza is not None and traza.estado == EstadoGrafico.ADJUNTADO:
        return

    estado = "ninguno" if traza is None else traza.estado.value
    raise ParteNoAdjuntado(
        f"este parte no consta adjuntado a la reclamación en Sigrid (estado "
        f"del gráfico: {estado}), así que no se cierra: primero se adjunta el "
        f"parte con POST /api/adjuntar y después se cierra, para que ninguna "
        f"reclamación quede cerrada sin su parte dentro del ERP"
    )


def _codigo_de_incidencia(numero_incidencia: str) -> str:
    """El código con el que se busca en el ERP, en su formato (R6).

    Sin código no hay a quién preguntar, y preguntar por una cadena vacía
    devolvería lo que devolviera. El borde lo traduce a **400**.
    """
    codigo = a_codigo_de_sigrid(numero_incidencia)
    if not codigo:
        raise CuerpoDeCierreInvalido(
            "la petición no trae el número de incidencia, que es lo que "
            "identifica la reclamación en el ERP"
        )
    return codigo


def _dry_run(erp: ErpPort, *, codigo: str, login: str) -> PlanDeCierre:
    """La lectura del ERP y la decisión del dominio, en ese orden (R8, R18, R19)."""
    reclamacion = erp.leer_reclamacion(
        codigo=codigo, codigo_estado_cierre=CODIGO_ESTADO_CIERRE
    )
    if reclamacion is None:
        raise ReclamacionNoLocalizada(
            f"no hay ninguna reclamación con el código {codigo} en el tipo de "
            f"posventa del ERP: no se cierra nada"
        )
    return evaluar(reclamacion, login_sigrid=login)


def exigir_autorizacion_para_escribir(
    preferencias: RepositorioPreferenciasPort, *, confirmado: bool, usuario_oid: str
) -> None:
    """Sin confirmación explícita o auto-cierre activo, no se escribe (R12–R14).

    **Es el requisito que impide cerrar por un error de flujo.** El auto-cierre
    ahorra un clic, no una comprobación: cuando está activo se llega aquí
    igual, con el dry-run ya hecho y las precondiciones ya pasadas (R13).

    La preferencia se consulta **solo si no hay confirmación**: quien acaba de
    confirmar en el front no necesita que le preguntemos a la base si además
    tenía auto-cierre, y es un viaje menos a un servidor compartido.

    Sale como `CuerpoDeCierreInvalido` (→ 400) y no como un 409 porque eso es
    lo que es: se pidió `commit` sin traer la confirmación que el contrato
    exige, y el 400 dice **qué** falta (R47).
    """
    if confirmado:
        return
    if preferencias.obtener_preferencias(usuario_oid=usuario_oid).auto_cierre:
        return
    raise CuerpoDeCierreInvalido(
        "se ha pedido cerrar con 'commit' sin 'confirmado' y este usuario no "
        "tiene el auto-cierre activo: no se escribe en el ERP sin que alguien "
        "lo confirme"
    )


def _escribir(
    ctx: ContextoParte,
    erp: ErpPort,
    repositorio: RepositorioPartesPort,
    plan: PlanDeCierre,
    *,
    usuario_oid: str,
    ahora: datetime,
) -> ContextoParte:
    """La escritura y su traza, pase lo que pase (R27, R41).

    Un fallo deja la traza en `error` con su motivo y **sube sin reintentar**:
    reintentar contra un ERP de producción sin que nadie mire es cómo se
    cierran dos veces las cosas, y el reintento lo pide una persona.

    Y hay un caso que el borde **no puede deducir**, así que se nombra aquí: si
    la escritura en el ERP salió bien y la traza no se pudo guardar, sale
    `CierreSinTraza` y no el `PersistenciaNoDisponible` de la base. La
    diferencia no es cosmética: aquel dice «no se ha cerrado nada, reintenta», y
    **la incidencia ya está cerrada en producción**. Es el defecto 14 de F-010
    —el mismo que en el archivo produjo `ArchivoSinTraza`— aplicado donde más
    caro sale.
    """
    try:
        filas = erp.cerrar(plan=plan, ahora=ahora)
        if filas != FILAS_ESPERADAS:
            raise CierreFallido(
                f"el cierre de {plan.reclamacion.codigo} ha afectado a {filas} "
                f"filas y se esperaban {FILAS_ESPERADAS}: no se da por cerrado"
            )
    except Exception as fallo:
        ctx.cierre = ResultadoCierre(
            plan=plan,
            estado=EstadoCierre.ERROR,
            motivo=getattr(fallo, "motivo", str(fallo)),
        )
        _dejar_constancia(
            repositorio,
            ctx,
            _traza(
                ctx,
                plan,
                estado=EstadoCierre.ERROR,
                usuario_oid=usuario_oid,
                motivo=ctx.cierre.motivo,
                dry_run_at_utc=ahora,
            ),
        )
        raise

    ctx.cierre = ResultadoCierre(
        plan=plan,
        estado=EstadoCierre.CERRADO,
        filas_afectadas=filas,
        cerrado_at_utc=ahora,
    )
    try:
        _dejar_constancia(
            repositorio,
            ctx,
            _traza(
                ctx,
                plan,
                estado=EstadoCierre.CERRADO,
                usuario_oid=usuario_oid,
                dry_run_at_utc=ahora,
                cerrado_at_utc=ahora,
            ),
        )
    except ErrorDePersistencia as sin_traza:
        # Aquí arriba **el ERP ya está escrito**, y eso es lo que hace falta
        # contar. Dejar salir el error de la base tal cual produciría el mismo
        # 503 que sale cuando no se ha tocado nada, y las dos lecturas llevan a
        # acciones opuestas: reintentar, o ir a mirar el ERP.
        log.error(
            "F-009 cierre sin traza: la incidencia %s ESTÁ cerrada en el ERP y "
            "no consta en la base",
            plan.reclamacion.codigo,
        )
        raise CierreSinTraza(sin_traza.motivo) from sin_traza

    _anotar_que_el_parte_queda_cerrado(repositorio, ctx, ahora=ahora)

    log.info(
        "F-009 incidencia cerrada: parte=%s incidencia=%s origen=%s destino=%s filas=%d",
        ctx.parte.hash,
        plan.reclamacion.codigo,
        plan.reclamacion.estado_origen_cod,
        plan.reclamacion.estado_destino_cod,
        filas,
    )
    return ctx


def _resolver_ya_cerrada(
    ctx: ContextoParte,
    repositorio: RepositorioPartesPort,
    plan: PlanDeCierre,
    *,
    ahora: datetime,
) -> ContextoParte:
    """La reclamación ya estaba cerrada, y **eso no es un error** (R18).

    Se registra y se devuelve en verde, sin escribir nada en Sigrid. Tratarlo
    como un fallo haría que un reintento legítimo —volver a lanzar una remesa
    que ya se procesó— pareciera un problema y mandara a alguien a mirar el
    ERP.
    """
    ctx.cierre = ResultadoCierre(plan=plan, estado=EstadoCierre.YA_CERRADA)
    _dejar_constancia(
        repositorio,
        ctx,
        _traza(
            ctx,
            plan,
            estado=EstadoCierre.YA_CERRADA,
            usuario_oid=None,
            motivo=plan.motivo,
            dry_run_at_utc=ahora,
        ),
    )
    _anotar_que_el_parte_queda_cerrado(repositorio, ctx, ahora=ahora)
    log.info(
        "F-009 incidencia ya cerrada: parte=%s incidencia=%s",
        ctx.parte.hash,
        plan.reclamacion.codigo,
    )
    return ctx


def _traza_de_dry_run(
    ctx: ContextoParte, plan: PlanDeCierre, *, ahora: datetime
) -> TrazaCierre:
    """La traza de R40: qué se leyó y cuándo, antes de escribir nada."""
    return _traza(
        ctx,
        plan,
        estado=EstadoCierre.DRY_RUN_OK,
        usuario_oid=None,
        dry_run_at_utc=ahora,
    )


def _traza(
    ctx: ContextoParte,
    plan: PlanDeCierre,
    *,
    estado: EstadoCierre,
    usuario_oid: str | None,
    motivo: str | None = None,
    dry_run_at_utc: datetime | None = None,
    cerrado_at_utc: datetime | None = None,
) -> TrazaCierre:
    """La traza local del cierre (R41, R43).

    Guarda el `oid` **opaco** de quien confirmó y **nunca** su correo, su
    nombre ni su login de Sigrid. No es una duplicación de R28 ni choca con
    R33: son tres sitios distintos. En el log del ERP va el login, porque es el
    ERP quien necesita saber quién ejecutó el proceso; aquí va solo el `oid`,
    porque para reconstruir qué hicimos no hace falta saber quién es.

    Los dos códigos de estado se guardan **como traza de lo que se hizo**, no
    como configuración: nadie los lee para decidir nada, y registrarlos a
    posteriori no incumple C3.
    """
    return TrazaCierre(
        hash_parte=ctx.parte.hash,
        numero_incidencia=plan.reclamacion.codigo,
        estado=estado,
        estado_origen_sigrid=plan.reclamacion.estado_origen_cod,
        estado_destino_sigrid=plan.reclamacion.estado_destino_cod,
        confirmado_por=usuario_oid,
        motivo=motivo,
        dry_run_at_utc=dry_run_at_utc,
        cerrado_at_utc=cerrado_at_utc,
    )


def _anotar_que_el_parte_queda_cerrado(
    repositorio: RepositorioPartesPort, ctx: ContextoParte, *, ahora: datetime
) -> None:
    """La fila `→ cerrado` del histórico de estado (F-028, T9).

    Se llama **después** de que el cierre conste —la escritura hecha y su traza
    guardada—, y por eso un cierre fallido no deja fila: una fila `→ cerrado` de
    algo que reventó dejaría el parte en un estado terminal (R7) del que no sale
    ninguna flecha, y nadie podría volver a intentarlo.

    También se llama cuando la reclamación **ya estaba cerrada**. No la cerramos
    nosotros, pero el hecho es el mismo —esa reclamación está cerrada en el
    ERP— y el parte queda `cerrado` igual (R18). Si no se anotara, la última
    fila del histórico diría `aprobado` mientras el parte está `cerrado`: el
    relato contradiciendo al estado.

    Y se aplica la misma regla de constancia que en `paso_persistencia`, que
    aquí no es un detalle: el camino de «ya cerrada» se recorre **cada vez** que
    alguien vuelve a lanzar una remesa procesada, así que sin la regla cada
    pasada añadiría un `cerrado → cerrado`.

    ## Si la base falla aquí, el cierre sigue siendo un cierre

    Es el único sitio del proyecto donde un fallo de persistencia **se traga**, y
    el motivo es que aquí arriba la incidencia **ya está cerrada en el ERP de
    producción** y su `TrazaCierre` —que es de donde se deriva el estado (R18)—
    **ya está guardada**. Lo que falla es el renglón del relato, que es
    constancia y nunca criterio (R26).

    Dejarlo salir convertiría un cierre que ocurrió en el 503 «vuelve a
    intentarlo» de la base, y quien lo reintentara le pediría otra vez al ERP
    que cerrara lo ya cerrado. No es `CierreSinTraza`, que es el caso de al
    lado y sí sube: allí lo que falta es la traza, o sea el hecho; aquí falta
    solo su eco, y el siguiente reproceso del parte lo recupera solo, porque la
    regla de constancia lo volverá a calcular con la traza ya en `cerrado`.

    El log lleva el `hash` y nada más: ni `oid`, ni motivo, ni nada del papel
    (R52, R44, R45).
    """
    try:
        anotar_estado(
            repositorio,
            situacion_leida(ctx, repositorio),
            hash_parte=ctx.parte.hash,
            estado=EstadoParte.CERRADO,
            ahora=ahora,
        )
    except ErrorDePersistencia:
        log.error(
            "F-028 constancia de cierre no anotada: el parte %s ESTÁ cerrado y "
            "su traza consta; falta solo la fila del histórico",
            ctx.parte.hash,
        )


def _dejar_constancia(
    repositorio: RepositorioPartesPort, ctx: ContextoParte, traza: TrazaCierre
) -> None:
    """Guarda la traza, tolerando que la fila ya sea terminal (R42).

    `guardar_cierre` devuelve `SIN_CAMBIOS` cuando la fila ya estaba en
    `cerrado`: no había nada que hacer, que no es lo mismo que no haber podido.
    Aquí no se distingue porque no cambia nada de lo que este paso hace; lo que
    importa es que **no se pisa** la traza de una escritura real.
    """
    repositorio.guardar_cierre(traza=traza)


def resolver_login_de_sigrid(
    usuarios: RepositorioUsuariosSigridPort,
    erp: ErpPort,
    *,
    usuario_oid: str,
    correo: str,
    ahora: datetime,
) -> str:
    """El login con el que se firmará el cierre (R29–R34).

    Levanta `UsuarioSigridNoMapeado` (→ 409) si no hay de dónde sacarlo y
    `UsuarioSigridInexistente` (→ 409) si el ERP no lo confirma. En los dos
    casos **no se escribe nada en Sigrid**: esto ocurre antes de tocar nada.

    Nada de lo que devuelve o levanta lleva el `oid` (R43, R45): el `oid` es
    dato personal seudónimo, no le dice nada a quien lea el mensaje y sí
    identifica a la persona en un log. El **correo** sí va en el mensaje, y no
    choca con R45: se lo estamos diciendo a su dueño, que lo tiene delante.
    """
    correspondencia = usuarios.resolver_login(usuario_oid=usuario_oid)

    if correspondencia is not None and correspondencia.confirmada:
        return correspondencia.login_sigrid

    login = _candidato(correspondencia, correo=correo)
    _exigir_que_el_erp_lo_confirme(erp, login=login, correo=correo)

    usuarios.guardar_login(
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=login,
            alta_at_utc=(
                correspondencia.alta_at_utc if correspondencia is not None else ahora
            ),
            verificado_at_utc=ahora,
        )
    )
    return login


def _candidato(
    correspondencia: CorrespondenciaSigrid | None, *, correo: str
) -> str:
    """El login que se le va a proponer al ERP (R30, R34).

    **El alta manual gana a la derivación**, y ese orden es el requisito: la
    tabla existe justamente para los casos en los que la convención falla —2 de
    los 8 usuarios medidos—, así que derivar por encima de lo que un
    administrador dio de alta la dejaría sin servir para nada.
    """
    if correspondencia is not None:
        return correspondencia.login_sigrid

    login = derivar_login_candidato(correo)
    if not login:
        raise UsuarioSigridNoMapeado(
            "no hay correspondencia guardada con el ERP para este usuario y "
            "tampoco un correo del que derivar un candidato, así que no hay con "
            "qué firmar el cierre: hay que dar el mapeo de alta a mano con "
            "infra/07_alta_usuario_sigrid.ps1"
        )
    return login


def _exigir_que_el_erp_lo_confirme(erp: ErpPort, *, login: str, correo: str) -> None:
    """El ERP tiene la última palabra, y sin ella no se cierra (R31, R32).

    Se comprueba **siempre** que la correspondencia no esté confirmada: venga de
    un alta manual o de una derivación. Dar por bueno un login sin comprobarlo
    sería firmar en el log de un ERP de producción a nombre de alguien que
    quizá no existe.

    El mensaje nombra el correo **y** el login intentado. Sin esas dos cosas,
    quien lo recibe no puede dar de alta la correspondencia: no sabría ni de
    quién es el problema ni qué se probó.
    """
    if erp.existe_usuario(login=login):
        return

    raise UsuarioSigridInexistente(
        f"el login «{login}», derivado del correo {correo}, no existe "
        f"exactamente una vez en el maestro de usuarios del ERP, así que no se "
        f"cierra nada y no se ha escrito nada en Sigrid: hay que dar de alta la "
        f"correspondencia a mano con infra/07_alta_usuario_sigrid.ps1"
    )
