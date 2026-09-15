<!-- progress/mutacion_F-028.md -->
# F-028 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-028 --workers 1` el 2026-09-16 01:07.

> **NOTA A MANO (2026-09-16, T13), no la escribe el arnés.** Esta campaña se
> lanzó con `--workers 1` y con **un caso deselecionado** mediante un
> `pytest.ini` temporal, ya borrado:
> `tests/test_f010_integracion_expuesto.py::test_f010_r26_dice_la_consecuencia_visible_de_cada_ausencia`.
> Ese caso está **rojo en `HEAD` por un cambio de `docs/INTEGRACION.md`
> (commit `6eb6d33`) ajeno a F-028**, y el evaluador de mutación da un mutante
> por **muerto** cuando la suite falla: con la línea base en rojo, **todos** los
> mutantes del servicio `api` salen «muertos» sin que ningún test los cace. Una
> primera campaña de este encargo dio 39/39 así y **no valía**. Con la
> deselección, la línea base es verde (`2612 passed, 13 skipped, 1 deselected`)
> y estos números sí significan algo. **Mientras ese caso siga rojo, una
> campaña lanzada a secas sobre `api` no vale nada.** Detalle en
> `progress/impl_F-028.md` §44.

## Alcance

Origen del diff: **rama** (`b90c3a4986b94967c9ac1ad48fc742788c154d99` .. `feature/F-028-estado-del-parte`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/constancia.py` | 91 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 22 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 24 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 88 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 14 |
| `services/postventa-api/application/pipelines/paso_persistencia.py` | 58 |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 137 |
| `services/postventa-api/domain/models/errores.py` | 71 |
| `services/postventa-api/domain/models/estado.py` | 412 |
| `services/postventa-api/domain/ports/persistencia.py` | 54 |
| `services/postventa-api/function_app.py` | 115 |
| `services/postventa-api/infrastructure/persistencia/ddl.py` | 80 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 49 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 113 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 169 |
| `services/postventa-api/interface_adapters/api/estado.py` | 356 |
| `services/postventa-api/interface_adapters/api/estado_serializado.py` | 107 |
| `services/postventa-api/interface_adapters/api/parte.py` | 23 |
| **Total** | **1983** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 39 |
| Mutantes evaluados | 39 |
| Muertos | 39 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 948.3 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

