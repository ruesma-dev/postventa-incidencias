<!-- progress/spec_F-059.md -->
# F-059 · Conciliación de la spec aprobada con `dev` 2d2efd7 — informe del spec-author

> **Fecha**: 2026-10-15. **Rama**: `feature/F-059-volcado-sigrid-backend`
> (base fija `2d2efd7`, arranque `a9c2475`). **Encargo**: conciliar con `dev`
> la spec aprobada el 2026-10-07 sobre f86d639, antes de F-056 (done
> 2026-10-09) y F-060 (done 2026-10-14). Sin reabrir decisiones (design §20).
> **Ficheros tocados**: los tres de `specs/F-059-volcado-sigrid-backend/` y
> este informe. Ni código, ni tests, ni `features.json`, `BACKLOG.md` o
> `progress/current.md`. En `azure-apps/`, solo lectura.

## Resultado

- **20 cambios mecánicos aplicados** (cuentas, nombres, rutas, números,
  estructura de módulos y orden de tareas que se derivan del código real sin
  tocar ninguna decisión, requisito ni contrato).
- **2 cambios de fondo**, **F-1** (R41 frente a los tests ajenos que el plan
  aprobado obliga a ampliar) y **F-2** (el objeto `volcado` también en la
  respuesta de `POST /api/revision/acciones`): **RESUELTOS** por el humano el
  2026-10-15, literal «a en las 2» → F-1 (a) y F-2 (a), **aplicadas** en un
  segundo commit (ver «Decisiones del humano» al final).
- Detalle técnico completo en `design.md` **§21** (nueva) y el resumen en §20.
- Requisitos tocados: R42 (la cifra) en la conciliación; R41 (bloque de
  excepciones) y R4 (la respuesta de la acción) por las decisiones del humano.

## Comprobaciones pedidas (puntos 1–7 del encargo)

| # | Punto | Resultado |
|---|---|---|
| 1 | Rutas anónimas | En `dev` son **21** (`function_app.py` y su cabecera, `test_f010_endpoints_protegidos.py`). Con las tres de F-059, **24**. Ajustado en R42, design §11/§17, tasks T13/T15/T20. Tests que citan la cuenta: inventario B de design §21.3 |
| 2 | `RevisionPort` con 7 operaciones | Confirmado (`registrar_lote` de F-060). F-059 **no añade ninguna** (lo suyo va en `RepositorioVolcadoPort`), así que `test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5` no se toca. `registrar_lote` ni se usa ni se cambia |
| 3 | Revisiones del sistema de F-060 | **Conviven sin cambios** (design §21.5): la normalización solo escribe sobre `nueva`/`editada` (lista permitida `ESTADOS_NORMALIZABLES`) y calcula el estado con el mismo `estado_de` que F-059 amplía; una `volcada` o `en_duda` tiene siempre como última revisión un `aprobar` (R2 impide cualquier otra después), así que tampoco sería normalizable como `aprobada`; ante una carrera, `_registrar_lote` salta por frescura bajo `FOR UPDATE`. Los tres bloqueos (`registrar`, `registrar_lote`, `anotar_enviados`) usan la misma `select_bloquear` en orden de `incidencia_id`: sin interbloqueos. `validar_quien` rechaza el literal del sistema como actor del volcado |
| 4 | Nombres reales de F-056 | Tabla completa en design §21.2. Todos casan con lo supuesto salvo detalles de ubicación: `candidatas_al_volcado` está en `application/pipelines/revision.py`; los valores de la candidata van en `candidata.valores`; las sentencias son una consulta común `_select_situaciones`; el paso de `registrar` es `_registrar`; el borde serializa con `_fila`/`_filtro`; `listar_revision` es ya pieza de F-060 |
| 5 | DDL `16_volcados_sigrid.sql` | **Libre**: el último es `15_revisiones_bandeja.sql`, F-060 no añadió DDL y ninguna otra rama/spec (F-038, F-040, F-057, F-058) reserva el 16. Tipos de las claves ajenas comprobados (`bigserial`, `uuid`) |
| 6 | Tests intocables y guardas | Inventario en design §21.3 (grupos A, B, C) y controles vigentes en §21.4. Ver F-1 |
| 7 | Variables, `infra/27_`/`28_`, §8.9 | `VOLCADO_HABILITADO` y `VOLCADO_PARTES_POR_LLAMADA` no existen en ningún fichero; `27_` y `28_` libres (el último es `26_`, luego `90_`); `azure-apps/sigrid_api.md` §8.9 **sin cambios** desde el 2026-10-07 (los commits posteriores al fichero, d066470 y abd1114, son de albaranes y facturas); la fila de §10 sigue diciendo «F-040» (Q-6 pendiente para el despliegue) |

## Cambios mecánicos aplicados

1. **Cuenta de anónimos 21 → 24** en R42, design §11 y §17, tasks T13, T15 y
   T20 («Los veinticuatro quedan en nivel», «Los veintiuno» fuera).
2. **Base fija `2d2efd7`** en la cabecera de tasks, en T0 (estado: rama y
   arranque hechos por el líder; falta la anotación en `impl_F-059.md`), en T22
   y en la línea de la campaña final.
3. **Nombres reales de F-056** (design §1, §5, §12 reescrita, §21.2): la tabla
   de §1 ya no dice que se amplían `CandidataAlVolcado` ni `huella_de_valores`
   (no se tocan, como dice F-060 §10.2), sino `EstadoRevision`, `FiltroEstado`,
   `SituacionDeRevision`, `estado_de`, `_PERMITIDAS`, `es_candidata` y `_pasa`.
4. **Módulo hoja `domain/models/situacion_volcado.py`** (design §7, §17; T1,
   T2): `revision.py` necesita `estado_de_volcado` y `volcado.py` necesita
   `CandidataAlVolcado` y `huella_de_valores`; en un solo módulo sería una
   importación circular.
5. **`SituacionDeRevision.volcado` como último campo con `None` por
   defecto** (design §12, §18; T1, T2): la construyen sin él los tests de F-056
   y F-060 y `tests/utiles_revision.py`.
6. **`RepositorioRevisionPostgres.aprobadas` filtra con `es_candidata` antes
   de `candidata_de`** (design §12, §18; T4): con la situación de volcado en la
   fila, una `volcada` en la obra haría fallar `candidata_de` (que exige
   `es_candidata`) y tumbaría `aprobadas`. Es lo que pide R3.
7. **`UltimoEvento` lleva el correo** (design §7): R4 pide `volcado_por` también
   para `en_duda`, `rechazado` y `no_procesado`.
8. **El bloqueo de `anotar_enviados` es `select_bloquear` de F-056**, importada
   (design §8.1); la última revisión con `accion` y huella, con sentencia
   propia; `select_bloquear`, `select_ultimas_revisiones` e `insert_revision`
   no cambian (las comparte `_registrar_lote`).
9. **R2 dentro de la transacción va en `_registrar`**, tras `select_bloquear`;
   `registrar_lote`/`_registrar_lote` no se tocan (design §12, §21.5).
10. **El borde**: `_fila` y `_filtro` cambian; `listar_revision` (pieza de
    F-060) no; `_error_de_revision` no; traducción de errores propia;
    `function_app.py` solo importa de `interface_adapters/api/volcado.py`, y
    nada nuevo carga `openpyxl`/`pymupdf`/`google.genai` (M-3 de F-060)
    (design §11, §12; T15).
11. **`RevisionPort` sin operación nueva** (design §12, §21.1).
12. **Convivencia con F-060 explícita** (requirements §0, design §4.1 y §21.5,
    T1 —test con `planificar_normalizacion` y `validar_quien`—, T7 —dos
    conexiones con `registrar_lote`—, T25 —la fila de prueba puede quedar
    `editada` tras importar—).
13. **DDL 16 confirmado libre** y tipos de claves ajenas (design §9, §21.1).
14. **`infra/27_`/`28_` y las dos variables, libres** (design §13, §21.1).
15. **§8.9 de `sigrid-api` sin cambios** (design §21.1).
16. **«No se toca» ampliado** con las piezas de F-060 y `tests/utiles_revision.py`;
    dobles de F-059 en un `tests/utiles_volcado.py` propio si hacen falta
    (design §17).
17. **Restricciones de las guardas que no dependen de `git`** (F-036, F-056,
    F-060), escritas para el implementer (design §12 al final, §21.4).
18. **Tests ajenos por bloque** (design §21.3; tasks T2, T4, T5, T6, T15, T16,
    T20): el grupo C de F-056 pasa a T2 (se pone rojo al crecer
    `EstadoRevision`), con la enmienda de la sección de F-056 de
    `ARCHITECTURE.md` adelantada de T20 a T2 (`test_f056_r44_nombra_cada_estado`);
    el A en T4/T5; el B en T15/T20; T8 añade `test_f060_bbdd_lote.py`. Las
    verificaciones de cada tarea incluyen esos tests. **Los que contradicen la
    letra de R41 quedan condicionados a F-1.**
19. **T16 con el patrón de `test_f060_alcance_cerrado.py`** (piezas por
    definición), `BASE_FIJA = "2d2efd7"` y la rama de F-059.
20. **Dos riesgos nuevos con datos de F-060/F-061** (design §19.13 y §19.14):
    los picos de 4–8 s de una lectura de `sigrid-api` antes de la llamada de
    lote (acercan la petición a los 45 s del proxy; ya cubierto por §6.2, Q-8 y
    R31), y las dos `LATERAL` nuevas en el listado que F-060 midió lento (misma
    consulta, por índice; F-061 lo vigila).

Y las notas «Conciliada con dev 2d2efd7 el 2026-10-15» en la cabecera de
`tasks.md`, en `design.md` §20 (con el resumen), en la cabecera de `design.md`
y en la de `requirements.md`.

## Cambios de fondo (resueltos el 2026-10-15: «a en las 2»)

### F-1 · R41 frente a los tests ajenos que el plan obliga a ampliar

**Qué pasa.** R41 dice que los tests de F-009, F-012, F-036 y F-053 siguen
**sin tocarse** y que los de F-056 solo se amplían donde fijan cuatro estados o
acciones. Con lo ya aprobado es imposible:

- El `16_…sql` (R32) pone rojos controles que no dependen de `git` y fijan la
  lista de `.sql`: de F-005, F-028, F-030, F-031, F-032, F-033, F-034,
  **F-036** (`test_f036_t14_…`), F-056 (`test_f056_r36_…` y
  `test_f056_r12_solo_15_declara_una_columna_de_correo`, por `actor_correo`) y
  F-060 (`test_f060_r37_los_sql_son_los_quince_de_antes`).
- La cuenta y la cabecera de `INTEGRACION.md` (R40, R42) ponen rojos
  **F-012** (`NUMERALES`), **F-053** (`CUENTA_VIGENTE`), F-019, F-056 y F-060
  (la cuenta y la cabecera «Última feature: F-060»).
- La clave `volcado` (R4) y el ancho de la fila cambian tests de F-056 fuera de
  «cuatro estados o acciones» (`CLAVES_DE_FILA`, filas falsas del repositorio).

Lista exacta, test a test, en `design.md` §21.3.

**Opciones.**

- **(a) Recomendada**: añadir a R41 un bloque «Excepciones, ampliando sin
  relajar» con la lista de §21.3, como hizo R45 de F-056; cada una declarada
  función a función en `test_f059_alcance_cerrado.py`, que vigila que no se
  pierde ninguna aserción. Es el criterio que el humano aprobó en F-056 y que
  el líder aplicó en F-060 (su design §12).
- (b) No hay una alternativa razonable: otro número de fichero no evita nada
  (las listas fijan los quince) y no contar las rutas contradiría R40.

**Bloquea**: T2 (grupo C fuera de la letra), T4/T5 (grupo A), T15/T20 (grupo B).

### F-2 · El objeto `volcado` en la respuesta de `POST /api/revision/acciones`

**Qué pasa.** R4 pide `volcado` en «cada incidencia» de `GET /api/revision`.
En el código, la fila del listado y la de la respuesta de la acción salen de
la misma función (`_fila`); el historial no la usa.

**Opciones.**

- **(a) Recomendada**: en las dos respuestas, por la función común. Es una
  clave añadida (F-038 ignora lo que no conoce) y la incidencia tiene una sola
  forma.
- (b) Solo en el listado: un parámetro en `_fila` o una segunda función, y dos
  formas de la misma incidencia.

**Bloquea**: T13/T15 (qué fija `test_f056_revision_http.py`).

## Observaciones sin cambio

- **No se propone** que `registrar_lote` gane la comprobación de R2 «por si
  acaso»: es inalcanzable por frescura (design §21.5) y tocaría una pieza de
  F-060.
- Q-6 sigue igual: la fila de F-040/F-059 de `azure-apps/sigrid_api.md` §10
  la actualiza el líder al desplegar (T24).
- La spec de F-040 (worktree `postventa-f040`) no necesita cambios por esta
  conciliación: el contrato de §11 no cambia; si el humano elige F-2 (a), la
  clave `volcado` le llega también en la respuesta de la acción.

## Para el líder

- Nada pendiente del humano en la spec: el Bloque 1 puede empezar.
- Commits locales: `F-059: spec conciliada con dev 2d2efd7 (F-056 y F-060)`
  (c469e74) y `F-059: F-1 (a) y F-2 (a) aplicadas en la spec (decisión del
  humano)`.

## Decisiones del humano (2026-10-15) y cómo se aplicaron

Literal del humano: **«a en las 2»** → F-1 (a) y F-2 (a).

- **F-1 (a)**, aplicada en: `requirements.md` R41 (bloque «Excepciones,
  ampliando sin relajar» con la lista test a test, como R45 de F-056: el
  `16_`, la cuenta 21 → 24 y la cabecera de `INTEGRACION.md`, los estados y la
  fila de F-056; F-009 sigue intacto); `design.md` §17 («A modificar»), §18
  (fila de R41), §20 (fila F-1), §21.3 y §21.6; `tasks.md` cabecera, T4, T16
  (la lista de excepciones, escrita a mano y función a función en
  `test_f059_alcance_cerrado.py`, que vigila que no se pierde ninguna
  aserción) y T20. T2 y T5 ya no llevaban condicionado explícito; T5 verifica
  el grupo A entero.
- **F-2 (a)**, aplicada en: `requirements.md` R4 (a); `design.md` §12 (`_fila`
  común, sin parametrizar ni duplicar; el historial no cambia), §18 (fila de
  R4), §20 (fila F-2) y §21.6; `tasks.md` cabecera, T13 (`CLAVES_DE_FILA` de
  `test_f056_revision_http.py` en el listado y en la respuesta de la acción) y
  T15.
