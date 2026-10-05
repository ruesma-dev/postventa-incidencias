<!-- specs/F-036-importar-excel/requirements.md -->
# F-036 · Importar el Excel de incidencias de la propiedad a una bandeja — Requisitos

> Rama `feature/F-036-importar-excel`. Rigor **`critico`**. Spec escrita por el
> spec-author el 2026-09-28 contra la ficha de `harness/features.json`
> (actualizada ese día con las decisiones del humano), la muestra
> `docs/referencia/05_excel_creacion_incidencias.md`, el alta manual
> `docs/referencia/04_alta_incidencia_sigrid.md` y el contrato del alta en lote
> de `azure-apps/sigrid_api.md` §8.9.
>
> Cada requisito se traduce a ≥ 1 test con nombre `test_f036_rN_...`. Los que
> solo pueden comprobarse contra Sigrid o PostgreSQL reales se verifican a mano
> (tareas `MANUAL (humano)` de `tasks.md`).

> **Enmienda del 2026-09-28 · revisión del humano sobre la spec de `101345d`.**
> Cuatro decisiones nuevas (§0 bis) cambian requisitos ya escritos; cada cambio
> lleva su recuadro con lo que decía antes. En resumen:
>
> 1. **Importación parcial**: las filas buenas entran y las malas vuelven en un
>    **Excel de errores** con la misma plantilla (R33, R39, R42, R43 cambian;
>    R62–R70 nuevos).
> 2. **Todo valor que no sea texto libre es tasado** y se compara **exacto**, sin
>    casado aproximado (R26, R29, R30, R31 cambian).
> 3. **Columna nueva `Proveedor`**, opcional y tasada (R2, R3, R5 cambian;
>    R71–R77 y R91 nuevos).
> 4. **Proveedores casi duplicados del maestro de Sigrid**: propuesta automática,
>    confirmación humana y equivalencias guardadas en el schema `postventa`
>    (R78–R90 nuevos).
>
> Retocados de paso para ser coherentes: R1, R11, R12, R21, R23, R35, R37,
> R47, R50–R52, R58–R61.
>
> Lo demás de la spec queda **aprobado** por el humano con las opciones por
> defecto de `design.md` §13.

> **Segunda enmienda del 2026-09-28 · los oficios también se agrupan** (sobre
> `ced9c8f`). El catálogo de oficios de Sigrid tiene entradas casi iguales, como
> el de proveedores, y el desplegable de `Oficio` enseña **una entrada por
> oficio real** (decisión 10). El mecanismo de §12 deja de ser «de proveedores»
> y pasa a ser **uno solo para los dos catálogos**. Cambian R8, R30, R51, R61,
> R71, R74, R75, R77, R78, R81, R83, R84, R86–R89 y R91; nuevos R92–R99 (R97,
> en §8, es de la migración). Las rutas
> `/api/proveedores/*` pasan a `/api/catalogos/*` y la página
> `proveedores.html` a `catalogos.html`.

> **Tercera enmienda del 2026-09-28 · el oficio de un proveedor sale de sus
> familias en Sigrid** (sobre `6cf1bf1`, decisión 11). Los proveedores que
> se ofrecen siguen siendo **los de la obra** (`obrofc`), pero qué oficios
> cubre cada uno lo dicen sus **familias asignadas** (`confam` → `auxfam`),
> no el oficio con el que figura en `obrofc`. Si familia y oficio son el mismo
> catálogo no se sabe: se mide (T1/T2, T8) y el diseño se bifurca con la
> medición. Cambian R71 y R94; nuevos R100–R110 (§14). Un proveedor que
> cubre un oficio por familia pero no figura en `obrofc` con ese oficio
> queda marcado `proveedor_fuera_de_obrofc` y F-040 no lo manda como
> interviniente (R104, R106).

> **Cuarta enmienda del 2026-09-28 · actividades (`conact`/`auxpronat`).** La
> medición de T2 (`progress/explore_F-036.md`) desmiente la tercera: `confam`,
> `auxfam` y `entfam` están **vacías** y `prv.ofcide` solo está relleno en 3
> de 526 proveedores. Las «familias» del humano son las **actividades** del
> proveedor, `conact` → `auxpronat` (catálogo en árbol, otro vocabulario que
> `auxofc`). §14 se reescribe (R100–R110 revisados, R111–R114 nuevos): la
> correspondencia actividad → oficio es una tabla que confirma el humano, por
> hoja, por rama o las dos (D-29), en el catálogo `actividad_oficio` del mismo
> mecanismo; y el texto medido tiene que llegar en UTF-8 sin doble
> codificación (R111). La medición decidió además D-2, D-8 y D-9 y el origen
> de las ubicaciones (D-3): `design.md` §13. Sobre la agrupación de
> proveedores, con **0** grupos en todo `obrofc`, el líder recomienda sacarla
> a otra ficha; el humano no lo ha decidido (D-18) y la spec deja preparadas
> las dos opciones.

> **Quinta enmienda del 2026-09-29 · PARADA T3: se simplifica.** Decisiones
> 12 y 13 del humano (§0 bis): (1) **opción A**, la relación oficio ↔
> proveedor de la plantilla sale **solo** de `obrofc` de la obra; las
> actividades (`conact`/`auxpronat`), su correspondencia con los oficios y el
> proveedor fuera de `obrofc` **salen a F-039**: §14 queda retirada; (2) la
> agrupación de **proveedores sale a F-050**; se queda la de **oficios**,
> con la costura del discriminador `catalogo` (§12). Cambian R51, R71, R72,
> R75, R78, R87–R89, R94, R96 y R98; R90 sale a F-050. La pantalla pasa a
> `oficios.html`. Lo medido en T1/T2 queda como hecho (R109, R111
> cumplidos).

> **Sexta enmienda del 2026-09-30 · review 1** (`progress/review_F-036.md`,
> CHANGES_REQUESTED). Dos requisitos nuevos, en §15: **R115**, el lector del
> Excel no recorre las hojas más allá del tope de filas (una celda con estilo
> en la fila 1.048.576 costaba ~51 s y ~1,9 GB), que precisa R20; y **R116**,
> el informe de migración no lleva códigos de proveedor, que precisa R58. El
> humano decidió además B5-1 (`COLLATE "C"` en el `CHECK` del par,
> `design.md` §6.1) y que el merge a `dev` sea con `git merge --squash`.

> **Sexta enmienda bis del 2026-09-30 · review 2** (CHANGES_REQUESTED, R2-1 y
> R2-3). R115 se amplía a lo que la biblioteca de Excel **expande al cargar**
> (rangos combinados, hipervínculos sobre un rango), en cualquier hoja: el
> libro se abre en modo de solo lectura (`design.md` §5.2). Y se corrige la
> errata del recuadro de R20: el código no cambia; el mensaje, en el caso
> nuevo, sí.

> **Séptima enmienda del 2026-10-01 · review 3** (CHANGES_REQUESTED, R3-1 y
> R3-2; el humano eligió hacer R3-1 el 2026-10-01). Requisito nuevo **R117**:
> antes de abrir el libro se cuentan, en *streaming*, los elementos XML de
> todas sus partes, con un presupuesto global de **200.000**; por encima,
> `fichero_sospechoso` (R16). Cierra la clase de ficheros pequeños con
> millones de elementos (64 KB con 4,1 millones de `<xf/>`: 114 s y 2,5 GB).

> **Séptima enmienda bis del 2026-10-01 (hallazgo T37-1; el humano eligió la
> opción (a)).** R117 cuenta **todas las partes del ZIP, sea cual sea su
> extensión** (una hoja guardada como `sheet1.dat` se saltaba el recuento:
> 74 KB → 48 s y 911 MB), y el presupuesto pasa a **300.000** para que quepa
> el Excel de errores más grande (148.916 elementos, con el VML de los
> comentarios).

> **Octava enmienda del 2026-10-01 · cambio de estrategia** (review 4, R4-1;
> decisión del humano: opción (A) del líder «pero dobla los límites»). Tras
> cuatro huecos de la misma familia —fila lejana, rangos al cargar, elementos XML
> y atributos con listas de rangos (`sqref`)—, la lectura con `openpyxl` de un
> fichero subido pasa a un **proceso hijo con tope de 30 s y de 1 GB**: si se
> pasa o muere, `fichero_sospechoso` (R118, §17). El tope descomprimido de R16
> pasa a **el doble** del fichero legítimo más grande, medido. Se mantienen el
> solo lectura, R115 y R117 como primera línea barata. R4-1 queda cerrado por
> R118, sin parche propio.

> **Décima enmienda del 2026-10-02 · formato visual** (petición del humano al
> abrir el `v2` de T28: el aspecto era «horrible»; lo quiere «limpio, ordenado,
> con colores Ruesma»; aprobó una muestra el mismo día). Requisitos nuevos en
> §18: **R121–R125**, el aspecto de la plantilla y del Excel de errores
> (cabecera, cuerpo, columna de errores y celdas con error, «Instrucciones»,
> impresión); **R126**, los invariantes: el formato **no cambia nada de lo que
> lee el importador** y las plantillas ya descargadas siguen valiendo; y
> **R127**, el formato cabe en los topes vigentes sin tocarlos. Ningún
> requisito anterior fijaba un color: R64 dice «relleno de color» y sigue
> igual, con una nota. Sin logotipo ni imágenes.

> **Enmienda 10 bis del 2026-10-02 · sin impresión y una sola fila a la
> vista** (review 7, R7-1 y R7-2; decisión del humano, literal: «no se
> imprimirá, o se importa o exporta a excel (de momento solo importar). la
> plantilla vacía no hace falta que tenga más de 1 línea»). Corrige la décima:
> **R125** pasa a «**sin ajustes de impresión**», con lo que el test fija como
> ausente; **R122** y **R123** pasan lo visible del cuerpo (líneas finas,
> bandas alternas y gris de `Errores`) de estilo estático en las 1.000 filas a
> **formato condicional**: se ve la fila 2 siempre y cada fila en cuanto
> lleva algo escrito. Las 1.000 filas siguen **preparadas** igual que antes
> (desbloqueo, formato `@`, desplegables, tope de 1.000 filas: R126 no
> cambia). **R126** suma la plantilla con el formato de la décima a las que
> se siguen importando igual, y **R127** pasa a tres reglas condicionales y
> pide medir de nuevo. R121, R124, los colores, las fuentes, los anchos y las
> pestañas no cambian. La impresión a PDF de los partes de trabajo es otra
> feature (F-044) y no aplica a este Excel.

> **Undécima enmienda del 2026-10-03 · la migración ante un catálogo de
> Sigrid que ha cambiado** (verificación MANUAL T29; decisión del humano,
> literal: «para rehacer v2, que al crear el excel, antes lea sigrid y en el
> v2 estén solo los oficios de sigrid»). El `v2` de T28 se generó con el
> catálogo leído de Sigrid el 2026-09-29. El 2026-10-03 la 0677 tenía otros
> oficios (18 de 39 filas de `obrofc` distintas: salen 5 oficios, entran 10,
> uno cambia de proveedor), y el entorno, que lee Sigrid en vivo, dejó 14
> filas del `v2` con error («no está en la lista de la obra»). **La
> aplicación hizo lo correcto**; lo que falla es generar el `v2` con un
> catálogo guardado. Al repetir la migración con el catálogo del día, el
> script se paraba porque un oficio de la tabla («V-Aire acondicionado», dos
> filas) ya no es de la obra. Cambia **R97** (un nombre que es de Sigrid
> pero ya no de la obra deja de parar; la errata sigue parando); nuevos, en
> §19: **R128** (ese oficio queda vacío y se avisa), **R129** (el proveedor
> del `v2` sale solo del catálogo con que se ejecuta), **R130** (el informe
> y la salida lo cuentan) y **R131** (el `v2` definitivo se genera con el
> catálogo y los grupos leídos en el momento). La interfaz del script no
> cambia. **La bandeja no se toca** (decisión del humano): las filas ya
> importadas con el catálogo viejo se quedan; las versiones viejas se
> descartarán con F-038.

> **Nota de la tercera enmienda.** La frase «Lo demás de la spec queda
> aprobado…» había quedado, al insertar la segunda enmienda, al final del
> recuadro de esta; es del primero y se ha devuelto a su sitio.

## 0 · Decisiones del humano del 2026-09-28 (no se reabren)

1. **El Excel de hoy es la muestra, no el contrato.** La feature lo mejora en
   formato y en contenido.
2. **Entregable 1 · la plantilla**: un `.xlsx` generado **por obra** desde el
   portal, con desplegables cargados desde Sigrid (unidades de posventa y
   oficios **de esa obra**): quien rellena ve nombres, el sistema resuelve
   códigos. Cabecera fija, una incidencia por fila sin celdas heredadas, hoja de
   instrucciones, descripción corta ≤ 128 (`con.res`) y detalle aparte,
   urgencia/seguridad como **columna**, ubicación de **lista cerrada**, un
   defecto por fila.
3. **Entregable 2 · el importador**: **solo** acepta la plantilla nueva; el
   formato viejo se rechaza con un motivo claro. Valida, marca duplicados (clave
   con unidad + ubicación + descripción normalizada: el mismo texto con distinta
   ubicación **es legítimo**), deja las filas en una bandeja **persistida**,
   reimportar no duplica y **no escribe en Sigrid**. Errores por fila y columna.
4. **Entregable 3 · la migración**: el Excel actual pasado a la plantilla nueva
   con el contenido corregido, entregado como `creacion_incidencias_v2.xlsx`
   junto al original en el OneDrive del humano, **sin tocar el original** y sin
   versionar ningún `.xlsx`. Las correcciones de contenido son **una propuesta
   que valida el humano**.
5. **Quien rellena es la propiedad (externa)**: la plantilla se tiene que
   entender sin formación.

### 0 bis · Revisión del humano del 2026-09-28 (no se reabren)

6. **Se importan las filas buenas y se devuelve un Excel solo con las
   erróneas**: la misma plantilla de esa obra (mismos catálogos y
   desplegables), cada error explicado en la fila y en la celda. La propiedad lo
   corrige y lo vuelve a subir; reimportar no duplica las buenas ya importadas.
   Un fichero que no es la plantilla se sigue rechazando entero.
7. **Todo valor de la plantilla es tasado**, salvo los textos libres
   (descripción corta y detalle): lista cerrada con validación estricta, y el
   importador rechaza cualquier valor que no esté **exactamente** en el
   catálogo. No hay casado aproximado de lo que llega escrito.
8. **Columna `Proveedor`, opcional y tasada**, con los proveedores de **esa
   obra** (`obrofc`) y preferiblemente solo los del oficio elegido. El importador
   valida que el proveedor esté ligado a ese oficio en la obra. Vacío, se
   completa en la bandeja (F-039). Se guarda para que F-040 lo lleve como
   interviniente. En el Excel migrado queda vacío salvo que la medición lo
   resuelva sin duda.
9. **Los proveedores casi duplicados del maestro de Sigrid se agrupan**: una
   entrada por empresa real. Propuesta automática por similitud, **confirmación
   humana siempre** (ante la duda, separadas) y equivalencias guardadas **fuera
   de git** (hay autónomos con nombre de persona). Cada grupo se resuelve al
   código de Sigrid que está en `obrofc` de esa obra para ese oficio.
10. **Los oficios también se agrupan** (segunda revisión del 2026-09-28): el
    desplegable de `Oficio` enseña una entrada por oficio real, con **el mismo
    mecanismo** que los proveedores —propuesta por similitud, solo cliques,
    confirmación humana, decisiones por pares y append-only—. El CIF y las
    formas jurídicas solo cuentan en proveedores. Un grupo de oficios se
    resuelve al código que está en `obrofc` de esa obra; si hay varios, la fila
    queda `oficio_ambiguo`, con la misma política que los proveedores.
11. **El oficio de un proveedor sale de las familias que Sigrid le tiene
    asignadas** (tercera revisión del 2026-09-28): «el oficio del proveedor
    viene de sigrid (las familias asignadas a un proveedor)». Se ofrecen
    **los proveedores de la obra** (`obrofc`), para que `sigrid-api` §8.9
    los acepte tal como está, **filtrados por familia**: qué oficios cubre
    cada uno se decide por sus familias, no por el oficio con el que figura
    en `obrofc`. Si familia (`auxfam`) y oficio (`auxofc`) son el mismo
    catálogo, el humano no lo sabe: **que se mida**.
    *(Cuarta enmienda del 2026-09-28: se midió. Las «familias asignadas a un
    proveedor» no están en `confam`/`auxfam`, que están vacías, sino en sus
    **actividades**, `conact` → `auxpronat`; así lo confirma el director de
    Compras con la ficha del proveedor delante. La decisión del humano no
    cambia: cambia de qué tabla se lee, §14.)*
    *(Quinta enmienda del 2026-09-29: sustituida por la decisión 12.)*
12. **Opción A** (PARADA T3, 2026-09-29): en F-036, la relación oficio ↔
    proveedor de la plantilla sale **solo** de `obrofc` de la obra, que es lo
    único que acepta `sigrid-api` §8.9. Las actividades del proveedor y su
    correspondencia con los oficios **pasan a F-039**. Los oficios que están en
    la obra sin proveedor (en la 0677, `0133`, `0144` y `0166`) no ofrecen
    ninguno: la fila entra sin proveedor y F-039 lo propondrá.
13. **La agrupación de proveedores sale a F-050** (D-18, PARADA T3,
    2026-09-29): 0 grupos parecidos entre los 526 proveedores de `obrofc`, y
    la plantilla solo ofrece proveedores de la obra. **Se queda la de
    oficios**, con el mecanismo preparado para que F-050 lo reutilice.

## Alcance

**Dentro**: generar la plantilla de una obra (`GET /api/plantilla`), importar
una plantilla rellena a la bandeja (`POST /api/importaciones`) devolviendo el
Excel de errores cuando los haya, ver lo que hay en la bandeja de una obra, en
solo lectura (`GET /api/bandeja`), proponer y confirmar grupos de oficios
casi duplicados (`GET /api/catalogos/propuestas`,
`POST /api/catalogos/decisiones`), las páginas del front que hacen todo eso,
tres tablas nuevas en el schema `postventa`, **dos** lecturas nuevas de Sigrid
por `sql/read` (unidades de la obra, y oficios de la obra con sus
proveedores), el script de migración del Excel actual y su informe de
revisión, y
la documentación de lo que cambia en `docs/INTEGRACION.md` y
`azure-apps/postventa_incidencias.md`.

> **Enmienda del 2026-09-28.** El párrafo anterior decía «dos tablas nuevas» y
> no mencionaba el Excel de errores ni los endpoints de proveedores.
> **Segunda enmienda del mismo día**: decía «grupos de proveedores» y las rutas
> `/api/proveedores/*`.
> **Tercera enmienda del mismo día**: decía «dos lecturas nuevas de Sigrid»; la
> tercera es la de las familias de los proveedores de la obra (R107).
> **Cuarta enmienda del mismo día**: decía «tres lecturas» y «familias»; son
> las actividades (`conact`) y el árbol (`auxpronat`), R107.
> **Quinta enmienda (2026-09-29)**: decía «grupos de oficios y de
> proveedores» y cuatro lecturas; los proveedores salen a F-050 y las
> actividades a F-039, y vuelven a ser dos lecturas.

**Fuera** (y dónde va):

| Qué | Dónde |
|---|---|
| Editar, descartar o aprobar una fila de la bandeja; su estado de revisión y quién y cuándo | **F-038** |
| Proponer el industrial cuando `Proveedor` viene vacío; elegir el código cuando un grupo tiene varios en la obra para ese oficio | **F-039** / **F-038** |
| Crear las incidencias en Sigrid (`sigrid/partes-reclamacion`), la `referencia_externa` `PVI-…`, el tipo `0002`/`0003`, los intervinientes | **F-040** |
| Que la urgencia viaje a Sigrid (`rcp.texurg`): §8.9 **no la admite** hoy | **F-040**, y quizá una petición al dueño de `sigrid-api` |
| Corregir el maestro de proveedores **en Sigrid** (fusionar fichas) | Nadie desde aquí: Sigrid solo se lee |
| Corregir el catálogo de oficios **en Sigrid** (fusionar entradas de `auxofc`) | Nadie desde aquí: Sigrid solo se lee |
| La entrada desde la web de clientes | **F-037** (la bandeja queda preparada para su `origen`, nada más) |
| La sección «Entrada» del portal de F-035 | Cuando F-035 se mergee (D-1) |
| Llevar la bandeja al datamart | **F-048** |
| Las actividades del proveedor (`conact` → `auxpronat`), la correspondencia actividad → oficio y proponer un proveedor que no está en `obrofc` con ese oficio (quinta enmienda) | **F-039**, con la dependencia de `sigrid-api` que eso trae |
| Agrupar los proveedores casi duplicados del maestro (quinta enmienda) | **F-050** |

> **Segunda enmienda del 2026-09-28.** La fila de los oficios decía «Agrupar
> oficios casi duplicados de `auxofc` · Se mide; decisión abierta D-21». El
> humano decidió agruparlos (decisión 10): ahora es alcance de F-036, y lo que
> queda fuera es corregirlos en Sigrid.

## Vocabulario

- **Plantilla**: el `.xlsx` que genera este servicio para una obra. Tiene
  **versión** (hoy, `1`).
- **Catálogo de la obra**: las unidades de posventa (`con.tip 707`, `upv`) y los
  oficios de la obra con sus proveedores (`obrofc` → `auxofc`, `prv`) leídos de
  Sigrid.
- **Etiqueta**: lo que ve quien rellena en un desplegable (un nombre). El
  **código** es lo que guarda el sistema.
- **Tasado**: el valor tiene que ser, carácter a carácter, una de las etiquetas
  de su lista.
- **Bandeja**: las incidencias importadas que esperan revisión, en
  `postventa.bandeja_incidencias`.
- **Clave de duplicado**: la huella de obra + unidad + ubicación normalizada +
  descripción normalizada (R35).
- **Formato antiguo**: el de `docs/referencia/05_excel_creacion_incidencias.md`
  (sin cabecera, unidad solo en la primera fila).
- **Excel de errores**: la plantilla de la obra con solo las filas que no
  entraron, explicadas (R62–R70).
- **Grupo** (de oficios o de proveedores): varios códigos de **un mismo
  catálogo** de Sigrid que una persona ha confirmado que son el mismo oficio o
  la misma empresa. Sin confirmación, cada código es su propio grupo. *(Segunda
  enmienda del 2026-09-28: decía solo «grupo de proveedores».)*
- **Catálogo** (en §12): `oficio` (`auxofc`) o `proveedor` (`prv`).

## 1 · La plantilla

- **R1** · CUANDO llega `GET /api/plantilla?obra=<código>`, el sistema debe
  leer en ese momento el catálogo de esa obra en Sigrid y los grupos de
  proveedores confirmados, y devolver **200** con un `.xlsx` (`Content-Type:
  application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  `Content-Disposition: attachment;
  filename="plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx"`).
- **R2** · La plantilla debe tener una hoja visible **«Incidencias»** cuya fila 1
  es la cabecera, con exactamente estas columnas y en este orden: `Unidad`,
  `Ubicación`, `Descripción corta`, `Detalle`, `Oficio`, `Proveedor`,
  `Urgencia`, `Listado`, `Errores (lo rellena el sistema)`. Los paneles quedan
  inmovilizados bajo la cabecera y la cabecera va bloqueada (protección de hoja
  sin contraseña, con las celdas de datos desbloqueadas —salvo la columna
  `Errores`— y permitido insertar y borrar filas, ordenar y filtrar).

  > **Enmienda del 2026-09-28.** Decía siete columnas, sin `Proveedor` ni
  > `Errores`. `Proveedor` es la decisión 8; `Errores` va en **toda** plantilla
  > para que el Excel de errores (R62) tenga la misma cabecera que la plantilla y
  > se pueda volver a subir. El importador ignora su contenido (R66).

- **R3** · Las columnas `Unidad`, `Ubicación`, `Oficio`, `Proveedor`, `Urgencia`
  y `Listado` deben llevar un desplegable (validación de lista, estilo
  **«detener»**, sin permitir otro valor, con mensaje de entrada y de error en
  español) en las filas 2 a 1001, alimentado desde una hoja de catálogos en
  estado **`veryHidden`**.

  > **Enmienda del 2026-09-28.** Se añade `Proveedor` y se dice explícitamente
  > que la validación no admite otro valor (decisión 7).

- **R4** · `Descripción corta` debe llevar validación de longitud **1–128** y
  `Detalle` de **0–2000**, con mensaje de entrada y de error en español.
- **R5** · La plantilla debe tener una hoja visible **«Instrucciones»** que diga,
  en lenguaje llano: para qué sirve; **una incidencia —un defecto— por fila**;
  que la unidad se elige en cada fila y **no se hereda de la de arriba**; que
  todo lo que tiene desplegable **se elige del desplegable** y no se escribe ni
  se pega; qué columnas son obligatorias (`Unidad` y `Descripción corta`); qué
  va en la descripción corta y qué en el detalle; que el proveedor es opcional y
  sale junto a su oficio; que la urgencia y el peligro para la seguridad se
  marcan **en la columna `Urgencia`** y no en mayúsculas en el texto; que si
  llega de vuelta un Excel de errores se corrigen las filas marcadas y se vuelve
  a subir ese mismo fichero; que no se cambien la cabecera ni los nombres de las
  hojas; y dos o tres **filas de ejemplo** (en esta hoja, **nunca** en
  «Incidencias»).

  > **Enmienda del 2026-09-28.** Se añaden el uso obligado del desplegable, el
  > proveedor y el Excel de errores.

- **R6** · La plantilla debe llevar una hoja `veryHidden` de metadatos con el
  identificador de la plantilla, su **versión** (`1`), el código de la obra y el
  instante de generación en UTC.
- **R7** · Ninguna celda generada puede ser una fórmula. Un texto que llegue de
  Sigrid o del fichero subido y empiece por `=`, `+`, `-` o `@` debe escribirse
  como **texto**.
- **R8** · La etiqueta de una unidad debe ser su nombre (`con.res`) recortado;
  SI dos unidades de la obra comparten nombre normalizado o el nombre está
  vacío, ENTONCES la etiqueta de cada una de ellas debe ser `<nombre> (<código>)`
  —o el código a secas si no hay nombre—. Los oficios tienen su propia regla
  (R92). Las listas van **ordenadas por código** y la función es determinista:
  el mismo catálogo da siempre las mismas etiquetas.

  > **Segunda enmienda del 2026-09-28.** Decía «Los oficios, igual, distintos
  > por código»: ahora el desplegable de oficios enseña grupos (R92).
- **R9** · SI el código de obra falta o, normalizado como los demás códigos del
  proyecto (sin espacios, F-032), está vacío, pasa de 24 caracteres o lleva algo
  fuera de `[0-9A-Za-z._-]`, ENTONCES el sistema debe responder **400** sin
  llamar a Sigrid.
- **R10** · SI ninguna obra con ese código tiene unidades de posventa, ENTONCES
  **404** `obra_sin_unidades`; SI las unidades leídas pertenecen a **más de una
  obra** distinta, ENTONCES **409** `obra_ambigua`; SI una de las lecturas llega
  al techo de filas pedido, ENTONCES **409** `catalogo_sin_verificar`. En los
  tres casos, sin fichero.
- **R11** · SI Sigrid no responde, la configuración de `sigrid-api` está
  incompleta, el entorno no es `dev` ni `pro` o la base no responde, ENTONCES
  **503** con el motivo, sin fichero.

  > **Enmienda del 2026-09-28.** Se añade «o la base no responde»: la plantilla
  > lee ahora los grupos de proveedores confirmados (R82).

- **R12** · SI la obra no tiene ningún oficio, ENTONCES la plantilla se genera
  igual, con las columnas `Oficio` y `Proveedor` sin opciones y una línea en
  «Instrucciones» que diga que se dejen en blanco.
- **R13** · Los oficios dados de baja (`auxofc.fecbaj` distinto de 0) no entran
  en el desplegable (D-8).

## 2 · Reconocer el fichero antes de leer una fila

- **R14** · CUANDO llega `POST /api/importaciones` (`multipart/form-data` con
  **un** fichero y el campo `usuario_oid`), el sistema debe reconocer la
  plantilla **antes** de validar ninguna fila.
- **R15** · SI el fichero pasa de **2 MiB**, ENTONCES **413** sin abrirlo.
- **R16** · SI el fichero no es un `.xlsx` —no empieza por la firma de un ZIP,
  no se puede abrir, trae macros (`xl/vbaProject.bin`), o sus partes
  descomprimidas pasan de **20 MiB** o de **500** entradas—, ENTONCES **400** con
  el código `no_es_xlsx`, `contiene_macros` o `fichero_sospechoso`.

  > **Séptima enmienda del 2026-10-01 (review 3, R3-1).** A esta lista se
  > añade el **presupuesto de elementos XML** de R117: por encima,
  > `fichero_sospechoso`. El tope de 20 MiB descomprimidos no acotaba el coste,
  > porque caben 4 millones de elementos en 20 MiB y `openpyxl` gasta por
  > elemento hasta ~600 B y 20–25 µs.

  > **Octava enmienda del 2026-10-01.** El tope de **20 MiB** descomprimidos
  > pasa a **el doble de lo que ocupe descomprimido el fichero legítimo más
  > grande** —la plantilla completa (1000 filas, detalle de 2000) o el Excel de
  > errores más grande (1000 filas con error en las 8 columnas, con el VML de
  > los comentarios)—, **medido** en T41, redondeado hacia arriba al MiB, y
  > fijado como constante con la medición pegada en el informe. El código de
  > error no cambia (`fichero_sospechoso`).

- **R17** · SI el fichero no tiene la hoja de metadatos o su identificador no es
  el de la plantilla, ENTONCES **400** `no_es_la_plantilla`; y SI además tiene
  la forma del formato antiguo (primera hoja sin cabecera reconocible, texto en
  la columna A de la primera fila y vacía debajo, texto en D y E), ENTONCES
  **400** `formato_antiguo`, con un mensaje que diga que ese formato ya no se
  admite y que hay que descargar la plantilla de la obra desde el portal.
- **R18** · SI la versión de la plantilla no está entre las soportadas (`{1}`),
  ENTONCES **400** `version_no_soportada`.
- **R19** · SI la cabecera de «Incidencias» no coincide exactamente con la de
  R2 (tras recortar espacios), ENTONCES **400** `cabecera_distinta` diciendo
  **qué** columna falta, sobra o está movida.
- **R20** · SI hay más de **1000** filas con datos, ENTONCES **400**
  `demasiadas_filas`.

  > **Sexta enmienda del 2026-09-30.** Con el tope de recorrido de R115,
  > «más de 1000 filas con datos» pasa a leerse como «algún dato por debajo de
  > la fila 1001», que es donde acaba la plantilla: 900 filas con datos
  > repartidas hasta la 1500 también son `demasiadas_filas`. El error y su
  > mensaje no cambian.
  >
  > **Errata corregida el 2026-09-30 (sexta enmienda bis, review 2, R2-3).**
  > «El error y su mensaje no cambian» no es exacto: el **código** no cambia
  > (`demasiadas_filas`) y, con más de 1000 filas leídas, el mensaje tampoco;
  > pero en el **caso nuevo** —datos por debajo de la fila 1001 con menos de
  > 1000 filas— el mensaje es otro, sin la cuenta, porque la cuenta sería
  > falsa: «El fichero trae datos por debajo de la fila 1001 y el máximo es
  > 1000. Pártelo en varios ficheros.» (B10-2).
- **R21** · En todos los casos de R15–R20 el sistema **no** debe llamar a Sigrid
  ni escribir en la base, y el fichero se rechaza **entero**: no hay Excel de
  errores.

  > **Enmienda del 2026-09-28.** Se añade la última frase (decisión 6): la
  > importación parcial es de **filas**, no de ficheros que no son la plantilla.

- **R22** · SI falta `usuario_oid`, llega vacío o no es un texto de hasta 128
  caracteres, ENTONCES **400** sin abrir el fichero.

## 3 · Validar fila a fila

- **R23** · Una fila con todas sus celdas vacías —sin contar `Errores`— se
  ignora y no cuenta como leída.
- **R24** · Cada error de fila debe decir el **número de fila de Excel** (la
  cabecera es la 1), el **nombre de la columna** y el problema, en español.
- **R25** · SI `Unidad` está vacía en una fila con datos, ENTONCES error «falta
  la unidad; en esta plantilla no se hereda de la fila de arriba».
- **R26** · La `Unidad` debe ser, **exactamente** y sin normalizar, una etiqueta
  del catálogo de la obra **leído de Sigrid en esa importación**; SI no lo es,
  ENTONCES error diciendo que ese valor no está en la lista, que se elija del
  desplegable (cuidado con mayúsculas, tildes y espacios) y que puede ser una
  plantilla antigua.

  > **Enmienda del 2026-09-28.** Decía «comparando normalizado: sin tildes,
  > mayúsculas ni espacios de más». Decisión 7: no hay casado aproximado. Excel
  > compara las listas sin distinguir mayúsculas al teclear, así que un valor
  > tecleado puede pasar el desplegable y fallar aquí: por eso el mensaje lo
  > explica.

- **R27** · `Descripción corta` es obligatoria: los saltos de línea pasan a
  espacio y los espacios se colapsan; SI queda vacía o pasa de **128**
  caracteres, ENTONCES error con la longitud y el tope.
- **R28** · `Detalle` es opcional; SI pasa de **2000** caracteres, ENTONCES
  error. Conserva sus saltos de línea.
- **R29** · `Ubicación` es opcional; SI viene, debe ser **exactamente** una
  etiqueta de la lista cerrada; SI no, ENTONCES error.
- **R30** · `Oficio` es opcional; SI viene, debe ser **exactamente** la
  etiqueta de un grupo de oficios de la obra (R92), y se guarda según R93; SI
  no, ENTONCES error.

  > **Segunda enmienda del 2026-09-28.** Decía «una etiqueta de los oficios de
  > la obra del catálogo de Sigrid, y se guarda su código».
- **R31** · `Urgencia` y `Listado` son opcionales y deben ser **exactamente** una
  etiqueta de su lista; SI no, ENTONCES error. Vacío en `Urgencia` significa
  «normal».

  > **Enmienda del 2026-09-28 (R29–R31).** Decían «debe casar» y R29 guardaba
  > «su etiqueta canónica», que presuponía casado normalizado. Ahora la
  > comparación es exacta (decisión 7).

- **R32** · SI una celda lleva una fórmula, ENTONCES error «la celda lleva una
  fórmula: escribe el texto». Un número en `Descripción corta` o `Detalle` se
  toma como texto; una fecha o un booleano en cualquier columna es error; y en
  una columna tasada, cualquier valor que no sea texto es error.
- **R33** · SI una fila tiene algún error, ENTONCES esa fila **no** entra en la
  bandeja y va al Excel de errores (R62); las filas sin error **sí** entran. La
  respuesta es **200** y lleva todos los errores (hasta 200 en la lista, más el
  total).

  > **Enmienda del 2026-09-28.** Decía: «SI alguna fila tiene algún error,
  > ENTONCES **422** con todos los errores […] y **no se escribe nada**: la
  > importación es todo o nada (D-6)». El humano cambió D-6 (decisión 6).

- **R34** · El sistema debe devolver, por fila y **sin bloquear**, un aviso
  cuando la descripción o el detalle mencionan peligro, seguridad o urgencia con
  `Urgencia` vacía, y cuando la descripción corta va mayoritariamente en
  mayúsculas.

## 4 · Duplicados y bandeja

- **R35** · La clave de duplicado debe ser el `sha256` (hexadecimal) de obra,
  código de unidad, ubicación y descripción corta, las dos últimas
  **normalizadas** (sin diacríticos, en minúsculas, espacios colapsados y sin
  puntuación al final). *Esta normalización es solo para la clave; no casa
  valores tasados.*
- **R36** · La misma descripción con **distinta ubicación no es duplicado**
  (caso real: «Miras de hierro…» en cinco ubicaciones de la muestra).
- **R37** · Dentro de un mismo fichero, la segunda y siguientes filas **sin
  error** con la misma clave deben guardarse marcadas como **duplicadas de la
  primera** (`duplicada_de`).
- **R38** · SI la clave ya existe en la bandeja **de esa obra** (en cualquier
  fila), ENTONCES ninguna fila del fichero con esa clave se guarda y cada una se
  informa `ya_en_bandeja` con el identificador de la existente.
- **R39** · CUANDO el fichero, byte a byte (`sha256`), ya consta en una
  importación **completa** (sin filas con error), el sistema debe responder
  **200** con `ya_importado: true` y el resumen de entonces, **sin escribir
  nada** y sin llamar a Sigrid. SI solo consta en importaciones **parciales**,
  ENTONCES el fichero se procesa de nuevo: sus filas buenas salen
  `ya_en_bandeja` y el Excel de errores se vuelve a generar.

  > **Enmienda del 2026-09-28.** Decía solo la primera frase, sin distinguir
  > completa de parcial. El Excel de errores **no se guarda** (R68): si se
  > pierde, volver a subir el mismo fichero tiene que devolverlo.

- **R40** · La importación —su registro y todas sus filas buenas— debe
  escribirse en **una transacción**; SI la base falla, ENTONCES **503** y no
  queda nada a medias.
- **R41** · La no duplicación la debe garantizar **la base** (índice único
  parcial por obra y clave) y no una consulta previa: dos importaciones
  simultáneas del mismo contenido no dejan dos filas no duplicadas con la misma
  clave.
- **R42** · De cada importación se guarda quién (`oid` opaco de Entra, nunca
  correo ni nombre), cuándo, el nombre del fichero, su `sha256`, la obra, la
  versión de la plantilla, los recuentos —incluidas las filas con error— y si
  fue **completa** o **parcial**. **No** se guardan los textos de las filas con
  error ni el Excel de errores.

  > **Enmienda del 2026-09-28.** Se añaden `filas_con_error`, el estado
  > completa/parcial y la última frase.

- **R43** · La respuesta **200** debe llevar `importacion_id`, `obra`,
  `ya_importado`, `estado ∈ {completa, parcial}`, `resumen {leidas, nuevas,
  duplicadas_en_fichero, ya_en_bandeja, con_error}`, por fila `{fila, estado,
  incidencia_id, duplicada_de_fila | existente_id, avisos}` con `estado ∈
  {nueva, duplicada_en_fichero, ya_en_bandeja, con_error}`, `errores[]`
  `{fila, columna, problema}` y, SI hay alguna fila con error,
  `excel_errores {nombre, contenido_b64}`.

  > **Enmienda del 2026-09-28.** Se añaden `estado`, `con_error`, `errores` y
  > `excel_errores`.

- **R44** · Una fila de la bandeja **no** lleva estado de revisión: eso es de
  F-038.

## 5 · Ver la bandeja (lo mínimo)

- **R45** · CUANDO llega `GET /api/bandeja?obra=<código>[&limite=N]`, el sistema
  debe devolver las incidencias de esa obra, las de la importación más reciente
  primero y en orden de fila, con un tope duro de **500** (por defecto 200);
  **400** si falta la obra o `limite` no es un entero ≥ 1, **503** sin base.
  Solo lee.

## 6 · Límites y seguridad

- **R46** · Nada de F-036 escribe en Sigrid: ningún fichero nuevo o modificado
  por F-036 nombra `sql/write`, `sigrid/partes-reclamacion` ni
  `sigrid/concepto-grafico`, y el adaptador del catálogo solo usa
  `POST /api/sql/read`.
- **R47** · Los logs de F-036 solo llevan código de obra, recuentos,
  `importacion_id` y códigos de motivo: **nunca** la descripción, el detalle, el
  nombre del fichero, el `oid`, el nombre de una unidad ni el nombre o el código
  de un proveedor.

  > **Enmienda del 2026-09-28.** Se añade el proveedor (hay autónomos con
  > nombre de persona).

- **R48** · La lectura del catálogo en Sigrid debe exigir `ENTORNO` en `dev` o
  `pro` (la misma lista que el resto del proyecto) y **no** depende de
  `CIERRE_HABILITADO` ni de `ARCHIVO_HABILITADO`.
- **R49** · Los endpoints nuevos no añaden ninguna variable de entorno.

## 7 · El front

- **R50** · La página de importación debe permitir: escribir un código de obra y
  descargar su plantilla; elegir un `.xlsx` e importarlo; ver el resumen, los
  errores por fila y columna, los avisos o el motivo del rechazo; **descargar el
  Excel de errores** cuando lo haya; y ver la bandeja de la obra en solo
  lectura, con las duplicadas marcadas.

  > **Enmienda del 2026-09-28.** Se añade la descarga del Excel de errores.

- **R51** · La página principal del front de `dev` debe enlazar a la de
  importación y a la de oficios repetidos, `oficios.html` (D-1). *(Segunda
  enmienda del 2026-09-28: decía «a la de proveedores repetidos»; cuarta:
  `catalogos.html`; quinta, 2026-09-29: `oficios.html`.)*
- **R52** · CUANDO el backend responde 400, 413, 409 o 503, el front debe enseñar
  el mensaje del backend, sin reintentar la importación por su cuenta.

  > **Enmienda del 2026-09-28.** Se quita el 422, que ya no existe (R33).

## 8 · La migración del Excel actual

- **R53** · El script de migración debe leer el original **sin modificarlo**
  (`sha256` igual antes y después) y negarse SI la salida es la misma ruta que el
  original o SI la salida ya existe y no se ha pedido sobrescribir.
- **R54** · El script debe comprobar que el original corresponde a la tabla de
  correcciones —cada fila del original aparece **exactamente una vez**, con su
  ubicación y su texto originales— y parar sin escribir nada SI no corresponde.
- **R55** · El `v2` debe producirse con **el mismo generador** que la plantilla
  del portal (R2–R8) y el catálogo de la obra leído de Sigrid (tarea T2).
- **R56** · El script debe pasar el `v2` que acaba de escribir por el lector y
  la validación del importador y exigir **cero errores**.
- **R57** · Contenido del `v2`: ninguna descripción corta pasa de 128; ninguna
  descripción ni detalle lleva «PELIGRO DE SEGURIDAD» (pasa a `Urgencia`);
  todas las ubicaciones son de la lista cerrada; las filas con dos defectos
  quedan separadas; ninguna fila remite a otra («como en los otros baños»); y
  cada fila del original que se descarte lleva su motivo.
- **R58** · El script debe escribir un informe de revisión —cada fila original
  frente a su propuesta, con el motivo de cada cambio y marcado lo que es
  propuesta (p. ej. un oficio completado)— sin datos personales (**sin nombres
  de proveedor**).

  > **Sexta enmienda del 2026-09-30.** «Sin datos personales» incluye **los
  > códigos** de proveedor: el de un autónomo lleva a su nombre en cuanto se
  > mira Sigrid (`design.md` §12, riesgo 14). Lo precisa R116.
- **R59** · Ningún `.xlsx` entra en git: ni la plantilla, ni el original, ni el
  `v2`, ni el Excel de errores, ni fixtures de tests (los tests construyen sus
  libros en memoria).
- **R91** · En el `v2`, `Proveedor` queda **vacío** salvo en las filas cuyo
  grupo de oficio tenga en la 0677 **un solo** grupo de proveedores y ese par
  resuelva a **un solo** código de oficio y **un solo** código de proveedor
  (R94); esas se rellenan y se marcan como propuesta en el informe.

  > **Segunda enmienda del 2026-09-28.** Decía «cuyo oficio tenga en la 0677 un
  > solo grupo de proveedores y ese grupo un solo código para ese oficio»: el
  > oficio es ahora un grupo.

- **R97** · Los oficios de la tabla de correcciones de la migración son
  **nombres exactos** de oficios de Sigrid (`auxofc.res`, como en la muestra:
  «Mamparas», «Mobiliario cocina»…). El script los resuelve a su código, y el
  código a su **grupo vigente** según un fichero de grupos confirmados
  descargado del entorno desplegado (R98); en el `v2` escribe la etiqueta del
  grupo. SI un nombre no es exactamente el de un oficio de la obra **ni el de
  ningún oficio del catálogo completo de Sigrid** (`oficios_catalogo`, todo
  `auxofc`), ENTONCES el script para: es una errata o una variante de la
  tabla de correcciones y se corrige en la tabla. SI es el nombre de varios
  oficios de la obra, ENTONCES también para. SI es el de un oficio de Sigrid
  que ya no está en la obra, R128. SI no recibe el fichero de grupos,
  ENTONCES solo admite el modo `--solo-informe` (cada código, su propio
  grupo).

  > **Undécima enmienda del 2026-10-03.** Decía «SI un nombre no es
  > exactamente el de un oficio de la obra, ENTONCES el script para», sin
  > distinguir la errata del oficio que ha salido de la obra en Sigrid. **La
  > errata sigue parando** porque es un fallo de la tabla que el humano
  > aprobó nombre a nombre en T25: dejarla vacía la escondería en un
  > recuento y perdería un oficio que sí está en la obra. Un oficio que ha
  > salido de la obra, en cambio, es un hecho de Sigrid, sin nada que
  > corregir en la tabla. El mensaje de la parada cambia (`design.md`
  > §10.5).

## 9 · Documentación

- **R60** · `docs/INTEGRACION.md` y su copia `azure-apps/postventa_incidencias.md`
  deben describir las lecturas nuevas de `sigrid-api`, las tablas nuevas, los
  endpoints nuevos y el texto libre de la propiedad y los nombres de proveedor
  como datos que no salen en logs.
- **R61** · `docs/ARCHITECTURE.md` debe describir la vía de entrada (plantilla →
  importación → bandeja, con el Excel de errores) y la agrupación de oficios y
  proveedores, y lo que no hacen. *(Segunda enmienda del 2026-09-28: decía «la
  agrupación de proveedores».)*

## 10 · El Excel de errores (añadido el 2026-09-28)

- **R62** · CUANDO una importación tiene alguna fila con error, el sistema debe
  generar un Excel de errores con **el mismo generador** que la plantilla, **el
  mismo catálogo** leído en esa importación, los mismos metadatos (identificador,
  versión y obra) y **solo** las filas con error, en su orden original.
- **R63** · Cada fila del Excel de errores debe llevar los valores **tal como
  llegaron** (una fórmula, como su texto; R7), y en la columna `Errores` todos
  sus problemas con el número de fila del fichero subido: «Fila 7 del fichero
  subido · Unidad: … · Oficio: …».
- **R64** · Cada celda con error debe ir **marcada**: relleno de color y un
  comentario con su problema.

  > **Décima enmienda del 2026-10-02.** El requisito no cambia: nunca fijó el
  > color. El naranja (`FFF4B084`) solo estaba en el código (`RELLENO_ERROR`)
  > y ningún test lo comprobaba; pasa al rojo suave de R123, que además pone
  > el texto en rojo. El comentario, su tamaño y su autor no cambian.
- **R65** · El Excel de errores se llama
  `incidencias_<obra>_errores_<AAAAMMDD-HHMM>.xlsx` (UTC) y viaja en la
  respuesta como `excel_errores {nombre, contenido_b64}`.
- **R66** · CUANDO se sube un Excel de errores corregido, el sistema debe
  tratarlo como cualquier plantilla: se reconoce, se valida y el contenido de la
  columna `Errores` se **ignora**.
- **R67** · SI en el Excel de errores corregido alguna fila coincide por clave
  con una ya importada, ENTONCES sale `ya_en_bandeja` (R38): corregir y volver a
  subir, o volver a subir el fichero completo, no duplica.
- **R68** · El Excel de errores **no** se guarda en ningún sitio del servidor;
  si se pierde, se recupera subiendo otra vez el mismo fichero (R39).
- **R69** · CUANDO no hay filas con error, la respuesta no lleva
  `excel_errores` y la importación consta **completa**.
- **R70** · Una importación en la que **todas** las filas tienen error consta
  **parcial** con 0 nuevas y devuelve el Excel de errores con todas.

## 11 · La columna `Proveedor` (añadido el 2026-09-28)

- **R71** · Las opciones de `Proveedor` deben ser los pares `<oficio> ·
  <proveedor>` de **esa obra**: una opción por cada combinación de **grupo de
  oficios** y **grupo de proveedores** para la que exista alguna fila de
  `obrofc` de la obra con un oficio del primero y un proveedor del segundo,
  ordenadas por oficio y proveedor, **sin fórmulas** (D-16).

  > **Segunda enmienda del 2026-09-28.** Decía «cada combinación de oficio de
  > `obrofc` y grupo de proveedores»: el oficio del par es ahora también un
  > grupo, y su etiqueta es la del desplegable de `Oficio` (R92).

  > **Tercera enmienda del 2026-09-28.** La condición «exista alguna fila de
  > `obrofc` de la obra con un oficio del primero y un proveedor del segundo»
  > se sustituye por R101: el par se ofrece si algún proveedor del grupo
  > —que tiene que ser de la obra— **cubre** algún oficio del grupo por sus
  > familias (R100).

  > **Quinta enmienda del 2026-09-29.** Vuelve la condición original: el par
  > se ofrece si existe una fila de `obrofc` de la obra con un oficio del grupo
  > y **ese** proveedor (R101 sale a F-039 con las actividades). Como los
  > proveedores ya no se agrupan (F-050), el segundo término del par es **un
  > proveedor**, no un grupo. Una fila de `obrofc` sin proveedor no da ningún
  > par.

- **R72** · La etiqueta del proveedor dentro del par es su nombre (`con.res`);
  SI dos proveedores dan el mismo nombre para el mismo grupo de oficio, ENTONCES
  cada uno lleva su código entre paréntesis.

  > **Quinta enmienda del 2026-09-29.** Decía «la del grupo (R86)»: sin
  > agrupación de proveedores (F-050), cada proveedor es su propia opción.
- **R73** · `Proveedor` es opcional; SI viene, debe ser **exactamente** una
  opción; SI no, ENTONCES error.
- **R74** · SI `Proveedor` viene y `Oficio` también, ENTONCES el grupo de oficio
  del par debe ser el de `Oficio`; SI no lo es, ENTONCES error «ese proveedor no
  está dado de alta en la obra para ese oficio». SI `Oficio` viene vacío,
  ENTONCES se toma el grupo de oficio del par (D-17).

  > **Segunda enmienda del 2026-09-28.** Decía «el oficio del par debe ser el de
  > `Oficio`».

- **R75** · El proveedor se resuelve con R94. CUANDO resuelve a **un solo**
  código, la bandeja guarda ese código; CUANDO a **más de uno**, la bandeja
  guarda el proveedor **sin código**, marcado `proveedor_ambiguo`, con un aviso
  en la fila, y el código se elige en la bandeja (D-19). El sistema nunca elige
  solo entre varios códigos.

  > **Quinta enmienda del 2026-09-29.** Sin agrupación de proveedores, el par
  > trae **un** código de proveedor y siempre resuelve a él: en F-036
  > `proveedor_ambiguo` no puede darse; la columna se queda para F-050.

  > **Segunda enmienda del 2026-09-28.** Decía «CUANDO el grupo elegido tiene
  > un solo código en `obrofc` de la obra para ese oficio»: con oficios
  > agrupados, «ese oficio» puede ser varios códigos, y la resolución conjunta
  > es R94.

- **R76** · SI `Proveedor` viene vacío, ENTONCES la bandeja guarda la fila sin
  proveedor y **no** propone ninguno (eso es F-039).
- **R77** · La clave de duplicado **no** incluye ni el proveedor ni el oficio.

## 12 · Catálogos casi duplicados de Sigrid: oficios y proveedores (añadido el 2026-09-28)

> **Segunda enmienda del 2026-09-28.** Esta sección se llamaba «Proveedores
> casi duplicados del maestro de Sigrid» y valía solo para proveedores. Ahora
> es **un solo mecanismo para los dos catálogos** (decisión 10). Cambian R78,
> R81, R83, R84, R86–R89, cada uno con lo que decía; R79, R80, R82 y R85 valen
> tal cual para los dos catálogos, y R90 sigue siendo solo de proveedores.

> **Quinta enmienda del 2026-09-29 · un solo catálogo, `oficio`.** La
> agrupación de proveedores sale a F-050 (decisión 13). Esta sección vale
> ahora **solo para oficios**: lo que en R78 es de proveedores (`mismo_cif`,
> formas jurídicas), R90 entero y la parte de proveedores de R96 pasan a
> F-050. R81–R86 y R95 siguen valiendo tal cual —el discriminador `catalogo`
> es la costura—; R87–R89 se ajustan abajo. La propuesta de oficios gana las
> palabras vacías y el motivo `incluido` (`design.md` §15.2, D-22).

- **R78** · El sistema debe proponer, para los oficios de una obra y para sus
  proveedores —cada catálogo por separado, nunca mezclados—, grupos de códigos
  que **podrían** ser el mismo oficio o la misma empresa, con el motivo de cada
  par: `mismo_nombre` (iguales tras quitar mayúsculas, tildes y puntuación),
  `plural` (iguales pasando cada palabra a singular) y `errata` (distancia de
  edición ≤ 2 y ≤ 10 % de la longitud, en nombres de al menos 8 caracteres). En
  **proveedores**, además, `mismo_cif` (el mismo CIF/NIF, comparado en Sigrid y
  sin que el valor salga de la lectura) y `mismo_nombre` quita también la forma
  jurídica (`S.L.`, `SL`, `S.L.U.`, `S.A.`, `C.B.`…) (R96).

  > **Segunda enmienda del 2026-09-28.** Decía «para los proveedores de una
  > obra, grupos de códigos que podrían ser la misma empresa», con los cuatro
  > motivos para todos.

- **R79** · SI un conjunto de códigos está conectado por parecidos pero no todos
  sus pares se parecen entre sí, ENTONCES se propone **por pares** y no como un
  grupo (ante la duda, separadas).
- **R80** · Ningún grupo se aplica sin que una persona lo confirme: la propuesta
  sola no cambia la plantilla ni la importación.
- **R81** · CUANDO una persona confirma que varios códigos de un catálogo son el
  mismo oficio o la misma empresa, o que dos no lo son, el sistema debe guardar
  la decisión **por pares**, con su catálogo, quién (`oid`) y cuándo, en el
  schema `postventa`, en **una sola** tabla **append-only** para los dos
  catálogos donde manda la última decisión de cada par (R95). Una decisión
  «distinto» sobre un par confirmado lo separa.

  > **Segunda enmienda del 2026-09-28.** Decía «que varios códigos son la misma
  > empresa», sin catálogo.

- **R82** · Los grupos vigentes son las componentes conexas de los pares cuya
  última decisión es «mismo»; SI una componente contiene un par cuya última
  decisión es «distinto», ENTONCES esa componente **no** se aplica (cada código
  vuelve a ser su propio grupo) y la pantalla de catálogos lo avisa.
- **R83** · La tabla de equivalencias **no** guarda nombres: solo el catálogo,
  los códigos de Sigrid, el `oid` de quien decide, la fecha, la decisión, los
  motivos propuestos y la obra desde la que se decidió. Los nombres se leen de
  Sigrid cada vez.

  > **Segunda enmienda del 2026-09-28.** Decía «solo códigos de proveedor».

- **R84** · Una equivalencia confirmada vale para **todas** las obras (es una
  verdad sobre el catálogo de Sigrid, no sobre una obra).
- **R85** · Un par ya decidido no se vuelve a proponer.
- **R86** · La etiqueta de un grupo —de oficios o de proveedores— es el nombre
  del miembro con más filas en `obrofc` de la obra; a igualdad, el de código
  menor.

  > **Segunda enmienda del 2026-09-28.** Se añade «de oficios o de
  > proveedores».

- **R87** · CUANDO llega `GET /api/catalogos/propuestas?obra=`, el sistema debe
  devolver, **para el catálogo `oficio`** *(quinta enmienda: decía «por catálogo
  (`oficio` y `proveedor`)»)*, los códigos de la obra
  con su grupo vigente, las propuestas pendientes con sus motivos y los avisos
  de R82; **400** obra inválida, 404/409 como R10, **503** sin Sigrid o sin
  base.
- **R88** · CUANDO llega `POST /api/catalogos/decisiones` con `obra`,
  `usuario_oid`, `confirmado: true` (booleano de JSON) y una lista de decisiones
  `{catalogo: "oficio" | "proveedor", codigos: [≥ 2], decision: "mismo" |
  "distinto"}` (`distinto`, con dos exactamente), el sistema debe comprobar que
  **todos** los códigos de cada decisión son de ese catálogo en `obrofc` de la
  obra indicada y guardar todos los pares en una transacción; **400** si el
  cuerpo no cumple, **409** si algún código no es de la obra, sin guardar nada.
  *(Quinta enmienda del 2026-09-29: en F-036 solo se admite `catalogo:
  "oficio"`; cualquier otro es **400** «catálogo no disponible en esta
  versión». F-050 abrirá `"proveedor"`.)*

  > **Segunda enmienda del 2026-09-28 (R87, R88).** Las rutas eran
  > `/api/proveedores/propuestas` y `/api/proveedores/decisiones`, y ni la
  > respuesta ni las decisiones llevaban catálogo.

- **R89** · La pantalla de oficios repetidos (`oficios.html`; quinta enmienda:
  era `catalogos.html` con dos apartados, Oficios y Proveedores) enseña
  cada propuesta de oficios con los nombres, los
  códigos y los motivos, y dos botones —«Son el mismo» y «Son distintos»—; los
  grupos vigentes, con «Separar». Nada se decide sin pulsar.

  > **Segunda enmienda del 2026-09-28.** Decía «la pantalla de proveedores», con
  > los botones «Son la misma empresa» y «Son distintas».

- ~~**R90**~~ · **Sale a F-050 (quinta enmienda, 2026-09-29).** Decía: la lectura de Sigrid de los proveedores **no** saca de la lectura el
  CIF/NIF: solo una marca opaca, válida dentro de esa respuesta, que dice qué
  códigos comparten el mismo.

## 13 · Los oficios agrupados en la plantilla y la importación (añadido en la segunda enmienda del 2026-09-28)

- **R92** · Las opciones de `Oficio` deben ser **una por grupo vigente de
  oficios** de la obra (sus oficios de `obrofc`, sin los de baja, R13), con la
  etiqueta de R86; SI dos grupos dan la misma etiqueta, ENTONCES cada una lleva
  sus códigos entre paréntesis. Sin grupos confirmados, cada código es su
  propio grupo y el desplegable queda como antes.
- **R93** · CUANDO la fila trae `Oficio` y no trae `Proveedor`: SI el grupo tiene
  **un solo** código en `obrofc` de la obra, ENTONCES la bandeja guarda ese
  código; SI tiene **más de uno**, ENTONCES guarda el oficio **sin código**,
  marcado `oficio_ambiguo`, con un aviso en la fila, y el código se elige en la
  bandeja (D-19). El sistema nunca elige solo.
- **R94** · CUANDO la fila trae `Proveedor`, el sistema debe tomar las filas de
  `obrofc` de la obra cuyo oficio es del grupo de oficio del par y cuyo
  proveedor es del grupo de proveedor del par, y: SI todas tienen **el mismo**
  código de oficio, ENTONCES el oficio queda resuelto (aunque R93 lo hubiera
  dejado ambiguo); SI todas tienen **el mismo** código de proveedor, ENTONCES el
  proveedor queda resuelto; lo que no quede resuelto va marcado
  `oficio_ambiguo` o `proveedor_ambiguo`. Así el oficio y el proveedor que se
  guardan forman **una fila real de `obrofc`**, que es lo que §8.9 exige a un
  interviniente.

  > **Tercera enmienda del 2026-09-28.** R94 sigue valiendo cuando **hay**
  > filas de `obrofc` para el par (caso A de R104). Cuando el par se ofrece
  > por familia y no hay ninguna (caso B), manda R104.

  > **Quinta enmienda del 2026-09-29.** Sale el caso B (a F-039): todo par
  > sale de `obrofc`, así que R94 vale siempre. Y como el proveedor del par es
  > **un** código (sin grupos, F-050), «el mismo código de proveedor» se cumple
  > siempre: lo único que puede quedar ambiguo es el oficio.
- **R95** · Las decisiones de los dos catálogos van a **la misma** tabla, con un
  discriminador `catalogo ∈ {oficio, proveedor}`; un par se identifica por
  (`catalogo`, `codigo_a`, `codigo_b`), y un código de oficio y otro de
  proveedor que se escriban igual nunca se confunden.
- **R96** · Las reglas de similitud reciben el **perfil** del catálogo, para
  que F-050 añada el suyo (con `mismo_cif` y las formas jurídicas) sin tocar
  las funciones. *(Quinta enmienda del 2026-09-29: decía «las mismas
  funciones para los dos catálogos; `mismo_cif` y formas jurídicas, solo en
  proveedores».)*
- **R98** · La pantalla de oficios debe permitir descargar los **grupos
  vigentes** de oficio de la obra como un JSON **solo con códigos**, que es lo
  que usa la migración (R97). *(Quinta enmienda: decía «la pantalla de
  catálogos» y «por catálogo».)*
- **R99** · Una fila de la bandeja con `oficio_ambiguo` no lleva código de
  oficio y sí su nombre; con `proveedor_ambiguo`, no lleva código de proveedor
  y sí su nombre; y no hay proveedor sin oficio.

## 14 · El oficio del proveedor, por sus actividades — RETIRADA de F-036 el 2026-09-29

> **Quinta enmienda del 2026-09-29 · PARADA T3, opción A.** Toda esta sección
> sale de F-036 y **pasa a F-039**, donde ya está anotada en su ficha de
> `harness/features.json`: R100–R108, R110, R112–R114 **no aplican** a F-036.
> En F-036 la relación oficio ↔ proveedor sale solo de `obrofc` (decisión
> 12). **R109** (la medición) y **R111** (UTF-8 sin doble codificación) quedan
> **cumplidos** por T1/T2 (T2 repetida el 2026-09-29, PASA, con las tildes
> bien). El texto se conserva abajo, tachado en su título, como punto de
> partida de F-039.

### (Texto retirado)

> **Cuarta enmienda del 2026-09-28 · la medición desmiente la tercera.** Esta
> sección se titulaba «El oficio del proveedor, por sus familias» y leía las
> familias de `confam` → `auxfam`, con una correspondencia familia → oficio que
> podía ser la identidad de códigos o una tabla `familia_oficio`, y medía
> además `entfam` y `prv.ofcide`. T2 (`progress/explore_F-036.md`) midió
> `confam`, `auxfam` y `entfam` **vacías** para la obra y para los 526
> proveedores de `obrofc`, y `prv.ofcide` relleno en 3 de 526. Lo que el
> humano llama «familias» son las **actividades** del proveedor: `conact`
> (`conide`, `actide` → `auxpronat`, `homolo`, `tip*`) sobre el catálogo **en
> árbol** `auxpronat` («Naturalezas de Productos / Actividades»), que es la caja
> «Naturaleza de productos, servicios y/o actividades…» de la pestaña Datos
> fiscales de la ficha (correo del director de Compras). Su vocabulario es
> otro que el de `auxofc`. Cambian R100, R102, R103, R104 (solo el nombre), R107,
> R108 y R109; nuevos R111–R114. R101, R105, R106 y R110 siguen valiendo con
> «actividad» donde decían «familia». El texto de antes no se conserva línea a
> línea: se conserva su resumen en este recuadro.

> Lo que exige Sigrid y no cambia: §8.9 resuelve cada interviniente
> `{oficio, proveedor}` contra `obrofc` de la obra y rechaza el parte con
> `interviniente_no_esta_en_la_obra` si esa pareja no está, y con
> `oficio_no_esta_en_la_obra` si el oficio del parte no está en la obra.
> F-036 no toca `sigrid-api` (R46); lo que no cabe en §8.9 se marca, no se
> fuerza.

- **R100** · Los oficios que **cubre** un proveedor de la obra deben salir de
  sus **actividades** —`conact` (`conide` = el proveedor) → `auxpronat`, sin
  actividades dadas de baja— llevadas a oficios por la **correspondencia
  actividad → oficio** de R102 con la herencia de R112, y quedarse con los
  oficios **de la obra**. SI el proveedor no tiene ninguna actividad **con
  correspondencia confirmada**, ENTONCES cubre los oficios con los que figura
  en `obrofc` de la obra (D-25, R114).
- **R101** · El par `<grupo de oficio> · <grupo de proveedor>` se ofrece en
  `Proveedor` SI algún código del grupo de proveedor está en `obrofc` de la
  obra (con cualquier oficio) Y cubre (R100) algún código del grupo de oficio.
  Solo se ofrecen proveedores **de la obra**. Una fila de `obrofc` **sin
  proveedor** cuenta como oficio de la obra pero no da ningún par.
- **R102** · La correspondencia actividad → oficio debe ser una tabla de **pares
  actividad–oficio confirmados por una persona**, con el **mismo** mecanismo de
  §12 —decisiones por pares, append-only, en la misma tabla— como el catálogo
  `actividad_oficio` en modo correspondencia (pares cruzados, nunca grupos). La
  propuesta automática (motivos `mismo_codigo`, `mismo_nombre`, `plural`,
  `errata`, `incluido`) es una ayuda; como los vocabularios son distintos, la
  pantalla debe permitir además **crear el par a mano** (R113). La identidad de
  códigos queda descartada salvo que T1 la demuestre (D-28).
- **R103** · Sin correspondencia confirmada, una actividad **no** aporta ningún
  oficio. La propuesta sola no cambia la plantilla ni la importación (como
  R80).
- **R104** · CUANDO la fila trae `Proveedor`, el sistema debe distinguir:
  - **caso A** · hay filas de `obrofc` de la obra con un oficio del grupo de
    oficio y un proveedor del grupo de proveedor → se resuelve con R94;
  - **caso B** · no hay ninguna (el par se ofreció por actividad, R101) → el
    oficio se resuelve con R93; el proveedor, entre los códigos del grupo que
    son de la obra y cubren el oficio por actividad (uno → ese código; varios
    → `proveedor_ambiguo`); y la fila queda marcada
    **`proveedor_fuera_de_obrofc`** con un aviso: «este proveedor cubre el
    oficio por sus actividades, pero en la obra no está dado de alta con él;
    para volcarlo como interviniente hay que darlo de alta en Sigrid o elegir
    otro» (D-26).
- **R105** · La bandeja debe guardar `proveedor_fuera_de_obrofc` (booleano, por
  omisión falso), y **solo** puede ser verdadero en una fila con proveedor.
- **R106** · `GET /api/bandeja` debe devolver `proveedor_fuera_de_obrofc`, y la
  documentación de la bandeja (`docs/INTEGRACION.md`, `design.md` §11) debe decir
  que **F-040 no manda como interviniente** una fila así —§8.9 la rechazaría con
  `interviniente_no_esta_en_la_obra`— hasta que alguien la resuelva. F-036 no
  cambia `sigrid-api`.
- **R107** · Las actividades de los proveedores de la obra se deben leer de
  Sigrid con **una** lectura más por `sql/read`, acotada a los proveedores de
  `obrofc` de esa obra, y el árbol de `auxpronat` con **otra** (entero si T1
  demuestra que cabe en el techo de filas; si no, solo las ramas de esas
  actividades); SI cualquiera de las dos llega al techo de filas, ENTONCES
  `catalogo_sin_verificar` (R10). Traen códigos, nombres, `pos` y la marca
  `homolo`, y ningún dato del proveedor que no sea su código.
- **R108** · El `CHECK` de `catalogo` de la tabla de decisiones debe admitir
  desde el principio `oficio`, `proveedor` y `actividad_oficio`: el guard del
  DDL no deja cambiar un `CHECK` después.
- **R109** · El Bloque 0 debe medir, **sin nombres por defecto**, para la 0677 y
  en global si es un `GROUP BY` en el servidor: (1) cuántos proveedores de la
  obra y de todo `obrofc` tienen actividades en `conact`, y cuántas cada uno;
  (2) `homolo`; (3) el tamaño y la **forma del árbol** de `auxpronat`
  —niveles y cómo se codifica el padre, deducidos de `cod` y `pos`—; (4)
  cuántas actividades de los proveedores de la obra hay por rama; y (5) el
  cruce por nombre normalizado de `auxpronat` con `auxofc` (en T8, con el
  normalizador de §15). Las PARADAS T3 y T9 lo enseñan al humano.
- **R110** · Los nombres de actividad no se consideran datos personales, pero la
  relación proveedor → actividades va con el código del proveedor: no sale en
  logs ni en `progress/` más que como recuentos (R47).
- **R111** · Todo texto que la medición lea de Sigrid debe llegar en **UTF-8 sin
  doble codificación**, tanto en la consola como en el JSON de `-SalidaJson`:
  «Fontanería» se escribe `46 6F 6E 74 61 6E 65 72 C3 AD 61`, nunca con
  `C3 83 C2 AD`. Es condición para que T8 pueda comparar nombres.
- **R112** · La correspondencia se debe poder confirmar por **actividad hoja**,
  por **rama** del árbol o por las dos (D-29). Con las dos (opción por
  defecto): para una actividad y un oficio, **manda la decisión del nodo más
  cercano** —la propia actividad, y si no tiene ninguna sobre ese oficio, su
  padre, y así hacia arriba—; una rama confirmada cubre a sus hijas **salvo**
  que una hija tenga su propia decisión «distinto» para ese oficio.
- **R113** · La pantalla de catálogos debe tener un apartado **«Actividades →
  oficios»** con las actividades (y sus ramas) de los proveedores de la obra y,
  para cada una, las propuestas si las hay y un selector con los oficios de la
  obra para **crear el par a mano**; las dos cosas envían una decisión
  `mismo` o `distinto` del catálogo `actividad_oficio`, con quién y cuándo.
- **R114** · CUANDO un proveedor de la obra no tiene actividades en `conact`, o
  ninguna con correspondencia confirmada, ENTONCES se ofrece con los oficios
  con que figura en `obrofc` (D-25). Mientras el humano no haya confirmado
  correspondencias, **todos** los proveedores caen aquí y la plantilla se
  comporta como antes de la tercera enmienda.

## 15 · Arreglos de la review 1 (añadido en la sexta enmienda del 2026-09-30)

- **R115** · El lector del Excel **no** debe recorrer ninguna hoja posición a
  posición más allá de lo que la plantilla puede tener: en «Incidencias», de la
  fila 2 a la **1002** (cabecera + el tope de 1000 filas de D-11 + 1) y solo en
  las columnas de datos; la cabecera, hasta una columna más que la de R2; los
  metadatos, en sus dos columnas y un tope pequeño de filas. SI hay **alguna
  celda con valor** (o fórmula) en las columnas de datos de la fila 1002 **o de
  cualquier otra por debajo**, ENTONCES el fichero se rechaza con **400**
  `demasiadas_filas`, el mismo error de R20. Para saberlo se miran **solo las
  celdas que el fichero trae**, nunca las posiciones intermedias. Las filas
  vacías con estilo —por debajo del tope o dentro de él— ni cuentan ni se leen
  como datos. Vale igual para el Excel de errores cuando se vuelve a subir
  (R66). Prueba: un libro con una celda vacía con estilo en la fila 1.048.576
  de «Incidencias» se lee en **menos de un segundo** y con la memoria acotada, y
  da las mismas filas que sin ella (`design.md` §5.2).

  **Ampliación de la sexta enmienda bis (2026-09-30, review 2, R2-1).** Lo
  anterior vale también **al cargar**: el lector **no** debe dejar que la
  biblioteca que abre el libro cree celdas por posición a partir de una
  estructura que las **expande** —un rango combinado, un hipervínculo sobre un
  rango o cualquier otra que el cargador enlace celda a celda—, en **ninguna**
  hoja del libro (`Incidencias`, `Instrucciones`, `_plantilla`, `_catalogos` o
  una que no sea de la plantilla). El libro se abre **en modo de solo
  lectura**, que no enlaza esas estructuras (`design.md` §5.2). Un combinado
  **pequeño** dentro de la plantilla (p. ej. dos celdas de la fila 2) **se
  admite**: cuenta el valor de su celda de arriba a la izquierda y las demás
  del rango se leen vacías. Prueba: los tres ficheros de la review 2 —rango
  combinado `A1003:A1048576` y `A1003:H1048576`, e hipervínculo sobre
  `A1003:H1048576`, en «Incidencias»— se leen (o se rechazan) en **menos de un
  segundo** y con la memoria acotada; lo mismo con el rango en `_plantilla` y
  en `Instrucciones`, y sobre un Excel de errores.

  > **Sexta enmienda bis del 2026-09-30.** R115 decía solo «el lector no debe
  > recorrer…». La review 2 midió que un rango combinado lejano cuesta 169 s y
  > 2,6 GB, y un hipervínculo sobre el mismo rango 228 s y 4,1 GB, **dentro de
  > `load_workbook`**, antes de que el lector recorra nada.
- **R116** · El informe de revisión de la migración (`progress/migracion_F-036.md`,
  que es un fichero versionado) **no** debe contener **ningún código** de
  proveedor: por fila dice «proveedor completado (único de la obra para ese
  oficio)», y en los recuentos, **cuántas filas llevan proveedor y por qué
  regla** (R91). El `v2` sí lleva el proveedor, porque es la plantilla, y no se
  versiona (R59). Prueba: el informe generado con un catálogo dado no contiene
  ninguno de los códigos de proveedor de su `obrofc`.

## 16 · El presupuesto de elementos XML (añadido en la séptima enmienda del 2026-10-01)

- **R117** · Antes de abrir el libro con la biblioteca de Excel (y después de
  las comprobaciones de R15 y R16 sobre el ZIP), el lector debe contar los
  **elementos XML de apertura** de **todas** las partes del ZIP, **sea cual
  sea su extensión** *(séptima enmienda bis)*, en *streaming* y con un
  analizador *expat* sin DTD ni entidades (`defusedxml`), sumándolos en un
  **presupuesto global de 300.000 elementos** *(séptima enmienda bis)*, y
  **dejar de leer** en cuanto lo pase. SI el total pasa de 300.000, ENTONCES
  **400** `fichero_sospechoso`, sin haber abierto el libro. SI una parte no se
  puede analizar (XML roto, DTD, entidades), ENTONCES **400** `no_es_xlsx`,
  también sin abrirlo. Se cuentan elementos, no etiquetas por nombre: no
  importa el espacio de nombres ni qué estructura sea.

  **Las partes que no acaban en `.xml` ni en `.rels`** *(séptima enmienda
  bis)*: se cuentan igual, y SI dejan de ser XML a mitad —o desde el primer
  byte, como una imagen o un `.bin` binario—, ENTONCES los elementos abiertos
  **hasta el fallo cuentan** en el presupuesto, esa parte se deja de leer en
  ese punto y el recuento sigue con la siguiente, **sin** rechazar el
  fichero por el fallo. Una parte con DTD o entidades, tenga la extensión que
  tenga, sigue siendo `no_es_xlsx`. Pruebas:
  - los siete ficheros de la tabla de R3-1 de la review 3 —la plantilla de 2
    filas más un elemento repetido hasta rozar los 20 MiB: `<xf/>` en
    `xl/styles.xml`; y en «Incidencias» `<dataValidation/>`, `<brk/>`,
    `<mergeCell/>`, celdas vacías con estilo, formato condicional e
    hipervínculos—, construidos en memoria, se rechazan en **menos de un
    segundo**, con la memoria acotada y **sin** llamar a la apertura del
    libro;
  - la **plantilla completa** (1000 filas, detalle de 2000 caracteres) se
    admite, y su cuenta queda por debajo de un quinto del presupuesto;
  - un doble del recuento dice cuántos elementos se leyeron: el recuento se
    corta al pasar el presupuesto, no al acabar el fichero;
  - justo en el presupuesto se admite; uno más, se rechaza.
  - *(séptima enmienda bis)* la plantilla con «Incidencias» en
    `xl/worksheets/sheet1.dat` y 1,6 millones de `<brk/>` (el fichero de
    T37-1) y un `.bin` con XML dentro por encima del presupuesto se
    rechazan con `fichero_sospechoso` en menos de un segundo y sin abrir el
    libro; una **imagen real** no cuenta ningún elemento y no se lee más
    allá de su primer trozo; una parte que empieza siendo XML y falla a
    mitad cuenta sus elementos hasta el fallo; el **Excel de errores más
    grande** (1000 filas con error en las 8 columnas, con el VML de los
    comentarios) se admite.

  > **Séptima enmienda bis del 2026-10-01 (T37-1).** R117 decía «todas las
  > partes `.xml` y `.rels`» y un presupuesto de 200.000. `openpyxl` localiza
  > hojas, cadenas compartidas y libro por **relaciones y tipos de
  > contenido**, no por la extensión: una hoja en `sheet1.dat` no se contaba
  > y costaba 48 s y 911 MB con 74 KB. Contar todas las partes sube el Excel
  > de errores más grande de 52.910 a 148.916 elementos, y el presupuesto se
  > recalibra a 300.000 (`design.md` §5.2).

## 17 · La lectura aislada en un proceso hijo (añadido en la octava enmienda del 2026-10-01)

- **R118** · Todo lo que hace la biblioteca de Excel con un **fichero subido**
  —abrirlo y recorrer sus hojas— debe correr en un **proceso hijo**, nunca en el
  proceso que atiende la petición. Vale para la importación y para el Excel de
  errores corregido que vuelve a entrar (es la misma importación). Las
  comprobaciones baratas que no usan la biblioteca —tamaño (R15), ZIP (R16) y
  presupuesto de elementos (R117)— van **antes**, en el proceso padre. El hijo
  tiene un tope de **30 s de reloj** y de **1 GB de memoria** (el doble de lo que
  propuso el líder, por decisión del humano). SI el hijo se pasa de tiempo, se
  queda sin memoria, muere o devuelve algo que no tiene la forma esperada o que
  pasa del tamaño acotado, ENTONCES se **mata** y la respuesta es **400
  `fichero_sospechoso`**, sin 5xx y sin escribir nada. El padre **nunca** carga
  el libro: recibe del hijo solo el resultado ya leído, en una forma
  **serializable sin ejecutar código** (JSON) y **acotada en tamaño**, y lo
  vuelve a validar antes de usarlo. Pruebas:
  - los ficheros hostiles de **todas** las reviews (incluidos los de R4-1: una
    validación de datos, un formato condicional y un escenario con un `sqref` de
    muchos rangos hasta el tope descomprimido) se rechazan **a tiempo** —antes
    del tope del hijo más el arranque— y **sin que crezca la memoria del
    padre** más allá del resultado acotado **más** lo que gasta el recuento
    de R117, que acota el tope descomprimido;

    > **Octava enmienda bis del 2026-10-01 (H-T40-1).** Decía solo «sin que
    > crezca la memoria del padre». El recuento de R117 corre en el padre y
    > gasta unas 5 veces el elemento más grande (80,8 MiB medidos con un
    > fichero de 17 MiB): está acotado por el tope descomprimido y se acepta
    > (`design.md` §5.2, «Lo que crece el padre»). El test fija el pico del
    > padre por debajo de 6 veces el tope descomprimido.
  - la plantilla completa y el Excel de errores más grande **se admiten** por el
    hijo real;
  - con un doble del ejecutor, cada salida del hijo (resultado bueno, tiempo
    agotado, memoria agotada, muerte, salida malformada, salida demasiado
    grande) da lo que dice este requisito, sin depender del sistema operativo;
  - el padre no llama nunca a la biblioteca de Excel para leer un fichero
    subido;
  - en Linux, un test real comprueba que el tope de memoria se aplica al hijo.
- **R119** · El tope de memoria del hijo se debe aplicar con el mecanismo del
  sistema (en Linux, `resource.setrlimit(RLIMIT_AS)` dentro del hijo, nada
  más empezar y antes de abrir el fichero). SI el sistema no lo permite (Windows, en local),
  ENTONCES: con `ENTORNO` en `dev` o `pro`, la lectura **no se hace** y la
  respuesta es **503** con el motivo (nunca se lee sin el tope en el entorno
  desplegado); fuera de `dev` y `pro`, se lee **solo con el tope de tiempo** y
  se registra un aviso. En todos los casos se registra, sin contenido, si el
  tope de memoria se aplicó.
  DONDE el sistema lo ofrece (Linux), el hijo debe ponerse además, en el mismo
  sitio y antes de abrir el fichero, un **tope de CPU**
  (`resource.setrlimit(RLIMIT_CPU)`) de los segundos del hijo **más 5**
  (35 s con los 30 de R118), para que un hijo **huérfano** —el padre muere a
  mitad de una lectura y ya nadie lo mata— no siga gastando CPU hasta acabar:
  al llegar a su tope, el sistema lo mata. `RLIMIT_CPU` cuenta **segundos de
  CPU del hijo, no de reloj**: no sustituye al tope de 30 s de reloj de R118,
  que sigue poniéndolo el padre y **no cambia**. SI el sistema no lo ofrece
  (Windows, en local), ENTONCES el tope de CPU **no se aplica**, con el mismo
  criterio que el de memoria y sin regla ni aviso propios. El tope de CPU **no
  se registra aparte**: se pone junto al de memoria, y la marca de «el tope de
  memoria se aplicó» vale para los dos. Pruebas:
  - en Linux, un test real comprueba que un hijo que no para de gastar CPU, sin
    un padre que lo mate, **muere solo** al llegar a su tope de CPU;
  - en Linux, un hijo que **espera** (reloj sin CPU) más que su tope de CPU
    **no** muere por él;
  - el tope de CPU que se pone al hijo son sus segundos más 5.

  > **Novena enmienda del 2026-10-01 (review 5, R5-1; «R5-1 se arregla»,
  > decisión del humano).** R119 solo hablaba del tope de memoria. El tope de
  > reloj lo pone el padre, así que si el padre muere (reciclado, despliegue)
  > el hijo sigue hasta acabar: visto por la review 5 con un fichero de R4-1,
  > vivo a los +22 s; medido por la review 6 en Linux, matando al padre con los
  > tres ficheros de R4-1, el huérfano gastaba 33,0 s, 30,2 s y **60,0 s** de
  > CPU. **Por qué 5 s de margen**:
  > con el padre vivo, el hijo —que no arranca hilos y por eso no gasta más CPU
  > que reloj— muere como muy tarde a los 32 s (30 de tope, 1 de `terminate` y
  > 1 de `kill`), así que el tope de CPU **no salta nunca antes** que el del
  > padre y lo que ve el padre (`tiempo`) no cambia; y un huérfano gasta como
  > mucho 35 s de CPU (medido con el arreglo, los mismos tres ficheros: 30,6 s,
  > 30,2 s y **34,9 s**), cuando sin tope no tenía límite.
  >
  > *Errata corregida el 2026-10-02 (review 6, R6-2).* Esta nota decía «del
  > orden de 90–110 s de CPU»: era una estimación de la review 5 a partir de
  > medidas de Windows, sin tope de memoria, no una medida en Linux. Las cifras
  > de arriba son las medidas por la review 6 (`progress/review_F-036.md`,
  > «Review 6», R6-2). Dos de los tres ficheros acaban solos antes de los 35 s,
  > con o sin tope; el arreglo acota el tercero y cualquier fichero que gaste
  > CPU sin gastar memoria. El requisito no cambia.
- **R120** · Como mucho **una** lectura aislada a la vez por proceso de la
  Function, para que 1 GB del hijo más el padre quepa en la memoria de la
  instancia (`design.md` §5.2, «La lectura aislada»). SI llega otra mientras
  hay una en curso y no queda libre en unos segundos, ENTONCES **503** «otra
  importación en curso; reintenta», sin escribir nada (D-30).

## 18 · El formato visual de la plantilla y del Excel de errores (añadido en la décima enmienda del 2026-10-02)

> **Origen.** El humano abrió el `v2` de T28 y pidió un formato «limpio,
> ordenado, con colores Ruesma»; aprobó una muestra el 2026-10-02. Los colores
> son los **tokens de la identidad Ruesma de F-035**
> (`services/postventa-front/css/styles.css` de la rama
> `feature/F-035-portal-posventa`, bloque `:root`), escritos aquí como ARGB
> opaco. La tabla completa, con el token de cada color, está en `design.md`
> §3.6. La tipografía es **Calibri**: las fuentes de la marca no están en los
> equipos de quien abre el fichero. **Sin logotipo ni imágenes**: una imagen
> incrustada es contenido que el lector trataría como sospechoso, y queda
> fuera de alcance.
>
> El formato lo pone **el único generador** (R55, R62), así que vale igual
> para la plantilla, el Excel de errores y el `v2` de la migración. Las hojas
> `veryHidden` no llevan formato.
>
> **Enmienda 10 bis (2026-10-02).** El humano decidió que este Excel **no se
> imprime** (se importa; más adelante, también se exportará) y que la
> plantilla vacía **enseñe la cabecera y una fila**. Cambian R122, R123, R125,
> R126 y R127; el texto anterior de cada uno se resume en su nota. Resultado
> a la vista: plantilla vacía = cabecera + fila 2; el `v2` de T28 = sus filas
> con formato y nada debajo; el Excel de errores = sus filas, con el rojo
> suave en las celdas con error.
- **R121** · **Cabecera de «Incidencias»** (fila 1, las 9 columnas). Cada
  celda debe llevar: relleno sólido **burdeos `FF9F2842`** —salvo la de
  `Errores (lo rellena el sistema)`, en **gris acero `FF7B868C`**—; fuente
  Calibri de **11** puntos, **negrita**, color blanco `FFFFFFFF`; alineación
  horizontal a la izquierda, vertical centrada, con ajuste de texto y sangría
  1; borde izquierdo y derecho finos (`thin`) blancos y borde inferior medio
  (`medium`) en burdeos fuerte `FF7A1E33`. La fila 1 mide **34** puntos de
  alto. El **texto** de cada celda es el de R2, sin cambios (R126).
- **R122** · **Cuerpo de «Incidencias»** (filas 2 a 1001, las 9 columnas).
  *(Reescrito en la enmienda 10 bis. Era: los cuatro bordes finos y el gris
  de `Errores` como estilo **estático** en las 9.000 celdas, y una sola
  regla de bandas `MOD(ROW(),2)=1`. Con eso Excel enseñaba una rejilla de
  1.000 filas vacías: R7-2.)*
  - **Estilo estático** (en las 9.000 celdas; no se ve mientras la celda está
    vacía): fuente Calibri de **10,5** puntos, color tinta `FF1D2024` (en
    `Errores`, el gris de R123); alineación vertical arriba y sangría 1, con
    ajuste de texto **solo** en `Descripción corta`, `Detalle` y `Errores`.
    **Ninguna** celda del cuerpo debe llevar **borde** ni **relleno**
    estáticos, salvo el relleno de la celda con error (R123). El desbloqueo y
    el formato de texto `@` de las columnas de datos **no son aspecto**:
    siguen en las 1.000 filas, igual que los desplegables (R126).
  - La hoja **no enseña la cuadrícula** de Excel y su pestaña es de color
    burdeos (`9F2842`).
  - Anchos de columna, en este orden: **30, 26, 48, 56, 28, 40, 24, 16, 50**.
  - **Fila pintada.** Una fila del cuerpo está *pintada* SI es la fila 2, O
    SI alguna de sus celdas de `A` a `I` tiene algo escrito. En la fórmula de
    Excel, relativa a la primera fila de cada rango:
    `OR(ROW()=2,COUNTA($A2:$I2)>0)`. Solo las filas pintadas enseñan líneas,
    bandas y el gris de `Errores`; las demás se ven en blanco, sin rejilla.
  - **Regla 1 · líneas.** La hoja debe llevar una regla de formato
    condicional de tipo expresión, con la fórmula
    `OR(ROW()=2,COUNTA($A2:$I2)>0)`, sobre el rango único **`A2:I1001`**, con
    **prioridad 1**, sin «detener si es verdad», cuyo formato son los cuatro
    bordes finos (`thin`) en gris claro `FFDFE2E4`, sin relleno ni fuente.
  - **Regla 3 · bandas alternas.** CUANDO ninguna fila lleva errores (la
    plantilla y el `v2`), la hoja debe llevar además una regla de tipo
    expresión con la fórmula `AND(MOD(ROW(),2)=1,COUNTA($A2:$I2)>0)`, sobre
    el rango único **`A2:H1001`** (las columnas de datos, sin `Errores`), con
    **prioridad 3**, sin «detener si es verdad», cuyo formato es el relleno
    sólido `FFFAFAFB`, sin borde ni fuente. Tiñe las filas impares pintadas
    (la 2 es par: no hace falta su caso). CUANDO alguna fila lleva errores
    (el Excel de errores), la hoja **no** debe llevar esta regla: el relleno
    de una regla se pinta encima del relleno fijo de la celda y taparía el
    rojo de R123 en las filas impares.
  - Las reglas van por **formato condicional** y no por estilo de celda para
    que sigan bien tras «ordenar», «insertar fila» y «borrar fila»: miran la
    posición y el contenido de la fila, no viajan con la celda. Sus formatos
    no se pisan entre sí (bordes en `A`–`I`; relleno gris solo en `I`, R123;
    relleno de banda solo en `A`–`H`): la prioridad fija el fichero, no el
    aspecto.
- **R123** · **La columna `Errores` y las celdas con error.** *(Reescrito en
  la enmienda 10 bis. Era: el gris de `Errores` como relleno estático de
  `I2:I1001`.)*
  - Las celdas de la columna `Errores` de las filas 2 a 1001 deben llevar,
    como estilo **estático**, la fuente Calibri de 10,5 en gris `FF5D676D`, y
    siguen **bloqueadas** (R2). Su fondo gris «no editable» `FFF3F4F5` va por
    la **regla 2**: tipo expresión, fórmula `OR(ROW()=2,COUNTA($A2:$I2)>0)`,
    rango único **`I2:I1001`**, **prioridad 2**, sin «detener si es verdad»,
    formato relleno sólido `FFF3F4F5`, sin borde ni fuente; en toda
    plantilla y en todo Excel de errores.
  - Cada celda con error (R64) debe llevar, como estilo **estático**, relleno
    sólido **rojo suave `FFFEF2F2`** y fuente Calibri de 10,5 puntos en
    **rojo `FFB91C1C`**, con la misma alineación, protección y formato de
    texto que las demás del cuerpo, **sin borde estático** (sus líneas son
    las de la regla 1: su fila tiene datos y está pintada), y su comentario
    (R64). El rojo puede seguir siendo estático porque **solo** va en filas
    con datos, que se pintan igualmente; y no puede ser condicional sin una
    regla por celda, que R127 prohíbe. Las celdas **sin** error —de datos o
    de `Errores`— no llevan relleno estático.
  - El Excel de errores, por tanto, lleva las reglas 1 y 2 y **no** la 3
    (R122). *Alternativa descartada*: unas bandas que salten las filas con
    texto en `Errores` (`…,$I2=""`): en el Excel de errores **todas** las
    filas lo llevan, así que las bandas solo saldrían en las filas que el
    usuario añada, a cambio de otro caso que probar.
- **R124** · **«Instrucciones».** La hoja no enseña la cuadrícula y su pestaña
  es gris acero (`7B868C`). «Las columnas de la tabla» son las 8 de datos
  (A–H). Los **textos** y su posición son los de R5, sin cambios.
  - **Fila 1, la obra**: banda burdeos `FF9F2842` en A–H; fuente Calibri de
    **15**, negrita, blanca; vertical centrada, sangría 1; alto **38**.
  - **Fila 2, el título**: fuente Calibri de **13**, negrita, **burdeos**
    `FF9F2842`, en A2; vertical centrada, sangría 1; alto **28**; y una línea
    debajo: borde inferior medio (`medium`) burdeos en A–H.
  - **Párrafos** (de la fila 3 a la anterior a la fila en blanco que precede
    a los ejemplos): Calibri de **11**, tinta `FF1D2024`, ajuste de texto,
    vertical arriba, sangría 1; el alto de cada fila se **calcula** con el
    largo de su texto: `max(20, 16 × (largo // 105 + 1) + 6)` puntos, para
    que ningún párrafo se vea cortado.
  - **Tabla de ejemplos**: su cabecera como la de «Incidencias» —relleno
    burdeos en las 8 columnas, Calibri 11 negrita blanca, bordes de R121—,
    con vertical centrada, sangría 1 y alto **26**; sus filas, Calibri de
    10,5 en tinta, los cuatro bordes finos `FFDFE2E4`, ajuste de texto,
    vertical arriba y sangría 1, y relleno `FFFAFAFB` en la **segunda,
    cuarta…** fila de ejemplo (relleno fijo: esta tabla no se ordena).
  - Anchos: la columna A, **100**; de la B a la H, **28**.
- **R125** · **Sin ajustes de impresión.** *(Reescrito en la enmienda 10 bis
  del 2026-10-02. **Retirado** el texto de la décima —A4 apaisado, ajuste a
  una página de ancho, fila 1 repetida, márgenes laterales de 0,4 y pie
  «Posventa · Construcciones Ruesma · página &P de &N»— porque este Excel no
  se imprime: se importa, y más adelante se exportará. Con ello desaparece
  R7-1 —no hay impresión que fijar— y queda resuelto R7-2. La impresión a
  PDF de los partes de trabajo es F-044 y no aplica aquí.)* El generador no
  debe poner **ningún** ajuste de impresión en **ninguna** de las cuatro
  hojas. En cada hoja:
  - sin área de impresión ni títulos de impresión (filas y columnas);
  - sin orientación, tamaño de papel, escala, `fitToWidth` ni
    `fitToHeight`, y sin «ajustar a página» (`fitToPage`);
  - sin opciones de impresión: ni centrado horizontal ni vertical, ni
    cuadrícula ni encabezados de fila y columna;
  - los márgenes, los de por defecto de la biblioteca (izquierdo y derecho
    0,75; superior e inferior 1; encabezado y pie 0,5);
  - sin encabezado ni pie de página (ni el impar, ni el par, ni el de la
    primera página; ningún trozo izquierdo, central ni derecho);
  - sin saltos de página.

  Y en el libro, **ningún nombre definido de impresión**
  (`_xlnm.Print_Titles`, `_xlnm.Print_Area`): los nombres definidos son los
  seis de las listas (R3) y el del filtro (`_xlnm._FilterDatabase`), nada
  más. Prueba: los valores leídos de cada hoja con `openpyxl` y, en el XML,
  la ausencia de `<pageSetup`, `<printOptions`, `<headerFooter`,
  `<rowBreaks` y `<colBreaks` en las hojas y de `_xlnm.Print_` en
  `xl/workbook.xml`. Esto **no** es un requisito sobre lo que se importa: un
  fichero al que el usuario le haya puesto ajustes de impresión en Excel se
  importa igual (R126).
- **R126** · **Invariantes: el formato no cambia lo que lee el importador.**
  El formato de R121–R125 es **solo aspecto**. Con él, el libro debe seguir
  teniendo, igual que antes de esta enmienda:
  - las **mismas cuatro hojas**, con los mismos nombres, orden y estado, e
    «Incidencias» primera y activa;
  - la **cabecera en la fila 1** de «Incidencias», con los **mismos textos**
    en el mismo orden (R2), y ninguna fila ni columna añadida, combinada ni
    desplazada: los datos siguen empezando en la fila 2;
  - los **mismos desplegables y validaciones** (R3, R4), con los mismos
    rangos, mensajes y rangos con nombre; la **misma protección** (R2); el
    **mismo filtro** en la cabecera; los **paneles inmovilizados** en `A2`; el
    **formato de texto** (`@`) y el prefijo de comilla en las celdas de
    datos; los **mismos metadatos** en `_plantilla` (R6), con la **misma
    versión `1`** y el mismo identificador;
  - **ninguna celda es una fórmula** (R7): las fórmulas de las reglas de
    formato condicional de R122 y R123 no son fórmulas de celda (van en
    `<cfRule><formula>`), y el XML de las hojas sigue sin llevar ningún
    `<f>`.

  *(Enmienda 10 bis: las 1.000 filas siguen preparadas igual —desbloqueo,
  `@`, desplegables, filtro `A1:I1001`, validaciones `A2:A1001`…`H2:H1001`—
  aunque solo se **vean** las pintadas; el tope de 1.000 filas no cambia.)*

  El lector debe devolver **el mismo `LibroLeido`** —metadatos, cabecera,
  filas y `datos_fuera_del_tope`— de un libro con formato que el que devolvía
  del mismo contenido sin él: el lector no lee estilos. Y las plantillas **ya
  descargadas** con cualquiera de los dos formatos anteriores deben seguir
  **importándose igual**: la del **formato antiguo** (anterior a la décima
  enmienda: sin estos estilos, con el relleno naranja en sus errores) y la
  del **formato de la décima** (bordes y gris de `Errores` estáticos en las
  1.000 filas, una sola regla de bandas `MOD(ROW(),2)=1` y los ajustes de
  impresión de la R125 retirada, con su `_xlnm.Print_Titles`). El importador
  no exige, ni mira, ningún estilo, color, ancho, formato condicional ni
  ajuste de impresión —tampoco los que el usuario ponga en Excel—, y la
  versión de la plantilla no cambia (R18). Pruebas:
  - ida y vuelta: una plantilla rellena generada con el formato nuevo, leída
    por el lector en proceso y por el lector aislado, da las filas que se
    escribieron y pasa la validación con cero errores; lo mismo un Excel de
    errores con formato, que da sus filas tal como llegaron;
  - un libro **sin** el formato nuevo (construido en el test quitando al
    generado los estilos y el formato condicional, o con otros distintos) da
    el **mismo** `LibroLeido`;
  - *(enmienda 10 bis)* una plantilla con el **formato de la décima**,
    construida en el test a partir de la generada (se le ponen los estilos
    estáticos, la regla única de bandas y los ajustes de impresión con
    `print_title_rows`, y se le quitan las tres reglas nuevas), da el
    **mismo** `LibroLeido` por el lector en proceso y por el aislado, y pasa
    la validación con cero errores; y la del formato antiguo, igual que ya se
    prueba;
  - los tests de R2–R7, R12 y R62–R66 que ya existen siguen en verde **sin
    tocarlos**, salvo los que fijaban el aspecto (anchos, tamaño del título
    de «Instrucciones», el relleno de la columna `Errores` en el de R64), que
    pasan a los valores de R121–R124 tal como quedan tras la enmienda 10 bis.
- **R127** · **El formato cabe en los topes vigentes, sin tocarlos.** Con el
  formato de R121–R125 *(medido de nuevo tras la enmienda 10 bis: hay más
  reglas condicionales y menos estilos estáticos; T57)*:
  - la **plantilla completa** (1000 filas, detalle de 2000) debe seguir por
    debajo de **un quinto** del presupuesto de elementos XML (60.000; R117), y
    el **Excel de errores más grande** (1000 filas con error en las 8
    columnas), en **la mitad o menos** (150.000): el margen de «2,0 veces»
    con el que se calibró el presupuesto (`design.md` §5.2);
  - el doble de lo que ocupa descomprimido el mayor de los dos, redondeado al
    MiB, debe seguir siendo **17 MiB** (R16), y el doble de su resultado
    leído, **11 MiB** (R118): `MAX_BYTES_DESCOMPRIMIDOS`,
    `MAX_BYTES_RESULTADO`, `PRESUPUESTO_ELEMENTOS_XML`, los 30 s y el 1 GiB
    del hijo **no cambian**;
  - los dos se siguen admitiendo por el **hijo real** (R118);
  - *(enmienda 10 bis; era «como mucho un elemento de formato condicional»)*
    la plantilla y el `v2` llevan **exactamente tres** elementos
    `<conditionalFormatting>` en «Incidencias» —las reglas 1, 2 y 3 de R122 y
    R123— y el Excel de errores, **exactamente dos** —la 1 y la 2—; cada
    elemento con **una** `<cfRule>` y un `sqref` de **un solo rango**, y en
    `xl/styles.xml` tantos `<dxf>` como reglas (tres o dos). **Ninguna** regla
    por fila ni por celda, y ningún formato condicional en las otras tres
    hojas;
  - **ninguna imagen** ni parte nueva en el ZIP (las mismas partes que antes
    de la décima enmienda); y el formato no crea celdas fuera de las filas
    1–1001 de «Incidencias» ni de las columnas A–I.

  SI el formato deja algún tope con menos margen que estos, ENTONCES se
  **recorta adorno** —lo primero, las bandas alternas— y **no** se sube ningún
  tope: subir un tope exige volver al humano (`design.md` §5.2, «Los topes y
  el formato visual»; `tasks.md`, T52 y T57).

  > **Los `sqref` legítimos y el control de R4-1.** R4-1 no se cerró con un
  > filtro de `sqref` sino con la lectura aislada (R118): un `sqref` hostil
  > —millones de rangos— agota el tiempo o la memoria del hijo y es
  > `fichero_sospechoso`. *(Enmienda 10 bis.)* Los **tres** `sqref` de R122 y
  > R123 son **un** rango cada uno (`A2:I1001`, `I2:I1001`, `A2:H1001`), como
  > los ocho de las validaciones de datos que la plantilla ya lleva: cuestan
  > tres objetos. No hay lista blanca ni excepción que mantener: el lector no
  > distingue un `sqref` «bueno» de uno malo, lo legítimo pasa porque es
  > pequeño, y los ficheros hostiles de R4-1 se siguen rechazando igual (sus
  > tests no se tocan; si un constructor hostil dependía de cuántas reglas
  > traía la plantilla, se arregla el constructor, no la comprobación).

## 19 · La migración ante un catálogo de Sigrid que ha cambiado (añadido en la undécima enmienda del 2026-10-03)

> **Origen.** Verificación MANUAL T29 del 2026-10-03: el `v2`, generado con
> el catálogo del 2026-09-29, dio 14 filas con error en el entorno porque
> Sigrid había cambiado los oficios de la 0677. Decisión del humano: el `v2`
> se rehace leyendo Sigrid justo antes, y en él solo van oficios y pares de
> Sigrid de ese día. Diseño en `design.md` §10.5; tareas en el Bloque 14.

- **R128** · CUANDO el oficio de una fila nueva de la tabla de correcciones
  no es, recortado, el nombre de ningún oficio de la obra (`oficios_obra` del
  JSON del catálogo) pero **sí** es exactamente, recortado, el nombre de
  algún oficio del catálogo completo de Sigrid (`oficios_catalogo`, todo
  `auxofc`), el script **no** debe parar: esa fila del `v2` debe llevar
  `Oficio` **vacío** y `Proveedor` **vacío**, y el informe la debe listar
  (R130). Entra aquí también el oficio que sigue en `obrofc` pero está dado
  de baja en `auxofc` (R13): no está entre los oficios de la obra. El resto
  de la fila (unidad, ubicación, descripción, detalle, urgencia, listado) no
  cambia, y la ida y vuelta por el importador sigue exigiendo **cero
  errores** (R56). La comparación con `oficios_catalogo` es la de R97:
  exacta, con los nombres de Sigrid recortados por los extremos; mayúsculas,
  tildes y puntuación, tal cual (decisión 7: nada de casado aproximado). SI
  el JSON del catálogo no trae `oficios_catalogo` como una lista de
  `{codigo, nombre}`, ENTONCES el script para con el error de forma del
  catálogo, como con cualquier otra clave que falte (§10.3); un `nombre`
  nulo o vacío no casa con nada.

  Prueba: con un catálogo cuyo `oficios_catalogo` lleva un oficio que la
  tabla usa y que no está en `oficios_obra`, `migrar` termina; esa fila
  compuesta lleva oficio y proveedor vacíos; el `v2` vuelve por el lector y
  `validar_filas` con **0 errores** y esa fila se lee con `Oficio` y
  `Proveedor` vacíos; ninguna celda de «Incidencias» lleva el nombre de ese
  oficio; un nombre que es a la vez de la obra y de `oficios_catalogo` se
  resuelve como siempre (la obra manda); y el JSON sin `oficios_catalogo`, o
  con él mal formado, para con el error de forma.

- **R129** · El `Proveedor` del `v2` debe salir **solo** de R91 aplicado al
  catálogo con que se ejecuta el script. Ni el original (columnas A, D, E y
  F, sin proveedor; doc. 05) ni la tabla de correcciones (que rechaza un
  campo `proveedor`, §10.2) pueden traer uno. Así, el `v2` nunca lleva un par
  `<oficio> · <proveedor>` que no esté en `obrofc` de la obra en el catálogo
  de ese día, y una fila con el oficio vacío por R128 no lleva proveedor.

  > **Decisión del humano y por qué no hay aviso propio.** El humano pidió
  > «lo mismo con un proveedor que el original o la corrección asignen y ya
  > no sea de la obra para ese oficio: se deja vacío y se avisa». En el
  > código de hoy ese caso **no se puede dar**: ni el original ni la tabla
  > llevan proveedor, y R91 lo calcula en cada ejecución con el catálogo
  > recibido. Lo que en el `v2` del 2026-09-29 dio «el par oficio ·
  > proveedor no está en la lista de la obra» se arregla solo al regenerar
  > con el catálogo del día (R131). Por eso R129 es un invariante con su
  > test, sin sección propia en el informe; lo que sí se avisa es la fila
  > sin oficio de R128, que tampoco lleva proveedor.

  Prueba: la misma tabla con dos catálogos que solo difieren en el
  proveedor único de un oficio: cada `v2` lleva el par de su catálogo y
  vuelve con 0 errores; el mismo oficio con dos proveedores en la obra:
  `Proveedor` vacío; una fila nueva de la tabla con un campo `proveedor`:
  para por la forma; la fila de R128, cuyo oficio tenía un único proveedor
  en el catálogo viejo: sin proveedor.

- **R130** · El informe de revisión debe llevar, **siempre**, en los
  recuentos, la fila «| Filas nuevas sin oficio porque ese oficio ya no está
  en la obra en Sigrid | N |»; y CUANDO N > 0, una sección **«## Filas sin
  oficio porque ese oficio ya no está en la obra en Sigrid»** justo después
  de los recuentos, con una fila por cada fila nueva afectada: fila del
  original, número de la fila nueva dentro de ella y el nombre del oficio
  que dice la tabla. En la tabla de su ubicación, esa fila nueva dice
  «Oficio: — (ya no está en la obra en Sigrid: «<nombre>»)». La línea de
  órdenes debe imprimir «Filas sin oficio porque ese oficio ya no está en la
  obra en Sigrid: N». Nada de esto lleva nombres ni códigos de proveedor
  (R116).

  Prueba: con el catálogo de los tests de siempre, la fila de recuento sale
  con 0 y la sección no sale; con el de R128, el recuento y la línea de
  órdenes dicen 1 (o las que haya), la sección lista la fila del original,
  la fila nueva y el nombre, la fila de su ubicación lleva el texto de
  arriba, y ni el informe ni la salida contienen ningún código ni nombre de
  proveedor del catálogo, tampoco el que ese oficio tenía en el catálogo
  viejo.

- **R131** · El `v2` definitivo (T28) se debe generar con el catálogo de la
  obra leído de Sigrid **en el momento** —`infra/26_catalogos_plantilla_sigrid.ps1
  -SalidaJson` justo antes de la migración, nunca un JSON guardado de otro
  día— y con los grupos vigentes descargados de `oficios.html` **justo
  antes**. Su importación en el entorno desplegado (T29, paso 4) debe dar
  **0 filas con error**.

  Prueba: un test documenta el porqué —el `v2` generado con un catálogo y
  validado contra otro en el que un oficio ha salido de la obra y otro ha
  cambiado de proveedor da errores en esas filas; el regenerado con el
  segundo catálogo, 0—; y el resto es **MANUAL** (T28 y T29): el script no
  sabe cuándo se leyó el JSON y su interfaz no cambia.
