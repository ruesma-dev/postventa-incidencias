<!-- specs/F-006-sharepoint/design.md -->
# F-006 · Nombrado y archivo en SharePoint — Diseño técnico

> Encaja en `docs/ARCHITECTURE.md` (pasos **5 · Nombrado** y **6 · Archivo**
> del pipeline) y en `docs/CONVENTIONS.md`. Servicio:
> **`services/postventa-api/`** y solo ese.
>
> **Ni un dato real.** Todos los códigos, rutas y nombres de este documento
> están inventados: `0677`, `RS26.08/0123`, `0677 - RS26.08 - 0123 PARTE
> FIRMADO.pdf`. Los partes reales llevan DNI y observaciones manuscritas de
> clientes; nada de eso entra en el repositorio, ni en fixtures, ni en logs.

---

## 0 · Dónde está el riesgo de esta feature

No está en el nombrado, aunque el nombrado sea el corazón. Está en que
**F-006 es la primera feature de este proyecto que escribe en un sistema
externo compartido**, y en que hay una regla dura que la atraviesa entera:

> **PROHIBIDO subir nada al SharePoint de Posventa desde local**
> (`CLAUDE.md`, reglas duras; `docs/ARCHITECTURE.md`, «Prohibido desde
> local»; `acceptance` 4 de F-006: «ninguna subida real desde local ni desde
> los tests»).

Esa regla no se cumple por disciplina: se cumple porque el código lo impide,
con tres puertas independientes que se describen en **§5** y que tienen sus
propios tests (R19–R22). Si una falla, quedan dos.

### Lo que se ha leído en `azure-apps/` antes de diseñar nada

`azure-apps/` es el repositorio del ecosistema. Esto es lo que dice sobre
SharePoint, y lo que **no** dice:

| Hecho | Fuente | Consecuencia para F-006 |
|---|---|---|
| **`partes` ya sube PDFs a SharePoint vía Microsoft Graph** desde su servicio `sv3` de persistencia | `partes.md` §3.3, §5.3 | No inventamos un mecanismo nuevo: mismo patrón (Graph + app registration), mismo vocabulario |
| **`albaranes` también archiva en SharePoint** (PDF del albarán, JSONs de IA, PDFs de contratos) y guarda `sharepoint_drive_id`, `sharepoint_item_id`, `sharepoint_relative_path`, `sharepoint_web_url` | `albaranes.md` §1, §3 | Nuestra traza (`archivos`, F-005) guarda **los mismos cuatro conceptos** con nombres equivalentes: `drive_id`, `item_id`, `carpeta` + `nombre_fichero`, `web_url` |
| `partes` guarda `sharepoint_drive_id`, `sharepoint_item_id`, `sharepoint_url` en `parte_documents` | `partes.md` §4.1 | Ídem: no se inventa un modelo de traza distinto |
| La credencial de Graph de `partes` es **client/secret de un app registration**, en Key Vault (`GRAPH_KEY`) | `partes.md` §5.4, §5.6 | F-006 usa **la misma forma de identidad**: app-only con client credentials. En Azure, el secreto va por Key Vault (F-010) |
| `remesas` tiene **pendiente** sustituir su escritura en disco efímero por «un adaptador que suba a SharePoint vía Microsoft Graph (como ya se hace en el proyecto de albaranes)» | `remesas.md` §11.3 | Confirma que el patrón de la casa es Graph, y que el adaptador tras un puerto es la forma esperada |
| **NO consta en `azure-apps/`**: qué sitio, qué biblioteca, qué librería cliente de Python, qué permisos de Graph (`Sites.Selected` vs `Files.ReadWrite.All`) ni qué nombres de variable usa cada proyecto | (ausencia comprobada con un barrido de `SHAREPOINT_*`, `GRAPH_*`, `SITE_*`, `DRIVE_*`, `Sites.`, `Files.` sobre los ocho documentos) | Es un **hueco real del ecosistema**. Se convierte en la decisión abierta **D1** (§10) y en la tarea **T15** (`docs/INTEGRACION.md`) + **T19** (copia manual a `azure-apps/`) |

**Conclusión operativa**: se reutiliza el patrón (Graph, app-only,
drive/item/URL en la traza) y **no se reutiliza ni un identificador**, porque
el ecosistema no los publica —ni debe: la regla 3 de `azure-apps/README.md`
prohíbe valores. Los identificadores viajan por configuración.

### Lo que este proyecto pasa a consumir, y a quién hay que avisar

Hasta hoy `postventa-incidencias` consume Gemini y (con F-005) el PostgreSQL
compartido. Con F-006 pasa a consumir **SharePoint del tenant**, en el sitio
de **IT** —el mismo donde vive la biblioteca de albaranes—. Los dueños de
`albaranes` y de `partes` tienen derecho a saber que hay otro inquilino en ese
sitio y otra aplicación con permisos de escritura sobre él.

Por eso, y **reusando el mecanismo que ya montó F-005** (no duplicándolo):

- La fuente de verdad es **`docs/INTEGRACION.md`** de este repositorio, que
  **F-005 crea**. F-006 le **añade una sección** de SharePoint (tarea **T15**).
  No se crea un documento nuevo ni un mecanismo paralelo.
- La copia a **`azure-apps/postventa_incidencias.md`** es **`MANUAL
  (humano)`** (tarea **T19**): es otro repositorio git, fuera de este
  worktree, y ningún agente commitea en un repositorio que no es el suyo.
- **Nunca** entra un valor: ni site id, ni drive id, ni tenant, ni client id,
  ni secreto. Solo **nombres** de recurso y de variable.

---

## 1 · Precondiciones: de qué ramas depende F-006 y en qué orden se mergea

> Escrito con la misma claridad con que lo hizo F-005, y por el mismo motivo:
> **no se diseña un modelo gemelo para poder empezar antes.**

F-006 habla dos vocabularios que **hoy no existen en `dev`**:

| Necesita | De dónde sale | Rama donde vive hoy |
|---|---|---|
| `ResultadoValidacion`, `Veredicto`, `Destino` (`ARCHIVO_Y_CIERRE`) | **F-004** | `feature/F-004-validacion` |
| `TrazaArchivo`, `EstadoArchivo`, `RepositorioPartesPort.guardar_archivo()`, la tabla `postventa.archivos`, y **`docs/INTEGRACION.md`** | **F-005** | `feature/F-005-persistencia` |

Y F-005 declara a su vez que **no se implementa hasta que F-004 esté mergeada
en `dev`**. Por tanto el orden es **uno solo**:

```
F-004 → dev        (validación: quién es apto)
   ↓
F-005 → dev        (persistencia: la tabla `archivos` y su traza)
   ↓
F-006              (rebase de feature/F-006-sharepoint sobre dev, y a implementar)
```

**F-006 se implementa la tercera.** La tarea **T1** de `tasks.md` es
exactamente esa comprobación, y si no se cumple la feature se marca `blocked`.

**Alternativas descartadas a propósito**, las dos por el mismo motivo (dos
modelos del mismo concepto divergen siempre):

- Inventar aquí un `ResultadoArchivo` propio en vez de usar la `TrazaArchivo`
  de F-005. La tabla `archivos` ya está diseñada, con PK por `hash_parte`
  precisamente para hacer verdad el `acceptance` de F-006.
- Inventar un «apto» propio (por ejemplo, «tiene obra e incidencia») en vez de
  leer el `Destino` de F-004. Eso archivaría partes que F-004 mandó a la cola
  de validación humana, contra `CHECKPOINTS.md` C3.

**Si F-004 o F-005 cambiaran su contrato, F-006 se rehace en esa parte.**
Ningún cambio a esas dos specs se hace desde aquí: lo detectado va como
decisión abierta (§10, **D4** y **D5**).

---

## 2 · La frontera: qué entra, qué sale

**Entra** (por parte, no por fichero — `CHECKPOINTS.md` C3):

- El `ParteTroceado` de F-002: su **`hash`** (la identidad) y su
  **`contenido`** (los bytes del PDF de ese parte).
- El `ResultadoValidacion` de F-004: `veredicto` y `destino`.
- El código de obra y el código de incidencia, tal y como los leyó F-003 (o
  tal y como los corrigió una persona en el front de F-007).

**Sale**: una `TrazaArchivo` de F-005 —estado, nombre, carpeta, `drive_id`,
`item_id`, `web_url`, motivo, fecha— más los avisos del paso.

**No sale**: ni los bytes del PDF, ni el DNI, ni las observaciones, ni el
token, ni la configuración del destino (R26, R30).

---

## 3 · Ficheros

### 3.1 A crear

#### Dominio (puro: ni Graph, ni HTTP, ni SQL, ni configuración)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | `SEPARADOR`, `SUFIJO`, `EXTENSION`, `GUIONES_EQUIVALENTES`, `CARACTERES_PROHIBIDOS`, `normalizar_codigo()`, `nombre_de_archivo()`, `carpeta_de_archivo()`, `DestinoArchivo`, `componer_destino()` |
| `services/postventa-api/domain/ports/archivo.py` | `ItemArchivado`, `ArchivoPort` (el `ArchivoPort` que `docs/ARCHITECTURE.md` ya nombra) |

#### Aplicación (orquesta; habla con puertos, nunca con adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | `paso_archivo(ctx, archivador, repositorio, *, carpeta_base, ahora)` |

#### Infraestructura (el único sitio que conoce Microsoft Graph)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/infrastructure/sharepoint/__init__.py` | vacío |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | `AdaptadorSharePointGraph`, `es_transitorio()`, `CODIGOS_TRANSITORIOS`, `CONFLICT_BEHAVIOR` |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | `construir_archivador(ajustes)`, `ENTORNOS_CON_ARCHIVO` |

#### Interfaz HTTP

| Ruta | Contenido |
|---|---|
| `services/postventa-api/interface_adapters/api/archivar.py` | handler `archivar_parte(...)` y la composición del paso |

#### Infra (scripts de verificación manual, sin secretos)

| Ruta | Contenido |
|---|---|
| `infra/verificar_destino_sharepoint.ps1` | **solo lectura**: confirma sitio, biblioteca y permisos del destino de dev (T17) |
| `infra/verificar_archivo_dev.ps1` | ejercita **dos veces** `POST /api/archivar` **contra el servicio desplegado** y comprueba que no hay duplicado (T18) |

#### Tests

| Ruta | Requisitos |
|---|---|
| `services/postventa-api/tests/utiles_sharepoint.py` | **entregable**: `BibliotecaFalsa` (doble que imita una biblioteca real), `ArchivoPortFalso`, `RepositorioFalso`, `ClienteGraphFalso` |
| `services/postventa-api/tests/test_f006_nombrado.py` | R1–R9 |
| `services/postventa-api/tests/test_f006_paso_archivo.py` | R10–R18, R23, R24, R27 |
| `services/postventa-api/tests/test_f006_adaptador_graph.py` | R11, R12, R15, R16, R25, R26 |
| `services/postventa-api/tests/test_f006_fabrica.py` | R19, R20, R28 |
| `services/postventa-api/tests/test_f006_archivar_http.py` | R30, R31 |
| `services/postventa-api/tests/test_f006_arquitectura.py` | R21, R22, R26, R29, R32 |

### 3.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `config/settings.py` | los campos `sharepoint_*` y `graph_*` de §7 |
| `services/postventa-api/.env.example` | las variables nuevas, **con placeholders y sin un solo valor** |
| `services/postventa-api/local.settings.json.example` | ídem |
| `services/postventa-api/requirements.txt` | `msal>=1.28,<2.0` y `requests>=2.31,<3.0` (ver **D1**) |
| `domain/models/errores.py` | `NombradoImposible`, `ParteNoApto`, `ArchivoDeshabilitado`, `ArchivoFallido`, `ConfiguracionSharePointIncompleta`, con la forma que ya usan todos (`__init__(self, motivo: str)` y atributo `.motivo`) |
| `application/pipelines/contexto_parte.py` | añade `archivo: TrazaArchivo \| None = None` (F-004 ya le añade `validacion`) |
| `function_app.py` | ruta nueva `POST /api/archivar`, **solo traducción** de errores a 400 / 409 / 502 / 503 |
| `docs/ARCHITECTURE.md` | pasos 5 y 6 del pipeline con la regla de la barra y la del reemplazo; la fila de SharePoint con las variables y con la puerta de entorno |
| `docs/INTEGRACION.md` | **lo crea F-005**; F-006 le añade la sección «SharePoint (Microsoft Graph)» (R32, T15) |

### 3.3 Ficheros que NO se tocan (los que tientan)

- **`services/postventa-api/tests/conftest.py`.** La guardia de red `sin_red`
  de F-003 se queda **exactamente** como está. Es la red de seguridad que
  convierte «ninguna subida desde los tests» en algo imposible en vez de en
  una promesa. Aflojarla para que algún test de F-006 «pruebe de verdad»
  sería destruir la mejor defensa del proyecto.
- **`domain/models/validacion.py`, `domain/models/firma.py`** (F-004) y
  **`domain/models/persistencia.py`, `domain/ports/persistencia.py`,
  `infrastructure/persistencia/*`** (F-005). F-006 los **consume**; si le
  faltara algo, se anota como decisión abierta (D4, D5) y **no** se cambian.
- **`domain/models/extraccion.py`, `domain/models/remesa.py`,
  `infrastructure/llm/`, `infrastructure/documentos/`.** F-006 no toca la
  extracción ni el troceado.
- **`harness/init.sh`, `harness/rigor.json`, `harness/servicios.json`,
  `harness/alcance.py`, `harness/rutas_sensibles.json`.** Ninguna puerta del
  arnés se retoca para que esta feature pase. Si algo del arnés estorba, se
  dice, no se afloja.
- **`muestras/`, `docs/referencia/*.pdf`.** Ni un parte real entra en un test.

### 3.4 SQL

**Ninguno.** F-006 **no añade ni una sentencia DDL**: la tabla
`postventa.archivos` y su fichero `.../05_archivos.sql` son de F-005. F-006
solo **escribe filas** a través de `RepositorioPartesPort.guardar_archivo()`.
Nada de esta feature toca el servidor compartido `psql-albaranes-rs9k2` fuera
del esquema propio, ni a nivel de servidor.

---

## 4 · El nombrado (dominio puro)

### 4.1 La trampa, escrita antes que el código

Tres cosas distintas que es fácil confundir, y que decide `docs/ARCHITECTURE.md`
(semánticas 2 y 5):

| Dato | Ejemplo **inventado** | De dónde sale | Para qué sirve aquí |
|---|---|---|---|
| **Código de obra** | `0677` | campo propio del papel | **la carpeta** y el primer tramo del nombre |
| **Código de incidencia** | `RS26.08/0123` | lo emite **Sigrid entero** (serie + correlativo) | el segundo tramo del nombre |
| Nombre del fichero | `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf` | se compone aquí | lo que ve Posventa |

- El código de incidencia **no es** «obra + número». Confundirlos estropea a
  la vez el nombre y la carpeta.
- La incidencia se **extrae con barra** (`RS26.08/0123`) y se **nombra con
  guion** (`RS26.08 - 0123`). La barra es un separador de ruta: dejarla
  caería el fichero en una subcarpeta inventada, o reventaría la subida.
- Los **ceros a la izquierda** de la obra se conservan. `int("0677")` es un
  bug, no una normalización.
- El sufijo ` PARTE FIRMADO` es el que ya usa Posventa: se conserva tal cual.
- **Sin nº de incidencia no hay nombre.** No se deduce, no se inventa, no se
  pone «SIN_INCIDENCIA»: el parte va a revisión manual. En la práctica ese
  caso no debería llegar aquí, porque F-004 no lo declara apto — por eso R6 es
  una **red de seguridad**, no el camino normal.

### 4.2 Firmas

```python
# domain/models/nombrado.py

SEPARADOR = " - "                  # espacio, guion NORMAL (U+002D), espacio
SUFIJO = " PARTE FIRMADO"
EXTENSION = ".pdf"

#: Todo lo que en el mundo real hace de guion y NO es U+002D.
GUIONES_EQUIVALENTES = "‐‑‒–—―−"

#: Lo que SharePoint (y Windows) no admiten en un nombre de fichero.
CARACTERES_PROHIBIDOS = '"*:<>?/\\|'

def normalizar_codigo(bruto: str | None) -> str:
    """Guiones a guion normal, espacios colapsados, extremos recortados.

    NO toca los ceros a la izquierda y NO convierte a número.
    """

def nombre_de_archivo(*, codigo_obra: str | None, numero_incidencia: str | None) -> str:
    """`<obra> - <incidencia> PARTE FIRMADO.pdf`. Levanta `NombradoImposible`."""

def carpeta_de_archivo(*, carpeta_base: str, codigo_obra: str | None) -> str:
    """`<base>/<obra>`, con los ceros intactos. Levanta `NombradoImposible`."""

@dataclass(frozen=True)
class DestinoArchivo:
    carpeta: str
    nombre_fichero: str

    @property
    def ruta_relativa(self) -> str: ...   # f"{carpeta}/{nombre_fichero}"

def componer_destino(
    *, carpeta_base: str, codigo_obra: str | None, numero_incidencia: str | None
) -> DestinoArchivo: ...
```

`nombre_de_archivo` hace exactamente esto, en este orden:

1. `normalizar_codigo` sobre los dos códigos. Vacío o `None` →
   `NombradoImposible` nombrando **cuál** falta (R6).
2. En la incidencia, `/` → `SEPARADOR` (R2). Se hace **después** de normalizar
   guiones para que `RS26.08 – 0123` (guion largo) y `RS26.08/0123` acaben en
   el mismo sitio.
3. Colapso final de espacios: `0677  -   RS26.08` → `0677 - RS26.08` (R8).
4. Composición: `obra + SEPARADOR + incidencia + SUFIJO + EXTENSION`.
5. **Comprobación, no saneo**: si el resultado trae un carácter de
   `CARACTERES_PROHIBIDOS`, empieza o acaba en espacio, o acaba en punto →
   `NombradoImposible` (R7).

El paso 5 es deliberadamente severo. La alternativa —sustituir el carácter
raro por `_`— archivaría un fichero con un nombre que nadie pidió, en un
archivo que Posventa consulta a mano, y **sin que nadie se entere**. Un error
ruidoso es mejor que un archivo sucio (§9, decisión D-b).

---

## 5 · Cómo se garantiza EN CÓDIGO que no hay subida desde local ni desde los tests

Tres puertas independientes. No es redundancia decorativa: es que la regla es
dura y el fallo sería irreversible (lo que se sube a SharePoint lo ve
Posventa).

### Puerta 1 · El constructor del adaptador muerde (R19)

```python
# infrastructure/sharepoint/graph.py

class AdaptadorSharePointGraph:
    def __init__(self, *, entorno: str, site_id: str, drive_id: str, ...) -> None:
        if entorno not in ENTORNOS_CON_ARCHIVO:      # ("dev", "pro")
            raise ArchivoDeshabilitado(
                f"el archivo en SharePoint solo se permite en {ENTORNOS_CON_ARCHIVO}; "
                f"ENTORNO={entorno!r}"
            )
```

Está **en el constructor** y no solo en la fábrica a propósito: alguien que
componga las piezas de otra manera —un script suelto, un test «solo para
probar», un `python -c`— se topa igual con la puerta. `ENTORNO` es
obligatoria desde F-001 y `tests/conftest.py` la fija a `test` para **toda**
la suite, así que dentro de la suite el adaptador real **no se puede
construir**. Ese es el mecanismo, y tiene su test.

### Puerta 2 · La fábrica es fail-closed (R20)

```python
# infrastructure/sharepoint/fabrica.py
def construir_archivador(ajustes: Ajustes) -> ArchivoPort:
    if not ajustes.archivo_habilitado:
        raise ArchivoDeshabilitado("ARCHIVO_HABILITADO no está activado")
    ...   # y luego exige la configuración completa (R28)
```

`archivo_habilitado` vale **`False` por defecto**. El comportamiento por
omisión —el de un `.env` recién copiado, el de un despliegue a medio
configurar— es **no subir**. Encenderlo es un gesto explícito y consciente,
que en dev hace el humano y en Azure hace el script de F-010.

### Puerta 3 · La guardia de red de F-003, intacta (R21)

`tests/conftest.py` sustituye `socket.socket.connect` durante toda la sesión
de pytest. Si algún día alguien salta las puertas 1 y 2, la conexión **no
llega a abrirse** y el test se cae diciendo por qué. F-006 **no la toca**, y
añade un test propio que comprueba que sigue mordiendo con `ArchivoPort`
delante.

### Y además: el test de arquitectura (R22)

`test_f006_arquitectura.py` recorre con `ast` `domain/` y `application/` y
comprueba que ninguno importa `msal`, `requests`, `httpx` ni `infrastructure`,
y que el único paquete que importa el cliente de Graph es
`infrastructure/sharepoint/`. Más un test que barre `tests/` buscando
construcciones de `AdaptadorSharePointGraph` fuera del test que verifica
precisamente que el constructor muerde.

### Dónde ocurre entonces la subida de verdad

**Solo desde el entorno desplegado** (Function App, `ENTORNO=dev`), contra la
biblioteca de dev del sitio de IT, invocando `POST /api/archivar`. Es la
verificación **T18**, `MANUAL (humano)`, y su comando exacto está en
`tasks.md`. Nada de este repositorio puede provocarla desde una máquina de
desarrollo.

---

## 6 · El puerto, el paso y la idempotencia

### 6.1 El puerto (dominio)

```python
# domain/ports/archivo.py

@dataclass(frozen=True)
class ItemArchivado:
    drive_id: str
    item_id: str
    web_url: str
    nombre: str
    carpeta: str

class ArchivoPort(Protocol):
    def asegurar_carpeta(self, *, carpeta: str) -> None:
        """Crea la carpeta si no existe. Llamarlo dos veces deja UNA (R11, R12)."""

    def buscar(self, *, carpeta: str, nombre: str) -> ItemArchivado | None:
        """El elemento con ese nombre exacto, o `None`. No lista la carpeta entera."""

    def subir(
        self, *, carpeta: str, nombre: str, contenido: bytes, mime: str
    ) -> ItemArchivado:
        """Sube REEMPLAZANDO el homónimo. Nunca renombra (R15).

        Levanta `ArchivoFallido` si el proveedor no responde de forma
        utilizable, y **nunca** vuelca los bytes ni ningún dato del parte en
        el mensaje (R26).
        """
```

Tres operaciones mecánicas y ninguna decisión: **la decisión vive en la
aplicación**, que es código puro y se prueba con dobles. Eso es lo que hace
que la campaña de mutación tenga superficie que morder.

### 6.2 El paso (aplicación)

```python
# application/pipelines/paso_archivo.py

def paso_archivo(
    ctx: ContextoParte,
    archivador: ArchivoPort,
    repositorio: RepositorioPartesPort,
    *,
    carpeta_base: str,
    ahora: datetime,
    traza_previa: TrazaArchivo | None = None,
) -> ContextoParte: ...
```

Orden exacto, y el orden importa:

1. **Puerta de aptitud (R17, R18).** Sin `ctx.validacion`, o con
   `destino != Destino.ARCHIVO_Y_CIERRE` → `ParteNoApto`. **Antes de nombrar
   y antes de tocar el puerto**: un parte no apto no crea ni la carpeta.
2. **Nombrado (R1–R9).** `componer_destino(...)` sobre los códigos de la
   extracción. `NombradoImposible` sale sin haber tocado el puerto.
3. **Idempotencia por traza (R14).** Si `traza_previa` existe y su estado es
   `EstadoArchivo.ARCHIVADO`, se devuelve esa traza con un aviso («ya estaba
   archivado») y **no se llama al puerto**. Es la capa barata: ni token, ni
   red, ni bytes.
4. **`asegurar_carpeta`** (R11, R12).
5. **`buscar`** el nombre en la carpeta (R16). Si existe, se anota aviso de
   reemplazo.
6. **`subir`** reemplazando (R15).
7. **Traza (R23, R24).** `TrazaArchivo` con `estado=ARCHIVADO` y todos los
   datos del `ItemArchivado`; o `estado=ERROR` con `motivo` si algo falló. Se
   persiste con `repositorio.guardar_archivo(traza=...)` en **los dos casos**.
8. Se deja en `ctx.archivo` y se devuelve el contexto.

`paso_archivo` **no construye adaptadores**: la composición vive en el punto
de entrada, como manda `docs/CONVENTIONS.md`.

### 6.3 Qué es «el mismo parte», y por qué no se inventa otro criterio

**El `hash` del parte troceado de F-002.** Es lo que promete
`docs/ARCHITECTURE.md` (semántica 9: «se identifica por hash del PDF troceado»)
y es la **clave primaria** de la tabla `archivos` de F-005, elegida allí
precisamente para «hacer verdad el `acceptance` de F-006 (subir dos veces el
mismo parte no genera un duplicado)». F-006 **reusa esa clave**; no define un
criterio propio ni compara por nombre, ni por incidencia, ni por bytes.

De ahí salen **tres capas de idempotencia**, cada una tapando lo que la
anterior no ve:

| Capa | Qué evita | Cómo |
|---|---|---|
| **L1 · traza** | Volver a subir el mismo parte (mismo `hash`) | La fila de `archivos` en estado `archivado` corta antes de llamar a nadie (R14) |
| **L2 · reemplazo** | El `archivo (1).pdf` | La subida pide **siempre** reemplazar el homónimo; **jamás** renombrar (R15) |
| **L3 · carpeta** | Dos carpetas para la misma obra | `asegurar_carpeta` tolera «ya existe» como éxito (R12) |

L2 es la que responde literalmente al `acceptance`, y es la que más fácil se
rompe sin querer: **la opción de renombrar es el comportamiento por defecto de
más de un cliente**, y produce exactamente el `(1)` que el criterio prohíbe.
Por eso no se prueba mirando una constante, sino con un doble que **se
comporta como una biblioteca de verdad** (§6.4).

### 6.4 `BibliotecaFalsa`: el doble que hace verdad el test de idempotencia

En `tests/utiles_sharepoint.py`. Un diccionario `ruta -> elemento` que imita
el comportamiento real:

- `subir(..., conflicto="reemplazar")` pisa la entrada existente y **mantiene
  el mismo `item_id`**.
- `subir(..., conflicto="renombrar")` crea `nombre (1).pdf`, `nombre (2).pdf`…
  **igual que haría el servicio real**.
- `subir(..., conflicto="fallar")` levanta un conflicto.
- `asegurar_carpeta` es idempotente y **cuenta** las creaciones reales.

Así, `test_f006_r15_subir_dos_veces_deja_un_solo_elemento` archiva el mismo
parte dos veces y afirma que la biblioteca tiene **exactamente un** elemento y
que **ningún** nombre contiene `(1)`. Si alguien cambia el comportamiento de
conflicto a «renombrar», el test cae por lo que de verdad pasaría en
producción, no por una aserción sobre una cadena.

---

## 7 · Configuración (y por qué F-013 sale casi gratis)

```python
# config/settings.py (añadidos)

archivo_habilitado: bool = Field(
    default=False, validation_alias="ARCHIVO_HABILITADO",
    description="Interruptor maestro del archivo. Por defecto FALSO: sin él no se sube nada.",
)
sharepoint_site_id: str | None = Field(default=None, validation_alias="SHAREPOINT_SITE_ID")
sharepoint_drive_id: str | None = Field(default=None, validation_alias="SHAREPOINT_DRIVE_ID")
sharepoint_carpeta_base: str = Field(default="Postventa", validation_alias="SHAREPOINT_CARPETA_BASE")
graph_tenant_id: str | None = Field(default=None, validation_alias="GRAPH_TENANT_ID")
graph_client_id: str | None = Field(default=None, validation_alias="GRAPH_CLIENT_ID")
graph_client_secret: str | None = Field(default=None, validation_alias="GRAPH_CLIENT_SECRET")
graph_timeout_s: int = Field(default=60, validation_alias="GRAPH_TIMEOUT_S")
graph_reintentos: int = Field(default=3, validation_alias="GRAPH_REINTENTOS")
```

Todos **opcionales en el modelo y obligatorios en la fábrica**, exactamente
como F-003 resolvió `GEMINI_API_KEY`: si fueran obligatorios en `Ajustes`,
`/health` dejaría de arrancar sin configuración de SharePoint y la suite
entera necesitaría valores falsos en el entorno. Quien los exige es
`construir_archivador`, cuando de verdad hacen falta, con
`ConfiguracionSharePointIncompleta` **nombrando la variable y jamás su valor**
(R28).

**Secretos**: `GRAPH_CLIENT_SECRET` es un secreto y no se escribe en ningún
fichero del repositorio. En local vive en el `.env` (que no se versiona); en
Azure, en App Settings con referencia a Key Vault (F-010). `.env.example` y
`local.settings.json.example` llevan **placeholders** (R29), y un test lo
comprueba barriendo esos ficheros.

**El destino de dev es configuración, no una constante** (R27): biblioteca
propia dentro del **sitio de IT**, con `SHAREPOINT_CARPETA_BASE=Postventa`, y
la ruta final `Postventa/0677/0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`
(inventada). **F-013** —mudar el archivo a la biblioteca de Posventa— es,
gracias a esto, cambiar tres variables y su documento: su `acceptance` («la
ruta destino es configuración, no código») queda satisfecho ya desde aquí.

---

## 8 · El adaptador y el borde

### 8.1 `AdaptadorSharePointGraph`

Único fichero del servicio que conoce Microsoft Graph. Igual que
`infrastructure/llm/gemini.py` es el único que conoce el SDK de Gemini.

- **Identidad**: app-only (client credentials) con `msal`, como `partes`.
  Token cacheado en memoria por su vencimiento; **nunca** se registra ni se
  devuelve (R26).
- **Llamadas**, sobre `https://graph.microsoft.com/v1.0`:
  - carpeta: `GET .../drives/{drive}/root:/{carpeta}` y, si `404`,
    `POST .../children` con `folder: {}` y comportamiento de conflicto
    «fallar», tolerando el `409 nameAlreadyExists` como éxito (R12);
  - búsqueda: `GET .../drives/{drive}/root:/{carpeta}/{nombre}`, `404` → `None`;
  - subida: `PUT .../drives/{drive}/root:/{carpeta}/{nombre}:/content` con
    `@microsoft.graph.conflictBehavior = "replace"` (R15). Para ficheros
    grandes, sesión de carga; el umbral queda en una constante del módulo.
- **Reintentos**: `tenacity` con `wait_exponential`, como el adaptador de
  Gemini. Transitorios = `TimeoutError`, `ConnectionError`, `408`, `429`,
  `5xx`. No transitorios = `400`, `401`, `403`, `404`: no se reintentan (R25).
- **Logging**: `hash_parte`, nombre, carpeta, tamaño en bytes, intento y
  duración. **Nunca** los bytes, ni un valor extraído, ni el token, ni el
  secreto (R26).
- Todo fallo utilizable se traduce a `ArchivoFallido(motivo)`.

Se prueba con `ClienteGraphFalso`, un doble del cliente HTTP construido en el
propio test, con `espera_inicial_s=0`. Ninguna llamada real, ninguna
credencial (ni siquiera de dev) en los tests.

### 8.2 `POST /api/archivar`

`multipart/form-data`: el PDF del parte, más `hash`, `codigo_obra`,
`numero_incidencia`, `veredicto` y `destino`. Una llamada = **un parte**, como
`/api/extraer`: la Function corta a los 230 s.

Respuesta **200** (R30), y ni una clave más:

```json
{
  "hash_parte": "9f2b...",
  "nombre_fichero": "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf",
  "carpeta": "Postventa/0677",
  "estado": "archivado",
  "web_url": "https://.../0677%20-%20RS26.08%20-%200123%20PARTE%20FIRMADO.pdf",
  "avisos": []
}
```

*(ejemplo inventado)*

Mapeo de errores en `function_app.py`, **solo traducción**:

| Excepción | HTTP | Qué significa |
|---|---|---|
| cuerpo inválido / sin fichero | **400** | «no me has mandado un parte» |
| `ParteNoApto` | **409** | «este parte no ha pasado la validación» |
| `NombradoImposible` | **409** | «no se puede nombrar; va a revisión manual» |
| `ArchivoDeshabilitado`, `ConfiguracionSharePointIncompleta` | **503** | «este entorno no archiva» |
| `ArchivoFallido` | **502** | «el proveedor no respondió» |

En los cinco casos, **sin haber subido nada** (R31).

Por qué existe el endpoint, y no solo el paso: sin él **no hay ninguna forma
legítima de ejercitar la subida real**, porque la única vía permitida es el
entorno desplegado (§5). El endpoint es lo que hace posible T18.

---

## 9 · Riesgos y decisiones (alternativas descartadas)

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| **a** · Puerta de entorno en el **constructor** además de en la fábrica | Solo en la fábrica | Componer las piezas a mano —un script, un `python -c`, un test— saltaría una puerta única. La regla es dura; la defensa, doble |
| **b** · Nombre imposible → **error**, nunca saneo silencioso | Sustituir el carácter raro por `_` | Archivaría en el archivo de Posventa un fichero con un nombre que nadie pidió y nadie se enteraría. Ruido > silencio |
| **c** · Idempotencia por **hash del parte** (F-005) | Un criterio propio (nombre, incidencia, bytes) | Semántica 9 de `ARCHITECTURE` y PK de `archivos`. Dos criterios del mismo concepto divergen |
| **d** · **Reemplazar** el homónimo | Renombrar (default de muchos clientes) o fallar | Renombrar produce el `(1).pdf` que el `acceptance` prohíbe. Fallar convierte cada reproceso en un error que alguien tiene que mirar |
| **e** · La decisión en la **aplicación**, el puerto mecánico | Un puerto «archiva esto» que lo decida todo dentro | Un puerto gordo mete la lógica en infraestructura, donde no se puede mutar ni cubrir sin red |
| **f** · `BibliotecaFalsa` que **imita** el comportamiento real | Afirmar sobre la constante `"replace"` | Una aserción sobre una cadena no prueba que no salgan duplicados; el doble que renombra, sí |
| **g** · Sin DDL propio | Crear aquí la tabla `archivos` | Es de F-005. Dos dueños del mismo DDL es el acoplamiento que `albaranes.md` ya documenta como problema («gana el que arranque primero») |
| **h** · Endpoint HTTP propio | Solo el paso del pipeline | Sin endpoint no hay forma legítima de ejercitar la subida real desde el entorno desplegado |

**Riesgo 1 · La feature no se puede cerrar sin entorno desplegado.** El
`acceptance` de rigor `critico` exige verificaciones manuales «con su
resultado real», y la única subida real permitida es desde el despliegue, que
es **F-010** (prioridad 10). Es la decisión abierta **D3**, y **bloquea el
cierre**, no la implementación.

**Riesgo 2 · El destino de dev todavía no existe.** Nadie ha creado aún la
biblioteca propia en el sitio de IT ni el app registration con permisos sobre
ella. Decisión abierta **D6**, bloqueante para T17/T18.

**Riesgo 3 · Los ceros a la izquierda.** El bug clásico. Mitigación: el
dominio trabaja con `str` de punta a punta, ningún `int()` toca el código de
obra, y hay test específico para el nombre **y** para la carpeta (R4).

**Riesgo 4 · Datos personales en la traza.** El nombre del fichero lleva obra
e incidencia, que **no** son datos personales; el DNI y las observaciones se
quedan dentro del PDF, que va a SharePoint y **no** a la base ni a los logs.
Test específico de que ni el motivo de error ni el log los llevan (R26).

**Riesgo 5 · Cobertura del adaptador.** Si el doble del cliente HTTP no
alcanza para cubrir el adaptador, la puerta del 80 % puede caer. Mitigación:
adaptador delgado; toda la decisión está en `nombrado.py` y `paso_archivo.py`,
que son puros.

**Riesgo 6 · Que F-004 o F-005 cambien.** F-006 depende de cinco símbolos
suyos (§1). Mitigación: el rebase de T1 y la suite completa; si algo no
encaja, `blocked` y se habla con el humano — **no se parchea la spec ajena**.

---

## 10 · Decisiones abiertas que necesita validar el humano

> Detalle y contexto en `progress/explore_F-006.md`. **Dos bloquean**.

| # | Decisión | ¿Bloquea? |
|---|---|---|
| **D1** | **Qué reutilizar de `partes`/`albaranes`**: librería cliente de Graph (aquí se propone `msal` + `requests`), app registration, y permisos (`Sites.Selected` acotado a la biblioteca, que es lo mínimo, frente a `Files.ReadWrite.All`, que es todo el tenant). `azure-apps/` no lo documenta: hay que mirarlo en el repositorio `partes` o preguntar. Si resulta ser otra librería, **solo cambia `infrastructure/sharepoint/`** | No |
| **D2** | **Mismo nombre, otro `hash`** (dos escaneos distintos de la misma incidencia): la spec **reemplaza y avisa**. La alternativa es fallar y mandarlo a revisión humana. Se implementa el reemplazo porque el archivo de Posventa debe quedarse con la última versión conformada | No |
| **D3** | **La verificación manual de una subida real necesita entorno desplegado**, que es **F-010** (prioridad 10, cuatro features más tarde). Opciones: (a) F-006 cierra con T18 declarada y **pendiente**, y se ejecuta al desplegar; (b) se adelanta un despliegue mínimo. Lo que **no** es opción es subir desde local | **SÍ** |
| **D4** | El endpoint **recibe** el veredicto en el cuerpo y lo vuelve a comprobar. Leerlo de la base sería más fuerte, pero exige un método nuevo en `RepositorioPartesPort` (F-005), y F-006 **no cambia specs ajenas** | No |
| **D5** | `EstadoArchivo` (F-005) no tiene `ya_archivado`: el caso «ya estaba» sale como `archivado` + aviso. Añadir el estado sería más limpio, pero es un cambio en F-005 | No |
| **D6** | **Nadie ha creado todavía** la biblioteca de dev en el sitio de IT ni el app registration con permiso sobre ella. Hace falta que el humano (o IT) lo cree y pase los identificadores por `.env`, **nunca por el repositorio** | **SÍ** (T17, T18) |

---

## 11 · Límite de microservicio

Comprobado, y **no hay desbordamiento**: F-006 vive entera en
`services/postventa-api/`. Nombrar y archivar el parte de posventa es
responsabilidad de este servicio.

Tres fronteras que se rozan y **no** se cruzan:

- **`services/postventa-front/`**: enseñar el resultado y dejar reintentar es
  **F-007**. Aquí no se escribe ni una línea de front.
- **`sigrid-api`**: F-006 no habla con Sigrid. Subir el PDF **a Sigrid** como
  gráfico es F-012 y exige un endpoint nuevo en **otro repositorio**.
- **`azure-apps/`**: el documento del ecosistema se escribe aquí
  (`docs/INTEGRACION.md`) y se **copia a mano** allí. Ningún agente commitea
  en un repositorio ajeno.

Lo único que cruza la frontera del proyecto es el **consumo** de SharePoint, y
eso se resuelve documentándolo (R32, T15, T19), que es justo lo que manda
`CLAUDE.md`.
