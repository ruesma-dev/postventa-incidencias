<!-- specs/F-035-portal-posventa/design.md -->
# F-035 · Diseño del portal de posventa · Diseño técnico

> Diseñado contra `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
> `docs/DESPLIEGUE.md`, `azure-apps/sigrid_tablas.md`, `azure-apps/portal.md`
> y `docs/referencia/03_modelo_posventa_sigrid.md`. Todas las referencias de
> línea están medidas sobre `dev` en `5bc0ca8`.

> **Puesta al día del 2026-09-25 (rebase sobre `dev` en `54c0884`).** Se
> añaden dos fuentes: `docs/referencia/04_alta_incidencia_sigrid.md` (el alta
> manual de Posventa, llegada el 2026-09-24) y `azure-apps/sigrid_api.md`
> §8.9 (`sigrid/partes-reclamacion`, el contrato del volcado de F-040), más la
> estructura de archivo de Posventa que dejaron desplegada F-013 y F-049
> (`docs/INTEGRACION.md` §3). Re-medido sobre `54c0884`: el front,
> `infra/desplegar_front.ps1` y los tests de la raíz no han cambiado desde
> `5bc0ca8`, así que §1 y sus líneas siguen valiendo; la fila de Entra ID de
> `docs/ARCHITECTURE.md` ha bajado de `:544` a **`:578`** (F-013 añadió
> enmiendas encima). Lo que cambia va en recuadros con esta fecha: §5.2,
> §5.3, §5.5, §5.6, §5.7, §6.3, §7, §8.1, §10, §11, §13 (D-10 nueva) y §14.

> **Decisiones del humano del 2026-09-25 (acta en §13).** El humano ha
> respondido D-1…D-10. Tres respuestas **cambian la premisa** del diseño y
> van en recuadros con el rótulo «Decisión del 2026-09-25», que citan lo que
> había sin borrarlo:
>
> - **D-1** («pagina aparte. esto que hemos hecho sera una pestaña de dicho
>   portal»): el portal es la página; el circuito **deja de ser una página
>   ajena enlazada** y pasa a ser la pestaña `partes` del portal.
> - **D-2** («barra superior»): una **barra superior común**, en el portal y
>   en el circuito.
> - **D-3** («si»): **la portada `/` pasa a ser el portal**. Revierte la
>   recomendación anterior. Diseño elegido, medido en §2: el circuito se
>   **muda de fichero**, de `index.html` a `partes.html`, sin tocar ni una
>   línea de su lógica, de `staticwebapp.config.json` ni de `dev_server.py`;
>   el portal ocupa `index.html` (donde decía `portal.html`).
>
> Recuadros de esta ronda: cabecera, §1.2, §1.3, §2, §3, §4, §5.1, §5.5,
> §5.7, §6.3, §8.1, §9, §11, §12, §13 y §14. **Regla de lectura**: en todo lo
> anterior a esta ronda, **`portal.html` se lee `index.html`** (el portal) y
> **el `index.html` del circuito se lee `partes.html`**, salvo donde un
> recuadro diga otra cosa.

> **Segunda ronda del humano · 2026-09-25, tras ver la maqueta (acta en
> §13.1, «Segunda ronda»).** Sobre `6bc4b6c` (review 2 APROBADA, sin mergear,
> V1/V2 pendientes). Dos decisiones:
>
> - **Navegación**: «en la misma ventana como en una web normal (para la
>   maqueta vale así)». **La maqueta no cambia** (D-2 sigue); entra la regla
>   para cuando las secciones sean reales (R48, recuadro de §2).
> - **Estilo**: «como el de portal ruesma (ohana.ruesma.es) […] muy bonito y
>   elegante», y «También el circuito entero». Todo el diseño está en la
>   **§15 nueva**: tokens compartidos en `css/styles.css`, logotipo copiado de
>   `front-portal`, sección a sección, accesibilidad y, para el circuito en
>   producción, una guardia que **solo deja cambiar clases** (R59).
>
> Recuadros de esta ronda: esta cabecera, §2, §3, §6.1, §11, §12, §13.1 y
> §14; y la §15 entera. Referencia medida, **solo lectura**:
> `C:\Users\pgris\PycharmProjects\front-portal\public` (`index.html`,
> `assets/css/styles.css`, `assets/img/`), commit `01fb1aa` de ese
> repositorio.

> **Enmienda del 2026-10-05 · el portal en producción tras F-036 (opción
> b).** Sobre `2a86bca` (merge de `dev` con F-036 en la rama). Todo el diseño
> está en la **§16 nueva**: dónde viven importar, bandeja y oficios (páginas
> propias con la barra común, §16.2), la regla de navegación («solo el
> circuito abre aparte», §16.3), el estado de cada sección y el rótulo «En
> construcción» (§16.4), los dos apuntes de la ficha y el **límite de
> servicio** que los afecta (§16.6: ninguno es solo front), qué guardias
> cambian y por qué (§16.9), la publicación con la parada del humano
> (§16.12) y las decisiones abiertas **D-11 a D-14** (§16.13). Recuadros de
> esta ronda fuera de §16: esta cabecera, §7.3 y §13. Regla de lectura: lo que
> el usuario ve como «maqueta» pasa a llamarse **«en construcción»**.

## 1 · Lo que hay hoy, medido

### 1.1 · El front

`services/postventa-front/` es un front estático sin cadena de build: HTML +
Tailwind por CDN + Alpine 3.14.1 + `dev_server.py` (biblioteca estándar), patrón
`front-nominas`.

| Pieza | Qué es | Dato |
|---|---|---|
| `index.html` | La **única** página: el circuito de partes firmados | 617 líneas; un solo componente Alpine en la raíz, `x-data="appPostventa()"` (`:16`); cabecera `:18-35`; nueve scripts propios al final del `<body>` (`:607-615`) |
| `js/app.js` | Pegamento de Alpine, **sin tests a propósito** | 973 líneas; `function appPostventa()` (`:21`) |
| `js/{config,traza,cola,api,seleccion,pipeline,confirmacion,autoguardado}.js` | Lógica probada, expuesta como `window.X` y `module.exports` | 8 módulos |
| `css/styles.css` | 11 líneas | compartido con nada más |
| `tests/` | 15 ficheros de pytest + `conftest.py` (guardia de red de sesión) | ~256 tests |
| `tests_js/` | 15 ficheros de `node --test`, lanzados por el puente `tests/test_f007_js.py` | 322 tests |

El servicio `front` está declarado en `harness/servicios.json` con lenguaje
`python`, así que `bash harness/init.sh` ejecuta su pytest (y con él los tests
de JavaScript). **La puerta de cobertura y la campaña de mutación solo miden
Python** (`harness/alcance.py`): un cambio de HTML o JavaScript no entra en su
alcance.

### 1.2 · Por qué la maqueta no puede vivir dentro de `index.html`

La suite del circuito protege la pantalla con **aserciones negativas sobre el
texto entero de `index.html`**. Son la defensa de decisiones cerradas —la
pantalla previa del dry-run retirada por F-025, los datos personales fuera de
la pantalla, la confirmación única— y una maqueta de todo el ciclo las pisa
por fuerza:

| Test | Qué prohíbe en **todo** `index.html` | Qué de la maqueta lo pisaría |
|---|---|---|
| `test_f009_front.py:73-107` | `descripcion`, `login_sigrid`, `estado_origen.codigo`… | el binding de la descripción de una incidencia (`inc.descripcion`) |
| `test_f025_front.py:587-594` (R46) | `dni`, `observaciones`, `usuario.correo`, `usuario_oid`, `nombre_cliente` | la ficha de incidencia y el correo de «no procede» |
| `test_f025_front.py:427-430`, `test_f009_front.py:193-197` | `Ver qué pasaría`, `no cierra nada` | el dry-run del volcado (F-040) y del cambio de estado (F-041) |
| `test_f012_front.py:244-253` | `PARTE FIRMADO.pdf`, `Cerrar las incidencias` | la impresión y las operaciones en bloque |
| `test_f025_front.py:365-368` | `pedirConfirmacionArchivo()` y `confirmarArchivo()` **una sola vez** | cualquier confirmación de la maqueta que reutilice el patrón |
| `test_f026_autoguardado.py:222-224` | `obsolet` | textos de la bandeja |
| `test_f007_estaticos.py:43-56, 285-289` | que los scripts propios sean **exactamente** los nueve del circuito | cualquier script de la maqueta |

Meter la maqueta en `index.html` obligaría a **reescribir o acotar** esas
aserciones, y R32 lo prohíbe: son la memoria de por qué el circuito es como
es. De ahí la página aparte (§2).

> **Decisión del 2026-09-25 (D-3) · medido de nuevo.** §2 decía que mover
> el circuito «toca el `INDEX` de nueve ficheros de test». Medido sobre
> `fb356a4` (`grep` en `tests/` y `tests_js/`): **nueve** ficheros nombran
> `index.html`, pero solo **siete** lo fijan como el circuito, con una única
> línea `INDEX = RAIZ_FRONT / "index.html"`:
>
> | Fichero | Línea | Qué hace con `index.html` | ¿Cambia con la mudanza? |
> |---|---|---|---|
> | `test_f007_estaticos.py` | `:36` | Constante `INDEX`: contrato de carga, los nueve scripts, sin almacenamiento | Sí, esa línea |
> | `test_f009_front.py` | `:44` | Constante `INDEX` | Sí, esa línea |
> | `test_f012_front.py` | `:46` | Constante `INDEX` | Sí, esa línea |
> | `test_f025_front.py` | `:47` | Constante `INDEX` | Sí, esa línea |
> | `test_f026_autoguardado.py` | `:33` | Constante `INDEX` | Sí, esa línea |
> | `test_f026_front.py` | `:55` | Constante `INDEX` | Sí, esa línea |
> | `test_f028_front.py` | `:47` | Constante `INDEX` | Sí, esa línea |
> | `test_f007_dev_server.py` | `:181-472`, `:530` | Que `dev_server.py` **exige un `index.html`** en su raíz para arrancar, con raíces temporales propias | **No**: el portal es el nuevo `index.html` y la exigencia se sigue cumpliendo |
> | `test_f031_front.py` | `:174` | Solo en el texto de un mensaje de error; lee `js/app.js` | **No** |
> | `tests_js/reintento_vaciado.test.js` | `:47` | Solo en un comentario | **No** |
>
> Y la tabla de arriba se da **la vuelta a favor**: las aserciones negativas
> leen `INDEX`, así que al cambiar esa constante **siguen al circuito** a
> `partes.html` y siguen protegiéndolo igual, y el portal —ahora en
> `index.html`— queda fuera de ellas sin reescribir ni acotar ni una. Es lo
> que hace posible D-3 con el menor cambio (§2, recuadro).

### 1.3 · Acceso y despliegue

- `staticwebapp.config.json` exige `authenticated` en `/*` y no tiene
  `navigationFallback`: **cualquier** página nueva del front queda protegida
  igual que `index.html`, sin tocar el fichero, y las rutas por hash (`#/…`)
  no necesitan reescritura de rutas en el servidor.
- `infra/desplegar_front.ps1:502-507` sube **la carpeta entera** del front
  menos `tests`, `tests_js`, `__pycache__`, `dev_server.py`, `dev_front.ps1` y
  `coverage.json`. Consecuencia: **el siguiente despliegue del front publica la
  maqueta**, se quiera o no. Es la decisión **D-4**.
- `dev_server.py` sirve cualquier estático de la carpeta: `portal.html` se abre
  en local sin tocarlo.

> **Decisión del 2026-09-25 (D-3) · lo que se mide para mover la portada.**
>
> - **Quién sirve `/`**: en Azure, la Static Web App sirve `index.html` como
>   documento por defecto; en local, `dev_server.py` hereda
>   `SimpleHTTPRequestHandler` (`do_GET`, `:59-63`) y hace lo mismo. **Poner
>   el portal en `index.html` basta para que `/` sea el portal en los dos
>   sitios**, sin tocar ninguno.
> - `dev_server.py:164-167` **se niega a arrancar sin `index.html`**: con el
>   portal ahí, sigue arrancando. `dev_front.ps1:69` anuncia
>   `http://localhost:$Puerto/`, que pasa a abrir el portal: correcto.
> - **Acceso**: `staticwebapp.config.json` protege `/*` con `authenticated`,
>   así que `/`, `/index.html` y `/partes.html` quedan igual de protegidos
>   **sin tocar el fichero**. El `401` redirige a `/.auth/login/aad` sin
>   `post_login_redirect_uri`: quien abra `/partes.html` sin sesión puede
>   volver del inicio de sesión a la portada en vez de al circuito (riesgo
>   de §12, se mira en V4).
> - **`globalHeaders` lleva `X-Frame-Options: DENY`**: el navegador se niega
>   a pintar cualquier página del front dentro de un `<iframe>`, **incluso
>   del mismo origen**. Incrustar el circuito en el portal con un marco
>   obligaría a relajar esa cabecera (§2, alternativa descartada).
> - **Despliegue**: `infra/desplegar_front.ps1:502-507` sube la carpeta
>   entera; no nombra `index.html` ni comprueba su contenido. `partes.html`
>   se publica sin tocar `infra/`.
> - **El circuito no depende de su nombre de fichero**: ni `js/app.js` ni
>   los otros ocho módulos usan `location`, `window.open`, `href` ni la
>   cadena `index.html` (medido con `grep` sobre `js/*.js`); los estáticos
>   se cargan con rutas relativas (`js/…`, `css/…`) que valen igual desde
>   `partes.html`, en la misma carpeta; y el backend está en `/api/*` del
>   mismo origen.
> - **La tarjeta del portal corporativo ya existe**: medido en
>   `front-portal/public/assets/js/catalog.js` (solo lectura; ni el host ni
>   el GUID se copian aquí), la entrada `postventa-incidencias` apunta a la
>   **raíz** de la Static Web App, sin ruta, con `requiredGroupName:
>   'posventa-usuarios'`. Con D-3, **la tarjeta aterriza en el portal**, que
>   es lo que se quiere, **sin tocar `front-portal`**. Su título («Partes de
>   Posventa») y su descripción (habla solo de leer y archivar partes) dejan
>   de describir lo que abre: se propone al humano (§9, H-4), no se toca.

## 2 · La decisión: una página aparte con rutas por hash

**`portal.html` es una aplicación Alpine de una sola página** con un componente
`portalPosventa()` y rutas por hash (`#/bandeja`, `#/incidencias/EJ-0003`…).
El circuito sigue siendo `index.html`, intacto salvo un bloque de navegación en
su cabecera.

| | Alternativa | Por qué no |
|---|---|---|
| **A** | Secciones dentro de `index.html`, con `x-show` por sección | Choca con las siete familias de aserciones de §1.2; habría que reescribirlas o acotarlas a una zona, y R32 lo prohíbe |
| **B** | Una página HTML por sección (`bandeja.html`, `incidencias.html`…) | Cada cambio de sección recarga: la selección de R20 se pierde, la cabecera y la navegación se duplican en ocho ficheros, y no aporta nada frente a una sola página con hash |
| **C** | Reescribir el circuito como una sección más del portal | Es justo lo que la ficha prohíbe («integrado, no reescrito»): 973 líneas de pegamento y 578 tests del circuito en juego para una maqueta |
| **D** | Un framework con enrutador (Vue, React…) | Cadena de build nueva en un front que presume de no tenerla (`README.md`), y dependencias no previstas (C3) |

**Por qué rutas por hash y no por ruta**: no necesitan `navigationFallback` en
la Static Web App (§1.3), recargar la página deja al usuario en la misma
sección, y se pueden enlazar desde `index.html` y desde un correo a Posventa.

**Cómo convive con el circuito** (R30, R31):

- En `index.html` se añade un `<nav>` estático dentro del `<header>` (después
  de la línea `:34`, antes de `</header>` en `:35`). Cada sección es un enlace
  a `portal.html#/<id>` que se abre **en una pestaña nueva**: el circuito
  guarda la remesa en curso en memoria, y salir de la página en la misma
  pestaña la perdería. «Partes firmados» aparece como la página actual, sin
  enlace. El bloque es HTML plano: **ningún script nuevo** en `index.html`,
  así que `ORDEN_CANONICO` y el test de los nueve scripts no cambian.
- En `portal.html`, la sección `partes` explica que el circuito ya funciona y
  enlaza a `index.html` en la **misma** pestaña (la maqueta no tiene nada que
  perder). Ahí vive también el placeholder de F-045.

La portada del dominio (`/`) sigue siendo el circuito. Convertir el portal en
portada —mover el circuito a otra página— toca el `INDEX` de nueve ficheros de
test y la URL de la tarjeta: es la decisión **D-3**, fuera de esta ficha.

> **Decisión del 2026-09-25 (D-1, D-2, D-3) · el portal es la portada y el
> circuito, su pestaña `partes`.** Lo de arriba se conserva como premisa
> original. Tres frases suyas **dejan de valer**: «`portal.html` es una
> aplicación Alpine…» (el portal se llama `index.html`), «El circuito sigue
> siendo `index.html`» (se muda a `partes.html`) y «La portada del dominio
> (`/`) sigue siendo el circuito» (el humano ha dicho «si» a D-3). Lo demás
> del apartado —una sola página con rutas por hash, las alternativas A–D, el
> porqué del hash— **sigue valiendo** para el portal.
>
> **Quién es quién desde ahora:**
>
> | Fichero | Antes (premisa) | Ahora |
> |---|---|---|
> | `services/postventa-front/index.html` | El circuito | **El portal** (lo que la premisa llamaba `portal.html`), portada `/` |
> | `services/postventa-front/partes.html` | — | **El circuito**, el mismo fichero de antes renombrado con `git mv`: su pestaña `partes` |
> | `services/postventa-front/portal.html` | La maqueta | **No existe** |
>
> **Cómo se integra el circuito como pestaña: cuatro opciones, medidas.**
>
> | | Opción | Riesgo para el circuito en producción | Veredicto |
> |---|---|---|---|
> | **E** | **El circuito sigue en su propio HTML** (`partes.html`) y la **barra superior común** lo presenta como la pestaña `partes`: el portal enlaza a `partes.html` y el circuito lleva la misma barra, en HTML plano, con `partes` marcada como la pestaña actual | Cambia **solo su URL** (`/` → `/partes.html`) y gana un bloque de HTML sin directivas. Ni un módulo JS, ni `css/styles.css`, ni `staticwebapp.config.json`, ni `dev_server.py`, ni el backend. En tests, **una línea** en cada uno de los siete ficheros de §1.2 (la constante `INDEX`), con una guardia que prueba que no cambia nada más (R32) | **Elegida** |
> | **F** | El circuito se queda en `index.html` y la portada se **reescribe** en la Static Web App (`"route": "/", "rewrite": "/portal.html"`) | Cero líneas de test, pero toca `staticwebapp.config.json`, que es **el fichero de autenticación de todo el front, `/api/*` del circuito incluido**, y que `test_f010_config_swa.py` vigila regla a regla; obliga a replicar la reescritura en `dev_server.py` (y sus tests) para que local y Azure no difieran; y **no se puede comprobar sin desplegar** que la plataforma distinga `/` de `/index.html` al aplicar la regla (si no los distingue, el circuito queda inalcanzable). El riesgo cae justo en el acceso al circuito | Descartada |
> | **G** | **Incrustar** el circuito en el portal con un `<iframe src="partes.html">` | Exige quitar o relajar `X-Frame-Options: DENY` (§1.3), una cabecera de seguridad de todo el front; y dentro de un marco cambian el alto, el arrastre de ficheros de la remesa y la impresión del navegador, que el circuito nunca ha probado así | Descartada |
> | **H** | **Incrustar** el marcado del circuito dentro del portal (una sección más) | Es la alternativa **C** de arriba: reescribir 973 líneas de pegamento y poner en juego ~578 tests del circuito. La ficha lo prohíbe («integrado, no reescrito») | Descartada |
>
> **Por qué E es la de menos riesgo.** Todo lo que ejecuta el circuito
> —sus nueve scripts, su hoja de estilos, su configuración de acceso y su
> backend— es **byte a byte** lo que hay hoy en producción; lo único que
> cambia es el nombre del fichero HTML que los carga y una barra de enlaces
> que Alpine no procesa. La alternativa F, la única que no toca tests, mueve
> el riesgo al fichero de autenticación, que es justo donde un error deja al
> circuito sin servicio. Los siete cambios de test son mecánicos, iguales, y
> una guardia (R32 enmendado) demuestra que no cambia ninguna aserción.
>
> **La barra superior (D-2), en las dos páginas.**
>
> - Es el **primer elemento visible** de la página: `<nav data-barra-portal>`
>   con la marca («Posventa · Ruesma») y las ocho pestañas de
>   `Portal.SECCIONES`, en su orden y con sus etiquetas (R44). Mismo aspecto
>   en las dos páginas (mismas clases de Tailwind, escritas enteras).
> - **En el portal** (`index.html`): las pestañas del portal son enlaces
>   `#/<id>`, la activa resaltada por Alpine; la pestaña `partes` es un
>   enlace a `partes.html` **en la misma pestaña del navegador** (la maqueta
>   no tiene nada que perder) (R46). El aviso de maqueta (R13) va **debajo**
>   de la barra.
> - **En el circuito** (`partes.html`): la barra se inserta como **primer
>   hijo del `<div x-data="appPostventa()">`**, justo después de la línea
>   `:16` y antes del `<header>` de `:18`, para que el diseño en columna de
>   ese `div` (`min-h-screen flex flex-col`) la absorba sin barra de
>   desplazamiento nueva. Es **HTML plano**: ni un atributo `x-*`, `@*` ni
>   `:*`, ni `<script>`, ni `<button>` (R45), así que Alpine la recorre sin
>   hacer nada. `partes` va como `<span aria-current="page">`, sin enlace; las
>   otras siete son `<a href="./#/<id>" target="_blank" rel="noopener">`
>   (R31 enmendado), y la barra lleva una leyenda visible: «Las demás
>   pestañas son una maqueta con datos de ejemplo y se abren aparte, para no
>   perder la remesa» (R47). La cabecera del circuito, su pie y todo lo demás
>   se quedan como están.
> - **Por qué pestaña nueva desde el circuito.** La remesa en curso vive en
>   memoria: `js/*.js` no tiene ni un `beforeunload` (medido) y el pie del
>   circuito lo dice («si la recargas, hay que volver a subir la remesa»).
>   Salir del circuito en la misma pestaña del navegador la perdería sin
>   aviso. Alternativa descartada: misma pestaña con un aviso de
>   `beforeunload` — es lógica nueva en `js/app.js`, y D-3 exige que el
>   circuito siga «exactamente igual». Si a Posventa le extraña (V3), lo
>   resuelve una ficha que toque el circuito (F-045 es la primera).
> - **`#/partes` en el portal**: no hay bloque `partes` dentro del portal (la
>   pestaña **es** el circuito), así que la ruta cae en R5 y muestra
>   `inicio`. No se añade código de redirección.
>
> **Lo que hay en el portal sobre el circuito** (sustituye a la viñeta «En
> `portal.html`, la sección `partes`…» de arriba): la tarjeta «Partes
> firmados» de `inicio` (§5.1) y la pestaña «Parte» de la ficha (§5.5)
> enlazan a `partes.html` en la misma pestaña; el placeholder de F-045 vive
> en esos dos sitios (§6.3).
>
> **Dónde aterriza cada entrada al front:**
>
> | Entrada | Antes | Ahora |
> |---|---|---|
> | Tarjeta del portal corporativo (raíz de la Static Web App, medido en §1.3) | El circuito | **El portal**, `inicio` — lo que se quiere; `front-portal` no se toca |
> | Favorito de un usuario a `/` | El circuito | El portal; el circuito, a un clic en la pestaña «Partes firmados» |
> | `http://localhost:5173/` (`dev_front.ps1`) | El circuito | El portal |
> | `/partes.html` | — | El circuito |

> **Segunda ronda del 2026-09-25 · navegación: «en la misma ventana como en
> una web normal (para la maqueta vale así)».** Lo de arriba **sigue
> valiendo para la maqueta**: dentro del portal ya se navega en la misma
> ventana (rutas `#/…` y `partes.html` sin `target`, R46), y desde el circuito
> las pestañas de maqueta siguen abriéndose aparte (R31) porque perder la
> remesa por ir a mirar una maqueta no compensa. Lo que entra es la **regla
> para después (R48)**:
>
> - Una sección es **real** cuando todas las fichas de su entrada de
>   `Portal.SECCIONES` están `done`; `inicio` (sin fichas propias) lo es cuando
>   lo son todas las demás del portal. `partes` es el circuito y no cuenta.
> - Desde que una sección es real, la barra del circuito la enlaza **sin
>   `target`**: misma ventana. Lo vigila un test de la suite de la **raíz**
>   (`tests/test_f035_placeholders_vivos.py`, que no se cachea y ya cruza la
>   maqueta con `features.json`): hoy pasa sin exigir nada (ninguna de
>   F-036…F-048 está `done`) y se pone en rojo en cuanto la última ficha de
>   una sección se cierre sin quitar su `target="_blank"`. Lleva un control
>   que demuestra que mira (una copia en memoria de `features.json` con F-048
>   `done` tiene que exigir `datos` sin `target`).
> - **Consecuencia que hereda la ficha que lo active** (no la resuelve F-035):
>   navegar desde el circuito en la misma ventana **descarga la remesa en
>   curso**, que vive en memoria (§2, «Por qué pestaña nueva desde el
>   circuito»). Esa ficha, en el mismo trabajo, decide cómo no perderla —aviso
>   al salir (`beforeunload` en `js/app.js`) o recuperar el trabajo— y lo
>   propone al humano. Se escribe como paso 4 de la retirada (§7.3, abajo) y en
>   `docs/ARCHITECTURE.md` y el `README.md` del front (R48).
>
> **§7.3, paso 4 (nuevo)**: cuando la ficha que construye una sección la deja
> real, quita el `target="_blank"` y el `rel` de esa pestaña en la barra de
> `partes.html`, y resuelve en el mismo trabajo lo de la remesa en curso.

## 3 · Ficheros

### 3.1 · A crear

| Ruta | Qué es | Papel (equivalente hexagonal) |
|---|---|---|
| `services/postventa-front/portal.html` | La maqueta: cabecera, aviso de maqueta, navegación, un `<section data-seccion>` por sección, región `aria-live` del aviso de placeholder | presentación |
| `services/postventa-front/js/maqueta_datos.js` | `window.MaquetaDatos`: los datos de ejemplo, por bloques con su ficha dueña. **Solo datos**, ni una función | datos (fixture) |
| `services/postventa-front/js/portal.js` | `window.Portal`: catálogos (`SECCIONES`, `PLACEHOLDERS`, `ESTADOS`) y funciones **puras** (rutas, filtros, formato, textos del aviso). Sin DOM, sin Alpine, sin red | lógica pura (lo que en el backend sería `domain`) |
| `services/postventa-front/js/portal_app.js` | `function portalPosventa()`: estado de Alpine y **nada más**, con la misma regla de oro que `app.js` | pegamento (interfaz) |
| `services/postventa-front/css/portal.css` | La clase `.placeholder` y poco más | presentación |
| `services/postventa-front/tests_js/portal.test.js` | Tests de `js/portal.js` y del componente de `js/portal_app.js` con dobles de red | test |
| `services/postventa-front/tests_js/maqueta_datos.test.js` | Tests de los datos de ejemplo (R23–R26) | test |
| `services/postventa-front/tests/test_f035_portal.py` | Tests estáticos de `portal.html` y de la frontera con el circuito (R1, R3, R9, R10, R13–R15, R17, R18, R30–R35) | test |
| `tests/test_f035_placeholders_vivos.py` | En la **suite de la raíz**: cruza la maqueta con `harness/features.json` (R27–R29) | test |

`tests/test_f035_placeholders_vivos.py` va en la raíz y no en el front **a
propósito**: la suite del front se salta por caché cuando su árbol no cambia
(`init.sh`, sección 7 bis), y cambiar el estado de una ficha en
`features.json` no toca ese árbol. En la raíz se ejecuta siempre.

> **Decisión del 2026-09-25 (D-3).** La primera fila de la tabla («`portal.html`
> · La maqueta») pasa a ser **`services/postventa-front/index.html`**: el
> portal, con el mismo contenido que describía esa fila más la barra
> superior de §2. Como `index.html` ya existe (hoy es el circuito), no se
> «crea» sino que **se escribe de nuevo** después de mudar el circuito
> (§3.2). `tests/test_f035_portal.py` cubre además R30, R32 y R42–R47.

### 3.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/index.html` | **Solo se añade** el bloque `<nav data-portal-nav>` en la cabecera (§2). Ni una línea borrada ni cambiada (R30) |
| `services/postventa-front/README.md` | Sección nueva «La maqueta del portal (F-035)» (R36) |
| `docs/ARCHITECTURE.md` | Sección nueva «El portal de posventa (F-035)» con el mapa de §4 y la regla de los placeholders (R37). La fila de Entra ID (`:544`; **`:578` en `54c0884`**) se corrige según la respuesta a **D-5** |
| `harness/features.json`, `BACKLOG.md` | Estado de F-035, como siempre |

> **Decisión del 2026-09-25 (D-1, D-2, D-3, D-5).** La fila de `index.html`
> («**Solo se añade** el bloque `<nav data-portal-nav>` en la cabecera») queda
> sustituida por estas; las de `README.md`, `ARCHITECTURE.md` y
> `features.json` siguen, con lo que se añade abajo:
>
> | Ruta | Qué cambia |
> |---|---|
> | `services/postventa-front/index.html` → **`services/postventa-front/partes.html`** | `git mv` (el historial sigue al circuito). En `partes.html`: la **línea 1** pasa a `<!-- services/postventa-front/partes.html -->` (convención de cabecera de `docs/CONVENTIONS.md`) y **se añade** la barra superior tras `:16` (§2). Ni una línea más cambiada ni borrada (R43) |
> | `services/postventa-front/index.html` (nuevo contenido) | El portal (§3.1, recuadro) |
> | Los siete ficheros de test de §1.2 (`test_f007_estaticos.py`, `test_f009_front.py`, `test_f012_front.py`, `test_f025_front.py`, `test_f026_autoguardado.py`, `test_f026_front.py`, `test_f028_front.py`) | **Una línea** cada uno: `INDEX = RAIZ_FRONT / "index.html"` → `INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html`. Ni el nombre de la constante, ni un docstring, ni una aserción. Van **en el mismo commit** que el `git mv`, o la suite queda en rojo entre commits (R32 enmendado) |
> | `services/postventa-front/README.md` | Además de R36: dónde vive ahora el circuito (`partes.html`) y la portada; la sección «Tres cosas del `index.html` que parecen cosméticas» se refiere ahora a `partes.html` y lo dice con una nota, sin reescribirla |
> | `docs/ARCHITECTURE.md` | Además de R37: la fila de Entra ID (`:578`) se **corrige con un recuadro** (D-5): el grupo `posventa-usuarios` existe. Sin un GUID |
> | `docs/DESPLIEGUE.md` §6 | Recuadro: la tarjeta apunta a la raíz y, desde F-035, aterriza en el portal; propuesta de título y descripción para quien lleve `front-portal` (H-4). El bloque para pegar no se reescribe |


- `js/app.js` y los otros ocho módulos del circuito (R33): la maqueta no reutiliza
  ni `Confirmacion` ni `Api`. Si una sección real los necesita, la ficha que la
  construya lo decidirá.
- Todos los tests existentes de `tests/` y `tests_js/` (R32). Ni para «ampliar»
  `ORDEN_CANONICO`: `index.html` no gana scripts.
- `css/styles.css`: los estilos de la maqueta van en `css/portal.css`, así que
  nada de lo que pinta el circuito puede cambiar por la maqueta.
- `staticwebapp.config.json` (R35), `dev_server.py`, `dev_front.ps1`,
  `infra/*`, `harness/servicios.json`.
- `services/postventa-api/` entero: ni un endpoint, ni una ruta, ni una
  variable.
- `azure-apps/` y `front-portal`: ver D-5 y D-8.

> **Decisión del 2026-09-25 (D-3).** Esta lista **no cambia** con la
> mudanza, y es lo que la hace la opción de menos riesgo: ni `js/*.js`, ni
> `css/styles.css`, ni `staticwebapp.config.json`, ni `dev_server.py`, ni
> `dev_front.ps1`, ni `infra/*`, ni `services/postventa-api/`. De los tests
> existentes, **solo** la línea `INDEX` de los siete ficheros de §1.2; de
> `tests_js/`, **nada**. `front-portal` tampoco: la tarjeta ya apunta a la
> raíz (§1.3).

> **Segunda ronda del 2026-09-25 · ficheros del estilo Ruesma.** Detalle en
> §15.4. En resumen:
>
> - **A crear**: `services/postventa-front/img/logo-ruesma.svg` e
>   `img/favicon.svg` (copias byte a byte de `front-portal`).
> - **A modificar**: `css/styles.css` (tokens y componentes compartidos; **deja
>   de estar en «No se tocan»**), `css/portal.css`, `index.html` (el portal),
>   `partes.html` (**solo** valores de `class`, cuatro `<link>` en la cabecera
>   y la barra), `README.md` del front, `docs/ARCHITECTURE.md` (R48) y dos tests
>   de F-035: `tests/test_f035_portal.py` (la guardia R59 sustituye a la de
>   `difflib`; R33 admite `css/styles.css`; tests nuevos) y
>   `tests/test_f035_placeholders_vivos.py` (R48), más `tests_js/portal.test.js`
>   (R57).
> - **Siguen sin tocarse**: `js/*.js` **todos** —los nueve del circuito y
>   también los tres de la maqueta: el estilo no necesita lógica—,
>   `staticwebapp.config.json` (medido: no lleva `Content-Security-Policy`, así
>   que Google Fonts carga sin tocarlo; y ya declara `.svg` como
>   `image/svg+xml`), `dev_server.py`, `dev_front.ps1`, `infra/*` (sube la
>   carpeta entera: `img/` se publica sola), `services/postventa-api/`, los
>   tests del circuito (§15.2) y `front-portal`, del que solo se lee.

## 4 · El mapa del portal

| Sección (`id`) | Etiqueta | Qué muestra | Fichas que la construyen |
|---|---|---|---|
| `inicio` | Inicio | El ciclo en una línea (entrada → revisión → Sigrid → gestión → parte → cierre → coste) con un contador de ejemplo por fase y enlace a cada sección | — (es la maqueta misma) |
| `entrada` | Entrada | Importar el Excel de la propiedad y el resultado de su validación; la entrada desde la web de clientes | F-036, F-037 |
| `bandeja` | Bandeja de revisión | Lo importado, antes de Sigrid: revisar, proponer industrial, aprobar, volcar | F-038, F-039, F-040, F-043 |
| `incidencias` | Incidencias | Listado de incidencias de Sigrid con filtros, selección y operaciones en bloque; y la **ficha** en `#/incidencias/<id>` | F-041, F-042, F-043, F-047 |
| `impresion` | Impresión de partes | Seleccionar partes y generar el PDF con la plantilla de posventa | F-044 |
| `partes` | Partes firmados | Enlace al circuito que ya funciona y el registro sin firma | F-045 (el circuito: F-001…F-034, ya hecho) |
| `economico` | Coste y venta | Coste por obra (capítulo de POSTV2) y vínculo incidencia-proforma-coste-venta | F-046, F-047 |
| `datos` | Datos y datamart | Qué publica cada fase en el datamart | F-048 |

La navegación es una barra horizontal bajo la cabecera, con las ocho entradas
en ese orden y la activa resaltada; en pantallas estrechas pasa a desplazarse
en horizontal. El aviso de maqueta (R13) va entre la cabecera y la navegación.

> **Decisión del 2026-09-25 (D-1, D-2).** «Una barra horizontal **bajo la
> cabecera**» y «el aviso **entre la cabecera y la navegación**» dejan de
> valer: la navegación es la **barra superior común** de §2 (recuadro), el
> primer elemento de la página, en el portal y en el circuito; el aviso de
> maqueta va **debajo** de ella y solo en el portal. Las ocho entradas, su
> orden y sus fichas no cambian. La fila `partes` cambia de sentido:
>
> | Sección (`id`) | Etiqueta | Qué muestra | Fichas que la construyen |
> |---|---|---|---|
> | `partes` | Partes firmados | **El circuito mismo** (`partes.html`): la pestaña lleva a él; no hay bloque `partes` dentro del portal | F-045 (el circuito: F-001…F-034, ya hecho) |

## 5 · Inventario de pantallas

Convenciones de esta sección: **[P F-0NN]** es un placeholder con su ficha;
**[L]** es un control local; «Pendiente: …» es un bloque de R26. Los datos son
los de `js/maqueta_datos.js` (§7), todos ficticios.

### 5.1 · `inicio`

- Tarjetas del ciclo, en orden, cada una con su contador de ejemplo y su
  enlace [L]: «Entradas por revisar» (bandeja, `nueva`), «Aprobadas sin volcar»
  (bandeja, `aprobada`), «Incidencias abiertas» (Sigrid, `SAT` + `PTE`),
  «Terminadas sin cerrar» (`TER`), «Partes pendientes de cierre» (enlace a
  `partes`), «Coste del año» (económico).
- Un párrafo que dice qué es la maqueta y para qué sirve (validar el recorrido).
- Los contadores se calculan en `Portal` a partir de los datos de ejemplo, no
  se escriben a mano en el HTML.

> **Decisión del 2026-09-25 (D-1, D-3).** La tarjeta «Partes pendientes de
> cierre (enlace a `partes`)» pasa a llamarse **«Partes firmados»**, enlaza
> a **`partes.html`** en la misma pestaña (R46) y recoge lo que era la
> sección `partes` de §5.7: la frase de que el circuito ya funciona y el
> placeholder «Registrar un parte sin firma (la incidencia queda en TER, no
> en CER)» **[P F-045]**. Sin contador: los partes pendientes son del
> circuito, que la maqueta no lee.

### 5.2 · `entrada` (F-036, F-037)

**Importar el Excel de la propiedad** (F-036):

- Zona para soltar el fichero y botón «Elegir el Excel» **[P F-036]**. Sin
  `<input type="file">`: la maqueta no lee ficheros.
- «Importar a la bandeja» **[P F-036]**.
- Pendiente: «columnas del Excel de la propiedad — llegará el Excel de
  ejemplo» (F-036). Una tabla vacía de columnas «Columna 1…n» con esa nota.
- Pendiente: «pasos de alta de una incidencia hoy — llegará el correo con los
  pasos» (F-036).

  > **Enmienda del 2026-09-25.** Los dos puntos de arriba se conservan como
  > estaban. Los pasos de alta **ya llegaron** (`04_alta_incidencia_sigrid.md`)
  > y ese pendiente **desaparece**. La tabla de columnas pasa a enseñar lo que
  > sí se sabe, de la ficha de F-036 (añadido del 2026-09-24): **qué necesita
  > cada fila** —«Unidad de posventa» y «Descripción», obligatorias;
  > «Ubicación» y «Oficio», opcionales porque se completan en la bandeja— y,
  > debajo, el pendiente que queda: «Pendiente: los nombres reales de las
  > columnas y el resto de columnas del Excel de la propiedad — el Excel de
  > ejemplo no ha llegado» (F-036). Nada de «Columna 1…n».
- **Resultado de una importación de ejemplo** (datos de F-036): fichero
  `incidencias_ejemplo.xlsx` (solo el nombre), fecha, filas leídas, filas
  válidas, filas con error y duplicadas; y la lista de errores **por fila y
  columna** («Fila 7 · columna Unidad · vacía»), que es el criterio de F-036.

**Web de clientes** (F-037):

- Panel informativo: la web de clientes es **un proyecto independiente**; lo que
  llegue de ella caerá en la misma bandeja, con origen «Web». Estado del
  contrato: «Pendiente: contrato de entrada (F-037), bloqueado por la web de
  clientes y por F-036».
- «Ver el contrato de entrada» **[P F-037]**.

### 5.3 · `bandeja` (F-038, F-039, F-040, F-043)

Lista de lo importado **antes** de Sigrid. Datos: bloque `bandeja` (F-038).

- **Filtros [L]**: origen (`Excel`, `Web`), estado de revisión, obra.
- **Columnas**: casilla de selección [L], origen, obra (código y nombre),
  unidad, descripción corta, fecha de entrada, **industrial propuesto** y su
  motivo (F-039), estado de revisión, marca «duplicada» (F-036), número de
  Sigrid tras el volcado («—» hasta entonces, F-040).
- **Estados de revisión** (vocabulario **propio**, propuesta a cerrar en F-038):
  `nueva`, `editada`, `aprobada`, `descartada`, `volcada`. La marca
  `duplicada` es aparte, no un estado.
- **Industrial propuesto** (F-039): nombre y motivo («3 trabajos de fontanería
  en esta obra», ficticio). Una fila **sin propuesta** con el texto «Sin
  histórico en la obra: no se propone» (criterio de F-039: «no se inventa»).
- **Acciones por fila**: «Editar» **[P F-038]**, «Descartar» **[P F-038]**,
  «Aprobar» **[P F-038]**, «Cambiar industrial» **[P F-039]**.
- **Acciones sobre la selección**: «Aprobar las seleccionadas» **[P F-043]**
  con el recuento de R12.
- **Volcado a Sigrid** (F-040), en un panel aparte bajo la lista: texto «Solo
  lo aprobado es candidato al volcado», contador de aprobadas, «Ver qué se
  crearía en Sigrid» **[P F-040]** (el dry-run) y «Volcar a Sigrid»
  **[P F-040]**. Nota fija: «Crear una incidencia en Sigrid necesita un
  endpoint nuevo en `sigrid-api`» (el bloqueo declarado de F-040).
- **Panel de detalle [L]** al pulsar una fila: los campos de la fila en
  solo lectura y el historial de revisión de ejemplo («quién y cuándo», criterio
  de F-038; la persona es «Usuario Ejemplo»).

> **Enmienda del 2026-09-25 · la bandeja con los campos del alta y el volcado
> con su contrato (R38–R40).** Lo de arriba se conserva; esto lo **precisa**
> donde choca. Fuentes: `04_alta_incidencia_sigrid.md` §2–§5 y
> `azure-apps/sigrid_api.md` §8.9.
>
> **Columnas de la lista** (sustituyen a las de arriba): casilla [L], origen,
> obra (código y nombre), **unidad de posventa** (`9901.03VILLA 3.` y su
> resumen), **descripción corta**, **oficio** (código · resumen, o «sin
> completar»), fecha de entrada, industrial propuesto y su motivo (F-039),
> estado de revisión, marca «duplicada» (F-036) y **código de Sigrid** tras el
> volcado («—» hasta entonces, F-040).
>
> **Panel de detalle [L]**, en solo lectura, en el orden de la ficha del parte
> de Sigrid (`04_alta…` §3), para que Posventa lo reconozca:
>
> | Bloque | Campos |
> |---|---|
> | Identificación | Obra · Unidad de posventa · **Tipo de reclamación** (`0002 · PRIMER LISTADO POSTVENTA` por defecto, R39) · Ubicación · Propietario (`9901_REF/0003 · Propietario Ejemplo 3`) · Persona que reclama (`9901_PER/0003 · …`). Propietario y persona llevan la nota «los copia Sigrid de la unidad» (`sigrid_api.md` §8.9) |
> | Datos de la reclamación | Forma de comunicación (`Escrita`, el defecto del contrato) · **Oficio** (catálogo general) · Descripción corta (≤128) · Descripción larga |
> | Intervinientes | Tabla: oficio de la obra, proveedor (`EJ07 · Fontanería Ejemplo, S.L.`) y casilla «Causante» (solo lectura). La lista sale de los **oficios de esa obra con su proveedor** (`obrofc`), que es de donde propone F-039. Pendiente: «qué oficio lleva el parte si hay varios intervinientes y quién marca Causante» (F-040) |
> | Volcado | Referencia externa (`PVI-EJEMPLO-0003`; nota «la forma exacta la fija F-040») · Código de Sigrid (`RS99.09/0003` o «—») |
>
> Sin completar: una fila de Excel sin ubicación ni oficio los enseña como «sin
> completar», que es justo lo que F-036 permite y F-038 rellenará. Una fila
> con tipo `0003` enseña «Pendiente: qué es y cuándo se usa» (R39).
>
> **Panel de volcado (F-040)**, que sustituye al de arriba:
>
> - Texto: «Solo lo aprobado es candidato al volcado. Se vuelca **obra a
>   obra**: cada lote es de una sola obra.» Contador de aprobadas **por
>   obra**.
> - «Ver qué se crearía en Sigrid» **[P F-040]** (el dry-run), «Volcar a
>   Sigrid» **[P F-040]** y, nuevo, «Reintentar los rechazados y no
>   procesados» **[P F-040]** (el contrato dice que reenviar es seguro:
>   la referencia `PVI-…` hace que lo ya creado vuelva `idempotente`).
> - **Dos resultados de ejemplo** (R40), uno debajo del otro, con el
>   resumen por estado (`previstos`, `creados`, `idempotentes`, `rechazados`,
>   `no_procesados`, los nombres del contrato) y una fila por parte:
>   referencia `PVI-…`, unidad, estado con su etiqueta y, si lo hay, código
>   de Sigrid y motivo.
>   - **Dry-run** de la obra `9901`: 3 `previsto` (código
>     `RS99.09/0001…0003` marcado «provisional», como dice el contrato), 1
>     `idempotente` (ya estaba creado: su código de verdad) y 1 `rechazado`
>     (`oficio_no_esta_en_la_obra`).
>   - **Volcado hecho** de la obra `9902`: 2 `creado`, 1 `idempotente`, 1
>     `rechazado` (`interviniente_ambiguo`) y 1 `no_procesado`
>     (`presupuesto_de_tiempo_agotado`, «se puede reenviar sin riesgo»).
> - Etiquetas legibles de los estados (catálogo en los datos de F-040):
>   `previsto` «Se crearía», `creado` «Creado en Sigrid», `idempotente` «Ya
>   estaba creado: no se duplica», `rechazado` «No se crea: hay que
>   corregirlo», `no_procesado` «No se llegó a intentar: se puede reenviar».
> - Los códigos de motivo, de la **lista cerrada** del contrato
>   (`sigrid_api.md` §8.9, «Códigos de parte»); la maqueta usa solo esos,
>   con un mensaje de ejemplo en castellano.
> - **Se quita** la nota fija «Crear una incidencia en Sigrid necesita un
>   endpoint nuevo en `sigrid-api`»: ya no es cierta (el endpoint existe y
>   espera despliegue, bloqueo de F-040). En su lugar, un pendiente sin
>   fechas que caduquen: «Pendiente: el volcado real espera a que
>   `sigrid-api` despliegue el alta en lote» (F-040).
> - Pendiente (F-040): «en qué estado queda el parte recién creado». La
>   captura de Posventa enseña el parte en `PTE` tras el alta
>   (`04_alta…` §3), y `sigrid-api` lo crea en el estado inicial de la serie
>   (`SAT`) y **no** pasa a `PTE` (§8.9, «Lo que NO hace»). La maqueta no
>   elige: los `creado` no enseñan estado (hallazgo H-3, §14).
>
> **Ni una llamada** (R14, R16): el panel pinta `MaquetaDatos.volcado`; la
> maqueta no contiene la ruta del endpoint, ni `/api/`, ni el nombre de la
> base.

### 5.4 · `incidencias`: el listado (F-041, F-043)

Incidencias **ya en Sigrid**. Datos: bloque `incidencias` (F-041).

- **Filtros [L]** (R19): estado (los cinco de `conest`), obra, texto libre
  (busca en código, resumen y descripción). Pendiente: «filtros de clase, tipo,
  oficio e industrial — los decide F-041».
- **Columnas**: casilla [L], código (`con.cod`), resumen (`con.res`), obra,
  unidad, fecha (`rcp.fec`), clase (`auxrcp`), oficio (`auxofc`), industrial,
  estado (código + resumen de `conest`, R21), y dos marcas: «parte cerrado en el
  circuito» y «proforma enlazada» (F-047).
- **Barra de operaciones en bloque**, visible con selección: «N seleccionadas»
  [L] (R20), «Cambiar estado…» **[P F-043]**, «Asignar industrial…»
  **[P F-043]**, «Imprimir los partes» **[P F-044]**; «Quitar la selección»
  [L].
- Cada fila abre su ficha [L] (`#/incidencias/<id>`).

### 5.5 · `incidencias`: la ficha (F-041, F-042, F-045, F-047)

Cabecera: código, resumen, estado (R21) y obra/unidad. Debajo, cuatro
pestañas [L]: **Datos**, **Parte**, **Económico** e **Historial**.

**Datos** — los campos, cada uno con su origen (R25). Lista cerrada de
orígenes permitidos, tomada de `azure-apps/sigrid_tablas.md` (entidades `con`,
`rcp`, `upv`, `rcpint`, `conest`) y de `docs/referencia/03_modelo_posventa_sigrid.md`:

| Etiqueta | Origen | Nota |
|---|---|---|
| Código | `con.cod` | clave de localización (`03_modelo…` §1.1) |
| Resumen | `con.res` | |
| Estado | `conest.cod` | por código, nunca `con.est` a pelo |
| Fecha / Hora | `rcp.fec` / `rcp.hor` | |
| Unidad | `rcp.upvide` | la unidad postventa |
| Obra | `upv.obride` | |
| Propietario | `rcp.cliide` | nombre ficticio |
| Persona que reclama | `rcp.recide` | |
| Persona de contacto | `rcp.cntide` | |
| Teléfonos de avisos | `rcp.tel` | en la maqueta, «sin datos de ejemplo» |
| Correo de avisos | `rcp.ele` | `…@ejemplo.invalid`; es el destino del correo de F-042 |
| Descripción larga | `rcp.tex` | |
| Clase | `rcp.rcpide` | catálogo `auxrcp` |
| Tipo | `rcp.trcpide` | catálogo `auxtrcp` |
| Motivo | `rcp.motrcp` | |
| Comunicado de forma | `rcp.rcptip` | Pendiente: los valores del entero no están documentados |
| Fecha prevista nueva visita | `rcp.fecpre` | |
| Solución | `rcp.solrcp` | vacío en todas: `03_modelo…` mide que nadie lo rellena |
| Ubicación | `rcp.resubi` | |
| Urgencia | `rcp.texurg` | |
| Oficio | `rcp.ofcide` | catálogo `auxofc` |
| Industrial | `rcpint.obrofcide` | **Pendiente**: de dónde sale el industrial lo confirma F-039; esta es la hipótesis |
| Causante de la avería | `rcpint.cauave` | |
| Fin de vicios y defectos | `upv.fecfin1` | garantías de la unidad |
| Habitabilidad / instalaciones | `upv.fecini2` – `upv.fecfin2` | |
| Inicio estructura | `upv.fecini3` | |
| Escrituración | `upv.fecesc` | |
| Visita del técnico acordada | `upv.fecvtec` | |
| Industrial propuesto y motivo | `propio` | F-039 |

> **Enmienda del 2026-09-25 a la tabla de arriba (R25, R38, R39).** La tabla
> se conserva; estas filas **cambian o entran**, con el alta de
> `04_alta_incidencia_sigrid.md` §3 y el contrato de `sigrid_api.md` §8.9, y
> la pestaña «Datos» se ordena en los mismos bloques que la ficha del parte
> de Sigrid (Identificación, Datos de la reclamación, Intervinientes), como
> el detalle de la bandeja (§5.3):
>
> | Etiqueta | Origen | Qué cambia |
> |---|---|---|
> | Código | `con.cod` | Nota nueva: serie `RS<aa>.<mm>/` + correlativo, **lo pone Sigrid** al crear |
> | Resumen → **Descripción corta** | `con.res` | Renombrada como en la pantalla de Sigrid; hasta 128 caracteres. `rcp` no tiene otra columna de descripción corta (`sigrid_tablas.md`) |
> | Propietario | `rcp.cliide` | Código `99NN_REF/NNNN` y nombre ficticio; nota «los copia Sigrid de la unidad al crear» |
> | Persona que reclama | `rcp.recide` | Código `99NN_PER/NNNN` y nombre ficticio; misma nota |
> | Tipo | `rcp.trcpide` | Catálogo `auxtrcp`, **por código y resumen** (R39): `0002 · PRIMER LISTADO POSTVENTA`, el defecto del contrato. El `0003` sale por defecto en el escritorio y **no se sabe qué es** |
> | Comunicado de forma | `rcp.rcptip` | Deja de ser del todo pendiente: `1` es «Escrita», el defecto del contrato. El `0` sigue sin documentar: la maqueta solo usa «Escrita» |
> | Ubicación | `rcp.resubi` | Hasta 48 caracteres; en Sigrid es un desplegable |
> | Oficio | `rcp.ofcide` | Catálogo **general** `auxofc` (130 oficios), por código y resumen. El contrato exige además que esté entre los oficios de la obra |
> | Industrial → **Intervinientes** | `rcpint.obrofcide` → `obrofc.ofcide`, `obrofc.prvide` | Deja de ser hipótesis en cuanto a **estructura**: cada interviniente apunta a un oficio **de la obra** (`obrofc`), que lleva oficio y proveedor (`sigrid_tablas.md`; `04_alta…` §5). Se enseña como tabla (oficio, proveedor, causante). **Sigue pendiente** cuál de ellos es «el industrial» cuando hay varios (F-039/F-040) |
> | Causante de la avería | `rcpint.cauave` | Pasa a ser la columna «Causante» de la tabla de intervinientes. Pendiente: quién la marca |
> | **Referencia externa** (nueva) | `conext[RCPCLI]` | Campo extendido de `conext` con código `RCPCLI` («Nº Referencia Externo», visible en la ficha de Sigrid): ahí guarda el volcado su `PVI-…` (`sigrid_api.md` §8.9). La columna exacta de `conext` no la dice el contrato: por eso la notación con corchetes y no `tabla.campo` |
>
> **Lista cerrada de orígenes** (la que comprueba el test de R25): la de la
> tabla de arriba con estas filas aplicadas, más `obrofc.ofcide`,
> `obrofc.prvide` y `conext[RCPCLI]`; y `propio` y `pendiente`, como antes.

Acciones: «Guardar cambios» **[P F-041]**, «Cambiar estado» (un `<select>` con
los cinco estados [L] y el botón «Ver qué cambiaría en Sigrid» **[P F-041]** +
«Aplicar el cambio» **[P F-041]**), «Cambiar industrial» **[P F-039]**,
«Imprimir el parte» **[P F-044]**.

**No procede** (F-042): botón «No procede…» [L] que abre un panel con:
justificación (área de texto [L], obligatoria: el panel lo dice), vista previa
del correo al cliente (destinatario `…@ejemplo.invalid`, asunto y cuerpo de
ejemplo con la justificación escrita), la frase «En pruebas nunca sale un correo
a un cliente real» (criterio de F-042) y «Pasar a no procede y enviar el correo»
**[P F-042]**. Pendiente: «buzón de envío — por decidir» (F-042).

**Parte** — el circuito, visto desde la incidencia: si hay parte firmado
guardado, archivado, adjunto y cerrado (marcas de ejemplo, sin nombre de
fichero); enlace [L] «Abrir el circuito de partes firmados» a `index.html`; y
«Registrar el parte sin firma (queda en TER)» **[P F-045]** con la nota «exigirá
confirmación expresa y queda constancia de quién» (criterio de F-045).

> **Enmienda del 2026-09-25 (R41).** Desde el corte de F-013 (2026-09-25) el
> circuito archiva en la **biblioteca de Posventa**, con su estructura. Las
> incidencias de ejemplo con el parte archivado enseñan además «Archivado
> en: `9901  EJEMPLO NORTE/PARTES INCIDENCIAS/VILLA 003/PARTES FIRMADOS`»:
> la carpeta, **sin** nombre de fichero (sigue la regla de «sin nombre de
> fichero» de arriba) y **sin** URL, con la carpeta de obra al modo de las
> reales (número, dos blancos y nombre: `docs/INTEGRACION.md` §3) pero
> ficticia —`99NN` y un nombre con «EJEMPLO»— y la villa con tres cifras
> (F-049). Solo en unidades `VILLA`: la maqueta no inventa carpetas para
> pisos o locales, que F-013 no ha medido. El dato vive en el bloque
> `incidencias` (F-041), que es el de la ficha.

> **Decisión del 2026-09-25 (D-3).** El enlace «Abrir el circuito de partes
> firmados» de la pestaña «Parte» apunta a **`partes.html`** (decía
> `index.html`), en la misma pestaña (R46).

**Económico** (F-047): proforma, coste y venta de la incidencia. Una incidencia
de ejemplo **enlazada** y otra **sin enlazar** (R22: «sin enlazar», no cero).
«Enlazar proforma» **[P F-047]**. Pendiente: «en qué momento y con qué campo se
relaciona la incidencia con la proforma — lo investiga F-047».

**Historial** (F-041): cambios de ejemplo (fecha, «Usuario Ejemplo», campo,
antes → después). Texto: «Queda histórico de cada cambio» (criterio de F-041).

### 5.6 · `impresion` (F-044)

- Lista de incidencias con casilla [L] y filtro por obra [L]; recuento de
  seleccionadas.
- Plantilla: «Plantilla de posventa» con Pendiente: «plantilla de referencia
  por convertir a `docs/referencia` en la spec de F-044» (su origen está en la
  ficha de F-044; la maqueta no nombra rutas personales).
- «Generar el PDF» **[P F-044]** e «Imprimir» **[P F-044]**, con el recuento
  de R12.

> **Enmienda del 2026-09-25 (R26).** La plantilla **existe** (la ficha de
> F-044 dice dónde, fuera del repositorio) pero **nadie la ha mirado**: puede
> traer datos personales, y ni se lee ni se convierte sin permiso del
> humano. El pendiente pasa a decir: «Pendiente: la plantilla de posventa
> existe y está sin revisar; se revisa, con permiso, y se convierte a
> `docs/referencia` en la spec de F-044». La maqueta sigue sin dibujar nada
> que imite la plantilla ni nombrar rutas personales. Pregunta abierta para
> el humano en `progress/spec_F-035.md`.

### 5.7 · `partes` (F-045 y el circuito)

- Texto: «El circuito de partes firmados ya funciona: soltar la remesa,
  revisar, aprobar, archivar en SharePoint, adjuntar a Sigrid y cerrar.»
- Enlace «Abrir el circuito de partes firmados» a `index.html` (misma pestaña).
- «Registrar un parte sin firma (la incidencia queda en TER, no en CER)»
  **[P F-045]**.

> **Enmienda del 2026-09-25.** El texto de la sección dice «archivar en
> SharePoint». Desde el corte de F-013 queda: «…revisar, aprobar, archivar
> en la **biblioteca de Posventa** (la carpeta `PARTES FIRMADOS` de cada
> vivienda), adjuntar a Sigrid y cerrar.» Con un ejemplo de ruta que cumple
> R41 (`9901  EJEMPLO NORTE/PARTES INCIDENCIAS/VILLA 003/PARTES FIRMADOS`).

> **Decisión del 2026-09-25 (D-1, D-3).** Esta sección **deja de existir
> como bloque del portal**: «esto que hemos hecho sera una pestaña de dicho
> portal» — la pestaña `partes` **es** el circuito (`partes.html`), no una
> página del portal que enlaza a él. Su contenido (la frase, con el texto de
> la enmienda de arriba y su ruta de ejemplo, y el placeholder de F-045) se
> muda a la tarjeta «Partes firmados» de `inicio` (§5.1). `#/partes` en el
> portal cae en R5 (§2).

### 5.8 · `economico` (F-046, F-047)

- Explicación: «POSTV2 es la obra de Sigrid donde se gestiona el coste de
  posventa; cada obra (promoción) es un capítulo».
- Tabla por capítulo (datos de F-046): capítulo (código `99NN` y nombre de
  promoción de ejemplo), incidencias, coste, venta enlazada, diferencia. Una fila
  con venta «sin enlazar» (R22).
- Al pulsar un capítulo [L], las incidencias de esa obra con proforma, coste y
  venta (datos de F-047), y las no enlazadas como tales.
- «Actualizar desde Sigrid» **[P F-046]**. Pendiente: «de qué tablas sale el
  coste del capítulo — lo decide F-046».

### 5.9 · `datos` (F-048)

- Tabla de lo que cada fase publicará en el datamart: fase, qué dato, ficha,
  estado «pendiente». Filas: entradas y su revisión (F-036/F-038), propuestas
  de industrial (F-039), volcados (F-040), cambios de estado e historial
  (F-041), no procede y correos (F-042), partes y cierres (circuito y F-045),
  coste y venta (F-046/F-047).
- Nota: «El datamart es de `datamart-seg-anual`; se coordina vía
  `azure-apps`.»
- «Ver el diccionario en el datamart» **[P F-048]**.

## 6 · Los placeholders

### 6.1 · Cómo se ven

- Clase `.placeholder` de `css/portal.css`: borde **discontinuo**, fondo con
  rayado suave, texto atenuado, `cursor: help`. No se usa `disabled`: un botón
  deshabilitado no recibe el clic y no podría explicar por qué no hace nada.
- Etiqueta visible `F-0NN` dentro del botón, en letra pequeña y monoespaciada
  (R9), y `title="Todavía no hace nada: lo construye F-0NN"`.
- `aria-disabled="true"` para que un lector de pantalla lo anuncie como no
  disponible.
- El aviso de maqueta (R13) incluye un placeholder de muestra dibujado como
  leyenda: «así se ve un botón que todavía no hace nada».

> **Segunda ronda del 2026-09-25 (R56).** Con el estilo Ruesma, el
> placeholder se redibuja **con los tokens** y conserva lo que lo delata:
> borde **discontinuo** de 1,5 px en `--rs-acero`, rayado diagonal suave,
> texto `--rs-acero-texto`, forma de píldora como los botones de verdad (así
> se ve que es «un botón», pero hueco) y la etiqueta `F-0NN` en un chip
> monoespaciado. Dos reglas nuevas: el **borde discontinuo queda reservado**
> a los placeholders en todo el portal (ninguna tarjeta, zona ni panel lo
> usa), y **ningún placeholder lleva el relleno burdeos** de la acción
> principal: la marca se reserva para lo que funciona.

### 6.2 · Qué hacen al pulsarlos

`@click="placeholder('<id>')"` y nada más en el atributo. `placeholder(id)` de
`portal_app.js` pone en `aviso` el texto de `Portal.textoPlaceholder(id,
{seleccionadas})` y ya: sin temporizadores (el aviso se queda hasta el
siguiente), sin red, sin tocar ningún otro estado. La región del aviso es
`role="status"` y `aria-live="polite"`.

### 6.3 · El catálogo (`Portal.PLACEHOLDERS`)

Cada entrada: `{ id, ficha, etiqueta, explicacion, enBloque }`. `enBloque`
marca los que dicen a cuántas afectarían (R12). Catálogo inicial:

| `id` | Ficha | Etiqueta | `enBloque` |
|---|---|---|---|
| `entrada.elegirExcel` | F-036 | Elegir el Excel | |
| `entrada.importar` | F-036 | Importar a la bandeja | |
| `entrada.verContratoWeb` | F-037 | Ver el contrato de entrada | |
| `bandeja.editar` | F-038 | Editar | |
| `bandeja.descartar` | F-038 | Descartar | |
| `bandeja.aprobar` | F-038 | Aprobar | |
| `bandeja.cambiarIndustrial` | F-039 | Cambiar industrial | |
| `bandeja.aprobarSeleccionadas` | F-043 | Aprobar las seleccionadas | sí |
| `bandeja.verVolcado` | F-040 | Ver qué se crearía en Sigrid | |
| `bandeja.volcar` | F-040 | Volcar a Sigrid | |
| `incidencias.cambiarEstadoBloque` | F-043 | Cambiar estado… | sí |
| `incidencias.asignarIndustrialBloque` | F-043 | Asignar industrial… | sí |
| `incidencias.imprimirBloque` | F-044 | Imprimir los partes | sí |
| `ficha.guardar` | F-041 | Guardar cambios | |
| `ficha.verCambioEstado` | F-041 | Ver qué cambiaría en Sigrid | |
| `ficha.aplicarEstado` | F-041 | Aplicar el cambio | |
| `ficha.cambiarIndustrial` | F-039 | Cambiar industrial | |
| `ficha.imprimir` | F-044 | Imprimir el parte | |
| `ficha.enviarNoProcede` | F-042 | Pasar a no procede y enviar el correo | |
| `ficha.registrarSinFirma` | F-045 | Registrar el parte sin firma | |
| `ficha.enlazarProforma` | F-047 | Enlazar proforma | |
| `impresion.generarPdf` | F-044 | Generar el PDF | sí |
| `impresion.imprimir` | F-044 | Imprimir | sí |
| `partes.registrarSinFirma` | F-045 | Registrar un parte sin firma | |
| `economico.actualizar` | F-046 | Actualizar desde Sigrid | |
| `datos.verDiccionario` | F-048 | Ver el diccionario en el datamart | |

> **Enmienda del 2026-09-25.** Entra una fila, tras `bandeja.volcar`:
>
> | `id` | Ficha | Etiqueta | `enBloque` |
> |---|---|---|---|
> | `bandeja.reintentarVolcado` | F-040 | Reintentar los rechazados y no procesados | sí |
>
> Y la `explicacion` de `bandeja.verVolcado` y `bandeja.volcar` dice que el
> volcado va **por obra** y que reintentar no duplica (referencia `PVI-…`).

> **Decisión del 2026-09-25 (D-1, D-3).** `partes.registrarSinFirma` sigue
> en el catálogo con el mismo `id` (su prefijo nombra la sección de la que
> es, no el bloque donde se pinta), pero se dibuja en la tarjeta «Partes
> firmados» de `inicio` (§5.1). F-045 conserva así sus dos placeholders
> (`partes.registrarSinFirma` y `ficha.registrarSinFirma`), ninguno en el
> circuito: la barra de `partes.html` no lleva botones (R45).

El implementer puede añadir entradas si el inventario de §5 lo pide; **no**
puede usar una ficha que no esté en `harness/features.json` (R27) ni la propia
F-035 (se quedaría viva para siempre: R28 la haría fallar al cerrarla).

## 7 · Los datos de ejemplo

### 7.1 · Dónde viven y con qué forma

`js/maqueta_datos.js` expone `window.MaquetaDatos` (y `module.exports`), un
objeto **congelado** (`Object.freeze` profundo) de bloques:

```
{
  obras:       { ficha: "F-041", filas: [...] },   // 3 obras 99NN
  entrada:     { ficha: "F-036", importacion: {...}, errores: [...], pendientes: [...] },
  web:         { ficha: "F-037", pendientes: [...] },
  bandeja:     { ficha: "F-038", filas: [...], historial: [...] },
  propuestas:  { ficha: "F-039", porFila: {...} },
  incidencias: { ficha: "F-041", filas: [...], campos: [...], historial: [...] },
  noProcede:   { ficha: "F-042", plantillaCorreo: {...}, pendientes: [...] },
  impresion:   { ficha: "F-044", pendientes: [...] },
  capitulos:   { ficha: "F-046", filas: [...], pendientes: [...] },
  vinculos:    { ficha: "F-047", porIncidencia: {...}, pendientes: [...] },
  datamart:    { ficha: "F-048", filas: [...] }
}
```

Tamaño orientativo: 3 obras, 8 filas de bandeja (6 de Excel y 2 de Web, una
duplicada y una sin propuesta de industrial), 12 incidencias repartidas entre
los cinco estados, 3 capítulos de POSTV2, una incidencia enlazada con proforma
y otra sin enlazar, 5 filas de historial.

> **Enmienda del 2026-09-25 (R38–R41).** Cambia la forma de tres bloques y
> entra uno:
>
> - `bandeja` (F-038): cada fila gana los campos del alta de §5.3 —`unidad`
>   (`{cod, res}`), `descripcionCorta`, `descripcionLarga`, `ubicacion`,
>   `oficio`, `tipo`, `forma`, `propietario`, `persona`, `intervinientes`
>   (`[{oficio, proveedor, causante}]`) y `referenciaExterna`—, con `null`
>   donde la bandeja puede completar (se pinta «sin completar»). Al menos una
>   fila de Excel sin ubicación ni oficio, y exactamente una con tipo `0003`
>   para enseñar el pendiente de R39.
> - `propuestas` (F-039): gana `oficiosObra`, por obra, la lista de oficios de
>   la obra con su proveedor (`[{oficio, proveedor, comentario}]`, 4–6 por
>   obra), que es de donde sale la propuesta y la tabla de intervinientes.
> - `incidencias` (F-041): las filas ganan los mismos campos del alta y, las
>   que tienen el parte archivado, `carpetaArchivo` (R41). Las unidades pasan
>   a ser `99NN.03VILLA N.` (sustituyen a `Vivienda EJ-NN`).
> - **Nuevo** `volcado: { ficha: "F-040", catalogos: {tipos, formas,
>   oficios, estados, motivos}, dryRun: {obra, partes: [...]}, hecho: {obra,
>   partes: [...]}, pendientes: [...] }`. `catalogos.tipos` lleva `0002`
>   con su resumen y `0003` con `res: null` (R39); `formas`, solo `Escrita`;
>   `oficios`, 5–6 del catálogo general tomados de `04_alta…` §4 y §3
>   (`0005`, `0011`, `0021`, `0024`, `0143`); `estados`, los cinco del
>   contrato con su etiqueta de §5.3; `motivos`, la lista cerrada de códigos
>   de parte de `sigrid_api.md` §8.9. Cada parte:
>   `{referenciaExterna, unidad, estado, cod, provisional, motivo}`. Los
>   partes de los dos resultados son ejemplos del resultado, no tienen por
>   qué ser filas de la bandeja.
>
> Los catálogos del alta van en el bloque de **F-040** porque existen para
> el volcado; cuando F-038 construya la edición y los necesite antes, se los
> lleva a sus módulos en el mismo trabajo (§7.3) y quita su parte del
> bloque.

### 7.2 · Convenciones de lo ficticio (R24)

| Dato | Forma | Ejemplo |
|---|---|---|
| Código de obra | `99NN` | `9901` |
| Nombre de obra | contiene «Ejemplo» | `PROMOCIÓN EJEMPLO NORTE` |
| Código de incidencia | `RS99.NN/NNNN` (serie de un «año 99» que Sigrid no ha emitido) | `RS99.01/0007` |
| Identificador de ruta | `EJ-NNNN` | `EJ-0007` |
| Persona o empresa | contiene «Ejemplo» | `Propietario Ejemplo 3`, `Fontanería Ejemplo, S.L.` |
| Correo | dominio reservado `ejemplo.invalid` | `propietario3@ejemplo.invalid` |
| Teléfono, DNI, NIF | **no hay** | «sin datos de ejemplo» |
| Unidad | `Vivienda EJ-NN` | `Vivienda EJ-12` |
| Textos | inventados, sin nada de `muestras/` | «Humedad en el techo del baño (ejemplo)» |
| Importes | redondos y claramente ilustrativos | `1.250,00 €` |
| Estados | por **código** de `conest` | `"PTE"`, nunca `3` |
| Unidad de posventa *(2026-09-25)* | `99NN.03VILLA N.` y resumen con «ejemplo»; **sustituye** a `Vivienda EJ-NN` | `9901.03VILLA 3.` · `Villa 3 (ejemplo)` |
| Propietario *(2026-09-25)* | `99NN_REF/NNNN` y nombre con «Ejemplo» | `9901_REF/0003` · `Propietario Ejemplo 3` |
| Persona que reclama *(2026-09-25)* | `99NN_PER/NNNN` y nombre con «Ejemplo» | `9901_PER/0003` · `Persona Ejemplo 3` |
| Proveedor *(2026-09-25)* | código `EJNN` y nombre con «Ejemplo» | `EJ07` · `Fontanería Ejemplo, S.L.` |
| Referencia externa *(2026-09-25)* | `PVI-EJEMPLO-NNNN` | `PVI-EJEMPLO-0003` |
| Código tras el volcado *(2026-09-25)* | `RS99.09/NNNN`, «provisional» en el dry-run | `RS99.09/0001` |
| Carpeta de archivo *(2026-09-25)* | `99NN  EJEMPLO …/PARTES INCIDENCIAS/VILLA NNN/PARTES FIRMADOS` | `9901  EJEMPLO NORTE/PARTES INCIDENCIAS/VILLA 003/PARTES FIRMADOS` |
| Catálogos generales *(2026-09-25)* | **códigos reales** de Sigrid (D-10): tipos, formas, oficios, estados | `0002 · PRIMER LISTADO POSTVENTA`, `0143 · Carpintería de madera` |

El barrido de DNI y base64 del front (`tests/test_f007_sin_datos_reales.py`)
ya cubre los ficheros nuevos, porque recorre todo el árbol.

### 7.3 · Cómo se retiran, sección a sección (R28)

Cuando una ficha F-0NN construya su pieza, **en el mismo trabajo**:

1. Borra de `portal.html` los elementos con `data-placeholder="F-0NN"` y pone
   en su lugar los controles reales.
2. Borra de `Portal.PLACEHOLDERS` sus entradas y de `MaquetaDatos` su bloque (o
   su parte del bloque), y cambia los `x-for` que lo pintaban por los datos
   reales.
3. Si la sección real habla con el backend, lo hace desde **sus propios**
   módulos (el patrón `api.js`): la regla R14 es de los ficheros de la maqueta,
   no una prohibición al portal de tener backend.

Si se olvida, `tests/test_f035_placeholders_vivos.py` (R28) se pone en rojo en
cuanto la ficha pase a `done`, con el identificador de cada resto. Cuando no
quede ninguna ficha con placeholders, `maqueta_datos.js` y la parte de
`portal.js` que solo sirve a la maqueta se borran en la última ficha que los
use.

> **Enmienda del 2026-10-05 · pasos 5 y 6 de la retirada (§16.4, §16.2).**
>
> 5. Al cerrar la ficha, **actualiza el `estado` de su sección** en
>    `Portal.SECCIONES` (R62): si la sección deja de estar en `construccion`,
>    quita su envoltorio de sección, saca de él lo que ya funciona y deja en
>    envoltorios de bloque `data-en-construccion="F-0NN"` lo que siga sin
>    funcionar (R64); quita también el `data-construccion` y el `aria-label`
>    de su pestaña en **las cuatro barras** (R66). Si se olvida,
>    `tests/test_f035_placeholders_vivos.py` (R62, en la raíz, sin caché) se
>    pone en rojo.
> 6. Si la sección real vive en su **propia página** (el patrón de
>    `importar.html` y `oficios.html`), esa página lleva la barra común en HTML
>    estático, la identidad Ruesma y nada de la maqueta (R70–R73, R77), y se
>    declara en `Portal.PAGINAS` con su sección.

## 8 · Funciones y firmas

### 8.1 · `js/portal.js` (puro; `window.Portal` y `module.exports`)

| Firma | Responsabilidad |
|---|---|
| `SECCIONES: ReadonlyArray<{id, etiqueta, fichas}>` | Catálogo de §4, en su orden (R2) |
| `PLACEHOLDERS: ReadonlyArray<{id, ficha, etiqueta, explicacion, enBloque}>` | Catálogo de §6.3 (R8) |
| `ESTADOS: ReadonlyArray<{cod, res}>` | `SAT SIN ATENDER`, `PTE PENDIENTE`, `TER TERMINADA`, `NPR NO PROCEDE`, `CER CERRADA` (R21). Sin el `est` numérico |
| `resolverRuta(hash: string, idsIncidencia: string[]): {seccion, incidencia, aviso}` | R4–R7. Tolerante: `""`, `"#"`, `"#/"`, mayúsculas, barra final |
| `hashDe(seccion: string, incidencia?: string): string` | Inversa de la anterior, para los enlaces |
| `placeholderPorId(id: string): object \| null` | Búsqueda en el catálogo |
| `textoPlaceholder(id: string, contexto?: {seleccionadas?: number}): string` | R11–R12. Un `id` desconocido devuelve un texto genérico, nunca lanza |
| `filtrarIncidencias(filas, filtros: {estado?, obra?, texto?}): filas` | R19. Texto sin distinguir mayúsculas ni tildes |
| `filtrarBandeja(filas, filtros: {origen?, estado?, obra?}): filas` | Igual, para la bandeja |
| `etiquetaEstado(cod: string): string` | `"PTE · PENDIENTE"`; código desconocido → el código tal cual |
| `formatoImporte(valor: number \| null \| undefined): string` | R22 |
| `contadoresInicio(datos): object` | Los contadores de §5.1 |
| `alternarSeleccion(seleccion: string[], id: string): string[]` | R20; devuelve una lista nueva, no muta |
| `etiquetaCatalogo(cod: string \| null, catalogo: Array<{cod, res}>): string` *(2026-09-25)* | R39. `"0002 · PRIMER LISTADO POSTVENTA"`; entrada con `res: null` → `"0003 · Pendiente: qué es y cuándo se usa"`; `null` → `"sin completar"`; código desconocido → el código tal cual |
| `resumenVolcado(partes: Array<{estado}>): {previstos, creados, idempotentes, rechazados, no_procesados}` *(2026-09-25)* | R40. Cuenta por estado con los nombres del resumen del contrato; un estado desconocido no suma a ninguno |
| `etiquetaEstadoVolcado(estado: string, estados: Array<{cod, etiqueta}>): string` *(2026-09-25)* | R40. Estado desconocido → el código tal cual, nunca lanza |

> **Decisión del 2026-09-25 (D-1, D-2, D-3).** Cambian dos firmas y entra
> una:
>
> | Firma | Responsabilidad |
> |---|---|
> | `SECCIONES: ReadonlyArray<{id, etiqueta, fichas, pagina}>` | Como antes, más `pagina`: `null` para las siete secciones que viven en el portal y `"partes.html"` para `partes` (R2, R44) |
> | `resolverRuta(hash, idsIncidencia)` | Como antes, pero una sección con `pagina` distinta de `null` **no es una sección del portal**: `#/partes` devuelve `inicio` sin aviso (R5) |
> | `enlaceSeccion(id: string, desde: "portal" \| "circuito"): {href, nuevaPestana}` | R31, R44, R46. Desde el portal: `{href: "#/<id>", nuevaPestana: false}` y, para `partes`, `{href: "partes.html", nuevaPestana: false}`. Desde el circuito: `{href: "./#/<id>", nuevaPestana: true}`; `partes` → `null` (es la página actual). Un `id` desconocido → `null`, nunca lanza. Es la **única** fuente de los `href` de las dos barras: el test de R44 cruza con ella el HTML de las dos páginas |

### 8.2 · `js/portal_app.js` (pegamento; `portalPosventa` global y `module.exports`)

Estado: `seccion`, `incidenciaAbierta`, `pestanaFicha`, `filtros` (uno por
lista), `seleccionIncidencias`, `seleccionBandeja`, `seleccionImpresion`,
`panelNoProcede`, `justificacion`, `filaBandejaAbierta`, `capituloAbierto`,
`aviso`, `avisoRuta`. Métodos: `iniciar()` (lee `location.hash` y se suscribe a
`hashchange`), `ir(seccion, incidencia?)`, `placeholder(id)`, y los de los
controles locales, cada uno una línea que delega en `Portal`.

Misma regla de oro que `app.js` («si algo merece un test, no vive aquí»), con
una guardia estática propia en `test_f035_portal.py`: sin `fetch(`,
`XMLHttpRequest`, `setTimeout`, `setInterval`, `console.`, `JSON.stringify` ni
`window.Api`. Se exporta también con `module.exports` para que
`tests_js/portal.test.js` pueda **instanciar el componente** con un `window`
falso y comprobar R16 recorriendo todos los placeholders y todas las rutas con
`fetch` y `XMLHttpRequest` sustituidos por dobles que fallan.

## 9 · Acceso, grupo de Entra y tarjeta del portal

- La maqueta **hereda el acceso del circuito** (R35): misma Static Web App,
  misma asignación obligatoria de la aplicación empresarial en Entra. Ni un
  cambio de configuración.
- **Discrepancia a resolver (D-5)**: la ficha y `docs/ARCHITECTURE.md:544`
  (`:578` en `54c0884`)
  dicen que **no existe** grupo de Entra de Posventa; pero `docs/DESPLIEGUE.md`
  §3 manda crear `posventa-usuarios` y `progress/history.md` (2026-08-25, cierre
  de F-010) y `progress/impl_F-010.md:950-958` registran que existe, está
  asignado y que **un no miembro rebota**. `azure-apps/portal.md` §5 y §6.5 no
  recogen ni la tarjeta ni el grupo de posventa. *(2026-09-25)*: la fila de
  `ARCHITECTURE.md` sigue diciendo «No existe» en `54c0884`, y
  `azure-apps/postventa_incidencias.md` registra el front del piloto como
  «miembros del grupo `posventa-usuarios`»: la discrepancia sigue abierta.
- La tarjeta vive en `front-portal` (`public/assets/js/catalog.js`), **otro
  repositorio**: esta ficha **no la toca**. Si Posventa entra a la maqueta por
  el portal corporativo, hace falta la tarjeta del bloque de
  `docs/DESPLIEGUE.md` §6, que es tarea del humano o de quien lleve
  `front-portal`.

> **Decisión del 2026-09-25 (D-5, D-3).** El humano: «creo que existe». El
> líder lo ha medido hoy, **solo lectura**, con `az ad group list`:
>
> - existe el grupo **de seguridad** `posventa-usuarios`, con **7 miembros**:
>   el que ya usa el front del piloto y el que citan `docs/DESPLIEGUE.md` y
>   `docs/INTEGRACION.md`;
> - existe además un grupo `Postventa` **no de seguridad**, con **9
>   miembros**; probablemente el de Microsoft 365 del sitio de Posventa.
>
> Consecuencias: la discrepancia de la segunda viñeta **se resuelve**: la
> fila de Entra ID de `docs/ARCHITECTURE.md` (`:578`, «No existe grupo de
> Posventa») está **desactualizada** y **T10 la corrige** con un recuadro
> fechado, sin un GUID en ningún fichero. La tercera viñeta también
> cambia: la tarjeta **ya existe** en `front-portal`, apunta a la raíz y
> exige `posventa-usuarios` (§1.3); con D-3 aterriza en el portal sin
> tocarla. **Pregunta abierta para el humano**: ¿el acceso al portal es
> `posventa-usuarios` (7) o hay que ampliarlo al departamento (¿los 9 de
> `Postventa`?)? Ampliarlo no es de F-035: es añadir miembros al grupo de
> seguridad (Entra) o asignar otro grupo a la aplicación, y lo haría el
> humano; la maqueta hereda el acceso que haya (R35).

## 10 · Límite de servicio

F-035 vive entera en `services/postventa-front/` (más un test de raíz y dos
documentos). No invade ningún otro servicio ni repositorio. Lo que las fichas
siguientes **sí** van a cruzar, para que no sorprenda y quede anotado desde el
primer día:

| Ficha | Frontera | Dónde va |
|---|---|---|
| F-037 | La web de clientes | **Proyecto independiente** con su repositorio y su documento en `azure-apps`; aquí solo el contrato de entrada |
| F-040, F-041 | Crear y modificar incidencias en Sigrid | Endpoints **nuevos en `sigrid-api`** (su §7.5: reserva de `ide`), propuestos en **su** repositorio |
| F-042 | Envío de correo | Permiso de la aplicación para enviar correo y buzón por decidir |
| F-048 | El datamart | Es de `datamart-seg-anual`; se coordina vía `azure-apps` |
| — | La tarjeta del portal | `front-portal` (§9) |

> **Enmienda del 2026-09-25 a la fila de F-040.** La fila dice «endpoints
> nuevos en `sigrid-api` (su §7.5), propuestos en **su** repositorio». Para
> **crear** ya no hay que proponer nada: `sigrid-api` tiene
> `POST /api/sigrid/partes-reclamacion` (`azure-apps/sigrid_api.md` §8.9,
> su F-006), alta en lote de una obra con dry-run por defecto e idempotencia
> por `PVI-…`; está pendiente de **su** despliegue (bloqueo actual de F-040
> en `harness/features.json`). F-035 solo toma su **vocabulario** —estados,
> motivos, resumen— para la maqueta; no lo consume. Para **modificar**
> (F-041) sigue haciendo falta proponerlo allí: el contrato dice que no
> modifica ni anula partes.

## 11 · Verificación

| Requisitos | Test |
|---|---|
| R2, R4–R8, R11, R12, R19–R22 | `tests_js/portal.test.js` (`f035 Rn: …`) |
| R16 | `tests_js/portal.test.js`: instancia `portalPosventa()` con dobles de `fetch`/`XMLHttpRequest` que fallan y recorre `ir()` de cada sección, de cada ficha y de un id inexistente, y `placeholder()` de **todo** el catálogo |
| R9 (coherencia id ↔ ficha), R31 (mismas secciones) | `tests_js/portal.test.js` leyendo `portal.html` e `index.html` con `fs` y cruzando con los catálogos |
| R23–R26 | `tests_js/maqueta_datos.test.js` |
| R1, R3, R9, R10, R13–R15, R17, R18, R30, R34 | `tests/test_f035_portal.py` (`test_f035_rN_…`), con parser de la biblioteca estándar (`html.parser`) |
| R30 (sin borrar líneas), R32, R33 | `tests/test_f035_portal.py` con `git diff --numstat` / `--name-status` contra `git merge-base dev HEAD` (git local, sin red). **Solo se ejecutan en la rama `feature/F-035-portal-posventa`**; en cualquier otra rama se saltan con el motivo escrito («verificación del diff de F-035: las fichas siguientes sí pueden tocar el circuito»). Un test permanente que prohibiera tocar `app.js` bloquearía a F-045 y compañía |
| R35 | `tests/test_f035_portal.py` (permanente): ninguna ruta de `staticwebapp.config.json` deja `portal.html` fuera de `authenticated`, y el `/*` sigue exigiéndolo |
| R27–R29 | `tests/test_f035_placeholders_vivos.py` (raíz) |
| R36, R37 | `tests/test_f035_portal.py` (README) y el test de raíz (ARCHITECTURE): presencia de las secciones |
| R38 *(2026-09-25)* | `tests_js/maqueta_datos.test.js`: cada fila de `bandeja` e `incidencias` trae todas las claves del alta (con valor o `null` solo en ubicación, oficio e intervinientes); `tests/test_f035_portal.py`: las etiquetas de los campos están en el detalle de la bandeja y en la pestaña «Datos» |
| R39 *(2026-09-25)* | `tests_js/portal.test.js` (`etiquetaCatalogo`: `0002`, `0003` con `res: null`, `null`, desconocido) y `tests_js/maqueta_datos.test.js` (todo `tipo` y `oficio` usado está en `volcado.catalogos`; exactamente una fila con `0003`) |
| R40 *(2026-09-25)* | `tests_js/maqueta_datos.test.js`: cada resultado es de una sola obra; todo `estado` es de los cinco; el dry-run sin `creado` y con `provisional: true` en los que llevan código; el hecho sin `previsto`; `rechazado`/`no_procesado` con `motivo.codigo` de `catalogos.motivos` y los demás con `motivo: null`; toda referencia empieza por `PVI-`. `tests_js/portal.test.js`: `resumenVolcado` y `etiquetaEstadoVolcado` |
| R41 *(2026-09-25)* | `tests_js/maqueta_datos.test.js`: toda `carpetaArchivo` casa con `^99\d\d  EJEMPLO [^/]+/PARTES INCIDENCIAS/VILLA \d{3}/PARTES FIRMADOS$` (sin `.pdf`, sin `://`) |

**Fase RED**: los tests se escriben antes que la maqueta (`tasks.md` bloque 2)
y fallan por ausencia de los ficheros; la traza va a `progress/impl_F-035.md`.

**Mutación**: `harness.mutacion` solo muta Python y esta feature no cambia
ninguna línea Python de producción, así que la campaña se ejecuta y sale con
**0 mutantes** («Sin líneas de producción en el alcance»); la puerta de
cobertura sale **N/A** con su motivo, como ya imprime hoy `init.sh` en esta
rama. **Compensación** (CHECKPOINTS C4 bis: un N/A se justifica): cinco
(seis desde el 2026-09-25) mutaciones **a mano, en una copia aislada** del front, con la traza del fallo
en el informe:

1. `placeholder()` de `portal_app.js` llama a `fetch("/api/x")` → cae R16.
2. Un botón de `portal.html` pierde `data-placeholder` → cae R10.
3. `portal.html` carga `js/api.js` → cae R15.
4. `formatoImporte(null)` devuelve `"0,00 €"` → cae R22.
5. `harness/features.json` con F-044 en `done` → cae R28.
6. *(2026-09-25)* Un parte del dry-run de ejemplo pasa a `creado` → cae R40.

> **Decisión del 2026-09-25 (D-1, D-2, D-3) · tests nuevos y enmendados.**
> Las filas de R30, R31 y R32 de la tabla se conservan como premisa; estas
> las **sustituyen** donde chocan. Todo sin red y sin BBDD; lo único que
> necesita git es lo que ya lo necesitaba (git local).
>
> | Requisitos | Test |
> |---|---|
> | R30 / R43 (el circuito es el de antes) | `tests/test_f035_portal.py`, **solo en la rama de F-035**: lee `git show <merge-base>:services/postventa-front/index.html` y `partes.html`, y compara línea a línea con `difflib.SequenceMatcher`. Pasa si los códigos de operación son solo `equal`, **un** `replace` de la línea 1 (la cabecera con la ruta) y **un** `insert` justo después de la línea del `x-data="appPostventa()"` que contiene `data-barra-portal`. Cualquier `delete` o cualquier otro `replace` falla con la línea |
> | R32 enmendado (los tests del circuito no cambian) | `tests/test_f035_portal.py`, **solo en la rama de F-035**: `git diff --numstat <merge-base> -- services/postventa-front/tests services/postventa-front/tests_js` da `1 1` **exactamente** en los siete ficheros de §1.2 y altas en los ficheros nuevos; nada más. Y `git diff -U0` de cada uno de los siete: la línea quitada es `INDEX = RAIZ_FRONT / "index.html"` y la puesta empieza por `INDEX = RAIZ_FRONT / "partes.html"` |
> | R42 (la portada es el portal) | `tests/test_f035_portal.py` (permanente): `index.html` monta `x-data="portalPosventa()"`, no carga ningún módulo del circuito (R15) y carga los tres de la maqueta en su orden (R34); `partes.html` existe y monta `x-data="appPostventa()"`. Y con el `HandlerDeTest` de `test_f007_dev_server.py` como patrón (copiado, no importado), que `dev_server.py` traduce `/` a `index.html` |
> | R44 (barra común) | `tests_js/portal.test.js`: lee `index.html` y `partes.html` con `fs`, extrae el `<nav data-barra-portal>` de cada una y comprueba que las etiquetas y su orden son las de `Portal.SECCIONES` y que cada `href` es el de `enlaceSeccion(id, "portal" \| "circuito")` |
> | R45 (barra inerte en el circuito) | `tests/test_f035_portal.py` (permanente): el `<nav data-barra-portal>` de `partes.html` no tiene ningún atributo que empiece por `x-`, `@` o `:`, ni `<script>`, `<button>`, `<form>` ni `<input>`; y `test_f007_estaticos.py` —sin tocarlo, salvo su `INDEX`— sigue exigiendo los nueve scripts del circuito en `partes.html` |
> | R31 enmendado, R46, R47 | `tests/test_f035_portal.py`: en `partes.html`, cada enlace de la barra lleva `target="_blank"` y `rel` con `noopener`, `partes` es un `aria-current="page"` sin `href`, y la leyenda de R47 está; en `index.html`, la pestaña `partes` y los enlaces al circuito de `inicio` y de la ficha apuntan a `partes.html` **sin** `target` |
> | R17 enmendado | `tests/test_f035_portal.py`: todo `href` de `index.html` es `#/…` o `partes.html` |
> | R35 enmendado | Como antes, para `/`, `/index.html` y `/partes.html` |
>
> **Compensación manual** (sigue C4 bis): siete y ocho, en la misma copia
> aislada:
>
> 7. Se añade `@click="x()"` a un enlace de la barra de `partes.html` → cae R45.
> 8. Se cambia, además de `INDEX`, una aserción de `test_f025_front.py` → cae
>    la guardia de R32.

> **Segunda ronda del 2026-09-25 · tests del estilo.** La fila «R30 / R43»
> del recuadro de arriba (comparación con `difflib`) **se sustituye** por la
> de R59; el resto sigue. Detalle de cada guardia en §15.8.
>
> | Requisitos | Test |
> |---|---|
> | R59 (sustituye a R30/R43 línea a línea) | `tests/test_f035_portal.py`, **solo en la rama de F-035**: `partes.html` frente a `git show <merge-base>:services/postventa-front/index.html`, como secuencia de tokens de `html.parser` sin el atributo `class`; más un control **permanente** (sin git) que aplica la misma función a copias estropeadas en memoria |
> | R33 enmendado | El mismo test de siempre, con `css/styles.css` admitido como `M` |
> | R48 | `tests/test_f035_placeholders_vivos.py` (raíz), con su control de F-048 `done`; y la regla presente en `docs/ARCHITECTURE.md` |
> | R49, R50, R53, R54, R55, R60 | `tests/test_f035_portal.py`: los CSS y las cabeceras leídos como texto; el contraste calculado con la fórmula WCAG a partir de los valores del `:root` |
> | R51, R56, R58 | `tests/test_f035_portal.py` con `html.parser` sobre las dos páginas |
> | R52 | `tests/test_f035_portal.py`: SHA-256 de los dos SVG y barrido de lo prohibido |
> | R57 | `tests_js/portal.test.js`: cada código de `Portal.ESTADOS`, de los estados de revisión y de `MaquetaDatos.volcado.catalogos.estados` tiene su `[data-estado="…"]` en `css/portal.css`; y en `index.html` todo `data-estado`/`:data-estado` va en un `rs-chip` con texto |
> | R61 | `tests/test_f035_portal.py`: la sección del README y sus palabras clave |
>
> **Compensación manual** (sigue C4 bis), de la 9 a la 13, en la misma copia
> aislada:
>
> 9. En `partes.html` se cambia `@click="reiniciar()"` por
>    `@click="reiniciar(); x = 1"` → cae R59.
> 10. En `partes.html` se pone el `class` del aviso de fallo del autoguardado
>     **antes** de su `x-show` → cae R59 (atributos en su orden) y, además,
>     `test_f026_autoguardado.py:280`.
> 11. Se añade `display: flex !important` a `.rs-panel` → cae R60.
> 12. `--rs-acero-texto` pasa a `#7b868c` → cae R53.
> 13. Un placeholder del portal gana `rs-btn--primario` → cae R56.

## 12 · Riesgos

| Riesgo | Mitigación |
|---|---|
| Posventa toma la maqueta por funcionalidad real | Aviso permanente (R13), placeholders con la ficha visible, textos «(ejemplo)», datos imposibles (`RS99…`) |
| Alguien pega datos reales «para que se vea mejor» | R24 y el barrido existente de DNI/base64; D-4 recuerda que la maqueta se publica con el siguiente despliegue |
| La navegación nueva de `index.html` hace perder una remesa en curso | Pestaña nueva (R31) |
| La maqueta se queda viva cuando las fichas avanzan | R28 en la suite de la raíz, que no se cachea |
| Los tests estáticos de la maqueta frenan a las fichas siguientes | R14 aplica a los ficheros de la maqueta, no a los módulos reales que vengan (§7.3.3) |
| Tailwind por CDN no pinta clases construidas dinámicamente | Clases escritas enteras en el HTML, como ya hace `index.html` |
| *(2026-09-25)* Posventa toma los valores del alta de la maqueta (`0002`, «Escrita», el volcado por obra) por decididos | Son los defectos del contrato de `sigrid-api`, no decisiones de F-040; cada uno lleva su pendiente (R26) y la validación V3 los pregunta |
| *(2026-09-25)* El contrato de `sigrid/partes-reclamacion` cambia antes de F-040 y la maqueta enseña estados o motivos viejos | Viven en un único bloque de datos (`volcado`, F-040), que F-040 retira al construir el panel real (R28) |
| *(D-3, 2026-09-25)* Quien usa hoy el circuito entra por la tarjeta o por un favorito a `/` y se encuentra el portal | La pestaña «Partes firmados» está a un clic, en la barra superior; aviso a Posventa al publicar (D-4, V4) |
| *(D-3)* Tras el inicio de sesión, quien abrió `/partes.html` sin sesión vuelve a la portada | El `401` redirige sin `post_login_redirect_uri` (§1.3). No se toca la configuración para esto; se mira en V4 y, si molesta, se propone una ficha |
| *(D-3)* El navegador tiene en caché el `index.html` viejo y enseña el circuito en `/` tras publicar | `Ctrl+F5` en V4, como ya dice `docs/DESPLIEGUE.md` §6 para el portal corporativo |
| *(D-2)* Posventa, desde el circuito real, toma las otras pestañas por funcionalidad | Leyenda de R47 en la barra del circuito, aviso de maqueta en el portal (R13), placeholders marcados |
| *(D-2)* La pestaña nueva al salir del circuito extraña | Es lo que evita perder la remesa sin tocar `app.js`; se pregunta en V3 |
| *(D-3)* Un cambio de test «de paso» al mudar el circuito | La guardia de R32 enmendado: solo la línea `INDEX` de los siete ficheros |

> **Segunda ronda del 2026-09-25.** Los riesgos del estilo Ruesma, y sobre
> todo los del circuito en producción, están en **§15.9**. La fila «Tailwind
> por CDN no pinta clases construidas dinámicamente» sigue valiendo para las
> utilidades de Tailwind; las clases `rs-*` son de nuestra hoja y no dependen
> de ello.

## 13 · Decisiones abiertas (con recomendación)

- **D-1 · ¿Una página o secciones dentro de `index.html`?** Recomendación:
  **página aparte `portal.html` con rutas por hash** (§2). Alternativas A–D de
  §2 descartadas con su motivo. Consecuencia que el humano tiene que aceptar: el
  criterio «el circuito sigue funcionando igual **dentro** del portal» se
  cumple **enlazándolo**, no incrustándolo.
- **D-2 · ¿Cómo convive la navegación con el circuito?** Recomendación:
  **barra en la cabecera de `index.html`, enlaces a pestaña nueva** (R31).
  Alternativas: (b) misma pestaña con aviso de que se pierde la remesa — obliga a
  tocar `app.js` para el aviso; (c) ningún enlace desde `index.html` y Posventa
  entra por `/portal.html` — la maqueta no se descubre.
- **D-3 · ¿La portada `/` pasa a ser el portal?** Recomendación: **no en
  F-035**. Mover el circuito a otra página toca el `INDEX` de nueve ficheros de
  test y la URL de la tarjeta; se hace cuando haya una sección real que lo
  justifique, como ficha propia.
- **D-4 · ¿Se despliega ya a `dev` para que Posventa la vea?** Recomendación:
  **sí, después de V1 y V2**, con `desplegar_front.ps1 -SoloFront` ejecutado por
  el humano, avisando a Posventa de que es una maqueta. Ojo: **no se puede
  desplegar el front sin la maqueta** (§1.3), así que mergear F-035 en `dev` es
  aceptar que el siguiente despliegue la publique. Excluirla del despliegue
  exigiría tocar `infra/` y se descarta.
- **D-5 · El acceso y el grupo de Entra.** Recomendación: la maqueta usa **el
  mismo acceso que el circuito** y F-035 no toca Entra ni el catálogo del
  portal. Pregunta al humano: ¿«no existe grupo de Posventa» significa que
  `posventa-usuarios` es solo del piloto y hace falta un grupo de departamento,
  o `ARCHITECTURE.md:544` (`:578` en `54c0884`) está desactualizado? Según la respuesta, T10 corrige
  esa fila o anota el prerrequisito, y la tarjeta queda para `front-portal`.
- **D-6 · ¿Qué funciona y qué no?** Recomendación: **lo que lee y navega
  funciona sobre los datos de ejemplo** (filtros, selección, pestañas, abrir la
  ficha, abrir el panel de «no procede»); **lo que escribiría, enviaría o
  llamaría es placeholder**. Alternativa descartada: todo inerte — se valida
  peor el recorrido con Posventa y no ahorra casi nada.
- **D-7 · Dos ubicaciones discutibles.** «Aprobar las seleccionadas» de la
  bandeja va como **F-043** (operación en bloque) y no F-038; el registro sin
  firma (F-045) va en la sección `partes` y en la ficha, **no** en `index.html`
  (tocaría el circuito). Recomendación: como está.
- **D-8 · `azure-apps/`.** Recomendación: **no se toca en F-035**: no cambia
  ningún endpoint, tabla, variable ni grupo. La ampliación de alcance del
  proyecto se documenta en `azure-apps/postventa_incidencias.md` cuando F-036
  añada el primer endpoint nuevo. *(2026-09-25)*: sigue igual con el panel de
  volcado: enseñar el vocabulario de `sigrid/partes-reclamacion` no es
  consumirlo; `postventa-incidencias` pasa a consumidor en F-040, que ya
  consta en `azure-apps/sigrid_api.md` §10.
- **D-9 · Mutación de JavaScript.** Recomendación: aceptar la campaña con 0
  mutantes y la compensación manual de §11. Llevar a `arnes-base` la mutación
  de JavaScript sería trabajo de otro producto.
- **D-10 · Catálogos de Sigrid con códigos reales** *(nueva, 2026-09-25)*.
  Recomendación: los **catálogos generales** —estados de `conest`, tipos de
  reclamación, formas de comunicación y oficios— con sus **códigos y
  resúmenes reales** (`0002 · PRIMER LISTADO POSTVENTA`, `0143 · Carpintería
  de madera`), porque no son datos de nadie y son lo que Posventa reconoce
  al validar; **todo lo que identifica a alguien o a una obra** —obras,
  unidades, propietarios, personas, proveedores, códigos de parte,
  referencias, carpetas— **ficticio** (R24, §7.2). Alternativa: oficios y
  tipos también ficticios (`EJ01 · Fontanería (ejemplo)`) — más fácil de
  comprobar por test, peor para validar con Posventa.

> **Enmienda del 2026-10-05.** Entran **D-11** (dónde viven importar, bandeja
> y oficios), **D-12** (el rótulo «En construcción» y la portada sin
> cifras), **D-13** (los dos apuntes necesitan un dato del backend: ficha
> aparte) y **D-14** (dónde ve el humano el portal entero antes de
> publicar). Están en §16.13, con su recomendación.

### 13.1 · Acta de las decisiones del humano · 2026-09-25

Transmitidas por el líder. Entre comillas, las palabras literales del
humano; donde el líder transmite la respuesta sin cita, se dice. Las
recomendaciones de arriba se conservan tal cual, como premisa.

| | Respuesta del humano | Qué queda decidido | Dónde se aplica |
|---|---|---|---|
| **D-1** | «pagina aparte. esto que hemos hecho sera una pestaña de dicho portal» | El portal es una página aparte del circuito, **y el circuito pasa a ser una pestaña del portal** (la sección `partes`), no un enlace a una página ajena. Revisa la «consecuencia que el humano tiene que aceptar» de la recomendación: el circuito ya no queda solo «enlazado», queda **presentado como pestaña** por la barra común | §2, §4, §5.1, §5.7, §6.3; R44–R47 |
| **D-2** | «barra superior» | La navegación del portal es una **barra superior común**, visible también en el circuito. Del circuito al resto, pestaña nueva del navegador (R31 enmendado); del portal al circuito, la misma | §2, §4; R31, R44–R47 |
| **D-3** | «si» | **La portada `/` pasa a ser el portal.** Revierte la recomendación («no en F-035»). Diseño: el circuito se muda a `partes.html` con `git mv`; el portal ocupa `index.html`; siete líneas de test (la constante `INDEX`), nada más; la tarjeta del portal corporativo aterriza en el portal sin tocar `front-portal`. Opción de menos riesgo y alternativas descartadas (reescritura en la Static Web App, `<iframe>`, incrustar el marcado), en §2 | §1.2, §1.3, §2, §3; R1, R17, R30, R32, R35, R42, R43 |
| **D-4** | «si» | Se publica para que lo vea Posventa, **después de V1 y V2**, con `desplegar_front.ps1 -SoloFront` ejecutado por el humano tras el cierre y el merge a `dev`, y avisando a Posventa de que las pestañas nuevas son una maqueta y de que el circuito está en la pestaña «Partes firmados». Se comprueba con **V4** | `requirements.md` §3 (V4); `tasks.md`, tras T13 |
| **D-5** | «creo que existe» | Medido por el líder (solo lectura, `az ad group list`): existe el grupo de seguridad `posventa-usuarios` (7 miembros), el del piloto; y un grupo `Postventa` no de seguridad (9 miembros, probablemente el de Microsoft 365 del sitio). La fila de Entra ID de `docs/ARCHITECTURE.md` está desactualizada: **T10 la corrige**. Ni un GUID en ningún fichero. **Abierto**: ¿acceso con `posventa-usuarios` o ampliarlo al departamento? | §9; T10 |
| **D-6** | Acepta la recomendación (el líder lo transmite sin cita literal) | Funciona lo que lee y navega sobre los datos de ejemplo; placeholder lo que escribe, envía o llama | §5, §6 (sin cambios) |
| **D-7** | «ok» (el líder: «ok, como estaban») | Como estaba: «Aprobar las seleccionadas» es F-043. Consecuencia de D-1/D-3 que **se somete al humano**: el registro sin firma (F-045) ya no puede ir «en la sección `partes`» del portal, porque esa sección es ahora el circuito; va en la tarjeta «Partes firmados» de `inicio` y en la ficha, y sigue **sin** tocar el circuito | §5.1, §6.3 |
| **D-8** | «ok» (el líder: «ok, como estaban») | `azure-apps/` no se toca en F-035. D-3 no lo cambia: `azure-apps/postventa_incidencias.md` no describe rutas del front (medido: no nombra `index.html`), ni cambia un endpoint, tabla, variable o grupo | — |
| **D-9** | «¿por qué no mutamos javascript? sino como recomiendas» | **Queda la recomendación para F-035**: campaña con 0 mutantes y compensación a mano (§11, ahora ocho mutaciones). La mutación de JavaScript la registra **el líder, aparte, como propuesta del arnés** (candidata a `arnes-base`); no es trabajo de F-035 | §11; H-5 |
| **D-10** | «ok» (el líder: «ok, como estaban») | Catálogos generales de Sigrid con códigos reales; todo lo que identifica a alguien o a una obra, ficticio | §7.2, R24 (sin cambios) |
| Plantilla de impresión | Se queda para F-044 (el líder lo transmite sin cita literal) | **No se abre ni se convierte** en F-035. El pendiente de §5.6 no cambia | §5.6 |

#### Segunda ronda · 2026-09-25, tras ver la maqueta

Transmitida por el líder, con F-035 en `6bc4b6c` (review 2 APROBADA, sin
mergear, V1/V2 pendientes). Palabras literales del humano:

> «en lugar de que se abran las pestañas aparte, me gustaría que se abrieran
> en la misma ventana como en una web normal (para la maqueta vale así). lo
> que sí quiero es que el estilo sea como el de portal ruesma
> (ohana.ruesma.es). es un buen comienzo. cámbiale el estilo. además quiero
> que sea muy bonito y elegante»

Preguntado por el líder si el estilo alcanza también al circuito:

> «También el circuito entero»

| Tema | Respuesta del humano | Qué queda decidido | Dónde se aplica |
|---|---|---|---|
| Navegación | «me gustaría que se abrieran en la misma ventana como en una web normal (para la maqueta vale así)» | **En la maqueta, como está** (D-2: desde el circuito, pestaña aparte; dentro del portal, misma ventana). Regla para las fichas que conviertan secciones en reales: misma ventana, con guardia | §2 (recuadro), §7.3 paso 4; R48 |
| Estilo | «que el estilo sea como el de portal ruesma (ohana.ruesma.es) […] cámbiale el estilo. además quiero que sea muy bonito y elegante» | Identidad visual de `front-portal` (burdeos `#9f2842`, gris acero `#7b868c`, trama de plano, Bricolage Grotesque y Archivo, radios 16/10 px, botones en píldora, barra con logotipo), aplicada con tokens compartidos | §15; R49–R58, R60, R61 |
| Alcance del estilo | «También el circuito entero» | El circuito en producción cambia **solo de presentación**: valores de `class`, cuatro `<link>` en la cabecera y la barra. Ni lógica, ni directivas, ni ids, ni configuración, ni backend; ningún test del circuito se toca | §15.2, §15.7; R59, R33 enmendado |
| Valoración | «es un buen comienzo» | La estructura de la maqueta (secciones, datos, placeholders) no cambia | — |

## 14 · Hallazgos (fuera de alcance, para el líder)

- **H-1**: `docs/ARCHITECTURE.md:544` (`:578` en `54c0884`) contradice lo registrado del despliegue de
  F-010 sobre el grupo `posventa-usuarios` (D-5).
- **H-2**: el `README.md` del front, «Lo que este front NO hace», sigue diciendo
  que el front no cierra en Sigrid, que es F-008/F-009 y depende de otro
  repositorio (F-009 y F-012 están hechas); y el pie de `index.html:596-597`
  dice que recargar pierde el trabajo «(F-019)», texto a comprobar tras F-019.
  F-035 **no los corrige** (R30 prohíbe cambiar líneas de `index.html`); se
  anotan para una ficha de limpieza.
- **H-3** *(2026-09-25)*: **en qué estado nace un parte dado de alta.** La
  captura del alta manual enseña el parte recién creado en `3 (PTE :
  PENDIENTE)` (`docs/referencia/04_alta_incidencia_sigrid.md` §3), mientras
  que `sigrid-api` lo crea en el estado inicial de la serie, `SAT`
  (`azure-apps/sigrid_api.md` §9.2), y **no** pasa a `PTE` porque eso crea
  tareas y envía correos (§8.9, «Lo que NO hace»). O Posventa lo pasa a mano
  a `PTE` después, o el escritorio lo hace solo al crear. Es de F-040, no de
  F-035: la maqueta no enseña el estado de los `creado` y lo deja como
  pendiente (§5.3).
- **H-1, resuelto el 2026-09-25** (D-5): el grupo existe; T10 corrige la fila.
- **H-2, precisión del 2026-09-25** (D-3): con la mudanza, `index.html:596-597`
  pasa a ser `partes.html` en las mismas líneas desplazadas por la barra;
  sigue sin corregirse en F-035 (R43 solo permite añadir la barra y cambiar
  la línea 1).
- **H-4** *(2026-09-25)*: **la tarjeta del portal corporativo describe solo
  el circuito.** En `front-portal`, título «Partes de Posventa» y una
  descripción de lectura y archivo de partes; con D-3 abre el portal entero.
  Propuesta para quien lleve `front-portal` (no se toca desde aquí): título
  «Posventa» y descripción «Portal de posventa: incidencias, bandeja de
  revisión, partes firmados y coste. Las secciones nuevas son una maqueta en
  validación.» T10 la deja escrita en `docs/DESPLIEGUE.md` §6.
- **H-5** *(2026-09-25)*: **mutación de JavaScript** (D-9). El humano
  pregunta por qué no se muta JavaScript. Es una capacidad del arnés, no de
  este proyecto: el líder la registra aparte como propuesta del arnés
  (`arnes-base`). F-035 no la espera.
- **H-6** *(2026-09-25, segunda ronda)*: **Tailwind va por su CDN de juego y
  sin versión fija** (`https://cdn.tailwindcss.com`, en las dos páginas desde
  antes de F-035), mientras Alpine sí va fijado (F-007 R36). Tailwind
  desaconseja ese CDN en producción, y un cambio de versión puede mover su
  hoja base (el *preflight*) por debajo de nuestras clases. F-035 **no lo
  cambia** (sería tocar la cabecera del circuito más allá de R59); se
  defiende escribiendo las reglas de componente con especificidad suficiente
  (§15.9). Propuesta para una ficha aparte: fijar la versión o compilar
  Tailwind.
- **H-7** *(2026-09-25, segunda ronda)*: el `css/styles.css` de la base
  declaraba `--ruesma-burdeos: #ad1833`, **otro burdeos** que el de la marca
  (`#9f2842`, el de `front-portal` y el del propio logotipo) y que **nadie
  usaba** (medido con `grep` en el front). Se retira al poner los tokens
  `--rs-*`.

## 15 · Identidad visual Ruesma (segunda ronda, 2026-09-25)

Decisión del humano tras ver la maqueta (acta en §13.1, «Segunda ronda»):
el estilo del portal corporativo, «muy bonito y elegante», en el portal **y
en el circuito entero**. Referencia, leída **solo en lectura**:
`front-portal/public/index.html` y `front-portal/public/assets/css/styles.css`
(commit `01fb1aa` de ese repositorio). No se copia su hoja: se toma su
lenguaje y se escribe como tokens y componentes propios, con nombres en
castellano y prefijo `rs-`.

### 15.1 · Qué significa «muy bonito y elegante», en criterios comprobables

1. **Una sola voz visual**: todo color, sombra y radio sale de un token del
   `:root` (R49). Las dos páginas comparten hoja (`css/styles.css`), así que
   la barra, los botones y los paneles son **los mismos** en las dos.
2. **Tipografía con jerarquía**: Bricolage Grotesque para titulares y
   cifras grandes (peso 700–800, interletrado negativo), Archivo para el
   texto (400–600); cifras tabulares en tablas e importes; códigos en
   monoespaciada (R50).
3. **Superficie de plano**: lienzo gris muy claro con la **trama de plano**
   de `front-portal` (cuadrícula de 34 px en acero al 22 % y un halo burdeos
   muy suave arriba a la derecha); sobre ella, paneles blancos con borde de
   1 px, radio 16 px (10 px en controles) y sombra suave.
4. **El color con intención**: el burdeos es **la marca y la acción
   principal** —logotipo, pestaña actual, botón principal, foco, acentos—, y
   **nunca un estado**. Los estados llevan su semántica (verde hecho, ámbar
   atención, rojo error, azul en curso, acero neutro) y **siempre texto**
   (R57): el color no es la única pista.
5. **Aire**: escala de espaciado 4 · 8 · 12 · 16 · 24 · 32 · 48 px, ancho
   de lectura contenido (`--rs-ancho: 1180px`) y márgenes que crecen con la
   pantalla (`clamp`), como `front-portal`.
6. **Movimiento sobrio** (R55): solo realimentación (color, sombra, una
   elevación de 1–4 px) y, en el portal, una entrada escalonada de las
   tarjetas de `inicio`; nada en bucle salvo el pulso que ya tenía el
   circuito; todo se apaga con `prefers-reduced-motion`.
7. **Accesible** (R53, R54): contraste AA medido, foco siempre visible,
   pestañas y regiones con su semántica.
8. **Honesto** (R56): lo que es maqueta se sigue viendo maqueta —borde
   discontinuo reservado, aviso permanente en su propio color— y lo que
   funciona se ve más firme que nunca.

No entra: cambiar textos, datos, secciones o comportamiento; modo oscuro
(`front-portal` tampoco lo tiene); capturas versionadas.

### 15.2 · El circuito en producción: qué fijan sus tests del HTML (medido sobre `6bc4b6c`)

| Test | Qué lee de `partes.html` | ¿Lo toca un cambio de estilo? |
|---|---|---|
| `test_f007_estaticos.py` (`:109-166`, `:172-289`, `:337`) | Los `<script src>`: sitio, orden, `defer`, versión de Alpine; almacenamiento del navegador sin comentarios | **No**: las cuatro `<link>` nuevas no son scripts |
| `test_f009_front.py` (`:102-219`, `:288`) | Textos y expresiones (`x-show="!usuario.usuarioOid"`, `resultado.incidencia`, `cargarUsuario()`) y ausencias | **No** |
| `test_f012_front.py` (`:198-293`) | Expresiones (`parte.estado === 'adjuntado'`) y textos («Reintentar el cierre», «adjunto en Sigrid») | **No** |
| `test_f025_front.py` (`:312-594`) | Recuentos (`pedirConfirmacionArchivo()` una vez), bloques entre marcas de texto (`<section` … `x-text="tituloDeFase()"`, `Archivar y cerrar</h2>` … `</section>`), `:key` | **No**, mientras ni se reordene ni se reescriba nada (R59) |
| `test_f026_autoguardado.py` (`:231-371`) | Orden de scripts; bloques del detalle; y **`:280`: exige `text-(red|rose|amber)-N00` en el `<p>` del fallo**, entre `estadoAutoguardado === 'fallo'` y `</p>` | **Sí, una clase**: es la **única** clase estática del circuito que fija un test. Se **conserva** `text-red-800` en ese `<p>` (junto a `rs-aviso rs-aviso--error`) y su `class` sigue **después** del `x-show`. El test no se toca |
| `test_f026_front.py` (`:236-345`) | Gestos en el detalle y no en la lista; `ring` en la línea del `:class` del aprobado (`:296`) | **No**: vive en un `:class`, que no se toca |
| `test_f028_front.py` (`:131-146`, `:257-708`) | Grupos `:class="{…}"` del semáforo, `line-through` (`:502`) y `ring` (`:536`) —todos dentro de `:class`—, candado, condiciones de `<template x-if>`, `x-text`/`x-html` | **No**: todo son directivas |
| `test_f031_front.py`, `test_f007_dev_server.py` | `js/app.js`; raíces temporales propias | **No** |
| `test_f007_sin_datos_reales.py` | Barre `.html`, `.css`, `.js`… del árbol (DNI, base64) | **No**, con R60 (sin `data:`); los `.svg` quedan fuera de su lista, por eso R52 los barre aparte |
| `tests_js/` del circuito (15 ficheros) | Ninguno lee HTML (`reintento_vaciado.test.js:47` nombra `index.html` en un comentario) | **No** |

Tests **de F-035** que sí cambian (son de esta feature, no del circuito):
`test_f035_portal.py::test_f035_r30_r43_partes_html_es_el_index_de_la_base_con_su_ruta_y_la_barra`
(la comparación con `difflib` línea a línea se sustituye por la guardia de
R59, §15.8) y `::test_f035_r33_no_se_modifica_nada_del_circuito` (admite
`M services/postventa-front/css/styles.css`). R31, R43 (los nueve scripts),
R45 y R47 siguen igual: `<img>`, `<span>` y `<p>` no están en la lista negra
de R45, y el `<nav>` sigue sin directivas. `tests_js/portal.test.js` (R44)
tampoco cambia: `pestanasDe` filtra enlaces y `aria-current` **por la
etiqueta de la sección**, y el logotipo no tiene esa etiqueta.

**Conclusión: ningún test del circuito cambia** y la guardia de R32 sigue
exigiendo exactamente las siete líneas `INDEX`. Si durante T16 apareciera un
test del circuito que exigiera otra cosa, **se para**: no se toca el test, se
anota en `progress/current.md` y se vuelve a proponer.

### 15.3 · Los tokens (`:root` de `css/styles.css`, R49)

| Token | Valor | Origen en `front-portal` | Uso |
|---|---|---|---|
| `--rs-burdeos` | `#9f2842` | `--brand` | Marca, acción principal, pestaña actual, foco, acentos |
| `--rs-burdeos-fuerte` | `#7a1e33` | `--brand-strong` | Hover de la acción principal |
| `--rs-burdeos-suave` | `#f7eaee` | `--brand-soft` | Fondo de la pestaña actual y del hover de los secundarios |
| `--rs-acero` | `#7b868c` | `--steel` | **Solo no texto**: bordes de campo, iconos, separadores (3,7:1 sobre blanco) |
| `--rs-acero-300` | `#aab1b6` | `--steel-300` | Índices decorativos de las tarjetas (`aria-hidden`) |
| `--rs-acero-100` | `#dfe2e4` | `--steel-100` | Fondo de chips neutros y de lo deshabilitado |
| `--rs-acero-texto` | `#5d676d` | **nuevo** | El gris **de texto**: `--steel` no llega a AA (§15.6) |
| `--rs-tinta` | `#1d2024` | `--ink` | Texto principal |
| `--rs-tinta-suave` | `#4a4f55` | `--ink-soft` | Texto secundario |
| `--rs-papel` | `#ffffff` | `--paper` | Paneles, barra |
| `--rs-lienzo` | `#f3f4f5` | `--canvas` | Fondo de página, cabeceras de tabla |
| `--rs-linea` | `rgba(123, 134, 140, 0.22)` | `--line` | Bordes de panel, separadores, trama |
| `--rs-linea-fuerte` | `rgba(123, 134, 140, 0.4)` | `--line-strong` | Separador de la barra, bordes de secundarios |
| `--rs-halo` | `rgba(159, 40, 66, 0.06)` | (su `radial-gradient` del `body`) | Halo burdeos de la trama |
| `--rs-velo` | `rgba(255, 255, 255, 0.85)` | (su `.topbar`, al 82 %) | Fondo translúcido de la barra |
| `--rs-rayado` | `rgba(123, 134, 140, 0.12)` | (su `.card__veil`) | Rayado del placeholder y del aviso de maqueta |
| `--rs-ok` / `--rs-ok-suave` | `#047857` / `#ecfdf5` | nuevo (el `emerald` del circuito) | Hecho, aprobado, en producción |
| `--rs-atencion` / `--rs-atencion-suave` | `#92400e` / `#fffbeb` | nuevo (`amber`) | Atención, pendientes, aviso de maqueta |
| `--rs-error` / `--rs-error-suave` | `#b91c1c` / `#fef2f2` | nuevo (`red`) | Error, rechazo, acción irreversible |
| `--rs-info` / `--rs-info-suave` | `#0369a1` / `#f0f9ff` | nuevo (`sky`) | En curso, información |
| `--rs-sombra-sm` | `0 1px 2px rgba(29, 32, 36, 0.05)` | `--shadow-sm` | Paneles y tarjetas en reposo |
| `--rs-sombra-md` | `0 18px 40px -22px rgba(29, 32, 36, 0.35)` | `--shadow-md` | Tarjeta al pasar, aviso flotante |
| `--rs-sombra-marca` | `0 22px 48px -24px rgba(159, 40, 66, 0.55)` | `--shadow-brand` | Botón principal |
| `--rs-fuente-titulos` | `'Bricolage Grotesque', Georgia, serif` | `--font-display` | Titulares, cifras grandes, etiqueta de la barra |
| `--rs-fuente-texto` | `'Archivo', system-ui, sans-serif` | `--font-body` | Todo el texto |
| `--rs-fuente-mono` | `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` | (su `code`) | Códigos, hashes, orígenes de campo |
| `--rs-radio` / `--rs-radio-sm` / `--rs-radio-pildora` | `16px` / `10px` / `999px` | `--radius`, `--radius-sm`, botones | Paneles; controles; botones, chips y pestañas |
| `--rs-ancho` | `1180px` | `--maxw` | Ancho máximo del contenido |
| `--rs-curva` / `--rs-duracion` | `cubic-bezier(0.2, 0.8, 0.2, 1)` / `180ms` | `--ease` | Toda transición |
| `--rs-trama` | `34px` | (su `background-size`) | Paso de la trama de plano |

Los tonos de estado son **los mismos** que el circuito ya usa en sus
directivas `:class` (Tailwind `emerald`, `amber`, `red`, `sky`), para que lo
que pintan las directivas —que no se tocan— y lo que pintan los componentes
casen. Fuera del `:root`, los dos CSS solo escriben colores, sombras y radios
con `var(--rs-…)` (o `transparent`, `currentColor`, `inherit`, `0` y `50 %`):
es lo que comprueba R49. `--ruesma-burdeos: #ad1833` se retira (H-7).

### 15.4 · Ficheros

**A crear**

| Ruta | Qué es | Cómo se verifica |
|---|---|---|
| `services/postventa-front/img/logo-ruesma.svg` | Copia **byte a byte** de `front-portal/public/assets/img/logo-ruesma.svg`. SHA-256 `1dfc97aa813fa45433191aaf6f3dff9d931b0cdbacc96933becbbb0349179959`, 2 242 bytes. Revisado en esta spec: solo `<svg>`, `<defs><style>` con dos rellenos (`#9f2842`, `#7b868c`), 3 `<rect>` y 5 `<path>`; **sin** metadatos, textos, scripts, enlaces, `data:` ni rutas de autor. Nada sensible | R52 |
| `services/postventa-front/img/favicon.svg` | Copia byte a byte de `front-portal/public/assets/img/favicon.svg`. SHA-256 `006623f03ec06e3570db7574917baf3de146fba6ba1e970228b3f04e7348926e`, 336 bytes: 4 `<rect>` en `#9f2842`, `#ffffff` y `#7b868c` | R52 |

`img/` y no `assets/img/`: el front ya sirve `css/` y `js/` en la raíz. El
despliegue sube la carpeta entera (§1.3) y `staticwebapp.config.json` ya
declara `.svg` como `image/svg+xml`.

**Las cuatro `<link>` de la cabecera** (R50, R59), **exactas**, en este
orden, justo **antes** de `<link rel="stylesheet" href="css/styles.css">`, en
las dos páginas (valores de atributo tal como los devuelve `html.parser`):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Archivo:wght@400;500;600;700&display=swap">
<link rel="icon" type="image/svg+xml" href="img/favicon.svg">
```

Las mismas familias que `front-portal`, con el peso 600 de Bricolage (su
etiqueta de la barra lo usa y su URL no lo pide) y el 700 de Archivo;
`display=swap` para que el texto se vea con la fuente de reserva mientras
llega. Por qué por Google Fonts y no alojadas: §15.10.

**A modificar**

| Ruta | Qué cambia |
|---|---|
| `css/styles.css` | Pasa a ser **la hoja de la marca**, compartida (ya la cargan las dos páginas): (1) tokens; (2) base —`body` con `--rs-fuente-texto`, `--rs-tinta` y el lienzo con la trama; `img { max-width: 100% }`—; (3) barra común (`rs-barra*`, `rs-pestana`); (4) componentes compartidos: `rs-contenedor`, `rs-titulo`, `rs-subtitulo`, `rs-entradilla`, `rs-rotulo`, `rs-panel` (y `--suave`, `--atencion`, `--destacado`, `--tabla`, `--lista`), `rs-btn` (y `--primario`, `--secundario`, `--texto`, `--ok`, `--peligro`, `--compacto`), `rs-campo`, `rs-chip` (y `--ok`, `--atencion`, `--neutro`), `rs-aviso` (y `--error`, `--atencion`, `--info`, `--compacto`), `rs-nota` (y variantes), `rs-enlace`, `rs-mono`, `rs-tabla`, `rs-pie`; (5) los del circuito: `rs-cuerpo`, `rs-cabecera`, `rs-estado-servicio`, `rs-principal`, `rs-zona`, `rs-progreso`, `rs-fila`, `rs-punto`, `rs-paso`, `rs-visor`, `rs-resumen`; (6) foco (R54); (7) `prefers-reduced-motion` (R55). Sin `!important`, `@import` ni `data:` (R60) |
| `css/portal.css` | Lo que solo usa el portal: `.placeholder` y `.placeholder-ficha` redibujados con tokens (§6.1, recuadro), aviso de maqueta, portada (`rs-ceja`, `rs-hero`, `rs-recorrido`), tarjetas (`rs-rejilla`, `rs-tarjeta*` con su entrada escalonada), chips `[data-estado]` (R57), pestañas de la ficha (`[role="tab"][aria-selected="true"]`), datos de la ficha (`rs-datos`, `rs-origen`), `rs-pendiente`, `rs-carta` (vista previa del correo), volcado (`rs-contadores`), estados vacíos (`rs-vacio`, R58) y aviso flotante. Conserva `[x-cloak]` (la única `!important` admitida) |
| `index.html` (portal) | Las cuatro `<link>`; la barra con el logotipo (§15.5); clases `rs-*` en todas las secciones; las directivas `:class` de las pestañas de la barra y de la ficha **se quitan** (las pinta `aria-current` / `aria-selected`, que ya estaban); las de fila abierta pasan a `'rs-fila--abierta'`; los chips ganan `:data-estado`; los estados vacíos de R58 (`data-vacio` con `x-show` sobre la lista filtrada que el componente ya expone). **Ni un `js/*.js` cambia** |
| `partes.html` (circuito) | **Solo**: las cuatro `<link>`, la barra (F-035) con el logotipo, y **valores de `class`** según §15.7. Nada más (R59) |
| `README.md` del front | Sección «Identidad visual Ruesma (F-035)» (R61) y la regla de R48 en la sección de la maqueta |
| `docs/ARCHITECTURE.md` | En la sección del portal: la regla de R48 (misma ventana cuando una sección es real, y que la ficha que lo active resuelve la remesa en curso) |
| `tests/test_f035_portal.py` | R59 sustituye a la comparación con `difflib`; R33 admite `css/styles.css`; tests nuevos de R49–R56, R58, R60, R61 (§15.8) |
| `tests/test_f035_placeholders_vivos.py` (raíz) | R48, con su control |
| `tests_js/portal.test.js` | R57 |

**No se tocan**: `js/*.js` (los doce), `staticwebapp.config.json`,
`dev_server.py`, `dev_front.ps1`, `infra/*`, `harness/*`,
`services/postventa-api/`, los tests del circuito, `azure-apps/` (no cambia
nada de lo que el proyecto expone ni consume) y `front-portal` (solo se lee).

### 15.5 · Sección a sección

**La barra superior (las dos páginas, R51).** Pegajosa arriba
(`position: sticky`, por encima del aviso flotante), fondo papel al 85 % con
desenfoque (`backdrop-filter`) y una línea inferior `--rs-linea`, como la de
`front-portal`. A la izquierda la marca: logotipo de 28 px de alto, separador
de 1 × 24 px en `--rs-linea-fuerte` y «POSVENTA» en Bricolage 600,
mayúsculas, interletrado 0,06 em, `--rs-acero-texto`. A la derecha las ocho
pestañas en píldora (Archivo 500, `--rs-tinta-suave`); al pasar, fondo
`--rs-burdeos-suave` y texto `--rs-burdeos`; la **actual**, por
`[aria-current="page"]`, con ese mismo fondo, texto burdeos y peso 600. Por
debajo de 560 px la etiqueta se oculta y las pestañas se desplazan en
horizontal dentro de la barra, con un desvanecido en los bordes. En el
circuito, la leyenda de R47 va en una segunda línea (`rs-barra__leyenda`,
0,78 rem, `--rs-acero-texto`, precedida de un punto ámbar decorativo). Mismo
marcado en las dos páginas salvo los enlaces y la pestaña actual:

```html
<nav data-barra-portal aria-label="Secciones de posventa" class="rs-barra">
  <div class="rs-barra__fila">
    <span class="rs-barra__marca">
      <img class="rs-barra__logo" src="img/logo-ruesma.svg" alt="Construcciones Ruesma">
      <span class="rs-barra__sep" aria-hidden="true"></span>
      <span class="rs-barra__etiqueta">Posventa</span>
    </span>
    <div class="rs-barra__pestanas">
      <!-- circuito: <a href="./#/inicio" target="_blank" rel="noopener" class="rs-pestana">Inicio</a> …
           y <span aria-current="page" class="rs-pestana">Partes firmados</span>
           portal:   <a href="#/inicio" class="rs-pestana" :aria-current="…">Inicio</a> …
           y <a href="partes.html" class="rs-pestana">Partes firmados</a> -->
    </div>
  </div>
  <!-- solo en el circuito: <p class="rs-barra__leyenda">Las demás pestañas son una maqueta…</p> -->
</nav>
```

La marca **no es un enlace** en ninguna de las dos: en el circuito, un enlace
más rompería R31 (sus enlaces son exactamente los siete de la maqueta) y, en
la misma ventana, perdería la remesa.

**Aviso de maqueta (portal, R13, R56).** Banda a todo el ancho bajo la barra,
fondo `--rs-atencion-suave` con un rayado diagonal muy tenue —el mismo
lenguaje que el placeholder, a propósito: «esto es maqueta»—, texto
`--rs-atencion`; «Esto es una maqueta.» en 600 y la muestra de placeholder a
continuación. **Nunca burdeos**: la marca no avisa de nada.

**Portada (`inicio`).** Como el *hero* de `front-portal`: una ceja en píldora
(«Posventa · maqueta del ciclo», 0,74 rem, mayúsculas, borde
`--rs-linea-fuerte`, fondo papel), el titular «Portal de posventa» en
Bricolage 800 con `clamp(2rem, 5vw, 3.2rem)` e interletrado −0,02 em, con
«posventa» en burdeos (`<em>`), y la entradilla actual en 1,05 rem
`--rs-tinta-suave`, 60 caracteres de ancho. El recorrido
«Entrada → Revisión → … → Coste» pasa a ser una **lista ordenada**
(`<ol class="rs-recorrido">`) de siete píldoras numeradas 01–07 unidas por
una línea fina; los enlaces y sus destinos **no cambian**.

> **Enmienda del 2026-10-06 (R84).** El recorrido sale de la portada y pasa
> a ser la **tira bajo la barra** de las cuatro páginas, con el paso actual
> marcado; sus reglas se mudan de `css/portal.css` a `css/styles.css`.
> Ver §16.16.

**Tarjetas de `inicio`.** Rejilla `repeat(auto-fill, minmax(260px, 1fr))`;
cada `rs-tarjeta`: papel, borde `--rs-linea`, radio 16, sombra pequeña,
índice «01…06» arriba a la derecha (Bricolage 700, `--rs-acero-300`,
`aria-hidden`), rótulo, **cifra** en Bricolage 800 a 2,6 rem con cifras
tabulares, nota en `--rs-acero-texto` y un pie con la llamada («Ver la
bandeja →») en burdeos 600 cuya flecha avanza 4 px al pasar. Al pasar, una
barra de acento burdeos de 3 px crece de izquierda a derecha, la tarjeta sube
3 px y gana `--rs-sombra-md`. Un chip arriba dice qué es cada una:
«Maqueta» (neutro) en las cinco de ejemplo y **«En producción»** (`--ok`) en
«Partes firmados», que además lleva el único **botón principal burdeos** de
la portada («Abrir el circuito de partes firmados», R46) junto al placeholder
hueco de F-045: el contraste entre lo que funciona y lo que no es máximo.
Entrada escalonada de 60 ms entre tarjetas (420 ms, opacidad y 10 px de
desplazamiento), sin JavaScript (`:nth-child`), apagada con
`prefers-reduced-motion`.

**Cabecera de cada sección.** `rs-titulo` (Bricolage 700, 1,9 rem) y una
entradilla; las acciones de la sección, alineadas a la derecha en pantallas
anchas.

**Tablas (`rs-tabla`, dentro de `rs-panel rs-panel--tabla`).** El panel
desplaza en horizontal su tabla, así que la página nunca lo hace (V1-e).
Cabecera en 0,72 rem, 600, mayúsculas, interletrado 0,08 em, `--rs-acero-texto`
sobre `--rs-lienzo`; filas de 0,9 rem separadas por `--rs-linea`; al pasar,
fondo lienzo; la fila abierta (`rs-fila--abierta`) con un filete burdeos de
3 px a la izquierda. Códigos en monoespaciada 0,82 rem; importes alineados a
la derecha con cifras tabulares; «sin enlazar» en cursiva `--rs-acero-texto`
(R22). Casillas con `accent-color: var(--rs-burdeos)`.

**Chips de estado (R57).** Píldora de 0,72 rem, 600, con el texto de siempre
(código · resumen, o la etiqueta del volcado) y el color por
`[data-estado]`: `conest` — `SAT` atención, `PTE` info, `TER` ok, `CER`
neutro relleno, `NPR` neutro de contorno; revisión — `nueva` info, `editada`
atención, `aprobada` ok, `descartada` neutro de contorno, `volcada` neutro;
volcado — `previsto` info, `creado` ok, `idempotente` neutro, `rechazado`
error, `no_procesado` atención. «duplicada» es una marca, no un estado:
`rs-chip rs-chip--atencion`. Fondo suave y texto fuerte del mismo tono
(pares de §15.6); el neutro, `--rs-tinta-suave` sobre `--rs-acero-100`.

**Filtros y campos.** En un panel lienzo sobre la tabla; `rs-campo` con radio
10, borde `--rs-acero` (3,7:1, suficiente para el borde de un control) y foco
burdeos.

**Ficha de incidencia.** Cabecera en panel: código en monoespaciada
`--rs-acero-texto`, descripción corta en Bricolage 700 a 1,6 rem, chip de
estado y obra · unidad. Pestañas `role="tab"` **subrayadas**: 2 px burdeos
bajo la activa (`[aria-selected="true"]`), sin fondo. «Datos» como rejilla de
definición (`rs-datos`): etiqueta en 0,72 rem mayúsculas `--rs-acero-texto`,
valor en 0,95 rem tinta, y el origen del campo (R25: `con.cod`,
`conext[RCPCLI]`, `propio`…) como chip diminuto monoespaciado de contorno
(`rs-origen`); los tres bloques con su subtítulo y una línea. «sin completar»
en cursiva `--rs-acero-texto`; cada «Pendiente: …» como `rs-pendiente`
(fondo atención suave, filete de 3 px a la izquierda, texto atención).

**Paneles** (detalle de la bandeja, capítulo, volcado, no procede).
`rs-panel` con cabecera propia —título Bricolage 600 a 1,1 rem y «Cerrar»
como `rs-btn--texto`— y aparición de 200 ms (opacidad y 6 px). El **volcado**:
dos paneles con su chip («Simulación» info, «Volcado hecho» ok) y el resumen
por estado como fila de contadores (cifra en Bricolage + etiqueta);
«provisional» en cursiva junto al código. **No procede**: filete de atención
a la izquierda; la vista previa del correo como `rs-carta` —papel, borde,
radio 10, cabecera «Para / Asunto» en rejilla con etiquetas acero, cuerpo a
0,95 rem con interlineado 1,6—; «En pruebas nunca sale un correo a un cliente
real» como `rs-aviso rs-aviso--info`.

**Estados vacíos (R58).** `rs-vacio`: bloque centrado, 2,5 rem de relleno,
fondo lienzo, radio 16, borde **continuo** `--rs-linea` (lo discontinuo es de
los placeholders), frase en `--rs-tinta-suave` («Ninguna incidencia de
ejemplo cumple esos filtros.») y una segunda en `--rs-acero-texto` («Prueba a
quitar algún filtro.»). En incidencias, bandeja e impresión. Los «Sin cambios
… todavía» que ya existen, en su variante de una línea.

**Aviso del placeholder pulsado (R11).** Tarjeta flotante abajo, papel,
filete de atención de 3 px, radio 16, `--rs-sombra-md`; «Entendido» como
`rs-btn--secundario rs-btn--compacto`; aparece en 180 ms. La región
`role="status"` no cambia.

**Botones (las dos páginas).** `rs-btn`: píldora, Archivo 600 a 0,92 rem,
relleno 0,6 × 1,2 rem. `--primario`: burdeos, texto papel,
`--rs-sombra-marca`; al pasar `--rs-burdeos-fuerte` y −1 px. `--secundario`:
papel, borde `--rs-acero`, texto tinta; al pasar borde y texto burdeos sobre
`--rs-burdeos-suave`. `--texto`: sin borde, `--rs-acero-texto`, al pasar
burdeos. `--ok`: `--rs-ok`. `--peligro`: `--rs-error`. `--compacto`:
0,35 × 0,85 rem a 0,82 rem. `:disabled`: `--rs-acero-100`, texto
`--rs-acero-texto`, sin sombra, `cursor: not-allowed` (lo deshabilitado está
exento de AA). **Una sola acción principal por vista.**

**Pie.** Como `front-portal`: línea superior, 0,8 rem, `--rs-acero-texto`.

### 15.6 · Accesibilidad (R53, R54, R55)

Contraste WCAG medido con los valores de §15.3 (el test lo recalcula del
`:root`):

| Texto / fondo | Contraste | Mínimo |
|---|---|---|
| `--rs-tinta` / `--rs-papel` · `--rs-lienzo` | 16,35 · 14,85 | 4,5 |
| `--rs-tinta-suave` / `--rs-papel` · `--rs-lienzo` · `--rs-acero-100` | 8,27 · 7,51 · 6,35 | 4,5 |
| `--rs-acero-texto` / `--rs-papel` · `--rs-lienzo` | 5,79 · 5,26 | 4,5 |
| `--rs-papel` / `--rs-burdeos` · `--rs-burdeos-fuerte` (botón principal) | 7,35 · 10,19 | 4,5 |
| `--rs-burdeos` / `--rs-papel` · `--rs-lienzo` · `--rs-burdeos-suave` (enlaces, pestaña actual) | 7,35 · 6,68 · 6,29 | 4,5 |
| `--rs-papel` / `--rs-ok` · `--rs-error` (botones) | 5,48 · 6,47 | 4,5 |
| `--rs-ok` / `--rs-ok-suave` | 5,21 | 4,5 |
| `--rs-atencion` / `--rs-atencion-suave` | 6,84 | 4,5 |
| `--rs-error` / `--rs-error-suave` | 5,91 | 4,5 |
| `--rs-info` / `--rs-info-suave` | 5,57 | 4,5 |
| **No texto**: `--rs-acero` / `--rs-papel` · `--rs-lienzo` (borde de campo); `--rs-burdeos` / `--rs-papel` (foco) | 3,73 · 3,39; 7,35 | 3 |

Descartado por la medida: `--rs-acero` como texto (3,73 sobre blanco; es lo
que `front-portal` usa en sus textos pequeños) y `--rs-acero-texto` sobre
`--rs-acero-100` (4,45): por eso el chip neutro lleva `--rs-tinta-suave`.

> **Enmienda del 2026-10-06 (O17-2, review del bloque 17).** De esta tabla
> sale la **lista blanca** de R53 enmendado: fuera del `:root`, la propiedad
> `color` solo puede llevar `inherit`, `currentColor` o uno de los tokens
> que esta tabla mide como texto (columna izquierda de las filas de texto),
> más `--rs-burdeos-fuerte`. Única excepción: `--rs-acero-300` en
> `.rs-tarjeta__indice`, decorativo y con `aria-hidden="true"`. Recuento
> de los `color:` de las dos hojas sobre `6106c5c`: `--rs-acero-texto`
> 30, `--rs-tinta-suave` 21, `--rs-tinta` 20, `--rs-atencion` 11,
> `--rs-burdeos` 11, `--rs-info` 6, `--rs-error` 4, `--rs-ok` 4,
> `--rs-papel` 3, `--rs-burdeos-fuerte` 2, `--rs-acero-300` 1 (el índice)
> e `inherit` 1. Si una regla nueva necesita otro token como texto, primero
> entra su par en esta tabla, medido, y después en la lista. Test: T51.

- **Foco (R54)**: `:focus-visible` con contorno de 2 px `--rs-burdeos` y
  separación de 2 px en enlaces, botones, campos, `summary` y pestañas; en
  los botones rellenos burdeos, separación de 3 px para que el contorno se
  vea fuera del relleno. Ninguna regla quita el contorno sin poner otro.
- **Movimiento (R55)**: transiciones de 180 ms (`--rs-duracion`), como
  mucho 250 ms, solo sobre `color`, `background-color`, `border-color`,
  `box-shadow`, `opacity` y `transform`. Animaciones de entrada solo en
  `css/portal.css`. `@media (prefers-reduced-motion: reduce)` en **las dos**
  hojas deja `transition: none` y `animation: none` en todo, incluido el
  pulso del circuito (`rs-paso`).
- **Semántica**: el logotipo con `alt`; el separador `aria-hidden`; la
  pestaña actual por `aria-current`; las de la ficha por `aria-selected`
  (ya estaban); los índices decorativos `aria-hidden`; el color nunca es la
  única pista (R57).

### 15.7 · El circuito: solo presentación (R59, R60)

**Reglas.**

1. En `partes.html` solo cambian **valores de `class`** (más las cuatro
   `<link>` y la barra, que son de F-035). Ni una directiva (`x-*`, `@*`,
   `:*`), ni un `id`, `type`, `data-*`, `aria-*`, ni un texto, ni un
   comentario, ni el orden de atributos o elementos.
2. Las **directivas `:class` se quedan como están**, con sus utilidades de
   Tailwind: son los colores de **estado** (semáforo, dudoso, arrastrando,
   parte abierto) y los fijan los tests de F-026 y F-028. Como el CDN de
   Tailwind inyecta sus utilidades **después** de nuestra hoja, a igual
   especificidad ganan ellas: justo lo que se quiere (el estado manda sobre
   el aspecto por defecto del componente).
3. En un mismo elemento no se mezclan una clase `rs-*` y una utilidad de
   Tailwind **que fije la misma propiedad** (color, fondo, borde, radio,
   relleno, tipografía): ganaría la utilidad. Las utilidades de maquetación
   (`flex`, `grid`, `gap-*`, `mt-*`, `ml-auto`, `truncate`, `lg:col-span-*`…)
   se pueden quedar. Excepción documentada: `text-red-800` en el `<p>` del
   fallo del autoguardado (§15.2), que coincide con el tono de
   `rs-aviso--error`.
4. Las reglas de fondo y borde de `rs-btn--*` se escriben con especificidad
   (0,2,0) (`.rs-btn.rs-btn--primario`), para no depender de la hoja base del
   CDN de Tailwind, que va sin versión (H-6).
5. Nada de `!important` en las hojas (R60): Alpine esconde con
   `style="display: none"` en línea, y una regla con `!important` sobre
   `display` lo taparía (por ejemplo, la pregunta de confirmación saldría
   siempre).

**Correspondencia** (líneas de `partes.html` en `6bc4b6c`; la columna «hoy»
resume):

| Líneas | Elemento | Hoy | Nuevo `class` |
|---|---|---|---|
| `:15` | `<body>` | `bg-slate-50 text-slate-800` | `rs-cuerpo` |
| `:16` | `div` del componente | `min-h-screen flex flex-col` | igual |
| `:23-38` | barra (F-035) | pizarra oscura | §15.5 (se reescribe entera, con R44/R45/R47) |
| `:40-44` | cabecera, `h1`, subtítulo | borde y blanco | `rs-cabecera`; `rs-contenedor rs-cabecera__fila`; `rs-titulo`; `rs-subtitulo` |
| `:46-54` | indicador del backend | puntos y textos | `rs-estado-servicio`; punto `rs-punto` (su `:class` sigue); textos `rs-nota`, `rs-nota rs-mono` |
| `:59` | `<main>` | `mx-auto … space-y-6` | `rs-contenedor rs-principal flex-1` |
| `:63`, `:124`, `:482` | secciones | `rounded-lg border … p-6` | `rs-panel`; la de archivar y cerrar, `rs-panel rs-panel--destacado` (filete burdeos arriba: es la acción del circuito) |
| `:64`, `:125`, `:153`, `:259`, `:483` | rótulos `h2` | mayúsculas pizarra | `rs-rotulo` |
| `:66` | zona de soltar | `mt-4 rounded-lg border-2 border-dashed p-8 text-center transition` | `rs-zona mt-4` (discontinua: en el circuito no hay placeholders y es la convención de «suelta aquí»; su `:class` de arrastre sigue) |
| `:77`, `:83` | «Elegir ficheros», «Elegir una carpeta» | borde gris | `rs-btn rs-btn--secundario` |
| `:92`, `:146`, `:577` | errores | rojo | `rs-aviso rs-aviso--error` |
| `:94`, `:374`, `:538`, `:558` | avisos | ámbar | `rs-aviso rs-aviso--atencion` (+ `rs-aviso--compacto` o la maquetación que ya tenían) |
| `:382`, `:546`, `:548` | cerrado; puertas de entorno | azul | `rs-aviso rs-aviso--info` (las puertas **no** en rojo, como dice su comentario) |
| `:110` | «Trocear la remesa» | pizarra | `rs-btn rs-btn--primario mt-4` |
| `:129-130` | barra de progreso | gris y cielo | `rs-progreso mt-2`; `rs-progreso__barra` (burdeos; su `:style` sigue) |
| `:136` | avisos de la remesa | ámbar | `rs-panel rs-panel--atencion` |
| `:151`, `:254` | lista y detalle | tarjetas | `lg:col-span-2 rs-panel rs-panel--lista`; `lg:col-span-3 rs-panel` |
| `:154`, `:262` | «Empezar otra remesa», «Cerrar» | texto gris | `rs-btn rs-btn--texto` |
| `:161` | fila de parte | `w-full px-4 py-3 text-left hover:bg-slate-50` | `rs-fila` (su `:class` de abierto sigue) |
| `:179`, `:346` | punto del semáforo | `inline-block h-2.5 w-2.5 … rounded-full` | `rs-punto` (+ `shrink-0` / `mr-1`); su `:class` sigue |
| `:191`, `:559`, `:578`, `:589`, `:605` | hashes | mono gris | `rs-mono rs-nota` (el `:class` del tachado sigue) |
| `:199` | etiqueta de estado | `rounded px-1.5 … uppercase` | `rs-chip` (colores del `:class`, que sigue) |
| `:212` | paso en curso | `ml-auto animate-pulse text-xs text-sky-600` | `rs-paso ml-auto` (pulso propio, apagado con R55) |
| `:214`, `:216`, `:228`, `:298`, `:423`, `:442`, `:453` | notas pequeñas | gris | `rs-nota` |
| `:224` | «Lo decidió una persona» | cielo | `rs-nota rs-nota--info` |
| `:234`, `:237`, `:243`, `:432`, `:437`, `:496`, `:506` | notas de error y de atención; «reintentar» | rojo, ámbar, subrayado | `rs-nota rs-nota--error` / `--atencion`; `rs-enlace` |
| `:275-288` | campos del parte | etiqueta, confianza, «editado», `<input>` | `rs-campo__etiqueta`; confianza `rs-chip` (su `:class` sigue); `rs-chip rs-chip--ok`; `rs-campo mt-1` (su `:class` de dudoso sigue) |
| `:295` | «Revalidar (no gasta IA)» | pizarra | `rs-btn rs-btn--secundario` |
| `:318` | «guardando / guardado» | `text-xs` | `rs-nota` (su `:class` sigue) |
| `:323` | **fallo del autoguardado** | `rounded border border-red-300 bg-red-50 px-2 py-1 text-xs text-red-800` | `rs-aviso rs-aviso--error rs-aviso--compacto text-red-800` (**`text-red-800` se conserva**: `test_f026_autoguardado.py:280`) |
| `:340` | caja del estado del parte | gris claro | `rs-panel rs-panel--suave mt-4` |
| `:404` | motivo (`<textarea>`) | borde gris | `rs-campo mt-1` |
| `:410`, `:415` | «Aprobar este parte», «Rechazar este parte» | esmeralda, rosa | `rs-btn rs-btn--ok`, `rs-btn rs-btn--peligro` |
| `:459` | visor del PDF | `mt-2 h-[28rem] … border` | `rs-visor mt-2` (28 rem en la hoja) |
| `:514` | **«Archivar y cerrar los partes aptos»** | esmeralda | `rs-btn rs-btn--primario` (pasa a **burdeos**: la acción principal del circuito; V4 lo avisa) |
| `:528`, `:530` | «Sí, archivar y cerrar», «Cancelar» | rosa, borde | `rs-btn rs-btn--peligro rs-btn--compacto` (escritura irreversible en el ERP: rojo, no burdeos), `rs-btn rs-btn--secundario rs-btn--compacto` |
| `:563` | «Reintentar el cierre» | borde ámbar | `rs-btn rs-btn--secundario rs-btn--compacto` |
| `:586`, `:602` | resúmenes | listas | `rs-resumen mt-4` |
| `:592` | «abrir en SharePoint» | cielo subrayado | `rs-enlace ml-2` |
| `:606` | número de incidencia | gris mono | `rs-chip rs-chip--neutro rs-mono ml-2` |
| `:616-617` | pie | borde y gris | `rs-pie`; `rs-contenedor rs-pie__texto` |

El implementer puede afinar nombres, pero **no** puede salir de las reglas
1–5. Lo que la tabla no nombre conserva sus utilidades de maquetación y
cambia solo lo que choque con un componente.

### 15.8 · Las guardias

**R59 · el circuito solo cambia en presentación.** Función pura en
`tests/test_f035_portal.py`:

- `tokens(html) -> list[tuple]` con `html.parser` (`convert_charrefs=True`):
  etiqueta de apertura `("<", nombre, ((atributo, valor), …))` **con los
  atributos en su orden y sin `class`**; cierre `("</", nombre)`; texto con los
  blancos normalizados (se omite el vacío); comentario normalizado; `doctype`.
  `style` **no** se quita: la base no lo usa y R60 prohíbe añadirlo, así que
  la guardia es más estricta que «sin `class`/`style`».
- `diferencias_de_presentacion(antes, ahora) -> list[str]`: a los dos lados
  quita el primer comentario (la ruta; en `ahora` tiene que ser
  `services/postventa-front/partes.html`), el subárbol del
  `<nav data-barra-portal>` con los comentarios que lo preceden, y las cuatro
  `<link>` de §15.4 **si** están en el `<head>` y antes de `css/styles.css`;
  compara lo que queda con `difflib.SequenceMatcher` sobre las tuplas y
  devuelve un problema legible por cada tramo distinto. Comprueba aparte que
  la barra es el primer elemento hijo del `<div x-data="appPostventa()">`.
- **Test de rama** (`feature/F-035*`, como el de antes): `antes` =
  `git show <merge-base>:services/postventa-front/index.html`, `ahora` =
  `partes.html`; tiene que dar `[]`.
- **Control permanente** (sin git): con el `partes.html` real,
  `diferencias_de_presentacion(real, copia)` da `[]` para una copia con un
  `class` cambiado, y **no** `[]` para copias con: un `@click` cambiado, dos
  atributos permutados, un elemento añadido, un texto cambiado, un
  `style="…"` añadido y una `<link>` a otro dominio. Demuestra que la
  guardia mira.

> **Enmienda del 2026-09-26 (bloque 6, T21) · la versión de la hoja.**
> `diferencias_de_presentacion` pasa antes, a los dos lados,
> `_quita_version_de_la_hoja`: la `<link rel="stylesheet"
> href="css/styles.css?v=<10 hex>">`, con esos dos atributos y en ese orden,
> vuelve a su forma de la base. Nada más se normaliza. La versión la calcula
> `version_de_las_hojas()` (SHA-256 de `css/styles.css` y `css/portal.css`
> con los finales de línea normalizados, diez primeras cifras): un test exige
> esa versión en las hojas propias de `index.html` y de `partes.html`, así que
> tocar una hoja sin cambiar la URL queda en rojo. Controles: la guardia
> admite una versión cualquiera en la hoja del circuito, y rechaza la versión
> en otra hoja, una query con algo más, una versión sin la forma, otro `rel`,
> un atributo más y la versión en un `src` (`ESTROPEOS_T21`). El riesgo de
> §15.9 «Caché del navegador» deja de depender de `Ctrl+F5`.

**R33 enmendado.** El mismo test, con `M services/postventa-front/css/styles.css`
admitido; `js/`, `staticwebapp.config.json`, `dev_server.py` y
`dev_front.ps1`, igual que antes.

**Las demás** (en `tests/test_f035_portal.py` salvo donde se dice):

| R | Qué comprueba |
|---|---|
| R48 | Raíz: para cada sección real según `features.json` (hoy ninguna), su enlace en la barra de `partes.html` no lleva `target`; control con F-048 `done` en memoria que tiene que exigirlo para `datos`; y la regla en la sección del portal de `docs/ARCHITECTURE.md` («misma ventana») |
| R49 | Los tokens de §15.3, con su valor, en el `:root` de `css/styles.css`; fuera del `:root`, en los dos CSS, ni `#hex`, ni `rgb(`/`rgba(`/`hsl(`, ni un `box-shadow`/`border-radius` sin `var(--rs-` (salvo `0`, `50%`, `none`) |
| R50 | Las cuatro `<link>` exactas, en orden y antes de `css/styles.css`, en las dos páginas; `body` con `var(--rs-fuente-texto)` y la trama (`linear-gradient` con `var(--rs-linea)`); `.rs-titulo` con `var(--rs-fuente-titulos)` |
| R51 | En las dos barras: `img.rs-barra__logo` con su `src` y `alt`, separador `aria-hidden="true"`, etiqueta «Posventa», ninguno dentro de un `<a>`; toda pestaña con `rs-pestana`; ninguna directiva `:class` en las pestañas del portal |
| R52 | SHA-256 de los dos SVG; sin `<script`, `<foreignObject`, `<metadata`, `<text`, ` on…=`, `href=`, `data:`; colores ⊆ {`#9f2842`, `#7b868c`, `#ffffff`} |
| R53 | Contraste calculado de los pares de §15.6 con los valores del `:root`; y ningún `color: var(--rs-acero)` en los dos CSS |
| R54 | Regla `:focus-visible` con `outline` y `var(--rs-burdeos)` en `css/styles.css`; ningún `outline: none`/`0` sin otro `outline` o `box-shadow` en la misma regla |
| R55 | Toda duración de `transition`/`animation` ≤ 250 ms (o `var(--rs-duracion)`); propiedades de `transition` en la lista; `@keyframes` y `animation:` solo en `css/portal.css` salvo el pulso `rs-paso`; bloque `prefers-reduced-motion: reduce` en las dos hojas con `transition: none` y `animation: none` |
| R56 | En `index.html`, `border-dashed` solo en elementos `placeholder`; en `css/portal.css`, `dashed` solo en reglas de `.placeholder` y de la muestra; ningún elemento con `placeholder` y `rs-btn--primario` a la vez; el aviso de maqueta sin `burdeos` en sus clases ni en su regla; `partes.html` sin la clase `placeholder` |
| R57 | `tests_js/portal.test.js`: cada código de `Portal.ESTADOS`, de los estados de revisión de los datos de la bandeja y de `MaquetaDatos.volcado.catalogos.estados` tiene su `[data-estado="…"]` en `css/portal.css`; todo elemento de `index.html` con `data-estado`/`:data-estado` lleva `rs-chip` y un `x-text` |
| R58 | En las secciones `incidencias`, `bandeja` e `impresion`, un `data-vacio` con `x-show` y texto |
| R60 | Sin `!important` (salvo `[x-cloak]` de `css/portal.css`), `@import` ni `data:` en los dos CSS; ningún atributo `style` en `partes.html` |
| R61 | La sección del README y sus palabras clave (`css/styles.css`, `tokens`, `discontinuo`, `!important`, `class`, `front-portal`) |

### 15.9 · Riesgos (y cómo se comprueba que el circuito sigue funcionando)

| Riesgo | Mitigación | Dónde se ve |
|---|---|---|
| Un cambio «de estilo» toca la lógica del circuito (una directiva, un id, un texto, el orden) | R59: solo `class` cambia, atributos en su orden; control permanente con copias estropeadas; toda la suite del circuito sin tocar | `init.sh`; review |
| Se cae una clase que fija un test del circuito | Medido (§15.2): solo `text-red-800` (`test_f026_autoguardado.py:280`), que se conserva; la suite del circuito corre entera y sin cambios | `init.sh` |
| Las utilidades del CDN (sin versión, inyectadas después) pisan un componente, o su hoja base pisa el fondo de un botón | Reglas 2–4 de §15.7; especificidad (0,2,0) en `rs-btn--*`; H-6 propone fijar la versión | V2 (los botones se ven con su color) |
| Una regla con `!important` tapa un `x-show` y aparece algo que debía estar oculto (p. ej. la confirmación) | R60 y regla 5 de §15.7 | `init.sh`; V2 (la pregunta de confirmación solo sale al pulsar) |
| El burdeos se confunde con el rojo de error o con una acción irreversible | Burdeos = marca y acción principal; irreversible («Sí, archivar y cerrar») y rechazo en `--rs-error`, siempre con su texto; los estados nunca en burdeos | V2; V3 con Posventa |
| Cambia el color del botón principal del circuito (verde → burdeos) y extraña | Es la marca; el texto no cambia; V4 avisa a Posventa. Pregunta abierta al humano | V4 |
| Google Fonts no carga (red corporativa, caída) | `display=swap` y fuentes de reserva en los tokens (Georgia / `system-ui`): se ve con otra letra, no se rompe; `staticwebapp.config.json` no tiene CSP que lo bloquee (medido). Alternativa: alojarlas (§15.10) | V1-a, V4 |
| Se confunden placeholders y controles reales con el estilo nuevo | R56 (discontinuo reservado, ningún placeholder relleno de marca) y la muestra en el aviso | V1-c; V3 |
| Gris acero ilegible en textos pequeños | `--rs-acero-texto` y R53 | `init.sh` |
| El SVG del logotipo no se sirve bien en local (tipo MIME en Windows) | `dev_server.py` usa los tipos de la biblioteca estándar; se mira en V1-b; en Azure, `.svg` ya está declarado | V1-b |
| Caché del navegador: HTML nuevo con `css/styles.css` viejo tras publicar | `Ctrl+F5` en las dos páginas (V4) | V4 |
| La barra pegajosa tapa contenido o el visor del PDF | No hay anclas que tape; se mira en V2 con un parte abierto | V2 |
| Un día una sección real navega en la misma ventana desde el circuito y se pierde una remesa | R48 obliga a quitar el `target` **y** la ficha que lo haga resuelve la remesa (§2, recuadro) | test de raíz de R48 |

**Cómo se comprueba que el circuito sigue funcionando**: (1) en la rama, la
suite entera del circuito —los ~256 de Python y los 322 de JavaScript— sin un
cambio y en verde, más R59 y R32; (2) V2 con `func start`, recorriendo el
circuito hasta la pregunta de confirmación y cancelándola
(`requirements.md` §3); (3) tras publicar, V4 con una remesa de prueba, como
antes.

### 15.10 · Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Redefinir en CSS las utilidades de Tailwind que usa el circuito (`.bg-slate-900 { … }`), para no tocar su HTML | Cambia el significado de clases que usa todo el mundo, compite con el orden de inyección del CDN (acabaría en `!important`) y colorearía también los estados de las directivas |
| Configurar Tailwind con un `<script>` en línea (`tailwind.config = …`) | Es JavaScript nuevo en la cabecera del circuito (R59 no lo admite) y ata el estilo a un CDN sin versión |
| Utilidades con valores arbitrarios (`bg-[#9f2842]`) | Los tokens se repetirían en cientos de atributos, sin un sitio único |
| Hoja nueva `css/marca.css` | `css/styles.css` ya la cargan las dos páginas: otra hoja sería otra `<link>` en el circuito sin ganar nada |
| Alojar las fuentes en el repositorio (`woff2`) | Binarios en git y otra forma distinta de la del portal corporativo; queda como plan B si la red bloquea Google Fonts |
| Cambiar también los colores de las directivas `:class` del circuito | Son directivas y las fijan tests de F-026/F-028; los tokens de estado usan sus mismos tonos para que casen |
| Copiar la hoja de `front-portal` tal cual | Trae la puerta de acceso, la tarjeta de catálogo y el usuario, que aquí no existen; y dos copias divergen (la misma regla que `azure-apps/`) |

### 15.11 · Verificación manual

V1, V2 y V4 de `requirements.md` §3 (recuadro de la segunda ronda). V2 pasa
a exigir `func start` y el recorrido del circuito con una remesa de
`muestras/` hasta la pregunta de confirmación, **cancelándola**.

## 16 · Enmienda tras F-036: el portal en producción (2026-10-05)

### 16.1 · Acta y punto de partida (medido sobre `2a86bca`)

**Decisiones del humano del 2026-10-05**, transmitidas por el líder (sin cita
literal):

| | Decisión | Dónde se aplica |
|---|---|---|
| 1 | Seguir con el portal **sin esperar el feedback de negocio**, antes que F-052 | Orden del backlog (líder) |
| 2 | **Opción (b)**: se publica en producción el portal con **todas** sus secciones; las que no funcionan, **marcadas «En construcción»**, para que Posventa vea el recorrido completo. Que nadie pueda confundir una sección en construcción con una que funciona: es el riesgo que el humano acepta | §16.4; R62–R67, R77; V5 |
| 3 | **Importar, bandeja y oficios** pasan a ser **secciones reales del portal**, con la identidad Ruesma, sustituyendo los placeholders y datos de ejemplo que hoy los representan. El spec-author decide cómo | §16.2, §16.3, §16.5; R68–R73 |
| 4 | Los dos apuntes de la ficha: (a) en oficios, «Decididos como distintos» con «Son el mismo» en cada par; (b) en importar, rotular los recuentos de un fichero ya importado como «resumen de la importación original del …» | §16.6; R74–R76 |
| 5 | **Fuera**: la tarjeta de `front-portal` y el grupo de Entra (H-4); construir de verdad lo que está en construcción (F-038 en adelante) | — |
| 6 | **Respuesta del humano a la enmienda (2026-10-05)**, literal: «paginas propias, pero como en la maqueta, con un banner superior, donde cambie de ventana pero sin abrir pestaña nueva. y las paginas que ya estan deben ser remodeladas para que el front siga el estilo del resto de app» | **§16.15** (ajuste); R31, R46–R48, R59, R70, R72, R73 ajustados; R78–R82 |

**Lo que hay hoy en la rama, medido:**

- **R28 en rojo, a propósito**: F-036 está `done` y la maqueta conserva sus
  cinco restos: `index.html:185` y `:188` (los placeholders «Elegir el Excel»
  e «Importar a la bandeja»), `js/portal.js:84` y `:91` (sus entradas de
  `PLACEHOLDERS`) y `js/maqueta_datos.js:123` (el bloque `entrada`). El resto
  de `init.sh`, en verde.
- **`importar.html` y `oficios.html`** (de F-036) son páginas sueltas: su
  cabecera enlaza «Partes firmados» a **`index.html`**, que desde D-3 es el
  portal; **en esta rama ese enlace lleva al portal, no al circuito** (en
  `dev`, donde `index.html` sigue siendo el circuito, es correcto: no es un
  fallo de producción). Cargan `css/styles.css` **sin** `?v=` y **sin** las
  fuentes: con la hoja de la marca el `body` coge la trama y la fuente de
  reserva, y lo demás sigue con utilidades de Tailwind (pizarra, esmeralda,
  rojo). Un aspecto a medias.
- **`partes.html`** conserva en su cabecera los dos enlaces de F-036 (R51 de
  F-036), con `target="_blank"`; `test_f036_front.py` los fija y R59 los
  admite porque están en la base (`git merge-base dev HEAD` es ahora el `dev`
  con F-036).
- **El apunte (a) no es solo front**, aunque la ficha lo diga.
  `GET /api/catalogos/propuestas` responde `{obra, oficio: {oficios, grupos,
  propuestas, avisos}}` (`interface_adapters/api/equivalencias.py`,
  `leer_propuestas`): **ningún dato de los pares decididos «distinto»**. Un par
  marcado «Son distintos» deja de proponerse y no vuelve en ninguna lista;
  solo si partía un grupo ya confirmado sale, como componente, en `avisos`.
  La pantalla no puede saber qué pares ofrecer para deshacer sin un dato
  nuevo del backend. El `POST /api/catalogos/decisiones` con «mismo» sí lo
  admite (manda la última decisión), como dice la ficha.
- **El apunte (b) tampoco, del todo**: la respuesta de
  `POST /api/importaciones` (`interface_adapters/api/importar.py`) no trae la
  fecha de la importación, aunque el backend la tiene (`importado_at_utc` de
  la importación original, leída por `select_importacion_completa_por_hash`).
  Hoy la pantalla dice «Este fichero ya se había importado: no se ha añadido
  nada a la bandeja.» (`textoDelEstado`) y debajo, sin rótulo, los recuentos
  de entonces (`resumenLegible`: «… · 14 nuevas · …»), que se leen como si
  hubieran entrado ahora. **El rótulo sí es solo front; la fecha, no.**
- **Lo que fijan los tests de F-036** sobre las dos páginas (no se tocan,
  R32): en `test_f036_front.py`, la línea 1, los scripts propios y su orden,
  `x-data="appImportacion()" x-init="iniciar()"` (y el de oficios) juntos,
  los textos exactos de los botones, `:disabled="!puedeDecidir()"` en los de
  decidir, el comentario `<!-- ── 3 · Bandeja` y la tabla de solo lectura
  detrás, `fila.marcas`/`fila.oficioTexto`/`fila.proveedorTexto`, que la
  **primera** `<header>` de `importar.html` enlace a `oficios.html` y a
  `index.html` (y la de `oficios.html`, a `importar.html` y a `index.html`),
  que ni `oficios.html` ni `js/oficios.js` digan «proveedor» ni «actividad», y
  que no aparezca ningún dato del piloto; en `oficios.js`, `confirmado: true`
  una vez, `decidirCatalogos(` una vez y `cuerpoDeDecision(` dos. En
  `importacion.test.js` y `oficios.test.js`, funciones puras cuya salida
  actual no cambia (ningún `deepEqual` sobre el objeto entero: se pueden
  **añadir** claves).

### 16.2 · Dónde viven importar, bandeja y oficios (D-11)

> **Ajuste del 2026-10-05: D-11 decidida por el humano, P** («paginas
> propias, pero como en la maqueta, con un banner superior»). Lo de abajo
> sigue valiendo, con dos matices de §16.15: las páginas se navegan **en la
> misma pestaña también desde el circuito**, y el remodelado alcanza
> también a lo que le quedaba a `partes.html`.

| | Alternativa | Por qué sí / por qué no | Veredicto |
|---|---|---|---|
| **I** | **Integrarlas en `index.html`** como secciones `#/entrada`, `#/oficios`…, con sus componentes Alpine anidados | El portal cargaría `js/config.js`, `js/traza.js`, `js/api.js`, `js/importacion.js` y `js/oficios.js`: rompe **R15**, y **R14/R16/V1** dejan de valer para la portada (cada carga del portal pediría `/.auth/me` desde los componentes anidados, aunque la sección esté oculta). **R10** tendría que admitir botones reales que no son ni placeholder ni `data-local`. Una página de más de mil líneas mezclaría la maqueta con escritura real (decisiones de oficios, importaciones). Y obliga a **reescribir unos veinte tests de F-036** (rigor `critico`) que fijan las páginas —scripts por página, componente, cabecera, bloques—, que R32 prohíbe tocar. A cambio no da nada: importar y oficios no comparten estado con la maqueta | Descartada |
| **P** | **Páginas propias con la barra común**: `importar.html` y `oficios.html` siguen siendo sus páginas, ganan la barra superior en HTML estático (el patrón de `partes.html`, R44/R45/R51), las migas y la subnavegación de «Entrada», y la identidad Ruesma; el portal las presenta desde su sección `entrada` (y la bandeja, desde `bandeja`) | Patrón ya probado con el circuito; **ningún test de F-036 cambia** (§16.5 lista lo que hay que respetar); la portada sigue sin red; cada página real carga solo lo suyo; el día que se borre la maqueta (§7.3), las páginas reales no cambian | **Elegida** |
| **G** | Incrustarlas con `<iframe>` | `X-Frame-Options: DENY` (§1.3), como con el circuito | Descartada |
| **R** | Reescribirlas como secciones de `portal_app.js` | Rompe la regla de oro de `portal_app.js` (pegamento sin red, §8.2) y duplica la lógica de F-036 | Descartada |

**Qué significa P:**

- Entra `Portal.PAGINAS`: `{"importar.html": "entrada", "oficios.html":
  "entrada"}`, la **única fuente** de qué página real pertenece a qué sección
  (`partes.html` no entra: es la sección `partes` misma, con su `pagina`).
- La pestaña «Entrada» de la barra sigue llevando a la sección `#/entrada`
  del portal, que pasa a ser **la entrada de la sección**: dos tarjetas «En
  producción» hacia las páginas reales y el recuadro «En construcción» de la
  web de clientes (§16.5). Desde las páginas reales, la pestaña «Entrada» es
  la actual (`<span aria-current="page">`) y las migas vuelven a `#/entrada`.
- **La bandeja en solo lectura se queda donde F-036 la puso**, en el bloque 3
  de `importar.html` (va atada al campo «Código de obra» de la página). La
  sección «Bandeja de revisión» del portal es **la revisión** (F-038, F-039,
  F-040, F-043), que no existe: sigue en construcción, y su recuadro enlaza a
  `importar.html#bandeja` para ver la bandeja de verdad (R69). Una página
  `bandeja.html` aparte sería estructura nueva que F-038 tendrá que decidir
  igualmente: no se adelanta.

### 16.3 · La navegación: solo el circuito abre aparte

> **Ajuste del 2026-10-05: esta sección queda SUPERADA por §16.15.1–§16.15.4.**
> El humano pide «cambie de ventana pero sin abrir pestaña nueva»: ningún
> enlace entre páginas del front abre aparte, **tampoco desde el circuito**,
> y la remesa la protege una guarda de salida. Se conserva abajo como
> premisa de la propuesta anterior.

**La tensión.** R46 y la segunda ronda (R48) quieren navegar en la misma
ventana «como una web normal»; F-036 decidió abrir importar y oficios en
**otra pestaña** desde el circuito (R51 de F-036, D4 de F-007) para no perder
una remesa en curso; y R31 abre el portal aparte desde el circuito por lo
mismo.

**La regla que lo resuelve (R73)**: lo que decide si un enlace abre aparte es
la página **de origen**, no la de destino. La única página que guarda trabajo
en memoria es el circuito (la remesa; `js/*.js` no tiene `beforeunload`,
§2). Por eso:

| Desde | Hacia | Cómo | Por qué |
|---|---|---|---|
| `partes.html` (circuito) | cualquier otra página del front | **aparte** (`target="_blank"`, `rel="noopener"`) | No perder la remesa (R31; R51 de F-036). Sin cambios |
| `index.html` (portal) | `#/…`, `partes.html`, `importar.html`, `oficios.html` | misma ventana | No hay nada que perder (R46, R73) |
| `importar.html`, `oficios.html` | cualquier otra página del front | misma ventana | Lo importado y lo decidido ya está guardado en el backend; una importación a medias se puede repetir sin duplicar (R39 de F-036, idempotente por la huella del fichero) |

R48 no cambia: cuando una ficha enseñe al circuito a no perder la remesa, sus
enlaces podrán pasar a la misma ventana. Hoy `entrada` es `parcial`, no
`real`, y R48 no exige nada; aunque llegara a `real`, el circuito seguiría
abriéndola aparte hasta que esa ficha lo resuelva.

### 16.4 · «En construcción»: el estado de cada sección y el rótulo (D-12)

**El estado (R62)**, declarado en `Portal.SECCIONES` y comprobado contra
`harness/features.json` por un test de la **raíz** (no se cachea, como R28 y
R48):

| Sección | Fichas | Estado hoy | Por qué |
|---|---|---|---|
| `inicio` | — | `parcial` | Es la portada: será `real` cuando lo sean todas las demás |
| `entrada` | F-036 ✔, F-037 | `parcial` | Importar y oficios funcionan; la web de clientes, no |
| `bandeja` | F-038, F-039, F-040, F-043 | `construccion` | Ninguna hecha (la bandeja en solo lectura es de F-036 y vive en `importar.html`) |
| `incidencias` | F-041, F-042, F-043, F-047 | `construccion` | |
| `impresion` | F-044 | `construccion` | |
| `partes` | F-045 | `parcial` | El circuito funciona; el registro sin firma, no |
| `economico` | F-046, F-047 | `construccion` | |
| `datos` | F-048 | `construccion` | |

> **Precisión del 2026-10-06 (H-8, review del bloque 8).** En la fila de
> `inicio`, «todas las demás» son **las otras siete, `partes` incluida**
> (R62): con todas las fichas `done` salvo F-045, `inicio` sigue `parcial`.
> La regla de R48, que deja fuera `partes`, es solo para la barra del
> circuito.

**El rótulo, en tres capas** (el riesgo que el humano acepta es que alguien
tome lo inventado por real; cada capa lo ataja en un sitio distinto):

1. **En la barra** (las cuatro páginas, R66): la pestaña de una sección en
   `construccion` lleva `data-construccion`, un **punto ámbar** de 6 px tras
   la etiqueta (`.rs-pestana[data-construccion]::after`, `--rs-atencion`) y
   `aria-label="<etiqueta> (en construcción)"`, para que el lector de
   pantalla lo diga. Avisa **antes** de entrar.

   > **Enmienda del 2026-10-06 (R87).** Los pasos de la tira del recorrido
   > (§16.16) llevan la misma marca. La regla del punto pasa a ser **una**
   > con dos selectores (`.rs-pestana[data-construccion]::after,
   > .rs-recorrido__paso[data-construccion]::after`): es el mismo punto
   > por construcción, no una copia.
2. **En la sección** (R63–R65): todo lo inventado va **dentro** de un
   envoltorio `data-en-construccion` que empieza por su rótulo. No es una
   banda que se pierde al desplazarse: es el marco de todo lo que no
   funciona. Aspecto (`rs-obras`, en `css/portal.css`): borde continuo de
   1 px `--rs-atencion`, radio 16, **cinta de obra** arriba (franja de 6 px
   de rayas diagonales `--rs-atencion` / `--rs-atencion-suave`) y, debajo,
   el rótulo sobre `--rs-atencion-suave`: chip «En construcción»
   (`rs-chip--atencion`), la frase «Todavía no funciona. Lo que ves son datos
   inventados para enseñar cómo será: no es información real y no se guarda
   nada.» y la lista «La construirán: F-0NN · <título>» (de
   `Portal.TITULOS_FICHAS`, con `x-for`). Dentro, el contenido de siempre.
   Los envoltorios de bloque (F-037, F-045) son la variante compacta
   (`rs-obras--bloque`): la misma cinta y una línea de rótulo.
3. **En la portada** (R67): ninguna cifra inventada —eran lo que más se
   parecía a un cuadro de mando real («5 incidencias abiertas»)—; las
   tarjetas en construcción dicen qué se verá ahí, con el chip «En
   construcción», y las de lo que funciona llevan «En producción» y su enlace.
   Más el **aviso permanente** (R13 enmendado) bajo la barra:

   > «Parte de este portal está en construcción. Las pestañas con punto ámbar
   > y lo que va dentro de un recuadro «En construcción» enseñan datos
   > inventados (obras 99NN, incidencias RS99…) y sus botones con borde
   > discontinuo no hacen nada todavía. Lo que funciona de verdad lleva el
   > sello «En producción».»

Y lo que ya había sigue: datos imposibles (`RS99…`, `99NN`, «Ejemplo»), el
borde discontinuo reservado a los placeholders (R56), el burdeos reservado a
lo que funciona. **Nada de «maqueta»** en lo que ve el usuario (R67): en
producción, la palabra que se entiende es «en construcción».

> **Enmienda del 2026-10-06 (O9-2, O9-3 y O9-4, review del bloque 9) · la
> capa 2, cerrada.** El detector de R63 reconoce lo inventado por lo que
> lee (`datos.`, `MaquetaDatos`). No ve un método del componente que lo
> lea ni una cifra escrita a mano: sobrevivieron A1, A2, A4, A5 y A6 de esa
> review. Hoy no hay ninguno fuera de un recuadro: el listado del reviewer
> y la medida del spec-author sobre `6106c5c` dan solo las directivas de la
> lista de R63 enmendado. La forma robusta es esa **lista cerrada**: no
> depende de qué métodos leen datos. Junto a ella, dos cierres:
>
> - **El aspecto sin el atributo (O9-3, B4).** `rs-obras` solo en elementos
>   `data-en-construccion`, y todo `data-en-construccion` con `rs-obras`
>   (R63 enmendado). Así una tarjeta real no puede llevar el marco ámbar,
>   ni un recuadro quedarse sin él.
> - **«Visible» (O9-4, C4, C5 y G4).** `_CERRABLE` mira atributos. R65
>   precisado suma las clases que esconden (`hidden`, `invisible` y
>   `sr-only`, también con prefijo, como `hidden md:flex`, que escondería
>   el rótulo justo en el móvil), el `style` y las reglas de `rs-obras*` que
>   lo esconden en la hoja. Puede reutilizar `_ESCONDE_POR_CLASE` de
>   `tests/test_f035_paginas.py` (la de R75), quitando antes los prefijos
>   y sin cambiar el conjunto.
>
> Tests: T49 (R63) y T50 (R65), en `tests/test_f035_paginas.py`, cada
> guardia con su control en memoria.

**Alternativas descartadas**: (i) solo el aviso global —ya existía como
«maqueta» y se pierde al desplazarse—; (ii) esconder los datos inventados y
dejar una descripción —más seguro, pero contradice la decisión (b): Posventa
no vería el recorrido—; (iii) atenuar lo inventado (opacidad, gris) —rompe
el contraste medido de R53—; (iv) una marca de agua en diagonal —ruido
visual en tablas que se tienen que poder leer—.

### 16.5 · Sección a sección

**`inicio`.** Ceja «Posventa»; entradilla nueva: «El portal de posventa.
Funcionan ya la entrada de incidencias (importar el Excel de la obra y los
oficios repetidos) y el circuito de partes firmados. El resto del ciclo está
en construcción: lo enseñamos con datos inventados para que veáis cómo
será.» El recorrido `<ol>` no cambia *(enmienda del 2026-10-06: sale de
la portada y pasa a la tira bajo la barra de las cuatro páginas, §16.16)*.
Tarjetas: **«Entrada de incidencias»**
(nueva, «En producción», con «Importar incidencias» → `importar.html` como
`rs-btn--primario` y «Oficios repetidos» → `oficios.html` como
`rs-btn--secundario`); «Bandeja de revisión», «Incidencias», «Coste y venta»
(«En construcción», sin cifra, enlace «Ver cómo será →» a su sección; las
dos tarjetas de bandeja y las dos de incidencias de hoy se funden en una por
sección); **«Partes firmados»** («En producción», su primario de siempre y,
dentro de un envoltorio de bloque `data-en-construccion="F-045"`, el
placeholder de F-045). Una acción principal **por tarjeta en producción**:
la regla de §15.5 («una por vista») se lee, en la portada, por tarjeta.
`contadores()` (`portal_app.js`) y `Portal.contadoresInicio` se retiran con
sus tests (son de F-035).

**`entrada`.** Cabecera «Entrada de incidencias». Dos tarjetas «En
producción»: «Importar incidencias» («Descarga la plantilla de una obra,
importa el Excel a su bandeja y mira la bandeja en solo lectura.» →
`importar.html`) y «Oficios repetidos» («Junta los oficios casi iguales de
Sigrid, que la plantilla enseña como uno.» → `oficios.html`). Debajo, el
panel de la web de clientes **tal cual**, dentro de
`data-en-construccion="F-037"`. Se van la zona de soltar, los dos
placeholders de F-036, la tabla «Qué necesita cada fila» y el resultado de
ejemplo (con el bloque `entrada` de `MaquetaDatos` y su pendiente, que además
ya era falso: el Excel llegó).

**`bandeja`.** Cabecera de siempre y, entera, dentro de
`data-en-construccion="bandeja"`. El rótulo añade una línea con enlace real
(`rs-enlace`): «Mientras tanto, la bandeja de una obra ya se puede ver, en
solo lectura, en Importar incidencias» → `importar.html#bandeja`.

**`incidencias`, `impresion`, `economico`, `datos`.** Cada una, entera
(listado y ficha incluidos), dentro de su envoltorio de sección. Nada más
cambia.

**`partes.html`.** Solo dentro de la barra (fuera de la comparación de R59):
`data-construccion` y `aria-label` en las cinco pestañas en construcción y la
leyenda de R47 enmendado. Fuera de la barra, solo valores de `class`: los dos
enlaces de F-036 de la cabecera pasan de `text-sky-700 hover:underline` a
`rs-enlace` (R59 a). Y la `?v=` de la hoja (R59 e).

> **Ajuste del 2026-10-05 (§16.15).** Además: la barra y esos dos enlaces
> pierden `target` y `rel` (R73, R59 g); entra el
> `<script src="js/guarda_salida.js">` antes de `js/app.js` (R59 f); la
> leyenda es la de R47 ajustado; y los veinte `class` estáticos que aún
> llevan utilidades de color o tipografía de Tailwind pasan a `rs-*` (R82,
> §16.15.5).

**`importar.html` y `oficios.html`.** Estructura común:

```html
<body class="rs-cuerpo">
  <div x-data="appImportacion()" x-init="iniciar()" class="min-h-screen flex flex-col">
    <!-- F-035 · barra común (R70), HTML estático como la del circuito -->
    <nav data-barra-portal aria-label="Secciones de posventa" class="rs-barra"> … </nav>
    <header class="rs-cabecera">
      <div class="rs-contenedor">
        <nav aria-label="Estás en" class="rs-migas">
          <a href="index.html" class="rs-enlace">Portal de posventa</a> ›
          <a href="./#/entrada" class="rs-enlace">Entrada</a>
        </nav>
        <h1 class="rs-titulo">Importar incidencias</h1>
        <p class="rs-subtitulo">…</p>
        <nav aria-label="Entrada de incidencias" class="rs-subnav">
          <span aria-current="page" class="rs-subnav__item">Importar incidencias</span>
          <a href="oficios.html" class="rs-subnav__item">Oficios repetidos</a>
        </nav>
      </div>
    </header>
    <main class="rs-contenedor rs-principal flex-1"> … </main>
  </div>
  … sus scripts de siempre, en su orden …
</body>
```

- La barra va como primer hijo del `<div x-data>`, como en el circuito, y no
  lleva ninguna directiva (R45); no es un `<header>`, así que la «primera
  `<header>`» que lee `test_f036_front.py` sigue siendo la de la página, y en
  ella están `index.html` (migas) y la otra página (subnavegación).
- **Ningún script nuevo**: la barra es estática; las páginas no cargan
  `js/portal.js` (R77). Que sus `href` sean los de `enlaceSeccion` lo
  comprueba un test (R70), no el navegador.
- La «Partes firmados» de la cabecera de hoy (→ `index.html`) desaparece: la
  pestaña «Partes firmados» de la barra lleva a `partes.html`, en la misma
  ventana.
- Clases: `rs-panel` en cada bloque, `rs-rotulo` en sus `h2`, `rs-campo` en
  los campos, `rs-campo__etiqueta` en sus etiquetas; botones `rs-btn` —
  **primario** «Importar a la bandeja» (en `importar.html`) y «Ver los
  oficios» (en `oficios.html`); **secundario** «Descargar la plantilla», la
  etiqueta «Elegir el Excel», «Ver la bandeja», «Descargar el Excel de
  errores» y «Descargar los grupos vigentes»; **`--ok` compacto** «Son el
  mismo»; **secundario compacto** «Son distintos» y «Separar»—; errores
  `rs-aviso rs-aviso--error`; el resultado, `rs-aviso` con
  `:class="resultado.estado === 'parcial' ? 'rs-aviso--atencion' :
  'rs-aviso--ok'"` (variante `--ok` nueva en `css/styles.css`, con
  `--rs-ok`/`--rs-ok-suave`, par ya medido en §15.6); tablas `rs-tabla` en
  `rs-desplazable`; marcas de la bandeja `rs-chip rs-chip--atencion`;
  avisos de oficios `rs-panel rs-panel--atencion`; notas `rs-nota`.

  > **Errata del 2026-10-06 (O10-1, review del bloque 10).** El `:class`
  > del resultado de arriba solo distingue `parcial` del resto. Con él, un
  > fichero **ya importado** («no se ha añadido nada a la bandeja») saldría
  > en el verde de éxito, o en ámbar si la importación original fue
  > parcial: el color contradiría al texto, que ya da prioridad a
  > `ya_importado` (`textoDelEstado`). Lo correcto, y lo que hace el bloque
  > 10: el resultado, `rs-aviso` con `--info` si `yaImportado`, `--atencion`
  > si `parcial` y `--ok` en otro caso:
  > `:class="resultado.yaImportado ? 'rs-aviso--info' : (resultado.estado === 'parcial' ? 'rs-aviso--atencion' : 'rs-aviso--ok')"`.
  > Lo vigila Node (T30). Encaja con el rótulo de R74 («de la importación
  > original»).
- **Lista cerrada de utilidades de Tailwind prohibidas en estas dos páginas
  (R72)**, en `class` y dentro de las comillas de `:class`, tras quitar los
  prefijos de estado o de pantalla (`hover:`, `disabled:`, `sm:`…): las que
  empiezan por `bg-`, `text-` (salvo `text-left`, `text-center` y
  `text-right`), `border`, `rounded`, `shadow`, `font-`, `tracking-`,
  `leading-`, `divide-`, `ring`, `opacity-` y `placeholder-`, y
  `uppercase`, `lowercase` y `underline`. El resto es maquetación y se puede
  quedar (`flex`, `grid`, `gap-*`, márgenes y rellenos, `w-*`, `space-*`,
  `items-*`, `overflow-*`, `hidden`, `tabular-nums`, `align-top`…).
- Lo que **no se toca** de ellas (los tests de F-036, §16.1): textos de los
  botones, `@click` y `:disabled`, el orden y el sitio de los scripts, el
  `x-data`/`x-init`, el comentario `<!-- ── 3 · Bandeja`, la tabla de la
  bandeja sin controles, el `<input type="file" … accept=".xlsx">`, los
  `x-text`/`x-show` que fijan sus tests. En la bandeja se **añade**
  `id="bandeja"` a su `<section>` (R69).
- En `oficios.html`, ni en la barra ni en ningún texto nuevo pueden salir las
  palabras «proveedor» ni «actividad» (test de la quinta enmienda de F-036).
- **Ajuste del 2026-10-05 (§16.15.5)**: la barra lleva también la leyenda
  `<p class="rs-barra__leyenda">` con la frase de las pestañas en
  construcción (R70 ajustado), y la página cierra con el pie común
  `<footer class="rs-pie">` dentro del `<div x-data>`, tras `</main>`, con
  «Construcciones Ruesma · Posventa · entrada de incidencias.» (R72
  ajustado).

Componentes nuevos en `css/styles.css` (los usan las páginas reales, que no
cargan `css/portal.css`): `rs-migas`, `rs-subnav` y `rs-subnav__item`
(píldoras como `rs-pestana`, la actual por `aria-current`), `rs-aviso--ok`, y
el punto de `.rs-pestana[data-construccion]`. En `css/portal.css`:
`rs-obras`, `rs-obras--bloque`, `rs-obras__cinta`, `rs-obras__rotulo`. Todo
con tokens (R49) y sin discontinuo ni burdeos en lo de construcción (R56).
Al cambiar las hojas cambia la `?v=`, y se actualiza **en las cuatro
páginas** (§15.8, enmienda de T21).

### 16.6 · Los dos apuntes y el límite de servicio (D-13)

**Lo que es de este servicio (`postventa-front`) y entra en F-035:**

- **(b) El rótulo del resumen (R74).** `js/importacion.js` gana
  `rotuloResumen(respuesta)` (pura) y `presentarImportacion` la clave
  `rotuloResumen`; `resumenTexto` y `textoDelEstado` **no cambian** (los fijan
  los tests de F-036). `importar.html` pinta el rótulo encima de los
  recuentos. Fecha: `importado_at_utc` con `Intl.DateTimeFormat("es-ES",
  {timeZone: "Europe/Madrid", day: "2-digit", month: "2-digit", year:
  "numeric"})`; si falta o no es una fecha, el rótulo sin fecha.
- **(a) «Decididos como distintos» (R75).** `js/oficios.js`:
  `presentarPropuestas` gana la clave `distintos` —`(oficio.distintos ||
  [])` en pares ordenados con sus nombres, con el mismo `par()` de
  siempre— y `sinNada` la cuenta. `oficios.html` gana la sección (entre
  «Grupos vigentes» y «Avisos») con `x-show="vista.distintos.length"`, el
  título «Decididos como distintos», la frase «Alguien dijo que estos
  oficios son distintos. Si fue un error, «Son el mismo» los vuelve a juntar:
  manda la última decisión.» y, por par, `<button type="button"
  @click="decidir([par.codigo_a, par.codigo_b], 'mismo')"
  :disabled="!puedeDecidir()" …>Son el mismo</button>`. **Ni una llamada
  nueva en el JS**: el botón usa `decidir()`, así que `decidirCatalogos(` y
  `cuerpoDeDecision(` siguen contándose igual (R88 de F-036).

**Lo que no es de este servicio y NO entra en F-035 (R76):** los dos datos
que faltan son del backend (`services/postventa-api`), otro servicio del
monorepo. La regla del repositorio es partir: **se propone una ficha nueva de
backend** (el líder la da de alta; si sigue la numeración, F-053), pequeña y
solo aditiva:

| Endpoint | Campo nuevo | Contrato propuesto |
|---|---|---|
| `POST /api/importaciones` | `importado_at_utc` | ISO 8601 en UTC de la importación de la respuesta: con `ya_importado: true`, la **original** (la que ya lee `select_importacion_completa_por_hash`) |
| `GET /api/catalogos/propuestas` | `oficio.distintos` | `[{codigo_a, codigo_b}]`, ordenados: los pares cuyos dos códigos son oficios de la obra y cuya **última** decisión es `distinto`. Sin `decidido_por` ni ningún `oid` (R47 de F-036) |

Es la ficha de backend la que fija el contrato, sus tests y su línea en
`azure-apps/postventa_incidencias.md`; si cambia la forma, el bloque de F-035
se ajusta. **Por qué el front puede ir antes**: los dos consumos son
**tolerantes** (sin el campo, R74 rotula sin fecha y R75 no pinta el bloque),
así que el orden de despliegue no rompe nada y F-035 no espera a nadie. Lo
que **sí** espera es la comprobación de verdad: el bloque «Decididos como
distintos» solo se verá en producción cuando la ficha de backend esté
desplegada (V4 g).

### 16.7 · Ficheros

**A crear**

| Ruta | Qué es |
|---|---|
| `services/postventa-front/tests/test_f035_paginas.py` | Tests estáticos de la enmienda en el front: R63–R65, R67–R73, R77 y las extensiones de R50, R51, R54, R60 y la `?v=` a las dos páginas nuevas (`html.parser`, sin red) |
| `services/postventa-front/tests_js/f035_paginas.test.js` | `Portal.PAGINAS`, `enlaceSeccion` desde una página, R44 y R66 en las cuatro barras, `estado` de `SECCIONES` frente a los envoltorios de `index.html`, y R74/R75 (`rotuloResumen`, `presentarPropuestas().distintos`) |

**A modificar**

| Ruta | Qué cambia |
|---|---|
| `index.html` | Retirada de F-036 (R68), envoltorios y rótulos (R63–R65), portada (R67), `entrada` (R68), `bandeja` (R69), pestañas con `data-construccion` (R66), aviso (R13), `?v=` |
| `partes.html` | Barra: `data-construccion`, `aria-label`, leyenda (R47, R66); `class` de los dos enlaces de F-036; `?v=` |
| `importar.html`, `oficios.html` | Barra, cabecera con migas y subnavegación, identidad (R70–R72), `id="bandeja"` (R69), rótulo del resumen (R74), bloque de distintos (R75) |
| `js/portal.js` | `estado` en `SECCIONES` (R62), `PAGINAS`, `enlaceSeccion` desde una página; fuera las dos entradas de F-036 de `PLACEHOLDERS`, `"F-036"` de `TITULOS_FICHAS` y `contadoresInicio` |
| `js/portal_app.js` | Fuera `contadores()`; lo que pida el rótulo (las fichas de una sección, delegando en `Portal`) |
| `js/maqueta_datos.js` | Fuera el bloque `entrada` (F-036) |
| `js/importacion.js` | `rotuloResumen` y su clave en `presentarImportacion` (R74) |
| `js/oficios.js` | `distintos` en `presentarPropuestas` y en `sinNada` (R75) |
| `css/styles.css`, `css/portal.css` | §16.5 (componentes nuevos) |
| `tests/test_f035_portal.py`, `tests_js/portal.test.js`, `tests_js/maqueta_datos.test.js` | Los de F-035 que cambian (§16.9) |
| `tests/test_f035_placeholders_vivos.py` (raíz) | R62 con su control; el escáner de R28 con `data-en-construccion="F-0NN"` |
| `services/postventa-front/README.md`, `docs/ARCHITECTURE.md`, `docs/DESPLIEGUE.md` | Bloque 14 (`tasks.md`) |

> **Ajuste del 2026-10-05 (§16.15.7).** Se crean además `js/guarda_salida.js`
> y `tests_js/guarda_salida.test.js`; se modifican además
> `tests/test_f007_estaticos.py` (una línea) y `tests/test_f036_front.py`
> (las líneas de R51), y en la raíz `tests/test_f035_placeholders_vivos.py`
> (el control de R48). La frase de abajo «ningún test de la base» queda con
> esas dos excepciones cerradas (R81).

**No se tocan**: los nueve módulos del circuito, `js/api.js`, `js/config.js`,
`js/traza.js`; **ningún test de la base** (los del circuito y los de F-036,
R32); `staticwebapp.config.json`, `dev_server.py`, `dev_front.ps1`,
`infra/*`; **`services/postventa-api/` entero** (R76); `harness/*` salvo lo
que el líder haga con `features.json`; `front-portal` (H-4, fuera).
`azure-apps/postventa_incidencias.md` sí cambia, **en su repositorio y por el
líder**, al publicar (§16.12): la raíz del front pasa a ser el portal.

### 16.8 · Funciones y firmas

| Firma | Responsabilidad |
|---|---|
| `Portal.SECCIONES: ReadonlyArray<{id, etiqueta, fichas, pagina, estado}>` | Como antes, más `estado` (`"real"`, `"parcial"`, `"construccion"`; R62). Lo lee la guardia de la raíz como texto: `estado: "…"` escrito literal en cada entrada |
| `Portal.PAGINAS: Readonly<Record<string, string>>` | `{"importar.html": "entrada", "oficios.html": "entrada"}` (§16.2) |
| `Portal.enlaceSeccion(id, desde)` | `desde` es `"portal"`, `"circuito"` o una clave de `PAGINAS`. Desde una página: la sección de la página → `null` (es la actual); `partes` → `{href: "partes.html", nuevaPestana: false}`; las demás → `{href: "./#/<id>", nuevaPestana: false}`. `desde` desconocido → `null`, nunca lanza |
| `Portal.enConstruccion(id): boolean` | `estado === "construccion"`; un `id` desconocido → `false` |
| `Portal.fichasDeSeccion(id): Array<{ficha, titulo}>` | Para el rótulo de un envoltorio de sección (R65), con `TITULOS_FICHAS` |
| `Importacion.rotuloResumen(respuesta): string` | R74. Nunca lanza; sin `ya_importado`, «Resumen de esta importación» |
| `Oficios.presentarPropuestas(respuesta).distintos` | R75. `[{clave, codigo_a, codigo_b, nombre_a, nombre_b, motivos: []}]`; sin `oficio.distintos`, `[]` |

> **Ajuste del 2026-10-05.** `Portal.enlaceSeccion(id, "circuito")` devuelve
> `nuevaPestana: false` para todas las secciones (R31 ajustado); la clave se
> conserva, siempre `false`, para no cambiar la forma del contrato. Y entra
> `GuardaSalida` (§16.15.3).

### 16.9 · Las guardias: qué cambia y por qué

| Guardia | ¿Cambia? | Por qué |
|---|---|---|
| **R28** (raíz) | **El escáner**, no la regla | Hoy en rojo por F-036: se pone en verde **retirando** sus restos (bloque 7), no tocando la guardia. Se amplía para contar `data-en-construccion="F-0NN"` como resto: un recuadro de una ficha cerrada tiene que saltar igual que un placeholder |
| **R29** (raíz) | No | F-037…F-048 siguen con restos; F-036, `done`, ya no los necesita |
| **R62** (raíz, nueva) | — | El `estado` de cada sección frente a `features.json`, con control: en memoria, con F-038 `done`, `bandeja` tiene que pasar a `parcial` y la guardia tiene que saltar |
| **R14** | No | Sigue siendo de los **ficheros de la maqueta** (`index.html`, `maqueta_datos.js`, `portal.js`, `portal_app.js`, `portal.css`). `importar.html`, `oficios.html` y sus módulos no son de la maqueta: hablan con el backend desde sus módulos, que es lo que preveía §7.3 (paso 3). La portada sigue sin red |
| **R15, R16** | No | El portal no carga ningún módulo de las páginas reales (§16.2, P) |
| **R17** | **Sí** | El portal enlaza también a las páginas de `Portal.PAGINAS` (con ancla opcional): sin ello, las tarjetas de `entrada` y el enlace de `bandeja` no podrían existir |
| **R18** | No | El portal sigue sin almacenamiento; las páginas reales ya lo prohíben por su cuenta (D4 de F-007, test de F-036) |
| **R59** | No | En `partes.html` esta enmienda solo toca la barra (fuera de la comparación), valores de `class` (a) y la `?v=` (e) |
| **R32** | No | Ningún test de la base se toca: lo nuevo va en `test_f035_paginas.py` y `f035_paginas.test.js`; las páginas se rediseñan respetando lo que fijan los de F-036 (§16.1, §16.5). Si un test de F-036 exigiera otra cosa, **se para** y se vuelve a proponer: no se toca el test |
| **R33** | **Sí** | Admite `M` en `js/importacion.js` y `js/oficios.js` (R74, R75). Los nueve del circuito, `api.js`, `config.js` y `traza.js`, igual que antes |
| **R13**, **R47** | **Sí, el texto** | «Maqueta» → «en construcción» (R67). R47 exige «en construcción», «datos de ejemplo», «aparte» y «remesa» |
| **R44**, **R45** | **Sí, el alcance** | Cuatro barras; `enlaceSeccion` desde una página |
| **R10**, **R9** | No | Las puertas reales son enlaces (`<a>`), no botones; el catálogo pierde dos entradas y el HTML, sus dos botones |
| **R56** | **Se amplía** | Ningún envoltorio con discontinuo ni burdeos; las páginas reales sin placeholders (R77) |
| **Versión de las hojas (T21)** | **Se amplía** | La misma `?v=` también en `importar.html` y `oficios.html` |
| Tests de F-035 sobre el bloque `entrada`, `contadoresInicio` y la palabra «maqueta» | **Sí** | Son de F-035 y describen lo que se retira: se borran o se reescriben en el mismo commit (bloques 7–9) |

> **Ajuste del 2026-10-05.** Las filas de R32, R33 y R59 de arriba cambian
> (excepciones cerradas de R81) y se suman R31, R43, R47 y R48: tabla en
> §16.15.6.

### 16.10 · Verificación

Todo sin red, sin BBDD y sin IA.

| Requisitos | Test |
|---|---|
| R62 | `tests/test_f035_placeholders_vivos.py` (raíz), con su control de F-038 `done` |
| R28 (escáner) | El mismo fichero: control con un `data-en-construccion="F-036"` en memoria, que tiene que saltar |
| R63, R64, R65 | `tests/test_f035_paginas.py`: con la pila de `html.parser`, todo `data-placeholder` y toda directiva que lea `datos.` está dentro de un `data-en-construccion`; cada sección en `construccion` (de `js/portal.js`, leído como texto) tiene su envoltorio y ninguna otra lo tiene; cada envoltorio empieza por `.rs-obras__rotulo` con «En construcción», «no funciona», «inventados», «no es información real» y «no se guarda»; `tests_js/f035_paginas.test.js`: `fichasDeSeccion` |
| R66 | `tests_js/f035_paginas.test.js`: en las cuatro barras, `data-construccion` y `aria-label` exactamente en las pestañas de las secciones `construccion` |
| R67 | `tests/test_f035_paginas.py`: en `inicio`, ningún `x-text` de cifra; chips por tarjeta; ningún texto visible con «maqueta» en `index.html` (sin comentarios ni atributos); `tests_js/f035_paginas.test.js`: ningún texto de `Portal.PLACEHOLDERS` ni de `textoPlaceholder` (también el genérico) dice «maqueta» |
| R68, R69 | `tests/test_f035_paginas.py`: enlaces y chips de `entrada`, envoltorio `F-037`; enlace a `importar.html#bandeja` y `id="bandeja"` |
| R70, R71 | `tests_js/f035_paginas.test.js` (los `href` contra `enlaceSeccion` y `PAGINAS`) y `tests/test_f035_paginas.py` (barra primera y estática, migas, subnavegación) |
| R72, R73, R77 | `tests/test_f035_paginas.py`, con la lista cerrada de §16.5 y su control |
| R74 | `tests_js/f035_paginas.test.js`: con y sin `ya_importado`, con fecha válida, sin fecha y con fecha basura; una fecha de las 23:30 UTC de un día de verano sale con el día siguiente (Madrid) |
| R75 | `tests_js/f035_paginas.test.js`: con y sin `distintos`, `sinNada` con solo distintos; el componente (`crearAppOficios` con un `api` doble) manda `mismo` con el par y recarga; `tests/test_f035_paginas.py`: los botones del bloque con `@click="decidir(…, 'mismo')"` y `:disabled="!puedeDecidir()"` |
| R76 | `tests/test_f035_paginas.py`, **solo en la rama de F-035**: `git diff --name-status <merge-base> -- services/postventa-api` vacío |
| R13, R17, R33, R44, R47 enmendados | Sus tests de siempre, enmendados en el mismo commit que el cambio |

**Mutación**: `python -m harness.mutacion --feature F-035 --base 2a86bca
--timeout 900` en cada bloque con código (se espera otra vez «Sin líneas de
producción en el alcance»: F-035 no tiene Python de producción). **Compensación
manual** (C4 bis), en una copia aislada (worktree en el scratchpad, nunca el
árbol real), de la 14 a la 28, repartidas por bloques en `tasks.md`:

14. Vuelve un placeholder de F-036 a `index.html` → cae R28.
15. Un enlace de `entrada` a `otra.html` → cae R17.
16. `bandeja` declarada `parcial` en `SECCIONES` → cae R62.
17. Se quita `data-construccion` de una pestaña de `partes.html` → cae R66.
18. Un placeholder sale de su envoltorio → cae R63.
19. Un envoltorio con `border-style: dashed` → cae R56.
20. Una tarjeta en construcción vuelve a pintar `x-text` con una cifra → cae R67.
21. `target="_blank"` en la pestaña «Inicio» de `importar.html` → cae R73 (y R44).
22. `bg-slate-800` en un botón de `importar.html` → cae R72.
23. `importar.html` carga `js/portal.js` → cae R77.
24. `rotuloResumen` devuelve «Resumen de esta importación» con `ya_importado` → cae R74.
25. La fecha se formatea en UTC → cae R74 (el caso de las 23:30).
26. El botón del bloque de distintos manda `'distinto'` → cae R75.
27. Sin `:disabled` en ese botón → cae R89 de F-036 (test sin tocar) y R75.
28. `presentarPropuestas` lanza sin `distintos` → cae R75.

> **Ajuste del 2026-10-05.** Verificación de R78–R82 y mutaciones manuales
> **29–36** en §16.15.8.

### 16.11 · Riesgos

| Riesgo | Mitigación | Dónde se ve |
|---|---|---|
| **Posventa toma lo que está en construcción por real** (el aceptado por el humano) | Tres capas (§16.4): punto y nombre accesible en la barra, recuadro que enmarca todo lo inventado, portada sin cifras; aviso permanente; datos imposibles; guardias R62–R67 que no dejan que un recuadro falte ni sobre | V1, **V5 (parada)**, V4 h |
| Una ficha se cierra y su sección sigue marcada en construcción (o al revés) | R62 en la raíz, sin caché; paso 5 de §7.3 | `init.sh` |
| El rediseño de las páginas de F-036 rompe algo de lo que fijan sus tests | §16.5 lista lo que no se toca; R32 prohíbe tocar el test; si choca, se para | `init.sh` |
| Navegar desde `importar.html` en mitad de una importación | La importación es idempotente por la huella del fichero (R39 de F-036): repetirla no duplica | — |
| El bloque de distintos nunca aparece porque la ficha de backend se retrasa | Consumo tolerante; V4 g lo dice; D-13 deja al humano elegir | V4 |
| La fecha del rótulo sale con el día cambiado | Hora de Madrid con `Intl`, test con un caso de medianoche | `init.sh` |
| `dev_server.py` sirve bien `importar.html#bandeja` | El ancla no llega al servidor | V1 j |
| Un enlace de las páginas reales que abriera aparte rompería la regla «solo el circuito» | R73 | `init.sh` |
| La vista previa no tiene backend y las páginas reales enseñan un error | Es lo esperado y lo dice V5; la comprobación funcional es V4, de solo lectura | V5 |
| Re-importar en V4 un fichero que no es exactamente el mismo escribiría en la bandeja | V4 f solo con el mismo fichero sin abrir ni guardar; con la menor duda, no se hace | V4 |

> **Ajuste del 2026-10-05.** La fila «Un enlace de las páginas reales que
> abriera aparte…» queda superada (ya nada abre aparte); los riesgos de la
> misma pestaña y de la guarda, en §16.15.9.

### 16.12 · Publicación y la parada del humano (D-4, D-14)

Orden, al terminar los bloques 7–14:

1. **Review** contra `CHECKPOINTS.md` (líder → reviewer).
2. **T12 · V1 y V2** (humano, en local). Sigue abierta desde el 2026-09-25 y
   ahora recoge también lo de esta enmienda.
3. **V5 · la parada** (humano): el portal entero antes de producción.
   **Recomendación (D-14): el entorno de vista previa** con
   `powershell -ExecutionPolicy Bypass -File infra\publicar_maqueta.ps1`
   (guion de `docs/DESPLIEGUE.md` §10 de esta rama) y, al terminar,
   `… publicar_maqueta.ps1 -Retirar`. Por qué: son los mismos estáticos y el
   mismo inicio de sesión que en producción, se puede abrir desde otro PC (y
   enseñárselo a Posventa antes de que sea «de verdad»), y el entorno **no
   tiene backend enlazado** (el script lo comprueba), así que nada de lo que
   se pulse escribe: importar y oficios enseñarán el error del servicio, que
   es lo esperado. Alternativa: en local con `.\dev_front.ps1`, igual de
   seguro sin `func start`, pero solo en el PC del humano. **Con `func
   start` no**: importar escribiría en la bandeja compartida desde local.
4. **Merge a `dev`** (líder, a petición del humano) y push (humano).
5. **Publicación** (humano, D-4):
   `powershell -ExecutionPolicy Bypass -File infra\desplegar_front.ps1 -SoloFront`,
   y **V4** con lo que añade la enmienda.
6. **Para el líder, en el mismo trabajo** (regla de `azure-apps/`):
   `azure-apps/postventa_incidencias.md` dice que la raíz del front es el
   portal, el circuito está en `/partes.html` e importar y oficios son
   secciones del portal (commit local en ese repositorio).
7. **Aviso a Posventa** (humano). Texto propuesto:

   > «Desde hoy, al entrar en Posventa veis el portal nuevo. Funcionan de
   > verdad: **Entrada** (descargar la plantilla de una obra, importar el
   > Excel y ver su bandeja; y los oficios repetidos) y **Partes firmados**
   > (el circuito de siempre, con otro aspecto y el botón principal en
   > burdeos; funciona igual). Lo demás —bandeja de revisión, incidencias,
   > impresión, coste y datos— está **en construcción**: se reconoce por el
   > punto ámbar en la pestaña y por el recuadro «En construcción»; lo que
   > enseña son datos inventados para que veáis cómo será. Contadnos qué os
   > falta o qué cambiaríais.»

   **Ajuste del 2026-10-05**: al texto se le añade, antes de «Contadnos»:
   «Ahora todo se abre en la misma pestaña. Si estáis con una remesa a
   medias en Partes firmados y pulsáis otra pestaña, el navegador os
   preguntará si queréis salir: decid que no, o perderéis la remesa.»

### 16.13 · Decisiones abiertas (con recomendación)

> **Ajuste del 2026-10-05 · estado de las decisiones.** **D-11, decidida
> por el humano**: P, páginas propias con la barra común, en la misma
> pestaña y remodeladas (§16.15). **D-12, D-13 (i) y D-14, decididas por
> defecto** con la recomendación de abajo: el humano no las ha objetado, y
> valen mientras no diga otra cosa (si objeta D-13, el bloque 13 se cae;
> si objeta D-14, T40 se hace en local). Entran **D-15** y **D-16**
> (§16.15.10), con recomendación, para validar.

- **D-11 · ¿Dónde viven importar, bandeja y oficios?** Recomendación:
  **páginas propias con la barra común** (P, §16.2); la bandeja en solo
  lectura se queda en `importar.html` y la sección «Bandeja de revisión»
  sigue en construcción con un enlace a ella. Alternativas I, G y R
  descartadas.
- **D-12 · El rótulo «En construcción».** Recomendación: las **tres capas**
  de §16.4, con la **portada sin cifras** y fuera la palabra «maqueta» de lo
  que se ve. Alternativa que el humano puede preferir: conservar las cifras
  de la portada con «(ejemplo)» —más vistoso, más confundible—.
- **D-13 · Los apuntes necesitan dos datos del backend.** Recomendación:
  **(i)** F-035 hace la parte de front con consumo tolerante (bloques 12 y
  13) y el líder da de alta **una ficha de backend aparte**, pequeña, con el
  contrato de §16.6, que puede ir en paralelo o justo después. Alternativas:
  (ii) sacar el apunte (a) entero de F-035 y hacerlo después de esa ficha —el
  bloque 13 desaparece; el apunte (b), sin fecha, se queda—; (iii) hacer el
  backend dentro de F-035 —**no**: rompe el límite de servicio de
  `CLAUDE.md`—.
- **D-14 · ¿Dónde ve el humano el portal entero antes de publicar?**
  Recomendación: **el entorno de vista previa** (`publicar_maqueta.ps1`),
  §16.12 paso 3. Alternativa: en local, sin `func start`.

### 16.14 · Hallazgos (para el líder)

- **H-8**: en esta rama, desde el merge `988c086`, «Partes firmados» de
  `importar.html` y `oficios.html` lleva al **portal** (apunta a
  `index.html`). En `dev` es correcto. Lo arregla el bloque 10/11 (la barra
  lleva a `partes.html`); hasta entonces, no se publica esta rama.
- **H-9**: la ficha de F-035 dice que «Decididos como distintos» «es solo
  front»; medido (§16.1), **no**: hace falta un dato del backend (D-13).
  Conviene corregir la descripción de la ficha al dar de alta la de backend.
- **H-10**: `test_f036_front.py::test_f036_s15_6_…` exige `index.html` en la
  cabecera de las dos páginas; antes era «volver al circuito», con esta
  enmienda es «Portal de posventa» (migas). El test no cambia y sigue
  teniendo sentido, pero su nombre y su docstring hablan del circuito: para
  una limpieza de F-036, no de F-035 (R32).
- **H-8, ajuste del 2026-10-05**: lo arreglan igual los bloques 10/11; la
  pestaña «Partes firmados» de las dos páginas lleva a `partes.html` en la
  misma pestaña.
- **H-11** (2026-10-05): el R51 **de F-036** no habla de pestañas («debe
  enlazar a la de importación y a la de oficios repetidos»): sigue
  cumpliéndose tal cual. Lo que cambia es el detalle de su diseño y su test
  (`target="_blank"`), que esta rama ajusta con la excepción cerrada de R81.
  No hace falta tocar la spec de F-036; conviene que `progress/history.md`
  lo diga al cerrar F-035.
- **H-12** (2026-10-05): `partes.html` **casi** sigue ya el estilo del
  portal, medido sobre `a54cd5d`: misma barra (logotipo, separador,
  «Posventa», ocho `rs-pestana`, actual por `aria-current`), fuentes,
  favicon, `rs-cuerpo`, `styles.css?v=`, cabecera, paneles, botones y pie
  `rs-*`. Le faltan tres cosas: (1) los puntos ámbar y el `aria-label` de
  las pestañas en construcción (ya en el bloque 8); (2) la leyenda dice
  todavía «maqueta» y «aparte» (bloque 16); (3) **35 utilidades de
  Tailwind de color o tipografía en 20 `class` estáticos** (líneas 59–61,
  89, 119, 144, 155–156, 170, 176, 293, 340, 363, 379, 414–415, 417, 502,
  539–540: `text-sm`, `text-xs`, `text-slate-400…700`, `text-sky-700`,
  `hover:underline`, `divide-y`/`divide-slate-100`, `text-amber-700/800`,
  `border-b border-slate-100`, el `uppercase tracking-wide font-semibold`
  de «Avisos de la remesa»), que se ven en gris o azul de Tailwind y no en
  los tokens: R82, bloque 17. **No** le falta el aviso «En construcción»
  del portal (es una página real, R77) ni `css/portal.css` (que es de la
  maqueta). Los colores de estado de los `:class` se quedan (§15.7 regla 2).

### 16.15 · Ajuste tras la respuesta del humano: misma pestaña, guarda de salida y remodelado (2026-10-05)

#### 16.15.1 · La respuesta y cómo se lee

Literal, del humano (2026-10-05), transmitida por el líder: **«paginas
propias, pero como en la maqueta, con un banner superior, donde cambie de
ventana pero sin abrir pestaña nueva. y las paginas que ya estan deben ser
remodeladas para que el front siga el estilo del resto de app»**.

Interpretación del líder, que esta spec adopta:

1. **D-11 = páginas propias** (`importar.html`, `oficios.html` y
   `partes.html`), **todas con la misma barra superior de la maqueta** (el
   «banner superior»: `<nav data-barra-portal>`, R44, R51), y la navegación
   entre secciones y páginas **siempre en la misma pestaña**: ningún
   `target="_blank"` en la barra, en las cabeceras ni en las tarjetas,
   **tampoco desde «Partes firmados»**. Cambia lo que §16.3 proponía (solo
   el circuito abría aparte) y, en esta rama, el detalle de diseño de R51
   de F-036 (los enlaces del circuito a importar y oficios ya no abren
   pestaña nueva; H-11).
2. **El riesgo que eso abre** —salir de `partes.html` en la misma pestaña
   con una remesa a medias pierde el trabajo en memoria (D4 de F-007; la
   rehidratación es F-021, pendiente)— se mitiga **por defecto** con una
   **guarda de salida**: si hay trabajo sin terminar, el navegador pide
   confirmación; si no, se navega sin preguntar (§16.15.2–§16.15.4).
3. **Remodelar las páginas que ya están** (`importar.html`, `oficios.html`)
   a la identidad Ruesma del portal —`css/styles.css`, tokens `--rs-*`,
   tipografías, componentes `rs-*`— es **presentación**: la lógica de F-036
   no cambia. Ya lo proponía §16.5 (R70–R72); el ajuste le añade la leyenda
   de la barra y el pie, y **termina** el de `partes.html` (H-12, R82).
4. **D-12, D-13 (i) y D-14, decididas por defecto** con la recomendación de
   §16.13, a falta de que el humano diga otra cosa.

#### 16.15.2 · Qué es «trabajo sin terminar» (R79), medido en el circuito

Sale de lo que `js/app.js` ya declara en el estado de `appPostventa()` y de
los selectores que exportan `js/pipeline.js` y `js/autoguardado.js`; nada
inventado:

| | Condición | Lo que lee | Por qué es trabajo que se perdería |
|---|---|---|---|
| (a) | **Algo en marcha** | `fase` ∈ {`troceando`, `procesando`, `archivando_y_cerrando`} (los literales que asigna `app.js:175`, `:269`, `:765`); o `Pipeline.hayTandaEnCurso()` | Trocear y procesar cuestan IA y tiempo; cortar una tanda a medias deja partes archivados sin adjuntar o adjuntados sin cerrar, que solo se recuperan desde esta pantalla (F-025 R24) |
| (b) | **Correcciones sin guardar** | `estadoAutoguardado` ∈ {`Autoguardado.GUARDANDO`, `Autoguardado.FALLO`} | Lo tecleado no está en la base (F-026 R52; `MENSAJE_FALLO` dice que «sigue ahí», en pantalla) |
| (c) | **Partes por terminar** | algún `parte` de `partes` con `!parte.cerrado` y `Pipeline.estadoDe(parte)` ∉ {`ESTADO_RECHAZADO`, `ESTADO_CERRADO`} | Por archivar y cerrar (`pendientesDeCircuito`), por decidir, por corregir o con error: sin F-021 no hay forma de volver a verlos sin subir otra vez la remesa (el pie de `partes.html` ya lo dice) |
| (d) | **Un parte abierto sin cerrar** | `parteAbierto !== null && !parteAbierto.cerrado` | Cubre el rebote del autoguardado **mientras el detalle sigue abierto** (1,5 s en los que lo tecleado aún no ha pasado a «guardando», y que la guarda no puede ver sin montar el autoguardado, R80; con el detalle ya cerrado, ver «se acepta» abajo, errata del 2026-10-06) y el motivo escrito y sin enviar (`motivoDeRechazo`), también sobre un parte rechazado. Mira solo el `cerrado` del circuito, no el del backend (precisión H16-6 en R79) |

**No** es trabajo: la página recién abierta (`fase` `inactivo`, sin
partes); ficheros elegidos sin trocear (`seleccionado`: nada ha salido del
navegador y volver a elegirlos es un gesto); una remesa con todos sus partes
cerrados o rechazados y el detalle cerrado (rechazado y cerrado constan en
la base, F-028); y lo que queda tras «Empezar otra remesa» (`reiniciar()`
vacía `partes` y `parteAbierto`). Con eso, quien acaba una remesa y cierra
el detalle navega sin que nadie le pregunte, que es lo que pide el humano.

Lo que la guarda **no** puede saber y se acepta: una tanda cuyas peticiones
ya salieron sigue en el servidor aunque la página se vaya (la guarda lo
pregunta antes, por (a)); y **la ventana de 1,5 s del rebote del
autoguardado tras cerrar el detalle** de un parte rechazado (o que el
backend da por cerrado): se edita un campo, se cierra el detalle y se sale
en ese instante, y lo tecleado se pierde sin pregunta.

> **Errata del 2026-10-06 (H16-5, review del bloque 16).** Decía «el rebote
> del autoguardado sobre un parte que no está abierto no existe (el
> autoguardado guarda el anterior al cambiar de parte)». Es inexacto. El
> autoguardado dispara el rebote pendiente cuando se **escribe en otro
> parte** (`alEscribir`, `autoguardado.js`), pero `cerrarParte()`
> (`app.js`) no lo cancela ni lo fuerza: el temporizador sigue vivo hasta
> 1.500 ms con el detalle ya cerrado. Durante ese tiempo lo tecleado aún no
> está en «guardando», así que (b) no lo ve, y (d) ya no aplica. Para un
> parte sin terminar lo cubre (c). Para uno rechazado, o cerrado según el
> backend, (c) lo excluye. Sus campos se pueden editar en cualquier estado
> (el detalle de `partes.html` no los deshabilita), así que queda ese hueco
> de como mucho 1,5 s. La guarda no puede verlo sin `_autoguardado()`, que
> R80 prohíbe, y cerrarlo exigiría tocar `app.js` (R33). Se **acepta**: es
> estrecho, exige tres gestos seguidos en 1,5 s y lo que se pierde son, como
> mucho, las últimas pulsaciones sobre un parte ya decidido. No cambia el
> código.

#### 16.15.3 · El módulo: `js/guarda_salida.js` (R78–R80)

```js
// services/postventa-front/js/guarda_salida.js
// La guarda de salida del circuito (F-035, R78-R80). SOLO LEE el estado de
// appPostventa(): ni escribe, ni llama a sus métodos, ni red, ni almacenamiento.
(function () {
  "use strict";
  const FASES_EN_MARCHA = Object.freeze(["troceando", "procesando", "archivando_y_cerrando"]);
  const SELECTOR_CIRCUITO = '[x-data="appPostventa()"]';

  function hayTrabajoSinTerminar(estado, pipeline, autoguardado) { … }   // pura, nunca lanza
  function leerEstado(ventana, documento) { … }  // Alpine.$data(el) o null; nunca lanza
  function alSalir(evento, ventana, documento) { … } // pide confirmación solo con trabajo; devuelve true si la pidió
  function instalar(ventana, documento) { ventana.addEventListener("beforeunload", …) }

  const GuardaSalida = { FASES_EN_MARCHA, SELECTOR_CIRCUITO, hayTrabajoSinTerminar, leerEstado, alSalir, instalar };
  if (typeof window !== "undefined") { window.GuardaSalida = GuardaSalida; instalar(window, document); }
  if (typeof module !== "undefined" && module.exports) { module.exports = GuardaSalida; }
})();
```

| Firma | Responsabilidad |
|---|---|
| `hayTrabajoSinTerminar(estado, pipeline, autoguardado): boolean` | R79 (a)–(d). `pipeline` y `autoguardado` son `window.Pipeline` y `window.Autoguardado` (inyectados para el test). `estado` nulo, sin `partes` o con formas raras → `false`; **nunca lanza** (un `try` que devuelve `false`) |
| `leerEstado(ventana, documento): object \| null` | `ventana.Alpine.$data(documento.querySelector(SELECTOR_CIRCUITO))`, **en el momento del evento** (Alpine va con `defer` y arranca después de este script). Sin `Alpine`, sin `$data`, sin el elemento o si lanza → `null` |
| `alSalir(evento, ventana, documento): boolean` | Si `hayTrabajoSinTerminar(leerEstado(…), ventana.Pipeline, ventana.Autoguardado)`, llama a `evento.preventDefault()` y pone `evento.returnValue = true` (la receta de MDN para los navegadores que aún miran `returnValue`) y devuelve `true`; si no, no toca el evento y devuelve `false` |
| `instalar(ventana, documento)` | Registra **un** `beforeunload` que llama a `alSalir`. Nada más: ni `click`, ni `popstate`, ni temporizadores |

Por qué estas formas:

- **Leer y no escribir**: `Alpine.$data(el)` es la API pública de Alpine 3
  (`Alpine.$data`, en 3.14.1) para leer el estado de un componente desde
  fuera; devuelve el proxy reactivo, y leerlo no dispara nada. Llamar a
  `pendientes()` o a `_autoguardado()` sería más corto, pero son métodos
  del componente y el segundo **monta** el autoguardado si no existía: por
  eso R80 los prohíbe y la guarda usa los selectores puros de `Pipeline`.
- **Falla abierta** (R80): si no se puede leer el estado, no se pregunta.
  Sin Alpine o sin componente, el circuito no funciona y no hay remesa que
  perder; preguntar siempre «por si acaso» enseñaría el diálogo en cada
  salida y la gente aprendería a aceptarlo sin leer, que es justo lo que lo
  inutilizaría cuando importa.
- **Solo `beforeunload`** cubre todas las salidas de la pestaña: los
  enlaces de la barra y de la cabecera (que ya no abren aparte), `F5`,
  cerrar la pestaña, «Atrás» y escribir otra URL. Ningún enlace del
  circuito navega dentro del mismo documento (no hay `#/` propios en
  `partes.html`), así que todos disparan el evento; el «abrir en
  SharePoint» abre aparte y no lo dispara. El circuito no navega solo
  (medido: ningún `location`, `window.open` ni `.download` en sus módulos),
  así que la guarda no salta por sorpresa.
- **El texto del diálogo es el del navegador** («¿Salir del sitio? Es
  posible que no se guarden los cambios»): los navegadores ignoran un texto
  propio desde hace años. Lo que dice qué se pierde es la leyenda de la
  barra (R47 ajustado), que se ve antes de pulsar.
- **El navegador solo enseña el diálogo si la persona ha interactuado con
  la página** (activación de usuario). Con trabajo sin terminar siempre la
  ha habido (soltar la remesa es un gesto), así que no es un hueco.
- **bfcache**: un `beforeunload` registrado puede impedir que el navegador
  guarde la página en su caché de «Atrás/Adelante». Para el circuito da
  igual (al volver, la página arranca vacía igual que hoy) y no se registra
  y desregistra según el estado, porque eso exigiría observar el estado
  (`Alpine.effect`) desde fuera: más código y más superficie que lo que
  ahorra.

#### 16.15.4 · Cómo entra en el circuito: la excepción mínima (R81)

R33 no se toca: **ningún módulo del circuito cambia**. La guarda es un
fichero nuevo, y para cargarla hacen falta tres cambios, todos cerrados:

| Dónde | Cambio exacto | Por qué no hay otra forma |
|---|---|---|
| `partes.html` | `<script src="js/guarda_salida.js"></script>` **justo antes** de `<script src="js/app.js"></script>`, sin atributos ni comentario nuevos (R59 f, R43 ajustado) | Es el único sitio donde el circuito carga código. Va antes de `app.js` porque F-007 exige que `app.js` sea el último; el orden da igual en ejecución, porque la guarda lee el estado al salir, no al cargar |
| `tests/test_f007_estaticos.py` (base, R32) | **Una línea añadida** en `ORDEN_CANONICO`, entre `"js/autoguardado.js",` y `"js/app.js",`: `    "js/guarda_salida.js",  # F-035 (R80, R81): solo lee el estado del circuito` | `problemas_del_index` rechaza todo script propio que no esté en `ORDEN_CANONICO`. Mismo precedente que las líneas `INDEX`: un cambio de una línea en un test de la base, declarado y vigilado por R32 |
| `tests/test_f036_front.py` (base, R32) | En `test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas`: el docstring `"""En otra pestaña: navegar fuera perdería la remesa en curso (D4 de F-007)."""` pasa a `"""En la misma pestaña (F-035, 2026-10-05): la remesa la protege la guarda de salida del circuito."""`, y las dos líneas `assert 'target="_blank"' in en_cabecera[destino]` y `assert 'rel="noopener"' in en_cabecera[destino]` pasan a **una**: `        assert "target=" not in en_cabecera[destino]` | El test fijaba justo lo que el humano cambia. Lo que protegía (que la remesa no se pierda al ir a importar u oficios) **no se pierde**: pasa a protegerlo la guarda, con sus tests (`tests_js/guarda_salida.test.js`); y el test sigue exigiendo los dos enlaces (su primer `assert`, sin tocar) y ahora, además, la misma pestaña |

> **Riesgo aceptado del 2026-10-06 (H16-4, review del bloque 16) · el
> comentario de F-036 en la cabecera de `partes.html` queda desfasado.** El
> comentario que precede al `<nav>` de los dos enlaces de F-036 sigue
> diciendo «la entrada de incidencias, en otra pestaña: salir de esta
> perdería la remesa en curso (D4 de F-007)». Desde T44 es al revés: los
> enlaces van en la misma pestaña y la remesa la protege la guarda. R59
> compara los comentarios fuera de la barra, y (g) solo admite retirar
> `target` y `rel`, así que no se puede tocar sin ampliar la excepción.
> Había dos salidas: (i) sumar a R59 (g) la sustitución **literal** de ese
> comentario, con su línea en la guardia, como las de R81; o (ii) aceptar
> el desfase. **Se elige (ii)**, porque es lo que menos toca: ni R59, ni su
> guardia, ni `partes.html`, ni un control más. El comentario no se ve, y
> la regla vigente está en R73 ajustado, en esta sección y en el README del
> front (T37). **Quien abra la excepción de R59 por otro motivo** (F-045 o
> F-021, que tocarán el circuito) sustituye ese comentario en el mismo
> cambio. Si el humano prefiere (i), es una línea en R59 (g), la sustitución
> en `partes.html` y una entrada en la guardia de R59, con su control.
>
> **Actualización del 2026-10-06 (el recorrido, §16.16.6).** La tira del
> recorrido abre la excepción de R59 por otro motivo, así que, por la regla
> de arriba, el comentario se sustituye **en el mismo cambio**: R59 (i),
> con su texto literal en §16.16.6 y su control. H16-4 queda en (i) y deja
> de estar pendiente.

Alternativas descartadas, en una línea cada una:

- **Meter la guarda en `js/app.js`** (un `beforeunload` en `init`): rompe
  R33 en el módulo que el humano pidió no tocar, y `app.js` no tiene tests
  (regla de oro de F-007).
- **Un `<script>` en línea en `partes.html`**: su lógica no se podría probar
  en `node --test` y seguiría siendo código nuevo en el circuito, sin
  ahorrarse la excepción de R59.
- **Un `confirm()` propio al pulsar un enlace de la barra**: cubre solo esos
  enlaces (no `F5`, ni cerrar, ni «Atrás»), sale **dos** diálogos seguidos
  (el propio y el de `beforeunload`) salvo que se coordinen con más estado,
  y obliga a escuchar clics sobre una barra que R45 quiere estática.
- **Seguir abriendo aparte desde el circuito**: es lo que el humano acaba de
  descartar.
- **Guardar la remesa en el navegador para rehidratarla**: rompe D4 de F-007
  (nada en `localStorage`) y es F-021, otra ficha.
- **Preguntar siempre al salir del circuito**: el diálogo constante enseña a
  aceptarlo sin leer y contradice «sin trabajo, se navega sin preguntar».
- **Guarda también en `importar.html` y `oficios.html`**: no guardan nada en
  memoria; importar es idempotente por la huella del fichero (R39 de F-036)
  y cada decisión de oficios se guarda al pulsar. No hace falta.

#### 16.15.5 · El remodelado (R70, R72 ajustados; R82)

**`importar.html` y `oficios.html`**: lo de §16.5 sigue entero (barra,
cabecera con migas y subnavegación, `rs-*` y la lista cerrada de Tailwind
prohibida). El ajuste añade:

- En la barra, tras `rs-barra__fila`, `<p class="rs-barra__leyenda">Las
  pestañas con punto ámbar están en construcción y enseñan datos de
  ejemplo.</p>` (R70 ajustado).
- Al final del `<div x-data>`, tras `</main>`, el pie común:
  `<footer class="rs-pie"><div class="rs-contenedor rs-pie__texto">Construcciones
  Ruesma · Posventa · entrada de incidencias.</div></footer>` (R72
  ajustado).
- Ningún `target` en ningún enlace (R73 ajustado).

**Lo que no cambia de F-036 y cómo se comprueba.** El remodelado no toca
`js/importacion.js`, `js/oficios.js` ni `js/api.js` (los cambios de esos dos
módulos son solo los de R74 y R75, aditivos y en sus bloques), ni ninguna
directiva de Alpine, texto de botón, `@click`, `:disabled`, `x-text`,
`x-show`, `id` o atributo `type`/`accept` de las páginas. **Ningún test de
F-036 fija una clase**: medido sobre `a54cd5d`, `test_f036_front.py` no
busca ningún valor de `class` (fija scripts, componente, botones por su
texto y su `@click`, `x-text`, `x-show`, el comentario `<!-- ── 3 ·
Bandeja`, los enlaces de la primera `<header>` y la ausencia de datos
reales y de botones prohibidos), y `importacion.test.js` y `oficios.test.js`
prueban funciones puras, sin HTML. Así que el remodelado **no obliga a
ajustar ningún test de F-036**; el único que se ajusta es el de R51, y por
la misma pestaña, no por el estilo (§16.15.4).

**`partes.html` (R82, H-12)**: las 35 utilidades de color y tipografía de
sus 20 `class` estáticos pasan a componentes `rs-*` existentes —`rs-nota`
para los textos pequeños en gris, `rs-enlace` para los dos enlaces de F-036,
`rs-rotulo` y `rs-aviso--atencion` para «Avisos de la remesa» y su lista,
el separador de `rs-panel--lista` para la cabecera de la lista (`divide-*`,
`border-b`)—, o a uno nuevo si ninguno sirve (con tokens, R49). Solo valores
de `class` (R59 a); `text-red-800` se queda (§15.7 regla 3); los `:class`
no se tocan. Medido: ningún test de la base fija ninguna de esas clases.

#### 16.15.6 · Las guardias que cambian con el ajuste

| Guardia | Cambio | Por qué / control |
|---|---|---|
| **R31** (`test_f035_portal.py`, `tests_js/portal.test.js`) | La barra de `partes.html` sin `target` ni `rel`; `enlaceSeccion(id, "circuito")` con `nuevaPestana: false` | Control en memoria: un `target="_blank"` repuesto en una pestaña tiene que saltar |
| **R43** (`test_f035_portal.py`) | Lista esperada: los nueve con `js/guarda_salida.js` justo antes de `js/app.js` | Control: la guarda después de `app.js`, o un segundo script nuevo, en rojo |
| **R47** | Exige «en construcción», «datos de ejemplo», «remesa», «confirmación»; prohíbe «aparte» | Control: la leyenda vieja, en rojo |
| **R48** (raíz) | El test principal sigue (verde: no queda ningún `target`). Su control `…_la_guardia_mira_una_seccion_que_pasa_a_real` deja de poder saltar sobre el HTML real; se reescribe para aplicar `enlaces_aparte_a_secciones_reales` a una **copia en memoria** de `partes.html` con `target="_blank"` repuesto en la pestaña `datos` y F-048 `done` | Sin eso, el control fallaría (no hay nada que cazar) o, peor, se borraría |
| **R32** (`test_f035_portal.py`) | `test_f007_estaticos.py`: admite `2 1` con las líneas añadidas **exactamente** [`INDEX` nueva, la de `ORDEN_CANONICO`] y la quitada [`INDEX` vieja]. `test_f036_front.py`: admite `3 4` con las añadidas exactamente [`INDEX` nueva, el docstring nuevo, el `assert "target=" not in …`] y las quitadas [`INDEX` vieja, el docstring viejo, los dos `assert` de `target`/`rel`] (textos literales de §16.15.4) | Una constante por fichero con las líneas literales; cualquier otra línea, en rojo |
| **R33** | `nuevos_admitidos` gana `js/guarda_salida.js` (`A`) | Un `M` en cualquier módulo del circuito sigue en rojo |
| **R59** | Admite (f) y (g) | `ESTROPEOS_T21` sigue en rojo, más dos controles: un segundo `<script>` nuevo y quitar el `target` del enlace de SharePoint |
| **«F-036 intacto»** (comprobación de `tasks.md`) | Desde T44, `git diff 2a86bca -- …test_f036_front.py` muestra **solo** las líneas de R81 | — |
| **R73** (nuevo alcance) | En las cuatro páginas, ningún `<a>` con `href` relativo (a `*.html`, `./`, `#/`) lleva `target` | Control en memoria por página |
| **R82** (nueva) | `class` estáticos de `partes.html` contra la lista cerrada, con `text-red-800` admitido solo en el aviso del autoguardado | Control: `text-slate-600` repuesto, en rojo |

#### 16.15.7 · Ficheros del ajuste

| Ruta | Qué |
|---|---|
| `services/postventa-front/js/guarda_salida.js` (**nuevo**) | §16.15.3 |
| `services/postventa-front/tests_js/guarda_salida.test.js` (**nuevo**) | R78–R80 con dobles: la tabla de (a)–(d) y sus negativos; el estado como `Proxy` que **lanza** al escribir o al llamar a cualquier función suya (R80); sin `Alpine`, sin elemento y con `$data` que lanza → `false` y el evento intacto; con trabajo, `preventDefault` llamado y `returnValue` puesto; `instalar` registra exactamente un `beforeunload` |
| `services/postventa-front/partes.html` | Barra y cabecera sin `target`/`rel`; leyenda R47; `<script>` de la guarda; `class` de R82 |
| `services/postventa-front/importar.html`, `oficios.html` | Leyenda en la barra, pie (§16.15.5) |
| `services/postventa-front/js/portal.js` | `enlaceSeccion(…, "circuito")` → `nuevaPestana: false` |
| `services/postventa-front/css/styles.css` | Lo que pida R82 si hace falta un componente nuevo; `?v=` en las cuatro páginas |
| `services/postventa-front/tests/test_f035_portal.py`, `tests_js/portal.test.js` | §16.15.6 (R31, R32, R33, R43, R47, R59) |
| `services/postventa-front/tests/test_f035_paginas.py` | R73 en las cuatro páginas, R82, la leyenda y el pie de R70/R72, y un test estático de `js/guarda_salida.js`: ni `fetch`, ni `XMLHttpRequest`, ni `localStorage`/`sessionStorage`/`indexedDB`, ni `addEventListener(` con otro evento que `"beforeunload"`, ni `_autoguardado`; y que cada literal de `FASES_EN_MARCHA` aparece en `js/app.js` como `this.fase = "<fase>"` (si el circuito renombra una fase, salta) |
| `services/postventa-front/tests/test_f007_estaticos.py`, `tests/test_f036_front.py` (**base**) | Solo las líneas de §16.15.4 |
| `tests/test_f035_placeholders_vivos.py` (raíz) | El control de R48 (§16.15.6) |
| `README.md` del front, `docs/ARCHITECTURE.md`, `docs/DESPLIEGUE.md` | Bloque 14: «misma ventana» para todo y la guarda de salida, en vez de «solo el circuito abre aparte» |

No cambia nada más de §16.7: ni `services/postventa-api/`, ni
`staticwebapp.config.json`, ni `dev_server.py`, ni `infra/*`
(`desplegar_front.ps1` y `publicar_maqueta.ps1` copian la carpeta entera:
el fichero nuevo viaja solo).

#### 16.15.8 · Verificación y mutaciones manuales 29–36

Todo sin red, sin BBDD y sin IA. Además de lo de §16.15.6:

| Requisito | Test |
|---|---|
| R78 | `tests_js/guarda_salida.test.js`: `alSalir` con trabajo → `preventDefault` y `returnValue`; sin trabajo → el evento intacto |
| R79 | El mismo: un caso por fila de la tabla de §16.15.2 (positivos y negativos: recién abierta, `seleccionado`, todo cerrado/rechazado con el detalle cerrado, tras reiniciar) |
| R80 | El mismo (el `Proxy` que lanza; los tres caminos de fallo) y el test estático de `test_f035_paginas.py` |
| R81 | Las guardias R32, R33, R43 y R59 de §16.15.6 |
| R82 | `test_f035_paginas.py` con su control |
| V2 (k)–(p), V1 (q), V4 (i) | Manual, humano (`requirements.md` §3) |

Mutaciones manuales (C4 bis), en una copia aislada, como las 14–28:

29. `hayTrabajoSinTerminar` olvida `archivando_y_cerrando` → cae R79 (a).
30. Cuenta un parte rechazado como por terminar → cae R79 (c) (el negativo).
31. Ignora el `fallo` del autoguardado → cae R79 (b).
32. `alSalir` no llama a `preventDefault` → cae R78.
33. La guarda escribe `estado.fase` o llama a `estado.pendientes()` → cae R80 (el `Proxy`).
34. Sin Alpine, la guarda pregunta igual (falla cerrada) → cae R80.
35. `target="_blank"` repuesto en la pestaña «Inicio» de `partes.html` → cae R31 y R73.
36. `text-slate-600` repuesto en un `class` estático de `partes.html` → cae R82.

#### 16.15.9 · Riesgos del ajuste

| Riesgo | Mitigación | Dónde se ve |
|---|---|---|
| Alguien acepta el diálogo con una remesa a medias y la pierde | La leyenda de la barra lo avisa antes; el aviso a Posventa (§16.12) lo dice; rechazado/cerrado ya están en la base; F-021 (rehidratar) sigue siendo la solución de fondo | V2 (m), T42 |
| La guarda pregunta cuando no hay nada que perder y se convierte en ruido | Definición estrecha de R79 con negativos probados; (d) se resuelve cerrando el detalle | V2 (l), (o), (p) |
| La guarda no pregunta cuando sí hay algo (un caso que R79 no ve) | Las cuatro condiciones cubren todo lo que el circuito tiene en memoria; el rebote del autoguardado lo cubre (d) con el detalle abierto (con el detalle ya cerrado, sobre un parte rechazado o cerrado por el backend, queda la ventana de 1,5 s que §16.15.2 acepta; errata H16-5 del 2026-10-06); test de fases contra `app.js` | `init.sh`, V2 |
| La guarda toca el circuito sin querer | R80 con el `Proxy` que lanza; R33 sigue vigilando los módulos | `init.sh` |
| `Alpine.$data` no se comporta igual en 3.14.1 | Falla abierta (no rompe nada); V2 (m) lo comprueba en el navegador de verdad. Si no pregunta en V2, **PARA**: se anota y se vuelve a proponer, sin parches | V2 |
| El remodelado rompe algo del circuito | Solo valores de `class` (R59 a) y los `:class` intactos | V2 (k) |

#### 16.15.10 · Decisiones nuevas (con recomendación, para validar)

- **D-15 · Qué cuenta como trabajo sin terminar.** Recomendación: las
  cuatro condiciones de §16.15.2, **sin** contar los ficheros elegidos sin
  trocear. Alternativa: contar también `seleccionado` (pregunta más a
  menudo por algo que se rehace con un gesto).
- **D-16 · La excepción mínima de R81** (un `<script>` en `partes.html` y
  cuatro líneas en dos tests de la base). Recomendación: aceptarla; es la
  única forma de cargar la guarda sin modificar un módulo del circuito.
  Alternativa: dejar el circuito abriendo aparte (lo que el humano
  descartó) o meter la guarda en `js/app.js` (rompe R33).

### 16.16 · El recorrido en todas las páginas (enmienda del 2026-10-06)

#### 16.16.1 · La petición y cómo se lee

Literal, del humano (2026-10-06): **«me gusta el flujo que sale en la
portada con los 7 pasos, me gustaría que saliera siempre en todas las
páginas para visualizar en qué parte del proceso estás»**. Aprobó («si») la
propuesta del líder, que esta spec adopta:

1. La tira del recorrido de la portada (01 Entrada · 02 Revisión · 03 Sigrid
   · 04 Gestión · 05 Parte · 06 Cierre · 07 Coste, con sus enlaces) sale
   **debajo de la barra en las cuatro páginas**: el portal (en todas sus
   secciones), `partes.html`, `importar.html` y `oficios.html`.
2. **Marca el paso actual** (`aria-current="step"` y su estilo).
3. Los pasos de secciones en construcción llevan **el mismo punto ámbar y
   el mismo nombre accesible** que la barra (R66), coherentes con
   `Portal.SECCIONES` y su `estado` (R62).
4. Se navega en la **misma pestaña**, con los mismos enlaces que la barra
   (`Portal.enlaceSeccion`); desde `partes.html`, con trabajo sin terminar,
   salta la guarda de salida (R78–R80), igual que con la barra.
5. Entra en la cabecera de `partes.html` con una excepción **explícita y
   literal** de R59, como la barra (R81, §16.15.4), sin tocar ningún módulo
   del circuito.
6. **Un único origen de verdad** para los pasos.

Requisitos: R83–R89, y R45, R59, R63 y R66 enmendados. Es **presentación y
navegación del front**: no cruza el límite de servicio, no toca
`services/postventa-api/` ni nada de Azure, y no cambia lo que el front
expone ni consume (no hay que tocar `azure-apps/`).

#### 16.16.2 · La correspondencia sección → paso (R83, R86)

`Portal.pasoDeSeccion(id)` devuelve el `num` del **primer** paso de
`Portal.RECORRIDO` cuya `seccion` es `id`; si no hay ninguno, `null`.

| Dónde se está | Sección | Paso marcado | Por qué |
|---|---|---|---|
| Portal, `#/inicio` (y `/`, hash vacío o desconocido, R5) | `inicio` | **ninguno** | La portada no es un paso: enseña el ciclo entero |
| Portal, `#/entrada` | `entrada` | **01 Entrada** | |
| Portal, `#/bandeja` | `bandeja` | **02 Revisión** | Ver la nota de 02 y 03 |
| Portal, `#/incidencias` y `#/incidencias/<id>` (la ficha) | `incidencias` | **04 Gestión** | La ficha es la gestión de una incidencia |
| Portal, `#/impresion` | `impresion` | **05 Parte** | |
| Portal, `#/economico` | `economico` | **07 Coste** | |
| Portal, `#/datos` | `datos` | **ninguno** | «Datos y datamart» no es un paso del ciclo: es transversal |
| `importar.html`, `oficios.html` | `Portal.PAGINAS[página]` = `entrada` | **01 Entrada** | Son las dos páginas de la sección «Entrada» |
| `partes.html` | `partes` | **06 Cierre** | El circuito cierra la incidencia con el parte firmado |

**02 y 03 apuntan hoy los dos a `#/bandeja`.** La revisión y el volcado a
Sigrid (F-040, el panel de volcado) viven en la misma sección. Como
`aria-current` tiene que señalar **un** elemento del conjunto, con la
bandeja visible se marca **solo 02 Revisión**, que es lo primero que hace
la bandeja. **03 Sigrid no se marca nunca** mientras no tenga sitio
propio. Pulsar «03 Sigrid» lleva a la bandeja y se ilumina 02. Es lo
esperado, y V1 (r) lo pide mirar. Cuando una ficha dé al volcado un sitio
propio, cambia la `seccion` del paso `03` en `Portal.RECORRIDO`, y las
guardias de §16.16.7 exigen cambiar con ella las cuatro tiras.

Los enlaces y sus destinos **no cambian** respecto a la tira de la
portada (§15.5): son `enlaceSeccion(paso.seccion, desde)`.

#### 16.16.3 · Un único origen de verdad: `Portal.RECORRIDO` y una guardia (R83, R84)

```js
// js/portal.js, junto a SECCIONES y PAGINAS
/**
 * El ciclo de una incidencia, la tira bajo la barra de las cuatro páginas
 * (R83-R87, design.md §16.16). `seccion` es la de Portal.SECCIONES a la que
 * lleva el paso; el enlace sale de enlaceSeccion(seccion, desde). 02 y 03
 * van a la misma sección (la bandeja): el actual es el PRIMERO
 * (pasoDeSeccion), así que 03 no se marca mientras no tenga sitio propio.
 */
const RECORRIDO = congelarLista([
  { num: "01", etiqueta: "Entrada", seccion: "entrada" },
  { num: "02", etiqueta: "Revisión", seccion: "bandeja" },
  { num: "03", etiqueta: "Sigrid", seccion: "bandeja" },
  { num: "04", etiqueta: "Gestión", seccion: "incidencias" },
  { num: "05", etiqueta: "Parte", seccion: "impresion" },
  { num: "06", etiqueta: "Cierre", seccion: "partes" },
  { num: "07", etiqueta: "Coste", seccion: "economico" },
]);

/** El num del primer paso de esa sección, o null; nunca lanza (R83). */
function pasoDeSeccion(id) { … }
```

Se exportan los dos en el objeto `Portal`, y el comentario de cabecera de
`js/portal.js` los lista. `js/portal_app.js` **no cambia**: el portal
marca el paso con `seccion`, que el componente ya tiene, como la barra.

**Por qué el HTML está escrito en las cuatro páginas, vigilado por una
guardia, y no se genera desde `Portal`.** Es el mismo mecanismo que la
barra (R44: HTML a mano, comparado con `Portal.SECCIONES` y
`enlaceSeccion` por `tests_js/portal.test.js`):

- `partes.html`, `importar.html` y `oficios.html` **no pueden cargar
  `js/portal.js`** (R77). En `partes.html`, generar la tira con JavaScript
  sería código nuevo en el circuito: otro `<script>` y otra excepción de
  R59 y R81, que es justo lo que se pide no tocar. R45 quiere además la
  barra estática, y la tira va con ella.
- Generarla solo en el portal (`x-for` sobre `Portal.RECORRIDO`) dejaría
  igualmente tres copias a mano, y con dos mecanismos distintos para lo
  mismo.
- Con la guardia, la fuente es `Portal.RECORRIDO` (más `SECCIONES`,
  `PAGINAS`, `enlaceSeccion`, `enConstruccion` y `pasoDeSeccion`), y cada
  una de las cuatro copias se compara con ella: número, etiqueta y orden de
  los pasos, `href`, paso actual, punto y `aria-label`. Si las cuatro
  cumplen con la fuente, cumplen entre sí. Cambiar un paso, o el estado de
  una sección (F-038 `done` → `bandeja` `parcial`), deja en rojo las tiras
  que no se actualicen en el mismo trabajo, igual que pasa ya con las
  barras.

Por eso, **en ningún sitio hace falta JavaScript nuevo para el paso
actual**. En las tres páginas reales es fijo y va escrito en el HTML. En el
portal, un `:aria-current` por paso, con la misma forma que el de la barra
(`seccion === '<id>' ? … : false`), que Alpine ya evalúa.

#### 16.16.4 · Dónde va y cómo se ve (R84, R86, R87, R88)

- **Sitio**: hermano **inmediatamente siguiente** del
  `<nav data-barra-portal>`, en las cuatro páginas. En el portal queda
  entre la barra y el aviso de construcción (`data-aviso-maqueta`). R13
  solo exige que el aviso vaya tras la barra, y lo sigue haciendo. En las
  páginas reales, entre la barra y la `<header class="rs-cabecera">`.
- **No es pegajosa.** La barra ya lo es (`position: sticky`) y ya marca la
  sección. Pegar también la tira sumaría arriba, siempre, una fila más en
  escritorio y tres o cuatro en el móvil (las siete píldoras bajan de
  línea). La tira se ve al llegar a cada página y se va al desplazarse.
- **Una sola tira por página.** La `<ol class="rs-recorrido">` de la
  sección `inicio` **se quita**: la tira bajo la barra se ve también en la
  portada y repetirla dentro de su cabecera sería ruido. La cabecera
  (`rs-hero`) termina en la entradilla y siguen las tarjetas.
- **Aspecto**: el de la portada, sin cambios en las píldoras
  (`rs-recorrido`, `rs-recorrido__paso`, `rs-recorrido__num`), dentro de una
  banda `rs-recorrido-banda` al ancho del contenido (`rs-contenedor`), con
  un filete inferior `--rs-linea` y sin fondo propio (se ve el lienzo).
  En el móvil las píldoras bajan de línea, como hoy (sin desplazamiento
  horizontal, V1 e).
- **El paso actual** lo pinta `aria-current="step"`, no una clase, como la
  pestaña actual (R51): borde y texto `--rs-burdeos` sobre
  `--rs-burdeos-suave`, peso 600, y el número en `--rs-papel` sobre
  `--rs-burdeos`. Los dos pares ya están medidos en §15.6 (6,29 y 7,35:
  pestaña actual y botón principal), y sus colores de texto están en la
  lista blanca de R53.
- **El punto ámbar**: la **misma regla** que el de las pestañas, con un
  selector más (§16.4, capa 1, enmendada). `.rs-recorrido__paso` ya es
  `inline-flex`, así que el `::after` conserva sus 6 px.
- **Las hojas**: las reglas de `rs-recorrido*` se **mudan** de
  `css/portal.css` a `css/styles.css`, porque las páginas reales no cargan
  `portal.css` (R77). Se mudan tal cual, salvo dos cambios: el `:hover`
  pasa a `a.rs-recorrido__paso:hover` (y su `.rs-recorrido__num`), como
  `a.rs-pestana:hover`, para que el paso actual sin enlace no reaccione al
  ratón; y se suma el estilo del paso actual. Las dos hojas cambian, así
  que la `?v=` se recalcula en las cuatro páginas (R59 e, R72).

Bloque nuevo de `css/styles.css`, tras el de la barra:

```css
/* ---------- El recorrido de una incidencia (las cuatro páginas, R84-R88) ----- */

/* La banda bajo la barra: no es pegajosa (la barra ya lo es) y va al ancho
   del contenido. */
.rs-recorrido-banda {
  padding-block: 0.75rem;
  border-bottom: 1px solid var(--rs-linea);
}

/* .rs-recorrido, .rs-recorrido > li, .rs-recorrido > li + li::before, su
   @media (max-width: 560px), .rs-recorrido__paso y .rs-recorrido__num:
   movidas TAL CUAL de css/portal.css. */

a.rs-recorrido__paso:hover {
  border-color: var(--rs-burdeos);
  color: var(--rs-burdeos);
}

a.rs-recorrido__paso:hover .rs-recorrido__num {
  background-color: var(--rs-burdeos-suave);
  color: var(--rs-burdeos);
}

/* El paso actual lo pinta aria-current="step", no una clase (R86). */
.rs-recorrido__paso[aria-current="step"] {
  border-color: var(--rs-burdeos);
  background-color: var(--rs-burdeos-suave);
  color: var(--rs-burdeos);
  font-weight: 600;
}

.rs-recorrido__paso[aria-current="step"] .rs-recorrido__num {
  background-color: var(--rs-burdeos);
  color: var(--rs-papel);
}
```

Y la regla del punto, en su sitio de siempre:

```css
.rs-pestana[data-construccion]::after,
.rs-recorrido__paso[data-construccion]::after {
  /* las mismas declaraciones de hoy, sin cambiar ninguna */
}
```

**Alternativas descartadas**:

- **La tira dentro de la barra**, como fila bajo `rs-barra__fila`. En
  `partes.html` no habría tocado R59, porque la guardia quita la barra
  entera. Pero la tira sería pegajosa (ver arriba), mezclaría dos
  navegaciones en un `<nav>` y haría que las guardias de la barra (R44,
  R51, R66, que buscan pestañas por su texto dentro de ella) tuvieran que
  saltarse los pasos.
- **Pegajosa, aparte de la barra**: por el espacio, como arriba.
- **Conservar también la tira de la portada**: dos tiras iguales en la
  misma pantalla.
- **Marcar 02 y 03 a la vez con la bandeja visible**: `aria-current` señala
  un elemento del conjunto, y dos marcados no dicen «dónde estás».
- **Cambiar el destino de 03**: no hay hoy otro sitio para el volcado, y
  los destinos de la tira no cambian (§15.5).

#### 16.16.5 · El marcado, página a página

**`index.html`**, entre el `</nav>` de la barra y el comentario del aviso
de construcción:

```html
    <!-- ── El recorrido de una incidencia (R83-R87), bajo la barra ─────────
         Los pasos, su orden y su sección son los de Portal.RECORRIDO; los
         href, los de Portal.enlaceSeccion(paso.seccion, "portal"). El paso
         actual lo pinta aria-current="step" (css/styles.css): el de
         Portal.pasoDeSeccion de la sección visible; en inicio y en datos,
         ninguno. 02 y 03 van los dos a la bandeja: solo se marca 02. Los
         pasos de secciones en construcción, con el punto de la barra (R87). -->
    <nav data-recorrido aria-label="El ciclo de una incidencia" class="rs-recorrido-banda">
      <div class="rs-contenedor">
        <ol class="rs-recorrido">
          <li><a href="#/entrada" class="rs-recorrido__paso" :aria-current="seccion === 'entrada' ? 'step' : false"><span class="rs-recorrido__num" aria-hidden="true">01</span>Entrada</a></li>
          <li><a href="#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Revisión (en construcción)" :aria-current="seccion === 'bandeja' ? 'step' : false"><span class="rs-recorrido__num" aria-hidden="true">02</span>Revisión</a></li>
          <li><a href="#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Sigrid (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">03</span>Sigrid</a></li>
          <li><a href="#/incidencias" class="rs-recorrido__paso" data-construccion aria-label="Gestión (en construcción)" :aria-current="seccion === 'incidencias' ? 'step' : false"><span class="rs-recorrido__num" aria-hidden="true">04</span>Gestión</a></li>
          <li><a href="#/impresion" class="rs-recorrido__paso" data-construccion aria-label="Parte (en construcción)" :aria-current="seccion === 'impresion' ? 'step' : false"><span class="rs-recorrido__num" aria-hidden="true">05</span>Parte</a></li>
          <li><a href="partes.html" class="rs-recorrido__paso"><span class="rs-recorrido__num" aria-hidden="true">06</span>Cierre</a></li>
          <li><a href="#/economico" class="rs-recorrido__paso" data-construccion aria-label="Coste (en construcción)" :aria-current="seccion === 'economico' ? 'step' : false"><span class="rs-recorrido__num" aria-hidden="true">07</span>Coste</a></li>
        </ol>
      </div>
    </nav>
```

Y en la sección `inicio` se **quita** la `<ol class="rs-recorrido"
aria-label="El ciclo de una incidencia">` con sus siete `<li>`. Las cinco
`:aria-current` nuevas son las de R63 enmendado. Fuera de ellas, la tira
del portal no lleva ninguna directiva.

**`importar.html` y `oficios.html`**, entre el `</nav>` de la barra y el
comentario de las migas. Es el mismo bloque en las dos, con el nombre de
la página en el comentario:

```html
    <!-- F-035 · El recorrido de una incidencia (R83-R88), en HTML PLANO como
         la barra. 01 Entrada es el paso de esta página (Portal.PAGINAS): el
         actual, sin enlace. Los demás href son los de
         Portal.enlaceSeccion(paso.seccion, "importar.html"), en la misma
         pestaña (R73). -->
    <nav data-recorrido aria-label="El ciclo de una incidencia" class="rs-recorrido-banda">
      <div class="rs-contenedor">
        <ol class="rs-recorrido">
          <li><span aria-current="step" class="rs-recorrido__paso"><span class="rs-recorrido__num" aria-hidden="true">01</span>Entrada</span></li>
          <li><a href="./#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Revisión (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">02</span>Revisión</a></li>
          <li><a href="./#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Sigrid (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">03</span>Sigrid</a></li>
          <li><a href="./#/incidencias" class="rs-recorrido__paso" data-construccion aria-label="Gestión (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">04</span>Gestión</a></li>
          <li><a href="./#/impresion" class="rs-recorrido__paso" data-construccion aria-label="Parte (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">05</span>Parte</a></li>
          <li><a href="partes.html" class="rs-recorrido__paso"><span class="rs-recorrido__num" aria-hidden="true">06</span>Cierre</a></li>
          <li><a href="./#/economico" class="rs-recorrido__paso" data-construccion aria-label="Coste (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">07</span>Coste</a></li>
        </ol>
      </div>
    </nav>
```

En `oficios.html`, el comentario dice `"oficios.html"`. Ninguno de los dos
lleva atributos funcionales, así que las huellas de O10-3 y O11-5 no
cambian.

**`partes.html`**: §16.16.6.

#### 16.16.6 · La excepción de `partes.html` (R59 h e i, R89): líneas literales

Dos cambios, y ninguno más. Ningún módulo del circuito, ningún `<script>`,
ningún test de la base.

**(h) La tira**, insertada entre la línea en blanco que sigue al `</nav>`
de la barra (hoy, línea 51) y `<header class="rs-cabecera">` (hoy, línea
53), con una línea en blanco detrás. Literal:

```html
    <!-- F-035 · El recorrido de una incidencia (R83-R89), en HTML PLANO como
         la barra: ni una directiva de Alpine, ni script, ni botón (R88).
         06 Cierre es esta página, el paso actual, sin enlace. Los demás
         href son los de Portal.enlaceSeccion(paso.seccion, "circuito"), en
         la MISMA pestaña: con una remesa a medias, la guarda de salida pide
         confirmación (R78), igual que desde la barra. -->
    <nav data-recorrido aria-label="El ciclo de una incidencia" class="rs-recorrido-banda">
      <div class="rs-contenedor">
        <ol class="rs-recorrido">
          <li><a href="./#/entrada" class="rs-recorrido__paso"><span class="rs-recorrido__num" aria-hidden="true">01</span>Entrada</a></li>
          <li><a href="./#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Revisión (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">02</span>Revisión</a></li>
          <li><a href="./#/bandeja" class="rs-recorrido__paso" data-construccion aria-label="Sigrid (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">03</span>Sigrid</a></li>
          <li><a href="./#/incidencias" class="rs-recorrido__paso" data-construccion aria-label="Gestión (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">04</span>Gestión</a></li>
          <li><a href="./#/impresion" class="rs-recorrido__paso" data-construccion aria-label="Parte (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">05</span>Parte</a></li>
          <li><span aria-current="step" class="rs-recorrido__paso"><span class="rs-recorrido__num" aria-hidden="true">06</span>Cierre</span></li>
          <li><a href="./#/economico" class="rs-recorrido__paso" data-construccion aria-label="Coste (en construcción)"><span class="rs-recorrido__num" aria-hidden="true">07</span>Coste</a></li>
        </ol>
      </div>
    </nav>
```

**(i) El comentario de F-036** de la cabecera (hoy, líneas 58–59). Sale:

```html
          <!-- F-036 (R51) · la entrada de incidencias, en otra pestaña: salir
               de esta perdería la remesa en curso (D4 de F-007). -->
```

y entra, con la misma sangría:

```html
          <!-- F-036 (R51) · la entrada de incidencias, en la misma pestaña
               (F-035, R73): con una remesa a medias, la guarda de salida
               pide confirmación antes de salir (R78). -->
```

**La guardia de R59** (`diferencias_de_presentacion`, en
`tests/test_f035_portal.py`) gana dos pasos, con la misma forma que los de
(c), (f) y (g):

- `_quita_recorrido(ts, sitio)`, después de `_quita_barra`. En el lado
  `partes.html`, si en `sitio` (donde estaba la barra), tras los
  comentarios que lo preceden, empieza un `<nav>` con `data-recorrido`,
  quita esos comentarios y el `<nav>` entero hasta su cierre (contando la
  profundidad de `nav`). Solo **uno** y solo **ahí**: una tira en otro
  sitio, o una segunda, quedan como diferencia. En el lado de la base no
  hay tira.
- `_COMENTARIO_F036_VIEJO` y `_COMENTARIO_F036_NUEVO`, los textos
  literales de (i) con los blancos normalizados. En el lado `partes.html`,
  **ese** comentario nuevo se cambia por el viejo antes de comparar.
  Cualquier otro texto, en ese comentario o en otro, sigue siendo
  diferencia.

El docstring de la función suma (h) e (i). Lo de **dentro** de la tira no
lo mira R59, porque la quita entera: lo vigilan las guardias de R84–R88
(§16.16.7), que también son las que exigen que en `partes.html` sea
estática.

#### 16.16.7 · Ficheros

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/portal.js` | `RECORRIDO`, `pasoDeSeccion`; exportados; el comentario de cabecera los lista |
| `services/postventa-front/index.html` | La tira tras la barra (§16.16.5); fuera la `<ol>` de `inicio`; `?v=` |
| `services/postventa-front/importar.html`, `oficios.html` | La tira tras la barra; `?v=` |
| `services/postventa-front/partes.html` | (h) y (i) de §16.16.6; `?v=` |
| `services/postventa-front/css/styles.css` | El bloque de §16.16.4; el selector más en la regla del punto |
| `services/postventa-front/css/portal.css` | Salen las reglas de `rs-recorrido*` |
| `services/postventa-front/tests_js/portal.test.js` | Tests puros de `RECORRIDO` y `pasoDeSeccion`; la guardia de la tira en las cuatro páginas, con sus controles |
| `services/postventa-front/tests/test_f035_portal.py` | R59 (h) e (i), con tres controles más en `ESTROPEOS_T21` o junto a ellos |
| `services/postventa-front/tests/test_f035_paginas.py` | R63 (la entrada nueva de `directivas_admitidas_r63` y el recuento de 7 a 12); las hojas (R88); el paso actual en la hoja (R86); la cascada del punto (H-6) también para `.rs-recorrido__paso` |
| `services/postventa-front/README.md` | La tira, su fuente y el paso 5 de la retirada (al cambiar el estado de una sección, barra **y tira** en las cuatro páginas) |
| `docs/ARCHITECTURE.md` | Una línea en «El portal de posventa (F-035)»: la tira y `Portal.RECORRIDO` |

**No se tocan**: los nueve módulos del circuito y `js/guarda_salida.js`;
`js/portal_app.js` (el portal marca con `seccion`, que ya tiene);
`js/maqueta_datos.js`; `js/importacion.js`, `js/oficios.js`, `js/api.js`,
`js/config.js`, `js/traza.js`; **ningún test de la base** (`test_f007_*`,
`test_f036_front.py`, `tests_js/importacion.test.js`,
`tests_js/oficios.test.js` y los del circuito); `staticwebapp.config.json`,
`dev_server.py`, `dev_front.ps1`; `infra/*`; `services/postventa-api/`;
`harness/features.json`. Si un test de la base sale en rojo por la tira,
**PARA**: no se toca el test, se anota y se vuelve a proponer.

**Las guardias, una por requisito, cada una con su control en memoria**:

| Guardia | Dónde | Qué mira | Controles (en rojo) |
|---|---|---|---|
| R83 | `tests_js/portal.test.js` | `RECORRIDO`: siete pasos, `num` `01`–`07`, etiquetas y secciones de la tabla de §16.16.2, cada `seccion` en `SECCIONES`, lista y pasos congelados; `pasoDeSeccion` con la tabla entera, más `"desconocida"`, `""`, `undefined`, `null` y `7`, que dan `null` sin lanzar | (la mutación manual 37) |
| R84–R87 | `tests_js/portal.test.js`, una función `problemasDelRecorrido(html, Portal, desde)` que devuelve una lista, como `problemasR66` | Por página: una sola `[data-recorrido]`, que es un `<nav>` con su `aria-label` y es el **hermano siguiente** de la barra; una sola `rs-recorrido` en la página; siete `<li>`, en orden, cada uno con un `rs-recorrido__paso` y su `rs-recorrido__num` `aria-hidden="true"`; número y etiqueta contra `RECORRIDO`; enlace contra `enlaceSeccion(paso.seccion, desde)` (`null` → `<span aria-current="step">` sin `href`), sin `target` ni `rel`; paso actual: en las páginas reales, `aria-current="step"` solo en `pasoDeSeccion(<sección de la página>)`; en el portal, `:aria-current` exactamente `seccion === '<seccion>' ? 'step' : false` solo en los pasos con `pasoDeSeccion(paso.seccion) === paso.num`, ninguno con `aria-current` estático; `data-construccion` y `aria-label` según `enConstruccion`; ninguna forma ligada; ningún `:class` | En una copia en memoria: «Gestión» → «Gestion» en `oficios.html`; dos pasos cambiados de orden en el portal; sin `data-construccion` en 07 de `oficios.html`; `data-construccion` en 01 de `importar.html`; `aria-current="step"` también en 05 de `partes.html`; 06 de `partes.html` como `<a href>`; `:aria-current` en 03 del portal; el de 04 del portal con `'impresion'`; la tira de `importar.html` tras `</header>`; una segunda tira; la `<ol>` de `inicio` repuesta; `target="_blank"` en un paso; y `Portal` falso con la `seccion` de `07` cambiada a `datos` (la guardia lee la fuente, no una lista copiada) |
| R88 (estática) | `tests_js/portal.test.js` | En `partes.html`, `importar.html` y `oficios.html`, dentro de `[data-recorrido]`: ningún atributo `x-*`, `@*` ni `:*`, ni `<script>`, `<button>`, `<form>` ni `<input>` | Un `x-show` en la tira de `partes.html`; un `<button>` en la de `oficios.html` |
| R88 (hojas) | `tests/test_f035_paginas.py` | Ninguna regla de `css/portal.css` nombra `rs-recorrido`; `css/styles.css` tiene `.rs-recorrido`, `.rs-recorrido__paso`, `.rs-recorrido__num` y `.rs-recorrido-banda` | Las reglas de vuelta en `portal.css` |
| R86 (hoja) | `tests/test_f035_paginas.py` | Existe `.rs-recorrido__paso[aria-current="step"]` en `css/styles.css` con `color: var(--rs-burdeos)` | Sin la regla; con otro color |
| R87 (cascada) | `tests/test_f035_paginas.py`, generalizando `problemas_de_la_cascada_r66` | Lo de hoy para `.rs-pestana`, y lo mismo para `.rs-recorrido__paso`: una sola regla sobre su `::after` (la compartida), sin `display`, `visibility`, `opacity` ni `background`, y `.rs-recorrido__paso` `inline-flex` o `flex` | `ESTROPEOS_H6` sigue en rojo, y entran dos: `.rs-recorrido__paso { display: block }` y otra regla sobre `.rs-recorrido__paso::after` |
| R63 | `tests/test_f035_paginas.py` | La entrada nueva de la lista cerrada (R63 enmendado): primer paso con su `href` `#/<id>`; recuento a 12 | `:aria-current` en 03; el de 04 con otro id; un `x-text` en un paso |
| R59 | `tests/test_f035_portal.py` | (h) e (i) | La tira tras `</header>`; dos tiras; otro texto en el comentario de F-036 |

Los demás tests que tocan lo mismo **siguen en verde sin cambios**, porque
miran la barra y no la tira: R44, R51, R66 (`pestanasDeLaBarra` corta en
el primer `</nav>`, que es el de la barra), R13 (el aviso, tras la barra),
R17 (destinos admitidos), R73 (ningún `target`), y las huellas de O10-3 y
O11-5 (la tira no tiene atributos funcionales). Los de R49, R53, R55 y R60
también cubren las reglas movidas.

#### 16.16.8 · Cómo se prueba

Todo sin red, sin BBDD y sin IA.

| Requisito | Test |
|---|---|
| R83 | `tests_js/portal.test.js`: los puros de §16.16.7 |
| R84, R85, R86 (HTML), R87 (HTML) | `tests_js/portal.test.js`: `problemasDelRecorrido` sobre las cuatro páginas, `[]` en cada una, y sus controles |
| R85 (la guarda desde la tira) | Sin test nuevo: la guarda escucha `beforeunload`, que se dispara con cualquier enlace (§16.15.3), y sus tests son los de R78. Lo comprueba V2 (s) |
| R86 (hoja), R87 (cascada), R88 | `tests/test_f035_paginas.py` y `tests_js/portal.test.js`, con sus controles |
| R63 enmendado | `tests/test_f035_paginas.py` |
| R59 (h, i), R89 | `tests/test_f035_portal.py` (R59), y R32, R33 y R43 tal como están: siguen en verde sin tocarse |
| V1 (r), V2 (s), V5 | Manual, humano (`requirements.md` §3) |

Mutaciones manuales (C4 bis), en un worktree desechable del scratchpad,
como las 14–36:

37. `pasoDeSeccion("bandeja")` devuelve `"03"` (el último paso, no el
    primero) → cae R83.
38. En `importar.html`, 01 como `<a href="./#/entrada">` → cae R85/R86.
39. En `partes.html`, `aria-current="step"` también en 05 → cae R86.
40. En el portal, el `:aria-current` de 04 con `'impresion'` → cae R86
    (JS) y R63 (Py).
41. En el portal, `:aria-current` también en 03 → cae R86 y R63.
42. Sin `data-construccion` en 07 de `oficios.html` → cae R87.
43. `data-construccion` en 06 de `partes.html` → cae R87.
44. La tira de `partes.html` movida tras `</header>` → cae R84 y R59 (h).
45. Un `x-show="true"` en la tira de `partes.html` → cae R88 (R59 no lo ve
    porque quita la tira entera: por eso existe R88).
46. Las reglas `rs-recorrido*` de vuelta en `css/portal.css` → cae R88.
47. Otro texto en el comentario de F-036 de `partes.html` → cae R59 (i).
48. La `<ol class="rs-recorrido">` de `inicio` repuesta junto a la tira →
    cae R84.
49. «Gestión» → «Gestion» solo en `oficios.html` → cae R84.
50. `.rs-recorrido__paso { display: block; }` → cae la cascada de R87.

En las de CSS, la `?v=` se recalcula o la guardia se prueba directamente,
para que no las mate la versión (como en T50 y T51).

#### 16.16.9 · Riesgos

| Riesgo | Mitigación | Dónde se ve |
|---|---|---|
| La tira ocupa alto, sobre todo en el móvil (tres o cuatro filas a 390 px) | No es pegajosa; la barra sí, y ya marca la sección | V1 (r), V5 |
| «03 Sigrid» lleva a la bandeja y se marca «02 Revisión» | Decidido y explicado (§16.16.2); el humano lo mira en V1 (r) | V1 (r) |
| Se cambia el estado de una sección y una tira se queda con el punto viejo | La guardia lee `enConstruccion` de `Portal`, y la de la raíz (R62) obliga a cambiar `SECCIONES`: mientras falte una tira, rojo. El README lo añade al paso 5 de la retirada | `init.sh` |
| Un test de la base cae por la tira (un enlace o un `<nav>` más en `partes.html`) | No se toca el test: **PARA** y se vuelve a proponer | `init.sh` |
| `:aria-current` con `false` deja el atributo puesto | Es el mismo patrón de la barra, ya en producción en el portal (Alpine 3 quita el atributo con `false`) | V1 (r), F12 |
| La guarda no salta al salir por la tira | La tira son enlaces normales y la guarda escucha `beforeunload`, sin mirar por dónde se sale | V2 (s) |

#### 16.16.10 · Decisiones (tomadas, para que el humano las valide)

- **D-17 · La tira no es pegajosa**: se ve al llegar a cada página y se va
  al desplazarse (la barra sigue pegada). Alternativa: pegarla con la barra
  (más alto fijo arriba, sobre todo en el móvil).
- **D-18 · La correspondencia de §16.16.2**: «Inicio» y «Datos y
  datamart» no marcan ningún paso; con la bandeja se marca solo 02, y 03
  no se marca hasta que el volcado tenga sitio propio. Alternativa: marcar
  02 y 03 a la vez (descartada por accesibilidad).
- **D-19 · La portada pierde su copia**, la que iba dentro de la cabecera:
  una sola tira por página.
- **D-20 · H16-4 pasa a (i)**: ya que se abre la excepción de R59, el
  comentario desfasado de F-036 en `partes.html` se sustituye en el mismo
  cambio, como dejaba escrito §16.15.4.
