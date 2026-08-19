<!-- progress/spec_F-003.md -->
# F-003 · Informe del spec-author

**Fecha**: 2026-08-18 · **Feature**: F-003 «Extracción multimodal del parte,
manuscritos incluidos» · **Rigor**: `critico` · **Estado**: spec redactada y
**actualizada con las cuatro decisiones del humano** (2026-08-18). No queda
ninguna decisión abierta.

**Entregable**:

- `specs/F-003-extraccion/requirements.md` — 20 requisitos EARS (R1–R19 más
  **R2 bis**) con tabla de trazabilidad requisito → nombre de test.
- `specs/F-003-extraccion/design.md` — diseño técnico, 12 secciones.
- `specs/F-003-extraccion/tasks.md` — **21 tareas** atómicas, 9 de ellas con
  fase RED, **ninguna condicional**.

No se ha escrito ni una línea de código de producción, ni se ha tocado nada
bajo `services/`, `tests/`, `harness/`, `specs/F-002-ingesta-troceado/` ni
`progress/current.md` (F-002 seguía en curso en la misma rama).

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

La verificación `MANUAL (humano)` **T20** se queda como estaba: es lo que tapa
el hueco mientras F-015 no exista.

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
   mide contra partes reales, y hoy eso es `MANUAL (humano)` (T20). Es
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
- No he añadido ninguna decisión nueva al aplicar las cuatro respuestas: todo
  ha encajado sin sorpresas.
- No he tocado `specs/F-002-ingesta-troceado/` ni nada bajo `services/` o
  `tests/`.
