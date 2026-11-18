<!-- progress/review_F-072_bloque5.md -->
Revisión completa del Bloque 5 (pasada 1): delta `86a1748..ecbfb0a` (T15 `91aba5d`, T16 `3b362f1`,
informe `877304f`, integración `ecbfb0a`). Los Bloques 1–3 quedan dados por buenos; el 4 lo revisa otro
reviewer en paralelo.

# F-072 · Review del Bloque 5 (plantilla e importación: R1, R3, R4, R6–R15, R32)

- **Veredicto: APROBADO** (APPROVED) en `ecbfb0a`, con dos condiciones que no son del código:
  1. `bash harness/init.sh` verde sobre la rama integrada (no lo he ejecutado: lo lanza el líder).
  2. T17 sigue abierta: la mutación del bloque depende de la decisión del humano (campaña de ~4 h o
     veredicto a mano). Mi reproducción de abajo es la evidencia a mano disponible hoy.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED, cobertura, mutación
  con 0 supervivientes, RM1–RM7.

## 1 · Qué he ejecutado

- `pytest tests/test_f072_plantilla.py tests/test_f072_importacion.py` en el árbol: **44 passed**.
- Los 17 ficheros de test que toca el bloque (los 8 de T16 + F-036/F-056/F-060/F-071 cambiados),
  sobre una copia de HEAD (`git archive`) en el scratchpad: **1124 passed in 565 s**. (Una primera
  pasada dio 26 rojos de `test_f071_documentacion.py` y otros que leen `docs/`: la copia no traía la
  raíz del repositorio. Con `docs/`, `harness/` y `specs/` añadidos, todo verde.)
- 19 mutantes a mano sobre **esa copia** (sección 3), no en el árbol de trabajo: hay otro reviewer
  ejecutando tests en esta carpeta y un mutante aplicado aquí le daría rojos falsos. `git status` limpio.

## 2 · Spec, diseño y alcance

| R | Implementación | Test que lo cubre |
|---|---|---|
| R1 (plantilla, importación) | `generar_plantilla`: catálogo → ubicaciones → `tipos()` → `listas_con_tipos`; handler con fuente por defecto | `test_f072_r1_la_plantilla_lee_los_tipos_una_vez...`, `..._cada_descarga_lee_los_tipos_de_nuevo`, `..._por_defecto_los_tipos_se_construyen...` |
| R3, R4 | los errores de `tipos()` suben sin fichero / sin validar ni registrar | `test_f072_r3_r4_*` (pipeline, paso y ruta HTTP 409/503), `test_f072_r4_al_techo_con_la_lectura_de_verdad...` |
| R6 | `tipos_del_desplegable` (dominio, bloque anterior) vía `listas_con_tipos` | `test_f072_r6_listado_ofrece_los_tipos_en_su_orden...` (orden leído, `res` recortado, `None` y solo espacios → código) |
| R7 | lista vacía → rama `textLength = 0` del generador de F-071 | `test_f072_r7_sin_tipos_listado_solo_admite_el_blanco` |
| R8 | sin cambio | `test_f072_r8_cabecera_hojas_identificador_y_version_2...` |
| R9 | `"listados" in crudo` → `ConfiguracionPlantillaInvalida`; `listados=()` | `test_f072_r9_*` (YAML real; con opciones, vacía y nula) |
| R10 | YAML §6.3 literal; `_ejemplos` sin `Listado` | `test_f072_r10_*` (6 tests; ≤ 32/255; urgencia aún validada) |
| R11 | `paso_catalogo` lee tipos tras ubicaciones, después de la guarda `ya_importado`; el handler construye la fuente dentro de `if not ya_importado` | `test_f072_r11_*` (7 tests: orden, una lectura, ni construir ni leer sin reconocer o con `ya_importado`) |
| R12 | `{etiqueta: codigo}` + `f.tasado` (casado de F-060) → código | `test_f072_r12_*` (exacta, única por clave con aviso, código suelto no casa) |
| R13 | `paso_excel_errores` con `listas_con_tipos(listas, contexto.tipos)` | `test_f072_r13_las_etiquetas_de_antes...`, `..._el_excel_de_errores_lleva_la_lista...` (abre el xlsx) |
| R14 | blanco → `TIPO_RECLAMACION_POR_DEFECTO` sin mirar `listados` | `test_f072_r14_en_blanco_guarda_0002_sin_mirar_la_lista[3]`, `..._sin_tipos_un_valor_es_error` |
| R15 | `listado=None`, `tipo_reclamacion` siempre puesto | `test_f072_r15_toda_valida...`, `test_f072_r12_r14_r15_la_bandeja_recibe...` |
| R32 | ni front, ni `excel_openpyxl.py`, ni `infrastructure/sigrid/`, ni `ddl.py`/`sql/` en el diff (comprobado con `git diff --name-only`) | `test_f072_alcance_cerrado.py` llega en el Bloque 7 (T21) |

- Ficheros: exactamente los de T16 y §3.2. Hexagonal: el pipeline recibe `FuenteTiposReclamacion`
  (Callable de aplicación), el handler compone la fábrica de infraestructura; el dominio no importa nada
  nuevo de fuera.
- Convenciones: primera línea con ruta en los ficheros nuevos; sin `print`, sin secretos; datos
  ficticios (`9001…`, «TIPO FICTICIO N», obra `0677`). `contexto.tipos` con `repr=False` (R30) y
  probado (`"TIPO FICTICIO" not in repr(contexto)`).
- Aserciones antiguas cambiadas: cada una con su R y su sustituta (`listados == ()`, ejemplo
  indicativo, `== listas_con_tipos(...)` en vez de `is CONFIG.listas`). Ninguna borrada sin sustituta.

## 3 · Mutación

**La tabla del implementer (24/24 muertos) no es reproducible tal cual**: describe cada mutante con una
frase, sin `fichero:línea`, sin el texto exacto original → mutado y sin el número de fallos que pide
mi protocolo para una campaña a mano. Por eso no la doy por buena como tabla, sino que he
**reproducido 19 mutantes** con texto exacto, que cubren las filas delicadas (M2, M6, M7, M9, M10,
M12, M13, M18–M20, M23) y añaden casos que ella no trae. Script: `mutar_b5.py` en el scratchpad de la
sesión; `-x` salvo las variantes «+», que van sin `-x` para ver todos los que caen.

| Id | Fichero | Original → mutado | Resultado (primer test que cae) |
|---|---|---|---|
| R14a | `importacion.py` | `TIPO_RECLAMACION_POR_DEFECTO` → `(… if … in listados.values() else None)` (blanco comprobado contra la lista) | muerto: `r14_en_blanco…[sin_0002_en_la_lista]` |
| R14b | `importacion.py` | `TIPO_RECLAMACION_POR_DEFECTO` → `next(iter(listados.values()), …)` (blanco = primer tipo) | muerto: ídem |
| R11a | `paso_importacion.py` | `_t = tipos()` antes de `if contexto.ya_importado:` | muerto: `r11_paso_catalogo…`; «+» con los dos tests de `ya_importado`: **2 fallan** |
| R11b | `paso_importacion.py` | `contexto.tipos = tipos()` antes de `leer_catalogo` (RM7, catálogo) | muerto: `r11_paso_catalogo_lee…` |
| R11c | `paso_importacion.py` | `contexto.tipos = tipos()` antes de `ubicaciones(catalogo)` (RM7, ubicaciones) | muerto: ídem |
| R11d | `paso_importacion.py` | `tipos()` dos veces | muerto: ídem |
| R11e | `api/importar.py` | `if tipos is None: tipos = fuente_de_tipos(…)` antes de `paso_huella` (fuera de la guarda) | muerto: `r11_por_defecto_los_tipos_se_construyen…` |
| P1 | `pipelines/plantilla.py` | `_t = tipos()` antes de `leer_catalogo` (RM7) | muerto: `r1_la_plantilla_lee_los_tipos_una_vez…` |
| P2 | `pipelines/plantilla.py` | `con_tipos = …tipos()` antes de `ubicaciones(catalogo)` (RM7) | muerto: ídem |
| R1a | `api/plantilla.py` | fuente de tipos construida antes que la de ubicaciones | muerto: `r1_por_defecto_los_tipos_se_construyen…` |
| R6a | `plantilla_incidencias.py` | `_nombre_recortado(t.nombre)` → `t.nombre.strip() if t.nombre else None` (`res` de espacios → `" (9004)"`) | muerto: `r6_listado_ofrece…` |
| R6b | `plantilla_incidencias.py` | `for t in tipos` → `for t in sorted(tipos, key=…codigo)` | muerto: ídem |
| R7a | `pipelines/plantilla.py` | sin tipos, `listas` de la configuración en vez de `listas_con_tipos` | muerto: `r7_sin_tipos_listado_solo_admite_el_blanco` |
| R12a | `importacion.py` | `{o.etiqueta: o.codigo …}` → `{o.codigo: o.codigo …}` | muerto: `r12_la_etiqueta_exacta…` |
| R12b | `importacion.py` | casa por etiqueta **o** por código | muerto: `r12_el_codigo_suelto…no_casa` |
| R12c+ | `paso_importacion.py` | `listas=listas_con_tipos(listas, contexto.tipos)` → `listas=listas` (validación, M9) | muerto, **4 fallan** (ver obs. 2) |
| R13a | `paso_importacion.py` | Excel de errores con `listas=listas` | muerto: `r13_el_excel_de_errores_lleva…` |
| R13b | `paso_importacion.py` | Excel de errores con `listas_con_tipos(listas, ())` | muerto: ídem |
| R9a | `plantilla_yaml.py` | `if "listados" in crudo:` → `if crudo.get("listados"):` | muerto: `r9_un_yaml_con_listados_no_carga[vacia]` |

**19 de 19 muertos, 0 supervivientes.** Ningún equivalente (RM3, RM5 N/A: no hay equivalentes
declarados). RM6: ningún mutante se mató quitando una guarda. **RM7** (el requisito central de R1/R11
es un orden): bajé la lectura de tipos un paso por cada colaborador que debe precederla —catálogo y
ubicaciones—, en la importación (R11b, R11c) y en la plantilla (P1, P2), más la construcción en los dos
bordes (R11e, R1a): **todas en rojo, y siempre con un test de F-072** (no de una suite vecina).
RM1/RM2/RM4: no hay informe automático que medir; mi reproducción es el RM4 (copia en el scratchpad).

## 4 · El puente hasta el Bloque 6

**Aceptable**, con una condición. En `ecbfb0a` el YAML trae `listados` vacío y la revisión HTTP aún
no lee Sigrid, así que `GET /api/revision` daría `catalogo.listados = []` y una edición solo admitiría
nulo (→ `0002`) o el tipo que ya tiene la fila. `aplicar_accion` todavía no pasa `tipos` a
`motivos_no_aprobable`, así que **no bloquea aprobaciones** (sin `tipos` no se calcula R24). Es un
estado intermedio coherente y declarado en el informe, y solo vive en la rama.
**Condición:** la rama no va a `dev` ni se despliega antes de que el Bloque 6 (T18–T19) cierre la
revisión con los tipos de Sigrid. Lo garantiza el plan (merge a `dev` tras la review final del
Bloque 7), pero el líder debe dejarlo escrito en `progress/current.md` mientras dure. El `CONFIG` de
`test_f056_revision_http.py` con `TIPOS_FICTICIOS` es legítimo y puede quedarse: imita lo que hará la
aplicación (`listas_con_tipos`).

## 5 · Checkpoints

- C1 `init.sh`: pendiente, lo ejecuta el líder (condición 1); no lo he lanzado porque el encargo me lo prohíbe. Ficheros base del arnés `[x]`.
- C2 `[x]` rama `feature/F-072-tipo-reclamacion-sigrid`; una feature activa. `current.md`/`history.md`: los cierra el líder.
- C3 `[x]` hexagonal, ruta en primera línea, sin `print`/secretos/TODO; reglas de partes (unidad, firmas, reprocesar, estados) N/A: el bloque no toca partes ni estados de Sigrid; sin escaneados en git.
- C3 bis / C3 ter `N/A`: ni documentos externos ni conversaciones. C3 quater `N/A` en el bloque: `azure-apps/` lo pone al día el líder al desplegar (design §11).
- C4 `[x]` cada R del bloque con test (tabla §2); sin red, base ni IA (dobles en memoria). Dobles: `PuertoTiposEnMemoria.leer()` es el único método de `TiposReclamacionPort`; `TiposEnMemoria` es una `FuenteTiposReclamacion` (callable). La comprobación automática de dobles es de `init.sh`.
- C4 bis: RED `[x]` (salida real, 38 failed / 6 passed, motivo por motivo); cobertura `pendiente: PUERTA COBERTURA de init.sh` (líder); mutación `pendiente: decisión del humano` (T17), con la reproducción de §3; «Evidencias» `[x]`; capa e2e `N/A` (sin front, R32).
- C4 ter `N/A`: no existe `harness/rutas_sensibles.json`.
- C5: T15 y T16 `[x]` con commits `F-072 T15/T16: …`; T17 abierta (condición 2); árbol limpio.

## 6 · Observaciones (no bloquean)

1. **Formato de la tabla a mano.** Para los Bloques 6 y 7, la tabla del implementer debe traer
   `fichero:línea`, el texto exacto original → mutado y el número de fallos; sin eso no se puede
   reproducir ninguna fila al pie de la letra (`reviewer.md`, campaña manual).
2. **`configuracion()` de `tests/utiles_plantilla.py` ya trae `TIPOS_FICTICIOS`**, que se solapan con
   los `TIPOS` de `test_f072_importacion.py` (9001, 9002). Por eso, con R12c (la validación ignora los
   tipos leídos) `test_f072_r12_r14_r15_la_bandeja_recibe_el_codigo_o_0002` **sigue en verde**: lo
   cazan cuatro tests de R11 que usan el YAML real o `LISTAS_DEL_YAML`. Está cubierto, pero por tests
   cuyo nombre no es R12. Mejora barata: que ese test use un tipo fuera de los ficticios (p. ej. 9003).
3. Líneas de más de 100 caracteres en `test_f071_pipelines.py` y `test_f072_*.py` (el lint no bloquea).

## 7 · Automejora (propuesta, no aplicada)

`reviewer.md`, campaña manual: añadir que, si hay otro agente ejecutando tests en la misma carpeta,
los mutantes se aplican en una copia (`git archive HEAD` al scratchpad), no en el árbol: así ningún
mutante da rojos falsos a otro, y RM4 ya da el procedimiento.
