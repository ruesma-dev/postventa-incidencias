<!-- progress/mutacion_F-031.md -->
# F-031 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-031 --workers 3` el 2026-09-22 13:12.

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
| Tiempo total | 82.7 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Nota del implementer · esta es la segunda vuelta

> Campaña del **Bloque 2 (backend)** de F-031. La T16 de `tasks.md` es la de
> la feature entera y sigue pendiente: se lanzará con el front hecho, porque
> el alcance del diff cambiará.

La **primera** campaña, el 2026-09-22 a las 13:09, dio **3 mutantes, 2
muertos, 1 superviviente**, en 86,9 s. El superviviente era:

- `services/postventa-api/application/pipelines/paso_archivo.py:142`
  `[booleano]` · `@dataclass(frozen=True)` → `@dataclass(frozen=False)`.

**Por qué ningún test lo cazaba**: `CodigosDelParte` se construye en dos
sitios —`_codigos_guardados` y el borde— y nadie escribe encima del objeto
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
(commit `55db9c8`). Con él, la segunda campaña —la de arriba— mata los **3 de
3**.

