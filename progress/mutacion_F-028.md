<!-- progress/mutacion_F-028.md -->
# F-028 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-028 --workers 1` el 2026-09-16 01:41.

> **NOTA A MANO (2026-09-16, T14), no la escribe el arnés.** Dos cosas que hay
> que saber para leer los números de abajo:
>
> 1. **La línea base de esta campaña es verde, y sin deseleccionar nada.** El
>    caso de F-010 que obligó a la deselección en T13 lo arregló el líder
>    (`2670936`). Se comprobó **antes** de lanzarla, con `bash harness/init.sh`
>    en verde y con la suite del servicio entera: `2619 passed, 3 skipped, 0
>    failed`. Sin eso los 39/39 no significarían nada: el evaluador da un
>    mutante por muerto cuando la suite falla, así que con la base en rojo
>    **todos** salen «muertos» sin que ningún test los cace.
> 2. **La campaña no generó ni un mutante de lo que toca T14.**
>    `interface_adapters/api/parte.py` (57 líneas) y
>    `application/pipelines/paso_persistencia.py` (74) están en alcance y no
>    produjeron ninguno: lo que T14 cambia son llamadas, sin comparaciones, sin
>    literales y sin operadores, que es lo único que este mutador reescribe. Es
>    el mismo hueco que ya observaron los bloques 3 (§23.1) y 4 (§32.1). Los
>    mutantes de T14 se han hecho **a mano**, 6 de 6 muertos, y están en
>    `progress/impl_F-028.md` §54.

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
| `services/postventa-api/interface_adapters/api/parte.py` | 57 |
| **Total** | **2033** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 39 |
| Mutantes evaluados | 39 |
| Muertos | 39 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 1000.5 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

