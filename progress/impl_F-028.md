<!-- progress/impl_F-028.md -->
# F-028 · Estado del parte — informe del implementer · bloques 0 y 1

> Encargo: **T1, T2, T3 y T4** de `specs/F-028-estado-del-parte/tasks.md`.
> Parada obligada al terminar el bloque 1. **No se ha entrado en el bloque 2.**
>
> Rama `feature/F-028-estado-del-parte`, desde `ed46181`. Rigor **`estandar`**
> (`harness/rigor.json`): fase RED obligatoria, puerta de cobertura al 80 % de
> las líneas cambiadas, campaña de mutación con los supervivientes
> documentados. Sin `push`, sin tocar `dev` ni `main`, sin tocar el `status` de
> ninguna feature.

---

## 1 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T1** | `643fcc3` | `tests/test_f028_puertas.py`: la red de seguridad de las tres puertas, **en verde antes de tocar nada** |
| **T2** | `d9c4b51` | `domain/models/estado.py`: `EstadoParte`, `DecisionEstado`, `SituacionParte`, `ESTADOS_DE_CIERRE_EN_FIRME`, `LIMITE_MOTIVO` |
| **T3** | `62ecaa1` | `estado_de_la_maquina` y `estado_del_parte` — la derivación de `design.md` §3 |
| **T4** | `6308bbc` | `ParteCerrado` y `CambioDeEstadoInvalido` en `domain/models/errores.py` |
| — | `dc10a6c` | Dos tests más, de los dos supervivientes de la campaña de mutación |

**Nada de producción fuera del dominio se ha tocado.** No hay ni una línea
nueva en `application/`, `infrastructure/`, `interface_adapters/`,
`function_app.py` ni en el front. Las tres puertas siguen funcionando
exactamente como las dejó F-026.

---

## 2 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/domain/models/estado.py` | El estado del parte y su derivación. **Dominio puro** (356 líneas, casi todas de docstring) |
| `services/postventa-api/tests/test_f028_puertas.py` | Bloque 0: los control-negativo de las tres puertas (16 casos) |
| `services/postventa-api/tests/test_f028_estado_dominio.py` | El dominio del estado, caso a caso (40 casos) |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/errores.py` | Dos errores nuevos al final y un párrafo en el inventario de la cabecera. **Ni una línea de las anteriores tocada** |
| `specs/F-028-estado-del-parte/tasks.md` | T1–T4 marcadas `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff --stat ed46181..HEAD`: en el diff **no aparece**
`domain/models/validacion.py`, ni `sql/04_validaciones.sql` (regla dura 1), ni
`huella_de_veredicto` ni `_normalizar` —`domain/models/aprobacion.py` no está
en el diff en absoluto— (regla dura 2 y D9), ni `sql/10_aprobaciones.sql`
(regla dura 3), ni `infrastructure/sigrid/`, ni `infrastructure/sharepoint/`,
ni `azure-apps/`, ni `harness/features.json`.

---

## 3 · Decisiones de diseño tomadas al implementar

Ninguna reabre nada de D1–D9, y ninguna se aparta de `design.md`. Las que
había que tomar porque la spec no las fijaba al detalle:

1. **`ESTADOS_DE_CIERRE_EN_FIRME` se deriva de `EstadoCierre`**, no de dos
   cadenas escritas a mano: `(EstadoCierre.CERRADO.value,
   EstadoCierre.YA_CERRADA.value)`. El dueño de lo que puede haber en esa
   columna es el `CHECK` de `sql/06_cierres.sql`, y el test lo compara contra
   el **texto del DDL**, no contra el enumerado. Así quedan amarrados los tres
   sitios que dicen lo mismo.

2. **La derivación no confía en el tipo de lo que le llega**: `estado_cierre`
   se declara `str | None` y la comparación funciona igual con una cadena de
   la base o con un `EstadoCierre`, porque los dos enumerados heredan de `str`.
   Es lo mismo que ya hacía F-009.

3. **Los dos huecos de la huella van hacia el lado seguro** (`_aprueba_lo_que_hay`):
   sin veredicto guardado o sin huella apuntada, la aprobación **no cuenta**.
   La spec fija el caso «huella distinta» (R19) y no dice qué hacer cuando
   falta una de las dos mitades; se elige el lado cuyo error no cierra una
   incidencia en el ERP de producción, y queda escrito en la docstring.

4. **Las filas de máquina no deciden aunque se pasen por la puerta de la
   decisión humana.** `estado_del_parte` comprueba `decision.por_persona`
   antes de mirar nada. Es R26 escrito en el código y no solo en el contrato
   del repositorio: si mañana `consultar_situacion` se equivocara y devolviera
   la última fila en vez de la última fila humana, el estado seguiría siendo
   el correcto.

5. **Una decisión a `pendiente` o a `cerrado` cae a la máquina.** R10 lo
   prohíbe en el borde (400), pero la derivación no se apoya en el borde: si
   una fila con un estado imposible llegara —de una migración, de una semilla
   mal hecha— lo que pasa es que decide la máquina, no que el parte quede
   colgado en un estado que nadie pidió.

6. **Los dos errores nuevos se colocan por herencia, no por nombre.** El test
   compara su `__mro__` con el de `ParteNoApto` (familia 409) y
   `CuerpoDeArchivoInvalido` (familia 400), y comprueba que **ninguno** cuelga
   de `ErrorDePersistencia`, que los convertiría en un 503 «vuelve a
   intentarlo».

### Desviaciones respecto a la spec

**Ninguna.** Una precisión, que no cambia nada de lo escrito: `design.md` §8.1
anuncia `tests/test_f028_puertas.py` como fichero de las puertas (T1 y T11) y
`tests/test_f028_estado_dominio.py` como el del dominio. Los dos errores de T4
no tienen fichero propio en §8.1, así que sus cuatro tests van en el del
dominio, que es donde vive `errores.py`.

---

## 4 · Fase RED · las trazas, pegadas

Rigor `estandar` exige fase RED sobre los requisitos centrales. Aquí van las
tres, con el comando exacto. **El intérprete es el del servicio**
(`services/postventa-api/.venv`), no el del repositorio: el del repositorio no
tiene `pydantic` y falla al cargar `conftest.py`.

### T2 · antes de que existiera `domain/models/estado.py`

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_dominio.py -q

=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f028_estado_dominio.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f028_estado_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f028_estado_dominio.py:28: in <module>
    from domain.models.estado import (
E   ModuleNotFoundError: No module named 'domain.models.estado'
=========================== short test summary info ===========================
ERROR tests/test_f028_estado_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

Después de escribir el módulo: `13 passed in 0.17s`.

### T3 · antes de que existiera la derivación

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_dominio.py -q

=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f028_estado_dominio.py ______________
ImportError while importing test module '...\tests\test_f028_estado_dominio.py'.
Traceback:
tests\test_f028_estado_dominio.py:29: in <module>
    from domain.models.estado import (
E   ImportError: cannot import name 'estado_de_la_maquina' from 'domain.models.estado' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\estado.py)
=========================== short test summary info ===========================
ERROR tests/test_f028_estado_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.62s
```

Después de escribir `estado_de_la_maquina` y `estado_del_parte`:
`34 passed in 1.06s`.

### T4 · antes de que existieran los dos errores

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_dominio.py -q

=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f028_estado_dominio.py ______________
ImportError while importing test module '...\tests\test_f028_estado_dominio.py'.
Traceback:
tests\test_f028_estado_dominio.py:30: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'CambioDeEstadoInvalido' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f028_estado_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.38s
```

Después de añadirlos: `38 passed in 0.80s`.

### T1 no lleva fase RED, y es a propósito

T1 es un **control negativo**: lo que pide la tarea es lo contrario, que esté
**verde antes** de tocar nada, porque lo que vigila ya funciona hoy. Salió
verde a la primera —`16 passed in 0.80s`— con el árbol en el commit `ed46181`.
**Ninguna de las tres puertas está floja hoy.**

---

## 5 · Lo que T1 deja fijado, y por qué es lo que hay que mirar en los bloques 4 y 5

`tests/test_f028_puertas.py`, 16 casos, todos con dobles en memoria:

| Qué fija | Casos |
|---|---|
| **R33** · un parte no apto **sin decisión humana** no se archiva, no se adjunta y no se cierra | 6 (dos destinos × tres puertas) |
| Que el material del control negativo es **decidible a mano** | 1 |
| **R34** · «no hay veredicto» conserva su error propio en las tres puertas | 3 |
| **R33** · la decisión no entra **por parámetro** en ninguno de los tres pasos | 3 |
| **R33** · la decisión no entra **por el cuerpo** de los tres handlers | 3 |

Dos decisiones del control, que el reviewer tiene que poder juzgar:

- **Los seis casos afirman contra la biblioteca falsa, no contra un mock.** Lo
  que se comprueba es que **no hay ningún fichero arriba**, que no se creó ni
  la carpeta, que el ERP no recibió ni una lectura y que no se guardó ni una
  traza. Una puerta que se aflojara y llamara al puerto sin escribir seguiría
  siendo un fallo, y así se ve.
- **El control del cuerpo se hace sobre el árbol sintáctico, no sobre el texto
  crudo.** El primer intento miraba el fuente como cadena y se puso rojo en
  `adjuntar.py` y `cerrar.py` por dos **docstrings** —«`GraficoRechazadoPorLaPasarela`»
  y «rechaza y punto»— que no tienen nada que ver con la decisión. Lo que hay
  que vigilar no es lo que el módulo *cuenta*, es lo que *hace*: se recogen
  identificadores y literales del código, saltándose las docstrings. La lista
  de palabras del borde excluye `estado` con su motivo escrito
  (`estado_archivo` viaja en el cuerpo de `/api/cerrar` desde F-009).

**Cuando el bloque 4 retire el atajo del apto y el 5 la tabla de F-026, estos
16 casos tienen que seguir en verde sin tocarlos.** Si alguno se pone rojo y la
tentación es editarlo, eso es exactamente la puerta aflojada que el bloque 0
existía para detectar.

---

## 6 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2399 passed, 13 skipped** | `bash harness/init.sh`, servicio `api` |
| Tests ejecutados (arnés, raíz) | **62 passed** | `bash harness/init.sh` |
| De ellos, **nuevos de F-028** | **56** (16 de T1 + 40 del dominio) | `pytest tests/test_f028_*.py` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (59/59, umbral 80 %) | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados** | **11** | `python -m harness.mutacion --feature F-028` |
| **Supervivientes** | **0** | ídem, 2.ª campaña |
| **Timeouts** | **0** | ídem |
| **Tiempo de la suite** | **46,99 s** (`api`) · 4,34 s (raíz) | la propia suite |
| **Tiempo de la campaña** | 120,6 s con 8 workers | `progress/mutacion_F-028.md` |

### Los dos supervivientes de la primera campaña, y qué se hizo con cada uno

La primera campaña dio **9 muertos y 2 supervivientes**. Los dos eran **huecos
reales**, no mutantes equivalentes, y los dos se han cerrado con un test (no
con una justificación):

| Superviviente | Por qué ningún test lo cazaba | Qué se ha hecho |
|---|---|---|
| `estado.py:354` · `if validacion is None **or** decision.huella_veredicto is None` → `and` | Faltaba el caso de una decisión **con huella pero sin veredicto guardado**. Con el `and`, ese caso ya no cortaba y acababa llamando a `huella_de_veredicto(None)`. No es teórico: la situación se lee del repositorio y el veredicto viene del contexto, así que las dos mitades pueden llegar desparejadas | `test_f028_r19_una_aprobacion_sin_veredicto_guardado_no_cuenta` |
| `estado.py:187` · `SituacionParte` con `frozen=True` → `frozen=False` | Se probaba que `DecisionEstado` es inmutable, pero no `SituacionParte`. Importa: viaja del repositorio a `ContextoParte` y de ahí a las tres puertas; si un paso pudiera reescribirla, daría igual haberla leído del almacén, que es lo que exige R33 | `test_f028_r33_la_situacion_leida_del_almacen_es_inmutable` |

Segunda campaña, con los dos tests dentro: **11 mutantes, 11 muertos, 0
supervivientes**. Informe completo en `progress/mutacion_F-028.md`.

> Nota de método: la campaña paralela crea sus worktrees desde `HEAD`, así que
> se aborta si el árbol tiene cambios sin commitear. Los dos tests se
> commitearon antes de relanzarla (`dc10a6c`).

### Ruff

`python -m ruff check` sobre los cuatro ficheros tocados: **All checks passed**.
Los 60 avisos que reporta `init.sh` son deuda previa del repositorio y no
crecen con este trabajo.

---

## 7 · Verificaciones MANUAL pendientes

**Ninguna de este bloque.** Todo lo entregado es dominio puro y se prueba sin
red, sin BBDD y sin IA. Las verificaciones manuales de la feature son las de
T27 (bloque 10) y siguen intactas: la base real y el ERP no se han tocado.

---

## 8 · Por dónde sigue · el encargo del bloque 2

**Todo lo del bloque 1 está cerrado.** El siguiente encargo es el **bloque 2 ·
La persistencia**, T5, T6 y T7 de `tasks.md`:

- **T5** · `sql/11_historico_estado.sql` con la tabla append-only, su índice y
  la semilla de `design.md` §8.4, más `tests/test_f028_ddl_historico.py`. Ojo a
  la **regla dura 3**: `sql/10_aprobaciones.sql` no se reescribe ni se borra, y
  hay que comprobarlo con un test.
- **T6** · `sentencias.py` (`insert_decision_estado`, `select_situacion_estado`,
  `select_estado_cierre`) y `mapeo.fila_a_decision_estado`, con
  `tests/test_f028_persistencia.py`.
- **T7** · el puerto y `repositorio_pg.py`: `consultar_situacion`,
  `registrar_decision` y `consultar_estado_cierre`. **Todavía no se retira nada
  de F-026.**

Lo que el bloque 2 se encuentra ya hecho y puede usar tal cual:
`DecisionEstado` (los siete campos son exactamente las siete columnas de la
tabla de §8.4, en el mismo orden conceptual), `SituacionParte` (las tres cosas
que tiene que devolver `consultar_situacion`), `EstadoParte` (contra el que se
compara el `CHECK` del DDL nuevo, como pide T5) y `LIMITE_MOTIVO`.

Y un apunte para quien escriba T7: `SituacionParte.ultimo_estado_registrado`
es `EstadoParte | None`, mientras que `estado_cierre` es `str | None` —viene
crudo de la columna de `cierres` y la derivación lo compara por valor—.

---

## 9 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde.
- Árbol limpio, **5 commits** sobre `ed46181`, todos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
