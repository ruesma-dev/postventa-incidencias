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

Salida real completa (solo se ha recortado el prefijo de la ruta hasta `services/postventa-api\`, y se ha
redactado **un** id de caso parametrizado, que era el texto de `UUID(int=1)`: un GUID literal en el repositorio
lo rechaza la guardia R26 de F-006. Desde T2 ese caso lleva `ids` y ya no sale en ninguna traza):

```
FFFFFFFFFFFFFF.FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF..FFFFFFFFFFFFFF.FFFFFFFFFFFFF.FFFFFFFFFFFFFFFFFFF.FFFFFFFFFFFF.                                                                                          [100%]
=========================================================================================================================================================================================== short test summary info ===========================================================================================================================================================================================
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_de_un_uuid_escrito_en_mayusculas_sale_en_minusculas - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_la_misma_incidencia_da_siempre_la_misma - NotImplementedError: F-059 T2
FAILED tests\test_f059_volcado_dominio.py::test_f059_r5_solo_sale_de_un_uuid[<id redactado: era el texto de UUID(int=1); ver nota>] - NotImplementedError: F-059 T2
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

### T2 · GREEN

**Ficheros tocados** (todos en `services/postventa-api/` salvo el último):

| Fichero | Qué |
|---|---|
| `domain/models/situacion_volcado.py` (nuevo) | El módulo **hoja** de §7: `ModoVolcado`, `EstadoEvento`, `EstadoVolcado`, `ESTADOS_CON_PARTE`, `ESTADOS_EN_DUDA`, `ParteEnSigrid`, `UltimoEvento`, `SituacionDeVolcado` (con su invariante) y `estado_de_volcado` (§4.1). No importa nada de `revision.py` |
| `domain/models/volcado.py` (nuevo) | Las constantes, los tipos y las funciones de §7 (R5–R7, R11, R12, R14, R17, R18, R20, R22–R27, R30); reexporta lo de la hoja |
| `domain/models/errores.py` | Los ocho errores de §7, al final, con su párrafo en la cabecera del módulo; `from uuid import UUID` para la anotación de `VolcadoSinRespuesta.en_duda` |
| `domain/models/revision.py` | Los cambios de §12 y nada más: `EstadoRevision` + `VOLCADA`, `EN_DUDA`; `FiltroEstado` + los dos; `_PERMITIDAS` → `()` para los dos; `_FUERA_DE_ACTIVAS` (D-7) y `_CANDIDATOS` (R3); `SituacionDeRevision.volcado` como último campo con `None` por defecto; `estado_de` con la precedencia de §4.1; `es_candidata` → última `aprobar` **y** estado `aprobada` o `en_duda` (con ello `candidata_de` rechaza una `volcada`); `_pasa` con `_FUERA_DE_ACTIVAS`. `resumen` sale solo (recorre `EstadoRevision`) |
| `tests/test_f056_revision_dominio.py`, `test_f056_paginacion.py`, `test_f056_pipeline_revision.py`, `test_f056_revision_http.py` | Ampliados sin quitar casos (abajo, uno a uno) |
| `docs/ARCHITECTURE.md` | La enmienda de la sección de F-056, adelantada de T20 (abajo) |

Nada más: ni `RevisionPort`, ni `normalizacion.py`, ni `interface_adapters/`, ni `function_app.py`, ni ningún
otro test ajeno.

#### Decisiones de diseño (para la review del Bloque 1)

`design.md` §7 da los nombres y la responsabilidad de cada función, no todas las firmas. Estas son las que fijan
los tests y las que he completado; ninguna cambia un requisito, y las dos primeras se señalan porque condicionan
los Bloques 2 y 4:

1. **`seleccionar_para_ensayo(pedidas, candidatas, situaciones, *, obra)` recibe `situaciones` como
   `Mapping[UUID, SituacionDeRevision]`** (el tipo de F-056, que desde T2 lleva `volcado`), no como
   `Mapping[UUID, SituacionDeVolcado]`. Motivo: R11 distingue `no_es_de_la_bandeja`, `de_otra_obra` y
   `no_es_candidata`, y `SituacionDeVolcado` no dice ni si la incidencia está en la bandeja ni de qué obra es.
   Con la `SituacionDeRevision` de cada pedida (ausente → no es de la bandeja; `obra_codigo`; `es_candidata`;
   `volcado`) la función decide sola y pura. En el Bloque 4 la aplicación la obtiene con la operación existente
   `RevisionPort.situacion`, que en T6 gana la situación de volcado (`select_situacion` usa
   `_select_situaciones`), sin tocar el puerto; `candidatas` sigue siendo `candidatas_al_volcado` (R11 lo dice
   así), y la función exige las dos cosas: estar en la lista **y** ser candidata en su situación. Si la review
   prefiere otra fuente, solo cambia el tipo de ese parámetro.
2. **`interpretar_respuesta(mandados, datos, *, modo)` devuelve `None` si la respuesta entera no tiene la forma
   de §8.9**, y una tupla de resultados (con `sin_respuesta` donde algo no cuadra) si la tiene. El `modo` hace
   falta porque lo válido cambia: `previsto` vale en un ensayo y es incoherente en un volcado; `creado`, al
   revés; y `dry_run` tiene que ser el del modo. El `None` es lo que permite a la aplicación distinguir R23
   (toda la llamada sin respuesta: `todos_sin_respuesta` y 502) de R22 (partes sueltos `sin_respuesta` en una
   200). Cómo he leído los casos de §18: «desordenados» = cada `indice` con la referencia de otro → esos dos
   `sin_respuesta` (la posición en la lista da igual: se empareja por el campo `indice`, que `sigrid-api`
   numera desde 0 con `enumerate`, comprobado en su código); «de menos» → el que falta `sin_respuesta` y los
   demás valen (R22 literal); «de más» —un elemento que no es un objeto, sin `indice` entero, fuera de rango o
   repetido— → `None`, porque una respuesta con partes que no se pueden atribuir no es la de lo mandado. Las
   dos salidas acaban en `sin_respuesta`, que es lo conservador: deja `en_duda` y el reintento es seguro.
3. Un `rechazado` o `no_procesado` **sin un código de motivo admisible** (`[a-z0-9_]{1,64}`, lo que cabe en
   `motivo_codigo` y nada que pueda ser texto libre) es `sin_respuesta`: no se inventa un código ni se guarda el
   `mensaje` (R35). Un `creado`/`idempotente` exige `ide` entero ≥ 1 (ni `bool` ni `float`).
4. `PATRON_COD_PARTE` es `RS[0-9]{2}\.[0-9]{2}/[0-9]{4}` con `fullmatch`, no el `^RS\d{2}\.\d{2}/\d{4}$` de §7:
   en Python `\d` admite cifras de cualquier alfabeto y `$` deja pasar un salto de línea final (hay un test de
   cada uno). Es más estricto, no menos.
5. `clasificar_codigo_de_lote` devuelve `None` para un código que no es de los siete de §8.9 (§7 solo nombra
   dos clases): la aplicación lo tratará como respuesta que no se entiende. `todos_no_procesados` se niega a
   guardar un código que no es de lote (R35).
6. `resumen_de(resultados, excluidas, *, modo)` da las claves de §11 en su orden y se niega a contar un estado
   que no es del modo (los recuentos tienen que sumar lo mandado).
7. `seleccionar_para_volcado`: primero lo del ensayo (R18: `fuera_del_ensayo`, `revision_desactualizada` frente
   a la pedida) y después lo de la fila bloqueada (R20: `no_es_de_la_bandeja`, `ya_volcada` con su código,
   `revision_desactualizada` si la última ya no es la del ensayo o no es `aprobar`, `huella_no_coincide`); lo
   mandado sale en el orden del ensayo (R21). La huella de R20 es la guardada en la última revisión frente a
   la del ensayo; la de R7 recalculada sobre los valores (`huella_intacta`) es la de la candidata con la que la
   aplicación reconstruye los partes (§10, Bloque 4).
8. Tipos y funciones que §7 no nombra y hacen falta: `EstadoVolcado`, `ESTADOS_CON_PARTE`, `ESTADOS_EN_DUDA`
   (hoja); `ClaseDeCodigoDeLote`, `CODIGOS_DE_PRECONDICION`, `CODIGOS_DE_RECHAZO`, `PATRON_CODIGO_MOTIVO`,
   `PedidaAlVolcado`, `SituacionBloqueada` (lo que lee la escritura anticipada), `Excluida`, `Seleccion`,
   `PosibleDuplicado` y `cuerpo_de_parte` (el cuerpo de un parte, que `cuerpo_de_lote` usa y del que T15
   sacará el `envio` de R12).
9. Errores: `EnsayoNoValido(motivo, *, causa)`, `VolcadoRechazadoPorLaPasarela(motivo, *, codigo_pasarela)`,
   `VolcadoSinRespuesta(motivo, *, en_duda)`; los demás, solo con `motivo`. Ninguno repite `oid`, correo ni
   texto recibido.
10. `SituacionDeVolcado` no se puede construir con un último evento `creado`/`idempotente` y sin parte: el
    parte sale de esos mismos eventos.
11. `es_candidata` exige las dos cosas —última `aprobar` y estado en `_CANDIDATOS`—: en datos coherentes la
    primera ya implica `aprobada`, `en_duda` o `volcada`, pero así una `en_duda` cuya última revisión no fuera
    un `aprobar` (imposible según §4.1) no se da por candidata con valores no aprobados.
12. `validar_partes_por_llamada` solo admite un `int` (ni `bool`, ni `"5"`): cómo llega el valor de los ajustes
    es de T11.

**Una observación para T15 (no se toca aquí).** El ejemplo de respuesta del ensayo de `design.md` §11 enseña
`"descripcion_larga": null` dentro de `envio`, mientras que R6 dice que sin detalle la clave **no va** y R12
que `envio` son «los campos de R6 que se han mandado». `cuerpo_de_parte` sigue a R6 (sin la clave); cómo se
presenta `envio` lo decide T15 contra la spec.

#### Tests ajenos ampliados, uno a uno (R41, F-1 (a); grupo C de `design.md` §21.3)

Se pusieron rojos al aplicar T2 exactamente estos 15 casos, todos del grupo C, y ninguno más de la suite
(abajo, la suite entera):

| Test | Por qué rojo | Ampliación (sin quitar nada) |
|---|---|---|
| `test_f056_revision_dominio.py` — constantes `PERMITIDAS` y `SITUACIONES`, que usan `test_f056_r2_acciones_posibles_de_cada_estado` (2 rojos) y `test_f056_r2_las_dieciseis_casillas` (8 rojos) | Los dos parametrizan con `list(EstadoRevision)`, que ahora tiene seis | `PERMITIDAS` + `E.VOLCADA: ()`, `E.EN_DUDA: ()`; `SITUACIONES` + `sit_volcada` y `sit_en_duda` (dos ayudantes nuevos sobre `sit_aprobada`). Las «dieciséis casillas» pasan a ser veinticuatro con el mismo nombre de función: las ocho nuevas exigen 409 con `acciones: []` |
| `test_f056_paginacion.py::test_f056_r23_filtros_de_estado` | La lista exacta de `FiltroEstado` | + `"volcada"`, `"en_duda"` al final |
| `test_f056_paginacion.py::test_f056_r27_resumen_sobre_todas_las_filas` | `por_estado` con cuatro claves | + `E.VOLCADA: 0`, `E.EN_DUDA: 0` |
| `test_f056_pipeline_revision.py::test_f056_r27_resumen_de_toda_la_obra_y_pagina_filtrada` | Ídem | + las dos a cero |
| `test_f056_revision_http.py::test_f056_r27_la_respuesta_lleva_lo_de_r27` | `por_estado` del listado | + `"volcada": 0`, `"en_duda": 0` |
| `test_f056_documentacion.py::test_f056_r44_nombra_cada_estado` (2 rojos: `volcada`, `en_duda`) | Exige que la sección de F-056 de `ARCHITECTURE.md` nombre cada `EstadoRevision` | **El test no se toca**: se enmienda el documento (párrafo «Enmienda de F-059 (2026-10-15): seis estados» al final de «La revisión es una tabla append-only, y el estado se deriva») |

Cada línea añadida en los tests lleva el comentario `F-059 (R41, F-1 (a); design.md §21.3 C)`. Del grupo C,
**el mensaje de `_filtro`** de `test_f056_revision_http.py` **no** se pone rojo en T2: es un literal de
`interface_adapters/api/revision.py`, que no cambia hasta T15 (allí se ampliará el test, con la función que lo
fija). `test_f056_repositorio_revision.py` es de T4/T6.

#### Verificación

La de `tasks.md` T2, lanzada desde `<scratchpad>/f059` (sin `.env`) con las rutas absolutas:

```
.venv/Scripts/python.exe -m pytest tests/test_f059_volcado_dominio.py tests/test_f059_estados.py \
  tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py tests/test_f056_pipeline_revision.py \
  tests/test_f056_revision_http.py tests/test_f056_documentacion.py tests/test_f060_normalizacion_dominio.py \
  tests/test_f060_pipeline_normalizacion.py tests/test_f005_arquitectura.py -q -p no:cacheprovider
1144 passed in 28.11s
```

Antes de ampliar los tests ajenos, la misma orden daba **15 failed, 1129 passed**: los 15 casos de la tabla de
arriba y ninguno más.

**La suite entera del servicio** (`pytest tests -q`, desde el mismo directorio sin `.env`): **2 failed, 8425
passed, 129 skipped in 1563.18s**. Los dos rojos eran de la guardia R26 de F-006
(`test_f006_arquitectura.py::test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador` y
`test_f006_repo_sin_identificadores.py::test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador`):
yo había escrito en `test_f059_volcado_dominio.py` la forma canónica de `UUID(int=0xABCDEF)` como texto, y el id
de un caso parametrizado (el texto de `UUID(int=1)`) salía en la traza RED pegada arriba. Corregido **en mis
ficheros** —la forma canónica se compone por partes (`CANONICO_ABCDEF`), el caso lleva `ids` y el id se ha
redactado en la traza, con nota— sin tocar la guardia; tras ello, las dos guardias y los dos ficheros de F-059:
**369 passed in 39.93s**. El GUID sintético queda en el commit de T1 (`ffaf804`), que no es un identificador
real (es `UUID(int=…)` escrito en hexadecimal); lo digo para que conste.

`ruff check` sobre `domain/` y los tests de F-059: sin avisos (lanzado desde la raíz, con la configuración de
`init.sh`; lanzado desde `services/postventa-api` reordena los imports de forma distinta y lo deshice).

### T3 · Mutación del bloque · 2026-10-15/16

#### La campaña de la herramienta

```
python -m harness.mutacion --feature F-059 --base 477e596 --timeout 1800 --salida progress/mutacion_F-059_bloque1.md
85 mutantes evaluados, 85 muertos, 0 supervivientes, 0 timeouts en 13042.6 s
```

Base `477e596` (el commit de T0, el anterior a T1); alcance: 1084 líneas de producción en `errores.py` (120),
`revision.py` (44), `situacion_volcado.py` (127) y `volcado.py` (793); **8 workers** (los de `harness/rigor.json`),
sobre `HEAD` `e0e93db`. Informe completo: `progress/mutacion_F-059_bloque1.md`.

**Cómo se llegó ahí** (para que conste, sin maquillar):

1. Una primera campaña, lanzada sobre `c84e979` (T2), la **paré** a los 48 de 85 (30 muertos, 18 `timeout`):
   la máquina tenía a la vez otras dos campañas de mutación de otros proyectos (`partes` F-046 y `porcentajes`
   F-055, que no toqué) y cada suite de 8 workers pasaba de los 1800 s; con el repaso en serie de los `timeout`
   le quedaban más de 10 h. Además, para entonces la reverificación (abajo) ya había encontrado seis
   supervivientes y el código que la campaña evaluaba dejaba de ser el final. Al pararla quedaron cinco
   `pytest` huérfanos de **esa** campaña (venv de este proyecto, padre muerto), que terminé, y sus ocho
   worktrees, que retiré (`git worktree remove --force` y `prune`; ninguno queda).
2. Con el test de T3 en `e0e93db`, la campaña se relanzó con el mismo comando y terminó limpia: la de arriba.
3. **Un incidente mío**: una reverificación que lancé sobre el **árbol de trabajo** se cortó a mitad y dejó
   aplicado un mutante en `volcado.py` (`2 <= n` en `validar_partes_por_llamada`), sin commit. El líder lo vio;
   lo devolví a `1 <= n` con `git checkout` antes de nada, y desde entonces los mutantes a mano y la
   reverificación se hicieron en un **worktree desechable** de `e0e93db` (retirado al terminar). El árbol de
   trabajo no se volvió a mutar.

#### Reverificación de cada mutante de la herramienta contra los tests de F-059 solos

La herramienta da por muerto un mutante si falla **cualquier** test de la suite (con `-x`), y no dice cuál.
Para saber qué test de F-059 caza cada uno, apliqué los 85 mismos mutantes —con `generar_mutantes` y
`aplicar_mutante` de la propia herramienta y el mismo alcance— y ejecuté solo `test_f059_volcado_dominio.py` y
`test_f059_estados.py`; si alguno sobrevivía, además los de F-056 y F-060 del bloque.

- Sobre `c84e979` (T2): **79 de 85** muertos por F-059 y **6 supervivientes**, todos `frozen=True → False` en
  tipos cuya inmutabilidad no fijaba ningún test (`ParteEnSigrid`, `UltimoEvento`, `SituacionDeVolcado`,
  `Interviniente`, `Seleccion`, `PosibleDuplicado`); tampoco los cazaba ningún test de F-056 ni de F-060 del
  bloque. **Hallazgo**: en la primera campaña la herramienta había dado por **muerto** el de `PosibleDuplicado`
  (`volcado.py:320`): lo tumbó algún otro test de la suite, o un fallo bajo carga, no un test que lo vigile.
- **Test nuevo** (`e0e93db`): `test_f059_los_tipos_son_inmutables` gana esos seis tipos. Con él, los 13
  mutantes `frozen` del alcance mueren por ese test (`DID NOT RAISE FrozenInstanceError`).
- Sobre `e0e93db`: **85 de 85** muertos por tests de F-059. La tabla:

Mutantes generados por la herramienta en el alcance: **85**.

| # | Línea | Operador | Original → mutado | Con los tests de F-059 solos | Primer test que lo caza |
|---|---|---|---|---|---|
| 1 | `domain/models/revision.py:950` | logico | `and estado_de(situacion) in _CANDIDATOS → or estado_de(situacion) in _CANDIDATOS` | muerto (F-059) | `test_f059_r3_una_volcada_no_es_candidata_nunca` |
| 2 | `domain/models/revision.py:1072` | logico | `if filtro is FiltroEstado.ACTIVAS and fila.estado in _FUERA_DE_ACTIVAS: → if filtro is FiltroEstado.ACTIVAS or fila.estado in _FUERA_DE_ACTIVAS:` | muerto (F-059) | `test_f059_r4_d7_activas_sin_descartada_ni_volcada` |
| 3 | `domain/models/situacion_volcado.py:66` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 4 | `domain/models/situacion_volcado.py:77` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 5 | `domain/models/situacion_volcado.py:88` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 6 | `domain/models/situacion_volcado.py:103` | logico | `and self.ultimo is not None → or self.ultimo is not None` | muerto (F-059) | `(recogida) copia/services/postventa-api/tests/test_f059_volcado_dominio.py` |
| 7 | `domain/models/situacion_volcado.py:104` | logico | `and self.ultimo.estado in ESTADOS_CON_PARTE → or self.ultimo.estado in ESTADOS_CON_PARTE` | muerto (F-059) | `(recogida) copia/services/postventa-api/tests/test_f059_volcado_dominio.py` |
| 8 | `domain/models/situacion_volcado.py:125` | logico | `if situacion.ultimo is not None and situacion.ultimo.estado in ESTADOS_EN_DUDA: → if situacion.ultimo is not None or situacion.ultimo.estado in ESTADOS_EN_DUDA:` | muerto (F-059) | `test_f059_r1_sin_eventos_no_hay_estado_de_volcado` |
| 9 | `domain/models/volcado.py:115` | entero | `FORMA_ESCRITA = 1 → FORMA_ESCRITA = 2` | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| 10 | `domain/models/volcado.py:117` | booleano | `CAUSANTE = False → CAUSANTE = True` | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| 11 | `domain/models/volcado.py:119` | entero | `CADUCIDAD_DEL_ENSAYO = timedelta(minutes=30) → CADUCIDAD_DEL_ENSAYO = timedelta(minutes=31)` | muerto (F-059) | `test_f059_r17_a_los_30_minutos_caduca[pasado0]` |
| 12 | `domain/models/volcado.py:121` | entero | `MAX_PARTES_POR_LLAMADA = 50 → MAX_PARTES_POR_LLAMADA = 51` | muerto (F-059) | `test_f059_r30_de_1_a_50_partes_por_cuerpo` |
| 13 | `domain/models/volcado.py:221` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 14 | `domain/models/volcado.py:230` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 15 | `domain/models/volcado.py:248` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 16 | `domain/models/volcado.py:261` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 17 | `domain/models/volcado.py:271` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 18 | `domain/models/volcado.py:283` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 19 | `domain/models/volcado.py:291` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 20 | `domain/models/volcado.py:302` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 21 | `domain/models/volcado.py:312` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 22 | `domain/models/volcado.py:320` | booleano | `@dataclass(frozen=True) → @dataclass(frozen=False)` | muerto (F-059) | `test_f059_los_tipos_son_inmutables` |
| 23 | `domain/models/volcado.py:344` | not | `if not isinstance(incidencia_id, UUID): → if isinstance(incidencia_id, UUID):` | muerto (F-059) | `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico` |
| 24 | `domain/models/volcado.py:346` | aritmetico | `return PREFIJO_REFERENCIA + str(incidencia_id) → return PREFIJO_REFERENCIA - str(incidencia_id)` | muerto (F-059) | `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico` |
| 25 | `domain/models/volcado.py:420` | not | `if not isinstance(commit, bool): → if isinstance(commit, bool):` | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| 26 | `domain/models/volcado.py:422` | not | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA: → if 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| 27 | `domain/models/volcado.py:422` | entero | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA: → if not 2 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| 28 | `domain/models/volcado.py:422` | comparacion | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA: → if not 1 < len(partes) <= MAX_PARTES_POR_LLAMADA:` | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| 29 | `domain/models/volcado.py:422` | comparacion | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA: → if not 1 <= len(partes) < MAX_PARTES_POR_LLAMADA:` | muerto (F-059) | `test_f059_r30_de_1_a_50_partes_por_cuerpo` |
| 30 | `domain/models/volcado.py:427` | comparacion | `if len(set(referencias)) != len(referencias): → if len(set(referencias)) == len(referencias):` | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| 31 | `domain/models/volcado.py:440` | comparacion | `return huella_de_valores(candidata.valores) == candidata.huella → return huella_de_valores(candidata.valores) != candidata.huella` | muerto (F-059) | `test_f059_r7_la_huella_intacta` |
| 32 | `domain/models/volcado.py:449` | comparacion | `if len(set(incidencias)) != len(incidencias): → if len(set(incidencias)) == len(incidencias):` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| 33 | `domain/models/volcado.py:481` | comparacion | `elif situacion.obra_codigo != obra: → elif situacion.obra_codigo == obra:` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| 34 | `domain/models/volcado.py:483` | logico | `elif situacion.volcado is not None and situacion.volcado.volcada is not None: → elif situacion.volcado is not None or situacion.volcado.volcada is not None:` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| 35 | `domain/models/volcado.py:491` | logico | `elif candidata is None or not es_candidata(situacion): → elif candidata is None and not es_candidata(situacion):` | muerto (F-059) | `test_f059_r11_no_es_candidata_si_la_situacion_no_lo_es_aunque_la_lista_la_traiga` |
| 36 | `domain/models/volcado.py:491` | not | `elif candidata is None or not es_candidata(situacion): → elif candidata is None or es_candidata(situacion):` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| 37 | `domain/models/volcado.py:493` | not | `elif not huella_intacta(candidata): → elif huella_intacta(candidata):` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| 38 | `domain/models/volcado.py:515` | comparacion | `if ensayo.obra_codigo != obra: → if ensayo.obra_codigo == obra:` | muerto (F-059) | `test_f059_r17_un_ensayo_vigente_vale` |
| 39 | `domain/models/volcado.py:519` | comparacion | `if ensayo.actor_oid != actor_oid: → if ensayo.actor_oid == actor_oid:` | muerto (F-059) | `test_f059_r17_un_ensayo_vigente_vale` |
| 40 | `domain/models/volcado.py:524` | aritmetico | `if ahora - ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO: → if ahora + ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO:` | muerto (F-059) | `test_f059_r17_un_ensayo_vigente_vale` |
| 41 | `domain/models/volcado.py:524` | comparacion | `if ahora - ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO: → if ahora - ensayo.at_utc > CADUCIDAD_DEL_ENSAYO:` | muerto (F-059) | `test_f059_r17_a_los_30_minutos_caduca[pasado0]` |
| 42 | `domain/models/volcado.py:538` | logico | `if evento is None or evento.estado is not EstadoEvento.PREVISTO: → if evento is None and evento.estado is not EstadoEvento.PREVISTO:` | muerto (F-059) | `test_f059_r18_fuera_del_ensayo_si_no_esta` |
| 43 | `domain/models/volcado.py:540` | comparacion | `if evento.revision_id != pedida.revision_id: → if evento.revision_id == pedida.revision_id:` | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| 44 | `domain/models/volcado.py:548` | comparacion | `actual.revision_id != evento.revision_id → actual.revision_id == evento.revision_id` | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| 45 | `domain/models/volcado.py:549` | logico | `or actual.accion is not AccionRevision.APROBAR → and actual.accion is not AccionRevision.APROBAR` | muerto (F-059) | `test_f059_r20_revision_desactualizada_si_hay_otra_revision_despues_del_ensayo` |
| 46 | `domain/models/volcado.py:552` | comparacion | `if actual.huella != evento.huella: → if actual.huella == evento.huella:` | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| 47 | `domain/models/volcado.py:583` | entero | `excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[1])) → excluidas.append(Excluida(pedida.incidencia_id, motivo[1], motivo[1]))` | muerto (F-059) | `test_f059_r18_fuera_del_ensayo_si_no_esta` |
| 48 | `domain/models/volcado.py:583` | entero | `excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[1])) → excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[2]))` | muerto (F-059) | `test_f059_r18_fuera_del_ensayo_si_no_esta` |
| 49 | `domain/models/volcado.py:595` | logico | `return isinstance(valor, int) and not isinstance(valor, bool) → return isinstance(valor, int) or not isinstance(valor, bool)` | muerto (F-059) | `test_f059_r22_con_parte_sin_ide_entero[None-creado]` |
| 50 | `domain/models/volcado.py:595` | not | `return isinstance(valor, int) and not isinstance(valor, bool) → return isinstance(valor, int) and isinstance(valor, bool)` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 51 | `domain/models/volcado.py:624` | logico | `or elemento.get("referencia_externa") != parte.referencia_externa → and elemento.get("referencia_externa") != parte.referencia_externa` | muerto (F-059) | `test_f059_r22_indices_cambiados_de_referencia_son_sin_respuesta` |
| 52 | `domain/models/volcado.py:624` | comparacion | `or elemento.get("referencia_externa") != parte.referencia_externa → or elemento.get("referencia_externa") == parte.referencia_externa` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 53 | `domain/models/volcado.py:628` | not | `if not isinstance(crudo, str) or crudo not in {e.value for e in validos}: → if isinstance(crudo, str) or crudo not in {e.value for e in validos}:` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 54 | `domain/models/volcado.py:628` | logico | `if not isinstance(crudo, str) or crudo not in {e.value for e in validos}: → if not isinstance(crudo, str) and crudo not in {e.value for e in validos}:` | muerto (F-059) | `test_f059_r22_un_estado_que_no_es_de_los_cuatro[previsto]` |
| 55 | `domain/models/volcado.py:633` | not | `if not _es_entero(ide) or ide < 1: → if _es_entero(ide) or ide < 1:` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 56 | `domain/models/volcado.py:633` | logico | `if not _es_entero(ide) or ide < 1: → if not _es_entero(ide) and ide < 1:` | muerto (F-059) | `test_f059_r22_con_parte_sin_ide_entero[None-creado]` |
| 57 | `domain/models/volcado.py:633` | comparacion | `if not _es_entero(ide) or ide < 1: → if not _es_entero(ide) or ide <= 1:` | muerto (F-059) | `test_f059_r22_un_cod_de_otro_mes_bien_formado_vale_y_el_ide_1_tambien` |
| 58 | `domain/models/volcado.py:633` | entero | `if not _es_entero(ide) or ide < 1: → if not _es_entero(ide) or ide < 2:` | muerto (F-059) | `test_f059_r22_un_cod_de_otro_mes_bien_formado_vale_y_el_ide_1_tambien` |
| 59 | `domain/models/volcado.py:635` | not | `if not isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None: → if isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None:` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 60 | `domain/models/volcado.py:635` | logico | `if not isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None: → if not isinstance(cod, str) and PATRON_COD_PARTE.fullmatch(cod) is None:` | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[None-creado]` |
| 61 | `domain/models/volcado.py:644` | not | `if not isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None: → if isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` | muerto (F-059) | `test_f059_r22_r35_rechazado_y_no_procesado_solo_con_el_codigo` |
| 62 | `domain/models/volcado.py:644` | logico | `if not isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None: → if not isinstance(codigo, str) and PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` | muerto (F-059) | `test_f059_r22_r35_sin_codigo_de_motivo_admisible[None-rechazado]` |
| 63 | `domain/models/volcado.py:671` | not | `if not isinstance(datos, Mapping): → if isinstance(datos, Mapping):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 64 | `domain/models/volcado.py:674` | not | `if not isinstance(partes, list) or not isinstance(dry_run, bool): → if isinstance(partes, list) or not isinstance(dry_run, bool):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 65 | `domain/models/volcado.py:674` | logico | `if not isinstance(partes, list) or not isinstance(dry_run, bool): → if not isinstance(partes, list) and not isinstance(dry_run, bool):` | muerto (F-059) | `test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion[datos4]` |
| 66 | `domain/models/volcado.py:674` | not | `if not isinstance(partes, list) or not isinstance(dry_run, bool): → if not isinstance(partes, list) or isinstance(dry_run, bool):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 67 | `domain/models/volcado.py:676` | comparacion | `if dry_run == (modo is ModoVolcado.VOLCADO): → if dry_run != (modo is ModoVolcado.VOLCADO):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 68 | `domain/models/volcado.py:680` | not | `if not isinstance(elemento, Mapping): → if isinstance(elemento, Mapping):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 69 | `domain/models/volcado.py:683` | not | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if _es_entero(indice) or not 0 <= indice < len(mandados):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 70 | `domain/models/volcado.py:683` | logico | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if not _es_entero(indice) and not 0 <= indice < len(mandados):` | muerto (F-059) | `test_f059_r22_r23_de_mas_o_indices_imposibles[de_mas]` |
| 71 | `domain/models/volcado.py:683` | not | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if not _es_entero(indice) or 0 <= indice < len(mandados):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 72 | `domain/models/volcado.py:683` | entero | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if not _es_entero(indice) or not 1 <= indice < len(mandados):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 73 | `domain/models/volcado.py:683` | comparacion | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if not _es_entero(indice) or not 0 < indice < len(mandados):` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| 74 | `domain/models/volcado.py:683` | comparacion | `if not _es_entero(indice) or not 0 <= indice < len(mandados): → if not _es_entero(indice) or not 0 <= indice <= len(mandados):` | muerto (F-059) | `test_f059_r22_r23_de_mas_o_indices_imposibles[de_mas]` |
| 75 | `domain/models/volcado.py:726` | logico | `if r.estado is not EstadoEvento.CREADO or anterior is None: → if r.estado is not EstadoEvento.CREADO and anterior is None:` | muerto (F-059) | `test_f059_r26_solo_un_creado[idempotente]` |
| 76 | `domain/models/volcado.py:729` | logico | `if parte is not None and parte.sigrid_ide != r.sigrid_ide: → if parte is not None or parte.sigrid_ide != r.sigrid_ide:` | muerto (F-059) | `test_f059_r26_con_el_mismo_ide_no_lo_es` |
| 77 | `domain/models/volcado.py:729` | comparacion | `if parte is not None and parte.sigrid_ide != r.sigrid_ide: → if parte is not None and parte.sigrid_ide == r.sigrid_ide:` | muerto (F-059) | `test_f059_r26_un_creado_con_otro_ide_es_un_posible_duplicado` |
| 78 | `domain/models/volcado.py:749` | not | `if not isinstance(codigo, str): → if isinstance(codigo, str):` | muerto (F-059) | `test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[escritura_reclamaciones_deshabilitada]` |
| 79 | `domain/models/volcado.py:775` | entero | `clave: sum(1 for r in lista if r.estado is estado) for clave, estado in claves → clave: sum(2 for r in lista if r.estado is estado) for clave, estado in claves` | muerto (F-059) | `test_f059_r12_el_resumen_del_ensayo` |
| 80 | `domain/models/volcado.py:788` | not | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_de_1_a_50[1]` |
| 81 | `domain/models/volcado.py:788` | logico | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if not _es_entero(n) and not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_fuera_de_rango_o_no_entero[0]` |
| 82 | `domain/models/volcado.py:788` | not | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if not _es_entero(n) or 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_de_1_a_50[1]` |
| 83 | `domain/models/volcado.py:788` | entero | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if not _es_entero(n) or not 2 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_de_1_a_50[1]` |
| 84 | `domain/models/volcado.py:788` | comparacion | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if not _es_entero(n) or not 1 < n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_de_1_a_50[1]` |
| 85 | `domain/models/volcado.py:788` | comparacion | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator] → if not _es_entero(n) or not 1 <= n < MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | muerto (F-059) | `test_f059_r30_n_de_1_a_50[50]` |

#### Mutantes a mano (lo que la herramienta no muta)

La herramienta solo muta comparaciones, aritmética, `and`/`or`, `not`, booleanos y enteros: no toca `in`/`not
in`, `is`/`is not`, textos, conjuntos, el orden de una tupla, lo que se devuelve ni qué campo se usa. Para eso,
88 mutantes a mano sobre `e0e93db`, en el worktree desechable, con los tests de F-059 solos (y, si sobrevivía,
los de F-056 y F-060 del bloque). **88 de 88 muertos por tests de F-059; ninguno lo caza solo otra feature.**

| Id | Fichero | Mutación | Resultado | Primer test que lo caza |
|---|---|---|---|---|
| M01 | `domain/models/situacion_volcado.py` | ESTADOS_CON_PARTE sin idempotente | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| M02 | `domain/models/situacion_volcado.py` | ESTADOS_EN_DUDA sin sin_respuesta | muerto (F-059) | `test_f059_r1_el_ultimo_enviado_o_sin_respuesta_deja_en_duda[sin_respuesta]` |
| M03 | `domain/models/situacion_volcado.py` | ESTADOS_EN_DUDA con rechazado | muerto (F-059) | `test_f059_r1_el_ultimo_rechazado_o_no_procesado_no_cambia_nada[rechazado]` |
| M04 | `domain/models/situacion_volcado.py` | estado_de_volcado(None) -> en_duda | muerto (F-059) | `test_f059_r1_sin_eventos_no_hay_estado_de_volcado` |
| M05 | `domain/models/situacion_volcado.py` | volcada `is not None` -> `is None` | muerto (F-059) | `test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar` |
| M06 | `domain/models/situacion_volcado.py` | `in ESTADOS_EN_DUDA` -> `not in` | muerto (F-059) | `test_f059_r1_el_ultimo_enviado_o_sin_respuesta_deja_en_duda[enviado]` |
| M07 | `domain/models/situacion_volcado.py` | en_duda devuelve volcada | muerto (F-059) | `test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar` |
| M08 | `domain/models/situacion_volcado.py` | invariante: `volcada is None` -> `is not None` | muerto (F-059) | (recogida de `test_f059_estados.py`: sus `parametrize` construyen una `volcada()` válida, que el mutante rechaza) |
| M09 | `domain/models/situacion_volcado.py` | invariante: `in` -> `not in` | muerto (F-059) | (recogida de `test_f059_estados.py`: `en_duda()` deja de poder construirse) |
| M10 | `domain/models/situacion_volcado.py` | EstadoVolcado.VOLCADA = 'volcado' | muerto (F-059) | `test_f059_r1_un_creado_deja_volcada` |
| M11 | `domain/models/situacion_volcado.py` | EstadoEvento.SIN_RESPUESTA mal escrito | muerto (F-059) | `test_f059_r32_los_estados_y_los_modos_de_un_evento` |
| M12 | `domain/models/revision.py` | estado_de sin la precedencia de §4.1 | muerto (F-059) | `test_f059_r1_la_tabla_de_cuatro_uno` |
| M13 | `domain/models/revision.py` | precedencia: `is not None` -> `is None` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| M14 | `domain/models/revision.py` | volcada admite recuperar | muerto (F-059) | `test_f059_r2_desde_volcada_y_en_duda_ninguna_accion[volcada]` |
| M15 | `domain/models/revision.py` | en_duda admite editar | muerto (F-059) | `test_f059_r2_desde_volcada_y_en_duda_ninguna_accion[en_duda]` |
| M16 | `domain/models/revision.py` | activas incluye volcada | muerto (F-059) | `test_f059_r4_d7_activas_sin_descartada_ni_volcada` |
| M17 | `domain/models/revision.py` | activas excluye en_duda | muerto (F-059) | `test_f059_r4_d7_activas_sin_descartada_ni_volcada` |
| M18 | `domain/models/revision.py` | en_duda no candidata | muerto (F-059) | `test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar` |
| M19 | `domain/models/revision.py` | volcada candidata | muerto (F-059) | `test_f059_r3_una_volcada_no_es_candidata_nunca` |
| M20 | `domain/models/revision.py` | es_candidata `in` -> `not in` | muerto (F-059) | `test_f059_r11_las_candidatas_van_en_el_orden_pedido` |
| M21 | `domain/models/revision.py` | es_candidata sin exigir el `aprobar` | muerto (F-059) | `test_f059_r3_en_duda_sin_un_aprobar_detras_no_es_candidata` |
| M22 | `domain/models/revision.py` | _pasa `in` -> `not in` | muerto (F-059) | `test_f059_r4_d7_activas_sin_descartada_ni_volcada` |
| M23 | `domain/models/revision.py` | EstadoRevision.VOLCADA = 'volcado' | muerto (F-059) | `test_f059_r1_seis_estados_en_su_orden` |
| M24 | `domain/models/revision.py` | FiltroEstado sin volcada | muerto (F-059) | `test_f059_r4_los_dos_filtros_nuevos[volcada-esperado0]` |
| M25 | `domain/models/revision.py` | SituacionDeRevision.volcado sin valor por defecto | muerto (F-059) | `test_f059_r1_la_tabla_de_cuatro_uno` |
| M26 | `domain/models/volcado.py` | prefijo en minúsculas | muerto (F-059) | `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico` |
| M27 | `domain/models/volcado.py` | tipo 0001 | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| M28 | `domain/models/volcado.py` | cod con 3 o 4 cifras | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/001-creado]` |
| M29 | `domain/models/volcado.py` | cod: punto sin escapar | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[RS26-10/0001-creado]` |
| M30 | `domain/models/volcado.py` | cod con \d | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[RS\uff12\uff16.10/0001-creado]` |
| M31 | `domain/models/volcado.py` | cod sin distinguir mayúsculas | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[rs26.10/0001-creado]` |
| M32 | `domain/models/volcado.py` | cod con match en vez de fullmatch | muerto (F-059) | `test_f059_r22_con_parte_sin_cod_bien_formado[RS26.10/00011-creado]` |
| M33 | `domain/models/volcado.py` | motivo hasta 65 | muerto (F-059) | `test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo8-rechazado]` |
| M34 | `domain/models/volcado.py` | motivo sin cifras | muerto (F-059) | `test_f059_r35_el_codigo_de_motivo_de_64_y_con_cifras_vale` |
| M35 | `domain/models/volcado.py` | motivo con mayúsculas, blancos y guiones | muerto (F-059) | `test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo5-rechazado]` |
| M36 | `domain/models/volcado.py` | motivo con match | muerto (F-059) | `test_f059_r22_r35_sin_codigo_de_motivo_admisible[motivo6-rechazado]` |
| M37 | `domain/models/volcado.py` | precondición sin base_de_datos_no_permitida | muerto (F-059) | `test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[base_de_datos_no_permitida]` |
| M38 | `domain/models/volcado.py` | rechazo sin lote_demasiado_grande | muerto (F-059) | `test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[lote_demasiado_grande]` |
| M39 | `domain/models/volcado.py` | rechazo con un código de parte | muerto (F-059) | `test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda[oficio_no_esta_en_la_obra]` |
| M40 | `domain/models/volcado.py` | ensayo admite creado | muerto (F-059) | `test_f059_r14_en_el_ensayo_un_estado_de_escritura_es_sin_respuesta[creado]` |
| M41 | `domain/models/volcado.py` | volcado admite previsto | muerto (F-059) | `test_f059_r22_un_estado_que_no_es_de_los_cuatro[previsto]` |
| M42 | `domain/models/volcado.py` | volcado sin idempotente | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| M43 | `domain/models/volcado.py` | ensayo sin rechazado | muerto (F-059) | `test_f059_r12_r13_en_el_ensayo_idempotente_rechazado_y_no_procesado_valen` |
| M44 | `domain/models/volcado.py` | orden del resumen del ensayo | muerto (F-059) | `test_f059_r12_el_resumen_del_ensayo` |
| M45 | `domain/models/volcado.py` | resumen del volcado sin sin_respuesta | muerto (F-059) | `test_f059_r22_el_resumen_del_volcado` |
| M46 | `domain/models/volcado.py` | referencia con el hex sin guiones | muerto (F-059) | `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico` |
| M47 | `domain/models/volcado.py` | referencia admite un texto | muerto (F-059) | `test_f059_r5_solo_sale_de_un_uuid[texto]` |
| M48 | `domain/models/volcado.py` | intervinientes al revés | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| M49 | `domain/models/volcado.py` | descripción larga = descripción | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| M50 | `domain/models/volcado.py` | ubicación = unidad | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| M51 | `domain/models/volcado.py` | oficio del interviniente = proveedor | muerto (F-059) | `test_f059_r6_el_parte_clave_a_clave` |
| M52 | `domain/models/volcado.py` | descripcion_larga siempre en el cuerpo | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| M53 | `domain/models/volcado.py` | commit siempre false | muerto (F-059) | `test_f059_r6_commit_siempre_explicito[True]` |
| M54 | `domain/models/volcado.py` | interviniente sin causante explícito | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| M55 | `domain/models/volcado.py` | sin forma_comunicacion | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| M56 | `domain/models/volcado.py` | sin database | muerto (F-059) | `test_f059_r6_el_cuerpo_clave_a_clave` |
| M57 | `domain/models/volcado.py` | ya_volcada sin su código (ensayo) | muerto (F-059) | `test_f059_r11_ya_volcada_con_su_codigo` |
| M58 | `domain/models/volcado.py` | ensayo sin mirar la obra | muerto (F-059) | `test_f059_r11_de_otra_obra` |
| M59 | `domain/models/volcado.py` | ensayo: candidata solo por la lista | muerto (F-059) | `test_f059_r11_no_es_candidata_si_la_situacion_no_lo_es_aunque_la_lista_la_traiga` |
| M60 | `domain/models/volcado.py` | ensayo: candidata solo por la situación | muerto (F-059) | `test_f059_r11_no_es_candidata_si_la_lista_no_la_trae` |
| M61 | `domain/models/volcado.py` | causa de otra persona = de otra obra | muerto (F-059) | `test_f059_r17_de_otra_persona` |
| M62 | `domain/models/volcado.py` | volcado no exige previsto | muerto (F-059) | `test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[idempotente]` |
| M63 | `domain/models/volcado.py` | volcado no exige el aprobar | muerto (F-059) | `test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[editar]` |
| M64 | `domain/models/volcado.py` | ya_volcada sin su código (volcado) | muerto (F-059) | `test_f059_r20_r27_ya_volcada_con_su_codigo` |
| M65 | `domain/models/volcado.py` | volcado: `is not None` -> `is None` | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| M66 | `domain/models/volcado.py` | volcado en el orden pedido y no en el del ensayo | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| M67 | `domain/models/volcado.py` | mandadas `in` -> `not in` | muerto (F-059) | `test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo` |
| M68 | `domain/models/volcado.py` | entero admite float | muerto (F-059) | `test_f059_r22_con_parte_sin_ide_entero[700001.0-creado]` |
| M69 | `domain/models/volcado.py` | con parte `in` -> `not in` | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| M70 | `domain/models/volcado.py` | previsto `is` -> `is not` | muerto (F-059) | `test_f059_r22_r35_rechazado_y_no_procesado_solo_con_el_codigo` |
| M71 | `domain/models/volcado.py` | previsto con ide y cod provisionales (D-13) | muerto (F-059) | `test_f059_r12_d13_el_previsto_sin_cod_ni_ide_provisionales_ni_filas` |
| M72 | `domain/models/volcado.py` | motivo entero en vez del código (R35) | muerto (F-059) | `test_f059_r22_r35_rechazado_y_no_procesado_solo_con_el_codigo` |
| M73 | `domain/models/volcado.py` | motivo en texto suelto aceptado | muerto (F-059) | `test_f059_r22_r35_sin_codigo_de_motivo_admisible[oficio_no_esta_en_la_obra-rechazado]` |
| M74 | `domain/models/volcado.py` | índice repetido aceptado | muerto (F-059) | `test_f059_r22_r23_de_mas_o_indices_imposibles[indice_repetido]` |
| M75 | `domain/models/volcado.py` | dry_run al revés | muerto (F-059) | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| M76 | `domain/models/volcado.py` | válidos siempre los del volcado | muerto (F-059) | `test_f059_r12_d13_el_previsto_sin_cod_ni_ide_provisionales_ni_filas` |
| M77 | `domain/models/volcado.py` | todos sin respuesta -> enviado | muerto (F-059) | `test_f059_r23_todos_sin_respuesta` |
| M78 | `domain/models/volcado.py` | no procesados: `is None` -> `is not None` | muerto (F-059) | `test_f059_r24_todos_no_procesados_con_el_codigo_de_lote[escritura_reclamaciones_deshabilitada]` |
| M79 | `domain/models/volcado.py` | duplicado con cualquier estado | muerto (F-059) | `test_f059_r26_solo_un_creado[idempotente]` |
| M80 | `domain/models/volcado.py` | duplicado: cod anterior = el nuevo | muerto (F-059) | `test_f059_r26_un_creado_con_otro_ide_es_un_posible_duplicado` |
| M81 | `domain/models/volcado.py` | precondición -> rechazo | muerto (F-059) | `test_f059_r14_r24_los_de_precondicion[escritura_reclamaciones_deshabilitada]` |
| M82 | `domain/models/volcado.py` | resumen: `not in` -> `in` | muerto (F-059) | `test_f059_r12_el_resumen_del_ensayo` |
| M83 | `domain/models/volcado.py` | resumen sin excluidas | muerto (F-059) | `test_f059_r12_el_resumen_del_ensayo` |
| M84 | `domain/models/volcado.py` | resumen sin la comprobación del modo | muerto (F-059) | `test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas[creado-ensayo]` |
| M85 | `domain/models/volcado.py` | N siempre 5 | muerto (F-059) | `test_f059_r30_n_de_1_a_50[1]` |
| M86 | `domain/models/errores.py` | EnsayoNoValido.causa = motivo | muerto (F-059) | `test_f059_r17_no_existe` |
| M87 | `domain/models/errores.py` | VolcadoSinRespuesta sin en_duda | muerto (F-059) | `test_f059_los_ocho_errores_del_volcado` |
| M88 | `domain/models/errores.py` | VolcadoRechazadoPorLaPasarela sin su código | muerto (F-059) | `test_f059_los_ocho_errores_del_volcado` |

#### Cobertura

Medida con `coverage run` sobre los tests de F-059, `test_f056_revision_dominio.py` y las dos guardias de F-006
(no forma parte de `init.sh`, que este bloque no exige): `domain/models/volcado.py` **100 %** (280 sentencias) y
`domain/models/situacion_volcado.py` **100 %** (47); en `errores.py` y `revision.py`, todas las líneas que añade
F-059 están cubiertas (las que faltan en `revision.py` son el cursor de F-056, que ese subconjunto no recorre).
La puerta `PUERTA COBERTURA` de `init.sh` la dará T23.

## Evidencias del Bloque 1

| Evidencia | Valor |
|---|---|
| Tests de F-059 | `test_f059_volcado_dominio.py` + `test_f059_estados.py`: **304 passed in 2.38s** (con el test de T3) |
| RED (T1) | 296 failed, 7 passed contra el esqueleto neutro (traza arriba) |
| Verificación de T2 | 1144 passed in 28.11s (los diez ficheros de `tasks.md`) |
| Suite entera del servicio | 8425 passed, 2 failed, 129 skipped in **1563.18 s** (tras T2); los 2 rojos, la guardia R26 de F-006 por un GUID sintético mío, corregido: guardias + F-059, 369 passed |
| Cobertura de lo nuevo | `volcado.py` 100 %, `situacion_volcado.py` 100 %; líneas cambiadas de `revision.py` y `errores.py` cubiertas |
| Mutación (herramienta) | **85 generados, 85 muertos, 0 supervivientes, 0 timeouts**, 13042.6 s, 8 workers |
| Reverificación contra F-059 solos | 85/85 sobre `e0e93db` (79/85 sobre `c84e979`: 6 `frozen` → test nuevo) |
| Mutación a mano | **88/88** muertos por tests de F-059 |
| Supervivientes abiertos | **0** |
| Tests ajenos tocados | Solo los del grupo C de §21.3 que se pusieron rojos (tabla de T2) y la enmienda de `ARCHITECTURE.md` |

## Commits del Bloque 1

| Tarea | Commit |
|---|---|
| T0 | `477e596` |
| T1 | `ffaf804` |
| T2 | `c84e979` |
| T3 | `e0e93db` (el test de inmutabilidad) y el de este informe con `progress/mutacion_F-059_bloque1.md` |

**Parado aquí: review del Bloque 1.** Lo que el reviewer debería mirar primero: las decisiones de diseño 1 y 2
de T2 (la fuente de `situaciones` del ensayo y el `None` de `interpretar_respuesta`), que condicionan los
Bloques 2 y 4, y la observación sobre `envio` para T15.

## Correcciones de la review del Bloque 1 (C-B1-1 a C-B1-3) · 2026-10-16

La review (`progress/review_F-059.md`, «Review del Bloque 1», CHANGES_REQUESTED) encontró tres mutantes vivos que
la herramienta no genera. Los tres se corrigen con tests de F-059, y los dos primeros con un cambio pequeño de
dominio en `domain/models/volcado.py`, dentro del Bloque 1.

### C-B1-1 y C-B1-2 · un texto vacío es «sin valor»: una sola regla

**El comportamiento elegido**: un `proveedor_codigo` o un `detalle` **vacío o solo de blancos** se tratan como
nulos. Una función privada nueva, `_con_texto(texto)`, devuelve el texto **tal cual** (sin recortar) si dice
algo, y `None` si es nulo, vacío o en blanco; la usan los tres sitios:

- `parte_de`: sin proveedor que diga algo, `intervinientes = ()` (antes: `is not None`, que con `""` mandaba
  `{"oficio": …, "proveedor": "", "causante": false}`);
- `parte_de`: `descripcion_larga = _con_texto(detalle)` (antes copiaba `""` tal cual);
- `cuerpo_de_parte`: la clave `descripcion_larga` solo va si `_con_texto` dice que hay texto (así tampoco la
  manda un `ParteAVolcar` construido a mano con `""`).

**Por qué este y no un error de programación**:

- **D-9** dice «sin proveedor, sin intervinientes»; un código vacío no identifica a ningún proveedor de
  `obrofc`. Mandarlo haría que la pasarela intentara resolver un interviniente con proveedor `""` contra los
  `obrofc` de la obra (§8.9: `interviniente_no_esta_en_la_obra` o, peor, `interviniente_ambiguo`): un parte
  rechazado por algo que la persona aprobó como «sin proveedor».
- **R6** dice que `descripcion_larga` va «solo si no es nulo» y, si no va, §8.9 pone la descripción, **como el
  alta manual** (`design.md` §5). Un `""` llegaría a `rcp.tex` como texto vacío: el parte tendría una
  descripción larga en blanco, distinto del alta manual. Lo que la regla protege es eso, y un detalle vacío no
  es un detalle.
- Rechazarlo (`ValueError`) tumbaría el ensayo o el volcado de **todo el lote** (un 500) por un dato que no es
  incoherente sino vacío, y `ValoresIncidencia` lo admite tal cual (`valores_importados` copia lo que trae la
  bandeja de F-036; `validar_valores` ya convierte en `None` un detalle en blanco al editar). La regla nueva es
  la misma idea que `validar_valores`, aplicada en la última puerta antes del ERP.
- Lo que sí dice algo se manda **sin recortar** (`" EJ07"` va como `" EJ07"`): lo aprobado es lo que se manda
  (R7); decidir si un código con blancos vale es de quien lo valida al aprobar (F-056), no de aquí.

No cambia la huella (se calcula sobre los valores, no sobre el parte) ni ningún otro requisito.

### C-B1-3 · el duplicado se decide por `sigrid_ide`

Sin cambio de código: faltaban los casos que separan `ide` de `cod`. Dos tests nuevos: el mismo `sigrid_ide` con
otro `cod` **no** es duplicado; otro `sigrid_ide` con el mismo `cod` **sí** lo es (con las dos referencias en el
aviso).

### Tests nuevos (todos en `tests/test_f059_volcado_dominio.py`)

| Test | Fija |
|---|---|
| `test_f059_d9_c_b1_1_un_codigo_de_proveedor_vacio_es_sin_proveedor[vacio, blancos, tabulador]` | `""`, `"  "`, `"\t"` → `intervinientes == ()` y `[]` en el cuerpo |
| `test_f059_d9_c_b1_1_un_codigo_de_proveedor_que_dice_algo_va_tal_cual` | `" EJ07"` → interviniente con `" EJ07"` |
| `test_f059_r6_c_b1_2_un_detalle_vacio_no_es_descripcion_larga[vacio, blancos, salto]` | `descripcion_larga is None` y sin la clave |
| `test_f059_r6_c_b1_2_el_cuerpo_no_manda_una_descripcion_larga_vacia[vacio, blancos]` | `cuerpo_de_parte` de un parte con `""`/`"   "` no lleva la clave |
| `test_f059_r6_c_b1_2_un_detalle_que_dice_algo_va_tal_cual` | `"  Ejemplo de detalle  "` va sin recortar |
| `test_f059_r26_c_b1_3_el_mismo_ide_con_otro_cod_no_lo_es` | sin aviso |
| `test_f059_r26_c_b1_3_otro_ide_con_el_mismo_cod_si_lo_es` | un `PosibleDuplicado` con las dos referencias |

### Los mutantes, repetidos en una copia desechable

En un worktree desechable de `6864483` con los dos ficheros cambiados copiados encima (retirado al terminar; el
árbol de trabajo no se mutó), solo con `test_f059_volcado_dominio.py` y `test_f059_estados.py`, `-x`. Además de
los tres del reviewer, el comportamiento anterior de cada sitio y dos mutantes de la regla nueva:

| Id | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|
| C-B1-1 a | el del reviewer: `if v.proveedor_codigo:` | muerto | `test_f059_d9_c_b1_1_un_codigo_de_proveedor_vacio_es_sin_proveedor[blancos]` |
| C-B1-1 b | el comportamiento anterior: `if v.proveedor_codigo is not None:` | muerto | `test_f059_d9_c_b1_1_un_codigo_de_proveedor_vacio_es_sin_proveedor[vacio]` |
| C-B1-2 a | el del reviewer: `if parte.descripcion_larga:` | muerto | `test_f059_r6_c_b1_2_el_cuerpo_no_manda_una_descripcion_larga_vacia[blancos]` |
| C-B1-2 b | el anterior en el cuerpo: `if parte.descripcion_larga is not None:` | muerto | `test_f059_r6_c_b1_2_el_cuerpo_no_manda_una_descripcion_larga_vacia[vacio]` |
| C-B1-2 c | el anterior en `parte_de`: `descripcion_larga=v.detalle` | muerto | `test_f059_r6_c_b1_2_un_detalle_vacio_no_es_descripcion_larga[vacio]` |
| C-B1-3 | el del reviewer: `parte.sigrid_cod != r.sigrid_cod` | muerto | `test_f059_r26_c_b1_3_el_mismo_ide_con_otro_cod_no_lo_es` |
| regla a | `_con_texto` decide sin recortar (`not texto`) | muerto | `test_f059_d9_c_b1_1_un_codigo_de_proveedor_vacio_es_sin_proveedor[blancos]` |
| regla b | `_con_texto` devuelve el texto recortado | muerto | `test_f059_r6_c_b1_2_un_detalle_que_dice_algo_va_tal_cual` |

**8/8 muertos por tests de F-059.** La campaña de la herramienta no se relanza (indicación del líder): los
cambios tocan líneas con `is`/`not`/`or` y una llamada; el `or` y el `not` de `_con_texto` sí los mutaría, y
ambos los cazan los casos de arriba (regla a; y quitar el `not` deja pasar los vacíos).

### Verificación

Desde `<scratchpad>/f059` (sin `.env`), los diez ficheros de la verificación de T2 más las dos guardias de F-006:
**1 failed, 1220 passed in 30.91s**. Los dos de F-059 solos: **316 passed in 4.40s** (los 333 de antes incluían `test_f006_arquitectura.py`).

El rojo **no es de este cambio**: `test_f006_repo_sin_identificadores.py::test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador`
encuentra **dos GUID en `progress/review_F-059.md`, línea 152** (commit `6864483` de la review): son los dos
GUID sintéticos de mi T1 que el reviewer cita al comentar el incidente de la guardia R26. No he tocado ese
fichero (no es mío); **para el líder**: hay que redactarlos allí o `init.sh` saldrá en rojo.

Cobertura, medida tras el cambio con los dos ficheros de F-059: `volcado.py` **100 %** (284 sentencias, la función
nueva entera) y `situacion_volcado.py` **100 %** (47).

## Bloque 2 · La tabla y los repositorios · **BLOQUEADO antes de T4** · 2026-10-16

Encargo: T4, T5, T6, T7 y T9 (T8 la hace el humano). **No he escrito código ni tests de este bloque.** Antes de
la RED he leído el bloque entero contra la spec y he hecho un inventario empírico (abajo), y hay **dos cosas que
la spec no deja decidir al implementer**. Lo dicen las reglas del encargo y del arnés: no se improvisa, se para.
Las dos se resuelven con una línea del humano cada una; las propongo con su recomendación para que vayan en una
sola ronda.

Árbol de trabajo sin tocar: `git status` limpio en `9fdb222` (solo este informe); el worktree desechable del
inventario, retirado. `progress/current.md` y `harness/features.json` no los he tocado (regla del encargo):
**que el líder marque el bloqueo donde corresponda.**

### B-1 · R17 frente a R33: para comparar la persona del ensayo hay que leer `actor_oid`, y R33 lo prohíbe

- **R17**: el volcado exige un ensayo «pedido por **el mismo `usuario_oid`**»; si no, 409 `ensayo_no_valido`
  con `motivo` `de_otra_persona`.
- **R33**: «**ninguna lectura selecciona `actor_oid`**». Igual de tajantes `design.md` §9 («`actor_oid` es el
  `oid` opaco y **no se lee nunca**») y §15 (`oid`: «Ninguna respuesta, ningún log, **ninguna lectura**»); §18
  lo pone como test de T4.
- **Pero el diseño exige leerlo**: §8.1 da `leer_ensayo(*, ensayo_id) -> Ensayo | None` y §7 define
  `Ensayo(ensayo_id, obra_codigo, actor_oid, at_utc, eventos)`; `validar_ensayo(ensayo, *, obra, actor_oid,
  ahora)` compara `ensayo.actor_oid != actor_oid` (así está, aprobado, en `domain/models/volcado.py:534`, Bloque
  1). Con esa firma, `leer_ensayo` **tiene** que seleccionar `actor_oid` para construir el `Ensayo`.

No hay implementación que cumpla las dos letras sin cambiar algo aprobado. Opciones:

- **(a) Recomendada: la comparación la hace la base y el `oid` nunca vuelve.** `leer_ensayo(*, ensayo_id,
  actor_oid)`; su `SELECT` lleva el booleano `(actor_oid = %s)` y **no** la columna. En el dominio,
  `Ensayo.actor_oid: str` pasa a `Ensayo.de_la_persona: bool` y `validar_ensayo(ensayo, *, obra, ahora)` mira ese
  booleano, con el mismo orden de motivos de R17 (`no_existe`, `de_otra_obra`, `de_otra_persona`, `caducado`).
  Mantiene R33 y §15 al pie de la letra y la misma propiedad que F-056 dio a `revisado_por` («se escribe y no se
  lee»). Coste: tocar dos piezas aprobadas del Bloque 1 (`Ensayo` y `validar_ensayo`, con sus tests de R17 y sus
  mutantes) y la firma de `leer_ensayo` de §8.1; lo haría dentro de este bloque, con su RED, y lo citaría aquí.
- (b) Excepción a R33 solo para `leer_ensayo`: selecciona `actor_oid` para construir el `Ensayo`, que solo va a
  `validar_ensayo` y nunca a un log ni a una respuesta (con `field(repr=False)` para que no salga en un `repr`
  por descuido). No toca el Bloque 1, pero relaja un requisito de datos personales en una feature `critico` y
  obliga a reescribir R33, §9 y §15.
- (c) Descartada: rellenar `Ensayo.actor_oid` con el `oid` de quien pide cuando la base dice que coincide, y con
  otra cosa si no. Sería un campo del dominio con un valor que no viene de donde dice.

### B-2 · El inventario de R41 (grupo A de §21.3) no recoge un test que el `16_` pone rojo

Inventario **empírico**: en un worktree desechable de `9fdb222`, con un `16_volcados_sigrid.sql` de borrador
(el `CREATE TABLE` y los dos índices de `design.md` §9, literales), los 41 ficheros de `tests/` que nombran el
DDL (`ficheros_ddl`, `cargar_ddl`, `DIRECTORIO_SQL`, `.sql`…), lanzados desde el scratchpad (sin `.env`):

```
<venv>/python.exe -m pytest <wt>/services/postventa-api/tests/<los 41> -q -p no:cacheprovider --tb=no -rf
12 failed, 1468 passed, 102 skipped in 86.42s
```

Los 12 rojos (los `skipped` son los controles de `git` de otras ramas, que fuera de la suya se saltan):

| Test | ¿En el grupo A de §21.3 / R41? |
|---|---|
| `test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden` | sí |
| `test_f028_ddl_historico.py::test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo` | sí |
| `test_f030_veredicto_persistido.py::test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo` | sí |
| `test_f031_alcance_cerrado.py::test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo` | sí |
| `test_f032_alcance_cerrado.py::test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo` | sí |
| `test_f033_alcance_cerrado.py::test_f033_no_hay_ni_un_fichero_de_ddl_nuevo` | sí |
| `test_f034_alcance_cerrado.py::test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo` | sí |
| `test_f036_ddl.py::test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden` | sí |
| `test_f056_alcance_cerrado.py::test_f056_r12_solo_15_declara_una_columna_de_correo` | sí |
| `test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_de_los_de_f036` | sí |
| `test_f060_alcance_cerrado.py::test_f060_r37_los_sql_son_los_quince_de_antes` | sí |
| **`test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo`** | **no** |

El duodécimo exige que la **única** columna de correo de todo el esquema sea `revisiones_bandeja.revisado_correo`;
`actor_correo` (D-8, aprobada) la rompe por fuerza. Es el gemelo del de `test_f056_alcance_cerrado.py` que §21.3
sí lista («el `16_` trae `actor_correo`»), pero **no está** en la lista de R41, que es «test a test», y el
encargo la cierra («ningún otro»). Sin ampliarlo, la verificación de T5 (que incluye `tests/test_f056_ddl.py`
entero) no puede salir en verde.

- **Propuesta (recomendada):** añadirlo a las excepciones de R41 (grupo A de §21.3) y ampliarlo como su gemelo,
  sin relajar: la igualdad exacta sigue siendo exacta, ahora con dos columnas
  (`revisiones_bandeja.revisado_correo` y `volcados_sigrid.actor_correo`), y se declara en T16.

Fuera de `tests/`, **sin decisión que pedir**: los `_limpiar` de `tests_bbdd` de F-036, F-056 y F-060 hacen
`DELETE FROM` de `revisiones_bandeja` y `bandeja_incidencias`; con filas de `volcados_sigrid` que las
referencien, el de F-060 (que corre después del de F-059, por orden alfabético) fallaría por la clave ajena en T8.
Lo resuelve mi propio `test_f059_bbdd_volcado.py` borrando sus filas de `volcados_sigrid` antes y después de cada
test (la limpieza de `tests_bbdd` no es código del servicio: O-5 de F-056), sin tocar los de los demás.

### Lo que haré salvo que se diga otra cosa (no bloquea; para que conste en la misma ronda)

1. `guardar_resultados(*, llamada_id, ensayo_id, obra, partes, resultados, quien, ahora)`: la firma de §8.1
   (`llamada_id, ensayo_id, resultados, quien, ahora`) no da `revision_id`, `huella_valores` ni `obra_codigo`, que
   son `NOT NULL` en §9, y `ResultadoParte` no los lleva. Se los paso como a `guardar_ensayo` (`obra` y los
   `ParteAVolcar` mandados), con la comprobación de que resultados y partes casan uno a uno.
2. `quien` es el `Quien(oid, correo)` de F-056; `situaciones` devuelve una entrada por cada incidencia pedida que
   está en la bandeja (sin eventos, `SituacionDeVolcado(None, None)`).
3. La sentencia nueva de R2 que lee `_registrar` vive en `sentencias_volcado.py` y la importa
   `repositorio_revision_pg.py` (sin tocar `select_bloquear`, `select_ultimas_revisiones` ni `insert_revision`).

### Para seguir

Con B-1 y B-2 decididos, retomo el Bloque 2 desde T4 (RED) tal cual está en `tasks.md`. Si se elige B-1 (a), la
RED de T4 incluirá además los casos de `Ensayo.de_la_persona` y de `validar_ensayo` que cambian, y T9 mutará esas
líneas del Bloque 1.


## Bloque 2 · La tabla y los repositorios · T4–T7 y T9 · 2026-10-16 (tras el desbloqueo)

Desbloqueado por el humano el 2026-10-16 («ok a b1 y b2»): **B-1 (a)** (la base compara la persona del ensayo;
`Ensayo.de_la_persona: bool`; `validar_ensayo(ensayo, *, obra, ahora)`), **B-2**
(`test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo` entra en las
excepciones de R41) y aceptados los tres puntos de «Lo que haré…». Lo escribió el spec-author en `13f9f51`
(`design.md` §7, §8.1, §18, §20, §21.3; `tasks.md` T4, T6, T9, T16). Releído antes de empezar.

**Hash anterior a T4 (base de T9): `13f9f51`.** Todo lanzado desde `<scratchpad>/f059` (sin `.env`) con rutas
absolutas, y la mutación con `--raiz <repo>` desde el mismo directorio. **`bash harness/init.sh` no se ha
lanzado**: su sección 7 bis ejecuta `pytest` desde `services/postventa-api`, donde está el `.env`, y el encargo
prohíbe que ningún proceso mío lo lea. En su lugar, las verificaciones de cada tarea, la suite entera del
servicio y `ruff` sobre lo tocado (abajo). La puerta completa es T23.

### T4 · Fase RED (`f50281b`)

**Tests nuevos:**

- `tests/test_f059_ddl.py` (R32, R33, R26): el `16_` el último, detrás del `15_`; la guarda real acepta sus tres
  sentencias; `cargar_ddl` lo carga; idempotente; ni semilla, ni `UPDATE`/`DELETE`/`TRUNCATE`, ni `CASCADE`; todo
  cualificado y sin `public`; sin binarias ni JSON; el esquema configurado se sustituye entero; la cabecera
  (ruta, «Construye», «Lee de» `13_` y `15_`, y quince frases: append-only, `evento_id`, el estado no se guarda,
  sin índice único y R26, `actor_oid` que no se lee, el correo de un empleado interno que nunca va a un log,
  `GET /api/revision`, `motivo.mensaje`, el login de Sigrid, sin cascada, F-048); las dieciséis columnas en
  orden; cada declaración; los `CHECK` de `modo` y `estado` = `ModoVolcado` y `EstadoEvento`; los **cuatro**
  `CHECK` de fila, literales, y diez `CHECK` en total; los literales de fila casan con el dominio
  (`ESTADOS_CON_PARTE`, los estados de un ensayo, la longitud del motivo); ni `UNIQUE` ni columna de estado
  de la incidencia; los dos índices.
- `tests/test_f059_repositorio_volcado.py`, con `ConexionDoble`: el puerto (cinco operaciones, cada una solo por
  nombre y con los parámetros de §8.1 enmendado) y que el repositorio lo cumple; el SQL **escrito a mano** de
  `select_volcado_de` (las dos `LATERAL`: el **primer** `creado`/`idempotente` por `evento_id` ascendente y el
  **último** de modo `volcado` por `evento_id` descendente, y la última revisión) y de `select_ensayo` (la
  comparación `(actor_oid = %s)` con el `oid` como **parámetro**); el `INSERT` sin `RETURNING` ni
  `ON CONFLICT`, en UTC y sin aceptar una hora sin zona; **R33**: en cada lectura (las de F-059 y las tres de
  F-056 que ganan las `LATERAL`), ninguna lista de columnas ni ningún texto nombra `actor_oid` fuera de
  `(actor_oid = %s)`, y solo la del ensayo lo compara, una vez (con su control negativo); el código de los dos
  módulos sin `UPDATE`/`DELETE`/`TRUNCATE`/DDL/consultivo; esquema configurado y hostil; de fila a dominio
  (`fila_a_volcado`, `fila_a_bloqueada`, `filas_a_ensayo`: `de_la_persona` solo si lo es en **todas** las
  filas, filas que no casan en obra u hora → `ValueError`, UTC); `situaciones` (una entrada por cada una de la
  bandeja, `SituacionDeVolcado(None, None)` sin eventos, sin pedidas no abre); `guardar_ensayo` y
  `guardar_resultados` (un evento por parte, clave a clave, uno a uno o `ValueError` sin abrir, 503 sin nada a
  medias); `leer_ensayo` (pasa el `oid` y no lo recibe); **`anotar_enviados`** (el orden: `select_bloquear`
  **exacta** de F-056, la lectura, la decisión **dentro** —el doble apunta lo ejecutado cuando se le llama—,
  los `INSERT` de los `enviado` y **un** `COMMIT`; con la decisión real del dominio; si la decisión falla,
  `ROLLBACK` sin escribir; si la base falla en cualquiera de los tres pasos, 503 y `ROLLBACK`; sin pedidas no
  abre; `select_bloquear` es el mismo objeto que el de `sentencias_revision`); R34 (ningún log con `oid`,
  correo ni textos); `construir_volcados` (la receta de la fábrica, sin contraseña no abre, fuera de `__all__`).
- `tests/test_f059_volcado_dominio.py` (B-1 (a)): el ayudante `ensayo()` pasa a `de_la_persona`; los casos de
  R17 (`causa_de`, «vigente vale», `de_otra_persona`, el orden obra-persona-caducidad y la inmutabilidad) sin
  `actor_oid`; y uno nuevo, `test_f059_r17_r33_b1_el_dominio_no_ve_ningun_oid` (los campos de `Ensayo` y la
  firma de `validar_ensayo`, exactos). Ningún caso se quita.

**Tests ajenos ampliados**, solo los de R41 (F-1 (a) y B-2), cada línea con su comentario `F-059 (R41, F-1 (a);
design.md §21.3 …)`:

| Test | Ampliación (sin quitar nada) | Grupo |
|---|---|---|
| `test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden` | + `"16_volcados_sigrid.sql"` al final de la lista exacta; una frase en el docstring | A |
| `test_f028_ddl_historico.py::test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo` | + el `16_` en la cola exacta tras el `11_` | A |
| `test_f030_veredicto_persistido.py::test_f030_r20_…`, `test_f031_…::test_f031_r17_…`, `test_f032_…::test_f032_r22_…`, `test_f033_…::test_f033_…`, `test_f034_…::test_f034_r23_…` (`no_hay_ni_un_fichero_de_ddl_nuevo`) | `== DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056 + ("16_volcados_sigrid.sql",)`, **dentro de la función** (la constante no se toca) | A |
| `test_f036_ddl.py::test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden` | + el `16_` en la cola exacta | A |
| `test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_de_los_de_f036` | `nombres[-1] == 15_` pasa a `nombres[-2] == 15_` **y** `nombres[-1] == 16_` (más estricta: dice también cuál va detrás) | A |
| `test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo` | La igualdad exacta pasa a dos: `revisado_correo` y `volcados_sigrid.actor_correo` | **A, B-2** |
| `test_f056_alcance_cerrado.py::test_f056_r12_solo_15_declara_una_columna_de_correo` | La igualdad exacta pasa a `["15_…", "16_…"]` | A |
| `test_f060_alcance_cerrado.py::test_f060_r37_los_sql_son_los_quince_de_antes` | `== (*SQL_DE_LA_BASE, "16_volcados_sigrid.sql")` (la constante no se toca); el docstring dice que el único es el de F-059 | A |
| `test_f056_repositorio_revision.py` | Ver abajo | C |

En `test_f056_repositorio_revision.py` (grupo C: «el ancho de las filas falsas de `_select_situaciones`,
`aprobadas` y `registrar`»):

- **El ancho**: la constante nueva `LEIDAS_DEL_VOLCADO` (las ocho de las `LATERAL`, escritas a mano), `SIN_VOLCADO`
  y el parámetro `volcado` (por defecto `SIN_VOLCADO`) del ayudante `_fila`.
- `test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original`: `count("LEFT JOIN LATERAL") == 2` pasa
  a `== 4` y **se añade** que dos de ellas son sobre `volcados_sigrid` de la propia. Las otras cuatro aserciones,
  intactas.
- `test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden`: la lista esperada gana, al final,
  `LEIDAS_DEL_VOLCADO`.
- `test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma`: `len(sql) == 3` pasa a `4`; el `INSERT` y sus
  parámetros pasan de la posición 2 a la 3, y **se añade** que la 2 es la lectura de `volcados_sigrid` con la
  propia como parámetro.
- **Añadidos** al final, en su sección «F-059 …», con nombre `test_f059_*` (R1–R4, R29, R33): la fila sin eventos
  sin `volcado`, la `volcada`, la `en_duda`, el último rechazado con su motivo, la original sin `volcado`, el
  ancho de más o de menos, `listar` y `situacion` con la situación de volcado, **`aprobadas` con una `volcada`
  que no falla y no la devuelve** (y sí la `en_duda`), **`registrar` con un volcado aparecido tras el primer
  chequeo → `AccionNoPermitida` sin insertar y `ROLLBACK`** (enviado, sin_respuesta, creado, idempotente de
  ensayo), el último rechazado que sí admite la acción, la lectura tras el bloqueo y solo de la propia, R2 antes
  que la frescura, 503 si la lectura falla, las `LATERAL` de la propia (añadido en T9) y ninguna lectura con
  `actor_oid`.
- `test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa` **no se toca** (y sigue en verde: ver
  la decisión 1 de T6).

**El esqueleto neutro** (como en T1): `domain/ports/volcado.py` ya con el puerto (es una declaración);
`sentencias_volcado.py` con `EventoNuevo` y las seis funciones con `raise NotImplementedError("F-059 T6")`;
`repositorio_volcado_pg.py` con la clase y sus cinco métodos que levantan lo mismo (e importando
`select_bloquear`). Sin `16_`, sin `construir_volcados`, y sin tocar `sentencias_revision.py`,
`repositorio_revision_pg.py` ni `domain/models/volcado.py`.

Comandos (desde `<scratchpad>/f059`, `R` = `<repo>/services/postventa-api`):

```
COLUMNS=400 $R/.venv/Scripts/python.exe -m pytest $R/tests/test_f059_ddl.py $R/tests/test_f059_repositorio_volcado.py \
  $R/tests/test_f056_repositorio_revision.py $R/tests/test_f059_volcado_dominio.py -q -p no:cacheprovider --tb=no -rf
```

Resultado: **171 failed, 328 passed**. Por tipo: 65 `NotImplementedError` (el esqueleto), 40 `TypeError`
(`Ensayo` sin `de_la_persona`, y `validar_ensayo` que aún exige `actor_oid`), 54 `AssertionError` (36 del `16_`
que falta; los de `sentencias_revision.py` sin las `LATERAL` y `fila_a_situacion` sin el volcado; la firma de
`Ensayo`), 7 `DID NOT RAISE` (R2 en `registrar` y el ancho de la fila), 2 `ValueError` (filas más anchas que la
consulta vieja), 2 `AttributeError` (`construir_volcados`) y 1 `RevisionDesactualizada` (R2 aún no va antes que
la frescura). **Los 328 que pasan** son los del dominio del Bloque 1 que no construyen un `Ensayo` y los de F-056
que el cambio no toca, y **14** de los ficheros nuevos que no dependen de lo que falta: las enumeraciones
escritas a mano (`test_f059_r32_los_modos_y_los_estados_son_los_de_la_spec`), el puerto (siete casos: es una
declaración), los dos controles negativos, el R33 de código sobre los dos esqueletos (no tienen SQL), que el
esqueleto importa `select_bloquear` de F-056 y que `construir_volcados` no está en `__all__`.

Traza real, completa (solo se ha recortado el prefijo de la ruta hasta `services\`; ningún GUID):

```
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_el_fichero_va_el_ultimo_detras_de_la_revision - AssertionError: assert '15_revisiones_bandeja.sql' == '16_volcados_sigrid.sql'
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_guarda_real_acepta_cada_sentencia_y_son_tres - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_el_ddl_real_entero_se_carga_con_el_fichero - AssertionError: assert 'CREATE TABLE IF NOT EXISTS postventa.volcados_sigrid ' in 'CREATE SCHEMA IF NOT EXISTS postventa CREATE TABLE IF NOT EXISTS postventa.remesas ( id uuid PRIMARY KEY, nombre_orig...INDEX IF NOT EXISTS...
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_todo_es_idempotente - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_r33_ni_datos_ni_escrituras_ni_borrados_en_el_ddl - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_todo_cualificado_sin_public_ni_ambito_de_servidor - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_sin_columnas_binarias_ni_json - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_un_esquema_configurado_distinto_se_sustituye_entero - AssertionError: assert 'CREATE TABLE IF NOT EXISTS otro_inventado.volcados_sigrid' in ''
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_dice_que_construye_y_de_que_lee - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[APPEND-ONLY] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[evento_id] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[NO SE GUARDA EL ESTADO] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[SIN INDICE UNICO] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[R26] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[actor_oid] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[NO SE LEE NUNCA] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[actor_correo] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[empleado interno] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[NUNCA va a un log] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[GET /api/revision] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[motivo.mensaje] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[login de Sigrid] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[ON DELETE CASCADE] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo[F-048] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_las_columnas_son_las_del_diseno_y_ninguna_mas - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_declaraciones_de_las_columnas - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_el_check_de_modo_es_el_enum_del_dominio - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_el_check_de_estado_es_el_enum_del_dominio - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_cuatro_check_de_fila[CHECK ((modo = 'ensayo') = (ensayo_id IS NULL))] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_cuatro_check_de_fila[CHECK (modo = 'volcado' OR estado IN ('previsto', 'idempotente', 'rechazado', 'no_procesado'))] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_cuatro_check_de_fila[CHECK ((estado IN ('creado', 'idempotente')) = (sigrid_ide IS NOT NULL AND sigrid_cod IS NOT NULL))] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_cuatro_check_de_fila[CHECK (estado NOT IN ('rechazado', 'no_procesado') OR motivo_codigo IS NOT NULL)] - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_solo_los_cuatro_check_de_fila_y_diez_en_total - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_check_de_fila_casan_con_el_dominio - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r26_ni_unique_ni_estado_de_la_incidencia_guardado - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_ddl.py::test_f059_r32_los_dos_indices - AssertionError: falta 16_volcados_sigrid.sql
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_el_insert_es_una_fila_sin_on_conflict - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_el_insert_de_un_ensayo_sin_ensayo_id_y_con_motivo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_no_se_escribe_una_hora_sin_zona - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_una_hora_con_otra_zona_se_escribe_en_utc - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_r33_la_unica_escritura_es_el_insert_en_volcados - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_ninguna_lectura_selecciona_actor_oid[volcado_de] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_ninguna_lectura_selecciona_actor_oid[ensayo] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_ninguna_lectura_selecciona_actor_oid[situaciones_de_obra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_ninguna_lectura_selecciona_actor_oid[situacion] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_ninguna_lectura_selecciona_actor_oid[aprobadas] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r33_solo_la_lectura_del_ensayo_compara_la_persona - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r4_el_correo_si_se_lee - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_cada_sentencia_con_el_esquema_configurado[volcado_de] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_cada_sentencia_con_el_esquema_configurado[ensayo] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_cada_sentencia_con_el_esquema_configurado[insert] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_un_esquema_hostil_no_llega_al_sql[volcado_de] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_un_esquema_hostil_no_llega_al_sql[ensayo] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_un_esquema_hostil_no_llega_al_sql[insert] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_las_constantes_del_sql_son_las_del_dominio - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_sin_eventos_la_situacion_esta_vacia - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_r4_el_parte_y_el_ultimo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_solo_el_ultimo_en_duda[enviado] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_solo_el_ultimo_en_duda[sin_respuesta] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r4_un_rechazo_con_su_codigo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_un_idempotente_de_ensayo_es_parte_sin_ultimo_de_volcado - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r1_las_fechas_vuelven_en_utc_y_sin_zona_no_se_adivinan - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_una_situacion_con_columnas_de_mas_o_de_menos_no_se_lee[7] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r32_una_situacion_con_columnas_de_mas_o_de_menos_no_se_lee[9] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_la_fila_bloqueada_con_su_ultima_revision_y_su_volcado - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_una_fila_bloqueada_sin_revisiones - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_una_fila_bloqueada_con_columnas_de_mas_no_se_lee - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_el_ensayo_de_sus_filas - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_sin_filas_no_hay_ensayo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[una-de-otra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[todas-de-otra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[la-ultima-de-otra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[la-primera-de-otra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_de_la_persona_es_un_booleano_de_verdad - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_un_ensayo_cuyas_filas_no_casan_no_se_adivina[otra-obra] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_un_ensayo_cuyas_filas_no_casan_no_se_adivina[otra-hora] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_la_hora_del_ensayo_en_utc - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r4_r11_situaciones_una_entrada_por_cada_una_de_la_bandeja - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_situaciones_de_ninguna_no_abre_nada - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[falta-un-resultado] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[sobra-un-resultado] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[cruzados] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[otra-referencia] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[vacio] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r13_si_la_base_falla_al_guardar_el_ensayo_es_503_y_nada_a_medias - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_leer_ensayo_pasa_el_oid_y_no_lo_recibe - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_leer_un_ensayo_que_no_existe_es_none - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r17_b1_un_ensayo_de_otra_persona_lo_dice_la_base - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_si_la_base_no_responde_al_leer_es_503[situaciones] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_si_la_base_no_responde_al_leer_es_503[leer_ensayo] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_ninguna_elegida_no_inserta_y_cierra - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_r2_con_la_decision_real_del_dominio - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_si_la_decision_falla_no_se_escribe_y_se_deshace - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_si_la_base_falla_es_503_y_nada_a_medias[FOR UPDATE] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_si_la_base_falla_es_503_y_nada_a_medias[ORDER BY b.incidencia_id] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_si_la_base_falla_es_503_y_nada_a_medias[INSERT INTO] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r20_sin_pedidas_no_se_abre_nada - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r22_guardar_resultados_un_evento_por_parte_con_su_ensayo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno[falta-un-resultado] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno[sobra-un-resultado] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno[cruzados] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno[otra-referencia] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno[vacio] - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r25_si_la_base_falla_al_guardar_los_resultados_es_503_y_nada_a_medias - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_r34_ningun_log_del_repositorio_lleva_oid_ni_correo - NotImplementedError: F-059 T6
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_construir_volcados_abre_fija_la_sesion_y_asegura_el_esquema - AttributeError: module 'infrastructure.persistencia.fabrica' has no attribute 'construir_volcados'
FAILED services\postventa-api\tests\test_f059_repositorio_volcado.py::test_f059_t6_sin_contrasena_construir_volcados_no_abre_nada - AttributeError: module 'infrastructure.persistencia.fabrica' has no attribute 'construir_volcados'
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[situaciones_de_obra] - AssertionError: assert 2 == 4
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[situacion] - AssertionError: assert 2 == 4
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[aprobadas] - AssertionError: assert 2 == 4
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[situaciones_de_obra] - AssertionError: assert False
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[situacion] - AssertionError: assert False
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[aprobadas] - AssertionError: assert False
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r22_una_fila_con_su_ultima_y_su_original_con_la_suya - ValueError: zip() argument 2 is longer than argument 1
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma - AssertionError: assert 3 == 4
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r1_r4_una_fila_volcada_trae_su_parte_y_su_ultimo - AssertionError: assert None == SituacionDeVolcado(volcada=ParteEnSigrid(sigrid_ide=77, sigrid_cod='RS26.10/0001', at_utc=datetime.datetime(2026, 10, ... at_utc=datetime.datetime(2026, 10, 6, 9, 30, tzinf...
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r1_una_fila_en_duda[enviado] - AssertionError: assert <EstadoRevision.APROBADA: 'aprobada'> is <EstadoRevision.EN_DUDA: 'en_duda'>
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r1_una_fila_en_duda[sin_respuesta] - AssertionError: assert <EstadoRevision.APROBADA: 'aprobada'> is <EstadoRevision.EN_DUDA: 'en_duda'>
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r4_un_ultimo_rechazado_deja_la_aprobada_con_su_motivo - AssertionError: assert None is not None
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r4_la_original_de_una_duplicada_queda_sin_volcado - ValueError: zip() argument 2 is longer than argument 1
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r36_una_fila_sin_el_ancho_del_volcado_no_se_lee_a_medias[de-menos] - Failed: DID NOT RAISE ValueError
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r36_una_fila_sin_el_ancho_del_volcado_no_se_lee_a_medias[de-mas] - Failed: DID NOT RAISE ValueError
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r4_listar_y_situacion_traen_la_situacion_de_volcado - AssertionError: assert <EstadoRevision.APROBADA: 'aprobada'> is <EstadoRevision.VOLCADA: 'volcada'>
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r3_aprobadas_con_una_volcada_no_falla_y_no_la_devuelve - AssertionError: assert [UUID('000000...00000000003')] == [UUID('000000...00000000003')]
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado] - Failed: DID NOT RAISE AccionNoPermitida
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[sin_respuesta] - Failed: DID NOT RAISE AccionNoPermitida
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[creado] - Failed: DID NOT RAISE AccionNoPermitida
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[idempotente-de-ensayo] - Failed: DID NOT RAISE AccionNoPermitida
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_se_lee_tras_el_bloqueo_y_solo_la_de_la_propia - AssertionError: assert 'FROM postventa.volcados_sigrid v' in 'INSERT INTO postventa.revisiones_bandeja (incidencia_id, accion, unidad_codigo, unidad_nombre, ubicacion, descripcion...t_utc)\nVALUES (%s, %...
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_la_comprobacion_va_antes_que_la_frescura - domain.models.errores.RevisionDesactualizada: la incidencia ha cambiado desde que se leyó: vuelve a cargarla
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r2_si_la_base_falla_al_leer_el_volcado_es_503_y_nada_a_medias - Failed: DID NOT RAISE PersistenciaNoDisponible
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r33_las_situaciones_no_seleccionan_actor_oid[situaciones_de_obra] - AssertionError: assert 'vp.actor_correo' in 'SELECT b.incidencia_id, b.origen, b.importacion_id, b.fila_origen, b.obra_codigo, b.unidad_codigo, b.unidad_nombre, b...true\nWHERE b.obra_co...
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r33_las_situaciones_no_seleccionan_actor_oid[situacion] - AssertionError: assert 'vp.actor_correo' in 'SELECT b.incidencia_id, b.origen, b.importacion_id, b.fila_origen, b.obra_codigo, b.unidad_codigo, b.unidad_nombre, b...) uo ON true\nWHERE b.incidenci...
FAILED services\postventa-api\tests\test_f056_repositorio_revision.py::test_f059_r33_las_situaciones_no_seleccionan_actor_oid[aprobadas] - AssertionError: assert 'vp.actor_correo' in 'SELECT b.incidencia_id, b.origen, b.importacion_id, b.fila_origen, b.obra_codigo, b.unidad_codigo, b.unidad_nombre, b...ERE b.obra_codigo = %s AND u.ac...
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_un_ensayo_vigente_vale - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_no_existe - TypeError: validar_ensayo() missing 1 required keyword-only argument: 'actor_oid'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_de_otra_obra - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_de_otra_persona - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_r33_b1_el_dominio_no_ve_ningun_oid - AssertionError: assert ['ensayo_id',...c', 'eventos'] == ['ensayo_id',...c', 'eventos']
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado0] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado1] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_a_los_30_minutos_caduca[pasado2] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r17_el_orden_obra_persona_caducidad - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_esta - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[idempotente] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[rechazado] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_fuera_del_ensayo_si_no_salio_previsto[no_procesado] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_revision_desactualizada_si_la_pedida_no_es_la_del_ensayo - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r18_lo_del_ensayo_antes_que_lo_de_la_base - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_hay_otra_revision_despues_del_ensayo - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[editar] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[descartar] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[recuperar] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar[None] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_r27_ya_volcada_con_su_codigo - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_ya_volcada_antes_que_la_revision - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado0] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado1] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado2] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar[volcado3] - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r7_r20_huella_no_coincide - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_no_es_de_la_bandeja_si_no_se_pudo_bloquear - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_las_excluidas_en_el_orden_pedido - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r20_ninguna_elegible - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_r15_pedidas_repetidas - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
FAILED services\postventa-api\tests\test_f059_volcado_dominio.py::test_f059_los_tipos_son_inmutables - TypeError: Ensayo.__init__() got an unexpected keyword argument 'de_la_persona'
171 failed, 328 passed in 6.92s
```

Y los doce del grupo A de R41, que en la RED se ponen rojos **porque piden el `16_`** (son exactamente los doce
del inventario de B-2, ni uno más):

```
COLUMNS=400 $R/.venv/Scripts/python.exe -m pytest $R/tests/test_f005_ddl_idempotente_texto.py $R/tests/test_f056_ddl.py \
  $R/tests/test_f028_ddl_historico.py $R/tests/test_f030_veredicto_persistido.py $R/tests/test_f031_alcance_cerrado.py \
  $R/tests/test_f032_alcance_cerrado.py $R/tests/test_f033_alcance_cerrado.py $R/tests/test_f034_alcance_cerrado.py \
  $R/tests/test_f036_ddl.py $R/tests/test_f056_alcance_cerrado.py $R/tests/test_f060_alcance_cerrado.py -q -p no:cacheprovider --tb=no -rf
```

```
FAILED services\postventa-api\tests\test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden - AssertionError: assert ['01_esquema....res.sql', ...] == ['01_esquema....res.sql', ...]
FAILED services\postventa-api\tests\test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_de_los_de_f036 - AssertionError: assert '14_decisione...ivalencia.sql' == '15_revisiones_bandeja.sql'
FAILED services\postventa-api\tests\test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo - AssertionError: assert ['postventa.r...isado_correo'] == ['postventa.r...actor_correo']
FAILED services\postventa-api\tests\test_f028_ddl_historico.py::test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo - AssertionError: assert ['12_importac..._bandeja.sql'] == ['12_importac...s_sigrid.sql']
FAILED services\postventa-api\tests\test_f030_veredicto_persistido.py::test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
FAILED services\postventa-api\tests\test_f031_alcance_cerrado.py::test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
FAILED services\postventa-api\tests\test_f032_alcance_cerrado.py::test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
FAILED services\postventa-api\tests\test_f033_alcance_cerrado.py::test_f033_no_hay_ni_un_fichero_de_ddl_nuevo - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
FAILED services\postventa-api\tests\test_f034_alcance_cerrado.py::test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
FAILED services\postventa-api\tests\test_f036_ddl.py::test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden - AssertionError: assert ['12_importac..._bandeja.sql'] == ['12_importac...s_sigrid.sql']
FAILED services\postventa-api\tests\test_f056_alcance_cerrado.py::test_f056_r12_solo_15_declara_una_columna_de_correo - AssertionError: assert ['15_revisiones_bandeja.sql'] == ['15_revision...s_sigrid.sql']
FAILED services\postventa-api\tests\test_f060_alcance_cerrado.py::test_f060_r37_los_sql_son_los_quince_de_antes - AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
12 failed, 274 passed, 95 skipped in 57.26s
```

### T5 · `16_volcados_sigrid.sql` (`54c3278`)

El `CREATE TABLE IF NOT EXISTS postventa.volcados_sigrid` y los dos `CREATE INDEX IF NOT EXISTS` de `design.md`
§9, **literales**, y la cabecera de §9: qué construye y de qué lee (`13_` y `15_`); append-only y manda el
`evento_id`; la escritura anticipada dentro de la transacción del `FOR UPDATE`, nunca consultivo; el estado de
la incidencia no se guarda; los `CHECK` de `modo` y `estado` son los `Enum` y no se pueden ampliar después;
qué dicen los cuatro de fila; **sin índice único a propósito** (R26); `actor_oid` seudónimo, que **no se lee
nunca** (la base lo compara, B-1 (a)); `actor_correo` de un empleado interno, que solo devuelve
`GET /api/revision` y nunca va a un log; ni textos, ni nombres, ni el login, ni el `motivo.mensaje`; sin
`ON DELETE CASCADE`; listas para F-048. Sin tildes en los comentarios, como el `15_`. **Solo el esquema
`postventa`; nada de servidor; nada se ha aplicado contra ninguna base** (eso es T8, con la efímera).

Verificación de `tasks.md` T5 (los doce ficheros): **323 passed, 95 skipped in 58.85s** (los `skipped` son los
controles de `git` de las ramas de F-030–F-036, F-056 y F-060, que fuera de la suya se saltan). La primera
pasada dio un rojo mío: la frase «empleado interno» de la cabecera partida entre dos líneas; reajustado el
comentario.

### T6 · El puerto, los repositorios y lo de §12 (`cf3b7a2`)

| Fichero | Qué |
|---|---|
| `domain/ports/volcado.py` (nuevo) | `RepositorioVolcadoPort` (las cinco operaciones de §8.1 enmendado) y el alias `DecisionDelVolcado` (la firma de `decidir`). Sin `VolcadoSigridPort`, que es T11 |
| `infrastructure/persistencia/sentencias_volcado.py` (nuevo) | Puro y **hoja** (no importa `sentencias_revision.py`): `columnas_del_volcado` y `joins_del_volcado` (las dos `LATERAL`, que también usa `_select_situaciones`), `select_volcado_de`, `select_ensayo`, `insert_evento` con `EventoNuevo`, y `fila_a_volcado`, `fila_a_bloqueada`, `filas_a_ensayo` |
| `infrastructure/persistencia/repositorio_volcado_pg.py` (nuevo) | `RepositorioVolcadoPostgres(_Transaccional)`: `situaciones`, `guardar_ensayo`, `leer_ensayo`, `anotar_enviados` (R20) y `guardar_resultados` |
| `infrastructure/persistencia/fabrica.py` | `construir_volcados` (la receta de `construir_revision`; fuera de `__all__`) |
| `infrastructure/persistencia/sentencias_revision.py` | `_select_situaciones` gana las dos `LATERAL` (de la propia, `b`) y sus ocho columnas al final; `fila_a_situacion` llena `volcado` (`None` sin eventos; la original, `None`). `select_bloquear`, `select_ultimas_revisiones` e `insert_revision`, **sin cambios** |
| `infrastructure/persistencia/repositorio_revision_pg.py` | `_registrar`: tras `select_bloquear` y `select_ultimas_revisiones`, `_exigir_que_no_este_volcada` (la sentencia nueva de `sentencias_volcado.py`, solo de la propia) **antes** de la comprobación de frescura; `aprobadas`: deja fuera la `volcada` antes de `candidata_de`. `registrar_lote` y `_registrar_lote`, **sin cambios** |
| `domain/models/volcado.py` (Bloque 1, por B-1 (a)) | `Ensayo.actor_oid: str` → `Ensayo.de_la_persona: bool`; `validar_ensayo(ensayo, *, obra, ahora)` con `if not ensayo.de_la_persona`, en el mismo orden de motivos |

**Decisiones de diseño (para la review del Bloque 2):**

1. **`aprobadas` deja fuera la `volcada` con `estado_de(s) is not VOLCADA`, no con `es_candidata`.** §12 dice
   «filtra con `es_candidata` antes de `candidata_de`», y lo que busca es que una `volcada` (última `aprobar`)
   no haga fallar a la obra entera. Filtrar con `es_candidata` lo conseguiría, pero se **tragaría en silencio**
   una fila cuya última revisión no fuera un `aprobar` —que el SQL no debería devolver nunca—, y eso es justo
   la doble defensa de R34 que fija `test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa`
   (espera `ValueError`): con `es_candidata` ese test de F-056 se pondría rojo y habría que **relajarlo**. Con el
   filtro estrecho, la `volcada` sale fuera, la `en_duda` pasa (R3) y lo imposible sigue explotando. Lo
   distinguen los mutantes a mano A04 y A05. Si la review prefiere la letra de §12, el cambio es una línea, pero
   obliga a relajar ese test.
2. **R2 en `_registrar`, entre la lectura de las últimas y su comprobación.** El orden de las sentencias es
   `FOR UPDATE` → `max(revision_id)` → la situación de volcado → (R2) → (frescura) → `INSERT`. Así la lectura va
   tras el bloqueo y dentro de la transacción, y la comprobación de R2 va **antes** de la de frescura (§12):
   si las dos fallan, manda la de R2. Y las dos primeras sentencias quedan donde estaban, que es lo que fija
   `test_f056_r7_r22_bloquea_las_dos_en_orden_fijo_y_mira_las_dos` (sin tocar).
3. **Los estados que bloquean, escritos uno a uno** (`_BLOQUEAN_LA_REVISION = {VOLCADA, EN_DUDA}`, D-14), en vez
   de `estado is not None` (cambio de T9: ver «Mutantes a mano»).
4. **Las `LATERAL` llevan literales** (`'creado', 'idempotente'` y `'volcado'`), compuestos con `valores_check`
   desde `ESTADOS_CON_PARTE` y `ModoVolcado`: no son valores recibidos. Pasarlos como parámetros habría
   desplazado los de `select_situaciones_de_obra`, `select_situacion` y `select_aprobadas`, que fijan tres
   tests de F-056 que no están en R41.
5. **`volcado` es `None` en una fila sin eventos**, no `SituacionDeVolcado(None, None)`: R4 dice `null`, y así
   las igualdades de los tests de F-056 y F-060 que construyen la situación sin `volcado` siguen valiendo. En
   `situaciones` del repositorio nuevo, en cambio, `SituacionDeVolcado(None, None)` (§8.1 enmendado).
6. **`filas_a_ensayo`** exige que las filas casen en obra y hora (se guardan juntas); si no, `ValueError`: no se
   elige una. `de_la_persona` = `all(...)` sobre la comparación de cada fila.
7. **`guardar_ensayo` y `guardar_resultados` sin partes** → `ValueError` (uno a uno exige al menos uno); y
   `anotar_enviados` sin pedidas, igual. Ninguno abre nada.
8. **`anotar_enviados`** anota el `enviado` con la obra **del ensayo** (ya validada contra la petición por
   `validar_ensayo`), su `ensayo_id`, la referencia de `referencia_de` y la revisión y la huella del evento del
   ensayo (las que la decisión ha comprobado contra la fila bloqueada). Devuelve la decisión tal cual.
9. **Los logs del repositorio**: la llamada, la obra y los recuentos. La referencia de cada parte la registrará
   la aplicación (R34, Bloque 4).

Verificación de `tasks.md` T6: **520 passed, 73 skipped in 21.91s** a la primera. **Suite entera del servicio**
tras T6 (`pytest <repo>/services/postventa-api/tests -q`, desde el scratchpad): **8592 passed, 129 skipped in
1285.55s**, sin un rojo.

### T7 · `tests_bbdd/tests/test_f059_bbdd_volcado.py` (`9b4c8d5`)

46 casos (16 funciones con su parametrización), con la base efímera y la limpieza de F-056 (que borra también
`volcados_sigrid`, antes y después de cada test, para que `test_f060_bbdd_lote.py`, que va después, pueda vaciar
`revisiones_bandeja`). Obra `9904`, identificadores `uuid4`.

- DDL dos veces sin cambiar nada (16 columnas) y nada en `public`; ningún índice único salvo la clave primaria.
- La fila válida entra; **26 que la base rechaza**: estado y modo desconocidos, `creado` sin `cod` o sin `ide`,
  `enviado` con `ide` y `cod`, `rechazado` y `no_procesado` sin motivo, `ensayo` con `ensayo_id`, `volcado` sin
  él, un ensayo `enviado`, `sin_respuesta` o `creado`, referencia sin `PVI-`, en minúsculas o de 81, motivo vacío
  o de 65, `cod` de 25, correo de 255 o de 2, y los seis `NOT NULL`; y **6 que el dominio escribe y entran**.
- Las dos claves ajenas (incidencia y revisión que no existen).
- Append-only: un segundo ensayo añade y deja el primero igual.
- **B-1 (a)**: `leer_ensayo` con el `oid` de quien ensayó → `de_la_persona` verdadero; con otro → falso; los
  eventos en su orden; un ensayo que no existe → `None`.
- La derivación de §4.1 leída de la base: aprobada → `enviado` = `en_duda` → `sin_respuesta` = `en_duda` (y
  candidata) → `rechazado` = `aprobada` con su motivo y el correo → `creado` y luego `sin_respuesta` = `volcada`
  (gana) y fuera de `aprobadas`; un `idempotente` de ensayo deja `volcada`, sin último de modo `volcado`;
  `registrar` sobre una `en_duda` → 409 sin escribir.
- **Dos conexiones**: (a) la edición tiene la fila bloqueada → la escritura anticipada **espera** y luego la
  excluye `revision_desactualizada`; (a') la escritura anticipada tiene la fila bloqueada (la decisión real
  espera dentro) → `registrar` **espera** y luego recibe 409 `en_duda`; (b) dos `anotar_enviados` → el segundo
  espera y los dos anotan su `enviado`, con una sola referencia; (c) la escritura anticipada bloquea `[z, y]` y
  el lote de F-060 `[y, z]`: el lote espera, **sin interbloqueo**, y salta `y` (ya no es su esperada) y escribe
  `z`.

Verificación de `tasks.md` T7 (desde el scratchpad):

```
$R/.venv/Scripts/python.exe -m pytest --collect-only -q -p no:cacheprovider $R/tests_bbdd/tests/test_f059_bbdd_volcado.py
46 tests collected in 0.90s
```

No se ha ejecutado contra ninguna base (regla del encargo): sin `POSTVENTA_PG_TEST_DSN` todos se saltan.

### T8 · MANUAL (humano) — preparada, **no ejecutada**

Con Docker Desktop arrancado, desde la raíz del repositorio:

```
powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
```

Debe salir **en verde** `tests_bbdd/tests/test_f059_bbdd_volcado.py` (**46** casos) junto con los de F-005,
F-036, F-056 y `test_f060_bbdd_lote.py`. Lo que hay que mirar, por si algo sale rojo:

- Los tres de dos conexiones esperan 1 s (`ESPERA`) a que la otra conexión esté de verdad esperando al
  `FOR UPDATE`; si la máquina va muy cargada y un `assert hilo.is_alive()` falla, no es un defecto: repetir.
  Si alguno acaba en `DeadlockDetected` o el hilo no termina en 10 s, **sí** lo es (§21.5).
- `test_f060_bbdd_lote.py` corre **después** del de F-059: si su limpieza falla con `ForeignKeyViolation`, es
  que alguna fila de `volcados_sigrid` quedó sin borrar.

Anotar aquí: el número de tests que pasan y el tiempo. Bloquea el cierre de F-059.

### T9 · Mutación del bloque (`64b25b8`, `42be797`, `55f27f5` y el de este informe)

Base: **`13f9f51`** (el commit anterior a T4). El alcance incluye las líneas del Bloque 1 que cambia B-1 (a)
(`domain/models/volcado.py`, 13 líneas: `Ensayo` y `validar_ensayo`).

#### Cómo se llegó a la campaña final (sin maquillar)

Antes de la campaña, **mutantes a mano** en un worktree desechable (lote 1, sobre `9b4c8d5`): 61, y 5 sobrevivían
y 1 lo cazaba solo un test de F-056. Cada uno se resolvió **en el código o con un test de F-059**, no con una
justificación:

| Hallazgo | Qué se hizo |
|---|---|
| V04 · `_con_zona` con `not instante.tzinfo` sobrevive | Test nuevo: una zona válida que se evalúa como falsa sigue siendo una zona (`test_f059_r32_lo_que_decide_la_zona_es_que_la_haya_y_no_su_veracidad`) |
| V05 · R2 con `if estado:` sobrevive | El código pasa a la lista explícita `_BLOQUEAN_LA_REVISION = {VOLCADA, EN_DUDA}` (D-14), cuyos mutantes sí se distinguen (lote 2: V05a–c muertos) |
| F09, F10, G04 · las comprobaciones de ancho sobreviven | Eran **redundantes** (los `zip` estrictos ya lo comprobaban); se quitan, y las filas se leen **desempaquetando** (`ide, cod, … = fila`; `incidencia, revision_id, accion, huella, *volcado = fila`): un solo mecanismo, sin código muerto (`42be797`) |
| G05 · las `LATERAL` sobre la original: solo lo cazaba la aserción que añadí **dentro** de `test_f056_r22_r38_…` | Test nuevo de F-059: `test_f059_r1_r4_las_lateral_del_volcado_son_de_la_propia` |

Una **primera campaña de la herramienta** sobre `42be797` (29 mutantes) la **paré** a los 22: dos supervivientes
(`repositorio_volcado_pg.py:253`, `strict=True` → `False` en `_exigir_que_casen`, y `sentencias_volcado.py:118`,
`EventoNuevo` sin `frozen`). El primero era redundante (la longitud se comprueba justo antes) y se quita el
`strict` de los tres `zip` que van detrás de esa comprobación; el segundo tenía un hueco real y gana
`test_f059_r32_el_evento_por_escribir_es_inmutable` (`55f27f5`). **Hallazgo, para que conste**: esa misma
campaña dio por **muerto** el mutante gemelo de la línea 123 (`strict=False` en `guardar_ensayo`), que es
**equivalente** (mismo motivo: las longitudes ya son iguales). Lo tumbó otro test de la suite bajo carga, no uno
que lo vigile, como ya pasó en el Bloque 1 con `PosibleDuplicado`. Por eso, abajo, cada mutante de la herramienta
se **reverifica contra los tests de F-059 solos**. Al pararla, sus ocho worktrees los retiré (`git worktree
remove --force` y `prune`); no quedó ningún `pytest` del venv de este proyecto (comprobado), y no toqué los
procesos de otras sesiones.

#### La campaña final de la herramienta

```
cd <scratchpad>/f059
PYTHONPATH=<repo> python -m harness.mutacion --feature F-059 --base 13f9f51 --timeout 1800 --workers 8 \
  --raiz <repo> --salida <repo>/progress/mutacion_F-059_bloque2.md
26 mutantes evaluados, 26 muertos, 0 supervivientes, 0 timeouts en 4484.1 s
```

Sobre `HEAD` `55f27f5`; alcance: **848** líneas de producción en siete ficheros (`domain/models/volcado.py` 13,
`domain/ports/volcado.py` 116, `fabrica.py` 17, `repositorio_revision_pg.py` 49, `repositorio_volcado_pg.py` 290,
`sentencias_revision.py` 33, `sentencias_volcado.py` 330); **8 workers** (los de `harness/rigor.json`, pasados a
mano porque se lanzó desde el scratchpad); ningún timeout que repasar. Informe completo:
`progress/mutacion_F-059_bloque2.md` (su primera línea, que la herramienta escribió con la ruta absoluta del
equipo, la he dejado relativa como las demás). Como en el Bloque 1 (P-2 de su review), la cabecera del informe
no repite `--timeout 1800`. Pocos mutantes para tanto alcance: el puerto son declaraciones y casi todo lo demás
es SQL en textos, que la herramienta no muta; por eso los mutantes a mano de abajo.

#### Reverificación de cada mutante de la herramienta contra los tests de F-059 solos

Con `generar_mutantes` y `aplicar_mutante` de la propia herramienta, el mismo alcance y la misma base, sobre
`55f27f5` en un worktree desechable (retirado), ejecutando solo los `test_f059_*` de los cinco ficheros del
bloque (`-k test_f059`, `-x`): **26 de 26 muertos por tests de F-059**.

| N.º | Fichero:línea | Operador | Original → mutado | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|---|
| 1 | `volcado.py:541` | not | if not ensayo.de_la_persona: -> if ensayo.de_la_persona: | muerto (F-059) | `test_f059_r17_un_ensayo_vigente_vale` |
| 2 | `repositorio_revision_pg.py:236` | not | if not filas: -> if filas: | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| 3 | `repositorio_revision_pg.py:238` | entero | _, bloqueada = sentencias_volcado.fila_a_bloqueada(filas[0]) -> _, bloqueada = sentencias_volcado.fila_a_bloqueada(filas[1]) | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| 4 | `repositorio_volcado_pg.py:85` | not | if not incidencias: -> if incidencias: | muerto (F-059) | `test_f059_r4_r11_situaciones_una_entrada_por_cada_una_de_la_bandeja` |
| 5 | `repositorio_volcado_pg.py:156` | not | if not pedidas: -> if pedidas: | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| 6 | `repositorio_volcado_pg.py:251` | not | if not partes or len(partes) != len(resultados): -> if partes or len(partes) != len(resultados): | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| 7 | `repositorio_volcado_pg.py:251` | logico | if not partes or len(partes) != len(resultados): -> if not partes and len(partes) != len(resultados): | muerto (F-059) | `test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[falta-un-resultado]` |
| 8 | `repositorio_volcado_pg.py:251` | comparacion | if not partes or len(partes) != len(resultados): -> if not partes or len(partes) == len(resultados): | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| 9 | `repositorio_volcado_pg.py:256` | comparacion | if (parte.incidencia_id, parte.referencia_externa) != ( -> if (parte.incidencia_id, parte.referencia_externa) == ( | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| 10 | `sentencias_revision.py:337` | aritmetico | fin_ultima_original = fin_original + _ANCHO_REVISION -> fin_ultima_original = fin_original - _ANCHO_REVISION | muerto (F-059) | `test_f059_r4_una_fila_sin_eventos_no_tiene_volcado` |
| 11 | `sentencias_revision.py:346` | comparacion | volcado=None if volcado == _SIN_EVENTOS else volcado, -> volcado=None if volcado != _SIN_EVENTOS else volcado, | muerto (F-059) | `test_f059_r4_una_fila_sin_eventos_no_tiene_volcado` |
| 12 | `sentencias_volcado.py:118` | booleano | @dataclass(frozen=True) -> @dataclass(frozen=False) | muerto (F-059) | `test_f059_r32_el_evento_por_escribir_es_inmutable` |
| 13 | `sentencias_volcado.py:217` | aritmetico | f"VALUES ({', '.join(['%s'] * len(COLUMNAS_INSERT))})" -> f"VALUES ({', '.join(['%s'] // len(COLUMNAS_INSERT))})" | muerto (F-059) | `test_f059_r32_el_insert_es_una_fila_sin_on_conflict` |
| 14 | `sentencias_volcado.py:290` | not | if not filas: -> if filas: | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 15 | `sentencias_volcado.py:292` | entero | if len({(fila[0], fila[1]) for fila in filas}) != 1: -> if len({(fila[1], fila[1]) for fila in filas}) != 1: | muerto (F-059) | `test_f059_r17_un_ensayo_cuyas_filas_no_casan_no_se_adivina[otra-obra]` |
| 16 | `sentencias_volcado.py:292` | entero | if len({(fila[0], fila[1]) for fila in filas}) != 1: -> if len({(fila[0], fila[2]) for fila in filas}) != 1: | muerto (F-059) | `test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[la-ultima-de-otra]` |
| 17 | `sentencias_volcado.py:292` | comparacion | if len({(fila[0], fila[1]) for fila in filas}) != 1: -> if len({(fila[0], fila[1]) for fila in filas}) == 1: | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 18 | `sentencias_volcado.py:292` | entero | if len({(fila[0], fila[1]) for fila in filas}) != 1: -> if len({(fila[0], fila[1]) for fila in filas}) != 2: | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 19 | `sentencias_volcado.py:294` | entero | primera = filas[0] -> primera = filas[1] | muerto (F-059) | `test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[una-de-otra]` |
| 20 | `sentencias_volcado.py:297` | entero | obra_codigo=primera[0], -> obra_codigo=primera[1], | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 21 | `sentencias_volcado.py:298` | entero | de_la_persona=all(fila[2] for fila in filas), -> de_la_persona=all(fila[3] for fila in filas), | muerto (F-059) | `test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[una-de-otra]` |
| 22 | `sentencias_volcado.py:299` | entero | at_utc=_con_zona(primera[1]), -> at_utc=_con_zona(primera[2]), | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 23 | `sentencias_volcado.py:302` | entero | incidencia_id=como_uuid(fila[3]), -> incidencia_id=como_uuid(fila[4]), | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 24 | `sentencias_volcado.py:303` | entero | revision_id=fila[4], -> revision_id=fila[5], | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 25 | `sentencias_volcado.py:304` | entero | huella=fila[5], -> huella=fila[6], | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| 26 | `sentencias_volcado.py:305` | entero | estado=EstadoEvento(fila[6]), -> estado=EstadoEvento(fila[7]), | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |

#### Mutantes a mano (lo que la herramienta no muta)

La herramienta no genera `x is not None` → `x` ni `x is None` → `not x` (lección del Bloque 1), ni toca textos,
alias, el orden de los argumentos, qué columna se usa ni qué se devuelve. Tres lotes, en worktrees desechables
(retirados; el árbol de trabajo no se ha mutado nunca), solo con los `test_f059_*` de los cinco ficheros del
bloque y, si sobrevivía, con los ficheros enteros.

**Lote 1** (sobre `9b4c8d5`, 61 mutantes). Los cinco supervivientes y el de G05 son los de la tabla de arriba;
V01, V02, F01–F03 se repiten en el lote 3 sobre el código reescrito (sus textos cambiaron), y V05, F09, F10 y
G04 dejaron de existir con los cambios de T9.

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| V01 | `infrastructure/persistencia/sentencias_volcado.py` | parte por veracidad del ide | muerto (F-059) | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| V02 | `infrastructure/persistencia/sentencias_volcado.py` | último por veracidad del estado | muerto (F-059) | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| V03 | `infrastructure/persistencia/sentencias_volcado.py` | acción vacía tomada por sin revisión | muerto (F-059) | `test_f059_r20_una_accion_vacia_no_es_sin_revision` |
| V04 | `infrastructure/persistencia/sentencias_volcado.py` | _con_zona por veracidad | **sobrevive** | `` |
| V05 | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 por veracidad del estado | **sobrevive** | `` |
| S01 | `infrastructure/persistencia/sentencias_volcado.py` | el parte: el último en vez del primero | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S02 | `infrastructure/persistencia/sentencias_volcado.py` | el último: el primero | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S03 | `infrastructure/persistencia/sentencias_volcado.py` | el último de modo ensayo | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S04 | `infrastructure/persistencia/sentencias_volcado.py` | parte solo con creado | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S05 | `infrastructure/persistencia/sentencias_volcado.py` | parte con cualquier estado | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S06 | `infrastructure/persistencia/sentencias_volcado.py` | volcado_de sin orden fijo | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S07 | `infrastructure/persistencia/sentencias_volcado.py` | la primera revisión en vez de la última | muerto (F-059) | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| S08 | `infrastructure/persistencia/sentencias_volcado.py` | ensayo leído de modo volcado | muerto (F-059) | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| S09 | `infrastructure/persistencia/sentencias_volcado.py` | el ensayo selecciona actor_oid | muerto (F-059) | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| S10 | `infrastructure/persistencia/sentencias_volcado.py` | el ensayo al revés | muerto (F-059) | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| S11 | `infrastructure/persistencia/sentencias_volcado.py` | oid y correo cruzados | muerto (F-059) | `test_f059_r32_el_insert_es_una_fila_sin_on_conflict` |
| S12 | `infrastructure/persistencia/sentencias_volcado.py` | insert sin pasar a UTC | muerto (F-059) | `test_f059_r32_no_se_escribe_una_hora_sin_zona` |
| S13 | `infrastructure/persistencia/sentencias_volcado.py` | insert sin el motivo | muerto (F-059) | `test_f059_r32_el_insert_de_un_ensayo_sin_ensayo_id_y_con_motivo` |
| S14 | `infrastructure/persistencia/sentencias_volcado.py` | ensayo sin filtrar el modo | muerto (F-059) | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| F01 | `infrastructure/persistencia/sentencias_volcado.py` | correo del parte cruzado | muerto (F-059) | `test_f059_r1_r4_el_parte_y_el_ultimo` |
| F02 | `infrastructure/persistencia/sentencias_volcado.py` | sin motivo | muerto (F-059) | `test_f059_r4_un_rechazo_con_su_codigo` |
| F03 | `infrastructure/persistencia/sentencias_volcado.py` | parte sin UTC | muerto (F-059) | `test_f059_r1_las_fechas_vuelven_en_utc_y_sin_zona_no_se_adivinan` |
| F04 | `infrastructure/persistencia/sentencias_volcado.py` | persona con una sola fila | muerto (F-059) | `test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[la-ultima-de-otra]` |
| F05 | `infrastructure/persistencia/sentencias_volcado.py` | ensayo sin comprobar que casan | muerto (F-059) | `test_f059_r17_un_ensayo_cuyas_filas_no_casan_no_se_adivina[otra-obra]` |
| F06 | `infrastructure/persistencia/sentencias_volcado.py` | eventos del ensayo al revés | muerto (F-059) | `test_f059_r17_el_ensayo_de_sus_filas` |
| F07 | `infrastructure/persistencia/sentencias_volcado.py` | ensayo sin UTC | muerto (F-059) | `test_f059_r17_la_hora_del_ensayo_en_utc` |
| F08 | `infrastructure/persistencia/sentencias_volcado.py` | bloqueada sin huella | muerto (F-059) | `test_f059_r20_la_fila_bloqueada_con_su_ultima_revision_y_su_volcado` |
| F09 | `infrastructure/persistencia/sentencias_volcado.py` | volcado sin comprobar el ancho | **sobrevive** | `` |
| F10 | `infrastructure/persistencia/sentencias_volcado.py` | bloqueada sin comprobar el ancho | **sobrevive** | `` |
| R01 | `infrastructure/persistencia/repositorio_volcado_pg.py` | anotar sin bloquear | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R02 | `infrastructure/persistencia/repositorio_volcado_pg.py` | decidir sin lo leído | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R03 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado anotado como previsto | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R04 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado sin ensayo_id | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R05 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado con la llamada del ensayo | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R06 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado de modo ensayo | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R07 | `infrastructure/persistencia/repositorio_volcado_pg.py` | no anota ningún enviado | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R08 | `infrastructure/persistencia/repositorio_volcado_pg.py` | ensayo con ensayo_id | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| R09 | `infrastructure/persistencia/repositorio_volcado_pg.py` | resultado sin ensayo_id | muerto (F-059) | `test_f059_r22_guardar_resultados_un_evento_por_parte_con_su_ensayo` |
| R10 | `infrastructure/persistencia/repositorio_volcado_pg.py` | casan sin mirar la referencia | muerto (F-059) | `test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[otra-referencia]` |
| R11 | `infrastructure/persistencia/repositorio_volcado_pg.py` | casan admite vacío | muerto (F-059) | `test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno[vacio]` |
| R12 | `infrastructure/persistencia/repositorio_volcado_pg.py` | situaciones abre sin pedidas | muerto (F-059) | `test_f059_t6_situaciones_de_ninguna_no_abre_nada` |
| R13 | `infrastructure/persistencia/repositorio_volcado_pg.py` | anotar sin pedidas abre | muerto (F-059) | `test_f059_r20_sin_pedidas_no_se_abre_nada` |
| R14 | `infrastructure/persistencia/repositorio_volcado_pg.py` | evento con otra huella | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| R15 | `infrastructure/persistencia/repositorio_volcado_pg.py` | evento con otra obra | muerto (F-059) | `test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden` |
| R16 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado con otra obra | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| R17 | `infrastructure/persistencia/repositorio_volcado_pg.py` | enviado con otra revisión | muerto (F-059) | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| A01 | `infrastructure/persistencia/repositorio_revision_pg.py` | registrar sin R2 | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| A02 | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 después de la frescura | muerto (F-059) | `test_f059_r2_la_comprobacion_va_antes_que_la_frescura` |
| A03 | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 sobre más de la propia (se define _todas) | muerto (F-059) | `test_f059_r2_se_lee_tras_el_bloqueo_y_solo_la_de_la_propia` |
| A04 | `infrastructure/persistencia/repositorio_revision_pg.py` | aprobadas filtra con es_candidata (pierde la doble defensa) | muerto (F-059) | `test_f059_r3_aprobadas_con_una_volcada_no_falla_y_no_la_devuelve` |
| A05 | `infrastructure/persistencia/repositorio_revision_pg.py` | aprobadas sin filtro | muerto (F-059) | `test_f059_r3_aprobadas_con_una_volcada_no_falla_y_no_la_devuelve` |
| A06 | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 con otro estado | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| A07 | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 con acciones | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| G01 | `infrastructure/persistencia/sentencias_revision.py` | volcado nunca None | muerto (F-059) | `test_f059_r4_una_fila_sin_eventos_no_tiene_volcado` |
| G02 | `infrastructure/persistencia/sentencias_revision.py` | volcado siempre None | muerto (F-059) | `test_f059_r1_r4_una_fila_volcada_trae_su_parte_y_su_ultimo` |
| G03 | `infrastructure/persistencia/sentencias_revision.py` | la original con volcado | muerto (F-059) | `test_f059_r4_la_original_de_una_duplicada_queda_sin_volcado` |
| G04 | `infrastructure/persistencia/sentencias_revision.py` | situación sin comprobar el ancho | **sobrevive** | `` |
| G05 | `infrastructure/persistencia/sentencias_revision.py` | las LATERAL de la original | muerto **solo por otra suite** | `test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[situaciones_de_obra]` |
| D01 | `domain/models/volcado.py` | persona nunca falla | muerto (F-059) | `test_f059_r17_de_otra_persona` |
| D02 | `domain/models/volcado.py` | persona antes que obra | muerto (F-059) | `test_f059_r17_el_orden_obra_persona_caducidad` |
| B01 | `infrastructure/persistencia/fabrica.py` | fábrica con el esquema fijo | muerto (F-059) | `test_f059_t6_construir_volcados_abre_fija_la_sesion_y_asegura_el_esquema` |

**Lote 2** (sobre `64b25b8`, 9): lo que cambió T9.

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| V04 | `infrastructure/persistencia/sentencias_volcado.py` | _con_zona por veracidad (con el test nuevo) | muerto (F-059) | `test_f059_r32_lo_que_decide_la_zona_es_que_la_haya_y_no_su_veracidad` |
| V05a | `infrastructure/persistencia/repositorio_revision_pg.py` | R2: in por not in | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| V05b | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 sin en_duda | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| V05c | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 sin volcada | muerto (F-059) | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[creado]` |
| V05d | `infrastructure/persistencia/repositorio_revision_pg.py` | R2 por veracidad | **sobrevive** | `` |
| F09a | `infrastructure/persistencia/sentencias_volcado.py` | zip del parte no estricto | **sobrevive** | `` |
| F09b | `infrastructure/persistencia/sentencias_volcado.py` | zip del último no estricto | muerto (F-059) | `test_f059_r32_una_situacion_con_columnas_de_mas_o_de_menos_no_se_lee[7]` |
| G05 | `infrastructure/persistencia/sentencias_revision.py` | las LATERAL de la original (con el test nuevo) | muerto (F-059) | `test_f059_r1_r4_las_lateral_del_volcado_son_de_la_propia[situaciones_de_obra]` |
| G06 | `infrastructure/persistencia/sentencias_revision.py` | volcado recortado a 8 (columnas de más no se notan) | muerto (F-059) | `test_f059_r36_una_fila_sin_el_ancho_del_volcado_no_se_lee_a_medias[de-mas]` |

**F09a** (el `zip` del parte sin `strict`) sobrevivía por lo mismo que F09 en el lote 1: la comprobación era
redundante, porque el `zip` del último ya rechazaba cualquier ancho distinto. Es lo que llevó a reescribir la
lectura desempaquetando (`42be797`): el mutante deja de existir, y lo que ahora vigila el ancho (desempaquetar)
lo cazan F12 y F14 del lote 3.

**V05d no es un superviviente: no cambia el programa.** Sustituye `estado in _BLOQUEAN_LA_REVISION` por
`if estado:`. `estado` sale de `estado_de_volcado`, que solo devuelve `None`, `EstadoVolcado.VOLCADA` o
`EstadoVolcado.EN_DUDA`; los dos miembros son textos no vacíos (verdaderos) y los dos están en el conjunto, y
`None` es falso y no está. Para cualquier entrada posible las dos líneas hacen lo mismo: no hay comportamiento
que un test pueda distinguir. Es la misma categoría que A5 y A8 de la re-review del Bloque 1. Lo dejo escrito
para que el humano lo vea; si prefiere la regla al pie de la letra, basta con su visto bueno a este párrafo.

> **Cerrado el 2026-10-16: el humano acepta por escrito el mutante equivalente V05d** (opción «Sí, lo acepto»,
> transmitida por el líder tras la review del Bloque 2, APPROVED en `8e668b2`).

**Lote 3** (sobre `42be797`, 13): las filas leídas desempaquetando.

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| V01 | `infrastructure/persistencia/sentencias_volcado.py` | parte por veracidad del ide | muerto (F-059) | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| V02 | `infrastructure/persistencia/sentencias_volcado.py` | último por veracidad del estado | muerto (F-059) | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| V03 | `infrastructure/persistencia/sentencias_volcado.py` | acción vacía tomada por sin revisión | muerto (F-059) | `test_f059_r20_una_accion_vacia_no_es_sin_revision` |
| F01 | `infrastructure/persistencia/sentencias_volcado.py` | correo del parte cruzado | muerto (F-059) | `test_f059_r1_r4_el_parte_y_el_ultimo` |
| F01b | `infrastructure/persistencia/sentencias_volcado.py` | correo del último cruzado | muerto (F-059) | `test_f059_r1_r4_el_parte_y_el_ultimo` |
| F02 | `infrastructure/persistencia/sentencias_volcado.py` | sin motivo | muerto (F-059) | `test_f059_r4_un_rechazo_con_su_codigo` |
| F03 | `infrastructure/persistencia/sentencias_volcado.py` | parte sin UTC | muerto (F-059) | `test_f059_r1_las_fechas_vuelven_en_utc_y_sin_zona_no_se_adivinan` |
| F03b | `infrastructure/persistencia/sentencias_volcado.py` | hora del último cruzada | muerto (F-059) | `test_f059_r1_solo_el_ultimo_en_duda[enviado]` |
| F11 | `infrastructure/persistencia/sentencias_volcado.py` | ide y cod cruzados | muerto (F-059) | `test_f059_r1_r4_el_parte_y_el_ultimo` |
| F12 | `infrastructure/persistencia/sentencias_volcado.py` | columnas de más ignoradas | muerto (F-059) | `test_f059_r32_una_situacion_con_columnas_de_mas_o_de_menos_no_se_lee[9]` |
| F13 | `infrastructure/persistencia/sentencias_volcado.py` | acción y huella cruzadas | muerto (F-059) | `test_f059_r20_la_fila_bloqueada_con_su_ultima_revision_y_su_volcado` |
| F14 | `infrastructure/persistencia/sentencias_volcado.py` | bloqueada ignora columnas de más | muerto (F-059) | `test_f059_r20_una_fila_bloqueada_con_columnas_de_mas_no_se_lee` |
| F15 | `infrastructure/persistencia/sentencias_volcado.py` | bloqueada sin revision_id | muerto (F-059) | `test_f059_r20_la_fila_bloqueada_con_su_ultima_revision_y_su_volcado` |

**En total, a mano: 61 + 9 + 13 = 83.** Sobre el código final, todos los que cambian el programa mueren con
un test de F-059 y ninguno lo caza solo otra suite. Los siete que sobrevivieron por el camino (V04, V05, F09,
F10, G04 del lote 1; V05d y F09a del lote 2) y G05, que solo cazaba una aserción dentro de un test de F-056, se
resolvieron así: V04 y G05, con un test nuevo de F-059; V05, F09, F10, G04 y F09a, cambiando el código (ese
mutante ya no existe, y los que lo sustituyen mueren: V05a–c, F12, F14); V05d, razonado arriba.

#### Cobertura

`coverage run` con los cinco ficheros del bloque (566 passed): `sentencias_volcado.py` **100 %** (86),
`repositorio_volcado_pg.py` **100 %** (69), `sentencias_revision.py` **100 %** (92), `domain/ports/volcado.py`
**100 %** (17), `domain/models/volcado.py` **100 %** (284), `situacion_volcado.py` **100 %** (47);
`repositorio_revision_pg.py` 77 % y `fabrica.py` 93 %, pero **todas las líneas de F-059 cubiertas**: lo que falta
es `registrar_lote`/`_registrar_lote` (F-060) y `construir_bandeja`/`construir_equivalencias`/`construir_revision`,
que este subconjunto no recorre. La `PUERTA COBERTURA` de `init.sh` la dará T23.

### Verificación final del bloque

Desde el scratchpad, sobre `55f27f5`: las verificaciones de T4–T7 juntas (`test_f059_repositorio_volcado.py`, `test_f059_volcado_dominio.py`, `test_f059_estados.py`, `test_f059_ddl.py`, `test_f056_repositorio_revision.py`, `test_f060_repositorio_lote.py`, `test_f056_alcance_cerrado.py`, `test_f060_alcance_cerrado.py`): **624 passed, 73 skipped in 29.66s**. **La suite entera del servicio** (`pytest <repo>/services/postventa-api/tests <repo>/services/postventa-api/tests_bbdd -q`): **8597 passed, 233 skipped in 730.60s**, sin un rojo.

`ruff check` (desde la raíz) sobre `infrastructure/persistencia/`, `domain/` y los tests de F-059 y los ajenos
tocados: sin avisos en lo mío; los `I001` que quedan son de ficheros que no he tocado (`test_f036_*`) o
anteriores a la rama (`test_f005_ddl_idempotente_texto.py`, `test_f028_ddl_historico.py`, ya en `13f9f51`).

Barrido de datos sensibles sobre `13f9f51..HEAD` (GUID, correos, IPv4, `password|secret|token|…`): ningún GUID; correos, solo `persona.volcado@ejemplo.invalid` y `otra.persona@ejemplo.invalid`; ninguna IP; las seis «password» son la contraseña inventada de los tests de la fábrica (`contrasena-inventada`, como en F-056). Obras `9901` y `9904`, proveedor `EJ07`, textos «Ejemplo», códigos `RS26.10/000n` inventados.

## Evidencias del Bloque 2

| Evidencia | Valor |
|---|---|
| RED (T4) | 171 failed, 328 passed (traza arriba) + los 12 del grupo A, rojos por el `16_` |
| Verificación de T5 | 323 passed, 95 skipped in 58.85s |
| Verificación de T6 | 520 passed, 73 skipped in 21.91s (624 passed tras T9) |
| T7 | 46 tests recogidos; ejecutados por el humano en T8 |
| Suite entera del servicio | **8597 passed, 233 skipped in 730.60s** (`tests` y `tests_bbdd`, sobre `55f27f5`; los de base se saltan sin DSN). Tras T6: 8592 passed, 129 skipped in 1285.55s (solo `tests`) |
| Cobertura de lo nuevo | 100 % de `sentencias_volcado.py`, `repositorio_volcado_pg.py`, `sentencias_revision.py`, `domain/ports/volcado.py` y `domain/models/volcado.py`; todas las líneas de F-059 de `repositorio_revision_pg.py` y `fabrica.py` |
| Mutación (herramienta) | **26 generados, 26 muertos, 0 supervivientes, 0 timeouts**, 4484.1 s, 8 workers |
| Reverificación contra F-059 solos | 26/26 |
| Mutación a mano | 83 (61 + 9 + 13); supervivientes abiertos: **0** (V05d no cambia el programa, razonado) |
| Tests ajenos tocados | Solo los del grupo A de §21.3 (con B-2) y `test_f056_repositorio_revision.py` (grupo C), tabla de T4 |

## Commits del Bloque 2

| Tarea | Commit |
|---|---|
| (bloqueo B-1/B-2) | `2203879` |
| T4 | `f50281b` |
| T5 | `54c3278` |
| T6 | `cf3b7a2` |
| T7 | `9b4c8d5` |
| T8 | MANUAL (humano), pendiente |
| T9 | `64b25b8`, `42be797`, `55f27f5` y el de este informe con `progress/mutacion_F-059_bloque2.md` |

**Parado aquí: review del Bloque 2.** Lo que el reviewer debería mirar primero: la decisión 1 de T6 (`aprobadas`
deja fuera solo la `volcada`, no filtra con `es_candidata`, para no relajar
`test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa`), la 2 (dónde va R2 dentro de
`_registrar`), V05d, y que `init.sh` no se ha lanzado por la regla del `.env`.


## Bloque 3 · El adaptador de `sigrid-api` y las fábricas · T10–T12 · 2026-10-16

Encargo del líder tras el APPROVED del Bloque 2 (`8e668b2`): T10, T11 y T12, y parar. Releídas las
observaciones de la review del Bloque 2: O-B2-1 ya está en la spec (`f7bcf9b`); **O-B2-2** (`guardar_ensayo` no
debe recibir un `sin_respuesta`: la aplicación lo convierte antes en `EnsayoSinRespuesta`) y **O-B1-1** (R7
recalculado sobre el parte que se manda en el volcado) son del Bloque 4 y quedan pendientes para él. **V05d**, el
mutante equivalente del Bloque 2, lo aceptó el humano por escrito el 2026-10-16: anotado como cerrado arriba
(`5c0a6d2`).

**Hash anterior a T10 (base de T12): `5c0a6d2`.** Todo desde `<scratchpad>/f059` (sin `.env`), con rutas
absolutas; la mutación, con `--raiz <repo>` desde el mismo directorio. `bash harness/init.sh`, por la misma regla
del `.env` que en el Bloque 2, no se ha lanzado: queda para T23. **Ningún test llama a la red ni a `sigrid-api`**:
el adaptador se prueba con `ClienteFalso` (`tests/utiles_sigrid.py`), la guarda `sin_red` de `conftest.py`
sigue puesta, las fábricas no reciben cliente y ningún test llama a `ensayar` ni a `volcar` sobre lo que
construyen salvo para ver que se niega **antes** de componer nada. Ningún `commit: true` sale de este puesto.

### T10 · Fase RED (`9bdc35c`)

**Tests nuevos:**

- `tests/test_f059_adaptador_volcado.py` (con `ClienteFalso`): la ruta exacta y la de lectura (R36); el cuerpo
  tal cual, a la ruta, con la clave en `x-functions-key` y **nunca** en la URL; la raíz con barra final; **R16**:
  `volcar` con `escritura_habilitada=False` → `VolcadoDeshabilitado` **sin** `post`, y antes de mirar el cuerpo;
  **D-4**: sin la ventana sí se ensaya; **R6**: `volcar` solo con `commit` igual al booleano `True` (ni `False`,
  ni nulo, ni `"true"`, ni `1`, ni sin la clave) y `ensayar` solo con `False`, sin `post` en otro caso; **R21,
  R31**: **un** `post` ante un tiempo agotado de lectura o de conexión, un corte o un error de protocolo
  (`sin_respuesta`, y la segunda respuesta preparada queda sin consumir), y tampoco se reintenta un 5xx, 408 ni
  429; **las tres familias**: 200 y 201 → `ok` con los datos **sin interpretar**; 400 → `lote_400` con
  `details.codigo` y **nada más** (ocho códigos, de lote y uno que no lo es); un 400 sin código de texto (no JSON,
  lista, sin `details`, `details` no objeto, sin código, código numérico o nulo) → `lote_400` sin código; otro
  código → `sin_respuesta`; un 200 que no es un objeto JSON → `sin_respuesta`; **R8**: `existe_usuario` por
  `sql/read` (cuerpo exacto con `SQL_USUARIO`, el login como parámetro y `MAX_FILAS_LECTURA`), verdadero solo con
  exactamente uno, los reintentos de lectura ante 503, 429 o un corte, agotados → `EnsayoSinRespuesta` sin el
  login, un definitivo sin reintentar, una lectura sin forma o truncada no decide; **R31, R34**: el log de cada
  llamada lleva obra, modo, `commit`, partes, familia, segundos y media, y **nada** del cuerpo, la respuesta, la
  URL, la clave o el login (con un 400 lleno de ruido inventado: un nombre y un DNI ficticios); el entorno `test`,
  `local` u otro → no se construye (`VolcadoDeshabilitado` con el entorno), y en `dev` y `pro` sí; la propiedad
  `escritura_habilitada`; y el puerto y `RespuestaDeLote` (las tres familias, lo que lleva cada una, inmutable).
- `tests/test_f059_fabrica.py`: los dos ajustes (por defecto, ventana cerrada y `N` = 5; por su alias; un `N` que
  no es un entero **no** impide cargar los ajustes y no se cambia en silencio por el defecto); el **orden de las
  puertas** de §8.3 (el entorno el primero en las dos, con la configuración completa y con todo mal; la ventana
  del volcador la segunda, también con `false`, `0` o sin la variable, y antes que la configuración; la
  configuración, que nombra **todas** las que faltan y ningún valor, con una en blanco como ausente, antes que
  `N`; y `N` 0, 51, `cinco`, `5.5`, vacío, `-3`, `1e1` o `true` → `ConfiguracionDeVolcadoInvalida`, que nombra la
  variable y no el valor; 1, 5 y 50 sí construyen); **D-4**: el ensayador se construye con la ventana abierta o
  cerrada y **no** puede volcar; el volcador sí; las fábricas pasan la configuración, `SIGRID_TIMEOUT_S` (R31) y
  los reintentos, y no construyen el cliente; lo que construyen cumple el puerto; **R37**: el volcado no mira
  `CIERRE_HABILITADO`, la ventana del volcado no abre el cierre ni el gráfico y la del cierre no abre el volcado;
  las fábricas nuevas se **añaden** sin quitar ninguna; **§8.4**: `VerificadorDeLoginPort` solo pide
  `existe_usuario`, lo cumplen el adaptador del cierre y el del volcado, y `resolver_login_de_sigrid` lo pide en
  `erp` con la misma firma; y los dos nombres en `.env.example` y `local.settings.json.example`, con la ventana
  cerrada.

**El esqueleto neutro**: `infrastructure/sigrid/volcado.py` con la clase, el constructor que no comprueba nada y
deja `escritura_habilitada` en falso, los tres métodos con `raise NotImplementedError("F-059 T11")` y las dos
rutas vacías; en `domain/ports/volcado.py`, `FamiliaDeRespuesta`, una `RespuestaDeLote` sin invariantes ni
`frozen` y el `VolcadoSigridPort` (declaraciones); y `VerificadorDeLoginPort` en
`domain/ports/usuarios_sigrid.py`. Ni las fábricas, ni los ajustes, ni la anotación de F-009, ni los ejemplos de
entorno.

Comando (desde `<scratchpad>/f059`, `R` = `<repo>/services/postventa-api`):

```
COLUMNS=400 $R/.venv/Scripts/python.exe -m pytest $R/tests/test_f059_adaptador_volcado.py $R/tests/test_f059_fabrica.py \
  -q -p no:cacheprovider --tb=no -rf
```

Resultado: **157 failed, 7 passed**. Por tipo: 79 `NotImplementedError` (el esqueleto), 65 `AttributeError` (las
fábricas y los dos ajustes, que no existen), 8 `DID NOT RAISE` (el entorno que no muerde y las invariantes de
`RespuestaDeLote`), 5 `AssertionError` (la ruta vacía, `escritura_habilitada`, la anotación de F-009 y los dos
ejemplos de entorno). **Los 7 que pasan** no dependen de lo que falta: el adaptador cumple el puerto y se
construye en `dev` y `pro` (el esqueleto lo permite), `construir_erp` y `construir_graficos` siguen cerrados sin
`CIERRE_HABILITADO` (caracterizan lo que F-059 **no** cambia, R37), y las dos declaraciones de
`VerificadorDeLoginPort`. En la primera pasada había 7 `TypeError` más, de un ayudante mío (`_completos` pasaba
`ENTORNO` dos veces): corregido el ayudante, no el código; y el test de «`N` que no es un entero no impide cargar
los ajustes» pasaba en vacío (el campo no existía y `extra="ignore"` lo tragaba), así que gana la aserción de que
el valor no se cambia en silencio por el defecto, y desde entonces falla en la RED. La traza de abajo es la
definitiva.

Traza real, completa (solo se ha recortado el prefijo de la ruta hasta `services\`; ningún GUID):

```
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r36_la_ruta_es_la_de_partes_reclamacion - AssertionError: assert '' == '/api/sigrid/...s-reclamacion'
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_t11_las_tres_familias_y_lo_que_lleva_cada_una - Failed: DID NOT RAISE ValueError
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_t11_la_respuesta_es_inmutable - Failed: DID NOT RAISE FrozenInstanceError
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r36_la_raiz_con_barra_final_no_duplica_la_barra - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r16_sin_la_ventana_no_se_vuelca_y_no_se_llama - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r16_sin_la_ventana_se_niega_antes_de_mirar_el_cuerpo - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_d4_sin_la_ventana_si_se_ensaya - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_r16_volcar_exige_commit_true_de_verdad[false] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_r16_volcar_exige_commit_true_de_verdad[nulo] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_r16_volcar_exige_commit_true_de_verdad[texto] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_r16_volcar_exige_commit_true_de_verdad[uno] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_r16_volcar_exige_commit_true_de_verdad[sin-clave] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_ensayar_exige_commit_false_de_verdad[true] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_ensayar_exige_commit_false_de_verdad[nulo] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_ensayar_exige_commit_false_de_verdad[texto] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_ensayar_exige_commit_false_de_verdad[cero] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r6_ensayar_exige_commit_false_de_verdad[sin-clave] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[lectura-agotada-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[lectura-agotada-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-agotada-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-agotada-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[protocolo-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[protocolo-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[500-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[500-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[502-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[502-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[503-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[503-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[504-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[504-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[408-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[408-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[429-volcar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r21_r23_un_5xx_tampoco_se_reintenta[429-ensayar] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r22_un_200_devuelve_los_datos_sin_interpretar[200] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r22_un_200_devuelve_los_datos_sin_interpretar[201] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[obra_no_encontrada] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[usuario_no_valido] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[serie_no_encontrada] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[estado_inicial_no_encontrado] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[lote_demasiado_grande] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[base_de_datos_no_permitida] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[escritura_reclamaciones_deshabilitada] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r24_r35_de_un_400_solo_details_codigo[un_codigo_que_no_es_de_lote] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[no-json] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[lista] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[sin-details] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[details-texto] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[sin-codigo] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[codigo-numero] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[codigo-nulo] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[401] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[403] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[404] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[409] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[422] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta[no-json] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta[lista] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta[texto] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta[numero] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_existe_usuario_solo_con_exactamente_uno[ninguno] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_existe_usuario_solo_con_exactamente_uno[dos] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_existe_usuario_solo_con_exactamente_uno[sin-filas] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_la_lectura_del_login_se_reintenta[503] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_la_lectura_del_login_se_reintenta[429] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_la_lectura_del_login_se_reintenta[corte] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_agotados_los_reintentos_es_sin_respuesta_y_no_dice_el_login - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_un_definitivo_no_se_reintenta[400] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_un_definitivo_no_se_reintenta[401] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_un_definitivo_no_se_reintenta[403] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_un_definitivo_no_se_reintenta[404] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[no-json] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[lista] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[truncada] - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r34_el_login_no_va_al_log - NotImplementedError: F-059 T11
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-test] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-local] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-otro] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[False-test] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[False-local] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[False-otro] - Failed: DID NOT RAISE VolcadoDeshabilitado
FAILED services\postventa-api\tests\test_f059_adaptador_volcado.py::test_f059_r16_el_adaptador_dice_si_puede_escribir - assert False is True
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_la_ventana_viene_cerrada_por_defecto_y_n_es_cinco - AttributeError: 'Ajustes' object has no attribute 'volcado_habilitado'. Did you mean: 'archivo_habilitado'?
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_r30_las_dos_variables_llegan_por_su_alias - AttributeError: 'Ajustes' object has no attribute 'volcado_habilitado'. Did you mean: 'archivo_habilitado'?
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[cinco] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[5.5] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[  ] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[1e1] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[-3] - AttributeError: 'Ajustes' object has no attribute 'volcado_partes_por_llamada'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[local-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[local-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[test-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[test-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[otro-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_primera_puerta_es_el_entorno[otro-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion[construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion[construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_d3_la_segunda_puerta_del_volcador_es_la_ventana[false] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_d3_la_segunda_puerta_del_volcador_es_la_ventana[cero] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_d3_la_segunda_puerta_del_volcador_es_la_ventana[sin-variable] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_la_ventana_va_antes_que_la_configuracion - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_configuracion_nombra_todas_las_que_faltan_y_ningun_valor[construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_r16_la_configuracion_nombra_todas_las_que_faltan_y_ningun_valor[construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_API_BASE_URL-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_API_BASE_URL-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_API_KEY-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_API_KEY-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_BASE_DATOS-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r10_una_variable_en_blanco_cuenta_como_ausente[SIGRID_BASE_DATOS-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_configuracion_va_antes_que_n[construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_configuracion_va_antes_que_n[construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[0-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[0-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[51-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[51-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[cinco-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[cinco-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[5.5-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[5.5-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[-3-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[-3-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[1e1-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[1e1-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[true-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[true-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[1-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[1-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[5-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[5-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[50-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r30_n_de_1_a_50_si_se_construye[50-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar[true] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar[false] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r16_el_volcador_si_puede_volcar - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r31_las_fabricas_pasan_la_configuracion_y_el_tiempo_de_sigrid[construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r31_las_fabricas_pasan_la_configuracion_y_el_tiempo_de_sigrid[construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_lo_que_construyen_cumple_el_puerto[construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_lo_que_construyen_cumple_el_puerto[construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_el_volcado_no_mira_cierre_habilitado[true-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_el_volcado_no_mira_cierre_habilitado[true-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_el_volcado_no_mira_cierre_habilitado[false-construir_ensayador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_el_volcado_no_mira_cierre_habilitado[false-construir_volcador] - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_r37_ni_la_ventana_del_cierre_abre_el_volcado - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_volcador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_las_fabricas_nuevas_se_anaden_sin_quitar_ninguna - AttributeError: module 'infrastructure.sigrid.fabrica' has no attribute 'construir_ensayador'
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_resolver_login_pide_un_verificador_de_login - assert 'ErpPort' in ('VerificadorDeLoginPort', <class 'domain.ports.usuarios_sigrid.VerificadorDeLoginPort'>)
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_los_ejemplos_declaran_las_dos_variables_con_la_ventana_cerrada[.env.example] - AssertionError: assert 'VOLCADO_HABILITADO' in '# services/postventa-api/.env.example\n# Copia este fichero a .env y rellena los valores. El .env NUNCA se versiona.\...S, 10\n# MB): su...
FAILED services\postventa-api\tests\test_f059_fabrica.py::test_f059_t11_los_ejemplos_declaran_las_dos_variables_con_la_ventana_cerrada[local.settings.json.example] - assert 'VOLCADO_HABILITADO' in '{\n  "IsEncrypted": false,\n  "Values": {\n    "AzureWebJobsStorage": "",\n    "FUNCTIONS_WORKER_RUNTIME": "python",\...ID_ZONA_HORARIA":...
157 failed, 7 passed in 1.90s
```

### T11 · GREEN (`7705354`)

| Fichero | Qué |
|---|---|
| `infrastructure/sigrid/volcado.py` | `AdaptadorVolcadoSigridApi` y `exigir_entorno_con_volcado`; `RUTA_PARTES_RECLAMACION` (vive **solo** aquí, R36) y `RUTA_LECTURA`. **Importa** de `cliente.py` (`CORRECTOS`, `ENTORNOS_CON_CIERRE`, `MAX_FILAS_LECTURA`, `ErrorDeSigrid`, `construir_cliente_http`, `es_transitorio`, `exigir_entorno_con_cierre`) y de `consultas.py` (`select_usuario`); no copia nada |
| `domain/ports/volcado.py` | `FamiliaDeRespuesta`, `RespuestaDeLote` (inmutable, con sus invariantes) y `VolcadoSigridPort` (§8.1) |
| `infrastructure/sigrid/fabrica.py` | `construir_ensayador` y `construir_volcador` **añadidas** (y en `__all__`), con `_adaptador_de_volcado`; enmienda fechada en la cabecera. Nada de las otras cinco cambia |
| `config/settings.py` | `volcado_habilitado` (`VOLCADO_HABILITADO`, falso) y `volcado_partes_por_llamada` (`VOLCADO_PARTES_POR_LLAMADA`, 5) |
| `domain/ports/usuarios_sigrid.py` | `VerificadorDeLoginPort` (solo `existe_usuario`) |
| `application/pipelines/paso_cierre.py` | **Solo** la anotación de `erp` en `resolver_login_de_sigrid` (`ErpPort` → `VerificadorDeLoginPort`) y su importación, que `ruff` parte en tres líneas. Ni una línea de lógica |
| `.env.example`, `local.settings.json.example` | `VOLCADO_HABILITADO=false` y `VOLCADO_PARTES_POR_LLAMADA=5`, con su comentario; el `.env.example` sigue en CRLF |

**Decisiones de diseño (para la review del Bloque 3):**

1. **El error del entorno es `VolcadoDeshabilitado`, no `CierreDeshabilitado`.** §8.2 dice
   «`exigir_entorno_con_cierre(entorno)` (la misma lista `dev`, `pro`)», y R16 que si falla una de las puertas,
   «503 `volcado_deshabilitado` o el de configuración incompleta». Las dos letras se cumplen:
   `exigir_entorno_con_volcado` **llama** a `exigir_entorno_con_cierre` (una sola lista, una sola comprobación) y
   traduce su `CierreDeshabilitado` en `VolcadoDeshabilitado` con un mensaje del volcado. Lo usan el constructor
   del adaptador y las dos fábricas. Para el ensayo (R10, «503» sin código), el mismo error: desde un puesto de
   trabajo no se ensaya ni se vuelca.
2. **`existe_usuario` sin respuesta utilizable → `EnsayoSinRespuesta` (502).** La spec no dice qué error levanta
   la lectura del login cuando la pasarela no responde (§8.2 solo da «con los reintentos de lectura de
   siempre»). De los ocho errores de §7, es el que dice «502 sin guardar nada: es una lectura y repetirla es
   inocuo», que es exactamente lo que pasa —tanto en el ensayo como en el volcado, el login se lee **antes** de
   escribir nada (R19)—. El nombre encaja peor en el volcado; si la review o el Bloque 4 prefieren otro, el
   cambio es una línea (`_sin_respuesta`). **Lo dejo señalado para el Bloque 4**, que es quien lo traduce a HTTP.
3. **`VOLCADO_PARTES_POR_LLAMADA` es `int | str` (`union_mode="left_to_right"`), no `int`.** §13 dice «`int`» y,
   a la vez, que el rango se valida en la fábrica (503) «y no al cargar los ajustes: `/health` tiene que arrancar
   igual»; T10 pide «no entero → 503». Con `int`, un `cinco` en la App Setting tumbaría la carga de los ajustes
   (y `/health`) en vez de dar el 503. Así, lo que es un entero llega como entero (`"12"` → 12, `" 7 "` → 7) y lo
   demás se queda como texto, que `validar_partes_por_llamada` (Bloque 1) rechaza. Sin la unión de izquierda a
   derecha, `"5"` llegaría como texto y ni el valor por defecto en Azure valdría (mutante C01, muerto).
4. **`RespuestaDeLote`**: los datos, obligatorios en `ok` y solo en él; el código, solo en `lote_400` (y
   opcional: un 400 «Solicitud invalida.» no lo trae); un `tipo` que no es `FamiliaDeRespuesta` →
   `TypeError` (lo pidió `ruff`, TRY004; el test se separó en ese mismo commit). La presencia se decide con
   `is not None`, y dos tests nuevos de T12 lo fijan (un `{}` es datos; un `""` es código).
5. **Lo que es `ok`**: `CORRECTOS` de `cliente.py` (200 y 201, importado como dice §1) con un **objeto** JSON. Un
   200 con una lista o con algo que no es JSON es `sin_respuesta`: no es la forma de §8.9, y así el dominio solo
   ve objetos. Un 400 sin código de texto es `lote_400` sin código: el dominio no lo clasifica
   (`clasificar_codigo_de_lote(None)`), y la aplicación lo tratará como respuesta que no se entiende.
6. **El adaptador manda `dict(cuerpo)`**, una copia, tal cual: no compone ni toca nada.
7. **El log de cada llamada (R31, R34)**: `obra`, `modo`, `commit`, `partes`, `familia`, `segundos` y
   `media_por_parte`; los cortes y los códigos inesperados, en un `warning` con el tipo del corte o el código. La
   referencia y el `sigrid_cod` de cada parte los registrará la aplicación (R34, Bloque 4), que es quien los
   interpreta.
8. **Las fábricas no devuelven `N`**: lo validan (503) y nada más. La aplicación del Bloque 4 lo leerá de los
   ajustes ya validados para el panel y para el tope de las peticiones (R9, R15, R28).
9. **`_HTTP_DEL_LOTE`, no `_ESTADO_DE_LOTE`**: la guardia de F-009 (`test_f009_r3_ninguna_constante_de_estado_de_produccion_es_un_numero`)
   prohíbe constantes con «ESTADO» en el nombre y un número de valor (es un código HTTP, no un estado de
   Sigrid). Renombrada en vez de tocar la guardia.

Verificación de `tasks.md` T11 (`test_f059_adaptador_volcado.py`, `test_f059_fabrica.py`, `test_f009_*.py`,
`test_f012_*.py`): **994 passed in 17.68s**. Además, F-005, F-006, F-013, F-036, F-056, F-060 y F-059 enteros
(las guardias de arquitectura, de ejemplos de entorno, de importación diferida y de alcance): **6661 passed, 104
skipped in 549.86s**. **Tests ajenos tocados: ninguno** (`git diff 5c0a6d2..HEAD -- services/postventa-api/tests`
solo enseña los dos de F-059).

### T12 · Mutación del bloque (`eb8d03b`, `93a3984` y el de este informe)

Base **`5c0a6d2`**. Antes de la campaña, la reverificación pura y los mutantes a mano (abajo) pidieron cuatro
tests más, todos de F-059 y sin tocar el código (`eb8d03b`): la duración y la media **medidas** con un reloj
controlado (el mutante `time.monotonic() + arranque` sobrevivía a un log que solo miraba que hubiera
«segundos=»), un lote sin partes que no divide entre cero, que con un cliente dado se use ese aunque se evalúe
como falso (y que sin cliente se fabrique uno con `SIGRID_TIMEOUT_S`, una vez), y que la presencia de datos y de
código se decide con `is not None`. La cobertura dejó una línea sin recorrer (el corte de red persistente en la
lectura del login) y gana su test (`93a3984`).

#### La campaña de la herramienta

```
cd <scratchpad>/f059
PYTHONPATH=<repo> python -m harness.mutacion --feature F-059 --base 5c0a6d2 --timeout 1800 --workers 8 \
  --raiz <repo> --salida <repo>/progress/mutacion_F-059_bloque3.md
25 mutantes evaluados, 25 muertos, 0 supervivientes, 0 timeouts en 3012.2 s
```

Sobre `HEAD` `eb8d03b`; alcance: **509** líneas de producción en seis ficheros (`paso_cierre.py` 5, `settings.py`
32, `usuarios_sigrid.py` 16, `domain/ports/volcado.py` 69, `infrastructure/sigrid/fabrica.py` 78,
`infrastructure/sigrid/volcado.py` 309); **8 workers**; ningún timeout. Informe: `progress/mutacion_F-059_bloque3.md`
(su primera línea, otra vez con la ruta absoluta del equipo, la he dejado relativa). Una sola campaña, sin
paradas. El test de `93a3984` llegó después de lanzarla: no toca código de producción, y sus dos mutantes (A25,
A26) van a mano.

#### Reverificación de cada mutante de la herramienta contra los tests de F-059 solos

Con `generar_mutantes` y `aplicar_mutante`, el mismo alcance y la misma base, sobre `eb8d03b` en un worktree
desechable (retirado), ejecutando solo `test_f059_adaptador_volcado.py` y `test_f059_fabrica.py` (`-x`):
**25 de 25 muertos por tests de F-059**.

| N.º | Fichero:línea | Operador | Original → mutado | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|---|
| 1 | `settings.py:527` | booleano | default=False, -> default=True, | muerto (F-059) | `test_f059_r37_la_ventana_viene_cerrada_por_defecto_y_n_es_cinco` |
| 2 | `settings.py:538` | entero | default=5, -> default=6, | muerto (F-059) | `test_f059_r37_la_ventana_viene_cerrada_por_defecto_y_n_es_cinco` |
| 3 | `volcado.py:79` | booleano | @dataclass(frozen=True) -> @dataclass(frozen=False) | muerto (F-059) | `test_f059_t11_la_respuesta_es_inmutable` |
| 4 | `volcado.py:93` | not | if not isinstance(self.tipo, FamiliaDeRespuesta): -> if isinstance(self.tipo, FamiliaDeRespuesta): | muerto (F-059) | `test_f059_t11_las_tres_familias_y_lo_que_lleva_cada_una` |
| 5 | `volcado.py:95` | comparacion | if (self.datos is not None) != (self.tipo is FamiliaDeRespuesta.OK): -> if (self.datos is not None) == (self.tipo is FamiliaDeRespuesta.OK): | muerto (F-059) | `test_f059_t11_las_tres_familias_y_lo_que_lleva_cada_una` |
| 6 | `volcado.py:97` | logico | if self.codigo is not None and self.tipo is not FamiliaDeRespuesta.LOTE_400: -> if self.codigo is not None or self.tipo is not FamiliaDeRespuesta.LOTE_400: | muerto (F-059) | `test_f059_t11_las_tres_familias_y_lo_que_lleva_cada_una` |
| 7 | `fabrica.py:310` | booleano | return _adaptador_de_volcado(ajustes, escritura_habilitada=False) -> return _adaptador_de_volcado(ajustes, escritura_habilitada=True) | muerto (F-059) | `test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar[true]` |
| 8 | `fabrica.py:323` | not | if not ajustes.volcado_habilitado: -> if ajustes.volcado_habilitado: | muerto (F-059) | `test_f059_r16_d3_la_segunda_puerta_del_volcador_es_la_ventana[false]` |
| 9 | `fabrica.py:333` | booleano | return _adaptador_de_volcado(ajustes, escritura_habilitada=True) -> return _adaptador_de_volcado(ajustes, escritura_habilitada=False) | muerto (F-059) | `test_f059_r16_el_volcador_si_puede_volcar` |
| 10 | `volcado.py:96` | entero | _HTTP_DEL_LOTE = 400 -> _HTTP_DEL_LOTE = 401 | muerto (F-059) | `test_f059_r14_r24_r35_de_un_400_solo_details_codigo[obra_no_encontrada]` |
| 11 | `volcado.py:173` | booleano | reraise=True, -> reraise=False, | muerto (F-059) | `test_f059_r8_agotados_los_reintentos_es_sin_respuesta_y_no_dice_el_login` |
| 12 | `volcado.py:184` | not | if not filas: -> if filas: | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| 13 | `volcado.py:185` | booleano | return False -> return True | muerto (F-059) | `test_f059_r8_existe_usuario_solo_con_exactamente_uno[sin-filas]` |
| 14 | `volcado.py:186` | entero | return int(filas[0][0]) == 1 -> return int(filas[1][0]) == 1 | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| 15 | `volcado.py:186` | entero | return int(filas[0][0]) == 1 -> return int(filas[0][1]) == 1 | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| 16 | `volcado.py:186` | comparacion | return int(filas[0][0]) == 1 -> return int(filas[0][0]) != 1 | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| 17 | `volcado.py:186` | entero | return int(filas[0][0]) == 1 -> return int(filas[0][0]) == 2 | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| 18 | `volcado.py:190` | booleano | if cuerpo.get("commit") is not False: -> if cuerpo.get("commit") is not True: | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[ensayar]` |
| 19 | `volcado.py:196` | not | if not self._escritura_habilitada: -> if self._escritura_habilitada: | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar]` |
| 20 | `volcado.py:201` | booleano | if cuerpo.get("commit") is not True: -> if cuerpo.get("commit") is not False: | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar]` |
| 21 | `volcado.py:213` | aritmetico | segundos = time.monotonic() - arranque -> segundos = time.monotonic() + arranque | muerto (F-059) | `test_f059_r31_la_duracion_y_la_media_son_las_medidas` |
| 22 | `volcado.py:214` | logico | partes = len(cuerpo.get("partes") or ()) -> partes = len(cuerpo.get("partes") and ()) | muerto (F-059) | `test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas` |
| 23 | `volcado.py:244` | comparacion | if respuesta.status_code == _HTTP_DEL_LOTE: -> if respuesta.status_code != _HTTP_DEL_LOTE: | muerto (F-059) | `test_f059_d4_sin_la_ventana_si_se_ensaya` |
| 24 | `volcado.py:254` | not | if not isinstance(datos, dict): -> if isinstance(datos, dict): | muerto (F-059) | `test_f059_d4_sin_la_ventana_si_se_ensaya` |
| 25 | `volcado.py:268` | not | if not isinstance(datos, dict): -> if isinstance(datos, dict): | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |

#### Mutantes a mano (lo que la herramienta no muta)

En worktrees desechables (retirados; el árbol de trabajo no se ha mutado), con los dos ficheros de F-059 del
bloque. Incluye los de veracidad frente a `is (not) None` y a `is True`/`is False` (V01–V06).

**Lote principal** (sobre `eb8d03b`, 45):

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| V01 | `domain/ports/volcado.py` | datos por veracidad | muerto (F-059) | `test_f059_t11_lo_que_decide_es_que_haya_datos_o_codigo_y_no_su_veracidad` |
| V02 | `domain/ports/volcado.py` | código por veracidad | muerto (F-059) | `test_f059_t11_lo_que_decide_es_que_haya_datos_o_codigo_y_no_su_veracidad` |
| V03 | `infrastructure/sigrid/volcado.py` | cliente por veracidad | muerto (F-059) | `test_f059_t11_lo_que_decide_es_que_haya_cliente_y_no_su_veracidad` |
| V04 | `infrastructure/sigrid/volcado.py` | ensayo: commit por veracidad | muerto (F-059) | `test_f059_r6_ensayar_exige_commit_false_de_verdad[nulo]` |
| V05 | `infrastructure/sigrid/volcado.py` | volcado: commit por veracidad | muerto (F-059) | `test_f059_r6_r16_volcar_exige_commit_true_de_verdad[texto]` |
| V06 | `infrastructure/sigrid/volcado.py` | código de lote por veracidad | muerto (F-059) | `test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[codigo-numero]` |
| A01 | `infrastructure/sigrid/volcado.py` | volcar sin la ventana | muerto (F-059) | `test_f059_r16_sin_la_ventana_no_se_vuelca_y_no_se_llama` |
| A02 | `infrastructure/sigrid/volcado.py` | el cuerpo antes que la ventana | muerto (F-059) | `test_f059_r16_sin_la_ventana_se_niega_antes_de_mirar_el_cuerpo` |
| A03 | `infrastructure/sigrid/volcado.py` | constructor sin el entorno | muerto (F-059) | `test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-test]` |
| A04 | `infrastructure/sigrid/volcado.py` | entorno que no muerde | muerto (F-059) | `test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-test]` |
| A05 | `infrastructure/sigrid/volcado.py` | el lote por sql/read | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar]` |
| A06 | `infrastructure/sigrid/volcado.py` | la ruta de escritura genérica | muerto (F-059) | `test_f059_r36_la_ruta_es_la_de_partes_reclamacion` |
| A07 | `infrastructure/sigrid/volcado.py` | otra cabecera | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar]` |
| A08 | `infrastructure/sigrid/volcado.py` | sin quitar la barra | muerto (F-059) | `test_f059_r36_la_raiz_con_barra_final_no_duplica_la_barra` |
| A09 | `infrastructure/sigrid/volcado.py` | el cuerpo retocado | **sobrevive** | `` |
| A10 | `infrastructure/sigrid/volcado.py` | solo los tiempos agotados son sin_respuesta | muerto (F-059) | `test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-volcar]` |
| A11 | `infrastructure/sigrid/volcado.py` | solo 200 es correcto | muerto (F-059) | `test_f059_r22_un_200_devuelve_los_datos_sin_interpretar[201]` |
| A12 | `infrastructure/sigrid/volcado.py` | un 200 que no es objeto, ok | muerto (F-059) | `test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta[lista]` |
| A13 | `infrastructure/sigrid/volcado.py` | el código fuera de details | muerto (F-059) | `test_f059_r14_r24_r35_de_un_400_solo_details_codigo[obra_no_encontrada]` |
| A14 | `infrastructure/sigrid/volcado.py` | otro campo de details | muerto (F-059) | `test_f059_r14_r24_r35_de_un_400_solo_details_codigo[obra_no_encontrada]` |
| A15 | `infrastructure/sigrid/volcado.py` | el login sin reintentos | muerto (F-059) | `test_f059_r8_la_lectura_del_login_se_reintenta[503]` |
| A16 | `infrastructure/sigrid/volcado.py` | el login reintenta todo | muerto (F-059) | `test_f059_r8_un_definitivo_no_se_reintenta[400]` |
| A17 | `infrastructure/sigrid/volcado.py` | otro techo de filas | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| A18 | `infrastructure/sigrid/volcado.py` | truncada vale | muerto (F-059) | `test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[truncada]` |
| A19 | `infrastructure/sigrid/volcado.py` | el login por la ruta del lote | muerto (F-059) | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| A20 | `infrastructure/sigrid/volcado.py` | log sin la obra | muerto (F-059) | `test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas` |
| A21 | `infrastructure/sigrid/volcado.py` | log con otra familia | muerto (F-059) | `test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas` |
| A22 | `infrastructure/sigrid/volcado.py` | el ensayo sin registrar | muerto (F-059) | `test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas` |
| A23 | `infrastructure/sigrid/volcado.py` | el login: otro error | muerto (F-059) | `test_f059_r8_agotados_los_reintentos_es_sin_respuesta_y_no_dice_el_login` |
| A24 | `infrastructure/sigrid/volcado.py` | el login: uno o más | muerto (F-059) | `test_f059_r8_existe_usuario_solo_con_exactamente_uno[dos]` |
| B01 | `infrastructure/sigrid/fabrica.py` | ensayador sin el entorno | muerto (F-059) | `test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion[construir_ensayador]` |
| B02 | `infrastructure/sigrid/fabrica.py` | volcador sin el entorno en la fábrica | muerto (F-059) | `test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion[construir_volcador]` |
| B03 | `infrastructure/sigrid/fabrica.py` | volcador: configuración antes que la ventana | muerto (F-059) | `test_f059_r16_la_ventana_va_antes_que_la_configuracion` |
| B04 | `infrastructure/sigrid/fabrica.py` | el ensayador mira la ventana | muerto (F-059) | `test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar[false]` |
| B05 | `infrastructure/sigrid/fabrica.py` | ensayador sin N | muerto (F-059) | `test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[0-construir_ensayador]` |
| B06 | `infrastructure/sigrid/fabrica.py` | volcador sin N | muerto (F-059) | `test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50[0-construir_volcador]` |
| B07 | `infrastructure/sigrid/fabrica.py` | volcador: N antes que la configuración | muerto (F-059) | `test_f059_r30_la_configuracion_va_antes_que_n[construir_volcador]` |
| B08 | `infrastructure/sigrid/fabrica.py` | timeout fijo | muerto (F-059) | `test_f059_r31_las_fabricas_pasan_la_configuracion_y_el_tiempo_de_sigrid[construir_ensayador]` |
| B09 | `infrastructure/sigrid/fabrica.py` | reintentos fijos | muerto (F-059) | `test_f059_r31_las_fabricas_pasan_la_configuracion_y_el_tiempo_de_sigrid[construir_ensayador]` |
| B10 | `infrastructure/sigrid/fabrica.py` | el cierre abre el volcado | muerto (F-059) | `test_f059_r37_ni_la_ventana_del_cierre_abre_el_volcado` |
| C01 | `config/settings.py` | N en modo smart | muerto (F-059) | `test_f059_r37_r30_las_dos_variables_llegan_por_su_alias` |
| C02 | `config/settings.py` | N solo entero | muerto (F-059) | `` |
| C03 | `config/settings.py` | la ventana del volcado es la del cierre | muerto (F-059) | `test_f059_r37_la_ventana_del_volcado_no_abre_el_cierre_ni_el_grafico[construir_erp]` |
| C04 | `application/pipelines/paso_cierre.py` | la anotación de antes | muerto (F-059) | `test_f059_t11_resolver_login_pide_un_verificador_de_login` |
| C05 | `domain/ports/usuarios_sigrid.py` | el verificador pide más | muerto (F-059) | `test_f059_t11_el_verificador_de_login_solo_pide_existe_usuario` |

**A09b y A09c** (sobre `eb8d03b`), en lugar de A09:

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| A09b | `infrastructure/sigrid/volcado.py` | el cuerpo siempre con commit true | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[ensayar]` |
| A09c | `infrastructure/sigrid/volcado.py` | el cuerpo sin el usu | muerto (F-059) | `test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera[volcar]` |

**A25 y A26** (sobre `93a3984`), el corte persistente en la lectura del login:

| Id | Fichero | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|---|
| A25 | `infrastructure/sigrid/volcado.py` | el login: solo los tiempos agotados | muerto (F-059) | `test_f059_r8_un_corte_que_no_se_arregla_es_sin_respuesta` |
| A26 | `infrastructure/sigrid/volcado.py` | el login: sin el tipo del corte | muerto (F-059) | `test_f059_r8_un_corte_que_no_se_arregla_es_sin_respuesta` |

**A09 no es un superviviente: no cambia el programa.** Sustituye `json=dict(cuerpo)` por
`json={**cuerpo, "commit": cuerpo.get("commit") is True}`. A esa línea solo se llega desde `ensayar` (con
`commit` **igual a** `False`) o desde `volcar` (con `commit` **igual a** `True`): en los dos casos
`cuerpo.get("commit") is True` es el mismo valor que ya había, así que el cuerpo mandado es idéntico para
cualquier entrada que llegue ahí. Es la categoría de V05d (que el humano aceptó para el Bloque 2) y de A5/A8 de la
re-review del Bloque 1. Lo sustituyen A09b (el cuerpo siempre con `commit: true`) y A09c (sin el `usu`), que sí
cambian el programa y mueren. **Lo dejo para que el humano lo vea**, como V05d.

**En total, a mano: 45 + 2 + 2 = 49** (lote principal, A09b y A09c, A25 y A26); todos los que cambian el programa
mueren con un test de F-059, y ninguno lo caza solo otra suite. A09, razonado arriba.

#### Cobertura

`coverage run` con los dos ficheros del bloque: `infrastructure/sigrid/volcado.py` **100 %** (109; la línea 180,
la única que faltaba en la primera medida, la cubre el test de `93a3984`), `domain/ports/volcado.py` **100 %**
(40), `domain/ports/usuarios_sigrid.py` **100 %** (12) y `config/settings.py` 98 % (lo que falta es
`obtener_ajustes`, que no es de F-059). En `infrastructure/sigrid/fabrica.py` (69 %), **todas las líneas de F-059
cubiertas**: lo que falta son las otras cinco fábricas, que estos dos ficheros no recorren (sus suites son las
de F-009, F-012, F-013, F-036 y F-056).

### Verificación final del bloque

Desde el scratchpad, sobre `93a3984`: los dos ficheros de F-059 del bloque, **170 passed in 1.21s**. **La suite entera del servicio** (`pytest <repo>/services/postventa-api/tests <repo>/services/postventa-api/tests_bbdd -q`): **8768 passed, 233 skipped in 471.95s**, sin un rojo (los de base se saltan sin DSN)

`ruff check` (desde la raíz) sobre los ficheros de producción y los dos tests del bloque: `All checks passed!`
(el `I001` de `catalogo_obra.py` es anterior y no lo toco). Barrido de datos sensibles sobre `5c0a6d2..HEAD`:
ningún GUID, ningún correo, ninguna IP; las URL, `https://pasarela-inventada.invalido` y `https://ejemplo-volcado.invalido`; las «api_key», nombres de parámetro y las claves inventadas de los tests (`clavedefuncioninventadaparaelvolcado`, `clave-de-mentira-para-el-volcado`); en los ejemplos de entorno, solo `false` y `5`. El ruido de los 400 de prueba es inventado (un nombre «Nombre Inventado» y un DNI `00000000T`).

## Evidencias del Bloque 3

| Evidencia | Valor |
|---|---|
| RED (T10) | 157 failed, 7 passed (traza arriba) |
| Verificación de T11 | 994 passed in 17.68s; con las guardias de F-005, F-006, F-013, F-036, F-056 y F-060, 6661 passed, 104 skipped |
| Tests de F-059 del bloque | `test_f059_adaptador_volcado.py` + `test_f059_fabrica.py`: **170 passed in 1.21s** |
| Suite entera del servicio | **8768 passed, 233 skipped in 471.95s**, sin un rojo (los de base se saltan sin DSN) |
| Cobertura de lo nuevo | 100 % de `infrastructure/sigrid/volcado.py`, `domain/ports/volcado.py` y `usuarios_sigrid.py`; todas las líneas de F-059 de `fabrica.py` y `settings.py` |
| Mutación (herramienta) | **25 generados, 25 muertos, 0 supervivientes, 0 timeouts**, 3012.2 s, 8 workers |
| Reverificación contra F-059 solos | 25/25 |
| Mutación a mano | 49; supervivientes abiertos: **0** (A09 no cambia el programa, razonado, para que lo vea el humano) |
| Tests ajenos tocados | **Ninguno** |

## Commits del Bloque 3

| Tarea | Commit |
|---|---|
| (V05d cerrado) | `5c0a6d2` |
| T10 | `9bdc35c` |
| T11 | `7705354` |
| T12 | `eb8d03b`, `93a3984` y el de este informe con `progress/mutacion_F-059_bloque3.md` |

**Parado aquí: review del Bloque 3.** Lo que el reviewer debería mirar primero: la decisión 2 (qué error levanta
la lectura del login sin respuesta: `EnsayoSinRespuesta`, y el Bloque 4 tendrá que traducirlo), la 3 (`N` como
`int | str` frente al `int` de §13), la 1 (`VolcadoDeshabilitado` para el entorno, envolviendo
`exigir_entorno_con_cierre`), A09, y que `init.sh` no se ha lanzado por la regla del `.env`. Para el Bloque 4
siguen abiertas O-B2-2 y O-B1-1.
