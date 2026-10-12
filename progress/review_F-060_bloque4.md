<!-- progress/review_F-060_bloque4.md -->
# Review · F-060 · Bloque 4 · Tras cada importación (T13–T16)

- **Veredicto:** **APPROVED condicionado a la aceptación escrita de I19.** No hay que tocar ni el código ni los
  tests. El único punto abierto es el mutante a mano **I19**, declarado equivalente. En nivel `critico`,
  `CHECKPOINTS.md` C4 bis exige que el humano acepte esa equivalencia por escrito. Mi juicio es que **I19 es
  equivalente** (ver C-1). Cuando la aceptación quede anotada en `progress/impl_F-060.md`, el veredicto pasa a
  APPROVED sin más revisión que comprobar esa anotación. Es el mismo trámite que se siguió con H11 en el Bloque 3 y
  con la C-3 del Bloque 1.
- **Rama:** `feature/F-060-normalizar-ubicaciones`, HEAD `3b330c9`. Base del bloque: `c8d60d1`. Base fija de la
  feature: `33d8938`.
- **Commits revisados:** `2624507` (T13), `5eebdc8` (T14), `eff95a4` (bloqueo en T15), `918e338` (decisión del
  humano 2026-10-12), `4be221b` (T13 bis), `8e049ba` (T14 bis), `4c50362` (T15) y `3b330c9` (T16).
- **Fecha:** 2026-10-12 · reviewer.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige:

- la fase RED con la traza pegada;
- cobertura de lo cambiado;
- mutación con cero supervivientes, salvo aceptación escrita del humano, **también para los mutantes a mano
  declarados equivalentes**;
- RM7, porque el requisito central del bloque es un orden: la normalización va **después** del registro y del
  Excel de errores (R31), la puerta «¿se registraron filas?» va antes que cualquier construcción (R32), y en la
  composición Sigrid va antes que la base (§9.2).

## Lo comprobado (resultados reales)

Todo se ha ejecutado desde `services/postventa-api`.

| Qué | Resultado |
|---|---|
| Sin caché (`-p no:cacheprovider`): los cinco `test_f060_*` (importación, dominio, HTTP, pipeline y lote) y `test_f006_repo_sin_identificadores.py` | **370 passed** en 201,45 s |
| Diff de los tests de F-036 y F-053 (y de `tests/utiles_importacion.py`) contra `c8d60d1` **y** contra la base fija `33d8938` | **Vacío.** En `tests/`, el único fichero cambiado en el bloque es `test_f060_importar_normaliza.py` |
| T15 (2261 passed, 16 skipped, igual que la línea base en `c8d60d1`) | No relanzado, por el encargo. El diff vacío garantiza que pasaron **sin tocarlos**, y el caso que los bloqueaba (`test_f036_r118_…`) lo reproduce un test propio, `test_f060_r34_sin_configuracion_de_sigrid_responde_igual_y_avisa` |
| `git status` antes y después de la review | Limpio. Todas las mutaciones y las mediciones se han hecho en copias desechables fuera del repositorio |

### El código (`interface_adapters/api/importar.py`)

- **El `except Exception` solo envuelve la normalización.** El `try` contiene una única sentencia:
  `resultado = normalizar(obra, contexto.catalogo, contexto.ahora)` (línea 255). Eso cubre la composición real
  (`_normalizar_de_verdad`) y su ejecución, y nada más. Quedan fuera del `try` los seis pasos de la importación, la
  puerta `_registro_filas`, la línea de éxito y `serializar_importacion`. Es el único `except Exception` que añade
  F-060 al servicio (grep sobre el código de producción).
- **«Cualquier excepción» = `Exception`.** Es la lectura correcta. `KeyboardInterrupt`, `SystemExit`,
  `GeneratorExit` y `asyncio.CancelledError` (que en 3.12 hereda de `BaseException`) no son fallos de la
  normalización: son paradas del proceso o del worker. Tragárselas dejaría seguir una petición que el host ha
  mandado parar. Es lo que fija el test `r34_una_interrupcion_no_es_un_fallo_y_sube`, y cumple la decisión del humano
  («cualquier excepción de la normalización se registra»): un fallo es una `Exception`; una interrupción no es un
  fallo.
- **La respuesta es idéntica.** `serializar_importacion` no cambia, y la normalización no toca el `contexto`:
  devuelve un resultado que solo va al log. Los tests lo comparan con un oráculo que monta los seis pasos de F-036
  sin F-060, por igualdad del diccionario. El Excel de errores se compara por el contenido de sus celdas, y un
  control comprueba que el comparador no es ciego. Se comprueba con normalizador que normaliza, que no normaliza
  nada y que falla (once errores de §5.1 y seis excepciones más). También se comprueba por la ruta HTTP
  (`function_app.importaciones`, 200 y el mismo cuerpo).
- **El log.** El aviso es exactamente `F-060 normalización tras importar no hecha: obra=<obra> motivo=<Tipo>`, sin
  `exc_info` ni mensaje. Los tests comparan la cadena entera y comprueban que `str(error)` no aparece en el log. En
  el caso de unos ajustes incompletos, comprueban que tampoco aparece el nombre del campo (`sigrid_api_base_url`).
  La línea de éxito lleva solo números, `ensayo` y la obra. `r35_el_log_no_lleva_textos_ni_oid_ni_correo` busca en
  el log las ubicaciones, la descripción, el texto del sistema, el `oid` de quien importa, el nombre del fichero y
  los `incidencia_id`, y no encuentra ninguno.
- **Solo se normaliza si se registraron filas.** La condición es `nuevas + duplicadas_en_fichero > 0`, dentro de
  `if not contexto.ya_importado`. Los tests cubren cinco casos de R32: ya importado, todas con error, plantilla vacía,
  todas ya en la bandeja y el caso de solo duplicadas. Sin filas, la composición real no construye ninguna fábrica.
- **No se lee Sigrid de más.** Se usa el catálogo que la importación ya leyó: el mismo objeto que recibe el Excel de
  errores, y `leer_unidades` se llama una sola vez. Hay una sola lectura de ubicaciones. Con `ENTORNO=test`, la
  puerta de entorno de la fuente se cierra antes de tocar la red, y esto es lo que ven los tests de F-036 y F-053.
- **No se escribe en Sigrid.** La composición son los lectores de F-056 (`sql/read`) y el lote de revisiones en el
  esquema propio. No hay ninguna ruta de escritura de la pasarela ni ninguna ventana (`grep` en `importar.py`).
- **Arquitectura.** La composición vive en el punto de entrada, como manda `docs/CONVENTIONS.md`.
  `paso_importacion.py` y `contexto_importacion.py` no cambian. Importar `construir_fuente_de_ubicaciones` de
  `interface_adapters/api/revision.py` sigue el precedente de `plantilla.py`: es el borde reutilizando el borde.
  El logging es el `logging` estándar, como en el resto del servicio. La primera línea lleva la ruta del fichero, no
  hay `print` ni secretos, y no hay dependencias nuevas.

### Fase RED (reproducida)

He copiado el servicio y le he puesto el `importar.py` de `5eebdc8` (T14, con la captura cerrada de §5.1) junto a los
tests de HEAD. Resultado: **25 failed, 57 passed**. Los 25 son exactamente los que lista el informe (6 + 1 + 12 + 6)
y caen por aserción (`Failed: la importación no ha respondido: sube <Tipo>`). Los 57 en verde son los 55 del informe
más los 2 de la interrupción añadidos en T16, que con la captura cerrada ya pasaban. La traza de T13 (51 fallos de
59, contra el esqueleto neutro) está pegada en el informe y no la he relanzado.

### Cobertura de lo cambiado (medida por el reviewer)

He ejecutado `coverage run --branch` sobre `test_f060_importar_normaliza.py` en una copia: **82 passed**.
`importar.py` sale con un 87 %, y las 8 líneas sin cubrir (124, 134, 139, 185, 189, 193, 195 y 380) son todas de
F-036. Ninguna cae en los fragmentos añadidos del diff (55–56, 72–75, 82–83, 93, 98, 108–109, 158–159, 168–173,
210–214 y 218–303). **Lo nuevo queda cubierto al 100 %, en sentencias y en ramas.** La línea `PUERTA COBERTURA` es
de T23.

### Mutación

- **Recálculo puro** con `harness.alcance.alcance_de_feature("F-060", base="c8d60d1")` y
  `harness.mutacion.generar_mutantes`: 1 fichero, **111 líneas**, **6 mutantes**. Coinciden uno a uno con los del
  informe: los cuatro de la línea 231 (`logico`, `aritmetico`, `comparacion` y `entero`), el de la línea 279
  (`aritmetico`, `-` → `+`) y el de la línea 300 (`booleano`, `ensayo=False` → `True`). Mismo operador y mismo texto
  original → mutado.
- **Campaña no reejecutada: 17,4 min (1042,9 s) según el informe.** Supera los 5 minutos, así que me quedo en el
  recálculo puro. El coste por mutante es 1042,9 × 6 ÷ 6 = **1042,9 s**, plausible para la suite del servicio con
  `-x`.
- **Supervivientes de la herramienta:** 0.
- **Mutantes a mano del implementer:** 19 de 20 muertos. I17 (`except BaseException`) quedó vivo en la primera
  pasada y era un **hueco real**; lo cierra el test de la interrupción añadido en T16. El que sigue vivo es **I19**:
  ver C-1.

### RM7 · mover cada puerta de orden (copia desechable, solo `test_f060_importar_normaliza.py`, sin `-x`)

| Mutación | Resultado | Tests que caen (de la propia feature) |
|---|---|---|
| RM7-a · la puerta y la normalización, **por encima** de `paso_registro` | **ROJO** | 74 de 82, empezando por `r31_con_filas_registradas_normaliza_una_vez_tras_el_excel_de_errores` |
| RM7-b · la normalización **sin puerta**, por encima de `paso_registro` | **ROJO** | 8: los de R31 por el orden (`llamadas[-2:]`) y los de R32 porque normaliza sin filas |
| RM7-c · la normalización entre el registro y el Excel de errores | **ROJO** | 2: `r31_con_filas_registradas…` y `s9_2_sin_normalizador_compone_el_real…` |
| RM7-d · la base (`construir_revision`) antes que Sigrid (`construir_fuente_de_ubicaciones`) | **ROJO** | 9, entre ellos `s9_2_sin_normalizador_compone_el_real_sigrid_antes_que_la_base` y `s9_2_en_entorno_test_la_composicion_real_no_sale_a_la_red` |

Cada puerta cae con tests **de la propia feature**: ninguna depende de una suite vecina. Los dobles ven a todos los
colaboradores del orden, porque la bandeja, el generador, el normalizador y las dos fábricas anotan en la misma lista.

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- N/A · `bash harness/init.sh` completo. **Justificación:** es un bloque intermedio, y el líder pidió no lanzarlo y
  ejecutar sin caché los tests de F-060 y `test_f006`. Están en verde (370 passed). T15 dejó en verde los de F-036 y
  F-053 (2261 passed, el mismo recuento que la línea base), y el diff vacío prueba que no se tocaron. La puerta
  completa se pasa en T23.
- [x] El arnés está completo (`CLAUDE.md`, `features.json`, `specs/SPECS.md`, `CHECKPOINTS.md` y `docs/`).

**C2**
- [x] Como mucho una `in_progress`, y es F-060 (ha vuelto de `blocked` con la decisión del humano).
- [x] La rama es `feature/F-060-normalizar-ubicaciones`.
- N/A en este bloque · `progress/current.md` solo con la sesión activa. **Justificación:** lo mantiene el líder.
  Ya lleva la decisión del 2026-10-12, y la limpieza pendiente es la de la O-6 del Bloque 3, que se exige en la
  review final.
- N/A · resumen en `history.md`. **Justificación:** F-060 no está `done`; se hace en T36.

**C3**
- [x] Hexagonal. La composición está en el punto de entrada, y los pasos y el contexto de F-036 no cambian.
- [x] La primera línea de cada fichero nuevo o tocado es un comentario con su ruta.
- [x] Sin `print`, sin TODO, sin secretos y sin dependencias nuevas. El logging es el `logging` estándar.
- [x] **Nada contra Sigrid sin dry-run.** No hay ninguna escritura en Sigrid: solo `sql/read`. La escritura en el
  esquema propio es la revisión del sistema de D-1/D-2, aprobada por el humano.
- N/A · reglas de partes (unidad de trabajo, manuscrito, firmado, reprocesar, estados de Sigrid y escaneados).
  **Justificación:** el bloque toca la importación de incidencias de F-036, no los partes.

**C3 bis**
- N/A. **Justificación:** el bloque no trae ningún documento de fuera ni toca `docs/referencia/`.

**C4**
- [x] R31–R35 tienen test, y todos pasan (tabla de abajo).
- [x] Los tests unitarios no tocan red ni base: dobles en memoria y fábricas sustituidas. Donde se usa la composición
  real, `ENTORNO=test` la cierra antes de la red.
- [x] Lo `MANUAL (humano)` sigue listado: T7 del Bloque 2. Este bloque no añade ninguno.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: las dos trazas están pegadas, y la de T13 bis la he **reproducido** (25 failed por aserción).
- [x] Cobertura de lo cambiado: 100 % en sentencias y ramas, medida por el reviewer.
- [x] Mutación: el informe existe, con totales reales, recalculados y coincidentes.
- [x] Muertos: campaña no reejecutada (17,4 min según el informe). Recálculo puro, e I3/I10 comprobados por mi
  cuenta como RM7-c y RM7-d.
- [x] Duración plausible: 1042,9 s por mutante con 6 workers.
- [ ] **Cero supervivientes sin aceptación escrita del humano: pendiente.** La herramienta deja 0, pero el mutante a
  mano **I19** se declara equivalente, y en `critico` eso necesita la aceptación escrita del humano → **C-1**.
- [x] RM7: las cuatro mutaciones de orden dan rojo con tests de la propia feature.
- [x] Las «Evidencias» del bloque traen tests, cobertura, mutantes (herramienta y a mano), workers (6) y tiempos. La
  suite completa es de T23.

**C4 ter**
- N/A. **Justificación:** no hay `harness/rutas_sensibles.json` en el repositorio.

**C5**
- [x] En `tasks.md`, T13–T16 están `[x]`, con sus commits. Los de T13 y T14 bis llevan el sufijo «(decisión
  2026-10-12)» tras el número, para distinguirlos de los primeros: lo acepto.
- [x] No hay temporales ni ficheros sin trackear.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test

| Requisito | Tests (`test_f060_importar_normaliza.py`) |
|---|---|
| R31 | `r31_con_filas_registradas_normaliza_una_vez_tras_el_excel_de_errores`, `r31_sin_filas_con_error_tambien_normaliza_tras_registrar`, `r31_una_duplicada_del_fichero_tambien_normaliza`, `r31_solo_duplicadas_del_fichero_tambien_cuenta`, `s9_2_sin_normalizador_compone_el_real_sigrid_antes_que_la_base` |
| R32 | `r32_ya_importado_no_normaliza`, `r32_todas_con_error_no_normaliza`, `r32_la_plantilla_vacia_no_normaliza`, `r32_todas_ya_en_la_bandeja_no_normaliza`, `r32_sin_filas_la_composicion_real_no_construye_nada` (×3) |
| R33 | `r33_el_comparador_del_excel_no_es_ciego`, `r33_la_respuesta_es_la_de_la_importacion_sin_normalizar` (×13), `r33_por_la_ruta_es_200_con_el_mismo_cuerpo` (×13) |
| R34 (y la decisión del 2026-10-12) | `r34_cada_error_se_avisa_con_la_obra_y_su_tipo` (×11), `r34_cualquier_excepcion_del_normalizador_se_avisa_por_su_tipo` (×6), `r34_sin_configuracion_de_sigrid_responde_igual_y_avisa`, `r34_una_composicion_que_lanza_cualquier_excepcion_no_cambia_nada` (×12), `r34_un_fallo_dentro_de_la_normalizacion_no_altera_la_respuesta` (×6), `r34_una_interrupcion_no_es_un_fallo_y_sube` (×2), `s9_2_si_la_base_no_se_construye_se_avisa_y_responde_igual`, `s9_2_en_entorno_test_la_composicion_real_no_sale_a_la_red` |
| R35 | `r35_una_linea_con_el_recuento_y_los_segundos`, `r35_el_log_no_lleva_textos_ni_oid_ni_correo` |
| §9.2 (la composición) | `s9_2_sin_normalizador_compone_el_real_sigrid_antes_que_la_base`, `s9_2_el_normalizador_inyectado_no_construye_nada` |
| R39 (F-036 y F-053 sin tocar) | diff vacío contra `c8d60d1` y `33d8938`; T15 con 2261 passed. Su test propio es T19 |

## Cambios requeridos

1. **C-1 · I19: aceptación escrita del humano (`CHECKPOINTS.md` C4 bis, nivel `critico`).** No se toca ni código
   ni tests.
   - **El mutante.** En la línea de éxito de `_normalizar_tras_importar`
     (`services/postventa-api/interface_adapters/api/importar.py:269`), `resultado.obra_codigo` se cambia por la
     `obra` de la importación.
   - **Mi juicio: es equivalente.** `normalizar_ubicaciones` (`application/pipelines/revision.py:412-413` y `:447-448`)
     devuelve `ResultadoNormalizacion(obra_codigo=obra_codigo, …)` con el mismo valor que recibe, sin
     transformarlo. `_normalizar_de_verdad` le pasa exactamente la `obra` de la importación. En producción, las dos
     versiones escriben el mismo texto en el log. Solo un normalizador inyectado de test podría devolver otra obra,
     y fijar eso sería fijar el comportamiento de un doble. No hay test útil que añadir.
   - **Qué falta.** Anotar en `progress/impl_F-060.md` la aceptación del humano («C-1 de la review del Bloque 4 ·
     aceptación del humano»), con fecha y su respuesta literal, igual que H11. Con eso, el veredicto pasa a
     APPROVED. Si el humano no la acepta, la otra salida es cambiar esa línea a `obra`: elimina la pregunta y obliga
     a repetir la T16 del bloque.

## Observaciones (no bloquean este bloque)

- **O-1 · El docstring del módulo `importar.py` se ha quedado corto.** Las secciones «Qué se construye y cuándo»
  (líneas 18–25) y la última frase de «La respuesta» (líneas 42–43) describen la importación de F-036. No dicen que,
  tras registrar filas, ahora se construyen también la fuente de ubicaciones (Sigrid, `sql/read`) y la revisión
  (escritura de revisiones del sistema en el esquema propio). El docstring de `importar_excel` sí lo dice. Conviene
  ponerlo al día en T20, junto a la enmienda del «No revisa» de F-036 en `docs/ARCHITECTURE.md`.
- **O-2 · T19 tiene que incluir `importar.py`.** A partir de este bloque, `importar.py` es código de F-060. El
  detector de R38 de T19 (ninguna ruta de escritura ni ventana) tiene que recorrerlo, y el de R36 tiene que
  comparar las claves de la respuesta de la importación con las de la base fija.
- **O-3 · La importación se alarga.** Ahora la importación incluye, de forma síncrona, el listado de la obra entera
  (hasta el tope de 10.000), una lectura de Sigrid y el lote. Es lo que pide D-2, pero suma a cada importación con
  filas parte del coste que el Bloque 5 va a medir en el listado (p50 de 7,1 s en F-056). El balanceador corta a
  los 230 s. Si cortara, la importación ya estaría guardada y un reintento daría `ya_importado`, sin pérdida, pero
  quien sube vería un error. Propongo que la medición de T28 apunte también los `segundos=` de la línea
  `origen=importacion` en la primera importación tras publicar.
- **O-4 · La línea de éxito queda fuera de la captura.** Es intencionado y lo acepto. Con
  `normalizar_ubicaciones`, el resultado siempre está bien formado. Solo un doble mal hecho podría hacer fallar el
  formateo después de guardar. Ampliar el `try` iría contra «nada más se captura de forma amplia».

## Automejora (propuesta, no aplicada)

Ninguna nueva. RM7 ha funcionado como estaba previsto: un orden de colaboradores (registro → Excel de errores →
normalización) que la herramienta no muta y que los dobles ven porque anotan en una lista común.
