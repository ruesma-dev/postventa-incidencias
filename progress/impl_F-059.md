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

## Bloque 1 · El dominio · T1, T2, T3 · 2026-10-15

### T1 · Fase RED

Dos ficheros de tests (303 casos con la parametrización):

- `tests/test_f059_volcado_dominio.py`: `referencia_de` (R5); `parte_de`, `cuerpo_de_parte` y `cuerpo_de_lote`
  clave a clave, con `tipo` `"0002"` para `listado` `primero`, `segundo` y nulo y `causante: false` (R6, Q-1,
  Q-2, D-9, D-10); `huella_intacta` (R7); `seleccionar_para_ensayo` (R11, R27); `validar_ensayo` con 29:59 y
  30:00 (R17); `seleccionar_para_volcado` (R18, R20, R27); `interpretar_respuesta` con cada incoherencia de R22
  y las respuestas sin forma de R23 y R14; `todos_sin_respuesta`, `todos_no_procesados`, `posibles_duplicados`
  (R26), `clasificar_codigo_de_lote` (R14, R24), `resumen_de` (R12, R22), `validar_partes_por_llamada` (R30) y
  los ocho errores (§7).
- `tests/test_f059_estados.py`: `estado_de_volcado` y la tabla de §4.1 con su precedencia, §4.2,
  `es_candidata`, `candidata_de` que rechaza una `volcada`, `resumen` con seis estados, `activas` y los dos
  filtros nuevos (R1–R4, D-7, D-14), `SituacionDeRevision` construida sin `volcado`, y la convivencia con F-060
  (§21.5): `planificar_normalizacion`, importada sin tocarla, con una `volcada` y una `en_duda` normalizables, y
  `validar_quien` que rechaza `sistema:normalizar_ubicacion`.

Contra un **esqueleto neutro**, como en F-060: `domain/models/situacion_volcado.py` y
`domain/models/volcado.py` con los nombres y los tipos de `design.md` §7, las constantes a su valor neutro
(`""`, `0`, `None`, `timedelta(0)`) y todas las funciones con `raise NotImplementedError("F-059 T2")`.
`domain/models/revision.py` y `domain/models/errores.py` **no** se tocan en T1: los casos que construyen una
`SituacionDeRevision` con `volcado` fallan con `TypeError` y los que nombran uno de los ocho errores, con
`AttributeError`. Así ningún caso falla en la importación ni en la recogida.

Comando, lanzado desde un directorio de trabajo **sin `.env`** (`<scratchpad>/f059`, regla del líder) con las
rutas absolutas de los tests:

```
COLUMNS=400 <repo>/services/postventa-api/.venv/Scripts/python.exe -m pytest \
  <repo>/services/postventa-api/tests/test_f059_volcado_dominio.py \
  <repo>/services/postventa-api/tests/test_f059_estados.py -q -p no:cacheprovider --tb=no -rf
```

Resultado: **296 failed, 7 passed**. Por tipo de fallo: 217 `NotImplementedError` (el esqueleto), 53
`TypeError` (`SituacionDeRevision` aún sin `volcado`), 18 `AttributeError` (los errores aún no existen o
`volcado` no es atributo), 3 `AssertionError` (constantes neutras y los cuatro estados), 2 `ValueError`
(`EstadoRevision("volcada")`) y 3 `DID NOT RAISE` (el invariante de `SituacionDeVolcado`). Los **7 que pasan**
no dependen de lo que falta: cuatro fijan enumeraciones y campos que el esqueleto ya declara
(`test_f059_d10_el_parte_no_tiene_mas_campos_que_los_de_r6`, `test_f059_r32_los_estados_y_los_modos_de_un_evento`,
`test_f059_r11_r18_los_motivos_de_exclusion`, `test_f059_r1_los_dos_estados_de_volcado`) y tres caracterizan lo
de F-056 y F-060 que F-059 **no** cambia (`test_f059_r2_las_de_f056_no_cambian`,
`test_f059_r3_las_de_f056_que_no_son_aprobada_no_lo_son`, `test_f059_f060_r9_r15_el_sistema_no_puede_ensayar_ni_volcar`).

Salida real completa (solo se ha recortado el prefijo de la ruta hasta `services/postventa-api\`):

```
FFFFFFFFFFFFFF.FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF..FFFFFFFFFFFFFF.FFFFFFFFFFFFF.FFFFFFFFFFFFFFFFFFF.FFFFFFFFFFFF.                                                                                          [100%]
=========================================================================================================================================================================================== short test summary info ===========================================================================================================================================================================================
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_de_un_uuid_escrito_en_mayusculas_sale_en_minusculas - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_la_misma_incidencia_da_siempre_la_misma - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_solo_sale_de_un_uuid[00000000-0000-0000-0000-000000000001] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_solo_sale_de_un_uuid[1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_solo_sale_de_un_uuid[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_el_parte_clave_a_clave - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_las_constantes - AssertionError: assert '' == '0002'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_q1_el_tipo_es_0002_con_cualquier_listado[primero] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_q1_el_tipo_es_0002_con_cualquier_listado[segundo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_q1_el_tipo_es_0002_con_cualquier_listado[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_con_detalle_va_como_descripcion_larga - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_d9_sin_proveedor_no_hay_intervinientes - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_q2_el_interviniente_lleva_el_oficio_del_parte_y_no_es_causante - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_el_cuerpo_clave_a_clave - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_siempre_explicito[False] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_siempre_explicito[True] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_solo_booleano[1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_solo_booleano[0] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_solo_booleano[true] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_commit_solo_booleano[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_detalle_nulo_sin_la_clave_y_con_detalle_con_ella - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_cuerpo_de_parte_es_lo_que_va_en_el_lote - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_d9_sin_proveedor_la_lista_vacia - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_d10_ninguna_clave_de_mas - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_los_partes_en_el_orden_dado_y_el_cuerpo_es_json - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_de_1_a_50_partes_por_cuerpo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r6_ninguna_referencia_repetida_en_el_cuerpo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r7_la_huella_intacta - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r7_un_valor_cambiado_con_la_huella_vieja - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_las_candidatas_van_en_el_orden_pedido - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_de_la_bandeja - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_de_otra_obra - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_la_obra_se_mira_antes_que_lo_volcado - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_ya_volcada_con_su_codigo - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_r13_ya_volcada_por_un_idempotente_de_ensayo - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_candidata[editar] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_candidata[descartar] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_candidata[recuperar] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_candidata_si_la_situacion_no_lo_es_aunque_la_lista_la_traiga - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_no_es_candidata_si_la_lista_no_la_trae - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r7_r11_huella_no_coincide - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_las_excluidas_en_el_orden_pedido_y_las_demas_se_mandan - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r11_pedidas_repetidas - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_un_ensayo_vigente_vale - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_no_existe - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_de_otra_obra - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_de_otra_persona - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado0] - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado1] - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado2] - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_el_orden_obra_persona_caducidad - AttributeError: module 'domain.models.errores' has no attribute 'EnsayoNoValido'
FAILED tests\test_f059_volcado_dominio.py::test_f059_r17_las_constantes_y_los_motivos - assert datetime.timedelta(0) == datetime.timedelta(seconds=1800)
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_esta - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_revision_desactualizada_si_la_pedida_no_es_la_del_ensayo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r18_lo_del_ensayo_antes_que_lo_de_la_base - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_hay_otra_revision_despues_del_ensayo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[editar] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[descartar] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[recuperar] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_r27_ya_volcada_con_su_codigo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_ya_volcada_antes_que_la_revision - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado0] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado2] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado3] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r7_r20_huella_no_coincide - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_no_es_de_la_bandeja_si_no_se_pudo_bloquear - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_las_excluidas_en_el_orden_pedido - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r20_ninguna_elegible - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r15_pedidas_repetidas - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_rechazado_y_no_procesado_solo_con_el_codigo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_el_orden_de_la_lista_no_importa_si_cada_indice_trae_su_referencia - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_indices_cambiados_de_referencia_son_sin_respuesta - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_parte_que_no_vuelve_es_sin_respuesta_y_los_demas_valen - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_referencia_cambiada - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[previsto] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[enviado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[sin_respuesta] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[otro] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[CREADO] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[3] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_estado_que_no_es_de_los_cuatro[estado8] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[None-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[None-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[700001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[700001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[700001.0-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[700001.0-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[True-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[True-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[0-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[0-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[-5-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_ide_entero[-5-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[None-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[None-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/00011-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/00011-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[rs26.10/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[rs26.10/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS2610/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS2610/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26-10/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26-10/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/0001\n-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/0001\n-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[ RS26.10/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[ RS26.10/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[XRS26.10/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[XRS26.10/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS\uff12\uff16.10/0001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS\uff12\uff16.10/0001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/000\u0661-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/000\u0661-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[260001-creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_con_parte_sin_cod_bien_formado[260001-idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_un_cod_de_otro_mes_bien_formado_vale_y_el_ide_1_tambien - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[None-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[None-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo1-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo1-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo2-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo2-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo3-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo3-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo4-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo4-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo5-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo5-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo6-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo6-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo7-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo7-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo8-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo8-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo9-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo9-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[oficio_no_esta_en_la_obra-rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r35_sin_codigo_de_motivo_admisible[oficio_no_esta_en_la_obra-no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r35_el_codigo_de_motivo_de_64_y_con_cifras_vale - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[texto] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos3] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos4] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos5] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos6] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos7] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos8] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos9] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos10] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_dry_run_true_en_el_volcado - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_dry_run_false_en_el_ensayo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[partes0] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[partes1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[de_mas] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[indice_bool] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[indice_texto] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[indice_negativo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[indice_repetido] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_r23_de_mas_o_indices_imposibles[sin_indice] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_nunca_mira_committed[False] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_nunca_mira_committed[True] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_nunca_mira_committed[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_nunca_mira_committed[no se mira] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_sin_la_clave_committed_tambien - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_d13_el_previsto_sin_cod_ni_ide_provisionales_ni_filas - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r13_en_el_ensayo_idempotente_rechazado_y_no_procesado_valen - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_en_el_ensayo_un_estado_de_escritura_es_sin_respuesta[creado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_en_el_ensayo_un_estado_de_escritura_es_sin_respuesta[enviado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_en_el_ensayo_un_estado_de_escritura_es_sin_respuesta[sin_respuesta] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_el_idempotente_del_ensayo_tambien_exige_ide_y_cod - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r23_todos_sin_respuesta - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[escritura_reclamaciones_deshabilitada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[base_de_datos_no_permitida] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[lote_demasiado_grande] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[obra_no_encontrada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[usuario_no_valido] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[serie_no_encontrada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[estado_inicial_no_encontrado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[oficio_no_esta_en_la_obra] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[otro_codigo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[Solicitud invalida.] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_un_creado_con_otro_ide_es_un_posible_duplicado - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_con_el_mismo_ide_no_lo_es - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_solo_un_creado[idempotente] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_solo_un_creado[rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_solo_un_creado[sin_respuesta] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_sin_parte_anterior_no_lo_es - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r26_de_varios_solo_los_duplicados_y_en_su_orden - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_precondicion[escritura_reclamaciones_deshabilitada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_precondicion[base_de_datos_no_permitida] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_rechazo[lote_demasiado_grande] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_rechazo[obra_no_encontrada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_rechazo[usuario_no_valido] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_rechazo[serie_no_encontrada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_r24_los_de_rechazo[estado_inicial_no_encontrado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[oficio_no_esta_en_la_obra] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[OBRA_NO_ENCONTRADA] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[ obra_no_encontrada] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[None] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r14_un_codigo_desconocido_no_tiene_clase[5] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_el_resumen_del_ensayo - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r22_el_resumen_del_volcado - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[creado-ensayo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[sin_respuesta-ensayo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[enviado-ensayo] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[previsto-volcado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[enviado-volcado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_de_1_a_50[1] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_de_1_a_50[5] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_de_1_a_50[50] - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[0] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[51] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[-1] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[True] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[False] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[5] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[cinco] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[5.0] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_r30_n_fuera_de_rango_o_no_entero[None] - AttributeError: module 'domain.models.errores' has no attribute 'ConfiguracionDeVolcadoInvalida'. Did you mean: 'ConfiguracionPlantillaInvalida'?
FAILED tests\test_f059_volcado_dominio.py::test_f059_los_tipos_son_inmutables - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_los_ocho_errores_del_volcado - AttributeError: module 'domain.models.errores' has no attribute 'CuerpoDeVolcadoInvalido'. Did you mean: 'CuerpoDeArchivoInvalido'?
FAILED tests\test_f059_estados.py::test_f059_r1_sin_eventos_no_hay_estado_de_volcado - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_un_creado_deja_volcada - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_r13_un_idempotente_de_ensayo_deja_volcada - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_volcada_gana_a_lo_que_diga_el_ultimo[enviado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_volcada_gana_a_lo_que_diga_el_ultimo[sin_respuesta] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_volcada_gana_a_lo_que_diga_el_ultimo[rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_el_ultimo_enviado_o_sin_respuesta_deja_en_duda[enviado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_el_ultimo_enviado_o_sin_respuesta_deja_en_duda[sin_respuesta] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_el_ultimo_rechazado_o_no_procesado_no_cambia_nada[rechazado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_el_ultimo_rechazado_o_no_procesado_no_cambia_nada[no_procesado] - NotImplementedError: F-059 T2
FAILED tests\test_f059_estados.py::test_f059_r1_un_ultimo_con_parte_en_sigrid_exige_la_parte[creado] - Failed: DID NOT RAISE ValueError
FAILED tests\test_f059_estados.py::test_f059_r1_un_ultimo_con_parte_en_sigrid_exige_la_parte[idempotente] - Failed: DID NOT RAISE ValueError
FAILED tests\test_f059_estados.py::test_f059_r1_seis_estados_en_su_orden - AssertionError: assert ['nueva', 'ed... 'descartada'] == ['nueva', 'ed...a', 'en_duda']
FAILED tests\test_f059_estados.py::test_f059_r1_la_tabla_de_cuatro_uno - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_aprobada_y_en_duda[enviado] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_aprobada_y_en_duda[sin_respuesta] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_r27_aprobada_con_el_ultimo_resultado_rechazado_sigue_aprobada[rechazado] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_r27_aprobada_con_el_ultimo_resultado_rechazado_sigue_aprobada[no_procesado] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_aprobada_sin_eventos_sigue_aprobada - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_volcada_y_en_duda_ganan_a_descartada - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_volcada_gana_aunque_no_haya_revisiones - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r1_sin_volcado_los_cuatro_de_f056 - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_situacion_construida_sin_volcado_vale_none - AttributeError: 'SituacionDeRevision' object has no attribute 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_desde_volcada_y_en_duda_ninguna_accion[volcada] - ValueError: 'volcada' is not a valid EstadoRevision
FAILED tests\test_f059_estados.py::test_f059_r2_desde_volcada_y_en_duda_ninguna_accion[en_duda] - ValueError: 'en_duda' is not a valid EstadoRevision
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-editar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-editar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-descartar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-descartar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-aprobar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-aprobar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-recuperar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[True-recuperar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-editar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-editar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-descartar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-descartar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-aprobar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-aprobar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-recuperar-volcado0-volcada] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones[False-recuperar-volcado1-en_duda] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r27_una_aprobada_con_rechazo_se_edita - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r3_aprobada_y_en_duda_son_candidatas - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r3_una_volcada_no_es_candidata_nunca - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r3_en_duda_sin_un_aprobar_detras_no_es_candidata - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r3_r27_candidata_de_una_en_duda - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r3_candidata_de_rechaza_una_volcada - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_resumen_con_seis_estados - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_d7_activas_sin_descartada_ni_volcada - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_d7_sin_filtro_es_activas - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_los_dos_filtros_nuevos[volcada-esperado0] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_los_dos_filtros_nuevos[en_duda-esperado1] - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_todas_son_las_seis - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_r4_los_valores_del_filtro - AssertionError: assert ['activas', '... 'descartada'] == ['activas', '...cartada', ...]
FAILED tests\test_f059_estados.py::test_f059_f060_la_normalizacion_no_toca_una_volcada_ni_una_en_duda - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
FAILED tests\test_f059_estados.py::test_f059_f060_ni_aunque_la_ultima_revision_no_fuera_un_aprobar - TypeError: SituacionDeRevision.__init__() got an unexpected keyword argument 'volcado'
296 failed, 7 passed in 3.75s
```
