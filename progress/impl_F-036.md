<!-- progress/impl_F-036.md -->
# F-036 · Informe del implementer

Rigor `critico` (`harness/features.json`). Rama `feature/F-036-importar-excel`.

## Bloque 0 · T1 (2026-09-28)

Encargo del líder: **solo T1**. No se ha tocado T2 (MANUAL, humano), ni T3
(PARADA), ni nada del Bloque 1 en adelante.

### Qué cambió

| Fichero | Qué |
|---|---|
| `infra/26_catalogos_plantilla_sigrid.ps1` | **Nuevo.** Script de medición de solo lectura sobre `08_lectura_sigrid_comun.ps1`. Parámetros `-CodigoObra` (obligatorio: sin él sale con código 3 antes de leer nada), `-SalidaJson`, `-MostrarNombres`, `-SinGlobal`, más `-WhatIf`, `-TimeoutS` (5–220; 110 por defecto) y `-SigridBaseUrl`/`-SigridBaseDatos` como el 24. ASCII, CRLF, sin BOM, con la ruta en la primera línea. |
| `services/postventa-api/tests/test_f036_scripts_infra.py` | **Nuevo.** 46 tests estáticos (sin red ni procesos). |
| `specs/F-036-importar-excel/tasks.md` | T1 marcada `[x]`. |
| `progress/current.md` | Estado de T1. |
| `progress/mutacion_F-036.md` | Generado por la campaña (0 mutantes: ver «Evidencias»). |

Lo que imprime el script, en el orden de `tasks.md` T1:

1. Las obras con ese código **que tienen unidades de posventa** («Obra 1», «Obra 2»),
   el nº de unidades y la forma de sus nombres con la **misma máscara** que el 24
   (copia idéntica: la exige un test). Si no hay exactamente una obra, lo dice,
   la marca en rojo en el veredicto y para sin leer nada más.
2. `obrofc` de la obra: filas, filas sin proveedor, oficios distintos, oficios de
   baja (`auxofc.fecbaj <> 0`), proveedores distintos, oficios con más de un
   proveedor y la lista `cod · res` de los oficios, con su marca de baja y cuántas
   filas y proveedores tiene cada uno.
3. Proveedores de la obra sin CIF; grupos por **CIF normalizado** (expresión de
   `design.md` §6.3, contada con `GROUP BY`, sale solo el tamaño); grupos de
   proveedores y de oficios con el mismo nombre en `COLLATE Latin1_General_CI_AI`.
4. Las 60 `rcp.resubi` más frecuentes (con total, nº de distintas y nº de
   reclamaciones sin ubicación) y los valores distintos de `upv.espacios`.
5. Familias (§16.2): proveedores con filas en `confam`, filas, homologadas, de
   baja y huérfanas; distribución de nº de familias por proveedor; cruce por
   código `auxfam.cod` = `auxofc.cod` en los catálogos enteros (en los dos, solo
   en uno, solo en otro y, de regalo, cuántas familias coinciden en código **y**
   nombre) y en las familias de los proveedores de la obra frente a sus oficios;
   filas de `obrofc` cuyo oficio está entre las familias (no de baja) del
   proveedor, las homologadas y las de proveedor sin familias; `entfam` (con
   `fampro` y con `fament`); `prv.ofcide` relleno y si es uno de los oficios con
   que figura en `obrofc`.
6. Salvo `-SinGlobal`: CIF y nombre sobre los proveedores de algún `obrofc` y
   sobre todo el maestro `prv`; nombre sobre todo `auxofc`; y el bloque de
   familias entero sobre los proveedores de algún `obrofc`. El tamaño de `auxfam`
   sale en el punto 5.
7. Con `-SalidaJson`: el JSON de §10.3 + §16.2 (ver decisiones).

### Decisiones de diseño

- **D-a · Plantillas de ámbito.** Las consultas que se repiten para la obra, para
  todos los `obrofc` y para el maestro se escriben una vez con una marca
  (`{PROVEEDORES}`, `{OFICIOS}`, `{FILAS}`) que se sustituye por un fragmento
  **fijo** de `$Fragmentos`. Nada de lo que entra por parámetro llega a un
  fragmento; solo los de obra llevan `?` y cada `?` recibe el `ide` de la obra
  (los tests fijan que las plantillas no traen `?` propios). Así la versión de la
  obra y la global son la misma consulta.
- **D-b · Solo `SELECT`, sin `WITH`.** `sigrid_api.md` §5.1: el guardia de lectura
  admite solo prefijo `SELECT`. Todo con tablas derivadas y subconsultas.
- **D-c · Lecturas tolerantes.** Salvo la de unidades (sin ella no hay obra), cada
  lectura va con `-Tolerante` del 08: si la pasarela rechaza una, se avisa, queda
  en rojo en el veredicto y siguen las demás. No lo he podido comprobar contra un
  SQL Server de verdad (ver «Lo que falta»).
- **D-d · El `ide` de la obra** sale de la lectura de unidades (`v.obride`) y
  solo se usa como parámetro. Test: cada línea que nombra `$obraIde` lo asigna o
  lo pasa a `-Parametros`.
- **D-e · Oficios, familias, ubicaciones y `espacios` salen tal cual.** Nombres de
  obra y de unidad, enmascarados salvo `-MostrarNombres`; de proveedor, **nunca**
  en consola (solo en el JSON). Oficios y familias son catálogo, no datos de
  nadie (§15.4, R110), y T2 tiene que comprobar si los de la muestra existen
  **exactamente** con ese nombre: enmascarados no serviría. `resubi` y `espacios`
  son lo que se mide; son texto libre, así que el script lo avisa en amarillo
  («revísalo antes de copiarlo a progress/, SIN nombres de persona»). **Para el
  reviewer:** si se prefiere que `resubi`/`espacios` salgan enmascarados por
  defecto, es un cambio de dos líneas, pero T2 tendría que lanzarse con
  `-MostrarNombres`.
- **D-f · El JSON.** Claves exactas de §10.3 + §16.2 (las fija un test).
  `oficios_obra` es `SQL_OFICIOS_DE_LA_OBRA` de §6.3 con un alias por columna, sin
  oficios de baja. `marca_cif` va como **texto** (`"1"`) o `null`, porque
  `Candidato.marca_cif` de §15.2 es `str | None`. `homolo` va como venga (entero).
  `oficios_catalogo` es **todo** `auxofc`, paginado con `OFFSET/FETCH` por `ide` en
  páginas de 500 (§6.4 de `sigrid_api.md`; por debajo del tope de 1.000 para que
  una página llena no se confunda con una respuesta truncada). `familias_catalogo`
  es todo `auxfam` **si cabe en una lectura** (< 1.000 filas); si no, `null`
  (la clave va siempre, para que T8 no tenga que distinguir «no está» de «no
  cabía»). Si falla cualquier lectura del JSON, no se escribe y el veredicto
  queda en rojo. Se escribe en UTF-8 sin BOM.
- **D-g · Código comparado literal**: `LTRIM(RTRIM(o.cod)) = ?` como §6.3 (el 24
  preguntaba también sin ceros; aquí manda la spec).
- **D-h · Cruce por código «tal cual»**: `fa.cod = a.cod`, con la intercalación de
  la base (probablemente sin distinguir mayúsculas; los espacios finales los
  ignora SQL Server de por sí). El cruce por nombre normalizado es de T8.

### Desviaciones respecto a la spec (justificadas)

- **Ruta del test**: `tasks.md` dice `tests/test_f036_scripts_infra.py`; vive en
  `services/postventa-api/tests/`, junto a los de F-005…F-013 de `infra/`. Es
  donde el precedente de F-013 lo puso con la misma redacción («`tests/…`» =
  la suite del servicio) y donde `init.sh` lo ejecuta; `tests/` de la raíz es la
  suite del arnés.
- **`-WhatIf` y `-TimeoutS`** no están en el encargo: `-WhatIf` es la convención de
  los scripts de medición (así se comprueba sin tocar nada) y `-TimeoutS` hace
  falta porque las lecturas globales recorren tablas enteras.

### Columnas del diccionario frente a la spec

Contrastadas contra `azure-apps/sigrid_tablas.md`: **todas existen**.
`upv` (`ide`, `obride`, `espacios` texto 255), `con` (`cod`, `res`), `obrofc`
(`obride`, `ofcide`, `prvide`), `auxofc` (`cod` 24, `res` 48, `fecbaj`), `prv`
(`cif` 24, `ofcide`), `confam` (`conide`, `famide`, `homolo`), `auxfam` (`cod`
16, `res` 48, `fecbaj`), `entfam` (`conide`, `fampro`, `fament`; en el diccionario
esas dos filas salieron descuadradas de la conversión del PDF, pero están),
`rcp` (`upvide`, `resubi` 48). No se ha usado `con.tip`: `upv` y `rcp` ya son
tablas de su tipo, y el 24 y §6.3 tampoco filtran por él.

### Lo que falta / fuera de alcance

- **El SQL no se ha ejecutado contra un SQL Server.** Los tests son estáticos y
  el ensayo fue contra un doble; si alguna consulta tiene un fallo de sintaxis o
  de intercalación, T2 lo enseñará como «lectura: … NO» en rojo sin llevarse por
  delante las demás. Sería una corrección de ese SQL, no de diseño.
- T2 (humano), T3 (PARADA) y todo el Bloque 1 en adelante: sin tocar.
- `azure-apps/`: no cambia nada de lo que el proyecto expone o consume (lecturas
  de un script local de medición, por la misma ruta `sql/read` de siempre).
- Nada del arnés que portar a `arnes-base`.

### Comando de T2 (para el humano)

Con `SIGRID_API_BASE_URL`, `SIGRID_BASE_DATOS` y `SIGRID_API_KEY` en la sesión
de PowerShell (o la clave por consola), desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson "$env:TEMP\catalogo_0677.json"
```

Antes, si se quiere ver qué haría sin llamar a nada: el mismo comando con
`-WhatIf`. El JSON queda en `%TEMP%` (fuera del repositorio: el script rechaza
cualquier ruta dentro) y lleva nombres de proveedor: guardar su ruta para T8,
T24 y T28, no copiarlo a `progress/`. Si las lecturas globales tardan demasiado,
se puede repetir con `-SinGlobal`.

### Fase RED

Test escrito antes que el script. Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f036_scripts_infra.py -q --tb=no -p no:cacheprovider
```

Salida (sin el script):

```
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF....                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_el_script_existe - Asse...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_sin_bom_como_el_resto_de_infra
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_crlf_en_todas_las_lineas
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_contenido_ascii_puro - ...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_empieza_por_su_ruta_relativa
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_se_lanza_desde_cualquier_sitio
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_carga_el_comun_de_lectura
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_los_parametros_del_encargo
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_sin_codigo_de_obra_no_pregunta_nada
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_whatif_no_llama_a_nada
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_sin_guid - FileNotFound...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_sin_host - FileNotFound...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_sin_credencial_ni_codigo_real
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_no_imprime_un_secreto
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_solo_lee_por_sql_read
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_no_ejecuta_python_ni_nada_de_fuera
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_hay_consultas_y_todas_son_select
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_las_consultas_son_literales
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_el_codigo_de_obra_solo_viaja_como_parametro
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_nunca_pide_mas_de_mil_filas
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_las_plantillas_no_llevan_parametros_propios
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_los_fragmentos_de_ambito
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_el_ide_de_la_obra_solo_va_a_los_parametros
FAILED tests/test_f036_scripts_infra.py::test_f036_r90_el_cif_solo_entra_normalizado
FAILED tests/test_f036_scripts_infra.py::test_f036_r90_la_marca_de_cif_es_la_de_design
FAILED tests/test_f036_scripts_infra.py::test_f036_r90_los_grupos_por_cif_se_cuentan_en_sql
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_ninguna_columna_devuelta_es_un_ide_salvo_la_obra
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_ninguna_linea_que_imprime_nombra_un_ide_o_un_cif
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_las_claves_del_json_son_las_de_design
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_la_mascara_es_la_del_24
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_los_nombres_de_obra_y_unidad_salen_por_la_mascara
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_los_nombres_de_proveedor_no_se_imprimen
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_unidades_de_la_obra_como_en_design
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_mide_obrofc_de_la_obra
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_nombres_parecidos_sin_mayusculas_ni_tildes
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_ubicaciones_y_espacios
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_mide_las_familias - F...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_lo_global_solo_sin_singlobal
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_el_json_no_cae_dentro_del_repositorio
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_solo_escribe_el_json - ...
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_todo_auxofc_en_el_json_paginado
FAILED tests/test_f036_scripts_infra.py::test_f036_r107_las_familias_de_los_proveedores_de_la_obra
42 failed, 4 passed in 0.12s
```

Traza de uno de ellos (`--tb=short`):

```
E   FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-incidencias\\infra\\26_catalogos_plantilla_sigrid.ps1'
FAILED tests/test_f036_scripts_infra.py::test_f036_r90_el_cif_solo_entra_normalizado
1 failed in 0.22s
```

Los 4 que pasaban en rojo son los **controles negativos** de los barridos (un
`UPDATE` inyectado, un host inventado, un `pv.cif` suelto y un `$obraIde`
impreso): prueban que el patrón salta, no dependen del script.

Ya con el script, un rojo de verdad: `test_f036_t1_los_nombres_de_proveedor_no_se_imprimen`
saltó con `'p.res' is contained here: a obra (rcp.resubi) …`. El fallo era del
test (subcadena demasiado laxa); se cambió a `\bp\.res\b` y no se tocó el
script. Verde:

```
46 passed in 0.23s
```

### Ensayo local (sin Sigrid ni red)

Contra un doble de `POST /api/sql/read` en `127.0.0.1` (en el scratchpad de la
sesión, no versionado; clave falsa), con PowerShell 5.1:

- `-WhatIf`: lista las 22 consultas y sale 0 sin llamar a nada. Sin
  `-CodigoObra`: «Falta -CodigoObra…», salida 3. `-SalidaJson "progress\x.json"`:
  «tiene que quedar fuera del repositorio», salida 3, sin fichero.
- Ejecución completa con `-SalidaJson` fuera del repo: **`PASA`**, salida 0.
  36 peticiones, todas a `/api/sql/read`, todas `SELECT`, `max_rows` ≤ 1.000 y
  en **todas** el nº de `?` igual al nº de parámetros. El `ide` de obra del doble
  (987654) aparece **0 veces** en la consola y 0 en el JSON; la unidad
  «VILLA 05 - GARCIA» sale como `VILLA 05 - <txt>`, y los nombres de proveedor, 0
  veces en consola. JSON con las 6 claves, `marca_cif` `"1"`/`null`,
  `oficios_catalogo` con las 650 filas del doble en dos páginas (0 y 500), y una
  lista de un solo elemento (`familias_proveedor`) sale como array, no como
  objeto (la trampa de `ConvertTo-Json` de PowerShell 5.1).
- `-SinGlobal -MostrarNombres`: 18 peticiones (ni globales ni JSON), nombres
  literales, `PASA`.
- El primer intento dio salida 5 («La respuesta no trae la columna marca_cif»):
  era el doble, que casaba `AS oficio_cod` también con `AS oficio_codigo`.
  Corregido el doble, no el script.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de la tarea | `tests/test_f036_scripts_infra.py`: **46 passed** en 0.23 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 5.09 s; servicio `api`: **4402 passed, 52 skipped** en 95.93 s; servicio `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-036 no cambia líneas Python de producción frente a dev)`: T1 solo añade un `.ps1` y un test |
| Mutación | `python -m harness.mutacion --feature F-036` → `progress/mutacion_F-036.md`: **0 ficheros, 0 líneas de producción, 0 mutantes, 0 supervivientes**. No hay nada que mutar: la mutación solo mide `.py` de producción, y el script es PowerShell. Lo que lo protege son los 46 tests estáticos y el ensayo local de arriba |
| Verificaciones MANUAL pendientes | T2: ejecutar el script contra Sigrid (comando arriba) |

## T1 bis (2026-09-28): tildes y actividades

Encargo del líder: corregir la doble codificación que encontró T2 y ampliar el
script con la medición de las actividades (`conact` → `auxpronat`, cuarta
enmienda). Nada más de la feature: `tasks.md`, `specs/` y `progress/current.md`
sin tocar (el spec-author los estaba editando en paralelo). Commit `1b3edfb`.

### A · Causa del defecto de codificación

- `sigrid-api` responde con `func.HttpResponse(json.dumps(..., ensure_ascii=False),
  mimetype="application/json")` (`interface_adapters/http/http_response_factory.py`).
  El worker de Python de Azure Functions solo añade `charset` a los mimetype
  `text/*` (`azure/functions/http.py`: `if obj.mimetype.startswith('text/')`),
  así que la cabecera real es **`Content-Type: application/json` sin `charset`**
  y el cuerpo lleva las tildes como bytes UTF-8.
- `Invoke-RestMethod` de PowerShell 5.1, sin `charset`, decodifica el cuerpo
  como **ISO-8859-1**: `í` (`C3 AD`) se convierte en `Ã­`, que se imprime así en
  consola y que `WriteAllText` en UTF-8 guarda como `C3 83 C2 AD`. La escritura
  del JSON (`UTF8Encoding($false)`) estaba bien; el fallo era de la lectura.
- Por qué el doble del primer ensayo no lo reprodujo: mandaba
  `application/json; charset=utf-8` y `json.dumps` con `ensure_ascii=True`
  (`í`, puro ASCII). El doble nuevo (`doble_t1bis.py`, en el scratchpad de
  la sesión, no versionado) responde como la pasarela: UTF-8 real y cabecera sin
  `charset`.
- **Corrección, en `infra/08_lectura_sigrid_comun.ps1`** (`Invoke-SigridLectura`):
  `Invoke-WebRequest -UseBasicParsing`, los bytes crudos
  (`$web.RawContentStream.ToArray()`) decodificados con
  `[Text.Encoding]::UTF8.GetString` y `ConvertFrom-Json`. A la ida, el cuerpo va
  en bytes UTF-8 con `application/json; charset=utf-8` (antes un parámetro con
  tilde salía en Latin-1). `$ProgressPreference` local a `SilentlyContinue`. Las
  ramas de error no cambian (mismo `WebException`, mismo HTTP, `-Tolerante` igual).

**Se benefician** todos los scripts que leen por el 08: `09`, `10`, `11`, `13`,
`15`, `16` (su lectura SQL; la descarga del binario es aparte y no es texto),
`20`, `24` y `26`. `12`, `17`, `21`, `23` y `25` cargan el 08 pero no llaman a
`Invoke-SigridLectura`. El `07` lee la pasarela desde Python, fuera de esto.
Sus tests (`test_f010_*`, `test_f012_*`, `test_f013_*`) siguen verdes.

### B · Medición de las actividades

En `infra/26_catalogos_plantilla_sigrid.ps1`, sección nueva «5 bis» y su
equivalente global:

- `Write-Actividades` (obra y, salvo `-SinGlobal`, todos los `obrofc`):
  proveedores con filas en `conact`, filas, actividades distintas, homologadas
  (`homolo <> 0`) y de cuántos proveedores, de actividades de baja
  (`auxpronat.fecbaj <> 0`), filas sin su actividad, y la distribución «N
  proveedores con K actividades» (`GROUP BY` en el servidor).
- `sqlArbolResumen`: filas de `auxpronat`, de baja, códigos distintos, sin
  código, longitud mínima y máxima del código, valores distintos de `pos` y
  filas con `pos` a 0/nulo.
- `auxpronat` entero, paginado (`OFFSET/FETCH` por `ide`, páginas de 500; tope
  de 20.000 filas) y `Get-ArbolActividades`: el diccionario no trae columna de
  padre, así que se deduce del código. Hipótesis por orden: **prefijo** (padre =
  el código más largo que es prefijo propio), **ceros** (solo si todos miden lo
  mismo: igual, quitando los ceros de relleno) y **ninguna** (se dice). Imprime
  la hipótesis, los separadores, niveles, códigos por nivel y las 20 **formas**
  más frecuentes (letra = `A`, cifra = `9`); si no gana «prefijo», también las
  formas **con sus ceros**, que enseñan el ancho de cada nivel.
- Actividades de los proveedores de la obra **por rama de primer nivel**
  (actividades distintas, filas, proveedores, homologadas, de baja) y cuántas
  quedan fuera del catálogo leído.
- `sqlCruceActividadesOficios`: códigos en los dos catálogos / solo en uno /
  solo en otro, y nombres iguales con `COLLATE Latin1_General_CI_AI` en los dos
  sentidos y con mismo código y nombre.
- JSON: `actividades_proveedor` (`proveedor_codigo`, `actividad_codigo`,
  `homolo`) y `actividades_catalogo` (`codigo`, `nombre`, `pos`, `fecbaj`; `null`
  si `auxpronat` pasa del tope). Lo de `confam`/`familias_*` se mantiene.
- `Read-Paginas` y `ConvertTo-Filas`: una sola forma de paginar (también la usa
  ya `oficios_catalogo`, que antes tenía su bucle propio).

### Decisiones y desviaciones (para el reviewer)

- **Nombres de actividad en consola solo con `-MostrarNombres`**, como pidió el
  líder: sin él, la rama se identifica por su número y la forma de su código.
  Es más estricto que D-e (los oficios salen literales): las actividades son
  catálogo (R110), pero el encargo lo pedía así. El JSON las lleva siempre.
- **`actividades_proveedor` trae también las actividades de baja** (el borrador
  de `design.md` §6.3 filtra `fecbaj = 0`): el encargo pide contarlas, y el
  catálogo del JSON lleva `fecbaj` para filtrarlas después.
- **El JSON no lleva `padre`** (el borrador de §16.2 lo pide «si T1 sabe
  deducirlo»): el encargo dice `cod, res, pos, fecbaj`, y la deducción de padre
  depende de una hipótesis que T2 tiene que confirmar primero. Si se confirma,
  añadirlo es una línea. **Tampoco se quita `familias_*`**, en contra de
  «sustituyen» del borrador: el encargo dice que se quede.
- **La hipótesis «ceros» es débil**: con ceros de relleno el ancho de nivel no se
  deduce seguro (en el ensayo sintético de tres niveles de dos cifras dio 4
  niveles). Por eso sale marcada «OJO» con las formas con ceros. «Prefijo», que es
  la forma que anticipa la spec (`01`, `0101`, `010101`), sale bien.
- El test `test_f036_r109_las_actividades_solo_con_mostrarnombres` saltó en rojo
  por un patrón demasiado laxo (`$textoSeparadores` acaba en «res»): se
  corrigió el patrón del test (`PATRON_NOMBRE_IMPRESO`, con su control
  negativo), no el script.
- Un fallo real que solo salió en el ensayo: `@($lista).Count` sobre un
  `List[object]` revienta en PowerShell 5.1 con «Los tipos de argumentos no
  coinciden». Se usa `.Count` directamente.

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `infra/08_lectura_sigrid_comun.ps1` | Lectura en UTF-8 (A). ASCII, CRLF, sin BOM. |
| `infra/26_catalogos_plantilla_sigrid.ps1` | Actividades (B) y ayuda. ASCII, CRLF, sin BOM. |
| `services/postventa-api/tests/test_f036_scripts_infra.py` | +21 tests (R111, R109, R107) y claves nuevas del JSON. |
| `progress/impl_F-036.md` | Esta sección. |

### Fase RED

Tests escritos antes que el código. Desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f036_scripts_infra.py -q --tb=no -p no:cacheprovider
```

```
............................F.................FFFF...FFFFFFFFFFF.        [100%]
=========================== short test summary info ===========================
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_las_claves_del_json_son_las_de_design
FAILED tests/test_f036_scripts_infra.py::test_f036_r111_el_comun_no_deja_decodificar_a_invoke_restmethod
FAILED tests/test_f036_scripts_infra.py::test_f036_r111_el_comun_decodifica_los_bytes_como_utf8
FAILED tests/test_f036_scripts_infra.py::test_f036_r111_el_comun_envia_el_cuerpo_en_utf8
FAILED tests/test_f036_scripts_infra.py::test_f036_r111_el_comun_sigue_leyendo_solo_por_sql_read
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_mide_las_actividades_de_los_proveedores
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_las_actividades_tambien_en_global
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_el_tamano_de_auxpronat
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_el_arbol_se_lee_entero_y_paginado
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_el_padre_se_deduce_por_prefijo_del_codigo
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_la_forma_del_codigo_enmascara_letras_y_cifras
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_las_actividades_solo_con_mostrarnombres
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_actividades_por_rama_de_primer_nivel
FAILED tests/test_f036_scripts_infra.py::test_f036_r109_cruce_de_actividades_y_oficios
FAILED tests/test_f036_scripts_infra.py::test_f036_r107_las_actividades_de_los_proveedores_de_la_obra
FAILED tests/test_f036_scripts_infra.py::test_f036_t1_las_lecturas_paginadas_anaden_desde_y_tamano
16 failed, 49 passed in 0.20s
```

Dos trazas (`--tb=line`):

```
E   assert '[Text.Encoding]::UTF8.GetString($web.RawContentStream.ToArray())' in 'function Invoke-SigridLectura {\n    \n    param(\n ...
E   KeyError: 'sqlActividadesResumen'
```

Los otros tests nuevos que pasaban en rojo son los que fijan lo que ya estaba
bien (08 en ASCII/CRLF, ningún otro script llama a la pasarela por su cuenta, el
JSON en `UTF8Encoding($false)`, lo de `confam` sigue).

**RED del defecto, dinámico**: el script **sin tocar** (commit `1496383`) contra
el doble fiel, con PowerShell 5.1
(`python ensayo_t1bis.py 18766 red -SinGlobal`):

```
salida del proceso: 0; consola decodificada como utf-8
  consola contiene 'Fontanería': False
  consola contiene 'Albañilería': False
  consola contiene 'Domótica': False
  consola contiene 'baño 1': False
  consola contiene 'lavandería': False
  consola contiene 'Ã' (doble codificacion): True
JSON: 121275 bytes; BOM: False
  bytes tras 'Fontaner': C3 83 C2 AD 61
  contiene C3 AD (i acentuada bien): False
  contiene C3 83 C2 AD (doble codificacion): True
```

Y en la consola: `0134  FontanerÃ­a`, `0200  DomÃ³tica`: lo mismo que vio el
humano en T2.

### Verde

- Tests: `tests/test_f036_scripts_infra.py`, **66 passed**. Con los de `infra/`
  que usan el 08 (`test_f010_prompt_keys_infra.py`, `test_f010_scripts_infra.py`,
  `test_f012_scripts_infra.py`, `test_f013_scripts_infra.py`): **370 passed,
  3 skipped** en 61,39 s.
- Solo con el 08 corregido (26 aún sin B), mismo ensayo: `bytes tras 'Fontaner':
  C3 AD 61`, sin `C3 83 C2 AD`, sin `Ã` en consola, `PASA`. Con la consola en la
  página de códigos **850** (la de un Windows en español): `Fontanería`,
  `Albañilería`, `Domótica`, `baño 1` bien y sin `Ã`.
- Ensayo final, script completo con global y `-SalidaJson`, doble recién
  arrancado (`python ensayo_t1bis.py 18766 final`): salida 0, `PASA`; consola con
  todas las tildes y sin `Ã`; JSON UTF-8 sin BOM con `46 6F 6E 74 61 6E 65 72 C3
  AD 61` y sin `C3 83 C2 AD`; las 8 claves (`actividades_proveedor` 20 filas,
  `actividades_catalogo` 610 en dos páginas). **45 peticiones**, todas a
  `/api/sql/read`, todas `SELECT`, `?` = nº de parámetros en todas,
  `max_rows` ≤ 1.000, todas con `charset=utf-8` y cuerpo UTF-8 válido. El `ide`
  de la obra del doble, 0 veces en consola y JSON; nombres de proveedor, 0 en
  consola; códigos de actividad literales, 0 en consola (sin `-MostrarNombres`).
- Árbol por prefijo del doble (`01`, `01.01`, `01.01.01`): «prefijo», 3 niveles
  (10 / 200 / 400), formas `99`, `99.99`, `99.99.99`, 4 ramas con actividades de
  la obra. Con `-MostrarNombres` y códigos de ancho fijo con ceros: la raíz sale
  como `010000  REVESTIMIENTOS HORIZONTALES Y VERTICALES`, con su tilde en
  `GRIFERÍA`.
- Rama de error del 08 nuevo: un 400 del doble da `AVISO: No se ha podido
  consultar el ERP (HTTP 400): WebException` y `$null` con `-Tolerante`; sin
  servidor, igual sin código HTTP. Un parámetro `Albañilería` llega al doble como
  UTF-8 válido con `charset=utf-8`.
- **Pendiente**: la comprobación en página 850 no se repitió tras B (el
  relanzamiento se quedó colgado y se cortó por tiempo; el líder pidió no
  repetir ensayos largos). B no toca la lectura ni la escritura de texto.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de la tarea | `test_f036_scripts_infra.py`: **66 passed** (46 de T1 + 20 nuevos; uno de T1 ampliado) |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 5,53 s; servicio `api`: **4422 passed, 52 skipped** en 136,14 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-036 no cambia líneas Python de producción frente a dev)`: solo `.ps1` y tests |
| Mutación | No se relanza: no hay líneas Python de producción que mutar (la campaña de T1 dio 0 mutantes por lo mismo). Protegen los tests estáticos y los ensayos de arriba |
| MANUAL pendiente | Repetir T2 (abajo) |

### Comando de T2 (para el humano, repetirlo)

Desde la raíz del repositorio, con `SIGRID_API_BASE_URL` y `SIGRID_API_KEY` en
la sesión (o la clave por consola):

```powershell
powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -SalidaJson "$env:TEMP\catalogo_0677.json"
```

Sobrescribe el JSON anterior (el que tenía los nombres corrompidos). Para ver
los nombres de las ramas de actividad en consola, el mismo comando con
`-MostrarNombres` (salen también los de obra y unidades: lo que se anote en
`progress/`, sin nombres de persona). Si las lecturas globales tardan, se
puede repetir con `-SinGlobal`. Qué mirar: que `Fontanería` salga bien en
consola; la hipótesis del árbol («prefijo» / «ceros» / «ninguna») y sus
formas; y el cruce con `auxofc`.

## Bloque 1 (T4–T6) · 2026-09-29 · T4 y T5 hechas; T6 BLOQUEADA

> **Resumen para el líder.** T4 (`dc83409`) y T5 (`5217b60`, más `7d5eb5d`
> con lo que destapó la mutación) hechas, con commit y `[x]` en `tasks.md`;
> el bloqueo de T6 va en `670c81e`. **T6 no se ha empezado: está bloqueada** porque
> la lista de las 44 `rcp.resubi` de la 0677 **no está escrita en ningún
> sitio** (detalle y cómo desbloquearla en «T6 · bloqueada», abajo). F-036
> queda `blocked` en `harness/features.json` con el motivo.

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `domain/models/plantilla_incidencias.py` (nuevo) | T4 (+T5) | §4.1: identificador, versión, `CABECERA`, topes, `SEPARADOR_PAR`, `Urgencia`/`Listado`/`OrigenIncidencia`, `UnidadPosventa`, `OficioObra`, `ProveedorEnObra`, `CatalogoObra`, `Opcion`, `OpcionOficio`, `OpcionProveedor`, `ListasCerradas`, `normalizar_codigo_obra` (R9), `normalizar_para_clave` (R35), `etiquetas_de_unidades` (R8) y `plegar` (pública desde T5, para los avisos de R34) |
| `domain/models/equivalencias.py` (nuevo) | T4 | **Solo** `Catalogo` (con `OFICIO`) y `Grupo`, tal cual §15.2. Lo demás del módulo es de T7 (ver decisión 1) |
| `domain/models/errores.py` | T4 | §4.6: `CodigoDeObraInvalido`, `PeticionDeImportacionInvalida`, `FicheroDemasiadoGrande`, `FicheroNoEsPlantilla(codigo, motivo)` con la lista cerrada `CODIGOS_FICHERO_NO_ES_PLANTILLA`, `ObraSinUnidades`, `ObraAmbigua`, `CatalogoSinVerificar`, `CatalogoNoDisponible`, `PeticionDeDecisionInvalida`, `CodigoNoEsDeLaObra`; párrafo nuevo en el docstring del módulo. Solo añadidos |
| `domain/models/importacion.py` (nuevo) | T5 | §4.2–§4.5: `CeldaLeida`, `FilaLeida`, `LibroLeido`, `reconocer_plantilla`, `ErrorDeFila`, `Elegido`, `IncidenciaValida`, `FilaConError`, `resolver_oficio_y_proveedor`, `validar_filas`, `clave_de_duplicado`, `GrupoDeClave`, `agrupar_por_clave`, `EstadoFilaImportada`, `EstadoImportacion`, `IncidenciaEnBandeja` |
| `tests/test_f036_plantilla_dominio.py` (nuevo) | T4 | 74 tests (65 en T4; 9 de inmutabilidad tras la mutación) |
| `tests/test_f036_importacion_dominio.py` (nuevo) | T5 | 168 tests (158 en T5; 10 tras la mutación) |
| `specs/F-036-importar-excel/tasks.md` | T4, T5 | `[x]` en T4 y T5 |

Nada de `openpyxl`, red, base, IA ni reloj en `domain/` (un test lo comprueba
con `ast` sobre `plantilla_incidencias.py` y `equivalencias.py`; el test de
arquitectura completo es de T10). Ningún nombre de proveedor real: los de los
tests son inventados («Carpinterías Ejemplo S.L.», «Juan Ejemplo Ejemplo»,
«Pinturas Ejemplo S.A.»).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **`Grupo` y `Catalogo` adelantados de T7 a T4.** `design.md` §4.1 define
   `OpcionOficio.grupo: Grupo` y `OpcionProveedor.grupo: Grupo`, y dice que
   `Grupo` es de `domain/models/equivalencias.py` (§15.2), que `tasks.md`
   asigna a T7. Para que T4 pueda definir las opciones (y T5 construirlas a
   mano), `equivalencias.py` nace en T4 **solo con esos dos tipos**, copiados
   de §15.2 sin cambios; T7 añade el resto en el mismo fichero.
2. **Desviación de §4.3: `validar_filas` recibe las opciones, no los grupos.**
   El diseño firma `validar_filas(..., grupos_oficio: GruposVigentes,
   grupos_proveedor: GruposVigentes, ...)` y calcula dentro las opciones con
   `opciones_de_oficio`/`opciones_de_proveedor`, que son de T7. `tasks.md` T5
   dice lo contrario: «la parte de oficio y proveedor se escribe contra
   `OpcionOficio` y `OpcionProveedor` construidas a mano». Manda el encargo
   literal: la firma es `validar_filas(filas, *, catalogo, opciones_oficio,
   opciones_proveedor, listas)`. Además es lo que necesita §7.3 (el paso 6
   genera el Excel de errores «con el mismo catálogo y opciones»): quien llama
   calcula las opciones una vez y las usa en los dos sitios. **Consecuencia
   para T7/T17**: `ContextoImportacion` guardará las opciones (o los grupos y
   las opciones); si el humano prefiere la firma del diseño, es un envoltorio
   de dos líneas en T7. Justificado también en `progress/current.md`.
3. **Hueco de la spec que hereda T7 (no bloquea T4/T5).** `OpcionProveedor.grupo`
   es un `Grupo`, y `Grupo.catalogo` es un `Catalogo`, que en F-036 solo tiene
   `OFICIO` (§15.2: «F-050 añadirá `PROVEEDOR`»). No hay valor correcto para el
   grupo de un proveedor. Los tests de T5 lo construyen con `Catalogo.OFICIO`
   y un comentario; la resolución solo usa `grupo.etiqueta` (el nombre del
   proveedor) y las `filas_en_obra`. **T7 tiene que decidirlo** (añadir
   `PROVEEDOR` ya —el `CHECK` de T14 lo admite desde el principio— o que el
   grupo de proveedor no sea un `Grupo`). Anotado para la PARADA T9.
4. **R8, colisiones.** La etiqueta base de cada unidad es su nombre recortado o,
   si no tiene, su código; dos bases que coinciden **plegadas** (sin tildes,
   mayúsculas ni blancos de más: Excel compara las listas sin distinguir
   mayúsculas) pasan a `<nombre> (<código>)`, y las que no tienen nombre se
   quedan con su código. Así una unidad sin nombre y otra que se llame como
   ese código no chocan. Las etiquetas salen siempre distintas y ordenadas por
   código (texto: `…VILLA 1.`, `…VILLA 10.`, … `…VILLA 2.`).
5. **Celdas vacías.** Una celda con solo blancos cuenta como vacía (R23, R25):
   «Unidad» con un espacio da «falta la unidad», no «no está en la lista». No
   es casado aproximado: un valor con texto se sigue comparando exacto y
   «Villa 1 » es error.
6. **Un error por columna.** Una fórmula (R32) en `Descripción corta` da solo
   «lleva una fórmula», no además «falta la descripción». Los errores de una
   fila salen en el orden de la cabecera y se recorren todas las filas.
7. **Números en texto libre (R32).** `12` → «12», `3.5` → «3.5», `4.0` → «4».
   Un booleano cuenta como fecha/booleano aunque el lector no lo marque.
8. **R74.** Con `Oficio` y `Proveedor` válidos pero de grupos distintos, el
   error va en la columna `Proveedor`. Con `Oficio` fuera de la lista y
   `Proveedor` bueno, solo se marca `Oficio`.
9. **Etiqueta del proveedor elegido.** `Elegido.etiqueta` del proveedor es
   `OpcionProveedor.grupo.etiqueta` (su nombre), no la del par («oficio ·
   proveedor»): es lo que irá a `proveedor_nombre` de la bandeja.
10. **Avisos (R34).** Búsqueda por subcadena sobre descripción + detalle
    plegados («peligroso», «estructurales» también avisan); mayúsculas con
    aritmética entera (`mayúsculas × 100 > letras × 60`, con ≥ 20 letras; las
    letras con tilde cuentan). Orden de los avisos: oficio ambiguo, proveedor
    ambiguo, urgencia, mayúsculas. Los textos van en lenguaje llano y sin datos
    de la fila salvo la etiqueta del oficio/proveedor ambiguo.
11. **Invariantes de R99 en el dominio.** `Elegido` exige `codigo is None ⇔
    ambiguo`; `IncidenciaValida` e `IncidenciaEnBandeja` rechazan un proveedor
    sin oficio; `IncidenciaEnBandeja` además un ambiguo con código o sin
    nombre, y un nombre sin código ni ambigüedad. Los `CHECK` de la base son de
    T14.
12. **Cabecera (R19).** Se recortan los espacios de cada celda y se ignoran las
    celdas vacías del final; el motivo dice qué falta, sobra (también «una
    columna sin nombre (la N.ª)»), está repetida o, si no hay nada de eso, la
    primera movida.
13. **Mensajes de error internos** (`ValueError` de invariantes) sin etiquetas ni
    nombres: acaban en una traza (R47).
14. `FicheroNoEsPlantilla` revienta con `ValueError` si recibe un código fuera
    de la lista cerrada: un código nuevo es un cambio de contrato.

### T6 · bloqueada (motivo y cómo desbloquearla)

`tasks.md` T6 exige que la lista de ubicaciones del YAML salga de **las 44
`rcp.resubi` de la 0677 normalizadas**, y el encargo dice que están en
`progress/explore_F-036.md`. **No están**: ese fichero solo trae los recuentos
(1.219 reclamaciones, 44 distintas), las ocho más frecuentes y las cuatro
parejas de variantes. Tampoco están en el JSON de T2
(`%TEMP%\catalogo_0677.json`, que no guarda ubicaciones: sus claves son
`obra`, `unidades`, `oficios_obra`, `oficios_catalogo`, `familias_*`,
`actividades_*`), ni en el historial de git, ni en otro fichero del
repositorio. El script de T1 las **imprime en consola** («Las 60 más
frecuentes») y nadie las copió.

No se han inventado: sería exactamente lo que D-3 descartó (la lista «de antes
de medir»). No se ha ejecutado el script: T2 es MANUAL (humano) y lee de la
pasarela de producción.

**Para desbloquear** (humano, solo lectura, unos segundos con `-SinGlobal`):

```powershell
powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -SinGlobal
```

y copiar a `progress/explore_F-036.md`, sección «Ubicaciones», las 44 líneas
del bloque «Las 60 más frecuentes» (recuento y texto, tal cual), revisando
antes que ninguna lleve un nombre de persona. Con eso T6 se hace en un encargo
(normalización propuesta para que la revise el humano, YAML, cargador y
tests).

### Fase RED

Tests escritos **antes** que el código, ejecutados desde `services/postventa-api`.

**T4** · `.venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_dominio.py -q`,
antes de crear `equivalencias.py` y `plantilla_incidencias.py`:

```text
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f036_plantilla_dominio.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_plantilla_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_plantilla_dominio.py:26: in <module>
    from domain.models.equivalencias import Catalogo, Grupo
E   ModuleNotFoundError: No module named 'domain.models.equivalencias'
=========================== short test summary info ===========================
ERROR tests/test_f036_plantilla_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.37s
```

**T5** · `.venv/Scripts/python.exe -m pytest tests/test_f036_importacion_dominio.py -q`,
antes de crear `importacion.py`:

```text
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_f036_importacion_dominio.py ___________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_importacion_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_importacion_dominio.py:27: in <module>
    from domain.models.importacion import (
E   ModuleNotFoundError: No module named 'domain.models.importacion'
=========================== short test summary info ===========================
ERROR tests/test_f036_importacion_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.38s
```

Un error de importación solo prueba que el módulo no existía. Para los dos
requisitos **centrales** se demostró además que los tests cazan el
comportamiento equivocado, sustituyendo a propósito el código bueno y
restaurándolo después (`git status` limpio tras cada prueba):

**Comparación exacta (decisión 7; R26, R29, R30, R73)**: `_Fila.tasado`
cambiado a comparar **plegado** (sin mayúsculas, tildes ni blancos de más), que
era la regla anterior a la enmienda del 2026-09-28.
`.venv/Scripts/python.exe -m pytest tests/test_f036_importacion_dominio.py -q -k "r26 or r29 or r30 or r73"`:

```text
def errores_de(f: FilaLeida) -> list[tuple[str, str]]:
        validas, con_error = validar(f)
>       assert validas == ()
E       AssertionError: assert (IncidenciaVa..., avisos=()),) == ()
E         
E         Left contains one more item: IncidenciaValida(fila=2, unidad=Opcion(etiqueta='Villa 1', codigo='0677.03VILLA 1.'), ubicacion=None, descripcion='x',...edor=Elegido(etiqueta='Carpinterías Ejemplo S.L.', codigo='P1', ambiguo=False), urgencia=None, listado=None, avisos=())
E         Use -v to get more diff

tests\test_f036_importacion_dominio.py:230: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta[villa 1]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta[Villa 1 ]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta[ Villa 1]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta[Villa  1]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r26_unidad_exacta[VILLA 1]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r29_ubicacion_exacta[cocina]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r29_ubicacion_exacta[Cocina ]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r29_ubicacion_exacta[COCINA]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r30_oficio_exacto[pintura]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r30_oficio_exacto[Pintura ]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r30_oficio_exacto[Carpinteria de madera]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r73_proveedor_exacto[Carpinter\xeda de madera \xb7 carpinter\xedas ejemplo s.l.]
FAILED tests/test_f036_importacion_dominio.py::test_f036_r73_proveedor_exacto[Carpinter\xeda de madera \xb7  Carpinter\xedas Ejemplo S.L.]
13 failed, 8 passed, 137 deselected in 0.88s
```

(Los 8 que pasan son los valores que tampoco casan plegados, p. ej.
«Villa 1.» o «Sala/estudio»: siguen siendo error con las dos reglas.)

**Resolución conjunta oficio–proveedor (R94, §15.5)**: el oficio con proveedor
resuelto por los códigos del grupo en vez de por las filas de `obrofc` del par.
`.venv/Scripts/python.exe -m pytest tests/test_f036_importacion_dominio.py -q -k "r94 or d17"`:

```text
E         ...Full output truncated (3 lines hidden), use '-vv' to show

tests\test_f036_importacion_dominio.py:988: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f036_importacion_dominio.py::test_f036_r94_design_15_5_el_proveedor_deshace_la_ambiguedad
FAILED tests/test_f036_importacion_dominio.py::test_f036_r74_d17_solo_proveedor_toma_el_oficio_del_par
FAILED tests/test_f036_importacion_dominio.py::test_f036_r94_fila_con_proveedor_que_resuelve
3 failed, 2 passed, 153 deselected in 0.48s
```

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_dominio.py tests/test_f036_importacion_dominio.py -q`
→ **242 passed** en 0,66 s (74 + 168). Cobertura de rama con `coverage.py`
sobre los tres módulos nuevos: **100 %** de líneas y de ramas
(`importacion.py` 292/292 y 98 ramas; `plantilla_incidencias.py` 102/102 y
14; `equivalencias.py` 10/10).

### Mutación: dos campañas

1. **Primera** (sobre `5217b60`): 105 mutantes, 90 muertos, **15
   supervivientes**, 3.956,9 s con 8 workers. Análisis:
   - 12 × `@dataclass(frozen=True)` → `frozen=False`: huecos reales, ningún
     test comprobaba la inmutabilidad de esas clases. **Test nuevo** en cada
     fichero de tests: recorre todas las dataclasses de los tres módulos y
     exige `frozen` (18 clases).
   - `PORCENTAJE_MAYUSCULAS = 60` → `61`: hueco real; el caso de 20 letras
     (12 = 60 % no, 13 = 65 % sí) no distinguía 60 de 61–64. **Test nuevo**
     con 100 letras (60 no avisa, 61 sí).
   - 2 × `zip(..., strict=True)` → `strict=False` (cabecera movida y
     etiquetas de unidades): **equivalentes** (las dos listas miden lo mismo
     por construcción), así que se **quitó el `zip`** en vez de justificarlos:
     la cabecera se recorre por posición y las colisiones se cuentan con
     `Counter`.
   Arreglado en `7d5eb5d`.
2. **Segunda** (sobre `670c81e`, árbol limpio): **105 mutantes, 105 muertos,
   0 supervivientes, 0 timeouts**, 2.260,7 s con 8 workers
   (`progress/mutacion_F-036.md`, 2026-09-29 13:20).

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de la tarea | `test_f036_plantilla_dominio.py` + `test_f036_importacion_dominio.py`: **242 passed** en 0,66 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 4,52 s; servicio `api`: **4667 passed, 52 skipped** en 64,99 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 448 líneas cambiadas cubiertas (448/448, umbral 80%, nivel critico)` |
| Mutación | 105 generados, **0 supervivientes** (segunda campaña; la primera dejó 15, analizados arriba y cerrados con tests o quitando el código redundante) |
| Tiempo de la suite | `api` 64,99 s; mutación 2.260,7 s |
| Lint | `ruff` sin avisos en los ficheros de F-036 (el total del árbol, 63, es deuda previa; los dos de orden de imports de los tests se corrigieron al final, commit de cierre del bloque) |
| MANUAL pendiente | Ninguna de T4/T5. **T6 bloqueada**: el comando de arriba (humano) |

### Qué queda fuera y qué falta

- **T6** entera (bloqueada, arriba).
- `opciones_de_oficio`, `opciones_de_proveedor`, `TextosPlantilla` y el resto
  de `equivalencias.py`: T7 y T6, como dice `tasks.md`.
- El test de arquitectura completo (`test_f036_arquitectura.py`) es de T10;
  aquí solo se comprueba la pureza de los dos módulos del contrato.
- Para T7: el hueco del catálogo del grupo de proveedor (decisión 3) y la
  firma de `validar_filas` (decisión 2).

### T6 · hecha (2026-09-29, tras el desbloqueo `1c768d6`)

> Sustituye a «T6 · bloqueada» de arriba, que queda como historia: el líder
> copió las 44 ubicaciones a `progress/explore_F-036.md` y devolvió F-036 a
> `in_progress`. Commit de la tarea: `37f45ae`.

#### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Qué |
|---|---|
| `config/plantilla_incidencias.yaml` (nuevo) | 42 ubicaciones (40 de las 44 medidas + 2 añadidas marcadas `revisar`), cada una con su `origen`; urgencias y listados con los códigos del dominio; textos de «Instrucciones» (R5), la línea de obra sin oficios (R12), el párrafo del Excel de errores (§3.5), 3 filas de ejemplo y los mensajes de entrada y de error de las 8 columnas con validación (R3, R4) |
| `infrastructure/documentos/plantilla_yaml.py` (nuevo) | `cargar_plantilla_yaml(ruta=RUTA_POR_DEFECTO) -> ConfiguracionPlantilla(listas, textos, ubicaciones_por_revisar)`. Ruta fija relativa al servicio (R49: sin variables nuevas), valida **todo** al cargar |
| `domain/models/plantilla_incidencias.py` | `MensajeColumna` y `TextosPlantilla` (§4.1 los anunciaba; ahora tienen la forma del YAML) |
| `domain/models/errores.py` | `ConfiguracionPlantillaInvalida` (ver decisión T6-1) |
| `tests/test_f036_configuracion_plantilla.py` (nuevo) | 102 tests (99 en `37f45ae`; 3 tras la mutación) |
| `specs/F-036-importar-excel/tasks.md` | `[x]` en T6 |

#### Tabla «ubicación original → ubicación normalizada» (para que la revise el humano)

Las 44 `rcp.resubi` de la 0677 tal como las midió T2, con su recuento. **Negrita**
= fusión (dos valores medidos a una ubicación) o cambio más allá de mayúscula
inicial y tildes.

| Recuento | Original (Sigrid) | Normalizada | Qué se hizo |
|---:|---|---|---|
| 179 | jardín | Jardín | mayúscula |
| 70 | cocina | Cocina | mayúscula |
| 64 | escalera | Escalera | mayúscula |
| 62 | salón | Salón | mayúscula |
| 58 | Garaje | Garaje | ninguno |
| 55 | baño 1 | Baño 1 | mayúscula |
| 55 | dormitorio 1 | Dormitorio 1 | mayúscula |
| 48 | distribuidor p. baja | **Distribuidor planta baja** | mayúscula y **abreviatura desplegada** («p.» → «planta») |
| 46 | dormitorio 3 | Dormitorio 3 | mayúscula |
| 44 | almacén | Almacén | mayúscula |
| 40 | dormitorio 4 | Dormitorio 4 | mayúscula |
| 40 | sala/estudio | Sala/estudio | mayúscula (sin espacios alrededor de «/», como en Sigrid) |
| 39 | dormitorio 2 | Dormitorio 2 | mayúscula |
| 32 | terraza planta 2 | Terraza planta 2 | mayúscula |
| 31 | terraza 1 | Terraza 1 | mayúscula |
| 28 | baño 7 | Baño 7 | mayúscula |
| 27 | baño 2 | Baño 2 | mayúscula |
| 26 | bao 3 | **Baño 3** | **fusión** con `baño 3` (errata, §3.4) |
| 25 | office | Office | mayúscula |
| 24 | Cuarto de plancha | Cuarto de plancha | ninguno; **recibe** `cuarto plancha` |
| 24 | vestíbulo sótano | Vestíbulo sótano | mayúscula |
| 20 | lavandería | Lavandería | mayúscula; **recibe** `lavanderçia/tendedero` |
| 20 | terraza 3 | Terraza 3 | mayúscula |
| 19 | baño 6 | Baño 6 | mayúscula |
| 15 | baño 4 | Baño 4 | mayúscula |
| 11 | terraza instalaciones | **Terraza de instalaciones** | mayúscula y «de», como «Cuarto de plancha»; **recibe** `terraza instaciones` |
| 10 | aseo | Aseo | mayúscula |
| 10 | distribuidor p. 1 | **Distribuidor planta 1** | mayúscula y **abreviatura desplegada** |
| 9 | baño 5 | Baño 5 | mayúscula |
| 9 | vestidor 3 | Vestidor 3 | mayúscula |
| 8 | baño 3 | Baño 3 | mayúscula; **recibe** `bao 3` |
| 8 | cuarto plancha | **Cuarto de plancha** | **fusión** con `Cuarto de plancha` (§3.4) |
| 7 | cuarto instalaciones | **Cuarto de instalaciones** | mayúscula y «de», por coherencia con «Cuarto de plancha» |
| 7 | lavanderçia/tendedero | **Lavandería** | **fusión** con `lavandería` (§3.4); **se pierde «tendedero»**: ver pregunta 2 |
| 7 | patio trasero | Patio trasero | mayúscula |
| 7 | terraza instaciones | **Terraza de instalaciones** | **fusión** con `terraza instalaciones` (errata, §3.4) |
| 7 | vestíbulo p. baja | **Vestíbulo planta baja** | mayúscula y **abreviatura desplegada** |
| 7 | vestidor 1 | Vestidor 1 | mayúscula |
| 6 | comedor | Comedor | mayúscula |
| 5 | patio delantero | Patio delantero | mayúscula |
| 4 | despacho | Despacho | mayúscula |
| 3 | ascensor | Ascensor | mayúscula |
| 2 | terraza 4 | Terraza 4 | mayúscula |
| 2 | trastero | Trastero | mayúscula |

Resultado: 44 medidas → **40** ubicaciones (las cuatro fusiones de §3.4, ni una
más). Ningún número de estancia cambia (un test lo comprueba). Añadidas sin
medir, con `revisar` en el YAML:

| Añadida | Por qué |
|---|---|
| `General (toda la unidad)` | La muestra usa `GENERALES` (5 filas) para defectos de toda la vivienda y ninguna medida lo cubre; la migración (T24) la necesita |
| `Otra (explicar en el detalle)` | Con una lista cerrada y comparación exacta, quien rellena necesita una salida para un sitio que no está; sin ella elegiría uno cualquiera. Estaba en la propuesta inicial de §3.4 |

El desplegable va en este orden: `General` primero, las medidas por orden
alfabético (con los números en su orden) y `Otra` al final.

**Preguntas para el humano** (lo hecho es la opción por defecto; cambiar
cualquiera es tocar el YAML y nada más):

1. ¿Desplegar las abreviaturas (`p. baja` → `planta baja`) y añadir «de»
   (`Cuarto de instalaciones`, `Terraza de instalaciones`)? Se hizo pensando
   en quien rellena sin formación; Posventa escribía la forma corta.
2. `lavanderçia/tendedero` → `Lavandería`, como dice §3.4. Si el tendedero es
   otro sitio, sería una ubicación más («Tendedero») o «Lavandería/tendedero».
3. ¿`General (toda la unidad)` y `Otra (explicar en el detalle)` se quedan?
4. Muestra sin equivalente claro, que decidirá la migración (T24) fila a fila
   y **no** se han añadido: `PASILLO` y `PASILLO DORMITORIO 1` (¿distribuidor?),
   `PATIO SOTANO`, `VENTANA PATIO`, `VENTANAS`, `TERRAZA` y `DORMITORIO 1
   TERRAZA` (¿cuál de las terrazas?), `DORMITORIO N BAÑO` (¿qué `Baño N`?),
   `BAÑO PLANTA BAJA` (¿`Aseo`?), `VESTIBULO` (¿planta baja o sótano?) y
   `TIRO DE ESCALERA` (→ `Escalera`, claro).

#### Decisiones de T6

- **T6-1 · `ConfiguracionPlantillaInvalida` en `errores.py`.** §3.4 dice que el
  cargador «falla» sin nombrar el error; §4.6 no lo lista. Se añadió uno propio
  (como `PromptNoEncontrado` para los prompts), sin código HTTP: es
  configuración y revienta al cargar.
- **T6-2 · El YAML guarda el origen de cada ubicación.** `origen` (los valores
  medidos) y `revisar` (motivo, en las añadidas) hacen comprobable la
  normalización: un test exige que las 44 medidas estén **una vez cada una**.
  Los valores medidos ya estaban versionados en `explore_F-036.md` y no llevan
  nombres de persona (revisado por el líder).
- **T6-3 · Qué valida el cargador**, además de lo de §3.4 (≤ 48, sin dos iguales
  plegadas —también quitando la puntuación final—, códigos = `Enum`): exige
  **exactamente** los códigos del `Enum` (ni falta ni sobra ninguno), etiquetas
  no vacías y sin repetir, ubicaciones sin blancos de más (se comparan exactas),
  cada origen en una sola ubicación, 2–3 ejemplos con columnas de la plantilla,
  sus obligatorias y valores de las listas, y un mensaje por cada columna con
  validación dentro de los **topes de Excel** (32 el título, 255 el texto).
- **T6-4 · Ejemplos.** La unidad y el oficio de un ejemplo no pueden ser reales
  (dependen de la obra): van como «Vivienda 1 (elígela de la lista)». Los
  ejemplos son para leer; el generador (T10) los escribirá en «Instrucciones».
- **T6-5 · Estructuras de solo lectura.** `mensajes` y cada ejemplo son
  `MappingProxyType`: nadie puede tocar los textos cargados.

#### Fase RED de T6

`.venv/Scripts/python.exe -m pytest tests/test_f036_configuracion_plantilla.py -q`,
antes de crear el YAML, el cargador y el error:

```text
=================================== ERRORS ====================================
_________ ERROR collecting tests/test_f036_configuracion_plantilla.py _________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_configuracion_plantilla.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_configuracion_plantilla.py:31: in <module>
    from domain.models.errores import ConfiguracionPlantillaInvalida
E   ImportError: cannot import name 'ConfiguracionPlantillaInvalida' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f036_configuracion_plantilla.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.42s
```

#### Verde de T6

`.venv/Scripts/python.exe -m pytest tests/test_f036_configuracion_plantilla.py -q`
→ **102 passed** en 3,36 s. Cobertura de rama de `plantilla_yaml.py`: **100 %** (133
líneas, 66 ramas; la línea de «falta la columna obligatoria» del ejemplo la
destapó la medición y tiene su test).

#### Mutación de T6

Campaña `python -m harness.mutacion --feature F-036 --workers 4 --timeout 400`
sobre `37f45ae` (todo F-036: T4, T5 y T6): **153 mutantes, 148 muertos, 5
supervivientes, 0 timeouts**, 4.162,9 s. (Una primera tanda con los 8 workers
de `rigor.json` se paró a mano: la máquina estaba cargada por otros procesos y
145 de 153 mutantes agotaban los 120 s; el repaso en serie iba a durar unas
tres horas.)

Los 5 supervivientes son de `plantilla_yaml.py` y son **huecos reales** de los
tests de T6 (bordes exactos de «dos o tres» ejemplos, el número del ejemplo en
el motivo y la descripción de 128 exactos del ejemplo). Tres tests nuevos los
cierran; en vez de repetir la campaña (69 min) se aplicó cada mutante a mano y
se pasó `tests/test_f036_configuracion_plantilla.py`, restaurando el fichero
después (`git status` limpio en producción):

```text
MIN_EJEMPLOS = 2 -> MIN_EJEMPLOS = 3: MUERTO | 1 failed, 101 passed in 12.69s
MAX_EJEMPLOS = 3 -> MAX_EJEMPLOS = 4: MUERTO | 1 failed, 101 passed in 5.45s
not MIN_EJEMPLOS <= len(crudo) -> not MIN_EJEMPLOS < len(crudo): MUERTO | 1 failed, 101 passed in 4.29s
enumerate(crudo, start=1) -> enumerate(crudo, start=2): MUERTO | 1 failed, 101 passed in 5.09s
if len(fila["Descripción corta"]) > MAX_DESCRIPCION: -> if len(fila["Descripción corta"]) >= MAX_DESCRIPCION:: MUERTO | 1 failed, 101 passed in 3.48s
```

El análisis de cada uno está también en `progress/mutacion_F-036.md` (ninguno
queda `PENDIENTE`).

#### Evidencias del Bloque 1 completo (T4–T6)

| Evidencia | Valor |
|---|---|
| Tests de la tarea (T6) | `test_f036_configuracion_plantilla.py`: **102 passed** en 3,36 s |
| Tests del bloque | T4 74 + T5 168 + T6 102 = **344** |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 5,37 s; servicio `api`: **4772 passed, 52 skipped** en 135,50 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 599 líneas cambiadas cubiertas (599/599, umbral 80%, nivel critico)` |
| Mutación | 153 generados, 148 muertos, 5 supervivientes cerrados con tests nuevos y comprobados a mano uno a uno (arriba); 0 sin analizar |
| Tiempo de la suite | `api` 135,50 s (máquina cargada; 64,99 s en la medición de T5); campaña 4.162,9 s |
| MANUAL pendiente | Revisión del humano de la tabla de ubicaciones y de las cuatro preguntas de arriba |

## Bloque 2 (T7–T8) · 2026-09-29 · hecho; T9 es PARADA del líder

> **Resumen para el líder.** T7 (`80e772a`) y T8 (`03d907d`) hechas, con
> commit y `[x]` en `tasks.md`. El hueco que dejó el Bloque 1 (el catálogo del
> grupo de proveedor) se cierra con la costura de §15.8 añadiendo
> **`Catalogo.PROVEEDOR` como discriminador, sin perfil** (decisión B2-1, para
> que el humano la confirme en T9). Los recuentos de T8 para la PARADA T9
> están abajo, en «Recuentos de T8 para T9», y en `progress/explore_F-036.md`.
> `bash harness/init.sh` en verde. No se ha tocado T9.

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `domain/models/equivalencias.py` | T7 | §15.2 y §15.4 completos: `Catalogo` (+`PROVEEDOR`), `Motivo`, `Perfil`, `PERFILES` (solo `oficio`, de solo lectura), `PALABRAS_VACIAS`, umbrales de D-22 como constantes, `Candidato`, `DecisionPar` (valida `codigo_a < codigo_b` y la decisión), `ParPropuesto`, `Propuesta`, `GruposVigentes` (valida catálogo y códigos sin repetir; `grupo_de`), `clave_de_nombre`, `clave_singular`, `distancia_edicion`, `motivos_del_par`, `proponer_grupos`, `grupos_vigentes` y la costura `grupos_de_proveedor` (§15.8) |
| `domain/models/plantilla_incidencias.py` | T7 | `opciones_de_oficio` (R92, R86) y `opciones_de_proveedor` (R71, R72); docstring del módulo al día |
| `tests/test_f036_equivalencias_dominio.py` (nuevo) | T7 | 106 tests: R78–R86, R95, R96, los tres pares medidos en la 0677 |
| `tests/test_f036_plantilla_dominio.py` | T7 | +24 tests (74 → 98): R71, R72, R92, R86, R12, la tabla de §15.5 de punta a punta con `resolver_oficio_y_proveedor`; el test de T4 que fijaba `Catalogo == ["oficio"]` pasa a `["oficio", "proveedor"]`; la lista blanca de imports del dominio admite `types` y `typing` |
| `tests/test_f036_importacion_dominio.py` | T7 | Los grupos de proveedor construidos a mano pasan de `Catalogo.OFICIO` (el apaño anotado en el Bloque 1) a `Catalogo.PROVEEDOR`. Ningún test nuevo ni quitado (168) |
| `scripts/medir_catalogos_f036.py` (nuevo; directorio nuevo) | T8 | Lee el JSON de T2, aplica `proponer_grupos` a la obra y a todo `auxofc`, calcula las opciones de la plantilla sin grupos y «con todo lo propuesto confirmado», e imprime solo recuentos |
| `tests/test_f036_medir_catalogos.py` (nuevo) | T8 | 13 tests con un JSON inventado en memoria (y en `tmp_path` para la línea de órdenes y para lanzarlo como script en un subproceso) |
| `progress/explore_F-036.md` (raíz) | T8 | Sección «T8 (2026-09-29): propuesta de oficios casi duplicados», sin nombres ni códigos |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T7, T8 | `[x]` en T7 y T8 |

Sin dependencias nuevas. Nada de red, Sigrid, base ni IA. Ningún nombre de
proveedor real en el repositorio: los de los tests son inventados y el JSON de
T2 no se ha copiado (el script solo lo lee de `%TEMP%`).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B2-1 · El hueco del grupo de proveedor: `Catalogo.PROVEEDOR` sin perfil.**
   La spec se contradice: §15.2 y la tabla de §15.8 dicen que en F-036
   `Catalogo` «solo tiene `OFICIO`», pero la misma §15.8 pide «grupos vigentes
   de proveedor: cada código, su propio grupo», §4.1 hace
   `OpcionProveedor.grupo: Grupo` (que lleva `catalogo`) y R95 exige un
   discriminador `catalogo ∈ {oficio, proveedor}` para que un código de oficio
   y otro de proveedor escritos igual no se confundan (§14 pide además un test
   de que «el discriminador `catalogo` separa decisiones con los mismos
   códigos», imposible con un solo valor). El encargo decía resolverlo con la
   costura y **sin perfil de proveedores**. Se hizo así: el valor `proveedor`
   (el mismo que ya admite el `CHECK` de la tabla, §15.4) existe en el `Enum`;
   `PERFILES` solo tiene `oficio`, no hay `FORMAS_JURIDICAS`, ni `mismo_cif`,
   ni lectura de grupos de proveedor. Consecuencias: nada puede **proponer**
   grupos de proveedores; `grupos_de_proveedor` da un grupo por código; T19
   tendrá que rechazar `"proveedor"` comparando con `Catalogo.OFICIO`, no con
   «es un valor del `Enum`». **A confirmar por el humano en T9**; la
   alternativa (que el grupo de proveedor no sea un `Grupo`) cambia §4.1 y
   T5.
2. **B2-2 · `Grupo.codigos` es la componente entera** (puede llevar códigos
   que no son de la obra, porque una equivalencia vale para todas, R84) y
   `OpcionOficio.codigos_en_obra` los de la obra. Es la distinción que ya
   hacía §4.1. Solo salen los grupos con algún código de la obra.
3. **B2-3 · Motivos que se excluyen.** §15.2 c define los cuatro por separado,
   pero con distancia 0 todo `mismo_nombre` sería también `errata`. Regla:
   `mismo_nombre` va solo; `errata` solo si no es `plural`; `incluido` puede
   acompañar a `plural` o `errata`. En la 0677 (y en todo `auxofc`) cada par
   sale con un solo motivo.
4. **B2-4 · `incluido` por palabras, no por caracteres.** «Una clave es el
   principio de la otra con al menos dos palabras»: se compara la lista de
   palabras («pintura exterior» no es principio de «pintura exteriores
   lisas»). D-22 dice que `incluido` propone `0085`/`0166` y `0033`/`0133`;
   con esta lectura `0085`/`0166` sale por `plural` (se propone igual) y
   `0033`/`0133` por `incluido`.
5. **B2-5 · El mínimo de 8 caracteres de `errata` no decide con los umbrales
   de D-22**: con distancia ≥ 1 y ≤ 10 %, la clave larga tiene ≥ 10 y la corta
   ≥ 9. Se deja (es la spec, y decidirá si T9 cambia el porcentaje) y su test
   lo prueba con el porcentaje parcheado a 100, para que no quede sin vigilar.
6. **B2-6 · `clave_singular` literal**: «muebles» → «muebl» (consonante +
   `es`), así que «Mueble» / «Muebles» **no** se proponen. Es el «burdo a
   propósito» de §15.2 b; lo anoto para D-22 por si el humano quiere afinar.
7. **B2-7 · Siglas**: dos o más letras sueltas con punto (`M.O.`, `S.A.T`),
   con o sin el último; «p. baja» no es sigla. El resto de la puntuación pasa
   a blanco («Pintura-exterior» → «pintura exterior»).
8. **B2-8 · Clique sobre el grafo sin los pares decididos.** Si un par de un
   trío ya está decidido, lo que queda no es clique y se propone por pares
   (test `r85_par_decidido_rompe_el_clique`).
9. **B2-9 · Última decisión**: manda `decidido_at_utc`; a igual fecha, la que
   llega después. `no_aplicados` (R82) solo lista componentes con algún código
   de la obra.
10. **B2-10 · Etiqueta (R86)**: un código sin filas en `obrofc` cuenta 0; si el
    elegido no tiene nombre, su código.
11. **B2-11 · `opciones_de_oficio`**: una por grupo, por orden del menor código
    (R8, «el desplegable queda como antes»); etiquetas que chocan **plegadas**
    (como las unidades del Bloque 1) llevan los códigos de la obra entre
    paréntesis. Sin grupos, «Carpinteria de madera» y «Carpintería de madera»
    salen como «… (0046)» y «… (0143)». `ValueError` si los grupos son de otro
    catálogo, si un oficio de la obra no tiene grupo o si, aun con códigos, dos
    etiquetas chocan (fail closed: el importador compara exacto).
12. **B2-12 · `opciones_de_proveedor`**: en el orden de las opciones de oficio
    y, dentro de cada una, por nombre plegado; R72 con el nombre **plegado**
    dentro del mismo oficio; filas sin proveedor o de un oficio que no está en
    el desplegable, sin par. `ValueError` si los grupos no son de proveedor o
    un proveedor de `obrofc` no tiene grupo.
13. **B2-13 · `validar_filas` conserva la firma del Bloque 1** (recibe
    opciones, no grupos; decisión 2 del Bloque 1). No hizo falta el envoltorio:
    T17 calculará las opciones con estas dos funciones una vez.
14. **B2-14 · Aviso para T14/T15**: `DecisionPar` exige `codigo_a < codigo_b`
    con el orden de Python (por punto de código). El `CHECK (codigo_a <
    codigo_b)` de §6.1 compara con la intercalación de la base: para códigos
    con letras y cifras podrían no coincidir. Conviene `COLLATE "C"` en el
    `CHECK` o que el repositorio ordene igual. No se toca nada aquí.
15. **B2-15 · Componentes con recorrido en anchura, no con unión-búsqueda**: la
    mutación de `while padre[n] != n` colgaba la suite (bucle infinito, un
    `timeout` en la campaña). Mismo resultado, sin mutantes de ese tipo.
16. **B2-16 · El script** vive en `services/postventa-api/scripts/` (lo dice
    §2.1; el directorio no existía) sin `__init__.py`: los tests lo importan
    como paquete de espacio de nombres. Se añade la raíz del servicio al
    final de `sys.path` para poder lanzarlo como `python scripts/…`. «Con todo
    lo propuesto confirmado» es hipotético: confirma cada par propuesto, así
    que es la cota alta de agrupación.

### Recuentos de T8 para T9

Ejecutado sobre `%TEMP%\catalogo_0677.json` (T2 repetida), umbrales por
defecto de D-22. **Solo recuentos**:

| | Obra 0677 | Todo `auxofc` |
|---|---:|---:|
| Oficios | 31 | 130 |
| Propuestas | 3 (3 grupos enteros de 2) | 12 (12 grupos enteros: 9 de 2, 1 de 3, 2 de 4) |
| Pares por motivo: `mismo_nombre` / `plural` / `errata` / `incluido` | 1 / 1 / 0 / 1 | 11 / 3 / 9 / 1 |
| Componentes que no son clique (R79) | 0 | 0 |

| Plantilla de la 0677 | Sin grupos | Con lo propuesto en la obra confirmado | Con lo propuesto en `auxofc` confirmado |
|---|---:|---:|---:|
| Opciones de `Oficio` | 31 | 28 | 28 |
| Grupos con más de un código en la obra (futuros `oficio_ambiguo`) | 0 | 3 | 3 |
| Pares de `Proveedor` | 36 | 36 | 36 |
| Oficios con un solo proveedor que resuelve (R91 los rellenaría) | 20 | 18 | 18 |
| Oficios sin ningún proveedor | 3 | 1 | 1 |

Lo que sale para la PARADA T9:

- **D-19** (oficio ambiguo): confirmar los tres grupos deja **3** oficios que
  entrarían `oficio_ambiguo` cuando la fila no trae proveedor.
- **D-22** (umbrales): en la obra, los tres pares medidos a ojo y ninguno más
  (0 `errata`); en todo `auxofc`, 9 pares por `errata` que alguien debería
  mirar antes de dar el umbral por bueno, y ninguna componente ambigua. Más
  B2-3, B2-4 y B2-6.
- **D-16 / D-17**: 36 pares en la lista de `Proveedor` con y sin grupos. Con
  los grupos, dos de los tres oficios sin proveedor (los que usa el Excel de
  Posventa) pasan a ofrecer los del código gemelo, y elegir uno resuelve el
  oficio al código gemelo (R94).
- **B2-1**: que el humano confirme `Catalogo.PROVEEDOR` sin perfil.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T7, equivalencias** · `.venv/Scripts/python.exe -m pytest tests/test_f036_equivalencias_dominio.py -q`,
antes de tocar `equivalencias.py`:

```text
=================================== ERRORS ====================================
__________ ERROR collecting tests/test_f036_equivalencias_dominio.py __________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_equivalencias_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_equivalencias_dominio.py:27: in <module>
    from domain.models.equivalencias import (
E   ImportError: cannot import name 'PALABRAS_VACIAS' from 'domain.models.equivalencias' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\equivalencias.py)
=========================== short test summary info ===========================
ERROR tests/test_f036_equivalencias_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.26s
```

**T7, opciones** · `.venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_dominio.py -q`,
con los tests de R71, R72 y R92 añadidos y antes de escribir las funciones:

```text
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f036_plantilla_dominio.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_plantilla_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_plantilla_dominio.py:32: in <module>
    from domain.models.equivalencias import (
E   ImportError: cannot import name 'PERFILES' from 'domain.models.equivalencias' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\equivalencias.py)
=========================== short test summary info ===========================
ERROR tests/test_f036_plantilla_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.49s
```

**T8** · `.venv/Scripts/python.exe -m pytest tests/test_f036_medir_catalogos.py -q`,
antes de crear el script:

```text
=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f036_medir_catalogos.py _____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_medir_catalogos.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_medir_catalogos.py:19: in <module>
    from scripts import medir_catalogos_f036 as medir
E   ModuleNotFoundError: No module named 'scripts'
=========================== short test summary info ===========================
ERROR tests/test_f036_medir_catalogos.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.33s
```

Un error de importación solo prueba que el código no existía. Para los tres
requisitos **centrales** de T7 se sustituyó a propósito el código bueno por uno
equivocado, se lanzaron sus tests y se restauró el fichero (script en el
directorio temporal de la sesión; `git status` sin cambios después):

```text
### R82: la componente contradicha se aplica igual
$ .venv/Scripts/python.exe -m pytest tests/test_f036_equivalencias_dominio.py -k r82 -q --tb=line
..F.                                                                     [100%]
================================== FAILURES ===================================
E   AssertionError: assert [['0028'], ['...143', '0200']] == [['0028'], ['...3'], ['0200']]
      
      At index 1 diff: ['0046', '0143', '0200'] != ['0046']
      Right contains 2 more items, first extra item: ['0143']
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_equivalencias_dominio.py:507: AssertionError: assert [['0028'], ['...143', '0200']] == [['0028'], ['...3'], ['0200']]
=========================== short test summary info ===========================
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r82_componente_con_distinto_no_se_aplica_y_avisa
1 failed, 3 passed, 102 deselected in 0.15s

### R78: la clave no quita las palabras vacías
$ .venv/Scripts/python.exe -m pytest tests/test_f036_equivalencias_dominio.py -k "r78 or r79" -q --tb=line
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_equivalencias_dominio.py:346: AssertionError: assert (Propuesta(ca..._pares=False)) == (Propuesta(ca..._pares=False))
=========================== short test summary info ===========================
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Carpinter\xeda de madera-carpinteria madera]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Carpinteria de madera-carpinteria madera]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[CARPINTER\xcdA DE MADERA-carpinteria madera]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Solados y Alicatados M.O.-solados alicatados mo]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Solados y Alicatados M.O-solados alicatados mo]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Solados y Alicatados-solados alicatados]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Mobiliario de cocinas-mobiliario cocinas]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[Fontaner\xeda & Calefacci\xf3n-fontaneria calefaccion]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_clave_de_nombre[El de la las los del e y-]
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_los_tres_pares_medidos_en_la_0677
FAILED tests/test_f036_equivalencias_dominio.py::test_f036_r78_propuestas_de_la_0677
11 failed, 47 passed, 48 deselected in 0.17s

### R92: una opción por código, sin mirar los grupos
$ .venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_dominio.py -k "r92 or r71" -q --tb=line
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_plantilla_dominio.py:622: AssertionError: assert ['Carpintería...adera (0200)'] == ['Carpintería...adera (0143)']
E   AssertionError: assert ['Pintura · P...mplo Ejemplo'] == ['Pintura · P...Ejemplo S.L.']
      
      At index 1 diff: 'Carpinteria de madera (0046) · Carpinterías Ejemplo S.L.' != 'Carpinteria de madera · Carpinterías Ejemplo S.L.'
      Left contains one more item: 'Carpinteria de madera (0143) · Juan Ejemplo Ejemplo'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_plantilla_dominio.py:694: AssertionError: assert ['Pintura · P...mplo Ejemplo'] == ['Pintura · P...Ejemplo S.L.']
=========================== short test summary info ===========================
FAILED tests/test_f036_plantilla_dominio.py::test_f036_r92_r86_grupo_confirmado_es_una_opcion
FAILED tests/test_f036_plantilla_dominio.py::test_f036_r92_grupo_con_codigos_de_fuera_de_la_obra
FAILED tests/test_f036_plantilla_dominio.py::test_f036_r92_dos_grupos_con_la_misma_etiqueta_llevan_sus_codigos
FAILED tests/test_f036_plantilla_dominio.py::test_f036_r71_con_grupo_de_oficio_y_la_tabla_de_15_5
4 failed, 8 passed, 86 deselected in 0.28s
```

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_equivalencias_dominio.py tests/test_f036_plantilla_dominio.py tests/test_f036_importacion_dominio.py tests/test_f036_medir_catalogos.py -q`
→ **385 passed** en 1,66 s (106 + 98 + 168 + 13). Cobertura de rama con
`coverage.py` sobre los módulos del dominio: **100 %** de líneas y ramas
(`equivalencias.py` 216 líneas y 70 ramas, `plantilla_incidencias.py` 150 y 30,
`importacion.py` 292 y 98).

### Mutación

1. **Mutación rápida, orientativa**, mientras se escribía: el mutador del
   arnés (`harness.mutacion.generar_mutantes`) sobre las líneas de T7 y T8,
   juzgando cada mutante solo con los tests de la tarea. Destapó y se
   cerraron:
   - `if not clave_a or not clave_b` → `and`: **equivalente** (un nombre sin
     clave frente a otro con ella no cumple ningún motivo por sí solo). Se
     reescribió la guarda (`return {MISMO_NOMBRE} if clave_a else ∅` dentro de
     la igualdad) en vez de justificarlo.
   - `while padre[n] != n` → `==`: bucle infinito (timeout). Se cambió a
     recorrido en anchura (B2-15).
   - En el script: `sys.path.insert(0, …parents[1])` (índices equivalentes) →
     `sys.path.append(…parent.parent)` y un test que lo lanza como script en un
     subproceso; la fecha fija de las decisiones hipotéticas (cualquiera vale)
     → `datetime.min`; `frozen=True` de sus tres `dataclass`, `required=True`
     de `--catalogo` y el `or 'ninguna'` de la salida → tests nuevos.
   Resultado final: equivalencias + opciones 78 mutantes, 0 supervivientes;
   script 24 mutantes, 0 supervivientes.
2. **Campaña oficial** sobre las líneas de T7–T8 (alcance contra `9e9510f`,
   el cierre del Bloque 1, cuya campaña ya estaba cerrada):
   `python -m harness.mutacion --feature F-036 --base 9e9510f --workers 6 --timeout 400 --salida progress/mutacion_F-036_bloque2.md`.
   Resultado: **101 mutantes, 101 muertos, 0 supervivientes, 0 timeouts**,
   1.753,3 s con 6 workers (informe completo en
   `progress/mutacion_F-036_bloque2.md`; `progress/mutacion_F-036.md` se deja
   como está, con la campaña del Bloque 1). Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | 385 passed en 1,66 s (T7: `equivalencias` 106 + `plantilla` 98 + `importacion` 168; T8: 13) |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 5,94 s; servicio `api`: **4914 passed, 52 skipped** en 182,63 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 944 líneas cambiadas cubiertas (943/944, umbral 80%, nivel critico)`. La que falta es `raise SystemExit(main())` del script: se ejecuta en el test que lo lanza en un subproceso, que `coverage` no mide |
| Mutación | 101 generados sobre las líneas de T7–T8, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque2.md`); los huecos que destapó la mutación rápida se cerraron antes, con tests o quitando el código equivalente |
| Tiempo de la suite | `api` 182,63 s (máquina cargada; 111,64 s en el `init.sh` previo del mismo día); campaña 1.753,3 s |
| Lint | `ruff check` y `ruff format` sin avisos en los ficheros tocados (el total del árbol, 61, es deuda previa) |
| MANUAL pendiente | Ninguna de T7/T8. **T9 · PARADA** del líder con el humano |

### Qué queda fuera y qué falta

- **T9** entera (PARADA): D-19, D-22, D-16 y D-17 con los recuentos de arriba,
  y la confirmación de B2-1.
- Nada de proveedores ni de actividades (F-050, F-039): ni perfil, ni
  `mismo_cif`, ni formas jurídicas, ni `cobertura.py`.
- `EquivalenciasPort`, las rutas `/api/catalogos/*` y la pantalla son de T15,
  T19, T21 y T22; el `CHECK` y su intercalación (B2-14), de T14.

## Bloque 3 (T10–T11) · 2026-09-29 · hecho

> **Resumen para el líder.** T10 (`d99478e`) y T11 (`46762f1`) hechas, con
> `[x]` en `tasks.md`; más tres ajustes: `f8c5200` (lo que destapó la mutación
> rápida) y `920a596` (un GUID inventado en un test; **aviso para el humano**
> abajo, en la decisión B3-12) y `6992dda` (un test de cobertura). `openpyxl` 3.1.5 y `defusedxml` 0.7.1 en
> `requirements.txt` e instalados en el `.venv` del servicio. Campaña de
> mutación de T10–T11: **138 mutantes, 138 muertos, 0 supervivientes, 0 timeouts**. `bash harness/init.sh` en verde. No se ha
> tocado T12 ni nada fuera del Bloque 3.

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `requirements.txt` | T10 | `openpyxl>=3.1,<4.0` y `defusedxml>=0.7,<1.0` (§2.2) |
| `domain/ports/hoja_calculo.py` (nuevo) | T10 | `FilaPlantilla`, `GeneradorPlantillaPort` y `LectorPlantillaPort` (§5.2), tal cual el diseño |
| `infrastructure/documentos/excel_openpyxl.py` (nuevo) | T10, T11 | `GeneradorPlantillaOpenpyxl` (plantilla, Excel de errores y migración) y `LectorPlantillaOpenpyxl`. Único módulo del servicio que importa `openpyxl` |
| `domain/models/plantilla_incidencias.py` | T11 | `MAX_BYTES_FICHERO = 2 MiB` (D-11, R15), junto a los demás topes (decisión B3-9) |
| `tests/utiles_plantilla.py` (nuevo) | T10 | Catálogo **inventado** de la 0677, opciones calculadas como lo hará la aplicación, `generar()` y `abrir()` en memoria; lo comparten los dos ficheros de tests |
| `tests/test_f036_excel_generador.py` (nuevo) | T10 | 78 tests: R2–R7, R12, R62–R65, R71/R92 y la disposición de §3.1 |
| `tests/test_f036_arquitectura.py` (nuevo) | T10 | 10 tests: dominio sin `openpyxl`/`defusedxml`/`httpx`/`psycopg`; `openpyxl` solo en `excel_openpyxl.py` (y `scripts/`); dominio de F-036 sin reloj; el puerto solo conoce el dominio; las dos líneas de `requirements.txt` |
| `tests/test_f036_excel_lector.py` (nuevo) | T11 | 74 tests: R15–R20 a nivel de bytes, formato antiguo con las primeras filas de la muestra, tipos de celda (R32), R23, ida y vuelta y R66 |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T10, T11 | `[x]` |

Ningún `.xlsx` en disco ni en git: todos los libros se construyen y se
reabren en memoria (`io.BytesIO`). Ningún nombre de proveedor real: los de
los tests son «Carpinterías Ejemplo S.L.», «Mamparas Ejemplo S.A.» y «Juan
Ejemplo Ejemplo».

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B3-1 · Todo texto se escribe como texto** (R7): `openpyxl` convierte en
   fórmula cualquier cadena que empiece por `=`, así que cada celda de texto
   se escribe con tipo cadena y el **prefijo de comilla** (lo que hace Excel
   con `'=…`), también en `_catalogos`, `_plantilla` e «Instrucciones». Un
   test recorre el XML de las cuatro hojas y exige que no haya ningún `<f>`,
   con nombres de unidad, oficio, proveedor y obra que empiezan por `=`, `+`,
   `-` y `@`.
2. **B3-2 · Celdas de datos en formato texto (`@`)**, filas 2–1001,
   columnas A–H, además de desbloqueadas: lo que se teclea no se convierte en
   fecha, número ni fórmula, que es justo lo que R32 rechaza después. No lo
   pide la spec con esas palabras; es la forma barata de que R32 salte menos.
3. **B3-3 · Lista vacía = columna que solo admite el blanco.** Una validación
   de lista no puede apuntar a un rango vacío. Con la obra sin oficios (R12)
   —y también con oficios pero **ningún** proveedor en `obrofc`, o sin
   unidades— la columna lleva una validación «longitud = 0» en estilo
   «detener», con los mismos mensajes. La línea de `sin_oficios` va en
   «Instrucciones» solo cuando no hay oficios.
4. **B3-4 · Protección (§3.3).** Sin contraseña; permitidos insertar y borrar
   filas, ordenar y filtrar; lo demás protegido. **Riesgo para T28 (MANUAL)**:
   Excel no deja *borrar* una fila, ni ordenar un rango, que tenga celdas
   bloqueadas, y la columna `Errores` lo está (R2). Puede que en Excel real
   «borrar fila» y «ordenar» no funcionen en la hoja protegida. Lo dice la
   spec y no se puede comprobar sin Excel: que el humano lo mire en T28 y, si
   molesta, se decide entre desbloquear `Errores` o aceptar la limitación.
5. **B3-5 · Filtro automático sobre `A1:I1001`**, no solo sobre la cabecera:
   con el rango solo en la fila 1 Excel no sabe qué filas filtrar.
6. **B3-6 · «Mensaje de entrada en la cabecera» (§3.1)** se lee como el mensaje
   de entrada de la validación de cada columna (filas 2–1001), que es lo que
   dice el paréntesis del diseño; la cabecera no lleva validación propia.
7. **B3-7 · Excel de errores = `importacion_origen` presente.** Con filas y
   sin `importacion_origen` (la migración) no se añade el párrafo de §3.5 ni
   la clave en `_plantilla`. Las celdas marcadas llevan relleno naranja claro y
   un comentario de 300 × 120 px (autor «Posventa»). Una columna que no es de
   la plantilla en `valores` o `errores` (incluida la de errores) y más de
   1000 filas son `ValueError` sin nombrar el valor.
8. **B3-8 · R65** (nombre `incidencias_<obra>_errores_<AAAAMMDD-HHMM>.xlsx` y
   `excel_errores {nombre, contenido_b64}`) **no es del generador**: se compone
   en el paso 6 de §7.3 (T17) y lo prueban los tests HTTP (T18). Aquí solo se
   comprueba que los bytes son un ZIP que sobrevive a base64 y se reabre.
9. **B3-9 · `MAX_BYTES_FICHERO` en el dominio y comprobado también en el
   lector.** R15 es del borde (T18: «se compara el tamaño antes de construir
   nada»), pero `tasks.md` pide R15 «a nivel de bytes» en T11. El tope va con
   los demás de D-11 en `plantilla_incidencias.py`, para que el handler de T18
   use el mismo, y el lector lo aplica también (defensa en profundidad):
   `FicheroDemasiadoGrande` sin mirar nada más.
10. **B3-10 · Comprobaciones del ZIP (§5.2, pasos 1–2).** Firma `PK\x03\x04`;
    ZIP que no abre → `no_es_xlsx`; > 500 entradas o > 20 MiB **declarados** →
    `fichero_sospechoso`; `vbaProject.bin` en **cualquier** carpeta y sin
    distinguir mayúsculas → `contiene_macros` (el diseño dice
    `xl/vbaProject.bin`; ampliarlo no cuesta nada y cierra un rodeo). El tamaño
    declarado sí acota lo que `openpyxl` descomprime luego: `zipfile` no lee
    más allá de él y lo que no cuadra falla por CRC. Un test prueba que en
    esos rechazos `openpyxl` **ni se llama**. Cualquier excepción al abrir con
    `openpyxl` (XML con entidades, partes que faltan) → `no_es_xlsx`; hay test
    con un `DOCTYPE` con entidad externa inyectado en la hoja.
11. **B3-11 · Lo que lee el lector.** Metadatos por **clave**, no por
    posición; con clave repetida, la primera. `version` solo vale si es un
    número entero (ni `"1"` ni `True` ni `1.5`); `identificador` y
    `obra_codigo` solo si son texto. Forma antigua (R17) **solo** sin
    `_plantilla`, en la primera hoja: ninguna celda de `A1:I1` es una columna
    de la plantilla (recortada), texto no en blanco en `A1`, `D1` y `E1`, y
    `A2:A10` vacías. Filas: columnas A–H (la de errores **ni se lee**, R66);
    entra la fila si alguna celda tiene dato con el mismo criterio que el
    dominio (solo blancos = vacía; una fórmula nunca lo es); dentro de la fila
    se guardan todas las celdas no `None`, también las que son solo blancos,
    para reescribirlas tal cual (R63). Celdas: fórmula (también matricial) →
    su texto con `=`; fecha → ISO (`2026-09-29`, o con hora
    `2026-09-29 10:15:00`; hora sola `10:15:00`); booleano →
    `VERDADERO`/`FALSO`; número → su texto (`12`, `3.5`, `4`). Valores de
    error de Excel (`#N/A`) → texto.
12. **B3-12 · AVISO PARA EL HUMANO: un GUID inventado entró en un commit
    local.** `tests/utiles_plantilla.py` llevaba en `d99478e` (T10) un
    `UUID("12345678-1234-…")` literal para el `importacion_id` de los tests.
    Es inventado, pero `test_f006_arquitectura.py` (R26) prohíbe cualquier
    GUID en el servicio y pide avisar si llega a commitearse. Se sustituyó por
    `UUID(int=0x1234)` en `920a596`. Sigue en el historial de la rama (local,
    sin push). No se ha reescrito la historia: si el humano lo quiere fuera,
    es un `rebase` antes del merge.
13. **B3-13 · Consecuencia del B3-12 para la mutación**: la primera campaña
    oficial (sobre `f8c5200`) dio 138/138 muertos, pero **no vale**: con el
    GUID dentro, `test_f006_arquitectura.py` fallaba antes de llegar a los
    tests de F-036, y con `-x` cualquier mutante «moría» por eso. Se descartó
    su informe y se repitió sobre `920a596` (abajo).
14. **B3-14 · Código equivalente quitado en vez de justificarlo** (lo destapó
    la mutación rápida): `tzinfo is None or utcoffset() is None` →
    `utcoffset() is None`; `keep_vba=False` → valor por defecto (los libros
    con macros ya se rechazaron en el paso 2); `zip(..., strict=True)` y
    `fila[0].row` → índices y numeración con `enumerate(start=2)`; la cabecera
    con `ws[1]` en vez de `next(iter_rows(max_row=1))`.
15. **B3-15 · Velocidad de los tests.** Generar y reabrir la plantilla cuesta
    del orden de 0,3–0,6 s (9.000 celdas con estilo). Los tests que solo leen
    el libro por defecto comparten uno (`functools.cache`); la plantilla vacía
    del lector, también (son bytes). Suite de los dos ficheros: ~40 s.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T10** · con el puerto escrito y un generador esqueleto que devolvía un libro
vacío de `openpyxl`, y sin tocar `requirements.txt`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_arquitectura.py -q`

```text
FAILED tests/test_f036_excel_generador.py::test_f036_r2_hojas_en_orden_con_su_estado_e_incidencias_activa
FAILED tests/test_f036_excel_generador.py::test_f036_r2_cabecera_exacta_en_la_fila_1_y_nada_mas
FAILED tests/test_f036_excel_generador.py::test_f036_r2_paneles_inmovilizados_bajo_la_cabecera_y_filtro
[… 64 líneas FAILED más, una por test de R2–R7, R12, R62–R65, R92 …]
FAILED tests/test_f036_arquitectura.py::test_f036_arquitectura_dependencias_nuevas_en_requirements[openpyxl>=3.1,<4.0]
FAILED tests/test_f036_arquitectura.py::test_f036_arquitectura_dependencias_nuevas_en_requirements[defusedxml>=0.7,<1.0]
70 failed, 12 passed in 19.00s
```

Los 12 que pasaban eran los de arquitectura que ya se cumplían (dominio sin
`openpyxl`, sin reloj, el puerto…) y los que no dependen del libro. Una muestra
de los fallos (`-k "r2_hojas_en_orden or r6_metadatos_de_la or r3_el_desplegable_sale_de_la_hoja_de_catalogos and Unidad or r64_celdas"`):

```text
E       AssertionError: assert ['Sheet'] == ['Incidencias... '_plantilla']
E         At index 0 diff: 'Sheet' != 'Incidencias'
E         Right contains 3 more items, first extra item: 'Instrucciones'
E       KeyError: 'Worksheet Incidencias does not exist.'
E       KeyError: 'Worksheet _plantilla does not exist.'
E       KeyError: 'Worksheet Incidencias does not exist.'
4 failed, 68 deselected in 3.52s
```

**T11** · con `LectorPlantillaOpenpyxl.leer` como esqueleto que levantaba
`NotImplementedError`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_lector.py -q`

```text
_______________ test_f036_r16_con_macros_se_rechaza_sin_abrirlo _______________

sin_openpyxl = None

    def test_f036_r16_con_macros_se_rechaza_sin_abrirlo(sin_openpyxl) -> None:
        contenido = _zip({"xl/vbaProject.bin": b"\0" * 10}, base=generar())
>       assert _rechazo(contenido) == "contiene_macros"
tests\test_f036_excel_lector.py:65: in _rechazo
    _leer(contenido)
E       NotImplementedError
_________________ test_f036_r17_formato_antiguo_de_la_muestra _________________

    def test_f036_r17_formato_antiguo_de_la_muestra() -> None:
>       libro = _leer(_formato_antiguo())
    def leer(self, *, contenido: bytes):
>       raise NotImplementedError
E       NotImplementedError
[…]
69 failed, 1 passed in 30.92s
```

El que pasaba es `test_f036_r16_defusedxml_esta_debajo_de_openpyxl`, que mira
la instalación y no el lector.

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_arquitectura.py -q`
→ **162 passed** (78 + 74 + 10) en 52,23 s (el 162.º es el test de las dos líneas que la campaña dejó sin cubrir, `6992dda`). Con los del dominio de F-036
(`plantilla_dominio`, `importacion_dominio`): 419 passed en 48,19 s. Suite
entera del servicio (`pytest -x`): **5077 passed, 52 skipped** en 90,63 s.

### Mutación

1. **Mutación rápida, orientativa**: el mutador del arnés
   (`harness.mutacion.generar_mutantes`) sobre las líneas del Bloque 3 (diff
   contra `b98bc3a`), juzgando cada mutante solo con los tests de T10/T11 y
   del dominio del contrato, en seis copias del servicio fuera del árbol.
   Primera pasada (sobre `46762f1`): **143 mutantes, 40 vivos**, 833 s:
   - 9 anchos de columna de «Incidencias», 15 de la disposición de
     «Instrucciones» (fila de inicio, columna, saltos, negritas, tamaño del
     título, anchos), 2 del tamaño del comentario, 2 de la fila de nombres de
     `_catalogos`, el prefijo de comilla y 4 del texto del 413: **huecos
     reales** (nada los miraba). Tests nuevos: anchos exactos, disposición
     exacta de «Instrucciones», fila 1 de `_catalogos` y columna de cada
     rango con nombre, tamaño del comentario en el VML, prefijo de comilla y
     el motivo «El fichero pasa de 2 MiB.».
   - 2 de la forma antigua (`range(1, …)` → `range(2, …)` y `+ 1` → `- 1`):
     **hueco real**; tests nuevos con la cabecera en `A1` y en `I1`.
   - 5 **equivalentes**, quitados en vez de justificados (B3-14).
   Segunda pasada (sobre `f8c5200`): **138 mutantes, 0 vivos**, 575 s.
2. **Campaña oficial** sobre las líneas de T10–T11 (alcance contra `b98bc3a`,
   el cierre del Bloque 2, cuya campaña ya estaba cerrada), con tope de 90
   minutos (`timeout 5400`) y sin dejarla en segundo plano al entregar:
   `python -m harness.mutacion --feature F-036 --base b98bc3a --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque3.md`.
   La primera, sobre `f8c5200`, no vale (B3-13). La buena, sobre `920a596`:
   **138 mutantes, 138 muertos, 0 supervivientes, 0 timeouts**, 3.017,2 s
   con 6 workers (informe en `progress/mutacion_F-036_bloque3.md`;
   `progress/mutacion_F-036.md` y `…_bloque2.md` se dejan como están).
   Nada que analizar. `6992dda` solo añade un test, así que no cambia el
   alcance mutado.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T10: 78 + 10; T11: 74. **162 passed** en 52,23 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 10,15 s; servicio `api`: **5078 passed, 52 skipped** en 377,95 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 1266 líneas cambiadas cubiertas (1265/1266, umbral 80%, nivel critico)`. La que falta es la de siempre: `raise SystemExit(main())` del script de T8, que se ejecuta en un subproceso que `coverage` no mide. Las dos que faltaban tras la campaña (el decimal entero en `_entero` y `_numero_como_texto`, que `openpyxl` nunca devuelve pero otro programa sí puede escribir) se cubrieron en `6992dda` |
| Mutación | 138 generados sobre las líneas de T10–T11, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque3.md`); los 40 vivos de la mutación rápida se cerraron antes, 35 con tests y 5 quitando código equivalente |
| Tiempo de la suite | `api` 377,95 s en `init.sh` (máquina cargada; 90,63 s con `pytest -x` suelto); tests de T10–T11: 52,23 s; campaña 3.017,2 s; mutación rápida 833 s + 575 s |
| Lint | `ruff check` y `ruff format` sin avisos en los ficheros tocados |
| MANUAL pendiente | Ninguna de T10/T11. Para **T28**: abrir la plantilla en Excel y comprobar desplegables, protección, «borrar fila» y «ordenar» con `Errores` bloqueada (B3-4) |

### Qué queda fuera y qué falta

- Nombre del Excel de errores y su viaje en base64 (R65): T17 y T18 (B3-8).
- La comprobación del tamaño en el borde (R15, 413): T18, con
  `MAX_BYTES_FICHERO`.
- Componer las `FilaPlantilla` del Excel de errores desde las `FilaConError`
  (valores originales, texto «Fila N del fichero subido · …»): paso 6 de
  §7.3, T17.
- La prueba en Excel real, Excel en la web y LibreOffice: T28 (MANUAL).
- **Aviso al humano** del GUID inventado en el historial local (B3-12).

## Bloque 4 (T12–T13) · 2026-09-30 · hecho

> **Resumen para el líder.** T12 (`59f6a50`) y T13 (`db8acdc`) hechas, con
> `[x]` en `tasks.md`; más `37d6626` (tres tests que destapó la mutación). Solo `POST /api/sql/read`, dos lecturas (unidades y
> `obrofc`), sin marca de CIF, sin actividades ni árbol (quinta enmienda).
> Tests sin red, con el `ClienteFalso` de `tests/utiles_sigrid.py` y un doble
> del puerto en memoria; ningún GUID literal. `bash harness/init.sh` en verde.
> Mutación de T12–T13: **29 mutantes, 29 muertos, 0 supervivientes, 0 timeouts** (la primera pasada dejó 4 vivos, huecos reales cerrados con tests). No se ha tocado T14 ni nada fuera
> del Bloque 4. **Para el humano**: las dos consultas no se han ejecutado nunca
> contra Sigrid real tal cual (B4-1, B4-2); la primera prueba es la descarga de
> la plantilla de la 0677 en T29, paso 2.

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `domain/ports/catalogo_obra.py` (nuevo) | T12 | `FilaUnidadCatalogo` (`obra_ref` fuera del `repr`), `FilaOficioCatalogo` (sin marca de CIF), `LecturaCatalogo[filas, llego_al_techo]` y `CatalogoObraPort` con **dos** métodos (`leer_unidades`, `leer_oficios`), §5.1 |
| `infrastructure/sigrid/consultas_catalogo.py` (nuevo) | T12 | `SQL_UNIDADES_DE_LA_OBRA` y `SQL_OFICIOS_DE_LA_OBRA` **literales de §6.3**, `select_*` (un `?` cada una) y el mapeo de filas. Puro: sin `httpx` ni cliente |
| `tests/test_f036_consultas_catalogo.py` (nuevo) | T12 | 45 tests: SQL carácter a carácter, un solo `SELECT` sin escritura, un `?`, ni `prv`/`cif`/`conact`/`auxpronat`/`DENSE_RANK` en el SQL ni en el módulo, parámetros sin interpolar, mapeo (texto, nulos, códigos que no se vuelven número, sin recortar), fila sin proveedor, fila sin `obra_ref` o sin oficio, nueve formas de fila mal formada, el puerto con dos métodos, los campos del diseño y la inmutabilidad de las dos filas y la lectura |
| `infrastructure/sigrid/catalogo_obra.py` (nuevo) | T13 | `AdaptadorCatalogoSigridApi` (calco de la forma de `ubicacion.py`), `exigir_entorno_con_catalogo`, `RUTA_LECTURA = "/api/sql/read"`, `MAX_FILAS_CATALOGO = 1000`. Importa de `cliente.py` solo la fontanería de lectura |
| `infrastructure/sigrid/fabrica.py` | T13 | `construir_catalogo_obra(ajustes)`: entorno → configuración, sin mirar interruptores; su línea en la docstring de cabecera y en `__all__` |
| `application/pipelines/catalogo_obra.py` (nuevo) | T13 | `leer_catalogo(puerto, codigo_obra) -> CatalogoObra` (§7.1): R9, R10, R12 y la composición del catálogo |
| `tests/test_f036_adaptador_catalogo.py` (nuevo) | T13 | 62 tests: R48 (entornos, lista importada, ni `CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO`, en el adaptador y en la fábrica), cuerpo de las dos lecturas, techo (999/1000/1001 filas, con y sin `truncated`), cortada por debajo del techo, R11 (transitorios, cortes de red, definitivos, respuestas mal formadas, fila mal formada, mensajes sin clave/URL/cuerpo), R46 (solo `sql/read`, imports), R47 en los logs (y la duración, no la hora), la fábrica (orden de las puertas, configuración incompleta, paso de ajustes, log) y el cliente HTTP perezoso |
| `tests/test_f036_catalogo_aplicacion.py` (nuevo) | T13 | 33 tests: composición de la 0677 inventada, R9 (normaliza; inadmisible → sin llamar a Sigrid), oficios distintos y ordenados, proveedores fila a fila, unidades sin código, R10 (cero, ambigua, techo en cada lectura y su orden), R11 (el fallo sube tal cual), R12, R47, hexagonal, y dos de punta a punta con el adaptador real sobre el `ClienteFalso` |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T12, T13 | `[x]` |
| `progress/mutacion_F-036_bloque4.md` (raíz, nuevo) | T12, T13 | Informe de la campaña de mutación del Bloque 4 |

No se han tocado `cliente.py`, `ubicacion.py`, `consultas_ubicacion.py`,
`UbicacionPort` ni nada de F-013 (§2.3).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B4-1 · El SQL es el de §6.3, al carácter; el de `infra/26` es su
   ensayo.** Las unidades son las de `infra/26` sin los alias y con
   `ORDER BY u.cod` (en `infra/26`, `ORDER BY v.obride, u.cod`; el diseño manda
   y el orden de filas no decide nada, solo lo hace determinista). La de
   oficios toma de `infra/26` el `FROM dbo.obrofc` + `JOIN dbo.auxofc` y el
   filtro de baja `ISNULL(a.fecbaj, 0)`; el `LEFT JOIN dbo.con p ON p.ide =
   f.prvide` **no se ensayó** tal cual en T2. Con `prvide` a 0 (lo medido: «a 0
   o nulo es una fila sin proveedor») no casa ningún `con` y sale `NULL`, que
   es la fila sin proveedor. Se comprobará en T29 (paso 2: los pares, y
   ninguno para `0133`, `0144` y `0166`).
2. **B4-2 · `obra_ref` vuelve a Sigrid como texto.** El diseño la define
   texto y opaca, y `leer_oficios(obra_ref: str)`; el adaptador la manda tal
   cual en `parameters` (`["987654321"]`). `infra/26` la mandaba como `[long]`.
   En SQL Server, `f.obride = ?` con un `nvarchar` convierte **el parámetro** a
   `int` (el `int` tiene más precedencia), así que la comparación vale y no
   estropea el índice. **No verificado contra Sigrid**: si fallara, sería un
   503 `CatalogoNoDisponible` con el código de la pasarela, visible y no
   silencioso; se ve en T29, paso 2. No se convierte a entero en el código
   para no decidir sobre una referencia que el diseño declara opaca.
3. **B4-3 · El techo lo marca el adaptador por número de filas.**
   `llego_al_techo = len(filas) >= 1000`, diga lo que diga `truncated` (con
   1.000 filas no se sabe si hay más). Una respuesta con `truncated` y menos de
   1.000 filas es `CatalogoNoDisponible` y no se devuelve (el patrón de F-013).
   Quien decide qué es el techo (409 `catalogo_sin_verificar`) es la
   aplicación.
4. **B4-4 · Una unidad sin código no entra en el catálogo** (hueco de la
   spec). `FilaUnidadCatalogo.unidad_codigo` admite `None` (§5.1) y §7.1 no
   dice qué hacer. Se deja fuera (no se puede ofrecer ni crear nada en ella en
   Sigrid) y se cuenta en el log (`unidades_sin_codigo=N`); si no queda
   ninguna, `ObraSinUnidades`. Las obras se cuentan **antes** de quitarlas:
   una segunda obra sin códigos sigue siendo otra obra (`ObraAmbigua`). La
   alternativa —503 por un dato roto del ERP— bloquearía la obra entera; si el
   humano la prefiere, es un cambio de dos líneas.
5. **B4-5 · `leer_catalogo` normaliza el código él mismo** con
   `normalizar_codigo_obra` (idempotente): R9 se cumple sin llamar a Sigrid lo
   llame quien lo llame (plantilla, importación, propuestas). El
   `obra_codigo` del catálogo es ese código normalizado —el que casa literal
   con `LTRIM(RTRIM(o.cod))`—, no el `o.cod` en bruto; `obra_nombre` es el
   `o.res` de la primera fila (todas son de la misma obra).
6. **B4-6 · Composición.** Unidades con código y nombre **tal cual** (las
   etiquetas las compone el dominio, R8). Oficios distintos por código,
   ordenados, y con dos nombres para un código el primero que llega (no
   debería pasar; así el resultado solo depende del orden de la lectura).
   Proveedores: una `ProveedorEnObra` por fila de `obrofc`, también las que no
   tienen proveedor, sin deduplicar (el dominio ya deduplica con conjuntos al
   componer los pares).
7. **B4-7 · Los grupos vigentes no se leen en `leer_catalogo`.** §2.1 dice de
   este módulo «le aplica los grupos vigentes», pero §7.1 —más concreto y
   enmendado— fija la firma `leer_catalogo(puerto, codigo_obra)` y dice que
   los grupos «se leen aparte (`EquivalenciasPort`, §15.4)», que es T15. Se
   sigue §7.1; los aplican la plantilla y la importación (T17). Un test fija
   que el módulo no los nombra.
8. **B4-8 · Errores.** Fuera de `dev`/`pro`, `CatalogoNoDisponible` (§5.1:
   «no con el error del cierre»); con configuración incompleta,
   `ConfiguracionSigridIncompleta` (la misma comprobación que
   `construir_ubicaciones`, compartida). Las dos son 503 (R11); el mapeo al
   borde es de T18.
9. **B4-9 · Fila mal formada = catálogo no disponible.** Una fila de `obrofc`
   sin código de oficio, una unidad sin `obra_ref` o una fila con otro número
   de columnas son `ValueError` en el mapeo y `CatalogoNoDisponible` («una
   fila no tiene la forma esperada») en el adaptador: todas o ninguna. Los
   mensajes no llevan la fila (R47).
10. **B4-10 · Logs (R47).** Adaptador: `obra=<código> filas= al_techo=
    segundos=` en las unidades; en los oficios, sin obra (solo tiene
    `obra_ref`). Aplicación: `obra= unidades= unidades_sin_codigo= oficios=
    filas_obrofc=`. Fábrica: el entorno. Tests con `obra_ref`, nombres de
    unidad y de proveedor y códigos de proveedor inventados buscados en todo
    lo registrado.
11. **B4-11 · Duplicación consciente.** `_leer`/`_un_intento`/`_mapear` repiten
    la forma de `ubicacion.py` con otro error (`CatalogoNoDisponible`). El
    diseño pide un «calco» y §2.3 deja F-013 intacto; sacar una base común
    arrastraría `ubicacion.py` a la mutación de F-036.
12. **B4-12 · ruff.** Los ficheros nuevos, sin avisos (`ruff check` y
    `ruff format`). `fabrica.py` conserva su aviso previo de orden de imports y
    su formato (ya estaban en `HEAD`); no se reformatea para no mover líneas de
    F-009 y F-012.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T12** · con `domain/ports/catalogo_obra.py` escrito (los tipos hacen falta
para escribir los tests) y `consultas_catalogo.py` como esqueleto (SQL vacío,
funciones con `NotImplementedError`):
`.venv/Scripts/python.exe -m pytest tests/test_f036_consultas_catalogo.py -q -p no:cacheprovider`

```text
fila = 42

    def fila_a_oficio_catalogo(fila):
>       raise NotImplementedError
E       NotImplementedError

infrastructure\sigrid\consultas_catalogo.py:21: NotImplementedError
=========================== short test summary info ===========================
FAILED tests/test_f036_consultas_catalogo.py::test_f036_t12_sql_unidades_de_la_obra_caracter_a_caracter
FAILED tests/test_f036_consultas_catalogo.py::test_f036_t12_sql_oficios_de_la_obra_caracter_a_caracter
FAILED tests/test_f036_consultas_catalogo.py::test_f036_r46_cada_una_es_un_solo_select_sin_nada_que_escriba[unidades]
[… 27 líneas FAILED más: marcadores, parámetros, mapeo, fila sin proveedor, filas mal formadas …]
FAILED tests/test_f036_consultas_catalogo.py::test_f036_t12_una_fila_con_otra_forma_es_valueerror[oficio_numero]
33 failed, 10 passed in 1.05s
```

Muestra de los fallos (`-k "caracter_a_caracter or sin_proveedor or unidad_texto"`):

```text
E       AssertionError: assert '' == 'SELECT v.obr...RDER BY u.cod'
E         - SELECT v.obride, o.cod, o.res, u.cod, u.res
E         - FROM dbo.upv v
E         - JOIN dbo.con o ON o.ide = v.obride
E         - JOIN dbo.con u ON u.ide = v.ide
E         - WHERE LTRIM(RTRIM(o.cod)) = ?
E         - ORDER BY u.cod
E       AssertionError: assert '' == 'SELECT a.cod... a.cod, p.cod'
E         - SELECT a.cod, a.res, p.cod, p.res
E         - FROM dbo.obrofc f
E         - JOIN dbo.auxofc a     ON a.ide = f.ofcide
E         - LEFT JOIN dbo.con p   ON p.ide = f.prvide
E         - WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0
E         - ORDER BY a.cod, p.cod
E       NotImplementedError
E       NotImplementedError
4 failed, 39 deselected in 0.30s
```

Los 10 que pasaban eran los que miran el puerto (dos métodos, campos,
inmutabilidad, argumentos por nombre), que el SQL del esqueleto no nombra
tablas vetadas y que el módulo es puro.

**T13** · con el adaptador como esqueleto (constructor vacío, lecturas con
`NotImplementedError`), `construir_catalogo_obra` y `leer_catalogo` con
`NotImplementedError`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_adaptador_catalogo.py tests/test_f036_catalogo_aplicacion.py -q -p no:cacheprovider`

```text
FAILED tests/test_f036_catalogo_aplicacion.py::test_f036_t13_de_punta_a_punta_la_referencia_de_la_obra_vuelve_como_llego
FAILED tests/test_f036_catalogo_aplicacion.py::test_f036_r10_de_punta_a_punta_mil_unidades_son_catalogo_sin_verificar
84 failed, 10 passed in 5.97s
```

Muestra (`-k "r10_dos_obras or r48_el_adaptador_se_niega… or leer_las_unidades_es_un_post or r12_una_obra or r48_la_fabrica_construye_igual…"`):

```text
>       with pytest.raises(CatalogoNoDisponible) as fallo:
E       Failed: DID NOT RAISE CatalogoNoDisponible
[… tres veces más, una por entorno …]
>       lectura = adaptador.leer_unidades(codigo_obra="0677")
>       raise NotImplementedError
E       NotImplementedError
>       assert isinstance(construir_catalogo_obra(ajustes), AdaptadorCatalogoSigridApi)
>       raise NotImplementedError
E       NotImplementedError
>       catalogo = leer_catalogo(_obra_0677(oficios=()), "0677")
>       raise NotImplementedError
E       NotImplementedError
>           leer_catalogo(puerto, "0677")
>       raise NotImplementedError
E       NotImplementedError
8 failed, 86 deselected in 1.40s
```

Los 10 que pasaban son estructurales y el esqueleto ya los cumplía: se
construye en `dev`/`pro` y encaja en el `Protocol` (el esqueleto no tenía
puerta), no nombra interruptores ni rutas de escritura, `RUTA_LECTURA`,
`MAX_FILAS_CATALOGO`, los imports de `cliente.py`, la fábrica no nombra
interruptores, la aplicación no importa infraestructura ni nombra los grupos
vigentes.

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_consultas_catalogo.py tests/test_f036_adaptador_catalogo.py tests/test_f036_catalogo_aplicacion.py -q`
→ **137 passed** (43 + 61 + 33) en 2,32 s en `db8acdc`; tras los tres tests
de la mutación (`37d6626`), **140 passed** (45 + 62 + 33) en 2,66 s. Suite
entera del servicio (`pytest -x`, en `db8acdc`): **5219 passed, 52 skipped**
en 179,66 s.

### Mutación

Campaña oficial sobre las líneas de T12–T13 (alcance contra `72dce57`, el
cierre del Bloque 3, cuya campaña ya estaba cerrada), con tope de tiempo
(`timeout 5400` la primera, `timeout 3600` la segunda) y sin dejar nada en
segundo plano al entregar:
`python -m harness.mutacion --feature F-036 --base 72dce57 --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque4.md`.

1. **Primera pasada** (sobre `db8acdc`): **29 mutantes, 25 muertos, 4
   supervivientes, 0 timeouts**, 766,9 s. Los cuatro, **huecos reales**:
   - `domain/ports/catalogo_obra.py:52` y `:81`, `frozen=True` → `frozen=False`
     en `FilaUnidadCatalogo` y `LecturaCatalogo`: solo se comprobaba la
     inmutabilidad de `FilaOficioCatalogo`. Test parametrizado con las tres.
   - `infrastructure/sigrid/catalogo_obra.py:156` y `:176`,
     `time.monotonic() - arranque` → `+`: nada miraba el valor de `segundos=`
     en los logs (el mismo hueco que destapó F-013). Test con el reloj
     parcheado a 10.000 s: la suma daría más de 20.000.
   Los cuatro se comprobaron a mano (mutante aplicado → 1 test en rojo) y se
   commitearon en `37d6626`. El informe de esa pasada se descartó.
2. **Segunda pasada** (sobre `37d6626`): **29 mutantes, 29 muertos, 0
   supervivientes, 0 timeouts**, 807,2 s con 6 workers (informe en
   `progress/mutacion_F-036_bloque4.md`; los de los bloques anteriores se dejan
   como están). Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T12: 45; T13: 62 + 33. **140 passed** en 2,66 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 15,84 s; servicio `api`: **5222 passed, 52 skipped** en 408,36 s (sobre `37d6626`; en `db8acdc`, 5219 en 360,99 s); `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 1449 líneas cambiadas cubiertas (1448/1449, umbral 80%, nivel critico)`. La que falta es la de siempre: `raise SystemExit(main())` del script de T8 (se ejecuta en un subproceso que `coverage` no mide). Los cinco ficheros de producción del Bloque 4, sin ninguna línea sin cubrir |
| Mutación | 29 generados sobre las líneas de T12–T13, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque4.md`); la primera pasada dejó 4 vivos, cerrados con tests en `37d6626` |
| Tiempo de la suite | `api` 408,36 s en `init.sh`; 179,66 s con `pytest -x` suelto; tests de T12–T13: 2,66 s; campaña 766,9 s + 807,2 s |
| Lint | `ruff check` y `ruff format` sin avisos en los ficheros nuevos; `fabrica.py`, su aviso previo (B4-12). `init.sh`: 69 avisos de deuda previa, informativo |
| MANUAL pendiente | Ninguna de T12/T13. Para **T29, paso 2**: la descarga de la plantilla de la 0677 es la primera ejecución real de las dos consultas y del `obra_ref` en texto (B4-1, B4-2) |

### Qué queda fuera y qué falta

- Los grupos vigentes de oficio (`EquivalenciasPort`, T15) y su aplicación a
  las opciones (T17) (B4-7).
- El mapeo de `ObraSinUnidades`, `ObraAmbigua`, `CatalogoSinVerificar`,
  `CatalogoNoDisponible` y `ConfiguracionSigridIncompleta` a 404/409/503 en el
  borde: T18.
- Las lecturas de actividades y su árbol (F-039) y la marca de CIF (F-050):
  fuera de F-036 por la quinta enmienda.
- La prueba contra Sigrid real: T29 (MANUAL).
- Decisión abierta para el humano, si no le vale la opción por defecto: la
  unidad sin código (B4-4).

## Bloque 5 (T14–T15) · 2026-09-30 · hecho; T16 es MANUAL del humano

> **Resumen para el líder.** T14 (`3e35175`) y T15 (`438ce0d`, más `bdafb87`: el test que destapó la mutación) hechas, con
> `[x]` en `tasks.md`. DDL nuevo **solo** en el schema `postventa` y solo con
> las formas que admite la guarda (`CREATE TABLE/INDEX IF NOT EXISTS`); no se
> ha ejecutado contra ninguna base: la suite usa el doble de
> `tests/utiles_pg.py` y la prueba real es T16. Sin
> `proveedor_fuera_de_obrofc`; el `CHECK` de `catalogo` admite `oficio`,
> `proveedor` y `actividad_oficio` (R108). Ningún GUID literal
> (`UUID(int=n)` y `uuid4`). `bash harness/init.sh` en verde. Mutación de T14–T15:
> **74 mutantes, 74 muertos, 0 supervivientes** (la primera pasada dejó 1, hueco
> real cerrado con un test en `bdafb87`). **Tres cosas para el humano**: el `COLLATE "C"` del `CHECK` del par
> (B5-1), la segunda fábrica `construir_equivalencias` (B5-3) y que se han
> ampliado —sin relajarlas— las listas de DDL de los tests de F-005, F-028 y
> F-030 a F-034 (B5-4).

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `infrastructure/persistencia/sql/12_importaciones.sql` (nuevo) | T14 | `postventa.importaciones` e `ix_importaciones_hash (hash_fichero, estado)`, literal de §6.1. `hash_fichero` **no** único; `CHECK ((estado = 'parcial') = (filas_con_error > 0))` |
| `infrastructure/persistencia/sql/13_bandeja_incidencias.sql` (nuevo) | T14 | `postventa.bandeja_incidencias` con `oficio_ambiguo`, `proveedor_ambiguo` (siempre falso en F-036) y los cuatro `CHECK` de tabla; `ux_bandeja_clave` único **parcial** (`WHERE duplicada_de IS NULL`) e `ix_bandeja_obra`. Sin `proveedor_fuera_de_obrofc` ni columna de revisión (R44) |
| `infrastructure/persistencia/sql/14_decisiones_equivalencia.sql` (nuevo) | T14 | `postventa.decisiones_equivalencia`, append-only, sin nombres; `CHECK (catalogo IN ('oficio', 'proveedor', 'actividad_oficio'))`; `CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")` (B5-1); índice del `DISTINCT ON` |
| `tests/test_f036_ddl.py` (nuevo) | T14 | 51 tests: orden y lista, guarda, idempotencia, ni datos ni escrituras en el DDL, todo cualificado, sin binarios, sustitución del esquema, cabeceras, columnas exactas de las tres tablas, cada `CHECK` contra su `Enum` (`EstadoImportacion`, `OrigenIncidencia`, `Urgencia`, `Listado`, `Catalogo` + `actividad_oficio`, `Decision`), los de R99, cuenta de `CHECK`, índices literales |
| `tests/test_f005_ddl_idempotente_texto.py` | T14 | Lista de ficheros ampliada con 12–14; el control D4 («ningún índice único») pasa a «el único índice único del esquema es `ux_bandeja_clave`, y no es de `partes`» (B5-4) |
| `tests/test_f028_ddl_historico.py` | T14 | «11 se aplica el último» pasa a «detrás de 11 van exactamente 12, 13 y 14» (B5-4) |
| `tests/test_f030_veredicto_persistido.py`, `test_f031…f034_alcance_cerrado.py` | T14 | `DDL_DE_F028 + DDL_DE_F036` en la aserción del test sin `git` (B5-4) |
| `domain/ports/bandeja.py` (nuevo) | T15 | `RegistroImportacion` (con la propiedad `estado`; `oid` y nombre de fichero fuera del `repr`), `FilaImportada`, `ResultadoImportacion`, `BandejaPort` (§5.3) |
| `domain/ports/equivalencias.py` (nuevo) | T15 | `EquivalenciasPort` (§15.4); `DecisionPar` sigue en el dominio |
| `infrastructure/persistencia/sentencias_bandeja.py` (nuevo) | T15 | Las nueve sentencias de §6.2 y las traducciones fila → dominio, puras; tope de 500 **también** aquí |
| `infrastructure/persistencia/repositorio_bandeja_pg.py` (nuevo) | T15 | `RepositorioBandejaPostgres` y `RepositorioEquivalenciasPostgres` (B5-2), una transacción por operación con `rollback` |
| `infrastructure/persistencia/fabrica.py` | T15 | `construir_bandeja` y `construir_equivalencias` (B5-3); los cuatro pasos de siempre pasan a `_conexion_con_esquema`, que usa también `construir_repositorio` sin cambiar su comportamiento |
| `tests/test_f036_repositorio_bandeja.py` (nuevo) | T15 | 95 tests con el doble de conexión (detalle abajo) |
| `tests_bbdd/tests/test_f036_bbdd_bandeja.py` (nuevo) | T15 | 15 tests para T16; la suite normal los **salta** (sin `POSTVENTA_PG_TEST_DSN`) |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T14, T15 | `[x]` |
| `progress/mutacion_F-036_bloque5.md` (raíz, nuevo) | — | Informe de la campaña |

No se han tocado `sentencias.py`, `repositorio_pg.py`, `mapeo.py`, `ddl.py`,
`arranque.py`, `conexion.py`, `RepositorioPartesPort` ni ningún `.sql`
anterior (§2.3). Nada se ha ejecutado contra una base real.

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B5-1 · `COLLATE "C"` en el `CHECK` del par** (el aviso B2-14 del Bloque
   2). §6.1 dice `CHECK (codigo_a < codigo_b)`; se escribe
   `CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")`. Motivo: `DecisionPar`
   exige `codigo_a < codigo_b` con el orden de Python (punto de código); con la
   intercalación por defecto de la base (p. ej. `en_US.utf8`) un par con
   letras podría ordenarse al revés y el `INSERT` fallaría con un 503. Con
   `"C"` en UTF-8 el orden es el de los bytes, que es el de Python. Para los
   códigos de oficio de hoy (solo cifras) da igual; importa para F-039 (`A:`,
   `O:`) y F-050. Y hay que decidirlo **ahora**: la guarda del DDL no deja
   cambiar un `CHECK` después. Lo fija `test_f036_r95_el_par_va_en_orden…` y,
   contra la base, `test_f036_b2_14_el_par_sigue_el_orden_de_python` de T16.
   **Si el humano prefiere el literal de §6.1**, es quitar las dos palabras
   antes de desplegar.
2. **B5-2 · Dos clases en `repositorio_bandeja_pg.py`.** §15.4 dice que
   `EquivalenciasPort` se implementa «en `repositorio_bandeja_pg.py`», pero los
   dos puertos llaman `registrar` a su escritura con argumentos distintos: una
   clase no puede tener los dos. Mismo fichero, dos clases, con la
   transacción en una base común.
3. **B5-3 · `construir_equivalencias`, además de `construir_bandeja`.** T15
   solo nombra `construir_bandeja`, pero sin una segunda fábrica el adaptador
   de equivalencias no sería alcanzable desde T19 (que no toca la fábrica).
   Es la misma receta, en una línea. Para no copiar los cuatro pasos, se
   sacan a `_conexion_con_esquema` y `construir_repositorio` la usa también;
   su comportamiento no cambia (lo fijan `test_f005_fabrica.py` y un test
   nuevo del camino feliz, que no existía).
4. **B5-4 · Tests de otras features ampliados, no relajados** (§2.2: «tests
   que fijan la lista de ficheros DDL… se amplían con lo nuevo, **sin**
   relajar lo que comprueban»). Al añadir 12–14 se rompían ocho tests:
   la lista de F-005, el «11 es el último» de F-028, el «ningún índice único»
   de F-005 (D4) y los cinco «no hay ni un fichero de DDL nuevo» de F-030 a
   F-034. Cada uno sigue cazando cualquier fichero o índice único **no
   declarado**; lo único que cambia es que declaran los tres de F-036. El D4
   se reescribe como «el único índice único es `ux_bandeja_clave`, y no es de
   `partes`», que sigue protegiendo `numero_incidencia`.
5. **B5-5 · `unidad_nombre` es la etiqueta de la plantilla**
   (`Opcion.etiqueta`): el nombre de la unidad o, si chocaba con otro,
   `<nombre> (<código>)`, o su código si no tiene nombre (decisión 4 del
   Bloque 1). Es lo único que trae `IncidenciaValida`, y la columna es
   `NOT NULL`.
6. **B5-6 · `creada_at_utc` = `importado_at_utc`** de su importación: todas
   las filas de una importación comparten instante, y así el orden de R45
   («las de la importación más reciente primero y en orden de fila») es el del
   índice `ix_bandeja_obra`. `select_bandeja` desempata además por
   `incidencia_id`, para que el orden no dependa del plan.
7. **B5-7 · El atajo de R39 devuelve la importación completa más antigua**
   (`ORDER BY importado_at_utc, importacion_id LIMIT 1`): dos subidas
   simultáneas pueden dejar dos completas (§5.3), y «el resumen de entonces»
   es el de la que hizo el trabajo.
8. **B5-8 · Qué devuelve `registrar`.** Las `FilaImportada` de las filas
   **válidas**, ordenadas por número de fila; las filas con error no llegan al
   puerto (R42) y las añade quien compone la respuesta (T17). `con_error` sí
   va en el resultado (es `filas_con_error`). Los ids de las filas se generan
   en Python (`uuid4`, inyectable); de la primera de cada grupo se sabe si
   entró por la `clave_duplicado` del `RETURNING` de §5.3.
9. **B5-9 · Una clave que el `ON CONFLICT` saltó y el `SELECT` no ve** no se
   da por buena: `PersistenciaNoDisponible` y `rollback`. No debería pasar (en
   `READ COMMITTED` la otra transacción ya confirmó), pero inventar un estado
   para esas filas sería peor.
10. **B5-10 · Transacciones.** Cada operación, también las lecturas, cierra
    su transacción (`commit` tras leer): una sesión `idle in transaction` en
    el servidor compartido la cortaría `idle_in_transaction_session_timeout`.
    Ante cualquier error, `rollback`; si el `rollback` también falla, se
    registra el tipo y manda el error original. Un error de la base es
    `PersistenciaNoDisponible` con la operación y el tipo, **nunca** los
    parámetros (R47).
11. **B5-11 · Decisiones.** `registrar(decisiones=())` no toca la base;
    `ultimas_decisiones` con menos de dos códigos distintos devuelve `()` sin
    consultar. Los motivos se guardan ordenados y separados por comas
    (`'errata,plural'`), `NULL` si no hay; un motivo que el dominio no conoce
    al leer es `ValueError`. Los códigos van al `ANY(%s)` ordenados y sin
    repetir.
12. **B5-12 · Logs (R47).** `registrar`: `importacion_id`, obra, estado y los
    cuatro recuentos; decisiones: catálogos y número de pares. Ni hash, ni
    nombre de fichero, ni `oid`, ni textos, ni nombre o código de proveedor ni
    de oficio. Lo fijan dos tests con `caplog`.
13. **B5-13 · Los `.sql` van en ASCII**, como los once anteriores (sin
    tildes en los comentarios).

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T14** · sin los tres `.sql`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_ddl.py -q`

```text
FAILED tests/test_f036_ddl.py::test_f036_t14_cada_fichero_lleva_su_cabecera[14_decisiones_equivalencia.sql]
FAILED tests/test_f036_ddl.py::test_f036_t14_las_cabeceras_dicen_de_donde_leen
[… 20 líneas FAILED más …]
FAILED tests/test_f036_ddl.py::test_f036_r108_el_check_de_catalogo_admite_ya_los_tres_catalogos
FAILED tests/test_f036_ddl.py::test_f036_r108_el_check_de_catalogo_cubre_el_enum_del_dominio
FAILED tests/test_f036_ddl.py::test_f036_r81_el_check_de_decision_sale_del_tipo_del_dominio
FAILED tests/test_f036_ddl.py::test_f036_r95_el_par_va_en_orden_con_la_intercalacion_de_python
FAILED tests/test_f036_ddl.py::test_f036_r95_el_indice_da_la_ultima_decision_de_cada_par_por_catalogo
44 failed, 7 passed in 3.81s
```

Muestra (`-k "r108_el_check_de_catalogo_admite or r41_la_no or detras_del_historico or r95_el_par"`):

```text
E       AssertionError: assert ['09_graficos...o_estado.sql'] == ['12_importac...valencia.sql']
E         At index 0 diff: '09_graficos.sql' != '12_importaciones.sql'
tests\test_f036_ddl.py:188: AssertionError
E       FileNotFoundError: [Errno 2] No such file or directory: '…\\infrastructure\\persistencia\\sql\\13_bandeja_incidencias.sql'
E       FileNotFoundError: [Errno 2] No such file or directory: '…\\infrastructure\\persistencia\\sql\\14_decisiones_equivalencia.sql'
E       FileNotFoundError: [Errno 2] No such file or directory: '…\\infrastructure\\persistencia\\sql\\14_decisiones_equivalencia.sql'
4 failed, 47 deselected in 0.70s
```

Los 7 que pasaban son los que fijan a mano los valores de los `Enum`, de
`Decision` y las longitudes del dominio, que no dependen del `.sql`.

Al añadir los tres `.sql`, la suite entera dio **8 failed** (los ocho de B5-4),
que se ampliaron uno a uno.

**T15** · con los dos puertos escritos (los tipos hacen falta para escribir
los tests) y `sentencias_bandeja.py`, `repositorio_bandeja_pg.py`,
`construir_bandeja` y `construir_equivalencias` como esqueletos con
`NotImplementedError` (antes, sin puertos: `ModuleNotFoundError: No module
named 'domain.ports.bandeja'`):
`.venv/Scripts/python.exe -m pytest tests/test_f036_repositorio_bandeja.py -q -p no:cacheprovider`

```text
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_sin_contrasena_la_fabrica_no_abre_nada[construir_bandeja]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_sin_contrasena_la_fabrica_no_abre_nada[construir_equivalencias]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_desde_local_contra_un_host_remoto_no_se_conecta[construir_bandeja]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_desde_local_contra_un_host_remoto_no_se_conecta[construir_equivalencias]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_si_no_se_puede_conectar_es_503[construir_bandeja]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_si_no_se_puede_conectar_es_503[construir_equivalencias]
FAILED tests/test_f036_repositorio_bandeja.py::test_f036_t15_la_fabrica_exporta_las_tres_construcciones
81 failed, 12 passed in 2.99s
```

Muestra (`-k "r41_insert_primeras or r38_una_clave or r40_si_falla_cualquier_paso or r95_el_catalogo_viaja or r70_cero or abre_fija"`):

```text
>           sentencias_bandeja.valores_de_fila(
>       raise NotImplementedError
E       NotImplementedError
>       resultado = _repositorio(conexion).registrar(
>       raise NotImplementedError
E       NotImplementedError
[… cinco veces más, una por paso que falla …]
>       _equivalencias(conexion).ultimas_decisiones(catalogo=Catalogo.PROVEEDOR, codigos=("0046", "0143"))
>       raise NotImplementedError
E       NotImplementedError
>       repositorio = construir(_ajustes())
>       raise NotImplementedError
E       NotImplementedError
10 failed, 1 passed, 82 deselected in 1.09s
```

Los 12 que pasaban son del puerto (métodos, campos, inmutabilidad, la
propiedad `estado` y el `repr`, ya escritos) y el camino feliz de
`construir_repositorio`, que existía.

### Verde

- `.venv/Scripts/python.exe -m pytest tests/test_f036_ddl.py tests/test_f005_ddl_orden.py tests/test_f005_ddl_seguro.py -q` → verde; con los ocho ampliados y `test_f005_ddl_troceado.py`, **311 passed, 22 skipped** en 22,85 s.
- `.venv/Scripts/python.exe -m pytest tests/test_f036_repositorio_bandeja.py -q` → **93 passed** en 0,67 s; con `test_f036_ddl.py`, `test_f005_ddl_*`, `test_f005_fabrica.py` y el de `tests_bbdd`, **203 passed, 15 skipped** en 1,11 s.
- `coverage` de `sentencias_bandeja.py` y `repositorio_bandeja_pg.py` con solo `test_f036_repositorio_bandeja.py`: **100 %** (208 sentencias, 0 sin cubrir).
- Suite entera del servicio (`pytest -q`, en `438ce0d`): **5370 passed, 67 skipped** en 92,95 s.

Qué fija `test_f036_repositorio_bandeja.py`, por requisito: puertos y tipos
(métodos, campos del diseño, inmutables, `estado` de R69/R70, `repr` sin `oid`
ni fichero); cada sentencia al carácter con sus parámetros, sin nada
interpolado y con el esquema validado; el tope de 500 (0, −5, 499, 500, 501,
100 000); `registrar` **completa** (tres sentencias, un `commit`), con
**duplicadas en el fichero** (R37: `duplicada_de` y `duplicada_de_fila`), con
una clave **ya en la bandeja** (R38: todo el grupo fuera, con el id
existente), **reimportar** (R67), **parcial** (R42) y **cero válidas** (R70:
dos sentencias); un fallo en **cada** paso deja `rollback` y ningún `commit`
(R40) sin datos en el mensaje; el `rollback` que también falla; la clave que
no cuadra (B5-9); `uuid4` por defecto; el log (R47); el atajo de R39 (nada,
completa, id en texto, fallo); `listar` (mapeo, ambiguos, web sin
importación, tope, fallo); las decisiones (una sentencia y un `commit`, cero
decisiones, fallo, mapeo de vuelta, el catálogo como parámetro que separa los
mismos códigos —R95—, menos de dos códigos, log); y las tres fábricas.

Lo que prepara `tests_bbdd/tests/test_f036_bbdd_bandeja.py` para T16: DDL dos
veces sin cambios en columnas, índices y restricciones de las tres tablas;
nada en `public`; el índice parcial rechaza la segunda no duplicada
(`UniqueViolation`) y admite la duplicada; reimportar no añade filas y el
listado sale en orden; **dos importaciones simultáneas** (A deja su fila sin
confirmar, B espera en otra conexión, A confirma y B sale `ya_en_bandeja`:
una copia, dos importaciones); el `CHECK` de estado en sus dos sentidos; los
cuatro de R99; las decisiones se acumulan (tres filas) sin mezclar catálogos;
`actividad_oficio` entra y `otro` no; y el par `B1`/`a1` en el orden de Python.
Se ha comprobado que se recoge y se salta (15 skipped); **no** se ha
ejecutado contra ninguna base.

### Mutación

Campaña oficial sobre las líneas de T14–T15 (alcance contra `dd6da93`, el
cierre del Bloque 4, cuya campaña ya estaba cerrada), con tope de tiempo
(`timeout 5400` la primera, `timeout 3600` la segunda) y sin dejar nada en
segundo plano al entregar:
`python -m harness.mutacion --feature F-036 --base dd6da93 --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque5.md`.
Los `.sql` no se mutan (`harness/alcance.py` solo mide `.py`): los fija
`tests/test_f036_ddl.py` al carácter.

1. **Primera pasada** (sobre `438ce0d`): **74 mutantes, 73 muertos, 1
   superviviente, 0 timeouts**, 2044,6 s. El superviviente, **hueco real**:
   `sentencias_bandeja.py:364`, `urgencia=None if fila[14] is None …` →
   `fila[15]`: todas las filas de prueba traían urgencia y listado a la vez, o
   ninguno de los dos, así que mirar la columna del listado para decidir la
   urgencia daba lo mismo. Test nuevo parametrizado (urgencia sin listado y al
   revés); comprobado a mano (mutante aplicado → **2 failed**, `assert None ==
   <Urgencia.SEGURIDAD: 'seguridad'>` y `ValueError: None is not a valid
   Urgencia`) y commiteado en `bdafb87`. El informe de esa pasada se descartó.
2. **Segunda pasada** (sobre `bdafb87`): **74 mutantes, 74 muertos, 0
   supervivientes, 0 timeouts**, 1927,5 s con 6 workers (informe en
   `progress/mutacion_F-036_bloque5.md`). Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T14: 51; T15: 95 (+ 15 de `tests_bbdd`, saltados sin base) |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 4,10 s; servicio `api`: **5372 passed, 67 skipped** en 152,67 s (sobre `bdafb87`); `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 1720 líneas cambiadas cubiertas (1719/1720, umbral 80%, nivel critico)`. La que falta es la de siempre: `raise SystemExit(main())` del script de T8. Los cinco `.py` de producción del Bloque 5, sin ninguna línea sin cubrir |
| Mutación | 74 generados sobre las líneas de T14–T15, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque5.md`); la primera pasada dejó 1 vivo, cerrado con un test en `bdafb87` |
| Tiempo de la suite | `api` 152,67 s en `init.sh`; 92,95 s con `pytest -q` suelto; tests de T14–T15: 0,58 s + 0,72 s; campañas 2044,6 s + 1927,5 s |
| Lint | `ruff check` y `ruff format` (desde la raíz) sin avisos en los ficheros nuevos; en `fabrica.py` solo se formatearon las líneas nuevas |
| MANUAL pendiente | **T16** (abajo) |

### T16 · comando para el humano (PowerShell, desde la raíz del repositorio, con Docker Desktop arrancado)

```powershell
powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
```

Levanta la base efímera local, ejecuta `pytest tests_bbdd` (incluye
`test_f036_bbdd_bandeja.py`, 15 tests) y la tira. Debe acabar sin fallos y
sin ningún `skipped` de `test_f036_bbdd_bandeja.py`. Anotar aquí el resultado.
Si falla `test_f036_b2_14_…`, es la decisión B5-1.

### Qué queda fuera y qué falta

- **T16** (MANUAL, humano): la prueba contra PostgreSQL real.
- La composición de la importación y el Excel de errores (T17), los handlers
  y las rutas (T18, T19): los puertos están listos; `construir_bandeja` y
  `construir_equivalencias` no los llama todavía nadie.
- `docs/INTEGRACION.md` §2 y `azure-apps/postventa_incidencias.md` (las tres
  tablas nuevas): T26. **El DDL nuevo se aplica solo al arrancar la Function
  desplegada** (T27); hasta entonces no existe en `psql-albaranes-rs9k2`.
- Para el humano: B5-1 (`COLLATE "C"`), B5-3 (segunda fábrica) y B5-4 (tests
  de otras features ampliados).


## Bloque 6a (T17–T18) · 2026-09-30 · hecho; T19 y T20 van en otro encargo

> **Resumen para el líder.** T17 (`e0a6494`) y T18 (`7032652`) hechas, con
> `[x]` en `tasks.md`, más `9686cad` (los tests que destapó la mutación). La plantilla y la importación ya
> tienen aplicación (seis pasos, en su orden) y borde HTTP: `GET /api/plantilla`,
> `POST /api/importaciones` y `GET /api/bandeja`, anónimas como las demás.
> Tests con dobles de los puertos (sin red, base ni IA; nada se escribe en
> Sigrid), el lector y el generador de verdad sobre libros en memoria, ningún
> GUID literal (`UUID(int=n)`). `bash harness/init.sh` en verde. Mutación de
> T17–T18: **65 mutantes, 65 muertos, 0 supervivientes** (la primera pasada dejó 17, todos huecos reales, cerrados con tests en `9686cad`). **T16 sigue siendo MANUAL del humano y está
> pendiente**. Cosas para el humano: B6-3 (las decisiones se piden solo entre
> los oficios de la obra), B6-7 (nombres de campo que la spec no fija), B6-9
> (500 con motivo si el YAML se rompe) y B6-13 (la cabecera de
> `function_app.py` y el test de F-010, ampliados).

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `application/pipelines/contexto_importacion.py` (nuevo) | T17 | `ContextoImportacion` (§7.3) con `ya_importado`; `ExcelDeErrores(nombre, contenido)`. Bytes, nombre de fichero, `oid`, libro, catálogo, filas y opciones fuera del `repr` (R47); exige hora con zona |
| `application/pipelines/plantilla.py` (nuevo) | T17 | §7.2: `opciones_de_la_obra` (grupos vigentes de oficio con las decisiones de la obra y `uso_en_obra` = filas de `obrofc`; proveedores, cada código su grupo), `nombre_de_la_plantilla` (fecha UTC) y `generar_plantilla` |
| `application/pipelines/paso_importacion.py` (nuevo) | T17 | Los seis pasos (`paso_huella`, `paso_reconocimiento`, `paso_catalogo`, `paso_validacion`, `paso_registro`, `paso_excel_errores`), `fila_del_excel_de_errores` (R63, R64) y `nombre_del_excel_de_errores` (R65) |
| `tests/utiles_importacion.py` (nuevo) | T17, T18 | Dobles en memoria de `BandejaPort` (se porta como la base: clave única por obra, grupo entero `ya_en_bandeja`, atajo solo de completas), `EquivalenciasPort` y `CatalogoObraPort`, y el lector y el generador de verdad anotando; todos escriben en una lista común de llamadas |
| `tests/test_f036_pipeline_importacion.py` (nuevo) | T17 | 90 tests (79 en T17; 11 tras la mutación) |
| `interface_adapters/api/plantilla.py` (nuevo) | T18 | `descargar_plantilla`: R9 antes de construir nada, adaptadores (Sigrid primero), `configuracion_de_la_plantilla()` (YAML cacheado por proceso) |
| `interface_adapters/api/importar.py` (nuevo) | T18 | `importar_excel` (R22 → nº de ficheros → R15 → composición de los seis pasos) y `serializar_importacion` (R43, R33, R65, R69) |
| `interface_adapters/api/bandeja.py` (nuevo) | T18 | `leer_bandeja` (R45): obra normalizada, `limite` por defecto 200 y acotado a 500, segundo cinturón en el handler, campos de §8 sin `importado_por` |
| `function_app.py` | T18 | Rutas `plantilla` (GET), `importaciones` (POST) y `bandeja` (GET), en `ANONYMOUS`; su entrada en la cabecera; la bandeja en «Qué añade `GET /api/cola`» (B6-13); `_rechazo_de_obra`, `_sin_sigrid_o_sin_base`, `_configuracion_rota` |
| `tests/test_f010_endpoints_protegidos.py` | T18 | `ENDPOINTS` de 12 a 15 (y su cuenta), con la línea de historia; ninguna comprobación cambia |
| `tests/test_f036_plantilla_http.py`, `test_f036_importar_http.py`, `test_f036_bandeja_http.py` (nuevos) | T18 | 24 + 54 + 35 tests (detalle abajo) |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T17, T18 | `[x]` |
| `progress/mutacion_F-036_bloque6a.md` (raíz, nuevo) | — | Informe de la campaña |

No se ha tocado el dominio, los puertos, los adaptadores de T10–T15, las
fábricas ni nada de §2.3. Ninguna variable de entorno nueva (R49).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B6-1 · El contexto guarda las opciones.** Es la decisión 2 del Bloque 1
   (`validar_filas` recibe opciones): `ContextoImportacion` lleva además de los
   campos de §7.3 `opciones_oficio` y `opciones_proveedor`, calculadas una vez
   y usadas en la validación y en el Excel de errores (R62: «el mismo catálogo
   y opciones»). `validas` y `con_error` empiezan en `None` y no en `()`: «sin
   validar» y «ninguna» son cosas distintas (una plantilla vacía se registra,
   completa y con 0 leídas).
2. **B6-2 · Un paso fuera de orden revienta.** §7.3 da el orden pero no dice
   qué pasa si se rompe. Cada paso exige lo que deja el anterior y, si falta,
   `ValueError("paso fuera de orden: …")` **antes** de tocar ningún puerto. Así
   el orden se puede probar paso a paso y, sobre todo, nadie genera un Excel
   de errores sin `resultado` del registro (R40). Con `ya_importado`, los pasos
   2–6 devuelven el contexto sin hacer nada.
3. **B6-3 · Las decisiones de oficio se piden solo entre los oficios de la
   obra** (para el humano, afecta también a T19). `EquivalenciasPort.
   ultimas_decisiones(codigos=…)` devuelve, por contrato de §15.4 (T15), los
   pares con **los dos** códigos en la lista. Con los códigos de la obra, una
   cadena A–X–B confirmada en otras obras con X fuera de esta **no** une A y B
   aquí, aunque R82/R84 dirían que es una sola componente. Con propuestas por
   cliques (§15.2) confirmar un grupo guarda todos sus pares, así que el caso
   solo sale si se confirman grupos que se solapan en obras distintas. No se
   ha cambiado el puerto (es de T15); si el humano quiere la componente global,
   es pedir las decisiones sin filtrar por obra (o por cierre transitivo) en
   `opciones_de_la_obra` (un cambio pequeño en la aplicación o en la
   consulta).
4. **B6-4 · `opciones_de_la_obra` vive en `plantilla.py`** y la usan la
   plantilla y `paso_catalogo`: el desplegable que se genera y la lista contra
   la que se valida salen de la misma función (la comparación es exacta). La
   etiqueta de un grupo es la del oficio con más filas en `obrofc` de la obra
   (R86) y, a igualdad, la del código menor; lo fija un test con los dos casos.
5. **B6-5 · `filas_leidas` = válidas + con error**, que son las filas no vacías
   del libro (el lector ya descarta las vacías; `validar_filas` también).
6. **B6-6 · El orden de §7.3 tiene una consecuencia**: la huella lee la base
   **antes** de reconocer el fichero, así que con la base caída o sin
   configurar un fichero que no es la plantilla da 503 y no 400. R21 solo
   prohíbe llamar a Sigrid y **escribir** en la base, y se cumple: el catálogo
   y las decisiones se construyen solo si el fichero no estaba importado y se
   ha reconocido (lo fijan tests con fábricas que revientan si se llaman).
7. **B6-7 · Nombres que la spec no fija** (para el humano y para T21):
   - la respuesta de `POST /api/importaciones` lleva **`total_errores`** junto a
     `errores` (R33: «hasta 200 en la lista, más el total»);
   - cada fila lleva **siempre** `duplicada_de_fila` y `existente_id`, a `null`
     si no aplican (R43 escribe `duplicada_de_fila | existente_id`);
   - las filas con error salen en `filas` con `estado: "con_error"`, sin
     identificadores y con `avisos: []`, mezcladas por número de fila;
   - `GET /api/bandeja` responde `{obra, total, incidencias}`.
8. **B6-8 · Los 404/409 de la obra llevan `codigo`** (`obra_sin_unidades`,
   `obra_ambigua`, `catalogo_sin_verificar`, los nombres de R10), como el 400
   de `FicheroNoEsPlantilla`: `{error, codigo}`. En la importación los tres son
   409 (§4.6: la obra que no tiene unidades es 404 solo en la plantilla).
9. **B6-9 · Un YAML roto es 500 con su motivo** (fuera de la tabla de §8). El
   YAML se carga en la primera petición que lo necesita y se cachea por
   proceso (`configuracion_de_la_plantilla`); cargarlo al importar el módulo
   tumbaría también `/api/health`. Si falla, la ruta responde 500 con
   `{"error": …}` en vez del 500 vacío del runtime (el defecto 14 de F-010). No
   puede pasar con el YAML versionado: `test_f036_configuracion_plantilla.py`
   lo carga en cada suite.
10. **B6-10 · Los 400 de la bandeja**: la obra, `CodigoDeObraInvalido`; el
    `limite`, `PeticionDePersistenciaInvalida` (la misma de `GET /api/cola` y
    con el mismo texto). No se añade ningún error al dominio.
11. **B6-11 · `usuario_oid` se recorta**: solo blancos cuenta como vacío (R22) y
    se guarda sin blancos alrededor. El motivo del 400 no repite el `oid`.
12. **B6-12 · Logs (R47).** Los pasos: obra, recuentos e `importacion_id`
    (tampoco el `sha256`, que identifica el fichero de una persona). Las rutas:
    un rechazo del fichero se registra **por su código**, no por su motivo,
    porque el de `cabecera_distinta` repite lo que escribió quien sube en la
    cabecera (hay un test con «Fulanita» en la cabecera: va a la respuesta y
    no al log). La bandeja: la obra y cuántas.
13. **B6-13 · La cabecera de `function_app.py`** (para el humano): además de
    las tres entradas nuevas, «los once endpoints» (ya eran doce) pasa a
    «todos los endpoints», «Los diez restantes» a «Los del circuito de
    partes», y el apartado de la cola dice que `GET /api/bandeja` es el
    **segundo** endpoint que devuelve dato de fuera acumulado, con sus
    cautelas (tope duro de 500 y log de solo recuentos). `test_f010_endpoints_
    protegidos.py` pasa de 12 a 15 rutas **sin quitar ninguna comprobación**;
    tres tests nuevos de F-036 fijan las entradas de la cabecera.
14. **B6-14 · «Exactamente un fichero» cuenta de verdad.** `req.files.values()`
    de `werkzeug` da **uno por campo**: dos ficheros en el mismo campo se
    verían como uno. La ruta usa `req.files.items(multi=True)`.
15. **B6-15 · Conexiones.** Cada petición construye sus adaptadores con las
    fábricas de T13/T15, como el resto de handlers (que tampoco cierran la
    conexión explícitamente). La plantilla construye primero el de Sigrid
    (su puerta de entorno no abre nada) y después el de decisiones.
16. **B6-16 · Dos errores en la misma columna** (no debería pasar: el dominio
    da uno por columna) se juntan con « · » en la marca de la celda; en la
    columna `Errores` salen los dos.
17. **B6-17 · ruff.** Los ficheros nuevos, sin avisos y formateados; en
    `function_app.py` no hay avisos y lo único que `ruff format` cambiaría es
    una línea previa de `remesa`, que no se toca.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T17** · con `contexto_importacion.py` escrito (los tipos hacen falta para
los tests) y `plantilla.py` y `paso_importacion.py` como esqueletos con
`NotImplementedError`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_pipeline_importacion.py -q -p no:cacheprovider`

```text
FAILED tests/test_f036_pipeline_importacion.py::test_f036_t17_los_seis_pasos_llaman_a_los_puertos_en_su_orden
FAILED tests/test_f036_pipeline_importacion.py::test_f036_t17_sin_filas_con_error_no_se_llama_al_generador
FAILED tests/test_f036_pipeline_importacion.py::test_f036_t17_reconocer_sin_huella_es_un_paso_fuera_de_orden
[… 62 líneas FAILED más …]
FAILED tests/test_f036_pipeline_importacion.py::test_f036_r10_r11_si_algo_falla_no_hay_plantilla[catalogo-fallo0]
FAILED tests/test_f036_pipeline_importacion.py::test_f036_r10_r11_si_algo_falla_no_hay_plantilla[catalogo-fallo1]
FAILED tests/test_f036_pipeline_importacion.py::test_f036_r10_r11_si_algo_falla_no_hay_plantilla[equivalencias-fallo2]
FAILED tests/test_f036_pipeline_importacion.py::test_f036_r12_la_plantilla_de_una_obra_sin_oficios_se_genera_igual
FAILED tests/test_f036_pipeline_importacion.py::test_f036_r47_la_plantilla_no_registra_nombres
72 failed, 7 passed in 8.53s
```

Muestra (`-k "seis_pasos or r39_los_mismos_bytes_de_una_completa or r1_la_plantilla_lee or fuera_de_orden and reconocer"`):

```text
>       raise NotImplementedError
E       NotImplementedError
application\pipelines\paso_importacion.py:34: NotImplementedError
>       raise NotImplementedError
E       NotImplementedError
application\pipelines\paso_importacion.py:40: NotImplementedError
>       raise NotImplementedError
E       NotImplementedError
application\pipelines\paso_importacion.py:48: NotImplementedError
>       raise NotImplementedError
E       NotImplementedError
application\pipelines\paso_importacion.py:34: NotImplementedError
>       raise NotImplementedError
E       NotImplementedError
application\pipelines\plantilla.py:50: NotImplementedError
5 failed, 74 deselected in 1.02s
```

Los 7 que pasaban: los dos del contexto (hora con zona, estado inicial), los
tres de arquitectura (qué importa cada módulo), el de la primera línea y el
control de los dobles.

**T18** · con los tres handlers como esqueletos con `NotImplementedError`,
sin rutas en `function_app.py` y con `ENDPOINTS` ya ampliado a quince:
`.venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_http.py tests/test_f036_importar_http.py tests/test_f036_bandeja_http.py tests/test_f010_endpoints_protegidos.py -q -p no:cacheprovider`

```text
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay
111 failed, 10 passed in 10.14s
```

Muestra (`-k "r43_una_importacion_completa or r1_la_plantilla_es_un_xlsx or r45_la_bandeja_devuelve or barrido_de_niveles or r33_la_lista_de_errores_se_corta or lista_las_tres_rutas and bandeja"`):

```text
E       AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'descargar_plantilla'
tests\test_f036_plantilla_http.py:91: AttributeError
E       AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'importar_excel'
tests\test_f036_importar_http.py:169: AttributeError
>       raise NotImplementedError
E       NotImplementedError
interface_adapters\api\importar.py:18: NotImplementedError
E       AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'leer_bandeja'
tests\test_f036_bandeja_http.py:121: AttributeError
E       assert 'GET /api/plantilla' in '# services/postventa-api/function_app.py\n"""Punto de entrada HTTP del servicio …'
tests\test_f036_bandeja_http.py:384: AssertionError
E       assert 'POST /api/importaciones' in '# services/postventa-api/function_app.py\n"""Punto de entrada HTTP del servicio …'
E       assert 'GET /api/bandeja' in '# services/postventa-api/function_app.py\n"""Punto de entrada HTTP del servicio …'
E       assert 12 == 15
tests\test_f010_endpoints_protegidos.py:248: AssertionError
8 failed, 113 deselected in 1.89s
```

Los 10 que pasaban: los tres de R48 (los handlers no nombran ninguna ventana
de escritura), `LIMITE_POR_DEFECTO == 200` y los seis de F-010 que no cuentan
rutas.

### Verde

- `.venv/Scripts/python.exe -m pytest tests/test_f036_pipeline_importacion.py -q` → **79 passed**.
- `.venv/Scripts/python.exe -m pytest tests/test_f036_plantilla_http.py tests/test_f036_importar_http.py tests/test_f036_bandeja_http.py tests/test_f010_endpoints_protegidos.py -q` → **121 passed** (24 + 54 + 35 + 8).
- Suite del servicio suelta: `5570 passed, 42 skipped in 102.20s`.
- Cobertura de los módulos nuevos medida aparte: `contexto_importacion.py`,
  `paso_importacion.py`, `plantilla.py` (aplicación) y los tres handlers,
  **100 %**; en `function_app.py`, todas las líneas nuevas cubiertas.

Qué fijan los tests, además de lo de la tabla de la tarea:

- **T17**: orden de las llamadas a los puertos (lista común); cada paso fuera
  de orden; el `sha256`; R39 completa (una sola llamada, a la bandeja) y
  parcial (se reprocesa: `ya_en_bandeja` y el mismo Excel de errores); R21
  con cinco libros que no son la plantilla, `demasiadas_filas` y dos rechazos
  del lector; el catálogo con la obra de los metadatos y las decisiones pedidas
  solo de oficio y de la obra; grupos aplicados (grupo ambiguo, par que
  resuelve el proveedor, el nombre suelto que deja de valer, «distinto» que
  anula la componente, la etiqueta por uso); R33, R42 campo a campo, R37, R40
  (sin Excel si falla el registro, y la huella), R62–R65 sobre el libro
  reabierto, R70, R69, plantilla vacía, R67 (corregido y reimportado; ida y
  vuelta del Excel de errores), R68; R47 en logs y `repr`; §7.2 (orden, nombre
  en UTC, R9 sin llamadas, R10/R11 sin fichero, R12, grupos en la plantilla).
- **T18**: códigos y cuerpos de §8 de las tres rutas, cabeceras de descarga
  (R1), R9 sin construir adaptadores, R10 con dos obras de verdad, R11 con el
  adaptador real fuera de `dev`/`pro`, la composición por defecto (qué fábrica
  se llama, en qué orden y **cuándo no**: R21 y R39), R22 (cuatro variantes,
  128 vale, oid no texto), R14 (cero y dos ficheros), R15 (límite exacto), R16
  a R20 con su `codigo` y su texto, R17 con «ya no se admite», R33 (corte en
  200 y total), R34 y R93 en `avisos`, R37/R38 en las filas, R39 completa y
  parcial, R65 (base64 que se reabre), R69, R70, nombre recortado a 255, R45
  (campos exactos, acentos, tope y segundo cinturón, 400 y 503), R47 con
  `caplog` en éxito y en rechazos, R48, y la cabecera de `function_app.py`.

### Mutación

Campaña oficial sobre las líneas de T17–T18 (alcance contra `cf86881`, el
cierre del Bloque 5, cuya campaña ya estaba cerrada), con tope de tiempo
(`timeout 5400`) y sin dejar nada en segundo plano al entregar:
`python -m harness.mutacion --feature F-036 --base cf86881 --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque6a.md`.

1. **Primera pasada** (sobre `7032652`): **65 mutantes, 48 muertos, 17
   supervivientes, 0 timeouts**, 2069,0 s. Los 17, **huecos reales** (ninguno
   equivalente), en cuatro familias:
   - `@dataclass(frozen=True) → False` en `ExcelDeErrores` y `OpcionesDeLaObra`
     (2): ningún test intentaba cambiarlos;
   - `repr=False → True` en `grupos_oficio`, `grupos_proveedor`,
     `opciones_oficio`, `opciones_proveedor`, `con_error` y `resultado` del
     contexto (6): el test de R47 buscaba textos concretos y esos campos, en
     los datos de prueba, no llevaban ninguno de ellos;
   - `or → and` en las guardas de `paso_catalogo` (1) y `paso_registro` (4):
     los tests de «fuera de orden» dejaban vacío todo lo anterior a la vez, así
     que cada condición por separado no se probaba;
   - la cuenta de los MiB del mensaje del 413 (4): el test solo buscaba «MiB».

   Tests nuevos en `9686cad`: cada guarda por separado (parametrizado),
   `FrozenInstanceError` de los dos tipos, el conjunto **exacto** de campos
   visibles en el `repr` del contexto (`ahora`, `hash`, `obra_codigo`,
   `excel_errores`) y «El fichero pasa de 2 MiB». Comprobado a mano antes de la
   segunda pasada: con el mutante de `hash` aplicado → `2 failed`; con el de
   `obra_codigo` en `paso_catalogo` → `2 failed`; con `repr=True` en
   `con_error` → `1 failed` (`assert {'ahora', 'co…'obra_codigo'} == {'ahora',
   'ex…'obra_codigo'}`). El informe de esa pasada se descartó.
2. **Segunda pasada** (sobre `9686cad`): **65 mutantes, 65 muertos, 0
   supervivientes, 0 timeouts**, 2003,9 s con 6 workers (informe en
   `progress/mutacion_F-036_bloque6a.md`). Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T17: 90 (79 + 11 de la mutación); T18: 24 + 54 + 35, más los 8 de `test_f010_endpoints_protegidos.py` |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed; servicio `api`: **5581 passed, 67 skipped** en 592,58 s (sobre `9686cad`, con la campaña de mutación corriendo a la vez); `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 2087 líneas cambiadas cubiertas (2086/2087, umbral 80%, nivel critico)`. La que falta es la de siempre: `raise SystemExit(main())` del script de T8. Los seis `.py` de producción del bloque y las líneas nuevas de `function_app.py`, sin ninguna línea sin cubrir |
| Mutación | 65 generados sobre las líneas de T17–T18, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque6a.md`); la primera pasada dejó 17, cerrados con tests en `9686cad` |
| Tiempo de la suite | `api` 592,58 s en `init.sh` (con la campaña en paralelo); 102,20 s con `pytest -q` suelto antes de la campaña; tests del bloque: 45,19 s (T17, 90 tests) + 8,06 s + 26,35 s + 3,54 s + 0,20 s; campañas 2069,0 s + 2003,9 s |
| Lint | `ruff check` y `ruff format` sin avisos en los ficheros nuevos; `function_app.py` sin avisos (B6-17) |
| MANUAL pendiente | **T16** (humano, del Bloque 5: base efímera con Docker). Las tres rutas contra Sigrid y PostgreSQL reales se ven en T29 |

### Qué queda fuera y qué falta

- **T16** (MANUAL, humano): sigue pendiente; el comando está en «Bloque 5».
- **T19** (propuestas y decisiones de oficios, `/api/catalogos/*`) y **T20**
  (alcance cerrado): el otro encargo del Bloque 6. T19 hereda B6-3.
- El front (T21–T22) usará los nombres de B6-7.
- `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` y `azure-apps/` (las tres rutas
  nuevas): T26.
- Nada se ha ejecutado contra Sigrid ni PostgreSQL reales.

## Bloque 6b (T19–T20) · 2026-09-30 · hecho; T16 sigue siendo MANUAL del humano

> **Resumen para el líder.** T19 (`6f86baf`) y T20 (`db69340`) hechas, con
> `[x]` en `tasks.md`. Más `58099ba` (los tests que destapó la mutación). Hay borde HTTP para los oficios casi duplicados:
> `GET /api/catalogos/propuestas` y `POST /api/catalogos/decisiones`, anónimas
> como las demás, **solo con el catálogo `oficio`** (quinta enmienda:
> cualquier otro es 400 «no disponible en esta versión»). Las decisiones se
> piden solo entre los oficios de la obra (el contrato B6-3 de la plantilla),
> y un test fija que la pantalla y el desplegable enseñan los mismos grupos.
> T20 deja el alcance cerrado en un test (R46, R48, R49, R59 y §2.3). Tests
> con dobles (sin red, base ni IA; nada se escribe en Sigrid), ningún GUID
> literal, logs sin nombres, sin códigos de oficio y sin `oid`.
> `bash harness/init.sh` en verde. Mutación de T19–T20: **41 mutantes, 41 muertos, 0 supervivientes** (la primera pasada dejó 9, todos huecos reales, cerrados con tests en `58099ba`).
> **T16 sigue siendo MANUAL del humano y está pendiente.** Cosas para el
> humano: **B6-19** (desviación: `infra/08_lectura_sigrid_comun.ps1` no es
> idéntico a `dev` porque T1 bis lo arregló por R111; T20 exige que no cambie
> nada **fuera** de `Invoke-SigridLectura`), **B6-18** (nombres de la
> respuesta que la spec no fija; §8 todavía escribe `{oficio, proveedor}`),
> **B6-20** (400 que la spec no enumera) y **B6-26** (el barrido de F-010 no
> veía rutas con `/`).

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Tarea | Qué |
|---|---|---|
| `application/pipelines/equivalencias.py` (nuevo) | T19 | §15.5: `propuestas_de_oficios` (catálogo → últimas decisiones entre los oficios de la obra → `grupos_vigentes` + `proponer_grupos`) y `registrar_decisiones` (catálogo disponible y pares sin repetir **sin** Sigrid → todos los códigos oficios de la obra, si no `CodigoNoEsDeLaObra` → expansión de cada «mismo» a sus pares con sus motivos → **una** llamada a `registrar` → grupos vigentes leídos de nuevo). `CATALOGOS_DISPONIBLES = {OFICIO}`, `catalogo_disponible`, `exigir_peticion_decidible`, `DecisionPedida` (con sus reglas de forma), `PeticionDeDecisiones` (el `oid` fuera del `repr`), `PropuestasDeOficios`, `DecisionesRegistradas` |
| `interface_adapters/api/equivalencias.py` (nuevo) | T19 | `leer_propuestas` y `decidir_equivalencias`: todo lo que se mira sin Sigrid (cuerpo, `confirmado` booleano, obra, `oid`, decisiones, catálogo, pares repetidos) **antes** de construir ningún adaptador; composición Sigrid primero (B6-15); serialización |
| `function_app.py` | T19 | Rutas `catalogos/propuestas` (GET) y `catalogos/decisiones` (POST) en `ANONYMOUS`, sus dos entradas en la cabecera, sus traducciones (400 / 404 / 409 / 503) |
| `tests/test_f036_catalogos_http.py` (nuevo) | T19 | 119 tests (113 en T19; 6 tras la mutación, `58099ba`) |
| `tests/test_f010_endpoints_protegidos.py` | T19 | `ENDPOINTS` de 15 a 17 y el patrón de rutas de `\w+` a `[\w/]+` (B6-26), con su control negativo; ninguna comprobación se quita |
| `tests/test_f036_alcance_cerrado.py` (nuevo) | T20 | 25 tests |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T19, T20 | `[x]` |
| `progress/mutacion_F-036_bloque6b.md` (raíz, nuevo) | — | Informe de la campaña |

No se ha tocado el dominio, los puertos, los adaptadores, las fábricas, los
handlers del Bloque 6a ni nada de §2.3. Ninguna variable de entorno nueva
(R49).

### Decisiones y desviaciones (para el reviewer y el humano)

18. **B6-18 · La forma de las respuestas** (la spec no fija los nombres; para
    T21):
    - `GET /api/catalogos/propuestas` →
      `{obra, oficio: {oficios: [{codigo, nombre, grupo}], grupos: [{etiqueta, codigos}], propuestas: [{codigos, por_pares, motivos, pares: [{codigo_a, codigo_b, motivos}]}], avisos: [{codigos}]}}`.
      `grupo` son los códigos del grupo vigente del oficio (R87: «los códigos
      de la obra con su grupo vigente»); los códigos y los motivos van
      ordenados; `nombre` puede ser `null`. **Sin clave `proveedor`**: la
      tabla de §8 todavía escribe `{oficio: {...}, proveedor: {...}}`, pero
      R87 y `tasks.md` T19 con la quinta enmienda dicen solo `oficio`
      (convendría retocar §8 en la próxima pasada de la spec).
    - `POST /api/catalogos/decisiones` →
      `{obra, pares_guardados: [{catalogo, codigo_a, codigo_b, decision, motivos}], grupos_vigentes: {oficio: {grupos, avisos}}}`
      («los pares guardados y los grupos vigentes resultantes de cada
      catálogo tocado», §8).
19. **B6-19 · Desviación en T20: `infra/08_lectura_sigrid_comun.ps1`.**
    `design.md` §2.3 dice que se usa «tal cual» y T20 pide los ficheros de
    §2.3 «idénticos a `dev`», pero T1 bis (`1b3edfb`, encargo del líder del
    2026-09-28) cambió en él la decodificación de la respuesta de la pasarela
    para cumplir **R111** (tildes en UTF-8). Exigir que fuera idéntico dejaría
    T20 en rojo por un cambio aprobado. El test exige lo más estricto que
    sigue siendo verdad: **fuera de `Invoke-SigridLectura` el fichero es
    idéntico carácter a carácter** al de la base de la rama, y esa función
    solo nombra `POST /api/sql/read` y ninguna escritura. Si el humano quiere
    otra cosa (p. ej. anotar la excepción en §2.3), es un cambio de la spec,
    no del código.
20. **B6-20 · 400 que la spec no enumera** (R88 dice «400 si el cuerpo no
    cumple»; estos son los que no cumplen):
    - `decisiones` vacía o que no es lista; una decisión que no es objeto;
      `codigos` que no es lista;
    - un código que no es texto o está en blanco, o **repetido** en la misma
      decisión (`["0085", "0085"]` no son dos códigos);
    - **el mismo par dos veces en la misma petición** (p. ej. «mismo» de
      `0085`/`0166` y «distinto» del mismo par): los dos se guardarían con la
      misma hora, y entonces manda el que la base numere después
      (`decision_id` en `select_ultimas_decisiones`), que en un `INSERT`
      de varias filas no es un orden que el código garantice. Se rechaza sin
      leer Sigrid;
    - `decision` en otra forma que `mismo`/`distinto` en minúsculas;
    - `catalogo` distinto de `"oficio"` **exacto**: `"Oficio"`, `"oficios"`,
      vacío, `null` o un número son también «no disponible en esta versión»
      (el motivo no repite lo que llegó).
    Los códigos **no se recortan**: la comparación con `obrofc` es exacta,
    así que `" 0166"` es 409 y no se corrige solo.
21. **B6-21 · En decisiones, la obra que no se puede comprobar es 409.**
    §4.6 da `ObraSinUnidades` como 404 «en la plantilla y en propuestas» y
    409 en la importación; para decisiones no dice nada, y la fila de §8 de
    decisiones solo tiene 400, 409 y 503. Se usa 409 con su `codigo` (B6-8),
    igual que la importación: la petición está bien, lo que falla es la obra.
22. **B6-22 · El 409 dice cuántos códigos no son de la obra, no cuáles.** El
    motivo va al log (R47 y el encargo: «logs sin nombres ni códigos»); el
    front sabe qué códigos mandó.
23. **B6-23 · Los motivos que se guardan** (R83: «los motivos propuestos»)
    se calculan en el momento con `motivos_del_par` y los nombres de Sigrid
    de hoy, también en un «distinto», y quedan vacíos si una persona agrupa
    dos oficios que no se parecen (en un «mismo» de tres, los pares sin
    parecido van con `motivos` vacío).
24. **B6-24 · Los grupos de la respuesta se leen después de guardar** (una
    segunda llamada a `ultimas_decisiones`), no se calculan en memoria: la
    pantalla recarga con lo que hay en la base.
25. **B6-25 · Las comprobaciones sin Sigrid, dos veces.** El borde llama a
    `exigir_peticion_decidible` antes de construir los adaptadores y
    `registrar_decisiones` la repite: la aplicación no se fía de quien la
    llame (un test le pasa un `Catalogo.PROVEEDOR` construido a mano).
26. **B6-26 · El barrido de F-010 no veía las rutas con barra.**
    `PATRON_RUTA` capturaba la ruta con `\w+`, que no casa `/`: con las dos
    rutas nuevas, `niveles()` habría seguido contando 15 y el test habría
    pasado **sin mirarlas**. Se amplía a `[\w/]+` (lo que casaba antes sigue
    casando igual) y el control negativo añade una ruta `a/b` con su nivel.
    `ENDPOINTS` pasa a 17. Además, un test de T19 mira las dos rutas en lo
    que publica el host (`utiles_rutas.ruta_registrada`): método, ruta y
    `anonymous`.
27. **B6-27 · La cabecera de `function_app.py`** gana las dos entradas.
    No se añade nada a «Qué añade `GET /api/cola`»: las propuestas devuelven
    nombres de oficio del catálogo de Sigrid, ni datos de la propiedad ni
    proveedores.
28. **B6-28 · Sin tope de decisiones por petición.** La spec no lo pone.
    Cada código está acotado por la comprobación de `obrofc` (409), pero el
    número de decisiones de un cuerpo no. Detrás del proxy y con la
    confirmación explícita no parece un riesgo; si el humano lo quiere, es
    una línea en `_peticion`.
29. **B6-29 · `MAX_USUARIO_OID` se importa de `importar.py`**: una sola
    definición del tope de 128 (R22).
30. **B6-30 · Cómo mira T20**:
    - el diff es **de la base de la rama al árbol de trabajo** (no
      `dev...HEAD` como F-034): ve también lo que no se ha commiteado, y así
      la fase RED se pudo demostrar sin commitear nada;
    - R46 mira **las líneas añadidas** al código (no los ficheros enteros:
      `function_app.py` ya documentaba `/api/cerrar`), y aparte el código
      **sin docstrings** de cada pieza de F-036 (varios docstrings dicen «no
      usa `sql/write`» o «no mira `CIERRE_HABILITADO`», y eso no puede contar
      como usarlos);
    - la lista de ficheros de F-036 está escrita a mano y los bloques 7 y 8
      la amplían con los suyos. **No** hay un test «el código tocado es
      exactamente esta lista» como en F-034: se rompería con T21–T23;
    - «la rama de F-035 ni se mergea ni se toca» se comprueba por commits
      (ninguno de F-035 que no esté en `dev` está en `HEAD`), no por
      ascendencia: `dev` ya trae el punto de pausa de F-035;
    - R48 por comportamiento ya lo prueban los tests de T13; aquí se fija que
      ninguna pieza de F-036 nombra un interruptor y que la fábrica del
      catálogo llama a la puerta del entorno.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`.

**T19** · con `application/pipelines/equivalencias.py` y
`interface_adapters/api/equivalencias.py` como esqueletos (los tipos, y las
funciones con `NotImplementedError`), sin rutas en `function_app.py` y con
`ENDPOINTS` ya ampliado a diecisiete:
`.venv/Scripts/python.exe -m pytest tests/test_f036_catalogos_http.py tests/test_f010_endpoints_protegidos.py -q -p no:cacheprovider`

```text
FAILED tests/test_f036_catalogos_http.py::test_f036_r87_las_propuestas_de_oficios_de_la_obra
FAILED tests/test_f036_catalogos_http.py::test_f036_r87_quinta_enmienda_solo_el_catalogo_oficio
[… 106 líneas FAILED más …]
FAILED tests/test_f036_catalogos_http.py::test_f036_t19_la_cabecera_de_function_app_lista_las_dos_rutas[POST /api/catalogos/decisiones]
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay
112 failed, 9 passed in 5.40s
```

Muestra (`--tb=short`, `-k "r87_las_propuestas_de_oficios_de_la_obra or r88_un_mismo_se_guarda or quinta_enmienda_otro_catalogo and proveedor or r88_un_codigo_que_no_es_oficio and decisiones0 or barrido_de_niveles or las_dos_rutas_se_publican and propuestas"`):

```text
E   AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'leer_propuestas'
E   AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'decidir_equivalencias'
E   AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'decidir_equivalencias'
E   AttributeError: <module 'function_app' from '…\\services\\postventa-api\\function_app.py'> has no attribute 'decidir_equivalencias'
E   AssertionError: el host no publica ninguna ruta «catalogos_propuestas»
E   assert 15 == 17
E    +  where 15 = len({'health': 'ANONYMOUS', 'split': 'ANONYMOUS', 'extraer': 'ANONYMOUS', 'firma': 'ANONYMOUS', ...})
6 failed, 115 deselected in 1.60s
```

Y en la aplicación (`-k "los_mismos_que_los_de_la_plantilla or pedida_mal_formada and decision0 or codigo_no_es_de_la_obra_es_el_error"`):

```text
application\pipelines\equivalencias.py:62: in propuestas_de_oficios
E   NotImplementedError
tests\test_f036_catalogos_http.py:853: in test_f036_r88_una_decision_pedida_mal_formada_no_se_construye
E   Failed: DID NOT RAISE PeticionDeDecisionInvalida
application\pipelines\equivalencias.py:72: in registrar_decisiones
E   NotImplementedError
3 failed, 110 deselected in 1.23s
```

Los 9 que pasaban: los dos de R48 sobre el texto de los módulos (los
esqueletos no nombran ningún interruptor), el `repr` de la petición sin el
`oid` (el tipo ya estaba) y los seis de F-010 que no cuentan rutas.

**T20** · es un test sin código de producción: la fase RED se demuestra
**inyectando en el árbol de trabajo**, sin commitear, una violación de cada
frontera y comprobando que el control la caza. Inyecciones: una línea en
`infrastructure/sigrid/cliente.py`; `_RED = "/api/sql/write"` en
`application/pipelines/equivalencias.py`; una función con
`ajustes.cierre_habilitado` en `interface_adapters/api/equivalencias.py`; un
`os.getenv("F036_NUEVA")` en `application/pipelines/plantilla.py`;
`F036_NUEVA=` en `.env.example`; un método más en `UbicacionPort`; un
comentario en `Get-SigridValor` de `infra/08_lectura_sigrid_comun.ps1` (fuera
de `Invoke-SigridLectura`); y un `tests/fixture_red.xlsx` vacío.
`.venv/Scripts/python.exe -m pytest tests/test_f036_alcance_cerrado.py -q -p no:cacheprovider --tb=short`

```text
E   assert ['+_RED = "/api/sql/write"'] == []
E   AssertionError: assert {'application...['sql/write']} == {}
E     {'application/pipelines/equivalencias.py': ['sql/write']}
E   AssertionError: assert ['interface_a...valencias.py'] == []
E   AssertionError: assert ['services/po....env.example'] == []
E   AssertionError: assert ['application...plantilla.py'] == []
E   AssertionError: hay libros en tests: ['fixture_red.xlsx']
E   AssertionError: F-036 no toca esto (§2.3). Sobran: ['services/postventa-api/domain/ports/ubicacion.py', 'services/postventa-api/infrastructure/sigrid/cliente.py']
E   AssertionError: assert '# infra/08_l..._VEREDICTO\n}' == '# infra/08_l..._VEREDICTO\n}'
E       lor {
E     +     # inyeccion RED de T20
E   AssertionError: assert ('leer_ubicac...eer_algo_mas') == ('leer_ubicac...s_del_numero')
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r46_ninguna_linea_anadida_por_la_rama_nombra_una_escritura
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r46_el_codigo_de_f036_no_nombra_ninguna_escritura
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r48_el_codigo_de_f036_no_mira_ninguna_ventana_de_escritura
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r49_la_rama_no_toca_la_configuracion_del_entorno
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r49_el_codigo_de_f036_no_lee_el_entorno_por_su_cuenta
FAILED tests/test_f036_alcance_cerrado.py::test_f036_r59_ningun_libro_versionado_ni_en_los_tests
FAILED tests/test_f036_alcance_cerrado.py::test_f036_s2_3_la_rama_no_toca_ningun_intocable
FAILED tests/test_f036_alcance_cerrado.py::test_f036_s2_3_la_lectura_comun_solo_cambia_dentro_de_invoke_sigrid_lectura
FAILED tests/test_f036_alcance_cerrado.py::test_f036_s2_3_los_puertos_del_circuito_no_ganan_ni_un_metodo[domain/ports/ubicacion.py-UbicacionPort]
9 failed, 16 passed in 2.67s
```

Las inyecciones se deshicieron con `git checkout --` de esos siete ficheros y
borrando el `.xlsx`; después, `25 passed in 4.09s`. Los 16 que siguieron en
verde son los controles negativos de los comparadores, las listas que tienen
que existir, `.gitignore`, el adaptador del catálogo, la puerta del entorno,
la lectura común (que sigue leyendo solo `sql/read`), los otros dos puertos,
el historial de la rama sin libros y F-035. R59 «en un commit» no se inyectó
(habría que commitear un `.xlsx`, y el historial no lo suelta); ese control
usa la misma función `_es_un_libro` que el que sí se vio en rojo.

### Verde

- `.venv/Scripts/python.exe -m pytest tests/test_f036_catalogos_http.py tests/test_f010_endpoints_protegidos.py -q` → **121 passed** (113 + 8) en 3,75 s.
- `.venv/Scripts/python.exe -m pytest tests/test_f036_alcance_cerrado.py -q` → **25 passed** en 4,09 s.
- Suite del servicio suelta tras T19: `5696 passed, 67 skipped in 108.40s`.
- Cobertura medida aparte (`coverage run` con los dos ficheros de T19):
  `application/pipelines/equivalencias.py` y
  `interface_adapters/api/equivalencias.py` **100 %**; en `function_app.py`,
  las líneas de las dos rutas nuevas, todas cubiertas.

Qué fijan los tests, además de lo de la tabla de la tarea:

- **T19, propuestas**: el cuerpo entero (`==`) con la 0677 inventada; sin
  clave `proveedor` y decisiones pedidas solo del catálogo `oficio`; un grupo
  confirmado (R85: ya no se propone; R86: etiqueta del de más filas y, a
  igualdad, del código menor); R82 con aviso; R79 (no clique → por pares) y
  clique de tres con motivos ordenados; oficio sin nombre; obra sin oficios;
  B6-3 (qué códigos se piden y en qué orden se llama a los puertos); **los
  mismos grupos que `opciones_de_la_obra`** (la plantilla); R9, R10 (también
  con dos obras de verdad), R11, R48 con el adaptador real fuera de
  `dev`/`pro`, la composición por defecto, R47 con `caplog`.
- **T19, decisiones**: un «mismo» de tres → tres pares en orden con sus
  motivos, el `oid`, la obra normalizada y la hora, en **una** llamada; la
  respuesta entera; grupos leídos después de guardar; un «distinto» que
  separa; varias decisiones juntas; `oid` recortado y 128 caracteres;
  `confirmado` en seis formas que no son `true`; seis catálogos que no son
  `oficio` y uno entre varios (nada se guarda); treinta cuerpos mal formados
  (400 sin llamar a ningún puerto); JSON roto; el 400 que no repite el
  `oid`; las reglas de `DecisionPedida`; la aplicación que rechaza
  `PROVEEDOR` y una petición vacía; el 409 en cuatro variantes (código
  inexistente, un código de **proveedor** de la obra, un código con un blanco
  delante, una decisión buena y otra mala) sin guardar y sin repetir
  códigos; 409 de la obra; 503 en cinco sitios; ningún adaptador construido
  con el cuerpo mal; la hora por defecto en UTC; R47 con `caplog` en éxito,
  409 y 400; las dos rutas publicadas y anónimas; la cabecera.

### Mutación

Campaña oficial sobre las líneas de T19–T20 (alcance contra `a5447ce`, el
cierre del Bloque 6a, cuya campaña ya estaba cerrada), con tope de tiempo
(`timeout 5400` y `timeout 3600`) y sin dejar nada en segundo plano al
entregar:
`python -m harness.mutacion --feature F-036 --base a5447ce --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque6b.md`.
El alcance son 3 ficheros y 675 líneas de producción (los dos módulos de T19
y las líneas nuevas de `function_app.py`; T20 es solo test).

1. **Primera pasada** (sobre `db69340`): **41 mutantes, 32 muertos, 9
   supervivientes, 0 timeouts**, 1007,3 s. Los 9, **huecos reales** (ninguno
   equivalente), en tres familias:
   - `@dataclass(frozen=True) → False` en `DecisionPedida`,
     `PeticionDeDecisiones`, `PropuestasDeOficios` y `DecisionesRegistradas`
     (4): ningún test intentaba cambiarlos;
   - los recuentos `mismo=`/`distinto=` del log de `registrar_decisiones`
     (`sum(1 …) → sum(2 …)` y `== → !=`, 4): el test de R47 miraba qué **no**
     sale en el log, no que los números fueran los de verdad;
   - `or → and` en la guarda de `decisiones` del handler (1): con el mutante
     una lista vacía o un texto siguen siendo 400, pero por otra comprobación
     más abajo y con otro motivo; ningún test fijaba el motivo.

   Tests nuevos en `58099ba`: `FrozenInstanceError` de los cuatro tipos, el
   log exacto `decisiones=2 pares=4 mismo=3 distinto=1` y el motivo del 400
   para `None`, `[]`, un texto y un objeto. Comprobado a mano antes de la
   segunda pasada: con `frozen=False` en `DecisionesRegistradas` →
   `Failed: DID NOT RAISE FrozenInstanceError`; con `sum(2 …)` en `mismo` →
   `assert 'decisiones=2 pares=4 mismo=3 distinto=1' in '… mismo=6 distinto=1 …'`;
   con `and` en la guarda → `3 failed, 1 passed`. El informe de esa pasada se
   descartó.
2. **Segunda pasada** (sobre `58099ba`): **41 mutantes, 41 muertos, 0
   supervivientes, 0 timeouts**, 733,8 s con 6 workers (informe en
   `progress/mutacion_F-036_bloque6b.md`). Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T19: 119 (`test_f036_catalogos_http.py`, 113 + 6 de la mutación) + los 8 de `test_f010_endpoints_protegidos.py`; T20: 25 (`test_f036_alcance_cerrado.py`) |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed; servicio `api`: **5727 passed, 67 skipped** en 253,60 s (sobre `58099ba`); `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 2286 líneas cambiadas cubiertas (2285/2286, umbral 80%, nivel critico)`. La que falta es la de siempre: `raise SystemExit(main())` del script de T8. Los dos `.py` de producción de T19 y las líneas nuevas de `function_app.py`, sin ninguna línea sin cubrir |
| Mutación | 41 generados sobre las líneas de T19–T20, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-036_bloque6b.md`); la primera pasada dejó 9, cerrados con tests en `58099ba` |
| Tiempo de la suite | `api` 253,60 s en `init.sh`; 108,40 s con `pytest -q` suelto tras T19; tests del bloque: 2,27 s (T19, 119 tests), 3,75 s (los 113 de T19 más los 8 de F-010, antes de la mutación) y 4,09 s (T20, 25 tests); campañas 1007,3 s + 733,8 s |
| Lint | `ruff check` y `ruff format` (desde la raíz, la configuración de `init.sh`) sin avisos en los ficheros nuevos; en `function_app.py` sin avisos, y `ruff format` solo cambiaría la línea previa de `remesa` (B6-17) |
| MANUAL pendiente | **T16** (humano, del Bloque 5: base efímera con Docker). Las rutas contra Sigrid y PostgreSQL reales se ven en T27 (confirmar grupos en `oficios.html`) y T29 |

### Qué queda fuera y qué falta

- **T16** (MANUAL, humano): sigue pendiente; el comando está en «Bloque 5».
- **Bloque 7** (T21–T22): el front. Usará los nombres de B6-7 y B6-18, y
  tendrá que ampliar `NUEVOS_DE_F036` de `test_f036_alcance_cerrado.py` si
  quiere que sus ficheros pasen por los controles sin `git`.
- `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` y `azure-apps/` (las cinco
  rutas nuevas): T26.
- La tabla de §8 de `design.md` todavía escribe la respuesta de propuestas
  con `proveedor` (B6-18) y §2.3 no recoge la excepción de `infra/08`
  (B6-19): retoques de spec, no de código.
- Nada se ha ejecutado contra Sigrid ni PostgreSQL reales.

## Bloque 7 (T21–T22) · 2026-09-30 · hecho; T16 sigue siendo MANUAL del humano

> **Resumen para el líder.** T21 (`6256697`) y T22 (`5c48215`) hechas, con
> `[x]` en `tasks.md`, más el commit de este informe (con `ruff format` del
> test nuevo). El front ya tiene la entrada de incidencias: `importar.html`
> (plantilla, importación con el Excel de errores y bandeja de **solo
> lectura**) y `oficios.html` (propuestas, grupos vigentes con «Separar»,
> avisos y la descarga de los grupos vigentes de R98), cada una con su módulo
> (`js/importacion.js`, `js/oficios.js`), y cinco métodos nuevos en
> `js/api.js`. Ningún botón de editar, descartar ni aprobar incidencias
> (F-038). Sin proveedores ni actividades en `oficios.html` (quinta
> enmienda). `index.html` solo gana los dos enlaces de R51 (7 líneas en la
> cabecera). Tests: 408 de JavaScript (86 nuevos) y 301 de Python del front
> (45 nuevos), todo en verde; `bash harness/init.sh` en verde. La mutación
> del arnés no mide JavaScript (0 líneas de producción `.py` en el alcance);
> 22 mutantes a mano del JS, **22 muertos**. **T16 sigue siendo MANUAL del
> humano y está pendiente.** Nada se ha abierto en un navegador (MANUAL
> pendiente, abajo). Cosas para el humano: B7-2 (las decisiones tampoco se
> reintentan), B7-4 (sin sesión no se importa ni se decide), B7-5 (los
> enlaces abren otra pestaña) y cómo quedará el conflicto con F-035 (abajo).

### Qué cambió

| Fichero (bajo `services/postventa-front/`) | Tarea | Qué |
|---|---|---|
| `js/api.js` | T21 | Cinco métodos: `descargarPlantilla(obra)` (binaria, `{blob, disposicion}`), `importarExcel(fichero, usuarioOid)` (multipart `fichero` + `usuario_oid`), `bandeja(obra, limite)`, `propuestasCatalogos(obra)` y `decidirCatalogos(cuerpo)`. `clasificar` deja en el error `mensajeServicio` y `codigo` del backend; `peticion` admite `sinReintentos` y `mensajeDelServicio`; `unIntento` se parte en `abrir` + `errorDeRespuesta` (sin cambiar lo que hace) para reutilizarlos en `descarga`. Los doce endpoints de antes no cambian |
| `js/importacion.js` (nuevo) | T21 | Lógica pura (Content-Disposition, base64 → `Blob` del Excel de errores, textos de estado y de fila, resumen, errores ordenados «Fila N · columna X · problema», aviso de lista recortada R33, marcas de la bandeja, `guardarBlob` con entorno inyectable) y el componente `crearAppImportacion({api, guardar})` / `appImportacion()` |
| `js/oficios.js` (nuevo) | T21 | Lógica pura (motivos legibles de §15.6, pares de un grupo, propuestas/grupos/avisos listos para pintar, `cuerpoDeDecision` —el único sitio con `confirmado: true`—, el JSON de R98) y el componente `crearAppOficios({api, guardar})` / `appOficios()` |
| `tests_js/api.test.js` | T21 | 22 tests nuevos de F-036; la lista de endpoints pasa de 12 a 17 (enmienda en el propio test, sin quitar ninguno) y el doble `respuesta()` gana `blob()` y `headers.get()` |
| `tests_js/importacion.test.js`, `tests_js/oficios.test.js` (nuevos) | T21 | 40 + 24 tests |
| `importar.html`, `oficios.html` (nuevos) | T22 | Las dos páginas (§9 y §15.6), con el patrón de `index.html`: Tailwind por CDN, Alpine 3.14.1 con `defer` en el `<head>`, scripts propios al final del `body` sin `defer`, cabecera de ruta en la línea 1 |
| `index.html` | T22 | **Solo** un `<nav>` con los dos enlaces (y su comentario) dentro de la cabecera: +6 líneas |
| `README.md` | T22 | Las dos páginas en «Cómo está organizado» y una sección «La entrada de incidencias (F-036)» |
| `tests/test_f036_front.py` (nuevo) | T22 | 45 tests (detalle abajo) |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T21, T22 | `[x]` |
| `progress/mutacion_F-036_bloque7.md` (raíz, nuevo) | — | Campaña del arnés: 0 líneas en el alcance |

No se ha tocado el backend, ni `app.js`, ni `dev_server.py`, ni
`staticwebapp.config.json` (el `/*` con `authenticated` ya cubre las dos
páginas nuevas). Ninguna dependencia nueva.

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B7-1 · El 503 de la entrada enseña el texto del backend (R52).** En el
   circuito de partes `clasificar` cambia el texto de un 503 por el fijo
   «Este entorno no archiva…» (la puerta de entorno de archivar). En F-036 un
   503 es «sin Sigrid o sin base» y el backend dice cuál, así que los cinco
   métodos nuevos piden `mensajeDelServicio`: el `ErrorApi` conserva su `tipo`
   (`entorno`) pero su `mensaje` es el del backend. `clasificar` gana dos
   propiedades (`mensajeServicio`, `codigo`) sin cambiar `tipo` ni `mensaje`;
   un test fija que el 503 de `archivar` sigue diciendo lo de siempre.
2. **B7-2 · `decidirCatalogos` tampoco se reintenta** (para el humano). R52
   solo habla de la importación; la spec no dice nada de las decisiones.
   Se tratan igual porque son el acto explícito de una persona (§8: «no sale
   de un doble clic»): un 502 o la red caída enseñan el motivo y la persona
   vuelve a pulsar. Un reintento no habría roto nada (la tabla es append-only
   y manda la última), pero no se repite sola una decisión. `bandeja` y
   `propuestasCatalogos` son lecturas y **sí** reintentan lo transitorio,
   como `cola`.
3. **B7-3 · La plantilla, un solo intento y por un camino propio**
   (`descarga`). `peticion` lee el cuerpo como JSON y un `.xlsx` no lo es; la
   descarga lleva el mismo timeout y la misma traza (`paso: "plantilla"`),
   pero no reintenta: la plantilla lee Sigrid, y tres intentos de 40 s serían
   dos minutos de espera muda. Si falla, se enseña el motivo y se vuelve a
   pulsar. Un fallo de transporte sin reintento dice «no se ha reintentado» y
   no «Reintentando…» (`TEXTO_SIN_REINTENTO`).
4. **B7-4 · Sin sesión no se importa ni se decide** (para el humano). El
   `usuario_oid` sale de `/.auth/me` (`api.identidad()`, el mismo del cierre).
   Sin él, «Importar a la bandeja» y los botones de decisión quedan
   deshabilitados con el motivo escrito, como el botón de cerrar: el backend
   respondería 400 igualmente (R22, R88). Consecuencia: en local con
   `dev_front.ps1` (sin el proxy de la SWA) se puede descargar la plantilla y
   ver la bandeja y las propuestas, pero no importar ni decidir.
5. **B7-5 · Los dos enlaces de `index.html` abren otra pestaña**
   (`target="_blank" rel="noopener"`, para el humano). Salir de `index.html`
   en la misma pestaña perdería la remesa en curso, que solo vive en memoria
   (D4 de F-007). Es el mismo criterio que la barra de F-035 (R31, R47 de
   F-035). Entre `importar.html` y `oficios.html` los enlaces son normales:
   ahí no hay nada que perder.
6. **B7-6 · `oficios.js` usa `window.Importacion`** (para `guardarBlob` y
   `mensajeDeError`) en vez de un tercer módulo: la tarea nombra solo esos
   ficheros. `oficios.html` carga `importacion.js` antes que `oficios.js` y
   un test fija el orden.
7. **B7-7 · Content-Disposition.** Se respeta `filename*` (RFC 6266) por
   delante de `filename`, se quita cualquier ruta del nombre (`../`, `\`) y,
   sin nombre, `plantilla_incidencias_<obra>.xlsx`. El backend manda hoy
   `attachment; filename="plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx"`.
8. **B7-8 · Las marcas de la bandeja** (§9 dice «duplicada de la fila N»).
   `duplicada_de` es un `incidencia_id`; la fila sale del original **si está
   en la lista devuelta** (tope por defecto 200): «duplicada de la fila N» si
   es de la misma importación, «duplicada de la fila N de otra importación»
   si no, y «duplicada de una incidencia anterior» si el original no ha
   venido en la lista. El oficio ambiguo: «varios códigos en Sigrid: se elige
   en la revisión», literal de §9, y el oficio se enseña sin código (R99).
9. **B7-9 · Cómo se decide en `oficios.html`** (§15.3): una propuesta que es
   clique (`por_pares: false`) tiene **un** «Son el mismo» para el grupo
   entero y «Son distintos» por par; una que viene por pares (R79) tiene los
   dos botones en cada par. Un grupo vigente enseña **todos** sus pares, cada
   uno con «Separar» (= «distinto» de ese par). Solo se pintan los grupos
   vigentes de más de un código. La obra de la decisión es la de las
   propuestas que se están viendo, no lo que haya en el campo en ese momento.
   Mientras se guarda una decisión, todos los botones quedan deshabilitados:
   un doble clic no produce dos.
10. **B7-10 · El JSON de R98**: `grupos_vigentes_oficio_<obra>.json`, con la
    forma de `design.md` §10.3 (`{"obra", "oficio": [[cod, cod], …]}`), solo
    grupos de más de un código, códigos ordenados y grupos por su primer
    código, sangrado de 2. Sale de los `grupos` de la última lectura de
    propuestas, que ya viene después de cada decisión (B6-24).
11. **B7-11 · `api.test.js` pasa de 12 a 17 endpoints** con una enmienda
    escrita en el propio test y la comparación nombre a nombre intacta. El
    doble `respuesta()` gana `blob()` y `headers.get()` sin cambiar lo que ya
    devolvía.
12. **B7-12 · `NUEVOS_DE_F036` de `test_f036_alcance_cerrado.py` no se
    amplía.** Esa lista alimenta controles que leen **Python con `ast`**
    bajo `services/postventa-api`; el front es JS y HTML. El control de R46
    sobre las líneas añadidas por la rama sí las ve, y sigue en verde
    (`25 passed`, ejecutado aparte porque `init.sh` usó la caché del `api`).
13. **B7-13 · «Sin datos reales» en el front.** Además del barrido general
    de F-007 (DNI, base64 largo, binarios), `test_f036_front.py` busca en las
    páginas, los módulos y los tests JS de F-036 la obra del piloto y los
    siete códigos de oficio medidos en ella (los que ya están en
    `design.md`). Todo lo de los tests es inventado: obra `9999`, oficios
    `9001…`, «Oficio inventado A», «Portal inventado 1».
14. **B7-14 · Retoques de spec, no de código**: el párrafo de F-035 de §9
    todavía nombra `js/catalogos.js` (es `js/oficios.js` desde la quinta
    enmienda), y la tabla de §8 sigue con `proveedor` en las propuestas
    (B6-18).

### Cómo quedará el conflicto con F-035 (para quien mergee segundo)

F-035 (`feature/F-035-portal-posventa`, sin mergear) **reescribe
`index.html` entero** (pasa a ser el portal) y muda el circuito de partes a
`partes.html`. Esta rama solo añade 6 líneas a la cabecera de `index.html`
(un `<nav>` con dos `<a>` y su comentario), así que:

- **`index.html`: conflicto seguro, de resolución mecánica.** Se toma la
  versión de F-035 entera y se descartan las 6 líneas de F-036. Los dos
  enlaces se llevan donde el portal los necesite: a la pestaña «Entrada» de
  la barra de `partes.html` y del portal (que hoy apunta a `./#/entrada`) o
  directamente a `importar.html` y `oficios.html`. §9 prevé además que los
  placeholders `data-placeholder="F-036"` de la sección «Entrada» del portal
  llamen a **estas mismas** funciones (`Api.descargarPlantilla`,
  `Api.importarExcel`, `Importacion.*`, `Oficios.*`); las páginas propias
  pueden quedarse o volverse una redirección.
- **`tests/test_f036_front.py`**: los dos tests de R51 miran la cabecera de
  `index.html` (`test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas`
  y `…_solo_gana_los_dos_enlaces`). Tras el merge hay que apuntarlos a donde
  vivan los enlaces (el segundo, que exige que la cabecera **solo** tenga esos
  dos enlaces, dejará de tener sentido en el portal y se quita o se
  reescribe). El resto del fichero no depende de `index.html`; importa de
  `test_f007_estaticos.py` solo funciones y `VERSION_ALPINE`, no su `INDEX`
  (que F-035 cambia a `partes.html`).
- **Sin conflicto**: `js/api.js`, `js/importacion.js`, `js/oficios.js`,
  `importar.html`, `oficios.html` y `tests_js/` (F-035 no los toca; añade
  `portal.js`, `portal_app.js` y `maqueta_datos.js`). `README.md`: F-035 no
  lo modifica en su diff contra `dev`.
- F-035 cambia estilos (`css/styles.css`, `css/portal.css`) y fuentes: las dos
  páginas de F-036 usan Tailwind y `css/styles.css` como el `index.html` de
  `dev`; si el portal quiere su identidad visual en ellas, es trabajo del
  merge.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-front`.

**T21** · con `js/importacion.js` y `js/oficios.js` como esqueletos (cada
función exportada lanza `Error("sin implementar")`) y `js/api.js` sin
tocar: `node --test "tests_js/*.test.js"`

```text
✖ f007 R27 / f019 / f009 / f012 / f028 / f036: los DIECISIETE endpoints llaman a su ruta, con su metodo (36.8178ms)
✖ f007 R27 / f036: son diecisiete, y la lista se entera si aparece otro (3.4285ms)
✖ f007 R27: todos cuelgan de baseApi, y baseApi es configurable (1.4148ms)
✖ f036 R22: sin usuario identificado no se importa, y se dice por que (0.546ms)
✖ f036 R43: importarExcel manda el fichero y usuario_oid en multipart, sin Content-Type a mano (3.5234ms)
✖ f036 R52: importarExcel NO se reintenta ante un 502 (0.622ms)
✖ f036 R52: un 503 de la entrada NO se confunde con la puerta de entorno de archivar (0.3395ms)
✖ f036 R65: el base64 se decodifica a los bytes exactos (0.5483ms)
✖ f036 R88/R89: confirmado: true solo sale al pulsar, con la obra cargada y el oid (0.4909ms)
✖ f036 R98: el JSON de grupos vigentes lleva solo codigos y solo grupos de mas de uno (0.5078ms)
[… 78 líneas ✖ más …]
ℹ tests 408
ℹ pass 320
ℹ fail 88
```

Trazas de muestra:

```text
✖ f007 R27 / f036: son diecisiete, y la lista se entera si aparece otro (3.4285ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  12 !== 17
✖ f036 R52: importarExcel NO se reintenta ante un 502 (0.622ms)
  TypeError: api.importarExcel is not a function
      at …\services\postventa-front\tests_js\api.test.js:1035:34
✖ f036 R65: el base64 se decodifica a los bytes exactos (0.5483ms)
  Error: sin implementar
      at Object.sinImplementar (…\services\postventa-front\js\importacion.js:5:11)
✖ f036 R88/R89: confirmado: true solo sale al pulsar, con la obra cargada y el oid (0.4909ms)
  Error: sin implementar
      at Object.sinImplementar (…\services\postventa-front\js\oficios.js:5:11)
      at componente (…\services\postventa-front\tests_js\oficios.test.js:258:23)
```

Los 320 que pasaban: los 322 de antes menos los tres de la lista de
endpoints que ya incluían los cinco nuevos, más el control «el 503 de
archivar sigue siendo la puerta de entorno» (que tiene que pasar antes y
después).

**T22** · sin `importar.html` ni `oficios.html`, sin enlaces en `index.html`
y sin tocar el README:
`python -m pytest tests/test_f036_front.py tests/test_f007_estaticos.py -q -p no:cacheprovider --tb=line`

```text
…\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: '…\\services\\postventa-front\\importar.html'
…\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: '…\\services\\postventa-front\\oficios.html'
…\tests\test_f036_front.py:343: AssertionError: la cabecera de index.html no enlaza a importar.html
…\tests\test_f036_front.py:352: AssertionError: assert [] == ['importar.ht...oficios.html']
…\tests\test_f036_front.py:454: AssertionError: el README no nombra importar.html
FAILED tests/test_f036_front.py::test_f036_t22_scripts_al_final_del_body_y_alpine_con_defer[importar.html]
FAILED tests/test_f036_front.py::test_f036_t22_ningun_boton_de_editar_descartar_ni_aprobar[ruta0]
FAILED tests/test_f036_front.py::test_f036_r65_boton_del_excel_de_errores - F...
FAILED tests/test_f036_front.py::test_f036_r98_boton_de_los_grupos_vigentes
FAILED tests/test_f036_front.py::test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas
FAILED tests/test_f036_front.py::test_f036_r89_el_html_solo_decide_desde_un_clic
FAILED tests/test_f036_front.py::test_f036_r93_la_bandeja_pinta_las_marcas_de_cada_fila
[… 27 líneas FAILED más …]
34 failed, 31 passed in 0.12s
```

Los 31 que pasaban: los 20 de `test_f007_estaticos.py` y 11 de F-036 que
miran lo ya hecho en T21 (la cabecera de ruta de los dos `.js`, «sin datos
reales» en los dos `.js` y sus dos tests, la guardia de datos reales, los dos
«el JS no llama a nada del circuito», `confirmado: true` en un solo sitio y
«solo `decidir()` llama al endpoint»). Al escribir las páginas, un test se
corrigió: el de las marcas buscaba `x-for="<nombre> in <nombre>.marcas"` y la
plantilla usa `(marca, n) in fila.marcas`; el patrón se amplió sin relajarlo
(sigue exigiendo `fila.marcas`). Y el de «la bandeja es de solo lectura»
pasó a medir desde la `<table>` y no desde el comentario del bloque, que
incluye el botón «Ver la bandeja» de su cabecera (fuera de la tabla).

### Verde

- `node --test "tests_js/*.test.js"` → **408 passed** en 0,91 s
  (`importacion.test.js` 40, `oficios.test.js` 24, `api.test.js` 69, de los
  que 22 son de F-036).
- `python -m pytest tests/test_f036_front.py tests/test_f007_estaticos.py -q` → **65 passed** en 0,14 s.
- Suite del front suelta (`python -m pytest -q`) → **301 passed** en 3,35 s.
- Del `api`: `tests/test_f036_alcance_cerrado.py` → **25 passed** (aparte:
  `init.sh` usó la caché del `api`, cuyo árbol no ha cambiado).
- `ruff check` y `ruff format` sin avisos en `tests/test_f036_front.py`.

Qué fijan los tests, además de lo de la tabla de la tarea:

- **T21, `api.js`**: ruta, método y obra escapada de los cinco; multipart sin
  `Content-Type` a mano; `importarExcel` sin reintento ante 502, red y tiempo
  agotado, sin decir «Reintentando»; 400/413/409/503 con el texto y el
  `codigo` del backend; el 503 de la entrada frente al de archivar; la
  plantilla binaria con su disposición, su timeout, sus errores (JSON y no
  JSON) y la red caída; `decidirCatalogos` sin reintento con el cuerpo tal
  cual; `bandeja` y `propuestas` que sí reintentan; la traza de los cinco
  (solo `hash`, `paso`, `estado`, `http`).
- **T21, `importacion.js`**: Content-Disposition en cinco formas y sin ruta;
  base64 exacto y vacío; el `Blob` del Excel de errores con su tipo; R69; los
  textos; errores ordenados de forma estable; R33; las tres marcas de
  duplicada y la de ambiguo; `guardarBlob` (clic, nombre y URL revocada); el
  componente: identidad, plantilla (bien, mal, sin obra), elegir fichero,
  R22 sin sesión, importar (orden de llamadas, obra fijada, bandeja
  recargada), rechazo sin reintento, doble clic, Excel de errores (con y sin),
  bandeja (bien, mal, sin obra), y que no tiene nada de editar, descartar,
  aprobar, rechazar, cerrar ni archivar.
- **T21, `oficios.js`**: motivos (y el desconocido), pares, propuestas con
  nombres y motivos, clique frente a por pares, solo grupos de más de uno
  con sus pares, código sin nombre (R84), obra vacía, cuerpo con
  `confirmado: true` booleano y sus rechazos (decisión mal escrita, un
  código, «distinto» de tres), JSON de R98 y su fichero; el componente:
  cargar no decide, decidir manda exactamente un cuerpo y recarga con la obra
  cargada, «Separar», sin vista o sin sesión no decide, doble clic, 409 sin
  recargar, fallo de carga, descarga de grupos (con y sin vista).
- **T22**: cabecera de ruta; carga (scripts propios en orden al final del
  `body`, sin `defer` ni `module`, Alpine fijo con `defer`, el componente y
  su `x-init`); nada en el navegador; sin datos reales; ningún `value=` de
  fábrica; ningún botón de editar/descartar/aprobar/rechazar/borrar/eliminar;
  el JS no llama a nada del circuito; los botones del Excel de errores (solo
  si lo hay) y de los grupos vigentes; los tres bloques de `importar.html`;
  los enlaces de R51 (en otra pestaña, y solo esos dos en la cabecera) y
  entre páginas; `confirmado: true` en un solo sitio; solo `decidir()` llama
  al endpoint; en el HTML, `decidir(` solo dentro de un `@click`; los tres
  botones de decisión con su `:disabled`; sin proveedores ni actividades ni
  `catalogos.html`; las marcas pintadas y la bandeja sin controles; el
  README. Cada guardia con su control negativo (una página estropeada en
  memoria: `defer`, `module`, script quitado o desplazado, un botón
  «Aprobar», un `decidir` en el `x-init`, un dato real).

### Mutación

- **Campaña del arnés** (`python -m harness.mutacion --feature F-036 --base b5e952f --workers 4 --timeout 600 --salida progress/mutacion_F-036_bloque7.md`,
  con `timeout 900`, sin nada en segundo plano): **0 ficheros, 0 líneas de
  producción, 0 mutantes**. El mutador del arnés solo muta Python, y el
  único `.py` del bloque es un test (`tests/` queda fuera del alcance).
- **Mutantes a mano del JavaScript** (un script en el directorio temporal
  que aplica cada cambio, ejecuta `node --test "tests_js/*.test.js"` y
  restaura el fichero; el árbol quedó limpio): **22 mutantes, 22 muertos**.
  - `api.js` (6): `importarExcel` con reintentos, el 503 sin el texto del
    backend, «Reintentando» sin reintento, sin `usuario_oid`, obra sin
    escapar, sin disposición.
  - `importacion.js` (8): errores sin ordenar, duplicada de otra importación,
    sin marca de ambiguo, sin aviso de recorte, sin revocar la URL, doble
    importación, importar sin `oid`, nombre con ruta.
  - `oficios.js` (8): `confirmado: "true"` en texto, «distinto» de tres,
    doble decisión, la obra del campo en vez de la cargada, sin recargar,
    grupos de uno en la vista, grupos de uno en el JSON, propuesta por pares
    confirmada entera.
  No es una campaña exhaustiva: son los puntos que sostienen R50, R52, R65,
  R88, R89 y R98. Nada que analizar.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de las tareas | T21: 86 de JavaScript (22 en `api.test.js`, 40 en `importacion.test.js`, 24 en `oficios.test.js`); T22: 45 en `tests/test_f036_front.py` |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed; servicio `api`: verde (caché: árbol sin cambios desde el último verde, 5727 passed del Bloque 6b); `front`: **301 passed** en 3,50 s (con los **408** de JavaScript a través de `test_f007_js.py`); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 2286 líneas cambiadas cubiertas (2285/2286, umbral 80%, nivel critico)`. **No mide este bloque**: la puerta solo cuenta `.py` de producción y el bloque no tiene ninguno (el JS y el HTML no los mide el arnés). La línea que falta es la de siempre: `raise SystemExit(main())` del script de T8 |
| Mutación | Arnés: 0 líneas en el alcance, 0 mutantes (`progress/mutacion_F-036_bloque7.md`). JavaScript a mano: 22 generados, **0 supervivientes** |
| Tiempo de la suite | JS: 0,91 s (408 tests); front con pytest: 3,35–3,50 s; `test_f036_front.py` + `test_f007_estaticos.py`: 0,14 s |
| Lint | `ruff check` y `ruff format` sin avisos en `tests/test_f036_front.py`; los `.js` compilan con `node --check` (`test_f007_js.py`) |
| MANUAL pendiente | **T16** (humano, del Bloque 5). **Ver las páginas en un navegador**: no se han abierto; lo que se ha probado es la lógica (node) y el HTML como texto. Se ven en T27 (`oficios.html`, obra 0677) y T29 (`importar.html`) en el entorno desplegado; en local, con `func start --port 7073` y `.\dev_front.ps1`, se puede ver la plantilla, la bandeja y las propuestas, pero no importar ni decidir (B7-4) |

### Qué queda fuera y qué falta

- **T16** (MANUAL, humano): sigue pendiente; el comando está en «Bloque 5».
- Editar, descartar o aprobar incidencias de la bandeja: **F-038**.
  Proveedores repetidos: **F-050**. Actividades: **F-039**.
- La integración con el portal de F-035 (sus placeholders de «Entrada»): de
  quien mergee segundo (arriba).
- **Bloque 8** (T23–T25): la migración del Excel actual.
- `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` y `azure-apps/` (las cinco
  rutas y las dos páginas): T26.
- Retoques de spec: §9 nombra `js/catalogos.js` y §8 escribe `proveedor` en
  las propuestas (B7-14, B6-18).
- Nada se ha ejecutado contra Sigrid ni PostgreSQL reales, y nada se ha
  abierto en un navegador.

## Bloque 8a (T23) · 2026-09-30 · hecho; T24 va en otro encargo, T25 es PARADA y T16 sigue siendo MANUAL del humano

> **Resumen para el líder.** T23 hecha (`ce3be66`), con `[x]` en `tasks.md`, más
> `ca976db` (los tests que destapó la mutación y el análisis de sus nueve
> supervivientes). Dos ficheros nuevos en `services/postventa-api/scripts/`:
> `migracion_f036.py` (la lógica, sin disco) y `migrar_excel_f036.py` (la CLI
> de `design.md` §10.3). **No reescriben nada**: el catálogo se compone con
> `leer_catalogo` sobre un puerto que lee el JSON de T2, las opciones con
> `opciones_de_la_obra` sobre un puerto que da las decisiones del fichero de
> grupos, el v2 con `GeneradorPlantillaOpenpyxl` y la vuelta con
> `LectorPlantillaOpenpyxl` + `reconocer_plantilla` + `validar_filas`: lo mismo
> que la plantilla y la importación del portal. 170 tests en
> `tests/test_f036_migracion.py`, con original, catálogo y grupos **falsos** en
> memoria y la CLI sobre un disco **en memoria** (ningún `.xlsx` toca el disco).
> `bash harness/init.sh` en verde. Mutación: 159 mutantes, 9 supervivientes,
> los 9 huecos reales, cerrados con tests y comprobados a mano. **No se ha
> ejecutado contra el Excel real ni contra el JSON de T2** (eso es T24). Para
> el humano, sobre todo: B8-1 (cotejo con blancos colapsados), B8-4 (urgencia
> y listado por código en el YAML) y B8-5 (R91 solo si el par resuelve al mismo
> código).

### Qué cambió

| Fichero (bajo `services/postventa-api/`) | Qué |
|---|---|
| `scripts/migracion_f036.py` (nuevo) | `leer_correcciones` (forma de §10.2; falla a la primera con el sitio exacto), `leer_original` (primera hoja, columnas A–F, `read_only` y `data_only`), `cotejar` (R54), `revisar_contenido` (lo de R57 que hace cumplir el script, §10.2), `CatalogoDeFichero` + `catalogo_de_la_obra` (R55), `decisiones_de_grupos` + `EquivalenciasDeFichero` (R97, R98), `componer` (R91, R97), `ida_y_vuelta` (R56), `migrar` (pasos 2–4 de §10.3) e `informe` (R58, §10.4) |
| `scripts/migrar_excel_f036.py` (nuevo) | CLI: `--original`, `--catalogo`, `--correcciones`, `--grupos`, `--salida`, `--informe`, `--sobrescribir`, `--solo-informe`. R53 (rutas y `sha256` antes y después), R97 (sin `--grupos`, solo `--solo-informe`). `Disco` inyectable; `DiscoLocal` escribe con `xb` sin `--sobrescribir` |
| `tests/test_f036_migracion.py` (nuevo) | 170 tests |
| `specs/F-036-importar-excel/tasks.md` (raíz) | T23 `[x]` |
| `progress/mutacion_F-036_bloque8a.md` (raíz, nuevo) | Campaña del arnés, con el análisis de los 9 supervivientes |

Sin dependencias nuevas (`openpyxl` y `yaml` ya estaban). Sin red, Sigrid,
base ni IA. Ningún nombre de proveedor en el repositorio: los de los tests son
«Proveedor Inventado …». No se ha tocado el dominio, los adaptadores ni la
aplicación: solo se usan.

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B8-1 · Cotejo con los blancos colapsados (R54).** La ubicación y el texto
   del original casan con los de la tabla si son iguales tras colapsar blancos
   (saltos de línea incluidos) y recortar los extremos. Mayúsculas, tildes y
   puntuación, tal cual. Motivo: la tabla se redacta desde el Markdown de
   `docs/referencia/05_…`, que no enseña blancos de más ni finales, y el
   cotejo está para detectar filas cambiadas o corridas, no espacios
   invisibles. 05 trae «REHACER  el rodapie» y un salto de línea dentro de una
   celda: casan escritos con un blanco.
2. **B8-2 · `origen` es el número de fila de Excel** de una fila con algún dato
   en A–F; las vacías no cuentan (una en blanco en medio se salta y la
   numeración sigue la de Excel). La tabla tiene que ir **en el orden del
   original** (§10.2 «en su orden»): si no, para.
3. **B8-3 · Una sola unidad.** El YAML lleva una `unidad` para todas las filas;
   si la columna A del original trae dos valores distintos (con blancos
   colapsados), para. La `unidad` del YAML tiene que ser **exactamente** una
   etiqueta del desplegable de unidades de la obra.
4. **B8-4 · `urgencia` y `listado` van por código** en el YAML (`urgente`,
   `seguridad`; `primero`, `segundo`) y el script escribe la etiqueta del YAML
   de la plantilla. La spec no lo fija (§10.2 solo pone `null`); se elige el
   código por lo mismo que el oficio va por nombre de Sigrid y no por
   etiqueta: las etiquetas pueden cambiar. **T24 tiene que escribirlo así.**
5. **B8-5 · R91 exige además que el par resuelva al mismo código** que dio el
   nombre del YAML. Con los grupos confirmados, el único par del grupo
   `0033`/`0133` es de `0033`: completarlo en una fila de `0133` la
   resolvería a `0033` al importar y cambiaría el oficio elegido. Así se
   cumple lo que dice `tasks.md` T23 («`0133`, `0144` y `0166` … quedan sin
   él»), que con la letra sola de R91 no se cumpliría. Tests
   `test_f036_r91_con_grupos` y `…_resuelve_al_mismo_oficio_al_importar`.
6. **B8-6 · El nombre de Sigrid se compara recortado** por los extremos
   (`auxofc.res` podría arrastrar blancos que el YAML no ve); el del YAML, tal
   cual (« Pintura» no vale). Un nombre que es el de **dos** oficios de la
   obra para («no se puede elegir»). Todos los nombres malos se dicen a la vez.
7. **B8-7 · Reutilización por puertos.** `CatalogoDeFichero` implementa
   `CatalogoObraPort` con `fila_a_unidad_catalogo`/`fila_a_oficio_catalogo`
   del adaptador de Sigrid, y `leer_catalogo` compone el catálogo (oficios
   distintos, primer nombre, unidades sin código fuera).
   `EquivalenciasDeFichero` implementa `EquivalenciasPort`: de cada grupo del
   fichero salen decisiones «mismo» entre **todos** sus pares, y devuelve solo
   las que tienen los dos códigos entre los pedidos, como el repositorio
   (B6-3). `registrar` levanta: la migración no escribe decisiones.
8. **B8-8 · El fichero de grupos, a prueba de errores**: claves exactamente
   `obra` y `oficio`, grupos de dos o más códigos de texto, ningún código
   repetido y la obra (normalizada) la de la tabla. Códigos que no son de la
   obra se admiten y no estorban (R84).
9. **B8-9 · Cuándo «cambia» una fila** (para exigir `cambios`, §10.2): si no
   es exactamente una fila nueva con la ubicación, el texto y el oficio del
   original y sin detalle, urgencia ni listado. Descartar (`resultado: []`)
   también exige motivo. `propuesto` solo admite nombres de campo de la fila
   nueva.
10. **B8-10 · Textos prohibidos (R57, §10.2)**, plegados: «peligro de
    seguridad», «como en los otros», «como en todos», «igual que» y, además,
    los femeninos «como en las otras» y «como en todas» (la misma remisión).
11. **B8-11 · Rutas (R53).** Además de `--salida` = original, se niega
    `--informe` = original y `--informe` = `--salida`. La comprobación de
    `--salida` existente se hace también con `--solo-informe` (§10.3: «hace
    1–4»), así que regenerar el informe con un v2 ya escrito pide
    `--sobrescribir` (con `--solo-informe` el v2 no se toca igualmente).
    `--salida` es obligatoria siempre (el comando de T24 la pasa). El informe
    se reescribe en cada ejecución que llega al final. Si el `sha256` del
    original cambia, el v2 y el informe **ya** están escritos: el error lo
    dice y sale con 1.
12. **B8-12 · Códigos de salida**: 0 bien, 1 parada (con la lista de
    problemas, sin escribir nada), 2 uso (argparse, y sin `--grupos` ni
    `--solo-informe`, antes de leer nada).
13. **B8-13 · El informe** agrupa por ubicación original en el orden de su
    primera aparición (en 05 «DORMITORIO 1» vuelve después de «DORMITORIO 1
    TERRAZA»). Cada fila nueva dice ubicación, descripción, detalle, oficio
    (nombre de Sigrid, código y, si difiere, la etiqueta del v2 y cuántos
    códigos tiene su grupo en la obra), proveedor **solo** como «proveedor
    completado (único de la obra para ese oficio), código `P…`», urgencia,
    listado y los avisos del importador **sin** los que nombran un proveedor.
    Un proveedor completado añade «proveedor» a `propuesto`. Recuentos: los de
    §10.4 más «filas nuevas con algún aviso». «Oficios de la muestra que no son
    exactamente un nombre de Sigrid» se cuenta por fila original; «oficio cuyo
    grupo tiene varios códigos», por fila nueva (las que entrarían
    `oficio_ambiguo` si no llevan proveedor).
14. **B8-14 · Los tests usan la configuración real de la plantilla**
    (`config/plantilla_incidencias.yaml`, como el resto de tests de F-036), no
    una inventada: el v2 tiene que pasar las listas de verdad.

### Fase RED

Tests escritos **antes** que el código, desde `services/postventa-api`:

`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -q`

```text
=================================== ERRORS ====================================
________________ ERROR collecting tests/test_f036_migracion.py ________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_migracion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_migracion.py:42: in <module>
    from scripts import migracion_f036 as mig
E   ImportError: cannot import name 'migracion_f036' from 'scripts' (unknown location)
=========================== short test summary info ===========================
ERROR tests/test_f036_migracion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.79s
```

Un error de importación solo prueba que el código no existía. Para los
requisitos **centrales** (R53, R54, R91, R97 y R56) se sustituyó a propósito
el código bueno por uno equivocado, se lanzaron sus tests y se restauró el
fichero (script en `%TEMP%`, `git status` limpio después):

```text
### R53: la salida puede ser el original   (if salida == original: -> if False:)
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k r53_salida_igual -q --tb=line
E   AssertionError: assert '--salida es el original: se niega a escribir encima (R53)' in 'ERROR: la migración se ha parado sin escribir nada:\n  - --salida ya existe: pasa --sobrescribir para reemplazarla (R53)\n'
FAILED tests/test_f036_migracion.py::test_f036_r53_salida_igual_al_original_se_niega[entrada/creacion_incidencias.xlsx]
FAILED tests/test_f036_migracion.py::test_f036_r53_salida_igual_al_original_se_niega[entrada/../entrada/creacion_incidencias.xlsx]
FAILED tests/test_f036_migracion.py::test_f036_r53_salida_igual_al_original_se_niega[./entrada/creacion_incidencias.xlsx]
3 failed, 160 deselected in 0.63s

### R54: no se coteja el texto   (if _colapsado(suyo) != _colapsado(dice): -> if False:)
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k r54 -q --tb=line
E   Failed: DID NOT RAISE MigracionDetenida
E   Failed: DID NOT RAISE MigracionDetenida
E   AssertionError: assert ('falta la fi...orrecciones',) == ('falta la fi... dice «otro»')
FAILED tests/test_f036_migracion.py::test_f036_r54_ubicacion_o_texto_que_no_casan
FAILED tests/test_f036_migracion.py::test_f036_r54_mayusculas_distintas_no_casan
FAILED tests/test_f036_migracion.py::test_f036_r54_todos_los_problemas_a_la_vez
3 failed, 22 passed, 138 deselected in 2.95s

### R91: se completa aunque el par resuelva a otro código   (sin «oficio.codigo != codigo»)
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k r91 -q --tb=line
E   AssertionError: assert ['Pintura · P...do Seis', ...] == ['Pintura · P...ne, None, ...]
      At index 2 diff: 'Solados y Alicatados · Proveedor Inventado Cuatro' != None
E   AssertionError: assert [('0010', 'P0... 'P006'), ...] == [('0010', 'P0...e, None), ...]
      At index 2 diff: ('0033', 'P004') != (None, None)
FAILED tests/test_f036_migracion.py::test_f036_r91_con_grupos - AssertionErro...
FAILED tests/test_f036_migracion.py::test_f036_r91_el_proveedor_completado_resuelve_al_mismo_oficio_al_importar
2 failed, 1 passed, 160 deselected in 1.76s

### R97: sin --grupos se admite escribir el v2   (la guarda de main -> if False:)
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k r97_sin_grupos -q --tb=line
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_migracion.py:1517: AssertionError: assert 0 == 2
FAILED tests/test_f036_migracion.py::test_f036_r97_sin_grupos_y_sin_solo_informe_se_niega_sin_leer_nada
1 failed, 1 passed, 161 deselected in 1.29s

### R56: los errores del importador no paran   (if con_error: -> if False:)
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k r56_errores -q --tb=line
E   AssertionError: assert ('el v2 trae ...cribieron 7',) == ('fila 2 del ... a «Detalle»')
      At index 0 diff: 'el v2 trae 5 filas válidas al volver a leerlo y se escribieron 7' != 'fila 2 del original (fila 3 del v2), Ubicación: ese valor no está en la lista de ubicaciones: elígelo del desplegable (cuidado con mayúsculas, tildes y espacios)'
FAILED tests/test_f036_migracion.py::test_f036_r56_errores_del_importador_paran_con_la_fila_del_original
1 failed, 162 deselected in 0.92s
```

Lo que enseñó el sabotaje de R53: con la guarda quitada, ese caso lo paraba
igual «--salida ya existe» (el original existe). Con `--sobrescribir` esa
segunda barrera no está, así que el test se amplió a los dos casos (con y sin
`--sobrescribir`) antes del commit de T23.

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -q` →
**170 passed** en 14,4 s. Cobertura de rama con `coverage.py` sobre los dos
scripts (antes de los tests de la mutación): `migracion_f036.py` 399
sentencias y 132 ramas, 99 %; `migrar_excel_f036.py` 100 y 18, 98 %. Faltaban
la línea del listado del informe (test añadido) y `raise SystemExit(main())`,
que se ejecuta en el test que lanza el script en un subproceso y `coverage` no
mide.

### Mutación

Campaña oficial sobre las líneas de T23 (alcance contra `588f3ce`, el cierre
del Bloque 7), con tope de tiempo (`timeout 5400`) y sin dejar nada en segundo
plano al entregar:
`python -m harness.mutacion --feature F-036 --base 588f3ce --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque8a.md`.
Alcance: 2 ficheros, 1244 líneas de producción.

1. **Pasada** (sobre `ce3be66`): **159 mutantes, 150 muertos, 9
   supervivientes, 0 timeouts**, 5267,9 s con 6 workers (dentro del tope). Los
   9, **huecos reales**, ninguno equivalente:
   - `COLUMNAS_ORIGINAL = 6 → 7`: ningún original de prueba traía nada en la
     columna G;
   - `frozen=False` en `FilaNueva`;
   - `<= → <` en `propuesto`: solo difieren con los seis campos a la vez;
   - `read_only=False` y `data_only=False` en `load_workbook` (el segundo
     leería una fórmula por su texto);
   - `codigos_en_obra=0 → 1` en una fila sin oficio;
   - tres en el texto del oficio del informe (`or → and`, `> 1 → > 2`,
     `> 1 → >= 1`): faltaban los casos «etiqueta distinta con grupo de un
     código» y «etiqueta igual con grupo de dos».
2. **Tests nuevos** en `ca976db`: `…mas_alla_de_la_columna_f_no_se_lee`,
   `FilaNueva` en `…resultados_inmutables`,
   `…propuesto_admite_todos_los_campos`,
   `…el_original_se_abre_solo_para_leer_y_por_sus_valores` (espía de
   `load_workbook`), las listas enteras de `codigos_en_obra` en los dos tests
   de R97 y `…el_oficio_dice_la_etiqueta_del_v2_cuando_no_es_su_nombre`.
   **Comprobado a mano** aplicando cada uno de los 9 mutantes y lanzando
   `tests/test_f036_migracion.py -x`: los 9 dan `1 failed`. No se lanzó una
   segunda pasada entera (otra hora y media): el análisis de cada
   superviviente está escrito en `progress/mutacion_F-036_bloque8a.md`, sin
   ningún `PENDIENTE`.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de la tarea | `tests/test_f036_migracion.py`: **170 passed** en 14,4 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 3,67 s; servicio `api`: **5899 passed, 67 skipped** en 227,97 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2785 líneas cambiadas cubiertas (2783/2785, umbral 80%, nivel critico)`. Las dos que faltan son `raise SystemExit(main())` de los scripts de T8 y T23, que se ejecutan en un subproceso |
| Mutación | 159 generados, 150 muertos, **9 supervivientes, los 9 cerrados con tests** y comprobados a mano; 0 timeouts (`progress/mutacion_F-036_bloque8a.md`) |
| Tiempo de la suite | `api` 227,97 s; el fichero nuevo 14,4 s; campaña 5267,9 s |
| Lint | `ruff check` y `ruff format` sin avisos en los tres ficheros nuevos |
| MANUAL pendiente | **T16** (humano, del Bloque 5). El script **no se ha ejecutado contra el Excel real ni contra el JSON de T2**: eso es T24 |

### Qué queda fuera y qué falta

- **T24** (otro encargo): redactar `scripts/migracion_f036_correcciones.yaml`
  con urgencia y listado **por código** (B8-4) y los oficios como nombres
  exactos de Sigrid, generar `progress/migracion_F-036.md` con
  `--solo-informe` y escribir `tests/test_f036_migracion_contenido.py`. Si el
  cotejo del original real falla, el script dice fila por fila qué no casa.
- **T25** (PARADA): el humano revisa el informe.
- **T16** (MANUAL, humano): sigue pendiente; el comando está en «Bloque 5».
- T27–T29, del humano (despliegue, grupos confirmados, v2 definitivo con
  `--grupos` y la verificación desplegada).

## Bloque 8b (T24) · 2026-09-30 · hecho; T25 es PARADA del líder con el humano y T16 sigue siendo MANUAL del humano

> **Resumen para el líder.** T24 hecha (`6b0ae24`), con `[x]` en `tasks.md`.
> La propuesta de migración está en
> `services/postventa-api/scripts/migracion_f036_correcciones.yaml` y el
> informe para el humano, generado con el comando de T24 y `--solo-informe`
> contra el **Excel real** y el **JSON de T2**, en `progress/migracion_F-036.md`:
> **144 filas originales → 158 filas nuevas, 0 errores** en la ida y vuelta por
> el importador, `sha256` del original igual antes y después. 30 tests nuevos
> en `tests/test_f036_migracion_contenido.py` sobre el YAML real. `bash
> harness/init.sh` en verde. **Siguiente: T25 · PARADA** (el humano revisa el
> informe; los cambios, en el YAML, y se regenera).

### Resumen para el humano (T25)

- **Filas**: 144 originales → **158** nuevas. **14 separadas**, **0
  descartadas**. 12 filas nuevas con urgencia «Peligro para la seguridad» (de
  las 11 filas originales con «PELIGRO DE SEGURIDAD»; la 50 se parte en dos y
  las dos la llevan) y 1 «Urgente» (la 15, «ERROR ESTRUCTURAL», con el texto en el
  detalle). Listado vacío en todas (D-5).
- **Oficios**: los 41 que traía la muestra se conservan; los 9 «Solados y
  alicatados» pasan a «Solados y Alicatados» (`0133`), el nombre exacto de
  Sigrid. De las 103 filas originales sin oficio salen 77 filas nuevas con
  oficio propuesto; **37 filas nuevas quedan sin oficio** porque el texto no
  permite deducirlo con seguridad, y `cambios` dice los candidatos
  (correderas del office, la cocina y el salón, garaje, techos irregulares,
  barandillas…). El informe cuenta 46 proveedores completados por R91 **sin
  grupos**: con los grupos confirmados en T27 cambiará (T28).
- **Filas separadas** (una por defecto; criterio: elementos u oficios
  distintos, o un «Además» en el texto; varios síntomas del mismo elemento se
  quedan juntos): 9 (rodapié · suelo porcelánico), 11 y 27 (uniones de
  albardillas · relleno de hueco), 42 (hoja de ventana · grifo), 50 (pared del
  casoneto · puerta corredera), 77 (mecanismos torcidos · pintura), 92 (laca
  arañada · silicona entre cristales), 93 (puerta del congelador · melamina),
  100 (sellado suelo-pared · puerta de la despensa), 108 (techos irregulares ·
  encuentro de focos), 120 (tela asfáltica · desagües), 140 (mecanismos
  sueltos · remate alrededor), 142 (pandeos · aristas) y 143 (aguas de los
  techos · cantos de las candilejas).
- **Filas marcadas para revisar: 41**, con `# REVISAR:` en el YAML y el mismo
  texto en `cambios` (sale en el informe):
  - **Ubicación sin equivalente claro**: 37 filas (tabla de abajo).
  - **9**: la muestra da «Solados y alicatados» a toda la fila; el rodapié, si
    es de madera como en las filas 8 y 14, sería Carpintería de madera.
  - **42**: «no se corta grifo» se lee como un segundo defecto (el grifo no
    corta el agua); si quiere decir que la ventana no abre por el grifo, es una
    sola fila.
  - **50**: un solo «PELIGRO DE SEGURIDAD» al final de la fila; se aplica a las
    dos filas nuevas.
  - **81**: «como en todos los baños» se reescribe como «Según la muestra, pasa
    en todos los baños de la vivienda.» en el detalle; ¿se prefiere una fila
    «General (toda la unidad)»?
  - **142**: habla de la escalera y la muestra la pone en GENERALES; se deja
    «General» (¿o «Escalera», donde ya está la fila 15?).
- **Ubicaciones sin equivalente** (Bloque 1, pregunta 4; T9 las dejó para la
  migración). Regla: **nunca se elige un número de baño o de terraza que la
  muestra no dice**. O la estancia a la que pertenece el sitio, con el sitio en
  el detalle (como ya hace la propia muestra, que pone baños y terrazas de los
  dormitorios bajo «DORMITORIO N»), o «Otra (explicar en el detalle)» con
  «Ubicación en el Excel original: …» en el detalle. `ubicacion` va en
  `propuesto` en todas.

  | Original | Filas orig. | Propuesta | Alternativa que decide el humano |
  |---|---:|---|---|
  | `TIRO DE ESCALERA` | 4 | Escalera | (§10.2, sin marca) |
  | `GENERALES` | 5 | General (toda la unidad) | (§10.2, sin marca; la 142, marcada) |
  | `TERRAZA` | 4 | Otra + «TERRAZA, sin decir cuál» | Terraza 1, 3, 4, planta 2 o de instalaciones |
  | `VENTANA PATIO` | 1 | Otra + «sin decir de qué estancia es la ventana» | ¿la misma ventana de la fila 1 (Sala/estudio)? |
  | `DORMITORIO 1 TERRAZA` | 2 | Dormitorio 1 + «En la terraza del dormitorio 1.» | ¿Terraza 1? |
  | `DORMITORIO N BAÑO` y `DORMITORIO BAÑO 1` | 13 | Dormitorio N + «En el baño del dormitorio N.» | ¿qué Baño N? |
  | `VENTANAS` | 1 | General (toda la unidad) | — |
  | `PASILLO` | 1 | Otra + «sin decir de qué planta» | ¿Distribuidor planta baja o planta 1? |
  | `PASILLO DORMITORIO 1` | 1 | Dormitorio 1 + «En el pasillo del dormitorio 1.» | ¿Distribuidor planta 1? |
  | `VESTIBULO` | 6 | Vestíbulo planta baja (sus filas hablan de la planta baja) | ¿Vestíbulo sótano? |
  | `PATIO SOTANO` | 2 | Otra + «PATIO SOTANO» | ¿Patio trasero o delantero? |
  | `BAÑO PLANTA BAJA` | 7 | Otra + «BAÑO PLANTA BAJA» | ¿Aseo o un Baño N? |

  El resto son normalizaciones directas (`SALA/ ESTUDIO` → Sala/estudio,
  `SALON` → Salón, `LAVANDERIA` → Lavandería…).

### Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/scripts/migracion_f036_correcciones.yaml` (nuevo) | La propuesta, fila a fila (§10.2): cabecera con los criterios, una entrada por fila del original, urgencia por código (B8-4), oficios con su nombre exacto de Sigrid, marcas `# REVISAR:` |
| `progress/migracion_F-036.md` (nuevo, generado) | El informe de §10.4, con `--solo-informe` y sin `--grupos` |
| `services/postventa-api/tests/test_f036_migracion_contenido.py` (nuevo) | 30 tests sobre el YAML real |
| `progress/explore_F-036.md` | Sección nueva «Los 31 oficios de la 0677, nombres exactos de Sigrid (T24)»: código y nombre, sin proveedores (B8b-2) |
| `specs/F-036-importar-excel/tasks.md` | T24 `[x]` |
| `progress/mutacion_F-036_bloque8b.md` (nuevo) | Campaña del arnés: 0 líneas de producción en el alcance |

Sin código de producción, sin dependencias, sin red, Sigrid, base ni IA en los
tests. El Excel original **solo se ha leído** (el `sha256` lo prueba) y el v2
no se ha escrito; `--salida` apuntaba al scratchpad de la sesión, no a
OneDrive. Ningún `.xlsx` en git.

### Decisiones y desviaciones (para el reviewer y el humano)

1. **B8b-1 · «Baño del dormitorio 1» no existe en la lista.** §10.2 pone de
   ejemplo `DORMITORIO 1 BAÑO` → `Baño del dormitorio 1`, pero la lista cerrada
   de T6 (aprobada en T9) no la tiene y R57 exige la lista cerrada. No se
   añade (tocar `config/plantilla_incidencias.yaml` no es de T24): se aplica la
   regla de arriba y se marca. Si el humano quiere esa ubicación, es añadirla
   al YAML de la plantilla y cambiar las 13 filas.
2. **B8b-2 · La lista de oficios «anotada en T2» no estaba completa.**
   `explore_F-036.md` solo tenía los 8 del Excel y 3 gemelos. Se añadieron los
   31 (código y `auxofc.res` tal cual, sacados del JSON de T2 sin ningún dato
   de proveedor) y el test la lee de ahí. Se comprobó por programa, sin
   imprimirlos, que **ninguno de los 36 nombres de proveedor** del JSON aparece
   en el YAML, el informe, el test ni `explore` (0 coincidencias).
3. **B8b-3 · Oficio por precedente.** Donde la muestra no trae oficio, se
   propone solo si el texto lo dice o si la muestra ya da oficio a un defecto
   igual en otra fila (y `cambios` cita la fila). Se respeta el oficio de la
   muestra aunque sorprenda («Mobiliario cocina» para las miras de hierro de
   las encimeras de los baños) y se extiende a las filas 70, 80 y 133, que
   repiten el mismo texto.
4. **B8b-4 · Texto: lo mínimo.** Erratas evidentes, tildes y mayúsculas de
   énfasis. Tres que son interpretación y van en `cambios`: «espotillada» →
   «desportillada» (98), «rallada/ralla» → «rayada/raya», «aacc» → «aire
   acondicionado». «Casoneto» se deja tal cual.
5. **B8b-5 · Marca doble.** El informe no ve los comentarios del YAML, así que
   cada `# REVISAR: …` va también en `cambios` como «REVISAR: …»; dos tests
   exigen que casen en los dos sentidos.
6. **B8b-6 · El test de punta a punta no lee el Excel real.** Rehace el
   original en memoria desde el Markdown del doc. 05 (R59) y usa un catálogo
   falso con los 31 nombres reales y proveedores inventados; pasa sin grupos y
   con los tres grupos de la 0677. Lo real se comprobó con el comando de T24
   (abajo).

### Comando de T24 (desde `services/postventa-api`)

```text
$ .venv/Scripts/python.exe scripts/migrar_excel_f036.py --original "C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\creacion_incidencias.xlsx" --catalogo "C:\Users\pgris\AppData\Local\Temp\catalogo_0677.json" --correcciones scripts/migracion_f036_correcciones.yaml --salida "<scratchpad de la sesión>\creacion_incidencias_v2.xlsx" --informe ../../progress/migracion_F-036.md --solo-informe
Migración F-036 · obra 0677 · sin --grupos: cada código es su propio grupo
Filas del original: 144 · filas nuevas: 158 · separadas: 14 · descartadas: 0
Ida y vuelta por el importador: 0 errores
Informe: C:\Users\pgris\PycharmProjects\postventa-incidencias\progress\migracion_F-036.md
v2: no se escribe (--solo-informe)
sha256 del original antes:   4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
sha256 del original después: 4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
salida=0
```

### Fase RED

Tests escritos **antes** que el YAML, desde `services/postventa-api`:

`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion_contenido.py -q --tb=line`

```text
E   FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-incidencias\\services\\postventa-api\\scripts\\migracion_f036_correcciones.yaml'
...
FAILED tests/test_f036_migracion_contenido.py::test_f036_el_yaml_no_nombra_proveedores
FAILED tests/test_f036_migracion_contenido.py::test_f036_r56_la_propuesta_pasa_tambien_con_los_tres_grupos_de_la_0677
ERROR tests/test_f036_migracion_contenido.py::test_f036_r56_la_propuesta_pasa_el_importador_sin_errores
ERROR tests/test_f036_migracion_contenido.py::test_f036_r58_el_informe_de_la_propuesta_no_lleva_nombres_de_proveedor
27 failed, 1 passed, 2 errors in 0.55s
```

El que pasa es `…la_unidad_del_doc_05_es_solo_villa_1`, que solo lee el doc.
05. La lista de oficios, antes de anotarla en `explore`:

```text
E   StopIteration
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_migracion_contenido.py:100: StopIteration
FAILED tests/test_f036_migracion_contenido.py::test_f036_r97_la_lista_de_oficios_de_la_0677_esta_anotada
```

Como un fichero que falta solo prueba que no existía, para los requisitos
**centrales** se estropeó a propósito el YAML bueno, se lanzaron sus tests y se
restauró (copia en el scratchpad, `diff` limpio después):

```text
### R57 peligro: se deja en la descripción (fila 4)
E   AssertionError: assert ['fila 4 del ...e seguridad»'] == []
1 failed, 1 passed, 28 deselected in 0.68s
### R57 urgencia: se olvida pasarla (fila 4)
E   AssertionError: 4
1 failed, 29 deselected in 0.59s
### R57 descripción de 129
E   scripts.migracion_f036.MigracionDetenida: fila 1 del original (fila 2 del v2), Descripción corta: la descripción corta tiene 129 caracteres y el máximo es 128: deja lo esencial y pasa el resto a «Detalle»
E   assert [(1, 1, 129)] == []
2 failed, 27 deselected, 1 error in 1.27s
### R57 ubicación fuera de la lista (Baño del dormitorio 1)
E   scripts.migracion_f036.MigracionDetenida: fila 39 del original (fila 43 del v2), Ubicación: ese valor no está en la lista de ubicaciones: elígelo del desplegable (cuidado con mayúsculas, tildes y espacios)
E   AssertionError: assert [(39, 'Baño d...ormitorio 1')] == []
1 failed, 28 deselected, 1 error in 0.92s
### R57 remisión que se queda (fila 73)
E   AssertionError: assert ['fila 73 del...n los otros»'] == []
1 failed, 1 passed, 28 deselected in 0.65s
### R57 fila 50 sin separar
E   assert {9, 11, 27, 42, 77, 92, ...} == frozenset({9,... 50, 77, ...})
1 failed, 29 deselected in 0.54s
### R97 oficio no exacto (fila 7)
E   scripts.migracion_f036.MigracionDetenida: fila 7 del original, fila nueva 1: el oficio «Solados y alicatados» no es exactamente el nombre de un oficio de la obra en Sigrid
E   AssertionError: assert [(7, 'Solados y alicatados')] == []
E   AssertionError: assert 'Solados y Alicatados' in {'Solados y alicatados'}
2 failed, 4 passed, 23 deselected, 1 error in 1.10s
### R54 falta una fila (la 144 pasa a 145)
E   scripts.migracion_f036.MigracionDetenida: falta la fila 144 del original en la tabla de correcciones; la fila 145 de la tabla no es una fila con datos del original
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 2, 3, 4, 5, 6, ...]
1 failed, 28 deselected, 1 error in 0.75s
### REVISAR sin su cambio (fila 12)
E   AssertionError: 12
1 failed, 2 passed, 27 deselected in 0.71s
```

### Verde

`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion_contenido.py -q`
→ **30 passed** en 3,90 s. `ruff check` y `ruff format` (desde la raíz) sin
avisos en el fichero nuevo.

### Mutación

`python -m harness.mutacion --feature F-036 --base 8fde6cd --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque8b.md`
→ «0 fichero(s), 0 línea(s) de producción»: T24 no añade código de producción
(un YAML de datos, un test y documentos), así que **0 mutantes y 0
supervivientes**. Aquí hacen de mutación los nueve sabotajes del YAML de la
fase RED, y los nueve se cazan.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de la tarea | `tests/test_f036_migracion_contenido.py`: **30 passed** en 3,90 s |
| Suite completa (`bash harness/init.sh`) | raíz: 62 passed en 3,75 s; servicio `api`: **5929 passed, 67 skipped** en 235,54 s; `front`: verde (caché); `ENTORNO LISTO` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2785 líneas cambiadas cubiertas (2783/2785, umbral 80%, nivel critico)` (igual que en el Bloque 8a: T24 no añade líneas de producción) |
| Mutación | 0 líneas de producción en el alcance, 0 mutantes (`progress/mutacion_F-036_bloque8b.md`); 9 de 9 sabotajes del YAML cazados |
| Tiempo de la suite | `api` 235,54 s; el fichero nuevo 3,90 s |
| Contra lo real | comando de T24: 144 → 158, **0 errores**, `sha256` igual antes y después |
| MANUAL pendiente | **T16** (humano, del Bloque 5) |

### Qué queda fuera y qué falta

- **T25 · PARADA**: el humano revisa `progress/migracion_F-036.md` y las 41
  marcas. Los cambios van en el YAML; se regenera el informe con el mismo
  comando y se vuelven a pasar los tests (si cambian las filas separadas, se
  actualiza `PARTIDAS` en el test).
- **T16** (MANUAL, humano): sigue pendiente; el comando está en «Bloque 5».
- T26–T30 (documentación, despliegue, grupos confirmados, v2 definitivo con
  `--grupos`, verificación desplegada, cierre). Con los grupos, el informe
  cambiará en los oficios de grupo de varios códigos y en los proveedores de
  R91: T28 dice parar y enseñarlo si difiere del aprobado.

## T25 · cambios aplicados (2026-09-30)

> Decisiones del humano en `progress/current.md`, «T25 (PARADA) decidida»
> (`7552726`). T25 `[x]` en `tasks.md`: su verificación es esa aprobación.

**Qué cambió**

- `config/plantilla_incidencias.yaml` (la lista de T6): se añaden «Baño del
  dormitorio 1»…«4», «Pasillo» y «Terraza», con `origen: []` y `revisar`
  «Añadida en T25 por decisión del humano: …», cada una en su sitio
  alfabético. Las 44 medidas siguen una vez cada una y las 40 medidas no
  cambian (tests de T6 intactos). Tests nuevos en
  `tests/test_f036_configuracion_plantilla.py`: las añadidas son exactamente
  las 2 de T6 y las 6 de T25, las de T25 dicen «T25», y su posición en el
  desplegable. La lista pasa de 42 a **48** ubicaciones.
- `scripts/migracion_f036_correcciones.yaml`: `DORMITORIO N BAÑO` y
  `DORMITORIO BAÑO 1` → «Baño del dormitorio N» (13 filas, sin el baño en el
  detalle); `BAÑO PLANTA BAJA` → «Aseo» (7); `VESTIBULO` se queda en
  «Vestíbulo planta baja» (6); `TERRAZA` → «Terraza» (4); `PASILLO` →
  «Pasillo» y `PASILLO DORMITORIO 1` → «Pasillo» con «Pasillo del dormitorio
  1.» en el detalle; `DORMITORIO 1 TERRAZA` → «Dormitorio 1» con la terraza en
  el detalle (como estaba); `VENTANA PATIO` → **«Sala/estudio»** con «La
  ventana que da al patio.» en el detalle, porque la única otra ventana de la
  muestra que choca con el ascensor es la de la fila 1; `PATIO SOTANO` →
  **«Almacén»** con «En el patio del sótano.» en el detalle, porque el almacén
  es la estancia que sale al patio (fila 115); fila 142 → «Escalera». Filas 9,
  42, 50 y 81 se quedan como se propusieron, con un «T25: …» en `cambios`.
  Ya **no queda ninguna fila en «Otra (explicar en el detalle)»**.
- `tests/test_f036_migracion_contenido.py`: el test de «ubicaciones sin
  equivalente marcadas» pasa a comprobar **las decididas** (tabla fija de T25,
  la 142 incluida), que el sitio va en el detalle cuando la ubicación es la
  estancia, qué filas quedan marcadas y que 9, 42, 50 y 81 siguen como se
  propusieron. Sale el `assert marcas` («la propuesta marca algo»): tras T25
  podría no quedar ninguna.
- `progress/migracion_F-036.md`, regenerado con el mismo comando de T24.

**Filas que quedan marcadas `REVISAR`: 3.**

- **46** (`VENTANAS` → «General (toda la unidad)»): T25 no la nombra; se deja
  la propuesta y la marca.
- **120 y 121** (`PATIO SOTANO` → «Almacén»): no hay forma de saber si el
  patio del sótano es el trasero o el delantero; se lleva a la estancia que
  sale a él, como pidió el humano, y se marca por si prefiere un patio.

**Recuentos finales** (comando de T24, contra el Excel real y el JSON de T2):

```text
Migración F-036 · obra 0677 · sin --grupos: cada código es su propio grupo
Filas del original: 144 · filas nuevas: 158 · separadas: 14 · descartadas: 0
Ida y vuelta por el importador: 0 errores
v2: no se escribe (--solo-informe)
sha256 del original antes:   4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
sha256 del original después: 4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
```

Sin cambios respecto a T24 en filas, separadas, oficios (77 completados, 37
filas nuevas sin oficio, 9 nombres corregidos), urgencias (12 de seguridad y 1
urgente) ni proveedores de R91 (46, sin grupos). Ubicaciones de las 158
filas: Dormitorio 1 23, Cocina 14, Dormitorio 4 13, Sala/estudio 12,
Dormitorio 3 12, Baño del dormitorio 2 8, Almacén 8, General 7, Aseo 7,
Escalera 6, Baño del dormitorio 1 6, Vestíbulo planta baja 6, Salón 6, Terraza
5, Dormitorio 2 5, Garaje 5, Cuarto de plancha 5, Office 3, Comedor 3, Pasillo
2, Baño del dormitorio 3 1 y Lavandería 1. Ningún nombre de proveedor en el
informe, el YAML de correcciones ni el de la plantilla (comprobado por
programa contra los 36 del JSON, sin imprimirlos).

**Fase RED** (desde `services/postventa-api`, con los tests nuevos y los YAML
todavía sin tocar):

`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion_contenido.py tests/test_f036_configuracion_plantilla.py -q --tb=line -p no:cacheprovider`

```text
E   AssertionError: 11
E   AssertionError: assert {9, 11, 12, 13, 14, 17, ...} == frozenset({46, 120, 121})
E   AssertionError: assert ['General (to... el detalle)'] == ['Baño del do...etalle)', ...]
E   KeyError: 'Baño del dormitorio 1'
E   ValueError: 'Baño del dormitorio 1' is not in list
FAILED tests/test_f036_migracion_contenido.py::test_f036_t25_las_ubicaciones_sin_equivalente_son_las_decididas
FAILED tests/test_f036_migracion_contenido.py::test_f036_t25_quedan_marcadas_solo_las_filas_sin_decidir
FAILED tests/test_f036_configuracion_plantilla.py::test_f036_t25_las_anadidas_son_exactamente_las_de_t6_y_t25
FAILED tests/test_f036_configuracion_plantilla.py::test_f036_t25_las_anadidas_en_t25_dicen_de_donde_vienen
FAILED tests/test_f036_configuracion_plantilla.py::test_f036_t25_orden_del_desplegable_general_alfabetico_y_otra
5 failed, 133 passed in 20.15s
```

(una primera tanda falló además en el test de la fila 81 por un error del
propio test, que buscaba «baños» en un texto plegado sin tildes; se corrigió
el test a «banos» antes de tocar los YAML). **Verde**: los dos ficheros, **138
passed**; `ruff check` y `ruff format --check` sin avisos.

**Mutación**: T25 no añade código de producción (dos YAML de datos y tests);
la campaña del arnés no tiene líneas en el alcance, como en T24.

**Evidencias**: `bash harness/init.sh` en verde: raíz 62 passed en 5,45 s;
servicio `api` **5935 passed, 67 skipped** en 844,59 s (la máquina iba
cargada: 235 s en T24); `front` verde (caché); `PUERTA COBERTURA: 99.9% de
2785 líneas cambiadas cubiertas (2783/2785, umbral 80%, nivel critico)`;
`ENTORNO LISTO`. Aviso de procedimiento: esta vez `init.sh` se lanzó con un
filtro de salida (`| grep -v` para quitar las líneas de progreso), no tal
cual; el resultado es el mismo, pero la regla pide el comando limpio.

## T26 · documentación · 2026-09-30 · hecho; T27–T29 son MANUALES del humano y T16 sigue PENDIENTE

> **Resumen para el líder.** T26 hecha: commit `0f07a46` (`F-036 T26: ...`) en
> esta rama y commit **local** `cd4a8e0` en `azure-apps` (rama `master`, sin
> push, solo `postventa_incidencias.md`; el `dedicacion.md` modificado que
> había allí **no es mío y no se ha tocado ni añadido**). La documentación
> describe **lo implementado** (bloques 0–8, con sus desviaciones), no el
> borrador de la spec. `bash harness/init.sh` en verde (abajo). T26 `[x]`.

### Qué cambió

| Fichero | Qué |
|---|---|
| `docs/INTEGRACION.md` | Cabecera (fecha 2026-09-30, última feature F-036, sin desplegar). **§1**: las filas de PostgreSQL y `sigrid-api` nombran F-036; párrafo «Lo nuevo de F-036» (vía de entrada, solo lectura en Sigrid, `openpyxl` y `defusedxml` en la compilación remota) y subsección «Con F-036 · el catálogo de una obra: dos lecturas de `sigrid-api`» (`dbo.upv`/`dbo.con`; `dbo.obrofc`/`dbo.auxofc`/`dbo.con`; techo de 1.000 → 409 `catalogo_sin_verificar`; cortada por debajo → 503 `CatalogoNoDisponible`; `ENTORNO` en `dev`/`pro`, sin `CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO`; qué no sale en logs; «no pide ningún cambio» al dueño de `sigrid-api`; lo que pedirán F-040 y F-039; lo que queda fuera: actividades F-039 y agrupación de proveedores F-050). **§2**: tres tablas en el árbol, recuadro fechado «ya no son diez, son trece» (cita literal la premisa; nada se borra) y subsección «Con F-036» con las tres tablas, la **costura del discriminador `catalogo`** (`oficio`/`proveedor`/`actividad_oficio`; F-036 solo escribe `oficio`; `proveedor_ambiguo` siempre falso), sin binarios, y volumen. **§4**: «Las de F-036: ninguna» (R49). **§6**: tres filas (techo de `sql/read`, pasarela caída, oficio renombrado o dado de baja en Sigrid). **§7**: la tercera superficie de datos personales (texto libre de la propiedad, `proveedor_nombre` de autónomos, `nombre_fichero`, `importado_por`, `decidido_por`; nada en logs; solo `GET /api/bandeja`). **§8**: cinco filas en la tabla de endpoints, párrafo de que no dependen de las ventanas, las dos páginas, «Los doce» → «Los diecisiete», y fila de F-036 en «Qué NO está desplegado» (no crea nada en Sigrid hasta F-040; la revisión es F-038). **§9**: seis filas |
| `docs/ARCHITECTURE.md` | Párrafo en «Qué hace este proyecto»; el árbol gana el `.xlsx` en `documentos/` y `scripts/`; sección nueva **«Entrada de incidencias (F-036)»** antes de «Acceso a datos»: la plantilla, la importación en sus seis pasos con el **Excel de errores**, la bandeja, la **agrupación de oficios** (propuesta, confirmación humana, append-only, la costura), dónde vive cada pieza, dependencias y **«Lo que no hacen»** (no escribe en Sigrid; F-040, F-038, F-037, F-039, F-050; no corrige Sigrid; no guarda ficheros). Las filas `sigrid-api` y PostgreSQL de la tabla de sistemas nombran F-036 |
| `services/postventa-api/tests/test_f036_documentacion.py` (nuevo) | 68 tests (R60, R61). Leen **el código** siempre que pueden: tablas de Sigrid del SQL de `consultas_catalogo.py`, tablas y `CHECK` de `catalogo` del DDL 12–14, rutas registradas en `function_app.py`, dependencias de `requirements.txt`. Más un control (con su negativo) de lo que retiró la quinta enmienda (`proveedor_fuera_de_obrofc`, `DENSE_RANK`, `/api/proveedores/`, `catalogos.html`…) y el barrido de valores de `test_f005` sobre la sección nueva de la arquitectura |
| `services/postventa-api/tests/test_f012_documentacion.py` | `NUMERALES` ampliado de 15 a 20 (la tabla de §8 pasa a 17 filas); la comprobación no cambia |
| `services/postventa-api/tests/test_f019_documentacion.py` | La cuenta fijada pasa de «Los doce» a «Los diecisiete», y «Los doce» entra en la lista de cifras viejas prohibidas. Nada se relaja |
| `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` | Cabecera con rama `feature/F-036-importar-excel` y commit de origen `0f07a46`, fecha 2026-09-30; recuadro nuevo «LO QUE CAMBIA EN ESTA REVISIÓN (2026-09-30, F-036)», y el de F-013 pasa a «LO QUE CAMBIÓ EN LA REVISIÓN DEL 2026-09-24»; los mismos bloques de F-036 que en `docs/INTEGRACION.md` (aplicados como parche: 12 de 13 trozos; la cabecera, a mano). **Commit local `cd4a8e0`** |
| `specs/F-036-importar-excel/tasks.md` | T26 `[x]` |

Sin código de producción, sin dependencias nuevas, sin red, Sigrid, base ni IA.
Ningún valor: ni host, ni GUID, ni IP, ni nombres de proveedor (lo barren
`test_f005_integracion_sin_secretos.py` y `test_f006_repo_sin_identificadores.py`;
sobre la copia de `azure-apps`, a mano con los mismos patrones: 0
coincidencias).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **T26-1 · La copia de `azure-apps` ya divergía de la fuente, y no se ha
   reconciliado.** Antes de tocarla, su cuerpo difería de `docs/INTEGRACION.md`
   en ~140 líneas en los dos sentidos: la copia tiene una subsección que la
   fuente no tiene («Cómo se configura el acceso a la pasarela (desde el
   2026-09-03)», con los nombres de los secretos del vault) y en la copia
   faltan los recuadros de la fuente del 2026-09-23 sobre las ventanas
   abiertas por defecto y F-034. Sobrescribir la copia con la fuente habría
   **perdido** esa subsección; se aplicaron solo los bloques de F-036 y la
   divergencia queda igual que estaba. **Para el humano**: decidir cuál manda
   en esas diferencias y reconciliarlas en un trabajo aparte.
2. **T26-2 · La cuenta de endpoints.** «Los doce quedan en nivel anónimo» pasa
   a «Los diecisiete» sin recuadro, como hicieron F-012 y F-026: es una cuenta,
   no una premisa derogada, y la vigilan `test_f012` (cuenta las filas) y
   `test_f019` (fija el literal). Se amplían los dos, no se relajan.
3. **T26-3 · «Las diez van en el orden…» de §2 sí lleva recuadro fechado**,
   porque es una afirmación sobre el inventario que deja de ser cierta; la
   frase original se conserva.
4. **T26-4 · La copia de `azure-apps` no se prueba en la suite** (otro
   repositorio; mismo criterio que `test_f028_documentacion.py`). Verificación
   a mano: `diff` de los cuerpos tras el parche → ninguna línea con «F-036»
   difiere entre fuente y copia. La única línea de F-036 distinta es la
   referencia a `sigrid_api.md` §8.9, que en la copia va sin el prefijo
   `azure-apps/` (es el mismo repositorio).
5. **T26-5 · §6 gana tres filas** aunque T26 nombra §1, §2, §7 y §8: sin ellas
   el documento no diría qué nos pasa si la pasarela cae o si Sigrid renombra
   un oficio, que es lo que busca quien administra la pasarela. Y §4 dice
   expresamente que no hay variables nuevas (R49).
6. **T26-6 · Lo que no se dice**: B4-1/B4-2 (las dos consultas aún no se han
   ejecutado contra Sigrid real; la primera prueba es T29) y el `COLLATE "C"`
   (B5-1) son detalle de la spec y del informe; los documentos del ecosistema
   describen el diseño vigente y dicen que F-036 está **sin desplegar**.
7. **T26-7 · Tiempos**: la comprobación de partida de `init.sh` tardó
   **2 h 15 min** (8.105 s la suite `api`, frente a 845 s en T25): la máquina
   iba muy cargada. De ahí la pausa larga en mitad del encargo.

### Nota para el líder: hallazgo para el dueño de `sigrid-api` (NO se ha tocado `azure-apps/sigrid_api.md`)

En T1 bis se vio que la pasarela responde `Content-Type: application/json`
**sin `charset`** (el worker de Python de Azure Functions solo añade `charset`
a los `text/*`) con el cuerpo en UTF-8 real (`ensure_ascii=False`), y
`Invoke-RestMethod` de **PowerShell 5.1**, sin `charset`, lo decodifica como
ISO-8859-1: las tildes salen dobladas (`í` → `Ã­`). Aquí se resolvió en
`infra/08_lectura_sigrid_comun.ps1` leyendo los bytes y decodificando UTF-8;
cualquier otro consumidor de la pasarela desde PowerShell 5.1 tendrá el mismo
problema. Propuesta para ellos: `mimetype="application/json; charset=utf-8"`
en su fábrica de respuestas, o dejarlo escrito en `sigrid_api.md`. Es suyo:
que el líder se lo haga llegar.

### Fase RED

Tests escritos, y `test_f012`/`test_f019` ajustados, **antes** de tocar los
dos documentos. Comando (desde `services/postventa-api`):

`.venv/Scripts/python.exe -m pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py tests/test_f012_documentacion.py tests/test_f019_documentacion.py -q --tb=no -rfE -p no:cacheprovider`

```text
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_cabecera_dice_que_f036_lo_toco_y_cuando
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_fila_de_sigrid_api_de_la_seccion_uno_nombra_f036
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_uno_nombra_cada_tabla_de_sigrid_que_se_lee[auxofc]
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_uno_describe_las_dos_lecturas_nuevas
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_dos_nombra_cada_tabla_nueva[importaciones]
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_dos_explica_la_costura_del_discriminador[proveedor]
FAILED tests/test_f036_documentacion.py::test_f036_r49_la_seccion_cuatro_dice_que_no_hay_variables_nuevas
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_siete_dice_los_datos_personales_nuevos
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_tabla_de_la_seccion_ocho_declara_cada_endpoint[POST-importaciones]
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_seccion_ocho_dice_que_f036_no_esta_desplegada
FAILED tests/test_f036_documentacion.py::test_f036_r60_integracion_dice_lo_que_queda_fuera
FAILED tests/test_f036_documentacion.py::test_f036_r61_la_fila_de_sigrid_api_nombra_las_lecturas_del_catalogo
FAILED tests/test_f036_documentacion.py::test_f036_r61_la_fila_de_postgresql_nombra_las_tablas_nuevas
FAILED tests/test_f019_documentacion.py::test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints
ERROR tests/test_f036_documentacion.py::test_f036_r61_la_arquitectura_tiene_la_seccion_de_la_entrada
ERROR tests/test_f036_documentacion.py::test_f036_r61_describe_la_via_de_entrada
ERROR tests/test_f036_documentacion.py::test_f036_r61_dice_lo_que_no_hacen
[… 26 FAILED y 7 ERROR más, del mismo tipo]
40 failed, 67 passed, 10 errors in 1.61s
```

(Los ERROR son del fixture `entrada`: la sección «Entrada de incidencias
(F-036)» no existía. `test_f019` falla porque el documento sigue diciendo «Los
doce».)

### Verde

El mismo comando más el resto de tests de documentación y de barrido
(`test_f005_integracion_sin_secretos`, `test_f006_repo_sin_identificadores` y
`test_f009`, `test_f013`, `test_f025`, `test_f026`, `test_f028`
`_documentacion`): **405 passed in 14.19s**. `ruff check` y `ruff format
--check` del test nuevo sin avisos (un orden de imports corregido con `--fix`).

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tal cual: raíz **62 passed** (4,77 s); servicio `api` **6003 passed, 67 skipped** (5935 + 68 del test nuevo); `front` en verde (caché, sin cambios en el front) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2785 líneas cambiadas cubiertas (2783/2785, umbral 80%, nivel critico)` — T26 no añade líneas de producción |
| Mutación | Sin líneas de producción `.py` en el alcance de T26 (dos documentos y tests): no aplica una campaña propia; la final es T30 |
| Tiempo de la suite | `api` **529,67 s** (0:08:49); `ENTORNO LISTO` |

### Qué queda fuera y qué falta

- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 · MANUALES del humano**: desplegar, confirmar los grupos de
  oficios de la 0677, ejecutar la migración a `v2` y la verificación
  desplegada. Tras desplegar, la fila de F-036 de «Qué NO está desplegado»
  (`docs/INTEGRACION.md` §8) y el «sin desplegar» de la cabecera y de §1 se
  enmiendan, **y se refresca la copia de `azure-apps`**.
- **T30**: `init.sh` final con la campaña de mutación.
- **Para el humano**: T26-1 (reconciliar la copia de `azure-apps` con la
  fuente) y la nota de `charset` para el dueño de `sigrid-api`.


## Bloque 10 (T31–T34) · 2026-09-30 · hecho; siguiente: review 2. T16 sigue siendo MANUAL del humano y está PENDIENTE

> **Resumen para el líder.** Los cuatro arreglos de la review 1 (cambios 1, 3,
> 5 y 6) hechos, cada uno en su commit: T31 `7b90fa9` (tope del lector, R115),
> T32 `d8fa8a4` (informe sin códigos de proveedor, R116, e informe
> regenerado), T33 `b3ff374` (lista de alcance cerrado) y T34 `1d44c34`
> (nombres `test_f036_rN_`), más `dee3824` (T31: los tests que matan los tres
> supervivientes de la campaña). Un commit fuera de las tareas, `629b29b`,
> **quita de `progress/review_F-036.md` el GUID de relleno de B3-12**, que
> dejaba en rojo `test_f006_r26` (ver B10-5). `bash harness/init.sh` en verde.
> T31–T34 `[x]`. Campaña de mutación única con `--base 444e0c4`: abajo.

### Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | **T31.** `_filas` recorre de `PRIMERA_FILA` a `ULTIMA_FILA + 1` (2–1002) con `max_row`; `_datos_fuera_del_tope` mira **solo las celdas que trae el fichero** (`ws._cells`) para ver si hay algún dato en las columnas de datos de la fila 1002 o más abajo; `_celdas_existentes` falla cerrado (`no_es_xlsx`) si `_cells` no está o no es un `dict`; `_cabecera` lee las 9 columnas de la cabecera por posición y, más a la derecha, solo las celdas existentes con valor, en orden de columna; `_metadatos` hasta `MAX_FILAS_METADATOS = 10` filas y 2 columnas. `LibroLeido` se construye con `datos_fuera_del_tope` |
| `services/postventa-api/domain/models/importacion.py` | **T31.** `LibroLeido.datos_fuera_del_tope: bool = False`; `reconocer_plantilla` lo convierte en `demasiadas_filas`, justo después de la comprobación del número de filas y antes de la obra (el orden de §4.2 no cambia) |
| `services/postventa-api/scripts/migracion_f036.py` | **T32.** Por fila, «Proveedor: proveedor completado (único de la obra para ese oficio)», **sin** el código; el recuento pasa de «Proveedores completados (R91)» a «Filas nuevas con proveedor, completado por R91 (el único de la obra para ese oficio)»; la nota de cabecera y los docstrings dicen «sin nombres ni códigos de proveedor (R58, R116)» |
| `progress/migracion_F-036.md` | **T32.** Regenerado con el comando de T24 (abajo) |
| `services/postventa-api/tests/test_f036_excel_lector.py` | **T31.** 25 tests `test_f036_r115_…` (contando los parametrizados); después de la campaña, 26 (la fila 1003) y dos reforzados (`dee3824`) |
| `services/postventa-api/tests/test_f036_importacion_dominio.py` | **T31.** 3 tests `test_f036_r115_…` del campo nuevo |
| `services/postventa-api/tests/test_f036_migracion.py`, `test_f036_migracion_contenido.py` | **T32.** `test_f036_r116_…` (3) y el de R58 exige también que no aparezca ningún código de proveedor; sale `test_f036_r58_el_informe_marca_los_proveedores_completados_con_su_codigo`, que exigía lo contrario |
| `services/postventa-api/tests/test_f036_alcance_cerrado.py` | **T33.** `NUEVOS_DE_F036` gana `scripts/migracion_f036.py` y `scripts/migrar_excel_f036.py`; `FRONT_DE_F036` nuevo con `importar.html`, `oficios.html`, `js/importacion.js` y `js/oficios.js`; el comentario dice qué controles aplican al front; test nuevo `test_f036_r46_los_bloques_7_y_8_tambien_estan_en_el_control` |
| `services/postventa-api/tests/test_f036_consultas_catalogo.py`, `test_f036_ddl.py` | **T34.** Renombrados a `test_f036_r13_sql_oficios_de_la_obra_caracter_a_caracter`, `test_f036_r44_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas` y `test_f036_r83_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas`; el cuerpo no cambia |
| `progress/review_F-036.md` | Una línea: el GUID de relleno de B3-12 pasa a «GUID omitido: R26 de F-006» (B10-5) |
| `specs/F-036-importar-excel/tasks.md` | T31–T34 `[x]` |

Sin dependencias nuevas, sin red, Sigrid, base ni IA. Sin cambios en `docs/`:
ni `ARCHITECTURE.md` ni `INTEGRACION.md` describían el recorrido del lector ni
el texto del informe.

### Decisiones y desviaciones (para el reviewer)

1. **B10-1 · `ws._cells` y no `read_only=True`** (las dos valen según §5.2).
   Con `_cells` el resto del lector (formato antiguo, metadatos, tipos de celda,
   fórmulas) no cambia, y no hay que tratar los huecos entre filas del modo
   `read_only`. Lo fija `test_f036_r115_el_diccionario_de_celdas_de_openpyxl_es_el_que_se_espera`
   (existe, es un `dict` con claves `(fila, columna)` coherentes con cada
   celda, trae la celda vacía con estilo de la fila 1.048.576 y **solo una
   celda más** que el mismo libro sin ella), y el fallo cerrado lo prueba
   `test_f036_r115_sin_el_diccionario_de_celdas_falla_cerrado`.
2. **B10-2 · El mensaje del caso nuevo.** R20 (sexta enmienda) dice «el error
   y su mensaje no cambian», pero el mensaje de hoy lleva la cuenta («trae N
   filas con datos y el máximo es 1000»), y con 5 filas y un dato en la 5000
   diría «trae 5 filas… y el máximo es 1000», que es falso para quien lo lee.
   Así que: con **más de 1000 filas** leídas, el mensaje de siempre, **igual**
   (lo fija `test_f036_r115_mas_de_1000_filas_y_datos_por_debajo_dice_cuantas`);
   con datos por debajo del tope y menos filas, el **mismo código** y la misma
   forma sin la cuenta: «El fichero trae datos por debajo de la fila 1001 y el
   máximo es 1000. Pártelo en varios ficheros.». Si el reviewer lo lee como
   desviación, cambiarlo es un literal.
3. **B10-3 · Qué es «un dato» por debajo del tope.** El mismo criterio que
   dentro de la plantilla (R23, `_con_dato`): una celda vacía o con solo
   espacios, aunque tenga estilo, no cuenta; una fórmula sí. Solo las columnas
   de datos (1–8): «Errores» (la 9, R66) y las de más a la derecha no cuentan.
   Lo fijan `test_f036_r115_texto_en_blanco_por_debajo_no_cuenta_como_dato`,
   `…_formula_por_debajo_cuenta_como_dato` y
   `…_por_debajo_solo_cuentan_las_columnas_de_datos` (1, 8, 9, 10 y 16.384).
4. **B10-4 · La cabecera se lee por posición en sus 9 columnas, no en 10.**
   §5.2 dice «de la columna 1 a `len(CABECERA) + 1`». Leer la 10.ª por
   posición metía un `""` al final de toda cabecera buena y rompía
   `test_f036_r17_libro_sin_metadatos_no_es_la_plantilla` (que espera la
   cabecera exacta). La 10.ª y todas las de más a la derecha se miran entre
   las celdas **existentes**: una con valor se añade (en orden de columna) y R19
   dice «sobra la columna «X»»; una con solo estilo no añade nada, como antes.
   El resultado es el de §5.2 (un valor más a la derecha es
   `cabecera_distinta`) y la salida de antes no cambia en ningún test previo
   (`test_f036_r19_cabecera_con_columna_de_mas…`, con `J1`, sigue igual).
   Mejora de paso: un valor en `XFD1` daba antes ~16.000 «sobra una columna
   sin nombre»; ahora, uno solo.
5. **B10-5 · El GUID de la review (fuera del encargo, para el líder).** La
   primera pasada de `init.sh` tras T34 salió en rojo en
   `test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador`:
   `{'progress/review_F-036.md': 1}`. La review 1 (`5fe4661`) cita
   literalmente el GUID de relleno de B3-12 en su línea 225; el `init.sh` de
   partida salió verde porque el servicio `api` venía de la caché. No es de
   este bloque, pero sin quitarlo no hay `init.sh` verde, y la tolerancia por
   ruta del test está para no usarse así. Se quitó **solo el valor** (commit
   `629b29b`); el sentido de la fila no cambia. El valor sigue en `5fe4661`,
   que con el `merge --squash` ya decidido no llega a `dev`.
6. **B10-6 · Metadatos: `MAX_FILAS_METADATOS = 10`.** «Un tope pequeño» (§5.2)
   con las claves en las filas 1–5: el doble. Un par clave/valor en la fila 11
   ya no se lee (`test_f036_r115_los_metadatos_se_leen_hasta_su_tope_de_filas`,
   con la frontera en 10 y 11).
7. **B10-7 · El recuento del informe cambia de rótulo** («Filas nuevas con
   proveedor, completado por R91 (el único de la obra para ese oficio)»),
   porque R116 pide «cuántas filas llevan proveedor y por qué regla». Por eso
   el `git diff` del informe tiene, además de las 46 líneas que pierden el
   código, esa fila y la nota de cabecera (abajo).
8. **B10-8 · T33 y el front.** Al front le aplican los controles de texto
   (R46: ninguna ruta de escritura de Sigrid; R48: ninguna ventana; R49: no lee
   el entorno), sobre el fichero **entero**, comentarios incluidos, que es más
   estricto que sin docstrings. **No** le aplica el de imports de R46 (mira
   módulos de Python) y el comentario lo dice. Los cuatro ficheros pasan sin
   tocarlos. Los dos scripts pasan también los tres controles y el de imports.

### Fase RED

**T31**, desde `services/postventa-api`, tests escritos antes que el código.

1. Primero con el lector y el dominio de antes:
   `.venv/Scripts/python.exe -m pytest tests/test_f036_excel_lector.py tests/test_f036_importacion_dominio.py -k r115 -p no:cacheprovider -q`
   → `27 failed, 1 passed, 242 deselected in 296.41s (0:04:56)` (el que pasa es
   la celda con estilo en `XFD1` de `_plantilla`: el lector de antes ya leía los
   metadatos acotados a dos columnas). Los dos centrales, uno a uno:

   ```text
   $ .venv/Scripts/python.exe -m pytest "tests/test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_en_la_ultima_fila_se_lee_en_menos_de_un_segundo" "tests/test_f036_excel_lector.py::test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias" "tests/test_f036_excel_lector.py::test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas" -p no:cacheprovider -q --tb=short
   FFF                                                                      [100%]
   _ test_f036_r115_celda_con_estilo_en_la_ultima_fila_se_lee_en_menos_de_un_segundo _
   tests\test_f036_excel_lector.py:820: in test_f036_r115_celda_con_estilo_en_la_ultima_fila_se_lee_en_menos_de_un_segundo
       assert segundos < TOPE_SEGUNDOS
   E   assert 35.57076979998965 < 1.0
   _______ test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias _______
   tests\test_f036_excel_lector.py:845: in test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias
       assert libro.datos_fuera_del_tope is True
   E   AttributeError: 'LibroLeido' object has no attribute 'datos_fuera_del_tope'
   __________ test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas ___________
   tests\test_f036_excel_lector.py:835: in test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas
       assert libro.datos_fuera_del_tope is True
   E   AttributeError: 'LibroLeido' object has no attribute 'datos_fuera_del_tope'
   3 failed in 38.68s
   ```

2. Para que el rojo de la fila 5000 no fuera solo «falta el campo», se hizo
   primero el dominio (campo y conversión en `reconocer_plantilla`; sus 3 tests
   en verde) y se repitió con **el lector de antes**:

   ```text
   $ .venv/Scripts/python.exe -m pytest "tests/test_f036_excel_lector.py::test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias" "tests/test_f036_excel_lector.py::test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas" -p no:cacheprovider -q --tb=short
   FF                                                                       [100%]
   tests\test_f036_excel_lector.py:845: in test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias
       assert libro.datos_fuera_del_tope is True
   E   AssertionError: assert False is True
   tests\test_f036_excel_lector.py:835: in test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas
       assert libro.datos_fuera_del_tope is True
   E   AssertionError: assert False is True
   2 failed in 3.57s
   ```

   Y lo que eso significa, con un guion del directorio temporal sobre el lector
   de antes (plantilla con `A2` y `A5000`): `filas leidas: [2, 5000]` y
   `reconocer_plantilla -> 0677 (sin demasiadas_filas)`: **el fichero entraba**.

**T32**, con el script de antes:

```text
$ .venv/Scripts/python.exe -m pytest "tests/test_f036_migracion.py::test_f036_r116_el_informe_no_contiene_ningun_codigo_de_proveedor" "tests/test_f036_migracion.py::test_f036_r116_el_informe_marca_los_proveedores_completados_sin_codigo" -p no:cacheprovider -q --tb=short
tests\test_f036_migracion.py:1338: in test_f036_r116_el_informe_no_contiene_ningun_codigo_de_proveedor
E   AssertionError: assert 'P001' not in '<!-- progre... | — | — |\n'
E     'P001' is contained here:
E       , código `P001` · Urgencia: — | ubicación normalizada | proveedor |
tests\test_f036_migracion.py:1343: in test_f036_r116_el_informe_marca_los_proveedores_completados_sin_codigo
E   AssertionError: assert 0 == 2
2 failed in 1.85s
```

(En la pasada de `-k "r58 or r116"`: `5 failed, 8 passed`, con el de R58
ampliado, el de recuentos y el del contenido real —`'`P0021`' is contained
here`, código inventado del catálogo falso— también en rojo.)

**T33**: `pytest tests/test_f036_alcance_cerrado.py -k bloques_7_y_8` →
`E   AssertionError: assert 'scripts/migracion_f036.py' in ('domain/models/plantilla_incidencias.py', …)`,
`1 failed, 25 deselected in 0.91s`.

**T34** (un renombrado): antes,
`pytest tests/test_f036_consultas_catalogo.py tests/test_f036_ddl.py --collect-only -q -k "test_f036_r13_ or test_f036_r44_ or test_f036_r83_"`
→ `no tests collected (96 deselected)`; después, `3 passed, 93 deselected`, y
los dos ficheros enteros `96 passed`.

### Verde y medición de R115 (tiempo y memoria)

`pytest tests/test_f036_excel_lector.py tests/test_f036_importacion_dominio.py`
→ **270 passed in 64.22s**; `test_f036_importar_http.py`,
`test_f036_pipeline_importacion.py` y `test_f036_arquitectura.py` →
**154 passed**; migración → **205 passed**; alcance cerrado → **26 passed**.

Medición aparte (guion del directorio temporal: la plantilla generada, con una
celda vacía en negrita en `A1048576` de «Incidencias», 33.162 bytes; tiempo con
`perf_counter` y pico con `tracemalloc` en otra lectura):

| Lector | Libro | Tiempo | Pico de memoria (`tracemalloc`) |
|---|---|---:|---:|
| antes | plantilla vacía (33.137 bytes) | 0,137 s | 3,12 MB |
| antes | celda con estilo en la fila 50.000 | 1,41 s | 86,2 MB |
| **antes** | **celda con estilo en la fila 1.048.576** | **36,43 s** | **1.633,6 MB** |
| después | plantilla vacía | 0,132 s | 3,13 MB |
| **después** | **celda con estilo en la fila 1.048.576** | **0,105 s** | **3,12 MB** |

Los topes de los tests: **1 s** y **32 MiB** de pico, lo que da ~10 veces de
margen sobre la lectura normal, también bajo la cobertura de `init.sh`. (La
review midió ~51 s y ~1,9 GB con la misma fila; la diferencia es la máquina.)

### Regenerar el informe (T32)

Desde `services/postventa-api`, con el comando de T24 y la salida del v2 en el
directorio temporal (con `--solo-informe` no se escribe):

`.venv/Scripts/python.exe scripts/migrar_excel_f036.py --original "C:\Users\pgris\OneDrive - Ruesma\Documentos\postventa\creacion_incidencias.xlsx" --catalogo "C:\Users\pgris\AppData\Local\Temp\catalogo_0677.json" --correcciones scripts/migracion_f036_correcciones.yaml --salida "<scratchpad>\creacion_incidencias_v2_T32.xlsx" --informe ../../progress/migracion_F-036.md --solo-informe`

```text
Migración F-036 · obra 0677 · sin --grupos: cada código es su propio grupo
Filas del original: 144 · filas nuevas: 158 · separadas: 14 · descartadas: 0
Ida y vuelta por el importador: 0 errores
v2: no se escribe (--solo-informe)
sha256 del original antes:   4f5f1f9db402fae2…
sha256 del original después: 4f5f1f9db402fae2…   (los 64 caracteres, iguales)
```

Comprobación del `git diff progress/migracion_F-036.md` (**48 −, 48 +**):
antes de regenerar se guardaron en el directorio temporal los 5 códigos de
proveedor distintos que traía el informe (no se copian aquí). Después: **0
apariciones** de cualquiera de ellos. Con un guion, a cada línea quitada se
le borra `, código `…`` tras el proveedor y se compara con la añadida: **46 de
48 iguales**; las otras dos son la nota de cabecera («Sin nombres ni códigos
de proveedor (R58, R116)…») y la fila de recuento (B10-7), que sigue diciendo
**46**. Recuentos intactos: 144 → 158, 14 separadas, 0 descartadas, 0
errores. Los 114 «código `…`» que quedan son de **oficio**.

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tal cual, tras el último commit de código (`dee3824`): raíz **62 passed** (8,66 s); servicio `api` **6035 passed, 67 skipped**; `front` en verde (caché, el front no cambió). La pasada anterior, tras T34 y el GUID: 6034 passed, 67 skipped |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2807 líneas cambiadas cubiertas (2805/2807, umbral 80%, nivel critico)` |
| Mutación | `python -m harness.mutacion --feature F-036 --base 444e0c4 --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque10.md`, con `timeout 5400` y sin nada en segundo plano al acabar (worktrees borrados): **94 líneas en alcance** (`importacion.py` 14, `excel_openpyxl.py` 67, `migracion_f036.py` 13), **26 mutantes, 23 muertos, 3 supervivientes**, 0 timeouts (1 repasado en serie), **1.558,5 s**. Los 3 eran huecos de los tests (tope de metadatos leído de la propia constante, ningún valor justo en la fila 1003, el campo sin hoja «Incidencias»): tests reforzados y cada mutante aplicado a mano → **3 de 3 muertos**. Resultado: **26/26 muertos, 0 equivalentes**. Análisis en `progress/mutacion_F-036_bloque10.md` |
| Tiempo de la suite | `api` **3.950,99 s** (1:05:50) en la última pasada, con la máquina compartida con las suites de `albaranes` y `facturas` corriendo a la vez; la anterior, **532,15 s** (0:08:52). `ENTORNO LISTO` en las dos |
| R115 | 36,43 s y 1.633,6 MB → 0,105 s y 3,12 MB (tabla de arriba) |

### Qué queda fuera y qué falta

- **Siguiente: review 2**, que repite sobre este código las mutaciones de
  orden del punto 7.
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 (MANUALES) y T30**: sin tocar. T29 paso 9 es la prueba desplegada
  de R115.
- **Para el líder**: B10-5 (el GUID de la review, quitado en `629b29b`) y
  B10-2 (el mensaje del caso nuevo de `demasiadas_filas`).
- Fuera de alcance, dicho: `scripts/migracion_f036.py` sigue leyendo el
  original con `iter_rows` sin `max_row`; es un script local sobre un fichero
  conocido, no una subida, y R115 no lo cubre.

## T35–T36 (solo lectura) · 2026-09-30 · hecho; siguiente: review 3. T16 sigue siendo MANUAL del humano y está PENDIENTE

> **Resumen para el líder.** El cambio R2-1 de la review 2, tal como lo decide
> la sexta enmienda bis (`design.md` §5.2, «Al cargar»): el lector abre el libro
> con `load_workbook(..., read_only=True, data_only=False)` y lo **cierra
> siempre** (`finally`), también cuando la lectura falla a medias. `ws._cells`
> sale del lector. Los tres ficheros de la review 2 —combinado `A1003:A1048576`,
> combinado `A1003:H1048576` e hipervínculo sobre `A1003:H1048576`— pasan de
> 9,7 s y 420 MB (el primero; los otros dos, cortados a los 60 s) a **~0,1 s y
> 47 MB de pico de proceso, sin crecer al leer**, en «Incidencias»,
> `_plantilla`, `Instrucciones` y en un Excel de errores. T35 `84ee911`, T36
> `5600388`. Mutación con `--base 52f8149`: **30 mutantes, 30 muertos**. Las tres
> mutaciones de orden de la lectura y el cierre, hechas a mano: las tres caen.
> El informe de migración **no cambia** (regenerado aparte: idéntico). T35 y T36
> `[x]`. `bash harness/init.sh` en verde y la suite del `api` entera, aparte, en
> verde (abajo).

### Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | **T35.** `_abrir`: `read_only=True, data_only=False`. `leer`: abre, llama a `_extraer` (los pasos 4 y 5, que eran el cuerpo de `leer`) y cierra en un `finally`; lo que falle al recorrer una hoja y no sea ya un `FicheroNoEsPlantilla` es `no_es_xlsx`; los avisos de `openpyxl` se ignoran durante la carga **y** la lectura (antes solo en la carga, que era donde se leía todo). `_parece_formato_antiguo`: **una** pasada `iter_rows(min_row=1, max_row=10, max_col=9, values_only=True)`, sin `ws.cell` ni `ws["A1"]`. `_filas_presentes` (nuevo): el analizador de filas de la hoja de solo lectura (`WorkSheetParser` sobre `ws._get_source()`, con los mismos parámetros que `ReadOnlyWorksheet._cells_by_row`), que da solo las filas que el XML trae; si falta la clase o un atributo, `no_es_xlsx`. `_datos_fuera_del_tope` y `_cabecera` lo usan en vez de `_celdas_existentes`, que desaparece. `_celda_leida` recibe valor y tipo en vez de la celda (la usan una `ReadOnlyCell` y una celda del analizador). `_filas` y `_metadatos` no cambian de recorrido |
| `services/postventa-api/tests/test_f036_excel_lector.py` | **T35.** Salen los dos tests que fijaban `ws._cells`; entran 11 funciones `test_f036_r115_…` (57 casos con los parametrizados), abajo |
| `specs/F-036-importar-excel/tasks.md` | T35 y T36 `[x]` |
| `progress/mutacion_F-036_bloque10bis.md` | **T36.** Informe de la campaña |

Sin dependencias nuevas, sin red, Sigrid, base ni IA. Sin cambios en `docs/` ni
en `azure-apps/`: no cambia nada de lo que el servicio expone o consume.

Tests nuevos (`tests/test_f036_excel_lector.py`):

- `test_f036_r115_rango_que_openpyxl_expande_al_cargar_se_lee_en_menos_de_un_segundo`
  (9: los tres ficheros de la review × «Incidencias», `_plantilla` e
  `Instrucciones`): < 1 s, la misma lectura que sin el rango y la plantilla
  reconocida;
- `…_rango_que_openpyxl_expande_al_cargar_con_la_memoria_acotada` (9): pico de
  `tracemalloc` < 32 MiB, el tope que ya usaban los tests;
- `test_f036_r115_r66_el_excel_de_errores_con_un_rango_lejano_sale_barato` (3):
  < 1 s, < 32 MiB, la misma lectura y la fila 2;
- `…_un_combinado_pequeno_en_una_fila_con_datos_se_admite`: `C2:D2` combinado
  en una fila con datos → la fila entra con la descripción corta, sin detalle,
  y valida sin errores;
- `…_el_libro_se_abre_en_solo_lectura_y_se_cierra` (4: plantilla, Excel de
  errores, formato antiguo y libro sin «Incidencias»): un doble de
  `load_workbook` registra `{"read_only": True, "data_only": False}` y **un**
  `close`;
- `…_el_libro_se_cierra_aunque_la_lectura_falle_a_medias` (10: cada uno de los
  cinco pasos de lectura, fallando con una excepción cualquiera → `no_es_xlsx`
  o con un rechazo → el mismo código): el `close` se llama igual;
- `…_un_xml_roto_que_solo_se_ve_al_recorrer_la_hoja_es_no_es_xlsx`: en solo
  lectura el XML de las filas se lee al recorrerlas, no al abrir; un `<v>` que
  no es un número acaba en `no_es_xlsx`, no en un 500;
- `…_el_analizador_de_filas_de_openpyxl_es_el_que_se_espera`: sustituye al de
  `ws._cells`. Fija que `_filas_presentes` da exactamente los números de fila
  que trae el XML (contados con una expresión regular sobre la parte), sin los
  huecos, y cada celda con `column`, `value` ya convertido (texto, fórmula como
  `"=1+1"` con tipo `f`, fecha como `datetime` con tipo `d`) y `data_type`, y la
  celda vacía con estilo de la fila 1.048.576 con valor `None`;
- `…_sin_el_analizador_de_filas_falla_cerrado`: hoja sin los atributos
  privados, o sin la clase del analizador → `no_es_xlsx`;
- `…_valores_lejanos_en_la_cabecera_por_columna_aunque_el_xml_no_vaya_en_orden`:
  con las celdas de la fila 1 fuera de orden en el XML, la cabecera sale en
  orden de columna (ni de XML ni alfabético);
- `…_los_ficheros_de_la_review_2_llevan_su_rango`: comprueba que los ficheros
  de las pruebas son lo que dicen (el analizador de `openpyxl` ve el combinado o
  el hipervínculo en la hoja que toca).

Los ficheros de la review se construyen **en memoria**: la plantilla generada
y, en la parte XML de la hoja, un `<mergeCells>` o un `<hyperlinks>` insertado
antes de `<dataValidations>`/`<pageMargins>` (con `openpyxl`, `merge_cells`
crearía al construirlos las mismas celdas que se quieren evitar al leerlos).
33.395–34.780 bytes, como los de la review.

### Decisiones y desviaciones (para el reviewer)

1. **T35-1 · La vía para lo que hay por debajo del tope: el analizador de
   filas, no `defusedxml` a mano** (las dos valen según §5.2). Da las celdas
   con el valor ya convertido como lo convierte `iter_rows` (cadenas
   compartidas, fórmulas, fechas), así que el criterio de B10-3 («   » no es un
   dato, una fórmula sí) sigue igual sin reimplementar la lectura del XML; con
   la pasada a mano por nombre local, una cadena compartida en blanco contaría
   como dato. Coste: más API privada que `ws._cells` (`WorkSheetParser`,
   `ws._get_source`, `ws._shared_strings`, `libro._date_formats`,
   `libro._timedelta_formats`); la fija el test del analizador y falla cerrado.
   La importación de `WorkSheetParser` va en un `try` a nivel de módulo: si
   una versión de `openpyxl` la quita, el servicio arranca y el lector rechaza
   con `no_es_xlsx`, en vez de romper la importación del módulo.
2. **T35-2 · `_parece_formato_antiguo` mira `A1:I10`, no `A1:E10`.** T35 y §5.2
   dicen «una pasada `A1:E10`» (`max_col=5`), pero R17 y §5.2 paso 4 piden «fila
   1 sin la cabecera de R2», que tiene 9 columnas, y el test
   `test_f036_r17_lo_que_no_tiene_la_forma_antigua_no_es_la_plantilla[cabecera-en-I1]`
   (anterior a este encargo, y el encargo exige que sigan verdes los del formato
   antiguo) pone `Errores` en `I1`. Con `max_col=5` ese test pasa a rojo y un
   Excel con la cabecera solo en `I1` se tomaría por formato antiguo. Se hace
   una sola pasada, acotada a 10 × 9 celdas fijas: el espíritu de la tarea (una
   pasada, celdas fijas, sin `ws.cell`) se mantiene. Si el reviewer lo quiere en
   5 columnas, hay que cambiar antes ese test y R17.
3. **T35-3 · La cabecera en una pasada, toda con el analizador.** No usa
   `iter_rows` sin `max_col`: en solo lectura el ancho saldría del `<dimension>`
   que declara el fichero, y un `<dimension>` falso (más estrecho que la fila)
   escondería una columna de más. El analizador lee la primera fila del XML; si
   es la 1, sus celdas con valor van a su columna (1–9) o, más allá, a la lista
   de sobrantes, que se ordena por columna. Si el XML no trae fila 1, la
   cabecera sale vacía (`cabecera_distinta`), como antes.
4. **T35-4 · Qué fila cuenta, por debajo del tope: la del elemento `<row>`.**
   `_datos_fuera_del_tope` usa el número de la fila del XML, no la coordenada de
   cada celda, que es lo mismo que usa `iter_rows` en solo lectura para
   `_filas`: una celda con una coordenada que no casa con su fila (fichero
   manipulado) se ve igual en los dos recorridos.
5. **T35-5 · Un fallo al recorrer es `no_es_xlsx`.** En solo lectura el XML de
   las filas se lee al recorrer, fuera de `_abrir`; sin convertirlo, un valor
   ilegible sería un 500. Se captura en `leer` todo lo que no sea ya un
   `FicheroNoEsPlantilla`, que es lo que §5.2 paso 3 decía de la carga
   («cualquier excepción de lectura, `no_es_xlsx`»). Contrapartida, dicha: un
   error de programación dentro de los pasos de lectura también se vería como
   `no_es_xlsx`; los tests del lector lo detectarían por el código.
6. **T35-6 · Lo que cambia de comportamiento, dicho.** (a) Un XML roto en una
   hoja que el lector **no** recorre (`_catalogos`, una hoja ajena) ya no hace
   fallar la lectura: en solo lectura esa hoja solo se abre para su
   `<dimension>`. Es lo que §5.2 dice («una hoja que no es de la plantilla no se
   recorre nunca»). (b) Un fichero **manipulado** con valores en las celdas
   escondidas de un combinado (Excel las vacía al combinar) se lee con esos
   valores: en solo lectura el combinado no existe. §5.2 lo acepta («el valor
   que cuenta es el que Excel enseña» para lo que Excel escribe); el importador
   valida esas celdas como cualquier otra. (c) Los comentarios de celda ya no se
   leen al cargar (en modo normal `openpyxl` los enlazaba); el lector nunca los
   usó.
7. **T35-7 · El informe de migración no se regenera en el repositorio.** El
   script lee el original con su propia `load_workbook` (ya en solo lectura);
   el lector solo interviene en la ida y vuelta del `v2`. Regenerado con el
   comando de T24 al directorio temporal (`--salida` e `--informe` allí,
   `--solo-informe`): 144 → 158, 14 separadas, 0 descartadas, **0 errores**, el
   mismo `sha256` del original antes y después, y el informe **idéntico** al
   versionado salvo la línea 1 (el comentario con su propio nombre de fichero).
   Así que `progress/migracion_F-036.md` no se toca y sigue sin códigos de
   proveedor.

### Fase RED

Tests escritos antes que el código, contra el lector de `52f8149` (el código de
producción de `80d60ce` es el mismo: los commits de después solo tocan
`specs/` y `progress/`). Desde `services/postventa-api`.

1. Los rápidos:

   ```text
   $ .venv/Scripts/python.exe -m pytest tests/test_f036_excel_lector.py -k "r115 and not expande_al_cargar and not con_un_rango_lejano" -p no:cacheprovider -q --tb=line
   …tests\test_f036_excel_lector.py:1246: AssertionError: assert [{'data_only': False}] == [{'read_only'...only': False}]
   E   AttributeError: module 'infrastructure.documentos.excel_openpyxl' has no attribute '_filas_presentes'
   …
   FAILED …::test_f036_r115_el_libro_se_abre_en_solo_lectura_y_se_cierra[plantilla]
   FAILED …::test_f036_r115_el_libro_se_abre_en_solo_lectura_y_se_cierra[excel-de-errores]
   FAILED …::test_f036_r115_el_libro_se_abre_en_solo_lectura_y_se_cierra[formato-antiguo]
   FAILED …::test_f036_r115_el_libro_se_abre_en_solo_lectura_y_se_cierra[sin-incidencias]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[excepcion-cualquiera-_metadatos]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[excepcion-cualquiera-_parece_formato_antiguo]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[excepcion-cualquiera-_datos_fuera_del_tope]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[excepcion-cualquiera-_cabecera]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[excepcion-cualquiera-_filas]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[rechazo-_metadatos]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[rechazo-_parece_formato_antiguo]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[rechazo-_datos_fuera_del_tope]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[rechazo-_cabecera]
   FAILED …::test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias[rechazo-_filas]
   FAILED …::test_f036_r115_el_analizador_de_filas_de_openpyxl_es_el_que_se_espera
   FAILED …::test_f036_r115_sin_el_analizador_de_filas_falla_cerrado
   16 failed, 29 passed, 95 deselected, 4 warnings in 11.70s
   ```

   (Los 29 que pasan son los de T31, el del combinado pequeño —que en modo
   normal también vacía `D2`—, el del XML roto —que en modo normal falla al
   cargar— y el que comprueba los ficheros de prueba. Los 4 avisos eran de un
   ZIP con la parte cambiada duplicada; el ayudante `_reemplazar` se añadió
   después para no duplicarla.)

2. **Los ficheros de la review (centrales)**, cada test en su subproceso con un
   tope de tiempo (guion del directorio temporal que lanza
   `python -m pytest <nodo>` con `subprocess.run(timeout=…)`):

   ```text
   --- …::test_f036_r115_rango_que_openpyxl_expande_al_cargar_se_lee_en_menos_de_un_segundo[combinado-A-Incidencias]
       20.4 s, rc=1
       E   assert 17.11851070006378 < 1.0
       1 failed in 18.45s
   --- …[combinado-A-H-Incidencias]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[hipervinculo-A-H-Incidencias]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[combinado-A-_plantilla]
       19.5 s, rc=1
       E   assert 16.66255489992909 < 1.0
       1 failed in 17.69s
   --- …[combinado-A-H-_plantilla]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[hipervinculo-A-H-_plantilla]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[combinado-A-Instrucciones]
       16.5 s, rc=1
       E   assert 13.608366100001149 < 1.0
       1 failed in 14.62s
   --- …[combinado-A-H-Instrucciones]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[hipervinculo-A-H-Instrucciones]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …::test_f036_r115_r66_el_excel_de_errores_con_un_rango_lejano_sale_barato[combinado-A]
       18.9 s, rc=1
       E   assert 15.66418030008208 < 1.0
       1 failed in 16.67s
   --- …[combinado-A-H]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[hipervinculo-A-H]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …::test_f036_r115_rango_que_openpyxl_expande_al_cargar_con_la_memoria_acotada[combinado-A-Incidencias]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[combinado-A-H-Incidencias]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   --- …[hipervinculo-A-H-Incidencias]
       CORTADO: sigue leyendo a los 20 s (tope del subproceso)
   ```

   Los 15 en rojo: los cuatro del rango de una columna fallan por tiempo (13,6–
   17,1 s frente al tope de 1 s) y los once con el rango de ocho columnas o el
   hipervínculo siguen dentro de `load_workbook` a los 20 s. Tras los cortes no
   quedó ningún proceso de Python de este repositorio vivo (comprobado con
   `Get-CimInstance Win32_Process`).

### Verde, y las mediciones de antes y después

`pytest tests/test_f036_excel_lector.py tests/test_f036_importacion_dominio.py`
→ **310 passed in 38.02s**. Todos los de F-036 (`pytest tests -k f036`, que
incluye la ida y vuelta generador → lector → importador, el Excel de errores,
el formato antiguo, la migración, el borde HTTP y la arquitectura) →
**1696 passed in 115.33s**.

Medición aparte (guiones del directorio temporal; cada fichero, la plantilla
generada con las filas `BUENA` y `MALA`, o el Excel de errores, más el rango):

| Fichero | Bytes | Lector de `52f8149` | Lector nuevo |
|---|---:|---|---|
| Combinado `A1003:A1048576` en «Incidencias» | 33.395 | **9,67 s · 420 MB** de pico de proceso (47 MB antes de leer); en el test, 17,1 s | **0,11 s · 47 MB** (no crece); `tracemalloc` 0,90 MB |
| Combinado `A1003:H1048576` en «Incidencias» | 33.395 | **cortado a los 60 s** (la review: 169 s y 2,6 GB) | **0,08 s · 47 MB**; `tracemalloc` 0,86 MB |
| Hipervínculo sobre `A1003:H1048576` en «Incidencias» | 33.435 | **cortado a los 60 s** (la review: 228 s y 4,1 GB) | **0,08 s · 47 MB**; `tracemalloc` 0,80 MB |
| Los tres, en `_plantilla` | 33.390–33.424 | 16,7 s el de una columna; los otros dos, cortados a los 20 s | 0,21–0,22 s; `tracemalloc` 0,90–1,21 MB |
| Los tres, en `Instrucciones` | 33.393–33.425 | 13,6 s el de una columna; los otros dos, cortados a los 20 s | 0,22 s; `tracemalloc` 0,80–0,93 MB |
| Los tres, en un Excel de errores con una fila con error | 34.743–34.780 | 15,7 s el de una columna; los otros dos, cortados a los 20 s | 0,19–0,23 s, la fila 2; `tracemalloc` 0,81–0,96 MB |
| Celda con estilo en `A1048576` (la de la review 1) | 33.162 | (Bloque 10: 0,105 s) | 0,22 s; `tracemalloc` 0,92 MB |
| La plantilla con 2 filas, sin nada más | 33.359 | 0,052 s | 0,088 s |

Las tres primeras filas son de un proceso por lectura (pico de *working set*
con `K32GetProcessMemoryInfo`, como la review); las demás, en un mismo proceso
(el mejor de tres, con otra suite de la máquina corriendo a la vez, por eso
~0,2 s). La lectura normal cuesta algo más que antes (0,05 → 0,09 s): en solo
lectura «Incidencias» se analiza dos veces enteras (filas 2–1002 y la pasada de
lo que hay por debajo) en vez de enlazarse una. Queda por debajo del tope de
1 s de los tests con un margen de ~10 veces.

### Mutación (T36)

`python -m harness.mutacion --feature F-036 --base 52f8149 --workers 6 --timeout 600 --salida progress/mutacion_F-036_bloque10bis.md`,
desde la raíz, con `timeout 5400` y nada en segundo plano al acabar (los
worktrees de la campaña, borrados; el `worktree-agent-a6e2f9bed1d46cdbc` que
lista `git worktree list` no es de este encargo y no se ha tocado):

- **144 líneas en alcance**, todas de `excel_openpyxl.py`;
- **30 mutantes, 30 muertos, 0 supervivientes, 0 timeouts**, 958,4 s.

Entre ellos, los que importan para R2-1: `read_only=True → False` (muerto: en
modo normal la hoja no tiene `_get_source` y todo acaba en `no_es_xlsx`, y el
doble lo ve), `data_only=False → True` (muerto: las fórmulas llegarían sin
texto), el tope `fila <= ULTIMA_FILA → <`, la columna `<= len(COLUMNAS_DE_DATOS) → <`,
`numero == 1`, `columna <= ancho`, `columna - 1`, la clave de orden de la
cabecera (`par[0] → par[1]`, lo mata el test nuevo del XML desordenado) y los
trece de `_parece_formato_antiguo`.

**Mutaciones de orden, a mano** (las que T36 anuncia para la review 3, hechas
ya para que la review las tenga de partida; guion del directorio temporal que
aplica cada una sobre `leer`, pasa `tests/test_f036_excel_lector.py` y
restaura el fichero):

| Mutación | Resultado |
|---|---|
| O1 · `libro.close()` justo después de abrir, antes de extraer | **113 failed**, 26 passed |
| O2 · `close` solo si la lectura va bien (sin `finally`) | **10 failed** (los de «falla a medias») |
| O3 · sin convertir en `no_es_xlsx` lo que falla al recorrer | **6 failed** (los de «excepción cualquiera» y el del XML roto) |

Que ningún camino abra en modo normal: lo cubren el mutante `read_only → False`
y el doble de `load_workbook`, que exige `read_only=True` en la única apertura
de los cuatro tipos de fichero y en los diez fallos a medias. Que no se recorra
una hoja antes de abrirla en solo lectura: no hay hoja que recorrer antes de
`_abrir`, que es lo primero después del examen del ZIP (sin puerta nueva que
ordenar, como dice T36).

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tras el último commit de código y de la campaña (`5600388`): raíz **62 passed** (8,91 s); servicio `api` **6074 passed, 67 skipped**, ejecutado de verdad (el árbol del servicio cambió: sin caché); `front` en verde (caché, el front no cambió). `ENTORNO LISTO`. La suite del `api` entera, aparte y después del commit de este informe (`fc7e670`, que es el que añade líneas a `progress/` y la caché de `init.sh` no ve): `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api` → **6074 passed, 67 skipped in 289.54s**; solo `tests/` → 6074 passed, 42 skipped in 278.41s (los 25 de diferencia son `tests_bbdd/`, que sin Docker se saltan) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2839 líneas cambiadas cubiertas (2837/2839, umbral 80%, nivel critico)` |
| Mutación | `--base 52f8149`: 144 líneas, **30 mutantes, 30 muertos, 0 supervivientes**, 0 timeouts, 958,4 s (`progress/mutacion_F-036_bloque10bis.md`). Orden a mano: 3 de 3 caen |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **717,99 s** (0:11:57), con la suite de `albaranes` corriendo a la vez en la máquina; la del lector y el dominio, 38,02 s; todas las de F-036, 115,33 s |
| R115 al cargar | 9,67 s y 420 MB (y dos ficheros cortados a los 60 s) → 0,08–0,11 s y 47 MB sin crecer (tabla de arriba) |

### Qué queda fuera y qué falta

- **Siguiente: review 3**, con las mutaciones de orden de T36 (hechas ya a
  mano, arriba) y la aceptación de T35-2 (`A1:I10` en vez de `A1:E10`).
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **R2-2** (aceptación escrita del humano de O4 y M1a) sigue siendo del líder
  con el humano; este encargo no la toca.
- **T27–T29 (MANUALES) y T30**: sin tocar. El paso 9 de T29 es la prueba
  desplegada de esto: una copia del `v2` con `A1003:A1048576` combinadas debe
  responder al momento y leerse normal.
- Fuera de alcance, dicho: `scripts/migracion_f036.py` lee el original con su
  propia `load_workbook(read_only=True, data_only=True)` y `iter_rows` sin
  `max_row`; es un script local sobre un fichero conocido, no una subida.

## T37–T38 (presupuesto de elementos XML) · 2026-10-01 · hecho; siguiente: review 4, con el hallazgo T37-1 para el humano antes. T16 sigue siendo MANUAL del humano y está PENDIENTE

> **Resumen para el líder.** El cambio R3-1 de la review 3, tal como lo decide
> la séptima enmienda (R117; `design.md` §5.2, «El presupuesto de elementos
> XML»). Entre `_inspeccionar_zip` y `_abrir`, **antes de `load_workbook`**, el
> lector cuenta en *streaming* (trozos de 64 KiB), con el *expat* de
> `defusedxml` sin DTD ni entidades y sin construir árbol, los elementos de
> apertura de todas las partes `.xml` y `.rels`, en un total global, y corta al
> pasar de **200.000**: `fichero_sospechoso`; una parte que no se analiza,
> `no_es_xlsx`; en los dos casos sin abrir el libro. Los siete ficheros de la
> review 3 pasan de **15–25 s o cortados a los 30 s** a **0,14–0,32 s**, con un
> pico de `tracemalloc` de **0,58–0,79 MB** y sin crecer la memoria del proceso.
> La plantilla completa (1000 filas, detalle de 2000) tiene **26.886**
> elementos, por debajo de un quinto (40.000). Script
> `scripts/contar_elementos_xml_f036.py` para T29. T37 `6039f0c`, T38 `a370b1d`:
> mutación con `--base becb693`, **22 mutantes, 18 muertos + 4 cerrados con 2
> tests nuevos, 0 equivalentes**; las mutaciones de orden de la puerta, hechas a
> mano: 4 de 4 caen. El informe de migración **no cambia** (regenerado
> aparte: idéntico, 144 → 158, 0 errores). `bash harness/init.sh` en verde y la
> suite del `api` entera, aparte, en verde (abajo).
>
> **Hallazgo T37-1, para el humano antes de la review 4 (no implementado: es
> decisión de spec).** R117 cuenta «las partes `.xml` y `.rels`» porque §5.2 da
> por hecho que son las que `openpyxl` puede analizar. **No es así**: `openpyxl`
> localiza las hojas por el `Target` de las relaciones, y las cadenas
> compartidas y el libro por `[Content_Types].xml`, sin mirar la extensión.
> Medido: la plantilla con «Incidencias» renombrada a `xl/worksheets/sheet1.dat`
> (relaciones y tipos de contenido retocados) y 1,6 millones de `<brk/>`, 74 KB:
> el lector nuevo la **admite** y tarda **48,4 s con un pico de 911 MB** (proceso
> aparte; 112 MB antes de leer). Es la misma clase de R3-1 por otra puerta.
> Opciones, con su coste medido: (a) contar **todas** las partes del ZIP, con
> las que no son `.xml`/`.rels` contadas mientras se analicen y sin rechazar si
> no son XML (una imagen falla en el primer byte y cuenta 0); coste: el Excel de
> errores más grande (1000 filas con error en las 8 columnas) pasa de 52.910 a
> **148.916** elementos, porque el dibujo VML de los comentarios, que hoy no se
> cuenta, suma 96.006 (el 74 % del presupuesto, aunque cabe); (b) aceptar el
> riesgo por escrito; (c) otra regla que decida el spec-author (por ejemplo,
> resolver los destinos de relaciones y tipos de contenido). Detalle abajo.

### Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | **T37.** Constantes `PRESUPUESTO_ELEMENTOS_XML = 200_000`, `EXTENSIONES_XML = (".xml", ".rels")` y `TROZO_DE_LECTURA = 64 * 1024`, junto a las de 2 MiB, 20 MiB y 500 entradas. `_analizador_de_elementos(al_abrir)`: el *expat* (`.parser`) de un `DefusedXMLParser(target=object(), forbid_dtd=True, forbid_entities=True, forbid_external=True)`, con `StartElementHandler = al_abrir` y sin el manejador por defecto de `ElementTree`. `_contar_elementos_xml(contenido, presupuesto=PRESUPUESTO_ELEMENTOS_XML) -> int`: recorre las entradas del ZIP en su orden, las `.xml`/`.rels` (sin distinguir mayúsculas), las lee por trozos de 64 KiB y se los da a un analizador nuevo por parte; el manejador suma uno y lanza `_PresupuestoAgotado` al pasar del presupuesto → `fichero_sospechoso` («El fichero tiene una estructura interna demasiado grande para ser la plantilla.» + la frase de descarga); cualquier otra excepción → `no_es_xlsx`; con `presupuesto=None` no corta. `leer`: la llamada entre `_inspeccionar_zip` y `_abrir`; el docstring de la clase dice el paso |
| `services/postventa-api/scripts/contar_elementos_xml_f036.py` (nuevo) | **T37.** `main([ruta])`: lee el fichero, llama a `_contar_elementos_xml(contenido, presupuesto=None)` e imprime solo cuatro líneas: elementos, presupuesto, un quinto y un veredicto (por debajo de un quinto / por encima de un quinto: parar y volver al spec-author / por encima del presupuesto: el lector lo rechaza). Sin nombres de fichero, parte u hoja ni contenido. Fichero ilegible → rc 2; no analizable → rc 1 con el código |
| `services/postventa-api/tests/test_f036_excel_lector.py` | **T37 y T38.** 22 funciones `test_f036_r117_…` (49 casos con los parametrizados), abajo |
| `services/postventa-api/tests/test_f036_alcance_cerrado.py` | El script nuevo entra en `NUEVOS_DE_F036`, para que le apliquen los controles de R46 (T37-6) |
| `specs/F-036-importar-excel/tasks.md` | T37 y T38 `[x]` |
| `progress/mutacion_F-036_bloque10ter.md` (nuevo) | **T38.** Informe de la campaña, con el análisis de los 4 supervivientes |

Sin dependencias nuevas (`defusedxml` ya estaba en `requirements.txt`), sin red,
Sigrid, base ni IA. Sin cambios en `docs/` ni en `azure-apps/`: no cambia nada de
lo que el servicio expone o consume (un fichero hostil ya daba
`fichero_sospechoso`, el mismo código 400).

Tests nuevos (`tests/test_f036_excel_lector.py`, sección «R117»):

- `…_el_presupuesto_es_de_200000_elementos`: la constante, escrita en el test;
- `…_los_ficheros_de_la_review_3_son_los_que_dicen_ser`: los siete, < 200 KB
  comprimidos, a menos de 1 KiB de los 20 MiB descomprimidos y por encima del
  presupuesto según un oráculo independiente (`_elementos`, que cuenta `<` menos
  `</`, `<!` y `<?` con `bytes.count`);
- `…_se_rechazan_en_menos_de_un_segundo` (7) y `…_con_la_memoria_acotada` (7):
  `fichero_sospechoso` con el mensaje de R117, < 1 s, pico de `tracemalloc` <
  32 MiB, y un doble de `load_workbook` que revienta y anota: **ninguna
  llamada**;
- `…_el_recuento_se_corta_al_pasar_el_presupuesto`: un doble de
  `_analizador_de_elementos` cuenta las aperturas que le llegan con 4.147.375
  `<xf/>`: **200.001**, ni una más;
- `…_sin_presupuesto_cuenta_todo_y_cuenta_bien`: con `presupuesto=None`, la
  cuenta de la función es la del oráculo (plantilla vacía, 210.887 elementos y
  Excel de errores);
- `…_cada_parte_se_lee_por_trozos_de_64_kib` (T38): un espía de
  `ZipExtFile.read` ve solo lecturas de 64 KiB, varias por parte;
- `…_el_analizador_lleva_las_tres_defensas_de_defusedxml` (T38): los cuatro
  manejadores de `defusedxml` puestos, el de apertura como único en Python, sin
  manejador por defecto, de texto ni de comentarios;
- `…_la_plantilla_completa_cabe_de_sobra_y_se_lee`: 26.886 < 40.000, y se lee
  con sus 1000 filas y se reconoce;
- `…_r66_el_excel_de_errores_mas_grande_cabe_en_el_presupuesto`: 1000 filas con
  error en las 8 columnas de datos (8000 comentarios): < 200.000 y se lee;
- `…_justo_el_presupuesto_se_admite_y_uno_mas_no`: frontera, con una parte
  `xl/relleno.xml` que no lee nadie;
- `…_el_total_es_de_todas_las_partes_juntas`: dos partes que caben por separado
  y juntas no;
- `…_cuentan_los_elementos_con_prefijo_y_los_de_un_rels`: `<x:mergeCell>` con
  su espacio de nombres declarado y un `.rels` suman exacto; y por encima del
  presupuesto con prefijo, `fichero_sospechoso`;
- `…_una_parte_que_no_se_analiza_es_no_es_xlsx_sin_abrir` (5): DTD en
  `styles.xml`, entidad externa en `workbook.xml`, entidad sin declarar en
  `core.xml`, `.rels` cortado y `[Content_Types].xml` roto; `no_es_xlsx` sin
  llamar a `load_workbook`;
- `…_el_tamano_y_el_zip_se_miran_antes_de_contar` (6) y
  `…_la_bomba_en_xml_se_rechaza_por_tamano_y_no_por_elementos`: el orden de la
  puerta por arriba (más de 2 MiB, sin firma, ZIP roto, macros, 501 entradas y
  una parte `.xml` de más de 20 MiB): cada uno con su código y su mensaje, y un
  doble de `_contar_elementos_xml` que revienta si se le llama;
- `…_el_recuento_va_antes_de_abrir_el_libro`: los tres pasos, anotados, van
  `_inspeccionar_zip` → `_contar_elementos_xml` → `_abrir`;
- el script: `…_cuenta_igual_que_la_funcion_y_no_imprime_contenido` (3: la
  plantilla de 2 filas, la completa y una por encima del presupuesto, sin
  cortar: la salida son exactamente las cuatro líneas),
  `…_en_las_fronteras_del_quinto_y_del_presupuesto` (4: 39.999, 40.000, 200.000
  y 200.001), `…_con_un_fichero_que_no_se_analiza` (2) y
  `…_con_un_fichero_que_no_se_puede_leer` (rc 2) y
  `…_se_lanza_desde_cualquier_sitio` (en un subproceso, sin `PYTHONPATH`, con un
  fichero que no existe: ningún test escribe un `.xlsx` en disco, R59).

Los siete ficheros se construyen **en memoria** escribiendo el XML: la
plantilla con las filas `BUENA` y `MALA` y, en `xl/styles.xml` o en la parte de
«Incidencias», el elemento repetido hasta rozar los 20 MiB (`<xf/>` antes de
`</cellXfs>`; `<dataValidation sqref="J2"/>`; `<brk id="1"/>` en un
`<rowBreaks>`; `<mergeCell ref="J2:K2"/>` en un `<mergeCells>`;
`<c r="J1200" s="1"/>` en una `<row r="1200">`; un `<conditionalFormatting>` de
`J2` con su regla y su fórmula; `<hyperlink ref="J2"/>` en un `<hyperlinks>`).

### Decisiones y desviaciones (para el reviewer y el humano)

1. **T37-1 · Hallazgo: partes con otra extensión** (ver el recuadro de arriba).
   No se ha tocado la regla de R117: cambiar qué partes se cuentan tiene un
   coste (el VML del Excel de errores) que decide el spec-author con el humano.
   El guion que construye el fichero `sheet1.dat` está en el directorio temporal
   de la sesión, no en el repositorio (no hay test que fije el hueco: fijaría un
   comportamiento que se quiere cambiar).
2. **T37-2 · Sin el manejador por defecto de `ElementTree`.** El
   `XMLParser` de Python que hay debajo de `DefusedXMLParser` pone
   `DefaultHandlerExpand`, que hace una llamada en Python por cada comentario o
   trozo de texto sin manejador. Medido con `styles.xml` lleno de `<!---->`
   hasta los 20 MiB (3 millones de comentarios, 0 elementos de más): **1,17 s**
   con él y **0,14 s** sin él. Quitarlo no abre nada: sin DTD, *expat* rechaza
   por sí mismo una entidad sin declarar (`undefined entity`), y la DTD la
   rechaza `defusedxml` al empezar (test `entidad-sin-declarar` y `dtd`). Se usa
   el `.parser` de `DefusedXMLParser`, que es lo que el propio `defusedxml`
   configura; el test de las tres defensas lo fija.
3. **T37-3 · Lo que cuesta de verdad el recuento: 0,14–0,32 s, no ~0,1 s.** §5.2
   estima «del orden de 0,1 s» para 200.000 elementos. Medido, depende de los
   bytes por elemento: casi todo es el propio *expat* (perfil: 0,38 de 0,47 s en
   `Parse` con el formato condicional; 0,06 s en el manejador). En un proceso
   por fichero, 0,14–0,32 s; en el mismo proceso, con otras suites de la
   máquina corriendo, 0,2–0,6 s; **con cobertura** (como en `init.sh`),
   0,44–0,69 s en el peor de tres. Margen frente al tope de 1 s de los tests: ~1,45
   veces con cobertura. Pasan en `init.sh` y en la campaña con 6 workers; si
   alguna vez fallara por tiempo con la máquina cargada, la causa es esa.
4. **T37-4 · El Excel de errores más grande: 52.910 elementos.** Pasa de un
   quinto del presupuesto (40.000), aunque cabe de sobra en 200.000; 24.004 son
   de `xl/comments/comment1.xml`, que en solo lectura `openpyxl` ni lee. El
   umbral de un quinto de T29 es para el `v2`, no para el Excel de errores; un
   test fija que el más grande cabe. Lo digo porque la opción (a) de T37-1 lo
   subiría a 148.916.
5. **T37-5 · El script usa `_contar_elementos_xml`, privada**, que es la que
   nombra T37 («con la misma función»), con `presupuesto=None`. El veredicto
   avisa desde 40.000 **incluido**: T29 pide que el `v2` quede «por debajo de
   40.000».
6. **T37-6 · El script entra en `NUEVOS_DE_F036`**
   (`tests/test_f036_alcance_cerrado.py`), como los otros tres scripts de
   F-036: así le aplican los controles de R46 (nada de escrituras en Sigrid).
7. **T37-7 · La extensión, sin distinguir mayúsculas** (`.XML` cuenta): es lo
   conservador, cuenta más.
8. **T37-8 · El informe de migración no se regenera en el repositorio.**
   Regenerado con el comando de T24 al directorio temporal (`--salida` e
   `--informe` allí, `--solo-informe`): 144 → 158, 14 separadas, 0 descartadas,
   **0 errores** (la ida y vuelta del `v2` pasa ya por el recuento), el mismo
   `sha256` del original antes y después, y el informe **idéntico** al
   versionado salvo la línea 1. `progress/migracion_F-036.md` no se toca y
   sigue sin códigos de proveedor.
9. **Otras mediciones.** El original real de OneDrive (guardado con Excel, solo
   leído): **1.680** elementos, y el lector nuevo sigue dando
   `formato_antiguo`. La plantilla vacía: 10.886.

### Fase RED

Tests escritos antes que el código, contra el lector de `becb693` (el código de
producción de HEAD antes de T37 es el mismo: `git diff becb693 HEAD --
services/` estaba vacío). Desde `services/postventa-api`.

1. Los rápidos (sin los catorce de los siete ficheros ni los del script):

   ```text
   $ .venv/Scripts/python.exe -m pytest tests/test_f036_excel_lector.py -k "r117 and not se_rechazan_en_menos and not se_rechazan_con_la_memoria and not script" -p no:cacheprovider -q --tb=line
   E   AttributeError: module 'infrastructure.documentos.excel_openpyxl' has no attribute 'PRESUPUESTO_ELEMENTOS_XML'
   E   AttributeError: module 'infrastructure.documentos.excel_openpyxl' has no attribute '_analizador_de_elementos'
   E   AttributeError: module 'infrastructure.documentos.excel_openpyxl' has no attribute '_contar_elementos_xml'
   …
   E   Failed: DID NOT RAISE FicheroNoEsPlantilla
   …
   E   AssertionError: assert [{'read_only'...only': False}] == []
   …
   14 failed, 8 passed, 160 deselected in 6.10s
   ```

   Con los del script: `21 failed, 8 passed` (`ImportError: cannot import name
   'contar_elementos_xml_f036' from 'scripts'`). Los 8 que pasan son los que
   fijan el orden por arriba (el lector de antes no cuenta, así que no llega al
   doble), el de la bomba en `.xml` (la para el tope de 20 MiB) y el que
   comprueba los ficheros de prueba. `DID NOT RAISE` es el total global: el
   lector de antes admite las dos partes juntas. Las cinco de `[{'read_only'…}]
   == []` son las partes que no se analizan: el lector de antes llega a llamar a
   `load_workbook`.

2. **Los siete ficheros (centrales)**, cada test en su subproceso con un tope de
   20 s (guion del directorio temporal, `subprocess.run(timeout=…)`). Con el
   doble de `load_workbook` del test, el lector de antes falla por **no dar
   `fichero_sospechoso`**:

   ```text
   --- …::test_f036_r117_los_ficheros_de_la_review_3_se_rechazan_en_menos_de_un_segundo[xf-en-estilos]
       3.0 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
       1 failed in 1.40s
   --- …[validacion]
       2.8 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
       1 failed in 1.31s
   --- …[salto-de-fila]
       2.8 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   --- …[combinado]
       2.8 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   --- …[celda-con-estilo-fila-1200]
       2.7 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   --- …[formato-condicional]
       2.7 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   --- …[hipervinculo]
       2.9 s, rc=1
       E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
       1 failed in 1.36s
   ```

   Y **sin dobles**, el lector de antes sobre los mismos ficheros, uno por
   subproceso con un tope de 30 s (el tiempo de verdad):

   ```text
   xf-en-estilos: CORTADO a los 30 s (sigue leyendo)
   validacion: CORTADO a los 30 s (sigue leyendo)
   salto-de-fila: CORTADO a los 30 s (sigue leyendo)
   combinado: CORTADO a los 30 s (sigue leyendo)
   celda-con-estilo-fila-1200: 84029 bytes, 14.94 s, admitido
   formato-condicional: 104251 bytes, 19.72 s, admitido
   hipervinculo: 84448 bytes, 24.60 s, admitido
   ```

   Tras los cortes no quedó ningún proceso de Python de este repositorio vivo
   (comprobado con `Get-CimInstance Win32_Process`; los que había eran de
   `markitdown-mcp` y de las suites de `albaranes`, que corrían a la vez).

### Verde, y las mediciones de antes y después

`pytest tests/test_f036_excel_lector.py` → **185 passed in 132.44s** (T37;
188 con los dos de T38 y el del fichero ilegible). `tests/test_f036_excel_lector.py`,
`tests/test_f036_alcance_cerrado.py` y `tests/test_f036_arquitectura.py` → 221
passed.

| Fichero (R3-1) | Elementos | Bytes | Lector de `becb693` (review 3 · aquí) | Lector nuevo (proceso aparte) | `tracemalloc` |
|---|---:|---:|---|---|---:|
| `<xf/>` en `styles.xml` | 4.147.375 | 63.626 | 113,9 s · 2.485 MB · cortado a los 30 s | **0,14 s**, `fichero_sospechoso`, 111 MB sin crecer | 0,79 MB |
| `<dataValidation/>` | 749.561 | 84.161 | 68,7 s · 901 MB · cortado a los 30 s | **0,22 s**, 112 MB sin crecer | 0,60 MB |
| `<brk/>` | 1.601.855 | 74.449 | 48,1 s · 858 MB · cortado a los 30 s | **0,17 s**, 112 MB sin crecer | 0,58 MB |
| `<mergeCell/>` | 872.670 | 84.150 | 34,7 s · 517 MB · cortado a los 30 s | **0,23 s**, 112 MB sin crecer | 0,60 MB |
| Celda vacía con estilo en la fila 1200 | 1.045.023 | 84.029 | 17,8 s · 647 MB · 14,9 s, admitido | **0,32 s**, 112 MB sin crecer | 0,60 MB |
| Formato condicional de una celda | 503.341 | 104.255 | 18,8 s · 240 MB · 19,7 s, admitido | **0,27 s**, 112 MB sin crecer | 0,62 MB |
| `<hyperlink/>` | 995.779 | 84.452 | 16,2 s · 393 MB · 24,6 s, admitido | **0,26 s**, 112 MB sin crecer | 0,60 MB |
| Plantilla completa (1000 filas, detalle de 2000) | **26.886** | 60.603 | — | admitida, 1000 filas | — |
| Excel de errores más grande (1000 × 8 errores) | 52.910 | 119.939 | — | admitido, 1000 filas | — |
| `sheet1.dat` con `<brk/>` (hallazgo T37-1) | 1.601.855 fuera del recuento | 74.456 | — | **48,4 s, admitido, 911 MB** | — |

El pico de proceso es el *working set* máximo (`GetProcessMemoryInfo`), con
~111 MB que son de construir el fichero de 20 MiB en memoria antes de leerlo:
la lectura no lo sube. Los elementos, del oráculo independiente. Mis ficheros
llevan algo más de elementos que los de la review (el mismo elemento, hasta los
mismos 20 MiB, sobre la plantilla con dos filas); el formato condicional,
503.341 frente a 164.113, porque mi bloque es más corto.

### Mutación (T38)

`timeout 5400 python -m harness.mutacion --feature F-036 --base becb693 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque10ter.md`,
desde la raíz, sin nada en segundo plano al acabar (los worktrees de la campaña,
borrados; el `worktree-agent-a6e2f9bed1d46cdbc` que lista `git worktree list`
no es de este encargo y no se ha tocado):

- **159 líneas en alcance**: 84 de `excel_openpyxl.py` y 75 del script;
- **22 mutantes: 18 muertos, 4 supervivientes, 0 timeouts**, 1436,5 s (24 min);
- los 4 supervivientes, cerrados con **2 tests nuevos** (commit de T38) y
  comprobados a mano, aplicando cada mutante sobre el árbol y pasando los dos
  tests: los cuatro **caen** (`1 failed`), y el fichero se restauró con
  `git checkout`:
  - `TROZO_DE_LECTURA = 64 * 1024` → `65 * 1024` y → `64 * 1025`: el tamaño del
    trozo no cambia la cuenta ni dónde se corta, pero §5.2 fija la lectura por
    trozos de 64 KiB, que es el *streaming*; lo fija
    `…_cada_parte_se_lee_por_trozos_de_64_kib`;
  - `forbid_entities=True` → `False` y `forbid_external=True` → `False`: con la
    DTD prohibida no pueden actuar (entidades y referencias externas van dentro
    de una DTD), así que eran equivalentes por comportamiento; en vez de pedir
    al humano que los acepte, lo fija `…_el_analizador_lleva_las_tres_defensas_de_defusedxml`.

Entre los muertos, los que importan: el presupuesto `200_000 → 200001` y la
comparación `total > limite → >=` (los mata la frontera), `total += 1 → += 2` y
`→ -= 1`, `total = 0 → 1`, `forbid_dtd=True → False` (lo mata el test `dtd`),
el `not` del filtro de extensiones, `Parse(trozo, False → True)` y
`Parse(b"", True → False)`, y los siete del script (umbrales, códigos de salida
y el `__main__`).

**Mutaciones de orden de la puerta, a mano** (las que T38 anuncia para la
review 4, hechas ya para que la review las tenga de partida; guion del
directorio temporal sobre una copia desechable de `git archive HEAD`, que
aplica cada una sobre `leer`, pasa `tests/test_f036_excel_lector.py` entero y
restaura):

| Mutación | Resultado |
|---|---|
| O7 · el recuento **después** de `_abrir` (dentro del `with`) | **Cae**: 20 failed (los siete `…_se_rechazan_en_menos_de_un_segundo`, los siete de memoria y los cinco de partes que no se analizan: el doble de `load_workbook` ve la llamada; y el del orden anotado) |
| O8 · el recuento **antes** de `_inspeccionar_zip` | **Cae**: 7 failed (`…_el_tamano_y_el_zip_se_miran_antes_de_contar[sin-firma, zip-roto, macros, 501-entradas, bomba-xml]`, `…_la_bomba_en_xml_se_rechaza_por_tamano_y_no_por_elementos` y el del orden anotado) |
| O9 · el recuento **antes** del tope de 2 MiB | **Cae**: 9 failed (`test_f036_r15_mas_de_2_mib_se_rechaza_sin_mirar_nada`, los seis de `…_se_miran_antes_de_contar`, el de la bomba y el del orden) |
| O10 · sin recuento | **Cae**: 24 failed |

Ningún equivalente nuevo. Con la puerta por debajo de `load_workbook` la suite
se pone en rojo, y por encima de `_inspeccionar_zip` o del tope de 2 MiB,
también: es lo que T38 pide que compruebe la review 4.

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tras el último commit de código (`e62b2d1`): raíz **62 passed** (5,64 s); servicio `api` **6124 passed, 67 skipped**, ejecutado de verdad (el árbol del servicio cambió: sin caché); `front` en verde (caché, no cambió). `ENTORNO LISTO`; ruff, 69 avisos (los de antes: el que añadí, ISC004, se corrigió). La suite del `api` entera, aparte: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api` → **6124 passed, 67 skipped in 518.24s**. De ellos, `tests/test_f036_excel_lector.py`: 188 (49 de R117, en 22 funciones) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2910 líneas cambiadas cubiertas (2907/2910, umbral 80%, nivel critico)`. Las 3 sin cubrir son del script: el `__main__` y lo que solo corre dentro del subproceso que lo lanza (con el `init.sh` anterior a `e62b2d1`, que añade el test del fichero ilegible en el mismo proceso, eran 2903/2910) |
| Mutación | `--base becb693`: 159 líneas, **22 mutantes, 18 muertos + 4 cerrados con 2 tests nuevos (comprobados a mano), 0 equivalentes**, 0 timeouts, 1436,5 s con 6 workers (`progress/mutacion_F-036_bloque10ter.md`). Orden a mano: 4 de 4 caen |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **1225,06 s** (0:20:25); aparte, sin cobertura: **518,24 s** (antes de T37, 289,54 s: los tests de R117 suman ~60–130 s según la carga, sobre todo los siete ficheros con `tracemalloc`, y la máquina tenía a la vez las suites de `albaranes` corriendo); `tests/test_f036_excel_lector.py`, 132,44 s |
| R117 | Los siete ficheros: de 15–25 s o cortados a los 30 s (la review: 16–114 s y 0,24–2,5 GB) → **0,14–0,32 s**, `tracemalloc` 0,58–0,79 MB y el proceso sin crecer (tabla de arriba). Plantilla completa: 26.886 elementos |

### Qué queda fuera y qué falta

- **Antes de la review 4: T37-1**, para el humano (vía el líder y el
  spec-author): contar también las partes con otra extensión (opción (a), con
  su coste en el Excel de errores), aceptar el riesgo por escrito (b) u otra
  regla (c). Con (a) o (c) hace falta una enmienda y una tarea más; lo de T37 se
  aprovecha entero (solo cambia qué partes entran en el recuento).
- **Siguiente: review 4**, con las mutaciones de orden de la puerta (hechas ya
  a mano, arriba).
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 (MANUALES) y T30**: sin tocar. En T29 paso 9, medir el `v2`
  guardado desde Excel con
  `.venv\Scripts\python.exe scripts\contar_elementos_xml_f036.py "<ruta del v2>"`
  (tiene que quedar por debajo de 40.000; el original guardado con Excel tiene
  1.680) y subir el fichero de los estilos: rechazo al momento.
- Fuera de alcance, dicho: la mejora de una sola pasada por «Incidencias»
  (§5.2 dice que no entra), y el coste de *expat* por encima de lo que estima
  §5.2 (T37-3).

## T37 bis–T38 bis (todas las partes del ZIP, presupuesto de 300.000) · 2026-10-01 · hecho; siguiente: review 4. T16 sigue siendo MANUAL del humano y está PENDIENTE

> **Resumen para el líder.** La opción (a) del hallazgo T37-1, tal como la
> escribe la séptima enmienda bis (R117; `design.md` §5.2, «Todas las
> partes»). El recuento recorre **todas** las entradas del ZIP, sea cual sea su
> extensión, y el presupuesto pasa a **300.000**. En una parte que no se
> declara XML, un fallo de *expat* deja contado lo abierto hasta ahí, deja de
> leer esa parte (ni se descomprime el resto) y el recuento sigue; en las `.xml`
> y `.rels`, sigue siendo `no_es_xlsx`; DTD o entidades, en cualquier parte,
> `no_es_xlsx`. **El fichero de T37-1** (`sheet1.dat`, 74 KB, 1,6 millones de
> `<brk/>`) pasa de **55,2 s, admitido y 898 MB** a **0,21 s,
> `fichero_sospechoso`, sin crecer la memoria y sin abrir el libro**. El Excel de
> errores más grande cuenta **148.916** (50 % del presupuesto) y se admite; la
> plantilla completa, **26.886** (9 %). Los tests de tiempo de R115 y R117 miden
> ahora en un subproceso sin cobertura. T37 bis `1b9e354`, T38 bis `d8572f4`:
> mutación con `--base 29e28a6`, **5 mutantes, 5 muertos**; mutaciones de orden
> a mano, **5 de 5 caen** (también volver a filtrar por extensión). El informe
> de migración no cambia (regenerado aparte: idéntico, 144 → 158, 0 errores).
> `bash harness/init.sh` en verde y la suite del `api` entera, aparte, en verde
> (abajo).
>
> **Para la review (T37 bis-1): el peor caso admitido cuesta más de lo que
> estima §5.2 con un tipo de elemento.** §5.2 estima 12–15 s con todo el
> presupuesto en «Incidencias». Medido en un proceso aparte, con 300.000
> elementos de un solo tipo: de **3,6 s** (celdas con estilo) a **13,7 s**
> (formato condicional), y **23,4 s y 389 MB** con `<dataValidation/>`. Cabe
> en los 45 s del proxy y en la memoria de una instancia, pero pasa la
> estimación. No cambia nada del código: la cifra es para que la review y el
> spec-author decidan si basta.

### Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | **T37 bis.** `PRESUPUESTO_ELEMENTOS_XML = 300_000`. `_contar_elementos_xml` recorre todas las entradas (sin el `continue` por extensión); `EXTENSIONES_XML` queda solo para decidir qué es un fallo: alrededor de cada parte, un `except ExpatError` que relanza (→ `no_es_xlsx`) si la parte se declara XML o si el fallo es una entidad sin declarar (`_ENTIDAD_SIN_DECLARAR`, el código de *expat* `XML_ERROR_UNDEFINED_ENTITY`), y si no, deja la parte ahí y sigue. Las excepciones de `defusedxml` (DTD, entidades declaradas o externas) no son `ExpatError` y siguen siendo `no_es_xlsx` en cualquier parte. Docstrings y comentarios de las constantes al día |
| `services/postventa-api/tests/test_f036_excel_lector.py` | **T37 bis.** `PRESUPUESTO = 300_000`; el oráculo `_elementos` cuenta también las partes que, con otra extensión, empiezan por `<`; el medidor en subproceso (`_segundos_aparte`, abajo) y 9 funciones nuevas `test_f036_r117_…` (13 casos) |
| `specs/F-036-importar-excel/tasks.md` | T37 bis y T38 bis `[x]` |
| `progress/mutacion_F-036_bloque10quater.md` (nuevo) | **T38 bis.** Informe de la campaña |

El script `scripts/contar_elementos_xml_f036.py` no cambia: cuenta con la misma
función, y su quinto sale de la constante (60.000). Sin dependencias nuevas, sin
red, Sigrid, base ni IA; sin cambios en `docs/` ni en `azure-apps/`.

**Los tests de tiempo, en un subproceso sin cobertura** (lo pide T37 bis):
`_cronometrado` sigue leyendo en el proceso del test (lo leído se compara
igual) y toma el tiempo de `_segundos_aparte`, que lanza `sys.executable -c` con
los bytes por la entrada estándar, sin ninguna variable `COV*` del entorno,
hace una pasada de calentamiento sin medir y mide la segunda. Lo usan todos
los tests de tiempo de R115 (los de `_cronometrado` y el del analizador de
filas, con el paso `filas_presentes`) y los de R117 (los siete de la review 3,
el de T37-1 y el del `.bin`).

Tests nuevos (`tests/test_f036_excel_lector.py`, sección «R117 · todas las
partes»):

- `…_el_fichero_de_t37_1_lleva_su_hoja_en_un_dat`: sin `sheet1.xml`; la
  relación de «Incidencias» apunta al `.dat`; < 200 KB; más de 1,5 millones de
  elementos; y, sin los saltos, `openpyxl` lee del `.dat` la plantilla con sus
  filas 2 y 3 (es decir, la hoja de verdad está ahí);
- `…_la_hoja_en_un_dat_se_rechaza_en_menos_de_un_segundo`:
  `fichero_sospechoso`, pico de `tracemalloc` < 32 MiB, ninguna llamada a
  `load_workbook` y < 1 s en el subproceso;
- `…_un_bin_con_xml_por_encima_del_presupuesto_se_rechaza`: lo mismo con
  `xl/oculto.bin`;
- `…_una_imagen_real_cuenta_cero_y_se_lee_un_solo_trozo`: un PNG válido de
  ~196 KB generado en el test; cuenta 0, un espía de `ZipExtFile.read` ve **una**
  lectura de 64 KiB de esa parte, y la plantilla se admite;
- `…_un_printer_settings_binario_no_impide_admitir_la_plantilla`;
- `…_una_parte_que_falla_a_mitad_cuenta_hasta_el_fallo` (2: `.dat` y `.bin`):
  1000 elementos, basura y otros 1000 → cuentan la raíz y los 1000 de antes, y
  se admite; con 300.000 antes del fallo, `fichero_sospechoso`;
- `…_tras_una_parte_que_no_es_xml_el_recuento_sigue`: una imagen antes, en el
  orden del ZIP, de una parte grande no corta el recuento;
- `…_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx`
  (5: entidad declarada y DTD en un `.bin`, entidad externa en un `.dat`,
  entidad sin declarar en un `.bin`, y un PNG con nombre `.xml`), sin llamar a
  `load_workbook`;
- `…_el_peor_caso_admitido_en_incidencias_se_lee`: justo 300.000 elementos,
  `<brk/>` en «Incidencias»: se admite y se lee con sus filas 2 y 3, sin tope de
  tiempo (12,96 s en la suite).

Cambiados: el de la constante (`…_es_de_300000_elementos`); el del Excel de
errores más grande (cuenta el VML, > 90.000 elementos, y el total es el del
oráculo); la frontera (300.000 / 300.001) y los del script (el quinto, 60.000)
salen solos de la constante.

### Decisiones y desviaciones (para el reviewer)

1. **T37 bis-1 · El peor caso admitido, medido** (recuadro de arriba). Tabla
   abajo.
2. **T37 bis-2 · Una entidad sin declarar es `no_es_xlsx` también en un
   binario.** R117 dice «una parte con DTD o entidades, tenga la extensión que
   tenga, sigue siendo `no_es_xlsx`». La DTD y las entidades declaradas o
   externas las corta `defusedxml` con sus propias excepciones; una referencia
   `&e;` sin DTD la corta *expat* con un `ExpatError` normal, que en un binario
   se habría tomado por «deja de ser XML». Se distingue por su código
   (`XML_ERROR_UNDEFINED_ENTITY`). Riesgo: un binario de verdad que empezara
   siendo XML y llevara `&algo;` se rechazaría; un PNG, un `printerSettings` o
   un VML no lo hacen (los tests los admiten).
3. **T37 bis-3 · Los tests de tiempo, con calentamiento.** El subproceso hace
   una lectura sin medir (importaciones perezosas) y mide la segunda: mide el
   producto en régimen, como en la Function, que no arranca en cada petición.
4. **T37 bis-4 · Lo que tarda la suite.** Con los subprocesos, cada test de
   tiempo paga ~1–2 s de arranque de Python; con el peor caso admitido
   (~13 s), el fichero del lector pasa de 132 s a ~185 s.
5. **T37 bis-5 · El informe de migración no se regenera en el repositorio.**
   Regenerado al directorio temporal con el comando de T24 (`--solo-informe`):
   144 → 158, 14 separadas, 0 descartadas, **0 errores**, el mismo `sha256`
   antes y después, e **idéntico** al versionado salvo la línea 1. El original
   real (guardado con Excel, solo leído) cuenta 1.680 elementos con todas las
   partes y sigue dando `formato_antiguo`.

### Fase RED

Contra el lector de `29e28a6` (el de producción de HEAD antes de T37 bis: los
commits de después de `e62b2d1` solo tocan `specs/` y `progress/`). Desde
`services/postventa-api`.

1. **El fichero de T37-1 y el `.bin` (centrales)**, cada uno en su subproceso,
   sin dobles, con un tope de 90 s (guion del directorio temporal; pico de
   *working set* con `GetProcessMemoryInfo`):

   ```text
   sheet1.dat (T37-1): 74455 bytes, 55.22 s, admitido, pico 898 MB (antes de leer 29 MB)
   xl/oculto.bin por encima: 34428 bytes, 0.17 s, admitido, pico 30 MB (antes de leer 29 MB)
   ```

   El primero pasa de 1 s y ninguno da `fichero_sospechoso`.

2. Los tests nuevos y los que cambian con el presupuesto:

   ```text
   $ .venv/Scripts/python.exe -m pytest tests/test_f036_excel_lector.py -k "r117 and (dat or bin or imagen or printer or falla_a_mitad or tras_una_parte or cualquier_parte or peor_caso or 300000 or mas_grande or justo_el or plantilla_completa)" -p no:cacheprovider -q --tb=line
   E   assert 200000 == 300000
   E   AssertionError: assert 52910 == 148916
   E   domain.models.errores.FicheroNoEsPlantilla: fichero_sospechoso: El fichero tiene una estructura interna demasiado grande para ser la plantilla. Descarga la plantilla de la obra desde el portal.
   E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
   E   assert [] == [65536]
   E   AssertionError: assert 10886 == (10886 + 1001)
   E   AssertionError: assert 10886 == (10886 + 1001)
   E   Failed: DID NOT RAISE FicheroNoEsPlantilla
   E   AssertionError: assert [{'read_only'...only': False}] == []
   E   AssertionError: assert [{'read_only'...only': False}] == []
   E   AssertionError: assert [{'read_only'...only': False}] == []
   E   AssertionError: assert [{'read_only'...only': False}] == []
   E   domain.models.errores.FicheroNoEsPlantilla: fichero_sospechoso: El fichero tiene una estructura interna demasiado grande para ser la plantilla. Descarga la plantilla de la obra desde el portal.
   FAILED …::test_f036_r117_el_presupuesto_es_de_300000_elementos
   FAILED …::test_f036_r117_r66_el_excel_de_errores_mas_grande_cabe_en_el_presupuesto
   FAILED …::test_f036_r117_justo_el_presupuesto_se_admite_y_uno_mas_no
   FAILED …::test_f036_r117_la_hoja_en_un_dat_se_rechaza_en_menos_de_un_segundo
   FAILED …::test_f036_r117_un_bin_con_xml_por_encima_del_presupuesto_se_rechaza
   FAILED …::test_f036_r117_una_imagen_real_cuenta_cero_y_se_lee_un_solo_trozo
   FAILED …::test_f036_r117_una_parte_que_falla_a_mitad_cuenta_hasta_el_fallo[xl/worksheets/sheet9.dat]
   FAILED …::test_f036_r117_una_parte_que_falla_a_mitad_cuenta_hasta_el_fallo[xl/raro.bin]
   FAILED …::test_f036_r117_tras_una_parte_que_no_es_xml_el_recuento_sigue
   FAILED …::test_f036_r117_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx[bin-entidad]
   FAILED …::test_f036_r117_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx[bin-dtd]
   FAILED …::test_f036_r117_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx[dat-entidad-externa]
   FAILED …::test_f036_r117_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx[bin-entidad-sin-declarar]
   FAILED …::test_f036_r117_el_peor_caso_admitido_en_incidencias_se_lee
   14 failed, 6 passed, 182 deselected in 17.11s
   ```

   Las dos de `fichero_sospechoso: …` son la frontera y el peor caso: con el
   presupuesto viejo, 300.000 elementos se rechazaban. Los 6 que pasan: el que
   comprueba el fichero de T37-1, el del `printerSettings`, el de la plantilla
   completa, el del PNG con nombre `.xml` (ya era `no_es_xlsx`) y los dos del
   fichero `combinado` de la review 3, que el filtro `-k` coge por «bin» y ya
   pasaban con T37.

### Verde, y las mediciones

`pytest tests/test_f036_excel_lector.py tests/test_f036_alcance_cerrado.py`
(la verificación de T37 bis) → **228 passed in 184.64s**; de R117, 63 casos.

**Antes y después, en un proceso aparte por fichero** (pico de *working set*;
~29 MB son del intérprete):

| Fichero | Elementos | Bytes | Lector de `29e28a6` | Lector nuevo |
|---|---:|---:|---|---|
| `sheet1.dat` con `<brk/>` (T37-1) | 1.601.855 | 74.455 | **55,22 s, admitido, 898 MB** | **0,21 s, `fichero_sospechoso`, 30 MB** |
| `xl/oculto.bin` con 300.001 | 300.001 | 34.428 | 0,17 s, admitido | 0,08 s, `fichero_sospechoso` |
| Los siete de la review 3 | 503.341–4.147.375 | 63.629–104.254 | (T37: 0,14–0,32 s) | 0,14–0,47 s, `fichero_sospechoso`, 30 MB |
| Plantilla completa | 26.886 (9 %) | 60.603 | admitida | admitida |
| Excel de errores más grande | 148.916 (50 %), 96.006 del VML | 119.939 | admitido (contaba 52.910) | admitido |
| Original real, guardado con Excel | 1.680 | 21.726 | `formato_antiguo` | `formato_antiguo` |

**El peor caso admitido** (la plantilla con 2 filas más un solo tipo de
elemento hasta justo 300.000 en total; un proceso aparte por fichero):

| Lo repetido | Dónde | Tiempo | Pico de proceso |
|---|---|---:|---:|
| `<dataValidation/>` | «Incidencias» | **23,39 s** | **389 MB** |
| Formato condicional | «Incidencias» | 13,71 s | 162 MB |
| `<hyperlink/>` | «Incidencias» | 10,59 s | 209 MB |
| `<mergeCell/>` | «Incidencias» | 9,28 s | 202 MB |
| `<xf/>` | `xl/styles.xml` | 7,69 s | 212 MB |
| `<brk/>` | «Incidencias» | 6,29 s | 190 MB |
| Celda vacía con estilo en la fila 1200 | «Incidencias» | 3,62 s | 214 MB |

Medido con la máquina cargada (las suites de `albaranes` corrían a la vez):
las cifras son un techo razonable, no un mínimo.

### Mutación (T38 bis)

`timeout 5400 python -m harness.mutacion --feature F-036 --base 29e28a6 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque10quater.md`,
desde la raíz, sin nada en segundo plano al acabar (worktrees de la campaña
borrados; el `worktree-agent-a6e2f9bed1d46cdbc` no es de este encargo):

> **Errata corregida en T47 (2026-10-01; R4-3, arrastrada en R5-5).** La orden
> de arriba pide `--workers 6`, pero la campaña corrió con **5 workers**: es lo
> que dice el informe de la herramienta
> (`progress/mutacion_F-036_bloque10quater.md`: «Workers | 5», y su cabecera,
> `--workers 5`). La tabla de «Evidencias» decía «con 6 workers» y ahora dice 5.
> Los 335,4 s son el tiempo total que midió la herramienta, no un cálculo a
> partir del número de workers: no cambian, y en esta sección no hay ninguna
> otra cifra derivada de él.

- **37 líneas en alcance**, de `excel_openpyxl.py`;
- **5 mutantes, 5 muertos, 0 supervivientes, 0 timeouts**, 335,4 s: el
  presupuesto `300_000 → 300001`, `Parse(trozo, False → True)`,
  `Parse(b"", True → False)` (lo mata el `.rels` cortado) y los dos de la
  condición del fallo (`==` → `!=` y `or` → `and`).

**Mutaciones de orden, a mano** (guion del directorio temporal sobre una copia
de `git archive HEAD`; cada una se aplica, se pasa
`tests/test_f036_excel_lector.py` entero y se restaura):

| Mutación | Resultado |
|---|---|
| O7 · el recuento **después** de `_abrir` | **Cae**: 27 failed (los de los siete ficheros, tiempo y memoria; los de partes que no se analizan; el de T37-1 y el del `.bin`, cuyo doble de `load_workbook` ve la llamada; y el del orden) |
| O8 · el recuento **antes** de `_inspeccionar_zip` | **Cae**: 7 failed |
| O9 · el recuento **antes** del tope de 2 MiB | **Cae**: 9 failed |
| O10 · sin recuento | **Cae**: 34 failed |
| O11 · **volver a filtrar por extensión** (`if not se_declara_xml: continue`) | **Cae**: 12 failed (`…_sin_presupuesto_cuenta_todo_y_cuenta_bien`, el del Excel de errores con el VML, el de T37-1, el del `.bin`, el de la imagen, los de la parte que falla a mitad…) |

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tras los commits de T37 bis y T38 bis (`d8572f4`): raíz **62 passed** (4,47 s); servicio `api` **6138 passed, 67 skipped**, ejecutado de verdad (sin caché: el árbol del servicio cambió); `front` en verde (caché). `ENTORNO LISTO`; ruff, 69 avisos (los de antes). La suite del `api` entera, aparte: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api` → **6138 passed, 67 skipped in 301.54s** |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 2916 líneas cambiadas cubiertas (2913/2916, umbral 80%, nivel critico)`. Las 3 sin cubrir siguen siendo las del script que solo corren en su subproceso |
| Mutación | `--base 29e28a6`: 37 líneas, **5 mutantes, 5 muertos, 0 supervivientes**, 0 timeouts, 335,4 s con **5** workers (`progress/mutacion_F-036_bloque10quater.md`; *errata corregida en T47: decía 6*). Orden a mano: 5 de 5 caen |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **703,27 s** (0:11:43); aparte, sin cobertura: **301,54 s**; `tests/test_f036_excel_lector.py` con `test_f036_alcance_cerrado.py`: 184,64 s |
| T37-1 | 55,22 s, admitido, 898 MB → **0,21 s, `fichero_sospechoso`, 30 MB** |

### Qué queda fuera y qué falta

- **Siguiente: review 4**, con las mutaciones de orden (hechas ya a mano,
  arriba) y la cifra del peor caso admitido (T37 bis-1) para decidir si basta.
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 (MANUALES) y T30**: sin tocar. En T29 paso 9, el `v2` guardado
  desde Excel se mide con el script de T37 y tiene que quedar por debajo de
  **60.000** (el quinto nuevo).

## T39–T41 (lectura aislada) · 2026-10-01 · hecho; siguiente: T42–T44. T16 sigue siendo MANUAL del humano y está PENDIENTE

Octava enmienda (review 4, R4-1; el humano eligió la opción (A) «pero dobla los
límites»): la biblioteca de Excel lee el fichero subido en un **proceso hijo**
con 30 s y 1 GiB (R118–R120). Este encargo: T39 (fase RED de R4-1), T40 (el
ejecutor y el lector aislado) y T41 (medir el tope descomprimido y el del
resultado). T42–T44 van en otro encargo.

### T39 · Fase RED: los ficheros de R4-1, medidos de extremo a extremo

Los tres ficheros, construidos en memoria por `_de_r4_1` en
`tests/test_f036_lector_aislado.py` (quedan ahí para T42): la plantilla
generada con dos filas (`BUENA`, `MALA`) y **un** elemento más en
«Incidencias» con un `sqref` de `A2 ` repetido hasta rozar el tope
descomprimido vigente (20 MiB en HEAD): un `<dataValidation>` delante de
`</dataValidations>`, un `<conditionalFormatting>` delante de
`<dataValidations` y `<scenarios sqref="…">` (con un `<scenario>` dentro)
delante de `<autoFilter`. En los escenarios el `sqref` va en la lista
(`ScenarioList`), que es donde lo convierte `openpyxl` 3.1.5
(`worksheet/scenario.py`); la review decía «un `<scenario>`», y el atributo
está en su contenedor.

Medida: guion del directorio temporal (no versionado); cada fichero se pasa
por la entrada estándar a un subproceso **sin cobertura** que ejecuta
`LectorPlantillaOpenpyxl().leer` de HEAD (`5bf96e7`), con tope de 120 s; el
pico es el `PeakWorkingSetSize` del proceso (Windows, `K32GetProcessMemoryInfo`),
que un hilo vigía va imprimiendo para tenerlo también si se corta.

Comando: `.venv/Scripts/python.exe <tmp>/medir_r4_1.py 120` desde
`services/postventa-api`. Salida real (segunda pasada; la primera, con el
medidor de memoria aún mal declarado, cortó dos a los 120 s y leyó el
escenario en 114,7 s):

```
validacion: comprimido=54421 descomprimido=20971517 rangos=6894083 elementos=10908 -> 109.4 s, leido, pico=1632 MB (antes de leer 28 MB)
formato-condicional: comprimido=54167 descomprimido=20971518 rangos=6894073 elementos=10909 -> 109.2 s, leido, pico=1635 MB (antes de leer 28 MB)
escenario: comprimido=54137 descomprimido=20971517 rangos=6894084 elementos=10909 -> 108.0 s, leido, pico=1632 MB (antes de leer 28 MB)
```

| Fichero | Comprimido | Descomprimido | Rangos del `sqref` | Elementos (R117) | Lector de HEAD |
|---|---:|---:|---:|---:|---|
| `<dataValidation>` | 54 KB | 20,0 MiB | 6.894.083 | 10.908 | **109,4 s, admitido, 1.632 MB** |
| `<conditionalFormatting>` | 54 KB | 20,0 MiB | 6.894.073 | 10.909 | **109,2 s, admitido, 1.635 MB** |
| `<scenarios>` | 54 KB | 20,0 MiB | 6.894.084 | 10.909 | **108,0 s, admitido, 1.632 MB** (114,7 s en la primera pasada) |

**Confirma la estimación de la review 4** (~100 s y 1,6 GB) y la empeora en
un punto: los tres ficheros **se admiten** —no hay nada que rechazar en las
filas—, así que una importación así no solo tarda: entra en la bandeja tras
casi dos minutos, por encima de los 40 s del front y los 45 s del proxy, con
1,6 GB en la instancia que comparte la Function con el circuito de partes.
Los tres pasan los pasos baratos: 54 KB comprimidos, justo bajo los 20 MiB y
~11.000 elementos, un 3,6 % del presupuesto de R117.

**Tests escritos en T39** (`tests/test_f036_lector_aislado.py`):

- `test_f036_r118_los_ficheros_de_r4_1_son_los_que_dicen_ser[…]` (×3,
  verdes): < 2 MiB comprimidos, al borde del tope descomprimido vigente, más
  del 90 % de los rangos que caben y por debajo de un quinto del presupuesto.
- `test_f036_r118_los_ficheros_de_r4_1_los_para_el_hijo_a_tiempo_y_sin_memoria_del_padre[…]`
  (×3, **en rojo**): por `LectorPlantillaAislado` con el hijo de verdad y un
  tope inyectado de 3 s, `fichero_sospechoso` antes de 3 s más el arranque y
  sin que el pico de `tracemalloc` del padre pase del resultado acotado más
  los bytes del fichero. Se commitean con `xfail(strict=True,
  raises=ImportError)` para que el árbol commiteado siga en verde; T40 les
  quita la marca.

Salida real del rojo, `.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q --runxfail --tb=short`:

```
...FFF                                                                   [100%]
================================== FAILURES ===================================
_ test_f036_r118_los_ficheros_de_r4_1_los_para_el_hijo_a_tiempo_y_sin_memoria_del_padre[validacion] _
tests\test_f036_lector_aislado.py:136: in test_f036_r118_los_ficheros_de_r4_1_los_para_el_hijo_a_tiempo_y_sin_memoria_del_padre
E   ImportError: cannot import name 'lector_aislado' from 'infrastructure.documentos' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\infrastructure\documentos\__init__.py)
(… lo mismo para [formato-condicional] y [escenario] …)
3 failed, 3 passed in 2.57s
```

Sin `--runxfail`: `3 passed, 3 xfailed in 2.95s`.

### T40 · El ejecutor en subproceso y el lector aislado

**Qué cambió** (todo bajo `services/postventa-api/`):

- **Nuevo `infrastructure/documentos/ejecutor_aislado.py`**: `EstadoHijo`
  (`ok`, `tiempo`, `memoria`, `murio`, `demasiado_grande`), `SalidaHijo`, el
  protocolo `EjecutorAislado` (la firma de `design.md` §5.2) y el ejecutor de
  verdad, `EjecutorMultiprocessing(destino, metodo=None)`:
  - `metodo_de_arranque()`: `forkserver` en Linux, con
    `set_forkserver_preload([ejecutor_aislado, <módulo del destino>])`;
    `spawn` en los demás;
  - el hijo (`_principal_hijo`) aplica `setrlimit(RLIMIT_AS, (tope, tope))`
    nada más empezar (si `resource` existe; si `setrlimit` falla, el error no
    se captura y el hijo muere **antes** de leer), manda un byte (`1`/`0`: si
    el tope se aplicó), importa la función por su nombre (`modulo:funcion`) y
    manda el resultado; un `MemoryError` sale con `CODIGO_SALIDA_MEMORIA = 77`;
  - el padre espera cada mensaje con `multiprocessing.connection.wait` sobre
    el canal y el `sentinel` del hijo, hasta el tope de reloj contado desde el
    arranque; lee con `recv_bytes(maxlength=…)` (1 byte la bandera,
    `max_bytes_resultado` el cuerpo); EOF o hijo muerto → `murio` (o
    `memoria` por el código de salida); mensaje de más → `demasiado_grande`;
    al acabar, `join(1 s)` si fue bien o `join(0)` si no, `terminate()`,
    `kill()` si sigue vivo al segundo y `join()` **siempre**;
  - `tope_de_memoria_disponible()`: si `resource.setrlimit` y `RLIMIT_AS`
    existen.
- **Nuevo `infrastructure/documentos/lector_aislado.py`**:
  `LectorPlantillaAislado(entorno=…, ejecutor=None, segundos=30,
  bytes_memoria=1 GiB, max_bytes_resultado=…, tope_de_memoria=None,
  semaforo=None, espera=5)`, que implementa `LectorPlantillaPort`:
  1. los pasos 1–2 bis en el padre: `_comprobar_tamano`, `_inspeccionar_zip`
     y `_contar_elementos_xml`, **trasladados aquí desde `excel_openpyxl.py`**
     sin cambiar ni una línea de su lógica (D-T40-2);
  2. R119: sin tope de memoria posible, en `dev`/`pro` →
     `LectorSinAislamiento` (503) sin leer; fuera, se lee y se avisa **una
     vez por proceso** (`lector_aislado: sin tope de memoria en esta
     plataforma`);
  3. R120: semáforo de una plaza por proceso (`_LECTURAS`), espera de 5 s;
     ocupado → `LecturaOcupada` (503), sin llamar al ejecutor; se suelta
     siempre (`finally`);
  4. el ejecutor con `SEGUNDOS_HIJO = 30`, `BYTES_MEMORIA_HIJO = 1024 ** 3` y
     `MAX_BYTES_RESULTADO` (provisional en T40, lo fija T41);
  5. el log de cada lectura: `lector_aislado: estado=… segundos=…
     tope_memoria_aplicado=…`, sin contenido (R119);
  6. cualquier salida que no sea `ok` con cuerpo → `fichero_sospechoso` con el
     mensaje de §5.2 («El fichero no se ha podido leer en el tiempo y la
     memoria que tiene la plantilla.») y la coletilla de siempre de los
     rechazos; con `ok`, `libro_desde_json` valida el JSON campo a campo
     (claves exactas, tipos, números de fila, columnas conocidas) y
     reconstruye el `LibroLeido`; un error de dominio del hijo
     (`{"error": {codigo, motivo}}`, código de la lista cerrada) se vuelve a
     levantar con su código y su motivo; lo demás, `fichero_sospechoso`.
  Además, `libro_a_json` y `error_a_json` (el JSON que manda el hijo). **No
  importa `openpyxl`**, ni directamente ni a través de `excel_openpyxl`.
- **`infrastructure/documentos/excel_openpyxl.py`**: pierde los pasos 1–2 bis
  (los importa de `lector_aislado` y reexporta `MAX_BYTES_DESCOMPRIMIDOS` y
  `PRESUPUESTO_ELEMENTOS_XML`, que siguen siendo sus topes); gana
  `_leer_libro` (abrir, extraer y cerrar siempre: lo que hacía el final de
  `leer`) y **`leer_en_hijo(contenido) -> bytes`**, la función que corre en el
  hijo. `_abrir` y `_leer_libro` dejan pasar `MemoryError` (antes lo
  convertían en `no_es_xlsx`). `LectorPlantillaOpenpyxl` sigue, en proceso,
  para el script de migración.
- **`domain/models/errores.py`**: `LectorSinAislamiento` y `LecturaOcupada`.
- **`function_app.py`**: `POST /api/importaciones` traduce los dos a **503**
  `{"error": motivo}`, con su línea en la docstring.
- **`interface_adapters/api/importar.py`**: sin lector inyectado, compone
  `LectorPlantillaAislado(entorno=obtener_ajustes().entorno)`.
- **Tests**: `tests/test_f036_lector_aislado.py` (129: 128 + 1 solo de Linux),
  `tests/hijos_f036.py` (las funciones que hacen de hijo, solo biblioteca
  estándar), y en `test_f036_arquitectura.py` (2 tests: los dos módulos del
  padre no importan `openpyxl` ni `excel_openpyxl`, por `ast`; y en un
  intérprete limpio, importar `lector_aislado` no carga `openpyxl`),
  `test_f036_importar_http.py` (3 nuevos: la composición con el entorno, que
  `importar.py` ya no compone el lector en proceso, y los dos 503),
  `test_f036_alcance_cerrado.py` (los dos módulos nuevos en `NUEVOS_DE_F036`)
  y `test_f036_excel_lector.py` (el espía del analizador de elementos se pone
  ahora en `lector_aislado`, donde vive).

**Decisiones y desviaciones** (para el reviewer):

- **D-T40-1 · Nombres.** `tasks.md` dice «`EjecutorAislado`, con
  `multiprocessing`» y `design.md` llama `EjecutorAislado` al **protocolo**.
  Se queda el protocolo con ese nombre y la clase de verdad es
  `EjecutorMultiprocessing`.
- **D-T40-2 · Dónde viven los pasos baratos.** §5.2 dice que
  `lector_aislado.py` hace los pasos 1–2 bis y no importa `openpyxl`, y que
  `excel_openpyxl.py` se queda con el generador y la parte del hijo. Como
  `excel_openpyxl.py` importa `openpyxl` al cargarse, los pasos se mueven a
  `lector_aislado.py` tal cual (mismo código, mismos mensajes) y
  `excel_openpyxl.py` los importa de allí. Los tests de R15–R17 y R117 siguen
  pasando sin tocarlos, salvo el espía de `_analizador_de_elementos`.
- **D-T40-3 · La función del hijo, por su nombre.** El ejecutor recibe
  `"modulo:funcion"` y el hijo la importa; si recibiera la función, el padre
  tendría que importar `excel_openpyxl` para pasarla. Por eso los tests del
  ejecutor de verdad usan `tests/hijos_f036.py`.
- **D-T40-4 · Número de filas.** §5.2 dice «número de filas ≤ 1002». El
  lector lee de la fila 2 a la 1002 (`ULTIMA_FILA + 1`), así que como mucho
  son 1001: se exige `len(filas) ≤ 1001` y cada `numero` en `[2, 1002]`,
  estrictamente creciente. Es más estricto que la letra y es lo que puede
  devolver el lector.
- **D-T40-5 · Los nulos.** Se admiten donde el dominio los admite
  (`identificador`, `version`, `obra_codigo`, `CeldaLeida.valor` y
  `texto_original`), aunque el lector de hoy no devuelva nunca un valor nulo
  en una celda: el esquema es el del dominio.
- **D-T40-6 · `MemoryError`** ya no es `no_es_xlsx` tampoco en el lector en
  proceso: sale tal cual. En el hijo es lo que da `memoria`; en la migración,
  un error de verdad en vez de un rechazo engañoso.
- **D-T40-7 · El orden** del lector aislado: pasos baratos → R119 → semáforo
  → ejecutor. Con R119 delante del semáforo, un `dev`/`pro` sin tope no hace
  esperar a nadie. Si `Process.start()` falla (no se puede crear el
  proceso), el error sube tal cual (500): es de la plataforma, no del
  fichero.
- **D-T40-8 · La guardia de red en Linux.** El servidor de *fork* habla con el
  padre por un *socket* Unix y `conftest.py` (`sin_red`) prohíbe todo
  `connect`. El fixture `ipc_local_permitido` (en
  `test_f036_lector_aislado.py`, importado en `test_f036_importar_http.py`)
  deja pasar **solo** `AF_UNIX` en los tests que arrancan hijos de verdad; en
  Windows no cambia nada. No se toca `conftest.py`.
- **H-T40-1 · Hallazgo: la memoria del padre en el paso 2 bis.** El recuento
  de R117 corre en el padre y *expat* guarda **la etiqueta de apertura entera,
  con sus atributos**, antes de llamar al manejador; `pyexpat` la copia luego
  a `str`. Con el fichero de R4-1 de validación, medido con `tracemalloc`
  sobre `_contar_elementos_xml` solo:

  | Tope descomprimido del fichero | Pico en el padre | Tiempo |
  |---:|---:|---:|
  | 4 MiB | 11,8 MiB | 0,07 s |
  | 8 MiB | 23,8 MiB | 0,10 s |
  | 20 MiB | 83,8 MiB | 0,21 s |

  Es de 3 a 4,2 veces el tamaño del elemento más grande, acotado por el tope
  descomprimido; no crece con lo que costaría en `openpyxl` (1,6 GB en T39).
  Existe desde T37 (también en el lector en proceso). §5.2 pide que «la
  memoria del padre no crezca más allá del resultado acotado»: con el recuento
  en el padre eso no se cumple al pie de la letra. El test de T39 (el de los
  ficheros de R4-1) admite `MAX_BYTES_RESULTADO + 5 × MAX_BYTES_DESCOMPRIMIDOS
  + margen`; **para T42 y la review 5**: o se acepta así (el tope de T41 lo
  deja en unas decenas de MB), o el spec-author decide otra cosa (p. ej. un
  tope de tamaño por etiqueta en el recuento). No se ha cambiado la
  producción por esto.
- **H-T40-2 · Observación de `spawn` en Windows, sin efecto en producción.**
  Midiendo con un guion **sin** `if __name__ == "__main__"`, el hijo de
  `spawn` vuelve a ejecutar el guion al arrancar, falla en el arranque y
  muere; si los argumentos (el fichero) no caben en la tubería de arranque,
  `Process.start()` de CPython se queda bloqueado escribiéndolos (se vio con
  la plantilla de 34 KB; con 1 byte el padre ve `murio` en 0,2 s). No pasa
  con un `__main__` protegido (pytest, el *worker* de Functions, los guiones
  de medida corregidos) ni en Linux (`forkserver`). Se anota por si alguien
  mide así.

**Fase RED** (tests escritos antes que el código). Comando:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q --tb=short`
con los tests nuevos y sin `ejecutor_aislado.py`, `lector_aislado.py`,
`leer_en_hijo` ni los errores nuevos. Salida real:

```
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f036_lector_aislado.py:29: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'LecturaOcupada' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f036_lector_aislado.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.60s
```

Primera pasada con el código (antes de ajustar el tope de memoria del padre
en el test de R4-1, H-T40-1): `3 failed, 125 passed, 1 skipped in 26.09s`,
los tres por `assert 87908320 < (16777216 + 8388608)` (el pico del padre).

**Verde.** `.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py tests/test_f036_arquitectura.py tests/test_f036_importar_http.py tests/test_f036_excel_lector.py tests/test_f036_alcance_cerrado.py tests/test_f036_migracion.py tests/test_f036_pipeline_importacion.py tests/test_f010_endpoints_protegidos.py -q -p no:cacheprovider`
→ **696 passed, 1 skipped in 183.52s**. El *skip* es
`test_f036_r119_en_linux_el_tope_de_memoria_se_aplica_al_hijo` (solo
Linux); lo mismo se ha comprobado a mano en Linux (abajo).

Los tres ficheros de R4-1 por el lector aislado, con el hijo de verdad y un
tope inyectado de 3 s: **`fichero_sospechoso` en 3,7–4,0 s** cada uno (eran
108–109 s, admitidos y 1,6 GB en T39).

**El coste de arranque del hijo** (guion del directorio temporal, un proceso
nuevo por medida, 6 lecturas seguidas; `segundos` es el de `SalidaHijo`, del
arranque a la entrega):

| Plataforma | Qué corre en el hijo | Primero | Siguientes |
|---|---|---:|---:|
| Windows 11, Python 3.12.7, `spawn` | `eco` (solo biblioteca estándar) | 0,48 s | 0,39–0,49 s |
| Windows 11, Python 3.12.7, `spawn` | `leer_en_hijo`, plantilla de 2 filas | 0,61 s | 0,64–0,81 s |
| Linux (contenedor `python` 3.12.14 local, sin red), `forkserver` | `leer_en_hijo`, plantilla de 2 filas | **0,79 s** (arranca el servidor y precarga `openpyxl`) | **0,11–0,13 s** |

En Linux, en el mismo contenedor (código y dependencias puras copiados dentro,
`--network none`): `metodo: forkserver tope disponible: True`; reservar
64 MiB con tope de 256 MiB → `ok`, `tope aplicado: True`; reservar 512 MiB →
**`memoria`** en 0,016 s; un hijo que no acaba con tope de 1 s → **`tiempo`**
en 1,002 s; y `openpyxl` **no** está en `sys.modules` del padre tras seis
lecturas. Es la comprobación del test que se salta en Windows, hecha con un
guion porque en el contenedor no hay `pydantic` (sin red no se instala).

### T41 · El tope descomprimido y el del resultado, medidos

**La medición** (guion del directorio temporal, `medir_t41.py`, con el
generador de la rama; `descomprimido` es la suma de `file_size` del ZIP,
`json` los bytes de `excel_openpyxl.leer_en_hijo`). Comando:
`.venv/Scripts/python.exe <tmp>/medir_t41.py` desde `services/postventa-api`,
con `ORIGINAL` apuntando al original de OneDrive y `CATALOGO` al JSON de T2
(los dos fuera del repositorio, solo leídos). Salida real:

```
plantilla completa: comprimido=60604 descomprimido=2744750 (2.62 MiB) elementos=26886 json=5257211 (5.01 MiB) filas=1000
errores (T37 bis, valores cortos): comprimido=119920 descomprimido=6357885 (6.06 MiB) elementos=148916 json=823451 (0.79 MiB) filas=1000
errores (valores de la plantilla completa): comprimido=140585 descomprimido=8574765 (8.18 MiB) elementos=148916 json=5257211 (5.01 MiB) filas=1000
original real (formato antiguo): comprimido=21726 descomprimido=64050 (0.06 MiB) elementos=1680 json=140 (0.00 MiB) filas=0
v2 de prueba (migracion sin grupos, en memoria): comprimido=41198 descomprimido=331367 (0.32 MiB) elementos=12442 json=104197 (0.10 MiB) filas=158
doble del mayor descomprimido: 17149530 -> redondeado al MiB: 17 MiB
doble del mayor JSON: 10514422 -> redondeado al MiB: 11 MiB
```

| Fichero | Comprimido | Descomprimido | Elementos | JSON del hijo |
|---|---:|---:|---:|---:|
| Plantilla completa (1000 filas, descripción de 128, detalle de 2000) | 60.604 | 2.744.750 (2,62 MiB) | 26.886 | **5.257.211** (5,01 MiB) |
| **Excel de errores más grande** (esas 1000 filas, error en las 8 columnas, VML) | 140.585 | **8.574.765** (8,18 MiB) | 148.916 | 5.257.211 |
| Excel de errores de T37 bis (valores cortos `v{i}`) | 119.920 | 6.357.885 (6,06 MiB) | 148.916 | 823.451 |
| Original real, formato antiguo (solo leído) | 21.726 | 64.050 | 1.680 | 140 |
| `v2` de prueba (la migración de la rama en memoria, sin `--grupos`) | 41.198 | 331.367 | 12.442 | 104.197 |

**Resultado** (en `lector_aislado.py`, con la medición en el comentario de cada
constante):

- `MAX_BYTES_DESCOMPRIMIDOS = 17 * 1024 * 1024` (era 20 MiB): el doble de
  8.574.765 B son 17.149.530 B, redondeado hacia arriba al MiB, **17 MiB**.
- `MAX_BYTES_RESULTADO = 11 * 1024 * 1024` (provisional en T40, 16 MiB): el
  doble de 5.257.211 B son 10.514.422 B, **11 MiB**.
- El formato antiguo real (64 KB) y el `v2` de prueba (324 KB) caben de sobra.
  El `v2` **guardado desde Excel** se mide en T29 (paso 9).

**D-T41-1 · Qué es «el Excel de errores más grande».** R16 lo describe como
«1000 filas con error en las 8 columnas, con el VML de los comentarios», sin
decir qué valores llevan. El de los tests de T37 bis (valores cortos) era el
más grande **en elementos**; en **bytes** lo es el que lleva los valores más
largos que la plantilla admite, los de la plantilla completa. Se toma ese
(8,18 MiB → 17 MiB). Con el de valores cortos saldría 13 MiB; los dos
ficheros legítimos caben con cualquiera de los dos topes, y la diferencia es
solo de margen frente a R4-1. Los tests calculan el tope a partir de los
ficheros generados, así que si el generador crece, fallan.

**Lo que no cubre el tope, dicho**: un Excel de errores sale del fichero
subido con sus valores tal cual (R63); si alguien sube textos mucho más
largos que los que admite la plantilla (un detalle de 30.000 caracteres en
cada fila, que ya es un error), su Excel de errores puede pasar de 17 MiB, o
su JSON de 11 MiB, y al volver a subirlo sería `fichero_sospechoso`. Lo mismo
un detalle de 2000 caracteres de control (cada uno, `\u00XX` en el JSON).

**Tests nuevos** (`tests/test_f036_lector_aislado.py`):
`test_f036_r16_el_tope_descomprimido_es_de_17_mib`,
`test_f036_r16_el_tope_descomprimido_es_el_doble_del_legitimo_mas_grande`,
`test_f036_r118_el_tope_del_resultado_es_de_11_mib`,
`test_f036_r118_el_tope_del_resultado_es_el_doble_del_json_mas_grande`,
`test_f036_r16_r117_los_legitimos_mas_grandes_pasan_los_pasos_baratos[…]` (×2)
y `test_f036_r118_los_legitimos_mas_grandes_se_admiten_por_el_hijo_real[…]`
(×2: el mismo `LibroLeido` que el lector en proceso). En
`tests/test_f036_excel_lector.py`, los que llevaban 20 MiB escrito a mano
pasan a la constante: la bomba de R16 y
`test_f036_r16_justo_20_mib_descomprimidos_se_admiten`, que se renombra
`test_f036_r16_justo_el_tope_descomprimido_se_admite`; y dos comprobaciones de
que los ficheros de la review 3 y de T37-1 son lo que dicen bajan su umbral
(4 → 3,5 millones de `<xf/>`; 1,5 → 1,3 millones de `<brk/>`), porque se
construyen hasta el tope vigente.

**Fase RED.** `.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q -p no:cacheprovider -k "r16 or tope_del_resultado or legitimos" --tb=line`
con los tests nuevos y los topes de T40 (20 MiB y 16 MiB):

```
E   AssertionError: assert 20971520 == 17825792
C:\...\tests\test_f036_lector_aislado.py:1109: AssertionError: assert 20971520 == 17825792
E   AssertionError: assert 16777216 == 11534336
C:\...\tests\test_f036_lector_aislado.py:1120: AssertionError: assert 16777216 == 11534336
4 failed, 4 passed, 129 deselected in 7.14s
```

(los cuatro de las constantes en rojo; los cuatro de admitir lo legítimo ya
pasaban). Con los topes nuevos, la primera pasada de
`test_f036_excel_lector.py` dio `3 failed, 335 passed`: el de «justo 20 MiB»
(ahora por encima del tope) y los dos umbrales de arriba.

**Hallazgo al medir, arreglado (H-T41-1): `openpyxl` tapa el `MemoryError`.**
En Linux, con el tope de 1 GiB y los ficheros de R4-1 a 17 MiB, dos de los tres
daban **`no_es_xlsx`** en vez de `fichero_sospechoso`: sus descriptores
(`openpyxl/descriptors/base.py`, `_convert`) capturan cualquier fallo al
construir un atributo con un `except:` desnudo y levantan `TypeError`, con el
`MemoryError` en `__context__`; el lector lo convertía en `no_es_xlsx`. Ahora
`excel_openpyxl._relanzar_si_falta_memoria` recorre la cadena del error (con
guarda de ciclos) en `_abrir` y en `_leer_libro` y, si hay un `MemoryError`,
lo vuelve a levantar: el hijo sale con su código de memoria. Tests (RED antes
del arreglo, `2 failed, 3 passed`, «DID NOT RAISE MemoryError»):
`test_f036_r118_openpyxl_tapa_el_memory_error_con_un_type_error` (fija el
comportamiento de la biblioteca),
`test_f036_r118_un_memory_error_tapado_por_openpyxl_sigue_siendo_memoria[_abrir|_extraer]`,
`…_un_error_sin_memoria_en_la_cadena_sigue_siendo_no_es_xlsx` y
`…_una_cadena_de_errores_circular_no_cuelga`.

**Para T42 y la review 5 (medido, sin tests nuevos de T42):** los ficheros de
R4-1 hasta el tope nuevo (17 MiB, 5,85 millones de rangos):

| Fichero de R4-1 a 17 MiB | Lector en proceso (Windows, sin aislar, 120 s de tope) | Lector aislado en Linux, topes de producción (30 s, 1 GiB) |
|---|---|---|
| `<dataValidation>` | 89,0 s, **admitido**, 1.391 MB | **`fichero_sospechoso`, 27,7 s** (`estado=memoria`) |
| `<conditionalFormatting>` | 75,8 s, **admitido**, 1.391 MB | **`fichero_sospechoso`, 30,2 s** (`estado=tiempo`, 30,03 s) |
| `<scenarios>` | 86,4 s, **admitido**, 1.390 MB | **`fichero_sospechoso`, 24,7 s** (`estado=memoria`) |
| Plantilla completa | — | admitida, 1000 filas, 0,35 s (`estado=ok segundos=0.28`) |
| Excel de errores más grande | — | admitido, 1000 filas, 1,09 s (`estado=ok segundos=0.96`) |

(Linux: el contenedor `python` 3.12.14 local con `--network none --memory 2g`,
el código y las dependencias puras copiados dentro; el estado sale de la línea de log del lector (`lector_aislado: estado=… tope_memoria_aplicado=True`); en otra pasada, 23,8 s, 30,2 s y 20,9 s. Antes del arreglo de
H-T41-1 la columna decía `no_es_xlsx` en 22,4 s y 22,6 s para validación y
escenarios.) El tope descomprimido más bajo **no** basta por sí solo: a 17 MiB
la biblioteca sigue tardando 76–89 s; lo que corta es el hijo.

Y H-T40-1 con el tope nuevo: el pico del padre en el recuento de R117 con un
fichero de R4-1 de 17 MiB es **80,8 MiB** (`tracemalloc`; *expat* dobla su
búfer hasta 32 MiB para una etiqueta de 17 MiB).

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tras T41 (con los retoques de *lint* del último commit en el árbol): raíz **62 passed** (4,76 s); servicio `api` **6288 passed, 68 skipped**, ejecutado de verdad (el árbol cambió); `front` en verde (caché). `ENTORNO LISTO`. La suite del `api` entera, aparte: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api` → **6288 passed, 68 skipped in 266.38s**. El *skip* nuevo es el de Linux de R119 (comprobado a mano en un contenedor, T40) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.8% de 3180 líneas cambiadas cubiertas (3175/3180, umbral 80%, nivel critico)` |
| Mutación | No toca en este encargo: la campaña de lo que cambia en producción desde `b8c51e1` es **T43** (`progress/mutacion_F-036_bloque10quinquies.md`). Lo del hijo que solo corre en otro proceso está cubierto por tests en este proceso (`_principal_hijo`, `_aplicar_tope_de_memoria`, `leer_en_hijo`), para que la campaña pueda matar sus mutantes |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **606,34 s**; aparte, sin cobertura: **266,38 s**; `tests/test_f036_lector_aislado.py` solo, ~19 s (los hijos de verdad: 3,7–4,0 s cada fichero de R4-1, el resto < 1,5 s) |
| *Lint* | `ruff` en la raíz: 71 avisos (eran 69). Los 2 nuevos son `I001` de `lector_aislado.py` y `test_f036_lector_aislado.py` con la configuración de la raíz, que trata `domain`/`infrastructure` como de terceros; con la del servicio (`services/postventa-api`) esos dos ficheros están limpios, y no se pueden contentar las dos a la vez |
| R4-1 | Lector de HEAD: 108–109 s, admitido, 1,6 GB (20 MiB); en proceso a 17 MiB, 76–89 s, admitido, 1,39 GB → aislado en Linux con los topes de producción: **`fichero_sospechoso` en 24,7–30,2 s**; en la suite (Windows, tope inyectado de 3 s): 3,7–4,0 s |

### Qué queda fuera y qué falta

- **Siguiente: T42–T44** (otro encargo): los ficheros hostiles de todas las
  reviews por el lector aislado (los constructores de R4-1 ya están en
  `tests/test_f036_lector_aislado.py`, `_de_r4_1`), la campaña de mutación con
  `--base b8c51e1` y la documentación (`docs/ARCHITECTURE.md`,
  `docs/INTEGRACION.md` y su copia en `azure-apps`). Ningún documento citaba
  los 20 MiB (comprobado con `grep`).
- **Decisiones para la review 5 / el spec-author**: H-T40-1 (memoria del padre
  en el recuento de R117: 80,8 MiB con un elemento de 17 MiB), D-T41-1 (qué
  Excel de errores fija el tope: 17 MiB con valores largos, 13 MiB con cortos)
  y D-T40-4 (filas ≤ 1001).
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 (MANUALES) y T30**: sin tocar. T29 paso 8 bis comprueba en Azure
  que el tope de memoria se aplica (la línea `lector_aislado: … 
  tope_memoria_aplicado=True` del log) y que `forkserver` arranca en Flex
  Consumption; paso 9, el `v2` guardado desde Excel frente al presupuesto y al
  tope de 17 MiB.
- Nada en segundo plano: los contenedores de Docker se lanzaron con `--rm` y
  los guiones de medida viven fuera del repositorio.

## T42–T44 · 2026-10-01 · BLOQUEADO antes de empezar T42 (H-T40-1 incumple la letra de la spec); T16 sigue siendo MANUAL del humano y está PENDIENTE

El encargo del líder: medir H-T40-1 y, si la spec exige que el padre no crezca
más allá del «resultado acotado» y la medición lo incumple, parar. Lo exige y lo
incumple. **No se ha escrito código ni tests de T42; T43 y T44 no se han
empezado.** Rama `feature/F-036-importar-excel`, F-036 marcada `blocked` en
`harness/features.json`.

### Lo que dice la spec

- `design.md` §5.2, octava enmienda (línea ~1069): «el padre solo crece lo que
  mide el resultado acotado (`MAX_BYTES_RESULTADO`)».
- `design.md` §5.2, «Cómo se prueba» (línea ~1433): «la memoria del padre
  (`tracemalloc` en el padre) no crece más allá del resultado acotado».
- `tasks.md` T42: «sin que crezca la memoria del padre más allá del resultado
  acotado (`tracemalloc` en el padre)».
- R118: «sin que crezca la memoria del padre».

`MAX_BYTES_RESULTADO` = 11 MiB (T41). Y R117 (el recuento) corre en el padre
por R118 («las comprobaciones baratas … van antes, en el proceso padre»): no se
puede mover sin enmienda.

### La medición

Guion del directorio temporal (`medir_padre_t42.py`, no versionado): cada
fichero por `LectorPlantillaAislado(entorno="test").leer`, con `tracemalloc`
arrancado en el padre justo antes; primero con un doble del ejecutor que
devuelve `tiempo` (aísla lo que gasta el padre), después con el hijo de verdad y
un tope inyectado de 3 s. Topes vigentes: descomprimido 17 MiB, resultado
11 MiB. Comando, desde `services/postventa-api`:
`.venv/Scripts/python.exe <tmp>/medir_padre_t42.py`. Salida real:

```
MAX_BYTES_RESULTADO 11.0 MiB; MAX_BYTES_DESCOMPRIMIDOS 17.0 MiB
R4-1 validacion                          doble         51358 B -> fichero_sospechoso     0.24 s  pico padre   80.8 MiB
R4-1 formato-condicional                 doble         51100 B -> fichero_sospechoso     0.21 s  pico padre   80.8 MiB
R4-1 escenario                           doble         51071 B -> fichero_sospechoso     0.21 s  pico padre   80.8 MiB
review 3 xf-en-estilos                   doble         59062 B -> fichero_sospechoso     0.85 s  pico padre    0.7 MiB
review 3 validacion                      doble         76531 B -> fichero_sospechoso     1.81 s  pico padre    0.6 MiB
review 3 salto-de-fila                   doble         68346 B -> fichero_sospechoso     1.33 s  pico padre    0.5 MiB
review 3 combinado                       doble         76522 B -> fichero_sospechoso     1.71 s  pico padre    0.6 MiB
review 3 celda-con-estilo-fila-1200      doble         76400 B -> fichero_sospechoso     1.39 s  pico padre    0.6 MiB
review 3 formato-condicional             doble         93576 B -> fichero_sospechoso     1.12 s  pico padre    0.6 MiB
review 3 hipervinculo                    doble         76821 B -> fichero_sospechoso     1.26 s  pico padre    0.6 MiB
T37-1 sheet1.dat                         doble         68353 B -> fichero_sospechoso     0.86 s  pico padre    0.5 MiB
R4-1 validacion                          hijo real     51358 B -> fichero_sospechoso     3.28 s  pico padre   80.8 MiB
R4-1 formato-condicional                 hijo real     51100 B -> fichero_sospechoso     3.31 s  pico padre   80.8 MiB
R4-1 escenario                           hijo real     51071 B -> fichero_sospechoso     3.37 s  pico padre   80.8 MiB
```

(Los tiempos de los de la review 3 van inflados por `tracemalloc`; sin él son
< 1 s, T37/T38.)

| Fichero | Pico en el padre | Frente al resultado acotado (11 MiB) |
|---|---:|---|
| Los tres de R4-1 (un elemento con un `sqref` de 17 MiB) | **80,8 MiB** | **7,3 veces**: incumple |
| Los siete de la review 3 y el `sheet1.dat` de T37-1 (millones de elementos pequeños) | 0,5–0,7 MiB | cumple |

El pico es **el mismo con el doble que con el hijo real**: todo sale del paso 2
bis (R117), no del hijo ni del canal. Es *expat* guardando la etiqueta de
apertura entera, con sus atributos, antes de llamar al manejador (dobla su búfer
hasta 32 MiB para una etiqueta de 17 MiB) más la copia a `str` de `pyexpat`
(H-T40-1). Lo acota el tope descomprimido (~4,75 veces), no el resultado.
Los ficheros de la review 1 (celda en la fila 1.048.576) y de la review 2
(rangos combinados, hipervínculo y comentario sobre rango) no se han medido aquí:
son, como los de la review 3, elementos pequeños, sin atributos de megas.

### Qué tiene que decidir el líder (o el spec-author)

1. **Aceptarlo y enmendar la letra**: el padre crece como mucho el resultado
   acotado **más** lo que cuesta el recuento de R117, acotado por el tope
   descomprimido (hoy ~81 MiB, ~5 veces el tope). Es lo que ya admite el test de
   T39/T40 (`VECES_EL_TOPE_EN_EL_RECUENTO = 5`). Cabe en las cuentas de §5.2
   (2.048 MB de instancia), pero no es lo que dice la spec.
2. **Un tope de tamaño por etiqueta en el recuento** (lo que H-T40-1 dejó
   apuntado): rechazar `fichero_sospechoso` en cuanto una etiqueta de apertura
   pase de N bytes, **antes** de dársela a *expat*. Cambia la producción del
   paso 2 bis (R117) y pide medir el N legítimo (la etiqueta más larga de la
   plantilla completa y del Excel de errores más grande).
3. **Mover el recuento al hijo**: contradice R118 («van antes, en el proceso
   padre») y quita la primera línea barata; no se recomienda.

Hasta que se decida, T42 no se puede escribir: su aserto de memoria es
justamente ese.

### Estado

- Código y tests: **sin cambios** respecto a `4a6a40b`. `bash harness/init.sh`
  no se ha vuelto a ejecutar (no hay cambio de código); el último verde es el de
  T41 (cifras en «T39–T41», Evidencias).
- `harness/features.json`: F-036 `blocked`; `BACKLOG.md` regenerado.
- T42, T43 y T44 siguen `[ ]`. T16 (MANUAL del humano) sigue PENDIENTE.

## T42–T44 · 2026-10-01 · hecho; siguiente: review 5. T16 sigue siendo MANUAL del humano y está PENDIENTE

Encargo: T42 (los ficheros hostiles de todas las reviews por el lector
aislado), T43 (campaña de mutación con `--base b8c51e1` y mutaciones de orden
a mano) y T44 (documentación hacia fuera). Se paró antes de T42 por H-T40-1
(arriba, «T42–T44 · BLOQUEADO»); el líder eligió la opción (1) y el
spec-author la escribió en la octava enmienda bis (`52689e7`): el pico del
padre, por debajo de un tope fijo de `6 * MAX_BYTES_DESCOMPRIMIDOS` (102 MiB).

Commits: T42 `c06709d`; T44 `634fa1c` (y `8f3be7f` en `azure-apps`); T43
`64b59c8`, `f356b91` y `e360e90` (tests que cierran lo que encontró la
mutación) y `4601799` (el informe de la campaña). T44 va antes que la campaña de
T43 a propósito: la campaña corre sobre lo commiteado de la rama, y así mide
también los tests de documentación que leen los topes del código.

### T42 · Los ficheros hostiles de todas las reviews, por el lector aislado

**Qué cambió** (`tests/test_f036_lector_aislado.py`, sin código de producción):

- Un catálogo, `HOSTILES`, con los **16** ficheros de las reviews 1 a 4 y de
  T37-1, cada uno con su constructor (los de los tests de siempre:
  `_con_celda`, `_con_rango`, `_de_la_review_3`, `_hoja_en_un_dat`,
  `_de_r4_1`, y uno nuevo, `_con_comentario_sobre_rango`) y **dónde debe
  pararlo** el lector aislado:

  | Fichero | Destino |
  |---|---|
  | Review 1: celda con estilo en la fila 1.048.576 | `SE_LEE_IGUAL` |
  | Review 2: combinado `A1003:A1048576`, combinado e hipervínculo `A1003:H1048576` | `SE_LEE_IGUAL` (×3) |
  | Review 3: comentario con `ref` `A1003:H1048576` en `Instrucciones` | `SE_LEE_IGUAL` |
  | Review 3 (R3-1): los siete elementos repetidos hasta el tope descomprimido | `EN_EL_PADRE` (×7) |
  | T37-1: «Incidencias» en `sheet1.dat` con 1,6 millones de `<brk/>` | `EN_EL_PADRE` |
  | Review 4 (R4-1): `sqref` de millones de rangos en validación, formato condicional y escenarios | `EN_EL_HIJO` (×3) |

- `test_f036_r118_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado[…]`
  (×16, suite normal): por `LectorPlantillaAislado` con el **hijo de verdad**
  (envuelto en un espía que guarda cada salida) y el tope inyectado de 3 s;
  `load_workbook` **revienta en el padre** durante la lectura (el hijo, otro
  proceso, no lo hereda). Comprueba: el destino (`EN_EL_PADRE`:
  `fichero_sospechoso` y el ejecutor **sin llamar**; `EN_EL_HIJO`:
  `fichero_sospechoso` con el hijo en `tiempo` o `memoria`; `SE_LEE_IGUAL`:
  el mismo `LibroLeido` que el lector en proceso, hijo en `ok`), el tiempo
  (< 3 s + 10 s de arranque) y el **pico de `tracemalloc` del padre por debajo
  de `TOPE_DEL_PICO_DEL_PADRE` = 102 MiB**.
- `test_f036_r118_los_de_r4_1_con_los_topes_de_produccion[…]` (×3): los de
  R4-1 con los topes de producción (30 s, 1 GiB), **marcados como lentos**:
  solo corren con `POSTVENTA_TESTS_LENTOS=1` (`skipif`), porque cada uno cuesta
  30 s en Windows.
- `test_f036_r118_el_tope_del_pico_del_padre_es_de_102_mib` (el número fijo,
  y que cubre resultado + 5 veces el tope descomprimido),
  `…_estan_los_hostiles_de_todas_las_reviews` (16: 8 en el padre, 3 en el hijo,
  5 se leen igual) y `…_el_comentario_de_la_review_3_es_lo_que_dice_ser`.
- Lo legítimo ya lo fijaba T41
  (`test_f036_r118_los_legitimos_mas_grandes_se_admiten_por_el_hijo_real`, el
  mismo `LibroLeido` que en proceso); no se duplica.
- El test de T39 de los ficheros de R4-1 con 3 s
  (`…_los_ficheros_de_r4_1_los_para_el_hijo_a_tiempo_y_sin_memoria_del_padre`)
  **queda dentro** del de los 16 (los tres `r4-1-…`), con el tope fijo en vez
  del cálculo de T40 (`MAX_BYTES_RESULTADO + 5 × MAX_BYTES_DESCOMPRIMIDOS +
  margen`). Se retira para no lanzar dos veces cada hijo de 3 s.

**D-T42-1 · «Se rechaza» no vale para los de las reviews 1 y 2 ni para el
comentario.** `tasks.md` dice «cada uno se rechaza a tiempo». Esos cinco ya no
son hostiles desde R115 (solo lectura): la plantilla con ellos **se lee igual
que sin ellos** y entra, y así lo fijan los tests de R115
(`…_se_lee_en_menos_de_un_segundo`, `_misma_lectura`). Rechazarlos rompería
R115, que la octava enmienda mantiene. Para ellos T42 comprueba lo mismo que
para el resto —a tiempo, padre por debajo del tope, el padre no abre el
libro— y que el resultado es el del lector en proceso. No es una desviación
de comportamiento: es la lectura de «rechazar» que no contradice R115.

**La medición** (guion del directorio temporal `tabla_t42.py`; cada fichero
por el lector aislado con el espía y 3 s; Windows, `spawn`, sin tope de
memoria; la plantilla completa y el Excel de errores, con los 30 s de
producción):

| Fichero | Bytes | Resultado | Hijo | Segundos | Pico del padre |
|---|---:|---|---|---:|---:|
| review-1 celda en la fila 1.048.576 | 33.381 | leído (2 filas) | `ok` | 0,85 | 0,5 MiB |
| review-3 comentario sobre rango | 34.680 | leído (2 filas) | `ok` | 0,82 | 0,5 MiB |
| review-2 combinado A | 33.396 | leído (2 filas) | `ok` | 0,90 | 0,5 MiB |
| review-2 combinado A-H | 33.396 | leído (2 filas) | `ok` | 0,84 | 0,5 MiB |
| review-2 hipervínculo A-H | 33.436 | leído (2 filas) | `ok` | 0,87 | 0,5 MiB |
| T37-1 hoja en un `.dat` | 68.349 | `fichero_sospechoso` | — | 0,95 | 0,5 MiB |
| review-3 `xf` en estilos | 59.058 | `fichero_sospechoso` | — | 0,59 | 0,7 MiB |
| review-3 validación | 76.527 | `fichero_sospechoso` | — | 1,38 | 0,6 MiB |
| review-3 salto de fila | 68.342 | `fichero_sospechoso` | — | 1,28 | 0,5 MiB |
| review-3 combinado | 76.518 | `fichero_sospechoso` | — | 1,27 | 0,6 MiB |
| review-3 celda con estilo en la fila 1200 | 76.397 | `fichero_sospechoso` | — | 1,03 | 0,6 MiB |
| review-3 formato condicional | 93.573 | `fichero_sospechoso` | — | 1,07 | 0,6 MiB |
| review-3 hipervínculo | 76.818 | `fichero_sospechoso` | — | 1,20 | 0,6 MiB |
| R4-1 validación | 51.360 | `fichero_sospechoso` | `tiempo` | 3,17 | **80,8 MiB** |
| R4-1 formato condicional | 51.101 | `fichero_sospechoso` | `tiempo` | 3,21 | **80,8 MiB** |
| R4-1 escenarios | 51.073 | `fichero_sospechoso` | `tiempo` | 3,19 | **80,8 MiB** |
| Plantilla completa (legítima) | 60.603 | leído (1000 filas) | `ok` | 1,25 | 17,3 MiB |
| Excel de errores más grande (legítimo) | 140.585 | leído (1000 filas) | `ok` | 1,69 | 17,6 MiB |

(Los tiempos del padre van con `tracemalloc` encendido, que encarece el
recuento de R117; sin él, < 1 s, lo fijan los tests de R117 en un subproceso.)

**Con los topes de producción**, `POSTVENTA_TESTS_LENTOS=1 .venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q -p no:cacheprovider -k "topes_de_produccion" --log-level=INFO -rA`:

```
INFO     ...lector_aislado: estado=tiempo segundos=30.00 tope_memoria_aplicado=False
INFO     ...lector_aislado: estado=tiempo segundos=30.02 tope_memoria_aplicado=False
INFO     ...lector_aislado: estado=tiempo segundos=30.02 tope_memoria_aplicado=False
30.63s call     tests/test_f036_lector_aislado.py::test_f036_r118_los_de_r4_1_con_los_topes_de_produccion[validacion]
30.62s call     tests/test_f036_lector_aislado.py::test_f036_r118_los_de_r4_1_con_los_topes_de_produccion[escenario]
30.58s call     tests/test_f036_lector_aislado.py::test_f036_r118_los_de_r4_1_con_los_topes_de_produccion[formato-condicional]
5 passed, 156 deselected in 92.25s (0:01:32)
```

(En Windows no hay tope de memoria, así que los para el reloj; en Linux, T41
midió `memoria` o `tiempo` en 24,7–30,2 s.)

**Fase RED.** T42 no añade código de producción: verifica el de T40, cuya fase
RED (y la de R4-1, T39) está arriba. Lo que se demuestra aquí es que **los
tests nuevos muerden**: en una copia desechable de `git archive HEAD` con el
fichero de tests nuevo, se rompe a mano el lector aislado y se pasa
`tests/test_f036_lector_aislado.py -k hostiles` (guion `mutar.py` del
directorio temporal). Primero, sin romper nada: `17 passed, 144 deselected in
39.42s`. Después:

```
== padre-lee: rc=1 :: 8 failed, 9 passed, 144 deselected in 19.37s
    E   AssertionError: assert 'no_es_xlsx' == 'fichero_sospechoso'
    (los cinco que se leen igual y los tres de R4-1: el padre abre el libro y `load_workbook` revienta)
== padre-abre: rc=1 :: 8 failed, 9 passed, 144 deselected in 28.72s
== sin-recuento: rc=1 :: 8 failed, 9 passed, 144 deselected in 45.10s
    E   AssertionError: assert [SalidaHijo(e...segundos=3.0)] == []
    (los siete de la review 3 y el `.dat` llegan al hijo)
== recuento-tras-hijo: rc=1 :: 8 failed, 9 passed, 144 deselected in 61.32s (0:01:01)
```

`padre-lee` sustituye la llamada al ejecutor por `leer_en_hijo(contenido)` en
el padre; `padre-abre` llama a `excel_openpyxl._abrir` en el padre antes del
hijo; `sin-recuento` quita `_contar_elementos_xml`; `recuento-tras-hijo` lo
mueve detrás del ejecutor.

**Verde.** `.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py -q -p no:cacheprovider`
→ **359 passed, 4 skipped in 134.62s** (los 3 lentos y el de Linux).

### T43 · Mutación con `--base b8c51e1` y mutaciones de orden

**Alcance**: 6 ficheros de producción, 893 líneas, **96 mutantes**
(`errores.py` 0, `function_app.py` 1, `ejecutor_aislado.py` 21,
`excel_openpyxl.py` 2, `lector_aislado.py` 72, `importar.py` 0).

**Mutación rápida previa** (orientativa; guion `mutacion_rapida.py` del
directorio temporal: cada mutante en una copia desechable contra
`test_f036_lector_aislado.py`, `test_f036_arquitectura.py`,
`test_f036_importar_http.py` y `test_f036_excel_lector.py`, 6 copias en
paralelo). Se cortó a mano a los ~55 min, con los mutantes 1–56 juzgados (los
57–96 salieron «muertos en 0 s» al cortar, que no vale: se juzgan aparte y en
la campaña). **8 vivos, todos en `ejecutor_aislado.py`**:

| Vivo | Por qué ningún test lo cazaba | Cerrado con |
|---|---|---|
| `:45` `CODIGO_SALIDA_MEMORIA = 77 → 78` | Los tests usan la constante en los dos lados | `…_el_codigo_de_salida_de_memoria_es_77` (es el contrato hijo–padre y lo que se ve en el sistema) |
| `:62` `@dataclass(frozen=True) → False` (`SalidaHijo`) | Nadie intentaba cambiarla | `…_la_salida_del_hijo_no_se_puede_cambiar` |
| `:97` `setrlimit and RLIMIT_AS → or` | En Windows `resource` no existe; en Linux están los dos | `…_con_resource_a_medias_no_hay_tope_de_memoria` |
| `:156` `restante > 0 → >= 0` | Un reloj justo en el límite no se daba nunca | `…_al_llegar_justo_al_tope_es_tiempo_aunque_haya_algo_en_el_canal` (reloj doblado en el módulo) |
| `:206` `Pipe(duplex=False) → True` | Un canal de dos sentidos funciona igual | `…_el_canal_va_solo_del_hijo_al_padre_y_el_hijo_es_daemon` (contexto espía) |
| `:210` `daemon=True → False` | Solo se nota si muere el padre | el mismo |
| `:219` `_recibir(…, 1) → 2` (la bandera) | El hijo siempre manda un byte | `…_la_bandera_del_hijo_se_lee_con_tope_de_un_byte` |
| `:234` `_acabar(…, … else 0) → else 1` | Esperar un segundo de más no rompía nada | `…_al_acabar_se_espera_al_hijo_solo_si_fue_bien[…]` |

Comprobación de los cierres (guion `comprobar_cierres.py`: cada mutante
aplicado en una copia de HEAD con los tests nuevos, pasando solo los
seleccionados): los 8 **MUERTO**, cada uno por su test, y los dos del 57–58
(`ULTIMA_FILA_LEIDA = MAX_FILAS ∓ …`) **MUERTO** por los de T40
(`…_las_filas_de_la_2_a_la_1002_se_admiten`, `…_filas_de_mas_…[hasta-la-1003]`).

**Mutaciones de orden, a mano** (guion `mutar.py`, copia desechable de `git
archive HEAD`, sin bytecode, pasando `test_f036_lector_aislado.py`,
`test_f036_arquitectura.py` y `test_f036_importar_http.py`). La primera pasada,
con los tests de antes, dejó **vivas las tres del final del hijo** —ningún test
miraba `kill`, `terminate` ni `join`, porque en Windows `terminate` ya mata—:

```
== sin-kill: rc=0 :: 236 passed, 4 skipped in 62.09s (0:01:02)
== sin-terminate: rc=0 :: 236 passed, 4 skipped in 66.66s (0:01:06)
== sin-join: rc=0 :: 236 passed, 4 skipped in 63.39s (0:01:03)
```

Cerradas con `…_al_acabar_terminate_kill_si_sigue_vivo_y_join_siempre[…]`
(×3, un doble del hijo que muere con `terminate`, solo con `kill` o ya había
acabado: la secuencia exacta `join(0)`, `terminate`, `join(1)`, `kill`,
`join()`), y en Linux, `…_ejecutor_real_un_hijo_que_ignora_terminate_muere_con_kill`
(un hijo que ignora `SIGTERM`, `tests/hijos_f036.py:ignora_terminate`;
`skipif` fuera de Linux). Comprobado en el contenedor `python` 3.12 local
(`--network none --rm`, solo `ejecutor_aislado.py` y `hijos_f036.py`):
`metodo: forkserver` / `ignora SIGTERM, tope 1 s -> tiempo en 2.013 s; hijos
vivos: []` (1 s de tope, 1 s esperando a `terminate` y `kill`).

Segunda pasada, las nueve:

| Mutación | Qué hace | Resultado |
|---|---|---|
| `sin-kill` | `proceso.kill()` → `pass` | **Cae**: 1 failed |
| `sin-terminate` | sin `proceso.terminate()` | **Cae**: 2 failed |
| `sin-join` | sin el `proceso.join()` final | **Cae**: 3 failed |
| `padre-lee` | el padre se salta el ejecutor y lee con `leer_en_hijo` | **Cae**: 79 failed |
| `padre-abre` | el padre llama a `_abrir` antes del hijo | **Cae**: 10 failed |
| `sin-recuento` | sin `_contar_elementos_xml` | **Cae**: 13 failed |
| `recuento-tras-hijo` | el recuento, después del ejecutor | **Cae**: 11 failed |
| `zip-tras-hijo` | `_inspeccionar_zip`, después del ejecutor | **Cae**: 4 failed |
| `tamano-tras-hijo` | `_comprobar_tamano`, después del ejecutor | **Cae**: 1 failed |

**La campaña** (`python -m harness.mutacion --feature F-036 --base b8c51e1 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque10quinquies.md`, desde la raíz):

Una primera tanda con `timeout 10800` se paró a mano a los ~15 min (6 de 96
juzgados, todos muertos): a ese ritmo, con otra suite de otro proyecto
corriendo en la misma máquina, no cabía en las 3 h. Se limpiaron sus procesos y
sus seis *worktrees* (`git worktree remove --force`, `git worktree prune`) y se
relanzó, sobre `f356b91`, con `timeout 18000` por fuera. Salida real:

```
96 mutantes evaluados, 92 muertos, 4 supervivientes, 0 timeouts en 5855.5 s
Informe: progress/mutacion_F-036_bloque10quinquies.md
```

Los 4 supervivientes, todos en `lector_aislado.py`, cerrados con tests nuevos
(`e360e90`) y **comprobados aplicando cada mutante a mano** en una copia de
HEAD (guion `comprobar_cierres.py`, por descripción del mutante):

| Superviviente | Por qué vivía | Cerrado con | Comprobación |
|---|---|---|---|
| `:281` `ensure_ascii=False → True` | `json.loads` lee igual la «ñ» tal cual que escapada; la plantilla completa de T41 es ASCII | `…_el_json_del_hijo_lleva_el_texto_en_utf_8_sin_escapar`: el tope de 11 MiB se midió en UTF-8 y escapar las tildes multiplica el tamaño | MUERTO (1 failed) |
| `:354` `- PRIMERA_FILA_LEIDA → +` | La comprobación por fila (creciente, de 2 a 1002) rechaza igual una lista de más; solo cambia el coste | `…_mas_de_1001_filas_se_rechazan_sin_mirar_ninguna` (espía de `_diccionario`) | MUERTO (1 failed) |
| `:354` `+ 1 → + 2` | Lo mismo | el mismo | MUERTO (1 failed) |
| `:451` `_AVISO_DADO = False → True` | El test del aviso lo ponía a `False` con `monkeypatch`: el valor de arranque no lo miraba nadie | `…_el_primer_lector_sin_tope_del_proceso_avisa` (intérprete limpio) | MUERTO (1 failed) |

Con eso, **0 supervivientes sin cerrar** y **0 equivalentes**. El análisis de
cada uno está escrito en el informe de la campaña; no se ha relanzado la
campaña entera (97,6 min) tras los cierres. Los 8 de la mutación rápida
también los mató la campaña (con los tests de `64b59c8`). Nada quedó en
segundo plano: ni procesos de la campaña ni *worktrees* (`git worktree list`
solo enseña el árbol principal y uno de otro agente, ajeno a este encargo).

### T44 · Documentación

**Qué cambió:**

- `docs/ARCHITECTURE.md`, «Entrada de incidencias (F-036)»: el paso 2 de la
  importación dice que `openpyxl` abre el fichero en un proceso hijo; sección
  nueva **«La lectura aislada en un proceso hijo (R118–R120)»** (por qué, la
  tabla de qué corre dónde con sus topes y su respuesta, JSON y no `pickle`,
  `forkserver`/`spawn` y `setrlimit`, el 503 sin tope en `dev`/`pro`, una
  lectura a la vez y su 503, la memoria del padre —resultado más recuento, por
  debajo de 102 MiB— y del hijo, los 2.048 MB, el tiempo frente al presupuesto
  de 45 s, y que la migración sigue en proceso); y «Dónde vive cada pieza»
  nombra `lector_aislado.py` y `ejecutor_aislado.py`.
- `docs/INTEGRACION.md`: cabecera a 2026-10-01; §6 «Qué se rompe si alguien
  toca algo», **cuatro filas**: bajar la memoria de la instancia (hoy 2.048 MB,
  el valor por defecto de Flex Consumption: el despliegue no pasa
  `--instance-memory`; D-31), subir la concurrencia por instancia o
  `FUNCTIONS_WORKER_PROCESS_COUNT` (el semáforo es por proceso), dos
  importaciones a la vez (503) y un despliegue sin `setrlimit` con `ENTORNO`
  en `dev`/`pro` (503); §8, la fila de `POST /api/importaciones` dice la
  lectura en el hijo y los 503.
- `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`:
  cabecera (commit `634fa1c`, 2026-10-01), un recuadro nuevo «LO QUE CAMBIA EN
  ESTA REVISIÓN (2026-10-01, F-036)» (el de 2026-09-30 pasa a «LO QUE CAMBIÓ»),
  y las mismas filas de §6 y la misma de §8, copiadas del origen. Commit
  **local** `8f3be7f` en `azure-apps`, con `git add` solo de ese fichero; sin
  push. (`git status` de `azure-apps` estaba limpio al empezar: el
  `dedicacion.md` modificado que avisaba el líder ya no aparecía.)
- `tests/test_f036_documentacion.py`: `FECHA` pasa a 2026-10-01 y **siete
  tests nuevos** (`test_f036_t44_…`): los topes que escribe la arquitectura se
  **leen del código** (`SEGUNDOS_HIJO`, `BYTES_MEMORIA_HIJO`,
  `MAX_BYTES_DESCOMPRIMIDOS`, `MAX_BYTES_RESULTADO`,
  `PRESUPUESTO_ELEMENTOS_XML`, `SEGUNDOS_ESPERA_LECTURA`) y un control fija lo
  que leen; la sección va dentro de la entrada; lo que describe (proceso hijo,
  el padre no abre el libro, JSON, `forkserver`, `spawn`, `setrlimit(RLIMIT_AS)`,
  los dos 503 por su nombre, una lectura a la vez, 2.048 MB, 102 MiB, el
  enlace a §6); los dos módulos nuevos; §6 (las cuatro filas, sin valores:
  pasa `hallazgos` de `test_f005`); y la fila de §8.

**Observación (no tocada)**: la copia de `azure-apps` ya divergía de
`docs/INTEGRACION.md` antes de este trabajo en tres sitios ajenos a F-036 (el
recuadro de las ventanas abiertas del 2026-09-23 en §3, la nota de
`CIERRE_HABILITADO` «en el código» de §3 bis y la fila de la rotación de la
clave de `sigrid-api` en §6). No se han tocado: solo se han portado los
cambios de T44.

**Fase RED.** Con los tests nuevos y los documentos de antes (`git stash push
docs/ARCHITECTURE.md docs/INTEGRACION.md`), `.venv/Scripts/python.exe -m pytest tests/test_f036_documentacion.py -q -p no:cacheprovider --tb=line`:

```
E   AssertionError: §6 no dice «Baja la memoria de la instancia»
E   AssertionError: assert 'proceso hijo' in '| POST /api/importaciones | F-036 · importa a la bandeja un Excel ... Nada en Sigrid |'
FAILED tests/test_f036_documentacion.py::test_f036_r60_la_cabecera_dice_que_f036_lo_toco_y_cuando
FAILED tests/test_f036_documentacion.py::test_f036_t44_la_arquitectura_nombra_los_modulos_nuevos
FAILED tests/test_f036_documentacion.py::test_f036_t44_integracion_dice_que_rompe_la_importacion
FAILED tests/test_f036_documentacion.py::test_f036_t44_la_fila_de_importaciones_dice_la_lectura_aislada
ERROR tests/test_f036_documentacion.py::test_f036_t44_la_lectura_aislada_va_dentro_de_la_entrada
ERROR tests/test_f036_documentacion.py::test_f036_t44_la_arquitectura_dice_los_topes_de_la_lectura_aislada
ERROR tests/test_f036_documentacion.py::test_f036_t44_la_arquitectura_describe_la_lectura_aislada
4 failed, 68 passed, 3 errors in 0.82s
```

(los tres `ERROR` son la fixture, que no encuentra la sección). **Verde**:
`pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py tests/test_f005_integracion_sin_secretos.py tests/test_f006_repo_sin_identificadores.py`
→ **153 passed in 12.71s**; todos los de documentación
(`tests/test_f0*_documentacion.py tests/test_f010_integracion_expuesto.py`)
→ **342 passed in 3.20s**.

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tal cual, tras el último commit de código (`4601799`): raíz **62 passed** (6,17 s); servicio `api` **6325 passed, 72 skipped**, ejecutado de verdad; `front` en verde (caché). `ENTORNO LISTO. Puedes trabajar.` La suite del `api` entera, aparte: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` en `services/postventa-api` → **6325 passed, 72 skipped in 344.05s**. Frente a T41 (6288 + 68): +37 en verde y +4 saltados (los 3 lentos de R4-1 con los topes de producción y el de Linux del hijo que ignora `SIGTERM`) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 3180 líneas cambiadas cubiertas (3176/3180, umbral 80%, nivel critico)` |
| Mutación | `progress/mutacion_F-036_bloque10quinquies.md`: **96 generados, 92 muertos, 4 supervivientes, 0 timeouts** en 5855,5 s con 6 workers; los 4, cerrados con tests (`e360e90`) y comprobados a mano: **0 sin cerrar, 0 equivalentes**. Mutaciones de orden de la review 5: **9 de 9 caen** (las tres del final del hijo, después de cerrarlas con tests) |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **857,20 s** (con otra suite de otro proyecto corriendo a la vez en la máquina); aparte, sin cobertura: **344,05 s**. `tests/test_f036_lector_aislado.py` solo: ~80 s (los 16 hostiles con el hijo de verdad, ~40 s) |
| *Lint* | `ruff` en la raíz: **71 avisos**, los mismos que en T41; los ficheros tocados, limpios con la configuración del servicio |
| Memoria del padre (H-T40-1) | 80,8 MiB con los de R4-1 (por debajo del tope fijo de 102 MiB); 0,5–0,7 MiB con el resto de hostiles; 17,3–17,6 MiB con lo legítimo más grande |

### Qué queda fuera y qué falta

- **Siguiente: review 5.** Para el reviewer: D-T42-1 (los cinco ficheros de
  las reviews 1 y 2 y el comentario **se leen igual** y entran, no se
  rechazan: R115), que el test de T39 queda dentro del de los 16, que la
  campaña no se relanzó tras cerrar los 4 supervivientes (comprobados uno a
  uno), y las tres divergencias previas de la copia de `azure-apps` (no
  tocadas).
- **Sin comprobar en esta máquina, solo en Linux**: el test
  `…_ejecutor_real_un_hijo_que_ignora_terminate_muere_con_kill` se salta en
  Windows; lo mismo se comprobó a mano en el contenedor (`tiempo en 2.013 s`,
  ningún hijo vivo).
- **Los tests lentos** (`POSTVENTA_TESTS_LENTOS=1`) no corren en `init.sh` ni
  en la mutación; se lanzaron una vez a mano (arriba, 92 s).
- **T16 · MANUAL del humano, PENDIENTE**: con Docker Desktop, desde la raíz,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`;
  debe pasar `tests_bbdd/tests/test_f036_bbdd_bandeja.py`.
- **T27–T29 (MANUALES) y T30**: sin tocar. T29 comprueba en Azure que el tope
  de memoria se aplica (`tope_memoria_aplicado=True` en el log), que
  `forkserver` arranca en Flex Consumption y que la instancia es de 2.048 MB
  (D-31).
- `git push` no se ha hecho en ninguno de los dos repositorios.

## Bloque 11 (T45–T49) · 2026-10-01 · hecho; siguiente: review 6. T16 y T27–T29 siguen siendo MANUAL del humano; T30 la lanza el líder

Arreglos de la review 5 (novena enmienda de la spec). Solo T45 toca código de
producción, y solo `infrastructure/documentos/ejecutor_aislado.py`.

| Tarea | Commit | Qué |
|---|---|---|
| T45 (RED) | `71cbba7` | Los tests del tope de CPU, en rojo sobre el ejecutor de HEAD |
| T45 | `3d20176` | `RLIMIT_CPU` en el hijo, una frase en `docs/ARCHITECTURE.md` y su test |
| T46 | `9d52277` | El test de los 16 hostiles ya no depende de la carga (R5-3) |
| T47 | `a4ac352` | Errata R4-3: la campaña de T38 bis corrió con 5 workers |
| T48 | `d2376fc` | Repuesto en `current.md` el bloque de H-T40-1 (R5-6) |
| T49 | `a2a293f` | Campaña de mutación con `--base c58e3b4` y su informe |

### Ficheros tocados

- `services/postventa-api/infrastructure/documentos/ejecutor_aislado.py` (T45):
  `MARGEN_SEGUNDOS_CPU = 5`; `tope_de_cpu(segundos) -> int`
  (`math.ceil(segundos) + MARGEN_SEGUNDOS_CPU`); `_aplicar_tope_de_cpu`, que
  pone `RLIMIT_CPU` blando y duro iguales; `_principal_hijo` recibe
  `segundos_cpu` y lo aplica justo después del tope de memoria, antes del byte
  del canal y antes de leer; `EjecutorMultiprocessing.ejecutar` calcula el
  valor con el `segundos` que ya recibía y se lo pasa al hijo. *Docstring* del
  módulo actualizado (el tope de CPU, y que cuenta CPU y no reloj).
- `services/postventa-api/tests/test_f036_lector_aislado.py` (T45, T46) y
  `services/postventa-api/tests/hijos_f036.py` (T45: dos hijos de prueba,
  `gasta_cpu` y `duerme`).
- `docs/ARCHITECTURE.md`, «La lectura aislada»: una frase (el tope de CPU, para
  el padre muerto) y `services/postventa-api/tests/test_f036_documentacion.py`:
  un test que la fija (`test_f036_t45_…`).
- `progress/impl_F-036.md` («Mutación (T38 bis)», T47), `progress/current.md`
  (T48), `progress/mutacion_F-036_bloque11.md` (T49),
  `specs/F-036-importar-excel/tasks.md` (T45–T49 marcadas).

**No cambian**, como pide la enmienda: el protocolo `EjecutorAislado`,
`SalidaHijo`, `tope_de_memoria_disponible()`, `lector_aislado.py`, el tope de
reloj del padre, ningún estado ni ninguna línea de log. `docs/INTEGRACION.md` y
`azure-apps` no se tocan: no cambia nada de lo que el servicio expone o consume.

### Decisiones de diseño

- **D-T45-1 · `_principal_hijo` gana un parámetro posicional** (`segundos_cpu`,
  entre `bytes_memoria` y `contenido`), sin valor por defecto: un hijo no puede
  arrancar sin su tope de CPU por descuido. Es una función privada del módulo;
  los tres tests que la llamaban en este proceso pasan ahora el argumento y
  doblan `_aplicar_tope_de_cpu` (en Linux, llamarla de verdad dentro de pytest
  le pondría el tope al propio pytest).
- **D-T45-2 · `_aplicar_tope_de_cpu` no devuelve nada.** La marca del canal
  sigue saliendo solo del tope de memoria (`limite_memoria_aplicado`): los dos
  se ponen juntos y antes del byte, y si el de CPU falla el error no se
  captura y el hijo muere sin mandarlo. Un valor de retorno que nadie usa
  habría sido además un mutante vivo.
- **D-T45-3 · `tope_de_cpu` es pública** (sin guion bajo): es la regla de R119
  («sus segundos más 5»), y así la fija el test del valor.
- **D-T46-1 · el test de los hostiles comprueba además qué tope recibe el
  ejecutor** (`EjecutorEspia.topes`): 30 s los `SE_LEE_IGUAL`, 3 s los
  `EN_EL_HIJO`, ninguna llamada los `EN_EL_PADRE`. Es lo que dio su fase RED.
  No se afloja nada más: resultado, estado del hijo, pico del padre y que el
  padre no abra el libro siguen igual; la comprobación de tiempo es
  «menos que **su** tope más el arranque».

**Desviaciones respecto a la spec: ninguna.** Dos cosas dichas, que no lo son:
la campaña de T49 se lanzó con `--timeout 900` además de la orden literal de
`tasks.md` (ver «T49»), y en el contenedor Linux hubo que copiar `pytest` y sus
dependencias de Python puro además de las tres bibliotecas de la review 5 (ver
«Cómo se ejecutó en Linux»).

### T45 · Fase RED

**Windows**, sobre el ejecutor de HEAD (`c58e3b4` + enmienda, `e045598`), con
los tests ya escritos. Comando, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q -p no:cacheprovider -k "r119" --tb=line`

```
E   AttributeError: module 'infrastructure.documentos.ejecutor_aislado' has no attribute 'MARGEN_SEGUNDOS_CPU'
E   AttributeError: module 'infrastructure.documentos.ejecutor_aislado' has no attribute 'tope_de_cpu'
E   AttributeError: module 'infrastructure.documentos.ejecutor_aislado' has no attribute '_aplicar_tope_de_cpu'. Did you mean: '_aplicar_tope_de_memoria'?
E   TypeError: _principal_hijo() takes 4 positional arguments but 5 were given
E   AssertionError: assert ('tests.hijos... 2048, b'abc') == ('tests.hijos...48, 8, b'abc')
=========================== short test summary info ===========================
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_margen_del_tope_de_cpu_es_de_5_s
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[30-35]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[30.0-35]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[29.01-35]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[3.0-8]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[2.5-8]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5[0.2-6]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_tope_de_cpu_es_rlimit_cpu_blando_y_duro
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_sin_resource_no_se_aplica_ningun_tope_y_el_byte_es_cero
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_si_el_tope_de_cpu_falla_el_hijo_muere_sin_mandar_el_byte
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_ejecutor_calcula_el_tope_de_cpu_y_se_lo_pasa_al_hijo[2.5-8]
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_ejecutor_calcula_el_tope_de_cpu_y_se_lo_pasa_al_hijo[30-35]
13 failed, 14 passed, 3 skipped, 161 deselected in 3.03s
```

(Las líneas `E` están deduplicadas: cada una se repite por cada test que falla
igual. Los 3 saltados son los tres tests de Linux: el de memoria y los dos
nuevos.)

**Linux**, mismo código de HEAD y mismos tests, con `pytest` dentro del
contenedor (ver «Cómo se ejecutó en Linux»):
`python -m pytest --noconftest -p no:cacheprovider tests/test_f036_lector_aislado.py -k r119 --tb=short -q`
→ **15 failed, 15 passed, 161 deselected in 17.66s**: los 13 de Windows y los
dos reales.

```
_ test_f036_r119_en_linux_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope _
tests/test_f036_lector_aislado.py:1369: in test_f036_r119_en_linux_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope
    assert lectura.recv_bytes(1) == b"1"
E   EOFError
----------------------------- Captured stderr call -----------------------------
Process ForkServerProcess-3:
TypeError: _principal_hijo() takes 4 positional arguments but 5 were given
_________ test_f036_r119_en_linux_el_tope_de_cpu_cuenta_cpu_y_no_reloj _________
tests/test_f036_lector_aislado.py:1387: in test_f036_r119_en_linux_el_tope_de_cpu_cuenta_cpu_y_no_reloj
    assert lectura.recv_bytes(1) == b"1"
E   EOFError
----------------------------- Captured stderr call -----------------------------
Process ForkServerProcess-4:
TypeError: _principal_hijo() takes 4 positional arguments but 5 were given
```

**Dicho con claridad: ese rojo de los dos tests de Linux es por la firma**, no
por el hueco. Los tests arrancan `_principal_hijo` con su tope de CPU, y el de
HEAD no admite ese argumento: el hijo muere al arrancar. No demuestra que el
huérfano siga vivo. Eso se enseña con un **guion contra el código de HEAD**
(lo prevé T45), que arranca `_principal_hijo` con la firma que tenga, con el
hijo `gasta_cpu` y **sin el reloj del padre**, y mira `/proc/<pid>/stat`:

```
parámetros de _principal_hijo: ['escritura', 'destino', 'bytes_memoria', 'contenido']
segundos del hijo=0.5 tope de CPU=None byte=b'1'
  a los 15.0 s de reloj SIGUE VIVO, CPU gastada 14.2 s; nadie lo ha parado (lo mata el guion)
segundos del hijo=30 tope de CPU=None byte=b'1'
  a los 50.0 s de reloj SIGUE VIVO, CPU gastada 49.8 s; nadie lo ha parado (lo mata el guion)
```

Es R5-1: en HEAD, un hijo sin padre gasta CPU hasta que acabe su trabajo. El
segundo test de Linux («cuenta CPU, no reloj») no tiene un rojo con sentido
propio: guarda que el arreglo no mate de más.

### T45 · En verde

**Windows**, la verificación de la tarea, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py tests/test_f036_arquitectura.py tests/test_f036_documentacion.py -q -p no:cacheprovider`
→ **272 passed, 7 skipped in 90.92s** (antes de añadir el test de la frase de
`ARCHITECTURE.md`; con él y con `test_f036_alcance_cerrado.py`, los tres de
documentación y arquitectura: **115 passed in 5.41s**).

**Linux**, los tests `r119` con el código del arreglo:

```
..............................                                           [100%]
============================= slowest 4 durations ==============================
3.02s call     tests/test_f036_lector_aislado.py::test_f036_r119_en_linux_el_tope_de_cpu_cuenta_cpu_y_no_reloj
1.10s call     tests/test_f036_lector_aislado.py::test_f036_r119_el_primer_lector_sin_tope_del_proceso_avisa
1.01s call     tests/test_f036_lector_aislado.py::test_f036_r119_en_linux_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope
0.74s call     tests/test_f036_lector_aislado.py::test_f036_r119_en_linux_el_tope_de_memoria_se_aplica_al_hijo
30 passed, 161 deselected in 14.56s
```

El huérfano de prueba (tope de CPU de 1 s) **muere solo en 1,01 s**; el que
duerme 3 s con el mismo tope responde y acaba con `exitcode` 0.

**Linux, el fichero entero** con el código final (`a2a293f`), mismo contenedor:
`python -m pytest --noconftest -p no:cacheprovider tests/test_f036_lector_aislado.py -q -rs`
→ **189 passed, 3 skipped in 47.47s** (los 3, los lentos de
`POSTVENTA_TESTS_LENTOS=1`). Ningún test de Linux se salta.

**Cuánto tarda en morir el huérfano**, mismo guion de la fase RED sobre el
código del arreglo:

```
parámetros de _principal_hijo: ['escritura', 'destino', 'bytes_memoria', 'segundos_cpu', 'contenido']
segundos del hijo=0.5 tope de CPU=6 byte=b'1'
  MUERTO SOLO a los 6.56 s de reloj, exitcode=-9, última CPU vista 5.94 s
segundos del hijo=30 tope de CPU=35 byte=b'1'
  MUERTO SOLO a los 35.12 s de reloj, exitcode=-9, última CPU vista 34.94 s
```

Con los 30 s de producción, **un huérfano muere a los 35,1 s** (35 s de CPU),
frente a seguir vivo sin tope en HEAD (y los 90–110 s de CPU que estimó la
review 5 para un fichero de R4-1). La señal es `SIGKILL` (`exitcode=-9`) en
este núcleo; el test pide solo `exitcode` negativo (aviso 3 de la enmienda).

#### Cómo se ejecutó en Linux

Contenedor de la imagen `python` 3.12.14 local (`09f7da3bc104`, la de la
review 5), **`--network none --rm`**, con dos carpetas montadas en solo
lectura: el código (`git archive HEAD` de `services/postventa-api`, más los
ficheros de trabajo de cada momento) y las bibliotecas copiadas del `.venv` de
Windows. Núcleo `Linux-6.18.33.1-microsoft-standard-WSL2`, `forkserver`.

- **Más bibliotecas que la review 5, dicho.** Además de `openpyxl`,
  `et_xmlfile` y `defusedxml`, para lanzar `pytest` dentro se copiaron
  `pytest`, `_pytest`, `iniconfig`, `pluggy`, `packaging`, `pygments`, `py.py`
  y `yaml` (todas de Python puro; `yaml` cae a su implementación en Python).
  Nada se instaló desde la red.
- **`--noconftest`.** El `conftest.py` de la suite importa `config.settings`
  (`pydantic`, binario de Windows), que no se puede copiar. Sin él no está la
  guardia `sin_red`; el contenedor no tiene red de ningún modo.
- Los guiones (`huerfano.py`, el de las mutaciones a mano) son de evidencia y
  viven en el directorio temporal de la sesión: **no se versionan**.

### T46 · El test que dependía de la carga (R5-3)

**RED** (el test pide ya que los `SE_LEE_IGUAL` reciban el tope de producción y
el lector sigue inyectando 3 s a todos):
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q -p no:cacheprovider -k "los_hostiles_de_todas or deben_leerse" --tb=line`

```
E   assert [3.0] == [30]
FAILED …a_tiempo_y_con_el_padre_acotado[review-1-celda-en-la-fila-1048576]
FAILED …a_tiempo_y_con_el_padre_acotado[review-3-comentario-sobre-rango]
FAILED …a_tiempo_y_con_el_padre_acotado[review-2-combinado-A]
FAILED …a_tiempo_y_con_el_padre_acotado[review-2-combinado-A-H]
FAILED …a_tiempo_y_con_el_padre_acotado[review-2-hipervinculo-A-H]
5 failed, 13 passed, 174 deselected in 47.65s
```

Justo los cinco que deben leerse. **Verde**, el fichero entero:
**185 passed, 7 skipped in 81.23s**.

**Tres veces seguidas con la máquina cargada.** La carga fue la suite entera
del `api` corriendo a la vez en una copia desechable de `git archive HEAD` (con
el test nuevo). `-k "los_hostiles_de_todas" --durations=6`:

| Vuelta | Hora | Tests de la suite de carga ya hechos | Resultado |
|---|---|---|---|
| 1 | 22:24:18 | 629 | **17 passed** in 64.70s |
| 2 | 22:25:25 | 4.497 | **17 passed** in 57.00s |
| 3 | 22:26:24 | 5.156 | **17 passed** in 63.14s |

(17: los 16 ficheros y el test que cuenta que están los 16.) La suite de carga
seguía corriendo al acabar la tercera vuelta (5.189 hechos) y terminó después
en verde: **6407 passed, 84 skipped in 529.09s** —en la copia, sin `.env` ni
`muestras/`, por eso 84 saltados y no 72—.

**Lo que no cubre, dicho:** los tres `EN_EL_HIJO` siguen con 3 s porque deben
**pasarse** del tope; cargar la máquina solo los hace pasarse más. No se ha
reproducido el rojo original de la review 5 (dos suites a la vez y
`[review-3-comentario-sobre-rango]` rozando los 3 s): el arreglo quita la
causa —ese fichero tiene ahora 30 s—, no lo he visto fallar antes y pasar
después bajo la misma carga.

### T47 · Errata R4-3

`progress/mutacion_F-036_bloque10quater.md` dice «Workers | 5»; la tabla de
«Evidencias» de «T37 bis–T38 bis» decía «con 6 workers». Corregido a **5**, con
una nota de errata en «Mutación (T38 bis)». La orden que hay en esa sección
(`--workers 6`) no se toca: es la orden, no el informe (aviso 4 de la
enmienda). Los 335,4 s son el total que midió la herramienta, no un cálculo a
partir de los workers: no cambian, y no hay otra cifra derivada.

Verificación: `grep -n "workers" progress/mutacion_F-036_bloque10quater.md` →
`--workers 5` y «Workers | 5»; la sección dice ahora 5.

### T48 · El bloque de H-T40-1, repuesto (R5-6)

Recuperado con `git show 6b7d598^:progress/current.md` (12 líneas, desde su
título hasta la línea anterior al bloque siguiente) y puesto entre el bloque
de T42–T44 y el de T39–T41. Verificación:
`grep -n "DESBLOQUEADA · 2026-10-01 · H-T40-1" progress/current.md` → **una**
línea; y un `diff` de esas 12 líneas contra las de `6b7d598^` → **idénticas**
(sin contar los finales de línea, que en el árbol de trabajo son CRLF).

### T49 · Mutación

**La herramienta.** Desde la raíz:
`python -m harness.mutacion --feature F-036 --base c58e3b4 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque11.md`

- **48 líneas en alcance**, todas de `ejecutor_aislado.py`.
- **2 mutantes generados, 2 muertos, 0 supervivientes, 0 timeouts**, 318,6 s.
  `MARGEN_SEGUNDOS_CPU = 5 → 6` y `math.ceil(segundos) + MARGEN → − MARGEN`.
- **Workers: 2**, según el informe de la herramienta (se pidieron 6; solo
  había dos mutantes).
- **Una primera tanda con la orden literal de `tasks.md`** (sin `--timeout`:
  120 s por mutante, el valor de `harness/rigor.json`) dio **2 timeouts y
  ningún veredicto**, también en el repaso en serie (362,4 s, 2 workers). No es
  un cuelgue: la suite del `api` tarda más de 120 s en llegar a los tests que
  matan. Se repitió con `--timeout 900`, como todas las campañas de F-036. Ese
  primer informe no se conserva en el repositorio (lo sustituye el bueno).

**Las mutaciones que pide T49, a mano.** La herramienta solo saca dos mutantes
de esas líneas, así que las de la lista de T49 —y alguna más— se aplicaron una
a una sobre una copia de `git archive HEAD`, pasando los tests `r119` de
`tests/test_f036_lector_aislado.py` en Windows y en el contenedor Linux, y
restaurando después (comprobado: la copia quedó igual que HEAD). Sin mutar:
Windows **27 passed, 3 skipped**; Linux **30 passed**.

| Mutación | Windows | Linux | Tests reales de Linux que caen |
|---|---|---|---|
| M1 · quitar el `setrlimit` de CPU (la llamada en el hijo) | **cae**: 2 failed | 3 failed | el del huérfano |
| M2 · `RLIMIT_CPU` → `RLIMIT_AS` | **cae**: 3 failed | 5 failed | el del huérfano y el de memoria |
| M3 · quitar el margen | **cae**: 8 failed | 8 failed | ninguno |
| M4 · margen 5 → 4 | **cae**: 9 failed | 9 failed | ninguno |
| M5 · quitar el redondeo | **cae**: 6 failed | 7 failed | el de memoria |
| M6 · `math.ceil` → `math.floor` | **cae**: 4 failed | 4 failed | ninguno |
| M7 · `math.ceil` → `round` | **cae**: 4 failed | 4 failed | ninguno |
| M8 · el tope de CPU después del byte del canal | **cae**: 2 failed | 2 failed | ninguno |
| M9 · el tope de CPU después de leer | **cae**: 2 failed | 3 failed | el del huérfano |
| M10 · el tope de CPU antes que el de memoria | **cae**: 1 failed | 1 failed | ninguno |
| M11 · duro distinto del blando | **cae**: 2 failed | 2 failed | ninguno |
| M12 · tragarse el fallo de `setrlimit` | **cae**: 1 failed | 1 failed | ninguno |
| M13 · el ejecutor pasa los segundos sin margen | **cae**: 2 failed | 2 failed | ninguno |
| M14 · el ejecutor pasa un tope fijo | **cae**: 1 failed | 1 failed | ninguno |

**14 de 14 caen en Windows**, por los tests con `setrlimit` doblado; **ninguna
cae solo en Linux**. Dos lecturas de la tabla:

> *Nota del 2026-10-02 (review 6, R6-1).* «Ninguna cae solo en Linux» valía
> para **estas 14**, las del implementer. La review 6 probó una más, su M16
> (`if segundos_cpu > 30:` delante de la llamada al tope de CPU en el hijo),
> y esa **sí caía solo en Linux**: en Windows sobrevivía, porque los tests
> doblados de `_principal_hijo` usaban siempre 35. Desde `dc49bfa` cae también
> en Windows (ver «Menores de la review 6 (R6-1 a R6-3)», al final).

- **Los tests reales de Linux no ven M8** (el tope después del byte): con el
  tope puesto una línea más tarde el huérfano muere igual. Lo caza solo el
  test del orden, que es el que tiene que cazarlo.
- **M5 hace caer el test de memoria de Linux** porque `setrlimit` no admite un
  número con decimales y el hijo muere al arrancar: efecto colateral, no un
  test del redondeo.

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `bash harness/init.sh` tal cual, tras el último commit de código y de la campaña (`a2a293f`): raíz **62 passed** (4,87 s); servicio `api` **6417 passed, 74 skipped**, ejecutado de verdad; `front` en verde (caché). `ENTORNO LISTO. Puedes trabajar.` Sobre los 6402 del merge de `dev`: **+15 tests** (13 del tope de CPU, 1 de T46 y 1 de la frase de `ARCHITECTURE.md`) y **+2 saltados** en Windows (los dos reales de Linux). La suite del `api` aparte, sin cobertura, en una copia desechable y con T46 ya puesto: **6407 passed, 84 skipped in 529.09s** |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 3191 líneas cambiadas cubiertas (3187/3191, umbral 80%, nivel critico)` |
| Mutación | `progress/mutacion_F-036_bloque11.md`, `--base c58e3b4 --timeout 900`: 48 líneas, **2 mutantes, 2 muertos, 0 supervivientes, 0 timeouts**, 318,6 s con **2 workers** (pedidos 6). A mano: **14 de 14 caen** en Windows; ninguna solo en Linux |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **638,02 s** (0:10:38); aparte, sin cobertura y con el test de los hostiles lanzándose a la vez: **529,09 s**. `tests/test_f036_lector_aislado.py` solo: **81,23 s** en Windows, **47,47 s** en Linux |
| Linux (contenedor sin red) | RED: 15 failed (los dos reales, por la firma) y el guion contra HEAD: huérfano **vivo a los 50 s** con 49,8 s de CPU. Verde: `r119` **30 passed**; el fichero entero **189 passed, 3 skipped in 47.47s**; el huérfano muere a los **35,12 s** con los topes de producción |
| *Lint* | `ruff` en la raíz, dentro de `init.sh`: **71 avisos**, los mismos que en T42–T44; los cuatro ficheros de código tocados, limpios con la configuración del servicio (`All checks passed!`) |

### Qué queda fuera y qué falta

- **Siguiente: review 6.** Para el reviewer: D-T45-1 (el parámetro nuevo de
  `_principal_hijo`), que el rojo de los dos tests reales de Linux es por la
  firma y el hueco lo enseña el guion, y que la campaña llevó `--timeout 900`.
- **Para validar el humano** (lo dejó la enmienda): el margen de 5 s y que el
  tope de CPU no tenga traza propia.
- **No comprobado en Azure.** Que `setrlimit(RLIMIT_CPU)` se aplica en Flex
  Consumption se ve con lo mismo que el de memoria: si fallara, el hijo
  moriría antes del byte y toda importación sería `fichero_sospechoso`. Entra
  en T29 sin paso nuevo (`tope_memoria_aplicado=True` en el log vale para los
  dos).
- **Lo que el tope de CPU no cubre** (lo dice `design.md`): un huérfano parado
  sin gastar CPU. Tampoco gasta nada.
- **Los tests lentos** (`POSTVENTA_TESTS_LENTOS=1`, los de R4-1 con 30 s) no se
  han relanzado en este bloque: T45 no cambia el tope de reloj.
- **T16 y T27–T29 · MANUAL del humano, PENDIENTES.** **T30**, del líder.
- `git push` no se ha hecho.

## Menores de la review 6 (R6-1 a R6-3) · 2026-10-02 · hecho; T16 y T27–T29 siguen siendo MANUAL del humano; T30 la lanza el líder

Encargo corto, aprobado por el humano: los tres hallazgos menores de la
review 6 y parar. **No se toca código de producción**: un test y textos.

| Hallazgo | Commit | Qué |
|---|---|---|
| R6-1 | `dc49bfa` | El test del orden de los topes del hijo va con dos valores de CPU (35 y 8) |
| R6-2 | `918cf6f` | Errata de `requirements.md` y `design.md`: la CPU del huérfano, con la medida de Linux |
| R6-3 | `621086b` | Errata de `tasks.md`: la orden de T49 lleva `--timeout 900` |

### Ficheros tocados

- `services/postventa-api/tests/test_f036_lector_aislado.py` (R6-1):
  `test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer`
  pasa a estar parametrizado con `segundos_cpu` en `[35, 8]`. Las
  comprobaciones son las mismas; solo cambia que el valor ya no es fijo.
  Un test más en la suite (+1).
- `specs/F-036-importar-excel/requirements.md` (nota de la novena enmienda, en
  R119) y `specs/F-036-importar-excel/design.md` §5.2 («El hueco») (R6-2).
- `specs/F-036-importar-excel/tasks.md`, verificación de T49 (R6-3).
- `progress/impl_F-036.md`: esta sección y una nota en «Bloque 11», «T49 ·
  Mutación», bajo «ninguna cae solo en Linux». `progress/current.md`: bloque
  de estado.

**No cambian:** `ejecutor_aislado.py` (ni ningún otro fichero de producción),
ningún requisito, ninguna tarea, `docs/` ni `azure-apps`.

### R6-1 · La mutación M16, antes y después

M16 es la de la review 6: en `infrastructure/documentos/ejecutor_aislado.py`,
dentro de `_principal_hijo`, la llamada `_aplicar_tope_de_cpu(segundos_cpu)`
pasa a ir bajo `if segundos_cpu > 30:`. Aplicada a mano **en el árbol de
trabajo** (no en una copia) y deshecha con `git checkout`. Comando, desde
`services/postventa-api`, los mismos tests que usó la review:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py -q -p no:cacheprovider -k "r119 or el_hijo_" --tb=short`

**1. Con M16 y el test de antes (HEAD `784d758`): sobrevive.** Reproduce lo
que dijo la review.

```
 services/postventa-api/infrastructure/documentos/ejecutor_aislado.py | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
.................................sss..........                           [100%]
43 passed, 3 skipped, 146 deselected in 7.26s
```

**2. Con M16 y el test nuevo: cae en Windows.** El `git diff` de la mutación
y la salida:

```
@@ -169,7 +169,8 @@ def _principal_hijo(
     """Lo que corre en el hijo: los topes, el aviso de si se aplicaron y la lectura."""
     try:
         aplicado = _aplicar_tope_de_memoria(bytes_memoria)
-        _aplicar_tope_de_cpu(segundos_cpu)
+        if segundos_cpu > 30:
+            _aplicar_tope_de_cpu(segundos_cpu)
         escritura.send_bytes(b"1" if aplicado else b"0")
         escritura.send_bytes(_funcion_del_hijo(destino)(contenido))
     except MemoryError:
==== CON M16
..........................F.......sss..........                          [100%]
================================== FAILURES ===================================
_ test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer[8] _
tests\test_f036_lector_aislado.py:1160: in test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer
    assert orden == [
E   AssertionError: assert [('setrlimit'...nal', b'cba')] == [('setrlimit'...nal', b'cba')]
E
E     At index 1 diff: ('canal', b'1') != ('setrlimit', 0, (8, 8))
E     Right contains one more item: ('canal', b'cba')
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_f036_lector_aislado.py::test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer[8]
1 failed, 43 passed, 3 skipped, 146 deselected in 6.92s
```

Cae justo el caso nuevo (`[8]`) y por lo que debe: falta el `setrlimit` de
CPU con (8, 8). El caso `[35]` sigue pasando con la mutación, que es por lo
que antes sobrevivía.

**3. Mutación deshecha** (`git checkout -- infrastructure/documentos/ejecutor_aislado.py`)
**y en verde.** `git status --short` solo enseña el test; `git diff --stat`
del ejecutor no da ninguna línea:

```
==== SIN M16
 M tests/test_f036_lector_aislado.py
(diff de ejecutor_aislado.py: vacio si no hay lineas encima)
..................................sss..........                          [100%]
44 passed, 3 skipped, 146 deselected in 6.47s
```

(44 y no 43: el caso nuevo. Los 3 saltados son los tres tests reales de
Linux.)

**Lo que no se ha hecho, dicho:** no se ha vuelto a lanzar M16 en el
contenedor Linux (allí ya caía, por el test real del huérfano, según la
review 6), ni se han repetido las otras 16 mutaciones de la review: el cambio
solo añade un caso a un test y no quita ninguna comprobación.

### R6-2 · La cifra de la CPU del huérfano

Donde `requirements.md` (nota de la novena enmienda, R119) y `design.md` §5.2
(«El hueco») decían «del orden de 90–110 s de CPU», va lo que midió la
review 6 en Linux matando al padre con los tres ficheros de R4-1: **antes**
33,0 s, 30,2 s y 60,0 s de CPU; **con el arreglo** 30,6 s, 30,2 s y 34,9 s.
Los dos sitios llevan una nota de errata fechada que dice qué decía antes, de
dónde salía (estimación de la review 5 con medidas de Windows) y de dónde
sale la cifra nueva (`progress/review_F-036.md`, «Review 6», R6-2). En la
nota de `requirements.md`, «un huérfano gasta 35 s de CPU en vez de 90–110»
pasa a «como mucho 35 s (…), cuando sin tope no tenía límite».

- **Ningún requisito cambia.** R119 (el texto EARS y sus pruebas), el margen
  de 5 s y su justificación quedan igual; solo cambia la cifra del motivo.
- **Las cifras no las he medido yo**: son las de la review 6, copiadas de su
  informe.
- **Los bloques históricos no se reescriben**, como pide el encargo: la cifra
  antigua sigue en `progress/current.md` (bloques de la review 6 y del
  Bloque 11), en «Bloque 11 · T45 · En verde» de este informe («los 90–110 s
  de CPU que estimó la review 5», que además lo llama estimación) y en
  `progress/review_F-036.md` (review 5).
- **Ningún test fijaba la cifra antigua**: `grep` de `90`/`110` en
  `tests/test_f036_documentacion.py` no da nada que tenga que ver, y no ha
  habido que ajustar ningún test.

### R6-3 · La orden de T49

La verificación de T49 en `tasks.md` lleva ahora `--timeout 900`, con una
nota de errata debajo: con los 120 s por defecto de `harness/rigor.json` da 2
timeouts y ningún veredicto. Es la orden con la que se lanzó de verdad la
campaña del informe (`progress/mutacion_F-036_bloque11.md`).

**Fuera de este encargo, dicho:** la review 6 propone además, en
«Automejora», que la cabecera del informe de la herramienta escriba el
`--timeout`. Es un cambio de `harness/mutacion.py` (y de `arnes-base`): no se
ha tocado.

### Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | `tests/test_f036_lector_aislado.py` y `tests/test_f036_documentacion.py`, con los tres commits ya hechos: **262 passed, 7 skipped in 45.71s**. `bash harness/init.sh` tal cual, una vez, con los tres commits y los textos de `progress/` ya escritos: raíz **62 passed** (5,88 s); servicio `api` **6418 passed, 74 skipped**, ejecutado de verdad (6417 + el caso nuevo); `front` en verde (caché). `ENTORNO LISTO. Puedes trabajar.` |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 3191 líneas cambiadas cubiertas (3187/3191, umbral 80%, nivel critico)` (igual que antes: no hay líneas de producción nuevas) |
| Mutación | Sin campaña de la herramienta: no cambia código de producción (lo dice el encargo). La evidencia es **M16 a mano**: sobrevivía (43 passed) y ahora **cae en Windows** (1 failed, el caso `[8]`); deshecha, 44 passed |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: **918,33 s** (0:15:18); los dos ficheros de la verificación, aparte: **45,71 s** |

### Qué queda fuera y qué falta

- **R6-4** es informativo, para T29 8 bis: no pedía cambio.
- **La cabecera del informe de mutación** sin `--timeout` (automejora de la
  review 6): sin tocar, es del arnés.
- **Para validar el humano**, igual que antes: el margen de 5 s y que el tope
  de CPU no tenga traza propia.
- **T16 y T27–T29 · MANUAL del humano, PENDIENTES.** **T30**, del líder.
- `git push` no se ha hecho.

## T16 · el test de las seis tablas de F-005 · 2026-10-02 · hecho; T16 queda en verde. T27–T29 siguen siendo MANUAL del humano; T30 la lanza el líder

Encargo mínimo aprobado por el humano. **Sin código de producción.**

### Qué pasó

El humano ejecutó la MANUAL T16 (`infra\pruebas_bbdd_efimera.ps1`, PostgreSQL
efímera en Docker) y salió **1 failed, 24 passed**. Todo
`test_f036_bbdd_bandeja.py` pasaba. Caía
`tests_bbdd/tests/test_f005_bbdd_ddl_idempotente.py::test_f005_r1_estan_las_seis_tablas_en_la_base`,
que exigía que el schema tuviera **exactamente** seis tablas (igualdad de
listas). Hoy hay trece: el DDL ha crecido con los ficheros `08_` a `14_` de
`infrastructure/persistencia/sql/` (los tres últimos, de F-036). El test no se
tocaba desde el 2026-08-20 y ya estaba roto en `dev`; nadie lo vio porque esta
suite necesita Docker y no corre en `init.sh`.

### Qué cambió

Un solo fichero, de test:
`services/postventa-api/tests_bbdd/tests/test_f005_bbdd_ddl_idempotente.py`.

- Las seis tablas pasan a una constante `TABLAS_DE_F005` (`frozenset`, escritas
  a mano, las mismas seis de antes).
- El test comprueba **subconjunto**, no igualdad: calcula las que faltan y
  exige que no falte ninguna, con un mensaje que dice cuáles. El nombre del
  test no mentía y se conserva; el docstring explica por qué no es lista
  cerrada.
- El resto de comprobaciones de F-005 (idempotencia, `bytea`, `CHECK`,
  aislamiento, reproceso) quedan **sin tocar**.

Los otros ficheros, leídos y sin cambio: `test_f005_bbdd_aislamiento.py`
también consulta `information_schema.tables`, pero con intersección contra
`public` (no es lista cerrada y no cae al crecer el DDL). Su tupla
`NUESTRAS_TABLAS` solo lleva las seis de F-005, así que **no vigila en
`public` las siete tablas posteriores**: es un hueco de cobertura anterior a
F-036, fuera de este encargo; queda apuntado para el líder.

### Verificación (salidas reales)

Orden, desde la raíz, con Docker arrancado:
`powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`

1. **Antes** (ejecución del humano): `1 failed, 24 passed`, el test de arriba.
2. **Con el arreglo**:

   ```
   ==> Ejecutando la suite de base de datos (tests_bbdd)
   .........................                                                [100%]
   25 passed in 5.99s

   ==> Destruyendo el contenedor

   SUITE DE BASE DE DATOS EN VERDE.
   ```
3. **Control** (el test no es un checkbox vacío): añadida a mano a
   `TABLAS_DE_F005` una tabla inventada, `tabla_inventada_control`, y
   relanzada la misma orden:

   ```
   E       AssertionError: faltan tablas de F-005 en la base: ['tabla_inventada_control']
   FAILED tests_bbdd/tests/test_f005_bbdd_ddl_idempotente.py::test_f005_r1_estan_las_seis_tablas_en_la_base
   1 failed, 24 passed in 9.26s
   SUITE DE BASE DE DATOS EN ROJO (codigo 1).
   ```
   Deshecha la tabla inventada (el diff ya no la contiene) y relanzada:
   `25 passed in 8.98s`, `SUITE DE BASE DE DATOS EN VERDE.`
4. `python -m pytest tests/test_f036_alcance_cerrado.py -q` desde
   `services/postventa-api` con su `.venv`: **26 passed in 6.70s**.

De las salidas en rojo solo se copian aquí la línea del test, la del `assert`
y el resumen: el resto de la traza lleva el `repr` de `Ajustes` (F-052) y no
entra en ningún fichero.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `tests_bbdd`: **25 passed** (base efímera); `test_f036_alcance_cerrado.py`: **26 passed** |
| Cobertura de las líneas cambiadas | No medida: `bash harness/init.sh` **no se ha relanzado** (lo dice el encargo: `tests_bbdd` no entra en `init.sh` y el líder lanza T30 después). No hay líneas de producción cambiadas |
| Mutación | Sin campaña: no cambia código de producción. La evidencia es el control a mano del punto 3 (cae con una tabla que falta) |
| Tiempo de la suite | `tests_bbdd`: 5,99 s (8,98 s en la repetición); alcance cerrado: 6,70 s |

### Qué queda fuera y qué falta

- **F-052** (el `repr` de `Ajustes` enseña secretos cuando un test falla): sin
  tocar, es otra feature.
- **`NUESTRAS_TABLAS` de `test_f005_bbdd_aislamiento.py`** no incluye las
  tablas posteriores a F-005: apuntado, sin tocar.
- **La suite `tests_bbdd` sigue fuera de `init.sh`**: un test de ahí puede
  volver a romperse sin que nadie lo vea. Decisión del humano / del arnés.
- `tasks.md`: T16 no se ha marcado aquí; es MANUAL del humano y la marca el
  líder con él.
- **T27–T29 · MANUAL del humano, PENDIENTES.** **T30**, del líder.
- `git push` no se ha hecho.

## Bloque 12 (T50–T54) · 2026-10-02 · formato visual de la plantilla y del Excel de errores

Décima enmienda de la spec (`d64ff0a`): R121–R127, `design.md` §3.6 y §5.2
(«Los topes y el formato visual»). Solo T51 toca código de producción, y solo
el **generador** de `infrastructure/documentos/excel_openpyxl.py`.

### T50 · el «antes» y la fase RED

**Medición del «antes»**, sobre HEAD `d64ff0a` (generador sin formato), con un
guion del directorio temporal de la sesión (no versionado, `medir_bloque12.py`):
genera en memoria los dos ficheros de `_legitimos()` de
`tests/test_f036_lector_aislado.py` y mide, por cada uno, elementos XML
(`lector_aislado._contar_elementos_xml(..., presupuesto=None)`), bytes del
fichero y descomprimidos (suma de `file_size` del ZIP), bytes del JSON de
`excel_openpyxl.leer_en_hijo` y su `sha256`; y cinco veces cada uno:

- la **lectura por el hijo real**: `LectorPlantillaAislado(entorno="test")` con
  el `EjecutorMultiprocessing` de producción envuelto en un espía (reloj de
  `leer` entero, con el arranque del hijo, y `SalidaHijo.segundos`);
- la **memoria**: en Windows no hay `RLIMIT_AS` ni máximo residente del hijo de
  `multiprocessing` a mano, así que se mide `leer_en_hijo` en un **subproceso
  aparte sin cobertura** (lo mismo que hace el hijo: importar el módulo y leer)
  con el `PeakWorkingSetSize` del proceso (`K32GetProcessMemoryInfo`), el mismo
  método de T39–T41; y, aparte, el pico de `tracemalloc` de `leer_en_hijo` en
  otro subproceso.

Comando: `.venv/Scripts/python.exe <scratchpad>/medir_bloque12.py 5` desde
`services/postventa-api` (Windows 11, Python 3.12.7, 22 núcleos). Salida real
(sin las líneas con los nombres de las partes, resumidas debajo):

```
d64ff0a
lector_aislado: sin tope de memoria en esta plataforma
python 3.12.7 · repeticiones=5 · núcleos=22
== plantilla completa
   fichero=60606 B  descomprimido=2744750 B (2.62 MiB)  elementos=26886
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=12
   hijo real, lector aislado entero (s): min=2.05 mediana=2.34 max=2.48  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.81 mediana=2.16 max=2.25
   leer_en_hijo en proceso aparte (s):   min=0.60 mediana=0.86 max=0.95
   pico de proceso, PeakWorkingSetSize (MiB): min=46.22 mediana=47.30 max=47.30  (antes de leer: min=30.02 mediana=30.07 max=30.10)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== Excel de errores más grande
   fichero=140585 B  descomprimido=8574765 B (8.18 MiB)  elementos=148916
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=15
   hijo real, lector aislado entero (s): min=2.10 mediana=2.63 max=2.76  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.73 mediana=2.17 max=2.22
   leer_en_hijo en proceso aparte (s):   min=0.50 mediana=0.62 max=0.89
   pico de proceso, PeakWorkingSetSize (MiB): min=46.52 mediana=46.66 max=47.49  (antes de leer: min=29.98 mediana=30.00 max=30.06)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== plantilla vacía
   fichero=33137 B  descomprimido=288750 B (0.28 MiB)  elementos=10886
   json=316 B  sha256(json)=e5ff022293e69cdf  partes=12
== v2 de prueba (158 filas sin errores, catálogo de los tests)
   fichero=37444 B  descomprimido=374723 B (0.36 MiB)  elementos=13419
   json=225771 B  sha256(json)=e07d490e5ca4640c  partes=12
```

Partes: la plantilla, las 12 de siempre (`[Content_Types].xml`, `_rels/.rels`,
`docProps/{app,core}.xml`, `xl/_rels/workbook.xml.rels`, `xl/styles.xml`,
`xl/theme/theme1.xml`, `xl/workbook.xml` y `xl/worksheets/sheet1–4.xml`); el
Excel de errores, esas más las 3 de los comentarios (`comment1.xml`,
`commentsDrawing1.vml` y `sheet1.xml.rels`). Elementos, descomprimido y JSON
coinciden **al byte** con T41 (26.886, 148.916, 8.574.765 y 5.257.211). El
`v2` de prueba es de **158 filas sin errores con el catálogo de los tests**, no
el `v2` real de la migración (ese necesita el original de OneDrive y el JSON
del catálogo, fuera del repositorio): sirve para comparar antes y después, no
sustituye la medición de T29.

| Medida («antes», HEAD `d64ff0a`) | Plantilla completa | Excel de errores más grande |
|---|---:|---:|
| Elementos XML | 26.886 | **148.916** |
| Bytes del fichero | 60.606 | 140.585 |
| Bytes descomprimidos | 2.744.750 | **8.574.765** |
| Bytes del JSON de `leer_en_hijo` | **5.257.211** | 5.257.211 |
| Hijo real, `leer` entero (mediana; máx.) | 2,34 s; 2,48 s | 2,63 s; 2,76 s |
| Hijo real, `SalidaHijo.segundos` (mediana) | 2,16 s | 2,17 s |
| Pico de proceso leyendo (`PeakWorkingSetSize`, mediana; máx.) | 47,3 MiB; 47,3 MiB | 46,7 MiB; 47,5 MiB |
| Pico de `tracemalloc` de `leer_en_hijo` | 20,59 MiB | 20,59 MiB |

**Fase RED.** Tests nuevos, todos con los valores **literales** de las tablas
de §3.6:

- `tests/test_f036_excel_generador.py`: `test_f036_r121_…` a
  `test_f036_r125_…` (cabecera, cuerpo, columna `Errores`, celda con error y
  sus vecinas, cuadrícula, pestañas, la regla condicional —una, su rango, su
  tipo, su fórmula y su color— y que no la hay con alguna fila con error,
  «Instrucciones» zona a zona, `_alto_de_parrafo` en sus fronteras, la tabla de
  ejemplos con su banda en la 2.ª y 4.ª fila, e impresión uno a uno); y los
  `test_f036_r126_…` de invariantes (mismas partes, hojas, cabecera, nombres
  definidos de las listas, validaciones, protección, filtro, paneles, formato
  de texto, versión y ningún `<f>`).
- `tests/test_f036_excel_lector.py`: `test_f036_r126_…` de ida y vuelta por
  `LectorPlantillaOpenpyxl` (plantilla rellena y Excel de errores con formato),
  el mismo `LibroLeido` de un libro al que se le quita el formato, y una
  plantilla con el **formato antiguo** (cabecera en negrita y error en naranja
  `FFF4B084`) que se importa igual.
- `tests/test_f036_lector_aislado.py`: `test_f036_r126_…` de ida y vuelta por
  `LectorPlantillaAislado` con el **hijo real**, y los `test_f036_r127_…` (la
  mitad del presupuesto son 150.000; el Excel de errores más grande cabe en
  ella; en la plantilla completa un `<conditionalFormatting>` con `sqref` de un
  rango y un `<cfRule>`, en el Excel de errores ninguno ni ningún `<dxf>`; las
  partes del ZIP; ninguna celda fuera de las filas 1–1001 y columnas A–I).
- Los **cuatro** que fijaban el aspecto antiguo, a los valores nuevos (ningún
  otro test existente tocado):
  `test_f036_s3_1_anchos_de_las_columnas_de_incidencias` (30, 26, 48, 56, 28,
  40, 24, 16, 50), `test_f036_r5_disposicion_de_instrucciones` (el título de
  14 a 15), `test_f036_r5_anchos_de_instrucciones` (B–H a 28) y
  `test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario` («sin
  relleno» solo en las columnas de datos; `Errores` con `FFF3F4F5`).

Ajuste al escribirlos: dos tests nuevos miraban `max_row` sobre el libro
**compartido** (`_plantilla()`), y un test que ya existía
(`test_f036_r2_celdas_de_datos_desbloqueadas_y_como_texto`) lee `ws["A1002"]`,
que en `openpyxl` **crea** la celda: según el orden salían en rojo sobre HEAD.
Ahora usan un libro recién abierto. No tenía que ver con el formato.

Comando (la verificación de T50), desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py -q -p no:cacheprovider --tb=line`.
Resumen real. De la traza solo se copian el resumen, los nombres y los
motivos: el resto podría llevar el `repr` de `Ajustes` (F-052); se comprobó
que esta salida no lo lleva.

```
101 failed, 493 passed, 7 skipped in 340.67s (0:05:40)
```

Los 101 en rojo, por test:

```
     18 test_f036_r121_cabecera_de_incidencias
      1 test_f036_r121_la_fila_de_la_cabecera_mide_34_puntos
      1 test_f036_r122_bandas_alternas_una_sola_regla_condicional_en_la_plantilla
     32 test_f036_r122_cuerpo_de_incidencias
      1 test_f036_r122_el_v2_sin_errores_lleva_las_bandas
      1 test_f036_r122_las_bandas_dependen_de_los_errores_y_no_del_origen
      1 test_f036_r122_r124_color_de_las_pestanas
      2 test_f036_r122_r124_las_hojas_visibles_no_ensenan_la_cuadricula
      3 test_f036_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo
      8 test_f036_r123_la_columna_errores_va_en_gris_no_editable
      5 test_f036_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo
      8 test_f036_r124_alto_de_un_parrafo_en_sus_fronteras
      2 test_f036_r124_cabecera_de_los_ejemplos
      1 test_f036_r124_el_alto_del_parrafo_no_baja_del_minimo
      1 test_f036_r124_el_parrafo_del_excel_de_errores_y_el_de_sin_oficios_tambien
      2 test_f036_r124_fila_1_la_obra_en_una_banda_burdeos
      2 test_f036_r124_fila_2_el_titulo_en_burdeos_con_su_linea
      1 test_f036_r124_filas_de_ejemplo_con_la_segunda_y_la_cuarta_en_banda
      1 test_f036_r124_los_cuatro_numeros_del_alto_de_un_parrafo
      1 test_f036_r124_los_ejemplos_del_yaml_con_su_banda
      1 test_f036_r124_parrafo_corto_y_largo_en_el_libro
      1 test_f036_r124_parrafos_en_calibri_11_con_el_alto_calculado
      2 test_f036_r125_impresion_de_incidencias
      1 test_f036_r127_la_plantilla_completa_lleva_una_regla_condicional_de_un_rango
      1 test_f036_r5_anchos_de_instrucciones
      1 test_f036_r5_disposicion_de_instrucciones
      1 test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario
      1 test_f036_s3_1_anchos_de_las_columnas_de_incidencias
```

Motivos más repetidos (líneas `E` de la salida):

```
     37 AssertionError: assert ('Calibri', 11.0, False, None) == ('Calibri', 1...e, 'FF1D2024')
     16 AssertionError: assert (None, None) == ('solid', 'FF9F2842')
      8 AttributeError: module 'infrastructure.documentos.excel_openpyxl' has no attribute '_alto_de_parrafo'
      8 AssertionError: assert (None, None) == ('solid', 'FFF3F4F5')
      3 AssertionError: assert ('solid', 'FFF4B084') == ('solid', 'FFFEF2F2')
      2 AssertionError: assert None == 'landscape'
      1 assert (True, 14.0) == (True, 15)
      1 AssertionError: assert {'A': 30.0, '...D': 60.0, ...} == {'A': 30, 'B'... 'D': 56, ...}
      1 assert 0 == 1
```

En verde **sobre HEAD**, a propósito (invariantes y guardas):

- los 7 `test_f036_r126_…` del generador (`-k r126`: `7 passed`), los 4 de
  `test_f036_excel_lector.py` (6 casos) y los 2 de ida y vuelta por el hijo
  real de `test_f036_lector_aislado.py` (`-k "r126 or r127"` en los dos
  ficheros del lector: `1 failed, 14 passed`; el rojo es el de la regla);
- de los `r121`–`r125`, los que comprueban lo que **no** tiene que pasar: que
  el texto de la cabecera no cambia, que el formato no crea celdas, que las
  hojas ocultas no llevan formato, que con alguna fila con error no hay regla
  condicional (5 casos) y que «Instrucciones» no lleva impresión propia (2);
- de los `r127`, todos menos el de la regla: el Excel de errores más grande ya
  estaba en 148.916 ≤ 150.000 (la guarda que vigila que el formato no lo pase).

### T51 · el formato en el generador

Solo `services/postventa-api/infrastructure/documentos/excel_openpyxl.py`, y
solo el generador (`git diff d64ff0a -- …/excel_openpyxl.py`: nada bajo «El
lector»):

- **Constantes** a nivel de módulo, una por valor de las tablas de §3.6: los
  once colores con su token de F-035 en el comentario (comprobados contra
  `git show feature/F-035-portal-posventa:services/postventa-front/css/styles.css`),
  `PESTANA_INCIDENCIAS`/`PESTANA_INSTRUCCIONES` (RGB de seis cifras sacado del
  ARGB), `FUENTE`, los cinco `PUNTOS_*`, `SANGRIA = 1`, los cuatro `ALTO_*`, los
  cuatro números del alto de un párrafo, `ANCHO_INSTRUCCIONES`,
  `ANCHO_EJEMPLOS`, `ANCHOS` con los valores nuevos, `RELLENO_ERROR` en
  `ERROR_SUAVE`, `FUENTE_ERROR`, `FORMULA_BANDAS`, `MARGEN_LATERAL` y
  `PIE_DE_PAGINA`. Funciones puras nuevas: `_alto_de_parrafo(texto) -> int`,
  `_solido(color)`, `_borde_de_cabecera()` y `_borde_fino()`.
- **`_incidencias`**: cabecera (relleno burdeos, acero en `I1`; Calibri 11
  negrita blanca; izquierda, centro, ajuste, sangría 1; laterales finos
  blancos y línea inferior media burdeos fuerte; fila de 34); cuerpo (Calibri
  10,5 tinta; cuatro lados finos `ACERO_100`; arriba y sangría 1, ajuste solo en
  C, D e I); `Errores` con `LIENZO` y texto `ACERO_TEXTO`; la celda con error
  con `RELLENO_ERROR` y `FUENTE_ERROR` (el comentario no cambia); la regla
  condicional `MOD(ROW(),2)=1` sobre `A2:H1001` con `bgColor` `BANDA` **solo
  si** `not any(fila.errores for fila in filas)`; cuadrícula oculta, pestaña
  burdeos e impresión (A4 apaisado, 1 de ancho y 0 de alto, `fitToPage`,
  `print_title_rows = "1:1"`, márgenes laterales 0,4 y el pie centrado).
- **`_instrucciones`**: la banda de la obra en A1–H1 (Calibri 15 negrita
  blanca, alto 38); el título en A2 (Calibri 13 negrita burdeos, alto 28) con
  la línea inferior media burdeos en A2–H2; los párrafos desde la fila 3 con
  Calibri 11 tinta, ajuste, arriba, sangría 1 y alto `_alto_de_parrafo`; la
  fila en blanco sin alto propio; la cabecera de los ejemplos como la de
  «Incidencias» con vertical centrada y alto 26; las filas de ejemplo con
  Calibri 10,5, bordes finos, ajuste, y `BANDA` en la 2.ª, 4.ª…; anchos 100 y
  28; cuadrícula oculta y pestaña acero.
- Los objetos de estilo se construyen una vez por zona y se comparten. **No
  cambian**: `_texto`, `_catalogos`, `_metadatos`, `_validacion`, la firma de
  `generar`, la protección, el filtro, los paneles, el formato de texto, el
  comentario del error ni el lector. Docstring del módulo, con un párrafo del
  aspecto.

**Desviación respecto al código de antes, dicha**: el título
(`textos.titulo`) ya no entra en la lista de párrafos (antes se escribía en
A2 dentro del bucle y luego se le ponía negrita); ahora se escribe aparte en
A2 con su estilo y los párrafos empiezan en la 3. Las posiciones son las
mismas (R126; `test_f036_r5_disposicion_de_instrucciones` lo fija).

**Un test de T50 ajustado** (solo su constructor, no lo que comprueba):
`_sin_formato` de `test_f036_excel_lector.py` hacía
`ws.print_title_rows = None`, que en `openpyxl` 3.1 **no** quita los títulos
(el *setter* ignora `None`); sobre HEAD pasaba porque no los había. Ahora vacía
el atributo que los guarda (`ws._print_rows = None`, API privada, dicho en el
comentario). Con eso, `…_sin_el_formato_se_lee_el_mismo_libro` (3 casos) pasó
de rojo a verde.

**El aviso 4 (el nombre definido de los títulos de impresión)**: no ha dado
problemas. Los dos tests de ida y vuelta por `LectorPlantillaAislado` con el
hijo real y los de `LectorPlantillaOpenpyxl` pasan, y el JSON de
`leer_en_hijo` sale idéntico (T52). `test_f036_r126_…_rangos_con_nombre_…`
comprueba que a nivel de libro siguen solo los seis de las listas (los
títulos de impresión son un nombre de la hoja).

**El aviso 3 (los hostiles de R4-1)**: ningún constructor se ha roto. El de
«formato-condicional» mete su `<conditionalFormatting>` delante de
`<dataValidations` en la plantilla de dos filas **sin errores**, que ahora ya
trae la regla de las bandas: el ancla sigue apareciendo una vez
(`assert xml.count(ancla) == 1`) y el fichero sigue siendo el mismo ataque
(un `sqref` de millones de rangos). `test_f036_r118_los_ficheros_de_r4_1_son_los_que_dicen_ser`
(3) y los 16 hostiles por el hijo real, en verde: `-k "r4_1 or
r118_los_hostiles or r127 or r126"` → `28 passed, 3 skipped` (los 3 *skip* son
los de los topes de producción, que solo corren con los lentos).

**Verificación de T51**, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_lector_aislado.py tests/test_f036_migracion.py tests/test_f036_importar_http.py tests/test_f036_arquitectura.py -q -p no:cacheprovider --tb=short`.
Primera pasada: `3 failed, 833 passed, 7 skipped in 434.31s` (los tres casos
de `_sin_formato`, arreglado arriba). Tras el arreglo,
`tests/test_f036_excel_lector.py -k r126` → `6 passed`, y la verificación de
T52 de abajo vuelve a pasar los dos ficheros del lector enteros. El generador
solo: `tests/test_f036_excel_generador.py` → `191 passed in 24.37s`.

### T52 · los topes, medidos otra vez (PARADA condicionada: **no hizo falta**)

Mismo guion (`medir_bloque12.py 5`), misma máquina, mismo método, sobre
`4eba996` (T51). Salida real:

```
4eba996
lector_aislado: sin tope de memoria en esta plataforma
python 3.12.7 · repeticiones=5 · núcleos=22
== plantilla completa
   fichero=61408 B  descomprimido=2749056 B (2.62 MiB)  elementos=26990
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=12
   hijo real, lector aislado entero (s): min=2.21 mediana=2.41 max=3.06  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=2.03 mediana=2.23 max=2.88
   leer_en_hijo en proceso aparte (s):   min=0.58 mediana=0.59 max=0.65
   pico de proceso, PeakWorkingSetSize (MiB): min=46.36 mediana=46.56 max=46.59  (antes de leer: min=29.97 mediana=30.01 max=30.10)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== Excel de errores más grande
   fichero=141193 B  descomprimido=8578900 B (8.18 MiB)  elementos=149016
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=15
   hijo real, lector aislado entero (s): min=2.97 mediana=3.28 max=3.41  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=2.59 mediana=2.81 max=2.98
   leer_en_hijo en proceso aparte (s):   min=0.72 mediana=0.90 max=1.11
   pico de proceso, PeakWorkingSetSize (MiB): min=46.57 mediana=46.57 max=47.60  (antes de leer: min=29.96 mediana=29.98 max=29.98)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== plantilla vacía
   fichero=33902 B  descomprimido=293056 B (0.28 MiB)  elementos=10990
   json=316 B  sha256(json)=e5ff022293e69cdf  partes=12
== v2 de prueba (158 filas sin errores, catálogo de los tests)
   fichero=38201 B  descomprimido=379029 B (0.36 MiB)  elementos=13524
   json=225771 B  sha256(json)=e07d490e5ca4640c  partes=12
```

**El tiempo, mirado dos veces más.** En esta pasada el reloj del hijo real
con el Excel de errores sale un 24,7 % peor (2,63 → 3,28 s de mediana), al
borde del 25 %; pero «antes» y «después» se midieron con una hora de
diferencia y la máquina tenía a la vez las suites de otros proyectos
corriendo (`datamart-seg-anual`, una campaña de mutación de `porcentajes`).
Para separar el formato de la carga se midió **intercalando** antes y
después en la misma pasada (guion `medir_ab_bloque12.py`: el «antes» se
genera con el generador de `d64ff0a` cargado de `git show`, el «después» con
el de HEAD, y los dos los lee el lector de HEAD, que no ha cambiado; mismos
constructores de `_legitimos()`). Dos pasadas, salida real (cambio de la
mediana, después frente a antes):

```
repeticiones=15, intercaladas antes/después
== plantilla-completa
   cambio de la mediana, leer entero: -5.7 %
   cambio de la mediana, SalidaHijo.segundos: -1.7 %
   cambio de la mediana, leer_en_hijo aparte: -4.3 %
== excel-de-errores-mas-grande
   antes    hijo real, leer entero (s): mediana=2.00 min=1.58 max=3.24
   después  hijo real, leer entero (s): mediana=2.22 min=1.80 max=2.87
   cambio de la mediana, leer entero: +10.9 %
   cambio de la mediana, SalidaHijo.segundos: +8.0 %
   cambio de la mediana, leer_en_hijo aparte: +10.9 %

repeticiones=21, intercaladas antes/después
== plantilla-completa
   cambio de la mediana, leer entero: -7.6 %
   cambio de la mediana, SalidaHijo.segundos: -8.2 %
   cambio de la mediana, leer_en_hijo aparte: +1.5 %
== excel-de-errores-mas-grande
   antes    hijo real, leer entero (s): mediana=1.63 min=1.11 max=2.15
   después  hijo real, leer entero (s): mediana=1.57 min=1.10 max=2.08
   cambio de la mediana, leer entero: -4.2 %
   cambio de la mediana, SalidaHijo.segundos: -4.7 %
   cambio de la mediana, leer_en_hijo aparte: -3.0 %
```

Es ruido de ±10 % alrededor de cero, sin una tendencia: el lector no lee
estilos, el JSON sale idéntico y el formato añade 100 elementos de 149.000. Se
toma como «no peor»; el peor dato de todas las pasadas (+24,7 %, sin
intercalar) tampoco pasa del 25 %.

**Tabla de T52** (elementos, bytes y JSON: medidas exactas; tiempo y
memoria: medianas de la primera pasada, y el cambio con las intercaladas):

| Medida | Antes (T50) | Después (T51) | Margen que hay que conservar | ¿Cabe? |
|---|---:|---:|---|---|
| Elementos XML, plantilla completa | 26.886 | 26.990 (+104) | < 60.000 | **Sí**, sobran 33.010 |
| Elementos XML, Excel de errores más grande | 148.916 | 149.016 (+100) | ≤ 150.000 | **Sí**, sobran **984** |
| Bytes descomprimidos, el mayor (el Excel de errores) | 8.574.765 | 8.578.900 (+4.135) | ≤ 8.912.896 | **Sí**, sobran 333.996; el doble, 17.157.800 B, sigue redondeando a **17 MiB** |
| Bytes del JSON de `leer_en_hijo`, el mayor | 5.257.211 | 5.257.211 (**idéntico**, mismo `sha256` `466c8afea7b78ef3`) | ≤ 5.767.168 | **Sí**, sobran 509.957; el doble sigue en **11 MiB** |
| Tiempo del hijo real, plantilla completa (`leer` entero) | 2,34 s | 2,41 s | ≤ 15 s y ≤ +25 % | **Sí** (+3 %; intercalado −6 % y −8 %) |
| Tiempo del hijo real, Excel de errores más grande | 2,63 s | 3,28 s (máx. 3,41) | ≤ 15 s y ≤ +25 % | **Sí** (+24,7 % sin intercalar; intercalado +10,9 % y −4,2 %) |
| Pico de memoria leyendo (`PeakWorkingSetSize`), el mayor | 47,3 MiB | 46,6 MiB | ≤ 512 MiB y ≤ +25 % | **Sí** (sin cambio) |
| Pico de `tracemalloc` de `leer_en_hijo` | 20,59 MiB | 20,59 MiB | (referencia) | Igual |
| Bytes del fichero (plantilla; Excel de errores) | 60.606; 140.585 | 61.408; 141.193 | (sin margen escrito; ≤ 2 MiB de R15) | Sí |
| Partes del ZIP (plantilla; Excel de errores) | 12; 15 | 12; 15 (las mismas) | ninguna parte nueva ni imagen | **Sí** |
| `v2` de prueba (158 filas, catálogo de los tests) | 13.419 | 13.524 | < 60.000 (un quinto) | **Sí** |

El `v2` de prueba también por el script de T37, sobre el fichero escrito en
el directorio temporal de la sesión (y borrado después):
`.venv/Scripts/python.exe scripts/contar_elementos_xml_f036.py "<scratchpad>\b12\v2_de_prueba_con_formato.xlsx"`:

```
Elementos XML: 13524
Presupuesto (R117): 300000
Un quinto del presupuesto: 60000
Veredicto: por debajo de un quinto del presupuesto
```

Es un `v2` **sintético**, no el de la migración real (que necesita el
original y el catálogo, fuera del repositorio): el `v2` de verdad, ya con
formato y guardado desde Excel, lo mide el humano en T29 tras repetir T28.

**Regla de decisión: caso 1, todo cabe. Ningún recorte.** Bandas alternas,
impresión y celdas de adorno de «Instrucciones» van **todas**, tal como la
muestra que aprobó el humano. Ningún tope tocado:
`git diff 07bd0c9 -- services/postventa-api/infrastructure/documentos/lector_aislado.py services/postventa-api/infrastructure/documentos/ejecutor_aislado.py`
→ vacío (0 bytes). Tampoco cambian el dominio, `config/` ni el front
(`git diff d64ff0a -- services/postventa-api/domain services/postventa-api/config services/postventa-front` → vacío).

**Para el humano y el spec-author: el margen que queda en elementos es de
984.** El Excel de errores más grande estaba a 1.084 de la mitad del
presupuesto y el formato se ha comido 100. Cabe, pero cualquier cosa que el
generador añada por fila con error (otro atributo con elemento propio, un
segundo comentario) lo pasará, y `test_f036_r127_el_excel_de_errores_mas_grande_cabe_en_la_mitad_del_presupuesto`
saltará antes de que llegue a producción. Las cifras nuevas para la spec
(design.md §5.2 y los docstrings de `lector_aislado.py`, que este bloque no
toca): 26.990 y 149.016 elementos; 8.578.900 B descomprimidos.

**Verificación de T52**, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py -q -p no:cacheprovider --tb=short`
→ `403 passed, 7 skipped in 342.89s (0:05:42)`, sin haber tocado los tests de
T41 ni las constantes de topes.

### T53 · documentación: búsqueda hecha, **nada que cambiar**

Búsqueda (sin distinguir mayúsculas) de
`naranja|relleno|negrita|ancho|color|F4B084|marcad|resaltad|aspecto|formato visual`
en los cuatro sitios de la tarea:

| Fichero | Lo que aparece | ¿Fija el aspecto? |
|---|---|---|
| `docs/ARCHITECTURE.md` | l. 638: «las celdas malas marcadas y una columna `Errores` que dice qué…»; l. 629 y 645: «marcada»/«marcados» de duplicadas y oficios ambiguos; l. 7: «Lo marcado `[PENDIENTE]`» | No: «marcadas» sigue siendo verdad, sin color |
| `docs/INTEGRACION.md` | l. 99 y 556: «respuesta marcada como cortada» (la pasarela de Sigrid) | No: nada de la plantilla |
| `services/postventa-front/importar.html` | ninguna coincidencia | — |
| `services/postventa-api/config/plantilla_incidencias.yaml` | l. 150 y 155: «con las celdas marcadas» (textos de «Instrucciones») | No: sin color, y el YAML no se toca (§3.6) |

Ninguno fija un color, un ancho ni una negrita: **no se cambia nada** y no se
añade la frase a `docs/ARCHITECTURE.md` (la tarea la pide solo si aparecía
alguna mención). El formato no cambia lo que el servicio expone ni consume:
`docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md` no se tocan. Los
cuadros de «Hoy» de `design.md` §5.2 y los docstrings de `lector_aislado.py` se
quedan como están; las cifras nuevas están en la tabla de T52, para el
spec-author.

Verificación, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py -q -p no:cacheprovider`
→ `84 passed in 0.59s`.

### T54 · campaña de mutación

Comando, desde la raíz:
`python -m harness.mutacion --feature F-036 --base 07bd0c9 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque12.md`
(con el `.venv` de la raíz). Salida real, cabecera y cierre:

```
F-036: 1 fichero(s), 219 línea(s) de producción (origen rama, 07bd0c98323a6e2be8cebc2e2c7bfc1ba11d4c4f..feature/F-036-importar-excel)
Campaña paralela: hasta 6 workers, uno por worktree.
...
60 mutantes evaluados, 60 muertos, 0 supervivientes, 0 timeouts en 1473.9 s
Informe: progress/mutacion_F-036_bloque12.md
```

- **Alcance**: solo `excel_openpyxl.py` (219 líneas cambiadas desde
  `07bd0c9`, todas del generador); ningún otro fichero de producción cambió.
- **Workers reales: 6** (el informe lo dice: «Workers | 6»; pedidos 6). Sin
  timeouts con `--timeout 900`.
- **60 mutantes, 60 muertos, 0 supervivientes.** Nada que justificar.

**Lo que el harness no muta, a mano.** `harness.mutacion` solo cambia
comparaciones, aritmética, lógicos, `not`, booleanos y enteros: **no** toca
cadenas ni decimales, así que los once colores, `FUENTE`, `PUNTOS_CUERPO`
(10,5), `MARGEN_LATERAL` (0,4), `PIE_DE_PAGINA`, `FORMULA_BANDAS`, las
alineaciones y estilos de borde, y las asignaciones que se pueden quitar, no
salen en su informe. La tarea exige que cada valor de §3.6 caiga por un test
con su literal, así que se mutaron a mano con un guion del directorio temporal
(`mutar_a_mano_b12.py`): cada mutación sola sobre `excel_openpyxl.py`,
`pytest -x` contra `tests/test_f036_excel_generador.py` (con `-k` donde se dice)
y el fichero restaurado siempre (`git status` limpio al acabar). **57
mutaciones, 57 caen**:

| Grupo | Mutaciones (cada una, sola) | Resultado |
|---|---|---|
| Los once colores | `BURDEOS`, `BURDEOS_FUERTE`, `ACERO`, `ACERO_100`, `ACERO_TEXTO`, `TINTA`, `LIENZO`, `BLANCO`, `ERROR_SUAVE`, `ERROR`, `BANDA`: la última cifra +1 | 11 caen |
| Tipografía, decimales y textos | `FUENTE` a `Arial`; `PUNTOS_CUERPO` 10,5 → 11; `MARGEN_LATERAL` 0,4 → 0,5; el pie sin «Construcciones Ruesma»; `FORMULA_BANDAS` `=1` → `=0` | 5 caen |
| Alineaciones y bordes | cabecera horizontal `left` → `center` y vertical `center` → `top`; lateral de cabecera `thin` → `hair`; inferior `medium` → `thin`; borde fino `thin` → `hair`; línea del título `medium` → `thin`; cuerpo `top` → `center`; «Instrucciones» `center` → `top` | 8 caen |
| Impresión | `portrait`; papel `LETTER`; títulos `1:2`; quitar títulos, margen izquierdo, margen derecho o pie | 7 caen |
| Pestañas | quitar la de «Incidencias» o la de «Instrucciones»; cruzarlas | 3 caen |
| Asignaciones quitadas en «Instrucciones» | alto de párrafo; alto de la cabecera de ejemplos; relleno de esa cabecera; borde y fuente de los ejemplos; fuente y ajuste de los párrafos; línea del título (*); alineación del título; relleno y alineación de la obra | 11 caen |
| Asignaciones quitadas en «Incidencias» | borde de la cabecera; borde del cuerpo | 2 caen |
| **Las que pide T54** | regla condicional **también en el Excel de errores** (`if True:`); su rango **hasta la columna `Errores`**; su color en `fgColor` en vez de `bgColor`; celda con error **sin relleno**; **sin color** de fuente; en **naranja** otra vez | 6 caen |
| **Invariantes de R126 al dar estilo** | quitar el **desbloqueo** de las celdas de datos (`-k "r2 or r126 or r64"`); quitar el **formato de texto** (ídem); **desbloquear** `Errores`; quitar las **validaciones** (`-k "r3 or r4 or r126"`) | 4 caen |

(*) La primera vez, quitar `ws.cell(row=2, column=indice).border = linea`
dejaba el `for` sin cuerpo y pytest no podía ni recoger (`rc=2`, no
compila); repetida con `pass` en su lugar: `1 failed, 161 passed`.

**Un tropiezo del guion, dicho para que nadie lo repita**: la primera pasada
del sondeo previo y de este guion lanzaban `.venv\Scripts\python.exe` con
ruta **relativa** y `cwd=services/postventa-api`; en Windows, `subprocess`
resuelve el ejecutable contra el directorio del **padre**, así que corría el
Python del `.venv` de la **raíz** y pytest salía con `rc=4` (o distinto de 0)
para todo, que el sondeo contaba como «muere». Se descartó esa pasada entera
y se repitió con la ruta absoluta y contando solo `rc=1` como muerto: los
resultados de arriba son los de la segunda.

Sondeo previo (el mismo guion de enumeración del harness, `generar_mutantes`
sobre las líneas cambiadas, contra `tests/test_f036_excel_generador.py`
solo): `mutantes: 60`, `supervivientes: 0`. Coincide con la campaña.

### `bash harness/init.sh` al acabar el bloque

Una vez, tal cual, sobre `33be26e` (T54). Salida real, las líneas que importan
(la salida no lleva ningún `repr` de `Ajustes`: comprobado):

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 6.39s
[OK] pytest en verde (con medición de cobertura)
6546 passed, 74 skipped in 970.59s (0:16:10)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3301 líneas cambiadas cubiertas (3297/3301, umbral 80%, nivel critico)
ENTORNO LISTO. Puedes trabajar.
```

Los avisos de `ruff` son deuda previa: los cuatro ficheros de este bloque
(`excel_openpyxl.py` y los tres de tests) pasan `ruff check` sin avisos.

### Ficheros tocados (Bloque 12)

- `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` (T51):
  solo el generador y el docstring del módulo.
- `services/postventa-api/tests/test_f036_excel_generador.py` (T50): tests
  nuevos `r121`–`r126` y los cuatro del aspecto antiguo.
- `services/postventa-api/tests/test_f036_excel_lector.py` (T50, T51): tests
  `r126` de ida y vuelta y del libro sin formato y con el formato antiguo.
- `services/postventa-api/tests/test_f036_lector_aislado.py` (T50): `r126` por
  el hijo real y los `r127`.
- `progress/impl_F-036.md`, `progress/mutacion_F-036_bloque12.md`,
  `progress/current.md` y `specs/F-036-importar-excel/tasks.md` (T50–T54
  marcadas).
- **No tocados**: el lector, `lector_aislado.py`, `ejecutor_aislado.py` y sus
  topes, el dominio, `config/plantilla_incidencias.yaml`, el front, `docs/` y
  `azure-apps/`.

### Commits

| Tarea | Commit |
|---|---|
| T50 | `a505e4a` |
| T51 | `4eba996` |
| T52 | `9e7b781` |
| T53 | `218c9f6` |
| T54 | `33be26e` |

### Evidencias (Bloque 12)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6546 passed, 74 skipped** (970,59 s); `front` en verde (caché). Del bloque: `test_f036_excel_generador.py` 191 passed; los dos del lector 403 passed, 7 skipped |
| Fase RED | `101 failed, 493 passed, 7 skipped` en los tres ficheros sobre HEAD `d64ff0a`, con los invariantes de R126 y las guardas de R127 en verde (T50, arriba) |
| Cobertura de las líneas cambiadas | **99,9 %** (3297/3301, `PUERTA COBERTURA`, rama entera desde `dev`) |
| Mutación | `--base 07bd0c9 --workers 6 --timeout 900`: **60 generados, 60 muertos, 0 supervivientes, 0 timeouts**, 1473,9 s con **6 workers reales**; más **57 mutaciones a mano** (cadenas, decimales, asignaciones quitadas y las que pide T54): **57 caen** |
| Topes (T52) | elementos 26.990 y **149.016** (≤ 150.000, sobran 984); descomprimido 8.578.900 B (sigue en 17 MiB); JSON idéntico; tiempo y memoria del hijo sin cambio apreciable. **Ningún recorte** |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 970,59 s |

### Pendiente y fuera del alcance

- **Nada recortado**: el humano recibe la muestra que aprobó, con bandas,
  impresión y adorno de «Instrucciones».
- **Margen estrecho de elementos (984)** en el Excel de errores más grande:
  para el spec-author y el humano, por si un cambio futuro del generador lo
  pasa (lo vigila `test_f036_r127_…_cabe_en_la_mitad_del_presupuesto`). Las
  cifras nuevas (26.990, 149.016 y 8.578.900) no se han llevado a `design.md`
  §5.2 ni a los docstrings de `lector_aislado.py` (fuera del encargo).
- **No probado aquí**: cómo se ve en Excel de escritorio, en la web y en
  LibreOffice, ni la impresión real. Es lo que verá el humano al repetir T28.
- **MANUAL del humano**: redesplegar el backend con el Bloque 12 y **repetir
  T28** (el `v2` nuevo, ya con formato), y luego **T29** (medir el `v2`
  guardado desde Excel con `scripts/contar_elementos_xml_f036.py`). T27 con
  `-SoloFront` (errata ya anotada en `tasks.md`). **T30**, del líder, la
  última. **F-052** sin tocar.
- `git push` no se ha hecho.

## Bloque 13 (T55–T58) · 2026-10-02 · sin impresión y una sola fila a la vista

Enmienda 10 bis de la spec (`af2b937`): R122, R123, R125, R126 y R127 tal
como quedan; `design.md` §3.6 y §5.2, notas «10 bis». Solo T56 toca código de
producción, y solo el **generador** de `infrastructure/documentos/excel_openpyxl.py`.
T59 (muestra, del líder con el humano) y T60 (mutación) **no** son de este
encargo; tampoco las MANUAL ni T30.

### T55 · el «antes» y la fase RED

**Medición del «antes»**, sobre HEAD `af2b937` (producción con el formato de
la décima, igual que en `50b42b1`), con **el mismo guion** de T50/T52
(`medir_bloque12.py`, en el directorio temporal de la sesión, no versionado),
en la misma máquina y con el mismo método: los dos ficheros de `_legitimos()`
de `tests/test_f036_lector_aislado.py` generados en memoria; elementos
(`lector_aislado._contar_elementos_xml(..., presupuesto=None)`), bytes del
fichero y descomprimidos, bytes y `sha256` del JSON de `leer_en_hijo`; cinco
veces la lectura por el **hijo real** (`LectorPlantillaAislado(entorno="test")`
con el `EjecutorMultiprocessing` de producción envuelto en un espía) y la
memoria en un subproceso aparte sin cobertura (`PeakWorkingSetSize` con
`K32GetProcessMemoryInfo`, y el pico de `tracemalloc` de `leer_en_hijo`).

Comando: `.venv/Scripts/python.exe <scratchpad>/medir_bloque12.py 5` desde
`services/postventa-api` (Windows 11, Python 3.12.7, 22 núcleos). Salida real
(sin las líneas con los nombres de las partes, que son las de T52: 12 en la
plantilla y 15 en el Excel de errores):

```
lector_aislado: sin tope de memoria en esta plataforma
python 3.12.7 · repeticiones=5 · núcleos=22
== plantilla completa
   fichero=61405 B  descomprimido=2749056 B (2.62 MiB)  elementos=26990
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=12
   hijo real, lector aislado entero (s): min=1.89 mediana=2.28 max=3.81  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.70 mediana=2.06 max=3.50
   leer_en_hijo en proceso aparte (s):   min=0.47 mediana=0.50 max=1.38
   pico de proceso, PeakWorkingSetSize (MiB): min=46.29 mediana=46.40 max=47.35  (antes de leer: min=29.96 mediana=29.96 max=30.04)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== Excel de errores más grande
   fichero=141193 B  descomprimido=8578900 B (8.18 MiB)  elementos=149016
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=15
   hijo real, lector aislado entero (s): min=2.35 mediana=2.94 max=3.29  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.81 mediana=2.53 max=2.81
   leer_en_hijo en proceso aparte (s):   min=0.66 mediana=0.72 max=0.86
   pico de proceso, PeakWorkingSetSize (MiB): min=46.45 mediana=46.50 max=46.52  (antes de leer: min=29.85 mediana=29.91 max=29.91)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== plantilla vacía
   fichero=33898 B  descomprimido=293056 B (0.28 MiB)  elementos=10990
   json=316 B  sha256(json)=e5ff022293e69cdf  partes=12
== v2 de prueba (158 filas sin errores, catálogo de los tests)
   fichero=38198 B  descomprimido=379029 B (0.36 MiB)  elementos=13524
   json=225771 B  sha256(json)=e07d490e5ca4640c  partes=12
```

**Salen las de T52**: 26.990 y 149.016 elementos, 8.578.900 B descomprimidos,
el mismo JSON (`466c8afea7b78ef3`). Los bytes del **fichero** difieren en
unos pocos (61.405 frente a 61.408 de T52; 33.898 frente a 33.902): el ZIP
lleva la fecha de creación en `docProps/core.xml` y la compresión cambia unos
bytes de una ejecución a otra; lo descomprimido es idéntico al byte.

| Medida («antes», HEAD `af2b937`) | Plantilla completa | Excel de errores más grande |
|---|---:|---:|
| Elementos XML | 26.990 | **149.016** |
| Bytes del fichero | 61.405 | 141.193 |
| Bytes descomprimidos | 2.749.056 | **8.578.900** |
| Bytes del JSON de `leer_en_hijo` | **5.257.211** | 5.257.211 |
| Hijo real, `leer` entero (mediana; máx.) | 2,28 s; 3,81 s | 2,94 s; 3,29 s |
| Hijo real, `SalidaHijo.segundos` (mediana) | 2,06 s | 2,53 s |
| Pico de proceso leyendo (`PeakWorkingSetSize`, mediana; máx.) | 46,4 MiB; 47,4 MiB | 46,5 MiB; 46,5 MiB |
| Pico de `tracemalloc` de `leer_en_hijo` | 20,59 MiB | 20,59 MiB |
| `v2` de prueba (158 filas): elementos | 13.524 | — |

**Fase RED.** Tests cambiados y nuevos según `design.md` §3.6, «Cómo se
prueba, tras la enmienda 10 bis», con los valores **literales**.

`tests/test_f036_excel_generador.py`:

| Test | Qué comprueba | Cambio |
|---|---|---|
| `test_f036_r122_cuerpo_de_incidencias` | bordes del cuerpo a `SIN_BORDES` | cambiado (de la lista) |
| `test_f036_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo` | vacía, rellena y Excel de errores × filas 2, 3, 500, 1001 × columnas A, H, I: sin borde ni relleno fijos, salvo la celda con error (`FFFEF2F2`, fuente `FFB91C1C`); fuente, alineación, bloqueo y `@` estáticos | **nuevo** |
| `test_f036_r122_r123_la_plantilla_lleva_las_tres_reglas_condicionales` | vacía y rellena: tres reglas, en orden, con `sqref`, tipo, fórmula literal, prioridad 1-2-3, `stopIfTrue` `None` y `dxf` (los cuatro lados `thin` `FFDFE2E4` sin relleno ni fuente; `bgColor` `FFF3F4F5` y `FFFAFAFB` sin borde ni fuente); ninguna en «Instrucciones» | cambiado y **renombrado**: era `…_r122_bandas_alternas_una_sola_regla_condicional_en_la_plantilla` |
| `test_f036_r122_el_v2_sin_errores_lleva_las_bandas` | tres reglas | cambiado (de la lista) |
| `test_f036_r122_las_bandas_dependen_de_los_errores_y_no_del_origen` | tres reglas | cambiado (de la lista) |
| `test_f036_r122_con_alguna_fila_con_error_no_hay_regla_de_bandas` (5 casos) | dos reglas, la 1 y la 2 | cambiado y **renombrado**: era `…_con_alguna_fila_con_error_no_hay_regla_condicional` |
| `test_f036_r122_r123_las_reglas_en_el_xml` (vacía, rellena, errores) | en el XML: los `sqref` en orden y sin espacios, tantos `<conditionalFormatting`/`<cfRule` como reglas, `<dxfs count="3">` (o `"2"`), ninguno en las otras tres hojas | **nuevo** |
| `test_f036_r123_la_columna_errores_va_en_gris_no_editable` | `I` sin relleno ni borde fijos; el gris, por la regla 2 | cambiado (de la lista) |
| `test_f036_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo` | sin borde fijo | cambiado (de la lista) |
| `test_f036_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo` | sin borde fijo | **cambiado, NO estaba en la lista** (abajo) |
| `test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario` | ninguna celda sin error con relleno fijo, tampoco en `Errores` | cambiado (de la lista) |
| `test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion` (2 libros × 4 hojas) | `print_area` `''`, títulos `None`, ningún nombre definido de hoja, `orientation`/`paperSize`/`scale`/`fitToWidth`/`fitToHeight` `None`, sin `fitToPage`, `print_options` sin centrado, cuadrícula ni encabezados, márgenes `(0.75, 0.75, 1.0, 1.0, 0.5, 0.5)`, los tres trozos de los seis encabezados y pies `None`, sin saltos | **funde** `…_r125_impresion_de_incidencias` y `…_r125_instrucciones_sin_ajustes_de_impresion_propios` (de la lista), parametrizado por hoja |
| `test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml` (plantilla, errores) | ni `<pageSetup`, `<printOptions`, `<headerFooter`, `<rowBreaks`, `<colBreaks` ni `fitToPage` en las cuatro hojas; ningún `_xlnm.Print_` en `xl/workbook.xml`; nombres definidos: los seis de las listas y `_xlnm._FilterDatabase` | **nuevo** |

`tests/test_f036_lector_aislado.py`:

| Test | Cambio |
|---|---|
| `test_f036_r127_la_plantilla_completa_lleva_tres_reglas_condicionales_de_un_rango` | cambiado y **renombrado** (era `…_lleva_una_regla_condicional_de_un_rango`): tres `<conditionalFormatting>` en el orden y con los rangos de §3.6, una `<cfRule>` cada uno, ninguno en otra hoja, tres `<dxf>` y `<dxfs count="3">` |
| `test_f036_r127_el_excel_de_errores_mas_grande_lleva_dos_reglas_condicionales` | cambiado y **renombrado** (era `…_no_lleva_regla_condicional`): dos (`A2:I1001`, `I2:I1001`) y dos `<dxf>` |
| `test_f036_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real` | solo el comentario que hablaba del nombre de los títulos de impresión |
| `test_f036_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real` (`decima`, `antiguo`) | **nuevo**: por el hijo real, el mismo `LibroLeido` que el lector en proceso y que el libro con el formato nuevo; la de la décima valida con cero errores |

`tests/test_f036_excel_lector.py`:

| Test | Cambio |
|---|---|
| `_con_formato_de_la_decima` (ayudante del test, no de producción) | **nuevo**: a la generada le quita las reglas y le pone como estilo de celda los bordes `thin` `FFDFE2E4` en `A2:I1001` y `FFF3F4F5` en `I2:I1001`, la regla única `MOD(ROW(),2)=1` en `A2:H1001` y la impresión de la R125 retirada, con `print_title_rows = "1:1"` |
| `test_f036_r126_una_plantilla_con_el_formato_de_la_decima_se_importa_igual` | **nuevo**: comprueba que el libro construido es de verdad el de la décima (bordes, gris, la regla, títulos `$1:$1`, apaisado y `_xlnm.Print_Titles` en `workbook.xml`), que da el mismo `LibroLeido` que el formato nuevo y que valida con cero errores |
| `_sin_formato` | sin tocar: sigue quitando ajustes de impresión (ya no hay; no estorba) |

**Desviación respecto a la lista de §3.6, dicha.**
`test_f036_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo` no está en la
lista de tests que cambian a propósito, pero comprobaba
`_bordes(celda) == BORDES_DEL_CUERPO` en celdas del cuerpo del Excel de
errores: es justo el «cuerpo estático» que R122 retira («**Ninguna** celda del
cuerpo debe llevar borde ni relleno estáticos»). Con T56 caería sí o sí. La
única línea cambiada es esa, a `SIN_BORDES`; lo demás que comprueba (sin
relleno, tinta, sin comentario) sigue igual. Ningún otro test existente se ha
tocado. Los cuatro renombrados lo son porque su nombre afirmaba lo contrario
de lo que ahora comprueban («una sola regla», «no hay regla condicional»).

Comando (la verificación de T55), desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py -q -p no:cacheprovider --tb=line`.
Resumen real. De la traza se copian solo el resumen, los nombres y los
motivos; la salida no lleva ningún `repr` de `Ajustes` (`grep -c "Ajustes("`
→ 0):

```
102 failed, 540 passed, 7 skipped in 354.40s (0:05:54)
```

Los 102 en rojo, por test:

```
      5 test_f036_r122_con_alguna_fila_con_error_no_hay_regla_de_bandas
     32 test_f036_r122_cuerpo_de_incidencias
      1 test_f036_r122_el_v2_sin_errores_lleva_las_bandas
      1 test_f036_r122_las_bandas_dependen_de_los_errores_y_no_del_origen
      1 test_f036_r122_r123_la_plantilla_lleva_las_tres_reglas_condicionales
      3 test_f036_r122_r123_las_reglas_en_el_xml
     36 test_f036_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo
      3 test_f036_r123_celda_con_error_en_rojo_suave_con_el_texto_en_rojo
      8 test_f036_r123_la_columna_errores_va_en_gris_no_editable
      5 test_f036_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo
      2 test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml
      2 test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion
      1 test_f036_r127_el_excel_de_errores_mas_grande_lleva_dos_reglas_condicionales
      1 test_f036_r127_la_plantilla_completa_lleva_tres_reglas_condicionales_de_un_rango
      1 test_f036_r64_celdas_con_error_marcadas_con_relleno_y_comentario
```

Los motivos, uno por fallo (102), de las líneas `fichero:línea: motivo` de
la salida; la coordenada sola (`AssertionError: A2`…) se agrupa como
`<coordenada>`:

```
     40 AssertionError: assert {'izquierdo':..., 'FFDFE2E4')} == {'izquierdo':... (None, None)}   (borde fijo en el cuerpo)
     37 AssertionError: <coordenada>                                    (36 del test nuevo y el `I2` de R64: borde o relleno fijo)
      8 AssertionError: assert ('solid', 'FFF3F4F5') == (None, None)    (gris fijo en `Errores`)
      5 AssertionError: assert [] == ['A2:I1001', 'I2:I1001']            (Excel de errores sin reglas)
      3 AssertionError: assert [b'A2:H1001'] == [b'A2:I1001',..., b'A2:H1001']
      3 AssertionError: assert ['A2:H1001'] == ['A2:I1001', ...', 'A2:H1001']   (una regla, no tres)
      2 assert '$1:$1' is None                                          (títulos de impresión)
      2 AssertionError: assert [] == [b'A2:I1001', b'I2:I1001']
      2 AssertionError: ('xl/worksheets/sheet1.xml', b'<pageSetup')
```

Los 6 casos de `…_r125_ninguna_hoja…` de «Instrucciones», `_catalogos` y
`_plantilla` (2 libros × 3 hojas) ya pasan sobre HEAD: esas hojas nunca
llevaron impresión. Los de «Incidencias» caen.

**En verde sobre HEAD, a propósito** (invariantes de R126): `-k r126` en los
dos ficheros del lector → `11 passed`:

```
PASSED test_f036_excel_lector.py::test_f036_r126_ida_y_vuelta_de_la_plantilla_rellena_con_formato
PASSED test_f036_excel_lector.py::test_f036_r126_ida_y_vuelta_del_excel_de_errores_con_formato
PASSED test_f036_excel_lector.py::test_f036_r126_sin_el_formato_se_lee_el_mismo_libro[vacia]
PASSED test_f036_excel_lector.py::test_f036_r126_sin_el_formato_se_lee_el_mismo_libro[rellena]
PASSED test_f036_excel_lector.py::test_f036_r126_sin_el_formato_se_lee_el_mismo_libro[errores]
PASSED test_f036_excel_lector.py::test_f036_r126_una_plantilla_con_el_formato_antiguo_se_importa_igual
PASSED test_f036_excel_lector.py::test_f036_r126_una_plantilla_con_el_formato_de_la_decima_se_importa_igual
PASSED test_f036_lector_aislado.py::test_f036_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real[rellena]
PASSED test_f036_lector_aislado.py::test_f036_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real[errores]
PASSED test_f036_lector_aislado.py::test_f036_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real[decima]
PASSED test_f036_lector_aislado.py::test_f036_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real[antiguo]
```

`ruff check` de los tres ficheros (con el `ruff` del `.venv` de la raíz,
lanzado desde `services/postventa-api`): `All checks passed!`.

### T56 · el generador sin impresión y con el cuerpo por formato condicional

Solo `services/postventa-api/infrastructure/documentos/excel_openpyxl.py`, y
dentro, solo `_incidencias`, las constantes y el docstring del módulo:

- **Fuera**: el bloque «Impresión (R125)» entero (`orientation`, `paperSize`,
  `fitToWidth`, `fitToHeight`, `pageSetUpPr.fitToPage`, `print_title_rows`,
  márgenes laterales y `oddFooter`) y las constantes `MARGEN_LATERAL` y
  `PIE_DE_PAGINA` (ningún otro sitio las usaba).
- **El bucle del cuerpo** deja de poner `border` en las 9.000 celdas y `fill`
  en las de `Errores`. Conserva fuente, alineación, `Protection(locked=False)`
  y `FORMATO_TEXTO` en las columnas de datos, y la fuente gris de `Errores`.
- **La celda con error**, sin cambios: `RELLENO_ERROR` y `FUENTE_ERROR`
  estáticos y su comentario (ya no tiene borde fijo que conservar).
- **Las tres reglas**, en este orden y con los rangos construidos con
  `PRIMERA_FILA`/`ULTIMA_FILA` y las letras de la cabecera: 1 · `A2:I1001`,
  `FORMULA_PINTADA`, `border=_borde_fino()`; 2 · `I2:I1001`,
  `FORMULA_PINTADA`, `PatternFill(fill_type="solid", bgColor=LIENZO)`;
  3 · `A2:H1001`, `FORMULA_BANDAS`, `bgColor=BANDA`, **solo si**
  `not any(fila.errores for fila in filas)`. `openpyxl` les da la prioridad 1,
  2, 3 por orden de alta; ninguna con `stopIfTrue`.
- **Constantes**: `FORMULA_PINTADA = "OR(ROW()=2,COUNTA($A2:$I2)>0)"` (nueva) y
  `FORMULA_BANDAS = "AND(MOD(ROW(),2)=1,COUNTA($A2:$I2)>0)"` (valor nuevo).
  El comentario de `ANCHOS` ya no habla del A4. El docstring del módulo dice
  que el cuerpo se pinta por formato condicional en las filas pintadas y que
  no hay ajustes de impresión.
- **No cambian**: `_instrucciones`, `_texto`, `_catalogos`, `_metadatos`,
  `_validacion`, la firma de `generar`, la protección, el filtro, los
  paneles, el comentario del error ni nada bajo «El lector».

Lo que sale ahora (sondeo en memoria de la plantilla vacía, guion del
directorio temporal): `xl/workbook.xml` con los seis nombres de las listas y
`_xlnm._FilterDatabase`, **sin** `_xlnm.Print_Titles`; en las cuatro hojas,
solo `<pageMargins>` con los valores por defecto (`0.75 0.75 1 1 0.5 0.5`),
ni `<pageSetup>` ni `<headerFooter>`.

**Verificación de T56**, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_lector_aislado.py tests/test_f036_migracion.py tests/test_f036_importar_http.py tests/test_f036_arquitectura.py -q -p no:cacheprovider --tb=short`
(sin ningún `repr` de `Ajustes` en la salida):

```
884 passed, 7 skipped in 324.54s (0:05:24)
```

Con los de T55 incluidos y los hostiles de R4-1 **sin tocar** (los 16 por el
hijo real y `…_los_ficheros_de_r4_1_son_los_que_dicen_ser`, en verde dentro
de esa pasada): el constructor «formato-condicional» sigue insertando su
`<conditionalFormatting>` hostil delante de `<dataValidations`, detrás de los
tres legítimos, y no contaba reglas. El generador solo:
`tests/test_f036_excel_generador.py` → `236 passed in 21.31s`.

`git diff 26a190e -- services/postventa-api/infrastructure/documentos/lector_aislado.py services/postventa-api/infrastructure/documentos/ejecutor_aislado.py`
→ vacío (0 bytes). `ruff check` de `excel_openpyxl.py`: `All checks passed!`.

### T57 · los topes, medidos otra vez (PARADA condicionada: **no hizo falta**)

Mismo guion (`medir_bloque12.py 5`), misma máquina, mismo método que T55,
sobre `89078a9` (T56). Salida real (las partes, iguales a las de T55: `diff`
de las líneas `partes:` vacío):

```
lector_aislado: sin tope de memoria en esta plataforma
python 3.12.7 · repeticiones=5 · núcleos=22
== plantilla completa
   fichero=61284 B  descomprimido=2749298 B (2.62 MiB)  elementos=26998
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=12
   hijo real, lector aislado entero (s): min=1.76 mediana=1.79 max=2.06  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.59 mediana=1.59 max=1.86
   leer_en_hijo en proceso aparte (s):   min=0.42 mediana=0.43 max=0.45
   pico de proceso, PeakWorkingSetSize (MiB): min=46.09 mediana=46.59 max=47.41  (antes de leer: min=29.86 mediana=29.99 max=30.01)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== Excel de errores más grande
   fichero=141163 B  descomprimido=8579139 B (8.18 MiB)  elementos=149025
   json=5257211 B  sha256(json)=466c8afea7b78ef3  partes=15
   hijo real, lector aislado entero (s): min=1.62 mediana=1.68 max=1.78  filas=1000
   hijo real, SalidaHijo.segundos (s):   min=1.33 mediana=1.36 max=1.50
   leer_en_hijo en proceso aparte (s):   min=0.38 mediana=0.44 max=0.46
   pico de proceso, PeakWorkingSetSize (MiB): min=46.55 mediana=46.61 max=47.44  (antes de leer: min=29.92 mediana=29.94 max=29.98)
   pico de tracemalloc de leer_en_hijo (MiB): min=20.59 mediana=20.59 max=20.59
== plantilla vacía
   fichero=33799 B  descomprimido=293298 B (0.28 MiB)  elementos=10998
   json=316 B  sha256(json)=e5ff022293e69cdf  partes=12
== v2 de prueba (158 filas sin errores, catálogo de los tests)
   fichero=38102 B  descomprimido=379271 B (0.36 MiB)  elementos=13532
   json=225771 B  sha256(json)=e07d490e5ca4640c  partes=12
```

| Medida | Antes (T55) | Después (T56) | Margen que hay que conservar | ¿Cabe? |
|---|---:|---:|---|---|
| Elementos XML, plantilla completa | 26.990 | 26.998 (+8) | < 60.000 | **Sí**, sobran 33.002 |
| Elementos XML, Excel de errores más grande | 149.016 | 149.025 (+9) | ≤ 150.000 (guarda de calibración, R7-3) | **Sí**, sobran **975** |
| Bytes descomprimidos, el mayor (el Excel de errores) | 8.578.900 | 8.579.139 (+239) | ≤ 8.912.896 | **Sí**, sobran 333.757; el doble, 17.158.278 B, sigue redondeando a **17 MiB** |
| Bytes del JSON de `leer_en_hijo`, el mayor | 5.257.211 | 5.257.211 (**idéntico**, mismo `sha256` `466c8afea7b78ef3`) | ≤ 5.767.168 | **Sí**, sobran 509.957; el doble sigue en **11 MiB** |
| Tiempo del hijo real, plantilla completa (`leer` entero, mediana; máx.) | 2,28 s; 3,81 s | 1,79 s; 2,06 s | ≤ 15 s y ≤ +25 % | **Sí** (−21 %) |
| Tiempo del hijo real, Excel de errores más grande | 2,94 s; 3,29 s | 1,68 s; 1,78 s | ≤ 15 s y ≤ +25 % | **Sí** (−43 %) |
| Pico de memoria leyendo (`PeakWorkingSetSize`, mediana), el mayor | 46,5 MiB | 46,6 MiB | ≤ 512 MiB y ≤ +25 % | **Sí** (sin cambio) |
| Pico de `tracemalloc` de `leer_en_hijo` | 20,59 MiB | 20,59 MiB | (referencia) | Igual |
| Bytes del fichero (plantilla; Excel de errores) | 61.405; 141.193 | 61.284; 141.163 | (sin margen escrito; ≤ 2 MiB de R15) | Sí |
| Partes del ZIP (plantilla; Excel de errores) | 12; 15 | 12; 15 (las mismas) | ninguna parte nueva ni imagen | **Sí** |
| `v2` de prueba (158 filas, catálogo de los tests) | 13.524 | 13.532 | < 60.000 (un quinto) | **Sí** |

- **Elementos**: +8 en la plantilla y +9 en el Excel de errores, por debajo
  de la estimación de §5.2 (+15): las reglas y sus `dxf` suman, y se van el
  `<pageSetup>`, el `<headerFooter>` con su `<oddFooter>` y el nombre
  `_xlnm.Print_Titles`; los estilos fijos que se quitan solo cambian `xf`
  deduplicados. El margen frente a la guarda de calibración pasa de **984 a
  975** (frente al rechazo, 300.000, siguen sobrando unos 151.000; R7-3).
- **El tiempo sale mejor, y no es por el formato**: el lector no lee estilos
  y el JSON es idéntico al byte. La diferencia es la carga de la máquina, que no
  se controla entre una pasada y otra (el máximo de la plantilla en T55,
  3,81 s, es un pico aislado), el mismo ruido de ±10–25 % que se vio en T52. Lo que la regla pide —no más de
  un 25 % peor y por debajo de 15 s— se cumple con holgura; no se ha medido
  intercalando porque no hay nada que separar: no empeora.

El `v2` de prueba también por el script de T37, sobre el fichero escrito en
el directorio temporal de la sesión (y borrado después):
`.venv/Scripts/python.exe scripts/contar_elementos_xml_f036.py "<scratchpad>\b13\v2_de_prueba_10bis.xlsx"`:

```
Elementos XML: 13532
Presupuesto (R117): 300000
Un quinto del presupuesto: 60000
Veredicto: por debajo de un quinto del presupuesto
```

Es un `v2` **sintético** (158 filas sin errores con el catálogo de los
tests), no el de la migración real: el de verdad lo mide el humano en T29.

**Regla de decisión: caso 1, todo cabe. NINGÚN RECORTE.** Van las tres
reglas (líneas, gris de `Errores` y bandas), el relleno alterno de los
ejemplos y las celdas de adorno de «Instrucciones», tal como la 10 bis.
Ningún tope tocado:
`git diff 26a190e -- services/postventa-api/infrastructure/documentos/lector_aislado.py services/postventa-api/infrastructure/documentos/ejecutor_aislado.py`
→ vacío (0 bytes).

**Verificación de T57**, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_lector_aislado.py tests/test_f036_excel_lector.py -q -p no:cacheprovider --tb=short`
→ `406 passed, 7 skipped in 193.19s (0:03:13)`, con el `git diff 26a190e` de
T56 vacío.

### T58 · documentación: búsqueda hecha, **nada que cambiar**

Búsqueda (sin distinguir mayúsculas) de `imprim|impresi|apaisad|A4|página`
en los cinco sitios de la tarea:

| Fichero | Lo que aparece | ¿Habla de imprimir este Excel o de su aspecto? |
|---|---|---|
| `docs/ARCHITECTURE.md` | l. 71, 74, 78, 85 y 92: las páginas de los **partes** escaneados y su pie «Página N» (F-002), y lo que «imprime Sigrid»; l. 646: «tienen su página en» el front; l. 809: «todas las páginas» de Graph | No |
| `docs/INTEGRACION.md` | l. 457: la unidad «que imprime el» parte; l. 510–513: paginación de Graph; l. 1138, 1142: páginas del front; l. 1180: recargar la página del navegador | No |
| `services/postventa-front/importar.html` | ninguna coincidencia | — |
| `services/postventa-api/config/plantilla_incidencias.yaml` (textos de «Instrucciones») | ninguna coincidencia | — |
| `azure-apps/postventa_incidencias.md` | l. 58: «dos páginas del front»; l. 592: la unidad «que imprime el» parte; l. 645–648: paginación de Graph; l. 1292, 1296: páginas del front; l. 1334: recargar la página | No |

Ninguna mención a imprimir la plantilla o el Excel de errores, ni a su
aspecto: **no se cambia nada** (ni aquí ni en `azure-apps`, donde no hay
commit). El cambio no toca lo que el servicio expone ni consume.

Verificación, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_documentacion.py tests/test_f010_integracion_expuesto.py -q -p no:cacheprovider`
→ `84 passed in 0.48s`.

### `bash harness/init.sh` al acabar el bloque

Una vez, tal cual, sobre `3eab450` (T58). Salida real, las líneas que importan
(sin ningún `repr` de `Ajustes`: `grep -c "Ajustes("` → 0):

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 4.72s
[OK] pytest en verde (con medición de cobertura)
6594 passed, 74 skipped in 832.83s (0:13:52)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3289 líneas cambiadas cubiertas (3285/3289, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

`init.sh` **no** lanza la mutación (lo dice el propio guion: «La campaña de
mutación NO corre aquí»); no ha exigido nada de mutación para estar en verde.
Los avisos de `ruff` son deuda previa: `excel_openpyxl.py` y los tres
ficheros de tests de este bloque pasan `ruff check` sin avisos.

### Ficheros tocados (Bloque 13)

- `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` (T56):
  solo `_incidencias`, las constantes (`FORMULA_PINTADA` nueva,
  `FORMULA_BANDAS` con valor nuevo, fuera `MARGEN_LATERAL` y `PIE_DE_PAGINA`,
  el comentario de `ANCHOS`) y el docstring del módulo.
- `services/postventa-api/tests/test_f036_excel_generador.py` (T55): los de
  la lista de §3.6, más `…_r123_la_vecina_sin_error_…` (dicho en T55), y los
  nuevos `…_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo`,
  `…_r122_r123_las_reglas_en_el_xml` y
  `…_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml`.
- `services/postventa-api/tests/test_f036_excel_lector.py` (T55): el ayudante
  `_con_formato_de_la_decima` y su test de R126.
- `services/postventa-api/tests/test_f036_lector_aislado.py` (T55): los dos
  `r127` de las reglas, el comentario del `r126` y el `r126` nuevo de los
  formatos anteriores por el hijo real.
- `progress/impl_F-036.md`, `progress/current.md` y
  `specs/F-036-importar-excel/tasks.md` (T55–T58 marcadas).
- **No tocados**: el lector, `lector_aislado.py`, `ejecutor_aislado.py` y sus
  topes, el dominio, `config/plantilla_incidencias.yaml`, el front, `docs/` y
  `azure-apps/`. Ningún `.xlsx` en git ni en OneDrive.

### Commits

| Tarea | Commit |
|---|---|
| T55 | `8330529` |
| T56 | `89078a9` |
| T57 | `322a4d0` |
| T58 | `3eab450` |

### Evidencias (Bloque 13, T55–T58)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6594 passed, 74 skipped** (832,83 s); `front` en verde (caché). Del bloque: los seis ficheros de T56, **884 passed, 7 skipped**; el generador solo, 236 passed |
| Fase RED | `102 failed, 540 passed, 7 skipped` en los tres ficheros sobre HEAD `af2b937`, con los 11 invariantes de R126 (formato nuevo, antiguo y de la décima, por los dos lectores) en verde |
| Cobertura de las líneas cambiadas | **99,9 %** (3285/3289, `PUERTA COBERTURA`, rama entera) |
| Mutación | **No lanzada en esta tanda** (es T60, tras el visto bueno del humano en T59): `python -m harness.mutacion --feature F-036 --base 26a190e --timeout 900`. Sin números todavía |
| Topes (T57) | elementos 26.998 y **149.025** (≤ 150.000, sobran 975); descomprimido 8.579.139 B (sigue en 17 MiB); JSON idéntico; tiempo y memoria del hijo sin empeorar. **Ningún recorte** |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 832,83 s |

### Pendiente y fuera del alcance

- **Nada recortado**: van las tres reglas, el relleno alterno de los ejemplos
  y las celdas de adorno de «Instrucciones».
- **Un test cambiado fuera de la lista de §3.6**:
  `test_f036_r123_la_vecina_sin_error_no_lleva_ni_relleno_ni_rojo` (una línea,
  `BORDES_DEL_CUERPO` → `SIN_BORDES`, forzada por R122). Y cuatro tests
  **renombrados** porque su nombre afirmaba lo contrario de lo que ahora
  comprueban (tabla de T55). Para el reviewer.
- **No probado aquí**: cómo se ve en Excel (una sola fila a la vista, que se
  pinte al escribir, las bandas, el gris), en la web ni en LibreOffice. Es T59
  (muestra del líder con el humano) y luego la T28 repetida.
- **T59** (líder y humano), **T60** (mutación, tras el visto bueno de T59),
  la review 8, el redespliegue, T28 repetida, T29 y **T30**: fuera de este
  encargo.
- `git push` no se ha hecho.

## T59–T60 · 2026-10-02 · la muestra con el visto bueno del humano y la mutación de la enmienda 10 bis

### T59 · hecha (líder y humano)

El líder generó las tres muestras (`MUESTRA_plantilla_vacia.xlsx`,
`MUESTRA_creacion_incidencias_v2.xlsx` y `MUESTRA_excel_de_errores.xlsx`) en la
carpeta de OneDrive, **sin versionar nada**: el informe del `v2` de muestra fue
a su scratchpad y `progress/migracion_F-036.md` quedó intacto. El humano dio su
**visto bueno** («ok»). Preguntó además si la plantilla mantiene el
desplegable en las 1.000 filas aunque estén vacías: el líder le confirmó que sí
(R126; las validaciones no cambian con la 10 bis). Marcada `[x]` en
`tasks.md` con esta constancia. Este encargo no ha tocado ninguna muestra ni
ningún `.xlsx`.

### T60 · la campaña de la herramienta

Comando, desde la raíz (con el `.venv` de la raíz):
`python -m harness.mutacion --feature F-036 --base 26a190e --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque13.md`.
Salida real, entera:

```
F-036: 1 fichero(s), 49 línea(s) de producción (origen rama, 26a190e87f4e47ba654065bf7c514d7b739c2475..feature/F-036-importar-excel)
Campaña paralela: hasta 6 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-036_bloque13.md
```

- **Alcance**: solo `excel_openpyxl.py`, 49 líneas añadidas o cambiadas
  desde `26a190e` (las borradas, como el bloque de impresión, no son líneas
  del alcance: ya no existen).
- **0 mutantes, y es real, no un fallo de la herramienta.** Lo comprobé con un
  sondeo aparte (`sondeo_b13.py`, en el scratchpad, sin versionar), que llama
  a `harness.mutacion.generar_mutantes` sobre esas 49 líneas: `mutantes: 0`
  (sobre el fichero entero, 177). Las 49 son el docstring del módulo,
  comentarios, las dos constantes de fórmula (**cadenas**: `ROW()=2`, `>0`,
  `MOD(...)=1` van dentro del texto), `errores = _letra(...)` y las dos
  llamadas `ws.conditional_formatting.add(...)` con sus f-strings. La
  herramienta solo muta comparaciones, aritmética, lógicos, `not`, booleanos y
  enteros de Python, y ahí no hay ninguno. (La línea `if not any(...)` de la
  regla 3 no cambió desde `26a190e`; sus mutantes ya los mató T54.)
- **Workers reales: 1** (pedidos 6). El informe dice «Workers | 1» y su
  cabecera, `--workers 1`: con cero mutantes, `ejecutar_campania_paralela`
  arranca `max(1, min(6, 0)) = 1` y no crea ningún worktree (R8 del arnés).
  Sin timeouts.
- Como la herramienta no ve nada aquí, **todo el peso está en las mutaciones a
  mano**, que es lo que T60 pide además.

### T60 · mutaciones a mano (85, todas caen)

Guion `mutar_a_mano_b13.py` (scratchpad, sin versionar). **En una copia
desechable**, como pide la tarea, no en el árbol: un `git worktree add
--detach` de HEAD (`674107c`) en el scratchpad, con el intérprete del `.venv`
de `services/postventa-api` y `cwd` en la copia (comprobado antes que
`excel_openpyxl.__file__` resolvía dentro de la copia, no en el árbol). Cada
mutación sola; `pytest -x -q --tb=no -rf -p no:cacheprovider
tests/test_f036_excel_generador.py`; muerta solo con `rc=1`; el fichero de la
copia restaurado tras cada una. Base sin mutar en verde: `236 passed`. Del
`-rf` se guardó solo el **nombre** del primer test caído, nunca el mensaje.
Resultado: `total=85 supervivientes=0 [] raros=0 []`.

| Grupo | Mutaciones (cada una, sola) | Caen | Primer test que las caza |
|---|---|---|---|
| **Volver a poner la impresión de la décima** (T60) | cada línea por separado: `orientation = "landscape"`; `paperSize = A4`; `fitToWidth = 1`; `fitToHeight = 0`; `fitToPage = True`; `print_title_rows = "1:1"`; margen izquierdo 0,4; margen derecho 0,4; el pie; y el bloque entero de una vez | 10/10 | `…_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]` |
| **M18b, M18, M27, M28, M29** (T60) | `print_area = "A1:I50"`; `"A1:I1001"`; `page_setup.scale = 50`; `horizontalCentered = True`; margen superior 0 | 5/5 | el mismo |
| Más impresión, por si algo se escapaba | centrado vertical; imprimir cuadrícula; imprimir encabezados; encabezado de página; pie de la primera página; `print_title_cols = "A:A"`; un salto de página; margen inferior 0 | 8/8 | el mismo |
| Impresión en las otras hojas | `orientation` en «Instrucciones»; `print_area` en «Instrucciones»; `orientation` en `_catalogos`; en `_plantilla` | 4/4 | `…_r125_ninguna_hoja…[Instrucciones-plantilla]`, `[_catalogos-plantilla]`, `[_plantilla-plantilla]` |
| **Cuerpo estático otra vez** (T60) | borde fijo en todo el cuerpo; solo en las columnas de datos; solo en `Errores`; `LIENZO` fijo en `Errores`; borde fijo solo en las filas con datos (`A`); borde fijo en la celda con error; banda fija en `B` de las filas impares con datos | 7/7 | `…_r122_cuerpo_de_incidencias[A-2]`, `…_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo[…]`, `…_r64_celdas_con_error_marcadas…`, y la última `…_r7_ninguna_celda…es_formula` (*) |
| **Fórmulas** (T60: `ROW()=2`→`ROW()=1`, quitar la `I` del `COUNTA`) | `ROW()=1`; `$I2`→`$H2` en la pintada y en la de bandas; `>0`→`>=0` en las dos; `OR`→`AND`; `AND`→`OR`; `MOD(...)=1`→`=0`; `$A2`→`A2`; `$I2`→`$I$2`; la regla 1 con la fórmula de bandas; la 2 con la de bandas; la 3 con la pintada | 13/13 | `…_r122_r123_la_plantilla_lleva_las_tres_reglas_condicionales` |
| **`sqref`** (T60: la 2 a `A2:I1001`, la 3 a `Errores`) | la 2 a `A2:I1001`; la 3 hasta `I`; la 1 sin `I` (`A2:H1001`); la 1 hasta la 1000; la 1 desde la fila 1; la 3 desde la 3; la 2 en `H` | 7/7 | el mismo |
| **Orden de alta y prioridad** (T60) | la 2 antes que la 1; la 3 antes que la 2; la 3 la primera; prioridades invertidas sin cambiar el orden (`10 - p`); todas 1; todas `+1` | 6/6 | el mismo |
| **`stopIfTrue`** (T60) | `True` en la 1, en la 2, en la 3; `False` explícito en la 1 (el test exige `None`) | 4/4 | el mismo |
| **La regla 3 en el Excel de errores** (T60) | `if True:`; la condición invertida (`if any(...)`) | 2/2 | `…_r122_r123_las_reglas_en_el_xml[errores]`; `…_tres_reglas_condicionales` |
| El `dxf` de cada regla | la 1 con el borde de la cabecera; la 1 con relleno además; la 2 en `fgColor`; la 2 con el color de las bandas; la 2 con fuente; la 2 con borde; la 3 con el gris; la 3 en `fgColor` | 8/8 | `…_tres_reglas_condicionales` |
| **El rojo de la celda con error** (T60) | sin relleno; sin color de fuente; la fuente en tinta | 3/3 | `…_r64_celdas_con_error…`; `…_sin_bordes_ni_relleno…[A-2-errores]` |
| **Lo estático que se conserva** (T60: desbloqueo, `@`, fuente) | sin desbloqueo; sin `@`; sin fuente en las columnas de datos; sin fuente en `Errores`; sin alineación; todas `arriba` sin ajuste; `Errores` desbloqueada; el cuerpo solo hasta la fila 1000 | 8/8 | `…_r2_celdas_de_datos_desbloqueadas_y_como_texto[Unidad]`, `…_r122_cuerpo…[A-2]`, `…_sin_bordes…[I-2-vacia]`, `…_r2_textos_largos_con_ancho_y_ajuste[…]`, `…_r2_la_columna_errores_y_la_cabecera_quedan_bloqueadas` |

(*) La «banda fija en `B`» del guion se escribió como expresión condicional
que reasignaba el relleno de la celda a sí misma en las filas pares, y con
`-x` cayó por un test ajeno (R7). No la cuento como prueba de nada: la repetí
limpia (`if numero % 2: ws[f"B{numero}"].fill = _solido(BANDA)`) y sin `-x`:
`1 failed, 235 passed`, y el único que la cazaba era
`…_r64_celdas_con_error…`, **en el Excel de errores**. Eso destapó el hueco
de abajo.

### T60 · un hueco encontrado y cerrado con un test (fase RED)

**El hueco.** `…_r122_sin_bordes_ni_relleno_estaticos_en_el_cuerpo` muestrea
solo las columnas **A, H e I** (filas 2, 3, 500 y 1001) de los tres libros, y
`…_r122_cuerpo_de_incidencias` mira todas las columnas pero solo de la
plantilla **vacía**. Un estilo fijo puesto en una columna de **B a G** y solo
en las **filas con datos** de un libro **sin errores** (la plantilla rellena,
es decir, el `v2`) no lo cazaba nadie. Tres mutantes lo prueban, cada uno
solo, con el fichero de tests de HEAD: relleno de banda fijo en `B`, borde
fino fijo en `C`, fuente roja fija en `D` (guion `hueco_b13.py`, scratchpad,
sobre la misma copia desechable):

```
== hueco 1
236 passed in 24.57s
== hueco 2
236 passed in 23.04s
== hueco 3
236 passed in 31.21s
```

Tres supervivientes reales, no equivalentes: el humano vería un relleno, una
línea o un texto rojo fijos en el `v2`, justo lo que la 10 bis quita.

**El test** (nuevo, en `tests/test_f036_excel_generador.py`):
`test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas`,
parametrizado por los tres libros (`vacia`, `rellena`, `errores`). Recorre las
**9.000 celdas** `A2:I1001` y exige en cada una: sin bordes; sin relleno y con
la fuente de su columna (salvo las tres celdas con error del Excel de errores,
con su rojo); y lo estático que se conserva (alineación con su ajuste, bloqueo
y `@`/`General`). Junta las coordenadas distintas, y la lista debe salir
vacía. En verde sobre producción: `3 passed, 236 deselected in 4.27s`.

**RED, contra los mutantes del hueco** (más tres del mismo tipo para lo
estático: `E` bloqueada, `F` con formato `General`, `G` centrada en vertical),
cada uno solo, sobre la copia desechable con el test nuevo. Comando, desde
`services/postventa-api` de la copia:
`python -m pytest tests/test_f036_excel_generador.py -q --tb=line -rf -p no:cacheprovider`.
Salida real (sin el mensaje largo de `-rf`):

```
== hueco 1
E   AssertionError: assert ['B2', 'B3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 32.42s
== hueco 2
E   AssertionError: assert ['C2', 'C3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 31.12s
== hueco 3
E   AssertionError: assert ['D2', 'D3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 33.95s
== hueco 4
E   AssertionError: assert ['E2', 'E3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 28.07s
== hueco 5
E   AssertionError: assert ['F2', 'F3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 28.90s
== hueco 6
E   AssertionError: assert ['G2', 'G3'] == []
FAILED tests/test_f036_excel_generador.py::test_f036_r122_ninguna_celda_del_cuerpo_lleva_borde_relleno_ni_fuente_de_mas[rellena]
1 failed, 238 passed in 49.08s
```

En los seis, el **único** test que cae es el nuevo: los otros 238 pasan, así
que sin él los seis sobrevivían. El fichero entero, sobre producción:
`239 passed in 36.70s`. `ruff check` del fichero: `All checks passed!`.

**Ningún superviviente queda abierto ni se da por equivalente**: los de la
herramienta son cero; los 85 a mano caen; los seis del hueco caen con el test
nuevo. No hay nada que el humano tenga que aceptar.

**Producción intacta.** La copia desechable se retiró
(`git worktree remove --force`); en el árbol,
`git diff -- services/postventa-api/infrastructure` → 0 bytes, y
`excel_openpyxl.py` no ha cambiado en este encargo. El otro worktree que lista
`git worktree list` (`.claude/worktrees/agent-…`) no es de este encargo y no
se ha tocado.

### `bash harness/init.sh` al acabar

Una vez, tal cual, tras el commit `a84ac02`. Salida real, las líneas que
importan (sin ningún `repr` de `Ajustes`: `grep -c "Ajustes("` → 0):

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 12.35s
[OK] pytest en verde (con medición de cobertura)
6597 passed, 74 skipped in 1975.49s (0:32:55)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3289 líneas cambiadas cubiertas (3285/3289, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

6.597 = 6.594 de T58 + los 3 casos del test nuevo. La suite tardó 1.975 s
frente a 833 s en T58: la máquina estaba cargada (las mutaciones a mano
también se frenaron a mitad de la pasada, de unos 15 s a unos 50 s por
ejecución); el test nuevo no es lento (4,3 s los tres casos).

### Ficheros tocados (T59–T60)

- `services/postventa-api/tests/test_f036_excel_generador.py`: el test nuevo
  del barrido de las 9.000 celdas. Ningún test existente cambia.
- `progress/mutacion_F-036_bloque13.md` (nuevo, generado por la herramienta).
- `specs/F-036-importar-excel/tasks.md`: T59 y T60 marcadas; T59 con la
  constancia del visto bueno.
- `progress/impl_F-036.md` y `progress/current.md`.
- **No tocados**: producción entera (`excel_openpyxl.py` incluido), los
  topes, `docs/`, `azure-apps/`. Ningún `.xlsx` en git.

### Commits

| Tarea | Commit |
|---|---|
| T60 (test, informe de mutación, T59 en `tasks.md`) | `a84ac02` |
| T60 (este informe, `current.md`, T60 marcada) | el siguiente |

### Evidencias (T60)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6597 passed, 74 skipped** (1.975,49 s); `front` en verde (caché). El generador solo: 239 passed |
| Fase RED | el test nuevo, en rojo contra **6 mutantes** que sin él sobrevivían (`1 failed, 238 passed` en cada uno; salida arriba) |
| Cobertura de las líneas cambiadas | **99,9 %** (3285/3289, `PUERTA COBERTURA`, rama entera) |
| Mutación (herramienta) | `--base 26a190e --workers 6 --timeout 900`: **0 generados, 0 supervivientes, 0 timeouts**, 0,0 s, **1 worker real** (con 0 mutantes no reparte). Confirmado aparte: 0 mutantes en las 49 líneas |
| Mutación (a mano) | **85 de 85 caen** (todas las que nombra T60 y más); y **6 del hueco**, que sobrevivían y caen con el test nuevo. **0 supervivientes abiertos** |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 1.975,49 s (máquina cargada; en T58, 832,83 s) |

### Pendiente y fuera del alcance

- **Review 8** (del bloque 13 entero, T55–T60), el **redespliegue** del
  backend, la **T28** repetida, **T29** y **T30**: fuera de este encargo.
- La herramienta de mutación no ve cadenas ni llamadas; en este bloque, la
  defensa son las mutaciones a mano. Los guiones están en el scratchpad de
  esta sesión (no versionados).
- `git push` no se ha hecho.

## Arreglos de la review 8 (R8-1, R8-2, R8-3) · 2026-10-02 · hecho; siguiente: review 9 corta

Encargo corto del líder: **solo tests, ninguna línea de producción**. R8-3 se
resuelve por test (decisión del líder), no por aceptación del humano.

### Qué cambió

Un solo fichero: `services/postventa-api/tests/test_f036_excel_generador.py`.

- **R8-1** (`4aced00`): `test_f036_r122_r123_las_reglas_en_el_xml` extrae el
  bloque `<dxfs>…</dxfs>` de `xl/styles.xml` y lo compara **entero** con el
  literal de la review (constante `DXF_DE_LAS_REGLAS`: tres `dxf` en la
  plantilla vacía, la rellena y el `v2`; los dos primeros con `count="2"` en el
  Excel de errores). La comparación es en forma canónica
  (`xml.etree.ElementTree.canonicalize`, C14N 2.0, `strip_text=True`), así que
  no depende de espacios ni del orden de atributos; el literal es exactamente
  el que escribe HEAD (comprobado antes de escribir el test). Sustituye a la
  comprobación de solo `<dxfs count="N">`.
- **R8-2** (`c6de60f`): en `test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion`
  (2 libros × 4 hojas):
  - `pageSetUpPr`: **`assert ajuste is None or dict(ajuste) == {}`** en lugar
    de `ajuste is None or ajuste.fitToPage is None` (ver la desviación);
  - `assert ws.sheet_view.view in (None, "normal")`.
  - Y en `test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml`,
    el único `<pageSetUpPr` admitido en el XML de cada hoja es el vacío
    `<pageSetUpPr />`.
- **R8-3** (`c6de60f`, en el mismo test de R8-2, como sugería la review):
  `ws.sheet_view.showRowColHeaders is not False` en «Incidencias» e
  «Instrucciones», y `ws.parent.calculation.calcMode in (None, "auto")`.

### Desviación respecto a la letra de la review (justificada)

La review pedía `assert ws.sheet_properties.pageSetUpPr is None` («es lo que
devuelve HEAD»). **No es lo que devuelve HEAD**: `openpyxl` crea siempre un
`PageSetupProperties()` vacío en `WorksheetProperties.__init__` (si recibe
`None`, lo construye), y además lo escribe siempre como `<pageSetUpPr />` en
`<sheetPr>`. Comprobado en las cuatro hojas de la plantilla y del Excel de
errores de HEAD: al releer, `pageSetUpPr` es un objeto con
`autoPageBreaks=None, fitToPage=None`; en el XML, `<pageSetUpPr />`. Con la
línea literal, el test caería en HEAD sin cambio alguno de producción.

Lo que pide la review (que **ningún** atributo de `pageSetUpPr` esté puesto, no
solo `fitToPage`) se fija con `dict(ajuste) == {}` (los `Serialisable` de
`openpyxl` iteran solo los atributos no nulos) y, en el XML, con «solo el
`<pageSetUpPr />` vacío». R12 (`autoPageBreaks=False`) cae por los dos
(4 failed, abajo). No cambia producción ni el alcance: es la forma de escribir
en `openpyxl` la misma comprobación. **Ojo reviewer** para la review 9.

### Verificación: HEAD

Árbol en `c6de60f`, sin mutantes:

```
$ .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=no -rf tests/test_f036_excel_generador.py
239 passed in 65.25s (0:01:05)
rc=0
$ .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=no -rf tests/test_f036_alcance_cerrado.py
26 passed in 16.40s
rc=0
```

(239 = los mismos casos que antes: no hay tests nuevos, solo comprobaciones
nuevas dentro de tres tests existentes.)

### Verificación: los mutantes de la review, cada uno solo

En una **copia desechable** (`git archive HEAD services/postventa-api` en el
scratchpad de la sesión, no en el árbol), con el `.venv` del servicio. Cada
mutante se aplica solo a `infrastructure/documentos/excel_openpyxl.py` de la
copia y se restaura después; al final, la copia es igual que el fichero del
repo (`True`). Se lanzó el fichero de tests de HEAD (con los arreglos) y, como
**fase RED**, el de `c1ebb94` (antes de los arreglos). Salida con
`--tb=no -rf`: ningún `repr` de objetos.

| Mutante | Cambio | Tests de `c1ebb94` | Tests de HEAD |
|---|---|---|---|
| R1 | regla 1 con `diagonal=Side(thin, ACERO_100)` y `diagonalDown=True` | rc=0, 239 passed (sobrevive) | **rc=1**, 3 failed |
| R2 | regla 2 con `fgColor=ERROR` además de `bgColor=LIENZO` | rc=0 (sobrevive) | **rc=1**, 3 failed |
| R3 | regla 3 con `fgColor=BURDEOS` además de `bgColor=BANDA` | rc=0 (sobrevive) | **rc=1**, 2 failed (el Excel de errores no lleva regla 3) |
| R10 | `ws.sheet_view.view = "pageLayout"` | rc=0 (sobrevive) | **rc=1**, 2 failed |
| R11 | `ws.sheet_view.view = "pageBreakPreview"` | rc=0 (sobrevive) | **rc=1**, 2 failed |
| R12 | `pageSetUpPr = PageSetupProperties(autoPageBreaks=False)` | rc=0 (sobrevive) | **rc=1**, 4 failed |
| R18 | `ws.sheet_view.showRowColHeaders = False` | rc=0 (sobrevive) | **rc=1**, 2 failed |
| R19 | `ws.parent.calculation.calcMode = "manual"` | rc=0 (sobrevive) | **rc=1**, 8 failed |

Salida real:

```
=== R1 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[vacia]
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[rellena]
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[errores]
3 failed, 236 passed in 63.48s (0:01:03)
=== R1 · tests c1ebb94 · rc=0
239 passed in 68.56s (0:01:08)
=== R2 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[vacia]
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[rellena]
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[errores]
3 failed, 236 passed in 69.08s (0:01:09)
=== R2 · tests c1ebb94 · rc=0
239 passed in 49.90s
=== R3 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[vacia]
FAILED tests/test_f036_excel_generador.py::test_f036_r122_r123_las_reglas_en_el_xml[rellena]
2 failed, 237 passed in 50.73s
=== R3 · tests c1ebb94 · rc=0
239 passed in 50.97s
=== R10 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-errores]
2 failed, 237 passed in 55.48s
=== R10 · tests c1ebb94 · rc=0
239 passed in 61.98s (0:01:01)
=== R11 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-errores]
2 failed, 237 passed in 52.42s
=== R11 · tests c1ebb94 · rc=0
239 passed in 53.41s
=== R12 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-errores]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml[plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml[errores]
4 failed, 235 passed in 52.51s
=== R12 · tests c1ebb94 · rc=0
239 passed in 53.53s
=== R18 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-errores]
2 failed, 237 passed in 59.30s
=== R18 · tests c1ebb94 · rc=0
239 passed in 57.61s
=== R19 · tests HEAD · rc=1
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Incidencias-errores]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Instrucciones-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[Instrucciones-errores]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[_catalogos-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[_catalogos-errores]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[_plantilla-plantilla]
FAILED tests/test_f036_excel_generador.py::test_f036_r125_ninguna_hoja_lleva_ajustes_de_impresion[_plantilla-errores]
8 failed, 231 passed in 50.37s
=== R19 · tests c1ebb94 · rc=0
239 passed in 50.41s
copia restaurada igual a la del repo: True
```

**Los 8 supervivientes de la review 8 caen: 0 supervivientes abiertos.**

### Otras comprobaciones

- `git diff c1ebb94 -- services/postventa-api/infrastructure/` vacío, y
  `git diff` de `excel_openpyxl.py` vacío: **ninguna línea de producción**.
- `ruff check` del fichero de tests: solo el `I001` que ya estaba en `c1ebb94`
  (bloque de imports); ninguno nuevo.
- Ningún `.xlsx` ni secreto en git; la copia, los libros y los guiones, en el
  scratchpad de la sesión (no versionados).
- No se relanzó `harness.mutacion` ni `bash harness/init.sh` (encargo: el líder
  lanza T30 después).

### Commits

| Qué | Commit |
|---|---|
| R8-1 | `4aced00` |
| R8-2 y R8-3 | `c6de60f` |
| Este informe y `current.md` | el siguiente |

### Evidencias (arreglos de la review 8)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `test_f036_excel_generador.py`: **239 passed** (65,25 s); `test_f036_alcance_cerrado.py`: **26 passed** (16,40 s) |
| Fase RED | los 8 mutantes de la review: **rc=0 con los tests de `c1ebb94`** y **rc=1 con los de HEAD** (salida arriba) |
| Cobertura de las líneas cambiadas | sin cambio de producción; la de la rama la mide `init.sh` en T30 (última: 99,9 %) |
| Mutación | herramienta no relanzada (no cambia producción); a mano, **8 de 8 caen** |
| Tiempo de la suite | el fichero del generador, 65,25 s |

### Pendiente y fuera del alcance

- **Review 9 corta** (solo estos tests); luego redespliegue, T28 repetida, T29,
  T30 (líder) y merge a `dev`.
- `git push` no se ha hecho.

## Bloque 14 (T61–T64) · 2026-10-03 · la migración ante un catálogo de Sigrid que ha cambiado

Encargo del líder: solo el Bloque 14 (undécima enmienda, `394ced4`), y parar.
No se han hecho las MANUAL (T28 repetida, T29) ni T30. Base de comparación:
`b56a718`.

### Qué cambió

Solo `services/postventa-api/scripts/migracion_f036.py`, una línea de salida
de `scripts/migrar_excel_f036.py` y sus tests en `tests/test_f036_migracion.py`
(`git diff b56a718 --stat -- services/postventa-api`: esos tres ficheros, 572
inserciones y 32 borrados, de ellos 457 líneas de tests). Ni la interfaz de la
línea de órdenes, ni `migracion_f036_correcciones.yaml`, ni
`test_f036_migracion_contenido.py`, ni el generador, el lector, el dominio, el
importador, `infra/` o el front.

- **`nombres_de_sigrid(datos) -> frozenset[str]`** (nueva, junto a
  `catalogo_de_la_obra`): los nombres de `oficios_catalogo` recortados, sin
  nulos ni vacíos. Si `oficios_catalogo` falta, no es una lista o algún
  elemento no es un mapping con `codigo` y `nombre` (texto o `null`), para con
  `_FORMA_CATALOGO`. `migrar` la llama justo después de `catalogo_de_la_obra`.
- **`componer(..., *, nombres_sigrid)`**, en el orden de §10.5 (la obra manda):
  de un oficio de la obra, como antes; de varios, para (mismo mensaje); de
  ninguno pero sí de `nombres_sigrid`, `Oficio` y `Proveedor` vacíos y la fila
  apunta el nombre; de ninguno de Sigrid, para con el **mensaje nuevo** literal
  de §10.5 (R97). Los problemas se siguen diciendo todos a la vez.
- **`FilaCompuesta.oficio_fuera_de_la_obra`** y
  **`Recuentos.oficios_fuera_de_la_obra`** (detrás de
  `oficios_en_grupo_de_varios`; no cuenta las filas a las que la tabla no pone
  oficio).
- **`informe`** (R130): la fila de recuento, siempre, detrás de la de grupos de
  varios códigos; la sección «## Filas sin oficio porque ese oficio ya no está
  en la obra en Sigrid» justo después de los recuentos si N > 0 (fila del
  original, número de la fila nueva dentro de ella, nombre con `_celda`); y en
  la tabla de su ubicación, «Oficio: — (ya no está en la obra en Sigrid:
  «…»)». Nada de proveedores ni de códigos de `auxofc`.
- **`migrar_excel_f036.py`**: la línea «Filas sin oficio porque ese oficio ya
  no está en la obra en Sigrid: N», detrás de la de filas; y su docstring.
- Docstrings al día: el paso 3 del módulo y una sección «Decisiones de la
  undécima enmienda» (la obra manda; el número de la fila nueva es su posición
  dentro de su fila del original, como en los mensajes de parada).

**Decisión de diseño menor**: la constante `SIN_OFICIO_FUERA_DE_LA_OBRA`
guarda el texto común a la fila de recuento y al título de la sección; la línea
de órdenes lleva su texto literal (es la «una línea» de la spec y no importa
nada nuevo).

### Tests: los que cambian a propósito, los nuevos y los que nacen en verde

**Cambian a propósito (solo los dos de la spec):**

- `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`: el mensaje
  nuevo de la errata, y un segundo `parametrize` (`CATALOGO` y
  `CATALOGO_SIGRID`): 6 casos → 12. Conserva su nombre (la spec permitía
  renombrarlo; se mantiene por trazabilidad con los informes anteriores).
- `test_f036_r58_recuentos_sin_grupos`: gana `oficios_fuera_de_la_obra=0`.

Ningún otro test compara `Recuentos` o `FilaCompuesta` enteros con un literal
(el nuevo `…_r128_la_obra_manda` los compara entre dos ejecuciones, no con un
literal). `test_f036_migracion_contenido.py` no cambia: su catálogo ya traía
`oficios_catalogo: []`.

**Casos nuevos** en el `parametrize` de `test_f036_catalogo_mal_formado` (9):
sin la clave, `null`, un texto, un mapping en vez de una lista, un elemento
texto, un elemento lista, sin `nombre`, sin `codigo`, `nombre` numérico.

**Catálogo de prueba nuevo** `CATALOGO_SIGRID`: el `CATALOGO` de siempre con
`oficios_catalogo` lleno (los nombres de la obra más dos inventados que no son
de ella: «Oficio que salió» y «Oficio retirado   », este con blancos al final
en Sigrid). Los proveedores siguen siendo inventados («Proveedor Inventado …»).
Al helper `_disco` se le añadió el parámetro `catalogo` (por defecto `CATALOGO`).

**Tests nuevos (16)**: `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio`,
`…_r128_el_v2_vuelve_con_cero_errores_y_la_fila_sin_oficio`,
`…_r128_el_nombre_de_sigrid_se_compara_recortado`,
`…_r128_nombres_de_sigrid_recortados_sin_nulos_ni_vacios`,
`…_r128_la_obra_manda`, `…_r128_nombre_de_varios_oficios_de_la_obra_sigue_parando`,
`…_r97_errata_y_fuera_de_la_obra_a_la_vez`,
`…_r129_el_proveedor_es_el_del_catalogo_con_que_se_ejecuta`,
`…_r129_la_fila_sin_oficio_no_lleva_proveedor`,
`…_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion`,
`…_r130_recuento_y_seccion`, `…_r130_varias_filas_y_su_numero_dentro_de_la_original`,
`…_r130_el_nombre_de_la_seccion_se_escapa`, `…_r130_la_linea_de_ordenes_lo_dice`,
`…_r130_sin_proveedores_en_el_informe`,
`…_r131_un_v2_de_otro_catalogo_da_errores_y_el_regenerado_no`.

**`test_f036_r129_la_tabla_no_admite_proveedor` no se ha escrito**: ya existe
el caso en `test_f036_forma_de_la_tabla_mal` (`_fila0(t)["resultado"][0].update(proveedor="x")`
→ «resultado 1: sobra «proveedor»»), como dice §10.5 («se cita en vez de
duplicarlo»).

**Nacen en verde, y por qué** (2 de los 16):

- `…_r129_el_proveedor_es_el_del_catalogo_con_que_se_ejecuta`: R129 es un
  **invariante** que el código de `b56a718` ya cumple (R91 calcula el
  proveedor en cada ejecución con el catálogo recibido); fija que siga así.
- `…_r128_nombre_de_varios_oficios_de_la_obra_sigue_parando`: con
  `CATALOGO_SIGRID`, un nombre de dos oficios de la obra sigue parando con el
  mensaje de siempre; el código de antes ni miraba `oficios_catalogo`. Fija el
  orden de decisión (que «varios» no caiga en el caso nuevo).

### T61 · fase RED (salida real)

Comando, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -q -p no:cacheprovider --no-header -rf --tb=no`
(sin `repr` de objetos; `grep -c Ajustes` de la salida → 0). Commit `01e28d7`.

```
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Solados y alicatados]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Pintura ]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO- Pintura]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-pintura]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Pintura (0010)]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Oficio que no existe]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-Solados y alicatados]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-Pintura ]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID- Pintura]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-pintura]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-Pintura (0010)]
FAILED tests/test_f036_migracion.py::test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-Oficio que no existe]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>8]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>9]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>10]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>11]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>12]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>13]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>14]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>15]
FAILED tests/test_f036_migracion.py::test_f036_catalogo_mal_formado[<lambda>16]
FAILED tests/test_f036_migracion.py::test_f036_r58_recuentos_sin_grupos
FAILED tests/test_f036_migracion.py::test_f036_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio
FAILED tests/test_f036_migracion.py::test_f036_r128_el_v2_vuelve_con_cero_errores_y_la_fila_sin_oficio
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
FAILED tests/test_f036_migracion.py::test_f036_r128_nombres_de_sigrid_recortados_sin_nulos_ni_vacios
FAILED tests/test_f036_migracion.py::test_f036_r128_la_obra_manda
FAILED tests/test_f036_migracion.py::test_f036_r97_errata_y_fuera_de_la_obra_a_la_vez
FAILED tests/test_f036_migracion.py::test_f036_r129_la_fila_sin_oficio_no_lleva_proveedor
FAILED tests/test_f036_migracion.py::test_f036_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion
FAILED tests/test_f036_migracion.py::test_f036_r130_recuento_y_seccion
FAILED tests/test_f036_migracion.py::test_f036_r130_varias_filas_y_su_numero_dentro_de_la_original
FAILED tests/test_f036_migracion.py::test_f036_r130_el_nombre_de_la_seccion_se_escapa
FAILED tests/test_f036_migracion.py::test_f036_r130_la_linea_de_ordenes_lo_dice
FAILED tests/test_f036_migracion.py::test_f036_r130_sin_proveedores_en_el_informe
FAILED tests/test_f036_migracion.py::test_f036_r131_un_v2_de_otro_catalogo_da_errores_y_el_regenerado_no
36 failed, 166 passed in 64.56s (0:01:04)
```

Los motivos, de la pasada con `--tb=line` (sin `repr`): el mensaje viejo
(«no es exactamente el nombre de un oficio de la obra en Sigrid») frente al
nuevo; `DID NOT RAISE MigracionDetenida` en los 9 casos de forma;
`Recuentos.__init__() got an unexpected keyword argument
'oficios_fuera_de_la_obra'`; `module 'scripts.migracion_f036' has no attribute
'nombres_de_sigrid'`; `'FilaCompuesta' object has no attribute
'oficio_fuera_de_la_obra'`; y, en los de R128–R131, la parada del código viejo
`fila 2 del original, fila nueva 1: el oficio «Oficio que salió» no es
exactamente el nombre de un oficio de la obra en Sigrid` (el caso del
incidente). Todo lo demás, **166 passed** (los 2 que nacen en verde, incluidos).

### T62 · verde (salida real)

Comando, desde `services/postventa-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py -q -p no:cacheprovider --no-header -rf --tb=short`.
Commit `e1a15a7`.

```
236 passed in 60.35s (0:01:00)
```

(202 de `test_f036_migracion.py` + 34 de `test_f036_migracion_contenido.py`.)
`git diff b56a718 --stat -- services/postventa-api`:

```
 services/postventa-api/scripts/migracion_f036.py   | 137 +++++-
 .../postventa-api/scripts/migrar_excel_f036.py     |  10 +
 .../postventa-api/tests/test_f036_migracion.py     | 457 ++++++++++++++++++++-
 3 files changed, 572 insertions(+), 32 deletions(-)
```

### T63 · ensayo en seco con los catálogos de fuera del repositorio

**Sin leer Sigrid**: los dos JSON del catálogo ya estaban fuera del repo
(`%TEMP%\catalogo_0677.json`, del 2026-09-29, y
`%TEMP%\catalogo_0677_20261003.json`, de hoy), los grupos vigentes en
`Downloads\grupos_vigentes_oficio_0677.json` (descargados el 2026-10-02) y el
original en su OneDrive. La orden de T28 con `--solo-informe` y `--salida` e
`--informe` al scratchpad de la sesión; **ni** `progress/migracion_F-036.md`
**ni** el OneDrive se han escrito; ningún `.xlsx` generado (con
`--solo-informe` el `v2` no se escribe). Desde `services/postventa-api`:

```
.venv/Scripts/python.exe scripts/migrar_excel_f036.py --original "<OneDrive>/postventa/creacion_incidencias.xlsx" \
  --catalogo "<TEMP>/<JSON del día>" --correcciones scripts/migracion_f036_correcciones.yaml \
  --grupos "<Downloads>/grupos_vigentes_oficio_0677.json" \
  --salida "<scratchpad>/ensayo/v2_<día>.xlsx" --informe "<scratchpad>/ensayo/informe_<día>.md" --solo-informe
```

Salida real (rutas del scratchpad recortadas a `<scratchpad>`):

```
===== catalogo 0929 =====
Migración F-036 · obra 0677 · con --grupos (5 grupos de varios códigos)
Filas del original: 144 · filas nuevas: 158 · separadas: 14 · descartadas: 0
Filas sin oficio porque ese oficio ya no está en la obra en Sigrid: 0
Ida y vuelta por el importador: 0 errores
Informe: <scratchpad>\ensayo\informe_0929.md
v2: no se escribe (--solo-informe)
sha256 del original antes:   4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
sha256 del original después: 4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
rc=0
===== catalogo 1003 =====
Migración F-036 · obra 0677 · con --grupos (5 grupos de varios códigos)
Filas del original: 144 · filas nuevas: 158 · separadas: 14 · descartadas: 0
Filas sin oficio porque ese oficio ya no está en la obra en Sigrid: 2
Ida y vuelta por el importador: 0 errores
Informe: <scratchpad>\ensayo\informe_1003.md
v2: no se escribe (--solo-informe)
sha256 del original antes:   4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
sha256 del original después: 4f5f1f9db402fae2b34370aaabb75b1efa7fc4a8917bddf50cf5674654cfa5f1
rc=0
```

El `sha256` del original, medido además por fuera antes y después de las dos
ejecuciones: el mismo (`4f5f1f9d…a5f1`, el del informe aceptado).

**Recuentos** (las filas de la tabla de recuentos de cada informe):

| Qué | Aceptado (`progress/migracion_F-036.md`) | Ensayo, JSON del 2026-09-29 | Ensayo, JSON del 2026-10-03 |
|---|---:|---:|---:|
| Filas del original | 144 | 144 | 144 |
| Filas nuevas | 158 | 158 | 158 |
| Separadas en varias | 14 | 14 | 14 |
| Descartadas | 0 | 0 | 0 |
| Oficios completados (la muestra no lo traía) | 77 | 77 | 75 |
| Oficios de la muestra que no son exactamente un nombre de Sigrid de la obra | 9 | 9 | 9 |
| Filas nuevas con un oficio cuyo grupo tiene varios códigos | 42 | 42 | 47 |
| **Filas nuevas sin oficio porque ese oficio ya no está en la obra** | (no existía) | **0** | **2** |
| Filas nuevas con proveedor por R91 | 15 | 15 | 47 |
| Urgencias: Urgente / Peligro para la seguridad | 1 / 12 | 1 / 12 | 1 / 12 |
| Filas nuevas con algún aviso del importador | 42 | 42 | 47 |

- **Con el JSON del 2026-09-29**: la fila nueva sale con **0**, sin sección, y
  los demás recuentos son **iguales** a los del informe aceptado. Más aún, el
  informe entero solo difiere del aceptado en **3 líneas**: el comentario de
  la cabecera (lleva el nombre del fichero de salida) y la fila de recuento
  nueva (`diff` → `< <!-- progress/migracion_F-036.md -->`,
  `> <!-- progress/informe_0929.md -->`, `> | Filas nuevas sin oficio … | 0 |`).
- **Con el JSON del 2026-10-03**: el script **termina** (rc=0, ida y vuelta con
  **0 errores**) donde antes se paraba, y la fila nueva sale con **2**: las
  filas **105 y 106** del original (fila nueva 1 en cada una), oficio de la
  tabla **«V-Aire acondicionado»**, el único oficio afectado. La sección:

  ```
  ## Filas sin oficio porque ese oficio ya no está en la obra en Sigrid

  | Fila del original | Fila nueva | Oficio en la tabla de correcciones |
  |---:|---:|---|
  | 105 | 1 | V-Aire acondicionado |
  | 106 | 1 | V-Aire acondicionado |
  ```

  En las dos filas, la muestra no traía oficio (columna «Oficio en la
  muestra»: —), y la columna «Propuesto» sigue diciendo `ubicacion, oficio`
  porque sale de la tabla (`propuesto`), que no cambia; la fila nueva dice
  «Oficio: — (ya no está en la obra en Sigrid: «V-Aire acondicionado»)» y ya
  no lleva «proveedor» en «Propuesto» (el 2026-09-29 sí: R91 lo completaba).
  Las otras diferencias con el del 2026-09-29 son del catálogo de hoy, no del
  código: 38 filas del original cambian de texto en las tablas por ubicación
  (etiquetas de grupo, códigos en la obra, proveedores completados), y los
  recuentos de la tabla de arriba (completados 77 → 75 por las dos filas sin
  oficio; grupo de varios 42 → 47; proveedor por R91 15 → 47; avisos 42 → 47).
  Es la lista de diferencias que el humano tendrá que **aceptar expresamente**
  en T28 (R131), con los grupos que descargue ese día.
- **Sin datos de proveedor** (comprobado con un guion del scratchpad contra
  los dos JSON, sin imprimir ningún nombre): en los dos informes, **0 de 36**
  nombres de proveedor de cada catálogo y **0** códigos de proveedor (ni entre
  comillas invertidas ni como palabra suelta). El informe de hoy no lleva
  ningún código de `auxofc` que no sea de la obra de hoy; el del 2026-09-29
  lleva el código de «V-Aire acondicionado», que ese día sí era de la obra.
- `git status` tras el ensayo: limpio salvo lo de este encargo; ningún `.xlsx`
  y `progress/migracion_F-036.md` sin cambios.

**Para T28 (aviso, no es de este encargo)**: el fichero de grupos que había a
mano es del 2026-10-02; R131 pide descargarlo de `oficios.html` el mismo día.

### T64 · la campaña de la herramienta

Desde la raíz, con el `.venv` de la raíz:
`python -m harness.mutacion --feature F-036 --base b56a718 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque14.md`.
Salida real, entera:

```
F-036: 2 fichero(s), 126 línea(s) de producción (origen rama, b56a718a0091f3eb63c084fe507634e438f63bde..feature/F-036-importar-excel)
Campaña paralela: hasta 6 workers, uno por worktree.
[1/16] muerto        services/postventa-api/scripts/migracion_f036.py:549 [not] if not isinstance(filas, list) or not all(_fila_de_auxofc(f) for f in filas): -> if isinstance(filas, list) or not all(_fila_de_auxofc(f) for f in filas):
[2/16] muerto        services/postventa-api/scripts/migracion_f036.py:534 [logico] and (fila["nombre"] is None or isinstance(fila["nombre"], str)) -> and (fila["nombre"] is None and isinstance(fila["nombre"], str))
[3/16] muerto        services/postventa-api/scripts/migracion_f036.py:532 [logico] and "codigo" in fila -> or "codigo" in fila
[4/16] muerto        services/postventa-api/scripts/migracion_f036.py:534 [logico] and (fila["nombre"] is None or isinstance(fila["nombre"], str)) -> or (fila["nombre"] is None or isinstance(fila["nombre"], str))
[5/16] muerto        services/postventa-api/scripts/migracion_f036.py:549 [logico] if not isinstance(filas, list) or not all(_fila_de_auxofc(f) for f in filas): -> if not isinstance(filas, list) and not all(_fila_de_auxofc(f) for f in filas):
[6/16] muerto        services/postventa-api/scripts/migracion_f036.py:533 [logico] and "nombre" in fila -> or "nombre" in fila
[7/16] muerto        services/postventa-api/scripts/migracion_f036.py:695 [not] if not codigos and nueva.oficio not in nombres_sigrid: -> if codigos and nueva.oficio not in nombres_sigrid:
[8/16] muerto        services/postventa-api/scripts/migracion_f036.py:688 [entero] if len(codigos) > 1: -> if len(codigos) > 2:
[9/16] muerto        services/postventa-api/scripts/migracion_f036.py:688 [comparacion] if len(codigos) > 1: -> if len(codigos) >= 1:
[10/16] muerto        services/postventa-api/scripts/migracion_f036.py:549 [not] if not isinstance(filas, list) or not all(_fila_de_auxofc(f) for f in filas): -> if not isinstance(filas, list) or all(_fila_de_auxofc(f) for f in filas):
[11/16] muerto        services/postventa-api/scripts/migracion_f036.py:695 [logico] if not codigos and nueva.oficio not in nombres_sigrid: -> if not codigos or nueva.oficio not in nombres_sigrid:
[12/16] muerto        services/postventa-api/scripts/migracion_f036.py:551 [logico] return frozenset(nombre for f in filas if (nombre := (f["nombre"] or "").strip())) -> return frozenset(nombre for f in filas if (nombre := (f["nombre"] and "").strip()))
[13/16] muerto        services/postventa-api/scripts/migracion_f036.py:702 [not] if not codigos: -> if codigos:
[14/16] muerto        services/postventa-api/scripts/migracion_f036.py:1063 [aritmetico] lineas += [ -> lineas -= [
[15/16] muerto        services/postventa-api/scripts/migracion_f036.py:1071 [entero] for n, i in enumerate(indices, start=1): -> for n, i in enumerate(indices, start=2):
[16/16] muerto        services/postventa-api/scripts/migracion_f036.py:853 [entero] 1 for c in compuestas if c.oficio_fuera_de_la_obra is not None -> 2 for c in compuestas if c.oficio_fuera_de_la_obra is not None
16 mutantes evaluados, 16 muertos, 0 supervivientes, 0 timeouts en 2236.9 s
Informe: progress/mutacion_F-036_bloque14.md
```

- **Alcance**: 126 líneas (116 de `migracion_f036.py`, 10 de
  `migrar_excel_f036.py`; de estas, ninguna mutable: docstring y un `print`).
- **16 generados, 16 muertos, 0 supervivientes, 0 timeouts**, 2.236,9 s.
- **Workers reales: 6** (pedidos 6; el informe dice «Workers | 6» y había 16
  mutantes, así que reparte en los seis worktrees `wk_0`–`wk_5`). Los
  worktrees se retiraron al terminar (`git worktree list` solo muestra el árbol
  y un `agent-…` ajeno a este encargo, que no se ha tocado).

### T64 · mutaciones a mano (23, todas caen)

Guion `mutaciones_t64.py` (scratchpad, sin versionar). **En una copia
desechable**: `git archive HEAD` del repositorio entero (`9908ef2`, el mismo
código que `e1a15a7`) extraído en el scratchpad, con el `.venv` de
`services/postventa-api` y `cwd` en la copia. Cada mutación sola, por
sustitución de texto que tiene que aparecer **exactamente una vez**; `pytest
tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py -q --tb=no
-rf -p no:cacheprovider`; muerta solo con `rc=1`; el fichero restaurado tras
cada una; al final, los dos scripts de la copia iguales que HEAD (`True`). Sin
`repr` en la salida (`grep -c Ajustes` → 0). La copia se borró al terminar.

**Una primera pasada no vale y no se cuenta**: la hice con `git archive HEAD
services/postventa-api` (solo el servicio) y la base sin mutar salió en rojo
(`9 failed, 224 passed, 3 errors`, todos en `test_f036_migracion_contenido.py`,
que lee `docs/referencia/` fuera del servicio); además 7 mutaciones no se
aplicaron porque la copia sale con CRLF y su texto llevaba `\n`. Corregí el
guion (repositorio entero, CRLF, y abortar si la base no está en verde) y
repetí **todas**. Los números de abajo son los de la segunda pasada:

```
=== sin mutar · rc=0
236 passed in 107.50s (0:01:47)
```

| # | Mutación (cada una, sola) | Resultado | Primer test que la caza |
|---|---|---|---|
| M1 | mirar `nombres_sigrid` **antes** que la obra | cae: 10 failed | `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio` |
| M2 | quitar el recorte de los nombres de `oficios_catalogo` | cae: 3 failed | `…_r128_el_nombre_de_sigrid_se_compara_recortado` |
| M3 | recortar el nombre de la tabla antes de compararlo | cae: 3 failed | `…_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO_SIGRID-Pintura ]` |
| M4 | dejar vacía también la errata (quitar su parada) | cae: 16 failed | `…_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Solados y alicatados]` |
| M5 | volver a parar en el oficio que ha salido | cae: 11 failed | `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio` |
| M6 | escribir en `Oficio` el nombre de la tabla en vez de vacío | cae: 10 failed | el mismo |
| M7a | calcular un proveedor en la fila sin oficio (un par en el v2) | cae: 3 failed | el mismo |
| M7b | calcular un proveedor en la fila sin oficio (el código) | cae: 2 failed | el mismo |
| M8 | aceptar un JSON sin `oficios_catalogo` (`.get(..., [])`) | cae: 2 failed | `test_f036_catalogo_mal_formado[<lambda>8]` |
| M9 | contar en el recuento también las filas a las que la tabla no pone oficio | cae: 5 failed | `test_f036_r58_recuentos_sin_grupos` |
| M10 | sacar la sección siempre | cae: 1 failed | `…_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion` |
| M11 | no sacarla nunca | cae: 3 failed | `…_r130_recuento_y_seccion` |
| M12 | quitar la línea del resumen de la línea de órdenes | cae: 1 failed | `…_r130_la_linea_de_ordenes_lo_dice` |
| M13 | no quitar los nombres vacíos de `oficios_catalogo` | cae: 1 failed | `…_r128_nombres_de_sigrid_recortados_sin_nulos_ni_vacios` |
| M14 | no exigir `codigo` en cada fila de `oficios_catalogo` | cae: 1 failed | `test_f036_catalogo_mal_formado[<lambda>15]` |
| M15 | no exigir que `nombre` sea texto o `null` | cae: 1 failed | `test_f036_catalogo_mal_formado[<lambda>16]` |
| M16 | la fila nueva de la sección contada desde 0 | cae: 3 failed | `…_r130_recuento_y_seccion` |
| M17 | la fila de su ubicación dice solo «Oficio: —» | cae: 2 failed | el mismo |
| M18 | sin la fila de recuento | cae: 3 failed | `…_r130_con_el_catalogo_de_siempre_recuento_cero_y_sin_seccion` |
| M19 | el mensaje de la errata, el de antes | cae: 14 failed | `…_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para[CATALOGO-Solados y alicatados]` |
| M20 | `migrar` no lee `oficios_catalogo` (`frozenset()`) | cae: 20 failed | `test_f036_catalogo_mal_formado[<lambda>8]` |
| M21 | la sección sin `_celda` | cae: 1 failed | `…_r130_el_nombre_de_la_seccion_se_escapa` |
| M22 | el oficio que ha salido no se apunta en la fila compuesta | cae: 6 failed | `…_r128_oficio_que_ya_no_esta_en_la_obra_queda_vacio` |

M1–M12 cubren todas las que nombra T64 (la del proveedor, en dos variantes,
M7a y M7b; «la sección siempre, o nunca», en M10 y M11); M13–M22, añadidas. **0 supervivientes, ni de la herramienta ni a mano; nada
que dar por equivalente ni que aceptar.**

### Ficheros tocados (Bloque 14)

- `services/postventa-api/scripts/migracion_f036.py` y
  `services/postventa-api/scripts/migrar_excel_f036.py` (producción).
- `services/postventa-api/tests/test_f036_migracion.py` (tests).
- `progress/mutacion_F-036_bloque14.md` (nuevo, generado por la herramienta).
- `specs/F-036-importar-excel/tasks.md` (T61–T64 marcadas),
  `progress/impl_F-036.md`, `progress/current.md`.
- **No tocados**: `progress/migracion_F-036.md`, el YAML de correcciones,
  `test_f036_migracion_contenido.py`, el generador, el lector, el dominio, el
  importador, `infra/`, el front, `docs/`, `azure-apps/`. Nada en OneDrive.
  Ningún `.xlsx` en git; los catálogos y los grupos, fuera del repositorio.

### Commits

| Tarea | Commit |
|---|---|
| T61 (RED) | `01e28d7` |
| T62 (el cambio) | `e1a15a7` |
| T63 (informe con el ensayo en seco) | `9908ef2` |
| T64 (mutación, `init.sh`, este cierre y `current.md`) | el siguiente |

### `bash harness/init.sh` al acabar

Una vez, tal cual, tras `9908ef2` (sin cambios de código después). Salida
real, las líneas que importan (sin ningún `repr` de `Ajustes`: `grep -c
"Ajustes("` → 0):

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[AVISO] Hay features en estado blocked: revisa progress/current.md
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 19.15s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
6628 passed, 74 skipped in 1524.51s (0:25:24)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3318 líneas cambiadas cubiertas (3314/3318, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

6.628 = 6.597 de T60 + 31 casos nuevos (16 tests, 9 casos de forma y 6 del
segundo `parametrize` de R97). Los 71 avisos de `ruff` son los mismos de
antes (deuda previa); el aviso de `blocked` es de otra feature, ajena a este
encargo.

### Evidencias (Bloque 14)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6628 passed, 74 skipped** (1.524,51 s); `front` en verde (caché). La migración sola: **236 passed** (60,35 s) |
| Fase RED | `test_f036_migracion.py`: **36 failed, 166 passed** antes del cambio (salida arriba); 2 tests nacen en verde a propósito (invariantes, justificados) |
| Ensayo en seco (T63) | 144 filas → 158 nuevas, 14 separadas, 0 descartadas en los dos catálogos; **filas sin oficio por R128: 0** con el del 2026-09-29 (resto de recuentos igual que el informe aceptado) y **2** con el del 2026-10-03 (filas 105 y 106, «V-Aire acondicionado»); **0 errores** en la ida y vuelta en los dos; `sha256` del original sin cambios |
| Cobertura de las líneas cambiadas | **99,9 %** (3314/3318, `PUERTA COBERTURA`, rama entera) |
| Mutación (herramienta) | `--base b56a718 --workers 6 --timeout 900`: **16 generados, 16 muertos, 0 supervivientes, 0 timeouts**, 2.236,9 s, **6 workers reales** |
| Mutación (a mano) | **23 de 23 caen** (todas las de T64 y 10 más), sobre una base en verde (236 passed). **0 supervivientes abiertos** |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 1.524,51 s |

### Pendiente y fuera del alcance

- **Review 10** (Bloque 14), **T28 otra vez** (grupos y catálogo leídos el
  mismo día, `--sobrescribir`, informe que el humano acepta expresamente con la
  lista de diferencias de arriba), **T29 pasos 4–7** (paso 4 por bueno con 0
  errores aunque salgan `ya_en_bandeja`) y **T30**: fuera de este encargo.
- Las cuatro decisiones que el spec-author dejó al humano en `current.md`
  siguen abiertas; esta implementación sigue la spec tal cual (R129 sin aviso
  propio; la errata para; un renombrado en Sigrid para).
- `git push` no se ha hecho.

## Arreglos de la review 10 (R10-1, R10-2) · 2026-10-03 · hecho; siguiente: review 11

Encargo corto del líder: los dos cambios requeridos de la review 10 y parar.
No cambia el comportamiento de producción.

### Qué cambió

- **R10-1** (`0097a6e`, solo test): en
  `services/postventa-api/tests/test_f036_migracion.py`,
  `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`, la tupla de
  erratas suma dos nombres, los dos con `CATALOGO_SIGRID` y esperando
  `(_errata(2, 1, nombre),)`:
  - `"Oficio que salio"`: `FUERA_DE_LA_OBRA` sin su tilde;
  - `"Albañileria"`: «Albañilería» (0020, de la obra en `CATALOGO`) sin la
    tilde de la «í». Es el mismo tipo de gemelo que la review encontró en
    `auxofc` real. No se usa «Fontaneria» porque en `CATALOGO` es un oficio
    de la obra (0160).
  - El comentario del bucle dice ya «blancos, capitalización o tildes».
- **R10-2** (`9e7f308`): `services/postventa-api/scripts/migracion_f036.py:892`,
  `decisiones =()` → `decisiones = ()`. Solo ese espacio.

### Evidencia de R10-1: V2 en rojo con el test nuevo

Copia desechable en el scratchpad (`git archive HEAD` + los dos ficheros del
árbol de trabajo), con el `.venv` del servicio. V2 se aplicó **solo en la
copia**, con un guion que exige que la línea aparezca una sola vez:

```
-                if not codigos and nueva.oficio not in nombres_sigrid:
+                if not codigos and __import__('unicodedata').normalize('NFKD', nueva.oficio).encode('ascii', 'ignore').decode() not in {__import__('unicodedata').normalize('NFKD', x).encode('ascii', 'ignore').decode() for x in nombres_sigrid}:
```

Es la V2 de la review: `oficios_catalogo` comparado sin tildes (NFKD sin
diacríticos, en los dos lados).

Con V2 y el test nuevo:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k "r128_el_nombre_de_sigrid_se_compara_recortado" --tb=short -p no:cacheprovider -q
F                                                                        [100%]
================================== FAILURES ===================================
___________ test_f036_r128_el_nombre_de_sigrid_se_compara_recortado ___________
tests\test_f036_migracion.py:1993: in test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
    problemas = _detenida(
tests\test_f036_migracion.py:358: in _detenida
    with pytest.raises(mig.MigracionDetenida) as error:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE MigracionDetenida
=========================== short test summary info ===========================
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 201 deselected in 5.02s
```

Cada nombre nuevo mata V2 **por separado** (en la copia, quitando el otro de
la tupla; restaurado después):

```
solo queda el otro; quitado: "Oficio que salio",
...\test_f036_migracion.py:358: Failed: DID NOT RAISE MigracionDetenida
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 201 deselected in 2.42s
solo queda el otro; quitado: "Albañileria",
...\test_f036_migracion.py:358: Failed: DID NOT RAISE MigracionDetenida
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 201 deselected in 2.28s
```

Control, los dos ficheros de la migración con V2 en la copia:

```
# test de HEAD (9a2aba4), sin los nombres nuevos: V2 sobrevive, como en la review
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py --tb=line -p no:cacheprovider -q
236 passed in 93.18s (0:01:33)
# test nuevo: V2 cae
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py --tb=line -p no:cacheprovider -q
...\test_f036_migracion.py:358: Failed: DID NOT RAISE MigracionDetenida
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 235 passed in 64.48s (0:01:04)
```

### Verificación sobre el código real

Los dos ficheros de tests de la migración, en el repositorio, con R10-1 y
R10-2 aplicados:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py --tb=line -p no:cacheprovider -q
236 passed in 71.19s (0:01:11)
```

Sigue siendo 236: los dos nombres son casos nuevos del bucle de un test que ya
existía, no tests nuevos.

`ruff` (0.16.3, el del sistema; el `.venv` del servicio no lo trae):

- `ruff format --check scripts/migracion_f036.py` → `1 file already formatted`
  (R10-2 resuelto).
- `ruff check scripts/migracion_f036.py tests/test_f036_migracion.py` → 1
  aviso `I001` (orden de imports del test, líneas 22–57). Es **previo**:
  sobre HEAD sin mis cambios (`git stash`) sale el mismo aviso. Lanzado desde
  `services/postventa-api`; la review lo vio limpio, probablemente lanzado con
  otra raíz de configuración. No lo toco: fuera del encargo.

`bash harness/init.sh`, una vez, tal cual, sobre `9e7f308` (sin ningún `repr`
de `Ajustes` en la salida: `grep -c "Ajustes("` → 0):

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[AVISO] Hay features en estado blocked: revisa progress/current.md
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 6.96s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
6628 passed, 74 skipped in 1143.59s (0:19:03)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3318 líneas cambiadas cubiertas (3314/3318, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

Los 71 avisos de `ruff` y el aviso de `blocked` (F-035) son los de antes.

### Evidencias (arreglos de la review 10)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6628 passed, 74 skipped**; `front` en verde (caché). La migración sola: **236 passed** (71,19 s) |
| Fase RED | V2 de la review, en copia: **1 failed, 235 passed** con el test nuevo; **236 passed** con el de HEAD. Cada nombre nuevo la mata por separado |
| Cobertura de las líneas cambiadas | **99,9 %** (3314/3318, `PUERTA COBERTURA`) |
| Mutación (herramienta) | no relanzada, por indicación del líder: R10-2 no cambia el AST y R10-1 solo toca un test. La de T64 sigue: 16/16 |
| Mutación (a mano) | V2, el único superviviente de la review 10, **cae**. 0 supervivientes abiertos |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 1.143,59 s |

### Pendiente y fuera del alcance

- **Review 11.**
- **R10-3** (la sección de R130 no distingue «ha salido» de «errata de tilde
  con gemelo en `auxofc`»): decisión del humano, (a) o (b) de la review 10,
  antes de T28 otra vez. No tocado.
- **R10-4** (informativo): no tocado.
- T28 otra vez, T29 pasos 4–7 y T30; las cuatro decisiones del spec-author.
- La copia desechable del scratchpad se ha borrado. `git push` no se ha hecho.

## Arreglos de la review 11 (R11-1, R11-2, R10-3) · 2026-10-03 · hecho; siguiente: review 12

Encargo corto del líder, **tercera vuelta autorizada expresamente por el
humano** («a», 2026-10-03): los cambios requeridos de la review 11 y la
opción (a) de R10-3, y parar. **Sin código de producción**:
`git diff 50df9e6 HEAD -- services/postventa-api/scripts/` vacío.

### Qué cambió

- **R11-1** (`0ac4832`, solo test): en
  `services/postventa-api/tests/test_f036_migracion.py`,
  `test_f036_r128_el_nombre_de_sigrid_se_compara_recortado`, la tupla de
  erratas suma `"Solados y Alicatados MO"`: «Solados y Alicatados M.O.»
  (0133, de la obra en `CATALOGO`) sin los puntos. Espera
  `(_errata(2, 1, nombre),)` con `CATALOGO_SIGRID`.
- **R11-2** (`073847e`, solo test): la misma tupla suma
  `unicodedata.normalize("NFD", FUERA_DE_LA_OBRA)` (con `import unicodedata`
  en el bloque de la biblioteca estándar). Espera también `_errata`. Se ha
  comprobado antes que la forma NFD de «Oficio que salió» **no** es igual a la
  cadena (que está en NFC), así que el caso no es vacío.
- El comentario del bucle dice ya «blancos, capitalización, tildes,
  puntuación o forma Unicode», con la referencia a R11-1 y R11-2.
- **R10-3, opción (a)** (`e6aebba`, solo spec): en
  `specs/F-036-importar-excel/tasks.md`, T28 (undécima enmienda), junto al
  criterio (a) de «Diferencias esperables»: la sección de filas sin oficio
  **no se acepta en bloque**; el líder comprueba a mano cada nombre contra los
  oficios **de la obra** del catálogo del día (`oficios_obra` del JSON del
  paso 2, **no** `auxofc`, con el motivo), buscando un gemelo que solo difiera
  en tildes, mayúsculas, blancos o puntuación (ejemplo «V Pintura» frente a
  «V-Pintura»); si lo hay, es errata de la tabla: se corrige
  `scripts\migracion_f036_correcciones.yaml` y se relanza la migración antes
  de aceptar el informe. **Ningún test de documentación fija el texto de
  T28** (buscado en `services/*/tests`: los únicos que leen un `tasks.md` son
  de F-013/F-051), así que no se ha tocado ningún test por esto.

### Evidencia: V2f y V2g en rojo con el test nuevo

Copia desechable: `git archive HEAD` (en `073847e`, el repositorio entero, por
los ficheros que lee `…_contenido.py`) extraída en el scratchpad; el `.venv`
del servicio real, con `cwd` en el servicio de la copia (comprobado que
`scripts.migracion_f036` y `domain` se importan **de la copia**). Guion
`mutaciones_r11.py` (scratchpad, sin versionar): exige que la línea de
`componer` aparezca una sola vez, aplica **cada mutación sola**, lanza los dos
ficheros de la migración y restaura. Solo se imprimen las líneas de fallo y
el resumen (ningún `repr`).

Línea mutada (`migracion_f036.py`, la de la errata en `componer`):

```
                if not codigos and nueva.oficio not in nombres_sigrid:
V2f →           if not codigos and __import__('re').sub(r'[^\w\s]', '', nueva.oficio) not in {__import__('re').sub(r'[^\w\s]', '', x) for x in nombres_sigrid}:
V2g →           if not codigos and __import__('unicodedata').normalize('NFC', nueva.oficio) not in {__import__('unicodedata').normalize('NFC', x) for x in nombres_sigrid}:
```

Orden en cada paso (desde `services/postventa-api` de la copia):
`.venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py --tb=line -p no:cacheprovider -q`.
Salida real (las rutas largas del scratchpad recortadas a `<copia>`):

```
--- base sin mutar, test nuevo: rc=0
236 passed in 77.20s (0:01:17)
--- V2f (sin puntuación [^\w\s], en los dos lados), test nuevo: rc=1
E   Failed: DID NOT RAISE MigracionDetenida
<copia>\services\postventa-api\tests\test_f036_migracion.py:359: Failed: DID NOT RAISE MigracionDetenida
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 235 passed in 61.19s (0:01:01)
--- V2f (sin puntuación [^\w\s], en los dos lados), test de 50df9e6 (sin R11): rc=0
236 passed in 53.32s
--- V2g (en NFC, en los dos lados), test nuevo: rc=1
E   Failed: DID NOT RAISE MigracionDetenida
<copia>\services\postventa-api\tests\test_f036_migracion.py:359: Failed: DID NOT RAISE MigracionDetenida
FAILED tests/test_f036_migracion.py::test_f036_r128_el_nombre_de_sigrid_se_compara_recortado
1 failed, 235 passed in 46.74s
--- V2g (en NFC, en los dos lados), test de 50df9e6 (sin R11): rc=0
236 passed in 45.94s
restaurado: True
```

Es decir: con el test de antes (`50df9e6`) las dos sobreviven, como en la
review 11; con el nuevo, las dos caen y solo por el test de R128. Cada nombre
mata a su mutante: V2f quita también la tilde combinante de la forma NFD
(no es `\w`), pero «Oficio que salio» no está en `oficios_catalogo`
recortado, así que a V2f la mata «Solados y Alicatados MO»; a V2g solo la
puede matar la forma NFD.

### Verificación sobre el código real

En el repositorio, con R11-1 y R11-2:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py -k "r128_el_nombre_de_sigrid_se_compara_recortado" --tb=short -p no:cacheprovider -q
1 passed, 201 deselected in 2.07s
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py --tb=line -p no:cacheprovider -q
236 passed in 55.75s
```

Sigue siendo 236: son casos nuevos del bucle de un test que ya existía.

- `git diff 50df9e6 HEAD -- services/postventa-api/scripts/` → **vacío**.
- `ruff check services/postventa-api/tests/test_f036_migracion.py` (desde la
  raíz) → `All checks passed!`.
- `ruff format --check` del test → «would be reformatted», pero es **previo**:
  el mismo diff de 7 líneas sale con el fichero de `50df9e6`, y ninguna toca
  las líneas añadidas (líneas 164, 184, 548 y 1889). No lo toco: fuera del
  encargo.

`bash harness/init.sh`, una vez, tal cual, sobre `e6aebba` (sin ningún `repr`
de `Ajustes` en la salida: 0 apariciones de `Ajustes(`):

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[AVISO] Hay features en estado blocked: revisa progress/current.md
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 5.79s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
6628 passed, 74 skipped in 1005.73s (0:16:45)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3318 líneas cambiadas cubiertas (3314/3318, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

La suite de `api` se ha relanzado de verdad (el árbol del servicio cambió).
Los 71 avisos de `ruff` y el de `blocked` (F-035) son los de antes.

### Evidencias (arreglos de la review 11)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6628 passed, 74 skipped**; `front` en verde (caché). La migración sola: **236 passed** (55,75 s) |
| Fase RED | En copia: V2f **1 failed, 235 passed** y V2g **1 failed, 235 passed** con el test nuevo; las dos **236 passed** con el test de `50df9e6` |
| Cobertura de las líneas cambiadas | **99,9 %** (3314/3318, `PUERTA COBERTURA`) |
| Mutación (herramienta) | no relanzada, por indicación de la review 11: no cambia producción ni el AST. La de T64 sigue: 16/16 |
| Mutación (a mano) | V2f y V2g, los dos supervivientes de la review 11, **caen**. 0 supervivientes abiertos (V11b, equivalente en la práctica según la review: no pedido) |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 1.005,73 s |

### Pendiente y fuera del alcance

- **Review 12.**
- **R11-3** (V11b, informativo): no tocado.
- **R10-4** (informativo): no tocado.
- La automejora que propone la review 11 para `.claude/agents/reviewer.md` (y
  `arnes-base`): no es de este encargo.
- T28 otra vez (ya con la comprobación a mano de R10-3), T29 pasos 4–7 y T30;
  las cuatro decisiones del spec-author.
- La copia desechable del scratchpad se borra al cerrar. `git push` no se ha
  hecho.

## Arreglos de la review 12 (R12-1) · 2026-10-04 · hecho; siguiente: review 13

Encargo corto del líder, **cuarta vuelta autorizada expresamente por el
humano** («a», 2026-10-04): el cambio requerido de la review 12, y parar.
**Sin código de producción**: `git diff 1186c1d HEAD -- services/postventa-api/scripts/`
vacío.

Decisiones del humano (2026-10-04), copiadas también en `progress/current.md`:

1. se añaden los ocho nombres que pide R12-1;
2. **se ACEPTAN en bloque los 20 equivalentes de R12-2** (4 por construcción y
   16 en la práctica, incluido V11b/R11-3), con el motivo de la review: solo se
   distinguirían con nombres que no existen en Sigrid (minúsculas, NFD,
   blancos dobles);
3. la review 13 se limita a verificar este cambio, sin abrir familias nuevas.

### Qué cambió

- **R12-1** (`13a297f`, solo test): en
  `services/postventa-api/tests/test_f036_migracion.py`, la parametrización de
  `test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para` suma los
  ocho nombres de la tabla de la review, cada uno con su comentario de una
  línea por familia: `"Solados y  Alicatados"` (dos espacios), `"Píntura"`,
  `"Albanileria"`, `"Pintura."`, `"Solados-y-Alicatados"`,
  `"Solados y Alicatados M O "` (con el espacio final),
  `"SoladosyAlicatados"` y `unicodedata.normalize("NFD", "Albañilería")`.
  `import unicodedata` ya estaba (R11-2). El test ya se cruzaba con `CATALOGO`
  y `CATALOGO_SIGRID`: son 16 casos nuevos (236 → 252).
- Nada más: ni producción, ni spec, ni otros tests.

### Evidencia: las diez mutaciones, cada una sola, en rojo con el test nuevo

Método (el de la review 11, reconstruido desde la sección «La familia
completa» de la review 12; guion `r12/mutar.py` en el scratchpad, sin
versionar):

- `git archive HEAD` (`13a297f`, el repositorio entero) extraído en 11 copias
  desechables del scratchpad; el `.venv` del servicio real con `cwd` en
  `services/postventa-api` de la copia. El guion **comprueba** que
  `scripts.migracion_f036` se importa de la copia (aserto sobre `__file__`).
- Cada mutación va **sola** en su copia: exige que cada línea a mutar aparezca
  una vez, la sustituye, añade al final del módulo la normalización `_F`, lanza
  `tests/test_f036_migracion.py` y `tests/test_f036_migracion_contenido.py`
  con `--tb=no -q -rf -p no:cacheprovider`; después sustituye el test por el
  de `HEAD~1` (`1186c1d`, sin los ocho nombres) y vuelve a lanzar (fase RED);
  restaura el fichero y comprueba `restaurado`.
- De la salida solo se guardan el resumen y el **id** de cada test caído,
  nunca el mensaje: ningún `repr`.

Las líneas mutadas, en `componer` (`services/postventa-api/scripts/migracion_f036.py`):

```
695 S  original:  if not codigos and nueva.oficio not in nombres_sigrid:
       ambos:     if not codigos and _F(nueva.oficio) not in {_F(s) for s in nombres_sigrid}:
       tabla-tol: if not codigos and nueva.oficio not in nombres_sigrid and _F(nueva.oficio) not in nombres_sigrid:
       sig-suma:  if not codigos and nueva.oficio not in (set(nombres_sigrid) | {_F(s) for s in nombres_sigrid}):
672 O  original:  codigos_de.setdefault((oficio.nombre or "").strip(), []).append(oficio.codigo)
686 O  original:  codigos = codigos_de.get(nueva.oficio, [])
       ambos:     672 con clave _F((oficio.nombre or "").strip())  y  686 codigos_de.get(_F(nueva.oficio), [])
       tabla-tol: 686 codigos = codigos_de.get(nueva.oficio) or codigos_de.get(_F(nueva.oficio), [])
       obra-suma: 672 for _k in {k, _F(k)}: codigos_de.setdefault(_k, []).append(oficio.codigo)   (k, el nombre recortado; el conjunto evita duplicar el código cuando _F(k) == k)
```

Normalizaciones `_F(s)`: `tildes` = NFKD sin combinantes (la ñ incluida);
`punt` = `re.sub(r'[^\w\s]', '', s)`; `punt_esp` = `re.sub(r'[^\w\s]', ' ', s)`;
`blancos_int` = `re.sub(r'\s+', ' ', s)`; `blancos_todos` =
`re.sub(r'\s+', '', s)`; `nfc` = `unicodedata.normalize('NFC', s)`.

Salida real del guion (el nombre del test es siempre
`test_f036_r97_nombre_que_no_es_exactamente_uno_de_la_obra_para`, abreviado a
`r97[…]`; `\xed` y `̃`/`́` son como pytest escapa en el id la «í» y
las combinantes de la forma NFD):

| Mutación | rc (test nuevo) | Resultado (test nuevo) | Tests que caen | rc (test de `1186c1d`) | Resultado (test de `1186c1d`) | restaurado |
|---|---|---|---|---|---|---|
| Base sin mutar (HEAD) | 0 | `252 passed` | — | | | |
| S-tabla-tolerante/tildes | 1 | `1 failed, 251 passed` | `r97[CATALOGO_SIGRID-P\xedntura]` | 0 | `236 passed` | True |
| O-tabla-tolerante/tildes | 1 | `2 failed, 250 passed` | `r97[CATALOGO-P\xedntura]`, `r97[CATALOGO_SIGRID-P\xedntura]` | 0 | `236 passed` | True |
| O-obra-suma/tildes | 1 | `2 failed, 250 passed` | `r97[CATALOGO-Albanileria]`, `r97[CATALOGO_SIGRID-Albanileria]` | 0 | `236 passed` | True |
| S-tabla-tolerante/punt | 1 | `1 failed, 251 passed` | `r97[CATALOGO_SIGRID-Pintura.]` | 0 | `236 passed` | True |
| S-ambos/punt_esp | 1 | `2 failed, 250 passed` | `r97[CATALOGO_SIGRID-Solados y Alicatados M O ]`, `r97[CATALOGO_SIGRID-Solados-y-Alicatados]` | 0 | `236 passed` | True |
| S-sigrid-suma/punt_esp | 1 | `1 failed, 251 passed` | `r97[CATALOGO_SIGRID-Solados y Alicatados M O ]` | 0 | `236 passed` | True |
| S-ambos/blancos_int | 1 | `1 failed, 251 passed` | `r97[CATALOGO_SIGRID-Solados y  Alicatados]` | 0 | `236 passed` | True |
| O-ambos/blancos_int | 1 | `2 failed, 250 passed` | `r97[CATALOGO-Solados y  Alicatados]`, `r97[CATALOGO_SIGRID-Solados y  Alicatados]` | 0 | `236 passed` | True |
| S-sigrid-suma/blancos_todos | 1 | `1 failed, 251 passed` | `r97[CATALOGO_SIGRID-SoladosyAlicatados]` | 0 | `236 passed` | True |
| O-ambos/nfc | 1 | `2 failed, 250 passed` | `r97[CATALOGO-Albañilería]`, `r97[CATALOGO_SIGRID-Albañilería]` | 0 | `236 passed` | True |

Lectura:

- **Las diez caen con el test nuevo y sobreviven con el de `1186c1d`**: es la
  fase RED de R12-1, y coincide con la matriz de la review 12 (eran `VIVO`).
- Cada una cae **solo** por el nombre que la review le asigna, y las de S solo
  con `CATALOGO_SIGRID` (con `oficios_catalogo` vacío la comparación S no se
  alcanza), como anticipaba la review.
- No he lanzado los 29 `VIVO` ni los 20 equivalentes: el encargo pide estas
  diez (una por fila de la tabla de la review); la review dice haber
  ejecutado la sonda de los 29.

### Verificación sobre el código real

En el repositorio, desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f036_migracion.py tests/test_f036_migracion_contenido.py -q --tb=no -p no:cacheprovider
252 passed in 45.95s
```

- `git diff 1186c1d HEAD -- services/postventa-api/scripts/` → **vacío**;
  `git diff -- services/postventa-api/scripts/` (árbol de trabajo) → vacío.
- `ruff check services/postventa-api/tests/test_f036_migracion.py` (desde la
  raíz) → `All checks passed!`.

`bash harness/init.sh`, una vez, tal cual, sobre `13a297f` (sin ningún `repr`
de `Ajustes` en la salida: 0 apariciones de `Ajustes(`):

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[AVISO] Hay features en estado blocked: revisa progress/current.md
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 71 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 7.15s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
6644 passed, 74 skipped in 1255.10s (0:20:55)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 99.9% de 3318 líneas cambiadas cubiertas (3314/3318, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-036-importar-excel
ENTORNO LISTO. Puedes trabajar.
```

La suite de `api` se ha relanzado de verdad (el árbol del servicio cambió):
6628 + 16 casos nuevos = 6644. Los 71 avisos de `ruff` y el de `blocked`
(F-035) son los de antes.

### Evidencias (arreglos de la review 12)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz **62 passed**; `api` **6644 passed, 74 skipped**; `front` en verde (caché). La migración sola: **252 passed** (45,95 s) |
| Fase RED | En copia: las diez mutaciones, cada una sola, **1 o 2 failed** con el test nuevo y **236 passed** con el de `1186c1d` (tabla de arriba) |
| Cobertura de las líneas cambiadas | **99,9 %** (3314/3318, `PUERTA COBERTURA`) |
| Mutación (herramienta) | no relanzada: no cambia producción ni el AST. La de T64 sigue: 16/16 |
| Mutación (a mano) | las diez pedidas (una por fila de la tabla de R12-1) **caen**. De la familia de la review 12: los 29 no equivalentes, cubiertos por los ocho nombres según la sonda de la review (aquí verificadas las diez pedidas); los **20 equivalentes, aceptados en bloque por el humano** (2026-10-04), incluido V11b/R11-3 |
| Tiempo de la suite | `api` dentro de `init.sh`, con cobertura: 1.255,10 s |

### Pendiente y fuera del alcance

- **Review 13**, limitada a verificar este cambio (decisión 3 del humano).
- R10-4 (informativo) y la automejora de la review 12 para
  `.claude/agents/reviewer.md` / `arnes-base`: no son de este encargo.
- T28 otra vez, T29 pasos 4–7 y T30; las cuatro decisiones del spec-author.
- Las copias desechables y el guion están en el scratchpad y no se versionan.
  `git push` no se ha hecho.


## T27–T29 · MANUAL del humano, con el líder (2026-10-02 a 2026-10-05)

Ejecutadas por el humano en el entorno desplegado; el líder cruzó cada paso con
Application Insights (solo lectura). Sin nombres de persona ni de proveedor.

**T27.** Backend y front desplegados desde la rama (el front con `-SoloFront`);
backend redesplegado tras el Bloque 12 y tras el Bloque 13. Grupos de oficio
confirmados en `oficios.html`: 5 grupos de dos códigos. El 2026-10-05 apareció
una propuesta nueva (Solados y Alicatados M.O. 0033 · Solados y Alicatados
0133) y el humano decidió «Son distintos»; el JSON de grupos no cambió
(idéntico byte a byte al del 2026-10-02).

**T28.** Repetida tres veces. La última (2026-10-05), con el guion del líder
que lee el catálogo de Sigrid justo antes de migrar: PASA (0 errores en la ida
y vuelta, original intacto, ningún `.xlsx` en git). Informe aceptado por el
humano (`fa84ec3`): 144 → 158 filas, 14 separadas, 0 descartadas, 47 filas con
oficio ambiguo, 47 proveedores completados por R91, **2 filas sin oficio por
R128** (filas 105 y 106 del original, «V-Aire acondicionado», que ha salido de
la obra en Sigrid). Revisión a mano de R10-3 hecha por el líder: ningún oficio
de la obra del día difiere de ese nombre solo en tildes, mayúsculas, blancos o
puntuación.

**Lo que destapó la primera pasada de T29 (2026-10-03).** El `v2` se había
generado con el catálogo del 2026-09-29 y Sigrid había cambiado los oficios de
la 0677 (18 de 39 filas de `obrofc`): el entorno dio `parcial` con 15 errores
(14 por oficios o pares caducados, 1 por una fila de prueba que el humano dejó
guardada en el `v2`). La aplicación hizo lo correcto. De ahí la undécima
enmienda y el Bloque 14. En la bandeja quedaron 144 filas de esa importación;
las filas cuyo proveedor ha cambiado conservan el de entonces (la bandeja no
compara el proveedor para decidir «ya en bandeja»): se corrigen en F-038.

**T29 (2026-10-05)**, cada paso con su traza en Application Insights:

| Paso | Resultado |
|---|---|
| 1 | 0677 antes: 15 unidades, 1.236 reclamaciones (2026-10-03) |
| 2 | Plantilla de la 0677 con sus 15 unidades, un oficio por grupo y los pares de `obrofc` |
| 3 | Original: 400 `formato_antiguo`, sin Excel de errores |
| 4 | `v2`: `completa`, 158 leídas, 14 nuevas, 144 ya en bandeja, 0 errores (lector 0,4 s) |
| 5 | Copia con 3 filas rotas (unidad en minúsculas, proveedor de otro oficio, descripción de 200): `parcial`, 155 ya en bandeja, 3 con error. Excel de errores con solo esas 3 filas, celda en rojo suave con texto rojo y comentario, sin bandas, 8 desplegables. Corregido (las filas, a sus valores del `v2`, para no meter incidencias falsas en la bandeja real): `completa`, 3 ya en bandeja, 0 errores |
| 6 | El mismo `v2`: «ya se había importado». Guardado desde Excel (COM, sin cambios, otro fichero): `completa`, 0 nuevas, 158 ya en bandeja |
| 7 | Bandeja de la 0677: 158 incidencias, con sus marcas |
| 8 | 0677 después: 1.253 reclamaciones (+8 en la villa 1, +9 en la villa 4). No es F-036: desde el día 3 la Function solo hizo importaciones, bandeja y dos cierres del circuito de partes, que cambian el estado de una reclamación existente y no crean ninguna. Altas manuales de Posventa |
| 8 bis | (a) instancia de 2.048 MB; (b) `lector_aislado: estado=ok … tope_memoria_aplicado=True` en cada importación; (c) fichero de R4-1 (validación con millones de rangos): 400 `fichero_sospechoso`, el hijo topa la memoria a los ~22 s, 25–27 s de petición, ningún 5xx, y la importación siguiente responde con normalidad; (d) proceso de la Function en reposo: 405–430 MB |
| 9 | `v2` con celda en la fila 1.048.576: `completa` en 9,1 s (lector 0,47 s); `v2` con `A1003:A1048576` combinadas: `completa` en 1,7 s; `v2` con millones de `<xf/>`: 400 `fichero_sospechoso` en 0,2 s; `v2` guardado desde Excel: 12.321 elementos XML (límite 60.000) |

Observación para la pantalla de importación (al pasarla al portal, F-035): con
un fichero ya importado, el mensaje «no se ha añadido nada» va acompañado de los
recuentos de la importación original («14 nuevas»), que se leen como si
hubieran entrado otra vez.
