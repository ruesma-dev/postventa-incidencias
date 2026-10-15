<!-- specs/F-059-volcado-sigrid-backend/design.md -->
# F-059 · Volcado a Sigrid en el backend — Diseño técnico

> **Aprobado por el humano el 2026-10-07** (decisiones y respuestas en §20).
> Es el **tramo A** de la spec conjunta de F-040, partida por D-1: esta ficha
> es el backend (R1–R43) y va **antes**; el front (R50–R59) es **F-040**
> (`specs/F-040-volcado-sigrid/`), que consume el contrato de §11 y está
> bloqueada por esta.
>
> **Conciliada con dev 2d2efd7 el 2026-10-15**: nombres reales de F-056,
> convivencia con F-060, cuentas y tests ajenos en **§21**; resumen en §20.

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
| `candidatas_al_volcado` (`application/pipelines/revision.py`), `CandidataAlVolcado`, `huella_de_valores`, `estado_de`, `acciones_posibles`, `es_candidata`, `resumen`, `RevisionPort`, `revisiones_bandeja` | F-056 | Se **importan**. Se **amplían** (§12) `EstadoRevision`, `FiltroEstado`, `SituacionDeRevision`, `estado_de`, `acciones_posibles`, `es_candidata` y el filtro de `paginar`, porque F-056 dejó ahí la costura (su design §3.2, §10). `CandidataAlVolcado`, `huella_de_valores` y `RevisionPort` (siete operaciones desde F-060) **no** cambian (§21.2) |
| `normalizar_ubicaciones`, `registrar_lote`, `ESTADOS_NORMALIZABLES` | F-060 | **Ni se usan ni se tocan**; conviven con los estados nuevos sin cambios (§21.5) |
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

Por lo mismo, la **última revisión** de una `volcada` o una `en_duda` es
siempre un `aprobar`: ninguna acción la sucede (R2). Eso es lo que deja fuera
a las revisiones del sistema de F-060, que solo escriben sobre `nueva` y
`editada` (§21.5).

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

«La candidata» es la `CandidataAlVolcado` de F-056 tal como está en `dev`:
`incidencia_id`, `obra_codigo`, `revision_id`, `huella` y `aprobada_at_utc`
arriba, y los trece valores en **`candidata.valores`** (`ValoresIncidencia`:
`unidad_codigo`, `descripcion`, `detalle`, `oficio_codigo`, `ubicacion`,
`proveedor_codigo`…). Su `__post_init__` ya exige oficio resuelto, ubicación
recortada de 48 como mucho y ningún ambiguo.

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
    ultimo: UltimoEvento | None       # último de modo volcado: estado, motivo, at, correo (R4: volcado_por)

@dataclass(frozen=True)
class EventoDeEnsayo: incidencia_id: UUID; revision_id: int; huella: str; estado: EstadoEvento
@dataclass(frozen=True)
class Ensayo: ensayo_id: UUID; obra_codigo: str; actor_oid: str; at_utc: datetime; eventos: tuple[EventoDeEnsayo, ...]
```

**Dónde vive cada tipo (conciliación 2026-10-15).** `domain/models/revision.py`
(F-056) necesita `SituacionDeVolcado` y `estado_de_volcado` para su
`estado_de`, y `volcado.py` necesita `CandidataAlVolcado` y
`huella_de_valores` de `revision.py`: en un solo módulo sería una importación
circular. Por eso `ModoVolcado`, `EstadoEvento`, `ParteEnSigrid`,
`UltimoEvento`, `SituacionDeVolcado` y `estado_de_volcado` van en un módulo
**hoja**, `domain/models/situacion_volcado.py`, que no importa nada de
`revision.py`; `revision.py` y `volcado.py` importan de él, y `volcado.py`
reexporta lo que necesite. El resto de este apartado vive en `volcado.py`.

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

El bloqueo es **la misma sentencia** `select_bloquear` de
`sentencias_revision.py` (F-056), importada y sin cambiarla: así
`anotar_enviados`, `registrar` (F-056) y `registrar_lote` (F-060) bloquean las
mismas filas en el mismo orden y no pueden interbloquearse (§21.5). La última
revisión con su `accion` y su huella se lee con una sentencia propia de
`sentencias_volcado.py` (`select_ultimas_revisiones` de F-056 solo devuelve el
`revision_id` y no se toca).

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
EXISTS`. El número **16 sigue libre** en `dev` 2d2efd7: F-060 no añadió DDL
(su D-4) y ninguna otra rama ni spec lo reserva (§21.1). Los tipos casan con
F-056: `revisiones_bandeja.revision_id` es `bigserial` y
`bandeja_incidencias.incidencia_id`, `uuid`.

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

Tres rutas nuevas en `function_app.py`, en `ANONYMOUS` (**veinticuatro**: las
veintiuna de `dev` 2d2efd7 —F-056 llevó la cuenta a veinte y F-060, con
`revision/normalizar`, a veintiuna— más estas tres). `function_app.py` solo
importa de `interface_adapters/api/volcado.py`, nunca de
`infrastructure.sigrid.escrituras` ni `graficos` (lo vigila
`test_f056_r39_…`), y ninguna importación nueva carga `openpyxl`, `pymupdf`
ni `google.genai` al importar `function_app` (M-3 de F-060,
`test_f060_importacion_diferida.py`). Los errores van en una traducción
propia; `_error_de_revision` (F-056, que también usa F-060) no cambia.

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

Sobre el código de F-056 **tal como está en `dev` 2d2efd7** (base fija), con
F-060 ya encima. Los nombres reales se comprobaron en la conciliación (§21.2):
el implementer **no** tiene que parar por ellos; sí si encuentra alguno que
difiera de §21.2.

| Fichero | Cambio |
|---|---|
| `domain/models/revision.py` | `EstadoRevision` + `VOLCADA`, `EN_DUDA`; `FiltroEstado` + los dos y `ACTIVAS` sin `volcada` (D-7; el filtro está en `_pasa`); `SituacionDeRevision` + `volcado: SituacionDeVolcado | None = None` como **último campo y con valor por defecto**, para que los tests de F-056 y F-060 y `tests/utiles_revision.py`, que la construyen sin él, sigan valiendo; `estado_de` con la precedencia de §4.1 (usa `estado_de_volcado`, de `situacion_volcado.py`, §7); `_PERMITIDAS` → `()` para los dos (lo devuelve `acciones_posibles`); `es_candidata` → `aprobada` o `en_duda` (y con ello `candidata_de` rechaza una `volcada`); `resumen` con seis estados (sale solo: recorre `EstadoRevision`) |
| `infrastructure/persistencia/sentencias_revision.py` | `_select_situaciones`, la consulta común de `select_situaciones_de_obra` (`listar`), `select_situacion` (`situacion`) y `select_aprobadas` (`aprobadas`), gana dos `LEFT JOIN LATERAL` sobre `volcados_sigrid` (el primer `creado`/`idempotente` por `evento_id`; el último de modo `volcado`, con su `actor_correo` y **nunca** `actor_oid`); `fila_a_situacion` llena `SituacionDeRevision.volcado` (la de la original de una duplicada queda `None`). `select_bloquear`, `select_ultimas_revisiones` e `insert_revision` **no** cambian: las comparte `registrar_lote` de F-060 |
| `infrastructure/persistencia/repositorio_revision_pg.py` | `_registrar` (el paso de `registrar`), tras `select_bloquear` y dentro de su transacción, lee con una sentencia nueva la situación de volcado de la incidencia bloqueada y levanta `AccionNoPermitida(estado=…, acciones=())` si es `volcada` o `en_duda` (R2), antes de la comprobación de frescura. `aprobadas` filtra con `es_candidata` **antes** de `candidata_de`: con la situación de volcado en la fila, una `volcada` (última revisión `aprobar`) haría fallar `candidata_de`; así devuelve `aprobada` y `en_duda` (R3). `registrar_lote` y `_registrar_lote` (F-060) **no** cambian (§21.5) |
| `interface_adapters/api/revision.py` | `_fila`, el objeto `volcado` de cada incidencia (R4): `_fila` es común al listado de `GET /api/revision` y a la respuesta de `POST /api/revision/acciones`, y la clave sale **en las dos** (F-2 (a), decisión del humano del 2026-10-15, §20); `_fila` no se parametriza ni se duplica, y el historial no cambia (no usa `_fila`); `_filtro`, los dos valores nuevos y su mensaje. **`listar_revision` no cambia** (es pieza de F-060: su medición) y no se añade ninguna importación de `infrastructure.sigrid` (`test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036`) |
| `RevisionPort` (`domain/ports/revision.py`) | **Nada**: sigue con sus siete operaciones (`test_f056_r34_…`, ampliado por F-060). Lo nuevo de F-059 va en `RepositorioVolcadoPort` (§8.1) |
| Tests de F-056 que fijan cuatro estados, `activas` o las acciones | Se **amplían**, sin quitar casos, citados en el informe (R41); lista en §21.3 |

Lo que estas piezas de F-056 **no pueden ganar**, porque lo vigilan los
controles de `test_f056_alcance_cerrado.py` que no dependen de `git` (y que no
se tocan): la palabra «habilitado», una ruta de escritura de `sigrid-api`,
`UPDATE`/`DELETE`/`TRUNCATE`, DDL, una lectura del entorno (`environ`,
`getenv`) o una importación de `infrastructure.sigrid` nueva (§21.4).

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
- Los números **27 y 28 siguen libres** en `dev` 2d2efd7 (el último script
  numerado es `26_catalogos_plantilla_sigrid.ps1`, y luego `90_`), igual que
  `VOLCADO_HABILITADO` y `VOLCADO_PARTES_POR_LLAMADA`, que no aparecen en
  ningún fichero del servicio ni de `infra/` (§21.1).
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
`domain/models/situacion_volcado.py` (el módulo hoja de §7),
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
`test_f059_documentacion.py` y `tests_bbdd/tests/test_f059_bbdd_volcado.py`;
si hacen falta, los dobles de F-059 en un `tests/utiles_volcado.py` propio
(`tests/utiles_revision.py` es de F-056 y no se toca: su `RevisionEnMemoria`
se envuelve o se hereda, no se cambia).
En `infra/`: `27_ventana_volcado.ps1`, `28_volcado_lectura_sigrid.ps1`.

**A modificar**: `domain/models/errores.py` (ocho errores);
`domain/ports/usuarios_sigrid.py` (`VerificadorDeLoginPort`);
`application/pipelines/paso_cierre.py` (**solo** la anotación de `erp` en
`resolver_login_de_sigrid`); `config/settings.py` (dos campos);
`infrastructure/sigrid/fabrica.py` (dos fábricas **añadidas**);
`infrastructure/persistencia/fabrica.py` (`construir_volcados`);
`function_app.py` (tres rutas, errores, cabecera: veinticuatro anónimos); los
de F-056 de §12; los tests que enumeran rutas, `.sql`, tablas o variables
(`test_f010_endpoints_protegidos.py`, `test_f005_ddl_idempotente_texto.py`,
los de scripts de `infra/` si fijan las App Settings), **añadiendo sin
quitar** y citándolos; los demás tests ajenos que el plan rompe, los de las
excepciones de R41 (inventario de §21.3; F-1 (a), decisión del humano del
2026-10-15), cada uno solo en su función declarada;
`infra/desplegar_backend.ps1`;
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
y **nada** del repositorio `sigrid-api`. Y lo de **F-060** (§21.5):
`domain/models/normalizacion.py`, `interface_adapters/api/normalizacion.py`,
`interface_adapters/api/tiempos.py`, `interface_adapters/api/importar.py`,
`normalizar_ubicaciones` y `ResultadoNormalizacion` de
`application/pipelines/revision.py`, `ResultadoDelLote` y
`RevisionPort.registrar_lote`, `RepositorioRevisionPostgres.registrar_lote` y
`_registrar_lote`, `listar_revision`, y `revision_normalizar` y
`_error_de_revision` de `function_app.py`; `select_bloquear`,
`select_ultimas_revisiones` e `insert_revision` de `sentencias_revision.py`;
y `tests/utiles_revision.py`.

## 18 · Tests

Sin red, base ni IA; nombres `test_f059_rN_…` (los números de requisito son
los de esta spec); obras `99NN`, correos `@ejemplo.invalid`, proveedores
«EJnn».

| R | Lo que fija además de lo obvio |
|---|---|
| R1–R3 | La tabla de §4.1 entera (precedencia: `volcada` gana a `en_duda` y a `descartada`); un `idempotente` de ensayo deja `volcada`; la tabla de §4.2; `es_candidata` |
| R2, R29 | `registrar` con una fila `enviado` entre el primer chequeo y el `FOR UPDATE` → 409 sin insertar (conexión falsa); y en `tests_bbdd`, dos conexiones |
| R4 | `volcado` en cada fila del listado **y** en la incidencia de la respuesta de `POST /api/revision/acciones` (F-2 (a)), con la misma forma; el historial sin cambios; seis estados en `resumen`; `activas` sin `volcada`; el correo sí y el `oid` no |
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
| R36, R37, R41, R42 | Alcance con la base fija: rutas nombradas; ninguna `sql/write` nueva; `VOLCADO_HABILITADO` no aparece en cierre/gráfico/archivo y estos no aparecen en volcado; «No se toca» sin cambios (front incluido); tests de F-009 sin diff; los de las excepciones de R41 (F-1 (a)) solo en su función o constante declarada y sin perder ninguna aserción; ningún otro test ajeno tocado |
| R38, R39 | Texto de los scripts: sin parámetros solo lee; `-Cerrar` sin palabra; `-Abrir` con palabra; relee; `28_` solo `sql/read` y sin columnas de nombres; `desplegar_backend.ps1` con `VOLCADO_HABILITADO=false` en su línea, con y sin `-VentanasCerradas` |
| R40 | Frases clave en los cuatro documentos, incluida «Posventa lo pasa a PTE a mano» |
| R1–R3 con F-060 (§21.5) | `planificar_normalizacion` de F-060, **importada y sin tocarla**, con una `volcada` y una `en_duda` cuya ubicación sería normalizable → ninguna revisión y las dos en `no_editables`; `validar_quien` rechaza `sistema:normalizar_ubicacion` como quien ensaya o vuelca (R9, R15); y en `tests_bbdd`, `registrar_lote` y `anotar_enviados` sobre la misma incidencia con dos conexiones se serializan sin interbloqueo |
| R4, `SituacionDeRevision` | Construida sin `volcado` sigue valiendo (`None`): los tests de F-056 y F-060 no cambian por eso; `aprobadas` con una `volcada` en la obra no falla y no la devuelve |

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
13. **Riesgo (dato nuevo, F-060/F-061): picos de 4–8 s en una sola lectura de
    `sigrid-api`**, también en procesos calientes (`progress/impl_F-060.md`,
    M1 y M2; ficha F-061). El ensayo y el volcado hacen una lectura (el login)
    antes de la llamada de lote: un pico ahí más una llamada lenta acercan la
    petición a los 45 s del proxy. No cambia ninguna decisión: el corte del
    proxy ya está en §6.2 (la Function sigue y lo que no conste queda
    `en_duda`), `N` es ajustable (Q-8) y el log de R31 lo mide.
14. **Riesgo: el listado de la revisión, que F-060 midió lento**, gana dos
    `LEFT JOIN LATERAL` sobre `volcados_sigrid` (§12). Van por
    `ix_volcados_sigrid_incidencia` y en la misma consulta (ninguna conexión ni
    lectura más por petición: `test_f056_r46_…` sigue igual); la traza «F-060
    tiempos del listado» lo enseñará en `bandeja.listar`, y F-061 lo vigila.

## 20 · Decisiones y respuestas (aprobadas por el humano el 2026-10-07)

> **Conciliada con dev 2d2efd7 el 2026-10-15** (spec-author, a petición del
> líder; detalle en §21 y en `progress/spec_F-059.md`). Ninguna decisión de
> esta tabla se reabre. Se ajustaron, como **mecánicos**: la cuenta de
> anónimos (21 → **24**); los nombres reales de F-056 (`_select_situaciones`,
> `_registrar`, `_fila`, `_filtro`, `candidata.valores`…); el módulo hoja
> `situacion_volcado.py` para no importar en círculo; `SituacionDeRevision.volcado`
> con valor por defecto; `aprobadas` filtrando con `es_candidata`; el bloqueo
> con la misma `select_bloquear` que F-056 y F-060; la convivencia con F-060
> (sus revisiones del sistema no pueden tocar una `volcada` ni una `en_duda`);
> la base fija `2d2efd7`; los números 16, 27 y 28, libres; §8.9 de
> `sigrid-api`, sin cambios desde el 2026-10-07; y dos riesgos nuevos con
> datos de F-060 (§19.13, §19.14). La conciliación abrió **dos de fondo**
> (§21.6), que el humano decidió el mismo día (filas F-1 y F-2 al final de la
> tabla).

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
| **F-1** | **Decisión del humano del 2026-10-15, literal: «a en las 2»** → opción (a). R41 gana el bloque «Excepciones, ampliando sin relajar» con la lista test a test de §21.3 (como R45 de F-056); cada una declarada **función a función** en `test_f059_alcance_cerrado.py` (T16), que vigila que no se pierde ninguna aserción |
| **F-2** | **Decisión del humano del 2026-10-15, literal: «a en las 2»** → opción (a). El objeto `volcado` va en las **dos** respuestas que serializa `_fila`: el listado de `GET /api/revision` y la respuesta de `POST /api/revision/acciones` (R4, §12) |

## 21 · Conciliación con `dev` 2d2efd7 (2026-10-15)

La spec se escribió el 2026-10-07 sobre `dev` f86d639, **antes** de que se
implementaran F-056 (`done` el 2026-10-09) y F-060 (`done` el 2026-10-14).
Esta sección contrasta lo supuesto con el código real de la base fija.

### 21.1 · Qué hay en `dev` que la spec no veía

| Pieza | Estado en 2d2efd7 | Efecto en F-059 |
|---|---|---|
| Rutas anónimas | **Veintiuna** (F-056 las llevó a veinte; F-060 añadió `revision/normalizar`) | Con las tres de F-059, **veinticuatro** (R42, §11) |
| `RevisionPort` | **Siete** operaciones (F-060 añadió `registrar_lote`; `test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5` las fija) | F-059 **no** añade ninguna: lo suyo va en `RepositorioVolcadoPort` |
| Revisiones del sistema (F-060) | `editar` con `oid` y correo `sistema:normalizar_ubicacion`, tras cada importación (mejor esfuerzo) y con `POST /api/revision/normalizar` | Conviven sin cambios (§21.5) |
| Medición del listado (F-060) | `listar_revision` envuelve los puertos en un cronómetro; una línea «F-060 tiempos del listado» | `listar_revision` no se toca; el riesgo de las `LATERAL`, en §19.14 |
| Importación diferida (F-060 M-3) | Importar `function_app` no carga `openpyxl`, `pymupdf` ni `google.genai` | Los módulos nuevos tampoco (§11) |
| DDL | El último es `15_revisiones_bandeja.sql`; F-060 no añadió ninguno | **`16_volcados_sigrid.sql` sigue libre** |
| `infra/` | El último numerado es `26_…`; luego `90_…` | **`27_` y `28_` libres** |
| Variables | Ni `VOLCADO_HABILITADO` ni `VOLCADO_PARTES_POR_LLAMADA` existen | Libres |
| `azure-apps/sigrid_api.md` §8.9 | Sin cambios desde el 2026-10-07 (los dos commits posteriores al fichero son de albaranes y de facturas y no tocan §8.9); la fila de consumidores de §10 sigue diciendo «F-040» | El contrato de §5 vale tal cual; Q-6 sigue pendiente para el despliegue |
| Otras ramas (F-038, F-040, F-057, F-058) | Ninguna reserva el 16, el 27 ni el 28 | — |

### 21.2 · Los nombres de F-056, como quedaron

| La spec decía | En el código de `dev` |
|---|---|
| `candidatas_al_volcado(obra)` | `application/pipelines/revision.py::candidatas_al_volcado(obra_codigo, *, revision)`, que devuelve `RevisionPort.aprobadas` |
| Los campos de la candidata | `CandidataAlVolcado(incidencia_id, obra_codigo, valores, huella, aprobada_at_utc, revision_id)`; los trece valores en `valores` (`ValoresIncidencia`) |
| `estado_de`, `acciones_posibles`, `es_candidata`, `resumen` | Los mismos, en `domain/models/revision.py`; las acciones salen del diccionario `_PERMITIDAS`; el filtro de estado está en `_pasa` (lo usa `paginar`); `candidata_de` exige `es_candidata` |
| Las sentencias de «`listar`, `situacion` y `aprobadas`» | Una consulta común, `_select_situaciones`, para `select_situaciones_de_obra`, `select_situacion` y `select_aprobadas`; la fila se parte con `fila_a_situacion` |
| El bloqueo de `registrar` | `select_bloquear` (`FOR UPDATE`, `ORDER BY incidencia_id`), en `RepositorioRevisionPostgres._registrar`; también la usa `_registrar_lote` (F-060) |
| El borde de la revisión | `interface_adapters/api/revision.py`: `_fila` (la incidencia serializada), `_filtro`, `listar_revision` (pieza de F-060) |
| Los errores reutilizados | `AccionNoPermitida(motivo, *, estado, acciones)`, `BandejaDemasiadoGrande(motivo, *, total)`, `RevisionDesactualizada`, `PeticionDeRevisionInvalida`, `PersistenciaNoDisponible`, como se suponía; en `function_app.py`, `_error_de_revision` |
| La validación de quien | `validar_quien(oid, correo)`; desde F-060, un correo sin `@` no vale (el literal del sistema no se puede enviar) |
| F-009 | `resolver_login_de_sigrid(usuarios, erp, *, usuario_oid, correo, ahora)` en `paso_cierre.py`, con `erp: ErpPort`; `RepositorioUsuariosSigridPort` en `domain/ports/usuarios_sigrid.py` |
| El cliente de Sigrid | `construir_cliente_http`, `CORRECTOS`, `ENTORNOS_CON_CIERRE`, `ErrorDeSigrid`, `es_transitorio`, `exigir_entorno_con_cierre` en `cliente.py`; `select_usuario` en `consultas.py`; `_exigir_configuracion` en `fabrica.py`; `sigrid_timeout_s` = 35 por defecto |
| La tabla | `postventa.revisiones_bandeja`: `revision_id bigserial`, `revisado_por` (el `oid`), `revisado_correo`, `huella_valores` |

Ningún nombre obliga a cambiar una decisión. Lo que sí cambió el diseño
(como mecánico) está en §7 (módulo hoja), §8.1 (bloqueo) y §12.

### 21.3 · Tests ajenos que el plan aprobado obliga a ampliar (inventario)

Comprobado leyendo cada test contra `dev` 2d2efd7. Todos se amplían **sin
relajar** (la cifra o el fichero vigente en `in`, el anterior en `not in`) y
se declaran función a función en `test_f059_alcance_cerrado.py`, con el
criterio que el humano aprobó en F-056 (R45) y que el líder aplicó en F-060
(§12). **Decidido: F-1 (a)** (humano, 2026-10-15): es la lista de excepciones
de R41.

**A · El `16_…sql`** (controles que no dependen de `git`; se ponen rojos en
T5):

| Test | Qué fija | De |
|---|---|---|
| `test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden` | La lista entera de `.sql` | F-005 (ya en la spec) |
| `test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_de_los_de_f036` | `nombres[-1] == 15_…` | F-056 (ya en la spec) |
| `test_f028_ddl_historico.py::test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo` | La cola tras el `11_` | F-028 |
| `test_f030_veredicto_persistido.py::test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo` | `DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056` | F-030 |
| `test_f031_alcance_cerrado.py::test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo` | Ídem | F-031 |
| `test_f032_alcance_cerrado.py::test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo` | Ídem | F-032 |
| `test_f033_alcance_cerrado.py::test_f033_no_hay_ni_un_fichero_de_ddl_nuevo` | Ídem | F-033 |
| `test_f034_alcance_cerrado.py::test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo` | Ídem | F-034 |
| `test_f036_ddl.py::test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden` | Lo que va tras el `11_`: `12_`…`15_` | **F-036 (R41 lo da por intocable)** |
| `test_f056_alcance_cerrado.py::test_f056_r12_solo_15_declara_una_columna_de_correo` | Solo el `15_` tiene una columna de correo; el `16_` trae `actor_correo` (D-8) | F-056 (fuera de «cuatro estados o acciones») |
| `test_f060_alcance_cerrado.py::test_f060_r37_los_sql_son_los_quince_de_antes` | Los quince `.sql`, «ni un `16_`» | F-060 |

**B · La cuenta de anónimos y la cabecera de `INTEGRACION.md`** (rojos en
T15 y T20):

| Test | Qué fija | De |
|---|---|---|
| `test_f010_endpoints_protegidos.py` (`ENDPOINTS`, `test_f010_r32_…`) | Las veintiuna rutas | F-010 (ya en la spec) |
| `test_f012_documentacion.py` (`NUMERALES`, `test_f012_r68_integracion_declara_el_endpoint_nuevo_que_exponemos`) | `NUMERALES` hasta 21 | **F-012 (R41 lo da por intocable)** |
| `test_f053_documentacion.py` (`CUENTA_VIGENTE`, `test_f053_t6_…`) | «Los veintiuno quedan en nivel» | **F-053 (R41 lo da por intocable)** |
| `test_f019_documentacion.py::test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints` | «Los veintiuno» en `in` | F-019 |
| `test_f056_documentacion.py::test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas` | «Los veintiuno» | F-056 |
| `test_f060_documentacion.py::test_f060_r43_la_seccion_ocho_dice_la_importacion_la_traza_y_la_cuenta` | «Los veintiuno» | F-060 |
| `test_f060_documentacion.py::test_f060_r43_la_cabecera_dice_que_f060_lo_toco_y_cuando` | «Última feature que lo tocó: F-060» y «Fecha: 2026-10-14.» | F-060: pasaría a exigir una cabecera bien formada que no retroceda, con F-060 y su despliegue constando (lo mismo que F-060 hizo con el de F-056) |

**C · Los estados y la fila de F-056** (rojos en T2, T6 y T15; R41 ya los
admite si «fijan cuatro estados o las acciones», salvo los marcados):

| Test | Qué fija |
|---|---|
| `test_f056_paginacion.py` (el `resumen` con cuatro `por_estado`; la lista exacta de `FiltroEstado`) | Cuatro estados |
| `test_f056_pipeline_revision.py` (el `por_estado` del resumen) | Cuatro estados |
| `test_f056_revision_dominio.py` (estados, acciones, `es_candidata`) | Cuatro estados y acciones |
| `test_f056_revision_http.py` (`CLAVES_DE_FILA`; `por_estado` en el listado; el mensaje de `_filtro`) | Cuatro estados, y **la clave nueva `volcado`** (fuera de la letra de R41) |
| `test_f056_repositorio_revision.py` (filas falsas con el ancho de `_select_situaciones`; `aprobadas`; `registrar`) | **El ancho de la fila** (fuera de la letra de R41; T4 ya lo preveía) |
| `test_f056_documentacion.py::test_f056_r44_nombra_cada_estado` | Que la sección de F-056 de `ARCHITECTURE.md` nombre cada `EstadoRevision`: con seis, la enmienda de esa sección va en T2 y no en T20 |

Ninguno de los de F-009 se toca: el cambio de anotación de §8.4 no lo fija
ningún test (`test_f009_arquitectura.py` mira las importaciones, no las
firmas).

### 21.4 · Controles ajenos que siguen vigentes y el plan respeta

Los controles de las guardas de F-036, F-056 y F-060 que **no** dependen de
`git` se comprueban en cualquier rama; los del diff se saltan fuera de la suya.
F-059 no los toca y su código no puede romperlos:

- `test_f056_alcance_cerrado.py`: en las piezas de F-056 (los ficheros nuevos
  de F-056 enteros y sus funciones de `function_app.py` y las fábricas), ni
  «habilitado», ni rutas de escritura de `sigrid-api`, ni `UPDATE`/`DELETE`/
  `TRUNCATE`, ni DDL, ni `environ`/`getenv`; `function_app.py` sin importar
  `infrastructure.sigrid.escrituras` ni `graficos`; `interface_adapters/api/revision.py`
  sin importaciones nuevas de `infrastructure.sigrid`.
- `test_f060_alcance_cerrado.py`: lo mismo sobre las piezas de F-060
  (`listar_revision`, `registrar_lote`, `importar.py` entero…), que F-059 no
  toca.
- `test_f036_alcance_cerrado.py`: `ErpPort` sigue con `leer_reclamacion`,
  `existe_usuario` y `cerrar` (§8.4 crea `VerificadorDeLoginPort` aparte y no
  toca `ErpPort`).
- `test_f060_importacion_diferida.py` (§11) y `test_f056_r46_…` (ninguna
  construcción ni lectura más en el listado: las `LATERAL` van en la misma
  consulta).

### 21.5 · Convivencia con F-060

- **La normalización no puede editar una `volcada` ni una `en_duda`.** Su
  plan (`planificar_normalizacion`) solo escribe sobre `ESTADOS_NORMALIZABLES`
  = {`nueva`, `editada`}, por **lista permitida**, y calcula el estado con el
  mismo `estado_de` que F-059 amplía; como `listar` trae la situación de
  volcado (§12), una `volcada` o una `en_duda` cuenta en `no_editables`. Y aun
  sin eso quedaría fuera: su última revisión es un `aprobar` (§4.1), y una
  `aprobada` tampoco es normalizable. Lo dice F-060 en su §10.2.
- **Ni con una carrera.** Para que una incidencia que el plan vio `nueva` o
  `editada` llegue a `en_duda` o `volcada`, alguien tiene que aprobarla antes
  (revisión nueva) y la escritura anticipada de R20 exige esa aprobación. El
  `_registrar_lote` de F-060 compara, bajo `FOR UPDATE`, la última
  `revision_id` con la esperada y salta la que cambió. Por eso
  `registrar_lote` **no** necesita la comprobación de R2 que gana `_registrar`
  y no se toca.
- **Sin interbloqueos.** `registrar` (F-056), `registrar_lote` (F-060) y
  `anotar_enviados` (F-059) bloquean las filas de `bandeja_incidencias` con la
  misma `select_bloquear`, en orden de `incidencia_id`. Un lote de
  normalización tras una importación grande puede retener las filas del orden
  de un segundo (F-060 §7): el volcado espera; si pasara de `pg_lock_timeout_s`,
  la escritura anticipada falla sin escribir nada (503, «Reintentar», §6.2).
- **El actor del volcado nunca es el sistema.** `usuario_correo` se valida con
  `validar_quien` (R9, R15), que rechaza `sistema:normalizar_ubicacion`.
- **Lo aprobado sigue siendo lo que se manda.** Una normalización es una
  revisión `editar` con su huella; si después se aprueba, la huella del
  `aprobar` es la de los valores normalizados y R7 la recalcula igual.
- **El estado `editada`** puede venir ahora también del sistema; no cambia
  nada de §4: se edita, se descarta o se aprueba como cualquier `editada`.
- **En la verificación (T25)**, la fila de prueba importada puede quedar
  `editada` por la normalización tras importar; da igual para el guion.

### 21.6 · Los dos cambios de fondo, y lo que decidió el humano

**Resueltos el 2026-10-15** por el humano, literal: **«a en las 2»** →
**F-1 (a)** y **F-2 (a)**, aplicadas en R41, R4, §12, §17 y las tareas (§20).
Las opciones se conservan abajo como constancia.

**F-1 · R41 frente al inventario de §21.3.** R41 dice que los tests de F-012,
F-036 y F-053 siguen **sin tocarse** y que los de F-056 solo se amplían donde
fijan cuatro estados o acciones. Con lo ya aprobado (el `16_`, R32; la cuenta
y la cabecera de `INTEGRACION.md`, R40 y R42; el objeto `volcado`, R4), eso es
imposible: `test_f036_t14_…`, `NUMERALES` de F-012 y `CUENTA_VIGENTE` de F-053
fallan por fuerza, y lo mismo los de F-028, F-030–F-034, F-056 y F-060 de
§21.3.

- **(a) Recomendada y elegida.** Añadir a R41 un bloque «Excepciones, ampliando sin
  relajar», como R45 de F-056, con la lista de §21.3; cada una declarada
  función a función en `test_f059_alcance_cerrado.py`, que vigila que no se
  pierde ninguna aserción. Es el criterio que el humano aprobó en F-056 y que
  el líder aplicó en F-060.
- (b) Evitarlo cambiando el plan: otro número de fichero no evita nada (las
  listas fijan los quince), y no contar las rutas en `INTEGRACION.md`
  contradiría R40. No hay una (b) razonable.

**F-2 · El objeto `volcado` en la respuesta de `POST /api/revision/acciones`.**
R4 lo pide en «cada incidencia» de `GET /api/revision`. En el código, la fila
del listado y la de la respuesta de la acción salen de la **misma** función
(`_fila`).

- **(a) Recomendada y elegida.** En las dos, por la función común: es una clave
  **añadida** (F-038 ignora lo que no conoce), una incidencia tiene la misma
  forma en las dos respuestas y no hace falta parametrizar `_fila`. El
  historial no cambia (no usa `_fila`).
- (b) Solo en el listado: un parámetro en `_fila` o una segunda función, y
  dos formas de la misma incidencia.
