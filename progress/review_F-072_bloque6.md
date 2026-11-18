<!-- progress/review_F-072_bloque6.md -->
Revisión incremental desde 705c85e (Bloque 6, pasada 1): delta `705c85e..3bb44e0` (T18 `ca86fd2`,
T19 `46b0abe` y `03b1e3d`, informe `6bc023a`, integración `3bb44e0`). Los Bloques 1–5 quedan dados
por buenos.

# F-072 · Review del Bloque 6 (la revisión: aplicación y HTTP con los tipos de Sigrid)

- **Veredicto: APROBADO** (APPROVED) en `3bb44e0`, con dos condiciones que no son del código, igual
  que el Bloque 5:
  1. `bash harness/init.sh` verde sobre `3bb44e0` (no lo he ejecutado por encargo: lo tiene en
     marcha el líder). Es además la primera suite entera tras `46b0abe` y `03b1e3d`.
  2. T20 sigue abierta: falta `progress/mutacion_F-072_bloque6.md` (campaña automática pendiente de
     la decisión del humano). La tabla a mano del implementer y mi reproducción (§3) son la
     evidencia disponible hoy; no sustituyen a C4 bis en `critico`.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED, cobertura,
  mutación con 0 supervivientes, RM1–RM7.

## 1 · Qué he ejecutado

- Worktree reiniciado a `3bb44e0` (estaba en `87a03f3`, limpio).
- `pytest` de la verificación de T19 más los ficheros de F-056/F-060/F-059/F-065 que toca el bloque
  (12 ficheros): **775 passed, 9 skipped in 23 s**.
- `pytest tests/test_f072_*.py tests/test_f056_*.py tests/test_f060_*.py tests/test_f036_*.py
  tests/test_f059_*.py` en el worktree: **4605 passed, 219 skipped in 801 s**.
- 13 mutantes a mano sobre una **copia desechable** de `3bb44e0` (`git archive` al scratchpad; línea
  base allí: 62 passed), no en el árbol: el pytest largo corría a la vez en el worktree. Copia
  restaurada byte a byte tras cada mutante (comprobado con `diff -r`); `git status` del worktree vacío.

## 2 · Spec, diseño y alcance

| R | Implementación | Test que lo cubre (en `test_f072_revision_http.py` salvo nota) |
|---|---|---|
| R1 listar | `listar_para_revisar`: catálogo → ubicaciones → `tipos()` → `listas_con_tipos` | `r1_listar_lee_los_tipos_una_vez_…`, `r1_cada_listado_vuelve_a_leer_…`, `r1_al_listar_los_tipos_se_construyen_tras_…` |
| R1 editar/aprobar | `aplicar_accion`, solo en `_LEEN_SIGRID`; `tipos is None` → `ValueError` | `r1_editar_y_aprobar_leen_…[editar,aprobar]`, `r1_cada_accion_vuelve_a_leer_…`, `r1_al_actuar_…`, `r1_editar_sin_la_fuente_…`, `test_f056_pipeline_revision::r46[…tipos]` |
| R1 borde | fábrica tras ubicaciones, antes de la base; 503 sin construir la base | `r1_sin_la_configuracion_de_los_tipos_es_503_…[listar,editar,aprobar]` |
| R3, R4 | `CatalogoNoDisponible`/`CatalogoSinVerificar` suben antes de `registrar` | `r3_…_503_sin_escribir[×3]`, `r4_…_409_sin_escribir[×3]` |
| R20 | `catalogo.listados` = leídos; `_valores_de` y `valores_importados` → tipo efectivo | `r20_catalogo_listados_…`, `r20_sin_tipos_vigentes_…`, `r20_listado_de_importados_y_vigentes_…`, `r20_la_respuesta_de_una_accion_…` |
| R21, R22 | `decidir` con las listas ya con tipos | `r21_*` (6 casos), `r22_editar_con_listado_nulo_guarda_0002` |
| R24 | `fila_de_revision(…, tipos=vigentes)`; respuesta con `_codigos(listas)` | `r24_*` (5 casos); `test_f056_revision_http::r8` |
| R27 | borde no construye ni pasa la fuente; aplicación no la llama | `r27_*` (3 tests, 5 casos); `test_f056_revision_http::r30` |
| R29 | sin cambio de producción: el volcado ya mandaba el guardado | `test_f072_volcado::r29_*` (5 tests, 9 casos) |
| §8 bandeja | `_serializar`: `listado = tipo_efectivo(tipo_reclamacion)` | `s8_la_bandeja_lleva_el_tipo_efectivo_en_listado`; `test_f036_bandeja_http::r45` |
| R32 | diff sin `services/postventa-front/**`, `infrastructure/sigrid/**`, SQL, `config/`, `function_app.py`, volcado | `git diff --stat 705c85e 3bb44e0` (19 ficheros, todos previstos o justificados abajo) |

**Puente del Bloque 5, resuelto**: `CONFIG` de `test_f056_revision_http.py` vuelve a ser
`cargar_plantilla_yaml()`; los tipos llegan por `construir_tipos_reclamacion` → `PuertoTiposEnMemoria`
y o2/r10/r42 editan con `9001` con el comentario puesto al día. **Nota del Bloque 2 para T19**,
resuelta: `revision.py:267` y `:337` ya pasan `tipos` (M-R24a abajo lo confirma).

### Las tres desviaciones

1. **`valores_importados` copia `tipo_reclamacion`** — **aceptada**. El fichero está en la lista de
   §3.2 del diseño («`domain/models/revision.py` | §4.2»), solo fuera de la lista de T19. Es un
   defecto real del Bloque 2: sin la línea, una incidencia importada con `9002` y sin revisar se
   serializaba como `0002` (R20), no podía conservar su tipo de baja (R21) y, aprobada sin editar,
   la foto vigente (que sale de `valores_importados`, `revision.py:477`) se volcaría con `0002`
   (R28). La huella (R26) de lo anterior a F-072 no cambia (tipo nulo → los 13 campos). Lo matan
   M22/M23 del implementer y mi R20b.
2. **Tramos `construir.tipos` y `tipos`** — **aceptada**. Sin ellos la lectura caería en `calculo`
   y rompería su definición («la aplicación menos los puertos»). La frase de `docs/ARCHITECTURE.md`
   es la mínima que exige `test_f060_documentacion`; T21 escribe la sección propia.
3. **`TIPOS_CON_EL_DEFECTO` en F-056/F-060** — **aceptada**. Lleva `0002` vigente como el `auxtrcp`
   medido en T0, así que esas secuencias no cambian de sentido; el caso contrario (`0002` no vigente)
   sigue cubierto por `test_f056_revision_http::r8` (con `TIPOS_FICTICIOS`, ahora
   `["tipo_fuera_de_sigrid"]`) y por `r24_el_0002_de_un_nulo_se_aprueba_si_esta_vigente`. Que esos
   dobles no anoten en `llamadas` es aceptable porque el orden lo fijan los de F-072: lo he
   comprobado moviendo la puerta (RM7, §3).

**`test_f056_alcance_cerrado::r39`** (`46b0abe`): la aserción sigue siendo de **igualdad exacta**
sobre la lista cerrada; solo entra `construir_tipos_reclamacion`, que es una lectura con la misma
puerta de entorno (`fabrica.py:356`, sin ventana de escritura, R31). No se vacía nada.

Aserciones anteriores cambiadas: las he recorrido en el diff; cada una lleva su comentario con el R
y el valor anterior, ninguna se borra sin sustituta (`r46` y `r41` de F-060 ganan el caso `tipos`).

## 3 · Mutación

**Tabla a mano del implementer (24/24)**: coherente con el diff; cada mutante apunta a una línea
nueva con lógica y a un test que existe. El equivalente declarado (`tipos=tipos if lee_sigrid else
None` → `tipos=tipos`) lo es: la aplicación solo llama a la fuente en `_LEEN_SIGRID`, y eso lo fija
`r27_la_aplicacion_no_lee_…` (mi R27a). M9 sobrevivió y se cerró con test (`03b1e3d`): correcto.

**Mi reproducción, 13 mutantes, 13 muertos** (script en el scratchpad; texto original → mutado):

| # | Fichero | Original → mutado | Test que cae |
|---|---|---|---|
| R1a | `pipelines/revision.py` | `listas_con_tipos(listas, tipos())` (listar) → `…(tipos(), tipos())[1]` | `r1_listar_lee_…_una_vez` |
| R1b | ídem | lo mismo en `aplicar_accion` | `r1_editar_y_aprobar_…` (2 fallos) |
| R1c | ídem | aprobar no lee: `listas if accion is APROBAR else listas_con_tipos(…)` | `r1_editar_y_aprobar_…[aprobar]` (409≠200) |
| R27a | ídem | `tipos()` antes del `if accion in _LEEN_SIGRID` en descartar/recuperar | `r27_la_aplicacion_no_lee_…` (2 fallos) |
| R27b | `api/revision.py` | la construcción de la fuente sale del `if lee_sigrid` | `r27_descartar_y_recuperar_ni_construyen_…` |
| RM7-503 | `pipelines/revision.py` | el error de `tipos()` se guarda y se lanza **tras** `registrar` | `r3_…[editar,aprobar]`, `r4_…[editar,aprobar]` |
| RM7-base | `api/revision.py` | en el listado, `construir.tipos` **después** de `construir.bandeja` | `r1_sin_la_configuracion_…[listar]` |
| R20a | `api/revision.py` | `tipo_efectivo(valores.tipo_reclamacion)` → `valores.tipo_reclamacion` | `r20_listado_de_importados_y_vigentes_…` |
| R20b | `domain/models/revision.py` | quitar `tipo_reclamacion=incidencia.tipo_reclamacion` | ídem |
| S8 | `api/bandeja.py` | `tipo_efectivo(incidencia.tipo_reclamacion)` → `incidencia.tipo_reclamacion` | `s8_la_bandeja_lleva_…` |
| R24a | `pipelines/revision.py` | `fila_de_revision(…, tipos=vigentes)` → `tipos=None` | `r24_un_tipo_guardado_fuera_…_en_la_fila` |
| R29a | `domain/models/volcado.py` | `tipo=tipo_efectivo(v.tipo_reclamacion)` → `tipo=TIPO_RECLAMACION` | `test_f072_volcado::r29_el_ensayo_manda_el_tipo_guardado_…` |
| R29b | `api/volcado.py` | añadir `from infrastructure.sigrid.fabrica import construir_tipos_reclamacion` | `test_f072_volcado::r29_el_volcado_no_lee_auxtrcp` |

**RM7** (la puerta de R3/R4 va antes de escribir; la construcción, antes de la base): bajada un
paso por cada colaborador que precede (`registrar` en la aplicación; `construir_revision` en el
borde), las dos en rojo y por **tests de esta feature**. En RM7-503 el caso `editar` cae ya por R21
(400, sin tipos no hay vigentes); el que demuestra el orden es `aprobar`, que escribe y luego sube
el error, y cae por `revision.registrar` en `llamadas`. Ningún superviviente.

RM1/RM2/RM5/RM6: sin informe de campaña automática todavía (condición 2). RM6: ningún mutante se
mató quitando código defensivo; la guarda `tipos is None` se **añadió** (M6). RM3: ningún
equivalente sale muerto en mi tabla.

## 4 · Checkpoints

- C1 `[ ]` **pendiente** del `init.sh` del líder sobre `3bb44e0` (condición 1); suite dirigida verde.
- C2 `[x]` una feature activa (F-072 `in_progress`); rama de worktree integrada en la de la feature.
- C3 `[x]` hexagonal: la aplicación importa `FuenteTiposReclamacion` de `application/`; el dominio
  sin infraestructura; la fábrica solo en el borde. Primera línea con ruta en el test nuevo; sin
  `print`, sin secretos; datos ficticios (`9901`, `@ejemplo.invalid`, «TIPO FICTICIO N»).
  Reglas de partes/Sigrid de C3: N/A, el bloque no archiva, ni cierra, ni escribe en Sigrid (R31).
- C3 bis / ter / quater: N/A — ni documentos de fuera, ni conversación registrada, ni cambio de lo
  que se expone a otros proyectos en este bloque (`azure-apps` lo pone al día el líder al desplegar, R33).
- C4 `[x]` cada R del bloque con test (§2); sin red, base ni IA (dobles en memoria).
- C4 bis: RED `[x]` (salida real en el informe, 33 failed / 27 passed, y los 27 explicados); cobertura
  **pendiente** de `PUERTA COBERTURA` del `init.sh`; mutación **pendiente** de T20 (condición 2);
  «Evidencias» `[x]` con los cuatro números y la capa e2e N/A (R32, el front no cambia).
- C4 ter: N/A, ninguna ruta sensible declarada tocada (`init.sh` lo dirá).
- C5: `tasks.md` T18 y T19 `[x]` con sus commits; T20 abierta por diseño; worktree limpio.

## 5 · Observaciones (no bloquean)

1. `test_f072_revision_http.py` conserva `raising=False` en los `monkeypatch` de
   `construir_tipos_reclamacion` (líneas 170, 328, 372), restos de la fase RED. Ya existe el
   nombre en el borde: quitarlo haría que un renombrado fallase en alto en vez de añadir un atributo
   suelto. Para T21/T22, si se toca el fichero.
2. `docs/ARCHITECTURE.md` (l. 1346): la frase nueva deja dos paréntesis seguidos («… F-072) (cada
   lectura de un puerto)») y una línea de más de 80 columnas. T21 reescribe esa sección.
3. La suite entera no se ha visto en verde tras `46b0abe`/`03b1e3d`: la da el `init.sh` del líder.
