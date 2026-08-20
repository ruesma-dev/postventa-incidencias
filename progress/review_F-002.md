<!-- progress/review_F-002.md -->
# F-002 · Ingesta y troceado — Informe de review

**Veredicto: APPROVED**

Rama `feature/F-002-ingesta-troceado`. Revisado contra
`specs/F-002-ingesta-troceado/{requirements,design,tasks}.md`, `CHECKPOINTS.md`,
`docs/CONVENTIONS.md` y `docs/ARCHITECTURE.md`.

**Fuera de esta review por indicación del líder** (trabajo de otra sesión
arrastrado por el commit `3211984`): `specs/F-003-extraccion/`,
`progress/spec_F-003.md`, `BACKLOG.md` y el estado de F-003/F-014/F-015 en
`harness/features.json`. Comprobado que **no se perdió nada de F-002** por ese
solapamiento: el commit `3211984` sí contiene los dos ficheros de test de T11
(`test_f002_split_http.py`, `test_f002_arquitectura.py`) y el diff
`dev...HEAD` trae los 13 ficheros de producción y los 8 de test previstos.

---

## Nivel de rigor y puertas exigidas

`harness/features.json` declara `rigor: "critico"` para F-002. Exige, además de
C1–C3 y C5: tests trazables, **fase RED** con traza real, **cobertura** de las
líneas cambiadas ≥ 80 %, **campaña de mutación con cero supervivientes** y las
verificaciones `MANUAL (humano)` listadas con su comando exacto.

---

## Comprobaciones hechas por mí, no leídas del informe

| Qué | Cómo lo he comprobado | Resultado |
|---|---|---|
| Portero en verde | `bash harness/init.sh` tal cual | exit 0, `ENTORNO LISTO` |
| Suite del servicio sin caché | `cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest -q` | **94 passed in 3.06s** |
| Suite del arnés | dentro de `init.sh` | **10 passed** |
| Tests trazables | `pytest --collect-only -q \| grep -c test_f002_r` | **76** (coincide con el informe) |
| Cobertura | línea `PUERTA COBERTURA` de `init.sh` | `[OK] 100.0% de 273 líneas cambiadas (273/273, umbral 80%)` |
| Cobertura **recalculada a mano** | `harness.alcance` + `services/postventa-api/coverage.json`, contando cubiertas/relevantes por fichero | **273/273**, y **ningún fichero del alcance sale «no medido»** (que es como se colaría un 100 % falso) |
| Alcance de mutación | `harness.alcance.alcance_de_feature('F-002')` | 13 ficheros, **749 líneas** — coincide con la tabla de `progress/mutacion_F-002.md` |
| Nº de mutantes | `harness.mutacion.generar_mutantes` fichero a fichero (cálculo puro) | **44** — coincide exactamente, con el mismo reparto por fichero |
| Muertos/supervivientes | **campaña completa reejecutada** con `--salida` al scratchpad, sin tocar `progress/` | **44 evaluados, 44 muertos, 0 supervivientes, 0 timeouts en 29.7 s** |
| Fase RED, verificada contra el historial | `git ls-tree -r` sobre los commits RED | en `5f5385c` (T3), `035c3ee` (T7), `7d43ebe` (T9) y `3211984` (T11) está el **fichero de test y NO está el módulo de producción** que la traza dice que faltaba |
| Ruff | `python -m ruff check .` | 32 avisos, **cero en ficheros de F-002** (deuda previa exacta) |
| Sin datos personales en git | `git log --all --diff-filter=A --name-only \| grep -iE '\.pdf$\|\.docx$\|\.xlsx$\|muestras/'` | **ningún resultado**: nunca ha entrado un PDF ni un ofimático |
| Árbol limpio tras mis pruebas | `git status --porcelain` | vacío |

La campaña de mutación declara 0 **supervivientes**, no 0 mutantes, así que la
prueba de control del cero (regenerar ignorando la exclusión de alcance) no
aplica: hay 44 mutantes reales y los he visto ejecutarse uno a uno.

---

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. Ejecutado por mí.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-002 (lo valida `init.sh`).
- [x] Rama actual `feature/F-002-ingesta-troceado`.
- [x] `progress/current.md` describe solo la sesión activa de F-002.
- [x] F-001, la única `done`, tiene su resumen en `progress/history.md:8`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `domain/` no importa `pymupdf`, `fitz`,
      `zipfile`, `azure`, `infrastructure`, `application` ni `config`; los dos
      adaptadores viven en `infrastructure/documentos/`; la composición del
      pipeline está en el punto de entrada
      (`interface_adapters/api/split.py:38-41`), como manda
      `docs/CONVENTIONS.md:12-14`. Además hay un **test guardián** que lo
      vigila con `ast` en las dos direcciones
      (`tests/test_f002_arquitectura.py:47` y `:64`).
- [x] Primera línea con la ruta relativa en **los 21 ficheros `.py`** del diff
      (comprobado uno a uno con `head -1`).
- [x] Sin `print()` en producción, sin `TODO`/`FIXME`/`HACK` añadidos, sin
      secretos, sin dependencias fuera de la spec (solo `pymupdf>=1.24,<2.0`,
      `services/postventa-api/requirements.txt`, previsto en `design.md` §6).
- [x] **La unidad de trabajo es el parte, no el fichero**: `ParteTroceado`
      lleva `origen` + `paginas_origen`, y el modo de detección se calcula
      **por documento y no por remesa**, con test que lo fija
      (`tests/test_f002_troceado.py:158`).
- [x] Nada se archiva ni se cierra: F-002 no toca Sigrid, SharePoint ni BBDD.
- [x] Lo manuscrito / firma / conformidad: **N/A justificado** — R18 prohíbe
      explícitamente interpretar el contenido en esta feature y hay dos tests
      que lo vigilan (`tests/test_f002_split_http.py:172` y `:187`).
- [x] **Reprocesar no duplica**: hash SHA-256 sobre el contenido de las
      páginas de origen, no sobre los bytes del PDF resultante
      (`infrastructure/documentos/pdf_pymupdf.py:50-60`), con R13 y R14
      probados en las dos familias de PDF (con capa de texto y escaneado).
- [x] Número de estado de Sigrid: **N/A justificado** — F-002 no habla con
      Sigrid (`design.md` §8).
- [x] Ningún parte escaneado ni PDF ha entrado en git, comprobado sobre el
      historial completo con `--diff-filter=A`, no solo sobre el árbol.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: el diff `dev...HEAD` **no añade ni modifica ningún fichero
de `docs/referencia/`**. El único documento externo que se cita
(`doc02871320260817093833.pdf`) no está versionado y ningún test lo abre; todo
el material de prueba se fabrica en memoria (`tests/utiles_pdf.py`).

### C4 — La verificación es real

- [x] **Los 19 requisitos EARS tienen test con el nombre canónico de la tabla
      de trazabilidad**, comprobado nombre a nombre contra
      `requirements.md:144-164`: los 22 nombres de la tabla existen y todos
      pasan. Tabla completa más abajo.
- [x] **Los tests no tocan red, BBDD, IA ni `muestras/`.** Comprobado por
      búsqueda: ni `requests`, ni `urllib`, ni `socket`, ni `psycopg`, ni
      lecturas de disco. Los PDF y los ZIP se generan en memoria con PyMuPDF y
      `io.BytesIO` (`tests/utiles_pdf.py:80-156`), sin un solo dato personal.
- [x] La verificación `MANUAL (humano)` está en `progress/current.md:41-67`
      con su comando exacto, su resultado esperado y **`Resultado real:
      PENDIENTE de ejecutar por el humano`**.

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"` declarado en `harness/features.json`.
- [x] **Fase RED.** `progress/impl_F-002.md:101-272` trae la salida real de
      T3, T5, T7 (más el rojo parcial tras T8, que es un `AssertionError` de
      ejecución, no de colección), T9 y T11. Además lo he **verificado contra
      el historial de git**: en cada commit RED el test existe y el módulo de
      producción todavía no. La fase RED de R19 —cuyo entregable es el propio
      test— se demostró rompiendo el invariante **en una copia fuera del
      repositorio**, como exige C4 bis, y la traza pegada es un fallo de
      aserción real (`impl_F-002.md:242-271`).
- [x] **Cobertura**: `[OK] 100.0 %` de 273 líneas cambiadas, umbral 80 %.
      Recalculada por mí desde `coverage.json`: 273/273, sin ficheros no
      medidos.
- [x] **Mutación**: existe `progress/mutacion_F-002.md`, generado por la
      herramienta, con totales **verificados de forma independiente** (alcance
      749 líneas y 44 mutantes recalculados; campaña reejecutada: 44/44
      muertos).
- [x] **Cero supervivientes**, como exige `critico`. Nada que analizar. El
      informe del implementer documenta además los 4 supervivientes de la
      **primera** campaña y qué se hizo con cada uno
      (`impl_F-002.md:367-381`): tres se cerraron con tests de inmutabilidad
      que vigilan un invariante real —el hash de un parte no se puede retocar
      después de calcularlo, de eso depende «reprocesar no duplica»— y el
      cuarto se cerró **quitando el parámetro equivalente** en vez de
      justificarlo. Es la respuesta correcta a un mutante, no el atajo.
- [x] Sección **«Evidencias»** con los cuatro números
      (`impl_F-002.md:358-365`): 104 tests, 100 % de cobertura, 44/0 mutantes,
      tiempos de suite y de campaña. Todos coinciden con lo que he medido.
- [x] Ningún punto N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A por configuración, sin justificación exigible**: no existe
`harness/rutas_sensibles.json` en este repositorio (solo el `.ejemplo.json`), y
`CHECKPOINTS.md:165-166` dice literalmente que sin esa declaración el bloque es
N/A y no hay nada que justificar. La puerta de `init.sh` no señaló ninguna ruta
tocada.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con T1–T14 y T16 en `[x]` y **un commit `F-002 Tn: ...` por
      tarea** (T1 `2b13828` … T14 `55c9124`/`ab4e2fb`, T16 `bf58a2e`), más tres
      commits de ajuste con el formato `F-002: ...` que permite
      `docs/CONVENTIONS.md:47`.
- [x] **T15 sigue en `[ ]`**, que es lo correcto: es `MANUAL (humano)` y no la
      ha ejecutado nadie. Está documentada con el comando exacto y el resultado
      esperado en `tasks.md:114-146` y en `progress/current.md:41-67`. **No la
      he ejecutado yo.**
- [x] `git status` limpio, sin artefactos sueltos.
- [x] `features.json` refleja el estado real: F-002 `in_progress` (pasa a
      `done` con este veredicto más T15, decisión del líder/humano).

---

## Cobertura requisito → test

| Req | Test | Fichero |
|---|---|---|
| R1 | `test_f002_r1_conserva_orden_y_nombre_de_origen` | `tests/test_f002_ingesta.py` |
| R2 | `test_f002_r2_zip_aporta_sus_pdf_en_orden_alfabetico`, `test_f002_r2_zip_descarta_lo_que_no_es_pdf_con_aviso` | `tests/test_f002_ingesta.py` |
| R3 | `test_f002_r3_entrada_que_no_es_pdf_ni_zip_se_descarta_con_aviso` | `tests/test_f002_ingesta.py` |
| R4 | `test_f002_r4_pdf_corrupto_no_tumba_la_remesa` | `tests/test_f002_ingesta.py` |
| R5 | `test_f002_r5_sin_pdf_utilizable_responde_400` | `tests/test_f002_split_http.py` |
| R6 | `test_f002_r6_zip_que_supera_el_limite_se_rechaza_sin_descomprimir` | `tests/test_f002_ingesta.py` |
| R7 | `test_f002_r7_una_pagina_un_parte` | `tests/test_f002_troceado.py` |
| R8 | `test_f002_r8_pagina_2_es_continuacion_del_parte_anterior` | `tests/test_f002_troceado.py` |
| R9 | `test_f002_r9_sin_pie_reconocido_abre_parte_nuevo`, `test_f002_r9_pagina_1_abre_parte_nuevo` | `tests/test_f002_troceado.py` |
| R10 | `test_f002_r10_primera_pagina_continuacion_abre_parte_con_aviso` | `tests/test_f002_troceado.py` |
| R11 | `test_f002_r11_sin_capa_de_texto_el_modo_es_una_pagina_por_parte` | `tests/test_f002_troceado.py` |
| R12 | `test_f002_r12_el_hash_es_sha256_del_contenido_de_las_paginas`, `test_f002_r12_el_hash_no_depende_de_los_bytes_del_pdf_resultante` | `tests/test_f002_adaptador_pdf.py` |
| R13 | `test_f002_r13_reprocesar_la_misma_remesa_da_los_mismos_hashes` | `tests/test_f002_troceado.py` |
| R14 | `test_f002_r14_zip_y_pdf_multiparte_dan_la_misma_lista_de_hashes` | `tests/test_f002_troceado.py` |
| R15 | `test_f002_r15_pagina_en_blanco_deja_aviso` | `tests/test_f002_troceado.py` |
| R16 | `test_f002_r16_split_devuelve_200_con_el_contrato` | `tests/test_f002_split_http.py` |
| R17 | `test_f002_r17_split_sin_ficheros_responde_400` | `tests/test_f002_split_http.py` |
| R18 | `test_f002_r18_la_respuesta_no_trae_campos_de_negocio` | `tests/test_f002_split_http.py` |
| R19 | `test_f002_r19_el_dominio_no_importa_infraestructura` | `tests/test_f002_arquitectura.py` |

Los 76 tests trazables cubren además los bordes, no solo el camino feliz: el
límite del ZIP **justo en el borde** y **justo pasado** (`test_f002_ingesta.py:294`
y `:306`), y el test de R6 que **prohíbe abrir cualquier entrada del ZIP con
`monkeypatch` sobre `zipfile.ZipFile.open`** (`:253-273`), que es la única forma
de demostrar que la bomba de descompresión se rechaza **sin descomprimirse** y
no solo que se rechaza.

---

## Lo que el humano decidió al aprobar la spec: respetado

1. **Degradación aceptada.** Implementada como pedía `design.md` §0: sin
   bifurcación de código. `_modo_de_deteccion` es una **etiqueta calculada**
   (`application/pipelines/paso_troceado.py:68-72`), no un `if` que cambie el
   algoritmo; la regla única produce «una página, un parte» porque sin texto no
   hay pie que leer.
2. **Nada preparando F-014.** Buscado explícitamente: **cero** apariciones de
   `F-014`/`F014` en el código, cero banderas, cero parámetros muertos, cero
   ramas sin ejercitar (la cobertura al 100 % y los 44 mutantes muertos lo
   corroboran: no hay código que ningún test toque). Lo único que queda es la
   precisión que se pidió conservar: `origen` (que en un ZIP incluye la
   procedencia completa, `remesa.zip/carpeta/parte.pdf`,
   `infrastructure/documentos/zip_estandar.py:51`) y `paginas_origen` numeradas
   desde 1.
3. **Riesgo 4 del diseño** («parar si `extraer_paginas` no conserva el
   contenido»): comprobado que no se da, con test en las dos familias de PDF.
   No hacía falta bloquear.

---

## Observaciones (ninguna bloquea; para la siguiente feature o para el humano)

1. **Un PDF válido de 0 páginas se descarta en silencio.**
   `application/pipelines/paso_troceado.py:44-52`: si `texto_por_pagina`
   devuelve `[]`, el bucle de agrupación no produce ningún parte y **no se
   añade aviso**, así que ese fichero desaparece del resultado sin dejar
   rastro. No incumple ningún requisito (R3 y R4 hablan de «no es PDF» y «no se
   puede abrir», y R5 salva el caso de que sea el único fichero), pero rompe el
   patrón de la feature —«lo que se descarta, se nombra»— en el único hueco que
   queda. Sugerencia para F-003 o para un ajuste menor: aviso
   `«<nombre>: el PDF no tiene páginas»`.
2. **`PdfIlegible` solo se captura en la primera llamada al puerto.**
   `paso_troceado.py:43-47` envuelve `texto_por_pagina`, pero
   `huella_de_paginas`, `paginas_sin_contenido` y `extraer_paginas`
   (`:83-90`) quedan fuera del `try`. Hoy es inalcanzable —si el documento se
   abrió una vez, se abre las cuatro— y por eso no es un defecto; anotado por
   si en F-005 se meten PDFs que se leen por partes.
3. **`docs/CONVENTIONS.md:28` («PDF en servidor: ReportLab») roza con el
   código de producción, no solo con los tests.** `design.md` §5 justificó
   PyMuPDF para el **generador de fixtures**, pero `extraer_paginas`
   (`infrastructure/documentos/pdf_pymupdf.py:62-71`) **produce un PDF de
   producto** con PyMuPDF. Es la decisión correcta —ReportLab no sabe extraer
   páginas de un PDF existente— y está dentro de la spec aprobada, así que no
   lo cuento como incumplimiento. Propuesta para el humano: matizar esa línea
   de `CONVENTIONS.md` para distinguir **componer un PDF nuevo** (ReportLab) de
   **manipular un PDF de entrada** (PyMuPDF), y evitar que la próxima review
   tenga que volver a razonarlo.
4. **El límite del ZIP se fía de lo que declara el índice.**
   `zip_estandar.py:76` suma `file_size`, que un ZIP construido a mala fe puede
   falsear; después `comprimido.read(entrada)` (`:59`) descomprime sin volver a
   medir. Es **exactamente lo que pide R6** (`requirements.md:64-67`), así que
   está conforme a spec; queda anotado como riesgo a revisar en F-010, cuando
   el endpoint quede expuesto fuera de la red interna.
5. **Coste de reapertura**, ya documentado por el implementer
   (`impl_F-002.md:85-89`): cuatro aperturas del PDF por parte. Irrelevante
   para 22 páginas; es el sitio a mirar si alguna remesa crece mucho.

---

## Automejora del arnés (propuesta, no aplicada)

La verificación independiente de la mutación que exige
`.claude/agents/reviewer.md` se queda corta en un punto: recalcular alcance y
número de mutantes **no demuestra que los muertos lo estén**. Un informe con
44 mutantes correctos y «44 muertos» inventados pasaría el recálculo puro. Lo
he cerrado reejecutando la campaña completa con `--salida` a un directorio
temporal (29,7 s, sin tocar `progress/` y con `git status` limpio después).

**Propuesta para `.claude/agents/reviewer.md` §4 y `CHECKPOINTS.md` C4 bis**:
añadir que, cuando la campaña sea barata (digamos < 5 min según el «Tiempo
total» del propio informe), el reviewer la **reejecute con `--salida` fuera de
`progress/`** y compare totales, en vez de limitarse al recálculo puro. Es
específico del arnés genérico, así que si el humano lo acepta, va a
`arnes-base` en el mismo trabajo, no solo aquí.

---

## Pendiente antes de cerrar (no es un cambio requerido)

**T15**, verificación `MANUAL (humano)`: el acierto sobre la remesa real de
Mirasierra. Está correctamente documentada y correctamente **sin marcar**. La
feature no debería pasar a `done` hasta que el humano la ejecute y anote el
resultado real en `progress/current.md`. Nada de lo que depende del
implementer queda pendiente.
