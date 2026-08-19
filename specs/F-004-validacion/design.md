<!-- specs/F-004-validacion/design.md -->
# F-004 · Validación del parte y clasificación de la firma — Diseño técnico

> Encaja en `docs/ARCHITECTURE.md` (paso **4** del pipeline) y en
> `docs/CONVENTIONS.md`. Servicio: **`services/postventa-api/`** y solo ese.
>
> **Ni un dato real.** Los ejemplos de este documento están inventados, igual
> que los de `config/prompts.yaml`.

## 0 · La frontera: qué entra, qué sale y qué se queda fuera

**Entra**: el `ExtraccionParte` de F-003 (nueve campos con su confianza) y una
**lectura de la firma** que esta feature produce.

**Sale**: un `ResultadoValidacion` con veredicto, destino, motivos y —cuando
las hay— la transcripción de las observaciones.

**Se queda fuera, y consta por escrito para que nadie lo lea como un olvido:**

| Fuera de F-004 | Dónde va | Por qué |
|---|---|---|
| Interpretar **qué dice** la observación | **F-016** | F-004 detecta que hay observaciones y las transcribe; no las juzga. Ningún test de F-004 depende del contenido (R10) |
| Comprobar contra Sigrid que la incidencia existe y está abierta | **F-008 / F-009** | `docs/ARCHITECTURE.md` lo pone en el paso 4, pero necesita red, y el `acceptance` exige reglas puras. Es una **segunda puerta**, posterior y con red, no parte de la validación documental |
| **Guardar** la cola de validación humana | **F-005** | La persistencia es su feature, con su schema propio |
| **Enseñar** la cola y recoger la decisión de la persona | **F-007 / F-011** | Es front |
| Reagrupar el parte de dos hojas | **F-014** | F-004 valida el parte que le llega, sea de una o dos páginas |

**Qué es «la cola» dentro de F-004**, entonces: un **destino declarado en el
resultado** (`cola_validacion_humana`) más las pruebas que necesita quien
decida (la transcripción y su confianza). F-004 dice **quién entra y con qué
delante**; F-005 lo guarda y F-007/F-011 lo pintan. Por eso F-016 está
`blocked_by` F-004: F-004 es quien define la entrada de esa cola.

## 1 · La tensión del enunciado, resuelta

`docs/ARCHITECTURE.md` (semántica **3**) dice que la firma debe ser humana y
que **un parte sin firma válida no se archiva ni se cierra: va a revisión
manual**. La decisión (2) del humano dice que las observaciones manuscritas
son **de momento el único motivo de rechazo**. Parecen incompatibles. No lo
son, y esta es la lectura que hace consistente la ficha entera:

1. La frase del humano viene acompañada, en `docs/ARCHITECTURE.md` 3 bis, de
   su propia acotación: *«Ningún otro **dato manuscrito** descalifica el
   parte»*. El alcance de «único motivo» son **los datos manuscritos** —DNI,
   fecha, horas, nombre—, no la firma, que no es un dato transcrito sino la
   conformidad misma.
2. El propio `acceptance` de F-004 exige que **un parte sin nº de incidencia o
   sin código de obra nunca quede apto**. Si «único motivo de rechazo» se
   leyera como «lo único que impide ser apto», ese criterio se contradiría con
   el anterior en la misma lista. Luego no puede leerse así.
3. El criterio está redactado con precisión: *«ninguna otra regla manda un
   parte **a la cola** por su cuenta»*. **A la cola.** La cola de validación
   humana es el destino de la decisión sobre la reparación, y ahí solo entra
   quien trae observaciones.

**De ahí salen dos destinos distintos, y no es una sutileza: son dos trabajos
distintos para dos personas distintas.**

| Destino | Qué significa | Qué tiene que hacer la persona |
|---|---|---|
| `cola_validacion_humana` | El parte está completo y firmado, pero el cliente escribió algo | **Decidir**: leer la observación y decir si la reparación se da por buena |
| `revision_manual` | Al parte le faltan los mínimos (dato decisivo ilegible o sin firma humana) | **Arreglar**: volver al papel, releer o pedir el parte otra vez |

Y con eso, las tres afirmaciones se sostienen a la vez:

- Las observaciones son el único motivo por el que un parte **completo y
  firmado** se rechaza (decisión 2). ✔
- Ese rechazo **no descarta** el parte: va a la cola con el texto delante
  (decisión 3). ✔
- Un parte sin firma humana no se archiva ni se cierra: va a revisión manual
  (`docs/ARCHITECTURE.md` 3, y `CHECKPOINTS.md` C3, que exige que una marca
  simple «nunca cuente como firma del cliente»). ✔

**Aun así, el punto 3 queda como decisión abierta D1 (§7)**: la lectura es
defendible, pero convierte la firma en algo que puede bloquear un parte, y eso
lo tiene que confirmar el humano con el dato de T14 delante. La spec se
implementa con esta lectura porque es la única compatible con los documentos
normativos; si el humano decide lo contrario, cambia **una** función pura y sus
tests, no el diseño.

## 2 · De dónde sale la clasificación de la firma (límite de microservicio)

La firma hay que **mirarla**: no está en ningún campo de texto. La pregunta
que toca contestar aquí es si eso cabe en este servicio y en esta feature, o
si hay que apoyarse en lo que ya existe.

**Cabe, y se apoya en lo que ya existe.** Es el mismo parte, el mismo dominio y
el mismo `ExtractorPort` de F-003, que se diseñó a propósito sin saber de
partes: recibe `documento: bytes`, `mime` y un `PromptSpec`. Su docstring ya lo
anticipa: *«es lo que F-004 podrá reutilizar para la firma si le conviene»*.
Así que **no se crea ningún adaptador nuevo, ningún proveedor nuevo, ninguna
dependencia nueva y ningún microservicio nuevo**: se añade **un segundo
prompt** y se reutiliza toda la tubería.

### Las tres vías que se estudiaron

| Vía | En qué consiste | Veredicto |
|---|---|---|
| **A** · un décimo campo `clasificacion_firma` en el contrato de F-003 | Una sola llamada de IA por parte | **Descartada**. Obliga a reescribir `parte_posventa_es`, el prompt **cuya calidad se midió ayer sobre 22 partes reales**, y *ningún test unitario detecta que un cambio de redacción empeore la extracción* (el modelo está simulado). Sin F-015, la única red de seguridad es volver a barrer los 22 partes a mano. Se pondría en riesgo lo que ya funciona para ahorrar una llamada barata |
| **B** · prompt propio `firma_parte_es` sobre el mismo `ExtractorPort` | Dos llamadas por parte, **independientes entre sí** | **Elegida** |
| **C** · detectar la firma por píxeles (densidad de tinta en la casilla) | Sin IA | **Descartada**. Exige conocer las coordenadas de la casilla en un escaneo torcido, añade dependencias de imagen, y **no distingue un aspa de una firma**, que es justo lo que pide el `acceptance` |

**Por qué B no duplica el tiempo de proceso**: las dos lecturas son
independientes —ninguna necesita el resultado de la otra—, así que el front
(F-007) puede lanzar `/api/extraer` y `/api/firma` **en paralelo** para el
mismo parte. Cada una gasta su propio presupuesto de 230 s de la Function, que
es justo lo que se perdería si se compusieran dentro de una sola invocación
(dos llamadas de 120 s de timeout suman 240 s y **se pasan del corte**).

**Coste**: dos llamadas multimodales por parte, 44 en una remesa como la de
Mirasierra. Con el modelo *flash* configurado es asumible, y el prompt de
firma es corto: una pregunta, una etiqueta.

**Y lo que se gana, además de no tocar el prompt medido**: la lectura de la
firma se puede reintentar, cambiar o apagar sin rozar la extracción, y su
verificación manual es pequeña y dirigida (T14), no un barrido de nueve campos.

### El obstáculo real de la vía B, y cómo se resuelve

`infrastructure/llm/gemini.py` hoy manda **siempre** el schema de los nueve
campos: `schema_del_parte()` está incrustado en la llamada, así que un segundo
prompt recibiría el schema equivocado.

Se arregla usando algo que ya existe y hoy es decorativo: **`PromptSpec.schema`
ya lleva el nombre del schema**. El adaptador pasa a resolver ese nombre contra
un **registro del dominio**:

```python
# domain/models/schemas.py
CAMPOS_POR_SCHEMA: Mapping[str, tuple[str, ...]] = {
    "parte_posventa": CAMPOS_DEL_PARTE,     # F-003, nueve campos
    "firma_cliente": CAMPOS_DE_LA_FIRMA,    # F-004, uno
}
```

Se conserva intacta la regla de F-003 —**la lista de campos vive en el dominio
y es fuente única** para el contrato y para el modelo—; lo que se quita es que
el adaptador supiera de memoria cuál de ellas usar. El adaptador deja de servir
a un solo prompt, que es lo que ya prometían `PROMPT_KEY` y el registro de
prompts.

## 3 · Ficheros

### 3.1 A crear

#### Dominio (puro: ni `google`, ni `yaml`, ni HTTP, ni SQL)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/domain/models/firma.py` | `ClasificacionFirma`, `CAMPOS_DE_LA_FIRMA`, `CAMPO_CLASIFICACION`, `clasificacion_desde_texto()`, `LecturaFirma` |
| `services/postventa-api/domain/models/schemas.py` | `CAMPOS_POR_SCHEMA` y `campos_del_schema(nombre)` |
| `services/postventa-api/domain/models/validacion.py` | `Veredicto`, `Destino`, `CodigoMotivo`, `Motivo`, `ResultadoValidacion`, `CAMPOS_DECISIVOS`, `UMBRAL_CONFIANZA`, `validar_parte()` |

#### Aplicación (orquesta; habla con puertos, nunca con adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/application/pipelines/confianza.py` | `sanear_confianza()`, `CONFIANZA_MINIMA`, `CONFIANZA_MAXIMA` — **extraídas** de `paso_extraccion.py`, sin cambiar su comportamiento |
| `services/postventa-api/application/pipelines/paso_firma.py` | `paso_firma(ctx, extractor, prompts, prompt_key)` |
| `services/postventa-api/application/pipelines/paso_validacion.py` | `paso_validacion(ctx)` |

#### Interfaz HTTP

| Ruta | Contenido |
|---|---|
| `services/postventa-api/interface_adapters/api/firma.py` | handler `leer_firma(...)` y la composición del paso |
| `services/postventa-api/interface_adapters/api/validar.py` | handler `validar(...)`: deserializa, valida y serializa. **Sin IA** |

#### Tests

| Ruta | Requisitos |
|---|---|
| `services/postventa-api/tests/utiles_validacion.py` | **entregable**: builders de extracción y de lectura de firma para los tests (§6) |
| `services/postventa-api/tests/test_f004_firma_dominio.py` | R1, R2, R14 |
| `services/postventa-api/tests/test_f004_reglas_validacion.py` | R6–R19 |
| `services/postventa-api/tests/test_f004_paso_firma.py` | R2, R3, R23 (parte de) |
| `services/postventa-api/tests/test_f004_paso_validacion.py` | R21 |
| `services/postventa-api/tests/test_f004_prompts_firma.py` | R4, R5 |
| `services/postventa-api/tests/test_f004_firma_http.py` | R23 |
| `services/postventa-api/tests/test_f004_validar_http.py` | R24 |
| `services/postventa-api/tests/test_f004_arquitectura.py` | R20, R22, R25, R26 |

### 3.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `application/pipelines/paso_extraccion.py` | **Solo** deja de tener copia propia del saneo: importa `sanear_confianza` de `confianza.py`. Comportamiento idéntico; **los tests de F-003 tienen que pasar sin tocarlos**, y esa es la prueba |
| `application/pipelines/contexto_parte.py` | Añade `lectura_firma: LecturaFirma \| None` y `validacion: ResultadoValidacion \| None` |
| `infrastructure/llm/gemini.py` | `schema_del_parte()` → `schema_para(nombre)`, que resuelve contra `CAMPOS_POR_SCHEMA`; la llamada usa `prompt.schema`. Nombre desconocido → `SchemaDesconocido` **antes** de llamar al modelo |
| `domain/models/errores.py` | Añade `SchemaDesconocido`, `ValidacionSinDatos` y `CuerpoDeValidacionInvalido` |
| `domain/models/extraccion.py` | **Solo comentario**: el docstring de `CAMPOS_MANUSCRITOS` dice que F-004 decidirá con ese conjunto la regla «firmado no es conforme». Tras la decisión del 2026-08-19 el conjunto que decide es **solo `observaciones`**; se corrige el texto para que no quede una afirmación falsa |
| `config/prompts.yaml` | **Añade** la clave `firma_parte_es` (§4). `parte_posventa_es` **no se toca ni una coma**: R4 lo fija clavando su huella |
| `config/settings.py` | Añade `prompt_key_firma` (`PROMPT_KEY_FIRMA`, por defecto `firma_parte_es`) |
| `.env.example` | Añade `PROMPT_KEY_FIRMA` con su valor por defecto. Ningún secreto |
| `function_app.py` | Dos rutas nuevas: `POST /api/firma` y `POST /api/validar`, solo traducción |
| `tests/test_f003_adaptador_gemini.py` | Se adapta al renombrado `schema_del_parte()` → `schema_para("parte_posventa")`. **Solo eso**: ni una aserción cambia de significado |
| `docs/ARCHITECTURE.md` | Paso 4 del pipeline: los dos destinos, la cola de validación humana y qué queda para F-008/F-016. Semántica 3: cómo conviven la regla de la firma y el «único motivo de rechazo» (§1) |

### 3.3 Ficheros que NO se tocan (los que tientan)

- `domain/models/remesa.py`, `pie_de_pagina.py`, `infrastructure/documentos/**`,
  `paso_ingesta.py`, `paso_troceado.py`, `interface_adapters/api/split.py` —
  **son F-002**. F-004 no trocea, no reagrupa y no vuelve a abrir el PDF de la
  remesa.
- `domain/ports/extractor.py`, `domain/ports/prompts.py` — **los puertos no
  cambian**. Si al implementar pareciera necesario tocarlos, **es una parada**:
  significaría que la vía B no era la correcta.
- `infrastructure/prompts/prompts_yaml.py`, `infrastructure/llm/fabrica.py` —
  cargan y construyen igual; una clave más en el YAML no les afecta.
- `interface_adapters/api/extraer.py` y su contrato (R17 de F-003) — el cuerpo
  de `/api/extraer` **no gana ninguna clave**. `/api/validar` lo consume tal
  cual.
- `config/prompts.yaml` → la clave `parte_posventa_es`: **intocable** en esta
  feature (R4).
- `muestras/`, `docs/referencia/*.pdf`, `.env`, `.gitignore` — no se versionan,
  no se tocan y **ningún test los mira**.
- `harness/features.json`, `BACKLOG.md` — los lleva el líder / se generan.
- `services/postventa-front/` — la cola se pinta en F-007/F-011.
- Nada de persistencia, SQL, SharePoint ni Sigrid.

## 4 · Clases y funciones

### 4.1 Dominio · la firma

```python
# domain/models/firma.py

class ClasificacionFirma(str, Enum):
    HUMANA = "humana"
    MARCA_SIMPLE = "marca_simple"
    CASILLA_VACIA = "casilla_vacia"
    ILEGIBLE = "ilegible"

CAMPO_CLASIFICACION = "clasificacion_firma"
CAMPOS_DE_LA_FIRMA: tuple[str, ...] = (CAMPO_CLASIFICACION,)

def clasificacion_desde_texto(texto: str | None) -> ClasificacionFirma:
    """La etiqueta que dice el modelo, o ILEGIBLE si no es una de las cuatro."""

@dataclass(frozen=True)
class LecturaFirma:
    hash_parte: str
    clasificacion: ClasificacionFirma
    confianza_pct: int
    traza: TrazaExtraccion
    avisos: tuple[str, ...] = ()

    @property
    def es_conformidad_del_cliente(self) -> bool:
        """HUMANA y con confianza suficiente. Cualquier duda, no (R14)."""

    @property
    def clasificacion_efectiva(self) -> ClasificacionFirma:
        """La etiqueta que se PUBLICA: ILEGIBLE si una HUMANA no llega
        al umbral; en cualquier otro caso, la que dijo el modelo (R14 bis)."""
```

- Capa **dominio**. `clasificacion_desde_texto` **nunca** devuelve `HUMANA`
  ante una etiqueta desconocida (R2): el fallo por defecto cae siempre del lado
  seguro. Normaliza minúsculas y espacios; nada más.
- **`clasificacion_efectiva` es la que sale al mundo** (decisión **D4**,
  resuelta por el humano el 2026-08-19): cuando R14 degrada una `humana`
  dudosa, lo que se publica es `ilegible`. Es la única etiqueta coherente con
  el motivo que se emite: publicar `humana` al lado de un destino de revisión
  manual es incomprensible para quien lo lea en Posventa. La lectura cruda
  sigue viva en `clasificacion` —y viaja entera en la respuesta de
  `/api/firma`, que es justo la entrada de `/api/validar`—, así que **no se
  añade ningún campo al contrato** para conservarla.
- Se reutiliza `TrazaExtraccion` de F-003 en vez de inventar una traza gemela:
  es exactamente el mismo dato (proveedor, modelo, prompt, versión, huella).

### 4.2 Dominio · las reglas

```python
# domain/models/validacion.py

class Veredicto(str, Enum):
    APTO = "apto"
    NO_APTO = "no_apto"

class Destino(str, Enum):
    ARCHIVO_Y_CIERRE = "archivo_y_cierre"
    COLA_VALIDACION_HUMANA = "cola_validacion_humana"
    REVISION_MANUAL = "revision_manual"

class CodigoMotivo(str, Enum):
    CODIGO_OBRA_NO_LEGIBLE = "codigo_obra_no_legible"
    NUMERO_INCIDENCIA_NO_LEGIBLE = "numero_incidencia_no_legible"
    FIRMA_NO_HUMANA = "firma_no_humana"
    OBSERVACIONES_MANUSCRITAS = "observaciones_manuscritas"

#: Los únicos campos de texto que deciden (ARCHITECTURE 4 bis).
CAMPOS_DECISIVOS: tuple[str, ...] = ("codigo_obra", "numero_incidencia")

#: Por debajo de esto, un dato no se considera leído.
UMBRAL_CONFIANZA = 50

@dataclass(frozen=True)
class Motivo:
    codigo: CodigoMotivo
    texto: str            # castellano llano, para Posventa

@dataclass(frozen=True)
class ResultadoValidacion:
    hash_parte: str
    veredicto: Veredicto
    destino: Destino
    motivos: tuple[Motivo, ...]
    clasificacion_firma: ClasificacionFirma   # la EFECTIVA (D4), no la cruda
    observaciones: str | None          # transcripción literal, para la cola
    confianza_observaciones: int
    avisos: tuple[str, ...] = ()

    @property
    def es_apto(self) -> bool: ...

def validar_parte(
    extraccion: ExtraccionParte, firma: LecturaFirma
) -> ResultadoValidacion: ...
```

`validar_parte` es **una función pura**: mismas entradas, mismo resultado, sin
reloj, sin azar, sin red. Hace exactamente esto, en este orden:

1. Reúne los motivos, **en el orden declarado** y **sin cortar al primero**
   (R18): campo decisivo ilegible → un motivo por campo; firma que no es
   conformidad → `FIRMA_NO_HUMANA` con el texto que corresponda a la etiqueta;
   observaciones no vacías → `OBSERVACIONES_MANUSCRITAS`.
2. Sin motivos → `APTO` + `ARCHIVO_Y_CIERRE`.
3. Un único motivo y es el de observaciones → `NO_APTO` +
   `COLA_VALIDACION_HUMANA` (R9).
4. Cualquier otro caso → `NO_APTO` + `REVISION_MANUAL` (R19).
5. La transcripción de las observaciones viaja **siempre** que la haya, vaya el
   parte a la cola o a revisión manual: quien lo mire la necesita delante.

**`clasificacion_firma` se rellena con `firma.clasificacion_efectiva`, no con
`firma.clasificacion`** (R14 bis, decisión **D4** de §7). Así, una `humana` con
confianza por debajo del umbral sale del resultado —y del JSON de
`/api/validar`— como `ilegible`, que es lo mismo que dice el motivo
`firma_no_humana` que la acompaña. Una única fuente para las dos cosas: si
alguien lee la etiqueta y el motivo, no puede leerlos contradiciéndose.

**Por qué la regla vive en `domain/models/`** y no en un paquete nuevo: es el
patrón que ya sigue este servicio —`domain/models/remesa.py` alberga
`es_nombre_de_pdf()`—, y el `acceptance` exige que las reglas sean **dominio
puro**. Ponerlas en `application/` las sacaría del dominio; abrir
`domain/servicios/` para una función chocaría con el `application/services/`
que ya existe.

**Legibilidad de un campo decisivo** (R12): `no campo.esta_vacio and
campo.confianza_pct >= UMBRAL_CONFIANZA`. `esta_vacio` ya lo da F-003 y ya
trata «solo espacios» como vacío.

**El umbral es una constante del dominio, no configuración.** Aflojarlo por
variable de entorno sería aflojar una regla de negocio sin revisión. El valor
50 sale del dato real: los seis campos impresos vinieron con confianzas medias
de **98,8 a 99,2** en los 22 partes de Mirasierra, así que 50 está a un abismo
de lo normal y solo dispara ante una lectura de verdad dudosa.

**El umbral no se aplica a `observaciones`**: una observación leída con poca
confianza es **más** motivo de revisión, no menos. Cualquier texto no vacío
manda el parte a la cola, y su confianza viaja en el resultado para que quien
decida sepa cuánto fiarse de la transcripción.

### 4.3 Aplicación

```python
# application/pipelines/confianza.py
CONFIANZA_MINIMA = 0
CONFIANZA_MAXIMA = 100
def sanear_confianza(declarada: object) -> tuple[int, str | None]: ...

# application/pipelines/paso_firma.py
def paso_firma(
    ctx: ContextoParte,
    extractor: ExtractorPort,
    prompts: RepositorioPromptsPort,
    prompt_key: str,
) -> ContextoParte: ...

# application/pipelines/paso_validacion.py
def paso_validacion(ctx: ContextoParte) -> ContextoParte: ...
```

- `paso_firma` es el gemelo pequeño de `paso_extraccion`: mismo tope de tamaño
  (`MAX_BYTES_PARTE`, importado, no duplicado), mismo saneo de confianza, misma
  traza. Lo que cambia es que traduce **un** campo a la enumeración.
- `paso_validacion` **no recibe puertos**: no los necesita. Si falta la
  extracción o la lectura de firma levanta `ValidacionSinDatos` (R21): un
  veredicto inventado sobre datos que no están es peor que un error.
- La **composición** vive en los puntos de entrada, como manda
  `docs/CONVENTIONS.md`; ningún paso construye adaptadores.

### 4.4 Errores nuevos (`domain/models/errores.py`)

| Excepción | Cuándo | HTTP |
|---|---|---|
| `SchemaDesconocido` | un prompt declara un `schema` que el dominio no registra | — (configuración; revienta antes de llamar al modelo) |
| `ValidacionSinDatos` | se pide validar sin extracción o sin lectura de firma | 400 |
| `CuerpoDeValidacionInvalido` | el cuerpo de `/api/validar` no trae lo que dice el contrato | 400 |

`ParteDemasiadoGrande` (413) y `ExtraccionFallida` (502) se **reutilizan** tal
cual en `/api/firma`: es la misma tubería y los mismos fallos.

### 4.5 Interfaz

```python
# interface_adapters/api/firma.py
def leer_firma(
    contenido: bytes, *, hash_parte: str = "",
    extractor: ExtractorPort | None = None,
    prompts: RepositorioPromptsPort | None = None,
) -> dict[str, Any]: ...

# interface_adapters/api/validar.py
def validar(cuerpo: Mapping[str, Any]) -> dict[str, Any]: ...
```

`POST /api/firma` — `multipart/form-data` con el PDF de un parte y `hash`:

```json
{
  "hash_parte": "9f2b…",
  "firma": {"clasificacion": "humana", "confianza_pct": 93},
  "traza": {
    "proveedor": "gemini", "modelo": "gemini-3.7-flash",
    "prompt_key": "firma_parte_es", "version_prompt": "1",
    "huella_prompt": "1a2b3c4d5e6f"
  },
  "avisos": []
}
```

`POST /api/validar` — JSON con **el cuerpo tal cual** de los otros dos
endpoints. No se admite un cuerpo montado a mano: si `/api/extraer` y
`/api/firma` emiten esa forma, aceptar exactamente esa forma es lo que impide
que el front invente datos por el camino.

```json
{
  "extraccion": { "hash_parte": "9f2b…", "campos": { }, "traza": { }, "avisos": [] },
  "firma":      { "hash_parte": "9f2b…", "firma": { }, "traza": { }, "avisos": [] }
}
```

Respuesta (ejemplo **inventado**, un parte firmado con observaciones):

```json
{
  "hash_parte": "9f2b…",
  "veredicto": "no_apto",
  "destino": "cola_validacion_humana",
  "motivos": [
    {
      "codigo": "observaciones_manuscritas",
      "texto": "El parte trae observaciones escritas a mano. Firmado no es lo mismo que conforme: alguien tiene que leerlas y decidir si la reparación se da por buena."
    }
  ],
  "firma": {"clasificacion": "humana", "confianza_pct": 93},
  "observaciones": {
    "texto": "Falta rematar el rodapié del salón",
    "confianza_pct": 74
  },
  "avisos": []
}
```

En ese ejemplo la firma vino `humana` con 93 de confianza y se publica tal
cual. **Si hubiera venido `humana` por debajo del umbral, `firma.clasificacion`
de esta respuesta diría `ilegible`** (R14 bis / D4): este campo sale de
`ResultadoValidacion.clasificacion_firma`, que ya es la etiqueta efectiva. La
respuesta de `/api/firma`, en cambio, sigue publicando la lectura **cruda** del
modelo: es la que registra qué vio, y es la entrada de este endpoint.

Textos de los motivos, en castellano llano y sin jerga (R6):

| Código | Texto |
|---|---|
| `codigo_obra_no_legible` | «No se lee el código de obra del parte. Sin él no se sabe en qué carpeta va ni cómo se llama el fichero.» |
| `numero_incidencia_no_legible` | «No se lee el nº de incidencia. Sin él no se puede nombrar el parte ni cerrar la incidencia.» |
| `firma_no_humana` · casilla vacía | «La casilla de la firma del cliente está vacía: no hay conformidad.» |
| `firma_no_humana` · marca simple | «En la casilla de la firma hay una marca simple —un aspa o un trazo—, no una firma. Eso no es la conformidad del cliente.» |
| `firma_no_humana` · ilegible | «No se ha podido leer la casilla de la firma. Tiene que mirarlo una persona.» |
| `observaciones_manuscritas` | «El parte trae observaciones escritas a mano. Firmado no es lo mismo que conforme: alguien tiene que leerlas y decidir si la reparación se da por buena.» |

## 5 · `config/prompts.yaml` · la clave nueva `firma_parte_es`

**Se añade una clave; no se toca ninguna letra de `parte_posventa_es`.** Eso
mantiene intacta su huella y, con ella, la validez del barrido de 22 partes
que el humano hizo el 2026-08-19 (R4 lo clava con un test).

```yaml
firma_parte_es:
  version: "1"
  schema: firma_cliente
  system: |
    …miras UNA casilla de un parte de posventa escaneado y dices qué hay en
    ella. No extraes datos, no lees texto, no juzgas si el parte es válido…
  task: |
    …devuelve `clasificacion_firma` con UNA de estas cuatro etiquetas…
```

Contenido normativo del prompt, escrito contra
`docs/referencia/02_parte_de_trabajo.md` y **sin un solo dato personal**:

- El bloque es «SERVICIO REALIZADO Y CONFORME». **La casilla que importa es la
  del cliente (columna izquierda, «Fdo.» / «DNI»)**; la del técnico viene
  vacía en toda la remesa y **no se mira**.
- Las cuatro etiquetas, con su criterio:
  - `humana` — un trazo continuo con estructura de firma o rúbrica, aunque sea
    ilegible como nombre. Una firma no tiene por qué poder leerse.
  - `marca_simple` — un aspa, una cruz, un tick, una raya, un círculo o
    cualquier trazo geométrico suelto. **No** es una firma.
  - `casilla_vacia` — no hay ningún trazo.
  - `ilegible` — hay algo, pero el escaneo no permite decir qué es.
- **No inventes**: ante la duda, `ilegible`. Etiquetar de `humana` lo que no lo
  es da por conforme una reparación que el cliente no firmó.
- **No transcribas el nombre**, ni el DNI, ni ningún texto de alrededor: solo
  la etiqueta y su confianza.
- Una `confianza_pct` entera de 0 a 100: tu certeza sobre **la etiqueta**.
- Salida: JSON del schema `firma_cliente` y nada más.

**Que el prompt no pida el nombre no es cortesía: es la regla de datos
personales.** La casilla de la firma es lo más identificativo del papel.

## 6 · Los dobles de prueba

`tests/utiles_validacion.py`, **entregable** como `utiles_ia.py` y
`utiles_pdf.py`:

```python
def extraccion_de_ejemplo(**cambios) -> ExtraccionParte   # los nueve campos
def lectura_de_firma(clasificacion="humana", confianza=93) -> LecturaFirma
def respuesta_de_firma(etiqueta="humana", confianza=93) -> RespuestaModelo
```

Reutiliza `CAMPOS_DE_EJEMPLO` de `utiles_ia.py` (ya inventados: DNI
`00000000T`, promoción y unidad de mentira). **Ni un dato real, ni un JSON
capturado de una llamada de verdad, ni una lectura de `muestras/`**: el parte
lleva DNI de clientes y el historial de git no suelta lo que entra.

La guardia de red autouse de `tests/conftest.py` (F-003) sigue vigente y cubre
también esta suite: R26 no es una promesa, es imposible saltársela.

## 7 · Riesgos y decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Prompt propio para la firma sobre el mismo puerto | Décimo campo en el prompt de extracción | No se toca el prompt cuya calidad se midió sobre 22 partes reales y que ningún test protege (§2) |
| Dos endpoints, lanzables en paralelo | Componer las dos llamadas en una invocación | Dos timeouts de 120 s suman 240 s y la Function corta a 230 s |
| `/api/validar` **puro**, sin IA ni PDF | Validar dentro de `/api/firma` | Se puede revalidar cuando una persona corrija un campo (F-011) o cuando F-016 reclasifique, sin volver a gastar una llamada |
| Dos destinos (`cola` y `revision_manual`) | Un único «no apto» | Son dos trabajos distintos: decidir sobre la reparación o arreglar el parte. Y es lo que hace consistente el `acceptance` (§1) |
| Umbral de confianza como constante del dominio | Variable de entorno | Aflojar una regla de negocio no puede ser un cambio de configuración |
| Registro `CAMPOS_POR_SCHEMA` en el dominio | Declarar los campos en el YAML | La lista de campos es contrato del dominio y fuente única (regla de F-003), no configuración |
| Ante etiqueta desconocida, `ILEGIBLE` | `HUMANA` por defecto, o error | El fallo cae del lado seguro: nunca se da por firmado lo que no se entendió |
| Sanear la confianza en **una** función compartida | Copiarla en `paso_firma` | Dos copias de una regla numérica divergen; y la campaña de mutación las contaría dos veces |

### Decisiones D1–D5 · RESUELTAS por el humano el 2026-08-19

> Las cinco quedaron resueltas antes de arrancar el `implementer`. Se
> conservan aquí con su razonamiento porque explican **por qué** la spec dice
> lo que dice; ninguna sigue abierta ni bloquea. La única que cambió el
> contenido de la spec es **D4**.

**D1 · ¿Qué hace el sistema con un parte cuya firma no es humana?** Es **la**
decisión de esta spec.

> **RESUELTA el 2026-08-19: APLAZADA a propósito. La spec se implementa tal y
> como está** —opción 1, `no_apto` + `revision_manual`—, que es la coherente
> con `docs/ARCHITECTURE.md` y `CHECKPOINTS.md`.
>
> Se aplaza porque **depende de un dato que todavía no existe**: el reparto de
> las cuatro etiquetas de firma sobre los 22 partes reales de Mirasierra. Por
> eso **T14 se adelanta**: se ejecuta **en cuanto el endpoint de firma
> funcione**, no al final, y con su resultado delante el humano confirma la
> opción 1 o cambia a la 2. Lo que cuesta cambiar entonces es **una función
> pura y sus tests**, no el diseño: ni el contrato HTTP, ni el dominio, ni los
> pasos se mueven.

- **Lo que implementa la spec (opción 1)**: `no_apto` + `revision_manual`,
  nunca apto. Es lo que dicen `docs/ARCHITECTURE.md` (semántica 3) y
  `CHECKPOINTS.md` C3 —«una marca simple nunca cuenta como firma del
  cliente»—, y no contradice el `acceptance`, que acota el «único motivo» a
  **la cola** (§1).
- **Opción 2**: la clasificación se emite pero **solo como aviso**; el parte
  sale apto igualmente y las observaciones son literalmente lo único que
  bloquea. Respeta la lectura más estricta de la decisión (2), pero **choca de
  frente con dos documentos normativos** y permitiría archivar y cerrar un
  parte con la casilla de la firma vacía.
- **Lo que debería decidirlo es un dato, y se mide en T14**: la distribución de
  las cuatro etiquetas sobre los 22 partes reales de Mirasierra. Si sale
  mayoritariamente `humana`, la opción 1 no molesta a nadie. Si un tercio sale
  `ilegible`, la opción 1 manda a revisión manual media remesa, que es
  exactamente el error contra el que avisa `docs/ARCHITECTURE.md` 4 bis, y
  entonces conviene la opción 2 —o subir la calidad del prompt de firma antes
  de aplicar la regla—.
- **Coste de cambiar de opción después**: una rama de `validar_parte` y sus
  tests. Ni el contrato HTTP, ni el dominio, ni los pasos cambian.

**D2 · ¿Entran los dos endpoints en F-004?** El `acceptance` no los pide.

> **RESUELTA el 2026-08-19: SÍ, los dos endpoints ENTRAN en F-004.** El humano
> acepta la razón de fondo: sin `/api/validar`, las reglas de validación
> acabarían reescritas en JavaScript en el front, que es una fuga de dominio.
> **R23 y R24 se quedan**, con sus tareas T11 y T12.

Se incluyen por la misma razón que en F-003 (decisión D2 de aquella spec): sin
endpoint no hay quien ejercite la validación, y **sin `/api/validar` las reglas
acabarían reescritas en JavaScript en el front**, que es una fuga de dominio de
libro. Si el humano prefiere dejarlos para F-007, se caen R23 y R24 con sus
tareas y el resto de la spec no se mueve.

**D3 · ¿Se clava la huella del prompt de extracción con un test?** La spec dice
que sí (R4): es lo único que garantiza que F-004 no ha rozado el prompt medido.
Efecto lateral, buscado: el día que alguien cambie ese prompt legítimamente
—F-015— tendrá que actualizar la constante **a conciencia** y volver a medir.
Si el humano lo considera un freno, se sustituye por un test más flojo (que la
clave siga existiendo) y se pierde esa red.

> **RESUELTA el 2026-08-19: SÍ, se mantiene el test que clava la huella
> (R4).** Es la red que garantiza que F-004 no roza el prompt cuya calidad se
> midió sobre 22 partes reales. **El efecto lateral es buscado**: quien lo
> cambie en F-015 actualizará la constante a conciencia y volverá a medir.

**D4 · Cuando R14 degrada una firma `humana` dudosa, ¿qué etiqueta se
publica?** El hueco se detectó al escribir `tasks.md`: R14 dice que una
`humana` por debajo del umbral **se trata como `ilegible`**, pero ni
`requirements.md` ni `design.md` decían qué salía en
`ResultadoValidacion.clasificacion_firma` y en el JSON de respuesta: la
etiqueta que devolvió el modelo (`humana`) o la degradada (`ilegible`).

> **RESUELTA el 2026-08-19: se publica la etiqueta DEGRADADA, `ilegible`.**
> Motivo del humano: es la única coherente con el motivo que se emite;
> publicar `humana` junto a un destino «revisión manual» es incomprensible
> para quien lo lea en Posventa.
>
> **Es la única de las cinco que cambió el contenido de la spec.** Está
> aplicado en **R14 bis** de `requirements.md` y en §4.1, §4.2 y §4.5 de este
> documento (`clasificacion_efectiva`). **No se añade ningún campo al
> contrato** para conservar la lectura cruda: no hace falta, porque la
> respuesta de `/api/firma` ya la publica y es la entrada de `/api/validar`.

**D5 · ¿Qué módulo escribe el log del camino de validación?** R25 exige que el
log no lleve la transcripción de las observaciones ni el DNI, pero ni
`requirements.md` ni `design.md` nombraban al módulo que lo escribe.

> **RESUELTA el 2026-08-19: se queda como está.** T13, con `caplog` sobre la
> validación, es exactamente lo que pide el requisito. **No se añade** una
> línea de log explícita en `paso_validacion`.

### Riesgos

**Riesgo 1 · la clasificación de la firma no la mide ningún test unitario.**
Igual que el prompt de extracción en F-003: la suite demuestra el contrato, no
el acierto. Por eso T14 es `MANUAL (humano)` y se ejecuta **en cuanto el
endpoint funciona**, no al final: si el modelo no distingue una firma de un
aspa, no falla el diseño de F-004, falla D1, y enterarse pronto ahorra la
documentación y la campaña de mutación entera.

**Riesgo 2 · doble coste y doble latencia por parte.** Dos llamadas
multimodales donde antes había una. Se absorbe con el paralelismo del front
(F-007) y con un prompt de firma corto. Si el coste resultara alto, la salida
natural **no** es volver a la vía A, sino recortar lo que se le manda a la
lectura de firma (una sola página, la primera).

**Riesgo 3 · falsos `humana`.** Es el fallo caro: da por conforme lo que el
cliente no firmó. Mitigación en tres capas: el prompt manda `ilegible` ante la
duda; el dominio traduce cualquier etiqueta desconocida a `ILEGIBLE` (R2); y
una `humana` con confianza baja se degrada a `ILEGIBLE` (R14).

**Riesgo 4 · datos personales.** La transcripción de las observaciones y el
DNI **no entran en el log** (R25). Van en el cuerpo de la respuesta porque
quien decide los necesita delante, y ahí acaba su viaje hasta que F-005 los
guarde en el schema propio.

**Riesgo 5 · tocar `gemini.py` reabre código de F-003.** El cambio es acotado
—de dónde sale el schema— y queda cubierto por los tests que ya existen más el
de R5. La prueba de que no se ha roto nada es que **los tests de F-003 pasan
sin modificar ninguna aserción**.

## 8 · SQL

**No aplica.** F-004 no lee ni escribe en ninguna base de datos: la cola de
validación humana la **declara**, no la guarda. La persistencia es F-005, con
su schema propio. Ni una sentencia, ni un fichero `NN_nombre.sql`, ni una
conexión.

## 9 · Límite de microservicio

F-004 cae **entera** dentro de `services/postventa-api/`: mismo dominio (el
parte de posventa), mismos puertos, mismo adaptador, ninguna dependencia nueva.

No aparece ninguna responsabilidad ajena a este servicio: no toca el catálogo
del portal, no llama a `sigrid-api` —la coherencia con Sigrid es F-008/F-009,
y por eso está fuera (§0)—, no escribe en SharePoint y no ejecuta SQL. El front
consumirá los dos endpoints en F-007, y **este repositorio todavía no tiene
documento en `azure-apps/`** (se crea al desplegar, F-010), así que no hay
documento del ecosistema que actualizar; consta escrito para que el reviewer no
lo lea como un olvido.
