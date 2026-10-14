<!-- specs/F-060-normalizar-ubicaciones/design.md -->
# F-060 · Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid — Diseño técnico

> **Estado: pendiente de aprobación del humano** (PARADA 1). Decisiones y
> preguntas en §15, cada una con recomendación. Lo que bloquea empezar: D-1,
> D-2, D-4 y Q-1 (forma de la constancia y estado resultante). Lo que bloquea
> solo el Bloque 7: D-9 y Q-3.

## 0 · Dónde está el riesgo

| Si falla… | Consecuencia | Quién lo ve |
|---|---|---|
| La regla de «salvo mayúsculas» | Se cambia una ubicación por **otra** de Sigrid (una errata, una ambigua) y el parte sale a otra estancia | El propietario, en la visita |
| Solo editables | Una `aprobada` recibe una revisión `editar` y **pierde la aprobación** sin que nadie lo pida; o se toca una volcada | Quien vuelca: la incidencia desaparece de las candidatas |
| La concurrencia | El sistema pisa una edición humana hecha entre la lectura y la escritura | Nadie, hasta que el parte sale mal |
| La constancia | No se sabe qué mandó la propiedad ni quién cambió la ubicación | Quien audite |
| La importación | Un fallo de la normalización tumba una importación que ya está guardada | Posventa, que reimporta y recibe `ya_importado` |
| La medición | La traza cambia el comportamiento o filtra un texto o un correo | Quien lea los logs |

**Rigor `critico`**: RED en los centrales (R1–R5, R7, R8, R12, R13, R19–R21,
R25, R26, R31, R33, R34, R41), cobertura de lo cambiado, cero supervivientes
sin justificación aceptada por escrito, `MANUAL (humano)` con su comando.

## 1 · Lo que hay hoy

- **F-036** valida la ubicación de cada fila, **exacta**, contra la lista de
  `config/plantilla_incidencias.yaml` (la misma para todas las filas) y la
  guarda en `postventa.bandeja_incidencias`, que **nadie modifica**.
- **F-056** valida, también **exacta tras recortar**, contra la lista de la
  tipología de la unidad en Sigrid (`prmtpl.ubica`, su design §16). Cada
  acción añade una **foto completa** a `postventa.revisiones_bandeja`
  (append-only, manda la mayor `revision_id`); el estado se deriva; aprobar
  guarda los vigentes sin cambiarlos y solo sin motivos de no aprobable.
- Las dos listas difieren en mayúsculas: la plantilla ofrece un texto y Sigrid
  guarda otro. De ahí los 110 de 148 de la 0677.
- `clave_de_duplicado` ya pliega mayúsculas y tildes (`normalizar_para_clave`
  de F-036): **normalizar la ubicación no cambia ninguna clave de duplicado**
  y el motivo `duplicada` (F-056 D-5) no se mueve.

## 2 · Límite de servicio

Solo `services/postventa-api`, más `docs/` y `azure-apps/`. **No** toca:

- la plantilla ni su YAML: ofrecer en cada fila las ubicaciones de su unidad
  es **F-058**, que hará que lo nuevo llegue ya exacto. F-060 sigue haciendo
  falta después: las plantillas viejas se seguirán importando (F-058 decide
  cómo) y lo ya importado no cambia solo;
- el front: la página de revisión es **F-038**, que no necesita cambios para
  consumir esto (§10);
- Sigrid: solo `POST /api/sql/read`, las mismas tres lecturas de F-056;
- `infra/`: salvo que el Bloque 7 elija un remedio de plataforma (§11.4), y
  entonces se decide aparte.

## 3 · La regla (D-3)

**Clave**: `unicodedata.normalize("NFC", texto).strip().casefold()`.

- **Mayúsculas**: sí, con `casefold` (más estricto que `lower` para Unicode,
  igual para el castellano).
- **Blancos en los extremos**: sí. F-056 ya compara recortado (R47); aquí el
  texto **guardado** pasa a ser el recortado de Sigrid, lo que de paso cierra
  el caso de la N-1 de F-056 (una vigente sin recortar que no se podía
  aprobar). Hoy es inalcanzable.
- **NFC**: sí. Una «ñ» compuesta y una «n» más tilde combinante se ven igual y
  son el mismo texto; no es «quitar tildes» (Q-4).
- **Blancos interiores, tildes, letras, puntuación**: **no**. Medido el
  2026-10-09: 0 casos por tildes o blancos. Lo que no es la misma palabra con
  otra caja es una errata o una ubicación distinta, y la decide una persona.

**Clasificación** de un texto `t` contra la lista `L` de su unidad (R2):

| Caso | Ejemplo ficticio (`L` = «Sala Ejemplo», «patio ficticio») | Resultado |
|---|---|---|
| `t ∈ L` | «Sala Ejemplo» | `exacta` |
| `t.strip() ∈ L` | « Sala Ejemplo » | `normalizable` → «Sala Ejemplo» |
| una clave igual | «SALA EJEMPLO», «Patio Ficticio» | `normalizable` → «Sala Ejemplo», «patio ficticio» |
| dos o más claves iguales (si `L` trajera «Patio Ficticio» y «patio ficticio») | «PATIO FICTICIO» | `ambigua` |
| ninguna | «Sála Ejemplo», «Sala  Ejemplo», «Sala Ejemplo.» | `sin_coincidencia` |

La **ambigüedad** existe de verdad: F-056 §16.2 conserva como dos opciones
dos valores de la misma tipología que solo difieren en una mayúscula («es su
dato y se respeta tal cual»). Si `t` no es exactamente uno de ellos, el
sistema no elige: queda `ubicacion_fuera_de_lista` y lo decide una persona.

## 4 · Dónde y cómo se normaliza (D-1, D-4, D-6, D-7)

### 4.1 · Las tres opciones

| | (a) Al importar | (b) Calculado al leer | (c) **Revisión del sistema** |
|---|---|---|---|
| Qué es | La fila nace en la bandeja con el texto de Sigrid | `vigentes` se calcula normalizado al listar y al aprobar, sin escribir | Una revisión `editar` más en `revisiones_bandeja`, hecha por el sistema |
| Lo ya importado (los 110) | **No lo cubre**: la bandeja no se reescribe; haría falta además (c) | Sí | Sí, con un proceso idempotente |
| Constancia | Hace falta una columna nueva en la bandeja (DDL) para guardar lo que llegó | Solo al aprobar, en la foto de quien aprueba | Una revisión con su foto, su hora y su autor (el sistema); el historial la enseña |
| Contrato con F-038 | `importados` deja de ser lo que mandó la propiedad | `vigentes` deja de ser lo guardado: `estado`, `cambios` y la edición dejan de cuadrar (F-038 R9 vacía una ubicación que no está en la lista) | **Sin cambios** de forma (§10) |
| Otros | La importación tiene que leer las ubicaciones; choca con F-058 | Cada regla de F-056 tendría que normalizar al vuelo | Escribe la base; necesita concurrencia |

**Recomendación: (c).** Es la única que cubre lo importado y lo que venga con
un solo mecanismo, deja constancia completa (la foto anterior sigue ahí) y no
cambia ninguna forma de respuesta. La (a) se descarta porque no basta sola; la
(b), porque rompe la idea de F-056 de que lo vigente es lo guardado.

### 4.2 · Constancia sin DDL (D-4)

La revisión de normalización es **una fila más** de `revisiones_bandeja`:

| Columna | Valor |
|---|---|
| `accion` | `editar` (el `CHECK` de F-056 no admite otra y la guarda de DDL solo permite `ALTER TABLE … ADD COLUMN IF NOT EXISTS`, no cambiar un `CHECK`) |
| valores | los vigentes con **solo** `ubicacion` cambiada al texto de Sigrid |
| `huella_valores` | `huella_de_valores` de esos valores |
| `motivo` | `NULL` |
| `revisado_por`, `revisado_correo` | el literal `sistema:normalizar_ubicacion` (Q-2) |
| `revisado_at_utc` | el instante de la petición |

Por qué el literal sirve de marca:

- **No se puede suplantar**: `validar_quien` exige un correo con `@`, así que
  ninguna petición de `POST /api/revision/acciones` puede escribir ese correo
  (R11, con test).
- **No es un dato personal** ni un `oid`: no amplía lo que F-056 §9 guarda de
  las personas.
- **Dice qué regla** la escribió, por si mañana hay otra automática.
- Cabe en el `CHECK` del correo (3–254) y en el `NOT NULL` del `oid`.

Alternativa descartada (y disponible si el humano la prefiere): una columna
nueva `automatica text` con `ALTER TABLE … ADD COLUMN IF NOT EXISTS`. Exige
un `16_…sql` (y entonces F-059 pasa su `16_volcados_sigrid.sql` a `17_`) o
tocar `15_…sql`, que F-056 fija en sus tests. No compensa mientras haya una
sola regla automática.

### 4.3 · El estado que queda (Q-1)

Con (c), la incidencia normalizada pasa de `nueva` a **`editada`**: sus
vigentes ya no son los importados. Es la regla de F-056 (§3.2) sin tocarla, y
es verdad: la ubicación ya no es la que mandó la propiedad. `acciones_posibles`
es la misma para las dos. Consecuencia: en la 0677, ~110 incidencias cambian
de `nueva` a `editada` en `resumen.por_estado`.

La alternativa —que siga `nueva`— obliga a que `estado_de` distinga las
revisiones del sistema de las humanas (cambia F-056 R1 y la costura que F-059
amplía en `estado_de`). **Recomendación: aceptar `editada`.**

### 4.4 · Qué incidencias (D-6)

Solo las `nueva` y `editada` (lista **permitida**, no prohibida):

- `aprobada`: una `editar` le quitaría la aprobación (F-056 D-7). Además no
  puede pasar con la regla de hoy (aprobar exige ubicación exacta), salvo que
  Sigrid cambie la lista después de aprobar; en ese caso, se cuenta en
  `no_editables` y la decide una persona.
- `descartada`: no admite `editar`. Si se recupera, la siguiente ejecución la
  normaliza.
- `volcada`, `en_duda` (F-059): no están en la lista permitida, así que
  quedan fuera sin que F-059 tenga que hacer nada (§10.2).

### 4.5 · Concurrencia (D-7)

El plan se calcula fuera de la transacción, con la última `revision_id` que
se leyó de cada incidencia como **esperada**. La escritura (§7) bloquea las
filas, compara y escribe **solo** las que siguen igual; las demás se saltan y
se cuentan en `conflictos`. No aborta el lote: una edición humana entre medias
no debe impedir normalizar el resto, y la siguiente ejecución recoge la que se
saltó si sigue haciendo falta. Quien tenga la página abierta y actúe sobre una
fila recién normalizada recibe el 409 `revision_desactualizada` de siempre, y
recarga.

## 5 · Cuándo se normaliza (D-2, D-8)

1. **Tras cada importación que registra filas** (R31–R35): el borde de la
   importación llama a `normalizar_ubicaciones` de la obra con el catálogo que
   ya leyó, **después** del Excel de errores. Es **la obra entera**, no solo
   lo recién importado: es idempotente y así no hace falta llevar los
   identificadores. Es de **mejor esfuerzo**: la importación ya está guardada,
   así que si la normalización no puede hacerse (Sigrid, la base, el tope), se
   avisa en el log y la respuesta es la misma. Lo que no se normaliza se ve
   como `ubicacion_fuera_de_lista` y se recoge en la siguiente ejecución.
   ~~Errores capturados, y solo estos: `CatalogoNoDisponible`,
   `CatalogoSinVerificar`, `ObraSinUnidades`, `ObraAmbigua`,
   `ConfiguracionSigridIncompleta`, `ErrorDePersistencia` (y subclases) y
   `BandejaDemasiadoGrande`. Un error de programación sube.~~
   **Decisión del humano 2026-10-12: mejor esfuerzo = cualquier excepción de la normalización se registra por su tipo y no afecta a la importación.** Se captura **cualquier** `Exception` al **componer o
   ejecutar** la normalización tras importar (también un `AttributeError` por
   una configuración incompleta, y los errores de programación), en ese único
   punto: el aviso lleva la obra y **solo el tipo** de la excepción (sin
   mensaje, sin textos de ubicación, sin correo ni `oid`) y la importación
   responde exactamente igual que sin normalización. Nada más de la
   importación se captura de forma amplia. Lo dispara la T15 del Bloque 4: un
   test de F-036 que no se toca (`test_f036_r118_…`) finge `ENTORNO=pro` con
   unos ajustes incompletos.
2. **A demanda** con `POST /api/revision/normalizar` (§9.1): para lo ya
   importado (los 110 de la 0677), para recoger lo que se saltó y para cuando
   Sigrid cambie una lista. Con **ensayo obligatorio en el cuerpo**
   (`ensayo: true|false`, sin valor por defecto): el humano lanza primero el
   ensayo, mira los números y luego la real. Lo lanza desde el entorno
   desplegado (consola del navegador en el portal, como la T19 de F-056).

Alternativa a 1 (D-2 b): sin normalización tras importar, solo a demanda.
Más simple y no toca la importación, pero cada Excel de una plantilla vieja
deja sus ubicaciones fuera de lista hasta que alguien lance el endpoint.
**Recomendación: 1 y 2.**

## 6 · Dominio puro: `domain/models/normalizacion.py` (nuevo)

Sin red, sin base, sin reloj. Importa de `domain/models/revision.py` sin
modificarlo.

```python
class Coincidencia(StrEnum): EXACTA="exacta"; NORMALIZABLE="normalizable"; AMBIGUA="ambigua"; SIN_COINCIDENCIA="sin_coincidencia"

TEXTO_SISTEMA = "sistema:normalizar_ubicacion"
QUIEN_SISTEMA = Quien(oid=TEXTO_SISTEMA, correo=TEXTO_SISTEMA)
ESTADOS_NORMALIZABLES = frozenset({EstadoRevision.NUEVA, EstadoRevision.EDITADA})

@dataclass(frozen=True)
class UbicacionDeSigrid:
    coincidencia: Coincidencia
    texto: str | None          # el de la lista si NORMALIZABLE; None si no

@dataclass(frozen=True)
class RecuentoNormalizacion:
    examinadas: int; no_exactas: int; normalizables: int
    ambiguas: int; sin_coincidencia: int; no_editables: int

@dataclass(frozen=True)
class PlanDeNormalizacion:
    revisiones: tuple[RevisionNueva, ...]          # en orden de incidencia_id
    esperadas: Mapping[UUID, int | None]           # una por revisión
    recuento: RecuentoNormalizacion
```

| Función | Responsabilidad | R |
|---|---|---|
| `clave_de_ubicacion(texto) -> str` | NFC, recorte, `casefold` | R1 |
| `ubicacion_de_sigrid(texto, lista) -> UbicacionDeSigrid` | La tabla de §3, en su orden | R2–R5 |
| `revision_de_normalizacion(situacion, texto, *, ahora) -> RevisionNueva` | Los vigentes con solo la ubicación cambiada, su huella, `QUIEN_SISTEMA`, sin motivo | R8 |
| `planificar_normalizacion(situaciones, ubicaciones, *, ahora) -> PlanDeNormalizacion` | R6, R7, R9, R10: la ubicación vigente contra la lista de la unidad vigente; solo `ESTADOS_NORMALIZABLES` | R6–R10 |

`ubicaciones` es el `Mapping[str, tuple[str, ...]]` de F-056 (por unidad).
Una unidad sin entrada tiene la lista vacía (R3).

## 7 · Puerto y repositorio: el lote

`domain/ports/revision.py` **gana** un método (los demás no cambian):

```python
@dataclass(frozen=True)
class ResultadoDelLote:
    registradas: Mapping[UUID, int]      # incidencia_id → revision_id
    desactualizadas: frozenset[UUID]

class RevisionPort(Protocol):
    ...
    def registrar_lote(self, *, revisiones: Sequence[RevisionNueva],
                       esperadas: Mapping[UUID, int | None]) -> ResultadoDelLote: ...
```

`RepositorioRevisionPostgres.registrar_lote`, en **una** transacción
(`_en_transaccion`, el de F-036/F-056):

1. Lote vacío → `ResultadoDelLote({}, frozenset())` sin abrir transacción (R16).
2. Precondiciones (error de programación, `ValueError`): cada revisión con su
   esperada y ninguna incidencia repetida.
3. `select_bloquear` de **todas** (las sentencias de F-056, sin cambiarlas:
   `FOR UPDATE`, orden fijo).
4. `select_ultimas_revisiones` y comparación con las esperadas.
5. Por cada fresca, en orden de `incidencia_id`, `insert_revision` (la misma
   sentencia de F-056, `RETURNING revision_id`).
6. `COMMIT`. Un fallo de la base → `ROLLBACK` y `PersistenciaNoDisponible`
   (R14). Ningún `UPDATE`, `DELETE` ni `TRUNCATE` (R15).

Coste: con N filas, dos sentencias más N `INSERT` en la misma conexión y
transacción; las filas quedan bloqueadas mientras dura. Con 110 es poco; con el
máximo de una plantilla (1.000) es del orden de un segundo: dentro del
presupuesto de la importación (§11 lo mide).

`sentencias_revision.py` no cambia (se reutilizan sus tres sentencias).
**Nunca `pg_advisory_lock`** (servidor compartido).

## 8 · Aplicación: `normalizar_ubicaciones`

En `application/pipelines/revision.py` (se **añade**; lo demás no cambia):

```python
@dataclass(frozen=True)
class ResultadoNormalizacion:
    obra_codigo: str; ensayo: bool; recuento: RecuentoNormalizacion
    normalizadas: int; conflictos: int

def normalizar_ubicaciones(obra_codigo: str, *, revision: RevisionPort,
                           catalogo: CatalogoObra, ubicaciones: FuenteDeUbicaciones,
                           ahora: datetime, ensayo: bool) -> ResultadoNormalizacion
```

`revision.listar(tope=10.000)` (si vuelven más, `BandejaDemasiadoGrande` con
`contar`, sin leer Sigrid ni escribir) → `ubicaciones(catalogo)` una vez →
`planificar_normalizacion` → si `ensayo` o el plan está vacío, se devuelve el
recuento → si no, `registrar_lote` y el resultado. Recibe el **catálogo ya
leído**: el endpoint lo lee con `leer_catalogo`; la importación pasa el suyo.

## 9 · El borde

### 9.1 · `POST /api/revision/normalizar`

Módulo nuevo `interface_adapters/api/normalizacion.py` (no se toca
`interface_adapters/api/revision.py` para esto, cuyas importaciones fija un
test de F-056):

```json
{"obra": "9901", "confirmado": true, "ensayo": true}
```

Respuesta 200 (ficticia):

```json
{"obra": "9901", "ensayo": true,
 "examinadas": 160, "no_exactas": 120, "normalizables": 100,
 "ambiguas": 2, "sin_coincidencia": 18, "no_editables": 0,
 "normalizadas": 0, "conflictos": 0}
```

- El cuerpo se comprueba **entero** antes de construir nada (R26): objeto,
  exactamente las tres claves, `confirmado is True`, `ensayo` booleano,
  `obra` con `normalizar_codigo_obra`. Mensajes que no repiten lo recibido.
- Composición, como el listado: `construir_catalogo_obra`,
  `construir_fuente_de_ubicaciones` (de `interface_adapters/api/revision.py`,
  importada) y después `construir_revision`. Inyectables por parámetro (la
  costura de test).
- Sin identidad en el cuerpo: las revisiones son del sistema (§4.2) y nadie
  más queda escrito. Cualquiera de `posventa-usuarios` puede lanzarlo, como
  cualquier acción de revisión (Q-6).
- Ruta en `function_app.py`, `ANONYMOUS` como las demás (veintiuna), con la
  traducción de errores del listado (`_error_de_revision` y las de obra y
  disponibilidad). Ninguna ventana de escritura.

### 9.2 · La importación

`interface_adapters/api/importar.py`, `importar_excel` gana un parámetro
`normalizar: Callable[[str, CatalogoObra, datetime], ResultadoNormalizacion] | None`
(la costura de test). Tras `paso_excel_errores`, si la importación registró
filas (R31), lo llama; si es `None`, compone el real (`construir_revision`,
`construir_fuente_de_ubicaciones`, `normalizar_ubicaciones` con
`ensayo=False`). ~~Captura solo los errores de §5.1~~ Captura cualquier
excepción al componer o ejecutar la normalización (**Decisión del humano 2026-10-12: mejor esfuerzo = cualquier excepción de la normalización se registra por su tipo y no afecta a la importación**, §5.1) y
registra el aviso con su tipo (R34).
`serializar_importacion` **no** cambia: la respuesta es la misma (R33).
`paso_importacion.py` no cambia: la composición es del punto de entrada
(`docs/CONVENTIONS.md`).

### 9.3 · Logs

- Endpoint: `F-060 normalización de ubicaciones: obra=… ensayo=… examinadas=…
  no_exactas=… normalizables=… ambiguas=… sin_coincidencia=… no_editables=…
  normalizadas=… conflictos=… segundos=…`.
- Importación: la misma línea con `origen=importacion`; o, si falla,
  `F-060 normalización tras importar no hecha: obra=… motivo=<TipoDeError>`.
- Nunca textos de ubicación, `oid`, correo ni `incidencia_id`.

## 10 · Impacto en los contratos

### 10.1 · F-038 (spec aprobada, sin implementar; `postventa-f038`)

**Ninguna forma cambia** (R36): las mismas claves en el listado, el historial
y la acción. Lo que verá distinto, con datos:

| Dónde | Antes | Después |
|---|---|---|
| Fila normalizada | `estado: "nueva"`, `cambios: []`, `revisado_por: null`, `ubicacion_fuera_de_lista` | `estado: "editada"`, `cambios: ["ubicacion"]`, `revisado_por: "sistema:normalizar_ubicacion"`, sin ese motivo |
| R4 de F-038 («<acción> por <correo> el <fecha>») | — | «editar por sistema:normalizar_ubicacion el …» |
| R8 (historial, «llegó así») | — | Una revisión `editar` del sistema con `ubicacion`; «llegó así: <lo de la propiedad>» |
| R9 (formulario) | La ubicación no casaba con ninguna opción y se vaciaba | Casa: es un valor de `catalogo.ubicaciones` |
| Acción sobre una fila recién normalizada | — | 409 `revision_desactualizada` si la página no se recargó |

Funciona tal cual. **Mejora opcional** (para el líder, antes de que F-038
empiece; no bloquea): que F-038 enseñe «normalizada por el sistema» cuando el
correo es `sistema:normalizar_ubicacion`.

### 10.2 · F-059 (spec aprobada; `postventa-f040`)

- **Candidatas**: no cambian. Lo aprobado ya exigía texto exacto; ahora es
  aprobable lo que antes no (R24). `CandidataAlVolcado`, `huella_de_valores`
  y `candidatas_al_volcado` no se tocan.
- **Estados**: F-059 amplía `estado_de` con `volcada` y `en_duda` (su §12) y
  deja `acciones_posibles` vacía para las dos. Como la normalización usa una
  lista **permitida** (`nueva`, `editada`), las dos quedan fuera sin que F-059
  haga nada. Si F-059 cambia `SituacionDeRevision` (gana `volcado`), el
  `listar` que use la normalización es el mismo que usa el listado: lo que F-059
  haga en uno vale para el otro.
- **`RevisionPort`** gana `registrar_lote`. F-059 lo importa y no lo
  implementa; sus dobles de test no lo necesitan.
- **Cuenta de rutas**: F-059 dice «veintitrés anónimos»; tras F-060 serán
  **veinticuatro** (su design §8 y su T de documentos). Lo ajusta el líder al
  llevar la spec de F-059 a su rama.
- **DDL**: ninguno en F-060; su `16_volcados_sigrid.sql` sigue siendo el 16.

### 10.3 · Otros

- **Front de F-036** (`importar.html`): la respuesta de la importación no
  cambia (R33).
- **F-058**: al rehacer la validación de la importación, debe conservar la
  llamada de §9.2 (o decir por qué sobra). Se anota en su ficha.
- **F-048** (datamart): las revisiones del sistema se reconocen por
  `revisado_correo = 'sistema:normalizar_ubicacion'`.

## 11 · El listado lento

### 11.1 · Lo que hace cada petición (leído en el código)

`listar_revision` (borde) → `listar_para_revisar` (aplicación), en este orden:

| Tramo | Qué es | E/S |
|---|---|---|
| `construir_catalogo_obra`, `construir_fuente_de_ubicaciones` | Adaptadores de Sigrid; solo puertas y configuración | No |
| `construir_revision` | `psycopg.connect` + 4 sentencias de sesión + `commit`; la **primera vez del proceso**, además, el DDL entero (15 ficheros) bajo `pg_advisory_lock` | Sí |
| `construir_equivalencias` | **Otra** `psycopg.connect` + sesión | Sí |
| `configuracion_de_la_plantilla` | El YAML de la plantilla, en caché (`@cache`) desde la primera petición del proceso | Disco, una vez |
| `revision.listar` | Una consulta con dos `LEFT JOIN LATERAL` (indexada por `ix_bandeja_obra` e `ix_revisiones_bandeja_incidencia`) | Sí |
| `leer_catalogo` | Dos `sql/read` (unidades y oficios), **en serie** | Sí |
| `opciones_de_la_obra` | Una consulta de decisiones + agrupación en memoria (sin Levenshtein: eso es solo de las propuestas) | Sí |
| ubicaciones | Un `sql/read` | Sí |
| Por fila | `estado_de`, `motivos_no_aprobable` (reconstruye en cada fila los conjuntos de unidades, oficios y pares del catálogo), `campos_cambiados` | No |
| `resumen`, `paginar` | Recuentos y una ordenación | No |
| Serializar | El catálogo entero (15 unidades × ~35 ubicaciones, oficios, pares) y 100 filas × 2 fotos | No |

Las conexiones no se cierran explícitamente: se liberan al recoger el objeto.
Las lecturas de Sigrid dejan su tiempo en el log (`segundos=`), y de ahí sale
el 0,1–0,3 s; **ningún otro tramo deja tiempo**.

### 11.2 · Hipótesis (no causas)

| | Hipótesis | Lo que la confirmaría |
|---|---|---|
| H1 | Las **dos conexiones** nuevas a PostgreSQL por petición (TLS + SCRAM + sesión) | `construir.revision` y `construir.equivalencias` altos en todas |
| H2 | La **primera petición de cada proceso**: imports de `function_app.py` y el DDL bajo bloqueo consultivo (que espera si otro proceso lo tiene) | Tiempos altos solo con `proceso_nuevo=True`, o `construir.revision` alto solo ahí |
| H3 | **Arranque en frío** de la instancia de Flex Consumption (fuera de nuestro código) | `requests.duration` de App Insights muy por encima del `total` de la traza |
| H4 | **Red y proxy** de la Static Web App (`westeurope` ↔ `spaincentral`) | Tiempo del navegador muy por encima de `requests.duration` |
| H5 | Las tres lecturas de Sigrid en serie | `catalogo.*` + `ubicaciones` cerca del total |
| H6 | La consulta de `listar` | `revision.listar` alto |
| H7 | El cálculo por fila o la serialización | `calculo` o `serializar` altos |

Con 158 filas, H7 es improbable por el código (milisegundos), pero no se
descarta sin medir. **El código no permite elegir entre H1–H4.**

### 11.3 · Cómo se mide (R40–R42)

Módulo nuevo `interface_adapters/api/tiempos.py`, solo en el borde (la
aplicación no cambia):

```python
class Cronometro:
    def __init__(self, reloj: Callable[[], float] = time.perf_counter) -> None
    def tramo(self, nombre: str) -> ContextManager[None]   # suma aunque salga por excepción
    def medir(self, objeto: T, prefijo: str) -> T           # proxy: cada método llamado suma en "prefijo.metodo"; un invocable, en "prefijo"
    def tramos(self) -> Mapping[str, float]
def es_primera_peticion() -> bool                           # True la primera vez en el proceso
def segundos_de_proceso() -> float                          # desde que se importó el módulo
```

En `listar_revision`: cada `construir_*` dentro de `tramo("construir.…")`;
los puertos envueltos con `medir` (`revision.listar`, `catalogo.leer_unidades`,
`catalogo.leer_oficios`, `equivalencias.ultimas_decisiones`, `ubicaciones`);
`listar_para_revisar` en `tramo("aplicacion")`; el cuerpo en
`tramo("serializar")`; `calculo` = `aplicacion` − los puertos. En un
`finally`, **una** línea:

```
F-060 tiempos del listado: obra=9901 resultado=200 total=7.12 proceso_nuevo=False
segundos_de_proceso=812 construir.catalogo=0.00 construir.ubicaciones=0.00
construir.revision=… construir.equivalencias=… configuracion=… revision.listar=…
catalogo.leer_unidades=… catalogo.leer_oficios=… equivalencias.ultimas_decisiones=…
ubicaciones=… aplicacion=… calculo=… serializar=…
```

(una sola línea en el log; partida aquí para leerla). Con el error, `resultado`
es su tipo y la línea sale igual. El proxy reenvía argumentos, valores y
excepciones sin tocarlos (R41). La línea de F-056 no cambia.

> **Desviación del implementer (Bloque 5, T18; pendiente de aceptación del
> líder y del humano).** El repositorio de la revisión se mide como
> `construir.bandeja` y `bandeja.listar` (y `bandeja.contar`), no como
> `construir.revision` y `revision.listar`: con esos nombres la línea de
> F-060 contiene «revision», y
> `test_f056_revision_http.py::test_f056_r31_el_log_del_listado_solo_lleva_obra_tamano_y_recuentos`
> —que no se toca (R39)— exige que la única línea del listado con «revision»
> sea la de F-056. R40–R42 no fijan los nombres; los demás tramos son los de
> arriba. Los números van con tres decimales y la obra es `-` si la de la
> petición no valía. Detalle en `progress/impl_F-060.md`, Bloque 5.

**En producción** (Bloque 6, MANUAL): 10 listados seguidos de la 0677 y uno
tras ≥ 20 min sin uso; el tiempo del navegador de cada uno; y dos consultas
de Application Insights, de solo lectura, que cruzan la traza con
`requests.duration` por `operation_Id` (textos exactos en `tasks.md`). Así
se separan H1–H7.

### 11.4 · Objetivo y remedios (D-9, D-10)

**Objetivo**: en caliente (sin `proceso_nuevo`), de 10 listados seguidos de la
primera página de la 0677, **máximo < 10 s** (la ficha) y **p50 < 3 s**
(deseable). El frío se mide y se informa aparte (Q-3).

**Remedios ya diseñados**, para elegir con la medición (Bloque 7). Ninguno se
implementa sin el dato:

| Si domina | Remedio | Riesgo |
|---|---|---|
| H1 | **M-1**: una sola conexión por petición para la revisión y las equivalencias (`construir_revision_y_equivalencias` en `persistencia/fabrica.py`, los dos repositorios sobre la misma conexión) y cerrarla al terminar (`finally`) | Bajo. Menos conexiones al servidor compartido |
| H1 (y M-1 no basta) | **M-2**: reutilizar la conexión dentro del proceso, con comprobación antes de usarla y reconexión ante fallo | Medio: conexiones vivas en un servidor de otros (Q-5) |
| H2 | **M-3**: mover a importación diferida los módulos pesados que el listado no usa (IA, PDF, `openpyxl`) | Bajo-medio: toca `function_app.py` |
| H3 | **M-4**: instancia «siempre lista» en Flex Consumption (`infra/`) | Coste mensual: decisión del humano, fuera del código |
| H5 | **M-5**: las lecturas de Sigrid en paralelo (hilos), la de ubicaciones con el código de obra ya normalizado | Medio: cambia el orden de F-056 §16.3 («tras `leer_catalogo`»), que hay que enmendar |
| H6 | **M-6**: revisar el plan con `EXPLAIN` en la base efímera y, si hace falta, un índice nuevo | Bajo (DDL en el esquema propio) |
| H7 | **M-7**: precalcular una vez por petición los conjuntos del catálogo que usa `motivos_no_aprobable` | Bajo |
| H4 | Nada en este servicio; se documenta | — |

Tras elegir (PARADA del humano), el líder anota la elección en esta sección y
el implementer hace el Bloque 7 con su RED, su mutación y su segunda medición.

**Elección (humano, 2026-10-14, T30).** M1 (`progress/impl_F-060.md`, T28) no cumple
D-10: en caliente p50 4,92 s y máximo 14,73 s. Descartadas H1, H4, H6 y H7. Dominan
dos causas: **A** (H2+H3), un proceso o instancia nueva, que suma ≈ 3 s antes del
handler y ≈ 2,5 s de plataforma (10 peticiones seguidas cayeron en 6 instancias); y
**B** (H5), picos de 4–8 s en una sola lectura de `sigrid-api`, también en procesos
calientes. **Se hace M-3** y nada más. Tras M2 (T35), F-060 se cierra **con el dato que
salga**, cumpla o no D-10: no se vuelve a T30. Lo que falte (la causa B, M-4, la
concurrencia por instancia y M-5) pasa a la ficha **F-061**.

## 12 · Ficheros

**A crear** (`services/postventa-api/`): `domain/models/normalizacion.py`,
`interface_adapters/api/normalizacion.py`, `interface_adapters/api/tiempos.py`;
tests `test_f060_normalizacion_dominio.py`, `test_f060_repositorio_lote.py`,
`test_f060_pipeline_normalizacion.py`, `test_f060_normalizar_http.py`,
`test_f060_importar_normaliza.py`, `test_f060_tiempos.py`,
`test_f060_alcance_cerrado.py`, `test_f060_documentacion.py` y
`tests_bbdd/tests/test_f060_bbdd_lote.py`.

**A modificar**:

- `domain/ports/revision.py`: `ResultadoDelLote` y `registrar_lote`.
- `infrastructure/persistencia/repositorio_revision_pg.py`: `registrar_lote`.
- `application/pipelines/revision.py`: `ResultadoNormalizacion` y
  `normalizar_ubicaciones` (se añaden; lo demás igual).
- `interface_adapters/api/revision.py`: solo `listar_revision`, para la
  medición (§11.3).
- `interface_adapters/api/importar.py`: `importar_excel` (§9.2).
- `function_app.py`: la ruta nueva y su cabecera (veintiuna anónimas).
- Tests que enumeran rutas o las cuentan, ampliando sin quitar:
  `test_f010_endpoints_protegidos.py`, `test_f053_documentacion.py`.
- **Decisión del humano 2026-10-10** (excepción a «No se toca»):
  `test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`
  fija la lista exacta de los métodos de `RevisionPort`; se amplía, sin
  relajarlo, al conjunto exacto de **siete** (las seis de F-056 más
  `registrar_lote`). Ninguna otra aserción de F-056 cambia.
- **Excepción del Bloque 5 (T20; decisión del líder 2026-10-13 con el criterio que el humano aprobó en F-056: un test de documentación que fija una frase que cambia se amplía sin relajar y se declara)**: `test_f056_documentacion.py::test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas` («Los veintiuno», y «Los veinte» en `not in`) y `…::test_f056_r44_la_cabecera_dice_que_f056_lo_toco` (deja de exigir que F-056 sea la **última** feature de la cabecera de `INTEGRACION.md` y exige una cabecera bien formada que no retroceda, con F-056 y su despliegue constando, como hizo F-056 con el de F-036); fuera de F-036 y F-056, `test_f053_documentacion.py` (`CUENTA_VIGENTE`), `test_f012_documentacion.py` (`NUMERALES` hasta 21) y `test_f019_documentacion.py::test_f019_r32_…`. Ninguna otra aserción cambia; `tests/test_f060_alcance_cerrado.py` lo vigila función a función.
- `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` (R43) y, al desplegar,
  `azure-apps/postventa_incidencias.md`.
- Bloque 7: lo que diga el remedio elegido (§11.4).

**No se toca**: todos los `.sql`; `domain/models/revision.py`,
`importacion.py`, `plantilla_incidencias.py`, `equivalencias.py`;
`sentencias_revision.py`, `sentencias_bandeja.py`,
`repositorio_bandeja_pg.py`, `persistencia/fabrica.py` (salvo M-1/M-2);
`application/pipelines/paso_importacion.py`, `catalogo_obra.py`,
`plantilla.py`, `equivalencias.py`; `infrastructure/sigrid/*`;
`config/plantilla_incidencias.yaml`; `interface_adapters/api/bandeja.py`,
`plantilla.py`, `equivalencias.py`; los tests de F-036 y F-056;
`services/postventa-front/`; `infra/*` (salvo M-4).

## 13 · Tests

Sin red, sin base, sin IA, sin `.xlsx`; nombres `test_f060_rN_…`; datos
ficticios.

| R | Lo que fija además de lo obvio |
|---|---|
| R1–R5 | Cada fila de la tabla de §3; `casefold` frente a `lower` con un carácter que los distinga; NFD frente a NFC; blancos interiores, tildes y punto final → `sin_coincidencia`; dos valores con la misma clave → `ambigua`; el exacto gana aunque haya otro con la misma clave; el resultado es el valor de la lista, carácter a carácter |
| R6–R10 | La unidad **vigente**, no la importada; una ubicación válida en otra unidad no vale; las seis cifras del recuento y su suma; una `aprobada` y una `descartada` normalizables → `no_editables` y ninguna revisión; sin ubicación → no examinada como no exacta; los otros doce valores idénticos; la huella recalculada; la esperada |
| R11 | `validar_quien` con el correo del sistema → `PeticionDeRevisionInvalida` |
| R12–R16 | Conexión falsa: `FOR UPDATE` en orden fijo, una desactualizada se salta y las demás se escriben, `ROLLBACK` y 503 sin parámetros en el mensaje, lote vacío sin transacción, ningún `UPDATE`/`DELETE`/`TRUNCATE` |
| R17–R23 | Tope con 10.001 → error sin leer Sigrid; una lectura de ubicaciones; ensayo no llama al lote; dos ejecuciones → la segunda 0; tras normalizar, la fila del listado y el historial de R22 (con los dobles de F-056) |
| R24, R25 | Normalizar y aprobar → la candidata lleva el texto de Sigrid; sin normalizar → 409; editar con la variante → 400 |
| R26–R30 | Cada cuerpo malo → 400 sin construir adaptadores (también `"true"`, `1`, claves de más, sin `ensayo`); Sigrid antes que la base; errores de R28; `caplog` sin textos |
| R31–R35 | Con filas registradas, una llamada con el catálogo de la importación; con `ya_importado` o cero filas, ninguna; respuesta idéntica con y sin normalización (igualdad del diccionario); cada error de §5.1 → misma respuesta y un aviso con el tipo; ~~un `ValueError` sube~~ cualquier excepción al componer o ejecutar (también `ValueError` o un `AttributeError` de configuración) → misma respuesta y un aviso con su tipo (decisión del humano 2026-10-12) |
| R36 | Las claves de las tres respuestas de F-056 y la de la importación, iguales a las de la base fija |
| R37–R39 | Alcance con base fija: ningún `.sql` cambiado; ninguna ruta de escritura ni ventana; los ficheros de «No se toca» sin cambios; los tests de F-036 y F-056 sin tocar salvo los dos ampliados y el test del puerto de F-056 (decisión del humano 2026-10-10) |
| R40–R42 | Con reloj falso: los tramos y el cálculo; la línea con 200 y con error; el proxy devuelve lo mismo y relanza lo mismo; el orden de construcción; `caplog` sin correo, `oid` ni textos; la línea de F-056 intacta |
| R43 | Frases clave en `ARCHITECTURE.md` e `INTEGRACION.md` |

Los de F-056 que cuentan lecturas o construcciones por petición
(`test_f056_r46_…`) siguen en verde sin tocarse: la medición no construye ni
lee nada más.

## 14 · Riesgos y alternativas descartadas

1. **Comparar sin mayúsculas** (en vez de normalizar): descartado por el
   humano. Dejaría en lo aprobado y en el volcado el texto de la plantilla.
2. **Normalizar al importar** (opción a): no cubre lo importado (§4.1).
3. **Vigente calculado** (opción b): rompe la coherencia de F-056 (§4.1).
4. **Acción nueva `normalizar`**: el `CHECK` de `accion` no se puede ampliar
   con la guarda de DDL; y F-038 no la conocería.
5. **Normalizar al listar** (un `GET` que escribe): descartado; un `GET` no
   escribe, y el listado tiene que ser **más** rápido.
6. **Abortar el lote ante un conflicto**: una persona editando una fila
   impediría normalizar las otras 109.
7. **Riesgo: la ambigüedad**. Mitigado: no se elige nunca entre dos.
8. **Riesgo: Sigrid cambia la lista** después de normalizar. Lo normalizado
   puede volver a salir fuera de lista; la siguiente ejecución lo recoge. Una
   `aprobada` no se toca nunca.
9. **Riesgo: la importación tarda más**: una lectura de Sigrid y una
   transacción más. Se mide en el Bloque 6 con la próxima importación real.
10. **Riesgo: optimizar a ciegas**: por eso la medición va antes que el
    remedio (D-9).

## 15 · Decisiones y preguntas para el humano

| Id | Decisión propuesta | Recomendación |
|---|---|---|
| **D-1** | **Dónde**: una revisión `editar` del sistema en `revisiones_bandeja` (opción c de §4.1) | Sí |
| **D-2** | **Cuándo**: automáticamente tras cada importación que registra filas (mejor esfuerzo) **y** a demanda con `POST /api/revision/normalizar`. **Decisión del humano 2026-10-12: mejor esfuerzo = cualquier excepción de la normalización se registra por su tipo y no afecta a la importación** (§5.1) | Sí (la alternativa: solo a demanda) |
| **D-3** | **Qué coincide**: mayúsculas (`casefold`), blancos en los extremos y forma Unicode (NFC); no blancos interiores, ni tildes, ni puntuación; dos candidatos → no se normaliza | Sí |
| **D-4** | **Constancia sin DDL**: el `oid` y el correo de la revisión, el literal `sistema:normalizar_ubicacion`, que ninguna persona puede enviar | Sí (la alternativa: columna nueva y F-059 a `17_`) |
| **D-5** | Editar y aprobar **siguen exactos**: no normalizan al vuelo | Sí |
| **D-6** | Solo `nueva` y `editada`; nunca `aprobada`, `descartada`, `volcada` ni `en_duda` | Sí |
| **D-7** | Un lote por ejecución, en una transacción, con frescura por fila; las desactualizadas se saltan | Sí |
| **D-8** | `ensayo` obligatorio en el cuerpo, sin valor por defecto | Sí |
| **D-9** | Medir en producción antes de optimizar; el remedio se elige con el dato (§11.4) | Sí |
| **D-10** | Objetivo en caliente: máximo < 10 s (obligatorio), p50 < 3 s (deseable) | Sí |

| Id | Pregunta | Recomendación |
|---|---|---|
| **Q-1** | ¿La incidencia normalizada queda `editada` (verdad, sin tocar F-056) o debe seguir `nueva`? | `editada` |
| **Q-2** | ¿El literal `sistema:normalizar_ubicacion`, u otro (p. ej. `sistema`)? | Ese: dice la regla |
| **Q-3** | ¿El arranque en frío cuenta para los 10 s? | No: se mide y se informa aparte; «siempre lista» (M-4) es una decisión de coste |
| **Q-4** | ¿Normalizar también la forma Unicode (NFC)? | Sí: no es quitar tildes, es la misma letra escrita de dos formas |
| **Q-5** | Si el dato señala las conexiones y M-1 no basta, ¿se acepta mantener una conexión viva por proceso (M-2) en el servidor compartido? | Decidir con el dato |
| **Q-6** | ¿Puede lanzar la normalización cualquiera de `posventa-usuarios`? | Sí, como cualquier acción de revisión |
