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
