<!-- specs/F-071-plantilla-desde-sigrid/tasks.md -->
# F-071 · La plantilla de incidencias saca todos sus desplegables de Sigrid al descargarla — Tareas

> **APROBADA POR EL HUMANO el 2026-11-05** (respuestas a Q-1..Q-13 en
> `design.md` §13.1 y `progress/spec_F-071.md`; D-1 pendiente de T0). Rama `feature/F-071-plantilla-desde-sigrid`
> (worktree `postventa-f071`). Rigor **`critico`**, prioridad 1.
>
> **Base fija: `dev` `ed935ad`** (el líder rebasó la rama el 2026-11-05,
> Q-13). El implementer la anota en `progress/impl_F-071.md` al empezar el
> Bloque 1. La usan `test_f071_alcance_cerrado.py` y la mutación.
>
> RED con la traza **pegada** en `progress/impl_F-071.md`; cobertura de las
> líneas cambiadas ≥ umbral de `init.sh`; **cero supervivientes** sin
> justificación aceptada por escrito por el humano. Un commit por tarea,
> `F-071 Tn: …`. **Un bloque por encargo**, y parar; review tras cada uno.
>
> Nunca desde esta rama: escribir en Sigrid (solo `sql/read`, y solo el
> servicio desplegado), DDL, tocar `.env`, versionar `.xlsx` (tampoco los
> prototipos), subir nada al SharePoint de Posventa, ni meter en tests,
> informes o commits ubicaciones, unidades, oficios, proveedores o correos
> reales (ficticios: obras `99NN`, «Vivienda N», «Estancia A-NN», «Oficio
> ficticio N»). **No se toca** `services/postventa-front/`, la revisión, el
> volcado, las equivalencias ni `infrastructure/sigrid/**` (`design.md` §3.4).
>
> `pytest` desde `services/postventa-api` con `.venv/Scripts/python.exe -m
> pytest …`. Mutación: `python -m harness.mutacion --feature F-071 --base
> ed935ad --timeout 1800` (el Bloque 1 escribe
> `progress/mutacion_F-071.md`; los demás, `--salida
> progress/mutacion_F-071_bloqueN.md`).

## Bloque 0 · La prueba del desplegable dependiente y la base (sin código)

- [x] **T0 · MANUAL (humano)** (confirmado por el humano, Q-1 2026-11-05; hecho el 2026-11-05: escritorio por el líder con COM, **D-1 = a1** decidido por el humano; Excel web opcional, no hecho):
  abrir los dos prototipos que F-058 dejó fuera
  del repositorio, `C:\Users\pgris\Downloads\f058_prototipos\prototipo_f058_a1.xlsx`
  y `prototipo_f058_a2.xlsx` (datos ficticios), en **Excel de escritorio** y en
  **Excel web** (subidos al OneDrive **personal**, nunca al SharePoint de
  Posventa), y recorrer los **nueve puntos** de la guía de
  `progress/impl_F-058.md` de la rama `feature/F-058-plantilla-ubicaciones-sigrid`
  («T1 · Guía para el humano»; se ve con
  `git show feature/F-058-plantilla-ubicaciones-sigrid:progress/impl_F-058.md`).
  Anotar la tabla programa × variante × punto (sí/no y una nota, sin datos
  reales) en `progress/impl_F-071.md` y la decisión **D-1**: a1, a2 o ninguna.
  Anotar aparte el punto 3/4 (si Excel acepta lo tecleado con la lista vacía,
  `design.md` §4.2). Borrar los prototipos del OneDrive al acabar. |
  Verificación: MANUAL (humano) — la tabla y la decisión en `progress/impl_F-071.md`
- [x] **T0 bis · líder** (hecho el 2026-11-05): rama rebasada sobre `dev`
  `ed935ad` (base fija) y F-040 aparcada (`blocked`, sin fallo); commit
  `e103d70`. |
  Verificación: `bash harness/init.sh` en verde (lo ejecuta el líder; el worktree aún no tiene venv)

**Parar. Si D-1 = ninguna, volver al humano con la opción (c) antes de seguir.**

## Bloque 1 · El dominio

> Es el bloque más grande. Si el encargo se cuelga, el líder lo parte en dos
> encargos: T1 (RED) y T2–T3 (GREEN y mutación). No se parte por fichero: quitar
> `ubicaciones` de `ListasCerradas` rompe a la vez la plantilla y la
> importación.

- [x] **T1 · RED** (hecha el 2026-11-05, traza en `progress/impl_F-071.md`): `tests/test_f071_casado_con_lista.py`,
  `tests/test_f071_dominio_opciones.py` y `tests/test_f071_dominio_importacion.py`
  contra lo que aún no existe (`design.md` §5):
  - casado (§5.5): `casado_con_lista` expone `Coincidencia`,
    `UbicacionDeSigrid`, `clave_de_ubicacion`, `ubicacion_de_sigrid` y
    `normalizacion` sigue exponiendo **los mismos objetos** (`is`);
    `casar_con_lista` exacta, única por clave, dos por clave → `None`,
    ninguna → `None`, recorte y NFC;
  - opciones (§5.1, §5.2): R12 (un código por entrada, por código, sin grupos
    aunque haya `GruposVigentes` con «mismo»), R13 (con y sin nombre,
    recortado), R14 (par por fila distinta, sin proveedor no da par, oficio
    fuera no da par, orden, sin nombre), R15 (`ValueError`), R8
    (`ubicaciones_de_la_plantilla`: tupla exacta, orden por código,
    determinista con las unidades barajadas, vacía o sin entrada → `None`,
    unidad ajena ignorada, `ValueError` sin el texto con una vacía, con
    blancos o de 49; `union()`), R17 (`VERSION_PLANTILLA == 2`,
    `VERSIONES_SOPORTADAS == {2}`), R22 (`ListasCerradas` sin `ubicaciones`);
  - importación: R23 (v1 → `version_anterior` con su texto; 0 y 3 →
    `version_no_soportada`; v2 sí), R26–R31 (con la unión, las dos ramas),
    R32–R35 (nombre de Sigrid guardado, no la etiqueta; par sin oficio; par
    de otro oficio; **ninguna** combinación de una obra ficticia con oficios
    de nombre repetido y un proveedor en dos oficios da ambiguo), R36 (en las
    cinco columnas, con aviso; dos por clave → error), R37 (texto de «ya no
    está en Sigrid»), R38, R39 (orden de errores), R41 (clave igual con otra
    mayúscula).
  Cada test `test_f071_rN_…`. Traza RED pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_casado_con_lista.py tests/test_f071_dominio_opciones.py tests/test_f071_dominio_importacion.py` en rojo por `ImportError`/aserción, nunca por sintaxis
- [ ] **T2 · GREEN**: `domain/models/casado_con_lista.py` (lo movido sin
  cambiar una letra y `casar_con_lista`), `normalizacion.py` (solo imports),
  `plantilla_incidencias.py`, `importacion.py`, `errores.py`
  (`version_anterior`). Adaptar los tests de dominio de F-036, F-056 y F-060
  que cambien, **citando** en `progress/impl_F-071.md` cada aserción cambiada
  y el R que la sustituye. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_casado_con_lista.py tests/test_f071_dominio_opciones.py tests/test_f071_dominio_importacion.py tests/test_f036_plantilla_dominio.py tests/test_f036_importacion_dominio.py tests/test_f060_*` en verde
- [ ] **T3 · mutación del bloque**: `python -m harness.mutacion --feature F-071
  --base ed935ad --timeout 1800` sobre lo del bloque; matar los
  supervivientes con tests nuevos o justificarlos uno a uno. |
  Verificación: `progress/mutacion_F-071.md` con 0 supervivientes sin justificación

**Parar. Review del Bloque 1.**

## Bloque 2 · El generador y la configuración

- [ ] **T4 · RED**: `tests/test_f071_generador.py` (sobre el `.xlsx`
  generado y abierto con `openpyxl`: R5–R7 con la fórmula elegida en D-1,
  `sqref` `B2:B1001`, `allowBlank`, estilo «detener»; R8, R9 —nombres,
  tabla, `ubicaciones_ninguna`, sin `lista_ubicaciones`, texto que empieza
  por `=`—; R10 ≤ 255; R11; R13–R15 en `lista_oficios` y
  `lista_proveedores`; R17 versión 2 en `_plantilla`; R19; R20 obra grande
  generada y leída por `LectorPlantillaOpenpyxl` y reconocida; R40 Excel de
  errores v2 con las filas tal cual) y `tests/test_f071_configuracion.py`
  (R16 urgencias y listados del YAML real; R18 mensajes e instrucciones ≤ 255
  y sin «General»/«Otra»/«en la revisión»; R21 YAML con `ubicaciones` en
  `tmp_path` → `ConfiguracionPlantillaInvalida`). Traza RED pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_generador.py tests/test_f071_configuracion.py` en rojo por aserción
- [ ] **T5 · GREEN**: `domain/ports/hoja_calculo.py` (firma),
  `infrastructure/documentos/excel_openpyxl.py`,
  `infrastructure/documentos/plantilla_yaml.py`,
  `config/plantilla_incidencias.yaml` (`design.md` §7). Adaptar
  `test_f036_excel_generador.py`, `test_f036_excel_lector.py`,
  `test_f036_configuracion_plantilla.py`, `tests/utiles_plantilla.py` con
  citas. Medir con `scripts/contar_elementos_xml_f036.py` la plantilla de
  R20 y anotar el número. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_generador.py tests/test_f071_configuracion.py tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_configuracion_plantilla.py` en verde
- [ ] **T6 · mutación del bloque**: como T3, `--salida
  progress/mutacion_F-071_bloque2.md`. |
  Verificación: el informe con 0 supervivientes sin justificación

**Parar. Review del Bloque 2.**

## Bloque 3 · Aplicación y bordes

- [ ] **T7 · RED**: `tests/test_f071_pipelines.py` (R1 orden catálogo →
  ubicaciones, una lectura cada una, sin `EquivalenciasPort`; R2; R3 y R25
  techo → 409 y fallo → 503 sin fichero ni registro; R24 sin lecturas con
  `ya_importado` ni con un fichero no reconocido, ni con una v1; R40 sin
  segunda lectura; R44 con `caplog`: ni ubicaciones ni nombres, solo
  recuentos) y `tests/test_f071_http.py` (`descargar_plantilla` sin
  `equivalencias` y con `ubicaciones=` inyectable; `importar_excel` con la
  fuente construida solo tras reconocer; `version_anterior` → 400 con su
  motivo; el borde usa `construir_fuente_de_ubicaciones` de
  `interface_adapters/api/revision.py`). Traza RED pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_pipelines.py tests/test_f071_http.py` en rojo por aserción
- [ ] **T8 · GREEN**: `application/pipelines/plantilla.py`,
  `contexto_importacion.py`, `paso_importacion.py`,
  `interface_adapters/api/plantilla.py`, `interface_adapters/api/importar.py`
  y, si hace falta, el docstring de la ruta en `function_app.py`
  (`design.md` §6). Adaptar `test_f036_pipeline_importacion.py`,
  `test_f036_plantilla_http.py`, `test_f036_importar_http.py`,
  `tests/utiles_revision.py` con citas. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_pipelines.py tests/test_f071_http.py tests/test_f036_pipeline_importacion.py tests/test_f036_plantilla_http.py tests/test_f036_importar_http.py` en verde
- [ ] **T10 · mutación del bloque**: como T3, `--salida
  progress/mutacion_F-071_bloque3.md`. |
  Verificación: el informe con 0 supervivientes sin justificación

**Parar. Review del Bloque 3.**

## Bloque 4 · Documentos, alcance y cierre del código

- [ ] **T9** (movida aquí desde el Bloque 3 para que cada encargo sea pequeño):
  retirar el script de migración y sus tests (`design.md` §3.3, R45, Q-9) y
  las menciones que los exijan (`test_f036_arquitectura.py`,
  `test_f036_documentacion.py` si los nombran). |
  Verificación: `.venv/Scripts/python.exe -m pytest` del servicio entero en verde
- [ ] **T11**: `docs/ARCHITECTURE.md` y `docs/INTEGRACION.md` (`design.md`
  §12), `tests/test_f071_documentacion.py` (R46) y
  `tests/test_f071_alcance_cerrado.py` (R42, R43, R45: con la base fija, ni un
  fichero de `infrastructure/sigrid/`, `infrastructure/persistencia/`, la
  revisión, el volcado, las equivalencias ni `services/postventa-front/`
  cambiado; ningún `.sql` nuevo; ninguna dependencia nueva; las consultas de
  Sigrid iguales carácter a carácter). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f071_documentacion.py tests/test_f071_alcance_cerrado.py` en verde
- [ ] **T12**: `bash harness/init.sh` en verde con la puerta de cobertura en
  `[OK]`, y la campaña de mutación de la feature entera sin supervivientes
  sin justificar. Informe en `progress/impl_F-071.md`. **Review final.** |
  Verificación: `bash harness/init.sh` en verde; `progress/mutacion_F-071.md` al día

**Parar. Review final APPROVED antes del Bloque 5.**

## Bloque 5 · Despliegue y verificación en producción

- [ ] **T13 · líder**: merge normal de la rama a `dev` **desde un worktree
  aparte** (la rama ya está sobre `dev`, T0 bis; R-6 resuelto). El push, el
  humano. |
  Verificación: `git log dev` con el merge; `bash harness/init.sh` en verde en `dev`
- [ ] **T14 · MANUAL (humano)**: publicar el backend desde una copia limpia de
  `dev`, en la raíz del repositorio principal:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
  git worktree remove ..\postventa-publicar
  ```
  Anotar el commit publicado en `progress/impl_F-071.md`. Si algo que antes
  funcionaba falla, volver a publicar el commit anterior con el mismo
  mecanismo. |
  Verificación: MANUAL (humano) — el commit publicado anotado
- [ ] **T15 · líder**: poner al día
  `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` (R46:
  la lectura de ubicaciones también en la plantilla; la plantilla ya no lee
  PostgreSQL; la lista del YAML y los grupos fuera de la plantilla), commit
  local en `azure-apps`. |
  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1`
- [ ] **T16 · MANUAL (humano)**: verificación en producción, obra **0677**
  (R47), sin datos personales en las notas:
  1. Desde `importar.html`, descargar la plantilla de la 0677. Abrirla en
     Excel. En la fila 2 elegir una unidad; en la 3, otra de **otra
     tipología**: los desplegables de `Ubicación` son distintos. Fila 4 sin
     unidad: no ofrece nada. Ni «General» ni «Otra» en ningún desplegable.
  2. Abrir `bandeja.html?obra=0677`, herramientas de desarrollo → Red → la
     respuesta de `/api/revision`: `catalogo.ubicaciones` de esas dos unidades
     tiene tantas entradas como su desplegable; `catalogo.oficios` tiene
     tantas entradas como el desplegable de `Oficio`, cada una con su código.
  3. **Autorizado por el humano el 2026-11-05 (Q-10)**; nada en Sigrid: en la plantilla, dos filas con
     «PRUEBA F-071 - DESCARTAR» en `Descripción corta`: la A con una
     ubicación **pegada** de otra unidad (pegar se salta la validación); la B
     con ubicación, `Oficio` y `Proveedor` del desplegable. Importar: la
     respuesta es `parcial`, la A vuelve en el Excel de errores con
     «esa ubicación no es de la unidad de esta fila…», la B entra con su
     código de oficio y de proveedor y **sin** «varios códigos en Sigrid».
     En la bandeja, **descartar** la B.
  4. Si el humano conserva una plantilla v1: subirla → 400 «Esta plantilla es
     de una versión anterior…», sin nada nuevo en la bandeja.
  Anotar el resultado de cada paso en `progress/impl_F-071.md`. |
  Verificación: MANUAL (humano) — los cuatro pasos anotados con su resultado real
- [ ] **T17 · líder**: `progress/history.md` (resumen), `progress/current.md`,
  F-071 a `done` en `harness/features.json` **solo con T18 en verde y la
  review final APPROVED** (regla dura de `CLAUDE.md`); F-058 ya consta como
  absorbida (Q-11, el líder el 2026-11-05): cerrar su ficha y retirar el
  worktree `postventa-f058` si el humano lo aprueba. Siguiente feature: F-072,
  luego retomar F-040 (Q-3). |
  Verificación: `python harness/backlog.py --comprobar` sin diferencias
- [ ] **T18**: Ejecutar `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
