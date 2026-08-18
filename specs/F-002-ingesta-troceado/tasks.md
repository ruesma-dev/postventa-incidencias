<!-- specs/F-002-ingesta-troceado/tasks.md -->
# F-002 · Ingesta y troceado — Tareas

> Rigor **`critico`**: los tests se escriben **antes** que el código y la
> **traza real en rojo** de cada tarea RED se pega en `progress/impl_F-002.md`.
> Un «se hizo TDD» sin traza es un checkbox vacío (CHECKPOINTS C4 bis).
>
> Una tarea = un commit `F-002 Tn: ...`. Rama `feature/F-002-ingesta-troceado`.
>
> La suite del servicio se ejecuta así (desde la raíz del repositorio):
> `cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q`

- [x] **T1**: Declarar `pymupdf>=1.24,<2.0` en
      `services/postventa-api/requirements.txt` e instalarlo en el venv del
      servicio.
      **Verificación**: `cd services/postventa-api && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt && .venv/Scripts/python.exe -c "import pymupdf; print(pymupdf.__doc__)"`
      imprime la versión, y `.venv/Scripts/python.exe -m pytest -q` sigue en
      verde (F-001 intacta).

- [x] **T2**: Escribir el generador de PDFs sintéticos
      `services/postventa-api/tests/utiles_pdf.py` (`pagina_de_parte`,
      `remesa_sintetica`, `remesa_escaneada`, `zip_con`) imitando la plantilla
      y el pie de `docs/referencia/02_parte_de_trabajo.md`, **sin ningún dato
      personal**, y sus tests `tests/test_f002_utiles_pdf.py`: el PDF
      sintético tiene las páginas pedidas y su pie es legible; el «escaneado»
      devuelve 0 caracteres de texto y una imagen por página.
      **Verificación**: `cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f002_utiles_pdf.py -q` en verde.
      *(Sin fase RED: el generador es material de test, no código de
      producción cuyo fallo previo se pueda enseñar.)*

- [x] **T3 · RED**: Escribir `tests/test_f002_pie_de_pagina.py` (R7–R10) sobre
      `PieDePagina`: `Página 1` abre parte, `Página 2` con plantilla es
      continuación, `Página 2` **sin** el marcador de plantilla abre parte,
      texto sin pie abre parte, y se toma la **última** aparición de `Página N`
      del texto.
      **Verificación**: los tests fallan con `ModuleNotFoundError` / `ImportError`;
      **traza pegada** en `progress/impl_F-002.md`.

- [x] **T4**: Implementar `domain/models/pie_de_pagina.py`,
      `domain/models/remesa.py` y `domain/models/errores.py`.
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f002_pie_de_pagina.py -q` en verde.

- [x] **T5 · RED**: Escribir los tests del adaptador de PDF (R12, R15) contra
      PDFs sintéticos: `texto_por_pagina` devuelve una entrada por página;
      `huella_de_paginas` es SHA-256 hex de 64 caracteres, **estable entre dos
      llamadas** y **distinta** para páginas distintas; la huella de la página
      N del multi-parte coincide con la de la página 1 del PDF extraído de esa
      misma página; página en blanco detectada.
      **Verificación**: los tests fallan por no existir el adaptador; **traza
      pegada** en `progress/impl_F-002.md`.

- [x] **T6**: Implementar `domain/ports/pdf.py` (`PdfPort`) e
      `infrastructure/documentos/pdf_pymupdf.py` (`AdaptadorPdfPyMuPdf`) con
      el cálculo de huella descrito en `design.md` §4.
      **Verificación**: los tests de T5 en verde.
      **Si R14 no se cumpliera aquí** (el contenido de la página no sobrevive
      a `extraer_paginas`): **PARAR**, marcar la feature `blocked` y anotarlo
      en `progress/current.md`. Nada de workarounds.

- [x] **T7 · RED**: Escribir `tests/test_f002_ingesta.py` (R1–R6): orden y
      nombre de origen conservados; ZIP aporta sus PDF en orden alfabético;
      lo que no es PDF se descarta con aviso; ZIP anidado con aviso; PDF
      corrupto no tumba la remesa; ZIP que se pasa de los límites levanta
      `LimiteDeEntradaSuperado` **sin descomprimir**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-002.md`.

- [x] **T8**: Implementar `domain/ports/comprimido.py` e
      `infrastructure/documentos/zip_estandar.py` (`AdaptadorZipEstandar`),
      con `MAX_ENTRADAS_ZIP` y `MAX_BYTES_DESCOMPRIMIDOS` comprobados sobre el
      índice del ZIP.
      **Verificación**: los tests de ingesta que no dependen del pipeline, en
      verde.

- [x] **T9 · RED**: Escribir `tests/test_f002_troceado.py` (R7–R15) sobre los
      pasos del pipeline: `remesa_sintetica([1,1,2,1])` → **3 partes** con
      `paginas_origen` `[1]`, `[2,3]`, `[4]`; `remesa_sintetica([2,1])` → 2
      partes y **aviso** en el primero; `remesa_escaneada(22)` → 22 partes y
      `modo_deteccion == "una_pagina_por_parte"`; dos pasadas dan los mismos
      hashes; el ZIP de partes sueltos y el PDF multi-parte dan **la misma
      lista de hashes en el mismo orden** (R14).
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-002.md`.

- [x] **T10**: Implementar `application/pipelines/contexto.py`,
      `paso_ingesta.py` y `paso_troceado.py`.
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f002_ingesta.py tests/test_f002_troceado.py -q` en verde.

- [x] **T11 · RED**: Escribir `tests/test_f002_split_http.py` (R16–R18) y
      `tests/test_f002_arquitectura.py` (R19): `POST /api/split` multipart
      devuelve 200 con el contrato exacto de `design.md` §4; sin ficheros,
      400; ZIP fuera de límite, 413; el JSON **no** trae campos de negocio; y
      ningún módulo de `domain/` importa `pymupdf`, `fitz`, `zipfile`, `azure`
      ni `infrastructure` (recorrido con `ast` sobre los ficheros).
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-002.md`.

- [x] **T12**: Implementar `interface_adapters/api/split.py` (handler +
      composición del pipeline) y añadir la ruta `split` en
      `function_app.py`, con el mapeo de errores a 400 y 413.
      **Verificación**: los tests de T11 en verde y la suite completa del
      servicio también.

- [x] **T13**: Actualizar `docs/ARCHITECTURE.md`: `infrastructure/documentos/`
      en el árbol, y en el paso 2 del pipeline la nota de que el modo de
      detección degrada a «una página, un parte» cuando el PDF no trae capa de
      texto.
      **Verificación**: el diff del documento lo refleja y
      `bash harness/init.sh` sigue en verde.

- [ ] **T14**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-002` genera
      `progress/mutacion_F-002.md` con **cero supervivientes** (nivel
      `critico`), o cada superviviente con su análisis escrito y aceptado por
      el humano.

- [ ] **T15**: **MANUAL (humano)** — acierto sobre la remesa real de
      Mirasierra (criterio `acceptance` 2). El fichero
      `docs/referencia/doc02871320260817093833.pdf` **no está versionado**:
      tiene que existir en el árbol de quien ejecute.
      **Verificación**: `MANUAL (humano)`. Comando exacto, desde la raíz del
      repositorio:

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
      El comando imprime **solo recuentos**: ningún dato personal del parte
      sale por pantalla, y no escribe nada en disco.
      Sobre el «parte de dos hojas»: en esta remesa **no hay ninguno** —el pie
      de las 22 páginas dice «Página 1» (`docs/referencia/02_parte_de_trabajo.md`)—
      y además el escaneo no tiene capa de texto, así que la regla del pie no
      se puede disparar aquí; queda cubierta por los tests sintéticos de T9.
      Ver el **riesgo abierto 1** de `design.md`, que necesita decisión del
      humano.
      El resultado real de esta ejecución se anota en `progress/current.md`.

- [ ] **T16**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` (umbral 80 %).
