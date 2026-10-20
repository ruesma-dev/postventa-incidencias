<!-- specs/F-038-bandeja-revision/design.md -->
# F-038 · Bandeja de revisión: editar, descartar y aprobar incidencias antes del volcado — Diseño técnico

> **Aprobado por el humano el 2026-10-06** (decisiones en §9). El backend es
> **F-056** (`specs/F-056-revision-bandeja-backend/design.md`): estados,
> reglas, tabla `revisiones_bandeja`, los tres endpoints, la paginación en el
> servidor y el correo guardado. Esta ficha es solo `services/postventa-front`.
>
> **D-4: contra Sigrid en vivo, decisión del humano 2026-10-06.** Las
> ubicaciones que ofrece el formulario son `catalogo.ubicaciones` de la
> respuesta, la misma lista de Sigrid con que F-056 valida: **Q-5 de F-056,
> resuelta** el mismo día (su design §16): las ubicaciones de la tipología de
> **cada unidad**, así que `catalogo.ubicaciones` es
> `{unidad_codigo: [ubicaciones]}` y el formulario ofrece las de la unidad
> elegida.

## 0 · Dónde está el riesgo

La puerta de verdad (qué se puede aprobar) es del backend, F-056. Lo que esta
página puede romper:

| Si falla… | Consecuencia |
|---|---|
| Una acción sale sin clic, dos veces o sin `revision_previa` | Se aprueba o se descarta algo que nadie pidió, o se pisa a otra persona |
| La página enseña «se puede aprobar» cuando no | La persona cree que algo está listo y no lo está (el backend lo frena, pero confunde) |
| La paginación repite o se salta filas | Se revisa dos veces o nunca una incidencia |
| El cierre de la sección queda a medias | Las guardias de F-035 en rojo, o el portal diciendo «en construcción» de algo que funciona |

**Rigor `critico`**, como la ficha. RED con traza pegada; cobertura de lo
cambiado (la puerta de `init.sh` dice lo que mide en el front); mutación:
`harness.mutacion` cubre los `.py` (aquí no hay `.py` de producción: su
informe lo dirá y se justifica por escrito) y, para `js/revision.js` y las
guardias del HTML, **mutaciones a mano por familias** como F-035 (bloques
17–18), con su traza.

## 1 · Dependencia de F-056

F-038 no empieza hasta que F-056 esté `done`, mergeada en `dev` y desplegada
(su T18–T19). Antes del Bloque 1, la rama de F-038 trae `dev` (merge) para
tener el contrato real; ese merge es la **base fija** de esta ficha (se anota
en `progress/impl_F-038.md`).

El contrato consumido, sin reinterpretarlo (F-056 design §8):

- `GET /api/revision?obra=&estado=&con_motivos=&tamano=&cursor=` →
  `{obra, catalogo, resumen, filtros, total_filtrado, incidencias, siguiente}`;
  cada incidencia con `importados`, `vigentes`, `cambios`, `estado`,
  `revision_id`, `revisado_at_utc`, `revisado_por` (el **correo**) y
  `motivos_no_aprobable`.
- `GET /api/revision/historial?incidencia_id=` → revisiones con `accion`,
  `revisado_at_utc`, `correo`, `campos_cambiados` y `motivo`.
- `POST /api/revision/acciones` con `usuario_oid`, `usuario_correo`,
  `confirmado: true` y `revision_previa`; responde la incidencia.
- Los códigos de error de F-056 design §4 y los de motivo de su §3.5 (con
  `sin_ubicacion`).

## 2 · La página `bandeja.html`

### 2.1 · Dónde vive (D-2)

Página real propia, `services/postventa-front/bandeja.html`, con su componente
Alpine `appRevision` en **`js/revision.js`** y tres funciones nuevas en
`js/api.js` (`revision(obra, filtros, cursor)`, `historialRevision(id)` y
`accionRevision(cuerpo)`), declarada en `Portal.PAGINAS` como
`"bandeja.html": "bandeja"`. Es el patrón de `importar.html` y `oficios.html`
(regla 6 de los placeholders). No dentro del portal: los ficheros de la
maqueta no pueden hablar con el backend (regla 2) y R63 cierra las directivas
fuera de los envoltorios.

### 2.2 · Cómo se ve

Identidad Ruesma (clases `rs-*`, sin utilidades de color de Tailwind, como
R72 de F-035), en el orden en que se usa:

1. **Cabecera**: migas «Portal de posventa › Bandeja de revisión», título y
   una frase: «Revisa lo importado antes de que llegue a Sigrid: corrige,
   elige el código del oficio, pon la ubicación, descarta o aprueba. Solo lo
   aprobado se podrá volcar.»
2. **Obra**: «Código de obra» (con `?obra=`) y «Cargar».
3. **Resumen** de toda la obra (del `resumen` de la respuesta): total, por
   estado, aprobadas, «con algo que corregir» y, desplegable, cuántas por
   motivo (así se ven los 47 ambiguos y los que tienen el oficio o el
   proveedor fuera de la obra). **Filtros** (estado, por defecto «activas»; y
   «solo las que tienen algo que corregir»): van al servidor.
4. **Lista**: una fila por incidencia (R4), con «<acción> por <correo> el
   <fecha>» si la tocó alguien. Debajo, «N de M» y **«Cargar más»** mientras
   haya `siguiente` (R7).
5. **Detalle**, en el sitio (no modal): valores vigentes con «llegó así: …»,
   motivos, historial con el **correo** de cada acción (R8), y las acciones:
   «Editar» (formulario, R9) con «Guardar cambios» y «Cancelar»; «Aprobar»
   (R11); «Descartar» con motivo y segundo clic; «Recuperar».

### 2.3 · La paginación en pantalla (Q-2)

- **Primera página**: «Cargar» o cambiar un filtro → vacía la lista y pide
  sin `cursor`.
- **Siguientes**: «Cargar más» → pide con `cursor = siguiente` y los mismos
  filtros, y **añade** las filas cuyo `incidencia_id` no esté ya (una fila que
  cambió de estado entre páginas no sale dos veces). Mientras se pide, el
  botón está deshabilitado.
- **El resumen** es siempre el de la última respuesta del servidor (de toda
  la obra); tras una acción se ajusta localmente con la diferencia entre la
  fila de antes y la de después (`ajustarResumen`), sin pedir nada.
- **Tras una acción**, la fila se sustituye en su sitio aunque ya no cumpla
  el filtro (desaparecería bajo el dedo); el filtro se vuelve a aplicar al
  pedir otra vez la primera página.
- **409 `revision_desactualizada`** → «otra persona la ha cambiado» y primera
  página otra vez. **409 `bandeja_demasiado_grande`** → mensaje con el
  recuento.

### 2.4 · `js/revision.js`

Lógica pura, con `node --test` (`tests_js/revision.test.js`):

| Función | Qué hace | R |
|---|---|---|
| `presentarRevision(respuesta)` | Filas listas para pintar; «<acción> por <correo> el <fecha>» | R4 |
| `textoMotivo(codigo)`, `etiquetaEstado(estado)` | Los textos de F-056 §3.5 (incluido `sin_ubicacion`) | R4 |
| `consultaDe(obra, filtros, cursor)` | Los parámetros de `GET /api/revision` (solo los que tocan) | R3, R6, R7 |
| `anadirPagina(cargadas, respuesta)` | Añade sin repetir por `incidencia_id`; devuelve también `siguiente` y «N de M» | R7 |
| `ajustarResumen(resumen, antes, despues)` | El resumen tras una acción | R12 |
| `opcionesDeOficio(catalogo, vigentes)`, `proveedoresDe(catalogo, oficio)`, `alCambiarOficio(formulario, catalogo)` | El formulario | R9 |
| `ubicacionesDe(catalogo, unidadCodigo)`, `alCambiarUnidad(formulario, catalogo)` | Las de `catalogo.ubicaciones[unidad]` (vacía si la unidad no está o no tiene); al cambiar la unidad, la ubicación se revalida: se conserva si está en la lista de la nueva, si no se vacía con aviso. Comparación exacta, como el backend | R9 |
| `formularioDe(vigentes)`, `valoresDelFormulario(formulario)`, `hayCambios(formulario, vigentes)` | Ida y vuelta (oficio ambiguo sin tocar → `oficio_codigo: null`, R15 de F-056) | R9, R13 |
| `cuerpoDeAccion(fila, accion, extra, identidad)` | **El único sitio** con `confirmado: true`; `usuario_oid`, `usuario_correo`, `revision_previa` | R10 |
| `puedeActuar(identidad, guardando)` | Sin `oid` o sin correo, o guardando, no | R10 |
| `queHacerConElError(error)` | §2.3 y R12 | R12 |
| `hayEdicionSinGuardar(estado)` | El `beforeunload` | R13 |
| `fechaDeMadrid(iso)` | `dd/mm/aaaa hh:mm`, hora de Madrid (la de `js/importacion.js` si está exportada; si no, la suya, sin tocar ese módulo) | R4, R8 |

La identidad es la de `identidadDe` de `js/api.js`, que ya devuelve
`{usuarioOid, correo}` (claim de correo o `userDetails`): no se escribe otra.

El componente `crearAppRevision({api})` solo guarda estado y delega en lo
puro. **Nada sale sin un clic**: cargar solo lee; las acciones solo desde
`@click`; con `guardando`, ningún botón de acción. El `beforeunload` vive en
`bandeja.html`, lee `hayEdicionSinGuardar(Alpine.$data(…))` y, si no puede,
no pregunta; **no** reutiliza `js/guarda_salida.js` (cerrado, R81 de F-035).
Ni el correo ni el `oid` se escriben en `console` ni en el almacenamiento del
navegador (R15).

### 2.5 · `importar.html` (R14)

Una frase y un enlace en el bloque de la bandeja: «Para corregir, elegir el
oficio, poner la ubicación o aprobar: [Revisar esta obra en la bandeja de
revisión]» (`bandeja.html?obra=<obra>`, misma pestaña). Sin tocar
`js/importacion.js`: el `href` se liga con el estado que el componente ya
expone.

## 3 · El portal: mientras se construye y al cerrar

### 3.1 · Mientras F-038 no esté `done` (R16)

`bandeja` sigue en `construccion`, con su envoltorio y los placeholders de
F-038; la pestaña lleva `data-construccion` en las **cinco** barras (R2). Lo
exigen las guardias de la raíz: R29 pide un resto de F-038 mientras no esté
`done`, y R62 pide `construccion` mientras ninguna ficha de la sección lo
esté. Lo que entra antes es la página nueva en las guardias: las listas de los
tests de F-035 y F-036 que enumeran cuatro páginas (`PAGINAS_DEL_FRONT`,
`PAGINAS_CON_BARRA`, `PAGINAS_REALES_CON_BARRA`, `PAGINAS_REALES_CON_VERSION`,
el `PAGINAS` esperado, el conjunto de `test_f035_portal.py`, las copias de la
tira…) pasan a cinco; y el control de R62 de
`tests/test_f035_placeholders_vivos.py` deja F-038 y usa **F-044**
(`impresion` pasa a `real` con ella), para seguir demostrando que mira (R18).

### 3.2 · El commit de cierre (R17, D-11)

Con F-038 sin `done`, R29 exige un resto y R62 `construccion`; con F-038
`done`, R28 exige cero restos y R62 `parcial`: no hay commit intermedio en
verde. Por eso va **un solo commit** que **también** pone F-038 en `done`:

1. `Portal.SECCIONES`: `bandeja` → `parcial`.
2. Cinco barras: la pestaña `bandeja` sin `data-construccion` ni su
   `aria-label`; cinco tiras: pasos 02 y 03 igual (R87).
3. `index.html#/bandeja`: fuera el envoltorio de sección; una tarjeta
   «Revisar la bandeja» con chip «En producción», enlace a `bandeja.html` y
   una frase; y en envoltorios de bloque con su rótulo (R64, R65): el
   industrial propuesto (`"F-039"`, con «Cambiar industrial» y el ejemplo de
   `MaquetaDatos.propuestas`), la aprobación en bloque (`"F-043"`) y el volcado
   (`"F-040"`, con su panel y `MaquetaDatos.volcado`). La frase de R69 sale con
   el envoltorio.
4. La tarjeta de la bandeja en la portada: chip «En producción» y enlace a
   `bandeja.html` (R67).
5. Fuera de la maqueta: los tres placeholders de F-038, sus entradas de
   `PLACEHOLDERS`, el bloque `bandeja` de `MaquetaDatos` (`ficha: "F-038"`), su
   título de `TITULOS_FICHAS` y lo que solo servía a ese bloque
   (`filtrarBandeja`, filtros y selección de la bandeja en `portal_app.js`, el
   contador de aprobadas leído de esas filas). Si «Aprobar las seleccionadas»
   (`enBloque`) se queda sin selección que contar, pasa a `enBloque: false` y
   su test de R12 se ajusta.
6. `harness/features.json`: F-038 → `done`.

Lo prepara el implementer **por encargo del líder**, tras la verificación en
producción (Bloque 3) y el APROBADO de todos los bloques; review corta solo de
ese commit; `bash harness/init.sh` **sobre él**; si falla, se revierte entero.
Tras él, F-039, F-040 y F-043 conservan restos (R18).

## 4 · Ficheros

**A crear** (`services/postventa-front/`): `bandeja.html`, `js/revision.js`,
`tests_js/revision.test.js`, `tests/test_f038_front.py` (la página como texto:
R1, R2, R10 —un solo `confirmado: true`, acciones solo en `@click`—, R14,
R15).

**A modificar**:

| Fichero | Qué |
|---|---|
| `js/api.js` | Tres funciones (§2.1) |
| `js/portal.js` | `PAGINAS` (Bloque 1); en el cierre, `SECCIONES`, `PLACEHOLDERS`, `TITULOS_FICHAS`, `filtrarBandeja` |
| `importar.html` | El enlace de R14 (Bloque 1); la pestaña en el cierre |
| `index.html`, `partes.html`, `oficios.html` | Solo en el cierre |
| `js/maqueta_datos.js`, `js/portal_app.js` | Solo en el cierre |
| `css/styles.css` | Solo si el formulario necesita una clase `rs-*` que no exista; nunca `css/portal.css` |
| `README.md` | R19 |
| Tests de F-035 y F-036 del front | Listas a cinco páginas (Bloque 1); los que fijan la sección en construcción, en el cierre. **Cada uno, en el informe con el porqué** |
| `tests/test_f035_placeholders_vivos.py` (raíz) | Control de R62: F-038 → F-044 (Bloque 1) |
| `harness/features.json` | Solo en el commit de cierre |

**No se toca**: `services/postventa-api/` (es F-056); `js/importacion.js`,
`js/oficios.js`, `js/guarda_salida.js`, `js/app.js`, `js/pipeline.js` y el
resto del circuito; `oficios.html` fuera del cierre; `dev_server.py`;
`staticwebapp.config.json` (`/*` ya exige sesión); `infra/*`.

## 5 · Tests

| R | Dónde | Lo que fija además de lo obvio |
|---|---|---|
| R1, R2 | pytest (front) | Las guardias de F-035 aplicadas a la quinta página; la marca de construcción en su `span` |
| R3, R6, R7 | node | `consultaDe` solo con lo que toca; filtros → primera página; `anadirPagina` no repite y para con `siguiente: null`; «N de M» |
| R4, R5, R8 | node | Textos de cada motivo y estado; el correo en la línea de la fila y en el historial; el resumen sale de la respuesta |
| R9 | node | Grupo primero si ambiguo; proveedores solo del oficio; cambiar oficio vacía el que no casa; ubicaciones solo de la unidad elegida; cambiar la unidad conserva una ubicación que también está en la nueva y vacía (con aviso) la que no; unidad sin lista → ninguna; una que difiere solo en mayúsculas **no** se conserva |
| R10, R11 | node, pytest | Un solo sitio con `confirmado: true`; sin `oid` o sin correo, nada habilitado; «Aprobar» con motivos o `null`, deshabilitado |
| R12 | node | Cada error a su salida; `ajustarResumen` en las cuatro acciones |
| R13 | node | `hayEdicionSinGuardar` con y sin cambios, y con estado ilegible |
| R14, R15 | pytest | El enlace sin `target`; ninguna ruta fuera de las tres y `/.auth/me`; ningún `console.*` ni `localStorage`/`sessionStorage` con el correo o el `oid` |
| R16–R18 | raíz | Las guardias de siempre; el control con F-044 |

## 6 · Riesgos y alternativas descartadas

1. **La pantalla dentro del portal** (`#/bandeja`): descartado (D-2, §2.1).
2. **Filtrar en el cliente sobre lo cargado**: con paginación, filtrar solo lo
   cargado engaña; los filtros van al servidor (F-056 R26).
3. **Paginación por número de página**: inestable si cambian filas entre
   peticiones; el `cursor` de F-056 es por clave.
4. **Riesgo: el cierre atómico** con muchas piezas: solo front y maqueta,
   review propia, revertir entero si falla.
5. **Riesgo: muchos tests de F-035 cambian a propósito**: el informe los lista
   todos con el porqué.
6. **Riesgo: el correo a la vista** de todos los del grupo: es lo decidido
   (D-8); no sale de la página (ni consola ni almacenamiento).

## 7 · Lo que se publica

El front se publica **dos veces**: tras el Bloque 1 (la página, con la sección
aún «en construcción») y tras el cierre (la sección «En producción»). Siempre
desde un worktree limpio de `dev` (`tasks.md`, Bloques 2 y 4).

## 8 · Lo que queda para otras fichas

Industrial propuesto (F-039), volcado (F-040), aprobar en bloque (F-043): sus
restos siguen en la sección `#/bandeja` del portal, en envoltorios de bloque.

## 9 · Decisiones (aprobadas por el humano el 2026-10-06)

| Id | Decisión |
|---|---|
| D-1 | Partir: el backend es F-056, que va antes; F-038 es la página y el cierre, bloqueada por F-056 |
| D-2 | Página propia `bandeja.html` en `Portal.PAGINAS` |
| D-4 | Ubicación obligatoria para aprobar (`sin_ubicacion`, en F-056), **contra Sigrid en vivo** (decisión del humano 2026-10-06); el formulario ofrece solo `catalogo.ubicaciones[unidad elegida]`, la lista con que valida el backend; cambiar la unidad la revalida. Fuente: Q-5 de F-056, resuelta (tipología de la unidad) |
| D-8 | Se enseña el **correo** de quien hizo cada cosa, en la lista y en el historial |
| D-11 | Cierre atómico: un commit con la sección en `parcial`, la maqueta sin restos de F-038 y F-038 `done` |
| D-12 | Guarda de salida solo con una edición sin guardar |
| D-13 | `oid` y correo de `/.auth/me`, en el cuerpo |
| Q-2 | Se pagina: «Cargar más» con el `cursor` del servidor |
| Q-3 | Cualquiera de `posventa-usuarios` |
| Q-4 | Merge normal a `dev` |

D-3, D-5, D-6, D-7, D-9, D-10 y D-14 son de F-056 (su design §15).
