<!-- progress/mutacion_F-036_bloque4.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base 72dce57 --workers 6` el 2026-09-30 00:27.

## Alcance

Origen del diff: **rama** (`72dce5738155070a07c4dfb82c944babf0c13cff` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/catalogo_obra.py` | 160 |
| `services/postventa-api/domain/ports/catalogo_obra.py` | 110 |
| `services/postventa-api/infrastructure/sigrid/catalogo_obra.py` | 270 |
| `services/postventa-api/infrastructure/sigrid/consultas_catalogo.py` | 144 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 43 |
| **Total** | **727** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 29 |
| Mutantes evaluados | 29 |
| Muertos | 29 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 807.2 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

