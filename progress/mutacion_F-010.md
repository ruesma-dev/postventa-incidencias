<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010` el 2026-08-20 15:21.

## Alcance

Origen del diff: **rama** (`0705d881d4a1c329006db5fe970c45bcb93c2e75` .. `feature/F-010-despliegue`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/function_app.py` | 55 |
| `services/postventa-front/dev_server.py` | 188 |
| **Total** | **243** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 11.1 s |
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

## Nota de alcance de esta campaña (F-010)

Los dos ficheros del alcance entran por el punto de partida del diff de rama,
no porque F-010 los haya reescrito:

- **`function_app.py`**: F-010 solo le ha tocado **la cabecera del módulo**
  (R32). El `auth_level` no cambia y no hay ni una línea de comportamiento
  nueva: por eso no ha generado ningún mutante.
- **`dev_server.py`**: F-010 **no lo toca**. Aparece porque el punto de
  partida del diff de rama es anterior a que se cerrara F-007.

Lo que F-010 entrega de verdad —cinco scripts de PowerShell, un cambio en JS y
documentación— **queda fuera de lo que la campaña sabe mutar**: la herramienta
solo muta `.py`. La disciplina de esa parte la sostienen los tests de contrato
de la fase 1 (`test_f010_scripts_infra.py`), `test_f010_tarjeta_portal.py`,
`test_f010_endpoints_protegidos.py`, `test_config_timeout.test.js` y la fase
RED de T5, cuya traza está en `progress/impl_F-010.md`.

## AVISO · la campaña deja bytecode envenenado en `__pycache__`

Encontrado al ejecutarla en esta feature, y **no es específico de F-010**: le
va a pasar a cualquiera.

**Qué pasa.** La campaña modifica el `.py` en el sitio y lo restaura al
terminar. Muchas mutaciones **conservan el tamaño exacto** del fichero
(`==` → `!=`, `60` → `61`), y la fecha queda dentro de la granularidad que
Python usa para invalidar. Resultado: el `.pyc` de `__pycache__` sigue
pareciendo válido y **contiene el mutante**, no el código bueno.

**Dos consecuencias, las dos vistas hoy:**

1. **La suite se rompe en el árbol limpio.** El mutante
   `if __name__ != "__main__":` sobrevivió en el `.pyc` de `dev_server.py`, así
   que importarlo ejecutaba `main()` durante la recolección de `pytest`, y el
   `argparse` del servidor mataba la sesión entera con `SystemExit: 2`:

   ```
   usage: __main__.py [-h] [--port PORT] [--api API] [--root ROOT]
   __main__.py: error: unrecognized arguments: tests/ -q
   INTERNALERROR> ...
   [KO] servicio front (services/postventa-front): pytest en rojo
   ```

   Comprobado desensamblando el `.pyc`: `COMPARE_OP 55 (!=)` sobre `__name__`,
   con el fuente diciendo `==`.

2. **Los resultados de la campaña dejan de ser fiables.** Con la caché sucia,
   dos ejecuciones seguidas dieron **0 supervivientes**; con
   `__pycache__` borrada, la misma campaña da **3**, que es el número de la
   primera ejecución del día. El falso negativo va en la dirección peligrosa:
   dice que todo está cazado cuando no lo está.

**Cómo se trabaja con esto hasta que se arregle**: borrar la caché **antes y
después** de cada campaña.

```
find services -name "__pycache__" -type d -prune -exec rm -rf {} +
```

**Los números de este informe se han obtenido con la caché limpia.**

Esto es un fallo del arnés genérico, no de este proyecto: la regla de
propagación de `CLAUDE.md` pide llevarlo a `arnes-base`, y esa es **decisión
del humano**, no del implementer. Queda anotado aquí y en
`progress/impl_F-010.md`.
