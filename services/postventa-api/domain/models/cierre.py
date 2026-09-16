# services/postventa-api/domain/models/cierre.py
"""El vocabulario del cierre de una incidencia en Sigrid (F-009, paso 7).

**Dominio puro**: sin red, sin SQL, sin reloj y sin configuración. Entra una
reclamación leída del ERP y sale la decisión de si se cierra. Mismas entradas,
misma decisión, hoy y dentro de un año — que es lo que permite probar entera la
única pieza de F-009 que decide algo, sin abrir una conexión contra el ERP de
producción.

## Las tres reglas que este módulo no negocia

1. **El estado de cierre es un CÓDIGO, nunca un número** (`CHECKPOINTS.md` C3).
   `CER` es lo que se busca en `conest`; el `est` que le corresponde lo dice el
   ERP en ejecución y varía por instalación. Aquí no hay ni un número de estado.
2. **El dominio no sabe qué es un gráfico** (R20). `Reclamacion` no tiene ese
   campo y este módulo **no nombra ninguna de las dos tablas de gráficos del
   ERP** —un control negativo de `test_f009_dominio_cierre.py` lo comprueba—.
   Es la decisión del humano del 2026-08-26 —validar → cerrar → subir el PDF—
   convertida en algo que no se puede incumplir por descuido: no se puede
   consultar lo que no existe.
3. **Aquí ya no hay ningún aviso de «quedará sin gráfico».** Lo hubo: R21 de
   F-009 obligaba a advertir, en cada plan, de que la reclamación quedaría
   cerrada sin el parte dentro de Sigrid. **F-012 lo deroga** (su R48), porque
   con el gráfico adjuntándose antes del cambio de estado ese aviso sería
   falso — y un aviso falso enseñado en cada confirmación es peor que ninguno.
   Lo que sí se enseña ahora es **el estado real del gráfico**, y no lo compone
   este módulo: lo lee `paso_cierre` de la traza propia (R49).

## Lo que decide `evaluar`, y lo que no

Decide dos cosas y ni una más: si la reclamación **ya estaba cerrada** (R18,
que no es un error) y si su estado **admite cierre automático** (R19). Todo lo
demás —que el parte sea apto, que conste archivado, que el login esté
verificado— lo comprueba `application/pipelines/paso_cierre.py`, que es quien
tiene los puertos delante.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.models.nombrado import normalizar_codigo, tramos_de_codigo
from domain.models.persistencia import EstadoCierre

__all__ = [
    "CODIGOS_ESTADO_CERRABLE",
    "CODIGO_ESTADO_CIERRE",
    "LONGITUD_MAXIMA_LOGIN",
    "TEXTO_LOG_CIERRE",
    "TEXTO_PROCESO_ERP",
    "CorrespondenciaSigrid",
    "EstadoSigrid",
    "PlanDeCierre",
    "Reclamacion",
    "ResultadoCierre",
    "a_codigo_de_sigrid",
    "derivar_login_candidato",
    "evaluar",
]

#: El código del estado de cierre en `conest`. **Es un código, no un número.**
#:
#: Hoy le corresponde un `est` concreto en esta instalación, pero ese número es
#: configuración del ERP: se resuelve consultando `dbo.conest` por `tip` y por
#: este `cod`, y si la consulta no devuelve exactamente una fila, no se cierra
#: nada (R1, R2).
CODIGO_ESTADO_CIERRE = "CER"

#: Los estados desde los que este servicio cierra, por código (R19).
#:
#: `SAT` (SIN ATENDER), `PTE` (PENDIENTE) y `TER` (TERMINADA). Es una **lista
#: blanca**: un estado nuevo en el ERP no puede empezar a cerrarse solo porque
#: nadie se acordó de prohibirlo.
#:
#: `NPR` (NO PROCEDE) queda fuera **a propósito**: alguien decidió que esa
#: reclamación no procede, y cerrarla la daría por resuelta.
CODIGOS_ESTADO_CERRABLE: tuple[str, ...] = ("SAT", "PTE", "TER")

#: El texto que el ERP escribe en `dbo.log.tex` al cerrar un parte.
#:
#: Medido por F-008 sobre 6.843 filas. Se conserva como **prefijo** para no
#: desaparecer de los informes de Posventa, que filtran por
#: `tex LIKE 'Cerrar parte%'`.
TEXTO_PROCESO_ERP = "Cerrar parte"

#: Lo que escribe **este servicio** en `dbo.log.tex` (D1, `design.md` §1).
#:
#: Empieza por el texto del ERP —así sigue apareciendo en los informes que ya
#: existen— y nombra el servicio, de modo que un cierre hecho aquí se distinga
#: de uno hecho a mano con un solo `LIKE`. Eso es lo que hace **reversible** el
#: conjunto si el piloto se tuerce: se sabe exactamente qué revertir.
#:
#: Cabe: `log.tex` es `text` («Texto ilimitado»), sin tope.
TEXTO_LOG_CIERRE = f"{TEXTO_PROCESO_ERP} (postventa-incidencias)"

#: Longitud del campo `usu` de `dbo.log`: «Texto de 48 caracteres» (R35).
#:
#: Sale de `azure-apps/sigrid_tablas.md`, que es el diccionario del ERP y la
#: única fuente. `usu.cod` es más corto (24), así que cualquier login real
#: cabe; el tope existe para que un candidato absurdo no llegue a intentarse.
LONGITUD_MAXIMA_LOGIN = 48

#: Lo que se comprueba al construir el texto del log: que el prefijo se
#: conserva. Un despiste aquí nos borra de los informes de Posventa.
if not TEXTO_LOG_CIERRE.startswith(TEXTO_PROCESO_ERP):  # pragma: no cover
    raise AssertionError("el texto del log tiene que empezar por el del ERP (R25)")


@dataclass(frozen=True)
class EstadoSigrid:
    """Un estado de `dbo.conest`, con su número y su texto legible.

    El `est` está aquí porque es lo que viaja al `WHERE` de la escritura, no
    porque nadie lo escriba a mano: **siempre** llega leído del ERP. Lo que
    enseña el dry-run son `cod` y `res`, que es lo que una persona entiende
    (R9).
    """

    est: int
    cod: str
    res: str


@dataclass(frozen=True)
class Reclamacion:
    """La reclamación tal y como la devuelve la consulta del dry-run.

    Los once datos son los de `design.md` §6, y **ninguno es de gráficos**
    (R20). `tip` y `emp` salen de la propia reclamación y no de una constante
    (R4, D1): hoy todas son de la misma empresa y del mismo tipo, pero eso es
    un dato de esta instalación, exactamente igual que el número del estado.

    Inmutable a propósito: entre leerla y escribir hay varias llamadas, y el
    control optimista de R11 se apoya en que el estado de origen que se leyó
    sea exactamente el que viaja al `WHERE`.
    """

    ide: int
    emp: int
    tip: int
    est: int
    codigo: str
    descripcion: str
    estado_origen_cod: str
    estado_origen_res: str
    estado_destino_est: int
    estado_destino_cod: str
    estado_destino_res: str

    @property
    def estado_origen(self) -> EstadoSigrid:
        """El estado de partida, legible, para el dry-run (R9)."""
        return EstadoSigrid(
            est=self.est, cod=self.estado_origen_cod, res=self.estado_origen_res
        )

    @property
    def estado_destino(self) -> EstadoSigrid:
        """El estado de cierre resuelto contra `conest` (R1)."""
        return EstadoSigrid(
            est=self.estado_destino_est,
            cod=self.estado_destino_cod,
            res=self.estado_destino_res,
        )


@dataclass(frozen=True)
class PlanDeCierre:
    """Lo que devuelve el dry-run: qué se haría, y si se puede hacer.

    `ya_cerrada` es un campo propio y no un `motivo` más porque **no es un
    error** (R18): la reclamación estaba cerrada antes de que llegáramos, y eso
    se registra y se responde en verde. Confundirlo con un fallo haría que un
    reintento legítimo pareciera un problema.

    **Ya no lleva `aviso_sin_grafico`**: R21 de F-009 quedó derogado por R48 de
    F-012 el 2026-09-06. Con el gráfico adjuntándose antes del cambio de
    estado, aquel aviso sería falso. El estado del gráfico lo enseña el borde a
    partir de la traza propia (R49), y no este dataclass: es un dato leído de
    la base y no una decisión del dominio.
    """

    reclamacion: Reclamacion
    login_sigrid: str
    cerrable: bool
    motivo: str | None
    ya_cerrada: bool = False


@dataclass(frozen=True)
class ResultadoCierre:
    """Qué pasó al ejecutar el cierre: el estado y cuántas filas se tocaron.

    `filas_afectadas` tiene que ser **2** en un cierre real —la fila del
    estado de la reclamación y la fila de auditoría—; cualquier otra cosa es
    un error con su motivo y nunca un cierre dado por bueno (`design.md`
    §7.3).

    El dominio habla de **filas** y no de sentencias a propósito: quien sabe
    qué SQL las produce es `infrastructure/sigrid/`, y aquí no se nombra.
    """

    plan: PlanDeCierre
    estado: EstadoCierre
    filas_afectadas: int = 0
    motivo: str | None = None
    cerrado_at_utc: datetime | None = None


def evaluar(reclamacion: Reclamacion, *, login_sigrid: str) -> PlanDeCierre:
    """Decide si esta reclamación se cierra, sin tocar nada (R18, R19).

    El orden de las dos comprobaciones importa: **ya cerrada va primero**,
    porque `CER` tampoco está en `CODIGOS_ESTADO_CERRABLE` y sin este orden una
    reclamación ya cerrada saldría como «estado que no admite cierre», que es
    un error donde no lo hay.

    `login_sigrid` entra por parámetro y no se deriva aquí: quién firma el
    cierre lo resuelve `paso_cierre` contra la tabla de correspondencias y
    contra el ERP (R29–R32), y el dominio no habla con ninguno de los dos.
    """
    if _ya_cerrada(reclamacion):
        return _plan(
            reclamacion,
            login_sigrid,
            cerrable=False,
            ya_cerrada=True,
            motivo=(
                f"la reclamación {reclamacion.codigo} ya está en el estado de "
                f"cierre {reclamacion.estado_destino_cod}: no se escribe nada "
                f"en Sigrid y esto no es un error"
            ),
        )

    if reclamacion.estado_origen_cod not in CODIGOS_ESTADO_CERRABLE:
        return _plan(
            reclamacion,
            login_sigrid,
            cerrable=False,
            ya_cerrada=False,
            motivo=(
                f"la reclamación {reclamacion.codigo} está en el estado "
                f"«{reclamacion.estado_origen_cod or 'desconocido'}» "
                f"({reclamacion.estado_origen_res or 'sin descripción'}), que "
                f"no admite cierre automático. Los que sí: "
                f"{', '.join(CODIGOS_ESTADO_CERRABLE)}"
            ),
        )

    return _plan(
        reclamacion, login_sigrid, cerrable=True, ya_cerrada=False, motivo=None
    )


def a_codigo_de_sigrid(bruto: str | None) -> str:
    """El código de incidencia del parte, al formato de Sigrid (R6).

    Es la **inversa exacta** de lo que hace `domain/models/nombrado.py` al
    componer el nombre del fichero: allí la barra pasa a ` - ` porque una barra
    partiría el fichero en dos carpetas; aquí vuelve a ser barra, que es como
    lo escribe el ERP.

    Se apoya en `normalizar_codigo` y en `tramos_de_codigo` del propio módulo de
    nombrado —no en una copia— para que las dos conversiones traten igual los
    guiones raros que salen de los escaneos y de Word. Dos criterios del mismo
    concepto divergen siempre.

    **Compone por tramos, y eso es lo que la hace inversa exacta** (F-028 R45,
    R47). Hasta el 2026-09-15 buscaba literalmente el ` - ` del nombre del
    fichero y lo cambiaba por una barra, lo que dejaba dos agujeros: un código
    leído como `RS26.09-0149` —guion pegado— salía tal cual y el ERP no
    encontraba la reclamación, y en cuanto R44 dejó de rodear el separador de
    espacios aquel `replace` no encontraba ya nada que sustituir. Partir en
    tramos y unirlos con `/` no depende de cómo viniera escrito el papel: las
    seis formas de `design.md` §9.3 dan el mismo código. **Y esto importa más
    que en el nombre del fichero**, porque Sigrid busca la reclamación por
    **igualdad exacta**: un espacio de más no devuelve «casi» la reclamación,
    no devuelve ninguna, y el parte se queda sin cerrar.

    Un código que ya venga con barra sale igual: la conversión es idempotente.

    Un código que sea **solo separadores** no tiene ningún tramo y sale como
    cadena vacía, igual que uno ausente. Es lo que quien llama ya sabe tratar:
    sin código no se busca ninguna reclamación y no se cierra nada.
    """
    codigo = normalizar_codigo(bruto)
    if not codigo:
        return ""
    return "/".join(tramos_de_codigo(codigo))


def derivar_login_candidato(correo: str | None) -> str:
    """El login que **se propondrá** al ERP, a partir del correo (R30).

    Son las palabras del humano —«en principio es el mismo el de login en la
    app y el de Sigrid»— convertidas en código, y **tratadas como el supuesto
    que son**: esto no devuelve un login, devuelve un **candidato**. Quien
    decide si vale es el ERP, por lectura, antes de cualquier escritura.

    Que el supuesto necesite comprobación no es desconfianza: está medido. De
    los 8 usuarios del ERP con correo registrado, **6** cumplen la convención.
    Un 75 % no vale cuando el error consiste en firmar en el log de un ERP de
    producción el cierre de una persona que no lo hizo.

    Se normaliza a minúsculas porque un login no son dos logins según cómo lo
    escriba el proveedor de identidad. Un correo que no lo sea —vacío, sin
    arroba, sin parte local— devuelve cadena vacía: aquí no se inventa nada, y
    quien decide qué hacer con «no hay candidato» es quien lo pidió.
    """
    limpio = (correo or "").strip().lower()
    if "@" not in limpio:
        return ""
    # `partition` y no `split(..., 1)`: dice lo que se quiere —lo que hay antes
    # de la primera arroba— sin un número que explicar, y da lo mismo con un
    # correo raro de dos arrobas.
    return limpio.partition("@")[0].strip()


def _ya_cerrada(reclamacion: Reclamacion) -> bool:
    """¿Está ya en el estado de cierre? (R18).

    Dos señales, y basta una: que el `est` sea el que `conest` resolvió para
    `CER`, o que el código legible del estado de origen sea ese. Ninguna de las
    dos es un número escrito aquí — las dos salen de la misma lectura del ERP.
    """
    return (
        reclamacion.est == reclamacion.estado_destino_est
        or reclamacion.estado_origen_cod == CODIGO_ESTADO_CIERRE
    )


def _plan(
    reclamacion: Reclamacion,
    login_sigrid: str,
    *,
    cerrable: bool,
    ya_cerrada: bool,
    motivo: str | None,
) -> PlanDeCierre:
    """El plan, compuesto en un solo sitio para las tres salidas de `evaluar`.

    Nació para que el aviso de R21 no dependiera de acordarse de pasarlo en
    cada salida. Ese aviso lo derogó R48 de F-012, y la función se queda: sigue
    siendo el único sitio donde se construye un `PlanDeCierre`, que es lo que
    hace que añadir un campo mañana no tenga tres sitios donde olvidarse.
    """
    return PlanDeCierre(
        reclamacion=reclamacion,
        login_sigrid=login_sigrid,
        cerrable=cerrable,
        motivo=motivo,
        ya_cerrada=ya_cerrada,
    )


@dataclass(frozen=True)
class CorrespondenciaSigrid:
    """El par `oid` de Entra → login de Sigrid de una persona (D2, R29–R34).

    Es la razón de existir de `postventa.usuarios_sigrid`, y es el **único**
    sitio del proyecto donde conviven las dos identidades: en el log del ERP va
    el login, en la traza del cierre va solo el `oid` (R43), y aquí va el par.

    `verificado_at_utc` es lo que distingue una correspondencia **confirmada**
    —comprobada contra `dbo.usu` y utilizable sin volver a preguntar (R29)— de
    un alta manual todavía por confirmar, que tiene precedencia sobre la
    derivación (R34) pero **no** exime de verificar antes de escribir (R32).
    """

    #: **DATO PERSONAL seudónimo**: el `oid` opaco de Entra ID.
    usuario_oid: str
    #: El `usu.cod` del ERP. Nunca se escribe sin haberlo verificado (R32).
    login_sigrid: str
    alta_at_utc: datetime
    verificado_at_utc: datetime | None = None

    @property
    def confirmada(self) -> bool:
        """¿Se puede usar sin derivar ni volver a preguntar al ERP? (R29)."""
        return self.verificado_at_utc is not None
