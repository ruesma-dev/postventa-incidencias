<!-- specs/F-072-tipo-reclamacion-sigrid/tasks.md -->
# F-072 · El tipo de reclamación sale de Sigrid (auxtrcp) de punta a punta — Tareas

> **Pendiente de aprobación** (decisiones Q-1..Q-11 en `design.md` §12). Rama
> `feature/F-072-tipo-reclamacion-sigrid`, en la carpeta principal. Rigor **`critico`**.
>
> **Base fija: `dev` `6994cb0`** (el implementer la anota en `progress/impl_F-072.md`
> al empezar el Bloque 1; la usan `test_f072_alcance_cerrado.py` y la mutación).
>
> RED con la traza **pegada** en `progress/impl_F-072.md` antes de cada GREEN;
> cobertura de las líneas cambiadas ≥ umbral de `init.sh`; **cero supervivientes**
> sin justificación aceptada por escrito por el humano. Un commit por tarea,
> `F-072 Tn: …`. **Un bloque por encargo, y parar**; review tras cada bloque.
> Cada bloque deja la suite en verde: los campos nuevos nacen con `None` por defecto.
>
> Nunca desde esta rama: escribir en Sigrid (ni `commit: true`, ni `sql/write`),
> DDL contra ninguna base, tocar `.env`, versionar `.xlsx`, ni meter en tests,
> informes o commits tipos, unidades, oficios o proveedores reales (ficticios:
> obras `99NN`, tipos `9001`…, «TIPO FICTICIO N»). **No se toca** lo de `design.md` §3.3.
>
> `pytest` desde `services/postventa-api` con `.venv/Scripts/python.exe -m pytest …`.
> Mutación de cada bloque: `python -m harness.mutacion --feature F-072 --base 6994cb0 --timeout 1800 --salida progress/mutacion_F-072_bloqueN.md`.

## Bloque 0 · Mediciones y decisiones (líder, solo lecturas)

- [x] **T0 · líder**: medir Q-1 (`SELECT cod, res, pos, fecbaj FROM dbo.auxtrcp ORDER BY pos, cod` por `sql/read` de `sigrid-api`), Q-2 (recuento por `listado` en `postventa.bandeja_incidencias` y en la última revisión de cada incidencia no volcada) y Q-3 (`tableowner` de `bandeja_incidencias` y `revisiones_bandeja` en `pg_tables` frente al rol de la Function), todo de solo lectura y sin datos personales en las notas; llevar al humano Q-1..Q-11 y escribir «Decidido» en `design.md` §12 con `spec_aprobada`. Si `0002` no está vigente o el rol no es dueño, **parar**. | Verificación: resultados y respuestas anotados en `progress/current.md`

## Bloque 1 · Dominio: tipos, tipo efectivo, huella y parte

- [x] **T1 · RED**: `tests/test_f072_dominio_tipos.py` (R6 etiquetas y orden de `tipos_del_desplegable`, `listas_con_tipos`, R19 `tipo_efectivo`, R26 huella con tipo nulo igual al literal medido con el código de `6994cb0` y con tipo al final) y `tests/test_f072_volcado.py` (R28: `parte_de` y `cuerpo_de_parte` con el tipo guardado y con nulo → `0002`; `TIPO_RECLAMACION` sigue siendo `"0002"`). | Verificación: los nuevos fallan por la razón esperada, traza pegada en `progress/impl_F-072.md`
- [x] **T2 · GREEN**: `domain/models/plantilla_incidencias.py` (`TipoReclamacion`, `TIPO_RECLAMACION_POR_DEFECTO`, `MAX_TIPO_RECLAMACION`, `tipos_del_desplegable`, `listas_con_tipos`, `tipo_efectivo`), `domain/models/revision.py` (solo `ValoresIncidencia.tipo_reclamacion = None` y `huella_de_valores`, `design.md` §4.2) y `domain/models/volcado.py` (alias y `parte_de`, §4.3). | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_dominio_tipos.py tests/test_f072_volcado.py tests/test_f056_revision_dominio.py tests/test_f059_volcado_dominio.py` en verde
- [x] **T3**: mutación del Bloque 1 y análisis de supervivientes en el informe. **Review del Bloque 1.** | Verificación: `progress/mutacion_F-072_bloque1.md`; `bash harness/init.sh` en verde

## Bloque 2 · Dominio de la revisión

- [x] **T4 · RED**: `tests/test_f072_revision_dominio.py`: R21 (vigente exacto, el efectivo que ya tiene aunque esté de baja, otro → error en `listado` sin repetir lo recibido), R22 (nulo → `0002`), R23 (copia de `listado` heredado en las cuatro acciones y en la del sistema de F-060; aprobar, descartar, recuperar y la del sistema copian el tipo), R24 (motivo `tipo_fuera_de_sigrid` en su sitio del orden, no aprobable), R25 (nulo → `0002` no es cambio). | Verificación: fallan por la razón esperada, traza pegada
- [x] **T5 · GREEN**: `domain/models/revision.py` según `design.md` §4.2 (`validar_valores`, `TIPO_NO_VALIDO`, `MotivoNoAprobable`, `motivos_no_aprobable` con los códigos vigentes, `cambios`); las aserciones de F-056/F-060 que cambien, citadas con su R. | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_revision_dominio.py tests/test_f056_revision_dominio.py tests/test_f060_normalizacion_dominio.py tests/test_f060_pipeline_normalizacion.py` en verde
- [x] **T6**: mutación del Bloque 2 y supervivientes. **Review del Bloque 2.** | Verificación: `progress/mutacion_F-072_bloque2.md`; `bash harness/init.sh` en verde

## Bloque 3 · La lectura de Sigrid

- [x] **T7 · RED**: `tests/test_f072_lectura_sigrid.py`: R2 (SQL carácter a carácter, sin parámetros), mapeo de 3 columnas y `ValueError` sin la fila, adaptador con `httpx` simulado (cuerpo de `sql/read`, techo), R3 (fallo y tiempo agotado → `CatalogoNoDisponible`), R4 (techo → `CatalogoSinVerificar`), R5 (vacíos y repetidos), R30 (la línea de log sin `res`), y la fábrica con la misma puerta de entorno que `construir_ubicaciones_validas`. | Verificación: fallan por la razón esperada, traza pegada
- [x] **T8 · GREEN**: `domain/ports/tipos_reclamacion.py`, `infrastructure/sigrid/consultas_tipos_reclamacion.py`, `infrastructure/sigrid/tipos_reclamacion.py`, `construir_tipos_reclamacion` en `infrastructure/sigrid/fabrica.py` y `application/pipelines/tipos_reclamacion.py` (`design.md` §3.1, §5, §6.1). | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_lectura_sigrid.py tests/test_f056_ubicaciones.py` en verde
- [ ] **T9**: mutación del Bloque 3 y supervivientes. **Review del Bloque 3.** | Verificación: `progress/mutacion_F-072_bloque3.md`; `bash harness/init.sh` en verde

## Bloque 4 · DDL y persistencia

- [x] **T10 · RED**: `tests/test_f072_ddl.py` (R16: las dos sentencias pasan `cargar_ddl` con el esquema por defecto y con otro; R18: ni `listado`, ni `UPDATE`/`DELETE`/`DROP`/`ALTER COLUMN`; `13_`, `15_`, `16_` sin cambios frente a la base fija) y `tests/test_f072_persistencia.py` (R15 en el `INSERT` de la bandeja: `tipo_reclamacion` y `listado` a `NULL`; la columna en la foto de la revisión, escrita y leída; nulo leído como nulo). | Verificación: fallan por la razón esperada, traza pegada
- [x] **T11 · GREEN**: `infrastructure/persistencia/sql/17_tipo_reclamacion.sql` (`design.md` §7), `sentencias_bandeja.py`, `sentencias_revision.py` (§6.2) y `tipo_reclamacion = None` en `IncidenciaValida` e `IncidenciaEnBandeja` (`domain/models/importacion.py`, solo los campos). | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_ddl.py tests/test_f072_persistencia.py tests/test_f005_ddl_seguro.py tests/test_f036_ddl.py tests/test_f056_ddl.py tests/test_f036_repositorio_bandeja.py tests/test_f056_repositorio_revision.py` en verde
- [x] **T12**: `tests_bbdd/tests/test_f072_bbdd_tipo.py`: DDL dos veces sobre una base con filas de F-036 y F-056 (R17), filas existentes con tipo nulo, el `CHECK` de 1 a 24, nada en `public`, y escritura y lectura de una fila de bandeja y de una revisión con tipo. | Verificación: `.venv/Scripts/python.exe -m pytest --collect-only tests_bbdd/tests/test_f072_bbdd_tipo.py` recoge sin errores
- [ ] **T13 · MANUAL (humano)**: con Docker Desktop arrancado, `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`; deben pasar `test_f072_bbdd_tipo.py` y los de F-036, F-056, F-059 y F-060. | Verificación: MANUAL (humano) — salida anotada en `progress/impl_F-072.md`
- [ ] **T14**: mutación del Bloque 4 y supervivientes. **Review del Bloque 4.** | Verificación: `progress/mutacion_F-072_bloque4.md`; `bash harness/init.sh` en verde

## Bloque 5 · Plantilla e importación

- [x] **T15 · RED**: `tests/test_f072_plantilla.py` (R6 y R7 sobre el `.xlsx` generado y abierto con `openpyxl`; R8 cabecera, hojas y versión 2; R9 YAML real sin `listados` y uno roto en `tmp_path`; R10 textos ≤ 32/255 y ejemplos sin validar `Listado`; R1 y R3/R4 en la descarga, con dobles) y `tests/test_f072_importacion.py` (R11 orden y número de lecturas, ninguna con `ya_importado`; R12 casado y código guardado; R13 «Primer listado» de una v2 anterior → Excel de errores con la lista nueva; R14 blanco → `0002`; R15). | Verificación: fallan por la razón esperada, traza pegada
- [x] **T16 · GREEN**: `config/plantilla_incidencias.yaml` (§6.3), `infrastructure/documentos/plantilla_yaml.py`, `application/pipelines/plantilla.py`, `contexto_importacion.py`, `paso_importacion.py`, `validar_filas` en `domain/models/importacion.py`, `interface_adapters/api/plantilla.py` e `importar.py` (§3.2); aserciones de F-036/F-071 que cambien, citadas con su R. | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_plantilla.py tests/test_f072_importacion.py tests/test_f071_generador.py tests/test_f071_configuracion.py tests/test_f071_dominio_importacion.py tests/test_f071_pipelines.py tests/test_f071_http.py tests/test_f036_importar_http.py` en verde
- [ ] **T17**: mutación del Bloque 5 y supervivientes. **Review del Bloque 5.** | Verificación: `progress/mutacion_F-072_bloque5.md`; `bash harness/init.sh` en verde

## Bloque 6 · La revisión: aplicación y HTTP

- [ ] **T18 · RED**: `tests/test_f072_revision_http.py` (R1 en listar, editar y aprobar, una lectura cada uno; R27 descartar y recuperar sin leer; R20 `catalogo.listados` y `listado` efectivo en `valores` e `importados`; R21/R22 por `POST /api/revision/acciones`; R24 el motivo en la fila; R3/R4 → 503/409 sin escribir; `GET /api/bandeja` con el tipo efectivo) y en `tests/test_f072_volcado.py` R29 (un `tipo_no_valido` simulado de la pasarela sale `rechazado` con su motivo y el volcado no lee tipos). | Verificación: fallan por la razón esperada, traza pegada
- [ ] **T19 · GREEN**: `application/pipelines/revision.py` (`tipos` en `listar_para_revisar` y `aplicar_accion`), `interface_adapters/api/revision.py` y `bandeja.py` (§8); `function_app.py` solo docstrings si hace falta. | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_revision_http.py tests/test_f072_volcado.py tests/test_f056_pipeline_revision.py tests/test_f056_revision_http.py tests/test_f036_bandeja_http.py` en verde
- [ ] **T20**: mutación del Bloque 6 y supervivientes. **Review del Bloque 6.** | Verificación: `progress/mutacion_F-072_bloque6.md`; `bash harness/init.sh` en verde

## Bloque 7 · Documentación, alcance y cierre del código

- [ ] **T21**: `docs/ARCHITECTURE.md` (sección «El tipo de reclamación (F-072)» y las frases «tipo 0002 siempre» de F-059) y `docs/INTEGRACION.md` (R33); `tests/test_f072_documentacion.py` y `tests/test_f072_alcance_cerrado.py` (R31, R32 contra la base fija); los dos en `ejecutar_siempre` de `api` en `harness/servicios.json`. | Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f072_documentacion.py tests/test_f072_alcance_cerrado.py tests/test_f059_documentacion.py tests/test_f071_documentacion.py` en verde
- [ ] **T22**: `bash harness/init.sh` en verde con la cobertura en `[OK]` (el líder valida además el cierre sin caché, `ARNES_SIN_CACHE=1`, como manda `harness/servicios.json`); campaña de mutación de la feature entera (`--salida progress/mutacion_F-072.md`) sin supervivientes sin justificar. **Review final.** | Verificación: `bash harness/init.sh` en verde; `progress/mutacion_F-072.md` al día

**Parar. Review final APPROVED antes del Bloque 8.**

## Bloque 8 · Despliegue y verificación en producción

- [ ] **T23 · líder**: merge normal de la rama a `dev` desde un worktree aparte; el push, el humano. | Verificación: `git log dev` con el merge; `bash harness/init.sh` en verde en `dev`
- [ ] **T24 · MANUAL (humano)**: publicar el backend desde una copia limpia de `dev`, en la raíz del repositorio principal: `git worktree add --detach ..\postventa-publicar dev`, `powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1`, `git worktree remove ..\postventa-publicar`. El DDL se aplica al arrancar: comprobar que la Function levanta (`GET /api/health`). Si algo falla, publicar el commit anterior igual. | Verificación: MANUAL (humano) — commit publicado y arranque anotados en `progress/impl_F-072.md`
- [ ] **T25 · líder**: `git -C C:\Users\pgris\PycharmProjects\azure-apps pull`; poner al día `postventa_incidencias.md` (columnas, lectura de `auxtrcp`, «mandamos el tipo elegido; en blanco `0002`») y la fila de consumidores de §8.9 en `sigrid_api.md`; commit local (push, el humano, con `pull` antes). | Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1`
- [ ] **T26 · MANUAL (humano)**: en la 0677, sin datos personales en las notas y **nada en Sigrid** (Q-10): (1) descargar la plantilla desde `importar.html`: el desplegable `Listado` trae los vigentes medidos en T0, en su orden y con `<res> (<cod>)`; (2) `bandeja.html?obra=0677`, Red → `/api/revision`: `catalogo.listados` igual y ningún `valores.listado` nulo; anotar el tiempo frente al de antes; (3) importar tres filas «PRUEBA F-072 - DESCARTAR»: A con `Listado` en blanco, B con un tipo ≠ `0002`, C con «Segundo listado» pegado → `parcial`, C vuelve en el Excel de errores, A entra con `0002` y B con su código; (4) editar A y ponerle el tipo de B: el historial marca `listado`; (5) aprobar B y **ensayar** desde el panel de volcado (ventana cerrada, sin volcar): el `envio` lleva el código de B y el parte sale `previsto`; la línea `F-072 tipos de reclamación leídos` de Application Insights sin `res`; (6) descartar A y B. | Verificación: MANUAL (humano) — los seis pasos anotados con su resultado real en `progress/impl_F-072.md`
- [ ] **T27 · líder**: `progress/history.md`, `progress/current.md`; F-072 a `done` solo con T28 en verde y la review final APPROVED; en F-040, `blocked_by` al día (T5.4 ya puede hacerse; los textos del front de Q-11 van con ella). | Verificación: `python harness/backlog.py --comprobar` sin diferencias
- [ ] **T28**: Ejecutar `bash harness/init.sh` en verde. | Verificación: `bash harness/init.sh`
