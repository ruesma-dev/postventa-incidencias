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
>
> **Conciliado con `dev` el 2026-10-20, base fija `87a03f3`** (F-056, F-060 y
> F-059 cerradas y desplegadas). Las decisiones aprobadas de §9 **no
> cambian**. Lo conciliado está en su sitio con la marca *«Conciliado
> 2026-10-20»* y resumido en **§10**; las decisiones nuevas (Q-6 a Q-10) están
> en §9 y §10.4, **aprobadas por el humano el 2026-10-20** (Q-6 en su opción
> (b) ampliada: la presentación del volcado es de esta ficha). La
> conciliación no encuentra nada que obligue a tocar `services/postventa-api`.

## 0 · Dónde está el riesgo

La puerta de verdad (qué se puede aprobar) es del backend, F-056. Lo que esta
página puede romper:

| Si falla… | Consecuencia |
|---|---|
| Una acción sale sin clic, dos veces o sin `revision_previa` | Se aprueba o se descarta algo que nadie pidió, o se pisa a otra persona |
| La página enseña «se puede aprobar» cuando no | La persona cree que algo está listo y no lo está (el backend lo frena, pero confunde) |
| La paginación repite o se salta filas | Se revisa dos veces o nunca una incidencia |
| El cierre de la sección queda a medias | Las guardias de F-035 en rojo, o el portal diciendo «en construcción» de algo que funciona |
| *(Conciliado 2026-10-20)* La página ofrece acciones sobre una `volcada` o una `en_duda` | El backend responde 409 `accion_no_permitida` (F-059 R2), pero la persona cree que puede cambiar algo que ya está, o puede estar, en Sigrid |
| *(Conciliado 2026-10-20)* Una acción sin respuesta se da por fallida | La persona la repite creyendo que no se guardó; la `revision_previa` lo frena (409), pero hay que decir «no se sabe» y recargar |

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

> *Conciliado 2026-10-20.* **Cumplida.** F-056 está `done` y desplegada desde
> el 2026-10-09, y detrás F-060 y F-059. La rama `feature/F-038-bandeja-revision`
> **nace de `dev` `87a03f3`** (2026-10-20): ya no hay merge previo, y la
> **base fija** de las guardias y de la mutación es **`87a03f3`**.

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

> *Conciliado 2026-10-20 · el contrato tal como está implementado*
> (`interface_adapters/api/revision.py`, `function_app.py` —`revision`,
> `revision_historial`, `revision_acciones`, `CODIGOS_DE_REVISION`,
> `_error_de_revision`, `_rechazo_de_obra`—, `domain/models/revision.py` y
> F-059 design §11–§12):
>
> - **`catalogo`**: `unidades [{codigo, nombre}]`; `ubicaciones
>   {unidad_codigo: [texto]}` (una entrada por unidad, vacía si no tiene);
>   `oficios [{codigo, nombre, grupo: {etiqueta, codigos}}]` (solo los de
>   `obrofc`; `grupo.codigos`, los del grupo que están en la obra);
>   **`pares [{oficio_codigo, proveedor_codigo, proveedor_nombre}]`** (cada
>   par una vez, con su primer nombre: «lo que se ofrece es lo que se
>   guarda»); `urgencias` y `listados [{codigo, etiqueta}]`.
> - **`resumen`**: `total`, `por_estado` con **seis** claves (`nueva`,
>   `editada`, `aprobada`, `descartada`, `volcada`, `en_duda`), `con_motivos`
>   y `por_motivo` con los **nueve** motivos. De toda la obra, sin filtros.
> - **`filtros`**: `{estado, con_motivos}` tal como los entendió el servidor.
> - **Cada incidencia**: `incidencia_id`, `origen`, `importacion_id`,
>   `fila_origen`, `creada_at_utc`, `duplicada_de` (el `incidencia_id` de la
>   original, o `null`), `importados` y `vigentes` (trece claves:
>   `unidad_codigo`, `unidad_nombre`, `ubicacion`, `descripcion`, `detalle`,
>   `oficio_codigo`, `oficio_nombre`, **`oficio_ambiguo`**,
>   `proveedor_codigo`, `proveedor_nombre`, **`proveedor_ambiguo`**,
>   `urgencia`, `listado`), `cambios` (los campos lógicos: `unidad`,
>   `ubicacion`, `descripcion`, `detalle`, `oficio`, `proveedor`, `urgencia`,
>   `listado`), `estado` (uno de los seis), `revision_id`, `revisado_at_utc`,
>   `revisado_por` (correo, o el literal del sistema de F-060),
>   `motivos_no_aprobable` (lista, o `null` tras descartar o recuperar) y
>   **`volcado`** (F-059 R4: `null` o `{estado, sigrid_cod, volcado_at_utc,
>   volcado_por, motivo}`, con `estado` `volcada`, `en_duda`, `rechazado` o
>   `no_procesado`). La respuesta 200 de una acción tiene **la misma forma**
>   (F-2 (a) de F-059).
> - **Filtro `estado`**: ausente o `activas` (todo menos `descartada` y
>   `volcada`), `todas`, o uno de los seis. **`tamano`**: 1–200 (100 por
>   defecto). **`cursor`**: base64url sin relleno, opaco; uno que no sea
>   «emitido por el sistema» es 400.
> - **Historial**: `{incidencia_id, importada: {origen, importacion_id,
>   creada_at_utc}, revisiones: [{revision_id, accion, revisado_at_utc,
>   correo, campos_cambiados, motivo}]}`, de la más antigua a la más reciente.
> - **Cuerpo de una acción**: exactamente las seis claves comunes
>   (`incidencia_id`, `accion`, `usuario_oid`, `usuario_correo`,
>   `confirmado`, `revision_previa`), más `valores` en `editar` (exactamente
>   `unidad_codigo`, `ubicacion`, `descripcion`, `detalle`, `oficio_codigo`,
>   `proveedor_codigo`, `urgencia`, `listado`) y `motivo` opcional en
>   `descartar`.
> - **Errores**: la tabla de R12 (requirements), con su HTTP, su `codigo` y
>   lo propio de cada uno. Los 503 y el 500 de configuración **no** llevan
>   `codigo`; los de obra (`obra_sin_unidades` 404, `obra_ambigua` y
>   `catalogo_sin_verificar` 409) llevan el suyo.
> - Los instantes, en UTC con microsegundos y `+00:00`.

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

> *Conciliado 2026-10-20 (R26; `js/api.js` de hoy).* Las tres funciones van
> con `mensajeDelServicio: true` —sin él, un 503 enseñaría
> `TEXTO_ENTORNO_NO_ARCHIVA`, el texto de la puerta de archivar—; las dos
> lecturas reintentan lo transitorio como `bandeja` de F-036, y
> `accionRevision` va con `sinReintentos: true`, como `decidirCatalogos`.
> Además, **`clasificar`** gana, **aditivo**, el cuerpo del error en el
> `ErrorApi` (p. ej. `error.detalle`, el JSON del error tal cual llegó; `null`
> si no era JSON): hoy solo conserva `error` y `codigo`, y R12 necesita
> `errores`, `motivos`, `estado`, `acciones` y `total`. Ningún error de F-056
> lleva el correo ni el `oid` (F-056 R11), y la traza (`registrar`) sigue sin
> el cuerpo. `api.test.js` cuenta los endpoints (`endpoints.length` 17 → 20)
> y su lista `LOS_ENDPOINTS`: se amplían.

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
   *Conciliado 2026-10-20:* «por estado» son los seis (R5, R21) y «por
   motivo» los nueve (R4 (a)); el selector de estado, el de R6.
4. **Lista**: una fila por incidencia (R4), con «<acción> por <correo> el
   <fecha>» si la tocó alguien. Debajo, «N de M» y **«Cargar más»** mientras
   haya `siguiente` (R7).
   *Conciliado 2026-10-20 (Q-6, aprobada):* en una `volcada`, la línea
   «Volcada como <sigrid_cod> por <quien> el <fecha>»; en una `en_duda`, la
   suya con el motivo si lo hay; y en el detalle de una aprobada con un
   intento fallido, «Último intento de volcado: …» (R21).
5. **Detalle**, en el sitio (no modal): valores vigentes con «llegó así: …»,
   motivos, historial con el **correo** de cada acción (R8), y las acciones:
   «Editar» (formulario, R9) con «Guardar cambios» y «Cancelar»; «Aprobar»
   (R11); «Descartar» con motivo y segundo clic; «Recuperar».
   *Conciliado 2026-10-20:* solo las acciones de su estado (R11); en una
   `volcada` o `en_duda`, ninguna (R21).
6. *(Conciliado 2026-10-20.)* **Pie** «Construcciones Ruesma · Posventa ·
   bandeja de revisión.» con la estructura común; sin subnavegación (R1).

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
  *Conciliado 2026-10-20 (`resumen` de `domain/models/revision.py`):* el
  resumen cuenta los motivos de **todas** las filas, también las
  descartadas. Con `motivos_no_aprobable: null` (descartar, recuperar: los
  valores no cambian) `ajustarResumen` mueve solo `por_estado` y deja los
  motivos como estaban. Lo que no puede ajustar —el `duplicada` de **otra**
  fila cuando se descarta o se recupera su original— se corrige al pedir otra
  vez la primera página; es una deriva conocida y se dice en el README.
- **Tras una acción**, la fila se sustituye en su sitio aunque ya no cumpla
  el filtro (desaparecería bajo el dedo); el filtro se vuelve a aplicar al
  pedir otra vez la primera página.
- **409 `revision_desactualizada`** → «otra persona la ha cambiado» y primera
  página otra vez. **409 `bandeja_demasiado_grande`** → mensaje con el
  recuento.
  *Conciliado 2026-10-20:* también vuelven a la primera página 409
  `accion_no_permitida`, 404 `incidencia_no_encontrada` y una acción sin
  respuesta (tabla de R12).

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

> *Conciliado 2026-10-20 · lo que cambia en la tabla:*
>
> | Función | Qué cambia o se añade | R |
> |---|---|---|
> | `textoMotivo(codigo)` | Los **nueve** motivos de `MotivoNoAprobable`, en su orden; un código desconocido, tal cual | R4 (a) |
> | `etiquetaEstado(estado)` | Los **seis** estados (con `volcada` y `en_duda`, R21); uno desconocido, tal cual | R4 (c), R21 |
> | `accionesDe(estado)` (nueva) | Las acciones que ofrece cada estado: la tabla de `_PERMITIDAS` (F-056 §3.3, F-059 §4.2); vacía para `volcada`, `en_duda` y un estado desconocido | R11, R21 |
> | `quienLegible(texto)` (nueva) | El correo tal cual; `sistema:normalizar_ubicacion` y cualquier `sistema:…`, el texto de R22; `null`, nada | R4 (d), R8, R22 |
> | `duplicadaDe(fila, cargadas)` (nueva) | «duplicada de la fila N» con el `fila_origen` de la original si está cargada; si no, «duplicada de otra fila del mismo fichero» | R4 (b) |
> | `presentarRevision(respuesta)` | Usa `quienLegible`, `duplicadaDe`, `accionesDe` y `lineaDeVolcado` | R4, R21 |
> | `lineaDeVolcado(volcado, estado)` (nueva) | La línea de R21.1 (`volcada`: «Volcada como <sigrid_cod> por <quien> el <fecha>»), R21.2 (`en_duda`, con el motivo si lo hay) o R21.3 (último intento `rechazado` / `no_procesado` de una que no está volcada ni en duda); `null` sin `volcado`. Fecha con `fechaDeMadrid`, quien con `quienLegible` | R21.1–R21.3 |
> | `textoMotivoVolcado(codigo)` (nueva) | Castellano para los quince códigos de parte de `sigrid_api.md` §8.9; uno desconocido, tal cual | R21.4 |
> | `consultaDe(obra, filtros, cursor)` | `estado` puede ser también `volcada` o `en_duda` | R6, R21.5 |
> | `opcionesDeOficio(catalogo, vigentes)` | «El grupo de la fila»: las entradas de `catalogo.oficios` cuyo `grupo.etiqueta` es el `oficio_nombre` vigente, primero | R9 (b) |
> | `proveedoresDe(catalogo, oficio, vigentes)` | De **`catalogo.pares`** (los de ese `oficio_codigo`); con el oficio ambiguo sin elegir, solo el vigente o ninguno (F-056 R15) | R9 (a), (c) |
> | `formularioDe(vigentes, catalogo)` | Un valor vigente fuera del catálogo de hoy se conserva como opción marcada (Q-9) | R24 |
> | `valoresDelFormulario(formulario)` | Ubicación y detalle vacíos → `null` (nunca `""`) | R9 (d) |
> | `hayCambios(formulario, vigentes)` | Con la normalización del backend (descripción con blancos colapsados; detalle, ubicación y motivo recortados) | R9 (e) |
> | `queHacerConElError(error)` | La tabla completa de R12, leyendo `error.codigo`, `error.http` y `error.detalle` (R26); una acción sin respuesta (`http: null`) → «no se sabe si se ha guardado» y primera página | R12 |
> | `fechaDeMadrid(iso)` | `js/importacion.js` **no** exporta su fecha (y la suya es solo día): `js/revision.js` lleva la suya, con hora, sin tocar ese módulo | R4, R8 |
>
> *Precisado 2026-10-20 (review del Bloque 1) · las funciones puras que
> creó T2 y que piden los R* (nombres de `js/revision.js` en `77122eb`); con
> las de arriba, es la **lista completa** que recorre la mutación de T5:
>
> | Función | Qué hace | R |
> |---|---|---|
> | `lineaDeRevision(fila)` | «<acción> por <quien> el <fecha>», con la acción deducida del estado (R4, D-a); nada sin revisiones | R4, R22 |
> | `puedeAprobar(fila)` | «Aprobar» solo con `motivos_no_aprobable` `[]` y en un estado que lo admite (`accionesDe`) | R11, R12 |
> | `presentarResumen(resumen)` | El resumen de toda la obra: seis estados y nueve motivos, con su texto | R5 |
> | `detalleDe(incidencia, catalogo)` | Los vigentes y, en cada campo de `cambios`, «llegó así: …» | R8 |
> | `presentarHistorial(respuesta)` | El historial, con fecha de Madrid y quién legible | R8, R22 |
> | `opcionesDeUnidad(catalogo, vigentes)` | Las unidades de la obra y, si la vigente ya no lo es, ella marcada | R9, R24 |
> | `opcionesDeUbicacion(catalogo, unidadCodigo, vigentes)` | Las ubicaciones de la unidad elegida y, si la vigente no está, ella marcada | R9, R24 |
> | `contador(texto, maximo)` | «N / máximo» de la descripción (128) y el detalle (2000) | R9 |
> | `obraDeLaUrl(busqueda)` | La obra de `?obra=`, recortada, o vacío | R3 |
> | `formularioDe(vigentes, catalogo)` | (firma definitiva) los valores del formulario, los vigentes para `hayCambios` y qué vigente no está en el catálogo de hoy; nada se vacía al abrir | R9, R24 |
> | `queHacerConElError(error, enAccion)` | (firma definitiva) la tabla de R12; `enAccion` distingue la acción sin respuesta («no se sabe si se ha guardado» y recarga) de una lectura (solo su error) | R12 |

La identidad es la de `identidadDe` de `js/api.js`, que ya devuelve
`{usuarioOid, correo}` (claim de correo o `userDetails`): no se escribe otra.

El componente `crearAppRevision({api})` solo guarda estado y delega en lo
puro. **Nada sale sin un clic**: cargar solo lee; las acciones solo desde
`@click`; con `guardando`, ningún botón de acción. El `beforeunload` vive en
`bandeja.html`, lee `hayEdicionSinGuardar(Alpine.$data(…))` y, si no puede,
no pregunta; **no** reutiliza `js/guarda_salida.js` (cerrado, R81 de F-035).
Ni el correo ni el `oid` se escriben en `console` ni en el almacenamiento del
navegador (R15).

> *Conciliado 2026-10-20 (para F-057 y F-040, que vienen detrás):* F-057 (su
> R23–R25) cargará páginas con `consultaDe`/`anadirPagina` hasta encontrar
> una incidencia y abrirá su detalle y su formulario; F-040 pondrá su panel
> de volcado en `bandeja.html` (la presentación del volcado en la lista, su
> antiguo R54, ya es de aquí: R21). Que
> abrir el detalle y el formulario de una fila sean funciones del componente
> a las que se pueda llamar con un `incidencia_id` facilita las dos, sin
> añadir nada que F-038 no use.

### 2.5 · `importar.html` (R14)

Una frase y un enlace en el bloque de la bandeja: «Para corregir, elegir el
oficio, poner la ubicación o aprobar: [Revisar esta obra en la bandeja de
revisión]» (`bandeja.html?obra=<obra>`, misma pestaña). Sin tocar
`js/importacion.js`: el `href` se liga con el estado que el componente ya
expone.

> *Conciliado 2026-10-20:* fuera de la `<table>` y como `<a>` (R14). F-057
> rehará esa tabla después y conserva el enlace (su R27).

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

> *Conciliado 2026-10-20 · inventario sobre `87a03f3`* (el implementer lo
> confirma con `grep` y lo lista entero en su informe, con el porqué):
>
> - **Listas de páginas** que pasan a incluir `bandeja.html`:
>   `PAGINAS_DEL_FRONT` y `PAGINAS_ESPERADAS` (`tests/test_f035_paginas.py`),
>   `PAGINAS_REALES_CON_VERSION` (ídem), el conjunto de `_paginas_del_front`
>   (`tests/test_f035_portal.py`), `PAGINAS_CON_BARRA` y
>   `PAGINAS_REALES_CON_BARRA` (`tests_js/f035_paginas.test.js`),
>   `PAGINAS_CON_RECORRIDO` y `PAGINAS_CON_RECORRIDO_ESTATICO`
>   (`tests_js/portal.test.js`) y el test de R44 de `enlaceSeccion` desde las
>   páginas reales («f035 R44: enlaceSeccion desde importar.html y
>   oficios.html…», `tests_js/f035_paginas.test.js`).
> - **Listas que son de `entrada` y no se amplían**: `PAGINAS_REMODELADAS`,
>   `MIGAS_DE_ENTRADA`, `SUBNAV_DE_ENTRADA`, `PIE_PAGINAS_REALES` (texto de
>   `entrada`). `bandeja.html` lleva sus propias constantes en
>   `tests/test_f038_front.py` (sus migas y su pie) y pasa por las mismas
>   funciones de guardia (`problemas_r70`, `_r72`, `problemas_r77`…).
> - **Controles que miran la sección `bandeja`** y que el cierre rompería; se
>   mudan **en el Bloque 1 bis** (T1 bis) a `impresion` (F-044), que sigue en
>   `construccion`: `test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done`
>   (raíz; ya lo decía la spec), `test_f035_r62_control_el_lector_de_estados_lee_el_texto`
>   (raíz; nuevo) y «f035 R66: control: quitar data-construccion de una
>   pestaña de partes.html salta» (`tests_js/f035_paginas.test.js`; nuevo).
> - **La guardia de la tira** (`problemasDelRecorrido`, R85): para el paso de
>   la propia sección que **no** es el actual (el 03 en `bandeja.html`) pide
>   hoy `<span aria-current="step">`, y R86 prohíbe ese `aria-current`: con
>   ninguna página se pueden cumplir las dos. Se ajusta según Q-10 (R25).
> - **`api.test.js`**: `LOS_ENDPOINTS` y la cuenta de 17 (§2.1).
> - **`test_f036_front.py`**: no cambia. Sus guardias (`botones_prohibidos`,
>   la tabla de la bandeja sin controles, `DATOS_REALES`, el README que nombra
>   «F-038») siguen valiendo con el enlace de R14.

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

> *Conciliado 2026-10-20 (recontado sobre `87a03f3`):*
>
> - Los restos de F-038 son **siete** (tres placeholders en `index.html`, tres
>   entradas de `PLACEHOLDERS`, el bloque `bandeja` de `MaquetaDatos`), más su
>   título de `TITULOS_FICHAS`.
> - En el punto 5, **dos** placeholders `enBloque: true` cuentan la selección
>   de la bandeja (`seleccionadasPara` por el prefijo `bandeja.`):
>   `bandeja.aprobarSeleccionadas` (F-043) y **`bandeja.reintentarVolcado`**
>   (F-040). Los dos pasan a `enBloque: false` si se quedan sin selección.
> - **`MaquetaDatos.propuestas.porFila`** (F-039) está indexado por los `id`
>   de las filas de ejemplo de la bandeja (`BJ-…`). Si el ejemplo del
>   industrial propuesto necesita filas, las que use se mudan a su bloque
>   (`ficha: "F-039"`); ninguna fila se queda en un bloque sin ficha ni con
>   la de F-038.
> - Los controles de la sección `bandeja` ya se mudaron en T1 bis (§3.1):
>   el cierre no los toca.
> - Otros tests que fijan la sección en construcción y que el cierre ajusta,
>   como candidatos a confirmar con `grep`: en `tests_js/portal.test.js`, los
>   de `SECCIONES` y `PLACEHOLDERS` de F-038 y los de `filtrarBandeja`; en
>   `tests/test_f035_paginas.py` y `tests/test_f035_portal.py`, los que
>   cuentan los enlaces del portal a páginas reales y los de R64, R67 y R69;
>   en `tests_js/maqueta_datos.test.js`, el bloque `bandeja`. **Cada uno**,
>   en el informe con el porqué.

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
| `js/api.js` | Tres funciones (§2.1) *y, conciliado 2026-10-20, el cuerpo del error en `clasificar`, aditivo (R26)* |
| `js/portal.js` | `PAGINAS` (Bloque 1); en el cierre, `SECCIONES`, `PLACEHOLDERS`, `TITULOS_FICHAS`, `filtrarBandeja` |
| `importar.html` | El enlace de R14 (Bloque 1); la pestaña en el cierre |
| `index.html`, `partes.html`, `oficios.html` | Solo en el cierre |
| `js/maqueta_datos.js`, `js/portal_app.js` | Solo en el cierre |
| `css/styles.css` | Solo si el formulario necesita una clase `rs-*` que no exista; nunca `css/portal.css` |
| `README.md` | R19 |
| Tests de F-035 y F-036 del front | Listas a cinco páginas (Bloque 1); los que fijan la sección en construcción, en el cierre. **Cada uno, en el informe con el porqué** |
| `tests/test_f035_placeholders_vivos.py` (raíz) | Control de R62: F-038 → F-044 (Bloque 1) |
| `harness/features.json` | Solo en el commit de cierre |
| *(Conciliado 2026-10-20)* `tests_js/api.test.js` | `LOS_ENDPOINTS` y la cuenta (17 → 20); los casos del cuerpo del error (R26) |
| *(Conciliado 2026-10-20)* `tests_js/portal.test.js` | `PAGINAS_CON_RECORRIDO*`; la guardia de la tira para el paso 03 (R25, Q-10) |
| *(Conciliado 2026-10-20)* `tests_js/f035_paginas.test.js` | Las listas de barras; el control de R66 de `bandeja` → `impresion` (Bloque 1) |
| *(Conciliado 2026-10-20)* `tests/test_f035_placeholders_vivos.py` (raíz) | Además, el control del lector de R62: `bandeja` → `impresion` (Bloque 1) |
| *(Conciliado 2026-10-20)* `docs/ARCHITECTURE.md` | R20: la página, su sección, sus rutas y `PAGINAS` con `bandeja.html` |
| *(Conciliado 2026-10-20)* `azure-apps/postventa_incidencias.md` (otro repositorio) | R20: la página nueva; **el líder**, en su repositorio, en T6 y en T10 |

**No se toca**: `services/postventa-api/` (es F-056); `js/importacion.js`,
`js/oficios.js`, `js/guarda_salida.js`, `js/app.js`, `js/pipeline.js` y el
resto del circuito; `oficios.html` fuera del cierre; `dev_server.py`;
`staticwebapp.config.json` (`/*` ya exige sesión); `infra/*`.
*Conciliado 2026-10-20:* tampoco `docs/INTEGRACION.md` (F-038 no añade
rutas) ni nada de F-059 o F-060.

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

> *Conciliado 2026-10-20 · lo que se añade:*
>
> | R | Dónde | Lo que fija |
> |---|---|---|
> | R4 (a)–(e) | node | Los nueve motivos en su orden y un código desconocido tal cual; «fila N» con la original cargada y el texto genérico sin ella; `volcado` ignorado |
> | R5, R6 | node | Seis estados en el resumen; `consultaDe` con `activas` por defecto y sin `tamano`; el cursor tal cual |
> | R9 (a)–(e) | node | Proveedores de `catalogo.pares`, con `proveedor_nombre` `null` → código; grupo por `grupo.etiqueta`; ambiguo sin elegir → solo el vigente o ninguno; ubicación y detalle vacíos → `null`; `hayCambios` falso con solo blancos de diferencia |
> | R10 | node, pytest | El cuerpo con exactamente las claves de cada acción (seis, más `valores` u opcional `motivo`); la acción sin reintentos (`api.test.js`) |
> | R11, R21.6 | node, pytest | `accionesDe` estado a estado (seis, y uno desconocido → ninguna); el HTML no pinta botones sin `accionesDe` |
> | R21.1–R21.5, R21.7 | node, pytest | `lineaDeVolcado` en los cuatro estados del objeto y con `null`; la fecha en hora de Madrid; `volcado_por` del sistema o correo; los quince textos de §8.9 y uno desconocido tal cual; los filtros `volcada` y `en_duda` en `consultaDe` y en el selector del HTML; `volcado_por` fuera de `console` y del almacenamiento |
> | R12, R26 | node | Cada fila de la tabla de R12 a su salida; sin respuesta → «no se sabe» y primera página; el `detalle` del error en `api.js`; un 503 con el texto del servicio |
> | R18 | raíz, node | Los tres controles mudados a `impresion` siguen cazando (una copia estropeada en memoria) |
> | R20 | pytest (raíz o front) | `docs/ARCHITECTURE.md` nombra `bandeja.html` y su sección |
> | R22 | node | `quienLegible` con correo, con el literal del sistema, con otro `sistema:…` y con `null` |
> | R23 | pytest | Ningún fichero de la página nombra `/revision/normalizar` |
> | R24 | node | Un vigente fuera del catálogo se conserva como opción marcada; cambiar la unidad sigue vaciando |
> | R25 | node | La tira de `bandeja.html`: 02 actual con su marca, 03 `<span>` sin `aria-current`; la guardia ajustada caza un 03 con `aria-current` |
>
> Datos de los tests, ficticios: obras `99NN`, textos «Ejemplo», correos
> `@ejemplo.invalid`, UUID inventados (el barrido de `test_f007_sin_datos_reales.py`
> y `DATOS_REALES` de F-036 siguen valiendo).

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
7. *(Conciliado 2026-10-20.)* **Riesgo: la primera carga tras un rato parado**
   puede tardar o dar 502/503: `GET /api/revision` lee Sigrid, y la primera
   lectura a `sigrid-api` tras un rato parada puede pasar de 35 s (aprendido
   en F-059). La lectura reintenta lo transitorio y T7 lo mide en caliente
   (objetivo de F-060 V3: máximo < 10 s).
8. *(Conciliado 2026-10-20.)* **Riesgo: el resumen ajustado en local deriva**
   en el motivo `duplicada` de otra fila (§2.3); se corrige al recargar.
9. *(Conciliado 2026-10-20.)* **Riesgo: tres fichas tocan `bandeja.html`**
   (F-038, F-040, F-057) y dos `importar.html` (F-038, F-057): cada una
   va detrás de la anterior, con su conciliación; F-038 no adelanta nada de
   las otras salvo la presentación del volcado, que el humano trajo aquí
   (Q-6, 2026-10-20): F-040 se queda con el panel y, en su conciliación,
   suelta su R54.

## 7 · Lo que se publica

El front se publica **dos veces**: tras el Bloque 1 —desde el 2026-10-20, los
bloques 1, 1 bis, 1 ter y 1 quater de `tasks.md`— (la página, con la sección
aún «en construcción») y tras el cierre (la sección «En producción»). Siempre
desde un worktree limpio de `dev` (`tasks.md`, Bloques 2 y 4).

> *Conciliado 2026-10-20 (`infra/desplegar_front.ps1` y `docs/DESPLIEGUE.md`
> de hoy):* `desplegar_front.ps1 -SoloFront` (el modo completo regenera el
> secreto de cliente y pisa las redirect URI; no se usa), lanzado **desde
> `infra\` del worktree limpio** (deduce la raíz con `$PSScriptRoot`). El
> merge a `dev`, desde un worktree aparte. En cada publicación, el líder pone
> al día `azure-apps/postventa_incidencias.md` (R20).

## 8 · Lo que queda para otras fichas

Industrial propuesto (F-039), volcado (F-040), aprobar en bloque (F-043): sus
restos siguen en la sección `#/bandeja` del portal, en envoltorios de bloque.

*Conciliado 2026-10-20:* y en `bandeja.html`, F-040 añade el panel de volcado
(la presentación del volcado en la lista ya es de F-038: R21, Q-6), y F-057 el
enlace profundo `?incidencia=`. **Editar o anular una incidencia ya volcada**
(backend y escritura en Sigrid) es una **ficha nueva** que abre el líder
aparte; F-038 no espera por ella y no ofrece nada sobre una `volcada`.

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

*Conciliado 2026-10-20:* ninguna cambia. D-1 está cumplida (F-056 `done`).

**Aprobadas por el humano el 2026-10-20** (las preguntas de la conciliación,
§10.4):

| Id | Decisión |
|---|---|
| Q-6 | **(b) ampliada**: `volcada` y `en_duda` se ven en F-038 **con todo** —estado, «Volcada como <sigrid_cod> por <quien> el <fecha>», el motivo de una `en_duda` si lo hay, el último intento fallido de una aprobada y los filtros `volcada` y `en_duda`—: la presentación del volcado que F-040 tenía en su R54 pasa aquí (R21). **Sin ninguna acción ni formulario** sobre ellas. Motivo del humano: «la idea es gestionar toda la postventa en el portal». Editar o anular una ya volcada es una ficha nueva aparte (§8) |
| Q-7 | Una revisión del sistema se enseña como «el sistema (ubicación puesta en el texto exacto de Sigrid)» (R22) |
| Q-8 | La página **no** ofrece normalizar; R15 se queda en tres rutas más `/.auth/me` (R23) |
| Q-9 | Un valor vigente fuera del catálogo de hoy se **conserva** como opción marcada «no está en la lista de Sigrid de hoy»; el backend lo rechaza junto al campo si se guarda así (R24) |
| Q-10 | El paso 03 de la tira en `bandeja.html`, `<span>` sin `href` ni `aria-current`; el 02 actual con `data-construccion` y su `aria-label`; la guardia de R85 (y la precisión de R87) se ajustan **a propósito** (R25) |

## 10 · Conciliación con `dev` `87a03f3` (2026-10-20)

### 10.1 · Qué hay en `dev` que la spec del 2026-10-06 no veía

| Qué | De dónde | Dónde se recoge |
|---|---|---|
| Estados `volcada` y `en_duda`, sin acciones; 409 `accion_no_permitida` con `estado` y `acciones: []` | F-059 R1–R2, design §4; `EstadoRevision`, `_PERMITIDAS` | R4 (c), R11, R12, R21 |
| `activas` sin descartadas **ni volcadas**; filtros `volcada` y `en_duda` | F-059 R4 (c)–(d), D-7 de F-059; `FiltroEstado`, `_FUERA_DE_ACTIVAS` | R6, R21 |
| Seis estados en `resumen.por_estado` | F-059 R4 (b) | R5 |
| Objeto `volcado` en cada incidencia y en la respuesta de la acción | F-059 R4 (a), F-2 (a); `volcado_de` | R4 (e), R21 (Q-6: de F-038) |
| Revisiones del sistema `sistema:normalizar_ubicacion` | F-060 R22, Q-2 de F-060, design §10.1 | R4 (d), R8, R22 |
| Normalización tras cada importación y `POST /api/revision/normalizar` | F-060 R26–R31 | R15, R23 |
| `catalogo.pares`, `oficio_ambiguo`/`proveedor_ambiguo` en `importados` y `vigentes` | F-056 R28, R29; `_pares`, `_valores_de` | R9 (a)–(c) |
| Los nueve motivos, en el orden de R21 de F-056 | `MotivoNoAprobable` | R4 (a) |
| 400 `sin_cambios`, 404 `incidencia_no_encontrada`, 404/409 de obra, 500, 503 sin `codigo` | `CODIGOS_DE_REVISION`, rutas de `function_app.py` | R12 |
| Ubicación `""` es 400, se quita con `null` | F-056 design §8 y §3.5 (precisión del 2026-10-07) | R9 (d) |
| `duplicada_de` es un UUID, no una fila | `_fila` | R4 (b) |
| `clasificar` de `js/api.js` no conserva lo propio del cuerpo de un error | `js/api.js` de hoy | R26, §2.1 |
| Tamaño de página 100/200, cursor base64url sin relleno | `TAMANO_POR_DEFECTO`, `TAMANO_MAXIMO`, `cursor_de` | R7 |
| El pie de las páginas reales es de su sección | `importar.html`, `oficios.html`, `PIE_PAGINAS_REALES` | R1 |
| La guardia de la tira no admite un paso de la propia sección que no sea el actual | `problemasDelRecorrido` (R85 frente a R86) | R25 |
| Dos controles más que miran `bandeja` | `test_f035_r62_control_el_lector_…`, «f035 R66: control …» | R18, §3.1 |
| `enBloque` de `bandeja.reintentarVolcado`; `propuestas.porFila` por fila de la bandeja | `js/portal.js`, `js/maqueta_datos.js` | R17, §3.2 |
| F-057 y F-040 también tocan `bandeja.html` / `importar.html` | Specs en sus ramas | R14, §2.4, §6.9 |
| La regla del repositorio sobre `azure-apps` y la arquitectura | `CLAUDE.md` | R20 |

### 10.2 · Lo que se comprobó y sigue como decía la spec

- `identidadDe` devuelve `{usuarioOid, correo}`; `/.auth/me` lo sirve el
  proxy (D-13, R10).
- `Portal.PAGINAS` tiene hoy dos páginas (`importar.html`, `oficios.html`);
  `bandeja` está en `construccion` con fichas F-038, F-039, F-040 y F-043; los
  pasos 02 y 03 son de `bandeja` y `pasoDeSeccion("bandeja")` es `"02"`.
- R28, R29 y R62 son los que describe la spec; el control de R28 ya usa F-044;
  el de R62 usa F-038 y se muda a F-044, como decía.
- `staticwebapp.config.json` exige sesión en `/*`; `test_f036_front.py` no se
  toca.
- `infra/desplegar_front.ps1 -SoloFront` e `infra/24_ubicacion_sigrid.ps1
  -CodigoObra` existen con esos parámetros.

### 10.3 · Lo que la conciliación no toca

- `services/postventa-api`: nada de lo encontrado lo necesita. Si al
  implementar apareciera algo que sí, **bloqueo** (límite de servicio).
- Las specs de F-040 y F-057: sus encajes con F-038 se dejan anotados para
  sus propias conciliaciones (`progress/spec_F-038.md`). En particular,
  **F-040 deja de traer la presentación del volcado** (su R54): queda para su
  conciliación quitarla de allí y apoyarse en la de F-038.

### 10.4 · Decisiones nuevas — **aprobadas por el humano el 2026-10-20**

Lo que se preguntó, con la recomendación y las alternativas que se dieron.
**Lo decidido**: Q-6 → **(b) ampliada** (no la recomendada (a)); Q-7, Q-8,
Q-9 y Q-10 → la recomendación. Queda en §9.

| Id | Pregunta | Recomendación | Alternativas |
|---|---|---|---|
| **Q-6** | ¿Qué hace F-038 con `volcada` y `en_duda`? | **(a)** Lo mínimo para no engañar: su etiqueta en la lista, el resumen y el detalle, «Ya no se revisa aquí» y **ningún** botón ni formulario; el historial se lee. Lo demás (línea con `sigrid_cod`, motivos de rechazo del objeto `volcado`, filtros `volcada`/`en_duda`) se queda en **F-040 R54**, como se aprobó (R21). Motivo: con `activas` por defecto, una `en_duda` sale en la lista, y ofrecerle botones que dan 409 confunde. | (a') Como (a), y además los filtros `volcada` y `en_duda` en el selector ya en F-038 (trivial; F-040 R54 los da por suyos). (b) Todo R54 de F-040 aquí (adelanta trabajo de otra ficha aprobada). (c) Nada: el código tal cual (riesgo 10 de F-059); descartada, porque ofrecería acciones que el backend rechaza |
| **Q-7** | ¿Cómo se enseña una revisión del sistema (`sistema:normalizar_ubicacion`, que no es un correo)? | «el sistema (ubicación puesta en el texto exacto de Sigrid)»; cualquier otro `sistema:…`, «el sistema» (R22). Es la «mejora opcional» que F-060 §10.1 dejó para F-038 | Enseñar el literal tal cual (funciona, pero no se entiende) |
| **Q-8** | ¿Ofrece la página normalizar las ubicaciones (`POST /api/revision/normalizar`)? | **No** (R23): corre sola tras cada importación (F-060 R31), lo ya importado de la 0677 se normalizó en su T26, y R15 se queda en tres rutas | Un botón con ensayo previo y confirmación (cuarta ruta: cambia R15, más tests y un acto más que confirmar) |
| **Q-9** | ¿Qué hace el formulario con un valor vigente que no está en el catálogo de hoy (las 38 ubicaciones fuera de lista, un oficio o un proveedor que ya no están)? | **Conservarlo** como opción propia marcada «no está en la lista de Sigrid de hoy» (R24): no se pierde en silencio, y si se guarda así el backend lo rechaza junto a ese campo | Vaciarlo con aviso al abrir el formulario, como al cambiar la unidad (riesgo: quien solo corrige la descripción quita la ubicación sin darse cuenta) |
| **Q-10** | En la tira de `bandeja.html`, el paso 03 es de la misma sección que el actual (02): `enlaceSeccion` da `null` y la guardia pide `aria-current`, que R86 prohíbe | **03 como `<span>` sin `href` ni `aria-current`**, y ajustar la guardia de R85 para ese caso (R25). El 02, actual, lleva `data-construccion` y su `aria-label` mientras la sección esté en construcción, como la pestaña (R2) y como ya exige la guardia; eso contradice la última frase de R87 de F-035 («un paso actual sin enlace no lleva `aria-label`»), que hasta hoy no se había dado | (b) 03 como enlace a `./#/bandeja` (lleva al recuadro «En construcción» del portal: confunde). (c) Seguir la letra de R87 en el 02 (sin `aria-label`) y ajustar también esa parte de la guardia |
