<!-- progress/mutacion_F-053.md -->
# F-053 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-053 --base 349ba06 --workers 5` el 2026-10-06 16:18.

## Alcance

Origen del diff: **rama** (`349ba06f3d496aa6202d70a83c1ac43bd9bfd8e0` .. `feature/F-053-datos-para-el-portal`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/equivalencias.py` | 18 |
| `services/postventa-api/domain/models/equivalencias.py` | 29 |
| `services/postventa-api/interface_adapters/api/equivalencias.py` | 10 |
| `services/postventa-api/interface_adapters/api/importar.py` | 22 |
| **Total** | **79** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 5 |
| Mutantes evaluados | 5 |
| Muertos | 2 |
| Supervivientes | 0 |
| Timeouts | 3 |
| Timeouts repasados en serie | 4 — 1 con veredicto tras el repaso, 3 en timeout todavía |
| Tiempo total | 4181.2 s |
| Workers | 5 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `services/postventa-api/domain/models/equivalencias.py:484` services/postventa-api/domain/models/equivalencias.py:484 [comparacion] if decision.decision == DISTINTO and par[0] in dados and par[1] in dados -> if decision.decision != DISTINTO and par[0] in dados and par[1] in dados
- `services/postventa-api/domain/models/equivalencias.py:484` services/postventa-api/domain/models/equivalencias.py:484 [entero] if decision.decision == DISTINTO and par[0] in dados and par[1] in dados -> if decision.decision == DISTINTO and par[1] in dados and par[1] in dados
- `services/postventa-api/domain/models/equivalencias.py:484` services/postventa-api/domain/models/equivalencias.py:484 [logico] if decision.decision == DISTINTO and par[0] in dados and par[1] in dados -> if decision.decision == DISTINTO and par[0] in dados or par[1] in dados


## Análisis del implementer (2026-10-06)

Comando lanzado: `python -m harness.mutacion --feature F-053 --base 349ba06 --timeout 900`
(la herramienta lo reescribe en la cabecera con `--workers 5`, los que usó).

**Resumen: 5 generados, 0 supervivientes, 2 muertos en la campaña y 3 en
`timeout`, los tres muertos al ejecutarlos contra los tests de F-053 (abajo).**
Además, 13 mutantes a mano (los «previsibles» de `design.md` §7 que la
herramienta no genera): los 13, muertos.

### Los tres `timeout`: no son cuelgues, son el `-x` de la suite completa en una máquina cargada

Los cinco mutantes caen en la misma línea, `domain/models/equivalencias.py:484`
(el filtro de `pares_distintos`). Cada evaluación lanza **la suite entera** con
`-x`, y los tests que los cazan (`test_f053_*`) van muy al final por orden
alfabético: antes hay que pasar ~6.600 tests. Durante la campaña la máquina
corría a la vez otra campaña de mutación de otro repositorio (4 workers), la
suite de otro proyecto y un `init.sh` de este repositorio que no era de este
encargo; el «repaso en serie» es en serie *dentro* de esta campaña, no en una
máquina libre. Por eso el repaso no los saca del `timeout` (900 s).

Comprobación directa: cada mutante aplicado en un worktree temporal (en
`HEAD` `a43623e`, el mismo código de producción que la campaña) y
`.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f053_propuestas_distintos.py tests/test_f036_catalogos_http.py -q --tb=no`
desde `services/postventa-api`. Sin mutar: `152 passed in 40.98s`.

| Mutante (línea 484) | Resultado | Tests que lo matan (ejemplos) |
|---|---|---|
| `==` → `!=` (comparación) | **muerto**: `25 failed, 127 passed in 19.83s` | `test_f053_r9_un_par_decidido_mismo_no_sale`, `test_f053_r10_*`, `test_f053_r14_con_solo_decisiones_mismo_*` |
| `par[0]` → `par[1]` (entero) | **muerto**: `1 failed, 151 passed in 21.38s` | `test_f053_r9_un_par_con_algun_codigo_fuera_de_la_obra_no_sale[a_fuera]` |
| 2.º `and` → `or` (lógico) | **muerto**: `10 failed, 142 passed in 20.10s` | `…_fuera_de_la_obra_no_sale[b_fuera]` y `[a_fuera]`, `test_f053_r10_distinto_y_despues_mismo_no_sale` |

### Por familias (las tres de la línea 484, completas)

- **Comparación** (1 mutante, `== DISTINTO`): muerto. Se añadió a mano su
  pariente `DISTINTO` → `MISMO` (D2): muerto, 25 fallos.
- **Índice del par** (2 mutantes): `par[1]` → `par[2]`, muerto en la campaña
  (`IndexError`); `par[0]` → `par[1]`, muerto por **un solo** test, el caso
  `a_fuera` de R9 (el código `a` fuera de la obra y el `b` dentro). Es el test
  que existe para eso: no es equivalente y está cubierto. No hace falta test
  nuevo.
- **Lógico** (2 mutantes, los dos `and`): el 1.º `and` → `or`, muerto en el
  repaso; el 2.º, muerto por los casos `a_fuera`/`b_fuera` y por R10.

### Mutantes a mano (lo que la herramienta no genera)

La herramienta solo muta comparaciones, aritmética, `and`/`or`, `not` y
literales enteros/booleanos: en `importar.py` y en los dos bordes de
`oficio.distintos` no genera **ninguno** (`is None`, llamadas y cadenas no son
de su repertorio). Se aplicaron a mano en el mismo worktree temporal, cada uno
contra su par de ficheros de test (importación:
`tests/test_f053_importado_at_utc.py tests/test_f036_importar_http.py`, 75 tests;
oficios: los tres de arriba, 152 tests).

| # | Fichero | Mutante | Resultado |
|---|---|---|---|
| I1 | `importar.py` | `_instante_utc(contexto.ahora)` en vez del resultado | muerto, `4 failed, 71 passed` |
| I2 | `importar.py` | `.isoformat()` sin `timespec="microseconds"` | muerto, `3 failed, 72 passed` |
| I3 | `importar.py` | sin `astimezone(UTC)` | muerto, `2 failed, 73 passed` |
| I4 | `importar.py` | `is None` → `is not None` | muerto, `11 failed, 64 passed` |
| I5 | `importar.py` | sin la rama sin zona (`return None`) | muerto, `1 failed, 74 passed` (R5) |
| I6 | `importar.py` | sin la clave `importado_at_utc` | muerto, `13 failed, 62 passed` |
| D1 | `domain/models/equivalencias.py` | `sorted(` → `list(` | muerto, `2 failed, 150 passed` (R12) |
| D2 | `domain/models/equivalencias.py` | `DISTINTO` → `MISMO` | muerto, `25 failed, 127 passed` |
| D3 | `domain/models/equivalencias.py` | `frozenset(codigos)` → `frozenset()` | muerto, `21 failed, 131 passed` |
| E1 | `interface_adapters/api/equivalencias.py` | `codigo_a`/`codigo_b` cruzados | muerto, `7 failed, 145 passed` |
| E2 | `interface_adapters/api/equivalencias.py` | `distintos` siempre `[]` | muerto, `7 failed, 145 passed` |
| A1 | `application/pipelines/equivalencias.py` | `Catalogo.OFICIO` → `Catalogo.PROVEEDOR` | muerto, `8 failed, 144 passed` |
| A2 | `application/pipelines/equivalencias.py` | `pares_distintos(..., (), ...)` sin las decisiones | muerto, `8 failed, 144 passed` |

(13 mutantes: I1–I6, D1–D3, E1–E2 y A1–A2. D2 es además el pariente de la
familia de comparación citado arriba.)

### Veredicto

**Cero supervivientes.** Los tres `timeout` son mutantes que los tests de F-053
matan en ~20 s; el `timeout` sale del coste de llegar a esos tests con la suite
completa y `-x` en una máquina compartida, no de un cuelgue del mutante. Nada
que justificar como equivalente y ningún test nuevo necesario. Lo decide el
reviewer/humano: si se quiere el veredicto `muerto` en la tabla de la propia
herramienta, basta relanzar la campaña con la máquina libre.
