<!-- specs/F-005-persistencia/design.md -->
# F-005 · Persistencia en el PostgreSQL compartido — Diseño técnico

> Encaja en `docs/ARCHITECTURE.md` (almacén de estado del pipeline) y en
> `docs/CONVENTIONS.md`. Servicio: **`services/postventa-api/`** y solo ese.
>
> **Ni un dato real.** Todos los ejemplos son inventados y van marcados.
> Los partes llevan DNI y observaciones manuscritas de clientes: eso vive en
> la base de datos, **nunca** en el repositorio, ni en fixtures, ni en logs.

## 0 · Dónde está el riesgo de esta feature

No está en el modelo de datos. Está en que **`psql-albaranes-rs9k2` es un
servidor compartido con producción ajena**. Lo que se ha leído en
`azure-apps/` antes de diseñar nada:

| Hecho | Fuente | Consecuencia para F-005 |
|---|---|---|
| El aislamiento del ecosistema es **una base de datos por proyecto** (`albaranes`, `partes`, y `sigrid_dm` diseñada), todas en el mismo servidor | `azure-apps/albaranes.md` §1, `partes.md` §4, `datamart_seg_anual.md` | Pedimos base propia `postventa`, y además esquema propio `postventa` dentro de ella (§2) |
| El servidor es `Standard_B1ms`: 1 vCPU, 2 GB de RAM, 32 GB de disco **compartidos entre todos** | `datamart_seg_anual.md` | Sin BLOBs, sin JSON crudo gigante, conexiones limitadas (§5) |
| El almacenamiento **solo crece, nunca decrece**, y el PITR restaura el **servidor entero** | `datamart_seg_anual.md` | No se puede volver atrás nuestra base sin arrastrar `albaranes` y `partes`. Lo que escribimos, escrito queda |
| **2026-08-09: disco al 93,4 % y servidor en solo-lectura diez minutos**, por el build de otro proyecto | `datamart_seg_anual.md` | Es el precedente real. Nuestra regla dura: los PDF no entran en la base (R12) |
| `albaranes` y `partes` trabajan contra el esquema **`public`** de su base | `albaranes.md` §1, `partes.md` §4 | Nosotros **no**: esquema nominado `postventa`, y `search_path` sin `public` (R8), para que un `CREATE TABLE` sin cualificar no pueda aterrizar en el sitio equivocado |
| El patrón «DDL idempotente al arranque» de **sv3** es: el servicio dueño del esquema aplica al arrancar `CREATE ... IF NOT EXISTS` + `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`, porque `create_all()` no añade columnas ni índices a una tabla que ya existe | `albaranes.md` §5.3, `partes.md` §4 | Se copia **el patrón**, no el mecanismo (§3, decisión D2) |
| En `partes`, el DDL complementario **se genera del propio ORM** porque las dos listas manuales anteriores «acabaron incompletas y distintas entre servicios» | `partes.md` §4 | Ese problema nace de tener **dos servicios** escribiendo el mismo esquema. Aquí solo hay uno (§3) |
| En `albaranes`, una tabla la crean dos servicios a la vez: «gana el que arranque primero», acoplamiento documentado | `albaranes.md` §3 | Ahí está la carrera de arranque. La cerramos con bloqueo consultivo (R10) |

Y las dos reglas duras de `CLAUDE.md` que gobiernan el diseño entero:

- **PROHIBIDO ejecutar DDL fuera del esquema propio.** Se convierte en código:
  una guarda que valida el DDL **antes de abrir la conexión** (§4.1) y falla
  el arranque si una sola sentencia se sale.
- **PROHIBIDO tocar nada a nivel de servidor.** Misma guarda: lista negra de
  verbos (R6). Ni `CREATE EXTENSION` —por eso los UUID se generan en Python y
  no con `gen_random_uuid()`—, ni `CREATE DATABASE` (R7), ni `GRANT`.

## 1 · Qué entra, qué sale y qué se queda fuera

**Entra**: `ParteTroceado` (F-002), `ExtraccionParte` (F-003),
`ResultadoValidacion` (F-004), y los hechos de archivo y de cierre que
producirán F-006 y F-009.

**Sale**: filas en una base propia, y una cola de validación humana
consultable.

**Se queda fuera, y consta por escrito para que nadie lo lea como un olvido:**

| Fuera de F-005 | Dónde va | Por qué |
|---|---|---|
| Ejecutar el pipeline entero y decidir *cuándo* se guarda | F-006/F-007 | F-005 entrega puertos y adaptador; quien los compone es el punto de entrada |
| Subir a SharePoint | F-006 | F-005 solo guarda la **traza** del archivo |
| Hablar con Sigrid | F-008/F-009 | F-005 solo guarda la **traza** del cierre |
| Pintar la cola de validación humana | F-007/F-011 | Es front |
| Interpretar las observaciones | F-016 | F-005 las guarda literales, no las juzga |
| Crear la base de datos y el rol | Infraestructura (§8) | R7: un `CREATE DATABASE` desde el arranque de una app es exactamente el gesto que la regla dura prohíbe en un servidor ajeno |
| Endpoints HTTP de la cola | F-007 | El `acceptance` no los pide y F-005 no necesita ninguno para probarse |

### Precondición dura: F-004 mergeada en `dev`

Los puertos de F-005 hablan `ResultadoValidacion`, `Veredicto`, `Destino`,
`CodigoMotivo` y `ClasificacionFirma`, que **hoy solo existen en la rama
`feature/F-004-validacion`**. F-005 **no se implementa hasta que F-004 esté
mergeada en `dev`** y esta rama rebasada sobre ella (T1 de `tasks.md`).

Se ha descartado a propósito la alternativa de inventar un modelo gemelo de
persistencia (`RegistroValidacion`) para poder empezar antes: dos modelos del
mismo concepto divergen siempre, y el `acceptance` de F-004 ya declara que la
cola la guarda F-005. **Si F-004 cambiara su contrato, F-005 se rehace en esa
parte.** Ver riesgo 1 (§9).

---

## 2 · Dónde vive el dato

```
Servidor  psql-albaranes-rs9k2      (COMPARTIDO — no se toca nada suyo)
   └── Base  postventa              (propia; la crea el humano, una vez)
         └── Esquema  postventa     (propio; lo crea el DDL de la app)
               ├── remesas
               ├── partes
               ├── validaciones
               ├── archivos
               ├── cierres
               └── preferencias_usuario
```

**Base propia y esquema nominado, las dos cosas.** La base propia es lo que
hace el ecosistema (`albaranes`, `partes`, `sigrid_dm`) y es el aislamiento
que de verdad separa proyectos. El esquema nominado —en vez del `public` que
usan los demás— es cinturón sobre tirantes: con `search_path` fijado a
`postventa` (R8), una sentencia sin cualificar **no puede** aterrizar en
`public` ni por descuido ni por copiar-pegar.

`docs/ARCHITECTURE.md` dice «schema propio» y el ecosistema dice «base
propia». No se contradicen: se cumplen las dos. **Cuál de las dos exige el
humano es la decisión abierta D1** (§10).

### Las tablas

Tipos: `text` en vez de `varchar(n)` (en PostgreSQL no hay diferencia de
rendimiento y una longitud inventada solo sirve para romperse), `timestamptz`
para los instantes, `jsonb` para las listas cortas. Los UUID se generan en
Python (R7/R6: no queremos `CREATE EXTENSION pgcrypto`).

#### `remesas` — una subida

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `uuid` PK | generado en Python |
| `nombre_origen` | `text NOT NULL` | nombre del fichero o del ZIP subido |
| `recibida_at_utc` | `timestamptz NOT NULL` | |
| `num_partes` | `integer NOT NULL DEFAULT 0` | lo que devolvió el troceado |
| `avisos` | `jsonb NOT NULL DEFAULT '[]'` | los de la ingesta |
| `usuario_oid` | `text` | **dato personal seudónimo** (§6) |

#### `partes` — la unidad de trabajo

`hash_parte` es la **clave primaria**: es la promesa de F-002 («el parte
extraído de la remesa y el mismo parte llegado suelto en un ZIP dan la misma
huella») convertida en restricción de base de datos. Ahí está R13–R16.

| Grupo | Columnas | Notas |
|---|---|---|
| Identidad | `hash_parte text PRIMARY KEY` | clave de deduplicación |
| Procedencia | `remesa_id uuid NOT NULL REFERENCES postventa.remesas(id)`, `origen text`, `paginas_origen integer[] NOT NULL`, `modo_deteccion text NOT NULL` | `remesa_id` apunta a la **última** remesa que lo produjo |
| Vida | `primera_vez_at_utc timestamptz NOT NULL`, `actualizado_at_utc timestamptz NOT NULL`, `reprocesos integer NOT NULL DEFAULT 0` | R15 |
| Campos leídos | `promocion`, `codigo_obra`, `unidad`, `numero_incidencia`, `fecha_servicio`, `descripcion`, `dni_cliente`, `observaciones`, `numero_pagina` — todas `text` | los nueve de `CAMPOS_DEL_PARTE`, R18 |
| Confianzas | las nueve anteriores con sufijo `_confianza_pct`, `integer NOT NULL DEFAULT 0` | R18 |
| Traza IA | `ia_proveedor`, `ia_modelo`, `prompt_key`, `prompt_version`, `prompt_huella` — `text` | R19 |
| Avisos | `avisos_extraccion jsonb NOT NULL DEFAULT '[]'` | |

Índices: `numero_incidencia`, `codigo_obra`, `remesa_id`.

**Los nueve campos van como columnas, no como un `jsonb`.** Son un contrato
cerrado y nombrado (`CAMPOS_DEL_PARTE`), la cola humana y el front van a
filtrar por ellos, y es lo que ya hace el ecosistema (`parte_documents` en
`partes`). Un `jsonb` escondería del `information_schema` justo lo que hay que
poder auditar: qué columnas guardan dato personal.

**`fecha_servicio` es `text`, no `date`.** F-003 devuelve lo que el modelo lee
del papel, y sus propios tests parametrizan formatos distintos para el mismo
día. Convertir a `date` en la capa de persistencia sería inventar una
interpretación y perder el literal. Quien normalice fechas, que lo haga en su
feature y en otra columna.

**No hay `raw_extraccion_json`**, a diferencia de `albaranes`. Duplicaría en
un blob de texto el DNI y las observaciones que ya están en sus columnas, y
engordaría un disco compartido de 32 GB que ya se llenó una vez. La
trazabilidad la da la traza IA (R19).

#### `validaciones` — 1:1 con el parte (F-004)

| Columna | Tipo | Notas |
|---|---|---|
| `hash_parte` | `text PRIMARY KEY REFERENCES postventa.partes(hash_parte) ON DELETE CASCADE` | R17: la PK es lo que impide acumular |
| `veredicto` | `text NOT NULL CHECK (veredicto IN ('apto','no_apto'))` | |
| `destino` | `text NOT NULL CHECK (destino IN ('archivo_y_cierre','cola_validacion_humana','revision_manual'))` | los **dos destinos distintos** de un parte no apto |
| `clasificacion_firma` | `text NOT NULL CHECK (... IN ('humana','marca_simple','casilla_vacia','ilegible'))` | las cuatro etiquetas |
| `motivos` | `jsonb NOT NULL DEFAULT '[]'` | `[{"codigo": "...", "texto": "..."}]`, **en orden** (R20) |
| `avisos` | `jsonb NOT NULL DEFAULT '[]'` | |
| `validado_at_utc` | `timestamptz NOT NULL` | |

Índice parcial de la cola:
`CREATE INDEX IF NOT EXISTS ix_validaciones_cola ON postventa.validaciones (validado_at_utc) WHERE destino = 'cola_validacion_humana';`

**Las observaciones no se copian aquí (R21).** `ResultadoValidacion` las
transporta, pero su origen es `ExtraccionParte`, que ya está en `partes`. Una
segunda copia de texto manuscrito de un cliente es superficie de exposición
gratuita, y dos copias divergen. La lectura de la cola (§4.4) las trae de
`partes` con un `JOIN`. El invariante «la transcripción del resultado es la
del parte» queda vigilado por un test (R21).

Los valores de los `CHECK` **se generan de los `Enum` de F-004**, no se
escriben a mano en el `.sql`: ver §4.1, `ddl.py`. Una etiqueta nueva en el
dominio que no llegue a la base es un fallo que se ve en la suite, no en
producción.

#### `archivos` — traza del archivo en SharePoint (F-006)

`hash_parte` PK (FK a `partes`, `CASCADE`), `nombre_fichero`, `carpeta`,
`drive_id`, `item_id`, `web_url`, `estado text CHECK IN ('pendiente',
'archivado','error')`, `motivo`, `intentos integer NOT NULL DEFAULT 0`,
`archivado_at_utc`. La PK por `hash_parte` es lo que hace verdad el
`acceptance` de F-006 «subir dos veces el mismo parte no genera un duplicado»
(R23).

#### `cierres` — traza del cierre en Sigrid (F-009)

`hash_parte` PK (FK a `partes`, `CASCADE`), `numero_incidencia text NOT NULL`,
`estado text CHECK IN ('pendiente','dry_run_ok','cerrado','error',
'ya_cerrada')`, `estado_origen_sigrid`, `estado_destino_sigrid`,
`dry_run_at_utc`, `cerrado_at_utc`, `confirmado_por text` (**seudónimo**, §6),
`motivo`, `intentos integer NOT NULL DEFAULT 0`.

`estado_origen_sigrid` y `estado_destino_sigrid` guardan **el código que se
resolvió contra `conest` en ejecución**, como traza de lo que se hizo. No es
configuración ni se lee para decidir: `CHECKPOINTS.md` C3 prohíbe hardcodear
un estado de Sigrid y esto no lo hace, lo registra a posteriori.

`estado = 'cerrado'` es **terminal** (R25): el repositorio no lo pisa.

#### `preferencias_usuario`

`usuario_oid text PRIMARY KEY` (**seudónimo**, §6), `auto_cierre boolean NOT
NULL DEFAULT false`, `actualizado_at_utc timestamptz NOT NULL`. Revocar es
poner `auto_cierre = false` con su marca de tiempo (R28): un booleano y una
fecha bastan, y así no hay dos maneras de estar revocado.

**Se guarda el `oid` de Entra, nunca el correo ni el nombre.** Es un
identificador opaco, sirve igual para la preferencia, y deja fuera de la base
un dato personal que no hace falta.

---

## 3 · «DDL idempotente al arranque, como hace sv3»: qué se copia y qué no

**Se copia el patrón**: el servicio dueño del esquema aplica, al arrancar,
todo su DDL en forma idempotente, sin herramienta de migraciones, de modo que
un despliegue nuevo y uno viejo convergen solos.

**No se copia el mecanismo.** sv3 y `partes` generan el DDL desde su ORM de
SQLAlchemy. Aquí no, por tres razones, en orden de peso:

1. **`docs/CONVENTIONS.md` es normativo y dice otra cosa**: «Un fichero por
   unidad lógica, numerado `NN_nombre.sql` dentro de su capa. Idempotente:
   `CREATE ... IF NOT EXISTS`». El reviewer valida contra ese documento.
2. **El problema que obligó a generar el DDL del ORM aquí no existe.** En
   `partes` lo causaron **dos servicios** (sv3 y sv4) escribiendo el mismo
   esquema, con listas manuales que «acabaron incompletas y distintas». En
   `postventa-incidencias` hay **un solo servicio** y un solo dueño.
3. **En un servidor compartido, el DDL tiene que poder leerse.** Un `.sql` que
   cabe en una pantalla se revisa antes de aplicarlo contra la base que
   sostiene la producción de otros dos proyectos. El DDL que emerge de un ORM,
   no.

Y no arrastramos SQLAlchemy: se usa **psycopg 3** con SQL escrito (§7).

### El agujero de las puertas de rigor, y cómo se tapa

`harness/alcance.py` filtra el diff a ficheros **`.py`**: un `.sql` **escapa
por completo** a la campaña de mutación y a la puerta de cobertura. Con
`rigor: critico` y cero supervivientes, poner el DDL en `.sql` lo dejaría sin
vigilancia automática — justo el fichero más peligroso de la feature.

Se tapa así: **el DDL vive en `.sql` (convención) y todo lo que lo interpreta
vive en `.py` (vigilancia).** `ddl.py` (§4.1) carga los ficheros, los ordena,
los trocea en sentencias y los **valida**; sus tests leen los `.sql` reales y
además ejemplos hostiles inventados. Un mutante en el validador se muere
porque algún test deja de rechazar lo que debe rechazar, o deja de aceptar el
DDL real. El `.sql` no se muta, pero **no puede cambiar sin que el validador
lo mire**.

---

## 4 · Ficheros

### 4.1 A crear

#### Dominio (puro: ni `psycopg`, ni SQL, ni HTTP)

**`services/postventa-api/domain/models/persistencia.py`**

```python
@dataclass(frozen=True)
class RegistroRemesa:
    id: str                       # UUID en texto, generado en aplicación
    nombre_origen: str
    recibida_at_utc: datetime
    num_partes: int
    avisos: tuple[str, ...] = ()
    usuario_oid: str | None = None   # DATO PERSONAL seudónimo

class EstadoArchivo(str, Enum):
    PENDIENTE = "pendiente"
    ARCHIVADO = "archivado"
    ERROR = "error"

class EstadoCierre(str, Enum):
    PENDIENTE = "pendiente"
    DRY_RUN_OK = "dry_run_ok"
    CERRADO = "cerrado"
    ERROR = "error"
    YA_CERRADA = "ya_cerrada"

@dataclass(frozen=True)
class TrazaArchivo:
    hash_parte: str
    estado: EstadoArchivo
    nombre_fichero: str | None = None
    carpeta: str | None = None
    drive_id: str | None = None
    item_id: str | None = None
    web_url: str | None = None
    motivo: str | None = None
    archivado_at_utc: datetime | None = None

@dataclass(frozen=True)
class TrazaCierre:
    hash_parte: str
    numero_incidencia: str
    estado: EstadoCierre
    estado_origen_sigrid: str | None = None
    estado_destino_sigrid: str | None = None
    confirmado_por: str | None = None      # DATO PERSONAL seudónimo
    motivo: str | None = None
    dry_run_at_utc: datetime | None = None
    cerrado_at_utc: datetime | None = None

@dataclass(frozen=True)
class PreferenciasUsuario:
    usuario_oid: str                        # DATO PERSONAL seudónimo
    auto_cierre: bool
    actualizado_at_utc: datetime

@dataclass(frozen=True)
class EntradaCola:
    """Un parte esperando decisión humana, con las pruebas delante."""
    hash_parte: str
    codigo_obra: str | None
    numero_incidencia: str | None
    observaciones: str | None               # DATO PERSONAL
    confianza_observaciones: int
    clasificacion_firma: str
    motivos: tuple[tuple[str, str], ...]
    validado_at_utc: datetime

class ResultadoGuardado(str, Enum):
    CREADO = "creado"
    ACTUALIZADO = "actualizado"
    SIN_CAMBIOS = "sin_cambios"     # R25: el cierre terminal no se pisa
```

**`services/postventa-api/domain/ports/persistencia.py`** — dos `Protocol`,
con el mismo estilo que los cuatro puertos que ya existen (sufijo `Port`,
kwargs-only, docstring que declara la excepción de dominio):

```python
class RepositorioPartesPort(Protocol):
    def guardar_remesa(self, *, remesa: RegistroRemesa) -> ResultadoGuardado: ...
    def guardar_parte(
        self, *, parte: ParteTroceado, extraccion: ExtraccionParte,
        remesa_id: str, ahora: datetime,
    ) -> ResultadoGuardado: ...
    def guardar_validacion(
        self, *, resultado: ResultadoValidacion, ahora: datetime
    ) -> ResultadoGuardado: ...
    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado: ...
    def guardar_cierre(self, *, traza: TrazaCierre) -> ResultadoGuardado: ...
    def cola_validacion_humana(self, *, limite: int) -> tuple[EntradaCola, ...]: ...

class RepositorioPreferenciasPort(Protocol):
    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario: ...
    def guardar_preferencias(self, *, preferencias: PreferenciasUsuario) -> ResultadoGuardado: ...
```

`guardar_parte` recibe `ParteTroceado` **sin sus bytes** en lo que persiste:
el adaptador toma de él `hash`, `origen`, `paginas_origen` y `modo_deteccion`,
y **nunca** `contenido` (R12).

**`services/postventa-api/domain/models/errores.py`** *(modificar)* — errores
nuevos con la forma que ya usan todos: `__init__(self, motivo: str)` y
atributo `.motivo`.

```python
class ErrorDePersistencia(Exception): ...        # raíz
class DdlInseguro(ErrorDePersistencia): ...      # R5, R6
class DdlNoPermitidoAqui(ErrorDePersistencia): ...  # R11
class PersistenciaNoDisponible(ErrorDePersistencia): ...
class ConfiguracionPgIncompleta(ErrorDePersistencia): ...
```

#### Infraestructura

**`infrastructure/persistencia/sql/01_esquema.sql`** — `CREATE SCHEMA IF NOT
EXISTS postventa;` y nada más.
**`.../02_remesas.sql`**, **`.../03_partes.sql`**, **`.../04_validaciones.sql`**,
**`.../05_archivos.sql`**, **`.../06_cierres.sql`**,
**`.../07_preferencias.sql`** — una unidad lógica por fichero, cabecera con
qué construye, todas las sentencias `IF NOT EXISTS` y **cualificadas con
`postventa.`**.

El nombre del esquema aparece literal en los `.sql`. Si el humano configura
otro (`PG_SCHEMA`), `ddl.py` lo sustituye por el configurado **en el mismo
paso en que valida** que no queda ninguna referencia sin cualificar: un solo
sitio, una sola pasada.

**`infrastructure/persistencia/ddl.py`** — puro, sin `psycopg`. Es la guarda.

```python
VERBOS_PROHIBIDOS: tuple[str, ...]   # R6
TIPOS_PROHIBIDOS: tuple[str, ...]    # R12: bytea, lo, oid grande

def ficheros_ddl(directorio: Path) -> tuple[Path, ...]:
    """Los NN_*.sql en orden lexicográfico ascendente (R1)."""

def sentencias(texto: str) -> tuple[str, ...]:
    """Trocea por ';', respetando comentarios y $$...$$."""

def validar(sentencia: str, *, esquema: str) -> None:
    """DdlInseguro si toca algo fuera de `esquema` o usa un verbo prohibido."""

def cargar_ddl(directorio: Path, *, esquema: str) -> tuple[str, ...]:
    """Todas las sentencias, sustituidas al esquema pedido y validadas."""

def valores_check(nombres: Iterable[str]) -> str:
    """La lista de un CHECK a partir de un Enum del dominio."""
```

`validar` rechaza: sentencia cuyo objeto no empiece por `<esquema>.`, verbo de
la lista negra, aparición de `public.`, `bytea`/large object, y `CREATE`/
`ALTER` sin `IF NOT EXISTS` cuando el verbo lo admite (R3). Falla **antes de
que exista conexión alguna**, en la carga del módulo de arranque.

**`infrastructure/persistencia/conexion.py`** — psycopg 3.

```python
HOSTS_LOCALES: frozenset[str] = frozenset({"localhost", "127.0.0.1", "::1"})

def es_host_local(host: str) -> bool: ...
def dsn_desde_ajustes(ajustes: Ajustes) -> str:
    """Sin la contraseña en el texto: va aparte. Nunca se registra (R29)."""
def sentencias_de_sesion(ajustes: Ajustes) -> tuple[str, ...]:
    """search_path solo al esquema, application_name y los tres timeouts (R8, R9)."""
```

**`infrastructure/persistencia/arranque.py`**

```python
CLAVE_ADVISORY_LOCK: int      # constante fija del proyecto

def puede_aplicar_ddl(ajustes: Ajustes) -> None:
    """DdlNoPermitidoAqui si entorno == 'local' y el host no es local (R11)."""

def asegurar_esquema(conexion, *, ajustes: Ajustes) -> int:
    """Aplica el DDL bajo pg_advisory_lock y devuelve nº de sentencias (R2, R10)."""
```

**`infrastructure/persistencia/sentencias.py`** — puro. Construye el SQL de
cada operación: los `INSERT ... ON CONFLICT (hash_parte) DO UPDATE SET ...`
(R14–R17), el `SELECT` de la cola con su `JOIN` a `partes` (R22), y el
`UPDATE` de cierre con `WHERE estado <> 'cerrado'` (R25). Devuelve
`(sql, parametros)`; **nunca** interpola valores en el texto.

**`infrastructure/persistencia/mapeo.py`** — puro. Fila ↔ modelo de dominio, y
`ExtraccionParte` → las 18 columnas de campos y confianzas, iterando
`CAMPOS_DEL_PARTE` (R18): si mañana hay un décimo campo, el mapeo se entera.

**`infrastructure/persistencia/repositorio_pg.py`** — implementa los dos
puertos. Es delgado a propósito: pide el SQL a `sentencias`, ejecuta, y pasa
las filas a `mapeo`.

**`infrastructure/persistencia/fabrica.py`** — `construir_repositorio(ajustes)`,
copiando el patrón de `infrastructure/llm/fabrica.py`; levanta
`ConfiguracionPgIncompleta` si falta host, base, usuario o contraseña.

#### Aplicación

**`application/pipelines/paso_persistencia.py`**

```python
def paso_persistencia(
    ctx: ContextoParte, repositorio: RepositorioPartesPort, *,
    remesa_id: str, ahora: datetime,
) -> ContextoParte: ...
```

Encaja en el patrón que el docstring de `contexto_parte.py` ya anuncia. Habla
con el **puerto**, jamás con el adaptador (R30).

#### Tests · suite por defecto (sin red, sin BBDD)

En `services/postventa-api/tests/`:
`test_f005_ddl_seguro.py`, `test_f005_ddl_idempotente_texto.py`,
`test_f005_sentencias.py`, `test_f005_mapeo.py`, `test_f005_repositorio.py`,
`test_f005_arranque.py`, `test_f005_conexion.py`, `test_f005_preferencias.py`,
`test_f005_arquitectura.py`, y el doble `utiles_pg.py`.

#### Tests · base efímera (fuera de la suite por defecto)

En `services/postventa-api/tests_bbdd/`: `conftest.py`,
`test_f005_bbdd_ddl_idempotente.py`, `test_f005_bbdd_reproceso.py`,
`test_f005_bbdd_aislamiento.py`.

#### Infraestructura de despliegue y verificación

**`infra/crear_base_postventa.ps1`** — crea la base y el rol **una vez**, a
mano, con confirmación explícita. No lo llama la aplicación (R7).
**`infra/pruebas_bbdd_efimera.ps1`** — levanta la PostgreSQL desechable,
lanza la suite de base de datos y la tira (§8).

#### Documento del ecosistema

**`docs/INTEGRACION.md`** — nuevo. Ver §11.

### 4.2 A modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | los campos `pg_*` de §5 |
| `services/postventa-api/.env.example` | las variables `PG_*`, **sin valores** |
| `services/postventa-api/local.settings.json.example` | ídem |
| `services/postventa-api/requirements.txt` | `psycopg[binary]>=3.1,<4.0` |
| `domain/models/errores.py` | los cinco errores de §4.1 |
| `docs/ARCHITECTURE.md` | la fila de PostgreSQL: base propia, esquema propio, y la regla de que los PDF no entran en la base |

### 4.3 Ficheros que NO se tocan (los que tientan)

- **`tests/conftest.py`.** La guarda `sin_red` de F-003 se queda **exactamente
  como está**, y el test que comprueba que muerde
  (`test_f003_r19_...`) sigue pasando sin tocar una aserción. Aflojarla para
  que los tests de F-005 puedan conectar sería destruir la mejor red del
  proyecto. La suite de base efímera vive en **otro directorio** justamente
  para no tener que hacerlo (§7).
- **`harness/init.sh`, `harness/rigor.json`, `harness/servicios.json`,
  `harness/alcance.py`.** Ninguna puerta del arnés se retoca para que esta
  feature pase. Si algo del arnés estorba, se dice, no se afloja.
- **`tests/test_f003_arquitectura.py`.** No se le añade `psycopg` a su lista:
  la comprobación de F-005 va en `test_f005_arquitectura.py`, para que un
  fallo diga de qué feature es.
- **F-002, F-003 y F-004**: ni sus modelos, ni sus pasos, ni sus adaptadores,
  ni `config/prompts.yaml`. F-005 lee sus resultados y los guarda.
- **`services/postventa-front/`** — es F-007.
- **`muestras/`** y cualquier PDF real.

---

## 5 · Configuración

Campos nuevos de `Ajustes`, con el estilo que ya hay (nombre en español,
`validation_alias` en mayúsculas, nombres de variable **iguales a los que usa
el ecosistema** para que quien despliegue no aprenda dos vocabularios):

| Campo | Alias | Por defecto | Notas |
|---|---|---|---|
| `pg_host` | `PG_HOST` | `None` | |
| `pg_puerto` | `PG_PORT` | `5432` | |
| `pg_base` | `PG_DB` | `postventa` | |
| `pg_usuario` | `PG_USER` | `None` | |
| `pg_password` | `PG_PASSWORD` | `None` | **secreto**; opcional a propósito |
| `pg_esquema` | `PG_SCHEMA` | `postventa` | |
| `pg_sslmode` | `PG_SSLMODE` | `require` | Azure Flexible Server lo exige |
| `pg_max_conexiones` | `PG_MAX_CONEXIONES` | `4` | §9, riesgo 3 |
| `pg_statement_timeout_s` | `PG_STATEMENT_TIMEOUT_S` | `30` | |
| `pg_lock_timeout_s` | `PG_LOCK_TIMEOUT_S` | `5` | |

**Los tres campos sin valor por defecto son opcionales (`None`), no
obligatorios.** Es el razonamiento que ya está escrito en el docstring de
`gemini_api_key`: si fueran obligatorios, `/health` dejaría de arrancar sin
base de datos y la suite entera necesitaría credenciales falsas en el
entorno. Quien los exige es la **fábrica**, cuando de verdad hace falta.

`.env.example` y `local.settings.json.example` llevan los **nombres**, nunca
los valores. En Azure, `PG_PASSWORD` va por referencia a Key Vault.

---

## 6 · Datos personales: qué columna guarda qué

Los partes llevan DNI y observaciones manuscritas de clientes. **Esto es lo
único que hay que saber para no versionar nada indebido, para no registrarlo
en logs y para responder mañana a un ejercicio de derechos.**

> **D2, resuelta el 2026-08-19: el DNI del cliente SÍ se persiste**, en
> `partes.dni_cliente`. Por eso esta sección no es informativa: es el
> **contrato de salvaguardas** que acompaña a esa decisión. Hay dato personal
> directo confirmado en una base de datos compartida por cuatro proyectos, así
> que cada regla de abajo tiene su requisito EARS (R37–R40) y su verificación.

| Columna | Qué contiene | Grado |
|---|---|---|
| `partes.dni_cliente` | DNI manuscrito del cliente | **Personal directo** |
| `partes.observaciones` | texto manuscrito del cliente sobre la reparación | **Personal directo** |
| `partes.descripcion` | descripción de la incidencia; puede citar a personas | **Personal posible** |
| `partes.promocion`, `partes.unidad` | localizan la vivienda concreta de una persona | **Personal indirecto** |
| `remesas.usuario_oid`, `cierres.confirmado_por`, `preferencias_usuario.usuario_oid` | identificador opaco de Entra ID de un empleado | **Personal seudónimo** |

Reglas que se aplican, cada una con su requisito y su verificación, y que el
reviewer puede comprobar una por una:

| # | Regla | Requisito | Cómo se comprueba |
|---|---|---|---|
| 1 | **Nunca en el repositorio** | R38 | ni en esta spec, ni en fixtures, ni en ejemplos, ni en `docs/`, ni en `tests_bbdd/`. Los ejemplos de los tests son **inventados** y van marcados como tales en el propio fichero. `tests/test_f005_repo_sin_datos_personales.py` barre los ficheros de la feature buscando un patrón de DNI español y falla si encuentra alguno (T19 bis) |
| 2 | **Nunca en el log** | R29, R37 | el logging estructurado de un parte registra `hash_parte`, estado y confianzas; de un campo manuscrito, como mucho, **si venía vacío** y su confianza. `tests/test_f005_logs_sin_datos_personales.py` captura el logger con un DNI y unas observaciones **inventados** y comprueba que ninguno de los dos valores aparece en la salida; el test falla si se quita el saneado (T19) |
| 3 | **Nunca duplicados en otra tabla** | R21, R39 | el DNI vive **solo** en `partes.dni_cliente` y la transcripción **solo** en `partes.observaciones`. Ninguna otra tabla los copia: `validaciones` los recupera con un `JOIN`. Un test comprueba que ninguna otra tabla del DDL declara una columna con ese nombre o equivalente |
| 4 | **El PDF no entra en la base** | R12, R40 | el DDL no declara ni una columna binaria; el PDF vive en SharePoint y de él se guardan solo metadatos y hash. Menos copias del DNI, menos disco compartido gastado. Lo vigila el validador de `ddl.py`, que ya rechaza `bytea` y large objects |
| 5 | **De los empleados se guarda el `oid`** | R27 | identificador opaco de Entra ID, nunca el correo ni el nombre |

Las reglas 1 a 4 son la contrapartida de **D2**: el humano decidió guardar el
DNI, y a cambio el dato queda **en un único sitio, sin salir nunca de la base**
—ni al log, ni al repositorio, ni a un segundo blob—.

*(Ejemplo inventado de cómo se ve una fila, para que se entienda la forma —
ningún dato es real: `hash_parte='9f2b…', codigo_obra='0000',
numero_incidencia='XX00.00 - 0000', observaciones='texto de ejemplo
inventado', dni_cliente=NULL`.)*

---

## 7 · Cómo se prueba: la tensión, resuelta por escrito

El `acceptance` exige **«tests contra base efímera, nunca contra el servidor
compartido»**. `CLAUDE.md` y `docs/CONVENTIONS.md` exigen que **los unit tests
no toquen red ni BBDD**. Y F-003 dejó en `tests/conftest.py` una guarda de
sesión que parchea `socket.socket.connect`, con un test que comprueba que
muerde: **cualquier conexión desde la suite por defecto es imposible, no
improbable**.

No es una contradicción una vez que se separa qué demuestra cada cosa.

### 7.1 Lo que se prueba **sin** base de datos (suite por defecto)

Es la mayor parte, y es donde se juegan la cobertura y la mutación.

| Qué | Cómo | Requisitos |
|---|---|---|
| El DDL real no se sale del esquema ni usa verbos de servidor | `ddl.validar` sobre los `.sql` **reales** del repositorio, más ejemplos hostiles inventados que **deben** ser rechazados | R5, R6, R12 |
| Todas las sentencias del DDL real son idempotentes | inspección del texto: `IF NOT EXISTS` / `OR REPLACE` en cada una | R3 |
| Los `CHECK` cubren exactamente los `Enum` de F-004 | comparación contra `Destino`, `Veredicto`, `ClasificacionFirma` | R20 |
| El orden de aplicación es el lexicográfico | `ficheros_ddl` sobre un directorio de prueba | R1 |
| El SQL de upsert y el de la cola son los esperados | `sentencias.*` devuelve `(sql, parametros)` comparables | R14, R17, R22, R25 |
| El mapeo fila ↔ dominio no pierde ni inventa nada | ida y vuelta sobre `ExtraccionParte` y `ResultadoValidacion` inventados | R18, R19, R20 |
| El repositorio ejecuta lo que debe, en el orden que debe | **doble de conexión** en `tests/utiles_pg.py`: un objeto que imita la DBAPI (`cursor()`, `execute()`, `fetchall()`, `commit()`), graba lo ejecutado y devuelve filas preparadas | R14–R17, R22–R28 |
| El arranque se niega a aplicar DDL desde local contra un host remoto | `puede_aplicar_ddl` con ajustes inventados | R11 |
| La sesión fija `search_path` sin `public` y los tres timeouts | `sentencias_de_sesion` | R8, R9 |
| El DDL se aplica una sola vez por proceso, bajo bloqueo consultivo | doble de conexión: se comprueba el `pg_advisory_lock`, el `unlock` en `finally` y que la segunda llamada no reejecuta | R2, R10 |
| Dominio y aplicación no importan `psycopg` ni `infrastructure` | AST sobre el servicio, como hace `test_f003_arquitectura.py` | R30, R31 |
| Ningún log lleva DNI ni observaciones | captura del logger con valores inventados | R29 |

**El doble de conexión es la pieza clave.** Deja al adaptador cubierto y
mutado sin abrir un socket, que es lo que hace compatible «unit tests sin
BBDD» con «cobertura ≥ 80 % de las líneas cambiadas» y «cero supervivientes».

Lo que un doble **no** puede demostrar, y por eso existe §7.2: que el SQL es
PostgreSQL **válido** y que aplicarlo dos veces de verdad no falla.

### 7.2 Lo que exige una base efímera

Suite aparte, en **`services/postventa-api/tests_bbdd/`**:

- `test_f005_bbdd_ddl_idempotente.py` — aplica el DDL dos veces seguidas y
  compara el `information_schema` (tablas, columnas, índices, restricciones)
  entre la primera y la segunda pasada. Es el `acceptance` 1, literal.
- `test_f005_bbdd_reproceso.py` — guarda la misma remesa dos veces y comprueba
  que el número de filas de `partes` no cambia y que `reprocesos` vale 1. Es
  el `acceptance` 3, literal.
- `test_f005_bbdd_aislamiento.py` — tras aplicar el DDL, el esquema `public`
  no contiene ni una de nuestras tablas. Es el `acceptance` 2, literal.

**Cómo se mantiene fuera del camino de `init.sh`**, sin tocar el arnés:

1. Directorio **distinto** de `tests/`, así que el `conftest.py` con la guarda
   `sin_red` **no aplica** ahí. La guarda de la suite por defecto se queda
   intacta.
2. Todos los tests llevan
   `@pytest.mark.skipif(not os.getenv("POSTVENTA_PG_TEST_DSN"), reason=...)`.
   `init.sh` ejecuta `pytest -q` sin selección de marcadores, así que el
   **skip por variable de entorno** es el único mecanismo que funciona sin
   inventar un `pytest.ini` que hoy no existe. Sin la variable, saltados; con
   ella, ejecutados. (R33)
3. `tests_bbdd/conftest.py` **aborta si el DSN no apunta a un host local**
   (R34). Es el fusible que hace imposible, no improbable, apuntar sin querer
   al servidor compartido.
4. La cobertura no se resiente porque las líneas de producción ya están
   cubiertas por §7.1: estos tests validan el **SQL**, no añaden código nuevo.
5. La campaña de mutación tampoco: los mutantes corren sin la variable
   definida, así que estos tests se saltan y no pagan arranques de base de
   datos dentro del presupuesto de 120 s por mutante.

### 7.3 Lo que queda como **MANUAL (humano)**

Dos verificaciones, con su comando exacto en `tasks.md`:

- **M1 · La suite contra base efímera.** El humano la lanza con un script
  PowerShell versionado, que levanta una PostgreSQL desechable, corre la suite
  y la tira. Una línea, sin `&&` ni pipes.
- **M2 · El DDL contra la base real de dev**, la primera vez. Es escritura en
  un servidor compartido: la ejecuta el humano, no un agente, con el resultado
  del dry-run (`ddl.cargar_ddl` imprime las sentencias) delante.

---

## 8 · Los dos scripts de PowerShell

`infra/pruebas_bbdd_efimera.ps1` (M1):

1. Comprueba que hay Docker **y que el demonio responde** (`docker info`). Si
   no, sale con un mensaje accionable, distinguiendo los dos casos: Docker no
   instalado, o Docker instalado con el demonio parado → «arranca Docker
   Desktop» (R35). Nada de dejar caer un error opaco de conexión tres pasos
   después. **En ningún punto se usa `psql`** (R36): no está en el `PATH` del
   puesto; se espera y se comprueba con `psycopg` o con `docker exec`.
2. `docker run --rm -d -p 55432:5432 -e POSTGRES_PASSWORD=... postgres:16-alpine`
   con contraseña generada al vuelo, **nunca versionada**.
3. Espera a que acepte conexiones.
4. `$env:POSTVENTA_PG_TEST_DSN` apuntando a `127.0.0.1:55432`.
5. Lanza `pytest tests_bbdd -q` con el intérprete del `.venv` del servicio.
6. `docker rm -f` del contenedor, **pase lo que pase** (`try/finally`).

`infra/crear_base_postventa.ps1` (una sola vez, servidor real): crea la base
`postventa` y el rol de la aplicación, pide confirmación escrita antes de
tocar nada, y **no crea ni toca nada más**. No lo invoca la aplicación (R7).

Los dos son re-ejecutables y en PowerShell, como manda `docs/ARCHITECTURE.md`
para `infra/`. Se le entregan al humano como script más **una línea corta**:
PowerShell no admite `&&` y parte los comandos largos al pegarlos.

---

## 9 · Riesgos y decisiones

### Alternativas descartadas

| Descartado | A favor de | Por qué |
|---|---|---|
| SQLAlchemy + `create_all()` + DDL generado del ORM (sv3, `partes`) | `.sql` numerados + psycopg 3 | `docs/CONVENTIONS.md` lo manda, aquí solo hay **un** servicio dueño del esquema, y en un servidor compartido el DDL tiene que poder leerse antes de aplicarlo (§3) |
| Esquema `public`, como `albaranes` y `partes` | esquema nominado `postventa` | Con `search_path` sin `public`, una sentencia sin cualificar **no puede** aterrizar donde no debe. Cinturón sobre tirantes en un servidor ajeno |
| Que la app haga `CREATE DATABASE` si no existe, como sv3 | script de infraestructura, una vez | Crear bases desde el arranque de una app en un servidor de producción ajeno es justo el gesto que prohíbe `CLAUDE.md` |
| Tabla de migraciones aplicadas (ledger) | DDL idempotente puro | Un ledger es una segunda fuente de verdad que se desincroniza; el `acceptance` pide idempotencia, no historial |
| Guardar los bytes del PDF en la base | solo metadatos + hash | El disco es compartido, solo crece, y ya se llenó una vez (2026-08-09). El PDF va a SharePoint |
| `raw_extraccion_json` como en `albaranes` | columnas explícitas | Duplicaría DNI y observaciones en un blob y engordaría el disco compartido |
| Copiar las observaciones también en `validaciones` | `JOIN` a `partes` | Dos copias de texto manuscrito de un cliente divergen y doblan la exposición |
| Aflojar la guarda `sin_red` para los tests de BBDD | suite aparte en otro directorio | La guarda es la mejor red del proyecto y F-003 la protege con un test |
| `testcontainers` / `pytest-postgresql` como dependencia | script PowerShell + `skipif` | Dependencia nueva que arrastra Docker al `requirements-dev`, y `init.sh` la ejecutaría sin querer |
| `date` para `fecha_servicio` | `text` | F-003 devuelve el literal del papel en varios formatos; convertir es inventar |

### Riesgos

**Riesgo 1 · F-005 depende de F-004, que aún no está mergeada.** Los puertos
hablan `ResultadoValidacion`. Si F-004 cambia de contrato tras su revisión,
cambian los `CHECK` de `validaciones` y el mapeo. Mitigación: T1 es rebasar
sobre `dev` con F-004 dentro, y los `CHECK` se generan de los `Enum` (§2), así
que una etiqueta nueva rompe la suite en vez de romper producción.

**Riesgo 2 · el disco compartido.** No hay cuota por base: nada impide que
nuestras filas contribuyan a llenar los 32 GB. Mitigación: sin BLOBs, sin JSON
crudo, y el volumen esperable es minúsculo (una remesa real son 22 partes).
Queda escrito en `docs/INTEGRACION.md` para el que venga.

**Riesgo 3 · agotar conexiones.** Un `Standard_B1ms` tiene pocas y las
comparten tres proyectos; una Function App que escale a N instancias podría
comérselas. Mitigación: `PG_MAX_CONEXIONES` con un techo bajo (4) y
`idle_in_transaction_session_timeout` (R9), para no dejar sesiones colgadas en
el servidor de otros.

**Riesgo 4 · carrera de arranque.** Dos instancias arrancando a la vez pueden
chocar aunque el DDL sea `IF NOT EXISTS` (PostgreSQL puede levantar
`DuplicateTable` bajo concurrencia). Es exactamente lo que `albaranes` tiene
documentado como «gana el que arranque primero». Mitigación: `pg_advisory_lock`
(R10) y tolerar `DuplicateObject` como éxito.

**Riesgo 5 · el `.sql` no se muta.** Tapado como se explica en §3: el
validador en `.py` sí se muta, y sus tests leen el `.sql` real.

**Riesgo 6 · la cobertura del adaptador.** Si el doble de conexión resulta
insuficiente y quedan líneas del adaptador sin cubrir, la puerta de cobertura
de las líneas cambiadas (≥ 80 %) puede caer. Mitigación: mantener el adaptador
delgado; la lógica está en `sentencias.py` y `mapeo.py`, que son puros.

---

## 10 · Decisiones del humano (las seis, resueltas el 2026-08-19)

> Las seis decisiones que esta sección planteaba **están resueltas**. El humano
> las respondió el **2026-08-19**, antes de escribir una sola línea de código.
> Ya **no** bloquean la implementación. Cada apartado conserva el planteamiento
> original —para que se entienda qué se sopesó— y abre con la resolución.
>
> Cinco confirman lo que el diseño ya proponía; **D2** y **D5** añaden trabajo
> concreto, recogido en §6 y en `tasks.md`.

**D1 · ¿Base propia `postventa` o esquema dentro de una base existente?**

> **RESUELTA el 2026-08-19 · CONFIRMADO el diseño: base propia `postventa`**,
> con esquema nominado `postventa` dentro y `search_path` sin `public`. Motivo
> aceptado: el ecosistema aísla por base, y meter un esquema en `albaranes`
> ataría el ciclo de vida de dos proyectos. **La base la crea el humano a mano;
> la aplicación nunca** (R7). Sin cambios en el diseño.

El diseño pide **base propia** `postventa` con esquema `postventa` dentro,
porque es lo que hace el ecosistema (`albaranes`, `partes`, `sigrid_dm`: «un
servidor, tres bases»). `docs/ARCHITECTURE.md` dice «schema propio», que se
cumple igualmente. La alternativa —un esquema `postventa` dentro de la base
`albaranes` o `partes`— reutilizaría una base ajena y mezclaría el ciclo de
vida de dos proyectos; solo tiene sentido si crear una base nueva en ese
servidor está vetado por coste o por política. **Crear la base es una acción
del humano en cualquier caso** (R7). Coste de cambiar después: el valor de
`PG_DB` y volver a aplicar el DDL.

**D2 · ¿Se persiste el DNI del cliente, o solo si lo había?**

> **RESUELTA el 2026-08-19 · SÍ se persiste el DNI del cliente**, en
> `partes.dni_cliente`. Decisión expresa del humano: *«si guarda el DNI es
> importante»*. Queda **descartada** la alternativa de guardar solo un booleano
> `dni_presente` con su confianza.
>
> Consecuencia, y es la única parte del diseño que D2 mueve: hay **dato personal
> directo confirmado en una base compartida**, así que las salvaguardas dejan de
> ser una nota de contexto y pasan a ser explícitas y comprobables. Están en
> **§6**, ampliada, y en los requisitos **R37–R40** de `requirements.md`: el DNI
> nunca en el log (con test), nunca en el repositorio ni en fixtures, nunca
> duplicado en otra tabla, y el PDF fuera de la base. El esquema de `partes` no
> cambia respecto a lo ya diseñado.

El diseño lo **persiste**, en columna marcada como dato personal (§6), con dos
argumentos: la fila del parte es la traza de lo que el modelo leyó, y el DNI ya
queda retenido de todos modos dentro del PDF archivado en SharePoint, así que
no guardarlo no lo elimina del sistema. El argumento contrario es de
minimización: nadie aguas abajo lo usa —F-004 declara conforme un parte sin
DNI, el nombrado usa obra e incidencia, el cierre usa la incidencia— así que
podría guardarse solo `dni_presente boolean`. **Es una decisión de protección
de datos, no técnica, y la toma el humano.** Coste de cambiar después: una
columna y su mapeo.

**D3 · ¿Docker para la base efímera, o PostgreSQL local con `initdb`?**

> **RESUELTA el 2026-08-19 · CONFIRMADO el diseño: Docker**
> (`postgres:16-alpine`, contenedor `--rm`). Dos datos verificados ese mismo día
> en el puesto del humano, que condicionan el script:
>
> 1. **Docker 29.5.3 está instalado**, pero el **demonio estaba parado** (Docker
>    Desktop cerrado). `infra/pruebas_bbdd_efimera.ps1` debe detectarlo y salir
>    con un mensaje **claro y accionable** —«arranca Docker Desktop»— en vez de
>    un error opaco de conexión al final.
> 2. **No hay `psql` en el PATH.** Ni el script ni la suite pueden depender de
>    que exista: la espera a que la base acepte conexiones y toda comprobación
>    se hacen con el cliente Python (`psycopg`) del `.venv` del servicio, o
>    dentro del contenedor con `docker exec`.
>
> Recogido en `tasks.md`, T21. Queda descartado el `initdb` local.

El diseño asume **Docker** (`postgres:16-alpine`, contenedor `--rm`), que es
lo más limpio y no deja nada instalado. Si el puesto no tiene Docker Desktop,
la alternativa es un `initdb` en un directorio temporal contra un PostgreSQL
ya instalado. Hace falta saber con qué cuenta el humano antes de escribir
`infra/pruebas_bbdd_efimera.ps1`.

**D4 · ¿`numero_incidencia` debe ser único?**

> **RESUELTA el 2026-08-19 · CONFIRMADO el diseño: `numero_incidencia` indexado
> pero NO único.** La deduplicación la hace el hash del parte. Motivos aceptados
> por el humano: una misma incidencia puede tener **más de un parte** (más de una
> visita), y un índice único **rompería** el día que F-014 reagrupe un parte de
> dos hojas. Queda descartado el único parcial. Sin cambios en el diseño.

El diseño lo deja **indexado pero no único**. `docs/ARCHITECTURE.md` (semántica
9) dice que un parte se identifica «por hash del PDF troceado **y** por número
de incidencia», y la deduplicación real la hace el hash. Hacerlo único
rompería el día que F-014 reagrupe un parte de dos hojas —el hash cambia y
habría dos filas para la misma incidencia— y también si una incidencia
llegase a tener legítimamente dos partes. La alternativa es único parcial
(`WHERE numero_incidencia IS NOT NULL`) y tratar el choque como error de
negocio. **Afecta a qué pasa cuando llegan dos partes de la misma
incidencia**, y eso es una regla de negocio que decide Posventa.

**D5 · ¿Se declara el DDL como ruta sensible del arnés?**

> **RESUELTA el 2026-08-19 · NO se declara ahora.** F-005 **no** crea
> `harness/rutas_sensibles.json` y el checkpoint C4 ter sigue siendo **N/A**.
> Motivo del humano: hacerlo aquí cambiaría el arnés para **todas** las features
> y obligaría a portarlo a `arnes-base` en el mismo trabajo.
>
> **No es un olvido, y que quede escrito para quien lo lea mañana:**
> `services/postventa-api/infrastructure/persistencia/sql/**` es un **candidato
> reconocido a ruta sensible** —DDL contra un servidor compartido por cuatro
> proyectos—, y **la decisión vive en F-017**, que ya está dada de alta, va a
> tocar `CHECKPOINTS.md` y va a viajar a `arnes-base`. Si F-017 la declara,
> F-005 no necesita ningún cambio retroactivo: se limitaría a exigir informe de
> verificación a las features **posteriores** que toquen ese directorio.
>
> `harness/features.json` no se toca desde esta spec: lo lleva el líder.

Hoy no existe `harness/rutas_sensibles.json`, así que el checkpoint C4 ter es
N/A. Un DDL contra un servidor compartido es el candidato de manual a ruta
sensible: se podría declarar `infrastructure/persistencia/sql/**` exigiendo un
informe de verificación por feature que lo toque. **No se hace en F-005 sin
permiso**, porque crear ese fichero cambia el arnés para **todas** las
features y, por la regla de propagación de `CLAUDE.md`, habría que portarlo a
`arnes-base` en el mismo trabajo.

**D6 · ¿Se guarda quién sube la remesa (`usuario_oid`) ya en F-005?**

> **RESUELTA el 2026-08-19 · CONFIRMADO el diseño: la columna `usuario_oid` se
> crea ya y queda `NULL`** hasta F-007/F-010, que son las que conocen al usuario
> autenticado. Motivo aceptado: cuesta cero ahora y ahorra un `ALTER TABLE`
> contra una base compartida después. Sin cambios en el diseño.

La columna está diseñada, pero quien conoce al usuario autenticado es el front
con Entra (F-007/F-010). En F-005 quedará siempre `NULL`. Se puede dejar la
columna preparada (lo que propone el diseño) o retrasarla a F-007. Dejarla
cuesta nada; retrasarla obliga a un `ALTER TABLE` que el DDL idempotente ya
soporta.

---

## 11 · Límite de microservicio y ecosistema

F-005 cae **entera** dentro de `services/postventa-api/`: mismo dominio, mismo
patrón de puertos y adaptador. No toca el catálogo del portal, no llama a
`sigrid-api`, no escribe en SharePoint. Ninguna responsabilidad ajena.

**Pero sí cruza la frontera del ecosistema**, y eso obliga por
`CLAUDE.md` y por el `README.md` de `azure-apps/`: F-005 hace que este
proyecto **consuma un recurso compartido** —una base nueva en
`psql-albaranes-rs9k2`— que hasta hoy no consumía. Los dueños de `albaranes`,
`partes` y `datamart-seg-anual` tienen derecho a saber que hay un cuarto
inquilino en su servidor de 32 GB.

Por eso:

- Se crea **`docs/INTEGRACION.md`** en este repositorio, que es la fuente de
  verdad según la regla 1 de `azure-apps/README.md`: qué base usamos, qué
  esquema, qué variables de entorno, qué volumen esperamos y qué se rompe si
  alguien toca el servidor. Es tarea de `tasks.md` (T20), no un «luego».
- Copiar ese documento a `azure-apps/postventa_incidencias.md` queda como
  **MANUAL (humano)**: es **otro repositorio git**, fuera de este worktree, y
  ningún agente commitea en un repositorio que no es el suyo sin que se le
  pida. F-004 dejó escrito que el documento del ecosistema se crearía al
  desplegar (F-010); F-005 adelanta el contenido porque el consumo del
  recurso compartido empieza aquí, no en el despliegue.
- **Nunca** entra en `docs/INTEGRACION.md` ni en `azure-apps/` un valor: ni
  host, ni usuario, ni contraseña, ni ID de suscripción. Solo **nombres** de
  recurso y de variable.
