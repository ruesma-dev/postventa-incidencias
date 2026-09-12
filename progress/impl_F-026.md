<!-- progress/impl_F-026.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Implementación

> Informe **acumulativo** de la feature, en dos partes. La **parte I** la
> escribió el implementer del **bloque 2** (2026-09-12), que además **recoge lo
> que hicieron los bloques 0 y 1** leyendo sus commits: los agentes que los
> escribieron se interrumpieron antes de redactar este fichero. Lo que allí se
> atribuye a ellos sale del código y del mensaje de su commit, y va marcado
> como tal. La **parte II** (§10 en adelante) la escribe el implementer del
> **bloque 3**, el mismo día.
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
| 3 · Las puertas y el borde HTTP | T9–T12 | **hecho** (`6b51d60`, `9760019`, `851f0d2`, `44c306c`) · ver parte II |
| 4 · La pantalla | T13–T16 | **hecho** (`3fbfbd2`, `bf2fdc0`, `48e2799`, `5270f8d`) · ver parte III |
| 4 bis · Autoguardado | TA1–TA5 | **hecho** (`428842c`, `7beaa0b`, `ebfb2ae`, `1259c39`) · ver parte IV |
| 5 · Enmiendas y documentación | T17–T19 | **hecho en esta tanda** (`b7ac982`, `c9258f0`, `02cb101`, `212ba40`, y `0d7c843` en `azure-apps`) · ver parte V |
| 6 · Verificación contra la base real | T20–T23 | **MANUAL (humano)**, pendiente |
| 7 · Cierre | T24–T25 | T25 en verde hoy; T24 se repite al cerrar |

> **Aviso de lectura.** El párrafo que sigue describía el estado **al cerrar el
> bloque 2** y dejó de ser cierto con el bloque 3, que es la parte II de este
> informe. Se conserva porque explica qué pasaba entre una tanda y la otra; lo
> que vale hoy está en §10.

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

> **Nota de concurrencia.** Esta sección la escribe el implementer del **bloque
> 2**, que **sí lanzó la campaña** al terminar su tanda. Mientras corría (49
> minutos), otro implementer trabajó el **bloque 3** en la misma rama y dejó
> aquí una versión de esta sección diciendo que no se había lanzado: no lo
> sabía. El informe de la campaña está en `progress/mutacion_F-026.md`. La
> Parte II, de la §10 en adelante, es suya y no se toca.

```
python -m harness.mutacion --feature F-026 --workers 8
242 mutantes evaluados, 228 muertos, 14 supervivientes, 0 timeouts en 2940.7 s
Informe: progress/mutacion_F-026.md
```

**Workers: 8**, los de `harness/rigor.json` (no se pasó `--workers`; el informe
lo registra igual). Sin muestreo: campaña completa. **Cero timeouts.**

| Métrica | Valor |
|---|---|
| Mutantes generados y evaluados | **242** |
| Muertos | **228** (94,2 %) |
| Supervivientes | **14** |
| Timeouts | **0** |
| Tiempo total | **2 940,7 s** (49 min) |
| Líneas en alcance | 6 382, en 25 ficheros |

### Los 14 supervivientes, analizados uno a uno

El análisis completo está en `progress/mutacion_F-026.md`, **sin ninguna
sección en `PENDIENTE`**. Resumen:

| Veredicto | Cuántos | Qué son |
|---|---|---|
| **Hueco real, tapado con test nuevo** | **3** | la inmutabilidad de `Aprobacion`; la guarda «no apto **sin** motivos» de `es_aprobable`; **cuál** de las columnas del `upsert` lleva `::jsonb` |
| **Equivalente, justificado** | **1** | `ensure_ascii` en `json_de_codigos_de_motivo`: los cuatro valores de `CodigoMotivo` son ASCII puro, así que ningún test puede distinguir las dos opciones sin inventar un código que no existe |
| **Fuera de F-026** | **10** | código de F-009, F-012 y F-025 que entra en el alcance porque la rama arranca de trabajo **no mergeado a `dev`**. Ya están analizados uno a uno en `progress/mutacion_F-012.md`, y no se duplica el análisis |

### El que más enseña: el `::jsonb`

El mutante cambiaba `columna == _COLUMNA_JSONB_APROBACION` por `!=`, y
**sobrevivía a la suite entera**. El test que miraba el `VALUES` contaba los
marcadores —y con la comparación invertida siguen siendo siete—, pero nadie
comprobaba *cuál* llevaba el `::jsonb`. No es cosmético en ninguna de las dos
direcciones: sin él, PostgreSQL rechaza el `INSERT` porque no convierte `text`
a `jsonb`; con él en las demás, el `oid` y la huella se intentarían convertir a
JSON. Las dos fallan en la **primera aprobación real contra la base**, no en la
suite.

### Los tres tests nuevos matan a sus mutantes · verificado a mano

Aplicadas las tres mutaciones sobre el árbol limpio:

```
FAILED tests/test_f026_aprobacion_dominio.py::test_f026_una_aprobacion_no_se_puede_modificar_despues_de_creada
FAILED tests/test_f026_aprobacion_dominio.py::test_f026_r8_un_no_apto_sin_motivos_no_es_aprobable
FAILED tests/test_f026_persistencia.py::test_f026_solo_la_columna_de_motivos_se_declara_como_jsonb
3 failed, 68 passed in 1.12s
```

Revertidas con `git checkout --`: `71 passed in 1.05s`.

### Esta campaña **no** sustituye a T24

Se lanzó con la feature a medias —sin bloque 3 cuando arrancó, y sin 4, 4 bis y
5 todavía—. `tasks.md` pone la campaña en **T24**, al cerrar, y **hay que
repetirla** allí: el alcance incluirá entonces el endpoint, las tres puertas y
el front. Lo que esta demuestra es el estado del dominio y de la persistencia
—y ya ha servido para tapar tres huecos reales que la suite no veía—.

---

# Parte II · Bloque 3 · Las puertas y el borde HTTP (2026-09-12)

> Segunda tanda del mismo día, por encargo acotado: **solo el bloque 3**
> (T9–T12). Los bloques 4, 4 bis y 5 **no se han tocado**, y esta tanda **no
> lanzó ninguna campaña de mutación**: lo prohibía el encargo.
>
> **Nota de concurrencia**, porque cambia cómo hay que leer la §9: mientras se
> escribía este bloque 3, el implementer del bloque 2 corría su campaña en la
> misma rama. Sus 242 mutantes se generaron sobre un árbol **sin el bloque 3**,
> así que **nada de lo que hay aquí está mutado**. T24 sigue en pie.
>
> El arnés estaba **en verde** al empezar (`ENTORNO LISTO`, cobertura 98,7 %),
> al contrario que en la tanda del bloque 2.

## 10 · Qué cambia de verdad con esta tanda

Hasta hoy, lo escrito por los bloques 0–2 **no cambiaba el comportamiento del
servicio**: la tabla existía y el repositorio sabía escribirla, pero nadie la
llamaba. A partir de este commit sí:

1. **Existe `POST /api/aprobar`** y una persona puede registrar su decisión.
2. **Las tres puertas del circuito miran dos cosas** en vez de una, así que un
   parte no apto **con aprobación viva del mismo destino** archiva, adjunta y
   cierra igual que un apto (R23).
3. **`POST /api/parte` cuenta si el parte consta aprobado** (R22).

Lo que **no** cambia, y está probado que no cambia: un parte no apto **sin**
aprobación sigue sin archivar, sin adjuntar y sin cerrar (R25, los trece casos
de control negativo de T1 siguen enteros en verde); y ninguno de los tres
endpoints del circuito gana una sola clave en su cuerpo (R24).

---

## 11 · T9 · el handler de `POST /api/aprobar`

`interface_adapters/api/aprobar.py`. Lo que decide el diseño del handler:

- **Dos puertas antes de tocar el puerto**, para que R20 («en los tres casos,
  sin haber escrito nada») sea verdad por construcción y no por suerte:
  1. `usuario_oid` no vacío (R4) y `confirmado` **exactamente `True`** —el
     booleano de JSON, no `"true"` ni `1`: un cliente que serializa mal no es
     una persona que confirma—;
  2. `es_aprobable` sobre el veredicto **recalculado** con `validar_parte`
     (R5). Este orden es lo que sostiene R9: si el veredicto llegara hecho,
     quien llama se declararía aprobable y aprobaría un parte al que le falta
     el código de obra.
- **Una llamada, tres escrituras, y en este orden**: parte → validación →
  aprobación. La validación va antes porque **guardarla revoca** la aprobación
  cuyo veredicto ya no coincide (R30, bloque 2); escribir la aprobación antes
  la dejaría revocada en el mismo acto de nacer. Hay un test que fija el orden
  (`..._se_guardan_antes_que_la_aprobacion`), no un comentario.
- **`ParteNoAprobable` distingue los dos casos** porque se arreglan de forma
  opuesta: al parte ya apto no hay que hacerle nada (R10); al que perdió un
  dato decisivo hay que **teclearlo** (R9), y el motivo lo dice nombrando el
  código que lo impide y sin una letra del papel (R43).

### Dos decisiones de estructura que el diseño no fijaba

**Los parsers del cuerpo bajaron a `cuerpos.py`.** `CLAVES_DEL_PARTE`,
`a_remesa_id` y `a_parte_troceado` eran privados de `parte.py`, y
`/api/aprobar` recibe **el mismo cuerpo**. Es la mudanza que ya hizo F-019 con
los parsers de `/api/validar`, y por el mismo motivo, que aquí muerde más
fuerte: el día que aprobar y guardar describan el parte de dos formas
distintas, **se aprueba un veredicto y se guarda otro**. Ni una regla ni un
mensaje de error cambian; lo confirman los 42 tests de `test_f019_parte_http.py`.

**`_AnotaLosResultados` pasa a ser `AnotaLosResultados`.** Los dos endpoints
componen exactamente lo mismo —guardar el parte y su veredicto, y contar qué
pasó con cada uno—, y dos envoltorios distintos informarían del mismo hecho de
dos formas distintas. Se toca una línea del test de F-019 que lo importaba por
su nombre privado.

### Fase RED de T9

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f026_aprobar_http.py -x -q
```

```
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f026_aprobar_http.py _______________
ImportError while importing test module 'C:\...\tests\test_f026_aprobar_http.py'.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f026_aprobar_http.py:47: in <module>
    from interface_adapters.api.aprobar import aprobar_parte_http
E   ModuleNotFoundError: No module named 'interface_adapters.api.aprobar'
=========================== short test summary info ===========================
ERROR tests/test_f026_aprobar_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.25s
```

Después de implementar T9: `31 passed in 2.87s`.

---

## 12 · T10 · la ruta, su traducción de errores y su log

`function_app.py` gana `POST /api/aprobar`, `ANONYMOUS` como las otras once, y
**solo traduce**: 400 / 409 / 503 según `design.md` §6. El 400 y el 409 no se
confunden a propósito —uno manda a revisar el cuerpo, el otro a corregir el
papel, y son dos sitios y dos personas distintas—, que es la misma lección del
defecto 15 de F-010.

El log lleva `hash_parte`, destino y resultado, y **nada más** (R44). Es el
endpoint donde más fácil sería filtrar: su cuerpo trae los nueve campos del
papel **y** el `oid` de quien decide.

**`test_f010_endpoints_protegidos.py` pasa de once endpoints a doce.** No es
daño colateral: es su mecanismo declarado —«la cuenta tuvo que cuadrar aquí
antes de que la ruta existiera»—, y la cabecera del fichero explica por qué
este también es `ANONYMOUS` (quien protege el servicio es Easy Auth por
delante, no la clave de función).

### Fase RED de T10

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f026_aprobar_http.py -q
```

```
    def _con_doble(monkeypatch, repositorio) -> None:
        """Inyecta el repositorio por la costura del handler. Sin base de datos."""
        import function_app

        def envoltura(cuerpo, **datos):
            return aprobar_parte_http(cuerpo, repositorio=repositorio, **datos)

>       monkeypatch.setattr(function_app, "aprobar_parte_http", envoltura)
E       AttributeError: <module 'function_app' from '...\function_app.py'> has no
    attribute 'aprobar_parte_http'

FAILED tests/test_f026_aprobar_http.py::test_f026_r20_aprobar_devuelve_200_con_su_contrato
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_un_cuerpo_que_no_es_json_es_400
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_r4_sin_usuario_oid_el_borde_responde_400
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_un_parte_no_aprobable_es_409[le-falta-el-codigo-de-obra]
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_un_parte_no_aprobable_es_409[ya-es-apto]
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_sin_remesa_registrada_es_409
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_sin_base_de_datos_es_503[fallo0]
FAILED tests/test_f026_aprobar_http.py::test_f026_r20_sin_base_de_datos_es_503[fallo1]
FAILED tests/test_f026_aprobar_http.py::test_f026_r44_el_log_lleva_hash_destino_y_resultado_y_nada_mas
FAILED tests/test_f026_aprobar_http.py::test_f026_r44_un_rechazo_tampoco_publica_lo_que_venia
FAILED tests/test_f026_aprobar_http.py::test_f026_r18_la_ruta_es_post_anonima_y_se_llama_aprobar
FAILED tests/test_f026_aprobar_http.py::test_f026_r21_la_ruta_no_mira_las_ventanas_de_escritura
12 failed, 31 passed in 5.44s
```

Después de implementar T10: `43 passed in 3.48s`.

---

## 13 · T11 · las tres puertas

`_exigir_apto(ctx)` → `_exigir_admitido(ctx, repositorio)` en `paso_archivo`,
`paso_grafico` y `paso_cierre`. Los tres hacen lo mismo:

```
si no hay veredicto            -> ParteNoApto (motivo propio: se revalida, no se aprueba)
si admite_circuito(v, None)    -> pasa (el apto de siempre, sin consultar nada)
ctx.aprobacion = repositorio.consultar_aprobacion(hash_parte=...)
si admite_circuito(v, aprob)   -> pasa (R23)
si no                          -> ParteNoApto, diciendo el destino y que nadie lo aprobó
```

Cuatro cosas que importan, y por qué:

- **Ninguna firma de paso cambia y ningún cuerpo de petición gana una clave.**
  La aprobación se **lee del repositorio dentro del paso** (R24), que es el
  precedente exacto de `traza_grafico` en F-012: si viniera del cuerpo, quien
  llama podría afirmar que alguien aprobó lo que nadie aprobó.
- **La consulta solo se hace cuando el veredicto no basta.** El parte apto no
  paga una lectura que no puede cambiar la decisión: en una remesa real de 22
  partes serían 66 consultas inútiles. Hay un test que lo fija
  (`..._el_parte_apto_de_siempre_no_consulta_ninguna_aprobacion`), para que no
  se pierda en la primera refactorización.
- **`admite_circuito` es dominio puro** y ya venía probado del bloque 1: la
  decisión no se reescribe en tres sitios.
- **La aprobación de otro destino no sirve.** Si el parte pasó de la cola ámbar
  a revisión manual, lo que alguien juzgó ya no es lo que hay delante.

### Dos guardianes ajenos que se enteraron, y qué se hizo con ellos

- **`test_f003_paso_extraccion.py`** fija los campos de `ContextoParte`. Se le
  declara `aprobacion` con el comentario que dice qué es y de dónde viene —el
  mismo trato que recibieron `archivo`, `cierre` y `traza_grafico`—. El test
  sigue impidiendo exactamente lo que impedía.
- **`RepositorioFalso`** (`tests/utiles_sharepoint.py`) gana
  `consultar_aprobacion` devolviendo `None`, porque los tests de F-006
  archivan también partes **no aptos** y esos ahora pasan por la consulta.
  `None` no es un error: es «no lo aprobó nadie». Y **no se apunta en
  `registro`**, que es lo que fija el orden de las *escrituras* de F-019: una
  lectura ahí convertiría «no se escribió nada» en «se escribió algo» en
  `test_f019_r19_un_parte_no_apto_no_escribe_ni_la_traza_previa`.

### Fase RED de T11

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f026_puertas.py -q
```

```
>       ctx = _archivar(repositorio, destino, archivador)
...
            raise ParteNoApto(
                f"el parte no es apto para archivo y cierre: la validación lo "
                f"manda a «{ctx.validacion.destino.value}»"
            )
E           domain.models.errores.ParteNoApto: el parte no es apto para archivo y
    cierre: la validación lo manda a «revision_manual»

application\pipelines\paso_archivo.py:232: ParteNoApto
=========================== short test summary info ===========================
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_se_archiva[cola_validacion_humana]
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_se_archiva[revision_manual]
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_se_adjunta[cola_validacion_humana]
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_se_adjunta[revision_manual]
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_llega_al_cierre[cola_validacion_humana]
FAILED tests/test_f026_puertas.py::test_f026_r23_un_parte_aprobado_y_vigente_si_llega_al_cierre[revision_manual]
FAILED tests/test_f026_puertas.py::test_f026_r24_los_tres_pasos_leen_la_aprobacion_del_repositorio[cola_validacion_humana]
FAILED tests/test_f026_puertas.py::test_f026_r24_los_tres_pasos_leen_la_aprobacion_del_repositorio[revision_manual]
8 failed, 18 passed in 2.73s
```

Y, a medio camino —con la puerta de archivo ya cambiada y el doble de F-006
todavía sin la operación nueva—, el fallo que descubrió el segundo guardián:

```
>       ctx.aprobacion = repositorio.consultar_aprobacion(hash_parte=ctx.parte.hash)
E       AttributeError: 'RepositorioFalso' object has no attribute 'consultar_aprobacion'

application\pipelines\paso_archivo.py:241: AttributeError
```

Después de implementar T11: `26 passed in 1.95s`, y la suite entera del
servicio en verde.

---

## 14 · T12 · `POST /api/parte` dice si el parte consta aprobado

La respuesta gana el bloque `aprobacion`, **leído después de guardar**. El
orden es el requisito: `guardar_validacion` revoca la aprobación cuyo veredicto
ya no coincide (R30), así que leerla antes devolvería como viva una aprobación
que esa misma llamada acaba de tumbar, y la pantalla pintaría la marca de un
parte que ya no circula. Hay un test del orden.

Tres valores y no dos: el bloque, `null` cuando no lo aprobó nadie, y
`estado: "revocado"` cuando se decidió y dejó de valer. **`revocado` y `null`
son distintos a propósito** (R31): es lo que hace que alguien vuelva a mirar el
parte en vez de darlo por olvidado.

La serialización vive en `interface_adapters/api/aprobacion_serializada.py`,
compartida por los dos endpoints. Módulo propio para una sola función porque
`aprobar.py` ya importa de `parte.py` el envoltorio de resultados y devolverle
el favor los volvería mutuamente dependientes; y porque lo que divergiría si
hubiera dos copias es **qué se publica de una decisión que lleva dentro el
`oid` de una persona**.

`test_f019_parte_http.py` declara la clave nueva en `CLAVES_DE_LA_RESPUESTA`:
ese conjunto es el contrato, y crece donde se ve.

### Fase RED de T12

Comando:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/test_f026_aprobar_http.py -q
```

```
>       assert cuerpo["aprobacion"] == {
            "estado": "aprobado",
            "destino_aprobado": "cola_validacion_humana",
            "motivos_aprobados": ["observaciones_manuscritas"],
            "aprobado_at_utc": AHORA.isoformat(),
        }
E       KeyError: 'aprobacion'

tests\test_f026_aprobar_http.py:895: KeyError

E         Right contains one more item: 'consulta_aprobacion'
FAILED tests/test_f026_aprobar_http.py::test_f026_r22_guardar_un_parte_aprobado_lo_dice_en_la_respuesta
FAILED tests/test_f026_aprobar_http.py::test_f026_r22_un_parte_que_no_ha_aprobado_nadie_devuelve_null
FAILED tests/test_f026_aprobar_http.py::test_f026_r22_una_aprobacion_revocada_se_devuelve_como_revocada
FAILED tests/test_f026_aprobar_http.py::test_f026_r22_la_aprobacion_se_lee_despues_de_guardar
4 failed, 44 passed in 4.57s
```

Después de implementar T12: `48 passed`, y `test_f019_parte_http.py` en verde
con la clave declarada.

---

## 15 · Ficheros tocados en el bloque 3

| Fichero | Qué cambia |
|---|---|
| `interface_adapters/api/aprobar.py` | **nuevo** · el handler de `POST /api/aprobar` |
| `interface_adapters/api/aprobacion_serializada.py` | **nuevo** · el bloque `aprobacion` de la respuesta, compartido |
| `interface_adapters/api/cuerpos.py` | reciben `CLAVES_DEL_PARTE`, `a_remesa_id` y `a_parte_troceado`, sin cambiar ni una regla |
| `interface_adapters/api/parte.py` | usa los parsers mudados; `AnotaLosResultados` público y con las dos operaciones nuevas; la respuesta gana `aprobacion` |
| `function_app.py` | la ruta `aprobar`, su traducción de errores, su log y la entrada en la cabecera |
| `application/pipelines/contexto_parte.py` | campo `aprobacion` y la docstring que dice que **viene del repositorio** |
| `application/pipelines/paso_archivo.py` | `_exigir_apto` → `_exigir_admitido` |
| `application/pipelines/paso_grafico.py` | ídem |
| `application/pipelines/paso_cierre.py` | ídem |
| `tests/test_f026_aprobar_http.py` | **nuevo**, 48 tests |
| `tests/test_f026_puertas.py` | de 13 a **26** casos: los positivos de R23, R24 y R31 |
| `tests/utiles_sharepoint.py` | `RepositorioFalso.consultar_aprobacion` → `None` |
| `tests/test_f003_paso_extraccion.py` | declara `aprobacion` entre los campos del contexto |
| `tests/test_f010_endpoints_protegidos.py` | doce endpoints en vez de once |
| `tests/test_f019_parte_http.py` | declara `aprobacion` en el contrato de la respuesta; `AnotaLosResultados` |
| `specs/F-026-aprobacion-humana/tasks.md` | T9–T12 marcadas |

**Ni una línea en `domain/models/validacion.py`, `sql/04_validaciones.sql`,
`domain/models/cierre.py` ni `infrastructure/sigrid/escrituras.py`** — las dos
reglas duras de `tasks.md`. Tampoco en `cola.py`, `validar.py`,
`archivar.py`, `adjuntar.py`, `cerrar.py` ni `js/confirmacion.js`. Ninguna
conexión a base de datos, ninguna llamada a Azure, a Sigrid ni a SharePoint: la
guarda `sin_red` de `tests/conftest.py` sigue puesta durante toda la suite.

---

## 16 · Lo que queda fuera y lo que falta

### Fuera del alcance de esta tanda (por encargo explícito)

- **Bloque 4 (T13–T16)**: la pantalla. `js/pipeline.js`, `js/api.js`,
  `js/app.js` e `index.html` **no se han tocado**. Hoy el backend admite en el
  circuito un parte aprobado, pero **no hay forma de aprobarlo desde la
  interfaz**: el endpoint solo se puede llamar a mano.
- **Bloque 4 bis (TA1–TA5)**: el autoguardado de las correcciones.
- **Bloque 5 (T17–T19)**: las enmiendas a F-025, los tres puntos de
  `docs/ARCHITECTURE.md` y el documento de `azure-apps/`. El endpoint nuevo y
  la tabla nueva **todavía no están documentados fuera de la spec**.
- **Bloque 7 (T24)**: la campaña de mutación, que el encargo reserva al líder.

### Pendiente y **MANUAL (humano)** · bloque 6

Lo escrito hoy está probado **entero con dobles en memoria**, que es como se
prueban F-006, F-012 y F-025, y no sustituye a T20–T23:

- **T21** — el circuito completo de un parte aprobado, extremo a extremo. Lo
  que los tests demuestran es que **la puerta se abre**; que SharePoint acepte
  el fichero y que Sigrid cambie el estado solo lo dice el entorno desplegado,
  con autorización expresa para la incidencia concreta.
- **T22** — que la traza hasta el ERP se puede reconstruir con el `JOIN` de la
  spec.
- **T23** — la revocación sobre datos reales.

### Un aviso que hay que leer antes de desplegar

`POST /api/aprobar` está **vivo en cuanto se despliegue**, y no depende de
`ARCHIVO_HABILITADO` ni de `CIERRE_HABILITADO` (R21, y es deliberado). Escribe
solo en el esquema propio, así que no puede tocar SharePoint ni el ERP por sí
mismo; lo que sí hace es **habilitar** que un parte no apto entre en el
circuito cuando alguien lo apruebe. La confirmación única de F-025 sigue
intacta delante de toda escritura externa (R27).

---

## 17 · Evidencias del bloque 3

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** (servicio `api`) | **2 317 pasan, 13 se saltan**, 0 fallan (eran 2 253 al cerrar el bloque 2). La cuenta subió de 2 314 a 2 317 al escribir este informe: hay barridos parametrizados que recorren los ficheros del árbol —los de `progress/` incluidos— y crecen con ellos |
| **Tests ejecutados** (raíz) | **62 pasan** en 12,29 s |
| **Tests ejecutados** (servicio `front`) | en verde, sin cambios (caché del arnés: el árbol del front no se ha tocado) |
| **Tests nuevos de esta tanda** | **61** — 48 en `test_f026_aprobar_http.py` y 13 más en `test_f026_puertas.py` |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1 325 de 1 338 líneas, umbral 80 %, nivel `estandar` → `[OK]` (venía de 98,7 % de 1 186) |
| **Tiempo de la suite** (`api`, dentro de `init.sh`) | **94,61 s** en la ejecución final (154,11 s en una anterior, con la máquina más cargada) |
| **Avisos de `ruff`** | **60**, uno más que los 59 de partida. El nuevo es un `I001` en `aprobar.py`, del **mismo tipo** que los otros 20 del servicio: el repositorio separa con línea en blanco el grupo `interface_adapters`/`application` y ruff, sin configuración de `known-first-party`, lo considera desordenado. Se ha seguido la convención del propio servicio en vez de dejar el fichero nuevo como la excepción; corregirlo de verdad es una línea de configuración que afectaría a los 21 a la vez y es decisión del líder, no de esta tanda |
| **`bash harness/init.sh`** | **ENTORNO LISTO** (exit 0) |
| **Mutantes generados y supervivientes** | **esta tanda no lanzó ninguna campaña**, por instrucción explícita del encargo. Sí la lanzó en paralelo el implementer del bloque 2 —242 mutantes, 228 muertos, **14 supervivientes**, 0 timeouts; §9 y `progress/mutacion_F-026.md`—, pero **sobre un árbol en el que el bloque 3 no existía**: ni `aprobar.py`, ni `aprobacion_serializada.py`, ni las tres puertas nuevas entraron en su alcance. Así que **nada de lo escrito en esta parte II está mutado**, y **T24 sigue siendo obligatoria** antes de cerrar F-026 (C4 bis), sobre la feature entera |

---
---

# Parte III · Bloque 4 · La pantalla (T13–T16)

> Tanda del **2026-09-12**. Encargo acotado: **solo el bloque 4**, y parar ahí.
> **No** se ha tocado el bloque 4 bis (el autoguardado), ni el 5, ni el 6, ni
> el 7. **No** se ha lanzado ninguna campaña de mutación: va en el cierre y la
> lleva el líder.
>
> Cuatro commits, uno por tarea: `3fbfbd2` (T13), `bf2fdc0` (T14), `48e2799`
> (T15) y `5270f8d` (T16).

## 18 · Qué cambia de verdad con esta tanda

Hasta hoy el backend admitía en el circuito un parte aprobado y **no había
forma de aprobarlo**: el endpoint solo se podía llamar a mano. A partir de
estos cuatro commits:

1. **quien revisa puede aprobar**, con el PDF delante, desde el detalle del
   parte y con un botón que no pide una segunda confirmación (R29, P7);
2. **un parte aprobado no se lee igual que uno que siempre fue verde** (R36):
   el semáforo tiene un cuarto estado, con marca propia —el mismo punto verde
   **con anillo**— y un texto que dice que lo aprobó una persona, de qué
   destino se rescató y cuándo (R37);
3. **el aprobado entra en la tanda** de archivo, gráfico y cierre (R23), y el
   revocado vuelve a salir de ella (R31).

Lo que **no** cambia, y hay control negativo de cada cosa: un no apto sin
aprobación sigue fuera de la tanda (R25), `esArchivable` conserva su
significado —«lo que dio por bueno **la máquina**»—, y en todo el front se
sigue armando **una sola** confirmación (R29, y R2 de F-025).

## 19 · T13 · `js/pipeline.js` · las reglas, donde hay tests

`MOTIVOS_APROBABLES`, `esAprobable`, `esCirculable`, `cuerpoDeAprobacion` y
`semaforoDe(validacion, aprobacion)`, todos exportados. Son la copia en
pantalla de `domain/models/aprobacion.py`: **la decisión de verdad la toma el
backend**, que vuelve a evaluarla con el veredicto que él mismo recalcula (R5).
Lo de aquí evita ofrecer un gesto que va a responder 409 y se niega a componer
cuerpos que el backend rechazaría.

El cuarto estado **no sustituye** a los tres de F-007: `semaforoDe` sigue
devolviendo `verde`, `ambar`, `rojo` y `""` exactamente igual cuando no hay
aprobación, y `aprobado` solo cuando la hay, está vigente y su
`destino_aprobado` coincide con el destino del veredicto de ahora. Un apto
sigue siendo verde aunque alguien lo hubiera aprobado.

## 20 · T14 · el circuito entero pasa por `esCirculable`

Cuatro sitios, y los cuatro importan: `pendientesDeCircuito` (quién entra en la
tanda), `cuerpoDeArchivo`, `esCerrable` —y por su puerta `cuerpoDeGrafico` y
`cuerpoDeCierre`—. Si uno solo se hubiera quedado mirando `esArchivable`, la
feature entera se habría quedado en una marca de color y encima el botón
parecería funcionar.

`esArchivable` **se conserva intacta** con su significado de siempre, porque la
usa `noArchivables()` y porque la distinción entre «lo dio por bueno la
máquina» y «lo dio por bueno una persona» es el requisito, no un detalle.

Los mensajes de rechazo de los tres compositores se han precisado —ahora dicen
que hace falta el apto **o** una aprobación vigente— conservando las subcadenas
que los tests de F-007, F-009 y F-012 afirman (`no es apto`, `no se puede
adjuntar`, `no se puede cerrar`). `tests_js/circuito.test.js` y
`tests_js/pipeline.test.js` siguen **enteros en verde y sin tocarlos**, como
pedía la tarea: los casos nuevos viven en `tests_js/aprobacion.test.js`.

## 21 · T15 · el gesto: `js/api.js` y `js/app.js`

- `api.aprobar(cuerpo, hash)` → `POST /api/aprobar`, JSON, con **paso propio**
  en la traza (`aprobar`): el registro tiene que poder distinguir «alguien
  guardó el parte» de «alguien decidió aprobarlo». Por la traza siguen pasando
  solo `hash`, `paso`, `estado` y `http` (R28 de F-007, R43).
- `app.aprobarParte()` compone el cuerpo con `js/pipeline.js`, llama, y guarda
  **lo que devuelve el backend**: quién decide si la aprobación sigue vigente
  es quien la escribió (D-F). La pantalla no se lo inventa.
- `_parteInicial` declara `aprobacion: null`. Sin declararla, Alpine no la hace
  reactiva y **la marca no repintaría** al aprobar: es el defecto que F-025
  documentó con `paso`, repetido.
- `esAprobable()`, `estaAprobado()`, `destinoDeOrigen()` y
  `fechaDeAprobacion()` son lecturas y formateo; ninguna decide nada.

## 22 · T16 · `index.html`

El botón «Aprobar este parte» va **en el detalle** y no en la lista (R35, y
R28: aprobar es de **un** parte, con ese parte delante; un botón por fila
invita a ir bajando y pulsando). La marca del semáforo del aprobado es
`bg-emerald-500 ring-2 ring-offset-1 ring-sky-600` —el mismo verde **con
anillo**, nunca el verde liso (R36)—, con su texto al lado en la fila y en el
detalle. Cuando el parte no es aprobable, en vez del botón va la frase que dice
**qué corregir** (R39). Y sin identidad el botón queda deshabilitado **con su
explicación** (R4), no mudo.

El contador de la sección de archivo decía «parte(s) **en verde** por archivar
y cerrar» y ya no era cierto: desde F-026 la tanda incluye los aprobados, que
no son verdes. Se ha corregido el texto, y hay un test que lo vigila.

## 23 · Decisiones que conviene mirar al revisar

### 23.1 · El cuerpo de aprobar es el de guardar **más dos claves** — y por qué

`tasks.md` T13 pide que `cuerpoDeAprobacion` «**no** lleve DNI, observaciones
ni bytes (R19)». **Se ha implementado lo que dice `design.md` §6** —«el mismo
cuerpo que `POST /api/parte` más `usuario_oid` y `confirmado`»—, y la
divergencia con la literalidad de la tarea es deliberada y se declara aquí:

- el backend **recalcula el veredicto** con `validar_parte` (R5) y lo hace
  sobre la extracción del cuerpo. **Sin el texto de las observaciones, el parte
  no traería `observaciones_manuscritas` y dejaría de ser aprobable**: aprobar
  contestaría 409 a todos los partes de la cola ámbar, que son la mitad del
  motivo de la feature;
- `cuerpos.py` exige las **nueve** claves de la extracción y responde 400 si
  falta una, y `/api/aprobar` **guarda el parte** en la misma llamada
  (`paso_persistencia`): mandar el DNI vacío no lo protegería de nada y
  **borraría de la base** lo que ya estaba guardado;
- el DNI y las observaciones **ya viajan** en cada `POST /api/parte` y en cada
  revalidación, así que no hay ninguna exposición nueva.

Lo que sí fija el test (`f026 R19: el cuerpo de aprobar es el de guardar MÁS
dos claves, y ni una más`) es que F-026 **no añade nada personal por su
cuenta**: las únicas claves nuevas son `usuario_oid` y `confirmado`, la
extracción es **idéntica** a la de guardar, y no viajan ni los bytes del PDF ni
un veredicto ya hecho. **Es un punto a confirmar por el líder**: si se prefiere
la lectura literal de T13, hay que cambiar antes el diseño y el backend, no el
front.

### 23.2 · `guardarParte` propaga la `aprobacion` de la respuesta · añadido

No está en la letra de T13–T16, y se ha hecho igualmente porque **sin ello la
pantalla miente**. `guardarParte` devuelve ahora `{ok, motivo, aprobacion}` y
`_anotarGuardado` la aplica cuando el guardado salió bien. Dos consecuencias,
las dos son requisito:

- **R31** · la revocación ocurre **en la escritura** (D-F): revalidar un parte
  corregido revoca su aprobación en la misma operación. Sin propagarla, la
  pantalla seguiría pintándolo «aprobado» y dejándolo entrar en la tanda hasta
  que alguien recargase, y el backend lo rechazaría con un error que nadie
  sabría leer.
- **R22** · al volver a subir la remesa —que es como se recupera el trabajo
  tras recargar— los partes aprobados se reconocen **sin una petición por
  parte** (22 llamadas de más en una remesa real), que es exactamente para lo
  que T12 puso el bloque en la respuesta de `/api/parte`.

Un guardado **fallido** no toca la aprobación: no se inventa ninguna y no borra
la que hubiera.

### 23.3 · Ni un dato personal nuevo en la pantalla

El identificador de quien aprueba **no se pinta** (R38, R43). El bloque que
llega del backend trae cuatro claves y ninguna es personal, y hay un test que
comprueba que la pantalla **solo** usa esas cuatro: leer una que no existe no
rompería nada —pintaría vacío— y por eso hay que mirarlo en el texto.

El guardián de F-025
—`test_f025_r46_los_textos_de_pantalla_no_llevan_datos_personales`— **cazó de
verdad** un texto de esta tanda: la frase de R39 decía «por las observaciones
manuscritas», y ese guardián prohíbe la palabra `observaciones` en todo el
HTML. Se reescribió la frase («por lo que el cliente escribió a mano») en vez
de tocar el test de otra feature.

### 23.4 · Nada de lo tocado es de otra feature

Ni una línea en `domain/models/validacion.py`, `sql/04_validaciones.sql`,
`domain/models/cierre.py`, `infrastructure/sigrid/escrituras.py` ni
`js/confirmacion.js` — las dos reglas duras de `tasks.md` y R29. Ningún fichero
del backend se ha tocado en esta tanda: el bloque 4 es **solo** front.

## 24 · Fase RED · las trazas reales

### 24.1 · T13 — `tests_js/aprobacion.test.js` antes de que existiera el código

```
$ cd services/postventa-front && node --test tests_js/aprobacion.test.js
✖ f026 R6: la lista de motivos aprobables es la del dominio, y solo esos dos (1.31ms)
✖ f026 R8: un parte con observaciones manuscritas es aprobable (0.25ms)
✖ f026 R9: con un motivo fuera de la lista NO es aprobable, aunque haya otro que sí
✖ f026 R10: un parte que la máquina dio por bueno no tiene nada que aprobar
✖ f026 R36: un parte aprobado y vigente se pinta 'aprobado', nunca 'verde' (1.26ms)
✖ f026 R23: un no apto con aprobación viva del mismo destino entra en el circuito
✖ f026 R4: sin saber quién aprueba no se compone ninguna petición (1.43ms)
ℹ tests 24
ℹ pass 3
ℹ fail 21

✖ failing tests:
  TypeError: Cannot read properties of undefined (reading 'slice')
      at TestContext.<anonymous> (...\tests_js\aprobacion.test.js:124:39)
  TypeError: esAprobable is not a function
      at TestContext.<anonymous> (...\tests_js\aprobacion.test.js:131:16)

✖ f026 R36: un parte aprobado y vigente se pinta 'aprobado', nunca 'verde'
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected

  + 'ambar'
  - 'aprobado'
```

**Los tres que pasaban en rojo dicen algo**, y por eso se dejan documentados:
«la revocada vuelve a ámbar», «la aprobación no cambia el verde» y el control
negativo de los tres semáforos de F-007 pasaban ya, porque `semaforoDe`
ignoraba su segundo argumento. Son precisamente los casos en los que la
respuesta correcta y la respuesta vieja coinciden; el que sostiene R36 es el
positivo, y ese salía `'ambar'` donde tenía que salir `'aprobado'`.

### 24.2 · T14 — el circuito, antes de pasar por `esCirculable`

```
$ cd services/postventa-front && node --test tests_js/aprobacion.test.js
✖ f026 R23: un aprobado vigente entra en la tanda de la confirmación única
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:

  0 !== 1

      at TestContext.<anonymous> (...\tests_js\aprobacion.test.js:410:10)

✖ f026 R23: el cuerpo de archivo se compone para un parte aprobado
  Error: este parte no es apto para archivo (hace falta veredicto 'apto' y destino 'archivo_y_cierre')
      at cuerpoDeArchivo (...\js\pipeline.js:309:13)
      at TestContext.<anonymous> (...\tests_js\aprobacion.test.js:434:18)
ℹ tests 34
ℹ pass 30
ℹ fail 4
```

### 24.3 · T15 — el endpoint del front y el estado del parte

```
$ cd services/postventa-front && node --test tests_js/api.test.js
✖ f007 R27 / f019 / f009 / f012 / f026: los DOCE endpoints llaman a su ruta, con su metodo
✖ f007 R27: son doce, y la lista se entera si aparece un decimotercero
✖ f026: aprobar manda POST /api/aprobar, con cuerpo JSON y su paso propio
ℹ tests 47
ℹ pass 42
ℹ fail 5

  TypeError: api.aprobar is not a function
```

```
$ cd services/postventa-front && python -m pytest tests/test_f026_front.py -q --tb=line
FF.FFFF                                                                  [100%]
tests\test_f026_front.py:105: AssertionError: `_parteInicial` no declara `aprobacion`:
    la marca del parte aprobado no repintaría al aprobarlo
tests\test_f026_front.py:115: AssertionError: la aprobación tiene que nacer vacía
tests\test_f026_front.py:159: AssertionError: assert 'window.Pipeline.esAprobable(' in '...'
tests\test_f026_front.py:169: assert '"/aprobar"' in '...'
6 failed, 1 passed in 0.07s
```

Y la propagación de la aprobación (§23.2), antes de que `guardarParte` la
devolviera:

```
$ cd services/postventa-front && node --test tests_js/aprobacion.test.js
✖ f026 R22: al guardar, la aprobación que devuelve el backend llega al parte
✖ f026 R31: si el backend dice que la revocó, eso es lo que llega
✖ f026 R22: sin aprobación en la respuesta, lo que llega es null y no un hueco
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected

  + undefined
  - null
ℹ tests 38
ℹ pass 34
ℹ fail 4
```

### 24.4 · T16 — la pantalla, antes de tener el botón y la marca

```
$ cd services/postventa-front && python -m pytest tests/test_f026_front.py -q --tb=line
tests\test_f026_front.py:203: assert 'Aprobar este parte' in 'x-show="parteAbierto">...'
tests\test_f026_front.py:221: assert ('x-show="esAprobable()"' in '...' or 'esAprobable()' in '...')
tests\test_f026_front.py:232: assert 'código de obra' in '...'
tests\test_f026_front.py:245: AssertionError: la fila no mira el cuarto estado del semáforo
tests\test_f026_front.py:260: assert ('revisión humana' in '...' or 'una persona' in '...')
tests\test_f026_front.py:267: assert 'destinoDeOrigen(' in '...'
tests\test_f026_front.py:318: AssertionError: el texto sigue diciendo que la tanda son
    los verdes, y ya no lo es
7 failed, 10 passed in 0.08s
```

## 25 · Ficheros tocados en el bloque 4

**Creados**

| Ruta | Qué es |
|---|---|
| `services/postventa-front/tests_js/aprobacion.test.js` | 38 tests: aprobable, circulable, el cuarto semáforo, el cuerpo de aprobar y la propagación |
| `services/postventa-front/tests/test_f026_front.py` | 17 tests de texto sobre `index.html`, `js/app.js` y `js/api.js` |

**Modificados**

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/pipeline.js` | `MOTIVOS_APROBABLES`, `esAprobable`, `esCirculable`, `cuerpoDeAprobacion`, `semaforoDe` con aprobación; los cuatro puntos del circuito pasan por `esCirculable`; `guardarParte` devuelve la `aprobacion` |
| `services/postventa-front/js/api.js` | `aprobar(cuerpo, hash)` |
| `services/postventa-front/js/app.js` | `aprobarParte()`, `esAprobable()`, `estaAprobado()`, `destinoDeOrigen()`, `fechaDeAprobacion()`, `mensajeAprobacion`, `aprobacion` en `_parteInicial`, el semáforo con aprobación |
| `services/postventa-front/index.html` | El botón en el detalle, la marca con anillo, el texto de R36/R37, la frase de R39 y el contador de la tanda |
| `services/postventa-front/tests_js/api.test.js` | La lista de endpoints pasa de once a doce, y dos tests propios de `aprobar` |
| `specs/F-026-aprobacion-humana/tasks.md` | T13–T16 marcadas `[x]` |

**Ni un fichero del backend.** Ninguna conexión a base de datos, ninguna
llamada a Azure, a Sigrid ni a SharePoint: la guardia `sin_red` de
`tests/conftest.py` sigue puesta durante toda la suite del front, y los tests
de JavaScript solo hablan con dobles inyectados.

## 26 · Lo que queda fuera y lo que falta

### Fuera del alcance de esta tanda (por encargo explícito)

- **Bloque 4 bis (TA1–TA5)** · el autoguardado de las correcciones (R50–R55).
  Hoy sigue haciendo falta pulsar «Revalidar» para que una corrección se
  guarde, y por tanto para que una aprobación se revoque.
- **Bloque 5 (T17–T19)** · la enmienda a R36 de F-025, los tres puntos de
  `docs/ARCHITECTURE.md` y `azure-apps/postventa_incidencias.md`. **El endpoint
  nuevo y la tabla nueva siguen sin documentar fuera de la spec.**
- **Bloque 7 (T24)** · la campaña de mutación, que el encargo reserva al líder.

### Pendiente y **MANUAL (humano)** · bloque 6

Nada de lo de esta tanda se ha visto en un navegador: los tests de pantalla son
**de texto**, que es lo que esta suite puede hacer. Quedan en pie T20–T23, y a
ellos se añade lo propio del bloque 4, que solo puede comprobar una persona:

- que el botón aparece donde se espera y **solo** en los partes aprobables;
- que la marca con anillo se distingue del verde liso **de un vistazo**, que es
  literalmente lo que pide R36;
- que tras aprobar, el parte aparece en la cuenta de la tanda;
- y que tras corregir un campo y revalidar, la marca **desaparece** (R31).

### Un aviso para quien siga

`esCirculable` es ahora la puerta de la tanda en el front. Cualquier cosa que
vuelva a preguntar por `esArchivable` para decidir **si algo se archiva, se
adjunta o se cierra** deshace F-026 sin romper ningún test de F-007: la
distinción está probada en `tests_js/aprobacion.test.js`, pero quien escriba un
selector nuevo tiene que saber cuál de las dos preguntas está haciendo.

## 27 · Evidencias del bloque 4

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** (servicio `front`) | **205 pasan**, 0 fallan, en **3,74 s** (eran 188 antes de esta tanda: +17 del fichero nuevo) |
| **Tests ejecutados** (JavaScript, `node --test tests_js/*.test.js`) | **271 pasan**, 0 fallan, en **0,63 s** (eran 231: +38 de `aprobacion.test.js` y +2 en `api.test.js`) |
| **Tests ejecutados** (servicio `api`) | **2 317 pasan, 13 se saltan**, 0 fallan · sin cambios: esta tanda no tocó el backend (el arnés los sirvió de su caché, árbol sin cambios) |
| **Tests ejecutados** (raíz) | **62 pasan** en 5,89 s |
| **Tests nuevos de esta tanda** | **57** — 38 en `tests_js/aprobacion.test.js`, 17 en `tests/test_f026_front.py` y 2 en `tests_js/api.test.js` |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1 325 de 1 338 líneas, umbral 80 %, nivel `estandar` → `[OK]`. **El número no se mueve respecto al bloque 3, y es correcto que no se mueva**: `coverage` mide Python y esta tanda solo ha cambiado JavaScript y HTML. Lo que cubre al front es su propia suite, que no entra en esa puerta |
| **Tiempo de la suite** (`front`, dentro de `init.sh`) | **3,74 s** |
| **Avisos de `ruff`** | **60**, los mismos de la tanda anterior. Esta tanda no ha tocado Python de producción |
| **`bash harness/init.sh`** | **ENTORNO LISTO** (exit 0) |
| **Mutantes generados y supervivientes** | **ninguna campaña en esta tanda**, por instrucción explícita del encargo: T24 la lleva el líder al cerrar. Y hay que anotar una limitación del arnés que afecta a este bloque entero: **`harness/mutacion` muta Python**, así que `js/` e `index.html` **no son mutables** con el utillaje de este repositorio. Lo que sostiene la calidad de esta tanda son los **control-negativo**: que `esArchivable` conserve su significado, que el no apto sin aprobación siga fuera de la tanda, que solo se arme una confirmación y que la pantalla no pinte el `oid` |

---

# Parte IV · Bloque 4 bis · el autoguardado de las correcciones (TA1–TA5)

> La escribe el implementer del **bloque 4 bis** (2026-09-12), el mismo día que
> las partes I a III. Encargo corto y explícito: **solo** TA1–TA5, sin tocar el
> bloque 5 ni lanzar la campaña de mutación.

## 28 · Qué se ha hecho, y qué problema cierra

Lo que pidió el responsable, en sus palabras: «escribir en un campo debe
guardar lo que escribes, según escribe guarda, sin botón». Hasta hoy
`editarCampo` dejaba la corrección **solo en memoria** (`parte.ediciones`) y
quien escribía y se iba la perdía; persistir existía, pero solo si alguien
pulsaba «Revalidar».

Y hay una consecuencia que va más allá de perder una línea de texto: **la
revocación de una aprobación ocurre en la escritura** (F-026 D-F). Mientras
corregir un campo no escribiera en la base, un parte podía quedarse con una
aprobación viva sobre un veredicto que ya no era el suyo hasta que alguien
pulsara el botón.

| Tarea | Commit | Qué entra |
|---|---|---|
| TA1 | `428842c` | `RETARDO_AUTOGUARDADO_MS` en `config.js`, `js/autoguardado.js`, `valoresDeCampos` en `pipeline.js` y el disparador en `app.js::editarCampo` |
| TA2 | `7beaa0b` | El guardado pasa por `revalidarYGuardar`, con su control negativo |
| TA3 | `ebfb2ae` | Los tres estados de R52 en `index.html` |
| TA4 + TA5 | `1259c39` | La corrección no pisa lo de la IA (R53); una revocación por pausa (R54); todos los partes (R55) |

## 29 · Las cinco decisiones que fijaba el encargo, y dónde están

### 29.1 · El retardo vive en la configuración (R51)

`js/config.js` gana `RETARDO_AUTOGUARDADO_MS: 1500`, con la razón del número
escrita **encima del valor**, como ya la lleva `TIMEOUT_PETICION_MS`: lo que se
dispara son **dos** peticiones y la segunda escribe en un PostgreSQL
**compartido con otros dos proyectos en producción**.

Que esté en un solo sitio no es una intención, es un test:
`test_f026_r51_el_numero_del_retardo_no_esta_repartido_por_el_codigo` busca el
literal en `app.js` y en `autoguardado.js` y falla si aparece. Y
`test_f026_r51_app_js_no_monta_su_propio_temporizador` prohíbe un `setTimeout`
en `app.js`, que es donde habría acabado el rebote si nadie mirara.

**Y solo se guarda si el valor cambió.** El módulo guarda una foto de lo último
guardado por parte y compara **normalizado** —mismo criterio que
`pipeline.js::normalizarValor`—, así que un espacio de sobra al final no es un
cambio, y escribir una letra y borrarla tampoco. Sin esa comparación, abrir un
parte y tocar un campo para volver a dejarlo igual escribiría en la base.

### 29.2 · Los tres estados, y el que importa es el tercero (R52)

`index.html`, dentro del detalle y justo debajo de «Revalidar»:

| Estado | Cómo se pinta |
|---|---|
| Guardando | gris pequeño, sin interrumpir a nadie |
| Guardado | verde pequeño, misma línea |
| **No se ha podido guardar** | **recuadro rojo, aparte**, con el texto entero |

El de fallo **no se va solo**: no hay temporizador que lo borre ni
`x-transition` que lo esconda, y lo quita el **siguiente guardado que salga
bien**. Hay un test para cada mitad de esa frase —uno sobre el HTML y otro
sobre el módulo, que comprueba que tras el fallo **no se programó ningún
temporizador más allá del rebote**—.

Y lo escrito se conserva: el `input` sigue atado a `valorDe(nombre)`, que
devuelve la corrección antes que la extracción, y **nada** borra
`parte.ediciones`. El módulo tampoco lo toca al fallar: lo pendiente **sigue
pendiente**, así que la siguiente pausa lo reintenta sola.

Detalle que sin querer se pasa por alto: `pipeline.js::guardarParte` **no
lanza** cuando el backend rechaza —devuelve `{ok: false, motivo}` para no tirar
un veredicto ya pagado—. Si `_guardarCorreccion` se hubiera quedado ahí, la
pantalla habría dicho «Guardado.» con la base sin tocar. Por eso convierte ese
`ok: false` en un error, que es lo que enciende el estado de fallo.

### 29.3 · Las correcciones no pisan lo que leyó la máquina (R53)

No hacía falta cambiar nada para conseguirlo —`aplicarEdiciones` ya devuelve la
extracción corregida **sin destruir el original**—, y justamente por eso hacía
falta **fijarlo**: lo que hoy es cierto por construcción deja de serlo el día
que alguien «simplifique» escribiendo la corrección dentro de
`extraccion.campos`.

Dos tests, y los dos citan el motivo con nombre: **F-015**. Evaluar el prompt
exige comparar lo que dijo el modelo con lo que resultó ser verdad, y un prompt
no se puede evaluar contra un dato que una persona corrigió encima.

### 29.4 · La revocación no ocurre a mitad de palabra (R54)

La revocación se ejecuta en la escritura, así que **contar escrituras es contar
revocaciones posibles**. El test lo dice en esos términos: cinco pulsaciones →
una sola llamada a `/api/parte`. Y otro comprueba que lo que se revalida es lo
escrito **hasta la pausa** («cliente») y no un trozo intermedio («clie»), que
produciría la huella de un veredicto que nadie quiso.

La otra mitad es que la revocación **se vea**: `_guardarCorreccion` anota la
respuesta con el mismo `_anotarGuardado` que el botón, y esa respuesta trae la
aprobación al día (R22, R31). Sin eso, la pantalla seguiría diciendo «Aprobado»
sobre una aprobación ya revocada en la base.

### 29.5 · Aplica a todos los partes (R55)

El módulo **no recibe** la validación: no tiene forma de discriminar. Y hay
tres control-negativo que lo sostienen: `editarCampo` no nombra
`validacion`/`semaforo`/`veredicto`/`destino`; el indicador del HTML tampoco; y
un test guarda un parte **verde** y comprueba que se guarda igual.

## 30 · Decisiones de diseño que conviene mirar al revisar

### 30.1 · El rebote vive en un módulo propio, no en `app.js`

`js/app.js` es **la única habitación de la casa sin tests** (`design.md` §3), y
la regla del proyecto es que si algo merece un test no vive ahí. El rebote lo
merece: la diferencia entre «cinco teclas, un guardado» y «cinco teclas, cinco
guardados» solo se ve mirando la carga de una base compartida.

Así que `js/autoguardado.js` sigue el patrón de `js/confirmacion.js`: lógica
pura, sin DOM, sin Alpine y **sin reloj propio** —el temporizador entra por
parámetro—. Sin eso, probar «una pausa» costaría 1,5 s de espera real por test
y nadie los escribiría.

### 30.2 · El módulo se monta en el cierre, no en el estado de Alpine

`let autoguardado = null` vive en el cierre de `appPostventa()` y se monta la
primera vez que alguien escribe (`_autoguardado()`). Dos motivos: sus dos
funciones —guardar y pintar— son **métodos del objeto**, así que montarlo antes
del `return` obligaría a atarlas a mano; y no es un dato que se pinte, así que
meterlo en el estado solo añadiría un proxy reactivo alrededor de un objeto con
closures.

Lo que **sí** está declarado en el estado, y nace declarado a propósito, es
`estadoAutoguardado` y `mensajeAutoguardado`: añadirlos a mitad de sesión no
los haría reactivos y el aviso no repintaría, que es el defecto que F-025
documentó con `paso` y F-026 repitió con `aprobacion`.

### 30.3 · Cambiar de parte con una corrección a medias **la guarda**

Si la pausa del parte A se cancelara al abrir el B, lo escrito en A se perdería
en silencio: exactamente el defecto que esta feature viene a cerrar, pero por
otra puerta. El módulo dispara el guardado pendiente del parte anterior antes
de programar el nuevo, y hay un test.

### 30.4 · Dos guardados no se pisan

Si la pausa se cumple con un guardado todavía en el aire, el módulo **vuelve a
esperar** en vez de lanzar otro encima. Dos escrituras en carrera dejarían en
la base el veredicto de la que ganara, que puede no ser la última.

### 30.5 · La foto de «lo guardado» tiene dos fuentes que dicen lo mismo

El módulo mueve lo pendiente a lo guardado cuando la promesa sale bien, y
`app.js::_anotarGuardado` la vuelve a fijar con `valoresDeCampos(parte)`. Es
deliberado: la primera lo hace autónomo y testeable; la segunda es la
autoritativa y cubre **los tres** sitios donde un parte se guarda —al
procesarlo, al revalidarlo a mano y al autoguardarlo—. Sin la segunda, la
primera pulsación de cada parte guardaría aunque no cambiara nada.

## 31 · Fase RED · la traza real

### TA1 · el módulo no existía

```
$ node --test tests_js/autoguardado.test.js
Error: Cannot find module '../js/autoguardado.js'
Require stack:
- C:\...\services\postventa-front\tests_js\autoguardado.test.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1456:15)
  code: 'MODULE_NOT_FOUND',
✖ tests_js\autoguardado.test.js (155.6424ms)
ℹ tests 1
ℹ pass 0
ℹ fail 1
```

```
$ python -m pytest tests/test_f026_autoguardado.py -q -p no:cacheprovider
FAILED tests/test_f026_autoguardado.py::test_f026_r51_el_retardo_se_declara_en_config_js
FAILED tests/test_f026_autoguardado.py::test_f026_r51_el_porque_del_retardo_esta_escrito_al_lado
FAILED tests/test_f026_autoguardado.py::test_f026_r51_app_js_lee_el_retardo_de_la_configuracion
FAILED tests/test_f026_autoguardado.py::test_f026_r51_editar_un_campo_dispara_el_autoguardado
FAILED tests/test_f026_autoguardado.py::test_f026_r51_el_modulo_se_carga_antes_que_app_js
FAILED tests/test_f026_autoguardado.py::test_f026_r51_al_reiniciar_no_queda_ningun_guardado_en_vuelo
ERROR tests/test_f026_autoguardado.py::test_f026_r51_el_numero_del_retardo_no_esta_repartido_por_el_codigo
6 failed, 2 passed, 1 error in 0.25s
```

El `ERROR` es el mismo motivo que los seis fallos: ese test lee
`js/autoguardado.js`, que todavía no existía.

### TA3 · los tres estados no estaban en la pantalla

```
$ python -m pytest tests/test_f026_autoguardado.py -q
E       ValueError: substring not found
FAILED tests/test_f026_autoguardado.py::test_f026_r52_los_tres_estados_estan_en_la_pantalla
FAILED tests/test_f026_autoguardado.py::test_f026_r52_el_aviso_de_fallo_se_ve_y_no_se_confunde_con_los_otros_dos
FAILED tests/test_f026_autoguardado.py::test_f026_r52_nada_borra_el_aviso_por_su_cuenta
3 failed, 13 passed in 0.19s
```

### TA2, TA4 y TA5 · **no hubo fase RED, y se dice**

Sus tests nacieron **en verde**, y es lo que tenía que pasar:

- **TA2** fija el acoplamiento «revalidar y guardar juntos», que TA1 ya dejó
  cableado al montar el disparador —y que existe desde F-019 R28—. Lo que
  aportan sus tests es la **red que impide deshacerlo**: que nunca se llame a
  `guardarParte` sin `revalidar`, y que no aparezca un estado de «veredicto
  obsoleto», que es la alternativa que `design.md` §15.1 descartó.
- **TA4** y **TA5** son **control-negativo**: fijan lo que **no** puede
  aparecer. Un control negativo no puede fallar antes de existir el código
  porque lo que vigila es que algo siga sin estar.

No se ha inventado un rojo artificial para rellenar el hueco. Lo que sostiene
la fase RED de este bloque son TA1 y TA3, que es donde había código nuevo que
escribir.

### Un test que pasaba sin comprobar nada · se cuenta porque casi cuela

Al escribir el control negativo de R55 se coló un `\b` mal escapado que acabó
siendo un **carácter de retroceso literal** (`0x08`) dentro del patrón, en vez
del límite de palabra. El regex quedó en `\x08validacion\x08`, que no puede
casar nunca: el test **pasaba sin comprobar nada**, y en el fichero se veía
idéntico a uno correcto. Se detectó porque el test pasó cuando tenía que estar
fallando, se miró con `cat -A` y ahí salió el `^H`. Corregido en el mismo
commit (`428842c`), y el test hoy falla si `editarCampo` mira el veredicto.

## 32 · Ficheros tocados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/autoguardado.js` | **Nuevo.** El rebote, la comparación con lo guardado y los tres estados |
| `services/postventa-front/js/config.js` | `RETARDO_AUTOGUARDADO_MS: 1500` con su porqué |
| `services/postventa-front/js/pipeline.js` | `valoresDeCampos(parte)`, exportada |
| `services/postventa-front/js/app.js` | El cierre `autoguardado`, `_autoguardado()`, `_guardarCorreccion()`, `_pintarAutoguardado()`, el disparo en `editarCampo`, la foto en `_anotarGuardado`, la cancelación en `reiniciar` y los dos campos reactivos |
| `services/postventa-front/index.html` | El `<script>` del módulo y el bloque de los tres estados |
| `services/postventa-front/tests_js/autoguardado.test.js` | **Nuevo.** 21 tests |
| `services/postventa-front/tests/test_f026_autoguardado.py` | **Nuevo.** 19 tests |
| `services/postventa-front/tests/test_f007_estaticos.py` | `js/autoguardado.js` en el orden canónico de carga |
| `specs/F-026-aprobacion-humana/tasks.md` | TA1–TA5 marcadas `[x]` |

**Ni un fichero del backend, ni una dependencia nueva.** Ninguna conexión a
base de datos, a Azure, a Sigrid ni a SharePoint: la guardia `sin_red` de
`tests/conftest.py` sigue puesta durante toda la suite y los tests de
JavaScript solo hablan con dobles inyectados.

## 33 · Lo que queda fuera y lo que falta

### Fuera del alcance de esta tanda (por encargo explícito)

- **Bloque 5 (T17–T19)** · la enmienda a R36 de F-025, los tres puntos de
  `docs/ARCHITECTURE.md` y `azure-apps/postventa_incidencias.md`. Sigue sin
  hacer, y el endpoint y la tabla nuevos siguen sin documentar fuera de la spec.
- **Bloque 7 (T24)** · la campaña de mutación.

### Pendiente y **MANUAL (humano)**

Nada de esto se ha visto en un navegador; los tests de pantalla son **de
texto**, que es lo que esta suite puede hacer. Lo que solo puede comprobar una
persona, y conviene añadir al bloque 6:

- que al escribir en un campo y **parar**, aparece «Guardando…» y luego
  «Guardado.» **sin pulsar nada**;
- que al escribir con el backend caído sale el **recuadro rojo**, que **no se
  va solo**, y que lo escrito **sigue en el campo**;
- que al volver el backend, escribir una letra más lo guarda y el recuadro
  desaparece;
- y que corregir un campo de un parte **aprobado** revoca la aprobación sola,
  sin pulsar «Revalidar» (es T23 del bloque 6, que ahora se puede hacer sin
  botón).

### Un aviso para quien siga

El autoguardado dispara **dos** peticiones por pausa contra un PostgreSQL
compartido. Si alguien añade campos a la pantalla, o baja
`RETARDO_AUTOGUARDADO_MS`, lo que cambia es la carga sobre una base que no es
solo nuestra. El número tiene su razón escrita al lado; conviene leerla antes
de tocarlo.

## 34 · Evidencias del bloque 4 bis

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** (servicio `front`, dentro de `init.sh`) | **224 pasan**, 0 fallan, en **4,76 s** (eran 205 al cerrar el bloque 4: **+19**) |
| **Tests ejecutados** (JavaScript, `node --test tests_js/*.test.js`) | **292 pasan**, 0 fallan, en **1,28 s** (eran 271: **+21**, todos en `tests_js/autoguardado.test.js`) |
| **Tests ejecutados** (raíz) | **62 pasan** en **7,73 s** |
| **Tests ejecutados** (servicio `api`) | sin cambios; el arnés los sirvió de su caché (árbol del backend sin tocar) |
| **Tests nuevos de esta tanda** | **40** — 21 en `tests_js/autoguardado.test.js` y 19 en `tests/test_f026_autoguardado.py` |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1 325 de 1 338, umbral 80 %, nivel `estandar` → `[OK]`. **No se mueve respecto al bloque 4, y es correcto que no se mueva**: `coverage` mide Python y esta tanda solo ha cambiado JavaScript y HTML. Al front lo cubre su propia suite, que no entra en esa puerta |
| **Tiempo de la suite** | `front` **4,76 s** · raíz **7,73 s** · JavaScript **1,28 s** |
| **Avisos de `ruff`** | **60**, los mismos. Esta tanda no ha tocado Python de producción |
| **`bash harness/init.sh`** | **ENTORNO LISTO** (exit 0) |
| **Mutantes generados y supervivientes** | **campaña no lanzada**, por instrucción explícita del encargo (T24 es del bloque 7). Y, como en el bloque 4, hay que anotar la limitación: **`harness/mutacion` muta Python**, así que `js/autoguardado.js`, `js/app.js` e `index.html` **no son mutables** con el utillaje de este repositorio. Lo que sostiene la calidad de esta tanda son los tests de comportamiento del módulo —con reloj inyectado, que es lo que permite probar el rebote— y los control-negativo sobre `app.js` y el HTML |

---

# Parte V · Bloque 5 · las enmiendas y la documentación (T17–T19)

> La escribe el implementer del **bloque 5**, el **2026-09-12**, con el encargo
> acotado a ese bloque y con instrucción explícita de **no** hacer el bloque 6
> (verificación contra la base real, que es del responsable), **ni** el 7
> (cierre, que lleva el líder), **ni** la campaña de mutación.

## 35 · Qué se ha hecho, y qué problema cierra

Tres documentos aprobados decían —y hasta hoy seguían diciendo— lo contrario de
lo que hace F-026: que un parte que la validación no declara `apto` **no se
archiva, no se adjunta y no se cierra, y punto**. Es verdad que la feature
existe precisamente para abrir esa puerta; lo que no puede pasar es que la abra
**en el código y no en los documentos**, porque entonces el próximo que lea
`ARCHITECTURE.md` encontrará `_exigir_admitido` y creerá que es un agujero que
alguien coló.

La regla del proyecto para esto está fijada desde R28 de F-010 (2026-09-03) y
la volvió a aplicar F-025 el 2026-09-11: **lo que se deroga no se borra**. Se
enmienda con un recuadro fechado que cita la premisa original **literal**, dice
qué la invalidó, quién lo decidió y cuándo.

| Tarea | Qué documento | Commit |
|---|---|---|
| **T17** | el recuadro bajo **R36 de F-025**, con su test de documentación | `b7ac982` |
| **T18** | los **tres** puntos de `docs/ARCHITECTURE.md` | `c9258f0` |
| **T19** | `docs/INTEGRACION.md` (fuente de verdad) | `02cb101` |
| **T19** | `azure-apps/postventa_incidencias.md` (**otro repositorio**) | `0d7c843` en `azure-apps` |
| — | la cuenta de endpoints en los dos tests ajenos que la vigilan | `212ba40` |

Ni una línea de código de producción. Lo único ejecutable que se ha escrito es
`services/postventa-api/tests/test_f026_documentacion.py`, que es lo que hace
que estas enmiendas **sobrevivan a la siguiente edición**: una revisión se
olvida, un test no.

## 36 · T17 · el recuadro bajo R36 de F-025

R36 decía, y sigue diciendo palabra por palabra:

> «El sistema **no debe** archivar, adjuntar ni cerrar un parte que no sea
> `apto` con destino `archivo_y_cierre`, ni siquiera dentro de la tanda y ni
> siquiera si el usuario pulsa dos veces. Los partes en revisión y los de la
> cola humana **siguen fuera** (aprobarlos es **F-026**).»

Debajo, sin tocar una coma de ese texto, hay ahora un recuadro fechado el
**2026-09-12** que dice seis cosas, y las seis tienen su test:

1. **Cae solo la última frase**, y el propio requisito la anunciaba. Lo demás
   sigue rigiendo. Es la confusión que más daño haría —«R36 está enmendado»
   leído como «R36 ya no rige»— y por eso está escrita la primera.
2. **Un no apto entra si y solo si consta aprobado y vigente** en
   `postventa.aprobaciones`, con revocación automática cuando cambia el
   veredicto (R30).
3. **La comprobación sigue donde estaba**: en los tres pasos del backend.
   `_exigir_apto` pasa a `_exigir_admitido`, nada más.
4. **La aprobación se lee del repositorio, nunca del cuerpo de la petición.**
   Sin esa frase, alguien puede «simplificar» el handler aceptando un
   `aprobado: true` de fuera, y entonces la puerta la abre cualquiera que sepa
   escribir JSON.
5. **Quién lo decidió, cuándo y con qué palabras**: el responsable, el
   2026-09-11, con las tres citas literales (los no aptos no se archivan hasta
   que los apruebe un revisor humano; «hay que guardarlo»; «no hace falta que
   conste en Sigrid, sí en nuestra base»).
6. **F-025 sigue `done`**, y su confirmación única sigue siendo una, porque R29
   de F-026 prohíbe armar ninguna confirmación nueva.

### 36.1 · Lo que se ha tenido cuidado de **no** atribuir al responsable

El recuadro separa, con su propio párrafo, que **el botón de aprobar es
interpretación del líder y no un pronunciamiento del responsable**. Importa
porque en la misma respuesta el responsable pidió justo lo contrario, pero para
otra cosa: *«escribir en un campo debe guardar lo que escribes, según escribe
guarda, sin botón»* —que es el bloque 4 bis—. Las dos conviven porque son
juicios distintos: guardar lo que alguien teclea es registrar un dato;
declarar que una firma dudosa vale es una decisión que necesita saber **quién**
la tomó. Solo la segunda lleva botón y `oid`.

Dicho de otra forma: quien mañana quiera quitar ese botón tiene derecho a saber
que discute con una interpretación y no con el responsable. Eso lo fija
`test_f026_r46_el_recuadro_de_r36_separa_la_interpretacion_del_lider`.

## 37 · T18 · los tres puntos de `docs/ARCHITECTURE.md`

Los tres que nombra R47, con la fórmula que pide el requisito —**precisión, no
borrado**— y los tres con la misma remisión:

| Punto | Decía | Ahora dice, además |
|---|---|---|
| **paso 6** del pipeline | «Solo se archiva lo que el paso 4 declaró apto» | … **salvo aprobación humana registrada**, con el caso de los dos destinos no aptos y la advertencia de que un código de obra o un número de incidencia ilegibles **no se aprueban, se teclean** |
| **semántica 3** | «Un parte sin firma válida no se archiva ni se cierra: va a revisión manual» | … de revisión manual **ya se sale**, pero solo por ahí; el criterio de qué es una firma no cambia, cambia **quién** puede darla por buena |
| **semántica 7** | «Nada se archiva ni se cierra si no ha pasado todas las validaciones» | … la aprobación es lo único que sustituye a una validación en verde, y **no se escribe en Sigrid**: quien audite cruza `aprobaciones` con `cierres` por `hash_parte` |

Los tres repiten, porque los tres se leen por separado, la frase que impide
leer la enmienda como una barra libre: es una puerta **más estrecha** que la
que abría el veredicto —una persona identificada, un parte concreto, un motivo
aprobable y un registro con quién y cuándo—, **nunca automática**, y revocada
en cuanto cambia el veredicto.

Y hay **dos controles negativos** sobre esto, que es lo que la verificación de
T18 pedía con todas las letras («los tres puntos siguen diciendo lo que decían
para todo lo demás»):

- el **literal original** de cada uno sigue en su sitio
  (`test_f026_r47_los_tres_puntos_conservan_su_texto`);
- y el **motivo** de cada uno también —que con otro destino no se sube nada,
  que solo firma el cliente, que archivar basura ensucia el archivo de
  Posventa—
  (`test_f026_r47_la_precision_no_se_ha_llevado_por_delante_el_resto`). Un punto
  al que se le añade la excepción y se le quita el razonamiento queda
  convertido en una regla arbitraria, y las reglas arbitrarias se borran en la
  siguiente limpieza.

## 38 · T19 · los dos documentos de integración, en dos repositorios

**Aquí hubo una decisión que conviene mirar.** La tarea dice «actualizar
`azure-apps/postventa_incidencias.md`», y ese fichero declara en su propia
cabecera que es una **copia** de `docs/INTEGRACION.md`, que es la fuente de
verdad, y que **no se edita allí: se edita aquí y se refresca la copia**. Tocar
solo la copia habría dejado el documento del ecosistema diciendo algo que en
este repositorio no está escrito, que es exactamente la divergencia que la
regla existe para evitar. Así que se han tocado **los dos**, con el mismo
contenido, y en **dos commits**, uno por repositorio:

| Dónde | Qué se escribió |
|---|---|
| §2, el árbol del esquema | `aprobaciones`, con un párrafo propio: qué registra, qué guarda (`oid`, destino, **códigos** de motivo, huella `sha256`), qué **no** guarda (ni texto manuscrito, ni binarios) y que revocar **no borra** |
| §8, la tabla de endpoints | `POST /api/aprobar`, con lo que escribe, que **no toca ningún sistema ajeno** y que en Sigrid no consta |
| §8, la cuenta | «los once» pasan a **«los doce»** |
| §8, las ventanas | que aprobar **no mira** `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO`, y que para que un no apto llegue al ERP hacen falta **las dos cosas**: la aprobación y la ventana abierta |
| §7, datos personales | el `oid` de quien aprueba, y por qué se guarda: **no es traza de un proceso, es la firma de una decisión** que contradice a la máquina |
| cabecera de la copia | qué cambia para el ecosistema —**nada de lo que consumimos**— y el único aviso que sí le importa a quien audite Sigrid |

`git -C ../azure-apps status` queda **limpio** y **sin `push`**, como manda el
encargo. El commit allí es `0d7c843`.

### 38.1 · Deuda ajena corregida al pasar, y se declara

El árbol de tablas de §2 listaba **seis** de las **nueve** que crea el DDL:
faltaban `usuarios_sigrid` (F-009) y `graficos` (F-012). Se han añadido junto
con `aprobaciones`, porque el bloque que había que editar era ese y un
inventario de tablas al que le faltan dos es peor que no tenerlo. Queda
declarado aquí y en la nota bajo R49 de la spec para que el reviewer no tenga
que averiguar de dónde salen esas dos líneas.

### 38.2 · Lo que **no** se ha tocado, y por qué

F-026 **no cambia nada de lo que consumimos**: ni un recurso nuevo, ni una
variable de entorno (R45 lo prohíbe explícitamente), ni una llamada nueva a
`sigrid-api`, a Graph o al servidor compartido. La única frontera que cruza
este bloque es documental. Por eso §1 («Qué consumimos hoy»), §3, §3 bis, §4 y
§5 de los dos documentos quedan **intactos**.

## 39 · Dos tests ajenos que se pusieron en rojo, y qué se hizo con cada uno

El endpoint nuevo rompió dos tests de documentación de otras features, y los
dos hicieron **exactamente** lo que venían a hacer: avisar de que el documento
que viaja a `azure-apps/` se había quedado atrás. Vale la pena contarlo porque
la reacción por defecto ante un test ajeno en rojo es aflojarlo.

- **`test_f019_documentacion.py`** · su docstring declara que la cuenta se
  escribe **a mano a propósito**, para que un endpoint nuevo tenga que pasar
  por ahí. Se ha respetado: pasa de «once» a «doce», y «once» se suma a la
  lista de cifras prohibidas junto a seis, nueve y diez.
- **`test_f012_documentacion.py`** · ese fijaba el literal «Los once quedan en
  nivel» sin comprobar nada más, así que la única forma de arreglarlo era
  teclear otro número —**que podía volver a ser falso**—. Ahora **cuenta** las
  filas de la tabla de endpoints de §8 y exige que el párrafo diga ese número.
  Sigue siendo un test de F-012 y sigue exigiendo lo que exigía; lo que gana es
  que el siguiente endpoint tampoco podrá colarse con una cifra inventada.

Los dos se quedan, y no se pisan: **uno obliga a pasar por el test, el otro
comprueba que lo que se escribió es cierto.**

## 40 · Fase RED · la traza real

El test se escribió **antes** que los tres documentos, y esta es la salida del
comando exacto que se lanzó, con el árbol todavía sin ninguna enmienda:

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f026_documentacion.py -q

FFFFFFF....FFFFFFF...                                                    [100%]
================================== FAILURES ===================================
_____ test_f026_r46_bajo_r36_de_f025_hay_un_recuadro_de_enmienda_fechado ______
>       assert "Enmienda" in bloque
E       AssertionError: assert 'Enmienda' in '**R36.** El sistema **no debe** archivar, adjuntar ni cerrar un parte que no sea `apto` con destino `archivo_y_cierre...el usuario pulsa dos veces. Los partes en revisión y los de la cola humana **siguen fuera** (aprobarlos es **F-026**).'
__________ test_f026_r46_el_recuadro_de_r36_cita_la_premisa_literal ___________
>       recuadro = bloque[bloque.index("Enmienda") :]
E       ValueError: substring not found
...
_ test_f026_r47_los_tres_puntos_dicen_que_la_puerta_es_mas_estrecha[semantica-7] _
>       assert "más estrecha" in bloque
E       AssertionError: assert 'más estrecha' in '7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.** Archivar un parte inválido ensucia el archivo de Posventa; cerrarlo en Sigrid da por resuelta una incidencia que sigue viva.'
_____ test_f026_r47_la_semantica_7_dice_que_la_aprobacion_no_va_a_sigrid ______
>       assert "no se escribe en Sigrid" in bloque
E       AssertionError: assert 'no se escribe en Sigrid' in '7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.** Archivar un parte inválido ensucia el archivo de Posventa; cerrarlo en Sigrid da por resuelta una incidencia que sigue viva.'
=========================== short test summary info ===========================
FAILED tests/test_f026_documentacion.py::test_f026_r46_bajo_r36_de_f025_hay_un_recuadro_de_enmienda_fechado
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_cita_la_premisa_literal
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_dice_que_solo_cae_la_ultima_frase
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_dice_que_la_aprobacion_no_viene_del_cuerpo
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_dice_quien_lo_decidio_y_con_que_palabras
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_separa_la_interpretacion_del_lider
FAILED tests/test_f026_documentacion.py::test_f026_r46_el_recuadro_de_r36_dice_que_f025_sigue_done
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_nombran_la_aprobacion_humana[paso-6-del-pipeline]
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_nombran_la_aprobacion_humana[semantica-3]
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_nombran_la_aprobacion_humana[semantica-7]
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_dicen_que_la_puerta_es_mas_estrecha[paso-6-del-pipeline]
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_dicen_que_la_puerta_es_mas_estrecha[semantica-3]
FAILED tests/test_f026_documentacion.py::test_f026_r47_los_tres_puntos_dicen_que_la_puerta_es_mas_estrecha[semantica-7]
FAILED tests/test_f026_documentacion.py::test_f026_r47_la_semantica_7_dice_que_la_aprobacion_no_va_a_sigrid
14 failed, 7 passed in 0.51s
```

**Los 7 verdes de ese rojo importan tanto como los 14 rojos**, y son
deliberados: son los **control-negativo** —que el texto original de R36 sigue
ahí, que los tres literales de `ARCHITECTURE.md` siguen ahí y que su
razonamiento sigue ahí—. Tenían que estar en verde **antes** y seguir en verde
**después**; si alguno hubiera salido rojo en esta foto, el test estaría
buscando un texto que no existe y no probaría nada.

Después de escribir los tres documentos, el mismo comando da **21 verdes**.

### 40.1 · Un rojo intermedio que conviene contar

Al precisar la semántica 7, la frase quedó como «…, **nunca es automática**, y
caduca sola…» y el test —que busca `Nunca es automática`— siguió en rojo por la
mayúscula. Se arregló **en el documento, no en el test**: la afirmación se
partió en su propia frase. Es la decisión correcta de las dos posibles, pero
merece constar, porque la otra —relajar el test a comparar sin mayúsculas—
habría dejado pasar también un «nunca es automática» escondido en mitad de una
subordinada, que es justo lo que no se quiere.

## 41 · Ficheros tocados en el bloque 5

| Fichero | Qué | Repositorio |
|---|---|---|
| `services/postventa-api/tests/test_f026_documentacion.py` | **nuevo** · 21 tests: 8 de R46 y 13 de R47 | este |
| `specs/F-025-confirmacion-unica/requirements.md` | +47 · el recuadro bajo R36, sin tocar su texto | este |
| `docs/ARCHITECTURE.md` | +37 · los tres puntos precisados | este |
| `docs/INTEGRACION.md` | +48/−7 · árbol, endpoint, cuenta, ventanas, datos personales, cabecera | este |
| `specs/F-026-aprobacion-humana/requirements.md` | +21 · la nota bajo R49 con lo hecho y dónde | este |
| `specs/F-026-aprobacion-humana/tasks.md` | T17–T19 marcadas | este |
| `services/postventa-api/tests/test_f012_documentacion.py` | la cuenta pasa a calcularse | este |
| `services/postventa-api/tests/test_f019_documentacion.py` | la cuenta a mano pasa a doce | este |
| `postventa_incidencias.md` | +63/−6 · el mismo contenido, más su cabecera propia | **`azure-apps`** |

**Ningún fichero de producción.** El diff de `services/postventa-api` fuera de
`tests/` está vacío, y es comprobable:
`git diff b7ac982~1 HEAD -- services/postventa-api --stat` solo lista ficheros
de `tests/`.

## 42 · Lo que queda fuera y lo que falta

### Fuera del alcance de esta tanda (por encargo explícito)

- **Bloque 6 (T20–T23)** · la verificación contra la base real. Es **MANUAL
  (humano)** y del responsable.
- **Bloque 7 (T24)** · la **campaña de mutación**. El encargo decía
  explícitamente que no se lanzara.
- **Bloque 7 (T25)** · el cierre lo lleva el líder.

### Lo que este bloque **no** demuestra

Que la documentación esté al día **no prueba que el circuito funcione**. Lo que
sigue sin haberse visto nunca contra la base real ni contra un navegador es
todo lo que enumeran §26, §33 y el bloque 6 de `tasks.md`: el DDL aplicado, un
parte aprobado recorriendo el circuito entero, la traza reconstruible hasta el
ERP y la revocación sobre datos reales.

### Un aviso para quien siga

El `oid` **no se copia a `progress/`** cuando se haga el bloque 6: se anota que
existe, no su valor. Está escrito en T22 y se repite aquí porque es el error
fácil de cometer con una consulta delante.

## 43 · Evidencias del bloque 5

| Evidencia | Medida |
|---|---|
| **Tests ejecutados** (servicio `api`) | **2 338 pasan**, 0 fallan, 13 saltados, en **51,8 s** (eran 2 317: **+21**, todos en `tests/test_f026_documentacion.py`) |
| **Tests ejecutados** (raíz) | **62 pasan** en **4,70 s** |
| **Tests ejecutados** (servicio `front`) | sin cambios; el arnés los sirvió de su caché (el árbol del front no se ha tocado) |
| **Tests nuevos de esta tanda** | **21** — 8 de R46 y 13 de R47, once de ellos parametrizados sobre los tres puntos |
| **Tests ajenos tocados** | **2**, los dos de la cuenta de endpoints; **ninguno aflojado**, uno de ellos reforzado (§39) |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1 325 de 1 338, umbral 80 %, nivel `estandar` → `[OK]`. **No se mueve respecto al bloque 4 bis, y es correcto que no se mueva**: esta tanda no ha cambiado ni una línea de Python de producción, que es lo que mide esa puerta |
| **Tiempo de ejecución de la suite** | `api` **51,8 s** en ejecución directa (**98,8 s** dentro de `init.sh`, que la corre con medición de cobertura) · raíz **4,70 s** |
| **Avisos de `ruff`** | **60**, los mismos de siempre. Esta tanda no ha tocado Python de producción |
| **`bash harness/init.sh`** | **ENTORNO LISTO** (exit 0) |
| **Mutantes generados y supervivientes** | **campaña no lanzada**, por instrucción explícita del encargo (T24 es del bloque 7). Y conviene decir qué aportaría si se lanzara **sobre este bloque**: nada. Lo único ejecutable que ha escrito esta tanda son tests, y `harness/mutacion` muta **código de producción**, no tests. Lo que sostiene la calidad de un bloque documental es otra cosa: que el test se escribiera **antes** (§40), que sus control-negativo pasaran antes y después, y que los dos tests ajenos que saltaron se arreglaran **sin aflojarlos** (§39) |
