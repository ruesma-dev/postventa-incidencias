<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010` el 2026-08-20 16:05.

## Alcance

Origen del diff: **rama** (`0705d881d4a1c329006db5fe970c45bcb93c2e75` .. `feature/F-010-despliegue`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 10 |
| `services/postventa-api/function_app.py` | 55 |
| `services/postventa-front/dev_server.py` | 188 |
| **Total** | **253** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 14.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-front/dev_server.py:169` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (completado por el implementer, 2026-08-20)

> **Por qué ningún test lo caza**: es el ancho del separador decorativo del
> banner que `dev_server.py` imprime al arrancar (`log.info("=" * 60)`).
> Ninguna prueba mira cuántos signos igual lleva esa línea, y no debería
> mirarlo: un test que fijara el ancho de un adorno se rompería en cada
> retoque de la salida y no protegería nada.
>
> **Decisión**: **mutante equivalente**. Cambiar 60 por 61 no altera ningún
> comportamiento observable —ni un código de respuesta, ni una ruta, ni un
> byte que viaje al navegador—: solo la anchura de una línea decorativa en el
> log de arranque del servidor de desarrollo local, que además **no se
> despliega** (`desplegar_front.ps1` lo excluye de la copia que sube). No se
> añade test.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `services/postventa-front/dev_server.py:171` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (completado por el implementer, 2026-08-20)

> **Por qué ningún test lo caza**: es el ancho del separador decorativo del
> banner que `dev_server.py` imprime al arrancar (`log.info("=" * 60)`).
> Ninguna prueba mira cuántos signos igual lleva esa línea, y no debería
> mirarlo: un test que fijara el ancho de un adorno se rompería en cada
> retoque de la salida y no protegería nada.
>
> **Decisión**: **mutante equivalente**. Cambiar 60 por 61 no altera ningún
> comportamiento observable —ni un código de respuesta, ni una ruta, ni un
> byte que viaje al navegador—: solo la anchura de una línea decorativa en el
> log de arranque del servidor de desarrollo local, que además **no se
> despliega** (`desplegar_front.ps1` lo excluye de la copia que sube). No se
> añade test.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `services/postventa-front/dev_server.py:175` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (completado por el implementer, 2026-08-20)

> **Por qué ningún test lo caza**: es el ancho del separador decorativo del
> banner que `dev_server.py` imprime al arrancar (`log.info("=" * 60)`).
> Ninguna prueba mira cuántos signos igual lleva esa línea, y no debería
> mirarlo: un test que fijara el ancho de un adorno se rompería en cada
> retoque de la salida y no protegería nada.
>
> **Decisión**: **mutante equivalente**. Cambiar 60 por 61 no altera ningún
> comportamiento observable —ni un código de respuesta, ni una ruta, ni un
> byte que viaje al navegador—: solo la anchura de una línea decorativa en el
> log de arranque del servidor de desarrollo local, que además **no se
> despliega** (`desplegar_front.ps1` lo excluye de la copia que sube). No se
> añade test.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

