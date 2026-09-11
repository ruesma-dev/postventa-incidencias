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
