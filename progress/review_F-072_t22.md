<!-- progress/review_F-072_t22.md -->
Revisión de evidencias desde 88adde2 (pasada de evidencias de la review final T22; delta `88adde2..5bd518c`)

# F-072 · Review T22: la campaña de mutación de la feature

- **Veredicto: APROBADO** (APPROVED) en `5bd518c`, con **una condición que no es mía**: la **aceptación
  escrita del humano** de los tres equivalentes (C4 bis, rigor `critico`). Hasta que conste en `progress/`, la
  feature no pasa a `done`. Queda en pie además la condición 3 de `progress/review_F-072.md` (el `init.sh` sin
  caché del líder en el SHA de cierre). Esta pasada **no** lo ejecuta, por encargo.
- **Principal:** `progress/review_F-072.md` (`88adde2`); esta pasada cierra sus condiciones 1 y 2.
- **Rigor:** `critico`, declarado: mutación con la regla del nivel (uno por línea, 60 % en [100, 300], semilla
  20261030), cero supervivientes sin aceptación del humano y RM1–RM7.
- **Delta revisado:** `88adde2..5bd518c` = `tasks.md` y papeleo (`43b472c`), más `progress/mutacion_F-072.{md,json}`
  (`1db3049`, `5bd518c`). `git diff --stat 43b472c HEAD` solo enseña esos dos ficheros. Sin código de producción.

## 1 · Totales recalculados por mi cuenta (cálculo puro)

Guion `scratchpad/t22/recalculo.py`: `alcance_de_feature("F-072", base="6994cb0")` + `generar_mutantes` +
`seleccionar` con `_regla_configurada("F-072")`. No ejecuta la suite ni escribe en disco. Salida real:

```
F-072: 20 fichero(s), 711 línea(s) de producción (origen rama, 6994cb0…..feature/F-072-tipo-reclamacion-sigrid)
TOTAL lineas 711 mutantes 70
nivel critico semilla 20261030 regla ReglaMuestreo(por_linea=True, fraccion=0.6, suelo=100, techo=300, origen='nivel')
candidatos 41 tope 100 elegidos 41
coinciden elegidos con json: True solo mios 0 solo suyos 0
```

Coinciden las 20 filas de «Alcance» y los «Totales». 41 candidatos ≤ suelo 100: campaña completa, como dice
«Muestreo». Mis 41 son, tupla a tupla (fichero, línea, operador, original, mutado), los 41 `evaluados` del
`.json`. Los tres supervivientes existen con ese texto (`importacion.py:604`, `api/importar.py:218`,
`api/plantilla.py:92`, `veracidad`).

## 2 · Checkpoints de mutación (C4 bis)

- [x] **Informe generado por la herramienta**, sin cabecera «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto (base
  rota)» = 0, `fiable: true`, criterio `codigo_1`, **línea base corrida** (1474,7 s, en verde).
- [x] **Totales verificados de forma independiente** (§1).
- [x] **Muertos comprobados, no solo contados.** «Tiempo total» 30 924,4 s (8,6 h), **más de 60 s**: campaña
  **no reejecutada**, por la regla de 60 s. Valen el recálculo puro, RM1–RM7 y la muestra de §3.
- [x] **Coste por mutante:** 30 924,4 × 1 ÷ 41 = 754 s, mucho más de 1 s.
- [x] **RM1.** «SHA de HEAD medido» `43b472c1230d8f6178c16c1bd1cdf6549c679ec3`, completo. De ahí a HEAD solo
  entra el propio informe, nada del alcance. El alcance medido es el que reviso.
- [x] **RM2.** Media 754,3 s frente a base 1474,7 s: ratio 0,51, lejos de 0,1. 41 × 754,3 = 30 926 ≈ 30 924,4.
  Es lo esperable con 38 de 41 muertos bajo `-x`. Workers 1, así que no hay que corregir por W. Timeout fijo
  de 3600 s, sin timeouts.
- [x] **RM3.** Recorridos los 38 muertos: ninguno equivalente. Los dudosos tienen su test: `repr=False→True`
  (`test_f072_importacion.py:242`, `lectura_sigrid.py:188`), `frozen` (`FrozenInstanceError`, `dominio_tipos.py:86`),
  `monotonic() -→+` (`r30_…duracion_y_no_la_hora`), `not valor` (`lectura_sigrid.py:155`, `[0, "", 0]`) y
  `revision.py:858` (`tipos=frozenset()`, `revision_dominio.py:434`).
- [x] **Superviviente reproducido a mano** (lo hizo el implementer con 35 ficheros, y yo con uno, §3).
- [x] **RM5** (§3): demostración ejecutable presente en los tres. Reproduzco **uno**, el 1, que es el único con
  un argumento que no es trivial.
- [x] **RM6.** No aplica: no se quitó ninguna guarda (`1db3049` y `5bd518c` son solo `progress/`).
- [x] **RM7** (§4): los tres del líder más los míos, de un paso, todos muertos por tests de F-072.
- [x] **Análisis completados:** `grep PENDIENTE` da una sola línea, la 118, que es el texto de la plantilla.
- [ ] → **condición:** en `critico`, **cero supervivientes salvo justificación aceptada por escrito por el
  humano**. La justificación es buena (§3), pero la aceptación **no consta** (el propio informe lo dice, línea
  276). No la doy por hecha.
- N/A **Campaña manual:** no la hubo (70 mutantes). N/A **Podados:** selección apagada. N/A **e2e:** la principal.

## 3 · RM5: el superviviente 1 (`domain/models/importacion.py:604`), reproducido

**Mutante aplicado byte a byte** en el árbol (`scratchpad/t22/reproducir.py`, restauración en `finally`):
`if etiqueta_listado is None` → `if not etiqueta_listado`. Corrí 27 ficheros: los `test_f072_*` (sin
alcance ni documentación, que miran el diff) y los de F-036/F-056/F-059/F-060/F-065/F-071 que usan
`validar_filas` o `models.importacion`. Salida real:

```
mutado: b'if not etiqueta_listado'
codigo 0 segundos 308.4
2475 passed, 7 skipped in 306.72s (0:05:06)
restaurado: True
```

**Demostración ejecutable del informe**, extraída tal cual y lanzada con el `.venv`: salida **idéntica, línea
a línea**, a la del informe (líneas 251-263; `etiquetas=['0001', '0002']`, ninguna en blanco, `bool(partial)=True`).

**Además lo comprobé en el código, en quien construye el dato** (el guion solo enseña casos):
- Las dos ramas solo se separan con `etiqueta_listado == ""`. `tasado` devuelve `None` o una opción de
  `casar_con_lista`, que es siempre un elemento de `listados`.
- `_vacia` trata como vacía toda cadena con `not valor.strip()`. Una fórmula sale por error en
  `_texto_tasado`. A `casar_con_lista` solo llega texto no blanco.
- `listados` solo lo fabrica `listas_con_tipos` → `tipos_del_desplegable` → `_con_codigo(nombre, codigo)`
  (`plantilla_incidencias.py:444`), que da el `codigo` o `"<nombre> (<codigo>)"`, nunca `""` si el código no
  está vacío. `leer_tipos_reclamacion` descarta los códigos nulos o en blanco tras `strip()`. Los únicos
  llamantes de producción (`paso_importacion.py:247` y `:328`) pasan por `listas_con_tipos`. El YAML deja
  `listados=()` y rechaza la clave (`plantilla_yaml.py:209-215`, mutante de la 209 muerto).

**Juicio: equivalente.** En los 2 y 3 (leídos, no reproducidos: RM5 pide uno), `tipos` es `None` o un `partial`
de `fuente_de_tipos` (`tipos_reclamacion.py:77`); `function_app.py:1391` y `:1453` no lo pasan.

## 4 · RM7: las puertas de orden, movidas un paso

El líder adelantó `tipos()` **dos** pasos (antes del catálogo). El requisito (R1, R11) es «tras catálogo **y**
ubicaciones», así que bajé la lectura **un solo paso**, entre el catálogo y las ubicaciones, en los cuatro
puntos donde se lee (`scratchpad/t22/rm7.py`, restauración en `finally`). Corrí **solo los tests de F-072**,
sin `-x`. Salida real:

| Punto mutado | Tests | Resultado | Lo caza (de F-072) |
|---|---|---|---|
| `paso_importacion.py:212-213` | `test_f072_importacion.py` | 2 failed / 21 passed | `r11_paso_catalogo_lee_los_tipos_tras_catalogo_y_ubicaciones`, `r11_el_orden_de_las_lecturas_de_la_importacion` |
| `plantilla.py:177-180` | `test_f072_plantilla.py` | 1 failed / 20 passed | `r1_la_plantilla_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones` |
| `revision.py:283-284` (listar) | `revision_http` + `revision_dominio` | 1 failed / 114 passed | `r1_listar_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones` |
| `revision.py:335-336` (editar/aprobar) | `revision_http` + `revision_dominio` | 2 failed / 113 passed | `r1_editar_y_aprobar_leen_los_tipos_una_vez_antes_de_escribir[editar]` y `[aprobar]` |

Los cuatro mueren con tests **de la propia feature**; el cuarto cubre editar/aprobar, que el líder no movió.

## 5 · Prueba de control de los 7 ficheros sin mutantes

`generar_mutantes` sobre el fichero **entero**, sin exclusión de alcance (`scratchpad/t22/control.py`):

| Fichero | Mutantes sin exclusión | En alcance | Lectura |
|---|---|---|---|
| `application/pipelines/paso_importacion.py` | 48 | 0 | cero legítimo (exclusión por alcance) |
| `application/pipelines/plantilla.py` | 6 | 0 | legítimo |
| `domain/models/volcado.py` | 139 | 0 | legítimo |
| `infrastructure/persistencia/sentencias_revision.py` | 21 | 0 | legítimo |
| `infrastructure/sigrid/fabrica.py` | 6 | 0 | legítimo |
| `interface_adapters/api/bandeja.py` | 13 | 0 | legítimo |
| `infrastructure/sigrid/tipos_reclamacion.py` | **0** | 0 | **investigado:** ver abajo |

El último da 0 sin exclusión: su AST no tiene `Compare`, `BinOp`, `BoolOp`, `UnaryOp`, `If`, `IfExp` ni
`AugAssign`, y sus 5 `Constant` son cadenas (un método de dos llamadas). Control positivo: en el vecino
`ubicaciones_validas.py` el generador saca 4. **Cero legítimo.** Las siete declaraciones casan con el diff.

## 6 · Observaciones (no bloquean)

- **O1.** La cabecera del informe (línea 4) omite `--sin-seleccion --timeout 3600`, que sí reflejan sus filas.
  Propuesta para `arnes-base`: que la cabecera copie la orden entera.
- **O2.** `progress/impl_F-072.md` no tiene la fila «Evidencias» de la campaña de la feature (70/41/38/3, workers
  1, 8,6 h). El informe de la herramienta trae el dato, pero C4 bis lo pide en el informe del implementer.
  Hay que añadirla antes de T24 (papeleo).

## 7 · Lo que falta para cerrar

1. **Aceptación escrita del humano** de los tres equivalentes, en `progress/` (condición de este APROBADO).
2. `ARNES_SIN_CACHE=1 bash harness/init.sh` del líder en verde en el SHA de cierre. 3. O2, antes de T24.

Árbol: `git status --short` limpio tras §3 y tras §4.
