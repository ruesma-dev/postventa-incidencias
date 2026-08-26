<!-- progress/impl_F-019.md -->
# F-019 · Informe del implementer

**Fecha**: 2026-08-26 · **Rama**: `feature/F-019-endpoints-persistencia`
**Spec**: `specs/F-019-endpoints-persistencia/` (34 requisitos, 24 tareas)
**Rigor**: `estandar` → fase RED, cobertura ≥ 80 % y mutación con
supervivientes analizados.

**23 de 24 tareas hechas.** T24 es `MANUAL (humano)` contra el entorno
desplegado y se deja **sin marcar**, con su procedimiento exacto en §8.

---

## 1 · Qué cambió, en una frase

Existen los tres endpoints que faltaban —`POST /api/remesa`,
`POST /api/parte`, `GET /api/cola`— y, sobre todo, **el orden dejó de depender
de la disciplina del llamante**: `POST /api/archivar` escribe la traza del
archivo en `pendiente` antes de tocar SharePoint, y como
`postventa.archivos.hash_parte` referencia a `postventa.partes`, esa escritura
sólo puede hacerse si el parte ya consta guardado.

La misma clave ajena que el 2026-08-25 hizo fallar el proceso **después** de
subir el fichero pasa a hacerlo fallar **antes**. El defecto 15 se muere aquí.

## 2 · Ficheros tocados

### Código de producción nuevo (4)

| Ruta | Qué hace |
|---|---|
| `services/postventa-api/interface_adapters/api/cuerpos.py` | Los parsers de cuerpo **compartidos** por `/api/validar` y `/api/parte`. Salieron de `validar.py` sin cambiar ni una regla (T1) |
| `services/postventa-api/interface_adapters/api/remesa.py` | `registrar_remesa`: compone el repositorio y llama a `guardar_remesa` |
| `services/postventa-api/interface_adapters/api/parte.py` | `guardar_parte_http`: reconstruye el parte, **recalcula el veredicto** y llama a `paso_persistencia` |
| `services/postventa-api/interface_adapters/api/cola.py` | `leer_cola`: tope duro al límite y serialización |

### Código de producción modificado (7)

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | Tres rutas nuevas en `ANONYMOUS`; `ReferenciaNoConsta` → **409** en `parte` y en `archivar`; cabecera reescrita (§4) |
| `services/postventa-api/interface_adapters/api/validar.py` | **Sólo** deja de definir los parsers y los importa. Comportamiento público idéntico |
| `services/postventa-api/application/pipelines/paso_archivo.py` | La traza previa `pendiente` (+ su porqué escrito) |
| `services/postventa-api/domain/models/errores.py` | `ReferenciaNoConsta` y `PeticionDePersistenciaInvalida` |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | `_escribir` distingue `ForeignKeyViolation` |
| `services/postventa-front/js/api.js` | `registrarRemesa`, `guardarParte`, `cola` |
| `services/postventa-front/js/pipeline.js` | `cuerpoDeParte`, `guardarParte`, `revalidarYGuardar`; `procesarParte` guarda tras validar; `cuerpoDeArchivo` se niega con un parte sin guardar |
| `services/postventa-front/js/app.js` | Registra la remesa antes de procesar, conserva `remesaId`, marca no archivable el parte no guardado |
| `services/postventa-front/index.html` | Pinta el motivo por el que un parte apto no es archivable (§7, desviación anotada) |

### Tests (8 nuevos, 6 ajustados) y documentación (2)

Nuevos: `test_f019_referencias_pg.py`, `test_f019_remesa_http.py`,
`test_f019_parte_http.py`, `test_f019_cola_http.py`,
`test_f019_logs_sin_datos_personales.py`, `test_f019_orden_archivado.py`,
`test_f019_documentacion.py` y `tests_js/persistencia.test.js`.

Ajustados: `test_f006_paso_archivo.py`, `test_f010_borde_persistencia.py`,
`test_f010_endpoints_protegidos.py`, `test_f010_integracion_expuesto.py`,
`test_f005_ddl_idempotente_texto.py`, `tests_js/pipeline.test.js`, más los dos
dobles (`utiles_pg.py`, `utiles_sharepoint.py`).

Documentación: `docs/ARCHITECTURE.md` (paso 6) y `docs/INTEGRACION.md` (§8).

**Cero ficheros SQL. Cero sentencias DDL. Cero conexiones reales.**
`RepositorioPartesPort` **no ganó ni un método**. `infra/` sin tocar.
`harness/features.json` sin tocar.

## 3 · Decisiones de diseño que la spec dejó abiertas

### 3.1 · Con qué excepción se responde 400 (nueva: `PeticionDePersistenciaInvalida`)

La spec exige 400 en R4, R5, R10 y R17 pero no dice con qué excepción. El
`design.md` §4 sólo declaraba `ReferenciaNoConsta` como añadido a
`errores.py`.

Se ha añadido **una** excepción más, `PeticionDePersistenciaInvalida`,
siguiendo el patrón que el código ya tiene —`CuerpoDeValidacionInvalido`,
`CuerpoDeArchivoInvalido`: una por familia de endpoint—. La alternativa era
reutilizar la de `/api/validar` para los tres endpoints nuevos, y su nombre
mentiría en `remesa` y en `cola`, que no validan nada.

`POST /api/parte` acepta **las dos** y las mapea al mismo 400: el resto de su
cuerpo lo comprueban los parsers compartidos, que levantan
`CuerpoDeValidacionInvalido` porque es literalmente el cuerpo de
`/api/validar`. Es la consecuencia directa de compartir los parsers, y se
prefiere a traducir una excepción en otra por el camino.

### 3.2 · De dónde salen `resultado_parte` y `resultado_validacion`

El contrato de R7 los promete, y `paso_persistencia` —que **no se
reescribe**, `design.md` §2— consume los dos `ResultadoGuardado` y los
descarta: devuelve el contexto.

Se resuelve con `_AnotaLosResultados`, un envoltorio del puerto que anota qué
devolvió cada guardado al pasar. Es composición en el punto de entrada, que
es donde `docs/CONVENTIONS.md` la pone.

Se descartó deducirlos del texto del aviso «este parte ya se había procesado
antes»: ataría la respuesta HTTP a la redacción de un mensaje y, sobre todo,
**no daría ninguna respuesta para la validación**, porque el paso no emite
aviso por ella.

### 3.3 · `procesarParte` y el `remesaId` en el front

`procesarParte(parte, api, remesaId)` gana un tercer argumento y devuelve una
clave más, `guardado`. Sin `remesaId` **no se intenta guardar** y se devuelve
`{ok: false, motivo}`: el backend respondería 409 y la petición sería ruido.
Los tests de F-007 siguen pasando sin tocarse porque sólo leen las tres claves
anteriores.

`revalidar` se deja **intacto** —es el contrato de F-007 R17: una petición,
sin IA— y R28 se cumple con `revalidarYGuardar`, que compone las dos cosas y
tiene test propio. Poner el guardado dentro de `revalidar` habría roto ese
contrato; ponerlo en `app.js` habría dejado R28 sin test, porque en `app.js`
«si algo merece un test, no vive aquí».

## 4 · Lo que se corrigió por el camino, y no estaba previsto

1. **Dos literales con forma de GUID.** `test_f006_repo_sin_identificadores.py`
   los cazó. **No se relajó el patrón**: los UUID de los tests se generan en
   ejecución. El guardián tenía razón — quien lea una cadena con forma de GUID
   no puede distinguir una inventada de una real.
2. **La palabra `SELECT` en un docstring de `application/`.**
   `test_f005_arquitectura.py` la cazó. Reescrita sin verbos SQL en vez de
   ampliar la tolerancia del test.
3. **Los tests del defecto 14 de F-010** describían «fichero arriba, traza
   perdida» con un repositorio caído de principio a fin. Con la garantía de
   orden ese montaje ya produce **otro** escenario: la traza previa falla y no
   se sube nada. Se **precisó el montaje** —el doble falla sólo en la segunda
   llamada— conservando todas las aserciones (`subidas == 1`, 500 con cuerpo)
   y se **añadió** el caso nuevo. Ni una aserción se debilitó.

5. **Dos agujeros que destapó la campaña de mutación**, en el valor frontera
   que los requisitos declaran válido: `limite=1` en `GET /api/cola` (R17) y
   `num_partes=0` en `POST /api/remesa` (R4). Los dos habrían respondido 400 a
   una petición legítima si alguien hubiera tocado la comparación. Cerrados
   con tests; el detalle, en «Evidencias».

## 5 · Los cuatro riesgos del encargo

| # | Riesgo | Qué se hizo |
|---|---|---|
| 1 | T1 mecánico en el camino crítico | Commit propio (`8024b2d`), con `test_f004_validar_http.py` **sin tocar** en verde: 16 passed |
| 2 | Los tests de F-006 se pueden aflojar | Se **apretaron**: `llamadas_guardar_archivo == 2` y `estados == ["pendiente", "archivado"]` (y `["pendiente", "error"]` en el camino fallido), y `== 0` con el parte ya archivado. Se vieron caer antes de implementar (§6) |
| 3 | Nadie fija la clave ajena | T15 la fija leyendo el DDL, y se comprobó a mano que cae al borrar la línea (§6) |
| 4 | Una llamada HTTP más por parte | Es una escritura en PostgreSQL, del orden de milisegundos, contra un presupuesto de 45 s con un peor caso medido de 6,5 s en `/api/extraer`. **Queda por medir en el entorno real: es parte de T24** (§8, paso 5) |

## 6 · Fase RED · las siete trazas rojas, pegadas

### T2 · el error de referencia

```
$ python -m pytest tests/test_f019_referencias_pg.py -q
=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f019_referencias_pg.py ______________
ImportError while importing test module 'tests\test_f019_referencias_pg.py'.
Traceback:
tests\test_f019_referencias_pg.py:29: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'ReferenciaNoConsta' from 'domain.models.errores'
=========================== short test summary info ===========================
ERROR tests/test_f019_referencias_pg.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.55s
```

### T4 · `POST /api/remesa`

```
$ python -m pytest tests/test_f019_remesa_http.py -q
...
E   ModuleNotFoundError: No module named 'interface_adapters.api.remesa'
tests\test_f019_remesa_http.py:71: ModuleNotFoundError
E   FileNotFoundError: [Errno 2] No such file or directory: '...\interface_adapters\api\remesa.py'
E   FileNotFoundError: [Errno 2] No such file or directory: '...\interface_adapters\api\parte.py'
E   FileNotFoundError: [Errno 2] No such file or directory: '...\interface_adapters\api\cola.py'
25 failed in 2.57s
```

### T6 · `POST /api/parte`

```
$ python -m pytest tests/test_f019_parte_http.py -q
...
E   ModuleNotFoundError: No module named 'interface_adapters.api.parte'
29 failed in 2.72s
```

### T8 · `GET /api/cola`

```
$ python -m pytest tests/test_f019_cola_http.py -q
...
E   ModuleNotFoundError: No module named 'interface_adapters.api.cola'
15 failed in 1.84s
```

### T10 · el tope duro de la cola

```
$ python -m pytest tests/test_f019_cola_http.py -q
FAILED tests/test_f019_cola_http.py::test_f019_r16_ningun_limite_supera_el_tope_duro[501]
FAILED tests/test_f019_cola_http.py::test_f019_r16_ningun_limite_supera_el_tope_duro[1000]
FAILED tests/test_f019_cola_http.py::test_f019_r16_ningun_limite_supera_el_tope_duro[100000]
FAILED tests/test_f019_cola_http.py::test_f019_r16_la_respuesta_nunca_trae_mas_del_tope
E       assert [501]    == [500]
E       assert [1000]   == [500]
E       assert [100000] == [500]
E       assert 525 == 500
INFO     function_app:function_app.py:437 cola: 525 partes esperando decision
4 failed, 16 passed in 2.41s
```

### T13 · la garantía de orden (el corazón)

```
$ python -m pytest tests/test_f019_orden_archivado.py -q
FAILED ...::test_f019_r19_la_traza_previa_se_escribe_antes_de_tocar_el_archivador
FAILED ...::test_f019_r19_las_dos_trazas_van_en_orden_pendiente_luego_archivado
FAILED ...::test_f019_r19_la_traza_previa_lleva_el_nombre_y_la_carpeta_que_se_van_a_usar
FAILED ...::test_f019_r19_la_traza_previa_no_lleva_fecha_de_archivado
FAILED ...::test_f019_r20_si_el_parte_no_consta_el_archivador_no_recibe_nada
FAILED ...::test_f019_r21_si_la_base_no_responde_tampoco_se_sube_nada
FAILED ...::test_f019_r22_un_fallo_del_proveedor_deja_pendiente_y_luego_error
FAILED ...::test_f019_r22_el_500_de_archivo_sin_traza_sigue_existiendo
FAILED ...::test_f019_r24_una_traza_pendiente_o_de_error_si_deja_reintentar[pendiente]
FAILED ...::test_f019_r24_una_traza_pendiente_o_de_error_si_deja_reintentar[error]
FAILED ...::test_f019_r20_el_borde_responde_409_diciendo_que_hay_que_guardar_el_parte
FAILED ...::test_f019_r20_el_409_promete_que_no_se_ha_subido_nada
FAILED ...::test_f019_r21_el_borde_responde_503_diciendo_que_se_puede_reintentar
FAILED ...::test_f019_r19_el_camino_feliz_del_borde_sigue_devolviendo_200
14 failed, 4 passed in 2.59s
```

Y los de F-006, **apretados** y vistos caer contra el comportamiento nuevo:

```
$ python -m pytest tests/test_f006_paso_archivo.py -q
E   AssertionError: assert 1 == 2
E    +  where 1 = RepositorioFalso(... llamadas_guardar_archivo=1).llamadas_guardar_archivo
tests\test_f006_paso_archivo.py:601: AssertionError
FAILED ...::test_f006_r23_la_traza_de_exito_lleva_todo_lo_declarado
FAILED ...::test_f006_r24_un_fallo_deja_traza_de_error_y_permite_reintentar
2 failed, 27 passed in 1.02s
```

### T19 · el cableado del front

```
$ node --test "tests_js/persistencia.test.js"
TypeError: cuerpoDeParte is not a function
TypeError: guardarParte is not a function
TypeError: revalidarYGuardar is not a function
  at TestContext.<anonymous> (tests_js\persistencia.test.js:395:26)
ℹ tests 18
ℹ pass 1
ℹ fail 17
```

### Verificaciones a mano que la spec pedía además de la fase RED

**T12 · el guardián de logs sabe cazar una fuga real.** Metida a mano en
`function_app.py::parte` (y revertida):

```
    log.debug("parte: cuerpo=%s", req.get_body())

$ python -m pytest tests/test_f019_logs_sin_datos_personales.py -q
tests\test_f019_logs_sin_datos_personales.py:74: AssertionError
DEBUG function_app: parte: cuerpo=b'{... "promocion": {"valor": "PROMOCION INVENTADA DEL TEST" ...
    "dni_cliente": {"valor": "00000000T"}, "observaciones": {"valor": "texto manuscrito ..."} ...}'
FAILED ...::test_f019_r18_guardar_un_parte_no_publica_nada_del_papel
FAILED ...::test_f019_r18_un_parte_rechazado_tampoco_publica_lo_que_venia
2 failed, 8 passed in 1.75s
$ (revertido) 10 passed in 1.52s
```

**T15 · el test cae si se borra la clave ajena del DDL.** Borrada a mano de
`05_archivos.sql` y **restaurada**; no se ejecutó DDL contra ningún servidor:

```
-    hash_parte       text PRIMARY KEY
-                     REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
+    hash_parte       text PRIMARY KEY,

$ python -m pytest tests/test_f005_ddl_idempotente_texto.py -q
E   AssertionError: assert sin_clave_ajena != archivos
FAILED ...::test_f019_r19_archivos_referencia_a_partes_y_es_un_requisito
FAILED ...::test_f019_r19_el_barrido_de_la_clave_ajena_ve_lo_que_hay
2 failed, 24 passed in 0.92s
$ (restaurado) 26 passed in 0.64s
```

**T16 y T17 · el test de anonimidad no se relajó.** Comprobado por las dos
vías que exige R31, y con `FUNCTION` en cada una de las rutas nuevas:

```
(a) auth_level de 'validar' a FUNCTION SIN tocar la explicacion:
    FAILED ...::test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada
    1 failed, 7 passed in 0.45s

(b) explicacion borrada SIN tocar ningun auth_level:
    FAILED ...::test_f010_r32_la_cabecera_avisa_de_que_la_cabecera_de_identidad_no_protege
    FAILED ...::test_f010_r18_health_sigue_anonimo   (+4 mas)
    6 failed, 2 passed in 0.46s

(c) FUNCTION en cada ruta nueva:
    health -> 2 failed | cola -> 1 failed | parte -> 1 failed | remesa -> 1 failed

(restaurado) 8 passed in 0.19s
```

## 7 · Desviaciones respecto a la spec, y su justificación

1. **`services/postventa-front/index.html` no estaba en la tabla de ficheros
   de `design.md` §4** y se ha tocado (16 líneas). Motivo: **R27 exige
   «enseñar el motivo»** por el que un parte no es archivable, y sin pintarlo
   no se enseña en ninguna parte. Son dos bloques: el motivo bajo cada parte y
   la cuenta de aptos no guardados en la sección de archivo. Sin la segunda,
   los partes desaparecerían de la cuenta del botón sin explicación y alguien
   daría la remesa por archivada entera.
2. **`errores.py` gana dos excepciones y no una** (§3.1).
3. **`tests_js/pipeline.test.js`**: al fixture común se le añade
   `guardado: true`. No relaja nada —los dos tests de `throws` siguen cayendo
   por su propio motivo— y refleja que «archivable» ahora incluye «ya
   guardado».
4. **`test_f010_borde_persistencia.py`** se precisó, con el porqué escrito en
   su cabecera (§4.3).

## 8 · T24 · Verificación MANUAL (humano) — **pendiente, sin marcar**

No la ejecuta el agente: exige el entorno desplegado y **abrir a propósito la
ventana de escritura**. Procedimiento exacto:

**Preparación.** Encender `ARCHIVO_HABILITADO` en las App Settings de
`func-postventa-dev` (sin redesplegar). **Anotar la hora**: hay que volver a
apagarlo al terminar.

**La vía es la consola del navegador en el front, con sesión iniciada**
(`docs/DESPLIEGUE.md` §5 bis). El host desnudo de la Function devuelve `400`
de la plataforma a todo el mundo, así que **no hay `-BaseUrl` que sirva**: las
llamadas van al mismo origen y pasan por el proxy.

Usar un **parte sintético**, nunca uno de `muestras/`: llevan datos
personales, DNI incluido.

1. **El defecto 15, de frente.** `POST /api/archivar` con un `hash` que no
   consta guardado → debe responder **409** y el cuerpo debe decir que hay que
   guardar el parte primero. **Comprobar la carpeta de SharePoint: no puede
   aparecer nada.**
2. **El circuito entero.** `POST /api/remesa` → guardar el `remesa_id` →
   `POST /api/parte` con ese id → `POST /api/archivar` → **200**. El fichero
   tiene que estar en su carpeta **una sola vez** y `postventa.archivos` tener
   su fila en `archivado`.
3. **La cola.** `GET /api/cola` con un parte con observaciones → devuelve su
   entrada. Con `limite=100000` → **como mucho 500** entradas (R16).
4. **Reproceso.** Repetir el paso 2 entero → sin duplicados en SharePoint,
   `resultado_parte: "actualizado"` y `reprocesos` incrementado.
5. **Medir el coste de la llamada de más** (riesgo 4): anotar el tiempo de
   `POST /api/parte` que da la pestaña de red. La previsión son milisegundos
   contra un presupuesto de 45 s; si pasara de un segundo, hay que decirlo.

**Al terminar: volver a apagar `ARCHIVO_HABILITADO`** y anotar aquí el
resultado real —no «debería funcionar»— con el fragmento de consola, **sin
secretos y sin datos personales**.

## 9 · Avisos para el líder

1. **`docs/INTEGRACION.md` §8 ha cambiado y hay que copiarla a
   `azure-apps/postventa-incidencias.md`.** No se ha commiteado allí: el
   humano decidió el 2026-08-20 que los agentes no commitean en ese
   repositorio. Cambian la tabla de endpoints (nueve filas), la nota de la
   anonimidad y la tabla de «qué NO está desplegado».
2. **Al cerrar la feature hay que decirlo (decisión D4)**: lo guardado queda
   guardado y la cola sobrevive entre sesiones, pero **recargar el navegador
   sigue perdiendo el trabajo en curso**. Rehidratar la sesión exige un método
   de lectura nuevo en `RepositorioPartesPort` y es **feature nueva**.
3. **`POST /api/archivar` cambia de comportamiento para quien ya lo llamaba**:
   un parte sin guardar recibe ahora un 409 donde antes recibía un 200 a
   medias o un 500. Es la mejora, pero conviene decirlo.

---

## Evidencias

Números **medidos**, no estimados. Máquina: 22 núcleos, Python 3.12.7.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests del backend** | **1233 passed, 13 skipped** | `pytest` en `services/postventa-api`, vía `harness/init.sh` |
| **Tests del front (Python)** | **85 passed** | `pytest` en `services/postventa-front` |
| **Tests del front (JavaScript)** | **122 pass, 0 fail** | `node --test tests_js/*.test.js`, por el puente `test_f007_js.py` |
| **Tests del arnés** | **17 passed** | `pytest` en la raíz |
| **Resultado global** | **verde, exit 0** | `bash harness/init.sh` → `ENTORNO LISTO. Puedes trabajar.` |
| **Tiempo de la suite** | **69,97 s** (backend) + **3,17 s** (front) | el que imprime la propia suite |
| **Cobertura de las líneas cambiadas** | **100,0 %** (269/269, umbral 80 %) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Ficheros «no medidos»** | **ninguno** | los nueve del alcance salen medidos |
| **Mutantes generados / evaluados** | **35 / 35** | `progress/mutacion_F-019.md` |
| **Muertos** | **35** | ídem |
| **Supervivientes** | **0** | ídem |
| **Timeouts** | **0** | ídem |
| **Tiempo total de la campaña** | **313,0 s** | ídem |
| **Workers** | **8** (`--workers 8`) | ver la nota de abajo |
| **Coste por mutante** | **71,5 s** | `313,0 × 8 ÷ 35`, la fórmula de `CHECKPOINTS.md` C4 bis |

El coste por mutante (**71,5 s**) cuadra con lo que tarda la suite del backend
(**69,97 s**), que es lo que tiene que pasar: evaluar un mutante **es**
ejecutarla entera. No hay campaña sospechosa por rápida.

### Las tres campañas, y por qué hubo tres

Se declaran las tres porque los totales de las dos primeras no son los que
valen, y ocultarlo sería peor que contarlo.

| # | Workers | Mutantes | Muertos | Supervivientes | Timeouts | Tiempo | Estado |
|---|---|---|---|---|---|---|---|
| 1 | 16 | 35 | 31 | **4** | 0 | 282,3 s | descartada: los 4 supervivientes se cerraron con tests |
| 2 | 16 | 35 | 25 | 0 | **10** | 305,7 s | **descartada por escrito**: 10 mutantes sin evaluar |
| 3 | 8 | 35 | **35** | **0** | **0** | 313,0 s | **la válida**, y la que está en `progress/mutacion_F-019.md` |

**Campaña 1 · los cuatro supervivientes eran el mismo agujero, y era real.**
Los cuatro caían sobre el valor frontera que el requisito declara **válido** y
que ningún test pedía:

- `cola.py:109`, `if pedidas < 1:` → `<= 1` y `< 2`. Con esa mutación,
  `limite=1` —que R17 admite explícitamente— habría respondido **400**. Ningún
  test pedía exactamente una entrada. **No es equivalente**: cambia una
  respuesta observable. Cerrado con
  `test_f019_r17_el_limite_uno_es_valido_y_llega_tal_cual`.
- `remesa.py:129`, `crudo < 0` → `<= 0` y `< 1`. Con esa mutación,
  `num_partes=0` —que R4 admite— habría respondido **400**. Y es un caso real:
  una remesa de la que el troceado no sacó ningún parte utilizable **se
  registra igual, con sus avisos**, y es justo la que hay que poder mirar
  después para saber qué llegó. Cerrado con
  `test_f019_r4_una_remesa_de_cero_partes_es_valida`.

Antes de relanzar se comprobó **a mano** que los cuatro mueren con los tests
nuevos: cada mutación aplicada al fichero real, suite en rojo, fichero
restaurado (`1 failed, 50 passed` en los cuatro).

**Campaña 2 · los 10 timeouts son míos, no del código.** Estuve ejecutando la
suite del backend y los tests del front **mientras** la campaña corría con 16
workers en una máquina de 22 núcleos. Los mutantes de esa tanda no llegaron a
los 120 s de presupuesto por contención de CPU, no por un bucle infinito: son
todos cambios de código de estado (`400 → 401`, `503 → 504`) en
`function_app.py`, y **los mismos mutantes salen muertos en la campaña 3**.
Diez mutantes sin evaluar no es un informe válido, así que se relanzó.

**Campaña 3 · limpia.** Con 8 workers en vez de 16 y sin ejecutar nada más en
la máquina: **35 evaluados, 35 muertos, 0 supervivientes, 0 timeouts**. Es la
que queda en `progress/mutacion_F-019.md` y la única cuyos números se
declaran arriba.

El nivel `estandar` no exige cero supervivientes —exige que estén
analizados—, pero aquí no queda ninguno que analizar: los cuatro que hubo se
convirtieron en dos tests.
