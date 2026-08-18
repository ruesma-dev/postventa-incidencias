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
> **Las cuatro decisiones abiertas están resueltas** (humano, 2026-08-18;
> detalle en `design.md` §9 y en `progress/spec_F-003.md`): entra
> `numero_pagina` (T6), entra el endpoint `POST /api/extraer` (T15–T16), el
> campo de la unidad de posventa se llama **`unidad`**, y
> `harness/rutas_sensibles.json` **no se toca aquí** (es F-015). **No queda
> ninguna tarea condicional**: las 21 se ejecutan, **8 de ellas con fase RED**
> (T2, T4, T6, T7, T9, T11, T13, T15).
>
> **Modelo por defecto: `gemini-3.7-flash`** (decisión del humano, 2026-08-18).
> Es configuración —`GEMINI_MODEL`—, no diseño: el adaptador no depende de la
> versión. Su identificador se confirma contra la API en el primer paso de
> **T17**.
>
> **Correcciones de orden aplicadas el 2026-08-18**: las dos verificaciones
> `MANUAL (humano)` pasan a ser **T17** y **T18**, justo detrás del endpoint, y
> la documentación y la campaña de mutación bajan a **T19** y **T20**.

- [x] **T1**: Declarar `google-genai>=0.3`, `pyyaml>=6.0` y
      `tenacity>=8.2,<10.0` en `services/postventa-api/requirements.txt` e
      instalarlos en el venv del servicio.
      **Verificación**: `cd services/postventa-api && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt && .venv/Scripts/python.exe -c "import google.genai, yaml, tenacity; print('ok')"`
      imprime `ok`, y `.venv/Scripts/python.exe -m pytest -q` sigue en verde
      (F-001 y F-002 intactas).

- [x] **T2 · RED**: Escribir `tests/test_f003_arquitectura.py` con
      `test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red` (R19): abrir un
      socket contra cualquier host debe levantar el error de la guardia.
      **Verificación**: el test falla porque **hoy la conexión se intenta de
      verdad**; **traza pegada** en `progress/impl_F-003.md`.

- [x] **T3**: Implementar la **guardia de red** en
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
      `tests/test_f003_extraccion_dominio.py` (R1, R3, R5): los ocho campos de
      contenido de R1 están declarados —con `unidad`, no `vivienda` ni
      `chalet`—; los tres manuscritos están marcados como tales; un
      `CampoExtraido` guarda valor y confianza; el número de incidencia conserva
      la barra y la fecha manuscrita no se reformatea.
      *(El noveno campo, `numero_pagina`, entra en T6: aquí no.)*
      **Verificación**: rojo por `ModuleNotFoundError` / `ImportError`; **traza
      pegada** en `progress/impl_F-003.md`.

- [ ] **T5**: Implementar `domain/models/extraccion.py`,
      `domain/models/prompt.py`, `domain/ports/extractor.py`,
      `domain/ports/prompts.py` y las excepciones nuevas en
      `domain/models/errores.py` (`design.md` §4.1–§4.5).
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q` en verde.

- [ ] **T6 · RED + verde**: El campo **`numero_pagina`** (R2 bis, decisión D1
      del humano). Primero el test —`test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie`
      en `tests/test_f003_extraccion_dominio.py`: el campo está declarado, es
      **impreso** (no entra en `CAMPOS_MANUSCRITOS`) y una respuesta simulada
      con `"Página 2"` en el pie devuelve `"2"` con su confianza—, y
      `test_f003_r2bis_la_extraccion_no_reagrupa_paginas` en
      `tests/test_f003_paso_extraccion.py`: leer `numero_pagina = "2"` **no**
      altera `paginas_origen`, ni `modo_deteccion`, ni une nada — F-003 lee, no
      reagrupa. Después, añadir la entrada a `CAMPOS_DEL_PARTE`.
      **Verificación**: **traza en rojo pegada** en `progress/impl_F-003.md` y
      luego los dos tests en verde. La línea del prompt que describe el campo
      entra en T8, y el schema estructurado se genera solo desde
      `CAMPOS_DEL_PARTE`: no hay una tercera copia que mantener.

- [ ] **T7 · RED**: Escribir `tests/test_f003_prompts_yaml.py` (R8, R9, R10):
      el prompt se carga del YAML con `system`, `task`, `schema` y `version`;
      un fichero inexistente falla nombrando la ruta; una clave desconocida
      falla listando las disponibles; una entrada sin `system` o sin `task`
      falla; y la huella cambia si cambia el texto (dos YAML temporales creados
      por el propio test con `tmp_path`).
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T8**: Escribir `services/postventa-api/config/prompts.yaml` con la clave
      `parte_posventa_es` según el contenido normativo de `design.md` §5.2
      —los nueve campos, incluida la línea de `numero_pagina` («lee el pie
      impreso; si no se ve, `null`; **no lo deduzcas**»)— y **sin un solo dato
      personal**. Implementar `infrastructure/prompts/prompts_yaml.py`.
      **Verificación**: los tests de T7 en verde, y
      `.venv/Scripts/python.exe -c "from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml; p = RepositorioPromptsYaml('config/prompts.yaml').obtener('parte_posventa_es'); print(p.clave, p.version, p.schema, p.huella)"`
      imprime la clave, la versión, el schema y la huella (no imprime el texto).

- [ ] **T9 · RED**: Escribir `tests/test_f003_paso_extraccion.py` (R2, R4, R6,
      R7, R13, R16) contra `ExtractorFalso`: el resultado trae **siempre las
      nueve claves**; un campo ausente sale `None`/`0` con aviso; una clave
      inventada por el modelo se descarta con aviso; confianza `120` → `100`,
      `-5` → `0`, `"no sé"` → `0`, cada una con su aviso; la traza trae
      proveedor, modelo, `prompt_key`, versión y huella, y el `hash` del parte;
      el resultado **no** trae veredicto, firma, nombre de fichero ni rutas; un
      parte por encima de `MAX_BYTES_PARTE` levanta `ParteDemasiadoGrande`
      **sin que el doble reciba ninguna llamada**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T10**: Implementar `application/pipelines/contexto_parte.py` y
      `application/pipelines/paso_extraccion.py` (`design.md` §4.3).
      **Verificación**: `.venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q` en verde, incluido el
      `test_f003_r2bis_la_extraccion_no_reagrupa_paginas` de T6.

- [ ] **T11 · RED**: Escribir `tests/test_f003_adaptador_gemini.py` (R14, R15)
      con `ClienteGenaiFalso` y `espera_inicial_s=0`: un error transitorio se
      reintenta y la segunda respuesta vale; agotados los reintentos, sale
      `ExtraccionFallida`; una respuesta que no es JSON, o que no es un mapping,
      sale `ExtraccionFallida`; un error **no** transitorio no se reintenta (el
      doble registra **una** llamada); y el mensaje de la excepción **no
      contiene los bytes del parte ni ningún valor extraído**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

- [ ] **T12**: Implementar `infrastructure/llm/gemini.py`
      (`AdaptadorGeminiVision`) con el schema estructurado generado desde
      `CAMPOS_DEL_PARTE` —los nueve campos, todos `required`— y el logging sin
      datos del parte (`design.md` §4.4).
      **Verificación**: los tests de T11 en verde. Ningún test abre red (la
      guardia de T3 lo garantiza).

- [ ] **T13 · RED**: Escribir `tests/test_f003_fabrica.py` (R11, R12): con la
      configuración por defecto la fábrica devuelve el adaptador de Gemini y el
      modelo es `gemini-3.7-flash`; `GEMINI_MODEL` cambia el modelo sin tocar
      nada más; `IA_PROVIDER=inventado` levanta `ProveedorNoSoportado`
      **listando los válidos**; sin `GEMINI_API_KEY` levanta
      `ConfiguracionIaIncompleta` nombrando la variable y **sin que el valor de
      la credencial aparezca en el mensaje**. Añadir a
      `tests/test_f003_arquitectura.py` **dos** tests más:
      `test_f003_r13_dominio_y_aplicacion_no_importan_proveedores` (R13):
      recorrido con `ast` de `domain/` y `application/` comprobando que ninguno
      importa `google`, `yaml`, `tenacity` ni `infrastructure`; y
      `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt` (**segunda mitad
      de R8**): ningún módulo bajo `services/postventa-api/` fuera de
      `config/prompts.yaml` contiene el texto del prompt —se comprueba con una
      firma del `system`/`task` cargados del YAML, o con las frases normativas de
      `design.md` §5.2—, de forma que el único sitio donde vive el prompt siga
      siendo el YAML.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

      > El test de R8 estaba declarado en la tabla de trazabilidad de
      > `requirements.md` y asignado a `test_f003_arquitectura.py` en
      > `design.md` §2, pero **ninguna tarea lo mandaba escribir**. Es el que
      > impide que alguien vuelva a incrustar el prompt en el código, o sea, el
      > requisito que más se degrada solo.

- [ ] **T14**: Ampliar `config/settings.py` con los ajustes de IA de
      `design.md` §8 (credencial **opcional**), actualizar `.env.example` con
      placeholders, e implementar `infrastructure/llm/fabrica.py`.
      **Verificación**: los tests de T13 en verde y la suite completa del
      servicio también. `.env` **no se toca**.

- [ ] **T15 · RED**: Escribir `tests/test_f003_extraer_http.py` (R17, R18) con
      **los cuatro caminos de respuesta**, uno por test:
      - `test_f003_r17_extraer_devuelve_200_con_el_contrato`: `POST` con un PDF
        devuelve **200** con el contrato exacto de `design.md` §4.6 —**nueve**
        campos— con dobles inyectados.
      - `test_f003_r18_extraer_sin_fichero_responde_400`: sin fichero, **400** y
        el doble **no** recibe llamada.
      - `test_f003_r18_parte_demasiado_grande_responde_413`: un cuerpo por encima
        de `MAX_BYTES_PARTE` responde **413** (no 502), el doble **no** recibe
        llamada y la respuesta no lleva el contenido del parte.
      - `test_f003_r18_extraccion_fallida_responde_502`: si el extractor levanta
        `ExtraccionFallida`, **502** y la respuesta **no** contiene el contenido
        del parte.

      **Verificación**: rojo; **traza pegada** en `progress/impl_F-003.md`.

      > El camino 413 se prueba **porque el rigor es `critico`**: sin su test, el
      > mapeo de `ParteDemasiadoGrande` en `function_app.py` es superficie de
      > mutantes sin cubrir, y T20 sacaría supervivientes que habría que
      > justificar a mano en vez de matarlos con una línea de test.

- [ ] **T16**: Implementar `interface_adapters/api/extraer.py` (handler +
      composición) y añadir la ruta `extraer` en `function_app.py` con el mapeo
      de errores a 400 / 413 / 502.
      **Verificación**: los tests de T15 en verde y la suite completa también.

> **A partir de aquí, el orden importa y no es el obvio.** Las dos
> verificaciones `MANUAL (humano)` van **inmediatamente después de T16**, en
> cuanto el adaptador y el endpoint están hechos, y **antes** de documentar
> (T19) y de la campaña de mutación (T20). Razón, en una línea: **si el modelo
> no lee estos manuscritos no falla F-003 —su contrato se cumpliría igual—,
> falla la premisa del proyecto, y saberlo antes ahorra la campaña de mutación
> entera.** Es un cambio de orden, no de alcance: las 21 tareas siguen siendo
> las mismas y `bash harness/init.sh` en verde sigue siendo la última.

- [ ] **T17**: **MANUAL (humano)** — humo contra el modelo **real** con un
      parte **sintético** (sin ningún dato personal). Requiere `GEMINI_API_KEY`
      en el `.env` local del servicio; **la clave no se pega en ningún informe
      ni en ningún commit**.

      **Primer paso, antes de gastar ninguna llamada de extracción: confirmar
      contra la API que el identificador del modelo existe tal y como está
      escrito** (`design.md` §8). Un ID mal escrito **no lo caza ningún test**
      —ahí el modelo está simulado— y revienta en tiempo de ejecución con un 404
      del proveedor, fácil de confundir con un problema de credencial:

      ```bash
      cd services/postventa-api && .venv/Scripts/python.exe -c "
      from config.settings import obtener_ajustes
      from google import genai
      ajustes = obtener_ajustes()
      cliente = genai.Client(api_key=ajustes.gemini_api_key)
      nombres = [m.name for m in cliente.models.list()]
      print('GEMINI_MODEL =', ajustes.gemini_model)
      print('reconocido:', any(ajustes.gemini_model in n for n in nombres))
      "
      ```

      Si sale `reconocido: False`, **es una parada**: se le pregunta al humano
      cuál es el identificador correcto; **no** se sustituye por otro modelo por
      iniciativa propia. Confirmado el ID, el humo:

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

      **Resultado esperado**: las **nueve** claves presentes, la traza con
      `proveedor=gemini` y `modelo=gemini-3.7-flash`, `codigo_obra` y
      `numero_incidencia` con los valores que el generador sintético imprime
      (`0677` y `RS26.08/0123`) y `numero_pagina = "1"`. Aquí **sí** se pueden
      imprimir los valores: son inventados. El resultado real se anota en
      `progress/current.md`.

- [ ] **T18**: **MANUAL (humano)** — acierto sobre **un parte real** de la
      remesa de Mirasierra. **Es el momento de la verdad del proyecto entero**:
      lo que se comprueba aquí no es el contrato de F-003 (eso ya lo demuestra
      la suite) sino si el modelo **lee de verdad estos manuscritos y estos
      escaneos**. Por eso va aquí y no al final. El fichero
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
          visible = campo['valor'] if nombre == 'numero_pagina' else (campo['valor'] is not None)
          print(f'{nombre}: {visible} confianza={campo[\"confianza_pct\"]}')
      print('avisos:', res['avisos'])
      "
      ```

      **Resultado esperado**: las nueve claves; `codigo_obra` y
      `numero_incidencia` con `True` y confianza alta; `numero_pagina` con
      valor `"1"` —es el dato que hace viable F-014, y por eso es el **único**
      cuyo valor se imprime: un número de página no es dato personal—; y los
      campos que el papel deja en blanco con `False` y confianza 0 (es lo normal
      en esta remesa, no un fallo: `docs/referencia/02_parte_de_trabajo.md`).
      Del resto de campos el comando imprime **solo el nombre, un booleano y la
      confianza**: **ningún valor extraído sale por pantalla**, porque el parte
      lleva DNI, y no escribe nada en disco. Lo que se anota en
      `progress/current.md` son esos booleanos y confianzas, **nunca los
      valores**.

      **Si el resultado es malo, se para y se habla con el humano antes de
      seguir con T19–T21.** Un acierto pobre no se arregla con más tests ni con
      más mutación: se arregla tocando el prompt (T8) o cambiando de modelo, y
      ambas cosas invalidarían el trabajo de documentar y mutar hecho encima.

- [ ] **T19**: Actualizar `docs/ARCHITECTURE.md`: `infrastructure/prompts/` en
      el árbol; en el paso 3 del pipeline, que la extracción devuelve
      **confianza por campo**, que lee el «Página N» del pie **sin reagrupar**
      (eso es F-014) y que **no juzga la firma** (eso es el paso 4); y en la
      tabla de sistemas externos, que el proveedor y el modelo se eligen con
      `IA_PROVIDER` / `GEMINI_MODEL`.
      **Verificación**: el diff del documento lo refleja y
      `bash harness/init.sh` sigue en verde.

- [ ] **T20**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-003` genera
      `progress/mutacion_F-003.md` con **cero supervivientes** (nivel
      `critico`), o cada superviviente con su análisis escrito y aceptado por
      el humano.

- [ ] **T21**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` (umbral 80 %).
