<!-- specs/F-004-validacion/tasks.md -->
# F-004 · Validación del parte y clasificación de la firma — Tareas

> Rigor **`critico`**: los tests se escriben **antes** que el código y la
> **traza real en rojo** de cada tarea RED se pega en `progress/impl_F-004.md`.
> Un «se hizo TDD» sin traza es un checkbox vacío (`CHECKPOINTS.md` C4 bis).
>
> Una tarea = un commit `F-004 Tn: ...`. Rama `feature/F-004-validacion`.
>
> La suite del servicio se ejecuta así (desde la raíz del repositorio):
> `cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q`
>
> **18 tareas, 7 de ellas con fase RED** (T1, T3, T6, T8, T11, T13 y la parte
> roja de T4). **T14** es la verificación `MANUAL (humano)` de la clasificación
> de firma sobre los partes reales y **T18** es `bash harness/init.sh` en verde:
> las dos anclas que `requirements.md` y `design.md` ya dan por hechas.
>
> **Ni un dato real en ningún fichero de esta feature.** Los partes llevan DNI
> de clientes y el historial de git no suelta lo que entra: todos los ejemplos
> de tests, fixtures y documentación son inventados (`design.md` §6).
>
> **Ninguna dependencia nueva.** F-004 reutiliza `ExtractorPort`,
> `RepositorioPromptsPort` y el adaptador de Gemini de F-003 (`design.md` §2).
> Si al implementar pareciera necesario tocar `domain/ports/`, **es una parada**
> y se marca `blocked`: significaría que la vía B del diseño no era la correcta.

## Orden y por qué es este

Tres bloques encadenados, y el orden no es negociable:

1. **T1–T5 · la firma**: dominio, registro de schemas y prompt. Primero porque
   `validar_parte` necesita `LecturaFirma` para existir.
2. **T6–T13 · las reglas y la tubería**: dominio puro, pasos, HTTP y guardias
   de arquitectura.
3. **T14 · el dato que decide D1**, en cuanto el endpoint funciona y **antes**
   de documentar, cubrir y mutar. Misma razón que en F-003: si el modelo no
   distingue una firma de un aspa, no falla el contrato de F-004 —la suite
   pasaría igual—, falla **D1** (`design.md` §7), y enterarse aquí ahorra la
   documentación y la campaña de mutación enteras.
4. **T15–T18 · el cierre**: documentación, cobertura, mutación y arnés.

---

## Bloque 1 · La firma (T1–T5)

- [ ] **T1 · RED**: Escribir `tests/utiles_validacion.py` con
      `lectura_de_firma(clasificacion="humana", confianza=93)` y
      `respuesta_de_firma(etiqueta="humana", confianza=93)` (`design.md` §6), y
      `tests/test_f004_firma_dominio.py` con R1, R2 y R14:
      las cuatro etiquetas existen y son exactamente cuatro
      (`test_f004_r1_las_cuatro_etiquetas_de_firma`); una etiqueta desconocida
      y la ausencia de etiqueta caen en `ILEGIBLE` y **nunca** en `HUMANA`
      (`test_f004_r2_una_etiqueta_desconocida_es_ilegible`,
      `test_f004_r2_sin_etiqueta_es_ilegible_nunca_humana`); y una `HUMANA` con
      confianza por debajo del umbral **no** es conformidad del cliente
      (`test_f004_r14_una_firma_humana_dudosa_se_trata_como_ilegible`).
      **Verificación**: rojo por `ModuleNotFoundError` / `ImportError`; **traza
      pegada** en `progress/impl_F-004.md`.

- [ ] **T2**: Implementar `domain/models/firma.py` (`ClasificacionFirma`,
      `CAMPO_CLASIFICACION`, `CAMPOS_DE_LA_FIRMA`, `clasificacion_desde_texto`,
      `LecturaFirma.es_conformidad_del_cliente`) y añadir a
      `domain/models/errores.py` las tres excepciones nuevas de `design.md`
      §4.4: `SchemaDesconocido`, `ValidacionSinDatos` y
      `CuerpoDeValidacionInvalido`.
      **Verificación**:
      `.venv/Scripts/python.exe -m pytest tests/test_f004_firma_dominio.py -q`
      en verde y la suite completa del servicio sin regresiones.

- [ ] **T3 · RED**: Escribir `tests/test_f004_prompts_firma.py` con R4 y R5:
      - `test_f004_r4_el_prompt_de_firma_existe_y_es_otro`: la clave
        `firma_parte_es` se carga del YAML con `system`, `task`, `schema` y
        `version`, y su huella **no** es la de `parte_posventa_es`.
      - `test_f004_r4_el_prompt_de_extraccion_conserva_su_huella`: la huella de
        `parte_posventa_es` sigue siendo **`2306ac1d07f1`**, la que se midió en
        F-003 sobre 22 partes reales. Es la constante que clava que F-004 no ha
        rozado el prompt medido (decisión D3 de `design.md` §7).
      - `test_f004_r5_cada_prompt_declara_un_schema_conocido`: **todas** las
        claves de `config/prompts.yaml` declaran un `schema` que está en
        `CAMPOS_POR_SCHEMA`; un nombre no registrado levanta `SchemaDesconocido`
        **antes** de llamar al modelo (el doble no recibe ninguna llamada).
      - `test_f004_r5_el_schema_de_la_firma_tiene_su_unico_campo`:
        `campos_del_schema("firma_cliente")` es exactamente
        `("clasificacion_firma",)`, y `campos_del_schema("parte_posventa")`
        sigue siendo los nueve de F-003.

      **Verificación**: rojo; **traza pegada** en `progress/impl_F-004.md`.

- [ ] **T4 · RED + verde**: Implementar `domain/models/schemas.py`
      (`CAMPOS_POR_SCHEMA`, `campos_del_schema`) y convertir
      `schema_del_parte()` en `schema_para(nombre)` en
      `infrastructure/llm/gemini.py`, resolviendo contra el registro y usando
      `prompt.schema` en la llamada (`design.md` §2).
      Adaptar `tests/test_f003_adaptador_gemini.py` **solo** al renombrado
      (`schema_para("parte_posventa")`): **ni una aserción cambia de
      significado**, y esa es la prueba de que no se ha roto nada (Riesgo 5).
      **Verificación**: los tests de R5 de T3 en verde y **toda la suite de
      F-003 en verde sin haber cambiado ninguna aserción**:
      `.venv/Scripts/python.exe -m pytest tests/test_f003_adaptador_gemini.py tests/test_f004_prompts_firma.py -q`.
      La parte RED es el rojo previo de T3; si al adaptar F-003 hubiera que
      tocar una aserción de verdad, **es una parada**.

- [ ] **T5**: Añadir a `config/prompts.yaml` la clave `firma_parte_es` con el
      contenido normativo de `design.md` §5 —una casilla, la del **cliente**
      (columna izquierda, «Fdo.» / «DNI»), las cuatro etiquetas con su
      criterio, «ante la duda, `ilegible`», «no transcribas el nombre ni el
      DNI», confianza entera 0–100— y **sin un solo dato personal**.
      `parte_posventa_es` **no se toca ni una coma**. Añadir
      `prompt_key_firma` (`PROMPT_KEY_FIRMA`, por defecto `firma_parte_es`) a
      `config/settings.py` y la variable a `.env.example` con su valor por
      defecto. **`.env` no se toca.**
      **Verificación**: los tests de T3 en verde y
      ```bash
      cd services/postventa-api && .venv/Scripts/python.exe -c "from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml; p = RepositorioPromptsYaml('config/prompts.yaml').obtener('firma_parte_es'); print(p.clave, p.version, p.schema, p.huella)"
      ```
      imprime la clave, la versión, `firma_cliente` y la huella (no imprime el
      texto del prompt).

## Bloque 2 · Las reglas y la tubería (T6–T13)

- [ ] **T6 · RED**: Ampliar `tests/utiles_validacion.py` con
      `extraccion_de_ejemplo(**cambios)` —los nueve campos, reutilizando
      `CAMPOS_DE_EJEMPLO` de `utiles_ia.py`, **todo inventado**— y escribir
      `tests/test_f004_reglas_validacion.py` con **R6 a R19**, un test por
      nombre declarado en `requirements.md`. Los que no pueden faltar:
      - **R7** completo y firmado sin observaciones → `apto` +
        `archivo_y_cierre` + **cero** motivos.
      - **R8/R9/R10** observaciones no vacías → `no_apto` +
        `cola_validacion_humana`, con la **transcripción literal** y su
        confianza en el resultado, y el mismo veredicto diga lo que diga el
        texto (dos textos inventados distintos, mismo resultado).
      - **R11/R12** campo decisivo vacío, «solo espacios» o con confianza por
        debajo del umbral → nunca `apto`; **justo en el umbral (50) sí es
        legible**.
      - **R13** las tres etiquetas no humanas → `firma_no_humana` +
        `revision_manual`, con **tres textos distintos** (casilla vacía, marca
        simple, ilegible).
      - **R15/R16/R17** sin DNI sale `apto`; ningún campo no decisivo vacío
        cambia el veredicto; **ningún** formato se exige al `numero_incidencia`
        (un valor con barra y otro sin ella salen igual de aptos).
      - **R18** varios incumplimientos → **todos** los motivos, en el orden
        declarado: código de obra, nº de incidencia, firma, observaciones.
      - **R19** incompleto **y** con observaciones → `revision_manual`, y la
        transcripción viaja igual.
      - **R6** todos los motivos traen texto en castellano llano: ningún texto
        contiene un nombre de campo del código (`codigo_obra`,
        `numero_incidencia`, `confianza_pct`) ni jerga técnica.

      **Verificación**: rojo; **traza pegada** en `progress/impl_F-004.md`.

- [ ] **T7**: Implementar `domain/models/validacion.py` (`Veredicto`,
      `Destino`, `CodigoMotivo`, `Motivo`, `ResultadoValidacion`,
      `CAMPOS_DECISIVOS`, `UMBRAL_CONFIANZA = 50`, `validar_parte`) con los
      cinco pasos y los seis textos de `design.md` §4.2. **Función pura**: sin
      reloj, sin azar, sin red, sin imports de `infrastructure`.
      **Verificación**:
      `.venv/Scripts/python.exe -m pytest tests/test_f004_reglas_validacion.py -q`
      en verde, con **todos** los tests de T6 pasando.

- [ ] **T8 · RED**: Escribir `tests/test_f004_paso_firma.py` (R2, R3) y
      `tests/test_f004_paso_validacion.py` (R21) contra dobles:
      el paso traduce el campo único a la enumeración; una etiqueta desconocida
      sale `ILEGIBLE` **con aviso**; la confianza se sanea con la **misma**
      regla que la extracción (`120` → `100`, `-5` → `0`, `"no sé"` → `0`, cada
      una con su aviso); la traza trae proveedor, modelo, `prompt_key`, versión
      y huella; un parte por encima de `MAX_BYTES_PARTE` levanta
      `ParteDemasiadoGrande` **sin que el doble reciba ninguna llamada**; y
      `paso_validacion` sin extracción, o sin lectura de firma, levanta
      `ValidacionSinDatos` **sin inventarse veredicto**.
      **Verificación**: rojo; **traza pegada** en `progress/impl_F-004.md`.

- [ ] **T9**: Extraer el saneo de confianza a
      `application/pipelines/confianza.py` (`sanear_confianza`,
      `CONFIANZA_MINIMA`, `CONFIANZA_MAXIMA`) y hacer que
      `paso_extraccion.py` lo importe en vez de tener copia propia.
      **Comportamiento idéntico.** Ampliar `contexto_parte.py` con
      `lectura_firma: LecturaFirma | None` y
      `validacion: ResultadoValidacion | None`.
      **Verificación**: **los tests de F-003 pasan sin tocarlos** —esa es la
      prueba del refactor—:
      `.venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q`
      en verde y la suite completa también.

- [ ] **T10**: Implementar `application/pipelines/paso_firma.py` y
      `application/pipelines/paso_validacion.py` (`design.md` §4.3).
      `MAX_BYTES_PARTE` se **importa** de `paso_extraccion`, no se duplica;
      `paso_validacion` **no recibe puertos**.
      **Verificación**:
      `.venv/Scripts/python.exe -m pytest tests/test_f004_paso_firma.py tests/test_f004_paso_validacion.py -q`
      en verde y la suite completa del servicio también.

- [ ] **T11 · RED**: Escribir `tests/test_f004_firma_http.py` (R23) y
      `tests/test_f004_validar_http.py` (R24), **un test por camino de
      respuesta**, con dobles inyectados:
      - `test_f004_r23_el_endpoint_de_firma_devuelve_el_contrato`: **200** con
        exactamente `hash_parte`, `firma`, `traza` y `avisos`, **y ninguna
        clave más** (se comprueba el conjunto de claves, no que estén).
      - `test_f004_r23_sin_fichero_es_400`, con el doble **sin** recibir
        llamada.
      - `test_f004_r23_un_parte_demasiado_grande_es_413` (no 502), con el doble
        **sin** recibir llamada y sin el contenido del parte en la respuesta.
      - `test_f004_r23_un_proveedor_caido_es_502`, sin el contenido del parte
        en la respuesta.
      - `test_f004_r24_validar_devuelve_el_veredicto_sin_llamar_al_modelo`: el
        cuerpo con las dos partes tal cual las emiten `/api/extraer` y
        `/api/firma` devuelve **200** con el veredicto, y **ningún doble de
        extractor recibe llamada** (se afirma sobre el contador del doble, no
        solo sobre el 200).
      - `test_f004_r24_un_cuerpo_incompleto_es_400`: falta `extraccion`, falta
        `firma` o falta el `hash_parte` → **400 diciendo qué falta**.

      **Verificación**: rojo; **traza pegada** en `progress/impl_F-004.md`.

      > El camino 413 y el «sin llamar al modelo» se prueban **porque el rigor
      > es `critico`**: sin ellos, el mapeo de errores y el «`/api/validar` es
      > puro» son superficie de mutantes sin cubrir, y T17 sacaría
      > supervivientes que habría que justificar a mano en vez de matarlos con
      > una línea de test.

- [ ] **T12**: Implementar `interface_adapters/api/firma.py` (`leer_firma`, con
      la composición del paso) e `interface_adapters/api/validar.py`
      (`validar`, **sin IA y sin PDF**), y añadir en `function_app.py` las dos
      rutas `POST /api/firma` y `POST /api/validar` con el mapeo de errores a
      400 / 413 / 502. `interface_adapters/api/extraer.py` **no se toca**: su
      contrato no gana ninguna clave.
      **Verificación**: los tests de T11 en verde y la suite completa también.

- [ ] **T13 · RED + verde**: Escribir `tests/test_f004_arquitectura.py` con
      R20, R22, R25 y R26:
      - `test_f004_r20_las_reglas_no_importan_infraestructura` y
        `test_f004_r22_el_modulo_de_validacion_no_conoce_sigrid`: recorrido con
        `ast` de `domain/` y `application/` —el mismo patrón que el test de R13
        de F-003— comprobando que no importan `google`, `yaml`, `tenacity`,
        `infrastructure`, ni nada de Sigrid, ni ningún cliente de BBDD.
      - `test_f004_r20_validar_no_abre_ninguna_conexion`: `validar_parte` se
        ejecuta con la guardia de red de `conftest.py` activa y no la dispara.
      - `test_f004_r25_el_log_no_lleva_observaciones_ni_dni`: con `caplog`,
        validar un parte cuyas observaciones y DNI son cadenas inventadas y
        **reconocibles** deja en el log hash, veredicto, destino y códigos de
        motivo, y **ninguna** de esas dos cadenas.
      - `test_f004_r26_la_suite_no_abre_red` y
        `test_f004_r26_ningun_test_lee_muestras`: ningún fichero de
        `tests/test_f004_*.py` ni `tests/utiles_validacion.py` menciona
        `muestras`, `docs/referencia` ni ninguna ruta a `.pdf` del árbol real.

      **Verificación**: primero rojo con la **traza pegada** en
      `progress/impl_F-004.md` (para R25, rompiendo deliberadamente la línea de
      log en una copia aislada si ya naciera limpia — `CHECKPOINTS.md` C4 bis);
      después la suite completa del servicio en verde.

## Bloque 3 · El dato que decide D1 (T14)

- [ ] **T14 · MANUAL (humano)**: **la distribución real de las cuatro etiquetas
      de firma sobre los 22 partes de la remesa de Mirasierra.** Es lo que
      decide **D1** (`design.md` §7): si la firma puede o no bloquear un parte.
      Va aquí, y no al final, por el Riesgo 1 del diseño.

      Requiere `GEMINI_API_KEY` en el `.env` local del servicio (ya existe) y
      el PDF `docs/referencia/doc02871320260817093833.pdf`, que **no está
      versionado**: tiene que existir en el árbol de quien ejecute. **La clave
      no se pega en ningún informe ni en ningún commit.**

      **Entrega para el humano (obligatoria, no es un comando largo).** El
      humano trabaja en **PowerShell**, que no admite `&&` y parte los comandos
      largos al pegarlos: la verificación se entrega como un **script en su
      home**, `C:\Users\pgris\f4_firma.py`, **fuera del repositorio** —igual
      que `f3_real.py`—, más **una línea corta** para invocarlo:

      ```
      python C:\Users\pgris\f4_firma.py todos
      ```

      Acepta `f4_firma.py` (solo el primer parte), `f4_firma.py 0 7 15` (esos)
      o `f4_firma.py todos` (los 22 con el recuento agregado). El script:
      trocea la remesa con `trocear_remesa`, llama a `leer_firma` parte a
      parte, e imprime **por parte: índice, etiqueta y confianza**, y al final
      **el recuento de las cuatro etiquetas** y la confianza media de cada una.
      Avisa y para si falta el `.env`, si la clave sigue con el placeholder o
      si no encuentra el PDF.

      **No imprime, ni escribe en disco, ningún valor extraído del parte**: ni
      nombre, ni DNI, ni observaciones. La etiqueta de la firma
      (`humana` / `marca_simple` / `casilla_vacia` / `ilegible`) y su confianza
      **no son datos personales**; el nombre de la casilla sí, y por eso el
      prompt de T5 ni siquiera lo pide.

      **Verificación**: `MANUAL (humano)`. Lo que se anota en
      `progress/current.md` es **el recuento y las confianzas, nunca valores**.

      **Cómo se lee el resultado, decidido de antemano para que el dato no se
      interprete a conveniencia:**
      - Mayoría `humana` y `ilegible` residual → **D1 opción 1 confirmada**: la
        spec queda como está y se sigue en T15.
      - Un tercio o más `ilegible` → **PARADA**. Se habla con el humano antes
        de T15–T18: o se sube la calidad del prompt de firma (T5) y se repite
        T14, o se pasa a la **opción 2** de D1 (la clasificación viaja como
        aviso y no bloquea). Cambiar de opción cuesta **una rama de
        `validar_parte` y sus tests**: ni el contrato HTTP, ni el dominio, ni
        los pasos se mueven. Documentar y mutar antes de saberlo sería tirar
        ese trabajo.
      - Alguna `marca_simple` detectada → es la prueba directa del criterio
        `acceptance` «la clasificación distingue firma de aspa» y de
        `CHECKPOINTS.md` C3. Se anota expresamente.

## Bloque 4 · Cierre (T15–T18)

- [ ] **T15**: Actualizar `docs/ARCHITECTURE.md`: en el **paso 4** del
      pipeline, los **dos destinos** (`cola_validacion_humana` para decidir,
      `revision_manual` para arreglar), qué campos son decisivos y qué queda
      para **F-008** (coherencia con Sigrid) y **F-016** (interpretar las
      observaciones); en la **semántica 3**, cómo conviven la regla de la firma
      y el «único motivo de rechazo» (`design.md` §1). Corregir además el
      docstring de `CAMPOS_MANUSCRITOS` en `domain/models/extraccion.py`: tras
      la decisión del 2026-08-19, el conjunto que decide «firmado no es
      conforme» es **solo `observaciones`**, y dejarlo como está sería dejar
      una afirmación falsa en el código.
      **Verificación**: el diff de ambos ficheros lo refleja y
      `bash harness/init.sh` sigue en verde.

- [ ] **T16**: Cobertura de las líneas cambiadas.
      **Verificación**: `bash harness/init.sh` imprime la puerta de cobertura
      en **`[OK]`** con el porcentaje de las líneas cambiadas (umbral 80 %). Si
      sale por debajo, se añaden los tests que falten **a los ficheros de test
      de F-004 que ya existen** —no se baja el umbral y no se marca N/A: para
      una feature `critico` eso es un checkbox vacío (`CHECKPOINTS.md` C4 bis)—.
      El detalle por fichero se obtiene con
      `python -m harness.cobertura --feature F-004` desde la raíz.

- [ ] **T17**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-004` desde la
      raíz del repositorio genera `progress/mutacion_F-004.md` con **cero
      supervivientes** (nivel `critico`), o cada superviviente con su análisis
      escrito y aceptado por el humano. Ninguna sección puede quedar en
      `PENDIENTE`.

      > Los mutantes de esta feature se concentran donde están los umbrales y
      > los booleanos: `UMBRAL_CONFIANZA >= 50`, el «único motivo» de R9 y las
      > tres ramas de texto de `firma_no_humana`. Si sobrevive alguno ahí, el
      > test que falta es el del **borde** (`49`, `50`, `51`), no uno más del
      > caso feliz.

- [ ] **T18**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la puerta de cobertura de las líneas
      cambiadas en `[OK]` (umbral 80 %) y `ENTORNO LISTO`. El informe del
      implementer cierra con la sección **«Evidencias»** y sus cuatro números:
      tests ejecutados y resultado, cobertura de las líneas cambiadas, mutantes
      generados y supervivientes, y tiempo de la suite.

---

## Verificaciones `MANUAL (humano)` de esta feature

Una sola, y está detallada arriba:

| Tarea | Qué mide | Cómo se invoca (PowerShell) |
|---|---|---|
| **T14** | Distribución de las cuatro etiquetas de firma sobre los 22 partes reales de Mirasierra. **Decide D1** | `python C:\Users\pgris\f4_firma.py todos` |

El script vive **fuera del repositorio**, en el home del humano, por la lección
operativa 2 de `progress/current.md`: PowerShell no admite `&&`, indenta los
`-c` multilínea de Python y parte las líneas largas al pegarlas. Nunca se le
entrega un comando largo.

**No hace falta repetir el chequeo del identificador del modelo** (`f3_modelo.py`
de F-003): F-004 no cambia `GEMINI_MODEL`, y el modelo `gemini-3.7-flash` ya se
confirmó contra la API el 2026-08-19.

## Lo que ninguna tarea de esta lista hace

Consta por escrito para que no se lea como un olvido (`design.md` §0):
interpretar **qué dice** la observación (F-016), comprobar contra Sigrid que la
incidencia exista o esté abierta (F-008/F-009), **guardar** la cola de
validación humana (F-005), **pintarla** (F-007/F-011) y reagrupar el parte de
dos hojas (F-014). Ni SQL, ni SharePoint, ni persistencia, ni front, ni
`harness/features.json` —lo lleva el líder—, ni `push`, ni PR.
