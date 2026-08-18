<!-- progress/current.md -->
# Sesión activa

> **Cierre de la sesión del 2026-08-18/19.** Este fichero es autosuficiente:
> una sesión limpia puede retomar leyendo `CLAUDE.md`, este documento y, si
> hace falta el detalle, los informes que se citan. No hay que releer el
> proyecto entero.

**F-003 · Extracción multimodal del parte, manuscritos incluidos** — estado
`in_progress`, rama `feature/F-003-extraccion`, rigor `critico`.
**Implementada, revisión APROBADA, y a falta de UNA comprobación del humano.**

## Lo primero que hay que hacer mañana

Ejecutar el barrido de la remesa entera (22 llamadas a Gemini, un par de
minutos, coste ridículo) y pegar el resumen:

```powershell
& "C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\.venv\Scripts\python.exe" $HOME\f3_real.py todos
```

Con ese resultado se cierra F-003 (`done`), se anota el resumen en
`progress/history.md` y se pasa a F-004.

**Qué responde ese barrido, y por qué importa más que cerrar la feature**: si
Gemini lee o no la letra manuscrita de estos escaneos. Es la premisa del
proyecto. Además da dos datos que necesitan features posteriores: cuántos
partes de una remesa real llevan observaciones (**F-004** lo necesita para
decidir qué es «conforme») y la línea base de acierto que **F-015** convertirá
en umbral.

Si `observaciones` sale en 0 de 22, **no está claro que sea un fallo**: puede
que el papel esté en blanco. Lo distingue el humano mirando un parte que sepa
que lleva algo escrito a mano, y pasando su índice: `f3_real.py 7`.

## Estado real de las dos verificaciones MANUAL

| Tarea | Estado | Resultado real |
|---|---|---|
| **Paso 0** · el identificador del modelo existe | **HECHA** 2026-08-19 | `GEMINI_MODEL = gemini-3.7-flash`, `reconocido: True` |
| **T17** · humo con parte sintético | **HECHA** 2026-08-19 | **Correcta.** Nueve claves, traza `gemini` / `gemini-3.7-flash` / `parte_posventa_es` v1 huella `2306ac1d07f1`; `codigo_obra = 0677` y `numero_incidencia = RS26.08/0001` con confianza 99; `numero_pagina = "1"`; sin avisos |
| **T18** · parte real de Mirasierra | **HECHA A MEDIAS** | Solo el parte 0 de 22. Los cinco campos impresos vinieron con **confianza 100** y `numero_pagina = "1"`, sin avisos. Los tres manuscritos, vacíos con confianza 0 |

**Por qué T18 no basta todavía**: ese parte traía los tres manuscritos en
blanco, así que no distingue «el papel no tiene nada escrito» de «el modelo no
lee la letra». De ahí el barrido de los 22.

**Corrección hecha al ejecutar T17** (ya aplicada en `tasks.md` con su nota):
el resultado esperado decía `numero_incidencia = RS26.08/0123` y es
`RS26.08/0001`. `remesa_sintetica()` numera correlativo
(`tests/utiles_pdf.py:121`); el `0123` es el valor por defecto de
`pagina_de_parte()` (`:43`), que es otra función y vale como ejemplo del papel,
no como resultado de la verificación. **El modelo leyó bien**: el error estaba
en la expectativa escrita.

## Los scripts de las verificaciones manuales

Viven **fuera del repositorio**, en el home del humano, porque no estaban en la
spec y porque PowerShell parte los comandos largos al pegarlos:

- `C:\Users\pgris\f3_modelo.py` — confirma contra la API que el identificador
  del modelo existe. No gasta llamadas de extracción.
- `C:\Users\pgris\f3_humo.py` — T17, parte sintético. Imprime valores: son
  inventados.
- `C:\Users\pgris\f3_real.py` — T18. `f3_real.py` (solo el primero),
  `f3_real.py 0 7 15` (esos) o `f3_real.py todos` (los 22 con resumen
  agregado). Imprime «vino / no vino» y confianza; el único valor que muestra
  es `numero_pagina`, que no es dato personal.

Los tres avisan y paran si falta el `.env`, si la clave sigue con el
placeholder o si no encuentran el PDF. El equivalente en comandos sueltos está
en `specs/F-003-extraccion/tasks.md`, T17 y T18.

**El `.env` ya existe** en `services/postventa-api/` con la credencial real. No
se versiona y ningún agente lo toca.

## Qué hay hecho en F-003 (verificado, no declarado)

`progress/impl_F-003.md` y `progress/review_F-003.md`.

- **207 tests** en el servicio (112 de F-003) y 16 en la raíz.
- **Cobertura de lo cambiado: 100 %** (631/631, umbral 80 %), sin ficheros «no
  medidos».
- **Mutación: 127 generados, 127 muertos, 0 supervivientes.** El reviewer
  **reejecutó la campaña entera** (101,0 s, mismos totales, salida fuera de
  `progress/`, árbol limpio) estrenando la exigencia del arnés 1.5.2.
- Buscados activamente y sin hallazgos: datos personales o respuesta cruda del
  modelo en logs, fixtures o informes; credenciales en el repositorio; ganchos
  preparando F-014; campos de otras features en la respuesta.

La lección de su campaña de mutación, que vale para cualquier feature: un test
que se parametriza con **la propia constante que vigila** no vigila nada — al
borrarse el valor de la constante desaparece también el caso de prueba y la
campaña aplaude el cambio. Pasó con los códigos HTTP transitorios y se arregló
escribiéndolos a mano.

## Observación abierta de la sesión

**El SDK avisa en cada llamada real**: «Direct use of automatic function
calling (AFC) in `Models.generate_content` is not recommended». No rompe nada
—los resultados son correctos— pero sugiere que el schema se pasa de una forma
que activa la llamada automática de funciones. Merece una revisión del
adaptador (`infrastructure/llm/gemini.py`) después de cerrar F-003. No bloquea.

## Cadena de ramas (el merge es del humano, sigue pendiente)

```
dev
 └── feature/F-002-ingesta-troceado      (F-002 cerrada y aprobada)
      └── chore/postreview-F-002         (3 decisiones de la review + arnés 1.5.2)
           └── feature/F-003-extraccion  (aquí estamos)
```

Cada rama sale de la anterior porque depende de su código. Se mergean **en ese
orden**, o directamente la última cuando todo esté cerrado. **Ningún agente
hace `push` ni PR.**

## Decisiones del humano vigentes sobre F-003

- **`numero_pagina`** entra en el contrato: F-003 lo lee y lo devuelve; **no
  reagrupa nada** (eso es F-014, con test que lo vigila).
- El endpoint **`POST /api/extraer`** entra en F-003.
- Los campos se llaman **`unidad`** y **`fecha_servicio`** (el papel imprime
  «Vivienda»; el backlog decía «chalet»). `docs/ARCHITECTURE.md` ya alineado.
- El modelo es **`gemini-3.7-flash`**. `azure-apps` documenta el proveedor pero
  **no fija versión**: ninguna afirmación puede decir qué versión corre en otro
  proyecto del ecosistema.
- **Dependencias aprobadas** e instaladas: `google-genai>=0.3`, `pyyaml>=6.0`,
  `tenacity>=8.2,<10.0`.
- La ruta sensible de `config/prompts.yaml` no se declara aún: hace falta antes
  el evaluador, que es **F-015**.

## Pendiente del humano (cola de decisiones)

1. **El barrido de los 22 partes** (arriba). Bloquea el cierre de F-003.
2. **Merge de la cadena de ramas** a `dev`.
3. **Tres propuestas de automejora** que dejó la review de F-003, ninguna
   aplicada:
   - **P1** · que la campaña de mutación use la base real de la rama. Con la
     cadena actual, el alcance de mutación arrastró 27 ficheros y 1912 líneas
     (incluido `harness/mutacion.py`, 32 de los 127 mutantes) mientras la
     cobertura medía 631. No es un defecto —el alcance es más ancho, nunca más
     estrecho— pero los números no son comparables entre features. Propuesta:
     campo `base` en `harness/features.json`, usado por `harness.cobertura` y
     `harness.mutacion`.
   - **P2** · que `CHECKPOINTS.md` C5 contemple las tareas `MANUAL (humano)`
     pendientes: hoy exige todas `[x]` y una feature `critico` está obligada a
     tener verificaciones que ningún agente puede ejecutar. **Genérica: iría a
     `arnes-base`.**
   - **P3** · que C4 bis nombre la comprobación de «no medido» en la cobertura.
     **Genérica: iría a `arnes-base`.**
4. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   (componer un PDF) frente a PyMuPDF (manipular uno de entrada) debe subir a
   `arnes-base` en su propia versión. Es el único fichero donde este
   repositorio adelanta al arnés genérico.

## Siguiente feature, cuando F-003 cierre

**F-004 · Validación del parte y clasificación de la firma** (prioridad 4,
`sdd: true`, rigor `critico`, `pending`). Consumirá los nueve campos y sus
confianzas que produce F-003. Dos hallazgos de dominio mandan sobre su diseño,
y están en `docs/ARCHITECTURE.md` y `docs/referencia/`:

- «Cerrar parte» de Sigrid **exige documento adjunto**.
- Un parte firmado **con observaciones manuscritas no es un parte conforme**.
  Por eso el recuento de `observaciones` del barrido es material de diseño para
  F-004, no una curiosidad.

## Contexto del proyecto y del arnés

- **Arnés 1.5.2**, verificado contra el payload de `arnes-base` fichero a
  fichero: 32 comparados, ninguna divergencia inesperada. La campaña de
  mutación conserva el análisis de supervivientes al repetirse, y el reviewer
  la reejecuta cuando declara menos de 5 minutos.
- `BACKLOG.md` se genera desde `harness/features.json` y lo regenera
  `bash harness/init.sh`: **no se edita a mano**.
- **Backlog: 15 features.** F-001 y F-002 `done`; F-003 `in_progress`; F-014
  (reagrupar el parte de dos hojas con el «Página N») y F-015 (evaluación del
  prompt) nacieron en esta sesión.
- Los agentes del arnés (`spec-author`, `implementer`, `reviewer`) están
  cargados: **se delega**, el líder orquesta y no implementa.

### Dos lecciones operativas de esta sesión

1. **Dos agentes a la vez en la misma rama se pisan en el índice de git.** Un
   `git add -A` de uno arrastró al commit el trabajo del otro (commit
   `3211984`, que se quedó como está: rehacer el historial de una rama ya
   revisada costaba más que documentarlo). Si se vuelve a paralelizar: el
   segundo agente no toca git y commitea el líder, o se aísla en otra rama.
2. **El humano trabaja en PowerShell.** No admite `&&`, y al pegar comandos
   multilínea con Python en `-c` los indenta y revientan con `IndentationError`;
   las líneas muy largas se parten al pegarse. Para cualquier verificación
   manual: **un script en el home y una línea corta para invocarlo**, nunca un
   comando largo de Bash.
