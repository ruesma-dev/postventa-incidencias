<!-- progress/spec_F-003.md -->
# F-003 · Informe del spec-author

**Fecha**: 2026-08-18 · **Feature**: F-003 «Extracción multimodal del parte,
manuscritos incluidos» · **Rigor**: `critico` · **Estado**: spec redactada,
**actualizada con las cuatro decisiones del humano** y **corregida con los seis
puntos de la revisión** (todo el 2026-08-18). No queda ninguna decisión abierta.

**Entregable**:

- `specs/F-003-extraccion/requirements.md` — 20 requisitos EARS (R1–R19 más
  **R2 bis**) con tabla de trazabilidad requisito → nombre de test.
- `specs/F-003-extraccion/design.md` — diseño técnico, 12 secciones.
- `specs/F-003-extraccion/tasks.md` — **21 tareas** atómicas, **8 de ellas con
  fase RED** (T2, T4, T6, T7, T9, T11, T13, T15), **ninguna condicional**.

No se ha escrito ni una línea de código de producción, ni se ha tocado nada
bajo `services/`, `tests/`, `harness/`, `docs/`, `.claude/`, `CHECKPOINTS.md`,
`specs/F-002-ingesta-troceado/` ni `progress/current.md`.

---

## Las seis correcciones aplicadas el 2026-08-18

Cinco vienen de la revisión de solo lectura (`progress/explore_F-003.md` §9),
aprobadas por el humano; la sexta la ordena el humano. **Ninguna cambia el
alcance de F-003**: siguen siendo los mismos nueve campos, el mismo endpoint y
las mismas 21 tareas.

### C1 · La contradicción del código HTTP: gana el **413**

`requirements.md` R18 decía «SI la extracción falla (R15/**R16**) → **502**»
mientras `design.md` §4.5 y T16 mapeaban `ParteDemasiadoGrande` → **413**. Dos
respuestas para el mismo caso, y una excusa legítima para que el reviewer
rechazara el trabajo.

**Se queda el 413** (*Payload Too Large*), que es el semánticamente correcto: al
modelo **ni se le ha llamado** (R16 corta antes), así que no hay proveedor roto
que reportar; hay una petición demasiado grande, y quien puede arreglarla es el
cliente. Lo que sobraba era la mención de R16 en R18.

Aplicado en los tres ficheros, que ahora dicen lo mismo —`400` / `413` / `502`—:
R18 reescrito con el `413` explícito y su nota de por qué; §4.5 del diseño con
un párrafo que remite a R18 y a T15/T16; T16 ya lo decía y no ha cambiado.

### C2 · El camino 413 ya tiene test

T15 solo describía los tests de 200, 400 y 502. Con rigor `critico` y campaña de
mutación de **cero supervivientes**, el mapeo del 413 en `function_app.py` era
superficie de mutantes sin cubrir: T20 habría sacado supervivientes que tocaría
justificar a mano en vez de matarlos con una línea de test.

T15 pasa a describir **los cuatro caminos, uno por test**, y la tabla de
trazabilidad de R18 incorpora
`test_f003_r18_parte_demasiado_grande_responde_413` —nombre coherente con
`..._sin_fichero_responde_400` y `..._extraccion_fallida_responde_502`—.

### C3 · El test declarado que ninguna tarea escribía

`test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt` estaba en la tabla de
trazabilidad de `requirements.md` (segunda mitad de R8) y asignado a
`test_f003_arquitectura.py` en `design.md` §2, pero **ninguna tarea lo mandaba
escribir**: T2 escribe el de red (R19) y T13 el de R13.

**Añadido a T13**, que ya toca ese fichero: ahora T13 escribe **dos** tests de
arquitectura, el de R13 y el de R8, con la comprobación descrita (ningún módulo
bajo `services/postventa-api/` fuera de `config/prompts.yaml` contiene el texto
del prompt). Es justo el test que impide que alguien vuelva a incrustar el
prompt en el código, o sea, el requisito que más se degrada solo.

### C4 · El recuento, cuadrado

Este informe decía «21 tareas, **9** con fase RED»; en `tasks.md` había **8**.
El número real, después de estas correcciones, sigue siendo **8**: T2, T4, T6,
T7, T9, T11, T13 y T15. Corregido arriba y escrito también en la cabecera de
`tasks.md`, para que el reviewer no persiga una tarea fantasma. El total de
tareas no cambia: **21**.

### C5 · La verificación contra un parte real sube al puesto 18

Era **T20**, al final de todo: después de documentar y después de la campaña de
mutación. Ahora es **T18**, inmediatamente detrás del endpoint (T16). La
verificación de humo contra el modelo real sube con ella y pasa a ser **T17**,
porque es su prerrequisito: comparte credencial, y su primer paso es confirmar
el identificador del modelo (ver C6). La documentación baja a **T19** y la
campaña de mutación a **T20**; `bash harness/init.sh` en verde sigue siendo
**T21**, la última.

**La razón, en una línea, escrita en `tasks.md` y en `design.md` §9:** si el
modelo no lee estos manuscritos no falla F-003 —su contrato se cumpliría
igual—, falla la premisa del proyecto, y saberlo antes **ahorra la campaña de
mutación entera**. T18 lleva además la instrucción de parar y hablar con el
humano si el resultado es malo: un acierto pobre se arregla tocando el prompt
(T8) o cambiando de modelo, y las dos cosas invalidarían el trabajo de
documentar y mutar hecho encima.

Renumeración propagada a las referencias cruzadas: `requirements.md` (nota de
verificación manual), `design.md` §9 (D3 y Riesgo 1).

### C6 · El modelo pasa a ser `gemini-3.7-flash`

Orden del humano. Sustituido en los tres ficheros de la spec y en este informe:
el valor por defecto de `GEMINI_MODEL` (`design.md` §8 y R11), el ejemplo de
traza del contrato de respuesta (§4.6), lo que espera el test de la fábrica
(T13) y lo que esperan las verificaciones manuales (T17).

**No ha cambiado nada del diseño, y era lo esperado**: el modelo es
**configuración**, no arquitectura. El adaptador habla con el SDK `google-genai`
y le pasa el nombre que venga de `GEMINI_MODEL`; ni los puertos, ni el paso del
pipeline, ni el schema estructurado —que se genera desde `CAMPOS_DEL_PARTE`—,
ni los tests —que usan dobles— dependen de la versión. **No he encontrado ni un
punto del diseño que dependiera de la versión concreta**, así que no hay defecto
que reportar por este lado.

Sí he corregido **dos afirmaciones de hecho** que sí nombraban la versión y
habrían quedado falsas:

- `design.md` §1 decía «El ecosistema ya extrae documentos con
  `gemini-2.5-flash`».
- `design.md` §8 justificaba el valor por defecto con «el que corre hoy en
  `albaranes` y `partes`».

Ninguna de las dos la respalda `azure-apps`, que **documenta el proveedor pero
no fija versión de modelo**. Reescritas para decir solo lo que consta: el
ecosistema usa Gemini, y el valor por defecto lo elige el humano. **No he
actualizado `azure-apps`**: cada proyecto mantiene su documento y
`postventa-incidencias` todavía no tiene el suyo (se crea en F-010).

**Comprobación nueva, añadida al diseño (§8) y a T17.** El identificador exacto
del modelo **se confirma contra la API antes de la primera llamada real**, como
primer paso de la verificación de humo, con su comando escrito. Motivo: un ID
mal escrito **no falla en los tests** —el modelo está simulado y la suite
seguiría verde— sino en tiempo de ejecución, y el síntoma (un 404 del proveedor)
se confunde fácilmente con un problema de credencial o de red. **No se ha
cambiado el nombre que ha dado el humano**; si la API no reconociera el
identificador, la spec manda **parar y preguntar**, no sustituirlo por otro
modelo.

---

## Las cuatro decisiones, resueltas por el humano el 2026-08-18

### D1 · `numero_pagina` en el contrato de F-003 — **SÍ**

Entra ya. Aplicado en la spec:

- **R2 bis** en `requirements.md`: el sistema lee el «Página N» del pie impreso
  y lo devuelve como un campo más, con su confianza; `None` si el pie no se lee.
- Novena entrada en `CAMPOS_DEL_PARTE` (`design.md` §4.1). Es campo **impreso**,
  así que no entra en `CAMPOS_MANUSCRITOS` y **no tiene camino de código
  propio**: viaja igual que los otros ocho (importa para el rigor `critico` —
  una rama especial para un solo campo sería superficie de mutantes gratis).
- Su línea en el prompt (`design.md` §5.2), con el aviso explícito de **no
  deducirlo** del número de páginas del documento.
- Tests `test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie` y
  `test_f003_r2bis_la_extraccion_no_reagrupa_paginas`.
- Tarea **T6**, entre T5 y T7, tal y como pidió el humano.

**Queda escrito, y en tres sitios** (§0 del diseño, R2 bis y el alcance de
`requirements.md`): el campo **existe para que F-014 pueda reagrupar**, pero
**F-003 no reagrupa nada**. No une páginas, no altera `paginas_origen`, no
cambia `modo_deteccion` y no reordena la lista de partes. Uno de los dos tests
de R2 bis vigila exactamente eso.

### D2 · Endpoint `POST /api/extraer` — **SÍ**

Se queda tal cual estaba diseñado: R17, R18, `interface_adapters/api/extraer.py`
y las tareas **T15** (RED) y **T16** (implementación), más la ruta en
`function_app.py` con el mapeo 400 / 413 / 502.

### D3 · Ruta sensible del prompt — **no se declara aquí; es F-015**

Aceptada la recomendación. En el diseño, la decisión abierta se ha sustituido
por la resolución: **F-015 · «Evaluación del prompt de extracción contra partes
reales»** (prioridad 15, `blocked_by` F-003), que registra el líder en
`harness/features.json`; `harness/rutas_sensibles.json` se declarará **cuando el
comando exista**, no antes.

Se conserva en `design.md` §9 (D3), como **material de partida para F-015**:

- el borrador del JSON de la declaración, con sus dos rutas
  (`config/prompts.yaml` y `domain/models/extraccion.py`) y sus motivos;
- el motivo por el que hace falta: **ningún test unitario detecta que un cambio
  de redacción del prompt empeore la extracción**, porque el modelo está
  simulado y la suite seguiría verde con el prompt roto;
- y el aviso de propagación, que F-015 debe tener delante desde el primer día:
  **ese evaluador sería genérico** —le vale igual a `partes` y a `albaranes`—,
  así que por la regla del arnés su sitio natural es **`arnes-base`**, no este
  repositorio; lo único específico de posventa son los partes de prueba y el
  umbral de acierto.

La verificación `MANUAL (humano)` contra un parte real se queda como estaba en
contenido: es lo que tapa el hueco mientras F-015 no exista. **Solo ha cambiado
de sitio**: era T20 y ahora es **T18** (corrección C5).

### D4 · El campo se llama `unidad`

Ni `chalet` (backlog) ni `vivienda` (etiqueta impresa): **`unidad`**, el término
que ya usa la estructura de archivo de Posventa
(`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`, F-013), para que el mismo
concepto se llame igual en el código y en el archivo.

Renombrado en `requirements.md` (tabla de R1, con la línea que deja constancia
de los tres nombres para que nadie lo lea como un descuido), en `design.md`
(§4.1, §4.6 y §6.2) y en `tasks.md` (T4).

---

## Lo que se ha decidido en el diseño, y por qué

1. **Se reutiliza el patrón de IA que ya corre en producción**, consultado en
   `azure-apps/partes.md` §3.2 y §5 y `azure-apps/albaranes.md` §3 antes de
   diseñar: SDK `google-genai`, prompt en YAML con clave + schema estructurado,
   y trazabilidad guardada con el dato (`proveedor`, `modelo`, `prompt_key`,
   `confianza_pct`). Mismos nombres de variables (`IA_PROVIDER`,
   `GEMINI_API_KEY`, `GEMINI_MODEL`, `PROMPT_KEY`, `PROMPTS_YAML_PATH`). No se
   ha copiado ningún documento de `azure-apps` a este repositorio.

2. **Nueve campos y una confianza entera 0–100 por campo**, incluidos los tres
   manuscritos (`fecha_servicio`, `dni_cliente`, `observaciones`). La escala
   0–100 y el nombre `confianza_pct` son los del ecosistema, no una invención.

3. **El resultado trae siempre las nueve claves**, aunque el parte las deje en
   blanco: el papel real deja vacíos fecha, horas, nombre y DNI en casi toda la
   remesa, y una clave que falta rompería F-004. Se consigue recorriendo la
   lista declarada en el dominio y no las claves que devuelve el modelo — con lo
   que «no falta ninguna» y «no sobra ninguna inventada» son la misma línea.

4. **El saneo de la confianza vive en la aplicación, no en el adaptador**: se
   prueba sin proveedor y vale igual para el siguiente proveedor que entre.

5. **Prompt fuera del código, versionado dos veces**: `version` declarada en el
   YAML (la sube quien lo cambia a conciencia) **y** una huella calculada del
   texto que se publica en la traza. La declaración dice qué querías; la huella
   dice qué había el día que se extrajo ese dato.

6. **«Ni una llamada real en la suite» pasa a ser imposible, no una promesa**:
   guardia de red autouse en `tests/conftest.py`. Con variante B ya aprobada por
   escrito en el diseño por si estorbara a pytest o a la cobertura, para que el
   implementer no tenga que improvisar.

7. **Las respuestas de ejemplo se construyen en el test, con datos inventados**
   (`tests/utiles_ia.py`, entregable como `utiles_pdf.py` en F-002). Nada de
   JSON capturados de una llamada real: el parte lleva DNI de clientes y eso no
   entra en git ni por asomo. Los dos comandos manuales imprimen **recuentos,
   booleanos y confianzas**; en el que toca un parte real, el **único** valor
   que sale por pantalla es `numero_pagina` —un número de página no es dato
   personal, y es justo el dato que hace viable F-014—.

---

## Riesgos que el humano debe conocer

1. **El acierto real del modelo no lo mide ningún test.** La suite demuestra el
   *contrato*; la *calidad de lectura* de manuscritos con mala letra solo se
   mide contra partes reales, y hoy eso es `MANUAL (humano)` (**T18**, que
   desde la corrección C5 se ejecuta justo detrás del endpoint). Es
   exactamente lo que viene a resolver **F-015**.
2. **Coste y tiempo**: una llamada multimodal por parte, 22 partes por remesa.
   Lo absorbe la concurrencia limitada del front (F-007), no un lote mayor: la
   Function corta a los 230 s.
3. **`google-genai` es un SDK joven**. Todo lo que sabe de él cabe en un
   fichero, detrás del puerto.
4. **Datos personales en logs**: prohibido volcar el contenido del parte, la
   respuesta cruda o los valores extraídos. Está escrito como requisito (R15) y
   como riesgo, porque es el error fácil de cometer «para depurar».
5. **El parte de dos hojas sigue sin reagruparse** (F-014): si llegó partido,
   F-003 extrae dos partes incompletos. Con `numero_pagina` en el contrato,
   F-014 ya tiene con qué; aceptado por el humano el 2026-08-18 para F-002.

## Dependencias nuevas que hay que aprobar

`google-genai>=0.3`, `pyyaml>=6.0` y `tenacity>=8.2,<10.0` en
`services/postventa-api/requirements.txt` (las mismas horquillas que corren hoy
en `partes`). Ninguna más: sin OCR, sin Pillow, sin cliente HTTP propio.

## Qué NO he hecho, a propósito

- No he creado `harness/rutas_sensibles.json` (D3: es F-015).
- No he tocado `harness/features.json`: el alta de F-015 la hace el líder.
- No he tocado `progress/current.md`: lo mantiene el implementer de F-002.
- No he diseñado nada de validación, firma, persistencia, SharePoint ni Sigrid:
  R7 lo vigila con un test sobre el conjunto de claves del resultado, igual que
  R18 hizo en F-002.
- No he añadido ninguna decisión nueva al aplicar las cuatro respuestas ni las
  seis correcciones: todo ha encajado sin sorpresas, y el alcance de F-003 es el
  mismo que antes de tocarla.
- No he tocado `specs/F-002-ingesta-troceado/` ni nada bajo `services/`,
  `tests/`, `harness/`, `docs/`, `.claude/` ni `CHECKPOINTS.md` (hay otro agente
  trabajando en `chore/postreview-F-002` sobre esos ficheros), ni he ejecutado
  ningún comando de git que escriba.
- No he actualizado `azure-apps/` por el cambio de modelo (C6): allí no se fija
  versión, no hay nada que contradiga, y este proyecto aún no tiene documento
  propio —lo crea F-010—.
- No he tocado `progress/explore_F-003.md`: es el informe histórico de la
  revisión que encontró estos defectos, y sus referencias a la numeración
  antigua (T20) describen la spec **tal y como estaba** cuando se escribió.
