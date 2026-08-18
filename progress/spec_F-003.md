<!-- progress/spec_F-003.md -->
# F-003 · Informe del spec-author

**Fecha**: 2026-08-18 · **Feature**: F-003 «Extracción multimodal del parte,
manuscritos incluidos» · **Rigor**: `critico` · **Estado**: spec redactada,
pendiente de aprobación del humano.

**Entregable**:

- `specs/F-003-extraccion/requirements.md` — 19 requisitos EARS con tabla de
  trazabilidad requisito → nombre de test.
- `specs/F-003-extraccion/design.md` — diseño técnico, 12 secciones.
- `specs/F-003-extraccion/tasks.md` — 20 tareas atómicas, 8 de ellas RED.

No se ha escrito ni una línea de código de producción, ni se ha tocado nada
bajo `services/`, `tests/`, `harness/`, `specs/F-002-ingesta-troceado/` ni
`progress/current.md` (F-002 estaba en curso en la misma rama).

---

## Lo que se ha decidido, y por qué

1. **Se reutiliza el patrón de IA que ya corre en producción**, consultado en
   `azure-apps/partes.md` §3.2 y §5 y `azure-apps/albaranes.md` §3 antes de
   diseñar: SDK `google-genai`, prompt en YAML con clave + schema estructurado,
   y trazabilidad guardada con el dato (`proveedor`, `modelo`, `prompt_key`,
   `confianza_pct`). Mismos nombres de variables (`IA_PROVIDER`,
   `GEMINI_API_KEY`, `GEMINI_MODEL`, `PROMPT_KEY`, `PROMPTS_YAML_PATH`). No se
   ha copiado ningún documento de `azure-apps` a este repositorio.

2. **Ocho campos y una confianza entera 0–100 por campo**, incluidos los tres
   manuscritos (`fecha_servicio`, `dni_cliente`, `observaciones`). La escala
   0–100 y el nombre `confianza_pct` son los del ecosistema, no una invención.

3. **El resultado trae siempre las ocho claves**, aunque el parte las deje en
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
   entra en git ni por asomo. Los dos comandos manuales están escritos para
   imprimir **recuentos, booleanos y confianzas**, nunca valores extraídos, en
   el que toca un parte real.

---

## Decisiones abiertas que necesita validar el humano

### D1 · ¿Entra `numero_pagina` en el contrato de F-003? (para F-014)

F-014 («reagrupar el parte de dos hojas») necesita el «Página N» del pie, y el
modelo multimodal **sí lo ve** aunque el escaneo no tenga capa de texto — que es
justo lo que F-002 no pudo leer. Sería un noveno campo `numero_pagina`
(`"1"` / `"2"` / `null`).

- **Coste si entra**: una línea en el prompt, una entrada en `CAMPOS_DEL_PARTE`,
  un test. Se añade como `R2 bis` y una tarea entre T5 y T6.
- **Coste si no entra**: F-014 tendrá que ampliar el contrato de extracción
  cuando le toque (cambio aditivo, sin romper nada).

**No lo he dado por hecho** porque la restricción del líder lo prohíbe
expresamente. **Mi recomendación: que entre.** El campo no cuesta nada ahora,
la lectura la hace el modelo igualmente, y si no entra, F-014 arrancará
modificando el contrato de una feature ya cerrada.

### D2 · ¿Entra el endpoint `POST /api/extraer` en F-003?

Los cinco criterios `acceptance` no lo piden. Pero `docs/ARCHITECTURE.md`
define el contrato HTTP como «`/split` rápido y luego **una llamada por
parte**», y sin endpoint la extracción no la puede ejercitar nadie: ni el front
(F-007), ni las verificaciones manuales T18/T19.

**El diseño lo incluye** (R17, R18, T14, T15). Si el humano prefiere dejarlo
para F-004, se caen esos dos requisitos, esas dos tareas y el fichero
`interface_adapters/api/extraer.py`; el resto del diseño no cambia. **Mi
recomendación: que entre**, porque sin él la feature no se puede probar contra
la realidad y el rigor `critico` exige verificaciones manuales con resultado
real.

### D3 · `harness/rutas_sensibles.json` para `config/prompts.yaml`

Este repositorio **no** tiene `harness/rutas_sensibles.json`, así que hoy el
bloque C4 ter de `CHECKPOINTS.md` es N/A. Y `config/prompts.yaml` es
exactamente el caso de manual del mecanismo: **ningún test unitario detecta que
un cambio de redacción del prompt empeore la extracción**, porque el modelo está
simulado y la suite seguiría verde con el prompt roto.

**Recomendación: sí declararlo, pero no en F-003.** La declaración exige un
`comando` que produzca el informe, y ese comando **no existe**: haría falta un
evaluador del prompt (juego de partes de prueba, llamada real con credencial,
umbral de acierto, informe con `VEREDICTO: VERDE`). Declarar hoy una
verificación que nadie puede ejecutar sería protección falsa, que es justo lo
que el propio ejemplo del arnés advierte.

**Propuesta concreta al humano**: abrir una feature nueva —«evaluación del
prompt contra partes reales»— y declarar `rutas_sensibles.json` cuando el
comando exista. Y ojo con dónde vive: ese evaluador **sería genérico** (valdría
igual para `partes` y `albaranes`), así que por la regla de propagación su sitio
natural es **`arnes-base`**, no este repositorio. Mientras tanto, F-003 tapa el
hueco con la verificación `MANUAL (humano)` T19, que es la misma comprobación
hecha a mano. El borrador del JSON está escrito en `design.md` §9 (D3).

### D4 · Nombres de dos campos

La descripción de la feature dice «chalet» y «fecha»; el papel impreso dice
**«Vivienda»** y **«Fecha servicio»** (`docs/referencia/02_parte_de_trabajo.md`).
He nombrado los campos `vivienda` y `fecha_servicio`, para que nadie tenga que
traducir entre el código y el documento que tiene delante, y lo he dejado
escrito en la tabla de R1. **Si el humano prefiere `chalet`, es un renombrado
de una línea**, mejor hacerlo antes de implementar que después de F-005.

---

## Riesgos que el humano debe conocer

1. **El acierto real del modelo no lo mide ningún test.** La suite demuestra el
   *contrato*; la *calidad de lectura* de manuscritos con mala letra solo se
   mide contra partes reales, y hoy eso es `MANUAL (humano)`. Es el argumento
   fuerte a favor de D3.
2. **Coste y tiempo**: una llamada multimodal por parte, 22 partes por remesa.
   Lo absorbe la concurrencia limitada del front (F-007), no un lote mayor: la
   Function corta a los 230 s.
3. **`google-genai` es un SDK joven**. Todo lo que sabe de él cabe en un
   fichero, detrás del puerto.
4. **Datos personales en logs**: prohibido volcar el contenido del parte, la
   respuesta cruda o los valores extraídos. Está escrito como requisito (R15) y
   como riesgo, porque es el error fácil de cometer «para depurar».
5. **El parte de dos hojas sigue sin reagruparse** (F-014): si llegó partido,
   F-003 extrae dos partes incompletos. Aceptado por el humano el 2026-08-18
   para F-002; aquí solo consta.

## Dependencias nuevas que hay que aprobar

`google-genai>=0.3`, `pyyaml>=6.0` y `tenacity>=8.2,<10.0` en
`services/postventa-api/requirements.txt` (las mismas horquillas que corren hoy
en `partes`). Ninguna más: sin OCR, sin Pillow, sin cliente HTTP propio.

## Qué NO he hecho, a propósito

- No he creado `harness/rutas_sensibles.json` (D3).
- No he tocado `progress/current.md`: lo mantiene el implementer de F-002.
- No he diseñado nada de validación, firma, persistencia, SharePoint ni Sigrid:
  R7 lo vigila con un test sobre el conjunto de claves del resultado, igual que
  R18 hizo en F-002.
- No he tocado `specs/F-002-ingesta-troceado/` ni nada bajo `services/` o
  `tests/`.
