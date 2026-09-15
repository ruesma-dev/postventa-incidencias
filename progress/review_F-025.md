<!-- progress/review_F-025.md -->
# F-025 · Archivar y cerrar en una sola confirmación — review

**Veredicto: RECHAZADO** (CHANGES_REQUESTED)

> **Léase esto antes que la lista de reparos.** El trabajo es bueno y la
> premisa que sostiene la feature **es cierta**: la he verificado yo en el
> código, no me la he creído del informe. Las enmiendas a F-009 y F-012 son
> ejemplares. El backend no ha cambiado ni una línea. Los tests nuevos son
> exigentes de verdad, y lo he medido mutando el JavaScript a mano.
>
> Lo que lo rechaza son **tres reparos concretos y baratos**, y uno de ellos
> es serio: el único requisito que la propia spec designa como contrapeso del
> riesgo aceptado en su §0 —R37, enseñar el número de incidencia sobre el que
> se escribió— tiene un test de control negativo que **no ejecuta la función
> que dice vigilar**. En una feature `critico` que escribe en un ERP de
> producción sin pantalla previa, eso no se aprueba: se arregla.

Revisado el 2026-09-11 sobre `feature/F-025-confirmacion-unica`, diff
`941a673..HEAD` (13 commits, 19 ficheros, +4.616/−579). La rama nace de la de
F-012, ya cerrada, y no se ha reabierto.

---

## 1 · Nivel de rigor y puertas que exige

`harness/features.json` declara **`rigor: "critico"`** para F-025. Según
`harness/rigor.json`, eso exige: fase RED, cobertura de las líneas cambiadas
≥ 80 %, campaña de mutación y **cero supervivientes** salvo justificación
escrita aceptada por el humano, más las verificaciones `MANUAL (humano)` con
su comando exacto y su resultado real.

| Puerta | Estado | Evidencia |
|---|---|---|
| `bash harness/init.sh` | **[OK]** | exit 0; 62 + 2.144 (13 skipped) + 185 tests; ruff con 58 avisos de deuda previa, que no bloquean |
| Cobertura de líneas cambiadas | **[OK]** | `PUERTA COBERTURA: 99,0 % de 1.079 líneas cambiadas cubiertas (1.068/1.079, umbral 80 %, nivel critico)` |
| Fase RED | **[OK]** | trazas reales pegadas en el informe, §4.1, §4.2, §15 y §23 |
| Mutación | **N/A justificado** | ver §2, que es la sección larga de esta review |

---

## 2 · La puerta de mutación: por qué el cero es legítimo y qué lo sustituye

La campaña (`progress/mutacion_F-025.md`) declara **0 mutantes, 0 líneas de
producción en el alcance, 0,0 s, 1 worker**. Un cero así no es una puerta
superada: es una campaña que no midió nada. Lo he tratado como tal.

### 2.1 · Recálculo independiente

```
python -c "from harness import alcance; alcance.alcance_de_feature(
  'F-025', base='941a673…', rama='feature/F-025-confirmacion-unica')"
→ Alcance(feature='F-025', origen='rama', lineas={})
```

Coincide con el informe: cero ficheros, cero líneas.

### 2.2 · Reejecución completa (el «Tiempo total» era 0,0 s < 5 min)

Relanzada con `python -m harness.mutacion --feature F-025 --base 941a673… --workers 1 --salida <scratchpad>` —**fuera de `progress/`**, para no pisar
el informe del implementer—. Totales idénticos: 0 mutantes, 0 evaluados,
0 muertos, 0 supervivientes, 0 timeouts. `git status` queda limpio después.

### 2.3 · La prueba de control: ¿el cero viene del alcance o de una avería?

Es la comprobación que distingue «no había nada que mutar» de «el generador
está roto o el informe es falso», porque los dos dan 0. He ejecutado
`harness.mutacion.generar_mutantes` sobre los ficheros del diff **ignorando
la exclusión de alcance**:

| Fichero `.py` del diff | Mutantes ignorando la exclusión |
|---|---|
| `services/postventa-api/tests/test_f025_documentacion.py` | 2 |
| `services/postventa-api/tests/test_f025_sin_dry_run_previo.py` | 80 |
| `services/postventa-front/tests/test_f009_front.py` | 3 |
| `services/postventa-front/tests/test_f012_front.py` | 3 |
| `services/postventa-front/tests/test_f025_front.py` | 10 |
| **Total** | **98** |

**El motor funciona.** El cero es legítimo y la razón es estructural: los
**cinco** ficheros `.py` del diff viven bajo `tests/`, que
`harness/alcance.py::es_produccion` excluye por diseño
(`DIRECTORIOS_EXCLUIDOS = ('tests','specs','progress','docs','harness')`).
Y lo confirmo de forma independiente: `git diff --stat 941a673..HEAD` sobre
`domain/`, `application/`, `infrastructure/`, `interface_adapters/` y
`config/` de `postventa-api` sale **vacío**. F-025 no cambia **ni una línea
de Python de producción**: todo es JavaScript, HTML, tests, specs y
documentación.

**N/A JUSTIFICADO**, y el motivo por escrito es este: *el entregable de F-025
no es Python de producción, y `harness.mutacion` solo muta Python.* No es
«no se lanzó la herramienta».

### 2.4 · Qué sustituye a la mutación aquí, y si es suficiente

Tres cosas, y **las he ejecutado yo, no leído**:

1. **`tests_js/circuito.test.js`** — 37 tests, `node --test`, en verde
   (224 en todo `tests_js/`).
2. **Los tests de pantalla** — `test_f025_front.py` (38), más
   `test_f009_front.py` y `test_f012_front.py` adaptados: 98 en verde.
3. **El control negativo del backend** — `test_f025_sin_dry_run_previo.py`
   (27) y `test_f025_documentacion.py` (21): 48 en verde.

«Muchos» no es «exigentes», así que **he hecho a mano la campaña de mutación
que la herramienta no puede hacer**: catorce mutaciones dirigidas sobre
`js/pipeline.js`, en una copia aislada del scratchpad, contando los tests que
caían con cada una.

| # | Mutación | Tests que caen |
|---|---|---|
| M0 | control, sin mutar | 0 |
| M1 | `commit: true` → `false` en las credenciales del ERP | **3** |
| M2 | `confirmado: true` → `false` | **2** |
| M3 | quitar el `return` tras fallo de archivar | **4** |
| M4 | no saltarse `archivar` aunque ya conste archivado (R25) | **2** |
| M5 | no saltarse `adjuntar` aunque ya conste adjuntado (R26) | **2** |
| M6 | ignorar la bandera `erpCerrado` (R21) | **1** |
| M7 | cerrar aunque el adjuntado no respondiera `adjuntado` (R18/R27) | **1** |
| M8 | la guarda de reentrada deja de guardar (R14) | **1** |
| M9 | `porcentajeDeTanda` sin la guarda del cero (R12) | **1** |
| M10 | `pendientesDeCircuito` deja de filtrar por aptitud (R36) | **1** |
| M11 | un cierre fallido se marca `error_cierre` en vez de `adjuntado` (R19) | **2** |
| M12 | el ámbito del 503 de archivar pasa a `erp` (R22) | **1** |
| M13 | no se anuncia el paso `adjuntando` (R13) | **2** |
| M14 | `numeroDeIncidenciaDe` **se inventa** un número (R37) | **0 ← SUPERVIVIENTE** |

**13 de 14 muertos.** Los tests del circuito son exigentes de verdad: cazan
el orden, el número de llamadas, el `commit`, los saltos de idempotencia, las
dos puertas de entorno y la guarda de reentrada. **Un superviviente**, y es
el reparo 1 de §4.

Este caso es exactamente el que describe el **encargo 1.7.12 pendiente en
`arnes-base`** sobre la puerta de mutación cuando el entregable no es Python:
la herramienta declara N/A con su motivo, el nivel de rigor sigue exigiendo
fase RED y evidencias, pero **nadie mide si los tests del entregable real son
exigentes**. Aquí lo he suplido a mano. Que haga falta suplirlo a mano es el
argumento de ese encargo.

---

## 3 · La premisa que hace segura la feature: verificada en el código

Es lo que había que comprobar antes de apoyarse en ello, porque si no se
sostiene la feature escribe a ciegas. **Se sostiene.**

**`application/pipelines/paso_grafico.py::paso_grafico` con `commit=True`**,
en una sola invocación y por este orden (líneas 149–249):

`_exigir_apto` → `_exigir_archivado` → `validar_fichero` →
`consultar_grafico` (traza local) → `resolver_login_de_sigrid` (verifica el
login **contra el ERP**) → **`erp.leer_reclamacion`** → `evaluar` →
`componer_peticion` → **`_dry_run` → `graficos.adjuntar(peticion, commit=False)`**
→ traza `dry_run_ok` → `if not commit: return` → `exigir_autorizacion_para_escribir`
→ `_escribir` → `graficos.adjuntar(commit=True)` → `_exigir_colgado`.

El `if not commit: return` está en la **línea 233**, es decir **después** del
dry-run, no antes. Un `commit` que llega sin ninguna llamada previa hace su
lectura y su comprobación él mismo.

**`paso_cierre.py::paso_cierre` con `commit=True`** (líneas 144–197):

`_exigir_apto` → `_exigir_archivado` → `_codigo_de_incidencia` →
`resolver_login_de_sigrid` → **`_dry_run` = `erp.leer_reclamacion` + `evaluar`**
(línea 296) → traza `dry_run_ok` → `consultar_grafico` →
`if not commit: return` (línea 181) → `_exigir_adjuntado` →
`exigir_autorizacion_para_escribir` → `_escribir` → `erp.cerrar(plan=plan)`.

**El plan que va al `WHERE` del `UPDATE` es el que se acaba de leer en esa
misma llamada** (`plan` sale de `_dry_run` y entra en `erp.cerrar`), con
`estado_origen_cod` resuelto en `infrastructure/sigrid/consultas.py:203`. R11
y R23 de F-009 se cumplen mejor que antes: ya no hay ~29 s de persona leyendo
una pantalla entre la lectura y la escritura.

No hay estado compartido entre peticiones HTTP. Las dos llamadas que F-025
elimina no aportaban nada al `commit`.

Y lo vigila un test que no se puede falsear: `test_f025_r10_adjuntar_con_commit_hace_su_dry_run_en_la_misma_llamada`
afirma la bitácora **exacta y ordenada** `['erp.leer_reclamacion',
'pasarela.adjuntar(commit=False)', 'pasarela.adjuntar(commit=True)']`, con
dobles construidos y usados una sola vez. La fase RED del informe (§4.1)
enseña la traza real de ese test **cayendo** cuando se rompe el dry-run
interno en una copia aislada.

---

## 4 · Hallazgos por severidad

### ALTA — ninguno

Ningún hallazgo que ponga en riesgo el ERP, los datos personales o la
arquitectura.

### MEDIA — los tres reparos que rechazan el cierre

**1. R37 tiene un control negativo que no ejecuta lo que dice vigilar.**
`services/postventa-front/js/pipeline.js:~672` (`numeroDeIncidenciaDe`) puede
mutarse para **inventarse** un número de incidencia y **ningún test cae**
(M14 de §2.4). El culpable es el test que precisamente lleva ese nombre:

`services/postventa-front/tests_js/circuito.test.js:463`
`test("R37 · si el backend no lo devolvió, no se inventa")` hace fallar
**`archivar`**, así que el circuito se corta en el paso 1 y
`numeroDeIncidenciaDe` **no llega a ejecutarse nunca**. Los otros dos tests
de R37 (líneas 444 y 455) sí la ejecutan, pero siempre con un backend que
**sí** devuelve `numero_incidencia`: en todo el fichero no hay un solo doble
que responda con éxito y sin esa clave (`RESPUESTA_OK` la trae siempre, y los
nueve guiones que la sobrescriben o la traen o son fallos).

Por qué no es un detalle: **R37 es, por escrito, la única compensación del
riesgo que §0 de `requirements.md` acepta a propósito** —que la IA lea mal el
número, la reclamación equivocada exista y esté abierta, y el sistema la
cierre sin que nadie lo haya visto—. La spec lo dice: «la primera y única
ocasión en que quien pulsó puede detectar que se escribió sobre la incidencia
equivocada». Un número inventado en ese resumen no compensa nada: engaña.

*Arreglo:* un test en `circuito.test.js` con
`apiDoble({ adjuntar: { estado: "adjuntado" }, cerrar: { estado: "cerrado" } })`
—respuestas de éxito **sin** `numero_incidencia`— que afirme
`resultado.numeroIncidencia === ""`. Y renombrar o rehacer el de la línea 463,
que hoy prueba otra cosa de la que dice.

**2. Siete requisitos sin test trazable, y la spec no los exime.**
C4 exige `>= 1 test trazable` por requisito EARS. La tabla «Trazabilidad de
los requisitos que no llevan test unitario» de `requirements.md` exime solo a
R7 (e2e), R29–R34 (en su ejecución real), R21, R22 y R37 (en su valor real).
Fuera de esa lista se quedan sin ningún test que los nombre:

| Requisito | Qué dice | Cobertura real que sí he encontrado |
|---|---|---|
| **R3** | sin confirmación no se escribe nada | `tests_js/confirmacion.test.js:20` («sin armar, un solo clic NO dispara nada») + `confirmarArchivo` corta en `if (!decision.dispara)` + `exigir_autorizacion_para_escribir` en el backend |
| **R15** | el segundo clic no dispara una segunda tanda | `confirmacion.test.js:37` («tras disparar, queda desarmada») + `test_f025_r14_la_tanda_pasa_por_la_guarda_de_reentrada` |
| **R23** | no se reintenta por cuenta propia | `circuito.test.js:247` («son TRES llamadas y ni una más») — indirecto |
| **R28** | ni un segundo gráfico ni una segunda fila de `dbo.log` | `test_f025_r31_si_la_pasarela_dice_que_ya_cuelga_no_se_duplica` + R25/R26 — indirecto |
| **R44** | R19–R22 de F-007 vigentes, R19 es la única confirmación | `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` + suite de F-007 en verde |
| **R45** | los cuerpos son exactamente los ya definidos | los compositores `cuerpoDeArchivo/Grafico/Cierre` no se han tocado; sus tests de F-007/F-009/F-012 siguen en verde |
| **R48** | `azure-apps/` no se toca | verificado por mí: `git -C azure-apps status` **limpio** — pero es un repaso, no un test, y `tasks.md` T18 lo declara así |

**Ninguno es un agujero de verificación**: los siete están cubiertos de hecho,
y lo dejo trazado arriba. Lo que falta es la trazabilidad nominal que la
propia spec promete al no exonerarlos. *Arreglo:* o se les pone su
`test_f025_rN_*` (R3, R15, R23 y R28 son baratos), o **se añaden a la tabla de
exenciones de `requirements.md` diciendo qué los cubre**. Las dos salidas
valen; dejarlo como está, no.

**3. Comentario derogado vivo en el código.**
`services/postventa-front/js/api.js:445` sigue diciendo que el bloque del
gráfico «hay que enseñarlo **antes**» de confirmar. Ese «antes» es justo lo
que R40 de F-025 enmienda y lo que los cinco recuadros de F-012 declaran
caído. No afecta al comportamiento, pero es la clase de texto que hace que
dentro de seis meses alguien «arregle» el front para reponer una pantalla
derogada — exactamente el daño que las enmiendas de T14/T15 vienen a evitar.
*Arreglo:* una línea.

### LEVE — para tener a la vista, no bloquean

4. **`AVISO_CADUCADA_CIERRE` y `avisoCaducada()` se quedan sin llamante** en
   producción (solo los usan sus propios tests). **Declarado a propósito** en
   §24.5 del informe, con su motivo: `design.md` §9.3 deja `confirmacion.js`
   fuera del alcance. Deuda menor aceptada; lo apunto para que no se pierda.
5. **`reintentarCierre` reinicia el estado de la tanda anterior.**
   `js/app.js:574` llama a `_lanzarTanda([parte])`, que pone a cero
   `terminados`, `totalTanda`, `entornoNoArchiva`, `entornoNoCierra`,
   `erpCerrado` y `tandaDetenida`. Si la ventana del ERP estaba cerrada, el
   aviso que acababa de salir **desaparece** al pulsar «Reintentar el cierre».
   Cosmético, y se vuelve a levantar solo.
6. **Clave duplicada en el `x-for` del resumen.** `resultadosCierre` y
   `resultadosArchivo` se pintan con `:key="resultado.hash"` y un reintento
   empuja una segunda fila con el mismo `hash`. Es preexistente —ya pasaba con
   `_cerrarUno`— pero F-025 hace el reintento más probable.
7. **El número de incidencia sale dos veces** en la fila del resumen: como
   etiqueta (R37) y dentro del mensaje `«RS…/…→ cerrado»`. Ya declarado por el
   implementer en §14.1. Lo verá Posventa.
8. **`progress/mutacion_F-025.md` está sin trackear.** Es el artefacto de T24
   y tiene que entrar en el commit de cierre del bloque 6.
9. **`progress/current.md` acumula cuatro bloques superados más la cola de
   F-012.** Van marcados «_(superado por el bloque de arriba)_» y el de
   cabecera describe el estado real, así que no lo cuento como checkbox vacío;
   pero C2 pide solo la sesión activa y esto crece en cada tanda.
10. **Commits agrupados por bloque** (`F-025 T3-T6`, `F-025 T7-T13`) frente al
    «una tarea, un commit» de C5. Justificado en §12 del informe; lo registro
    como desviación consciente, no como reparo.

### ESTRUCTURAL — no es de F-025, pero esta feature lo deja más expuesto

11. **`js/app.js` e `index.html` no se ejecutan en ninguna suite.** Los 38
    tests de `test_f025_front.py` y los adaptados de F-009/F-012 son
    aserciones sobre el **texto** de los ficheros: un `x-show` mal escrito o
    un binding a un campo inexistente no lo caza nada. Deuda vieja del front
    (F-007 §3), pero **la única pantalla que escribe en el ERP se acaba de
    reescribir entera**.
    Lo que lo mitiga, y es la decisión más acertada de la feature: el orden de
    las tres escrituras, los saltos de idempotencia y las dos puertas de
    entorno **se mudaron a `js/pipeline.js`**, que sí se ejecuta y que mi
    campaña manual mata 13 de 14 veces. En `app.js` solo queda mover estado de
    Alpine.
    He añadido mi propio control: he extraído los identificadores que
    `index.html` invoca en sus atributos Alpine y **todos existen en
    `app.js`**; `node --check` pasa sobre los ocho módulos. **Eso sigue sin
    ser abrir la pantalla**, y abrirla es lo primero del bloque 5.

---

## 5 · Lo que el encargo pedía comprobar, punto por punto

### 5.1 · El backend no ha cambiado su contrato — **CONFIRMADO**

`git diff --stat 941a673..HEAD` sobre `domain/`, `application/`,
`infrastructure/`, `interface_adapters/` y `config/` de `postventa-api`:
**vacío**. Los únicos `.py` del diff son cinco ficheros de tests. Ni
`paso_grafico.py` ni `paso_cierre.py` ni el borde se han tocado. La regla dura
de `tasks.md` se ha respetado.

### 5.2 · Las enmiendas a F-009 y F-012 — **CORRECTAS**

`git diff --numstat`: `specs/F-012-grafico-sigrid/requirements.md` **77
añadidas / 0 suprimidas**; `specs/F-009-cierre-sigrid/requirements.md` **21 /
0**. **Ningún requisito derogado se ha borrado.**

Los cinco recuadros de F-012 (bajo R21, R22, R49, R50 y R63) y la nota de
F-009 (bajo R8/R10) traen las cuatro cosas que el patrón de R28 de F-010
exige: **fecha** (`2026-09-11`), **premisa original citada literal** entre
comillas, **qué la invalidó** y **quién lo decidió, con sus palabras**
(«quiero que al darle a archivar los partes aptos me pida confirmación como
ahora…» y «no hace falta enseñar nada»).

He comprobado que **lo que afirman es cierto**, que es lo que más importa:

- «el contrato de respuesta no cambia ni una clave» (recuadros de R21 y R49)
  → cierto: el backend no se ha tocado.
- «R20 de esta misma spec sigue vigente» y el cálculo previo se ejecuta dentro
  de la llamada que escribe (recuadro de R63) → cierto, verificado en §3.
- «R21 de F-009 ya quedó derogado por R48 de F-012 el 2026-09-06»
  (nota de F-009) → **cierto**: `specs/F-012-grafico-sigrid/requirements.md:334`
  lo dice con esa fecha. F-025 lo comprueba y lo dice, no lo vuelve a derogar,
  que es lo que R42 pedía.
- «F-012 sigue `done`: esto no reabre la feature» → correcto, y así lo he
  tratado.

Una observación sin acción: quien abra **R21 de F-009 en su sitio**
(línea 154) no ve ninguna marca; la constancia de su derogación vive en R48 de
F-012 y ahora también bajo R8/R10. Es deuda de F-012, no de F-025, y F-025
hizo justo lo que su R42 le mandaba.

### 5.3 · Los tests ajenos adaptados — **NINGUNA RETIRADA SIN SUSTITUTO**

He cotejado el diff de los dos ficheros aserción por aserción:

| Retirado de `test_f009_front.py` | Sustituto |
|---|---|
| los 7 campos de la tarjeta del dry-run pintados | `test_f009_r9_derogado_la_pantalla_previa_del_dry_run_no_deja_rastro` (6 campos, `not in html`) + `test_f009_r9_derogado_el_numero_de_incidencia_solo_sale_en_el_resumen` (el séptimo, que **sí** debe estar, por R37) |
| «el botón de cerrar no aparece hasta que hay dry-run» | `test_f009_r8_derogado_el_gesto_de_mirar_antes_ya_no_existe`: ni el botón, ni «no cierra nada», ni `hayDryRun()` |
| `count(resolver) >= 2` y `avisoCaducada("cierre")` | `count(resolver) == 1` y `'avisoCaducada("cierre")' not in codigo` — **más fuerte** que el original |
| `cuerpoDeCierre(` en `app.js` | `ejecutarCircuito(` en `app.js` **y** `cuerpoDeCierre(` en `pipeline.js`: el control se muda con la lógica |

| Retirado de `test_f012_front.py` | Sustituto |
|---|---|
| R63 · orden de los dos dry-run | `test_f012_r63_derogado_no_queda_ningun_camino_de_pantalla_previa` (parametrizado) |
| R63 · la tarjeta enseña gráfico y cierre juntos | `test_f012_r63_derogado_la_tarjeta_del_calculo_previo_no_existe` |
| R21 · la tarjeta pinta los campos | `test_f012_r21_la_tarjeta_del_calculo_previo_ya_no_se_pinta` |
| R22 · el aviso de idempotente está | `test_f012_r22_..._ya_no_se_pinta_antes_de_confirmar` |
| R64 · orden en `app.js` (`_cerrarUno`) | mismo test, movido a `pipeline.js`: `index("api.adjuntar(") < index("api.cerrar(")` |
| R65 · los tres estados en `app.js` | `test_f012_r65_los_tres_estados_se_distinguen_en_el_circuito` |
| `count(armar) == 2` | `count(armar) == 1` + `"confirmacionCierre" not in app` |

**Cada retirada deja un control negativo en su sitio**, y varios son más
estrictos que lo que sustituyen. Las bajas netas de función son fusiones, no
desapariciones. Los 98 tests de los tres ficheros de front, en verde.

### 5.4 · Los tres avisos del implementer — **RESUELTOS COMO DICE**

1. **La bandera del ERP cerrado y los partes en vuelo.** Resuelto
   **escribiéndolo**, no silenciándolo: el comentario está en
   `js/app.js::_circuitoDeUno`, junto al parámetro, y dice el alcance exacto
   —los que aún no han arrancado sí la ven, los ya emitidos no; como mucho dos
   `503` de más—. Lo he verificado en el código y en el test
   `test_f025_r21_la_bandera_del_erp_cerrado_entra_por_parametro`. La decisión
   pura entra y sale por parámetro, así que **tiene test** (M6 mata).
2. **El botón de reintentar el cierre.** Resuelto sin código nuevo:
   `reintentarCierre` es hoy `_lanzarTanda([parte])` y el circuito se salta
   `archivar` y `adjuntar` porque constan hechos (R25/R26 — M4 y M5 matan).
   **El PDF no vuelve a viajar.** He comprobado además que el recuadro ámbar
   sigue apareciendo: tras un cierre fallido, `anotarFallo(..., ESTADO_ADJUNTADO, ...)`
   deja `parte.estado === 'adjuntado'` y `parte.cerrado === false`, y
   `cerrables()` (vía `esCerrable`: apto + archivado + número) lo incluye.
   El `:disabled` del botón se actualizó a la fase nueva.
3. **El fallo a mitad con varios partes.** Las dos puertas de entorno van al
   revés la una de la otra y así está implementado: `ambito === "archivo"` →
   `tandaDetenida = true` y la tanda para (R22); `ambito === "erp"` →
   `erpCerrado = true`, se sigue archivando y el aviso se dice **una sola vez**
   porque `entornoNoCierra` es un campo de texto, no una lista (R21). El corte
   se mira **al empezar cada parte**, que es lo correcto: cuando se levanta la
   bandera la cola ya tiene a los demás encolados. M12 mata la confusión de
   ámbitos.

### 5.5 · Datos personales y secretos — **LIMPIO**

Barrido ejecutado por mí sobre el diff completo `941a673..HEAD`, con estos
patrones: `[0-9]{8}[A-Za-z]` (DNI), IPv4, GUID de suscripción/tenant,
`password|passwd|secret|api[_-]?key|token=`, `BEGIN (RSA|PRIVATE)`,
`AccountKey`, `Bearer `, `ruesma\.es`, correos con TLD real, y códigos de
incidencia `RS2[0-9]\.[0-9]{2}/[0-9]{4}`.

- **Un solo acierto**: `RS26.09/0150` en `progress/impl_F-025.md:497`. Es el
  número de la incidencia de la verificación de F-012, **ya presente en nueve
  ficheros del repositorio antes de esta rama** (`BACKLOG.md`,
  `harness/features.json`, las tres specs de F-012, etc.). No es dato
  personal: es un identificador de expediente del ERP con precedente amplio.
  **No es un hallazgo de F-025.**
- Los correos de los tests son inventados y con TLD reservado:
  `fulanito@ejemplo.invalido`, `personainventada@ejemplo.invalido`.
- **Ningún PDF ni parte escaneado ha entrado nunca en git**, comprobado con
  `git log --all --diff-filter=A` (no solo el árbol): cero resultados.
- `js/pipeline.js` sigue sin mandar el DNI ni las observaciones al archivar
  (`CAMPOS_DE_ARCHIVO` intacto), y
  `test_f025_r46_los_textos_de_pantalla_no_llevan_datos_personales` lo fija en
  la pantalla nueva.

---

## 6 · Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0.
- [x] Existen los siete ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-025`); `F-009` está `blocked`, que es
      otro estado.
- [x] Rama actual `feature/F-025-confirmacion-unica`, nunca `main`.
- [x] `progress/current.md` describe la sesión activa. **Con la salvedad
      leve 9**: arrastra cuatro bloques marcados «superado» y la cola de
      F-012. El de cabecera es el vigente, así que no lo cuento vacío.
- [x] Toda feature `done` con su resumen en `history.md` (F-025 no es `done`
      todavía; el estado lo aplica el líder, y ha hecho bien en no tocarlo).

### C3 — El código respeta arquitectura y convenciones

- [x] Arquitectura hexagonal: **no se ha tocado ningún fichero de producción
      del backend**, así que nada puede haberla roto. El front mantiene su
      separación: `pipeline.js` decide, `app.js` mueve estado de Alpine, y hay
      un test que lo vigila (`test_f025_r7_el_orden_de_las_tres_escrituras_vive_en_el_pipeline`).
- [x] Primera línea con la ruta relativa en los once ficheros nuevos o
      tocados. Verificado uno a uno.
- [x] Sin `print()` de debug, sin TODO sin contexto, sin secretos, sin
      dependencias nuevas. (Los dos aciertos del grep eran `"XXX"` como código
      de estado falso y la palabra «TODOS».)
- [x] La unidad de trabajo es el **parte**: `ejecutarCircuito(parte, …)`,
      `pendientesDeCircuito(partes)`, `totalTanda` sobre partes.
- [x] **Nada se archiva ni se cierra sin pasar las validaciones**, y ningún
      `commit` sin confirmación explícita. *Esto merece la frase entera*: sigue
      habiendo dry-run antes de cada escritura —**dentro de la misma llamada**,
      §3— y sigue habiendo confirmación explícita, una y caducable. Lo que ha
      caído, por decisión fechada del responsable, es **enseñárselo a una
      persona**. Ver la propuesta de automejora de §8.
- [x] Lo manuscrito no se descarta / marca simple no es firma — intocado.
- [x] Firmado no es conforme — intocado.
- [x] Reprocesar no duplica: R24–R28 implementados y probados; **F-025 no
      añade ninguna capa de idempotencia ni se salta ninguna** (M4, M5 matan).
- [x] Ningún número de estado hardcodeado — `CODIGO_ESTADO_CIERRE` se sigue
      resolviendo contra `conest`; nada de esto se ha tocado.
- [x] Ningún PDF con datos personales en el historial de git.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: el diff **no toca ni un fichero de `docs/referencia/`**
(`git diff --name-only 941a673..HEAD -- docs/referencia` sale vacío). La
cláusula de apertura del bloque dice que entonces es N/A.

### C4 — La verificación es real

- [ ] **Cada requisito EARS tiene >= 1 test trazable.** **Esta es la casilla
      vacía.** R3, R15, R23, R28, R44, R45 y R48 no tienen ningún
      `test_f025_rN_*` ni figuran en la tabla de exenciones de la spec. Los
      siete están **cubiertos de hecho** y dejo el mapa en el reparo 2 de §4,
      pero la trazabilidad que C4 exige no está. Es reparo, no agujero.
- [x] Los unit tests no tocan red ni BBDD: dobles en memoria en los 27 del
      bloque 0, `apiDoble` en los 37 de JS, lectura de texto en los de
      pantalla. `test_f025_r35_la_guardia_de_red_de_la_suite_sigue_puesta` lo
      fija.
- [x] Las verificaciones `MANUAL (humano)` están listadas: bloque 5 de
      `tasks.md` (T19–T23) y `progress/current.md` §«Por dónde sigue», con sus
      reglas. **Sus comandos exactos viven en `progress/guion_bloque5_F-025.md`,
      que es T19 y todavía no existe** — pero T19 *es* la primera tarea del
      bloque 5, que el encargo declara pendiente y no reparo.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"` con valor válido.
- [x] **Fase RED**: trazas reales pegadas, no resumidas, en §4.1 (rompiendo el
      `_dry_run` interno en copia aislada: `2 failed in 0.94s`, con el diff de
      la bitácora), §4.2 (37 rojos), §15 (44 rojos sobre código real) y §23
      (17 rojos de 21). El implementer **declara por escrito** que el rojo de
      §4.2 es `is not a function` y por qué, que es el aviso honesto que un
      informe tiene que dar.
- [x] **Cobertura**: `[OK]` con porcentaje, 99,0 % sobre 1.079 líneas.
- [x] **Mutación**: existe el informe, generado por la herramienta, con
      totales **verificados por mí de forma independiente** (§2.1) —alcance
      recalculado con `harness.alcance`, coincide— y **N/A justificado por
      el lenguaje del entregable** (§2.3), con la prueba de control hecha.
- [x] **Los muertos están comprobados, no solo contados**: «Tiempo total» era
      0,0 s < 5 min, así que **reejecuté la campaña entera** a una ruta del
      scratchpad, fuera de `progress/`. Totales idénticos. `git status` limpio
      después.
- [x] **La campaña tardó lo que tenía que tardar**: con 0 mutantes el coste
      por mutante no es calculable, y no hay nada sospechoso que calcular. Lo
      que sustituye a ese control es la prueba de control de §2.3 y la campaña
      manual de §2.4.
- [x] Cero supervivientes en la campaña de la herramienta (no hubo mutantes).
      **En la mía sí hay uno** (M14) y está en el reparo 1: no lo escondo
      detrás de la N/A.
- [ ] **La sección «Evidencias» con los cuatro números.** Están los tres
      primeros (tests, cobertura, tiempo de suite) en §9, §18 y §28, y el
      cuarto —mutantes y supervivientes— **con el número de workers**, en el
      informe de mutación. Pero las tres tablas de Evidencias dicen «**No
      ejecutada**», y **la campaña sí se ejecutó** (el informe existe, con
      `--workers 1`, fechado ese mismo día). El informe del implementer se
      quedó en el bloque 4 y nadie volvió a §28 a cerrarlo. Es papeleo, pero
      es el papeleo que C4 bis pide expresamente. **Casilla vacía.**
- [x] Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A sin nada que justificar**: `harness/rutas_sensibles.json` **no existe**
en este repositorio, que es el caso mayoritario que el propio bloque describe.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]`.** T1–T18 sí. **T19–T25 siguen
      `[ ]`**: bloques 5 (responsable) y 6 (líder). Por el encargo, esto es
      **pendiente, no reparo**, y lo registro así — pero la casilla de C5 no
      se puede marcar hasta que esos bloques se cierren, y por tanto F-025 no
      se puede pasar a `done` hoy con independencia de esta review.
      Desviación menor registrada: hay commits que agrupan tareas
      (`T3-T6`, `T7-T13`) frente al «una tarea, un commit».
- [ ] **Sin artefactos sin trackear sospechosos.** `git status` muestra
      `?? progress/mutacion_F-025.md`. No es sospechoso —es el artefacto de
      T24— pero tiene que entrar en git.
- [x] `features.json` refleja el estado real: `F-025` sigue `in_progress`, que
      es lo correcto. El implementer **no lo ha tocado**, como debía.

**Resultado del recorrido: cuatro casillas vacías** (C4 trazabilidad, C4 bis
Evidencias, C5 tasks.md y C5 sin trackear). Dos son de los bloques 5 y 6, que
el encargo exime; **dos no lo son** y sostienen el veredicto junto con el
reparo 1.

---

## 7 · Cambios requeridos, en orden

1. **`services/postventa-front/tests_js/circuito.test.js`** — añadir el test
   que falta para R37: un `apiDoble` que responda **con éxito y sin**
   `numero_incidencia` en `adjuntar` y en `cerrar`, afirmando
   `resultado.numeroIncidencia === ""`. Y corregir el de la **línea 463**,
   `test("R37 · si el backend no lo devolvió, no se inventa")`, que hoy hace
   fallar `archivar` y por tanto no ejecuta `numeroDeIncidenciaDe`. Mientras
   no exista, la función se puede mutar para inventarse un número y ningún
   test cae (M14 de §2.4). Es el contrapeso del riesgo aceptado en §0 de la
   spec, así que va el primero.
2. **`specs/F-025-confirmacion-unica/requirements.md`** — cerrar la
   trazabilidad de **R3, R15, R23, R28, R44, R45 y R48**: o su
   `test_f025_rN_*` (R3, R15, R23 y R28 son de tres líneas), o una entrada en
   la tabla «Trazabilidad de los requisitos que no llevan test unitario»
   diciendo qué los cubre. El mapa de lo que ya los cubre está en el reparo 2
   de §4; no hay que buscarlo otra vez.
3. **`progress/impl_F-025.md` §28** — corregir la fila «Mutantes generados y
   supervivientes» de la tabla de Evidencias: dice «**No ejecutada**» y la
   campaña **sí se ejecutó** (`progress/mutacion_F-025.md`, `--workers 1`,
   0 mutantes, 0 líneas de producción en el alcance, N/A por el lenguaje del
   entregable). C4 bis pide los cuatro números y el nº de workers.
4. **`services/postventa-front/js/api.js:445`** — retirar el «hay que
   enseñarlo **antes**» de confirmar del comentario: lo derogó R40 de F-025 y
   contradice los cinco recuadros de F-012.
5. **`git add progress/mutacion_F-025.md`** — el artefacto de T24 tiene que
   entrar en el commit de cierre.

Nada de esto exige tocar `js/pipeline.js`, `js/app.js`, `index.html` ni el
backend. Son tres tests, dos líneas de texto y un `git add`.

---

## 8 · Lo que queda para el responsable y para el líder

**No son reparos.** Se quedan fuera de este veredicto por el encargo, y los
listo para que no se pierdan.

**Bloque 5 · `MANUAL (humano)`, del responsable** — T19–T23. Escribe en el
histórico de una **obra en uso**. Reglas que vienen de F-012 y no se negocian:
autorización expresa para la incidencia concreta, `CIERRE_HABILITADO` abierto
**solo** durante la prueba y **releído** al cerrarlo, y ninguna escritura desde
un puesto de trabajo. Empieza por **T19**, el guion
`progress/guion_bloque5_F-025.md`, que aún no existe. Lo que hay que anotar:

- que hubo **una** confirmación y no dos (R1, R2);
- que en el registro salen **exactamente tres** peticiones por parte y ninguna
  sin `commit` (R7, R8, R9);
- la **duración de `adjuntar` fusionada** frente a los 35 s de
  `SIGRID_TIMEOUT_S` y los 40 s de `TIMEOUT_PETICION_MS`; **si pasa del 60 %
  del presupuesto, se para y se lleva la decisión de P4 al humano**;
- el **tamaño en bytes del parte**, que es el número que F-012 se dejó sin
  medir;
- que el reintento **no duplica**: ni un segundo gráfico en el ERP ni una fila
  más en `dbo.log`. Es la comprobación que F-012 no llegó a hacer.

Y lo primero de todo, antes que nada de eso: **abrir la pantalla en un
navegador**. Ninguna suite la ejecuta (§4, hallazgo 11) y se acaba de
reescribir entera.

**Bloque 6 · del líder** — T24 (la campaña, ya ejecutada: queda marcar la
casilla y commitear el informe) y T25 (`init.sh` en verde, que ya lo está).

---

## 9 · Automejora propuesta (no aplicada; la decide el humano)

1. **`CHECKPOINTS.md`, C3.** El bullet dice «ningún `commit` contra Sigrid
   ocurre sin confirmación explícita: **dry-run siempre primero**». Después de
   F-025 esa frase es ambigua: un reviewer futuro puede leerla como «dry-run
   **mostrado al usuario** primero» y rechazar una feature correcta, o al
   revés, aceptar que se quite el dry-run interno porque «ya no se enseña».
   Propuesta de redacción: *«…dry-run siempre primero: la comprobación previa
   contra el ERP se ejecuta antes de toda escritura, **en la misma llamada si
   hace falta**. Que se le enseñe o no a una persona es decisión de producto;
   que se ejecute, no.»*
2. **`CHECKPOINTS.md`, C4 bis · el hueco que esta review ha tenido que tapar a
   mano.** Cuando el entregable de una feature no es Python, la puerta de
   mutación sale N/A y **nada mide si los tests del entregable real son
   exigentes**: la N/A está justificada y aun así la feature queda sin el
   control que el nivel `critico` promete. Aquí lo he suplido con catorce
   mutaciones manuales sobre `js/pipeline.js` (§2.4), y ha valido la pena:
   encontró el reparo 1. Propuesta: que C4 bis exija, cuando la campaña salga
   N/A por el lenguaje, **una campaña manual mínima del reviewer sobre el
   módulo que concentra las decisiones**, con su tabla mutación → tests que
   caen en el informe de review. Es el encargo **1.7.12 pendiente en
   `arnes-base`**, y este caso es su ejemplo de manual: conviene portarlo allí
   con esta review como prueba.
3. **`.claude/agents/reviewer.md`.** El protocolo manda reejecutar la campaña
   si tarda menos de 5 minutos, pero **no dice qué hacer cuando el informe
   declara cero mutantes por alcance vacío y el diff no tiene Python de
   producción**. La prueba de control ya está descrita; lo que falta es la
   frase que obliga a **declarar en el informe qué sustituye a la mutación**.
   Sin ella, un N/A correcto se convierte en un hueco silencioso.

---
---

# Segunda pasada · 2026-09-11

**Veredicto de esta pasada: RECHAZADO** (CHANGES_REQUESTED)

> **Léase esto antes que nada, porque el titular no es el veredicto.** El
> reparo serio —el 1, el de R37— **está resuelto de verdad**, y no me lo he
> creído del informe: he vuelto a montar la copia aislada y he mutado
> `numeroDeIncidenciaDe` de cuatro maneras distintas. **Las cuatro mueren
> ahora**, y antes de esta tanda la primera de ellas sobrevivía. El reparo 2,
> el de trazabilidad, también está cerrado, y lo he comprobado barriendo los
> 48 requisitos de la spec uno a uno, no leyendo la tabla.
>
> Lo que rechaza es **el reparo 3, que está resuelto a medias**: se retiró el
> comentario derogado que cité por número de línea, y **su gemelo literal
> sigue vivo 26 líneas más arriba, en el mismo fichero**, diciendo exactamente
> lo mismo que R40 deroga. Mi reparo era sobre la afirmación, no sobre la
> línea. Y, al ir a comprobarlo, aparece lo segundo: **esta tanda no ha dejado
> rastro en `progress/impl_F-025.md`**. No hay sección de la tanda, no hay
> fase RED del control negativo nuevo —que es el entregable central de la
> corrección— y las «Evidencias» siguen siendo las de la tanda 3, con números
> que los cuatro commits han dejado desfasados.
>
> Es **una frase de comentario y una sección de informe**. El trabajo técnico
> está hecho y verificado.

Alcance acotado, como pedía el encargo: solo los tres reparos, que no se haya
roto nada al corregirlos, y las puertas del arnés. Lo aprobado en la primera
pasada sigue aprobado. Commits revisados: `fe2f7d3`, `2e4e14a`, `90ee2a9`,
`1d1e3c6` y el de rastro `e276f0e`.

---

## S1 · Reparo 1 · R37 — **RESUELTO, verificado con la prueba que lo destapó**

Es el que importaba: R37 es, por escrito, la única compensación del riesgo que
§0 de la spec acepta a propósito. Lo he verificado **rehaciendo la campaña
manual**, no leyendo el diff.

Copia aislada en el scratchpad (`js/` y `tests_js/` enteros, fuera del árbol
real). Línea base: **231 tests, 231 pass, 0 fail**.

| # | Mutación sobre `js/pipeline.js` | Antes (1ª pasada) | **Ahora** |
|---|---|---|---|
| M14a | `numeroDeIncidenciaDe` rellena el hueco con un número fijo: `: (actual \|\| "XX00.00/0000")` | **SUPERVIVIENTE** | **MUERTO** — 1 fail |
| M14b | el paso 3 pasa como respaldo el número **leído del papel** (`parte.extraccion.campos.numero_incidencia.valor`) | no probada | **MUERTO** — 1 fail |
| M14c | condición invertida: `numero ? actual : String(numero)` | — | **MUERTO** — 4 fails |
| M14d | la función ignora al ERP: `return actual;` | — | **MUERTO** — 3 fails |

El test que mata M14a y M14b es el que faltaba, y solo él:

`services/postventa-front/tests_js/circuito.test.js` ·
`test("R37 · con los tres pasos en verde y sin número en la respuesta, no se inventa ninguno")`

Es el único guion del fichero que ejecuta `numeroDeIncidenciaDe` **con la
clave ausente y el circuito entero en verde** (`apiDoble({adjuntar: {estado:
"adjuntado"}, cerrar: {estado: "cerrado"}})`), que era exactamente el hueco.
Afirma tres cosas y las tres hacen falta: que los tres pasos se ejecutaron,
que `numeroIncidencia === ""`, y —esto es lo que mata M14b— que el número del
papel **no se ha colado**, ni como valor ni por la puerta de atrás del
`mensaje` del resumen.

Dos aciertos más de esta corrección, que no pedí y suman:

- El viejo test de la línea 463 **no se ha borrado**: se ha renombrado a
  «un parte que no llega al ERP se queda sin número» y lleva escrito en el
  cuerpo que ahí la función **no se ejecuta**. Se le añadió
  `assert.equal(resultado.estado, "error_archivo")`, que es lo que de verdad
  prueba. Un test mal nombrado convertido en un test honesto, en vez de
  suprimido.
- El tercer guion nuevo («si solo lo devuelve el cierre, ese es el que se
  enseña») no es relleno: es el único que mata M14d por sí solo.

**Casilla cerrada.** Con esto, el módulo que concentra las decisiones de las
tres escrituras queda en **14 de 14** de mi campaña manual.

## S2 · Reparo 2 · trazabilidad — **RESUELTO, barrido independiente**

No me he fiado de la tabla. He extraído los **48 requisitos** de
`requirements.md` y he cruzado cada uno contra el corpus entero de tests de
F-025 (`test_f025_*.py` y `tests_js/*.test.js`), buscando su test nominal o su
entrada en la tabla de exenciones.

**Resultado: ningún requisito queda fuera.** Los únicos tres sin test nominal
—R44, R45 y R48— están ahora en la tabla, y con evidencia concreta, que era la
condición del encargo. (R49, R50, R51, R53, R54, R63, R65–R67 aparecen en el
texto de la spec pero son requisitos **de F-012 y de F-009** citados, no de
F-025: no cuentan.)

Los cuatro que recibieron test nominal:

| Requisito | Test nuevo | ¿Prueba lo que dice? |
|---|---|---|
| **R3** | `f025 R3` en `tests_js/confirmacion.test.js` + `test_f025_r3_sin_confirmacion_que_dispare_no_arranca_ninguna_escritura` | Sí. El de JS ejecuta `Confirmacion.resolver` de verdad en los **tres** estados que no disparan (sin armar, caducada, consumida). El de Python fija el **orden** dentro de `confirmarArchivo`: la salida por `return` antes de `pendientes()`, de `conGuardaDeTanda(` y de `_lanzarTanda(` |
| **R15** | `f025 R15` en `confirmacion.test.js` + `test_f025_r15_la_confirmacion_se_consume_antes_de_lanzar_la_tanda` | Sí, y con el matiz correcto: el segundo clic llega **dentro** de la ventana —lo afirma— así que no lo salva la caducidad; lo para el consumo del armado |
| **R23** | dos tests en `circuito.test.js` | Sí: cuentan que `adjuntar` se llamó **una** vez tras fallar, y que un cierre fallido por entorno tampoco se repite |
| **R28** | `R28 · relanzar la tanda sobre un parte a medias…` | Sí, y es el mejor de los cuatro: corre la tanda entera, la deja a medias con el cierre caído, **relanza** con el parte tal y como lo deja `app.js`, y afirma que el paso que produce el gráfico —y con él la fila de `dbo.log`— **no se vuelve a pedir** |

Las tres exenciones, comprobadas por mí y no leídas:

- **R45** — «los compositores intactos en el diff». **Cierto.** El diff de
  `js/pipeline.js` contra `941a673` tiene cuatro hunks y **ninguno cae dentro
  de `cuerpoDeArchivo`, `cuerpoDeGrafico` ni `cuerpoDeCierre`**. El único
  cambio en esa zona es `estaAdjuntado`, que pasa de `"adjuntado"` literal a
  la constante `ESTADO_ADJUNTADO`, definida en la línea 69 como `"adjuntado"`:
  refactor de valor idéntico.
- **R48** — `git -C azure-apps status` **limpio**, ejecutado por mí ahora
  (`02025db` como último commit, ajeno a este trabajo). Solo lectura.
- **R44** — los dos tests que cita existen y pasan; la suite de F-007 sigue
  entera.

**Casilla C4 cerrada.**

## S3 · Reparo 3 · el comentario derogado — **RESUELTO A MEDIAS**

Lo que pedí está hecho, y bien: `js/api.js`, en el docstring de `cerrar`, ya
no dice «hay que enseñarlo **antes** de que nadie confirme». Lo que hay en su
sitio es mejor que lo que pedí —dice que la comprobación **no** desapareció,
solo la pantalla, y avisa a quien lea dentro de seis meses de que reponerla es
deshacer una decisión fechada—.

**Pero el encargo pedía además comprobar que no quedan otros iguales en el
front, y queda uno.** Es literal, es el mismo fichero y está **26 líneas más
arriba**, en el docstring de `adjuntar`:

```
services/postventa-front/js/api.js:417-419

 * **Por omisión no escribe nada**: sin `commit` el backend responde el
 * dry-run —nombre, clase, tamaño, `sha256` y los avisos de la pasarela—,
 * y eso hay que enseñarlo antes de que nadie confirme.
```

Tres razones por las que no lo dejo pasar:

1. **Es la misma afirmación, no una parecida.** Mi reparo era sobre lo que el
   comentario **afirma** —que el dry-run hay que enseñarlo antes de
   confirmar—, no sobre la línea 445. Corregir la línea citada y dejar viva la
   frase gemela deja el reparo sin resolver en lo que lo motivaba.
2. **Este es, si acaso, el peor de los dos.** El de `cerrar` hablaba del
   bloque `grafico` dentro de la respuesta del cierre. Este está en
   `adjuntar`, que es **el endpoint cuya pantalla previa se ha retirado**
   (R40 deroga R21 y R49 de F-012). Es el sitio exacto donde alguien iría a
   «arreglarlo».
3. **El fichero ha quedado contradiciéndose a sí mismo.** En la línea 419 dice
   que hay que enseñarlo; en la 447, que ya no se le enseña a nadie. Quien lea
   solo la primera —que es la que está en el endpoint del gráfico— concluirá
   que falta una pantalla.

Procede: `git blame` confirma que viene de `cf5f028c` (F-012, 2026-09-06) y
que F-025 no lo ha tocado. Igual que el de la 445, que también era anterior.

**Lo que sí he comprobado y está limpio**: el resto del front no tiene ningún
otro caso. `js/app.js:93` e `index.html:250-255` hablan del cálculo previo en
**pasado** y con su constancia de derogación —«aquí vivían `dryRunCierre` y
`dryRunGrafico`», «el responsable decidió… y respondió *no hace falta enseñar
nada*»—, que es justo como tiene que estar escrito. Barrido hecho sobre `js/`
e `index.html` con los patrones `enseñ`, `antes de confirmar`, `antes de que
nadie`, `pantalla previa` y `Ver qué pasaría`: **un solo acierto**, el de
arriba.

## S4 · Hallazgo nuevo de esta pasada · la tanda no ha dejado rastro

No estaba en el encargo, pero aparece al comprobar el reparo 3 y toca una
casilla que ya estaba vacía en la primera pasada, así que no lo puedo callar.

El encargo dice que el informe de esta tanda está al final de
`progress/impl_F-025.md`. **No está.** El fichero termina en **§29** y lo único
que los cinco commits le han cambiado es **una línea** (la fila de mutación de
las Evidencias, `e276f0e`). Consecuencias concretas:

1. **No hay fase RED del control negativo de R37**, que es el entregable
   central de esta corrección. C4 bis es explícito para este caso: cuando el
   entregable **es el propio test**, la fase RED se demuestra rompiendo en una
   copia aislada lo que el test vigila y **pegando la traza**. Esa traza no
   existe en ningún informe. *La sustancia está probada* —la he producido yo
   en §S1, y es más fuerte que la que se pedía—, pero el arnés pide que la
   traiga el implementer y este es justo el requisito donde no conviene
   relajarlo.
2. **Las «Evidencias» vigentes son las de la tanda 3** y sus números ya no son
   los de lo entregado. Medidos por mí ahora: **front 188** tests (decía 185),
   **`node --test` 231** (decía 224), **api 2.144** (13 skipped), **raíz 62**.
   El total de la tabla, 2.391, es del estado anterior a los cuatro commits.
3. **Referencia colgada**: la fila corregida remite a «**§30.3**, las
   mutaciones a mano sobre `js/pipeline.js`». No hay §30 en el fichero, y esas
   mutaciones son de **§2.4 de esta review**, no del informe del implementer.

Nada de esto pone en riesgo el ERP. Es el papeleo que C4 bis pide por su
nombre, y es lo mismo que dejó vacía esa casilla la primera vez.

## S5 · Que corregir no ha roto nada — **COMPROBADO**

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` | **exit 0**, `ENTORNO LISTO` |
| **Cobertura** | `PUERTA COBERTURA: 99,0 % de 1.079 líneas cambiadas (1.068/1.079, umbral 80 %, nivel critico)` — **[OK]**, sigue muy por encima |
| Suite del front, sin caché (`pytest tests -q`) | **188 passed** en 2,88 s (eran 185: +3) |
| Suite JS del árbol real (`node --test "tests_js/*.test.js"`) | **231 pass, 0 fail** (eran 224: +7) |
| `git status` | **limpio**, antes y después de mi campaña en el scratchpad |
| `progress/mutacion_F-025.md` | **trackeado** (`git ls-files` lo confirma): el punto 5 de §7 está hecho |
| Fila «Mutantes generados y supervivientes» de §28 | **corregida**: ya dice «Ejecutada» con los totales y `--workers 1`. El punto 3 de §7 está hecho salvo la referencia colgada de §S4.3 |
| Hallazgo leve 6 (clave del `x-for`) | **arreglado bien**: `clave: "${hash}:${longitud}"` al empujar la fila, en los **dos** resúmenes, con su test. Único cambio de esta tanda en código de producción, y el comentario explica por qué la fila descartada sería la del reintento —la que trae el número de R37—. `index.html` pasa a `:key="resultado.clave"` en las dos listas |

El backend sigue sin tocarse: los cuatro commits solo alcanzan
`tests_js/`, `tests/`, `js/api.js`, `js/app.js`, `index.html` y
`requirements.md`.

## S6 · Checkpoints que cambian respecto a la primera pasada

Solo los que estos commits mueven. El resto queda como en §6.

| Checkpoint | 1ª pasada | **2ª pasada** |
|---|---|---|
| C4 · cada requisito con test trazable | `[ ]` | **`[x]`** — barrido de los 48, §S2 |
| C4 bis · fase RED | `[x]` | **`[ ]`** — falta la del control negativo nuevo de R37, §S4.1. La sustancia la aporta §S1, pero no la aporta el informe |
| C4 bis · Evidencias con los cuatro números | `[ ]` | **`[ ]`** — la fila de mutación está corregida, pero la tabla es de la tanda 3 y sus números están desfasados, §S4.2 |
| C3 · sin textos que contradigan lo vigente | `[x]` con reparo | **`[x]` con el reparo abierto** — `api.js:419`, §S3. No lo cuento como casilla vacía, igual que la primera vez, pero es el reparo que no se ha cerrado |
| C1, C2, C3 bis, C4 ter | `[x]` / N/A justificado | **sin cambios** |
| C5 · `tasks.md`, sin artefactos sin trackear | `[ ]` | **parcial**: el artefacto ya está trackeado y el árbol limpio; **T19–T25 siguen `[ ]`**, que es pendiente de los bloques 5 y 6, no reparo |

---

## S7 · Cambios requeridos de esta pasada

Dos, y ninguno toca `js/pipeline.js`, `js/app.js`, `index.html` ni el backend.

1. **`services/postventa-front/js/api.js:417-419`** — retirar el «y eso hay
   que enseñarlo antes de que nadie confirme» del docstring de **`adjuntar`**,
   que es el gemelo literal del que se corrigió en `cerrar`. Sirve la misma
   redacción que ya se escribió en las líneas 447-453: que la comprobación
   previa **se sigue ejecutando dentro de la llamada que escribe**, que lo que
   desapareció es la pantalla (R40 de F-025, que deroga R21 y R49 de F-012), y
   que reponerla no es arreglar nada. Con el fichero contradiciéndose entre la
   419 y la 447, es más fácil que alguien concluya lo contrario.
2. **`progress/impl_F-025.md`** — añadir la sección de esta tanda (§30), con:
   - la **fase RED del control negativo de R37**: romper en copia aislada lo
     que el test vigila —vale mutar `numeroDeIncidenciaDe` como M14a de §S1— y
     **pegar la traza real** del test cayendo. C4 bis lo pide literalmente
     para el caso en que el entregable es el propio test;
   - las **Evidencias actualizadas** con los cuatro números de lo entregado:
     tests (front 188, `node --test` 231, api 2.144 con 13 skipped, raíz 62),
     cobertura 99,0 %, mutación (los totales que ya están, con `--workers 1`) y
     tiempo de la suite;
   - y de paso, **arreglar la referencia colgada a «§30.3»** de la fila de
     mutación: hoy apunta a una sección que no existe, y las mutaciones
     manuales viven en §2.4 y §S1 **de esta review**, no en el informe.

Nada más. Con esas dos cosas, F-025 queda aprobada por lo que a esta review
respecta —siguen pendientes, por el encargo y no por reparo, los bloques 5
(`MANUAL (humano)`, T19–T23) y 6 (T24–T25), y hasta cerrarlos la casilla de C5
no se puede marcar ni la feature pasar a `done`.

## S8 · Automejora que esta pasada añade

*(No la aplico: la propongo, como manda el protocolo.)*

4. **`.claude/agents/reviewer.md` y `CHECKPOINTS.md` · un reparo se cierra por
   la afirmación, no por la línea citada.** Esta pasada ha encontrado el
   gemelo literal de un comentario derogado 26 líneas más arriba del que cité.
   Un reviewer que cita `fichero:línea` induce a corregir esa línea; el
   implementer hizo exactamente lo que decía el papel. Propuesta de frase para
   el protocolo del reviewer, en «Informe»: *«Cuando un cambio requerido sea
   sobre un texto o una afirmación, el reviewer da el **patrón de búsqueda**
   además de la línea, y en la revisión siguiente **repite el barrido**, no
   solo la línea.»* Y la contrapartida para el implementer: *«Ante un reparo
   sobre un texto, barrer el fichero y sus vecinos antes de darlo por
   cerrado.»* Vale para cualquier proyecto: va a `arnes-base`.
5. **`CHECKPOINTS.md`, C4 bis · la fase RED de una tanda de correcciones.**
   C4 bis ya contempla que el entregable sea el propio test, pero se lee como
   algo de la tanda de implementación. Aquí el entregable de la tanda entera
   **eran tres tests**, y no hubo traza de ninguno. Propuesta: decir
   explícitamente que **una tanda post-review también trae su fase RED y sus
   Evidencias**, porque lo que entrega es exactamente la clase de artefacto
   para el que la puerta existe. También genérico: `arnes-base`.

---
---

# Tercera pasada · 2026-09-11

**Veredicto de esta pasada: APROBADO**

> Los dos reparos de la segunda pasada están cerrados. El **gemelo** del
> comentario derogado ya no está, y el barrido —`js/` entero e `index.html`,
> por término y por afirmación, no por línea— no encuentra **ningún otro**
> texto en el front que diga que el dry-run se enseña antes de confirmar. La
> **§30 del informe** existe, es veraz en todo lo que afirma y dice sin
> adornos lo que no puede afirmar.
>
> Sobre la fase RED que la §30 declara no registrada: **no la exijo**, y no
> por indulgencia. De los cinco commits de la tanda, cuatro no tocan código de
> producción —dos son solo tests, dos solo comentarios—, y para el único que
> sí lo toca **he reconstruido el rojo yo mismo** y lo tengo medido abajo. Lo
> que la fase RED demuestra ya está demostrado, y por una vía más fuerte:
> medida por el reviewer, no declarada por el implementer.

Alcance: exactamente el del encargo. Lo aprobado en la primera y la segunda
pasada sigue aprobado y no se reabre. Commit revisado: `f1d7453`.

---

## T1 · El gemelo, y el barrido completo del front

`git show f1d7453` retira la afirmación de `js/api.js:418` (bloque de
`adjuntar`) y la sustituye por el mismo texto que ya llevaba `cerrar`: la
derogación explícita de R63 por R40, dónde sigue viva la comprobación previa
(`design.md` §2) y el aviso a quien lo lea dentro de seis meses. **Cerrado.**

No me quedo en la línea del reparo —que es justo el error de la pasada
anterior—. Tres barridos sobre `services/postventa-front/js/` (los ocho
ficheros) e `index.html`:

| Barrido | Patrón | Resultado |
|---|---|---|
| Por término | `dry.run`, `dryrun` | 9 aciertos, todos revisados uno a uno |
| Por afirmación | `antes de que nadie`, `antes de confirmar`, `antes de que se confirme`, `enseñarlo`, `se le enseña`, `hay que enseñar`, `revisar antes`, `previsualiz`, `pantalla previa`, `vista previa`, `comprobar antes`, `ver antes` | 3 aciertos, los 3 correctos |
| Por vecindad | `pantalla`, `enseñ`, `previo`, `previa` | 44 aciertos, revisados |

**Ninguno afirma que el dry-run se enseñe antes de confirmar.** Los 9 del
primer barrido, en detalle:

- `js/api.js:418,420` y `js/api.js:451,453` — las dos negaciones expresas, una
  en `adjuntar` y otra en `cerrar`. Son el texto correcto.
- `js/api.js:449` — describe lo que el **backend** responde sin `commit`. Es
  cierto: el endpoint sigue teniendo ese modo, y decirlo no es afirmar que
  alguien lo vea. Cuatro líneas más abajo está la negación.
- `js/app.js:92-96` — la nota de dónde vivían `dryRunCierre` y `dryRunGrafico`.
  Está **en pasado** y explícita: «la pantalla previa se retiró entera». Es
  historia bien fechada, no una afirmación vigente.
- `js/pipeline.js:257` y `js/pipeline.js:332` — «por omisión es un dry-run»
  sobre `cuerpoDeCierre` y `cuerpoDeGrafico`. Describen el **valor por defecto
  de la función que compone el cuerpo**, que sigue siendo ese, y es la
  propiedad que hace segura la composición. No dicen nada de enseñar.
- `js/pipeline.js:715` — remata al revés: «lo que desaparece con F-025 es la
  pantalla, no la verificación», con el test que lo vigila citado por ruta.

Y en `index.html`, el comentario de la sección 5 (líneas 249-262) cuenta la
decisión del responsable con su fecha, lo que se pierde y lo que no. Es el
registro que R40 merece.

**Una sola observación cosmética, que NO es reparo y no bloquea:** el titular
de `js/api.js:445` sigue siendo «cierra la incidencia en Sigrid, o enseña qué
pasaría». Es verdad del *endpoint* y queda desmentido como pantalla ocho
líneas más abajo, en el mismo bloque, así que no engaña a nadie. Lo dejo
anotado por si alguien pasa por ahí, no como condición.

---

## T2 · La §30 del informe · existe, y dice la verdad

Verificado punto por punto, sin creerme la tabla:

| Lo que afirma la §30 | Comprobación | Resultado |
|---|---|---|
| Los cinco commits de la tanda | `git log -1` sobre `fe2f7d3`, `2e4e14a`, `90ee2a9`, `1d1e3c6`, `f1d7453` | Los cinco existen, con el asunto que la tabla les atribuye |
| Cuál cierra cada reparo | `git show --stat` de cada uno | Coincide: `fe2f7d3` solo `circuito.test.js`; `2e4e14a` tests + `requirements.md`; `90ee2a9` solo `js/api.js`; `1d1e3c6` `index.html` + `app.js` + su test |
| La fase RED **no quedó registrada** y **no se reconstruye** | Lectura de la §30 y del historial | Cierto, y dicho en la cabecera de la sección, no enterrado |
| Lo que la sustituye está en la §S1 de esta review | Releída la §S1 | Exacto: línea base 231 tests, M14a superviviente antes y muerto ahora, M14b/c/d muertos |
| «Comentarios derogados vivos en el front: 0» | El barrido de T1 | Confirmado |
| «Ejecutado contra Azure, Sigrid, PostgreSQL o SharePoint: nada» | Diff de la tanda | Confirmado; tampoco yo he tocado ninguno |

Sobre la estructura del informe: cada tanda lleva sus propias Evidencias
—§9, §18, §28 y ahora §30—, y la §30 las titula «medidas después de esta
tanda». El desfase que rechazó la segunda pasada queda resuelto: las de la §28
no se presentan como vigentes, se presentan como las de la tanda 3.

---

## T3 · Las evidencias que cita, verificadas en mi máquina

No las tomo del informe ni de la caché del arnés:

| Evidencia | Declarado en la §30 | Medido por mí | Cómo |
|---|---|---|---|
| Suite del servicio `api` | 2.144 pasan, 13 saltados | **2144 passed, 13 skipped** en 72,42 s | El intérprete del venv del servicio con `-m pytest -q -p no:cacheprovider`, ejecución completa y **sin caché** (el `init.sh` la daba por buena por árbol sin cambios) |
| Suite del front | 188 pasan | **188 passed** en 6,31 s | `harness/init.sh` |
| Cobertura de lo cambiado | 99,0 % | **99.0 %**, 1068/1079 líneas, umbral 80 %, nivel `critico` | `PUERTA COBERTURA` de `harness/init.sh` |
| `ruff` | 58 avisos, la deuda previa | **58 avisos** | `harness/init.sh` |

Las cuatro cifras son ciertas.

---

## T4 · La fase RED: por qué no la exijo, y el rojo que he medido yo

El encargo pide un juicio explícito, y este es, con su razonamiento a la
vista.

**Qué entregó realmente la tanda.** De los cinco commits, `fe2f7d3` y
`2e4e14a` tocan **solo ficheros de test**; `90ee2a9` y `f1d7453`, **solo
comentarios**. El único que cambia código que se ejecuta es `1d1e3c6`, el
hallazgo leve 6.

**Por qué en los de test la fase RED clásica no aplica, y qué la sustituye.**
El entregable de `fe2f7d3` es un control negativo sobre `numeroDeIncidenciaDe`,
una función que **ya existía y ya era correcta**. Un test así pasa en verde
desde el primer minuto contra el código bueno: no hay rojo que enseñar. Lo que
demuestra que el test vale es que **mate al mutante**, y eso está medido en la
§S1 de esta review por mí, no por el implementer: cuatro mutaciones de la
función, las cuatro muertas ahora, y la primera **sobrevivía antes de la
tanda**. Exigir aquí una fase RED sería exigir un artefacto más débil que el
que ya hay, y encima reconstruido a posteriori, que es justo lo que la §30 se
niega —bien— a hacer.

**El único cambio de producción sí tenía un rojo que enseñar, y lo enseño
yo.** No me conformo con darlo por bueno: he montado una copia del front en el
scratchpad, he repuesto `index.html` y `js/app.js` **en su versión anterior a
`1d1e3c6`** (`git show 1d1e3c6^:...`) dejando el test nuevo en su sitio, y lo
he ejecutado:

```
$ python -m pytest tests/test_f025_front.py::test_f025_r16_cada_fila_del_resumen_lleva_una_clave_unica -q
>       assert html.count(':key="resultado.hash"') == 0, (
E       AssertionError: el hash se repite entre la fila original y la del reintento
E       assert 2 == 0
1 failed in 0.22s
```

**El rojo existe y es reproducible.** Falla por lo que tiene que fallar —las
dos `:key` duplicadas que hacían que Alpine descartara la fila del reintento,
con el número de incidencia de R37 dentro— y pasa con el cambio puesto. La
casilla de C4 bis queda cubierta **con evidencia real**; la única diferencia
es quién la produjo.

**Veredicto sobre este punto: NO exijo la fase RED de la tanda 4.** La
declaración de la §30 es aceptable, y lo es precisamente porque declara en vez
de inventar. Un informe que hubiera reconstruido un rojo plausible sin haberlo
ejecutado habría sido peor y más difícil de detectar.

Lo que sí dejo dicho, para que no se lea como un precedente: esto se sostiene
porque la tanda era **casi toda tests y comentarios** y porque la evidencia
sustitutiva la produjo el reviewer de forma independiente. Una tanda que
cambie comportamiento sin fase RED y sin sustituto medido no pasa.

---

## T5 · El arnés, en verde

`bash harness/init.sh`, ejecutado limpio al abrir la pasada:

- Arnés v1.5.2, `features.json` y `rigor.json` válidos, `BACKLOG.md` al día.
- 62 tests del arnés en verde; servicio `api` en verde; servicio `front`, 188
  en verde.
- `PUERTA COBERTURA`: `[OK]` 99.0 %, nivel `critico`.
- Rama `feature/F-025-confirmacion-unica`, la correcta. No la he cambiado.
- Único aviso: F-009 en `blocked`, que es anterior a F-025 y consta en
  `progress/current.md`. Y los 58 de `ruff`, la deuda previa exacta.

`git status` en el árbol: limpio salvo este mismo informe. La copia de la
verificación RED vive entera en el scratchpad, **fuera del repositorio**, y no
ha dejado nada detrás.

---

## T6 · Estado de los checkpoints tras esta pasada

Solo los que se movían. El resto se queda como lo dejó la segunda pasada.

| Checkpoint | Antes | Ahora | Motivo |
|---|---|---|---|
| **C3** — código y convenciones | `[ ]` por el comentario derogado | **`[x]`** | El gemelo retirado y el barrido completo del front sin un solo acierto falso |
| **C4 bis** — el rigor declarado se cumple | `[ ]` por la tanda sin rastro | **`[x]`** | §30 escrita y veraz; fase RED del único cambio de producción **medida por el reviewer**; Evidencias al día y verificadas una a una |
| **C4** — la verificación es real | `[x]` | **`[x]`** | 2.144 + 13, 188, 99,0 %, comprobados sin caché |
| **C1** — arnés completo y en verde | `[x]` | **`[x]`** | `init.sh` en verde |

Ningún checkpoint queda en `[ ]`. Ninguno queda en `N/A` sin justificación:
los `N/A` vigentes son los de la primera pasada —la puerta de mutación sobre
un diff cuyo alcance Python es nulo—, justificados allí y reverificados en la
§2 con su prueba de control.

---

## T7 · Lo que queda, y no es de esta review

1. **El bloque 5 de `tasks.md`**: la verificación contra el ERP real, que es
   del responsable y escribe en una obra en uso. Nada de esta pasada la
   sustituye.
2. **El bloque 6**, el cierre, que lleva el líder.
3. **Aviso de proceso, no reparo:** las pasadas segunda y tercera de este
   informe están **sin commitear** en el árbol (`git status` marca
   `progress/review_F-025.md` como modificado). El rastro del arnés no existe
   hasta que se commitea; que el líder lo recoja al cerrar.

---

## T8 · Automejora: ninguna nueva

Las cinco propuestas de las pasadas anteriores siguen en pie y no las repito.
Esta pasada confirma que **la número 4** —cerrar un reparo por la afirmación y
no por la línea, repitiendo el barrido— habría evitado la segunda pasada
entera, y que **la número 5** —una tanda post-review también trae su fase RED
y sus Evidencias— es la que hoy se ha resuelto por la vía del reviewer. Las
dos son genéricas: van a `arnes-base`.
