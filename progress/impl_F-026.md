<!-- progress/impl_F-026.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Implementación

> Informe **acumulativo** de la feature. Lo empieza el implementer del
> **bloque 2** (2026-09-12), que además **recoge lo que hicieron los bloques 0
> y 1** leyendo sus commits: los agentes que los escribieron se interrumpieron
> antes de redactar este fichero. Lo que aquí se atribuye a ellos sale del
> código y del mensaje de su commit, y va marcado como tal.
>
> Rama: `feature/F-026-aprobacion-humana`. Rigor: **`estandar`**
> (`harness/features.json`) → fase RED y cobertura obligatorias, mutación con
> supervivientes documentados.

---

## 0 · Estado de la feature al cerrar esta tanda

| Bloque | Tareas | Estado |
|---|---|---|
| 0 · Control negativo de las tres puertas | T1 | **hecho** (commit `1361416`) |
| 1 · El dominio | T2–T5 | **hecho** (`1b30a7c`, `6ccf09a`) |
| 2 · La persistencia | T6–T8 | **hecho en esta tanda** (`f1e5718`, `1ece459`, `4d80aaa`, `fc5a37a`) |
| 3 · Las puertas y el borde HTTP | T9–T12 | **sin empezar** |
| 4 · La pantalla | T13–T16 | **sin empezar** |
| 4 bis · Autoguardado | TA1–TA5 | **sin empezar** |
| 5 · Enmiendas y documentación | T17–T19 | **sin empezar** |
| 6 · Verificación contra la base real | T20–T23 | **MANUAL (humano)**, pendiente |
| 7 · Cierre | T24–T25 | T25 en verde hoy; T24 se repite al cerrar |

**La feature NO está terminada y no se puede cerrar.** Nada de lo escrito
hasta aquí cambia el comportamiento del servicio: la tabla existe y el
repositorio sabe escribirla y leerla, pero **todavía no hay nadie que llame a
esas operaciones** — el endpoint `POST /api/aprobar` (T9) y las tres puertas
que leen la aprobación (T11) son el bloque 3. Un parte no apto sigue sin
archivarse, sin adjuntarse y sin cerrarse, exactamente como antes, y eso lo
vigilan los trece casos de control negativo de T1.

La única pieza que **sí** está viva desde hoy es la revocación: cada guardado
de una validación ejecuta el `UPDATE` de revocación. Contra la base de
desarrollo, mientras la tabla esté vacía, ese `UPDATE` no toca ninguna fila.

---

## 1 · El punto de partida: el arnés estaba en **rojo**, y por lo que tocaba

Al arrancar esta sesión, `bash harness/init.sh` fallaba por dos cosas:

```
FAILED tests/test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden
[KO] servicio api (services/postventa-api): pytest en rojo
[KO] PUERTA COBERTURA: 47.6% de 1131 líneas cambiadas cubiertas (538/1131, umbral 80%, nivel estandar)
```

No es un rojo ajeno: es **exactamente el encargo**. El commit `f1e5718` dejó
`10_aprobaciones.sql` escrito pero sin declarar en la lista que lo vigila, y
el dominio del bloque 1 estaba sin ejercitar por la persistencia que faltaba.
Se anota aquí porque el protocolo manda no trabajar sobre un entorno en rojo:
se trabajó sobre él **a sabiendas**, porque apagarlo era la primera tarea.

---

## 2 · Lo que hicieron los bloques 0 y 1 (recogido de sus commits)

### T1 · `1361416` — el control negativo, antes de abrir nada

`services/postventa-api/tests/test_f026_puertas.py`, **300 líneas, 13 casos**.
Fija lo que hoy es imposible y tiene que seguir siéndolo cuando F-026 esté
entera: un parte no apto **sin aprobación** no archiva, no adjunta y no
cierra (R25), para los **dos** destinos no aptos; y la aprobación **no entra
por el cuerpo** de la petición (R24), ni por la firma de los tres pasos ni por
los handlers.

El detalle que lo hace valer: los partes del control negativo son los que el
bloque 3 hará **aprobables** —observaciones manuscritas y firma no humana—,
con un test que lo vigila. Un control negativo sobre un parte que nunca será
aprobable no vigila nada.

### T2–T4 · `1b30a7c` — el dominio, que es donde se decide

`services/postventa-api/domain/models/aprobacion.py`, **285 líneas de dominio
puro** (ni red, ni SQL, ni `psycopg`), con `tests/test_f026_aprobacion_dominio.py`
(457 líneas). Lo que declara:

- `MOTIVOS_APROBABLES` — se aprueba **por motivo y no por destino** (R6–R9):
  observaciones manuscritas y firma no humana sí; código de obra y nº de
  incidencia ilegibles **no**, porque ahí no hay nada que decidir, hay algo que
  teclear.
- `huella_de_veredicto` — `sha256` de destino + códigos ordenados +
  clasificación de firma + observaciones normalizadas. **No lleva dentro ni una
  letra del texto manuscrito** (R15), y normaliza espacios y mayúsculas para
  que una relectura del mismo papel no revoque el juicio de una persona.
- `Aprobacion`, `esta_vigente`, `admite_circuito`.

Ni una regla de F-004 se toca: la aprobación se registra **al lado** del
veredicto, nunca encima (R11).

### T5 · `6ccf09a` — `ParteNoAprobable`

En `domain/models/errores.py`. Un error propio y **no un 400**: la petición
está bien formada; lo que no admite la decisión es el estado del parte. Un 400
mandaría a revisar el cuerpo a quien tiene que ir a corregir un campo del
papel.

### Un hueco que hay que declarar

**La traza de la fase RED de los bloques 0 y 1 se perdió.** El mensaje de
`1b30a7c` dice «Fase RED documentada en `progress/impl_F-026.md`», pero ese
fichero **no existía**: el agente se interrumpió antes de escribirlo. No se
reconstruye aquí porque una traza reconstruida hoy no es la que se pegó
entonces, y pegarla como si lo fuera sería peor que no tenerla. Lo que sí se
puede afirmar, y se afirma: el test de T1 es **anterior** al código de todos
los bloques posteriores, y eso consta en el orden de los commits. La fase RED
del **bloque 2** está pegada íntegra más abajo.

---

## 3 · Bloque 2 · lo que se ha hecho en esta tanda

### T6 · el DDL, declarado donde se declaran los demás — commit `1ece459`

El fichero `infrastructure/persistencia/sql/10_aprobaciones.sql` y su test
existían desde `f1e5718`. Lo que faltaba era **registrarlo**, y aquí conviene
precisar dónde, porque no es obvio: `ddl.py` **no lleva ninguna lista** —
`ficheros_ddl()` descubre los `.sql` por `glob` y los aplica en orden
lexicográfico—. El único sitio donde un fichero de DDL «se declara» es la
lista escrita **a mano y a propósito** de
`tests/test_f005_ddl_idempotente_texto.py`, cuya docstring lo dice:

> La lista se escribe entera y a mano **a propósito**: es la forma de que
> añadir o quitar un fichero de DDL no pueda pasar desapercibido.

Eso es lo que estaba en rojo. Cambios: la lista gana `"10_aprobaciones.sql"` y
la docstring recoge que F-026 añadió el décimo — y que llegó a existir como
fichero un commit antes de estar declarado, que es justo lo que la aserción
detectó.

### T7 · el SQL y el mapeo — commit `4d80aaa`

`infrastructure/persistencia/sentencias.py`:

| Función | Qué hace |
|---|---|
| `upsert_aprobacion(*, esquema, aprobacion)` | `INSERT … ON CONFLICT (hash_parte) DO UPDATE`, una sola fila por parte (R17) |
| `select_aprobacion(*, esquema, hash_parte)` | las nueve columnas, en el mismo orden que escribe el `upsert` |
| `revocar_aprobacion_si_cambio(*, esquema, resultado, ahora)` | el `UPDATE` de la revocación (R30) |

`infrastructure/persistencia/mapeo.py`: `json_de_codigos_de_motivo` y
`fila_a_aprobacion` (con `_codigos_desde_json`).

### T8 · el puerto y el adaptador — commit `fc5a37a`

- `domain/ports/persistencia.py`: `RepositorioPartesPort` gana
  `guardar_aprobacion` y `consultar_aprobacion`, y la docstring de
  `guardar_validacion` recoge que **revocar es parte de su contrato**.
- `infrastructure/persistencia/repositorio_pg.py`: las dos operaciones, y
  `guardar_validacion` ejecutando además la revocación.
- `domain/models/persistencia.py`: solo la nota de cabecera de datos
  personales, ampliada con `Aprobacion.aprobado_por` (lo que pedía
  `design.md` §9.2).
- `tests/utiles_pg.py`: `RepositorioEnMemoria` crece con las dos operaciones.

---

## 4 · Decisiones de diseño que conviene mirar al revisar

### 4.1 · La revocación ocurre **en la escritura** (D-F), y «en la misma operación» es literal

Es el punto que el encargo marcaba como innegociable. `guardar_validacion`
ejecuta dos sentencias **dentro del mismo cursor y con un solo `commit`**:

```python
guardado = self._escribir(
    sql, parametros, operacion="guardar_validacion", ademas=(revocacion,)
)
```

Para eso `_escribir` acepta `ademas`: sentencias que van en la misma
transacción, después de la principal y sin mirar lo que devuelvan. Con dos
transacciones habría una ventana —corta, pero real— en la que el veredicto
nuevo ya está guardado y la aprobación del viejo sigue viva, y un paso que
leyera justo ahí admitiría en el circuito un parte que nadie ha aprobado. Hay
un test que lo fija: `len(conexion.ejecutadas) == 2 and conexion.commits == 1`.

### 4.2 · La revocación se ejecuta **siempre**, haya aprobación o no

No se consulta antes para decidir si merece la pena. Si no hay aprobación, el
`UPDATE` no toca ninguna fila y no ha pasado nada. Consultar antes sería una
consulta de más en el camino **más transitado del servicio** —`POST /api/parte`
se llama una vez por parte y por reproceso— y, peor, una condición de carrera
con quien apruebe a la vez.

### 4.3 · El `upsert` no escribe las columnas de revocación **desde el objeto**

Podría: la dataclass las trae. Pero entonces que una segunda aprobación naciera
viva dependería de que quien la construya se acuerde de dejarlas a `None`. El
`DO UPDATE` las pone a **`NULL` literal**, con lo que la garantía la da la
sentencia (R17). Por eso hay dos listas de columnas —`_COLUMNAS_APROBACION_VIVA`
para escribir, `_COLUMNAS_APROBACION` para leer— y la segunda se construye
desde la primera, para que no puedan divergir.

### 4.4 · La huella viaja como **parámetro**, y se calcula en `sentencias.py`

`revocar_aprobacion_si_cambio` recibe el `ResultadoValidacion` y llama a
`huella_de_veredicto`. Es lo que mantiene el adaptador delgado —su propia
docstring dice que todo lo decidible sin base de datos vive en `sentencias.py`
y `mapeo.py`, que son puros y por tanto medidos y mutados—. El `WHERE` no lleva
nada interpolado: `hash_parte = %s AND revocada_at_utc IS NULL AND
huella_aprobada <> %s`.

### 4.5 · El identificador de quien aprueba se guarda **opaco**, y no se registra

`aprobado_por` es el `oid` de Entra ID y nada más (R13). Y el log del
repositorio dice **qué** se aprobó —`hash`, destino, resultado, vigencia— y
nunca **quién**, ni la huella. Hay un test con `caplog` que lo comprueba sobre
las dos operaciones nuevas: este log lo lee cualquiera que abra Application
Insights.

### 4.6 · Nada de lo tocado es de otra feature

No se ha tocado `domain/models/validacion.py`, ni `sql/04_validaciones.sql`,
ni `domain/models/cierre.py`, ni `infrastructure/sigrid/escrituras.py` — las
dos reglas duras de la cabecera de `tasks.md`. Tampoco `cola.py`, ni
`validar.py`, ni los tres handlers del circuito.

---

## 5 · Fase RED · las trazas reales

### 5.1 · T6 — el fichero de DDL sin declarar

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f005_ddl_idempotente_texto.py -q
```

Salida (recortada donde no aporta):

```
>       assert nombres == [
            "01_esquema.sql",
            ...
            "09_graficos.sql",
        ]
E       AssertionError: assert ['01_esquema....res.sql', ...] == ['01_esquema....res.sql', ...]
E
E         Left contains one more item: '10_aprobaciones.sql'
E         Use -v to get more diff

tests\test_f005_ddl_idempotente_texto.py:90: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f005_ddl_idempotente_texto.py::test_f005_r1_se_aplican_todos_los_ficheros_en_orden
1 failed, 25 passed in 0.79s
```

Después de declararlo: `54 passed in 0.68s` (ese fichero más el de F-026).

### 5.2 · T7 — las sentencias y el mapeo, antes de existir

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f026_persistencia.py -q
```

```
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f026_persistencia.py _______________
ImportError while importing test module '...\tests\test_f026_persistencia.py'.
Traceback:
tests\test_f026_persistencia.py:45: in <module>
    from infrastructure.persistencia.mapeo import (
E   ImportError: cannot import name 'fila_a_aprobacion' from
    'infrastructure.persistencia.mapeo'
=========================== short test summary info ===========================
ERROR tests/test_f026_persistencia.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.57s
```

Después de implementar T7: `21 passed in 0.89s`.

### 5.3 · T8 — el puerto, el adaptador y **la revocación que no ocurría**

Mismo comando, con la sección T8 ya escrita y el adaptador todavía sin tocar:

```
E       AttributeError: 'RepositorioPostgres' object has no attribute 'guardar_aprobacion'.
        Did you mean: 'guardar_validacion'?
E       AttributeError: 'RepositorioPostgres' object has no attribute 'consultar_aprobacion'
E       AssertionError: assert 0 == 1
E        +  where 0 = veces_con('UPDATE postventa.aprobaciones')
E       assert 1 == 2
E        +  where 1 = len([Ejecutada('INSERT INTO postventa.validaciones (hash_parte, veredicto, d', ...)])
E       AssertionError: no se ejecutó ninguna sentencia con 'UPDATE postventa.aprobaciones';
        se ejecutaron: ['INSERT INTO postventa.validaciones (hash_parte, veredicto, d']
E       IndexError: list index out of range

FAILED tests/test_f026_persistencia.py::test_f026_guardar_la_aprobacion_ejecuta_el_upsert
FAILED tests/test_f026_persistencia.py::test_f026_consultar_una_aprobacion_que_no_existe_devuelve_none
FAILED tests/test_f026_persistencia.py::test_f026_consultar_devuelve_la_aprobacion_del_parte
FAILED tests/test_f026_persistencia.py::test_f026_r30_guardar_una_validacion_revoca_en_la_misma_operacion
FAILED tests/test_f026_persistencia.py::test_f026_r30_las_dos_sentencias_van_en_una_sola_transaccion
FAILED tests/test_f026_persistencia.py::test_f026_r30_la_revocacion_compara_con_la_huella_del_veredicto_guardado
FAILED tests/test_f026_persistencia.py::test_f026_r32_revalidar_sin_cambios_manda_la_misma_huella
FAILED tests/test_f026_persistencia.py::test_f026_r30_un_veredicto_distinto_manda_otra_huella
FAILED tests/test_f026_persistencia.py::test_f026_r34_lo_que_se_escribe_como_motivo_es_la_etiqueta_corta
FAILED tests/test_f026_persistencia.py::test_f026_el_log_de_la_aprobacion_no_lleva_ni_el_oid_ni_la_huella
10 failed, 24 passed in 1.50s
```

El fallo que importa no es el `AttributeError` —eso solo dice que el método no
existe—, sino **`assert 0 == 1` sobre `veces_con('UPDATE postventa.aprobaciones')`**
y el `len(ejecutadas) == 1` en vez de 2: antes del cambio, guardar una
validación cuyo veredicto ya no era el aprobado **no revocaba nada**, que es
precisamente el agujero que D-F cierra.

Después de implementar T8: `34 passed in 1.08s`.

---

## 6 · Ficheros tocados en esta tanda

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/tests/test_f005_ddl_idempotente_texto.py` | la lista manual de ficheros de DDL gana el décimo, y la docstring lo cuenta |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | `upsert_aprobacion`, `select_aprobacion`, `revocar_aprobacion_si_cambio` y sus tres listas de columnas |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | `json_de_codigos_de_motivo`, `fila_a_aprobacion`, `_codigos_desde_json` |
| `services/postventa-api/domain/ports/persistencia.py` | `guardar_aprobacion`, `consultar_aprobacion`, y la revocación en el contrato de `guardar_validacion` |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | las dos operaciones, `_escribir(..., ademas=…)` y la revocación pegada al guardado |
| `services/postventa-api/domain/models/persistencia.py` | **solo** la nota de cabecera de datos personales |
| `services/postventa-api/tests/utiles_pg.py` | `RepositorioEnMemoria` cumple el puerto ampliado |
| `services/postventa-api/tests/test_f026_persistencia.py` | **nuevo**, 34 tests |
| `specs/F-026-aprobacion-humana/tasks.md` | T6, T7 y T8 marcadas |

**Ni una línea de producción fuera de `infrastructure/persistencia/` y de los
dos módulos de dominio citados.** Nada de Sigrid, nada de SharePoint, nada de
Azure, y ninguna conexión a base de datos: la guarda `sin_red` de
`tests/conftest.py` sigue puesta durante toda la suite.

---

## 7 · Lo que queda fuera y lo que falta

### Fuera del alcance de esta tanda (por encargo)

Los bloques 3, 4, 4 bis y 5 enteros. En concreto, y para que no se lea como un
olvido:

- **`POST /api/aprobar` no existe** (T9, T10). Nadie llama todavía a
  `guardar_aprobacion`.
- **Las tres puertas siguen mirando solo el veredicto** (T11). `admite_circuito`
  está escrito y probado, pero `paso_archivo`, `paso_grafico` y `paso_cierre`
  siguen con su `_exigir_apto`.
- **La respuesta de `POST /api/parte` todavía no trae el bloque `aprobacion`**
  (T12).
- **La pantalla no sabe nada de aprobaciones** (T13–T16).

### Pendiente y **MANUAL (humano)**

Todo el bloque 6 (T20–T23). El más relevante para lo escrito hoy:

- **T20** — que el DDL se aplica de verdad y es idempotente, y que la tabla
  tiene las nueve columnas. Un doble de conexión **no puede** demostrar que el
  SQL sea PostgreSQL válido: eso solo lo dice la base.
- **T23** — que la revocación funciona sobre datos reales: corregir un campo de
  un parte aprobado y no cerrado, revalidar, y ver `revocada_at_utc` relleno y
  `revocada_motivo = 'veredicto_cambiado'`.

Hasta que T20 se haga, lo único verificado del `.sql` es **su texto**.

---

## 8 · Evidencias

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** (servicio `api`) | **2 253 pasan, 13 se saltan**, 0 fallan |
| **Tests ejecutados** (raíz + servicio `front`) | 62 pasan (raíz) · front en verde |
| **Tests nuevos de esta tanda** | **34** (`test_f026_persistencia.py`) |
| **Cobertura de las líneas cambiadas** | **98,7 %** — 1 171 de 1 186 líneas, umbral 80 %, nivel `estandar` → `[OK]`. Al empezar la tanda: 47,6 % de 1 131, en `[KO]` |
| **Tiempo de la suite** (`api`, dentro de `init.sh`) | **95,5 s** (67,99 s en la ejecución aislada previa) |
| **Avisos de `ruff`** | **59**, los mismos que al empezar: esta tanda **no añade deuda de lint** |
| **`bash harness/init.sh`** | **ENTORNO LISTO** (exit 0) |
| **Mutantes generados y supervivientes** | ver §9 |

---

## 9 · Campaña de mutación

PENDIENTE-DE-RELLENAR
