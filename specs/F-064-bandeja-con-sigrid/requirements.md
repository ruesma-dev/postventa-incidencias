<!-- specs/F-064-bandeja-con-sigrid/requirements.md -->
# F-064 · La bandeja enseña también las incidencias que ya están en Sigrid y los conflictos con lo importado — Requisitos

> **Spec conjunta partida por el límite de servicio (Q-1, aprobada por el
> humano el 2026-10-21).** Esta ficha es la **página** (`bandeja.html`):
> requisitos **R50–R69**. El backend —las dos rutas de solo lectura, el cruce
> y los criterios, R1–R40— es **F-065**
> (`specs/F-065-revision-sigrid-backend/`), y va antes. Orden: **F-038 →
> F-065 → F-064 → F-040**. F-064 está bloqueada por F-065 **y por F-038 en
> `done`** (las dos tocan `bandeja.html` y `js/revision.js`).
>
> Rigor **`critico`**: es la pantalla con la que se aprueba lo que luego se
> escribe en Sigrid, y enseña datos personales de clientes.
>
> **Decisiones del humano del 2026-10-21**, todas «Aprobada por el humano el
> 2026-10-21» (`design.md` §6 y `specs/F-065-revision-sigrid-backend/design.md`
> §14.1): Q-1 partición; **Q-2 todas las reclamaciones de la obra, con
> filtros en pantalla**; Q-3 criterios; **Q-4 no bloquea: aviso y segundo
> clic**; Q-5 ruta aparte; **Q-6 los datos personales se enseñan en la
> página**, nunca en consola, almacenamiento, logs ni repositorio; Q-7, Q-8,
> Q-9 y Q-10 como se recomendaban; y las que derivan de ellas en F-065
> (§14.2), **aprobadas también el 2026-10-21**: N-1 una sola lectura con el
> techo de la pasarela (llegan todas las reclamaciones de la obra de una vez),
> N-2 la «descripción parecida» y **N-3 todo en el listado, una sola ruta**: los
> datos personales viajan con cada reclamación para poder **buscar y filtrar
> por propietario o teléfono** en la página; no hay ficha bajo demanda.

## 0 · De dónde sale

Petición del humano (2026-10-20): «en la bandeja de revisión deberán poder
verse tanto las incidencias que queremos importar que salen del Excel, como
las que ya hay en Sigrid y si hay conflictos entre ellas». F-065 sirve las
reclamaciones de la obra, con sus datos (también los personales de su R33), y
los hallazgos, en **una sola ruta** (`GET /api/revision/sigrid`); esta ficha
los enseña en `bandeja.html`, junto a la revisión de F-038, que no cambia.

## 1 · La carga

**R50.** CUANDO se carga la bandeja de una obra, la página debe pedir
`GET /api/revision/sigrid` **a la vez** que la primera página de
`GET /api/revision`, sin esperar una a la otra. La lectura de Sigrid se
reintenta ante lo transitorio y **no** bloquea ni retrasa la lista de la
bandeja.

**R51.** SI la lectura de Sigrid falla (503, 409, sin respuesta o tiempo
agotado), ENTONCES la bandeja debe seguir **entera y operativa** —listar,
filtrar, editar, descartar, aprobar— y el panel de Sigrid debe decir, con texto
propio por caso, que no se han podido mirar las reclamaciones ni los
conflictos, con un botón **«Volver a mirar Sigrid»**. MIENTRAS se lee,
«Leyendo Sigrid…».

**R52.** «Volver a mirar Sigrid» y el cambio de obra deben volver a pedir el
listado de Sigrid; **ninguna otra cosa** lo pide (ni una acción, ni un filtro,
ni «Ver más»).

## 2 · Cómo se ve

**R53.** La página debe ofrecer un selector de vista: **«Bandeja»** (la de
F-038, por defecto), **«Ya en Sigrid (N)»** y **«Conflictos (N)»**, con N de la
respuesta (Q-7, aprobada el 2026-10-21).

**R54.** La vista «Ya en Sigrid» debe listar **todas** las reclamaciones de la
respuesta, de solo lectura, marcadas «Sigrid · solo lectura»: código, estado
legible («Sin atender», «Pendiente», «Terminada», «Cerrada», «No procede»; un
código desconocido, tal cual), fecha, unidad (el nombre del catálogo de la
página si la unidad está en él; si no, el código), ubicación, oficio, tipo,
descripción, **propietario** y **persona que reclama**; las emparejadas,
«Volcada desde el portal». Pagina en el navegador de 100 en 100 con «Ver más».
**Ningún** botón, enlace ni formulario que escriba. *(N-1 de F-065: llegan
todas en una respuesta.)*

**R55.** *(Q-2, aprobada el 2026-10-21.)* La vista «Ya en Sigrid» debe tener
**filtros en pantalla**, aplicados en el navegador sobre lo ya leído y sin
volver a pedir nada: **estado** (varios a la vez; por omisión, todos), **fecha
desde** y **fecha hasta**, **unidad**, **oficio**, **tipo**, **persona**
(busca en propietario, persona que reclama y persona de contacto), **teléfono**
(compara solo las cifras, en todos los teléfonos de la reclamación y de sus
personas: «000 00 00 00» encuentra «000000000»), **correo** (en los de avisos y
de las personas, sin mayúsculas), **texto** (en código, ubicación, descripción
corta y larga, motivo y solución, sin tildes ni mayúsculas), **«solo volcadas
desde el portal»** y **«solo con conflicto o aviso»**; un recuento «N de M» y
«Quitar filtros». *(N-1 y N-3 de F-065.)*

**R56.** Cada tarjeta de la bandeja con hallazgos debe enseñar **una línea por
hallazgo**, compuesta por una única función pura (`lineaDeHallazgo`), con
estilo distinto para conflicto y aviso; con más de 3 `coincide`, las 3 primeras
y «y N más» (`coincidencias_total`). Ejemplos: «Choca con RS26.09/0123
(Pendiente): misma unidad, oficio y ubicación»; «Choca con RS26.08/0046
(Sin atender): misma unidad y descripción parecida (50 %)»; «Ya hubo una igual,
cerrada: RS26.03/0456 (Cerrada, mayo de 2026)»; «Sigrid ya tiene este parte:
RS26.10/0074».

**R57.** La vista «Conflictos» debe listar los hallazgos con incidencia, de
solo lectura, con un filtro **conflictos / avisos / todos** (por omisión,
conflictos), enseñando de cada par la incidencia (los campos de `incidencias`
de la respuesta) y la reclamación; «Ir a la incidencia» **solo** si está
cargada en la lista; si no, una nota de cómo llegar (filtrar o «Ver más»).

## 3 · Aprobar con un conflicto (Q-4, aprobada el 2026-10-21)

**R58.** CUANDO una incidencia con algún hallazgo de severidad **conflicto**
ofrece «Aprobar», el primer clic **no debe mandar nada**: enseña los conflictos
y cambia el botón a **«Aprobar a pesar del conflicto»**; solo el segundo clic,
sobre la misma incidencia y sin haber cambiado de fila ni de vista, manda la
acción, con el **mismo** `cuerpoDeAccion` de F-038, sin ningún campo nuevo. Con
solo avisos, «Aprobar» funciona como en F-038. Con Sigrid sin leer o con error,
«Aprobar» funciona como en F-038 y la tarjeta dice que los conflictos no se han
podido mirar.

**R59.** CUANDO una acción se acepta, el panel de Sigrid debe marcar «Los
conflictos pueden haber cambiado» y **no** volver a leer Sigrid sin un clic
(Q-8, aprobada el 2026-10-21).

## 4 · La ficha de una reclamación (Q-6 y N-3 de F-065, aprobadas el 2026-10-21)

**R60.** Cada reclamación de «Ya en Sigrid» y de «Conflictos» debe poder
**desplegar su ficha** con lo que ya trae la respuesta —descripción larga,
motivo, urgencia, forma de comunicación, fecha prevista, solución, clase,
teléfonos y correo de avisos, propietario, persona que reclama y persona de
contacto con sus teléfonos y correos—, de solo lectura, **sin pedir nada al
servidor**, con un aviso «Datos personales: no los copies fuera de Sigrid». Un
campo sin valor no se pinta.

**R61.** Los datos de Sigrid —la lista, las fichas y los filtros con texto—
deben vivir **solo en memoria**: al cambiar de obra o recargar, se descartan;
no se guardan en el almacenamiento del navegador ni en la URL.

## 5 · Seguridad y forma

**R62.** Ni los datos de Sigrid —textos, nombres, teléfonos, correos,
referencias, códigos de reclamación—, ni los correos de quien revisa, ni el
`oid` deben ir a `console` ni al almacenamiento del navegador (`localStorage`,
`sessionStorage`, IndexedDB), tampoco los filtros si llevan texto.

**R63.** La lógica de presentar, filtrar, componer las líneas, contar, el
estado del panel, la ficha y la doble confirmación debe vivir en un módulo
**puro** (`js/sigrid_bandeja.js`) probado con `node --test`; el HTML no lee la
respuesta cruda.

**R64.** `js/api.js` debe ganar **una** función de lectura,
`sigridDeLaBandeja(obra)`, con reintentos de lectura y el mensaje del
servicio; ninguna otra ruta nueva.

**R65.** `bandeja.html` no debe nombrar ninguna ruta de escritura nueva, ni
llamar a la pasarela, ni a `POST /api/revision/normalizar`; las acciones siguen
saliendo solo de un `@click`.

**R66.** Todo texto que venga de Sigrid se pinta como **texto** (`x-text`),
nunca como HTML (`x-html`), ni en la lista ni en la ficha.

**R67.** Los tests usan **solo datos inventados** («Ejemplo …»,
`@ejemplo.invalid`, `000 000 000`); un test comprueba que los ficheros de tests
de F-064 no traen otro dominio de correo.

**R68.** `docs/ARCHITECTURE.md` (sección de la página de revisión), el README
del front y `azure-apps/postventa_incidencias.md` deben describir el panel, los
filtros, la ficha y dónde no van los datos personales.

**R69.** Verificación en producción: `MANUAL (humano)`, `tasks.md` Bloque B5.
