<!-- specs/F-036-importar-excel/tasks.md -->
# F-036 · Importar el Excel de incidencias de la propiedad a una bandeja — Tareas

> Rama `feature/F-036-importar-excel`. Rigor **`critico`**: fase RED en los
> requisitos centrales, cobertura ≥ 80 % de las líneas cambiadas y cero
> supervivientes de mutación sin justificación aceptada por el humano. Cada
> tarea = un commit `F-036 Tn: ...`. **Encargos por bloques**: un bloque por
> encargo al implementer, y parar.
>
> Ningún test toca red, base de datos ni IA, y ninguno usa un `.xlsx` de disco:
> los libros se construyen en memoria. **Nadie escribe en Sigrid desde esta
> rama**: F-036 solo lee (`sql/read`). Nada de lo que hay aquí escribe en el
> SharePoint de Posventa. El DDL nuevo va al schema `postventa` y se aplica solo
> al arrancar la Function desplegada. **Ningún nombre de proveedor** entra en
> el repositorio: ni en `progress/`, ni en el YAML de la migración, ni en tests.
>
> Los `pytest` se lanzan desde `services/postventa-api` con
> `.venv/Scripts/python.exe -m pytest …` (y los del front desde
> `services/postventa-front`).
>
> **Decisiones** (`design.md` §13): siguen **abiertas** D-16, D-17, D-19, D-20,
> D-22 y D-23; las demás están aprobadas, decididas o han salido a F-039 o
> F-050. Las que condicionan una tarea se dicen en ella; el resto se implementa
> con la opción por defecto y se cambia si el humano dice otra cosa.
>
> **Orden de lo que queda** (sexta enmienda, 2026-09-30; bis, el mismo día):
> **Bloque 10** (arreglos de la review 1, T31–T34, hechos) → review 2 →
> **T35–T36** (arreglo de la review 2, hechos) → review 3 → **T37–T38**
> (arreglo de la review 3; séptima enmienda, 2026-10-01) → **T37 bis–T38 bis**
> (hallazgo T37-1; séptima enmienda bis) → review 4 → **T39–T44** (cambio de
> estrategia por R4-1; octava enmienda) → review 5 → **Bloque 11, T45–T49**
> (arreglos de la review 5; novena enmienda) → review 6 → T16
> (MANUAL) → T27, T28 y T29 (MANUAL) → T30. Los Bloques 10 y 11 están escritos antes del Bloque 9 porque se
> hacen antes que sus MANUAL; T16 sigue en su sitio, en el Bloque 5.
> *(Décima enmienda, 2026-10-02)*: con T16 y T27 hechas y T28 ejecutada una
> vez, entra el **Bloque 12, T50–T54** (formato visual) → review 7 →
> **redesplegar el backend** (T27, solo esa parte) → **repetir T28** → T29 →
> T30.
> *(Enmienda 10 bis, 2026-10-02)*: tras la review 7 entra el **Bloque 13,
> T55–T60** (sin impresión; el cuerpo por formato condicional; muestra para el
> humano con su PARADA) → review 8 → **redesplegar el backend** → **repetir
> T28** → T29 → T30.
> *(Undécima enmienda, 2026-10-03)*: con T28 repetida y T29 empezada, entra
> el **Bloque 14, T61–T64** (la migración ante un catálogo de Sigrid que ha
> cambiado) → review 10 → **T28 otra vez**, con el catálogo leído en el
> momento → **T29, pasos 4–7** otra vez → T30. Sin redespliegue: solo cambia
> el script local de la migración.
>
> **Merge a `dev`**: con **`git merge --squash`**, sin reescribir la rama
> (decisión del humano del 2026-09-30), para que los códigos de proveedor del
> informe de migración y el GUID de relleno de B3-12 de los commits
> intermedios no lleguen a `dev`. Push y merge los hace el humano.

> **Enmienda del 2026-09-28 · revisión del humano.** Las tareas se renumeran
> (eran T1–T25, ahora T1–T29) porque ninguna estaba empezada. Cambian T1/T2
> (miden además proveedores y oficios), T5 (comparación exacta, proveedor,
> filas con error), el generador (Excel de errores), la bandeja (importación
> parcial) y el front (descarga del Excel de errores). Nuevos: el Bloque 2
> (proveedores casi duplicados, dominio y medición), T19 (endpoints de
> proveedores) y la página de proveedores en T21/T22. Equivalencias de la
> numeración anterior: T6→T6, T7→T10, T8→T11, T9→T12, T10→T13, T11→T14,
> T12→T15, T13→T16, T14→T17, T15→T18, T16→T20, T17→T21, T18→T22, T19→T23,
> T20→T24, T21→T25, T22→T26, T23→T27, T24→T28, T25→T29.

> **Segunda enmienda del 2026-09-28 · los oficios también se agrupan.** El
> Bloque 2 pasa a ser de **catálogos** (oficios y proveedores con un solo
> mecanismo): cambian T5, T7, T8, T9, T15, T19, T21, T22, T24 y el nombre de
> los ficheros (`equivalencias.py`, `14_decisiones_equivalencia.sql`,
> `medir_catalogos_f036.py`, `catalogos.html`, `/api/catalogos/*`). El final se
> reordena porque el `v2` definitivo necesita los grupos confirmados en el
> entorno desplegado (D-23): T26→T28 (ejecutar la migración), T27→T26
> (documentación), T28→T29 (verificación desplegada, sin la confirmación de
> grupos, que pasa a la nueva **T27**) y T29→T30 (`init.sh`). T1–T25 conservan
> su número.

> **Tercera enmienda del 2026-09-28 · el oficio del proveedor sale de sus
> familias** (`design.md` §16). **No se renumera nada.** Cambian T1, T2, T3
> (miden y enseñan las familias: `confam`, `auxfam` ↔ `auxofc`, `entfam`,
> `prv.ofcide`), T7 (`cobertura.py` y el catálogo `familia_oficio`), T8 y T9
> (cruce por nombre y número de pares), T12/T13 (tercera lectura), T14
> (`proveedor_fuera_de_obrofc` y el `CHECK` de `catalogo`), T19, T22 y T29.

> **Cuarta enmienda del 2026-09-28 · actividades (`conact`/`auxpronat`).** La
> medición de T2 desmintió la tercera (`progress/explore_F-036.md`): las
> familias están vacías y lo que el humano llama así son las actividades del
> proveedor, en árbol (`design.md` §16). **Se reabre T1** (actividades y
> UTF-8, R111) y T2 se repite con el script corregido. Cambian T3, T6
> (ubicaciones de las 44 `rcp.resubi`), T7 (actividades, herencia por rama,
> `actividad_oficio`), T8, T9 (D-18 con los números, D-28, D-29), T12, T13,
> T14, T19 y T22 (apartado «Actividades → oficios» con creación a mano). No
> se renumera nada. Si la agrupación de proveedores sale de F-036 (D-18),
> cada tarea pierde su parte de proveedores según `design.md` §15.8.

> **Quinta enmienda del 2026-09-29 · PARADA T3: se simplifica.** El humano
> decidió la **opción A** —la relación oficio ↔ proveedor sale solo de
> `obrofc`; las actividades pasan a F-039— y **sacar la agrupación de
> proveedores a F-050** (D-18). **No se renumera nada.** T1, T2 y T3 quedan
> hechas. Salen de F-036, y se quitan de las tareas: `cobertura.py` y su test
> (T7), la medición de proveedores y actividades en T8, el perfil
> `actividad_oficio` y el de proveedores (T7), las lecturas de actividades y
> árbol y la marca de CIF (T12, T13), `proveedor_fuera_de_obrofc` (T14), los
> catálogos `proveedor` y `actividad_oficio` en las rutas (T19), los
> apartados Proveedores y «Actividades → oficios» (T22), la confirmación de
> proveedores (T27) y el paso 7 bis (T29). La pantalla pasa a `oficios.html`.
> Lo que ya se midió en T1/T2 queda como hecho y el script no se toca.

> **Sexta enmienda del 2026-09-30 · review 1** (`progress/review_F-036.md`,
> CHANGES_REQUESTED). **No se renumera nada.** Se añade el **Bloque 10**
> (T31–T34) con los arreglos: el tope de recorrido del lector (R115), el
> informe de migración sin códigos de proveedor (R116), la lista de ficheros de
> `test_f036_alcance_cerrado.py` y la trazabilidad por nombre de R13, R44 y R83.
> T28 y T29 ganan las comprobaciones que pide la review. B5-1 (`COLLATE "C"`)
> queda decidida sin tocar código, y el merge será con `git merge --squash`.

> **Novena enmienda del 2026-10-01 · review 5** (`progress/review_F-036.md`,
> «Review 5», APPROVED con residuales; el humano decidió «R5-1 se arregla» y
> aceptó R5-2 y R5-4). **No se renumera nada.** Enmienda **menor** de R119: el
> hijo de la lectura aislada se pone además un tope de **CPU** (`RLIMIT_CPU`,
> sus segundos más 5; solo en Linux), para que un hijo huérfano no siga
> gastando CPU; el tope de 30 s de reloj del padre no cambia (`design.md` §5.2,
> «El tope de CPU del hijo»). Se corrige en `design.md` la errata R4-2. Se
> añade el **Bloque 11** (T45–T49): R5-1, R5-3 (el test sensible a la carga),
> las erratas R5-5/R4-3 y R5-6, y la campaña de mutación de lo cambiado. T30
> sigue siendo la última.

> **Décima enmienda del 2026-10-02 · formato visual** (petición del humano al
> abrir el `v2` de T28: «horrible»; lo quiere «limpio, ordenado, con colores
> Ruesma»; muestra aprobada el mismo día). **No se renumera nada.** Requisitos
> nuevos R121–R127 (`requirements.md` §18) y `design.md` §3.6 («Formato
> visual») y §5.2 («Los topes y el formato visual»). Se añade el **Bloque 12**
> (T50–T54): fase RED y medición del «antes», el formato en el generador, la
> medición de topes con su PARADA, la documentación y la campaña de mutación.
> Solo cambia el generador de `excel_openpyxl.py`; ningún tope se toca. Dos
> avisos en las MANUAL: T27 lleva `-SoloFront` (errata) y, tras el Bloque 12,
> hay que **redesplegar el backend y repetir T28** antes de T29. T30 sigue
> siendo la última.

> **Enmienda 10 bis del 2026-10-02 · sin impresión y una sola fila a la
> vista** (review 7, R7-1 y R7-2; el humano: «no se imprimirá, o se importa o
> exporta a excel (de momento solo importar). la plantilla vacía no hace
> falta que tenga más de 1 línea»). **No se renumera nada.** R125 pasa a
> «sin ajustes de impresión»; R122 y R123, el cuerpo por **tres reglas de
> formato condicional** (fila 2 siempre y cada fila con algo escrito); R126
> suma la plantilla con el formato de la décima; R127, tres reglas y nueva
> medición (`design.md` §3.6 y §5.2, notas «10 bis»). Se añade el **Bloque 13**
> (T55–T60): RED y «antes», el generador, la medición con su PARADA, una
> **muestra** para el humano con su PARADA, la búsqueda en la documentación y
> la mutación. R7-1 desaparece (ya no hay impresión que fijar; el test pasa
> a fijar la ausencia) y R7-2 queda resuelto. En las MANUAL, T28 y T29 pierden
> toda comprobación de impresión y T28 gana la de «una fila a la vista». T30
> sigue siendo la última. La impresión a PDF de los partes de trabajo es
> F-044 y no aplica aquí.

> **Undécima enmienda del 2026-10-03 · la migración ante un catálogo de
> Sigrid que ha cambiado** (verificación MANUAL T29: el `v2`, generado con el
> catálogo del 2026-09-29, dio 14 filas con error en el entorno porque Sigrid
> cambió los oficios de la 0677; el humano: «para rehacer v2, que al crear el
> excel, antes lea sigrid y en el v2 estén solo los oficios de sigrid»).
> **No se renumera nada.** Cambia R97 y entran R128–R131 (`requirements.md`
> §19; `design.md` §10.5): un oficio de la tabla que es de Sigrid pero ya no
> de la obra deja el oficio y el proveedor vacíos y se cuenta en el informe,
> en vez de parar; la errata sigue parando. Se añade el **Bloque 14**
> (T61–T64): RED, el cambio en `scripts/migracion_f036.py` (y una línea de
> `migrar_excel_f036.py`), el informe y la mutación. En las MANUAL, **T28 se
> repite** con el catálogo y los grupos leídos en el momento y un informe que
> el humano acepta expresamente, y **T29 repite los pasos 4–7**, con el paso
> 4 dado por bueno con **0 errores** aunque las filas ya importadas salgan
> `ya_en_bandeja`. La bandeja no se toca. T30 sigue siendo la última.

## Bloque 0 · Medir antes de escribir (solo lectura) — HECHO

- [x] **T1**: crear `infra/26_catalogos_plantilla_sigrid.ps1` sobre
  `infra/08_lectura_sigrid_comun.ps1`, **solo `sql/read`**, con `-CodigoObra`,
  `-SalidaJson`, `-MostrarNombres` y `-SinGlobal`, que mide sin nombres ni
  `ide` ni `cif`: unidades de la obra, oficios y proveedores de `obrofc`,
  proveedores y oficios parecidos (en la obra y globales), ubicaciones
  (`rcp.resubi`, `upv.espacios`), familias (`confam`/`auxfam`/`entfam`,
  `prv.ofcide`) y actividades (`conact`/`auxpronat`, forma del árbol), con el
  texto en **UTF-8 sin doble codificación** (R111); y
  `tests/test_f036_scripts_infra.py`. |
  Verificación: `pytest tests/test_f036_scripts_infra.py`

  > **Cuarta enmienda del 2026-09-28 · T1 reabierta.** Estaba hecha
  > (`63c0879`); la medición demostró que las familias estaban vacías, que las
  > buenas eran `conact`/`auxpronat` y que el script doblaba la codificación.
  >
  > **Quinta enmienda del 2026-09-29 · hecha.** T1 bis en `1b3edfb` (UTF-8 y
  > actividades), informe en `progress/impl_F-036.md` (`bfc0949`). La parte de
  > proveedores y de actividades de la medición queda como hecho para F-050 y
  > F-039; el script **no se toca**. El texto largo de la tarea está en el
  > historial (`a6c2f46`).
- [x] **T2 · MANUAL (humano)**: ejecutar
  `infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson "<fuera del repo>"`
  y anotar en `progress/explore_F-036.md`, sin identificadores ni nombres. |
  Verificación: MANUAL (humano)

  > **Quinta enmienda del 2026-09-29 · hecha.** Primera ejecución el 2026-09-28
  > (familias vacías, tildes mal); **repetida el 2026-09-29** con T1 bis
  > (`8cc1c86`): **PASA**, con las tildes bien. El JSON queda en
  > `%TEMP%\catalogo_0677.json`, fuera del repositorio, para T8, T24 y T28.
- [x] **T3 · PARADA**: el líder lleva T2 al humano. |
  Verificación: decisión anotada en `progress/current.md`

  > **Quinta enmienda del 2026-09-29 · hecha** (`a6c2f46`). El humano decidió la
  > **opción A** (actividades a F-039) y **D-18** (proveedores a F-050). Con la
  > medición quedan decididas D-2, D-3, D-8, D-9 y D-27; D-24, D-25, D-26, D-28
  > y D-29 salen a F-039. `design.md` §13.

## Bloque 1 · Dominio puro y configuración

- [x] **T4**: `domain/models/plantilla_incidencias.py` (`design.md` §4.1,
  **sin** `opciones_de_oficio` ni `opciones_de_proveedor`, que van en T7) y los
  errores nuevos de §4.6 en `domain/models/errores.py`. Tests
  `tests/test_f036_plantilla_dominio.py` (R8, R9; colisiones de nombre, nombre
  vacío, orden por código, determinismo; códigos con espacios, de 25
  caracteres, con `/`). |
  Verificación: `pytest tests/test_f036_plantilla_dominio.py`
- [x] **T5**: `domain/models/importacion.py` (§4.2–§4.5): `reconocer_plantilla`,
  `validar_filas` (comparación **exacta**, filas con error agrupadas con su
  `FilaLeida`), `resolver_oficio_y_proveedor` (R93, R94: solo `obrofc`; el
  proveedor del par es un código y siempre resuelve), `clave_de_duplicado`,
  `agrupar_por_clave`, los `Enum` de estado e `IncidenciaEnBandeja`. La parte de
  oficio y proveedor se escribe contra `OpcionOficio` y `OpcionProveedor`
  construidas a mano en los tests. Tests
  `tests/test_f036_importacion_dominio.py`: R17–R20, R23–R37 una a una
  —incluidos «villa 1», «Villa 1 » y «Villa  1» como error, los cinco «Miras de
  hierro» (R36), fila sin unidad debajo de una con unidad (R25), 129
  caracteres (R27), fórmula, fecha y número en columna tasada (R32), errores de
  varias filas y columnas a la vez (R33)—, R73–R77, la tabla de ejemplo de
  `design.md` §15.5 (R93, R94), R99 y los avisos (R34). |
  Verificación: `pytest tests/test_f036_importacion_dominio.py`
- [x] **T6**: `config/plantilla_incidencias.yaml` (lista de ubicaciones de
  §3.4: **las 44 `rcp.resubi` de la 0677 normalizadas**, con lo que falte para
  la migración marcado para revisión; urgencias, listados, textos de
  instrucciones y mensajes por columna en lenguaje llano para alguien sin
  formación, incluidos el uso obligado del desplegable, el proveedor —que solo
  ofrece los de la obra, y ninguno en los oficios que no tienen— y el Excel de
  errores) e `infrastructure/documentos/plantilla_yaml.py`. Tests
  `tests/test_f036_configuracion_plantilla.py`. |
  Verificación: `pytest tests/test_f036_configuracion_plantilla.py`

## Bloque 2 · Oficios casi duplicados: dominio y medición

> Condicionado a **D-22** (umbrales). *(Quinta enmienda: era «Catálogos casi
> duplicados (oficios y proveedores)» y dependía de D-18, ya decidida.)*

- [x] **T7**: `domain/models/equivalencias.py` (§15.2 con `Perfil`, `PERFILES`
  —solo `oficio`—, `PALABRAS_VACIAS` y los motivos `mismo_nombre`, `plural`,
  `errata` e `incluido`; §15.4 `grupos_vigentes`), la función de grupos de
  proveedor «cada código, su propio grupo» (costura, §15.8), y
  `opciones_de_oficio` y `opciones_de_proveedor` en `plantilla_incidencias.py`
  (R71, R72, R86, R92). Tests `tests/test_f036_equivalencias_dominio.py` con el
  catálogo `oficio` (R78–R86, R95; los tres pares medidos en la 0677) y los de
  R71, R72 y R92 en `tests/test_f036_plantilla_dominio.py`. |
  Verificación: `pytest tests/test_f036_equivalencias_dominio.py tests/test_f036_plantilla_dominio.py`

  > **Quinta enmienda del 2026-09-29.** Salen el perfil de proveedores (con
  > `mismo_cif` y formas jurídicas, a F-050), el perfil `actividad_oficio`,
  > `cobertura.py` y `tests/test_f036_cobertura_dominio.py` (a F-039).
- [x] **T8**: `scripts/medir_catalogos_f036.py` (lee el JSON de T2, aplica
  `proponer_grupos` a los oficios de la obra y a todo `auxofc`, y
  `opciones_de_oficio`/`opciones_de_proveedor`, e imprime **solo recuentos**:
  propuestas por motivo y por tamaño, componentes que no son clique, grupos de
  oficio propuestos con más de un código en la obra —los futuros
  `oficio_ambiguo`—, número de pares de la columna `Proveedor`, y oficios con un
  solo proveedor —los que R91 rellenaría—) y un test del script con un JSON
  inventado en memoria. Ejecutarlo sobre el JSON de T2 y anotar los recuentos en
  `progress/explore_F-036.md`, **sin nombres ni códigos**. |
  Verificación: `pytest tests/test_f036_equivalencias_dominio.py` y
  `.venv/Scripts/python.exe scripts/medir_catalogos_f036.py --catalogo "<JSON de T2>"`

  > **Quinta enmienda del 2026-09-29.** Ya no mide proveedores (F-050) ni el
  > cruce actividad ↔ oficio (F-039).
- [x] **T9 · PARADA**: el líder enseña al humano los recuentos de T8 y el humano
  decide D-19 (oficio ambiguo), D-22 (umbrales) y, si procede, D-16 y D-17.
  Commit solo del informe. |
  Verificación: decisión anotada en `progress/current.md`

  > **Quinta enmienda del 2026-09-29.** Ya no decide D-18 (decidida), D-25,
  > D-26, D-28 ni D-29 (a F-039).

## Bloque 3 · El Excel

- [x] **T10**: `openpyxl` y `defusedxml` en `requirements.txt` (e instalarlos en
  el `.venv`); `domain/ports/hoja_calculo.py`; el **generador** de
  `infrastructure/documentos/excel_openpyxl.py` (§3, §5.2): la plantilla con
  sus nueve columnas, el desplegable de grupos de oficio y la lista de pares de
  `Proveedor` sacados solo de `obrofc` (D-16), y el **Excel de errores** (§3.5).
  Tests `tests/test_f036_excel_generador.py` (R2–R7, R12, R62–R65, R92, sobre el
  libro generado reabierto en memoria) y `tests/test_f036_arquitectura.py`. |
  Verificación: `pytest tests/test_f036_excel_generador.py tests/test_f036_arquitectura.py`
- [x] **T11**: el **lector** de `excel_openpyxl.py`, con las comprobaciones de
  bytes y ZIP antes de `openpyxl` (§5.2). Tests
  `tests/test_f036_excel_lector.py` (R15–R20 a nivel de bytes, formato antiguo
  construido con las primeras filas de la muestra, ida y vuelta generador →
  lector → `reconocer_plantilla` → `validar_filas`, también del Excel de
  errores con la columna `Errores` rellena e ignorada, R66). |
  Verificación: `pytest tests/test_f036_excel_lector.py`

## Bloque 4 · Sigrid, solo lectura

- [x] **T12**: `domain/ports/catalogo_obra.py` e
  `infrastructure/sigrid/consultas_catalogo.py` (§6.3: **dos** lecturas,
  `SQL_UNIDADES_DE_LA_OBRA` y `SQL_OFICIOS_DE_LA_OBRA` sin marca de CIF). Tests
  `tests/test_f036_consultas_catalogo.py` (SQL carácter a carácter, `?`,
  ninguna referencia a `prv`, `cif`, `conact` ni `auxpronat`, mapeo de filas,
  fila sin proveedor, fila mal formada). |
  Verificación: `pytest tests/test_f036_consultas_catalogo.py`

  > **Quinta enmienda del 2026-09-29.** Salen la marca de CIF (a F-050) y las
  > lecturas de actividades y del árbol (a F-039).
- [x] **T13**: `infrastructure/sigrid/catalogo_obra.py`,
  `construir_catalogo_obra` en `infrastructure/sigrid/fabrica.py` y
  `application/pipelines/catalogo_obra.py` (§5.1, §7.1). Tests
  `tests/test_f036_adaptador_catalogo.py` y
  `tests/test_f036_catalogo_aplicacion.py` (R10, R11, R12, R48). |
  Verificación: `pytest tests/test_f036_adaptador_catalogo.py tests/test_f036_catalogo_aplicacion.py`

  > **Quinta enmienda del 2026-09-29.** Salen `leer_actividades` y
  > `leer_arbol_actividades` (a F-039).

## Bloque 5 · La bandeja y las decisiones en PostgreSQL

- [x] **T14**: `infrastructure/persistencia/sql/12_importaciones.sql`,
  `13_bandeja_incidencias.sql` (con `oficio_ambiguo` y `proveedor_ambiguo`, este
  siempre falso en F-036) y `14_decisiones_equivalencia.sql` (con el `CHECK` de
  `catalogo` en `oficio`, `proveedor` y `actividad_oficio`: la costura para
  F-050 y F-039, R108) (§6.1, con su cabecera), ampliando los tests que fijan la
  lista y el orden del DDL. Tests `tests/test_f036_ddl.py`. |
  Verificación: `pytest tests/test_f036_ddl.py tests/test_f005_ddl_orden.py tests/test_f005_ddl_seguro.py`

  > **Quinta enmienda del 2026-09-29.** Sale `proveedor_fuera_de_obrofc` (a
  > F-039).
- [x] **T15**: `domain/ports/bandeja.py`, `domain/ports/equivalencias.py`,
  `infrastructure/persistencia/sentencias_bandeja.py`,
  `infrastructure/persistencia/repositorio_bandeja_pg.py` y `construir_bandeja`
  en `infrastructure/persistencia/fabrica.py` (§5.3, §6.2, §15.4). Tests
  `tests/test_f036_repositorio_bandeja.py` con doble de conexión (completa,
  parcial, cero válidas, decisiones por catálogo y pares). Escribir también
  `tests_bbdd/tests/test_f036_bbdd_bandeja.py` (no lo ejecuta la suite
  normal). |
  Verificación: `pytest tests/test_f036_repositorio_bandeja.py`
- [x] **T16 · MANUAL (humano)**: con Docker Desktop arrancado,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`.
  Debe pasar `test_f036_bbdd_bandeja.py`: DDL aplicado dos veces, nada en
  `public`, el índice parcial rechaza la segunda fila no duplicada con la misma
  clave, reimportar no añade filas, dos importaciones simultáneas del mismo
  contenido dejan una sola copia, el `CHECK` de estado casa con
  `filas_con_error`, los `CHECK` de oficio y proveedor ambiguos, y las
  decisiones de equivalencia se acumulan sin mezclar catálogos. Anotar el
  resultado en `progress/impl_F-036.md`. |
  Verificación: MANUAL (humano)

## Bloque 6 · Aplicación y endpoints

- [x] **T17**: `application/pipelines/plantilla.py`,
  `contexto_importacion.py` y `paso_importacion.py` (§7.2, §7.3, seis pasos).
  Tests `tests/test_f036_pipeline_importacion.py` con dobles de los puertos:
  orden de los pasos, atajo solo con importación completa (R39), R21,
  importación parcial con Excel de errores **después** del registro, cero
  válidas (R70), R40, R67–R69, grupos de oficio aplicados. |
  Verificación: `pytest tests/test_f036_pipeline_importacion.py`
- [x] **T18**: `interface_adapters/api/plantilla.py`, `importar.py` y
  `bandeja.py`, y sus tres rutas en `function_app.py` con su docstring (§8),
  ampliando los tests que enumeran rutas. Tests
  `tests/test_f036_plantilla_http.py`, `tests/test_f036_importar_http.py` y
  `tests/test_f036_bandeja_http.py` (R1, R9–R11, R14–R22, R33, R39, R43, R45,
  R47 con `caplog`, R65, R69). |
  Verificación: `pytest tests/test_f036_plantilla_http.py tests/test_f036_importar_http.py tests/test_f036_bandeja_http.py tests/test_f010_endpoints_protegidos.py`
- [x] **T19**: `application/pipelines/equivalencias.py`,
  `interface_adapters/api/equivalencias.py` y sus dos rutas
  (`/api/catalogos/propuestas`, `/api/catalogos/decisiones`; §15.5, §8). Tests
  `tests/test_f036_catalogos_http.py` (R87, R88 con `catalogo: "oficio"`;
  cualquier otro catálogo → 400 «no disponible en esta versión»; `confirmado`
  booleano; códigos que no son oficios de la obra → 409 sin guardar; expansión
  a pares; logs sin nombres ni códigos). |
  Verificación: `pytest tests/test_f036_catalogos_http.py tests/test_f010_endpoints_protegidos.py`

  > **Quinta enmienda del 2026-09-29.** Salen los catálogos `proveedor` (a
  > F-050) y `actividad_oficio` (a F-039).
- [x] **T20**: `tests/test_f036_alcance_cerrado.py` (R46, R48, R49, R59 y los
  ficheros de `design.md` §2.3 idénticos a `dev`). |
  Verificación: `pytest tests/test_f036_alcance_cerrado.py`

## Bloque 7 · El front

- [x] **T21**: en `services/postventa-front/js/api.js`, `descargarPlantilla`,
  `importarExcel` (sin reintento automático, R52), `bandeja`,
  `propuestasCatalogos` y `decidirCatalogos`; `js/importacion.js` (con la
  descarga del Excel de errores desde base64) y `js/oficios.js` (con la
  descarga de los grupos vigentes, R98), con su lógica pura y sus componentes
  Alpine. Tests `tests_js/importacion.test.js`, `tests_js/oficios.test.js` y los
  de `api.js` que correspondan. |
  Verificación: desde `services/postventa-front`, `node --test "tests_js/*.test.js"`
- [x] **T22**: `services/postventa-front/importar.html` (§9) y `oficios.html`
  (§15.6), los dos enlaces en la cabecera de `index.html` y las páginas en
  `services/postventa-front/README.md`. Tests `tests/test_f036_front.py`
  (cabecera de ruta, scripts al final del `body`, sin datos reales, ningún
  botón de editar, descartar ni aprobar incidencias, botón de descarga del
  Excel de errores y de los grupos vigentes, enlaces presentes, `confirmado:
  true` solo tras pulsar, oficios ambiguos marcados en la bandeja). |
  Verificación: desde `services/postventa-front`, `python -m pytest tests/test_f036_front.py tests/test_f007_estaticos.py`

  > **Quinta enmienda del 2026-09-29.** `catalogos.html` y `js/catalogos.js`
  > pasan a `oficios.html` y `js/oficios.js`; salen los apartados Proveedores
  > (F-050) y «Actividades → oficios» (F-039) y la marca
  > `proveedor_fuera_de_obrofc`.

## Bloque 8 · La migración del Excel actual (propuesta)

> Necesita el JSON de T2. El `v2` definitivo se genera en T28, con los grupos
> confirmados (D-23).

- [x] **T23**: `scripts/migracion_f036.py` (lógica pura: cotejo con el
  original, resolución de los nombres de oficio a su código y a su grupo con
  `--grupos` (R97), composición de filas con R91 —los oficios `0133`, `0144` y
  `0166` no tienen proveedor en la obra y quedan sin él—, ida y vuelta por el
  importador, informe en Markdown sin nombres de proveedor) y
  `scripts/migrar_excel_f036.py` (CLI de `design.md` §10.3, con `--grupos`,
  `--sobrescribir` y `--solo-informe`; sin `--grupos` solo admite
  `--solo-informe`). Tests `tests/test_f036_migracion.py` con un original, un
  catálogo y un fichero de grupos **falsos** construidos en memoria (R53–R56,
  R58, R91, R97). |
  Verificación: `pytest tests/test_f036_migracion.py`
- [x] **T24**: redactar `scripts/migracion_f036_correcciones.yaml` —la
  **propuesta** de contenido, fila a fila, con los criterios de `design.md`
  §10.2: oficios como **nombres exactos de Sigrid**, sin nombres de proveedor—
  y generar `progress/migracion_F-036.md` con
  `.venv/Scripts/python.exe scripts/migrar_excel_f036.py --original "<ruta del original>" --catalogo "<JSON de T2>" --correcciones scripts/migracion_f036_correcciones.yaml --salida "<ruta del v2>" --informe ../../progress/migracion_F-036.md --solo-informe`.
  Tests `tests/test_f036_migracion_contenido.py` sobre el YAML real (R57; cubre
  una a una las filas de `docs/referencia/05_excel_creacion_incidencias.md`; cada
  oficio es un nombre de la lista de oficios de la 0677 anotada en T2). |
  Verificación: `pytest tests/test_f036_migracion_contenido.py` y el informe generado
- [x] **T25 · PARADA**: el humano revisa `progress/migracion_F-036.md` y
  aprueba la propuesta o pide cambios. Los cambios se hacen **en el YAML** y se
  regenera el informe; se itera hasta su visto bueno. |
  Verificación: aprobación del humano anotada en `progress/current.md`

## Bloque 10 · Arreglos de la review 1 (añadido en la sexta enmienda del 2026-09-30)

> De `progress/review_F-036.md` (CHANGES_REQUESTED): cambios 1, 3, 5 y 6. Van
> antes de las MANUAL pendientes (T16, T27–T29) y de T30. Cada uno con su fase
> RED, y una sola campaña de mutación al acabar el bloque, con
> `--base 444e0c4` sobre lo que cambie (no hace falta relanzar la rama
> entera). Las mutaciones de orden del punto 7 de la review se repiten sobre
> este código en la review 2. Se encarga el bloque entero; T31 es la que
> bloquea el despliegue.

- [x] **T31**: tope de recorrido del lector del Excel (R115, `design.md` §5.2,
  cambio 1 de la review). En
  `infrastructure/documentos/excel_openpyxl.py`, `_filas` (hoy
  `ws.iter_rows(min_row=PRIMERA_FILA, max_col=…)` sin `max_row`, ~línea 549)
  recorre de `PRIMERA_FILA` a `ULTIMA_FILA + 1`; los datos por debajo se
  detectan mirando **solo las celdas que existen** (el diccionario interno de
  celdas de la hoja, fijado por un test, o `read_only=True`; §5.2), y se
  rechazan con el `demasiadas_filas` que ya existe, a través de un campo nuevo
  de `LibroLeido` que `reconocer_plantilla` convierte en ese error. Lo mismo
  para la cabecera (hasta `len(CABECERA) + 1` columnas) y los metadatos de
  `_plantilla`. El Excel de errores pasa por el mismo lector. Tests en
  `tests/test_f036_excel_lector.py` (y en `tests/test_f036_importacion_dominio.py`
  el del campo nuevo), con nombres `test_f036_r115_…`: celda vacía con estilo en
  la fila 1.048.576 leída en < 1 s y con el pico de `tracemalloc` bajo un tope
  fijo, y con las mismas filas que sin ella; valor en la fila 1002 y en la 5.000
  → `demasiadas_filas`; celda con estilo sin valor por debajo → no cuenta;
  celda con estilo en `XFD1` y en `_plantilla` lejana → barato. Fase RED: los
  dos primeros en rojo sobre el lector de antes. |
  Verificación: `pytest tests/test_f036_excel_lector.py tests/test_f036_importacion_dominio.py`
- [x] **T32**: el informe de migración sin códigos de proveedor (R116,
  `design.md` §10.4, cambio 3 de la review). En `scripts/migracion_f036.py`,
  el texto del proveedor completado (en torno a `PROVEEDOR_COMPLETADO`, ~línea
  143, y su uso en el informe, ~línea 913) deja de escribir el código; los
  recuentos del informe dicen cuántas filas llevan proveedor y por qué regla
  (R91). Test `test_f036_r116_…` en `tests/test_f036_migracion.py`: el informe
  generado con un catálogo inventado **no contiene ninguno** de los códigos de
  proveedor de su `obrofc`; y el de R58 exige lo mismo. Después, **regenerar
  `progress/migracion_F-036.md`** con el comando de T24 (`--solo-informe`, el
  Excel real y el JSON de T2) y comprobar con `git diff` que solo desaparecen
  los códigos y que siguen 158 filas, 14 separadas, 0 descartadas, 0 errores. |
  Verificación: `pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py`
  y `git diff progress/migracion_F-036.md` sin ningún código de proveedor
- [x] **T33**: la lista `NUEVOS_DE_F036` de `tests/test_f036_alcance_cerrado.py`
  (~líneas 194–228; cambio 5 de la review): añadir los ficheros de los bloques
  7 y 8 que su comentario prometía —`scripts/migracion_f036.py`,
  `scripts/migrar_excel_f036.py`, y los del front
  (`services/postventa-front/importar.html`, `oficios.html`,
  `js/importacion.js`, `js/oficios.js`) si los controles de R46 y de imports
  les aplican; si a alguno no le aplican, decirlo en el comentario en vez de
  prometerlo. |
  Verificación: `pytest tests/test_f036_alcance_cerrado.py`
- [x] **T34**: trazabilidad por nombre de R13, R44 y R83 (cambio 6 de la
  review): que cada uno tenga un test `test_f036_rN_…`, renombrando o con un
  alias, sin perder lo que comprueban:
  `tests/test_f036_consultas_catalogo.py::test_f036_t12_sql_oficios_de_la_obra_caracter_a_caracter`
  (R13), `tests/test_f036_ddl.py::test_f036_t14_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas`
  (R44) y `tests/test_f036_ddl.py::test_f036_t14_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas`
  (R83). |
  Verificación: `pytest tests/test_f036_consultas_catalogo.py tests/test_f036_ddl.py`

> **Sexta enmienda bis del 2026-09-30 · review 2** (CHANGES_REQUESTED, R2-1).
> T31 cerró el caso de la review 1 con `ws._cells` (B10-1), pero un rango
> combinado o un hipervínculo sobre un rango lejanos hacen que `openpyxl` cree
> las celdas **dentro de `load_workbook`**, antes de que el lector recorra nada
> (169 s y 2,6 GB, 228 s y 4,1 GB con 33 KB). La spec decide abrir el libro en
> **solo lectura** (`design.md` §5.2, «Al cargar»), y se añaden T35 y T36.

- [x] **T35**: el lector abre el libro en **solo lectura** (R115 ampliado,
  `design.md` §5.2 «Al cargar»; cambio R2-1 de la review 2). En
  `infrastructure/documentos/excel_openpyxl.py`: `_abrir` con
  `load_workbook(io.BytesIO(contenido), read_only=True, data_only=False)` y el
  libro **cerrado siempre** (`finally`) antes de devolver el `LibroLeido`;
  `_metadatos`, `_parece_formato_antiguo` (una pasada `A1:I10`; *séptima
  enmienda: decía `A1:E10`, errata R3-2*), `_cabecera` y
  `_filas` con `iter_rows` acotados, sin `ws.cell` ni `ws._cells`;
  `_datos_fuera_del_tope` sin `_celdas_existentes`, mirando solo las filas que
  el XML trae, **sin** el relleno de huecos de `iter_rows` en solo lectura (el
  analizador de filas de la hoja, fijado por un test y con fallo cerrado, o una
  pasada con `defusedxml` por nombre local; §5.2). El test que fijaba
  `ws._cells` se sustituye por el de la vía elegida. Tests en
  `tests/test_f036_excel_lector.py`, nombres `test_f036_r115_…`:
  - los tres ficheros de la review 2 —rango combinado `A1003:A1048576`, rango
    combinado `A1003:H1048576` e hipervínculo sobre `A1003:H1048576`, en
    «Incidencias» de una plantilla generada— se leen o se rechazan en **< 1 s**
    y con el pico de `tracemalloc` bajo el tope que ya usan los tests;
  - lo mismo con el rango en `_plantilla` y en `Instrucciones`;
  - lo mismo sobre un **Excel de errores** con una fila con error;
  - un **combinado pequeño** `C2:D2` en una fila con datos se **admite**: la
    fila entra con la descripción corta y sin detalle;
  - el libro se abre con `read_only=True` y se cierra, también cuando la
    lectura falla a medias (doble de `load_workbook`);
  - los `test_f036_r115_…` de T31 siguen en verde.
  Fase RED: los tres ficheros de la review pasan de 1 s sobre el lector de
  `52f8149` (con un tope de tiempo en el subproceso para no esperar minutos). |
  Verificación: `pytest tests/test_f036_excel_lector.py tests/test_f036_importacion_dominio.py`
- [x] **T36**: campaña de mutación del cambio con `--base 52f8149` sobre lo que
  cambie en producción, y su informe
  (`progress/mutacion_F-036_bloque10bis.md`), con cero supervivientes sin
  cerrar o sin justificación. En la **review 3**, además, las mutaciones de
  orden del código nuevo: que ningún camino del lector llame a `load_workbook`
  en modo normal ni recorra una hoja antes de abrirla en solo lectura, y que el
  `close` no pueda quedar antes de extraer los datos ni saltarse en un error.
  (Si se hubiera elegido el examen previo del XML, la puerta tendría que ir
  **antes** de `load_workbook`; con solo lectura no hay puerta nueva que
  ordenar.) |
  Verificación: `python -m harness.mutacion --feature F-036 --base 52f8149 --workers 6`
  (desde la raíz, como las campañas anteriores) y el informe generado

> **Séptima enmienda del 2026-10-01 · review 3** (CHANGES_REQUESTED, R3-1; el
> humano eligió hacer el arreglo). El solo lectura cierra lo que se expande al
> cargar, pero no el coste por **elemento**: con 64 KB y 4,1 millones de `<xf/>`
> en `styles.xml`, 114 s y 2,5 GB. Se añaden T37 y T38 (R117, `design.md` §5.2
> «El presupuesto de elementos XML»).

> **Séptima enmienda bis del 2026-10-01 · hallazgo T37-1** (el humano eligió la
> opción (a)). El recuento de T37 miraba solo `.xml` y `.rels`, y una hoja en
> `sheet1.dat` se lo saltaba (74 KB → 48 s y 911 MB). Se añaden T37 bis y T38
> bis: todas las partes del ZIP y presupuesto de 300.000.

- [x] **T37**: el **presupuesto de elementos XML** (R117; cambio R3-1 de la
  review 3). En `infrastructure/documentos/excel_openpyxl.py`, la constante
  `PRESUPUESTO_ELEMENTOS_XML = 200_000` junto a las de 2 MiB, 20 MiB y 500
  entradas, y un paso `_contar_elementos_xml(contenido)` **entre
  `_inspeccionar_zip` y `_abrir`** en `LectorPlantillaOpenpyxl.leer`: cuenta en
  *streaming*, por trozos, con un analizador expat de `defusedxml` sin DTD ni
  entidades y sin construir árbol, los elementos de **apertura** de todas las
  partes `.xml` y `.rels` del ZIP, en un total global; se corta al pasar el
  presupuesto; por encima, `fichero_sospechoso`; un XML que no se analiza,
  `no_es_xlsx`; en los dos casos sin llamar a `load_workbook`. Además, un script
  pequeño `scripts/contar_elementos_xml_f036.py <ruta.xlsx>` que imprime el total
  de elementos (con la misma función, sin cortar al presupuesto) y el
  presupuesto, para medir el `v2` guardado desde Excel en T29; sin nombres ni
  contenido del fichero en la salida. Tests en `tests/test_f036_excel_lector.py`,
  nombres `test_f036_r117_…`, con los libros **construidos en memoria**:
  - los siete ficheros de la tabla de R3-1 (`<xf/>` en `xl/styles.xml`; en
    «Incidencias», `<dataValidation/>`, `<brk/>`, `<mergeCell/>`, celdas vacías
    con estilo, formato condicional e hipervínculos, cada uno repetido hasta
    rozar los 20 MiB) se rechazan con `fichero_sospechoso` en **< 1 s**, con el
    pico de `tracemalloc` bajo el tope de los tests y **sin** llamar a
    `load_workbook` (doble que revienta);
  - la plantilla completa (1000 filas, detalle de 2000) se admite y su cuenta es
    menor que `PRESUPUESTO_ELEMENTOS_XML // 5`;
  - un doble dice cuántos elementos se contaron: con 4 millones, no más de
    `PRESUPUESTO_ELEMENTOS_XML + 1`;
  - frontera: exactamente el presupuesto se admite; uno más, se rechaza;
  - el total es global (dos partes que caben por separado y no juntas);
  - elementos con prefijo y un `.rels` cuentan;
  - DTD, entidad o XML roto en una parte → `no_es_xlsx` sin abrir;
  - el script cuenta igual que la función y no imprime contenido.
  Fase RED: los siete ficheros sobre el lector de `becb693` pasan de 1 s (con
  tope de tiempo en el subproceso) o no dan `fichero_sospechoso`. |
  Verificación: `pytest tests/test_f036_excel_lector.py`
- [x] **T38**: campaña de mutación con `--base becb693` sobre lo que cambie en
  producción, y su informe (`progress/mutacion_F-036_bloque10ter.md`), con cero
  supervivientes sin cerrar o sin justificación. En la **review 4**, la mutación
  de orden de la puerta nueva: bajar `_contar_elementos_xml` por debajo de
  `_abrir` (o de `load_workbook`) tiene que poner la suite en rojo; y subirla por
  encima de `_inspeccionar_zip` o del tope de 2 MiB, también. |
  Verificación: `python -m harness.mutacion --feature F-036 --base becb693 --workers 6`
  (desde la raíz) y el informe generado
- [x] **T37 bis**: el presupuesto cuenta **todas las partes del ZIP** y vale
  **300.000** (R117 con la séptima enmienda bis; `design.md` §5.2, «Todas las
  partes»). En `infrastructure/documentos/excel_openpyxl.py`:
  `PRESUPUESTO_ELEMENTOS_XML = 300_000`; `_contar_elementos_xml` recorre todas
  las entradas, sin `EXTENSIONES_XML`; en una parte que no acaba en `.xml` ni
  en `.rels`, un fallo de *expat* deja contados los elementos abiertos hasta
  ahí, deja de leer esa parte y sigue con la siguiente; en las `.xml` y `.rels`
  el fallo sigue siendo `no_es_xlsx`; DTD o entidades, en cualquier parte,
  `no_es_xlsx`. El script `scripts/contar_elementos_xml_f036.py` cuenta igual y
  su veredicto usa el quinto nuevo (60.000). Tests en
  `tests/test_f036_excel_lector.py`, nombres `test_f036_r117_…`, con los
  libros construidos en memoria:
  - el fichero de T37-1 —la plantilla con «Incidencias» en
    `xl/worksheets/sheet1.dat`, su relación y su tipo de contenido apuntando
    ahí, y 1,6 millones de `<brk/>`— → `fichero_sospechoso` en < 1 s, con
    memoria acotada y sin llamar a `load_workbook`;
  - un `.bin` con XML dentro por encima del presupuesto → lo mismo;
  - una **imagen real** (un PNG válido, generado en el test) cuenta **0**
    elementos y no se lee más allá de su primer trozo (un doble cuenta los
    bytes leídos); un `printerSettings1.bin` binario no impide admitir la
    plantilla;
  - una parte `.dat` que empieza siendo XML y falla a mitad: sus elementos
    hasta el fallo cuentan (por encima del presupuesto, `fichero_sospechoso`;
    por debajo, el recuento sigue);
  - un `.bin` con DTD → `no_es_xlsx`; un `.xml` roto, como en T37;
  - el **Excel de errores más grande** (1000 filas con error en las 8
    columnas, con el VML de los comentarios: 148.916 elementos) se admite;
  - la plantilla completa queda por debajo de `PRESUPUESTO_ELEMENTOS_XML // 5`;
  - el test de la constante pasa a 300.000 y el de la frontera, a 300.000 /
    300.001;
  - los tests de tiempo de R115 y R117 miden en un **subproceso sin
    cobertura**;
  - el coste del peor caso admitido: un fichero con ~300.000 elementos en
    «Incidencias» se lee, y se anota en el informe cuánto tarda y cuánta
    memoria usa (sin tope en el test; la cifra es para la review).
  Fase RED: el fichero de T37-1 y el `.bin` sobre el lector de `29e28a6`
  pasan de 1 s o no dan `fichero_sospechoso`. |
  Verificación: `pytest tests/test_f036_excel_lector.py tests/test_f036_alcance_cerrado.py`
- [x] **T38 bis**: campaña de mutación con `--base 29e28a6` sobre lo que cambie
  en producción, y su informe (`progress/mutacion_F-036_bloque10quater.md`), con
  cero supervivientes sin cerrar o sin justificación. En la **review 4**, la
  mutación de orden de la puerta: bajar `_contar_elementos_xml` por debajo de
  `_abrir` (o de `load_workbook`) pone la suite en rojo, también con el fichero
  de T37-1; y quitar la parte no-XML del recuento (volver a filtrar por
  extensión) también. |
  Verificación: `python -m harness.mutacion --feature F-036 --base 29e28a6 --workers 6`
  (desde la raíz) y el informe generado

> **Octava enmienda del 2026-10-01 · cambio de estrategia** (review 4, R4-1;
> opción (A) del humano «pero dobla los límites»). Cuarto hueco de la misma
> familia: los atributos `sqref` se convierten en un objeto por rango y el
> presupuesto de elementos no los ve. En vez de otro parche, la lectura con
> `openpyxl` de un fichero subido pasa a un **proceso hijo con 30 s y 1 GB**
> (R118–R120; `design.md` §5.2, «La lectura aislada en un proceso hijo»), y el
> tope descomprimido pasa a el doble del fichero legítimo más grande (R16). Se
> mantienen el solo lectura, R115 y R117. Se añaden T39–T44; se encarga el
> bloque entero, en orden.

- [x] **T39**: fase RED con los ficheros de R4-1 (cambio R4-1 de la review 4).
  Construir en memoria, sobre una plantilla generada, tres ficheros con un
  **`<dataValidation>`**, un **`<conditionalFormatting>`** y un **`<scenario>`**
  en «Incidencias», cada uno con un `sqref` de muchos rangos hasta rozar el tope
  descomprimido de hoy (20 MiB) dentro de los 2 MiB comprimidos, y **medir de
  extremo a extremo** el lector de HEAD (`LectorPlantillaOpenpyxl().leer`) en un
  subproceso con tope de 120 s: tiempo, pico de memoria y resultado. Pegar la
  tabla en el informe: confirma o corrige la estimación de la review 4 (~100 s y
  1,6 GB). Dejar los constructores de esos ficheros en los tests (para T42) y los
  tests de T42 escritos en rojo. Sin código de producción. |
  Verificación: la tabla en `progress/impl_F-036.md` y los tests nuevos en rojo
- [x] **T40**: el **ejecutor en subproceso** (R118–R120; §5.2 «La lectura
  aislada»).
  - `infrastructure/documentos/ejecutor_aislado.py`: `EjecutorAislado`, con
    `multiprocessing` (`forkserver` con `set_forkserver_preload` en Linux;
    `spawn` en Windows), tope de reloj, `terminate` y `kill`, `join` siempre,
    canal con `recv_bytes(maxlength=…)`, y el hijo con `setrlimit(RLIMIT_AS)` al
    empezar (Linux) y un código de salida propio para `MemoryError`.
  - `infrastructure/documentos/excel_openpyxl.py`: `leer_en_hijo(contenido) ->
    bytes`, que hace `_abrir` + `_extraer` y devuelve el JSON (o el error de
    dominio como JSON).
  - `infrastructure/documentos/lector_aislado.py`: `LectorPlantillaAislado`
    (pasos 1–2 bis en el padre, ejecutor, validación del JSON, reconstrucción
    del `LibroLeido`, semáforo de una plaza con 5 s de espera, 503
    `LectorSinAislamiento` en `dev`/`pro` sin `setrlimit`, aviso fuera), con
    `SEGUNDOS_HIJO = 30` y `BYTES_MEMORIA_HIJO = 1024 ** 3`; sin importar
    `openpyxl`. Los errores nuevos (`LectorSinAislamiento`, `LecturaOcupada`, los
    dos 503) en `domain/models/errores.py` y su traducción en `function_app.py`.
  - `interface_adapters/api/importar.py` compone `LectorPlantillaAislado`.
  - Medir y anotar el coste de arranque del primer hijo y de los siguientes, en
    Windows (`spawn`) y, si la máquina lo permite, en Linux (`forkserver`).
  Tests `tests/test_f036_lector_aislado.py` (`test_f036_r118_…`, `r119_…`,
  `r120_…`): con un **doble del ejecutor**, cada estado del hijo, el JSON
  validado (roto, tipos, filas de más, columna desconocida), el orden (los pasos
  baratos rechazan sin llamar al ejecutor), el semáforo y la plataforma; con el
  **ejecutor real** y topes inyectados pequeños, tiempo agotado (todas las
  plataformas) y memoria agotada (solo Linux, `skipif`); un test que fija los
  topes de producción; y el de arquitectura: `lector_aislado.py` no importa
  `openpyxl`. |
  Verificación: `pytest tests/test_f036_lector_aislado.py tests/test_f036_arquitectura.py tests/test_f036_importar_http.py`
- [x] **T41**: **medir** el tope descomprimido y el del resultado (R16 con la
  octava enmienda; `MAX_BYTES_RESULTADO`). Con el generador de la rama:
  - la plantilla completa (1000 filas, detalle de 2000) y el Excel de errores
    más grande (1000 filas con error en las 8 columnas, con el VML de los
    comentarios): bytes descomprimidos (suma de `file_size` del ZIP) y bytes
    del JSON que devuelve `leer_en_hijo`;
  - `MAX_BYTES_DESCOMPRIMIDOS` = el **doble** del mayor de los dos, redondeado
    hacia arriba al MiB; `MAX_BYTES_RESULTADO` = el doble del mayor JSON,
    redondeado al MiB;
  - pegar la medición en el informe y en el docstring de las constantes, y
    escribir los dos números en un test (`test_f036_r16_…`, `test_f036_r118_…`);
  - comprobar que el formato antiguo real (1.680 elementos) y un `v2` de prueba
    caben; si el `v2` guardado desde Excel no cupiera, T29 lo dirá y se volverá
    al spec-author. |
  Verificación: `pytest tests/test_f036_excel_lector.py tests/test_f036_lector_aislado.py`
  y la tabla en `progress/impl_F-036.md`
- [x] **T42**: los **ficheros hostiles de todas las reviews**, por el lector
  aislado: la celda con estilo en la fila 1.048.576 (review 1), los rangos que
  se expanden al cargar y el comentario sobre rango (reviews 2 y 3), los siete
  de la review 3, el `sheet1.dat` de T37-1 y los tres de R4-1 (T39). Cada uno se
  rechaza **a tiempo** —en el padre por los pasos baratos o en el hijo antes de
  su tope más el arranque— y con el **pico de la memoria del padre**, medido con
  `tracemalloc` en el padre, **por debajo de `6 * MAX_BYTES_DESCOMPRIMIDOS`**
  (102 MiB), un tope fijo escrito en el test que cubre el resultado acotado y
  el recuento de R117 (*octava enmienda bis, H-T40-1: decía «sin que crezca la
  memoria del padre más allá del resultado acotado»; medido, 80,8 MiB con los
  ficheros de R4-1*). Lo legítimo **se admite** por el
  hijo real: la plantilla completa y el Excel de errores más grande dan el mismo
  `LibroLeido` que el lector en proceso. Los de R4-1, que dependen del hijo, con
  el tope de producción de 30 s, marcados como lentos si hace falta, y además con
  un tope inyectado pequeño para la suite normal. |
  Verificación: `pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py`
- [x] **T43**: campaña de mutación con `--base b8c51e1` sobre lo que cambie en
  producción, y su informe (`progress/mutacion_F-036_bloque10quinquies.md`), con
  cero supervivientes sin cerrar o sin justificación. En la **review 5**, las
  mutaciones de orden: que el padre **no llame nunca** a `openpyxl` para leer un
  fichero subido (mover `_abrir`/`_extraer` al padre, o saltarse el ejecutor,
  pone la suite en rojo); que los pasos baratos sigan antes del hijo; y que el
  `kill` y el `join` no se puedan saltar en un tiempo agotado. |
  Verificación: `python -m harness.mutacion --feature F-036 --base b8c51e1 --workers 6`
  (desde la raíz) y el informe generado
- [x] **T44**: documentación de lo que cambia hacia fuera: `docs/ARCHITECTURE.md`
  (la lectura aislada en «Entrada de incidencias») y `docs/INTEGRACION.md` («Qué
  se rompe si alguien toca algo»: la importación necesita una instancia de
  **2.048 MB** y **una** lectura a la vez por proceso; bajar la memoria, subir
  la concurrencia o `FUNCTIONS_WORKER_PROCESS_COUNT` la rompe; los 503 nuevos), y
  su copia en `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  (commit local en `azure-apps`, sin push). Tests de documentación que
  apliquen. |
  Verificación: `pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py`

## Bloque 11 · Arreglos de la review 5 (añadido en la novena enmienda del 2026-10-01)

> Review 5 **APPROVED** con residuales. Decisión del humano (2026-10-01): R5-1
> **se arregla**; R5-2 y R5-4, aceptados; R5-3, R5-5 y R5-6, antes del merge.
> El bloque va antes de las MANUAL pendientes (T16, T27–T29) y de T30, y se
> encarga entero, en orden. Solo T45 toca código de producción.

- [x] **T45**: el **tope de CPU del hijo** (R119 con la novena enmienda;
  hallazgo R5-1; `design.md` §5.2, «El tope de CPU del hijo» y paso 1 bis de
  «El hijo»).
  - **Fase RED**, antes de tocar producción: los tests de `design.md` §5.2,
    «Cómo se prueba», punto del tope de CPU, en
    `tests/test_f036_lector_aislado.py` (`test_f036_r119_…`), en rojo sobre
    HEAD. El del hijo huérfano (un hijo que gasta CPU sin parar y sin padre que
    lo mate **no muere** hoy) y el de «cuenta CPU, no reloj» son **solo de
    Linux** (`skipif`): en Windows se saltan, y su rojo y su verde se enseñan
    ejecutándolos en un **contenedor Linux**, como hizo la review 5 (si el
    contenedor no tiene las dependencias de la suite, con un guion contra el
    código de HEAD, diciéndolo). El del valor (`math.ceil(segundos) +
    MARGEN_SEGUNDOS_CPU`, con `setrlimit` doblado) corre en todas las
    plataformas y es el que ve la campaña de mutación en Windows.
  - **Arreglo**, en `infrastructure/documentos/ejecutor_aislado.py`:
    `MARGEN_SEGUNDOS_CPU = 5`; el hijo se pone `RLIMIT_CPU` (blando y duro
    iguales) junto al `RLIMIT_AS`, antes de mandar el byte del canal y antes
    de leer; el ejecutor calcula el valor a partir de `segundos` y se lo pasa
    al hijo. **No cambian**: el protocolo `EjecutorAislado`, `SalidaHijo`,
    `tope_de_memoria_disponible()`, `lector_aislado.py`, el tope de reloj del
    padre ni ningún estado. Sin `resource` (Windows) no se aplica y no hay
    aviso nuevo. Actualizar el docstring del módulo (el tope de CPU y que
    cuenta CPU, no reloj).
  - Una frase en `docs/ARCHITECTURE.md`, «La lectura aislada»: el hijo lleva
    también tope de CPU, para el caso del padre muerto. No cambia nada de lo
    que el servicio expone o consume: `docs/INTEGRACION.md` y `azure-apps` no
    se tocan.
  - Pegar en `progress/impl_F-036.md` la salida de Linux (rojo antes, verde
    después) y cuánto tarda en morir el huérfano. |
  Verificación: `pytest tests/test_f036_lector_aislado.py tests/test_f036_arquitectura.py tests/test_f036_documentacion.py`
  y, en un contenedor Linux, los dos tests `skipif` de Linux en verde (salida
  en `progress/impl_F-036.md`)
- [x] **T46**: el test que depende de la carga de la máquina (R5-3). En
  `tests/test_f036_lector_aislado.py`,
  `test_f036_r118_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado`
  usa `SEGUNDOS_INYECTADOS = 3.0` para todos los ficheros. Los `SE_LEE_IGUAL`
  (los que **deben leerse**) pasan a un tope inyectado **holgado**
  —`lector_aislado.SEGUNDOS_HIJO`, el de producción— y su comprobación de
  tiempo se ajusta a ese tope; los 3 s se quedan **solo** para los
  `EN_EL_HIJO`, que deben pasarse de él. Los que se paran en el padre no
  dependen del tope. No se afloja ninguna otra comprobación (resultado, pico
  del padre, que el padre no abra el libro). Sin código de producción. |
  Verificación: `pytest tests/test_f036_lector_aislado.py`, y el test de los
  hostiles lanzado tres veces seguidas con la máquina cargada (por ejemplo,
  con la suite del `api` corriendo a la vez), en verde las tres
- [x] **T47**: errata R4-3 (arrastrada en R5-5). En `progress/impl_F-036.md`,
  «Mutación (T38 bis)» dice **6** workers y el informe de la herramienta
  (`progress/mutacion_F-036_bloque10quater.md`) dice **5**: corregir el
  informe del implementer a 5, con una nota de que es una errata corregida
  (los segundos que haya calculados a partir de 6, también). La errata R4-2
  ya queda corregida en `design.md` por esta enmienda: no hay que tocarla. |
  Verificación: `grep -n "workers" progress/mutacion_F-036_bloque10quater.md`
  y la sección «Mutación (T38 bis)» de `progress/impl_F-036.md` dicen lo mismo
- [x] **T48**: reponer la decisión que desapareció del registro (R5-6). El
  commit `6b7d598` quitó de `progress/current.md` el bloque «F-036
  DESBLOQUEADA · H-T40-1 decidido por el líder: opción (1)», con su motivo.
  Recuperarlo **literal** con `git show 6b7d598^:progress/current.md` y
  reponerlo en su sitio cronológico (entre el bloque de T42–T44 y el de
  T39–T41), sin reescribirlo ni resumirlo. |
  Verificación: `grep -n "DESBLOQUEADA · 2026-10-01 · H-T40-1" progress/current.md`
  da una línea, y el bloque es igual al de `git show 6b7d598^:progress/current.md`
- [x] **T49**: campaña de mutación con `--base c58e3b4`, **solo** sobre lo que
  cambia en producción en este bloque (`ejecutor_aislado.py`), y su informe
  (`progress/mutacion_F-036_bloque11.md`), con cero supervivientes sin cerrar
  o sin justificación. La campaña corre en Windows, donde los dos tests de
  Linux se saltan: las mutaciones del tope de CPU (quitar el `setrlimit`,
  cambiar `RLIMIT_CPU` por otro, quitar o cambiar el margen, quitar el
  redondeo, ponerlo después del byte del canal) tienen que caer por el test
  del valor con `setrlimit` doblado; si alguna solo cae en Linux, decirlo en
  el informe con la ejecución en el contenedor. |
  Verificación: `python -m harness.mutacion --feature F-036 --base c58e3b4 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque11.md`
  (desde la raíz) y el informe generado
  > *Errata corregida el 2026-10-02 (review 6, R6-3):* a la orden le faltaba
  > `--timeout 900`. Con los 120 s por defecto de `harness/rigor.json` da 2
  > timeouts y ningún veredicto: la suite del `api` tarda más que eso en llegar
  > a los tests que matan. La campaña del informe se lanzó ya con él.

## Bloque 12 · Formato visual de la plantilla (añadido en la décima enmienda del 2026-10-02)

> Petición del humano del 2026-10-02, con muestra aprobada. R121–R127;
> `design.md` §3.6 y §5.2, «Los topes y el formato visual». El bloque va
> después de la primera T28 y **antes** de T29, y se encarga entero, en
> orden. Solo T51 toca código de producción, y solo el **generador** de
> `infrastructure/documentos/excel_openpyxl.py`: ni el lector, ni
> `lector_aislado.py`, ni `ejecutor_aislado.py`, ni el dominio, ni el YAML, ni
> el front. **Ningún tope se cambia** en este bloque. Sin logotipo ni
> imágenes. El script de la muestra **no** está en el repositorio ni se
> añade: la referencia son las tablas de `design.md` §3.6.
>
> *(Enmienda 10 bis.)* Bloque **hecho**; la review 7 pidió cambios y el
> humano decidió quitar la impresión y enseñar una sola fila. Lo que aquí
> fija el cuerpo estático, la regla única de bandas y la impresión lo
> corrige el **Bloque 13**; estas tareas no se reabren.

- [x] **T50**: **medir el «antes»** y fase RED.
  - Sobre HEAD, sin tocar producción, medir de la plantilla completa y del
    Excel de errores más grande (los de `_legitimos()` de
    `tests/test_f036_lector_aislado.py`): elementos XML, bytes
    descomprimidos, bytes del fichero, bytes del JSON de `leer_en_hijo`, y
    tiempo y pico de memoria de la lectura por el hijo real (`design.md`
    §5.2, tabla de medidas; decir con qué se midió la memoria). Pegar la
    tabla en `progress/impl_F-036.md`: es la referencia de T52.
  - Tests nuevos en rojo (`design.md` §3.6, «Cómo se prueba»):
    `test_f036_r121_…` a `test_f036_r125_…` en
    `tests/test_f036_excel_generador.py`, con los valores **literales** de
    las tablas de §3.6; y `test_f036_r127_…` (una sola regla condicional de
    un rango en la plantilla y ninguna en el Excel de errores; el Excel de
    errores más grande `<= PRESUPUESTO // 2`) en
    `tests/test_f036_lector_aislado.py`.
  - Los **cuatro tests que fijaban el aspecto antiguo** pasan a los valores
    nuevos y quedan en rojo:
    `test_f036_s3_1_anchos_de_las_columnas_de_incidencias`,
    `test_f036_r5_disposicion_de_instrucciones`,
    `test_f036_r5_anchos_de_instrucciones` y
    `test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario`
    (este último: «sin relleno» solo en las columnas de datos; la columna
    `Errores` lleva `FFF3F4F5`). **Ningún otro test existente se toca.**
  - Tests de invariantes `test_f036_r126_…` (ida y vuelta por
    `LectorPlantillaOpenpyxl` y por `LectorPlantillaAislado`; mismo
    `LibroLeido` con y sin formato; sin `<f>`; mismas hojas, nombres
    definidos de las listas, validaciones, protección, filtro, paneles y
    formato de texto): estos nacen **en verde** sobre HEAD y tienen que
    seguir en verde tras T51; decirlo en el informe, con la salida. |
  Verificación: `pytest tests/test_f036_excel_generador.py tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py`
  con los `r121`–`r125`, los `r127` de la regla condicional y los cuatro
  retocados en rojo y todo lo demás en verde; y la tabla del «antes» en
  `progress/impl_F-036.md`
- [x] **T51**: **el formato en el generador** (R121–R125; `design.md` §3.6).
  En `infrastructure/documentos/excel_openpyxl.py`: las constantes de §3.6,
  «Dónde vive cada constante» (colores con su token de F-035 en el
  comentario, `FUENTE`, tamaños, altos, `ANCHOS` con los valores nuevos,
  `RELLENO_ERROR` en rojo suave, `FUENTE_ERROR`, `FORMULA_BANDAS`,
  `PIE_DE_PAGINA`); `_incidencias` (cabecera, cuerpo, columna `Errores`,
  celdas con error, cuadrícula, pestaña, la regla condicional **solo si
  ninguna fila lleva errores**, impresión); `_instrucciones` (banda de la
  obra, título con su línea, párrafos con el alto calculado por
  `_alto_de_parrafo`, tabla de ejemplos, cuadrícula, pestaña, anchos); y el
  docstring del módulo. Los objetos de estilo se construyen una vez por zona
  y se comparten. **No cambian**: `_texto`, `_catalogos`, `_metadatos`,
  `_validacion`, la firma de `generar`, la protección, el filtro, los
  paneles, el formato de texto, el comentario del error ni nada de lo que
  hay bajo «El lector». Si el título de impresión o cualquier otro ajuste
  rompe la lectura en solo lectura (test de ida y vuelta de R126), **no** se
  toca el lector: se aplica la regla de recorte de T52. |
  Verificación: `pytest tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_lector_aislado.py tests/test_f036_migracion.py tests/test_f036_importar_http.py tests/test_f036_arquitectura.py`
  en verde, con los de T50 incluidos
- [x] **T52 · con PARADA si falta margen**: **volver a medir los topes**
  (R127; `design.md` §5.2, «Los topes y el formato visual»). Las mismas
  medidas de T50, en la misma máquina y con el mismo método, de la plantilla
  completa y del Excel de errores más grande ya con formato; tabla
  «antes / después / margen que hay que conservar / ¿cabe?» en
  `progress/impl_F-036.md`. Márgenes: elementos de la plantilla completa
  < 60.000; del Excel de errores más grande ≤ 150.000; bytes descomprimidos
  del mayor ≤ 8.912.896 (el doble sigue siendo 17 MiB); JSON del mayor
  ≤ 5.767.168 (debería salir idéntico al de T50; si cambia un solo byte,
  explicarlo: el lector no lee estilos); tiempo del hijo real ≤ 15 s y pico
  de memoria ≤ 512 MiB, y ninguno más de un 25 % peor que en T50. Medir
  también un `v2` de prueba de la migración con formato frente a un quinto
  del presupuesto (`scripts/contar_elementos_xml_f036.py`). **Regla de
  decisión**: si todo cabe, seguir. Si algo no cabe, **recortar adorno y
  volver a medir**, en el orden de `design.md` §5.2 —(a) bandas alternas,
  (b) ajustes de impresión, (c) celdas sin valor de «Instrucciones»—,
  anotando cada recorte con la medida que lo motivó y cambiando su test a
  «no está». **Si recortado todo sigue sin caber: PARADA** (`blocked` en
  `progress/current.md`, con la tabla): **no se sube ningún tope** ni se
  toca ninguna constante de `lector_aislado.py`; subir un tope es decisión
  del humano. |
  Verificación: la tabla en `progress/impl_F-036.md` con todos los márgenes
  conservados (o los recortes anotados), y
  `pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py`
  en verde **sin haber tocado** los tests de T41 ni las constantes de topes
  (`git diff 07bd0c9 -- services/postventa-api/infrastructure/documentos/lector_aislado.py services/postventa-api/infrastructure/documentos/ejecutor_aislado.py`
  vacío)
- [x] **T53**: **documentación**, solo si algún documento describe el
  aspecto. Buscar en `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`,
  `services/postventa-front/importar.html` y
  `config/plantilla_incidencias.yaml` menciones al color o al aspecto de la
  plantilla o del Excel de errores (naranja, relleno, negrita, anchos). El
  spec-author no encontró ninguna que fije un color (dicen «celdas
  marcadas», que sigue siendo verdad): si es así, **no se cambia nada** y se
  anota la búsqueda en el informe. Si aparece alguna, se corrige y se añade
  una frase en `docs/ARCHITECTURE.md`, «Entrada de incidencias (F-036)».
  El formato **no cambia lo que el servicio expone o consume**:
  `docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md` no se tocan
  por este bloque. Los cuadros de «Hoy» de `design.md` §5.2 se dejan como
  están, y los docstrings de las constantes de `lector_aislado.py` también
  (ese fichero no se toca): las cifras nuevas van en el informe, para que el
  spec-author las lleve a la spec si hace falta. |
  Verificación: `pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py`
  y la búsqueda anotada en `progress/impl_F-036.md`
- [x] **T54**: campaña de mutación con `--base 07bd0c9`, **solo** sobre lo
  que cambia en producción en este bloque (el generador de
  `excel_openpyxl.py`), y su informe (`progress/mutacion_F-036_bloque12.md`),
  con cero supervivientes sin cerrar o sin justificación. El formato son
  muchas constantes: cada valor de las tablas de `design.md` §3.6 tiene que
  caer por un test que compruebe su valor literal; un superviviente en un
  color, un tamaño o un ancho se cierra con el test que falta, no con una
  justificación. Mutaciones que tienen que caer, además: poner la regla
  condicional también en el Excel de errores; ampliar su rango a la columna
  `Errores`; quitar el relleno o el color de la celda con error; quitar el
  bloqueo, el formato de texto o la validación al aplicar los estilos
  (invariantes de R126). |
  Verificación: `python -m harness.mutacion --feature F-036 --base 07bd0c9 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque12.md`
  (desde la raíz) y el informe generado

## Bloque 13 · Sin impresión y una sola fila a la vista (añadido en la enmienda 10 bis del 2026-10-02)

> Decisión del humano tras la review 7 (R7-1, R7-2). R122, R123, R125, R126 y
> R127 tal como quedan en la 10 bis; `design.md` §3.6 y §5.2, notas «10 bis».
> El bloque va después de la review 7 y **antes** de la review 8, del
> redespliegue y de la T28 repetida. Se encarga en dos tandas, con la PARADA
> de T59 en medio: **T55–T58** al implementer; **T59** al líder y al humano;
> **T60** al implementer cuando el humano dé el visto bueno. Solo T56 toca
> código de producción, y solo el **generador** de
> `infrastructure/documentos/excel_openpyxl.py`: ni el lector, ni
> `lector_aislado.py`, ni `ejecutor_aislado.py`, ni el dominio, ni el YAML, ni
> el front. **Ningún tope se cambia.** Base de comparación: `26a190e` (la
> review 7; producción igual que en `50b42b1`).

- [x] **T55**: **medir el «antes»** y fase RED.
  - Sobre HEAD (producción con el formato de la décima), las mismas medidas
    de T50/T52 con el mismo método y en la misma máquina en que se hará
    T57: elementos XML, bytes descomprimidos, bytes del fichero, bytes del
    JSON de `leer_en_hijo`, tiempo y pico de memoria de la lectura por el
    hijo real, de la plantilla completa y del Excel de errores más grande de
    `_legitimos()`. Tabla en `progress/impl_F-036.md`, «Bloque 13»: es la
    referencia de T57. (Deberían salir las de T52: 26.990 y 149.016
    elementos, 8.578.900 B; si no, explicarlo.)
  - Tests nuevos o cambiados, en rojo, según `design.md` §3.6, «Cómo se
    prueba, tras la enmienda 10 bis»: las tres reglas (y las dos del Excel
    de errores) leídas del libro, con `sqref`, tipo, fórmula literal,
    prioridad, `stopIfTrue` y `dxf`; el cuerpo sin bordes ni relleno
    estáticos (salvo el rojo de la celda con error) y con su fuente,
    alineación, desbloqueo y `@` estáticos; la **ausencia** de impresión en
    las cuatro hojas y en `workbook.xml`; los `r127` de tres y dos
    `<conditionalFormatting>`. Los tests del Bloque 12 que cambian a
    propósito son los de la lista de §3.6; **ningún otro test existente se
    toca**.
  - Tests nuevos que nacen **en verde** sobre HEAD y deben seguir en verde
    tras T56: la plantilla con el **formato de la décima** (ayudante del
    test) da el mismo `LibroLeido` por `LectorPlantillaOpenpyxl` y por
    `LectorPlantillaAislado` y valida con cero errores (R126). Decirlo en el
    informe, con la salida. |
  Verificación: `pytest tests/test_f036_excel_generador.py tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py`
  con los nuevos y los cambiados en rojo y todo lo demás en verde (salida
  real en el informe), y la tabla del «antes» en `progress/impl_F-036.md`
- [x] **T56**: **el generador sin impresión y con el cuerpo por formato
  condicional** (R122, R123, R125; `design.md` §3.6). En
  `infrastructure/documentos/excel_openpyxl.py`, solo en `_incidencias`, las
  constantes y el docstring del módulo:
  - quitar el bloque «Impresión (R125)» entero y las constantes
    `MARGEN_LATERAL` y `PIE_DE_PAGINA`;
  - en el bucle del cuerpo, dejar de poner `border` en todas las celdas y
    `fill` en las de `Errores`; **conservar** fuente, alineación,
    `Protection(locked=False)` y `FORMATO_TEXTO` en las columnas de datos, y
    la fuente de `Errores`;
  - en la celda con error, el relleno y la fuente rojos estáticos, como hoy
    (sin borde estático, que ya no tiene);
  - las tres reglas de la tabla de §3.6, en su orden (1 líneas `A2:I1001`,
    2 gris `I2:I1001`, 3 bandas `A2:H1001` solo sin errores), con
    `FORMULA_PINTADA` y el valor nuevo de `FORMULA_BANDAS`, los rangos
    construidos con `PRIMERA_FILA`/`ULTIMA_FILA`, y el `dxf` de la 1 con
    `_borde_fino()`;
  - el comentario de `ANCHOS` sin el A4, y el docstring del módulo al día.
  **No cambian**: `_instrucciones`, `_texto`, `_catalogos`, `_metadatos`,
  `_validacion`, la firma de `generar`, la protección, el filtro, los
  paneles, el comentario del error ni nada de lo que hay bajo «El lector». |
  Verificación: `pytest tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_lector_aislado.py tests/test_f036_migracion.py tests/test_f036_importar_http.py tests/test_f036_arquitectura.py`
  en verde, con los de T55 incluidos y los hostiles de R4-1 sin tocar; y
  `git diff 26a190e -- services/postventa-api/infrastructure/documentos/lector_aislado.py services/postventa-api/infrastructure/documentos/ejecutor_aislado.py`
  vacío
- [x] **T57 · con PARADA si falta margen**: **volver a medir los topes**
  (R127; `design.md` §5.2, «Los topes tras la enmienda 10 bis»). Las mismas
  medidas de T55, con el mismo método y en la misma máquina, ya con el
  generador de T56; tabla «antes / después / margen que hay que conservar /
  ¿cabe?» en `progress/impl_F-036.md`. Márgenes, los de T52 sin cambios:
  elementos de la plantilla completa < 60.000; del Excel de errores más
  grande ≤ 150.000 (frente a la guarda de calibración, no al rechazo: R7-3);
  bytes descomprimidos del mayor ≤ 8.912.896; JSON del mayor ≤ 5.767.168 e
  **idéntico** al de T55 (si cambia un byte, explicarlo); tiempo del hijo
  real ≤ 15 s y pico de memoria ≤ 512 MiB, ninguno más de un 25 % peor que
  en T55. Medir también un `v2` de prueba con el formato nuevo frente a un
  quinto del presupuesto (`scripts/contar_elementos_xml_f036.py`). **Regla
  de decisión** (§5.2, con el orden de la 10 bis): si todo cabe, seguir; si
  no, recortar y volver a medir —(a) bandas alternas, (b) celdas sin valor
  de «Instrucciones», (c) la regla 2—, anotando cada recorte con la medida y
  cambiando su test a «no está»; la regla 1 no se recorta. **Si recortado
  todo sigue sin caber: PARADA** (`blocked` en `progress/current.md`, con la
  tabla): **no se sube ningún tope** ni se toca `lector_aislado.py`. |
  Verificación: la tabla en `progress/impl_F-036.md` con los márgenes
  conservados (o los recortes anotados), y
  `pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py`
  en verde, con el `git diff 26a190e` de T56 vacío
- [x] **T58**: **documentación**, solo si algún documento habla de imprimir
  la plantilla o el Excel de errores, o de su aspecto. Buscar «imprim»,
  «impresi», «apaisad», «A4» y «página» en `docs/ARCHITECTURE.md`,
  `docs/INTEGRACION.md`, `services/postventa-front/importar.html`,
  `config/plantilla_incidencias.yaml` (los textos de «Instrucciones») y
  `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`. Si no
  aparece nada sobre este Excel, **no se cambia nada** y se anota la
  búsqueda en el informe. Si aparece, se corrige (en `azure-apps`, commit
  **local**, sin push). El cambio **no** toca lo que el servicio expone o
  consume. |
  Verificación: `pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py`
  y la búsqueda anotada en `progress/impl_F-036.md`
- [x] **T59 · MUESTRA (líder) y PARADA del humano**: antes de la mutación y
  de la review 8, el humano **ve** lo que va a recibir. El líder, con el
  código de T56 y **sin versionar nada**, genera tres libros y los deja en
  `C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\`, todos con prefijo
  `MUESTRA_`:
  1. **`MUESTRA_creacion_incidencias_v2.xlsx`**: desde
     `services/postventa-api`, la orden de T28 con los mismos ficheros que
     cita (el original, el JSON de T2, el YAML de correcciones y el JSON de
     grupos de T27, todos fuera del repo), pero con
     `--salida "C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\MUESTRA_creacion_incidencias_v2.xlsx"`
     y **`--informe` a un fichero del scratchpad**, nunca a
     `progress/migracion_F-036.md` (es el informe aceptado y no se toca);
  2. **`MUESTRA_plantilla_vacia.xlsx`** y **`MUESTRA_excel_de_errores.xlsx`**
     (tres filas, cada una con error en una o dos columnas, valores
     inventados y sin nombres reales): con un guion desechable en el
     scratchpad que llama a `GeneradorPlantillaOpenpyxl().generar(...)` con
     el catálogo y los textos de los tests, o con los de la 0677 si es
     inmediato; para mirar el aspecto da igual.

  Después: `git status` sin ningún `.xlsx` ni cambio en
  `progress/migracion_F-036.md`. El líder **para** y le dice al humano las
  tres rutas y qué mirar, en Excel de escritorio y en Excel web: la
  plantilla vacía enseña la cabecera y **una** fila; al escribir en la
  fila 3 se pinta (líneas, gris de `Errores` y banda); el `v2` enseña sus
  filas con formato y nada debajo, y las bandas siguen bien tras ordenar; el
  Excel de errores, el rojo suave con el texto rojo y sus líneas, sin
  bandas. LibreOffice puede pintar distinto los bordes por formato
  condicional: riesgo aceptado, no se revisa ahí. Si el humano pide
  cambios, vuelve al spec-author; T60 no empieza sin su visto bueno. |
  Verificación: MANUAL (humano): el visto bueno anotado en
  `progress/current.md`
  > *(Hecha, 2026-10-02.)* El líder generó las tres muestras con prefijo
  > `MUESTRA_` en la carpeta de OneDrive (plantilla vacía, `v2` y Excel de
  > errores), sin versionar nada: el informe del `v2` de muestra fue al
  > scratchpad del líder y `progress/migracion_F-036.md` quedó intacto. El
  > humano dio su **visto bueno** («ok»). Preguntó además si la plantilla
  > mantiene el desplegable en las 1.000 filas aunque estén vacías: el líder le
  > confirmó que sí (R126; las validaciones no cambian con la 10 bis).
- [x] **T60**: campaña de mutación con `--base 26a190e`, **solo** sobre lo
  que cambia en producción en este bloque (el generador de
  `excel_openpyxl.py`), y su informe (`progress/mutacion_F-036_bloque13.md`),
  con cero supervivientes sin cerrar o sin justificación. Mutaciones a mano
  que tienen que caer (en copias desechables, nunca en el árbol), además de
  las de la herramienta: volver a poner cualquier línea del bloque de
  impresión de la décima; `ws.print_area = "A1:I50"` y `"A1:I1001"` (M18b,
  M18); `page_setup.scale = 50` (M27); centrado horizontal (M28); margen
  superior 0 (M29); volver a poner el borde estático en el cuerpo o el
  `LIENZO` estático en `Errores`; cambiar `ROW()=2` por `ROW()=1`; quitar la
  `I` del `COUNTA`; intercambiar el orden de alta de dos reglas; poner
  `stopIfTrue`; poner la regla 3 también en el Excel de errores; ampliar el
  rango de la 2 a `A2:I1001` o el de la 3 a la columna `Errores`; quitar el
  relleno o el color rojos de la celda con error; quitar el desbloqueo, el
  `@` o la fuente estática del cuerpo. |
  Verificación: `python -m harness.mutacion --feature F-036 --base 26a190e --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque13.md`
  (desde la raíz), el informe generado y la tabla de mutaciones a mano en
  `progress/impl_F-036.md`

## Bloque 14 · La migración ante un catálogo de Sigrid que ha cambiado (añadido en la undécima enmienda del 2026-10-03)

> Decisión del humano tras la verificación MANUAL T29 del 2026-10-03.
> R97 (enmendado), R128–R131 (`requirements.md` §19); `design.md` §10.5. El
> bloque va **antes** de la review 10, de la T28 otra vez y de los pasos 4–7
> de T29. Un solo encargo al implementer, T61–T64. Solo cambian
> `services/postventa-api/scripts/migracion_f036.py` y una línea de
> `services/postventa-api/scripts/migrar_excel_f036.py`, con sus tests en
> `tests/test_f036_migracion.py`: **ni** la interfaz de la línea de órdenes,
> **ni** `scripts/migracion_f036_correcciones.yaml`, **ni**
> `tests/test_f036_migracion_contenido.py`, ni el generador, el lector, el
> dominio, el importador, `infra/` o el front. No se redespliega nada. **No
> se regenera** `progress/migracion_F-036.md`: lo hace T28 con el catálogo
> del día. Base de comparación: **`b56a718`** (HEAD al escribir esta
> enmienda; la enmienda solo toca `specs/` y `progress/current.md`, así que
> producción es la misma).

- [x] **T61**: **fase RED.** En `tests/test_f036_migracion.py`, los tests de
  `design.md` §10.5, «Cómo se prueba» (R97, R128–R131), con el catálogo de
  prueba `CATALOGO_SIGRID` (el `CATALOGO` de siempre con `oficios_catalogo`
  lleno; `CATALOGO` sigue con la lista vacía). Cambian a propósito **solo**
  `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para` (el
  mensaje nuevo de la errata) y `test_f036_r58_recuentos_sin_grupos` (el
  campo nuevo de `Recuentos`), más los casos nuevos del `parametrize` de
  `test_f036_catalogo_mal_formado`; si otro test compara `Recuentos` o
  `FilaCompuesta` enteros, se dice en el informe. Decir en el informe qué
  tests nacen en verde y por qué (p. ej. R129 con dos catálogos, que ya
  cumple el código de hoy: es un invariante, no una regresión). |
  Verificación: `pytest tests/test_f036_migracion.py` con los nuevos y los
  cambiados en rojo (salvo los que el informe justifique en verde) y todo lo
  demás en verde; salida real en `progress/impl_F-036.md`, «Bloque 14»
- [x] **T62**: **el cambio** (`design.md` §10.5, «Qué cambia, y dónde»): en
  `scripts/migracion_f036.py`, `nombres_de_sigrid` nueva, el orden de
  decisión de `componer` con el parámetro `nombres_sigrid`, el mensaje nuevo
  de la errata, `FilaCompuesta.oficio_fuera_de_la_obra`,
  `Recuentos.oficios_fuera_de_la_obra`, el informe (fila de recuento,
  sección, texto de la fila) y los docstrings; en
  `scripts/migrar_excel_f036.py`, la línea del resumen y el docstring. |
  Verificación: `pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py`
  en verde; y `git diff b56a718 --stat -- services/postventa-api` solo con
  esos dos scripts y `tests/test_f036_migracion.py`
- [x] **T63**: **informe de implementación** en `progress/impl_F-036.md`,
  «Bloque 14»: qué cambió, la salida real de T61 (RED) y de T62 (verde), los
  tests que cambiaron a propósito, y un **ensayo en seco** con los JSON del
  catálogo que haya fuera del repositorio, **sin leer Sigrid**: la orden de
  T28 con `--solo-informe`, `--salida` e `--informe` a ficheros del
  scratchpad, **nunca** a `progress/migracion_F-036.md` ni al OneDrive,
  anotando solo los recuentos (sin nombres de proveedor). Con el JSON del
  2026-09-29, la fila de recuento nueva sale con **0** y los demás
  recuentos, iguales a los del informe aceptado; con el del 2026-10-03, si
  está, el script **termina** y la fila nueva sale con al menos 2 (las dos
  filas de «V-Aire acondicionado»). Sin alguno de esos JSON a mano, se dice
  y se salta esa parte. |
  Verificación: el informe en `progress/impl_F-036.md` y `git status` sin
  ningún `.xlsx` ni cambio en `progress/migracion_F-036.md`
- [x] **T64**: campaña de mutación con `--base b56a718`, **solo** sobre lo
  que cambia en producción en este bloque (los dos scripts de la
  migración), y su informe (`progress/mutacion_F-036_bloque14.md`), con
  cero supervivientes sin cerrar o sin justificación. Mutaciones a mano que
  tienen que caer (en copias desechables, nunca en el árbol), además de las
  de la herramienta: mirar `nombres_sigrid` **antes** que la obra; quitar el
  recorte de los nombres de `oficios_catalogo`; recortar el nombre de la
  tabla antes de compararlo; dejar vacía también la errata (quitar su
  parada); volver a parar en el oficio que ha salido; escribir en `Oficio`
  el nombre de la tabla en vez de dejarlo vacío; calcular el proveedor de
  R91 en la fila sin oficio; aceptar un JSON sin `oficios_catalogo`
  (`.get(..., [])`); contar en el recuento también las filas a las que la
  tabla no pone oficio; sacar la sección siempre, o nunca; quitar la línea
  del resumen de la línea de órdenes. |
  Verificación: `python -m harness.mutacion --feature F-036 --base b56a718 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque14.md`
  (desde la raíz), el informe generado y la tabla de mutaciones a mano en
  `progress/impl_F-036.md`

## Bloque 9 · Documentación, despliegue, `v2` definitivo y cierre

- [x] **T26**: `docs/ARCHITECTURE.md` (sección «Entrada de incidencias
  (F-036)», con el Excel de errores y la agrupación de oficios, y filas de
  `sigrid-api` y PostgreSQL), `docs/INTEGRACION.md` (§1, §2, §7, §8) y su copia
  en `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  (cabecera con rama y commit de origen; commit **local** en `azure-apps`, sin
  push). Tests `tests/test_f036_documentacion.py` (R60, R61) y los de
  documentación existentes que apliquen. |
  Verificación: `pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py`
- [x] **T27 · MANUAL (humano)**: desplegar la rama en el entorno que el humano
  decida (backend con `infra\desplegar_backend.ps1` —las dependencias nuevas se
  instalan en la compilación remota— y front con `infra\desplegar_front.ps1`);
  en `oficios.html`, obra 0677, revisar las propuestas de oficios y confirmar o
  rechazar cada una (anotar solo cuántas); y pulsar «Descargar los grupos
  vigentes» y guardar el JSON **fuera** del repositorio. |
  Verificación: MANUAL (humano)

  > **Quinta enmienda del 2026-09-29.** Ya no se confirman proveedores (F-050).

  > **Décima enmienda del 2026-10-02 · errata y aviso.** (1) *Errata*: el
  > front se despliega con **`infra\desplegar_front.ps1 -SoloFront`**. Sin
  > ese parámetro el script **regenera el secreto** de la Static Web App,
  > además de publicar: no hay que lanzarlo «a secas». (2) T27 la hizo el
  > humano el 2026-10-02, **antes** del Bloque 12. Tras el Bloque 12 hay que
  > **redesplegar el backend** (`infra\desplegar_backend.ps1`) para que la
  > plantilla y el Excel de errores del entorno salgan con el formato nuevo;
  > el front no cambia y no hace falta volver a publicarlo, ni repetir la
  > confirmación de oficios ni la descarga de los grupos.

  > **Enmienda 10 bis del 2026-10-02.** El redespliegue del backend se hace
  > tras el **Bloque 13** y la review 8 (no tras el 12): es el generador del
  > Bloque 13 el que tiene que salir en el entorno. Lo demás, igual.
- [x] **T28 · MANUAL (humano)**: desde `services/postventa-api`,
  `.venv\Scripts\python.exe scripts\migrar_excel_f036.py --original "C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\creacion_incidencias.xlsx" --catalogo "<JSON de T2>" --correcciones scripts\migracion_f036_correcciones.yaml --grupos "<JSON de grupos de T27>" --salida "C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\creacion_incidencias_v2.xlsx" --informe ..\..\progress\migracion_F-036.md`.
  Comprobar: el script termina con «0 errores» y el mismo `sha256` del original
  antes y después; `v2` junto al original; al abrirlo en Excel, los
  desplegables de Unidad, Ubicación, Oficio (**una entrada por oficio real**),
  Proveedor, Urgencia y Listado funcionan y no dejan escribir otra cosa, la
  cabecera y la columna `Errores` no se dejan editar, «Instrucciones» se
  entiende sin ayuda, las filas son las del informe aprobado (y si el informe
  regenerado con grupos difiere del aprobado en T25, parar y enseñarlo); si D-16
  fue el desplegable dependiente, probarlo también en Excel en la web y en
  LibreOffice; `git status` no enseña ningún `.xlsx`; *(sexta enmienda)* el
  informe regenerado no lleva ningún código de proveedor
  (`git diff progress/migracion_F-036.md`), y con la columna `Errores`
  bloqueada siguen funcionando «borrar fila» y «ordenar» (B3-4). Anotar el
  resultado en `progress/impl_F-036.md`. |
  Verificación: MANUAL (humano)

  > **Décima enmienda del 2026-10-02 · hay que REPETIRLA.** El humano la
  > ejecutó el 2026-10-02 con el generador sin formato (informe aceptado en
  > `07bd0c9`). Tras el Bloque 12, **se repite entera, antes de T29**, con la
  > misma orden: el `v2` tiene que salir con el formato nuevo, porque es el
  > que se importa en T29. Además de lo de arriba, comprobar al abrirlo: la
  > cabecera burdeos con la de `Errores` en gris, las bandas alternas, que
  > siguen bien tras **ordenar** por una columna, la columna `Errores` en
  > gris y sin poder editarse y «Instrucciones» con todos los párrafos
  > enteros (ninguno cortado). *(Enmienda 10 bis: fuera la comprobación de
  > la vista previa de impresión; el Excel no se imprime.)* El informe
  > regenerado tiene que ser **igual** que el aceptado (las mismas filas: el
  > formato no cambia el contenido); si difiere, parar y enseñarlo.

  > **Enmienda 10 bis del 2026-10-02.** Se repite con el backend
  > redesplegado tras el **Bloque 13** (y después de la muestra de T59, que
  > el humano ya habrá visto). Al abrir el `v2`, comprobar además: sus filas
  > tienen líneas y bandas y **debajo de la última no hay nada** (ni líneas,
  > ni gris en `Errores`); al escribir algo en la primera fila vacía, esa
  > fila **se pinta** entera (líneas, gris de `Errores` y, si es impar,
  > banda), y al borrarlo vuelve a quedar en blanco. Y descargar del entorno
  > (`importar.html`) una **plantilla vacía** de la 0677 y abrirla: enseña
  > la cabecera y **una sola fila** (la 2); al escribir en la 3, la 3 se
  > pinta; los desplegables y el bloqueo de `Errores` funcionan también en
  > las filas que aún no se ven (por ejemplo, en la 50). En Excel de
  > escritorio y en Excel web; LibreOffice puede pintar distinto los bordes
  > (riesgo aceptado). **Ninguna** comprobación de impresión.

  > **Undécima enmienda del 2026-10-03 · hay que REPETIRLA otra vez, con el
  > catálogo leído en el momento** (R131; `design.md` §10.1 y §10.5). Tras el
  > Bloque 14 y la review 10. La lanza el guion del líder (fuera del
  > repositorio), en este orden y **el mismo día, seguido**:
  > 1. **Grupos, justo antes**: en `oficios.html` del entorno, obra 0677,
  >    «Descargar los grupos vigentes» a un JSON **fuera** del repositorio.
  >    Han entrado oficios nuevos en la obra: si la pantalla enseña
  >    propuestas nuevas, el humano decide si las revisa antes de descargar;
  >    lo que no confirme queda como su propio grupo, que es correcto (R80).
  > 2. **Catálogo, justo antes**: desde la raíz,
  >    `powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson "<fuera del repo, con la fecha del día en el nombre>"`
  >    (con los mismos parámetros de conexión que en T2, si hacen falta;
  >    `progress/explore_F-036.md`). **Nunca** el JSON del 2026-09-29 ni
  >    otro guardado: si el `.ps1` falla, no se migra.
  > 3. **Migración**: la orden de arriba con `--catalogo` el JSON del paso 2,
  >    `--grupos` el del paso 1 y **`--sobrescribir`** (el `v2` anterior se
  >    reemplaza).
  >
  > Comprobar: el script **termina** («0 errores» en la ida y vuelta) y el
  > `sha256` del original es el mismo antes y después; la línea «Filas sin
  > oficio porque ese oficio ya no está en la obra en Sigrid: N» (se esperan
  > al menos las dos filas de «V-Aire acondicionado»); el informe regenerado
  > **difiere** del aceptado y el humano lo tiene que **aceptar
  > expresamente** (anotado en `progress/current.md`). Diferencias
  > esperables, y solo estas: (a) la fila de recuento nueva y la sección de
  > filas sin oficio (R130). *(R10-3, opción (a), decidida por el humano el
  > 2026-10-03: la sección no se acepta en bloque.)* Antes de aceptarla, el
  > líder comprueba **a mano** cada nombre de esa sección contra los oficios
  > **de la obra** del catálogo del día (`oficios_obra` del JSON del paso 2,
  > **no** `auxofc`: todo nombre de la sección está en `auxofc` por
  > definición, así que mirar ahí no detecta nada), buscando un gemelo que
  > solo difiera en tildes, mayúsculas, blancos o puntuación (p. ej. «V
  > Pintura» frente a «V-Pintura»). Si lo hay, no ha salido de la obra: es
  > una errata de la tabla, se corrige
  > `scripts\migracion_f036_correcciones.yaml` y se vuelve a lanzar la
  > migración antes de aceptar el informe; (b) etiquetas de grupo que cambian porque el
  > grupo tiene otros códigos en la obra (R86; p. ej. «Fontanería» frente a
  > «Fontaneria»), y el recuento de filas con un grupo de varios códigos;
  > (c) proveedores completados que cambian por R91 con el catálogo nuevo,
  > y su recuento; (d) el recuento de oficios de la muestra que no son
  > exactamente de la obra. Cualquier otra diferencia —textos, ubicaciones,
  > urgencias, número de filas nuevas, separadas o descartadas— o una
  > **parada** por errata: parar y volver al spec-author. Además: ningún
  > código de proveedor en el informe (`git diff progress/migracion_F-036.md`)
  > y `git status` sin ningún `.xlsx`. El aspecto no hace falta revisarlo
  > otra vez (el generador no cambia); basta abrir el `v2` y ver que el
  > desplegable de `Oficio` enseña los oficios del día. Anotar en
  > `progress/impl_F-036.md`, sin nombres de proveedor, la fecha del
  > catálogo y los recuentos.
- [x] **T29 · MANUAL (humano)**, en el entorno desplegado en T27
  *(décima enmienda: con el backend **redesplegado** tras el Bloque 12 y el
  `v2` de la T28 **repetida**; en el paso 5, comprobar además que las celdas
  con error del Excel de errores salen en rojo suave con el texto en rojo y
  su comentario, y que una **plantilla descargada antes del redespliegue**,
  con el formato antiguo, se importa igual)*
  *(enmienda 10 bis: el backend, redesplegado tras el **Bloque 13**; en el
  paso 5, el Excel de errores enseña solo sus filas, con líneas y el gris de
  `Errores` y sin bandas, y nada debajo; ninguna comprobación de impresión)*:
  1. `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677` y anotar el nº de reclamaciones por unidad (**antes**);
  2. en `importar.html`, descargar la plantilla de la 0677: salen sus unidades, un oficio por grupo confirmado y los pares oficio · proveedor de `obrofc` (ninguno para `0133`, `0144` y `0166`);
  3. importar el **original** `creacion_incidencias.xlsx`: rechazo `formato_antiguo` con su mensaje y sin Excel de errores;
  4. importar `creacion_incidencias_v2.xlsx`: 200, `completa`; anotar el tiempo de respuesta (< 10 s);
  5. en una copia del `v2`, estropear tres filas (una unidad tecleada en minúsculas, un proveedor de otro oficio, una descripción de 200 caracteres) e importarla: `parcial`, 3 con error; descargar el Excel de errores, comprobar que trae solo esas tres filas, marcadas y explicadas, con los desplegables; corregirlo e importarlo: 3 nuevas;
  6. importar el `v2` otra vez: `ya_importado`; abrirlo y guardarlo en Excel sin cambios e importarlo: 0 nuevas, todas `ya_en_bandeja`;
  7. la bandeja de la 0677 enseña las filas con las duplicadas y los oficios ambiguos marcados;
  8. repetir el paso 1 (**después**): los recuentos no han cambiado;
  8 bis. *(octava enmienda)* **comprobar en Azure que el tope de memoria del hijo se aplica**: (a) `az functionapp show -g rg-postventa-dev -n func-postventa-dev --query "functionAppConfig.scaleAndConcurrency.instanceMemoryMB"` da 2048; (b) tras una importación, en Application Insights la línea del lector aislado dice que el tope de memoria **se aplicó** y cuánto tardó el hijo (sin contenido); (c) subir uno de los ficheros de R4-1 (T39): `fichero_sospechoso` en unos 30 s como mucho, sin 5xx, y la instancia sigue viva (la siguiente petición responde sin arranque en frío); (d) anotar la memoria del proceso de la Function (padre) en reposo, para cerrar la cuenta de §5.2 («¿Cabe en la instancia?»). Si algo de esto falla, parar y volver al spec-author;
  9. *(sexta enmienda)* subir una copia del `v2` con una celda con formato en la fila 1.048.576 de «Incidencias» y anotar el tiempo de respuesta (debe ser como el del paso 4); *(sexta enmienda bis)* y otra copia con las celdas `A1003:A1048576` de «Incidencias» **combinadas** (en Excel: seleccionar el rango y «Combinar celdas»): la respuesta tiene que ser inmediata y la lectura normal, porque el libro se abre en solo lectura; nunca un minuto de espera ni un 5xx; *(séptima enmienda)* el caso de los **estilos**: subir el fichero de la review 3 con 4,1 millones de `<xf/>` en `styles.xml` (el que construyó el reviewer; o uno igual hecho con su guion): rechazo `fichero_sospechoso` al momento, nunca un minuto ni un 5xx; y **medir el `v2` guardado desde Excel** frente al presupuesto: `.venv\Scripts\python.exe scripts\contar_elementos_xml_f036.py "<ruta del v2>"` desde `services/postventa-api`, anotando el total (tiene que quedar por debajo de 60.000, un quinto del presupuesto de 300.000; *séptima enmienda bis: decía 40.000, un quinto de 200.000*; si no, parar y volver al spec-author); y en el paso 2, comprobar que las dos lecturas de Sigrid funcionan tal cual contra el ERP (el `LEFT JOIN` de B4-1 y el `obride` como texto de B4-2), que la review marca como no ensayadas.
  Anotar en `progress/impl_F-036.md`, sin nombres. |
  Verificación: MANUAL (humano)

  > **Quinta enmienda del 2026-09-29.** Sale el paso 7 bis (caso B, a F-039) y
  > los proveedores ambiguos del paso 7.

  > **Undécima enmienda del 2026-10-03 · pasos 4–7 otra vez.** El 2026-10-03
  > el paso 4 dio `parcial` con 14 filas en error (más una fila de prueba
  > del humano): el `v2` llevaba el catálogo del 2026-09-29 y Sigrid había
  > cambiado. El importador hizo lo correcto. **La bandeja no se toca**
  > (decisión del humano): las filas importadas entonces se quedan; las
  > versiones viejas se descartarán con F-038. Con el `v2` de la T28
  > repetida tras el Bloque 14, se repiten los pasos 4–7; los demás, como
  > estén anotados en `progress/impl_F-036.md` (los que falten, se hacen):
  > 4. importar el `v2` nuevo: 200 y **0 filas con error**, sin Excel de
  >    errores. **Por decisión del humano se da por bueno así** aunque no
  >    sea el resultado del paso 4 original: las filas que ya entraron el
  >    2026-10-03 (unas 144) tienen la misma clave (R35; ni el oficio ni el
  >    proveedor cuentan, R77) y salen `ya_en_bandeja`, no `nueva`; solo
  >    entran como `nueva` las que entonces dieron error. Con 0 errores el
  >    `estado` es `completa` (R42, R43: `parcial` es solo con filas con
  >    error); si saliera `parcial`, hay errores: parar y volver al
  >    spec-author. Anotar el tiempo de respuesta (< 10 s) y los recuentos
  >    (`nuevas`, `ya_en_bandeja`, `con_error`);
  > 5. igual que arriba; al importar el Excel de errores corregido, el
  >    criterio es **0 errores** y las 3 filas contadas entre `nueva` y
  >    `ya_en_bandeja` (una fila que, corregida, vuelve a tener la clave de
  >    una ya importada sale `ya_en_bandeja`, R38);
  > 6. igual que arriba: el `v2` otra vez da `ya_importado` (el paso 4 fue
  >    `completa`, R39), y guardado desde Excel sin cambios, 0 nuevas, todas
  >    `ya_en_bandeja`;
  > 7. igual que arriba; además, las filas que entraron en el paso 4 sin
  >    oficio por R128 salen sin oficio y sin proveedor, y las de antes
  >    siguen con el oficio del catálogo viejo (esperado; F-038).
- [x] **T30**: ejecutar `bash harness/init.sh` en verde (tests, cobertura de las
  líneas cambiadas ≥ 80 % y campaña de mutación con cero supervivientes sin
  justificación aceptada). |
  Verificación: `bash harness/init.sh`
