<!-- progress/review_F-035.md -->
# F-035 · Review · Diseño del portal de posventa: todas las secciones con placeholders

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`
> (`54c0884` .. `f5634ea`), contra `specs/F-035-portal-posventa/` (aprobada por
> el humano: acta de T1 y `design.md` §13.1), `docs/CONVENTIONS.md`,
> `docs/ARCHITECTURE.md` y `CHECKPOINTS.md`.
>
> **En esta revisión no se ha implementado ni corregido nada.** No se ha
> desplegado nada ni se ha escrito en Sigrid, SharePoint, Azure ni PostgreSQL.
> `front-portal` y `azure-apps` solo se han leído. Las mutaciones se aplicaron
> en una copia desechable del front dentro del scratchpad de la sesión, nunca
> en el árbol de trabajo. La campaña reejecutada escribió su informe en el
> scratchpad. `git status` queda limpio. El único fichero que se escribe en
> el árbol es este.

## Veredicto

**CHANGES_REQUESTED** (RECHAZADO), por **un hallazgo bloqueante de gravedad
MEDIA** (H-R1) y uno BAJO que conviene cerrar en la misma vuelta (H-R2).

**Lo que más importaba está bien, y lo he comprobado yo:**

- **La mudanza del circuito es solo una mudanza.** `diff` entre el blob
  `54c0884:services/postventa-front/index.html` y `HEAD:services/postventa-front/partes.html`
  da exactamente dos cambios: la línea 1 (ruta) y 22 líneas insertadas tras la
  línea 16 (`<div x-data="appPostventa()">`), que son la barra. `git diff -C`:
  `C093 index.html -> partes.html`, `23 1`.
- **Nada del circuito cambia.** `git diff --stat 54c0884 HEAD` sobre
  `js/`, `css/`, `staticwebapp.config.json`, `dev_server.py`, `dev_front.ps1`,
  `infra/` y `tests_js/`: solo **altas** (`maqueta_datos.js`, `portal.js`,
  `portal_app.js`, `portal.css` y los dos `*.test.js` nuevos). Ni un byte de
  un fichero existente.
- **Los siete tests del circuito cambian solo la línea `INDEX`**: los siete
  diffs leídos uno a uno, `-INDEX = RAIZ_FRONT / "index.html"` →
  `+INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3)…`, `1 1` cada uno.
- **La barra de `partes.html` es inerte (R45).** Solo `<nav>`, `<div>`,
  `<span>` y `<a>` con `href`, `target`, `rel`, `class` y `aria-current`. Ni
  `x-`, ni `@`, ni `:`, ni `<script>`, `<button>`, `<form>` o `<input>`. Los
  nueve módulos del circuito no consultan el DOM ni `location`: `grep` de
  `location|querySelector|getElementsBy|href` en los nueve, vacío. Tampoco
  `css/styles.css` tiene selectores de `nav`, `header` o `a`.
- **La maqueta no llama a nada (R14–R18).** Esto es lo que he buscado en los
  cinco ficheros de la maqueta: `fetch`, `XMLHttpRequest`, `sendBeacon`,
  `WebSocket`, `EventSource`, `import(`, `/api/`, `mailto:`, las URL de
  SharePoint, Graph o sigrid, el almacenamiento del navegador, `<form`,
  `<iframe`, `action=`, `window.open`, `location.href/assign/replace`,
  `navigator.`, `postMessage`, `new Image` y `http`. No aparece nada salvo los
  dos CDN y dos menciones textuales a «sigrid-api» en comentarios y en un
  texto «Pendiente», que no son URL. Los `<input>` son casillas y un buscador
  locales. Los `href` son solo `#/…`, `partes.html` y `:href="hashDe(…)"`.
- Las **tres decisiones del implementer que no estaban en la spec se
  sostienen** (ver «Decisiones fuera de la spec»).

**Lo que falla (H-R1):** en JavaScript la herramienta de mutación no genera
mutantes, así que D-9 exige compensarlo con mutaciones a mano. Las ocho de
`design.md` §11 están bien hechas, pero ninguna toca el **cableado del
componente**: `iniciar()` y `aplicarRuta()` de `js/portal_app.js`, que es lo
que convierte el hash en la sección que se ve. He aplicado **32 mutaciones
propias**: 22 muertas y **10 supervivientes** con toda la suite en verde
(398/398 en JS y la suite de pytest sin cambios). Seis de los supervivientes
están en el componente, y cinco de esos seis **rompen la navegación del
portal**: quitar el `addEventListener("hashchange", …)`, fijar
`this.seccion = "inicio"`, fijar `this.incidenciaAbierta = null`, fijar
`this.avisoRuta = ""` y quitar el `aplicarRuta()` inicial de `iniciar()`. En
esos casos, un portal que nunca sale de `inicio`, que nunca abre una ficha,
que nunca da el aviso de R7 o que ignora un enlace profundo **pasa todas las
pruebas**. Es el primer criterio de la ficha («todas las secciones…
existen **y se navegan**») y R4, R6 y R7 del componente. Hoy solo lo
detectaría V1, que está sin ejecutar. La infraestructura del test ya existe
(`conVentanaFalsa`, `navegar` con los `oyentes`): falta afirmar el resultado.

La corrección es de tests, pequeña y en una sola tarea: ver «Cambios
requeridos».

## Nivel de rigor

`estandar`, declarado en `harness/features.json` (entrada F-035,
`"rigor": "estandar"`). Exige C1–C3, C3 bis, C5, tests trazables (C4), fase
RED en los requisitos centrales, cobertura de las líneas cambiadas y campaña
de mutación con los supervivientes documentados y analizados.

## Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` tal cual | **Exit 0**, `ENTORNO LISTO`. Raíz 69 passed. Servicios api y front en verde (desde caché). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. `ruff` con 61 avisos, deuda previa |
| pytest del front **sin caché** (`-p no:cacheprovider`) | **294 passed** |
| `node --test tests_js/*.test.js` | **398 pass, 0 fail** |
| Alcance recalculado (`harness.alcance.alcance_de_feature("F-035")`) | 0 ficheros, 0 líneas de producción. Coincide con el informe |
| Mutantes recalculados (`generar_mutantes` sobre el alcance) | **0**. Coincide |
| Prueba de control del cero, sin la exclusión de alcance | `test_f035_portal.py`: 846 líneas y **154** mutantes. `test_f035_placeholders_vivos.py`: 182 líneas y **22**. Los siete `INDEX`: 0 cada uno. **El generador funciona**: el cero es la exclusión por diseño (los únicos `.py` del diff son tests; el resto es JS, HTML, CSS y Markdown) |
| Campaña reejecutada (el «Tiempo total» es 0,0 s, menos de 5 min) | `python -m harness.mutacion --feature F-035 --workers 1 --salida <scratchpad>/mutacion_F-035_reviewer.md`: 0 generados, 0 evaluados, 0 muertos, 0 supervivientes, 0 timeouts. **Idéntica** al informe. `git status` limpio después |
| Mutaciones propias en JS, HTML y datos (copia desechable) | 32 aplicadas: **22 muertas y 10 supervivientes** (6 del componente y 4 de la lógica pura). Detalle en H-R1 y H-R2 |
| Diff de la mudanza | Ver el veredicto. `diff` de blobs git: solo la línea 1 y un bloque insertado de 22 líneas |
| Barrido de datos sensibles (R24, D-10) | Ver C3. Ni un GUID, ni un correo fuera de `ejemplo.invalid`, ni un DNI, NIF o teléfono, ni una IP |
| Despliegue (solo lectura) | Ver «Despliegue» |

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0 (ejecutado por mí, tal cual).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (init.sh los verifica).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`, F-035 (init.sh).
- [x] Rama `feature/F-035-portal-posventa`.
- [x] `progress/current.md` describe arriba la sesión activa (bloques 2 a 4
      de F-035). *Conserva debajo el histórico de sesiones anteriores: es
      deuda previa del repositorio, no imputable a F-035, igual que en las
      reviews de F-031 y F-034.*
- [x] Toda feature `done` tiene su resumen en `history.md`: F-035 no toca
      ninguna otra feature ni su estado.

### C3 — El código respeta arquitectura y convenciones
- [x] Arquitectura: `portal.js` es puro (sin DOM, sin Alpine, sin red),
      `portal_app.js` solo guarda estado y delega en él, y
      `maqueta_datos.js` solo lleva datos (congelados). No entra nada en
      `postventa-api`.
- [x] Primera línea con la ruta en los diez ficheros nuevos o renombrados
      (`index.html`, `partes.html`, `portal.css`, los tres JS, los tres tests
      nuevos y `maqueta_datos.test.js`), todos comprobados.
- [x] Sin `print` ni `console.` de depuración (`grep` vacío; en los tests, el
      único «console.» es el texto de la guardia que lo prohíbe). Sin TODO.
      Sin secretos. Sin dependencias nuevas: Alpine 3.14.1 y Tailwind son los
      mismos CDN que ya usaba el circuito.
- [x] La unidad es el parte: **N/A justificado**. La maqueta no procesa
      partes. El único dato por parte, el panel de volcado (R40), va por parte
      con su `PVI-…`.
- [x] Nada se archiva ni se cierra sin validaciones: **N/A justificado**. La
      maqueta no archiva, no cierra y no llama (R14–R16, verificado arriba).
      Los placeholders de volcado y de cambio de estado explican el
      dry-run previo.
- [x] Lo manuscrito no se descarta: **N/A justificado**, la maqueta no lee
      partes.
- [x] Firmado no es conforme: **N/A justificado**, por el mismo motivo.
- [x] Reprocesar no duplica: **N/A justificado**. No hay proceso. El texto
      del volcado explica la idempotencia por `PVI-`.
- [x] Ningún número de estado hardcodeado: `Portal.ESTADOS` usa
      código y resumen de `conest` (`SAT`, `PTE`, `TER`, `NPR`, `CER`), nunca
      el número (R21, probado).
- [x] Ningún PDF ni parte escaneado en git:
      `git log --diff-filter=A --name-only 54c0884..HEAD` sin
      `.pdf/.docx/.xlsx/.pptx/.zip/.png/.jpg`.

**Barrido de datos sensibles** (aunque no es C3 bis, el encargo lo pide para
R24 y para `docs/ARCHITECTURE.md`). Patrones usados sobre los ficheros de la
maqueta, el README y las líneas añadidas del diff completo (`docs/`,
`progress/`, `specs/`):

- GUID: `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`,
  `azurestaticapps`, `azurewebsites` y los nombres de host de producción.
  Resultado: **0**.
- Correos: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}`. Resultado: todos en
  `ejemplo.invalid` (13 distintos). El único otro acierto es
  `@pytest.mark.parametrize`.
- DNI, NIF y teléfono: `\b[0-9]{8}[A-Z]\b`, `\b[A-Z][0-9]{7}[0-9A-Z]\b`,
  `\b[6789][0-9]{8}\b` y `\+34`. Resultado: **0**.
- IP: `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` en las líneas añadidas. Resultado:
  **0**.
- Obras: solo `9901`, `9902` y `9903`. Los códigos de catálogo `0002`,
  `0003`, `0005`, `0011`, `0021`, `0024` y `0143` los contrasté con
  `docs/referencia/04_alta_incidencia_sigrid.md` §2–§4, y `1 · Escrita` con
  `azure-apps/sigrid_api.md` (fila `forma_comunicacion`, «defecto 1
  "Escrita"»). Son reales, como pide D-10.
- `docs/ARCHITECTURE.md`: el recuadro de la fila «Entra ID» nombra el grupo
  `posventa-usuarios` y **no lleva ningún identificador**. Lo dice él mismo
  y lo confirma el barrido.

### C3 bis — Documentos que entran de fuera
- [x] **N/A justificado**: F-035 no añade ni modifica nada en
      `docs/referencia/` (`git diff --name-status` sin esa ruta).

### C4 — La verificación es real
- [x] Cada requisito tiene al menos un test trazable. Conteo por `f035[_ ]rN`
      en los cuatro ficheros de test: los 47 cubiertos, entre 1 y 9 tests
      cada uno (tabla abajo). Todos pasan. **Pero** R4, R6 y R7 solo están
      cubiertos a nivel de la función pura, no del componente: ver H-R1.
- [x] Los unit tests no tocan red ni BBDD. El componente se prueba con un
      `window` falso cuyos `fetch` y `XMLHttpRequest` lanzan. Git se usa en
      local, en solo lectura (R30, R32 y R33).
- [x] Las MANUAL están listadas: V1 y V2 (T12) en `current.md`, con el guion
      y las URL en `impl_F-035.md` §5 del bloque 4. V4 está en
      `requirements.md` §3 y `tasks.md` (tras el cierre, D-4). Pendientes del
      humano.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado y válido.
- [x] **Fase RED**: salidas reales pegadas en `impl_F-035.md`. Bloque 2 (T2
      a T4): 72 fallos en JS con el nombre de cada test, 34 en el front y 7
      en la raíz. Bloques 3a y 3b: qué pasó a verde con cada tarea, con las
      trazas. Bloque 4: R36 y R37. Cubre los requisitos centrales (R4–R7,
      R9–R18, R30–R33, R43–R45).
- [x] **Cobertura**: `N/A` con el motivo impreso por `init.sh` («no cambia
      líneas Python de producción frente a dev»). Es legítimo: los únicos
      `.py` del diff son tests.
- [x] **Mutación**: `progress/mutacion_F-035.md` generado por la herramienta.
      Alcance y nº de mutantes recalculados por mí: 0 y 0, coinciden. Prueba
      de control del cero hecha (176 mutantes sin la exclusión): **el cero es
      legítimo**.
- [x] **Muertos comprobados**: el «Tiempo total» es 0,0 s, menos de 5 min,
      así que **reejecuté la campaña entera** en el scratchpad. Totales
      idénticos. Árbol limpio.
- [x] **Coste por mutante**: **N/A justificado**. Con 0 mutantes no hay
      cociente que calcular, y la campaña no ejecuta ninguna suite. La
      sospecha que esta regla vigila (una suite que no corre) la descarta el
      control del cero y la ejecución real de las suites que hice yo.
- [ ] **Supervivientes analizados**: la campaña de la herramienta no deja
      ninguno, y las 8 mutaciones a mano de `design.md` §11 murieron las 8
      (las trazas pegadas son coherentes con los tests que existen). **Pero
      D-9 hace de las mutaciones a mano la compensación de la mutación en
      JS**, y esa compensación deja sin mirar el cableado del componente. Mis
      mutaciones encuentran **10 supervivientes sin analizar**. Al menos
      nueve no son equivalentes, y cinco caen sobre un requisito central. Es H-R1 y H-R2.
      *Sobre P-3 (comprobar numéricamente el motivo de cada equivalente): el
      implementer no declara ningún equivalente, así que no hay motivo que
      comprobar. Los que yo he encontrado **no** son equivalentes; los he
      ejecutado (ver H-R1).*
- [x] Sección «Evidencias» con los números: tests (294, 398 y 69),
      cobertura N/A con su motivo, mutantes (0 de la campaña y 8/8 a mano),
      workers (1) y tiempo de las suites.
- [x] Ningún N/A de este bloque sin justificación escrita.

### C4 ter — Rutas sensibles
- [x] **N/A justificado**: el repositorio no declara
      `harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`), y la
      puerta de `init.sh` no señaló nada.

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T1 a T11, T9 bis y T13 están `[x]`, y hay un commit
      `F-035 Tn:` por tarea (`b28b9aa` T1 … `f5634ea` T13, más los informes).
      **T12 sigue `[ ]` con justificación**: es `MANUAL (humano)` (V1 y V2) y
      por definición no la cierra un agente. Las dos premisas tachadas (T8 y
      T9 antiguas) se conservan como acta.
- [x] Sin ficheros temporales ni sin trackear (`git status
      --untracked-files=all` vacío).
- [x] `features.json`: F-035 `in_progress`, que es su estado real.

## Cobertura: requisito → test

Todos en `services/postventa-front/tests/test_f035_portal.py` (py),
`tests_js/portal.test.js` (js), `tests_js/maqueta_datos.test.js` (datos) o
`tests/test_f035_placeholders_vivos.py` (raíz).

| Req. | Tests (nº) | Nota |
|---|---|---|
| R1, R42 | py `r1_el_portal_es_index_html…`, `r42_el_circuito_monta…`, `r42_la_raiz_del_dev_server_sirve_el_portal` | |
| R2 | js ×2 | |
| R3 | py ×2 | |
| R4 | js ×4 (`resolverRuta`) | **Solo la función pura**: el componente no (H-R1) |
| R5 | js ×2, incluido `#/partes` → inicio | Mutante de `resolverRuta` muerto |
| R6 | js ×2 (`resolverRuta` y `buscarPorId`) | **Componente sin probar** (H-R1) |
| R7 | js ×1 (`resolverRuta`) | **`avisoRuta` del componente sin probar** (H-R1) |
| R8 | js ×4 | |
| R9 | py ×2, js ×2 (ficha del `data-placeholder` = la del catálogo) | |
| R10 | py ×1 | |
| R11 | py ×1, js ×2 | |
| R12 | js ×4 | Singular «1 incidencia» sin probar (H-R2) |
| R13 | py ×2 | |
| R14 | py ×5 (uno por fichero de la maqueta) | |
| R15 | py ×1 | |
| R16 | js ×2 (dobles que lanzan) | |
| R17 | py ×1 | |
| R18 | py ×5 | |
| R19 | js ×5 | |
| R20 | js ×2 | |
| R21 | js ×3 | |
| R22 | js ×3 | `undefined` y negativos sin probar (H-R2) |
| R23–R26 | datos ×2, ×5, ×1, ×2 | |
| R27–R29 | raíz ×2, ×2, ×1 | Mutación 5 (F-044 en `done`) muerta |
| R30, R43 | py `r30_r43_partes_html_es_el_index_de_la_base…` (difflib contra `merge-base`), `r43_…nueve_scripts` | |
| R31 | py ×1, js ×1 | |
| R32, R33 | py ×1 cada uno | Se saltan fuera de `feature/F-035…` (diseño §11) |
| R34, R35 | py ×1 cada uno | |
| R36, R37 | py ×1, raíz ×2 | |
| R38–R41 | py ×2 y datos (R38 ×4, R39 ×4, R40 ×9, R41 ×1) | |
| R44 | js ×5 (cruce de los `href` de las dos barras con `enlaceSeccion`) | |
| R45 | py ×1 | Mutación 7 muerta; yo quité `target` y `rel` en dos enlaces: muertas |
| R46, R47 | py ×1 cada uno | |

## Despliegue (lectura del código y la configuración; no se despliega nada)

- **Autenticación.** `staticwebapp.config.json` no cambia: `/*` exige
  `authenticated`, y `/`, `/index.html` y `/partes.html` no caen en ninguna
  otra regla (lo prueba R35 y lo he leído). El 401 lleva a
  `/.auth/login/aad`. La asignación obligatoria de la aplicación en Entra
  no cambia.
- **Qué se publica.** `infra/desplegar_front.ps1` copia **el directorio
  entero** del front y solo retira `tests`, `tests_js`, `__pycache__`,
  `dev_server.py`, `dev_front.ps1` y `coverage.json`. `partes.html`,
  `js/portal*.js`, `js/maqueta_datos.js` y `css/portal.css` se publican sin
  tocar el script.
- **Rutas.** El circuito llama al backend por rutas absolutas (`/api`,
  `/.auth/me`: `js/config.js` y `js/api.js`), así que servirse desde
  `/partes.html` en vez de `/` no cambia ninguna petición. Desde el
  circuito, `./#/<id>` se resuelve a `/#/<id>` (el portal), en otra pestaña.
  En local, `dev_server.py` sirve estáticos del directorio: `/` da
  `index.html` (probado por R42) y `/partes.html` se sirve tal cual.
- **La tarjeta del portal corporativo.** La he leído en
  `front-portal/public/assets/js/catalog.js`, en solo lectura: su `url` es la
  **raíz** de la Static Web App, sin ruta. Con D-3 aterriza en el portal,
  como documenta `docs/DESPLIEGUE.md` §6. El título y la descripción siguen
  hablando solo del circuito. La propuesta para cambiarlos al publicar está
  bien encauzada como trabajo de `front-portal`.
- **Riesgo que queda, ya documentado** (`design.md` §12, V4 c): quien abra
  `/partes.html` sin sesión vuelve a `/` tras el login, porque la regla 401
  no lleva `post_login_redirect_uri`. Aterriza en el portal, a un clic del
  circuito. No es peor que hoy, porque antes también volvía a `/`.
- **`azure-apps/`.** D-8 («no se toca») se sostiene: `postventa_incidencias.md`
  no nombra `index.html` ni describe rutas del front, y no cambia ningún
  endpoint, tabla, variable ni grupo.

## Decisiones del implementer fuera de la spec

1. **Botón «Entendido» del aviso de placeholder**: **se sostiene.** No
   cierra el aviso de maqueta de R13, que sigue sin botón (probado por
   `r13_el_aviso_de_maqueta_esta_siempre_y_no_se_cierra`): cierra la franja
   **fija** del aviso de R11, que sin temporizadores (§6.2) taparía el pie
   de la página para siempre. Es `data-local` (cumple R10). La región
   `role="status"` sigue siempre presente. Observación menor: es la única
   asignación escrita en el HTML (`@click="aviso = ''"`). Un método
   `cerrarAviso()` sería más coherente con §8.2, pero no es bloqueante.
2. **Acciones por fila en el panel de detalle**: **se sostiene.**
   `design.md` §5.2 dice «acciones por fila», y siguen siendo de la fila.
   El argumento es sólido: 32 botones rayados en la tabla no se leen, y un
   placeholder dentro de una fila pulsable abriría también el detalle. Que
   Posventa lo valide en V3.
3. **Oficios limitados a los cinco documentados**: **se sostiene, y es lo
   correcto.** D-10 pide códigos reales de catálogo, y
   `04_alta_incidencia_sigrid.md` solo documenta código y resumen de `0005`,
   `0011`, `0021`, `0024` y `0143`. `0046` aparece sin resumen propio. Usar
   el «Fontanería» de ejemplo de `design.md` §5.3 habría obligado a
   inventarse un código.

## Hallazgos

### H-R1 · MEDIA · bloqueante · el cableado de rutas del componente no lo ve ningún test

**Dónde:** `services/postventa-front/js/portal_app.js`, líneas 56–68
(`iniciar()` y `aplicarRuta()`), frente a
`services/postventa-front/tests_js/portal.test.js`, líneas 225–229
(`navegar`, «*si* el componente escucha `hashchange`») y 730–778: los tests
del componente navegan, pero solo afirman `llamadas == []` (R16) y la
selección (R20), **nunca** `c.seccion`, `c.incidenciaAbierta` ni
`c.avisoRuta`.

**Evidencia (ejecutada** en una copia desechable, sustitución de bytes con
exactamente una coincidencia, suites completas y restauración verificada con
`cmp`):

| Mutación en `portal_app.js` | JS | pytest del front |
|---|---|---|
| quitar `window.addEventListener("hashchange", () => this.aplicarRuta());` | 398/398 en verde | sin cambios |
| `this.seccion = ruta.seccion;` → `this.seccion = "inicio";` | 398/398 en verde | sin cambios |
| `this.incidenciaAbierta = ruta.incidencia;` → `= null;` | 398/398 en verde | sin cambios |
| `this.avisoRuta = ruta.aviso \|\| "";` → `= "";` | 398/398 en verde | sin cambios |
| `iniciar()` sin el `this.aplicarRuta()` inicial (un enlace profundo `#/bandeja` abriría inicio) | 398/398 en verde | sin cambios |
| `aplicarRuta` sin `this.panelNoProcede = false` | 398/398 en verde | sin cambios |

Las cinco primeras **no son equivalentes**. Con cualquiera de ellas, la
navegación del portal deja de funcionar en el navegador: ninguna pestaña
cambia de sección, no se abre ninguna ficha o no sale el aviso de R7. Y la
suite no se entera. `resolverRuta` está bien probada, pero R4 dice «**el
portal** debe mostrar ese bloque», y lo que lo muestra es el componente.

**Por qué bloquea:** el primer criterio de la ficha es que las secciones
«**se navegan**», y D-9 hace de las mutaciones a mano la compensación de la
mutación en JS. Una compensación que no mira la única pieza con estado no
compensa. Hoy lo único que lo cazaría es V1, sin ejecutar.

### H-R2 · BAJA · supervivientes de la lógica pura sin analizar

Todos **ejecutados**. Ninguno es equivalente para el contrato de la función,
aunque con los datos de ejemplo actuales no se vea:

- `formatoImporte`: quitar el signo (`(numero < 0 ? "-" : "") +`) sobrevive.
  Con los datos de hoy no se nota: las diferencias venta menos coste de
  `capitulos` son 250, «sin enlazar» y 0. Pero la columna «Diferencia» de
  `index.html`, línea 874, calcula `c.venta - c.coste`, que sale negativa en
  cuanto la venta es menor que el coste. Comprobado:
  `formatoImporte(-250)` da `-250,00 €` y con la mutación da `250,00 €`.
- `formatoImporte`: tratar solo `null`, y no `undefined`, como ausente
  sobrevive. R22 dice «valor ausente». Hoy los datos traen `null` explícito,
  pero un campo que falta es `undefined` y saldría `NaN,undefined €`.
- `formatoImporte`: quitar la guarda `Number.isFinite` sobrevive (misma
  salida `NaN,undefined €` con un valor no numérico).
- `textoPlaceholder`: `n === 1` → `n === 0` sobrevive, porque solo se prueba
  con 2 y 3. Con la mutación saldría «afectaría a 1 incidencias.».

Las otras 22 mutaciones (de la lógica pura, del HTML de las dos páginas y
de los datos) murieron.
Mataron esas mutaciones R5, R6, R9, R12, R19 (×3), R20, R21, R22 (miles),
R24, R31, R39, R40 (×2), R44 (×4) y §5.1.

## Cambios requeridos

1. **`services/postventa-front/tests_js/portal.test.js`: probar el cableado
   de rutas del componente (R4, R5, R6, R7)**, con el `conVentanaFalsa` y el
   `navegar` que ya existen:
   - (a) tras `navegar(c, oyentes, "bandeja")`, `c.seccion === "bandeja"`;
   - (b) tras `navegar(c, oyentes, "incidencias", <id de ejemplo>)`,
     `c.seccion === "incidencias"` y `c.incidenciaAbierta === <id>`;
   - (c) tras `navegar(c, oyentes, "incidencias", "EJ-9999")`,
     `c.avisoRuta === "Esa incidencia no existe en los datos de ejemplo"` y
     `c.incidenciaAbierta === null`;
   - (d) tras `navegar(c, oyentes, "partes")`, `c.seccion === "inicio"`;
   - (e) que `iniciar()` **se suscribe** a `hashchange`
     (`oyentes.hashchange` con al menos un oyente) y que, con
     `location.hash = "#/bandeja"` **antes** de `iniciar()`, el componente
     arranca en `bandeja` (enlace profundo).

   Comprobación: las cinco primeras mutaciones de la tabla de H-R1 tienen
   que ponerse en rojo. Pega sus trazas en el informe, en una copia aislada
   y nunca en el árbol. La sexta (`panelNoProcede`) puede quedarse
   documentada como superviviente con su análisis si no se quiere probar.
2. **`tests_js/portal.test.js`, R22 y R12**: añade los casos
   `formatoImporte(undefined) === "sin enlazar"`,
   `formatoImporte(-250) === "-250,00 €"` y un valor no numérico →
   «sin enlazar», y `textoPlaceholder(<en bloque>, { seleccionadas: 1 })`
   que acabe en «1 incidencia.». Si alguno se decide no probarlo, documéntalo
   en el informe como superviviente con su análisis, nunca en silencio.
3. **`progress/impl_F-035.md`**: una sección corta con las mutaciones de
   los puntos 1 y 2, sus trazas y, si queda alguna viva, su análisis.
   Después, `bash harness/init.sh` en verde.

No hace falta tocar código de producción, ni `partes.html`, ni los tests del
circuito.

## Observaciones sin acción (no bloquean)

- **O-1**: `docs/ARCHITECTURE.md`, tabla del mapa, pone `F-045` en la fila
  `incidencias`, pero `Portal.SECCIONES` (probado contra `design.md` §4) no
  lo lista ahí. Es coherente con el placeholder `ficha.registrarSinFirma` y
  el implementer lo avisó (informe §2.3). Si molesta, basta una nota al pie.
- **O-2**: `current.md` sigue acumulando histórico (deuda previa, ver C2).
- **O-3**: el «Entendido» podría ser un método del componente (ver
  «Decisiones fuera de la spec», 1).

## Automejora (propuesta, no aplicada)

**P-R1 · `CHECKPOINTS.md` C4 bis y `.claude/agents/reviewer.md`, para
`arnes-base` (vale para cualquier proyecto con front en JS).** Cuando la
mutación de un lenguaje no la cubre la herramienta y se compensa con
mutaciones a mano, el conjunto de mutaciones a mano debe incluir **al menos
una por cada asignación de estado del «pegamento»** (el componente o
controlador que une la lógica pura con la pantalla: suscripciones a eventos
y copias del resultado de la función pura al estado). Motivo: las
mutaciones a mano tienden a atacar la lógica pura y las guardias estáticas,
que ya están bien probadas, y dejan sin mirar el cableado, que es justo lo
que un test de lógica pura no ve. Caso de origen: F-035, H-R1, con cinco
mutaciones que rompen la navegación y dejan 398/398 en verde.
