<!-- progress/mutacion_F-031.md -->
# F-031 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-031 --workers 3` el 2026-09-22 13:41.

## Alcance

Origen del diff: **rama** (`127e457579eceae2611f854beccb840aee4e1f68` .. `feature/F-031-nombrado-persistido`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | 167 |
| `services/postventa-api/domain/models/errores.py` | 49 |
| `services/postventa-api/domain/models/nombrado.py` | 26 |
| `services/postventa-api/function_app.py` | 15 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 48 |
| **Total** | **305** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 78.6 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Nota del implementer · ésta es la campaña de T16, la de la feature entera

> Lanzada al cerrar el **Bloque 5**, con los cuatro bloques hechos. Sustituye a
> las dos vueltas del Bloque 2, cuyo análisis se conserva abajo porque explica
> por qué hoy no hay supervivientes. Un informe regenerado pisa lo que había:
> si se vuelve a lanzar la campaña, esta sección hay que reponerla.

### Por qué el alcance sigue siendo 305 líneas de Python

**Medido**, no supuesto: `harness/alcance.py:134` filtra el alcance con
`if not normalizada.endswith(".py")`. **El mutador solo muerde Python.**

Lo que el Bloque 3 cambió son dos ficheros **JavaScript** de producción
(`js/autoguardado.js`, `js/app.js`) y dos de tests; lo que el Bloque 4 añadió
es un fichero de **tests**. Nada de eso entra en una campaña, así que el
alcance de la feature entera coincide, línea por línea, con el del Bloque 2.
La mutación de JavaScript **no está disponible en este proyecto**: se dice
así, con el motivo, en vez de omitir el dato.

De esas 305 líneas salen solo **3 mutantes** porque casi todo lo cambiado es
docstring y enmiendas fechadas, y el mutador solo muerde operadores y
constantes reales.

### Los tres mutantes, uno a uno

| Mutante | Veredicto |
|---|---|
| `nombrado.py:188` · `normalizar_codigo(uno) == normalizar_codigo(otro)` → `!=` | **muerto** |
| `paso_archivo.py:579` · `if not es_el_mismo_codigo(...)` → `if es_el_mismo_codigo(...)` | **muerto** |
| `paso_archivo.py:142` · `@dataclass(frozen=True)` → `frozen=False` | **muerto** (ver abajo) |

### El único que sobrevivió alguna vez, y por qué se mató en vez de justificarlo

En la **primera** campaña del Bloque 2 (2026-09-22, 13:09 · 3 mutantes, 2
muertos, **1 superviviente**, 86,9 s) sobrevivió el tercero:
`paso_archivo.py:142` `[booleano]` · `@dataclass(frozen=True)` →
`@dataclass(frozen=False)`.

**Por qué ningún test lo cazaba**: `CodigosDelParte` se construye en dos
sitios —`_codigos_guardados` y el borde— y nadie escribía encima del objeto
después, así que quitarle la inmutabilidad no cambiaba ningún resultado
observable. Era una guardia sin nadie que la ejercitara.

**Decisión: test nuevo, no mutante equivalente.** Se descartó justificarlo
porque esa inmutabilidad protege algo real, y es la misma razón que
`DestinoArchivo` ya tiene escrita en su docstring: entre resolver los dos
códigos y componer con ellos la carpeta y el nombre hay varias líneas, y en el
borde una llamada entera de por medio. Si alguien pudiera reescribir un código
por el camino, lo que se cotejó en el punto 1 bis no sería lo que acaba en el
nombre del fichero, y ni el cotejo ni el nombrado estarían protegiendo nada.

El test es
`tests/test_f031_nombrado_persistido.py::test_f031_r11_los_codigos_resueltos_no_se_pueden_reescribir`
(commit `55db9c8`). Desde él, las campañas matan los **3 de 3**: la segunda
vuelta del Bloque 2 (82,7 s) y ésta (78,6 s).

### La línea base, comprobada antes de lanzar esto

Una campaña contra una suite que ya venía roja no mide nada. Antes de lanzarla
se reejecutaron las tres suites **enteras y sin caché**, no se leyó el verde
del arnés:

| Suite | Comando | Resultado |
|---|---|---|
| `api` | `pytest tests -q -p no:cacheprovider` | **3.066 passed, 14 skipped** en 65,58 s |
| `front` | `pytest tests -q -p no:cacheprovider` | **256 passed** en 3,33 s |
| JavaScript | `node --test "tests_js/*.test.js"` | **310 passed, 0 failed** en 819 ms |

