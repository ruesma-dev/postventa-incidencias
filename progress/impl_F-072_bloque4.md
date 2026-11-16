# F-072 · Bloque 4 · DDL y persistencia (T10, T11, T12) — informe del implementer

Rama del worktree `worktree-agent-a8112cd5b3fc5721b`, creada desde `feature/F-072-tipo-reclamacion-sigrid`
en `5e9f675` (el worktree nació en `87a03f3`; estaba limpio y se hizo `git reset --hard 5e9f675`, como
pedía el encargo). Commits: T10 `6278b98`, T11 `baed128`, T12 `3fe185f`. Fuera del encargo: T13 (MANUAL),
T14 (mutación) y `bash harness/init.sh` (los lanza el líder). Nada de DDL contra ninguna base ni red.

## Hecho

- **`infrastructure/persistencia/sql/17_tipo_reclamacion.sql`** (nuevo): las dos sentencias de `design.md` §7,
  carácter a carácter (`ALTER TABLE postventa.<tabla> ADD COLUMN IF NOT EXISTS tipo_reclamacion text CHECK
  (char_length(tipo_reclamacion) BETWEEN 1 AND 24)`) sobre `bandeja_incidencias` y `revisiones_bandeja`. Cabecera:
  ruta, «Construye:», «Lee de: 13_ y 15_», columna nueva y no `CHECK` sobre `listado`, nulo = anterior a F-072
  (tipo efectivo `0002`), sin `UPDATE`, y el aviso de Q-3 (dueño, bloqueo breve). La guarda (`ddl.py`) lo acepta
  sin cambios; `13_`, `15_`, `16_` y `ddl.py` intactos (lo comprueba un test contra `6994cb0`).
- **`domain/models/importacion.py`**: `tipo_reclamacion: str | None = None` como último campo de
  `IncidenciaValida` y de `IncidenciaEnBandeja`. Solo los campos (`validar_filas` es del Bloque 5).
- **`sentencias_bandeja.py`**: `tipo_reclamacion` al final de `COLUMNAS_BANDEJA` (orden en que `ADD COLUMN` la deja
  en la tabla) y de `_COLUMNAS_LISTADO`; `valores_de_fila` escribe `valida.tipo_reclamacion` y **`listado` a `NULL`**
  siempre (R15); `fila_a_incidencia` lee `fila[18]`.
- **`sentencias_revision.py`**: la columna al final de `_LEIDAS_DE_LA_BANDEJA`, `_LEIDAS_DE_LA_REVISION` y
  `COLUMNAS_INSERT`; `insert_revision` escribe `v.tipo_reclamacion` (la copia de `listado` sigue tal cual, R23);
  `fila_a_revision` y `_situacion` la leen (nulo, nulo: el `0002` lo pone el dominio). Sección nueva en el docstring.

## Ficheros

- Nuevos: `services/postventa-api/infrastructure/persistencia/sql/17_tipo_reclamacion.sql`,
  `tests/test_f072_ddl.py`, `tests/test_f072_persistencia.py`, `tests_bbdd/tests/test_f072_bbdd_tipo.py`.
- Modificados (código): `domain/models/importacion.py`, `infrastructure/persistencia/sentencias_bandeja.py`,
  `infrastructure/persistencia/sentencias_revision.py`.
- Modificados (tests anteriores, ver abajo): 15 de `tests/` y 3 de `tests_bbdd/tests/`.
- `specs/F-072-tipo-reclamacion-sigrid/tasks.md`: T10, T11 y T12 marcadas.

## Fase RED (T10, commit `6278b98`)

Comando, desde `services/postventa-api` del worktree (sin `.venv` propio: intérprete de la carpeta principal):

```
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\.venv\Scripts\python.exe -m pytest tests/test_f072_ddl.py tests/test_f072_persistencia.py -q -p no:cacheprovider --tb=line
```

Salida real (resumen de las líneas `E`, contadas; traza completa fuera del repo):

```
FFFFFFFFFFFFFFFFFFFFF....FFFFFFFFFFFFFFFFFF                              [100%]
E   AssertionError: assert '16_volcados_sigrid.sql' == '17_tipo_reclamacion.sql'
E   AssertionError: falta 17_tipo_reclamacion.sql                                   (x18)
E   AssertionError: assert ('CREATE INDE...(llamada_id)') == ('ALTER TABLE...EN 1 AND 24)')   (x2: por defecto y otro esquema)
E   TypeError: IncidenciaValida.__init__() got an unexpected keyword argument 'tipo_reclamacion'   (x5)
E   AttributeError: 'IncidenciaEnBandeja' object has no attribute 'tipo_reclamacion'   (x2)
E   AssertionError: ... Right contains one more item: 'tipo_reclamacion'            (COLUMNAS_BANDEJA, campos, COLUMNAS_INSERT)
E   AssertionError: assert False  ...startswith('SELECT ... creada_at_utc, tipo_reclamacion\n')   (select_bandeja, select_revisiones)
E   AssertionError: assert 'b.creada_at_utc, b.tipo_reclamacion' in 'SELECT b.incidencia_id, ...'
E   ValueError: zip() argument 2 is shorter than argument 1                          (x2: insert_revision)
E   ValueError: zip() argument 2 is longer than argument 1                           (x2: fila_a_revision)
E   ValueError: badly formed hexadecimal UUID string                                 (fila_a_situacion, anchos)
39 failed, 4 passed in 1.51s
```

Todas fallan por la razón esperada (falta el `.sql`, faltan los campos y la columna en las sentencias). Los
**4 que pasan** son `test_f072_r16_r32_lo_que_no_se_toca_sigue_igual_que_en_la_base[13_, 15_, 16_, ddl.py]`:
protegen que algo **no** cambie, así que pasan antes y después por diseño (no son RED-ables).

## GREEN (T11, commit `baed128`)

Verificación de `tasks.md`, mismo intérprete:

```
python -m pytest tests/test_f072_ddl.py tests/test_f072_persistencia.py tests/test_f005_ddl_seguro.py tests/test_f036_ddl.py tests/test_f056_ddl.py tests/test_f036_repositorio_bandeja.py tests/test_f056_repositorio_revision.py
397 passed in 4.63s
```

## T12 (commit `3fe185f`)

`tests_bbdd/tests/test_f072_bbdd_tipo.py`, 16 tests: R17 (base sin la columna —`DROP COLUMN IF EXISTS` **solo en la
base efímera**, explicado en la cabecera—, una fila de bandeja y una revisión escritas con las columnas de antes, DDL
dos veces: definición igual en la segunda pasada y las dos filas con tipo nulo), columna `text` nula sin defecto en
las dos tablas, nada en `public`, `CHECK` en las dos tablas (`""` y 25 caracteres → `CheckViolation`; 1, 24 y nulo
entran), y escritura y lectura con tipo por `RepositorioBandejaPostgres.listar` (tipo y `listado` nulo) y
`RepositorioRevisionPostgres.situacion`/`historial` (tipo de la bandeja y de la foto).

```
python -m pytest --collect-only tests_bbdd/tests/test_f072_bbdd_tipo.py   ->  16 tests collected in 0.44s
python -m pytest tests_bbdd/tests/test_f072_bbdd_tipo.py                  ->  16 skipped (sin POSTVENTA_PG_TEST_DSN)
```

Con los de F-036, F-056, F-059 y F-060: `110 tests collected` sin errores.

## Aserciones anteriores que cambian (todas ampliadas, ninguna borrada ni relajada)

Cada cambio lleva en el propio test un comentario `F-072 (R…)`.

- **R16, el `17_` en la lista u orden del DDL**: `test_f005_ddl_idempotente_texto.py` (lista completa),
  `test_f028_ddl_historico.py` (ídem), `test_f036_ddl.py::test_f036_t14_los_tres_ficheros_…` (cola),
  `test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_…` (`[-2]`/`[-1]` → `[-3]`/`[-2]` y `[-1] == 17_`),
  `test_f059_ddl.py::test_f059_r32_el_fichero_va_el_ultimo_…` (ídem), `test_f030_veredicto_persistido.py`,
  `test_f031/32/33/34_alcance_cerrado.py` (`DDL_DE_F056 + ("16_…", "17_…")`), `test_f060_alcance_cerrado.py::…_los_quince_de_antes`
  y `test_f065_alcance_cerrado.py::…_los_dieciseis_de_antes` (el `17_` es de F-072, no de esas features).
- **R15, `test_f036_repositorio_bandeja.py`**: `COLUMNAS_BANDEJA` gana `tipo_reclamacion`; marcas 21 → 22 (dos tests);
  `test_f036_t15_valores_de_una_fila_completa`: la posición de `listado` pasa de `"segundo"` a `None` (R15) y la fila
  válida lleva `tipo_reclamacion="9001"`, que sale el último; `select_bandeja` lee también `tipo_reclamacion`; el
  ayudante `_fila_bandeja` lleva `tipo_reclamacion: None`.
- **R16/§6.2, `test_f056_repositorio_revision.py`**: las tres listas escritas a mano (`LEIDAS_DE_LA_BANDEJA`,
  `LEIDAS_DE_LA_REVISION`, `ESCRITAS`) ganan la columna al final; las filas de ejemplo (`_fila_bandeja`,
  `_fila_revision`, `_fila_aprobada`) y los parámetros esperados del `INSERT` llevan `None` al final.
- **`tests_bbdd` (para que T13 siga en verde)**: `test_f056_bbdd_revision.py` (21 → 22 columnas en
  `information_schema`; el `INSERT … generate_series` gana `NULL::text`; ayudante con `tipo_reclamacion: None`),
  `test_f059_bbdd_volcado.py` y `test_f060_bbdd_lote.py` (ayudante con `tipo_reclamacion: None`; sin él, `KeyError`).

## Decisiones y observaciones para la review

1. **Lo que escribe la bandeja**: `valores_de_fila` escribe `valida.tipo_reclamacion` tal cual, como dice §6.2
   («`tipo_reclamacion` en el `INSERT`»); el «no nulo» de R15 lo garantiza `validar_filas` (R12/R14, Bloque 5). Hasta
   el Bloque 5 una importación escribiría tipo nulo y `listado` nulo (tipo efectivo `0002`): estado intermedio que no
   se despliega. Alternativa descartada por no estar en la spec: escribir `tipo_efectivo(...)` en la persistencia.
2. **Hueco de la spec, sin tocar (fuera de alcance)**: `domain/models/revision.py::valores_importados` no copia
   `incidencia.tipo_reclamacion` a `ValoresIncidencia`. Con lo de este bloque la fila de la bandeja ya trae su tipo,
   pero una incidencia **sin revisiones** sigue teniendo tipo efectivo `0002` en la revisión, en `validar_valores`
   (R21) y en `parte_de` si se aprobara así, aunque se importara con otro (R12). `design.md` §3.2 no lo lista en
   ningún bloque; propongo que el líder decida si va en el Bloque 5 o 6 (es una línea más su test).
3. La columna va **la última** en todas las listas (es donde `ADD COLUMN` la deja en la tabla y donde la puso §4.2 en
   `ValoresIncidencia`).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests dirigidos de T11 | `397 passed in 4.63s` |
| Tests de F-072 del bloque | 43 (`test_f072_ddl.py` 25, `test_f072_persistencia.py` 18) + 16 de `tests_bbdd` (saltados sin DSN) |
| Suite `api` entera (`pytest tests`, en serie, tras T12) | `10161 passed, 369 skipped in 954.05s (0:15:54)`, 0 fallos |
| Cobertura de líneas cambiadas | sin medir: `init.sh` lo lanza el líder |
| Mutantes | sin medir: T14 la decide el líder |
| Capa e2e | N/A (persistencia) |

## Pendiente

T13 (MANUAL, humano: base efímera con Docker), T14 (mutación y review del Bloque 4), `bash harness/init.sh` (líder)
y la observación 2.
