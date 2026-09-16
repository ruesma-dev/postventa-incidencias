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

---
---

# F-028 · Estado del parte — informe del implementer · bloque 3

> Encargo: **T8 y T9** de `specs/F-028-estado-del-parte/tasks.md`, la
> constancia en los pipelines. Parada obligada al terminar el bloque 3. **No se
> ha entrado en el bloque 4.**
>
> Rama `feature/F-028-estado-del-parte`, desde `7cab1cb`. Rigor **`estandar`**:
> fase RED, puerta de cobertura, campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature.

---

## 19 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T8** | `4c0934a` | `paso_persistencia` apunta el estado del parte tras guardar el veredicto, **solo si cambió**; la regla vive en `application/pipelines/constancia.py` |
| **T9** | `117421e` | `paso_cierre` apunta `→ cerrado` **después** de que el cierre conste; un cierre fallido no la escribe, y un fallo al apuntarla **no se lleva por delante el cierre** |

**Las tres puertas no se han tocado.** `_exigir_admitido` sigue exactamente
como lo dejó F-026 en los tres pasos, el atajo del apto sigue ahí y
`consultar_aprobacion` se sigue leyendo igual: eso es el bloque 4.
`tests/test_f028_puertas.py` sigue en verde **sin editarlo** — 16 pasados—, que
es lo que este bloque tenía que demostrar además de lo suyo.

Tampoco se ha tocado el front, ni `infrastructure/sigrid/`, ni
`infrastructure/sharepoint/`, ni `azure-apps/`, ni `harness/features.json`.

---

## 20 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/application/pipelines/constancia.py` | La **regla de constancia** de `design.md` §4, una sola vez: `anotar_estado` |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `application/pipelines/paso_persistencia.py` | `_dejar_constancia_del_estado` detrás de `guardar_validacion`, y el párrafo de la cabecera que dice por qué |
| `application/pipelines/paso_cierre.py` | `_anotar_que_el_parte_queda_cerrado`, llamado desde `_escribir` y desde `_resolver_ya_cerrada`; paso 8 en la lista de la docstring |
| `interface_adapters/api/parte.py` | `AnotaLosResultados` delega `consultar_situacion` y `registrar_decision`. Ver §22.2 — **sin esto, `POST /api/parte` revienta** |
| `tests/test_f028_persistencia.py` | 18 casos nuevos: 10 de T8 y 8 de T9, con dos dobles locales |
| `specs/F-028-estado-del-parte/tasks.md` | T8 y T9 marcadas `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff --stat 7cab1cb..HEAD`: en el diff **no aparece**
`domain/models/validacion.py`, ni `sql/04_validaciones.sql` (regla dura 1), ni
`domain/models/aprobacion.py` —o sea, ni `huella_de_veredicto` ni
`_normalizar`— (regla dura 2 y D9), ni `sql/10_aprobaciones.sql` ni
`sql/11_historico_estado.sql` (regla dura 3), ni `infrastructure/sigrid/`, ni
`infrastructure/sharepoint/`, ni `tests/test_f028_puertas.py`, ni
`azure-apps/`, ni `harness/features.json`. Y **no se ha retirado nada de
F-026**: `Aprobacion`, `admite_circuito`, `guardar_aprobacion`,
`consultar_aprobacion` y `/api/aprobar` siguen vivos y en uso.

---

## 21 · Fase RED · las trazas, pegadas

El intérprete es el del servicio (`services/postventa-api/.venv`): el del
repositorio no tiene `pydantic` y falla al cargar `conftest.py`.

### T8 · antes de que `paso_persistencia` apuntara nada

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_persistencia.py -q

...........................FFF.F..FFFFF...F.F                            [100%]
================================== FAILURES ===================================
__ test_f028_r23_un_parte_apto_nace_aprobado_y_consta_que_lo_dijo_la_maquina __

    def test_f028_r23_un_parte_apto_nace_aprobado_y_consta_que_lo_dijo_la_maquina():
        repositorio = RepositorioEnMemoria()

        _guardar(repositorio, _veredicto(apto=True))

>       assert len(repositorio.decisiones) == 1
E       assert 0 == 1
E        +  where 0 = len([])
E        +    where [] = <tests.utiles_pg.RepositorioEnMemoria object at 0x...>.decisiones

tests\test_f028_persistencia.py:714: AssertionError
...
11 failed, 34 passed in 1.66s
```

Después de escribir `constancia.py`, el paso y la delegación del envoltorio:
los 11 en verde, y la suite entera del servicio también.

### T9 · antes de que `paso_cierre` apuntara nada

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f028_persistencia.py -q

.....................................FF...F.F                            [100%]
================================== FAILURES ===================================
______________ test_f028_el_cierre_deja_su_fila_en_el_historico _______________

    def test_f028_el_cierre_deja_su_fila_en_el_historico():
        repositorio = RepositorioEnMemoria(
            traza_grafico=GRAFICO_ADJUNTADO,
            situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
        )

        _cerrar(repositorio)

>       assert len(repositorio.decisiones) == 1
E       assert 0 == 1
E        +  where 0 = len([])
E        +    where [] = <tests.utiles_pg.RepositorioEnMemoria object at 0x...>.decisiones

tests\test_f028_persistencia.py:990: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f028_persistencia.py::test_f028_el_cierre_deja_su_fila_en_el_historico
FAILED tests/test_f028_persistencia.py::test_f028_la_fila_cerrado_se_escribe_despues_de_que_el_cierre_conste
FAILED tests/test_f028_persistencia.py::test_f028_r18_una_reclamacion_ya_cerrada_tambien_deja_su_fila
FAILED tests/test_f028_persistencia.py::test_f028_si_la_constancia_falla_el_cierre_sigue_siendo_un_cierre
4 failed, 41 passed in 1.57s
```

Después de `_anotar_que_el_parte_queda_cerrado` y sus dos llamadas:
`45 passed in 1.07s`.

### Los siete casos que ya pasaban en rojo, y por qué es lo correcto

De los 18 casos nuevos, siete estaban verdes desde el principio, y son **todos
los control negativo**: «un reproceso que no cambia nada no escribe fila», «sin
veredicto no se estrena histórico», «el dry-run no escribe», «un cierre fallido
no escribe», «un cierre que no cuadra tampoco», «no se repite la fila si ya
constaba cerrado» y «reprocesar un parte aprobado a mano no lo degrada». Antes
de T8 **nadie escribía ninguna fila**, así que afirmar que no se escribe fila
salía gratis. Su valor no está en la fase RED sino en la de después: son los
que se ponen rojos si mañana la condición desaparece, y de eso hay prueba en
§23.

**T8 y T9 sí llevan fase RED de verdad** en los once y cuatro casos positivos,
que son los que dicen lo que el código tiene que hacer.

---

## 22 · Decisiones de diseño, y las dos que hay que juzgar

### 22.1 · La regla vive en un módulo propio, y §8.2 no lo lista

**Es la única desviación del bloque.** `design.md` §8.2 lista
`paso_persistencia.py` y `paso_cierre.py` como los ficheros a modificar, y no
anuncia un fichero nuevo. Se ha creado
`application/pipelines/constancia.py` con `anotar_estado`, que es la regla de
§4 escrita una vez: *si el estado derivado no es el de la última fila, se añade
una fila*.

**Por qué, y no es una preferencia de estilo.** La aplican los **dos** pasos.
Escribirla dos veces es lo que `confianza.py` (F-004) ya razonó en su cabecera
y que aquí vale igual de literalmente: dos copias divergen el día que alguien
corrija una sola, y **en una campaña de mutación cada copia se cuenta aparte**,
con lo que la segunda se queda sin tests que la maten. Hay además un precedente
exacto en este mismo repositorio —`confianza.py` nació dentro de
`paso_extraccion.py` y se sacó cuando la lectura de la firma necesitó la misma
regla—, así que no se está inventando una capa nueva: se está usando la que ya
existe para esto.

**Lo que el módulo NO decide**, y es la mitad del diseño: la política de
errores. `anotar_estado` deja subir lo que levante el repositorio, y cada paso
hace con ese fallo lo contrario que el otro (§22.3). Meter la política dentro
habría obligado a un parámetro booleano que es justo donde se esconden los
fallos de este tipo.

### 22.2 · `AnotaLosResultados` tenía un agujero que T8 destapó

`interface_adapters/api/parte.py` envuelve el repositorio para anotar qué
devolvió cada guardado, y su docstring promete: «implementa
`RepositorioPartesPort` entero delegando: si mañana el paso llamara a otra
operación, este envoltorio no se interpone». **No era verdad.** En cuanto
`paso_persistencia` llamó a `consultar_situacion`, la suite dio:

```
E       AttributeError: 'AnotaLosResultados' object has no attribute
E       'consultar_situacion'. Did you mean: 'consultar_aprobacion'?
```

Lo caza `tests/test_f019_logs_sin_datos_personales.py`, que no es de esta
feature. Se han añadido las **dos** operaciones que el paso usa de verdad
—`consultar_situacion` y `registrar_decision`—, y solo esas dos: una
delegación que nadie ejercita es una línea sin test y la puerta de cobertura la
cantaría.

> Apunte para el reviewer, porque es deuda previa y no mía: al envoltorio le
> siguen faltando `guardar_grafico`, `consultar_grafico` y
> `consultar_estado_cierre`. Hoy es inocuo —`/api/parte` y `/api/aprobar` no
> llegan al paso del gráfico— pero la docstring sigue prometiendo algo que el
> código no cumple. No se arregla aquí porque no es de este bloque.

### 22.3 · Un fallo al apuntar la constancia **no puede llevarse por delante un cierre que sí ocurrió**

Es el punto que el encargo pedía explicar, y los dos pasos hacen lo contrario a
propósito:

| | `paso_persistencia` | `paso_cierre` |
|---|---|---|
| Qué se ha escrito fuera cuando falla | **nada** | la incidencia **está cerrada en el ERP de producción** y su `TrazaCierre` guardada |
| Qué hace | deja subir el error | lo **traga**, lo registra y devuelve el cierre |
| Qué ve quien llama | el 503 honesto de siempre | 200: el cierre, que es lo que ocurrió |

**Por qué tragarlo es lo correcto en el cierre.** El estado del parte **no se
lee del histórico**: se deriva de la traza de cierre, que ya está guardada
(R18, R26). Lo que se pierde es una línea del relato, no el hecho. Dejar salir
ese error convertiría un cierre que ocurrió en el 503 «vuelve a intentarlo» de
la base, y quien lo reintentara le pediría otra vez al ERP de producción que
cerrara lo ya cerrado. Es el mismo argumento de `CierreSinTraza` (defecto 14 de
F-010) aplicado un escalón más abajo — y la diferencia con él está escrita en
la docstring: allí lo que falta es **el hecho**, y por eso sube; aquí falta
**su eco**, y por eso no.

**Y la fila no se pierde para siempre**: el siguiente reproceso de ese parte
pasa por `paso_persistencia`, que aplica la misma regla con la traza ya en
`cerrado` y escribe el `→ cerrado` que faltaba. La recuperación no es una
esperanza, es una consecuencia de que la regla sea una sola.

El log de ese caso lleva el `hash` del parte y nada más: **ni `oid`, ni
motivo**, ni nada del papel (R52, R44, R45). Hay test.

### 22.4 · La reclamación **ya cerrada** también deja su fila

`design.md` §4 dice «se cierra la incidencia en el ERP → `paso_cierre`, tras la
escritura», y T9 verifica dos casos: la fila tras el cierre y ninguna fila si
el cierre falla. `_resolver_ya_cerrada` no está en ninguno de los dos, así que
había que decidir. **Se anota también**, por tres motivos:

1. `ya_cerrada` está en `ESTADOS_DE_CIERRE_EN_FIRME`, así que el parte queda
   `cerrado` igualmente (R18). No anotarlo dejaría la última fila del histórico
   diciendo `aprobado` mientras el parte está `cerrado`: el relato
   contradiciendo al estado, que es lo que §4 existe para impedir.
2. No es un cierre fallido. El cierre **consta** —hay `TrazaCierre` en
   `ya_cerrada`— y el paso devuelve en verde.
3. Y si no se anotara aquí, lo anotaría igual el siguiente reproceso por
   `paso_persistencia`, porque la derivación mira la traza. O sea: la fila
   aparece de todas formas, y anotarla donde ocurre el hecho es lo que hace que
   su `decidido_at_utc` signifique algo.

Ese camino es además el que **más se repite** —cada relanzamiento de una remesa
ya procesada pasa por él una vez por parte—, así que la regla de constancia ahí
no es decoración: sin ella, cada pasada añadiría un `cerrado → cerrado`. Hay
test de las dos cosas.

### 22.5 · Se apunta el **estado del parte**, no lo que dijo la máquina

`estado_del_parte(validacion, decision_humana, estado_cierre)` y no
`estado_de_la_maquina(validacion)`. Es lo que dice §4 —«el derivado»— y lo que
salva el caso más común de todos: un parte no apto que **alguien aprobó** está
`aprobado` (R9); con el veredicto suelto, cada reproceso escribiría un
`aprobado → pendiente` que nunca ocurrió y el histórico contaría una
degradación falsa cada vez que alguien recarga la pantalla. El caso tiene test
propio y mata el mutante correspondiente (§23).

### 22.6 · La constancia **solo si hay veredicto**

El disparador de §4 es «se guarda un veredicto». Un parte extraído al que
todavía no se le ha mirado la firma —F-003 y F-004 son independientes— no
estrena histórico: abrirle uno con un `→ pendiente` diría que algo ya se
pronunció sobre él, y no es verdad. De paso se ahorra la consulta en el único
camino donde no puede aportar nada.

### 22.7 · La fila de constancia va sin `huella_veredicto`

La huella dice **sobre qué veredicto exacto decidió una persona**, y es lo que
hace que una aprobación deje de contar cuando el veredicto cambia (R19). Una
constancia no concede nada, así que apuntarle una huella sería darle la forma
de algo que sí. Va a `NULL`, como el autor y el motivo.

---

## 23 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2494 passed, 13 skipped** | `bash harness/init.sh`, servicio `api` |
| Tests del front | en verde por caché (árbol del front sin cambios) | `bash harness/init.sh` |
| De ellos, **nuevos de este bloque** | **18** (10 de T8 + 8 de T9) | `pytest tests/test_f028_persistencia.py` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (158/158, umbral 80 %) | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados** | **18** | `python -m harness.mutacion --feature F-028` |
| **Supervivientes** | **0** | ídem |
| **Timeouts** | **0** | ídem |
| **Mutantes generados del código de ESTE bloque** | **0** · ver abajo | ídem |
| **Mutantes a mano sobre este bloque** | **9 generados, 9 muertos** | §23.1 |
| **Tiempo de la suite** | **103,3 s** (`api`) | la propia suite |
| **Tiempo de la campaña** | **253,0 s** con 8 workers | `progress/mutacion_F-028.md` |

### Los supervivientes de la campaña

**Ninguno.** 18 mutantes, 18 muertos, 0 timeouts.

### 23.1 · Lo que hay que mirar de las evidencias: la campaña **no generó ni un mutante de este bloque**

Los tres ficheros nuevos y modificados entraron en el alcance —`constancia.py`
(91 líneas), `paso_cierre.py` (65) y `paso_persistencia.py` (58), 214 líneas
entre los tres, así lo lista `progress/mutacion_F-028.md`— y **no salió ni un
mutante de ellos**. Los 18 son de los bloques 1 y 2 (`estado.py`, `ddl.py`,
`repositorio_pg.py`, `sentencias.py`), y siguen muertos.

**Por qué, medido.** Los operadores de `harness.mutacion` son comparación,
lógico, `not`, booleano, entero y aritmético. El código de este bloque no les
ofrece nada:

- la única condición de `constancia.py` es `if estado is
  situacion.ultimo_estado_registrado:` — una comparación de **identidad**, que
  esta herramienta no muta (en `estado.py` tampoco mutó los `is`: mutó los
  `and` que los rodeaban);
- `paso_persistencia` añade un `if ctx.validacion is not None` sobre una línea
  que ya existía, y llamadas;
- `paso_cierre` añade un `try/except` y dos llamadas. Ni una comparación, ni un
  literal, ni un operador.

Así que **el 100 % de mutantes muertos de la campaña no dice nada sobre este
bloque**, y presentarlo como si lo dijera sería exactamente el número que
tranquiliza sin medir nada. Lo que **no** se ha hecho es retorcer el código para
darle material a la herramienta —cambiar el `is` por un `==` para que salga un
mutante es escribir para el medidor, no para el problema—.

Lo que se ha hecho en su lugar: **mutar los nueve puntos a mano**, uno a uno,
ejecutando la suite con cada mutación aplicada y restaurando el fichero después.
Es reproducible con el script de la sesión y estos son los resultados reales:

| # | Mutante aplicado a mano | Resultado | Quién lo caza |
|---|---|---|---|
| 1 | `constancia.py` · la regla se desactiva (`if False`): **siempre escribe** | **muerto** (3 fallos) | `un_reproceso_que_no_cambia_nada_no_escribe_ninguna_fila`, `no_se_repite_la_fila_si_el_parte_ya_constaba_cerrado`, `r26_la_constancia_mira_el_estado_derivado…` |
| 2 | `constancia.py` · la regla se invierte: **nunca escribe** | **muerto** (13 fallos) | los once positivos de T8 y T9 |
| 3 | `constancia.py` · `decidido_por="sistema"` (R24) | **muerto** (2 fallos) | `r24_la_fila_de_la_maquina_va_sin_autor_y_sin_motivo`, `r23_un_parte_apto_nace_aprobado…` |
| 4 | `constancia.py` · `estado_anterior=None` siempre (R22) | **muerto** (3 fallos) | `teclear_el_codigo_que_faltaba_deja_pendiente_aprobado`, `r18_si_la_traza_de_cierre_manda…`, `el_cierre_deja_su_fila_en_el_historico` |
| 5 | `paso_persistencia` · apunta `estado_de_la_maquina` y no el estado derivado | **muerto** (2 fallos) | `r26_la_constancia_mira_el_estado_derivado_y_no_solo_el_veredicto` (§22.5) |
| 6 | `paso_persistencia` · la constancia **antes** de guardar la validación | **muerto** (1 fallo) | `la_constancia_se_apunta_despues_de_guardar_la_validacion` |
| 7 | `paso_cierre` · la fila **antes** de escribir en el ERP | **muerto** (3 fallos) | `la_fila_cerrado_se_escribe_despues_de_que_el_cierre_conste`, y los **dos de cierre fallido** |
| 8 | `paso_cierre` · el fallo de la constancia **se deja subir** | **muerto** (1 fallo) | `si_la_constancia_falla_el_cierre_sigue_siendo_un_cierre` (§22.3) |
| 9 | `paso_cierre` · la reclamación ya cerrada **no** deja fila | **muerto** (1 fallo) | `r18_una_reclamacion_ya_cerrada_tambien_deja_su_fila` (§22.4) |

**9 de 9 muertos.** Los dos mutantes que un reviewer miraría primero —el 7 y el
8, que son los que tocan el camino del ERP de producción— mueren cada uno por
su test propio, y el 7 muere además por los dos control negativo del cierre
fallido, que es lo que tenían que hacer.

> **Propagación pendiente a `arnes-base`, y no la hago yo.** Que la campaña
> genere cero mutantes de un fichero en alcance **sin decirlo en ninguna parte**
> es un hueco del arnés genérico, no de esta feature: el informe sale con un
> 100 % que parece cobertura de mutación del trabajo y no lo es. Lo suyo sería
> que `harness/mutacion.py` avisara de los ficheros en alcance que no
> produjeron ningún mutante. Queda anotado para que lo decida el líder: el
> implementer no toca el arnés por su cuenta.

### Ruff

`python -m ruff check` sobre los cuatro ficheros de producción tocados y el de
test: **All checks passed**. Los avisos que reporta `init.sh` son deuda previa
del repositorio y **no crecen** con este trabajo.

---

## 24 · Verificaciones MANUAL pendientes

**Ninguna nueva.** Las de este bloque son las que ya estaban escritas en T27
(bloque 10), y este trabajo añade material a dos de ellas:

- **T27.3** (aprobar → rechazar → aprobar deja tres filas): a las filas humanas
  se les suman ahora las de constancia. Con la base real hay que comprobar que
  el histórico de un parte que se sube dos veces **no crece**, que es lo que
  aquí solo se puede probar contra un doble.
- **T27.5** (un parte cerrado responde 409): la fila `→ cerrado` tiene que
  aparecer con `decidido_por` a `NULL` y con su `estado_anterior` correcto en
  la consulta de solo lectura de T27.

**La base real y el ERP no se han tocado**, y no se ha escrito ni una línea que
pueda escribir en Sigrid: todo lo de este bloque corre con
`RepositorioEnMemoria` y `ErpEnMemoria`, sin red, sin BBDD y sin IA.

---

## 25 · Por dónde sigue · el encargo del bloque 4

**Todo el bloque 3 está cerrado.** El siguiente es el **bloque 4 · Las tres
puertas**, T10 y T11 — y es el primero que **afloja** algo que hoy funciona, así
que es donde `tests/test_f028_puertas.py` deja de ser decorado:

- **T10** · `contexto_parte.py`: `aprobacion` → `situacion: SituacionParte |
  None`, con la docstring que diga que viene del repositorio y **nunca del
  cuerpo**.
- **T11** · `paso_archivo`, `paso_grafico` y `paso_cierre`: `_exigir_admitido`
  pasa a exigir `EstadoParte.APROBADO` y **se retira el atajo del apto**
  (`design.md` §6). Con los cuatro estados contra los tres pasos, incluido
  **`rechazado` con veredicto apto**, que es el caso que hoy es imposible.

Lo que el bloque 4 se encuentra ya hecho y puede usar tal cual:

- `repositorio.consultar_situacion(hash_parte=…)` y `estado_del_parte(...)` son
  las dos piezas de la puerta nueva, y ya están probadas;
- **`paso_cierre` ya consulta la situación** una vez, dentro de
  `_anotar_que_el_parte_queda_cerrado`. Cuando T11 la lea también en
  `_exigir_admitido`, lo suyo es **guardarla en `ctx.situacion`** y que la
  anotación reutilice esa, para no hacer dos viajes por parte a un servidor
  compartido. Hoy no se hace porque `ContextoParte` todavía no tiene el hueco:
  eso es T10.
- `anotar_estado(repositorio, situacion, hash_parte=…, estado=…, ahora=…)` ya
  acepta una situación que le llegue de fuera, justo para eso.

Tres apuntes para quien lo coja:

- **Si `test_f028_puertas.py` se pone rojo, no se toca.** Significa que se ha
  aflojado una puerta que impide que un parte no apto escriba en Sigrid. Hoy
  está verde, 16 pasados, sin una sola edición desde el bloque 0.
- **El bloque 4 sigue sin retirar nada de F-026.** `Aprobacion`,
  `admite_circuito` y `consultar_aprobacion` se retiran en T15, bloque 5.
- **Ojo con el orden dentro de `_exigir_admitido`**: «no hay veredicto» tiene
  que seguir levantando su error propio y **antes** que el resto (R34), y hay
  tres casos del bloque 0 vigilándolo.

---

## 26 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las 158 líneas cambiadas.
- Árbol limpio, **2 commits** sobre `7cab1cb` (`4c0934a`, `117421e`), todos
  locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.

---

# F-028 · Estado del parte — informe del implementer · bloque 4

> Encargo: **T10 y T11** de `specs/F-028-estado-del-parte/tasks.md`, las tres
> puertas. Parada obligada al terminar. **No se ha entrado en el bloque 5.**
>
> Rama `feature/F-028-estado-del-parte`, desde `2393fa2`. Rigor **`estandar`**:
> fase RED, puerta de cobertura y campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature, sin tocar
> `azure-apps/`, `infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

**Este es el bloque que cambia el criterio de las tres puertas**, y por eso lo
primero que hay que saber es esto: `tests/test_f028_puertas.py` **sigue en
verde con sus 16 casos de T1 sin una sola edición de sus cuerpos**. El único
cambio en ese fichero fuera de lo añadido son dos ayudantes que ganan un
`commit: bool = True` —valor por defecto idéntico al que tenían escrito a
mano—, y se ve en el diff: `git diff 2393fa2 -- tests/test_f028_puertas.py`
solo borra siete líneas, y son imports y esas dos firmas.

---

## 27 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T10** | `4130495` | `ContextoParte.aprobacion` → `situacion: SituacionParte \| None`, con la docstring que dice que viene del repositorio y **nunca del cuerpo** |
| **T11** | `51fbe77` | Las tres puertas exigen `EstadoParte.APROBADO`; **se retira el atajo del apto**; la puerta vive en un solo sitio |

Lo que esto hace posible, que es medio encargo de la feature: **un parte apto
que una persona rechaza ya no se archiva, ni se adjunta, ni cierra su
incidencia**. Hasta el commit `51fbe77` eso era imposible por construcción.

---

## 28 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | La puerta de las tres puertas: `exigir_parte_aprobado` y `situacion_leida` |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `application/pipelines/contexto_parte.py` | `aprobacion` → `situacion`, con su docstring (T10) |
| `application/pipelines/paso_archivo.py` | `_exigir_admitido` delega en la puerta; fuera `admite_circuito` |
| `application/pipelines/paso_grafico.py` | Lo mismo |
| `application/pipelines/paso_cierre.py` | Lo mismo, **más** la puerta nueva del parte `cerrado` (R7) y la constancia reutilizando la situación ya leída |
| `tests/test_f028_puertas.py` | **Ampliado**: 16 → 48 casos (2 de T10, 30 de T11) |
| `tests/test_f026_puertas.py` | Cinco casos retirados, con su nota de sustitución (§30) |
| `tests/test_f028_persistencia.py` | Un caso que ahora falla antes y mejor, y una aserción nueva (§30) |
| `tests/test_f003_paso_extraccion.py` | El control de campos del contexto: `aprobacion` → `situacion` |
| `tests/utiles_sharepoint.py` | `RepositorioFalso` aprende `consultar_situacion` |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff 2393fa2 --stat`: no aparecen en el diff
`domain/models/validacion.py`, `sql/04_validaciones.sql`,
`sql/10_aprobaciones.sql`, `domain/models/aprobacion.py`,
`infrastructure/sigrid/`, `infrastructure/sharepoint/`,
`interface_adapters/api/`, `function_app.py`, el front, ni
`harness/features.json`.

**El borde no se ha tocado y no hacía falta**: las tres puertas siguen
levantando `ParteNoApto`, que los tres handlers ya traducen a **409** con el
motivo dentro. Un parte `cerrado` al que alguien intente archivar responde hoy
un 409 que dice «su incidencia ya consta cerrada en el ERP, y "cerrado" es
terminal», que es exactamente lo que R7 quiere que pase y el mismo código que
`design.md` §5 reserva para `ParteCerrado` en el endpoint nuevo.

---

## 29 · Fase RED · las trazas, pegadas

### T10 · antes de que el contexto tuviera `situacion`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f028_puertas.py -q -k "contexto"

    def test_f028_r33_el_contexto_lleva_la_situacion_y_no_la_aprobacion():
        campos = {campo.name: campo.type for campo in fields(ContextoParte)}
>       assert "situacion" in campos
E       AssertionError: assert 'situacion' in {'parte': 'ParteTroceado',
        'extraccion': 'ExtraccionParte | None', 'lectura_firma': 'LecturaFirma | None',
        'validacion': 'ResultadoValidacion | None', ...}

tests\test_f028_puertas.py:509: AssertionError

    def test_f028_r33_el_contexto_dice_que_la_situacion_no_viene_del_cuerpo():
        documentacion = (ContextoParte.__doc__ or "").lower()
>       assert "situacion" in documentacion or "situación" in documentacion
E       AssertionError

tests\test_f028_puertas.py:526: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f028_puertas.py::test_f028_r33_el_contexto_lleva_la_situacion_y_no_la_aprobacion
FAILED tests/test_f028_puertas.py::test_f028_r33_el_contexto_dice_que_la_situacion_no_viene_del_cuerpo
2 failed, 16 deselected in 1.23s
```

### T11 · antes de retirar el atajo del apto

**La traza que importa de todo el bloque**, porque es el defecto que la feature
viene a arreglar, visto desde el test:

```
$ .venv/Scripts/python.exe -m pytest "tests/test_f028_puertas.py::test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta" -q

_ test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta[archivo] _

    @pytest.mark.parametrize("puerta", PUERTAS)
    def test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta(puerta):
        dobles = _dobles()

>       with pytest.raises(ParteNoApto) as fallo:
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ParteNoApto

tests\test_f028_puertas.py:762: Failed
FFF                                                                      [100%]
3 failed
```

«DID NOT RAISE» leído en voz alta: **el parte apto que una persona había
rechazado se archivaba igual**, y en las otras dos puertas se adjuntaba al ERP
y se cerraba la incidencia. Los tres casos fallaban, uno por puerta.

Y la tanda entera de T11, antes de tocar producción:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f028_puertas.py -q
...
FAILED ...::test_f028_r9_un_parte_no_apto_que_una_persona_aprobo_pasa[archivo|grafico|cierre]
FAILED ...::test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta[archivo|grafico|cierre]
FAILED ...::test_f028_r5_el_rechazo_tampoco_caduca_cuando_trae_otra_huella[archivo|grafico|cierre]
FAILED ...::test_f028_r7_un_parte_ya_cerrado_no_vuelve_a_escribir_nada[archivo|grafico|cierre - cerrado|ya_cerrada]
FAILED ...::test_f028_r33_las_tres_puertas_preguntan_por_la_situacion[True|False - archivo|grafico|cierre]
21 failed, 27 passed in 1.98s
```

Los 27 que ya pasaban en rojo son los 16 de T1 —que no podían fallar, y ese es
justo su oficio—, los 2 de T10 —ya implementados—, y los que describen lo que
F-026 ya hacía bien y F-028 conserva: `test_f028_r3_...` (el apto pasa),
`test_f028_r19_...` (una aprobación sobre otro veredicto no abre nada) y
`test_f028_r33_ninguna_puerta_consulta_ya_la_tabla_de_f026` —este último
pasaba en rojo **por el atajo**: el parte apto no consultaba nada, así que
tampoco consultaba la tabla de F-026. Hoy pasa por el motivo bueno.

---

## 30 · Los tests de antes que han cambiado, y por qué

Son siete, y ninguno se ha «ajustado para que pase». Se listan uno a uno
porque un test que cambia sin justificación escrita es un test aflojado.

### 30.1 · Cinco retirados de `tests/test_f026_puertas.py`

Los cinco probaban **el mecanismo que T11 sustituye**, no un comportamiento que
siga existiendo. En su sitio queda un recuadro fechado que dice qué probaban,
por qué se van y **dónde está su sustituto** —escrito y en verde antes de
borrarlos—:

| Retirado | Qué probaba | Sustituto en F-028 |
|---|---|---|
| `test_f026_r23_un_parte_aprobado_y_vigente_si_se_archiva` | Una fila vigente de `postventa.aprobaciones` abría la puerta | `test_f028_r9_un_parte_no_apto_que_una_persona_aprobo_pasa[archivo]` |
| `..._si_se_adjunta` | Lo mismo en el gráfico | `...[grafico]` |
| `..._si_llega_al_cierre` | Lo mismo en el cierre | `...[cierre]` |
| `test_f026_r24_los_tres_pasos_leen_la_aprobacion_del_repositorio` | Que se **preguntaba** al almacén | `test_f028_r33_las_tres_puertas_preguntan_por_la_situacion` |
| `test_f026_r23_el_parte_apto_de_siempre_no_consulta_ninguna_aprobacion` | **El atajo del apto** | `..._preguntan_por_la_situacion[True-*]` y `..._ninguna_puerta_consulta_ya_la_tabla_de_f026` |

Los cuatro primeros se ponían **rojos** con T11 y no podían quedarse: la
decisión humana ya no vive en esa tabla. No se han «adaptado» cambiándoles el
doble, que es lo que los habría dejado verdes sin que nadie se enterara de que
probaban otra cosa.

El quinto **seguía en verde**, y por eso merece un párrafo: `admite_circuito`
ya no se llama desde ninguna puerta, así que `aprobaciones_consultadas == []`
es trivialmente cierto. Dejarlo habría sido peor que borrarlo — un test verde
cuyo nombre («el parte apto de siempre no consulta ninguna aprobación») afirma
justo lo que `design.md` §6 retira. El sustituto comprueba lo contrario: que el
apto **sí** paga su consulta.

> **Para el bloque 5 (T15)**: quedan dos casos en ese fichero que siguen verdes
> pero cuyo montaje ya es inerte —`test_f026_r31_una_aprobacion_revocada_no_abre_ninguna_puerta`
> y `test_f026_r23_una_aprobacion_de_otro_destino_no_sirve`—: pasan una
> `Aprobacion` a un doble al que ya nadie se la pide, así que hoy prueban lo
> mismo que los `r25`. Se dejan a T15, que es quien retira `Aprobacion`. **No
> están rotos**: están de más.

### 30.2 · `tests/test_f028_persistencia.py` · un caso que ahora falla antes

`test_f028_no_se_repite_la_fila_si_el_parte_ya_constaba_cerrado` montaba un
parte con su traza de cierre ya en `cerrado` y comprobaba que un reproceso no
añadía un segundo `cerrado → cerrado`. Con T11 ese parte **ya no pasa la puerta
de aptitud**, así que el paso ni llega a preguntarle al ERP.

Mantiene su nombre porque su afirmación sigue siendo verdad, y gana dos
aserciones (`erp.lecturas == []`, `erp.cierres == []`): la garantía es **más
fuerte** que antes, no menos. Antes se evitaba la fila repetida; ahora se evita
además el viaje al ERP de producción. El cambio va explicado dentro del propio
test, en un recuadro.

También se le ha añadido a `test_f028_el_cierre_deja_su_fila_en_el_historico`
la aserción `repositorio.situaciones_consultadas == [HASH]`: es lo que fija que
la constancia **reutiliza** la situación que leyó la puerta y no hace un
segundo viaje.

### 30.3 · `tests/test_f003_paso_extraccion.py` · el control de campos

`test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas` enumera los
campos de `ContextoParte` para que nadie meta ahí una ruta de SharePoint, un
identificador de base o un estado de Sigrid. `aprobacion` → `situacion`, con el
comentario que explica que el campo **cambia de nombre, no de naturaleza**: la
lista blanca sigue teniendo la misma longitud y la misma fuerza.

### 30.4 · `tests/utiles_sharepoint.py` · el doble aprende a contestar

`RepositorioFalso` no sabía responder `consultar_situacion` y, al retirarse el
atajo, **60 tests de F-006, F-010 y F-019 se pusieron rojos con un
`AttributeError`**. No es un fallo de esos tests: es la consecuencia directa y
esperada de que ahora se pregunte siempre. El doble devuelve una
`SituacionParte()` vacía, que es lo que devuelve el adaptador de verdad cuando
de un parte no consta nada, y la docstring explica por qué devuelve valor en
vez de levantar.

---

## 31 · Decisiones de diseño, y las tres que hay que juzgar

### 31.1 · La puerta vive en **un** módulo, y §8.2 no lo lista

`design.md` §8.2 dice «`paso_archivo.py`, `paso_grafico.py`, `paso_cierre.py`:
`_exigir_admitido` mira el estado». Lo implementado hace exactamente eso, pero
la mecánica —leer la situación, derivar el estado, exigir `APROBADO` y componer
el motivo— vive en `application/pipelines/puerta_de_estado.py` y los tres pasos
la llaman con su frase.

**Es una desviación de forma y se declara.** El argumento es el que ya escribió
`constancia.py` en el bloque 3 y `confianza.py` en F-004: dos copias de una
regla divergen el día que alguien la corrija en una sola, y en una campaña de
mutación **cada copia se cuenta aparte**, con lo que la segunda y la tercera se
quedan sin tests que las maten.

Aquí pesa más que en ningún otro sitio del proyecto: esto es **lo único** que
separa un parte sin revisar de un PDF con el DNI de un cliente en SharePoint y
de una reclamación cerrada en el ERP. Tres copias son tres sitios donde puede
aflojarse, y basta con que se afloje uno.

Lo que **no** se ha unificado, a propósito: los mensajes de «no hay veredicto»
y el final de cada error («no se archiva», «no se adjunta a la reclamación»,
«no se cierra la incidencia»). Cada puerta le está diciendo al lector qué se ha
quedado sin hacer, y esa parte sí es de cada paso.

### 31.2 · El error sigue siendo `ParteNoApto`, y **no** `ParteCerrado`

Un parte `cerrado` que llega a una de las tres puertas levanta `ParteNoApto`
con un motivo que dice que está cerrado, no el `ParteCerrado` que T4 creó.

Por qué: `ParteCerrado` es de `design.md` §5 —el **cambio de estado** de un
parte cerrado, 409 en `POST /api/estado`— y su traducción HTTP la escribe T13,
en el bloque 5. Levantarlo hoy desde las puertas daría un **500** en tres
endpoints que funcionan, porque `function_app.py` todavía no sabe traducirlo, y
el bloque 4 no toca el borde.

Y no se pierde nada por el camino: `ParteNoApto` ya se traduce a **409** en los
tres handlers, que es el código que `design.md` §5 reserva para el parte
cerrado, y el motivo que viaja dentro dice literalmente por qué. Si el reviewer
prefiere el tipo propio, el sitio es una línea de `puerta_de_estado.py` y la
tabla de traducción de T13.

### 31.3 · Los motivos son **tres** y no uno, y eso tiene un porqué operativo

`MOTIVOS` mapea cada estado no admitido a su explicación. No es adorno: **cada
estado se arregla de una forma distinta y quien lee el error es quien tiene que
ir a arreglarlo**. El `pendiente` se resuelve mirando el parte y decidiendo; el
`rechazado` solo lo deshace otra persona volviendo a decidir; el `cerrado` no
se deshace de ninguna manera desde aquí (R7). Un error único para los tres
mandaría a alguien a intentar lo que no se puede — y en este dominio «lo que no
se puede» es deshacer una escritura en el ERP de producción.

Los dos mensajes que la suite comprueba palabra a palabra son `"rechaz"` y
`"cerrad"`, y están en los tests precisamente para que no se fundan en uno.

### 31.4 · La constancia del cierre reutiliza la situación de la puerta

El informe del bloque 3 lo dejó apuntado y se ha hecho:
`_anotar_que_el_parte_queda_cerrado` ya no consulta, usa `situacion_leida(ctx,
repositorio)`, que devuelve `ctx.situacion` —puesta por la puerta, que es lo
primero que hace el paso— o consulta si no la hubiera.

El `or` de la derecha no es defensa vacía: es lo que garantiza que, si algún
día alguien reordenara el paso, lo que pase sea **una consulta de más** y no un
`AttributeError` **justo en el punto en el que el ERP ya está escrito** — que
es el único sitio del proyecto donde un fallo de persistencia se traga a
propósito. La campaña de mutación lo ataca (mutante 7/19) y muere.

### Desviaciones respecto a la spec

Una, la de §31.1. Ninguna más: el criterio implementado es literalmente el de
`design.md` §6, `estado_del_parte(...) is EstadoParte.APROBADO`, con la
situación leída del repositorio.

---

## 32 · Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** (servicio `api`) | **2.517 pasados, 13 saltados, 0 fallos** |
| **Tests del servicio `front`** | en verde (caché del portero: árbol sin cambios) |
| **Casos en `test_f028_puertas.py`** | **48** (16 de T1 intactos + 2 de T10 + 30 de T11) |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 183/183, umbral 80 %, nivel `estandar` |
| **Mutantes generados / supervivientes** | automáticos **19 / 0** (0 timeouts, 274,2 s) · **a mano 13 / 0** |
| **Tiempo de la suite** | **103,19 s** bajo medición de cobertura (64,9 s sin ella) |
| **Ruff** | Sin avisos nuevos: los dos que quedan en `tests/utiles_sharepoint.py` (`I001`, `RET501`) **ya estaban en `HEAD`** antes de tocarlo |

### Los supervivientes, y qué se hace con cada uno

**Ninguno**, ni en la campaña automática ni en la manual. 19 mutantes
evaluados, 19 muertos (informe en `progress/mutacion_F-028.md`), más 13 a mano,
13 muertos.

### Los 13 mutantes **a mano**, porque la campaña no llega a este bloque

Mismo método que usó el bloque 3 por el mismo motivo (§23.1): se aplica la
mutación, se corre la suite acotada, se restaura el fichero. «Muerto» = al
menos un test falla.

| # | Mutante | Resultado |
|---|---|---|
| M1 | La puerta no levanta cuando falta el veredicto | muerto |
| M2 | La puerta **no consulta el almacén** y se inventa una situación vacía | muerto |
| M3 | La puerta se abre para todo lo que no sea `pendiente` | muerto |
| M4 | La puerta se abre **también para el `rechazado`** | muerto |
| M5 | La puerta se abre **también para el `cerrado`** | muerto |
| M6 | La derivación ignora la traza de cierre | muerto |
| M7 | La derivación ignora la decisión humana | muerto |
| M8 | El motivo del rechazo deja de nombrar el rechazo | muerto |
| M9 | El motivo del cerrado deja de nombrar el cierre | muerto |
| M10 | La constancia del cierre vuelve a consultar en vez de reutilizar | muerto |
| M11 | `paso_archivo` se queda sin puerta | muerto |
| M12 | `paso_grafico` se queda sin puerta | muerto |
| M13 | `paso_cierre` se queda sin puerta | muerto |

**Dos de ellos hubo que reformularlos, y se cuenta porque es información sobre
el método, no sobre el código**:

- **M11 en su primera forma era un mutante equivalente**: cambiaba
  `exigir_parte_aprobado(...)` por `return exigir_parte_aprobado(...)`, y como
  el valor devuelto no lo lee nadie en `_exigir_admitido`, el programa mutado
  hace exactamente lo mismo. Sobrevivió con razón. Reformulado como «la llamada
  desaparece», muere.
- **M9 en su primera forma solo cambiaba la primera mitad del mensaje**, y la
  segunda seguía diciendo «"cerrado" es terminal», así que la aserción
  `"cerrad" in motivo` seguía encontrando la palabra. Sustituido el mensaje
  entero, muere.

Los tres que más valen son **M2, M4 y M5**: son, literalmente, las tres formas
de volver a dejar pasar lo que este bloque viene a frenar.

### 32.1 · Lo que hay que mirar de las evidencias: la campaña genera **un solo** mutante del bloque

De los 19, **uno** cae en `puerta_de_estado.py` (línea 137, el `or` de
`situacion_leida`) y ninguno en el `if estado is EstadoParte.APROBADO`, que es
el corazón de la puerta. El motivo es el mismo que ya observó el bloque 3: el
mutador no reescribe comparaciones `is`, ni condiciones `x is None`, ni las
entradas de un diccionario literal. Los otros 18 son del dominio y de la
persistencia de los bloques anteriores, y siguen muriendo — que también es
información: T11 no ha roto nada de lo que ya estaba probado.

Por eso se ha mutado **a mano**, con el método del bloque 3, y ahí están los 13
mutantes que la campaña no genera. Aun así, conclusión honesta: **para este
bloque la campaña automática aporta poco y no es la evidencia que lo
respalda.** La que lo respalda es la fase RED, que es
directa y está pegada arriba: los 21 casos en rojo antes del cambio y los 48 en
verde después, con los 16 control-negativo de T1 sin tocar. Quien quiera
comprobarlo a mano, la forma más rápida es revertir el `if estado is
EstadoParte.APROBADO` a `is not` y ver caer 30 casos.

---

## 33 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes y este bloque añade peso a dos de ellas, que ahora
**ya se pueden ejecutar de verdad** en cuanto se despliegue:

- **T27.4 · un parte apto rechazado a mano no se archiva.** Era la que no podía
  pasar antes de este bloque. Ojo: hasta que el bloque 5 dé el endpoint
  `POST /api/estado`, la fila de rechazo hay que sembrarla a mano en
  `postventa.historico_estado` para probarlo contra la base real.
- **T27.5 · un parte cerrado responde 409.** Hoy ya lo responden `archivar`,
  `adjuntar` y `cerrar`, con el motivo dentro. El 409 del **cambio de estado**
  es de T13.

Y una nueva, que sale del coste que este bloque acepta a conciencia:

- **MANUAL (humano) · el coste de la retirada del atajo.** En la primera tanda
  real de una remesa de ~22 partes, mirar cuánto tarda el circuito completo
  contra `psql-albaranes-rs9k2`, que es **compartido**. `design.md` §6 lo
  cuantifica en 66 consultas por tanda donde antes había cero para los verdes.
  Si molestara, el arreglo **no es volver al atajo**: es leer la situación una
  vez por parte y tanda, y el sitio donde se hace es `ContextoParte`.

---

## 34 · Por dónde sigue · el encargo del bloque 5

**Todo el bloque 4 está cerrado.** El siguiente es el **bloque 5 · El borde
HTTP**, T12 a T15, y es el que **retira** código de F-026: el endpoint
`/api/aprobar`, la serialización de la aprobación, las sentencias y el puerto.

Lo que el bloque 5 se encuentra ya hecho:

- **la decisión ya no la lee nadie de `postventa.aprobaciones`**: las tres
  puertas leen `consultar_situacion` y el único sitio de producción que sigue
  llamando a `consultar_aprobacion` es `interface_adapters/api/parte.py:131`
  —el bloque `aprobacion` de la respuesta—, que es justo lo que T14 sustituye
  por el bloque `estado`;
- `ContextoParte.situacion` ya existe y lo rellena la puerta, así que T14 puede
  leer el estado sin una consulta más por parte;
- `ParteCerrado` y `CambioDeEstadoInvalido` existen desde T4 y **siguen sin
  traducirse** en `function_app.py`: eso es T13, y es lo que permitiría, si se
  quiere, que las tres puertas pasen a levantar `ParteCerrado` (§31.2).

Cuatro apuntes para quien lo coja:

- **`tests/test_f028_puertas.py` sigue siendo la red, y ahora vigila más.** 48
  casos. Si uno se pone rojo en el bloque 5, **parar y decirlo**: los 16 de T1
  llevan intactos desde el bloque 0 y los 30 de T11 son los cuatro estados
  contra las tres puertas.
- **En `tests/test_f026_puertas.py` quedan dos casos inertes** (§30.1) que T15
  debería retirar con el resto de `Aprobacion`.
- **`RepositorioFalso` y `RepositorioEnMemoria` aún declaran
  `consultar_aprobacion`**: se retira en T15, junto con el puerto.
- **Que el bloque 5 no dé por hecho que puede quitar `huella_de_veredicto`**:
  la usa `estado.py::_aprueba_lo_que_hay`, que es lo que hace que una
  aprobación deje de contar cuando el veredicto cambia (R19). D9 y §10 la
  congelan.

---

## 35 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las 183 líneas cambiadas.
- Árbol limpio, **3 commits** sobre `2393fa2` (`4130495` T10, `51fbe77` T11 y
  el de este informe), todos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado**: todo corre con
  `RepositorioEnMemoria`, `RepositorioFalso`, `ErpEnMemoria` y
  `ArchivoPortFalso`, sin red, sin BBDD y sin IA.

---

# F-028 · Estado del parte — informe del implementer · bloque 5, T13

> Encargo: **T13 y nada más** de `specs/F-028-estado-del-parte/tasks.md`.
> Parada obligada al terminar. **No se ha entrado en T14 ni en T15.**
>
> Rama `feature/F-028-estado-del-parte`, desde `6eb6d33`. Rigor **`estandar`**:
> fase RED, puerta de cobertura y campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature, sin tocar
> `azure-apps/`, `infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

**T13 venía a medias y en rojo a propósito.** El commit `822100e` la dejó así
—«EL VIGILANTE MATO AL AGENTE por 600 s sin progreso»— con el handler escrito
(356 líneas), su fichero de test (1.126) y **57 casos en verde y 12 en rojo**.
Este encargo la termina. Lo primero que hay que saber, porque cambia cómo se
lee todo lo demás:

1. **Los 12 rojos eran de los tests, no del handler** —lo dice el propio
   commit y se ha confirmado uno a uno—, y **ninguno** era lo que ese commit
   creía: `consultar_estado_cierre` **ya estaba** en `AnotaLosResultados` (son
   las nueve líneas de `parte.py` que el agente alcanzó a escribir antes de que
   lo mataran). Lo que fallaba era otra cosa, y está en §38.
2. **El handler no se ha tocado.** `interface_adapters/api/estado.py` entra en
   este commit **byte a byte como lo dejó `822100e`**: `git diff 822100e --
   services/postventa-api/interface_adapters/api/estado.py` está vacío. Se
   miró requisito a requisito buscando el error del lado del código, y no lo
   hay; el detalle, en §39.

---

## 36 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T13** | `2732199` | Los 12 tests arreglados, la ruta `POST /api/estado` en `function_app.py` con sus 12 traducciones —incluida la de `ParteCerrado` a **409**, que no existía— y `tests/utiles_rutas.py` |

Lo que esto hace posible: **el endpoint existe de verdad**. Hasta hoy el
handler estaba escrito y no lo llamaba nadie; `ParteCerrado` existía desde T4
y `function_app.py` no sabía traducirlo, así que un parte cerrado que llegara
por la puerta de atrás habría salido con un **500** —un error del servidor
para algo que no lo es—.

> **T12 sigue sin marcar en `tasks.md`** aunque el commit `0af9830` la hizo
> («F-028 T12: el bloque «estado» de las respuestas»). No se ha marcado aquí
> porque el encargo era «T13 y nada más», y marcar la tarea de otro es
> exactamente la clase de arreglo silencioso que luego nadie sabe de dónde
> salió. **Queda para el líder.**

---

## 37 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/tests/utiles_rutas.py` | La caché **de proceso** de `app.get_functions()`. Ver §40.3: no es adorno |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | La ruta `estado` (115 líneas), los dos errores nuevos en el bloque de imports, el import del handler y la entrada del endpoint en la cabecera |
| `services/postventa-api/tests/test_f028_estado_http.py` | Los 12 arreglados, `_fila_humana` / `_filas_de_maquina`, el control de R37 reescrito sobre el árbol sintáctico, y **19 casos nuevos** de la ruta |
| `services/postventa-api/tests/utiles_pg.py` | `registrar_decision` actualiza la situación que devolverá `consultar_situacion`. Ver §40.2 |
| `services/postventa-api/tests/test_f026_aprobar_http.py` | Su `_rutas_registradas` **se muda** a `utiles_rutas.py` y delega; se quita el `lru_cache` que ya no usa |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | `"estado"` entra en `ENDPOINTS` y el barrido pasa de 12 a **13** rutas |
| `specs/F-028-estado-del-parte/tasks.md` | T13 marcada |

**No se ha tocado** `interface_adapters/api/estado.py` (el handler),
`estado_serializado.py`, el dominio, la persistencia, las tres puertas,
`tests/test_f028_puertas.py` (la red de seguridad de T1, que sigue en verde con
sus 48 casos), `sql/`, el front, `harness/features.json`, `azure-apps/`,
`infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

---

## 38 · Los 12 rojos que había, y qué tenía cada uno

Eran **dos** causas, no doce.

### 38.1 · Once daban por hecho que una llamada deja **una** fila. Deja dos

Y las dos son correctas, que es lo que hace este caso interesante. `POST
/api/estado` hace **las dos cosas en una llamada** (`design.md` §5): guarda el
parte con `paso_persistencia` y escribe la decisión. Y `paso_persistencia`
anota desde T8 la constancia del estado derivado **si cambió** (R23, R24). Con
el cuerpo por omisión de ese fichero —un parte **no apto** que nunca se había
guardado— la secuencia real es:

| # | Fila | Autor | Qué cuenta |
|---|---|---|---|
| 1 | `→ pendiente` | máquina (`decidido_por` a `None`) | el parte nace pendiente (R4, R23) |
| 2 | `pendiente → rechazado` | la persona | la decisión de T13 |

Los tests miraban `repositorio.decisiones[0]` —la de máquina— y afirmaban
sobre ella el `oid`, el motivo y la huella, que una constancia **no lleva a
propósito**. De ahí los `assert None == 'oid-opaco-...'`.

**Arreglo**: `_fila_humana(repositorio)`, que busca por `decidido_por` y no por
posición —con el índice, el día que la constancia dejara de escribirse el test
seguiría en verde afirmando sobre la fila equivocada— y **falla si hay más de
una**, que sería el doble registro que R21 prohíbe. El test de R9 afirma ahora
**las dos filas**: es la película que el histórico tiene que contar, y dejarla
a medias era desperdiciar el mejor test del fichero.

**Y con ello cambia una expectativa, que hay que decir en voz alta**: el
`estado_anterior` de la respuesta pasa de `null` a `"pendiente"`. Es lo
correcto y no un apaño: el handler lee la situación **después** de guardar
—está escrito así y con su porqué en la docstring— precisamente para que el
«de» salga del histórico ya actualizado y no del cuerpo (R33). El `null` que
el test esperaba solo podía salir de leer antes.

### 38.2 · El control de R37 miraba el **texto** y se topaba con una docstring

`test_f028_r37_...` buscaba la cadena `"sharepoint"` en el fuente del handler y
la encontraba dentro de la docstring de `_exigir_que_no_este_cerrado`, la que
explica por qué un parte cerrado no se puede rechazar: «lo escrito en Sigrid y
en **SharePoint** no se deshace desde aquí». El control era bueno; el módulo
estaba **fallando por documentarse bien**.

Es el mismo tropiezo que el bloque 3 dejó escrito en §5 de este informe, y se
ha usado **su** solución y no otra: vocabulario del **árbol sintáctico**
—nombres, atributos, argumentos, definiciones, alias y literales— saltándose
las docstrings. Con **una línea más** que allí no hacía falta y aquí decide
todo: `ImportFrom.module`. Un `from infrastructure.sharepoint.biblioteca import
subir` deja «sharepoint» **únicamente** ahí; sin esa línea el control se habría
puesto verde mirando a otro lado, que es peor que no tenerlo.

Y por eso va acompañado de `test_f028_r37_el_control_del_vocabulario_ve_los_
imports_de_verdad`: se le da al vocabulario un módulo de mentira que importa
los dos adaptadores prohibidos **de las dos formas en que se importan de
verdad** y se comprueba que las dos caen. Un control negativo que no sabe
fallar da tranquilidad y no da nada más.

---

## 39 · Se buscó el fallo en el handler. No está

El encargo decía: «arregla los tests, no el handler, salvo que al hacerlo
descubras que el handler está mal de verdad — en ese caso dilo». Se buscó, y la
conclusión es que **no lo está**. Lo que se comprobó, uno a uno:

- **el orden** (`parte`, `validacion`, constancia, lectura, decisión) es el que
  `design.md` §5 y la docstring prometen, y es el único que deja la huella del
  veredicto que **acaba de escribirse**;
- **la puerta del parte cerrado va antes de `paso_persistencia`**, que es lo
  que hace honesto el 409: se comprueba con `repositorio.orden == []` y
  `repositorio.partes == []`, no suponiendo;
- **las cuatro claves propias se miran antes que nada**, así que un cuerpo sin
  `usuario_oid` **y** sin `parte` falla por `usuario_oid`;
- **`confirmado` exige el booleano** (`crudo is not True`), no un valor que
  parezca verdadero;
- **el motivo** se recorta por los extremos, se acota contra `LIMITE_MOTIVO`
  —que es del dominio— y **se rechaza** en vez de recortarse;
- **el veredicto se recalcula** y lo que venga hecho en el cuerpo se ignora;
- **ni el `oid`, ni el correo, ni el nombre, ni el motivo** salen de la
  respuesta.

Lo único que se le podría objetar al handler es de forma y no de fondo, y se
deja anotado sin tocarlo: `_exigir_que_no_este_cerrado` recibe el parámetro con
el nombre `repositorio` cuando lo que le llega es el envoltorio
`AnotaLosResultados`. Funciona —el envoltorio implementa el puerto entero
delegando— y el tipo declarado, `RepositorioPartesPort`, es el correcto.

---

## 40 · Decisiones de diseño, y las tres que hay que juzgar

### 40.1 · §31.2 resuelta: las tres puertas **siguen levantando `ParteNoApto`**

El bloque 4 lo dejó abierto en §31.2 y el encargo pedía decidirlo ahora que la
traducción de `ParteCerrado` existe. **Se decide no cambiarlo**, y por tres
motivos:

1. **`ParteCerrado` significa otra cosa.** Es de `design.md` §5: «se ha pedido
   **cambiar el estado** de un parte ya cerrado». En las tres puertas nadie
   está cambiando el estado de nada — se está pidiendo archivar, adjuntar o
   cerrar un parte que no está `aprobado`. Reusar el tipo porque el código HTTP
   coincide sería nombrar por el síntoma.
2. **`cerrado` es uno de tres**, no un caso aparte. Las puertas rechazan
   `pendiente`, `rechazado` y `cerrado`, y `MOTIVOS` le da a cada uno su
   explicación porque **cada uno se arregla de una forma distinta** (§31.3).
   Partir uno de los tres a otro tipo de excepción rompe esa simetría y obliga
   a los tres handlers a capturar dos cosas donde hoy capturan una.
3. **No se gana nada medible.** `ParteNoApto` ya se traduce a **409** en los
   tres, que es el código que `design.md` §5 reserva, y el motivo que viaja
   dentro dice literalmente que el parte está cerrado. Lo que se ganaría es un
   tipo; lo que se pagaría es tocar `puerta_de_estado.py` y la tabla de
   traducción de tres endpoints que hoy funcionan, y volver a mover
   `tests/test_f028_puertas.py`, que es **la red de seguridad de T1** y lleva
   intacta desde el bloque 0.

> Si el reviewer prefiere el tipo propio, el sitio sigue siendo el que dijo el
> bloque 4: una línea de `puerta_de_estado.py` y un `except` en los tres
> handlers. Esta decisión no lo cierra, lo documenta.

### 40.2 · El doble aprende a leerse a sí mismo

`RepositorioEnMemoria.consultar_situacion` devolvía **siempre** lo que el test
le preparó en el constructor, así que no veía la fila que el propio doble
acababa de escribir. La tabla sí: `select_situacion_estado` lee las dos últimas
filas del histórico, y una consulta posterior a una escritura ve lo que se
acaba de apuntar.

La diferencia no es teórica y es justo la que rompía: en **una sola llamada** a
`/api/estado` se escribe la constancia y después se lee la situación para
componer el `estado_anterior` de la decisión humana. Con el doble viejo ese
encadenado no se podía probar — el test habría quedado afirmando sobre nada.

Se mueve `ultimo_estado_registrado` siempre y `decision_humana` **solo si la
fila la firmó una persona** (R24, R26): una constancia de máquina no es una
decisión, y darle ese hueco convertiría una anotación en criterio.

**Es un doble compartido y por eso se dice aquí**: la suite entera del servicio
—2.612 casos— sigue en verde con el cambio, `tests/test_f028_puertas.py`
incluido.

### 40.3 · `utiles_rutas.py`, o por qué dos ficheros no pueden mirar rutas

`function_app.app.get_functions()` **no es idempotente**: a la segunda llamada
levanta `ValueError: Function health does not have a unique function name`.
F-026 lo descubrió y lo resolvió con un `lru_cache` **en su fichero**, que vale
mientras solo un fichero mire rutas. T13 necesita mirar la suya, y con dos
cachés el segundo fichero revienta **y el fallo no habla de ninguno de los
dos**: dice que `health` está repetida.

El problema es del proceso, así que la caché se muda al proceso:
`tests/utiles_rutas.py`. F-026 delega ahí en dos líneas. No se ha tocado
ninguno de sus 48 casos.

---

## 41 · Fase RED · las trazas, pegadas

### 41.1 · Los 12 que había, antes de tocar nada

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_http.py -q
...
E   AssertionError: assert 2 == 1
     +  where 2 = len([DecisionEstado(hash_parte='9f2b0011aabb',
        estado=<EstadoParte.PENDIENTE: 'pendiente'>, ...)])
tests/test_f028_estado_http.py:495: AssertionError

E   AssertionError: assert None == 'oid-opaco-inventado-para-este-test'
     +  where None = DecisionEstado(hash_parte='9f2b0011aabb',
        estado=<EstadoParte.PENDIENTE: 'pendiente'>, estado_anterior=None,
        decidido_por=None, motivo=None, huella_veredicto=None).decidido_por
tests/test_f028_estado_http.py:1068: AssertionError

E   AssertionError: assert ['parte', 'va...', 'decision'] == ['parte', 'va...', 'decision']
      At index 3 diff: 'decision' != 'consulta_situacion'
      Left contains one more item: 'decision'
tests/test_f028_estado_http.py:550: AssertionError

E   assert 'sharepoint' not in "from __futu...desde aquí')"
E     'sharepoint' is contained here:
E       grid y en sharepoint no se deshace desde aquí, y cambiar el
E     ?           ++++++++++
tests/test_f028_estado_http.py:1124: AssertionError

=========================== short test summary info ===========================
FAILED ...::test_f028_r9_rechazar_un_parte_deja_su_fila_con_quien_cuando_y_por_que
FAILED ...::test_f028_r5_un_parte_apto_se_puede_rechazar_y_esa_es_la_feature
FAILED ...::test_f028_r22_el_parte_y_su_veredicto_se_guardan_antes_que_la_decision
FAILED ...::test_f028_r28_un_veredicto_metido_en_el_cuerpo_se_ignora
FAILED ...::test_f028_r13_el_motivo_se_recorta_por_los_extremos
FAILED ...::test_f028_r13_el_limite_del_motivo_lo_pone_el_dominio
FAILED ...::test_f028_r18_un_cierre_a_medias_no_cierra_la_puerta[pendiente]
FAILED ...::test_f028_r18_un_cierre_a_medias_no_cierra_la_puerta[dry_run_ok]
FAILED ...::test_f028_r18_un_cierre_a_medias_no_cierra_la_puerta[error]
FAILED ...::test_f028_r18_un_cierre_a_medias_no_cierra_la_puerta[None]
FAILED ...::test_f028_r15_lo_que_se_guarda_de_la_persona_es_el_oid_y_nada_mas
FAILED ...::test_f028_r37_cambiar_de_estado_no_toca_sharepoint_ni_el_erp
12 failed, 57 passed in 1.28s
```

Tras arreglarlos y **antes** de escribir la ruta: `70 passed`.

### 41.2 · La ruta, escrita en rojo primero

Los 19 casos de la sección nueva se escribieron **antes** que la ruta, y así
fallaban:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_http.py -q --tb=line
E   AttributeError: <module 'function_app' from '...\function_app.py'>
    has no attribute 'cambiar_estado_http'
tests/test_f028_estado_http.py:1294: AttributeError

E   AssertionError: el host no publica ninguna ruta «estado»
tests/utiles_rutas.py:43: AssertionError

=========================== short test summary info ===========================
FAILED ...::test_f028_r31_la_ruta_devuelve_200_con_las_seis_claves_del_contrato
FAILED ...::test_f028_r31_repetir_la_misma_decision_tambien_es_200
FAILED ...::test_f028_r31_un_cuerpo_que_no_es_json_es_400
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[sin-usuario-oid]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[sin-confirmado]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[confirmado-es-la-cadena-y-no-el-booleano]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[un-estado-que-no-existe]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[a-pendiente-no-se-vuelve]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[rechazo-sin-motivo]
FAILED ...::test_f028_r31_el_borde_responde_400_sin_escribir_nada[motivo-demasiado-largo]
FAILED ...::test_f028_r7_un_parte_cerrado_es_409_por_el_borde[cerrado]
FAILED ...::test_f028_r7_un_parte_cerrado_es_409_por_el_borde[ya_cerrada]
FAILED ...::test_f028_r31_sin_remesa_registrada_es_409
FAILED ...::test_f028_r31_sin_base_de_datos_es_503[fallo0]
FAILED ...::test_f028_r31_sin_base_de_datos_es_503[fallo1]
FAILED ...::test_f028_r53_el_log_lleva_hash_origen_destino_y_resultado_y_nada_mas
FAILED ...::test_f028_r53_un_rechazo_del_borde_tampoco_publica_lo_que_venia
FAILED ...::test_f028_r31_la_ruta_es_post_anonima_y_se_llama_estado
FAILED ...::test_f028_r32_la_ruta_no_mira_las_ventanas_de_escritura
19 failed, 70 passed in 0.98s
```

Y después de escribirla: `89 passed in 1.03s`.

---

## 42 · La lista de casos de T13, recontada

La verificación de T13 nombra doce casos. Están los doce, y **cada uno se
prueba dos veces**: contra el handler (levanta el error de dominio) y contra la
ruta (devuelve el código HTTP). Son cosas distintas y la campaña de mutación de
F-009 ya enseñó por qué: cambiar un `409` por un `503` en la traducción no
rompía nada porque ningún test recorría la ruta.

| Caso de T13 | Handler | Ruta |
|---|---|---|
| **200** al cambiar | `test_f028_r9_rechazar_un_parte_deja_su_fila_...` | `..._la_ruta_devuelve_200_con_las_seis_claves_del_contrato` |
| **200 `sin_cambios`** al repetir | `..._repetir_la_misma_decision_no_escribe_una_segunda_fila` (×2) | `..._repetir_la_misma_decision_tambien_es_200` |
| **400** sin `usuario_oid` | `..._r14_sin_usuario_oid_no_se_registra_nada` (×5) | `[sin-usuario-oid]` |
| **400** sin `confirmado: true` | `..._r29_sin_confirmacion_explicita_...` (×5) | `[sin-confirmado]` |
| **400** con `confirmado` como cadena `"true"` | `[la-cadena-y-no-el-booleano]` | `[confirmado-es-la-cadena-y-no-el-booleano]` |
| **400** con un estado que no es manual | `..._r10_un_estado_que_no_es_manual_...` (×8) | `[un-estado-que-no-existe]`, `[a-pendiente-no-se-vuelve]` |
| **400** con **rechazo sin motivo** | `..._r11_un_rechazo_sin_motivo_...` (×5) | `[rechazo-sin-motivo]` |
| **400** con motivo demasiado largo | `..._r13_un_motivo_demasiado_largo_...` | `[motivo-demasiado-largo]` |
| **409** si el parte está `cerrado` | `..._r7_un_parte_cerrado_no_admite_cambios_...` (×4) | `..._r7_un_parte_cerrado_es_409_por_el_borde` (×2) |
| **409** si la remesa no consta | `..._r31_sin_remesa_registrada_sube_referencia_no_consta` | `..._r31_sin_remesa_registrada_es_409` |
| **503** sin base | `..._r31_sin_base_de_datos_el_error_sube_sin_traducir` (×2) | `..._r31_sin_base_de_datos_es_503` (×2) |
| **Y en los rechazos, ni una escritura** | `repositorio.orden == []` en **los 30** | ídem en los **11** de la ruta |

Esa última fila es la que no se supone: `orden == []` afirma que **no se ha
tocado el puerto**, que es más fuerte que mirar si quedaron filas. En el 409
del parte cerrado se afirma además `repositorio.partes == []` y
`repositorio.cierres_consultados == [HASH]`: no solo no escribió, es que lo
único que hizo fue preguntar por la traza de cierre.

---

## 43 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2612 passed, 13 skipped, 1 deselected** | la propia suite (ver §44) |
| Tests ejecutados (arnés, raíz) | **62 passed** | `bash harness/init.sh` |
| De ellos, **de T13** | **89** en `test_f028_estado_http.py` (70 del handler + 19 de la ruta) | `pytest tests/test_f028_estado_http.py` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (301/301, umbral 80 %) | `python -m harness.cobertura --base dev --config harness/rigor.json` |
| **Mutantes generados** | **39** (alcance: 18 ficheros, 1.983 líneas) | `python -m harness.mutacion --feature F-028 --workers 1` |
| **Supervivientes** | **0** | ídem, `progress/mutacion_F-028.md` |
| **Timeouts** | **0** | ídem |
| **Tiempo de la suite** | **~26-40 s** (`api`) · 3,4 s (raíz) | la propia suite |
| **Tiempo de la campaña** | **948,3 s** en serie, 1 worker | `progress/mutacion_F-028.md` |

**Ningún superviviente que analizar**: cada una de las 39 mutaciones la cazó al
menos un test. Siete de ellas son de la ruta nueva y son justo las que F-009
enseñó a temer —`200 → 201`, `400 → 401`, los dos `409 → 410`, los dos
`503 → 504`—: sin los 19 casos de la sección de la ruta, esas siete habrían
sobrevivido, porque nadie recorría el `try/except`.

> La cifra de cobertura sube de 276 a 301 líneas entre la medición previa al
> commit y esta: es el mismo código, contado contra `dev` con el commit ya
> hecho. Las dos dan 100,0 %.

---

## 44 · Lo que está en rojo, y **no es de F-028**

`bash harness/init.sh` sale **ROJO**, y hay que decir exactamente por qué
porque no se arregla desde aquí.

```
FAILED tests/test_f010_integracion_expuesto.py::test_f010_r26_dice_la_consecuencia_visible_de_cada_ausencia
E   AssertionError: assert 'Sigrid no se toca' in '...'
```

**Ya estaba rojo en `HEAD` antes de tocar nada** —comprobado con `git stash`—,
y lo rompió el commit `6eb6d33` («INTEGRACION: los dos cierres reales, que el
documento seguia negando»), que reescribió `docs/INTEGRACION.md` y sacó de la
tabla la fila que contenía la frase «Sigrid no se toca» que ese test exige. Es
**documentación de F-010** y la decisión de qué debe decir ahora ese documento
no es del implementer de T13: se deja al líder.

Sus dos consecuencias, para que nadie las confunda con un problema de F-028:

- `[KO] servicio api: pytest en rojo` — ese caso y ningún otro;
- `[KO] PUERTA COBERTURA: 58.3 %` — **falso**. `init.sh` lanza la suite con
  `-x`, así que se para en ese fallo y mide la cobertura de media suite.
  Ejecutada entera (menos ese caso), la puerta da **100,0 % de 276 líneas**.

### 44.1 · Y lo mismo invalidaba la campaña de mutación

Esto importa más y por eso va aparte. El evaluador de `harness.mutacion` da un
mutante por **muerto** cuando la suite falla. Con un caso rojo **antes** de
mutar nada, la suite falla siempre, así que **todos** los mutantes del servicio
`api` salían «muertos» sin que ningún test los hubiera cazado. La primera
campaña lanzada en este encargo dio 39/39 muertos y **no vale**: era una
medición de la nada.

La campaña que se reporta se lanzó con ese único caso deselecionado —un
`pytest.ini` temporal en `services/postventa-api/`, **borrado al terminar y
nunca commiteado**— y con `--workers 1`, porque los worktrees de la campaña
paralela se crean desde `HEAD` y no verían ese fichero. La línea base, con esa
deselección, es **verde**: `2612 passed, 13 skipped, 1 deselected`.

---

## 45 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes y este bloque añade materia a dos de ellas. Nada
de esto se puede comprobar sin la base real y sin el ERP, y **lo ejecuta el
humano tras desplegar**:

- **T27.5** («un parte cerrado responde 409 y la web lo explica»): la mitad del
  backend ya se puede probar de verdad —`POST /api/estado` sobre un parte cuya
  incidencia conste cerrada tiene que devolver **409** y **no dejar ni una
  fila**—; la mitad de la web es del bloque 6.
- **T27.3** («aprobar → rechazar → aprobar deja tres filas»): con el endpoint
  puesto, ya se puede recorrer contra la base real. Ojo al contarlas: **el
  primer guardado de un parte deja también su fila de constancia**, así que un
  parte no apto recién subido y luego rechazado enseña **dos** filas, no una
  (§38.1). La consulta de solo lectura es la que fija T27.
- **Nuevo**: que el host publique la ruta al desplegar. Los tests la leen de
  `app.get_functions()`, que es lo que se despliega, pero un `curl -X POST
  .../api/estado` contra el entorno desplegado es la única comprobación de que
  el despliegue la recogió.

---

## 46 · Por dónde sigue · el encargo de T14

**T13 está cerrada. No se ha entrado en T14 ni en T15**, como pedía el encargo.

Lo que T14 se encuentra ya hecho:

- **el endpoint existe y su bloque `estado` está serializado**:
  `estado_serializado.py` publica `bloque_de_estado` (a partir de una decisión)
  y `bloque_de_estado_derivado` (a partir del veredicto y la situación, sin
  escribir nada), y el segundo es exactamente lo que T14 necesita para la
  respuesta de `/api/parte`;
- **`AnotaLosResultados` ya sabe consultar la situación y la traza de cierre**,
  así que T14 no tiene que ampliar el envoltorio;
- las **nueve líneas de `parte.py`** que `822100e` dejó son de T14 y ya están
  puestas (los dos métodos delegados del envoltorio). Lo que falta de T14 es
  cambiar el bloque `aprobacion` de la respuesta por `estado`, que es lo que
  retira la última llamada de producción a `consultar_aprobacion`.

Tres apuntes para quien lo coja:

- **`tests/test_f028_puertas.py` sigue siendo la red**, 48 casos, intacta desde
  el bloque 0. Si uno se pone rojo en T14 o T15, **parar y decirlo**.
- **Al añadir o quitar un endpoint hay que tocar `ENDPOINTS` de
  `tests/test_f010_endpoints_protegidos.py`** y su recuento. T15 retira
  `aprobar`: son 13 → 12 otra vez. Y lo que mira rutas ya no es de cada
  fichero: es `tests/utiles_rutas.py`.
- **T15 puede retirar el fichero de tests de `/api/aprobar` entero**, pero no
  el módulo `utiles_rutas.py`, que ahora usan los dos.

---

## 47 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ROJO**, por **un caso de F-010 ajeno a esta
  feature que ya estaba rojo en `HEAD`** (§44). Todo lo demás en verde.
- Cobertura de las líneas cambiadas: **100,0 % (276/276)**, medida con la suite
  entera.
- Árbol limpio, **2 commits** sobre `6eb6d33` (`2732199` T13 y el de este
  informe), los dos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado**: todo corre con
  `RepositorioEnMemoria` y dobles en memoria, sin red, sin BBDD y sin IA.

---

# F-028 · Estado del parte — informe del implementer · bloque 5, T14

> Encargo: **T14 y nada más** de `specs/F-028-estado-del-parte/tasks.md`.
> Parada obligada al terminar. **No se ha entrado en T15.**
>
> Rama `feature/F-028-estado-del-parte`, desde `2670936`. Rigor **`estandar`**:
> fase RED, puerta de cobertura y campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature, sin tocar
> `azure-apps/`, `infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

La línea base estaba **verde de verdad** al empezar —el rojo de
`test_f010_integracion_expuesto.py` que denunció §44 lo arregló el líder en
`2670936` reponiendo la frase, no aflojando el test—, así que este encargo no
ha necesitado deseleccionar nada ni para la suite ni para la campaña.

---

## 48 · Qué se ha hecho

| Tarea | Commit | Qué deja |
|---|---|---|
| **T14** | `96367a2` | `POST /api/parte` devuelve el bloque `estado` en vez de `aprobacion`, **sin una consulta más por parte** |

Lo que esto cierra: **`parte.py:131` era el último sitio de producción que
leía `consultar_aprobacion`**, y ya no lo lee. Comprobado con un `grep` sobre
`domain/`, `infrastructure/`, `application/`, `interface_adapters/` y
`function_app.py`: lo que queda de esa operación son **tres** sitios, y los
tres están en la lista de T15 —el puerto (`domain/ports/persistencia.py:147`),
el adaptador (`repositorio_pg.py:257`) y la delegación del envoltorio
(`parte.py`)—. De `bloque_de_aprobacion` queda un solo llamante,
`interface_adapters/api/aprobar.py`, que también retira T15.

---

## 49 · Ficheros tocados

### Creados

**Ninguno.**

### Modificados

| Ruta | Qué cambia |
|---|---|
| `interface_adapters/api/parte.py` | La respuesta cambia `aprobacion` por `estado`; dos imports; la sección nueva de la cabecera; la docstring de `AnotaLosResultados.consultar_aprobacion`, que prometía algo que ya no pasa |
| `application/pipelines/paso_persistencia.py` | La situación que ya leía **se deja en `ctx.situacion`** (§50.1), con el párrafo que dice por qué y qué situación es exactamente la que se deja |
| `tests/test_f028_estado_http.py` | **12 casos nuevos** en una sección T14, con sus tres ayudantes |
| `tests/test_f019_parte_http.py` | `CLAVES_DE_LA_RESPUESTA`: `aprobacion` → `estado`, y los dos comentarios que lo explican |
| `tests/test_f026_aprobar_http.py` | **Cinco casos retirados** con su recuadro fechado y su sustituto (§51), más los tres ayudantes y los tres imports que se quedaban sin llamante |
| `specs/F-028-estado-del-parte/tasks.md` | T14 marcada `[x]` |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git show --stat 96367a2`: en el diff **no aparece**
`domain/models/validacion.py`, ni `sql/04_validaciones.sql` (regla dura 1), ni
`domain/models/aprobacion.py` —o sea, ni `huella_de_veredicto` ni
`_normalizar`— (regla dura 2 y D9), ni `sql/10_aprobaciones.sql` ni
`sql/11_historico_estado.sql` (regla dura 3), ni `infrastructure/sigrid/`, ni
`infrastructure/sharepoint/`, ni el front, ni `azure-apps/`, ni
`harness/features.json`.

Y **`tests/test_f028_puertas.py` no está en el diff**: sus 48 casos siguen en
verde sin una sola edición desde el bloque 0, que es lo que este bloque tenía
que demostrar además de lo suyo.

---

## 50 · Decisiones de diseño, y la que hay que juzgar

### 50.1 · De dónde sale el estado sin gastar una consulta más

**Es la decisión del encargo**, porque la verificación de T14 es exactamente
esa: «volver a subir la remesa devuelve el estado de cada parte sin multiplicar
las consultas».

`paso_persistencia` ya leía la situación del parte —desde T8, para la regla de
constancia (R23)— y la tiraba al salir. Lo que se ha hecho es **dejarla en
`ctx.situacion`**, igual que hace `puerta_de_estado.exigir_parte_aprobado` en
los tres pasos del circuito desde T11, y que el handler la recoja con
`situacion_leida(contexto, almacen)`, que es el ayudante que T11 escribió
justo para esto.

El balance de consultas por parte en `POST /api/parte`, medido con el doble
que las cuenta:

| | Antes de T14 | Después |
|---|---|---|
| `consultar_situacion` | 1 (la constancia) | **1** (la constancia, reutilizada) |
| `consultar_aprobacion` | 1 (el bloque de la respuesta) | **0** |
| **Total** | **2** | **1** |

O sea: T14 **no añade** ninguna consulta y **quita una**. En una remesa real de
22 partes son 22 viajes menos por subida contra `psql-albaranes-rs9k2`, que es
un servidor **compartido** con albaranes y compañía. Importa decirlo con el
número porque el bloque 4 avisó de lo contrario: retirar el atajo del apto
costó **66 consultas por tanda** (`design.md` §6 y §11.1), y ese aviso sigue en
pie —es de las tres puertas del circuito, no de este endpoint—.

Lo fija `test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte`, que
afirma las dos mitades: `situaciones_consultadas == [HASH]` (una y no dos) y
`aprobaciones_consultadas == []` (ninguna a la tabla congelada).

**Las dos alternativas que se descartaron**, con lo que cuestan:

1. **Que el handler consulte la situación por su cuenta**, como hace
   `POST /api/estado`. Sale a **dos** consultas por parte, las mismas que
   costaba antes: no empeora, pero deja sobre la mesa la mitad de la mejora y
   la deja justo donde el diseño dijo que la iba a coger (§11.1: «el sitio
   donde se acota es el contexto»).
2. **Leer la situación una vez por parte y tanda**, que es lo que §11.1 propone
   si el coste molestara. Es más de lo que pide T14, toca a los tres pasos del
   circuito y no a este endpoint, y se queda como está escrito: pendiente de
   que la medición manual diga si hace falta.

### 50.2 · La situación que se reutiliza es la de **antes** de la fila de constancia, y es lo correcto

Es lo único fino del cambio y por eso va escrito en la docstring del paso.
`paso_persistencia` lee la situación y **después** puede escribir una fila de
constancia. El handler reutiliza la **de antes**.

No es un descuido: la derivación mira **tres hechos** —el veredicto, la última
decisión **humana** y la traza de cierre— y una constancia no es ninguno de los
tres (R26). Escribirla no puede cambiar el estado que se publica, y por eso
volver a preguntar solo costaría un viaje.

Quien sí necesita el `ultimo_estado_registrado` **de después** es
`POST /api/estado`, para encadenar el `estado_anterior` de la fila humana que
va a escribir; por eso ese handler vuelve a preguntar a propósito y lo dice
donde lo hace. **No se ha tocado.**

### 50.3 · La docstring que prometía algo que ya no pasa

`AnotaLosResultados.consultar_aprobacion` decía «la lee `/api/parte` para poder
contarla en su respuesta (R22)». Desde este commit no la lee nadie. La
delegación **se queda** —el puerto todavía la declara y quitarla sola rompería
la promesa de que el envoltorio implementa el puerto entero—, pero la docstring
dice ahora lo que es: código que sobrevive hasta T15. Un comentario que miente
es peor que no tenerlo.

### Desviaciones respecto a la spec

**Ninguna.** `design.md` §5 pide exactamente lo hecho —«`guardar_parte_http`
sustituye su bloque `aprobacion` por el bloque `estado`, leído después de
guardar»— y §8.2 lista `interface_adapters/api/parte.py` como fichero a
modificar. `paso_persistencia.py` no está en la lista de §8.2 **para T14**,
pero sí en la de la feature (lo modificó T8) y el cambio es de dos líneas: la
situación que ya leía se guarda en el hueco que T10 creó en `ContextoParte`
para esto mismo. Se declara aquí para que el reviewer lo mire con nombre
propio.

---

## 51 · Los tests de antes que han cambiado, y por qué

Son **seis**, y ninguno se ha «ajustado para que pase».

### 51.1 · Uno actualizado · `tests/test_f019_parte_http.py`

`CLAVES_DE_LA_RESPUESTA` enumera el contrato de `POST /api/parte` para que no
crezca ni cambie sin que alguien lo escriba ahí. Cambia `aprobacion` por
`estado`, que es **justo para lo que existe**: el test se puso rojo antes de
tocarlo y su rojo es la señal de que el contrato se movió. El comentario que lo
acompaña dice que no es un cambio de nombre y remite a
`tests/test_f028_estado_http.py` para lo que va dentro del bloque.

### 51.2 · Cinco retirados de `tests/test_f026_aprobar_http.py`

Los cinco probaban **el bloque de respuesta que T14 sustituye**, no un
comportamiento que siga existiendo. En su sitio queda un recuadro fechado con
qué probaba cada uno y **dónde está su sustituto**, escrito y en verde antes de
borrarlos:

| Retirado | Qué probaba | Sustituto en F-028 |
|---|---|---|
| `test_f026_r22_guardar_un_parte_aprobado_lo_dice_en_la_respuesta` | Que la respuesta cuenta lo que una persona aprobó | `test_f028_r39_un_parte_que_aprobo_una_persona_lo_dice_en_la_respuesta` |
| `test_f026_r22_un_parte_que_no_ha_aprobado_nadie_devuelve_null` | Que la clave está siempre y su valor dice qué pasa | `test_f028_r4_un_parte_que_nadie_ha_mirado_sale_pendiente_y_sin_firma` |
| `test_f026_r22_una_aprobacion_revocada_se_devuelve_como_revocada` | «Se decidió y dejó de valer» ≠ «nadie decidió» | `test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_firma_el_estado` |
| `test_f026_r22_la_aprobacion_se_lee_despues_de_guardar` | Que se lee **después** de guardar el veredicto | `test_f028_r22_el_estado_se_lee_despues_de_guardar_el_veredicto` |
| `test_f026_r38_la_respuesta_de_guardar_tampoco_publica_el_oid` | Que esa respuesta no lleva el `oid` | `test_f028_r42_la_respuesta_de_guardar_tampoco_publica_el_oid_ni_el_motivo` |

Los cuatro primeros se ponían **rojos** con un `KeyError: 'aprobacion'`. No se
han «adaptado» cambiándoles la clave, que es lo que los habría dejado verdes
probando otra cosa.

El quinto **seguía en verde**, y por eso merece su párrafo: comprobaba que no
se filtraba el `oid` de un bloque que a partir de T14 ya no se emite, así que
era verdad **por vacío** — la clase de test verde que tranquiliza sin medir
nada. Su sustituto comprueba lo mismo sobre el bloque que sí viaja y **además**
que no sale el motivo (R42, R52), que es el dato con más peligro porque lo
escribe una persona en texto libre y puede llevar dentro el nombre de un
cliente.

Con ellos se van `_guardar`, `_aprobacion_guardada`, la anotación de
`consultar_aprobacion` en `RepositorioQueAnotaElOrden` y los tres imports que
se quedaban sin llamante (`Aprobacion`, `MotivoRevocacion`, `CodigoMotivo`):
un ayudante sin llamantes es código muerto que el día de T15 alguien tendría
que volver a leer para borrarlo.

**Lo que NO se ha tocado de ese fichero**: todo lo de `POST /api/aprobar`, que
sigue vivo hasta T15 y sigue devolviendo su bloque `aprobacion`.

---

## 52 · Fase RED · la traza, pegada

Los 12 casos de la sección T14 se escribieron **antes** de tocar producción.
El intérprete es el del servicio (`services/postventa-api/.venv`): el del
repositorio no tiene `pydantic` y falla al cargar `conftest.py`.

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_http.py -q -k "..." --tb=short

E   AssertionError: assert {'aprobacion'...o_validacion'} == {'avisos', 'e...o_validacion'}
E     Extra items in the left set:
E     'aprobacion'
E     Extra items in the right set:
E     'estado'
____ test_f028_r4_un_parte_que_nadie_ha_mirado_sale_pendiente_y_sin_firma _____
tests\test_f028_estado_http.py:1633: in test_f028_r4_un_parte_que_nadie_ha_mirado_sale_pendiente_y_sin_firma
    assert respuesta["estado"] == {
E   KeyError: 'estado'
_________ test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte _________
tests\test_f028_estado_http.py:1758: in test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte
    assert repositorio.aprobaciones_consultadas == []
E   AssertionError: assert ['9f2b0011aabb'] == []
E     Left contains one more item: '9f2b0011aabb'
=========================== short test summary info ===========================
FAILED ...::test_f028_r38_guardar_un_parte_devuelve_el_estado_y_no_la_aprobacion
FAILED ...::test_f028_r4_un_parte_que_nadie_ha_mirado_sale_pendiente_y_sin_firma
FAILED ...::test_f028_r23_un_parte_apto_sale_aprobado_y_dice_que_lo_dijo_la_maquina
FAILED ...::test_f028_r39_un_parte_que_aprobo_una_persona_lo_dice_en_la_respuesta
FAILED ...::test_f028_r5_un_parte_apto_rechazado_a_mano_sale_rechazado
FAILED ...::test_f028_r18_un_parte_con_su_incidencia_cerrada_sale_cerrado
FAILED ...::test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_firma_el_estado
FAILED ...::test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte
FAILED ...::test_f028_r33_el_estado_de_la_respuesta_no_sale_del_cuerpo
9 failed, 2 passed in 1.02s
```

Después del cambio: `100 passed in 0.92s` en ese fichero.

El de la consulta —`assert ['9f2b0011aabb'] == []`— es el que cuenta de todo el
bloque: leído en voz alta dice **«la respuesta seguía yendo a la tabla
congelada de F-026 a preguntar por cada parte»**.

### Los dos que ya pasaban en rojo, y por qué es lo correcto

- `test_f028_r22_el_estado_se_lee_despues_de_guardar_el_veredicto`: el orden
  `parte → validacion → consulta_situacion → decision` ya era el de T8. Su
  valor no está en la fase RED sino en la de después: es el que se pone rojo si
  mañana alguien adelanta la lectura, y de eso hay prueba en §54 (mutante M6);
- `test_f028_r42_la_respuesta_de_guardar_tampoco_publica_el_oid_ni_el_motivo`:
  el bloque `aprobacion` tampoco los publicaba. Es el sustituto del quinto
  retirado (§51.2) y hereda su oficio, ahora sobre el bloque que sí viaja.

---

## 53 · La verificación de T14, recontada

T14 pide una cosa y se prueba entera:

| Lo que pide la tarea | Dónde se fija |
|---|---|
| La respuesta cambia `aprobacion` por `estado` | `test_f028_r38_guardar_un_parte_devuelve_el_estado_y_no_la_aprobacion` (las cinco claves exactas) y `CLAVES_DE_LA_RESPUESTA` de F-019 |
| **Subir la remesa otra vez devuelve el estado de cada parte** | Los cuatro estados: `..._r4_...pendiente...`, `..._r23_...apto_sale_aprobado...`, `..._r5_...rechazado_a_mano...`, `..._r18_...incidencia_cerrada_sale_cerrado` |
| **Sin una petición más por parte** | `test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte` |
| Ni el `oid`, ni el correo, ni el nombre, ni el motivo (R42, R52) | `test_f028_r42_la_respuesta_de_guardar_tampoco_publica_el_oid_ni_el_motivo`, que serializa la respuesta entera a JSON y busca dentro |

Y dos que no pide la tarea y sostienen el resto:

- `test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_firma_el_estado`: el
  parte es apto, así que está `aprobado`, **pero lo dice la máquina**. Es la
  distinción de R43 que no se ve a simple vista: quien comparase «el estado
  derivado» con «el estado de la fila» los vería coincidir y anunciaría
  «aprobado por una persona» con la fecha de una decisión que R19 ya tumbó;
- `test_f028_r33_el_estado_de_la_respuesta_no_sale_del_cuerpo`: se le mete al
  cuerpo un bloque `estado` y un bloque `aprobacion` ya hechos y **se ignoran
  los dos**. Si el estado viniera del cuerpo, quien compone la petición podría
  afirmar que un parte lo aprobó alguien que no lo aprobó.

---

## 54 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2.619 pasados, 13 saltados, 0 fallos** | `bash harness/init.sh` |
| Tests ejecutados (arnés, raíz) | **62 pasados** | `bash harness/init.sh` |
| De ellos, **nuevos de T14** | **12** en `tests/test_f028_estado_http.py` | `pytest tests/test_f028_estado_http.py` → 100 pasados en ese fichero |
| Tests **retirados** | **5**, todos de `tests/test_f026_aprobar_http.py`, con su sustituto (§51.2) | — |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 303/303, umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados / supervivientes** | automáticos **39 / 0** (0 timeouts, 1.000,5 s) · **a mano 6 / 0** | `python -m harness.mutacion --feature F-028 --workers 1` y §54.2 |
| **Tiempo de la suite** | **40,9 s** (`api`, bajo medición de cobertura) · 25,4 s sin ella · 4 s (raíz) | la propia suite |
| **Ruff** | `All checks passed` sobre los cinco ficheros tocados | `python -m ruff check` |

### Los supervivientes, y qué se hace con cada uno

**Ninguno**, ni en la campaña automática ni en la manual. 39 mutantes
evaluados, 39 muertos (informe en `progress/mutacion_F-028.md`), más 6 a mano,
6 muertos.

### 54.1 · La línea base estaba verde, y se comprobó antes de creerse el resultado

El encargo lo pedía expresamente y es lo primero que se hizo, porque el
evaluador de `harness.mutacion` da un mutante por **muerto** cuando la suite
falla: con la base en rojo, **todos** salen «muertos» sin que ningún test los
cace, que es lo que invalidó la primera campaña de T13.

Aquí no hizo falta deseleccionar nada. Antes de lanzarla:

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde;
- la suite del servicio, entera y a pelo → `2619 passed, 3 skipped` y **cero
  fallos**.

El caso de F-010 que estaba rojo lo arregló el líder en `2670936` reponiendo la
frase que `docs/INTEGRACION.md` había perdido. Queda anotado también en
`progress/mutacion_F-028.md`, porque ese fichero lo regenera la campaña y se
llevó por delante la nota equivalente de T13.

### 54.2 · Lo que hay que mirar de las evidencias: la campaña **no genera ni un mutante de T14**

De los 39 mutantes, **cero** caen en los dos ficheros que T14 toca, y los dos
están en alcance: `interface_adapters/api/parte.py` (57 líneas en alcance) y
`application/pipelines/paso_persistencia.py` (74). Los 39 son de los bloques 1
a 5 —`estado.py`, `function_app.py`, `ddl.py`, `repositorio_pg.py`,
`sentencias.py`, `estado.py` del borde y `estado_serializado.py`— y siguen
muriendo, que también es información: T14 no ha roto nada de lo ya probado.

**Por qué, medido.** Los operadores del mutador son comparación, lógico, `not`,
booleano, entero y aritmético. Lo que T14 cambia son **llamadas**: una clave de
diccionario que pasa a llamar a otra función, y una asignación a un campo del
contexto. Ni una comparación, ni un literal, ni un operador. Es el mismo hueco
que ya observaron el bloque 3 (§23.1) y el bloque 4 (§32.1), y **no** se ha
retorcido el código para darle material a la herramienta: escribir para el
medidor no es escribir para el problema.

Así que se ha mutado **a mano**, con el mismo método de los bloques 3 y 4 —se
aplica la mutación, se corre la suite entera del servicio, se restaura el
fichero; «muerto» = al menos un test falla—:

| # | Mutante aplicado a mano | Resultado | Quién lo caza |
|---|---|---|---|
| M1 | `parte.py` vuelve a publicar el bloque `aprobacion` de F-026 | **muerto** (9 fallos) | los 9 casos del contrato: los 8 de la sección T14 más `test_f019_r7_guardar_un_parte_devuelve_200_con_su_contrato` |
| M2 | `parte.py` **pregunta la situación otra vez** en vez de reutilizar la del contexto | **muerto** (2 fallos) | `test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte` y `test_f019_logs_sin_datos_personales` |
| M3 | `parte.py` deriva el estado **sin el veredicto** que acaba de guardar | **muerto** (3 fallos) | `..._r23_un_parte_apto_sale_aprobado...`, `..._r39_...aprobo_una_persona...`, `..._r5_...rechazado_a_mano...` |
| M4 | `parte.py` **nunca anuncia** que lo decidió una persona | **muerto** (2 fallos) | `..._r39_un_parte_que_aprobo_una_persona_lo_dice_en_la_respuesta`, `..._r5_...rechazado_a_mano...` |
| M5 | `paso_persistencia` **no deja la situación en el contexto** | **muerto** (2 fallos) | `test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte` (pasa a dos consultas) |
| M6 | `paso_persistencia` lee la situación **antes** de guardar el veredicto | **muerto** (3 fallos) | `test_f028_r22_el_estado_se_lee_despues_de_guardar_el_veredicto` y dos de la constancia |

**6 de 6 muertos.** El que más vale es **M2**, porque es el único que no se ve
mirando la respuesta: el JSON sale idéntico y lo único que cambia es que cada
parte cuesta un viaje más a un PostgreSQL compartido. Sin
`test_f028_r2_...` esa regresión entraría un día sin que nadie se enterara
hasta tener 22 partes y una remesa lenta. **M5** es su gemelo por el otro lado:
con la situación fuera del contexto, `situacion_leida` se cae al camino de la
derecha y vuelve a preguntar — o sea, el mismo coste, escrito en otro sitio.

El script de los seis está reproducido tal cual en la sesión y restaura cada
fichero al terminar; el árbol quedó limpio, comprobado con `git status`.

---

## 55 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes. T14 añade materia a una y **no crea ninguna
nueva**:

- **T27.2** («la aprobación que ya había en `postventa.aprobaciones` aparece
  sembrada y el parte sigue saliendo `aprobado`»): con T14 esto ya se puede
  comprobar **desde la propia pantalla**, sin consultar la base: al volver a
  subir la remesa, la respuesta de `POST /api/parte` de ese parte tiene que
  traer `"estado": {"estado": "aprobado", "decidido_por_persona": true, ...}`.
  Antes de T14 la respuesta hablaba de la tabla vieja y no decía nada del
  histórico sembrado.

Y una observación de despliegue que **no es una verificación manual sino un
aviso para el líder**, en §56.

**La base real y el ERP no se han tocado**: todo corre con
`RepositorioEnMemoria` y dobles en memoria, sin red, sin BBDD y sin IA.

---

## 56 · Lo que queda fuera del alcance de T14, y hay que decirlo

**El front sigue leyendo `aprobacion` y a partir de este commit no la va a
encontrar.** `services/postventa-front/js/app.js` (líneas 307, 516, 526, 550,
558) y `js/pipeline.js::semaforoDe` esperan el bloque viejo; con el nuevo
recibirán `undefined`. No revienta —`aprobacionVale(undefined, …)` devuelve
`false`— pero **el anillo de «aprobado por una persona» (R39) desaparecería**
y un parte que alguien aprobó a mano volvería a pintarse como pendiente.

Es exactamente lo que la spec secuencia: el front es el **bloque 6** (T16, T17
y T18), y `design.md` §5 ya lo declara como riesgo de despliegue con su
mitigación —«el front y la Function se despliegan juntos (`infra/`)»—. Se
apunta aquí porque el repositorio queda, entre T14 y el bloque 6, en un estado
que **no se debe desplegar a medias**. Ningún test del front se ha puesto rojo,
y eso no es tranquilizador: es que los tests del front prueban el front contra
sus propios dobles, no contra el contrato del backend.

**Tampoco es de T14** —y sigue intacto— nada de lo de T15: `/api/aprobar`, su
handler, `aprobacion_serializada.py`, la tabla `postventa.aprobaciones`, las
sentencias de F-026 y `domain/models/aprobacion.py`.

---

## 57 · Por dónde sigue · el encargo de T15

**T14 está cerrada. No se ha entrado en T15**, como pedía el encargo.

Lo que T15 se encuentra ya hecho:

- **`consultar_aprobacion` ya no la llama nadie en producción**. Quedan tres
  sitios y los tres están en la lista de T15: el puerto
  (`domain/ports/persistencia.py:147`), el adaptador
  (`repositorio_pg.py:257`) y la delegación de `AnotaLosResultados` en
  `parte.py`, cuya docstring ya dice que sobrevive solo hasta T15;
- **`bloque_de_aprobacion` tiene un solo llamante**,
  `interface_adapters/api/aprobar.py`, que T15 retira entero;
- **`tests/test_f026_aprobar_http.py` ya no prueba `/api/parte`**: lo que queda
  ahí es todo de `/api/aprobar`, así que T15 puede llevárselo de una pieza.

Cuatro apuntes para quien lo coja:

- **`tests/test_f028_puertas.py` sigue siendo la red**, 48 casos, intacta desde
  el bloque 0. Si uno se pone rojo en T15, **parar y decirlo**.
- **`tests/utiles_rutas.py` no se va con el fichero de F-026**: lo usan los dos
  (F-026 y F-028), y sin él `app.get_functions()` revienta a la segunda llamada
  (§40.3).
- **Al retirar la ruta `aprobar` hay que tocar `ENDPOINTS` de
  `tests/test_f010_endpoints_protegidos.py`** y su recuento: son 13 → 12.
- **`huella_de_veredicto` y `_normalizar` no se tocan** (D9 y §10): la usa
  `estado.py::_aprueba_lo_que_hay`, que es lo que hace que una aprobación deje
  de contar cuando el veredicto cambia (R19). Y ahora también la usan los tests
  de T14 para montar la aprobación vigente.

---

## 58 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las 303 líneas cambiadas. (La medición previa al
  commit dio 304/304 y esta, con el commit hecho, 303/303: es el mismo código
  contado contra `dev` desde dos sitios, y las dos dan 100,0 %.)
- Árbol limpio, **2 commits** sobre `2670936` (`96367a2` T14 y el de este
  informe), los dos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado**: todo corre con
  `RepositorioEnMemoria` y dobles en memoria, sin red, sin BBDD y sin IA.

---

# F-028 · Estado del parte — informe del implementer · bloque 5, T15

> Encargo: **T15 y nada más** de `specs/F-028-estado-del-parte/tasks.md`.
> Parada obligada al terminar. **No se ha entrado en el bloque 6.**
>
> Rama `feature/F-028-estado-del-parte`, desde `014fd6a`. Rigor **`estandar`**:
> fase RED, puerta de cobertura y campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature, sin tocar
> `azure-apps/`, `infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

**Es la tarea más destructiva de la feature**, y por eso lo primero que hay que
saber son las tres cosas que no se han tocado:

1. **`sql/10_aprobaciones.sql` no aparece en el diff.** Ni el fichero, ni el
   directorio `sql/` entero: `git diff 014fd6a -- services/postventa-api/infrastructure/persistencia/sql/` está **vacío**. La tabla
   `postventa.aprobaciones` sigue declarada, sigue aplicándose en el arranque y
   la semilla de `11_historico_estado.sql` sigue leyendo de ella. Y ahora hay
   además un test que comprueba que **nadie escribe** en ella.
2. **`tests/test_f028_puertas.py` no aparece en el diff.** Sus **48 casos**
   siguen intactos desde el bloque 0 y en verde. Ninguno se ha puesto rojo en
   ningún momento de este trabajo.
3. **Los 14 tests de la huella de F-026 se conservan byte a byte.** El diff de
   `tests/test_f026_aprobacion_dominio.py` **no añade ni una línea** que
   contenga `def test_` o un `assert`: las 29 líneas añadidas son cabecera e
   imports. `huella_de_veredicto` y `_normalizar` siguen en
   `domain/models/aprobacion.py`, con el mismo nombre y en el mismo módulo.

---

## 59 · Qué se ha hecho

| Tarea | Commit | Qué deja |
|---|---|---|
| **T15** | `a0b4ac7` | Retirado el código de F-026 que enumera la tarea; la tabla, congelada y vigilada; la cabecera del módulo, con su enmienda fechada |

Lo que esto cierra: **`POST /api/aprobar` ya no existe**, y con él se va el
último sitio del servicio que podía escribir una decisión humana en un almacén
que ya nadie lee. `design.md` §5 dice que `/api/estado` **sustituye** a
`/api/aprobar`, no que conviva con él, y esa era la parte peligrosa de dejarlo:
quien llamara al viejo habría dejado una aprobación en `postventa.aprobaciones`
sin ningún efecto sobre el estado del parte, y la pantalla le habría dicho que
sí lo tuvo.

Los endpoints del servicio vuelven de **trece a doce**.

---

## 60 · Ficheros tocados

### Creados

**Ninguno.** T15 solo resta.

### Borrados

| Ruta | Qué era |
|---|---|
| `interface_adapters/api/aprobar.py` | El handler de `POST /api/aprobar` (231 líneas) |
| `interface_adapters/api/aprobacion_serializada.py` | El bloque `aprobacion` de las respuestas (61) |
| `tests/test_f026_aprobar_http.py` | Los 28 casos del endpoint retirado (848) |
| `tests/test_f026_persistencia.py` | Los 35 casos de las sentencias retiradas (803) |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `domain/models/aprobacion.py` | **Solo quedan `huella_de_veredicto` y `_normalizar`**, más sus dos separadores. Cabecera nueva con la enmienda fechada (§62) |
| `domain/ports/persistencia.py` | Fuera `guardar_aprobacion` y `consultar_aprobacion` |
| `infrastructure/persistencia/sentencias.py` | Fuera `upsert_aprobacion`, `select_aprobacion`, `revocar_aprobacion_si_cambio` y sus tres listas de columnas |
| `infrastructure/persistencia/mapeo.py` | Fuera `fila_a_aprobacion`, `_codigos_desde_json` y `json_de_codigos_de_motivo` (§63.2) |
| `infrastructure/persistencia/repositorio_pg.py` | Fuera los dos métodos, y **`guardar_validacion` deja de revocar** (R57, §63.1) |
| `interface_adapters/api/parte.py` | `AnotaLosResultados` deja de delegar las dos operaciones |
| `function_app.py` | Fuera la ruta `aprobar`, su import y su entrada en la cabecera |
| `tests/utiles_pg.py` | `RepositorioEnMemoria` pierde las dos operaciones; `aprobaciones_consultadas` **se queda** y hay que leer por qué (§63.3) |
| `tests/utiles_sharepoint.py` | `RepositorioFalso` pierde `consultar_aprobacion` |
| `tests/test_f010_endpoints_protegidos.py` | 13 → **12** endpoints, con el porqué escrito |
| `tests/test_f026_aprobacion_dominio.py` | 41 → **14** casos: se conserva el bloque de la huella, intacto |
| `tests/test_f026_puertas.py` | Los **dos casos inertes** que el bloque 4 dejó anotados, retirados |
| `tests/test_f028_estado_dominio.py`, `test_f028_persistencia.py`, `test_f028_estado_http.py` | **18 casos nuevos** de T15 |
| `specs/F-028-estado-del-parte/tasks.md` | T15 marcada `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

**Balance: 518 líneas añadidas, 3.169 borradas** en 20 ficheros.

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff 014fd6a --stat`: en el diff **no aparecen**
`domain/models/validacion.py` ni `sql/04_validaciones.sql` (regla dura 1); ni
`sql/10_aprobaciones.sql` ni `sql/11_historico_estado.sql` ni ningún otro `.sql`
(regla dura 3); ni `infrastructure/sigrid/`, ni `infrastructure/sharepoint/`
(regla dura 2); ni `tests/test_f028_puertas.py`; ni el front; ni `azure-apps/`;
ni `harness/features.json`.

`huella_de_veredicto` y `_normalizar` **sí** están en el diff, porque el módulo
que los contiene se ha podado alrededor, pero **sus cuerpos no cambian**: el
único cambio dentro de `huella_de_veredicto` es la palabra «revocar» → «caducar»
en tres frases de su docstring, porque el mecanismo que la revocaba ya no
existe. Ni una línea de código.

---

## 61 · Fase RED · las trazas, pegadas

Los 18 casos de T15 se escribieron **antes** de tocar producción, en tres
tandas. El intérprete es el del servicio (`services/postventa-api/.venv`): el
del repositorio no tiene `pydantic` y falla al cargar `conftest.py`.

### 61.1 · El dominio · antes de podar `domain/models/aprobacion.py`

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_dominio.py -q -k "t15" --tb=short

_ test_f028_t15_del_dominio_de_f026_no_queda_nada_de_la_decision[admite_circuito] _
tests\test_f028_estado_dominio.py:985: in test_f028_t15_del_dominio_de_f026_no_queda_nada_de_la_decision
    assert not hasattr(modulo, nombre)
E   AssertionError: assert not True
E    +  where True = hasattr(<module 'domain.models.aprobacion' from '...\domain\models\aprobacion.py'>, 'admite_circuito')
_______ test_f028_t15_la_huella_y_su_normalizador_siguen_donde_estaban ________
tests\test_f028_estado_dominio.py:999: in test_f028_t15_la_huella_y_su_normalizador_siguen_donde_estaban
    assert modulo.__all__ == ["huella_de_veredicto"]
E   AssertionError: assert ['MOTIVOS_APR...vigente', ...] == ['huella_de_veredicto']
E     At index 0 diff: 'MOTIVOS_APROBABLES' != 'huella_de_veredicto'
E     Left contains 6 more items, first extra item: 'Aprobacion'
__ test_f028_t15_la_cabecera_explica_que_la_decision_vive_ahora_en_estado_py __
tests\test_f028_estado_dominio.py:1018: in ...
    assert "Enmienda" in documentacion
E   AssertionError: assert 'Enmienda' in 'La aprobación humana de un parte que la validación mandó a revisión (F-026).\n\n**Dominio puro.** ...'
=========================== short test summary info ===========================
FAILED ...[Aprobacion]  FAILED ...[MOTIVOS_APROBABLES]  FAILED ...[MotivoRevocacion]
FAILED ...[admite_circuito]  FAILED ...[es_aprobable]  FAILED ...[esta_vigente]
FAILED ...::test_f028_t15_la_huella_y_su_normalizador_siguen_donde_estaban
FAILED ...::test_f028_t15_la_cabecera_explica_que_la_decision_vive_ahora_en_estado_py
8 failed, 47 deselected in 0.62s
```

Después de reescribir el módulo: `8 passed in 0.41s`.

### 61.2 · La persistencia · antes de retirar las sentencias y el puerto

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_persistencia.py -q -k "t15" --tb=short

____ test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026 ____
    assert {nombre: textos for nombre, textos in culpables.items() if textos} == {}
E   AssertionError: assert {'sentencias....probaciones']} == {}
E     Left contains 1 more item:
E     {'sentencias.py': ['aprobaciones', 'aprobaciones', 'aprobaciones']}
__________ test_f028_t15_las_tres_sentencias_de_f026_se_han_retirado __________
    assert not hasattr(sentencias, nombre), nombre
E   AssertionError: upsert_aprobacion
________ test_f028_t15_el_puerto_ya_no_declara_las_operaciones_de_f026 ________
    assert not hasattr(RepositorioPartesPort, nombre), nombre
E   AssertionError: guardar_aprobacion
__________ test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada __________
    assert conexion.veces_con(f"{ESQUEMA}.aprobaciones") == 0
E   AssertionError: assert 1 == 0
E    +  where 1 = veces_con('postventa.aprobaciones')
=========================== short test summary info ===========================
FAILED ...::test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026
FAILED ...::test_f028_t15_las_tres_sentencias_de_f026_se_han_retirado
FAILED ...::test_f028_t15_el_mapeo_ya_no_sabe_reconstruir_una_aprobacion
FAILED ...::test_f028_t15_el_puerto_ya_no_declara_las_operaciones_de_f026
FAILED ...::test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada
5 failed, 1 passed, 45 deselected in 0.86s
```

El `assert 1 == 0` es el de R57, y leído en voz alta dice lo que todavía pasaba:
**cada guardado de un veredicto seguía tocando la tabla congelada**, 22 veces
por remesa.

El que ya pasaba en rojo es
`test_f028_t15_la_tabla_de_f026_sigue_declarada_en_el_ddl`, y eso es **lo
correcto**: es un control negativo de la regla dura 3, tiene que estar verde
antes y después. Su fase útil no es esta, es la de después — lo mata el mutante
M8 (§65).

### 61.3 · El borde · antes de retirar el endpoint

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_estado_http.py -q -k "t15" --tb=short

_____________ test_f028_t15_los_dos_modulos_de_f026_ya_no_existen _____________
    assert importlib.util.find_spec(modulo) is None, modulo
E   AssertionError: interface_adapters.api.aprobar
_____________ test_f028_t15_el_host_ya_no_publica_la_ruta_aprobar _____________
    assert "aprobar" not in publicadas
E   AssertionError: assert 'aprobar' not in {'health': <...>, 'split': <...>, ...}
________________ test_f028_t15_function_app_ya_no_sabe_aprobar ________________
    assert not hasattr(function_app, "aprobar")
E   AssertionError: assert not True
________ test_f028_t15_el_envoltorio_de_parte_ya_no_delega_lo_de_f026 _________
    assert not hasattr(AnotaLosResultados, "guardar_aprobacion")
E   AssertionError: assert not True
4 failed, 100 deselected in 1.15s
```

Después de la retirada: los cuatro en verde, y la suite entera del servicio
también.

---

## 62 · La cabecera de `domain/models/aprobacion.py`, que era medio encargo

`design.md` §8.2 pide que «la cabecera del módulo explique que la decisión vive
ahora en `estado.py`», y el encargo añade el patrón de este repositorio: **no se
borra la premisa, se dice qué la sustituyó y cuándo**.

Lo que hay, y es lo que el reviewer tiene que juzgar:

- un recuadro **`Enmienda del 2026-09-16 · F-028 T15`** que enumera lo que el
  módulo era —las seis piezas retiradas, con `admite_circuito` señalado como
  «el criterio con el que las tres puertas dejaban pasar un parte al circuito»—;
- **la premisa de F-026 citada literal**, entre comillas y sin tocar: «*La
  aprobación se registra al lado del veredicto, nunca encima (R11)…*». Sigue
  siendo verdad, y decirlo importa: lo que cambió no es que F-004 vuelva a ser
  pisable, es **dónde vive la segunda cosa**;
- **los dos motivos de la mudanza**, que son los de `requirements.md` §0.4 y
  §0.5: que F-026 no podía rechazar un parte apto, y que su tabla tiene una
  fila por parte, así que un ciclo aprobar → rechazar → aprobar no dejaba rastro
  del rechazo;
- la frase que cierra la ambigüedad para quien llegue dentro de seis meses:
  **«la tabla no se ha borrado»**, con el porqué —guarda decisiones de personas
  reales y el DDL del histórico la siembra en cada arranque—;
- y una sección nueva que explica **por qué sobrevive la huella y por qué
  sobrevive aquí**, con la única diferencia de fondo respecto a F-026: antes la
  caducidad se resolvía **al escribir** y ahora se resuelve **al derivar**.

El test que lo fija es
`test_f028_t15_la_cabecera_explica_que_la_decision_vive_ahora_en_estado_py`, y
exige las cuatro cosas por separado: la palabra «Enmienda», la fecha, el nombre
del módulo que releva y **la cita de la premisa**. Una cabecera que se limitara
a borrar los párrafos viejos no pasa.

> **Un detalle que costó un rojo y merece quedar escrito.** La primera versión
> de la cabecera decía que `postventa.aprobaciones` «se pisa con `ON CONFLICT DO
> UPDATE`», y eso puso rojo a
> `test_f005_arquitectura.py::test_f005_r31_solo_el_adaptador_de_persistencia_escribe_sql`,
> que barre el código de producción buscando verbos SQL fuera de
> `infrastructure/persistencia/`. El test tenía razón y el arreglo fue decir lo
> mismo sin el SQL: «tiene una fila por parte y cada decisión nueva sustituye a
> la anterior». **No se tocó el test.**

---

## 63 · Decisiones de diseño, y las tres que hay que juzgar

### 63.1 · `guardar_validacion` vuelve a ser **una sola sentencia** (R57)

Es la decisión de más peso operativo del encargo y no está en la lista literal
de T15 —lo está en `design.md` §8.2, «`guardar_validacion` deja de revocar
(R57)»— pero **no había alternativa**: T15 retira
`revocar_aprobacion_si_cambio`, y su único llamante era esa operación.

Lo que había: el guardado del veredicto llevaba colgada una segunda sentencia en
la misma transacción, porque F-026 resolvía la vigencia de la decisión humana
**al escribir** (su D-F). Lo que hay ahora: nada. F-028 la resuelve **al
derivar** —`estado.py::_aprueba_lo_que_hay` compara la huella apuntada en el
histórico con la del veredicto de ahora, cada vez que hace falta el estado
(R19)—.

**La preocupación que justificaba meterlas en una sola transacción desaparece
por construcción**, y eso va escrito en la docstring: el argumento de F-026 era
«una ventana, corta pero real, en la que el veredicto nuevo ya está guardado y
la aprobación del viejo sigue viva». Ya no hay nada que actualizar, así que no
hay ventana.

Y tiene precio en el sitio donde más se nota. `guardar_validacion` es el camino
**más transitado del servicio**: una vez por parte y por subida, **22 veces en
una remesa real de Mirasierra**. Cada una de esas 22 hacía un `UPDATE` de más
contra `psql-albaranes-rs9k2`, que es un servidor **compartido** con albaranes y
compañía. Ya no.

Lo fija `test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada`, que afirma
las tres mitades: cero sentencias contra la tabla congelada, una contra
`validaciones`, y **`len(conexion.ejecutadas) == 1`**. Esta última es la que
cuenta: `_escribir` ejecuta la sentencia que se le pasa **más las que le cuelguen
en `ademas`**, así que contar las ejecutadas es lo único que distingue «se retiró
la llamada» de «se retiró la función y alguien la repuso por otro camino». Lo
mata el mutante M5 (§65).

### 63.2 · Tres piezas retiradas que T15 **no enumera**, y por qué se van igual

Se declaran aquí con nombre propio para que el reviewer las juzgue una a una.
Las tres son **la mitad interna** de algo que T15 sí enumera, igual que
`_COLUMNAS_APROBACION_VIVA`, `_COLUMNAS_REVOCACION` y `_COLUMNA_JSONB_APROBACION`
—que tampoco están en la lista y son el cuerpo de `upsert_aprobacion`—:

| Retirado | De quién era la mitad | Por qué no se queda |
|---|---|---|
| `mapeo._codigos_desde_json` | de `fila_a_aprobacion` (en la lista) | Privado y sin ningún otro llamante. Un `_ayudante` sin llamantes es código muerto que además se queda sin cobertura |
| `mapeo.json_de_codigos_de_motivo` | de `upsert_aprobacion` (en la lista) | Su único llamante era el `upsert`. Su docstring entera habla de «la fila de la aprobación», así que dejarla viva es dejar un comentario que miente sobre una función que nadie llama |
| El import de `ParteNoAprobable` en `function_app.py` | del `except` de la ruta `aprobar` | Sin la ruta, es un import sin uso y `ruff` lo canta (F401) |

**Lo que NO se ha retirado aunque haya quedado sin llamante**, porque ahí la
línea sí está fuera de T15 y no la cruzo por mi cuenta:

- **`domain/models/errores.py::ParteNoAprobable`.** Era el 409 de «este parte no
  se puede aprobar», y su único emisor era `aprobar.py`. F-028 no tiene ese
  concepto: una persona puede mover a `aprobado` o a `rechazado` **cualquier**
  parte que no esté `cerrado` (R9, R10), y el único 409 que queda es el del
  parte cerrado. O sea que la excepción está viva, documentada en el inventario
  de la cabecera de `errores.py` y **nadie la levanta**. `design.md` §8.2 solo
  manda **añadir** dos errores a ese fichero, no quitar ninguno, y T15 no la
  nombra. **Queda para el líder o para T24**, que es quien escribe las enmiendas
  de `specs/F-026-aprobacion-humana/requirements.md`.
- **`repositorio_pg._escribir(..., ademas=...)`.** Se queda sin su único
  llamante al retirar la revocación. Es un mecanismo genérico del adaptador —«N
  sentencias en una transacción»— con su docstring propia, no una pieza de
  F-026, y su línea se sigue ejecutando en todos los guardados con la tupla
  vacía, así que no deja hueco de cobertura. **No lo quito porque no es mío**,
  pero lo digo para que no se lea como un descuido.

### 63.3 · `aprobaciones_consultadas` se queda en el doble, y es lo peor del encargo

Es lo que más honestamente hay que contar. `RepositorioEnMemoria` tenía
`aprobaciones_consultadas`, y **dos tests de F-028 afirman sobre ella**:

- `test_f028_r33_ninguna_puerta_consulta_ya_la_tabla_de_f026`, en
  `tests/test_f028_puertas.py` —que es **la red de seguridad de T1 y no se
  toca**—;
- `test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte`, en
  `tests/test_f028_estado_http.py`.

Al retirar `consultar_aprobacion` del doble, esa lista **ya no puede crecer**.
Las dos aserciones pasan de ser ciertas **por comportamiento** a ciertas **por
construcción**: es exactamente la clase de test verde que tranquiliza sin medir
nada, y el informe del bloque 4 (§30.1) y el de T14 (§51.2) retiraron sendos
tests justo por eso.

Aquí no se pueden retirar: uno de los dos es la red de seguridad que el encargo
prohíbe tocar, y el otro es de T14. Así que lo que se ha hecho es:

1. **dejar el atributo**, con un comentario en `utiles_pg.py` que dice
   literalmente que se queda vacío para siempre, por qué, y cuál es el control
   que de verdad vigila la tabla;
2. **escribir ese control**, que es
   `test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026` —y
   que es más fuerte que lo que había: no mira una función retirada, mira
   **todas** las cadenas que compone la capa de persistencia—.

**Lo que el reviewer tiene que decidir** es si las dos aserciones vacías se
quedan como están. Mi lectura es que sí, y por dos motivos: retirarlas obliga a
editar la red de seguridad del bloque 0, y el día que alguien repusiera
`consultar_aprobacion` volverían a medir. Pero son dos aserciones que hoy no
prueban nada, y decirlo es lo que impide que dentro de un año alguien las cuente
como cobertura.

### 63.4 · El control de la tabla mira el **árbol sintáctico**, no el texto

`test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026` recorre
los `.py` de `infrastructure/persistencia/` y recoge **las cadenas que el módulo
usa, saltándose las docstrings**. Es el método que ya usaron el bloque 0 (§5) y
T13 (§38.2), y hace falta por lo mismo: las cabeceras de este repositorio
**explican** por qué la tabla se congela, y nombrarla para explicarlo no es
escribir en ella. Un control sobre el texto crudo se habría puesto rojo por la
cabecera de `ddl.py`, y el arreglo habría sido dejar de explicarlo.

El `.sql` de la semilla queda fuera del barrido a propósito: es la **lectura**
que la regla dura 3 manda conservar, y es SQL, no un módulo.

### Desviaciones respecto a la spec

**Ninguna respecto a `design.md` §8.2**, que lista uno a uno todos los ficheros
tocados —incluido `guardar_validacion` (R57) y los «tests de F-026» que se
sustituyen—. Las tres retiradas de §63.2 son extensiones declaradas de la lista
literal de `tasks.md` T15, y están ahí para que se juzguen por nombre.

---

## 64 · Los 90 tests retirados, uno a uno, con su sustituto

El encargo lo pide expresamente: **un test que desaparece sin sustituto es
cobertura que se pierde en silencio**. Van los cuatro ficheros.

### 64.1 · `tests/test_f026_aprobacion_dominio.py` · 25 retirados, 14 conservados

Los 14 conservados son **el bloque entero de la huella** (T3 de F-026), byte a
byte. Los 25 retirados:

| Retirado (bloque) | Sustituto en F-028 |
|---|---|
| `r6_los_motivos_aprobables_son_exactamente_dos` (T2) | **Sin sustituto, y a propósito** — ver el recuadro de abajo |
| `r6_un_parte_con_observaciones_manuscritas_es_aprobable` (T2) | ídem |
| `r6_un_parte_con_firma_no_humana_es_aprobable` (T2) | ídem |
| `r8_un_parte_con_los_dos_motivos_aprobables_es_aprobable` (T2) | ídem |
| `r7_un_parte_sin_codigo_de_obra_no_es_aprobable` (T2) | ídem |
| `r7_un_parte_sin_numero_de_incidencia_no_es_aprobable` (T2) | ídem |
| `r9_un_motivo_no_aprobable_contamina_al_resto` (T2) | ídem |
| `r8_un_no_apto_sin_motivos_no_es_aprobable` (T2) | ídem |
| `r7_una_aprobacion_de_lo_inaprobable_tampoco_abriria_la_puerta` (T2) | ídem |
| `r10_un_parte_que_ya_es_apto_no_se_aprueba` (T2) | **Lo contrario** está probado: `test_f028_r5_un_rechazo_humano_manda_sobre_un_veredicto_apto` y `test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta`. Es la feature |
| `r10_sin_veredicto_no_hay_nada_que_aprobar` (T2) | `test_f028_r4_sin_veredicto_el_parte_esta_pendiente` |
| `r11_la_aprobacion_no_toca_el_veredicto_de_f004` (T2) | Regla dura 1: `domain/models/validacion.py` no está en el diff de la feature entera, y `test_f028_r17_nadie_mas_deriva_el_estado_del_parte` lo vigila desde el otro lado |
| `r2_una_aprobacion_recien_hecha_esta_vigente` (T4) | `test_f028_r20_la_misma_huella_conserva_la_aprobacion` |
| `r31_una_aprobacion_revocada_no_esta_vigente` (T4) | `test_f028_r19_una_aprobacion_de_otro_veredicto_no_cuenta` — F-028 no revoca, **caduca al derivar** |
| `r24_sin_aprobacion_no_hay_vigencia` (T4) | `test_f028_r26_una_fila_de_maquina_no_decide_nada` y `test_f028_r2_una_situacion_vacia_es_un_parte_del_que_no_consta_nada` |
| `r33_la_revocacion_no_borra_quien_decidio_ni_cuando` (T4) | `test_f028_r21_el_insert_del_historico_no_lleva_ningun_on_conflict` y `..._r21_el_insert_tampoco_actualiza_ni_borra_por_otro_camino`: el histórico no borra **nada**, que es más fuerte |
| `r34_el_motivo_de_revocacion_es_una_etiqueta_corta_y_cerrada` (T4) | **Sin sustituto**: no hay revocación, así que no hay motivo de revocación que acotar. Lo que sí se acota es el motivo **de la persona**, en `test_f028_r13_el_limite_del_motivo_lo_declara_el_dominio` |
| `r23_el_apto_de_siempre_sigue_entrando_en_el_circuito` (T4) | `test_f028_r3_un_parte_apto_nace_aprobado` y `test_f028_r3_el_parte_apto_sigue_pasando_las_tres_puertas` |
| `r23_un_no_apto_con_aprobacion_viva_entra_en_el_circuito` (T4) | `test_f028_r9_una_aprobacion_humana_rescata_un_parte_no_apto` y `test_f028_r9_un_parte_no_apto_que_una_persona_aprobo_pasa` |
| `r25_un_no_apto_sin_aprobacion_no_entra` (T4) | `test_f028_r4_un_parte_no_apto_nace_pendiente` y los seis casos R33 de `test_f028_puertas.py` |
| `r31_un_no_apto_con_aprobacion_revocada_no_entra` (T4) | `test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_abre_nada` |
| `r30_una_aprobacion_de_otro_destino_no_sirve` (T4) | `test_f028_r19_una_aprobacion_de_otro_veredicto_no_cuenta`: F-028 no compara destinos, compara **la huella del veredicto entero** —que incluye el destino, los motivos, la firma, las observaciones y los dos campos decisivos—. Es **más estrecho**, no más laxo |
| `r25_sin_validacion_no_se_admite_nada` (T4) | `test_f028_r4_sin_veredicto_el_parte_esta_pendiente` + los tres R34 de `test_f028_puertas.py` |
| `r10_un_apto_con_destino_raro_no_entra_por_la_puerta_de_siempre` (T4) | `test_f028_r3_un_apto_con_otro_destino_no_nace_aprobado` |
| `una_aprobacion_no_se_puede_modificar_despues_de_creada` (huecos) | `test_f028_r21_una_decision_es_inmutable` y `test_f028_r33_la_situacion_leida_del_almacen_es_inmutable` |

> **Los nueve «sin sustituto» de T2 no son cobertura perdida: son una regla que
> F-028 deroga a propósito.** F-026 preguntaba «¿es este parte **aprobable**?» y
> respondía mirando sus motivos: `observaciones_manuscritas` y `firma_no_humana`
> sí; `codigo_obra_no_legible` y `numero_incidencia_no_legible` no. F-028 no
> tiene esa pregunta (D1–D9, R9 y R10): **una persona puede mover a `aprobado` o
> a `rechazado` cualquier parte que no esté `cerrado`**, y lo que impide que un
> parte sin código de obra acabe archivado no es un veto en el borde, son las
> tres puertas del circuito y el veredicto de F-004, que sigue intacto. El único
> 409 que sobrevive es el del parte cerrado, y tiene seis casos propios entre
> `test_f028_r7_un_parte_cerrado_no_admite_cambios_ni_escribe_nada` y
> `test_f028_r7_un_parte_cerrado_es_409_por_el_borde`.

### 64.2 · `tests/test_f026_persistencia.py` · el fichero entero, 35 casos

**Los 35 probaban las cuatro sentencias retiradas, su mapeo o su adaptador.** No
queda ni uno que hable de algo que siga existiendo, y por eso el fichero se va
de una pieza. Agrupados por lo que probaban:

| Retirados | Qué probaban | Sustituto en F-028 |
|---|---|---|
| `r17_aprobar_dos_veces_actualiza_la_misma_fila`, `r17_volver_a_aprobar_deja_la_aprobacion_viva` | Que el `upsert` **pisa** la fila anterior | `test_f028_r21_el_insert_del_historico_no_lleva_ningun_on_conflict` y `test_f028_r21_el_insert_tampoco_actualiza_ni_borra_por_otro_camino`, que prueban **lo contrario y es el punto de la feature**: el histórico acumula |
| `el_upsert_no_interpola_ni_un_valor_en_el_texto`, `el_upsert_tiene_tantos_marcadores_como_parametros`, `la_revocacion_tiene_tantos_marcadores_como_parametros` | Que ningún valor se pega al SQL | `test_f028_r22_el_insert_escribe_las_siete_columnas_de_la_fila` y los controles de `test_f028_persistencia.py` sobre `insert_decision_estado` |
| `r14_lo_que_se_guarda_son_codigos_de_motivo_y_no_textos`, `los_codigos_se_serializan_como_lista_de_cadenas`, `solo_la_columna_de_motivos_se_declara_como_jsonb` | El `jsonb` de `motivos_aprobados` | **Sin sustituto, y no hace falta**: `historico_estado` **no tiene ninguna columna `jsonb`** ni ninguna binaria, y eso lo comprueba `tests/test_f028_ddl_historico.py`. Es una columna que ya no existe |
| `r15_el_upsert_no_lleva_ni_una_letra_del_texto_manuscrito` | Que el papel no entra en esa tabla | `test_f028_r52_una_decision_no_tiene_hueco_para_datos_del_papel` y `test_f028_r52_registrar_una_decision_no_saca_el_motivo_ni_el_oid` |
| `r33_la_revocacion_es_un_update_y_nunca_un_delete`, `r30_la_revocacion_solo_toca_lo_vigente_y_lo_que_cambio`, `r30_la_huella_viaja_como_parametro_y_no_pegada_al_sql`, `r34_el_motivo_de_la_revocacion_es_una_etiqueta_corta` | La sentencia de revocación | **Sin sustituto: no hay revocación.** La caducidad se resuelve al derivar, y eso lo prueban `test_f028_r19_una_aprobacion_de_otro_veredicto_no_cuenta` y `test_f028_r20_la_misma_huella_conserva_la_aprobacion` |
| `el_select_busca_por_hash_con_parametro`, `el_select_lee_las_mismas_columnas_que_escribe_el_upsert` | El `SELECT` de la tabla | `test_f028_la_situacion_se_resuelve_con_un_union_all_de_dos_limit_1` y `test_f028_r25_la_consulta_ordena_por_instante_y_desempata_por_contador` |
| `fila_a_aprobacion_reconstruye_la_dataclass_con_sus_enum`, `fila_a_aprobacion_admite_el_jsonb_como_texto`, `r33_una_fila_revocada_vuelve_del_mapeo_como_revocada`, `lo_que_escribe_el_upsert_vuelve_igual_por_el_mapeo` | `fila_a_aprobacion` | `test_f028_una_fila_humana_vuelve_al_dominio_entera`, `test_f028_r24_una_fila_de_maquina_vuelve_sin_autor_y_lo_dice` y `test_f028_un_estado_que_el_dominio_no_conoce_revienta_al_mapear` |
| `un_esquema_hostil_no_llega_al_sql`, `las_tres_sentencias_van_al_esquema_propio` | Que el esquema se valida y nada va sin cualificar | `test_f028_el_insert_solo_escribe_en_el_historico` y los control negativos de esquema de `tests/test_f028_ddl_historico.py` |
| `el_adaptador_cumple_el_puerto_ampliado`, `el_doble_en_memoria_tambien_cumple_el_puerto_ampliado` | Que adaptador y doble cumplen el puerto | `test_f028_el_adaptador_cumple_el_puerto_ampliado` y `test_f028_el_doble_en_memoria_tambien_cumple_el_puerto_ampliado` — **mismo nombre, mismo oficio, puerto nuevo** |
| `guardar_la_aprobacion_ejecuta_el_upsert`, `consultar_una_aprobacion_que_no_existe_devuelve_none`, `consultar_devuelve_la_aprobacion_del_parte` | Las dos operaciones del adaptador | `test_f028_registrar_una_decision_ejecuta_el_insert`, `test_f028_la_situacion_de_un_parte_sin_ninguna_fila_viene_vacia` y `test_f028_la_situacion_trae_la_ultima_decision_humana` |
| `r30_guardar_una_validacion_revoca_en_la_misma_operacion`, `r30_las_dos_sentencias_van_en_una_sola_transaccion`, `r30_la_revocacion_compara_con_la_huella_del_veredicto_guardado`, `r32_revalidar_sin_cambios_manda_la_misma_huella`, `r30_un_veredicto_distinto_manda_otra_huella`, `r30_corregir_el_numero_de_incidencia_manda_otra_huella`, `r33_la_revocacion_que_se_ejecuta_no_borra_la_fila`, `r34_lo_que_se_escribe_como_motivo_es_la_etiqueta_corta` | La revocación enganchada al guardado | **`test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada`**, que afirma justo lo contrario, más los cuatro casos de caducidad del dominio (`r19`, `r20`) que prueban que el resultado no se pierde |
| `el_log_de_la_aprobacion_no_lleva_ni_el_oid_ni_la_huella` | Que el log no publica datos personales | `test_f028_r52_registrar_una_decision_no_saca_el_motivo_ni_el_oid`, `test_f028_r52_leer_la_situacion_tampoco_los_saca` y `test_f028_el_log_si_registra_lo_que_hace_falta_para_operar` |

### 64.3 · `tests/test_f026_aprobar_http.py` · el fichero entero, 28 casos

Todos son de `POST /api/aprobar`. **Los 28 tienen sustituto en
`tests/test_f028_estado_http.py`**, y no por casualidad: el fichero de T13 se
escribió recorriendo esta misma lista.

| Retirado | Sustituto en F-028 |
|---|---|
| `r2_aprobar_registra_quien_y_cuando_y_lo_devuelve` | `r9_rechazar_un_parte_deja_su_fila_con_quien_cuando_y_por_que` |
| `r2_el_parte_y_su_veredicto_se_guardan_antes_que_la_aprobacion` | `r22_el_parte_y_su_veredicto_se_guardan_antes_que_la_decision` |
| `r2_la_aprobacion_lleva_la_huella_del_veredicto_que_se_guardo` | `r22_el_estado_anterior_sale_de_la_ultima_fila_del_historico` y `r19_aprobar_lo_que_aprobo_otro_veredicto_si_escribe_fila` |
| `r4_sin_usuario_oid_no_se_registra_nada` (×5) | `r14_sin_usuario_oid_no_se_registra_nada` (×5) |
| `r4_sin_confirmacion_explicita_no_se_registra_nada` (×5) | `r29_sin_confirmacion_explicita_no_se_registra_nada` (×5) |
| `r9_un_motivo_no_aprobable_es_409_sin_escribir_nada` | **Derogado** (§64.1). Lo que queda de 409 es `r7_un_parte_cerrado_no_admite_cambios_ni_escribe_nada` (×4) |
| `r10_un_parte_que_ya_es_apto_es_409` | **Derogado, y es la feature**: `r5_un_parte_apto_se_puede_rechazar_y_esa_es_la_feature` |
| `r9_el_motivo_del_rechazo_no_lleva_nada_del_papel` | `r42_la_respuesta_no_lleva_el_oid_ni_el_motivo` y `r53_un_rechazo_del_borde_tampoco_publica_lo_que_venia` |
| `r5_un_veredicto_metido_en_el_cuerpo_se_ignora` | `r28_un_veredicto_metido_en_el_cuerpo_se_ignora` |
| `r5_un_parte_con_firma_no_humana_tambien_se_aprueba` | `r9_deshacer_la_propia_decision_si_escribe_fila` y `r12_al_aprobar_el_motivo_es_opcional` |
| `r38_la_respuesta_no_lleva_el_oid_ni_el_texto_del_papel` | `r42_la_respuesta_no_lleva_el_oid_ni_el_motivo` |
| `r13_lo_que_se_guarda_de_la_persona_es_el_oid_y_nada_mas` | `r15_lo_que_se_guarda_de_la_persona_es_el_oid_y_nada_mas` |
| `r20_un_cuerpo_que_no_es_un_objeto_es_400` (×3) | `r31_un_cuerpo_que_no_es_un_objeto_es_400` (×3) |
| `r20_un_bloque_que_falta_es_400` (×3) | `r31_un_bloque_que_falta_es_400` (×3) |
| `r20_sin_remesa_registrada_sube_referencia_no_consta` | `r31_sin_remesa_registrada_sube_referencia_no_consta` |
| `r20_sin_base_de_datos_el_error_sube_sin_traducir` (×2) | `r31_sin_base_de_datos_el_error_sube_sin_traducir` (×2) |
| `r21_el_endpoint_no_mira_las_ventanas_de_escritura` | `r32_el_endpoint_no_mira_las_ventanas_de_escritura` |
| `r21_aprobar_no_toca_sharepoint_ni_el_erp` | `r37_cambiar_de_estado_no_toca_sharepoint_ni_el_erp`, **más** `r37_el_control_del_vocabulario_ve_los_imports_de_verdad`, que aquel no tenía |
| `r20_aprobar_devuelve_200_con_su_contrato` | `r31_la_ruta_devuelve_200_con_las_seis_claves_del_contrato` |
| `r20_un_cuerpo_que_no_es_json_es_400` | `r31_un_cuerpo_que_no_es_json_es_400` |
| `r20_r4_sin_usuario_oid_el_borde_responde_400` | `r31_el_borde_responde_400_sin_escribir_nada[sin-usuario-oid]` |
| `r20_un_parte_no_aprobable_es_409` (×2) | **Derogado**; el 409 que queda es `r7_un_parte_cerrado_es_409_por_el_borde` (×2) |
| `r20_sin_remesa_registrada_es_409` | `r31_sin_remesa_registrada_es_409` |
| `r20_sin_base_de_datos_es_503` (×2) | `r31_sin_base_de_datos_es_503` (×2) |
| `r44_el_log_lleva_hash_destino_y_resultado_y_nada_mas` | `r53_el_log_lleva_hash_origen_destino_y_resultado_y_nada_mas` |
| `r44_un_rechazo_tampoco_publica_lo_que_venia` | `r53_un_rechazo_del_borde_tampoco_publica_lo_que_venia` |
| `r18_la_ruta_es_post_anonima_y_se_llama_aprobar` | `r31_la_ruta_es_post_anonima_y_se_llama_estado` |
| `r21_la_ruta_no_mira_las_ventanas_de_escritura` | `r32_la_ruta_no_mira_las_ventanas_de_escritura` |

**`tests/utiles_rutas.py` NO se va con el fichero**: lo usa
`tests/test_f028_estado_http.py`, y sin él `app.get_functions()` revienta a la
segunda llamada (§40.3). Su cabecera sigue contando que F-026 descubrió el
problema, que es un hecho y no una deuda.

### 64.4 · `tests/test_f026_puertas.py` · los dos casos inertes

Los que el bloque 4 dejó anotados expresamente para T15 (§30.1). En su sitio
queda un **recuadro fechado del 2026-09-16** dentro del propio fichero, con qué
probaban, por qué se van y dónde está el sustituto:

| Retirado | Qué probaba | Sustituto |
|---|---|---|
| `r31_una_aprobacion_revocada_no_abre_ninguna_puerta` (×2 destinos) | Que una decisión revocada no abría las tres puertas | `test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_abre_nada` |
| `r23_una_aprobacion_de_otro_destino_no_sirve` (×2 destinos) | Que la aprobación valía para el destino aprobado | ídem — y más estrecho: F-028 compara la huella del veredicto entero |

Los dos **seguían en verde**, y ese era el problema: desde T11 pasaban una
`Aprobacion` a un doble al que ninguna puerta se la pedía, así que probaban lo
mismo que los `r25` de arriba y **no lo que sus nombres afirman**. Con ellos se
van `_aprobacion`, `_reclamacion`, `_archivar`, `_adjuntar`, `_cerrar` y
`CODIGO_EN_SIGRID`, que se quedaban sin un solo llamante.

Los **13 casos que quedan** en ese fichero siguen en verde sin tocarlos: los seis
`r25` (un parte no apto sin decisión no se archiva, no se adjunta, no cierra),
el control de que el material no es aprobable por accidente, y los seis de R24
(ningún paso recibe la decisión por parámetro, ningún handler la lee del cuerpo).

---

## 65 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2.528 pasados, 13 saltados, 0 fallos** | `bash harness/init.sh` |
| Tests ejecutados (arnés, raíz) | **62 pasados** | `bash harness/init.sh` |
| De ellos, **nuevos de T15** | **18 casos** (8 dominio + 6 persistencia + 4 borde), de 11 funciones | `pytest -k t15` |
| Tests **retirados** | **90 funciones** (25 + 35 + 28 + 2), todas con su sustituto en §64 | — |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 283/283, umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados / supervivientes** | automáticos **31 / 0** (0 timeouts, 158,3 s, 8 workers) · **a mano 10 / 0** | `python -m harness.mutacion --feature F-028` y §65.2 |
| **Tiempo de la suite** | **35,4 s** (`api`, bajo medición de cobertura) · 25,4 s sin ella · 4 s (raíz) | la propia suite |
| **Balance de líneas** | **+518 / −3.169** en 20 ficheros | `git show --stat a0b4ac7` |
| **Ruff** | **0 avisos** en los 15 ficheros tocados; el repositorio baja de **62 a 61** | `python -m ruff check` |

### Los supervivientes, y qué se hace con cada uno

**Ninguno**, ni en la campaña automática ni en la manual.

### 65.1 · La línea base estaba verde, y se comprobó **antes** de creerse el resultado

El encargo lo advertía y es lo primero que se hizo, porque el evaluador de
`harness.mutacion` da un mutante por **muerto** cuando la suite falla: con la
base en rojo, **todos** salen «muertos» sin que ningún test los cace, que es lo
que invalidó la primera campaña de T13 (§44.1).

Aquí no hizo falta deseleccionar nada. Inmediatamente antes de lanzarla:

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, cobertura 100,0 %;
- la suite del servicio, entera y a pelo → `2528 passed, 3 skipped` y **cero
  fallos**.

El descenso de 39 mutantes (T14) a **31** no es una campaña más floja: es que el
alcance ha **menguado** con el código. `function_app.py` pasa de **115 a 72**
líneas en alcance, `sentencias.py` de **169 a 144** y `mapeo.py` de **49 a 34**;
`domain/models/aprobacion.py` entra por primera vez en el alcance de la feature,
con 67. El total baja de 2.033 a **2.013** líneas **pese a** que este commit
suma un fichero nuevo al diff. Los 31 mutantes que quedan son de los bloques 1 a
5 y **siguen muriendo**, que también es información: T15 no ha roto nada de lo
ya probado.

### 65.2 · Lo que hay que mirar de las evidencias: **una retirada no se puede mutar**

Es el punto de método de este encargo y va en voz alta. `harness.mutacion` muta
**código que existe**. T15 casi solo borra, así que la campaña automática no
tiene nada suyo que atacar: de los 31 mutantes, **cero** caen en lo que T15
hace. `domain/models/aprobacion.py` entra en alcance con 67 líneas y no produce
ni un mutante, porque lo que queda es un `sha256` y un `if texto is None` —y el
mutador no reescribe comparaciones `is`, como ya observaron el bloque 3 (§23.1),
el 4 (§32.1) y T14 (§54.2)—.

**Presentar «31/31 muertos» como evidencia de T15 sería el número que tranquiliza
sin medir nada.** Lo que mide T15 es otra cosa, y hay que construirla al revés:
un mutante de una retirada es **reponer lo que se fue**, o **llevarse lo que
tenía que quedarse**.

Así que se han mutado **diez puntos a mano**, con el método de los bloques 3, 4
y 5 —se aplica la mutación, se corre la suite acotada (376 casos de los diez
ficheros implicados), se restaura con `git checkout`; «muerto» = al menos un test
falla—. El script está en el área de trabajo de la sesión y **restaura cada
fichero al terminar**; el árbol quedó limpio, comprobado con `git status`.

| # | Mutante aplicado a mano | Resultado | Quién lo caza |
|---|---|---|---|
| M1 | `aprobacion.py` **repone `admite_circuito`**, el criterio viejo de las puertas | **muerto** (2 fallos) | `t15_del_dominio_de_f026_no_queda_nada_de_la_decision[admite_circuito]`, `t15_la_huella_y_su_normalizador_siguen_donde_estaban` |
| M2 | La enmienda de la cabecera **pierde la fecha y la cita** | **muerto** (1) | `t15_la_cabecera_explica_que_la_decision_vive_ahora_en_estado_py` |
| M3 | `sentencias.py` **repone `upsert_aprobacion`** | **muerto** (2) | `t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026`, `t15_las_tres_sentencias_de_f026_se_han_retirado` |
| M4 | **Una escritura NUEVA a la tabla congelada, con otro nombre** | **muerto** (1) | `t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026` |
| M5 | `guardar_validacion` **vuelve a revocar** (R57) | **muerto** (2) | `t15_r57_guardar_la_validacion_ya_no_revoca_nada`, `t15_ningun_modulo_...` |
| M6 | El envoltorio **vuelve a delegar `consultar_aprobacion`** | **muerto** (1) | `t15_el_envoltorio_de_parte_ya_no_delega_lo_de_f026` |
| M7 | **La ruta `aprobar` vuelve al host** | **muerto** (4) | `t15_el_host_ya_no_publica_la_ruta_aprobar`, `t15_function_app_ya_no_sabe_aprobar`, y los **dos de F-010** sobre el recuento |
| M8 | **Se borra `sql/10_aprobaciones.sql`** (regla dura 3 al revés) | **muerto** (30) | `t15_la_tabla_de_f026_sigue_declarada_en_el_ddl` y 29 casos de `test_f026_ddl_aprobaciones.py` y `test_f028_ddl_historico.py` |
| M9 | **Se corta de más**: `_normalizar` desaparece del módulo | **muerto** (69) | 69 casos, entre ellos `r20_la_misma_huella_conserva_la_aprobacion` y `r9_una_aprobacion_humana_rescata_un_parte_no_apto` |
| M10 | **Se corta de más**: `huella_de_veredicto` deja de ser pública | **muerto** (8 errores de importación) | La suite entera de F-028 y los 14 de la huella de F-026 |

**10 de 10 muertos.** Los que más valen son tres:

- **M4** es el único que no se ve mirando ninguna función retirada: alguien
  vuelve a escribir en `postventa.aprobaciones` **con otro nombre**. Ningún test
  de `upsert_aprobacion` puede cazarlo, porque `upsert_aprobacion` ya no existe.
  Lo caza el control del vocabulario, que es justo para lo que está (§63.4).
- **M8** es el error caro de esta tarea: llevarse la tabla con el código. Mata a
  30 casos, y el primero que salta es el de la regla dura 3.
- **M9 y M10** son el error simétrico: cortar de más y llevarse la huella. Entre
  los dos tumban media suite de F-028, que es exactamente lo que el encargo
  avisaba que pasaría («si al retirar algo un test de la huella se pone rojo,
  para y dilo»). **No pasó en ningún momento del trabajo real.**

### Ruff

`python -m ruff check` sobre los **15 ficheros tocados**: cero avisos en catorce
y **uno** en `tests/utiles_sharepoint.py` (`I001`, orden de imports), que
**ya estaba en `HEAD` antes de tocarlo** —comprobado contra `HEAD~1`—. El
recuento del repositorio entero **baja de 62 a 61**: el `RET501` que el bloque 4
dejó anotado en ese mismo fichero se va con el `return None` de
`consultar_aprobacion`.

---

## 66 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes. T15 **no crea ninguna nueva** y añade peso a dos,
que siguen necesitando la base real y las ejecuta el humano tras desplegar:

- **T27.1** (el DDL aplicado dos veces no falla y la semilla no duplica): ahora
  importa más. `postventa.aprobaciones` deja de tener código que la escriba, así
  que **la semilla es lo único que la conecta con el sistema vivo**. Si el
  `CREATE TABLE` no se aplicara en un entorno nuevo, la semilla apuntaría a una
  tabla que no existe y `cargar_ddl` levantaría antes de abrir la conexión. Aquí
  solo se puede comprobar que el fichero sigue declarado y en su sitio.
- **T27.2** (la aprobación que ya había aparece sembrada y el parte sigue
  saliendo `aprobado`): es **la verificación que cierra T15**. Hasta hoy había
  dos caminos —la tabla vieja y el histórico— y uno de ellos tapaba el fallo del
  otro. Desde este commit **solo hay uno**: si la semilla no copió bien
  `aprobado_por` y `huella_aprobada`, el parte que alguien aprobó antes del
  despliegue saldrá `pendiente`, y no hay nada detrás que lo rescate.

**La base real y el ERP no se han tocado**: todo corre con
`RepositorioEnMemoria`, `RepositorioFalso`, `ErpEnMemoria` y dobles en memoria,
sin red, sin BBDD y sin IA.

---

## 67 · Lo que queda fuera del alcance de T15, y hay que decirlo

1. **El front sigue sin poder cambiar el estado.** Lo denunció T14 en §56 y
   sigue igual: `services/postventa-front/js/app.js` y `js/pipeline.js` leen el
   bloque `aprobacion`, que ya no viaja, y `js/api.js::aprobar` llama a un
   endpoint que **desde este commit devuelve 404**. Ningún test del front se ha
   puesto rojo, y eso no tranquiliza: los tests del front prueban el front
   contra sus propios dobles, no contra el contrato del backend. **El
   repositorio, entre T15 y el bloque 6, no se debe desplegar.** Es lo que la
   spec secuencia (T16–T18) y lo que `design.md` §5 ya declaraba como riesgo,
   con su mitigación: el front y la Function se despliegan juntos (`infra/`).
2. **`docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md` siguen
   documentando `POST /api/aprobar` y sin documentar `POST /api/estado`.** Es
   **T25** (R59, bloque 9) y no se ha tocado nada de eso. Los dos tests que
   vigilan esos documentos —`test_f012_r68_...` cuenta las filas de la tabla de
   §8 y exige que el párrafo diga ese número, y `test_f019_r32_...` exige «Los
   doce quedan en nivel»— **siguen en verde**, porque cuentan lo que el
   documento declara y el documento no ha cambiado. Dicho de otro modo: hoy el
   documento afirma doce endpoints y el servicio publica doce, pero **no son los
   mismos doce**. T25 tiene que arreglar las dos cosas a la vez.
3. **`ParteNoAprobable` sigue en `domain/models/errores.py` sin que nadie lo
   levante**, y `_escribir(..., ademas=...)` sigue en el adaptador sin
   llamantes. Los dos están razonados en §63.2 y **los dos quedan para el
   líder**.

---

## 68 · Por dónde sigue · el encargo del bloque 6

**T15 está cerrada, y con ella el bloque 5 entero.** No se ha entrado en el
bloque 6, como pedía el encargo.

Lo que el bloque 6 se encuentra ya hecho:

- **el backend está completo y probado**: `POST /api/estado` existe, publica su
  bloque `estado` con las cuatro claves y responde 200 / 400 / 409 / 503 según
  el caso, y `POST /api/parte` devuelve el estado de cada parte sin una consulta
  más;
- **`POST /api/aprobar` ya no existe**, así que `js/api.js::aprobar` no tiene a
  quién llamar: T16 no está «retirando algo que aún funciona», está arreglando
  algo que desde este commit está roto;
- **el contrato del bloque `estado`** —`estado`, `decidido_por_persona`,
  `decidido_at_utc`, `estado_anterior`, y **ni el `oid`, ni el correo, ni el
  nombre, ni el motivo** (R42, R52)— está fijado por
  `tests/test_f028_estado_http.py`, que es contra lo que el front tiene que
  programar.

Tres apuntes para quien lo coja:

- **`tests/test_f028_puertas.py` sigue siendo la red**, 48 casos, intacta desde
  el bloque 0. Si uno se pone rojo en el bloque 6, **parar y decirlo**.
- **El cuerpo de `POST /api/estado` exige `confirmado: true` como booleano**, no
  como la cadena `"true"`, y **exige motivo al rechazar** (R11). Las dos cosas
  las tiene que respetar `cuerpoDeCambioDeEstado` (T16), y las dos tienen test
  en el backend por si sirven de contrato.
- **El front y la Function se despliegan juntos.** Hasta que el bloque 6 esté,
  este repositorio no se despliega.

---

## 69 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las **283** líneas cambiadas. (La medición hecha
  justo tras el commit de T15, con el informe todavía sin commitear, dio
  **320/320**; la de cierre, **283/283**. Es el mismo código contado contra
  `dev` desde dos sitios, y las dos dan 100,0 % — pasó igual en T13 y en T14.)
- Árbol limpio, **2 commits** sobre `014fd6a` (`a0b4ac7` T15 y el de este
  informe), los dos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado.** `sql/10_aprobaciones.sql` tampoco:
  el directorio `sql/` entero está fuera del diff.

---

# F-028 · Estado del parte — informe del implementer · bloque 6, T16 y T17

> Encargo: **T16 y T17** de `specs/F-028-estado-del-parte/tasks.md`, la capa JS
> del front. Parada obligada al terminar. **No se ha entrado en T18.**
>
> Rama `feature/F-028-estado-del-parte`, desde `70ec902`. Rigor **`estandar`**:
> fase RED, puerta de cobertura y campaña de mutación. Sin `push`, sin tocar
> `dev` ni `main`, sin tocar el `status` de ninguna feature, sin tocar
> `azure-apps/`, `infrastructure/sigrid/` ni `infrastructure/sharepoint/`.

La línea base estaba **verde de verdad** al empezar: `bash harness/init.sh` →
ENTORNO LISTO, 2.528 pasados en `api`, 224 en `front`, 292 casos de JavaScript
y cobertura 100 % de 283 líneas. No hizo falta deseleccionar nada ni para la
suite ni para la campaña.

**Lo que cierra este encargo, y es por lo que era urgente**: hasta `70ec902` el
repositorio estaba en un estado **no desplegable** —lo denunciaron §56 y §67—
porque `js/api.js::aprobar` llamaba a un endpoint que T15 había retirado y todo
el front leía un bloque `aprobacion` que T14 había dejado de emitir. Con T16 y
T17 la capa que *decide* algo ya habla el contrato nuevo. **Falta T18**: la
pantalla (`js/app.js` e `index.html`) sigue llamando a lo viejo, así que el
repositorio **sigue sin poder desplegarse** hasta que el bloque 6 esté entero.

---

## 70 · Qué se ha hecho, en una frase por tarea

| Tarea | Commit | Qué deja |
|---|---|---|
| **T16** | `9d379f3` | `js/api.js::cambiarEstado` (`POST /api/estado`, paso propio de traza) y `js/pipeline.js::cuerpoDeCambioDeEstado`; se retira `aprobar` |
| **T17** | `efaaea4` | `semaforoDe(validacion, estado)` con las cuatro marcas, `esCirculable` por estado y `pendientesDeCircuito` filtrando por `estado === "aprobado"` |

Lo que esto hace posible en pantalla, que es el encargo de la feature: **un
parte `rechazado` sale de la tanda aunque su veredicto sea apto**. Hasta
`efaaea4` el selector miraba el veredicto, así que un parte verde rechazado a
mano entraba igual en el circuito que archiva en SharePoint y cierra la
incidencia en el ERP. Tiene test propio y lo mata el mutante M12.

---

## 71 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-front/tests_js/estado.test.js` | Las dos mitades del bloque 6: qué viaja al decidir (T16) y qué se pinta y qué circula (T17). **41 casos** |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/api.js` | `cambiarEstado` en lugar de `aprobar`; ruta `/estado` y `paso: "estado"` |
| `services/postventa-front/js/pipeline.js` | `cuerpoDeCambioDeEstado`, `ESTADOS_MANUALES`, `LIMITE_MOTIVO`, `estadoDe`, `semaforoDe` reescrito, `esCirculable` reescrito, `guardarParte` devuelve `estado`; se retiran `aprobacionVale` y `APROBACION_VIGENTE` |
| `services/postventa-front/tests_js/api.test.js` | Los tres casos de `aprobar` reescritos sobre `cambiarEstado` (§74.1) |
| `services/postventa-front/tests_js/aprobacion.test.js` | **25 casos retirados** con dos recuadros fechados (§74.2) |
| `services/postventa-front/tests_js/pipeline.test.js` | **3 casos del semáforo retirados** con su recuadro; el fixture gana `estadoParte`; uno reescrito |
| `services/postventa-front/tests_js/cierre.test.js` | El fixture gana `estadoParte`; un caso reescrito sobre el estado |
| `services/postventa-front/tests_js/grafico.test.js` | Ídem, dos casos reescritos |
| `services/postventa-front/tests_js/circuito.test.js` | Ídem, dos casos reescritos |
| `services/postventa-front/tests_js/persistencia.test.js` | Dos partes ganan `estadoParte` para que sigan fallando por lo suyo (R27 de F-019) |
| `services/postventa-front/tests/test_f026_front.py` | Un caso retirado con su recuadro fechado (§74.1) |
| `specs/F-028-estado-del-parte/tasks.md` | T16 y T17 marcadas `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff 70ec902 --stat`: en el diff **no aparece** ni un
fichero de `services/postventa-api/` —ni el dominio, ni la persistencia, ni las
tres puertas, ni el borde, ni `sql/`—, ni `domain/models/validacion.py`, ni
`domain/models/aprobacion.py`, ni `infrastructure/sigrid/`, ni
`infrastructure/sharepoint/`, ni `azure-apps/`, ni `harness/features.json`, ni
`js/confirmacion.js` (R35), ni `js/app.js`, ni `index.html` (los dos son T18).

Y **`tests/test_f028_puertas.py` no está en el diff**: sus 48 casos siguen en
verde sin una sola edición desde el bloque 0.

---

## 72 · Fase RED · las trazas, pegadas

### 72.1 · T16 · antes de que existieran `cuerpoDeCambioDeEstado` y `cambiarEstado`

```
$ cd services/postventa-front
$ node --test "tests_js/estado.test.js"

✖ f028 R10: los dos únicos destinos manuales son aprobado y rechazado
✖ f028 R10: no se compone ningún cambio a un estado que no sea manual
✖ f028 R11: un rechazo SIN motivo no se compone, y se dice por qué
✖ f028 R12: al aprobar el motivo es opcional, y sin él el cuerpo no lo lleva
✖ f028 R14: sin saber quién decide no se compone ninguna petición
✖ f028 R11, R14: el rechazo sin motivo NI oid tampoco se cuela por el otro lado
✖ f028: sin remesa registrada no se compone nada, porque el backend responde 409
✖ f028 R13: el motivo viaja recortado por los extremos
✖ f028 R13: el límite del motivo es el del dominio, y pasarse se rechaza
✖ f028 R13: el motivo se acota DESPUÉS de recortar, no antes
✖ f028 R29: la confirmación viaja como el BOOLEANO de JSON, no como la cadena
✖ f028: el cuerpo es el de guardar MÁS las cuatro claves propias, y ni una más
✖ f028 R30: no viaja NI UN BYTE del PDF ni un veredicto ya hecho
✖ f028 R30: un veredicto metido a mano en el parte tampoco se cuela
✖ f028: las ediciones de la persona SÍ viajan, que es lo que se decide
ℹ tests 15
ℹ pass 0
ℹ fail 15

✖ failing tests:
test at tests_js\estado.test.js:112:1
✖ f028 R10: los dos únicos destinos manuales son aprobado y rechazado
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected
  + undefined
  - [
  -   'aprobado',
  -   'rechazado'
  - ]
```

**15 de 15 en rojo.** Después de escribir las dos funciones: `15 passed`.

### 72.2 · Y la fase RED destapó un hueco real, que es lo que hay que mirar de T16

Con la implementación ya escrita, **catorce** casos pasaron y uno siguió rojo:

```
$ node --test "tests_js/estado.test.js"
ℹ pass 14
ℹ fail 1

✖ f028 R14: sin saber quién decide no se compone ninguna petición
  AssertionError [ERR_ASSERTION]: Missing expected exception:
  un cambio de estado con oid «"   "» no debería componerse
    expected: /qui[eé]n/i,
    operator: 'throws'
```

Leído en voz alta: **un `usuario_oid` de solo espacios se colaba**. `"   "` es
`truthy` en JavaScript, así que `if (!ajustes.usuarioOid)` lo dejaba pasar y se
componía una petición con `usuario_oid: "   "` que el backend contesta con un
400 —él sí hace `.strip()` antes de mirarlo (`estado.py::_usuario_oid`)—. El
arreglo es recortar antes de mirar, como hace el backend, y mandar el valor
recortado. **No es teórico**: el `oid` lo pone `api.identidad()`, que lo saca
de `/.auth/me` a través del proxy de la Static Web App, y un valor en blanco
vuelve de ahí sin que nadie lo note. Lo mata el mutante M4.

> El mismo defecto está en `cuerpoDeAprobacion` (F-026) y **no se ha
> arreglado**: esa función se retira en T18 con el resto de lo que llama
> `js/app.js`, y arreglar código que se va es trabajo que se tira.

### 72.3 · T17 · antes de que el semáforo y la tanda miraran el estado

```
$ node --test "tests_js/estado.test.js"
ℹ tests 40
ℹ pass 23
ℹ fail 17

✖ f028 R39: un parte aprobado POR UNA PERSONA no se pinta igual que el verde
✖ f028 R39: y la marca depende de QUIÉN decidió, no del veredicto
✖ f028 R5: un parte APTO que una persona rechazó se pinta rechazado
✖ f028 R7: un parte cerrado se pinta cerrado, aunque su veredicto sea apto
✖ f028 R17: sin el bloque del backend NO se inventa ninguna marca
✖ f028 R17: un estado que esta pantalla no conoce tampoco se pinta
✖ f028: el aprobado, el rechazado y el cerrado no necesitan veredicto
✖ f028 R9: un parte NO APTO que una persona aprobó entra en la tanda
✖ f028 R5: un parte RECHAZADO sale de la tanda AUNQUE su veredicto sea apto
✖ f028 R7: un parte CERRADO también sale de la tanda, aunque sea apto
✖ f028 R17: sin bloque de estado el parte NO entra en la tanda
✖ f028 R5: el cuerpo de archivo se NIEGA a componer un parte apto rechazado
✖ f028 R5: un parte apto rechazado NO es cerrable ni adjuntable, aunque conste archivado
✖ f028 R7: y un parte cerrado tampoco compone ninguna de las tres
✖ f028 R38: al guardar, el estado que devuelve el backend llega al parte
✖ f028: sin bloque de estado en la respuesta, lo que llega es null y no un hueco
✖ f028: un guardado fallido no inventa ningún estado
```

El que cuenta de todo el bloque es **«un parte RECHAZADO sale de la tanda
AUNQUE su veredicto sea apto»**: es el caso que el responsable pidió y que
hasta este commit no se podía ni escribir. Después del cambio:
`41 passed` (los 40 más el de §73.3).

### 72.4 · Los 23 que ya pasaban en rojo, y por qué es lo correcto

Son **todos control negativo** —«un parte pendiente sale de la tanda», «una
lista vacía no revienta», «el estado no relaja las otras puertas», los quince
de T16 ya implementados—: antes del cambio ningún parte tenía bloque `estado`,
así que afirmar que *no* circula salía gratis. Su valor no está en la fase RED
sino en la de después: son los que se ponen rojos si la condición desaparece, y
de eso hay prueba en §76 (mutantes M13 y M14).

---

## 73 · Decisiones de diseño, y las tres que hay que juzgar

### 73.1 · El bloque del backend se guarda en `parte.estadoParte`, y no en `parte.estado`

**Es la decisión con más consecuencias para T18** y por eso va primero.
`js/app.js` usa `parte.estado` desde F-007 para la **fase** del parte en
pantalla —`"leyendo"`, `"listo"`, `"error"`—. El bloque que devuelven
`/api/parte` y `/api/estado` se llama `estado` en el JSON, así que asignarlo a
`parte.estado` habría metido dos cosas distintas en el mismo campo del mismo
objeto: un día la fase pisa al estado del parte y el parte aparece `"listo"` en
vez de `aprobado`, o al revés, y el bicho es de los que tardan una tarde.

Se llama `estadoParte`, está escrito en la docstring de `estadoDe` y en la
cabecera de la sección T17 de `tests_js/estado.test.js`. **T18 puede
renombrar la fase si prefiere** —es suya, `app.js` es su fichero—, pero
mientras no lo haga, este nombre es lo que evita la colisión.

La clave que devuelve `guardarParte` sí se llama `estado`, porque es
literalmente lo que vino en la respuesta.

### 73.2 · Sin bloque `estado`, **no se pinta ninguna marca y el parte no circula**

Es la aplicación literal de R17 y de `design.md` §7 —«el estado lo manda el
backend y el front lo pinta: no hay derivación en JavaScript»— y tiene un
efecto visible que hay que declarar: **un parte cuyo guardado falló se queda
sin color**. Antes se pintaba verde/ámbar/rojo a partir del veredicto.

Por qué se acepta, y por qué no se ha dejado un camino de respaldo:

1. **El caso normal no existe.** El bloque llega en la respuesta de
   `POST /api/parte`, que es parte de `procesarParte`. Sin él tampoco hay
   `parte.guardado`, y sin `guardado` el parte ya estaba fuera de la tanda
   desde F-019 R27 y la pantalla ya enseña `errorGuardado` con el motivo.
2. **El respaldo sería exactamente el defecto de la feature.** Pintar verde un
   parte apto cuyo estado no se ha podido leer es afirmar que está aprobado sin
   haberlo preguntado — y si ese parte estaba rechazado en la base, la pantalla
   estaría diciendo lo contrario de lo que consta.
3. **El fallo se va al lado seguro**, que es el criterio que ya tomó el bloque
   1 en `_aprueba_lo_que_hay`: sin marca, nunca con la marca de aprobado.

Lo fija `f028 R17: sin el bloque del backend NO se inventa ninguna marca` y lo
mata el mutante **M11**, que es el que repone la derivación.

### 73.3 · Un hueco que abre T17 y se cierra en el mismo commit

`esCirculable` dejó de mirar `parte.validacion`. Antes no podía: los dos
caminos de F-026 —`esArchivable(validacion)` y `aprobacionVale(...)`— exigían
una validación, así que un parte sin veredicto no llegaba nunca a componer
nada. Ahora sí llega, y `cuerpoDeArchivo` hace
`cuerpo.append("veredicto", parte.validacion.veredicto)`: lo que salía era un
`TypeError` en vez de un error que diga qué falta.

Se ha cerrado en los dos sitios donde el veredicto viaja de verdad
—`cuerpoDeArchivo` con su propia comprobación, `esCerrable` con una condición
más—, **no** metiéndolo otra vez en `esCirculable`, que tiene que seguir siendo
«su estado es `aprobado`» y nada más (R33). Tiene test:
`f028: un parte aprobado SIN veredicto dice qué le falta, no revienta`.

### 73.4 · Lo que se retira porque se queda sin llamante, y lo que NO se retira

Se van con T17, declarados aquí uno a uno porque `tasks.md` no los nombra y son
**la mitad interna** de lo que T17 sí sustituye —el mismo criterio de §63.2—:

| Retirado | De quién era la mitad |
|---|---|
| `pipeline.js::aprobacionVale` | de `esCirculable` y del `semaforoDe` viejo. Comparaba el destino aprobado con el de la validación de ahora; F-028 resuelve la caducidad **al derivar**, en el backend (R19) |
| `pipeline.js::APROBACION_VIGENTE` | el literal que `aprobacionVale` comparaba |
| `aprobacion.test.js::FormDataFalso`, `parteAprobado`, `apiQueGuarda`, `aprobacionInventada` | ayudantes de los 25 casos retirados; sin un solo llamante |

**Lo que NO se retira aunque haya quedado a medio camino**, y no lo cruzo por
mi cuenta:

- **`pipeline.js::cuerpoDeAprobacion`, `esAprobable` y `MOTIVOS_APROBABLES`.**
  Los tres siguen vivos porque `js/app.js` e `index.html` los llaman, y esos
  dos ficheros son **T18**. `cuerpoDeAprobacion` compone hoy el cuerpo de un
  endpoint que ya no existe, así que es código muerto en cuanto T18 reescriba
  la pantalla; `esAprobable` es además una copia de `es_aprobable`, que T15
  retiró del dominio porque F-028 **deroga** esa pregunta (R9, R10: una persona
  puede mover a `aprobado` o a `rechazado` cualquier parte que no esté
  `cerrado`). **Los tres son para T18.**
- **`js/app.js:546 · api.aprobar(cuerpo, parte.hash)`.** Desde T16 ese método no
  existe, así que el botón de aprobar da hoy un `TypeError` en vez de un 404.
  Las dos cosas son igual de rotas y las dos las arregla T18; decirlo aquí es
  para que nadie lo lea como un descuido de este commit.

---

## 74 · Los tests de antes que han cambiado, y por qué

Son **31**, en siete ficheros, y ninguno se ha «ajustado para que pase». Van
uno a uno porque un test que cambia sin justificación escrita es un test
aflojado.

### 74.1 · T16 · tres reescritos y uno retirado

| Fichero | Qué pasa |
|---|---|
| `tests_js/api.test.js` · la entrada `aprobar` de `LOS_ENDPOINTS` | **Reescrita** como `cambiarEstado` → `/api/estado`. Siguen siendo **doce** endpoints, y por eso el comentario del recuento dice ahora en voz alta que «no son los mismos doce»: el número que no se mueve es justo el caso que esa lista existe para no dejar pasar en silencio, y lo que lo caza es la comparación nombre a nombre |
| `tests_js/api.test.js` · «aprobar manda POST /api/aprobar…» | **Reescrito** sobre `cambiarEstado`: ruta, método, cabecera y `paso: "estado"` |
| `tests_js/api.test.js` · «por la traza de aprobar no pasa el oid» | **Reescrito** y **más fuerte**: ahora por el cuerpo viaja además el `motivo`, que es texto libre y puede llevar dentro el nombre de un cliente (R52) |
| `tests/test_f026_front.py` · `test_f026_r2_aprobar_es_una_peticion_propia_a_su_endpoint` | **Retirado** con recuadro fechado. Buscaba `"/aprobar"` y `paso: "aprobar"` en el texto de `api.js`. Su sustituto son los dos de arriba, que prueban lo mismo contra un `fetch` doble en vez de contra el texto del fichero |

### 74.2 · T17 · 25 retirados de `tests_js/aprobacion.test.js`

Dos recuadros fechados dentro del propio fichero, con la tabla completa
«retirado → sustituto». El resumen:

- **11 del semáforo y del circuito de F-026** (`semaforoDe(validacion,
  aprobacion)`, `esCirculable` con destino). Probaban **el mecanismo que T17
  sustituye**: el color y la entrada al circuito salían del veredicto y de una
  aprobación con su destino. Todos tienen sustituto en `estado.test.js`, y uno
  de ellos —«sin aprobación, el semáforo sigue diciendo exactamente lo que
  decía»— **dejó de ser cierto a propósito**: F-028 sí reescribe los tres
  colores de F-007, y eso es la feature.
- **14 de la tanda, las tres composiciones y `guardarParte`**. Cuatro de estos
  catorce **seguían en verde** y merecen su párrafo: «un no apto sin aprobación
  sigue fuera de la tanda», «un aprobado que no consta guardado tampoco entra»,
  «el cuerpo de archivo se sigue negando sin aprobación ninguna» y «un revocado
  ni se cierra ni se adjunta» pasaban porque el montaje se había quedado
  **inerte** —le pasan una `aprobacion` a un pipeline al que ya nadie se la
  pide, así que el parte se queda fuera por no tener estado y no por lo que su
  nombre afirma—. Es la misma clase de test verde que el bloque 4 retiró de
  `test_f026_puertas.py` (§30.1) y T15 dos más (§64.4).
- **Uno se queda sin sustituto, y se dice**: «si el backend dice que la revocó,
  eso es lo que llega». F-028 **no revoca nada**; la aprobación caduca al
  derivar, y eso se prueba en el backend (`test_f028_r19_…`, `test_f028_r20_…`).

Con ellos se van cuatro ayudantes y nueve imports que se quedaban sin un solo
llamante.

### 74.3 · T17 · tres retirados de `tests_js/pipeline.test.js`

Los tres del semáforo de F-007: «el semáforo sale de veredicto y destino», «sin
veredicto todavía, no hay semáforo que pintar» y «un apto con destino que no es
archivo_y_cierre NO es verde». Se retiran con su recuadro porque **derivar el
color del veredicto es exactamente lo que F-028 prohíbe** (R17). No se les ha
pasado un segundo argumento para dejarlos verdes; sus sustitutos cubren más que
ellos, incluidas las dos marcas que antes no existían.

**`esArchivable` sigue en ese fichero y sin tocar**, y es deliberado: conserva
su significado de siempre —«lo que la máquina dio por bueno»—, lo usa
`noArchivables()` y distinguirlo del aprobado a mano **es** el requisito (R39).

### 74.4 · T17 · cinco reescritos y seis fixtures ampliados

| Fichero | Qué cambia |
|---|---|
| `cierre.test.js` | `parteCerrable` gana `estadoParte`; «un parte no apto NO es cerrable» → **«un parte que no consta APROBADO no es cerrable»**, recorriendo los tres estados que no son `aprobado` —incluido `rechazado`, que antes no se podía ni montar— más el caso sin bloque |
| `grafico.test.js` | `parteAdjuntable` gana `estadoParte`; dos casos reescritos igual |
| `circuito.test.js` | `parteDeLaTanda` gana `estadoParte`; «los que no son aptos quedan fuera» → por estado; y «un parte no apto no llega a ninguna petición» se monta ahora **apto y rechazado a mano**, que es más fuerte: comprueba que la negativa no tumba la tanda **sobre el parte que la máquina había dado por bueno** |
| `pipeline.test.js` | El fixture común gana `estadoParte` —por el mismo motivo que ya tenía `guardado`—; «componer el cuerpo de archivo de un parte no apto es imposible» → «de un parte **no aprobado**» |
| `persistencia.test.js` | Los dos partes de R27 (F-019) ganan `estadoParte`. Sin él fallarían por el motivo de **otro** requisito —`cuerpoDeArchivo` mira primero el estado— y el par dejaría de vigilar lo suyo. La combinación «con estado conocido pero sin guardar» no es artificial: es lo que queda cuando un parte que ya estaba en la base se vuelve a guardar y el guardado falla, porque `guardarParte` conserva a propósito el estado que ya tenía |

---

## 75 · La verificación de T16 y T17, recontada

| Lo que pide la tarea | Dónde se fija |
|---|---|
| **T16** · el cuerpo lleva `estado`, `usuario_oid`, `confirmado: true` y el motivo recortado | `f028: el cuerpo es el de guardar MÁS las cuatro claves propias, y ni una más`, `f028 R29: la confirmación viaja como el BOOLEANO de JSON`, `f028 R13: el motivo viaja recortado por los extremos` |
| **T16** · se niega a componer un rechazo **sin motivo** (R11) | `f028 R11: un rechazo SIN motivo no se compone, y se dice por qué` (5 formas de «vacío», espacios incluidos) |
| **T16** · y **sin `usuario_oid`** | `f028 R14: sin saber quién decide no se compone ninguna petición` (4 formas), más `f028 R11, R14: el rechazo sin motivo NI oid tampoco se cuela por el otro lado` — **las dos puertas, no una** |
| **T16** · no lleva ningún byte del PDF (R30) | `f028 R30: no viaja NI UN BYTE del PDF ni un veredicto ya hecho`, sobre el JSON ya serializado, más su control negativo `…un veredicto metido a mano en el parte tampoco se cuela` |
| **T17** · las cuatro marcas | Siete casos: verde, aprobado con anillo, rechazado, cerrado, ámbar, rojo y sin marca |
| **T17** · `pendientesDeCircuito` filtra por `estado === "aprobado"` | `f028 R33: entra en la tanda el que está APROBADO, lo diga la máquina o una persona` y `f028 R9: un parte NO APTO que una persona aprobó entra en la tanda` |
| **T17** · **un parte `rechazado` sale de la tanda aunque su veredicto sea apto** | `f028 R5: un parte RECHAZADO sale de la tanda AUNQUE su veredicto sea apto`, que **afirma primero** `parte.validacion.veredicto === "apto"` para que el caso no pueda quedarse sin su mitad |
| **T17** · un `cerrado` también | `f028 R7: un parte CERRADO también sale de la tanda, aunque sea apto` |
| **T17** · el `aprobado` por persona se distingue del de máquina (R39) | `f028 R39: un parte aprobado POR UNA PERSONA no se pinta igual que el verde` y su control negativo `…y la marca depende de QUIÉN decidió, no del veredicto` |

Y tres que no pide la tarea y sostienen el resto: que las **tres**
composiciones (`cuerpoDeArchivo`, `esCerrable`, `cuerpoDeGrafico`) se niegan
igual —no basta con no pintar el botón—, que el motivo se acota **después** de
recortar, y que las ediciones de la persona **sí** viajan, porque el backend
recalcula el veredicto sobre lo que se le manda y sin ellas la huella apuntada
no sería la del veredicto que se está mirando.

---

## 76 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `front`, Python) | **223 pasados, 0 fallos** | `bash harness/init.sh` |
| **Tests ejecutados** (servicio `front`, JavaScript) | **305 pasados, 0 fallos** | `node --test "tests_js/*.test.js"`, que lanza el puente `tests/test_f007_js.py` |
| Tests ejecutados (servicio `api`) | **2.528 pasados, 13 saltados** | la suite del servicio, a pelo |
| Tests ejecutados (arnés, raíz) | **62 pasados** | `bash harness/init.sh` |
| De ellos, **nuevos de este bloque** | **41** en `tests_js/estado.test.js` (15 de T16 + 26 de T17) | `node --test "tests_js/estado.test.js"` |
| Tests **retirados** | **29** (25 de `aprobacion.test.js`, 3 de `pipeline.test.js`, 1 de `test_f026_front.py`), todos con su sustituto en §74 | — |
| Tests **reescritos en su sitio** | **8**, con su enmienda fechada dentro | §74 |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 283/283, umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `init.sh`. **Ver §76.1: no mide nada de este bloque** |
| **Mutantes generados / supervivientes** | automáticos **31 / 0** (0 timeouts, 146,2 s, 8 workers) · **a mano 15 / 0** | `python -m harness.mutacion --feature F-028` y §76.2 |
| **Tiempo de la suite** | `api` **23,7 s** · `front` **1,9 s** (Python) + **0,41 s** (JavaScript) · raíz 3,0 s | la propia suite |
| **Ruff** | `All checks passed` sobre el único `.py` tocado; el repositorio sigue en **61** avisos, sin crecer | `python -m ruff check` |

### Los supervivientes, y qué se hace con cada uno

**Ninguno**, ni en la campaña automática ni en la manual.

### 76.1 · Lo que hay que mirar de las evidencias: **ni la cobertura ni la campaña miden este bloque**

Va en voz alta porque presentarlo de otro modo sería el número que tranquiliza
sin medir nada, que es el aviso del encargo.

**La puerta de cobertura da 100,0 % de 283 líneas, y son las mismas 283 líneas
que medía T15.** El arnés mide cobertura de **Python** (`harness/servicios.json`
lo dice expresamente: el front va con lenguaje `python` por `dev_server.py`), y
T16 y T17 no tocan una sola línea de Python de producción. Las **307 líneas de
JavaScript de producción** que este bloque cambia no entran en esa cifra ni pueden entrar.

**Y la campaña automática no genera ni un mutante de este bloque**, por lo
mismo: `harness.mutacion` muta ficheros `.py`. Los 31 mutantes son de los
bloques 1 a 5 y **siguen muriendo** —que también es información: el bloque 6 no
ha roto nada de lo ya probado—, pero no dicen absolutamente nada de T16 ni de
T17.

La línea base se comprobó **antes** de creerse el resultado, como avisaba el
encargo y como enseñó T13 (§44.1): `bash harness/init.sh` → ENTORNO LISTO, y la
suite del servicio `api` entera y a pelo → `2528 passed, 13 skipped`, cero
fallos.

> **Propagación pendiente a `arnes-base`, y no la hago yo.** Es el mismo hueco
> que el bloque 3 anotó en §23.1 —que la campaña no avise de los ficheros en
> alcance sin mutantes— más uno nuevo: un servicio con código en **dos
> lenguajes** mide y muta solo uno, y el informe no lo dice. Queda anotado para
> que lo decida el líder; el implementer no toca el arnés por su cuenta.

### 76.2 · Los 15 mutantes **a mano**, que son la evidencia que sí respalda el bloque

Mismo método que los bloques 3, 4 y 5: se aplica la mutación sobre el fichero,
se corre la suite del front entera —`node --test "tests_js/*.test.js"` y
`pytest`, porque hay controles que miran el texto de `api.js`— y se restaura.
«Muerto» = al menos un caso falla. El script está en el área de trabajo de la
sesión, restaura cada fichero en un `finally` y el árbol quedó limpio,
comprobado con `git status`.

| # | Mutante aplicado a mano | Resultado | Quién lo caza |
|---|---|---|---|
| M1 | `cuerpoDeCambioDeEstado` deja de exigir motivo al rechazar (R11) | **muerto** | `f028 R11: un rechazo SIN motivo no se compone` |
| M2 | `confirmado` viaja como la **cadena** `"true"` (R29) | **muerto** | `f028 R29: la confirmación viaja como el BOOLEANO de JSON` |
| M3 | deja de exigir quién decide (R14) | **muerto** | `f028 R14: sin saber quién decide…` y `f028 R11, R14: …tampoco se cuela por el otro lado` |
| M4 | el `oid` deja de recortarse: uno de espacios se cuela | **muerto** | `f028 R14`, caso `"   "` — es el hueco de §72.2 |
| M5 | se admite cualquier `estado`, no solo los dos manuales (R10) | **muerto** | `f028 R10: no se compone ningún cambio a un estado que no sea manual` |
| M6 | el motivo demasiado largo deja de rechazarse (R13) | **muerto** | `f028 R13: el límite del motivo es el del dominio` |
| M7 | el cuerpo lleva el **veredicto ya hecho** (R28, R30) | **muerto** | `f028 R30: no viaja NI UN BYTE del PDF ni un veredicto ya hecho` |
| M8 | `cambiarEstado` vuelve a llamar a `/aprobar` | **muerto** | `LOS_ENDPOINTS` y `f028: cambiarEstado manda POST /api/estado` |
| M9 | el cambio de estado pierde su paso propio de traza | **muerto** | ídem |
| M10 | el aprobado **por una persona** se pinta igual que el verde (R39) | **muerto** | `f028 R39` (los dos casos) |
| M11 | sin bloque de estado, el semáforo **vuelve a derivar del veredicto** (R17) | **muerto** | `f028 R17: sin el bloque del backend NO se inventa ninguna marca` |
| M12 | el circuito se abre **también para el `rechazado`** (R5) | **muerto** | `f028 R5: un parte RECHAZADO sale de la tanda…` y las tres composiciones |
| M13 | el circuito se abre para **todo lo que no sea `pendiente`** (R7) | **muerto** | `f028 R7: un parte CERRADO también sale de la tanda` |
| M14 | la tanda **deja de filtrar por el estado** (R33) | **muerto** | `f028 R5`, `f028 R7`, `f028 R4` y `f028 R17` |
| M15 | `guardarParte` vuelve a leer el bloque `aprobacion`, que ya no viaja | **muerto** | `f028 R38: al guardar, el estado que devuelve el backend llega al parte` |

**15 de 15 muertos.** Los cuatro que más valen:

- **M12 y M13** son, literalmente, las dos formas de volver a dejar circular lo
  que este bloque viene a frenar — y detrás del circuito hay dos escrituras en
  un ERP de producción y un PDF con el DNI de un cliente subiendo a SharePoint.
- **M2** es el error clásico del front que serializa mal, y es el único de los
  quince que **no se ve mirando la pantalla**: la petición sale, el backend la
  rechaza con un 400 y lo que ve el usuario es «no se ha podido registrar».
- **M11** es el que repone la derivación en JavaScript, o sea el defecto
  original de la feature escrito en el front.

---

## 77 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes y este bloque **no crea ninguna nueva**, pero deja
media de una lista para ejecutar y añade un aviso de despliegue:

- **T27.4** («un parte apto rechazado a mano no se archiva»): la mitad del
  backend está desde el bloque 4 y la mitad del front, desde T17 —la tanda ya
  no lo lleva—. Lo que falta para poder ejecutarla **desde la pantalla** es el
  botón de rechazar, que es T18.
- **T27.5** («un parte cerrado responde 409 y la web lo explica»): la marca del
  cerrado ya existe (`semaforoDe` → `"cerrado"`); **la frase que lo explica
  (R41) es T18**.
- **Aviso de despliegue, y no es una verificación**: `js/app.js` sigue llamando
  a `api.aprobar` y a `window.Pipeline.cuerpoDeAprobacion`, y sigue pasándole a
  `semaforoDe` el bloque viejo. **El repositorio no se debe desplegar hasta que
  T18 esté.** Es lo que la spec secuencia y lo que `design.md` §5 declara como
  riesgo, con su mitigación: el front y la Function se despliegan juntos
  (`infra/`).

**La base real y el ERP no se han tocado**: todo lo de este bloque corre con
`fetch` dobles inyectados y objetos en memoria, sin red, sin BBDD y sin IA. La
guardia de red de sesión de `tests/conftest.py` sigue puesta.

---

## 78 · Por dónde sigue · el encargo de T18

**T16 y T17 están cerradas. No se ha entrado en T18**, como pedía el encargo.

Lo que T18 se encuentra ya hecho:

- **`api.cambiarEstado(cuerpo, hash)`** y **`Pipeline.cuerpoDeCambioDeEstado(parte,
  {estado, usuarioOid, remesaId, motivo})`**, que se niega a componer un rechazo
  sin motivo y sin `oid`. `app.js` solo tiene que recoger el motivo del campo
  de texto y pasarlo;
- **`Pipeline.semaforoDe(validacion, parte.estadoParte)`** devuelve una de
  `"verde"`, `"aprobado"`, `"ambar"`, `"rojo"`, `"rechazado"`, `"cerrado"` o
  `""`. `index.html` ya pinta las cuatro primeras (líneas 150-153); **faltan las
  clases de `rechazado` (gris apagado y tachado) y `cerrado` (azul con
  candado)**, y `Pipeline.SEMAFORO_RECHAZADO` / `SEMAFORO_CERRADO` están
  exportadas para no repetir los literales;
- **`Pipeline.estadoDe(parte)`** devuelve el estado o `""`, que es lo que T18
  necesita para decidir si enseña los dos botones o la frase de R41;
- **`Pipeline.ESTADOS_MANUALES` y `LIMITE_MOTIVO`**, para el desplegable y para
  acotar el campo de motivo con el número del dominio y no con uno inventado.

Cinco apuntes para quien lo coja:

- **El campo del parte se llama `parte.estadoParte`**, no `parte.estado`, y el
  porqué está en §73.1. `guardarParte` lo devuelve como `guardado.estado`, así
  que `_anotarGuardado` tiene que hacer `parte.estadoParte = guardado.estado`
  —y **solo cuando el guardado salió bien**, igual que hoy—.
- **`app.js` está roto a propósito en tres sitios** y T18 los arregla:
  `api.aprobar` (línea 546, ya no existe), `cuerpoDeAprobacion` (compone para un
  endpoint retirado) y `semaforoDe(validacion, parte.aprobacion)` (le pasa el
  bloque viejo).
- **Con T18 se van `cuerpoDeAprobacion`, `esAprobable` y `MOTIVOS_APROBABLES`**
  de `pipeline.js`, y con ellos los 13 casos que quedan en
  `tests_js/aprobacion.test.js` —que entonces se puede retirar entero— y los
  casos de `tests/test_f026_front.py` que miran `esAprobable()` en el HTML
  (líneas 159-160 y 221-222). F-028 **deroga** la pregunta «¿es este parte
  aprobable?» (R9, R10), así que no hay que buscarles sustituto: hay que decir
  que se deroga, como hizo T15 en §64.1.
- **`js/confirmacion.js` no se toca** (R29, R35): el botón **es** el acto
  explícito y `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front`
  tiene que seguir en verde sin tocarlo.
- **`tests/test_f028_puertas.py` sigue siendo la red**, 48 casos, intacta desde
  el bloque 0. Si uno se pone rojo en T18, **parar y decirlo**.

---

## 79 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de
  cobertura al **100,0 %** de las 283 líneas cambiadas (que son las de Python:
  ver §76.1).
- Árbol limpio, **3 commits** sobre `70ec902` (`9d379f3` T16, `efaaea4` T17 y
  el de este informe), todos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado.** El backend entero está fuera del
  diff: `git diff 70ec902 -- services/postventa-api/` está vacío.

---

# T18 · La pantalla · encargo del 2026-09-16

## 80 · Qué se ha hecho

| Tarea | Commit | Qué deja |
|---|---|---|
| **T18** | `4b85e6b` | `index.html` y `js/app.js` reescritos sobre el estado: los dos gestos en el detalle, el motivo obligatorio al rechazar, las cuatro marcas en lista y detalle, los textos de R43 y la frase del parte `cerrado`. Se retira la aprobación de F-026 de los dos ficheros y de `js/pipeline.js` |

Y lo que esto cierra, que es el motivo del encargo: **la rama vuelve a ser
desplegable**. Desde `a0b4ac7` (T15) `js/app.js` llamaba a `api.aprobar`, que
`9d379f3` (T16) retiró del cliente, contra un endpoint que T15 había quitado del
backend. Eran tres líneas rotas a propósito —enumeradas en §73.4— y las tres
están arregladas. El detalle, en §89.

---

## 81 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-front/tests/test_f028_front.py` | Lo que la pantalla tiene que decir y lo que no puede decir. **36 casos** |

### Borrados

| Ruta | Por qué |
|---|---|
| `services/postventa-front/tests_js/aprobacion.test.js` | Sus **13 casos restantes** probaban `esAprobable`, `MOTIVOS_APROBABLES` y `cuerpoDeAprobacion`, que se van con T18. §84.2 los recorre uno a uno |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/index.html` | Los dos gestos y el campo de motivo en el detalle; las cuatro marcas en la lista (punto de color + etiqueta legible) y en el detalle; la frase del `cerrado`; el aviso de R43; el texto de la tanda. Se retira la sección de aprobación de F-026 |
| `services/postventa-front/js/app.js` | `aprobarParte()`, `rechazarParte()` y `_cambiarEstado`; `motivoDeRechazo`, `mensajeEstado` y `LIMITE_MOTIVO` en el estado; `estadoParte` y `avisoEstado` en `_parteInicial`; `estadoDelParte`, `etiquetaDeEstado`, `estaCerrado`, `decidioUnaPersona`, `fechaDeDecision`, `hayIdentidad`, `hayMotivo`, `puedeDecidir`, `puedeRechazar`. Se retiran `esAprobable`, `estaAprobado`, `destinoDeOrigen`, `fechaDeAprobacion`, `aprobarParte` (el viejo) y `mensajeAprobacion` |
| `services/postventa-front/js/pipeline.js` | `avisoDeEstado` y `AVISO_DECISION_CADUCADA` (R43); se exportan `ESTADO_APROBADO`, `ESTADO_RECHAZADO`, `ESTADO_PENDIENTE` y `ESTADO_CERRADO`; se retiran `esAprobable`, `cuerpoDeAprobacion` y `MOTIVOS_APROBABLES` con su recuadro fechado |
| `services/postventa-front/tests_js/estado.test.js` | Sección **T18**: 6 casos nuevos sobre `avisoDeEstado` |
| `services/postventa-front/tests/test_f026_front.py` | **7 casos retirados** en cinco recuadros fechados (§84.1); quedan 7 |
| `specs/F-028-estado-del-parte/tasks.md` | T18 marcada `[x]` |
| `progress/mutacion_F-028.md` | Lo genera la campaña |

### Lo que la spec prohíbe tocar, y que sigue intacto

Comprobado con `git diff 5b3fe22 --name-only`: en el diff **no aparece ni un
fichero de `services/postventa-api/`** —`git diff 5b3fe22 -- services/postventa-api/`
está vacío—, ni `azure-apps/`, ni `harness/features.json`, ni
`infrastructure/sigrid/`, ni `infrastructure/sharepoint/`, ni
`domain/models/validacion.py`, ni `domain/models/aprobacion.py`, ni `sql/`.

Y **`js/confirmacion.js` tampoco está en el diff** (R29, R35):
`test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en verde sin
tocarlo, y F-028 añade su propio control del mismo hecho
(`test_f028_r29_decidir_no_arma_ninguna_confirmacion_nueva`).

**`tests/test_f028_puertas.py` sigue siendo la red**, 48 casos, intacta desde el
bloque 0. Se ejecutó a pelo al terminar: `48 passed in 0.50s`.

---

## 82 · Fase RED · las trazas, pegadas

### 82.1 · La mitad de `js/pipeline.js` · antes de que existiera `avisoDeEstado`

```
$ cd services/postventa-front
$ node --test "tests_js/estado.test.js"

✖ f028 R43: si había decisión de una persona y deja de haberla, se avisa (0.1448ms)
✖ f028 R43: el aviso no acusa a nadie ni nombra a quien decidió (0.1046ms)
✖ f028 R43: mientras la decisión siga firmada no se avisa de nada (0.0727ms)
✖ f028 R43: un parte que nunca decidió nadie no estrena ningún aviso (0.0747ms)
✖ f028 R43: un rechazo que sustituye a una aprobación tampoco es una caducidad (0.0594ms)
✖ f028 R43: sin bloque nuevo tampoco se inventa un aviso (0.0575ms)
ℹ tests 47
ℹ pass 41
ℹ fail 6

✖ failing tests:
test at tests_js\estado.test.js:711:1
✖ f028 R43: si había decisión de una persona y deja de haberla, se avisa
  TypeError: avisoDeEstado is not a function
      at TestContext.<anonymous> (...\tests_js\estado.test.js:712:17)
```

**6 de 6 en rojo.** Después de escribir la función: `47 passed`.

### 82.2 · La pantalla · antes de tocar `index.html` y `js/app.js`

```
$ python -m pytest tests/test_f028_front.py -q
FFFFFF.FFFFFFFF.FFFFFFFF.FFFFFFF..FF                                     [100%]

___________ test_f028_r38_el_parte_declara_su_estado_desde_que_nace ___________

        inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

>       assert "estadoParte:" in inicial, (
            "`_parteInicial` no declara `estadoParte`: la marca del estado no "
            "repintaría al cambiarlo"
        )
E       AssertionError: `_parteInicial` no declara `estadoParte`: la marca del
        estado no repintaría al cambiarlo
E       assert 'estadoParte:' in '_parteInicial(crudo) {\n      return {\n
        hash: crudo.hash,\n ... errorGuardado: "",\n        aprobacion: null,\n
        };\n    },\n\n    '

31 failed, 5 passed in 0.29s
```

**31 de 36 en rojo.** Después del cambio: `36 passed`.

### 82.3 · Los 5 que ya pasaban en rojo, y por qué es lo correcto

| El que pasaba | Por qué pasaba, y qué vale |
|---|---|
| `…r36_ningun_gesto_en_la_lista` | Control negativo: F-026 ya tenía el botón solo en el detalle, y R36 conserva esa garantía. Su valor está en el después: se pone rojo si alguien mete el botón de rechazar en la fila |
| `…r29_decidir_no_arma_ninguna_confirmacion_nueva` | Cuenta `Confirmacion.armar(` y ya valía 1. Es el control de que T18 **no** añade una segunda confirmación, y no podía fallar antes de escribir T18 |
| `…r39_el_aprobado_por_una_persona_no_es_el_verde_liso` | El anillo de F-026 R36 ya estaba. Lo que este test hace es **impedir que se pierda** al reescribir el bloque, que es exactamente el riesgo de esta tarea |
| `…r42_ningun_texto_de_la_plantilla_pinta_una_identidad` | Ningún `x-text` pintaba un `oid` antes tampoco. Lo caza el mutante M19 |
| `…r42_del_bloque_del_backend_solo_se_leen_las_cuatro_claves` | **Pasaba en vacío**: no había ninguna `estadoParte.` que mirar. Hoy sí las hay, y es lo que lo convierte en un test de verdad. Lo dejo dicho porque un verde así, antes, no medía nada — es la misma clase de test que §84.1 retira de F-026 |

---

## 83 · Decisiones de diseño, y las cuatro que hay que juzgar

### 83.1 · R43 no se puede leer de una sola respuesta, y por eso hay una función nueva

**Es la decisión con más contenido de la tarea**, y por eso va primero.

R43 pide distinguir dos hechos: «lo decidió una persona» y «el veredicto cambió
y la decisión dejó de contar». El primero lo dice el bloque:
`decidido_por_persona`. **El segundo no está publicado en ninguna clave.**

Cuando una aprobación caduca (R19), `decision_en_firme` devuelve `None` y
`bloque_de_estado` emite `decidido_por_persona: false`, `decidido_at_utc: null` y
`estado_anterior: null`. Es **byte a byte el mismo bloque** que el de un parte
que nadie ha mirado nunca. Mirando una sola respuesta, la pantalla no puede
cumplir R43.

Lo que sí distingue los dos casos es **el par de respuestas consecutivas**:
había una decisión firmada y, después de revalidar, ya no la hay. Eso es
`js/pipeline.js::avisoDeEstado(anterior, nuevo)`, que se llama en
`_anotarGuardado` **antes** de pisar `parte.estadoParte` —después ya no quedaría
con qué comparar— y deja el texto en `parte.avisoEstado`.

Tres cosas que hay que mirar de esta decisión:

1. **No deriva ningún estado** (R17). Los dos bloques vienen del backend tal
   cual; aquí no se calcula ninguno, solo se mira si la firma se perdió por el
   camino.
2. **Vive en `js/pipeline.js` y no en `js/app.js`**, porque comparar dos bloques
   es una decisión y las decisiones se prueban. Tiene 6 casos propios y la matan
   cuatro mutantes (M1 a M4).
3. **El aviso es por parte, no por pantalla.** `parte.avisoEstado` nace
   declarado en `_parteInicial` igual que todo lo demás: `_anotarGuardado` lo
   llama también el autoguardado, y un mensaje global se pintaría sobre el parte
   equivocado.

El texto **no acusa a nadie**, que es lo que R43 pide expresamente: dice que el
veredicto ha cambiado al revalidar, no que nadie hiciera nada mal. Quien corrigió
un campo estaba haciendo justo lo que la pantalla le pide. Tiene control negativo
propio (`…el aviso no acusa a nadie ni nombra a quien decidió`).

> **Alternativa descartada, y se dice:** publicar una quinta clave en el bloque
> —algo como `decision_caducada`— sería más directo, pero toca
> `estado_serializado.py` y el contrato que fija `tests/test_f028_estado_http.py`,
> que es backend y **no es T18**. Si el reviewer prefiere esa vía, es una tarea
> del bloque 5 reabierta, no una corrección de esta.

### 83.2 · El `oid` no aparece en la plantilla, ni dentro de una condición

La tarea pide que el test compruebe que «no aparece ningún `oid` en la
plantilla». Tomado al pie de la letra, el HTML de antes ya lo incumplía:
`index.html` traía `usuario.usuarioOid` en tres sitios —el `:disabled` del botón
de aprobar de F-026 y dos de la sección de la tanda de F-025—, aunque ninguno lo
**pintase**.

Lo que se ha hecho, en vez de relajar el test o de dejarlo pasar:

- la sección del estado pregunta por `hayIdentidad()`, un método de `app.js`, así
  que **el `oid` no aparece en ella ni una vez**, ni siquiera dentro de una
  condición. Lo comprueba `…r42_la_seccion_del_estado_no_pinta_ningun_oid`, que
  además de la lista de prohibidos busca `\boid\b` sin distinguir mayúsculas;
- y sobre **toda** la plantilla se comprueba lo que de verdad importa: que
  ningún `x-text` ni `x-html` —las dos formas que tiene Alpine de escribir un
  valor en la página— saque una identidad. Ese es
  `…r42_ningun_texto_de_la_plantilla_pinta_una_identidad`.

**Lo que NO se ha tocado** son los dos `usuario.usuarioOid` de la sección de la
tanda (F-025 P2). No pintan nada —son `:disabled` y un `x-show`— y esa sección no
es T18. Queda dicho aquí para que nadie lo lea como un descuido: si el reviewer
quiere el criterio literal en todo el fichero, es un cambio de una línea en
`index.html` y de otra en `app.js`, pero toca una feature cerrada.

### 83.3 · Un solo campo de motivo para los dos gestos

`design.md` §8.2 nombra `motivoDeRechazo` y `design.md` §7 dice que al rechazar
es obligatorio y al aprobar «se ofrece opcional». Se ha resuelto con **un solo
campo**, etiquetado «obligatorio para rechazar, opcional al aprobar», cuyo valor
viaja en los dos gestos.

Por qué uno y no dos: dos campos de texto para el mismo concepto, uno al lado del
otro, es la clase de pantalla en la que se escribe en el de arriba y se pulsa el
botón de abajo. Y el riesgo del campo único —escribir un motivo pensando en
rechazar y acabar aprobando— deja el motivo escrito en una aprobación, que es
información de más, nunca de menos.

Se conserva el nombre de la spec (`motivoDeRechazo`) aunque el campo sirva para
los dos: renombrarlo dejaría la spec y el código diciendo cosas distintas.

### 83.4 · `esAprobable`, `cuerpoDeAprobacion` y `MOTIVOS_APROBABLES` se van, y no era neutral dejarlos

§78 lo anticipaba y se cumple: los tres se retiran de `js/pipeline.js` con su
recuadro fechado. F-028 **deroga la pregunta** (R9, R10) igual que T15 la derogó
en el dominio.

Lo que hay que mirar, y no es solo limpieza: **`esAprobable()` escondía el gesto
en los partes aptos**. Mientras siguiera gobernando la sección, el botón de
**rechazar** no se habría ofrecido justo en los partes que esta feature existe
para poder rechazar antes de que se archiven. Dejarlo «por si acaso» habría
dejado la feature en una marca de color.

Con ellos se va `tests_js/aprobacion.test.js` entero (§84.2).

### Desviaciones respecto a la spec

**Una, y es un añadido.** `design.md` §8.2 dice que T18 toca `js/app.js` e
`index.html`; se ha tocado además **`js/pipeline.js`**, por dos motivos ya
razonados: la retirada de las tres piezas de F-026 (§83.4, que §78 declaraba como
trabajo de T18) y la función `avisoDeEstado` (§83.1), que va ahí porque `app.js`
no puede alojar una decisión sin tests.

El resto de la tarea se ha implementado tal cual.

---

## 84 · Los tests de antes que han cambiado, y por qué

Son **20**, en dos ficheros, y ninguno se ha «ajustado para que pase».

### 84.1 · Siete retirados de `tests/test_f026_front.py`, en cinco recuadros

De los catorce casos quedan **siete**. Los otros siete van con su recuadro
fechado en el sitio donde vivían, y **tres de ellos seguían en verde**:

| Retirado | Rojo o verde | Sustituto en `tests/test_f028_front.py` |
|---|---|---|
| `…r22_el_parte_declara_su_aprobacion_desde_que_nace` | **rojo** | `…r38_el_parte_declara_su_estado_desde_que_nace`, que además exige `avisoEstado` |
| `…la_aprobacion_nace_vacia_y_no_se_inventa_ninguna` | **rojo** | `…el_estado_nace_vacio_y_no_se_inventa_ninguno` + `…el_parte_ya_no_declara_la_aprobacion_de_f026` |
| `…el_front_no_decide_la_aprobacion_en_app_js` | **rojo** | `…r17_app_js_no_compone_el_cuerpo_ni_decide_nada` + `…el_front_ya_no_llama_al_endpoint_retirado` |
| `…r22_la_respuesta_de_aprobar_se_guarda_en_el_parte` | **rojo** | `…r38_lo_que_devuelve_el_guardado_es_lo_que_se_pinta`, que además exige que solo se pise cuando el guardado salió bien |
| `…r39_sin_ser_aprobable_no_se_ofrece_el_gesto` | **rojo** | `…r40_los_dos_botones_estan_en_el_detalle` + `…r41_el_parte_cerrado_no_ofrece_ningun_gesto` + `…r9_la_pregunta_…_queda_derogada` |
| `…r37_el_texto_dice_de_donde_venia_y_cuando` | **rojo** | `…r39_el_detalle_distingue_quien_decidio`. «De dónde venía» **no tiene sustituto y se dice**: el bloque `estado` no publica `destino_aprobado`, y F-028 no compara destinos. La fecha sí sobrevive |
| `…r39_cuando_no_es_aprobable_se_dice_que_hay_que_corregir` | **verde** | La sección nueva conserva el consejo —«si le falta el código de obra o el número de incidencia, corrígelo arriba y revalida»—, así que el test seguía pasando **dando por comprobada una condición que ya no existe** (`x-show="!esAprobable()"`) |
| `…r38_la_pantalla_no_pinta_quien_aprobo` | **verde, y en verde por nada** | Recorría las líneas del detalle que contienen `aprobacion`, y desde este commit no hay ninguna: **iteraba sobre una lista vacía**. Sustituto: los dos controles de R42, uno de ellos sobre toda la plantilla |
| `…r38_el_bloque_de_aprobacion_solo_usa_las_cuatro_claves_publicadas` | **verde, y en verde por nada** | Comparaba un conjunto vacío contra las cuatro claves permitidas. Sustituto: `…r42_del_bloque_del_backend_solo_se_leen_las_cuatro_claves`, que sí tiene claves que mirar |

Los tres verdes merecen el párrafo que ya se han ganado los bloques 4, 5 y 6: **un
test que no puede fallar no protege nada**, y estos dos últimos eran los que
sostenían el requisito de privacidad, que es de los que más pesan de la feature.

**Lo que se queda, y es deliberado**: que el gesto vive en el detalle y no en la
lista, que no se arma ninguna segunda confirmación, que el aprobado por una
persona no se pinta como el verde liso y que la tanda no habla solo de verdes.
Los cuatro siguen siendo ciertos con F-028 y los cuatro siguen en verde sin una
sola edición. La cabecera del fichero lo dice en un recuadro fechado.

### 84.2 · `tests_js/aprobacion.test.js` · el fichero entero, 13 casos

Se retira completo porque sus trece casos prueban las tres piezas que T18 borra:

- **7 de `esAprobable` y `MOTIVOS_APROBABLES`** (R6 a R10 de F-026): la lista de
  motivos, los dos aprobables, el motivo fuera de la lista, el parte sin código
  de obra, el apto que «no tiene nada que aprobar» y el parte sin veredicto.
  **No tienen sustituto y no hace falta buscárselo**: F-028 deroga la pregunta
  (R9, R10). Lo que sí tiene control es la derogación en sí:
  `test_f028_r9_la_pregunta_de_si_un_parte_es_aprobable_queda_derogada`.
- **6 de `cuerpoDeAprobacion`** (R4, R19, R29 de F-026): sin `oid` no se compone,
  el booleano de la confirmación, el cuerpo es el de guardar más dos claves, no
  viajan los bytes del PDF, el no aprobable se niega, y sin remesa no se compone.
  **Los cinco primeros tienen sustituto uno a uno** en la sección T16 de
  `tests_js/estado.test.js`, y los sustitutos son más anchos —el de `oid` cubre
  ahora cuatro formas de vacío, incluida la cadena de espacios que la fase RED de
  T16 destapó—. El sexto («el no aprobable se niega») se va con la pregunta.

Con el fichero se van sus cinco ayudantes y el `require` de `cuerpoDeParte`.

Es la misma decisión que T15 tomó con `test_f026_persistencia.py` y
`test_f026_aprobar_http.py` (§64.2, §64.3): cuando lo que se retira es el
mecanismo entero, el fichero se va con él y la tabla «retirado → sustituto»
queda escrita aquí.

---

## 85 · La verificación de T18, recontada

T18 pide seis cosas y las cuatro que el encargo subraya van primero:

| Lo que pide la tarea | Dónde se fija |
|---|---|
| **El botón de rechazar está deshabilitado mientras no haya motivo** | `…r11_el_boton_de_rechazar_esta_deshabilitado_sin_motivo`, que busca el `:disabled` del botón **y** que mire `puedeRechazar()`; `…r11_puede_rechazar_exige_el_motivo`; y `…r11_hay_motivo_no_acepta_una_cadena_de_espacios`, que cierra el hueco del `truthy` que T16 encontró en el `oid`. Mutantes M5, M6 y M13 |
| **La frase del parte `cerrado`** (R41) | `…r41_la_pantalla_explica_por_que_no_se_puede_cambiar` (la frase, literal) y `…r41_el_parte_cerrado_no_ofrece_ningun_gesto`, que comprueba que **cada uno de los tres gestos** —aprobar, rechazar y el campo de motivo— está dentro de una plantilla cuya condición niega `estaCerrado`. Mutantes M14 y M15 |
| **Ningún `oid` en la plantilla** | `…r42_la_seccion_del_estado_no_pinta_ningun_oid` y `…r42_ningun_texto_de_la_plantilla_pinta_una_identidad`. El alcance exacto y lo que queda fuera, en §83.2. Mutante M19 |
| **Las cuatro marcas se distinguen de verdad, y el aprobado por persona del de la máquina** (R39) | `…r38_la_lista_pinta_las_cuatro_marcas` (las seis clases), `…r38_el_rechazado_no_se_pinta_como_el_pendiente` y `…el_cerrado_tiene_marca_propia_y_candado`, los dos **grupo de clases a grupo de clases**, y `…r39_el_aprobado_por_una_persona_no_es_el_verde_liso`. Mutantes M16 y M17 |
| Los dos botones en el detalle (R40), y ninguno en la lista (R36) | `…r40_los_dos_botones_estan_en_el_detalle` y `…r36_ningun_gesto_en_la_lista` |
| El campo de motivo, acotado con el límite del dominio (R13) | `…r40_el_campo_de_motivo_esta_en_el_detalle` y `…r13_el_campo_de_motivo_se_acota_con_el_limite_del_dominio`, que además exige que **no** haya un `maxlength` literal al lado. Mutante M18 |
| Las cuatro marcas **en el detalle** y no solo en la lista (R38) | `…r38_el_detalle_tambien_enseña_el_estado` |
| Los textos de R43 | `…r43_la_pantalla_avisa_cuando_la_decision_deja_de_contar`, `…r43_el_aviso_lo_decide_pipeline_y_no_app_js`, `…r43_el_aviso_se_calcula_antes_de_pisar_el_estado` y los 6 casos de `tests_js/estado.test.js`. Mutantes M1 a M4, M10 y M20 |

Y cuatro que no pide la tarea y sostienen el resto: que el estado **solo** se
pisa cuando el guardado salió bien (M8), que la marca sale del bloque del backend
y no del veredicto (M7), que la marca «por una persona» sale de
`decidido_por_persona` y no de comparar estados (M11), y que `app.js` no compone
ningún cuerpo ni llama a nada retirado.

### 85.1 · Y una verificación que no es un test: la pantalla se ha ejecutado

`js/app.js` no tiene tests por diseño —es la única habitación sin tests de la
casa, y `test_f007_r36_app_js_es_solo_pegamento` existe para que siga
vacía—, así que todo lo de arriba comprueba **texto**. Para no entregar una
pantalla que solo se ha leído, se cargaron los nueve `js/*.js` en un contexto de
Node —en el mismo orden que `index.html`, con `fetch` doble que lanza si alguien
lo toca— y se ejercitaron los métodos nuevos contra objetos en memoria:

```
OK   estadoDelParte: "aprobado"          OK   puedeRechazar sin motivo: false
OK   etiquetaDeEstado: "Aprobado"        OK   puedeRechazar con espacios: false
OK   decidioUnaPersona: true             OK   puedeRechazar con motivo: true
OK   estaCerrado(cerrado): true          OK   puedeRechazar sin identidad: false
OK   etiqueta(sin bloque): ""            OK   avisoEstado tras caducar: La decisión…
OK   estadoParte pisado: "pendiente"     OK   guardado fallido no pisa: "aprobado"
OK   cuerpo.estado: "rechazado"          OK   guardado fallido no avisa: ""
OK   semaforo del rechazado: "rechazado" OK   el rechazado sale de la tanda: 0
exit=0
```

23 comprobaciones, 23 en verde. **No se ha versionado**: el script vive en el
área de trabajo de la sesión, porque convertirlo en suite sería decidir que
`app.js` pasa a tener tests, y eso es una decisión de arquitectura que no me
toca. Queda propuesto en §88.

Además, `index.html` se ha validado con un analizador: **ninguna etiqueta
descuadrada, ninguna sin cerrar**, y cada `<template x-if>` con **una sola raíz**,
que es lo que Alpine exige y lo que ningún test de texto habría cazado.

---

## 86 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `front`, Python) | **250 pasados, 0 fallos** | `bash harness/init.sh` |
| **Tests ejecutados** (servicio `front`, JavaScript) | **298 pasados, 0 fallos** | `node --test "tests_js/*.test.js"`, que lanza el puente `tests/test_f007_js.py` |
| Tests ejecutados (servicio `api`) | **2.528 pasados, 13 saltados** | sin cambios: el backend entero está fuera del diff |
| Tests ejecutados (arnés, raíz) | **62 pasados** | `bash harness/init.sh` |
| De ellos, **nuevos de T18** | **42** — 36 en `tests/test_f028_front.py` y 6 en `tests_js/estado.test.js` | las dos suites |
| Tests **retirados** | **20** — 13 de `tests_js/aprobacion.test.js` (el fichero entero) y 7 de `tests/test_f026_front.py`, todos con su sustituto o su derogación en §84 | — |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 283/283, umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `init.sh`. **Ver §86.1: no mide nada de esta tarea** |
| **Mutantes generados / supervivientes** | automáticos **31 / 0** (0 timeouts, 146,1 s) · **a mano 21 / 0** | `python -m harness.mutacion --feature F-028` y §86.2 |
| **Tiempo de la suite** | `front` **1,94 s** (Python) + **0,35 s** (JavaScript) · raíz 2,35 s · `api` sin ejecutar de nuevo (árbol sin cambios) | la propia suite |
| **Ruff** | `All checks passed` sobre los dos `.py` tocados; el repositorio sigue en **61** avisos, sin crecer | `python -m ruff check` |

### Los supervivientes, y qué se hace con cada uno

**Ninguno al cerrar**, ni en la campaña automática ni en la manual. Pero la
manual **tuvo dos en la primera pasada**, y eso es lo que más vale de esta
sección: ver §86.3.

### 86.1 · Lo que hay que mirar de las evidencias: **ni la cobertura ni la campaña miden esta tarea**

Va en voz alta, como en §76.1, porque presentarlo de otro modo sería el número
que tranquiliza sin medir nada.

**La puerta de cobertura da 100,0 % de 283 líneas, y son las mismas 283 líneas de
T15, T16 y T17.** El arnés mide cobertura de **Python** (`harness/servicios.json`
lo dice: el front va con lenguaje `python` por `dev_server.py`), y T18 no toca una
sola línea de Python de producción. Lo que esta tarea cambia son **423 líneas añadidas y 247 retiradas de
JavaScript y de HTML** —`index.html` 166/69, `js/app.js` 174/76,
`js/pipeline.js` 83/102—, y no entran en esa cifra ni pueden entrar.

**Y la campaña automática no genera ni un mutante de T18**: `harness.mutacion`
muta ficheros `.py`. Los 31 mutantes son de los bloques 1 a 5 y **siguen
muriendo** —que también es información: la pantalla no ha roto nada de lo ya
probado—, pero no dicen nada de esta tarea.

Lo que sí la respalda son los **21 mutantes a mano** de §86.2 y la ejecución real
de §85.1.

> **Propagación pendiente a `arnes-base`, y no la hago yo.** Es el mismo hueco que
> anotó §76.1 y ya lleva dos bloques seguidos: un servicio con código en **dos
> lenguajes** mide y muta solo uno, y ni `init.sh` ni el informe de mutación lo
> dicen. Queda anotado para el líder; el implementer no toca el arnés por su
> cuenta.

### 86.2 · Los 21 mutantes **a mano**, que son la evidencia que sí respalda la tarea

Mismo método que los bloques 3 a 6: se aplica la mutación sobre el fichero, se
corre la suite del front entera —`pytest`, que arrastra `node --test` por el
puente— y se restaura. «Muerto» = al menos un caso falla. El script está en el
área de trabajo de la sesión, restaura cada fichero en un `finally` y el árbol
quedó limpio, comprobado con `git status`.

| # | Mutante aplicado a mano | Resultado | Quién lo caza |
|---|---|---|---|
| M1 | `avisoDeEstado` no avisa nunca (R43) | **muerto** | `f028 R43: si había decisión de una persona y deja de haberla, se avisa` |
| M2 | avisa también de un parte que **nunca** decidió nadie | **muerto** | `f028 R43: un parte que nunca decidió nadie no estrena ningún aviso` |
| M3 | avisa aunque la decisión **siga firmada** | **muerto** | `f028 R43: mientras la decisión siga firmada no se avisa de nada` |
| M4 | el aviso mira el **estado** en vez de quién firmó | **muerto** | los seis casos de R43 |
| M5 | `hayMotivo` deja de recortar: un motivo de espacios habilita el botón (R11) | **muerto** | `…r11_hay_motivo_no_acepta_una_cadena_de_espacios` |
| M6 | `puedeRechazar` deja de exigir motivo (R11) | **muerto** | `…r11_puede_rechazar_exige_el_motivo` |
| M7 | la marca vuelve a salir del bloque `aprobacion` viejo (R17) | **muerto** | `…r17_la_marca_sale_del_estado_y_no_del_veredicto` |
| M8 | un guardado fallido **pisa** el estado que sigue en la base (R38) | **muerto** | `…r38_lo_que_devuelve_el_guardado_es_lo_que_se_pinta` |
| M9 | `estadoParte` deja de nacer declarado: la marca no repinta | **muerto** | `…r38_el_parte_declara_su_estado_desde_que_nace` |
| M10 | `avisoEstado` deja de nacer declarado (R43) | **muerto** | ídem |
| M11 | la marca «por una persona» se deduce del **estado** y no de `decidido_por_persona` (R39) | **muerto** | `…r39_la_marca_por_persona_sale_de_la_clave_del_backend` |
| M12 | `estaCerrado` duplica el literal `"cerrado"` en `app.js` | **muerto** | `…r41_estar_cerrado_lo_dice_el_backend` |
| M13 | el botón de rechazar pierde su `:disabled` (R11) | **muerto** | `…r11_el_boton_de_rechazar_esta_deshabilitado_sin_motivo` |
| M14 | se ofrecen los dos gestos **sobre un parte cerrado** (R41) | **muerto** | `…r41_el_parte_cerrado_no_ofrece_ningun_gesto` — **y en la primera pasada sobrevivió: §86.3** |
| M15 | desaparece la frase que explica el cerrado (R41) | **muerto** | `…r41_la_pantalla_explica_por_que_no_se_puede_cambiar` |
| M16 | el rechazado se pinta **como un pendiente** (R38) | **muerto** | `…r38_el_rechazado_no_se_pinta_como_el_pendiente` — **también sobrevivió: §86.3** |
| M17 | el cerrado pierde el candado (R38) | **muerto** | `…el_cerrado_tiene_marca_propia_y_candado` |
| M18 | el límite del motivo se escribe a mano en la plantilla (R13) | **muerto** | `…r13_el_campo_de_motivo_se_acota_con_el_limite_del_dominio` |
| M19 | el `oid` vuelve a la plantilla (R42) | **muerto** | `…r42_la_seccion_del_estado_no_pinta_ningun_oid` |
| M20 | el aviso de R43 deja de pintarse | **muerto** | `…r43_la_pantalla_avisa_cuando_la_decision_deja_de_contar` |
| M21 | vuelve `esAprobable` a `js/pipeline.js` (R9, R10) | **muerto** | `…r9_la_pregunta_de_si_un_parte_es_aprobable_queda_derogada` |

**21 de 21 muertos.** Los que más valen:

- **M14** es, literalmente, ofrecerle a alguien dos botones sobre una incidencia
  ya cerrada en el ERP: la petición sale, el backend responde 409 y lo que ve
  quien pulsó es un error en vez de la explicación que R41 pide.
- **M13 y M6** son las dos formas de dejar rechazar sin motivo. Lo que se pierde
  no se recupera después: quien vuelva a mirar el parte dentro de un mes no sabrá
  qué había que arreglar.
- **M8** es el que borra de la pantalla una decisión que sigue escrita en la base,
  y lo hace en el caso en que menos se mira: cuando el guardado ya ha fallado.
- **M11** es la trampa de R43 que §53 ya había señalado en el backend, escrita
  esta vez en el front: anunciar «lo decidió una persona» sobre una decisión que
  R19 tumbó.

### 86.3 · Los dos supervivientes de la primera pasada, y qué agujero tapaban

Esto es lo que la campaña a mano existe para encontrar, así que va entero y no en
una nota.

**M14 · «se ofrecen los dos gestos sobre un parte cerrado» sobrevivió.** El test
de R41 comprobaba que la sección contuviera `estaCerrado(` y que apareciera
*antes* del primer botón. Las dos cosas seguían siendo ciertas con la condición
puesta a `true`, porque la frase del cerrado —que está más arriba— también
nombra `estaCerrado`. Un test que mira si una palabra aparece «antes» de otra no
comprueba anidamiento.

Arreglo: el test recorre las plantillas con **una pila**, encuentra el
`<template x-if>` más interno que envuelve a cada gesto y exige que su condición
**niegue** `estaCerrado`. Se comprueba para los tres —aprobar, rechazar y el
campo de motivo—, no solo para el primero. No se usa una expresión regular a
propósito: las plantillas están anidadas y una regex no codiciosa cerraría en la
plantilla equivocada, que es el mismo tipo de error que dejó pasar M14.

**M16 · «el rechazado se pinta como un pendiente» sobrevivió.** El test metía
**todos** los `:class` de la lista en un solo diccionario. Como el punto de color
y la etiqueta de texto usan clases distintas para la misma marca, la clase de la
etiqueta tapaba la del punto y la comparación se hacía sobre el grupo
equivocado.

Arreglo: `_grupos_de_marcas` devuelve **un diccionario por cada `:class`**, y el
test exige que dentro de cada grupo el rechazado no comparta clase con el ámbar
ni con el rojo. El de `cerrado` se reescribió igual y ahora lo compara contra las
cinco marcas restantes, no solo contra el verde.

Los dos agujeros tenían la misma forma —**un test de texto que da por comprobada
una estructura sin mirar la estructura**— y los dos habrían pasado la revisión sin
que nadie los viera. Después del arreglo: **21 de 21 muertos**, y los 36 casos
siguen en verde.

### 86.4 · La línea base estaba verde, y se comprobó antes de creerse el resultado

Como avisaba el encargo y como enseñó T13 (§44.1): `bash harness/init.sh` →
**ENTORNO LISTO** antes de tocar nada, con `62 passed` en la raíz, los dos
servicios en verde y la puerta de cobertura al 100,0 %.

---

## 87 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes y esta tarea **no crea ninguna nueva**, pero deja
listas para ejecutar las dos que le faltaban su mitad de pantalla:

- **T27.4** («un parte apto rechazado a mano no se archiva»): ya se puede
  ejecutar **entera desde la web**. La mitad del backend está desde el bloque 4,
  la de la tanda desde T17 y **el botón de rechazar es esto**.
- **T27.5** («un parte cerrado responde 409 y la web lo explica»): la frase de
  R41 ya está, y la pantalla **no llega a pedir el 409**, porque no ofrece el
  gesto. Quien verifique tiene que mirar las dos cosas: que la web lo explica, y
  que el 409 sigue estando para quien llame al endpoint por su cuenta (eso lo
  cubre `tests/test_f028_estado_http.py`).

Dos cosas que conviene mirar con el navegador delante y que ningún test de texto
comprueba, y por eso van aquí:

1. **Que el `🔒` se ve** en el navegador de quien revisa. Es un carácter, no una
   imagen, y depende de la fuente del sistema. Si se viera como un cuadro, la
   marca del cerrado sigue distinguiéndose por color y por la palabra
   «Cerrado» —de ahí que la etiqueta lleve texto y no solo el candado—, pero
   conviene saberlo.
2. **Que el campo de motivo no molesta en los partes verdes.** Está siempre
   visible mientras el parte no esté cerrado, y en una remesa de 22 partes aptos
   nadie lo va a usar. Si estorba, esconderlo detrás del botón de rechazar es un
   cambio pequeño, pero es una decisión de quien usa la pantalla y no mía.

**La base real y el ERP no se han tocado**: todo lo de esta tarea corre contra el
texto de los ficheros y contra objetos en memoria, sin red, sin BBDD y sin IA. La
guardia de red de sesión de `tests/conftest.py` sigue puesta, y el `fetch` del
script de humo lanza si alguien lo llama.

---

## 88 · Lo que queda fuera del alcance de T18, y hay que decirlo

1. **`docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md` siguen
   documentando `POST /api/aprobar`.** Es **T25** (R59, bloque 9) y no se ha
   tocado nada. Sigue siendo cierto lo que anotó §67.2: el documento afirma doce
   endpoints y el servicio publica doce, pero **no son los mismos doce**.
2. **`js/app.js` sigue sin tener tests**, y ahora tiene bastante más lógica de
   pantalla que antes —nueve métodos nuevos—. Todo lo que **decide** algo está en
   `js/pipeline.js`, y `test_f007_r36_app_js_es_solo_pegamento` sigue en verde,
   así que la regla se respeta. Pero el script de §85.1 demuestra que **se puede
   ejecutar `app.js` bajo Node sin navegador**, en 40 líneas y sin dependencias.
   Convertirlo en `tests_js/app.test.js` es una decisión de arquitectura del front
   (F-007 `design.md` §3) y **la dejo para el líder**, no la tomo yo.
3. **Los dos `usuario.usuarioOid` de la sección de la tanda** (F-025) siguen en
   `index.html`. No pintan nada y esa sección no es T18; el razonamiento entero
   está en §83.2.
4. **R43 se resuelve comparando dos respuestas y no leyendo una clave.** Funciona
   y está probado, pero depende de que la pantalla haya visto la respuesta
   anterior: si alguien recarga la página, el aviso se pierde —aunque también se
   pierde la remesa entera, que es lo que F-019 R30 ya declara—. La alternativa
   —publicar la caducidad en el bloque— es backend y está razonada en §83.1.
5. **`ParteNoAprobable` sigue en `domain/models/errores.py` sin que nadie lo
   levante**, igual que anotó §67.3. Con T18 se queda además sin su último
   pariente en el front. Sigue siendo del líder.

---

## 89 · Estado al cerrar el encargo · **la rama vuelve a ser desplegable**

Lo digo explícitamente porque es lo que pedía el encargo.

**Sí, la rama es desplegable.** Las tres líneas que §73.4 dejó rotas a propósito
están arregladas, y se ha comprobado una por una:

| Lo que estaba roto | Cómo se comprueba que ya no |
|---|---|
| `js/app.js:546 · api.aprobar(cuerpo, parte.hash)` — el método no existe desde T16 | `test_f028_el_front_ya_no_llama_al_endpoint_retirado`, que busca `api.aprobar(` en `app.js`. Hoy llama a `api.cambiarEstado(`, que sí existe y apunta a `POST /api/estado`, que el backend publica desde T13 |
| `cuerpoDeAprobacion` — componía para un endpoint retirado | La función ya no existe en `js/pipeline.js` (mutante M21) y `app.js` usa `cuerpoDeCambioDeEstado` |
| `semaforoDe(validacion, parte.aprobacion)` — le pasaba el bloque viejo, que el backend ya no emite | `test_f028_r17_la_marca_sale_del_estado_y_no_del_veredicto` (mutante M7) |

Y no queda ninguna otra llamada del front a algo que el backend no sirva: los
doce endpoints de `LOS_ENDPOINTS` en `tests_js/api.test.js` siguen comprobados
nombre a nombre.

- `bash harness/init.sh` → **ENTORNO LISTO**, en verde, con la puerta de cobertura
  al **100,0 %** de las 283 líneas cambiadas (que son las de Python: ver §86.1).
- Árbol limpio, **2 commits** sobre `5b3fe22` (`4b85e6b` T18 y el de este
  informe), los dos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla `done`
  no es cosa del implementer.
- **No se ha entrado en el bloque 7**, como pedía el encargo: `normalizar_codigo`,
  `tramos_de_codigo`, `nombre_de_archivo` y `a_codigo_de_sigrid` están sin tocar,
  y `tests/test_f028_espacios_codigos.py` no existe.
- **La base real y el ERP no se han tocado.** El backend entero está fuera del
  diff: `git diff 5b3fe22 -- services/postventa-api/` está vacío.

---

# F-028 · Estado del parte — informe del implementer · bloque 7, T19 y T20

> **Encargo del 2026-09-16**: T19 y T20 del bloque 7 —el defecto de los
> espacios en los códigos—, y parar. No entrar en T21 ni en T22.
>
> ## ⛔ LÉASE ESTO ANTES QUE NADA: la rama **NO es desplegable** en este commit
>
> `bash harness/init.sh` sale **EN ROJO**, y no solo por el test que T21 tiene
> que actualizar. Hay **25 tests en rojo**, y **24 de ellos son una sola
> causa**: `a_codigo_de_sigrid` todavía convierte con `replace(" - ", "/")`, y
> el arreglo de T20 deja esa sustitución sin efecto. Componer por tramos es
> **T22**, que el encargo prohíbe expresamente tocar.
>
> **T20 y T22 no se pueden separar.** No es una decisión mía ni un descuido:
> es una consecuencia inevitable de R44, y la explico entera en **§94**. La
> línea de verificación de T20 en `tasks.md` —«T19 en verde»— **no es
> alcanzable** sin T22, y T22 lo delata al pedir «T19 **entero** en verde».
>
> Lo que sí se ha cumplido, y era la condición que puso el encargo:
> `tests/test_f006_nombrado.py` está **entero en verde salvo un único test**,
> `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, que es el de T21 y
> **no se ha tocado**. Ningún otro de ese fichero se ha puesto en rojo.

---

## 90 · Qué se ha hecho, en una frase por tarea

- **T19** (`98968c8`) · `tests/test_f028_espacios_codigos.py`: la tabla de
  `design.md` §9.3 recorrida **entera y fila a fila** para las dos
  conversiones, escrita **antes** de tocar el dominio. Falló donde tenía que
  fallar: las **tres filas rotas**, con la quinta rompiendo además el nombre
  del fichero. Trazas pegadas en **§92**.
- **T20** (`c12d826`) · el arreglo, en `normalizar_codigo` (R44), más
  `SEPARADORES_DE_CODIGO` y `tramos_de_codigo`; `nombre_de_archivo` compone
  uniendo los tramos (R46, R48, R49).

---

## 91 · Ficheros tocados

### Creados

| Fichero | Qué es |
|---|---|
| `services/postventa-api/tests/test_f028_espacios_codigos.py` | **59 casos**. La tabla de §9.3 para las dos conversiones, el saneo de R44 sobre `normalizar_codigo` directamente, los tramos, y los control-negativo de R48 y R49 |

### Modificados

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | `import re`; `SEPARADORES_DE_CODIGO`; dos expresiones regulares privadas; `normalizar_codigo` quita los espacios del separador; `tramos_de_codigo` nueva; `nombre_de_archivo` compone por tramos y se niega si no hay ninguno; `__all__` al día |
| `specs/F-028-estado-del-parte/tasks.md` | T19 y T20 marcadas `[x]` |

**Ni una línea más.** El diff de producción del bloque 7 es **un solo fichero**:
`services/postventa-api/domain/models/nombrado.py`. `git diff 71a5e00 --stat`
sobre `domain/`, `application/`, `infrastructure/` e `interface_adapters/` no
devuelve ningún otro.

### Lo que la spec prohíbe tocar, y que sigue intacto

- `domain/models/validacion.py` y `sql/04_validaciones.sql` — **sin tocar**
  (regla dura 1).
- `huella_de_veredicto` y `aprobacion.py::_normalizar` — **sin tocar** (regla
  dura 2, D9). Ver §93.4: el riesgo de la ficha está medido y **no ocurre**.
- `infrastructure/sigrid/` y `infrastructure/sharepoint/` — **sin tocar**.
- `sql/10_aprobaciones.sql` — **sin tocar** (regla dura 3).
- `domain/models/cierre.py` — **sin tocar**: es T22.
- `harness/features.json` — **sin tocar**. F-028 sigue `in_progress`.
- `azure-apps/` — **sin tocar**.
- **Ni base de datos real, ni ERP, ni SharePoint, ni red, ni IA.** Todo lo de
  este bloque son dos cadenas entrando en una función pura.

---

## 92 · Fase RED · las trazas, pegadas

Comando exacto, sobre el árbol **sin una línea del dominio tocada** (commit
`71a5e00` más el fichero de test):

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_espacios_codigos.py -q
...
14 failed, 16 passed in 0.23s
```

### 92.1 · Las tres filas rotas de la conversión al ERP (R45)

Es el defecto que el responsable vio fallar en real el 2026-09-15.

```
$ ./.venv/Scripts/python.exe -m pytest "tests/test_f028_espacios_codigos.py::test_f028_r45_todas_las_formas_dan_el_mismo_codigo_para_el_erp" -q

E       AssertionError: la forma «barra con espacio a los dos lados» no llega al ERP como la canónica
E       assert 'RS26.09 / 0149' == 'RS26.09/0149'
E         - RS26.09/0149
E         + RS26.09 / 0149
E         ?        + +
E       AssertionError: la forma «barra con espacio solo delante» no llega al ERP como la canónica
E       assert 'RS26.09 /0149' == 'RS26.09/0149'
E         - RS26.09/0149
E         + RS26.09 /0149
E         ?        +
E       AssertionError: la forma «guion normal pegado delante y con espacio detrás» no llega al ERP como la canónica
E       assert 'RS26.09- 0149' == 'RS26.09/0149'
E         - RS26.09/0149
E         ?        ^
E         + RS26.09- 0149
E         ?        ^^

3 failed, 3 passed in 0.17s
```

**Tres rotas de seis, y las otras tres ya pasaban.** Eso es exactamente lo que
tenía el defecto escondido: la forma canónica y las dos de guion «normal»
funcionaban, así que en una revisión por encima el circuito parecía bien.

### 92.2 · La fila que además estropea el nombre del fichero (R46)

```
$ ./.venv/Scripts/python.exe -m pytest "tests/test_f028_espacios_codigos.py::test_f028_r46_todas_las_formas_dan_el_mismo_nombre_de_fichero" -q

E       AssertionError: la forma «guion normal pegado delante y con espacio detrás» se archivaría con otro nombre
E       assert '0626 - RS26....E FIRMADO.pdf' == '0626 - RS26....E FIRMADO.pdf'
E         - 0626 - RS26.09 - 0149 PARTE FIRMADO.pdf
E         ?               -
E         + 0626 - RS26.09- 0149 PARTE FIRMADO.pdf
```

**Una sola de las seis.** Las otras cinco salían bien **por casualidad**: la
barra pasa a `" - "` y el colapso posterior se comía el sobrante. Por eso el
parte se archivaba con el nombre correcto y **solo fallaba el cierre** — medio
circuito en verde tapando la mitad rota.

### 92.3 · El saneo, donde R44 dice que vive

```
$ ./.venv/Scripts/python.exe -m pytest "tests/test_f028_espacios_codigos.py::test_f028_r44_normalizar_quita_los_espacios_que_rodean_al_separador" -q

E       AssertionError: la forma «barra con espacio a los dos lados» normaliza a «RS26.09 / 0149»
E       assert 'RS26.09 / 0149' in ('RS26.09/0149', 'RS26.09-0149')
E       AssertionError: la forma «barra con espacio solo delante» normaliza a «RS26.09 /0149»
E       assert 'RS26.09 /0149' in ('RS26.09/0149', 'RS26.09-0149')
E       AssertionError: la forma «guion normal con espacio a los dos lados» normaliza a «RS26.09 - 0149»
E       assert 'RS26.09 - 0149' in ('RS26.09/0149', 'RS26.09-0149')
E       AssertionError: la forma «guion normal pegado delante y con espacio detrás» normaliza a «RS26.09- 0149»
E       assert 'RS26.09- 0149' in ('RS26.09/0149', 'RS26.09-0149')
E       AssertionError: la forma «guion largo con espacio a los dos lados» normaliza a «RS26.09 - 0149»
E       assert 'RS26.09 - 0149' in ('RS26.09/0149', 'RS26.09-0149')

5 failed, 1 passed in 0.15s
```

Cinco de seis. Se afirma **sobre `normalizar_codigo` directamente** y no solo
por sus resultados porque es donde R44 pone el arreglo: comprobarlo únicamente
por las dos puntas dejaría pasar un saneo local en una de ellas, que es lo que
R47 prohíbe.

---

## 93 · Decisiones de diseño, y las tres que hay que juzgar

### 93.1 · El saneo va en `normalizar_codigo`, y eso es lo que rompe T20 sin T22

`design.md` §9.1 lo manda y la docstring de `a_codigo_de_sigrid` lo razonaba
desde F-009: «se apoya en `normalizar_codigo` —no en una copia— […] dos
criterios del mismo concepto divergen siempre».

Y la prueba de que el sitio es ese la da la fila `RS26.09- 0149`: es la
**única** que estropea también el nombre del fichero. Un saneo puesto en el
lado del ERP la habría dejado viva en el archivo de Posventa.

La consecuencia —que la conversión al ERP se queda rota hasta T22— está en §94.

### 93.2 · Un nº de incidencia de **solo separadores** ahora se niega (R49)

Es lo único que hago y que `tasks.md` no enumera, así que va por delante para
que el reviewer lo juzgue.

`"/"` **no** normaliza a la cadena vacía —es un carácter—, así que la guardia
de F-006 R6 lo deja pasar. Con el nombre compuesto por tramos, unir **cero**
tramos daría `0626 -  PARTE FIRMADO.pdf`: con un espacio doble y sin número. Y
`nombre_admisible` **lo acepta**: no lleva ningún carácter prohibido, no empieza
ni acaba en espacio y no acaba en punto.

Es decir: se archivaría en Posventa un fichero con un nombre que nadie pidió, en
un archivo que se consulta a mano, y nadie se enteraría — que es literalmente el
escenario que F-006 R7 existe para impedir.

Se levanta `NombradoImposible` con un motivo que **nombra el campo**, como los
otros dos, y con seis casos que lo fijan (`/`, `-`, ` / `, `//`, ` - - `).

> Antes de T20 ese caso tampoco estaba bien: `"/"` producía
> `0677 - - PARTE FIRMADO.pdf`. No es una regresión que yo abra, es un agujero
> que el cambio deja a la vista y se tapa en el mismo commit.

### 93.3 · El código de **obra** no pasa por los tramos, y tiene test propio

`design.md` §9.2 lo dice con todas las letras y es la trampa obvia del cambio:
`06-77` es **una** obra escrita con guion, no dos tramos. Si la obra se
compusiera por tramos, el guion pasaría a `" - "` y —mucho peor— la carpeta se
partiría en una subcarpeta que nadie pidió.

Lo fija `test_f028_r48_el_codigo_de_obra_no_se_parte_en_tramos`, que comprueba
**el nombre y la carpeta**, y lo respalda el mutante **M14** de §95.2, que muere.

### 93.4 · El riesgo de la huella: ya estaba descartado y **no se ha rediseñado nada por él**

La ficha avisaba de que cambiar la normalización podría revocar aprobaciones
vigentes. Está medido y no ocurre, y el encargo lo daba por cerrado. Lo dejo
comprobado también desde aquí, con el diff en la mano:

- `aprobacion.py` **no importa nada** de `nombrado.py`
  (`grep -n "nombrado" domain/models/aprobacion.py` no devuelve nada);
- la huella usa `aprobacion.py::_normalizar`, que es otra función y **no se ha
  tocado**;
- `domain/models/aprobacion.py` no aparece en el diff del bloque.

El control explícito es el **bloque 8**, y no se ha adelantado.

---

## 94 · ⛔ Lo que queda en rojo, por qué, y por qué no lo he arreglado

### 94.1 · Los 25 rojos, y sus **dos** causas

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest -q --tb=no
25 failed, 2562 passed, 13 skipped in 21.42s
```

| Cuántos | Tests | Causa | Lo arregla |
|---|---|---|---|
| **1** | `test_f006_nombrado.py::test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` | Afirma `normalizar_codigo("RS26.08   -    0123") == "RS26.08 - 0123"`; ahora da `"RS26.08-0123"` | **T21**, que cambia su expectativa. **No lo he tocado**, como pedía el encargo |
| **24** | `test_f009_consultas.py` (3), `test_f009_dominio_cierre.py` (1), `test_f009_paso_cierre.py` (5), `test_f012_cerrar_exige_grafico.py` (1), `test_f028_puertas.py` (4), `test_f028_espacios_codigos.py` (10) | **Una sola**: `a_codigo_de_sigrid` | **T22** |

Los 24 fallan todos con la misma forma. Este es el de `test_f028_puertas.py`,
que es la red de seguridad de T1 y por eso es el que más duele ver:

```
E   AssertionError: assert ['XX00.00-0000'] == ['XX00.00/0000']
```

### 94.2 · Por qué T20 rompe `a_codigo_de_sigrid`, y por qué era inevitable

`a_codigo_de_sigrid` convierte así, desde F-009:

```python
codigo = normalizar_codigo(bruto)                        # "RS26.08 - 0123"
return " ".join(codigo.replace(SEPARADOR, "/").split())  # SEPARADOR == " - "
```

Su conversión **depende de que `normalizar_codigo` deje los espacios puestos**:
busca literalmente `" - "`. R44 manda quitarlos. Así que en cuanto el arreglo
entra, `normalizar_codigo("RS26.08 - 0123")` da `"RS26.08-0123"`, el `replace`
ya no encuentra nada y el código sale con guion en vez de con barra.

**No hay forma de cumplir R44 sin romper esa línea**, y por eso `design.md` §9.2
rehace las dos conversiones por tramos. La única punta que T20 rehace es la del
nombre; la otra es T22, de una línea.

> **Discrepancia de la spec, para el líder.** `tasks.md` pide en T20
> «Verificación: T19 en verde», y eso **no es alcanzable** en T20: las filas de
> guion de la columna del ERP solo pueden estar en verde cuando
> `a_codigo_de_sigrid` componga por tramos. La propia T22 lo delata al pedir
> «T19 **entero** en verde». **El bloque 7 no admite un corte entre T20 y T22.**

### 94.3 · Y por qué no lo he arreglado igualmente

Porque el encargo lo prohíbe con todas las letras («No entres en T21 ni en
T22») y porque tocar `cierre.py` sería hacer T22 por mi cuenta. Tampoco he
marcado la feature `blocked`: el encargo prohíbe expresamente tocar el `status`
de ninguna feature.

Así que paro, lo dejo escrito y **lo levanto**: T22 es una línea, ya está
especificada y **deja los 24 en verde de una vez**. Mi recomendación es
autorizarla —junto con T21— en el encargo siguiente, sin intercalar nada. Si se
prefiere que la rama vuelva a estar verde ahora mismo, la alternativa es
revertir `c12d826` y hacer el bloque 7 entero de una tacada; no recomiendo
dejar la rama en este estado más de lo necesario.

---

## 95 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (servicio `api`) | **2.562 pasados, 25 fallos, 13 saltados** | `pytest -q` en `services/postventa-api` |
| De ellos, **nuevos del bloque 7** | **59**, todos en `tests/test_f028_espacios_codigos.py` · **49 en verde, 10 pendientes de T22** | la propia suite |
| Tests ejecutados (servicio `front`) | **250 pasados, 0 fallos** | sin cambios: el front está fuera del diff |
| Tests ejecutados (arnés, raíz) | **62 pasados** | `bash harness/init.sh` |
| Tests **retirados** | **ninguno** | — |
| Tests **con la expectativa cambiada** | **ninguno**: el único que cambia es el de T21, y **sigue sin tocar**, en rojo | `git diff 71a5e00 -- services/postventa-api/tests/test_f006_nombrado.py` está vacío |
| **Cobertura de las líneas cambiadas** | **100,0 %** — **295/295**, umbral 80 %, nivel `estandar` | `python -m harness.cobertura`. Eran 283 antes del bloque: las 12 nuevas son las de `nombrado.py`, y están cubiertas |
| **Mutantes automáticos** | **32 / 32 muertos, 0 supervivientes** — y **este número NO VALE**: ver §95.1 | `python -m harness.mutacion --feature F-028` → `progress/mutacion_F-028.md` |
| **Mutantes a mano** | **16 generados · 15 muertos · 1 superviviente**, y el superviviente es **equivalente**, demostrado | §95.2 y §95.3 |
| **Tiempo de la suite** | `api` **21,4 s** · `front` 1,7 s · raíz 2,5 s | la propia suite |
| **Ruff** | `All checks passed` sobre los dos ficheros tocados; el repositorio sigue en **61** avisos, sin crecer | `python -m ruff check` |

### 95.1 · La campaña automática da 32 de 32 y **es exactamente el número que no hay que creerse**

Va en voz alta, como en §54.1 y §65.1, porque presentarla como respaldo sería
mentir con un número verdadero.

`harness.mutacion` juzga a un mutante lanzando la suite: si el proceso sale con
código distinto de 0, lo da por **muerto**. Y la suite **ya sale distinta de
cero sin mutar nada**:

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest -x -q --tb=no -p no:cacheprovider > /dev/null; echo $?
1
```

Con la línea base en rojo, **cualquier** mutante —incluido uno que no cambiara
nada— saldría «muerto». Los 32 de 32 no dicen nada de T20. Lo digo aquí y no en
una nota al pie porque el informe de mutación queda escrito en
`progress/mutacion_F-028.md` con ese titular.

> **Propagación pendiente a `arnes-base`, y no la hago yo.** `harness.mutacion`
> **no comprueba que la línea base esté verde** antes de empezar. Debería
> medirla y negarse —o al menos avisar— en vez de publicar un 100 % que solo
> dice que la suite ya fallaba. Es el tercer hueco del arnés que anota esta
> feature (los dos anteriores, en §76.1 y §86.1, son de medición en dos
> lenguajes). Queda para el líder: el implementer no toca el arnés por su
> cuenta.

### 95.2 · Los 16 mutantes **a mano**, que son la evidencia que sí respalda T20

Misma receta que los bloques 3 a 6, con una diferencia que es el motivo de que
esta campaña valga algo: **la línea base se construye verde a propósito**. Se
mide qué nodos estaban rojos **antes** de mutar nada —no se escriben a mano— y
se deseleccionan; el resto de la suite del servicio `api` se ejecuta entera.

```
LINEA BASE (sin mutar, con los rojos deseleccionados):
   2561 passed, 13 skipped, 26 deselected in 19.82s
```

> Se deseleccionan **26** y los rojos son **25**: el `--deselect` de pytest
> empareja por prefijo de id, y los ids con espacios (`[RS26.08 - 0123]`) se
> cortan por el espacio, así que arrastran también a
> `test_f009_r6_todas_las_formas_del_codigo_acaban_en_la_de_sigrid[RS26.08/0123]`,
> que estaba en verde. No afecta al resultado: ese caso es de
> `a_codigo_de_sigrid`, no de `nombrado.py`, y su hermano
> `[  RS26.08/0123  ]` sigue dentro de la línea base.

«Muerto» = al menos un caso falla. El script restaura el fichero en un
`finally` y el árbol quedó limpio, comprobado con `git status`.

| # | Mutante aplicado a mano | Resultado |
|---|---|---|
| M1 | `SEPARADORES_DE_CODIGO` pierde el guion (`"/-"` → `"/"`) | muerto |
| M2 | `SEPARADORES_DE_CODIGO` pierde la barra (`"/-"` → `"-"`) | muerto |
| M3 | El saneo solo mira **detrás** del separador (`\s*(…)\s*` → `(…)\s*`) | muerto |
| M4 | El saneo solo mira **delante** (`\s*(…)\s*` → `\s*(…)`) | muerto |
| M5 | El saneo quita como mucho **un** espacio por lado (`\s*` → `\s?`) | **SUPERVIVIENTE · equivalente**, ver §95.3 |
| M6 | El saneo se come también el separador (`sub(r"\1")` → `sub("")`) | muerto |
| M7 | El arreglo de R44 se cae entero (vuelta al código de antes) | muerto |
| M8 | El saneo ocurre **antes** de traducir los guiones raros | muerto |
| M9 | `tramos_de_codigo` conserva los tramos vacíos | muerto |
| M10 | `tramos_de_codigo` parte solo por la barra | muerto |
| M11 | `tramos_de_codigo` parte por espacios | muerto |
| M12 | Los tramos se unen **sin** separador | muerto |
| M13 | Los tramos se unen con **barra** (la barra vuelve al nombre) | muerto |
| M14 | El código de **obra** también pasa por los tramos | muerto |
| M15 | Se quita la guardia de R49 (código de solo separadores) | muerto |
| M16 | La guardia de R49 invertida — es el **único** mutante que el arnés sí genera de este fichero (`nombrado.py:237`) | muerto |

M3, M4 y M5 están escritos aparte **a propósito**: son los tres arreglos a
medias que un saneo apresurado produce, y cada uno deja viva una fila distinta
de la tabla.

### 95.3 · El superviviente M5, y por qué es **equivalente** y no un hueco

M5 cambia `\s*` por `\s?` y **ningún test se entera**. No es un test flojo: es
que los dos programas son el mismo.

La sustitución se aplica sobre `colapsado`, que ya ha pasado por
`" ".join(bruto.split())`. Ahí dentro **no queda ninguna racha de espacios**:
todo blanco es exactamente un espacio. Así que `\s*` nunca puede casar más de
uno, y `\s?` hace lo mismo.

No me lo creo por el razonamiento; se comprueba a lo bruto, con las **55.987**
cadenas de hasta 6 caracteres sobre el alfabeto «espacio, tabulador, salto de
línea, barra, guion, A»:

```
cadenas probadas hasta 6 caracteres sobre « \t\n/-A»
entradas en las que original y mutante difieren: 0
[]

sin el colapso previo, sí se distinguen:
  original: A/A
  mutado  : A / A
```

La segunda mitad es la que cierra el análisis: los dos **sí** se distinguen si
se quita el colapso previo — y quitarlo o moverlo es el mutante **M8**, que
muere. O sea: la propiedad está cubierta, solo que por el test que vigila el
orden y no por uno que cuente espacios.

**Se queda `\s*` y no `\s?`.** Son equivalentes hoy porque el colapso va
delante; `\s*` sigue siendo correcto si mañana ese colapso se moviera, y `\s?`
no. Entre dos formas equivalentes, la que no depende de una precondición puesta
en otra línea.

---

## 96 · Verificaciones MANUAL pendientes

Las de T27 siguen pendientes, y este bloque **deja apuntada una**, que es la que
cierra el asunto 2 de la feature:

- **R45 contra el ERP** (`requirements.md` §10 ya la declara
  `MANUAL (humano)`): pasar un parte cuyo número la IA lea con espacios
  alrededor del separador y comprobar que **la reclamación se localiza** y el
  cierre ocurre. El dominio está probado entero —la tabla de §9.3, fila a
  fila—, pero que el ERP encuentre la reclamación con el código canónico solo lo
  demuestra el ERP.
  **Todavía no se puede ejecutar**: necesita T22.

**La base real y el ERP no se han tocado.** Todo lo de este bloque corre sobre
funciones puras, sin red, sin BBDD y sin IA. La guardia de red de sesión de
`tests/conftest.py` sigue puesta.

---

## 97 · Por dónde sigue · T21 y T22, y **juntas**

1. **T21** · actualizar `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`
   a `normalizar_codigo("RS26.08   -    0123") == "RS26.08-0123"`, con su
   comentario, y escribir el recuadro fechado de R8 en
   `specs/F-006-sharepoint/requirements.md` (R55).
2. **T22** · `a_codigo_de_sigrid` compone por tramos:
   `"/".join(tramos_de_codigo(codigo))`, sin tocar nada más de `cierre.py`.
   `tramos_de_codigo` ya existe y está probada. **Esto deja los 24 rojos de
   §94.1 en verde de una vez.**

Las dos tareas juntas devuelven la rama a verde. Hacerlas por separado deja la
rama rota entre medias otra vez, sin ganar nada: T21 no arregla ningún rojo de
T22 ni al revés.

---

## 98 · Estado al cerrar el encargo

- `bash harness/init.sh` → **EN ROJO**, y es lo que §94 explica: `[KO] servicio
  api: pytest en rojo` y `[KO] PUERTA COBERTURA`. **Ojo con esa segunda línea**:
  dice 58,6 % porque `init.sh` corre la suite con `-x` y la aborta en el primer
  fallo, así que mide media suite. Medida sobre la suite entera, la cobertura de
  las líneas cambiadas es **100,0 % (297/297)**.
- Árbol limpio, **2 commits** sobre `71a5e00` (`98968c8` T19 y `c12d826` T20),
  los dos locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`.
- **No se ha entrado en T21 ni en T22**, como pedía el encargo:
  `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` está sin tocar,
  `specs/F-006-sharepoint/requirements.md` está sin tocar y
  `domain/models/cierre.py` está sin tocar.
- **La rama NO es desplegable** hasta T22. Dicho en §94 y repetido aquí porque
  es lo que más importa de este informe.

---

# F-028 · Estado del parte — informe del implementer · bloque 7, T21 y T22

> **Encargo del 2026-09-16**: T21 y T22, las dos juntas y sin intercalar nada.
> Parar al terminar y no entrar en el bloque 8.
>
> ## ✅ LÉASE ESTO ANTES QUE NADA: **la rama vuelve a estar EN VERDE**
>
> `bash harness/init.sh` → **ENTORNO LISTO**. **2.593 pasados, 13 saltados, 0
> fallos** en `api`, front en verde (caché, árbol sin cambios) y **PUERTA
> COBERTURA 100,0 % de 297 líneas cambiadas (297/297)**.
>
> Los **25 rojos** que declaraba §94 están los 25 en verde. Y lo que más
> importa de los 25: **los 4 de `tests/test_f028_puertas.py` —la red de
> seguridad del bloque 0— han vuelto a verde SOLOS**, sin que se tocara ni una
> línea de ese fichero. Era la condición que ponía el encargo, y se cumple:
> fallaban por el código convertido (`assert ['XX00.00-0000'] ==
> ['XX00.00/0000']`), no por el control. El control nunca se aflojó.

---

## 99 · Qué se ha hecho, en una frase por tarea

- **T21** (`30cf674`) · `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`
  pasa a esperar `"RS26.08-0123"`; R8 de F-006 recibe su **recuadro fechado**
  con el patrón de R28 de F-010; y `tests/test_f028_documentacion.py` (nuevo)
  **fija ese recuadro con seis casos**, para que la enmienda no se pueda
  perder en la siguiente edición del documento.
- **T22** (`2482607`) · `a_codigo_de_sigrid` compone por tramos:
  `return "/".join(tramos_de_codigo(codigo))`. **Una línea de código** y la
  importación que la acompaña. Con ella vuelven a verde los 24 rojos que T20
  dejó declarados.

---

## 100 · ⚠️ Qué test cambió de expectativa, y por qué

Lo pide `tasks.md` T21 con todas las letras y `design.md` §9.4 lo llama «el
único test existente que cambia de expectativa»: **un test que cambia sin
justificación escrita es un test aflojado**. Así que va primero y con su
nombre.

**El test**: `tests/test_f006_nombrado.py::test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`

**Lo que afirmaba** (literal, hasta `c12d826`):

```python
def test_f006_r8_los_espacios_interiores_se_colapsan_a_uno():
    """R8 · varios espacios seguidos dentro del código pasan a ser uno."""
    assert normalizar_codigo("RS26.08   -    0123") == "RS26.08 - 0123"
```

**Lo que afirma ahora**:

```python
    assert normalizar_codigo("RS26.08   -    0123") == "RS26.08-0123"
    assert normalizar_codigo("RS26.08   0123") == "RS26.08 0123"
```

**Por qué cambia, y por qué esto no es aflojarlo.** R8 pedía —y sigue
pidiendo— que «dos lecturas del mismo parte que solo difieran en espacios
produzcan **el mismo** nombre». Esa garantía **no se cumplía**, y el ejemplo
del propio requisito era el que describía el defecto:

- `RS26.09- 0149` —guion pegado por delante, suelto por detrás— producía un
  nombre de fichero **distinto** del canónico. Dos lecturas del mismo parte,
  dos ficheros;
- y el código que viajaba al ERP conservaba los espacios. Sigrid busca la
  reclamación por **igualdad exacta**, así que el parte se archivaba bien y el
  cierre fallaba en silencio. Es el fallo que abrió el asunto 2.

O sea: **la garantía de R8 no se recorta, se cumple por primera vez**. Lo que
cambia es el **valor intermedio** de `normalizar_codigo`, que este test fija.

**Qué se ha hecho para que el cambio no quede sin respaldo**, que es lo que
distingue esto de un test acomodado al código:

1. **El test conserva su nombre.** Lo citan `design.md` §9.4 y `tasks.md` T21;
   renombrarlo rompería la trazabilidad justo en el punto donde más falta hace.
2. **Su docstring cita la expectativa anterior literal** y remite al recuadro
   de R8. Quien lo lea dentro de seis meses ve qué decía antes y por qué ya no.
3. **Se le añade una segunda aserción.** Con la primera sola, el test dejaría
   de probar ningún colapso: los únicos espacios de `"RS26.08   -    0123"`
   flanquean al guion y ahora desaparecen. `"RS26.08   0123"` → `"RS26.08 0123"`
   conserva lo que R8 sí garantizaba y sigue garantizando. El mutante **N7** de
   §105.2 demuestra que esa aserción no es decorativa.
4. **R8 recibe su recuadro fechado** y su texto original **no se borra**
   (§101), con un test que lo vigila.

**Ningún otro test cambió de expectativa.** Los dos de F-009 sobre la
conversión pasan **sin tocarlos**, y los cuatro de `test_f028_puertas.py`
volvieron a verde solos.

---

## 101 · El recuadro de R8, y el test que lo sostiene (R55)

`specs/F-006-sharepoint/requirements.md` queda con el patrón del proyecto
—R28 de F-010 (2026-09-03), §7 de F-025, H-1 de F-026—: **la premisa original
no se borra**, se cita literal y se dice qué la invalidó, quién lo decidió y
cuándo.

| Pieza del patrón | Qué dice el recuadro |
|---|---|
| Premisa original, **literal** | el texto entero de R8, ejemplo `0677  -  RS26.08` incluido |
| Qué cambia | los espacios que flanquean a un separador **se eliminan**; `RS26.08   -    0123` → `RS26.08-0123` |
| Qué la invalidó | el ERP busca por **igualdad exacta**: el parte se archivaba bien y el cierre fallaba |
| Quién y cuándo | **el responsable del proyecto, el 2026-09-15**, al ver fallar el circuito en real; asunto 2 de F-028 |
| Qué **no** cambia | R4 (ceros), R5 (sufijo), R7 (error ruidoso) y que el código de **obra** no se parte: `06-77` es una obra |

El cuerpo de R8 se reescribe para que **el requisito no mienta** —decía
«colapsar» y ahora el sistema elimina—, y la fila de trazabilidad queda anotada
con «**Premisa enmendada el 2026-09-15**: ver el recuadro bajo R8», exactamente
como hizo F-010 con su R28.

**Y hay un test nuevo que lo vigila**: `tests/test_f028_documentacion.py`, con
el patrón de `test_f026_documentacion.py` (aplanado de Markdown incluido, para
que un reajuste de márgenes no lo ponga en rojo por un motivo falso). Seis
casos: el recuadro existe, está fechado y nombra la feature; cita la premisa
literal; dice el valor nuevo; dice el porqué y el quién; dice que la garantía
no se recorta; y **control negativo** de que el texto original de R8 no se ha
borrado del fichero.

> **Decisión que `tasks.md` no enumera, y que el reviewer debe juzgar.** T21
> pide «el recuadro presente» como verificación, pero no nombra ningún test, y
> el test de documentación que sí enumera la spec es el de **T24** (R56, R57,
> R58). He creado el fichero ahora con **solo los casos de R55**, para que T21
> tenga verificación automática en vez de a ojo; **T24 lo extiende**, no lo
> sustituye. Si el reviewer prefiere que R55 se verifique a ojo y el fichero
> nazca en T24, es retirar seis tests y el fichero.
>
> Un detalle del aplanado, por si alguien lo toca: la cita del ejemplo
> `0677  -  RS26.08` se comprueba contra el texto **sin aplanar**, y es el
> único caso del fichero que lo hace. Aplanar colapsaría esos espacios dobles y
> el test daría por buena una cita que ya no dice lo que decía el requisito —
> justo el error que este fichero existe para cazar—. Va comentado en el sitio.

---

## 102 · Fase RED · las trazas, pegadas

### 102.1 · T21 · el test con la expectativa vieja, contra el código de T20

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f006_nombrado.py::test_f006_r8_los_espacios_interiores_se_colapsan_a_uno -q

    def test_f006_r8_los_espacios_interiores_se_colapsan_a_uno():
        """R8 · varios espacios seguidos dentro del código pasan a ser uno."""
>       assert normalizar_codigo("RS26.08   -    0123") == "RS26.08 - 0123"
E       AssertionError: assert 'RS26.08-0123' == 'RS26.08 - 0123'
E
E         - RS26.08 - 0123
E         ?        - -
E         + RS26.08-0123

tests\test_f006_nombrado.py:435: AssertionError
1 failed in 0.14s
```

### 102.2 · T21 · el test de documentación, **antes** de escribir el recuadro

Escrito primero y ejecutado contra el `requirements.md` sin enmendar
—restaurado a propósito con `git checkout --` para medirlo, y devuelto
después—:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_documentacion.py -q --tb=line
FFFFF.                                                                   [100%]
E   AssertionError: assert 'Enmienda' in '**R8.** El sistema debe colapsar los espacios redundantes de los códigos (`0677 - RS26.08` → ...
E   ValueError: substring not found
E   AssertionError: assert 'se eliminan' in '**R8.** El sistema debe colapsar los espacios redundantes ...
E   AssertionError: assert 'igualdad exacta' in '**R8.** El sistema debe colapsar los espacios redundantes ...
E   AssertionError: assert 'se cumple por primera vez' in '**R8.** El sistema debe colapsar los espacios redundantes ...
5 failed, 1 passed in 0.06s
```

El que pasa es el **control negativo**: el texto original de R8 estaba, claro,
porque todavía no se había tocado nada. Es lo que tenía que hacer.

### 102.3 · T22 · los 24 rojos, y las dos trazas que los explican

Línea base con T21 ya dentro y `cierre.py` **sin tocar**:

```
$ ./.venv/Scripts/python.exe -m pytest tests/ -q --tb=no -p no:randomly
24 failed, 2569 passed, 3 skipped in 21.34s
```

El caso de la tabla de T19 (R45), con su mensaje propio:

```
tests\test_f028_espacios_codigos.py:149: in test_f028_r45_todas_las_formas_dan_el_mismo_codigo_para_el_erp
    assert a_codigo_de_sigrid(entrada) == CODIGO_DE_SIGRID, (
E   AssertionError: la forma «guion normal con espacio a los dos lados» no llega al ERP como la canónica
E   assert 'RS26.09-0149' == 'RS26.09/0149'
E     - RS26.09/0149
E     ?        ^
E     + RS26.09-0149
E     ?        ^
```

Y el de F-009, que es el mismo defecto visto desde la feature que lo sufre:

```
tests\test_f009_dominio_cierre.py:298: in test_f009_r6_el_codigo_del_parte_vuelve_al_formato_con_barra
    assert a_codigo_de_sigrid("RS26.08 - 0123") == "RS26.08/0123"
E   AssertionError: assert 'RS26.08-0123' == 'RS26.08/0123'
```

---

## 103 · T22 · el cambio, y el control negativo que pide la tarea

`domain/models/cierre.py`, **dos trozos y ni uno más**:

```python
-from domain.models.nombrado import SEPARADOR, normalizar_codigo
+from domain.models.nombrado import normalizar_codigo, tramos_de_codigo
...
-    return " ".join(codigo.replace(SEPARADOR, "/").split())
+    return "/".join(tramos_de_codigo(codigo))
```

Más la docstring, que explica por qué y deja escrito lo que la función gana:
un código leído como `RS26.09-0149` —guion pegado, sin espacios— **antes salía
tal cual** y el ERP no encontraba la reclamación; ahora sale `RS26.09/0149`.
Mismo defecto, misma familia, arreglado de paso (`design.md` §9.2 lo anunciaba).

### 103.1 · Control negativo del diff (lo pide T22 con nombre y apellidos)

```
$ git diff | grep -n "TEXTO_LOG_CIERRE\|batch_de_cierre\|escrituras"
NINGUNA de las tres marcas aparece en el diff de T22
```

`git diff -- services/postventa-api/domain/models/cierre.py` son exactamente
los dos *hunks* de arriba. **Lo que se ha arreglado es cómo se compone el
código con el que se BUSCA la reclamación, no lo que se escribe en el ERP.**
`TEXTO_LOG_CIERRE`, `batch_de_cierre` e `infrastructure/sigrid/escrituras.py`
están intactos, y el camino que cerró `RS26.09/0150` y `RS26.09/0149` es el
mismo que antes: lo único que cambia es que ahora también llega ahí el parte
cuyo número se leyó con espacios.

### 103.2 · La red de seguridad volvió a verde sola

Los 4 de `tests/test_f028_puertas.py` que el encargo señalaba pasan **sin que
el fichero se haya tocado** —no aparece en el diff del bloque 7— y sin que se
haya tocado ninguna de las tres puertas. Era la comprobación que pedía el
encargo («si alguno siguiera rojo después, para y dilo»): **ninguno sigue
rojo**.

---

## 104 · Ficheros tocados

### Creados

- `services/postventa-api/tests/test_f028_documentacion.py` — 6 casos, R55.

### Modificados

- `services/postventa-api/tests/test_f006_nombrado.py` — **un** test cambia de
  expectativa (§100), con su docstring y una aserción más.
- `specs/F-006-sharepoint/requirements.md` — R8 reescrito + recuadro fechado +
  fila de trazabilidad anotada. **Ningún texto borrado.**
- `services/postventa-api/domain/models/cierre.py` — la importación y
  `a_codigo_de_sigrid` (§103).
- `specs/F-028-estado-del-parte/tasks.md` — T21 y T22 a `[x]`.
- `progress/impl_F-028.md`, `progress/current.md`, `progress/mutacion_F-028.md`.

### Lo que la spec prohíbe tocar, y sigue intacto

`domain/models/validacion.py`, `sql/04_validaciones.sql`,
`domain/models/aprobacion.py` (`huella_de_veredicto` y `_normalizar`),
`infrastructure/sigrid/` **entero**, `infrastructure/sharepoint/`,
`sql/10_aprobaciones.sql`, `harness/features.json` y `azure-apps/`. Ninguno
aparece en el diff.

---

## 105 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (`api`) | **2.593 pasados, 0 fallos, 13 saltados** | `bash harness/init.sh` |
| **Tests ejecutados** (`front`) | verde, **por caché** (árbol sin cambios) | `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100,0 % (297/297)**, umbral 80 % | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados (automáticos)** | **32 · 32 muertos · 0 supervivientes** | `python -m harness.mutacion --feature F-028` |
| **Mutantes a mano** | **15 · 14 muertos · 1 superviviente equivalente** | §105.2 y §105.3 |
| **Tiempo de la suite** | **31,7 s** dentro de `init.sh`; 22,8 s suelta | la propia suite |

### 105.1 · La campaña automática da 32/32, y esta vez **sí** vale — pero no mide T22

Al revés que en el bloque anterior (§95.1), la línea base estaba **verde**
antes de lanzarla, así que los 32 muertos son muertos de verdad. Lo comprobé
antes de creérmelo:

```
$ ./.venv/Scripts/python.exe -m pytest tests/ -q --tb=no -p no:randomly
2593 passed, 3 skipped in 22.79s
```

**Pero ni uno de los 32 cae sobre la línea de T22.** Es una limitación del
generador, no un descuido: `harness.mutacion` muta operadores aritméticos,
lógicos, comparaciones, `not`, booleanos y enteros, y
`return "/".join(tramos_de_codigo(codigo))` no tiene ninguno. Lo más cerca que
llega del bloque 7 es el mutante **[22]**, sobre `nombrado.py:237`
(`if not tramos:` → `if tramos:`), que es de T20.

**Así que el 32/32 no respalda T22.** Lo que la respalda son los mutantes a
mano de §105.2, y dejarlo claro es la mitad del valor de esta sección.

### 105.2 · Los 15 mutantes a mano

**Ocho sobre `a_codigo_de_sigrid`** (T22), cada uno con la suite entera:

| # | Mutante | Resultado |
|---|---|---|
| M1 | `"/".join(...)` → `"-".join(...)` | **muerto** |
| M2 | `"/".join(...)` → `" / ".join(...)` | **muerto** |
| M3 | `return codigo` (sin partir en tramos: **el bug de antes**) | **muerto** |
| M4 | `normalizar_codigo(bruto)` → `bruto or ""` | **muerto** |
| M5 | partir **solo** por la barra, ignorando el guion | **muerto** |
| M6 | tramos al revés | **muerto** |
| M7 | quedarse con el primer tramo | **muerto** |
| M8 | quitar la guarda `if not codigo: return ""` | **SUPERVIVIENTE** (§105.3) |

**Siete sobre lo de T21**, que no es código ejecutable sino constancia, y por
eso se mutan el recuadro y la normalización que el test fija:

| # | Mutante | Resultado |
|---|---|---|
| N1 | el recuadro pierde la fecha | **muerto** |
| N2 | la cita literal pasa a ser un resumen | **muerto** |
| N3 | la cita pierde los espacios dobles del ejemplo | **muerto** |
| N4 | desaparece «se cumple por primera vez» | **muerto** |
| N5 | desaparece quién lo decidió | **muerto** |
| N6 | desaparece el porqué («igualdad exacta») | **muerto** |
| N7 | el colapso se come **todos** los espacios interiores | **muerto** |

**N3 y N7 son los dos que más me importaban.** N3 demuestra que el test de
documentación no da por buena una cita «casi» literal: si alguien reenvuelve
el párrafo y colapsa `0677  -  RS26.08`, salta. Y **N7 es el que justifica la
segunda aserción de §100**: sin ella, un `normalizar_codigo` que borrara todos
los espacios interiores —no solo los del separador— pasaría el test
inadvertido, y el nombre de un parte con texto interior saldría mutilado.

El árbol se restauró tras cada mutante y la suite quedó comprobada en verde al
final (`2593 passed, 3 skipped`).

### 105.3 · El superviviente M8, y por qué es **equivalente**

`a_codigo_de_sigrid` conserva de F-009 esta guarda:

```python
codigo = normalizar_codigo(bruto)
if not codigo:
    return ""
return "/".join(tramos_de_codigo(codigo))
```

Quitarla no cambia **ningún** resultado, y no es una impresión: con el cambio
de T22, `tramos_de_codigo("")` devuelve la tupla vacía y `"/".join(())` es
`""`, que es exactamente lo que devolvía la guarda. Medido:

```
None     -> ''    | con guarda '' | sin guarda '' | iguales True
''       -> ''    | con guarda '' | sin guarda '' | iguales True
'   '    -> ''    | con guarda '' | sin guarda '' | iguales True
'/'      -> '/'   | con guarda '' | sin guarda '' | iguales True
'///'    -> '///' | con guarda '' | sin guarda '' | iguales True
' - '    -> '-'   | con guarda '' | sin guarda '' | iguales True
'\t\n'   -> ''    | con guarda '' | sin guarda '' | iguales True
'- /-'   -> '-/-' | con guarda '' | sin guarda '' | iguales True
```

**Es un mutante equivalente, no un hueco de test**: ningún test puede
distinguir las dos versiones porque no hay ninguna entrada que las separe.

**No la he quitado**, y la decisión es discutible, así que la dejo a la vista:
la guarda **dice** algo que el `join` no dice —sin código no se convierte
nada— y la tarea manda no tocar de `cierre.py` más de lo necesario. Quitarla
sería un cambio de comportamiento nulo y de intención sí. Si el reviewer
prefiere código sin ramas inalcanzables, es borrar tres líneas y ningún test
se mueve; queda anotado precisamente para que esa decisión se tome mirándola.

> Ojo a la diferencia con el superviviente equivalente del bloque anterior
> (§95.3): aquel lo era **por la naturaleza del dato**; este lo es **porque T22
> lo ha vuelto redundante**. Antes de T22, la guarda sí hacía falta: `" - "`
> normalizado daba `"-"`, y el viejo `replace` habría devuelto `"-"` en vez de
> cadena vacía.

---

## 106 · Verificaciones MANUAL pendientes

No añado ninguna nueva: las de este bloque siguen siendo las que ya estaban
declaradas y **las ejecuta el humano tras desplegar** (`tasks.md` T27).

- **T27.6** — un parte cuyo número se lea con **espacios alrededor de la
  barra** cierra la incidencia en el ERP. **Es la que cierra el asunto 2**, y
  hasta este commit no se podía ni intentar: el código llegaba al ERP con
  guion. Ahora el dominio entero está probado (la tabla de `design.md` §9.3,
  fila a fila, en las dos conversiones), pero **el ERP de producción no lo
  está y no puede estarlo desde aquí**: `CLAUDE.md` prohíbe escribir en Sigrid
  desde local.
- **T27.1 a T27.5** — las del estado, sin cambios respecto a §87.

Recomendación para cuando llegue: hacer **primero el dry-run** de un parte con
el número leído con espacios y comprobar que la reclamación que devuelve es la
que se espera, **antes** de confirmar el cierre. El arreglo hace que se
encuentre una reclamación donde antes no se encontraba ninguna; que sea la
correcta es lo que hay que mirar con los ojos una vez.

---

## 107 · Lo que queda fuera del alcance de T21 y T22

- **El bloque 8 (T23) no se ha tocado**, como pedía el encargo. Es el que
  prueba que **la huella de F-026 no se ha movido**, y es el control que cierra
  el riesgo que la ficha manda tratar. `tests/test_f028_huella_intacta.py` no
  existe todavía.
- **El defecto latente de D9 sigue ahí y sigue sin arreglarse** (`design.md`
  §10): una relectura que solo cambie los espacios alrededor de la barra hace
  que una aprobación humana deje de contar, porque la huella normaliza con otro
  criterio. Está **declarado**, no olvidado, y arreglarlo cambiaría huellas ya
  escritas.
- **T24 (los recuadros de R56, R57 y R58) y T25 (los dos documentos) siguen
  pendientes.** `docs/ARCHITECTURE.md` todavía **no** dice que los espacios
  alrededor del separador no forman parte del código; lo pide T24.
- **`azure-apps/` sin tocar**, como manda el encargo. Es T25.

---

## 108 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**. **2.593 pasados**, 13 saltados,
  **0 fallos**; front en verde por caché; **PUERTA COBERTURA 100,0 % de 297
  líneas cambiadas (297/297)**; rama correcta.
- **La rama vuelve a ser desplegable.** Los 25 rojos de §94 están en verde, y
  los 4 de la red de seguridad volvieron solos.
- Árbol limpio. **2 commits** sobre `2307648`: `30cf674` (T21) y `2482607`
  (T22), los dos **locales**. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`. No he marcado
  `done` nada.
- **No se ha entrado en el bloque 8**, como pedía el encargo.
- Tres cosas con nombre propio para el reviewer: **§100** (qué test cambió de
  expectativa y por qué), **§105.1** (el 32/32 automático **no** mide T22; lo
  que la mide son los 15 mutantes a mano) y **§105.3** (el superviviente M8, y
  por qué no lo he quitado).

---

# F-028 · Estado del parte — informe del implementer · bloques 8 y 9, T23 y T24

> **Encargo del 2026-09-16**: T23 (bloque 8) y T24 (bloque 9), las dos, y
> parar. **No entrar en T25**, que toca dos repositorios.
>
> ## ✅ LO PRIMERO, PORQUE ES LO QUE EL ENCARGO PEDÍA SABER YA
>
> **Los tres controles de T23 pasan. Ninguna decisión humana vigente se ha
> invalidado.** No había que parar.
>
> Las **siete huellas** medidas en el árbol anterior al bloque 7 y en el de
> ahora son **idénticas**, carácter a carácter. El módulo de la huella **no
> importa** `nombrado` ni usa ninguna pieza del bloque 7. Y un parte aprobado
> por una persona —incluido el que tiene el número leído con espacios
> alrededor de la barra, que es el caso exacto del riesgo— **sigue
> `aprobado`**.
>
> `bash harness/init.sh` → **ENTORNO LISTO**. **2.650 pasados**, 13 saltados,
> **0 fallos**; front en verde (caché); **PUERTA COBERTURA 100,0 % de 297
> líneas cambiadas (297/297)**.

---

## 109 · Qué se ha hecho, en una frase por tarea

- **T23** (`6256762`) · `tests/test_f028_huella_intacta.py`, **15 casos**: los
  tres controles negativos de `design.md` §10 —el valor, el acoplamiento y el
  efecto—, con las siete huellas esperadas **escritas literales** y medidas en
  el árbol anterior al bloque 7. **Ni una línea de código de producción.**
- **T24** (`0417104`) · **siete recuadros fechados**: R12, R17 y R22 de F-026
  **enmendados** (R56); R30 y R31 **precisados, no derogados** (R57); R36 de
  F-025 con un **segundo** recuadro debajo del de F-026 (R58); y los tres
  puntos de `docs/ARCHITECTURE.md` que F-026 precisó, más la **semántica 5**,
  al día (R58). **42 casos nuevos** en `tests/test_f028_documentacion.py`, ocho
  de ellos control negativo. **Ningún texto original borrado.**

---

## 110 · ⚠️ T23 · el control que la ficha exigía. Los tres pasan

El encargo lo decía con todas las letras: si alguno fallaba, **parar**, porque
significaría que el arreglo de los espacios está revocando decisiones que
tomaron personas. No hay que parar. Esto es lo que se ha medido, control a
control.

### 110.1 · Control del **valor** (R50) · las siete huellas no se han movido

Siete veredictos, cuatro de ellos con el número o la obra escritos con
espacios alrededor del separador —que son justo los que el bloque 7 toca—.
Las huellas esperadas van **escritas literales** en el test, en hexadecimal.
No se calculan con la función que se está probando: eso sería comparar una
huella consigo misma, y pasaría verde aunque el arreglo hubiera cambiado las
huellas de todo el sistema.

| Caso | Huella (medida antes y después del bloque 7) |
|---|---|
| apto con el número canónico | `e5ba9b9d…a70d20` |
| apto con espacios a los dos lados de la barra | `930f188a…2d930b7` |
| apto con guion y espacios (la forma del asunto 2) | `50cb4591…77aaa3d5` |
| apto con el código de obra escrito `06 - 77` | `716b481c…ee2792c00` |
| en cola por observaciones manuscritas | `e7157161…fa9a00bfef3` |
| revisión manual, número con espacio delante | `5d6f33cd…5584ea8580` |
| revisión manual, número canónico | `b69ff1d8…2cf85a5fe148` |

### 110.2 · Control del **acoplamiento** (R51) · dos funciones, dos módulos

`domain/models/aprobacion.py` importa exactamente tres cosas —`__future__`,
`hashlib` y `domain.models.validacion`— y ninguna es el nombrado. Se comprueba
sobre el **árbol sintáctico** y no sobre el texto, y no es remilgo: el módulo
menciona la palabra «nombrado» en prosa, dentro de la enmienda de H-1, así que
un `"nombrado" not in fuente` se pondría rojo por una cita. Hay además un
segundo control por el otro lado —ni `normalizar_codigo`, ni
`tramos_de_codigo`, ni `SEPARADORES_DE_CODIGO` aparecen en el fuente—, que
caza el `from domain.models import nombrado` que el control de importaciones
dejaría pasar.

Y queda escrito **en qué se separan**, que es lo que pide R51:

```
normalizar_codigo("RS26.09 / 0149")  ->  "RS26.09/0149"
_normalizar("RS26.09 / 0149")        ->  "rs26.09 / 0149"
```

Una prepara un código para **identificar algo fuera** (un fichero en
SharePoint, una reclamación que el ERP busca por igualdad exacta); la otra
prepara un texto para **comparar dos lecturas del mismo papel**. La segunda es
deliberadamente tonta, porque lo que no puede hacer es cambiar de valor cuando
se toque el nombrado.

### 110.3 · Control del **efecto** (R50) · la decisión de la persona sigue en pie

Tres casos, y el tercero es el del riesgo:

1. un parte que la máquina dejó en la cola, aprobado por una persona con la
   huella guardada **antes** del arreglo, sigue `aprobado`;
2. `decision_en_firme` sigue devolviendo esa decisión, o sea que la pantalla
   sigue diciendo **«aprobado por una persona»** y no «lo dio por bueno la
   máquina» (R43). Sin este caso, un parte apto habría podido quedarse
   `aprobado` **por la máquina** y nadie habría notado que la marca de autoría
   se perdió;
3. **el parte cuyo número se leyó `RS26.09 /0149`** —el del asunto 2— aprobado
   a mano, sigue `aprobado`. Si la huella hubiera seguido a
   `normalizar_codigo`, esta sería la primera aprobación en caerse.

---

## 111 · De dónde salen los siete literales · la medición, con las dos trazas

Esto es lo que separa un control de verdad de una foto: los literales **no
salen del código de hoy**. Se midieron en el árbol **anterior al bloque 7**
—`git worktree` sobre `71a5e00`, el último commit antes de T19— y se
compararon con el de ahora.

```
$ git worktree add <scratch>/antes-bloque7 71a5e00
$ PYTHONPATH=<scratch>/antes-bloque7/services/postventa-api \
    ./.venv/Scripts/python.exe <scratch>/medir_huellas.py
apto_canonico: e5ba9b9dab22705ffa67a48af2670559ac629be72f67ec72f4b645a995a70d20
apto_barra_con_espacios: 930f188aa51e7819c247081b235b1e8adb13683cee312fdef24dc1bbd2d930b7
apto_guion_con_espacios: 50cb4591a881d84f1f4dba35fc318623d311f58e2b1eb75101a2bfb177aaa3d5
apto_obra_con_guion_espaciado: 716b481ce240827bb7ce20b6c144e50e3243dad73b68cdd2babb0fdee2792c00
cola_observaciones: e7157161e90fdf660f2724373e499bf441f421e7b99af0b779c42fa9a00bfef3
revision_manual_dos_motivos: 5d6f33cd1e38795a69674d8e2294a3db60daf538116ffd015544cd5584ea8580
revision_manual_numero_canonico: b69ff1d8d47a03f3ac1ee6567f9d0d83c25f32135d23266b2ce82cf85a5fe148

$ PYTHONPATH=services/postventa-api ./.venv/Scripts/python.exe <scratch>/medir_huellas.py
apto_canonico: e5ba9b9dab22705ffa67a48af2670559ac629be72f67ec72f4b645a995a70d20
apto_barra_con_espacios: 930f188aa51e7819c247081b235b1e8adb13683cee312fdef24dc1bbd2d930b7
apto_guion_con_espacios: 50cb4591a881d84f1f4dba35fc318623d311f58e2b1eb75101a2bfb177aaa3d5
apto_obra_con_guion_espaciado: 716b481ce240827bb7ce20b6c144e50e3243dad73b68cdd2babb0fdee2792c00
cola_observaciones: e7157161e90fdf660f2724373e499bf441f421e7b99af0b779c42fa9a00bfef3
revision_manual_dos_motivos: 5d6f33cd1e38795a69674d8e2294a3db60daf538116ffd015544cd5584ea8580
revision_manual_numero_canonico: b69ff1d8d47a03f3ac1ee6567f9d0d83c25f32135d23266b2ce82cf85a5fe148
```

**Las siete, idénticas.** El worktree se retiró al terminar; el script de
medición vivió en el scratchpad y **no se ha versionado**.

### 111.1 · Y un segundo camino, que no depende de ninguna medición

Un literal medido sigue siendo una foto: si el código ya hubiera estado mal
antes del bloque 7, la foto lo consagraría. Por eso hay un caso más
—`test_f028_r50_la_huella_canonica_se_recalcula_a_mano`— que **reconstruye la
cadena canónica a mano** con `hashlib` y sale el mismo hexadecimal:

```
$ python -c "import hashlib; ..."
canonica a mano -> e5ba9b9dab22705ffa67a48af2670559ac629be72f67ec72f4b645a995a70d20
con espacios    -> 930f188aa51e7819c247081b235b1e8adb13683cee312fdef24dc1bbd2d930b7
```

Fija además **el formato**: los seis campos, en su orden, separados por saltos
de línea y en minúsculas. Si mañana alguien añade un campo o cambia el orden,
el test lo dice con palabras en vez de enseñar solo un hexadecimal distinto.

> **Decisión que el reviewer debe juzgar**: este caso **duplica** a propósito
> el algoritmo de `huella_de_veredicto` dentro del test. Es una segunda
> opinión, y una segunda opinión que reutiliza las constantes de la primera no
> lo es —por eso el separador se escribe en el test y no se importa de
> `aprobacion.py`—. El precio es que un cambio legítimo del formato pondrá
> **dos** tests en rojo en vez de uno. Me parece el precio correcto; si el
> reviewer no lo ve así, es borrar un test y no se mueve nada más.

---

## 112 · Fase RED · las trazas, pegadas

### 112.1 · T23 · un control negativo **no tiene** fase RED natural, y esto es lo que hay en su lugar

Los tres controles de T23 pasan desde el primer momento: ese es justo su
resultado esperado. Escribirlos «en rojo» primero habría exigido romper a
propósito el código de producción, y lo que mide un control negativo no es que
el código haga algo, sino que **no** ha dejado de hacerlo.

Lo que sí se puede —y se ha hecho— es demostrar que **el test es capaz de
fallar**, y que falla exactamente por el motivo para el que existe. El mutante
es **la unificación de buena fe**: que alguien vea dos normalizaciones que
«hacen lo mismo» y las junte.

```
$ # mutante: _normalizar pasa a delegar en normalizar_codigo
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_huella_intacta.py -q -p no:randomly --tb=line

E   AssertionError: la huella de «apto con espacios a los dos lados de la barra» ha cambiado: hay aprobaciones humanas vigentes que dejan de contar
    assert 'e5ba9b9dab22...645a995a70d20' == '930f188aa51e...dc1bbd2d930b7'
E   AssertionError: la huella de «apto con guion y espacios, la forma que abrió el asunto 2» ha cambiado: hay aprobaciones humanas vigentes que dejan de contar
E   AssertionError: la huella de «apto con el código de obra escrito «06 - 77»» ha cambiado: hay aprobaciones humanas vigentes que dejan de contar
E   AssertionError: assert 'normalizar_codigo' not in '# services/...o).lower()\n'
E   AssertionError: assert 'rs26.09/0149' == 'rs26.09 / 0149'
E   AssertionError: assert <EstadoParte.PENDIENTE: 'pendiente'> is <EstadoParte.APROBADO: 'aprobado'>
9 failed, 6 passed in 0.10s
```

Léase la penúltima línea despacio, porque es el daño entero en un `assert`:
**el parte que una persona aprobó vuelve a `pendiente`**. Eso es lo que este
fichero existe para que no ocurra en silencio. El árbol se restauró con
`git checkout --` y la suite quedó comprobada en verde.

### 112.2 · T24 · los tests **antes** de escribir un solo recuadro

Escritos primero y ejecutados contra los tres documentos sin enmendar
—restaurados a propósito con `git checkout 6256762 --` para medirlo, y
devueltos después—:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_documentacion.py -q -p no:randomly --tb=line
......FFFFFFFFFFFFFFF...FFFFFFFF..FFF..FFF...FF.                         [100%]
E   AssertionError: assert 'Enmienda' in '**R12.** La aprobación debe guardarse en una **tabla propia** del esquema propio del proyecto...'
E   AssertionError: assert 'Enmienda' in '**R17.** El sistema debe dejar **una sola fila por parte**: volver a aprobar el mismo parte...'
E   AssertionError: assert 'Enmienda' in '**R22.** CUANDO el sistema devuelve el resultado de guardar un parte, debe decir...'
E   ValueError: substring not found
E   AssertionError: assert 'ON CONFLICT DO UPDATE' in '**R12.** La aprobación debe guardarse en una **tabla propia**...'
31 failed, 17 passed in 0.14s
```

**Los 17 que pasan son los control-negativo**, y tenían que pasar: comprueban
que el texto original de R12, R17, R22, R30, R31, R36 y de los tres puntos de
`ARCHITECTURE.md` **no se ha borrado**, y en ese momento nadie lo había
tocado. Que nacieran en verde es la prueba de que miden lo que dicen medir.

---

## 113 · T24 · los siete recuadros, y qué dice cada uno

**Ningún texto original se ha borrado.** Es el patrón del proyecto —R28 de
F-010 (2026-09-03), §7 de F-025, H-1 de F-026 y el R8 de F-006 de anteayer— y
la razón por la que existe: un requisito derogado que desaparece deja a quien
lo lee sin saber que hubo una decisión.

| Dónde | Qué dice el recuadro |
|---|---|
| **R12** de F-026 (R56) | La decisión se muda al histórico append-only. Qué la invalidó: `hash_parte` como **clave primaria** obliga al `ON CONFLICT DO UPDATE` que borra la decisión anterior (**§0.4**), y con eso «el histórico conserva las decisiones en orden» es **imposible**, no difícil. Lo que no cambia: sigue siendo tabla propia, con su clave ajena, y la decisión se registra **al lado del veredicto, nunca encima** (R11). Y `postventa.aprobaciones` **no se borra**: se congela y se siembra |
| **R17** de F-026 (R56) | Ya no hay una fila por parte: hay **una fila por decisión**. Qué la invalidó: sustituir **borra el rechazo anterior**, y un ciclo aprobar → rechazar → aprobar no dejaba rastro. Lo que no cambia: sigue habiendo **una sola respuesta** al estado; lo que se acumula son los hechos, no los criterios (R26 de F-028) |
| **R22** de F-026 (R56) | Lo que se devuelve al guardar ya no son dos banderas: es **el estado**. Qué la invalidó: «aprobado / vigente» no sabe decir `rechazado` —del que no se sale reprocesando— ni `cerrado`, y obligaría a la pantalla a reconstruir el estado por su cuenta, que es la segunda copia del criterio que R17 de F-028 prohíbe. Lo que no cambia: viaja **en la respuesta de guardar**, sin una petición más |
| **R30** de F-026 (R57) | **No se deroga: se precisa.** La aprobación **sigue** dejando de valer cuando cambia el veredicto; lo que cambia es que se resuelve al **derivar**, comparando huellas, y no con una escritura que marca la fila. Y cierra un hueco: revocar era una **segunda** escritura, y entre las dos había una **ventana** en la que el parte se quedaba aprobado sobre un veredicto que ya no existía |
| **R31** de F-026 (R57) | **No se deroga: se precisa.** Ya no existe «revocada» como dato: una aprobación tomada sobre otro veredicto **no cuenta** al derivar, y la consecuencia es la misma. Declara la diferencia que sí importa: si el veredicto vuelve a ser el que se aprobó, la aprobación **vuelve a contar**. Y lo que no cambia: el `rechazado` humano **no caduca jamás** |
| **R36** de F-025 (R58) | Segundo recuadro, **debajo** del de F-026 y sin tocarlo. **«Solo se archiva, se adjunta y se cierra lo que está `aprobado`.»** Qué lo invalidó: con F-026 la única operación era aprobar lo rechazado; F-028 añade la contraria, y entonces «apto» deja de bastar —un parte **apto y `rechazado` no se archiva**—. La puerta es **más estrecha**, no más ancha, y se sigue comprobando en **los tres pasos del backend**, leyendo **del repositorio y nunca del cuerpo** |
| **Tres puntos** de `ARCHITECTURE.md` (R58) | Paso 6 del pipeline, semántica 3 y semántica 7, cada uno con su **«Precisado por F-028 el 2026-09-16»** debajo del de F-026, que sigue entero. Los tres nombran `postventa.historico_estado`, dicen que `postventa.aprobaciones` se congela y se siembra, y los tres declaran el caso nuevo: el parte **apto** que una persona dejó `rechazado` |
| **Semántica 5** de `ARCHITECTURE.md` (R58) | **Los espacios que rodean al separador no forman parte del código.** Las cinco formas con espacio son **el mismo** número que `RS26.09/0149`; al ERP viaja siempre con barra y al fichero con ` - `. Con el porqué —Sigrid busca por **igualdad exacta**, así que el parte se archivaba bien y el cierre fallaba **en silencio**— y con el aviso que impide arreglar de más: **`06-77` es una obra**, no dos tramos |

### 113.1 · Los tests de F-025 y de F-026 **no se han tocado, y siguen en verde**

Era el riesgo real de esta tarea: `test_f026_documentacion.py` fija el
contenido de esos mismos bloques —«salvo aprobación humana registrada»,
«motivo aprobable», «no se escribe en Sigrid»— y `test_f025_documentacion.py`
hace lo propio con R36. Todo lo de T24 es **aditivo**: ni una línea borrada, ni
una reescrita.

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f028_documentacion.py \
    tests/test_f026_documentacion.py tests/test_f025_documentacion.py -q -p no:randomly
90 passed in 0.23s
```

El aviso del encargo sobre `docs/INTEGRACION.md` y su test (R26 de F-010) se
ha respetado por la vía más simple: **T24 no lo toca**. Es T25.

---

## 114 · Ficheros tocados

### Creados

- `services/postventa-api/tests/test_f028_huella_intacta.py` — 15 casos, T23.

### Modificados

- `services/postventa-api/tests/test_f028_documentacion.py` — **+42 casos**
  (R56, R57, R58). El `_bloque_r8` de T21 se generalizó a
  `_bloque(fichero, abre, cierra)`; los seis casos de R55 no cambian de
  expectativa ni de nombre.
- `specs/F-026-aprobacion-humana/requirements.md` — cinco recuadros. **Nada
  borrado.**
- `specs/F-025-confirmacion-unica/requirements.md` — un recuadro, debajo del de
  F-026. **Nada borrado.**
- `docs/ARCHITECTURE.md` — cuatro precisiones. **Nada borrado.**
- `specs/F-028-estado-del-parte/tasks.md` — T23 y T24 a `[x]`.
- `progress/impl_F-028.md`, `progress/current.md`, `progress/mutacion_F-028.md`.

### Lo que el encargo prohíbe tocar, y sigue intacto

`azure-apps/` (es T25), `docs/INTEGRACION.md` (es T25),
`infrastructure/sigrid/`, `infrastructure/sharepoint/`,
`harness/features.json` —F-028 sigue `in_progress`, no he marcado `done`
nada—, `domain/models/aprobacion.py` (`huella_de_veredicto` y `_normalizar`,
regla dura 2), `domain/models/validacion.py`, `sql/04_validaciones.sql` y
`sql/10_aprobaciones.sql`. **Ninguno aparece en el diff.**

**Y algo que conviene decir en voz alta**: T23 y T24 **no añaden ni una línea
de código de producción**. El diff de estos dos commits es tests y documentos.

---

## 115 · Evidencias

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** (`api`) | **2.650 pasados, 0 fallos, 13 saltados** | `bash harness/init.sh` |
| **Tests nuevos** | **57** · 15 de T23 + 42 de T24 | 2.593 → 2.608 → 2.650 |
| **Tests ejecutados** (`front`) | verde, **por caché** (árbol sin cambios) | `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100,0 % (297/297)**, umbral 80 % | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados (automáticos)** | **32 · 32 muertos · 0 supervivientes** en 151,8 s | `python -m harness.mutacion --feature F-028` |
| **Mutantes a mano** | **13 · 13 muertos · 0 supervivientes** | §115.2 |
| **Tiempo de la suite** | **31,7 s** dentro de `init.sh`; 22,2 s suelta | la propia suite |

### 115.1 · El 32/32 automático es verdad, y **no mide nada de este encargo**

La línea base estaba verde antes de lanzarla, así que los 32 muertos son
muertos de verdad. Pero `harness.mutacion` muta **operadores de código de
producción**, y T23 y T24 no añaden código de producción: añaden **controles**
y **constancia**. Ni uno de los 32 cae sobre nada de lo que se ha escrito hoy.

Decirlo es la mitad del valor de esta sección: un «32/32, sin supervivientes»
sin esta línea se lee como si el trabajo de hoy estuviera medido, y no lo
está por ahí.

### 115.2 · Los 13 mutantes a mano, que son los que sí lo miden

Cada uno se aplicó, se ejecutó el fichero que debería cazarlo y se restauró el
árbol con `git checkout --`.

**Seis sobre lo que vigila T23**:

| # | Mutante | Resultado |
|---|---|---|
| M1 | `_normalizar` delega en `normalizar_codigo` (**la unificación temida**) | **muerto** · 9 rojos |
| M2 | la cadena canónica cambia el orden de obra y número | **muerto** · 11 rojos |
| M3 | `_normalizar` deja de bajar a minúsculas | **muerto** · 12 rojos |
| M4 | `aprobacion.py` importa `nombrado` **sin llegar a usarlo** | **muerto** · 1 rojo |
| M5 | un campo más en la canónica (el `hash_parte`) | **muerto** · 11 rojos |
| M6 | una aprobación humana cuenta siempre, mire o no la huella | **muerto** · 1 rojo |

**M4 y M6 son los dos que más me importaban.** M4 no cambia **ningún**
resultado —el import no se usa— y aun así muere: es el control del
acoplamiento haciendo su trabajo, que es impedir la dependencia **antes** de
que haga daño. Y M6 lo mata **solo** el test del defecto latente D9, lo que
demuestra que ese caso no es decorativo: es el que vigila que la caducidad de
una aprobación siga existiendo.

**Siete sobre lo que vigila T24**, que no es código sino constancia:

| # | Mutante | Resultado |
|---|---|---|
| N1 | el recuadro de R12 pierde la fecha | **muerto** |
| N2 | la cita de R17 pasa a ser un resumen | **muerto** |
| N3 | el recuadro de R30 **deroga** en vez de precisar | **muerto** |
| N4 | el recuadro de R31 se calla que la aprobación puede revivir | **muerto** |
| N5 | alguien «limpia» `ARCHITECTURE.md` y borra la precisión de F-026 | **muerto** |
| N6 | la semántica 5 pierde el aviso del código de obra | **muerto** |
| N7 | el recuadro de F-026 en R36 de F-025 se degrada a «nota vieja» | **muerto** |

**N2, N3 y N5 son los que justifican que esto sea un test.** N2 demuestra que
una cita «casi» literal no cuela; N3, que degradar una precisión a derogación
—que es exactamente el error que R57 quiere impedir— salta; y N5, que el
control negativo caza el impulso de dejar el documento «limpio» borrando la
capa anterior.

**13 de 13 muertos, ningún superviviente.** Es la primera campaña de esta
feature sin ninguno.

---

## 116 · Verificaciones MANUAL pendientes

No añado ninguna nueva. Las de esta feature siguen siendo las de `tasks.md`
T27, y **las ejecuta el humano tras desplegar**. Dos con relación directa con
lo de hoy:

- **T27.2** — la aprobación que ya había en `postventa.aprobaciones` aparece
  sembrada y el parte **sigue saliendo `aprobado`**. T23 prueba en el dominio
  que la huella no se movió; lo que no puede probar desde aquí es que la
  **semilla** haya metido bien esa fila en el histórico, porque eso necesita la
  base real. **Son dos cosas distintas y las dos hacen falta.**
- **T27.6** — el parte cuyo número se lea con espacios alrededor de la barra
  cierra la incidencia en el ERP. Sigue siendo la que cierra el asunto 2, y
  sigue sin poder intentarse desde local (`CLAUDE.md` prohíbe escribir en
  Sigrid).

---

## 117 · Lo que queda fuera del alcance de T23 y T24

- **T25 no se ha tocado**, como pedía el encargo: ni `docs/INTEGRACION.md` ni
  `azure-apps/postventa_incidencias.md`. Son dos repositorios y van en su
  propio encargo. Ojo al aviso del líder cuando llegue: `INTEGRACION.md` tiene
  un test que exige frases concretas (R26 de F-010,
  `tests/test_f010_integracion_expuesto.py`).
- **El defecto latente de D9 sigue ahí y sigue sin arreglarse**, ahora con su
  test: una relectura que solo cambie los espacios alrededor de la barra hace
  que una aprobación humana deje de contar. Arreglarlo es alinear las dos
  normalizaciones, y eso **cambiaría las huellas ya escritas** en
  `postventa.aprobaciones`, con F-026 desplegada y decisiones reales dentro. El
  humano decidió el 2026-09-15 no alinearlas aquí. El test
  `test_f028_d9_el_defecto_latente_sigue_ahi_y_se_declara` **no bendice el
  defecto**: lo fija para que quien vaya a arreglarlo se tropiece con el porqué
  y traiga un plan para las huellas que ya están escritas.
- **T26 (la campaña de mutación de cierre) y T28 (el `init.sh` final)** siguen
  siendo tareas del bloque 10, aunque la campaña se haya lanzado hoy: lo de hoy
  es la evidencia de este encargo, no el cierre de la feature.

---

## 118 · Estado al cerrar el encargo

- `bash harness/init.sh` → **ENTORNO LISTO**. **2.650 pasados**, 13 saltados,
  **0 fallos**; front en verde por caché; **PUERTA COBERTURA 100,0 % de 297
  líneas cambiadas (297/297)**; rama correcta.
- **Los tres controles de T23 pasan. No hay que parar**: el arreglo de los
  espacios no ha invalidado ninguna decisión humana vigente.
- Árbol limpio. **2 commits** sobre `133728b`: `6256762` (T23) y `0417104`
  (T24), los dos **locales**. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`. No he marcado
  `done` nada.
- **No se ha entrado en T25**, como pedía el encargo.
- Tres cosas con nombre propio para el reviewer: **§111.1** (el test que
  recalcula la huella a mano duplica el algoritmo **a propósito**; es una
  decisión, no un descuido), **§115.1** (el 32/32 automático **no** mide nada
  de este encargo; lo miden los 13 mutantes a mano de §115.2) y **§117** (el
  defecto latente D9, ahora con test, sigue sin arreglar **por decisión del
  humano**).
