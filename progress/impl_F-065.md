<!-- progress/impl_F-065.md -->
# F-065 · Informe del implementer

## Anotación de base

| Qué | Valor |
|---|---|
| Worktree | `C:\Users\pgris\PycharmProjects\postventa-f065` |
| Rama | `feature/F-065-revision-sigrid-backend` |
| `git merge-base HEAD dev` | `f7f63da32c49273fcdd51c672610b8bde306ed31` (`dev` `f7f63da`) |
| **Base fija del tramo** (guarda de alcance y mutación) | **`b863b46`**: el último commit de spec («S-1 a S-9 aprobadas por el humano»), justo antes del primer commit de código. Lo que hay entre `f7f63da` y `b863b46` es spec y backlog |

## Bloque A1 · T1, T2 y T2 bis (2026-10-28)

Encargo del líder: T1, T2 y T2 bis tal como los describe `tasks.md`; T-A0 y
T-A0 bis son del humano. **No se ha conectado a Sigrid, a la base ni a
SharePoint**: el script solo se ha ejecutado contra un lector doble local.

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `e57a60c` | T1 | Tests RED de `infra/29_reclamaciones_obra_sigrid.ps1` (`tests/test_f065_scripts_infra.py`) |
| `fe78ca8` | T2 | El script 29: la consulta de `design.md` §3, `-CodigoObra` con y sin ceros, `-MaxFilas 500000`, los recuentos de R29 |
| `63d1daa` | T2 bis | `-Unidades` (R70): la consulta de la guarda de §15.5, con sus tests (primero en rojo) |
| `062025c` | T2 bis | El script **ejecutado** contra un lector doble y las comprobaciones por línea entera (salen de la mutación a mano) |
| `aa693fb` | T2 bis | El tramo de 24 meses y el techo alcanzado, ejecutados (los dos últimos supervivientes de la mutación a mano) |
| `e119e9f` | — | T1, T2 y T2 bis marcadas `[x]` en `tasks.md` |
| `2616857` | T2 bis | El test sin avisos de ruff (imports arriba, `check=False`, la fecha local explicada). Sin cambio de lo que comprueba |

### Ficheros tocados

| Fichero | Cambio |
|---|---|
| `infra/29_reclamaciones_obra_sigrid.ps1` | **Nuevo** (729 líneas, ASCII sin BOM, CRLF) |
| `services/postventa-api/tests/test_f065_scripts_infra.py` | **Nuevo** (41 tests) |
| `specs/F-065-revision-sigrid-backend/tasks.md` | Tres casillas `[x]` |

Nada más: ni `08_lectura_sigrid_comun.ps1` (lo usa tal cual), ni código del
servicio, ni `features.json`, `BACKLOG.md` o `current.md`.

### Qué hace el script

- **Solo lectura**, por `08_lectura_sigrid_comun.ps1` (`POST /api/sql/read`).
  Tres consultas, todas `SELECT` con marcadores `?`:
  1. **Q0**, la forma del código que guarda Sigrid: pregunta las dos formas
     (`PadLeft(4, "0")` y `TrimStart("0")`, como el 28 y el 24) y cuántas obras
     con unidades de posventa tiene cada una (`COUNT(DISTINCT v.obride)`, nunca
     el `ide`). A la consulta de la obra va esa forma, recortada.
  2. **Q1**, la que se mide: `$SQL_RECLAMACIONES_DE_LA_OBRA`, **la de
     `design.md` §3 carácter a carácter**, con `RCPCLI`, `PVI-%`, `-Tip` (708)
     y la obra, `max_rows` `-MaxFilas` (500.000 por defecto, de 1 a 500.000) y
     `-Tolerante`. Con `-Unidades`, `$SQL_RECLAMACIONES_DE_LAS_UNIDADES`, la de
     §15.5, con un marcador por unidad.
  3. **Q2** (solo la obra entera), `con.fec` frente a `rcp.fec`: un `SELECT` de
     recuentos (iguales, posterior, anterior, vacías).
- **Imprime solo recuentos, bytes y segundos** con el veredicto del común: si
  la pasarela aceptó la consulta (sin `truncated`), filas, si quedan por debajo
  del techo, columnas, segundos, bytes (todos y los de R33), obras distintas,
  por estado (PTE, SAT, TER, CER, NPR, otro, sin estado), por antigüedad (< 6,
  6–12, 12–24, ≥ 24 meses y sin fecha legible), por unidad (cuántas, mínimo,
  mediana, máximo), sin oficio, sin ubicación, con `PVI-`, por cada uno de los
  19 campos de R33 cuántas lo traen, los grupos (unidad, oficio, ubicación) con
  más de una reclamación y cuántas suman, los pares de la misma unidad
  comparados y los que casarían con 40, 50 y 60. Con `-Unidades`: aceptada,
  `truncated`, filas, columnas, segundos, bytes y **cuántas** unidades.
- **Veredicto**: PASA (0) si la pasarela la acepta sin `truncated`, las filas
  quedan por debajo del techo y llegan las columnas esperadas (31 o 12); si no,
  NO PASA (6). Parámetros malos, 3; un texto donde iba una cifra, 5.

### Decisiones

1. **ASCII sin BOM y CRLF**, como dicen R29 y T1 y la excepción de `infra/` de
   `docs/CONVENTIONS.md` (`test_f010_prompt_keys_infra.py` lee todos los `.ps1`
   como `ascii`). El encargo decía «UTF-8 con BOM si lo piden los tests del
   resto de scripts»: no lo piden, piden lo contrario.
2. **El SQL se manda en LF.** El fichero es CRLF y el texto del adaptador
   (Bloque A3) será LF; para que a la pasarela llegue **el mismo** texto,
   `ConvertTo-SqlConLf` lo convierte y toda consulta pasa por ahí (lo fija un
   test). Comprobado ejecutándolo: lo que llega al lector doble es idéntico,
   byte a byte, a §3 y a §15.5 con 1, 2 y 5 unidades.
3. **Columnas por posición.** La consulta de §3 no lleva alias (es la del
   adaptador) y la respuesta repite `cod`, así que `Get-SigridValor` (por
   nombre) no sirve; el script comprueba **antes** que llegan 31 (o 12) y, si
   no, da el veredicto sin contar nada.
4. **`-Tolerante` en Q1**: si la pasarela rechaza la consulta (el `OUTER
   APPLY`) o viene `truncated`, el común lo avisa sin el cuerpo y devuelve
   `$null`; el script lo convierte en «la pasarela acepto la consulta, sin
   truncated: no» y NO PASA, con los segundos. Sin `-Tolerante` saldría con un
   `exit 4` a medias.
5. **Q0 no exige una sola obra**: la 0677 tiene dos filas en el maestro de
   obras (ayuda del 24), y contarlas es justo lo que R6/R9 quieren
   (`obra_ambigua`). Si existen las dos formas del código, va la tecleada.
6. **Q2 es una consulta aparte** porque la de §3 no lee `rcp.fec` y su texto
   no puede cambiar; solo cuenta.
7. **Nada de una fila sale por la consola.** Toda cifra pasa por
   `Anotar-Cifra`, que la valida con `TryParse` y, si no es una cifra, para con
   5 **sin repetirla** (un `[double]` en la firma la repetiría en el error de
   conversión). Las etiquetas que cambian salen de listas constantes del script.
   `Write-Host` y los mensajes de `Salir-Con` solo llevan variables de una lista
   cerrada (la obra tecleada y sus formas, el tipo, el techo, el modo).
8. **Los bytes se aproximan** (dicho en la ayuda): el común devuelve la
   respuesta ya leída, así que se cuentan como su JSON compacto en UTF-8; los de
   R33, cada valor con su coma. Si la pasarela escapa las tildes como
   `\uXXXX`, los reales son algo más. El test los compara con
   `json.dumps(..., separators=(",", ":"), ensure_ascii=False)`.
9. **El parecido se aproxima en PowerShell** (dicho en la ayuda), con la regla
   entera de §5.3 (parecido ≥ umbral y ≥ 2 palabras en común, o 100); la buena
   será la del dominio (Bloque A2). Unidad y oficio por código exacto
   (`Dictionary` ordinal: un `@{}` de PowerShell no distingue mayúsculas); la
   ubicación del ruido de R14, `NFC`, recortada y en minúsculas
   (`clave_de_ubicacion`).
10. **Relleno de R33**: ni nulo ni en blanco; la fecha prevista a 0 no cuenta
    (es «sin fecha»); `rcptip` 0 sí (es un valor de la forma de comunicación).
11. **Antigüedad**: meses cumplidos desde `con.fec`; el tramo de 24 meses
    exactos cuenta en «mas de 24» (R29 escribe «12–24 y > 24» sin decir dónde
    va el 24: la frontera queda fijada por un test).
12. **`-Unidades` se parte por comas.** Con `powershell -File` (el comando de
    T-A0 bis) la lista `'<u1>','<u2>'` llega como **un** texto con comas;
    comprobado lanzándolo desde PowerShell. Se recortan y se quitan los vacíos;
    de 1 a 50 (las partes de una llamada del ensayo, F-059 R30).
13. **Desviación de `tasks.md` (P-4).** `tasks.md` dice que el implementer no
    ejecuta `init.sh`; el encargo del líder pide ejecutarlo al final, y se ha
    hecho (abajo).

### Un fallo encontrado por el camino

La primera versión de T2 bis guardaba la lista en `$unidades = @()`: las
variables de PowerShell **no distinguen mayúsculas**, así que eso borraba el
parámetro `$Unidades` antes de leerlo, y el script respondía «sin ninguna
unidad». Los tests de lectura no lo vieron (el texto era correcto); lo vio la
ejecución contra el doble. La lista se llama ahora `$codigosDeUnidad` y un test
prohíbe `$unidades =` en cualquier grafía.

## Fase RED

### T1 (`e57a60c`): el script no existe

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f065_scripts_infra.py -q
E       FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-f065\\infra\\29_reclamaciones_obra_sigrid.ps1'
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\pathlib.py:1013: FileNotFoundError
=========================== short test summary info ===========================
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_el_script_existe - Ass...
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_empieza_por_su_ruta - ...
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_ascii_puro_sin_bom_y_crlf
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_tiene_ayuda_con_parametros_y_ejemplos
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_la_ayuda_dice_lo_que_hace_y_lo_que_no
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_carga_el_comun_y_solo_lee_por_el
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_no_escribe_en_disco_ni_lanza_nada
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_hay_consultas_y_todas_son_select_con_marcadores
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_ninguna_consulta_nombra_lo_vetado_de_r33
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_la_consulta_de_la_obra_es_la_de_design_caracter_a_caracter
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_el_sql_viaja_con_saltos_lf_como_el_del_adaptador
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_los_parametros_van_en_el_orden_de_los_marcadores
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_la_obra_con_y_sin_ceros_como_el_28
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_la_pasarela_tiene_que_aceptarla_y_sin_truncar
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_nada_de_una_fila_sale_por_la_consola
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_anotar_cifra_solo_deja_pasar_cifras_y_no_repite_lo_que_recibe
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_las_etiquetas_variables_salen_de_listas_constantes
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_imprime_los_recuentos_de_r29
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_los_campos_de_r33_son_los_diecinueve_y_en_su_columna
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_las_columnas_de_trabajo_estan_en_su_sitio
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_el_parecido_es_el_de_r36_aproximado
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_los_grupos_y_las_unidades_distinguen_mayusculas
FAILED tests/test_f065_scripts_infra.py::test_f065_r29_ningun_valor_en_el_fichero
23 failed, 3 passed in 3.30s
```

Los 3 que pasan son los **controles negativos** (`los_detectores_no_son_ciegos`,
`el_detector_de_impresion_no_es_ciego`) y `el_comun_sigue_siendo_de_solo_lectura`:
no dependen del script nuevo. Que pasen en RED es la prueba de que los
detectores cazan lo que tienen que cazar.

Primera ejecución tras escribir el script: `1 failed, 25 passed`
(`ascii_puro_sin_bom_y_crlf`: la ayuda llevaba una `á` en el ejemplo de
`\uXXXX`); corregido, `26 passed`.

### T2 bis (`63d1daa`): el script de T2 no tiene `-Unidades`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_scripts_infra.py -q
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_admite_unidades_y_lo_explica
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_la_consulta_de_la_guarda_es_la_de_design_con_una_y_con_cinco
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_la_guarda_es_la_de_la_obra_sin_r33_y_con_el_filtro_de_unidades
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_un_marcador_por_unidad_y_los_parametros_en_orden
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_la_lista_se_parte_por_comas_y_tiene_tope
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_imprime_cuantas_unidades_y_no_cuales
FAILED tests/test_f065_scripts_infra.py::test_f065_r70_con_unidades_no_hace_las_cuentas_de_la_obra
7 failed, 26 passed in 0.97s

$ .venv/Scripts/python.exe -m pytest tests/test_f065_scripts_infra.py -q -k r70
E       assert '[string[]]$Unidades' in '\n\n[CmdletBinding()]\nparam(\n    [string]$CodigoObra,\n    [string]$SigridBaseUrl,\n    [string]$SigridBaseDatos,\n..."con.fec vacia" -Valor (Get-CifraDeColumna $fechas "con_vacia")\n}\n\nEscribir-Veredicto -Titulo "MEDICION DE LA OBRA"'
E       assert '$MARCADORES = "__MARCADORES__"' in '\n\n[CmdletBinding()]\nparam(\n    [string]$CodigoObra, ...'
E       AssertionError: no hay un here-string $SQL_RECLAMACIONES_DE_LAS_UNIDADES
E       assert '$parametros = @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraCod) + $unidades' in '...'
E       assert '-split ","' in '...'
E       assert 'Anotar-Cifra -Que "unidades pedidas" -Valor $unidades.Count' in '...'
E       ValueError: substring not found
```

Con `-Unidades` escrito: `2 failed, 31 passed`. Los dos eran **fallos de los
propios tests**, no del script, y se corrigieron sin aflojar lo que comprueban:
`admite_unidades` buscaba el ejemplo con `[^.]*?`, que se paraba en el punto
de `infra\29_….ps1` (ahora parte la ayuda por `.EXAMPLE`); y
`con_unidades_no_hace_las_cuentas` tomaba el **primer** `if ($conUnidades)`
(el del rótulo) en vez del que cierra la guarda (ahora, el último antes de su
veredicto). Después, `33 passed`. La lista se renombró a `$codigosDeUnidad`
por el fallo de arriba (en los tests y en el script).

## Tests

`tests/test_f065_scripts_infra.py`, **41 tests**, todos `test_f065_r29_…`,
`test_f065_r70_…` o `test_f065_r8_r29_…`:

- **Leyendo el script** (34): fichero (existe, ruta, ASCII/CRLF/sin BOM,
  ayuda), solo lectura por el común, ninguna escritura a disco ni otra salida,
  las consultas (`SELECT`, `?`, sin `$`, sin lo vetado de R33), **§3 y §15.5
  carácter a carácter** (1 y 5 unidades), Q0 y Q2 enteras, el paso a LF,
  parámetros y constantes **por línea entera**, la obra con y sin ceros, el
  rechazo y el techo, las reglas de impresión (con su detector y su control no
  ciego), `Anotar-Cifra`, las listas constantes, los 19 campos de R33, las
  columnas, el parecido de §5.3, el `Dictionary`, ningún valor dentro (GUID,
  host, credencial, `RS..`, correo, IP, código de obra, el nombre de la base,
  los recursos de F-010), `-Unidades` (partido por comas, tope 50, cuántas y
  no cuáles, sin cuentas de la obra).
- **Ejecutándolo** contra un lector doble (7): el `08` de verdad con
  `Invoke-SigridLectura` redefinida al final, 14 reclamaciones inventadas
  (`Ejemplo …`, `@ejemplo.invalid`, `000 000 000`, R39) y raíz
  `http://pasarela.ejemplo.invalid`. Fijan: que **ningún valor de las filas**
  sale por la consola (obra y guarda); el texto y los parámetros exactos que
  llegan a la pasarela, en orden; **las 58 cifras** de R29 sobre esos datos;
  la guarda con `"VILLA 05, ,VILLA 07"`; el rechazo (sale 6); un texto en una
  cifra (sale 5 sin repetirlo); y el techo alcanzado (sale 6). Se saltan si
  el puesto no tiene PowerShell.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_scripts_infra.py -q
.........................................                                [100%]
41 passed in 9.90s

$ .venv/Scripts/python.exe -m pytest tests/test_f010_prompt_keys_infra.py tests/test_f036_scripts_infra.py tests/test_f059_scripts_infra.py tests/test_f010_scripts_infra.py tests/test_f065_scripts_infra.py -q
296 passed, 3 skipped in 4.08s     (antes del lector doble; los barridos de todo infra/ siguen en verde)
```

**Humo a mano** (scratchpad, sin red, mismo doble): el comando de T-A0 y los
dos de T-A0 bis lanzados **desde PowerShell** con la sintaxis de `tasks.md`;
lo que llegó al doble, comparado con los textos de los tests: obra, 1 unidad y
5 unidades, **idénticos**; parámetros `RCPCLI|PVI-%|708|0999[|unidades…]`.

## Mutación

### La herramienta

```
$ python -m harness.mutacion --feature F-065 --base b863b46 --salida progress/mutacion_F-065_bloqueA1.md
F-065: 0 fichero(s), 0 línea(s) de producción (origen rama, b863b466c168c913279aff21a7e3e148b63d36d8..feature/F-065-revision-sigrid-backend)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
```

Sobre `HEAD` `e119e9f`, árbol limpio (`2616857`, después, solo toca el fichero de tests: el alcance sigue en 0 líneas). Informe: `progress/mutacion_F-065_bloqueA1.md`.
**El motor no entra en un `.ps1`**: `harness/alcance.py` solo cuenta `.py`
(línea 134, `if not normalizada.endswith(".py")`) y los tests no son
producción. Así que el bloque da 0 líneas en alcance, como ya dejaron escrito
`test_f036_scripts_infra.py` y `test_f059_scripts_infra.py`.

### A mano (lo que la herramienta no muta)

La spec no prevé nada propio para los `.ps1`; se ha seguido el precedente de
F-059 («Mutantes a mano», `progress/impl_F-059.md`): **58 mutantes** sobre el
script, aplicados uno a uno en un **worktree desechable** (`git worktree add
--detach`, borrado al acabar) con un guion del scratchpad que sustituye una
ocurrencia, ejecuta `pytest tests/test_f065_scripts_infra.py -x` y restaura.

| Ronda | Tests | Muertos | Supervivientes | Tiempo |
|---|---|---|---|---|
| 1 (`63d1daa`) | 33, solo leyendo | 36/58 | 22 | 251 s |
| 2 (`062025c`) | + ejecutado, + líneas enteras | 56/58 | M40, M44 | ≈ 290 s |
| 3 (`aa693fb`) | + 24 meses, + techo | **58/58** | **0** | 291 s |

Los 22 supervivientes de la ronda 1 eran **huecos reales**: M08 y M47 (Q0/Q2
sin comprobar enteras), M09/M14/M20 (`in` de subcadena: `= 500` contiene
`= 50`, y la línea de la guarda empieza como la de la obra), M16 (solo se
miraba **una** de las dos asignaciones de `$sql`), y la lógica de las cuentas
(M29, M38–M48, M51–M54, M56), que solo puede fijarse ejecutando. Ronda 2:
M40 (no había una fecha de 24 meses justos) y M44 (nunca se llegaba al techo).

| Id | Mutación | Test que lo caza (ronda 3) |
|---|---|---|
| M01 | sin cargar el `08` | `carga_el_comun_y_solo_lee_por_el` |
| M02, M04, M06 | §3: `LIKE`→`=`, sin `pc.ele`, sin `LTRIM` | `la_consulta_de_la_obra_es_la_de_design_caracter_a_caracter` |
| M03, M07, M18, M19 | §15.5: `LIKE`→`=`, sin `LTRIM`, separador `,`, un marcador de más | `la_consulta_de_la_guarda_es_la_de_design_con_una_y_con_cinco` |
| M05 | §3 con `pr.dni` | `ninguna_consulta_nombra_lo_vetado_de_r33` |
| M08, M47 | Q2 sin `LTRIM`; `>` → `>=` | `las_consultas_auxiliares_son_las_que_dice_la_ayuda` |
| M09, M11–M14, M57 | parámetros cruzados; `MaxFilas` 1000; techo 1.000.000; `max_rows` 1000; sin `-Tolerante`; `Tip` 709 | `los_parametros_van_en_el_orden_de_los_marcadores` |
| M10 | la guarda sin las unidades | `un_marcador_por_unidad_y_los_parametros_en_orden` |
| M15 | `-eq $null` → `-ne` | `la_pasarela_tiene_que_aceptarla_y_sin_truncar` |
| M16, M17 | el SQL de la obra sin LF; `ConvertTo-SqlConLf` que no convierte | `el_sql_viaja_con_saltos_lf_como_el_del_adaptador` |
| M20, M21 | tope 500; sin partir por comas | `la_lista_se_parte_por_comas_y_tiene_tope` |
| M22 | la guarda no para antes de las cuentas | `con_unidades_no_hace_las_cuentas_de_la_obra` |
| M23–M25 | Q0 sin las dos formas; `PadLeft(5)`; `TrimStart(" ")` | `la_obra_con_y_sin_ceros_como_el_28` |
| M26 | `$COL_ESTADO = 1` | `las_columnas_de_trabajo_estan_en_su_sitio` |
| M27, M58 | R33 en otra columna; R33 desde la 13 | `los_campos_de_r33_son_los_diecinueve_y_en_su_columna` |
| M28, M37 | sin `NPR`; umbral 70 | `las_etiquetas_variables_salen_de_listas_constantes` |
| M30, M31 | `porUnidad` / `grupos` en `@{}` | `los_grupos_y_las_unidades_distinguen_mayusculas` |
| M32–M36, M55 | sin `del`; `-lt 4`; plural desde 6; una palabra basta; `Ceiling`; sin quitar tildes | `el_parecido_es_el_de_r36_aproximado` |
| M29, M38–M43, M45, M46, M48, M51–M54, M56 | `-contains`; tramos 7/≤12/25; sin ajuste del día; blanco relleno; fecha prevista 0; bytes sin comillas; R33 sin la primera; sin contar obras; `Anotar-Cifra` sin validar; ubicación sin minúsculas; descripción vacía casa; sin la regla del 100; sin palabras vacías | `ejecutado_cuenta_lo_que_pide_r29` |
| M44 | techo con `-le` | `r8_r29_ejecutado_llegar_al_techo_no_es_quedar_por_debajo` |
| M49, M50 | `Write-Host $descripcion`; `Anotar … $unidad` | `nada_de_una_fila_sale_por_la_consola` |

Ningún mutante equivalente aceptado. Lo que **no** se ha mutado: la ayuda (no
se ejecuta) y los textos de los mensajes de error.

## `init.sh`

**Primera ejecución**, sobre `e119e9f` (todo el bloque), `bash harness/init.sh`
tal cual: **exit 0, `ENTORNO LISTO`**.

```
[OK] Arnés v1.5.2 (2026-08-18)
    68 features, 39 abiertas, en curso: ['F-065'], bloqueadas: ['F-038', 'F-040', 'F-066']
[OK] features.json válido
[OK] BACKLOG.md al día
[AVISO] Hay features en estado blocked: revisa progress/current.md
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 85 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
115 passed in 8.88s
[OK] pytest en verde (con medición de cobertura)
9143 passed, 365 skipped in 3175.68s (0:52:55)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-065-revision-sigrid-backend
ENTORNO LISTO. Puedes trabajar.
```

Los 85 avisos de ruff incluían **9 de este fichero de tests** (imports a
media página, una variable sin usar, `subprocess.run` sin `check`, un
`date.today()`): corregidos en `2616857` (`ruff check` del fichero: «All checks
passed!»; `41 passed`). El tiempo de la suite (53 min) es el de un puesto
cargado: había otras campañas de mutación de otros proyectos a la vez.

**Segunda ejecución**, sobre `2616857` (estado final del código):

```
[AVISO] ruff: 76 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
115 passed in 22.19s
[OK] pytest en verde (con medición de cobertura)
9143 passed, 365 skipped in 3605.53s (1:00:05)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)
ENTORNO LISTO. Puedes trabajar.
```

**Exit 0.** Ruff baja de 85 a 76 avisos: los 9 eran de este fichero, y los 76
que quedan son deuda previa de otros ficheros.

## Órdenes para el humano (MANUAL, solo lectura)

No se han ejecutado. Se lanzan desde la raíz del repositorio en el puesto del
humano; la clave de la pasarela la pide el script por consola como
`SecureString` si no está en `$env:SIGRID_API_KEY`. Lo que se copie a este
informe: **solo** la tabla del veredicto (recuentos, bytes y segundos), que es
lo único que imprime.

### T-A0 (antes del Bloque A2)

```
powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0626 -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
```

Anotar de cada una: «la pasarela acepto la consulta» (es la respuesta a si
acepta el `OUTER APPLY`), `truncated`, filas, «filas por debajo del techo»,
segundos, los bytes (todos y los de R33), por estado, por antigüedad, por
unidad, sin oficio / sin ubicación / con `PVI-`, los 19 «R33 rellenos», los
grupos de R14 y sus filas, los pares con 40/50/60, y `con.fec` frente a
`rcp.fec`. Si Q1 tarda más de ≈ 10 s, si el umbral 50 o la fecha cambian, el
líder vuelve al humano y se enmienda la spec **antes** del Bloque A2.

### T-A0 bis (junto con T-A0, antes del Bloque A4 bis)

```
powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -Unidades 'VILLA 15' -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -Unidades '<u1>','<u2>','<u3>','<u4>','<u5>' -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
```

Cinco unidades cualesquiera de la 0677, las que elija el humano (el código de
la unidad tal cual, `con.cod`). **Cada comando tres veces** (los picos de
F-061), y también la de la obra entera de T-A0 tres veces. Anotar **solo**
filas, `truncated`, bytes y segundos de cada ejecución. Umbrales para volver al
humano antes del Bloque A4 bis: obra > ≈ 10 s, guarda > ≈ 3 s.

## Pendiente

- **T-A0 y T-A0 bis** (humano), y con sus números, la decisión del líder sobre
  N-1, N-2, la fecha y S-5 antes de los Bloques A2 y A4 bis.
- **Review del Bloque A1.** Bloque A2 no empezado (por encargo).
- **T15** cambia `SQL_DE_UNA_UNIDAD`/`SQL_DE_CINCO_UNIDADES` por la función
  `select_reclamaciones_de_las_unidades`, y **T5** compara el SQL del adaptador
  con el `$SQL_RECLAMACIONES_DE_LA_OBRA` del script.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests del bloque | **41 passed** (`tests/test_f065_scripts_infra.py`), 18.48 s tras `2616857` |
| Suite entera (`init.sh`, `2616857`) | **9143 passed, 365 skipped**, servicio api; front, caché en verde; la raíz, 115 passed |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)`. El `.ps1` no se mide; lo cubren los 7 tests que lo ejecutan |
| Mutación (herramienta) | **0 generados, 0 supervivientes**: 0 líneas `.py` de producción en alcance; el motor no muta `.ps1`. 0.0 s, workers: la herramienta escribe `--workers 1` en la cabecera (sin nada que repartir) |
| Mutación a mano (`.ps1`) | **58 generados, 58 muertos, 0 supervivientes** (ronda 3, 291 s, en serie en un worktree desechable); ronda 1: 22 supervivientes, todos cerrados con tests |
| Tiempo de la suite | **3605.53 s** (1:00:05) en la 2.ª ejecución, 3175.68 s en la 1.ª: un puesto cargado con otras campañas. Los 41 tests del bloque: 9.9–18.5 s (los 7 que lanzan PowerShell suman la mayor parte) |

## Corrección C-A1-1 (2026-10-28)

Encargo del líder: corregir **solo** C-A1-1 de `progress/review_F-065.md`. El
script `infra/29_reclamaciones_obra_sigrid.ps1` **no se ha tocado** (el humano
lo lanza contra Sigrid mientras tanto): el test nuevo confirma que sus
precondiciones ya van antes de la primera llamada al ERP. Sin conexión a
Sigrid, a la base ni a SharePoint. Bloque A2 no empezado.

### Qué cambió

Commit `4fa1b61`, solo `services/postventa-api/tests/test_f065_scripts_infra.py`:

- `_lanzar` admite `obra: str | None = "999"` (solo por nombre); con `None` no
  pasa `-CodigoObra`. Las llamadas de siempre no cambian.
- `PARAMETROS_MALOS` y
  `test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer`
  (`@necesita_powershell`, parametrizado, seis casos): `-MaxFilas 0`,
  `-MaxFilas 500001`, `-Unidades " , "`, `-Unidades` con 51 códigos
  (`",".join(...)`, `U00`..`U50`), `-CodigoObra "0 9"` y sin `-CodigoObra`.
  Cada uno exige **salida 3**, **`llamadas == []`** (no se llega ni a Q0) y el
  trozo del mensaje de la comprobación que tiene que saltar, para que un 3
  dado por otra comprobación no lo dé por bueno.

### Fase RED

El script ya era correcto, así que el test pasa nada más escribirse (6 passed
en 24.72 s). La RED que importa aquí es la de los mutantes de la review: el
test tiene que caer cuando una comprobación baja por debajo de la lectura.
Aplicados en una **copia desechable** del scratchpad (`infra/` y
`services/postventa-api/` sin `.venv`, borrada al acabar; el árbol de trabajo
no se ha tocado), con un guion que mueve el bloque de la comprobación justo
detrás de `$reloj.Stop()` (el sitio de R08/R09 en la review), ejecuta los
tests y restaura.

Comando (desde el scratchpad, intérprete del servicio):

```
.venv/Scripts/python.exe -I traza_c_a1_1.py <copia> R08 R09 RC1
  -> pytest tests/test_f065_scripts_infra.py -q --tb=short -k parametro_malo
```

Traza real (recortada solo en las líneas repetidas):

```
=== R08 (39.6 s) exit=1
FF....                                                                   [100%]
_ test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer[maxfilas_0] _
tests\test_f065_scripts_infra.py:1268: in test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer
    assert llamadas == []
E   AssertionError: assert [('SELECT LTR...708\x1f0999')] == []
E     Left contains 2 more items, first extra item: ('SELECT LTRIM(RTRIM(o.cod)) AS obra_cod, COUNT(DISTINCT v.obride) AS obras\nFROM dbo.upv v\nJOIN dbo.con o ON o.ide = v.obride\nWHERE LTRIM(RTRIM(o.cod)) IN (?, ?)\nGROUP BY LTRIM(RTRIM(o.cod))', '10\x1fFalse\x1f0999\x1f999')
_ test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer[maxfilas_500001] _
    assert llamadas == []
E   AssertionError: assert [('SELECT LTR...708\x1f0999')] == []
FAILED ...[maxfilas_0]
FAILED ...[maxfilas_500001]
2 failed, 4 passed, 41 deselected in 28.63s

=== R09 (32.8 s) exit=1
...F..                                                                   [100%]
_ test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer[unidades_51] _
    assert llamadas == []
E   AssertionError: assert [('SELECT LTR...fU49\x1fU50')] == []
E     Left contains 2 more items, first extra item: ('SELECT LTRIM(RTRIM(o.cod)) AS obra_cod, ...', '10\x1fFalse\x1f0999\x1f999')
FAILED ...[unidades_51]
1 failed, 5 passed, 41 deselected in 16.51s

=== RC1 (17.3 s) exit=1
....F.                                                                   [100%]
_ test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer[obra_no_valida] _
    assert llamadas == []
E   AssertionError: assert [('SELECT LTR...708\x1f0999')] == []
E     Left contains 2 more items, first extra item: ('SELECT LTRIM(RTRIM(o.cod)) AS obra_cod, ...', '10\x1fFalse\x1f00 9\x1f 9')
FAILED ...[obra_no_valida]
1 failed, 5 passed, 41 deselected in 11.71s
```

Lo que dice la traza: en los tres, **la salida sí es 3** (la primera aserción
pasa) y aun así cae, porque la pasarela ya habría recibido Q0 y Q1 (en R09,
la guarda con los 51 marcadores, `...U49\x1fU50`). Es justo lo que C-A1-1
pedía fijar: salir con 3 no basta, hay que salir **antes**.

### Mutantes

Suite de F-065 **entera** (sin `-k`, sin `-x`) sobre cada mutante, para ver
quién lo caza. Antes de C-A1-1, R08 y R09 dejaban 41 passed (review).

| Id | Mutación (bloque movido detrás de `$reloj.Stop()`) | Resultado | Lo caza |
|---|---|---|---|
| R08 | la de `-MaxFilas` (1..500.000) | **muerto** (2 failed, 45 passed) | `…parametro_malo…[maxfilas_0]` y `[maxfilas_500001]`, solo esos |
| R09 | el tope de 50 unidades | **muerto** (1 failed, 46 passed) | `…[unidades_51]`, solo ese |
| RC1 | el código de obra no válido (la del código, pedida «de paso») | **muerto** (1 failed, 46 passed) | `…[obra_no_valida]`, solo ese |
| RC2 | extra: «Falta -CodigoObra» | **muerto** (1 failed, 46 passed) | `…[sin_obra]`, solo ese |
| RC3 | extra: `-Unidades` sin ninguna unidad | **muerto** (6 failed, 41 passed) | `…[unidades_vacia]` y cinco ejecutados más |

RC3 lo cazan más tests porque, al sacar el bloque de su `if
($PSBoundParameters…)`, la comprobación salta también sin `-Unidades` y la
medición de la obra entera sale con 3; aun así, el caso `unidades_vacia` del
test nuevo cae por sí solo. **5 generados, 5 muertos, 0 supervivientes.**
Ningún equivalente. Copia desechable borrada al acabar; `git status` del
worktree limpio salvo los cambios de este encargo.

### Verificación

| Qué | Resultado |
|---|---|
| `pytest tests/test_f065_scripts_infra.py` (servicio api) | **47 passed in 26.50 s** (41 de antes + 6 nuevos) |
| Barridos de `infra/` (`test_f005`, `f006`, `f009`, `f010_prompt_keys`, `f010`, `f012`, `f013`, `f036`, `f051`, `f059`, `f065` `_scripts_infra.py`) | **529 passed, 3 skipped in 35.62 s** |
| `ruff check` del fichero de tests | **All checks passed!** (`ruff format --check` lo reformatearía, pero ya pasaba igual antes del cambio y `init.sh` solo mide `ruff check`) |
| `bash harness/init.sh` | **No ejecutado** por encargo: lo lanza el líder |

### Pendiente

- `init.sh` entero (el líder) y la re-review de C-A1-1.
- Lo demás de la review (O-1 a O-4) no es de este encargo.

### Evidencias de la corrección

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 47 passed (F-065), 529 passed + 3 skipped (barridos de `infra/`) |
| Cobertura de las líneas cambiadas | N/A: el cambio es solo de tests; el `.ps1` no se mide |
| Mutación (herramienta) | 0: no hay líneas `.py` de producción en alcance |
| Mutación a mano (`.ps1`) | **5 generados, 5 muertos, 0 supervivientes** (R08, R09, RC1, RC2, RC3), ≈ 175 s en serie |
| Tiempo | 26.50 s los tests de F-065; 35.62 s los barridos |

## T-A0 y T-A0 bis · resultado del humano (2026-10-28, lo anota el líder)

Lanzado por el humano desde su puesto, solo lectura, con el script 29 de `f715576`. Solo recuentos, bytes y segundos.

| Medición | Filas | `truncated` | Bytes (todos / R33) | Segundos (3 ejecuciones) |
|---|---|---|---|---|
| 0626 entera | 7 | no | 1.776 / 739 | 1,21 (una) |
| 0677 entera | 1.345 | no | 493.218 / 260.168 | 0,83 · 0,62 · 0,77 |
| Guarda 0677, 5 unidades | 0 | no | 2 | 0,49 · 0,10 · 0,12 y 0,14 · 0,10 · 0,13 |

- La pasarela acepta la consulta de §3 (con el `OUTER APPLY`), 31 columnas; la guarda de §15.5, 12 columnas.
- 0677: 10 unidades con reclamaciones (mínimo 2, mediana 159, máximo 261); PTE 309, SAT 23, TER 135, CER 719,
  NPR 159; todas con menos de 6 meses; sin oficio 8, sin ubicación 2, con `PVI-` 0. Ruido de R14: 272 grupos con
  857 reclamaciones. Pares de la misma unidad: 132.347; con parecido ≥ 40: 1.254, ≥ 50: 874, ≥ 60: 465.
- `con.fec` igual a `rcp.fec` en las 1.345 (y en las 7 de la 0626).
- **Fallo del guion del líder**: con `powershell -File`, la lista `-CincoUnidades` llegó como un solo texto con
  comas, así que las tres ejecuciones «de 1 unidad» pidieron también las 5. Y las 5 unidades tecleadas
  (`VILLA 15`…`VILLA 11`) no casan con el código de Sigrid: 0 filas. La guarda se ha medido, pues, sin filas.
  Cota superior: la guarda lee un subconjunto de la consulta de la obra y sin R33, y la obra entera tarda < 1 s.

### Decisiones del líder con estas cifras

- **N-1**: sin lectura por trozos (0,6–0,8 s frente al umbral de ≈ 10 s; 493 KB).
- **Fecha**: indiferente, `con.fec` = `rcp.fec` en todas; se queda la de la spec.
- **N-2**: el umbral 50 se queda; las cifras no dan motivo para moverlo (874 de 132.347 pares, un 0,66 %).
- **S-5**: la guarda por unidades se queda; muy por debajo de ≈ 3 s (cota: < 1 s la obra entera).
- No se enmienda la spec. Pendiente, no bloqueante: medir la guarda con códigos de unidad reales de la 0677.

## Bloque A2 · T3 y T4 (2026-10-28)

Encargo del líder: T3 y T4 tal como los describe `tasks.md`, con N-1, N-2
(umbral 50, 2 palabras en común), la fecha y S-5 como dice la spec (no se ha
tocado nada de eso). **Sin red, sin base, sin IA, sin Sigrid ni SharePoint**;
ni adaptadores, ni rutas, ni nada del Bloque A3. `features.json`, `BACKLOG.md`
y `current.md` sin tocar.

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `3282d8b` | T3 | Tests RED de `domain/models/sigrid_bandeja.py` (`tests/test_f065_dominio.py`) |
| `96d9f54` | T4 | El dominio (`design.md` §10.1); T3 y T4 `[x]` en `tasks.md`; el test de coste con otros datos (ver «Desviaciones») |
| `718a633` | T4 | Sin GUID literal en el test (lo rechazaba la guarda de F-006) e inmutabilidad fijada (los 5 supervivientes de la primera pasada de mutación) |
| (el de este informe) | — | Este informe y `progress/mutacion_F-065_bloqueA2.md` |

### Ficheros tocados

| Fichero | Cambio |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | **Nuevo**: `EstadoSigrid`, `ABIERTAS`, `CERRADAS`, las constantes de §10.1 (más `MIN_LETRAS` 3 y `MIN_LETRAS_PLURAL` 5 de R36, con nombre para no dejar números sueltos), `Severidad`, `Criterio`, `TipoHallazgo`, `EVALUABLES`, `ReclamacionSigrid`, `Hallazgo`, `Cruce`, `palabras_significativas`, `parecido`, `incidencia_de_referencia`, `cruzar` |
| `services/postventa-api/tests/test_f065_dominio.py` | **Nuevo**: 108 funciones, **137 tests** con los parametrizados |
| `specs/F-065-revision-sigrid-backend/tasks.md` | T3 y T4 `[x]` |

Sin tocar `revision.py`, `normalizacion.py`, `plantilla_incidencias.py` ni
`volcado.py`: se importan `estado_de`, `valores_vigentes`, `EstadoRevision`,
`SituacionDeRevision`, `clave_de_ubicacion`, `normalizar_para_clave`,
`plegar` y `PREFIJO_REFERENCIA`. Nada más del servicio importa el módulo nuevo.

### Decisiones de diseño

- **`FichaReclamacion` solo bajo `TYPE_CHECKING`.** §10.1 la tipa con la
  clase del puerto (`domain/ports/reclamaciones_obra.py`), que crea T6 en el
  Bloque A3. El módulo la importa solo para la anotación (con `from __future__
  import annotations` no se evalúa), así que funciona hoy sin crear el puerto
  antes de tiempo. Los tests pasan una ficha inventada cualquiera
  (`SimpleNamespace`): el cruce no la mira. En A3 la importación ya resuelve.
- **El cruce es por unidad**: un índice `unidad_codigo → candidatas`, con la
  severidad, la clave de ubicación y las palabras de cada reclamación
  calculadas **una vez**. Las `NPR` y las de estado desconocido no entran en
  el índice (no dan pares, R17).
- **Lo barato primero** en la descripción: si no hay 2 palabras en común no
  se calcula el Jaccard. Y cada texto se pliega una sola vez (la clave es el
  plegado sin la puntuación final, que de todos modos separa palabras).
- **`_codigo_guardado` sin guarda**: una `volcada` siempre tiene parte en
  Sigrid (sale de ahí, R1 de F-059); la guarda defensiva era una línea
  inalcanzable y un mutante equivalente.
- `coincidencias_total` es un `MappingProxyType` (no se puede tocar desde
  fuera) con solo las incidencias que tienen algún `coincide`; el borde (A4)
  usará `get(…, 0)` para las demás.

### Lecturas de la spec que he tenido que concretar (para la review)

Ninguna cambia una decisión aprobada; son detalles que la spec no fija del
todo. Cada una tiene su test, así que cambiarla es cambiar una línea y un test.

1. **`sigrid_cod` de cada hallazgo.** Es el código de la reclamación de la que
   habla el hallazgo, para que la página la encuentre en `reclamaciones`
   (`lineaDeHallazgo(hallazgo, reclamacionesPorCod)` de F-064): la emparejada
   en `ya_en_sigrid`, `varias_en_sigrid` (la mayor), `codigo_distinto` y
   `anulada_en_sigrid`; el **guardado** en `volcada_no_encontrada`, que no
   tiene otra. En `codigo_distinto` el guardado va en `sigrid_cods`.
2. **`varias_en_sigrid` sustituye a `ya_en_sigrid`** (la tabla de §5.1 las da
   como situaciones distintas, y R41 las trata como alternativas). Con una
   `volcada` con varias, sale `varias_en_sigrid` **y** las comprobaciones de
   R12 contra la de código mayor (la emparejada de R13 bis). `sigrid_cods`, de
   mayor a menor.
3. **R13 con varias**: ninguna de las reclamaciones que llevan la referencia
   de una incidencia se cruza por criterios con ella (no solo la mayor): son
   sus propios partes, y `varias_en_sigrid` ya los enseña.
4. **`ya_en_sigrid` en cualquier estado no `volcada`**, también `descartada` y
   también si la emparejada está en `NPR` (R11 literal).
5. **Referencia**: toda referencia no nula que no da una incidencia de la
   bandeja es `referencia_desconocida` (R6 garantiza que solo llegan las
   `PVI-`). Se aceptan **blancos al final** (`rstrip`), como la intercalación
   de SQL Server, por si `conext.valt` («texto de 80») viene rellenado; el
   UUID, solo en su forma de 36 caracteres (sin llaves ni sin guiones).
6. **Estado desconocido**: cualquiera que no sea uno de los cinco **tal
   cual**, también `None`, `sat` o ` SAT`; se cuentan sobre todas las
   reclamaciones de la obra. Si Sigrid trae los códigos con relleno, el
   recorte es del mapeo del adaptador (A3), no de aquí.
7. **Oficio vacío** (`""`) cuenta como sin oficio; la ubicación vacía o de
   solo blancos no casa (R14).
8. **R18 sin fecha**: detrás de las fechadas (la misma regla que R21).
9. **R21**: tipos en el orden del enumerado (`coincide` …
   `referencia_desconocida`), `incidencia_id` y código **ascendentes** (la
   spec solo dice «descendente» para las reclamaciones). El tope de R18 elige
   por fecha; la lista sale por código.
10. **R36**: `parecido("por la", "por la")` es 100 (claves iguales y no
    vacías, la primera regla de R36), pero **no casa** (R15: sin palabras
    significativas no casa). Con claves distintas y las mismas palabras
    (`Grifos` / `grifo`): 100 de parecido, una sola en común, no casa.

### Desviaciones

- **El test de coste cambió de datos entre T3 y T4** (`96d9f54`). En T3 todas
  las descripciones de una unidad casaban entre sí: 400.000 hallazgos y ≈ 7 s
  de cruce, que miden la construcción de hallazgos y no el índice. Ahora solo
  la primera incidencia de cada unidad casa (con la primera reclamación, por
  los dos criterios); las demás no tienen dos palabras en común: 500.000 pares
  evaluados, 3,1 s el test entero. Sus aserciones cambiaron con los datos
  (`len(coincidencias_total) == 10_000` pasó a comprobar el `coincide` de la
  primera) y el límite bajó de 30 s a 20 s.
- **La mutación no es el comando tal cual**: ver «Mutación (Bloque A2)».

### Fase RED (Bloque A2)

**T3 (`3282d8b`): el módulo no existe.** Comando, desde
`services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f065_dominio.py -q --tb=short
```

Salida real:

```
=================================== ERRORS ====================================
_________________ ERROR collecting tests/test_f065_dominio.py _________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f065_dominio.py:34: in <module>
    from domain.models.sigrid_bandeja import (
E   ModuleNotFoundError: No module named 'domain.models.sigrid_bandeja'
=========================== short test summary info ===========================
ERROR tests/test_f065_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 2.27s
```

**T4 (`96d9f54`): en verde**, el mismo comando: `136 passed in 9.75s`.
Tras `718a633` (un test más, el de inmutabilidad): **137 passed in 4.08 s**.
Ese test caza los cinco `frozen=False`: la segunda pasada de mutación lo
demuestra (mueren todos).

### Tests (Bloque A2)

| Qué | Resultado |
|---|---|
| `pytest tests/test_f065_dominio.py` | **137 passed in 4.08 s** (el de coste, 3,14 s) |
| `pytest tests/test_f065_dominio.py tests/test_f006_arquitectura.py tests/test_f006_repo_sin_identificadores.py` (tras `718a633`) | **202 passed in 44.98 s** |
| Suite entera del servicio api (sobre `96d9f54`, con la máquina cargada) | **2 failed, 9284 passed, 365 skipped in 1533.06 s** (25 min 33 s). Los dos fallos eran míos: `test_f006_r26_…incrusta_un_identificador` (servicio y repositorio), por el GUID literal del test (`{'services/postventa-api/tests/test_f065_dominio.py': 1}`); corregido en `718a633`, verde en la fila de arriba. **No he relanzado la suite entera** tras `718a633` (otros 25 min): solo cambiaron el módulo nuevo, que solo importa su test, y ese test |
| `ruff check` del módulo y del test | **All checks passed!** |
| `bash harness/init.sh` | **No ejecutado** por encargo: lo lanza el líder |

### Mutación (Bloque A2)

`progress/mutacion_F-065_bloqueA2.md`. **No es el comando del encargo tal
cual**, y lo dice la cabecera del informe: la máquina estaba ocupada con las
campañas de mutación de `partes`, `facturas` y `albaranes` (sus procesos
`pytest` estaban vivos), la suite entera tardaba 25 min y, con el timeout de
120 s por mutante, todos habrían salido `timeout`. He usado
`harness.mutacion.main` con el **mismo alcance, los mismos mutantes y el mismo
informe**, pero con un `EjecutorPytest` que lanza solo
`tests/test_f065_dominio.py` (en serie, `--timeout 300`). Es equivalente para
matar o sobrevivir porque ningún otro módulo importa `sigrid_bandeja.py`. El
comando oficial queda en la cabecera del informe para relanzarlo con la
máquina libre.

| Pasada | Generados | Muertos | Supervivientes | Timeouts | Tiempo |
|---|---|---|---|---|---|
| 1.ª (sobre `96d9f54`) | 52 | 47 | **5**: los cinco `@dataclass(frozen=True) → False` | 0 | 255,4 s |
| 2.ª (sobre `718a633`) | **50** | **50** | **0** | 0 | **193,5 s** |

Los cinco de la 1.ª eran un **hueco real** (nada comprobaba la
inmutabilidad), no equivalentes: `test_f065_r19_los_tipos_del_cruce_son_inmutables`
fija los tres públicos, y `_Texto` y `_Candidata` (privados) pasan a
`NamedTuple`, inmutables sin bandera que mutar (por eso la 2.ª genera 50).

### Cobertura (Bloque A2)

`coverage run --branch -m pytest tests/test_f065_dominio.py` y `coverage
report --include=domain/models/sigrid_bandeja.py`: **226 sentencias, 0 sin
cubrir; 66 ramas, 0 parciales: 100 %**. Todo el fichero es nuevo, así que es
la cobertura de las líneas cambiadas. La `PUERTA COBERTURA` de `init.sh` la
dará el líder.

### Pendiente (Bloque A2)

- `bash harness/init.sh` entero (el líder) y la review del Bloque A2.
- Relanzar la mutación con el comando oficial cuando la máquina esté libre,
  si el líder o el reviewer la quieren con la suite entera.
- Las lecturas 1–10 de arriba, para que el reviewer las confirme o las mande
  cambiar.
- En A3, `FichaReclamacion` en el puerto (la anotación ya la espera ahí). En
  A4 bis (T14), `ficha: FichaReclamacion | None` (§15.2) y `Cruce.pares`: aquí
  no se ha adelantado nada de eso.

### Evidencias (Bloque A2)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **137 passed** (dominio de F-065) en 4,08 s; 202 passed con las guardas de F-006; suite entera: 9284 passed, 2 failed (corregidos después), 365 skipped |
| Cobertura de las líneas cambiadas | **100 %** (226/226 sentencias, 66/66 ramas) del módulo nuevo, medida con `coverage`; la puerta de `init.sh`, pendiente del líder |
| Mutantes | **50 generados, 50 muertos, 0 supervivientes, 0 timeouts** (2.ª pasada; la 1.ª, 52/47/5), 1 worker, suite reducida a `test_f065_dominio.py` (ver arriba) |
| Tiempo de la suite | 4,08 s la de F-065; 1.533 s la del servicio entero con la máquina cargada |

## Bloque A2 · T4 bis (2026-10-28)

Encargo del líder: **solo T4 bis** de `tasks.md`, la corrección del dominio
tras la review del Bloque A2 (C-A2-1, C-A2-2) con las decisiones del humano
sobre las lecturas 1–4 y 9 (enmiendas `c961345` y `7269617`: R12, R13, R20,
R21, R41 y `design.md` §10.1). **Sin red, sin base, sin IA, sin Sigrid ni
SharePoint**; nada del Bloque A3 (el recorte de T5 es del adaptador) ni de
A4 bis. `features.json`, `BACKLOG.md` y `current.md` sin tocar. `init.sh` no
ejecutado: lo lanza el líder.

### Commits

| Commit | Qué |
|---|---|
| `a0201d7` | `F-065 T4 bis`: tests RED (`tests/test_f065_dominio.py`) |
| `c99a0d3` | `F-065 T4 bis`: el dominio (`domain/models/sigrid_bandeja.py`) |
| `d3f94c8` | `F-065 T4 bis`: un test más para el mutante a mano M8b (ver «Mutación») |
| (el de este informe) | Este informe, `progress/mutacion_F-065_bloqueA2.md` regenerado y T4 bis `[x]` en `tasks.md` |

### Ficheros tocados

| Fichero | Cambio |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | `Hallazgo.guardado_cod` (con la tabla de §10.1 en la docstring); `volcada_no_encontrada` con `sigrid_cod=None`; `codigo_distinto` con `sigrid_cods=()`, el guardado en `guardado_cod` y callado si el guardado está entre las emparejadas; `_Ordenable` y `_ordenable` (privados) para el orden de R21 |
| `services/postventa-api/tests/test_f065_dominio.py` | 8 tests nuevos, 5 cambiados y 2 cambiados y renombrados (ver «Tests»): 137 → **145** |
| `specs/F-065-revision-sigrid-backend/tasks.md` | T4 bis `[x]` |
| `progress/mutacion_F-065_bloqueA2.md` | Regenerado sobre `d3f94c8` (C-A2-2) |

### Lo que pide T4 bis, punto por punto

1. **`guardado_cod`.** `Hallazgo` gana `guardado_cod: str | None = None`, al
   final (§10.1). `volcada_no_encontrada`: `sigrid_cod=None`, el guardado en
   `guardado_cod`. `codigo_distinto`: la emparejada (la mayor) en
   `sigrid_cod`, el guardado en `guardado_cod`, `sigrid_cods=()`. La
   docstring de `Hallazgo` lleva la tabla. Tests:
   `test_f065_r12_r20_los_codigos_de_cada_hallazgo_segun_la_tabla` (los siete
   tipos con sus tres campos, sobre un juego que da los siete) y
   `test_f065_r12_r20_las_invariantes_de_los_codigos` (sobre el mismo juego:
   `sigrid_cod` no nulo está en `Cruce.reclamaciones`, `sigrid_cods` son de
   Sigrid y solo no vacíos en `varias_en_sigrid`, `guardado_cod` solo en los
   dos tipos).
2. **`codigo_distinto` con varias.** Se da solo si el guardado **no** está
   entre las suyas (`all(r.cod != guardado for r in suyas)`; con una sola
   equivale a lo de antes). El test de T4
   `test_f065_r13_bis_varias_de_una_volcada_y_el_codigo_contra_la_mayor`
   cambia con la decisión y **de nombre**, porque ya no decía lo que fija:
   ahora `test_f065_r12_r13_bis_volcada_con_varias_y_el_guardado_entre_ellas_sin_codigo_distinto`
   (`0081` guardada, `PVI-` en `0081` y `0082` → solo `varias_en_sigrid`).
   Nuevo: `..._y_el_guardado_fuera_da_codigo_distinto` (`0080` guardada →
   `varias_en_sigrid` y `codigo_distinto` con `sigrid_cod` `0082` y
   `guardado_cod` `0080`).
3. **`anulada_en_sigrid` solo contra la mayor (C-A2-1).** El código ya lo
   hacía (T4); faltaba el test. `test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid`
   y el simétrico `..._la_mayor_anulada_da_anulada_en_sigrid`. **Matan M12**:
   traza abajo, en «Mutación».
4. **R13 con varias.** El test de T4 (`r13_bis_varias_emparejadas…`) fijaba
   que ninguna de las suyas coincide con ella, pero **no** que sí lo hacen
   frente a otra. Se completa con
   `test_f065_r13_enmienda_ninguna_de_las_suyas_coincide_con_ella_y_todas_con_las_demas`
   (X `en_duda` con tres `PVI-<X>` y B `nueva` igual: ningún `coincide` de X,
   los tres —también las dos menores— de B; `coincidencias_total` `{B: 3}`).
   Compara los `coincide` como conjunto: el orden lo fija R21, aparte.
5. **El orden de los `coincide`.** Cada `coincide` lleva como desempate su
   puesto en la lista de la incidencia ya ordenada por R18 (`enumerate` sobre
   los 10 del tope); los demás tipos, su `sigrid_cod` (`""` si es `None`, que
   así va delante). `Hallazgo` no gana campo: el puesto vive en un
   `NamedTuple` privado (`_Ordenable`) solo mientras se ordena (§10.1). Tests:
   `test_f065_r21_los_coincide_de_una_incidencia_en_el_orden_de_r18_con_el_tope`
   (12 pares: conflictos y avisos con fechas que **no** siguen el orden de sus
   códigos —el de código menor, el más reciente—, uno sin fecha en cada
   severidad, dos de la misma fecha en cada una; filtrar por incidencia y
   `coincide` da el orden de R18 y los 10 del tope; fuera, los dos avisos sin
   fecha) y `test_f065_r21_los_coincide_por_fecha_y_no_por_codigo` (sustituye
   a `test_f065_r21_dentro_del_tope_el_orden_es_por_codigo`, cuyo nombre
   decía lo contrario de la decisión; además, sus datos daban el mismo orden
   por fecha que por código, así que no distinguían).
   `test_f065_r21_hallazgos_por_severidad_tipo_incidencia_y_codigo` se
   adapta: los dos `coincide` de cada incidencia, de igual fecha, salen por
   código **descendente**, y `volcada_no_encontrada` con `sigrid_cod` `None`.
6. **La enmienda a S-3** (una emparejada en `NPR` da `choca`, R41): **no**
   toca este dominio. Es del veredicto, que nace en T13/T14 (Bloque A4 bis),
   como dice `tasks.md` (T4 bis, punto 6). Aquí nada.
7. **C-A2-2**: abajo, en «Mutación».

### Decisiones de diseño

- **El desempate es `int | str`** en la clave de orden: un entero (el puesto
  de R18) en los `coincide`, el código en los demás. Nunca se comparan entre
  sí porque la clave pone antes el tipo: a igual tipo, los dos son del mismo.
  La alternativa —un campo de fecha o de puesto en `Hallazgo`— cambiaba el
  tipo público, que §10.1 descarta («sin campo público nuevo»).
- **Sin literales nuevos** que la herramienta de mutación pueda cambiar por un
  equivalente: el puesto sale de `enumerate` (no de un `0` fijo para los
  demás tipos), para que la campaña no dé un superviviente equivalente.
- `codigo_distinto` con `all(...)` en vez de `guardado not in {...}`: el mismo
  resultado, sin construir un conjunto por incidencia.

### Desviaciones

- **Dos tests de T4 cambian de nombre** (puntos 2 y 5): sus nombres afirmaban
  el comportamiento que la decisión del humano cambia. T4 bis pedía
  «cambia» / «se adapta»; el nombre nuevo cita la enmienda en su docstring.
- **Un test fuera de los puntos de T4 bis**,
  `test_f065_r14_los_dos_con_oficio_vacio_no_casan` (`d3f94c8`): el mutante a
  mano M8b (la bandeja con oficio `""` casa con una reclamación con oficio
  `""`) **sobrevivía**, porque ningún test de T4 ponía `""` en los dos lados.
  Es la lectura 7 de T4, ya implementada (`if oficio and …`); el test solo la
  fija. En `critico` no podía quedar vivo. No cambia código.

### Fase RED (T4 bis)

Desde `services/postventa-api`, sobre `a0201d7` (los tests nuevos contra el
dominio de T4):

```
.venv/Scripts/python.exe -m pytest tests/test_f065_dominio.py -q --tb=line -p no:cacheprovider
```

Salida real:

```
..............................................FF.F....FF...FF........... [ 50%]
.................................................FFF................F... [100%]
================================== FAILURES ===================================
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:538: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:550: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:576: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
E   AssertionError: assert (Hallazgo(tip...arecido=None)) == (Hallazgo(tip...recido=None),)
      
      Left contains one more item: Hallazgo(tipo=<TipoHallazgo.CODIGO_DISTINTO: 'codigo_distinto'>, severidad=<Severidad.AVISO: 'aviso'>, incidencia_id=U...0-0000-0000-0000-000000000001'), sigrid_cod='RS26.10/0082', sigrid_cods=('RS26.10/0081',), criterios=(), parecido=None)
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:664: AssertionError: assert (Hallazgo(tip...arecido=None)) == (Hallazgo(tip...recido=None),)
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:679: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:778: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
E   AttributeError: 'Hallazgo' object has no attribute 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:801: AttributeError: 'Hallazgo' object has no attribute 'guardado_cod'
E   AssertionError: assert [(<Severidad....9/0200'), ...] == [(<Severidad....9/0100'), ...]
      
      At index 0 diff: (<Severidad.CONFLICTO: 'conflicto'>, <TipoHallazgo.COINCIDE: 'coincide'>, UUID(int=1), 'RS26.09/0100') != (<Severidad.CONFLICTO: 'conflicto'>, <TipoHallazgo.COINCIDE: 'coincide'>, UUID(int=1), 'RS26.09/0200')
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:1254: AssertionError: assert [(<Severidad....9/0200'), ...] == [(<Severidad....9/0100'), ...]
E   AssertionError: assert ['RS26.09/000...RS26.09/0003'] == ['RS26.09/000...RS26.09/0001']
      
      At index 0 diff: 'RS26.09/0001' != 'RS26.09/0003'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:1280: AssertionError: assert ['RS26.09/000...RS26.09/0003'] == ['RS26.09/000...RS26.09/0001']
E   AssertionError: assert [(<Severidad....8/0001'), ...] == [(<Severidad....8/0001'), ...]
      
      At index 1 diff: (<Severidad.CONFLICTO: 'conflicto'>, 'RS26.09/0002') != (<Severidad.CONFLICTO: 'conflicto'>, 'RS26.09/0004')
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:1316: AssertionError: assert [(<Severidad....8/0001'), ...] == [(<Severidad....8/0001'), ...]
E   TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_dominio.py:1449: TypeError: Hallazgo.__init__() got an unexpected keyword argument 'guardado_cod'
=========================== short test summary info ===========================
FAILED tests/test_f065_dominio.py::test_f065_r12_volcada_no_encontrada - Type...
FAILED tests/test_f065_dominio.py::test_f065_r12_codigo_distinto - TypeError:...
FAILED tests/test_f065_dominio.py::test_f065_r12_anulada_y_con_otro_codigo_da_los_dos_avisos
FAILED tests/test_f065_dominio.py::test_f065_r12_r13_bis_volcada_con_varias_y_el_guardado_entre_ellas_sin_codigo_distinto
FAILED tests/test_f065_dominio.py::test_f065_r12_r13_bis_volcada_con_varias_y_el_guardado_fuera_da_codigo_distinto
FAILED tests/test_f065_dominio.py::test_f065_r12_r20_los_codigos_de_cada_hallazgo_segun_la_tabla
FAILED tests/test_f065_dominio.py::test_f065_r12_r20_las_invariantes_de_los_codigos
FAILED tests/test_f065_dominio.py::test_f065_r21_hallazgos_por_severidad_tipo_incidencia_y_codigo
FAILED tests/test_f065_dominio.py::test_f065_r21_los_coincide_por_fecha_y_no_por_codigo
FAILED tests/test_f065_dominio.py::test_f065_r21_los_coincide_de_una_incidencia_en_el_orden_de_r18_con_el_tope
FAILED tests/test_f065_dominio.py::test_f065_e13_volcada_no_encontrada - Type...
11 failed, 133 passed in 4.59s
```

(En la traza, el identificador de la incidencia se ha escrito `UUID(int=1)`: el
literal de 36 caracteres lo rechaza la guarda de F-006, R26.)

Lo que falla y por qué: `guardado_cod` no existe (puntos 1 y 2), el
`codigo_distinto` con el guardado entre las suyas (2) y el orden por código
(5). **En verde ya en la RED, y es lo esperado**: los dos tests de la
anulación (3: T4 ya miraba solo la mayor; su prueba es que matan M12, abajo)
y el de R13 (4: T4 ya lo hacía así; completa lo que faltaba por fijar).

**En verde** (sobre `d3f94c8`), el mismo comando: **145 passed in 4.53 s**.

### Tests (T4 bis)

| Qué | Resultado |
|---|---|
| `pytest tests/test_f065_dominio.py` | **145 passed in 4.53 s** (el de coste, 3,50 s) |
| `pytest tests/test_f065_dominio.py tests/test_f006_arquitectura.py tests/test_f006_repo_sin_identificadores.py` | **210 passed in 33.58 s** |
| `ruff check` del módulo y del test (desde la raíz del worktree) | **All checks passed!** |
| Importadores de `sigrid_bandeja` (`grep -rln` en `services/`, `harness/`, `tests/`) | solo el módulo y su test |
| `bash harness/init.sh` | **No ejecutado** por encargo: lo lanza el líder |

- **Nuevos (8):** `r12_r13_bis_volcada_con_varias_y_el_guardado_fuera_da_codigo_distinto`,
  `r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid`,
  `r12_r13_bis_la_mayor_anulada_da_anulada_en_sigrid`,
  `r13_enmienda_ninguna_de_las_suyas_coincide_con_ella_y_todas_con_las_demas`,
  `r12_r20_los_codigos_de_cada_hallazgo_segun_la_tabla`,
  `r12_r20_las_invariantes_de_los_codigos`,
  `r21_los_coincide_de_una_incidencia_en_el_orden_de_r18_con_el_tope` y
  `r14_los_dos_con_oficio_vacio_no_casan` (`d3f94c8`).
- **Cambiados y renombrados (2):** `r13_bis_varias_de_una_volcada_y_el_codigo_contra_la_mayor`
  → `r12_r13_bis_volcada_con_varias_y_el_guardado_entre_ellas_sin_codigo_distinto`;
  `r21_dentro_del_tope_el_orden_es_por_codigo` → `r21_los_coincide_por_fecha_y_no_por_codigo`.
- **Cambiados (5):** `r12_volcada_no_encontrada`, `e13_volcada_no_encontrada`,
  `r12_codigo_distinto`, `r12_anulada_y_con_otro_codigo_da_los_dos_avisos`,
  `r21_hallazgos_por_severidad_tipo_incidencia_y_codigo`.

### Mutación (T4 bis)

**Herramienta (C-A2-2).** `progress/mutacion_F-065_bloqueA2.md`, regenerado
**sobre `d3f94c8`** con `git status --porcelain` vacío antes de empezar
(23:11:37) y la rama sin moverse durante la campaña. Misma suite reducida que
en T4, con su nota en la cabecera (la review la acepta):
`harness.mutacion.main` con un `EjecutorPytest` que lanza solo
`tests/test_f065_dominio.py`, `--base 16453b5 --workers 1 --timeout 300`. El
alcance ahora cuadra con lo medido: **570 líneas** = `wc -l` del módulo en
`d3f94c8` (el fichero entero, nuevo desde `16453b5`).

| Generados | Muertos | Supervivientes | Timeouts | Tiempo | Workers |
|---|---|---|---|---|---|
| **50** | **50** | **0** | 0 | **178,7 s** | 1 |

Un primer intento a las 23:11 falló **antes de mutar nada**: el envoltorio
pasaba la ruta del intérprete relativa y `subprocess` no la encontraba desde
`services/postventa-api` (`FileNotFoundError` en la ejecución de referencia).
`git status` siguió limpio y se relanzó con la ruta absoluta.

**A mano** (lo que la herramienta no muta): M1–M18 de la review, reescritos
sobre el código de T4 bis (M8 en dos variantes), y M19–M26 por los cambios 1,
2 y 5. Cada uno contra `tests/test_f065_dominio.py` entero, sin `-x`, en un
`git worktree` desechable del scratchpad sobre `d3f94c8` (ya borrado), con
`PYTHONDONTWRITEBYTECODE=1`:

| Id | Mutación | Resultado | Lo caza |
|---|---|---|---|
| M1 | R13: sin `if r.cod in propias: continue` | muerto (4) | `r13_la_emparejada_no_coincide…`, `r13_bis_varias_emparejadas…`, `r13_enmienda_…`, `e7` |
| M2 | R10: la referencia sin `rstrip()` | muerto (1) | `r10_referencia_con_blancos_al_final` |
| M3 | lectura 3: `propias` solo con la mayor | muerto (2) | `r13_bis_varias_emparejadas…`, `r13_enmienda_…` |
| M4 | R15: sin el atajo de la clave igual | muerto (1) | `r15_la_misma_clave_con_una_sola_palabra_casa` |
| M5 | `_texto` con `plegar` | muerto (1) | `r15_la_misma_clave_con_una_sola_palabra_casa` |
| M6 | `None` no cuenta como desconocido | muerto (2) | `r17_estado_desconocido…[None]`, `r17_los_desconocidos…` |
| M7 | sin la guarda «la bandeja sin palabras» | muerto (2) | `r15_descripcion_vacia_o_sin_palabras…` (2) |
| M8 | `if oficio == r.oficio_codigo` (sin oficio casa con sin oficio; la de la review) | muerto (2) | `r14_los_dos_sin_oficio_no_casan`, `r14_los_dos_con_oficio_vacio_no_casan` |
| M8b | `if oficio is not None and …` (el `""` de la bandeja cuenta) | muerto (1) | `r14_los_dos_con_oficio_vacio_no_casan` (**sobrevivía** antes de `d3f94c8`) |
| M9 | la ubicación vacía casa | muerto (3) | `r14_ubicacion_vacia_o_ausente…` (3) |
| M10 | `varias` además da `ya_en_sigrid` | muerto (4) | `r13_bis_varias…`, `r13_bis_dos_bastan…`, `r13_enmienda_…`, `r12_r20_…segun_la_tabla` |
| M11 | los demás tipos por código descendente | muerto (1) | `r21_hallazgos_por_severidad…` |
| **M12** | **`if any(r.estado == EstadoSigrid.NPR for r in suyas):`** | **muerto (1)** | **`r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid`** |
| M13 | `referencia_desconocida` solo si hay UUID | muerto (5) | `r10_pvi_sin_uuid…`, los 2 `r12_r20_…`, `r21_hallazgos…`, `e8` |
| M14 | `codigo_distinto` contra la menor | muerto (1) | `r12_r13_bis_…_guardado_fuera_da_codigo_distinto` |
| M15 | `ya_en_sigrid` solo para las evaluables | muerto (1) | `r11_emparejada_y_no_volcada…[descartada]` |
| M16 | se empareja con la menor | muerto (7) | los 4 `r12_r13_bis_…`, `r13_bis_varias…`, `r13_enmienda_…`, `r12_r20_…segun_la_tabla` |
| M17 | R18 sin «conflicto primero» | muerto (1) | `r18_primero_los_conflictos` |
| M18 | el tope sobre la lista sin ordenar | muerto (7) | 4 de R18 y los 3 de R21 con `coincide` |
| M19 | 1: `volcada_no_encontrada` sin `guardado_cod` | muerto (4) | `r12_volcada_no_encontrada`, `e13`, los 2 `r12_r20_…` |
| M20 | 1: `codigo_distinto` sin `guardado_cod` | muerto (5) | `r12_codigo_distinto`, `r12_anulada_y_con_otro…`, `…_guardado_fuera…`, los 2 `r12_r20_…` |
| M21 | 1: `volcada_no_encontrada` con el guardado en `sigrid_cod` (como T4) | muerto (5) | `r12_volcada_no_encontrada`, `e13`, los 2 `r12_r20_…`, `r21_hallazgos…` |
| M22 | 1: `codigo_distinto` con el guardado también en `sigrid_cods` (como T4) | muerto (5) | los mismos que M20 |
| M23 | 2: `codigo_distinto` con el guardado entre las suyas (`mayor.cod != guardado`, como T4) | muerto (1) | `r12_r13_bis_…_guardado_entre_ellas_sin_codigo_distinto` |
| M24 | 2: `all` → `any` | muerto (3) | `…_guardado_entre_ellas…` y los 2 de la anulación |
| M25 | 5: los `coincide` otra vez por código (como T4) | muerto (3) | los 3 de R21 con `coincide` |
| M26 | 5: los `coincide` en el orden inverso de R18 (`-puesto`) | muerto (3) | los 3 de R21 con `coincide` |

**27 a mano, 27 muertos, 0 supervivientes.** En la primera pasada (sobre
`c99a0d3`) M8b sobrevivía —su test entró en `d3f94c8`— y M17 daba un error de
sintaxis (`(*x)` sin coma), no un mutante válido: corregido a `(*x,)`. La
tabla es la segunda pasada, sobre `d3f94c8`. Todos los cazan tests **de la
propia feature** (nadie más importa el módulo).

**La traza de M12 muerto** (C-A2-1), en la copia desechable sobre `d3f94c8`,
con `sigrid_bandeja.py` l. 451 cambiada a
`if any(r.estado == EstadoSigrid.NPR for r in suyas):`, desde
`services/postventa-api`:

```
$ python -m pytest tests/test_f065_dominio.py -q --tb=short -p no:cacheprovider
........................................................F............... [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
================================== FAILURES ===================================
_______ test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid ________
tests\test_f065_dominio.py:699: in test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid
    assert cruce.hallazgos == (_varias(1, "RS26.10/0081", "RS26.10/0082"),)
E   AssertionError: assert (Hallazgo(tip...ado_cod=None)) == (Hallazgo(tip...do_cod=None),)
E     
E     Left contains one more item: Hallazgo(tipo=<TipoHallazgo.ANULADA_EN_SIGRID: 'anulada_en_sigrid'>, severidad=<Severidad.AVISO: 'aviso'>, incidencia_...00-0000-0000-000000000001'), sigrid_cod='RS26.10/0082', sigrid_cods=(), criterios=(), parecido=None, guardado_cod=None)
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_f065_dominio.py::test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid
1 failed, 144 passed in 5.78s
```

(Sobre el árbol de la review, `44c3163`, el mismo mutante daba `137 passed`.)

### Cobertura (T4 bis)

`coverage run --branch -m pytest tests/test_f065_dominio.py` y
`coverage report --include=domain/models/sigrid_bandeja.py` (sobre `c99a0d3`;
`d3f94c8` solo añade un test): **234 sentencias, 0 sin cubrir; 66 ramas, 0
parciales: 100 %**. Todo el fichero es nuevo desde la base del tramo, así que
es la cobertura de lo cambiado. La `PUERTA COBERTURA` de `init.sh`, del líder.

### Pendiente (T4 bis)

- `bash harness/init.sh` entero (el líder) y la **review del Bloque A2**
  otra vez, sobre T4 bis (`tasks.md`: «Parar»).
- La mutación con el comando oficial (suite entera), si la quieren con la
  máquina libre.
- Lo que T4 bis deja en cascada, de otros bloques y sin tocar aquí: T7
  serializa `guardado_cod` (R20, `null` donde no toca); T13/T14, la `choca`
  por `NPR` (enmienda a S-3); F-064 (otro worktree) recoge `guardado_cod`, el
  `sigrid_cod` `null` en `volcada_no_encontrada` y los `coincide` ya en el
  orden de R18.
- Sin verificaciones MANUAL en este bloque.

### Evidencias (T4 bis)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **145 passed** (dominio de F-065) en 4,53 s; **210 passed** con las guardas de F-006 en 33,58 s. Suite entera del servicio: no ejecutada (la lanza el líder con `init.sh`) |
| Cobertura de las líneas cambiadas | **100 %** (234/234 sentencias, 66/66 ramas) del módulo, medida con `coverage`; la puerta de `init.sh`, pendiente del líder |
| Mutantes | Herramienta: **50 generados, 50 muertos, 0 supervivientes, 0 timeouts**, 1 worker, 178,7 s, sobre `d3f94c8` con el árbol limpio (suite reducida). A mano: **27, 27 muertos, 0 supervivientes** (M12, muerto) |
| Tiempo de la suite | 4,53 s la de F-065 (el test de coste, 3,50 s) |
