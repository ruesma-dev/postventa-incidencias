<!-- progress/mutacion_F-007.md -->
# F-007 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-007` el 2026-08-20 11:26.

## Alcance

Origen del diff: **rama** (`0705d881d4a1c329006db5fe970c45bcb93c2e75` .. `feature/F-007-front`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-front/dev_server.py` | 188 |
| **Total** | **188** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 12.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-front/dev_server.py:169` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (implementer, 2026-08-20)

> **Por qué ningún test lo caza:** es la **anchura del separador** del rótulo
> que `main()` imprime al arrancar (las tres líneas de `====…`). Ningún test
> afirma nada sobre esa decoración, y no debería: lo que importa de `main()`
> —que configura el handler con `--port`, `--api` y `--root`, que se niega a
> arrancar sin `index.html` devolviendo 1, y que un `Ctrl+C` apaga y devuelve
> 0— sí está cubierto, y todos los mutantes que tocan eso murieron.
>
> **Decisión: mutante equivalente justificado.** Un rótulo de 61 iguales en vez
> de 60 no cambia ni el comportamiento del proxy, ni el código de salida, ni
> una sola respuesta HTTP: cambia cuántos `=` ve el humano en su terminal.
> Fijarlo con un test —capturar el log y afirmar `len(linea) == 60`— compraría
> un mutante muerto a cambio de un test que se rompe la próxima vez que alguien
> ajuste el rótulo, sin haber roto nada. Es el tipo de test que enseña a la
> gente a no fiarse de la suite.
>
> Los tres supervivientes de esta campaña son **la misma mutación repetida** en
> las tres líneas del rótulo (169, 171 y 175), no tres huecos distintos: mismo
> fichero, mismo operador, mismo original y mismo mutado. Por eso este análisis
> es idéntico en los tres — `harness.mutacion` indexa por esa clave y descarta
> el análisis si encuentra dos textos distintos para ella.
>
> Nivel `estandar`: no se exigen cero supervivientes, se exige que estén
> explicados (`CHECKPOINTS.md` C4 bis).

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `services/postventa-front/dev_server.py:171` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (implementer, 2026-08-20)

> **Por qué ningún test lo caza:** es la **anchura del separador** del rótulo
> que `main()` imprime al arrancar (las tres líneas de `====…`). Ningún test
> afirma nada sobre esa decoración, y no debería: lo que importa de `main()`
> —que configura el handler con `--port`, `--api` y `--root`, que se niega a
> arrancar sin `index.html` devolviendo 1, y que un `Ctrl+C` apaga y devuelve
> 0— sí está cubierto, y todos los mutantes que tocan eso murieron.
>
> **Decisión: mutante equivalente justificado.** Un rótulo de 61 iguales en vez
> de 60 no cambia ni el comportamiento del proxy, ni el código de salida, ni
> una sola respuesta HTTP: cambia cuántos `=` ve el humano en su terminal.
> Fijarlo con un test —capturar el log y afirmar `len(linea) == 60`— compraría
> un mutante muerto a cambio de un test que se rompe la próxima vez que alguien
> ajuste el rótulo, sin haber roto nada. Es el tipo de test que enseña a la
> gente a no fiarse de la suite.
>
> Los tres supervivientes de esta campaña son **la misma mutación repetida** en
> las tres líneas del rótulo (169, 171 y 175), no tres huecos distintos: mismo
> fichero, mismo operador, mismo original y mismo mutado. Por eso este análisis
> es idéntico en los tres — `harness.mutacion` indexa por esa clave y descarta
> el análisis si encuentra dos textos distintos para ella.
>
> Nivel `estandar`: no se exigen cero supervivientes, se exige que estén
> explicados (`CHECKPOINTS.md` C4 bis).

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `services/postventa-front/dev_server.py:175` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (implementer, 2026-08-20)

> **Por qué ningún test lo caza:** es la **anchura del separador** del rótulo
> que `main()` imprime al arrancar (las tres líneas de `====…`). Ningún test
> afirma nada sobre esa decoración, y no debería: lo que importa de `main()`
> —que configura el handler con `--port`, `--api` y `--root`, que se niega a
> arrancar sin `index.html` devolviendo 1, y que un `Ctrl+C` apaga y devuelve
> 0— sí está cubierto, y todos los mutantes que tocan eso murieron.
>
> **Decisión: mutante equivalente justificado.** Un rótulo de 61 iguales en vez
> de 60 no cambia ni el comportamiento del proxy, ni el código de salida, ni
> una sola respuesta HTTP: cambia cuántos `=` ve el humano en su terminal.
> Fijarlo con un test —capturar el log y afirmar `len(linea) == 60`— compraría
> un mutante muerto a cambio de un test que se rompe la próxima vez que alguien
> ajuste el rótulo, sin haber roto nada. Es el tipo de test que enseña a la
> gente a no fiarse de la suite.
>
> Los tres supervivientes de esta campaña son **la misma mutación repetida** en
> las tres líneas del rótulo (169, 171 y 175), no tres huecos distintos: mismo
> fichero, mismo operador, mismo original y mismo mutado. Por eso este análisis
> es idéntico en los tres — `harness.mutacion` indexa por esa clave y descarta
> el análisis si encuentra dos textos distintos para ella.
>
> Nivel `estandar`: no se exigen cero supervivientes, se exige que estén
> explicados (`CHECKPOINTS.md` C4 bis).

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

