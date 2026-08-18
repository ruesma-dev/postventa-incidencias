<!-- progress/impl_F-001.md -->
# F-001 · Esqueleto del monorepo y /health — informe de implementación

Rama: `feature/F-001-esqueleto`. Fecha: 2026-08-18.
Implementado sin subagentes: la sesión arrancó con
`CLAUDE_CODE_CHILD_SESSION=1` y los agentes del arnés se instalaron en esta
misma sesión, por lo que aún no estaban cargados.

## Qué se ha creado

### Declaración del monorepo

- `harness/servicios.json` — declara `api` (`services/postventa-api`, python,
  venv propio). Sin este fichero el portero trataría el repositorio como un
  solo proyecto y no validaría los servicios por separado. El front **no** se
  declara todavía: entra en F-007.

### `services/postventa-api` (Function App, Python v2)

- `function_app.py` — adaptador de Azure: registra `GET /api/health` y
  traduce a `HttpResponse`. No tiene lógica.
- `interface_adapters/api/health.py` — el handler real, sin `azure.functions`
  dentro, para poder probarlo sin levantar el runtime.
- `config/settings.py` — pydantic-settings. **`ENTORNO` es obligatoria a
  propósito**: un valor por defecto haría que un despliegue mal configurado
  arrancase diciendo que es «local». `NOMBRE_SERVICIO` y `VERSION_SERVICIO`
  viven aquí.
- `config/logging_config.py` — fija el nivel de log raíz. No añade handlers:
  en Functions, el runtime ya tiene el suyo y se duplicarían las líneas en
  Application Insights.
- Paquetes vacíos de `domain/` (con `models/` y `ports/`), `application/`
  (con `pipelines/` y `services/`) e `infrastructure/`: la forma hexagonal
  desde el primer commit, para que nadie improvise otra después.
- `requirements.txt`, `requirements-dev.txt`, `host.json`, `.funcignore`,
  `local.settings.json.example`, `.env.example`.
- `tests/conftest.py`, `tests/test_health.py` y
  `tests/test_f001_adaptador_http.py` — 7 tests con nombre trazable
  (`test_f001_rN_*`, donde N es el criterio de aceptación que cubren).

### `services/postventa-front` — SACADO de F-001, va a F-007

Se llegó a escribir y a verificar entero (ver más abajo), pero **ya no forma
parte de esta feature**: sus 114 líneas de `dev_server.py` —un servidor de
desarrollo copiado de `front-nominas`, que no se despliega— hundían la puerta
de cobertura al 26 % sin proteger nada que vaya a producción.

Decisión del humano: sacar el front de F-001. El trabajo **no se ha perdido**:
está íntegro en la rama `feature/F-007-front`, y F-007 lo recupera con
`git checkout feature/F-007-front -- services/postventa-front`.

Lo que ya se sabe y F-007 no tiene que volver a descubrir:

- **Alpine y el orden de los scripts**: los scripts propios van sin `defer` al
  final del `body`; con `defer`, cuando Alpine arranca el documento ya está en
  `interactive` y no encuentra la función del `x-data`.
- **Alpine con versión fija** (`3.14.1`), no `3.x.x`: un cambio del CDN no
  debe poder romper el front.
- **`staticwebapp.config.json` con `<TENANT_ID>` como marcador**:
  `front-nominas` tiene el ID de tenant real en claro y `CLAUDE.md` lo
  prohíbe.
- El `dev_server.py` proxea `/api/*` al puerto **7073** (el 7072 lo ocupa la
  Function de nóminas).

### Raíz

- `tests/test_servicios_declarados.py` — 3 tests que comprueban que la
  declaración de servicios describe la realidad: que cada ruta declarada
  existe, que ningún servicio en disco se queda sin declarar y que el venv
  declarado está. Una declaración que miente deja zonas sin comprobar
  mientras el portero imprime que todo va bien.
- `requirements-dev.txt` — pytest, ruff, coverage y pymupdf (esta última hará
  falta para el troceado de F-002; se instaló para poder leer las muestras).
- `.gitignore` — añadidos `**/.venv/`, `local.settings.json`, `.pytest_cache/`,
  `.ruff_cache/`, `.coverage`, `coverage.json` y `services/*/coverage.json`.

## Evidencias

| Número | Valor |
|---|---|
| **Tests** | 10 en verde (3 en la raíz, 7 en el servicio `api`), 0 fallos |
| **Tiempo de las suites** | 0,03 s la de la raíz y 0,21 s la del servicio (0,24 s en total). Tan bajo porque ningún test toca red, BBDD ni el runtime de Functions |
| **Cobertura de las líneas de la feature** | **100 %** (40/40), umbral 80 % |
| **Mutación** | 3 mutantes: **2 muertos, 1 superviviente** (equivalente, analizado en `progress/mutacion_F-001.md`) |
| **Portero** | `bash harness/init.sh` → **ENTORNO LISTO**, exit 0 |

## Verificación (resultados reales, no «debería funcionar»)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO** |
| Suite de la raíz / suite de `api` | 3 passed / 7 passed |
| `ruff check services/ tests/` | All checks passed (tras corregir un `I001` que introdujo el test nuevo) |
| Puerta de cobertura | 100.0 % de 40 líneas (40/40) |
| Campaña de mutación | 2 muertos, 1 superviviente equivalente |
| Import de `function_app` | OK, función `health` registrada |
| `func start --port 7073` + `curl /api/health` | **HTTP 200** con `{"servicio":"postventa-api","version":"0.1.0","entorno":"local","estado":"ok"}` |
| `dev_server.py` + `curl :5173/api/health` (front, antes de sacarlo) | **HTTP 200**, el proxy reenvía bien |
| Página en Chrome (front, antes de sacarlo) | Semáforo verde, «Servicio disponible (entorno local)» y `postventa-api 0.1.0` |

## Fase RED: NO se hizo — excepción declarada

El nivel `estandar` exige fase RED, y **esta feature no la tuvo**: el código
se escribió antes que los tests. Al detectarlo el reviewer, se intentó cubrir
el criterio que faltaba (`/api/health` devuelve 200) escribiendo primero el
test, con la hipótesis de que fallaría por un efecto colateral al importar
`function_app`; **pasó a la primera**, porque el código ya existía.

No se ha fabricado una traza roja retroactiva. Falsificar la evidencia
precisamente en el sitio donde el arnés existe para impedirlo sería peor que
el incumplimiento. El humano aprobó cerrar F-001 con esta excepción anotada,
por ser la feature de calentamiento y estar ya verificada de punta a punta.

**Compromiso para F-002 en adelante: se empieza por los tests**, y la traza en
rojo se pega en el informe de implementación.

## Cosas que se arreglaron durante la verificación y la review

1. **`func` cogía el Python global** en lugar del venv del servicio, y la
   Function no cargaba (`ModuleNotFoundError: pydantic`). Se arranca con
   `VIRTUAL_ENV` apuntando al venv del servicio.
2. **Alpine no encontraba `appPostventa`.** Con los scripts propios en
   `defer`, cuando Alpine se ejecuta el documento ya está en `interactive` y
   arranca antes de que se defina la función. Corregido como en
   `front-nominas`: los scripts propios van **sin `defer` al final del
   `body`**, y Alpine con `defer` y **versión fija** (`3.14.1` en vez de
   `3.x.x`, para que un cambio del CDN no pueda romper el front).
   Detectado con la consola del navegador, no adivinando.
3. **Nada estaba commiteado.** Lo detectó el reviewer: sin commits, las tres
   puertas del nivel `estandar` medían un diff vacío y se autodeclaraban N/A.
   El portero imprimía «ENTORNO LISTO» sobre una feature que formalmente no
   existía. Con la feature commiteada, la puerta de cobertura pasó de un `N/A`
   falso a un KO real del 0 %.
4. **El venv del servicio no tenía `coverage`**, así que el arnés nunca
   escribía `services/postventa-api/coverage.json` y la cobertura del servicio
   no contaba para nada. Añadido a su `requirements-dev.txt`.
5. **Faltaba el test del criterio principal**: que `GET /api/health` devuelve
   **200** solo se había comprobado con `curl` a mano. Ahora lo cubre
   `test_f001_r1_health_devuelve_200`.

## Lo que queda fuera y hay que saber

- **El front entero queda para F-007**, guardado en la rama
  `feature/F-007-front`. Allí habrá que decidir cómo se cubre el
  `dev_server.py`: hoy el arnés **no tiene mecanismo de exclusión**
  configurable para scripts de desarrollo (`harness/alcance.py` excluye solo
  `tests`, `specs`, `progress` y `docs`, por constante en el código). Si se
  decide excluir `scripts/`, es un cambio del arnés y hay que portarlo a
  `arnes-base`.
- Los avisos de `ruff` que quedan son de `harness/*.py`, código del arnés
  genérico. Tocarlos aquí obligaría a propagarlos a `arnes-base` y no son de
  esta feature.
- **Los originales `.docx` y `.pdf` siguen en `docs/referencia/`.** No están
  en git ni lo han estado nunca (verificado con `git log --diff-filter=A`),
  pero C3 bis pide que tampoco estén en el árbol de trabajo. Es deuda del
  trabajo de definición, anterior a esta rama.
- No se ha desplegado nada: eso es F-010.
