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
| — | `af4f71d` | Dos tests más, de los dos supervivientes de la campaña de mutación |

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
> commitearon antes de relanzarla (`af4f71d`).

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
- Árbol limpio, **6 commits** sobre `ed46181`, todos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.

---
---

# F-028 · Estado del parte — informe del implementer · bloque 2

> Encargo: **T5, T6 y T7** de `specs/F-028-estado-del-parte/tasks.md`, la
> persistencia. Parada obligada al terminar el bloque 2. **No se ha entrado en
> el bloque 3.**
>
> Rama `feature/F-028-estado-del-parte`, desde `58fdf7e`. Rigor **`estandar`**:
> fase RED, puerta de cobertura, campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature.

---

## 10 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T5** | `fc9efb1` | `sql/11_historico_estado.sql`: la tabla append-only, su índice y la semilla; y la **sexta forma** de la guarda del DDL, sin la cual no arrancaría |
| **T6** | `2de1289` | `insert_decision_estado`, `select_situacion_estado`, `select_estado_cierre` y `mapeo.fila_a_decision_estado` |
| **T7** | `f20f1ce` | El puerto y `repositorio_pg`: `consultar_situacion`, `registrar_decision`, `consultar_estado_cierre`; y el doble en memoria al día |

**Nada del pipeline, del borde ni del front se ha tocado.** No hay una línea
nueva en `application/`, en `interface_adapters/`, en `function_app.py` ni en
`services/postventa-front/`. Las tres puertas siguen funcionando exactamente
como las dejó F-026, y `postventa.aprobaciones` se sigue escribiendo y leyendo
igual que ayer: **retirar nada de F-026 es T15**, y T7 lo dice expresamente.

---

## 11 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/infrastructure/persistencia/sql/11_historico_estado.sql` | La tabla `postventa.historico_estado`, su índice y la semilla de `design.md` §8.4 |
| `services/postventa-api/tests/test_f028_ddl_historico.py` | El **texto** del DDL, auditado (50 casos) |
| `services/postventa-api/tests/test_f028_persistencia.py` | Sentencias, mapeo y adaptador, con dobles (27 casos) |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `infrastructure/persistencia/ddl.py` | La **sexta forma** de sentencia: la semilla. Ver §13.1 — es la decisión del bloque |
| `infrastructure/persistencia/sentencias.py` | Tres sentencias nuevas, `_COLUMNAS_HISTORICO`, `_ORDEN_HISTORICO` y los dos marcadores de origen. **Ni una línea de las anteriores tocada** |
| `infrastructure/persistencia/mapeo.py` | `fila_a_decision_estado` al final, más su import y su `__all__` |
| `infrastructure/persistencia/repositorio_pg.py` | Una sección nueva con los tres métodos. Ninguno de los existentes cambia |
| `domain/ports/persistencia.py` | Los tres métodos nuevos en `RepositorioPartesPort`. **No se retira ninguno** |
| `tests/utiles_pg.py` | `RepositorioEnMemoria` cumple el puerto ampliado (ver §13.4) |
| `tests/test_f005_ddl_idempotente_texto.py` | Dos aserciones: el undécimo fichero y `NOT EXISTS` como tercera forma de idempotencia |
| `tests/test_f026_ddl_aprobaciones.py` | Un test: `10_aprobaciones.sql` deja de ser **el último** |
| `specs/F-028-estado-del-parte/tasks.md` | T5–T7 marcadas `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff --stat 58fdf7e..HEAD`: en el diff **no aparece**
`domain/models/validacion.py`, ni `sql/04_validaciones.sql` (regla dura 1), ni
`domain/models/aprobacion.py` —o sea, ni `huella_de_veredicto` ni
`_normalizar`— (regla dura 2 y D9), ni **`sql/10_aprobaciones.sql`** (regla
dura 3, y además hay un test que compara su `sha256`), ni
`infrastructure/sigrid/`, ni `infrastructure/sharepoint/`, ni `azure-apps/`, ni
`harness/features.json`.

---

## 12 · Fase RED · las trazas, pegadas

El intérprete es el del servicio (`services/postventa-api/.venv`): el del
repositorio no tiene `pydantic` y falla al cargar `conftest.py`.

### T5 · antes de que existiera `sql/11_historico_estado.sql`

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_ddl_historico.py -q

_______ test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo ________
        nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

>       assert nombres[-1] == FICHERO
E       AssertionError: assert '10_aprobaciones.sql' == '11_historico_estado.sql'
E         - 11_historico_estado.sql
E         + 10_aprobaciones.sql

tests\test_f028_ddl_historico.py:144: AssertionError
_______________ test_f028_la_guarda_acepta_las_tres_sentencias ________________
>       for sentencia in _sentencias()
tests\test_f028_ddl_historico.py:103: in _sentencias
    return ddl.sentencias(_texto())
tests\test_f028_ddl_historico.py:98: in _texto
    return _ruta().read_text(encoding="utf-8")
...\Lib\pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
E   FileNotFoundError: [Errno 2] No such file or directory:
E   '...\\infrastructure\\persistencia\\sql\\11_historico_estado.sql'

38 failed, 12 passed in 3.38s
```

Después de escribir el `.sql` y la sexta forma de la guarda: `50 passed in 0.59s`.

Los 12 que ya pasaban en rojo son, uno a uno, **los que no dependen del fichero
nuevo**: el `sha256` del congelado, la tabla de `aprobaciones` en el DDL y los
control negativos de la guarda que ya se rechazaban antes (`UPDATE`, `DELETE`,
`TRUNCATE`, `DROP TABLE`, y los `INSERT` mal formados, que en rojo caían por «no
tiene ninguna de las formas reconocidas» en vez de por su motivo propio). Que
esos doce estuvieran verdes desde el principio es lo correcto: son la parte del
fichero que vigila lo que **ya** funcionaba.

### T6 · antes de que existieran las sentencias y el mapeo

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_persistencia.py -q

=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f028_persistencia.py _______________
ImportError while importing test module '...\tests\test_f028_persistencia.py'.
Traceback:
tests\test_f028_persistencia.py:43: in <module>
    from infrastructure.persistencia.mapeo import fila_a_decision_estado
E   ImportError: cannot import name 'fila_a_decision_estado' from
E   'infrastructure.persistencia.mapeo' (...\infrastructure\persistencia\mapeo.py)
=========================== short test summary info ===========================
ERROR tests/test_f028_persistencia.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.60s
```

Después de escribir `sentencias.py` y `mapeo.py`: los 16 casos de T6 en verde y
**los 11 de T7 en rojo**, que es la fase RED de T7.

### T7 · antes de que existieran el puerto y el adaptador

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_persistencia.py -q

        with caplog.at_level("INFO"):
>           repositorio.registrar_decision(decision=_decision())
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           AttributeError: 'RepositorioPostgres' object has no attribute
E           'registrar_decision'

tests\test_f028_persistencia.py:566: AttributeError
=========================== short test summary info ===========================
FAILED tests/test_f028_persistencia.py::test_f028_registrar_una_decision_ejecuta_el_insert
FAILED tests/test_f028_persistencia.py::test_f028_la_situacion_de_un_parte_sin_ninguna_fila_viene_vacia
FAILED tests/test_f028_persistencia.py::test_f028_la_situacion_se_resuelve_con_dos_consultas
FAILED tests/test_f028_persistencia.py::test_f028_la_situacion_trae_la_ultima_decision_humana
FAILED tests/test_f028_persistencia.py::test_f028_r26_una_fila_de_maquina_no_se_confunde_con_una_decision
FAILED tests/test_f028_persistencia.py::test_f028_cuando_la_ultima_fila_es_la_humana_vienen_las_dos_mitades
FAILED tests/test_f028_persistencia.py::test_f028_r18_la_situacion_trae_el_estado_de_la_traza_de_cierre
FAILED tests/test_f028_persistencia.py::test_f028_el_estado_de_cierre_se_puede_consultar_por_su_cuenta
FAILED tests/test_f028_persistencia.py::test_f028_r52_registrar_una_decision_no_saca_el_motivo_ni_el_oid
FAILED tests/test_f028_persistencia.py::test_f028_r52_leer_la_situacion_tampoco_los_saca
FAILED tests/test_f028_persistencia.py::test_f028_el_log_si_registra_lo_que_hace_falta_para_operar
11 failed, 16 passed in 0.72s
```

Después del puerto, el adaptador y el doble: `27 passed in 0.49s`.

---

## 13 · Decisiones de diseño, y la que hay que juzgar

### 13.1 · La guarda del DDL aprende una **sexta forma**, y es lo que más hay que mirar de este bloque

**El problema, medido.** `infrastructure/persistencia/ddl.py` reconocía
**cinco** formas de sentencia —`CREATE SCHEMA`, `CREATE TABLE`, `CREATE INDEX`,
`CREATE VIEW`, `ALTER TABLE ADD COLUMN`— y rechaza todo lo demás por diseño
(«lo que no se reconoce, no pasa»). La semilla de `design.md` §8.4 es un
`INSERT … SELECT … WHERE NOT EXISTS`, **la primera sentencia de datos de todo
el DDL del proyecto** (comprobado: `grep -rn INSERT sql/` no devolvía nada). Sin
enseñarle esa forma, `cargar_ddl` levanta `DdlInseguro` y **el servicio no
arranca**: valida antes de abrir la conexión.

**Por qué se implementa y no se marca `blocked`.** No hay ambigüedad que
resolver: `design.md` §8.4 escribe la semilla entera, dice que «se ejecuta con
el resto del DDL al arrancar, antes de atender ninguna petición» y dice que su
idempotencia es el `NOT EXISTS`. Lo único que faltaba es que §8.2 no listó
`ddl.py` entre los ficheros a modificar. Es una omisión de la lista, no una
decisión sin tomar: la alternativa —no aplicar la semilla— contradice §4, §8.4
y la verificación 2 de T27.

**Lo que se ha abierto, exactamente.** Una forma nueva, `_validar_insert_semilla`,
con cuatro condiciones que se comprueban **antes** de aceptarla:

1. **`SELECT` obligatorio** — un `INSERT … VALUES` es datos escritos a mano
   dentro del DDL, no una semilla;
2. **`NOT EXISTS` obligatorio** — sin él la sentencia no es idempotente y cada
   arranque de la Function duplicaría filas;
3. **`ON CONFLICT` prohibido** — R21 escrito en la guarda: el DDL de este
   proyecto no vuelve a admitir una escritura que pise filas;
4. **todo cualificado con el esquema propio**, lo que se escribe (`INTO`) y
   **también lo que se lee** (`FROM`, `JOIN`): en un servidor compartido con la
   producción de albaranes, leer la base de otro cruza la misma frontera.

**Lo que NO se ha abierto**, y hay control negativo de cada uno:
`UPDATE`, `DELETE FROM`, `TRUNCATE` y `DROP TABLE` siguen cayendo en
«la sentencia no tiene ninguna de las formas reconocidas». Y todo lo anterior
de la guarda sigue aplicándose a la semilla igual que a las otras cinco formas:
`VERBOS_PROHIBIDOS` (los quince de ámbito de servidor), `public.` y los tipos
binarios.

**Lo que el reviewer tiene que juzgar** es si esa apertura es la mínima. Los
siete control negativos están en `tests/test_f028_ddl_historico.py`, en la
sección final.

### 13.2 · El `UNION ALL` lleva un **marcador de origen** en cada rama

`design.md` §8.5 dice «un `UNION ALL` de dos `SELECT … LIMIT 1`» y no dice cómo
se distinguen las dos filas al leerlas. Hace falta distinguirlas, porque **las
dos ramas pueden devolver la misma fila**: cuando el último cambio del parte lo
decidió una persona, su fila es a la vez la última humana y la última de todas.
Sin marcador, «una decisión humana reciente» y «una decisión humana antigua más
una constancia reciente» llegarían como dos filas indistinguibles.

Se añade una primera columna literal, `ORIGEN_DECISION_HUMANA` /
`ORIGEN_ULTIMO_CAMBIO`, constantes públicas de `sentencias.py`. Son parte de la
**forma** de la consulta, como el nombre de la tabla, no un valor que venga de
fuera: por eso se pegan al texto y no viajan como parámetro, y eso no rompe la
regla del módulo («ningún valor se interpola nunca»). El adaptador compara
contra la constante, no contra una cadena escrita otra vez.

La alternativa —adivinarlo comparando campos de las dos filas— se descartó: dos
filas iguales campo a campo pueden ser la misma fila o dos filas distintas
escritas en el mismo instante, y ahí ya no hay forma de saberlo.

### 13.3 · `consultar_estado_cierre` existe aparte **y** lo usa `consultar_situacion`

`tasks.md` T7 pide los tres métodos; `design.md` §8.5 solo enseña dos en el
puerto y dice que el adaptador resuelve la situación «con dos consultas». Se
implementan los tres y `consultar_situacion` llama al tercero, en vez de
duplicar el `SELECT`. Consecuencia declarada: **el log lo escribe
`consultar_situacion` y no `consultar_estado_cierre`**, para no escribir dos
líneas por parte y por paso en el camino que se recorre 66 veces por tanda.

El estado de cierre vuelve **en crudo**, como `str | None`, y no como
`EstadoCierre`. Es lo que dijo el bloque 1 en su §8 y lo que espera la
derivación: el dueño de lo que puede haber en esa columna es el `CHECK` de
`sql/06_cierres.sql`, y convertirlo aquí obligaría a decidir qué hacer con un
valor que el `Enum` no conozca.

### 13.4 · El doble en memoria **acumula** las decisiones

`RepositorioEnMemoria.decisiones` es una lista y no un diccionario por
`hash_parte`. Es deliberado y es la mitad de R21: un doble que guardara la
última decisión por parte **no podría hacer fallar** a un código que pisara
filas, que es exactamente el defecto de `postventa.aprobaciones` del que nace
la feature. El bloque 3 se apoya en eso para comprobar que un reproceso que no
cambia nada no escribe ninguna fila.

Y `consultar_situacion` devuelve `SituacionParte()` —los tres huecos vacíos— y
no `None` cuando el test no prepara nada: es lo que hace el adaptador de verdad.

### 13.5 · Congelar `10_aprobaciones.sql` se comprueba con su `sha256`

Regla dura 3 dice «sin un solo cambio» y T5 pide verificarlo. Un test de texto
que buscara fragmentos dejaría pasar un reordenado o un comentario nuevo. Lo que
hay es el `sha256` del fichero —con los finales de línea normalizados a `\n`,
para que la comprobación sea del contenido y no de cómo git lo saque de la
caja— escrito literal:
`2764945a4cf4881147ab8bb1201736aee9b04d938ba62fdd9914d5f5bc22d3f7`, el del
commit `f1e5718` que lo creó. La docstring del test dice que **si se pone rojo,
la respuesta correcta no es actualizar la huella**.

### Desviaciones respecto a la spec

**Una, y está en §13.1**: `design.md` §8.2 no lista `ddl.py` entre los ficheros
a modificar, y se ha modificado. Sin ese cambio la semilla de §8.4 no se puede
aplicar y el servicio no arranca. Todo lo demás sigue la spec al pie de la letra.

---

## 14 · Los tres tests de antes que han cambiado, y por qué

Son tres, todos por la **misma causa** —hay un undécimo fichero de DDL—, y
ninguno afloja lo que vigilaba:

| Test | Qué cambia | Por qué |
|---|---|---|
| `test_f005_r1_se_aplican_todos_los_ficheros_en_orden` | Una línea más en la lista escrita a mano | Es justo para lo que existe: añadir un `.sql` **tiene** que obligar a venir aquí a declararlo |
| `test_f005_r3_todas_las_sentencias_reales_son_idempotentes` | Admite `NOT EXISTS` además de `IF NOT EXISTS` y `OR REPLACE` | Las tres dicen lo mismo: no hagas nada si ya está hecho. Y no exime a la semilla de nada: `ddl.validar` la exige por su lado, con su control negativo propio |
| `test_f026_r16_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo` → `…_en_su_sitio` | Deja de exigir que `10_aprobaciones.sql` sea **el último** y gana que va **antes** que el histórico | La semilla lee de esa tabla, así que el orden nuevo es una dependencia real. Lo que le importaba a F-026 —que el fichero existe, sigue la convención y va detrás de `03_partes`— se conserva |

**Ningún test de F-026 sobre la huella se ha tocado**, y los 16 control
negativos de `tests/test_f028_puertas.py` (bloque 0) siguen en verde **sin
tocarlos**, que es lo que tenían que hacer.

---

## 15 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2476 passed, 13 skipped** | `bash harness/init.sh`, servicio `api` |
| Tests del front | en verde por caché (árbol del front sin cambios) | `bash harness/init.sh` |
| De ellos, **nuevos de este bloque** | **77** (50 del DDL + 27 de la persistencia) | `pytest tests/test_f028_ddl_historico.py tests/test_f028_persistencia.py` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (98/98, umbral 80 %) | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados** | **18** | `python -m harness.mutacion --feature F-028` |
| **Supervivientes** | **0** | ídem |
| **Timeouts** | **0** | ídem |
| **Tiempo de la suite** | **90,8 s** (`api`) | la propia suite |
| **Tiempo de la campaña** | **257,7 s** con 8 workers | `progress/mutacion_F-028.md` |

### Los supervivientes, y qué se hace con cada uno

**Ninguno.** 18 mutantes, 18 muertos. De los 18, **6 son del código nuevo de
este bloque** y los 12 restantes, del dominio del bloque 1 (siguen muertos):

| Mutante de este bloque | Quién lo caza |
|---|---|
| `ddl.py:351` · `if not re.search(SELECT)` → sin el `not` | `test_f028_la_guarda_acepta_la_semilla_del_diseno` |
| `ddl.py:357` · `if not re.search(NOT EXISTS)` → sin el `not` | ídem |
| `repositorio_pg.py:317` · `origen == ORIGEN_DECISION_HUMANA` → `!=` | `test_f028_la_situacion_trae_la_ultima_decision_humana` |
| `repositorio_pg.py:388` · `if not filas` → `if filas` | `test_f028_el_estado_de_cierre_se_puede_consultar_por_su_cuenta` |
| `repositorio_pg.py:390` · `filas[0][0]` → `filas[1][0]` y → `filas[0][1]` | ídem |
| `sentencias.py:627` · `['%s'] * len(...)` → `//` | `test_f028_r22_el_insert_escribe_las_siete_columnas_de_la_fila` |

Informe completo en `progress/mutacion_F-028.md`.

> Un apunte que se corrigió por el camino: la primera pasada de la puerta de
> cobertura dio **99,0 % (99/100)**. La línea suelta era una rama **inalcanzable**
> que había escrito de más en `_validar_insert_semilla` —«la semilla no nombra
> ninguna tabla cualificada»—: una sentencia que llega ahí empieza siempre por
> `INSERT INTO`, así que el patrón siempre encuentra al menos un objeto. Se
> **retiró la rama muerta** en vez de escribirle un test que no podía existir, y
> la puerta pasó a 100 % (98/98).

### Ruff

`python -m ruff check` sobre los cuatro ficheros de producción tocados:
**All checks passed**. Los tres avisos `I001` de los ficheros de test y los dos
`PYI034` de `utiles_pg.py` son deuda previa del repositorio —los ficheros
vecinos de F-005 y F-026 los tienen igual— y **no crecen** con este trabajo: el
fichero nuevo sigue el mismo orden de imports que sus vecinos a propósito.

---

## 16 · Verificaciones MANUAL pendientes

**Ninguna nueva.** Las de este bloque son las que ya estaban escritas en T27
(bloque 10) y siguen intactas, porque necesitan la base real:

1. **el DDL nuevo aplicado dos veces seguidas no falla, y la semilla no
   duplica** — aquí solo se comprueba que el `NOT EXISTS` está escrito y que la
   guarda lo exige;
2. **la aprobación que ya había en `postventa.aprobaciones` aparece sembrada y
   el parte sigue saliendo `aprobado`** — la semilla copia `aprobado_por`, que
   es lo que la hace contar como decisión humana;
3. **aprobar → rechazar → aprobar deja tres filas** — que el `INSERT` no pise
   está probado sobre el SQL; que la base acumule, no.

La base real y el ERP **no se han tocado**: todo lo de este bloque se prueba con
el doble de `tests/utiles_pg.py` y con el texto del `.sql`, sin red y sin BBDD.

---

## 17 · Por dónde sigue · el encargo del bloque 3

**Todo el bloque 2 está cerrado.** El siguiente es el **bloque 3 · La
constancia: que el histórico cuente la película**, T8 y T9:

- **T8** · `paso_persistencia`: tras guardar la validación, calcular el estado
  derivado y **añadir la fila solo si difiere del último registrado**
  (`design.md` §4). Los casos van en `tests/test_f028_persistencia.py`, que ya
  existe.
- **T9** · `paso_cierre`: la fila `→ cerrado` **después** de que el cierre
  conste, y ninguna si el cierre falla.

Lo que el bloque 3 se encuentra ya hecho y puede usar tal cual:

- `repositorio.consultar_situacion(hash_parte=…)` devuelve `SituacionParte` con
  los tres huecos, y `ultimo_estado_registrado` es exactamente lo que hay que
  comparar contra el estado derivado para decidir si se escribe fila;
- `repositorio.registrar_decision(decision=…)` escribe la fila y **no pisa
  ninguna**; para una fila de constancia, `decidido_por=None` y `motivo=None`
  (R24);
- `estado_de_la_maquina(validacion)` y `estado_del_parte(...)` del bloque 1 son
  la derivación, y no hay que reescribirla en ningún sitio (R17);
- `RepositorioEnMemoria` ya tiene `decisiones` (lista, acumula), `situacion`,
  `estado_cierre` y `situaciones_consultadas`.

Dos apuntes para quien lo coja:

- **`registrar_decision` no es idempotente, y es a propósito.** Quien evita la
  fila repetida es la **regla de constancia** de T8 —solo se escribe si el
  estado derivado cambió—, no la base. Si T8 se salta esa comprobación, el
  autoguardado de F-026 llena la tabla, y eso no lo caza ningún `ON CONFLICT`
  porque aquí no hay ninguno.
- **El bloque 3 sigue sin tocar las tres puertas.** Eso es el bloque 4, y es
  donde `tests/test_f028_puertas.py` tiene que seguir en verde sin que nadie lo
  edite.

---

## 18 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las líneas cambiadas.
- Árbol limpio, **3 commits** sobre `58fdf7e` (`fc9efb1`, `2de1289`, `f20f1ce`),
  todos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
