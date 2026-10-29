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

## Bloque A3 · T5 y T6 (2026-10-29)

Encargo del líder: solo T5 y T6 (la consulta, el puerto, el adaptador de
lectura y la fábrica), sobre la base aprobada del Bloque A2 (`4246645`). Sin
conectar a Sigrid, a la base ni a SharePoint; sin tocar `features.json`,
`BACKLOG.md` ni `current.md`; sin empezar el Bloque A4. `init.sh` entero lo
ejecuta el líder.

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `f82abfb` | T5 | Los tests en RED: `tests/test_f065_consulta.py` y `tests/test_f065_adaptador.py`; T5 `[x]` |
| `883d7be` | T6 | El puerto, la consulta, el adaptador y `construir_reclamaciones_obra`; T6 `[x]` |
| (el siguiente) | — | Este informe y `progress/mutacion_F-065_bloqueA3.md` |

### Ficheros tocados

- **Nuevos**: `services/postventa-api/domain/ports/reclamaciones_obra.py`
  (`FichaReclamacion`, `FilaReclamacionObra`, `ReclamacionesObraPort`);
  `services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py`
  (`SQL_RECLAMACIONES_DE_LA_OBRA`, `CAMPO_REFERENCIA`, `PATRON_REFERENCIA`,
  `COLUMNAS_RECLAMACION`, `select_reclamaciones_de_la_obra`,
  `fila_a_reclamacion_obra`);
  `services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py`
  (`AdaptadorReclamacionesObraSigridApi`); y los dos ficheros de tests.
- **Modificado**: `services/postventa-api/infrastructure/sigrid/fabrica.py`:
  solo se **añade** `construir_reclamaciones_obra`, su entrada en `__all__`,
  dos importaciones y un párrafo de enmienda en la cabecera (46 líneas, todas
  nuevas; ninguna fábrica existente cambia).
- `specs/F-065-revision-sigrid-backend/tasks.md`: T5 y T6 `[x]`.
- **Sin tocar** (comprobado con `git diff 4246645`): `catalogo_obra.py`,
  `ubicaciones_validas.py`, `consultas_catalogo.py`, todo `domain/models/`
  (también `sigrid_bandeja.py`), `tests/test_f036_adaptador_catalogo.py` y
  `tests/test_f056_ubicaciones.py`.

### Decisiones de diseño

- **La consulta** es la de `design.md` §3 carácter a carácter, con saltos LF.
  Tres tests la fijan: contra un literal en el test, contra el bloque `sql` de
  §3 leído de `design.md`, y contra el here-string
  `$SQL_RECLAMACIONES_DE_LA_OBRA` del script 29 (CRLF pasado a LF, que es lo
  que el script manda por `ConvertTo-SqlConLf`). El test del script ya la
  comparaba con §3
  (`test_f065_r29_la_consulta_de_la_obra_es_la_de_design_caracter_a_caracter`);
  con el nuevo, código = spec = script. `test_f065_scripts_infra.py` no se toca.
- **Los parámetros**: `RCPCLI` (`CAMPO_REFERENCIA`), `PVI-%` (compuesto con
  `PREFIJO_REFERENCIA` del dominio de F-059, para que el prefijo tenga un solo
  dueño), el `tip` que pasa quien lee y la obra. El adaptador **no** lleva el
  tipo en el constructor: lo pide `leer(..., tip=)`, como dice el puerto de
  §10.2.
- **El adaptador hereda** `AdaptadorCatalogoSigridApi` sin tocarlo y usa sus
  `_un_intento`, `_mapear`, `_cabeceras` y `_cliente_http`. Su lectura propia
  se llama **`_leer_todas`** y no `_leer`: así no sobrescribe el `_leer` del
  catálogo, y los métodos heredados (`leer_unidades`, `leer_oficios`) siguen
  siendo exactamente lo que eran. `design.md` §2 dice «compone su propio
  `_leer`»: es el mismo diseño con otro nombre, por eso. La política de
  `tenacity` se compone igual que en el catálogo (`es_transitorio`,
  `wait_exponential`, `stop_after_attempt(self._reintentos)`), y `_fallo` es
  propio del módulo y da el mismo `CatalogoNoDisponible` con la misma forma
  (§2, conciliado).
- **El techo**: `max_rows` = `TOPE_RECLAMACIONES_OBRA` (500.000, importado del
  dominio). `llego_al_techo` = filas ≥ tope **o** `truncated`: un `truncated`
  por debajo del tope **no** es el 503 de F-036, es «al techo» y la aplicación
  dará 409 (A4).
- **`truncated` que no es booleano** (ausente, `null`, `"false"`, `0`) es
  **503** «la respuesta no dice si viene cortada». Lectura mía de R8
  («respuesta mal formada → 503»): `truncated` es la única señal de que la
  lista está entera, y darla por buena sin ella podría cruzar conflictos a
  medias. El catálogo trata la ausencia como `False`; aquí no. La pasarela
  siempre lo manda (`sigrid_api.md` §6.1). Si el reviewer prefiere la
  tolerancia del catálogo, es una línea y un caso del test.
- **El log** (R25, R38): una línea `F-065 reclamaciones de la obra leídas en
  Sigrid: obra=… filas=… al_techo=… truncated=… segundos=…`. `al_techo` es
  «filas ≥ tope» y `truncated` lo que dijo la pasarela, por separado (R25:
  «si llegó al techo o vino `truncated`»); la lectura devuelve la `o` de los
  dos. Con error no se registra nada (como F-036 y F-056).
- **El mapeo** (§10.2): `obra_ref` tal cual y obligatoria (no vacía tras
  recortar, como `FilaUnidadCatalogo`); `cod` recortado y obligatorio
  («una reclamación sin código»); `estado_codigo`, `tipo_codigo` y
  `clase_codigo` recortados, `None` si quedan vacíos; `unidad_codigo` y
  `oficio_codigo` **tal cual** (también un código de solo blancos se queda
  como llega), con su test; nombres y textos tal cual. Lo que no es `None` se
  pasa a `str`, como el catálogo.
- **Las fechas** (`con.fec`, `rcp.fecpre`): solo un `int` que no sea `bool`;
  `0` y `NULL` son `None`; una fecha imposible, un texto, un `float` o un
  `bool` son `ValueError` con un mensaje fijo, **sin el valor y sin causa**
  (`from None`, para que la traza tampoco lleve el error de `date`).
- **`forma_comunicacion`** (`rcp.rcptip`, «Entero» en `sigrid_tablas.md`): un
  entero tal cual, **también el `0`**. El «`0` a nulo» de T5 lo leo de las
  fechas (va junto a «`YYYYMMDD` a fecha»); `rcptip` es un código, y su `0`
  puede ser una opción. Lo que no es entero es `ValueError` sin el valor.
- **El `repr`** (R40): **todos** los campos de `FilaReclamacionObra` y de
  `FichaReclamacion` con `repr=False`, también `cod` (un código `RS` no va a
  ningún log, T-A15) y `obra_ref`. El `repr` es `FilaReclamacionObra()`.
- **La fábrica**: entorno → configuración, como
  `construir_ubicaciones_validas`; sin ninguna ventana; log `F-065 lector de
  las reclamaciones de la obra en Sigrid construido en el entorno …`.

### Desviaciones

Ninguna respecto a la spec. Las dos lecturas que he tenido que concretar
(`truncated` no booleano → 503, y `rcptip` `0` tal cual) y el nombre
`_leer_todas` están arriba, justificadas, para la review.

### Fase RED (Bloque A3)

Los tests de T5 escritos antes que el código (`f82abfb`), desde
`services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_consulta.py tests/test_f065_adaptador.py -q --tb=short -p no:cacheprovider
=================================== ERRORS ====================================
________________ ERROR collecting tests/test_f065_consulta.py _________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_consulta.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f065_consulta.py:32: in <module>
    from domain.ports.reclamaciones_obra import FichaReclamacion, FilaReclamacionObra
E   ModuleNotFoundError: No module named 'domain.ports.reclamaciones_obra'
________________ ERROR collecting tests/test_f065_adaptador.py ________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_adaptador.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f065_adaptador.py:45: in <module>
    from domain.ports.reclamaciones_obra import ReclamacionesObraPort
E   ModuleNotFoundError: No module named 'domain.ports.reclamaciones_obra'
=========================== short test summary info ===========================
ERROR tests/test_f065_consulta.py
ERROR tests/test_f065_adaptador.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 2.19s
```

Como el RED de módulos nuevos es una importación que falla, el de **los
requisitos centrales** se demuestra también con el código ya escrito,
quitándolo: en una copia desechable sobre `883d7be`, con el estado **sin
recortar** y la unidad **recortada** a la vez (`_codigo(estado)` →
`_texto(estado)`, `_texto(unidad)` → `_codigo(unidad)`):

```
$ python -m pytest tests/test_f065_consulta.py -q --tb=line -p no:cacheprovider -k "estado_se_recorta or unidad_y_el_oficio"
E   AssertionError: assert None == ''
     +  where None = FilaReclamacionObra().unidad_codigo
...\tests\test_f065_consulta.py:506: AssertionError: assert None == ''
=========================== short test summary info ===========================
FAILED tests/test_f065_consulta.py::test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo[relleno]
FAILED tests/test_f065_consulta.py::test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo[blanco-delante]
FAILED tests/test_f065_consulta.py::test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo[los-dos-lados]
FAILED tests/test_f065_consulta.py::test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo[solo-blancos]
FAILED tests/test_f065_consulta.py::test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo[vacio]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[relleno]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[blanco-delante]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[oficio-relleno]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[oficio-blanco-delante]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[solo-blancos]
FAILED tests/test_f065_consulta.py::test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036[vacio]
11 failed, 2 passed, 97 deselected in 2.44s
```

(Las dos que pasan son los casos limpio y nulo del estado, que no dependen
del recorte.) Los demás requisitos centrales, con los mutantes a mano de
abajo: `truncated` como en F-036 (MA8), `max_rows` del catálogo (MA9), el
`_leer` heredado (MA11), las puertas de la fábrica (MA19–MA21).

Verde tras T6:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_consulta.py tests/test_f065_adaptador.py -q -p no:cacheprovider
183 passed in 2.29s
```

### Tests (Bloque A3)

| Suite | Resultado |
|---|---|
| `tests/test_f065_consulta.py` + `tests/test_f065_adaptador.py` (T5/T6) | **183 passed** en 2,29 s |
| T6: `tests/test_f036_adaptador_catalogo.py` y `tests/test_f056_ubicaciones.py`, sin cambios | en verde (dentro de las dos de abajo) |
| F-065 (los cuatro ficheros) + F-036/F-056 de T6 + las guardas de F-006 (`tests/test_f006_*.py`) | **791 passed** en 54,97 s |
| Lo anterior más todas las guardas de arquitectura, fábricas, alcance cerrado (F-031…F-060) y logs/repo sin datos personales | **1359 passed, 234 skipped** en 245,38 s |

`ruff check` (0.16.3) de los seis ficheros: solo `I001` (orden de
importaciones), el mismo que ya dan con esta configuración `fabrica.py`,
`ubicaciones_validas.py`, `test_f056_ubicaciones.py` y `test_f065_dominio.py`
(el estilo del repositorio: `domain`/`infrastructure` y `tests` en bloques
aparte). Ningún otro aviso.

### Mutación (Bloque A3)

**Herramienta**: `progress/mutacion_F-065_bloqueA3.md`, con `--base 4246645`,
sobre `883d7be` con el árbol limpio, suite reducida a los dos ficheros de T5
(la nota de su cabecera dice quién importa lo mutado y por qué vale).
Alcance: 516 líneas (los tres módulos nuevos enteros y las 46 nuevas de
`fabrica.py`).

| Generados | Muertos | Supervivientes | Timeouts | Tiempo | Workers |
|---|---|---|---|---|---|
| **58** | **58** | **0** | 0 | **326,6 s** | 1 |

**A mano** (lo que la herramienta no muta), cada uno contra los dos ficheros
de T5 enteros, sin `-x`, en un `git worktree` desechable del scratchpad sobre
`883d7be` (ya borrado), con `PYTHONDONTWRITEBYTECODE=1`:

| Id | Mutación | Resultado | Lo caza |
|---|---|---|---|
| MA1 | el estado sin recortar | muerto (5) | `r17_el_estado_se_recorta_y_el_vacio_es_nulo` |
| MA2 | el `cod` sin recortar | muerto (3) | `r12_el_codigo_se_recorta` |
| MA3 | el tipo sin recortar | muerto (4) | `r6_el_tipo_y_la_clase_se_recortan…` |
| MA4 | la clase sin recortar | muerto (4) | `r6_el_tipo_y_la_clase_se_recortan…` |
| MA5 | la unidad recortada | muerto (6) | `r14_la_unidad_y_el_oficio_van_tal_cual…` |
| MA6 | el oficio recortado | muerto (6) | `r14_la_unidad_y_el_oficio_van_tal_cual…` |
| MA7 | un código vacío se queda `""` y no `None` | muerto (7) | `r17_…`, `r6_el_codigo_es_obligatorio…`, `r6_el_tipo_y_la_clase…`, `r8_r40_…mal_formada…` |
| MA8 | `truncated` no cuenta como techo (como F-036) | muerto (3) | `r8_truncated_por_debajo_del_techo_es_al_techo_y_no_503` |
| MA9 | `max_rows` 1.000 | muerto (5) | `r8_leer_es_un_post…`, `r8_con_el_techo_o_mas…` |
| MA10 | sin `truncated` se da por entera | muerto (4) | `r8_r40_…mal_formada…` (los cuatro de `truncated`) |
| MA11 | el `_leer` heredado (1.000 filas, 503 por debajo) | muerto (14) | `r8_leer_es_un_post…`, `r8_con_el_techo…`, `r25_el_log_distingue…`, `r8_r40_…` |
| MA12 | la fecha `0` no es nula | muerto (1) | `r6_r33_las_fechas_yyyymmdd_y_el_cero_es_nulo` |
| MA13 | la fecha imposible con la causa de `date` | muerto (16) | `r40_una_fecha_imposible_es_error_sin_la_fila` |
| MA14 | un `bool` vale como entero | muerto (3) | `r40_una_fecha_imposible…`, `r40_una_forma_de_comunicacion…` |
| MA15 | la fecha imposible con el valor en el mensaje | muerto (16) | `r40_una_fecha_imposible…` |
| MA16 | `cod` en el `repr` | muerto (2) | `r40_la_fila_y_la_ficha_no_imprimen…`, `r40_la_lectura_no_imprime…` |
| MA17 | `propietario` en el `repr` | muerto (1) | `r40_la_fila_y_la_ficha_no_imprimen…` |
| MA18 | el log con la unidad de la primera fila | muerto (5) | los tres de R25/R38 |
| MA19 | la fábrica sin la puerta del entorno | muerto (5) | `r2_la_fabrica_se_niega…`, `r2_la_fabrica_fuera_de_entorno…` |
| MA20 | la fábrica con las puertas al revés | muerto (3) | `r2_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion` |
| MA21 | la fábrica mira `CIERRE_HABILITADO` | muerto (4) | `r2_la_fabrica_no_mira_ninguna_ventana…` y dos más |
| MA22 | el tipo y la obra intercambiados | muerto (5) | `r5_los_parametros_en_el_orden…`, `r5_el_tipo_viaja…`, `r8_leer_es_un_post…` |
| MA23 | `obra_ref` recortada | muerto (1) | `r9_obra_ref_va_tal_cual` |

**23 a mano, 23 muertos, 0 supervivientes.**

### Cobertura (Bloque A3)

`coverage run --branch -m pytest tests/test_f065_consulta.py tests/test_f065_adaptador.py`:
`domain/ports/reclamaciones_obra.py` 45/45; `consultas_reclamaciones_obra.py`
49/49 sentencias y 14/14 ramas; `reclamaciones_obra.py` 42/42 y 4/4; en
`fabrica.py`, las líneas sin cubrir son todas de las **otras** fábricas
(163–171, 203–210, 233–240, 264–271, 294–301, 351–356, 368–379, 386,
408–411); `construir_reclamaciones_obra` (311–342), entera. **Cobertura de lo
cambiado: 100 %.** La `PUERTA COBERTURA` de `init.sh`, del líder.

### Pendiente (Bloque A3)

- `bash harness/init.sh` entero (el líder) y la **review del Bloque A3**
  (`tasks.md`: «Parar»).
- La mutación con el comando oficial (suite entera), si la quieren con la
  máquina libre.
- Para el Bloque A4, sin tocar aquí: `mirar_sigrid` pasa de
  `FilaReclamacionObra` a `ReclamacionSigrid` (`estado_codigo` → `estado`) y
  cuenta las obras por `obra_ref`; `llego_al_techo` → 409
  `ReclamacionesSinVerificar`; el borde construye con
  `construir_reclamaciones_obra` antes que la base (R2) y pasa
  `ajustes.sigrid_tip_reclamacion` como `tip`.
- Sin verificaciones MANUAL en este bloque.

### Evidencias (Bloque A3)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **183 passed** (T5/T6) en 2,29 s; **791 passed** con el resto de F-065, F-036/F-056 de T6 y las guardas de F-006 en 54,97 s; **1359 passed, 234 skipped** con todas las guardas de arquitectura, fábricas y alcance en 245,38 s. Suite entera: la lanza el líder con `init.sh` |
| Cobertura de las líneas cambiadas | **100 %** (136/136 sentencias y 18/18 ramas de los tres módulos nuevos; `construir_reclamaciones_obra` entera), medida con `coverage`; la puerta de `init.sh`, pendiente del líder |
| Mutantes | Herramienta: **58 generados, 58 muertos, 0 supervivientes, 0 timeouts**, 1 worker, 326,6 s, sobre `883d7be` con el árbol limpio (suite reducida). A mano: **23, 23 muertos, 0 supervivientes** |
| Tiempo de la suite | 2,29 s la de T5/T6 |

## Bloque A4 · T7, T8 y T9 (2026-10-29)

Encargo del líder: solo T7, T8 y T9 (la aplicación, el borde HTTP, la ruta y
la guarda de alcance), sobre el Bloque A3 aprobado (`509ef57`). Con las dos
observaciones de la review del A3: **O-A3-2** (el 503 de «la respuesta no dice
si viene cortada» no puede acabar en 409 en el borde: fijado con un test HTTP)
y **O-A3-1** (`fabrica.py` no se ha tocado en este bloque, así que sus
importaciones siguen como estaban). Sin conectar a Sigrid, a la base ni a
SharePoint; sin tocar `features.json`, `BACKLOG.md` ni `current.md`; sin
empezar el Bloque A4 bis (veredicto, guarda del ensayo, NPR → `choca`).
`init.sh` entero lo ejecuta el líder.

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `d26060d` | T7 | Los tests en RED: `test_f065_aplicacion.py`, `test_f065_http.py`, `test_f065_datos_personales.py`; T7 `[x]` |
| `71ded50` | T8 | La aplicación, el borde, la ruta, `ReclamacionesSinVerificar`, la cuenta de rutas de F-010; T8 `[x]` |
| `d338de7` | T9 | La guarda de alcance `test_f065_alcance_cerrado.py`; T9 `[x]` |
| `fb0ad71` | T8 | Tres tests que matan los tres supervivientes de la 1.ª pasada de la herramienta |
| `ca66e3f` | T8 | Dos tests que matan los dos supervivientes reales de los mutantes a mano (MA16, MA23) |
| (el siguiente) | — | Este informe y `progress/mutacion_F-065_bloqueA4.md` |

### Ficheros tocados

- **Nuevos de producción**:
  - `services/postventa-api/application/pipelines/sigrid_bandeja.py`:
    `VistaDeSigrid` y `mirar_sigrid` (§10.3).
  - `services/postventa-api/interface_adapters/api/sigrid_bandeja.py`:
    `sigrid_de_la_bandeja`, `CAMPOS_DE_LA_FICHA` y la línea de R24.
- **Modificados de producción**, solo añadiendo:
  - `domain/models/errores.py`: `ReclamacionesSinVerificar(motivo, *, filas)`,
    su bloque de sección y un párrafo de la cabecera.
  - `function_app.py`: dos importaciones, `CACHE_CONTROL_SIN_CACHE`,
    `_sin_cache`, `_json_sin_cache`, la ruta `revision_sigrid`, su entrada en
    la lista de endpoints de la cabecera y su párrafo en la de seguridad
    («Con él los anónimos son veinticinco»).
- **Tests nuevos**: `tests/test_f065_aplicacion.py`, `tests/test_f065_http.py`,
  `tests/test_f065_datos_personales.py` y `tests/test_f065_alcance_cerrado.py`.
- **Test de otra feature**: `tests/test_f010_endpoints_protegidos.py`. Gana
  `revision/sigrid` en `ENDPOINTS`, su comentario, y la cuenta pasa de 24 a 25
  (ver Desviaciones).
- `specs/F-065-revision-sigrid-backend/tasks.md`: T7, T8 y T9 `[x]`.
- **Sin tocar** (lo comprueba T9 contra `b863b46`): `fabrica.py` en este
  bloque, todo `revision.py` (modelo, pipeline y borde), el catálogo, todo el
  volcado, la normalización, la plantilla, `tiempos.py`, `config/settings.py`,
  `requirements*.txt`, los `.sql` y `services/postventa-front/`.

### Decisiones de diseño

- **El orden de `mirar_sigrid`** es el de §10.3, y lo fijan los tests de R3:
  1. `listar(tope=10.000)`; si hay más, `contar` y `BandejaDemasiadoGrande`
     **sin leer Sigrid**. 10.000 justas sí se leen.
  2. Una sola lectura `leer(codigo_obra, tip)`.
  3. `llego_al_techo` lanza `ReclamacionesSinVerificar` con las `filas`. Se
     mira **antes** que la obra ambigua: si la lista viene cortada, ni siquiera
     se sabe cuántas obras hay.
  4. Más de un `obra_ref` lanza `ObraAmbigua`.
  5. Se mapea a `ReclamacionSigrid` (`estado` = `estado_codigo`, la misma
     `ficha`, **sin** `obra_ref`) y se llama a `cruzar`. `cruzar` se importa a
     nivel de módulo para que un test lo sustituya por `prohibido` y demuestre
     que no se cruza nada.
  Ningún mensaje de error lleva una fila: solo la obra y los recuentos.
- **O-A3-2.** El 503 sin `truncated` (ausente, texto o `0`) es un
  `CatalogoNoDisponible` del adaptador, y el borde lo traduce con
  `_sin_sigrid_o_sin_base`, como cualquier caída de Sigrid. Lo fija
  `test_f065_r8_o_a3_2_la_respuesta_que_no_dice_si_viene_cortada_es_503_y_no_409`
  con el **adaptador de verdad** y un `ClienteFalso`: 503, el texto «no dice
  si viene cortada», sin `codigo` y sin ningún secreto del adaptador (el
  `no-store` del 503 lo fija `test_f065_r35_las_de_error_tambien[sigrid]`).
- **La composición del borde** (R2): obra normalizada → `construir_reclamaciones_obra`
  → `construir_revision`. Con la obra inválida es 400 sin construir nada. Con
  la fábrica de verdad en `local` es 503 sin llamar a `construir_cliente_http`.
  Con la configuración incompleta es 503 nombrando las variables, no sus
  valores. El `tip` sale de `obtener_ajustes().sigrid_tip_reclamacion`
  también cuando los puertos llegan inyectados.
- **`proceso_nuevo`** sale de un indicador propio del módulo (`_atendida` con un
  `threading.Lock`), y **no** de `es_primera_peticion()` de F-060. Un test lo
  comprueba: tras usar la ruta, el listado de F-060 sigue registrando
  `proceso_nuevo=True`. `segundos_de_proceso()` sí se reutiliza.
- **La línea de R24** se compone aquí, no con `Cronometro.linea()` (que dice
  «F-060 tiempos del listado»), y en el mismo formato:
  ```
  F-065 sigrid de la bandeja: obra=… resultado=… total=… proceso_nuevo=… segundos_de_proceso=… <tramos> aplicacion=… calculo=… serializar=… reclamaciones=… evaluadas=… conflictos=… avisos=… bytes=…
  ```
  Los tramos son `construir.sigrid`, `construir.bandeja`, `bandeja.listar`,
  `sigrid.leer` (con `Cronometro.medir`), `aplicacion`, `calculo` y
  `serializar`.
  - Con error, `resultado` es el nombre del tipo y los recuentos y `bytes` son
    `-`. Con la obra inválida, `obra=-`.
  - Va en un `finally`: exactamente una línea por petición.
- **Los bytes** son `len(json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"))`
  dentro del tramo `serializar`, igual que serializa `_json`. Un test comprueba
  que coinciden con el cuerpo de la respuesta. El precio es serializar dos
  veces; con un cuerpo de cientos de KB es aceptable y mide lo que viaja.
- **El cuerpo de R20.**
  - Las claves se comprueban **exactas** en cada nivel. `guardado_cod` va en
    todos los hallazgos (`null` donde no toca). `incidencia_id`, como texto o
    `null`.
  - La `ficha` lleva **exactamente** `CAMPOS_DE_LA_FICHA` (19), con las fechas
    en ISO. Un test exige que las claves de la `ficha` sean exactamente los
    campos de `FichaReclamacion`, así que un campo nuevo del puerto rompe el
    test y obliga a decidir si viaja.
  - `leido_at_utc` es ISO con microsegundos en UTC (`ahora=` como costura de
    test).
  - El orden de reclamaciones y hallazgos es el del dominio (R21). Los
    `coincide` ya llegan en el orden de R18.
- **El `resumen`.**
  - `por_estado` lleva siempre los cinco códigos; los desconocidos van solo
    en `estados_desconocidos`, y entre los dos suman `reclamaciones`.
  - `emparejadas` cuenta las reclamaciones con incidencia.
  - `incidencias_con_conflicto` e `incidencias_con_aviso` cuentan incidencias
    **distintas** con algún hallazgo de esa severidad, así que una incidencia
    puede estar en las dos.
  - `por_tipo` y `por_criterio` cuentan los hallazgos que viajan, ya con el
    tope de R18.
- **`incidencias`**: solo las que tienen algún hallazgo, con su estado y sus
  valores **vigentes** (`valores_vigentes`, `estado_de` de F-056 sin
  cambiarlos) y `coincidencias_total`.
- **La traducción de errores de la ruta** reutiliza sin cambiarlos
  `_error_de_revision` (400 y 409 `bandeja_demasiado_grande` con el `total`),
  `_rechazo_de_obra` (409 `obra_ambigua`) y `_sin_sigrid_o_sin_base` (503).
  - Lo único nuevo es el 409 `reclamaciones_sin_verificar`, con
    `{error, codigo, filas}`.
  - **Todas** las respuestas, también las de error, llevan
    `Cache-Control: no-store` (R35).
  - Un test exige que ninguna otra ruta lo lleve y que `"no-store"` aparezca
    una sola vez en `function_app.py`.
- **R37** (nada guardado). Lo comprueban tres cosas:
  - un test que parchea `open` y las escrituras de `Path` tras una llamada de
    calentamiento;
  - un barrido regex del código ejecutable (sin docstrings, por AST) de las
    seis piezas de F-065;
  - la regla de que de `persistencia` solo se importa `construir_revision`.
- **R38/R39** (datos personales). Las fichas de los tests llevan datos
  inventados («Ejemplo …», `@ejemplo.invalid`, `000 000 00n`). Ningún valor de
  ninguna aparece en ningún registro, ni con los dobles ni con el adaptador de
  verdad (entera, `truncated`, dos obras, sin `truncated`), ni con 200 ni con
  error. Un barrido exige que los ficheros de F-065 (tests, spec, progress)
  solo traigan correos `@ejemplo.invalid`, con un control que demuestra que
  ve un correo real.
- **Los helpers de test** viven en `test_f065_aplicacion.py` y los otros dos
  los importan (patrón que ya hay en el repo), sin un `utiles_*.py` nuevo.

### Desviaciones

- **`tests/test_f010_endpoints_protegidos.py`**, que §9.2 no nombra. Toda ruta
  nueva tiene que pasar por su cuenta de rutas anónimas, y T8 exige el servicio
  entero en verde. Lo hicieron igual F-019, F-036, F-056, F-059 y F-060.
  - Cambian **solo** `ENDPOINTS` (más `revision/sigrid` y un párrafo del
    comentario) y la cuenta de
    `test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay` (24 → 25). Ninguna
    aserción se quita.
  - La guarda T9 lo declara como única excepción y lo vigila: solo cambian
    esas dos definiciones, ninguna aserción de la base se pierde, y la de la
    cuenta conserva su número de aserciones.
- **La guarda T9** declara además, como ficheros que la rama puede tocar, los
  documentos de §9.2 que llegan en el Bloque A5 (`docs/ARCHITECTURE.md`,
  `docs/INTEGRACION.md`), el script 29, `specs/F-065…`, `specs/F-064…`
  (enmiendas de contrato), `progress/`, `features.json` y `BACKLOG.md`. El
  Bloque A4 bis (T17) tendrá que ampliar `PIEZAS_DE_F065`, `INTOCABLES` y
  `NUEVOS_DE_F065` con lo que toca del volcado (§15.6). Así lo dice la cabecera
  de la guarda.

### Fase RED (Bloque A4)

Los tests de T7, escritos antes que el código (`d26060d`), lanzados desde
`services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_aplicacion.py tests/test_f065_http.py tests/test_f065_datos_personales.py -q --tb=line -p no:cacheprovider
FFFF.FFFFFFFFFFFFFFEEEEEEEEEFFFFFEFFFFFFFFFFEEEFEEEEEEFEFEFEEFEEEFFFFEEF [ 67%]
.FEFFFFF.FEFFFFF.....FFFFFFFFFF...                                       [100%]
=================================== ERRORS ====================================
_ ERROR at setup of test_f065_r1_la_obra_que_no_vale_es_400_sin_construir_nada[sin-obra] _
E   ImportError: cannot import name 'sigrid_bandeja' from 'interface_adapters.api' (C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\interface_adapters\api\__init__.py)
...
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_aplicacion.py:370: ImportError: cannot import name 'ReclamacionesSinVerificar' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\domain\models\errores.py)
...
FAILED tests/test_f065_aplicacion.py::test_f065_r4_mas_de_diez_mil_es_409_con_el_recuento_y_sin_sigrid
FAILED tests/test_f065_aplicacion.py::test_f065_r8_al_techo_es_409_con_las_filas_y_sin_cruzar
FAILED tests/test_f065_aplicacion.py::test_f065_r8_el_techo_va_antes_que_la_obra_ambigua
FAILED tests/test_f065_aplicacion.py::test_f065_r9_dos_obras_es_obra_ambigua_sin_cruzar
FAILED tests/test_f065_http.py::test_f065_r8_truncated_con_el_adaptador_de_verdad_es_409
FAILED tests/test_f065_http.py::test_f065_r8_o_a3_2_la_respuesta_que_no_dice_si_viene_cortada_es_503_y_no_409[sin-truncated]
FAILED tests/test_f065_http.py::test_f065_r8_o_a3_2_la_respuesta_que_no_dice_si_viene_cortada_es_503_y_no_409[texto]
FAILED tests/test_f065_http.py::test_f065_r8_o_a3_2_la_respuesta_que_no_dice_si_viene_cortada_es_503_y_no_409[cero]
FAILED tests/test_f065_http.py::test_f065_r35_las_de_error_tambien[techo] - I...
FAILED tests/test_f065_datos_personales.py::test_f065_r38_ni_la_ruta_ni_el_adaptador_de_verdad_registran_nada_de_una_fila[truncated]
...
65 failed, 11 passed, 30 errors in 4.32s
```

Las 11 que ya pasaban en RED lo hacen legítimamente:
- los controles de que los detectores no son ciegos;
- que el doble de la bandeja no deja hacer nada más;
- que el listado y las acciones no construyen el lector de Sigrid (R26);
- que ninguna otra ruta lleva `no-store`;
- el barrido de R37 sobre las piezas que ya existían (dominio, puerto,
  consulta y adaptador).

**El RED de comportamiento, no solo de importación.** En RED casi todo falla
por `ImportError`, que prueba que el test existía antes que el código pero no
qué comportamiento caza. Esa parte la dan los mutantes a mano (abajo): cada
requisito central tiene uno que lo rompe y su test lo mata, entre ellos:
- el techo que no frena el cruce (MA4);
- el techo después de la obra ambigua (MA6);
- `reclamaciones_sin_verificar` como 503 (MA29);
- `CatalogoNoDisponible` sin traducir, que es O-A3-2 (MA32);
- `no-cache` en lugar de `no-store` (MA35);
- el 200 sin `no-store` (MA36);
- `proceso_nuevo` con el indicador del listado (MA12);
- la base construida antes que Sigrid (MA11).

T9 es una guarda y no tiene RED propio. Su prueba de que no es ciega: con tres
violaciones sembradas a la vez en el árbol (un comentario en
`interface_adapters/api/revision.py`, una función `_otra` en `function_app.py`
y un `os.getenv` en el pipeline nuevo), revertidas después con `git checkout`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_alcance_cerrado.py -q --tb=no -p no:cacheprovider
FAILED tests/test_f065_alcance_cerrado.py::test_f065_s9_la_rama_solo_toca_los_ficheros_declarados
FAILED tests/test_f065_alcance_cerrado.py::test_f065_s9_en_cada_fichero_tocado_solo_cambia_lo_declarado[function_app.py]
FAILED tests/test_f065_alcance_cerrado.py::test_f065_s9_3_la_rama_no_toca_ningun_intocable
FAILED tests/test_f065_alcance_cerrado.py::test_f065_r28_el_codigo_de_f065_no_lee_el_entorno_ni_escribe_ni_guarda
4 failed, 42 passed in 47.71s
```

Además, cada detector tiene su test «no es ciego» dentro de la guarda.

### Tests (Bloque A4)

Desde `services/postventa-api`, sobre `ca66e3f`:

| Qué | Resultado |
|---|---|
| Los del bloque: `test_f065_aplicacion.py` (20), `test_f065_http.py` (67), `test_f065_datos_personales.py` (23), `test_f065_alcance_cerrado.py` (46) y `test_f010_endpoints_protegidos.py` (8) | **164 passed** en 26,20 s |
| Todos los `test_f065_*.py` | **531 passed** en 47,04 s |
| F-065, F-010 y **todas** las guardas de arquitectura, fábricas y alcance (`test_*arquitectura*`, `test_*fabrica*`, `test_*alcance_cerrado*`), sobre `fb0ad71` | **1105 passed, 234 skipped** en 420,39 s (los *skipped* son las guardas de diff de otras ramas) |
| El servicio entero (`pytest` sin filtro), sobre `71ded50` (T8; después solo se han añadido tests) | **9589 passed, 365 skipped** en 1525,54 s |
| `ruff check` de los ficheros nuevos y tocados | limpio salvo `I001` (la línea en blanco entre bloques de `import` que lleva todo el repositorio, igual que en A3) |

### Mutación (Bloque A4)

**Herramienta** (`progress/mutacion_F-065_bloqueA4.md`, con la nota del
implementer sobre la suite reducida y quién importa lo mutado). Base
`509ef57`, 4 ficheros y 561 líneas en alcance, 1 worker, en un `git worktree`
desechable, porque muta en el sitio y la suite entera corría a la vez.

- **1.ª pasada**, sobre `d338de7`: **19 generados, 16 muertos, 3
  supervivientes**, 206,0 s. Los tres eran huecos reales:
  - la vista se podía cambiar (`frozen=False`);
  - nadie miraba el valor inicial del indicador propio;
  - los bytes con `ensure_ascii=True` coincidían porque el cuerpo de los tests
    era ASCII.
  Los tres tests nuevos van en `fb0ad71`.
- **2.ª pasada**, sobre `fb0ad71`: **19 generados, 19 muertos, 0
  supervivientes, 0 timeouts**, 293,5 s. `ca66e3f` solo añade tests.

**A mano: 40.** La herramienta solo genera 19 y no toca el orden, las
cabeceras, los recuentos ni la traducción de cada error, que son lo que sostiene
la ruta. Los mutantes a mano cubren eso. Script fuera del repo, en otro
worktree desechable; misma suite reducida, sin `-x`.

- **1.ª vuelta**, sobre `d338de7`: 36 muertos y **3 supervivientes**:
  - MA14 (`ensure_ascii`), el mismo hueco de la herramienta;
  - **MA16**: `por_estado` solo con los estados presentes. La obra de ejemplo
    tiene los cinco, así que nadie lo veía;
  - **MA23**: el `tip` fijo a 708. Todos los tests usaban el defecto.
  Además, **MA18 salió mal formado** (dejaba un error de sintaxis y «moría»
  por importación), así que se rehízo sustituyendo la línea entera. MA16 y
  MA23 tienen su test en `ca66e3f`: el resumen con todas sus claves a cero y
  `test_f065_r5_el_tipo_de_concepto_sale_de_la_configuracion`.
- **Vuelta definitiva**, sobre `ca66e3f`, con el árbol limpio antes y después:
  **40, 40 muertos, 0 supervivientes.**

| Id | Mutante | Resultado (tests que fallan) | Uno de los que lo matan |
|---|---|---|---|
| MA1 | la bandeja de 10.000 justas ya es demasiado grande | muerto (1) | `r4_justo_diez_mil_no_es_demasiado` |
| MA2 | el total del 409 sin contar (len de lo leido) | muerto (2) | `r4_bandeja_demasiado_grande_409_con_el_recuento_sin_sigrid` |
| MA3 | Sigrid se lee antes de mirar el tamano de la bandeja | muerto (17) | `r1_la_obra_se_normaliza_como_en_f036` |
| MA4 | el techo no frena el cruce | muerto (10) | `r22_r40_los_errores_no_repiten_ninguna_fila` |
| MA5 | obra ambigua solo con tres obras | muerto (7) | `r22_r40_los_errores_no_repiten_ninguna_fila` |
| MA6 | obra ambigua antes que el techo | muerto (2) | `r8_el_techo_va_antes_que_la_obra_ambigua` |
| MA7 | el estado de la reclamacion es el tipo | muerto (12) | `r19_la_vista_lleva_la_bandeja_entera_y_el_cruce_del_dominio` |
| MA8 | la referencia es la descripcion | muerto (11) | `r10_la_referencia_empareja_con_la_bandeja_de_la_obra` |
| MA9 | el mensaje del techo con el cod de una fila | muerto (2) | `r22_r40_los_errores_no_repiten_ninguna_fila` |
| MA10 | las filas del 409 son cero | muerto (3) | `r8_al_techo_409_reclamaciones_sin_verificar_con_las_filas` |
| MA11 | se construye la base antes que Sigrid | muerto (6) | `r2_fuera_de_dev_y_pro_503_con_la_fabrica_de_verdad_y_sin_abrir_nada` |
| MA12 | proceso_nuevo con el indicador del listado | muerto (2) | `r24_el_borde_no_llama_al_indicador_del_listado` |
| MA13 | el indicador propio no se apaga | muerto (2) | `r24_proceso_nuevo_es_propio_y_no_toca_el_del_listado` |
| MA14 | los bytes con ensure_ascii | muerto (1) | `r24_los_bytes_son_los_del_cuerpo_tambien_con_acentos` |
| MA15 | la linea sin calculo | muerto (1) | `r24_una_linea_con_200_con_los_tramos_los_recuentos_y_los_bytes` |
| MA16 | por_estado solo con los que hay | muerto (1) | `r9_ninguna_fila_es_200_con_las_listas_vacias` |
| MA17 | emparejadas cuenta todas | muerto (1) | `r20_el_resumen` |
| MA18 | incidencias con conflicto cuenta hallazgos | muerto (1) | `r20_el_resumen` |
| MA19 | guardado_cod siempre null | muerto (1) | `r20_guardado_cod_solo_en_volcada_no_encontrada_y_codigo_distinto` |
| MA20 | incidencias: toda la bandeja | muerto (1) | `r9_ninguna_fila_es_200_con_las_listas_vacias` |
| MA21 | la fecha de la reclamacion en dd/mm/aaaa | muerto (2) | `r20_cada_reclamacion_con_sus_campos_y_su_ficha` |
| MA22 | con error, resultado=200 | muerto (4) | `r24_una_linea_tambien_con_error_con_el_tipo` |
| MA23 | el tipo de concepto fijo | muerto (1) | `r5_el_tipo_de_concepto_sale_de_la_configuracion` |
| MA24 | obra=None con la obra invalida | muerto (1) | `r24_una_linea_tambien_con_error_con_el_tipo` |
| MA25 | leido_at_utc sin la zona normalizada | muerto (1) | `r20_leido_at_utc_es_el_instante_de_la_lectura_en_utc` |
| MA26 | la ficha sin un campo | muerto (3) | `r20_cada_reclamacion_con_sus_campos_y_su_ficha` |
| MA27 | coincidencias_total por defecto 1 | muerto (1) | `r20_incidencias_solo_las_que_tienen_hallazgos_con_sus_vigentes` |
| MA28 | el 400 sin no-store | muerto (1) | `r35_las_de_error_tambien` |
| MA29 | reclamaciones_sin_verificar como 503 | muerto (3) | `r38_ni_la_ruta_ni_el_adaptador_de_verdad_registran_nada_de_una_fila` |
| MA30 | reclamaciones_sin_verificar sin las filas | muerto (2) | `r8_al_techo_409_reclamaciones_sin_verificar_con_las_filas` |
| MA31 | obra_ambigua como 422 | muerto (4) | `r35_las_de_error_tambien` |
| MA32 | CatalogoNoDisponible sin traducir | muerto (10) | `r23_sin_sigrid_o_sin_base_503_con_el_cuerpo_de_siempre` |
| MA33 | el 503 con otro texto | muerto (2) | `r23_sin_sigrid_o_sin_base_503_con_el_cuerpo_de_siempre` |
| MA34 | bandeja demasiado grande como 413 | muerto (2) | `r35_las_de_error_tambien` |
| MA35 | no-cache en vez de no-store | muerto (7) | `r35_el_sin_cache_solo_lo_usa_esta_ruta` |
| MA36 | el 200 sin no-store | muerto (1) | `r35_la_respuesta_200_lleva_no_store` |
| MA37 | la ruta acepta POST | muerto (1) | `r26_la_ruta_es_otra_funcion_y_get` |
| MA38 | el error no guarda las filas | muerto (4) | `r8_al_techo_409_reclamaciones_sin_verificar_con_las_filas` |
| MA39 | la ConfiguracionPgIncompleta sin traducir | muerto (1) | `r2_si_la_base_no_se_construye_503` |
| MA40 | la obra sin normalizar | muerto (1) | `r1_la_obra_se_normaliza_como_en_f036` |

### Cobertura (Bloque A4)

Con `coverage run --branch -m pytest tests/test_f065_aplicacion.py tests/test_f065_http.py tests/test_f065_datos_personales.py tests/test_f010_endpoints_protegidos.py` (sobre `d338de7`; los commits siguientes solo añaden tests, así que la cobertura de lo cambiado no puede bajar):

- `application/pipelines/sigrid_bandeja.py`: 28/28 sentencias y 6/6 ramas.
- `interface_adapters/api/sigrid_bandeja.py`: 94/94 sentencias y 14/14 ramas.
- `domain/models/errores.py`, a partir de la línea 1590 (la clase nueva): sin
  ninguna línea sin cubrir. Lo que queda sin cubrir en ese fichero son errores
  de otras features.
- `function_app.py`, a partir de la 2010: las únicas líneas sin cubrir son la
  2029 a la 2037, que son el `volcado_volcar` de F-059. De la 2042 en adelante
  (la constante, `_sin_cache`, `_json_sin_cache` y `revision_sigrid`) no falta
  ninguna línea ni ninguna rama.

**Cobertura de lo cambiado: 100 %.** `python -m harness.cobertura --base 509ef57
--cov <ese coverage.json> --raiz services/postventa-api` responde
`PUERTA COBERTURA: N/A (F-065: las líneas cambiadas no contienen sentencias
ejecutables)` con ese `coverage.json` de suite reducida (lanzado desde la raíz
del worktree). No lo he investigado más, porque la medición a mano de arriba
es directa. La puerta oficial es la de `init.sh`, que lanza el líder, y si
vuelve a dar N/A con la suite entera merece mirarse.

### Pendiente (Bloque A4)

- `bash harness/init.sh` entero, con la puerta de cobertura (el líder), y la
  **review del Bloque A4** (`tasks.md`: «Parar»).
- **Bloque A4 bis**, sin empezar: el veredicto, la guarda del ensayo y
  NPR → `choca`. Cuando llegue, T17 amplía la guarda de este bloque
  (`PIEZAS_DE_F065`, `INTOCABLES`, `NUEVOS_DE_F065`) a lo que toque del volcado.
- **Bloque A5 (T10)**: los documentos de §9.2, `azure-apps/postventa_incidencias.md`
  y la fila de consumidores de `azure-apps/sigrid_api.md`, porque la API expone
  una ruta nueva. En este bloque no se ha tocado ningún documento: no entraba
  en T7–T9.
- **T11**: la campaña de mutación de la feature entera.
- Sin verificaciones MANUAL en este bloque. La ruta contra Sigrid de verdad
  (volumen, tiempos y bytes de R29) es del despliegue, no de local.

### Evidencias (Bloque A4)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **164 passed** los del bloque en 26,20 s; **531 passed** todo F-065 en 47,04 s; **1105 passed, 234 skipped** con todas las guardas de arquitectura, fábricas y alcance en 420,39 s; servicio entero **9589 passed, 365 skipped** en 1525,54 s (sobre `71ded50`) |
| Cobertura de las líneas cambiadas | **100 %**: el pipeline 28/28 sentencias y 6/6 ramas; el borde 94/94 y 14/14; la clase nueva de `errores.py` y la ruta con sus ayudantes de `function_app.py`, enteras. Medida con `coverage --branch`; la puerta de `init.sh` es del líder |
| Mutantes | Herramienta: **19 generados, 19 muertos, 0 supervivientes, 0 timeouts**, 1 worker, 293,5 s, sobre `fb0ad71` con el árbol limpio (suite reducida; la 1.ª pasada dio 3 supervivientes, cada uno con su test). A mano: **40, 40 muertos, 0 supervivientes**, sobre `ca66e3f` |
| Tiempo de la suite | 26,20 s la del bloque; 1525,54 s la del servicio entero |

## Bloque A4 bis · T13–T14 (2026-10-29)

Encargo del líder: la **primera mitad** del Bloque A4 bis, **solo T13 y T14**,
el veredicto por incidencia. La guarda del ensayo (T15–T17) va en otro encargo
y no se ha empezado: ni `volcado.py`, ni `guarda_sigrid.py`, ni la consulta por
unidades, ni `function_app.py`. Trabajo hecho sobre el A4 aprobado (`0919e5d`),
con S-1 a S-9 aprobadas, T-A0 bis hecho y la **enmienda del humano a S-3**
(2026-10-28): una candidata cuya emparejada está en `NPR` da `choca`, no
`se_enlaza`. No me he conectado a Sigrid, a la base ni a SharePoint. No he
tocado `features.json`, `BACKLOG.md` ni `current.md`. `init.sh` entero lo lanza
el líder.

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `36d10b5` | T13 | Tests en RED: `tests/test_f065_veredicto.py` (nuevo) y el bloque `volcado` entre las claves exactas de `tests/test_f065_http.py`; T13 `[x]` |
| `af4b356` | T14 | El dominio (`Veredicto`, `VeredictoDeVolcado`, `ParDeCoincidencia`, `Cruce.pares`, `veredictos`), la vista del pipeline y el bloque `volcado` del borde; T14 `[x]` |
| `2ef038d` | T14 | Una aserción que mata MV18, el único superviviente de los mutantes a mano |
| (el siguiente) | — | Este informe y `progress/mutacion_F-065_bloqueA4bis_veredicto.md` |

### Ficheros tocados

- **Producción**. Son tres ficheros nuevos de F-065, así que no hay ninguno de
  otra feature:
  - `services/postventa-api/domain/models/sigrid_bandeja.py`:
    - `Veredicto` (`va`, `se_enlaza`, `ya_existe`, `choca`, en ese orden);
    - `ParDeCoincidencia(sigrid_cod, estado, criterios, parecido, fecha)`;
    - `VeredictoDeVolcado(incidencia_id, veredicto, sigrid_cods)`;
    - el campo `Cruce.pares`, con `cruzar` rellenándolo;
    - `veredictos(situaciones, cruce)` y su ayudante `_veredicto`;
    - `_LOS_DOS_CRITERIOS`, `_par` y `_sin_pares`;
    - la cabecera del módulo, que gana el párrafo del veredicto.
  - `services/postventa-api/application/pipelines/sigrid_bandeja.py`:
    `VistaDeSigrid.veredictos`, y `mirar_sigrid` lo rellena con
    `veredictos(situaciones, cruce)` (paso 6 de la cabecera).
  - `services/postventa-api/interface_adapters/api/sigrid_bandeja.py`: la clave
    `volcado` del cuerpo, `_volcado` y `_por_veredicto`, y el párrafo de la
    cabecera.
- **Tests**:
  - `tests/test_f065_veredicto.py`: nuevo, 64 tests.
  - `tests/test_f065_http.py`: `CLAVES_DE_LA_RESPUESTA` gana `volcado`; se
    añaden `CLAVES_DEL_VOLCADO`, `CLAVES_DE_VEREDICTO` y
    `VALORES_DEL_VEREDICTO`; las claves permitidas de R22 ganan las del bloque,
    y la tabla de la cabecera gana una fila. Ver «Desviaciones».
- `specs/F-065-revision-sigrid-backend/tasks.md`: T13 y T14 `[x]`.
- **Sin tocar**: `revision.py`, `volcado.py`, `normalizacion.py`,
  `plantilla_incidencias.py`, el puerto, la consulta, el adaptador,
  `fabrica.py`, `errores.py`, `function_app.py` y ningún test de F-059 ni de
  otra feature.

### Decisiones de diseño

- **`veredictos` es una función pura** del dominio y recibe lo que ya da
  `cruzar`. De `Cruce.reclamaciones` saca la emparejada de cada incidencia: es
  la única reclamación con su `incidencia_id`, y por R13 bis siempre es la de
  código mayor. De `Cruce.pares` saca todos sus pares. `Cruce` no gana nada más
  por la regla 0, como dice §15.2. La precedencia, en `_veredicto`:
  0. Si hay emparejada y está en `NPR`: `choca`, con **solo** su código
     (enmienda a S-3).
  1. Si hay emparejada (en cualquier otro estado, también uno desconocido o
     ninguno): `se_enlaza`, con su código. Si son varias, solo la mayor, que es
     la emparejada: R41 dice «la emparejada».
  2. Si algún par tiene los dos criterios y está abierto (`SAT`/`PTE`):
     `ya_existe`, con los códigos de **esos** pares.
  3. Si algún par está abierto, es decir, si hay algún conflicto: `choca`, con
     los códigos de **todos** los abiertos.
  4. En los demás casos, `va`, sin códigos. Así quedan las que solo tienen
     avisos (`TER`/`CER`).
  Los códigos salen en el orden de los pares, que ya es el de R18.
- **Lectura de «las de los dos criterios en `ya_existe`»**: solo los pares con
  los dos criterios **y abiertos**. Uno con los dos criterios contra una
  cerrada es un aviso y no decide nada: con una `TER` de dos criterios y una
  `PTE` de uno, la incidencia sale `choca` con la `PTE`. Así lo leo de R41
  («con una reclamación abierta») y lo fija un test.
- **`Cruce.pares`** lleva solo las incidencias evaluables con algún par, las
  mismas claves que `coincidencias_total`; un test fija que coinciden. Los pares
  van en el orden de R18, sin el tope de 10, y sus 10 primeros son exactamente
  los `coincide` de la vista. `estado` es `EstadoSigrid`: solo dan pares los
  cuatro estados conocidos. Es un campo **con valor por defecto** (un mapa
  vacío e inmutable), para que `Cruce(...)` siga construyéndose sin él como en
  `test_f065_r9_sin_nada_que_cruzar`, que no cambia.
- **El orden de los veredictos** es el de `situaciones`, sin reordenar:
  - la ruta pasa la bandeja tal como la da `listar`, que ya viene en el orden
    de R25 de F-056 (R42);
  - el ensayo (T16) podrá pasar las suyas en el orden pedido (R47) con la
    misma función.
- **El bloque `volcado`** (R42) lo arma el borde con `VistaDeSigrid.veredictos`.
  La aplicación no calcula nada más: solo llama a la función del dominio, y lo
  fija un test con un espía.
  - `unidad_codigo` y `estado` son los **vigentes** (`valores_vigentes`,
    `estado_de`), es decir, los de lo aprobado.
  - `por_veredicto` y cada unidad de `por_unidad` llevan siempre las cuatro
    claves, en el orden del enumerado.
  - `por_unidad` solo lleva las unidades con candidatas, ordenadas por código.
  - `sigrid_cods` va entero, sin el tope de los hallazgos.
  - `unidad_codigo` nunca es nulo (`ValoresIncidencia.unidad_codigo: str`), así
    que no hace falta una clave `null` en `por_unidad`.
- **R49, con fixtures**: una obra con candidatas en dos unidades y una tercera
  sin candidatas pero con reclamaciones que casarían con ellas si el cruce no
  fuera por unidad. Da los cuatro veredictos y la regla 0. El veredicto con
  toda la obra es igual que con solo `{U, U2}`, y también que con la unidad de
  cada candidata por separado, que es el troceo de D-6.
  - **La excepción escrita**, en dos casos: la única `PVI-` en otra unidad
    (con la obra `se_enlaza`, con su unidad `va`) y la mayor de dos en otra
    unidad y anulada (con la obra `choca`, con su unidad `se_enlaza` con la
    menor). Las dos las para la pasarela con `referencia_en_conflicto`.
  - En los dos lados la bandeja es **entera**: es lo que necesita el
    emparejamiento. Qué bandeja pasará el ensayo es cosa de T16.
- **`ReclamacionSigrid.ficha` sigue sin admitir `None`** (§15.2 lo prevé para
  la lectura de la guarda). Es de T16, que es quien lee sin R33: aquí no lo
  necesita nada.

### Desviaciones

- **`tests/test_f065_http.py` cambia dos aserciones** de la forma de R20:
  - `set(cuerpo) == CLAVES_DE_LA_RESPUESTA` ahora incluye `volcado`;
  - las claves permitidas de R22 ganan las del bloque.

  Es un test de F-065 y es la consecuencia directa de R42 («aditivo: R20 no
  pierde ni cambia nada»): no se quita ninguna clave ni ninguna aserción. Va en
  el commit de T13, porque es parte del RED. T14 lo pide en verde y la guarda
  T9 lo admite (patrón `test_f065_*.py`).
- Nada más. No he tenido que decidir nada que la spec no diga, salvo las
  lecturas de arriba sobre los códigos de `ya_existe` y de `se_enlaza` con
  varias, y las dos salen del texto de R41.

### Fase RED (T13)

**1. Contra el árbol de `0919e5d`** (sin nada de T14), desde
`services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_veredicto.py tests/test_f065_http.py -q --tb=line -p no:cacheprovider --continue-on-collection-errors
..........................F..................F.....................      [100%]
=================================== ERRORS ====================================
________________ ERROR collecting tests/test_f065_veredicto.py ________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_veredicto.py'.
...
tests\test_f065_veredicto.py:45: in <module>
    from domain.models.sigrid_bandeja import (
E   ImportError: cannot import name 'ParDeCoincidencia' from 'domain.models.sigrid_bandeja' (C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\domain\models\sigrid_bandeja.py)
================================== FAILURES ===================================
E   AssertionError: assert {'criterio', ...aciones', ...} == {'criterio', ...aciones', ...}
      Extra items in the right set:
      'volcado'
...
C:\Users\pgris\PycharmProjects\postventa-f065\services\postventa-api\tests\test_f065_http.py:906: KeyError: 'volcado'
=========================== short test summary info ===========================
FAILED tests/test_f065_http.py::test_f065_r20_las_claves_de_la_respuesta_y_el_criterio
FAILED tests/test_f065_http.py::test_f065_r22_las_claves_son_solo_las_de_r20_y_r33
ERROR tests/test_f065_veredicto.py
2 failed, 65 passed, 1 error in 11.35s
```

**2. El RED de comportamiento, no solo de importación.** Con un `ImportError`
solo se prueba que el test es anterior al código. Para ver qué caza cada test,
pegué **temporalmente** en el dominio unos tipos de relleno: los tres tipos con
sus campos, `Cruce.pares` siempre vacío y `veredictos` devolviendo `()`. Sin
pipeline ni borde. Lancé la suite y lo revertí con `git checkout`, sin
versionarlo:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_veredicto.py tests/test_f065_http.py -q --tb=line -p no:cacheprovider
...
E   ValueError: not enough values to unpack (expected 1, got 0)          (×40: los ejemplos E1–E12, la regla 0, el orden de R18)
E   KeyError: 'volcado'                                                    (×8: el bloque de R42 y las dos de test_f065_http)
E   KeyError: UUID(int=1)                 (Cruce.pares sin los pares)
E   AttributeError: 'VistaDeSigrid' object has no attribute 'veredictos'
E   AttributeError: <module 'application.pipelines.sigrid_bandeja' ...> has no attribute 'veredictos'
E   AssertionError: assert {} == {UUID('000000...26, 9, 15)),)}
E   AssertionError: assert [] == [(1, <Veredic...to.VA: 'va'>)]
E   AssertionError: assert () == (VeredictoDeV....10/0074',)),)
...
FAILED tests/test_f065_veredicto.py::test_f065_r41_s3_e7_con_la_emparejada_en_npr_choca_con_solo_su_codigo[aprobada]
FAILED tests/test_f065_veredicto.py::test_f065_r41_s3_la_emparejada_en_npr_choca_tambien_con_un_ya_existe_por_criterios
FAILED tests/test_f065_veredicto.py::test_f065_r41_s3_la_menor_de_dos_en_npr_se_enlaza_con_la_mayor
FAILED tests/test_f065_veredicto.py::test_f065_r41_mira_todos_los_pares_y_no_los_diez_de_r18
FAILED tests/test_f065_veredicto.py::test_f065_r49_con_toda_la_obra_o_con_sus_unidades_el_mismo_veredicto
FAILED tests/test_f065_veredicto.py::test_f065_r42_por_unidad_las_unidades_de_las_candidatas_por_codigo
... (58 en total)
58 failed, 73 passed in 5.21s
```

Los 73 que pasan son los 65 de `test_f065_http.py` que no miran el bloque y 8
de `test_f065_veredicto.py`, que con esos tipos de relleno pasan por motivos
legítimos:
- los valores y los campos de los tipos;
- E12 y los demás estados que no son candidatas (que no tengan veredicto es
  justo lo que devuelve `()`);
- el cruce vacío.

El octavo **pasaba en vacío**:
`test_f065_r49_cada_candidata_con_solo_su_unidad_tiene_el_mismo_veredicto`
recorría un diccionario vacío. Antes del commit de T13 le añadí
`assert len(toda) == 6`, así que ya no puede pasar sin mirar nada.

**3. En verde, sobre `2ef038d`**:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f065_veredicto.py tests/test_f065_dominio.py tests/test_f065_http.py -q -p no:cacheprovider
276 passed in 13.41s
```

### Tests (T13–T14)

Desde `services/postventa-api`:

| Qué | Sobre | Resultado |
|---|---|---|
| La verificación de T14: `test_f065_veredicto.py` (64), `test_f065_dominio.py` y `test_f065_http.py` | `2ef038d` | **276 passed** en 13,41 s |
| Todos los `test_f065_*.py` | `af4b356` (después solo cambia una aserción) | **595 passed** en 103,61 s |
| Las guardas de arquitectura, alcance y fábricas (`test_*arquitectura*`, `test_*alcance_cerrado*`, `test_*fabrica*`) más `test_f010_endpoints_protegidos.py` | `af4b356` | **621 passed, 234 skipped** en 415,33 s. Los *skipped* son las guardas de diff de otras ramas. `test_f065_alcance_cerrado.py` pasa en verde: los tres ficheros de producción son nuevos de F-065 y los tests siguen el patrón `test_f065_*.py` |
| `ruff check` de los tres módulos y de los dos tests | `2ef038d` | Limpio salvo el `I001` de siempre (la línea en blanco entre bloques de `import` que lleva todo el repositorio) |

No he lanzado ni `init.sh` ni el servicio entero, como pedía el encargo. Los
tests de F-059 no se han ejecutado porque este encargo no toca nada de F-059:
eso es de T16.

### Mutación (T13–T14)

**Herramienta** (`progress/mutacion_F-065_bloqueA4bis_veredicto.md`, con la
nota del implementer): `--base 0919e5d`, 3 ficheros y 194 líneas en alcance,
1 worker, en un `git worktree` desechable de `af4b356`, con el árbol limpio
antes y después. La suite está reducida a los cinco ficheros que importan lo
mutado; la búsqueda de quién lo importa está en la nota.
- **7 generados, 7 muertos, 0 supervivientes, 0 timeouts**, en 103,0 s.
- La herramienta casi no encuentra qué mutar en este código. Solo da:
  - el `frozen` de los dos tipos;
  - el `not` de `es_candidata`;
  - el `==` de `NPR` y el de los dos criterios;
  - el `+= 1` del recuento por unidad (dos mutantes).

**A mano: 33.** Atacan lo que sostiene R41 y R42: la precedencia, los códigos
de cada veredicto, el orden, la regla 0, los pares y el bloque. Los lanza un
script fuera del repo, en otro worktree desechable, con la misma suite
reducida y sin `-x`. El script sustituye el texto exacto, comprueba que solo
aparece una vez y restaura el fichero byte a byte; el árbol queda limpio
después.
- **1.ª vuelta**, sobre `af4b356`: 32 muertos y **1 superviviente**, MV18 (el
  estado del par como texto y no como `EstadoSigrid`). Es casi equivalente,
  porque `StrEnum` compara igual que el texto, pero T16 (el ensayo) va a
  consumir ese campo y debe poder contar con el enumerado. Lo mata una aserción
  `type(p.estado) is EstadoSigrid`, en `2ef038d`.
- **2.ª vuelta**, de MV18 sobre `2ef038d`: muerto. Las otras 32 no hace falta
  repetirlas: `2ef038d` solo añade una aserción, y una aserción de más solo
  puede matar más.
- Resultado: **33, 33 muertos, 0 supervivientes.**

| Id | Mutante | Resultado (tests que fallan) | Uno de los que lo matan |
|---|---|---|---|
| MV1 | la emparejada en NPR se enlaza (sin la regla 0) | muerto (7) | `r41_s3_e7_con_la_emparejada_en_npr_choca_con_solo_su_codigo` |
| MV2 | la regla 0 con los códigos de los pares además | muerto (1) | `r41_s3_la_emparejada_en_npr_choca_tambien_con_un_ya_existe_por_criterios` |
| MV3 | `se_enlaza` por detrás de `ya_existe` | muerto (2) | `r41_se_enlaza_gana_a_ya_existe_y_a_choca_con_solo_la_emparejada` |
| MV4 | `ya_existe` también con una cerrada | muerto (4) | `r41_los_dos_criterios_con_una_cerrada_no_es_ya_existe_sino_va` |
| MV5 | `ya_existe` con cualquier criterio | muerto (13) | `r41_e1_un_criterio_con_una_pte_choca` |
| MV6 | `ya_existe` solo con la descripción | muerto (2) | `r41_e2_la_descripcion_100_con_una_sat_choca` |
| MV7 | `ya_existe` con los códigos de todas las abiertas | muerto (1) | `r41_ya_existe_lleva_solo_las_de_los_dos_criterios_abiertas_en_el_orden_de_r18` |
| MV8 | `choca` con los avisos entre sus códigos | muerto (3) | `r41_los_codigos_de_choca_en_el_orden_de_r18_y_sin_los_avisos` |
| MV9 | `choca` solo con el primer código | muerto (4) | `r41_mira_todos_los_pares_y_no_los_diez_de_r18` |
| MV10 | `choca` con los códigos en orden ascendente | muerto (4) | `r41_mira_todos_los_pares_y_no_los_diez_de_r18` |
| MV11 | las cerradas cuentan como abiertas | muerto (9) | `r41_los_dos_criterios_con_una_cerrada_no_es_ya_existe_sino_va` |
| MV12 | veredicto también para las que no son candidatas | muerto (12) | `r41_e6_b_con_los_dos_criterios_con_la_sat_emparejada_con_a_ya_existe` |
| MV13 | solo las aprobadas son candidatas (sin `en_duda`) | muerto (18) | `r41_e1_un_criterio_con_una_pte_choca[en_duda]` |
| MV14 | los veredictos ordenados por `incidencia_id` y no en el orden recibido | muerto (2) | `r41_solo_las_candidatas_y_en_el_orden_recibido` |
| MV15 | los pares con el tope de 10 | muerto (3) | `r41_mira_todos_los_pares_y_no_los_diez_de_r18` |
| MV16 | los pares ordenados por código y no en el orden de R18 | muerto (7) | `r41_mira_todos_los_pares_y_no_los_diez_de_r18` |
| MV17 | el par sin la fecha | muerto (1) | `r41_cada_par_con_su_codigo_estado_criterios_parecido_y_fecha` |
| MV18 | el estado del par como texto y no como `EstadoSigrid` | superviviente en `af4b356`; **muerto (1)** en `2ef038d` | `r41_los_pares_son_todos_en_el_orden_de_r18_y_empiezan_como_la_vista` |
| MV19 | sin la emparejada (nadie se enlaza) | muerto (27) | `r41_e7_emparejada_y_no_anulada_se_enlaza` |
| MV20 | la regla 0 con `is` (el estado llega como texto) | muerto (7) | `r41_s3_e7_con_la_emparejada_en_npr_choca_con_solo_su_codigo` |
| MV21 | los pares sin criterios | muerto (9) | `r41_e1_con_la_descripcion_de_e2b_los_dos_criterios_ya_existe` |
| MV22 | los pares sin parecido | muerto (1) | `r41_cada_par_con_su_codigo_estado_criterios_parecido_y_fecha` |
| MV23 | `pares` también para las incidencias sin pares (vacíos) | muerto (1) | `r41_pares_solo_de_las_evaluables_con_algun_par_y_sin_las_suyas` |
| MP1 | la vista sin veredictos | muerto (7) | `r42_las_candidatas_sus_veredictos_y_las_cuentas` |
| MP2 | los veredictos de un cruce vacío | muerto (6) | `r42_las_candidatas_sus_veredictos_y_las_cuentas` |
| MB1 | `por_unidad` sin ordenar | muerto (1) | `r42_por_unidad_las_unidades_de_las_candidatas_por_codigo` |
| MB2 | la unidad importada y no la vigente | muerto (1) | `r42_la_unidad_es_la_vigente` |
| MB3 | `por_veredicto` solo con los que hay | muerto (4) | `r42_el_bloque_volcado_con_sus_claves` |
| MB4 | los `sigrid_cods` del bloque con el tope de 10 | muerto (1) | `r42_la_ruta_da_todos_los_codigos_aunque_los_hallazgos_lleven_diez` |
| MB5 | `candidatas` cuenta toda la bandeja | muerto (2) | `r42_las_candidatas_sus_veredictos_y_las_cuentas` |
| MB6 | el estado del veredicto, fijo | muerto (1) | `r42_las_candidatas_sus_veredictos_y_las_cuentas` |
| MB7 | sin el bloque `volcado` | muerto (9) | `r42_el_bloque_volcado_con_sus_claves` |
| MB8 | cada unidad de `por_unidad` con las cuentas de toda la obra | muerto (1) | `r42_por_unidad_las_unidades_de_las_candidatas_por_codigo` |

### Cobertura (T13–T14)

Medida con `coverage run --branch` y la suite reducida (los cinco ficheros), sobre
`af4b356`, con el fichero de datos fuera del árbol para no ensuciar la guarda
de alcance:

```
Name                                       Stmts   Miss Branch BrPart  Cover
application\pipelines\sigrid_bandeja.py       29      0      6      0   100%
domain\models\sigrid_bandeja.py              282      0     78      0   100%
interface_adapters\api\sigrid_bandeja.py     106      0     16      0   100%
TOTAL                                        417      0    100      0   100%
```

**Cobertura de lo cambiado: 100 %, 63 de 63 sentencias** (las líneas añadidas
del diff `0919e5d..HEAD` que son sentencias ejecutables, cruzadas con el
`coverage.json`):
- el pipeline, 3/3;
- el dominio, 48/48;
- el borde, 12/12.

Ninguna rama queda sin cubrir. `python -m harness.cobertura --base 0919e5d
--cov <ese json> --raiz services/postventa-api` vuelve a responder `PUERTA
COBERTURA: N/A (… no contienen sentencias ejecutables)`, igual que en el A4.
Las claves del json salen relativas al servicio y con `\`, y sospecho que la
puerta no las casa con las rutas del diff. No lo he investigado: no es de este
encargo y la medición de arriba es directa. La puerta oficial es la de
`init.sh`.

### Pendiente (T13–T14)

- `bash harness/init.sh` entero (el líder).
- **T15–T17** (la guarda del ensayo), en el encargo siguiente. Lo que dejan
  preparado T13 y T14:
  - `veredictos` acepta las situaciones **en el orden que se le den**, que en
    el ensayo será el pedido (R47);
  - `ParDeCoincidencia.estado` es `EstadoSigrid`;
  - `ReclamacionSigrid.ficha` sigue sin admitir `None`, y T16 tendrá que
    abrirla para la lectura sin R33 (§15.2). Al hacerlo, el borde de esta ruta
    sigue leyendo fichas no nulas, porque la ruta lee con R33.
- **Para F-040**: la forma del bloque `volcado` es la de §15.3, con los cuatro
  veredictos siempre presentes en `por_veredicto` y en cada unidad.
- **La review del Bloque A4 bis** llega después de T17 (`tasks.md`: «Parar»).
- Sin verificaciones MANUAL en esta mitad.

### Evidencias (T13–T14)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | **276 passed** los de la verificación de T14, en 13,41 s; **595 passed** todo F-065, en 103,61 s; **621 passed, 234 skipped** las guardas de arquitectura, alcance y fábricas más F-010, en 415,33 s |
| Cobertura de las líneas cambiadas | **100 %** (63/63 sentencias y ninguna rama sin cubrir), con `coverage --branch`. La puerta de `harness.cobertura` da N/A con el json de la suite reducida (ver arriba); la de `init.sh` es del líder |
| Mutantes | Herramienta: **7 generados, 7 muertos, 0 supervivientes, 0 timeouts**, 1 worker, 103,0 s, sobre `af4b356` con el árbol limpio (suite reducida). A mano: **33, 33 muertos, 0 supervivientes**. MV18 sobrevivió en `af4b356` y lo mata `2ef038d` |
| Tiempo de la suite | 13,41 s la de la verificación de T14; 103,61 s todo F-065 |
