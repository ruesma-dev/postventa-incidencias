<!-- specs/F-003-extraccion/design.md -->
# F-003 · Extracción multimodal del parte — Diseño técnico

> Encaja en `docs/ARCHITECTURE.md` (paso **3** del pipeline) y en
> `docs/CONVENTIONS.md`. Servicio: **`services/postventa-api/`** y solo ese.

## 0 · La frontera con F-002 y con F-004

**Entrada**: el `ParteTroceado` que produce F-002 (`domain/models/remesa.py`):
`hash`, `origen`, `paginas_origen`, `modo_deteccion`, `contenido` (el PDF de
un parte, una o dos páginas) y `avisos`. **F-003 no lo modifica, no lo
reordena y no lo vuelve a trocear**: lo lee.

**Salida**: un `ExtraccionParte` con los nueve campos, su confianza y la traza.
Nada más. F-004 tomará ese objeto y decidirá; F-005 lo guardará.

**Por qué el modelo ve un PDF y no imágenes sueltas**: la remesa real de
Mirasierra son páginas escaneadas sin capa de texto (hallazgo de F-002,
`specs/F-002-ingesta-troceado/design.md` §0). Un parte troceado son 1–2
páginas: cabe de sobra en una petición en línea, y el proveedor ya sabe
rasterizarlo. Rasterizarlo nosotros con PyMuPDF añadiría un paso, un formato
más que decidir (DPI, JPEG/PNG) y ninguna ventaja medible en esta fase.

**Lo que F-003 le deja a F-014, y lo que no.** Por decisión del humano del
2026-08-18 (D1, §9), el contrato incluye un noveno campo: **`numero_pagina`**,
el «Página N» que el modelo lee del pie impreso. Existe **para que F-014 pueda
reagrupar** el parte de dos hojas que F-002 no supo detectar —el escaneo no
tiene capa de texto, pero el modelo sí ve el pie—.

**F-003 no reagrupa nada.** Lo lee y lo devuelve, y ahí acaba: no une páginas,
no altera `paginas_origen`, no cambia `modo_deteccion` y no reordena la lista
de partes. Tampoco se añaden ganchos, banderas ni código muerto «preparando»
F-014: la reagrupación se diseña en su spec, con este campo ya disponible.

## 1 · Reutilización del patrón que ya corre en producción

Consultado `C:\Users\pgris\PycharmProjects\azure-apps` (documento `partes.md`,
§3.2 y §5; `albaranes.md` §3) **antes** de diseñar. El ecosistema ya extrae
documentos con Gemini —`azure-apps` documenta el proveedor pero **no fija
versión de modelo**, así que nada de allí contradice la elegida en §8— y su
patrón es:

- SDK **`google-genai`** (`from google import genai`), no la librería vieja
  `google.generativeai`.
- **Prompt en YAML** con clave (`prompt_key`) + **schema estructurado**
  (`response_json_schema` + `response_mime_type: application/json`).
- **Trazabilidad guardada con el dato**: `provider`, `model_name`,
  `prompt_key`, `schema_name`, `confianza_pct`.
- Variables de entorno con los mismos nombres: `IA_PROVIDER`, `GEMINI_API_KEY`,
  `GEMINI_MODEL`, `PROMPT_KEY`, `PROMPTS_YAML_PATH`.

F-003 **reutiliza ese patrón y esos nombres**; no inventa otro. Lo que no se
copia es el código: `partes` es otro repositorio y otro dominio (regla de
`azure-apps/`: se enlaza, no se duplica). Este proyecto todavía **no tiene
documento en `azure-apps/`** —se crea al desplegar, F-010—, así que aquí no
hay documento del ecosistema que actualizar; consta escrito para que el
reviewer no lo lea como un olvido.

## 2 · Ficheros a crear

### Dominio (puro: ni `google`, ni `yaml`, ni `tenacity`)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/domain/models/extraccion.py` | `CAMPOS_DEL_PARTE`, `CAMPOS_MANUSCRITOS`, `CampoExtraido`, `CampoBruto`, `RespuestaModelo`, `TrazaExtraccion`, `ExtraccionParte` |
| `services/postventa-api/domain/models/prompt.py` | `PromptSpec` |
| `services/postventa-api/domain/ports/extractor.py` | `ExtractorPort` (Protocol) |
| `services/postventa-api/domain/ports/prompts.py` | `RepositorioPromptsPort` (Protocol) |

### Aplicación (orquesta; habla con puertos, nunca con adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | `ContextoParte` |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | `paso_extraccion(...)` |

### Infraestructura (adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/infrastructure/llm/__init__.py` | paquete |
| `services/postventa-api/infrastructure/llm/gemini.py` | `AdaptadorGeminiVision` (implementa `ExtractorPort`) |
| `services/postventa-api/infrastructure/llm/fabrica.py` | `construir_extractor(ajustes)` y el registro `PROVEEDORES` |
| `services/postventa-api/infrastructure/prompts/__init__.py` | paquete |
| `services/postventa-api/infrastructure/prompts/prompts_yaml.py` | `RepositorioPromptsYaml` (implementa `RepositorioPromptsPort`) |

### Configuración

| Ruta | Contenido |
|---|---|
| `services/postventa-api/config/prompts.yaml` | el prompt `parte_posventa_es` (§5). **No existe hoy: lo crea esta feature.** |

### Interfaz HTTP

| Ruta | Contenido |
|---|---|
| `services/postventa-api/interface_adapters/api/extraer.py` | handler `extraer_parte(...)` y la **composición** del paso |

### Tests

| Ruta | Contenido |
|---|---|
| `services/postventa-api/tests/utiles_ia.py` | dobles y respuestas simuladas (§6). **Entregable**, como `utiles_pdf.py` en F-002 |
| `services/postventa-api/tests/test_f003_extraccion_dominio.py` | R1, R2 bis, R3, R5 |
| `services/postventa-api/tests/test_f003_paso_extraccion.py` | R2, R2 bis, R4, R6, R7, R13, R16 |
| `services/postventa-api/tests/test_f003_prompts_yaml.py` | R8, R9, R10 |
| `services/postventa-api/tests/test_f003_fabrica.py` | R11, R12 |
| `services/postventa-api/tests/test_f003_adaptador_gemini.py` | R14, R15, R16 |
| `services/postventa-api/tests/test_f003_extraer_http.py` | R17, R18 |
| `services/postventa-api/tests/test_f003_arquitectura.py` | R8 (segunda mitad), R13, R19 |

## 3 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/config/settings.py` | Añade los ajustes de IA de §8. **Todos con valor por defecto salvo la credencial, que es `None`**: `/health` y la suite tienen que seguir arrancando sin `GEMINI_API_KEY`. La credencial se exige en la fábrica (R12), no al importar. |
| `services/postventa-api/.env.example` | Añade las variables nuevas **con placeholders**, nunca con valores reales. |
| `services/postventa-api/requirements.txt` | Añade `google-genai`, `pyyaml` y `tenacity` (§7). |
| `services/postventa-api/function_app.py` | Añade la ruta `@app.route(route="extraer", methods=["POST"])`, que solo traduce `func.HttpRequest` ↔ handler y mapea `ExtraccionFallida`/`ParteDemasiadoGrande` → 502/413 y «sin fichero» → 400. |
| `services/postventa-api/domain/models/errores.py` | Añade las excepciones de dominio de §4.5. Se amplía el fichero que ya existe en vez de crear un segundo cajón de errores. |
| `services/postventa-api/tests/conftest.py` | Añade la **guardia de red** autouse (§6.3), que es el mecanismo de R19. |
| `docs/ARCHITECTURE.md` | Añade `infrastructure/prompts/` al árbol; detalla en el paso 3 del pipeline que la extracción devuelve **confianza por campo**, que **lee** el «Página N» del pie **sin reagrupar** (eso es F-014) y que no juzga la firma; anota en la tabla de sistemas externos las variables `IA_PROVIDER` / `GEMINI_MODEL`. |

## 4 · Clases y funciones

### 4.1 Dominio · modelos

```python
# domain/models/extraccion.py

CAMPOS_DEL_PARTE: tuple[str, ...] = (
    "promocion", "codigo_obra", "unidad", "numero_incidencia",
    "fecha_servicio", "descripcion", "dni_cliente", "observaciones",
    "numero_pagina",               # R2 bis: el «Página N» del pie, para F-014
)
CAMPOS_MANUSCRITOS: frozenset[str] = frozenset(
    {"fecha_servicio", "dni_cliente", "observaciones"}
)

@dataclass(frozen=True)
class CampoBruto:
    """Lo que dice el modelo, sin tocar: valor y confianza tal cual llegan."""
    valor: str | None
    confianza_pct: object          # se valida en la aplicación (R4)

@dataclass(frozen=True)
class RespuestaModelo:
    """Lo que devuelve un ExtractorPort. Sin normalizar."""
    proveedor: str
    modelo: str
    campos: Mapping[str, CampoBruto]

@dataclass(frozen=True)
class CampoExtraido:
    valor: str | None
    confianza_pct: int             # ya en 0..100 (R3, R4)

    @property
    def esta_vacio(self) -> bool: ...

@dataclass(frozen=True)
class TrazaExtraccion:
    proveedor: str
    modelo: str
    prompt_key: str
    version_prompt: str
    huella_prompt: str

@dataclass(frozen=True)
class ExtraccionParte:
    hash_parte: str
    campos: Mapping[str, CampoExtraido]   # claves == CAMPOS_DEL_PARTE, siempre
    traza: TrazaExtraccion
    avisos: tuple[str, ...] = ()

    def campo(self, nombre: str) -> CampoExtraido: ...
```

- Capa: **dominio**. `CAMPOS_MANUSCRITOS` es conocimiento del papel
  (`docs/referencia/02_parte_de_trabajo.md`), no algo que el modelo declare:
  **quién es manuscrito lo sabe el dominio**, no la IA. Lo usará F-004 para la
  regla «firmado no es conforme» sin volver a preguntarle a nadie.
- **`unidad`** es la unidad de posventa: el papel la imprime como «Vivienda» y
  el backlog la llamaba «chalet». Se llama `unidad` por decisión del humano del
  2026-08-18, para que coincida con la estructura de archivo de Posventa
  (`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`, F-013).
- **`numero_pagina`** es campo **impreso** (está en el pie), así que no entra en
  `CAMPOS_MANUSCRITOS`, y viaja por el mismo camino que los otros ocho: sin
  ninguna rama de código propia. Eso importa para el rigor `critico`: un camino
  especial para un solo campo sería superficie de mutantes gratis.
- `CampoBruto.confianza_pct` es `object` a propósito: el modelo puede devolver
  `"85"`, `120` o `null`, y quien lo saneé es la aplicación (R4), en un sitio
  probable sin proveedor.

```python
# domain/models/prompt.py
@dataclass(frozen=True)
class PromptSpec:
    clave: str
    version: str
    schema: str          # nombre del schema, para la traza
    system: str
    task: str
    huella: str          # sha256(system + "\n" + task)[:12]  (R10)
```

### 4.2 Dominio · puertos

```python
# domain/ports/extractor.py
class ExtractorPort(Protocol):
    def extraer(
        self, *, documento: bytes, mime: str, prompt: PromptSpec
    ) -> RespuestaModelo: ...

# domain/ports/prompts.py
class RepositorioPromptsPort(Protocol):
    def obtener(self, clave: str) -> PromptSpec: ...
```

Dos métodos en total. `ExtractorPort` **no** sabe de PDFs ni de partes: recibe
bytes y un mime. Eso es lo que permite cambiar de proveedor sin tocar nada por
encima (R11) y es lo que F-004 podrá reutilizar para la firma si le conviene.

### 4.3 Aplicación

```python
# application/pipelines/contexto_parte.py
@dataclass
class ContextoParte:
    parte: ParteTroceado
    extraccion: ExtraccionParte | None = None
    avisos: list[str] = field(default_factory=list)

# application/pipelines/paso_extraccion.py
MIME_PDF = "application/pdf"
MAX_BYTES_PARTE = 15 * 1024 * 1024      # R16

def paso_extraccion(
    ctx: ContextoParte,
    extractor: ExtractorPort,
    prompts: RepositorioPromptsPort,
    prompt_key: str,
) -> ContextoParte: ...
```

Lo que hace `paso_extraccion`, en orden, y **nada más**:

1. Si `len(ctx.parte.contenido) > MAX_BYTES_PARTE`, levanta
   `ParteDemasiadoGrande` **sin llamar al extractor** (R16).
2. `prompt = prompts.obtener(prompt_key)`.
3. `respuesta = extractor.extraer(documento=..., mime=MIME_PDF, prompt=prompt)`.
4. **Completa y sanea** (R2, R4): recorre `CAMPOS_DEL_PARTE` —no las claves que
   devolvió el modelo—, y por cada uno construye el `CampoExtraido`; los que
   falten salen vacíos con confianza 0 y aviso; las claves que el modelo se
   invente **se descartan con aviso** (R1/R7); las confianzas fuera de rango se
   ajustan con aviso.
5. Monta `TrazaExtraccion` con `respuesta.proveedor`, `respuesta.modelo` y los
   datos del prompt (R6, R10) y deja el `ExtraccionParte` en `ctx.extraccion`.

Recorrer **la lista declarada** y no las claves de la respuesta es lo que hace
que R2 y R7 sean la misma línea de código: no puede faltar una clave ni sobrar
una que el modelo se haya inventado.

`ContextoParte` existe porque `docs/CONVENTIONS.md` manda «pipeline + steps con
objeto contexto»: F-004 engancha `paso_validacion(ctx, ...)` detrás sin cambiar
firmas. La **composición** vive en el punto de entrada
(`interface_adapters/api/extraer.py`), nunca dentro de un paso.

### 4.4 Infraestructura

```python
# infrastructure/llm/gemini.py
PROVEEDOR = "gemini"
ERRORES_TRANSITORIOS = (...)   # timeouts, 429, 5xx del SDK

class AdaptadorGeminiVision:          # implementa ExtractorPort
    def __init__(
        self, *, api_key: str, modelo: str,
        timeout_s: int = 120, reintentos: int = 3,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,    # <- costura de test (§6.1)
    ) -> None: ...

    def extraer(self, *, documento, mime, prompt) -> RespuestaModelo: ...
```

- Construye `genai.Client(api_key=...)` **en la primera llamada**, no en el
  `__init__`, salvo que se le inyecte `cliente`. Así el objeto se puede crear
  en un test sin SDK vivo y sin abrir nada.
- La llamada usa el patrón de `partes` (`azure-apps/partes.md` §3.2):
  `system_instruction=prompt.system`, contenido = `[prompt.task, Part.from_bytes(...)]`,
  `response_mime_type="application/json"` y `response_json_schema` con el schema
  de los nueve campos (§5.2).
- **Reintentos con `tenacity`** (`docs/CONVENTIONS.md`): `retry` solo sobre
  `ERRORES_TRANSITORIOS`, `wait_exponential` a partir de `espera_inicial_s`,
  `stop_after_attempt(reintentos)`. Un error no transitorio sale a la primera
  (R15). Los tests fijan `espera_inicial_s=0` para no dormir.
- **Nada del contenido del parte entra en el log ni en el mensaje de error**
  (R15): se registran `modelo`, tamaño en bytes, nº de intento y duración. El
  parte lleva DNI.
- Parseo: `json.loads` del texto → por cada clave, `CampoBruto(valor, confianza)`.
  Si no es JSON o no es un mapping, `ExtraccionFallida`.

```python
# infrastructure/llm/fabrica.py
PROVEEDORES: dict[str, Callable[[Ajustes], ExtractorPort]] = {
    "gemini": _construir_gemini,
}

def construir_extractor(ajustes: Ajustes) -> ExtractorPort: ...
```

- Resuelve por `ajustes.ia_proveedor`. Desconocido → `ProveedorNoSoportado`
  con la lista de claves válidas. Sin credencial → `ConfiguracionIaIncompleta`
  nombrando **la variable** (`GEMINI_API_KEY`), **jamás su valor** (R12).
- Es **el único sitio** del servicio que sabe qué proveedores existen. Añadir
  uno nuevo = una función privada y una entrada en el diccionario; el pipeline
  no se entera (criterio `acceptance` 1).

```python
# infrastructure/prompts/prompts_yaml.py
class RepositorioPromptsYaml:          # implementa RepositorioPromptsPort
    def __init__(self, ruta: str | Path) -> None: ...
    def obtener(self, clave: str) -> PromptSpec: ...
```

- Carga el YAML **al construir** y valida: existe, es mapping, y cada entrada
  trae `system`, `task`, `schema` y `version` no vacíos (R9). Calcula la
  `huella` de cada prompt al cargar (R10).
- Errores con el nombre del fichero y las claves disponibles; nunca un
  `PromptSpec` a medias.
- Ruta por defecto: `ajustes.prompts_yaml` (`config/prompts.yaml`), resuelta
  **relativa al directorio del servicio**, no al cwd: la Function App arranca
  desde otro sitio.

### 4.5 Errores de dominio (se añaden a `domain/models/errores.py`)

| Excepción | Cuándo | HTTP |
|---|---|---|
| `ParteDemasiadoGrande` | R16 | 413 |
| `ExtraccionFallida` | R15 | 502 |
| `PromptNoEncontrado` | R9 | — (arranque) |
| `ProveedorNoSoportado` | R12 | — (arranque) |
| `ConfiguracionIaIncompleta` | R12 | — (arranque) |

Las tres últimas son fallos de **configuración**: revientan al construir, no
en mitad de una remesa.

`ParteDemasiadoGrande` → **413** y nunca `502`: al modelo no se le ha llamado
(R16), así que no hay proveedor roto que reportar; lo que hay es una petición
demasiado grande, y eso lo arregla el cliente. R18 de `requirements.md` y la
tarea **T16** dicen exactamente esto mismo, y **T15** le pone su test.

### 4.6 Interfaz

```python
# interface_adapters/api/extraer.py
def extraer_parte(
    contenido: bytes,
    *,
    hash_parte: str = "",
    extractor: ExtractorPort | None = None,
    prompts: RepositorioPromptsPort | None = None,
) -> dict[str, Any]: ...
```

Compone: si no le inyectan nada, construye `construir_extractor(obtener_ajustes())`
y `RepositorioPromptsYaml(...)`; ejecuta `paso_extraccion` y serializa. Los
parámetros inyectables son **la costura de test** del endpoint: los tests pasan
dobles y no hay proveedor por ninguna parte.

Contrato de respuesta (R17):

```json
{
  "hash_parte": "9f2b…",
  "campos": {
    "promocion":         {"valor": "15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)", "confianza_pct": 96},
    "codigo_obra":       {"valor": "0677", "confianza_pct": 99},
    "unidad":            {"valor": "Viviendas Bloque Villa 5", "confianza_pct": 94},
    "numero_incidencia": {"valor": "RS26.08/0123", "confianza_pct": 97},
    "fecha_servicio":    {"valor": null, "confianza_pct": 0},
    "descripcion":       {"valor": "Sellado de encuentro de falsos techos de porches", "confianza_pct": 92},
    "dni_cliente":       {"valor": "00000000T", "confianza_pct": 61},
    "observaciones":     {"valor": "Se aprecia que se han hecho parcheados", "confianza_pct": 74},
    "numero_pagina":     {"valor": "1", "confianza_pct": 98}
  },
  "traza": {
    "proveedor": "gemini",
    "modelo": "gemini-3.7-flash",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "3f9a1c2b7d04"
  },
  "avisos": ["fecha_servicio: el modelo no devolvió el campo"]
}
```

Ni una clave más: R7 lo fija con un test sobre el conjunto de claves. Todos los
valores del ejemplo son **inventados** (el DNI `00000000T` no es válido).

## 5 · `config/prompts.yaml`

### 5.1 Estructura

```yaml
# config/prompts.yaml
parte_posventa_es:
  version: "1"
  schema: parte_posventa
  system: |
    Eres un extractor de datos de PARTES DE TRABAJO de posventa …
  task: |
    Extrae los campos … Devuelve SIEMPRE los nueve campos …
```

Una clave por prompt; `PROMPT_KEY` elige cuál. Versionado en dos niveles, a
propósito:

1. **`version` declarada**: la sube quien cambia el prompt a conciencia; viaja
   en la traza y se guardará con el dato en F-005.
2. **`huella` calculada** (R10): sha256 de `system + task`, 12 hex. Detecta el
   cambio aunque nadie suba la versión. La declaración dice *qué querías*; la
   huella dice *qué había*.

### 5.2 Qué tiene que decir el prompt (contenido normativo)

Escrito contra `docs/referencia/02_parte_de_trabajo.md`, en español y **sin un
solo dato personal real**:

- El documento es un parte de trabajo de posventa impreso por Sigrid, escaneado
  y **rellenado a mano**; puede llegar girado y con calidad pobre.
- **Distingue lo impreso de lo manuscrito**, y extrae los dos. Lo manuscrito
  (observaciones y DNI) **es dato de primera, no decoración**.
- **No inventes**: si un campo no aparece o es ilegible, `valor: null` y
  `confianza_pct: 0`. Casi todos los partes traen vacíos fecha de servicio,
  horas, nombre y DNI: **eso es normal, no un fallo**.
- **Copia literal**: `numero_incidencia` con su barra (`RS26.08/0123`),
  `codigo_obra` con sus ceros a la izquierda (`0677`), la fecha tal y como esté
  escrita. Nada de reformatear ni completar.
- **Una confianza `0–100` por campo**, incluidos los manuscritos: es tu certeza
  de haber leído *ese* campo, no de que el parte esté bien.
- **`numero_pagina`**: lee el **pie impreso** de la página
  (`(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo … Página N`) y devuelve solo
  ese número como texto (`"1"`, `"2"`); si el pie no se lee, `null`. **No lo
  deduzcas** del número de páginas del documento ni de nada más: si no se ve,
  es `null` (R2 bis).
- **No juzgues la firma ni digas si el parte es válido**: eso no es tu trabajo
  (F-004). No devuelvas ningún campo que no esté en el schema.
- Salida: **JSON válido conforme al schema `parte_posventa`** y nada más.

El schema estructurado que viaja con la petición es el mismo objeto de **nueve**
campos, cada uno `{"valor": string|null, "confianza_pct": integer}`, con los
nueve `required`. Se genera **desde `CAMPOS_DEL_PARTE`**, no se escribe a mano
dos veces: una única fuente de verdad para el contrato y para el modelo. Añadir
un campo en el futuro es tocar la tupla del dominio y la línea del prompt que lo
describe, nada más.

## 6 · Los dobles de prueba y las respuestas de ejemplo

### 6.1 Dos costuras, dos dobles

| Doble | Sustituye a | Prueba |
|---|---|---|
| `ExtractorFalso` | todo el adaptador (cumple `ExtractorPort`) | el paso del pipeline y el endpoint: R2, R4, R6, R7, R13, R17, R18 |
| `ClienteGenaiFalso` | el `cliente` del SDK dentro de `AdaptadorGeminiVision` | el adaptador de verdad: parseo, reintentos, errores — R14, R15 |

Ambos viven en `services/postventa-api/tests/utiles_ia.py`, que es
**entregable**, igual que `tests/utiles_pdf.py` en F-002:

```python
def respuesta_simulada(**campos) -> RespuestaModelo
def json_del_modelo(**campos) -> str          # lo que devolvería Gemini
def prompt_de_prueba(**cambios) -> PromptSpec
class ExtractorFalso:      # registra las llamadas recibidas
class ClienteGenaiFalso:   # secuencia programable: errores y/o respuestas
```

### 6.2 De dónde salen las respuestas de ejemplo

**Se construyen en el propio test**, con `respuesta_simulada(...)` /
`json_del_modelo(...)`, y **con datos inventados**: promoción y unidad de
mentira, DNI `00000000T`, observaciones escritas para el test. **No** hay
ficheros JSON de ejemplo capturados de una llamada real, y **no** se lee
`muestras/` ni `docs/referencia/*.pdf`.

Motivo, y es duro: el parte lleva **DNI de clientes**, esos ficheros no se
versionan (`CLAUDE.md`, reglas duras), y una respuesta real pegada en el repo
sería exactamente el dato personal que no puede entrar en git. Un builder
parametrizable, además, hace legible cada test: `respuesta_simulada(dni_cliente=None)`
dice qué se está probando; un JSON de 40 líneas, no.

### 6.3 La guardia de red (mecanismo de R19)

En `tests/conftest.py`, fixture **autouse** de alcance sesión que sustituye
`socket.socket.connect` por algo que levanta `RuntimeError("la suite no puede
abrir conexiones")`. Con eso, «ni una llamada real en la suite» deja de ser una
promesa y pasa a ser **imposible**: si alguien construye el cliente de verdad
en un test, el test se cae solo. `test_f003_r19_...` comprueba que intentar una
conexión falla.

> **Alternativa ya aprobada, por si la guardia estorba** (regla del arnés: nada
> de workarounds improvisados). Si bloquear `socket` rompiera algún plugin de
> pytest o la recogida de cobertura, el implementer usa **la variante B** sin
> volver a preguntar: fixture autouse que hace que `genai.Client` levante en
> tests, más la comprobación de que ningún test importa `google` fuera de
> `utiles_ia.py`. Cualquier tercera vía es una parada y un `blocked`.

## 7 · Dependencias

A `services/postventa-api/requirements.txt` —lo que se despliega a la Function
App—, con las mismas horquillas que ya corren en `partes`:

| Paquete | Para qué |
|---|---|
| `google-genai>=0.3` | SDK de Gemini. **El nuevo**, no `google-generativeai`, que está deprecado |
| `pyyaml>=6.0` | cargar `config/prompts.yaml` |
| `tenacity>=8.2,<10.0` | reintentos con backoff, como manda `docs/CONVENTIONS.md` |

`requirements-dev.txt` del servicio ya hace `-r requirements.txt`: la suite las
hereda sin tocar nada más. **Ninguna dependencia más**: sin OCR, sin Pillow,
sin cliente HTTP propio.

## 8 · Configuración (`config/settings.py`)

| Campo | Variable | Por defecto | Notas |
|---|---|---|---|
| `ia_proveedor` | `IA_PROVIDER` | `gemini` | criterio `acceptance` 1 |
| `gemini_api_key` | `GEMINI_API_KEY` | `None` | **secreto**: en Azure va por Key Vault; en local, `.env` (que no se versiona ni se toca) |
| `gemini_model` | `GEMINI_MODEL` | `gemini-3.7-flash` | decisión del humano del 2026-08-18. Ver la nota de abajo |
| `ia_timeout_s` | `IA_TIMEOUT_S` | `120` | la Function corta a 230 s; una llamada colgada no puede comérselos |
| `ia_reintentos` | `IA_REINTENTOS` | `3` | R14 |
| `prompt_key` | `PROMPT_KEY` | `parte_posventa_es` | |
| `prompts_yaml` | `PROMPTS_YAML_PATH` | `config/prompts.yaml` | relativo al directorio del servicio |

**La credencial es opcional en `Ajustes` a propósito.** Si fuera obligatoria,
`/health` dejaría de arrancar sin clave de IA y la suite entera necesitaría una
credencial falsa en el entorno. Quien la exige es la fábrica, en el momento en
que de verdad hace falta (R12).

**Sobre el modelo `gemini-3.7-flash`.** Lo elige el humano (2026-08-18) y es
**configuración pura**: el adaptador no depende de la versión del modelo —habla
con el SDK `google-genai` y le pasa el nombre que venga de `GEMINI_MODEL`—, así
que el cambio de modelo **no altera ni una decisión de diseño**: ni los puertos,
ni el paso del pipeline, ni el schema estructurado, ni los tests (que usan
dobles). `azure-apps` documenta que `partes` y `albaranes` usan Gemini pero **no
fija versión**, luego nada de allí lo contradice; y este proyecto todavía no
tiene documento propio en `azure-apps` (se crea en F-010), así que aquí no hay
nada que actualizar fuera del repositorio.

> **Comprobación obligatoria antes de la primera llamada real.** El
> identificador exacto del modelo **se confirma contra la API** como **primer
> paso de la verificación de humo T17**, antes de gastar una sola llamada de
> extracción. Motivo: un ID mal escrito **no falla en los tests** —ahí el modelo
> está simulado y la suite seguiría verde— sino en tiempo de ejecución, y el
> síntoma (un 404 del proveedor) es fácil de confundir con un problema de
> credencial o de red. Si la API no reconociera el identificador, **es una
> parada**: se le pregunta al humano cuál es el nombre correcto, no se sustituye
> por otro modelo por iniciativa propia.

## 9 · Riesgos y decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Confianza **entera 0–100** (`confianza_pct`) | float 0.0–1.0 | Es el nombre y la escala que ya usan `partes` y `albaranes` en el ecosistema; los modelos la devuelven mejor en 0–100; y evita una conversión que solo aporta mutantes |
| Saneo y completado en la **aplicación** | En el adaptador | Se prueba sin proveedor y vale igual para el siguiente proveedor que entre: si lo hiciera el adaptador, habría que repetirlo en cada uno |
| Recorrer `CAMPOS_DEL_PARTE` y no las claves de la respuesta | Confiar en lo que devuelva el modelo | Un campo que falta rompería F-004 y una clave inventada ensuciaría el contrato. Así R2 y R7 son la misma línea |
| Enviar el **PDF** al modelo | Rasterizar a PNG con PyMuPDF | Un paso más, dos parámetros más que decidir (DPI, formato) y ninguna ventaja: 1–2 páginas caben en línea |
| El adaptador acepta un `cliente` inyectable | `monkeypatch` de `genai.Client` en los tests | Una costura explícita se ve en la firma; un parcheo global se pudre en cuanto el SDK cambia de nombre interno |
| Fábrica con **registro** de proveedores | `if proveedor == "gemini": ... elif ...` | Añadir proveedor = una entrada del diccionario; y el test de R12 comprueba la lista, no una cadena de `if` |
| Guardia de red en `conftest.py` | Confiar en que nadie llame de verdad | «Ni una llamada real» debe ser **imposible**, no una promesa |
| Prompt con `version` **y** huella calculada | Solo la versión declarada | Nadie sube la versión el día que toca una coma. La huella no se olvida |

### Decisiones del humano, resueltas el 2026-08-18

Las cuatro decisiones que este diseño dejó abiertas están **resueltas**. Se
conservan aquí, con lo decidido, porque explican por qué el diseño es como es.

**D1 · `numero_pagina` entra en el contrato de F-003. RESUELTA: SÍ.** F-014
(«reagrupar el parte de dos hojas») necesita el «Página N» del pie, y **el
modelo lo ve aunque el escaneo no tenga capa de texto** — justo lo que F-002 no
pudo leer. Es el noveno campo de `CAMPOS_DEL_PARTE` (§4.1), con su línea en el
prompt (§5.2), su requisito **R2 bis**, sus tests
(`test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie`,
`test_f003_r2bis_la_extraccion_no_reagrupa_paginas`) y su tarea **T6**.
**F-003 lo lee y lo devuelve; no reagrupa nada** (§0).

**D2 · El endpoint `POST /api/extraer` entra en F-003. RESUELTA: SÍ.** Los
cinco criterios `acceptance` no lo piden, pero `docs/ARCHITECTURE.md` define el
contrato HTTP como «`/split` rápido y luego **una llamada por parte**», y sin
endpoint la extracción no la puede ejercitar nadie: ni el front (F-007), ni las
verificaciones manuales contra partes reales. Se queda R17, R18,
`interface_adapters/api/extraer.py` y las tareas T15/T16.

**D3 · `harness/rutas_sensibles.json` NO se declara en F-003. RESUELTA:
aceptada la recomendación.** El evaluador del prompt se abre como feature
propia: **F-015 · «Evaluación del prompt de extracción contra partes reales»**
(prioridad 15, `blocked_by` F-003), que la registra el líder en
`harness/features.json`. La ruta sensible se declarará **cuando el comando
exista**, no antes.

El razonamiento, que sigue vigente: `config/prompts.yaml` es el caso de manual
del mecanismo —**ningún test unitario detecta que un cambio de redacción empeore
la extracción**, porque el modelo está simulado y la suite seguiría verde con el
prompt roto—. Pero una verificación declarada cuyo comando nadie puede ejecutar
es **protección falsa**, que es justo contra lo que avisa
`harness/rutas_sensibles.ejemplo.json`. Mientras F-015 no exista, el hueco lo
tapa la verificación `MANUAL (humano)` **T18**, que es la misma comprobación
hecha a mano.

Material para F-015 — el borrador de la declaración, ya escrito:

```jsonc
{
  "nombre": "evaluacion-prompt",
  "comando": "python -m harness.evals_prompt --feature {feature}",
  "informe": "progress/evals_{feature}.md",
  "exigencia": "aviso",
  "exige_lineas": ["VEREDICTO: VERDE"],
  "rutas": [
    { "patron": "services/postventa-api/config/prompts.yaml",
      "motivo": "el prompt del modelo: un cambio de redacción no lo caza ningún test" },
    { "patron": "services/postventa-api/domain/models/extraccion.py",
      "motivo": "el schema que el modelo rellena" }
  ]
}
```

Y el aviso que F-015 debe tener delante desde el primer día: **ese evaluador
sería genérico**. Un juego de documentos de prueba, una llamada real con
credencial, un umbral de acierto y un informe con veredicto le sirve igual a
`partes` y a `albaranes`. Por la **regla de propagación** del arnés, su sitio
natural es **`arnes-base`**, no este repositorio; lo específico de posventa
—los partes de prueba y el umbral— es lo único que se queda aquí.

**D4 · El campo de la unidad de posventa se llama `unidad`. RESUELTA.** Ni
`chalet` (como decía el backlog) ni `vivienda` (como lo imprime el papel):
**`unidad`**, que es el término que ya usa la estructura de archivo de Posventa
(`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`, F-013). El mismo concepto se
llama igual en el código y en el archivo. La tabla de R1 en `requirements.md`
deja escritos los tres nombres para que nadie lo lea como un descuido.

### Riesgos abiertos

**Riesgo 1 · el acierto real del modelo no lo mide ningún test.** La suite
demuestra el *contrato*, no la *calidad de lectura*. Con manuscritos de mala
letra y escaneos flojos, la única medida es contra partes reales, y eso es
`MANUAL (humano)` (**T18**) hasta que exista **F-015**.

Por eso **T18 se ejecuta en cuanto el adaptador y el endpoint están hechos**
(justo detrás de T16), y no al final de la lista: si el modelo no lee estos
manuscritos, no falla F-003 —su contrato se cumpliría igual— sino la premisa del
proyecto, y enterarse antes ahorra la documentación (T19) y **la campaña de
mutación entera** (T20).

**Riesgo 2 · el coste y el tiempo por parte.** Una llamada multimodal por
parte, 22 partes por remesa. Si el modelo tarda más de lo previsto, la
concurrencia limitada del front (F-007) es lo que lo absorbe, no un lote más
grande: la Function corta a los 230 s y `docs/ARCHITECTURE.md` ya decidió ir
parte a parte.

**Riesgo 3 · el SDK `google-genai` es joven y cambia.** Todo lo que sabe de él
está en **un fichero** (`infrastructure/llm/gemini.py`), detrás del puerto. Si
cambia la firma, se cambia ahí y ni el dominio ni la aplicación se enteran; el
test del adaptador (con `ClienteGenaiFalso`) es el que avisa.

**Riesgo 4 · datos personales en logs.** El parte lleva DNI. Está prohibido
volcar el contenido, la respuesta cruda del modelo o los valores extraídos en
el log o en un mensaje de error (R15). Se registran tamaños, tiempos, modelo y
nombres de campo. Cualquier volcado «para depurar» es un fallo de review.

**Riesgo 5 · el paso no sabe reagrupar dos hojas.** Si un parte de dos hojas
llegó partido en dos por F-002, F-003 lo extrae **como dos partes** y ninguno
de los dos tendrá todos los campos. Es F-014 y está aceptado por el humano el
2026-08-18 (`specs/F-002-ingesta-troceado/design.md` §0). Aquí solo consta.

## 10 · SQL

**No aplica.** F-003 no lee ni escribe en ninguna base de datos: la
persistencia es F-005, con su propio schema. Ni una sentencia, ni un fichero
`NN_nombre.sql`, ni una conexión.

## 11 · Límite de microservicio

F-003 cae **entera** dentro de `services/postventa-api/`. No toca el front
(F-007), no toca `sigrid-api`, no toca SharePoint, no toca el PostgreSQL
compartido y no ejecuta SQL. La única pieza que *no* pertenecería a este
servicio es el **evaluador de prompts** de **F-015**: es herramienta de
arnés, valdría para `partes` y `albaranes` igual, y su sitio es `arnes-base`
—por eso se propone, y no se implementa aquí—.

## 12 · Ficheros que NO se tocan (los que tientan)

- `domain/models/remesa.py`, `domain/models/pie_de_pagina.py`,
  `domain/ports/pdf.py`, `domain/ports/comprimido.py`,
  `infrastructure/documentos/**`, `application/pipelines/contexto.py`,
  `application/pipelines/paso_ingesta.py`, `paso_troceado.py`,
  `interface_adapters/api/split.py` — **son F-002**. F-003 consume
  `ParteTroceado`; no lo amplía, no lo reordena, no lo vuelve a trocear. Si al
  implementar pareciera necesario cambiarlos, **es una parada**, no un ajuste.
- `interface_adapters/api/health.py`, `config/logging_config.py`,
  `tests/test_health.py`, `tests/test_f001_adaptador_http.py` — F-001 está
  cerrada.
- **Nada de validación ni de firma** (F-004), **nada de persistencia ni SQL**
  (F-005), **nada de nombrado ni SharePoint** (F-006), **nada de Sigrid**
  (F-008/F-009). R7 lo vigila con un test sobre las claves del resultado.
- `services/postventa-front/` — consume `/api/extraer` en F-007. No se toca ni
  se declara en `harness/servicios.json`.
- `harness/rutas_sensibles.json` — **no se crea** en esta feature: es F-015
  (decisión D3, resuelta el 2026-08-18).
- `muestras/`, `docs/referencia/*.pdf`, `.gitignore`, `.env` — los originales
  no se versionan, `.env` no se toca jamás, y **ningún test los mira**.
- `azure-apps/` — este servicio aún no tiene documento allí (F-010).
