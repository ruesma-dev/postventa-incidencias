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
> Rama `feature/F-038-bandeja-revision`. Rigor **`critico`**. Solo
> `services/postventa-front` (más las guardias de la raíz de F-035 y, en el
> commit de cierre, `harness/features.json`).
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
- **R5.** El resumen de la obra (total, por estado, aprobadas, con algo que
  corregir y por motivo) debe salir del `resumen` de la respuesta, que es de
  **toda** la obra, no de lo cargado.
- **R6.** Los filtros —estado (por defecto `activas`: todo menos descartadas)
  y «solo las que tienen algo que corregir» (`con_motivos=true`)— deben ir al
  **servidor**: cambiar uno vuelve a pedir la primera página.
- **R7.** **Paginación (Q-2).** CUANDO la respuesta trae `siguiente`, la
  página debe ofrecer «Cargar más» (con «N de M»: lo cargado frente a
  `total_filtrado`), que pide la página siguiente con ese `cursor` y los mismos
  filtros y **añade** sus filas sin repetir ninguna (por `incidencia_id`);
  SI `siguiente` es `null`, ENTONCES no se ofrece.
- **R8.** Al abrir una incidencia, el detalle debe enseñar sus valores
  vigentes y, en cada campo de `cambios`, los importados («llegó así: …»); y
  su historial (`GET /api/revision/historial`) con fecha y hora de Madrid,
  acción, **el correo de quien la hizo**, campos cambiados y motivo.
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
- **R10.** Las acciones deben salir **solo de un clic**, con el cuerpo
  compuesto por **una única función pura** —la única que escribe
  `confirmado: true`—, con `usuario_oid` y `usuario_correo` de `/.auth/me`
  (`identidadDe` de `js/api.js`, D-13) y la `revision_id` de la incidencia como
  `revision_previa`. Sin `oid` o sin correo, ningún botón de acción está
  habilitado (se puede leer). Mientras una acción se guarda, ninguna otra
  sale.
- **R11.** «Aprobar» debe estar deshabilitado, con los motivos a la vista,
  cuando `motivos_no_aprobable` no está vacío o es `null`; «Descartar» pide un
  segundo clic en el propio panel, con el motivo opcional (≤ 500); y
  «Recuperar» solo aparece en una `descartada`.
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
- **R13.** MIENTRAS haya un formulario con cambios sin guardar, salir de la
  página debe pedir confirmación (`beforeunload`); sin cambios, nada (D-12).
- **R14.** El bloque de la bandeja de `importar.html` debe llevar un enlace,
  en la misma pestaña, «Revisar esta obra en la bandeja de revisión» a
  `bandeja.html?obra=<obra>`; ningún otro cambio en esa página ni en
  `js/importacion.js`.
- **R15.** Ningún fichero de la página debe llamar a Sigrid, a SharePoint ni a
  otra ruta que no sean las tres de F-056 y `/.auth/me`; el correo y el `oid`
  no se escriben en la consola ni en el almacenamiento del navegador.

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
- **R18.** Tras ese commit, las guardias de la raíz en verde con F-038 `done`;
  el control de R62 usa otra ficha (F-044); y F-039, F-040 y F-043 conservan
  al menos un resto cada una (R29 de F-035).
- **R19.** El `README.md` del front debe contar la página, su sección, sus tres
  rutas, la paginación y la regla de R16–R17.

## 3 · Fuera de alcance

| Qué | Dónde |
|---|---|
| Estados, reglas, tabla, endpoints, paginación en el servidor, el correo guardado | **F-056** |
| Crear las incidencias en Sigrid | **F-040** |
| Proponer industrial | **F-039** |
| Aprobar o descartar varias a la vez | **F-043** |
| Cambiar `GET /api/bandeja`, la importación, la plantilla, `oficios.html`, `js/importacion.js` | Nadie |

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
| R49 | R11 | | | |
