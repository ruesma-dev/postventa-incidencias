<!-- progress/impl_F-059.md -->
# F-059 · Volcado a Sigrid en el backend — Informe del implementer

Rama `feature/F-059-volcado-sigrid-backend`. Rigor **`critico`**.
Spec: `specs/F-059-volcado-sigrid-backend/` (aprobada por el humano el 2026-10-07; conciliada con `dev`
2d2efd7 el 2026-10-15, `design.md` §20 y §21; F-1 (a) y F-2 (a) decididas por el humano el 2026-10-15).

## Bloque 0 · Precondición · T0 · 2026-10-15

La rama y su commit de arranque (`a9c2475`) los hizo el líder. Anotación del implementer, con los dos
comandos de la verificación lanzados desde la raíz del repositorio:

```
$ git log --oneline -1 dev
2d2efd7 Merge: F-060 cierre (T35 M2, T36 documentación y done; init.sh 8173 passed)
$ git merge-base HEAD dev
2d2efd7ab6968510ed9e6f12d526c426115b421e
```

**Base fija: `2d2efd7`** (`dev` con F-056 y F-060 mergeadas). HEAD de la rama al empezar: `3673aca`.

Nombres de F-056 y F-060 contrastados con la tabla de `design.md` §21.2 sobre el código de la base: todos
coinciden (`candidatas_al_volcado(obra_codigo, *, revision)`; `CandidataAlVolcado` con `valores`;
`estado_de`, `acciones_posibles`, `es_candidata`, `candidata_de`, `resumen`, `_PERMITIDAS` y `_pasa` en
`domain/models/revision.py`; `_select_situaciones`, `fila_a_situacion`, `select_bloquear`,
`select_ultimas_revisiones` e `insert_revision` en `sentencias_revision.py`; `_registrar`, `registrar_lote`,
`_registrar_lote` y `aprobadas` en `repositorio_revision_pg.py`; `_fila`, `_filtro` y `listar_revision` en
`interface_adapters/api/revision.py`; `RevisionPort` con siete operaciones; `resolver_login_de_sigrid(usuarios,
erp: ErpPort, *, …)`; `construir_cliente_http`, `CORRECTOS`, `ENTORNOS_CON_CIERRE`, `ErrorDeSigrid`,
`es_transitorio`, `exigir_entorno_con_cierre`, `select_usuario`, `_exigir_configuracion`; `sigrid_timeout_s` = 35;
`_error_de_revision`; veintiuna rutas `ANONYMOUS` en `function_app.py`). Ninguno difiere: no hay motivo para
parar.
