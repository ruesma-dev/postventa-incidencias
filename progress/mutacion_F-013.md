<!-- progress/mutacion_F-013.md -->
# F-013 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-013 --workers 6` el 2026-09-25 00:49.

## Alcance

Origen del diff: **rama** (`fadb67801bfe82d72c6fa42219e562bc16b4a8fb` .. `feature/F-013-archivo-posventa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/destino_archivo.py` | 403 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 224 |
| `services/postventa-api/config/settings.py` | 76 |
| `services/postventa-api/domain/models/destino_posventa.py` | 563 |
| `services/postventa-api/domain/models/errores.py` | 58 |
| `services/postventa-api/domain/ports/biblioteca.py` | 71 |
| `services/postventa-api/domain/ports/ubicacion.py` | 75 |
| `services/postventa-api/function_app.py` | 43 |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | 49 |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | 155 |
| `services/postventa-api/infrastructure/sigrid/consultas_ubicacion.py` | 155 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 47 |
| `services/postventa-api/infrastructure/sigrid/ubicacion.py` | 270 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 102 |
| **Total** | **2291** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 109 |
| Mutantes evaluados | 109 |
| Muertos | 108 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 2407.1 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/destino_archivo.py:102` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> **Por qué ningún test lo caza**: es un mutante **equivalente**. `_Nivel` es
> una dataclass **privada** del resolutor; sus cuatro instancias (obra,
> incidencias, unidad, firmados) se construyen en línea en la llamada a
> `_Camino.bajar` (`destino_archivo.py:242`, `:253`, `:264`, `:278`) y nadie
> les asigna nada después. Con `frozen=False` el comportamiento observable es
> idéntico: no hay escritura que la congelación impida. (Su vecina
> `DestinoResuelto`, `:89`, sí sale del módulo y su mutante **muere**: lo mata
> `test_f013_t9_el_destino_resuelto_no_se_puede_reescribir`, commit `821b27d`.)
>
> **Decisión**: mutante equivalente justificado; se deja `frozen=True` por
> coherencia con el resto de dataclasses del módulo. Es el mismo superviviente
> de las campañas de los bloques 2, 2-cierre, 3 y 4 y está **aceptado por el
> humano el 2026-09-24** (preguntado si aceptaba la justificación, respondió
> literalmente «si»; nota del líder en `progress/impl_F-013.md`, «Nota del
> líder · superviviente `_Nivel` aceptado»). Es la aceptación escrita que
> exige el nivel `critico` para un superviviente sin test.


## Nota del implementer · T20 (campaña formal, 2026-09-25)

> La cabecera y las tablas de arriba las escribe la herramienta, sin retocar;
> solo se ha completado el análisis del superviviente. Esta nota añade lo que
> la herramienta no dice.

### Comando real y condiciones

- **Comando**: `python -m harness.mutacion --feature F-013 --timeout 900 --workers 6`
  (la cabecera generada no lista `--timeout`). Timeout de 900 s por mutante y
  6 workers en vez de 8, el mismo criterio que desde el cierre del bloque 2:
  aquella campaña, con `init.sh` a la vez, dio 60 timeouts por carga.
- **Sola**: lanzada sobre `HEAD` **`50b9cd2`** con el árbol limpio, el
  2026-09-25 de 00:08:57 a 00:49:15 (40 min 17 s de reloj). `bash
  harness/init.sh` se ejecutó **antes** y había terminado (ENTORNO LISTO);
  durante la campaña no corrió nada más en este repositorio.
- **Salida de la herramienta**: `109 mutantes evaluados, 108 muertos, 1
  supervivientes, 0 timeouts en 2407.1 s`, código de salida **1**, que es lo
  que devuelve cuando hay algún superviviente (`harness/mutacion.py:899`,
  `return 1 if informe.supervivientes else 0`); el único es el aceptado.
- **Coste por mutante**: 2.407,1 s × 6 ÷ 109 = **132,5 s**, muy por debajo
  del timeout de 900 s (ninguno lo agotó).

### Alcance frente al que pide T20

T20 nombra cuatro ficheros; la herramienta **no admite** limitar el alcance
(lo calcula del diff de la rama, `fadb678..feature/F-013-archivo-posventa`) y
mutó los **14** de producción que toca F-013. Los cuatro de T20 están todos
dentro:

| Fichero | Generados | Muertos | Supervivientes |
|---|---|---|---|
| `domain/models/destino_posventa.py` (**objetivo principal**) | 39 | 39 | 0 |
| `application/pipelines/destino_archivo.py` | 25 | 24 | 1 (`_Nivel`, aceptado) |
| `application/pipelines/paso_archivo.py` | 5 | 5 | 0 |
| `infrastructure/sigrid/consultas_ubicacion.py` | 10 | 10 | 0 |
| *Resto del diff* (`graph.py` 14, `ubicacion.py` 8, `sharepoint/fabrica.py` 3, `function_app.py` 2, `archivar.py` 2, `settings.py` 1) | 30 | 30 | 0 |
| `errores.py`, los dos puertos, `sigrid/fabrica.py` | 0 | — | — (sin operadores que mutar) |
| **Total** | **109** | **108** | **1** |

Reparto de los 39 de `destino_posventa.py` por la parte que T20 señala como
objetivo principal: **reglas de parecidas** 11 (`parecidas_de_obra` 4,
`parecidas_de_tramo` 5, `parecidas_de_unidad` 2); **casado por número** 14
(`_casa_con_la_obra` 8, `_casa_con_la_unidad` 5, `numero_de_obra` 1);
`nombre_derivado_de_unidad` 3; `obras_del_mismo_numero` 3; el resto 8
(`carpetas_de_obra`, `_numeros_de_la_unidad`, `nombre_de_obra_nueva`,
`_palabras`, `_sin_marcas` y las tres dataclasses/enumerados). **Los 39,
muertos.**

`unidades_que_casan` y `carpetas_de_unidad` reciben **0** mutantes: sus cuerpos
son una comprensión que delega en `_casa_con_la_unidad`, sin comparaciones,
lógicos, `not`, booleanos ni enteros, que son los únicos operadores de la
herramienta. Como `unidades_que_casan` es objetivo principal de T20, se
cubre con la mutación a mano de abajo.

### Mutación a mano de lo que la herramienta no muta (T20)

Script `mutar_t20.py` en el scratchpad (no se versiona): copia desechable del
servicio (sin `.venv`, `.env` ni cachés), sustitución de un ancla **única**
(comprobada con `assert`), `pytest tests/test_f013_destino_dominio.py
tests/test_f013_resolver_destino.py -x` con el intérprete del servicio, y
restauración byte a byte en un `finally` (comprobada con `assert` al final).
Base en verde antes de mutar y restaurada después. El repositorio no se tocó.

**Primera pasada** (sobre `50b9cd2`): base `380 passed`; **18 generados, 17
muertos, 1 superviviente**:

```
== U4 unidades_que_casan: sin el código de la unidad: SOBREVIVE
   380 passed in 3.64s
```

**Hueco real**: ningún test tenía una unidad que casara con la carpeta **solo
por su código** (regla 1 de §4.3). Con el mutante, R50 contaría solo las que
casan por el nombre: una carpeta compartida entre una unidad por código y otra
por nombre pasaría como única, y una carpeta elegida por el código se quedaría
sin su unidad. No exige tocar producción: test nuevo
`test_f013_r50_la_unidad_que_casa_solo_por_su_codigo_tambien_cuenta`
(`test_f013_destino_dominio.py`), commit **`ea91013`**. En el código real pasa
a la primera (el comportamiento ya existía); con U4 inyectado, **falla**:

```
== U4 unidades_que_casan: sin el código de la unidad: MUERTO
   FAILED tests/test_f013_destino_dominio.py::test_f013_r50_la_unidad_que_casa_solo_por_su_codigo_tambien_cuenta
   1 failed, 234 passed in 2.36s
```

**Segunda pasada** (con el test nuevo): base `381 passed`; **18 generados, 18
muertos, 0 supervivientes**; restaurada `381 passed`.

| # | Mutante | Resultado | Lo caza (primer fallo) |
|---|---|---|---|
| U1 | `unidades_que_casan` sin filtrar | muere | `test_f013_r37_tabla_4_6_los_15_casos_de_la_0677[… VILLA 1 …]` |
| U2 | `unidades_que_casan` con el filtro negado | muere | ídem |
| U3 | `unidades_que_casan` devuelve solo la primera (R50 ciego) | muere | `test_f013_r50_dos_grupos_que_comparten_villa_casan_los_dos` |
| U4 | `unidades_que_casan` sin el código de la unidad | **sobrevivía**; muere tras `ea91013` | `test_f013_r50_la_unidad_que_casa_solo_por_su_codigo_tambien_cuenta` |
| U5 | `unidades_que_casan` sin el nombre de la unidad | muere | `test_f013_r37_tabla_4_6_…` |
| U6 | `unidades_que_casan` con código y nombre cruzados | muere | ídem |
| C1 | `carpetas_de_unidad` sin filtrar | muere | `test_f013_r11_tabla_4_3_casado_de_la_unidad[VILLA 15-False]` |
| C2 | `carpetas_de_unidad` sin el código | muere | `test_f013_r11_la_regla_1_casa_por_el_codigo` |
| C3 | `carpetas_de_unidad` sin el nombre | muere | `test_f013_r11_tabla_4_3_casado_de_la_unidad[VILLA 05-True]` |
| N1 | `nombre_derivado_de_unidad` con `match` en vez de `fullmatch` | muere | `test_f013_r37_fuera_del_patron_no_se_inventa[0677.03VILLA 5.X-…]` |
| N2 | ídem, sin recortar el código | muere | `test_f013_r37_fuera_del_patron_no_se_inventa[  0677.03VILLA 5.  -…]` |
| N3 | ídem, sin rellenar a dos cifras | muere | `test_f013_r37_tabla_4_6_…` |
| N4 | ídem, el `<grupo>` en vez de `<n>` | muere | ídem |
| N5 | ídem, `<n>` literal con sus ceros | muere | ídem |
| N6 | ídem, sin comprobar que la obra del código es la del parte | muere | `test_f013_r37_fuera_del_patron_no_se_inventa[0680.03VILLA 13.-0677-None]` |
| O1 | `obras_del_mismo_numero` devuelve el código y no `obra_ref` | muere | `test_f013_r44_la_0677_medida_es_una_sola_obra` |
| O2 | ídem, código no numérico sin normalizar la fila | muere | `test_f013_r44_codigo_no_numerico_mismo_codigo_normalizado[ ADM -1]` |
| O3 | ídem, sin volver a filtrar lo preseleccionado por el SQL | muere | `test_f013_r44_obras_del_mismo_numero[1677-1]` |

(N6 se escribió mal en la primera versión del script —el ancla dejaba una
sangría de más y el mutante era un `IndentationError`, que «muere» sin decir
nada del test—; corregida el ancla, muere por la aserción.)

**Sin relanzar la campaña del arnés** tras `ea91013`: el commit es solo de
tests, así que el alcance de producción y los 109 mutantes son los mismos; un
test añadido solo puede matar más, y el único superviviente (`_Nivel`) no
depende de él.

### Mutación de orden a mano de los bloques anteriores (punto 7 del reviewer)

Los operadores de la herramienta no mueven sentencias, así que el **orden**
entre colaboradores se demostró a mano en cada bloque. Resumen; el detalle,
con sus trazas, en `progress/impl_F-013.md`, en la sección que indica la
última columna:

| Bloque | Qué se movió | Generados | Muertos | Supervivientes y su cierre | Detalle |
|---|---|---|---|---|---|
| 2 · T9 (resolutor) | 5 de orden (P1–P5: R8, R44, R50 y las dos lecturas de Sigrid) + 21 de lógica (M1–M21); más 6 de los dobles (T8) | 26 (+6) | 23 (+6) | 3 **equivalentes** justificados: P2 (R44 tras construir `_Camino`, que no llama a nadie), M19 (`camino.ruta` = `unir_ruta(base, …)` por construcción), M20 (código de Sigrid = el del parte tras R8, normalizado) | «Bloque 2», §5 |
| 2-cierre · T10 (`paso_archivo.py`) | O0–O11: puerta de estado, cotejo, corte de L1, aviso, traza previa, crear carpetas (antes/después/inverso), log de R47 y R40, traza `error` | 12 | 12 | O0 **sobrevivía** (hueco real): cerrado con test en `668145c` | «Bloque 2 (cierre)», §5 |
| 4 · T13 (composición en `archivar.py`) | O1–O9b de orden de construcción, C1–C6 de configuración, E1–E10 de traducción de errores | 26 | 26 | O9 **sobrevivía** (hueco real, estrategia desconocida): cerrado en `3d9c5b1` | «Bloque 4», §4 |
| 4 · T14 (scripts PowerShell) | M1–M17, incluida la comprobación del repositorio antes de leer Sigrid (M15) | 17 | 17 | M17 **sobrevivía** (hueco real): cerrado en `3bb32e1` | «Bloque 4», §4 |
| 5 · T15 (L1 corta antes del resolutor) | M1–M9 (resolver antes del corte, precarga de la ubicación, orden de construcción, traza previa…) | 10 | 10 | M4b sobrevive **solo** con la selección de T15, a propósito: construir no es leer; lo mata T13 (`test_f013_t13_el_orden_de_construccion_en_posventa`) | «Bloque 5», §3 |

Otras tandas a mano de la feature, fuera del punto 7 pero con el mismo
método: bloque 3 (adaptadores Graph y Sigrid), **21/21**; bloque 6 (T16
arquitectura **11/11**, T17 documentación **10/10**, con M6 cerrado antes del
commit); y la de T20, arriba, **18/18** tras `ea91013`.

### Historia de la campaña del arnés en la rama

| Bloque | Generados | Muertos | Supervivientes |
|---|---|---|---|
| 1 (dos pasadas, `a941acf` → `0783c54`) | 56 → 43 | 47 → 43 | 9 → 0 (6 huecos con test; 3 equivalentes eliminados simplificando el código) |
| 2 | 68 | 66 | 2: `DestinoResuelto` (hueco, test en `821b27d`) y `_Nivel` |
| 2-cierre | 73 | 72 | 1: `_Nivel` |
| 3 | 105 | 101 | 4: tres duraciones de log (huecos, test en `4da38a3`) y `_Nivel` |
| 4 | 109 | 108 | 1: `_Nivel` (ya aceptado) |
| **7 · T20, sobre `50b9cd2`** | **109** | **108** | **1: `_Nivel`, aceptado por el humano el 2026-09-24** |

Las campañas de los bloques 1 a 4 dejaron su informe en el scratchpad para no
adelantar este; este es el único informe de mutación versionado de F-013.

**Veredicto de T20**: cero supervivientes sin justificar. El único de la
herramienta es un equivalente con aceptación escrita del humano; el único de
la mutación a mano (U4) era un hueco real y está cerrado con test.

## Aceptaciones del humano

- `destino_archivo.py:102` (`_Nivel`, `frozen`): equivalente **aceptado el 2026-09-24**.
- Mutación a mano del bloque 2, P2, M19 y M20: equivalentes **aceptados por el humano el 2026-09-25**, preguntado tras la review APROBADA (`progress/review_F-013.md` §5): eligió «Aceptar los tres (Recomendado)». M19 con la
  salvedad del reviewer (base patológica): mejora pendiente H-3, `design.md` §10.
