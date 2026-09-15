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
| **Cobertura de las líneas cambiadas** | **100,0 %** — 158/158, umbral 80 %, nivel `estandar` |
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
  cobertura al **100,0 %** de las 158 líneas cambiadas.
- Árbol limpio, **2 commits** sobre `2393fa2` (`4130495`, `51fbe77`), todos
  locales. **Sin `push`.**
- `harness/features.json` sin tocar: F-028 sigue `in_progress`, y marcarla
  `done` no es cosa del implementer.
- **La base real y el ERP no se han tocado**: todo corre con
  `RepositorioEnMemoria`, `RepositorioFalso`, `ErpEnMemoria` y
  `ArchivoPortFalso`, sin red, sin BBDD y sin IA.
