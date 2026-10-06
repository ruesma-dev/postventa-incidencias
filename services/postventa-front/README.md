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
>
> **Desde la enmienda del 2026-10-05 (F-035, opción b)** el portal se publica
> **en producción entero**: lo que funciona (la entrada de incidencias con
> `importar.html` y `oficios.html`, y el circuito) y lo que todavía no, marcado
> **«En construcción»**. Las cuatro páginas llevan la misma barra superior y
> todo se navega **en la misma pestaña**; la remesa del circuito la protege la
> guarda de salida. Detalle en «La maqueta del portal (F-035)».

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

Desde F-036 hay dos páginas más, cada una con su módulo (lógica pura más su
componente Alpine, que se prueba en `node --test` con un `api` doble):

```
importar.html   js/importacion.js   plantilla, importación y bandeja    (F-036 §9)
oficios.html    js/oficios.js       oficios repetidos en Sigrid          (F-036 §15.6)
```

Y desde F-035, en el circuito, `js/guarda_salida.js`: la guarda de salida
(lógica pura más un `beforeunload`, probada en `tests_js/guarda_salida.test.js`
con dobles; ver «La maqueta del portal (F-035)»).

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
pestaña del navegador. Desde el circuito, las otras siete se abrían **en otra
pestaña** para no perder la remesa en curso; desde el ajuste del 2026-10-05
ya no: ver «Todo en la misma pestaña, y la guarda de salida del circuito»,
más abajo.

### El portal en producción, con secciones en construcción (enmienda del 2026-10-05)

Con F-036 cerrada, el humano decidió (opción b) **publicar el portal
entero**: lo que funciona y lo que no, marcado. Lo que antes se llamaba
«maqueta» es, para quien lo usa, **«En construcción»**: datos inventados y
botones que no hacen nada todavía, para que Posventa vea el recorrido
completo. Ningún texto visible del portal dice «maqueta» (R67). Diseño:
`specs/F-035-portal-posventa/design.md` §16.

**El `estado` de cada sección.** Cada entrada de `Portal.SECCIONES`
(`js/portal.js`) declara, escrito literal, su `estado`: `real`, `parcial` o
`construccion` (R62). Sale de las fichas de `harness/features.json`:
`construccion` si ninguna está `done`, `parcial` si alguna, `real` si todas;
`partes` (el circuito) es `parcial` mientras F-045 no esté `done`; `inicio`
es `real` solo cuando lo son las otras siete, `partes` incluida. Hoy:
`inicio`, `entrada` y `partes`, `parcial`; las otras cinco, `construccion`.
Si una ficha se cierra y el `estado` no se actualiza, la guardia de la
**raíz** `tests/test_f035_placeholders_vivos.py` se pone en rojo (sin caché,
como R28). `Portal.enConstruccion(id)` lo consulta.

**El rótulo, en tres capas, y cómo se reconoce** (`design.md` §16.4):

1. **En la barra** de las cuatro páginas: la pestaña de una sección en
   construcción lleva `data-construccion`, un **punto ámbar** tras la
   etiqueta y `aria-label="<etiqueta> (en construcción)"` (R66). Las barras
   de las páginas reales llevan además una leyenda (`rs-barra__leyenda`) que
   explica el punto.
2. **En la sección**: todo lo inventado va **dentro** de un recuadro
   `data-en-construccion` con la clase `rs-obras` (borde ámbar continuo y una
   cinta de obra arriba, nunca discontinuo ni burdeos), que empieza por su
   rótulo `rs-obras__rotulo`: el chip «En construcción», «Todavía no
   funciona…», que son datos inventados, que no es información real y que no
   se guarda nada, y qué fichas lo construirán (`F-0NN · <título>`, de
   `Portal.fichasDeSeccion`). Una sección en `construccion` tiene **un**
   recuadro de sección (`data-en-construccion="<id>"`); una que no lo está
   solo lleva recuadros de bloque (`data-en-construccion="F-0NN"`) en lo que
   le falte: hoy, la web de clientes (F-037) en `entrada` y el registro sin
   firma (F-045) en la tarjeta «Partes firmados» (R63–R65). El rótulo no se
   puede cerrar ni esconder (ni `x-show`, ni `hidden`, ni `sr-only`, ni
   `style`). Fuera de los recuadros, `index.html` solo admite una **lista
   cerrada** de directivas de Alpine (R63 enmendado): un dato inventado que
   se escape del recuadro pone la suite en rojo.
3. **En la portada**: ninguna cifra inventada; las tarjetas de lo que está
   en construcción llevan su chip «En construcción», y las de lo que
   funciona («Entrada de incidencias» y «Partes firmados»), «En producción»
   (R67). Y bajo la barra, el aviso permanente (R13).

**Las páginas reales: `Portal.PAGINAS`.** `importar.html` y `oficios.html`
son **páginas propias** del portal, de la sección `entrada`:
`Portal.PAGINAS = {"importar.html": "entrada", "oficios.html": "entrada"}` es
la única fuente de qué página real pertenece a qué sección (`partes.html` no
entra: es la sección `partes` misma). Llevan la barra común en HTML estático
con «Entrada» como pestaña actual, migas y subnavegación, la identidad
Ruesma y nada de la maqueta (R70–R73, R77); los enlaces de su barra los da
`Portal.enlaceSeccion(id, "<página>.html")`. El portal las presenta desde
`#/entrada` con dos tarjetas «En producción», y el recuadro de `bandeja`
enlaza a `importar.html#bandeja`, donde está la bandeja de solo lectura de
F-036 (R68, R69).

**El recorrido bajo la barra (enmienda del 2026-10-06, R83–R89).** Las
cuatro páginas llevan, justo debajo de la barra y sin pegarse arriba al
desplazarse, la **tira del recorrido**: los siete pasos del ciclo de una
incidencia (01 Entrada · 02 Revisión · 03 Sigrid · 04 Gestión · 05 Parte ·
06 Cierre · 07 Coste), con el paso en el que estás marcado con
`aria-current="step"` en burdeos y el mismo punto ámbar que la barra en los
pasos de secciones en construcción. Su **fuente** es `Portal.RECORRIDO`
(`js/portal.js`), con `Portal.pasoDeSeccion`; las cuatro tiras van escritas
a mano, como la barra, y una guardia (`problemasDelRecorrido`, en
`tests_js/portal.test.js`) compara cada una con la fuente: pasos, enlaces
(`Portal.enlaceSeccion`), paso actual, punto y `aria-label`. La
correspondencia: cada sección marca el **primer** paso que lleva a ella
—entrada → 01, bandeja → 02 (nunca 03, que también va a la bandeja),
incidencias y su ficha → 04, impresión → 05, partes → 06, económico →
07—; inicio y datos no marcan ninguno, e `importar.html` y `oficios.html`
marcan 01. En `partes.html`, `importar.html` y `oficios.html` la tira es
HTML estático y el paso actual va fijo; en el portal lo marca un
`:aria-current` por paso. Sus estilos viven en `css/styles.css`, que cargan
las cuatro páginas.

### Todo en la misma pestaña, y la guarda de salida del circuito

**Regla (ajuste del 2026-10-05, R73; absorbe R48):** ningún enlace entre
páginas del front abre aparte. Del portal, de `importar.html`, de
`oficios.html` **y también del circuito**, todo se navega en la **misma
pestaña** («misma ventana», como una web normal): ni la barra, ni las
cabeceras, ni las tarjetas llevan `target`. Lo único que sigue abriendo
aparte es lo que no es del front (el «abrir en SharePoint» del circuito).
R48 pedía la misma ventana para las secciones reales y dejar que la ficha
que lo activara resolviera la **remesa** en curso; con todo en la misma
pestaña, eso queda cumplido de antemano y la remesa la protege la guarda.

**La guarda de salida** (`js/guarda_salida.js`, R78–R80; `design.md`
§16.15.2–§16.15.4):

- **Qué cuenta como trabajo sin terminar** (R79): (a) algo en marcha
  (trocear, procesar, archivar y cerrar, o una tanda en curso); (b)
  correcciones sin guardar (el autoguardado guardando o en fallo); (c) algún
  parte sin cerrar que no esté rechazado ni cerrado; (d) un parte abierto en
  el detalle sin cerrar. **No** lo es la página recién abierta, los ficheros
  elegidos sin trocear, una remesa con todo cerrado o rechazado y el detalle
  cerrado, ni lo que queda tras «Empezar otra remesa». Con trabajo, el
  navegador pide confirmación al salir (su texto, no uno propio); sin él, se
  navega sin preguntar.
- **Que solo lee** (R80): lee el estado de `appPostventa()` con
  `Alpine.$data` en el momento de salir y usa los selectores puros de
  `Pipeline` y `Autoguardado`; no escribe, no llama a métodos del
  componente, ni red ni almacenamiento. Si no puede leer el estado, **no
  pregunta** (falla abierta).
- **Dónde vive**: un solo `beforeunload`, en su propio módulo, cargado en
  `partes.html` con un `<script>` justo antes del de `js/app.js`.
- **La excepción de R81**: para cargarla sin tocar ningún módulo del
  circuito (R33) hacen falta, y solo esas, ese `<script>` en `partes.html`,
  una línea en `ORDEN_CANONICO` de `tests/test_f007_estaticos.py` y las
  líneas de R51 de `tests/test_f036_front.py` (los enlaces de la cabecera,
  ahora sin `target`). Las guardias de R32, R33, R43 y R59 admiten
  exactamente eso.

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
4. *(Superado por el ajuste del 2026-10-05.)* Decía que, cuando la sección
   entera pasara a ser real, se quitara el `target="_blank"` de su enlace en
   la barra de `partes.html` (R48). Hoy no queda ningún `target` en la barra
   del circuito: todo va en la misma ventana y la remesa la protege la
   guarda de salida. La guardia de R48 de la raíz sigue, en verde por
   construcción.
5. **Actualiza el `estado` de su sección** en `Portal.SECCIONES` (R62). Si
   la sección deja de estar en `construccion`, quita su recuadro de sección,
   saca de él lo que ya funciona y deja en recuadros de bloque
   `data-en-construccion="F-0NN"` lo que siga sin funcionar (R64); y quita el
   `data-construccion` y el `aria-label` de su pestaña en **las cuatro
   barras** (R66) **y de sus pasos en las cuatro tiras del recorrido**
   (R87), en el mismo trabajo. Si se olvida, la guardia de R62 de la raíz se
   pone en rojo, y la de la tira (`tests_js/portal.test.js`) también.
6. **Si la sección real vive en su propia página** (el patrón de
   `importar.html` y `oficios.html`), esa página lleva la barra común en HTML
   estático, la identidad Ruesma y nada de la maqueta (R70–R73, R77), y se
   declara en `Portal.PAGINAS` con su sección.

Si se olvida, la guardia de la **raíz** `tests/test_f035_placeholders_vivos.py`
(R28) se pone en rojo en cuanto la ficha pase a `done` en
`harness/features.json`, con el fichero y la línea de cada resto. Vive en la
raíz y no aquí porque la suite del front se salta por caché cuando su árbol no
cambia. Cuando no quede ninguna ficha con restos, la última borra
`js/maqueta_datos.js` y la parte de `js/portal.js` que solo sirve a la
maqueta.

## Identidad visual Ruesma (F-035)

Las dos páginas —el portal y el circuito— visten la identidad del portal
corporativo de Ruesma, y desde la enmienda del 2026-10-05 también las dos
páginas reales de la entrada, **`importar.html`** y **`oficios.html`**
(R70–R72): la misma barra con su leyenda, migas y subnavegación, componentes
`rs-*`, el pie común y ninguna utilidad de color de Tailwind de la lista
cerrada. Es presentación: su lógica (`js/importacion.js`, `js/oficios.js`,
`js/api.js`) no cambió por el estilo. La referencia es `front-portal` (su `public/index.html`
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
  **no** se usa para texto: el texto gris es `--rs-acero-texto`. Desde el
  2026-10-06, **lista blanca**: fuera del `:root`, todo `color` vale
  `inherit`, `currentColor` o un `var()` de los tokens medidos como texto;
  única excepción, `--rs-acero-300` en el índice decorativo
  `.rs-tarjeta__indice`, que lleva `aria-hidden="true"`.
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

**El remodelado del circuito, terminado (R82, ajuste del 2026-10-05).**
`partes.html` ya **no lleva utilidades de color de Tailwind** en sus `class`
estáticos: pasaron a componentes `rs-*` (`rs-nota`, `rs-enlace`,
`rs-rotulo`, `rs-aviso--atencion`…), con `text-red-800` como única
excepción, por lo de arriba. Las que quedan son las de los **`:class` de
estado** (el semáforo), que no se tocan (R59). Lo vigila una guardia con
lista cerrada en `tests/test_f035_paginas.py`. A R59 se suman además
(f) el `<script>` de la guarda de salida y (g) la retirada de `target` y
`rel` en los dos enlaces de la cabecera a `importar.html` y `oficios.html`.

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

## La entrada de incidencias (F-036)

Dos páginas propias, enlazadas desde la cabecera de `index.html` y abiertas
**en otra pestaña**: salir de `index.html` perdería la remesa en curso (D4).

> **Desde F-035 (enmienda del 2026-10-05) son secciones del portal.** Las
> dos son páginas reales de la sección «Entrada» (`Portal.PAGINAS`), con la
> barra común, migas y la identidad Ruesma, y se abren **en la misma
> pestaña**, también desde el circuito (que ahora es `partes.html` y protege
> la remesa con la guarda de salida). Ver «La maqueta del portal (F-035)».
> Su lógica es la de F-036, con dos añadidos de F-035 que se explican al
> final de esta sección.

- **`importar.html`** (`js/importacion.js`). Tres bloques, en el orden en que
  se usan: **1 · la plantilla** de una obra (un `.xlsx` que el backend genera
  leyendo Sigrid en el momento; el nombre sale de `Content-Disposition`),
  **2 · importar** un `.xlsx` a la bandeja (completa o parcial, el resumen, los
  errores «Fila N · columna X · problema» y, si hay filas con error, el botón
  **«Descargar el Excel de errores»**, que llega en base64 dentro de la
  respuesta) y **3 · la bandeja** de la obra, **de solo lectura**, con las
  duplicadas y los oficios ambiguos marcados. La importación **no se reintenta
  sola** (R52): si falla, se enseña el mensaje del backend y volver a importar
  lo decide quien importa (repetir no duplica nada).
- **`oficios.html`** (`js/oficios.js`). Oficios casi iguales de Sigrid: las
  propuestas («Son el mismo» / «Son distintos»), los grupos vigentes
  («Separar») y los avisos de grupos que no se aplican. Cada botón manda
  **una** decisión con `confirmado: true` y recarga; nada se decide sin pulsar.
  **«Descargar los grupos vigentes»** baja el JSON (solo códigos) que usa la
  migración del Excel actual. Solo oficios: los proveedores son F-050 y las
  actividades F-039.

Lo que **no** hay en ninguna de las dos, a propósito: editar, descartar o
aprobar una incidencia de la bandeja. Eso es **F-038**. Las dos necesitan
saber quién es el usuario (`/.auth/me`): sin sesión, importar y decidir se
quedan deshabilitados, como el cierre.

**Los dos añadidos de F-035 (apuntes de la ficha, `design.md` §16.6):**

- **El rótulo del resumen original (R74)**, en `importar.html`. Justo encima
  de los recuentos, `Importacion.rotuloResumen(respuesta)` dice de qué
  importación es el resumen: «Resumen de esta importación» normalmente, y,
  cuando el fichero ya se había importado (`ya_importado`), «Resumen de la
  importación original de este fichero» o, si la respuesta trae
  `importado_at_utc`, «Resumen de la importación original del dd/mm/aaaa»,
  con la fecha en hora de Madrid. **La fecha depende de F-053** (la ficha de
  backend que añade ese campo a `POST /api/importaciones`): hasta que esté
  desplegada, el rótulo sale sin fecha, que es lo correcto. Sin desfase en
  el texto, la fecha se lee en UTC.
- **«Decididos como distintos» (R75)**, en `oficios.html`, entre «Grupos
  vigentes» y «Avisos»: los pares de oficios que alguien decidió que son
  distintos, cada uno con un botón «Son el mismo» que manda la decisión
  `mismo` con sus dos códigos (la misma llamada que los demás botones, con
  `confirmado: true`) y recarga; manda la última decisión. **La sección
  depende de F-053**, que añade `oficio.distintos` a
  `GET /api/catalogos/propuestas`: sin ese campo,
  `Oficios.presentarPropuestas` devuelve `distintos: []` y la sección **no se
  ve**. Hasta que F-053 esté desplegada, no aparece en ningún entorno.

Los dos consumos son **tolerantes**: el front puede publicarse antes que
F-053 sin romper nada. Los dos datos son del backend, otro servicio, y por
eso son de otra ficha y no de F-035 (R76).

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
