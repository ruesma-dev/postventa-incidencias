<!-- specs/F-036-importar-excel/design.md -->
# F-036 · Importar el Excel de incidencias de la propiedad a una bandeja — Diseño técnico

> Diseñado contra `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
> `azure-apps/sigrid_api.md` §6, §8.9 y §9.8, `azure-apps/sigrid_tablas.md`
> (`upv`, `obrofc`, `auxofc`, `prv`, `rcp`) y el código de `dev` en `a468367`.
> Los requisitos (`R1`…`R91`) están en `requirements.md`; las decisiones, en
> §13.

> **Enmienda del 2026-09-28 · revisión del humano sobre `101345d`.** Cambia:
> la importación deja de ser todo o nada y devuelve un **Excel de errores**
> (§3.5, §5.3, §6.1, §7.3, §8, §9); todo valor no libre se compara **exacto**
> (§4.3, §4.4); columna **`Proveedor`** (§3.2, §5.1, §6.1, §6.3); y una pieza
> nueva, **proveedores casi duplicados del maestro de Sigrid** (§15, con su
> tabla en §6.1 y sus endpoints en §8). La tabla de tareas se ha renumerado
> (T1–T29): las referencias de este documento son ya las nuevas. Cada sección
> que cambia algo escrito lleva su recuadro.

> **Segunda enmienda del 2026-09-28 · los oficios también se agrupan** (sobre
> `ced9c8f`, decisión 10 de `requirements.md`). La pieza de §15 deja de ser «de
> proveedores» y pasa a ser **un solo mecanismo para los dos catálogos**,
> oficios y proveedores: mismos módulos, misma tabla con un discriminador
> `catalogo`, misma pantalla (`proveedores.html` → **`catalogos.html`**) y
> mismas rutas (`/api/proveedores/*` → **`/api/catalogos/*`**). El desplegable
> de `Oficio` enseña grupos; la bandeja gana `oficio_ambiguo`; el oficio y el
> proveedor se resuelven **juntos** contra `obrofc` (§15.5); la migración
> resuelve los nombres de oficio de la muestra contra los grupos confirmados
> (§10). D-21 pasa a decidida y D-18 se reevalúa (§13). Las tareas se renumeran
> otra vez en el final (T1–T30), porque la migración definitiva necesita los
> grupos confirmados en el entorno desplegado. Las referencias de este
> documento son ya las nuevas.

> **Tercera enmienda del 2026-09-28 · el oficio de un proveedor sale de sus
> familias en Sigrid** (sobre `6cf1bf1`, decisión 11 de `requirements.md`).
> Los proveedores que se ofrecen siguen siendo los de la obra (`obrofc`), pero
> qué oficios cubre cada uno lo dicen sus familias (`confam` → `auxfam` →
> correspondencia → `auxofc`). Si familia y oficio son el mismo catálogo se
> **mide** (T1/T2, T8) y el diseño se bifurca (§16.3): identidad de códigos o
> una correspondencia confirmada por el humano con **el mismo** mecanismo de
> §15, como catálogo `familia_oficio`. Nueva lectura de Sigrid (§6.3), nuevo
> módulo puro `cobertura.py`, nueva marca `proveedor_fuera_de_obrofc` en la
> bandeja para lo que §8.9 no aceptaría (§16.6), D-16/D-17 revisadas y
> D-24…D-28 nuevas. El detalle está en §16; cada sección que cambia lleva su
> recuadro. La numeración de tareas no cambia.

> **Cuarta enmienda del 2026-09-28 · actividades (`conact`/`auxpronat`).** La
> medición de T2 (`progress/explore_F-036.md`) desmiente §16: `confam`,
> `auxfam` y `entfam` están **vacías** y `prv.ofcide` casi no se usa. Las
> familias del humano son las **actividades** del proveedor, `conact` →
> `auxpronat`, un catálogo **en árbol** con otro vocabulario que `auxofc`. §16
> se reescribe: la correspondencia actividad → oficio es una tabla que
> confirma el humano (catálogo `actividad_oficio`, antes `familia_oficio`), a
> nivel de hoja, de rama o de las dos (D-29), y se puede crear a mano. La
> medición también decide D-2, D-8 y D-9 y da el origen de las ubicaciones
> (D-3). Con **0** grupos de proveedores parecidos en todo `obrofc`, D-18
> queda abierta con la recomendación del líder de sacar la agrupación de
> proveedores a otra ficha, y la costura para las dos opciones está en
> §15.8. T1 se reabre (actividades y UTF-8, R111). Cada sección que cambia
> lleva su recuadro.

> **Quinta enmienda del 2026-09-29 · PARADA T3: se simplifica.** El humano
> decidió (1) **opción A**: la relación oficio ↔ proveedor sale **solo** de
> `obrofc` de la obra, que es lo único que acepta `sigrid-api` §8.9; las
> actividades (`conact`/`auxpronat`), la correspondencia `actividad_oficio`,
> su apartado de pantalla, la lectura del árbol, `cobertura.py` y el caso B
> `proveedor_fuera_de_obrofc` **salen a F-039** (§16, retirada); y (2) **D-18**:
> la agrupación de proveedores **sale a F-050**. Queda la de **oficios**, con
> el mecanismo de §15 para un solo catálogo y la costura del discriminador
> `catalogo` para que F-050 y F-039 lo reutilicen (§15.8). Fuera de F-036 se
> van también la marca de CIF, las formas jurídicas y el apartado
> Proveedores; la pantalla pasa a `oficios.html`. Lo medido en T1/T2 se
> queda como hecho. D-18, D-24 y D-27 quedan decididas; D-25, D-26, D-28 y
> D-29 salen con las actividades a F-039. Cada sección que cambia lleva su
> recuadro.

> **Sexta enmienda del 2026-09-30 · review 1 (`progress/review_F-036.md`,
> CHANGES_REQUESTED) y decisión del humano del mismo día.** Cuatro cosas:
> (1) **tope de recorrido del lector del Excel** (R115, §5.2): una celda vacía
> con estilo en una fila lejana hacía recorrer la hoja hasta `max_row`; (2)
> **B5-1 decidida**: el `CHECK` del par lleva `COLLATE "C"` (§6.1, §13); (3)
> **el informe de migración no lleva códigos de proveedor** (R116, §10.4); y
> (4) §2.3 y §8 como quedaron implementados (la excepción de
> `infra/08_lectura_sigrid_comun.ps1` y las respuestas de `/api/catalogos/*`).
> El merge a `dev` será con `git merge --squash` (decisión del humano), para
> que los códigos de proveedor y el GUID de relleno de los commits
> intermedios no lleguen a `dev`.

> **Sexta enmienda bis del 2026-09-30 · review 2** (CHANGES_REQUESTED, R2-1).
> Un rango combinado o un hipervínculo sobre un rango lejanos hacen que
> `openpyxl` cree una celda por posición **dentro de `load_workbook`** (169 s y
> 2,6 GB, 228 s y 4,1 GB con 33 KB), en cualquier hoja. R115 se amplía a lo que
> el cargador expande, y el lector abre el libro **en solo lectura**
> (`read_only=True`), que no lo expande (§5.2, «Al cargar»). Un combinado
> pequeño dentro de la plantilla se admite. Tareas T35–T36 en el Bloque 10.

> **Séptima enmienda del 2026-10-01 · review 3** (CHANGES_REQUESTED, R3-1 y
> R3-2; el humano eligió hacer R3-1). El tope de 20 MiB no acotaba el coste: con
> 64 KB y 4,1 millones de `<xf/>` en `styles.xml`, 114 s y 2,5 GB, también en
> solo lectura. Nuevo **R117**: un **presupuesto global de 200.000 elementos
> XML**, contado en *streaming* con expat de `defusedxml` antes de
> `load_workbook` (§5.2, «El presupuesto de elementos XML»; §0.1). Las dos
> pasadas por «Incidencias» no se funden. Erratas de R3-2 corregidas
> (`A1:I10`; «todos los recorridos limitados»). Tareas T37–T38 en el Bloque
> 10.

> **Séptima enmienda bis del 2026-10-01 · hallazgo T37-1** (el humano eligió
> la opción (a)). El presupuesto cuenta **todas las partes del ZIP**, no solo
> las `.xml` y `.rels`: `openpyxl` encuentra las partes por relaciones y tipos
> de contenido, y una hoja en `sheet1.dat` se saltaba el recuento (74 KB → 48
> s y 911 MB). El presupuesto pasa de 200.000 a **300.000** para que quepa el
> Excel de errores más grande (148.916). §5.2, «El presupuesto de elementos
> XML». Tareas T37 bis y T38 bis.

> **Octava enmienda del 2026-10-01 · cambio de estrategia** (review 4, R4-1;
> el humano eligió la opción (A) del líder «pero dobla los límites»). La
> review 4 encontró el cuarto hueco de la misma familia: los atributos `sqref`
> se convierten en un objeto por rango y el presupuesto de elementos no los ve.
> En vez de otro parche: **la lectura con `openpyxl` de un fichero subido
> pasa a un proceso hijo con tope de 30 s de reloj y 1 GB de memoria**
> (R118–R120; §5.2, «La lectura aislada en un proceso hijo»): si se pasa o
> muere, se mata y es `fichero_sospechoso`; el padre nunca carga el libro y
> recibe un JSON acotado. El tope descomprimido de R16 pasa a el doble del
> fichero legítimo más grande, medido. Se mantienen el solo lectura, R115 y
> R117. R4-1 queda cerrado por R118. Tareas T39–T44 en el Bloque 10.

> **Décima enmienda del 2026-10-02 · formato visual** (petición del humano al
> abrir el `v2` de T28; muestra aprobada el mismo día). Sección nueva **§3.6,
> «Formato visual»**: la tabla de colores, fuentes, tamaños, anchos y alturas
> de la plantilla y del Excel de errores (R121–R125), dónde vive cada
> constante en `excel_openpyxl.py` y cómo se prueba; y en §5.2, **«Los topes y
> el formato visual»**: qué añade el formato al fichero, qué hay que volver a
> medir y la regla de decisión (recortar adorno antes que subir un tope;
> R127). Solo cambia el generador de `excel_openpyxl.py`: ni el lector, ni el
> dominio, ni el contrato de la plantilla, ni su versión (R126). Tareas
> T50–T54 en el Bloque 12.

> **Enmienda 10 bis del 2026-10-02 · sin impresión y una sola fila a la
> vista** (review 7, R7-1 y R7-2; decisión del humano: el Excel no se
> imprime, se importa; la plantilla vacía, con una línea basta). En §3.6:
> fuera los ajustes de impresión (R125 pasa a «sin ajustes de impresión»),
> y lo visible del cuerpo —líneas, bandas y gris de `Errores`— pasa de estilo
> estático en las 1.000 filas a **tres reglas de formato condicional** que
> pintan la fila 2 y cada fila con algo escrito (R122, R123). Las 1.000 filas
> siguen preparadas igual (R126). En §5.2, «Los topes y el formato visual»:
> qué cambia en el fichero, volver a medir, la regla de decisión sin el
> recorte de impresión y la aclaración de R7-3 (los ~984 elementos de margen
> son frente a la guarda de calibración, no frente al rechazo). Solo cambia el
> generador de `excel_openpyxl.py`. Tareas T55–T60 en el Bloque 13.

> **Undécima enmienda del 2026-10-03 · la migración ante un catálogo de
> Sigrid que ha cambiado** (verificación MANUAL T29; decisión del humano: el
> `v2` se rehace leyendo Sigrid justo antes y solo lleva oficios de Sigrid de
> ese día). Sección nueva **§10.5**: cuando un oficio de la tabla de
> correcciones es de Sigrid pero ya no de la obra, la migración **no se
> para**: deja el oficio (y el proveedor) vacíos y lo dice en el informe
> (R128, R130); una errata sigue parando (R97); el proveedor del `v2` sale
> solo del catálogo con que se ejecuta (R129); y T28 lee el catálogo y los
> grupos en el momento (R131). Retocados §10.1, §10.3 (paso 3) y §10.4.
> Solo cambian `scripts/migracion_f036.py` y una línea de
> `scripts/migrar_excel_f036.py`; ni su interfaz, ni el YAML, ni el
> generador, ni el lector, ni el importador, ni la bandeja. Tareas T61–T64
> en el Bloque 14.

## 0 · Dónde está el riesgo

### 0.1 · Qué se rompe si esto sale mal, y quién lo ve

| Fallo | Quién lo ve | Qué lo impide |
|---|---|---|
| Una incidencia entra dos veces en la bandeja y luego se crea dos veces en Sigrid | Posventa, la propiedad y el industrial que va dos veces | Clave de duplicado (R35) + atajo por `sha256` de un fichero ya importado completo (R39) + **índice único parcial** en la base (R41) |
| Una fila se asigna a otra unidad, otra obra u otro proveedor | El industrial va a otra vivienda, o va otro industrial | Valores tasados comparados **exactos** contra el catálogo **leído de Sigrid en esa importación**, no contra lo que diga el fichero (§4.4) |
| Se importa parte del fichero y nadie lo sabe | Posventa cree que está todo | La respuesta dice `parcial`, cuenta las filas con error y trae el **Excel de errores**; la importación queda registrada `parcial` (R33, R42, R62) |
| Dos oficios distintos se funden en uno *(quinta enmienda: los proveedores ya no se agrupan en F-036)* | La incidencia se clasifica en otro oficio | Nunca se agrupa solo: propuesta + confirmación humana, cliques y no cadenas, y una decisión «distinto» anula la componente (§15) |
| Un grupo con varios códigos en la obra se resuelve a uno cualquiera | El volcado de F-040 da de alta el oficio o el proveedor equivocado | El sistema no elige: la fila queda `oficio_ambiguo` y se decide en la bandeja (R93, R94) *(quinta enmienda: `proveedor_ambiguo` ya no puede darse en F-036)* |
| Un fichero hostil (zip bomb, XML con entidades, macros, una celda con estilo en la fila 1.048.576, un rango combinado o un hipervínculo sobre un rango lejanos, millones de elementos pequeños dentro de 20 MiB) tumba la Function | Todo el servicio | Tope de 2 MiB antes de abrir, inspección del ZIP antes de `openpyxl`, `defusedxml`, sin macros (R15, R16), **recorrido acotado** de las hojas (R115; sexta enmienda), libro abierto **en solo lectura**, que no expande rangos al cargar (R115; sexta enmienda bis), y **presupuesto de 300.000 elementos XML** contado antes de abrir sobre todas las partes del ZIP (200.000 y solo `.xml`/`.rels` hasta la séptima enmienda bis), porque el tope de 20 MiB no acota cuántos elementos analiza `openpyxl` (R117; séptima enmienda); y, como red para toda la familia, también los atributos con listas de rangos de R4-1: **lectura en un proceso hijo con tope de 30 s y 1 GB**, que si se pasa se mata (`fichero_sospechoso`), y tope descomprimido al doble del fichero legítimo más grande (R118–R120, R16; octava enmienda) |
| La plantilla lleva una fórmula que se ejecuta al abrirla en el equipo de la propiedad | La propiedad | Ninguna celda generada es fórmula; texto con `=` se escribe como texto (R7) |
| Se escribe en Sigrid | El ERP de producción | F-036 **no tiene** ninguna ruta de escritura; un test lo vigila (R46) |
| Un texto libre de la propiedad o el nombre de un autónomo acaba en los logs o en git | Cualquiera con acceso | R47, R83: logs solo con códigos y recuentos; la tabla de equivalencias no guarda nombres; ningún YAML con nombres |

> **Enmienda del 2026-09-28.** La fila «Se importa medio fichero» decía que lo
> impedía el todo o nada; ahora la importación parcial es la decisión del
> humano y lo que se garantiza es que **se sabe**. Se añaden las filas de
> proveedores.
>
> **Segunda enmienda del mismo día.** Las dos filas de proveedores decían
> solo «proveedores» y `proveedor_ambiguo`: ahora cubren también los oficios.
>
> **Sexta enmienda y bis (2026-09-30) y séptima (2026-10-01).** La fila del
> fichero hostil gana, en cada una, el caso que midió su review: la celda con
> estilo lejana (R115), los rangos que se expanden al cargar (R115 ampliado) y
> los millones de elementos pequeños dentro de 20 MiB (R117). Hasta la séptima,
> la fila daba a entender que los topes de tamaño acotaban el coste; no lo
> hacían.

### 0.2 · Rigor `critico`

Por el cruce con Sigrid, la base compartida y la entrada de ficheros de fuera.
Implica fase RED, cobertura ≥ 80 % de las líneas cambiadas y **cero
supervivientes** de mutación sin justificación aceptada por el humano. Los
tests no tocan red, base de datos ni IA; lo que exige Sigrid o PostgreSQL real
es `MANUAL (humano)` (T2, T16, T27, T28, T29).

## 1 · Lo que se sabe y lo que falta medir

**Se sabe** (diccionario de Sigrid y contrato de §8.9):

- `upv` (`con.tip 707`) cuelga de la obra por `upv.obride`; su código y su nombre
  están en `con.cod` / `con.res` del propio `ide`. En la 0677 hay 15 unidades
  con forma `0677.03VILLA N.` y nombre «Viviendas Bloque Villa N», **sin nombres
  de persona** (medido en F-013, T3).
- Los oficios de una obra están en `obrofc` (`obride` → la obra, `ofcide` →
  `auxofc`, `prvide` → proveedor); una fila por oficio **y proveedor**, así que
  un mismo oficio se repite. En la 0677 hay 39 filas (doc. 04 §5).
- `auxofc` tiene `cod` (24), `res` (48) y `fecbaj`. `prv` tiene `cif` (24) y
  `raz` (razón social, 128); su código y nombre, en `con.cod` / `con.res`.
  Sigrid **duplica fichas de proveedor al actualizarlas**; el criterio conocido
  para reconocerlas es el CIF (`sigrid_api.md` §9.8).
- `rcp.resubi` es **texto libre de 48** caracteres; `rcp.texurg`, texto de 32.
  El desplegable de ubicación que enseña Sigrid **no** tiene catálogo conocido
  (`auxubi` es de almacén). `upv.espacios` (texto de 255) podría ser su origen:
  **no está medido**.
- §8.9 admite `descripcion` 1–128, `descripcion_larga` libre, `ubicacion` ≤ 48,
  `oficio` que tiene que estar en `obrofc` de la obra, `intervinientes`
  `{oficio, proveedor?}` resueltos contra `obrofc` (varios proveedores sin
  indicar → `interviniente_ambiguo`), y **no** tiene campo de urgencia.
- En el maestro de obras hay códigos repetidos (la 0677 tiene dos filas; solo
  una con unidades de posventa, F-013 §4.7).

**Falta medir** (Bloque 0, solo lectura, T1–T3; y T8 con la función del
dominio): cuántas unidades, oficios y proveedores tiene la 0677; cuántos
proveedores comparten CIF o nombre (en la obra y, si es barato, en todo el
maestro); si el catálogo de oficios tiene el mismo problema; qué ubicaciones
escribe hoy Posventa en `rcp.resubi` y qué hay en `upv.espacios`. **Si la
medición desmiente algo de este diseño, se vuelve al spec-author.**

> **Enmienda del 2026-09-28.** Se añaden los proveedores y el CIF.
>
> **Tercera enmienda del mismo día.** Falta medir además las **familias** de
> los proveedores (`confam`, `auxfam`), su cruce con `auxofc`, `entfam` y
> `prv.ofcide`: §16.1 dice lo que se sabe de esas tablas y §16.2 lo que se
> mide.
>
> **Cuarta enmienda del mismo día · lo medido en T2.** 15 unidades
> `0677.03VILLA N.` con `con.res` «Viviendas Bloque Villa N», sin nombres de
> persona; `upv.espacios` vacío. `obrofc`: 39 filas, 31 oficios, **0 de
> baja**, 36 proveedores, y 3 filas **sin proveedor** (`0133`, `0144`,
> `0166`, justo tres de los oficios del Excel). Oficios parecidos en la obra:
> `0046`/`0143`, `0085`/`0166`, `0033`/`0133`. Proveedores parecidos: 0 en la
> obra y en los 526 de `obrofc`; 793 grupos por CIF y 530 por nombre en el
> maestro. `confam`/`auxfam`/`entfam` vacías; las familias son `conact` →
> `auxpronat` (§16). Ubicaciones: 44 `rcp.resubi` distintas, con variantes.
> Falta medir `conact`/`auxpronat` (T1 reabierta).

## 2 · Ficheros

Rutas relativas a `services/postventa-api/` salvo que se diga otra cosa.

### 2.1 · A crear

| Fichero | Capa | Qué |
|---|---|---|
| `domain/models/plantilla_incidencias.py` | domain | Contrato de la plantilla: identificador, versión, cabecera, topes, catálogo, etiquetas, enumeraciones (§4.1) |
| `domain/models/importacion.py` | domain | Libro leído, reconocimiento, validación de filas, clave de duplicado, grupos (§4.2–§4.5) |
| `domain/models/equivalencias.py` | domain | El mecanismo de equivalencias, hoy para el catálogo `oficio` y con la costura para F-050 y F-039: normalización de nombres, propuesta de grupos, grupos vigentes, etiqueta y resolución a código (§15). *Quinta enmienda: decía «para los dos catálogos»* |
| `domain/ports/catalogo_obra.py` | domain | `CatalogoObraPort` (§5.1) |
| `domain/ports/hoja_calculo.py` | domain | `GeneradorPlantillaPort`, `LectorPlantillaPort` (§5.2) |
| `domain/ports/bandeja.py` | domain | `BandejaPort` (§5.3) |
| `domain/ports/equivalencias.py` | domain | `EquivalenciasPort` (§15.4) |
| `application/pipelines/catalogo_obra.py` | application | Lee el catálogo, le aplica los grupos vigentes y las decisiones del dominio (§7.1) |
| `application/pipelines/plantilla.py` | application | Genera la plantilla de una obra (§7.2) |
| `application/pipelines/contexto_importacion.py` | application | `ContextoImportacion` (§7.3) |
| `application/pipelines/paso_importacion.py` | application | Los seis pasos de la importación (§7.3) |
| `application/pipelines/equivalencias.py` | application | Propuestas y registro de decisiones, de los dos catálogos (§15.5) |
| `config/plantilla_incidencias.yaml` | config | Listas cerradas y textos de la plantilla (§3.4) |
| `infrastructure/documentos/plantilla_yaml.py` | infrastructure | Carga y valida el YAML anterior |
| `infrastructure/documentos/excel_openpyxl.py` | infrastructure | Generador (plantilla y Excel de errores) y lector con `openpyxl` (§5.2). **Único** módulo del servicio que importa `openpyxl`, junto a los scripts |
| `infrastructure/sigrid/consultas_catalogo.py` | infrastructure | El SQL del catálogo, puro (§6.3) |
| `infrastructure/sigrid/catalogo_obra.py` | infrastructure | Adaptador de solo lectura sobre `POST /api/sql/read` (§5.1) |
| `infrastructure/persistencia/sql/12_importaciones.sql` | infrastructure · schema `postventa` | §6.1 |
| `infrastructure/persistencia/sql/13_bandeja_incidencias.sql` | infrastructure · schema `postventa` | §6.1 |
| `infrastructure/persistencia/sql/14_decisiones_equivalencia.sql` | infrastructure · schema `postventa` | §6.1, §15.4 |
| `infrastructure/persistencia/sentencias_bandeja.py` | infrastructure | SQL de la bandeja y de las decisiones de equivalencia, puro (§6.2) |
| `infrastructure/persistencia/repositorio_bandeja_pg.py` | infrastructure | `BandejaPort` y `EquivalenciasPort` sobre PostgreSQL |
| `interface_adapters/api/plantilla.py` | interface | Handler de `GET /api/plantilla` |
| `interface_adapters/api/importar.py` | interface | Handler de `POST /api/importaciones`; compone la importación |
| `infrastructure/documentos/lector_aislado.py` | infrastructure | *Octava enmienda.* `LectorPlantillaAislado` (implementa `LectorPlantillaPort`): pasos baratos en el padre, lectura por el ejecutor, validación del JSON, semáforo de una plaza. **No importa `openpyxl`** (§5.2, «La lectura aislada») |
| `infrastructure/documentos/ejecutor_aislado.py` | infrastructure | *Octava enmienda.* `EjecutorAislado` real con `multiprocessing` (`forkserver` en Linux, `spawn` en Windows), topes de 30 s y 1 GiB (`setrlimit` en Linux) y canal acotado. *Novena enmienda:* el hijo se pone además un tope de CPU (`RLIMIT_CPU`, los segundos más 5), solo en Linux |
| `tests/test_f036_lector_aislado.py` | tests | *Octava enmienda.* R118–R120 con un doble del ejecutor y con el ejecutor real (memoria, solo en Linux) |
| `interface_adapters/api/bandeja.py` | interface | Handler de `GET /api/bandeja` |
| `interface_adapters/api/equivalencias.py` | interface | Handlers de `GET /api/catalogos/propuestas` y `POST /api/catalogos/decisiones` |
| `scripts/migracion_f036.py` | script | Lógica **pura y testeable** de la migración (§10) |
| `scripts/migrar_excel_f036.py` | script | CLI fina sobre la anterior; `print()` permitido |
| `scripts/migracion_f036_correcciones.yaml` | datos | La **propuesta** de correcciones, fila a fila (§10.2); **sin nombres de proveedor** |
| `scripts/medir_catalogos_f036.py` | script | Aplica `proponer_grupos` a los oficios del JSON de T2 e imprime **solo recuentos** (T8). *Quinta enmienda: ya no a los proveedores* |
| `infra/26_catalogos_plantilla_sigrid.ps1` (raíz) | infra | Medición de solo lectura y catálogo de una obra a JSON fuera del repo (§1, §10.3) |
| `services/postventa-front/importar.html` | front | La página de importación (§9) |
| `services/postventa-front/oficios.html` | front | La página de oficios repetidos (§15.6). *Quinta enmienda: era `catalogos.html`, con oficios y proveedores* |
| `services/postventa-front/js/importacion.js` | front | Lógica pura de la importación + componente Alpine |
| `services/postventa-front/js/oficios.js` | front | Lógica pura de la página de oficios + componente Alpine *(era `js/catalogos.js`)* |
| `progress/explore_F-036.md` | progress | Lo medido en T2 y T8, **sin identificadores ni nombres** |
| `progress/migracion_F-036.md` | progress | Informe de revisión de la migración, lo genera el script (§10.4) |
| Tests | — | §14 |

### 2.2 · A modificar

| Fichero | Qué cambia |
|---|---|
| `requirements.txt` | `openpyxl>=3.1,<4.0` y `defusedxml>=0.7,<1.0` (con `defusedxml` instalado, `openpyxl` parsea el XML sin entidades externas) |
| `domain/models/errores.py` | Errores nuevos (§4.6) |
| `infrastructure/sigrid/fabrica.py` | `construir_catalogo_obra(ajustes)`; misma comprobación de configuración que `construir_ubicaciones` y **sin** mirar `CIERRE_HABILITADO` |
| `infrastructure/persistencia/fabrica.py` | `construir_bandeja(ajustes)` con la misma conexión y esquema que `construir_repositorio` |
| `function_app.py` | Cinco rutas (`plantilla` GET, `importaciones` POST, `bandeja` GET, `catalogos/propuestas` GET, `catalogos/decisiones` POST), en `ANONYMOUS` como las demás, y su línea en la docstring de cabecera |
| Tests que fijan la lista de ficheros DDL o de rutas (`test_f0xx_ddl_orden`, `test_f010_endpoints_protegidos`…) | Se amplían con lo nuevo, **sin** relajar lo que comprueban |
| `services/postventa-front/js/api.js` | `descargarPlantilla(obra)`, `importarExcel(fichero, usuarioOid)`, `bandeja(obra, limite)`, `propuestasCatalogos(obra)`, `decidirCatalogos(cuerpo)` |
| `services/postventa-front/index.html` | Dos enlaces en la cabecera: `importar.html` y `oficios.html` (D-1) |
| `services/postventa-front/README.md` | Las páginas nuevas |
| `docs/ARCHITECTURE.md` | Sección «Entrada de incidencias (F-036)» y las filas de `sigrid-api` y PostgreSQL de la tabla de sistemas (R61) |
| `docs/INTEGRACION.md` | §1 (lecturas nuevas), §2 (tres tablas), §7 (texto libre de la propiedad y nombres de proveedor), §8 (cinco endpoints) (R60) |
| `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` | Copia refrescada de `docs/INTEGRACION.md` (regla 1 de `azure-apps`), commit local en aquel repositorio |

> **Enmienda del 2026-09-28 (§2.1 y §2.2).** Se añaden `proveedores.py` (dominio,
> aplicación e interfaz), el puerto de equivalencias, `14_decisiones_proveedor.sql`,
> `medir_proveedores_f036.py`, `proveedores.html` y `js/proveedores.js`, y las
> dos rutas y dos métodos de `api.js` de proveedores. `function_app.py` pasa de
> tres rutas a cinco e `index.html` de un enlace a dos.

> **Segunda enmienda del 2026-09-28 (§2.1 y §2.2).** Lo que la primera
> enmienda llamó «de proveedores» se generaliza a los dos catálogos y se
> renombra: `proveedores.py` → `equivalencias.py` (dominio, aplicación e
> interfaz), `equivalencias_proveedor.py` → `equivalencias.py`
> (`EquivalenciasProveedorPort` → `EquivalenciasPort`),
> `14_decisiones_proveedor.sql` → `14_decisiones_equivalencia.sql`,
> `medir_proveedores_f036.py` → `medir_catalogos_f036.py`,
> `proveedores.html` → `catalogos.html`, `js/proveedores.js` →
> `js/catalogos.js`, las rutas `proveedores/*` → `catalogos/*` y los métodos
> de `api.js` `…Proveedores` → `…Catalogos`. Ninguno existía todavía.

> **Quinta enmienda del 2026-09-29 (§2.1 y §2.2).** Sale `cobertura.py`
> (actividades, a F-039); `catalogos.html` y `js/catalogos.js` pasan a
> `oficios.html` y `js/oficios.js`; `medir_catalogos_f036.py` mide solo
> oficios. Las rutas y los métodos de `api.js` (`/api/catalogos/*`,
> `propuestasCatalogos`, `decidirCatalogos`) no cambian de nombre: son el
> punto de entrada genérico que reutilizarán F-050 y F-039.

### 2.3 · Lo que NO se toca (y tienta)

- `infrastructure/sigrid/cliente.py`, `escrituras.py`, `graficos.py`: son las
  escrituras en el ERP. El adaptador nuevo **importa** de `cliente.py` lo mismo
  que importa `ubicacion.py` (cliente HTTP, `ErrorDeSigrid`, `es_transitorio`,
  `CORRECTOS`, `ENTORNOS_CON_CIERRE`) y no copia nada.
- `infrastructure/sigrid/consultas_ubicacion.py` y su `SQL_UNIDADES_DEL_CODIGO`:
  se parecen a lo que hace falta, pero son de F-013 y su test los fija carácter
  a carácter. El catálogo lleva su propio SQL.
- `infrastructure/persistencia/sentencias.py` y `repositorio_pg.py`: los puertos
  nuevos van en módulos propios. Tocarlos arrastraría la mutación de
  F-005…F-034.
- `RepositorioPartesPort`, `ErpPort`, `UbicacionPort`: ni un método más.
- Los pasos del circuito de partes (`paso_*.py` de F-002…F-034) y sus handlers.
- `infra/08_lectura_sigrid_comun.ps1`: se usa tal cual, **salvo**
  `Invoke-SigridLectura`, que T1 bis (`1b3edfb`) cambió para decodificar la
  respuesta de la pasarela en UTF-8 (R111). Fuera de esa función el fichero es
  el de `dev`, y `test_f036_alcance_cerrado.py` lo exige así.

  > **Sexta enmienda del 2026-09-30 (O-2, B6-19).** Decía «se usa tal cual»,
  > sin la excepción de R111.
- La rama `feature/F-035-portal-posventa`: ni se mergea ni se toca.
- `.env`, `local.settings.json`, `infra/00_vars_postventa.ps1`: F-036 no añade
  variables (R49).
- El maestro de proveedores y el catálogo de oficios **de Sigrid**: ni se
  fusionan ni se corrigen desde aquí (§15.1). *(Segunda enmienda del
  2026-09-28: decía solo «el maestro de proveedores».)*

## 3 · La plantilla, por dentro

### 3.1 · Hojas

| Hoja | Estado | Contenido |
|---|---|---|
| `Incidencias` | visible, **primera y activa** | Cabecera en la fila 1 (R2); filas 2–1001 con validaciones (R3, R4); paneles inmovilizados en `A2`; ancho de columna y ajuste de texto; filtro automático en la cabecera |
| `Instrucciones` | visible, segunda | Título con la obra (`<código> · <nombre de la obra>`), los textos de §3.4 y una tabla de 2–3 ejemplos (R5) |
| `_catalogos` | `veryHidden` | Una columna por lista: etiquetas de unidades, ubicaciones, etiquetas de **grupos** de oficios, pares grupo de oficio · proveedor *(quinta enmienda: sin grupos de proveedor)*, urgencias, listados. Rangos con nombre para las validaciones. *(Segunda enmienda del 2026-09-28: decía «etiquetas de oficios, pares oficio · proveedor».)* |
| `_plantilla` | `veryHidden` | Pares clave/valor: `identificador`, `version`, `obra_codigo`, `generada_at_utc` y, solo en un Excel de errores, `importacion_origen` (R6, R62) |

`veryHidden` y no `hidden`: una hoja oculta se muestra con dos clics y quien la
toque rompe los desplegables; `veryHidden` solo se muestra con VBA.

**Por qué «Incidencias» primero**: es donde se trabaja cada vez; las
instrucciones se leen una. La cabecera de cada columna lleva además un
**mensaje de entrada** (la validación de datos lo enseña al pinchar la celda),
que es la ayuda que se ve sin cambiar de hoja.

### 3.2 · Columnas

| Columna | Obligatoria | Valor | Se guarda como |
|---|---|---|---|
| `Unidad` | **Sí** | Tasado: etiquetas de las unidades de la obra (R8) | código y nombre de la unidad |
| `Ubicación` | No | Tasado: lista cerrada (§3.4) | la etiqueta (≤ 48) |
| `Descripción corta` | **Sí** | Texto libre 1–128 | texto de una línea |
| `Detalle` | No | Texto libre ≤ 2000 | texto con saltos de línea |
| `Oficio` | No | Tasado: **grupos** de oficios de la obra (R92, R12, R13) | código (o ambiguo, R93, R94) y etiqueta del grupo |
| `Proveedor` | No | Tasado: pares `<grupo de oficio> · <proveedor>` sacados **solo** de `obrofc` de la obra (R71, R72) | código y nombre del proveedor *(quinta enmienda: decía «grupo de proveedor» y «código (o ambiguo)»)* |
| `Urgencia` | No | Tasado: `Urgente` / `Peligro para la seguridad` (vacío = normal) | `urgente` / `seguridad` |
| `Listado` | No | Tasado: `Primer listado` / `Segundo listado` | `primero` / `segundo` |
| `Errores (lo rellena el sistema)` | — | Bloqueada; vacía en la plantilla, rellena en el Excel de errores | nada: se ignora (R66) |

Topes: 128 es `con.res` y la `descripcion` de §8.9; 48 es `rcp.resubi`; 2000 es
propio (D-11): `rcp.tex` es ilimitado y el tope solo protege la bandeja y el
volcado de un texto pegado sin querer.

**La columna `Listado` es una propuesta aprobada (D-5)**: ayuda a la pregunta
abierta de F-040 —qué regla elige entre el tipo `0002 PRIMER LISTADO
POSTVENTA` y el `0003`—, pero F-036 **no** la traduce a ningún tipo de Sigrid.

> **Enmienda del 2026-09-28.** Se añaden `Proveedor` y `Errores`, y la columna
> «Valor» dice «tasado» donde antes decía «desplegable»: el desplegable ya no es
> una ayuda, es el único valor admitido (decisión 7). `Ubicación` se guardaba
> como «etiqueta canónica», que presuponía casado normalizado.
>
> **Segunda enmienda del mismo día.** `Oficio` decía «oficios de la obra (R8,
> R12, R13) · código y nombre del oficio» y `Proveedor`, «pares `<oficio> ·
> <proveedor>` · código (o ambiguo, R75)»: los dos son ahora grupos.

#### 3.2.1 · Por qué el proveedor va en pares y no en un desplegable dependiente (D-16)

El desplegable «solo los proveedores del oficio elegido» se hace en Excel con
una **fórmula de validación** —`INDIRECT` sobre un rango con nombre por oficio,
o `OFFSET` + `MATCH` + `COUNTIF` sobre una tabla ordenada— y `openpyxl` la
escribe sin problema. No se propone por defecto porque es frágil justo donde
esta plantilla no puede serlo: con `Oficio` vacío la fórmula da error y cada
programa reacciona distinto (Excel de escritorio, Excel en la web y LibreOffice
no se comportan igual); se rompe si alguien ordena o pega filas; y
`INDIRECT` depende de que los nombres de rango sobrevivan a guardar con otro
programa.

La alternativa por defecto no necesita ninguna fórmula: **una sola lista de
pares** `Carpintería de madera · <proveedor>`, ordenada por oficio, así que al
desplegar quien rellena ve los proveedores **agrupados por su oficio**. El
importador comprueba que el grupo de oficio del par sea el de la columna
`Oficio` (R74). En la 0677 son del orden de 39 opciones, menos si se
confirman grupos. La parte de oficio del par es **exactamente** la etiqueta
del desplegable de `Oficio` (R92), así que quien rellena ve el mismo nombre
en las dos columnas. Si el humano prefiere el dependiente, se implementa con
`OFFSET`/`MATCH` y se prueba a mano en los tres programas en T28 (D-16).

> **Segunda enmienda del 2026-09-28.** Decía «que el oficio del par sea el
> de la columna `Oficio`» y la prueba manual era T26.

### 3.3 · Protección

La hoja `Incidencias` se protege **sin contraseña** con las celdas de datos
desbloqueadas —salvo `Errores`— y permitidos insertar y borrar filas, ordenar y
filtrar: la cabecera no se cambia por accidente, y nadie cree que eso sea
seguridad. Las hojas `veryHidden` también se protegen. Pegar desde otro libro
se salta la validación de Excel, y Excel compara las listas **sin distinguir
mayúsculas** al teclear: por eso **el importador valida todo otra vez**, exacto
(§4.3).

### 3.4 · `config/plantilla_incidencias.yaml`

Parametrización versionada (`docs/CONVENTIONS.md`), cargada y validada por
`infrastructure/documentos/plantilla_yaml.py`. **No lleva ningún nombre de
proveedor ni de persona.**

- `ubicaciones`: la lista cerrada. **Desde la cuarta enmienda (D-3,
  decidida por la medición)**: sale de las **44 `rcp.resubi` distintas** de la
  0677, normalizadas —variantes del mismo sitio unidas (`baño 3` / `bao 3`,
  `cuarto plancha` / `Cuarto de plancha`, `terraza instalaciones` / `terraza
  instaciones`, `lavandería` / `lavanderçia/tendedero`), mayúscula inicial y
  tildes correctas— y **no** de `upv.espacios`, que está vacío. Lo que la
  migración necesite y no esté entre ellas se añade en T6 marcado para que lo
  revise el humano. La lista que sigue era la **propuesta inicial** de antes
  de medir y queda solo como referencia:
  `General (toda la unidad)`, `Vestíbulo`, `Pasillo`, `Salón`, `Comedor`,
  `Sala / estudio`, `Cocina`, `Office`, `Despensa`, `Lavandería`,
  `Cuarto de plancha`, `Dormitorio 1`…`Dormitorio 6`,
  `Baño del dormitorio 1`…`Baño del dormitorio 6`, `Vestidor del dormitorio 1`…
  `Vestidor del dormitorio 6`, `Terraza del dormitorio 1`…
  `Terraza del dormitorio 6`, `Baño 1`…`Baño 3`, `Aseo`,
  `Baño de planta baja`, `Escalera`, `Terraza`, `Patio`, `Sótano`, `Almacén`,
  `Garaje`, `Trastero`, `Tendedero`, `Fachada`, `Cubierta`, `Jardín`,
  `Zonas comunes`, `Otra (explicar en el detalle)`.
- `urgencias` y `listados`: `{codigo, etiqueta}`; los códigos tienen que ser los
  del `Enum` del dominio (el cargador lo comprueba).
- `textos`: los párrafos de «Instrucciones», los ejemplos y los mensajes de
  entrada y de error de cada columna.

El cargador falla (y el arranque del handler con él) si una ubicación pasa de
48, si dos ubicaciones son iguales normalizadas, o si un código de urgencia o
listado no es del dominio.

### 3.5 · El Excel de errores (añadido el 2026-09-28)

Es **la plantilla** de la obra, generada por el mismo `GeneradorPlantillaPort`
con el catálogo leído en esa importación (R62), con tres diferencias:

1. `Incidencias` lleva solo las filas con error, en su orden original y con los
   valores **tal como llegaron**, escritos como texto (una fórmula llega como su
   texto, sin el `=` interpretado; R63).
2. La columna `Errores` lleva, por fila, «Fila N del fichero subido ·
   `<columna>`: `<problema>` · …» (R63), y cada celda con error va con relleno
   de color y un comentario con su problema (R64). Escribir en una celda con
   validación un valor que no está en la lista es posible desde `openpyxl`: la
   validación solo actúa sobre lo que teclea una persona, así que quien abre el
   fichero ve el valor malo y, al corregirlo, el desplegable.
3. `_plantilla` añade `importacion_origen` (el `importacion_id`), solo
   informativo: el reconocimiento no lo mira.

`Instrucciones` añade un párrafo: «Este fichero trae solo las filas que no
entraron. Corrige las celdas marcadas y súbelo otra vez; lo que ya entró no se
duplica».

**Cómo se entrega**: en la propia respuesta de `POST /api/importaciones`, como
`excel_errores {nombre, contenido_b64}` (R65), igual que `POST /api/split`
devuelve los PDF en base64. Mil filas de errores son del orden de un centenar
de KB. **No se guarda** en el servidor (R68): ni en la base —no hay columnas
binarias, y llevaría texto libre de la propiedad— ni en SharePoint. Si se
pierde, se vuelve a subir el mismo fichero y se regenera (R39).

**Alternativa descartada**: un `GET /api/importaciones/{id}/errores` que lo
regenere. Obligaría a guardar las filas con error (texto libre) solo para
poder repetirlas, y no aporta nada que no dé volver a subir el fichero.

### 3.6 · Formato visual (añadido en la décima enmienda del 2026-10-02)

El humano abrió el `v2` de T28 y pidió un formato «limpio, ordenado, con
colores Ruesma». El líder hizo una muestra desechable fuera del repositorio
(no se versiona) y el humano la aprobó tal cual el 2026-10-02. Esta sección
es esa muestra, escrita: R121–R125 son el aspecto, R126 lo que **no** cambia
y R127 los topes.

> **Enmienda 10 bis del 2026-10-02.** La review 7 midió con Excel que la
> plantilla vacía imprimía 15 páginas de rejilla vacía (R7-2): los bordes y el
> gris estáticos en las 1.000 filas hacen que Excel las cuente como usadas.
> El humano decidió que el Excel **no se imprime** y que la plantilla vacía
> enseñe **la cabecera y una fila**. Cambia lo de esta sección marcado
> «10 bis»: el cuerpo pasa a formato condicional (las tres reglas, más abajo)
> y se quitan los ajustes de impresión. **No cambian** la cabecera, los
> colores, las fuentes, los anchos, «Instrucciones» ni las pestañas.

**Qué se toca y qué no.**

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` (infrastructure) | **Solo el generador**: las constantes de formato, `_incidencias` e `_instrucciones`, y el docstring del módulo. `RELLENO_ERROR` cambia de color; `ANCHOS` cambia de valores |
| `services/postventa-api/tests/test_f036_excel_generador.py` | Tests nuevos `test_f036_r121_…` a `test_f036_r126_…`, y los cuatro que fijaban el aspecto antiguo pasan a los valores nuevos (abajo, «Cómo se prueba») |
| `services/postventa-api/tests/test_f036_excel_lector.py`, `test_f036_lector_aislado.py` | Tests nuevos de ida y vuelta y de topes (R126, R127). Los que ya hay **no se tocan** |

*(10 bis.)* El Bloque 13 vuelve a tocar **solo** el generador de
`excel_openpyxl.py` (`_incidencias`, las constantes y el docstring del
módulo) y los tests de esos tres ficheros: los del Bloque 12 que fijaban el
cuerpo estático, la regla única de bandas y la impresión cambian a propósito
(lista en «Cómo se prueba»). Lo que «No se toca» de abajo sigue igual.

**No se toca**: el lector (`_abrir`, `_extraer`, `leer_en_hijo` y todo lo que
hay bajo «El lector» en `excel_openpyxl.py`), `lector_aislado.py`,
`ejecutor_aislado.py` y **sus constantes de topes**; el dominio
(`plantilla_incidencias.py`: `CABECERA`, `VERSION_PLANTILLA`,
`IDENTIFICADOR_PLANTILLA`, `TextosPlantilla`); `config/plantilla_incidencias.yaml`
(ningún texto cambia); `_catalogos`, `_metadatos` y `_validacion`; el puerto
`GeneradorPlantillaPort` (la firma de `generar` no cambia); el script de
migración (recibe el formato solo por usar el mismo generador, R55); el front.
**La versión de la plantilla sigue en `1`**: una versión nueva dejaría fuera
las plantillas ya descargadas, y el formato no cambia nada que el importador
lea (R126).

**Colores.** Los tokens de la identidad Ruesma de F-035
(`git show feature/F-035-portal-posventa:services/postventa-front/css/styles.css`,
bloque `:root`), como ARGB opaco. Se **copian** como constantes: esa rama no
está fusionada, el generador es del backend y no puede leer una hoja de
estilos del front. Si la identidad cambia, se cambian aquí a mano.

| Constante | ARGB | Token de F-035 | Dónde se usa |
|---|---|---|---|
| `BURDEOS` | `FF9F2842` | `--rs-burdeos` | Cabeceras, banda de la obra, título de «Instrucciones», pestaña de «Incidencias» |
| `BURDEOS_FUERTE` | `FF7A1E33` | `--rs-burdeos-fuerte` | Borde inferior de las cabeceras |
| `ACERO` | `FF7B868C` | `--rs-acero` | Cabecera de `Errores`, pestaña de «Instrucciones» |
| `ACERO_100` | `FFDFE2E4` | `--rs-acero-100` | Líneas finas del cuerpo y de los ejemplos |
| `ACERO_TEXTO` | `FF5D676D` | `--rs-acero-texto` | Texto de la columna `Errores` |
| `TINTA` | `FF1D2024` | `--rs-tinta` | Texto del cuerpo, de los párrafos y de los ejemplos |
| `LIENZO` | `FFF3F4F5` | `--rs-lienzo` | Fondo «no editable» de la columna `Errores` |
| `BLANCO` | `FFFFFFFF` | `--rs-papel` | Texto de las cabeceras y sus bordes laterales |
| `ERROR_SUAVE` | `FFFEF2F2` | `--rs-error-suave` | Relleno de la celda con error (era el naranja `FFF4B084`) |
| `ERROR` | `FFB91C1C` | `--rs-error` | Texto de la celda con error |
| `BANDA` | `FFFAFAFB` | — (propio: entre `--rs-papel` y `--rs-lienzo`) | Bandas alternas |

Las pestañas van en RGB de seis cifras (`9F2842`, `7B868C`), que es como las
admite `sheet_properties.tabColor`. La hoja de estilos de F-035 dice que el
burdeos es marca y nunca un estado: por eso el error usa los tokens de error y
no el burdeos.

**Tipografía**: `FUENTE = "Calibri"` en todo. Las fuentes de la marca
(`Bricolage Grotesque`, `Archivo`) no están instaladas en los equipos de la
propiedad, y Excel las sustituiría por otra sin avisar.

**«Incidencias».**

| Zona | Fuente | Relleno | Bordes | Alineación | Alto / ancho |
|---|---|---|---|---|---|
| Cabecera, fila 1, columnas A–H | Calibri 11, negrita, `BLANCO` | `BURDEOS` | izquierdo y derecho `thin` `BLANCO`; inferior `medium` `BURDEOS_FUERTE` | horizontal izquierda, vertical centro, ajuste, sangría 1 | fila de **34** |
| Cabecera de `Errores`, I1 | igual | `ACERO` | igual | igual | — |
| Cuerpo, filas 2–1001, A–H | Calibri 10,5, `TINTA` (estática) | **ninguno estático**; bandas por la regla 3 *(10 bis)* | **ninguno estático**; los cuatro `thin` `ACERO_100` por la regla 1 *(10 bis)* | vertical arriba, sangría 1; ajuste solo en C y D (estática) | — |
| Columna `Errores`, I2–I1001 | Calibri 10,5, `ACERO_TEXTO` (estática) | **ninguno estático**; `LIENZO` por la regla 2 *(10 bis)* | **ninguno estático**; regla 1 *(10 bis)* | vertical arriba, sangría 1, ajuste (estática) | — |
| Celda con error (R64) | Calibri 10,5, `ERROR` (estática) | `ERROR_SUAVE` (estático) | **ninguno estático**; regla 1 *(10 bis)* | como su columna | — |

*(10 bis.)* «Estático» es el estilo de la celda; lo demás es formato
condicional. El estilo estático que queda en el cuerpo (fuente y alineación)
no se ve en una celda vacía; el desbloqueo y el `@` no son aspecto (R126).

- **Anchos** (`ANCHOS`): `Unidad` 30, `Ubicación` 26, `Descripción corta` 48,
  `Detalle` 56, `Oficio` 28, `Proveedor` 40, `Urgencia` 24, `Listado` 16,
  `Errores` 50. *(Eran 30, 24, 50, 60, 28, 45, 24, 18 y 60.)* Suman menos que
  antes para que la hoja quepa a lo ancho en un A4 apaisado sin que la letra
  quede ilegible. *(10 bis: ya no se imprime, pero los anchos son los de la
  muestra aprobada y no cambian; el comentario de `ANCHOS` en el código deja
  de hablar del A4.)*
- **Cuadrícula**: `ws.sheet_view.showGridLines = False`. **Pestaña**:
  `ws.sheet_properties.tabColor = "9F2842"`.
- **Las tres reglas del cuerpo** *(10 bis; R122, R123)*. Sustituyen a la
  regla única de bandas de la décima y a los bordes y el gris estáticos. Se
  añaden con `ws.conditional_formatting.add(rango, FormulaRule(...))`, **en
  este orden**: `openpyxl` 3.1 numera la prioridad por orden de alta (1, 2,
  3; comprobado), y los tests fijan el número.

  | Regla | Rango (`sqref`) | Fórmula | Formato (`dxf`) | Prioridad | Dónde |
  |---|---|---|---|---|---|
  | 1 · líneas | `A2:I1001` | `OR(ROW()=2,COUNTA($A2:$I2)>0)` (`FORMULA_PINTADA`) | `border=_borde_fino()`: los cuatro `thin` `ACERO_100`; sin relleno ni fuente | 1 | plantilla, `v2` y Excel de errores |
  | 2 · gris de `Errores` | `I2:I1001` | la misma, `FORMULA_PINTADA` | `fill=PatternFill(fill_type="solid", bgColor=LIENZO)`; sin borde ni fuente | 2 | plantilla, `v2` y Excel de errores |
  | 3 · bandas | `A2:H1001` | `AND(MOD(ROW(),2)=1,COUNTA($A2:$I2)>0)` (`FORMULA_BANDAS`, valor nuevo) | `fill=PatternFill(fill_type="solid", bgColor=BANDA)`; sin borde ni fuente | 3 | **solo** si `not any(fila.errores for fila in filas)` |

  - **La fórmula.** Es relativa a la celda de arriba a la izquierda de cada
    rango: con las columnas fijas (`$A`, `$I`) y la fila libre, en la fila
    *n* evalúa `COUNTA($An:$In)` en cualquiera de las columnas del rango, y
    vale igual para `I2:I1001` que para `A2:I1001`. `ROW()=2` es posición,
    no contenido: la fila 2 se ve siempre, también después de ordenar o de
    borrar filas. `COUNTA` cuenta las celdas no vacías (texto, aunque sea un
    espacio); no hay fórmulas de celda (R7), así que no cuenta cadenas
    vacías calculadas. Se cuenta `I` además de `A`–`H` para que una fila del
    Excel de errores se pinte siempre entera, aunque sus datos llegasen
    vacíos; en la plantilla, `I` está bloqueada y manda lo que se escribe en
    `A`–`H`. Funciones de antes de 2007 (`OR`, `AND`, `ROW`, `MOD`,
    `COUNTA`): sin prefijo `_xlfn.`. El XML las guarda en inglés y con comas;
    Excel en español las enseña como `O(FILA()=2;CONTARA($A2:$I2)>0)`.
  - **Convivencia.** Ninguna lleva `stopIfTrue`. Excel aplica todas las
    reglas verdaderas y, si dos fijan la misma propiedad, gana la de más
    prioridad; aquí ninguna coincide en propiedad y celda (bordes en `A`–`I`;
    relleno gris solo en `I`; relleno de banda solo en `A`–`H`), así que el
    orden fija el fichero y no cambia el aspecto. El **rojo de la celda con
    error es estático** (`RELLENO_ERROR`, `FUENTE_ERROR`) y convive con la
    regla 1 (bordes, otra propiedad) y con la 2 (otra columna); con la 3
    chocaría —el relleno de una regla se pinta encima del fijo—, y por eso
    la 3 no va en el Excel de errores (R123, alternativa descartada allí).
  - **Lo que se ve.** Plantilla vacía: la cabecera y la fila 2 (con sus
    líneas y el gris de `I2`; la 2 es par, sin banda); al escribir en la 3,
    la 3 se pinta, con banda. `v2` de T28: sus filas con líneas y bandas, y
    nada debajo. Excel de errores: sus filas con líneas, el gris de `I` y
    el rojo en las celdas con error.
  - **Insertar en la fila 2.** Si alguien inserta una fila **encima** de la
    2, Excel desplaza los rangos de las reglas igual que los de las
    validaciones de datos (R3): la nueva fila 2 queda fuera de ambos. Es el
    comportamiento que la plantilla ya tenía con las validaciones; no se
    trata aparte.
  - *Alternativas descartadas.* (1) Lo de la décima, estático en las 1.000
    filas: Excel las da por usadas y enseña una rejilla vacía (R7-2).
    (2) Preparar solo las filas con datos más una: rompe R126 (desbloqueo,
    `@` y desplegables en las 1.000) y el tope de R3. (3) Una tabla de Excel
    (`ListObject`) que crezca sola: parte nueva en el ZIP (`xl/tables/`), y
    en una hoja protegida la tabla no se amplía al escribir debajo.
    (4) Estilo condicional también para la fuente: un `dxf` no fija ni el
    nombre ni el tamaño de la fuente, y la fuente no se ve en una celda
    vacía; se queda estática.
- **Lo que se conserva tal cual** (R126): `_texto` y el prefijo de comilla,
  `FORMATO_TEXTO` y `Protection(locked=False)` en las columnas de datos, las
  validaciones, `freeze_panes`, `auto_filter`, la protección de la hoja y el
  comentario de la celda con error. El formato **añade** atributos de estilo
  a las celdas que el generador ya crea (las 9 columnas de las filas 1–1001):
  no crea ninguna celda más en «Incidencias». *(10 bis: las 9.000 celdas
  del cuerpo se siguen creando, con fuente, alineación, protección y `@`;
  pierden el borde y, en `I`, el relleno.)*

**Sin impresión** *(10 bis; R125)*. Se **quita** el bloque «Impresión
(R125)» de `_incidencias` entero —`page_setup.orientation`, `paperSize`,
`fitToWidth`, `fitToHeight`, `pageSetUpPr.fitToPage`, `print_title_rows`,
`page_margins.left/right` y `oddFooter`— y las constantes `MARGEN_LATERAL`
y `PIE_DE_PAGINA`. Ninguna hoja recibe ajustes de impresión, y
`workbook.xml` deja de llevar `_xlnm.Print_Titles`. El lector **no cambia**:
sigue aceptando un fichero con ajustes de impresión puestos por el usuario
en Excel, legítimos o no; uno hostil (`Print_Titles` de 4 MB, R7-4) lo para
el tope del hijo, como cualquier otro fichero (R118). La impresión a PDF de
los partes de trabajo es F-044 y no tiene que ver con este Excel.

> *Texto de la décima, retirado:* A4 apaisado, una página de ancho y las de
> alto que hagan falta, `print_title_rows = "1:1"` (el nombre definido
> reservado `_xlnm.Print_Titles`), márgenes laterales de 0,4 y el pie
> «Posventa · Construcciones Ruesma · página &P de &N».

**«Instrucciones».** Cuadrícula oculta y pestaña `7B868C`. Las columnas de la
tabla son las 8 de `COLUMNAS_DE_DATOS` (A–H).

| Zona | Fuente | Relleno | Bordes | Alineación | Alto |
|---|---|---|---|---|---|
| Fila 1, la obra, A–H | Calibri 15, negrita, `BLANCO` | `BURDEOS` | — | vertical centro, sangría 1 | **38** |
| Fila 2, el título (`textos.titulo`), A2 | Calibri 13, negrita, `BURDEOS` | — | inferior `medium` `BURDEOS` en A–H | vertical centro, sangría 1 | **28** |
| Párrafos (columna A) | Calibri 11, `TINTA` | — | — | ajuste, vertical arriba, sangría 1 | `max(20, 16 * (len(texto) // 105 + 1) + 6)` |
| Cabecera de los ejemplos, A–H | Calibri 11, negrita, `BLANCO` | `BURDEOS` | los de la cabecera de «Incidencias» | vertical centro, sangría 1 | **26** |
| Filas de ejemplo, A–H | Calibri 10,5, `TINTA` | `BANDA` en la 2.ª, 4.ª… (relleno fijo) | los cuatro `thin` `ACERO_100` | ajuste, vertical arriba, sangría 1 | — |

- Anchos: A, **100** (no cambia); B–H, **28** *(eran 30)*.
- **El alto de los párrafos se calcula** porque Excel no ajusta solo el alto
  de una fila escrita por programa: 105 son los caracteres que caben en una
  línea de la columna A (ancho 100, Calibri 11), 16 los puntos por línea y 6
  el respiro. Vale para todos los párrafos: los de `textos.instrucciones`, el
  del Excel de errores (`textos.excel_errores`) y el de la obra sin oficios
  (`textos.sin_oficios`). La fila en blanco que separa los párrafos de los
  ejemplos se queda con el alto por defecto.
- En las filas 1 y 2 y en la cabecera de los ejemplos el formato crea las
  celdas B–H **sin valor** (solo estilo): una docena larga de celdas en una
  hoja que el lector no recorre (R115).

**Dónde vive cada constante.** Todas en `excel_openpyxl.py`, a nivel de
módulo, junto a las que ya hay (`ANCHOS`, `AJUSTADAS`, `FORMATO_TEXTO`,
`RELLENO_ERROR`), con nombre y sin números sueltos dentro de las funciones:

- los once colores de la tabla y `FUENTE`;
- `ANCHOS` (valores nuevos), `ANCHO_INSTRUCCIONES` (100) y
  `ANCHO_EJEMPLOS` (28);
- los tamaños: `PUNTOS_CABECERA = 11`, `PUNTOS_CUERPO = 10.5`,
  `PUNTOS_OBRA = 15`, `PUNTOS_TITULO = 13`, `PUNTOS_PARRAFO = 11`;
- los altos: `ALTO_CABECERA = 34`, `ALTO_OBRA = 38`, `ALTO_TITULO = 28`,
  `ALTO_CABECERA_EJEMPLOS = 26`, y los cuatro números del alto de un párrafo
  (`ALTO_MINIMO_PARRAFO = 20`, `PUNTOS_POR_LINEA = 16`,
  `CARACTERES_POR_LINEA = 105`, `RESPIRO_PARRAFO = 6`), con una función pura
  `_alto_de_parrafo(texto: str) -> int`;
- `RELLENO_ERROR` (ahora `ERROR_SUAVE`), `FUENTE_ERROR`, `FORMULA_BANDAS =
  "MOD(ROW(),2)=1"`, `MARGEN_LATERAL = 0.4` y `PIE_DE_PAGINA`.
- *(10 bis)* `FORMULA_PINTADA = "OR(ROW()=2,COUNTA($A2:$I2)>0)"` (nueva) y
  `FORMULA_BANDAS = "AND(MOD(ROW(),2)=1,COUNTA($A2:$I2)>0)"` (valor nuevo);
  **fuera** `MARGEN_LATERAL` y `PIE_DE_PAGINA`. Los rangos de las reglas se
  construyen con `PRIMERA_FILA`, `ULTIMA_FILA` y las letras de
  `COLUMNAS_DE_DATOS`/`CABECERA`, como el de las bandas de la décima, no como
  cadenas sueltas. El docstring del módulo deja de decir «ajustes de
  impresión en A4 apaisado» y dice que el cuerpo se pinta por formato
  condicional.

Los nombres son orientativos; lo que obliga es que cada valor de las tablas
esté en **una** constante con nombre y que los tests comprueben el valor
**literal** (no la constante importada): con rigor `critico`, una constante
que ningún test fija es un mutante que sobrevive. Los objetos de estilo
(`Font`, `PatternFill`, `Border`, `Alignment`) se construyen **una vez** por
zona y se comparten entre celdas, como hace hoy el generador con
`desbloqueada` y `ajuste`: `openpyxl` deduplica los estilos al guardar, y
`styles.xml` crece en unas decenas de elementos, no en miles.

**Cómo se prueba** (sin red ni disco: el libro se genera en memoria y se
vuelve a abrir con `openpyxl`, como el resto de `test_f036_excel_generador.py`):

- **Estilos** (`test_f036_r121_…` a `test_f036_r125_…`, en
  `test_f036_excel_generador.py`): por cada zona de las dos tablas, se leen
  de las celdas `font.name`, `font.sz`, `font.b`, `font.color.rgb`,
  `fill.fill_type`, `fill.fgColor.rgb`, los cuatro lados de `border` (estilo
  y color) y `alignment` (horizontal, vertical, ajuste, sangría), en la
  primera y en la última celda de la zona (fila 2 y fila 1001; columna A y
  columna H) y en la frontera (I1 frente a H1; I2 frente a H2); los anchos y
  altos, con sus valores literales; `sheet_view.showGridLines`,
  `sheet_properties.tabColor`; la regla condicional (una sola, su rango, su
  tipo, su fórmula y el color de su relleno) y que **no hay ninguna** en el
  Excel de errores; la celda con error (relleno y color de la fuente) frente
  a su vecina sin error; los ajustes de impresión, uno a uno, y el pie; el
  alto de un párrafo corto y de uno largo, y `_alto_de_parrafo` en sus
  fronteras (104, 105 y 210 caracteres).
- **Los cuatro tests que fijaban el aspecto antiguo** cambian de valor, a
  propósito: `test_f036_s3_1_anchos_de_las_columnas_de_incidencias` (los
  anchos), `test_f036_r5_disposicion_de_instrucciones` y
  `test_f036_r5_anchos_de_instrucciones` (el título de 14 a 15; los anchos de
  30 a 28) y `test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario`
  (las celdas no marcadas de la columna `Errores` llevan ahora relleno
  `LIENZO`: «sin relleno» pasa a valer solo para las columnas de datos).
- **Invariantes** (`test_f036_r126_…`): los tests de R2–R7, R12 y R62–R66
  siguen en verde sin tocarlos (salvo los cuatro de arriba); además, ida y
  vuelta por `LectorPlantillaOpenpyxl` y por `LectorPlantillaAislado` de una
  plantilla rellena y de un Excel de errores con formato; el mismo
  `LibroLeido` de un libro al que el test le quita el formato (reabrirlo en
  modo normal, borrar estilos, regla condicional y ajustes de impresión, y
  guardarlo); el conjunto de partes del ZIP, sin `xl/media/` ni imágenes; el
  XML de las hojas sin `<f>`; y los nombres definidos: los seis de las listas
  siguen ahí y resuelven a lo mismo.
- **Topes** (`test_f036_r127_…`): §5.2, «Los topes y el formato visual».

**Cómo se prueba, tras la enmienda 10 bis** (mismo método: en memoria, sin
red ni disco; manda sobre lo anterior donde choque):

- **Las reglas, leídas del libro generado** (`test_f036_r122_…`,
  `test_f036_r123_…`, en `test_f036_excel_generador.py`): con
  `load_workbook` normal, `list(ws.conditional_formatting)` de
  «Incidencias». En la plantilla vacía, en una rellena y en un libro como el
  `v2` (filas sin errores): **tres** elementos, en este orden, y de cada uno
  el `sqref` (`"A2:I1001"`, `"I2:I1001"`, `"A2:H1001"`), una sola regla,
  `type == "expression"`, `formula` (la lista con la cadena literal de la
  tabla), `priority` (1, 2, 3), `stopIfTrue` sin poner, y del `dxf`: en la
  1, los cuatro lados `thin` con color `FFDFE2E4` y `dxf.fill` y `dxf.font`
  vacíos; en la 2 y la 3, `fill.fill_type == "solid"` y `fill.bgColor.rgb`
  (`FFF3F4F5`, `FFFAFAFB`) y `dxf.border` y `dxf.font` vacíos. En el Excel de
  errores (alguna fila con errores): **dos**, la 1 y la 2, iguales. Y que
  las bandas dependen de que haya errores, no del origen (el test que ya
  existe, a las nuevas cuentas). En el XML: tres (o dos)
  `<conditionalFormatting`, cada `sqref` sin espacios, y
  `<dxfs count="3">` (o `"2"`).
- **Sin estilo visual estático en el cuerpo** (`test_f036_r122_…`): en la
  plantilla vacía, en una rellena y en el Excel de errores, en las filas 2,
  3, una intermedia y 1001 y en las columnas A, H e I, `border` sin ningún
  lado con estilo y `fill.fill_type` vacío; **salvo** la celda con error,
  que lleva `("solid", "FFFEF2F2")` y fuente `FFB91C1C`, también sin borde.
  Y lo estático que sigue: fuente Calibri 10,5 `FF1D2024` (en `I`,
  `FF5D676D`), alineación con su ajuste, desbloqueo y `@` en las columnas
  de datos, en las filas 2 y 1001.
- **Sin impresión** (`test_f036_r125_…`, para las **cuatro** hojas):
  `ws.print_area` vacío (`openpyxl` 3.1 devuelve `''`); `print_title_rows`
  y `print_title_cols` `None`; `page_setup.orientation`, `paperSize`,
  `scale`, `fitToWidth`, `fitToHeight` `None`; `pageSetUpPr` sin
  `fitToPage`; `print_options.horizontalCentered`, `verticalCentered`,
  `gridLines`, `headings` `None`; márgenes `(0.75, 0.75, 1.0, 1.0, 0.5,
  0.5)` (izquierdo, derecho, superior, inferior, encabezado, pie); los tres
  trozos de `oddHeader`, `oddFooter`, `evenHeader`, `evenFooter`,
  `firstHeader` y `firstFooter` `None`. En el XML de cada hoja, ni
  `<pageSetup`, ni `<printOptions`, ni `<headerFooter`, ni `<rowBreaks`, ni
  `<colBreaks`; en `xl/workbook.xml`, ningún `_xlnm.Print_` y, como nombres
  definidos, exactamente los seis de las listas más `_xlnm._FilterDatabase`.
  Es lo que pedía R7-1, ahora como ausencia de todo: las mutaciones M18
  (área `A1:I1001`), M18b (área `A1:I50`), M27 (`scale`), M28 (centrado) y
  M29 (margen superior), y volver a poner cualquier línea del bloque de la
  décima, tienen que caer.
- **Invariantes** (`test_f036_r126_…`): los que hay siguen; ida y vuelta por
  `LectorPlantillaOpenpyxl` y por `LectorPlantillaAislado` (hijo real) de
  una plantilla rellena y de un Excel de errores con el formato nuevo; el
  mismo `LibroLeido` sin el formato; y, **nuevo**, una plantilla con el
  **formato de la décima** construida en el test (`_con_formato_de_la_decima`,
  ayudante del test, no de producción: a la generada se le quitan las tres
  reglas y se le ponen los bordes `thin` `FFDFE2E4` en `A2:I1001` y el
  `LIENZO` en `I2:I1001` como estilo de celda, la regla única
  `MOD(ROW(),2)=1` en `A2:H1001` y los ajustes de impresión de la R125
  retirada con `print_title_rows = "1:1"`) que da el **mismo** `LibroLeido`
  por los dos lectores y valida con cero errores. La del formato antiguo
  (anterior a la décima) se sigue probando con el test que ya existe.
- **Los tests del Bloque 12 que cambian a propósito** (en rojo en T55,
  verdes en T56). Por nombre, según la tabla de la review 7; el implementer
  confirma la lista en su informe y no toca ninguno más:
  - `test_f036_excel_generador.py`: `…_r122_cuerpo_de_incidencias` (sin
    bordes estáticos), `…_r122_bandas_alternas_una_sola_regla_condicional_en_la_plantilla`
    y `…_r122_el_v2_sin_errores_lleva_las_bandas` (tres reglas),
    `…_r122_las_bandas_dependen_de_los_errores_y_no_del_origen` (cuentas
    nuevas), `…_r122_con_alguna_fila_con_error_no_hay_regla_condicional`
    (dos reglas, ninguna de bandas), `…_r123_la_columna_errores_va_en_gris_no_editable`
    (el gris por la regla 2; la fuente sigue estática),
    `…_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo` (sin borde
    estático), `test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario`
    (vuelve a «sin relleno estático» en todas las celdas sin error, también
    en `Errores`), `…_r125_impresion_de_incidencias` y
    `…_r125_instrucciones_sin_ajustes_de_impresion_propios` (a la ausencia
    de arriba; se pueden fundir en uno parametrizado por hoja);
  - `test_f036_lector_aislado.py`:
    `…_r127_la_plantilla_completa_lleva_una_regla_condicional_de_un_rango`
    (tres, de un rango cada una) y
    `…_r127_el_excel_de_errores_mas_grande_no_lleva_regla_condicional`
    (dos); el comentario que habla del nombre de los títulos de impresión;
  - `test_f036_excel_lector.py`: el ayudante que quita el formato puede
    seguir quitando ajustes de impresión (ya no hay; no estorba). Si algún
    test deja de tener sentido, decirlo en el informe en vez de borrarlo.
  - Ningún test de documentación (`test_f036_documentacion.py`) mira el
    texto de la spec ni el aspecto: no se rompe ninguno.

## 4 · Dominio puro

Sin `openpyxl`, sin `httpx`, sin `psycopg`, sin reloj (la hora entra por
parámetro). Lo vigila `test_f036_arquitectura.py`.

### 4.1 · `domain/models/plantilla_incidencias.py`

```python
IDENTIFICADOR_PLANTILLA = "ruesma.postventa-incidencias.plantilla-incidencias"
VERSION_PLANTILLA = 1
VERSIONES_SOPORTADAS: frozenset[int] = frozenset({1})
COLUMNA_ERRORES = "Errores (lo rellena el sistema)"
CABECERA: tuple[str, ...] = ("Unidad", "Ubicación", "Descripción corta", "Detalle",
                             "Oficio", "Proveedor", "Urgencia", "Listado", COLUMNA_ERRORES)
SEPARADOR_PAR = " · "   # entre oficio y proveedor en la columna Proveedor
MAX_DESCRIPCION = 128   # con.res y `descripcion` de sigrid-api §8.9
MAX_UBICACION = 48      # rcp.resubi
MAX_DETALLE = 2000      # propio (D-11)
MAX_FILAS = 1000
MAX_CODIGO_OBRA = 24    # `obra` de sigrid-api §8.9

class Urgencia(StrEnum): URGENTE = "urgente"; SEGURIDAD = "seguridad"
class Listado(StrEnum): PRIMERO = "primero"; SEGUNDO = "segundo"
class OrigenIncidencia(StrEnum): EXCEL = "excel"; WEB = "web"   # WEB: F-037 (D-13)

@dataclass(frozen=True)
class UnidadPosventa: codigo: str; nombre: str | None
@dataclass(frozen=True)
class OficioObra: codigo: str; nombre: str | None
@dataclass(frozen=True)
class ProveedorEnObra:                     # una fila de obrofc, ya con su proveedor
    oficio_codigo: str; proveedor_codigo: str | None; proveedor_nombre: str | None   # None: fila sin proveedor (cuarta enmienda)
    # quinta enmienda: sale `marca_cif` (era de la agrupación de proveedores, a F-050)
@dataclass(frozen=True)
class CatalogoObra:
    obra_codigo: str; obra_nombre: str | None
    unidades: tuple[UnidadPosventa, ...]; oficios: tuple[OficioObra, ...]
    proveedores: tuple[ProveedorEnObra, ...]
    # quinta enmienda: salen `actividades` y `arbol` (a F-039, §16)
@dataclass(frozen=True)
class Opcion: etiqueta: str; codigo: str
@dataclass(frozen=True)
class OpcionOficio:                        # una entrada del desplegable de Oficio (R92)
    etiqueta: str; grupo: Grupo; codigos_en_obra: tuple[str, ...]
@dataclass(frozen=True)
class OpcionProveedor:                     # un par de la columna Proveedor (R71)
    etiqueta: str; oficio: OpcionOficio; grupo: Grupo
    filas_en_obra: tuple[tuple[str, str], ...]   # (oficio_codigo, proveedor_codigo) de obrofc (R94)
    # quinta enmienda: sale `por_actividad` (a F-039); `grupo` es siempre de un código
@dataclass(frozen=True)
class ListasCerradas:
    ubicaciones: tuple[str, ...]; urgencias: tuple[Opcion, ...]; listados: tuple[Opcion, ...]

def normalizar_codigo_obra(bruto: object) -> str: ...        # R9; usa nombrado.normalizar_codigo
def normalizar_para_clave(texto: str) -> str: ...            # R35: solo para la clave de duplicado
def etiquetas_de_unidades(unidades: Iterable[UnidadPosventa]) -> tuple[Opcion, ...]: ...  # R8
def opciones_de_oficio(catalogo: CatalogoObra,
                       grupos: GruposVigentes) -> tuple[OpcionOficio, ...]: ...          # R92, R86
def opciones_de_proveedor(catalogo: CatalogoObra, grupos: GruposVigentes,
                          oficios: tuple[OpcionOficio, ...]) -> tuple[OpcionProveedor, ...]: ...  # R71, R72, R86
```

`Grupo` y `GruposVigentes` son de `domain/models/equivalencias.py` (§15): un
`GruposVigentes` por catálogo, construido con las mismas funciones.
`TextosPlantilla` es un `dataclass` inmutable con los párrafos de
instrucciones, los ejemplos y los mensajes por columna que carga el YAML de
§3.4.

> **Enmienda del 2026-09-28.** Se añaden `COLUMNA_ERRORES`, `Proveedor` en la
> cabecera, `SEPARADOR_PAR`, `ProveedorEnObra`, `OpcionProveedor` y
> `opciones_de_proveedor`. `normalizar_para_comparar` pasa a
> `normalizar_para_clave`: ya no se usa para casar valores tasados, solo para la
> clave de duplicado.
>
> **Segunda enmienda del mismo día.** `etiquetas_de_oficios(oficios) ->
> tuple[Opcion, ...]` pasa a `opciones_de_oficio(catalogo, grupos)`, con el
> nuevo `OpcionOficio`; `OpcionProveedor` llevaba `oficio: Opcion`, `grupo:
> GrupoProveedor` y `codigos_en_obra`, y ahora lleva el `OpcionOficio`, un
> `Grupo` genérico y las filas de `obrofc` que casan con el par (R94).

### 4.2 · El libro leído y el reconocimiento

```python
@dataclass(frozen=True)
class CeldaLeida:
    valor: str | int | float | None
    es_formula: bool
    es_fecha_o_booleano: bool
    texto_original: str | None             # lo que se reescribe en el Excel de errores (R63)

@dataclass(frozen=True)
class FilaLeida:
    numero: int                            # número de fila de Excel (cabecera = 1)
    celdas: Mapping[str, CeldaLeida]       # por nombre de columna de CABECERA, sin Errores

@dataclass(frozen=True)
class LibroLeido:
    identificador: str | None; version: int | None; obra_codigo: str | None
    cabecera: tuple[str, ...]
    filas: tuple[FilaLeida, ...]           # solo filas con algún dato fuera de Errores (R23)
    parece_formato_antiguo: bool           # lo calcula el lector (§5.2)

def reconocer_plantilla(libro: LibroLeido) -> str:
    """Devuelve el código de obra normalizado, o levanta FicheroNoEsPlantilla (R17–R20)."""
```

El orden de las comprobaciones es el de los requisitos: identificador (con el
matiz de formato antiguo), versión, cabecera (diciendo qué columna), número de
filas, código de obra de los metadatos.

### 4.3 · Validación de filas (R24–R34, R73–R76, R92–R94)

```python
@dataclass(frozen=True)
class ErrorDeFila: fila: int; columna: str; problema: str

@dataclass(frozen=True)
class Elegido:                             # un oficio o un proveedor ya resuelto
    etiqueta: str; codigo: str | None; ambiguo: bool      # codigo None ⇔ ambiguo (R75, R93, R94)

@dataclass(frozen=True)
class IncidenciaValida:
    fila: int; unidad: Opcion; ubicacion: str | None
    descripcion: str; detalle: str | None
    oficio: Elegido | None; proveedor: Elegido | None    # proveedor ⇒ oficio (R99)
    urgencia: Urgencia | None; listado: Listado | None
    avisos: tuple[str, ...]

@dataclass(frozen=True)
class FilaConError:
    fila: FilaLeida; errores: tuple[ErrorDeFila, ...]

def validar_filas(filas: Iterable[FilaLeida], *, catalogo: CatalogoObra,
                  grupos_oficio: GruposVigentes, grupos_proveedor: GruposVigentes,
                  listas: ListasCerradas
                  ) -> tuple[tuple[IncidenciaValida, ...], tuple[FilaConError, ...]]
```

Se recorren **todas** las filas y todas sus columnas: el error de una no esconde
el de otra. Las opciones se calculan aquí con las funciones de §4.1 sobre el
catálogo **recién leído** y los grupos vigentes.

**Comparación de valores tasados: exacta.** `str(valor) == etiqueta`, sin
recortar, sin mayúsculas, sin tildes (decisión 7). Un valor que no es texto en
una columna tasada es error (R32). Solo los textos libres se tocan: la
descripción corta pasa saltos de línea a espacio y colapsa espacios; el detalle
se recorta en los extremos.

Oficio y proveedor (R73–R76, R92–R94), con la función pura
`resolver_oficio_y_proveedor(oficio: OpcionOficio | None, proveedor:
OpcionProveedor | None) -> tuple[Elegido | None, Elegido | None]`:

- `Oficio` tiene que ser una `OpcionOficio.etiqueta` y `Proveedor` una
  `OpcionProveedor.etiqueta`; si vienen los dos y el grupo de oficio del par
  no es el de `Oficio`, error; si solo viene `Proveedor`, el oficio es el del
  par (D-17);
- **sin proveedor** (R93): `codigos_en_obra` del grupo de oficio con un código
  → ese código; con más de uno → `ambiguo=True`;
- **con proveedor** (R94): se miran las `filas_en_obra` del par —las filas de
  `obrofc` con un oficio del grupo y un proveedor del grupo—; si todas
  comparten código de oficio, el oficio queda resuelto, y si todas comparten
  código de proveedor, el proveedor queda resuelto. Lo que no, `ambiguo=True`.
  Por eso elegir proveedor puede **deshacer** la ambigüedad del oficio: si el
  grupo «Mamparas» son dos códigos pero el proveedor elegido solo está dado de
  alta con uno, ese es el oficio;
- cada `ambiguo=True` añade un aviso a la fila. Nunca se elige solo entre
  varios códigos (D-19).

Avisos (R34): menciona `peligro`, `seguridad`, `urgente`, `urgencia` o
`estructural` (normalizado) con `Urgencia` vacía; o más del 60 % de las letras
de la descripción corta en mayúsculas con al menos 20 letras. **No** se intenta
detectar automáticamente «dos defectos en una fila» ni las referencias
cruzadas: no hay regla fiable, y un falso positivo enseñaría a ignorar los
avisos. Eso lo cubren las instrucciones y la migración.

> **Enmienda del 2026-09-28.** Decía que las etiquetas «se casan normalizadas
> (R26, R30)» y que `validar_filas` devolvía `ErrorDeFila` sueltos. Ahora la
> comparación es exacta, se valida el proveedor y los errores vuelven agrupados
> por fila con la fila leída entera, porque el Excel de errores la necesita.
>
> **Segunda enmienda del mismo día.** `ProveedorElegido` pasa a `Elegido`
> (sirve para oficio y proveedor); el oficio era `Opcion | None` y se
> resolvía siempre a un código; `validar_filas` recibía un solo `grupos`; y
> el párrafo del proveedor decía «`codigos_en_obra` con un código →
> `ProveedorElegido(codigo=…)`, con más de uno → `ambiguo=True`», sin
> resolución conjunta con el oficio.

### 4.4 · Resolver códigos: contra Sigrid, no contra el fichero

La hoja `_catalogos` solo alimenta los desplegables. El importador **no** lee
de ella ningún código: recalcula las opciones a partir del catálogo leído de
Sigrid en esa importación (y de los grupos vigentes en la base) y compara la
etiqueta que trae la fila. Así un fichero manipulado o una plantilla vieja no
pueden colar el código de otra unidad u otro proveedor, y lo que ya no es de la
obra da error de fila y vuelve en el Excel de errores, **ya con las listas
nuevas** (R26).

**El precio, aceptado**: si entre la descarga y la importación Sigrid gana una
unidad con el mismo nombre que otra, o alguien confirma o separa un grupo de
proveedores, las etiquetas afectadas cambian y esas filas vuelven como error
con el mensaje de «plantilla antigua». Es raro, falla cerrado, y el Excel de
errores ya trae los desplegables buenos.

### 4.5 · Duplicados (R35–R38)

```python
def clave_de_duplicado(*, obra_codigo: str, unidad_codigo: str,
                       ubicacion: str | None, descripcion: str) -> str:
    """sha256 hex de "obra\x1funidad\x1fubicación_norm\x1fdescripción_norm"."""

@dataclass(frozen=True)
class GrupoDeClave:
    clave: str
    filas: tuple[IncidenciaValida, ...]    # en orden de aparición; la primera manda

def agrupar_por_clave(validas: Iterable[IncidenciaValida], *, obra_codigo: str) -> tuple[GrupoDeClave, ...]

class EstadoFilaImportada(StrEnum):
    NUEVA = "nueva"; DUPLICADA_EN_FICHERO = "duplicada_en_fichero"
    YA_EN_BANDEJA = "ya_en_bandeja"; CON_ERROR = "con_error"

class EstadoImportacion(StrEnum): COMPLETA = "completa"; PARCIAL = "parcial"

@dataclass(frozen=True)
class IncidenciaEnBandeja:      # una fila de GET /api/bandeja (§8)
    incidencia_id: UUID; importacion_id: UUID | None; fila_origen: int | None
    unidad_codigo: str; unidad_nombre: str; ubicacion: str | None
    descripcion: str; detalle: str | None; oficio_codigo: str | None; oficio_nombre: str | None
    oficio_ambiguo: bool
    proveedor_codigo: str | None; proveedor_nombre: str | None; proveedor_ambiguo: bool
    # quinta enmienda: sale `proveedor_fuera_de_obrofc` (a F-039)
    urgencia: Urgencia | None; listado: Listado | None
    duplicada_de: UUID | None; creada_at_utc: datetime
```

La normalización de la descripción para la clave quita además la puntuación
del final (`.`, `,`, `;`, `:`), para que «Sellar sifón» y «Sellar sifon.» sean
lo mismo. La ubicación vacía cuenta como cadena vacía. El separador `\x1f` no
puede aparecer en ningún campo porque el dominio lo quita al normalizar. Solo se
agrupan las filas **sin error** (R37).

**Por qué la primera de un grupo manda y el grupo entero se salta si su clave ya
está en la bandeja**: si solo se saltara la primera, reimportar un fichero con
dos filas iguales volvería a meter la segunda (su `duplicada_de` no entra en el
índice único) y reimportar **sí** duplicaría (R38).

> **Enmienda del 2026-09-28.** Se añaden `CON_ERROR`, `EstadoImportacion` y los
> campos de proveedor de `IncidenciaEnBandeja`. **Segunda enmienda del mismo
> día**: se añade `oficio_ambiguo`.

### 4.6 · Errores nuevos (`domain/models/errores.py`)

| Error | HTTP | Cuándo |
|---|---|---|
| `CodigoDeObraInvalido` | 400 | R9 |
| `PeticionDeImportacionInvalida` | 400 | R22, sin fichero, más de un fichero |
| `FicheroDemasiadoGrande` | 413 | R15 |
| `FicheroNoEsPlantilla(codigo, motivo)` | 400 | R16–R20; `codigo` ∈ `no_es_xlsx`, `contiene_macros`, `fichero_sospechoso`, `no_es_la_plantilla`, `formato_antiguo`, `version_no_soportada`, `cabecera_distinta`, `demasiadas_filas`, `obra_invalida` |
| `ObraSinUnidades` | 404 en la plantilla y en propuestas, 409 en la importación | R10 |
| `ObraAmbigua` / `CatalogoSinVerificar` | 409 | R10 |
| `CatalogoNoDisponible` | 503 | R11: red, tiempo, respuesta mal formada, entorno |
| `PeticionDeDecisionInvalida` | 400 | R88: cuerpo mal formado, sin `confirmado: true`, menos de dos códigos, `distinto` con más de dos |
| `CodigoNoEsDeLaObra` | 409 | R88: un código de oficio o de proveedor que no está en `obrofc` de la obra |

Se reutilizan `ConfiguracionSigridIncompleta`, `ConfiguracionPgIncompleta` y
`PersistenciaNoDisponible` (503). Los mensajes **no** llevan el cuerpo de la
respuesta de la pasarela, ni nombres de unidad o proveedor, ni textos de fila.

> **Enmienda del 2026-09-28.** Desaparece `FilasInvalidas` (422): una fila con
> error ya no es un error de la petición (R33). Se añaden los dos de proveedores.
> **Segunda enmienda del mismo día**: `ProveedorNoEsDeLaObra` pasa a
> `CodigoNoEsDeLaObra`, que sirve para los dos catálogos.

## 5 · Puertos y adaptadores

### 5.1 · `CatalogoObraPort` y su adaptador

```python
@dataclass(frozen=True)
class FilaUnidadCatalogo:
    obra_ref: str; obra_codigo: str | None; obra_nombre: str | None
    unidad_codigo: str | None; unidad_nombre: str | None

@dataclass(frozen=True)
class FilaOficioCatalogo:                  # una fila de obrofc
    oficio_codigo: str; oficio_nombre: str | None
    proveedor_codigo: str | None; proveedor_nombre: str | None; marca_cif: str | None

class CatalogoObraPort(Protocol):
    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]: ...
    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]: ...
    # quinta enmienda: salen `leer_actividades` y `leer_arbol_actividades` (a F-039)
```

> **Tercera enmienda del 2026-09-28.** Se añade `leer_familias` (R107): las
> familias de los proveedores de `obrofc` de la obra, en una lectura más.
> **Cuarta enmienda del mismo día**: `leer_familias` pasa a `leer_actividades`
> (`conact`) y se añade `leer_arbol_actividades` (`auxpronat`; entero si cabe,
> `codigos=None`, o solo las ramas de esas actividades).
> **Quinta enmienda del 2026-09-29**: las dos salen a F-039; el puerto vuelve a
> tener dos métodos. `FilaOficioCatalogo` pierde `marca_cif` (a F-050).

`LecturaCatalogo` lleva las filas y si la respuesta llegó al techo (R10).

Dos métodos y no uno porque la segunda lectura necesita **la** obra, y decidir
si hay una, ninguna o varias es del dominio, no del adaptador (patrón de
F-013). `obra_ref` es el `upv.obride` en texto: **opaco**, no sale de la
lectura ni a un log ni a una respuesta.

`infrastructure/sigrid/catalogo_obra.py` (`AdaptadorCatalogoSigridApi`) es un
calco de `ubicacion.py` en su forma: constructor que se niega fuera de
`ENTORNOS_CON_CIERRE` (con `CatalogoNoDisponible`, no con el error del cierre),
**solo** `RUTA_LECTURA = "/api/sql/read"`, reintentos con `tenacity` solo de lo
transitorio, clave en la cabecera y `max_rows = 1000`. Nada de este módulo
nombra otra ruta (R46).

> **Enmienda del 2026-09-28.** `leer_oficios` devolvía `OficioObra` distintos;
> ahora devuelve las filas de `obrofc` con su proveedor y la marca de CIF, y los
> oficios distintos se sacan en el dominio.

### 5.2 · `GeneradorPlantillaPort` y `LectorPlantillaPort`

```python
@dataclass(frozen=True)
class FilaPlantilla:                       # la usan la migración y el Excel de errores
    valores: Mapping[str, str | None]      # por columna de CABECERA, sin Errores
    errores: Mapping[str, str] = field(default_factory=dict)   # columna → problema (marca la celda, R64)
    texto_errores: str | None = None       # lo que va en la columna Errores (R63)

class GeneradorPlantillaPort(Protocol):
    def generar(self, *, catalogo: CatalogoObra, opciones_oficio: tuple[OpcionOficio, ...],
                opciones_proveedor: tuple[OpcionProveedor, ...],   # opciones_oficio: segunda enmienda
                listas: ListasCerradas, textos: TextosPlantilla, generada_at: datetime,
                filas: tuple[FilaPlantilla, ...] = (),
                importacion_origen: UUID | None = None) -> bytes: ...

class LectorPlantillaPort(Protocol):
    def leer(self, *, contenido: bytes) -> LibroLeido: ...
```

`filas` existe para que la migración y el Excel de errores usen **el mismo**
generador que el portal (R55, R62) en lugar de escribir otra plantilla
parecida.

`infrastructure/documentos/excel_openpyxl.py`:

- **Generador**: construye el libro de §3; cada texto que venga de fuera se
  escribe forzando tipo texto (R7); las celdas de `FilaPlantilla.errores` llevan
  relleno y comentario (R64). Devuelve los bytes (`BytesIO`).
- **Lector**, en este orden y sin abrir `openpyxl` hasta el paso 3:
  1. los bytes empiezan por `PK\x03\x04`; si no, `no_es_xlsx`;
  2. `zipfile`: ≤ 500 entradas, suma de tamaños descomprimidos ≤ 20 MiB, sin
     `xl/vbaProject.bin` (`fichero_sospechoso`, `contiene_macros`); un ZIP roto,
     `no_es_xlsx`;
  2 bis. *(séptima enmienda; bis)* el **presupuesto de elementos XML** (R117):
     se cuentan en *streaming* los elementos de **todas** las partes del ZIP
     (*bis*: decía «las `.xml` y `.rels`»); por encima de **300.000** (*bis*:
     decía 200.000), `fichero_sospechoso`, y un XML que no se analiza,
     `no_es_xlsx` (ver «El presupuesto de elementos XML», abajo);
  3. `openpyxl.load_workbook(..., read_only=True, data_only=False)` con
     `defusedxml` instalado (**solo lectura** desde la sexta enmienda bis: ver
     «Al cargar», abajo); cualquier excepción de lectura, `no_es_xlsx`;
  4. metadatos de `_plantilla` si existe; si no, calcula
     `parece_formato_antiguo` sobre la primera hoja (fila 1 sin la cabecera de
     R2, texto en `A1`, `A2:A10` vacías, texto en `D1` y `E1`);
  5. cabecera de `Incidencias` y filas con algún dato fuera de `Errores`; cada
     celda con `es_formula` (`data_type == "f"`), `es_fecha_o_booleano` y su
     `texto_original`, **con el recorrido acotado de abajo** (R115).
  El lector **no valida** reglas de negocio: eso es `reconocer_plantilla` y
  `validar_filas`.

**El recorrido acotado (R115; añadido en la sexta enmienda).** `openpyxl`,
en `iter_rows` sin `max_row`, crea una `Cell` por **posición** hasta
`ws.max_row`, y `max_row` lo fija la última celda que exista en el XML,
aunque esté vacía y solo tenga estilo. La review 1 lo midió: un fichero de
33 KB con una celda con estilo en la fila 1.048.576 de «Incidencias» cuesta
~51 s y ~1,9 GB de pico (9,2 s y 553 MB con la fila 300.000), y ninguna
puerta lo frenaba (2 MiB, 20 MiB, 500 entradas, 1000 filas). Un Excel con
filas formateadas hasta el final lo provoca también sin mala intención. Así
que ningún recorrido del lector va posición a posición más allá de lo que la
plantilla puede tener:

- **Filas de «Incidencias»**: de `PRIMERA_FILA` (2) a `ULTIMA_FILA + 1`
  (1002), y de la columna 1 a la última de datos. Es decir, `iter_rows` con
  `min_row`, **`max_row`** y `max_col`, nunca sin `max_row`. Las filas 2–1001
  son las de la plantilla (cabecera + D-11: 1000); la 1002 es la «fila
  siguiente al tope».
- **Qué hay por debajo**: si la fila 1002 **o cualquier otra por debajo** trae
  alguna celda **con valor** (o fórmula) en las columnas de datos, el libro se
  marca con datos fuera del tope y se rechaza con el **mismo** error que ya
  existe para el tope: `FicheroNoEsPlantilla("demasiadas_filas", …)` (R20).
  Para saberlo **no** se recorre la hoja: se miran **solo las celdas que el
  fichero trae**. Dos formas válidas, a elegir por el implementer con su
  prueba de tiempo y memoria:
  - en el modo normal de `openpyxl`, el diccionario interno de celdas
    existentes de la hoja (`ws._cells`, claves `(fila, columna)`): es API
    privada, así que un test fija que existe y se comporta así con la
    versión de `requirements.txt` (`openpyxl>=3.1,<4.0`), y el lector falla
    cerrado (`no_es_xlsx`) si no lo encuentra;
  - o `load_workbook(..., read_only=True)`, que va leyendo el XML sin crear
    celdas por posición; en ese caso el paso que busca datos por debajo del
    tope no puede rellenar los huecos entre filas uno a uno, y el libro se
    cierra al acabar.
- **Las filas vacías con estilo** por debajo —y las de 2–1002 sin valor— ni
  cuentan ni se leen como datos (R23).
- **Los demás recorridos** del lector, con el mismo criterio: la cabecera se
  lee de la columna 1 a `len(CABECERA) + 1` (un valor más a la derecha, mirado
  solo entre las celdas que existen, es `cabecera_distinta`, R19); los
  metadatos de `_plantilla`, en sus dos primeras columnas y hasta un tope
  pequeño de filas (las claves son cinco); y `parece_formato_antiguo` mira
  celdas fijas (`A1:I10`; *séptima enmienda: decía `A1:E10`, errata R3-2*).
- **El Excel de errores** pasa por el mismo lector cuando se vuelve a subir
  (R66): lo genera el generador con las validaciones hasta `ULTIMA_FILA`, así
  que el tope no le cambia nada; y si quien lo corrige formatea filas hasta el
  final de la hoja, sale igual de barato.

**Precisión de R20 que trae el tope.** Antes contaba «más de 1000 filas con
datos» en toda la hoja: 900 filas con datos repartidas hasta la fila 1500
pasaban, con números de fila de hasta 1500. Ahora **cualquier** dato por debajo
de la fila 1001 es `demasiadas_filas`, aunque haya menos de 1000 filas con
datos. Es lo coherente con la plantilla, cuyos desplegables solo llegan a la
1001, y el mensaje sigue diciendo que se parta el fichero.

**Riesgo que queda, dicho.** El tope de 20 MiB descomprimidos (paso 2) sigue
siendo lo que acota cuántas celdas **reales** trae el XML y, con el modo
normal, cuántas crea `load_workbook`. R115 cierra el caso de la review
(pocas celdas, `max_row` enorme); un XML con cientos de miles de celdas reales
dentro de 20 MiB lo acota ese tope, no este.

**Cómo se prueba** (`tests/test_f036_excel_lector.py`, nombres
`test_f036_r115_…`):

- un libro generado por el generador con **una celda vacía con estilo en la
  fila 1.048.576** de «Incidencias» se lee en **menos de un segundo** y con
  la memoria acotada (pico de `tracemalloc` por debajo de un tope fijo, del
  orden de decenas de MB), y da las mismas filas que sin la celda;
- un valor en la fila 1002 → `demasiadas_filas`; un valor en la fila 5.000
  con las 1002–4999 vacías → `demasiadas_filas`; una celda con estilo y sin
  valor en la fila 5.000 → no cuenta;
- lo mismo para una celda con estilo lejana en la columna `XFD` de la fila 1
  (cabecera) y en `_plantilla`;
- con fase RED: los dos primeros fallan (por tiempo o por no dar el error)
  sobre el lector de antes.

**Al cargar: el libro se abre en solo lectura (R115 ampliado; sexta enmienda
bis del 2026-09-30).** La review 2 encontró el mismo daño **antes** de que el
lector recorra nada. `openpyxl` 3.1.5, en `load_workbook` en modo normal,
llama a `WorksheetReader.bind_all`, y dos de sus *binders* crean una celda por
posición: `bind_merged_cells` (`ws._clean_merge_range` crea un `MergedCell` por
posición del rango combinado) y `bind_hyperlinks` (con un `ref` que es un
rango, recorre `ws[link.ref]`). Medido con 33 KB: `A1003:A1048576` combinado,
24 s y 430 MB; `A1003:H1048576` combinado, 169 s y 2,6 GB; un hipervínculo sobre
ese rango, 228 s y 4,1 GB. Pasa en **cualquier** hoja del libro, porque el modo
normal las carga todas. Ni el tope de 2 MiB ni el de 20 MiB ni el recorrido
acotado lo frenan: el daño está hecho en `_abrir`.

**Decisión: `load_workbook(io.BytesIO(contenido), read_only=True,
data_only=False)`** —la opción (b) de la review 2, que recomienda el líder—, y
no un examen previo del XML (la opción (a)). Por qué:

- **Cierra de raíz** cualquier estructura que el cargador expanda, no solo las
  dos conocidas: en solo lectura las hojas no se enlazan al cargar, sino que se
  leen en *streaming* cuando se recorren, y ni los combinados ni los
  hipervínculos se enlazan nunca. Un examen previo cerraría los dos casos
  medidos y dejaría abierto el siguiente *binder* que alguien descubra.
- **No hay un analizador de XML propio** que mantener ni un prefijo de espacio
  de nombres que lo esquive (`<x:mergeCell>`).
- **Medido por la review 2: 0,08 s** en los dos peores casos.
- **No rompe nada que la plantilla necesite leer.** El lector solo lee
  **valores** —los metadatos de `_plantilla`, la cabecera y las filas de
  «Incidencias»—, el **tipo** de cada celda (`data_type == "f"` para una
  fórmula, que en solo lectura con `data_only=False` llega igual) y si es fecha
  o booleano (la celda de solo lectura trae su formato de número y su tipo). La
  validación de datos, la protección de hoja, los comentarios y los rellenos
  **no** se leen: son cosa del generador, y el importador vuelve a validar todo
  él mismo (§3.3, §4.3). Las hojas `veryHidden` se leen igual en solo lectura.

Lo que obliga a rehacer en `excel_openpyxl.py` (el modo normal y
`ws._cells` salen del lector por completo):

- **`_abrir`**: `read_only=True`; el libro se **cierra siempre** (`close()` en
  un `finally`) antes de devolver el `LibroLeido`, que ya lleva solo objetos del
  dominio.
- **`_metadatos`**: `iter_rows(min_row=1, max_row=MAX_FILAS_METADATOS,
  max_col=2, values_only=True)`.
- **`_parece_formato_antiguo`**: **una** pasada `iter_rows(min_row=1,
  max_row=10, max_col=9)` —`A1:I10`, las 9 columnas de la cabecera de R2;
  *séptima enmienda: decía `max_col=5`, errata R3-2, aceptado en T35-2*— sobre la primera hoja, no `ws.cell(...)` celda a
  celda (en solo lectura cada `ws.cell` vuelve a leer la hoja entera).
- **`_cabecera`**: la fila 1 en una pasada. Un valor a la derecha de la
  columna `len(CABECERA) + 1` sigue siendo `cabecera_distinta` (R19). En solo
  lectura la fila trae como mucho hasta su última celda existente (16.384
  columnas en el peor caso, una vez): acotado.
- **`_filas`**: `iter_rows(min_row=2, max_row=ULTIMA_FILA + 1,
  max_col=len(COLUMNAS_DE_DATOS))`, igual que tras la sexta enmienda.
- **`_datos_fuera_del_tope`** (hoy sobre `_celdas_existentes`, que lee
  `ws._cells`): mirando **solo las filas que el XML trae** por debajo de la
  fila 1002. **Ojo con el relleno**: en solo lectura, `iter_rows` sin
  `max_row` **rellena** los huecos entre filas con una fila vacía por cada
  número de fila que falta, así que recorrerlo hasta la fila 1.048.576 son un
  millón de iteraciones, que es justo lo que §5.2 prohíbe («no puede rellenar
  los huecos entre filas uno a uno»). Dos formas válidas, con la prueba de
  tiempo que ya existe (celda con estilo en la fila 1.048.576, < 1 s) como
  criterio:
  - el analizador de filas que usa la hoja de solo lectura por dentro
    (`WorkSheetParser` sobre `ws._get_source()`), que solo da las filas
    presentes: es API privada, así que, como pasaba con `ws._cells`, un test
    fija que existe y se comporta así con `openpyxl>=3.1,<4.0`, y el lector
    falla cerrado (`no_es_xlsx`) si no lo encuentra;
  - o una pasada en *streaming* con `defusedxml` sobre la parte XML de
    «Incidencias», por nombre local de etiqueta (`row/@r`, y `c` con hijo `v`,
    `is` o `f`), sin expresiones regulares sobre los bytes.
- El test que fijaba `ws._cells` se sustituye por el que fija la vía elegida.

**El combinado pequeño dentro de la plantilla se admite.** En solo lectura un
rango combinado no existe como tal: su celda de arriba a la izquierda trae el
valor y las demás llegan vacías. Así que, si alguien combina, por ejemplo,
`C2:D2` (descripción corta y detalle), la fila se lee con la descripción corta
y sin detalle, y se valida como cualquier otra. Rechazarlo exigiría leer los
combinados, que es justo lo que ahora no se hace; y no hay nada que proteger:
el valor que cuenta es el que Excel enseña. Un hipervínculo en una celda se lee
igual: cuenta su texto, no el enlace.

**Por qué no la opción (a)**, aunque cuesta 0,002 s: habría que mantener un
analizador de XML propio para cada estructura expandible que se conozca
(combinados, hipervínculos con rango y las que vengan), con la regla de que un
`ref` ilegible o sin fila cuenta como el máximo, y la puerta tendría que ir
**antes** de `load_workbook` para servir de algo. Con (b) no hay puerta nueva
que ordenar: lo que cierra el hueco es cómo se abre el libro.

**Cómo se prueba** (añadido a los `test_f036_r115_…`):

- los tres ficheros de la review 2 —`A1003:A1048576` combinado,
  `A1003:H1048576` combinado e hipervínculo sobre `A1003:H1048576`, los tres en
  «Incidencias» de una plantilla generada— se leen o se rechazan en **menos de
  un segundo** y con el pico de `tracemalloc` bajo el tope que ya usan los
  tests; el combinado se lee con las mismas filas que sin él, y el hipervínculo
  también (en solo lectura el enlace no crea celdas);
- lo mismo con el rango en `_plantilla` y en `Instrucciones` (la plantilla se
  reconoce igual);
- lo mismo sobre un **Excel de errores** con una fila con error;
- un combinado pequeño `C2:D2` en una fila con datos: la fila entra con la
  descripción corta y sin detalle;
- que el lector abre el libro en solo lectura y lo cierra (un doble de
  `load_workbook` que registra `read_only=True` y la llamada a `close`, también
  cuando la lectura falla a medias);
- los de la sexta enmienda siguen pasando (celda con estilo en la fila
  1.048.576, valores en la 1002 y la 5.000, `XFD1`, `_plantilla`);
- fase RED: los tres ficheros de la review pasan de 1 s sobre el lector de
  `52f8149`.

**Riesgo que queda, dicho (y que mejora).** Con solo lectura, `load_workbook`
ya no crea las celdas de ninguna hoja al cargar. Una hoja que no es de la
plantilla no se recorre nunca.

> **Séptima enmienda del 2026-10-01 (review 3, R3-1 y R3-2).** Este párrafo
> seguía: «así que el tope de 20 MiB descomprimidos deja de ser lo que acota la
> memoria de la carga: lo acotan los recorridos, que están todos limitados». No
> era exacto por dos lados: (1) **no todos los recorridos están limitados**:
> `_datos_fuera_del_tope` analiza entera la hoja «Incidencias» (lo que limita es
> qué **filas** se miran, no cuántos **elementos** se analizan), y `_filas`, en
> solo lectura, también llega al final si no hay filas por debajo de la 1002;
> (2) `load_workbook`, también en solo lectura, analiza entero `styles.xml`,
> `sharedStrings.xml`, el tema y `workbook.xml`. **Qué no acota el tope de 20
> MiB**: el número de elementos, y con él el coste, porque en 20 MiB caben 4
> millones y `openpyxl` gasta hasta ~600 B y 20–25 µs por elemento. **Qué lo
> acota ahora**: el presupuesto de 200.000 elementos de R117, contado antes de
> abrir; con él, cada pasada de `openpyxl` sobre el libro analiza como mucho
> 200.000 elementos (≈ 120 MB y unos 5 s en el peor caso admitido), y
> «Incidencias» se analiza dos veces (§5.2, «Una sola pasada»: no entra).
>
> **Octava enmienda del 2026-10-01 (review 4, R4-1).** Tampoco el presupuesto
> de elementos acota todo: un **atributo** con una lista de rangos (`sqref` de
> validaciones, formato condicional y escenarios) se convierte en un objeto por
> rango dentro de **un** elemento, y esos bytes solo los acotaba el tope
> descomprimido. En vez de un quinto tope específico, lo que **acota ahora la
> clase entera** es la **lectura aislada** (R118): `openpyxl` lee el fichero
> subido en un proceso hijo con **30 s y 1 GB**, y si se pasa se mata
> (`fichero_sospechoso`). R4-1 queda cerrado por R118, sin parche propio. El
> solo lectura, R115, R117 y el tope descomprimido (que pasa a el doble del
> fichero legítimo más grande, R16) **se mantienen** como primera línea
> barata: rechazan casi todo lo hostil en el padre, sin pagar el arranque de
> un hijo. Lo que queda, dicho: cada importación puede costar **como mucho 30 s
> y 1 GB** en el hijo, una a la vez por proceso (R120), y el padre solo crece lo
> que mide el resultado acotado (`MAX_BYTES_RESULTADO`).
>
> **Octava enmienda bis del 2026-10-01 (H-T40-1).** La última frase no era
> exacta: el padre crece el resultado acotado **más** lo que gasta el recuento
> de R117 (unas 5 veces el elemento más grande, acotado por el tope
> descomprimido: 80,8 MiB medidos con 17 MiB). Ver «Lo que crece el padre»,
> en «La lectura aislada».

**El presupuesto de elementos XML (R117; séptima enmienda del 2026-10-01).**
La review 3 midió lo que el solo lectura no cierra: `openpyxl` analiza **entero**
cada `xml` que toca —al cargar, en los dos modos, `xl/styles.xml`,
`xl/sharedStrings.xml`, el tema y `workbook.xml`; al recorrer una hoja, todas
sus estructuras (`WorkSheetParser.parse` hace `from_tree` de `mergeCells`,
`hyperlinks`, `dataValidations`, `rowBreaks`…, aunque el lector solo quiera las
filas)— y gasta **hasta ~600 B y 20–25 µs por elemento**. Con 5 bytes por
elemento, en 20 MiB caben 4 millones: el tope de 20 MiB **no acota el coste**.

| Qué se repite (review 3) | Dónde | Elementos | Bytes | Lector de `becb693` |
|---|---|---:|---:|---|
| `<xf/>` | `xl/styles.xml` | 4.135.650 | 63.622 | 113,9 s · 2.485 MB (84,8 s solo en `load_workbook(read_only=True)`) |
| `<dataValidation sqref="J2"/>` | «Incidencias» | 738.507 | 84.159 | 68,7 s · 901 MB |
| `<brk id="1"/>` | «Incidencias» | 1.590.632 | 74.443 | 48,1 s · 858 MB |
| `<mergeCell ref="J2:K2"/>` | «Incidencias» | 861.592 | 84.141 | 34,7 s · 517 MB |
| Celda vacía con estilo en la fila 1200 | «Incidencias» | 1.033.911 | 84.019 | 17,8 s · 647 MB |
| Formato condicional de una celda | «Incidencias» | 164.113 | 104.239 | 18,8 s · 240 MB |
| `<hyperlink ref="J2"/>` | «Incidencias» | 626.612 | 94.470 | 16,2 s · 393 MB |

**La puerta.** Un paso nuevo del lector, `_contar_elementos_xml(contenido)`,
**entre** `_inspeccionar_zip` (paso 2) y `_abrir` (paso 3), es decir, **antes
de `load_workbook`**:

- recorre **todas** las entradas del ZIP, **sea cual sea su extensión**, en el
  orden del ZIP *(séptima enmienda bis: decía «cuyo nombre acaba en `.xml` o
  `.rels` (las que `openpyxl` puede analizar; las binarias no)»; ver «Todas
  las partes», abajo)*;
- lee cada una **en trozos** (`zipfile.ZipFile.open(...).read(64 KiB)`) y se
  los da a un analizador **expat** configurado por `defusedxml`, que prohíbe
  DTD, declaraciones de entidades y entidades externas, **sin construir árbol**:
  el único trabajo por elemento es sumar uno en el manejador de **apertura** de
  elemento (`StartElementHandler`, o el `start` de un *target* que no guarda
  nada). Se cuentan elementos, no etiquetas por nombre: no depende del prefijo
  de espacio de nombres ni de qué estructura sea, así que cierra la **clase**
  entera, también lo que `openpyxl` analice mañana. No le aplica la objeción que
  §5.2 hacía a la opción (a) de la review 2 (mantener un analizador por
  estructura): este no sabe de estructuras;
- el total es **global**, de todas las partes juntas, y en cuanto pasa del
  presupuesto el analizador **se detiene** (una excepción propia desde el
  manejador): el coste es proporcional al presupuesto y no al fichero;
- por encima del presupuesto, `FicheroNoEsPlantilla("fichero_sospechoso", …)`
  con un mensaje que no da cifras internas («El fichero tiene una estructura
  interna demasiado grande para ser la plantilla.»); un XML que no se puede
  analizar (roto, con DTD, con entidades), `no_es_xlsx`, igual que si fallara
  `_abrir`. En los dos casos, **sin** haber llamado a `load_workbook`.

**El número: `PRESUPUESTO_ELEMENTOS_XML = 200_000`** *(séptima enmienda bis:
pasa a **300_000**; la calibración vigente está en «Todas las partes»,
abajo)*, constante del adaptador
junto a las de 2 MiB, 20 MiB y 500 entradas. Calibración:

- la **plantilla legítima más grande** que se puede generar —1000 filas con un
  detalle de 2000 caracteres— tiene **26.886** elementos (review 3): el margen
  es de **7,4 veces**;
- un test fija que la plantilla completa queda **por debajo de un quinto del
  presupuesto** (40.000): si el generador crece, salta antes de que una
  plantilla de verdad se acerque al tope;
- el **`v2` guardado desde Excel** añade `sharedStrings`, estilos y el tema; se
  mide en T29 frente al presupuesto con el script de T37. Si pasara de 40.000,
  se para y se vuelve al spec-author antes de subir el tope;
- lo que acota por arriba: **200.000 × ~600 B ≈ 120 MB y unos 5 s** en el peor
  caso admitido, por cada pasada de `openpyxl` sobre esos elementos (ver
  «Riesgo que queda»). Contar 200.000 elementos con expat cuesta del orden de
  0,1 s (4,1 millones, sin cortar, 2,65 s).

**Todas las partes del ZIP, y el presupuesto recalibrado (séptima enmienda
bis del 2026-10-01; hallazgo T37-1, opción (a) del humano).**

*Por qué todas.* `openpyxl` no busca las partes por su extensión: encuentra
el libro por `_rels/.rels` y `[Content_Types].xml`, y las hojas, las cadenas
compartidas y los estilos por las relaciones de `xl/_rels/workbook.xml.rels`.
Una hoja guardada como `xl/worksheets/sheet1.dat`, con su relación y su tipo
de contenido apuntando ahí, se lee igual que una `.xml`, y el recuento por
extensión no la veía: medido por el implementer, 74 KB con 1,6 millones de
`<brk/>` → 48,4 s y 911 MB. Mirar las relaciones para decidir qué contar
sería repetir la lógica de localización de `openpyxl` (y de sus próximas
versiones); contar **todo** no depende de ella.

*Qué pasa con lo que no es XML.* Cada parte se da al mismo analizador,
trozo a trozo:

- **una parte que no es XML** (una imagen, un `printerSettings1.bin` de los
  que añade Excel) hace fallar a *expat* en los primeros bytes: cuenta **0**,
  se deja de leer en ese trozo (no se descomprime el resto) y el recuento
  sigue. Coste: un trozo de 64 KiB como mucho;
- **una parte que empieza siendo XML y falla a mitad**: los elementos abiertos
  **hasta el fallo cuentan**, la parte se deja de leer ahí y el recuento sigue.
  No pasa gratis: si lo que había antes del fallo agota el presupuesto, es
  `fichero_sospechoso`; y si no lo agota, lo que `openpyxl` pueda analizar de
  esa parte está acotado por lo ya contado (si la usa, fallará en el mismo
  sitio y dará `no_es_xlsx` en `_abrir`). **Por qué no `fichero_sospechoso`
  al primer fallo**: rechazaría cualquier libro con una imagen o con el
  `printerSettings` binario que Excel guarda a veces, y un `v2` guardado desde
  Excel tiene que entrar;
- **las `.xml` y `.rels`** siguen como en la séptima enmienda: un XML roto en
  ellas es `no_es_xlsx`, porque una parte que se declara XML y no lo es no es
  un `.xlsx`;
- **DTD o entidades**, en cualquier parte y con cualquier extensión:
  `no_es_xlsx`, como antes. Un binario real falla antes de llegar a ellas.

*El número: `PRESUPUESTO_ELEMENTOS_XML = 300_000`.* Con todas las partes:

| Libro legítimo | Elementos | Fracción del presupuesto |
|---|---:|---:|
| Plantilla completa (1000 filas, detalle de 2000) | 26.886 | 9 % |
| **Excel de errores más grande** (1000 filas con error en las 8 columnas; el VML de los comentarios suma 96.006) | **148.916** | 50 % |
| `v2` guardado desde Excel | se mide en T29 con el script de T37 | tiene que quedar por debajo de un quinto (60.000) |

- **Margen**: el Excel de errores más grande es el **máximo absoluto** que
  produce el generador (1000 filas × 8 columnas con error), y queda a **2,0
  veces** del tope; el margen cubre que Excel reescriba los comentarios y el
  VML al guardarlo antes de volver a subirlo. La plantilla queda a 11 veces.
- **Coste del peor caso admitido**, estimado con las cifras de la review 3
  (~600 B y 20–25 µs por elemento que `openpyxl` convierte en objeto):
  **300.000 × ~600 B ≈ 180 MB y 6–7,5 s por pasada**. «Incidencias» se
  analiza dos veces (las dos pasadas no se funden), así que, con todo el
  presupuesto en esa hoja, **12–15 s** y el mismo pico de memoria, porque las
  pasadas van una detrás de otra. Cabe en el presupuesto de 45 s del proxy y
  en la memoria de una instancia. T37 bis lo **mide** con un fichero de
  300.000 elementos en «Incidencias» y lo anota.

  > **Novena enmienda del 2026-10-01 (errata R4-2, arrastrada en R5-5).** Los
  > **12–15 s** y los ~180 MB de arriba eran la **estimación**; se conservan
  > como estaban. **Lo medido en T37 bis** con 300.000 elementos de un solo
  > tipo en «Incidencias» fue de **3,6 s a 23,4 s** según el tipo de elemento
  > (el peor, `<dataValidation/>`) y **389 MB** de pico: por encima de lo
  > estimado, y dentro de los 45 s del proxy. Desde la octava enmienda ese
  > coste **ya no lo acota el presupuesto solo**: la lectura corre en el
  > **proceso hijo**, con 30 s de reloj y 1 GiB (R118; «La lectura aislada»,
  > «Topes»), y el peor caso medido cabe dentro.
- **Coste del recuento**: proporcional al presupuesto. T37-3 midió 0,14–0,32 s
  con 200.000 en un proceso aparte y 0,44–0,69 s con cobertura; con 300.000,
  del orden de 0,2–0,5 s y hasta ~1 s con cobertura. Por eso los tests de
  tiempo de R115 y R117 **miden en un subproceso sin cobertura**: el segundo
  de tope mide el producto, no la instrumentación. Si aun así no cupiera en la
  máquina de la campaña, se vuelve al spec-author; no se afloja el tope en
  silencio.
- **Los umbrales que fijan los tests**: la plantilla completa, por debajo de
  un quinto (60.000); el Excel de errores más grande, dentro del presupuesto;
  el `v2` (T29), por debajo de un quinto, y si no, se para.

> **Séptima enmienda bis del 2026-10-01.** Lo de arriba sustituye, para el
> número y su calibración, a «El número: 200_000» y a la tabla de umbrales de
> 40.000 de la séptima enmienda, que se conservan como estaban. Lo que no
> cambia: la puerta, su sitio (antes de `load_workbook`), el corte al pasar el
> presupuesto y los códigos de error.

**Una sola pasada por «Incidencias»: no entra.** `_datos_fuera_del_tope` y
`_filas` siguen siendo dos pasadas del analizador de filas sobre la misma hoja,
como las dejó T35. Con el presupuesto, cada pasada analiza como mucho 200.000
elementos, así que fundirlas ahorra tiempo pero no cambia ninguna cota; y
tocaría código que ya han revisado y mutado dos reviews. Queda como mejora
posible, sin requisito.

**Cómo se prueba** (`tests/test_f036_excel_lector.py`, nombres
`test_f036_r117_…`, libros construidos **en memoria** escribiendo el XML):

- los siete ficheros de la tabla se rechazan con `fichero_sospechoso` en
  **menos de un segundo**, con el pico de `tracemalloc` bajo el tope que ya usan
  los tests, y **sin** llamar a `load_workbook` (un doble que revienta si se le
  llama);
- la plantilla completa (1000 filas, detalle de 2000) se admite y su cuenta es
  menor que `PRESUPUESTO_ELEMENTOS_XML // 5`;
- el recuento se corta: un doble del analizador (o del lector de trozos) dice
  cuántos elementos se contaron, y con un fichero de 4 millones no pasa de
  `PRESUPUESTO_ELEMENTOS_XML + 1`;
- frontera: un ZIP con exactamente el presupuesto se admite en el recuento; con
  uno más, `fichero_sospechoso`;
- el total es global: dos partes que por separado caben y juntas no, se
  rechazan;
- se cuentan elementos con prefijo (`<x:mergeCell>`) y en un `.rels`;
- una parte con DTD o entidad, o XML roto, da `no_es_xlsx` sin llamar a
  `load_workbook`;
- fase RED: los siete ficheros, sobre el lector de `becb693`, pasan de 1 s (con
  tope de tiempo en el subproceso) o no dan `fichero_sospechoso`.

> **Séptima enmienda del 2026-10-01 (review 3, R3-1).** Hasta aquí §5.2 daba
> el tope de 20 MiB por cota del coste de lo que se analiza (párrafo «Riesgo que
> queda» de la sexta enmienda y el de la bis). La review 3 lo desmintió con 64
> KB, y el humano eligió el presupuesto de elementos el 2026-10-01.

> **Sexta enmienda bis del 2026-09-30 (review 2, R2-1).** El punto 3 de arriba
> decía `openpyxl.load_workbook(..., data_only=False, keep_vba=False)`, en modo
> normal, y la sexta enmienda dejaba elegir entre `ws._cells` y `read_only`; el
> Bloque 10 eligió `ws._cells` (B10-1), que cerró el caso de la review 1 pero no
> este. Ahora es `read_only=True` y `ws._cells` sale del lector. El párrafo de
> «Riesgo que queda» de la sexta enmienda describía el modo normal.

> **Enmienda del 2026-09-28.** `FilaPlantilla` tenía un campo por columna y
> servía solo a la migración; ahora lleva los valores por columna y los errores,
> para el Excel de errores. El generador recibe las opciones de proveedor y el
> `importacion_origen`.

**La lectura aislada en un proceso hijo (R118–R120; octava enmienda del
2026-10-01).**

*Por qué se cambia de estrategia.* Cuatro reviews, cuatro huecos de la misma
familia: una celda lejana (R115), rangos que se expanden al cargar (R115
ampliado), millones de elementos pequeños (R117) y, en la review 4 (R4-1),
**atributos con listas de rangos**: el `sqref` de las validaciones de datos, del
formato condicional y de los escenarios se convierte en un `CellRange` por rango
(~7,5 µs y ~227 B cada uno), dentro de **un** elemento que el presupuesto cuenta
como uno; estimado del orden de 100 s y 1,6 GB dentro de los 20 MiB. Cada parche
cierra un caso y el siguiente sale de leer más código de `openpyxl`. El humano
eligió el 2026-10-01 la opción (A) del líder, «pero dobla los límites»: **la
biblioteca lee el fichero subido en un proceso hijo con tope de tiempo y de
memoria**, y lo que se pase se mata. Eso cierra la **clase** entera, también lo
que `openpyxl` analice mañana. R4-1 queda cerrado por R118, **sin** parche
propio.

*Qué corre dónde.*

| Paso | Proceso | Usa `openpyxl` |
|---|---|---|
| 1. Tamaño ≤ 2 MiB (R15) | padre | no |
| 2. ZIP: firma, entradas, macros, **tope descomprimido** (R16) | padre | no |
| 2 bis. Presupuesto de 300.000 elementos (R117) | padre | no |
| 3–5. `load_workbook(read_only=True)`, metadatos, cabecera, filas, datos fuera del tope (R115) | **hijo** | **sí** |
| Validación de filas, catálogo, registro, Excel de errores | padre | el generador escribe, no lee (abajo) |

Los pasos 1–2 bis se quedan delante, en el padre: son baratos, rechazan casi
todo lo hostil sin pagar el arranque de un proceso, y ninguno toca `openpyxl`.

*Módulos.*

- `infrastructure/documentos/excel_openpyxl.py` se queda con el **generador** y
  con la parte del lector que corre **en el hijo**: `_abrir`, `_extraer` y una
  función de entrada `leer_en_hijo(contenido) -> bytes` que devuelve el JSON.
- **Nuevo** `infrastructure/documentos/lector_aislado.py`:
  `LectorPlantillaAislado`, que implementa `LectorPlantillaPort` (el puerto no
  cambia). Hace los pasos 1–2 bis, pide la lectura al ejecutor, valida el JSON y
  reconstruye el `LibroLeido`. **No importa `openpyxl`** (un test de
  arquitectura lo fija).
- **Nuevo** `infrastructure/documentos/ejecutor_aislado.py`: el ejecutor real,
  con `multiprocessing`, detrás de un protocolo pequeño para poder doblarlo:

```python
class EstadoHijo(StrEnum):
    OK = "ok"; TIEMPO = "tiempo"; MEMORIA = "memoria"; MURIO = "murio"
    DEMASIADO_GRANDE = "demasiado_grande"

@dataclass(frozen=True)
class SalidaHijo:
    estado: EstadoHijo; cuerpo: bytes | None; limite_memoria_aplicado: bool; segundos: float

class EjecutorAislado(Protocol):
    def ejecutar(self, contenido: bytes, *, segundos: float, bytes_memoria: int,
                 max_bytes_resultado: int) -> SalidaHijo: ...
```

- `interface_adapters/api/importar.py` compone `LectorPlantillaAislado` en vez
  de `LectorPlantillaOpenpyxl`. El **script de migración** sigue usando el lector
  en proceso: corre en local sobre ficheros conocidos (el original y el `v2` que
  genera él mismo), no sobre una subida (como dijo B10 para R115).

*Topes (`lector_aislado.py`).*

- `SEGUNDOS_HIJO = 30` (reloj, desde que el hijo arranca hasta que entrega el
  resultado) y `BYTES_MEMORIA_HIJO = 1024 ** 3` (1 GiB). Son el doble de lo que
  propuso el líder (15 s y 512 MB), por decisión del humano. El peor caso
  admitido medido por T37 bis (23,4 s y 389 MB) cabe dentro.
- `MAX_BYTES_RESULTADO`: el **doble** del JSON del resultado legítimo más
  grande, medido en T41 (plantilla completa y Excel de errores más grande),
  redondeado al MiB. El padre lee el canal con ese tope
  (`Connection.recv_bytes(maxlength=…)`): si el hijo manda más, se descarta y es
  `fichero_sospechoso`. Este tope protege también al **generador** del Excel de
  errores, que corre en el padre y escribe los valores tal como llegaron (R63):
  sus entradas ya vienen acotadas por él.
- *(Novena enmienda.)* `MARGEN_SEGUNDOS_CPU = 5`, en `ejecutor_aislado.py`: el
  tope de **CPU** del hijo es `math.ceil(segundos) + MARGEN_SEGUNDOS_CPU`
  (`RLIMIT_CPU` va en segundos enteros), **35 s** con los de producción. Lo
  calcula el ejecutor a partir del `segundos` que ya recibe: el protocolo
  `EjecutorAislado` y `SalidaHijo` **no cambian**, ni los dobles de los tests.

*Los topes y el formato visual (R127; décima enmienda del 2026-10-02).* Los
topes de arriba se calibraron con los dos ficheros legítimos más grandes que
produce el generador. El formato de §3.6 cambia ese generador, así que **hay
que volver a medirlos**; ningún tope cambia en esta enmienda.

Qué añade el formato al fichero:

| Qué | Dónde | Cuánto, estimado |
|---|---|---|
| Fuentes, rellenos, bordes y combinaciones (`xf`), y un formato diferencial (`dxf`) | `xl/styles.xml` | Decenas de elementos: los estilos se deduplican |
| El índice de estilo de cada celda (`s="…"`) | hojas | Ningún elemento: las 9.000 celdas de «Incidencias» ya existen y ya llevan `s`; unos bytes si el índice gana una cifra |
| Una regla de formato condicional con **un** `sqref` de un rango (solo sin errores) | hoja «Incidencias» | 3 elementos |
| Alto de fila, color de pestaña, vista sin cuadrícula, ajustes de página y pie | hojas | Una decena de elementos y atributos |
| El nombre definido de los títulos de impresión | `xl/workbook.xml` | 1 elemento |
| Celdas sin valor en «Instrucciones» (B–H de tres filas) | hoja «Instrucciones» | ~21 elementos |

Ninguna imagen ni parte nueva. La estimación es que todo cabe con holgura;
**la estimación no vale: se mide** (T50 antes, T52 después, en la misma
máquina y con los mismos constructores de `_legitimos()` de
`test_f036_lector_aislado.py`).

Qué se mide, de la **plantilla completa** y del **Excel de errores más
grande**, y con qué margen (el que la spec exige hoy):

| Medida | Hoy (T37 bis, T41) | Margen que hay que conservar | Quién lo vigila |
|---|---|---|---|
| Elementos XML, plantilla completa | 26.886 | < **60.000** (un quinto del presupuesto) | test que ya existe (`PRESUPUESTO // 5`) |
| Elementos XML, Excel de errores más grande | 148.916 | ≤ **150.000** (la mitad: «2,0 veces») | test **nuevo** `test_f036_r127_…` (`PRESUPUESTO // 2`) |
| Bytes descomprimidos, el mayor | 8.574.765 | ≤ **8.912.896** (la mitad de 17 MiB: el doble sigue redondeando a 17 MiB) | test que ya existe (`_doble_al_mib`) |
| Bytes del JSON de `leer_en_hijo`, el mayor | 5.257.211 | ≤ **5.767.168** (la mitad de 11 MiB); debería salir **idéntico**: el lector no lee estilos | test que ya existe (`_doble_al_mib`) |
| Tiempo del hijo real (reloj, con arranque) | sin cifra escrita: «se admiten» | ≤ **15 s** (la mitad del tope) y no más de un 25 % peor que el «antes» | medición de T52; el test que ya existe solo exige que se admitan |
| Pico de memoria de la lectura | sin cifra escrita | ≤ **512 MiB** (la mitad del tope) y no más de un 25 % peor que el «antes» | medición de T52 |

Los dos últimos no tenían margen escrito: la spec solo pedía que el hijo real
los admitiera con 30 s y 1 GiB. Esta enmienda fija la mitad del tope —el
mismo criterio del «doble» con el que se pusieron los otros— como umbral
**para decidir**, no como constante nueva del código. La memoria se mide en
el proceso que lee (en Linux, el máximo residente del hijo; en Windows, lo
que la plataforma permita o el pico de `tracemalloc` de `leer_en_hijo` en un
subproceso), diciendo en el informe cuál se usó, y la misma antes y después.

Dos márgenes son **estrechos de partida** y son los que hay que mirar: el
Excel de errores más grande está a **1.084 elementos** de la mitad del
presupuesto y a **338.131 B** de la mitad del tope descomprimido. El Excel
de errores no lleva la regla condicional, pero sí los estilos, el nombre
definido y las celdas de «Instrucciones».

> **Qué quiere decir ese margen** *(10 bis; review 7, R7-3)*. Los ~1.000
> elementos (984 tras el Bloque 12) son margen frente a la **guarda de
> calibración** —la mitad del presupuesto, 150.000, que vigila que el
> generador no engorde—, **no** frente al **rechazo**, que es el presupuesto
> entero (300.000): un Excel de errores real sigue a unos 150.000 elementos
> del rechazo. Y «el Excel de errores más grande» se mide con el **catálogo
> fijo de los tests** (3 unidades, 4 oficios, 5 filas de `obrofc`): con un
> catálogo real mayor, la hoja `_catalogos` crece y ese mismo fichero puede
> pasar de 150.000 (la review 7 midió 151.011 con +300 unidades, +80 oficios
> y +200 proveedores; ya pasaba de la guarda **antes** del formato) sin
> acercarse al rechazo. La guarda es del generador y por eso usa un catálogo
> fijo; no es una predicción del fichero de una obra concreta. Que nadie lea
> «984» como «a punto de rechazar».

**Regla de decisión** (T52):

1. Si todas las medidas conservan su margen, se sigue.
2. Si alguna no, **se recorta adorno y se vuelve a medir**, en este orden,
   parando en cuanto quepa: (a) las **bandas alternas** (la regla
   condicional de «Incidencias» y el relleno alterno de los ejemplos);
   (b) los ajustes de **impresión** (títulos de impresión y pie);
   (c) las celdas sin valor de «Instrucciones» (la banda de la obra y la
   línea del título se quedan solo en la columna A). Cada recorte se anota en
   `progress/impl_F-036.md` con la medida que lo motivó, el test del adorno
   recortado pasa a comprobar que **no** está, y el líder lo dice al humano
   en el resumen: la muestra que aprobó ya no es exactamente lo que recibe.
3. Si recortado (a)–(c) sigue sin caber, **PARADA**: no se toca ningún tope.
   `PRESUPUESTO_ELEMENTOS_XML`, `MAX_BYTES_DESCOMPRIMIDOS`,
   `MAX_BYTES_RESULTADO`, `SEGUNDOS_HIJO` y `BYTES_MEMORIA_HIJO` son
   decisiones del humano (R3-1, T37-1, R4-1): subir cualquiera exige volver
   a él con la medición.

*(10 bis.)* La regla sigue igual, con este orden de recorte, porque (b)
—la impresión— ya no existe: (a) las **bandas alternas** (la regla 3 y el
relleno alterno de los ejemplos); (b) las celdas sin valor de
«Instrucciones»; (c) la **regla 2** (el gris de `Errores`: la columna se ve
blanca con sus líneas y sigue bloqueada). La **regla 1** no se recorta: es la
que enseña la fila a la vista que pidió el humano. Recortado (a)–(c) sin
caber: **PARADA**, sin subir ningún tope.

**Los `sqref` legítimos y R4-1.** R4-1 eran `sqref` con millones de rangos,
que `openpyxl` convierte en un objeto por rango (~7,5 µs y ~227 B cada uno).
No se cerró con un filtro de `sqref` —no hay lista blanca, ni tope de rangos,
ni nada que distinga un `sqref` «bueno»— sino aislando la lectura: lo que se
pase de tiempo o de memoria se mata. Por eso el `sqref` de las bandas
convive con ese control sin ninguna excepción: es **un** rango, igual que
los ocho de las validaciones de datos que la plantilla lleva desde el primer
día, y cuesta un objeto. Si quien rellena corta y pega filas, Excel puede
partir la regla en decenas o cientos de rangos: sigue siendo despreciable
(cientos de objetos frente a los millones de R4-1), y «ordenar» no la parte.
El generador **nunca** escribe una regla por fila ni un `sqref` de varios
rangos (R127), y los ficheros hostiles de R4-1 se siguen rechazando: sus
tests (`test_f036_r118_…` con los constructores de T39) **no se tocan** y
tienen que seguir en verde. Ojo al construirlos: insertan su
`<conditionalFormatting>` hostil en el XML de «Incidencias» de una plantilla
generada, que ahora puede traer ya una regla; si algún constructor depende
de que no hubiera ninguna, se arregla **el constructor** (el fichero hostil
tiene que seguir siendo el mismo ataque), no la comprobación.

**Cómo se prueba** (`test_f036_r127_…`, en `test_f036_lector_aislado.py`
junto a los de T41, con `_legitimos()`): el Excel de errores más grande,
`<= PRESUPUESTO // 2` elementos; en la plantilla completa, exactamente un
`<conditionalFormatting>` con un `sqref` sin espacios (un rango) y un
`<cfRule>`, y en el Excel de errores, ninguno; las partes del ZIP, las de
siempre y sin imágenes; y los que ya existen y no se tocan: un quinto del
presupuesto, `_doble_al_mib` del descomprimido y del JSON, los pasos baratos
y la lectura de los dos por el hijo real, que da el mismo `LibroLeido` que
el lector en proceso.

*Los topes tras la enmienda 10 bis.* El generador vuelve a cambiar, así que
**se mide otra vez** (T55 el «antes», que es HEAD con el formato de la
décima; T57 el «después»), en la misma máquina y con el mismo método que
T50/T52. Qué cambia en el fichero:

| Qué | Dónde | Cuánto, estimado |
|---|---|---|
| Fuera: `<pageSetup>`, `<headerFooter>` con `<oddFooter>`, el atributo `fitToPage` | hoja «Incidencias» | −3 elementos |
| Fuera: `_xlnm.Print_Titles` | `xl/workbook.xml` | −1 elemento |
| Dentro: dos `<conditionalFormatting>` más en la plantilla y el `v2` (tres en total) y dos en el Excel de errores (antes, ninguno), cada uno con su `<cfRule>` y su `<formula>` | hoja «Incidencias» | +6 elementos |
| Dentro: los `<dxf>` de las reglas 1 (borde de cuatro lados con su color: ~10 elementos) y 2 (relleno: ~4), y el contenedor `<dxfs>` en el Excel de errores | `xl/styles.xml` | +~15 elementos |
| Menos estilos estáticos: el cuerpo pierde el borde y `I` el relleno; las 9.000 celdas siguen existiendo con su `s="…"` | hojas y `xl/styles.xml` | ningún elemento en las hojas; puede haber menos `<xf>` (decenas como mucho) |

Estimación: del orden de +15 elementos en la plantilla y en el Excel de
errores más grande, frente a los 984 de margen a la guarda; bytes
descomprimidos casi iguales (unos cientos de bytes de reglas, quizá menos
por los estilos); el JSON de `leer_en_hijo`, **idéntico** (el lector no lee
estilos). **La estimación no vale: se mide.** Los márgenes que hay que
conservar son los de la tabla de arriba, sin cambios, y la regla de decisión
la de arriba con el orden de recorte de la 10 bis.

**Los `sqref` legítimos y R4-1, tras la 10 bis.** Lo dicho arriba vale para
los **tres** `sqref`: `A2:I1001`, `I2:I1001` y `A2:H1001`, un rango cada uno,
tres objetos al cargar. Siguen sin lista blanca ni excepción: el lector no
distingue un `sqref` legítimo de uno hostil, y el hostil lo para el tope del
hijo. El constructor hostil «formato-condicional» de T39 inserta su propio
`<conditionalFormatting>` delante de `<dataValidations`, detrás de los
legítimos: con tres legítimos sigue siendo el mismo ataque. Si algún
constructor contaba las reglas de la plantilla, se arregla el constructor.

**Cómo se prueba, tras la 10 bis** (`test_f036_r127_…`, en
`test_f036_lector_aislado.py`, con `_legitimos()`): en la plantilla completa,
**exactamente tres** `<conditionalFormatting>`, cada uno con un `sqref` sin
espacios y una `<cfRule>`, en el orden y con los rangos de §3.6; en el Excel
de errores más grande, **exactamente dos** (`A2:I1001` e `I2:I1001`); el
Excel de errores más grande `<= PRESUPUESTO // 2`; las partes del ZIP, las de
siempre y sin imágenes; ningún `<conditionalFormatting>` en las otras tres
hojas; y los que ya existen y no se tocan (un quinto del presupuesto,
`_doble_al_mib` del descomprimido y del JSON, los pasos baratos y la lectura
por el hijo real con el mismo `LibroLeido`).

*El hijo.* Recibe los bytes del fichero (≤ 2 MiB) y, nada más empezar:

1. aplica el tope de memoria: en Linux,
   `resource.setrlimit(resource.RLIMIT_AS, (BYTES_MEMORIA_HIJO, BYTES_MEMORIA_HIJO))`
   (R119). `RLIMIT_AS` limita el **espacio de direcciones**, no la memoria
   residente: es más estricto que el uso real, y el hijo no arranca hilos (cada
   pila reserva espacio). Una reserva que no cabe hace saltar `MemoryError` en
   Python; el hijo **no** la captura: sale con un código propio, que el padre
   lee como `MEMORIA`;

   1 bis. *(novena enmienda del 2026-10-01; R119, hallazgo R5-1)* aplica el
   tope de **CPU**, en el mismo sitio y con el mismo módulo: en Linux,
   `resource.setrlimit(resource.RLIMIT_CPU, (s, s))` con
   `s = math.ceil(segundos) + MARGEN_SEGUNDOS_CPU`, blando y duro iguales, como
   el de memoria. Los dos topes se ponen **antes** de mandar el byte que dice
   si se aplicaron y antes de leer;
2. lee con `_abrir` + `_extraer` (las de siempre: solo lectura, R115);
3. serializa el `LibroLeido` a **JSON** —`identificador`, `version`,
   `obra_codigo`, `cabecera`, `filas` (`numero`, `celdas` por columna con
   `valor`, `es_formula`, `es_fecha_o_booleano`, `texto_original`),
   `parece_formato_antiguo`, `datos_fuera_del_tope`— o, si la lectura dio un
   error de dominio (`no_es_xlsx`, `cabecera_distinta`…), `{"error": {codigo,
   motivo}}`, y lo manda por el canal con `send_bytes`.

**JSON y no `pickle`**: el padre no ejecuta nada al leerlo, y el esquema se
valida campo a campo (tipos, número de filas ≤ 1002, columnas conocidas); algo
que no cuadra es `fichero_sospechoso`. Un error de dominio que manda el hijo se
vuelve a levantar en el padre **con su mismo código**, así que los 400 que ya
existían (`no_es_xlsx`, `cabecera_distinta`…) no cambian.

*El padre.* `ejecutar` arranca el hijo, espera el resultado con el tope de 30 s
y, si se pasa, `terminate()`, y `kill()` si sigue vivo al segundo; siempre
`join()`. Cualquier salida que no sea `OK` con un JSON válido —`TIEMPO`,
`MEMORIA`, `MURIO` (código de salida distinto de 0 o señal),
`DEMASIADO_GRANDE`, esquema malo— es `FicheroNoEsPlantilla("fichero_sospechoso",
"El fichero no se ha podido leer en el tiempo y la memoria que tiene la
plantilla.")`: un 400, **sin 5xx** y sin escribir nada. El log lleva el estado,
los segundos y si el tope de memoria se aplicó; ningún contenido.

*Cómo arranca el hijo.* En Linux, **`forkserver`**, con
`set_forkserver_preload` del módulo del hijo: el servidor de *fork* se arranca
una vez por proceso de la Function (con *spawn*, sin heredar los hilos del
*worker* de Functions) y ya trae `openpyxl` importado; cada hijo es un *fork* de
ese servidor, **barato** (decenas de ms), y aplica su `setrlimit` al empezar.
**`fork` a secas, no**: el *worker* de Python de Azure Functions tiene hilos
(gRPC), y hacer *fork* de un proceso con hilos puede dejar cerrojos tomados en el
hijo. **`spawn` por cada lectura, tampoco en Linux**: cuesta reimportar Python y
`openpyxl` cada vez (del orden de 0,5–1 s). En Windows no hay `forkserver`: se
usa **`spawn`**. T40 mide el coste de arranque del primer hijo y de los
siguientes en las dos plataformas y lo anota.

*El tope de memoria según la plataforma (R119).*

- **Azure** (Function App en **Linux**, Python 3.12, Flex Consumption:
  `infra/desplegar_backend.ps1`): `setrlimit` existe y se aplica.
- **Windows en local**: `resource` no existe. Con `ENTORNO` en `local` o `test`,
  se lee **solo con el tope de tiempo** y se registra una vez un aviso
  (`lector_aislado: sin tope de memoria en esta plataforma`). Con `ENTORNO` en
  `dev` o `pro` y sin `setrlimit`, la lectura **no se hace**: 503
  (`LectorSinAislamiento`), porque en el entorno desplegado no se lee nunca sin
  el tope. No pasa en Azure, que es Linux; el test lo fija igual.

*El tope de CPU del hijo, para el hijo huérfano (R119; novena enmienda del
2026-10-01, hallazgo R5-1 de la review 5).*

- **El hueco.** El tope de 30 s de reloj lo pone el **padre** (`_recibir` y
  `_acabar`). Si el *worker* muere a mitad de una lectura (reciclado,
  despliegue), el hijo queda bajo el servidor de *fork* y nadie lo mata: sigue
  hasta acabar. La memoria seguía topada; la CPU, no (visto por la review 5
  con un fichero de R4-1: vivo a los +22 s; medido por la review 6 en Linux,
  matando al padre con los tres ficheros de R4-1: 33,0 s, 30,2 s y **60,0 s**
  de CPU antes del arreglo, y 30,6 s, 30,2 s y **34,9 s** con él).
  *Errata corregida el 2026-10-02 (review 6, R6-2):* aquí decía «del orden de
  90–110 s de CPU», una estimación de la review 5 con medidas de Windows, no
  una medida en Linux. Dos de los tres acaban solos antes de los 35 s; el tope
  acota el tercero y cualquier fichero que gaste CPU sin gastar memoria, que
  sin tope no tenía límite.
- **El arreglo.** El hijo se pone él mismo un `RLIMIT_CPU` (paso 1 bis de «El
  hijo»). Al llegar a su tope, **el sistema lo mata por señal**; el hijo no la
  captura ni la maneja. Con el padre muerto no hay a quién responder; con el
  padre vivo, saldría como `MURIO` y sería `fichero_sospechoso`, como cualquier
  otra muerte: **ningún estado nuevo**.
- **`RLIMIT_CPU` cuenta CPU, no reloj.** Suma el tiempo de CPU del proceso
  (usuario y sistema); un hijo que espera sin gastar CPU no lo alcanza nunca.
  Por eso **no sustituye** al tope de reloj del padre, que **no cambia**: lo
  complementa para el caso en que el padre ya no está. La lectura es CPU casi
  pura, así que para el huérfano los dos relojes van a la par. El contador del
  hijo empieza en cero: cada hijo es un *fork* del servidor, y el *fork* no
  hereda el tiempo de CPU gastado.
- **El margen: 5 s.** El hijo no arranca hilos, así que no puede gastar más
  CPU que reloj. Con el padre vivo muere como muy tarde a los 32 s de reloj
  (30 de tope, más `SEGUNDOS_PARA_MORIR` de `terminate` y otro tanto de
  `kill`), antes de los 35 s de CPU: el tope de CPU **no gana nunca** al del
  padre, el estado que ve el padre con un fichero lento sigue siendo `TIEMPO` y
  los tests de R118 no cambian. Los 3 s que sobran cubren el redondeo a
  segundos enteros. Más margen solo alargaría lo que gasta un huérfano.
- **Plataforma.** Igual que el tope de memoria: Linux (Azure) lo tiene y se
  aplica; en **Windows** `resource` no existe y **no se aplica**. No añade
  regla propia: en `dev`/`pro` sin `setrlimit` ya no se lee (503 por el tope de
  memoria), y en `local`/`test` se lee con el tope de reloj del padre, como
  hoy. Si `resource` existe y `setrlimit(RLIMIT_CPU)` falla, el error **no se
  captura** (mismo criterio que `_aplicar_tope_de_memoria`): el hijo muere
  antes de leer.
- **Traza: la misma, sin campo nuevo.** No hay un «tope de CPU aplicado»
  aparte. Los dos topes se ponen juntos y antes del byte del canal, así que
  `limite_memoria_aplicado` verdadero quiere decir que se pusieron **los dos**
  (si uno falla, el hijo muere sin mandar el byte). Es lo más simple: ni un
  segundo byte en el canal, ni un campo más en `SalidaHijo`, ni otra línea de
  log. `tope_de_memoria_disponible()` no cambia.
- **Lo que no cubre, dicho.** Un huérfano **parado** sin gastar CPU no moriría
  por este tope; tampoco gasta nada, y la lectura no espera a nadie.

*¿Cabe en la instancia? (R120)* La Function App se crea en **Flex Consumption
sin `--instance-memory`** (`infra/desplegar_backend.ps1`), así que su instancia
tiene la memoria por defecto, **2.048 MB** (la review 4 lo da por bueno). Las
cuentas:

| Qué | Memoria |
|---|---:|
| Hijo, como mucho | 1.024 MB (tope de espacio de direcciones; lo residente es menos) |
| *Worker* de Python con la Function cargada, más el servidor de *fork* con `openpyxl` | del orden de 200–400 MB (**a medir en T29**) |
| *Host* de Functions | del orden de 100–200 MB (**a medir en T29**) |
| Padre, durante el recuento de R117 *(octava enmienda bis)* | hasta ~100 MB (< 6 × el tope descomprimido; 80,8 MiB medidos), **antes** de arrancar el hijo y liberado al acabar |
| **Total estimado** | **~1,3–1,6 GB de 2,0 GB** (el recuento del padre y el hijo no coinciden en el tiempo) |

Cabe, **con una sola lectura aislada a la vez por proceso**. Python en Flex
Consumption atiende por defecto una petición HTTP por instancia, pero eso es
configuración y puede cambiar; por eso R120 lo hace explícito en el código: un
semáforo de una plaza en `lector_aislado.py`. Si al llegar una lectura hay otra
en curso y no queda libre en **5 s**, 503 «otra importación en curso; reintenta»
(D-30). **Riesgo, dicho**: si alguien baja la memoria de la instancia a 512 MB,
sube la concurrencia o sube `FUNCTIONS_WORKER_PROCESS_COUNT`, deja de caber; va
a `docs/INTEGRACION.md` («Qué se rompe si alguien toca algo») en T44. No se toca
el número que fijó el humano; si T29 mide que no cabe, se para y se le lleva.

*Tiempo de la petición.* 30 s del hijo, más los pasos del padre (Sigrid, la
base, el Excel de errores: unos pocos segundos), quedan por debajo de los 40 s
del front y los 45 s del proxy. Un fichero legítimo se lee en menos de un
segundo (más el arranque del hijo).

*Cómo se prueba* (`tests/test_f036_lector_aislado.py`, nombres
`test_f036_r118_…`, `r119_…`, `r120_…`):

- **Sin sistema operativo, con un doble de `EjecutorAislado`**: `OK` con JSON
  válido → el `LibroLeido` esperado; `OK` con un error de dominio → el mismo
  código; `TIEMPO`, `MEMORIA`, `MURIO`, `DEMASIADO_GRANDE`, JSON roto, esquema
  malo (tipos, filas de más, columna desconocida) → `fichero_sospechoso`; los
  pasos 1–2 bis rechazan **sin** llamar al ejecutor (orden); el semáforo ocupado
  más de 5 s → 503 sin llamar al ejecutor; `dev`/`pro` sin `setrlimit` → 503
  (`LectorSinAislamiento`); `local`/`test` sin `setrlimit` → lee y avisa;
- **el padre no lee con `openpyxl`**: `lector_aislado.py` no lo importa (test de
  arquitectura), y con `openpyxl.load_workbook` parcheado en el padre para
  reventar, una lectura real por el hijo sigue funcionando;
- **con el ejecutor real** (topes **inyectados** pequeños para que el test sea
  rápido —p. ej. 3 s y 256 MB— y otro test que fija los de producción, 30 s y
  1 GiB): un hijo que no acaba se mata y da `TIEMPO` (en todas las plataformas);
  un hijo que reserva más que el tope da `MEMORIA` (**solo en Linux**,
  `skipif(sys.platform != "linux")`); los ficheros hostiles de R4-1 (un
  `<dataValidation>`, un `<conditionalFormatting>` y un `<scenario>` con un
  `sqref` de muchos rangos hasta el tope descomprimido) se rechazan con
  `fichero_sospechoso` antes del tope más el arranque, y el pico de la memoria
  del padre (`tracemalloc` en el padre) queda **por debajo de 6 veces el tope
  descomprimido** (resultado acotado más el recuento de R117; *octava
  enmienda bis: decía «no crece más allá del resultado acotado»*);
- **los ficheros hostiles de todas las reviews** (fila lejana, rangos al cargar,
  comentario sobre rango, los siete de la review 3, `sheet1.dat`, los de R4-1):
  rechazados a tiempo, en el padre o en el hijo, con el pico del padre por
  debajo del mismo tope fijo (6 veces el tope descomprimido);
- **lo legítimo entra**: la plantilla completa y el Excel de errores más grande
  se leen por el hijo real y dan el mismo `LibroLeido` que el lector en proceso;
- *(novena enmienda)* **el tope de CPU** (`test_f036_r119_…`, los dos primeros
  **solo en Linux**, `skipif(sys.platform != "linux")`): (1) el hijo huérfano:
  se arranca `_principal_hijo` en un proceso con un tope de CPU pequeño (1–2 s)
  y una función de prueba que gasta CPU sin parar, **sin el reloj del padre**
  (nadie llama a `terminate` ni a `kill`; solo un `join` con un tope holgado
  para que el test no cuelgue): el proceso **muere solo, por señal**
  (`exitcode` negativo) en pocos segundos; (2) cuenta CPU y no reloj: con el
  mismo tope, un hijo que **duerme** más que el tope y luego responde, acaba
  bien; (3) en todas las plataformas, con `setrlimit` doblado: el valor que se
  pide es `math.ceil(segundos) + MARGEN_SEGUNDOS_CPU`, blando y duro iguales, y
  `MARGEN_SEGUNDOS_CPU == 5` (junto al test que fija los topes de producción);
  (4) sin `resource` (Windows, o doblado): no se aplica ninguno de los dos y el
  byte del canal es `0`, como hoy. En Windows (1) y (2) se saltan: su evidencia
  es la ejecución en un **contenedor Linux**, como hizo la review 5, pegada en
  el informe.

**Lo que crece el padre (octava enmienda bis del 2026-10-01; hallazgo
H-T40-1, opción (1) del líder).** El padre crece, como mucho, **el resultado
acotado (`MAX_BYTES_RESULTADO`, 11 MiB) más lo que gasta el recuento de R117**
del paso 2 bis, que R118 deja en el padre. *Expat* guarda la etiqueta de
apertura **entera, con sus atributos**, antes de llamar al manejador, y
`pyexpat` la copia luego a `str`; así que el recuento gasta unas **5 veces el
elemento más grande**, y el elemento más grande lo acota el **tope
descomprimido** (`MAX_BYTES_DESCOMPRIMIDOS`, 17 MiB). Medido por el
implementer con `tracemalloc` en el padre (`progress/impl_F-036.md`,
«T42–T44»): **80,8 MiB** con los ficheros de R4-1 de 17 MiB (un solo `sqref`
enorme); 0,5–0,7 MiB con los siete de la review 3 y el `sheet1.dat`. El coste
es lineal en el tamaño del elemento y **no** depende de lo que costaría en
`openpyxl` (1,6 GB en T39).

- **Por qué cabe.** El pico del padre durante una lectura queda por debajo de
  **6 veces el tope descomprimido** (102 MiB), que cubre los dos conceptos.
  Sumado a la cuenta de «¿Cabe en la instancia?» —instancia de **2.048 MB**,
  hijo de **1 GiB**—, el total sigue por debajo de los 2 GB: el recuento y el
  hijo **no coinciden** en el tiempo (el recuento acaba antes de arrancar el
  hijo, y su memoria se libera al acabar), y una sola lectura a la vez por
  proceso (R120).
- **Por qué no un tope de bytes por etiqueta** antes de *expat* (opción 2):
  sería otra medida por estructura dentro del recuento, con su propio N
  legítimo que medir, y reabriría R117 justo cuando R118 ha cerrado la clase.
- **Por qué no mover el recuento al hijo** (opción 3): contradice R118, que
  deja en el padre las comprobaciones baratas para rechazar casi todo lo
  hostil sin pagar el arranque de un proceso; y el hijo tampoco ganaría nada
  que el tope descomprimido no acote ya.

> **Octava enmienda del 2026-10-01 (review 4, R4-1; opción (A) del humano con
> los límites doblados).** Hasta aquí el lector leía en el proceso de la
> petición, y cada hueco de coste se cerraba con un tope específico. R115 y
> R117 se quedan como primera línea barata; R118 es la red de debajo.

### 5.3 · `BandejaPort` y su repositorio

```python
@dataclass(frozen=True)
class RegistroImportacion:
    importacion_id: UUID; hash_fichero: str; nombre_fichero: str
    obra_codigo: str; plantilla_version: int; importado_por: str
    importado_at_utc: datetime; filas_leidas: int; filas_con_error: int

@dataclass(frozen=True)
class FilaImportada:
    fila: int; estado: EstadoFilaImportada; incidencia_id: UUID | None
    duplicada_de_fila: int | None; existente_id: UUID | None

@dataclass(frozen=True)
class ResultadoImportacion:
    importacion: RegistroImportacion; ya_importado: bool; estado: EstadoImportacion
    nuevas: int; duplicadas_en_fichero: int; ya_en_bandeja: int; con_error: int
    filas: tuple[FilaImportada, ...]      # vacío si ya_importado

class BandejaPort(Protocol):
    def importacion_completa_por_hash(self, *, hash_fichero: str) -> ResultadoImportacion | None: ...
    def registrar(self, *, importacion: RegistroImportacion,
                  grupos: tuple[GrupoDeClave, ...]) -> ResultadoImportacion: ...
    def listar(self, *, obra_codigo: str, limite: int) -> tuple[IncidenciaEnBandeja, ...]: ...
```

`registrar` hace, en **una** transacción (R40):

1. `INSERT` de la importación, con `estado` = `parcial` si
   `filas_con_error > 0` y `completa` si no.
2. `INSERT` de la **primera** fila de cada grupo, en bloque, con
   `ON CONFLICT (obra_codigo, clave_duplicado) WHERE duplicada_de IS NULL DO
   NOTHING RETURNING incidencia_id, clave_duplicado` (R41).
3. Para las claves que no volvieron: `SELECT` de la incidencia existente →
   `ya_en_bandeja` para **todo** el grupo (R38).
4. `INSERT` del resto de filas de los grupos cuya primera sí entró, con
   `duplicada_de` = la primera (R37).
5. `UPDATE` de los recuentos de la importación y `COMMIT`.

Con **cero** filas válidas (R70) se hace solo el paso 1 y el 5: la importación
consta, parcial, con 0 nuevas.

Dos subidas simultáneas de los mismos bytes: las dos se procesan, el índice
único deja una sola copia de cada fila, y constan dos importaciones —una con
las filas nuevas y otra con todo `ya_en_bandeja`—. Es lo que ya pasaría si la
misma persona pulsa dos veces, y no duplica nada.

Los identificadores (`uuid4`) se generan en Python, como en el resto del
proyecto (`CREATE EXTENSION` está prohibido). Presupuesto: una importación de
1000 filas son cinco sentencias y debe quedar por debajo de 10 s (se mide en
T29; el proxy corta a 45 s).

> **Enmienda del 2026-09-28.** `importacion_por_hash` pasa a
> `importacion_completa_por_hash` (R39). El paso 1 hacía `ON CONFLICT
> (hash_fichero) DO NOTHING` y, si no volvía fila, respondía `ya_importado`: el
> `hash_fichero` ya no es único, porque el mismo fichero de una importación
> parcial se vuelve a procesar para recuperar su Excel de errores. Se añaden
> `filas_con_error`, `estado`, `con_error` y el caso de cero filas válidas.

## 6 · SQL

### 6.1 · DDL, schema `postventa`, capa de persistencia propia

Numeración siguiente a `11_historico_estado.sql`. Idempotente, con cabecera que
diga qué construye y de qué lee, y **solo** con las formas que admite
`infrastructure/persistencia/ddl.py` (CREATE TABLE/INDEX IF NOT EXISTS).

`12_importaciones.sql` (lee de: nada):

```sql
CREATE TABLE IF NOT EXISTS postventa.importaciones (
    importacion_id              uuid        PRIMARY KEY,
    hash_fichero                text        NOT NULL,            -- sha256 hex de los bytes
    nombre_fichero              text        NOT NULL,            -- recortado a 255 en el borde
    obra_codigo                 text        NOT NULL,
    plantilla_version           integer     NOT NULL,
    estado                      text        NOT NULL CHECK (estado IN ('completa', 'parcial')),
    importado_por               text        NOT NULL,            -- oid opaco de Entra; dato personal seudónimo
    importado_at_utc            timestamptz NOT NULL,
    filas_leidas                integer     NOT NULL CHECK (filas_leidas >= 0),
    filas_con_error             integer     NOT NULL CHECK (filas_con_error >= 0),
    filas_nuevas                integer     NOT NULL DEFAULT 0 CHECK (filas_nuevas >= 0),
    filas_duplicadas_en_fichero integer     NOT NULL DEFAULT 0 CHECK (filas_duplicadas_en_fichero >= 0),
    filas_ya_en_bandeja         integer     NOT NULL DEFAULT 0 CHECK (filas_ya_en_bandeja >= 0),
    CHECK ((estado = 'parcial') = (filas_con_error > 0))
);
CREATE INDEX IF NOT EXISTS ix_importaciones_hash
    ON postventa.importaciones (hash_fichero, estado);
```

> **Enmienda del 2026-09-28.** `hash_fichero` era `UNIQUE`; se quita y se indexa
> con el estado, que es la consulta del atajo de R39. Se añaden `estado` y
> `filas_con_error`. Las filas con error **no** se guardan (R42).

`13_bandeja_incidencias.sql` (lee de: `12_importaciones.sql`):

```sql
CREATE TABLE IF NOT EXISTS postventa.bandeja_incidencias (
    incidencia_id     uuid        PRIMARY KEY,
    origen            text        NOT NULL CHECK (origen IN ('excel', 'web')),
    importacion_id    uuid        REFERENCES postventa.importaciones (importacion_id),
    fila_origen       integer,
    obra_codigo       text        NOT NULL,
    unidad_codigo     text        NOT NULL,
    unidad_nombre     text        NOT NULL,
    ubicacion         text        CHECK (char_length(ubicacion) <= 48),
    descripcion       text        NOT NULL CHECK (char_length(descripcion) BETWEEN 1 AND 128),
    detalle           text        CHECK (char_length(detalle) <= 2000),
    oficio_codigo     text,
    oficio_nombre     text,
    oficio_ambiguo    boolean     NOT NULL DEFAULT false,
    proveedor_codigo  text,
    proveedor_nombre  text,
    proveedor_ambiguo boolean     NOT NULL DEFAULT false,
    urgencia          text        CHECK (urgencia IN ('urgente', 'seguridad')),
    listado           text        CHECK (listado IN ('primero', 'segundo')),
    clave_duplicado   text        NOT NULL,
    duplicada_de      uuid        REFERENCES postventa.bandeja_incidencias (incidencia_id),
    creada_at_utc     timestamptz NOT NULL,
    CHECK (origen <> 'excel' OR (importacion_id IS NOT NULL AND fila_origen IS NOT NULL)),
    CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL)),
    CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL)),
    CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_bandeja_clave
    ON postventa.bandeja_incidencias (obra_codigo, clave_duplicado)
    WHERE duplicada_de IS NULL;
CREATE INDEX IF NOT EXISTS ix_bandeja_obra
    ON postventa.bandeja_incidencias (obra_codigo, creada_at_utc DESC, fila_origen);
```

> **Enmienda del 2026-09-28.** Se añaden `proveedor_codigo`, `proveedor_nombre`,
> `proveedor_ambiguo` y sus dos `CHECK`: un proveedor ambiguo no lleva código, y
> no hay proveedor sin oficio (el interviniente de §8.9 es oficio + proveedor).
>
> **Segunda enmienda del mismo día.** Se añaden `oficio_ambiguo` y su `CHECK`
> (R99). El último `CHECK` decía `proveedor_nombre IS NULL OR oficio_codigo IS
> NOT NULL`: con un oficio ambiguo no hay código, así que «no hay proveedor sin
> oficio» se comprueba con el nombre.
>
> **Tercera enmienda del mismo día.** Se añaden `proveedor_fuera_de_obrofc` y
> su `CHECK` (R105, §16.6).
>
> **Quinta enmienda del 2026-09-29.** Salen `proveedor_fuera_de_obrofc` y su
> `CHECK` (a F-039, que la añadirá con `ADD COLUMN IF NOT EXISTS` si la
> necesita). `proveedor_ambiguo` se queda: en F-036 siempre es falso, y es la
> costura para F-050 (§15.8).

`14_decisiones_equivalencia.sql` (lee de: nada) — §15.4:

```sql
CREATE TABLE IF NOT EXISTS postventa.decisiones_equivalencia (
    decision_id     bigserial   PRIMARY KEY,
    catalogo        text        NOT NULL CHECK (catalogo IN ('oficio', 'proveedor', 'actividad_oficio')),
    codigo_a        text        NOT NULL,
    codigo_b        text        NOT NULL,
    decision        text        NOT NULL CHECK (decision IN ('mismo', 'distinto')),
    motivos         text,                                 -- los propuestos, p. ej. 'mismo_cif,errata'
    obra_codigo     text        NOT NULL,                 -- desde dónde se decidió; vale para todas (R84)
    decidido_por    text        NOT NULL,                 -- oid opaco de Entra
    decidido_at_utc timestamptz NOT NULL,
    CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")
);
CREATE INDEX IF NOT EXISTS ix_decisiones_equivalencia_par
    ON postventa.decisiones_equivalencia (catalogo, codigo_a, codigo_b, decidido_at_utc DESC, decision_id DESC);
```

> **Sexta enmienda del 2026-09-30 · B5-1, decidida por el humano.** El `CHECK`
> del par decía `CHECK (codigo_a < codigo_b)`; se queda como lo implementó
> el Bloque 5, `CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")`.
> Motivo: `DecisionPar` exige `codigo_a < codigo_b` con el orden de Python, que
> es por punto de código; `COLLATE "C"` compara por bytes, que en UTF-8 es el
> mismo orden, y existe siempre (también en bases con ICU). Con la collation de
> la base (p. ej. `en_US.utf8`), un par como `'B1'`/`'a1'` se ordenaría al
> revés que en Python y el `INSERT` fallaría; hoy no pasa porque los códigos de
> oficio son cifras, pero pasaría con los prefijos `A:`/`O:` de F-039 o con
> F-050. Ninguna otra sentencia depende de la collation: las búsquedas y los
> índices van por igualdad. Como el guard del DDL no deja cambiar un `CHECK`
> una vez aplicado, la decisión consta antes de T27. Lo valida contra un
> PostgreSQL real `test_f036_b2_14_el_par_sigue_el_orden_de_python` en T16.

> **Segunda enmienda del 2026-09-28.** La tabla era
> `postventa.decisiones_proveedor`, en `14_decisiones_proveedor.sql`, sin
> columna `catalogo`, y su índice empezaba por `codigo_a`. Por qué **una**
> tabla con discriminador y no otra para los oficios: el mecanismo es uno
> (§15), y con una tabla hay un puerto, un repositorio, unas sentencias, un
> test de append-only y una sola regla de «manda la última decisión del
> par»; dos tablas duplicarían todo eso para ganar solo la ausencia de una
> columna. El discriminador es necesario de todas formas: un código de
> oficio y uno de proveedor pueden escribirse igual (R95). Por qué **no** un
> YAML versionado para los oficios, aunque no lleven datos personales: el
> mecanismo dejaría de ser uniforme (dos almacenes, dos caminos de lectura,
> y la confirmación de un oficio exigiría un commit y un despliegue en vez
> de un clic en la pantalla).
>
> **Tercera enmienda del mismo día.** El `CHECK` de `catalogo` admitía
> `oficio` y `proveedor`; admite ya `familia_oficio` aunque la medición acabe
> en la identidad (R108, §16.3). En ese catálogo los códigos llevan prefijo
> `F:`/`O:` (§16.4).
>
> **Cuarta enmienda del mismo día.** `familia_oficio` pasa a
> `actividad_oficio`, con prefijos `A:`/`O:` (§16.3). `proveedor` se queda
> en el `CHECK` aunque la agrupación de proveedores salga de F-036 (D-18,
> §15.8): el guard no deja ampliarlo después.
>
> **Quinta enmienda del 2026-09-29.** El `CHECK` se queda con los tres valores
> aunque F-036 solo escriba `oficio`: `proveedor` es de F-050 y
> `actividad_oficio` de F-039, y ninguna de las dos tendrá que tocar el
> esquema.

Notas que van en la cabecera de los `.sql`:

- **Los `CHECK` de `origen`, `urgencia`, `listado`, `estado`, `catalogo` y `decision` se
  generan de los `Enum` del dominio** (`valores_check`), y un test los compara:
  un valor nuevo en el dominio que no llegue aquí rompe la suite, no producción.
  `web` entra ya porque el guard del DDL no admite cambiar un `CHECK` después
  (D-13).
- **No hay columna de estado de revisión**: la revisión es de F-038, que la
  añadirá con su propia tabla (R44), igual que F-028 hizo con el histórico.
- `descripcion` y `detalle` son **texto libre de la propiedad**, y
  `proveedor_nombre` puede ser el nombre de un **autónomo**: no salen en ningún
  log (R47) y solo los devuelve `GET /api/bandeja` a usuarios autenticados.
- `decisiones_equivalencia` **no guarda nombres** (R83) y es **append-only**, como
  `historico_estado`: nada la actualiza ni la borra; manda la última fila de
  cada par.
- Ni una columna binaria: ni el `.xlsx` ni el Excel de errores se guardan.
- Volumen: una importación típica son decenas o cientos de filas de menos de
  1 KB; las decisiones de equivalencia, decenas por obra. No cambia el orden de
  magnitud del disco del servidor compartido.

### 6.2 · Sentencias (`sentencias_bandeja.py`, puro)

`insert_importacion`, `select_importacion_completa_por_hash`,
`insert_primeras`, `select_existentes_por_clave`, `insert_duplicadas`,
`update_recuentos`, `select_bandeja(obra, limite)` con tope duro de 500 aplicado
**también** aquí (dos cinturones, como la cola de F-019), `insert_decisiones`
(varios pares en una sentencia) y `select_ultimas_decisiones(catalogo, codigos)`
(la última decisión de cada par de ese catálogo entre esos códigos, con
`DISTINCT ON`; segunda enmienda del 2026-09-28: no llevaba `catalogo`). Todo
parametrizado; el esquema sale de la configuración como en `sentencias.py`.

### 6.3 · Lecturas de Sigrid (`consultas_catalogo.py`, puro)

```sql
-- SQL_UNIDADES_DE_LA_OBRA · parámetro: el código de obra normalizado
SELECT v.obride, o.cod, o.res, u.cod, u.res
FROM dbo.upv v
JOIN dbo.con o ON o.ide = v.obride
JOIN dbo.con u ON u.ide = v.ide
WHERE LTRIM(RTRIM(o.cod)) = ?
ORDER BY u.cod

-- SQL_OFICIOS_DE_LA_OBRA · parámetro: el obride de la única obra
SELECT a.cod, a.res, p.cod, p.res
FROM dbo.obrofc f
JOIN dbo.auxofc a     ON a.ide = f.ofcide
LEFT JOIN dbo.con p   ON p.ide = f.prvide
WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0
ORDER BY a.cod, p.cod
```

`max_rows = 1000` en las dos. **Dos** lecturas por plantilla, por importación
y por consulta de propuestas. `LEFT JOIN` en el proveedor: una fila de
`obrofc` sin proveedor (en la 0677, `0133`, `0144` y `0166`) es un oficio de la
obra que no ofrece ningún par.

> **Quinta enmienda del 2026-09-29.** `SQL_OFICIOS_DE_LA_OBRA` traía la marca
> de CIF (`DENSE_RANK` sobre `prv.cif`, `LEFT JOIN dbo.prv`), que era de la
> agrupación de proveedores y sale a F-050; y había dos lecturas más,
> `SQL_ACTIVIDADES_DE_PROVEEDORES_DE_LA_OBRA` (`conact` → `auxpronat`) y
> `SQL_ARBOL_ACTIVIDADES`, que salen a F-039 (§16). Eran cuatro lecturas;
> vuelven a ser dos. §15.8 guarda cómo era la marca de CIF.

En las dos, el código de obra se compara **literal** (sin quitar
ceros): es lo que hace §8.9 con `obra`, y lo que tiene que coincidir con el
volcado de F-040.

**La marca de CIF (R90)** *(retirada en la quinta enmienda: pasa a F-050; se
conserva el texto porque es el diseño que reutilizará)*: el CIF/NIF **no sale** de la lectura; sale un número
de orden que solo dice qué filas comparten el mismo CIF normalizado **dentro de
esa respuesta**. No se guarda en ningún sitio, no se registra y no viaja en
ninguna respuesta HTTP. El `DENSE_RANK` sobre las filas con CIF vacío no se usa
(sale `NULL`). La expresión exacta la fija un test carácter a carácter; si
T2 enseña que el `cif` trae prefijo de país o variantes que esta normalización
no iguala, se amplía ahí.

> **Enmienda del 2026-09-28.** `SQL_OFICIOS_DE_LA_OBRA` era un `SELECT DISTINCT
> a.cod, a.res`; ahora trae cada fila de `obrofc` con su proveedor y la marca de
> CIF, porque la columna `Proveedor` y la propuesta de grupos la necesitan. El
> `DISTINCT` de oficios pasa al dominio. Sigue siendo una sola lectura.
>
> **Segunda enmienda del mismo día.** Sin cambios en el SQL: la propuesta de
> oficios usa los oficios de esta misma lectura (`a.cod`, `a.res`), que son
> los que la plantilla enseña. La medición de todo `auxofc` es de T1/T2.

## 7 · Aplicación

### 7.1 · `catalogo_obra.leer_catalogo(puerto, codigo_obra) -> CatalogoObra`

Lee las unidades; con el dominio decide: techo alcanzado →
`CatalogoSinVerificar`; cero filas → `ObraSinUnidades`; más de un `obra_ref`
distinto → `ObraAmbigua`. Con la única obra lee los oficios con sus proveedores
(techo → `CatalogoSinVerificar`) y compone el `CatalogoObra`. Los grupos
vigentes de **oficio** se leen aparte (`EquivalenciasPort`, §15.4); los de
proveedor son, en F-036, cada código su propio grupo (§15.8). *(Quinta
enmienda del 2026-09-29: se leían también las actividades y el árbol, a
F-039, y los grupos de proveedor, a F-050.)*
*(Segunda enmienda del 2026-09-28: decía `EquivalenciasProveedorPort` y solo
los de proveedor.)*

### 7.2 · `plantilla.generar_plantilla(...) -> tuple[str, bytes]`

`normalizar_codigo_obra` → `leer_catalogo` → grupos vigentes de los dos
catálogos → `opciones_de_oficio` → `opciones_de_proveedor` →
`generador.generar` → nombre
`plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx` (la fecha, de `generada_at` en
UTC).

### 7.3 · La importación: contexto y seis pasos

`ContextoImportacion(contenido, nombre_fichero, usuario_oid, ahora, hash,
libro, obra_codigo, catalogo, grupos_oficio, grupos_proveedor, validas, con_error,
agrupadas, resultado,
excel_errores)`. Los pasos viven en `paso_importacion.py` y la composición en el
handler (`docs/CONVENTIONS.md`):

1. **`paso_huella`** — `sha256`; si `importacion_completa_por_hash` devuelve
   algo, el contexto queda resuelto como `ya_importado` y los demás pasos no
   hacen nada (R39: sin Sigrid).
2. **`paso_reconocimiento`** — `LectorPlantillaPort.leer` + `reconocer_plantilla`
   (R16–R20; R21: sin Sigrid ni base, rechazo entero).
3. **`paso_catalogo`** — `leer_catalogo` con la obra de los metadatos y los
   grupos vigentes.
4. **`paso_validacion`** — `validar_filas` (válidas y con error; R33).
5. **`paso_registro`** — `agrupar_por_clave` sobre las válidas +
   `BandejaPort.registrar` (también con cero válidas, R70).
6. **`paso_excel_errores`** — si hay filas con error, compone las
   `FilaPlantilla` con sus valores originales y errores y llama al **mismo**
   generador, con el mismo catálogo y opciones (R62–R65). Va **después** del
   registro: si la base falla, no se entrega un Excel de errores de una
   importación que no consta.

> **Enmienda del 2026-09-28.** Eran cinco pasos y el cuarto levantaba
> `FilasInvalidas` con un solo error. Ahora la validación separa válidas y con
> error, el registro guarda las válidas y un sexto paso genera el Excel de
> errores.

## 8 · Borde HTTP

| Ruta | Éxito | Errores |
|---|---|---|
| `GET /api/plantilla?obra=` | 200, binario (R1) | 400 `CodigoDeObraInvalido`; 404 `ObraSinUnidades`; 409 `ObraAmbigua`, `CatalogoSinVerificar`; 503 Sigrid o base |
| `POST /api/importaciones` | 200 JSON (R43), con `excel_errores` si hay filas con error | 400 `PeticionDeImportacionInvalida`, `FicheroNoEsPlantilla` (`{error, codigo}`); 413; 409 catálogo; 503 Sigrid o base |
| `GET /api/bandeja?obra=&limite=` | 200 JSON (R45) | 400; 503 base |
| `GET /api/catalogos/propuestas?obra=` | 200 JSON (R87): `{obra, oficio: {oficios: [{codigo, nombre, grupo}], grupos: [{etiqueta, codigos}], propuestas: [{codigos, por_pares, motivos, pares: [{codigo_a, codigo_b, motivos}]}], avisos: [{codigos}]}}`; `grupo` son los códigos del grupo vigente del oficio, códigos y motivos ordenados, `nombre` puede ser `null` | 400; 404; 409; 503 |
| `POST /api/catalogos/decisiones` | 200 JSON: `{obra, pares_guardados: [{catalogo, codigo_a, codigo_b, decision, motivos}], grupos_vigentes: {oficio: {grupos, avisos}}}` | 400 `PeticionDeDecisionInvalida` (también un catálogo que no es `oficio`); 409 `CodigoNoEsDeLaObra`, y 409 con su `codigo` si la obra no tiene unidades o es ambigua; 503 |

`POST /api/importaciones` lee el fichero de `req.files` (exactamente uno) y
`usuario_oid` de `req.form`, como hace el front en `POST /api/estado` con el
`oid` que saca de `/.auth/me`. Se compara el tamaño **antes** de construir nada
(R15). El nombre del fichero se recorta a 255 caracteres y se guarda, pero no
se registra en el log (R47).

`GET /api/bandeja` devuelve por fila: `incidencia_id`, `importacion_id`,
`fila_origen`, `unidad_codigo`, `unidad_nombre`, `ubicacion`, `descripcion`,
`detalle`, `oficio_codigo`, `oficio_nombre`, `oficio_ambiguo`, `proveedor_codigo`,
`proveedor_nombre`, `proveedor_ambiguo` (siempre falso en F-036), `urgencia`,
`listado`, `duplicada_de`,
`creada_at_utc`. Nada de `importado_por`.

`POST /api/catalogos/decisiones`: cuerpo `{obra, usuario_oid, confirmado:
true, decisiones: [{catalogo, codigos, decision}]}`. `confirmado` tiene que ser
el booleano de JSON, como en `POST /api/estado`: una decisión que cambia a quién
se manda un industrial, o en qué oficio se da de alta una incidencia, no sale
de un doble clic ni de un `"true"` en texto.

Ninguno de los cinco mira `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO` (R48):
leer Sigrid y escribir en el esquema propio no abren ninguna ventana de
escritura en un sistema ajeno.

> **Enmienda del 2026-09-28.** La importación respondía 422 con los errores de
> fila; ahora responde 200 con ellos y el Excel de errores. Se añaden las dos
> rutas de proveedores y los campos de proveedor de la bandeja. La plantilla
> puede dar 503 por la base: lee los grupos vigentes.
>
> **Segunda enmienda del mismo día.** Las rutas eran
> `/api/proveedores/propuestas` y `/api/proveedores/decisiones`, sin
> `catalogo` en la respuesta ni en las decisiones, y el 409 era
> `ProveedorNoEsDeLaObra`. La bandeja gana `oficio_ambiguo`.
>
> **Sexta enmienda del 2026-09-30 (O-1, B6-18, B6-21).** Las dos filas de
> `/api/catalogos/*` se ponen como quedaron implementadas: la de propuestas
> decía `{oficio: {...}, proveedor: {...}}` (con la quinta enmienda ya no hay
> `proveedor`), y la de decisiones no daba la forma de la respuesta ni decía
> que la obra sin unidades, o ambigua, es 409 (como en la importación: la
> petición está bien, lo que falla es la obra).

## 9 · Front

**Dónde vive (D-1, aprobada)**: página propia en `dev`,
`services/postventa-front/importar.html`, con su componente Alpine
(`appImportacion`, en `js/importacion.js`), y un enlace en la cabecera de
`index.html`. Tres bloques, en el orden en que se usan:

1. **Plantilla** — campo «Código de obra» y botón «Descargar la plantilla»
   (`fetch` → `Blob` → descarga con el nombre de `Content-Disposition`).
2. **Importar** — elegir un `.xlsx` (`accept=".xlsx"`) y «Importar a la
   bandeja». Resultado: la obra, si fue **completa** o **parcial**, el resumen,
   la tabla de filas con su estado y avisos, la lista de errores «Fila N ·
   columna X · problema» y, si hay errores, un botón destacado **«Descargar el
   Excel de errores»** (base64 → `Blob` → descarga con `excel_errores.nombre`),
   con la frase «corrígelo y súbelo otra vez; lo que ya entró no se duplica».
   Un rechazo del fichero enseña su motivo. Sin reintentos automáticos (R52).
3. **Bandeja de la obra** — tabla de solo lectura con `GET /api/bandeja`, con
   las duplicadas marcadas «duplicada de la fila N» y los oficios ambiguos
   marcados «varios códigos en Sigrid: se elige en la revisión». Sin botones de
   editar, descartar ni aprobar: eso es F-038.

La página de oficios repetidos es `oficios.html` (§15.6; era `catalogos.html`
hasta la quinta enmienda).

Cuando F-035 se mergee, su sección «Entrada» (hoy placeholders con
`data-placeholder="F-036"`) llamará a **estas mismas** funciones de
`js/api.js`, `js/importacion.js` y `js/catalogos.js`; es trabajo de quien
mergee segundo. Las páginas propias pueden quedarse como redirección.

`js/importacion.js` y `js/catalogos.js` exportan funciones puras (formatear
el resumen, ordenar errores, texto de cada estado, nombre de fichero de
`Content-Disposition`, decodificar el base64, componer el cuerpo de una
decisión) que se prueban con `node --test`, como el resto del front.

> **Enmienda del 2026-09-28.** Se añaden la descarga del Excel de errores, el
> estado completa/parcial, la marca de proveedor ambiguo y la página de
> proveedores.
> **Segunda enmienda del mismo día**: la página pasa a `catalogos.html` (con
> `js/catalogos.js`) y se marcan también los oficios ambiguos.

## 10 · La migración del Excel actual (entregable 3)

### 10.1 · El flujo, de punta a punta

```
T2  humano: 26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson <fuera del repo>
T23 implementer: scripts/migracion_f036.py + CLI + tests (con catálogo y original falsos)
T24 implementer: redacta scripts/migracion_f036_correcciones.yaml (la PROPUESTA)
    y genera progress/migracion_F-036.md con el script en modo --solo-informe
T25 PARADA humano: revisa el informe; lo que cambie, lo aplica el implementer
T27 humano: despliega, confirma en oficios.html (era catalogos.html) los grupos de oficios
    de la 0677 y descarga los grupos vigentes (JSON, solo códigos)
T28 humano: ejecuta el script con --grupos → creacion_incidencias_v2.xlsx
    en su OneDrive
```

> **Segunda enmienda del 2026-09-28.** El último paso era «T26 humano: ejecuta
> el script». El `v2` definitivo espera ahora a que haya grupos confirmados
> en el entorno desplegado (T27), porque sus oficios se escriben con la
> etiqueta del grupo (R97).

> **Undécima enmienda del 2026-10-03.** En T28 el JSON del catálogo **no**
> es el de T2: se vuelve a leer de Sigrid justo antes de migrar, con el
> mismo `.ps1`, y los grupos se descargan de `oficios.html` justo antes
> (R131). Lo hace el guion del líder para T28, fuera del repositorio:
>
> ```
> T28 humano/líder: oficios.html → grupos vigentes de la 0677 (JSON, fuera del repo)
>                   26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson <fuera del repo, del día>
>                   migrar_excel_f036.py --catalogo <ese JSON> --grupos <ese JSON> --sobrescribir
> ```
>
> El `v2` del 2026-09-29 se generó con el JSON de T2 y el entorno, que lee
> Sigrid en vivo, lo validó contra la 0677 de otro día: §10.5.

### 10.2 · La tabla de correcciones (`migracion_f036_correcciones.yaml`)

Versionada: la muestra ya está versionada en Markdown y **no lleva datos
personales** (doc. 05). **No lleva nombres de proveedor** (R58, R83): el
proveedor, si lo hay, lo pone el script con la regla de R91. Una entrada por
fila del original, en su orden:

```yaml
obra: "0677"
unidad: "<etiqueta de la unidad, p. ej. la de 0677.03VILLA 1.>"   # D-9
filas:
  - origen: 1                                  # fila del original (la 1 es la primera incidencia)
    ubicacion_original: "SALA/ ESTUDIO"        # para cotejar (R54)
    texto_original: "Choca ventana con ascensor"
    resultado:                                 # 0, 1 o más filas nuevas
      - ubicacion: "Sala / estudio"
        descripcion: "..."
        detalle: null
        oficio: "Carpintería de aluminio"      # nombre EXACTO de un oficio de Sigrid de la obra (R97)
        urgencia: null
        listado: null
    cambios:                                   # motivo de cada cambio; obligatorio si hay alguno
      - "ubicación normalizada"
    propuesto: []                              # campos que son juicio del implementer (p. ej. "oficio")
```

Reglas que el script y sus tests hacen cumplir (R54, R57): cada `origen` de 1 a
N aparece una sola vez; `resultado: []` exige un `cambios` que diga por qué se
descarta; cada fila de `resultado` pasa `validar_filas` con el catálogo real;
ninguna descripción ni detalle contiene «peligro de seguridad» (normalizado) ni
patrones de remisión («como en los otros», «como en todos», «igual que»).

Criterios de la propuesta, a aplicar por el implementer y a validar por el
humano: ubicaciones de la muestra llevadas a la lista cerrada (`DORMITORIO 1
BAÑO` y `DORMITORIO BAÑO 1` → `Baño del dormitorio 1`; `GENERALES` → `General
(toda la unidad)`; `TIRO DE ESCALERA` → `Escalera`); una fila por defecto (p.
ej. «Pared de casoneto sin anclaje… Puerta corredera del baño suelta…» son
dos); las referencias («como en los otros baños») se reescriben con lo que
significan; «PELIGRO DE SEGURIDAD» → `Urgencia: Peligro para la seguridad`;
«ERROR ESTRUCTURAL» → `Urgencia: Urgente` y el texto conservado en el detalle;
descripciones de más de 128 → descripción corta + detalle; mayúsculas de
énfasis → frase normal; erratas evidentes corregidas («Reahacer», «inglentes»,
«lavavo»); oficio: el nombre de la muestra («Mamparas», «Mobiliario
cocina»…) si es **exactamente** el de un oficio de Sigrid de la obra; si no
lo es, el nombre exacto del oficio de la obra que evidentemente es, marcado
en `propuesto`; y donde no venga, **propuesto** a partir del texto. El YAML
guarda siempre un **nombre de Sigrid**, nunca una etiqueta de grupo: los
grupos pueden cambiar y el nombre no. `Listado` vacío (D-5).

> **Segunda enmienda del 2026-09-28.** El oficio del YAML era «etiqueta exacta
> del catálogo de la obra» y el criterio decía «el de la muestra si es
> exactamente —o evidentemente— uno de la obra». Ahora es un nombre exacto de
> Sigrid, que el script lleva a su grupo (R97).

### 10.3 · El script

`scripts/migrar_excel_f036.py`, lanzado por el humano con el intérprete del
servicio:

```
.venv\Scripts\python.exe scripts\migrar_excel_f036.py ^
  --original "<OneDrive>\postventa\creacion_incidencias.xlsx" ^
  --catalogo "<ruta del JSON de T2>" ^
  --correcciones scripts\migracion_f036_correcciones.yaml ^
  --grupos "<JSON de grupos vigentes de T27>" ^
  --salida "<OneDrive>\postventa\creacion_incidencias_v2.xlsx" ^
  --informe ..\..\progress\migracion_F-036.md [--sobrescribir] [--solo-informe]
```

Qué hace, en orden, y para en el primer fallo sin escribir nada:

1. `sha256` del original; se niega si `--salida` es el original (resuelto) o si
   existe sin `--sobrescribir` (R53).
2. Lee el original con `openpyxl` en modo lectura (el lector de la plantilla lo
   rechazaría, a propósito) y lo coteja con la tabla (R54).
3. Carga el catálogo del JSON y los grupos vigentes de `--grupos` (sin él,
   cada código es su propio grupo y solo se admite `--solo-informe`); calcula
   `opciones_de_oficio` y `opciones_de_proveedor` con esos grupos; lleva cada
   nombre de oficio del YAML a su código (debe ser **exactamente** el de un
   oficio de la obra, o para) y el código a su grupo, cuya etiqueta es la que
   se escribe (R97); y compone las `FilaPlantilla`, con `Proveedor` según R91
   (R55). *(Undécima enmienda: si el nombre no es de la obra pero sí de
   `oficios_catalogo`, la fila va con oficio y proveedor vacíos y no se para,
   R128; solo para la errata, que no es de ningún oficio de Sigrid, R97;
   §10.5.)*
4. Genera el `v2` con `GeneradorPlantillaOpenpyxl` y lo vuelve a leer con
   `LectorPlantillaOpenpyxl` + `reconocer_plantilla` + `validar_filas`: cero
   errores o no se escribe (R56).
5. Escribe el `v2` y el informe; vuelve a calcular el `sha256` del original y
   falla si ha cambiado (R53).

`--solo-informe` hace 1–4 sin escribir el `v2` (para T24, sin `--grupos`). El
JSON de `--grupos` es el que descarga `oficios.html` (R98; era `catalogos.html`):
`{"obra", "oficio": [["<cod>", "<cod>"], …]}` *(quinta enmienda: sin `"proveedor"`)*, solo
códigos y solo los grupos de más de un código. El JSON del catálogo
tiene esta forma, y la escribe `infra/26_catalogos_plantilla_sigrid.ps1`:
`{"obra": {"codigo", "nombre"}, "unidades": [{"codigo", "nombre"}],
"oficios_obra": [{"oficio_codigo", "oficio_nombre", "proveedor_codigo",
"proveedor_nombre", "marca_cif"}], "oficios_catalogo": [{"codigo",
"nombre"}]}` —el último, todo `auxofc`, solo para la medición de T8—. Vive
**fuera** del repositorio: lleva nombres de proveedor. *(Undécima enmienda:
`oficios_catalogo` deja de ser solo para la medición; la migración lo usa
para distinguir la errata del oficio que ha salido de la obra, §10.5. El
`.ps1` ya lo escribe siempre con `-SalidaJson`, sin filtrar bajas, y no
cambia.)*

**Por qué los grupos llegan por fichero y no leyendo la base**: el script
corre en local y no tiene por qué alcanzar el PostgreSQL compartido; el
fichero de grupos es solo de códigos, se descarga de la pantalla desplegada
(R98), vive fuera del repositorio y hace el resultado **reproducible**: el
mismo YAML, el mismo catálogo y el mismo fichero de grupos dan el mismo `v2`.
Si después se confirman más grupos, las etiquetas del `v2` pueden quedar
antiguas: el importador lo detecta y esas filas vuelven en el Excel de
errores con las listas buenas (§4.4); o se regenera el `v2` con un fichero
de grupos nuevo.

> **Segunda enmienda del 2026-09-28 (§10.3).** Se añaden `--grupos`, la
> resolución de los nombres de oficio y `oficios_catalogo` en el JSON. El
> último párrafo se titulaba «Por qué el `v2` va sin grupos confirmados» y
> defendía generarlo sin grupos; con los oficios agrupados, un `v2` sin
> grupos enseñaría el mismo oficio dos veces, que es justo lo que el humano
> quiere evitar.

> **Enmienda del 2026-09-28 (§10.2 y §10.3).** Se añaden R91, la regla de no
> guardar nombres de proveedor en el YAML, el paso 3 con las opciones de
> proveedor y la forma nueva del JSON (`oficios` pasaba a ser lista de oficios
> distintos; ahora son filas de `obrofc`). Las tareas pasaban de T19–T22 a
> T23–T26.

### 10.4 · Cómo lo revisa el humano antes de darlo por bueno

1. **El informe** (`progress/migracion_F-036.md`, T25): una tabla por
   ubicación original con «fila original · texto original → filas nuevas
   (ubicación, descripción, detalle, oficio, urgencia) · cambios · propuesto».
   Arriba, los recuentos: filas originales, filas nuevas, separadas,
   descartadas, oficios completados, oficios cuyo nombre de la muestra no era
   exactamente el de Sigrid, oficios que caen en un grupo de varios códigos,
   proveedores completados por R91, urgencias marcadas. **Sin nombres ni
   códigos de proveedor** (R116): el informe dice, por fila, «proveedor
   completado (único de la obra para ese oficio)», y arriba **cuántas filas
   llevan proveedor y por qué regla** (R91); nunca el nombre ni el código. El
   `v2` sí lleva el proveedor, porque es la plantilla, pero no se versiona.
   *(Undécima enmienda)*: entre los recuentos, siempre, las **filas nuevas
   sin oficio porque ese oficio ya no está en la obra en Sigrid**; y si hay
   alguna, su sección justo después de los recuentos (R130, §10.5).

   > **Sexta enmienda del 2026-09-30 (review 1, cambio 3).** Decía «y el
   > código, nunca el nombre». El informe de T24/T25 salió con 5 códigos de
   > proveedor reales, 46 veces, en un fichero versionado. Chocaba con R58
   > («sin datos personales») y con el riesgo 14 de §12: el código de un
   > autónomo lleva a su nombre en cuanto se mira Sigrid. El informe se
   > regenera sin ellos (Bloque 10); los commits que ya los llevan no llegan a
   > `dev` porque el merge será con `git merge --squash`.
   El humano aprueba o pide cambios; se itera sobre el YAML, nunca sobre el
   `.xlsx`.
2. **El fichero** (T28): abrirlo en Excel y comprobar que los desplegables
   salen, que «Instrucciones» se entiende, que las filas son las del informe y
   que el original no ha cambiado (el script imprime los dos `sha256`).
3. **Tras generarlo** (T29): importar el `v2` en el entorno
   desplegado; debe dejar las filas en la bandeja, completa y sin errores.
   *(Undécima enmienda: el criterio es **0 filas con error**; con filas ya
   importadas antes, salen `ya_en_bandeja` y no `nueva`, y vale igual —
   decisión del humano del 2026-10-03, T29 paso 4.)*

Nada de esto se entrega a Posventa ni a la propiedad desde este trabajo: la
plantilla es una **propuesta** que Posventa tiene que aceptar y difundir
(riesgo de la ficha).

### 10.5 · Un catálogo de Sigrid que ha cambiado (añadido en la undécima enmienda del 2026-10-03)

**Qué pasó.** El `v2` de T28 se generó con el JSON del catálogo leído el
2026-09-29. El 2026-10-03, en T29, Sigrid tenía otros oficios en la 0677 (18
de 39 filas de `obrofc` distintas: salen 5 oficios, entran 10, uno cambia de
proveedor). El entorno lee Sigrid en vivo y dejó 14 filas en error («el
oficio no está en la lista de la obra», «el par oficio · proveedor no está
en la lista de la obra»); la 15.ª era una fila de prueba del humano. El
importador hizo lo correcto. Al repetir la migración con el catálogo del
día, el script se paraba en `componer`: «el oficio "V-Aire acondicionado" no
es exactamente el nombre de un oficio de la obra en Sigrid» (dos filas del
original). Decisión del humano: el `v2` se rehace leyendo Sigrid justo antes
y en él solo van oficios y pares de Sigrid de ese día (R128–R131).

**Qué cambia, y dónde.** Solo `services/postventa-api/scripts/migracion_f036.py`
y una línea de `services/postventa-api/scripts/migrar_excel_f036.py`; los dos
son el script local de la migración, sin red (§10.3).

- **`nombres_de_sigrid(datos: object) -> frozenset[str]`** (nueva, en
  `migracion_f036.py`, junto a `catalogo_de_la_obra`): los nombres de
  `oficios_catalogo` del JSON (todo `auxofc`), **recortados** por los
  extremos, sin los nulos ni los vacíos. SI `oficios_catalogo` falta, no es
  una lista o alguno de sus elementos no es un mapping con `codigo` y
  `nombre` (este, texto o `null`), ENTONCES `MigracionDetenida` con
  `_FORMA_CATALOGO`, el mismo mensaje que cualquier otra clave que falte.
  `migrar` la llama justo después de `catalogo_de_la_obra`.
- **`componer(tabla, catalogo, opciones, listas, *, nombres_sigrid)`**: el
  nombre de oficio de cada fila nueva se decide en este orden —la obra
  manda—:

  | El nombre de la tabla… | Resultado |
  |---|---|
  | es exactamente el de **un** oficio de la obra | como hoy: su grupo, y el proveedor por R91 |
  | es el de **varios** oficios de la obra | para, como hoy (mismo mensaje) |
  | no es de la obra, pero sí de `nombres_sigrid` | **no para**: `Oficio` y `Proveedor` vacíos, y la fila compuesta lo apunta (R128) |
  | no es de la obra ni de `nombres_sigrid` | para, con el mensaje nuevo (R97) |

  El nombre de la tabla se compara **tal cual** con los de Sigrid
  recortados, en los dos conjuntos (como hoy: «Pintura » en la tabla no casa).
  Los problemas se siguen juntando y se dicen todos a la vez.
- **El mensaje de la errata** pasa a ser, literal:
  `fila {origen} del original, fila nueva {n}: el oficio «{nombre}» no es
  exactamente el nombre de ningún oficio de Sigrid, ni de la obra ni del
  resto del catálogo: corrígelo en la tabla de correcciones (R97)`.
- **`FilaCompuesta`** gana `oficio_fuera_de_la_obra: str | None`: el nombre de
  la tabla cuando la fila va sin oficio por R128; `None` en los demás casos
  (también cuando la tabla no trae oficio). En esas filas, `oficio_codigo`,
  `oficio_etiqueta` y `proveedor_codigo` son `None` y `codigos_en_obra`, 0.
- **`Recuentos`** gana `oficios_fuera_de_la_obra: int`, detrás de
  `oficios_en_grupo_de_varios`: cuántas filas compuestas tienen
  `oficio_fuera_de_la_obra`. **No** cuenta las filas a las que la tabla no
  pone oficio.
- **`informe`** (R130): la fila de recuento
  `| Filas nuevas sin oficio porque ese oficio ya no está en la obra en Sigrid | N |`,
  siempre, detrás de la de grupos de varios códigos; y si N > 0, justo
  después de la tabla de recuentos:

  ```
  ## Filas sin oficio porque ese oficio ya no está en la obra en Sigrid

  | Fila del original | Fila nueva | Oficio en la tabla de correcciones |
  |---:|---:|---|
  | <origen> | <n> | <nombre, con _celda> |
  ```

  En `_descripcion_de`, esa fila dice
  `Oficio: — (ya no está en la obra en Sigrid: «<nombre>»)` en lugar de
  `Oficio: —`. Ni el informe ni la sección llevan códigos de oficio de
  `auxofc` que no sean de la obra, ni nada de proveedores (R116).
- **`migrar_excel_f036.py`**: una línea más en el resumen, detrás de la de
  filas: `Filas sin oficio porque ese oficio ya no está en la obra en Sigrid: N`.
- Los docstrings de los dos módulos, al día (el paso 3 y las «Decisiones que
  no fija la spec»).

**Por qué la errata sigue parando.** Una errata es un fallo de la tabla de
correcciones, que el humano aprobó nombre a nombre en T25 (R97, §10.2):
dejarla vacía la escondería en un recuento y perdería un oficio que sí está
en la obra; un oficio que ha salido de la obra es un hecho de Sigrid, sin
nada que corregir en la tabla.

**El proveedor (R129).** El humano pidió lo mismo para un proveedor que el
original o la corrección asignen y ya no sea de la obra. Ese caso no se da:
el original no tiene columna de proveedor (doc. 05: A, D, E y F), la tabla
rechaza un campo `proveedor` (`_CLAVES_FILA`, `CAMPOS_NUEVA`) y R91 lo
calcula en cada ejecución con el catálogo recibido. Los errores de par del
`v2` viejo desaparecen al regenerarlo con el catálogo del día. Se fija con
tests como invariante; no lleva sección propia en el informe.

**El grupo «Fontanería» frente a «Fontaneria».** No es un defecto. La
etiqueta de un grupo es el nombre del miembro con más filas en `obrofc` de
la obra (R86); con el catálogo nuevo el grupo tiene en la obra un código que
antes no estaba, y la etiqueta puede cambiar. El informe ya lo enseña («en el
v2, «…»»).

**Lo que NO se toca.** La interfaz de la línea de órdenes (`--catalogo`
sigue, y nada nuevo); `scripts/migracion_f036_correcciones.yaml` (sigue con
los nombres que aprobó el humano: «V-Aire acondicionado» se queda en la
tabla, y si vuelve a la obra vuelve al `v2`); `tests/test_f036_migracion_contenido.py`;
el generador y el lector de `excel_openpyxl.py`, `lector_aislado.py`, el
dominio, el importador y sus endpoints; `infra/26_catalogos_plantilla_sigrid.ps1`
(ya escribe `oficios_catalogo` con todo `auxofc`, sin filtrar bajas, siempre
que hay `-SalidaJson`); la bandeja, su DDL y sus filas (decisión del humano:
las importadas con el catálogo viejo se quedan; F-038); `oficios.html`. No
hay que redesplegar nada: el script es local.

**Límite de microservicio.** Dentro: es el script de migración de este
servicio, local y sin red. Leer Sigrid lo sigue haciendo el `.ps1` por
`sigrid-api` (`sql/read`), como en T2.

**Alternativas descartadas.**

- *Parar también en el caso nuevo* (lo de hoy): obliga a tocar la tabla
  aprobada cada vez que Sigrid cambie la obra; el humano pidió lo contrario.
- *Quitar del YAML los oficios que han salido*: la tabla es la propuesta
  aprobada contra la muestra, no contra el catálogo de un día, y se volvería
  a romper con el cambio siguiente.
- *Distinguir errata de «ha salido de la obra» por parecido de texto*: sería
  casado aproximado, que la decisión 7 prohíbe. Se distingue por pertenencia
  exacta a `auxofc`.
- *Llevar el oficio que ha salido al grupo de un código que siga en la
  obra*: el fichero de grupos (R98) es de los oficios de la obra, descargado
  justo antes; un código que ha salido no está en él.
- *Que el script lea Sigrid él mismo*: rompería «sin red» (§10.3) y cambiaría
  su interfaz; el guion de T28 lanza el `.ps1` justo antes (R131).
- *Que el script compruebe la fecha del JSON*: el JSON no la lleva, y
  añadirla cambia el `.ps1` y la forma; el control es de procedimiento (T28).

**Cómo se prueba** (todo en `tests/test_f036_migracion.py`, sin red, sin
base y sin `.xlsx` de disco; nombres orientativos). Un catálogo de prueba
nuevo, `CATALOGO_SIGRID`: el `CATALOGO` de siempre con `oficios_catalogo`
lleno —los nombres de `oficios_obra` más dos inventados que no son de la
obra, uno de ellos con blancos al final en Sigrid—. `CATALOGO` sigue con
`oficios_catalogo: []`, y por eso los tests de siempre no cambian de
comportamiento.

- `test_f036_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio`: la tabla
  pone en una fila un oficio inventado de `oficios_catalogo` que no es de la
  obra; `migrar` termina; la fila compuesta lleva `oficio_fuera_de_la_obra`
  con ese nombre y `oficio_codigo`, `oficio_etiqueta` y `proveedor_codigo` a
  `None`; las demás filas, igual que con `CATALOGO`.
- `test_f036_r128_el_v2_vuelve_con_cero_errores_y_la_fila_sin_oficio`: el
  `v2` leído con `LectorPlantillaOpenpyxl` y validado con `validar_filas`
  contra ese catálogo: 0 errores, y en esa fila `Oficio` y `Proveedor`
  vacíos; ninguna celda de «Incidencias» contiene el nombre de ese oficio.
- `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`: el inventado
  con blancos al final en Sigrid casa con el de la tabla sin ellos; y la
  tabla con blancos o con otra capitalización (`"oficio que salió"`) para
  con el mensaje de la errata.
- `test_f036_r128_la_obra_manda`: un nombre que está a la vez en la obra y
  en `oficios_catalogo` se resuelve a su código y su grupo, con proveedor por
  R91, como siempre.
- `test_f036_r128_oficios_catalogo_mal_formado`: casos nuevos en el
  `parametrize` de `test_f036_catalogo_mal_formado` —sin la clave, `null`,
  un texto en vez de una lista, un elemento que no es mapping o sin
  `nombre`—: para con `_FORMA_CATALOGO`.
- `test_f036_r97_errata_para_con_el_mensaje_nuevo`: los nombres del
  `parametrize` de hoy, con `CATALOGO` y con `CATALOGO_SIGRID`: para, con el
  mensaje nuevo. Y `test_f036_r97_errata_y_fuera_de_la_obra_a_la_vez`: una
  errata y un oficio que ha salido en la misma tabla: para, y los problemas
  solo nombran la errata.
- `test_f036_r129_el_proveedor_es_el_del_catalogo_con_que_se_ejecuta`: la
  misma tabla con dos catálogos que solo difieren en el proveedor único de
  `Pintura`: cada `v2` lleva el par de su catálogo y vuelve con 0 errores; y
  con dos proveedores para ese oficio, `Proveedor` vacío.
- `test_f036_r129_la_tabla_no_admite_proveedor`: una fila nueva con un campo
  `proveedor` para por la forma («sobra «proveedor»»); si ya existe un test
  igual, se cita en el informe en vez de duplicarlo.
- `test_f036_r129_la_fila_sin_oficio_no_lleva_proveedor`: el oficio que ha
  salido tenía un único proveedor en el catálogo viejo; con el nuevo, su fila
  va sin proveedor (celda `Proveedor` vacía en el `v2`) y ni el código ni el
  nombre de ese proveedor salen en el informe.
- `test_f036_r130_recuento_y_seccion`: con `CATALOGO`, la fila de recuento
  con 0 y sin la sección; con el de R128, el recuento con 1, la sección con
  la fila del original, la fila nueva y el nombre, la fila de su ubicación
  con «Oficio: — (ya no está en la obra en Sigrid: «…»)», y
  `Recuentos.oficios_fuera_de_la_obra` igual a 1; y las filas a las que la
  tabla no pone oficio no cuentan.
- `test_f036_r130_la_linea_de_ordenes_lo_dice`: con el disco en memoria, la
  salida lleva «Filas sin oficio porque ese oficio ya no está en la obra en
  Sigrid: 1» (y 0 con `CATALOGO`), y ningún nombre de proveedor.
- `test_f036_r130_sin_proveedores_en_el_informe`: el informe y la salida no
  contienen ningún código ni nombre de proveedor de los dos catálogos.
- `test_f036_r131_un_v2_de_otro_catalogo_da_errores_y_el_regenerado_no`: el
  incidente en pequeño. Catálogo «viejo»: `CATALOGO` con un oficio más en la
  obra, con proveedor único, que la tabla usa; catálogo «nuevo»: ese oficio
  fuera de la obra (sigue en `oficios_catalogo`) y `Pintura` con otro
  proveedor único. El `v2` generado con el viejo, validado contra las
  opciones del nuevo, da errores **justo** en las filas de ese oficio y en
  las del par de `Pintura`; el regenerado con el nuevo, 0.

**Tests que cambian a propósito** (y ninguno más):
`test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para` (el mensaje
de la errata; puede renombrarse al de arriba) y
`test_f036_r58_recuentos_sin_grupos` (compara `Recuentos` entero y gana
`oficios_fuera_de_la_obra=0`). Si otro test compara `Recuentos` o
`FilaCompuesta` enteros, se le añade el campo nuevo y se dice en el informe.
Ningún test de documentación se rompe: ningún test lee estos ficheros de la
spec ni `progress/migracion_F-036.md`.

## 11 · Límite de microservicio y dependencias

Todo es de `postventa-api` y `postventa-front`, que es donde la decisión del
2026-09-23 pone toda la posventa («un solo backend»). F-036 **no pide nada a
`sigrid-api`**: sus lecturas caben en `sql/read` tal y como está desplegado.

Lo que sí deja escrito para otros:

- **F-040 / `sigrid-api`**: la urgencia no tiene dónde ir en §8.9 (`rcp.texurg`
  no está en el contrato). Opciones para F-040, no para aquí: pedir al dueño de
  `sigrid-api` que admita `urgencia` → `rcp.texurg` (≤ 32), o anteponerla a la
  `descripcion_larga`. La `referencia_externa` `PVI-…` puede derivarse de
  `incidencia_id` (`PVI-` + 36 caracteres ≤ 80). El proveedor de la bandeja va
  como `intervinientes: [{oficio, proveedor}]`; una fila con
  `oficio_ambiguo` o `proveedor_ambiguo` no se puede volcar hasta que se elija
  el código (F-038).
- **F-040**: `listado` es un dato de quien rellena, no un tipo de Sigrid.
- **F-039** (quinta enmienda): las **actividades** del proveedor y la
  correspondencia actividad → oficio, para proponer proveedores en los
  oficios que están en la obra sin proveedor; con ellas, la dependencia de
  `sigrid-api` para dar de alta en `obrofc` la pareja oficio–proveedor (§16).
- **F-050** (quinta enmienda): la agrupación de proveedores casi duplicados
  del maestro, sobre la costura de §15.8.
- **F-038**: estado de revisión, edición y descarte sobre esta tabla; elegir el
  código de un oficio o de un proveedor ambiguos (segunda enmienda del
  2026-09-28: decía solo «de un proveedor ambiguo»); puede afinar si una clave que coincide con
  una fila **descartada** debe seguir bloqueando (D-7).
- **F-039**: proponer industrial para las filas **sin** proveedor —entre ellas,
  todas las de los oficios que están en `obrofc` sin proveedor—; y, cuando
  F-050 exista, usar sus grupos para no proponer dos veces la misma empresa.
- **F-037**: `origen = 'web'` ya admitido; su contrato decide el resto.
- **F-048**: tablas planas, sin JSON, listas para el datamart.
- **Los dueños del maestro de proveedores y del catálogo de oficios en
  Sigrid**: las equivalencias confirmadas son, de hecho, una lista de fichas
  duplicadas. Fusionarlas en
  Sigrid no es de este servicio; el recuento de T2/T8 puede servirle.

## 12 · Riesgos y alternativas descartadas

1. **Aceptar también el formato viejo**: descartado por decisión del humano; y
   con razón: sin cabecera ni obra, cada fichero exigiría adivinar.
2. **Fiarse de los códigos de la hoja oculta**: descartado (§4.4).
3. **Todo o nada**: era la opción por defecto; el humano eligió la importación
   parcial con Excel de errores (decisión 6). Lo que se pierde: una
   importación puede quedar a medias **a sabiendas**, y por eso consta
   `parcial` y el front lo dice.
4. **Deduplicar solo por `sha256` del fichero**: no basta; Excel reescribe los
   bytes con solo abrir y guardar.
5. **Comprobar la clave con un `SELECT` antes de insertar**: descartado por la
   misma razón que F-019 prefirió la restricción: entre la consulta y la
   escritura cabe otra petición (R41).
6. **Contraseña en la protección de hoja**: no protege nada y estorba a
   Posventa si tiene que retocar una plantilla.
7. **`con.res` de la unidad con nombres de persona**: si alguna obra los tuviera,
   la plantilla de toda la obra se los enseñaría a cada propietario. En la 0677
   no pasa (medido); en general, T2 lo mira y D-2 lo decide.
8. **La plantilla de toda la obra y no de una unidad**: decidido «por obra»
   (D-15 aprobada).
9. **Lista de ubicaciones insuficiente**: mitigado con `Otra (explicar en el
   detalle)`; cambiar la lista es cambiar el YAML, y una etiqueta retirada solo
   afecta a plantillas viejas (error de fila, falla cerrado).
10. **`openpyxl` no conserva todo al reabrir**: irrelevante, el importador lee
    y no reescribe.
11. **Excel en otros idiomas o LibreOffice**: las validaciones de lista con
    rango de otra hoja funcionan en los dos; se comprueba a mano en T28.
12. **Casado aproximado de lo tecleado**: descartado por el humano (decisión
    7). El coste: Excel deja teclear «villa 1» contra «Villa 1» y el importador
    lo rechaza; el Excel de errores lo explica y trae el desplegable.
13. **Los nombres de proveedor en la plantilla**: la plantilla la rellena la
    propiedad y lleva los proveedores de la obra, algunos autónomos con su
    nombre. Es lo que Sigrid ya enseña a Posventa y lo que el humano pidió; se
    deja escrito porque el fichero sale de la empresa. Si no se quiere,
    la columna se quita de la plantilla que se entrega a la propiedad y se
    rellena en la bandeja (D-20).
14. **Tabla de equivalencias en un YAML versionado**: descartado por el humano:
    hay autónomos con nombre de persona, y el historial de git no suelta lo que
    entra. Guardar **códigos** en git tampoco sirve: el código de un autónomo
    lleva a su nombre en cuanto se mira Sigrid, y además la Function
    desplegada no lee ficheros de fuera del paquete. Un fichero **fuera** del
    repositorio no llega al entorno desplegado ni lo comparte Posventa. Por
    eso va en el schema `postventa` (§15.4).
15. *(Pasa a F-050 en la quinta enmienda.)* **Agrupar por CIF sin preguntar**: el CIF igual es la señal más fuerte, pero
    Sigrid puede tener CIF mal tecleados o vacíos, y un autónomo y su sociedad
    pueden compartir persona; se propone como `mismo_cif` y lo confirma una
    persona, como todo lo demás (R80).
16. **La pieza de catálogos agranda mucho la feature**: *(resuelto en la quinta
    enmienda: los proveedores salen a F-050 y las actividades a F-039; queda
    la de oficios)* se puede partir (D-18). La costura está diseñada: sin §15, cada código de oficio y de
    proveedor es su propio grupo y todo lo demás funciona igual —nunca hay
    ambiguos, porque un grupo de un código tiene un código—. *(Segunda
    enmienda del 2026-09-28: decía «la pieza de proveedores».)*
17. **Dos oficios distintos agrupados por error** (añadido en la segunda
    enmienda): «Carpintería de madera» y «Carpintería metálica» no se
    proponen —la distancia pasa de 2—, pero «Pintura» y «Pinturas» sí, y
    podrían ser partidas distintas en alguna obra. Por eso tampoco aquí se
    agrupa solo; y como la resolución a código sigue mirando `obrofc` de la
    obra (R93, R94), un grupo equivocado nunca inventa un oficio que la obra
    no tiene: como mucho deja la fila `oficio_ambiguo`.

## 13 · Decisiones

> **Enmienda del 2026-09-28.** Esta sección se llamaba «Decisiones abiertas».
> El humano aprobó D-1…D-5 y D-7…D-15 con su opción por defecto, **cambió D-6**
> y tomó cuatro decisiones nuevas (`requirements.md` §0 bis). Las abiertas que
> quedan son las nuevas, D-16…D-22.
>
> **Segunda enmienda del mismo día.** El humano **decidió D-21** (los oficios
> se agrupan). Se revisan D-18 y D-19 para los dos catálogos, D-16, D-17 y
> D-22 pasan a hablar de grupos, y se abre D-23.
>
> **Tercera enmienda del mismo día.** Se revisan D-16 y D-17 y se abren
> D-24…D-28 (familias del proveedor, §16).
>
> **Cuarta enmienda del mismo día.** La medición de T2 **decide** D-2, D-3,
> D-8, D-9 y D-24; se revisan D-16, D-17, D-18 (con la recomendación del líder
> de sacar los proveedores, sin decidir), D-22, D-25, D-27 y D-28, y se abre
> D-29. Cada fila dice lo que decía. Un dato que no es decisión pero pesa: los
> tres oficios de la obra que usa el Excel (`0133`, `0144`, `0166`) están en
> `obrofc` **sin proveedor** (§16.1).
>
> **Quinta enmienda del 2026-09-29 · PARADA T3.** Decididas D-18 (proveedores
> a F-050) y D-27 (no aplica); D-24, D-25, D-26, D-28 y D-29 salen con las
> actividades a F-039; se revisan D-16, D-17, D-19 y D-22. Siguen abiertas
> D-16, D-17, D-19, D-20, D-22 y D-23.
>
> **Sexta enmienda del 2026-09-30 · review 1.** El humano decide B5-1
> (`COLLATE "C"`, se mantiene) y que el merge a `dev` sea con
> `git merge --squash`. Las abiertas siguen siendo las mismas.
>
> **Séptima enmienda del 2026-10-01.** El humano decide R3-1: se hace el
> presupuesto de elementos XML. Las abiertas siguen siendo las mismas.
>
> **Octava enmienda del 2026-10-01.** El humano decide R4-1 (opción (A) con los
> límites doblados). Se abren D-30 (lectura concurrente) y D-31 (memoria de la
> instancia).

| Id | Decisión | Estado |
|---|---|---|
| D-1 | Dónde vive la pantalla | **Aprobada 2026-09-28**: página propia en `dev` con enlace desde `index.html`; se integra en la «Entrada» de F-035 cuando se mergee |
| D-2 | Etiqueta de la unidad en el desplegable | **Decidida por la medición (T2, 2026-09-28)**: `con.res` de la unidad, «Viviendas Bloque Villa N»; las 15 unidades de la 0677 sin nombres de persona. Decía: «Aprobada: `con.res`, si T2 confirma que no lleva nombres de persona» |
| D-3 | Origen de la lista cerrada de ubicaciones | **Decidida por la medición (T2, 2026-09-28)**: las **44 `rcp.resubi`** de la 0677, normalizadas y sin variantes (§3.4); `upv.espacios` está vacío. Decía: «YAML versionado propio, ajustado con lo medido en T2» (sigue siendo un YAML versionado; lo que cambia es de dónde sale) |
| D-4 | Valores de `Urgencia` | **Aprobada 2026-09-28**: `Urgente` y `Peligro para la seguridad`; vacío = normal |
| D-5 | Columna `Listado` | **Aprobada 2026-09-28**: incluida, opcional, sin traducir a tipo; vacía en la migración |
| D-6 | Errores de fila | **Cambiada por el humano 2026-09-28**: entran las buenas y las malas vuelven en un Excel de errores (decía: todo o nada) |
| D-7 | Contra qué filas de la bandeja se comprueba el duplicado | **Aprobada 2026-09-28**: cualquier fila de la obra; F-038 lo afina |
| D-8 | Oficios dados de baja | **Decidida por la medición (T2, 2026-09-28)**: fuera del desplegable, y en la 0677 **no hay ninguno** (0 de 31) |
| D-9 | Unidad del Excel actual | **Decidida por la medición (T2, 2026-09-28)**: «Villa 1» = `0677.03VILLA 1.` |
| D-10 | Correcciones de contenido | **Aprobada 2026-09-28**: las redacta el implementer (T24) y las valida el humano (T25) |
| D-11 | Topes | **Aprobada 2026-09-28**: 2 MiB, 1000 filas, detalle de 2000 |
| D-12 | Quién importa | **Aprobada 2026-09-28**: `usuario_oid` obligatorio |
| D-13 | `origen = 'web'` en el `CHECK` | **Aprobada 2026-09-28**: sí |
| D-14 | La urgencia en Sigrid | **Aprobada 2026-09-28**: se guarda en la bandeja; lo decide F-040 |
| D-15 | Filtro de la plantilla por unidades | **Aprobada 2026-09-28**: no en F-036 |
| D-16 | Desplegable de `Proveedor` | **Abierta.** Por defecto: una lista de pares `grupo de oficio · proveedor` sacados **solo** de `obrofc`, sin fórmulas (§3.2.1); en la 0677, del orden de 36 pares (39 filas, 3 sin proveedor). Alternativa: dependiente con `OFFSET`/`MATCH`, probado a mano en Excel, Excel web y LibreOffice. *(Quinta enmienda: decía «con los pares que dan las actividades» y «grupo de proveedor»)* |
| D-17 | `Proveedor` con `Oficio` vacío | **Abierta.** Por defecto: se toma el grupo de oficio del par. Alternativa: error «elige primero el oficio». *(Quinta enmienda: sale el caso «oficio que cubre solo por actividad»)* |
| D-18 | Partir la pieza de catálogos casi duplicados | **Decidida por el humano 2026-09-29 (PARADA T3)**: la agrupación de **proveedores sale a F-050**; la de **oficios se queda**. Números: 0 grupos parecidos entre los 526 proveedores de `obrofc`; 793/530 solo en el maestro. Costura en §15.8 |
| D-19 | Grupo de oficio con varios códigos en la obra | **Abierta.** Por defecto: la fila entra `oficio_ambiguo`, sin código, y se elige en la bandeja (F-038); elegir proveedor puede deshacer la ambigüedad (R94). Alternativa: error de fila y vuelve en el Excel de errores. *(Quinta enmienda: decía también «proveedor para el oficio»; sin agrupación de proveedores, no hay proveedor ambiguo)* |
| D-20 | Nombres de proveedor en la plantilla que sale a la propiedad | **Abierta**. Por defecto: sí, como pidió el humano (riesgo 13). Alternativa: sin columna `Proveedor` en la plantilla externa |
| D-21 | Oficios casi duplicados en `auxofc` | **Decidida por el humano 2026-09-28**: se agrupan, con el mismo mecanismo que los proveedores (§15). Decía: «solo se miden (T2); no se agrupan en F-036» |
| D-22 | Umbrales de la propuesta | **Abierta.** Por defecto: errata con distancia ≤ 2 y ≤ 10 % en nombres de ≥ 8 caracteres; fuera las palabras vacías; motivo `incluido`, para proponer `0085`/`0166` y `0033`/`0133` (§15.2). Se ajustan con T8. *(Quinta enmienda: salen las formas jurídicas, a F-050)* |
| D-24 | De dónde salen las «familias» del proveedor | **Ya no aplica a F-036 (quinta enmienda, 2026-09-29)**: sale con las actividades a F-039. Lo medido —`conact` → `auxpronat`— queda como punto de partida de F-039 |
| D-25 | Proveedor de la obra sin actividades mapeadas | **Sale a F-039 (quinta enmienda, 2026-09-29).** En F-036 todo proveedor se ofrece con los oficios con que figura en `obrofc`, que es la única fuente |
| D-26 | Proveedor que cubre un oficio por actividad pero no figura con él en `obrofc` | **Sale a F-039 (quinta enmienda, 2026-09-29).** En F-036 ese caso no existe: los oficios sin proveedor en `obrofc` (`0133`, `0144`, `0166` en la 0677) no ofrecen ninguno y la fila entra sin proveedor |
| D-27 | Actividades no homologadas (`conact.homolo`) | **No aplica (quinta enmienda, 2026-09-29)**: `homolo` vale 0 en las 825 filas de `conact` de los proveedores de `obrofc`; y las actividades salen a F-039 |
| D-28 | Correspondencia actividad → oficio | **Sale a F-039 (quinta enmienda, 2026-09-29).** Lo medido: 0 códigos en común con `auxofc`, 21 actividades que se llaman como un oficio |
| D-29 | Nivel de la correspondencia actividad → oficio | **Sale a F-039 (quinta enmienda, 2026-09-29).** Lo medido: el árbol se reconstruye (padre por prefijo, 3 niveles), así que «hoja y rama» es viable |
| D-23 | Cuándo se genera el `v2` definitivo | **Abierta** (segunda enmienda). Por defecto: después de desplegar y de confirmar los grupos de la 0677 (T27), con `--grupos`; hasta entonces solo el informe. Alternativa: generarlo ya sin grupos (oficios repetidos en el desplegable) y regenerarlo después |
| B5-1 | `COLLATE "C"` en el `CHECK (codigo_a < codigo_b)` de `postventa.decisiones_equivalencia` (desviación del Bloque 5, review 1) | **Decidida por el humano 2026-09-30**: se mantiene `COLLATE "C"` (§6.1) |
| R2-1 | Cómo se cierra lo que `openpyxl` expande al cargar (review 2) | **Decidida en la sexta enmienda bis (2026-09-30)**, por recomendación del líder: `read_only=True` (§5.2), no un examen previo del XML; el combinado pequeño dentro de la plantilla se admite |
| R3-1 | Cómo se acota el coste por elemento XML (review 3) | **Decidida por el humano 2026-10-01** (opción «a»: hacer el arreglo, no aceptar el riesgo): presupuesto global de elementos XML antes de `load_workbook` (R117, §5.2). La fusión de las dos pasadas por «Incidencias» **no entra** (§5.2) |
| R4-1 | Cómo se cierra la familia de huecos de coste del lector (review 4) | **Decidida por el humano 2026-10-01**: opción (A) del líder **con los límites doblados**: lectura en un proceso hijo con **30 s y 1 GB** (R118–R120), tope descomprimido al **doble** del fichero legítimo más grande (R16); se mantienen solo lectura, R115 y R117; sin parche específico para `sqref` |
| D-30 | Qué pasa si llega una lectura mientras otra está en curso en el mismo proceso (octava enmienda) | **Abierta.** Por defecto: espera hasta **5 s** a que quede libre; si no, 503 «otra importación en curso; reintenta», sin escribir nada (R120). Alternativa: esperar más (con el riesgo de pasar de los 40 s del front) o encolar |
| D-31 | Fijar la memoria de la instancia en el despliegue (octava enmienda) | **Abierta.** Por defecto: no tocar `infra/desplegar_backend.ps1` (la instancia ya es de 2.048 MB, el valor por defecto de Flex Consumption); comprobarlo en T29 y escribir en `docs/INTEGRACION.md` que bajarla rompe la importación. Alternativa: pasar `--instance-memory 2048` explícito al crear y en un `az functionapp scale config set` para la existente |
| T37-1 | Qué partes cuenta el presupuesto | **Decidida por el humano 2026-10-01** (opción «a»): **todas** las partes del ZIP, sea cual sea su extensión; lo que no es XML cuenta hasta su fallo y no rechaza el fichero; el presupuesto pasa de 200.000 a **300.000** (§5.2, «Todas las partes») |
| Merge | Cómo entra F-036 en `dev` | **Decidida por el humano 2026-09-30**: `git merge --squash`, sin reescribir la rama, para que los códigos de proveedor del informe de migración y el GUID de relleno (B3-12) de los commits intermedios no lleguen a `dev` |

## 14 · Tests

Todos sin red, sin base de datos y sin IA; los libros se construyen **en
memoria** con `openpyxl` (ni un `.xlsx` versionado, R59). Nombres trazables
`test_f036_rN_...`. Los nombres de proveedor de los tests son **inventados**
(«Carpinterías Ejemplo S.L.», «Juan Ejemplo Ejemplo»), nunca de Sigrid.

| Fichero (`services/postventa-api/tests/`) | Qué cubre |
|---|---|
| `test_f036_plantilla_dominio.py` | R8, R9, R71, R72, R92, `normalizar_para_clave`, enumeraciones |
| `test_f036_importacion_dominio.py` | R17–R20 (`reconocer_plantilla`), R23–R34 con comparación **exacta** («villa 1», «Villa 1 », «Villa  1» son error), R35–R37, R73–R77, R93, R94 (el proveedor que deshace la ambigüedad del oficio, y el que no), R99, `agrupar_por_clave`; los «Miras de hierro» de la muestra en cinco ubicaciones no son duplicados (R36) |
| `test_f036_equivalencias_dominio.py` | R78–R86, R95 **con el catálogo `oficio`** *(quinta enmienda: eran dos catálogos)*: normalización (tildes, puntuación, palabras vacías, plural), cada motivo (`mismo_nombre`, `plural`, `errata`, `incluido`), los tres pares medidos en la 0677, cliques frente a cadenas, «distinto» que anula una componente, pares ya decididos, que el discriminador `catalogo` separa decisiones con los mismos códigos, etiqueta del grupo, resolución a uno o varios códigos |
| `test_f036_configuracion_plantilla.py` | El YAML real carga; ubicaciones ≤ 48 y sin repetidas; códigos de urgencia y listado = `Enum`; ningún nombre propio |
| `test_f036_excel_generador.py` | R2–R7, R12: hojas y estados, cabecera, paneles, validaciones con sus rangos, estilo «detener» y topes, metadatos, ninguna fórmula, texto con `=` como texto; y el Excel de errores: R62–R65 (celdas marcadas, comentarios, columna `Errores`, `importacion_origen`) |
| `test_f036_excel_lector.py` | R15–R20 a nivel de bytes: no ZIP, ZIP roto, macros, bomba (tamaño declarado), formato antiguo construido con filas de la muestra, sin metadatos, versión 2, cabecera movida, fórmulas, fechas; **ida y vuelta** generador → lector, también del Excel de errores con `Errores` ignorada (R66) |
| `test_f036_consultas_catalogo.py` | El SQL carácter a carácter; parámetros `?`; ningún valor interpolado; ninguna referencia a `prv`, `cif`, `conact` ni `auxpronat` *(quinta enmienda: la marca de CIF sale a F-050 y las actividades a F-039)* |
| `test_f036_adaptador_catalogo.py` | Puerta de entorno, solo `/api/sql/read`, reintentos de lo transitorio, techo marcado, errores sin cuerpo, clave en la cabecera |
| `test_f036_catalogo_aplicacion.py` | R10: cero, una, dos obras; techo en cada lectura; oficios vacíos (R12); grupos vigentes aplicados |
| `test_f036_ddl.py` | Los tres `.sql` pasan el guard; orden; `CHECK` = `Enum`; índice parcial presente; `hash_fichero` **no** único; sin binarios; `decisiones_equivalencia` con `catalogo` y sin columnas de nombre; los `CHECK` de `oficio_ambiguo` |
| `test_f036_repositorio_bandeja.py` | Las sentencias y la secuencia de §5.3 con un doble de conexión: completa y parcial, cero válidas, grupo entero `ya_en_bandeja`, duplicadas con `duplicada_de`, recuentos, `ROLLBACK` ante fallo; decisiones de equivalencia por catálogo y pares, y última decisión |
| `test_f036_pipeline_importacion.py` | Orden de los pasos: atajo solo con importación completa (R39); reconocimiento sin Sigrid ni base (R21); catálogo después; parcial con Excel de errores después del registro; mismo fichero parcial reprocesado (R67, R68) |
| `test_f036_plantilla_http.py`, `test_f036_importar_http.py`, `test_f036_bandeja_http.py`, `test_f036_catalogos_http.py` | Códigos y cuerpos de §8, cabeceras de descarga, `excel_errores` presente solo con errores (R69), `confirmado` booleano, logs sin texto de fila, `oid`, nombre de fichero ni proveedor (R47) |
| `test_f036_alcance_cerrado.py` | R46 (ningún fichero de F-036 nombra rutas de escritura), R48, R49, R59 (`git ls-files` sin `.xlsx`), ficheros de §2.3 intactos respecto de `dev` |
| `test_f036_arquitectura.py` | `domain/` no importa `openpyxl`, `httpx` ni `psycopg`; `openpyxl` solo en `infrastructure/documentos/` y `scripts/` |
| `test_f036_migracion.py` | R53–R56, R91 y R97 (nombre de oficio exacto, llevado a su grupo; sin `--grupos` solo `--solo-informe`) con original, catálogo y grupos falsos en memoria |
| `test_f036_migracion_contenido.py` | R57 sobre el YAML real: cubre las filas de `docs/referencia/05_excel_creacion_incidencias.md` una a una, con su texto; límites y patrones prohibidos; ningún nombre de proveedor |
| `test_f036_scripts_infra.py` | `infra/26_…`: solo `sql/read`, sin `ide` ni `cif` impresos, nombres solo con `-MostrarNombres`, sin hosts ni GUID, ASCII + CRLF, cabecera de ruta; *(cuarta enmienda)* texto en UTF-8 sin doble codificación en consola y JSON (R111) y las lecturas de `conact`/`auxpronat` |
| `test_f036_documentacion.py` | R60, R61: las secciones existen y nombran rutas, tablas y lecturas |
| `tests_bbdd/tests/test_f036_bbdd_bandeja.py` | **MANUAL (humano)**, contra la base efímera: DDL dos veces, índice parcial, reimportación, dos importaciones simultáneas, decisiones de equivalencia append-only con los dos catálogos |
| Front: `tests/test_f036_front.py`, `tests_js/importacion.test.js`, `tests_js/catalogos.test.js` | R50–R52, R89, R98 |
| ~~`test_f036_cobertura_dominio.py`~~ | **Retirado en la quinta enmienda**: las actividades pasan a F-039 |
| `test_f036_excel_lector.py`, casos `test_f036_r115_…` (sexta enmienda y bis) | R115: celda con estilo en la fila 1.048.576 leída en < 1 s y con memoria acotada; valor en la fila 1002 y en la 5.000 → `demasiadas_filas`; celda con estilo sin valor por debajo → no cuenta; lo mismo en la cabecera (`XFD1`) y en `_plantilla`; *(bis)* rangos combinados `A1003:A1048576` y `A1003:H1048576` e hipervínculo sobre `A1003:H1048576` en < 1 s, también en `_plantilla`, en `Instrucciones` y en un Excel de errores; combinado pequeño `C2:D2` admitido; libro abierto en solo lectura y cerrado |
| `test_f036_lector_aislado.py`, casos `test_f036_r118_…`, `r119_…`, `r120_…` (octava enmienda) | Doble del ejecutor: cada estado del hijo, el JSON validado, el orden (pasos baratos antes del hijo), el semáforo, la plataforma sin `setrlimit` en `dev`/`pro` (503) y fuera (aviso). Ejecutor real: tiempo agotado (todas las plataformas), memoria agotada (solo Linux), los ficheros de R4-1 y de todas las reviews rechazados a tiempo y sin crecer la memoria del padre, lo legítimo admitido igual que en proceso, topes de producción 30 s y 1 GiB fijados; el padre no lee con `openpyxl` |
| `test_f036_excel_lector.py`, casos `test_f036_r117_…` de T37 bis (séptima enmienda bis) | El fichero de T37-1 (`sheet1.dat`) y un `.bin` con XML dentro → `fichero_sospechoso` en < 1 s y sin abrir; una imagen real cuenta 0 y no se lee más allá de su primer trozo; parte que falla a mitad cuenta hasta el fallo; `printerSettings` binario admitido; DTD en un `.bin` → `no_es_xlsx`; el Excel de errores más grande admitido; la plantilla, por debajo de un quinto; presupuesto = 300.000; coste medido de un fichero de 300.000 elementos en «Incidencias» |
| `test_f036_excel_lector.py`, casos `test_f036_r117_…` (séptima enmienda) | R117: los siete ficheros de la review 3 rechazados con `fichero_sospechoso` en < 1 s, con memoria acotada y sin llamar a `load_workbook`; plantilla completa admitida por debajo de un quinto del presupuesto; recuento cortado; frontera exacta; total global; prefijos y `.rels`; DTD, entidad o XML roto → `no_es_xlsx` sin abrir |
| `test_f036_migracion.py`, caso `test_f036_r116_…` (sexta enmienda) | R116: el informe generado no contiene **ningún** código de proveedor de `obrofc` del catálogo que se le pasa, y dice cuántas filas llevan proveedor y por qué regla |
| `test_f036_excel_generador.py`, casos `test_f036_r121_…` a `r126_…`; `test_f036_excel_lector.py` y `test_f036_lector_aislado.py`, casos `test_f036_r126_…` y `r127_…` (décima enmienda) | R121–R125: estilos de cada zona leídos del libro generado, con sus valores literales (colores, fuentes, bordes, alineación, anchos, altos, cuadrícula, pestaña, regla condicional, impresión y pie; *10 bis*: las tres reglas condicionales del cuerpo —dos en el Excel de errores— con su fórmula, rango, prioridad y `dxf`, el cuerpo sin bordes ni relleno estáticos, y la **ausencia** de todo ajuste de impresión en las cuatro hojas y en `workbook.xml`). R126: ida y vuelta por los dos lectores, mismo `LibroLeido` con y sin formato, *10 bis*: también la plantilla con el formato de la décima, sin `<f>`, mismas hojas y nombres definidos. R127: elementos del Excel de errores más grande ≤ la mitad del presupuesto, *10 bis*: tres reglas condicionales de un rango cada una (dos en el Excel de errores), sin imágenes, y los topes de T41 sin cambiar (§3.6; §5.2, «Los topes y el formato visual») |

> **Enmienda del 2026-09-28.** Se añaden los tests de proveedores, del Excel de
> errores y de la importación parcial; desaparece el 422. **Segunda enmienda
> del mismo día**: `test_f036_proveedores_dominio.py` →
> `test_f036_equivalencias_dominio.py`, `test_f036_proveedores_http.py` →
> `test_f036_catalogos_http.py`, `proveedores.test.js` → `catalogos.test.js`,
> y se añaden los casos de oficios.

## 15 · Oficios casi duplicados de Sigrid (añadido el 2026-09-28; reducido a un catálogo el 2026-09-29)

> **Quinta enmienda del 2026-09-29 · PARADA T3.** Esta sección se titulaba
> «Catálogos casi duplicados de Sigrid: oficios y proveedores» y diseñaba un
> mecanismo para tres catálogos: `oficio`, `proveedor` (con la marca de CIF, las
> formas jurídicas, el motivo `mismo_cif` y un apartado Proveedores en la
> pantalla) y, desde la tercera y la cuarta enmienda, `actividad_oficio` (modo
> correspondencia, motivos `mismo_codigo` y `manual`, herencia por rama). El
> humano decidió en T3:
>
> - **la agrupación de proveedores sale a F-050** (D-18): 0 grupos parecidos
>   entre los 526 proveedores de `obrofc`, y la plantilla solo ofrece
>   proveedores de la obra. F-050 reutiliza este diseño; lo que era solo de
>   proveedores está resumido en §15.8 para que no se pierda;
> - **las actividades salen a F-039** (opción A, §16).
>
> Queda **un** catálogo, `oficio`, con la **costura** del discriminador
> `catalogo` en `postventa.decisiones_equivalencia` para que F-050 y F-039 lo
> reutilicen sin migrar nada (§15.4, §15.8). La pantalla se renombra
> `catalogos.html` → **`oficios.html`**; las rutas siguen siendo
> `/api/catalogos/*`, porque son el punto de entrada genérico que reutilizarán
> las otras fichas.

### 15.1 · El problema y lo que no se hace

El catálogo de oficios de Sigrid (`auxofc`) tiene entradas casi iguales, y en
la propia 0677 se midieron tres pares: `0046`/`0143` «Carpinteria de madera» /
«Carpintería de madera» (tilde), `0085`/`0166` «Mobiliario de cocinas» /
«Mobiliario cocina» y `0033`/`0133` «Solados y Alicatados M.O.» / «Solados y
Alicatados». Un desplegable con una entrada por código enseña el mismo oficio
dos veces, y quien rellena elige uno al azar.

Se agrupa **para enseñar**, no para corregir: Sigrid no se toca (solo se lee), y
lo que viaja al volcado sigue siendo **un código de oficio concreto** (§15.5).

### 15.2 · La propuesta automática (dominio puro, `domain/models/equivalencias.py`)

```python
class Catalogo(StrEnum):
    OFICIO = "oficio"
    # F-050 añadirá PROVEEDOR y F-039 ACTIVIDAD_OFICIO: sus valores ya están en
    # el CHECK de la tabla (§15.4) y sus perfiles en §15.8.

class Motivo(StrEnum):
    MISMO_NOMBRE = "mismo_nombre"; PLURAL = "plural"; ERRATA = "errata"; INCLUIDO = "incluido"

@dataclass(frozen=True)
class Perfil:                               # lo único que distingue a un catálogo
    catalogo: Catalogo
    palabras_ignoradas: frozenset[str]      # vacío en oficios; F-050 pondrá las formas jurídicas

PALABRAS_VACIAS: frozenset[str] = frozenset({"de", "del", "la", "las", "el", "los", "y", "e"})

PERFILES: Mapping[Catalogo, Perfil] = {Catalogo.OFICIO: Perfil(Catalogo.OFICIO, frozenset())}

@dataclass(frozen=True)
class Candidato: codigo: str; nombre: str | None

@dataclass(frozen=True)
class Grupo: catalogo: Catalogo; codigos: frozenset[str]; etiqueta: str

def clave_de_nombre(nombre: str, perfil: Perfil) -> str: ...     # a)
def clave_singular(clave: str) -> str: ...                       # b)
def distancia_edicion(a: str, b: str) -> int: ...                # Levenshtein, sin dependencias
def motivos_del_par(a: Candidato, b: Candidato, perfil: Perfil) -> frozenset[Motivo]: ...
def proponer_grupos(candidatos: Iterable[Candidato], decisiones: Iterable[DecisionPar],
                    perfil: Perfil) -> tuple[Propuesta, ...]: ...
def grupos_vigentes(candidatos: Iterable[Candidato], decisiones: Iterable[DecisionPar],
                    perfil: Perfil, uso_en_obra: Mapping[str, int]) -> GruposVigentes: ...
```

Las funciones reciben el `Perfil` aunque hoy haya uno solo: es la costura que
F-050 usará para meter el suyo sin tocarlas.

a) **`clave_de_nombre`**: NFKD sin diacríticos; minúsculas; `&` → `y`; se
   quitan los puntos **dentro** de siglas (`M.O.` → `mo`) y luego toda la
   puntuación; espacios colapsados; fuera las `PALABRAS_VACIAS` y las de
   `perfil.palabras_ignoradas`. Con esto «Mobiliario de cocinas» y
   «Mobiliario cocina» dan la misma clave singular.
b) **`clave_singular`**: cada palabra de más de 4 letras pierde una `s` final
   (y `es` si la palabra acaba en consonante + `es`). Es burdo a propósito: solo
   **propone**, y lo que propone lo mira una persona.
c) **Motivos** de un par: `MISMO_NOMBRE` si las claves son iguales; `PLURAL` si
   solo las claves singulares lo son; `ERRATA` si la distancia de edición entre
   claves es ≤ 2 y ≤ 10 % de la más larga, y la más corta tiene ≥ 8 caracteres;
   `INCLUIDO` si una clave es el principio de la otra con al menos dos palabras
   (D-22). `INCLUIDO` propone `0033`/`0133`; ojo: «M.O.» es probablemente «mano
   de obra» y puede ser **otro oficio**, por eso se propone y lo decide el
   humano.
d) **Grupos propuestos**: grafo con una arista por par con algún motivo, **sin**
   los pares ya decididos (R85). Cada componente conexa que sea un **clique**
   (todos sus pares tienen motivo) se propone como un grupo; si no lo es, se
   proponen sus aristas una a una (R79).

Solo se proponen códigos **de la obra** (los de su `obrofc`, sin oficios de
baja): es lo que la plantilla enseña. Una decisión, en cambio, vale para todas
las obras (R84).

### 15.3 · La confirmación humana

Nada se agrupa solo (R80). La pantalla de §15.6 enseña cada propuesta con
nombres, códigos y motivos; la persona pulsa «Son el mismo» o «Son distintos».
Un grupo propuesto de tres se confirma entero (se guardan sus tres pares) o se
rechaza por pares. «Separar» un grupo vigente guarda «distinto» para el par que
se elija.

### 15.4 · Dónde se guarda y por qué

En **`postventa.decisiones_equivalencia`** (§6.1), append-only, por pares, con
el discriminador `catalogo` y sin nombres (R81, R83, R95).

- **No en un YAML versionado**: los oficios no llevan datos personales, pero
  confirmar un oficio costaría un commit y un despliegue en vez de un clic, y
  F-050 —con autónomos que se llaman como una persona— **no** podría usar un
  YAML: el mecanismo dejaría de ser reutilizable.
- **No en un fichero fuera del repositorio**: la Function desplegada no lo ve.
- **Sí en el schema `postventa`**, detrás de Entra, con el `oid` de quien
  decide, sin nombres y sin salir a los logs.
- **La costura**: la tabla lleva `catalogo` y su `CHECK` admite **ya**
  `oficio`, `proveedor` y `actividad_oficio`, aunque F-036 solo escriba
  `oficio`. El guard del DDL no deja ampliar un `CHECK` después; así F-050 y
  F-039 añaden su perfil y su pantalla sin tocar el esquema (R108).

`EquivalenciasPort` (implementado en `repositorio_bandeja_pg.py`):

```python
@dataclass(frozen=True)
class DecisionPar:
    catalogo: Catalogo; codigo_a: str; codigo_b: str; decision: Literal["mismo", "distinto"]
    motivos: frozenset[Motivo]; obra_codigo: str; decidido_por: str; decidido_at_utc: datetime

class EquivalenciasPort(Protocol):
    def ultimas_decisiones(self, *, catalogo: Catalogo, codigos: Collection[str]) -> tuple[DecisionPar, ...]: ...
    def registrar(self, *, decisiones: tuple[DecisionPar, ...]) -> None: ...   # una transacción
```

**Grupos vigentes**: unión de los pares cuya **última** decisión es «mismo»;
una componente que contenga un par cuya última decisión es «distinto» **no se
aplica** y se devuelve como aviso (R82). Cada código sin grupo es su propio
grupo. La etiqueta del grupo es la del miembro con más filas en `obrofc` de la
obra; a igualdad, el de código menor (R86).

### 15.5 · De grupo a código de Sigrid

§8.9 exige que el `oficio` del parte esté en `obrofc` de la obra y resuelve
cada interviniente `{oficio, proveedor}` contra `obrofc`. Con la función pura
`resolver_oficio_y_proveedor` de §4.3:

- **Solo oficio** (R93): los códigos del grupo que están en `obrofc` de la obra.
  Uno → ese código; más de uno → `oficio_ambiguo`.
- **Oficio y proveedor** (R94): las filas de `obrofc` con un oficio del grupo y
  **ese** proveedor. Si todas comparten código de oficio, oficio resuelto; si
  no, `oficio_ambiguo`. El proveedor es un código concreto de Sigrid (sin
  agrupación de proveedores, cada código es su propia opción), así que **queda
  siempre resuelto**: `proveedor_ambiguo` no puede darse en F-036 (la columna se
  queda para F-050, §15.8). El resultado es siempre una fila real de `obrofc`.

Ejemplo: el grupo «Carpintería de madera» son `0046` y `0143`; en la obra, el
proveedor `P1` está con `0046` y el `P2` con `0143` y con `0046`.

| Fila trae | Oficio | Proveedor |
|---|---|---|
| `Carpintería de madera` | ambiguo (`0046`, `0143`) | — |
| `Carpintería de madera · P1` | `0046` | `P1` |
| `Carpintería de madera · P2` | ambiguo (`0046`, `0143`) | `P2` |

En los ambiguos decide una persona en la bandeja (F-038) antes del volcado
(D-19).

`application/pipelines/equivalencias.py` hace las dos operaciones del borde:
**propuestas** (oficios de la obra → `ultimas_decisiones` → `grupos_vigentes` +
`proponer_grupos`) y **registrar decisiones** (comprueba que el catálogo es
`oficio` —400 si no, «catálogo no disponible en esta versión»— y que todos los
códigos son oficios de la obra —409 si no—, expande cada «mismo» a sus pares y
registra en una transacción).

### 15.6 · La pantalla (`oficios.html`)

Se llamaba `proveedores.html` y luego `catalogos.html`; con un solo catálogo se
renombra **`oficios.html`** («Oficios repetidos en Sigrid»), con
`js/oficios.js`.

Campo «Código de obra» → `GET /api/catalogos/propuestas`. Tres listas:
**propuestas pendientes** (nombres, códigos, motivos legibles —«mismo nombre
salvo mayúsculas, tildes o puntuación», «plural», «posible errata», «uno
contiene al otro»— y los botones «Son el mismo» / «Son distintos»), **grupos
vigentes** (con «Separar») y **avisos** de grupos no aplicados por
contradicción (R82). Cada pulsación manda `POST /api/catalogos/decisiones` con
`confirmado: true` y `catalogo: "oficio"`, y recarga. Un botón **«Descargar los
grupos vigentes»** baja el JSON de R98 (solo códigos) que usa la migración.
Enlace desde `index.html` y desde `importar.html`.

### 15.7 · La medición

Hecha en T1/T2 (`progress/explore_F-036.md`): 31 oficios en la obra, 1 grupo
por nombre sin mayúsculas ni tildes, y los tres pares de §15.1; 7 grupos de 2 en
todo `auxofc`. T8 aplica `proponer_grupos` al JSON de T2 y cuenta propuestas
por motivo y por tamaño, componentes que no son clique y grupos con más de un
código en la obra (los futuros `oficio_ambiguo`). **Solo recuentos.**

### 15.8 · La costura para F-050 (proveedores) y F-039 (actividades)

**D-18, decidida por el humano el 2026-09-29: la agrupación de proveedores sale
a F-050.** Los números: 0 grupos por CIF y 0 por nombre en la 0677 y entre los
**526** proveedores de `obrofc`; 793 grupos por CIF (1.980 códigos) y 530 por
nombre (1.229) solo en el maestro completo (9.585), que la plantilla no ofrece.

Lo que F-036 deja hecho para que F-050 y F-039 no toquen el esquema ni el
mecanismo:

| Pieza | En F-036 | Lo que añade F-050 (proveedores) | Lo que añade F-039 (actividades) |
|---|---|---|---|
| `CHECK` de `catalogo` | `oficio`, `proveedor`, `actividad_oficio` | nada | nada |
| `Catalogo`, `Perfil`, `PERFILES` | solo `OFICIO` | `PROVEEDOR` con `palabras_ignoradas = FORMAS_JURIDICAS` (`sl`, `slu`, `sll`, `slne`, `sa`, `sau`, `sal`, `scoop`, `scl`, `sc`, `cb`, `sociedad`, `limitada`, `anonima`, `unipersonal`, `cooperativa`) y un campo `usa_marca_cif` | `ACTIVIDAD_OFICIO`, con un modo «correspondencia» (pares cruzados actividad–oficio con prefijos `A:`/`O:`, sin grupos) y los motivos `mismo_codigo` y `manual` |
| `Motivo` | `mismo_nombre`, `plural`, `errata`, `incluido` | `mismo_cif` | `mismo_codigo`, `manual` |
| Lectura de Sigrid | `SQL_OFICIOS_DE_LA_OBRA` sin CIF | la marca opaca de CIF (`DENSE_RANK` sobre el CIF normalizado, sin que el valor salga de la lectura) y, si hace falta, el maestro | `conact` → `auxpronat` (padre por prefijo del código, 3 niveles, 514 actividades) |
| Grupos vigentes de proveedor | cada código, su propio grupo | leídos de la tabla | — |
| Bandeja | `proveedor_ambiguo` (siempre falso aquí) | lo usa cuando un grupo tenga varios códigos en la obra | una marca para el proveedor propuesto fuera de `obrofc`, que exige cambiar `sigrid-api` (su ficha lo dice) |
| Pantalla | `oficios.html` | un apartado o página de proveedores | un apartado «Actividades → oficios» con creación a mano |
| Ruta | `/api/catalogos/*` con `catalogo: "oficio"` | acepta `"proveedor"` | acepta `"actividad_oficio"` |

Lo que en F-036 **no** hay que hacer por esa costura: ni una columna ni una
lectura de más. `proveedor_ambiguo` ya estaba en la tabla y se queda porque
sale gratis; un `ADD COLUMN IF NOT EXISTS` de F-050 también habría valido.

## 16 · El oficio del proveedor, por sus actividades — RETIRADA de F-036 el 2026-09-29

> **Quinta enmienda del 2026-09-29 · PARADA T3, opción A.** Esta sección
> (añadida en la tercera enmienda como «por sus familias» y reescrita en la
> cuarta como «por sus actividades») diseñaba que los oficios que cubre un
> proveedor salieran de sus actividades en Sigrid (`conact` → `auxpronat`),
> con una correspondencia actividad → oficio confirmada por el humano (catálogo
> `actividad_oficio`, por hoja y por rama), el apartado «Actividades →
> oficios» de la pantalla, una lectura del árbol, el módulo `cobertura.py` y el
> caso B (`proveedor_fuera_de_obrofc`: un proveedor que cubre el oficio por
> actividad pero no está en `obrofc` con él).
>
> **El humano decidió sacarlo de F-036 y llevarlo a F-039**, donde ya está
> anotado en su ficha de `harness/features.json`: en F-036, la relación oficio ↔
> proveedor sale **solo** de `obrofc` de la obra, que es lo único que acepta
> `sigrid-api` §8.9 sin cambios. Lo que se midió en T1/T2 se queda como hecho y
> es el punto de partida de F-039: 33 de 36 proveedores de la 0677 con
> actividades (81 filas, 58 distintas), 360 de 526 en `obrofc`; `homolo` = 0 en
> las 825 filas; árbol de 514 actividades en 3 niveles con padre por prefijo del
> código; 0 códigos en común con `auxofc` y 21 actividades que se llaman como
> un oficio. El script de medición no se toca.
>
> Consecuencia en la 0677: los oficios que están en `obrofc` **sin proveedor**
> (`0133`, `0144` y `0166`, justo los del Excel de Posventa) no ofrecen ningún
> proveedor en la plantilla; la fila entra sin proveedor y F-039 lo propondrá.
>
> Salen con ella las decisiones D-24, D-25, D-26, D-28 y D-29 (§13). El texto
> retirado está en el historial de git (`a6c2f46` y anteriores).
