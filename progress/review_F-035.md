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

---

## Review del bloque 7 (reanudación) · T23–T24 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 56b90b0..HEAD` (`bdf8747` T23,
> `baa3317` T24) en `feature/F-035-portal-posventa`. Las tareas de los demás
> bloques de la enmienda (8 → 16 → 17 → 9 → … → 15) siguen abiertas **a
> propósito**: no cuentan como `[ ]` de esta review.

### Veredicto

**APPROVED** (del bloque 7, no de la feature). El bloque hace lo que pide
T23/T24: retira del portal todo lo que la maqueta tenía de F-036, `entrada`
enlaza en la misma ventana a `importar.html` y `oficios.html`, `init.sh`
vuelve a verde sin tocar la guarda R28, y no se toca ni el circuito ni F-036.
La fase RED es real (reproducida) y las mutaciones 14 y 15 del diseño mueren.
Quedan cinco hallazgos **menores**, cada uno con destino en un bloque ya
planificado (abajo); ninguno deja un checkbox vacío.

### Nivel de rigor

`estandar` (declarado en `harness/features.json`). Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con supervivientes analizados.
F-035 no tiene Python de producción: la cobertura sale N/A con motivo impreso
y la campaña da 0 mutantes; la compensación son las mutaciones a mano de
`design.md` §16.10 (14 y 15 en este bloque) más las del reviewer.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, árbol real) | **exit 0**, `ENTORNO LISTO`. Raíz 107 passed; api y front en verde (caché: árbol sin cambios desde el último verde); `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos, deuda previa |
| Front en un worktree desechable del scratchpad (HEAD `baa3317`, sin caché) | pytest **417 passed, 3 skipped** (los 3 son los del diff de rama, saltados por HEAD separado); Node **499 pass, 0 fail**; raíz `tests/test_f035_placeholders_vivos.py` **11 passed** |
| **RED reproducido**: tests nuevos de `baa3317` sobre `index.html`, `js/portal.js` y `js/maqueta_datos.js` de `56b90b0` | **7 failed, 6 passed**, los mismos 7 tests y mensajes que pega el informe (§3); los 6 que pasan son los controles del detector y del lector de `PAGINAS` |
| Ruff sobre `test_f035_paginas.py` y `test_f035_portal.py` | `All checks passed!` |
| Recálculo de la mutación: `harness.alcance.alcance_de_feature("F-035", base="2a86bca")` | 0 ficheros, 0 líneas de producción: coincide con `progress/mutacion_F-035.md` |
| **Reejecución de la campaña** («Tiempo total» 0,0 s < 5 min): `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900 --salida <scratchpad>` | 0 generados, 0 muertos, 0 supervivientes, 0 timeouts, 0,0 s: **idéntico** al informe. `git status` limpio después |
| **Control del cero**: `generar_mutantes` sobre los `.py` del diff ignorando la exclusión de alcance | `test_f035_paginas.py` 15 y `test_f035_portal.py` 5 mutantes: el generador funciona y el cero es **legítimo** (en el diff solo hay tests, excluidos por diseño) |
| «F-036 intacto»: `git diff 2a86bca -- …test_f036_front.py …importacion.test.js …oficios.test.js` | vacío (0 líneas) |
| R76: `git diff --name-status 2a86bca..HEAD -- services/postventa-api` | vacío |
| Circuito y F-036: `git diff --name-status 56b90b0..HEAD --` `partes.html`, `importar.html`, `oficios.html`, `js/app.js`, `js/api.js`, `js/importacion.js`, `js/oficios.js`, `css/` | vacío |
| `git show --stat bdf8747` | exactamente los 7 ficheros de (a)–(e) de T23 |
| `git worktree list` / `git status` al acabar | solo el árbol real y el worktree ajeno `agent-a6e2f9bed1d46cdbc` (no se toca); árbol limpio |

Nota sobre la cabecera de `progress/mutacion_F-035.md`: dice `--workers 1`
aunque el comando tecleado no lo llevaba. Lo escribe la herramienta
(`comando_de` pone los workers efectivos; con 0 mutantes, 1). No es un
informe a mano: la reejecución da los mismos totales.

### Respuestas a las preguntas del líder

**1 · ¿Quedan restos de F-036 que la guarda R28 no vea?** De **maqueta**
(placeholders, bloques de `MaquetaDatos`, directivas `datos.entrada`, ids del
catálogo, título en `TITULOS_FICHAS`): **ninguno**. Barrido propio de
`index.html`, `js/portal.js`, `js/maqueta_datos.js` y `js/portal_app.js` por
`F-036`, `Excel`, `importa`, `soltar`, `oficio`, `plantilla`, `duplicad` y
`entrada.`. Lo que aparece y **es legítimo**: `SECCIONES` (`entrada` con
`fichas: ["F-036", "F-037"]`, el catálogo de la sección, que R62 usará en el
bloque 8); la fila del datamart (`fichas: ["F-036", "F-038"]`, dato de F-048:
su «pendiente» es la publicación en el datamart, que sigue sin existir); el
comentario de `BJ-0006` («Duplicada de BJ-0005 (F-036)») y los
`origen: "Excel"` de la bandeja (datos de F-038). Lo que **no** es maqueta
pero sí **texto que contradice que F-036 esté en producción**, y que ni R28
ni R68 ven: H-4 (tres textos) y H-5 (CSS muerto).

**2 · ¿El enlace de `entrada` cumple R17 enmendado y no rompe R14/R18?**
Sí. Los dos `<a>` van a `importar.html` y `oficios.html`, **sin `target` ni
`rel`**: misma ventana (comprobado en el HTML y con las mutaciones A, B, F y
R). R14 (primitivas de red) y R18 (almacenamiento) siguen en verde: el cambio
no añade ningún script ni atributo ligado, solo dos `href` estáticos. El test
de R17 se endureció bien (además de admitir `PAGINAS` con ancla opcional,
exige que **ningún** `<a>` del portal lleve `target`); su única grieta es la
forma ligada `:target`, ver H-1.

**3 · ¿Se ha tocado la lógica del circuito o de F-036?** **No.** Ni
`partes.html`, ni ningún `js/` del circuito, ni `js/importacion.js`,
`js/oficios.js`, `js/api.js`, ni `importar.html`/`oficios.html`, ni `css/`,
ni sus tests (diffs vacíos, tabla de arriba).

**4 · `tests/test_f035_paginas.py` (R68): ¿RED real y mata lo que dice?**
**Sí** a las dos. RED reproducido con el código de `56b90b0` (7 rojos, los
mismos mensajes). Mutaciones a mano del reviewer en un worktree desechable
del scratchpad (`git worktree add --detach`, retirado con
`git worktree remove --force`; árbol real limpio), con la suite **entera** del
front + la guarda de la raíz por mutación (+ Node cuando la mutación es JS):

| # | Mutación | Resultado | Lo caza |
|---|---|---|---|
| A | `target="_self"` en la tarjeta de importar | muerto | R68[importar], R17 |
| B | `target="_blank" rel="noopener"` en la de oficios | muerto | R68[oficios], R17 |
| C | `target="_blank"` en el paso 06 del recorrido (`partes.html`) | muerto | R17, R46 |
| D | La tarjeta va a `importar.html#bandeja` | muerto | R68[importar] |
| E | `PAGINAS` gana `"otra.html": "entrada"` | muerto | R17 `…declara_las_paginas_reales…` y `…cada_pagina…existe` |
| F | `href="./importar.html"` | muerto | R68, R17 |
| G | Chip de oficios «En construcción» | muerto | R68[oficios] |
| H | Chip de importar `rs-chip--neutro` | muerto | R68[importar] |
| I | Frase de oficios cambiada | muerto | R68[oficios] |
| J | `<span class="rs-ficha">F-036</span>` estático en el `h1` | muerto | R29 (`CHIPS_DE_FICHA`) |
| K | `<dl>` estático con «Filas leídas 8 · Duplicadas 1» en `entrada` (sin `datos.`) | **sobrevive** | — (H-3) |
| L | `<button class="placeholder">Elegir el Excel</button>` sin `data-placeholder` | muerto | R10 |
| M | `"F-036"` vuelve a `TITULOS_FICHAS` | muerto | detector de R68 |
| N | `importacion: { ficha: "F-036" }` en `MaquetaDatos` (otro nombre de bloque) | muerto | detector de R68 y R28 de la raíz (+ su control) |
| O | Se cambia el título «Web de clientes» | muerto | R68, panel web |
| P | La tarjeta de oficios va a `#/datos` | muerto | R68[oficios] |
| Q (= manual 14) | Vuelve `data-placeholder="F-036"` con `entrada.importar` | muerto | R28 de la raíz (+ control), R68 ×2, R9, F-007 R32 (suite JS) |
| R (= manual 15) | Tarjeta de oficios a `otra.html` | muerto | R17, R68[oficios] |
| S | `:target` ligado (`_blank`) en la tarjeta de importar | **sobrevive** | — (H-1) |
| T | `@click.prevent` con `window.open(…)` en la tarjeta de oficios | **sobrevive** | — (H-2) |

17 de 20 muertas; las 3 vivas, analizadas en H-1, H-2 y H-3. Ninguna es de
las que el diseño fija para este bloque (14 y 15, muertas) y las tres tienen
destino en un bloque ya planificado; por eso no bloquean.

**5 · CHECKPOINTS aplicables:** a continuación.

### Checkpoints (acotados al bloque)

**C1**
- [x] `init.sh` exit 0 (ejecutado por el reviewer).
- [x] Ficheros del arnés presentes (`init.sh` los da en `[OK]`).

**C2**
- [x] Una sola feature `in_progress` (F-035; `init.sh`).
- [x] Rama `feature/F-035-portal-posventa`.
- [x] `current.md`: la entrada nueva describe el bloque y su siguiente paso.
  Sigue acumulando histórico de la feature (deuda previa, O-2 de la review
  anterior); no lo introduce este bloque.
- [x] Features `done` con resumen en `history.md`: este bloque no cierra
  ninguna.

**C3**
- [x] Hexagonal: el diff es HTML, JS de la maqueta y tests del front; no toca
  `domain/` ni adaptadores, así que no hay frontera que romper.
- [x] Primera línea con ruta: `test_f035_paginas.py` (`# services/…`); los
  demás ficheros conservan la suya.
- [x] Sin `print()`, sin TODOs, sin secretos, sin dependencias nuevas
  (`test_f035_paginas.py` importa de `test_f035_portal.py`, con el precedente
  `test_f036_front.py` → `test_f007_estaticos.py`).
- [x] Parte como unidad, validaciones antes de archivar/cerrar, manuscrito,
  firmado ≠ conforme, reprocesar no duplica, `conest`: **N/A justificado**:
  el bloque no toca el circuito ni el backend (diffs vacíos arriba) y ninguno
  de esos invariantes vive en los ficheros cambiados.
- [x] Ningún PDF ni parte en git: `git log --diff-filter=A 56b90b0..HEAD`
  añade solo `services/postventa-front/tests/test_f035_paginas.py`.

**C3 bis** — **N/A**: el bloque no añade ni modifica nada en
`docs/referencia/`.

**C4**
- [x] R68 y R17 enmendado con tests trazables (`test_f035_r68_*`,
  `test_f035_r17_*`) en verde; R28 con su control, en verde.
- [x] Sin red ni BBDD: los tests leen ficheros como texto (`html.parser` y
  regex).
- [x] MANUAL (humano): este bloque no añade ninguna; las de la enmienda (V1,
  V2, V4, V5) están en la spec para el bloque 15.

**C4 bis**
- [x] `rigor: "estandar"` declarado.
- [x] Fase RED: traza real en el informe (§3) **y reproducida** por el
  reviewer (7 rojos).
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh` (sin líneas
  Python de producción frente a `dev`; JS y HTML no se miden).
- [x] Mutación: `progress/mutacion_F-035.md` generado por la herramienta;
  alcance y nº de mutantes recalculados (0/0) y control del cero hecho.
- [x] Muertos comprobados: campaña **reejecutada** (0,0 s < 5 min), totales
  idénticos.
- [x] Coste por mutante: N/A **justificado**: 0 mutantes, no hay división
  posible; la compensación son las mutaciones a mano.
- [x] Supervivientes: 0 de la herramienta; de las manuales, 14 y 15 muertas y
  las tres vivas del reviewer analizadas (H-1, H-2, H-3). Nivel `estandar`:
  no exige aceptación escrita del humano.
- [x] «Evidencias» del bloque con los cuatro números (workers: 0 mutantes,
  la cabecera dice 1).
- [x] Ningún N/A sin justificar.

**C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] T23 y T24 `[x]`, con sus commits `F-035 T23: …` y `F-035 T24: …`. El
  resto de `tasks.md` sigue abierto **a propósito** (bloques 8–17 de la
  enmienda).
- [x] Sin ficheros sin trackear (`git status` limpio).
- [x] `features.json`: F-035 `in_progress`, correcto con la feature a medias.

### Cobertura del bloque: requisito → test

| Requisito | Test |
|---|---|
| R68 (enlaces, misma ventana, chip, frase) | `test_f035_r68_entrada_enlaza_a_la_pagina_real_en_la_misma_ventana[importar.html]` y `[oficios.html]` |
| R68 (nada de F-036 en el portal) | `test_f035_r68_no_queda_en_el_portal_nada_de_f036` + `…_control_el_detector_ve_cada_resto_de_f036` ×5 |
| R68 (sigue la web de clientes) | `test_f035_r68_el_panel_de_la_web_de_clientes_sigue_en_entrada` (el envoltorio F-037 es del bloque 9) |
| R17 enmendado | `test_f035_portal.py::test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito`; `test_f035_r17_portal_paginas_declara_…`, `…_cada_pagina_de_portal_paginas_existe`, `…_control_paginas_del_portal_lee_…` |
| R28 | raíz `tests/test_f035_placeholders_vivos.py` (y su control), en verde |

### Hallazgos

1. **H-1 · menor · El test de R17 no ve un `target` ligado.** En
   `services/postventa-front/tests/test_f035_portal.py`,
   `test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito`,
   `assert "target" not in a.atributos` solo mira el atributo literal:
   `:target="…"` o `x-bind:target="…"` pasan (mutación S). El mismo test ya
   trata `:href` y `x-bind:href`, así que es una incoherencia de una línea.
   Lo mismo en `services/postventa-front/tests/test_f035_paginas.py:132`.
   **Arreglo**: recorrer `("target", ":target", "x-bind:target")` en los dos.
   **Destino**: bloque 8 (T25 (f) ya toca `test_f035_portal.py`) o, como
   tarde, las guardias de R73 del bloque 10.
2. **H-2 · menor · «Misma ventana» no ve un `window.open`.** Un
   `@click.prevent` con `window.open(…)` en una tarjeta abre otra ventana con
   el `href` intacto y nada cae (mutación T). `window.open` no está en la
   lista de R14, que es de red, no de navegación. **Destino**: la lista
   cerrada de R73 (bloque 10, `design.md` §16.10) debería incluir
   `window.open` en `index.html`, `importar.html` y `oficios.html`; el
   bloque 16 (guarda de salida) es el otro sitio natural. Lo decide el
   líder; no es de este bloque.
3. **H-3 · menor · El detector de R68 es por patrones.** Datos de ejemplo
   escritos a mano en `entrada`, sin `datos.` ni `data-placeholder` (un
   `<dl>` con «Filas leídas 8»), pasan (mutación K). La spec define «bloque
   de datos de ejemplo» como bloque de `MaquetaDatos`, así que el test cumple
   la letra; lo que falta es fijar la **estructura cerrada** de `entrada`.
   **Destino**: bloque 9 (T27), cuando entre el envoltorio
   `data-en-construccion="F-037"`: que R68 exija que `entrada` contenga solo
   la cabecera, la rejilla de las dos tarjetas y el envoltorio F-037.
4. **H-4 · menor · Textos visibles que siguen diciendo que solo funciona el
   circuito.** Ni R28 ni R68 los ven y ninguno es de este bloque, pero el
   líder pidió buscarlos:
   - `services/postventa-front/index.html:78`, en el aviso: «El circuito de
     verdad es la pestaña «Partes firmados».» → R13 enmendado, **bloque 8**
     (T25 (e)).
   - `index.html:87` («Posventa · maqueta del ciclo») y `index.html:92`
     («lo único que funciona de verdad es el circuito de partes firmados»),
     más los chips «Maqueta» de las tarjetas de `inicio` → R67, **bloque 9**.
   - `services/postventa-front/js/maqueta_datos.js:129`, pendiente del bloque
     `web` (F-037): «bloqueado por la web de clientes **y por la importación
     del Excel**», que ya existe. **Ningún bloque lo recoge**: T23 y R68 piden
     el panel «tal cual». Lo apuntó el implementer. **Decisión del
     líder/humano**: quitar «y por la importación del Excel» en el bloque 9
     (cuando ese panel entra en su envoltorio), con una nota en T27.
5. **H-5 · nit · CSS muerto tras T23.** En
   `services/postventa-front/css/portal.css` quedan sin uso en las cuatro
   páginas: `.rs-encabezado` (l. 450), `.rs-acciones--centro` (l. 498),
   `.rs-soltar` y `.rs-soltar__texto` (l. 509–520) y
   `.rs-cifras--compactas` (l. 997). El implementer no tocó el CSS para no
   mover la `?v=`, lo que es razonable en este bloque. **Destino**: bloque 9,
   T27 (d), que ya toca `portal.css` y la `?v=`.

### Observaciones sin acción

- **O-1**: `SECCIONES.entrada.fichas` conserva `F-036`; es el catálogo de la
  sección, no un resto (el escáner de R28 no lo cuenta, y R62 del bloque 8 le
  pondrá estado). Correcto.
- **O-2**: la cabecera de `progress/mutacion_F-035.md` (`--workers 1`, sin
  `--timeout`) no coincide con el comando del informe; la escribe la
  herramienta con los valores efectivos. Correcto.

### Qué queda para el humano

- Nada que decidir para cerrar el bloque 7.
- Para el líder (y el humano si quiere): el texto de `maqueta_datos.js:129`
  (H-4, tercer punto), que hoy no recoge ningún bloque, y si `window.open`
  (H-2) entra en la lista cerrada de R73. H-1, H-3 y H-5 tienen ya bloque de
  destino; conviene que el líder los cite en el encargo de ese bloque.

### Automejora (propuesta, no aplicada)

**P-R2 · `CHECKPOINTS.md` C4 bis, para `arnes-base` (vale para cualquier
front con un framework reactivo: Alpine, Vue).** Cuando una guarda estática
prohíbe o exige un **atributo HTML** (`target`, `href`, `disabled`…), las
mutaciones a mano deben incluir **la forma ligada** del atributo (`:attr`,
`x-bind:attr`, `v-bind:attr`): `html.parser` la ve como otro nombre de
atributo y una guarda literal no la caza. Caso de origen: F-035, bloque 7,
H-1 (mutación S).

## Review del bloque 8 · T25–T26 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff dd67d48..HEAD` (`023b7a5` T25,
> `0a6819f` T26) en `feature/F-035-portal-posventa`. Los bloques que vienen
> (16 → 17 → 9 → … → 15) siguen abiertos **a propósito**: no cuentan como
> `[ ]` de esta review. La primera pasada se cortó por un error de la API
> (529); se retomó desde cero: el árbol estaba limpio y no quedaba ninguna
> mutación aplicada ni ningún worktree mío.

### Veredicto

**APPROVED** (del bloque 8, no de la feature). T25 y T26 hacen lo que piden:
`estado` literal en las ocho entradas de `Portal.SECCIONES` y
`Portal.enConstruccion`; la guardia R62 en la raíz contra `features.json`,
con su control de F-038; R66 en las dos barras que existen hoy; el punto
ámbar con tokens; el aviso de R13 enmendado. No se toca la lógica del
circuito ni F-036. La fase RED es real (reproducida) y las mutaciones 16 y
17 del diseño mueren. Quedan dos hallazgos **menores** de prueba (H-6, H-7)
y uno **de spec** (H-8), con destino; ninguno deja un checkbox vacío.

### Nivel de rigor

`estandar` (declarado en `harness/features.json`). Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con supervivientes analizados.
F-035 no tiene Python de producción: la cobertura sale N/A con motivo impreso
y la campaña da 0 mutantes; la compensación son las mutaciones a mano de
`design.md` §16.10 (16 y 17 en este bloque), más las del implementer y las
del reviewer.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, árbol real) | **exit 0**, `ENTORNO LISTO`. Raíz **112 passed**; api en verde (caché); front **425 passed**; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos, deuda previa |
| Front en un worktree desechable del scratchpad (`git worktree add --detach`, HEAD `0a6819f`) | pytest **422 passed, 3 skipped** (los 3 del diff de rama, saltados por HEAD separado); Node **509 pass, 0 fail**; raíz `tests/test_f035_placeholders_vivos.py` **16 passed** |
| **RED reproducido**: tests de HEAD sobre `portal.js`, `index.html`, `partes.html` y `styles.css` de `dd67d48` | Raíz `-k r62`: **4 failed, 1 passed** (los mismos 4 del informe). Front `-k "r13 or r17 or r66 or r68"`: **2 failed, 18 passed** (R13 nuevo y el punto de R66). Node `f035_paginas.test.js`: **9 failed, 1 passed** (los 8 del informe más el de B8, que entró en T26; el que pasa es el control del lector) |
| H-1, RED por mutación: mutación S del bloque 7 (`:target` ligado en la tarjeta de importar) | **muerta** ahora: `test_f035_r17_los_enlaces_…` y `test_f035_r68_…[importar.html]`. En el bloque 7 sobrevivía |
| B8 del implementer (`enConstruccion` con `estado !== "parcial"`) | **muerta**: cae `f035 R62: enConstruccion sigue al estado…` (el test de T26) |
| Ruff sobre los tres ficheros de test tocados | `All checks passed!` |
| Recálculo: `harness.alcance.alcance_de_feature("F-035", base="2a86bca")` | `lineas={}`: 0 ficheros, 0 líneas; coincide con `progress/mutacion_F-035.md` |
| **Reejecución de la campaña** («Tiempo total» 0,0 s < 5 min), `--salida` al scratchpad | 0 evaluados, 0 muertos, 0 supervivientes, 0 timeouts, 0,0 s: **idéntico** al informe. `git status` limpio después |
| **Control del cero**: `generar_mutantes` sobre los `.py` del diff (líneas añadidas en `dd67d48..HEAD`) ignorando la exclusión | `test_f035_paginas.py` 5, `test_f035_portal.py` 4, `tests/test_f035_placeholders_vivos.py` 24: el generador funciona y el cero es **legítimo** (solo tests, excluidos por diseño) |
| «F-036 intacto»: `git diff 2a86bca --` `test_f036_front.py`, `importacion.test.js`, `oficios.test.js` | vacío (0 líneas) |
| R76: `git diff --name-status 2a86bca..HEAD -- services/postventa-api` | vacío |
| `git diff --name-status dd67d48..HEAD --` `js/`, `importar.html`, `oficios.html`, `css/portal.css` | solo `js/portal.js` (la maqueta: `estado` y `enConstruccion`); ningún módulo del circuito ni de F-036 |
| `git show --stat 023b7a5` | exactamente los ficheros de (a)–(f) de T25 más `tasks.md` |
| `git log --diff-filter=A dd67d48..HEAD` | añade solo `tests_js/f035_paginas.test.js` (ningún PDF ni parte) |
| Estado de las fichas en `features.json` | F-036 `done`; F-037 a F-048 `pending` |
| `git worktree list` / `git status` al acabar | worktree retirado (`git worktree remove --force` + `prune`); quedan el árbol real y el ajeno `agent-a6e2f9bed1d46cdbc` (no se toca); árbol limpio |

### Respuestas a las preguntas del líder

**1 · ¿Se cumplen R62 y R66? ¿Es correcto el estado de cada sección?**
**Sí.**

- **R62**: las ocho entradas llevan `estado` literal. Hoy `inicio`,
  `entrada` y `partes` están en `parcial`, y `bandeja`, `incidencias`,
  `impresion`, `economico` y `datos`, en `construccion`. Es justo lo que dan
  las fichas: F-036 está `done` y F-037 no, así que `entrada` es `parcial`;
  ninguna de F-038 a F-044, F-046, F-047 ni F-048 está `done`; F-045 sigue
  pendiente, así que `partes` es `parcial`; e `inicio` es `parcial` porque
  no todas las demás son reales. Coincide con la tabla de `design.md` §16.4
  y con el «Hoy:» de R62. La guardia de la raíz lo compara con
  `features.json` de verdad: con F-038 `done` **en el fichero** (mutación V8,
  abajo) cae `…_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas`.
  `enConstruccion` es `estado === "construccion"` y no lanza nunca.
- **R66**: en `index.html` y en `partes.html`, las **cinco** pestañas de las
  secciones en construcción llevan `data-construccion` y
  `aria-label="<etiqueta> (en construcción)"`, y ninguna otra lleva ninguno
  de los dos. «Partes firmados» (la `<span aria-current>` de `partes.html`)
  e «Inicio» y «Entrada» van sin marca. El nombre accesible contiene la
  etiqueta visible (WCAG 2.5.3). El punto ámbar es
  `.rs-pestana[data-construccion]::after`: 6 px, redondo y en
  `var(--rs-atencion)`. Se ve porque `.rs-pestana` es `inline-flex`, así
  que el `::after` es un elemento flex y respeta su tamaño. La `?v=` nueva
  (`064ee0dc11`) está en las dos páginas. `importar.html` y `oficios.html`
  aún no llevan la barra común: R66 llega allí con los bloques 10 y 11
  (`PAGINAS_CON_BARRA`), como dice el informe.

**2 · `inicio` y `partes`, R62 frente a R48: ¿es una incoherencia de la spec?**
Sí, **una ambigüedad de la spec**, y no bloquea porque hoy las dos lecturas
dan lo mismo. Va como **H-8**, para el spec-author.

**3 · ¿Quedan cerrados H-1 y el primer punto de H-4? ¿Y los demás?**

- **H-1, cerrado.** `FORMAS_DE_TARGET` y `targets_de` sirven al test de R17
  y al de R68, y llevan un control parametrizado (literal, ligado y
  `x-bind`). Comprobado con la mutación S, que ahora muere.
- **H-4, primer punto, cerrado.** El aviso ya no dice «El circuito de
  verdad es la pestaña «Partes firmados».» ni «Esto es una maqueta». Lo
  impide `test_f035_r13_el_aviso_dice_que_parte_del_portal_esta_en_construccion`,
  que exige siete frases y prohíbe «maqueta» y «circuito de verdad».
- **Los demás siguen asignados**, pero **solo en esta review y en
  `progress/current.md`**: `tasks.md` no los recoge.
  - H-3 (estructura cerrada de `entrada`), H-4 punto 2 (ceja, entradilla,
    chips «Maqueta» y pie de `index.html`) y H-5 (CSS muerto de
    `portal.css`): **bloque 9**.
  - H-4 punto 3 (`js/maqueta_datos.js:129`, «…y por la importación del
    Excel»): sigue **sin bloque**, pendiente de que el líder decida.
  - H-2 (`window.open`): bloque 10 o 16. **El 16 va ahora**, así que el
    líder tiene que decidir **antes de encargarlo** si `window.open` entra
    en la guarda de salida o en la lista cerrada de R73.

**4 · ¿Se ha tocado la lógica del circuito o de F-036?** **No.**

- En `partes.html` cambian solo tres cosas: la barra (los atributos de R66),
  la `?v=` y el `class` de los dos enlaces de F-036
  (`text-sky-700 hover:underline` → `rs-enlace`).
- Los `href`, `target` y `rel` de esos dos enlaces no cambian: es
  presentación. `rs-enlace` ya existía en `css/styles.css` (l. 363). Es
  burdeos, que §16.4 reserva a lo que funciona, y esos enlaces funcionan.
- Ningún módulo del circuito, ni `js/api.js`, `js/importacion.js` o
  `js/oficios.js`, ni `importar.html` u `oficios.html`. «F-036 intacto» sale
  vacío.
- Dos mutaciones prueban que la lógica de esos enlaces sigue vigilada por
  los tests de F-036, sin tocar:
  - V9, quitar el `target` del de importar: lo caza
    `test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas`.
  - V10, el de oficios apuntando a importar: lo cazan ese test y
    `…_solo_gana_los_dos_enlaces`.
- R59 sigue en verde.

**5 · Mutaciones a mano sobre lo nuevo.** Se hicieron en el mismo worktree
desechable, con el script `mutar_b8_rev.py` del scratchpad, nunca en el
árbol real. En cada mutación se pasaron la suite **entera** del front (que
incluye `test_f007_r32_…`, el que lanza Node), Node aparte y el fichero de
la raíz. Después se restauraban los ficheros y se comprobaba con
`git status --porcelain` que el worktree quedaba limpio. En las mutaciones
de CSS **se recalculó la `?v=`** con `version_de_las_hojas()`, para que no
las matara solo la versión de caché de T21 (la E8 del implementer murió
también por eso).

| # | Mutación | Resultado | Lo caza |
|---|---|---|---|
| V1 | `display: none` dentro de `.rs-pestana[data-construccion]::after` | **sobrevive** | — (H-6) |
| V2 | `background: var(--rs-burdeos)` detrás del `background-color` de esa regla | **sobrevive** | — (H-6) |
| V3 | `.rs-pestana` pasa de `inline-flex` a `inline-block` (el `::after` vuelve a ser inline y pierde los 6 px) | **sobrevive** | — (H-6) |
| V4 | Una regla posterior `.rs-pestana::after { content: none }` | **sobrevive** | — (H-6) |
| V5 | `:data-construccion="false"` ligado en «Bandeja de revisión» de `index.html` (Alpine quita el atributo al arrancar) | **sobrevive** | — (H-7) |
| V6 | `:aria-label="'Incidencias'"` ligado en `index.html` (pisa el literal al arrancar) | **sobrevive** | — (H-7) |
| V7 | `data-construccion` y `aria-label` en «Partes firmados» de `partes.html` | muerta | Node R66 `partes.html` y su control; F-007 R32 |
| V8 | F-038 `done` en `harness/features.json` **del worktree** (no en memoria) | muerta | raíz R62 `…_el_estado_…` y `…_control_el_lector…`; R28 ×2 (restos de F-038 en la maqueta) |
| V9 | Sin `target` en el enlace de F-036 a importar (`partes.html`) | muerta | `test_f036_r51_…enlaza_a_las_dos_paginas` |
| V10 | El enlace de F-036 a oficios va a `importar.html` | muerta | `test_f036_r51_…` ×2 |
| V11 | `enConstruccion` da `true` también para `inicio` | muerta | Node R62 ×2, R66 ×3; F-007 R32 |
| V12 | El aviso dice «marca naranja» en vez de «punto ámbar» | muerta | R13 enmendado |
| V13 | El aviso dentro de un `x-show` | muerta | `test_f035_r13_el_aviso_esta_siempre_y_no_se_cierra` |
| V14 | `estado: "construcción"` (con tilde) en `datos` | muerta | raíz R62 ×3; Node R62 ×2, R66 ×3; F-007 R32 |
| S (b7) | `:target` ligado en la tarjeta de importar | muerta | R17, R68 (H-1 cerrado) |
| B8 (impl.) | `estado !== "parcial"` | muerta | Node R62 (test de T26) |

Mueren 10 de 16. Las 6 que sobreviven son de **dos familias**, analizadas en
H-6 y H-7. Ninguna es de las que el diseño fija para este bloque (la 16 y la
17, que el implementer mató y que V7 y V8 confirman por otro lado), y ninguna
toca el estado declarado ni qué pestañas se marcan: las dos familias tratan
de **cómo se pinta** la marca. Con rigor `estandar` no bloquean.

### Checkpoints (acotados al bloque)

**C1**
- [x] `init.sh` exit 0 (ejecutado por el reviewer).
- [x] Ficheros del arnés presentes (`init.sh` los da en `[OK]`).

**C2**
- [x] Una sola feature `in_progress` (F-035; `init.sh`).
- [x] Rama `feature/F-035-portal-posventa`.
- [x] `current.md`: la entrada nueva describe el bloque, sus hallazgos y el
  siguiente paso (review, después bloque 16). Sigue acumulando el histórico
  de la feature (O-2 de una review anterior, deuda previa).
- [x] Features `done` con resumen en `history.md`: este bloque no cierra
  ninguna.

**C3**
- [x] Hexagonal: el diff es HTML, CSS, el JS de la maqueta (`portal.js`, que
  sigue siendo lógica pura sin red ni DOM) y tests. No toca `domain/` ni los
  adaptadores.
- [x] Primera línea con la ruta: `tests_js/f035_paginas.test.js`
  (`// services/…`); los demás ficheros conservan la suya.
- [x] Sin `print()`, sin `console.log`, sin TODOs, sin secretos y sin
  dependencias nuevas (`node:vm` es del propio Node).
- [x] Parte como unidad, validaciones antes de archivar o cerrar,
  manuscrito, firmado ≠ conforme, reprocesar no duplica y `conest`: **N/A
  justificado**. El bloque no toca el circuito ni el backend (diffs vacíos
  arriba) y ninguno de esos invariantes vive en los ficheros cambiados.
- [x] Ningún PDF ni parte en git: el único fichero añadido es
  `tests_js/f035_paginas.test.js`.

**C3 bis** — **N/A**: el bloque no añade ni modifica nada en
`docs/referencia/`.

**C4**
- [x] R62, R66, R13 enmendado y H-1 tienen tests trazables en verde (tabla
  de cobertura abajo).
- [x] Sin red ni BBDD: lectura de ficheros como texto y `node:vm` en un
  contexto aislado.
- [x] MANUAL (humano): este bloque no añade ninguna. La verificación visual
  del punto ámbar entra en V1/V5 (bloque 15); H-6 la hace más necesaria.

**C4 bis**
- [x] `rigor: "estandar"` declarado.
- [x] Fase RED: hay traza real en el informe (§3) y **la reproduje** (4 + 2
  + 9 rojos).
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh`.
- [x] Mutación: `progress/mutacion_F-035.md` lo generó la herramienta. Lo
  recalculé (alcance 0, 0 mutantes) e hice el control del cero (5 + 4 + 24
  mutantes ignorando la exclusión).
- [x] Muertos comprobados: campaña **reejecutada** (0,0 s < 5 min), con los
  mismos totales.
- [x] Coste por mutante: N/A **justificado**. Hay 0 mutantes, así que no
  hay nada que dividir.
- [x] Supervivientes: la herramienta no deja ninguno. De los manuales, la 16
  y la 17 mueren; B8 sobrevivió en la primera pasada y la mata el test de
  T26. Las seis vivas del reviewer están analizadas en H-6 y H-7. Con nivel
  `estandar` no hace falta que el humano las acepte por escrito.
- [x] «Evidencias» del bloque con los cuatro números.
- [x] Ningún N/A sin justificar.

**C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] T25 y T26 `[x]`, con sus commits `F-035 T25: …` y `F-035 T26: …`. El
  resto de `tasks.md` sigue abierto **a propósito**.
- [x] Sin ficheros sin trackear (`git status` limpio).
- [x] `features.json`: F-035 `in_progress`, correcto con la feature a medias.

### Cobertura del bloque: requisito → test

| Requisito | Test |
|---|---|
| R62 (estado literal y válido) | raíz `test_f035_r62_cada_seccion_declara_su_estado_literal`; Node `f035 R62: cada entrada de SECCIONES declara un estado válido` |
| R62 (frente a `features.json`) | raíz `test_f035_r62_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas`, con los controles `…_la_guardia_mira_una_ficha_que_pasa_a_done` (F-038) y `…_control_el_lector_de_estados_lee_el_texto` |
| R62 (`inicio` y `partes`) | raíz `test_f035_r62_partes_e_inicio_siguen_su_propia_regla`; Node `f035 R62: inicio y partes nunca están en construcción` |
| R62 (`enConstruccion`) | Node `f035 R62: enConstruccion es true justo…`, `…id desconocido o vacío…`, `…sigue al estado: real y parcial no, construccion sí` |
| R66 (atributo y `aria-label`, dos barras) | Node `f035 R66: en la barra de index.html…` y `…de partes.html…`, más tres controles |
| R66 (marca visual) | `test_f035_paginas.py::test_f035_r66_la_pestana_en_construccion_lleva_un_punto_ambar_con_tokens` (con el límite de H-6) |
| R13 enmendado | `test_f035_r13_el_aviso_dice_que_parte_del_portal_esta_en_construccion`, `…_esta_siempre_y_no_se_cierra`, `…_va_debajo_de_la_barra` |
| R17 / R68 «misma ventana» (H-1) | `test_f035_r17_los_enlaces_…`, `test_f035_r68_entrada_enlaza_…`, `test_f035_r17_control_targets_de_ve_el_target_literal_y_el_ligado` ×3 |
| R59 (`partes.html`: solo barra, `class` y `?v=`) | la guardia de R59 de siempre, en verde |

### Hallazgos

1. **H-6 · Menor · La marca visual de R66 se comprueba en su regla CSS,
   no en la cascada.**
   `test_f035_r66_la_pestana_en_construccion_lleva_un_punto_ambar_con_tokens`
   (`services/postventa-front/tests/test_f035_paginas.py`, al final) mira
   que exista la regla y qué propiedades declara. No ve nada de lo que
   esconde o repinta el punto desde fuera de ella:
   - `display: none` dentro de la propia regla (V1);
   - un atajo `background` posterior (V2);
   - que `.rs-pestana` deje de ser flex (V3), que es de lo que depende que
     el `::after` respete sus 6 px;
   - otra regla que lo anule (V4).

   **Arreglo barato**, en el mismo test:
   - (a) La regla no declara `display`, `visibility`, `opacity` ni
     `background`.
   - (b) `.rs-pestana` declara `display: inline-flex` o `flex`.
   - (c) Ninguna otra regla de `styles.css` ni de `portal.css` tiene un
     selector con `.rs-pestana` y `::after`.

   **Destino**: el bloque 16 o el 17, que vuelven a tocar la barra y
   `styles.css`. Si no, el 10, cuando R66 llegue a `importar.html`. Lo
   demás lo cubre la verificación visual del humano (V1/V5, bloque 15).
2. **H-7 · Menor · R66 no ve la forma ligada de sus atributos** (la misma
   familia que H-1, la P-R2 de la automejora del bloque 7).
   `problemasR66` (`services/postventa-front/tests_js/f035_paginas.test.js`,
   l. 84–106) lee `data-construccion` y `aria-label` literales. En
   `index.html`, que es una página de Alpine, un `:data-construccion="false"`
   o un `:aria-label` pisan al arrancar lo que el lector ve (V5, V6).

   **Arreglo**: que la presencia de `:data-construccion`,
   `x-bind:data-construccion`, `:aria-label` o `x-bind:aria-label` en una
   pestaña cuente como problema. El lector ya separa esos nombres de
   atributo, así que son dos líneas.

   **Destino**: el bloque 10, cuando `PAGINAS_CON_BARRA` crezca, o antes si
   el implementer vuelve a tocar ese fichero.
3. **H-8 · Spec, para el spec-author · «Todas las demás del portal» tiene
   dos lecturas, y el repositorio usa las dos.** R48
   (`requirements.md` l. 599–602) y R62 (l. 742–752) dicen lo mismo para
   `inicio`: real «cuando lo son todas las demás (secciones) del portal».
   Pero en el mismo fichero de la raíz (`tests/test_f035_placeholders_vivos.py`)
   hay dos funciones que lo leen distinto:
   - `secciones_reales` (R48) deja fuera `partes`, porque «es el circuito y
     no cuenta»;
   - `estados_segun_las_fichas` (R62) la incluye.

   Solo dan resultados distintos en un estado: todo `done` salvo F-045.
   Ahí R48 diría que `inicio` es real y R62, que es parcial. Hoy dan lo
   mismo (`parcial`) y R48 queda absorbida por R73 (§16.15.6), así que no
   bloquea.

   La lectura del implementer, **con** `partes`, es la que conviene en R62:
   la portada no debería pasar a «real» con el registro sin firma (F-045)
   sin hacer. En R48 tenía sentido sin ella, porque la barra de
   `partes.html` no se enlaza a sí misma.

   **Arreglo de spec**:
   - en R62 y en la tabla de §16.4, decir «las otras siete, `partes`
     incluida»;
   - en R48, o en la reescritura de su control del bloque 16, anotar que su
     `inicio` es solo a efectos de la barra del circuito.

### Observaciones sin acción

- **O-1**: los dos controles de R62
  (`…_la_guardia_mira_una_ficha_que_pasa_a_done` y
  `…_control_el_lector_de_estados_lee_el_texto`) dependen de que F-038 siga
  pendiente y de que `bandeja` no sea `parcial`. El día que se cierre F-038
  caerán y habrá que moverlos a otra ficha. Es el mismo patrón que los
  controles de R28 (F-044) y R48 (F-048), y la spec fija F-038. Pero el
  mensaje del de lector («el control no encuentra el estado de «bandeja»»)
  despistará: conviene que quien cierre F-038 lo sepa. Lo confirma V8, que
  tumba el del lector.
- **O-2**: `test_f035_r46_los_enlaces_al_circuito_van_en_la_misma_pestana`
  (`test_f035_portal.py` l. 734) sigue mirando solo el `target` literal. No
  deja hueco: el test de R17 recorre **todos** los `<a>` del portal con
  `targets_de`, `partes.html` incluido.
- **O-3**: el aviso conserva `data-aviso-maqueta` y las clases `rs-maqueta*`
  (no se ven) y la muestra de placeholder entre la frase de los datos
  inventados y la del sello. Es razonable: la muestra es la leyenda del
  «borde discontinuo» que nombra el texto. El renombrado, si se quiere, es
  de R67 (bloque 9).

### Qué queda para el humano

- Nada que decidir para cerrar el bloque 8.
- Para el líder, **antes de encargar el bloque 16**:
  - dónde va H-2 (`window.open`: guarda de salida del 16 o lista cerrada de
    R73 en el 10);
  - si H-6 entra en el 16 o el 17;
  - H-8 al spec-author (dos líneas de spec);
  - el texto de `maqueta_datos.js:129` (H-4, tercer punto), que sigue sin
    bloque.

  Conviene que H-3, H-4 punto 2, H-5 y H-7 se citen en el encargo de su
  bloque: hoy solo constan aquí y en `progress/current.md`, no en
  `tasks.md`.

### Automejora (propuesta, no aplicada)

**P-R3 · `CHECKPOINTS.md` C4 bis, para `arnes-base` (vale para cualquier
front).** Cuando una guarda estática comprueba una **marca visual** leyendo
una regla CSS, las mutaciones a mano deben incluir al menos una que la
**anule desde fuera de la regla**: otra regla posterior, un atajo que pisa
la propiedad o un cambio en el `display` del padre. Y si la página fija la
caché con una `?v=` derivada del CSS, la mutación debe **recalcularla**: si
no, la mata la versión y no el test de la marca, y el superviviente no se
ve. Caso de origen: F-035, bloque 8, H-6 (V1–V4; la E8 del implementer
murió también por la `?v=`).

## Review del bloque 16 · T43–T45 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 8ced4bd..HEAD` (`e3842b4` T43,
> `3a89d82` T44, `89296ce` T45) en `feature/F-035-portal-posventa`. Los
> bloques 17 y 9–15 siguen abiertos **a propósito**: no cuentan como `[ ]`.
> Numeración propia (`H16-n`) para no chocar con los H-8…H-12 del
> spec-author.

### Veredicto

**CHANGES_REQUESTED** (del bloque 16, no de la feature). El código está
bien:

- La guarda lee lo que tiene que leer, con los nombres reales del circuito.
- Falla abierta.
- No toca ningún módulo del circuito.
- Las líneas de R81 son literales.
- No queda ningún `target` entre páginas del front.

Lo que falta son **dos tests**, y los dos van a lo que este bloque viene a
proteger: que la remesa no se pierda al salir en la misma pestaña.

- **H16-1**: borrar la línea que **instala** la guarda en el navegador deja
  toda la suite en verde (mutación G1).
- **H16-2**: que un parte ya cerrado **corte** el recorrido de (c) también
  deja todo en verde (G12). Es el caso más normal en que la guarda importa:
  una tanda que cierra unos partes y falla en otros.

Son dos tests en `tests_js/guarda_salida.test.js`, sin tocar código de
producción.

### Nivel de rigor

`estandar` (declarado en `harness/features.json`). Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción:

- la cobertura sale N/A con el motivo impreso;
- la campaña da 0 mutantes.

La compensación son las mutaciones a mano:

- las 29–35 de `design.md` §16.15.8;
- las del implementer;
- las del reviewer.

La regla 7 de `reviewer.md` (mutaciones de orden) es para rigor `critico`:
**N/A**. Además, la guarda no ordena llamadas a ningún colaborador.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, árbol real) | **exit 0**, `ENTORNO LISTO`. Raíz **112 passed**; api en verde (caché); front **473 passed**; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos, deuda previa |
| Worktree desechable del scratchpad (`git worktree add --detach`, HEAD `89296ce`), línea base | Node **563/563**; front pytest **470 passed, 3 skipped** (los 3 del diff de rama, saltados con HEAD separado) |
| **RED de T43 reproducido** (sin `js/guarda_salida.js`) | Node: `Cannot find module '../js/guarda_salida.js'` (1 fail). Pytest `-k r80`: **14 failed**. Igual que el informe |
| **RED de T44 reproducido**: tests de HEAD con `partes.html`, `js/portal.js`, `test_f007_estaticos.py` y `test_f036_front.py` de `e3842b4` | Front **13 failed**, 457 passed y 3 skipped. Son los del informe (R43 ×4, R59 ×2, R31 ×4, R47, R73 `partes.html` y F-007 R32/Node) **menos** el de R32 de F-035, que con HEAD separado se salta. Node **562/563** (cae R31 de `portal.test.js`) |
| Recálculo `harness.alcance.alcance_de_feature("F-035", base=…)` | `lineas={}` con `2a86bca` y con `8ced4bd`: 0 ficheros y 0 líneas, como `progress/mutacion_F-035.md` |
| **Reejecución de la campaña** («Tiempo total» 0,0 s, menos de 5 min), `--salida` al scratchpad | 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts en 0,0 s: **idéntico** al informe |
| **Control del cero**: `generar_mutantes` sobre los `.py` del diff ignorando la exclusión | `test_f035_paginas.py` 41, `test_f035_portal.py` 58, `tests/test_f035_placeholders_vivos.py` 3; `test_f007_estaticos.py` y `test_f036_front.py` 0 (sus líneas nuevas son un literal y un `assert`). El generador funciona: el cero es **legítimo** (solo tests) |
| R33: `git diff --name-status $(git merge-base dev HEAD)..HEAD -- services/postventa-front/js` | solo `A`: `guarda_salida.js`, `maqueta_datos.js`, `portal.js` y `portal_app.js`. **Ningún `M`** en un módulo del circuito |
| `git diff --name-status 8ced4bd..HEAD` en `js/`, api, `importar.html`, `oficios.html` y `css/` | `A js/guarda_salida.js`, `M js/portal.js`; nada más |
| «F-036 intacto», versión ajustada: `git diff 2a86bca --` los tres ficheros | **solo** las líneas de R81 en `test_f036_front.py` (+2 −3); `importacion.test.js` y `oficios.test.js` vacíos |
| `git show --stat` de T43, T44 y T45 | T44 lleva en **un solo commit** la retirada de los `target`, la guarda en `partes.html` y las líneas de R81 |
| `git log --diff-filter=A 8ced4bd..HEAD` | añade solo `js/guarda_salida.js` y `tests_js/guarda_salida.test.js` (ningún PDF ni parte) |
| H-6, en el worktree: V3 (`.rs-pestana` a `inline-block`) y V4 (`::after { content: none }` en `portal.css`) **sobre las hojas reales** | las dos tumban `test_f035_r66_nada_esconde_ni_repinta_el_punto_ambar`. V1 y V2 los cubren los controles en memoria |
| Prueba de concepto (scratchpad, no va al repo): `js/guarda_salida.js` cargado con `vm.runInNewContext` y un `window` y un `document` falsos | registra `['beforeunload']`, deja `window.GuardaSalida`; con `Alpine.$data` y una remesa `[cerrado, aprobado sin cerrar]`, `preventDefault` 1 y `returnValue` `true`. Así se escribe el test de H16-1 |
| Al acabar | worktree retirado (`git worktree remove --force` + `prune`); queda el ajeno `agent-a6e2f9bed1d46cdbc`, que no se toca; `git status` limpio |

### Respuestas a las preguntas del líder

**1 · La guarda, contra el circuito real.**

Leí `js/app.js` entero, más `js/pipeline.js` (`estadoDe`, `hayTandaEnCurso`,
`conGuardaDeTanda` y las exportaciones) y `js/autoguardado.js` (`publicar`,
`disparar`, `alEscribir`, `cancelarPendiente` y las constantes).

Cada condición de D-15 se lee de donde vive ese estado, con su nombre real:

| D-15 | La guarda lee | Dónde vive en el circuito |
|---|---|---|
| (a) fases | `estado.fase` ∈ {`troceando`, `procesando`, `archivando_y_cerrando`} | `app.js:39` (declarada) y `:175`, `:269`, `:765` (asignadas). Las demás asignaciones (`:161`, `:204`, `:275`, `:753`, `:929`, `:944`) son `seleccionado`, `inactivo`, `revision` o `resumen`, que no cuentan |
| (a) tanda | `pipeline.hayTandaEnCurso()` | `pipeline.js:1244–1269`: la bandera de `conGuardaDeTanda`, que `app.js:749` y `:925` envuelven. Cubre el hueco entre que acaba `_lanzarTanda` y la fase pasa a `resumen` |
| (b) | `estado.estadoAutoguardado` frente a `GUARDANDO`/`FALLO` | `app.js:70` y `:493` (`_pintarAutoguardado`), con los valores de `publicar` (`autoguardado.js:249`, `:274`). Las constantes son `"guardando"` y `"fallo"` (`:70`, `:72`) |
| (c) | `estado.partes[i].cerrado` y `Pipeline.estadoDe(parte)` frente a `ESTADO_RECHAZADO`/`ESTADO_CERRADO` | `cerrado` nace en `app.js:234` y se fija en `:834`. `estadoDe` lee `parte.estadoParte.estado` (`pipeline.js:260`), que nace en `app.js:257` |
| (d) | `estado.parteAbierto` y su `.cerrado` | `app.js:61`; `abrirParte` en `:378`, `cerrarParte` en `:393`, `reiniciar` en `:953` |
| lectura | `window.Pipeline`, `window.Autoguardado` y `Alpine.$data(document.querySelector('[x-data="appPostventa()"]'))` | `pipeline.js:1332` y `autoguardado.js:457` exportan a `window`; el selector casa con `partes.html:20` |

Lo que hace el circuito y la guarda ve, aunque no esté en la tabla:

- un reintento de parte (`reintentarParte`): el parte pasa a «leyendo», sin
  marca, y lo ve (c);
- `revalidarParte` o una decisión (`_cambiarEstado`) en vuelo: se pide con
  el detalle abierto, y lo ve (d);
- `reintentarCierre`: pasa por `_lanzarTanda` y lo ve (a).

(c) no depende de la fase, así que unos partes que sobrevivan a un cambio de
fase también se ven.

**Lo que la guarda no ve, y deja salir perdiendo algo.** Solo un caso, y
estrecho (H16-5):

- `cerrarParte()` no cancela ni fuerza el rebote del autoguardado
  (`autoguardado.js:355–362`).
- Durante los 1.500 ms siguientes a cerrar el detalle, lo tecleado aún no
  está en «guardando».
- Si ese parte está rechazado (o cerrado según el backend), (c) lo excluye y
  (d) ya no aplica: se sale sin pregunta.
- Los campos se pueden editar en cualquier estado: `partes.html:306` no
  tiene `:disabled`.
- La guarda no lo puede ver sin `_autoguardado()`, que R80 prohíbe.
- El diseño dice que este caso «no existe»: es inexacto (H16-5, de spec).

**Lo que avisa y no debería.** Nada que contradiga D-15. Hay dos matices que
avisan por decisión del diseño:

- el detalle abierto de un parte rechazado (es (d), a propósito: el motivo
  sin enviar);
- el detalle abierto de un parte que el backend da por cerrado pero con
  `parte.cerrado` en `false`, por ejemplo uno ya cerrado y subido de nuevo
  (H16-6, nit de spec).

Probé los negativos de D-15 contra lo que deja el circuito:

| Caso | Por qué no avisa |
|---|---|
| Página recién abierta | `fase` `inactivo`, `partes` `[]` |
| `seleccionado` | `_aceptar` no crea partes |
| Todo cerrado o rechazado | cerrados con `cerrado: true` (`:834`); rechazados con su `estadoParte` |
| Tras `reiniciar()` | `:941`, `:950` y `:953` vacían lo que mira la guarda |

**¿Falla abierta?** **Sí.** En todos estos casos `leerEstado` da `null` o
`hayTrabajoSinTerminar` da `false`, y no se pregunta:

- sin Alpine;
- con Alpine sin `$data`;
- sin el elemento del circuito;
- con un `$data` que lanza;
- con Alpine cargado pero el componente aún sin montar: `Alpine.$data`
  devuelve una mezcla vacía y todo lee `undefined`;
- sin `Pipeline`.

Matiz: un solo `try` envuelve las cuatro condiciones. Si faltara
`window.Autoguardado`, (b) lanzaría y (c) y (d) no llegarían a evaluarse. No
es realista, porque `autoguardado.js` se carga estático y antes (R43), y el
circuito no funcionaría sin él. Sin acción.

**2 · ¿El circuito sigue sin modificarse (R33)? ¿R81, literal?** **Sí a
las dos.**

- Contra `git merge-base dev HEAD` no hay ningún `M` en `js/`.
- Comparé R81 línea a línea con `design.md` §16.15.4:
  - **`partes.html`**: `  <script src="js/guarda_salida.js"></script>`
    justo antes de `  <script src="js/app.js"></script>`, sin atributos ni
    comentario. Vigilado por R43 (tres controles) y R59 (f) (dos controles:
    un segundo script y `defer`).
  - **`test_f007_estaticos.py`**: la línea
    `    "js/guarda_salida.js",  # F-035 (R80, R81): solo lee el estado del circuito`,
    entre `"js/autoguardado.js",` y `"js/app.js",`. Idéntica, con sus cuatro
    espacios. El diff contra la base es esa línea más la de `INDEX`.
  - **`test_f036_front.py`**: el docstring nuevo y
    `        assert "target=" not in en_cabecera[destino]` sustituyen al
    docstring viejo y a los dos `assert` de `target` y `rel`. Idéntico,
    sangrías incluidas: +2 −3 contra `2a86bca`.
- `LINEAS_R81` (`test_f035_portal.py`) guarda esas mismas líneas literales,
  y R32 las exige por fichero con cuatro controles.

**3 · ¿Queda algún `target`, `window.open` o pestaña nueva entre páginas del
front?** **No.**

- Busqué `target`, `window.open`, `.open(`, `location`, `_blank` y
  `nuevaPestana` en las cuatro páginas y en todo `js/`.
- El único `target` es el «abrir en SharePoint» (`partes.html:610`,
  `:href="resultado.web_url"`). Es externo y R73 no lo cubre, a propósito.
- `window.location.hash` en `portal_app.js:62` y `:71` es el enrutado por
  ancla dentro del portal (mismo documento), no una pestaña nueva.
- `enlaceSeccion` da `nuevaPestana: false` en los dos caminos.
- R73 lo vigila en las cuatro páginas, con un control por página. Mi
  mutación G22 (`:target` ligado en el enlace a oficios) la tumban R73 y el
  R51 ajustado.

**4 · El test de R51 de F-036 invertido: ¿sigue protegiendo lo que
importa?** **Sí.**

- Su primer `assert` (los dos destinos están entre los `href` de la primera
  `<header>`) no cambia.
- `…_solo_gana_los_dos_enlaces` sigue intacto: los enlaces existen y van a
  donde deben.
- El `assert` nuevo es una subcadena: `"target="` caza el literal y el
  ligado (`:target=`); G22 lo confirma.
- Lo único que no ve es un `rel` suelto sin `target` (G21). Es
  **equivalente**: sin `target`, `rel="noopener"` no cambia la navegación, y
  R59 (g) lo neutraliza igual.
- Lo que el test protegía antes (que la remesa no se pierda) lo protege
  ahora la guarda, que es justo lo que H16-1 y H16-2 piden blindar.

**5 · H-2 y H-6.** **Cerrados los dos.**

- **H-2**: `problemas_r73` busca `window.open` en las cuatro páginas, sin
  comentarios, con un control por página. El estático de R80 lo prohíbe en
  la guarda. El implementer razona bien que la guarda en ejecución no puede
  ver clics.
- **H-6**: `test_f035_r66_nada_esconde_ni_repinta_el_punto_ambar` mira la
  regla, el `display` de `.rs-pestana` y que haya una sola regla sobre el
  `::after`. Lleva los controles V1–V4 en memoria. V3 y V4 sobre los ficheros
  reales la tumban.

**6 · Los apuntes del §5 del implementer.** Los dos son **incoherencias de
spec**, para el spec-author, y **no bloquean**: no rompen nada.

- **H16-3**: R79 (`requirements.md` l. 888) escribe
  `hayTrabajoSinTerminar(estado, Pipeline)`, y el diseño (§16.15.3), con
  razón, `(estado, pipeline, autoguardado)`, porque (b) necesita las
  constantes de `Autoguardado`. El código sigue al diseño.
- **H16-4**: el comentario de F-036 en la cabecera de `partes.html` («la
  entrada de incidencias, en otra pestaña: salir de esta perdería la remesa
  en curso») dice ahora lo contrario de lo que pasa, y R59 no deja tocarlo.
  R59 compara comentarios fuera de la barra y (g) solo admite quitar
  `target` y `rel`.
- La reescritura del comentario **de la barra**, aunque T44 diga «ningún
  otro cambio en el HTML», la acepto: R59 (c) la admite («con el comentario
  que la precede») y el texto viejo afirmaba lo contrario de lo que hace la
  página.

**7 · El vistazo en el navegador de T44.** **Puede esperar a V1/V2 del
humano, con dos matices.**

- Ese vistazo (página recién abierta, «Inicio» sin pregunta) **no habría
  detectado** una guarda sin instalar: sin trabajo, una guarda instalada y
  una ausente se comportan igual. La instalación la cubrirá el test de
  H16-1; esperar al navegador para eso no sirve.
- Lo único que solo se ve en un navegador de verdad es que `Alpine.$data`
  exista y devuelva el estado en 3.14.1 (riesgo de §16.15.9). Se puede
  comprobar **en un minuto y sin backend**: `.\dev_front.ps1`, abrir
  `http://localhost:5173/partes.html` y, en la consola,
  `GuardaSalida.leerEstado(window, document).fase` (tiene que dar
  `"inactivo"`). Después:
  `Alpine.$data(document.querySelector('[x-data="appPostventa()"]')).fase = "procesando"`,
  un clic en la página y otro en «Inicio»: tiene que salir el diálogo del
  navegador, y con «Cancelar» la página se queda. Recomiendo que lo haga el
  humano (o el implementer con la extensión conectada) **antes del bloque
  15**. Si falla, la spec manda PARAR, y cuanto antes se sepa, menos
  trabajo encima. No bloquea este bloque.

**8 · Mutaciones a mano sobre la guarda.** Las hice en el worktree
desechable, con el guion `mutar_b16_rev.py` del scratchpad. En cada una
pasé Node entero (reporter TAP) y la suite pytest del front, y después
restauré el fichero. `git status --porcelain` del worktree salió vacío al
final y el worktree está retirado.

| # | Mutación | Resultado | La mata |
|---|---|---|---|
| G1 | En el navegador **no se instala** (fuera `instalar(window, document);`, `guarda_salida.js:162`) | **sobrevive** | — (**H16-1**) |
| G4 | `if (pipeline.hayTandaEnCurso)` (la función como booleano) | muerta | Node R79 (a) tanda real y los negativos ×19 |
| G5 | (b) ignora `GUARDANDO` | muerta | R79 (b) GUARDANDO |
| G6 | (c) ignora el `cerrado` del backend | muerta | R79 (c) negativo; «todo cerrado o rechazado» |
| G7 | `alSalir` sin `returnValue` | muerta | R78 ×2 |
| G8 | `returnValue = true` siempre (falla cerrada) | muerta | R78 sin trabajo; R80 falla abierta ×4 |
| G11 | (d) no cuenta un abierto rechazado | muerta | R79 (d) |
| G12 | (c): un parte con `cerrado: true` hace `return false` en vez de `continue` | **sobrevive** | — (**H16-2**) |
| G13 | (c) solo mira el primer parte | muerta | R79 (c) ×4 |
| G14 | `instalar` no pasa el evento a `alSalir` | muerta | R78 «el beforeunload instalado…» |
| G16 | `seleccionado` entre las fases en marcha (contra D-15) | muerta | Node ×3; estático R80 ×2 |
| G18 | (b) cuenta también `GUARDADO` | muerta | R79 (b) negativo; «todo cerrado…» |
| G19 | Lee `estado.parteAbierta` (nombre mal escrito) | muerta | R79 (d) |
| G20 | `leerEstado` sin comprobar que `$data` sea función | sobrevive | **equivalente**: el `$data` ausente lanza dentro del `try` y da `null` igual |
| G21 | `rel="noopener"` sin `target` en el enlace a importar | sobrevive | **equivalente**: sin `target`, `rel` no cambia la navegación |
| G22 | `:target="'_blank'"` en el enlace a oficios de la cabecera | muerta | R73 `partes.html`; R51 de F-036 ajustado |

Mueren 13 de 16. G20 y G21 son equivalentes. **G1 y G12 son reales** y
tocan el núcleo de R78 y R79 (c): H16-1 y H16-2.

### Checkpoints (acotados al bloque)

**C1**
- [x] `init.sh` exit 0 (ejecutado por el reviewer).
- [x] Ficheros del arnés presentes (`init.sh` los da en `[OK]`).

**C2**
- [x] Una sola feature `in_progress` (F-035).
- [x] Rama `feature/F-035-portal-posventa`.
- [x] `current.md`: la entrada del bloque describe lo hecho, el MANUAL
  pendiente y lo que va al spec-author. Sigue acumulando el histórico de la
  feature (deuda previa, O-2 de una review anterior).
- [x] Features `done` con resumen en `history.md`: el bloque no cierra
  ninguna.

**C3**
- [x] Hexagonal: el diff es el front estático (un módulo JS nuevo de lógica
  pura con su enganche al navegador, HTML y tests). No toca `domain/` ni
  los adaptadores.
- [x] Primera línea con la ruta en los dos ficheros nuevos.
- [x] Sin `console.*`, `debugger`, TODOs, secretos ni dependencias nuevas
  (`node:test` y `node:assert` son de Node).
- [x] Parte como unidad, validaciones antes de archivar, manuscrito,
  firmado ≠ conforme, reprocesar no duplica y `conest`: **N/A
  justificado**. El bloque no cambia ningún módulo del circuito ni el
  backend (diffs de arriba). La guarda solo lee, y lo vigilan el `Proxy`
  que lanza y el estático de R80.
- [x] Ningún PDF ni parte en git (`--diff-filter=A`: solo los dos ficheros
  de la guarda).

**C3 bis** — **N/A**: el bloque no toca `docs/referencia/`.

**C4**
- [ ] **Cada requisito con un test trazable que lo cubra.** R78 se prueba
  sobre `alSalir` e `instalar` **inyectados**. Ningún test comprueba que la
  guarda **se instale** al cargarse en la página (G1). Y R79 (c) no tiene
  un caso con un parte cerrado **antes** de uno pendiente (G12). Ver
  H16-1 y H16-2.
- [x] Sin red ni BBDD: dobles en memoria, el `Pipeline` y el `Autoguardado`
  reales (lógica pura) y lectura de ficheros.
- [x] MANUAL (humano): el vistazo de T44 consta como pendiente en
  `progress/current.md`, junto a V1 (q) y V2 (k)–(p) de T12, que llevan sus
  pasos. Mi respuesta 7 añade la comprobación de un minuto sin backend.

**C4 bis**
- [x] `rigor: "estandar"` declarado.
- [x] Fase RED: traza real en el informe (§2) y **reproducida** (T43: 1
  fail en Node y 14 en pytest; T44: 13 + 1).
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh`.
- [x] Mutación: `progress/mutacion_F-035.md` lo generó la herramienta.
  Recalculado (alcance 0 con las dos bases) y con el control del cero
  hecho (41 + 58 + 3 mutantes ignorando la exclusión).
- [x] Muertos comprobados: campaña **reejecutada** (0,0 s, menos de 5 min),
  con los mismos totales.
- [x] Coste por mutante: N/A **justificado**. Hay 0 mutantes, así que no
  hay nada que dividir.
- [ ] **Supervivientes analizados y sin hueco en lo central.** Las 18 del
  implementer mueren. De las mías, G20 y G21 son equivalentes (analizadas
  arriba). **G1 y G12 son huecos reales** de R78 y R79 (c): no son
  equivalentes, y el arreglo es barato. Con `estandar` no hace falta la
  aceptación escrita del humano, pero tampoco cabe dejar sin test la línea
  que activa la guarda.
- [x] «Evidencias» del bloque con los cuatro números y los workers (1).
- [x] Ningún N/A sin justificar.

**C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] T43, T44 y T45 `[x]`, cada una con su commit `F-035 Tn: …`. El resto
  de `tasks.md` sigue abierto **a propósito**.
- [x] Sin ficheros sin trackear (`git status` limpio; `coverage.json` del
  front está ignorado).
- [x] `features.json`: F-035 `in_progress`, correcto.

### Cobertura del bloque: requisito → test

| Requisito | Test |
|---|---|
| R78 | Node `f035 R78: con trabajo sin terminar, alSalir llama a preventDefault…`, `…sin trabajo, alSalir deja el evento intacto…`, `…lee la tanda y el autoguardado de la ventana…` y `…el beforeunload instalado pregunta con trabajo y calla sin él`. **Falta**: la instalación al cargar (H16-1) |
| R79 (a) | Node `f035 R79 (a)` ×3 fases, tanda (doble y `conGuardaDeTanda` **real**), negativos ×4 fases; estático `test_f035_r80_las_fases_de_la_guarda_existen_en_app_js` con su control |
| R79 (b) | Node `f035 R79 (b)` GUARDANDO, FALLO y los negativos GUARDADO e INACTIVO |
| R79 (c) | Node `f035 R79 (c)` ×4 positivos y tres negativos. **Falta**: un cerrado antes del pendiente (H16-2) |
| R79 (d) | Node `f035 R79 (d)`, positivo (rechazado abierto) y negativo |
| R79 «no es trabajo» | Node: recién abierta, `seleccionado`, todo cerrado o rechazado, tras `reiniciar`; estados raros ×8 |
| R80 | Node: el `Proxy` de solo lectura (con su control), `leerEstado` ×7 y falla abierta ×4; `test_f035_r80_la_guarda_solo_lee_y_solo_escucha_beforeunload` con 11 controles |
| R81 / R32 / R33 | `test_f035_r32_de_los_tests_del_circuito_solo_cambian_index_y_las_lineas_de_r81` (`LINEAS_R81`) con cuatro controles; R33 con el alta de `js/guarda_salida.js`; `test_f007_estaticos.py` entero |
| R43 ajustado | `test_f035_r43_partes_html_carga_los_nueve_scripts_y_la_guarda_justo_antes_de_app_js` con tres controles |
| R59 (f), (g) | la guardia de R59, más tres estropeos nuevos (segundo script, `defer`, `target` fuera del enlace de SharePoint) |
| R31 ajustado | `test_f035_r31_la_barra_del_circuito_navega_en_la_misma_pestana` con tres controles; Node `f035 R31: enlaceSeccion desde el circuito…` |
| R47 ajustado | `test_f035_r47_la_barra_del_circuito_avisa_de_la_confirmacion_al_salir` con las dos leyendas viejas como control |
| R73 ajustado y H-2 | `test_f035_r73_ninguna_pagina_del_front_abre_otra_aparte[×4]`, más controles de `target` ×4, `window.open` ×4 y SharePoint |
| R48 (absorbida) | raíz `test_f035_r48_…` en verde por construcción; el control, sobre una copia en memoria |
| R51 de F-036 (ajustado) | `test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas` y `…_solo_gana_los_dos_enlaces` |
| H-6 (R66) | `test_f035_r66_nada_esconde_ni_repinta_el_punto_ambar` con controles V1–V4 |

### Hallazgos

1. **H16-1 · MEDIA · bloqueante · Ningún test ve que la guarda se instale
   en la página.**

   *Qué pasa.* `services/postventa-front/js/guarda_salida.js:160–163` es lo
   único que conecta la guarda con el navegador:
   `if (typeof window !== "undefined") { window.GuardaSalida = …; instalar(window, document); }`.
   Los tests de Node cargan el módulo con `require`, donde no hay `window`,
   así que esa rama no se ejecuta nunca. Sin la línea `instalar(…)`, la
   suite entera sigue en verde (G1). En producción eso es: la guarda se
   carga, no escucha nada y la remesa se pierde sin pregunta, que es justo
   el riesgo que el humano aceptó a cambio de la guarda.

   *Por qué no basta el navegador.* El vistazo de T44 no lo vería (sin
   trabajo, instalada y ausente se comportan igual). Hoy solo lo cazaría V2
   (m), al final de la feature.

   *Precedente.* El mismo patrón que H-R1 de la primera review: cableado sin
   ningún test.

2. **H16-2 · MEDIA · bloqueante · R79 (c) no tiene ningún caso con un parte
   cerrado antes de uno pendiente.**

   *Qué pasa.* En `services/postventa-front/tests_js/guarda_salida.test.js:281–295`,
   los cuatro positivos de (c) usan
   `[rechazado, <el del caso>, parte(null, true)]`, con el cerrado al
   **final**. Cambiar `continue` por `return false` cuando un parte está
   cerrado (`guarda_salida.js:87–88`) deja todo en verde (G12).

   *Por qué importa.* Es el caso más corriente en que la guarda importa: una
   tanda que cierra los primeros partes y falla en uno posterior. Con esa
   mutación se saldría sin pregunta y se perderían los pendientes. El código
   de hoy lo hace bien: lo comprobé con la prueba de concepto de arriba,
   `[cerrado, aprobado sin cerrar]` → pregunta. Pero ningún test lo fija.

3. **H16-3 · Spec, para el spec-author · Firma de R79.** `requirements.md`
   l. 888 escribe `GuardaSalida.hayTrabajoSinTerminar(estado, Pipeline)`;
   `design.md` §16.15.3 y el código, `(estado, pipeline, autoguardado)`.
   Hace falta el tercero para (b). **Arreglo**: en R79, «`(estado, Pipeline,
   Autoguardado)`». No bloquea.

4. **H16-4 · Spec, para el spec-author · El comentario de F-036 en la
   cabecera de `partes.html` queda desfasado y R59 no deja arreglarlo.**

   *Dónde.* `services/postventa-front/partes.html`, el comentario
   `<!-- F-036 (R51) · la entrada de incidencias, en otra pestaña: salir de esta perdería la remesa en curso (D4 de F-007). -->`
   que precede al `<nav>` de los dos enlaces. Dice lo contrario de lo que
   hace la página.

   *Por qué no se puede tocar.* R59 compara los comentarios fuera de la
   barra, y (g) solo admite retirar `target` y `rel`.

   *Arreglo, a elegir:*
   - (i) añadir a R59 (g) la sustitución **literal** de ese comentario, con
     su línea en la guardia, igual que las de R81;
   - (ii) aceptar el desfase hasta que F-045 toque el circuito, y anotarlo en
     §16.15.4.

   Es invisible para el usuario. No bloquea.

5. **H16-5 · Spec, para el spec-author · «El rebote del autoguardado sobre
   un parte que no está abierto no existe» (`design.md` §16.15.2, último
   párrafo) es inexacto.**

   *Qué pasa.* `cerrarParte()` (`app.js:391–394`) no cancela ni fuerza el
   rebote: el temporizador sigue vivo hasta 1.500 ms con el detalle ya
   cerrado (`autoguardado.js:355–362`). Para un parte sin terminar lo cubre
   (c). Para uno **rechazado** (o cerrado según el backend), que se puede
   editar (`partes.html:306`, sin `:disabled`), es un hueco de como mucho
   1,5 s: editar, cerrar el detalle y salir en ese instante.

   *Por qué no se arregla en la guarda.* No lo puede ver sin
   `_autoguardado()` (R80).

   *Arreglo.* Pasar la frase a «Lo que la guarda no puede saber y se
   acepta», con la ventana de 1,5 s. No bloquea.

6. **H16-6 · Nit de spec · (d) mira solo el indicador `parteAbierto.cerrado`;
   (c) acepta también `estadoDe(parte) === ESTADO_CERRADO`.**

   *Qué pasa.* Con el detalle abierto de un parte que el backend da por
   cerrado (subido otra vez), la guarda pregunta; con el detalle cerrado, no.
   Es lo que dice D-15, literal. Es inocuo (se resuelve cerrando el
   detalle), pero es incoherente.

   *Arreglo.* Si se quiere coherencia, que (d) acepte también el estado del
   backend; si no, nada.

7. **H16-7 · Menor · El estático ata a `app.js` las fases, pero no los
   nombres que lee la guarda.**

   *Qué falta.* `test_f035_r80_las_fases_de_la_guarda_existen_en_app_js`
   salta si se renombra una fase. Si se renombrara `partes`, `parteAbierto`,
   `estadoAutoguardado` o `cerrado` en `app.js`, o el `x-data` de
   `partes.html`, la guarda fallaría **abierta y en silencio**: los tests de
   comportamiento escriben esos nombres a mano. Hoy R33 y R59 congelan esos
   nombres, pero F-021 y F-045 tocarán el circuito.

   *Arreglo.* Ampliar el estático para exigir:
   - las declaraciones `partes:`, `parteAbierto:`, `estadoAutoguardado:` y
     `cerrado:` en `app.js`;
   - un único elemento de `partes.html` que case con `SELECTOR_CIRCUITO`.

   *Destino.* Con H16-1 si sale barato; si no, el bloque 17. No bloquea por
   sí solo.

### Cambios requeridos

1. **H16-1.** En `services/postventa-front/tests_js/guarda_salida.test.js`,
   un test **`f035 R78: cargada en la página, la guarda se instala sola…`**.
   Tiene que:
   - leer `js/guarda_salida.js` con `fs`;
   - ejecutarlo con `vm.runInNewContext(fuente, { window, document })`, con
     un `window` falso que apunte sus `addEventListener` y lleve `Pipeline`
     y `Autoguardado` reales, y un `Alpine.$data` que devuelva un estado con
     trabajo;
   - comprobar que queda **exactamente un** `beforeunload` en `window` y que
     `window.GuardaSalida` existe;
   - llamar a ese manejador con un evento falso y comprobar `preventDefault`
     1 y `returnValue` `true`.

   Y su **control**: la misma fuente sin la línea `instalar(window, document);`
   (en memoria, `replace` con la cuenta exigida a 1) no deja ninguna
   escucha. La prueba de concepto del reviewer, en el scratchpad
   (`vm_prueba.js`), confirma que así funciona. Al terminar, G1 tiene que
   morir.
2. **H16-2.** En el mismo fichero, un positivo de R79 (c) con el parte
   cerrado **antes** del pendiente. Por ejemplo,
   `[parte(PipelineReal.ESTADO_APROBADO, true), parte(PipelineReal.ESTADO_APROBADO)]`
   → `true`, sin violaciones. O bien, en los cuatro positivos de l. 281–295,
   poner `parte(null, true)` el **primero**. Al terminar, G12 tiene que
   morir.
3. En `progress/impl_F-035.md`, una nota de las dos correcciones con G1 y
   G12 muertas (salida real) y `bash harness/init.sh` en verde. Ningún
   cambio de código de producción ni de HTML.

H16-3 a H16-6 van al spec-author. H16-7 se puede hacer junto a 1 si sale
barato.

### Observaciones sin acción

- **O16-1**: las bases de mutación. El encargo decía `8ced4bd` y T45,
  `2a86bca`; el implementer lanzó las dos (0 mutantes en ambas). Correcto.
- **O16-2**: el implementer declara que lanzó `init.sh` una vez con la
  salida redirigida. Yo lo lancé limpio y sale en verde: sin efecto.
- **O16-3**: el `bfcache` y `beforeunload` registrado siempre. Lo aceptó el
  diseño (§16.15.3): la página vuelve vacía igual que hoy. Sin acción.

### Qué queda para el humano

- Nada que decidir para corregir: H16-1 y H16-2 son dos tests.
- Recomendado, **antes del bloque 15**: la comprobación de un minuto de
  `Alpine.$data` en el navegador (respuesta 7).
- Para el líder: H16-3 a H16-6 al spec-author.

### Automejora (propuesta, no aplicada)

**P-R4 · `CHECKPOINTS.md` C4 bis, para `arnes-base` (vale para cualquier
front con módulos duales navegador/Node).**

*La regla.* Cuando un módulo se prueba en Node con `require` y se engancha
al navegador en una rama `if (typeof window !== "undefined")`, las
mutaciones a mano deben incluir **borrar el enganche** (la autoinstalación,
el registro en `window`). Y el módulo debe tener un test que lo cargue con
`vm.runInNewContext` y un `window` falso. Con `require` esa rama no se
ejecuta nunca: el módulo puede estar perfecto y no hacer nada en la página.

*Caso de origen.* F-035, bloque 16, H16-1 (G1).

**P-R5 · Para el spec-author, en general.** Cuando un recorrido salta
elementos (`continue`), al menos un caso positivo debe poner el elemento
saltado **antes** del que decide.

*Caso de origen.* F-035, bloque 16, H16-2 (G12).

---

## Re-review del bloque 16 · arreglos de H16-1 y H16-2 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 82db245..HEAD` (`e00ffbc` H16-1,
> `87e24e8` H16-2, `36cf799` informe y estado), solo tests en
> `services/postventa-front/tests_js/guarda_salida.test.js`. H16-3 a H16-6
> son de spec y van al bloque 14: fuera de esta re-review.

### Veredicto

**CHANGES_REQUESTED** (del bloque 16, no de la feature).

- **H16-1 y H16-2 cierran.** G1 y G12, repetidas por mí cada una sola en una
  copia desechable, caen en rojo, cada una con su test nuevo. El código de
  producción no se ha tocado.
- Pero el encargo pedía probar mutaciones **cercanas**, y una de ellas sigue
  viva en el mismo recorrido de (c) que arregla H16-2. **N14**: el bucle de
  (c) empieza en `i = 1` y la suite entera sigue en verde. En producción eso
  es que **una remesa de un solo parte**, o una cuyo único pendiente es el
  primero, se pierde al salir sin pregunta. Es el mismo criterio que bloqueó
  G12: un hueco central de R79 (c), con un arreglo de un test (**H16-8**).
- Otra cercana a G1 (instalar con `{ once: true }` o `{ passive: true }`)
  también vive. Es menos probable y no bloquea, pero se arregla con una
  aserción y conviene hacerlo en el mismo commit (**H16-9**).

H16-8 es un hueco que **mi review anterior no buscó**: mi G13 (solo el
primer parte) miraba el otro extremo del bucle. No es un fallo del
implementer, que hizo exactamente lo pedido.

### Nivel de rigor

`estandar`, como en la review del bloque 16: fase RED, cobertura de lo
cambiado y mutación con supervivientes analizados. El diff es solo de tests:

- la cobertura sale N/A con el motivo impreso;
- la campaña de la herramienta da 0 mutantes (el implementer la lanzó con
  base `82db245`; el control del cero ya se hizo en la review del bloque);
- la compensación son las mutaciones a mano.

La regla 7 (orden) es de rigor `critico`: **N/A**.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, árbol real) | **exit 0**, `ENTORNO LISTO`. Raíz 112 passed; api y front en verde (caché del árbol); `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos, deuda previa |
| `git diff 82db245 HEAD -- services/postventa-front/js/` | **vacío** (0 líneas) |
| `git diff --stat 82db245 HEAD` | 3 ficheros: `guarda_salida.test.js` (+63 −1), `progress/impl_F-035.md`, `progress/current.md`. Nada más |
| Worktree desechable del scratchpad (`git worktree add --detach`, HEAD `36cf799`), línea base | Node **567/567** (54 → 58 en `guarda_salida.test.js`, +4); front pytest **470 passed, 3 skipped** (los 3 de diff de rama, saltados con HEAD separado) |
| Mutaciones a mano | guion `mutar_b16_rerev.py` del scratchpad: aplica cada mutación **sola** con la cuenta del patrón exigida a 1 (respetando el CRLF del fichero), pasa Node entero y el pytest del front (sin el puente a Node, que repite Node) y restaura. «restaurado: True» al acabar |
| Al acabar | worktree retirado (`git worktree remove --force` + `prune`); el ajeno `agent-a6e2f9bed1d46cdbc` no se toca; `git status` del árbol real limpio antes del commit |

### H16-1 y H16-2: ¿cierran?

**Sí, las dos.**

- **H16-1.** El test `f035 R78: cargada como script en la página, la guarda
  se instala sola y su beforeunload pregunta con trabajo` hace lo pedido:
  - lee el fichero real con `fs` y lo ejecuta con `vm.runInNewContext` en un
    contexto con `window` y `document` y sin `module`, como `partes.html`;
  - exige **un** `beforeunload` en la ventana y **nada** en el documento;
  - exige `window.GuardaSalida` con `hayTrabajoSinTerminar`;
  - llama al manejador registrado: sin trabajo no toca el evento, y con
    `fase: "procesando"` llama a `preventDefault` una vez y pone
    `returnValue = true`. Lee el estado **al salir**, no al cargar.
- **H16-2.** Tres positivos con el parte terminado **delante** de uno
  aprobado sin cerrar: cerrado por el circuito, rechazado y cerrado del
  backend. El primero mata G12; los otros dos fijan que la rama de
  `estadoDe` tampoco corte el recorrido. Que G12 solo la mate el primero es
  lo esperado, y el informe lo explica.
- El informe trae las salidas reales de G1 y G12, el `diff` de cada mutante
  y la nota honesta del primer `sed` de G12 que no aplicó.

### Mutaciones repetidas y cercanas

Cada una sola, sobre `js/guarda_salida.js` del worktree.

| # | Mutación | Resultado | La mata |
|---|---|---|---|
| **G1** | fuera `instalar(window, document);` (l. 162) | **muerta** | Node: `f035 R78: cargada como script…` (1 fail; pytest verde) |
| **G12** | (c) parte con `cerrado: true`: `continue` → `return false` (l. 88) | **muerta** | Node: `f035 R79 (c): un parte cerrado por el circuito (cerrado: true) delante…` (1 fail) |
| N1 | instalar con `"unload"` | muerta | Node ×2 (vm y R80 «exactamente un beforeunload»); pytest `test_f035_r80_la_guarda_solo_lee_y_solo_escucha_beforeunload` |
| N2 | instalar con `"pagehide"` | muerta | ídem N1 |
| N3 | instalar en `documento` | muerta | Node ×3 |
| N4 | instalar dos veces | muerta | Node: el test vm (lista exacta de escuchas) |
| **N5** | `addEventListener("beforeunload", fn, { once: true })` | **sobrevive** | — (**H16-9**) |
| **N6** | `addEventListener("beforeunload", fn, { passive: true })` | **sobrevive** | — (**H16-9**) |
| N7 | el manejador no pasa el evento a `alSalir` | muerta | Node ×2 |
| N8 | `alSalir` sin `returnValue` | muerta | Node ×3 |
| N9 | `alSalir` sin `preventDefault` | muerta | Node ×4 |
| N10 | fuera `window.GuardaSalida = …` | muerta | Node: el test vm |
| N11 | instala solo si además hay `module` | muerta | Node: el test vm |
| N12 | `instalar(window, {})` | muerta | Node: el test vm |
| N13 | (c) parte cerrado: `continue` → `break` | muerta | Node: el positivo nuevo de H16-2 |
| **N14** | (c) el bucle empieza en `i = 1` | **sobrevive** | — (**H16-8**) |
| N15 | (c) el bucle acaba en `length - 1` | muerta | Node ×3 (los tres de H16-2) |
| N16 | (c) `return false` tras el primer parte rechazado o cerrado del backend | muerta | Node ×6 |
| N17 | `ventana.onbeforeunload = …` en vez de `addEventListener` | muerta | Node ×3; pytest R80 ×2 |

Mueren 16 de 19. Ninguna de las tres vivas es equivalente.

### Checkpoints (acotados al diff)

**C1**
- [x] `init.sh` exit 0 (ejecutado por el reviewer).

**C2**
- [x] Una sola feature `in_progress` (F-035), rama correcta.
- [x] `current.md`: entrada nueva arriba con lo hecho, lo que queda para el
  spec-author y el MANUAL pendiente.

**C3**
- [x] Solo tests: `js/` sin diff. Primera línea con ruta (fichero ya
  existente). Sin `console.*`, `debugger`, secretos ni dependencias nuevas
  (`node:fs`, `node:path` y `node:vm` son de Node).
- [x] Hexagonal y reglas de dominio: **N/A justificado**, el diff no toca
  código de producción.
- [x] Ningún PDF ni parte en git.

**C3 bis** — **N/A**: no toca `docs/referencia/`.

**C4**
- [ ] **Cada requisito con un test trazable que lo cubra.** R78 (la
  instalación) y R79 (c) con el terminado delante, ya sí. Pero R79 (c) no
  tiene **ningún** positivo con el pendiente en la **primera** posición
  (N14). Ver H16-8.
- [x] Sin red ni BBDD: `vm` sobre el fichero local y dobles en memoria.

**C4 bis**
- [x] `rigor: "estandar"`.
- [x] Fase RED: G1 y G12 con salida real en el informe, y **reproducidas**
  por mí.
- [x] Cobertura: N/A **con el motivo impreso** por `init.sh` (solo tests JS).
- [x] Mutación de la herramienta: 0 mutantes con base `82db245`, legítimo
  (el diff no tiene Python de producción; control del cero hecho en la
  review del bloque). No se reejecuta: el informe va al scratchpad y no
  pisa `progress/mutacion_F-035.md`.
- [ ] **Supervivientes analizados y sin hueco en lo central.** N14 es un
  hueco real de R79 (c), no equivalente (H16-8). N5 y N6 son reales pero
  menores (H16-9).
- [x] «Evidencias» con los cuatro números.
- [x] Ningún N/A sin justificar.

**C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] Commits `F-035 H16-1: …`, `F-035 H16-2: …` y el del informe. Sin
  ficheros sin trackear.

### Hallazgos

1. **H16-8 · MEDIA · bloqueante · R79 (c) no tiene ningún positivo con el
   pendiente en la primera posición.**

   *Qué pasa.* En `services/postventa-front/tests_js/guarda_salida.test.js`,
   todos los positivos de (c) ponen el parte pendiente en el **índice 1**:
   los cuatro de l. 285–299 (`[rechazado, <el del caso>, cerrado]`) y los
   tres nuevos de l. 304–317 (`[terminado, aprobado]`). Si el bucle de
   `services/postventa-front/js/guarda_salida.js:85` empieza en `i = 1`,
   la suite entera sigue en verde (N14).

   *Por qué importa.* Con esa mutación, una **remesa de un solo parte** sin
   cerrar, o una cuyo único pendiente es el primero, deja salir sin pregunta
   y se pierde. Una remesa de un parte es de lo más corriente, y en
   `revision` o `resumen` solo la ve (c). El código de hoy lo hace bien;
   ningún test lo fija.

2. **H16-9 · BAJA · no bloquea · Nada fija que el `beforeunload` se registre
   sin opciones.**

   *Qué pasa.* El doble `navegador()` (l. 147–179) ignora el tercer argumento
   de `addEventListener`, y el estático de R80
   (`test_f035_paginas.py`, `_ESCUCHA`) solo mira el evento. Con
   `{ once: true }` (N5) el navegador retira la escucha tras la primera
   salida: el usuario cancela una vez y la siguiente salida pierde la
   remesa sin pregunta. Con `{ passive: true }` (N6) el navegador ignora
   `preventDefault()`. Las dos sobreviven.

   *Por qué no bloquea.* Requiere tocar a propósito la línea de `instalar`,
   y no es un error de los que salen solos. Pero el arreglo es una
   aserción.

### Cambios requeridos

1. **H16-8.** En `services/postventa-front/tests_js/guarda_salida.test.js`,
   un positivo de R79 (c) con el pendiente **primero**. Por ejemplo, la
   remesa de un solo parte:
   `[parte(PipelineReal.ESTADO_APROBADO)]` → `true`, sin violaciones.
   Mejor aún, ese y `[parte(PipelineReal.ESTADO_APROBADO), parte(null, true)]`
   (pendiente delante de un terminado). Al terminar, N14 (`let i = 1` en
   `js/guarda_salida.js:85`) tiene que morir, con su salida real en el
   informe.
2. **H16-9 (recomendado en el mismo commit, no bloquea).** Que `navegador()`
   apunte también el tercer argumento de `addEventListener` (por ejemplo,
   `registro.escuchas.push({ tipo, manejador, opciones })`), y que el test
   vm de H16-1 y el de R80 «instalar registra exactamente un
   beforeunload…» exijan `opciones === undefined`. Al terminar, N5 y N6
   tienen que morir.
3. En `progress/impl_F-035.md`, la nota con N14 (y N5 y N6 si se hace el 2)
   muertas y `bash harness/init.sh` en verde. Ningún cambio de producción.

### Observaciones sin acción

- **O16-4**: el control en memoria que pedía el cambio 1 de la review
  (la fuente sin `instalar(…)` no deja ninguna escucha) no está como test,
  y el informe no lo menciona. G1 muere de forma reproducible (el
  implementer y yo), así que el test **no** es vacuo hoy; el control lo
  blindaría frente a un cambio futuro del doble. Opcional, si se toca el
  fichero por H16-8.
- **O16-5**: H16-7 (el estático que ata los nombres que lee la guarda) sigue
  abierto, como estaba previsto: bloque 17.

### Automejora (propuesta, no aplicada)

**P-R6 · Amplía P-R5 (para `arnes-base`, vale para cualquier proyecto).**
Cuando un test fija un recorrido, los positivos deben poner el elemento que
decide en la **primera** posición, en una **intermedia** y en la **última**,
y debe haber un caso de **un solo elemento**. Y las mutaciones a mano de un
bucle incluyen siempre los dos extremos (`i = 1` y `length - 1`).

*Caso de origen.* F-035, re-review del bloque 16: N14 vivo con los siete
positivos de (c) en el índice 1. Mi G13 de la review anterior miraba solo
uno de los dos extremos.

**P-R7 · Para los dobles de `addEventListener` (`arnes-base`, fronts).** Un
doble de `addEventListener` apunta **todos** sus argumentos, no solo el
evento. Si no, `{ once: true }` o `{ passive: true }` pasan sin que se vean.

*Caso de origen.* F-035, re-review del bloque 16, H16-9 (N5, N6).

## Re-review final del bloque 16 · cierre de H16-8 y H16-9 · 2026-10-05

> reviewer. Alcance **cerrado** a `git diff df88470..HEAD`: `e20765e` (H16-8),
> `07058b6` (H16-9) y `8f1a56c` (informe y estado). Solo tests, en
> `services/postventa-front/tests_js/guarda_salida.test.js`. **Límite expreso
> del humano (2026-10-05)**: esta vuelta solo comprueba que H16-8 y H16-9
> quedan cerrados, sin abrir familias ni variantes nuevas. No se ha probado
> ninguna mutación fuera de N14, N5 y N6.

### Veredicto

**APPROVED** (del bloque 16, no de la feature). H16-8 y H16-9 cierran.

### Las tres preguntas del líder

| Pregunta | Respuesta |
|---|---|
| ¿N14, N5 y N6, cada una sola y en copia desechable, caen en rojo con los tests nuevos? | **Sí, las tres** (tabla siguiente) |
| ¿La suite JS en verde sobre el código real? | **Sí**: `guarda_salida.test.js` **60/60**; `tests_js/*.test.js` **569/569** (Node v24.14.1) |
| ¿`git diff df88470 HEAD -- services/postventa-front/js/` vacío? | **Sí**: 0 líneas |

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, árbol real) | **exit 0**, `ENTORNO LISTO`. Raíz 112 passed; api y front en verde (caché del árbol); `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos, deuda previa |
| `git diff --stat df88470..HEAD` | 3 ficheros: `guarda_salida.test.js` (+36 −2), `progress/impl_F-035.md`, `progress/current.md`. Nada de producción |
| Mutaciones a mano | guion `mutar_b16_final.py` del scratchpad: copia `services/postventa-front/` entero a una carpeta desechable, aplica cada mutación **sola** con el patrón exigido a una aparición (el fichero está en LF), pasa `guarda_salida.test.js` y la suite Node entera con reporter TAP, y rehace la copia en cada vuelta. Un **CONTROL** sin mutar en la misma copia da 60/60 y 569/569, así que los rojos son de la mutación y no del entorno. La copia se borró al final |
| Al acabar | `git status` del árbol real limpio antes del commit |

| # | Mutación (`js/guarda_salida.js`) | Resultado | La matan |
|---|---|---|---|
| **N14** | (c) el bucle empieza en `let i = 1` (l. 85) | **muerta** (58/60; suite 567/569) | `f035 R79 (c): una remesa de un solo parte aprobado sin cerrar…` y `f035 R79 (c): con el único pendiente en primer lugar, delante de uno cerrado…`, los dos de H16-8 |
| **N5** | `instalar` con `}, { once: true });` (l. 148) | **muerta** (58/60; suite 567/569) | `f035 R80: instalar registra exactamente un beforeunload…` y `f035 R78: cargada como script en la página…`, por la aserción nueva de `opciones` |
| **N6** | `instalar` con `}, { passive: true });` (l. 148) | **muerta** (58/60; suite 567/569) | los mismos dos que N5 |

Coinciden con las salidas reales del informe del implementer (mismos tests,
mismos 58/60). Las tres caen con tests **de esta feature**.

### H16-8 y H16-9: ¿cierran?

- **H16-8, sí.** Los dos positivos nuevos ponen el pendiente en el índice 0:
  `[aprobado]` (la remesa de un solo parte) y `[aprobado, cerrado: true]`.
  Los dos exigen `true` y cero violaciones del Proxy, en fase `resumen`, donde
  solo decide (c). Es justo lo que pedía el cambio 1.
- **H16-9, sí.** El doble `navegador()` apunta el tercer argumento
  (`{ tipo, manejador, opciones }`), y los dos tests que pedía el cambio 2 (el
  vm de H16-1 y el R80 de «exactamente un beforeunload») exigen
  `opciones === undefined`. El código real registra sin tercer argumento, así
  que la aserción es cierta hoy y cae con `once` o `passive`.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` exit 0 (ejecutado por el reviewer).
- **C2** [x] Una sola feature `in_progress` (F-035), rama
  `feature/F-035-portal-posventa`; `current.md` con la entrada nueva arriba.
- **C3** [x] Solo tests: `js/` sin diff; sin `console.*`, `debugger`,
  secretos ni dependencias nuevas; comentarios en español. Hexagonal y reglas
  de dominio: **N/A justificado**, el diff no toca código de producción.
  [x] Ningún PDF ni parte en git.
- **C3 bis** — **N/A**: no toca `docs/referencia/`.
- **C4** [x] R79 (c) con el pendiente en la primera posición y en la única;
  R78/R80 con el registro sin opciones. Sin red ni BBDD.
- **C4 bis** [x] `rigor: "estandar"`. Fase RED: N14, N5 y N6 con salida real
  en el informe y **reproducidas** por mí. Cobertura: N/A con el motivo
  impreso por `init.sh` (solo tests JS). Mutación de la herramienta: 0
  mutantes con base `df88470`, legítimo (el diff no tiene Python de
  producción; el control del cero se hizo en la review del bloque); no se
  reejecuta, el informe del implementer fue al scratchpad. Mutantes a mano:
  3 de 3 muertos. «Evidencias» con los cuatro números. Regla 7 (orden): N/A,
  es de rigor `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5** [x] Commits `F-035 H16-8: …`, `F-035 H16-9: …` y el del informe.
  Sin ficheros sin trackear.

### Informativo (para después, no bloquea)

Nada nuevo: por el límite del humano no se ha buscado. Siguen abiertos, como
estaban, O16-4 (el control en memoria sin `instalar(…)`, opcional) y H16-7
(bloque 17); H16-3 a H16-6 siguen para el spec-author en el bloque 14.
