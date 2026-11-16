<!-- progress/review_F-072_bloque3.md -->
Revisión completa del Bloque 3 (pasada 1): delta `a3fcb46..5e9f675` (T7 `daca1b9`, T8 `a7d959c` `a0f93d6`,
T9 `26c6f36` `ae15470` `c2f842e`, nota del líder `5e9f675`). Los Bloques 1 y 2 quedan dados por buenos.

# F-072 · Review del Bloque 3 (la lectura de `dbo.auxtrcp`: R1–R5, R30, R31)

- **Veredicto: APROBADO** (APPROVED) en `5e9f675`, condicionado a que el `init.sh` del líder salga
  verde (no lo he ejecutado: lo lanza el líder, por su encargo) y con **una condición de cierre de
  F-072** (no del bloque): el OK explícito del humano a la excepción de mutación, abajo.
- **Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura (90 %) y
  mutación con 0 supervivientes; e2e informativa.

## 1 · Mutación: ¿vale la tabla a mano como veredicto?

**Sí, como evidencia; no como checkbox.** El punto de C4 bis «el informe NO lleva la cabecera
⚠ CAMPAÑA NO VÁLIDA» no se cumple, y mi protocolo dice rechazar ante esa cabecera. Lo que esa regla
protege es no creerse los números de una suite rota, y aquí **nadie usa esos números**: el veredicto es
una campaña a mano que he recalculado y reproducido. Por eso apruebo el bloque, dejando la excepción a
la vista para que la confirme el humano (el «terminar cuanto antes» de `current.md` no es un OK a esta
excepción concreta).

**Por qué es suficiente:**
- **Causa ajena y demostrada.** Las dos bases se rompen al final en tests de **tiempo** de F-036
  (`test_f036_r115_*`, tope de 1 s, `tests/test_f036_excel_lector.py`), que F-072 no toca; con 8 y con
  4 suites enteras en paralelo. En serie, la suite `api` pasa (`10133 passed`, informe del implementer).
- **La tabla es reproducible al pie de la letra.** Recalculado con `harness.alcance` +
  `generar_mutantes` (cálculo puro) sobre la base `6994cb0`: **489 líneas y 45 mutantes**, fichero a
  fichero igual que el informe (10, 4, 20, 0, 2, 9, 0, 0). Las 24 filas de la tabla corresponden **una
  a una** a mutantes del generador por `fichero:línea` + operador; ninguna fila es ambigua.
- **Reproducidas 9 filas** con `generar_mutantes`/`aplicar_mutante` sobre una **copia de HEAD** en el
  scratchpad (`git archive`; base `172 passed`), tests `lectura` + `f056_ubicaciones` +
  `f072_dominio_tipos`, sin `-x`:

| Mutante (texto exacto del generador) | Tabla | Yo | Lo caza (de F-072) |
|---|---|---|---|
| `consultas:61` `valor is None` → `not valor` | 1 failed | **1 failed** | `r2_cada_fila...[falsos-no-nulos]` |
| `aplicación:62` `if lectura.llego_al_techo:` → `if not ...` (techo, R4) | 12 failed | **12 failed** | `r5_codigos_vacios_fuera...`, `r4_al_techo...` |
| `aplicación:51` `codigo not in tipos` → `in` (repetidos, R5) | 8 failed | **8 failed** | `r5_codigos_vacios_fuera...` |
| `aplicación:49` `if not codigo:` → `if codigo:` (vacíos, R5) | 8 failed | **8 failed** | `r5_un_codigo_nulo_o_en_blanco...` |
| `aplicación:48` `or ""` → `and ""` | 11 failed | **11 failed** | `r5_...` |
| `aplicación:58` `- len(tipos)` → `+ len(tipos)` (repetidos del log) | 2 failed | **2 failed** | `r30_la_linea_de_log...`, `r30_al_techo...` |
| `consultas:51` `or` → `and` | 5 failed | **5 failed** | `r2_una_fila_sin_tres_columnas...[nula]` |
| `ports:44` `repr=False` → `repr=True` | 1 failed | **1 failed** | `r30_la_fila_es_inmutable...` |
| `plantilla_incidencias:579` `codigo is None` → `not codigo` | 2 failed | 1 failed¹ | `r19_con_tipo_el_efectivo_es_el_guardado[]` |

¹ Mismo test asesino; el número difiere porque la tabla no dice con qué ficheros se juzgó esa fila
(«los tres `test_f072_*` de dominio y volcado»); yo solo pasé `test_f072_dominio_tipos.py`.

- **Todos los cazan tests de la propia feature**, ninguno solo una suite vecina.
- **El superviviente real (`consultas:61`) está bien cerrado:** con el mutante cae exactamente el caso
  nuevo `falsos-no-nulos` (`[0, "", 0]` → `FilaTipoReclamacion("0", "", 0)`), y no es equivalente: un
  `cod` `0` numérico acabaría en «sin código». Que la 1.ª campaña lo diera por **muerto** es la prueba de
  que sus «muertos» no valían: bien detectado por el implementer.
- **Ficheros sin mutantes (prueba de control sin exclusión de alcance):** `fabrica.py` da 6 mutantes en
  el fichero entero y 0 en sus líneas de alcance (exclusión legítima); `volcado.py`, 139 y 0 (líneas del
  Bloque 1, sin operadores); `infrastructure/sigrid/tipos_reclamacion.py` da **0 incluso entero**: es
  legítimo (una clase con un método de 3 líneas sin comparaciones, literales ni operadores), y lo
  cubren las mutaciones a mano M24/M25, que he reproducido (abajo). Declaraciones escritas, ninguna
  en `PENDIENTE`.
- **Mutaciones a mano propias** (copia del scratchpad, `test_f072_lectura_sigrid.py`):
  - **RM7 · fábrica, la configuración antes que el entorno** (bajar la puerta del entorno un paso):
    `3 failed` (`r31_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion[test|local|'']`).
  - **Orden log → 409:** el `raise` del techo antes de la línea de log: `2 failed`
    (`r30_al_techo_tambien_se_registra_antes_del_409`).
  - **M25** mapeo identidad en el adaptador: `3 failed`; **M24** texto de la operación: `6 failed`.
- **RM1:** SHA medido `ae15470…`; de ahí a HEAD solo cambia `progress/current.md`: alcance idéntico.
- **RM2:** base 2292,8–2363,7 s, media 476,0 s × 4 workers = 1904 s por mutante, coherente con una
  base de ~2340 s y 30/30 muertos con `-x`; `30 × 476,0 = 14280 ≈ 14281,0` s. Sin salto de orden.
- **RM3:** ningún equivalente salió muerto en la 2.ª campaña (no hay equivalentes declarados; el único
  dudoso, `:61`, no lo es). **RM5:** N/A, no hay supervivientes declarados equivalentes.
  **RM6:** `26c6f36` añade un caso de test; no quita ninguna guarda.
- **Árbol:** las mutaciones se hicieron sobre la copia; `git status` del árbol de trabajo, limpio.

## 2 · R30: la línea de log en la aplicación y no en el adaptador

**Coherente con la spec.** R30 no dice dónde va la línea, solo qué lleva; R5 pide contar en el log los
vacíos y los repetidos, y esos recuentos solo existen en la aplicación, que es quien filtra y deduplica
(§5: el adaptador «no decide»). §6.1 lo fija expresamente («Log de R30 en la aplicación») y da el
formato literal, que coincide carácter a carácter con el código. Lo que choca es la fila de §3.1
(«adaptador: `leer()` y el log de R30»): es una **contradicción interna del design**, no del código, y el
implementer la dejó escrita como decisión en `impl_F-072_bloque3.md`. Además, el adaptador no registra
nada con el `res` (`r30_el_adaptador_no_registra_nada_con_el_nombre`), y la línea se escribe **antes**
del 409, para que `al_techo=True` conste (comprobado moviéndola, arriba).
→ Observación O1: enmendar la fila de §3.1.

## 3 · Checkpoints (lo que aplica al bloque)

- **C1** — [ ] pendiente del líder: `init.sh` no es mío por encargo. Mis ejecuciones: lectura +
  ubicaciones `172 passed`; arquitectura (`f006`, `f013`) + resto de `test_f072_*` `336 passed, 2
  skipped`; `test_f013_puertos_y_dobles.py` `42 passed`.
- **C2** — [x] rama `feature/F-072-tipo-reclamacion-sigrid`; F-072 única activa (`in_progress`);
  `current.md` describe la sesión.
- **C3** — [x] hexagonal: el puerto solo importa `domain.ports.catalogo_obra`; la aplicación, solo
  `domain.*`; el adaptador hereda `AdaptadorCatalogoSigridApi` sin tocarlo y la fábrica sigue la puerta
  de `construir_ubicaciones_validas`. [x] primera línea con la ruta en los 5 ficheros; sin `print`, sin
  secretos (URL, clave y base inventadas en tests). [x] Nada contra Sigrid escribe: solo `sql/read`.
  Resto de C3 (parte, firmas, manuscritos…): N/A, el bloque no los toca.
- **C3 bis / C3 ter** — N/A: no entra ningún documento externo ni acta.
- **C3 quater** — N/A en este bloque: `azure-apps` (lectura de `auxtrcp`) es la T25 del líder.
- **C4** — [x] trazabilidad (tabla abajo). [x] sin red ni base: `ClienteFalso` y un puerto en memoria.
  [x] dobles: `PuertoDeTipos` solo declara `leer`, que es el único método del puerto; la comprobación
  automática (`test_f013_puertos_y_dobles.py`) pasa. MANUAL: ninguna en este bloque.
- **C4 bis** — [x] rigor declarado. [x] **fase RED** con salida real (`ImportError` de colección y, en
  un worktree desechable con esqueletos, `72 failed, 7 passed` con las líneas de error por
  comportamiento). [ ] **cobertura**: la mide el `init.sh` del líder (`PUERTA COBERTURA`). [x]
  **mutación**: por **sustitución**, ver §1 (cabecera NO VÁLIDA presente; veredicto a mano recalculado
  y reproducido; 0 supervivientes tras `26c6f36`). [x] RM1, RM2, RM6, RM7; RM3 sin caso; RM5 N/A. [x]
  «Evidencias» con sus cuatro números y la capa e2e (N/A: lectura con dobles, sin front).
- **C5** — [ ] T9 sin marcar en `tasks.md` (correcto hasta esta review y el `init.sh`); árbol limpio.

## 4 · Cobertura de requisitos (Bloque 3)

| Req. | Tests (`tests/test_f072_lectura_sigrid.py`) |
|---|---|
| R1 | `r1_leer_es_un_post_a_sql_read_con_su_cuerpo`, `r1_la_fuente_lee_una_vez_por_llamada_y_sin_cache`, `r1_cero_filas...`, `r1_sin_tipos_vigentes...` |
| R2 | `r2_la_consulta_caracter_a_caracter`, `r2_la_consulta_es_la_de_requirements`, `r2_sin_parametros`, `r2_cada_fila...` (7 casos), `r2_una_fila_sin_tres_columnas...`, `r2_una_posicion...` |
| R3 | `r3_cortada_por_debajo_del_techo...`, `r3_lo_transitorio_se_reintenta`, `r3_agotados_los_reintentos...`, `r3_el_tiempo_agotado...`, `r3_un_definitivo...`, `r3_una_respuesta_sin_la_forma...`, `r3_el_fallo_del_puerto_sube_tal_cual` |
| R4 | `r4_mil_filas_o_mas...`, `r4_novecientas_noventa_y_nueve...`, `r4_al_techo_es_catalogo_sin_verificar...` |
| R5 | `r5_codigos_vacios_fuera_y_repetidos_el_primero`, `r5_un_codigo_nulo_o_en_blanco_se_ignora`, `r5_el_repetido_se_compara_recortado...` |
| R30 | `r30_la_linea_de_log_lleva_los_recuentos...`, `r30_al_techo_tambien_se_registra_antes_del_409`, `r30_la_linea_registra_la_duracion...`, `r30_el_adaptador_no_registra_nada...`, `r30_la_fila_es_inmutable...` |
| R31 | `r31_el_adaptador_se_niega_fuera_de_dev_y_pro`, `r31_solo_lee_y_no_mira_ningun_interruptor`, `r31_la_fabrica_*` (5) |

R1 «una vez por petición» en los handlers y el orden catálogo → ubicaciones → tipos (§5) son de los
bloques siguientes (composición en `plantilla`, `importar`, `revision`): aquí solo la fuente sin caché.

## 5 · Cambios requeridos

Ninguno para el bloque.

**Condición de cierre de F-072 (líder → humano):** que conste en `progress/` el OK explícito del humano
a cerrar la mutación del Bloque 3 con el veredicto a mano en lugar de una campaña válida. Sin él, el
punto «CAMPAÑA NO VÁLIDA» de C4 bis queda `[ ]` en la review final.

## 6 · Observaciones (no bloquean)

- **O1.** `design.md` §3.1, fila de `infrastructure/sigrid/tipos_reclamacion.py`: cambiar «`leer()` y el
  log de R30» por «`leer()`, sin log (la línea de R30 la escribe la aplicación, §6.1)».
- **O2.** La tabla a mano abrevia el texto mutado (`or` → `and`, `= 25`): aquí es reproducible porque
  cada fila sale del generador, pero el formato debería copiar `Mutante.descripcion()` literal y decir
  con qué ficheros de test se juzgó cada fila (la de `:579` no lo dice).
- **O3.** Deuda fuera de F-072: los `test_f036_r115_*` (tope de 1 s) rompen las líneas base de **toda**
  campaña con workers en este repositorio. Conviene una ficha propia antes de la próxima campaña.

## 7 · Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis / `reviewer.md`: contemplar el caso «campaña NO VÁLIDA por un test ajeno a la
  feature, demostrado» con la misma vía que la campaña MANUAL (una fila por mutante con
  `descripcion()` literal y nº de fallos, el reviewer reproduce ≥ 3 filas) y el OK del humano por
  escrito; hoy solo está prevista para «0 mutantes», y la regla de rechazo directo no distingue causa.
- Arnés (`arnes-base`): un marcador de tests de tiempo (p. ej. `@pytest.mark.tiempo`) que la campaña
  excluya de la línea base y de los mutantes, o que relance en serie al fallar, porque un tope de
  pared no es estable con W suites en paralelo. Vale para cualquier proyecto.
