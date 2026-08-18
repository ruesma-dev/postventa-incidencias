<!-- specs/F-003-extraccion/tasks.md -->
# F-003 · Extracción multimodal del parte — Tareas

> Rigor **`critico`**: los tests se escriben **antes** que el código y la
> **traza real en rojo** de cada tarea RED se pega en `progress/impl_F-003.md`.
> Un «se hizo TDD» sin traza es un checkbox vacío (`CHECKPOINTS.md` C4 bis).
>
> Una tarea = un commit `F-003 Tn: ...`. Rama `feature/F-003-extraccion`.
>
> La suite del servicio se ejecuta así (desde la raíz del repositorio):
> `cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q`
>
> **Antes de empezar, el humano decide** (ver `design.md` §9):
> **D1** — si el contrato gana el campo `numero_pagina` para F-014: si **sí**,
> entra `R2 bis` con su test y una tarea entre T5 y T6; si **no**, se cierra
> con ocho campos.
> **D2** — si el endpoint `POST /api/extraer` entra en F-003: si **no**, caen
> T14 y T15 y los requisitos R17/R18.
> **D3** — `harness/rutas_sensibles.json` **no se toca en esta feature**.

- [ ] **T1**: Declarar `google-genai>=0.3`, `pyyaml>=6.0` y
      `tenacity>=8.2,<10.0` en `services/postventa-api/requirements.txt` e
      instalarlos en el venv del servicio.
      **Verificación**: `cd services/postventa-api && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt && .venv/Scripts/python.exe -c "import google.genai, yaml, tenacity; print('ok')"`
      imprime `ok`, y `.venv/Scripts/python.exe -m pytest -q` sigue en verde
      (F-001 y F-002 intactas).

- [ ] **T2 · RED**: Escribir `tests/test_f003_arquitectura.py` con
      `test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red` (R19): abrir un
      socket contra cualquier host debe levantar el error de la guardia.
      **Verificación**: el test falla porque **hoy la conexión se intenta de
      verdad**; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T3**: Implementar la **guardia de red** en
      `services/postventa-api/tests/conftest.py` (fixture autouse que sustituye
      `socket.socket.connect`), sin tocar la fixture `entorno_de_test` que ya
      existe.
      **Verificación**: `.venv/Scripts/python.exe -m pytest -q` en verde, con el
      test de T2 pasando y **la suite completa de F-001/F-002 sin regresiones**.
      Si la guardia rompiera pytest o la cobertura, aplicar **la variante B** ya
      aprobada en `design.md` §6.3 y anotarlo; cualquier tercera vía es
      `blocked`.

- [ ] **T4 · RED**: Escribir `tests/utiles_ia.py` (`respuesta_simulada`,
      `json_del_modelo`, `prompt_de_prueba`, `ExtractorFalso`,
      `ClienteGenaiFalso`) **con datos inventados**, y
      `tests/test_f003_extraccion_dominio.py` (R1, R3, R5): los campos
      declarados son los ocho de R1; los tres manuscritos están marcados como
      tales; un `CampoExtraido` guarda valor y confianza; el número de
      incidencia conserva la barra y la fecha manuscrita no se reformatea.
      **Verificación**: rojo por `ModuleNotFoundError` / `ImportError`; **traza
      pegada** en `progress/impl_F-003.md`.

- [ ] **T5**: Implementar `domain/models/extraccion.py`,
      `domain/models/prompt.py`, `domain/ports/extractor.py`,
      `domain/ports/prompts.py` y las excepciones nuevas en
      `domain/models/errores.py` (`design.md` §4.1–§4.5).
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q` en verde.

- [ ] **T6 · RED**: Escribir `tests/test_f003_prompts_yaml.py` (R8, R9, R10):
      el prompt se carga del YAML con `system`, `task`, `schema` y `version`;
      un fichero inexistente falla nombrando la ruta; una clave desconocida
      falla listando las disponibles; una entrada sin `system` o sin `task`
      falla; y la huella cambia si cambia el texto (dos YAML temporales creados
      por el propio test con `tmp_path`).
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T7**: Escribir `services/postventa-api/config/prompts.yaml` con la clave
      `parte_posventa_es` según el contenido normativo de `design.md` §5.2
      (**sin un solo dato personal**) e implementar
      `infrastructure/prompts/prompts_yaml.py`.
      **Verificación**: los tests de T6 en verde, y
      `.venv/Scripts/python.exe -c "from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml; p = RepositorioPromptsYaml('config/prompts.yaml').obtener('parte_posventa_es'); print(p.clave, p.version, p.schema, p.huella)"`
      imprime la clave, la versión, el schema y la huella (no imprime el texto).

- [ ] **T8 · RED**: Escribir `tests/test_f003_paso_extraccion.py` (R2, R4, R6,
      R7, R13, R16) contra `ExtractorFalso`: el resultado trae **siempre** las
      ocho claves; un campo ausente sale `None`/`0` con aviso; una clave
      inventada por el modelo se descarta con aviso; confianza `120` → `100`,
      `-5` → `0`, `"no sé"` → `0`, cada una con su aviso; la traza trae
      proveedor, modelo, `prompt_key`, versión y huella, y el `hash` del parte;
      el resultado **no** trae veredicto, firma, nombre de fichero ni rutas; un
      parte por encima de `MAX_BYTES_PARTE` levanta `ParteDemasiadoGrande`
      **sin que el doble reciba ninguna llamada**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T9**: Implementar `application/pipelines/contexto_parte.py` y
      `application/pipelines/paso_extraccion.py` (`design.md` §4.3).
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q` en verde.

- [ ] **T10 · RED**: Escribir `tests/test_f003_adaptador_gemini.py` (R14, R15)
      con `ClienteGenaiFalso` y `espera_inicial_s=0`: un error transitorio se
      reintenta y la segunda respuesta vale; agotados los reintentos, sale
      `ExtraccionFallida`; una respuesta que no es JSON, o que no es un mapping,
      sale `ExtraccionFallida`; un error **no** transitorio no se reintenta (el
      doble registra **una** llamada); y el mensaje de la excepción **no
      contiene los bytes del parte ni ningún valor extraído**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T11**: Implementar `infrastructure/llm/gemini.py`
      (`AdaptadorGeminiVision`) con el schema estructurado generado desde
      `CAMPOS_DEL_PARTE` y el logging sin datos del parte (`design.md` §4.4).
      **Verificación**: los tests de T10 en verde. Ningún test abre red (la
      guardia de T3 lo garantiza).

- [ ] **T12 · RED**: Escribir `tests/test_f003_fabrica.py` (R11, R12): con la
      configuración por defecto la fábrica devuelve el adaptador de Gemini y el
      modelo es `gemini-2.5-flash`; `GEMINI_MODEL` cambia el modelo sin tocar
      nada más; `IA_PROVIDER=inventado` levanta `ProveedorNoSoportado`
      **listando los válidos**; sin `GEMINI_API_KEY` levanta
      `ConfiguracionIaIncompleta` nombrando la variable y **sin que el valor de
      la credencial aparezca en el mensaje**. Añadir a
      `tests/test_f003_arquitectura.py` el test de R13: recorrido con `ast` de
      `domain/` y `application/` comprobando que ninguno importa `google`,
      `yaml`, `tenacity` ni `infrastructure`.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T13**: Ampliar `config/settings.py` con los ajustes de IA de
      `design.md` §8 (credencial **opcional**), actualizar `.env.example` con
      placeholders, e implementar `infrastructure/llm/fabrica.py`.
      **Verificación**: los tests de T12 en verde y la suite completa del
      servicio también. `.env` **no se toca**.

- [ ] **T14 · RED** *(solo si el humano aprueba D2)*: Escribir
      `tests/test_f003_extraer_http.py` (R17, R18): `POST` con un PDF devuelve
      200 con el contrato exacto de `design.md` §4.6 (dobles inyectados); sin
      fichero, 400 y el doble **no** recibe llamada; si el extractor levanta
      `ExtraccionFallida`, 502 y la respuesta **no** contiene el contenido del
      parte.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T15** *(solo si el humano aprueba D2)*: Implementar
      `interface_adapters/api/extraer.py` (handler + composición) y añadir la
      ruta `extraer` en `function_app.py` con el mapeo de errores a 400 / 413 /
      502.
      **Verificación**: los tests de T14 en verde y la suite completa también.

- [ ] **T16**: Actualizar `docs/ARCHITECTURE.md`: `infrastructure/prompts/` en
      el árbol; en el paso 3 del pipeline, que la extracción devuelve
      **confianza por campo** y **no juzga la firma** (eso es el paso 4); y en
      la tabla de sistemas externos, que el proveedor y el modelo se eligen con
      `IA_PROVIDER` / `GEMINI_MODEL`.
      **Verificación**: el diff del documento lo refleja y
      `bash harness/init.sh` sigue en verde.

- [ ] **T17**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-003` genera
      `progress/mutacion_F-003.md` con **cero supervivientes** (nivel
      `critico`), o cada superviviente con su análisis escrito y aceptado por
      el humano.

- [ ] **T18**: **MANUAL (humano)** — humo contra el modelo **real** con un
      parte **sintético** (sin ningún dato personal). Requiere `GEMINI_API_KEY`
      en el `.env` local del servicio; **la clave no se pega en ningún informe
      ni en ningún commit**.
      **Verificación**: `MANUAL (humano)`. Comando exacto, desde la raíz:

      ```bash
      cd services/postventa-api && .venv/Scripts/python.exe -c "
      from tests.utiles_pdf import remesa_sintetica
      from interface_adapters.api.extraer import extraer_parte
      pdf = remesa_sintetica([1])
      res = extraer_parte(pdf, hash_parte='humo')
      print('traza:', res['traza'])
      for nombre, campo in res['campos'].items():
          print(f'{nombre}: valor={campo[\"valor\"]!r} confianza={campo[\"confianza_pct\"]}')
      print('avisos:', res['avisos'])
      "
      ```

      **Resultado esperado**: las **ocho** claves presentes, la traza con
      `proveedor=gemini` y `modelo=gemini-2.5-flash`, y al menos
      `codigo_obra` y `numero_incidencia` leídos con los valores que el
      generador sintético imprime (`0677` y `RS26.08/0123`). Aquí **sí** se
      pueden imprimir los valores: son inventados. El resultado real se anota
      en `progress/current.md`.

- [ ] **T19**: **MANUAL (humano)** — acierto sobre **un parte real** de la
      remesa de Mirasierra. El fichero
      `docs/referencia/doc02871320260817093833.pdf` **no está versionado**:
      tiene que existir en el árbol de quien ejecute.
      **Verificación**: `MANUAL (humano)`. Comando exacto, desde la raíz:

      ```bash
      cd services/postventa-api && .venv/Scripts/python.exe -c "
      from pathlib import Path
      from domain.models.remesa import DocumentoEntrada
      from interface_adapters.api.split import trocear_remesa
      from interface_adapters.api.extraer import extraer_parte
      import base64
      ruta = Path('../../docs/referencia/doc02871320260817093833.pdf')
      partes = trocear_remesa([DocumentoEntrada(nombre=ruta.name, contenido=ruta.read_bytes())])['partes']
      p = partes[0]
      res = extraer_parte(base64.b64decode(p['contenido_b64']), hash_parte=p['hash'])
      print('traza:', res['traza'])
      for nombre, campo in res['campos'].items():
          print(f'{nombre}: tiene_valor={campo[\"valor\"] is not None} confianza={campo[\"confianza_pct\"]}')
      print('avisos:', res['avisos'])
      "
      ```

      **Resultado esperado**: las ocho claves, `codigo_obra` y
      `numero_incidencia` con `tiene_valor=True` y confianza alta, y los campos
      que el papel deja en blanco con `tiene_valor=False` y confianza 0 (es lo
      normal en esta remesa, no un fallo: `docs/referencia/02_parte_de_trabajo.md`).
      El comando imprime **solo nombres de campo, un booleano y la confianza**:
      **ningún valor extraído sale por pantalla**, porque el parte lleva DNI, y
      no escribe nada en disco. Lo que se anota en `progress/current.md` son
      esos booleanos y confianzas, **nunca los valores**.

- [ ] **T20**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` (umbral 80 %).
