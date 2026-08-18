<!-- progress/impl_F-002.md -->
# F-002 · Ingesta y troceado — Informe de implementación

**Rama**: `feature/F-002-ingesta-troceado` · **Rigor**: `critico` ·
**Estado**: implementada, `bash harness/init.sh` en verde (exit 0).
**Pendiente**: la verificación **MANUAL (humano)** de T15 (ver más abajo) y el
veredicto del reviewer.

Las 16 tareas de `specs/F-002-ingesta-troceado/tasks.md` están marcadas, con un
commit por tarea (T15 no: es del humano).

---

## 1 · Qué cambió

### Código nuevo del servicio `services/postventa-api/`

| Fichero | Qué hace |
|---|---|
| `domain/models/pie_de_pagina.py` | La regla del comienzo de parte: marcador de plantilla **y** `Página N` con N ≥ 2. Dominio puro, se prueba con `str` |
| `domain/models/remesa.py` | `DocumentoEntrada`, `ParteTroceado`, `ModoDeteccion` y `es_nombre_de_pdf` |
| `domain/models/errores.py` | `ErrorDeIngesta` y sus tres hijos: `RemesaSinPdfUtilizable`, `PdfIlegible`, `LimiteDeEntradaSuperado` |
| `domain/ports/pdf.py` | `PdfPort`: texto por página, huella, extracción y páginas sin contenido |
| `domain/ports/comprimido.py` | `ComprimidoPort`: `es_comprimido` y `extraer_pdfs` → `(pdfs, avisos)` |
| `application/pipelines/contexto.py` | `ContextoRemesa`, el objeto que atraviesa los pasos |
| `application/pipelines/paso_ingesta.py` | Paso 1: normaliza la entrada a lista de PDFs **sin abrir ninguno** |
| `application/pipelines/paso_troceado.py` | Paso 2: agrupa páginas en partes, calcula huella, extrae el PDF y declara el modo |
| `infrastructure/documentos/pdf_pymupdf.py` | Adaptador PyMuPDF: umbral de texto útil, huella estable, extracción de páginas |
| `infrastructure/documentos/zip_estandar.py` | Adaptador ZIP: límites sobre el índice, orden alfabético, descartes con aviso |
| `interface_adapters/api/split.py` | Handler: **compone** el pipeline y serializa. Sin nada de Azure dentro |

### Código modificado

| Fichero | Qué cambia |
|---|---|
| `function_app.py` | Ruta `POST /api/split`: lee `req.files`, llama al handler y mapea `RemesaSinPdfUtilizable`→400 y `LimiteDeEntradaSuperado`→413. Se extrajo `_json(...)`, que `health` también usa |
| `requirements.txt` | `pymupdf>=1.24,<2.0` (instalado: 1.28.2) |
| `docs/ARCHITECTURE.md` | `infrastructure/documentos/` en el árbol y, en el paso 2 del pipeline, la degradación a «una página, un parte» cuando el PDF no trae capa de texto |

### Tests (8 ficheros nuevos, 87 tests de F-002)

`tests/utiles_pdf.py` (generador sintético), `test_f002_utiles_pdf.py`,
`test_f002_pie_de_pagina.py`, `test_f002_adaptador_pdf.py`,
`test_f002_ingesta.py`, `test_f002_troceado.py`, `test_f002_split_http.py`,
`test_f002_arquitectura.py`.

**Ningún test toca red, BBDD, IA, disco ni `muestras/`.** Todos los PDF se
fabrican en memoria con PyMuPDF, imitando la plantilla de
`docs/referencia/02_parte_de_trabajo.md`, sin un solo dato personal.

---

## 2 · Decisiones de diseño (y las desviaciones, con su motivo)

1. **`PdfIlegible` vive en `domain/models/errores.py`**, no junto al adaptador
   que lo levanta. `design.md` §1 solo listaba dos errores en ese fichero.
   Motivo: quien lo captura es `paso_troceado` (R4), y la aplicación no puede
   importar infraestructura. Lo levanta el adaptador, lo caza el pipeline y el
   dominio es el único sitio que los dos pueden mirar.
2. **Un fichero de test más de los que lista `design.md` §1**:
   `tests/test_f002_adaptador_pdf.py`. La spec exige los tests de R12/R15 en
   T5 pero no les asigna fichero; mezclarlos con los del pipeline confundiría
   dos niveles. Los nombres canónicos de la tabla de trazabilidad siguen en el
   fichero que les toca.
3. **`UMBRAL_TEXTO_UTIL` se aplica dentro del adaptador**: `texto_por_pagina`
   devuelve `""` para una página que no llega al umbral. Así la degradación de
   R11 **no es una bifurcación**: sin texto no hay pie reconocido, y la única
   regla produce «una página, un parte». `modo_deteccion` es una etiqueta
   calculada por documento, no un `if` que cambie el algoritmo.
   La **huella sí usa el texto completo** de la página, sin umbral: R12 habla
   del contenido, no de lo que sea legible.
4. **Los límites del ZIP son constantes de módulo** (`design.md` §7), no
   configuración. Los tests de comportamiento los bajan con `monkeypatch` para
   probar el borde exacto, y un test aparte fija sus valores reales
   (500 entradas, 209.715.200 bytes) para que nadie los mueva sin querer.
5. **El nombre de un PDF sacado de un ZIP conserva su procedencia**:
   `remesa.zip/carpeta/parte.pdf`. Es lo que hace trazable el `origen` de cada
   parte sin volver a abrir nada.
6. **`es_nombre_de_pdf` en el dominio**: lo usan el paso de ingesta y el
   adaptador de ZIP, y saber qué es un PDF de entrada es vocabulario del
   dominio, no un detalle de `zipfile`.
7. **Nada de F-014.** No hay ganchos, banderas ni parámetros «para el futuro».
   Lo único que se conserva es lo que pidió el humano: `origen` y
   `paginas_origen` con precisión suficiente para reagrupar después.
8. **Coste conocido**: el `PdfPort` recibe bytes en cada llamada, así que el
   troceado abre el PDF cuatro veces por parte (texto, huella, contenido y
   extracción). Sobre la remesa real —22 páginas— son decenas de aperturas de
   un documento de pocos MB, muy lejos de los 230 s de la Function. Se deja
   escrito porque, si alguna remesa creciera mucho, este es el sitio a mirar.

### Riesgo 4 del diseño: comprobado, **no da la cara**

`design.md` §7 mandaba **parar y reportar** si `extraer_paginas` no conservara
el contenido de la página. No hace falta: `test_f002_r12_el_hash_no_depende_de_los_bytes_del_pdf_resultante`
y su gemelo para páginas escaneadas demuestran que la página extraída da la
misma huella que en la remesa de origen, con capa de texto y sin ella. R14 se
cumple en los dos sentidos y con las dos familias de PDF.

---

## 3 · Fase RED · trazas reales

Las tareas `· RED` de `tasks.md` se ejecutaron con los tests escritos **antes**
que el código. Estas son las salidas reales, tal cual.

### T3 · regla del pie de página (R7–R10)

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_pie_de_pagina.py -q

=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f002_pie_de_pagina.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f002_pie_de_pagina.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f002_pie_de_pagina.py:16: in <module>
    from domain.models.pie_de_pagina import PieDePagina
E   ModuleNotFoundError: No module named 'domain.models.pie_de_pagina'
=========================== short test summary info ===========================
ERROR tests/test_f002_pie_de_pagina.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.18s
```

### T5 · adaptador de PDF (R12, R15)

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_adaptador_pdf.py -q

=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f002_adaptador_pdf.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f002_adaptador_pdf.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f002_adaptador_pdf.py:23: in <module>
    from domain.models.errores import PdfIlegible
E   ImportError: cannot import name 'PdfIlegible' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f002_adaptador_pdf.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.38s
```

### T7 · ingesta (R1–R6)

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_ingesta.py -q

=================================== ERRORS ====================================
_________________ ERROR collecting tests/test_f002_ingesta.py _________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f002_ingesta.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f002_ingesta.py:27: in <module>
    from infrastructure.documentos import zip_estandar
E   ImportError: cannot import name 'zip_estandar' from 'infrastructure.documentos' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\infrastructure\documentos\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f002_ingesta.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

Tras T8 —adaptador de ZIP ya escrito, pipeline todavía no— la misma suite
enseña **el rojo parcial que la propia tarea T8 anuncia**: verde lo que
depende del adaptador, rojo lo que depende del pipeline.

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_ingesta.py -q
FF......FFFFF.....                                                       [100%]
================================== FAILURES ===================================
_______________ test_f002_r1_conserva_orden_y_nombre_de_origen ________________
    def _ingesta(entradas):
        """Ejecuta el paso de ingesta con el adaptador real de ZIP."""
>       from application.pipelines.contexto import ContextoRemesa
E       ModuleNotFoundError: No module named 'application.pipelines.contexto'

tests\test_f002_ingesta.py:38: ModuleNotFoundError
```

### T9 · troceado (R7–R15)

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_troceado.py -q

=================================== ERRORS ====================================
________________ ERROR collecting tests/test_f002_troceado.py _________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f002_troceado.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f002_troceado.py:18: in <module>
    from application.pipelines.contexto import ContextoRemesa
E   ModuleNotFoundError: No module named 'application.pipelines.contexto'
=========================== short test summary info ===========================
ERROR tests/test_f002_troceado.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

### T11 · endpoint (R16–R18)

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_split_http.py tests/test_f002_arquitectura.py -q

=================================== ERRORS ====================================
_______________ ERROR collecting tests/test_f002_split_http.py ________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f002_split_http.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f002_split_http.py:27: in <module>
    from interface_adapters.api.split import trocear_remesa
E   ModuleNotFoundError: No module named 'interface_adapters.api.split'
=========================== short test summary info ===========================
ERROR tests/test_f002_split_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.44s
```

### T11 · R19, el test guardián · RED **en copia aislada**

`test_f002_arquitectura.py` pasa contra el árbol real desde el primer día: su
entregable es el propio test. Se demostró su fase RED como manda
`CHECKPOINTS.md` C4 bis: copiando el servicio a un directorio temporal fuera
del repositorio, metiendo ahí `import zipfile` en
`domain/models/pie_de_pagina.py` y ejecutando el test sobre esa copia. **El
árbol real no se tocó**; la copia se borró después.

```
$ cd <copia temporal del servicio> && python -m pytest tests/test_f002_arquitectura.py -q
FF                                                                       [100%]
================================== FAILURES ===================================
_____________ test_f002_r19_el_dominio_no_importa_infraestructura _____________

    def test_f002_r19_el_dominio_no_importa_infraestructura():
        """R19 · el dominio no sabe de PyMuPDF, ni de ZIP, ni de Azure."""
        ficheros = sorted((SERVICIO / "domain").rglob("*.py"))
        ...
>       assert culpables == {}
E       AssertionError: assert {'domain\\mod...: ['zipfile']} == {}
E
E         Left contains 1 more item:
E         {'domain\\models\\pie_de_pagina.py': ['zipfile']}
E         Use -v to get more diff

tests\test_f002_arquitectura.py:61: AssertionError
____ test_f002_r19_los_adaptadores_de_documentos_estan_en_infraestructura _____
>       assert fuera == []
E       AssertionError: assert ['domain\\mod...de_pagina.py'] == []
E
E         Left contains one more item: 'domain\\models\\pie_de_pagina.py'
E         Use -v to get more diff

tests\test_f002_arquitectura.py:74: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f002_arquitectura.py::test_f002_r19_el_dominio_no_importa_infraestructura
FAILED tests/test_f002_arquitectura.py::test_f002_r19_los_adaptadores_de_documentos_estan_en_infraestructura
2 failed in 0.13s
```

### Dos tests escritos **después** del código, y por qué

Honestidad sobre el orden, porque el resto sí fue RED primero:

- `test_f002_r2_una_ruta_que_sale_del_zip_se_descarta_con_aviso`: lo pidió la
  puerta de cobertura, que señaló esa guarda como la única línea del alcance
  sin ejercitar (commit `da9a26d`).
- Los tres tests de inmutabilidad (`..._no_se_puede_retocar...`): los pidió la
  campaña de mutación (commit `f06929c`). No son relleno para el contador:
  vigilan un invariante real —a un parte no se le puede cambiar el hash
  después de calcularlo— y sin ellos `frozen=True` era decorativo.

---

## 4 · Trazabilidad requisito → test

Los 19 requisitos EARS tienen test con el nombre exacto de la tabla de
`requirements.md`, y todos pasan. **87 tests de F-002, 76 de ellos con nombre
trazable `test_f002_rN_...`**, repartidos así (contados con
`pytest --collect-only | grep -c "test_f002_rN_"`):

| R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 7 | 2 | 4 | 3 | 7 | 1 | 8 | 7 | 1 |

| R11 | R12 | R13 | R14 | R15 | R16 | R17 | R18 | R19 |
|---|---|---|---|---|---|---|---|---|
| 6 | 6 | 3 | 2 | 7 | 3 | 1 | 2 | 2 |

Los nombres de la tabla viven donde ocurre el requisito: R1–R6 en
`test_f002_ingesta.py` (R5 en `test_f002_split_http.py`, que es donde está el
400), R7–R15 en `test_f002_troceado.py` (con el nivel de adaptador en
`test_f002_adaptador_pdf.py` y el de dominio puro en
`test_f002_pie_de_pagina.py`), R16–R18 en `test_f002_split_http.py` y R19 en
`test_f002_arquitectura.py`.

---

## 5 · Verificaciones MANUAL (humano) pendientes

### T15 · acierto sobre la remesa real de Mirasierra

**No ejecutada**: es del humano, y el PDF
`docs/referencia/doc02871320260817093833.pdf` **no está versionado** (lleva
datos personales), así que tiene que existir en el árbol de quien lo lance.
Comando exacto, desde la raíz del repositorio:

```bash
cd services/postventa-api && .venv/Scripts/python.exe -c "
from pathlib import Path
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.split import trocear_remesa
ruta = Path('../../docs/referencia/doc02871320260817093833.pdf')
res = trocear_remesa([DocumentoEntrada(nombre=ruta.name, contenido=ruta.read_bytes())])
print('partes:', res['total_partes'])
print('modos:', sorted({p['modo_deteccion'] for p in res['partes']}))
print('hashes distintos:', len({p['hash'] for p in res['partes']}))
print('paginas por parte:', [len(p['paginas_origen']) for p in res['partes']])
print('avisos:', res['avisos'])
"
```

**Resultado esperado**: `partes: 22`, `modos: ['una_pagina_por_parte']`,
`hashes distintos: 22`, `paginas por parte: [1] * 22`, `avisos: []`.
Solo imprime recuentos: ningún dato personal sale por pantalla y no escribe
nada en disco. El resultado real se anota en `progress/current.md`.

---

## 6 · Aviso al líder: trabajo ajeno colado en un commit de esta rama

El commit `3211984` («F-002 T11: …») arrastró, además de sus dos ficheros de
test, cambios que **no son de F-002**: `specs/F-003-extraccion/` (los tres
documentos), `progress/spec_F-003.md`, `BACKLOG.md` y el estado de F-003 en
`harness/features.json`. Estaban preparados en el índice de git por otra
sesión que trabajaba en paralelo, y mi `git commit` se los llevó por delante.

**No los he tocado**: borrarlos de la rama podría destruir el trabajo de esa
sesión, y eso no es una decisión mía. Queda aquí anotado para que el líder o
el humano decidan si se quedan en esta rama o se mueven a la suya. No afecta a
nada de lo verificado en F-002.

---

## 7 · Evidencias

| Evidencia | Valor real | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados** | **104 pasan, 0 fallan**: 94 de la suite del servicio (87 de ellos de F-002, 7 heredados de F-001) + 10 de la suite del arnés en la raíz | salida de `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (273/273 líneas, umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / supervivientes** | **44 generados, 44 muertos, 0 supervivientes, 0 timeouts** | `python -m harness.mutacion --feature F-002` → `progress/mutacion_F-002.md` |
| **Tiempo de ejecución de la suite** | **5,12 s** la del servicio dentro de `init.sh` (2,3 s lanzada sola); 0,22 s la de la raíz. Campaña de mutación: 28,6 s | salida de las propias suites |

### Supervivientes de la campaña: ninguno, y cómo se llegó ahí

La **primera** campaña dejó 4 supervivientes. El nivel `critico` exige cero, y
ninguno se justificó a la ligera:

| Superviviente | Qué se hizo |
|---|---|
| `@dataclass(frozen=True)` → `frozen=False` en `PieDePagina` | Test nuevo: leer el pie y no poder retocarlo después |
| `@dataclass(frozen=True)` → `frozen=False` en `DocumentoEntrada` | Test nuevo: lo que subió el usuario es lo que se procesa |
| `@dataclass(frozen=True)` → `frozen=False` en `ParteTroceado` | Test nuevo: al parte no se le cambia el hash después de calcularlo —de eso depende «reprocesar no duplica»— |
| `get_images(full=True)` → `full=False` en `pdf_pymupdf.py` | **Equivalente de verdad**: de cada imagen solo se usa el `xref`, que es el elemento 0 en las dos formas. En vez de justificar un superviviente, se quitó el parámetro que no aportaba nada |

El informe `progress/mutacion_F-002.md` corresponde a la **campaña final**
sobre el código tal y como está en `HEAD`: sección «Supervivientes» → *Ninguno:
cada mutación aplicada la cazó al menos un test.*

### Otras comprobaciones

- `ruff` desde la raíz —que es como lo ejecuta el portero—: **32 avisos, la
  deuda previa exacta**. Cero avisos nuevos.
- Nada de `muestras/`, ningún PDF real y ningún dato personal han entrado en
  git: los únicos ficheros binarios que tocan los tests se generan en memoria.
- Ni una dependencia nueva más allá de `pymupdf`, que la spec exigía.
