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
| 4 · La pantalla | T13–T16 | **sin empezar** |
| 4 bis · Autoguardado | TA1–TA5 | **sin empezar** |
| 5 · Enmiendas y documentación | T17–T19 | **sin empezar** |
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
> (T9–T12). Los bloques 4, 4 bis, 5 y 7 **no se han tocado**, y la campaña de
> mutación tampoco: va en el bloque de cierre y la lanza el líder.
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
| **Mutantes generados y supervivientes** | **no se ha lanzado la campaña**, por instrucción explícita del encargo: es T24 y la lleva el líder en el bloque de cierre, sobre la feature entera. No es un `PENDIENTE` sin dueño: es trabajo asignado a otro paso del plan, y `CHECKPOINTS.md` C4 bis sigue exigiéndolo **antes de cerrar F-026** |
