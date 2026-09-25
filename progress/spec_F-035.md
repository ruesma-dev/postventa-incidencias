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
