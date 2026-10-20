<!-- specs/F-038-bandeja-revision/requirements.md -->
# F-038 · Bandeja de revisión: editar, descartar y aprobar incidencias antes del volcado — Requisitos

> **Aprobado por el humano el 2026-10-06**, con estas decisiones (detalle en
> `design.md` §9): **D-1** partir por el límite de servicio —el backend es
> **F-056** (`specs/F-056-revision-bandeja-backend/`), que va antes; F-038 es
> la página del portal y el cierre de la sección, **bloqueada por F-056**—;
> **D-4** ubicación obligatoria para aprobar, **contra Sigrid en vivo**
> (decisión del humano 2026-10-06; fuente, la **Q-5 de F-056, resuelta** el
> mismo día: las ubicaciones de la tipología de **cada unidad**, por unidad);
> **D-8** se enseña el **correo**
> de quien hizo cada cosa; **Q-2** la lista se **pagina**; y D-2, D-3, D-5,
> D-6, D-7, D-9, D-10, D-11, D-12, D-13 y D-14 como se recomendaban.
>
> **Conciliada con `dev` el 2026-10-20, base fija `87a03f3`** (F-056, F-060 y
> F-059 cerradas, mergeadas y desplegadas). Las decisiones aprobadas **no
> cambian**. Lo que cambia es el contrato que se consume, ahora el de verdad
> («tal como está implementado»): los requisitos tocados llevan la marca
> *«Conciliado 2026-10-20»* con su fuente, y lo nuevo va al final, en §2 bis
> (R20–R26). **R21–R25 dependen de las preguntas Q-6 a Q-10 y están
> PENDIENTES DE APROBACIÓN DEL HUMANO** (`design.md` §10.4); el resto de la
> conciliación es contrato y no decide nada nuevo. Detalle de cada cambio y su
> porqué: `progress/spec_F-038.md`, sección «Conciliación con dev · 2026-10-20».
>
> Rama `feature/F-038-bandeja-revision`. Rigor **`critico`**. Solo
> `services/postventa-front` (más las guardias de la raíz de F-035, en el
> commit de cierre `harness/features.json`, y los documentos de R20).
>
> **Renumeración.** La spec del 2026-10-06 tenía R1–R58 en dos tramos; el
> backend (R1–R40) es ahora F-056 con su propia numeración, y aquí R41–R58
> pasan a R1–R19 (tabla al final).

## 0 · De dónde sale

La ficha pide que una incidencia de la bandeja se pueda editar, descartar o
aprobar con constancia de quién y cuándo, y que solo lo aprobado sea
candidato al volcado. Las reglas, la tabla y los tres endpoints son de
**F-056**; aquí está la página que los usa y el cambio de la sección
«Bandeja de revisión» del portal (F-035) de «En construcción» a «En
producción». Los dos apuntes del cierre de F-036 —las 144 filas con oficio o
proveedor viejos y las 47 con oficio ambiguo— se **ven** en esta página por
sus motivos de no aprobable y se **corrigen** con su formulario.

El contrato que se consume es el de `specs/F-056-revision-bandeja-backend/`
(requirements R5–R33 y design §8): `GET /api/revision` (paginado),
`GET /api/revision/historial` y `POST /api/revision/acciones`.

*Conciliado 2026-10-20.* Con lo que añadieron después, sin cambiar ninguna
forma salvo una clave nueva:

- **F-059** (`specs/F-059-volcado-sigrid-backend/`, R1–R4, design §4 y §12):
  dos estados más, **`volcada`** y **`en_duda`**, desde los que **no se admite
  ninguna acción** (409 `accion_no_permitida` con `estado` y `acciones: []`);
  `activas` deja fuera las descartadas **y las volcadas**; dos filtros más
  (`volcada`, `en_duda`); seis estados en `resumen.por_estado`; y un objeto
  **`volcado`** en cada incidencia (listado y respuesta de la acción).
- **F-060** (`specs/F-060-normalizar-ubicaciones/`, R22, R31, R36, design
  §10.1): revisiones `editar` **del sistema**, con `revisado_por` y `correo`
  iguales al literal `sistema:normalizar_ubicacion` (no es un correo); la
  normalización corre sola tras cada importación; y una ruta más,
  `POST /api/revision/normalizar`. Ninguna clave cambia.

## 1 · La página de revisión

- **R1.** El front debe tener una página real nueva, **`bandeja.html`** (D-2),
  declarada en `Portal.PAGINAS` como `"bandeja.html": "bandeja"`, con todo lo
  que F-035 exige a una página real: la barra común con la pestaña de su
  sección como `<span aria-current="page">` (R70 de F-035), la leyenda de la
  barra, las migas «Portal de posventa › Bandeja de revisión» (enlaces a
  `index.html` y a `./#/bandeja`), la tira del recorrido con el paso 02 como
  actual (R83–R88), la identidad Ruesma con la misma `?v=` de
  `css/styles.css` y el pie común (R72), ningún placeholder ni envoltorio
  `data-en-construccion` ni fichero de la maqueta (R77) y ningún enlace con
  `target` (R73).
  *Conciliado 2026-10-20 (`dev` de hoy: `importar.html`, `oficios.html`,
  `tests/test_f035_paginas.py`):* el pie común es la estructura
  (`<footer class="rs-pie">` con `rs-contenedor rs-pie__texto`); su texto es
  de cada sección («… · entrada de incidencias.» en las dos de `entrada`), y
  el de esta página, «Construcciones Ruesma · Posventa · bandeja de
  revisión.». Sin subnavegación: la sección `bandeja` tiene una sola página
  real (la subnavegación de R71 es de `entrada`). El paso 03 de la tira, en
  R25.
- **R2.** MIENTRAS la sección `bandeja` esté en `construccion`, la pestaña
  «Bandeja de revisión» de `bandeja.html` debe llevar `data-construccion` y su
  `aria-label` «(en construcción)», como las otras cuatro barras (R66).
- **R3.** La página debe tener un campo «Código de obra» (relleno con `?obra=`
  si la URL lo trae) y «Cargar», que pide la **primera página** de
  `GET /api/revision` con los filtros elegidos.
- **R4.** La lista debe enseñar, por incidencia: unidad, ubicación,
  descripción corta, oficio («código · nombre», «sin elegir: varios códigos
  en la obra» o «sin oficio»), proveedor, urgencia, estado, la marca
  «duplicada de la fila N», los motivos de no aprobable en texto legible y,
  si tiene revisiones, «<acción> por <correo> el <fecha>» (D-8).
  *Conciliado 2026-10-20:* (a) los motivos son los **nueve** de
  `MotivoNoAprobable` (`domain/models/revision.py`), en su orden —
  `unidad_fuera_de_la_obra`, `sin_ubicacion`, `ubicacion_fuera_de_lista`,
  `sin_oficio`, `oficio_ambiguo`, `oficio_fuera_de_la_obra`,
  `par_fuera_de_la_obra`, `proveedor_ambiguo`, `duplicada`—, cada uno con su
  texto (F-056 design §3.5), y un código que no esté en la lista se enseña
  tal cual, sin romper la fila; (b) `duplicada_de` es el `incidencia_id` de la
  original, no un número de fila: N es el `fila_origen` de la original **si
  está entre las cargadas**; si no, «duplicada de otra fila del mismo
  fichero» (con paginación, la original puede no estar cargada); (c) el
  estado es uno de los **seis** (R21); (d) quien revisó por última vez es
  `revisado_por`, que en las revisiones del sistema no es un correo (R22); y
  (e) el objeto `volcado` no se enseña aquí (es F-040, R21).
- **R5.** El resumen de la obra (total, por estado, aprobadas, con algo que
  corregir y por motivo) debe salir del `resumen` de la respuesta, que es de
  **toda** la obra, no de lo cargado.
  *Conciliado 2026-10-20 (F-059 R4 (b)):* `por_estado` trae **seis** estados
  y la página enseña los seis con su etiqueta (R21); `por_motivo`, los nueve
  de R4 (a).
- **R6.** Los filtros —estado (por defecto `activas`: todo menos descartadas)
  y «solo las que tienen algo que corregir» (`con_motivos=true`)— deben ir al
  **servidor**: cambiar uno vuelve a pedir la primera página.
  *Conciliado 2026-10-20 (F-059 R4 (d), D-7 de F-059; `FiltroEstado`):*
  `activas` es todo menos `descartada` **y `volcada`** (incluye `en_duda`). El
  selector de estado ofrece `activas` (por defecto), `todas`, `nueva`,
  `editada`, `aprobada` y `descartada`; `volcada` y `en_duda`, según Q-6
  (R21).
- **R7.** **Paginación (Q-2).** CUANDO la respuesta trae `siguiente`, la
  página debe ofrecer «Cargar más» (con «N de M»: lo cargado frente a
  `total_filtrado`), que pide la página siguiente con ese `cursor` y los mismos
  filtros y **añade** sus filas sin repetir ninguna (por `incidencia_id`);
  SI `siguiente` es `null`, ENTONCES no se ofrece.
  *Conciliado 2026-10-20 (`interface_adapters/api/revision.py`):* el
  `cursor` es opaco (base64url sin relleno) y viaja tal cual, sin
  decodificarlo ni construirlo; la página no manda `tamano` (el servidor da
  100 por defecto, 200 como mucho).
- **R8.** Al abrir una incidencia, el detalle debe enseñar sus valores
  vigentes y, en cada campo de `cambios`, los importados («llegó así: …»); y
  su historial (`GET /api/revision/historial`) con fecha y hora de Madrid,
  acción, **el correo de quien la hizo**, campos cambiados y motivo.
  *Conciliado 2026-10-20:* el «correo» de una revisión del sistema se enseña
  como dice R22.
- **R9.** El formulario de edición debe ofrecer solo valores del `catalogo`
  de la respuesta: unidades de la obra; ubicaciones **solo de
  `catalogo.ubicaciones[<unidad elegida en el formulario>]`**, la lista de
  Sigrid de hoy de esa unidad con la que el backend valida (F-056 R28, R48):
  lo que se ofrece es lo que se puede aprobar. Al **cambiar la unidad**, la
  ubicación elegida se **revalida** contra la lista de la nueva: si está, se
  conserva; si no, se vacía y se dice («esta ubicación no es de la nueva
  unidad»). Una unidad con lista vacía no ofrece ninguna. Vacía se permite al
  guardar, pero la fila queda con `sin_ubicacion`. Oficios por
  código («código · nombre»), con los del grupo de la fila primero si su
  oficio es ambiguo; proveedores **solo** del oficio elegido o «sin
  proveedor»; urgencia y listado de sus listas. Cambiar el oficio vacía un
  proveedor que no case. Descripción y detalle con contador (128 y 2000).
  *Conciliado 2026-10-20 (F-056 R13–R16, R28 y design §8, tal como están en
  el handler):*
  (a) los proveedores de un oficio salen de **`catalogo.pares`**
  (`[{oficio_codigo, proveedor_codigo, proveedor_nombre}]`), los de ese
  `oficio_codigo`, con su `proveedor_nombre` (o el código si es `null`);
  (b) «el grupo de la fila» de un oficio ambiguo son las entradas de
  `catalogo.oficios` cuyo `grupo.etiqueta` es el `oficio_nombre` vigente;
  (c) con el oficio ambiguo **sin elegir**, el proveedor solo puede ser el
  vigente o «sin proveedor» (F-056 R15), y el cuerpo lleva
  `oficio_codigo: null`;
  (d) una ubicación vacía viaja como **`null`**, nunca `""` (`""` es 400
  `valores_no_validos` en `ubicacion`, F-056 design §8); un detalle vacío,
  como `null`;
  (e) «hay cambios» se decide con la misma normalización que el backend
  (descripción con los blancos colapsados; detalle, motivo y ubicación
  recortados), para no mandar una edición que el servidor rechazaría con
  400 `sin_cambios` (F-056 R16);
  (f) lo que hace el formulario con un valor vigente que **no** está en el
  catálogo de hoy, en R24.
- **R10.** Las acciones deben salir **solo de un clic**, con el cuerpo
  compuesto por **una única función pura** —la única que escribe
  `confirmado: true`—, con `usuario_oid` y `usuario_correo` de `/.auth/me`
  (`identidadDe` de `js/api.js`, D-13) y la `revision_id` de la incidencia como
  `revision_previa`. Sin `oid` o sin correo, ningún botón de acción está
  habilitado (se puede leer). Mientras una acción se guarda, ninguna otra
  sale.
  *Conciliado 2026-10-20 (handler `_peticion`):* el cuerpo lleva
  **exactamente** las claves de su acción —las seis comunes, más `valores`
  (las ocho claves de `CAMPOS_PEDIDOS`) en `editar` y `motivo` (opcional) en
  `descartar`—; una clave de más es 400. La acción **no se reintenta sola**
  (es el acto de una persona, como `decidirCatalogos` de F-036).
- **R11.** «Aprobar» debe estar deshabilitado, con los motivos a la vista,
  cuando `motivos_no_aprobable` no está vacío o es `null`; «Descartar» pide un
  segundo clic en el propio panel, con el motivo opcional (≤ 500); y
  «Recuperar» solo aparece en una `descartada`.
  *Conciliado 2026-10-20 (F-056 design §3.3, F-059 design §4.2;
  `_PERMITIDAS`):* cada estado ofrece **solo** sus acciones: `nueva` y
  `editada`, «Editar», «Descartar» y «Aprobar»; `aprobada`, «Editar» y
  «Descartar» (no «Aprobar»: ya lo está); `descartada`, «Recuperar»;
  `volcada` y `en_duda`, **ninguna** (ni el formulario).
- **R12.** CUANDO una acción responde 200, la página debe sustituir la
  incidencia por la de la respuesta y **ajustar el resumen** con la
  diferencia entre la fila de antes y la de después, sin recargar; si trae
  `motivos_no_aprobable: null`, enseña «recarga para ver si se puede aprobar»
  en vez de habilitar «Aprobar». Con 409 `revision_desactualizada`: «otra
  persona la ha cambiado» y vuelve a pedir la primera página; con 409
  `incidencia_no_aprobable`, sus motivos; con 400 `valores_no_validos`, el
  problema junto a cada campo; con 409 `bandeja_demasiado_grande`, que la obra
  pasa del tope y no se puede revisar aquí; con 503, que no se ha guardado
  nada.
  *Conciliado 2026-10-20 (`CODIGOS_DE_REVISION`, `_error_de_revision`,
  `_rechazo_de_obra` y las rutas de `function_app.py`):* los errores reales
  son `{error, codigo}` más lo propio de cada uno, y la página los trata así:

  | HTTP · `codigo` | Lo propio del cuerpo | Qué hace la página |
  |---|---|---|
  | 400 `peticion_invalida` | — | «La página ha mandado algo que el servicio no acepta; no se ha guardado nada. Recarga la página.» (es un fallo de la página) |
  | 400 `valores_no_validos` | `errores: [{campo, problema}]` (`campo`, una clave de `CAMPOS_PEDIDOS`) | El `problema` junto a cada campo; el formulario sigue abierto |
  | 400 `sin_cambios` | — | «No hay cambios que guardar»; el formulario sigue abierto |
  | 404 `incidencia_no_encontrada` | — | «Esta incidencia ya no está en la bandeja» y primera página |
  | 404 `obra_sin_unidades` | — | El texto del servicio (listado y acción) |
  | 409 `accion_no_permitida` | `estado`, `acciones` | «Esta incidencia está <estado>: ya no admite esa acción» y primera página (otra persona la ha cambiado o la han volcado) |
  | 409 `revision_desactualizada` | — | «Otra persona la ha cambiado» y primera página |
  | 409 `incidencia_no_aprobable` | `motivos` | Sus motivos en texto (R4 (a)) |
  | 409 `bandeja_demasiado_grande` | `total` | Que la obra pasa del tope (con `total`) y no se puede revisar aquí |
  | 409 `obra_ambigua`, `catalogo_sin_verificar` | — | El texto del servicio |
  | 500 (sin `codigo`) | — | El texto del servicio; no se ha guardado nada |
  | 503 (sin `codigo`) | — | El texto del servicio, que dice que no se ha escrito nada |
  | Sin respuesta (red, tiempo) en una acción | — | «No se sabe si se ha guardado: recarga para verlo» y primera página; la `revision_previa` impide que un segundo intento pise al primero |

  Para eso `js/api.js` debe conservar lo propio del cuerpo en el error
  (R26). Un `codigo` que no esté en la tabla se trata por su HTTP, con el
  texto del servicio.
- **R13.** MIENTRAS haya un formulario con cambios sin guardar, salir de la
  página debe pedir confirmación (`beforeunload`); sin cambios, nada (D-12).
- **R14.** El bloque de la bandeja de `importar.html` debe llevar un enlace,
  en la misma pestaña, «Revisar esta obra en la bandeja de revisión» a
  `bandeja.html?obra=<obra>`; ningún otro cambio en esa página ni en
  `js/importacion.js`.
  *Conciliado 2026-10-20:* el enlace va **fuera** de la `<table>` de la
  bandeja (`test_f036_r50_la_bandeja_es_de_solo_lectura` no admite controles
  dentro) y no es un `<button>` (`botones_prohibidos` de F-036). **Solape con
  F-057** (`pending`, spec en `feature/F-057-tabla-bandeja-paso1`): rehace esa
  tabla y conserva este enlace (su R27), y añade a `bandeja.html` el enlace
  profundo `?incidencia=` (su R23–R25, con el «Editar» de su R21); va
  **después** de F-038.
- **R15.** Ningún fichero de la página debe llamar a Sigrid, a SharePoint ni a
  otra ruta que no sean las tres de F-056 y `/.auth/me`; el correo y el `oid`
  no se escriben en la consola ni en el almacenamiento del navegador.
  *Conciliado 2026-10-20:* `POST /api/revision/normalizar` (F-060) **no** es
  una de las tres; si la página la ofrece o no es Q-8 (R23).

## 2 · El portal cuando F-038 se cierra

- **R16.** MIENTRAS F-038 no esté `done`, la sección `bandeja` del portal sigue
  como hoy (`construccion`, su envoltorio y los placeholders de F-038), y las
  guardias de la raíz (R28, R29 y R62 de F-035) en verde.
- **R17.** En **un solo commit** —el que pasa F-038 a `done` (D-11)—: `bandeja`
  en `parcial` en `Portal.SECCIONES`; fuera `data-construccion` y su
  `aria-label` de la pestaña `bandeja` en las cinco barras y de los pasos 02 y
  03 en las cinco tiras; fuera el envoltorio de sección de `#/bandeja`, con
  una tarjeta «En producción» a `bandeja.html` y lo que sigue sin funcionar en
  envoltorios de bloque de F-039, F-040 y F-043; el chip «En producción» en la
  tarjeta de la bandeja de la portada; y fuera los placeholders de F-038, sus
  entradas de `Portal.PLACEHOLDERS`, su bloque de `MaquetaDatos` y su título
  de `TITULOS_FICHAS`.
  *Conciliado 2026-10-20 (recontado sobre `87a03f3`):* los restos de F-038 son
  **siete** —tres placeholders en `index.html`, tres entradas de
  `PLACEHOLDERS` y el bloque `bandeja` de `MaquetaDatos`—, más su título de
  `TITULOS_FICHAS` (que el escáner no cuenta, pero R65 sí usa). Al irse las
  filas de ejemplo de la bandeja, **dos** placeholders `enBloque: true` se
  quedan sin selección que contar: `bandeja.aprobarSeleccionadas` (F-043) y
  `bandeja.reintentarVolcado` (F-040); y `MaquetaDatos.propuestas.porFila`
  (F-039) apunta a esas filas por su `id`. Cómo se resuelve, en `design.md`
  §3.2.
- **R18.** Tras ese commit, las guardias de la raíz en verde con F-038 `done`;
  el control de R62 usa otra ficha (F-044); y F-039, F-040 y F-043 conservan
  al menos un resto cada una (R29 de F-035).
  *Conciliado 2026-10-20:* recontados hoy, F-039 tiene 5 restos, F-040 7 y
  F-043 6; tras el cierre siguen con al menos uno cada una (F-039 y F-043
  tienen restos fuera de `#/bandeja`; los de F-040 se quedan en su envoltorio
  de bloque). Hay **dos controles más** que miran la sección `bandeja` y que
  el cierre rompería: `test_f035_r62_control_el_lector_de_estados_lee_el_texto`
  (raíz; cambia `bandeja` a `parcial` en una copia y, con `bandeja` ya en
  `parcial`, la copia no cambiaría) y «f035 R66: control: quitar
  data-construccion de una pestaña de partes.html salta» (front; quita la
  marca de la pestaña `bandeja`). Los dos pasan a otra sección que siga en
  `construccion` (`impresion`, la de F-044) en el Bloque 1, como el de R62.
- **R19.** El `README.md` del front debe contar la página, su sección, sus tres
  rutas, la paginación y la regla de R16–R17.

## 2 bis · Lo nuevo de la conciliación (2026-10-20)

R20 y R26 son contrato y reglas del repositorio. **R21 a R25 son decisiones
nuevas, PENDIENTES DE APROBACIÓN DEL HUMANO**: van redactadas con la
recomendación de su pregunta (`design.md` §10.4) y cambian si el humano elige
otra alternativa.

- **R20.** *(Regla del repositorio: la página nueva es algo que el proyecto
  expone.)* `docs/ARCHITECTURE.md` debe contar la página (su sección, sus
  rutas y que `Portal.PAGINAS` gana `bandeja.html`), y
  `azure-apps/postventa_incidencias.md` debe nombrar `bandeja.html` junto a
  `importar.html` y `oficios.html`. El segundo es de otro repositorio: lo
  actualiza **el líder**, en un commit de `azure-apps`, al publicar (T6) y al
  cerrar (T10), como hizo F-059 con su Q-6.
- **R21.** *(Q-6, pendiente.)* MIENTRAS una incidencia esté `volcada` o
  `en_duda`, la página debe enseñarla con su etiqueta —«Volcada a Sigrid» y
  «En duda: se mandó a Sigrid y no consta qué pasó»— y la frase «Ya no se
  revisa aquí», **sin ningún botón de acción ni formulario** (R11), y su
  historial se puede leer. El objeto `volcado` (`sigrid_cod`, quién y cuándo
  volcó, el motivo de un rechazo), la línea «Volcada como RS… por <correo> el
  <fecha>», los textos de los motivos de rechazo y los filtros `volcada` y
  `en_duda` son de **F-040** (su R54, aprobado el 2026-10-07), que los añade
  a esta página; mientras tanto, se ven con `todas` (las volcadas) y con
  `activas` (las en duda).
- **R22.** *(Q-7, pendiente.)* CUANDO `revisado_por` (en la lista) o `correo`
  (en el historial) es el literal `sistema:normalizar_ubicacion`, la página
  debe enseñar «el sistema (ubicación puesta en el texto exacto de Sigrid)»
  en lugar del literal; cualquier otro valor que empiece por `sistema:`, «el
  sistema»; y un correo, tal cual (D-8).
- **R23.** *(Q-8, pendiente.)* La página **no** debe ofrecer normalizar las
  ubicaciones ni llamar a `POST /api/revision/normalizar`: la normalización
  corre sola tras cada importación (F-060 R31) y R15 sigue con tres rutas.
- **R24.** *(Q-9, pendiente.)* CUANDO se abre el formulario de una incidencia
  cuyo valor vigente de unidad, ubicación, oficio o proveedor **no** está
  entre las opciones del catálogo de hoy, el formulario debe **conservarlo**
  —como opción propia marcada «no está en la lista de Sigrid de hoy»—, sin
  vaciarlo en silencio; si se guarda así, el backend responde 400
  `valores_no_validos` en ese campo y la página lo enseña junto a él (R12).
  Es el caso de las 38 ubicaciones fuera de lista que F-060 no normaliza.
  Cambiar la unidad sigue vaciando la ubicación que no es de la nueva (R9).
- **R25.** *(Q-10, pendiente.)* En la tira de `bandeja.html`, el paso **03**
  «Sigrid» (de la misma sección, `bandeja`, y para el que `enlaceSeccion`
  devuelve `null`) debe ser un `<span>` **sin** `href` y **sin**
  `aria-current`, porque el paso actual es solo el 02 (R86 de F-035); y el
  paso 02, actual, lleva `data-construccion` y su `aria-label` mientras la
  sección esté en construcción, como la pestaña de R2. La guardia de la tira
  (`tests_js/portal.test.js`, R85) se ajusta para el paso de la propia
  sección que no es el actual.
- **R26.** *(Contrato.)* Las tres funciones de revisión de `js/api.js` deben
  dar, en el error, además del texto y el `codigo` del servicio, **lo propio
  del cuerpo** de R12 (`errores`, `motivos`, `estado`, `acciones`, `total`),
  y el texto del servicio también en un 503 (no el de la puerta de entorno de
  archivar). La lectura (`GET /api/revision` y el historial) reintenta lo
  transitorio como las demás lecturas; la acción, no (R10). Ningún error de
  F-056 lleva el correo (F-056 R11).

## 3 · Fuera de alcance

| Qué | Dónde |
|---|---|
| Estados, reglas, tabla, endpoints, paginación en el servidor, el correo guardado | **F-056** |
| Los estados `volcada` y `en_duda`, el objeto `volcado` | **F-059** (backend, hecho) |
| La línea del parte volcado, los motivos de rechazo, los filtros `volcada`/`en_duda`, el panel de volcado | **F-040** (su R50–R59; R21 aquí si Q-6 sale como se recomienda) |
| Normalizar las ubicaciones | **F-060** (tras cada importación; R23 si Q-8 sale como se recomienda) |
| La tabla ancha de `importar.html` y el enlace profundo `?incidencia=` | **F-057** |
| Crear las incidencias en Sigrid | **F-040** |
| Proponer industrial | **F-039** |
| Aprobar o descartar varias a la vez | **F-043** |
| Cambiar `GET /api/bandeja`, la importación, la plantilla, `oficios.html`, `js/importacion.js` | Nadie |
| Cualquier cambio en `services/postventa-api` | Nadie desde aquí: si hiciera falta, es un bloqueo (límite de servicio) |

## 4 · Correspondencia con la numeración del 2026-10-06

| Antes | Ahora | | Antes | Ahora |
|---|---|---|---|---|
| R41 | R1 | | R50 | R12 |
| R42 | R2 | | R51 | R13 |
| R43 | R3 | | R52 | R14 |
| R44 | R4 | | R53 | R15 |
| R45 | R5, R6 | | R54 | R16 |
| — | R7 (paginación, nuevo) | | R55 | R17 |
| R46 | R8 | | R56, R57 | R18 |
| R47 | R9 | | R58 | R19 |
| R48 | R10 | | R1–R40 | F-056 |
| R49 | R11 | | — | R20–R26 (conciliación del 2026-10-20) |
