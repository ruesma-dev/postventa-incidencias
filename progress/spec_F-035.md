<!-- progress/spec_F-035.md -->
# F-035 · Puesta al día de la spec · 2026-09-25

spec-author. Rama `feature/F-035-portal-posventa`, **rebasada sobre `dev`
(`54c0884`)**; sin push. Estado `spec_ready`, **sigue sin aprobar** por el
humano. Sin código; nada ejecutado contra Azure, Sigrid, SharePoint ni
PostgreSQL. La plantilla de impresión **no se ha abierto**.

## 1 · El rebase

- `git rebase dev` desde `05345e0` (base `fadb678`). Conflictos en
  `progress/current.md` y `BACKLOG.md`, resueltos **a favor de `dev`**;
  `harness/features.json` entró sin conflicto con F-035 en `spec_ready`, y
  `BACKLOG.md` se regeneró con `python harness/backlog.py`. El commit de la
  spec original queda como `bedee71`.
- El bloque de F-035 de `progress/current.md` no sobrevivió a la resolución
  (se tomó el fichero de `dev` entero); se reescribe, al día, en el commit de
  esta puesta al día.
- Re-medido sobre `54c0884`: `services/postventa-front/`,
  `infra/desplegar_front.ps1` y `tests/` de la raíz **no han cambiado** desde
  `5bc0ca8` (`git diff --stat` vacío). Las líneas citadas del front siguen
  valiendo. La fila de Entra ID de `docs/ARCHITECTURE.md` pasó de `:544` a
  `:578`.

## 2 · Qué cambió respecto a `05345e0`

Todo lo que enmienda una premisa va en recuadro fechado 2026-09-25, con el
texto original conservado. Lo esencial **no cambia**: página aparte
`portal.html` con rutas por hash, ninguna llamada (R14–R18 intactos), el
circuito intacto (R30–R33), rigor `estandar`, D-1…D-9 con la misma
recomendación.

**requirements.md**

- Cabecera: recuadro de la puesta al día.
- §0 «No entra»: recuadro. Los pasos de alta **llegaron**
  (`docs/referencia/04_alta_incidencia_sigrid.md`); la plantilla existe y
  está **sin revisar**; el Excel **sigue sin llegar**; ninguna llamada a
  `sigrid/partes-reclamacion`.
- R24: precisión (misma regla) con los identificadores nuevos del alta, todos
  ficticios (`99NN.03VILLA N.`, `99NN_REF/NNNN`, `99NN_PER/NNNN`,
  `PVI-EJEMPLO-NNNN`, proveedores `EJNN`), y los catálogos generales con
  códigos reales (D-10).
- R26: enmienda. Los pasos de alta dejan de ser pendiente; quedan el resto de
  columnas del Excel (con los mínimos que ya fija F-036), la plantilla, el
  enlace con la proforma y las preguntas del alta que el contrato no cierra
  (tipo `0003`, oficio con varios intervinientes y causante, estado en que
  nace el parte).
- **Nuevos** (§1.5 bis): **R38** (los campos del alta en el detalle de la
  bandeja y en la pestaña «Datos»), **R39** (tipo y oficio por código y
  resumen; `0003` como pendiente), **R40** (panel de volcado con un dry-run
  y un volcado hecho de ejemplo, de una obra cada uno, con los cinco estados
  del contrato, motivos de su lista cerrada y resumen), **R41** (ruta de
  archivo con la estructura de Posventa, ficticia, sin fichero ni URL).
- R32: nota (la base es ahora `54c0884`; mismos tests).
- Trazabilidad y V3 ampliadas.

**design.md**

- Cabecera: fuentes nuevas y re-medición.
- §5.2 entrada: fuera el pendiente de «pasos de alta»; la tabla de columnas
  enseña los campos mínimos de F-036 y el pendiente del Excel.
- §5.3 bandeja: columnas y detalle con los campos del alta, en el orden de la
  ficha de Sigrid; panel de volcado reescrito sobre el contrato de
  `sigrid_api.md` §8.9 (por obra, dos resultados de ejemplo, etiquetas de
  estado, motivos de la lista cerrada, placeholder nuevo «Reintentar»); se
  **quita** la nota «necesita un endpoint nuevo en `sigrid-api`», que ya no es
  cierta.
- §5.5 ficha: tabla de orígenes enmendada (descripción corta = `con.res`,
  tipo, forma `1 = Escrita`, oficio, **intervinientes** vía `obrofc`,
  referencia externa `conext[RCPCLI]`) y lista cerrada de orígenes ampliada.
  Pestaña «Parte»: la carpeta de archivo de Posventa (R41).
- §5.6 impresión: el pendiente de la plantilla dice que existe y está sin
  revisar.
- §5.7 partes: «archivar en SharePoint» → «en la biblioteca de Posventa».
- §6.3: `bandeja.reintentarVolcado` (F-040).
- §7.1 y §7.2: bloque nuevo `volcado` (F-040) con los catálogos del alta y
  los dos resultados; campos del alta en `bandeja` e `incidencias`;
  `oficiosObra` en `propuestas`; convenciones de lo ficticio ampliadas.
- §8.1: `etiquetaCatalogo`, `resumenVolcado`, `etiquetaEstadoVolcado`.
- §10: enmienda de la fila de F-040 (el endpoint de alta existe en
  `sigrid-api`, pendiente de su despliegue; modificar, F-041, sigue por
  proponer).
- §11: tests de R38–R41 y sexta mutación manual.
- §12: dos riesgos nuevos. §13: **D-10** nueva; D-5 y D-8 con nota. §14:
  **H-3** nuevo.

**tasks.md**: ninguna tarea nueva; T1, T2, T3, T5, T6, T8, T10, T11 y T12
dicen qué entra de lo nuevo.

## 3 · Preguntas abiertas para el humano

Las de siempre (`design.md` §13; **bloquean el arranque D-1, D-2 y D-6**):
D-1 página aparte, D-2 enlaces a pestaña nueva, D-3 portada, D-4 publicar la
maqueta con el siguiente despliegue del front, D-5 grupo de Entra
(`ARCHITECTURE.md:578` sigue diciendo «no existe»), D-6 qué funciona, D-7
ubicaciones, D-8 `azure-apps` sin tocar, D-9 mutación de JavaScript.

Nuevas de esta puesta al día:

1. **D-10 · Catálogos con códigos reales.** Recomendación: estados, tipos de
   reclamación, formas de comunicación y oficios con sus códigos reales de
   Sigrid (`0002 · PRIMER LISTADO POSTVENTA`, `0143 · Carpintería de
   madera`); todo lo que identifica a alguien o a una obra, ficticio.
   ¿Conforme? Condiciona T5.
2. **La plantilla de impresión**
   (`postventa_17-12-2025.pdf`, en OneDrive, Documentos/postventa). **No se
   ha abierto ni convertido.** ¿Lleva datos personales? ¿Autorizas mirarla
   (y convertirla con `markitdown` a `docs/referencia`) ya, para que la
   sección `impresion` de la maqueta enseñe su forma, o se queda para la spec
   de F-044 como dice su ficha? Recomendación: **dejarla para F-044**; la
   maqueta solo dice que existe y está sin revisar.
3. **El Excel de ejemplo** sigue sin llegar. La maqueta enseña los campos
   mínimos que fija la ficha de F-036 y un pendiente. ¿Hay fecha, o se valida
   la maqueta con Posventa sin él?
4. **Estado en que nace un parte (H-3, para F-040).** La captura del alta
   manual lo enseña en `PTE`; `sigrid-api` lo crea en `SAT` y no pasa a
   `PTE`. La maqueta no elige. Conviene preguntarlo a Posventa en la
   validación (V3), junto con el tipo `0003` y quién marca «Causante».

## 4 · Lo que no se ha hecho

- No se ha abierto ni convertido la plantilla de impresión.
- No se ha tocado `azure-apps/` ni `arnes-base` (nada del arnés cambió).
- `harness/features.json`: sin cambios en esta puesta al día (F-035 sigue en
  `spec_ready`).
- `bash harness/init.sh` no se ha ejecutado: esta puesta al día solo cambia
  Markdown de `specs/` y `progress/`.

---

# F-035 · Enmienda por las decisiones del humano · 2026-09-25

spec-author. Rama `feature/F-035-portal-posventa` sobre `fb356a4`; sin push.
Estado **`spec_ready`**, **pendiente de aprobación** de la spec enmendada.
Sin código. Solo lecturas: el árbol del front, `azure-apps/` y la tarjeta en
`front-portal/public/assets/js/catalog.js` (ni host ni GUID copiados). La
plantilla de impresión **no se ha abierto**. Acta literal de las respuestas:
`design.md` §13.1.

## 5 · Qué cambia

**D-1** («pagina aparte. esto que hemos hecho sera una pestaña de dicho
portal»), **D-2** («barra superior») y **D-3** («si») cambian la premisa:

- **El portal es la portada**: ocupa `index.html` (ya no existe
  `portal.html`). **El circuito se muda** con `git mv` a `partes.html` y es
  la pestaña `partes` del portal. Una **barra superior común** en las dos
  páginas.
- **Opción elegida (E)**: el circuito sigue en su propio HTML y la barra lo
  presenta como pestaña. Riesgo para producción: cambia **solo su URL** y
  gana un bloque de HTML sin directivas; ni un módulo JS, ni
  `css/styles.css`, ni `staticwebapp.config.json`, ni `dev_server.py`, ni
  backend.
- **Descartadas**, medidas: (F) reescribir `/` en la Static Web App —cero
  tests tocados, pero toca el fichero de autenticación de todo el front
  (`/api/*` incluido), obliga a replicarlo en `dev_server.py` y no se puede
  comprobar sin desplegar que la plataforma distinga `/` de `/index.html`—;
  (G) `<iframe>` —`globalHeaders` lleva `X-Frame-Options: DENY`, que lo
  impide incluso en el mismo origen—; (H) incrustar el marcado —es
  reescribir el circuito—.
- **Tests que fijan `index.html`**: la spec decía nueve; medidos, **siete**
  lo fijan como el circuito, con **una** línea `INDEX = …` cada uno
  (`test_f007_estaticos`, `f009`, `f012`, `f025`, `f026_autoguardado`,
  `f026_front`, `f028`). Los otros dos (`test_f007_dev_server`, que exige un
  `index.html` para arrancar y lo sigue teniendo, y `test_f031_front`, solo
  en un mensaje) no cambian. Al mover la constante, las aserciones negativas
  **siguen al circuito** a `partes.html` y el portal queda fuera de ellas sin
  acotar ninguna. Guardia nueva (R32 enmendado): solo esa línea en esos
  siete; `tests_js/` intacto.
- **Del circuito al portal, pestaña nueva del navegador**: `js/*.js` no
  tiene `beforeunload` y la remesa vive en memoria; poner aviso sería tocar
  `app.js`. Del portal al circuito, misma pestaña.
- **Tarjeta del portal corporativo**: ya existe en `front-portal` y apunta
  a la **raíz**: con D-3 **aterriza en el portal**, que es lo que se quiere,
  sin tocar `front-portal`. Su título y descripción describen solo el
  circuito (H-4, propuesta de texto en `design.md` §14).
- **`#/partes`** en el portal cae en `inicio` (R5): no hay bloque `partes`.
  Lo que tenía esa sección (frase y placeholder de F-045) pasa a la tarjeta
  «Partes firmados» de `inicio`.

**requirements.md**: recuadros en cabecera, §0, vocabulario, R1, R3, R5
(nota), R17, R30–R32 (R33 no cambia), R34–R35, R36–R37, trazabilidad y §3.
**Nuevos**: R42 (la portada es el portal), R43 (`partes.html` = el
`index.html` de la base + línea 1 + barra), R44 (barra común, mismos
`href` que `Portal.enlaceSeccion`), R45 (barra del circuito inerte: sin
`x-`/`@`/`:`, sin `<script>`/`<button>`), R46 (portal → circuito en la misma
pestaña), R47 (leyenda de maqueta en la barra del circuito). V1 y V2 con las
URL nuevas; **V4** nuevo (tras publicar, D-4).

**design.md**: recuadros en cabecera, §1.2 (medición de los tests), §1.3
(quién sirve `/`, acceso, `X-Frame-Options`, la tarjeta), §2 (la decisión,
cuatro opciones, la barra), §3.1–§3.3, §4, §5.1, §5.5, §5.7 (la sección
`partes` deja de ser bloque), §6.3, §8.1 (`SECCIONES.pagina`,
`resolverRuta`, `enlaceSeccion` nueva), §9 (D-5), §11 (tests de R30, R32,
R42–R47; mutaciones 7 y 8), §12 (seis riesgos), **§13.1 acta**, §14 (H-1
resuelto, H-2 precisado, **H-4** tarjeta, **H-5** mutación de JS).

**tasks.md**: la T8 y la T9 de la premisa se conservan tachadas en un
recuadro; entran **T8** (mudanza: `git mv` + línea 1 + las siete líneas
`INDEX`, en un solo commit), **T9** (el portal en `index.html`) y **T9 bis**
(la barra en `partes.html`). T1, T2, T3, T10, T11 y T12 enmendadas; T13
sigue la última; tras ella, la publicación de D-4 (del humano) con V4.

**El resto**: D-4 («si»), publicar tras V1 y V2. D-5 («creo que existe»):
el líder midió `posventa-usuarios` (seguridad, 7 miembros) y `Postventa`
(no de seguridad, 9); T10 corrige `docs/ARCHITECTURE.md:578` con recuadro y
sin GUID. D-6, D-7, D-8 y D-10 con la recomendación. D-9: queda la
recomendación; **la mutación de JavaScript la registra el líder aparte como
propuesta del arnés** (H-5). Plantilla de impresión: para F-044, sin abrir.

## 6 · Abierto para el humano

1. **Aprobar la spec enmendada** (T1), en particular lo que D-3 arrastra y
   no se había enseñado: el circuito en `partes.html`, **una línea en siete
   tests** del circuito, y la pestaña nueva del navegador al salir del
   circuito.
2. **D-7, consecuencia de D-1**: el placeholder de F-045 ya no puede ir en
   una sección `partes` del portal (esa pestaña es el circuito); va en la
   tarjeta «Partes firmados» de `inicio` y en la ficha. ¿Conforme?
3. **D-5, alcance del acceso**: ¿el portal es para `posventa-usuarios` (7) o
   se amplía al departamento (¿los 9 de `Postventa`?)? No bloquea: F-035
   hereda el acceso que haya; ampliarlo es Entra, del humano.
4. **H-4, la tarjeta**: ¿se cambia título y descripción en `front-portal`?
   Propuesta en `design.md` §14; no se toca desde aquí.
5. Siguen de antes: el Excel de ejemplo (sin fecha) y el estado en que nace
   un parte (H-3, para V3 y F-040).

## 7 · Lo que no se ha hecho

- Ni código ni tests: solo `specs/` y `progress/`.
- No se ha tocado `azure-apps/`, `front-portal` ni `arnes-base`.
- `harness/features.json`: F-035 sigue en `spec_ready`, sin cambios.
- `bash harness/init.sh` no se ha ejecutado: solo cambia Markdown.
