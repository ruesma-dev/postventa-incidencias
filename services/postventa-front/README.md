<!-- services/postventa-front/README.md -->
# postventa-front

Pantalla de carga y revisión de partes de posventa. HTML + Tailwind (CDN) +
Alpine.js + un `dev_server.py` de biblioteca estándar. **Sin cadena de build,
sin `package.json`, sin `node_modules`.**

En producción va desplegado como **Static Web App** con la Function enlazada al
mismo origen; eso es **F-010**. En local, `dev_server.py` reproduce ese mismo
comportamiento.

> **Desde F-035 (2026-09-25) el front tiene dos páginas.** La portada
> (`index.html`, lo que se abre en `/`) es el **portal de posventa**, una
> maqueta con datos de ejemplo; el circuito de partes firmados de este README
> vive en **`partes.html`**, byte a byte el de antes salvo la barra superior
> común. Donde este README dice «`index.html`» hablando del circuito, léase
> `partes.html`. La maqueta se explica en «La maqueta del portal (F-035)».

## Arrancar en local

Hacen falta **dos terminales**. El humano trabaja en PowerShell: una línea por
línea, sin `&&`.

**Terminal A — el backend** (la Azure Function):

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
func start --port 7073
```

El **7073 no es el puerto por defecto de `func`**: es el que espera el proxy.
Si no existe `local.settings.json`, cópialo antes de
`local.settings.json.example` y rellénalo.

**Terminal B — el front**:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
.\dev_front.ps1
```

Y en `http://localhost:5173/`. El script es un envoltorio de una línea sobre:

```
python dev_server.py --port 5173 --api http://localhost:7073
```

Para ver la ayuda **sin arrancar nada**:

```
.\dev_front.ps1 -Ayuda
```

> **Por qué `-Ayuda` y no `-?`.** Con `powershell -File`, Windows PowerShell 5.1
> se queda el `-?`: no ejecuta el script (bien) pero tampoco imprime nada. Y la
> ayuda basada en comentarios (`<# .SYNOPSIS #>`) solo la indexa `Get-Help` si
> el bloque es **lo primero** del fichero, lo que chocaría con la convención de
> abrir cada fichero con un comentario con su ruta. `-Ayuda` funciona con
> `-File` y respeta las dos cosas.

## Probarlo

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
python -m pytest -q
```

Eso ejecuta **todo**: los tests de Python y, a través del puente
`tests/test_f007_js.py`, los de JavaScript. Para lanzar solo estos últimos:

```
node --test "tests_js/*.test.js"
```

> **El argumento es el patrón, no la carpeta.** Desde Node 24, `node --test
> tests_js` intenta cargar el directorio como módulo y muere con
> `MODULE_NOT_FOUND` sin descubrir ningún test.

**Si `node` no está, la suite FALLA diciéndolo**, no se salta con un `skip`: un
salto silencioso volvería a dejar el front sin comprobar.

El servicio está declarado en `harness/servicios.json`, así que
`bash harness/init.sh` ejecuta esta suite y se pone en rojo si falla.

## Cómo está organizado, y por qué se puede probar sin navegador

```
js/cola.js       lógica pura        sin fetch, sin DOM   ← el grueso de los tests
js/pipeline.js   orquestación       recibe `api` inyectada
js/seleccion.js  lógica pura        sin DOM (recibe File[])
js/traza.js      lógica pura
js/confirmacion.js  lógica pura     el doble clic antes de archivar (R19)
js/api.js        adaptador HTTP     `fetch` y temporizadores inyectables
js/app.js        pegamento Alpine   NO se prueba: no debe tener lógica
```

**Regla de oro: si algo merece un test, no vive en `app.js`.** Hay dos guardias
en `tests/test_f007_estaticos.py` que lo vigilan, porque `app.js` es la única
habitación sin tests de la casa.

Los módulos se exponen en las dos direcciones —`window.X` para el navegador,
`module.exports` para `node --test`—, que es lo que permite probarlos sin
herramientas nuevas.

## La maqueta del portal (F-035)

### Qué es

La **portada** del front (`index.html`) es el portal de posventa: el ciclo
entero —entrada, bandeja de revisión, incidencias con su ficha, impresión,
partes firmados, coste y datos— en una barra superior de ocho pestañas. Salvo
«Partes firmados», **todas son una maqueta**: datos de ejemplo ficticios y
botones que todavía no hacen nada. Sirve para validar el recorrido con
Posventa antes de construir cada pieza (F-036 a F-048), no para trabajar.

El **circuito de partes firmados**, el que está en producción, se mudó de
`index.html` a **`partes.html`** con `git mv` y es la pestaña «Partes
firmados». No cambió ni una línea de su lógica: solo su nombre de fichero, su
línea 1 y la barra superior añadida encima, que es HTML plano sin Alpine; y,
desde la segunda ronda, su aspecto (clases y fuentes: ver «Identidad visual
Ruesma (F-035)», más abajo).

| Fichero | Qué es |
|---|---|
| `index.html` | El portal (la portada `/`): barra superior, aviso de maqueta, siete secciones con rutas por hash (`#/bandeja`, `#/incidencias/EJ-0003`…) |
| `partes.html` | El circuito de siempre, con la barra superior encima |
| `js/maqueta_datos.js` | `window.MaquetaDatos`: **solo** datos de ejemplo, por bloques, cada uno con la ficha que lo sustituirá (`ficha: "F-0NN"`) |
| `js/portal.js` | `window.Portal`: catálogos (`SECCIONES`, `PLACEHOLDERS`, `ESTADOS`) y funciones puras. Sin DOM ni red |
| `js/portal_app.js` | `portalPosventa()`: el componente de Alpine, pegamento sin lógica (misma regla de oro que `app.js`) |
| `css/styles.css` | La hoja de la marca, **compartida** por el portal y el circuito: tokens `--rs-*`, barra, botones, paneles… |
| `css/portal.css` | Lo que solo usa el portal: `.placeholder`, aviso de maqueta, portada, tarjetas, chips de estado, ficha |
| `img/logo-ruesma.svg`, `img/favicon.svg` | Copias exactas de los de `front-portal` |

Los ficheros de la maqueta **no hablan con nadie**: ni `fetch`, ni
`XMLHttpRequest`, ni `/api/`, ni Sigrid, ni SharePoint, ni correo (R14–R16 de
`specs/F-035-portal-posventa/requirements.md`, vigilado por
`tests/test_f035_portal.py` y `tests_js/portal.test.js`).

### Cómo se abre en local

Igual que el circuito, con `.\dev_front.ps1` desde esta carpeta (sección
«Arrancar en local»):

- `http://localhost:5173/` → el **portal** (la portada).
- `http://localhost:5173/partes.html` → el **circuito**. Para verlo hablar con
  el backend hace falta además `func start` (terminal A); para la maqueta, no.

Desde el portal, la pestaña «Partes firmados» lleva al circuito en la misma
pestaña del navegador. Desde el circuito, las otras siete se abren **en otra
pestaña**: la remesa en curso vive en memoria y salir de la página la
perdería.

### Cómo se reconoce un placeholder

Un botón que todavía no hace nada lleva el atributo
**`data-placeholder="F-0NN"`** con la ficha que lo construirá, la clase
`.placeholder` (borde discontinuo y fondo rayado), una etiqueta `F-0NN`
visible y `aria-disabled="true"`. No está deshabilitado a propósito: al
pulsarlo, la franja de aviso de abajo dice qué haría y qué ficha lo construye,
y nada más (sin red, sin temporizadores). Todo lo demás —pestañas, filtros,
selección, abrir una ficha, abrir el panel de «no procede»— funciona, pero
solo en pantalla y sobre los datos de ejemplo.

### Cómo se retira, ficha a ficha

Cuando una ficha F-0NN construya su pieza, **en el mismo trabajo**
(`specs/F-035-portal-posventa/design.md` §7.3):

1. Borra de `index.html` los elementos con `data-placeholder="F-0NN"` y pone
   en su lugar los controles reales.
2. Borra de `Portal.PLACEHOLDERS` (`js/portal.js`) sus entradas y de
   `js/maqueta_datos.js` su bloque (o su parte del bloque), y cambia los
   `x-for` que lo pintaban por los datos reales.
3. Si la sección real habla con el backend, lo hace desde **sus propios**
   módulos (el patrón de `js/api.js`), no desde los de la maqueta.
4. **Si con ella la sección entera pasa a ser real** (todas las fichas de su
   entrada de `Portal.SECCIONES` en `done`; `inicio`, cuando lo son todas las
   demás), quita el `target="_blank"` de su enlace en la barra de
   `partes.html`: desde el circuito se va a una sección real **en la misma
   ventana**, como en una web normal (R48). Y en el mismo trabajo resuelve
   lo que eso rompe: la **remesa** en curso vive en memoria y se perdería al
   salir, así que la ficha decide cómo no perderla (aviso al salir o
   recuperar el trabajo) y lo propone al humano. Mientras la sección sea
   maqueta, se sigue abriendo aparte (R31). Lo vigila la guardia de la raíz
   `tests/test_f035_placeholders_vivos.py`.

Si se olvida, la guardia de la **raíz** `tests/test_f035_placeholders_vivos.py`
(R28) se pone en rojo en cuanto la ficha pase a `done` en
`harness/features.json`, con el fichero y la línea de cada resto. Vive en la
raíz y no aquí porque la suite del front se salta por caché cuando su árbol no
cambia. Cuando no quede ninguna ficha con restos, la última borra
`js/maqueta_datos.js` y la parte de `js/portal.js` que solo sirve a la
maqueta.

## Identidad visual Ruesma (F-035)

Las dos páginas —el portal y el circuito— visten la identidad del portal
corporativo de Ruesma. La referencia es `front-portal` (su `public/index.html`
y `public/assets/css/styles.css`), leída **solo en lectura**: no se copia su
hoja, se toma su lenguaje (burdeos `#9f2842`, gris acero, trama de plano,
Bricolage Grotesque para titulares y Archivo para el texto, radios de 16 y
10 px, botones en píldora, barra con logotipo). Diseño completo:
`specs/F-035-portal-posventa/design.md` §15.

**Dónde vive.** Los **tokens** (`--rs-burdeos`, `--rs-acero-texto`,
`--rs-radio`…) están en el `:root` de **`css/styles.css`**, la hoja que
cargan las dos páginas; ahí van también la barra, los botones, los paneles,
los avisos y los componentes del circuito (clases `rs-*`). `css/portal.css`
lleva lo que solo usa el portal. Fuera del `:root`, un color, una sombra o
un radio se escriben **siempre** con `var(--rs-…)` (R49). Las fuentes vienen
de Google Fonts con `display=swap` (si no cargan, se ve la de reserva; no se
rompe nada) y el logotipo y el favicon, de `img/`, copias byte a byte de los
de `front-portal` (R52).

**Reglas** (cada una con su test en `tests/test_f035_portal.py`):

- **Contraste (R53)**: todo par texto/fondo de los tokens llega a AA (4,5:1),
  calculado por el test desde el `:root`. El gris acero (`--rs-acero`, 3,7:1)
  **no** se usa para texto: el texto gris es `--rs-acero-texto`.
- **Foco (R54)**: `:focus-visible` con contorno burdeos en todo; ninguna regla
  lo quita sin poner otro.
- **Movimiento (R55)**: transiciones de 250 ms como mucho y solo de color,
  fondo, borde, sombra, opacidad o `transform`; las entradas animadas, solo en
  el portal; con `prefers-reduced-motion: reduce` no se mueve nada.
- **La maqueta se sigue viendo maqueta (R56)**: el borde **discontinuo** es
  solo de los placeholders; ningún placeholder lleva el burdeos de la marca ni
  `rs-btn--primario`, y el aviso de maqueta va en su color de atención. El
  burdeos es la marca y la acción principal, **nunca** un estado.
- **Estados con texto (R57)**: cada estado va en un chip `rs-chip` con su
  `data-estado` y su texto; el color nunca es la única pista.
- **Sin `!important` ni `@import` ni `data:` (R60)**: Alpine esconde con
  `style="display: none"` en línea y un `!important` sobre `display` lo
  taparía (la pregunta de confirmación del circuito saldría siempre). Única
  excepción, `[x-cloak]` de `css/portal.css`. Y `partes.html` no lleva
  atributos `style`.

**En el circuito solo se cambian clases (R59).** `partes.html` está en
producción: frente al `index.html` de antes de F-035 solo pueden cambiar los
**valores de `class`**, la barra superior y las cuatro `<link>` de las
fuentes y el favicon. Ni una directiva de Alpine (tampoco las `:class` de
estado, que siguen pintando el semáforo con Tailwind), ni un id, ni un
texto, ni el orden de los atributos. Lo comprueba una guardia que compara el
HTML como secuencia de etiquetas, con un control que demuestra que mira.
Una sola clase estática del circuito la fija un test ajeno a F-035:
`text-red-800` en el aviso de fallo del autoguardado
(`test_f026_autoguardado.py`); por eso sigue ahí junto a `rs-aviso--error`.

## Tres cosas del `index.html` que parecen cosméticas y no lo son

> **Nota de F-035 (2026-09-25).** Esta sección habla del **circuito**, que
> desde F-035 vive en `partes.html`: las tres reglas se aplican ahí, y
> también al portal de `index.html` (R34), con sus propios scripts.

1. **Los scripts propios van al final del `<body>` y SIN `defer`.** Con
   `defer`, Alpine arrancaría antes de que exista `appPostventa` y la pantalla
   quedaría muerta.
2. **Alpine sí va con `defer`, en el `<head>` y con versión fija `3.14.1`.**
3. **Ningún `type="module"`**: un módulo se difiere de forma implícita, que es
   el mismo fallo por otra puerta.

Las tres las vigila `tests/test_f007_estaticos.py`.

## `dev_server.py` frente a la puerta de cobertura (decisión D1)

**Se prueba.** Es la opción **O1** de `specs/F-007-front/design.md` §9, y la
confirmó el humano el **2026-08-20**.

**El problema.** `harness/alcance.py` considera código de producción cualquier
`.py` cuya ruta no lleve un segmento `tests`, `specs`, `progress` o `docs`. No
hay lista de exclusiones, ni por fichero ni por servicio. `dev_server.py` llega
**entero como fichero nuevo** frente a `dev`, así que sus ~114 líneas entran en
el alcance de la feature hagamos lo que hagamos: **no existe la opción «no
tocarlo»**. Sin tests, la puerta lo cuenta como no cubierto y `init.sh` se pone
en rojo. Eso es exactamente lo que expulsó al front de F-001.

**Lo que se descartó, y por qué:**

| | Opción | Por qué no |
|---|---|---|
| **O2** | Añadir exclusiones configurables al arnés | Abre una puerta que se ensancha sola: cualquier fichero incómodo pasa a ser «script de desarrollo». Y es trabajo de **otro producto** (`arnes-base`), con su regla de propagación, no de esta feature |
| **O3** | Esconderlo en una carpeta ya excluida (`tests/`, `docs/`) | Es mentira: un servidor de desarrollo no es documentación ni un test. Y enseña el truco: «si no lo puedes probar, muévelo a `tests/`» |
| **O4** | Adelgazarlo hasta que casi no tenga líneas | Reescribir algo que ya funciona y está verificado. No elimina el problema, solo lo encoge |
| **O5** | Cerrar con el portero en rojo | `CLAUDE.md` lo prohíbe |

**Por qué O1 es mejor, y no solo «la que quedaba»:**

1. **Cierra dos criterios con el mismo trabajo**: que alguien compruebe el
   front, y qué hacer con `dev_server.py`. O2 y O3 resuelven el segundo y dejan
   el primero igual de abierto.
2. **`dev_server.py` no es un script cualquiera.** Es el único sitio donde se
   reproduce el comportamiento de la SWA en producción: proxy al mismo origen,
   cabeceras reenviadas, `x-ms-client-principal`. Si se rompe, el desarrollo
   local deja de parecerse al despliegue y nadie se entera hasta F-010. Es
   código que **merece** tests.
3. **Es barato y no toca el arnés.** El fichero no abre red por sí mismo: la
   conexión se crea en `_proxy` a través de `http.client.HTTP(S)Connection`,
   que en los tests se sustituye por un doble. Ni un socket.

Resultado: `tests/test_f007_dev_server.py`, y la puerta de cobertura mide esas
líneas en vez de contarlas como no medidas.

## Lo que este front NO hace (a propósito)

- **No guarda nada.** Ni `localStorage`, ni `sessionStorage`, ni `IndexedDB`,
  ni cookies. **Recargar la pestaña pierde el trabajo de revisión** y hay que
  volver a subir la remesa. Se acepta para el piloto (decisión **D4** del
  2026-08-20). La vía fácil está **prohibida**: los partes llevan DNI y
  observaciones manuscritas de clientes. La solución de verdad son endpoints de
  persistencia en `postventa-api`, dados de alta como
  **F-019 · Endpoints de persistencia**. Hay un test que impide tomar el atajo.
- **No hace login.** `/.auth/me`, el grupo de Entra y el `<TENANT_ID>` de
  `staticwebapp.config.json` son **F-010**. En local el backend va con
  `AUTH_DISABLED`.
- **No cierra la incidencia en Sigrid.** Es F-008 / F-009, y depende de un
  endpoint nuevo en otro repositorio.
- **No archiva desde tu puesto.** `/api/archivar` responde **503 «este entorno
  no archiva»** con la puerta de entorno apagada, que es lo **correcto**. El
  front lo pinta en azul y no en rojo justamente para que nadie intente
  «arreglarlo» tocando esa puerta.

## Datos personales

Los partes traen **DNI y observaciones manuscritas** de clientes reales.

- **Sí se enseñan en pantalla**: quien revisa los necesita para corregir una
  lectura y para decidir si el parte se cierra.
- **No se registran en ningún sitio.** El único registro que el front emite
  pasa por `js/traza.js`, que acepta **cuatro claves** (`hash`, `paso`,
  `estado`, `http`) y tira el resto. Es un filtro, no una convención.
- **No viajan al archivar**: `/api/archivar` recibe cinco campos y ninguno es
  personal.
- **No entran en el repositorio**: los fixtures son PDFs mínimos construidos en
  el propio test. Lo vigila `tests/test_f007_sin_datos_reales.py`.

## Navegador soportado

**Edge / Chrome** (decisión **D5**). El selector de carpeta usa
`webkitdirectory`, que Firefox no implementa igual. Es el navegador corporativo.

## Sobre `staticwebapp.config.json`

**No lleva comentarios, y no es un olvido**: el esquema de Static Web Apps
declara `additionalProperties: false`, así que cualquier clave de más —un
`$comentario`, por ejemplo— hace que la CLI **rechace el fichero entero** con
un `NoAdditionalPropertiesError`. Pasó de verdad al desplegar F-010 el
2026-08-21: Azure lo aceptaba igualmente, pero fiarse de eso es frágil, porque
el día que la CLI deje de subir la configuración la aplicación se queda **sin
autenticación** y sin que nadie se entere. Por eso lo que había que explicar se
explica aquí.

- **`openIdIssuer` lleva el marcador `<TENANT_ID>` a propósito.** El
  identificador de inquilino no se versiona (regla de `CLAUDE.md`). Lo
  sustituye `infra/desplegar_front.ps1` **en una copia de trabajo temporal**,
  que se borra al terminar: el fichero del repositorio no se toca nunca.
- **`clientIdSettingName` y `clientSecretSettingName` no son valores, son
  punteros**: nombran App Settings de la Static Web App (`AZURE_CLIENT_ID` y
  `AZURE_CLIENT_SECRET`), que el despliegue rellena desde el Key Vault. Es la
  misma convención que usan el portal y los demás fronts del ecosistema.
- **`allowedRoles: ["authenticated"]` NO restringe por grupo**: solo exige
  estar autenticado. Quien impide entrar a quien no es del piloto es la
  **asignación requerida** de la aplicación empresarial en Entra, con el grupo
  `posventa-usuarios` asignado. Sin eso, cualquiera de la empresa entraría
  aunque no vea la tarjeta en el portal.

### La ruta que evita el bucle de inicio de sesión

La **primera** ruta de `staticwebapp.config.json` es esta, y no se puede
quitar:

```json
{ "route": "/.auth/login/aad", "allowedRoles": ["anonymous", "authenticated"] }
```

**El orden importa: manda la primera ruta que casa.** Sin ella, el `/*` de
abajo —que exige `authenticated`— captura también **la propia página de inicio
de sesión**: pides `/.auth/login/aad`, la plataforma exige sesión para poder
iniciar sesión, responde 401, el `responseOverrides` te devuelve a
`/.auth/login/aad`, y así indefinidamente. Entra corta el ciclo con
**`AADSTS50196`**, cuyo mensaje —«No podemos iniciar su sesión»— no dice nada
de bucles y manda a buscar en el sitio equivocado.

Ocurrió de verdad al desplegar F-010 el 2026-08-21. El patrón correcto se copió
de `front-portal`, que lleva meses en producción con él.
