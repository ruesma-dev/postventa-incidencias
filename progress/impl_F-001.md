<!-- progress/impl_F-001.md -->
# F-001 · Esqueleto del monorepo y /health — informe de implementación

Rama: `feature/F-001-esqueleto`. Fecha: 2026-08-18.
Implementado sin subagentes: la sesión arrancó con
`CLAUDE_CODE_CHILD_SESSION=1` y los agentes del arnés se instalaron en esta
misma sesión, por lo que aún no estaban cargados.

## Qué se ha creado

### Declaración del monorepo

- `harness/servicios.json` — declara `api` (`services/postventa-api`, python,
  venv propio) y `front` (`services/postventa-front`, lenguaje `otro`). Sin
  este fichero el portero trataría el repositorio como un solo proyecto y no
  validaría los servicios por separado.

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
- `tests/conftest.py` y `tests/test_health.py` — 4 tests.

### `services/postventa-front` (estático)

- `index.html` — Tailwind y Alpine por CDN. De momento solo pinta el estado
  del backend.
- `js/config.js`, `js/app.js`, `css/styles.css`.
- `dev_server.py` — copiado de `front-nominas` y adaptado: puerto de API 7073
  (el 7072 lo ocupa la Function de nóminas) y nombres del proyecto.
- `staticwebapp.config.json` — auth de Entra y rutas. **El `openIdIssuer`
  lleva `<TENANT_ID>` como marcador**: `front-nominas` tiene el ID de tenant
  real en claro y `CLAUDE.md` lo prohíbe. Se sustituye al desplegar (F-010).

### Raíz

- `tests/test_servicios_declarados.py` — 3 tests que comprueban que la
  declaración de servicios describe la realidad: que cada ruta declarada
  existe, que ningún servicio en disco se queda sin declarar y que el venv
  declarado está. Una declaración que miente deja zonas sin comprobar
  mientras el portero imprime que todo va bien.
- `requirements-dev.txt` — pytest, ruff, coverage y pymupdf (esta última hará
  falta para el troceado de F-002; se instaló para poder leer las muestras).
- `.gitignore` — añadidos `**/.venv/`, `local.settings.json`, `.pytest_cache/`,
  `.ruff_cache/` y `.coverage`.

## Verificación (resultados reales, no «debería funcionar»)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**, con las dos suites en verde |
| Suite de la raíz | 3 passed |
| Suite de `api` | 4 passed |
| `ruff check services/` | All checks passed |
| Import de `function_app` | OK, función `health` registrada |
| `func start --port 7073` + `curl /api/health` | **HTTP 200** con `{"servicio":"postventa-api","version":"0.1.0","entorno":"local","estado":"ok"}` |
| `dev_server.py` + `curl :5173/api/health` | **HTTP 200**, el proxy reenvía bien |
| Página en Chrome | Semáforo verde, «Servicio disponible (entorno local)» y `postventa-api 0.1.0` |

## Dos cosas que se arreglaron durante la verificación

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

## Lo que queda fuera y hay que saber

- **Nadie comprueba el front**: está declarado como lenguaje `otro` sin
  `comando_tests`, y el portero lo avisa en cada arranque. Tiene sentido
  resolverlo en F-007, cuando el front tenga lógica que merezca pruebas.
- Los 11 avisos de `ruff` que quedan son de `harness/*.py`, código del arnés
  genérico. Tocarlos aquí obligaría a propagarlos a `arnes-base` y no son de
  esta feature.
- No se ha desplegado nada: eso es F-010.
