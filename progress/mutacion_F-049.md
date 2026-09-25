<!-- progress/mutacion_F-049.md -->
# F-049 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-049 --workers 1` el 2026-09-25 09:24.

## Alcance

Origen del diff: **rama** (`884a0ee58ddb9883cfbce2c566a0f7c1f6aa96c9` .. `feature/F-049-villa-tres-cifras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/destino_posventa.py` | 10 |
| **Total** | **10** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 0 |
| Mutantes evaluados | 0 |
| Muertos | 0 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 0.0 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Mutación a mano (la herramienta no genera mutantes para esta línea)

La campaña del arnés, lanzada sola con
`python -m harness.mutacion --feature F-049 --timeout 900 --workers 6`, ve 10
líneas en alcance y genera **0 mutantes**: 9 de esas líneas son docstring, y
la única de código, `return f"VILLA {int(encaje['n']):03d}"`, no tiene
comparaciones, aritmética, lógica, `not`, booleanos ni enteros literales, que
son los únicos operadores de `harness/mutacion.py` (el `03` es una
especificación de formato dentro de la f-string, no un `ast.Constant` entero).
(La cabecera de arriba dice `--workers 1`: con cero mutantes la herramienta no
llega a abrir worktrees.)

Por eso se muta **a mano**, como en F-013 T20, con el script
`mutar_f049.py` (en el scratchpad de la sesión, fuera del repositorio): cada
mutante sustituye la línea, corre `tests/test_f049_villa_tres_cifras.py` y
todos los `tests/test_f013_*.py` con `-x`, y restaura el fichero.

| Mutante | Línea mutada | Resultado | Test que lo caza |
|---|---|---|---|
| M1 · ancho 2 (la regresión) | `:02d` | muerto | `test_f049_r1_la_villa_se_crea_con_tres_cifras[… VILLA 001]` |
| M2 · ancho 4 | `:04d` | muerto | ídem |
| M3 · sin relleno | `{int(n)}` | muerto | ídem |
| M4 · relleno de texto, sin `int()` | `{encaje['n']:0>3}` | muerto | `…[0677.03VILLA 0013.-VILLA 013]` (los ceros del `con.cod` no cuentan) |
| M5 · relleno con blancos | `:3d` | muerto | `…[… VILLA 001]` |
| M6 · sin blanco tras `VILLA` | `f"VILLA{…}"` | muerto | ídem |
| M7 · `:03` sin tipo | `:03` | **sobrevive** | ninguno: **equivalente** |
| M8 · `:0=3d` | `:0=3d` | **sobrevive** | ninguno: **equivalente** |
| M9 · minúsculas | `f"Villa {…}"` | muerto | `…[… VILLA 001]` |

**7 de 9 muertos; los 2 supervivientes son equivalentes**, no huecos:

- **M7** (`:03`): para un `int`, el formato sin tipo es `d`. `format(n, "03")
  == format(n, "03d")` para todo entero.
- **M8** (`:0=3d`): el `0` delante del ancho ya pone relleno `0` **y**
  alineación `=` (relleno tras el signo), así que `:0=3d` es igual que `:03d`
  **para todo entero, negativos incluidos**: `format(-5, '0=3d') ==
  format(-5, '03d') == '-05'`.

> **Corrección del 2026-09-25 (review de F-049, §6.2).** La viñeta de M8
> decía, literal: *«Solo se distinguiría con un negativo, y `<n>` sale de
> `PATRON_CODIGO_UNIDAD`, `[0-9]+`: nunca lo es.»* **Era falso**: con un
> negativo tampoco se distingue (lo señaló el reviewer). La conclusión se
> mantiene y queda más fuerte: M8, como M7, es equivalente para **cualquier**
> entero, sin depender del patrón.

Comprobado numéricamente, **también con negativos**: `format(n,'03') ==
format(n,'03d') == format(n,'0=3d')` para todo `n` en `-200000 … 199999`
(resultado `True`; antes solo se había comprobado `0 … 199999`). Ningún test
puede distinguirlos, así que no se añade ninguno.
