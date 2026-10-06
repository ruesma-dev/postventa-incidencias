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

## Review del bloque 17 · T46–T47 y H16-7 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 7e69c69..HEAD`: `15aa0a7` (T46),
> `6839be6` (H16-7), `04802ed` (T47, guardia extra) y `9840c02` (evidencias)
> en `feature/F-035-portal-posventa`. El remodelado de `partes.html` (R82)
> es solo presentación. Los bloques 9–15 siguen abiertos **a propósito**: no
> cuentan como `[ ]`. El vistazo en navegador queda para V1/V2 del humano.
> Criterio de severidad del líder: es bloqueante lo que deja un riesgo real
> para el usuario o incumple la spec. Lo demás va como informativo, con su
> destino.

### Veredicto

**APPROVED** (del bloque 17, no de la feature).

- El cambio es solo de presentación, comprobado atributo a atributo.
- No queda ninguna utilidad de color ni de tipografía de Tailwind en los
  `class` estáticos de `partes.html`, salvo la excepción de R82.
- Las clases nuevas usan tokens y no traen ningún par de contraste nuevo.
- H16-7 cierra.
- De 26 mutaciones de 6 familias mueren 20. Las 6 que sobreviven son
  estéticas o tienen ya un bloque de destino (ver «Informativo»).

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes. Lo compensan las
mutaciones a mano: la 36 de §16.15.8, las 13 del implementer y las 26 del
reviewer.

La regla 7 de `reviewer.md` (orden) es **N/A**: solo aplica en rigor
`critico`, y aquí no hay orden entre colaboradores que proteger.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, en el árbol real | **exit 0**, `ENTORNO LISTO`. Raíz 112 passed; api y front en verde (desde caché); `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; ruff, 71 avisos de deuda previa |
| Front `python -m pytest tests -q -p no:cacheprovider` en el árbol real, sin caché | **540 passed**, 13,26 s. Con `-k "r82 or h16_7"`: 67 passed |
| `node --test "tests_js/*.test.js"` | **569/569** |
| `git diff --stat 7e69c69..HEAD -- services/postventa-front/js services/postventa-api` | **vacío** |
| `partes.html` de `7e69c69` frente a HEAD, con `html.parser` (guion `cmp_attrs.py` en el scratchpad) | 562 eventos en los dos lados. Cambian **17 valores de `class`** y el `href` de la hoja (`?v=064ee0dc11` → `?v=5c6cb12598`). **Nada más**: ningún otro atributo (`:class`, `x-*`, `@*`, `id`, `type`…), ningún texto, ningún comentario, ni el orden de atributos o elementos |
| Barrido propio (no el detector del test) de los `class` estáticos de HEAD: color de cualquier paleta en `text-`, `bg-`, `border-`, `divide-`, `ring-`, `from-`/`to-`/`via-`, `fill-`, `stroke-`, `placeholder-`, `outline-`, `decoration-`, `accent-`, `caret-` y `shadow-`, más los tamaños y pesos de letra | **una sola**: `text-red-800` en `<p x-show="estadoAutoguardado === 'fallo'">` (l. 341), la excepción de R82 |
| Las 17 reversiones en memoria, una a una (cada `class` nuevo devuelto a su valor viejo, en cada aparición) contra `problemas_r82` | **0 vivas**. Y la barra con `text-sky-700 hover:underline` en una `rs-pestana` también salta |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `lineas={}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el «Tiempo total» declarado es 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre los `.py` del diff, ignorando la exclusión | `test_f035_paginas.py`: 274 líneas, **42 mutantes**. El generador funciona y el cero es **legítimo**: solo cambian tests, HTML y CSS |
| `git log --diff-filter=A 7e69c69..HEAD` | no se añade ningún fichero |
| Mutaciones a mano | worktree desechable en el scratchpad sobre `9840c02`. Las del circuito (R59, R33) se repitieron en una rama temporal con el prefijo `feature/F-035`, porque con la HEAD separada esas 3 guardias se saltan. En las de CSS se recalculó la `?v=` de las cuatro páginas, para que no las matara T21 por accidente. Al final se retiraron el worktree y la rama temporal; `git status` limpio |

### Mutaciones del reviewer, por familias

Cada mutación se aplicó **sola**, con la suite del front entera. Línea base:
540 passed en la rama con prefijo y 537 passed + 3 skipped con la HEAD
separada.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **Reglas nuevas que faltan** | C-a | sin la regla `.rs-texto` | muerta | guardia `cada_clase_rs…tiene_regla` y su control |
| | C-b | sin la regla `.rs-texto--apagado` | muerta | las mismas dos |
| | C-e | sin la regla `.rs-panel__franja` | muerta | las mismas dos |
| | C-c | sin la regla de color de `.rs-rotulo--atencion` (queda su `::before`) | **sobrevive** | informativo O17-1 |
| | C-d | sin `.rs-rotulo--atencion::before` | **sobrevive** | informativo O17-1 |
| **Tokens (R49, R53, R60)** | C-f | `.rs-texto` con `color: #475569` | muerta | R49 `[styles.css]` |
| | C-k | `.rs-panel__franja` con `#e2e8f0` | muerta | R49 |
| | C-l | `.rs-rotulo--atencion` con `rgb(146, 64, 14)` | muerta | R49 |
| | C-g | `.rs-texto--apagado` con `var(--rs-acero)` | muerta | R53 (`el_acero_no_se_usa_como_color_de_texto`) |
| | C-j | `!important` en `.rs-texto` | muerta | R60 |
| | C-h | `.rs-texto--apagado` con `var(--rs-acero-100)` (contraste ≈1,3) | **sobrevive** | informativo O17-2 |
| | C-i | `.rs-texto` a `0.5rem` | **sobrevive** | informativo O17-1 |
| **Versión de la hoja** | V-c | `partes.html` con la `?v=` vieja | muerta | T21 (×2) |
| | V-a | `importar.html` sin `?v=` | **sobrevive** | informativo O17-3 |
| | V-b | `oficios.html` con la `?v=` vieja | **sobrevive** | informativo O17-3 |
| **Solo presentación (R59, R33)** | D-a | `:class` de la zona: `bg-sky-50` → `bg-sky-100` | muerta | R59 `solo_cambia_en_presentacion` |
| | D-b | `x-show` de los avisos: `… > 0` | muerta | R59 |
| | D-c | texto «Avisos de la remesa» → «Avisos» | muerta | R59 |
| | D-d | `class` delante del `x-show` en `<p class="rs-texto">` | muerta | R59 |
| | D-e | `:class` añadido a la lista de partes | muerta | R59 |
| | D-f | comentario `── 3 · Avisos…` recortado | muerta | R59 |
| | D-h | `id` añadido a la pregunta de confirmación | muerta | R59 |
| | D-g | sin `text-red-800` en el aviso del autoguardado | muerta | F-026 R52, la excepción de R82 y el control de R59 |
| | J-a | un comentario en `js/app.js` | muerta | R33 |
| **H16-7** | H-a | la guarda lee `estado.autoguardado` | muerta | `h16_7_los_nombres…` y F-007 R32 (Node) |
| | H-b | `app.js` declara `estadoAutoguardo:` | muerta | `h16_7_los_nombres…` y su control |
| | H-c | `SELECTOR_CIRCUITO` a `appCircuito()` | muerta | `h16_7_…unico_elemento_del_selector` y F-007 R32 |

**20 de 26 muertas**, todas por tests de esta feature salvo D-g, que además
cae con F-026. Las 6 vivas no son bloqueantes con el criterio del líder.

### Respuestas a las preguntas del líder

**1 · ¿Es solo presentación?** **Sí.**

- `js/` no tiene diff, y `services/postventa-api/` tampoco.
- En `partes.html` cambian solo los 17 valores de `class` y la `?v=`. Ningún
  `:class`, `x-*` ni `@*`, comprobado atributo a atributo con el parser, no
  leyendo el diff.
- Las directivas de ESTADO están intactas: el semáforo (l. 199 y 366), el
  dudoso (l. 298 y 304), el arrastre de la zona (l. 86) y el parte abierto
  (l. 182).
- Siguen ganando sobre el aspecto por defecto. Ninguna clase nueva fija
  fondo, y el color que fijan `.rs-texto` y `.rs-texto--apagado` es
  (0,1,0), el mismo que las utilidades que el CDN inyecta después.
- Los `:class` del semáforo van en `rs-punto` y los del chip en `rs-chip`, no
  en las clases nuevas. Ningún `:class` cae sobre un elemento con `rs-texto`,
  `rs-rotulo--atencion` ni `rs-panel__franja`.
- La lista de partes conserva su `bg-slate-50` del parte abierto sobre
  `rs-fila`, que ya estaba así.

**2 · Tailwind, tokens y contraste.**

- **Utilidades de color de Tailwind en los `class` estáticos: ninguna**, con
  mi barrido y con el detector. Solo queda la excepción `text-red-800`.
- El detector `utilidades_prohibidas` implementa la lista cerrada de §16.5
  tal cual: prefijos, enteras, alineaciones admitidas y quitado de `hover:`,
  `sm:`… y de `!`.
- **Las clases `rs-*` nuevas usan solo tokens**: `--rs-tinta-suave`,
  `--rs-acero-texto`, `--rs-atencion`, `currentColor` y `--rs-linea`. R49 lo
  vigila (C-f, C-k y C-l mueren).
- **Contraste**: ningún texto queda por debajo de §15.6. Comprobé el fondo
  real de cada elemento cambiado:

| Elemento | Par | Contraste (§15.6) |
|---|---|---|
| `rs-texto` en la zona (`rs-zona`, o `bg-sky-50` al arrastrar), en los paneles y en la pregunta de confirmación | `--rs-tinta-suave` sobre `--rs-papel` | 8,27 (algo menos sobre `sky-50`, muy por encima de 4,5) |
| `rs-texto` del estado del parte (`rs-panel--suave`) | `--rs-tinta-suave` sobre `--rs-lienzo` | 7,51 |
| `rs-texto--apagado` («Lo dice la validación…» y «— obligatorio para rechazar…»), los dos dentro de `rs-panel--suave` | `--rs-acero-texto` sobre `--rs-lienzo` | 5,26 |
| `rs-nota` del motivo (`rs-panel--suave`) | `--rs-acero-texto` sobre `--rs-lienzo` | 5,26 |
| rótulo y lista de «Avisos de la remesa» (`rs-panel--atencion`) | `--rs-atencion` sobre `--rs-atencion-suave` | 6,84 |

- Lo que era `text-slate-400`, por debajo de 4,5 sobre blanco, **mejora** a
  5,26.
- El implementer hizo bien en no dejar `rs-rotulo` a secas sobre el fondo
  ámbar: ese par no está medido. Calculado por mí da unos 5,6, así que
  tampoco habría sido un fallo.

**3 · Los apuntes del §5: los tres, bien.**

1. **El separador nuevo (`rs-panel__franja`) en lugar de tocar
   `.rs-panel--lista`: bien.** `index.html` usa `rs-panel--lista` en
   **cinco** paneles (l. 236, 529, 838, 891 y 971), no en cuatro como dice el
   informe. Una regla ahí le cambiaría el aspecto al portal. §16.15.5 admite
   «uno nuevo si ninguno sirve», y el nuevo no fija relleno, así que no choca
   con `px-4 py-3` (regla 3 de §15.7).
2. **La `?v=` también en `importar.html` y `oficios.html`: bien.** Lo pide la
   letra de T46 («su `?v=` en las cuatro páginas»). R59 no mira esas páginas
   y ningún test de F-036 lee esa `<link>`: la suite sigue verde. Hoy ningún
   test la vigila (V-a y V-b sobreviven), pero el bloque 10 ya lo tiene
   previsto (`tasks.md` l. 639: «las extensiones … de la `?v=`»). Ver O17-3.
3. **R82 mira también la barra: bien.** Es más estricto que la letra y hoy se
   cumple. Lo comprobé con una `rs-pestana` con `text-sky-700 hover:underline`
   en memoria, y salta.

Dos apuntes más:

- La guardia extra (cada `rs-*` estático con su regla en la hoja) está bien
  pensada. Cierra un hueco real que T21 solo tapaba por accidente.
- `rs-resumen mt-2` mezcla `margin: 0` con `mt-2`. Es margen, que la regla 3
  no prohíbe, y el patrón ya existía (`rs-resumen mt-4`).

**4 · H16-7: cerrado.** Pedía dos cosas, y están las dos:

- **Que `app.js` declare lo que lee la guarda.** El test exige
  `estado.fase|partes|parteAbierto|estadoAutoguardado` y `.cerrado` en la
  guarda, sin comentarios, y sus declaraciones `<nombre>:` en `app.js`.
  Muerde por los dos lados: H-a renombra en la guarda y H-b en `app.js`, y
  las dos mueren. El control comprueba además que hay **una sola**
  declaración de cada nombre. Así, si F-021 o F-045 añadieran otra
  `partes:`, sería ese control el que obligara a revisar la regla.
- **Un único elemento de `partes.html` que case con `SELECTOR_CIRCUITO`.** El
  selector se lee de la propia guarda, no se copia en el test, y H-c muere.
  Con un `x-data` duplicado, R59 caería además.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo). [x] Existen los
  ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba, como en los bloques anteriores. [x] Ninguna feature pasa a `done`
  en este diff.
- **C3** [x] Primera línea con la ruta en los ficheros tocados (sin cambios
  ahí). [x] Sin `print`, `console.*`, `debugger`, TODO ni secretos en el
  diff, y sin dependencias nuevas. [x] Comentarios en español. [x] Ningún PDF
  ni parte en git: `--diff-filter=A` vacío. Arquitectura hexagonal, unidad
  de trabajo «parte», Sigrid, firma, «firmado no es conforme», duplicados y
  `conest`: **N/A justificado**, porque el diff no toca código de producción
  ni lógica (solo HTML de presentación, CSS y tests).
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4** [x] R82 tiene su test trazable
  (`test_f035_r82_partes_html_no_lleva_utilidades…`) con controles, y H16-7
  los suyos. Todos pasan. [x] Sin red ni BBDD: los tests leen ficheros del
  repo. [x] El MANUAL (el vistazo de T46) consta en `current.md`, que lo
  manda a V1/V2.
- **C4 bis** [x] `rigor: "estandar"`. [x] **Fase RED**: el informe trae la
  salida real del fallo de R82 sobre la página sin remodelar, con 30
  utilidades en 17 elementos, coherente con mis 17 reversiones. H16-7 no
  tiene RED porque ata nombres que ya existen; lo demuestran sus controles y
  mis H-a, H-b y H-c. [x] **Cobertura**: N/A con el motivo impreso por
  `init.sh`. [x] **Mutación**: informe de la herramienta con 0 mutantes,
  recalculado, reejecutado y con el control del cero hecho. [x] El coste por
  mutante no aplica, porque hay 0 mutantes. [x] Mutantes a mano: 14/14 del
  implementer y 20/26 del reviewer, con las 6 vivas analizadas abajo (rigor
  `estandar`: basta con documentarlas). [x] «Evidencias» con los cuatro
  números y los workers (1). [x] Ningún N/A sin justificar. Regla 7: N/A,
  porque es de `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T46 y T47 están `[x]`, con commits `F-035 T46: …`,
  `F-035 T47: …` (×2) y `F-035 H16-7: …`. [x] No hay ficheros sin trackear.
  [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **O17-1 · Lo puramente visual de las clases nuevas lo ve solo el ojo.**
  Sobreviven C-c, C-d e C-i:
  - C-c quita el color del rótulo de avisos: queda gris sobre ámbar, unos
    5,6, legible.
  - C-d quita su trazo ámbar: vuelve el burdeos.
  - C-i encoge `.rs-texto`.

  Ninguna deja un riesgo de contraste ni de función, y fijar tamaños o trazos
  con tests sería sobreespecificar. **Destino: V1/V2 del humano**, que ya
  incluyen el vistazo de T46. El implementer dejó escrito qué mirar.
- **O17-2 · R53 no exige que cada color de texto sea un token de texto
  medido.** C-h (`.rs-texto--apagado` con `var(--rs-acero-100)`, contraste
  ≈1,3) sobrevive. R53 prohíbe solo `var(--rs-acero)`, que es el error
  plausible (C-g muere), y comprueba los pares de §15.6, no qué token usa
  cada regla. El hueco ya existía, vale para cualquier regla de la hoja (por
  ejemplo, `rs-nota`) y nadie escribiría ese marcado a propósito.
  **Destino: spec-author, bloque 14.** Sería una lista blanca de tokens
  admitidos en `color:` fuera de `:root`.
- **O17-3 · La `?v=` de `importar.html` y `oficios.html` no la vigila nadie
  todavía.** V-a y V-b sobreviven. **Destino: bloque 10**, que ya extiende
  T21 a esas páginas (`tasks.md` l. 639).
- **O17-4 · Erratas del informe, sin efecto.** Son **17** `class` estáticos,
  no 18 (H-12 contaba 20, de los que 2 pasaron en el bloque 8 y queda
  `text-red-800`). `rs-panel--lista` está en **5** paneles del portal, no en
  4.
- **O17-5 · Efecto visual que esperar en V1/V2.** La lista de partes pasa de
  1 rem heredado a los 0,9 rem de `rs-resumen`. El separador de filas ya no
  dibuja una línea sobre el primer parte: `li + li` frente al `divide-y` de
  antes, que con el `<template>` delante sí la dibujaba. Es coherente con el
  portal y no hace falta hacer nada.
- Siguen abiertos, como estaban: **O16-4** (opcional), **H16-3 a H16-6**
  (spec-author, bloque 14) y **H-5** (bloque 9).

### Automejora (propuesta, no aplicada)

**`reviewer.md`**: avisar de que, en un worktree con la HEAD separada, las
guardias de diff de rama (R30/R43, R32, R33, R59 de F-035) se **saltan**
(«sin rama») y las mutaciones del circuito salen vivas en falso. En esta
review pasó con 8 mutaciones de R59/R33 hasta que las repetí en una rama
temporal con el prefijo `feature/F-XXX`.

La regla propuesta: si la línea base del worktree trae `skipped` que en el
árbol real no salen, crear la rama temporal y borrarla al acabar. Es
genérica para cualquier proyecto cuyas guardias dependan de la rama, así que
iría también a `arnes-base`.

## Review del bloque 9 · T27–T28 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 22d8820..HEAD`: `39fa3e6` (T27)
> y `81b0f78` (T28), en `feature/F-035-portal-posventa`. Son los recuadros
> «En construcción» y la portada sin cifras (R63–R67, R69), con H-3, H-4
> (puntos 2 y 3) y H-5 de la review del bloque 7.
>
> Decisión del humano: opción (b). Lo que no funciona se publica visible y
> marcado. El riesgo aceptado es que alguien tome lo inventado por real, y lo
> mitiga el rótulo en tres capas (D-12).
>
> Los bloques 10–15 siguen abiertos **a propósito** y no cuentan como `[ ]`.
> El vistazo en navegador queda para V1/V2 del humano.
>
> Criterio de severidad del líder: es bloqueante lo que deja un riesgo real
> para el usuario o incumple la spec. Una mutación que solo se distingue con
> un marcado que nadie escribiría, o una variante de una familia ya cubierta,
> va como informativo con su destino.

### Veredicto

**APPROVED** (del bloque 9, no de la feature).

- Recorrí `index.html` entero y lo que pinta `js/maqueta_datos.js`. Ningún
  dato inventado de la maqueta queda fuera de un recuadro. Hay una salvedad
  estática, ya existente y rotulada «Por ejemplo» (O9-1).
- Ninguna sección real lleva recuadro ni rótulo de construcción.
- La portada no enseña ninguna cifra.
- El enlace de R69 es claro.
- No se ha tocado nada de F-036 ni del circuito.
- H-3, H-4 (puntos 2 y 3) y H-5 quedan cerrados.
- De 20 mutaciones mías en 7 familias, sobreviven 9. Ninguna corresponde a
  algo que esté hoy en la página. Todas exigen un marcado que nadie escribe a
  propósito, o son variantes de familias que ya están cubiertas. Van como
  informativo, con su destino.

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes (control del cero
hecho más abajo). Lo compensan las mutaciones a mano: las 23 del implementer
y las 20 mías.

La regla 7 de `reviewer.md` (orden) es **N/A**: solo aplica en rigor
`critico`, y aquí no hay orden entre colaboradores que proteger.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, en el árbol real | **exit 0**, `ENTORNO LISTO`. Raíz 114 passed. Front 581 passed (8,28 s, ejecutado, no desde caché). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. ruff, 71 avisos de deuda previa |
| `node --test "tests_js/*.test.js"` | **576/576** |
| `git diff --stat 22d8820..HEAD` sobre `services/postventa-api`, `js/importacion.js`, `js/oficios.js`, `js/app.js`, `js/guarda_salida.js`, `tests/test_f036_front.py`, `tests_js/importacion.test.js` y `tests_js/oficios.test.js` | **vacío** |
| `git diff --numstat 22d8820..HEAD -- *.html` | `importar.html` `2 2` (el `id="bandeja"` y la `?v=`). `oficios.html` y `partes.html`, `1 1` (solo la `?v=`) |
| Qué páginas cargan `css/portal.css` | solo `index.html`: el recuadro y el renombrado no alcanzan a las páginas reales |
| Directivas de Alpine **fuera** de todo `data-en-construccion` (guion propio con el parser de los tests, no el detector de R63) | Solo hay: el `x-data`/`x-init` raíz, los `:aria-current` de la barra, los `x-show` de las secciones y el aviso del placeholder (`aviso`). **Ninguna lee datos**, ni directamente ni a través de un método del componente |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `{}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el «Tiempo total» declarado es 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre los `.py` del diff, ignorando la exclusión | `test_f035_paginas.py`: 147 mutantes. `tests/test_f035_placeholders_vivos.py`: 9. El generador funciona y el cero es **legítimo**: solo cambian tests, HTML, CSS y JS |
| `git log --diff-filter=A 22d8820..HEAD` | no se añade ningún fichero |
| `console.*`, `debugger`, `print(`, `TODO` en las líneas añadidas | ninguno |
| Mutaciones a mano | En un worktree desechable del scratchpad, sobre `81b0f78`, con una rama temporal con prefijo `feature/F-035` para que no se salten las guardias de rama. Línea base: 581 passed, 0 skipped. Al final se retiraron el worktree y la rama, y `git status` quedó limpio |

### Mutaciones del reviewer, por familias

Cada mutación se aplicó **sola**, con la suite entera del front, y con Node
cuando la mutación tocaba JS. Las de CSS se midieron con `-k "not t21"`,
porque T21 (la versión de las hojas) cae con cualquier cambio de CSS.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **A · Lo inventado fuera de un recuadro** | A3 | `x-text="bandejaFiltrada().length"` en la pestaña «Bandeja» de la barra | muerta | barra estática (Node, vía F-007 R32) |
| | A1 | «Hay 7 entradas por revisar.» escrito a mano en la cabecera de `bandeja` | **sobrevive** | O9-2 |
| | A2 | `x-text="bandejaFiltrada().length + ' por revisar'"` en la cabecera de `bandeja` | **sobrevive** | O9-2 |
| | A4 | `x-text="'Última obra: ' + obra('9901')"` en la tarjeta «Partes firmados» (en producción) | **sobrevive** | O9-2 |
| | A5 | «23 partes archivados este mes.» escrito a mano en «Partes firmados» | **sobrevive** | O9-2 |
| | A6 | `x-text="bandejaFiltrada().length…"` en la tarjeta real «Importar» de `entrada` | **sobrevive** | O9-2 |
| **B · Lo real vestido de construcción** | B1 | `data-en-construccion="F-036"` en la tarjeta real «Importar» | muerta | R64 (bloque) y R65 (×2) |
| | B5 | chip «En construcción» en la tarjeta real «Importar» de `entrada` | muerta | `r68_entrada_enlaza_a_la_pagina_real…[importar.html]` |
| | B6 | `data-construccion` en la pestaña «Entrada» | muerta | R66 (Node, vía F-007 R32) |
| | B4 | clase `rs-obras` (el marco ámbar) en la tarjeta real «Importar», sin el atributo | **sobrevive** | O9-3 |
| **C · El rótulo** | C1 | el rótulo F-045 con `titulos['F-037']` | muerta | `r65_cada_recuadro_empieza_por_un_rotulo…` |
| | C4 | `class="rs-obras__rotulo hidden"` | **sobrevive** | O9-4 |
| | C5 | `style="display:none"` en el rótulo | **sobrevive** | O9-4 |
| **D · El enlace de R69** | D3 | el enlace sale del rótulo y pasa al contenido del recuadro | muerta | `r69_el_recuadro_de_bandeja_enlaza…` y el control de B9-19 |
| | D5 | el texto del enlace pasa a «aquí» | muerta | `r69_el_recuadro_de_bandeja_enlaza…` |
| **G · CSS del recuadro** | G6 | `.rs-obras__rotulo .rs-enlace:hover { color: var(--rs-burdeos) }` | muerta | `r56_ningun_recuadro_usa_el_discontinuo_ni_el_burdeos` |
| | G1 | el borde de `.rs-obras` en `--rs-linea` (gris) | muerta **solo por el control** (deja de encontrar su cadena); en sustancia, sobrevive | O9-5 |
| | G4 | `.rs-obras__rotulo { display: none; }` en la hoja | **sobrevive** | O9-4 |
| **F · `fichasDeSeccion`** | F4 | la lista en orden inverso | muerta | Node (3 tests de R65) |
| **I · El renombrado del §5** | I1 | la lista por obra vuelve a `class="rs-obras"` | muerta | `h5_ninguna_clase…` y su control |

**11 de 20 muertas**, contando G1 entre las vivas. Las 9 vivas forman tres
familias. Todas exigen un marcado que hoy no está en la página y que nadie
escribe a propósito: no son bloqueantes con el criterio del líder.

### Respuestas a las preguntas del líder

**1 · Mirándolo como lo verá Posventa.** Recorrí `index.html` línea a línea
y lo que pinta `MaquetaDatos`.

- **¿Hay datos inventados fuera de un recuadro? No, salvo uno estático y
  rotulado.**
  - Todo lo que lee `datos.` o los métodos del componente que los usan
    (`bandejaFiltrada`, `obra`, `propuesta`, `vinculo`, `importe`…) está
    dentro de su recuadro. Lo comprobé con mi propio listado de directivas
    fuera de los recuadros (tabla de arriba), no solo con el detector de
    R63.
  - Fuera quedan solo textos fijos: la barra, el aviso, la portada, las
    cabeceras de sección y el pie.
  - Única salvedad: la tarjeta «Partes firmados», que está en producción,
    enseña «Por ejemplo: `9901  EJEMPLO NORTE/PARTES INCIDENCIAS/VILLA
    003/PARTES FIRMADOS`». Ver O9-1.
  - La cabecera de «Coste y venta» nombra POSTV2: es la obra real de Sigrid,
    no un dato inventado.
- **¿Alguna sección real lleva recuadro o un rótulo que la haga parecer de
  mentira? No.**
  - `partes.html`, `importar.html` y `oficios.html` solo cambian en la
    `?v=` (más el `id` en importar) y no cargan `portal.css`.
  - En `entrada`, las dos tarjetas reales están en su rejilla, con «En
    producción». El recuadro F-037 va aparte, debajo, y R68 (H-3) fija esa
    estructura.
  - La tarjeta «Partes firmados» lleva el recuadro F-045 **debajo** de su
    primario. Su rótulo dice «Todavía no funciona…» y «Lo construirá F-045 ·
    Registrar un parte sin firma…». Se lee como un bloque aparte, pero
    conviene mirarlo en V1 (O9-6).
  - Las pestañas reales no llevan el punto ámbar (B6 muere).
- **¿La portada enseña alguna cifra? No.**
  - Han desaparecido `rs-tarjeta__cifra`, `contadores()` y
    `contadoresInicio`.
  - Las tarjetas en construcción no tienen ni un dígito ni ningún
    `x-text`/`x-html`.
  - Los únicos números visibles son los índices decorativos 01–05 y 01–07
    (`aria-hidden`) y el 9901 de la ruta de ejemplo (O9-1).

**2 · El enlace de «Bandeja de revisión» a `importar.html#bandeja`: sí,
claro.**

- La frase dice «Mientras tanto, la bandeja de una obra ya se puede ver, en
  solo lectura, en Importar incidencias».
- Va dentro del rótulo, justo después de «Todavía no funciona…», así que no
  se confunde con el contenido inventado.
- Se abre en la misma ventana, sin `target` ni `rel`.
- El ancla existe y es la `<section>` correcta: la de `cargarBandeja()`,
  «3 · Bandeja de la obra».
- El color es el de atención, también al pasar el ratón: `.rs-obras__rotulo
  .rs-enlace` (0,2,0) va en `portal.css`, que se carga después de
  `.rs-enlace:hover` (0,2,0) en `styles.css`, así que gana. Conserva el
  subrayado.
- El anillo de foco en burdeos es el global de R54, igual que en los
  placeholders. No es color del rótulo.

**3 · Los apuntes del §5: bien.** No se ha tocado nada de la lógica de F-036
ni del circuito.

1. **`importar.html` en dos líneas: bien.** Son el `id="bandeja"` y la `?v=`,
   nada más (`numstat 2 2`). §16.5 pide la `?v=` en las cuatro páginas, y
   dejarla vieja serviría la hoja de caché. La verificación de T27 («una sola
   línea») es anterior al bloque 17. Ver O9-7.
2. **`rs-obras` → `rs-por-obra`: bien, y necesario.**
   - Sin el renombrado, el recuadro habría heredado `flex-wrap` y
     `list-style`.
   - Además, `.rs-obras > li` y `.rs-obras strong` habrían pintado cada
     `<li>` y cada `<strong>` dentro de los cinco recuadros de sección (la
     lista de fichas del rótulo, «seleccionadas»…).
   - No queda ningún `rs-obras` en una lista, y I1 muere por H-5.
3. **H-4 punto 3 hecho aquí: bien.**
   - Es una sola cadena de `maqueta_datos.js`: «…bloqueado por la web de
     clientes» sin «y por la importación del Excel», que ya existe.
   - Se pinta dentro del recuadro F-037.
   - El encargo decía «el resto de H-4», y el bloque 7 ya lo proponía para
     este bloque.

Lo demás del §5 también está bien:

- `fichasDeSeccion` filtra por `TITULOS_FICHAS`, así que no nombra una ficha
  hecha.
- `titulos['F-0NN']` sirve para los recuadros de bloque.
- En `incidencias`, el rótulo va encima del listado y de la ficha, y sigue
  visible con una ficha abierta.
- La guardia de H-5 está bien.
- La corrección de ruff no cambia nada de fondo.

Me parece **bien detectado** el fallo del propio guion del implementer:
mutaciones «muertas» por `No module named pytest`. Repitió la campaña
entera, y es justo lo que el arnés pide vigilar.

**4 · H-3, H-4 (puntos 2 y 3) y H-5: cerrados.**

- **H-3**: `problemas_de_entrada` fija la estructura cerrada de `entrada`
  (cabecera, rejilla con las dos tarjetas y recuadro F-037) y que no haya
  cifras fuera del recuadro. La mutación K muere (B9-17 y el control
  `dl-suelto`), y mi B5 también.
- **H-4 punto 2**:
  - La ceja es «Posventa».
  - La entradilla es la literal de §16.5.
  - Los chips son «En producción» y «En construcción».
  - El pie es nuevo.
  - Ningún texto visible dice «maqueta». Lo vigila
    `r67_ningun_texto_visible…`, con su control, y en Node los textos de
    `Portal` y de `MaquetaDatos`.
  - Quedan «maqueta» en atributos, clases y comentarios, que no se ven
    (O-3 del bloque 8).
- **H-4 punto 3**: hecho (respuesta 3).
- **H-5**: las cinco clases muertas que listaba están fuera, junto con las
  dos que deja muertas este bloque (`rs-tarjeta__cifra` y
  `rs-tarjeta__nota`). `clases_del_portal_css_sin_uso` impide que vuelvan.

**5 · Navegador**: queda para V1/V2 del humano. En `current.md` consta lo
que hay que mirar, y O9-5 y O9-6 lo amplían.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo). [x] Existen los
  ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba, como en los bloques anteriores. [x] Ninguna feature pasa a `done`.
- **C3** [x] La primera línea con la ruta sigue en los ficheros tocados.
  [x] Sin depuración, TODO ni secretos, y sin dependencias nuevas.
  [x] Comentarios en español. [x] Ningún PDF ni parte en git:
  `--diff-filter=A` vacío. Arquitectura hexagonal, unidad «parte», Sigrid,
  firma, «firmado no es conforme», duplicados y `conest`: **N/A
  justificado**, porque el diff es front de presentación (HTML, CSS, el
  catálogo de `portal.js`) y tests. No toca la API ni el circuito.
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4** [x] Cada requisito tiene tests trazables y todos pasan:
  - R63: `test_f035_r63_*` (3 controles).
  - R64: `test_f035_r64_*` (2 controles).
  - R65: `test_f035_r65_*` (6 controles, más el de B9-19) y Node.
  - R56 ampliado: `test_f035_r56_*` (3 controles).
  - R67: `test_f035_r67_*` (5 controles) y Node.
  - R69: `test_f035_r69_*`.
  - R28 (enmienda): `tests/test_f035_placeholders_vivos.py::test_f035_r28_el_escaner_*`.
  - H-3: `test_f035_r68_entrada_tiene_la_estructura_cerrada` (3 controles).
  - H-5: `test_f035_h5_*`.

  [x] Sin red ni BBDD. [x] El MANUAL (vistazo en navegador) consta en
  `current.md`, enviado a V1/V2.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae las salidas reales: raíz 2 failed,
    front 31 failed / 8 passed (los 8 explicados) y Node 9/9 failed.
  - [x] **Cobertura**: N/A con el motivo impreso por `init.sh`.
  - [x] **Mutación**: informe de la herramienta con 0 mutantes, recalculado,
    reejecutado y con el control del cero hecho. El coste por mutante no
    aplica, porque hay 0 mutantes.
  - [x] **Mutantes a mano**: 23/23 del implementer y 11/20 míos, con las 9
    vivas analizadas abajo. En rigor `estandar` basta con documentarlas.
  - [x] «Evidencias» con los cuatro números. Los workers son los de la
    cabecera de `mutacion_F-035.md` (1), y con 0 mutantes no influyen.
  - [x] Ningún N/A sin justificar. La regla 7 es N/A, porque es de
    `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T27 y T28 están `[x]`, con commits `F-035 T27: …` y
  `F-035 T28: …`. [x] No hay ficheros sin trackear. El worktree
  `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
  bloque. [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **O9-1 · La ruta de ejemplo de «Partes firmados».**
  - La tarjeta, que está en producción, enseña «Por ejemplo: `9901  EJEMPLO
    NORTE/…/VILLA 003/PARTES FIRMADOS`».
  - La obra 9901 «PROMOCIÓN EJEMPLO NORTE» es de `MaquetaDatos`, y el texto
    está fuera de un recuadro.
  - Ya existía (estaba en `22d8820`), §16.5 pide «su primario de siempre», y
    R63/R67 no la alcanzan: es texto fijo, no una cifra de cuadro de mando.
  - Explica dónde archiva el circuito real, va rotulada «Por ejemplo» y
    lleva «EJEMPLO» en el nombre. No veo riesgo de confusión.
  - **Destino: V1 del humano.** Si prefiere, se puede cambiar por la forma
    genérica (`<obra>/PARTES INCIDENCIAS/<vivienda>/PARTES FIRMADOS`).
- **O9-2 · R63 detecta los datos de ejemplo por patrones.** Es la familia
  de H-3, ahora fuera de `entrada`. Sobreviven A1, A2, A4, A5 y A6.
  - El detector reconoce `datos.`/`MaquetaDatos` en una directiva. No
    reconoce un método del componente que los lea (`bandejaFiltrada()`,
    `obra()`) ni una cifra escrita a mano.
  - Así que un contador en la cabecera de una sección, o en una tarjeta en
    producción de la portada, pasaría. R67 solo lo ve en las tarjetas en
    construcción.
  - La spec define así «datos de ejemplo», de modo que el test cumple la
    letra. Hoy no hay ninguno: mi listado lo confirma.
  - **Destino: spec-author, bloque 14.** Propuesta: enmendar R63 con una
    **lista cerrada de las directivas admitidas fuera de un recuadro**:
    `x-data`/`x-init` raíz, `:aria-current` de la barra, `x-show` de
    sección y las del aviso del placeholder. Es la forma robusta, porque no
    depende de qué métodos leen datos.
- **O9-3 · El aspecto de recuadro sin el atributo.**
  - `class="… rs-obras"` en una tarjeta real (B4) la enmarca en ámbar, y
    nada cae.
  - Nadie lo escribiría a propósito.
  - **Destino: el mismo que O9-2.** Sería una guardia de una línea: «la
    clase `rs-obras` solo en elementos con `data-en-construccion`, y todo
    `data-en-construccion` con `rs-obras`».
- **O9-4 · R65 «visible» solo mira atributos.**
  - Sobreviven C4 (`hidden` como clase), C5 (`style`) y G4
    (`display: none` en la hoja).
  - Es una variante de la familia «rótulo cerrable», que ya está cubierta:
    B9-5 `x-show` y el botón mueren.
  - La más verosímil es C4 en su forma responsive (`hidden md:flex`, para
    «ahorrar sitio en el móvil»), que escondería el rótulo justo en el
    teléfono.
  - **Destino: el mismo que O9-2.** Propuesta: añadir a `_CERRABLE` las
    clases `hidden`, `invisible` y `sr-only` (también con prefijo de
    pantalla) y el atributo `style`. Y comprobar que ninguna regla de
    `.rs-obras*` lleva `display: none`, `visibility: hidden` ni
    `opacity: 0`.
- **O9-5 · El color del marco solo lo ve el ojo.**
  - G1 (borde gris) solo cae porque el control de R56 deja de encontrar su
    cadena; la guardia en sí solo mira el discontinuo y el burdeos.
  - Lo mismo vale para la cinta.
  - Fijar colores con tests sería sobreespecificar.
  - **Destino: V1/V2 del humano**: cinta y borde ámbar en los cinco
    recuadros de sección y en los dos de bloque.
- **O9-6 · El recuadro F-045 dentro de una tarjeta «En producción».**
  - Su frase genérica («Lo que ves son datos inventados…») habla de datos
    donde solo hay un botón placeholder.
  - Además, queda dentro de la tarjeta que dice que el circuito funciona.
  - Cumple R64/R65 tal como están escritos.
  - **Destino: V1**: que se lea como «esto de aquí abajo todavía no», no
    como «la tarjeta no funciona». El implementer ya lo dejó en su lista.
- **O9-7 · La verificación de T27 en `tasks.md` está desfasada.** Dice «una
  sola línea cambiada (`id="bandeja"`)» en `importar.html`, y son dos por la
  `?v=` (§16.5). **Destino: spec-author, bloque 14**, una línea.
- Siguen abiertos, como estaban: **O16-4** (opcional), **H16-3 a H16-6** y
  **O17-2** (spec-author, bloque 14), y **O17-3** y **H-7** (bloque 10).

### Automejora (propuesta, no aplicada)

**`reviewer.md`, regla para cualquier proyecto con «detectores» de marcado
(va también a `arnes-base`).** Cuando un test vigila que «X no aparece
fuera de Y» con un detector por patrones, el reviewer genera además el
**listado positivo** de lo que hay fuera de Y (en este bloque, las
directivas fuera de los recuadros) y lo lee entero.

El detector solo demuestra que no está el patrón que conoce. El listado
demuestra que no hay nada más. Aquí fue lo que permitió afirmar que hoy no
hay ningún contador fuera de los recuadros, aunque A2, A4 y A6 sobrevivan al
test.

## Review del bloque 10 · T29–T30 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff 190b726..HEAD`: `9b31674` (T29)
> y `b72078d` (T30), en `feature/F-035-portal-posventa`. Es `importar.html`
> remodelado al estilo del portal (barra común, migas, subnavegación, pie,
> identidad Ruesma; R70–R73, R77), por la petición del humano de que las
> páginas existentes sigan el estilo del resto de la app. Es presentación:
> la lógica de F-036 no debe cambiar.
>
> Los bloques 11–15 siguen abiertos **a propósito** y no cuentan como `[ ]`.
> El vistazo en navegador queda para V1/V2 del humano.
>
> Criterio de severidad del líder: bloqueante es un riesgo real para el
> usuario o un incumplimiento de la spec. Una mutación que solo se distingue
> con un marcado que nadie escribiría, o una variante de una familia ya
> cubierta, va como informativo con su destino.

### Veredicto

**APPROVED** (del bloque 10, no de la feature).

- **La lógica de F-036 no ha cambiado.** `js/importacion.js`, `js/api.js`,
  `js/oficios.js`, `js/app.js`, `js/guarda_salida.js`, la API y los tres
  ficheros de tests de F-036 no tienen diff. En `importar.html` comparé con
  un parser los atributos funcionales de base y HEAD. La única directiva que
  cambia es el `:class` del resultado, y ese cambio lo pide la spec.
- **`enlaceSeccion(id, desde)`** cumple §16.8, R17, R44 y R46. Las ramas
  `"portal"` y `"circuito"` no se tocan.
- **Los estados se distinguen por la semántica de la marca y siempre llevan
  texto.** El «ya importado» en `info` es una desviación de la letra de
  §16.5, pero es la lectura coherente (O10-1).
- **H-7 y O17-3 quedan cerrados.**
- Hice 21 mutaciones en 6 familias y sobreviven 9. De ellas, 4 son huecos
  previos de los tests de F-036, 1 es equivalente, 2 exigen un marcado que
  nadie escribiría y 2 son de color, que solo se ven con el ojo. Ninguna
  corresponde a algo que esté hoy en la página. Van como informativo, con
  su destino.

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes (el control del
cero está más abajo). Lo compensan las mutaciones a mano: 53 del
implementer y 21 mías.

La regla 7 de `reviewer.md` (orden) es **N/A**. Solo aplica en rigor
`critico`, y además aquí no hay un orden entre colaboradores que proteger.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, en el árbol real | **exit 0**, `ENTORNO LISTO`. Raíz: 114 passed. Front: **628 passed** (21,24 s, ejecutado, no desde caché). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. ruff: 71 avisos de deuda previa |
| `node --test "tests_js/*.test.js"` | **597/597** |
| `git diff --stat 190b726..HEAD` sobre `services/postventa-api`, `js/importacion.js`, `js/api.js`, `js/oficios.js`, `js/app.js`, `js/guarda_salida.js`, `tests/test_f036_front.py`, `tests_js/importacion.test.js` y `tests_js/oficios.test.js` | **vacío** |
| `js/` en el diff | solo `portal.js`: +8/−1 (la rama nueva y su comentario) |
| Atributos funcionales de `importar.html`, base contra HEAD, con un guion propio sobre `html.parser`. Mira `x-*`, `@*`, `:*`, `id`, `name`, `for`, `type`, `accept`, `value`, `href`, `disabled` y `required`, junto con su etiqueta | Las directivas, `id`, `type` y `accept` son **idénticas**, con una excepción: el `:class` del resultado (Tailwind → `rs-aviso--*`, con el caso `yaImportado` delante). No había ni hay `name` ni `for`. Lo demás que cambia son `href`: las cuatro `<link>` de la marca, la `?v=` y los enlaces de la barra, las migas y la subnavegación |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `lineas={}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el informe declara un «Tiempo total» de 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre `test_f035_paginas.py` entero, ignorando la exclusión | 390 mutantes. El generador funciona y el cero es **legítimo**: el diff solo trae HTML, CSS, JS y tests |
| `git log --diff-filter=A 190b726..HEAD` | no se añade ningún fichero |
| `console.*`, `debugger`, `print(`, `TODO` en las líneas añadidas | ninguno |
| Mutaciones a mano | Las hice en un worktree desechable del scratchpad, sobre `b72078d`, con una rama temporal con prefijo `feature/F-035` para que no se salten las guardias de rama. Línea base: 628 passed, 0 skipped; Node, 597/597. Al terminar retiré el worktree y la rama, y `git status` quedó limpio |

### Mutaciones del reviewer, por familias

Apliqué cada mutación **sola**. Después corrí la suite entera del front y la
de Node, y anoté todos los tests que caen. En las de CSS recalculé la `?v=`
de las cuatro páginas con `version_de_las_hojas()`. Sin ese recálculo, T21 y
R72 matan cualquier cambio de hoja por accidente, que es lo que me pasó en la
primera pasada.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **S · Estados** | S1 | el error de la plantilla en `rs-aviso--atencion` | muerta | `t30_los_errores_y_las_marcas…` |
| | S3 | las marcas en `rs-chip`, sin modificador | muerta | `t30_…` |
| | S5 | `:class` reordenado: `completa` → ok **antes** de mirar `yaImportado` | muerta | Node T30 (el caso «ya importado (completa)») |
| | S2 | `class="rs-aviso rs-aviso--ok"` estático junto al `:class`; Alpine suma los dos, y `--ok` gana a `--info` por orden en la hoja | **sobrevive** | O10-4 |
| | S4 | la lista de errores con `rs-aviso--error rs-aviso--ok` | muerta **solo por el control** G3, que deja de encontrar su cadena; en sustancia, sobrevive | O10-4 |
| | S6 | `.rs-aviso--ok` con los colores de error (con la `?v=` recalculada) | **sobrevive** | O10-5 |
| **L · Lógica de F-036** | L1 | sin `@keydown.enter.prevent` en «Código de obra» | **sobrevive** | O10-3 |
| | L2 | «Importando…» sin `x-show` (siempre visible) | **sobrevive** | O10-3 |
| | L3 | `:key` de la bandeja a `fila.fila_origen` | **sobrevive** | O10-3 |
| | L4 | la tabla de la bandeja con `x-show="bandejaCargada"` | **sobrevive** | O10-3 |
| | L5 | `@change` pasa del `input` a su `label` | **sobrevive**: es equivalente, porque `change` burbujea | — |
| **N · Navegación** | N1 | la miga «Entrada» a `#/entrada` (sin `./`, que dejaría al usuario en la misma página) | muerta | `r71_…` |
| | N2 | «Inicio» de la barra a `index.html` | muerta | Node R70 (la guardia, no solo sus controles) |
| | N3 | «Oficios repetidos» de la subnavegación a `./#/entrada` | muerta | `r71_…`, `test_f036_s15_6_…` (sin tocar) |
| | N4 | el pie fuera del `<div x-data>` | muerta | `r72_…` |
| **P · `enlaceSeccion`** | P1 | `desde === "importar.html"` en vez de la clave de `PAGINAS` (se rompe `oficios.html`) | muerta | Node R44 (×2) |
| | P2 | `nuevaPestana: true` solo desde `oficios.html` | muerta | Node R44 (×2) |
| **A · Accesibilidad** | A1 | la subnavegación actual sin `aria-current` | muerta | `r71_…` |
| | A2 | «Entrada» de la barra sin `aria-current` | muerta | `r70_…` y Node R70 |
| | A3 | las migas sin `aria-label` | muerta | `r71_…` |
| **C · CSS** | C1 | sin la regla `.rs-subnav__item[aria-current="page"]` (con la `?v=` recalculada) | **sobrevive** | O10-5 |

Mueren **12 de 21**, contando S4 entre las vivas. Ninguna de las 9 vivas
corresponde a algo que esté hoy en la página.

Además repetí las dos de O17-3 sobre el código real. Las dos **mueren**:

- V-a, `importar.html` sin `?v=`: la matan `t21_…[importar.html]` y `r72_…`,
  con sus controles.
- V-b, `oficios.html` con la `?v=` vieja: la mata `t21_…[oficios.html]`.

### Respuestas a las preguntas del líder

**1 · El comportamiento está intacto.**

- `js/importacion.js`, `js/api.js` y los tests de F-036 no tienen diff: lo
  comprobé en la tabla de arriba. `test_f036_front.py` pasa entero y nadie lo
  ha tocado. Lo mismo `importacion.test.js` y `oficios.test.js`.
- **Recorrí `importar.html` directiva a directiva**, primero con el parser y
  luego leyendo el diff (`git diff -w`):
  - Todos los `@click`, `:disabled`, `x-model`, `x-show`, `x-text`, `x-for`
    y `:key` siguen en el **mismo elemento** (misma etiqueta) y con el mismo
    valor. También el `@keydown.enter.prevent`, el `@change` del fichero,
    `x-data`/`x-init`, el `<template x-if="resultado">`, el
    `id="bandeja"` y `type="file"`/`accept=".xlsx"`.
  - La única directiva que cambia es el `:class` del resultado. §16.5 la
    pide cambiada, y el caso `yaImportado` está explicado en la respuesta 2.
  - La estructura tampoco altera el ámbito de Alpine. El `<template x-if>`
    sigue teniendo un solo hijo raíz (`div.mt-5`): el `rs-desplazable`
    nuevo va dentro de ese hijo. El `input` de la obra sigue dentro de su
    `label`. El pie queda dentro del `<div x-data>`, como pide §16.15.5 (si
    se saca, N4 muere).
  - La «primera `<header>`» que lee `test_f036_front.py` sigue siendo la de
    la página, porque la barra es un `<nav>`. Conserva `index.html` (en las
    migas) y `oficios.html` (en la subnavegación).
  - Se va el enlace «Partes firmados → `index.html`» de la cabecera, como
    dice §16.5. Lo sustituye la pestaña de la barra, que lleva a
    `partes.html`.
  - El botón «Descargar el Excel de errores» pasa de rojo a secundario. Es
    lo que pide §16.5, y el aviso rojo de errores que tiene encima ya marca
    el estado.
- **`js/portal.js`, `enlaceSeccion(id, desde)`: encaja.**
  - La rama nueva solo entra con una clave **propia** de `PAGINAS`
    (`hasOwnProperty`, con `PAGINAS` congelado). Devuelve `null` para la
    sección de la página, `partes.html` para `partes` y `./#/<id>` para las
    demás, siempre con `nuevaPestana: false`. Es la tabla de §16.8 al pie de
    la letra.
  - R46 y R73 se cumplen: misma pestaña.
  - R17 enmendado no cambia, porque habla de los enlaces de `index.html`, y
    esta rama no los genera.
  - Las ramas `"portal"` y `"circuito"` no tienen diff, así que las barras de
    `index.html` y `partes.html` no cambian: sus R44 y R66 de Node pasan.
  - Esta rama la usa **solo el test**. `importar.html` no carga
    `portal.js` (R77), y su barra es HTML estático comparado contra la
    función (R70). P1 y P2 mueren.

**2 · Los estados se distinguen, y siempre con texto.**

| Estado | Clase | Texto en el mismo elemento |
|---|---|---|
| Completa | `rs-aviso rs-aviso--ok` | `x-text="resultado.estadoTexto"` («Importación completa…») |
| Parcial | `rs-aviso rs-aviso--atencion` | ídem («Importación parcial…») |
| Ya importado | `rs-aviso rs-aviso--info` | ídem («Este fichero ya se había importado: no se ha añadido nada…») |
| Error de plantilla, de importar y de bandeja | `rs-aviso rs-aviso--error` | su `x-text` |
| Lista de errores | `rs-aviso rs-aviso--error` | `h3` «Errores» y un `x-text` por línea |
| Marcas de la bandeja (duplicada, oficio ambiguo) | `rs-chip rs-chip--atencion` | `x-text="marca"`. Las dos marcas comparten color y las distingue su texto, como en R93 de F-036 |

Lo vigila T30 en sus dos mitades:

- Node **evalúa el `:class` de verdad** con lo que devuelve
  `presentarImportacion`, en cuatro casos: completa, parcial, ya importado
  completa y ya importado parcial.
- Python fija la clase y el texto de los errores y de las marcas.

Mis S1, S3 y S5 mueren.

**El «ya importado» en `rs-aviso--info`: es una desviación aceptable y
corrige una incoherencia de la spec.**

- El `:class` literal de §16.5 solo distingue `parcial` de lo demás.
- `textoDelEstado` (`js/importacion.js`, l. 133–144) ya da prioridad a
  `ya_importado` sobre `estado`.
- Con la letra de §16.5, la frase «no se ha añadido nada a la bandeja»
  saldría en el verde de éxito, o en ámbar si la importación original fue
  parcial. Color y texto se contradirían.
- `info` es lo que dice el texto. Además encaja con R74 (bloque 12), que
  rotula esos recuentos como «de la importación original».
- No toca ni una línea de JS: `yaImportado` ya lo devolvía
  `presentarImportacion`.
- Queda pendiente alinear la spec: O10-1.

**3 · El `input` de fichero con `hidden`: es cierto. Importa, pero es previo
a este bloque.**

- `class="hidden"` es `display: none` en Tailwind, y el `<label>` que lo
  envuelve no es enfocable. Con el tabulador se salta: no hay forma de abrir
  el selector de fichero sin ratón.
- En la base (`190b726`) ya estaba igual. Viene de F-036, no de este bloque.
- **Cuánto importa:**
  - Es la acción principal de la página.
  - Incumple WCAG 2.1.1 (teclado, nivel A).
  - En la práctica, Posventa trabaja con ratón, así que no bloquea a nadie
    hoy.
  - El remodelado no lo causa, pero sí lo hace más visible: ahora la
    etiqueta tiene aspecto de botón (`rs-btn rs-btn--secundario`), y quien
    use el teclado esperará poder llegar a ella.
- Lo anoto como hallazgo con destino: **O10-2**.

**4 · H-7 y O17-3: cerrados.**

- **H-7**: `problemasR66` trata como problema las cuatro formas ligadas
  (`FORMAS_LIGADAS_R66`, `tests_js/f035_paginas.test.js` l. 73 y 126).
  - Tiene cuatro controles: V5 y V6 en `index.html`, y las formas
    `x-bind:` en `importar.html`.
  - La mutación H1 del implementer (quitar la guardia) los hace caer.
  - Mi N2 también arrastra el control H-7 de `importar.html`.
- **O17-3**: T21 cubre ya `importar.html` y `oficios.html`
  (`PAGINAS_REALES_CON_VERSION`). V-a y V-b, que sobrevivían en el bloque
  17, ahora mueren: los repetí yo.

**5 · Navegador**: queda para V1/V2 del humano.

- La lista de qué mirar está en el §6 del informe y en `current.md`.
- O10-5 añade dos puntos: el aviso «completa» en verde y la píldora actual
  de la subnavegación en burdeos.

**Los apuntes del §5 del informe: están bien.**

- §5.2: `rs-desplazable` se ha **movido** a `styles.css`, no duplicado.
  `portal.css` se carga después, así que el portal no cambia.
- §5.3: `rs-aviso__titulo` solo pone el peso de letra, y el color sigue
  siendo el del aviso.
- §5.4: el separador de las migas lleva `aria-hidden`, que mejora el
  esqueleto de §16.5.
- §5.5: `w-40` pasa a la etiqueta para no mezclar una utilidad con
  `rs-campo` en la misma propiedad.
- §5.7: en `oficios.html` solo cambia la `?v=`.
- **B11 es equivalente.** Un elemento entre la barra y la cabecera no
  incumple R70, que pide que la barra vaya primera, no que la cabecera vaya
  pegada a ella.
- Es **un acierto** haber detectado y cerrado G1–G5 dentro del mismo bloque.
  La lista cerrada de R72 solo prohíbe Tailwind, no exige el `rs-*`
  correcto, y T30 tapa justo ese hueco.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo). [x] Existen los
  ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba, como en los bloques anteriores. [x] Ninguna feature pasa a
  `done`.
- **C3**
  - [x] La primera línea con la ruta está en los ficheros tocados
    (`importar.html`, `styles.css`, `portal.js` y los dos de tests).
  - [x] Sin depuración, TODO ni secretos, y sin dependencias nuevas: las
    fuentes y el favicon son las `<link>` de §15.4, que ya usan las otras
    páginas.
  - [x] Comentarios en español.
  - [x] Ningún PDF ni parte en git: `--diff-filter=A` vacío.
  - Arquitectura hexagonal, unidad «parte», Sigrid, firma, «firmado no es
    conforme», duplicados y `conest`: **N/A justificado**. El diff es front
    de presentación (HTML, CSS y una rama de `portal.js`) y tests, y no toca
    la API ni el circuito.
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4** [x] Cada requisito tiene tests trazables, y todos pasan:

  | Requisito | Tests |
  |---|---|
  | R70 | `test_f035_r70_la_pagina_real_lleva_la_barra_comun_primera_y_estatica[importar.html]` y sus controles; Node «f035 R70: la barra de importar.html…» (7 controles) |
  | R44 (enmienda) | Node «f035 R44: enlaceSeccion desde una página de PAGINAS…», «…desde importar.html y oficios.html: Entrada es la actual» y «desde desconocido…» |
  | R66 en la barra de `importar.html` y H-7 | Node «f035 R66 … importar.html» y «f035 R66 (H-7): control…» (×4) |
  | R71 | `test_f035_r71_la_cabecera_lleva_migas_y_subnavegacion[importar.html]` y sus controles |
  | R72 | `test_f035_r72_la_pagina_real_lleva_la_identidad_ruesma[importar.html]` y sus controles, incluido el de la `?v=` |
  | R73 | `test_f035_r73_…[importar.html]` (desde el bloque 16) y Node R70 |
  | R77 | `test_f035_r77_…` y sus controles |
  | R50, R51, R54 y R60 extendidos | `r70_…` y `r54_r60_…` |
  | `?v=` (T21, O17-3) | `test_f035_t21_la_pagina_real_…[importar.html / oficios.html]` y sus controles |
  | Semántica de estados (T30) | `test_f035_t30_*` y Node «f035 T30…» (4 controles cada uno) |

  [x] Sin red ni BBDD. [x] El MANUAL (vistazo en navegador) consta en
  `current.md`, enviado a V1/V2.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae las salidas reales: Node, 14 fail de
    35; Python, 26 failed y 16 passed. Explica los 16 que ya pasaban (no
    regresión) y el `NameError` de la primera pasada.
  - [x] **Cobertura**: N/A con el motivo impreso por `init.sh`.
  - [x] **Mutación**: informe de la herramienta con 0 mutantes, recalculado,
    reejecutado y con el control del cero hecho.
  - [x] **Mutantes a mano**: 52/53 del implementer (B11 equivalente) y
    12/21 mías, con las 9 vivas analizadas abajo. En rigor `estandar` basta
    con documentarlas.
  - [x] «Evidencias» con los cuatro números.
  - [x] Ningún N/A sin justificar. La regla 7 es N/A porque es de
    `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T29 y T30 están `[x]`, con commits `F-035 T29: …` y
  `F-035 T30: …`. [x] No hay ficheros sin trackear. El worktree
  `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
  bloque. [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **O10-1 · §16.5 da un `:class` del resultado que contradice el texto del
  «ya importado».**
  - La implementación lo corrige con `rs-aviso--info` delante, y lo vigila
    Node T30.
  - **Destino: spec-author, bloque 14.** Es una línea en §16.5: «el
    resultado, `rs-aviso` con `--info` si `yaImportado`, `--atencion` si
    `parcial` y `--ok` en otro caso».
- **O10-2 · El selector de fichero no se alcanza con el teclado (previo, de
  F-036).**
  - `<input type="file" class="hidden">` dentro de una `<label>` que no es
    enfocable.
  - El arreglo es solo de presentación:
    - Cambiar `hidden` por una clase de ocultación accesible (`sr-only`,
      que ya trae Tailwind).
    - Pintar el foco en la etiqueta con
      `.rs-btn:focus-within { outline: … }` en `styles.css`.
  - Es compatible con `test_f036_front.py`, que solo fija `type` y
    `accept` (l. 360).
  - Su test sería: el `input` de fichero no lleva `hidden` ni
    `display: none`, y la etiqueta que lo envuelve tiene una regla de foco.
  - **Destino: el líder, para el humano.** Puede ser una tarea pequeña
    dentro de F-035 (la página ya se ha remodelado aquí, así que cabe en el
    bloque 14) o una ficha aparte. No se carga a este bloque.
- **O10-3 · Los tests de F-036 no fijan cuatro directivas de
  `importar.html`** (L1–L4: `@keydown.enter.prevent`, `x-show="importando"`,
  `:key` de la bandeja y `x-show="bandeja.length"`).
  - El hueco es previo a este bloque, y aquí no se ha cambiado ninguna:
    el parser lo confirma.
  - Pero R72 fía «remodelar es presentación» a que «los tests de
    comportamiento de F-036 siguen en verde», y esos tests no ven todas las
    directivas.
  - **Destino: bloque 11** (`oficios.html`, el siguiente remodelado).
    Su reviewer debe repetir la comparación de atributos funcionales con el
    parser (ver la automejora). Opcionalmente, si el líder la quiere, se
    puede añadir una guardia de «huella de directivas» por página. Yo no la
    exijo, porque congelaría las páginas ante cambios de lógica legítimos
    (R74, R75).
- **O10-4 · Un modificador de estado de más pasa la guardia T30** (S2 y S4:
  un `rs-aviso--ok` estático junto al `:class`, o dos modificadores en la
  lista de errores).
  - Nadie lo escribe a propósito, y la familia G está cubierta.
  - **Destino: opcional, en el bloque 11** si se vuelve a tocar
    `test_f035_paginas.py`. La propuesta es que `problemas_de_estados` y
    `avisoDelResultado` exijan **exactamente un** `rs-aviso--*` o
    `rs-chip--*` en el `class` estático (y ninguno en el del resultado, que
    lo pone el `:class`).
- **O10-5 · El color solo lo ve el ojo** (S6, C1; es la familia O9-5).
  - Que `.rs-aviso--ok` sea verde y que la píldora actual de la
    subnavegación se distinga de la otra no lo fija ningún test. Fijar
    colores sería sobreespecificar.
  - **Destino: V1/V2 del humano.** Hay que mirar el resultado en verde,
    ámbar y azul, los errores en rojo y «Importar incidencias» en burdeos
    junto a «Oficios repetidos» en gris.
- Siguen abiertos, como estaban:
  - **O16-4**, que es opcional.
  - **H16-3 a H16-6**, **O17-2**, **O9-2 a O9-4** y **O9-7**: van al
    spec-author, en el bloque 14.
  - **O9-1**, **O9-5** y **O9-6**: van a V1.

### Automejora (propuesta, no aplicada)

**`reviewer.md`: una regla para los bloques de «remodelado de
presentación», válida para cualquier proyecto. Va también a `arnes-base`.**

Cuando un encargo declare que un cambio es «solo presentación» sobre una
página con lógica (Alpine, Vue, plantillas), el reviewer compara con un
parser el **multiconjunto de atributos funcionales** (directivas, `id`,
`name`, `for`, `type`, `accept`, `href`, cada uno con su etiqueta) entre la
base y HEAD. Después lee entera la lista de diferencias.

El motivo es este bloque. Los tests de comportamiento de la página no
fijaban cuatro directivas (L1–L4 sobreviven), así que «los tests de F-036
siguen en verde» no demostraba que la lógica estuviera intacta. El
multiconjunto sí lo demuestra, cuesta un guion de veinte líneas y da una
lista corta y legible.

## Review del bloque 11 · T31–T32 y O10-2 · 2026-10-05

> reviewer. Alcance **acotado** a `git diff f3a5bcb..HEAD`: `0112d91` (T31),
> `a7d6292` (O10-2) y `05d12b7` (T32), en `feature/F-035-portal-posventa`.
> Es `oficios.html` remodelado al estilo del portal (R70–R73, R77), solo
> presentación, y el arreglo de accesibilidad O10-2 de la review del bloque
> 10 (el selector de fichero de `importar.html` alcanzable con teclado), que
> el líder añadió al encargo.
>
> Los bloques 12–15 siguen abiertos **a propósito** y no cuentan como `[ ]`.
> El vistazo en navegador, incluido tabular hasta «Elegir el Excel», queda
> para V1/V2 del humano.
>
> Criterio de severidad del líder: bloqueante es un riesgo real para el
> usuario o un incumplimiento de la spec. Una mutación que solo se distingue
> con un marcado que nadie escribiría, o una variante de una familia ya
> cubierta, va como informativo con su destino.

### Veredicto

**APPROVED** (del bloque 11, no de la feature).

- **La lógica de F-036 no ha cambiado.** `js/`, la API y los tres ficheros
  de tests de F-036 no tienen diff. Con un parser **propio** (no el del
  implementer), las directivas, `id`, `type`, `accept` y `autocomplete` de
  `oficios.html` son idénticas, en orden y ámbito, entre `f3a5bcb`,
  `2a86bca` y HEAD. Lo único que el parser ve de más es el `src` del logo de
  la barra y el `type` del favicon, que son presentación. En `importar.html`,
  entre `f3a5bcb` y HEAD, la huella es idéntica: O10-2 solo cambia el
  `class` del `input`.
- **Los estados se distinguen por la semántica de la marca y llevan texto.**
  «Son el mismo» va en verde relleno y «Son distintos» y «Separar», en blanco
  con borde. El burdeos no marca ningún estado.
- **O10-2 está bien resuelto.** `sr-only` deja el control en el orden del
  tabulador. `label.rs-btn:focus-within` es mejor que el
  `.rs-btn:focus-within` que propuse yo.
- **O10-3 y O10-4 están bien resueltos.** La huella de `importar.html` cabe
  en el bloque 12 (lo explico en la respuesta 4).
- Hice 25 mutaciones en 5 familias y sobreviven 8. Ninguna corresponde a
  algo que esté hoy en la página. Van como informativo, con su destino. La
  más seria es K1: un `tabindex="-1"` deshace O10-2 y la guardia no lo ve
  (O11-1).

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes (el control del
cero está más abajo). Lo compensan las mutaciones a mano: 58 del implementer
y 25 mías.

La regla 7 de `reviewer.md` (orden) es **N/A**. Solo aplica en rigor
`critico`, y además aquí no hay un orden entre colaboradores que proteger.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, en el árbol real. Lo relancé porque el implementer lo corrió **antes** de su último cambio (el `UP034` del test) | **exit 0**, `ENTORNO LISTO`. Raíz: 114 passed. Front: **673 passed** (25,22 s, ejecutado, no desde caché). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. ruff: 71 avisos, todos de deuda previa |
| `node --test "tests_js/*.test.js"` (línea base del worktree) | **607/607** |
| `git diff --stat f3a5bcb..HEAD` sobre `services/postventa-api`, `services/postventa-front/js`, `tests/test_f036_front.py`, `tests_js/importacion.test.js` y `tests_js/oficios.test.js` | **vacío** |
| Huella funcional de `oficios.html` y de `importar.html` con mi guion (`html.parser`). Mira `x-*`, `@*`, `:*`, `id`, `name`, `for`, `type`, `accept`, `value`, `disabled`, `required`, `autocomplete` y `src`, y para cada uno su etiqueta, su ámbito de Alpine y el texto si es un botón | **`oficios.html`**: base 42 entradas y HEAD 44. Las dos de más son el `<img src="img/logo-ruesma.svg">` de la barra y el `<link rel="icon" type="image/svg+xml">`. El resto es igual frente a `f3a5bcb` y frente a `2a86bca`. **`importar.html`**: 53 y 53, idénticas y en el mismo orden |
| `git diff -w`, leído línea a línea en las que llevan directivas | Solo cambia el valor de `class`. Ninguna línea con `@click`, `:disabled`, `:key` o `x-for` aparece en el diff |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `lineas={}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el informe declara un «Tiempo total» de 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre las 439 líneas del diff de `test_f035_paginas.py`, ignorando la exclusión | **63** mutantes. El generador funciona y el cero es **legítimo** |
| `git log --diff-filter=A f3a5bcb..HEAD` | no se añade ningún fichero |
| `console.*`, `debugger`, `print(`, `TODO` en las líneas añadidas | ninguno |
| Arrastrar y soltar en `importar.html` / `oficios.html` (`drop`, `drag`) | No hay ninguno. `sr-only` no tiene nada que romper ahí |
| Mutaciones a mano | Las hice en un worktree desechable del scratchpad, sobre `05d12b7`, con una rama temporal `feature/F-035-rev-b11` para que las guardias de rama no se salten. Línea base: 673 passed; Node, 607/607. Al terminar retiré el worktree y la rama, y `git status` quedó limpio |

### Mutaciones del reviewer, por familias

Apliqué cada mutación **sola**, conservando los CRLF. Después corrí la suite
entera del front y la de Node, y anoté todos los tests que caen. En las de
CSS recalculé la `?v=` de las cuatro páginas, como en el bloque 10. Evité
repetir las 58 del implementer: estas buscan lo que su tabla no prueba.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **F · Lógica de oficios** | F1 | «Separar» con los códigos al revés: `decidir([par.codigo_b, par.codigo_a], 'distinto')` | muerta | `o10_3_…huella…` |
| | F2 | «Son distintos» sin `:disabled` | muerta | `o10_3_…` y `test_f036_r89_los_botones…[Son distintos]` |
| | F3 | el error de carga con `x-text="errorDecision"` | muerta | `t31_los_estados…` y `o10_3_…` |
| | F4 | sin `x-init="iniciar()"` | muerta | `o10_3_…` y dos de F-036 (t22 y r89) |
| | F5 | `:key` de los avisos a `aviso.texto` | muerta | `o10_3_…` (antes de O10-3 habría sobrevivido, como L3) |
| **E · Estados** | E1 | «Son distintos» en `--ok`: se pinta igual que «Son el mismo» | muerta | `t31_los_estados…` |
| | E2 | «Son el mismo» par a par en `--primario`: el burdeos como estado | muerta | `t31_…` |
| | E3 | `errorDecision` en `rs-aviso--atencion` | muerta | `t31_…` |
| | E6 | «Descargar los grupos vigentes» en primario: dos acciones principales | muerta | `t31_…` |
| | E7 | el rótulo «Avisos» pasa a decir «Atención» | muerta | `t31_…` |
| | E4 | la lista de avisos sin `rs-texto--atencion`: el texto en gris dentro del panel ámbar | **sobrevive** | O11-3 |
| | E8 | los miembros de un aviso sin `rs-nota--atencion` | **sobrevive** | O11-3 |
| | E5 | cada propuesta en `rs-panel--atencion` en vez de `--suave` | **sobrevive** | O11-2 |
| | E9 | el nombre de un grupo con `rs-panel--atencion` | **sobrevive** | O11-2 |
| **K · O10-2** | K2 | la regla de foco con `outline: 2px solid transparent` | muerta | `o10_2_…[foco-sin-contorno]`, pero **solo el control**: ver la nota |
| | K4 | el `input` con `style="visibility: hidden"` | muerta | `r54_r60_…[importar.html]` (prohíbe `style`) |
| | K6 | la regla en `label.rs-btn:focus-within:hover` | muerta | `o10_2_…[importar.html]` |
| | K1 | el `input` con `tabindex="-1"`: **el tabulador se lo vuelve a saltar** | **sobrevive** | O11-1 |
| | K5 | el `input` con `aria-hidden="true"`: enfocable pero mudo para el lector | **sobrevive** | O11-1 |
| | K3 | el `input` con `disabled` | **sobrevive** | O11-1 |
| **N · Navegación de oficios** | N1 | «Partes firmados» de la barra a `index.html` | muerta | Node R70 (y `test_f007_r32`, que corre Node) |
| | N2 | «Importar incidencias» de la subnavegación a `importar.html#bandeja` | muerta | `r71_…[oficios.html]` y `test_f036_s15_6_…` |
| | N3 | la miga «Portal de posventa» a `./#/inicio` | muerta | `r71_…` |
| | N4 | la píldora actual con `aria-current="true"` en vez de `"page"` | muerta | `r71_…` |
| **C · CSS nuevo** | C1 | `.rs-texto--atencion` movida **antes** de `.rs-texto`: pierde la cascada (con la `?v=` recalculada) | **sobrevive** | O11-3 |

Mueren **17 de 25**. Ninguna de las 8 vivas corresponde a algo que esté
hoy en la página.

**Nota sobre K2.** Muere, pero solo porque el control `foco-sin-contorno`
deja de encontrar su cadena, igual que S4 en el bloque 10. La guardia
`problemas_o10_2` acepta un contorno `transparent`, porque solo rechaza
`none` y `0`. En sustancia es de la familia O11-1.

### Respuestas a las preguntas del líder

**1 · El comportamiento está intacto.**

- `js/`, la API y los tests de F-036 no tienen diff (tabla de arriba).
  `test_f036_front.py` pasa entero y nadie lo ha tocado. Lo mismo
  `importacion.test.js` y `oficios.test.js`.
- **Recorrí `oficios.html` directiva a directiva**, primero con mi parser y
  luego leyendo el `git diff -w`:
  - `x-data="appOficios()"` y `x-init="iniciar()"` siguen en el mismo `div`
    raíz. Como en `importar.html`, la barra, la cabecera y el pie quedan
    dentro de él.
  - El campo «Código de obra» conserva `type="text"`, `x-model="obra"`,
    `autocomplete="off"` y `@keydown.enter.prevent="cargar()"`, y sigue
    dentro de su `label`. Solo cambia el `class`: el `w-40` pasa a la
    etiqueta, como en T29.
  - `x-show="cargando"`, `motivoSinDecidir()` (`x-show` y `x-text`),
    `errorCarga`, `errorDecision`, `vista && vista.sinNada`,
    `<template x-if="vista">`, los tres `x-for` con sus `:key`, los `x-show`
    de cada sección y los `x-text` de miembros, motivos, pares, grupos y
    avisos son idénticos y siguen en el mismo ámbito.
  - **Los cuatro botones llaman a lo mismo, con los mismos argumentos:**

    | Botón | `@click` | `:disabled` |
    |---|---|---|
    | «Descargar los grupos vigentes» | `descargarGrupos()` | `!vista` |
    | «Son el mismo» (grupo entero) | `decidir(propuesta.codigos, 'mismo')`, dentro de `x-show="propuesta.confirmarEntero"` | `!puedeDecidir()` |
    | «Son el mismo» (par a par) | `decidir([par.codigo_a, par.codigo_b], 'mismo')`, con `x-show="!propuesta.confirmarEntero"` | `!puedeDecidir()` |
    | «Son distintos» | `decidir([par.codigo_a, par.codigo_b], 'distinto')` | `!puedeDecidir()` |
    | «Separar» | `decidir([par.codigo_a, par.codigo_b], 'distinto')`, dentro de `x-for="par in grupo.pares"` | `!puedeDecidir()` |

    También «Ver los oficios» sigue con `cargar()` y `!obra.trim() ||
    cargando`. Los textos de los botones no cambian.
  - Los cinco scripts siguen al final y en su orden: el diff no los toca.
  - La «primera `<header>`» que lee `test_f036_front.py` sigue siendo la de
    la página, porque la barra es un `<nav>`. Enlaza a `index.html` (en las
    migas) y a `importar.html` (en la subnavegación). Se va el `<nav>` viejo
    «Partes firmados → `index.html`», como dice §16.5.
  - Ni «proveedor» ni «actividad» aparecen en ningún texto nuevo:
    `test_f036_quinta_enmienda_…` pasa.
- Ahora **la huella O10-3 lo vigila de forma permanente**. Mis F1–F5
  mueren, y F5 habría sobrevivido sin ella.

**2 · Los estados se distinguen, y siempre con texto.**

| Estado / acción | Clase | Texto |
|---|---|---|
| Propuesta pendiente | `rs-panel rs-panel--suave` (recuadro neutro, sobre el lienzo) dentro de un `rs-panel` con el `h2` «Propuestas pendientes» | los miembros y «Por qué se proponen: …» |
| Grupo vigente | el mismo recuadro neutro, con el nombre en `rs-texto--fuerte`, bajo el `h2` «Grupos vigentes» | la etiqueta del grupo y sus pares |
| Avisos (grupos no aplicados) | `rs-panel rs-panel--atencion`, con el rótulo `rs-rotulo--atencion` «Avisos» | `aviso.texto` y sus miembros, en el tono del panel |
| Errores (carga y decisión) | `rs-aviso rs-aviso--error` | su `x-text` |
| Leyendo, sin nada que revisar, motivo para no decidir | `rs-nota` y `rs-texto` | su texto |

- **Las acciones están bien diferenciadas.** «Son el mismo» va en `--ok`
  compacto: verde relleno con texto blanco. «Son distintos» y «Separar» van
  en secundario compacto: blanco con borde acero y texto en tinta. Se
  distinguen por el relleno, no solo por el tono, y además por su texto.
- **El burdeos no marca ningún estado.** Solo aparece:
  - en la acción principal («Ver los oficios», primario);
  - en el filete del bloque de búsqueda (`rs-panel--destacado`, marca);
  - en el foco;
  - en el *hover* de los secundarios, que es interacción y no estado.

  Mi E2 («Son el mismo» en primario) muere.
- `t31_los_estados…` fija todo esto, con nueve controles. Mis E1, E2, E3,
  E6 y E7 mueren.
- Lo que sobrevive es solo de color, o un marcado que nadie escribiría (E4,
  E5, E8, E9 y C1): O11-2 y O11-3.

**3 · O10-2: está bien resuelto.**

- **Alcanzable con teclado: sí.** `sr-only` es `position: absolute`, 1 px,
  `clip`, sin `display: none` ni `visibility`, así que el `input` sigue en
  el orden del tabulador. En Chrome y Firefox, Espacio o Intro sobre un
  `input type=file` enfocado abren el selector. Su nombre accesible es
  «Elegir el Excel», porque la etiqueta lo envuelve.
- **El posicionamiento no da saltos.** El ancestro posicionado más cercano
  es `rs-panel--destacado` (`position: relative`). El píxel queda dentro
  del panel y, al enfocarlo, la página no salta.
- **La etiqueta enseña el foco: sí.** `label.rs-btn:focus-within` pone
  `outline: 2px solid var(--rs-burdeos)` y `outline-offset: 2px`. Es el
  mismo foco que el `:focus-visible` global (R54).
- **El ratón no se rompe.** Al pulsar la `<label>` se activa el control que
  envuelve, igual con `sr-only` que con `hidden`. No hay zona de arrastre en
  ninguna de las dos páginas, así que no hay nada que romper.
- **Si falla Tailwind,** `sr-only` desaparece y el control nativo se ve:
  degrada a funcional. Con `hidden` pasaba lo mismo.
- **`label.rs-btn:focus-within` frente a `.rs-btn:focus-within`: está bien
  así, mejor que mi propuesta.** `:focus-within` también se cumple cuando
  el propio elemento tiene el foco. En un `<button class="rs-btn">`, que
  recibe el foco al pulsarlo con el ratón en Chrome y Firefox, pintaría el
  contorno en cada clic y anularía la decisión de usar `:focus-visible`.
  Restringido a `label`, solo salta cuando el foco lo tiene el control que
  envuelve.
  - El precio, que el implementer declara: tras elegir un fichero con el
    ratón, el contorno se queda mientras el foco siga en el `input`. Es
    aceptable, porque es donde está el foco.
  - Si en V1 molesta, la alternativa es `label.rs-btn:has(:focus-visible)`.
    Solo salta con teclado, y `:has` está en todos los navegadores
    actuales. Va como opcional en O11-4.
- **La guardia tiene un hueco: O11-1.** `problemas_o10_2` no ve
  `tabindex="-1"` (K1), que deshace exactamente lo que O10-2 arregla. Es un
  marcado plausible, porque muchos fragmentos de «subida de fichero a
  medida» lo traen. Tampoco ve `aria-hidden` (K5), `disabled` (K3) ni un
  contorno `transparent` (K2). Hoy no hay ninguno, así que no bloquea. El
  arreglo es pequeño.

**4 · O10-3 y O10-4: bien resueltos.**

- **O10-3.**
  - `HUELLA_DE_OFICIOS` coincide con lo que da mi parser independiente
    sobre `2a86bca`.
  - La función mira la etiqueta, los atributos funcionales, el texto del
    botón, el ámbito y el orden.
  - Los controles prueban que muerde: L1–L3 trasladadas, «Separar» que
    junta y el ámbito y el orden, este último con el fallo G5 que el propio
    implementer detectó y corrigió.
  - Que excluya `class` y `href` es correcto: son presentación y
    navegación, y ya las vigilan R70–R73.
  - El riesgo que yo señalé, congelar la página, queda acotado: el
    comentario dice que R75 (bloque 13) la amplía en el mismo commit.
- **La huella de `importar.html` sí hace falta**, por L1–L4 de la review
  del bloque 10. Mi parser confirma que hoy la página está intacta, pero
  ningún test lo fija. **Dónde encaja: en T33 (bloque 12)**, que es el que
  toca `importar.html` para el rótulo de R74. El orden propuesto:
  1. Antes del cambio de R74, fijar `HUELLA_DE_IMPORTAR` con
     `huella_funcional` sobre HEAD (no sobre `2a86bca`). Desde F-036 ya
     cambiaron, por la spec, el `:class` del resultado y el `id="bandeja"`.
     La huella de HEAD no lleva `class`, pero sí `:class`.
  2. Comprobar que pasa.
  3. Hacer R74 y ampliar la huella con sus entradas nuevas en el mismo
     commit, para que el diff de la constante enseñe solo lo añadido.

  Cuesta poco, porque la función ya existe y es parametrizable con
  `esperada`. Si el líder prefiere no cargar T33, el sitio alternativo es
  el bloque 14. Va como **O11-5**.
- **O10-4.**
  - `_VARIANTE` cuenta `rs-aviso--*`, `rs-chip--*`, `rs-btn--*` (salvo
    `--compacto`) y `rs-panel--atencion`.
  - `problemas_de_estados` y los botones de oficios exigen exactamente las
    variantes que tocan.
  - Node T30 rechaza una variante fija junto al `:class`.
  - Los controles S2, S4 y «separar con dos variantes» lo prueban, y las
    mutaciones G1, G2, G6 y G9 del implementer muestran que no pasan en
    vacío.
  - El límite es que solo mira los elementos **listados**. Una variante en
    un elemento que no está en la lista (E5, E9) pasa: O11-2.

**5 · Navegador**: queda para V1/V2 del humano.

- La lista de qué mirar está en el §6 del informe y en `current.md`. Incluye
  tabular hasta «Elegir el Excel» y abrir el selector con Espacio.
- O11-3 añade un punto: el texto de los avisos en ámbar, no en gris.

**Los apuntes del §5 del informe: están bien.**

- §5.2: que la huella no mire `class` ni `href` es correcto.
- §5.3: hacer O10-4 aquí es un acierto.
- §5.4: las dos clases nuevas están justificadas, son de tokens y respetan
  el orden de cascada (`.rs-texto--atencion` va tras `.rs-texto`, y C1
  demuestra que importa).
- §5.5: `rs-panel--destacado` en la búsqueda, coherente con T29.
- §5.6: la respuesta 3.
- §5.7: `oficios.html` no tiene ningún control oculto. Lo confirmo, y la
  guardia lo fija con `(1, 0)`.
- §5.8: los controles comprueban primero que el detector da vacío sobre la
  página real. Es buena práctica.
- **El `UP034` corregido después de `init.sh`** lo cubre mi ejecución de
  `init.sh` sobre HEAD: verde y ruff 71.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo, sobre HEAD).
  [x] Existen los ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba, como en los bloques anteriores. [x] Ninguna feature pasa a
  `done`.
- **C3**
  - [x] La primera línea con la ruta está en los cinco ficheros de código
    tocados (`oficios.html`, `importar.html`, `styles.css` y los dos de
    tests). `index.html` y `partes.html` solo cambian la `?v=`.
  - [x] Sin depuración, TODO ni secretos, y sin dependencias nuevas:
    - las fuentes y el favicon son las `<link>` de §15.4, que ya usan las
      otras páginas;
    - `sr-only` es de Tailwind, que la página ya cargaba.
  - [x] Comentarios en español.
  - [x] Ningún PDF ni parte en git: `--diff-filter=A` vacío.
  - Arquitectura hexagonal, unidad «parte», Sigrid, firma, «firmado no es
    conforme», duplicados y `conest`: **N/A justificado**. El diff es front
    de presentación (HTML y CSS) y tests, y no toca la API ni el circuito.
    Las decisiones de oficios siguen llamando a lo mismo (respuesta 1).
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4** [x] Cada requisito tiene tests trazables, y todos pasan:

  | Requisito | Tests |
  |---|---|
  | R70 | `test_f035_r70_…[oficios.html]` y los controles `t31_…[r70-*]`; Node «f035 R70: la barra de oficios.html…» y sus 7 controles sobre las dos páginas |
  | R44 / R66 en la barra de `oficios.html` | Node «f035 R44: enlaceSeccion desde importar.html y oficios.html: Entrada es la actual» y «f035 R66: en la barra de oficios.html…» |
  | R71 | `test_f035_r71_…[oficios.html]` y los controles `t31_…[r71-*]` |
  | R72 | `test_f035_r72_…[oficios.html]` y sus controles (22b permanente, pie, body) |
  | R73 | `test_f035_r73_…[oficios.html]` y Node R70 |
  | R77 | `test_f035_r77_…[oficios.html]` y el control `t31_…[r77-portal-js]` |
  | R54 / R60 | `test_f035_r54_r60_…[oficios.html]` y el control `t31_…[r54-sin-foco]` |
  | Semántica de estados de oficios (§16.5, T31) | `test_f035_t31_los_estados_y_los_botones…` y 9 controles |
  | O10-3 (lógica intacta) | `test_f035_o10_3_oficios_conserva_la_huella…`, 6 controles y el de ámbito y orden |
  | O10-4 | los controles `dos-variantes-S4`, `marca-con-dos-variantes`, `separar-con-dos-variantes` y Node T30 S2 |
  | O10-2 | `test_f035_o10_2_el_selector…[importar.html, oficios.html]`, `…importar_tiene_un_selector…` y 8 controles |
  | Quinta enmienda de F-036 | `test_f036_quinta_enmienda_…` (sin tocar) |

  [x] Sin red ni BBDD. [x] El MANUAL (vistazo en navegador y tabulador)
  consta en `current.md`, enviado a V1/V2.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae las salidas reales de T31 (Node, 10
    fail de 50; Python, 21 failed y 213 passed) y de O10-2 (8 failed). Los
    que ya pasaban están explicados: son guardias de no regresión, como la
    huella, que por definición tiene que pasar antes y después.
  - [x] **Cobertura**: N/A con el motivo impreso por `init.sh`.
  - [x] **Mutación**: informe de la herramienta con 0 mutantes, recalculado,
    reejecutado y con el control del cero hecho (63).
  - [x] **Mutantes a mano**: 58/58 del implementer y 17/25 mías, con las 8
    vivas analizadas abajo. En rigor `estandar` basta con documentarlas.
  - [x] «Evidencias» con los cuatro números, más los workers de la campaña.
  - [x] Ningún N/A sin justificar. La regla 7 es N/A porque es de
    `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] T31 y T32 están `[x]`, con sus commits `F-035 T31: …` y
    `F-035 T32: …`.
  - [x] O10-2 lleva su propio commit `F-035 O10-2: …`. Es una tarea añadida
    por el líder y no está en `tasks.md`, así que no le toca número `Tn`.
  - [x] No hay ficheros sin trackear. El worktree
    `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
    bloque.
  - [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **O11-1 · La guardia de O10-2 no ve otras formas de sacar el control del
  teclado** (K1 `tabindex="-1"`, K5 `aria-hidden="true"`, K3 `disabled`, y
  K2 en sustancia: contorno `transparent`).
  - K1 es la que importa: deshace exactamente O10-2, y es un marcado que se
    escribe de verdad. Hoy no está, así que no bloquea.
  - **Propuesta** para `problemas_o10_2`:
    - rechazar un `tabindex` negativo, `aria-hidden="true"` y `disabled`
      en el `input`;
    - aceptar como contorno solo uno con `solid` y color distinto de
      `transparent`, o directamente `var(--rs-burdeos)`, como el
      `:focus-visible` global.
    - Cada caso con su control.
  - **Destino: bloque 12 (T33)**, que vuelve a tocar `importar.html` y
    `test_f035_paginas.py`. Si no, bloque 14.
- **O11-2 · Una variante de estado en un elemento no listado pasa la
  guardia** (E5, propuestas en `rs-panel--atencion`; E9, el nombre de un
  grupo con `rs-panel--atencion`).
  - Es de la familia O10-4, con un marcado que nadie escribiría, y el texto
    sigue diciendo qué es cada cosa.
  - **Destino: opcional.** Si el líder la quiere, se puede exigir que
    `rs-panel--atencion` solo aparezca en el bloque de avisos (en
    `oficios.html`) y en ningún otro elemento. No la exijo.
- **O11-3 · El tono del texto de los avisos solo lo ve el ojo** (E4 y E8,
  sin las clases de tono; C1, la regla antes de `.rs-texto`, que pierde la
  cascada). Es la familia O10-5 / O9-5: fijar colores sería
  sobreespecificar.
  - **Destino: V1/V2 del humano.** El texto de los avisos tiene que verse
    en ámbar, no en gris, dentro del panel ámbar.
- **O11-4 · Opcional: `label.rs-btn:has(:focus-visible)`** en vez de
  `:focus-within`, si en V1 molesta que el contorno se quede tras elegir el
  fichero con el ratón.
  - Cambia una línea de `styles.css` y el regex de la guardia.
  - **Destino: V1/V2**, y solo si el humano lo ve.
- **O11-5 · La huella funcional de `importar.html`** (L1–L4 del bloque 10
  siguen sin fijar).
  - **Destino: bloque 12, en T33.** Fijarla sobre HEAD **antes** del cambio
    de R74 y ampliarla con sus entradas en el mismo commit (respuesta 4).
    Si no, bloque 14.
  - Lo decide el líder, como pide §5.1 del informe.
- Siguen abiertos, como estaban:
  - **O10-1**, **H16-3 a H16-6**, **O17-2**, **O9-2 a O9-4** y **O9-7**: van
    al spec-author, en el bloque 14.
  - **O10-5**, **O9-1**, **O9-5** y **O9-6**: van a V1/V2.
  - **O16-4**, que es opcional.

### Automejora (propuesta, no aplicada)

**`reviewer.md`: en la regla de «remodelado de presentación» que propuse en
el bloque 10, pedir que el parser del reviewer sea propio.**

Cuando el implementer ya trae una guardia de huella, como aquí
`huella_funcional`, el reviewer compara con **su propio** parser y no
reutiliza la función del implementer. Si las dos compartieran un punto
ciego, por ejemplo un atributo funcional que ninguna de las dos mira, el
error se confirmaría a sí mismo.

En este bloque coinciden en todo, pero la mía mira además `src`. Gracias a
eso vi que las únicas diferencias son el logo y el favicon, y no otra cosa
oculta.

Vale para cualquier proyecto. Va también a `arnes-base`.

## Review del bloque 12 · T33–T34, O11-1 y O11-5 · 2026-10-06

> reviewer. Alcance **acotado** a `git diff 9812d69..HEAD`: `bcdf46a`
> (O11-5), `09b5660` (O11-1), `fa14520` (T33) y `e5e4201` (T34), en
> `feature/F-035-portal-posventa`. Es el apunte (b) del humano (R74): en
> `importar.html`, con un fichero ya importado, los recuentos se rotulan
> «Resumen de la importación original del <fecha>». Lo resuelve
> `rotuloResumen(respuesta)` en `js/importacion.js`, tolerante a que falte
> `importado_at_utc`, que lo dará F-053 y hoy no existe.
>
> Los bloques 13–15 siguen abiertos **a propósito** y no cuentan como `[ ]`.
> El vistazo en navegador (importar el mismo fichero dos veces) queda para
> V1/V2 del humano.
>
> Criterio de severidad del líder: bloqueante es un riesgo real para el
> usuario o un incumplimiento de la spec. Una mutación que solo se distingue
> con datos que nadie mandaría, o una variante de una familia ya cubierta, va
> como informativo con su destino.

### Veredicto

**APPROVED** (del bloque 12, no de la feature).

- **El único cambio de lógica es el que la spec admite.** `js/importacion.js`
  gana 65 líneas y no pierde ninguna frente a `2a86bca`: `rotuloResumen`, su
  ayudante privado `instanteDeIso`, la clave en `presentarImportacion` y la
  exportación. `resumenTexto` y `textoDelEstado` no cambian. Los tests de
  F-036 no tienen diff y pasan.
- **La fecha es la de Madrid.** La comparé con un oráculo independiente en
  122.198 instantes de 2024 a 2027, incluidos los cambios de hora al
  segundo, y no falla ninguno.
- **El rótulo «original» solo sale con `ya_importado`.** Una importación
  nueva dice siempre «Resumen de esta importación», aunque la respuesta
  traiga una fecha.
- **C1 y C2 son equivalentes de verdad.** Lo comprobé con un barrido de 2
  millones de entradas.
- **O11-1 y O11-5 están cerrados.** Con mi parser, la huella de
  `importar.html` solo gana la entrada del rótulo.
- Hice 19 mutaciones mías en 4 familias. Las que sobreviven solo se
  distinguen con datos o marcado que nadie mandaría, y ninguna produce una
  fecha equivocada con datos reales. Van como informativo (O12-1 a O12-4).

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes (el control del
cero está más abajo). Lo compensan las mutaciones a mano: 61 del
implementer y 19 mías.

La regla 7 de `reviewer.md` (orden) es **N/A**. Solo aplica en rigor
`critico`, y además aquí no hay un orden entre colaboradores que proteger.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, sobre HEAD. Lo relancé porque el implementer lo corrió **antes** del commit de T34, que añade tests | **exit 0**, `ENTORNO LISTO`. Raíz: 114 passed. Front: **707 passed** (30,23 s, ejecutado, no desde caché). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. ruff: 71 avisos, todos de deuda previa |
| `node --test "tests_js/*.test.js"` (línea base del worktree) | **645/645** |
| `git diff --stat 9812d69..HEAD` sobre `services/postventa-api`, `js/api.js`, `js/oficios.js`, `css/`, `tests/test_f036_front.py`, `tests_js/importacion.test.js` y `tests_js/oficios.test.js` | **vacío** |
| `git diff --stat 2a86bca..HEAD -- js/importacion.js` y los dos tests de Node de F-036 | `importacion.js`, 65 líneas añadidas y ninguna borrada. Los tests de F-036, vacíos |
| Huella funcional de `importar.html` con mi parser (`html.parser`). Mira `x-*`, `@*`, `:*`, `id`, `name`, `for`, `type`, `accept`, `value`, `disabled`, `required`, `autocomplete`, `src`, `href`, `tabindex`, `aria-hidden`, `inert` y `hidden`, con el ámbito de Alpine y el texto de los botones | `9812d69`: 69 entradas; HEAD: 70. La **única** diferencia es `('p', (('x-text', 'resultado.rotuloResumen'),), …template[x-if=resultado])` |
| Diff de `HUELLA_DE_IMPORTAR` entre `09b5660` y `fa14520` | Una tupla añadida, la del rótulo, más su comentario |
| Oráculo de fechas (Node, en el scratchpad) | Comparé `rotuloResumen` con `Intl` sobre `new Date(iso)` cada 17 min 13 s de 2024 a 2027 (122.198 instantes), en tres formas cada uno: con `Z`, sin desfase y como `isoformat()` de Python con microsegundos. **0 fallos** |
| Barrido de C1 y C2 | Lo detallo en la respuesta 4 |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `{}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el informe declara un «Tiempo total» de 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 generados, 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre las líneas del diff del bloque, ignorando la exclusión | `test_f035_paginas.py`: 321 líneas y 61 mutantes; `test_f035_portal.py`: 44 líneas y 11 mutantes. El generador funciona y el cero es **legítimo** |
| `git log --diff-filter=A 9812d69..HEAD` | No se añade ningún fichero |
| `console.*`, `debugger`, `print(`, `TODO` y `FIXME` en las líneas añadidas | Ninguno |
| Zona horaria del proceso en Node 24 sobre Windows | `process.env.TZ = …` en caliente sí cambia la zona (`America/New_York` y `Pacific/Kiritimati`). Los tres tests «aunque el proceso esté en …» prueban de verdad otra zona |
| Mutaciones a mano | Las hice en un worktree desechable del scratchpad, sobre `e5e4201`, con la rama temporal `feature/F-035-rev-b12` para que las guardias de rama no se salten. Apliqué cada mutación sola, con los CRLF conservados, y Node con el reporter `tap`. Al terminar retiré el worktree y la rama, y `git status` quedó limpio |

### Mutaciones del reviewer, por familias

Evité repetir las 61 del implementer: estas buscan lo que su tabla no
prueba. En las de HTML separo los tests que caen **de verdad** de los
controles que solo dejan de encontrar su cadena, que es la muerte
artificial de K2 y S4 en bloques anteriores.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **J · `rotuloResumen` / `instanteDeIso`** | J1 | decide por la fecha y no por `ya_importado`: `!ya_importado && !importado_at_utc` | muerta | R74 «sin ya_importado» (que trae fecha) |
| | J2 | `rotuloResumen(respuesta.resumen)` en `presentarImportacion` | muerta | R74 `presentarImportacion` |
| | J8 | `instante.toLocaleDateString("es-ES")`: la zona del proceso y sin ceros | muerta | 19 casos, entre ellos los tres de la zona del proceso |
| | J9 | `new Date(anio, …)` local en vez de `Date.UTC` | muerta | 12 casos, entre ellos «sin zona», «solo la fecha» y dos de la zona del proceso |
| | J3 | el separador solo `T` (rechaza el espacio de `str(datetime)`) | **sobrevive** | O12-2 |
| | J4 | el regex sin la `i` (rechaza `t`/`z` en minúscula) | **sobrevive** | O12-2 |
| | J5 | sin `trim()` | **sobrevive** | O12-2 |
| | J6 | los segundos obligatorios (rechaza `…T23:30Z`) | **sobrevive** | O12-2 |
| | J7 | sin `minutos > 59` en el desfase | **sobrevive** | O12-2 |
| **H · El rótulo en `importar.html`** | H3 | `x-html` en vez de `x-text` | muerta | `o11_5_…huella…` y `r74_importar_pinta…` |
| | H4 | `:class="resultado.yaImportado ? '' : 'hidden'"`: se esconde en una importación nueva | muerta | `o11_5_…huella…` |
| | H5 | el rótulo, fundido en el `x-text` de los recuentos | muerta | `o11_5_…` y `r74_importar_pinta…` |
| | H1 | `class="mt-2 hidden"` en el rótulo | **sobrevive en sustancia** (solo caen 6 controles) | O12-1 |
| | H2 | `class="mt-2 sr-only"` en el rótulo | **sobrevive en sustancia** (solo caen 6 controles) | O12-1 |
| **G · Guardia de O10-2 / O11-1** (probadas con `_o10_2` directamente, para que la `?v=` no las mate de forma artificial) | G1 | una regla posterior `label:focus-within { outline: none !important; }` | **sobrevive** | O12-3 |
| | G2 | `.rs-btn:focus-within` sólido y `label.rs-btn:focus-within { outline: none }`: gana la del `label` por especificidad | **sobrevive** | O12-3 |
| | G3 | el contorno del color del lienzo (`#fff`) | **sobrevive** | O12-3 |
| | G4 | `tabindex="-1.5"`: el navegador lo lee como -1 | **sobrevive** | O12-3 |
| **L · El selector desde fuera** | H6 | `class="… hidden"` en la `<label>` de «Elegir el Excel» | **sobrevive en sustancia** (solo caen 2 controles) | O12-4 |

Mueren **5 de 19**. Las 14 vivas:

- **Familia J**: ninguna superviviente produce una fecha **equivocada** con
  datos que el backend vaya a mandar. Todas, salvo J7, solo hacen que una
  fecha rara se rotule **sin fecha**, que es lo seguro. J7 acepta un
  desfase de 99 minutos, que nadie manda.
- **Familias H, G y L**: es marcado o CSS que nadie escribiría. Además el
  estado (`textoDelEstado`) ya dice «Este fichero ya se había importado» y
  el ojo de V1 lo ve.

### Respuestas a las preguntas del líder

**1 · El cambio en `js/importacion.js`: solo `rotuloResumen` y la clave.**

- El diff contra `9812d69` y contra `2a86bca` es el mismo, y solo añade:
  - el bloque «El rótulo del resumen»: `FECHA_DE_MADRID`, `FECHA_ISO`,
    `instanteDeIso`, que es privada, y `rotuloResumen`;
  - la línea `rotuloResumen: rotuloResumen(respuesta),` en
    `presentarImportacion`;
  - la línea `rotuloResumen: rotuloResumen,` en la exportación.
- **`resumenTexto` y `textoDelEstado` están intactos.** Ninguna línea de
  `resumenLegible` ni de `textoDelEstado` aparece en el diff. El caso de
  `presentarImportacion` lo fija además con el texto literal de F-036.
- **Los tests de F-036 no tienen diff** (`test_f036_front.py`,
  `importacion.test.js` y `oficios.test.js`, desde `9812d69`; los dos de
  Node, también desde `2a86bca`) y pasan: los 707 del front y los 645/645
  de Node.
- **R33 enmendado**: admite `M js/importacion.js` y nada más. El control sin
  git rechaza `oficios.js`, `api.js`, `app.js`, el `M` de la guarda y el `A`
  o el `D` de `importacion.js`. Es más estricto que la enmienda de la spec,
  que ya admite `oficios.js`, y lo hace a propósito: R75 es del bloque 13.

**2 · La fecha.**

- **El día es el correcto en hora de Madrid, también cuando en UTC es otro
  día.** El oráculo da 0 fallos en 122.198 instantes. Las fronteras exactas
  salen bien:
  - `2026-03-28T22:59:59Z` es el 28/03 y `23:00:00Z`, el 29/03 (todavía
    UTC+1);
  - `2026-03-29T21:59:59Z` es el 29/03 y `22:00:00Z`, el 30/03 (ya UTC+2);
  - `2026-10-24T22:00:00Z` es el 25/10, y `2026-10-25T23:00:00Z`, el 26/10;
  - el 29/02 de 2028 y la noche de fin de año también salen bien.

  No depende de la zona del navegador: lo prueban los tres tests de la
  zona del proceso, que de verdad la cambian, y mis J8 y J9 mueren.
- **Sin desfase, se lee como UTC.** Es razonable, porque el campo se llama
  `_utc`, y es lo contrario de lo que haría `Date`, que lo leería en la
  hora del navegador. Pero es una **suposición sobre F-053, y F-053 tiene
  que respetarla.** Lo que F-053 debe cumplir:
  1. **`importado_at_utc` es un instante, con desfase explícito.**
     Preferiblemente en UTC: `…T23:30:00Z` o `…T23:30:00+00:00`, el
     `isoformat()` de un `datetime` *aware* pasado a
     `astimezone(timezone.utc)`. La columna es `timestamptz`
     (`12_importaciones.sql:38`), así que psycopg la devuelve *aware* y en
     la zona de la sesión.
  2. **Nunca quitar el `tzinfo`** (`replace(tzinfo=None)`, un `strftime`
     sin `%z`) a un valor que esté en hora de Madrid. El front lo leería
     como UTC, y entre las 22:00 y las 24:00 de Madrid (las 23:00 en
     invierno) el rótulo diría el **día siguiente**. Es el único fallo
     posible del contrato que da una fecha **equivocada** en vez de ninguna.
  3. **El desfase va con cuatro cifras** (`+00:00` o `+0000`). El texto
     crudo de PostgreSQL (`2026-07-15 23:30:00+00`, con dos cifras) no se
     acepta, y el rótulo saldría **sin fecha**. Es seguro, pero se pierde
     la fecha.
  4. **Con `T` y con segundos.** El front tolera el espacio y la falta de
     segundos, pero ningún test fija esa tolerancia (J3 y J6), así que F-053
     no debe contar con ella.

  Lo dejo escrito aquí para la ficha de F-053. El §5.2 del informe del
  implementer dice lo mismo en corto.
- **La validación «más estricta que `Date`» es razonable.** Un rótulo con
  una fecha equivocada engaña justo donde R74 quiere evitarlo. Uno sin
  fecha solo se queda corto, y R74 ya prevé ese texto. `Date` daría el 30
  de febrero como el 2 de marzo, «10/03/2026» como el 3 de octubre y un
  número como un instante epoch. El implementer los rechaza y los tests lo
  fijan.
  - Comprobé además que se rechazan la hora 24, el año `0050` (que
    `Date.UTC` convertiría en 1950) y el desfase `+24:00`.
  - Se aceptan `+14:00` y `+23:59`, que son instantes bien formados.
  - El precio está en O12-2: unas pocas formas de ISO válidas que hoy se
    aceptan no las fija ningún test. Nunca dan una fecha equivocada.

**3 · El rótulo «original» solo sale con un fichero ya importado.**

- `rotuloResumen` mira primero `!respuesta || !respuesta.ya_importado`. Con
  `ya_importado` falso, ausente, `0` o `null` devuelve «Resumen de esta
  importación», **aunque la respuesta traiga `importado_at_utc`**. Lo probé
  con `{ya_importado: false, importado_at_utc: "…Z"}` y con
  `{importado_at_utc: "…Z"}`, y lo fija el primer caso de Node: mi J1
  muere.
- Esto importa porque el contrato de §16.6 dice «de la importación de la
  respuesta». F-053 seguramente mandará la fecha **también** en las
  importaciones nuevas.
- Usa la misma veracidad que `textoDelEstado` (`if (respuesta.ya_importado)`)
  y que `yaImportado: Boolean(…)`, que elige el `:class` azul. Las tres
  cosas no pueden discrepar.
- En `importar.html` el rótulo **se ve siempre**: dice «de esta importación»
  o «la original». La guardia prohíbe esconderlo con un atributo, y la
  huella prohíbe un `:class` nuevo (H4 muere). Con una clase estática como
  `hidden` sí se escaparía (O12-1).

**4 · C1 y C2: son equivalentes de verdad.**

- Barrí 2.000.000 de entradas:
  - los años 2024, 2026, 1900 y 2000;
  - todos los meses y días de `00` a `99`;
  - las horas 0, 12, 23, 24, 25, 47, 48, 72, 95 y 99;
  - los minutos y segundos `00:00`, `59:59`, `60:00`, `00:60` y `99:99`.

  Lo comparé con el original (con los CRLF normalizados, para que la
  mutación se aplicara de verdad: lo verifiqué).
- **C1** (sin `getUTCDate() !== dia`): **0 diferencias.** Un día que no
  existe siempre cambia el mes. El desborde de horas, minutos y segundos lo
  paran sus propias comparaciones.
- **C2** (sin `hora > 23`): **0 diferencias.** Una hora de 24 a 99 suma de
  1 a 4 días, y eso siempre cambia el día del mes.
- **Las dos a la vez sí cambian el resultado**: 19.700 diferencias, por
  ejemplo `2026-07-15T24:00:00Z`, que pasaría a leerse como el 16/07. Las
  dos condiciones se cubren **la una a la otra**, y el par entero lo
  protege el caso «hora 25», que caería. Por eso está bien dejarlas las
  dos: quitar una no cambia nada, y quitar las dos sí.
- **Anotado: equivalentes, no bloquea.**

**5 · O11-1 y O11-5: cerrados.**

- **O11-5.** `HUELLA_DE_IMPORTAR` se fijó en `bcdf46a`, antes de R74.
  Coincide con mi parser independiente sobre `9812d69`, que además mira
  `href`, `src`, `tabindex`, `aria-hidden`, `inert` y `hidden`.
  - En `fa14520` gana **una sola tupla**, la del rótulo. Mi parser dice lo
    mismo entre `9812d69` y HEAD: **una sola entrada nueva**.
  - Los 7 controles (L1–L4, K3, una directiva nueva y un texto de botón)
    muerden.
  - Mis H3, H4 y H5 mueren por la huella.
- **O11-1.** Hace lo que la review del bloque 11 pidió, y algo más:
  - el `tabindex` negativo (K1), `disabled`, también heredado de un
    `fieldset`, `aria-hidden="true"` e `inert`, en el control o en un
    ancestro;
  - un contorno sólido, con ancho y no transparente, calculado con la
    cascada por propiedades;
  - cada caso con su control, 11 que saltan y 6 que no.

  Las K1, K3 y K5 de la review anterior, aplicadas sobre la página real,
  mueren con la guardia (no solo con los controles): lo trae la tabla del
  implementer, familia J.

  Lo que queda fuera (O12-3, O12-4) son casos de especificidad entre
  selectores distintos, `!important`, un color igual al fondo, un
  `tabindex` decimal y una clase `hidden` en la etiqueta. Nadie los
  escribe, y V1 los vería.

**6 · Navegador**: queda para V1/V2 del humano.

- Importar el mismo fichero dos veces:
  - la primera, aviso verde o ámbar con «Resumen de esta importación»;
  - la segunda, aviso azul con «Resumen de la importación original de este
    fichero», sin fecha hasta que exista F-053.
- Comprobar que el rótulo se distingue de los recuentos (§5.3 del informe).

**Los apuntes del §5 del informe: están bien.**

- §5.1 y §5.2: las respuestas 2 y 3.
- §5.3: el rótulo sin clase propia, con `mt-2` en el tono del aviso, es
  correcto, porque evita tocar la hoja y la `?v=`. Si en V1 no se distingue,
  la salida que propone es la buena.
- §5.4: que se vea siempre es lo que pide R74.
- §5.5: `instanteDeIso` privada, bien.
- §5.6: el refactor de R33 a `problemas_r33` no cambia su comportamiento
  sobre la rama, y gana un control sin git.
- §5.7: no mirar `:disabled` ni `:tabindex` ligados es correcto, porque
  dependen del estado.
- §5.8 y §5.9: correctos.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo, sobre HEAD).
  [x] Existen los ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba. [x] Ninguna feature pasa a `done`.
- **C3**
  - [x] La primera línea con la ruta está en los nueve ficheros tocados.
  - [x] Sin depuración, TODO ni secretos. Sin dependencias nuevas:
    `Intl.DateTimeFormat` es del lenguaje.
  - [x] Comentarios en español.
  - [x] Ningún PDF ni parte en git: `--diff-filter=A` vacío.
  - [x] El límite de servicio se respeta: `services/postventa-api` no tiene
    diff, y el dato que falta se deja a F-053 (R76).
  - Arquitectura hexagonal, unidad «parte», Sigrid, firma, «firmado no es
    conforme», duplicados y `conest`: **N/A justificado**. El diff es front
    (una función pura de presentación, una línea de HTML) y tests, y no
    toca la API ni el circuito.
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4** [x] Cada requisito tiene tests trazables, y todos pasan:

  | Requisito | Tests |
  |---|---|
  | R74, texto según `ya_importado` | Node «f035 R74: rotuloResumen, sin ya_importado / sin el campo ya_importado / ya importado con fecha válida…» y «nunca lanza» |
  | R74, sin fecha o fecha no válida | Node, los 15 casos de fecha ausente y de fecha basura (incluidos los de T34: lista, segundo 60 y fecha con cola) |
  | R74, día de Madrid (23:30 UTC de verano y demás) | Node, los 12 casos de cambio de día y desfase, y los 3 de la zona del proceso |
  | R74, `presentarImportacion` con el rótulo y sin cambiar los recuentos | Node «f035 R74: presentarImportacion lleva el rótulo…» y los de F-036 sin tocar (R43, R50) |
  | R74, en `importar.html`: justo encima, dentro del aviso y siempre visible | `test_f035_r74_importar_pinta_el_rotulo…`, 6 controles y `…fuera_del_aviso_salta` |
  | R33 enmendado | `test_f035_r33_no_se_modifica_nada_del_circuito` y `…control_admite_el_m_de_importacion_js…` |
  | R76 (la API, sin tocar) | `git diff --stat 9812d69..HEAD -- services/postventa-api` vacío. Lo vigilan R32 y R33 en la rama |
  | O11-5 | `test_f035_o11_5_importar_conserva_su_huella_funcional` y 7 controles |
  | O11-1 | `test_f035_o10_2_control_el_selector_inalcanzable_salta` (17 casos), `…o11_1_control_un_fieldset…` y `…o11_1_control_lo_que_si_deja_llegar…` (6 casos) |

  [x] Sin red ni BBDD. [x] El MANUAL (vistazo en navegador) consta en
  `current.md`, enviado a V1/V2.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae las salidas reales:
    - R74 en Node: 34 fallos de 84, con `TypeError: rotuloResumen is not a
      function`;
    - R74 en Python: «hay 0 y 1» y los controles;
    - O11-1: 11 fallos de 26;
    - R33 sin enmendar: cae con el `M` de `importacion.js`.

    O11-5 no tiene RED por definición, porque es de no regresión. Que
    muerde lo prueban sus 7 controles, y que cayó con **solo** la entrada
    nueva al meter R74.
  - [x] **Cobertura**: N/A con el motivo impreso por `init.sh`.
  - [x] **Mutación**: informe de la herramienta con 0 mutantes, recalculado,
    reejecutado con totales idénticos y con el control del cero hecho (72).
    Que tarde 0,0 s es coherente: no hay nada que evaluar.
  - [x] **Mutantes a mano**: del implementer, 61, con 59 muertas y 2
    equivalentes que he comprobado (C1 y C2). Mías, 5 de 19, con las 14
    vivas analizadas arriba. En rigor `estandar` basta con documentarlas.
  - [x] «Evidencias» con los cuatro números.
  - [x] Ningún N/A sin justificar. La regla 7 es N/A porque es de
    `critico`.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] T33 y T34 están `[x]`, con sus commits `F-035 T33: …` y
    `F-035 T34: …`.
  - [x] O11-5 y O11-1 llevan cada una su propio commit (`F-035 O11-5: …` y
    `F-035 O11-1: …`). Son tareas de la review, no de `tasks.md`, así que
    no les toca número `Tn`.
  - [x] No hay ficheros sin trackear. El worktree
    `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
    bloque. El del implementer y el mío están retirados.
  - [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **Contrato para F-053 (no es un hallazgo de este bloque, pero hay que
  pasarlo).** Son los cuatro puntos de la respuesta 2.
  - El que importa es el 2: **nunca un `importado_at_utc` sin desfase que
    esté en hora de Madrid**. Es el único caso que pintaría una fecha
    equivocada.
  - **Destino: el spec-author de F-053**, cuando se dé de alta: en sus
    requisitos y en su test de contrato. El líder decide si lo apunta ya en
    `harness/features.json`.
- **O12-1 · La guardia de R74 no ve que el rótulo se esconda con una
  clase** (H1 `hidden`, H2 `sr-only`; también `invisible`). Solo mira
  `_CERRABLE`, que son atributos.
  - El §1 del informe dice «que nada lo puede esconder». Es algo más de lo
    que la guardia comprueba.
  - Hoy el rótulo no lleva ninguna. Además `estadoTexto` ya dice «ya se
    había importado», así que el riesgo es bajo.
  - **Propuesta**: en `problemas_r74`, rechazar también `clases(rotulo) &
    (_OCULTA_DEL_TODO | {"sr-only"})`, con su control.
  - **Destino: bloque 14**, o el siguiente bloque que toque `importar.html`.
- **O12-2 · Tolerancias de `instanteDeIso` que ningún test fija** (J3 el
  espacio, J4 las minúsculas, J5 los espacios alrededor, J6 la falta de
  segundos, J7 los minutos del desfase por encima de 59).
  - Todas, salvo J7, solo deciden si una forma rara sale con fecha o sin
    ella. Ninguna da una fecha equivocada.
  - **Destino: F-053.** Si F-053 fija una forma (la recomendada es `T`,
    segundos y `Z` o `+00:00`), basta con un caso de Node con **esa** forma
    exacta, que ya existe: «con +00:00 y microsegundos». Si eligiera el
    espacio de `str(datetime)`, que añada su caso.
  - J7 es opcional: un desfase de 99 minutos no lo manda nadie.
- **O12-3 · La cascada de O11-1 se calcula por selector exacto, no por
  especificidad ni `!important`.** Tampoco ve un color igual al del fondo
  ni un `tabindex="-1.5"` (G1–G4).
  - Es la familia O11-1, con un CSS que nadie escribiría. Modelar la
    especificidad sería sobreespecificar la guardia.
  - **Destino: V1/V2.** Tabular hasta «Elegir el Excel» y ver el contorno
    burdeos, que ya está en el guion.
- **O12-4 · La guardia de O10-2 no mira las clases de ocultar en los
  ancestros** (H6: `hidden` en la `<label>`).
  - Sin la etiqueta no hay botón «Elegir el Excel», y cualquiera lo ve en
    el primer vistazo.
  - **Destino: opcional.** Si se quiere, en `problemas_o10_2` basta con
    extender a los ancestros la comprobación de `_OCULTA_DEL_TODO` que ya
    hace con el control.
- Siguen abiertos, como estaban:
  - **O11-2** (opcional), **O11-3** y **O11-4** (V1/V2);
  - **O10-1**, **H16-3 a H16-6**, **O17-2**, **O9-2 a O9-4** y **O9-7**:
    van al spec-author, en el bloque 14;
  - **O10-5**, **O9-1**, **O9-5** y **O9-6**: van a V1/V2;
  - **O16-4**, que es opcional.
  - El README del front tiene que contar el rótulo de R74 (bloque 14, §6
    del informe).

### Automejora (propuesta, no aplicada)

**`reviewer.md`, regla para las mutaciones de HTML o CSS: separar los tests
que caen de verdad de los controles que solo dejan de encontrar su
cadena.**

Ya pasó tres veces (S4 en el bloque 10, K2 en el 11, y H1, H2 y H6 aquí).
Una mutación sobre la página real hace caer los controles parametrizados
que buscan el texto literal con `real.count(viejo) == 1`. La suite se pone
en rojo, pero la guardia **no ha visto nada**.

La propuesta: al anotar el resultado de una mutación, contar como muerta
solo si cae algún test que **no** sea un control de «el control ya no
encuentra una sola vez». Si solo caen esos, se anota **«sobrevive en
sustancia»**. En las mutaciones de CSS, además, probar la guardia
directamente, porque la `?v=` mata cualquier cambio de la hoja de forma
artificial.

Vale para cualquier proyecto con guardias estáticas sobre marcado, así que
va también a `arnes-base`.

## Review del bloque 13 · T35–T36 · 2026-10-06

> reviewer. Alcance **acotado** a `git diff 6c7bafc..HEAD`: `75246db` (T35) y
> `892487d` (T36), en `feature/F-035-portal-posventa`. Es el apunte (a) del
> humano (R75): en `oficios.html`, «Decididos como distintos» con un «Son el
> mismo» por par. El dato `oficio.distintos` lo dará F-053, que aún no existe,
> y el front lo consume de forma tolerante. Es el único cambio de lógica que
> se admite en `js/oficios.js`, y sin ninguna llamada nueva (R88 de F-036).
>
> Los bloques 14–15 siguen abiertos **a propósito** y no cuentan como `[ ]`.
> El vistazo en navegador queda para V1/V2. La sección solo se verá con F-053
> desplegada (V4 g).
>
> Criterio de severidad del líder: bloqueante es un riesgo real para el
> usuario o un incumplimiento de la spec. Una mutación que solo se distingue
> con datos que nadie mandaría, o una variante de una familia ya cubierta, va
> como informativo con su destino.

### Veredicto

**CHANGES_REQUESTED** (del bloque 13). Hay un solo cambio, y es **solo de
tests**. El código de producción es correcto y no hay que tocarlo.

- **Lo que está bien**:
  - el botón manda «mismo» con los códigos de su par, y nunca «distinto»;
  - la tolerancia, cuando falta el campo o llega mal formado;
  - «ni una llamada nueva»: los conteos de R88 no cambian;
  - la huella de `oficios.html` solo crece con lo de R75;
  - F-036 y la API, sin diff;
  - A6 es equivalente de verdad.
- **Lo que falla: ningún test de R75 junta los distintos con otras
  secciones.** Todos usan `propuestasSinDistintos()`, que no lleva
  propuestas, ni avisos, ni grupos de más de un código. Por eso sobreviven
  tres mutaciones mías (K1, K12 y K13). Se distinguen con los datos
  **normales**, no con datos raros:
  - K1: la sección desaparece si hay cualquier otra;
  - K12: los avisos desaparecen si hay distintos;
  - K13: los grupos vigentes desaparecen si hay distintos.
- **El test que debería verlo no puede fallar.** «los distintos no cambian
  propuestas, grupos ni avisos» compara tres listas vacías, así que no
  comprueba lo que dice su nombre.
- **El caso no es raro, es seguro.** Un aviso (R82) solo existe si algún par
  del grupo se decidió «distinto». Así que, con F-053 desplegada, **toda obra
  con avisos traerá también `distintos`**. Es justo la combinación que nadie
  prueba. El primer caso real, la obra 0677, tendrá además propuestas.
- Por eso no lo dejo como informativo: no hacen falta datos raros para
  verlo. La regresión dejaría al usuario sin avisos o sin la sección en el
  caso real, con toda la suite en verde.

### Nivel de rigor

`estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura
de las líneas cambiadas y campaña de mutación con los supervivientes
analizados.

El bloque no tiene Python de producción. Por eso la cobertura sale N/A, con
el motivo impreso por `init.sh`, y la campaña da 0 mutantes (el control del
cero está más abajo). Lo compensan las mutaciones a mano: 50 del
implementer y 14 mías.

La regla 7 de `reviewer.md` (orden) es **N/A**, por dos motivos: solo aplica
en rigor `critico`, y el bloque no añade ninguna puerta antes de un
colaborador. La única es `puedeDecidir()` dentro de `decidir()`, que es de
F-036 y no tiene diff. Aun así, el test «sin sesión, … no manda nada» la
recorre con un `api` doble que anota cada llamada.

### Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, sobre HEAD (lo pide el paso 1 del protocolo) | **exit 0**, `ENTORNO LISTO`. Raíz: 114 passed. Front: **729 passed** (21,43 s). La API, en caché (árbol sin cambios). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| `node --test "tests_js/*.test.js"` | **677/677** |
| `git diff --stat 6c7bafc..HEAD` sobre `js/importacion.js`, `js/api.js`, `css/`, `services/postventa-api`, `tests/test_f036_front.py`, `tests_js/oficios.test.js` y `tests_js/importacion.test.js` | **vacío** |
| `git diff --stat $(git merge-base dev HEAD) HEAD -- services/postventa-api` | **vacío** (R76) |
| `git diff --stat 2a86bca HEAD -- js/oficios.js` | 43 líneas, todas de este bloque: F-035 no había tocado `oficios.js` antes |
| Conteos de R88 sobre `js/oficios.js` sin comentarios | `decidirCatalogos(`: **1**. `cuerpoDeDecision(`: **2**. Igual que antes: el test de F-036 que los fija pasa sin tocarse |
| Huella funcional de `oficios.html` con **mi** parser (`html.parser`). Mira `x-*`, `@*`, `:*`, `id`, `name`, `for`, `type`, `accept`, `value`, `disabled`, `required`, `autocomplete`, `src`, `href`, `tabindex`, `aria-hidden`, `inert`, `hidden` y `style`, con el ámbito de Alpine y el texto de los botones | `6c7bafc`: 60 entradas; HEAD: 64. **No se quita ninguna.** Se añaden 4: la sección, el `x-for`, el `x-text` del par y el botón. Son las mismas cuatro que añade `HUELLA_DE_OFICIOS` |
| Recálculo `alcance_de_feature("F-035", base="2a86bca")` | `lineas={}`: 0 mutantes, igual que `progress/mutacion_F-035.md` |
| Reejecución de la campaña (el informe declara un «Tiempo total» de 0,0 s, menos de 5 min), con `--salida` en el scratchpad | 0 generados, 0 evaluados, 0 muertos, 0 supervivientes y 0 timeouts: **idéntico** al informe. `git status` limpio |
| Control del cero: `generar_mutantes` sobre las líneas del diff del bloque, ignorando la exclusión | `test_f035_paginas.py`: 192 líneas y 45 mutantes. `test_f035_portal.py`: 16 líneas y 1 mutante. El generador funciona y el cero es **legítimo** |
| `git log --diff-filter=A 6c7bafc..HEAD` | No se añade ningún fichero |
| `console.*`, `debugger`, `print(`, `TODO` y `FIXME` en las líneas añadidas | Ninguno. La única coincidencia es `_OCULTA_DEL_TODO`, un nombre |
| Backend de F-036: ¿manda la última decisión? | Sí. `domain/models/equivalencias.py` toma la última decisión de cada par (R81, R95), y `codigo_a`/`codigo_b` son `str` con `codigo_a < codigo_b`. La frase de §16.6 («manda la última decisión») es cierta, y «Son el mismo» deshace un «distinto» |
| Mutaciones a mano | Las hice en un worktree desechable del scratchpad, sobre `892487d`, con la rama temporal `feature/F-035-rev-b13` para que las guardias de rama no se salten. Apliqué cada mutación sola, con los CRLF conservados. Corrí Node entero y `test_f035_paginas.py`, `test_f036_front.py` y `test_f035_portal.py`. Distingo los controles que solo dejan de encontrar su cadena. La S26 (la 26 del implementer) es el control de cordura del guion: muere. Al terminar retiré el worktree y la rama, y `git status` quedó limpio |

### Mutaciones del reviewer, por familias

Evité repetir las 50 del implementer: estas buscan lo que su tabla no
prueba. Las lancé en dos tandas, por familias completas.

| Familia | # | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **K · `paresDistintos` / `presentarPropuestas`** | K2 | la clave sale de la entrada cruda (`codigo_a + "-" + codigo_b`) y no del par ordenado | muerta | Node: forma del par, repetido al revés, lista desordenada |
| | K4 | se descarta un par con un código sin nombre en la obra | muerta | Node: «un código que no es de la obra» y «un oficio sin nombre» |
| | K5 | solo el primer par (`distintos.slice(0, 1)`) | muerta | Node: varios pares, desordenada, claves distintas… |
| | K11 | lee `respuesta.distintos` (en la raíz) en vez de `oficio.distintos` | muerta | Node: 13 casos. Fija **dónde** va el campo, lo que importa al contrato de F-053 |
| | K3 | gana el primer repetido en vez del último | **equivalente** | Mismo par, mismo objeto: la clave fija los códigos, y los nombres salen del mismo mapa |
| | **K1** | `distintos = []` si hay propuestas, grupos o avisos | **sobrevive** | **Cambio requerido 1** |
| **K' · Los distintos junto a las demás secciones** | **K12** | `avisos: distintos.length ? [] : avisos` | **sobrevive** | **Cambio requerido 1** |
| | **K13** | `grupos: distintos.length ? [] : grupos` | **sobrevive** | **Cambio requerido 1** |
| **L · HTML: visible pero no pulsable, o escondido por estilo** | L1 | `style="display: none"` en el botón | muerta | `test_f035_r54_r60_la_pagina_real_no_quita_el_foco_ni_lleva_style[oficios.html]` |
| | L2 | `style="display:none"` en el `<li>` del par | muerta | el mismo de R54/R60 |
| | L7 | `opacity-0` en la sección | muerta | `test_f035_r72_la_pagina_real_lleva_la_identidad_ruesma[oficios.html]` (lista cerrada) |
| | L15 | `inert` en la sección: se ve, pero no se puede pulsar | **sobrevive en sustancia** (solo caen 4 controles) | O13-1 |
| | L17 | `pointer-events-none` en el `<li>` del par | **sobrevive en sustancia** (solo cae 1 control) | O13-1 |
| **S · Cordura del guion** | S26 | el botón manda `'distinto'` (la 26) | muerta | Node «manda mismo…», `r75_oficios_pinta…` y la huella de O10-3 |

Mueren **8 de 14**, más 1 equivalente (K3). Las 5 vivas:

- **K1, K12 y K13**: el **cambio requerido 1**. Se distinguen con los datos
  de siempre (ver el veredicto).
- **L15 y L17**: marcado que nadie escribiría para dejar un botón visible
  pero sin respuesta. Es la familia O12-1 (lo que la guardia no ve). Va como
  informativo.

### Respuestas a las preguntas del líder

**1 · El botón.**

- **Manda `decidir([codigo_a, codigo_b], 'mismo')` con los códigos de su
  par, y nunca «distinto».**
  - En la sección hay **un solo** botón, dentro del `x-for="par in
    vista.distintos"`. Su `@click` es literalmente
    `decidir([par.codigo_a, par.codigo_b], 'mismo')`, con
    `:disabled="!puedeDecidir()"`.
  - `problemas_r75` exige ese `@click` exacto, un solo botón y que vaya
    dentro del bucle. La 26 (`'distinto'`) y la E3 (los códigos al revés)
    caen.
  - El test de Node lee la directiva **del HTML** y la evalúa con `vm` sobre
    `crearAppOficios` con un `api` doble. Comprueba que sale **una** llamada
    a `decidirCatalogos` con:
    - `codigos: ["9001", "9002"]`, el par de la vista, que llegó al revés;
    - `decision: "mismo"`;
    - la obra de las propuestas y no la del campo;
    - `confirmado: true`.

    Después recarga.
  - Sin sesión, o mientras se guarda otra decisión, el botón está
    deshabilitado y no manda nada (R89 de F-036).
  - Lo confirmé con mi S26: la mata Node, no solo la guardia estática.
- **Qué par es.** `x-for` recorre `vista.distintos`. Cada elemento es el
  `par()` de siempre, con `codigo_a < codigo_b`, y su clave `a-b` es la del
  `:key`. K2, K5 y K11 confirman que es el par correcto y que cada uno sale
  una sola vez.
- **`decidirCatalogos(` y `cuerpoDeDecision(` se cuentan igual**, 1 y 2.
  `test_f036_r88_solo_decidir_llama_al_endpoint_de_decisiones` no tiene diff
  y pasa. El JS no gana ninguna llamada: `paresDistintos` y `esCodigo` son
  puras y privadas.

**2 · Tolerancia.** Con el campo ausente, vacío, mal formado o con entradas
raras, **la pantalla sale como antes**:

- **Sin el campo**:
  - `distintos` es `[]`;
  - `sinNada` vale lo mismo que antes;
  - las demás claves de la vista no cambian (un test compara la vista sin el
    campo con la de una lista vacía, y comprueba sus siete claves).
- **En el HTML**, la sección va dentro del `<template x-if="vista">` con
  `x-show="vista.distintos.length"`. Con `[]` está en el DOM pero con
  `display: none`, igual que «Grupos vigentes» cuando no hay grupos. No
  parpadea antes de cargar, porque el `x-if` no la crea hasta que hay
  vista. La huella (mi parser) solo crece en sus cuatro entradas.
- **Si no es una lista** (texto, objeto, número, `true`, `null`):
  `Array.isArray` da `[]`. El literal `(oficio.distintos || [])` de §16.6
  habría **lanzado** con un texto o un objeto (A2 del implementer), y la
  pantalla entera dejaría de pintarse. La desviación es correcta y mejora la
  spec.
- **Si una entrada es rara** (`null`, un texto, una lista, falta un código,
  un código numérico, vacío, en blanco o igual al otro): se descarta, y las
  buenas siguen. «nunca lanza» lo prueba también sin respuesta y sin
  `oficio`.
- **Lo que no está probado es el caso contrario**: con distintos, que el
  resto de la pantalla siga como antes. Es el cambio requerido 1.

**3 · Contrato para F-053 (`oficio.distintos`).** Es lo que el front ya
supone, escrito para la ficha de F-053, igual que `importado_at_utc` en el
bloque 12:

1. **Dónde va: dentro de `oficio`**, en `GET /api/catalogos/propuestas`
   (`{obra, oficio: {oficios, grupos, propuestas, avisos, distintos}}`).
   - En la raíz de la respuesta el front **no lo ve** y no lo dice (K11).
2. **Qué forma tiene: una lista JSON de objetos `{codigo_a, codigo_b}`.**
   - Si no es una lista, el front lo ignora entero, sin avisar.
   - Las claves de más se ignoran.
   - **Sin `decidido_por` ni ningún `oid`** (R47 de F-036).
3. **Los códigos, como textos JSON, nunca como números.**
   - Tienen que ser **exactamente** el mismo texto que
     `oficio.oficios[].codigo`, con los ceros a la izquierda: `"0033"`, no
     `33` ni `"33"`.
   - Un código numérico, vacío o en blanco hace que **el par se descarte en
     silencio**: el usuario no lo vería.
   - El nombre se busca por igualdad exacta. Si el texto no coincide, sale
     «(sin nombre en esta obra)».
   - **Este punto es el que importa**: el primer caso real es `0033` ·
     `0133`, y como entero se perdería.
4. **Dos códigos distintos por par.** Un par de un código consigo mismo se
   descarta.
5. **El orden lo arregla el front, pero el contrato lo pide.** El front
   ordena cada par y la lista y quita los repetidos (la clave tiene que ser
   única para el `:key`). El contrato de §16.6 pide `codigo_a < codigo_b` y
   la lista ordenada. Es el mismo orden que el `CHECK` de la tabla y el
   `sort()` de JS para códigos ASCII.
6. **Sin guiones en los códigos.** El front identifica el par con `a-b`.
   Dos pares cuyos códigos lleven guiones podrían compartir clave, y uno
   desaparecería. Con los códigos de oficio de Sigrid (dígitos) no pasa. Si
   F-053 lo garantiza con un test, mejor; si no, basta con que conste.
7. **El backend filtra por obra; el front no.** Solo pares cuyos **dos**
   códigos son oficios de la obra y cuya **última** decisión es `distinto`.
   Un código de fuera de la obra se pintaría con «(sin nombre en esta obra)»
   y su «Son el mismo» funcionaría igual.
8. **Después de «Son el mismo», el par ya no viene.** El front manda
   `POST /api/catalogos/decisiones` con `decision: "mismo"` y los dos
   códigos ordenados, y luego recarga. Espera que ese par **ya no** venga en
   `distintos`, porque manda la última decisión.
   - **Test que F-053 debe tener**: «distinto, luego mismo» y el par no sale.
   - Otro: «mismo, luego distinto» y el par sí sale.
9. **Un par puede salir a la vez en `distintos` y entre los códigos de un
   aviso.** Es lo esperado: el aviso existe porque hay un «distinto». El
   front pinta las dos secciones (cambio requerido 1).
10. **Sin el campo, el bloque no se pinta.** El orden de despliegue es
    libre. Lo que espera a F-053 es solo V4 g.

**Destino: el spec-author de F-053**, en sus requisitos y en su test de
contrato. El líder decide si lo apunta ya en `harness/features.json`, como
hizo con `importado_at_utc` en `6c7bafc`.

**4 · Sin diff en lo de F-036 y en la API; la huella de `oficios.html` solo
crece en lo de R75.**

- `js/importacion.js`, `js/api.js`, `css/`, `services/postventa-api` y los
  tres tests de F-036 (`test_f036_front.py`, `oficios.test.js` e
  `importacion.test.js`): **sin diff** en `6c7bafc..HEAD`.
- La API tampoco tiene diff contra el merge-base con `dev`.
- `oficios.html`: +22 líneas y ninguna borrada.
- Mi huella independiente: 60 → 64 entradas, **cero quitadas** y las cuatro
  añadidas son las de R75. `HUELLA_DE_OFICIOS` gana exactamente esas cuatro
  tuplas, más su comentario.
- R33 admite el `M` de `oficios.js`. Su control sigue rechazando un `A` o un
  `D` de ese fichero, y el `M` de `api.js` y del circuito.

**5 · A6 es equivalente de verdad.** La mutación es
`paresDistintos(oficio.distintos || null, …) || []`:

- **`|| null`**: solo cambia los valores falsos (`undefined`, `null`, `0`,
  `""`, `false`, `NaN`) por `null`. Para todos ellos, `Array.isArray(x)` ya
  era falso, así que el resultado es `[]` igual. Los valores verdaderos
  pasan sin cambio.
- **`|| []`**: nunca actúa, porque `paresDistintos` siempre devuelve una
  lista, y una lista (también `[]`) es verdadera en JS.
- La equivalencia vale para cualquier entrada, no solo para las probadas.
  En `estandar` basta con documentarla, y está documentada.

**6 · El vistazo en navegador** queda para V1/V2: con el backend de hoy, la
pantalla de oficios tiene que salir como antes, sin la sección. La sección
solo se verá con F-053 desplegada (V4 g). Consta en `current.md` y en el §6
del informe del implementer.

### Cambios requeridos

1. **Un test de R75 con los distintos junto a las otras tres secciones, que
   cace K1, K12 y K13.**
   - **Dónde**: `services/postventa-front/tests_js/f035_paginas.test.js`.
   - **Qué está mal**: el test «f035 R75: los distintos no cambian
     propuestas, grupos ni avisos» (línea 903) parte de
     `propuestasSinDistintos()` (línea 759). Esa respuesta tiene
     `propuestas: []` y `avisos: []`, y sus cuatro grupos son de un solo
     código, que `presentarPropuestas` filtra. Así que compara listas vacías
     y no puede fallar.
   - **Qué hacer**: darle a ese test (o a uno nuevo, al lado) una respuesta
     con:
     - al menos **una propuesta**;
     - un **grupo vigente de dos o más códigos**;
     - un **aviso**;
     - y `distintos` con un par que coincida con dos códigos del aviso, que
       es el caso real.
   - **Qué comprobar**:
     - que `distintos` trae ese par;
     - que `propuestas`, `grupos`, `avisos` y `gruposVigentes` son iguales
       que sin `distintos`;
     - que **no están vacíos**, con un `assert` explícito, para que el test
       no vuelva a quedarse sin contenido;
     - y que `sinNada` es `false`.
   - **Cómo verificarlo**:
     - las tres mutaciones tienen que caer: K1, K12 (`avisos: distintos.length
       ? [] : avisos`) y K13 (`grupos: distintos.length ? [] : grupos`), en
       una copia aislada;
     - Node tiene que seguir en 677 + los nuevos, con `oficios.test.js` sin
       tocar;
     - y `bash harness/init.sh` en verde.
   - **Opcional, en el mismo commit**: que el test del componente
     («…manda «mismo»… y la pantalla recarga», `componenteDeOficios`, línea
     941) use esa misma respuesta, y así pruebe el botón en una pantalla con
     todo.

   Es un commit de tests, sin tocar `js/oficios.js` ni `oficios.html`. Puede
   ir como `F-035 T36: …` o como hallazgo de review (`F-035 R13-1: …`), según
   decida el líder.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo, sobre HEAD).
  [x] Existen los ficheros del arnés.
- **C2** [x] Una sola feature `in_progress` (F-035). [x] Rama
  `feature/F-035-portal-posventa`. [x] `current.md` lleva la entrada nueva
  arriba. [x] Ninguna feature pasa a `done`.
- **C3**
  - [x] La primera línea con la ruta está en los cinco ficheros de código y
    de test tocados.
  - [x] Sin depuración, TODO ni secretos. Sin dependencias nuevas.
  - [x] Comentarios en español.
  - [x] Ningún PDF ni parte en git: `--diff-filter=A` vacío.
  - [x] El límite de servicio se respeta: `services/postventa-api` no tiene
    diff, y el dato se deja a F-053 (R76).
  - Arquitectura hexagonal, unidad «parte», Sigrid, firma, «firmado no es
    conforme», duplicados y `conest`: **N/A justificado**. El diff es front
    (una función pura de presentación y una sección de HTML) y tests. No
    toca la API ni el circuito, y la decisión «mismo» va por el endpoint de
    F-036 que ya existe, sin cambios.
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4**
  - [ ] **Cada requisito tiene tests trazables, y todos pasan; pero R75 no
    está verificado entero.** Falta el caso «con distintos, lo demás sale
    como antes» (cambio requerido 1):

    | Requisito | Tests |
    |---|---|
    | R75, `presentarPropuestas().distintos` (contrato, orden, repetidos, nombres) | Node, los 22 casos de `CASOS_R75`, «cada par lleva su clave…» y «las claves… son distintas» |
    | R75, sin `distintos` la pantalla como antes | Node «sin oficio.distintos (hasta F-053)…» y «nunca lanza…» |
    | R75, `sinNada` | Node «sinNada cuenta los distintos…» |
    | R75, con distintos el resto como antes | Node «los distintos no cambian propuestas, grupos ni avisos»: **vacuo** (cambio requerido 1) |
    | R75, el botón (mismo, par, sesión, guardando, recarga) | Node «…manda «mismo» con sus dos códigos y la pantalla recarga», «sin sesión…», «mientras se guarda otra…»; `test_f036_r89_…[Son el mismo]` (sin tocar) |
    | R75, la sección en `oficios.html` (sitio, frase, bucle, botón, nada lo esconde) | `test_f035_r75_oficios_pinta_los_decididos_como_distintos_con_son_el_mismo` y 21 controles; `ROTULOS_DE_OFICIOS` (t31); la huella de O10-3 |
    | R76 (la API, sin tocar) | `git diff` vacío, contra `6c7bafc` y contra el merge-base. Lo vigilan R32 y R33 en la rama |
    | R33 enmendado | `test_f035_r33_no_se_modifica_nada_del_circuito` y `…control_admite_el_m_de_importacion_y_oficios_js…` |
    | R88 de F-036 («ni una llamada nueva») | `test_f036_r88_solo_decidir_llama_al_endpoint_de_decisiones`, sin tocar |

  - [x] Sin red ni BBDD.
  - [x] El MANUAL (vistazo en navegador) consta en `current.md`, enviado a
    V1/V2 y a V4 g.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae las salidas reales:
    - Node: 31 fallos de 120, con `TypeError … reading 'map'` y
      `oficios.html no tiene <section …>`;
    - Python: 22 fallos;
    - R33 sin enmendar: cae con el `M` de `oficios.js`.
  - [x] **Cobertura**: N/A con el motivo impreso por `init.sh`.
  - [x] **Mutación**: informe de la herramienta con 0 mutantes, recalculado,
    reejecutado con totales idénticos y con el control del cero hecho (46).
    Que tarde 0,0 s es coherente: no hay nada que evaluar.
  - [ ] **Mutantes a mano**:
    - del implementer, 50, con 49 muertas y A6 equivalente (comprobado);
    - míos, 14, con 8 muertas, K3 equivalente y 5 vivas.

    L15 y L17 van como informativo. **K1, K12 y K13 no**, porque los
    distingue el dato real: esto es el cambio requerido 1.
  - [x] «Evidencias» con los cuatro números y los workers de la campaña.
  - [x] Ningún N/A sin justificar. La regla 7 es N/A porque es de
    `critico` y porque no hay una puerta nueva.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] T35 y T36 están `[x]`, con sus commits `F-035 T35: …` y
    `F-035 T36: …`.
  - [x] No hay ficheros sin trackear. El worktree
    `.claude/worktrees/agent-a6e2f9bed1d46cdbc` ya existía y no es de este
    bloque. El del implementer y el mío están retirados.
  - [x] `features.json` dice `in_progress`, que es lo real.

### Informativo (no bloquea), con su destino

- **O13-1 · La guardia de R75 no ve un botón que se ve pero no se puede
  pulsar** (L15 `inert` en la sección, L17 `pointer-events-none` en el par).
  - Es la familia O12-1: marcado que nadie escribiría, y cualquiera lo
    notaría en el primer vistazo.
  - **Propuesta**: en `problemas_r75`, rechazar también `inert` y la clase
    `pointer-events-none` en el botón y en sus ancestros hasta la sección.
    Puede ser la misma lista que ya usa O11-1 para el selector.
  - **Destino: opcional**, en el mismo commit del cambio requerido 1 si se
    quiere.
- **O13-2 · `esCodigo` admite códigos con espacios alrededor y no los
  recorta.** `" 0033"` y `"0033"` serían dos pares distintos, y el primero
  se mandaría con el espacio a `POST /api/catalogos/decisiones`.
  - Nadie lo manda: los códigos salen de la misma tabla que
    `oficio.oficios`.
  - **Destino: el contrato de F-053** (punto 3: el mismo texto que
    `oficio.oficios[].codigo`). En el front no hace falta tocar nada.
- **O13-3 · El README del front tiene que contar R75**: la sección, que
  solo se ve con F-053, y su botón. **Destino: bloque 14** (T37), como ya
  dice el §6 del informe.
- Siguen abiertos, como estaban:
  - **O12-1 a O12-4**;
  - **O11-2** (opcional), **O11-3** y **O11-4** (V1/V2);
  - **O10-1**, **H16-3 a H16-6**, **O17-2**, **O9-2 a O9-4** y **O9-7**:
    van al spec-author, en el bloque 14;
  - **O10-5**, **O9-1**, **O9-5** y **O9-6**: van a V1/V2;
  - **O16-4**, que es opcional.

### Automejora (propuesta, no aplicada)

**`reviewer.md` y la plantilla del implementer: un test que afirma «X no
cambia Y» tiene que demostrar que Y no está vacío.**

Pasó aquí: «los distintos no cambian propuestas, grupos ni avisos» compara
tres listas vacías. La campaña del implementer no lo vio, porque sus 50
mutaciones atacan lo que **añade** el bloque, y ninguna lo que el bloque
podría **romper** del resto.

La propuesta, en dos partes:

- **En el implementer**: todo test de no interferencia lleva un `assert`
  de que lo que dice preservar **no está vacío** en su fixture.
- **En el reviewer**: en las mutaciones a mano, una familia fija de **no
  interferencia**. Son mutaciones que hacen que lo nuevo borre o esconda lo
  que ya existía cuando lo nuevo está presente (`viejo: nuevo.length ? [] :
  viejo`).

Vale para cualquier proyecto, así que va también a `arnes-base`.

## Re-review del bloque 13 · cierre de R13-1 · 2026-10-06

> reviewer. Alcance **cerrado** a `git diff d62d420..HEAD`: `897416f` (R13-1,
> solo `services/postventa-front/tests_js/f035_paginas.test.js`) y `d82e7a2`
> (informe y `current.md`). Solo compruebo que el cambio requerido 1 de la
> «Review del bloque 13» queda cerrado. No abro familias ni variantes nuevas:
> lo que se ve fuera va como informativo.

### Veredicto

**APPROVED** (bloque 13). El cambio requerido 1 queda cerrado: K1, K12 y K13
caen con el test nuevo y sobreviven con el viejo, y el código de producción no
tiene diff.

### Las preguntas del líder

1. **¿K1, K12 y K13, cada una sola y en copia desechable, caen en rojo con el
   test nuevo?** **Sí, las tres.** Las apliqué con mi propio guion: copia
   entera del front en el scratchpad, la cadena original tiene que aparecer
   **una** vez en `js/oficios.js`, y cada mutación se corre sola y contra los
   dos ficheros de test, el de HEAD y el de `d62d420`.

   | Mutación | Test de HEAD | Test de `d62d420` (el vacuo) |
   |---|---|---|
   | ninguna (control) | 677/677 | 677/677 |
   | K1 · `distintos = [] si hay propuestas, grupos o avisos` | **1 fallo**: «el par del aviso, en distintos» | 677/677 (sobrevive) |
   | K12 · `avisos: distintos.length ? [] : avisos` | **1 fallo**: `avisos` | 677/677 (sobrevive) |
   | K13 · `grupos: distintos.length ? [] : grupos` | **1 fallo**: `grupos` | 677/677 (sobrevive) |

   Las tres caen en «f035 R75: los distintos no cambian propuestas, grupos ni
   avisos», cada una por su aserción. Coincide con la salida del §2 del
   informe del implementer. Las copias se borraron tras cada corrida, y
   `git status` quedó limpio.

2. **¿El test compara listas no vacías y puede fallar?** **Sí.**
   - La fixture nueva, `propuestasDeUnaObraConTodo`, trae una propuesta
     (`9003`·`9004`), un grupo vigente de dos códigos (`9001`·`9002`), un
     aviso (`9005`·`9006`·`9007`) y, si se le pasa, `distintos` con el par del
     aviso **al revés** (`9007`·`9005`). Es el caso real que pedía la review.
   - El test afirma con `assert` explícitos que lo que preserva **no está
     vacío**: una propuesta, el grupo `[9001, 9002]`, el aviso y seis grupos
     vigentes.
   - Después compara `obra`, `propuestas`, `grupos`, `avisos` y
     `gruposVigentes` con y sin `distintos`. También comprueba que
     `distintos` trae el par ordenado con sus nombres y que `sinNada` es
     `false`.
   - Que puede fallar lo demuestra la tabla anterior.

3. **¿La suite JS y la del front están en verde sobre el código real?**
   **Sí.**
   - `node --test "tests_js/*.test.js"`: **677/677**. Es el mismo número que
     antes, porque se reescribió el test vacuo y no se añadió uno nuevo; la
     review admitía las dos cosas.
   - `python -m pytest -q` en `services/postventa-front`: **729 passed**.
     Lo lancé directamente, porque `init.sh` lo sirvió de caché.
   - `bash harness/init.sh`, tal cual: **ENTORNO LISTO**. Raíz: 114 passed.
     `api` y `front`, de caché. `PUERTA COBERTURA: N/A (F-035 no cambia
     líneas Python de producción frente a dev)`. ruff: 71 avisos, que son
     deuda previa.

4. **¿`git diff d62d420 HEAD -- services/postventa-front/js/
   services/postventa-front/oficios.html` está vacío?** **Sí, vacío.**
   También lo están `tests_js/oficios.test.js` y `services/postventa-api`.
   El diff de `services/` es solo `f035_paginas.test.js` (+56, −2).

5. **Los opcionales que no se hicieron: ¿hacen falta?** **No. Quedan como
   informativos para el bloque 14, sin bloquear nada.**
   - **El test del componente con la misma respuesta.** Lo que K1, K12 y K13
     podían romper vive en `presentarPropuestas`, que es pura, y el test
     reescrito ya lo fija. En `oficios.html` cada sección tiene su propio
     `x-show` sobre su lista: lo que se pinta depende de la vista, y la vista
     ya está probada con todo junto. Pasar el test del botón a esa respuesta
     solo añadiría «el botón funciona en una pantalla llena». Sería otra
     variante, y el líder pidió no abrirlas.
     - **Destino**: el bloque 14, opcional; o el vistazo V4 g, cuando F-053
       esté desplegada.
   - **O13-1** (la guardia de R75 no ve `inert` ni `pointer-events-none`).
     Sigue como estaba: es la familia O12-1, marcado que nadie escribiría.
     - **Destino**: el bloque 14, opcional, junto con O12-1.

### Checkpoints (acotados al diff)

- **C1** [x] `init.sh` termina con exit 0 (lo ejecuté yo, sobre HEAD).
- **C2**
  - [x] Una sola feature `in_progress` (F-035), en la rama
    `feature/F-035-portal-posventa`.
  - [x] `current.md` lleva la entrada de R13-1 arriba.
  - [x] Ninguna feature pasa a `done`.
- **C3**
  - [x] El fichero de test tocado lleva su ruta en la primera línea.
  - [x] Las líneas añadidas no traen `console.*`, `debugger`, `TODO`,
    `FIXME` ni secretos.
  - [x] Comentarios en español.
  - [x] No se añade ningún fichero.
  - Arquitectura hexagonal: **N/A justificado**. El diff es un único test JS
    y no toca código de producción.
- **C3 bis** — **N/A**: el diff no toca `docs/referencia/`.
- **C4**
  - [x] R75, «con distintos, el resto de la pantalla sale como antes», queda
    cubierto por «f035 R75: los distintos no cambian propuestas, grupos ni
    avisos», que ya no es vacuo. Era el `[ ]` de la review del bloque 13.
  - [x] Todos los tests pasan, sin red ni BBDD.
- **C4 bis** [x] `rigor: "estandar"`.
  - [x] **Fase RED**: el informe trae la salida real de K1, K12 y K13, que
    sobreviven con el test viejo y caen con el nuevo. La reproduje.
  - [x] **Cobertura**: N/A, con el motivo impreso por `init.sh`.
  - [x] **Mutación de la herramienta**: 0 mutantes, coherente porque no hay
    Python de producción. El control del cero ya se hizo en la review del
    bloque 13, y este diff no cambia nada que lo afecte.
  - [x] **Mutantes a mano**: los 3 supervivientes de la review están
    muertos.
  - [x] «Evidencias» con los cuatro números.
  - [x] La regla 7 es **N/A**, como en la review: el rigor no es `critico`
    y no hay una puerta nueva.
- **C4 ter** — **N/A**: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] Los commits son `F-035 R13-1: …`.
  - [x] El árbol está limpio y no quedan copias ni worktrees míos.
  - [x] `features.json` dice `in_progress`, que es lo real: siguen abiertos
    los bloques 14 y 15.

### Informativo (no bloquea)

- Siguen abiertos, con el destino que tenían:
  - **O13-1**, **O13-2** (contrato de F-053) y **O13-3** (README, bloque 14);
  - el resto de la lista de la review del bloque 13.
- La **automejora** de la review del bloque 13 sigue pendiente de que la
  apruebe el humano: los tests de no interferencia tienen que afirmar que lo
  que preservan no está vacío, y el reviewer tiene que añadir una familia
  fija de mutaciones de no interferencia. Este arreglo la aplica ya en el
  test que la originó, pero no está en `reviewer.md` ni en `arnes-base`.
