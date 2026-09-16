<!-- progress/mutacion_F-028.md -->
# F-028 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-028 --workers 8` el 2026-09-16 02:07.

> **NOTA A MANO (2026-09-16, T15), no la escribe el arnés.** Tres cosas que hay
> que saber para leer los números de abajo:
>
> 1. **La línea base de esta campaña es verde, y sin deseleccionar nada.** Se
>    comprobó **antes** de lanzarla, con `bash harness/init.sh` en verde y con la
>    suite del servicio entera: `2528 passed, 3 skipped, 0 failed`. Sin eso los
>    31/31 no significarían nada: el evaluador da un mutante por muerto cuando la
>    suite falla, así que con la base en rojo **todos** salen «muertos» sin que
>    ningún test los cace.
> 2. **La campaña no puede medir T15, porque T15 es una RETIRADA.** Este mutador
>    muta código que existe; T15 casi solo borra. De los 31 mutantes, **cero**
>    caen en lo que T15 hace. `domain/models/aprobacion.py` entra en alcance con
>    67 líneas y no produce ninguno: lo que queda ahí es un `sha256` y un
>    `if texto is None`, y el mutador no reescribe comparaciones `is`. Presentar
>    «31/31 muertos» como evidencia de T15 sería el número que tranquiliza sin
>    medir nada.
> 3. **Los mutantes de T15 se han hecho a mano, y son del revés**: reponer lo que
>    se fue (`admite_circuito`, `upsert_aprobacion`, la ruta `aprobar`, la
>    revocación de `guardar_validacion`) o llevarse lo que tenía que quedarse
>    (`sql/10_aprobaciones.sql`, `_normalizar`, `huella_de_veredicto`). **10 de
>    10 muertos**, con la tabla en `progress/impl_F-028.md` §65.2.
>
> El alcance baja de 2.033 a 2.013 líneas y los mutantes de 39 a 31 **porque el
> código ha menguado**, no porque la campaña sea más floja.

## Alcance

Origen del diff: **rama** (`b90c3a4986b94967c9ac1ad48fc742788c154d99` .. `feature/F-028-estado-del-parte`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/constancia.py` | 91 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 22 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 24 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 88 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 14 |
| `services/postventa-api/application/pipelines/paso_persistencia.py` | 74 |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 137 |
| `services/postventa-api/domain/models/aprobacion.py` | 67 |
| `services/postventa-api/domain/models/errores.py` | 71 |
| `services/postventa-api/domain/models/estado.py` | 412 |
| `services/postventa-api/domain/ports/persistencia.py` | 44 |
| `services/postventa-api/function_app.py` | 72 |
| `services/postventa-api/infrastructure/persistencia/ddl.py` | 80 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 34 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 123 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 144 |
| `services/postventa-api/interface_adapters/api/estado.py` | 356 |
| `services/postventa-api/interface_adapters/api/estado_serializado.py` | 107 |
| `services/postventa-api/interface_adapters/api/parte.py` | 53 |
| **Total** | **2013** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 31 |
| Mutantes evaluados | 31 |
| Muertos | 31 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 158.3 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

