<!-- specs/F-059-volcado-sigrid-backend/design.md -->
# F-059 · Volcado a Sigrid en el backend — Diseño técnico

> **Aprobado por el humano el 2026-10-07** (decisiones y respuestas en §20).
> Es el **tramo A** de la spec conjunta de F-040, partida por D-1: esta ficha
> es el backend (R1–R43) y va **antes**; el front (R50–R59) es **F-040**
> (`specs/F-040-volcado-sigrid/`), que consume el contrato de §11 y está
> bloqueada por esta.

## 0 · Dónde está el riesgo

| Si falla… | Consecuencia | Quién lo ve |
|---|---|---|
| Se escribe sin ensayo o sin confirmar | Partes en el **ERP de producción** que nadie revisó | Posventa y la propiedad; anularlos es a mano, uno a uno |
| Se manda algo distinto de lo aprobado | Un parte con otra unidad, oficio o industrial | Posventa, al tramitarlo |
| Se duplica un parte | Dos partes de la misma incidencia; el industrial recibe dos avisos al pasar a PTE | Posventa y el industrial |
| Se pierde el resultado | La bandeja dice «aprobada» de algo que ya está en Sigrid, o «volcada» de algo que no | Quien vuelca, que repetiría o daría por hecho |
| La ventana no muerde | Cualquier versión desplegada escribe sin gesto previo | Nadie, hasta que pasa |
| El tiempo | El proxy corta a los 45 s y la persona no sabe qué se creó | Quien vuelca |
| Datos personales | Propietario o persona que reclama en un log o una respuesta | Quien lea los logs |
| El DDL | Algo fuera del esquema propio de `psql-albaranes-rs9k2` | Albaranes y los demás |

**Rigor `critico`**: RED con traza pegada en los centrales (R1–R3, R5–R8,
R11, R15–R27, R30, R32–R34), cobertura ≥ 80 % de lo cambiado, **cero
supervivientes** sin justificación escrita aceptada por el humano, y las
`MANUAL (humano)` con su comando exacto y su resultado real.

**Lo que hace que esto sea seguro**, de fuera adentro: la plataforma (sesión
del grupo de Posventa); el entorno (`dev`/`pro`); la ventana
`VOLCADO_HABILITADO`, **publicada cerrada**; el **ensayo previo guardado** de
la misma persona; la **confirmación** explícita; la **escritura anticipada**
del evento `enviado`; la **referencia `PVI-`**, que hace idempotente el
reintento **en Sigrid** (no depende de que nuestra base recuerde nada); la
transacción por parte de `sigrid-api` y sus dos llaves; y la guardia de red
de la suite.

## 1 · Lo que hay y se reutiliza

| Pieza | De | Cómo se usa |
|---|---|---|
| `POST /api/sigrid/partes-reclamacion` | `sigrid-api` F-006 (§8.9) | Ensayo (`commit:false`) y volcado (`commit:true`). Sin cambios |
| `candidatas_al_volcado`, `CandidataAlVolcado`, `huella_de_valores`, `estado_de`, `acciones_posibles`, `es_candidata`, `RevisionPort`, `revisiones_bandeja` | F-056 | Se **importan**; los cuatro primeros se **amplían** (§12), porque F-056 dejó ahí la costura (su design §3.2, §10) |
| `resolver_login_de_sigrid`, `postventa.usuarios_sigrid` | F-009 | Se **importa**; solo se ensancha el tipo de un parámetro (§8.4) |
| `construir_cliente_http`, `CORRECTOS`, `ENTORNOS_CON_CIERRE`, `ErrorDeSigrid`, `es_transitorio` | `infrastructure/sigrid/cliente.py` | Se **importan**, como hacen `graficos.py` y `catalogo_obra.py` |
| `select_usuario` | `infrastructure/sigrid/consultas.py` | Se **importa** para verificar el login |
| Validación de la obra y del correo | F-036 / F-056 | Se **importan** |
| `pruebas_bbdd_efimera.ps1` | F-036 | Las pruebas de base de la tabla nueva |

## 2 · Límite de servicio

**Frente a `sigrid-api`: cabe.** Crear el parte con sus cinco filas, reservar
códigos, resolver oficios e intervinientes contra `obrofc`, copiar propietario
y persona de la UPV y garantizar la idempotencia es de la pasarela, y ya lo
hace. Lo que es de este servicio es **qué** se vuelca (lo aprobado), **cómo
se traduce** la incidencia a los campos de §8.9, **quién** firma (`usu`) y
**qué se recuerda** de lo que pasó. Esta ficha **no pide ningún cambio** en
`sigrid-api`. Lo que la pasarela no hace —pasar a PTE, la urgencia— se queda
fuera: PTE lo hace **Posventa a mano** (Q-3) y la urgencia no se manda (D-10).

**Frente al front: partido (D-1, decisión del humano del 2026-10-07).**

| Ficha | Qué | Depende de |
|---|---|---|
| **F-059** (esta) | R1–R43: `services/postventa-api`, `16_volcados_sigrid.sql`, `infra/`, documentos | F-056 `done` y mergeada |
| **F-040** | R50–R59: `services/postventa-front` (panel en `bandeja.html`) y el cierre de los restos de F-040 en el portal | F-059 `done` y verificada; F-038 `done` |

F-040 conserva el id porque es la ficha que nombran los placeholders del
portal (`data-placeholder="F-040"`) y las guardias R28/R29/R62 de F-035,
igual que F-038 se quedó con el front al partir F-056. **Esta ficha no toca
`services/postventa-front/`.**

## 3 · El flujo

```
bandeja (F-056)       GET /api/volcado?obra=       → candidatas (aprobada, en_duda) y recuentos
      │
      ▼  quien llama trocea en grupos de N (R30)
POST /api/volcado/ensayo  ×k   → partes-reclamacion commit:false
      │                          → eventos «ensayo» guardados, ensayo_id, caduca en 30 min
      ▼  la persona lee el ensayo y confirma (F-040: segundo clic + nº de partes)
POST /api/volcado/volcar  ×k   (uno por ensayo, de uno en uno; F-040 para al primer fallo)
      │  1. puertas: entorno → VOLCADO_HABILITADO → configuración      (503)
      │  2. el ensayo: existe, misma obra, misma persona, < 30 min       (409)
      │  3. login de Sigrid de quien confirma (F-009)                    (409)
      │  4. TX PostgreSQL: FOR UPDATE + recomprobar + eventos «enviado»  (escritura anticipada)
      │  5. partes-reclamacion commit:true, UNA llamada, sin reintento
      │  6. eventos de resultado: creado / idempotente / rechazado / no_procesado / sin_respuesta
      ▼
bandeja: volcada (con su RS.., en SAT), en_duda, o aprobada con su motivo → corregir (editar) o reintentar
      ▼
Posventa pasa a PTE en Sigrid, a mano (Q-3)
```

**Reintentar** es repetir ensayo y volcado: la referencia es la misma
(`PVI-<incidencia_id>`), así que lo que ya esté en Sigrid vuelve
`idempotente` y queda `volcada`; lo que no, se crea.

## 4 · Estados y acciones

### 4.1 · Los seis estados (R1)

| Eventos de volcado | Última revisión | Estado |
|---|---|---|
| alguno `creado` o `idempotente` (cualquier modo) | — | **`volcada`** |
| si no, el último de modo `volcado` es `enviado` o `sin_respuesta` | — | **`en_duda`** |
| si no (ninguno, o el último es `rechazado`/`no_procesado`) | según F-056 | `nueva`, `editada`, `aprobada`, `descartada` |

`en_duda` solo puede venir de una `aprobada` (no se manda otra cosa) y
`volcada` de una `aprobada` o una `en_duda`. Un `idempotente` en un ensayo
también deja `volcada`: es Sigrid diciendo que el parte existe.

### 4.2 · Acciones (R2, R27; D-14)

| Desde \ acción | `editar` | `descartar` | `aprobar` | `recuperar` | ensayar y volcar |
|---|---|---|---|---|---|
| `nueva`, `editada` | sí | sí | sí | — | — |
| `aprobada` | sí | sí | — | — | **sí** |
| `descartada` | — | — | — | sí | — |
| **`en_duda`** | — | — | — | — | **sí** (reintento) |
| **`volcada`** | — | — | — | — | — (`ya_volcada`) |

Por qué `en_duda` no se edita: el parte puede existir ya en Sigrid con los
valores aprobados; editarlo en la bandeja dejaría una incidencia que dice una
cosa y un parte que dice otra. Por qué `volcada` no se descarta: anularla es
NO PROCEDE en Sigrid, a mano; descartarla aquí no la anularía allí.

Una `aprobada` cuyo último resultado fue `rechazado` (p. ej.
`oficio_no_esta_en_la_obra`) **sí** se edita: §8.9 garantiza que un parte
rechazado no dejó ninguna fila (su transacción se revierte), y si por
cualquier camino existiera, la misma referencia lo devolvería `idempotente` o
`referencia_en_conflicto`, nunca duplicado.

## 5 · Campo a campo contra §8.9 (R6)

| Campo de §8.9 | Valor | De dónde | Garantiza / decide |
|---|---|---|---|
| `database` | `SIGRID_BASE_DATOS` | Configuración (como el cierre) | Adaptador |
| `obra` | `obra_codigo` | La candidata | F-056 |
| `usu` | Login de quien pide | `resolver_login_de_sigrid` (F-009) | **F-059** (R8) |
| `commit` | `false` / `true`, explícito | Ensayo / volcado | **F-059** |
| `referencia_externa` | `PVI-` + `incidencia_id` (40) | `referencia_de(incidencia_id)` | **F-059** (R5) |
| `unidad_postventa` | `unidad_codigo` | La candidata | F-056 (de la obra al aprobar) |
| `descripcion` (1–128) | `descripcion` | La candidata | F-056 |
| `descripcion_larga` | `detalle`; **sin clave** si es nulo (§8.9 pone entonces la descripción, como el alta manual) | La candidata | **F-059** |
| `tipo` | **`"0002"` siempre** (PRIMER LISTADO POSTVENTA; Q-1). El `listado` de la bandeja **no** interviene | Constante `TIPO_RECLAMACION` | **F-059** |
| `clase` | **No se manda** (el alta manual la deja vacía; `rcp.rcpide = 0`) | — | **F-059** |
| `oficio` | `oficio_codigo` | La candidata | F-056 (resuelto, no ambiguo, de `obrofc` al aprobar) |
| `ubicacion` (≤ 48) | `ubicacion` | La candidata | F-056 (de la tipología de su unidad al aprobar; D-11) |
| `forma_comunicacion` | `1` («Escrita»), **explícito** aunque sea el defecto de §8.9 | Constante `FORMA_ESCRITA` | **F-059** |
| `intervinientes` | `[{oficio, proveedor, causante: false}]` con proveedor (Q-2); `[]` sin él (D-9) | La candidata | F-056 el par; **F-059** el resto |
| urgencia | **No existe en §8.9** y no se manda (D-10) | — | **F-059** |
| propietario, persona | **No se mandan**: los copia la pasarela de la UPV | — | `sigrid-api` |

`tipo` y `causante` se mandan **explícitos** aunque coincidan con el defecto
de §8.9: si la pasarela cambiara su defecto, este servicio no cambiaría de
comportamiento sin que nadie lo decidiera.

Con una incidencia por parte, **el oficio del parte y el del interviniente
coinciden siempre**: la pregunta 3 de `04_alta_incidencia_sigrid.md` («qué
oficio lleva el parte cuando hay varios intervinientes») no se da aquí; varios
intervinientes son de F-039. La 1 (tipo) la resolvió el humano (Q-1); la 2
(qué tablas escribe el alta) y la 4 (de dónde salen propietario y persona) las
cerró F-006 de `sigrid-api`.

**El estado del parte.** Nace en el estado inicial de la serie (**SAT**, sin
atender). La captura del alta manual lo enseña en PTE porque Posventa lo pasa
después; **Posventa lo seguirá pasando a PTE a mano en Sigrid** (Q-3), que es
cuando Sigrid crea las tareas y avisa al industrial. Este servicio no lo hace
y la documentación lo dice (R40).

## 6 · Tiempo, troceo, fallos y concurrencia

### 6.1 · El tiempo manda (R30, R31; D-6)

```
proxy de la Static Web App 45 s  >  front 40 s  >  llamada a partes-reclamacion SIGRID_TIMEOUT_S (35 s)
                                                  sigrid-api: presupuesto 150 s, balanceador 230 s
```

El que aprieta es el **proxy** (`docs/ARCHITECTURE.md`, «El presupuesto de 45
segundos»), no los 150 s de la pasarela. Medido en `sigrid-api` F-006: un
ensayo de 3 partes, 5,0 s; un alta real de 1 parte, 6,1 s (con las lecturas
comunes del lote). El coste por parte dentro de un lote **no está medido**.
Por eso `N` empieza en **5** y es una App Setting (1–50): se ajusta sin
desplegar cuando se mida el primer volcado real (Q-8, fuera de esta ficha).
El log de cada llamada lleva su duración y la media por parte (R31) para
poder hacerlo.

**Una obra = k llamadas de N**, que el front encadena de una en una. La
alternativa —una cola y un proceso en segundo plano— se descarta (§19): es
otro montaje, y con la idempotencia por referencia el troceo síncrono ya es
seguro.

### 6.2 · Qué pasa con cada fallo

| Dónde falla | Qué ha pasado en Sigrid | Qué guarda | Estado | Qué hace la persona |
|---|---|---|---|---|
| Puertas, cuerpo, ensayo no válido, login | Nada | Nada | igual | Lo que diga el mensaje |
| Escritura anticipada (base caída) | Nada | Nada (rollback) | igual | Reintentar |
| Un parte `rechazado` | Nada de ese parte (§8.9: su transacción se revierte) | `rechazado` + código | `aprobada` | Editar y reaprobar, o descartar |
| Un parte `no_procesado` | Nada de ese parte | `no_procesado` + código | `aprobada` | Reintentar |
| 400 de lote | Nada | `no_procesado` + código de lote | `aprobada` | Lo que diga el código (R24) |
| **Tiempo agotado / corte / 5xx / respuesta rara** | **No se sabe**: la pasarela sigue con el lote hasta 150 s | `sin_respuesta` | **`en_duda`** | Volver a ensayar y volcar: lo creado vuelve `idempotente` |
| Respondió y no se pudo guardar el resultado | Lo que diga la respuesta (perdida) | Solo `enviado` | **`en_duda`** | Igual: el ensayo lo encuentra `idempotente` |
| El proxy corta al front (> 45 s) | Lo que sea; la Function sigue | Lo que la Function termine | según la Function | Recargar el panel |
| La Function muere a medias | Desconocido | `enviado` | **`en_duda`** | Reintentar |

La fila clave es la del tiempo agotado: **en el cierre, un tiempo agotado
obliga a que una persona mire el ERP** (`docs/INTEGRACION.md` §3 bis, «la
escritura no se reintenta nunca»); **aquí no**, porque `sigrid-api` busca la
referencia **dentro** de la transacción y bajo `sp_getapplock` antes de
crear. El reintento sigue sin ser automático —lo pide una persona—, pero es
seguro y el mensaje lo dice (R23).

### 6.3 · Concurrencia (R29)

- **Edición contra volcado**: los dos bloquean la fila de
  `bandeja_incidencias` con `FOR UPDATE` en orden fijo (F-056 `registrar` y la
  escritura anticipada de R20). El que entra segundo ve el cambio del primero:
  o el volcado ve otra revisión (excluida), o la edición ve el `enviado` (409).
- **Dos personas volcando la misma obra**: cada una necesita su propio ensayo
  (R17). Si las dos llegan a mandar la misma incidencia, `sigrid-api` serializa
  por referencia y la segunda vuelve `idempotente`. En nuestra tabla quedan dos
  `enviado` y un `creado` más un `idempotente`: estado `volcada`. Sin bloqueos
  consultivos (servidor compartido).
- **El escritorio de Sigrid** dando de alta a la vez en la serie: lo resuelve
  `sigrid-api` (índice único y reintento de la transacción; `colision_de_clave`
  si se agota, reintentable).

## 7 · Dominio puro: `domain/models/volcado.py`

Sin red, sin base, sin reloj, sin `infrastructure/`.

```python
PREFIJO_REFERENCIA = "PVI-"
TIPO_RECLAMACION = "0002"            # PRIMER LISTADO POSTVENTA, siempre (Q-1)
FORMA_ESCRITA = 1
CAUSANTE = False                     # Q-2
CADUCIDAD_DEL_ENSAYO = timedelta(minutes=30)
MAX_PARTES_POR_LLAMADA = 50          # el tope de sigrid-api
PATRON_COD_PARTE = re.compile(r"^RS\d{2}\.\d{2}/\d{4}$")

class ModoVolcado(StrEnum): ENSAYO="ensayo"; VOLCADO="volcado"
class EstadoEvento(StrEnum):
    PREVISTO="previsto"; ENVIADO="enviado"; CREADO="creado"; IDEMPOTENTE="idempotente"
    RECHAZADO="rechazado"; NO_PROCESADO="no_procesado"; SIN_RESPUESTA="sin_respuesta"
class MotivoExclusion(StrEnum):
    NO_ES_DE_LA_BANDEJA=...; DE_OTRA_OBRA=...; NO_ES_CANDIDATA=...; YA_VOLCADA=...
    HUELLA_NO_COINCIDE=...; FUERA_DEL_ENSAYO=...; REVISION_DESACTUALIZADA=...
class MotivoEnsayoNoValido(StrEnum): NO_EXISTE=...; DE_OTRA_OBRA=...; DE_OTRA_PERSONA=...; CADUCADO=...

@dataclass(frozen=True)
class Interviniente: oficio: str; proveedor: str; causante: bool

@dataclass(frozen=True)
class ParteAVolcar:                   # exactamente lo de R6, por parte
    incidencia_id: UUID; revision_id: int; huella: str
    referencia_externa: str; unidad_postventa: str; descripcion: str
    descripcion_larga: str | None; tipo: str; oficio: str; ubicacion: str
    forma_comunicacion: int; intervinientes: tuple[Interviniente, ...]

@dataclass(frozen=True)
class ResultadoParte:                 # lo que se guarda de cada parte
    incidencia_id: UUID; referencia_externa: str; estado: EstadoEvento
    motivo: str | None; sigrid_ide: int | None; sigrid_cod: str | None

@dataclass(frozen=True)
class SituacionDeVolcado:             # lo que la base sabe de una incidencia
    volcada: ParteEnSigrid | None     # primer creado/idempotente: cod, ide, at, correo
    ultimo: UltimoEvento | None       # último de modo volcado: estado, motivo, at

@dataclass(frozen=True)
class EventoDeEnsayo: incidencia_id: UUID; revision_id: int; huella: str; estado: EstadoEvento
@dataclass(frozen=True)
class Ensayo: ensayo_id: UUID; obra_codigo: str; actor_oid: str; at_utc: datetime; eventos: tuple[EventoDeEnsayo, ...]
```

| Función | Responsabilidad | R |
|---|---|---|
| `referencia_de(incidencia_id) -> str` | `PVI-` + UUID canónico; la única | R5 |
| `parte_de(candidata) -> ParteAVolcar` | La tabla de §5: `tipo` = `TIPO_RECLAMACION` sin mirar `listado`; `detalle` nulo → `None`; sin proveedor → `()`; con él, `causante=CAUSANTE` | R6 |
| `cuerpo_de_lote(partes, *, obra, usu, commit, base) -> dict` | El JSON de §8.9, con `commit`, `tipo`, `forma_comunicacion` y `causante` explícitos y sin claves de más (`descripcion_larga` ausente si `None`) | R6 |
| `estado_de_volcado(situacion) -> EstadoVolcado | None` | §4.1 (`volcada`, `en_duda` o nada) | R1 |
| `huella_intacta(candidata) -> bool` | `huella_de_valores(valores) == huella` | R7 |
| `seleccionar_para_ensayo(pedidas, candidatas, situaciones, *, obra)` | Las que se mandan y las excluidas con motivo, en el orden pedido | R11 |
| `validar_ensayo(ensayo, *, obra, actor_oid, ahora) -> None` | `EnsayoNoValido(motivo)`; caduca en `>= 30 min` | R17 |
| `seleccionar_para_volcado(pedidas, ensayo, situaciones_actuales)` | R18 y R20: `previsto` en el ensayo, misma revisión, última revisión `aprobar`, no `volcada`, huella | R18, R20 |
| `interpretar_respuesta(mandados, datos) -> tuple[ResultadoParte, ...]` | Emparejar por `indice` y referencia; `sin_respuesta` ante cualquier incoherencia; nunca mira `committed` | R22 |
| `todos_sin_respuesta(mandados)` | R23 | R23 |
| `todos_no_procesados(mandados, codigo)` | R24 | R24 |
| `posibles_duplicados(resultados, situaciones)` | R26 | R26 |
| `clasificar_codigo_de_lote(codigo) -> "precondicion" | "rechazo"` | 503 frente a 409 | R14, R24 |
| `resumen_de(resultados, excluidas)` | Recuentos por estado | R12, R22 |
| `validar_partes_por_llamada(n) -> int` | 1..50 o `ConfiguracionDeVolcadoInvalida` | R30 |

Errores nuevos en `domain/models/errores.py`, traducidos en `function_app.py`:

| Error | HTTP | Cuerpo |
|---|---|---|
| `CuerpoDeVolcadoInvalido` | 400 | `{error, codigo: "peticion_invalida"}` |
| `VolcadoDeshabilitado` | 503 | `{error, codigo: "volcado_deshabilitado"}` |
| `ConfiguracionDeVolcadoInvalida` | 503 | `{error, codigo: "configuracion_de_volcado_invalida"}` |
| `EnsayoNoValido` | 409 | `{error, codigo: "ensayo_no_valido", motivo}` |
| `VolcadoRechazadoPorLaPasarela` | 409 / 503 | `{error, codigo: "volcado_rechazado_por_la_pasarela", codigo_pasarela}` |
| `EnsayoSinRespuesta` | 502 | `{error, codigo: "ensayo_sin_respuesta"}` |
| `VolcadoSinRespuesta` | 502 | `{error, codigo: "volcado_sin_respuesta", en_duda: [incidencia_id…]}` |
| `VolcadoSinTraza` | 500 | `{error, codigo: "volcado_sin_traza"}` |

Los de F-009 (`UsuarioSigridNoMapeado`, `UsuarioSigridInexistente`, 409) y
F-056 (`AccionNoPermitida`, `BandejaDemasiadoGrande`, 409) se reutilizan.

## 8 · Puertos y adaptadores

### 8.1 · `domain/ports/volcado.py`

```python
class VolcadoSigridPort(Protocol):
    def existe_usuario(self, *, login: str) -> bool: ...
    def ensayar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote: ...    # commit:false
    def volcar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote: ...     # commit:true

class RepositorioVolcadoPort(Protocol):
    def situaciones(self, *, incidencias: Sequence[UUID]) -> Mapping[UUID, SituacionDeVolcado]: ...
    def guardar_ensayo(self, *, ensayo_id: UUID, obra: str, resultados, partes, quien, ahora) -> None: ...
    def leer_ensayo(self, *, ensayo_id: UUID) -> Ensayo | None: ...
    def anotar_enviados(self, *, llamada_id, ensayo, pedidas, quien, ahora,
                        decidir: Callable[..., Seleccion]) -> Seleccion: ...      # R20, en UNA transacción
    def guardar_resultados(self, *, llamada_id, ensayo_id, resultados, quien, ahora) -> None: ...
```

`RespuestaDeLote` es `{tipo: "ok" | "lote_400" | "sin_respuesta", datos | codigo}`:
el adaptador **no interpreta** los partes (eso es `interpretar_respuesta`,
puro); solo distingue las tres familias y se queda, de un 400, con
`details.codigo` y nada más (R35).

`anotar_enviados` recibe la función pura de decisión: abre la transacción,
`SELECT … FROM postventa.bandeja_incidencias WHERE incidencia_id = ANY(%s)
ORDER BY incidencia_id FOR UPDATE`, lee la última revisión de cada una
(`revision_id`, `accion`, `huella_valores`) y su `SituacionDeVolcado`, llama a
`decidir`, inserta los `enviado` y hace `COMMIT`. Así la regla vive en el
dominio y el bloqueo en el adaptador.

### 8.2 · `infrastructure/sigrid/volcado.py` — `AdaptadorVolcadoSigridApi`

Calco de la **forma** de `graficos.py` y `catalogo_obra.py`: **importa** de
`cliente.py`, no copia.

- Constructor: `exigir_entorno_con_cierre(entorno)` (la misma lista `dev`,
  `pro`); guarda `escritura_habilitada: bool` (`VOLCADO_HABILITADO`).
- `volcar`: si `not escritura_habilitada` → `VolcadoDeshabilitado` **antes**
  de componer nada; si no, `POST RUTA_PARTES_RECLAMACION` con el cuerpo, que
  **tiene** que llevar `commit: True` (si no, `ValueError`: no se puede volcar
  con un cuerpo de ensayo). **Un intento**, sin `Retrying`.
- `ensayar`: exige `commit: False` en el cuerpo; **un intento** (el tiempo del
  proxy no admite tres).
- `existe_usuario`: `select_usuario` por `sql/read`, con los reintentos de
  lectura de siempre (`es_transitorio`).
- La clave, en la cabecera `x-functions-key`, nunca en la URL; ningún mensaje
  lleva cuerpo de respuesta, URL ni clave.
- `RUTA_PARTES_RECLAMACION = "/api/sigrid/partes-reclamacion"` vive **solo**
  aquí (R36, test de alcance).

### 8.3 · Fábricas, en `infrastructure/sigrid/fabrica.py` (se **añaden**)

| Fábrica | Puertas, en orden | Para |
|---|---|---|
| `construir_ensayador(ajustes)` | entorno → configuración → `N` válido | `ensayo` (y `existe_usuario`). **No** mira la ventana (D-4) |
| `construir_volcador(ajustes)` | entorno → **`VOLCADO_HABILITADO`** → configuración → `N` válido | `volcar` |

Las dos devuelven el mismo adaptador; la del volcado con
`escritura_habilitada=True`, la del ensayo con `False`, de modo que un
ensayador compuesto por error **no puede** volcar.
`infrastructure/persistencia/fabrica.py` añade `construir_volcados(ajustes)`.

### 8.4 · El login: un cambio de tipo en F-009, nada más

`resolver_login_de_sigrid(usuarios, erp, …)` declara `erp: ErpPort`, pero solo
llama a `erp.existe_usuario`. Se añade a `domain/ports/usuarios_sigrid.py` el
protocolo `VerificadorDeLoginPort` (solo `existe_usuario`) y se **cambia solo
la anotación** de ese parámetro. `ErpPort` y `VolcadoSigridPort` lo cumplen
los dos. Ni una línea de lógica de `paso_cierre.py` cambia, y sus tests
siguen intactos (R41). Alternativa descartada: construir el adaptador del
cierre para leer el login, que exige `CIERRE_HABILITADO`, otra ventana.

## 9 · SQL: `16_volcados_sigrid.sql`

Esquema `postventa`, siguiente a `15_revisiones_bandeja.sql` (F-056); lee de
`13_` y `15_`; solo `CREATE TABLE IF NOT EXISTS` y `CREATE INDEX IF NOT
EXISTS`.

```sql
CREATE TABLE IF NOT EXISTS postventa.volcados_sigrid (
    evento_id          bigserial   PRIMARY KEY,
    llamada_id         uuid        NOT NULL,
    modo               text        NOT NULL CHECK (modo IN ('ensayo', 'volcado')),
    ensayo_id          uuid,
    incidencia_id      uuid        NOT NULL
                       REFERENCES postventa.bandeja_incidencias (incidencia_id),
    revision_id        bigint      NOT NULL
                       REFERENCES postventa.revisiones_bandeja (revision_id),
    huella_valores     text        NOT NULL,
    obra_codigo        text        NOT NULL,
    referencia_externa text        NOT NULL
                       CHECK (referencia_externa LIKE 'PVI-%'
                              AND char_length(referencia_externa) <= 80),
    estado             text        NOT NULL CHECK (estado IN ('previsto', 'enviado',
                       'creado', 'idempotente', 'rechazado', 'no_procesado', 'sin_respuesta')),
    motivo_codigo      text        CHECK (char_length(motivo_codigo) BETWEEN 1 AND 64),
    sigrid_ide         bigint,
    sigrid_cod         text        CHECK (char_length(sigrid_cod) <= 24),
    actor_oid          text        NOT NULL,
    actor_correo       text        NOT NULL CHECK (char_length(actor_correo) BETWEEN 3 AND 254),
    at_utc             timestamptz NOT NULL,
    CHECK ((modo = 'ensayo') = (ensayo_id IS NULL)),
    CHECK (modo = 'volcado'
           OR estado IN ('previsto', 'idempotente', 'rechazado', 'no_procesado')),
    CHECK ((estado IN ('creado', 'idempotente'))
           = (sigrid_ide IS NOT NULL AND sigrid_cod IS NOT NULL)),
    CHECK (estado NOT IN ('rechazado', 'no_procesado') OR motivo_codigo IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_incidencia
    ON postventa.volcados_sigrid (incidencia_id, evento_id DESC);
CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_llamada
    ON postventa.volcados_sigrid (llamada_id);
```

Cabecera del `.sql`: append-only (manda el `evento_id`); el estado de la
incidencia no se guarda, se deriva (§4.1); **sin índice único** sobre
`creado` a propósito: si Sigrid llegara a crear dos partes, la segunda fila
tiene que **poder guardarse** y avisar (R26), no fallar tras haber escrito en
el ERP; `actor_oid` es el `oid` opaco y no se lee nunca; `actor_correo` es el
correo corporativo de quien ensaya o vuelca (D-8, como `revisado_correo` de
F-056), que solo devuelve `GET /api/revision` y que **nunca** va a un log; ni
descripciones, ni nombres, ni el login de Sigrid, ni el `motivo.mensaje` de la
pasarela; sin `ON DELETE CASCADE`; listas para F-048.

## 10 · Aplicación: `application/pipelines/volcado.py`

```python
def panel_de_volcado(obra, *, revision, volcados, partes_por_llamada) -> PanelDeVolcado
def ensayar(peticion: PeticionDeEnsayo, *, revision, volcados, usuarios, sigrid, ajustes_volcado, ahora) -> ResultadoDeEnsayo
def volcar(peticion: PeticionDeVolcado, *, revision, volcados, usuarios, sigrid, ajustes_volcado, ahora) -> ResultadoDeVolcado
```

`ensayar`: candidatas y situaciones (base) → `seleccionar_para_ensayo` → si no
queda ninguna, 200 sin llamar → login (Sigrid, lectura) → `parte_de` →
`cuerpo_de_lote(commit=False)` → `sigrid.ensayar` → `interpretar_respuesta`
(o error de R14) → `guardar_ensayo` → respuesta.

`volcar`: `leer_ensayo` + `validar_ensayo` (base, sin Sigrid) → login →
`anotar_enviados` (TX con `seleccionar_para_volcado`) → si no queda ninguna,
200 → `cuerpo_de_lote(commit=True)` con los `ParteAVolcar` **reconstruidos de
la candidata** (no del ensayo: la huella garantiza que son los mismos valores)
→ `sigrid.volcar` → `interpretar_respuesta` / `todos_sin_respuesta` /
`todos_no_procesados` → `posibles_duplicados` → `guardar_resultados` (si
falla, `VolcadoSinTraza`) → respuesta (o 502/409/503 **después** de guardar).

El orden **puertas → base → Sigrid lectura → base escritura → Sigrid
escritura → base** es el requisito: lo barato y lo que no escribe, primero.

## 11 · Borde HTTP: `interface_adapters/api/volcado.py` (el contrato de F-040)

Tres rutas nuevas en `function_app.py`, en `ANONYMOUS` (veintitrés):

| Ruta | Éxito | Errores |
|---|---|---|
| `GET /api/volcado?obra=` | 200 | 400; 409 `bandeja_demasiado_grande`; 503 base |
| `POST /api/volcado/ensayo` | 200 | 400; 409 login, `volcado_rechazado_por_la_pasarela`; 502; 503 entorno, configuración, base, `base_de_datos_no_permitida` |
| `POST /api/volcado/volcar` | 200 | 400; 409 `ensayo_no_valido`, login, pasarela; 502 `volcado_sin_respuesta`; 500 `volcado_sin_traza`; 503 `volcado_deshabilitado`, configuración, base |

Ensayo (datos ficticios):

```json
{"obra": "9901", "usuario_oid": "…", "usuario_correo": "persona@ejemplo.invalid",
 "incidencias": ["0b9c…", "51e2…"]}
```
```json
{"ensayo_id": "7f3a…", "obra": "9901", "caduca_at_utc": "2026-10-07T10:30:00+00:00",
 "resumen": {"previstos": 1, "idempotentes": 0, "rechazados": 1, "no_procesados": 0, "excluidas": 0},
 "partes": [
  {"incidencia_id": "0b9c…", "revision_id": 12, "referencia_externa": "PVI-0b9c…",
   "estado": "previsto", "motivo": null, "sigrid_cod": null,
   "envio": {"unidad_postventa": "9901.03VILLA 1.", "descripcion": "Ejemplo de descripción",
             "descripcion_larga": null, "tipo": "0002", "oficio": "0046", "ubicacion": "baño",
             "forma_comunicacion": 1,
             "intervinientes": [{"oficio": "0046", "proveedor": "EJ07", "causante": false}]}},
  {"incidencia_id": "51e2…", "revision_id": 15, "referencia_externa": "PVI-51e2…",
   "estado": "rechazado", "motivo": "oficio_no_esta_en_la_obra", "sigrid_cod": null, "envio": {"…": "…"}}],
 "excluidas": []}
```

Volcado:

```json
{"obra": "9901", "ensayo_id": "7f3a…", "usuario_oid": "…",
 "usuario_correo": "persona@ejemplo.invalid", "confirmado": true,
 "incidencias": [{"incidencia_id": "0b9c…", "revision_id": 12}]}
```
```json
{"llamada_id": "c41d…", "obra": "9901",
 "resumen": {"creados": 1, "idempotentes": 0, "rechazados": 0, "no_procesados": 0, "sin_respuesta": 0, "excluidas": 0},
 "partes": [{"incidencia_id": "0b9c…", "referencia_externa": "PVI-0b9c…",
             "estado": "creado", "motivo": null, "sigrid_cod": "RS99.10/0001"}],
 "excluidas": [], "avisos": []}
```

Se comprueba el cuerpo entero antes de construir nada (R9, R15). El log:
obra, `llamada_id`, modo, recuentos, duración; por parte, referencia,
estado, código y `sigrid_cod` (R34).

## 12 · Lo que cambia en F-056

Sobre el código de F-056 **tal como esté en `dev`** al empezar (base fija). Si
sus nombres difieren de su design, el implementer **para** y lo dice.

| Fichero | Cambio |
|---|---|
| `domain/models/revision.py` | `EstadoRevision` + `VOLCADA`, `EN_DUDA`; `FiltroEstado` + los dos y `ACTIVAS` sin `volcada` (D-7); `SituacionDeRevision` + `volcado: SituacionDeVolcado | None`; `estado_de` con la precedencia de §4.1 (usa `estado_de_volcado`); `acciones_posibles` → `()` para los dos; `es_candidata` → `aprobada` o `en_duda`; `resumen` con seis estados |
| `infrastructure/persistencia/sentencias_revision.py` | `listar`, `situacion` y `aprobadas` traen la situación de volcado con dos `LEFT JOIN LATERAL` sobre `volcados_sigrid` (el primer `creado`/`idempotente` por `evento_id`; el último de modo `volcado`) |
| `infrastructure/persistencia/repositorio_revision_pg.py` | `registrar`, dentro de su transacción y tras el `FOR UPDATE`, lee la situación de volcado de las filas bloqueadas y levanta `AccionNoPermitida` si es `volcada` o `en_duda` (R2) |
| `interface_adapters/api/revision.py` | El objeto `volcado` de cada incidencia (R4); los filtros nuevos |
| Tests de F-056 que fijan cuatro estados, `activas` o las acciones | Se **amplían**, sin quitar casos, citados en el informe (R41) |

`15_revisiones_bandeja.sql` **no** se toca: su `CHECK` de `accion` no admite
`volcar`, y F-056 lo dejó así a propósito («F-040 llevará el volcado en su
tabla»; hoy, esta ficha).

## 13 · Interruptor, ventana y despliegue (D-3, D-4)

- `config/settings.py`: `volcado_habilitado: bool` (`VOLCADO_HABILITADO`,
  **`False` por defecto**) y `volcado_partes_por_llamada: int`
  (`VOLCADO_PARTES_POR_LLAMADA`, 5), con el mismo patrón que
  `cierre_habilitado`. El rango de `N` se valida en la fábrica (503), no al
  cargar los ajustes: `/health` tiene que arrancar igual.
- **Por qué una ventana propia** y no `CIERRE_HABILITADO`: el gráfico compartió
  ventana con el cierre porque era su primera mitad (D-B de F-012); el volcado
  es otra operación, con otro volumen (decenas o cientos de altas de golpe) y
  se abre en otro momento. Una sola variable abriría el volcado masivo cada vez
  que alguien abriera la ventana para cerrar un parte.
- `infra/desplegar_backend.ps1`: `VOLCADO_HABILITADO=false` en `$ajustes`, en
  su línea, al lado de las otras dos, **en todos los despliegues** (D-3,
  aprobada: se publica **cerrada**, a diferencia de archivo y cierre; con o sin
  `-VentanasCerradas`). Cambiarla a «abierta por defecto» sería otra decisión
  expresa del humano. Y `VOLCADO_PARTES_POR_LLAMADA=5`.
- `infra/27_ventana_volcado.ps1`: calco de `19_ventana_escritura.ps1` sobre
  `VOLCADO_HABILITADO` (mirar / `-Abrir` con palabra / `-Cerrar` sin preguntar
  / releer). Su aviso de `-Abrir`: «abre la creación de partes en el ERP de
  producción para cualquier usuario del grupo con login de Sigrid; el
  siguiente despliegue la vuelve a cerrar».
- `infra/28_volcado_lectura_sigrid.ps1`: solo lectura sobre
  `08_lectura_sigrid_comun.ps1` (R39), para las fotos de antes y después.
- Se publica **desde un worktree limpio de `dev`**, nunca desde la carpeta de
  trabajo.

## 14 · Verificación en producción y vuelta atrás (R43)

Guion completo en `tasks.md` Bloque 6. Obra **0626** (Q-4), que es una obra
**en uso**; la UPV se elige en el momento (tipología con ubicaciones y un
oficio con proveedor en `obrofc`). Resumen:

1. Publicar: la ventana del volcado queda **cerrada** (D-3).
2. **Fotos de antes** con `28_volcado_lectura_sigrid.ps1`: el `MAX(cod)` de la
   serie del mes y cero partes con la referencia de prueba.
3. Fila de prueba («PRUEBA F-059 - ANULAR») importada en la 0626, en la UPV
   elegida, con ubicación de su tipología, y aprobada.
4. Con la ventana cerrada: `volcar` → **503**, y la foto no cambia. El ensayo →
   `previsto`, con el `envio` esperado (`tipo` `0002`, `causante: false`).
5. **Autorización expresa del humano** en el chat para **una** escritura;
   `27_ventana_volcado.ps1 -Abrir`; volcar esa incidencia → `creado` con su
   `RS…`; `27_ventana_volcado.ps1 -Cerrar` enseguida.
6. **Fotos de después**: **un** parte con la referencia, de la UPV elegida, con
   tipo `0002`, el oficio, la ubicación (por longitud), un interviniente sin
   Causante, en **SAT**. El humano lo abre en Sigrid. **No se pasa a PTE**:
   pasar a PTE crea tareas y avisa al industrial.
7. `GET /api/revision`: la incidencia `volcada` con su código y el correo de
   quien prueba; `editar` → 409. Un ensayo nuevo → excluida `ya_volcada`.
8. Application Insights: ningún `oid`, correo, login ni texto.

**Vuelta atrás.** Si algo sale mal en cualquier paso: `27_ventana_volcado.ps1
-Cerrar` (sin preguntar) y parar. Lo creado se localiza por su referencia
(`28_volcado_lectura_sigrid.ps1`, `RCPCLI LIKE 'PVI-%'`) y **se anula desde
la UI de Sigrid** (NO PROCEDE, **sin** correo), **nunca** con `DELETE` ni
`sql/write`. En la bandeja la incidencia queda `volcada` —lo estuvo— y no se
toca la tabla a mano. El parte de prueba se anula igual al terminar, salga
bien o mal. Si el defecto es del código, se redespliega el commit anterior
desde un worktree limpio con `-VentanasCerradas`. Recrear un parte anulado
queda fuera de alcance (Q-5).

## 15 · Datos personales y logs (R34, R35)

| Dato | Dónde va | Dónde no |
|---|---|---|
| Propietario y persona que reclama | Sigrid los copia de la UPV | No los mandamos, no los recibimos (se descartan las `filas`), no se guardan |
| Descripción, detalle, ubicación (texto de la propiedad) | Sigrid (`con.res`, `rcp.tex`, `rcp.resubi`); la respuesta del ensayo (`envio`), detrás de la sesión | Ni logs ni `volcados_sigrid` |
| Código del proveedor (para un autónomo, identifica a una persona) | Sigrid; `envio` | Logs; su nombre no viaja |
| `oid` de quien ensaya o vuelca | `volcados_sigrid.actor_oid` | Ninguna respuesta, ningún log, ninguna lectura |
| Correo de quien vuelca | `volcados_sigrid.actor_correo`; `GET /api/revision` (D-8) | Logs y mensajes de error |
| Login de Sigrid | El `usu` del cuerpo y la fila de `dbo.log` del ERP | Nuestra base (solo la correspondencia de F-009), logs, respuestas |
| `motivo.mensaje` de la pasarela | — | Ni se guarda ni se reenvía: solo el código |

`docs/INTEGRACION.md` §7 lo cuenta como **cuarta superficie**: lo que este
servicio escribe en el ERP sale de la bandeja y del texto de la propiedad.

## 16 · El front: es F-040

El panel de volcado en `bandeja.html`, el troceo en llamadas de `N`, la
confirmación (segundo clic y número de partes, D-12), la parada al primer
fallo, las etiquetas de `volcada` y `en_duda` en la lista de F-038 y el cierre
de los placeholders de F-040 en el portal son **F-040**
(`specs/F-040-volcado-sigrid/`). Esta ficha solo garantiza el contrato de §11
y el de R4.

## 17 · Ficheros

**A crear**, en `services/postventa-api/`:
`domain/models/volcado.py`, `domain/ports/volcado.py`,
`application/pipelines/volcado.py`,
`infrastructure/persistencia/sql/16_volcados_sigrid.sql`,
`infrastructure/persistencia/sentencias_volcado.py`,
`infrastructure/persistencia/repositorio_volcado_pg.py`,
`infrastructure/sigrid/volcado.py`, `interface_adapters/api/volcado.py`;
tests `test_f059_volcado_dominio.py`, `test_f059_estados.py`,
`test_f059_ddl.py`, `test_f059_repositorio_volcado.py`,
`test_f059_adaptador_volcado.py`, `test_f059_fabrica.py`,
`test_f059_pipeline_volcado.py`, `test_f059_volcado_http.py`,
`test_f059_alcance_cerrado.py`, `test_f059_scripts_infra.py`,
`test_f059_documentacion.py` y `tests_bbdd/tests/test_f059_bbdd_volcado.py`.
En `infra/`: `27_ventana_volcado.ps1`, `28_volcado_lectura_sigrid.ps1`.

**A modificar**: `domain/models/errores.py` (ocho errores);
`domain/ports/usuarios_sigrid.py` (`VerificadorDeLoginPort`);
`application/pipelines/paso_cierre.py` (**solo** la anotación de `erp` en
`resolver_login_de_sigrid`); `config/settings.py` (dos campos);
`infrastructure/sigrid/fabrica.py` (dos fábricas **añadidas**);
`infrastructure/persistencia/fabrica.py` (`construir_volcados`);
`function_app.py` (tres rutas, errores, cabecera: veintitrés anónimos); los
de F-056 de §12; los tests que enumeran rutas, `.sql`, tablas o variables
(`test_f010_endpoints_protegidos.py`, `test_f005_ddl_idempotente_texto.py`,
los de scripts de `infra/` si fijan las App Settings), **añadiendo sin
quitar** y citándolos; `infra/desplegar_backend.ps1`;
`docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, `docs/DESPLIEGUE.md`;
`.env.example` y `local.settings.json.example` (los dos nombres, con
placeholder); `azure-apps/postventa_incidencias.md` y la fila de F-040/F-059
de `azure-apps/sigrid_api.md` §10 (Q-6).

**No se toca**: `infrastructure/sigrid/cliente.py`, `escrituras.py`,
`graficos.py`, `consultas.py`, `catalogo_obra.py`, `ubicacion.py` (se
importan); la lógica de `paso_cierre.py`, `paso_grafico.py`,
`paso_archivo.py`; `interface_adapters/api/cerrar.py`, `adjuntar.py`,
`archivar.py`; `13_`, `14_` y `15_*.sql`; `bandeja.py`, `importar.py`,
`plantilla.py`, `catalogo_obra.py` de aplicación;
`config/plantilla_incidencias.yaml`; `infra/19_ventana_escritura.ps1`,
`22_ventana_archivo.ps1`; **`services/postventa-front/` entero** (es F-040);
y **nada** del repositorio `sigrid-api`.

## 18 · Tests

Sin red, base ni IA; nombres `test_f059_rN_…` (los números de requisito son
los de esta spec); obras `99NN`, correos `@ejemplo.invalid`, proveedores
«EJnn».

| R | Lo que fija además de lo obvio |
|---|---|
| R1–R3 | La tabla de §4.1 entera (precedencia: `volcada` gana a `en_duda` y a `descartada`); un `idempotente` de ensayo deja `volcada`; la tabla de §4.2; `es_candidata` |
| R2, R29 | `registrar` con una fila `enviado` entre el primer chequeo y el `FOR UPDATE` → 409 sin insertar (conexión falsa); y en `tests_bbdd`, dos conexiones |
| R4 | `volcado` en cada fila; seis estados en `resumen`; `activas` sin `volcada`; el correo sí y el `oid` no |
| R5 | 40 caracteres, minúsculas, prefijo exacto `PVI-`; la misma para la misma incidencia |
| R6 | El cuerpo **clave a clave** (`tipo` `"0002"` con `listado` `primero`, `segundo` y nulo; `causante: false`; sin `clase`; sin `descripcion_larga` con detalle nulo; `commit` siempre presente; `forma_comunicacion` 1; `[]` sin proveedor); ninguna clave de propietario, persona, urgencia, `ide`, `cod`, `emp`, `est`, `pos` |
| R7 | Un valor cambiado en la base con la huella vieja → excluida, no se manda |
| R8 | Sin login → 409 y el doble de la pasarela **no** recibe la llamada de lote |
| R9, R15 | Cada forma inválida (también `confirmado: "true"`, `1`, `commit` en el ensayo, ids repetidos, `N+1` ids) → 400 con fábricas que fallan si se llaman; el mensaje no lleva `oid` ni correo |
| R10, R16 | Ventana cerrada: ensayo sí, volcado 503 **sin** abrir la base (repositorio que falla si se usa); entorno `test`/`local` → 503; el adaptador con `escritura_habilitada=False` se niega a volcar aunque se llame directo; un cuerpo sin `commit:True` no se manda por `volcar` |
| R11–R14 | Cada exclusión; orden pedido; `filas` no aparece en ninguna respuesta ni registro; los `cod` provisionales tampoco; cada código de lote a su HTTP; 502 sin guardar |
| R17, R18 | Cada motivo de `ensayo_no_valido` (con 29:59 vale, con 30:00 no); fuera del ensayo; revisión distinta |
| R20 | La TX: `FOR UPDATE` en orden, re-chequeo, `enviado` insertados **antes** de la llamada (el doble de la pasarela comprueba que ya están), `COMMIT` antes de llamar; ninguno elegible → sin llamada |
| R21 | Un solo `post` incluso ante `httpx.TimeoutException` |
| R22 | Partes desordenados, de menos, de más, con referencia cambiada, `previsto` en commit, `creado` sin `cod` o con `cod` mal formado → `sin_respuesta`; `committed:false` con un `idempotente` es éxito |
| R23–R25 | Cada familia de fallo con lo que se guarda y el HTTP; `guardar_resultados` que falla → 500 y quedan `enviado` |
| R26 | El segundo `creado` con otro `ide` se guarda, sale en `avisos` y en un `log.error` |
| R30, R31 | `N` 0, 51, «cinco» → 503; un solo intento; la duración en el log |
| R32, R33 | La guarda real acepta el `.sql`; idempotente; `CHECK` = `Enum`; los cuatro `CHECK` de fila; ningún `UPDATE`/`DELETE`/`TRUNCATE`; ninguna lectura selecciona `actor_oid` |
| R34, R35 | `caplog` en todos los caminos: ni descripción, ni ubicación, ni `oid`, ni correo, ni login; el `mensaje` de la pasarela no aparece |
| R36, R37, R41, R42 | Alcance con la base fija: rutas nombradas; ninguna `sql/write` nueva; `VOLCADO_HABILITADO` no aparece en cierre/gráfico/archivo y estos no aparecen en volcado; «No se toca» sin cambios (front incluido); tests de F-009/F-012/F-036/F-053 sin diff |
| R38, R39 | Texto de los scripts: sin parámetros solo lee; `-Cerrar` sin palabra; `-Abrir` con palabra; relee; `28_` solo `sql/read` y sin columnas de nombres; `desplegar_backend.ps1` con `VOLCADO_HABILITADO=false` en su línea, con y sin `-VentanasCerradas` |
| R40 | Frases clave en los cuatro documentos, incluida «Posventa lo pasa a PTE a mano» |

## 19 · Riesgos y alternativas descartadas

1. **Dry-run y escritura en la misma llamada** (como el cierre): duplica el
   tiempo de cada trozo contra un proxy de 45 s y la persona confirmaría algo
   que no ha visto. Descartada (D-5).
2. **Una llamada por obra entera**: 160 partes de la 0677 no caben en 45 s;
   tampoco en el tope de 50 de la pasarela.
3. **Volcado asíncrono** (cola + proceso): otro montaje (`docs/DESPLIEGUE.md`
   §7), más piezas que vigilar; con referencia idempotente, el troceo síncrono
   basta. Se reconsidera si el primer volcado real enseña que `N` útil es 1–2.
4. **Guardar la referencia solo aquí** sin `RCPCLI`: no sobrevive a un corte
   (lo descartó F-006 de `sigrid-api`).
5. **Índice único sobre `creado`**: convertiría un duplicado en Sigrid en un
   fallo de nuestra base **después** de escribir en el ERP (§9).
6. **Revalidar la ubicación en el ensayo** con la tercera lectura de F-056:
   aprobar ya la comprobó, §8.9 la escribe sin validar y es texto libre en
   `rcp.resubi`; una lectura más por trozo a cambio de poco (D-11).
7. **Riesgo: el coste por parte no está medido**: `N`=5 conservador y
   ajustable; el log lo mide. El ajuste es Q-8, más adelante.
8. **Riesgo: `sigrid-api` sigue trabajando tras nuestro tiempo agotado** (su
   presupuesto es 150 s, el nuestro 35): partes creados sin que lo sepamos
   → `en_duda` → el reintento los recupera como `idempotente`. Aceptado y
   explicado en el mensaje.
9. **Riesgo: `en_duda` no se puede editar**: si el parte no llegó a crearse y
   hay que corregir algo, primero hay que reintentar (sale `previsto` o
   `rechazado`) y después editar. Es el precio de que bandeja y Sigrid no
   diverjan.
10. **Riesgo: la página de F-038 recibe estados que no conoce** entre el
    despliegue de esta ficha y el de F-040: los enseña con su código tal
    cual; solo pasa si alguien vuelca desde la consola (la verificación).
11. **Riesgo: los partes quedan en SAT** hasta que Posventa los pase a PTE
    (Q-3): si no lo hace, el industrial no se entera. Lo dicen la
    documentación y el panel de F-040.
12. **Riesgo: escritura real en una obra en uso** (0626) para la verificación:
    una sola, autorizada, sin pasar a PTE y anulada al terminar.

## 20 · Decisiones y respuestas (aprobadas por el humano el 2026-10-07)

| Id | Decisión |
|---|---|
| **D-1** | **Partir**: esta ficha (F-059) es el backend y va antes; F-040 se queda el front y el cierre de sus placeholders, bloqueada por F-059 |
| D-2 | El panel vive en `bandeja.html` (es de F-040) |
| **D-3** | `VOLCADO_HABILITADO` se publica **cerrada** en cada despliegue; se abre con `27_ventana_volcado.ps1` para cada volcado |
| **D-4** | El ensayo **no** exige la ventana (solo lee) |
| **D-5** | Ensayo previo obligatorio en el servidor: guardado, misma persona, < 30 min, solo lo `previsto` con la misma revisión |
| D-6 | Troceo en el front, de uno en uno; `N` = 5 por App Setting (1–50) |
| D-7 | `activas` sin `volcada` ni `descartada` |
| **D-8** | Se guarda el correo de quien ensaya y vuelca (nunca en logs) |
| D-9 | Sin proveedor, sin intervinientes |
| D-10 | La urgencia no se manda |
| D-11 | No se revalida la ubicación en el ensayo |
| D-12 | Confirmación con segundo clic y el número de partes (es de F-040) |
| D-13 | No se enseñan los `cod` provisionales del ensayo |
| D-14 | `en_duda` y `volcada` bloquean la revisión |
| **Q-1** | **Tipo `0002` siempre** (PRIMER LISTADO POSTVENTA, el defecto de §8.9); el `listado` de la bandeja no decide el tipo |
| **Q-2** | **`causante: false`** |
| **Q-3** | El parte queda en **SAT**; **Posventa lo pasa a PTE a mano** en Sigrid. Consta en la documentación y en la verificación |
| **Q-4** | Verificación en la **obra 0626**; la UPV se elige en el momento |
| Q-5 | Recrear un parte anulado: fuera de alcance |
| Q-6 | Este trabajo actualiza la fila de consumidores de `azure-apps/sigrid_api.md` (el líder, al desplegar) |
| Q-7 | Puede volcar cualquiera de `posventa-usuarios` con login de Sigrid, por ahora |
| Q-8 | El primer volcado masivo de la 0677 y el ajuste de `N`: más adelante, fuera de esta ficha |
