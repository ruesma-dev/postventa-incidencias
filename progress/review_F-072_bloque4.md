Revisión completa del Bloque 4 (pasada 1): `5e9f675..201b8f6` (T10 `6278b98`, T11 `baed128`, T12 `3fe185f`, informe `61f651b`, integración `42c16ae`, corrección `201b8f6`), en HEAD `ecbfb0a`

# F-072 · Bloque 4 (T10–T12: DDL `17_tipo_reclamacion.sql` y persistencia) — review

- **Veredicto:** APROBADO, con dos condiciones que no son de código: T13 repetido en verde por el humano y su
  OK a la verificación de mutación a mano en lugar de la campaña (el mismo trato que el Bloque 3).
- **Nivel de rigor:** `critico` (declarado en `features.json`). Exige RED, cobertura, mutación con cero
  supervivientes y RM1–RM7. Este bloque no tiene campaña (decisión pendiente del humano), así que la sustituye
  la verificación a mano de abajo.
- **Alcance:** solo el Bloque 4. `bash harness/init.sh` no lo he ejecutado (el encargo lo prohíbe); me apoyo
  en el verde del líder en `5e9f675`+B4 (api 10177, cobertura 126/126) y en pytest dirigido.

## Lo que he ejecutado

- En el árbol real, T11 más los 17 ficheros de `tests/` tocados: `629 passed, 168 skipped in 87.97s`.
  `--collect-only` de `tests_bbdd` (F-072, F-036, F-056, F-059, F-060): `110 tests collected`.
- En la copia (`git archive HEAD`, en el scratchpad), la línea base da `393 passed, 4 skipped`; los 4 son la
  base fija por git, que en la copia no existe. Sobre ella, 27 mutantes a mano: 26 muertos y 1 equivalente
  (M27). `git status`, limpio: nada se mutó en el árbol de trabajo.

## Checkpoints

- C1 `[x]`: el verde de `init.sh` lo vio el líder (no lo repito por el encargo); pytest dirigido, verde.
- C2 `[x]`: rama `feature/F-072-tipo-reclamacion-sigrid`, una sola feature activa (`in_progress`).
- C3 `[x]`: hexagonal respetada. El dominio solo gana dos campos con defecto `None` (último campo, §3.2). Las
  sentencias y el `.sql` están en persistencia. Ficheros nuevos con su ruta en la primera línea, sin `print`,
  sin TODO y sin secretos. Datos de prueba ficticios (`9901`, `9001`, `@ejemplo.invalid`).
- C3 bis / ter `N/A`: no entra documentación de fuera ni actas. C3 quater `N/A` en el bloque: la columna es
  interna del esquema propio y no cambia lo expuesto ni lo consumido (`azure-apps`, el líder al desplegar).
- C4 `[x]`: R15, R16, R18 y R32 (parte DDL) tienen tests unitarios trazables que pasan. R17 queda en
  `tests_bbdd`, como pide la spec (MANUAL). Los unit tests no tocan red ni BBDD: el único `subprocess` es un
  `git show` local de solo lectura. T13 consta en `progress/current.md`. Dobles: no hay dobles nuevos.
- C4 bis:
  - RED `[x]`: salida real en el informe, con 39 fallos por la razón esperada. Los 4 que pasan protegen que
    algo no cambie, y está justificado.
  - Cobertura `[x]`: 126/126 según el líder.
  - Mutación `[ ]→pendiente del humano`: no hay `progress/mutacion_F-072_bloque4.md`. La sustituye la tabla
    de abajo, con texto exacto y número de fallos, y con todas las filas reproducidas por mí. Queda aceptada
    solo con el OK del humano.
  - RM1: HEAD `ecbfb0a`, igual en la copia y en el árbol. RM2 `N/A`: no hay tiempos de campaña. RM3 `[x]`:
    ningún equivalente salió muerto. RM5 `[x]`: M27 lleva su demostración (abajo). RM6 `N/A`: no se quitó
    ninguna guarda. RM7 `N/A`: ningún requisito del bloque protege un orden entre colaboradores.
- C4 ter `N/A`: no existe `harness/rutas_sensibles.json`. C5 `[x]` para el bloque: T10–T12 en `[x]` con sus
  commits `F-072 Tn:`; T13 y T14 siguen abiertas, como corresponde.

## Trazabilidad (requisito → test)

| Req. | Test(s) |
|---|---|
| R15 (tipo escrito, `listado` a NULL) | `test_f072_persistencia.py::test_f072_r15_*` (4); `test_f036_t15_valores_de_una_fila_completa`; `tests_bbdd::test_f072_r15_la_bandeja_se_escribe_y_se_lee_con_su_tipo` |
| R16 (dos `ALTER`, guarda, `CHECK` 1–24, orden) | `test_f072_ddl.py::test_f072_r16_*` (8); `tests_bbdd::test_f072_r16_*` (columna `text` nula sin defecto, `CHECK` en las dos tablas) |
| R17 (DDL dos veces sobre filas previas, nada en `public`) | `tests_bbdd::test_f072_r17_*` (2), MANUAL en T13 |
| R18 (ni `listado`, ni escrituras, ni borrados) | `test_f072_r18_*` (3, uno parametrizado con 11 prohibidos) |
| R32 (13_, 15_, 16_, `ddl.py` intactos) | `test_f072_r16_r32_lo_que_no_se_toca_sigue_igual_que_en_la_base` (4) |
| §6.2 (lectura en la bandeja y la revisión) | `test_f072_select_bandeja_*`, `fila_a_incidencia_*`, `la_foto_*`, `la_situacion_*`, `el_historial_*` |

Los tests anteriores que cambiaron se **amplían**, ninguno se relaja: 21→22 marcas, `[-3]/[-2]/[-1]`,
`(*SQL_DE_LA_BASE, "17_…")`, y `"segundo"`→`None` más `"9001"` al final, que es lo que pide R15. Cada cambio
lleva su comentario `F-072 (R…)`.

## Verificación de mutación a mano (RM4: sobre una copia de `git archive HEAD`, nunca en el árbol)

Tests: los 7 de T11. Cada mutante, solo, sin `-x` y revertido. B = `sentencias_bandeja.py`, R =
`sentencias_revision.py`, Q = `sql/17_tipo_reclamacion.sql`.

| # | Línea | Original → mutado | Resultado |
|---|---|---|---|
| M01 | B:305 | `None,  # listado` → `None if valida.listado is None else valida.listado.value` | MUERTO, 3 fallos (`r15_…listado_a_null[primero/segundo]`, f036 t15) |
| M02 | B:309 | `valida.tipo_reclamacion,` → `None,` | MUERTO, 6 |
| M03 | B:96 | se quita `"tipo_reclamacion"` de `COLUMNAS_BANDEJA` | MUERTO, 10 |
| M04 | B:151 | se quita de `_COLUMNAS_LISTADO` | MUERTO, 2 (`f072_select_bandeja_lee_el_tipo`, f036 r45) |
| M05 | B:375 | `fila[18]` → `fila[17]` | MUERTO, 3 |
| M06 | B:375 | `fila[18]` → `None` | MUERTO, 1 (`f072_fila_a_incidencia_…[9001]`) |
| M07 | B:375 | `fila[18]` → `fila[15]` | MUERTO, 3 |
| M26 | B:308-309 | `importado_at_utc` y `tipo_reclamacion` intercambiados | MUERTO, ≥6 (r15 ×5, f036 t15) |
| M08 | R:321 | `v.tipo_reclamacion,` → `None,` | MUERTO, 1 (`f072_r23_la_foto_…[9001]`) |
| M27 | R:321 | `v.tipo_reclamacion,` → `v.tipo_reclamacion or None,` | **EQUIVALENTE** (393 passed), ver abajo |
| M09 | R:373 | `tipo_reclamacion=d["tipo_reclamacion"]` → `=None` (`fila_a_revision`) | MUERTO, 2 |
| M11 | R:373 | `d["tipo_reclamacion"]` → `d["listado"]` | MUERTO, 8 |
| M10 | R:398 | `tipo_reclamacion=d["tipo_reclamacion"]` → `=None` (`_situacion`) | MUERTO, 1 (`f072_la_situacion_lee_el_tipo_…`) |
| M12 | R:123 | se quita de `_LEIDAS_DE_LA_BANDEJA` | MUERTO, 23 |
| M13 | R:149 | se quita de `_LEIDAS_DE_LA_REVISION` | MUERTO, 29 |
| M25 | R:175 | se quita de `COLUMNAS_INSERT` | MUERTO, 4 |
| M14 | Q:24 | `BETWEEN 1 AND 24` → `AND 25` | MUERTO, 4 |
| M15 | Q:25 | `BETWEEN 1` → `BETWEEN 0` | MUERTO, 4 |
| M16 | Q:25 | `ADD COLUMN IF NOT EXISTS` → `ADD COLUMN` | MUERTO, 10 (lo caza también la guarda de F-005) |
| M17 | Q:25 | sin el `CHECK (…)` | MUERTO, 5 |
| M18 | Q:24 | `text CHECK` → `text NOT NULL CHECK` | MUERTO, 4 |
| M19 | Q:25 | `postventa.revisiones_bandeja` → `public.revisiones_bandeja` | MUERTO, 11 |
| M20 | Q:+26 | `+ UPDATE postventa.bandeja_incidencias SET tipo_reclamacion = '0002' WHERE … IS NULL;` | MUERTO, 12 (R18) |
| M21 | Q:+26 | `+ ALTER TABLE … DROP CONSTRAINT IF EXISTS bandeja_incidencias_listado_check;` | MUERTO, 13 (R18) |
| M22 | Q:+26 | `+ ALTER TABLE … ALTER COLUMN listado SET DEFAULT 'primero';` | MUERTO, 14 (R18) |
| M23 | Q:24 | `tipo_reclamacion text` → `varchar(24)` | MUERTO, 4 |
| M24 | Q:25 | se borra la sentencia de `revisiones_bandeja` | MUERTO, 4 |

Los mutantes que solo mata un test (M06, M08, M10) los mata un test **de F-072**, no uno vecino.

**M27, la demostración de equivalencia (RM5).** Solo cambia el resultado si `v.tipo_reclamacion == ""`, y
el dominio no lo produce: `_tipo_pedido` (`domain/models/revision.py:741-762`) devuelve
`TIPO_RECLAMACION_POR_DEFECTO`, un código de `listas.listados` o el tipo efectivo vigente, y
`valores_importados` lo deja `None`. Si llegara un `""`, el `CHECK` de la base lo rechaza
(`tests_bbdd::test_f072_r16_el_check_de_la_revision_rechaza_vacio_y_mas_de_24[]`).

## La corrección `201b8f6` frente a R17: la conserva

R17 pide tres cosas: el DDL aplicado dos veces sobre una base con filas de F-036/F-056 no falla, deja el tipo
nulo en esas filas y no crea nada fuera de `postventa`. Tras la corrección, el test sigue haciendo lo mismo:
quita la columna, escribe una fila de bandeja y una revisión con las columnas de antes (`_sin_tipo`), aplica
el DDL dos veces (`_YA_ASEGURADOS.clear()`, y `asegurar_esquema` lo reaplica entero, sin registro de
aplicados), compara la definición tras la segunda pasada, y comprueba una fila por tabla con tipo nulo. Lo
de `public` sigue en su propio test.

Lo único que cambia es de dónde salen los valores de la revisión. Antes se leían por el repositorio, cuyo
`SELECT` ya pide la columna (el `UndefinedColumn` de T13). Ahora se construyen en memoria con
`_valores_de_la_bandeja`. He comparado ese constructor con `valores_importados` campo a campo: son los mismos
13 campos, con el mismo paso de `urgencia`/`listado` a su enum y sin tipo. El diagnóstico es correcto: en el
servicio el DDL corre al arrancar, antes de leer. Falta verlo en verde: **T13 lo repite el humano**.

## Observaciones (no bloquean el Bloque 4)

1. **Hueco funcional de la feature (la observación 2 del implementer), que hay que cerrar antes de terminar
   F-072.** `valores_importados` (`revision.py:453-469`) no copia `incidencia.tipo_reclamacion`. Una
   incidencia importada con un tipo distinto de `0002` y sin revisiones tendría tipo efectivo `0002` en la
   revisión, en `validar_valores` y en `parte_de`. Así escribiría en Sigrid un tipo que no es el importado,
   contra R12 y R28. Es del dominio (Bloque 3, ya aprobado) y la spec no lo asigna a ningún bloque. **El
   líder decide** el bloque y si hace falta una enmienda de spec. Basta una línea y su test.
2. **R15, «no nulo», todavía no lo garantiza ningún test.** La persistencia escribe lo que trae la fila
   válida, como manda §6.2, y el «no nulo» lo pone `validar_filas` (R12/R14, Bloque 5). Que la review del
   Bloque 5 compruebe que lo cierra.
3. **R17 (mejora opcional).** La fila «de F-036» se construye con el `valores_de_fila` de ahora, así que
   nace con `listado` NULL, mientras que una fila real anterior a F-072 trae `primero`/`segundo`. Ponerle
   `listado='primero'` y comprobar que sobrevive al DDL acercaría el test a los datos reales y daría a R18
   una prueba contra base.

## Cambios requeridos

Ninguno en el código del bloque. Para cerrar T13/T14:
1. El humano repite T13 (`infra\pruebas_bbdd_efimera.ps1`) y salen 120 en verde.
2. El humano da el OK a que esta verificación a mano sustituya la campaña del Bloque 4, y queda anotado en
   `progress/`.
