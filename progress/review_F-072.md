<!-- progress/review_F-072.md -->
Revisión completa (pasada principal, review final T22) de `dev...88adde2` (merge-base `05c8a5a`; base fija `6994cb0`). Lo bloque a bloque lo dan por bueno las reviews 1–6; el Bloque 7 (T21) se revisa aquí entero.

# F-072 · Review final (el tipo de reclamación sale de Sigrid de punta a punta)

- **Veredicto: APROBADO** (APPROVED) en `88adde2`, **condicionado** a tres cosas que no son del código (§6): la
  campaña de la feature (`progress/mutacion_F-072.md`) válida y revisada en la pasada de evidencias, RM7
  ejecutado en esa pasada y el `init.sh` sin caché del líder en el SHA de cierre. Antes de T24, retocar
  `tasks.md` (§5, C-4).
- **Rigor:** `critico` (declarado): RED, cobertura, mutación sin supervivientes sin justificar, RM1–RM7.
- **Ejecutado** (ni suites enteras ni mutantes, por encargo): alcance + documentación con la rama forzada por un
  plugin del scratchpad, **110 passed, 0 skipped** (los 12 del diff incluidos); `test_f072_volcado`,
  `revision_http`, `importacion` y `dominio_tipos`, **113 passed**; un guion de punta a punta (§1); `ruff` en `dev`
  y en `88adde2`. `init.sh` **no**: vale el del líder en `539e928` (≡ `88adde2` salvo `tasks.md`, comprobado):
  raíz 2202, api 10377, front 911, cobertura 158/158, tamaño en topes.

## 1 · Coherencia de punta a punta

| Punta | Qué hace con el tipo | ¿Cierra? |
|---|---|---|
| Plantilla | catálogo → ubicaciones → `tipos()` → `listas_con_tipos` → generador; `<res> (<cod>)` (`application/pipelines/plantilla.py`) | sí (R1, R6, R7) |
| Importación | `paso_catalogo` lee los tipos solo si se reconoció y no es `ya_importado`; `_validar_fila` guarda el código o `0002` y `listado=None` | sí (R11–R15) |
| Bandeja | `INSERT` con `tipo_reclamacion` y `listado` NULL; lectura de la columna 19 (`sentencias_bandeja.py`) | sí (R15) |
| Revisión | `valores_importados` copia el tipo (O1 del Bloque 4, cerrada en `46b0abe`, M22 muerto); editar con `_tipo_pedido`; aprobar con los códigos leídos; `_mismos_valores` y `campos_cambiados` por tipo efectivo | sí (R19–R27) |
| Volcado | `parte_de` → `tipo_efectivo(v.tipo_reclamacion)`; candidatas de `revision.listar` (foto completa); `select_volcado_de` solo lee `revision_id`, `accion` y `huella_valores` | sí (R28) |

**R28, aparte** (guion del scratchpad, sin base ni red): importada con `9001` y aprobada **sin editar** → parte
`tipo = 9001`, huella intacta; con tipo nulo → `0002`, intacta. El camino que dejaba abierto la O1 del Bloque 4.

**R29 / R31.** El volcado no lee `auxtrcp`: `application/pipelines/volcado.py`, `guarda_sigrid.py` y
`infrastructure/sigrid/volcado.py`/`cliente.py` siguen iguales a la base (lo fija el test de alcance, mitad del
diff ejecutada aquí) y `test_f072_volcado.py::r29_*` lo prueba por comportamiento. Lo nuevo que habla con
Sigrid hereda `AdaptadorCatalogoSigridApi` (`/api/sql/read`) y solo define `leer`. `construir_tipos_reclamacion`
usa las dos puertas de las ubicaciones y ninguna ventana. **Front (Q-4):** `bandeja.html:675-681` pinta
`opciones().listados` por `codigo` y manda `formulario.listado`. No hay `primero`/`segundo` cableados.

## 2 · R32 y R33 (Bloque 7)

- **R32** `[x]`. Los 12 controles del diff pasan: nada del front ni de §3.3; en `infrastructure/sigrid/` solo
  `A` de los dos módulos y `M` de la fábrica (solo gana la función); el único `.sql` es `A 17_…`; `consultas*.py`
  y `function_app.py`, iguales. Entre `6994cb0` y la merge-base solo entraron tests y un informe: no inflan el
  alcance de la campaña. Los dos tests van en `ejecutar_siempre` de `api` (`servicios.json`).
- **R33** `[x]`. `ARCHITECTURE.md` tiene la sección «El tipo de reclamación (F-072)», y las frases «tipo 0002
  siempre» de F-059 quedan como historia con «desde F-072, el tipo efectivo». `INTEGRACION.md` §1, §2, §3 bis,
  §4, §6, §8 y §9, fiel al código (SQL literal, orden, techo, log sin `res`, aviso a F-048). Los controles leen
  el código, no solo el texto. RED con salida real (32 failed / 1 passed; alcance sembrado, 5 failed).

## 3 · El DDL (R16–R18), listo para producción

`17_tipo_reclamacion.sql` son dos `ALTER TABLE postventa.<tabla> ADD COLUMN IF NOT EXISTS tipo_reclamacion
text CHECK (char_length(…) BETWEEN 1 AND 24)`. No hay `UPDATE`, `DELETE`, `DROP` ni `ALTER COLUMN`, y nada toca
`listado`. La guarda (`ddl.py:432-445`, sin cambios) solo admite esa forma, y `cargar_ddl` aplica el fichero el
último. Lo aplica `asegurar_esquema` una vez por proceso, bajo `pg_advisory_lock` y con el `lock_timeout` de la
sesión. R17: T13 repetido, **120 passed** (humano, 2026-11-17). Q-3: `postventa_app` es el dueño. La
**marcha atrás** es segura: el código anterior nombra sus columnas en `SELECT` e `INSERT`.

## 4 · Checkpoints

- **C1** `[x]`, condicionado a la condición 3. `init.sh` del líder verde en `539e928`, igual a `88adde2` salvo
  `tasks.md`. Los ficheros base del arnés están.
- **C2** `[x]`. Una feature activa, en la rama `feature/F-072-tipo-reclamacion-sigrid`. Podar `current.md` e
  ir a `history.md` es de T27.
- **C3** `[x]`. Hexagonal: puerto en `domain/ports`, adaptador hijo en `infrastructure/sigrid` y fuente callable
  en `application`. Los 17 ficheros nuevos llevan la ruta en la primera línea. Sin `print` ni secretos, y
  ejemplos ficticios. Las reglas de partes, firmas y estados no aplican (N/A): F-072 no toca partes ni estados
  de Sigrid.
- **C3 bis / ter** `N/A`: ni documentos externos ni conversaciones. **C3 quater** `N/A` en la rama: T25 (líder).
- **C4** `[x]`. Cada R tiene su test (§7); R17 y R34 son MANUAL (T13, T26). Sin red, base ni IA (`sin_red`
  sigue `autouse`). Los dobles anotan sus llamadas en una lista común a todos los colaboradores (base de RM7).
- **C4 bis** `[x]` `rigor`, RED en los 7 bloques, cobertura 158/158 y «Evidencias»; capa e2e `N/A` (R32 deja
  fuera el front). **Mutación `pendiente: pasada de evidencias`** (condición 1). Por bloque: 1 y 2, campañas
  válidas (5/5 y 16/16 muertos); 3, a mano con OK del humano («a ok a cerrarla», 2026-11-17); 4–6, a mano y
  reproducidas por su reviewer, con OK del humano a (b) («ok, t13 hecha y 120 passed»). RM1–RM6 `pendiente`
  del informe; RM7 `pendiente` (condición 2).
- **C4 ter** `N/A`: no hay `harness/rutas_sensibles.json`, y el diff no toca `rigor.local.json`. **C5**: T1–T21
  `[x]` con commits `F-072 Tn: …`, T22–T28 abiertas y el árbol limpio.

## 5 · Observaciones abiertas y preparación del Bloque 8

- **C-4 (antes de T24; no afecta al código).** T24 da el DDL por aplicado si `GET /api/health` responde. Pero
  `health` no abre PostgreSQL (`interface_adapters/api/health.py:20`): el DDL se aplica en la **primera
  petición que construye un repositorio** en cada proceso (`fabrica.py:_conexion_con_esquema`). Hay que añadir a
  T24 una petición que abra la base (`GET /api/bandeja?obra=0677`) y comprobar que no hay error del DDL en
  Application Insights, o leer `information_schema.columns` de las dos tablas.
- **O-1 (para el aviso a F-048, T25).** `ALTER TABLE … ADD COLUMN IF NOT EXISTS` pide `ACCESS EXCLUSIVE` **antes**
  de ver que la columna ya existe. Así, cada arranque en frío bloquea un instante las dos tablas. Con
  `lock_timeout` falla rápido, pero si hay un lector largo esa petición falla y la siguiente vuelve a intentarlo.
- **O-2.** Sigue sin aplicar la O1 del Bloque 3: `design.md:49` dice «`leer()` y el log de R30», cuando el log es
  de la aplicación. **O-3.** Siguen la O2 del Bloque 6 (dos paréntesis seguidos en `ARCHITECTURE.md`, «… F-072)
  (cada lectura de un puerto)») y su O1 (`raising=False` en `test_f072_revision_http.py:170,328,372`). Son
  cosméticas, para el commit de cierre.
- **O-4 · ruff 103 → 112.** Los 9 nuevos son de ficheros de F-072 y ninguno es un fallo: siete `I001` (orden
  de imports; uno de producción, `domain/models/importacion.py:56`, y seis de tests), un `SIM114`
  (`test_f072_alcance_cerrado.py:299`) y un `ISC004` (`test_f072_importacion.py:166`, tupla de dos con la
  cadena partida adrede, no una coma perdida). `UP031` de `backlog.py` sale en los dos lados (BOM). Ocho se
  arreglan con `ruff check --fix`.
- **O-5.** Sigue la deuda O3 del Bloque 3: `test_f036_r115_*`, con su tope de 1 s, puede volver a invalidar la
  campaña. **O-6.** La cabecera de `INTEGRACION.md` sigue en F-065, porque la fija `test_f065_documentacion.py`;
  decide el líder.
- **T23–T28 bien preparadas**: merge desde un worktree aparte; publicación desde una copia limpia de `dev`;
  `azure-apps` con `pull` antes y commit aparte; T26 sin escrituras en Sigrid (solo filas «PRUEBA F-072» y un
  **ensayo**, Q-10); `done` solo con T28 y esta review.

## 6 · Condiciones del veredicto (las completa el líder)

1. **`progress/mutacion_F-072.md`** (`--feature F-072 --base 6994cb0`), revisado en la **pasada de
   evidencias**: sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto (base rota)» a 0 y línea base declarada; RM1 (el SHA
   de HEAD; si es posterior a `88adde2`, que el delta no toque el alcance); RM2 coherente; recálculo con
   `harness.alcance` y `generar_mutantes` y 2–3 supervivientes muestreados; RM5 con **uno** de los
   equivalentes, y RM6; cero supervivientes sin justificación aceptada por el humano. Si sale NO VÁLIDA **solo**
   por `test_f036_r115_*`, vuelve al humano: su OK del 2026-11-17 cubre los Bloques 4–6, no la campaña de T22.
2. **RM7 dinámico**, en esa pasada y en copias del scratchpad. Hay que aplicar tres mutaciones que suben la
   lectura de tipos por encima del catálogo: `paso_importacion.py:211-213`, `application/pipelines/revision.py:334-336`
   y `plantilla.py:176-180`. No las ejecuté: el encargo lo prohíbe con la campaña en marcha y el clasificador
   también lo bloqueó. **Por lectura, las caza la suite.** `test_f072_importacion.py:233`,
   `test_f072_revision_http.py:288` y `test_f072_plantilla.py:270` comparan la lista **exacta** de llamadas de
   todos los colaboradores. Además, `revision_http.py:294` exige `tipos.leer` antes de `revision.registrar`.
   Falta verlas en rojo.
3. `ARNES_SIN_CACHE=1 bash harness/init.sh` en verde en el SHA de cierre, con la cobertura en `[OK]`.

## 7 · Trazabilidad (requisito → test; el detalle por R, en las reviews de bloque)

| R | Test | R | Test |
|---|---|---|---|
| R1–R5, R30 | `test_f072_lectura_sigrid.py`; `r1_*` de `_plantilla`, `_importacion`, `_revision_http` | R19, R26, R28 | `test_f072_dominio_tipos.py`, `test_f072_volcado.py` |
| R6–R10 | `test_f072_plantilla.py`, `test_f072_dominio_tipos.py` | R20–R25, R27 | `test_f072_revision_dominio.py`, `test_f072_revision_http.py` |
| R11–R15 | `test_f072_importacion.py`, `test_f072_persistencia.py` | R29 | `test_f072_volcado.py` (`r29_*`) |
| R16, R18 | `test_f072_ddl.py` | R31, R32 | `test_f072_alcance_cerrado.py` |
| R17 | `tests_bbdd/…/test_f072_bbdd_tipo.py` (T13 MANUAL, 120 passed) | R33 / R34 | `test_f072_documentacion.py` / T26 MANUAL |

## Cambios requeridos

Ninguno en el código. Para cerrar: las condiciones 1–3 de §6; antes de T24, el retoque C-4.

## Automejora (propuesta, no aplicada)

- `reviewer.md`, RM7: si los dobles anotan todas las llamadas en una lista exacta, aceptar en la pasada principal
  un RM7 «por lectura» como provisional y exigir el dinámico en la de evidencias, para no chocar con una campaña
  en marcha. Y en `CHECKPOINTS.md` (vale para `arnes-base`): una tarea que verifica un DDL con `health` tiene que
  nombrar una petición que toque la base.
