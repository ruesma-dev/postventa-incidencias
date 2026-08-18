<!-- specs/F-002-ingesta-troceado/design.md -->
# F-002 · Ingesta y troceado — Diseño técnico

> Encaja en `docs/ARCHITECTURE.md` (pasos 1 y 2 del pipeline) y en
> `docs/CONVENTIONS.md`. Servicio: **`services/postventa-api/`** y solo ese.

## 0 · El hallazgo que manda sobre este diseño

**La remesa real de Mirasierra no tiene capa de texto.** Comprobado al
diseñar, sobre `docs/referencia/doc02871320260817093833.pdf` (no versionado):

```
paginas: 22
pagina 1..3: chars=0, imgs=1
TOTAL chars capa texto: 0
```

Cada página es una imagen escaneada. Consecuencias directas:

1. La regla del pie —«`Página 2` delata el parte de dos hojas»— **solo puede
   dispararse en PDFs que sí traigan texto** (los que genera Sigrid
   directamente, o un escaneo con OCR). En la remesa de Mirasierra no se
   dispara ninguna vez.
2. Eso **no rompe** el criterio `acceptance` 2: Mirasierra son 22 páginas de
   partes de una hoja (el pie de todas dice «Página 1», según
   `docs/referencia/02_parte_de_trabajo.md`), y la regla por defecto —una
   página, un parte— acierta las 22.
3. Pero sí obliga a que el resultado **diga en qué modo se troceó**, para que
   nadie confunda «no hay parte de dos hojas» con «no se ha podido mirar».
   De ahí R11 y el campo `modo_deteccion`.

**Decisión de diseño consecuente**: la degradación **no es un camino de código
alternativo**, es el resultado natural de la única regla (sin texto no hay pie
reconocido → toda página abre parte → una página, un parte). `modo_deteccion`
es una **etiqueta informativa** calculada por documento, no un `if` que
bifurque el algoritmo. Un solo camino = menos superficie de mutantes y nada
que se pudra sin ejercitarse.

**Decisión del humano (2026-08-18): degradación ACEPTADA para F-002.** Hasta
que las remesas lleguen con OCR, el parte de dos hojas no se detectará en
producción, y eso es admisible porque `modo_deteccion` lo declara. Alternativas
evaluadas en §7.

La recuperación queda planificada, no olvidada: **`F-014` · «Reagrupar el parte
de dos hojas con el "Página 2" que lee la extracción»** (prioridad 14,
`blocked_by` F-003). Cuando la extracción multimodal de F-003 lea el pie
impreso —que un modelo sí ve aunque no haya capa de texto—, una página cuyo pie
diga `Página N` con N ≥ 2 se reagrupará como continuación del parte anterior.

**Qué significa esto para el implementer de F-002**: nada que implementar aquí,
pero **no cierres la puerta**. La salida de cada parte debe conservar
`paginas_origen` y `origen` con la precisión suficiente para que después se
puedan unir dos partes contiguos sin volver a abrir el PDF de la remesa. No
añadas ganchos, banderas ni código muerto «preparando» F-014: eso se diseña en
su spec.

## 1 · Ficheros a crear

### Dominio (puro: ni pymupdf, ni zipfile, ni azure)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/domain/models/pie_de_pagina.py` | `PieDePagina` — la regla del comienzo de parte |
| `services/postventa-api/domain/models/remesa.py` | `DocumentoEntrada`, `ParteTroceado`, `ModoDeteccion` |
| `services/postventa-api/domain/models/errores.py` | `LimiteDeEntradaSuperado`, `RemesaSinPdfUtilizable` |
| `services/postventa-api/domain/ports/pdf.py` | `PdfPort` (Protocol) |
| `services/postventa-api/domain/ports/comprimido.py` | `ComprimidoPort` (Protocol) |

### Aplicación (orquesta; habla con puertos, nunca con adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/application/pipelines/contexto.py` | `ContextoRemesa` |
| `services/postventa-api/application/pipelines/paso_ingesta.py` | `paso_ingesta(...)` |
| `services/postventa-api/application/pipelines/paso_troceado.py` | `paso_troceado(...)` |

### Infraestructura (adaptadores)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/infrastructure/documentos/__init__.py` | paquete |
| `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py` | `AdaptadorPdfPyMuPdf` (implementa `PdfPort`) |
| `services/postventa-api/infrastructure/documentos/zip_estandar.py` | `AdaptadorZipEstandar` (implementa `ComprimidoPort`) |

> `infrastructure/documentos/` es una carpeta nueva. `docs/ARCHITECTURE.md`
> lista hoy `llm/`, `sharepoint/`, `sigrid/` y `persistencia/`; la lista es
> ilustrativa, pero el árbol es normativo, así que **T13 lo actualiza**. Una
> sola carpeta nueva para los dos adaptadores: ambos convierten *ficheros de
> entrada* en material del dominio.

### Interfaz HTTP

| Ruta | Contenido |
|---|---|
| `services/postventa-api/interface_adapters/api/split.py` | handler `trocear_remesa(...)`, sin nada de Azure dentro, y la **composición del pipeline** |

### Tests (el generador sintético es entregable)

| Ruta | Contenido |
|---|---|
| `services/postventa-api/tests/utiles_pdf.py` | generador de PDFs sintéticos (§5) |
| `services/postventa-api/tests/test_f002_utiles_pdf.py` | tests del propio generador |
| `services/postventa-api/tests/test_f002_pie_de_pagina.py` | R7–R10 (dominio puro) |
| `services/postventa-api/tests/test_f002_ingesta.py` | R1–R6 |
| `services/postventa-api/tests/test_f002_troceado.py` | R7–R15 |
| `services/postventa-api/tests/test_f002_split_http.py` | R16–R18 |
| `services/postventa-api/tests/test_f002_arquitectura.py` | R19 |

## 2 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | Añade la ruta `@app.route(route="split", methods=["POST"])`. Solo traduce `func.HttpRequest` ↔ handler: lee `req.files` (multipart) y serializa el `dict` del handler a JSON con `ensure_ascii=False`. Mapea `RemesaSinPdfUtilizable`→400, `LimiteDeEntradaSuperado`→413. |
| `services/postventa-api/requirements.txt` | **Añade `pymupdf>=1.24,<2.0`** (ver §6). |
| `docs/ARCHITECTURE.md` | Añade `infrastructure/documentos/` al árbol y una línea al paso 2 del pipeline: el modo de detección degrada a «una página, un parte» cuando el PDF no trae capa de texto. |

## 3 · Ficheros que NO se tocan (los que tientan)

- `services/postventa-api/interface_adapters/api/health.py`, `config/settings.py`,
  `config/logging_config.py`, `tests/test_health.py`,
  `tests/test_f001_adaptador_http.py` — F-001 está cerrada. Los límites de la
  ingesta van como **constantes del adaptador** (§4), no como variables nuevas
  de `Ajustes`: nadie las va a tunear en dev y cada campo nuevo de settings es
  superficie de configuración que hay que desplegar.
- **Nada de extracción**: no se crea `infrastructure/llm/`, ni
  `ExtractorPort`, ni `config/prompts.yaml`, ni campo alguno de negocio en el
  resultado. Es F-003, y R18 lo vigila con un test.
- **Nada de persistencia**: no se crea `infrastructure/persistencia/` ni SQL.
  El hash que produce F-002 es la clave que **F-005** usará para deduplicar;
  aquí solo se calcula y se devuelve. **F-002 no lleva SQL de ningún tipo.**
- **Nada de validación ni de firma** (F-004), **nada de nombrado ni SharePoint**
  (F-006), **nada de Sigrid** (F-008/F-009).
- `services/postventa-front/` — el front consume `/split` en F-007. No se
  toca, ni se declara en `harness/servicios.json`.
- `muestras/`, `docs/referencia/*.pdf`, `.gitignore` — los originales no se
  versionan y ningún test los mira.
- `azure-apps/` — este servicio todavía no tiene documento allí (se crea al
  desplegar, F-010). No aplica en F-002; consta aquí para que el reviewer no
  lo marque como olvido.

## 4 · Clases y funciones

### Dominio

```python
# domain/models/pie_de_pagina.py
MARCADOR_PLANTILLA = "RCP_Parte_de_Trabajos"
PATRON_PAGINA = re.compile(r"P[áa]gina\s*(\d+)", re.IGNORECASE)

@dataclass(frozen=True)
class PieDePagina:
    plantilla_reconocida: bool
    numero: int | None

    @classmethod
    def desde_texto(cls, texto: str) -> "PieDePagina": ...

    @property
    def es_continuacion(self) -> bool:
        return self.plantilla_reconocida and self.numero is not None and self.numero >= 2
```

- `plantilla_reconocida` = el texto contiene `MARCADOR_PLANTILLA` (el
  `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo` que Sigrid imprime en cada
  pie, según `docs/referencia/02_parte_de_trabajo.md`).
- `numero` = **última** coincidencia de `PATRON_PAGINA` en el texto de la
  página. Se toma la última porque el pie es lo último que devuelve la
  extracción en orden de lectura; y se exige **además** la plantilla para que
  un «página» suelto en la descripción de una reclamación no pueda fundir dos
  partes (R9, regla conservadora).
- Capa: **dominio**. Es la regla de negocio de la plantilla impresa; se prueba
  con `str`, sin PDF ninguno.

```python
# domain/models/remesa.py
class ModoDeteccion(str, Enum):
    POR_PIE_DE_PAGINA = "por_pie_de_pagina"
    UNA_PAGINA_POR_PARTE = "una_pagina_por_parte"

@dataclass(frozen=True)
class DocumentoEntrada:
    nombre: str
    contenido: bytes

@dataclass(frozen=True)
class ParteTroceado:
    hash: str
    origen: str
    paginas_origen: tuple[int, ...]      # numeradas desde 1
    modo_deteccion: ModoDeteccion
    contenido: bytes                      # el PDF del parte
    avisos: tuple[str, ...] = ()
```

`bytes` en un modelo de dominio es dato, no infraestructura: el dominio no
sabe **cómo** se produjeron.

### Puertos

```python
# domain/ports/pdf.py
class PdfPort(Protocol):
    def texto_por_pagina(self, contenido: bytes) -> list[str]: ...
    def huella_de_paginas(self, contenido: bytes, paginas: Sequence[int]) -> str: ...
    def extraer_paginas(self, contenido: bytes, paginas: Sequence[int]) -> bytes: ...
    def paginas_sin_contenido(self, contenido: bytes, paginas: Sequence[int]) -> bool: ...

# domain/ports/comprimido.py
class ComprimidoPort(Protocol):
    def es_comprimido(self, documento: DocumentoEntrada) -> bool: ...
    def extraer_pdfs(self, documento: DocumentoEntrada) -> tuple[list[DocumentoEntrada], list[str]]: ...
```

`extraer_pdfs` devuelve `(pdfs, avisos)`. Capa: **dominio** (solo interfaces).

### Aplicación

```python
# application/pipelines/contexto.py
@dataclass
class ContextoRemesa:
    entradas: list[DocumentoEntrada]
    pdfs: list[DocumentoEntrada] = field(default_factory=list)
    partes: list[ParteTroceado] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

# application/pipelines/paso_ingesta.py
def paso_ingesta(ctx: ContextoRemesa, comprimido: ComprimidoPort) -> ContextoRemesa
# application/pipelines/paso_troceado.py
def paso_troceado(ctx: ContextoRemesa, pdf: PdfPort) -> ContextoRemesa
```

- `paso_ingesta`: clasifica cada entrada (PDF / comprimido / otra cosa),
  expande los comprimidos, acumula avisos. **No abre PDFs**.
- `paso_troceado`: por cada PDF, `texto_por_pagina` → `PieDePagina` por
  página → agrupa páginas en partes → por cada grupo `huella_de_paginas` y
  `extraer_paginas`. Si un PDF no se puede abrir, el adaptador levanta
  `PdfIlegible` y el paso lo convierte en aviso y sigue (R4).
- La **composición** (`paso_ingesta` → `paso_troceado`) vive en el punto de
  entrada, `interface_adapters/api/split.py`, como manda `docs/CONVENTIONS.md`.

### Infraestructura

```python
# infrastructure/documentos/pdf_pymupdf.py
UMBRAL_TEXTO_UTIL = 20      # caracteres no en blanco por página

class AdaptadorPdfPyMuPdf:  # implementa PdfPort
```

**Cómo se calcula la huella (R12)** — para cada página del parte, en orden:

```
h.update(b"P")                       # separador de página
h.update(longitud + texto_normalizado_utf8)
para cada imagen incrustada, en orden de xref:
    h.update(longitud + bytes_crudos_de_la_imagen)
```

- `texto_normalizado` = texto de la página con los blancos colapsados
  (`" ".join(texto.split())`).
- Las imágenes se leen con su xref y se toman **tal cual están guardadas** en
  el PDF, sin recomprimir.
- Cada trozo va precedido de su longitud para que dos concatenaciones
  distintas no puedan dar la misma cadena.

**Por qué así y no el hash de los bytes del PDF resultante**: los bytes que
escribe PyMuPDF dependen de su versión, del nivel de compresión y del `/ID`
que genera al guardar. Dos máquinas —o dos versiones— darían hashes distintos
para el mismo parte, y eso rompería la promesa de F-005 («reprocesar
actualiza, no duplica»). El texto y las imágenes se recuperan de los objetos
del PDF y **sobreviven a una reserialización**, que es justo lo que hace falta
para R14: el parte extraído de la remesa multi-parte y el mismo parte llegado
suelto dentro de un ZIP dan la misma huella.

Ese es también el motivo de que la huella se calcule **sobre las páginas de
origen** y no sobre el PDF ya troceado.

```python
# infrastructure/documentos/zip_estandar.py
MAX_ENTRADAS_ZIP = 500
MAX_BYTES_DESCOMPRIMIDOS = 200 * 1024 * 1024
```

- Antes de leer nada, suma `file_size` del índice del ZIP y cuenta entradas:
  si se pasa de los límites, `LimiteDeEntradaSuperado` (R6). Así una bomba de
  descompresión **nunca llega a expandirse**.
- Recorre las entradas en `sorted()` de la ruta interna (comparación exacta,
  determinista y sin depender del locale).
- Descarta con aviso: directorios, entradas con `..` en la ruta, ZIP anidados
  y todo lo que no acabe en `.pdf` (comparación en minúsculas).
- Solo `zipfile` de la biblioteca estándar; nada se escribe en disco.

### Interfaz

```python
# interface_adapters/api/split.py
def trocear_remesa(entradas: list[DocumentoEntrada]) -> dict[str, Any]
```

Compone el pipeline con `AdaptadorPdfPyMuPdf()` y `AdaptadorZipEstandar()`,
lo ejecuta y serializa. Levanta `RemesaSinPdfUtilizable` (→400) si tras la
ingesta no queda ningún PDF. Contrato de respuesta (R16):

```json
{
  "total_partes": 22,
  "partes": [
    {
      "hash": "9f2b…",
      "origen": "remesa.pdf",
      "paginas_origen": [1],
      "modo_deteccion": "una_pagina_por_parte",
      "avisos": [],
      "contenido_b64": "JVBERi0…"
    }
  ],
  "avisos": ["notas.txt: descartado, no es un PDF ni un ZIP"]
}
```

Ni un campo de negocio: R18 lo fija con un test sobre el conjunto de claves.

## 5 · El generador de PDFs sintéticos (entregable)

`tests/utiles_pdf.py`, construido con **PyMuPDF**, que ya es dependencia del
servicio. (`docs/CONVENTIONS.md` manda ReportLab para «PDF en servidor»: eso
es para el PDF que el servicio produzca como producto, no para material de
test; añadir ReportLab solo para fabricar fixtures sería una dependencia de
más. Decisión consciente, anotada aquí para que el reviewer no la lea como
incumplimiento.)

```python
def pagina_de_parte(numero_pagina: int = 1, incidencia: str = "RS26.08/0123",
                    obra: str = "0677", observaciones: str = "") -> str
def remesa_sintetica(numeros_de_pagina: Sequence[int]) -> bytes
def remesa_escaneada(n_paginas: int = 1) -> bytes
def zip_con(ficheros: Mapping[str, bytes]) -> bytes
```

- `pagina_de_parte` devuelve el **texto** de una página que imita la plantilla
  impresa descrita en `docs/referencia/02_parte_de_trabajo.md`: las etiquetas
  del bloque «PROFESIONAL Y SERVICIOS ASIGNADOS» (Promoción, Código Obra, Nº
  Incidencia, Oficio, Empresa, Vivienda, Descripción), las del bloque
  «SERVICIO REALIZADO Y CONFORME», y **el pie**:
  `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo    Página N`.
  Nada de datos personales: ni nombres, ni DNI reales.
- `remesa_sintetica([1, 1, 2, 1])` = un PDF de 4 páginas con **3 partes**, el
  segundo de dos hojas. Es la pieza que ejercita R8 y R10.
- `remesa_escaneada(n)` = PDF de `n` páginas **sin capa de texto**: cada
  página lleva una imagen PNG distinta, generada con un `Pixmap` de PyMuPDF
  (píxeles derivados del índice de página, para que dos páginas no colisionen
  de hash). Imita la remesa real de Mirasierra y ejercita R11.
- `zip_con({...})` = ZIP en memoria, para R2, R6 y R14.

## 6 · Dependencias

`pymupdf` está hoy en el `requirements-dev.txt` **de la raíz**, que es el del
arnés y la suite de la raíz. F-002 lo usa en **código de producción del
servicio**, así que su sitio es
**`services/postventa-api/requirements.txt`** —lo que se despliega a la
Function App— con la misma horquilla que la raíz: `pymupdf>=1.24,<2.0`.
`requirements-dev.txt` del servicio ya hace `-r requirements.txt`, así que la
suite del servicio lo hereda sin tocar nada más. El `requirements-dev.txt` de
la raíz se deja como está: el generador sintético vive en la suite del
servicio, pero el humano puede querer trastear con PyMuPDF desde la raíz.

Ninguna dependencia más. Sin OCR, sin Pillow, sin ReportLab.

## 7 · Riesgos y decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Huella sobre texto + imágenes de las páginas de origen | SHA-256 de los bytes del PDF troceado | Los bytes dependen de la versión de PyMuPDF, del `/ID` y de la compresión: dos ejecuciones podrían dar hashes distintos del mismo parte y F-005 duplicaría |
| Regla conservadora: ante la duda, **abrir** parte | Ante la duda, continuar el parte anterior | Trocear de más manda un parte a revisión manual; fundir dos partes **pierde una incidencia**, que es el error caro |
| Exigir marcador de plantilla **y** `N ≥ 2` | Solo `Página N` | Un «página» en la descripción de una reclamación podría fundir dos partes |
| Degradación sin bifurcación de código | `if hay_texto: … else: …` | Un camino sin ejercitar se pudre y regala mutantes supervivientes (rigor `critico`) |
| Límites del ZIP como constantes del adaptador | Variables nuevas en `Ajustes` | Nadie las va a tunear en dev; cada variable nueva hay que desplegarla y documentarla |
| Devolver el PDF de cada parte en `contenido_b64` | Guardarlos en servidor y devolver ids | No hay persistencia hasta F-005, y `docs/ARCHITECTURE.md` ya define el contrato: `/split` devuelve N partes y el front llama luego uno a uno |

**Riesgo abierto 1 · el parte de dos hojas no se detecta en producción.** La
remesa real no trae texto. Alternativas, para que decida el humano:
(a) aceptar la degradación en v1 —Mirasierra sale 22/22— y dejarlo declarado
en `modo_deteccion`; (b) meter OCR del pie (dependencia nueva, binario de
tesseract, tests offline complicados); (c) aprovechar que **F-003 ya pasa
cada página por un modelo multimodal** y hacer que devuelva el «Página N» del
pie, reagrupando después. **Recomendación: (a) ahora, (c) cuando exista
F-003.** Ni (b) ni (c) se implementan en F-002.

**Riesgo abierto 2 · tamaño de la respuesta.** 22 partes escaneados en base64
inflan un 33 % la remesa. Aceptable para el piloto; cuando F-005 traiga
persistencia, `/split` podrá devolver identificadores en vez de bytes.

**Riesgo 3 · colisión de huella en páginas en blanco.** Una página sin texto
ni imágenes hashea igual que cualquier otra igual de vacía. R15 obliga al
aviso; además F-004 nunca daría por apto un parte en blanco.

**Riesgo 4 · que `extraer_paginas` no conserve el contenido de la página.** Si
en la fase RED se ve que R14 no se cumple porque PyMuPDF reescribe lo que
copia, **el implementer para y lo reporta** (regla del arnés: nada de
workarounds). La alternativa ya evaluada —y la única aceptada sin volver a
pasar por el humano— es calcular la huella siempre desde el documento de
origen, nunca desde el PDF extraído; que es como está escrito arriba.

## 8 · Límite de microservicio

F-002 cae **entera** dentro de `services/postventa-api/`. No toca el front
(F-007), no toca `sigrid-api`, no toca SharePoint, no toca el PostgreSQL
compartido y no ejecuta SQL. No hay nada en esta feature que pertenezca a
otro servicio ni que haya que extraer a uno nuevo.
