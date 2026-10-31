<!-- progress/mutacion_F-040.md -->
# F-040 · Mutación a mano del panel de volcado (T3, Bloque 1)

Implementer, 2026-10-31. Rama `feature/F-040-volcado-sigrid`, base fija `f97ec6e`.

## Por qué a mano

El código de producción de este bloque es JavaScript (`js/volcado.js`, `js/api.js`, `js/revision.js`) y HTML.
`harness.mutacion` solo muta `.py`. Lanzada igualmente, por encargo:

```
$ python -m harness.mutacion --feature F-040 --base f97ec6e --salida <scratchpad>
F-040: 0 fichero(s), 0 línea(s) de producción (origen rama, f97ec6e..feature/F-040-volcado-sigrid)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
```

Es correcto que salgan 0: los únicos `.py` que cambian desde `f97ec6e` son dos tests
(`tests/test_f038_front.py`, `tests/test_f040_front.py`), que la herramienta no muta.

## Método

Un guion (fuera del repositorio) aplica cada mutante como una sustitución de texto que aparece **una sola vez**
en el fichero, lanza `node --test tests_js/volcado.test.js tests_js/api.test.js` (con `--test-timeout=30000` y
240 s de tope para la suite), anota si muere y qué test lo mata, y restaura el fichero byte a byte. Al acabar,
`git status` limpio. Las familias son las de `tasks.md` T3, más agrupar la sincronización y el resultado.

**Primera pasada: 82 mutantes aplicables (1 no aplica), 75 muertos, 7 vivos.** Para seis de los vivos se
escribieron tests nuevos (al final de `tests_js/volcado.test.js`, sección «T3 · tests añadidos por la mutación
a mano») y se volvieron a lanzar: **muertos**. Queda **un vivo, V3, equivalente** (abajo).

## Resultado final

| Métrica | Valor |
|---|---|
| Mutantes aplicados | 82 (O12 no aplica: su texto no existe; lo cubre O13) |
| Muertos en la primera pasada | 75 |
| Muertos tras los tests nuevos | 6 (O5, O14, V5, C6, C7, G2) |
| Vivos | 1, V3, **equivalente** (pendiente de aceptación escrita del humano) |


## O · El orden de «Registrar» (sincronizar → enseñar → ensayar → volcar) y las guardas de los clics

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| O1 | `registrar()` sin la guarda `volcadoPuedeRegistrar()` | muerto (1 tests) | f040 R56, R55: con una serie en marcha, ni registrar, ni ensayar, ni volcar; y la guarda lo sabe |
| O2 | cargar la obra también registra (sincroniza sin clic) | muerto (25 tests) | f040 R50, R56: cargar la obra pide GET /api/volcado (solo lee) y nada más; el panel enseña sus recuentos |
| O3 | tras sincronizar, ensaya solo (sin clic) | muerto (7 tests) | f040 R53.5: sin idempotentes, tras ensayar no se relee nada |
| O4 | una sincronización fallida deja la fase en `sincronizado` | muerto (7 tests) | f040 R60: con la sincronización en 400 peticion_invalida, el panel para ahí: ni ensaya ni deja ensayar, y lo dice |
| O5 | «Registrar» no vacía `ensayos` | vivo → **muerto** con test nuevo | f040 R53.6 (T3, O5): «Volver a registrar» tras un ensayo sin volcar tira el ensayo: ya no se puede volcar |
| O6 | «Registrar» no vacía `vistaEnsayo` ni `resultado` | muerto (1 tests) | f040 R53.6: «Volver a registrar» repite desde la sincronización y limpia el ensayo y el resultado |
| O7 | se puede registrar con una petición en vuelo | muerto (2 tests) | f040 R56, R55: con una serie en marcha, ni registrar, ni ensayar, ni volcar; y la guarda lo sabe |
| O8 | el botón dice siempre «Registrar» (nunca «Volver a registrar») | muerto (15 tests) | f040 R53.2: un volcado con 200 con un sin_respuesta para: no manda el siguiente, enseña qué quedó y relee |
| O9 | volver a cargar la MISMA obra pone el panel a cero | muerto (14 tests) | f040 R50: cargar otra obra deja el panel a cero; volver a leer la misma no borra lo ensayado |
| O10 | `ensayar()` sin la guarda `volcadoPuedeEnsayar()` | muerto (9 tests) | f040 R56, R55: con una serie en marcha, ni registrar, ni ensayar, ni volcar; y la guarda lo sabe |
| O11 | la serie de ensayos no para en el primer fallo | muerto (2 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| O12 | (no aplica: el texto buscado no existe; sustituido por O13) | no aplica | — |
| O13 | relee tras ensayar justo al revés (sin idempotentes sí, con ellos no) | muerto (3 tests) | f040 R53.5: sin idempotentes, tras ensayar no se relee nada |
| O14 | `pedirVolcado()` sin la guarda `volcadoPuedeVolcar()` | vivo → **muerto** con test nuevo | f040 R52 (T3, O14): el primer clic de volcar no abre la confirmación si no se puede volcar |
| O15 | `volcar()` sin exigir el primer clic (`confirmando`) | muerto (1 tests) | f040 R52, D-12: volcar pide un segundo clic y teclear N; sin eso no sale nada |
| O16 | `volcar()` sin exigir el número tecleado | muerto (1 tests) | f040 R52, D-12: volcar pide un segundo clic y teclear N; sin eso no sale nada |
| O17 | `volcar()` sin exigir `volcadoPuedeVolcar()` | muerto (1 tests) | f040 R52: con el ensayo ya caducado al confirmar, no sale nada |
| O18 | tras volcar no se relee la bandeja | muerto (8 tests) | f040 R52, R53: con la confirmación, un volcado por ensayo con previstos, de uno en uno y en su orden |
| O19 | la guarda de salida no pregunta con ensayos en marcha | muerto (3 tests) | f040 R55: hayVolcadoEnMarcha solo con una serie de ensayos o de volcados en marcha; ilegible, no |
| O20 | la guarda de salida no pregunta con volcados en marcha | muerto (2 tests) | f040 R55: hayVolcadoEnMarcha solo con una serie de ensayos o de volcados en marcha; ilegible, no |

## E · `paraEnsayar`, `puedeEnsayar`, `conflictos_confirmados` y la guarda de F-065

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| E1 | `paraEnsayar` también manda lo que ya existe | muerto (5 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| E2 | `paraEnsayar` manda lo que choca sin casilla posible (veredicto desconocido) | muerto (1 tests) | f040 R61: un veredicto desconocido va a choca SIN casilla (no se puede incluir) |
| E3 | `paraEnsayar` manda lo que choca aunque no esté marcado | muerto (8 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| E4 | `paraEnsayar` no manda lo que va | muerto (30 tests) | f040 R50: cargar otra obra deja el panel a cero; volver a leer la misma no borra lo ensayado |
| E5 | una casilla vale con cualquier valor verdadero, no solo `true` | muerto (1 tests) | f040 R62, P-2: lo que choca solo entra con SU casilla, por incidencia, en su sitio del orden |
| E6 | `puedeEnsayar` sin exigir la fase `sincronizado` | muerto (1 tests) | f040 R60, R56: puedeEnsayar pide sincronización en 200, algo que ensayar y nada en vuelo |
| E7 | `puedeEnsayar` con una petición en vuelo | muerto (1 tests) | f040 R60, R56: puedeEnsayar pide sincronización en 200, algo que ensayar y nada en vuelo |
| E8 | `puedeEnsayar` sin nada que ensayar | muerto (1 tests) | f040 R60, R56: puedeEnsayar pide sincronización en 200, algo que ensayar y nada en vuelo |
| E9 | `volcadoPuedeEnsayar` sin exigir la sesión completa | muerto (1 tests) | f040 R56: sin la sesión completa (oid y correo) no se ensaya ni se vuelca |
| E10 | `confirmadosDelTrozo` lleva las no marcadas | muerto (1 tests) | f040 R62: confirmadosDelTrozo lleva las incluidas de ESE trozo, con TODOS sus códigos |
| E11 | `conflictos_confirmados` vacío viaja en el cuerpo | muerto (2 tests) | f040 R51, R62: cuerpoDeEnsayo es exactamente el de F-059, sin confirmado, y conflictos_confirmados solo si hay |
| E12 | `conflictos_confirmados` de toda la serie, no del trozo | muerto (1 tests) | f040 R62: el ensayo lleva lo que va y lo incluido, por trozos de partes_por_llamada, con conflictos_confirmados del trozo |
| E13 | la guarda no marca «cambió» un choque con otro código | muerto (1 tests) | f040 R62: excluidasDeLaGuarda junta duplicada_en_sigrid y conflicto_sin_confirmar y marca lo que cambió desde la sincronización |

## V · `puedeVolcar`, `caducado`, `siguientePaso` y la cuenta atrás

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| V1 | `puedeVolcar` con una petición en vuelo | muerto (2 tests) | f040 R52, R56: puedeVolcar con previstos, todos los ensayos en 200, sin caducar y sin nada en vuelo |
| V2 | `puedeVolcar` con algún ensayo fallido | muerto (2 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| V3 | `puedeVolcar` sin el «ningún ensayo con previstos → false» | **vivo (equivalente)** | ninguno: ver abajo |
| V4 | `puedeVolcar` sin mirar la caducidad | muerto (3 tests) | f040 R52, R56: puedeVolcar con previstos, todos los ensayos en 200, sin caducar y sin nada en vuelo |
| V5 | `volcadoPuedeVolcar` sin exigir la sesión completa | vivo → **muerto** con test nuevo | f040 R56 (T3, V5): sin la sesión completa no se puede volcar aunque haya ensayo |
| V6 | `caducado` en el instante exacto de caducar dice que no | muerto (3 tests) | f040 R52, R56: puedeVolcar con previstos, todos los ensayos en 200, sin caducar y sin nada en vuelo |
| V7 | sin caducidad legible, no está caducado | muerto (1 tests) | f040 R53.1: caducado mira el caduca_at_utc del ensayo de ese trozo |
| V8 | la caducidad de la serie es la más TARDÍA | muerto (2 tests) | f040 R51: un ensayo 200 sin ensayo_id es un trozo sin previstos, no un fallo; la caducidad es la más temprana de los que tienen |
| V9 | un trozo caducado se manda igual | muerto (1 tests) | f040 R53.1: con el ensayo de un trozo caducado, ese trozo no se manda y el panel para |
| V10 | un `sin_respuesta` no para la serie (hacen falta dos) | muerto (2 tests) | f040 R53.2: un volcado 200 con algún sin_respuesta para y lo dice en duda |
| V11 | un error sin respuesta del servicio (http null) no para | muerto (5 tests) | f040 R51, R53: siguientePaso sigue con un 200 limpio y para con cualquier otra cosa |
| V12 | un volcado 200 con `sin_respuesta` no para | muerto (1 tests) | f040 R53.2: un volcado con 200 con un sin_respuesta para: no manda el siguiente, enseña qué quedó y relee |
| V13 | un volcado con error no corta el bucle | muerto (6 tests) | f040 R53.2: un volcado con 400 peticion_invalida para: no manda el siguiente, enseña qué quedó y relee |
| V14 | la cuenta atrás no dice «caducado» en el instante exacto | muerto (1 tests) | f040 R52: la cuenta atrás hasta la caducidad más temprana, en minutos y segundos |

## C · El `confirmado: true` y la confirmación tecleada

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| C1 | `confirmado: false` | muerto (2 tests) | f040 R52, R53: con la confirmación, un volcado por ensayo con previstos, de uno en uno y en su orden |
| C2 | `confirmado: "true"` (texto, no booleano) | muerto (2 tests) | f040 R52, R53: con la confirmación, un volcado por ensayo con previstos, de uno en uno y en su orden |
| C3 | `confirmacionValida` sin el patrón de entero positivo | muerto (1 tests) | f040 R52, D-12: confirmacionValida solo con el número exacto de partes |
| C4 | `confirmacionValida` acepta un número mayor que N | muerto (1 tests) | f040 R52, D-12: confirmacionValida solo con el número exacto de partes |
| C5 | `confirmacionValida` no quita los espacios | muerto (1 tests) | f040 R52, D-12: confirmacionValida solo con el número exacto de partes |
| C6 | cancelar no borra lo tecleado | vivo → **muerto** con test nuevo | f040 R52 (T3, C6, C7): la confirmación empieza siempre vacía: ni cancelar ni volver a pedir dejan el número |
| C7 | abrir la confirmación no borra lo tecleado | vivo → **muerto** con test nuevo | f040 R52 (T3, C6, C7): la confirmación empieza siempre vacía: ni cancelar ni volver a pedir dejan el número |

## P · El filtro de `previsto`

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| P1 | `previstosDe` coge todo lo que no es `rechazado` | muerto (4 tests) | f040 R52, R56: puedeVolcar con previstos, todos los ensayos en 200, sin caducar y sin nada en vuelo |
| P2 | un ensayo sin previstos da cuerpo (lista vacía) | muerto (2 tests) | f040 R52: cuerpoDeVolcado sin ningún previsto (o sin ensayo_id) es null: ese trozo no se manda |
| P3 | el volcado no lleva la `revision_id` | muerto (2 tests) | f040 R52: cuerpoDeVolcado lleva confirmado true, el ensayo_id y SOLO los previsto, con su revision_id |
| P4 | N y el recuento cuentan todas las filas, no solo las `previsto` | muerto (3 tests) | f040 R51, R52: juntarEnsayos cuenta N previstos, las excluidas con su texto y el recuento por unidad de lo que se crearía |
| P5 | un ensayo sin previstos se manda | muerto (1 tests) | f040 R52: un ensayo sin previstos no se manda (el backend rechaza una lista vacía) |

## T · El troceo

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| T1 | cada trozo coge uno de más | muerto (3 tests) | f040 R51: 285 incidencias entre 5 son 57 trozos de 5, sin perder ni repetir ninguna |
| T2 | el troceo pierde el último | muerto (18 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| T3 | `trocear` acepta un `n` no entero | muerto (1 tests) | f040 R51: trocear con un n que no es un entero positivo lanza (nunca un bucle sin fin) |
| T4 | `trocear` acepta `n = 0` (bucle sin fin) | muerto (1 tests) | tests_js\volcado.test.js |
| T5 | un solo trozo con todo | muerto (18 tests) | f040 R51: la serie de ensayos para en el primer no-200: no pide los trozos siguientes y no deja volcar |
| T6 | el panel cuenta los trozos por defecto (`floor`) | muerto (1 tests) | f040 R50: resumenDelPanel cuenta aprobadas, en duda, volcadas, candidatas y trozos |

## U · El recuento por unidad

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| U1 | el recuento por unidad no suma (siempre 1) | muerto (3 tests) | f040 R51, R52: juntarEnsayos cuenta N previstos, las excluidas con su texto y el recuento por unidad de lo que se crearía |
| U2 | el recuento por unidad sin el nombre del catálogo | muerto (3 tests) | f040 R51, R52: juntarEnsayos cuenta N previstos, las excluidas con su texto y el recuento por unidad de lo que se crearía |
| U3 | `va` sin sumar `se_enlaza` | muerto (2 tests) | f040 R61, C-3: el recuento por unidad de cada grupo sale de por_unidad (va = va + se_enlaza), con nombre o código |
| U4 | el recuento de la confirmación cuenta todas las filas | muerto (1 tests) | f040 R51, R52: juntarEnsayos cuenta N previstos, las excluidas con su texto y el recuento por unidad de lo que se crearía |
| U5 | el recuento por grupo incluye unidades con 0 | muerto (1 tests) | f040 R61, C-3: el recuento por unidad de cada grupo sale de por_unidad (va = va + se_enlaza), con nombre o código |
| U6 | la confirmación sin los números por unidad | muerto (2 tests) | f040 R52, C-3: el texto de la confirmación dice N, la obra y el recuento por unidad |

## G · Agrupar la sincronización

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| G1 | un veredicto desconocido tiene casilla | muerto (1 tests) | f040 R61: un veredicto desconocido va a choca SIN casilla (no se puede incluir) |
| G2 | el porqué de un choque no llega en texto | vivo → **muerto** con test nuevo | f040 R61 (T3, G2): cada reclamación de lo que choca lleva su porqué ya en texto (el HTML no llama a Volcado) |

## R · El resultado del volcado

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| R1 | el aviso de PTE al revés (sin creados sí, con creados no) | muerto (3 tests) | f040 R52, R53: con la confirmación, un volcado por ensayo con previstos, de uno en uno y en su orden |
| R2 | un `volcado_sin_traza` no deja el trozo en duda | muerto (2 tests) | f040 R53.2, R53.4: en duda salen los sin_respuesta de un 200 y, del fallo, los de cada parada de §3.2 |
| R3 | un 502 `volcado_sin_respuesta` deja en duda todo el trozo, no solo sus `en_duda` | muerto (2 tests) | f040 R53.2, R53.4: en duda salen los sin_respuesta de un 200 y, del fallo, los de cada parada de §3.2 |
| R4 | lo que no se llegó a mandar no sale en el resultado | muerto (9 tests) | f040 R53.1: con el ensayo de un trozo caducado, ese trozo no se manda y el panel para |

## A · `js/api.js`: `sinReintentos` y `mensajeDelServicio` de las cuatro

| Mutante | Qué cambia | Resultado | Test asesino (el primero) |
|---|---|---|---|
| A1 | `volcadoEnsayo` sin `sinReintentos` | muerto (1 tests) | f040 R53, R60: volcadoEnsayo, volcadoVolcar y revisionSigrid NO se reintentan: ni un 502, ni la red, ni el corte |
| A2 | `volcadoVolcar` sin `sinReintentos` | muerto (1 tests) | f040 R53, R60: volcadoEnsayo, volcadoVolcar y revisionSigrid NO se reintentan: ni un 502, ni la red, ni el corte |
| A3 | `revisionSigrid` sin `sinReintentos` | muerto (1 tests) | f040 R53, R60: volcadoEnsayo, volcadoVolcar y revisionSigrid NO se reintentan: ni un 502, ni la red, ni el corte |
| A4 | `volcadoVolcar` sin `mensajeDelServicio` | muerto (1 tests) | f040 R54, R60: un 503 de las cuatro ensena el texto del servicio (con o sin codigo), no la puerta de archivar |
| A5 | `volcadoPanel` sin `mensajeDelServicio` | muerto (1 tests) | f040 R54, R60: un 503 de las cuatro ensena el texto del servicio (con o sin codigo), no la puerta de archivar |
| A6 | `volcadoPanel` con `sinReintentos` (es una lectura: reintenta) | muerto (1 tests) | f040 R50: volcadoPanel es una lectura: reintenta lo transitorio, como revision |

## Los siete vivos de la primera pasada

- **O5** (`registrar()` no vacía `ensayos`): hueco real. Tras «Volver a registrar» sin haber volcado, los
  ensayos viejos seguían ahí y `volcadoPuedeVolcar()` decía que sí (el botón lo escondía `vistaEnsayo`, pero el
  método se podía llamar). El único test de «Volver a registrar» venía de un volcado, que ya vacía `ensayos`.
  Test nuevo: tras ensayar, registrar otra vez deja `ensayos` vacío y no deja volcar.
- **O14** (`pedirVolcado()` sin guarda): hueco menor (`volcar()` vuelve a mirar `volcadoPuedeVolcar()`, así
  que no escribía), pero la confirmación se abría con el ensayo caducado. Test nuevo.
- **V5** (`volcadoPuedeVolcar` sin la sesión): hueco real; el test de la sesión solo miraba ensayar. Test nuevo:
  con el ensayo hecho y la sesión sin correo, ni se puede volcar ni sale el volcado.
- **C6, C7** (lo tecleado sobrevive a cancelar / a reabrir): cada uno solo, el otro lo tapa; se fija el estado
  observable («la confirmación empieza siempre vacía») y mueren los dos.
- **G2** (`porqueTexto` vacío): el recorrido del HTML evalúa la expresión pero no mira el texto. Test nuevo
  sobre `agruparSincronizacion`: cada reclamación de lo que choca trae `textoPorque(...)` y fuera de choca, nada.
- **V3, equivalente.** Quitar de `puedeVolcar` el `if (conPrevistos.length === 0) return false` no cambia nada:
  sin ensayos con previstos, `caducidadMasTemprana([])` es `null`, `caducado` de una caducidad ilegible es
  `true` (fijado por V7) y `puedeVolcar` devuelve `false` igual. Se deja la línea porque dice la regla (R52:
  «≥ 1 previsto») en vez de depender de un efecto de la caducidad. **Para aceptación escrita del humano.**

## Verificación tras los tests nuevos

```
$ python <guion> O5 O14 V3 V5 C6 C7 G2
O5 muerto 1 f040 R53.6 (T3, O5): «Volver a registrar» tras un ensayo sin volcar tira el ensayo: ya no se puede volcar
O14 muerto 1 f040 R52 (T3, O14): el primer clic de volcar no abre la confirmación si no se puede volcar
V3 VIVO 0
V5 muerto 1 f040 R56 (T3, V5): sin la sesión completa no se puede volcar aunque haya ensayo
C6 muerto 1 f040 R52 (T3, C6, C7): la confirmación empieza siempre vacía: ni cancelar ni volver a pedir dejan el número
C7 muerto 1 f040 R52 (T3, C6, C7): la confirmación empieza siempre vacía: ni cancelar ni volver a pedir dejan el número
G2 muerto 1 f040 R61 (T3, G2): cada reclamación de lo que choca lleva su porqué ya en texto (el HTML no llama a Volcado)
```
