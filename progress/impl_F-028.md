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
