# F-072 · Bloque 5 · Plantilla e importación (T15, T16)

Rama `worktree-agent-aad7489c16fc49a1d`, sobre `42c16ae` (integración del Bloque 4).
Commits: T15 `91aba5d` (RED), T16 `3b362f1` (GREEN), más el commit de este informe.
Fuera de alcance por encargo: T17 (campaña de mutación y review) y `bash harness/init.sh`,
que los lanza el líder.

## Hecho

La columna Listado de la plantilla deja de salir del YAML: ofrece los tipos de reclamación
que se leen de Sigrid en cada descarga (R1, R6–R10). La importación lee esos tipos tras el
catálogo y las ubicaciones (R11), guarda el **código** del tipo elegido (R12), lleva la
misma lista al Excel de errores (R13) y en blanco guarda `0002` (R14, R15). Con Sigrid
caída o sin entorno, la plantilla y la importación responden igual que con el catálogo
(409/503, R3/R4).

## Ficheros (todos bajo `services/postventa-api/`)

Producción:
- `config/plantilla_incidencias.yaml`: fuera `listados`; cabecera, instrucción, ejemplo 3
  y `mensajes.Listado` reescritos (R6, R9, R10).
- `infrastructure/documentos/plantilla_yaml.py`: un YAML con `listados` no carga (R9);
  `listados=()`; los ejemplos solo validan Urgencia (R10).
- `domain/models/importacion.py`: `tipo_reclamacion` = código elegido o
  `TIPO_RECLAMACION_POR_DEFECTO`; `listado=None` (R12, R14).
- `application/pipelines/contexto_importacion.py`: campo `tipos`.
- `application/pipelines/paso_importacion.py`: `paso_catalogo(..., tipos)` lee los tipos
  tras las ubicaciones; validación y Excel de errores usan `listas_con_tipos` (R11–R13).
- `application/pipelines/plantilla.py`: `generar_plantilla(..., tipos, ...)` (R1, R6).
- `interface_adapters/api/plantilla.py`, `interface_adapters/api/importar.py`: parámetro
  `tipos` opcional; por defecto `fuente_de_tipos(construir_tipos_reclamacion(ajustes))`,
  construido después de las ubicaciones y, en la importación, solo si no es `ya_importado`.

Sin tocar (R32): `excel_openpyxl.py`, el front y las consultas existentes de
`infrastructure/sigrid/`.

Tests nuevos: `tests/test_f072_plantilla.py` (R1, R3, R4, R6–R10) y
`tests/test_f072_importacion.py` (R3, R4, R11–R15), a nivel de dominio, paso y HTTP. Sin
red, BBDD ni IA: fuentes en memoria (`TiposEnMemoria`, `PuertoTiposEnMemoria`).
Utilidades: `tests/utiles_plantilla.py` (`TIPOS_FICTICIOS` 9001/9002, «TIPO FICTICIO N»;
`configuracion()` ya compone las listas con ellos), `tests/utiles_importacion.py`.

## Decisiones de diseño

- **`tipos` obligatorio en los pipelines, opcional en los handlers**, el mismo patrón que
  `ubicaciones` en F-071: el pipeline no sabe de dónde salen, y el handler tiene la fuente
  por defecto detrás de la puerta de entorno.
- **Orden R11 en el handler de importación**: la fuente de tipos se construye dentro del
  `if not contexto.ya_importado` y después de las ubicaciones. Si el fichero ya se importó o
  no se reconoce, no se leen.
- **Etiqueta R6** (`<res recortado> (<cod>)`, o `<cod>` si no hay descripción): sale de
  `listas_con_tipos` / `tipos_del_desplegable` del dominio (Bloque 2), no se duplica aquí.
- **Puente hasta el Bloque 6 (revisión)**: la revisión HTTP aún compone `listados` desde el
  YAML, que ahora viene vacío, así que **en producción la pantalla de revisión no ofrecería
  tipos** hasta que el Bloque 6 la conecte a Sigrid. En `test_f056_revision_http.py`,
  `CONFIG` lleva los tipos ficticios (`replace(..., listas=listas_con_tipos(...))`) para
  seguir probando la edición. Esto no se mezcla con el trabajo de T15/T16.

## Aserciones de F-036 / F-056 / F-060 / F-071 cambiadas (con su R)

- `test_f036_configuracion_plantilla`: fuera las parametrizaciones de `listados` (R9);
  los tests de ejemplos inválidos usan Urgencia (R10); `listados == ()` (R9).
- `test_f036_excel_lector`: el Listado de la fila buena es «TIPO FICTICIO 2 (9002)» y
  la tupla esperada es `(urgente, "9002", None)` (R6, R12).
- `test_f036_importacion_dominio`, `test_f060_importar_normaliza`,
  `test_f071_dominio_importacion`: el resultado lleva `tipo_reclamacion` y `listado=None`
  (R12, R14).
- `test_f036_pipeline_importacion`, `test_f060_importacion_diferida`,
  `test_f071_pipelines`: `paso_catalogo` recibe `tipos` (R11; la lista de parámetros
  esperada es `contexto, catalogo_obra, ubicaciones, tipos`); dos comprobaciones
  `listas is CONFIG.listas` pasan a `== listas_con_tipos(CONFIG.listas, TIPOS_FICTICIOS)`
  (R12, R13).
- `test_f036_importar_http`, `test_f036_plantilla_http`, `test_f071_http`,
  `test_f071_generador`: inyectan la fuente de tipos (R1, R11).
- `test_f071_configuracion`, `test_f071_documentacion`: textos del YAML nuevos (R6, R10).
- `test_f056_revision_http`: el puente descrito arriba; las ediciones usan
  `listado="9001"` en vez de `"primero"` (R12).

## Fase RED (T15, commit `91aba5d`)

Comando, desde `services/postventa-api`:

```
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_f072_plantilla.py tests/test_f072_importacion.py --tb=line
```

Salida real, con una línea por motivo distinto (la traza entera, 38 fallos, se guardó en
el scratchpad de la sesión):

```
E   TypeError: generar_plantilla() got an unexpected keyword argument 'tipos'
E   AssertionError: assert 'listados' not in {'urgencias': [{'codigo': 'urgente', 'etiqueta': 'Urgente'}, ...
E   AssertionError: assert 'config/plant...mero, segundo' == 'config/plant...igrid (F-072)'
E   AssertionError: assert 'config/plant...on sus campos' == 'config/plant...igrid (F-072)'
E   AssertionError: assert 'Listado' == 'Listado (tip... reclamación)'
E   AssertionError: assert 'Los desplega...la plantilla.' == 'Los desplega...la plantilla.'
config/plantilla_incidencias.yaml  Listas cerradas y textos de la plantilla de incidencias (F-...los Enum del dominio (Urgencia, Listado). ...
E   AssertionError: assert ['Segundo listado'] == ['Tipo de rec...de la lista)']
E   domain.models.errores.ConfiguracionPlantillaInvalida: config/plantilla_incidencias.yaml: textos.ejemplos, ejemplo 1: «Listado» no está en su lista
E   TypeError: descargar_plantilla() got an unexpected keyword argument 'tipos'
...\interface_adapters\\api\\plantilla.py'> has no attribute 'construir_tipos_reclamacion'
E   ValueError: '9002' is not a valid Listado
E   ValueError: '9001' is not a valid Listado
E   AssertionError: assert None == '0002'
E   AssertionError: assert ['contexto', ...'ubicaciones'] == ['contexto', ...nes', 'tipos']
E   TypeError: paso_catalogo() takes 3 positional arguments but 4 were given
E   TypeError: importar_excel() got an unexpected keyword argument 'tipos'
...\interface_adapters\\api\\importar.py'> has no attribute 'construir_tipos_reclamacion'
38 failed, 6 passed in 13.76s
```

Los 6 que ya pasaban en RED comprueban comportamiento que se mantiene, como que la
urgencia de un ejemplo se siga validando (R10). Con `--tb=line` no salen los nombres de
los que pasan, así que la lista exacta no está en esta traza.

## GREEN (T16, commit `3b362f1`)

- Verificación dirigida de tasks.md (los 8 ficheros de T16): **257 passed in 170.60s**.
- Suite completa `api` (`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests`):
  **10199 passed, 369 skipped in 1011.77s**. Sin fallos, tampoco los de tiempo de
  `test_f036_r115_*`, así que no hizo falta relanzarlos aparte.

## Mutación a mano dirigida (líneas nuevas con lógica)

Cada mutante se aplicó al fichero, se lanzó el fichero de test del requisito con `-x` y se
restauraron los bytes originales. **24 mutantes, 24 muertos, 0 supervivientes**. El árbol
quedó limpio (`git status` vacío antes de escribir este informe).

| mutante | test que lo mata | resultado |
|---|---|---|
| M1 `importacion.py`: rama blanco/elegido invertida | `test_f072_r12_la_etiqueta_exacta_guarda_el_codigo_sin_aviso` | muerto |
| M2 `importacion.py`: blanco → `None` en vez de `0002` | `test_f072_r14_en_blanco_guarda_0002_sin_mirar_la_lista[sin_0002_en_la_lista]` | muerto |
| M3 `importacion.py`: guarda la etiqueta, no el código | `test_f072_r12_la_etiqueta_exacta_guarda_el_codigo_sin_aviso` | muerto |
| M4 `importacion.py`: no guarda el tipo | `test_f072_r12_la_etiqueta_exacta_guarda_el_codigo_sin_aviso` | muerto |
| M5 `importacion.py`: `listado` heredado no nulo | `test_f072_r12_la_etiqueta_exacta_guarda_el_codigo_sin_aviso` | muerto |
| M6 `paso_importacion.py`: tipos antes que ubicaciones (R11) | `test_f072_r11_paso_catalogo_lee_los_tipos_tras_catalogo_y_ubicaciones` | muerto |
| M7 `paso_importacion.py`: lectura de tipos de más, antes del catálogo | `test_f072_r11_paso_catalogo_lee_los_tipos_tras_catalogo_y_ubicaciones` | muerto |
| M8 `paso_importacion.py`: no lee los tipos | `test_f072_r11_paso_catalogo_lee_los_tipos_tras_catalogo_y_ubicaciones` | muerto |
| M9 `paso_importacion.py`: valida sin los tipos (R12) | `test_f072_r11_con_ya_importado_no_se_leen_los_tipos` | muerto |
| M10 `paso_importacion.py`: Excel de errores sin los tipos (R13) | `test_f072_r13_el_excel_de_errores_lleva_la_lista_de_los_tipos_leidos` | muerto |
| M11 `plantilla.py` (pipeline): plantilla sin los tipos (R6) | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta` | muerto |
| M12 `plantilla.py` (pipeline): tipos antes que ubicaciones (R1) | `test_f072_r1_la_plantilla_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones` | muerto |
| M13 `plantilla_yaml.py`: un YAML con `listados` carga (R9) | `test_f072_r9_un_yaml_con_listados_no_carga[con_opciones]` | muerto |
| M14 `plantilla_yaml.py`: condición de R9 invertida | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta` | muerto |
| M15 `plantilla_yaml.py`: `listados` del YAML no vacíos | `test_f072_r9_el_yaml_real_no_trae_listados` | muerto |
| M16 `plantilla_yaml.py`: ejemplo de Listado validado (R10) | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta` | muerto |
| M17 `plantilla_yaml.py`: ejemplo de Urgencia sin validar | `test_f072_r10_la_urgencia_de_un_ejemplo_se_sigue_validando` | muerto |
| M18 `api/importar.py`: sin fuente por defecto | `test_f072_r11_por_defecto_los_tipos_se_construyen_tras_las_ubicaciones` | muerto |
| M19 `api/importar.py`: puerta de la fuente invertida | `test_f072_r11_el_orden_de_las_lecturas_de_la_importacion` | muerto |
| M20 `api/importar.py`: tipos construidos antes que ubicaciones | `test_f072_r11_por_defecto_los_tipos_se_construyen_tras_las_ubicaciones` | muerto |
| M21 `api/plantilla.py`: puerta de la fuente invertida | `test_f072_r1_cada_descarga_lee_los_tipos_de_nuevo` | muerto |
| M22 `api/plantilla.py`: sin fuente por defecto | `test_f072_r1_por_defecto_los_tipos_se_construyen_tras_catalogo_y_ubicaciones` | muerto |
| M23 `plantilla_incidencias.py`: etiqueta R6 sin recortar ni vacío→código | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta` | muerto |
| M24 `plantilla_incidencias.py`: formato de la etiqueta R6 | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta` | muerto |

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite `api` completa) | 10199 passed, 369 skipped, 0 failed |
| Verificación dirigida de T16 | 257 passed |
| Cobertura de las líneas cambiadas | no medida en este bloque: sale de `PUERTA COBERTURA` de `init.sh`, que por encargo lanza el líder |
| Mutantes (a mano, dirigidos) | 24 generados, 24 muertos, 0 supervivientes |
| Campaña `harness.mutacion` | no lanzada: es T17, del líder |
| Tiempo de la suite | 1011.77 s (dirigida: 170.60 s) |
| Capa e2e | N/A en este bloque (no hay cambios de front, por R32) |

## Pendiente

- T17 (campaña de mutación del bloque y review): lo hace el líder.
- `bash harness/init.sh` sobre la rama integrada: lo hace el líder.
- Bloque 6: conectar la revisión a los tipos de Sigrid. Hasta entonces, en producción la
  revisión no ofrece tipos (ver «Puente» en las decisiones).
