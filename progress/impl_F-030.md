<!-- progress/impl_F-030.md -->
# F-030 · Informe del implementer

> Rama `feature/F-030-veredicto-persistido`. Rigor **`critico`**: fase RED
> obligatoria con traza pegada, puerta de cobertura sobre las líneas cambiadas
> y campaña de mutación con cero supervivientes (T18).
>
> **El encargo va por bloques y este informe crece con ellos.** Cada bloque se
> entrega y se para: lo que hay aquí abajo es lo hecho hasta el bloque
> entregado, no la feature entera.

---

## Bloque 0 · La red de seguridad, en rojo (T1, T2) — **ENTREGADO**

**El bloque termina en ROJO a propósito.** No se ha tocado ni una línea de
producción: lo único que hay es el fichero de tests nuevo que reproduce la
regresión y la deja fijada. El arreglo es de los bloques 1 a 3.

### Ficheros tocados

| Fichero | Qué es |
|---|---|
| `services/postventa-api/tests/test_f030_veredicto_persistido.py` | **Nuevo.** T1 (las dos caras del defecto) y T2 (la ida y vuelta de la huella). |
| `specs/F-030-veredicto-persistido/tasks.md` | T1 y T2 marcadas `[x]`. |
| `progress/impl_F-030.md` | Este informe. |
| `progress/current.md` | Estado del bloque y el hallazgo de entorno de abajo. |

Ni `.env`, ni `infra/`, ni `sql/`, ni `services/postventa-front/`, ni ningún
módulo de producción. **Ninguna llamada a Azure, a Sigrid, a SharePoint ni al
PostgreSQL compartido**: los tests hablan con dobles en memoria y la guardia de
red de `conftest.py` sigue en pie.

### T1 · las dos caras del defecto

**(a) `test_f030_r11_un_parte_no_apto_aprobado_a_mano_pasa_las_tres_puertas`**
—6 casos: tres puertas × dos destinos no aptos—. El veredicto está guardado, la
aprobación de una persona lleva la huella **de ese** veredicto y el cuerpo de la
petición dice la verdad. Las tres puertas tienen que abrirse. Es la incidencia
**RS26.09/0178**.

**(b) `test_f030_r7_un_cuerpo_que_miente_no_pasa_ninguna_de_las_tres_puertas`**
—3 casos—. El parte está guardado como no apto a `revision_manual` y nadie lo ha
decidido; el cuerpo dice `veredicto=apto` y `destino=archivo_y_cierre`. Ninguna
puerta puede abrirse y no puede salir nada a SharePoint ni al ERP (§0.9).

Más un caso que **hoy ya pasa** y que explica por qué falla (a):
`test_f030_r1_la_huella_del_stub_del_cuerpo_no_depende_del_parte`.

### T2 · la ida y vuelta de la huella (R10)

`test_f030_r10_el_veredicto_recompuesto_da_la_misma_huella`, **7 casos**:
motivos en orden inverso, observaciones con saltos de línea y mayúsculas,
observaciones `None` frente a `"   "`, `codigo_obra` con espacio final,
`numero_incidencia` con espacios alrededor del separador, campos decisivos
vacíos guardados como `NULL` y un aviso de más de 240 caracteres.

La fila se arma con **las columnas que produce `mapeo.valores_de_validacion`**
—la misma función que escribe la fila— más las cuatro de `postventa.partes`, en
el orden del `SELECT` de `design.md` §3.

---

## Fase RED · las trazas, tal cual

### T1 · el rojo del defecto

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py -q --tb=line

E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que no se archiva
application/pipelines/puerta_de_estado.py:119: domain.models.errores.ParteNoApto: ... así que no se archiva
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «revision_manual» y no consta que nadie lo haya aprobado, así que no se archiva
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que no se adjunta a la reclamación
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «revision_manual» y no consta que nadie lo haya aprobado, así que no se adjunta a la reclamación
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que no se cierra la incidencia
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda a «revision_manual» y no consta que nadie lo haya aprobado, así que no se cierra la incidencia
E   Failed: DID NOT RAISE ParteNoApto
tests/test_f030_veredicto_persistido.py:588: Failed: DID NOT RAISE ParteNoApto
E   Failed: DID NOT RAISE ParteNoApto
E   Failed: DID NOT RAISE ParteNoApto
=========================== short test summary info ===========================
FAILED ...::test_f030_r11_un_parte_no_apto_aprobado_a_mano_pasa_las_tres_puertas[archivo-cola_validacion_humana]
FAILED ...::test_f030_r11_...[archivo-revision_manual]
FAILED ...::test_f030_r11_...[grafico-cola_validacion_humana]
FAILED ...::test_f030_r11_...[grafico-revision_manual]
FAILED ...::test_f030_r11_...[cierre-cola_validacion_humana]
FAILED ...::test_f030_r11_...[cierre-revision_manual]
FAILED ...::test_f030_r7_un_cuerpo_que_miente_no_pasa_ninguna_de_las_tres_puertas[archivo]
FAILED ...::test_f030_r7_...[grafico]
FAILED ...::test_f030_r7_...[cierre]
9 failed, 1 passed in 0.52s
```

**El rojo es el del defecto, y se lee en la traza**:

- los seis de (a) fallan en **`puerta_de_estado.py:119`** con «este parte está
  **pendiente** … y **no consta que nadie lo haya aprobado**» — habiendo una
  aprobación humana con la huella del veredicto guardado. Es literalmente el
  §0.4 de `requirements.md`: la puerta recompone la huella sobre el stub, no
  coincide, la aprobación no cuenta y el parte cae a `estado_de_la_maquina`;
- los tres de (b) fallan con **`DID NOT RAISE ParteNoApto`**: el cuerpo que
  miente **pasa hoy las tres puertas**, y en las tres el paso siguió su camino
  —el archivo llegó a la biblioteca y las otras dos a leer la reclamación del
  ERP—. Ninguna es un fallo de import ni de nombre.

### T1 · la comprobación de que ese rojo se pondrá verde

Guion de un solo uso, **no versionado** (`design.md` §2 lo prevé así), que no
toca producción: solo llama a `estado_del_parte` con las dos fuentes.

```
$ ./.venv/Scripts/python.exe <guion de un solo uso, en el scratchpad>
huella apuntada (veredicto guardado): e9bfa607
huella recomputada (stub del cuerpo): 9d8596a0
estado con el stub     : pendiente
estado con lo guardado : aprobado
huella del stub con destino archivo_y_cierre: 371a85e5
huella del stub con destino cola_validacion_humana: 9d8596a0
huella del stub con destino revision_manual: e647e345
```

Dos cosas **[MEDIDAS]** aquí, y las dos confirman la spec:

1. las tres huellas del stub son **exactamente** las tres constantes de §0.5
   —`371a85e5…`, `9d8596a0…`, `e647e345…`—, incluida la `9d8596a0…` que midió
   el humano sobre RS26.09/0178. La huella con la que se juzga hoy no depende
   del parte;
2. con el veredicto **guardado** el estado es **`aprobado`**, así que los seis
   casos de (a) se pondrán verdes cuando la puerta lea de donde tiene que leer
   (T8), y no por ninguna otra razón.

### T2 · el rojo esperado, y es de «todavía no existe»

```
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_validacion_y_cierre'
tests/test_f030_veredicto_persistido.py:740: AttributeError: ... (×7 casos)
```

`mapeo.fila_a_validacion_y_cierre` la añade **T4**. Es el rojo que la propia
tarea declara. Para que ese «todavía no existe» **no contaminara el rojo de
T1**, el módulo se importa entero (`from infrastructure.persistencia import
mapeo`) en vez de importar la función: un `from … import` habría dejado en rojo
el fichero completo por un `ImportError`, que no demuestra nada.

---

## Decisiones de diseño de este bloque

1. **El stub del borde se escribe en el test, no se importa de `archivar.py`.**
   T10 va a retirar esa construcción del borde; si el test la importara,
   dejaría de probar nada en cuanto se arreglara. Escribiéndolo aquí, lo que
   queda vigilado después es más fuerte y es lo que pide R1: **aunque alguien
   vuelva a meter un veredicto en el contexto, la puerta no lo mira**
   (`design.md` §5.3, punto 1).
2. **El veredicto guardado lo emite `validar_parte` de verdad**, no un
   `ResultadoValidacion` montado a mano, y los dos campos decisivos se fijan a
   los del formulario. Así el cuerpo **dice la verdad** y el único desajuste
   posible entre las dos huellas es el que mete el stub, que es lo que el caso
   viene a enseñar.
3. **Andamio declarado, con fecha de retirada: T3.** El campo
   `SituacionParte.validacion` es de T3. Para que el rojo de T1 fuera el del
   defecto y no un `TypeError` de construcción, el ayudante `_situacion` cuelga
   el veredicto del objeto con `object.__setattr__` **mientras el campo no
   exista** (`_SITUACION_TRAE_VEREDICTO`). En T3 desaparecen la constante y la
   rama; está escrito en el propio fichero, al lado de las dos.
4. **El caso del cuerpo que miente prepara la traza del gráfico adjuntado.**
   Sin ella, la puerta de F-012 cortaría el cierre antes y el rojo no diría
   nada del defecto. Con ella, el caso enseña que hoy **se llega a escribir en
   el ERP**.
5. **Dobles propios y no importados de `test_f028_puertas.py`.**
   `UsuariosConLogin` y `PreferenciasSinAutoCierre` se repiten aquí (20 líneas)
   en vez de importarse de otro módulo de tests: T9 va a tocar los ayudantes de
   ese fichero, y F-030 no puede quedar colgando de ellos.

---

## Estado de la suite y del portero

### La suite del servicio, completa

```
$ ./.venv/Scripts/python.exe -m pytest -q --tb=no --ignore=tests/test_f010_prompt_keys_infra.py
16 failed, 2646 passed, 13 skipped in 30.97s
```

**Los 16 rojos son los 16 casos nuevos** —9 de T1 y 7 de T2—. Ni uno más: el
fichero nuevo no ha movido nada de lo que ya estaba verde.

### `bash harness/init.sh` · **ROJO, y por dos motivos distintos**

El rojo de este bloque **es el esperado** y está descrito arriba. Pero el
portero **ni siquiera llega a verlo**, porque se para antes en otro que ya
estaba ahí:

```
$ bash harness/init.sh
...
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)      ← suite de la raíz
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f010_prompt_keys_infra.py ____________
tests\test_f010_prompt_keys_infra.py:74: in claves_de_infra
    for variable, valor in claves_fijadas_en(script.read_text(encoding="ascii"))
E   UnicodeDecodeError: 'ascii' codec can't decode byte 0xef in position 0: ordinal not in range(128)
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
[KO] servicio api (services/postventa-api): pytest en rojo
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-030 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-030-veredicto-persistido
1 comprobaciones fallidas. NO empieces a trabajar.
```

> **HALLAZGO DE ENTORNO · no es de F-030 y no lo arregla este bloque.**
> `tests/test_f010_prompt_keys_infra.py:74` lee todos los `.ps1` de `infra/`
> con `encoding="ascii"`, y **`infra/90_push_dev_main.ps1` empieza por BOM**
> (`ef bb bf`), que es justo lo que manda `docs/CONVENTIONS.md` para
> PowerShell: «UTF-8 con BOM». El choque entra con el commit `ae38aa0`
> («Script 90»), **anterior a esta rama**, y tumba la colección entera del
> módulo, así que `pytest -x` se para ahí y **no llega a ejecutar ni un test**
> de `services/postventa-api`.
>
> Se comprueba fácil: `head -c 3 infra/90_push_dev_main.ps1` da `ef bb bf`, y
> es el **único** `.ps1` de `infra/` con BOM.
>
> **No se toca**: cae fuera de los límites de este encargo —ni `infra/` ni
> ningún fichero de `services/` que no sea el de tests nuevo— y arreglarlo es
> elegir entre dos convenciones (`utf-8-sig` en el test, o quitar el BOM del
> script en contra de `CONVENTIONS.md`). **Lo decide el humano.** Mientras no
> se arregle, el portero se queda rojo por este motivo aunque F-030 acabe
> verde, y **T20 no se podrá cerrar**.

---

## Evidencias

Números **medidos**, no estimados. La feature va por bloques y este es el
bloque 0: lo que aquí no se puede medir todavía se dice, con su motivo y con la
tarea que lo medirá.

| Evidencia | Valor medido | Cómo |
|---|---|---|
| Tests ejecutados (servicio) | **2 675**: 2 646 pasan, 16 fallan (los nuevos, el rojo buscado), 13 se saltan | `pytest -q --ignore=tests/test_f010_prompt_keys_infra.py` |
| Tests nuevos de este bloque | **17** casos: 9 de T1 (+1 que ya pasa) y 7 de T2 | recuento del fichero |
| Tiempo de la suite del servicio | **30,97 s** | la salida de pytest de arriba |
| Suite de la raíz (`tests/`) | 62 pasan en **3,58 s** | `bash harness/init.sh` |
| Cobertura de las líneas cambiadas | **N/A en este bloque**, y lo dice el propio portero: «F-030 no cambia líneas Python de producción frente a `dev`». Se mide en **T18**, cuando haya producción que cubrir | línea `PUERTA COBERTURA` de `init.sh` |
| Mutantes generados y supervivientes | **No procede todavía**: mutar producción sin haberla tocado no diría nada. La campaña es **T18**, con cero supervivientes y análisis uno a uno | `python -m harness.mutacion --feature F-030` |
| Lint del fichero nuevo | **0 avisos** (`ruff 0.16.3`) | `python -m ruff check services/postventa-api/tests/test_f030_veredicto_persistido.py` |

---

## Verificaciones MANUAL (humano) — pendientes, de la feature entera

- **V1 · el parte que está esperando.** Con F-030 desplegado en `dev`, archivar
  el parte `b7e9b037` de **RS26.09/0178** y comprobar que se archiva sin volver
  a decidir nada. **Escribe en SharePoint: exige autorización expresa del
  humano para esa incidencia y no se hace desde local.**
- **V2 · el coste, medido.** Contar las consultas de una tanda real de 22 partes
  contra el PostgreSQL compartido y comprobar que no ha subido respecto a F-028
  (R18).
- **Aviso de entorno vigente:** `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` están
  **abiertas** en `dev`. Este bloque no ha ejecutado ninguna llamada real.

> El riesgo de `design.md` §10.7 —el nombrado de `/api/archivar` sale del
> cuerpo— **ya está dado de alta como `F-031`** (commit `11c04d0`, `pending`),
> así que no hay nada que proponer: sigue fuera del alcance de F-030.

## Lo que queda para cerrar la feature

Bloques 1 a 5 de `tasks.md` (T3–T20), en su orden y de uno en uno. El siguiente
encargo es el **bloque 1**: `SituacionParte` gana el veredicto (y con él
desaparece el andamio de T3), `mapeo.fila_a_validacion_y_cierre`, la sentencia
nueva y `consultar_situacion`.

---

# Bloque 1 · Traer el veredicto guardado, sin un viaje más (T3–T7) — **ENTREGADO**

> Cinco tareas, cinco commits, del `c8bb670` al `aa94d32` sobre
> `feature/F-030-veredicto-persistido`. **Los 7 casos de T2 están en verde.**
> Los 9 de T1 siguen en rojo, y eso es lo correcto: son del bloque 2.
>
> Ni una llamada real. Ni a Sigrid, ni a SharePoint, ni al PostgreSQL. Las dos
> ventanas de escritura siguen abiertas en `dev` y este bloque no ha tocado
> ninguna.

## Qué cambió, en una frase

El veredicto guardado **ya se puede leer**: viaja dentro de la consulta de
situación que las tres puertas ya hacían, así que llega sin costar ni un viaje
más. Lo que todavía **no** ha cambiado es quién lo juzga: la puerta sigue
mirando `ctx.validacion`. Eso es T8, del bloque 2.

## Ficheros tocados

### Producción (5)

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/models/estado.py` | `SituacionParte` gana `validacion` como **cuarto y último** campo (T3), y su docstring queda enmendada con nota fechada. |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | `fila_a_validacion_y_cierre` y `_avisos_desde_json` (T4). Sigue **puro**: sin `psycopg` y **sin logger**. |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | `select_veredicto_y_cierre` (T5). |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | `consultar_situacion` usa la sentencia nueva y devuelve las cuatro cosas (T6). |
| `services/postventa-api/domain/ports/persistencia.py` | Docstrings de contrato de `consultar_situacion` y `guardar_validacion` (T7). |

### Tests (6)

| Fichero | Qué |
|---|---|
| `tests/test_f030_veredicto_persistido.py` | **Se retira el andamio de T3** y se añaden 2 casos de T3 + 4 de T7. |
| `tests/test_f005_mapeo.py` | 10 casos de T4. |
| `tests/test_f005_sentencias.py` | 5 casos de T5. |
| `tests/test_f028_persistencia.py` | 5 casos de T6; **2 casos existentes adaptados** (ver más abajo). |
| `tests/test_f005_logs_sin_datos_personales.py` | 1 caso de T6 (R21). |
| `tests/test_f028_estado_dominio.py` | **1 aserto de centinela enmendado**: la desviación de la spec, explicada abajo. |

**No se tocó nada** de lo que la spec prohíbe: ni `aprobacion.py`, ni
`validacion.py`, ni `infrastructure/persistencia/sql/`, ni
`interface_adapters/api/`, ni `paso_persistencia.py`, ni `puerta_de_estado.py`,
ni el front, ni `infra/`, ni `.env`. **No hay DDL** (R20).

## El andamio de T1, retirado

`_situacion()` colgaba el veredicto del objeto con `object.__setattr__` porque
el campo no existía. Con T3 el campo existe, así que:

- desaparecen la constante `_SITUACION_TRAE_VEREDICTO` y su rama;
- `_situacion()` construye la situación **normal**, con los cuatro argumentos;
- se anota en su docstring que el andamio se retiró en T3, para que no lo
  busque nadie.

## Decisiones de este bloque

1. **`validacion` va el último de los cuatro campos** (lo manda `design.md`
   §5.1). Todo el código construye `SituacionParte` por palabra clave, pero una
   construcción posicional que aparezca por el camino tiene que seguir leyendo
   los tres de antes en su sitio. Hay un caso que afirma el **orden**, no solo
   el conjunto.
2. **Los enumerados revientan, los dos campos decisivos no.**
   `Veredicto`, `Destino`, `ClasificacionFirma` y `CodigoMotivo` levantan
   `ValueError` ante un literal que el dominio no conoce. En cambio
   `codigo_obra` y `numero_incidencia` a `NULL` se leen como `""`: eso no es
   criterio, es el valor por defecto que ya declara `ResultadoValidacion`, y es
   lo que hace que la huella coincida con la del veredicto que se emitió con
   `""`. Las **observaciones** se pasan tal cual vienen —`None` o `"   "`—
   porque normalizarlas aquí sería una segunda copia del criterio de
   `_normalizar`, que es de la huella y no se toca (R13).
3. **`veredicto IS NULL` es «no hay validación»**, no el `hash`. La consulta se
   ancla en `partes`, así que el `hash` viene siempre. Un parte **con ficha y
   sin veredicto** y uno **sin ficha** acaban los dos en los dos huecos, que es
   lo que pedían R8 y R9.
4. **Dos sentencias, ni una más.** `consultar_situacion` sustituye la llamada a
   `consultar_estado_cierre`; no la añade. Hay un caso que comprueba que dentro
   de ese camino ya **no se ejecuta** `FROM postventa.cierres`: si siguiera,
   serían tres.
5. **Al log va el destino y nada más.** Un literal de `Enum`, que no es del
   papel y es lo que hace falta para diagnosticar por qué una puerta no se
   abrió. El caso de R21 comprueba las tres ausencias —observaciones, código de
   obra, número de incidencia— y además un **control positivo**, para que un
   logger que no registrara nada no pasara por bueno.
6. **Las dos enmiendas del puerto se citan literales.** La premisa retirada de
   `guardar_validacion` —«los tres pasos del circuito … **no puede** recomputar
   la huella»— es la descripción literal del defecto, y estaba escrita en el
   sitio donde se declaran los contratos. Se enmienda, no se borra: hay un caso
   que exige que el texto viejo **siga citado** dentro del recuadro y otro que
   exige que **ya no se afirme** fuera de él.

## Desviación de la spec, y por qué

**T3 pedía `tests/test_f028_estado_dominio.py` en verde «sin cambios», y eso
es imposible.** Ese fichero tiene un centinela estructural,
`test_f028_r2_la_situacion_trae_las_tres_cosas_que_hacen_falta_y_ninguna_mas`,
que afirma por construcción que los campos de `SituacionParte` son
**exactamente tres** — que es justo lo que T3 cambia por decisión de la propia
spec (`design.md` §5.1, R2). El fichero no está en la regla dura 4 (que protege
`test_f028_puertas.py`, `test_f028_huella_intacta.py` y `test_f026_*`), y
§5.5 no lo lista porque no se previó.

Qué se hizo, y qué **no**:

- **Se enmendó el aserto con nota fechada**: el conjunto pasa a ser los cuatro
  campos. El texto viejo se cita entero en la docstring, con el motivo.
- **No se aflojó nada.** El caso sigue exigiendo que el conjunto sea
  **exactamente** el declarado: un quinto campo lo pone en rojo igual que antes
  lo ponía el cuarto. No se cambió a «contiene al menos», que habría sido
  desactivar el centinela.

Se deja anotado para el reviewer: si se prefiere otra lectura, el cambio está
aislado en un solo aserto del commit `c8bb670`.

## Fase RED · los tests del bloque, contra el código de antes del bloque

El rigor es `critico`, así que no vale decir «se siguió TDD». Se montó un
`git worktree` en `3e4a799` —el HEAD de antes de este bloque— con **los
ficheros de test de ahora** encima, y se ejecutó. Comando:

```
git worktree add /tmp/f030red 3e4a799
cp <los 5 ficheros de test> /tmp/f030red/services/postventa-api/tests/
cd /tmp/f030red/services/postventa-api && python -m pytest \
  tests/test_f005_mapeo.py tests/test_f028_persistencia.py \
  tests/test_f005_logs_sin_datos_personales.py \
  tests/test_f030_veredicto_persistido.py -q -p no:randomly
```

Resultado: **39 failed, 75 passed**, y `tests/test_f005_sentencias.py` ni
siquiera colecciona. Las trazas, tal cual:

### T5 · la sentencia no existe (el fichero entero no colecciona)

```
ImportError while importing test module '...\tests\test_f005_sentencias.py'.
tests\test_f005_sentencias.py:34: in <module>
    from infrastructure.persistencia.sentencias import (
E   ImportError: cannot import name 'select_veredicto_y_cierre' from
    'infrastructure.persistencia.sentencias'
```

### T3 · el cuarto campo no está

```
        nombres = tuple(campo.name for campo in fields(SituacionParte))

>       assert nombres == (
            "decision_humana",
            "ultimo_estado_registrado",
            "estado_cierre",
            "validacion",
        )
E       AssertionError: assert ('decision_hu...stado_cierre') == ('decision_hu... 'validacion')
E         Right contains one more item: 'validacion'

tests\test_f030_veredicto_persistido.py:501: AssertionError
```

### T4 · la función no existe

```
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute
    'fila_a_validacion_y_cierre'
tests\test_f005_mapeo.py:451: AttributeError
```

### T6 · el adaptador seguía yendo a `cierres` por su cuenta

```
tests\test_f028_persistencia.py:1443: in test_f030_r18_traer_el_veredicto_no_cuesta_ninguna_consulta_mas
    assert conexion.veces_con(f"FROM {ESQUEMA}.cierres") == 0
E   AssertionError: assert 1 == 0
E    +  where 1 = veces_con('FROM postventa.cierres')
```

### T6 (R21) · la situación no traía veredicto que registrar ni que callar

```
E   AttributeError: 'SituacionParte' object has no attribute 'validacion'
------------------------------ Captured log call ------------------------------
INFO  infrastructure.persistencia.repositorio_pg:repositorio_pg.py:284
      F-028 situación del parte leída: hash=hash-inventado-0001
      decidida_por_persona=False ultimo_estado=None cierre=None
tests\test_f005_logs_sin_datos_personales.py:262: AttributeError
```

*(La línea de log de antes no llevaba `destino=`: se ve en la traza.)*

### T7 · el puerto seguía afirmando lo retirado

```
E   AssertionError: assert 'revoca la a...a no es este' not in 'Guarda el v...sign.md` §7.'
      'revoca la aprobaci...dicto ya no es este' is contained here:
        R39). **Y revoca la aprobación humana cuyo veredicto ya no es este**
        (F-026, R30), en la misma operación. […] incluidos los tres pasos del
        circuito, cuyo cuerpo de pet...
tests\test_f030_veredicto_persistido.py:873: AssertionError
```

**Un caso nuevo pasa en verde también contra el código viejo, y es a propósito:**
`test_f030_r1_el_puerto_no_gana_ningun_metodo`. No es un test de fase RED, es un
**centinela**: afirma que el puerto no crece con un `consultar_validacion`
aparte, que habría costado tres consultas más por parte. Su valor está en el
futuro, no en este bloque.

## Estado de la suite

### La suite del servicio, completa

```
cd services/postventa-api && python -m pytest tests -q
...
9 failed, 2685 passed, 3 skipped in 23.44s
```

- **Antes del bloque** (HEAD `3e4a799`): `16 failed, 2651 passed, 3 skipped`.
- **Ahora**: `9 failed, 2685 passed, 3 skipped`.
- **Los 7 que pasaron de rojo a verde son exactamente los 7 de T2**, los
  `test_f030_r10_el_veredicto_recompuesto_da_la_misma_huella[...]`.
- **Los 9 que siguen en rojo son exactamente los 9 de T1**: los 6 de
  `test_f030_r11_...` y los 3 de `test_f030_r7_...`. Son del **bloque 2** (T8),
  que es quien hace que la puerta lea el veredicto guardado.
- **Nada de lo que pasaba antes se ha puesto en rojo.** 2 651 → 2 685 son +34:
  27 casos nuevos y los 7 de T2 que cambiaron de lado.

### Recuento por fichero tocado

| Fichero | Resultado |
|---|---|
| `test_f030_veredicto_persistido.py` | 9 failed, 14 passed *(los 9 son de T1)* |
| `test_f005_mapeo.py` | 29 passed |
| `test_f005_sentencias.py` | 26 passed |
| `test_f028_persistencia.py` | 56 passed |
| `test_f005_logs_sin_datos_personales.py` | 6 passed |
| `test_f028_estado_dominio.py` | 55 passed |

### `bash harness/init.sh` · **ROJO, y es el rojo esperado**

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)
[KO] servicio api (services/postventa-api): pytest en rojo
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 23 líneas cambiadas cubiertas (23/23, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-030-veredicto-persistido
```

El único `[KO]` es la suite del servicio, y el portero corta en el primer fallo:

```
tests\test_f030_veredicto_persistido.py:559: in test_f030_r11_...
    puerta(ctx, repositorio, dobles, commit=False)
application\pipelines\puerta_de_estado.py:119: in exigir_parte_aprobado
    raise ParteNoApto(f"{motivo}, así que {y_por_eso}")
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación
    lo manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado,
    así que no se archiva
```

Es **el defecto**, intacto y esperando a T8: el veredicto ya está en la
situación, pero la puerta todavía juzga el del contexto.

**Los 61 avisos de ruff son deuda previa y no han subido**: se contaron 61 en
`3e4a799` y 61 ahora, sobre un `git worktree` del punto de partida. Este bloque
no añade ninguno.

## Evidencias

| Evidencia | Valor medido | Cómo se obtuvo |
|---|---|---|
| Tests ejecutados (servicio) | **2 697**: 2 685 pasan, 9 fallan (los 9 de T1, del bloque 2), 3 se saltan | `cd services/postventa-api && python -m pytest tests -q` |
| Tests nuevos de este bloque | **27** (2 de T3, 10 de T4, 5 de T5, 6 de T6, 4 de T7) | 2 697 − 2 670 del punto de partida |
| Tests que pasaron de rojo a verde | **7**, los de T2 | comparación de las dos salidas |
| Tests que pasaron de verde a rojo | **0** | ídem |
| Tests existentes adaptados | **3** (los dos de `consultar_situacion` en `test_f028_persistencia.py` y el centinela de `test_f028_estado_dominio.py`), ninguno aflojado | diff de los commits `7bc7721` y `c8bb670` |
| Cobertura de las líneas cambiadas | **100,0 %** (23/23, umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| Tiempo de la suite del servicio | **23,44 s** | la salida de pytest de arriba |
| Avisos de lint | **61 antes, 61 ahora**: este bloque no añade ninguno | `python -m ruff check . --output-format=concise` sobre `3e4a799` y sobre `HEAD` |
| Mutantes generados y supervivientes | **No procede en este bloque.** La campaña es **T18** (bloque 5), con cero supervivientes y análisis uno a uno; mutar ahora la puerta —que es el mutante decisivo— no diría nada, porque el arreglo es T8 | `python -m harness.mutacion --feature F-030` |

## Lo que queda

**Bloque 2 (T8, T9)**: que `puerta_de_estado.py` lea `ctx.situacion.validacion`
y deje de mirar `ctx.validacion`, y que los **dos ayudantes** de
`test_f028_puertas.py` preparen el veredicto en la situación. Con eso los 9
casos de T1 pasan a verde. Después, bloques 3, 4 y 5.

Sigue abierto, de la feature entera: **V1** (archivar RS26.09/0178 en `dev`,
escribe en SharePoint y exige autorización expresa del humano) y **V2** (contar
las consultas de una tanda real de 22 partes). Ninguna de las dos es condición
de cierre.

---

# Bloques 2 y 3 · La puerta juzga lo guardado, y el borde deja de fabricarlo (T8–T12) — **ENTREGADO**

> Cinco tareas, cinco commits, del `5fab17e` al `1c8fe2b` sobre
> `feature/F-030-veredicto-persistido`. **Los 9 casos de T1 están en verde**, y
> con ellos los 40 de `test_f030_veredicto_persistido.py`.
>
> **`bash harness/init.sh` termina en VERDE**, suite del servicio incluida:
> `2 711 passed, 13 skipped`. **Cero regresiones.**
>
> Ni una llamada real. Ni a Azure, ni a Sigrid, ni a SharePoint, ni al
> PostgreSQL compartido. Las dos ventanas de escritura siguen abiertas en
> `dev` y estos dos bloques no han tocado ninguna.

## Qué cambió, en una frase

**La regresión está arreglada.** La puerta de los tres pasos deriva el estado
del veredicto que consta en `postventa.validaciones` —que llegó en el bloque 1
dentro de `SituacionParte`— y los tres endpoints han dejado de fabricar el
suyo. El parte de RS26.09/0178 se archivará sin que nadie vuelva a decidir en
cuanto esto se despliegue (queda como verificación manual **V1**).

---

## T8 · la puerta lee `ctx.situacion.validacion` — commit `5fab17e`

`exigir_parte_aprobado` **consulta primero** y lee el veredicto de la
situación; «no hay veredicto» pasa a mirarse después, porque no hay forma de
saber si consta validación sin preguntar. La precedencia de los motivos no
cambia: «no consta que este parte haya pasado la validación» sigue yendo el
primero y sigue siendo el suyo (R8, R17). El destino del mensaje de
`pendiente` sale del veredicto **guardado**.

**`ctx.validacion` no se vuelve a leer en este módulo.** Es el blindaje de R1
y es más fuerte que retirar el stub del borde: aunque alguien vuelva a meter
un veredicto en el contexto, esta puerta no se entera.

La cabecera del módulo gana una enmienda fechada con las dos caras del
defecto y el porqué del cambio de fuente; la docstring de la función, el
porqué del orden nuevo.

**Tests nuevos: 15 casos.**

| Caso | Qué fija |
|---|---|
| `test_f030_r1_un_stub_apto_en_el_contexto_no_abre_ninguna_puerta` (×3) | **El decisivo.** Contexto con veredicto **apto a `archivo_y_cierre`**, almacén con **no apto a `revision_manual`** y sin decisión humana → **no pasa** ninguna. Y se afirma que el contexto **sigue trayendo** su veredicto: lo que se prueba es que la puerta no lo mira, no que nadie se lo haya puesto. |
| `test_f030_r1_un_stub_no_apto_en_el_contexto_no_cierra_una_puerta_abierta` (×3) | La otra mitad, y sin ella la anterior no demuestra nada: una puerta que lo rechazara todo también la pasaría. Guardado **apto**, contexto **no apto** → **pasa**. |
| `test_f030_r17_el_mensaje_de_pendiente_nombra_el_destino_guardado` (×6) | Los tres finales propios —«no se archiva», «no se adjunta a la reclamación», «no se cierra la incidencia»— y el destino **guardado** dentro. El del cuerpo (`archivo_y_cierre`) **no puede aparecer**. |
| `test_f030_r8_sin_veredicto_guardado_cada_puerta_dice_lo_suyo` (×3) | El orden nuevo: se consulta antes de decir que no, el motivo sigue siendo el suyo y no se cuela «pendiente». |

## T9 · los ayudantes de `test_f028_puertas.py` — commit `12328b7`

**Los 48 casos en verde y ni un aserto cambiado.** El diff del fichero son el
import, una nota fechada y **tres líneas**.

`tests/utiles_pg.py` gana `con_el_veredicto_guardado(repositorio, ctx)`, que
deja en el doble el veredicto que la base tendría de ese parte. Dos cosas que
**no** hace, y son las que impiden que sea una puerta trasera:

1. **no inventa un veredicto** —si el contexto no trae ninguno, el doble se
   queda sin él, que es lo que exige `_contexto_sin_veredicto()`—;
2. **no pisa** la situación que un caso haya preparado a propósito.

Y no se usa en los tests que vigilan la puerta: `test_f030_*` separa las dos
fuentes a mano, que es lo único que hace que cacen el defecto.

> **Desviación declarada.** `design.md` §5.5 hablaba de «dos ayudantes,
> `_dobles()` / `_con()`». En ese fichero **no existen**: los ayudantes que
> reciben a la vez el contexto y el doble son **tres**, `_archivar`,
> `_adjuntar` y `_cerrar`. Se tocaron esos tres y ningún caso.

## T10 · los tres endpoints — commit `4750483`

`_como_contexto` devuelve el contexto con `validacion=None` en `archivar.py`,
`adjuntar.py` y `cerrar.py`. Se van con el stub los tres valores inventados
—`motivos=()`, `clasificacion_firma=HUMANA`, `observaciones=None`— y los
parámetros `veredicto` / `destino` de `_como_contexto`, que ya no pintaban
nada. Imports huérfanos retirados: `ResultadoValidacion` en los tres y
`ClasificacionFirma` donde solo servía para el stub. **`Veredicto` y `Destino`
se quedan**: los sigue usando `_exigir_valor_conocido`.

El párrafo «El veredicto llega en el cuerpo, y se vuelve a comprobar» de
`archivar.py` —donde F-006 anotó la deuda D4 que esta feature paga— queda
sustituido por lo que pasa ahora. `adjuntar.py` y `cerrar.py` ganan la misma
nota fechada en su cabecera.

**El contrato HTTP no cambia (R19, D6)**, y está comprobado: los casos de 400
ante un `veredicto` o un `destino` desconocidos siguen en verde en los tres
ficheros de endpoint.

Con esto, **los 3 casos de T1 (b)** —el cuerpo que miente— quedan en verde.

## T11 · los tests que pasaban gracias al cuerpo — commit `7d7dacc`

Al leerse el veredicto de la base se quedaron en la puerta **232 casos de 14
ficheros**. Todos arreglados **preparando el veredicto en el doble**, que es
lo que prescribe `design.md` §10.5. **Ninguna puerta se afloja: ni un solo
caso se pone verde relajando una comprobación.**

### Utillería nueva

| Sitio | Qué | Por qué |
|---|---|---|
| `tests/utiles_validacion.py` | `veredicto_apto(...)` y `veredicto_no_apto(...)` | Los emite `validar_parte` **de verdad**: si F-004 cambiara sus reglas, estos tests se enterarían en vez de seguir archivando lo que ya no es apto. |
| `tests/utiles_sharepoint.py` | `RepositorioFalso` gana `situacion` programable | Hasta hoy devolvía siempre una situación vacía y era deliberado. Dejó de poder serlo cuando el **veredicto** pasó a viajar dentro de ella: un doble que contestara «de este parte no consta validación» pararía en la puerta a todos los tests de F-006, que van de otra cosa. |

### Los 14 ficheros, uno a uno

| Fichero | Casos | Qué se cambió, y por qué |
|---|---|---|
| `test_f012_paso_grafico.py` | 57 | El ayudante `_adjuntar` deja el veredicto del contexto en el doble. **Un ayudante.** |
| `test_f009_paso_cierre.py` | 29 | Igual en `_cerrar`, más **dos casos sueltos** (`r47_sin_numero_de_incidencia`, `r32_sin_login_confirmado`) que llamaban a `paso_cierre` directo. |
| `test_f025_sin_dry_run_previo.py` | 22 | Igual en `_adjuntar` y `_cerrar`. **Dos ayudantes.** |
| `test_f012_cerrar_exige_grafico.py` | 20 | El ayudante `_cerrar`, más `_respuesta_del_borde`, que es de endpoint y necesita el veredicto **apto guardado**. |
| `test_f006_paso_archivo.py` | 20 | El atajo `archivar(...)`, más `r27_el_destino_sale_de_configuracion`, que llama al paso directo. |
| `test_f012_adjuntar_http.py` | 17 | Endpoint: ayudante `_repositorio()` que siembra el veredicto apto, usado en el doble por omisión y en el caso de la traza idempotente. |
| `test_f019_orden_archivado.py` | 16 | `_dobles()` siembra el apto (con `setdefault`, para que un caso pueda dar el suyo), `_archivar` llama al ayudante, y el caso del 503 con la base caída. **Más el caso del parte no apto (abajo).** |
| `test_f009_cerrar_http.py` | 15 | Endpoint: mismo ayudante `_repositorio()`. **Más el caso del parte no apto (abajo).** |
| `test_f028_persistencia.py` | 7 | El ayudante `_cerrar` de la sección de constancia del cierre. |
| `test_f012_logs_sin_datos_personales.py` | 7 | El ayudante `_adjuntar`. |
| `test_f009_logs_sin_datos_personales.py` | 6 | El ayudante `_cerrar`. |
| `test_f010_borde_persistencia.py` | 6 | Los dos constructores de repositorio caído (`_repositorio_caido`, `_caida_desde_el_principio`) llevan el veredicto apto: sin él pararían en la puerta en vez de llegar a la caída de la base, que es lo que prueban. |
| `test_f026_puertas.py` | 5 | `r25_..._no_se_archiva` (×2), que **afirma el destino dentro del mensaje**: sin veredicto guardado el motivo sería otro. Y los 3 de `r24_ningun_handler_lee_la_aprobacion_del_cuerpo` (abajo). |
| `test_f006_archivar_http.py` | 5 | Endpoint: ayudante `_repositorio()`. **Más el caso del parte no apto y los dos asertos (abajo).** |

### Tres casos que había que arreglar con el veredicto **no apto**, no con el apto

Si se les hubiera dejado sin veredicto seguirían dando **el mismo error por
otro motivo** —«no consta que este parte haya pasado la validación» en vez de
«la validación lo manda a la cola»— y habrían dejado de probar lo que dicen:

- `test_f006_archivar_http.py::test_f006_r31_parte_no_apto_responde_409`;
- `test_f019_orden_archivado.py::test_f019_r19_un_parte_no_apto_no_escribe_ni_la_traza_previa`;
- `test_f009_cerrar_http.py::test_f009_r48_un_parte_no_apto_sube_como_error_de_dominio`.

### Un caso que **pasaba por el motivo equivocado** y se arregló igualmente

`test_f006_archivar_http.py::test_f006_r30_la_respuesta_no_lleva_el_parte_ni_la_configuracion`
**no estaba en rojo**: comprueba que la respuesta no filtra datos, y una
respuesta de 409 tampoco los filtra. Se le preparó el veredicto de todas
formas, para que siga recorriendo el camino feliz que dice recorrer.

### Los dos únicos asertos cambiados en todo el bloque

Los dos en `test_f006_archivar_http.py::test_f006_r30_el_endpoint_no_inventa_lecturas_de_los_campos_que_no_recibe`:

```
assert contexto.validacion.observaciones is None
assert contexto.validacion.confianza_observaciones == 0
```

Miraban **el stub que T10 acaba de retirar**. Pasan a
`assert contexto.validacion is None`, que es lo contrario y más fuerte: ya no
se afirma que el veredicto fabricado salga vacío, sino que **no se fabrica
ninguno**. Los dos casos siguen afirmando lo suyo sobre los nueve campos de la
extracción, sin tocar.

Ningún aserto de `test_f028_puertas.py`, `test_f028_huella_intacta.py` ni
`test_f026_*` cambia (regla dura 4).

### Un centinela ajeno que tenía razón

`test_f026_puertas.py::test_f026_r24_ningun_handler_lee_la_aprobacion_del_cuerpo`
lee el **fuente** de los tres handlers y falla si aparece la palabra «aprob».
Las cabeceras nuevas de T10 la usaban al contar el defecto («la aprobación de
una persona no contaba nunca»). **Se reescribieron las cabeceras**, no el
centinela: el control tiene razón y se respeta. Dice lo mismo con «lo que una
persona hubiera decidido sobre ese parte».

## T12 · el centinela estructural (R3) — commit `1c8fe2b`

`test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto` recorre con
`ast` **todos** los módulos de `interface_adapters/api/` y falla si alguno
**construye** un `ResultadoValidacion`.

Tres decisiones:

1. **La carpeta entera**, no los tres ficheros de la feature: el fallo que
   viene a cazar es que mañana aparezca un endpoint nuevo que vuelva a
   fabricarlo, y un control apuntado a tres nombres no lo vería.
2. **El árbol y no el texto.** `"ResultadoValidacion"` aparece en las
   anotaciones de tipo de `parte.py`, `validar.py` y `estado_serializado.py`
   —legítimas— y en las cabeceras de los tres endpoints, que cuentan lo que
   pasó. Un `grep` nacería inútil o lleno de excepciones.
3. **Por nombre y por atributo**: `ResultadoValidacion(...)` y
   `validacion.ResultadoValidacion(...)`. Cambiar la forma del import no puede
   ser la manera de esquivarlo.

Va con su **control del control**,
`test_f030_r3_el_centinela_sabe_ver_una_construccion`: un módulo escrito en el
propio test con la construcción de pega que tenía `archivar.py`, que el
centinela tiene que ver, y otro con solo anotaciones, que no puede hacerlo
saltar.

### La comprobación en rojo, de verdad

Se le devolvió el stub a `archivar.py` y se ejecutó:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py -q --tb=short -p no:randomly -k "r3"
F.                                                                       [100%]
================================== FAILURES ===================================
_________ test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto _________
tests\test_f030_veredicto_persistido.py:1137: in test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto
    assert culpables == {}, (
E   AssertionError: estos módulos del borde fabrican un ResultadoValidacion, y eso es
    exactamente lo que rompió el circuito en F-030: el veredicto lo emite F-004 con la
    extracción, o se lee de la base. {'archivar.py': [208]}
E   assert {'archivar.py': [208]} == {}
E     Left contains 1 more item:
E     {'archivar.py': [208]}
=========================== short test summary info ===========================
FAILED tests/test_f030_veredicto_persistido.py::test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto
1 failed, 1 passed, 38 deselected in 0.48s
```

**Caza el fichero y la línea.** El cambio se deshizo acto seguido con
`git checkout --`, la suite volvió a verde y el árbol quedó limpio antes del
commit.

---

## Fase RED · las trazas, tal cual

Rigor `critico`: no vale decir «se siguió TDD». Los 15 casos de T8 se
ejecutaron contra el código de antes de T8 —`git stash push` **solo** sobre
`application/pipelines/puerta_de_estado.py`, dejando los tests de ahora
encima— y **los 15 fallan**, cada uno por su motivo:

```
$ git stash push -- services/postventa-api/application/pipelines/puerta_de_estado.py
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py \
    -q --tb=line -p no:randomly -k "r1_un_stub or r17_el_mensaje or r8_sin_veredicto"

FFFFFFFFFFFFFFF                                                          [100%]
================================== FAILURES ===================================
E   Failed: DID NOT RAISE ParteNoApto
...test_f030_veredicto_persistido.py:693: Failed: DID NOT RAISE ParteNoApto      (x3, r1 stub apto)
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo manda
    a «revision_manual» y no consta que nadie lo haya aprobado, así que no se archiva
...application\pipelines\puerta_de_estado.py:119                                 (x3, r1 stub no apto)
E   Failed: DID NOT RAISE ParteNoApto
...test_f030_veredicto_persistido.py:748: Failed: DID NOT RAISE ParteNoApto      (x6, r17)
E   Failed: DID NOT RAISE ParteNoApto
...test_f030_veredicto_persistido.py:781: Failed: DID NOT RAISE ParteNoApto      (x3, r8)
```

Y la tanda entera del fichero contra ese mismo código: **24 failed, 14 passed**
—los 9 de T1 más los 15 de T8—. Cada rojo se lee y es el suyo:

- los tres de **`r1_un_stub_apto`** no levantan nada: con la puerta vieja, el
  `veredicto=apto` del contexto abre las tres puertas aunque el almacén diga
  `revision_manual`. Es el agujero de §0.9;
- los tres de **`r1_un_stub_no_apto`** fallan en `puerta_de_estado.py:119`
  nombrando **el destino del contexto**: la puerta vieja rechaza un parte cuyo
  veredicto guardado es apto;
- los seis de **`r17`** y los tres de **`r8`** no levantan nada, por lo mismo
  que los primeros.

El stash se recuperó con `git stash pop` y quedó constancia en la salida.

---

## Estado de la suite y del portero

### `bash harness/init.sh` · **VERDE**

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 30 líneas cambiadas cubiertas (30/30, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-030-veredicto-persistido
ENTORNO LISTO. Puedes trabajar.
```

> El **hallazgo de entorno** del bloque 0 —`test_f010_prompt_keys_infra.py`
> leyendo los `.ps1` de `infra/` en `ascii` contra un script con BOM— ya está
> resuelto en `dev` y llegó a esta rama con el merge `3e4a799` («el script 90
> en ASCII»). El portero ya no se para ahí.

### El recuento exacto

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests -q
2711 passed, 3 skipped in 20.10s
```

| | Antes del bloque 2 (`7a42a74`) | Ahora (`1c8fe2b`) |
|---|---|---|
| Pasan | 2 685 | **2 711** |
| Fallan | 9 | **0** |
| Se saltan | 3 | 3 |

- **Los 9 que estaban en rojo son exactamente los 9 de T1**, y están en verde:
  los 6 de `test_f030_r11_...` (la aprobación humana que no sobrevivía, que es
  RS26.09/0178) y los 3 de `test_f030_r7_...` (el cuerpo que miente).
- **Tests que pasaron de verde a rojo y se quedaron ahí: 0.**
- **Tests que se pusieron en rojo por el camino y se arreglaron: 232**, en 14
  ficheros, todos listados arriba con su motivo.
- **+26 casos netos**: 15 de T8, 2 de T12 y 9 que cambiaron de lado.
- La suite se ejecutó también **en orden aleatorio** (sin `-p no:randomly`):
  mismo resultado.

### Por fichero, los tocados

| Fichero | Resultado |
|---|---|
| `test_f030_veredicto_persistido.py` | **40 passed** (23 del bloque 1 + 15 de T8 + 2 de T12) |
| `test_f028_puertas.py` | **48 passed**, ni un aserto cambiado |
| `test_f012_paso_grafico.py` | 60 passed |
| `test_f009_paso_cierre.py` | 35 passed |
| `test_f006_paso_archivo.py` | 29 passed |
| `test_f006_archivar_http.py` | 14 passed |
| `test_f009_cerrar_http.py` | 28 passed |
| `test_f012_adjuntar_http.py` | 62 passed |
| `test_f026_puertas.py` | 13 passed |
| `test_f010_borde_persistencia.py` | 8 passed |

---

## Evidencias (bloques 2 y 3)

Números **medidos**, no estimados.

| Evidencia | Valor medido | Cómo se obtuvo |
|---|---|---|
| Tests ejecutados (servicio) | **2 714**: 2 711 pasan, **0 fallan**, 3 se saltan | `cd services/postventa-api && python -m pytest tests -q` |
| Tests ejecutados (portero completo) | 2 711 pasan, 13 se saltan | `bash harness/init.sh` |
| Tests nuevos de estos bloques | **17** (15 de T8, 2 de T12) | 2 714 − 2 697 del punto de partida |
| Tests que pasaron de rojo a verde | **9**, los de T1 | comparación de las dos salidas |
| Tests que pasaron de verde a rojo | **0** | ídem |
| Tests existentes adaptados | **232 casos en 14 ficheros** + los 48 de `test_f028_puertas.py`; **2 asertos cambiados en total**, los dos sobre el stub que T10 retira | diff de `7d7dacc` |
| Cobertura de las líneas cambiadas | **100,0 %** (30/30, umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| Tiempo de la suite del servicio | **20,10 s** | la salida de pytest de arriba |
| Avisos de lint | **61 antes, 61 ahora**: estos bloques no añaden ninguno. Los 4 `I001` que introdujeron mis inserciones de import se corrigieron con `ruff --fix` sobre esos 4 ficheros | `python -m ruff check .` y la línea `[AVISO] ruff` del portero |
| Mutantes generados y supervivientes | **No procede todavía.** La campaña es **T18** (bloque 5), con cero supervivientes y análisis uno a uno | `python -m harness.mutacion --feature F-030` |
| DDL | **Cero.** El diff de la rama no toca `infrastructure/persistencia/sql/` (R20; lo formaliza T17) | `git diff --name-only dev...HEAD` |

---

## Desviaciones de la spec, declaradas

**1. El alcance de T11 era mucho mayor de lo que preveía `design.md` §5.5.**
La spec listaba **cinco** ficheros de test a tocar y describía T9 como «un
cambio mecánico en dos ayudantes». La realidad medida: **232 casos en 14
ficheros**, de los cuales la spec nombraba tres (`test_f006_archivar_http.py`,
`test_f012_adjuntar_http.py`, `test_f009_cerrar_http.py`) y §5.5 no previó los
otros once —los de los **pasos** del pipeline, no de los endpoints—.

No se paró porque **la dirección no era ambigua**: §10.5 lo prescribe letra
por letra —«cada uno se arregla preparando el veredicto en el doble. Lo que
**no** vale es relajar la puerta»— y el encargo hacía explícitamente mías las
regresiones. Lo que la spec subestimó fue el **volumen**, no el método. Queda
anotado para el reviewer: si se prefiere otra forma, el cambio está aislado en
el commit `7d7dacc` y se apoya en un solo ayudante compartido
(`con_el_veredicto_guardado`) más dos builders de veredicto.

**2. T9 tocó tres ayudantes, no dos.** `design.md` §5.5 nombraba
`_dobles()` / `_con()`, que en `test_f028_puertas.py` no existen. Los que
reciben a la vez el contexto y el doble son `_archivar`, `_adjuntar` y
`_cerrar`. Ningún aserto cambió.

**3. Dos asertos de `test_f006_archivar_http.py` cambiaron.** Miraban el stub
que T10 retira, así que no podían sobrevivir a T10. Pasan a afirmar algo más
fuerte. Ese fichero no está en la regla dura 4.

## Lo que queda

**Bloque 4 (T13–T15)**: el doble `RepositorioComoLaBase` que guarda columnas y
no objetos, y el test de borde a borde con los cuerpos reales de los dos
endpoints sobre el caso de RS26.09/0178, con sus control-negativo. Después, el
bloque 5 (T16–T20): compatibilidad hacia atrás, control de DDL, cobertura y
mutación, documentación y verde final.

Sigue abierto, de la feature entera: **V1** (archivar RS26.09/0178 en `dev`;
escribe en SharePoint y exige autorización expresa del humano por incidencia) y
**V2** (contar las consultas de una tanda real de 22 partes). Ninguna es
condición de cierre.


---

# Bloques 4 y 5 · El test que faltó, y el cierre (T13–T20) — **ENTREGADO**

> Ocho tareas, ocho commits, del `d3252a3` al `0a94f00` sobre
> `feature/F-030-veredicto-persistido`, más el de este informe.
>
> **`bash harness/init.sh` termina en VERDE con exit code 0**: suite del
> servicio `2 736 passed, 0 failed, 3 skipped`. **Cero regresiones**, **cero
> supervivientes de mutación** y **cero DDL**.
>
> **Estos dos bloques no tocan ni una línea de producción.** Lo único que
> cambia fuera de `tests/` es `docs/ARCHITECTURE.md` (T19). Ni una llamada
> real a Azure, Sigrid, SharePoint ni al PostgreSQL compartido: las dos
> ventanas de escritura siguen abiertas en `dev` y aquí no se ha usado
> ninguna.
>
> **La feature no se marca `done`**: falta el APROBADO del reviewer.

## Qué cambió, en una frase

**La regresión ya no puede volver sin que un test lo diga.** Los bloques 2 y 3
arreglaron el defecto; estos dos son la prueba de que se queda arreglado: el
doble que se comporta como la base, el circuito recorrido de borde a borde con
los cuerpos reales, la compatibilidad hacia atrás medida, y el cierre formal
—cobertura, mutación, documentación y verde—.

## Ficheros tocados

### Producción: **ninguno**

| Fichero | Qué |
|---|---|
| `docs/ARCHITECTURE.md` | La precisión fechada del 2026-09-16 de F-030 en el punto 3 de «Semántica de dominio imprescindible» (T19). **Documentación, no código.** |

Ni `.env`, ni `infra/`, ni `services/postventa-front/`, ni
`infrastructure/persistencia/sql/`, ni ningún módulo de
`application/`, `domain/`, `infrastructure/` o `interface_adapters/`.

### Tests y utillería (3)

| Fichero | Qué |
|---|---|
| `services/postventa-api/tests/utiles_pg.py` | **`RepositorioComoLaBase`** (T13). `RepositorioEnMemoria` **no se toca**. |
| `services/postventa-api/tests/test_f030_circuito_borde_a_borde.py` | **Nuevo.** T14 (4 casos) y T15 (6 casos). |
| `services/postventa-api/tests/test_f030_veredicto_persistido.py` | Secciones de T13 (3 casos), T16 (7), T17 (3) y T19 (2). |

### Memoria del arnés (4)

`progress/current.md`, `progress/mutacion_F-030.md` (generado),
`progress/impl_F-030.md` (este informe) y
`specs/F-030-veredicto-persistido/tasks.md` (T13–T20 marcadas).

---

## T13 · el doble que se comporta como la base — commit `d3252a3`

`tests/utiles_pg.py` gana `RepositorioComoLaBase`, con **una** regla: guarda lo
que guardaría PostgreSQL y **no el objeto**.

| Operación | Qué guarda |
|---|---|
| `guardar_parte` | las **18 columnas** de `mapeo.valores_de_campos` |
| `guardar_validacion` | las **7 columnas** de `mapeo.valores_de_validacion` (sin observaciones: su DDL lo prohíbe, R21/R39) |
| `registrar_decision` | **acumula**, como la tabla append-only |
| `consultar_situacion` | **recompone** con la misma `mapeo.fila_a_validacion_y_cierre` de producción, armando la fila en el orden de `sentencias.select_veredicto_y_cierre` |

Que no pueda devolver el objeto que entró es **todo su valor**: es la propiedad
que `RepositorioEnMemoria` no tiene y por la que el defecto pasó. Si la
recomposición perdiera las observaciones, el código de obra o el orden de los
motivos, la huella dejaría de coincidir y el test se pondría rojo. Lo confirma
la mutación a mano de T18: **M2 y M3 lo ponen rojo**.

**Tres casos propios**, y cada uno mira una cosa distinta:

1. `..._no_devuelve_el_objeto_que_entro`: lo devuelto **no es** el mismo objeto
   y **sí** tiene la misma huella. Las dos mitades hacen falta: sin la primera
   el doble sería `RepositorioEnMemoria` con otro nombre; sin la segunda, una
   aprobación caducaría cada vez que el veredicto diera una vuelta por la base.
2. `..._no_guarda_ni_un_veredicto_dentro`: la propiedad **por construcción**.
   Si mañana alguien le metiera el atajo de quedarse el objeto, el primer caso
   seguiría en verde y este no.
3. `..._sin_ficha_del_parte_no_devuelve_veredicto`: la consulta de verdad se
   ancla en `partes`, y el doble también (R8, R9).

### Fase RED

```
$ git stash push -- services/postventa-api/tests/utiles_pg.py
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py \
    -q --tb=line -p no:randomly -k "r23"

tests\test_f030_veredicto_persistido.py:103: in <module>
    from tests.utiles_pg import RepositorioComoLaBase, RepositorioEnMemoria
E   ImportError: cannot import name 'RepositorioComoLaBase' from 'tests.utiles_pg'
1 error in 0.25s
$ git stash pop
```

Es un rojo de «todavía no existe» y no demuestra gran cosa por sí solo: **el
rojo que vale para este doble es el de T18**, donde dos mutaciones de la
recomposición lo ponen en rojo por lo que de verdad viene a vigilar.

---

## T14 · el circuito entero, con los cuerpos reales — commit `79b603d`

`tests/test_f030_circuito_borde_a_borde.py`. El recorrido es
`POST /api/estado` → `POST /api/archivar`, **con los cuerpos que manda el
front**, sobre un parte **no apto con observaciones manuscritas**: el caso de
RS26.09/0178.

**La decisión de diseño que hace que este test valga algo**: el formulario del
archivo **dice la verdad** —`veredicto=no_apto`, `destino=cola_validacion_humana`,
que es lo que el front tiene de ese parte—, y el parte **se archiva igual**,
porque lo que decide es la aprobación de la persona. Antes de F-030, este
mismo formulario daba 409.

Cuatro casos:

| Caso | Qué fija |
|---|---|
| `r4_el_parte_que_una_persona_aprobo_se_archiva` | **El decisivo.** El parte se archiva, la biblioteca recibe el fichero y la traza queda en la base. |
| `r4_la_huella_apuntada_es_la_del_veredicto_que_vuelve_de_la_base` | El **porqué**, medido: la huella que apuntó `POST /api/estado` y la del veredicto recompuesto desde las columnas son la misma. |
| `r23_sin_aprobacion_el_archivo_no_pasa_la_puerta[sin_nada_en_la_base]` | Control negativo 1: de este parte no consta nada. |
| `r23_sin_aprobacion_el_archivo_no_pasa_la_puerta[guardado_pero_sin_aprobar]` | Control negativo 2, **el que caza el defecto**: el parte entró por `POST /api/parte`, el veredicto **está** en la base y lo que falta es la aprobación. |

> **Los dos mundos del control negativo, y por qué van los dos.** `design.md`
> §7.2 pedía «el mismo recorrido sin el paso 1». Ese mundo deja la base vacía y
> da «no consta que este parte haya pasado la validación», que es **otro**
> error: un endpoint que volviera a fabricar el veredicto desde el cuerpo
> seguiría pasando ese control. El segundo mundo —guardado por
> `guardar_parte_http` y sin aprobar— es el que da «la validación lo manda a
> «cola_validacion_humana» y no consta que nadie lo haya aprobado», que es la
> forma exacta de RS26.09/0178 menos la aprobación. Es un **refuerzo** de lo
> que pedía la spec, no un recorte.

En los dos negativos se afirma además que **no se tocó SharePoint**: ni una
llamada, ni un elemento, ni una carpeta. Un 409 después de haber subido el PDF
de un parte sin revisar sería el fallo de verdad.

### Fase RED · la comprobación de que el test caza el defecto

**(a) Devolviendo solo el stub a `archivar.py`, este test sigue en verde — y
está bien que así sea.**

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_circuito_borde_a_borde.py \
    tests/test_f030_veredicto_persistido.py -q --tb=line -p no:randomly

E   AssertionError: estos módulos del borde fabrican un ResultadoValidacion, y eso es
    exactamente lo que rompió el circuito en F-030 […] {'archivar.py': [213]}
FAILED tests/test_f030_veredicto_persistido.py::test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto
1 failed, 46 passed in 0.69s
```

El stub **solo** no reabre el defecto, porque T8 dejó la puerta ciega a
`ctx.validacion` (R1): aunque alguien vuelva a fabricar un veredicto en el
borde, la puerta no lo mira. Quien caza esa mitad es el **centinela estructural
de T12**, y lo hace nombrando fichero y línea. Eso **no es que el test de T14
no sirva**: es que hay dos defensas y cada una caza su mitad.

**(b) El defecto entero —el stub en `archivar.py` **más** la puerta leyendo
`ctx.validacion`— pone este test en ROJO, con el error de producción:**

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_circuito_borde_a_borde.py \
    -q --tb=short -p no:randomly

___________ test_f030_r4_el_parte_que_una_persona_aprobo_se_archiva ___________
tests\test_f030_circuito_borde_a_borde.py:365: in test_f030_r4_...
    respuesta = archivar_parte(
interface_adapters\api\archivar.py:119: in archivar_parte
    contexto = paso_archivo(
application\pipelines\paso_archivo.py:230: in _exigir_admitido
    exigir_parte_aprobado(
application\pipelines\puerta_de_estado.py:157: in exigir_parte_aprobado
    raise ParteNoApto(f"{motivo}, así que {y_por_eso}")
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo
    manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que
    no se archiva
_ test_f030_r23_sin_aprobacion_el_archivo_no_pasa_la_puerta[sin_nada_en_la_base] _
E   AssertionError: assert 'no consta que este parte haya pasado la validación' in
    'este parte está pendiente: la validación lo manda a «cola_validacion_humana» y
    no consta que nadie lo haya aprobado, así que no se archiva'
2 failed, 2 passed in 0.72s
```

**Es literalmente el error que dejó sin archivar el parte de RS26.09/0178.** Y
el segundo rojo es un regalo: con el defecto, un parte del que **no consta
nada** en la base recibe el error del veredicto que trae el cuerpo —el cuerpo
estaba concediendo el veredicto—, que es la segunda cara del agujero (§0.9).

Los dos cambios se deshicieron con `git checkout --` acto seguido; el árbol
quedó limpio y la suite en verde antes del commit.

---

## T15 · las otras dos puertas, en dry-run — commit `db15535`

Los equivalentes de `adjuntar_grafico` y `cerrar_incidencia` con `commit=False`,
sus dobles (`ErpEnMemoria`, `GraficoEnMemoria`, `UsuariosConLogin`,
`PreferenciasSinAutoCierre`) y **dos control-negativo cada uno**: seis casos.

Dos decisiones que son lo que hace que los negativos prueben lo que dicen:

1. **La puerta corta antes de cualquier otra comprobación**, y se afirma con
   `erp.lecturas == []`. Los dos pasos leen la reclamación **nada más** pasar
   la puerta, así que si no se leyó, la puerta cortó primero. Un parte sin
   aprobar no llega ni a mirar el ERP, y mucho menos a mandarle un documento
   con el DNI de un cliente dentro.
2. **En el caso del cierre, el gráfico consta adjuntado a propósito.** Así la
   puerta de F-012 no puede ser la que corte: si algo para el paso, es la del
   estado. Es la diferencia entre un control y una coincidencia.

> **Un aserto que hubo que afinar, y no es aflojarlo.** El final propio de cada
> puerta (R17) es el de la rama `pendiente` —«no se adjunta a la reclamación»—,
> pero la rama «no consta veredicto» tiene **su propio** final —«no se adjunta
> a una incidencia del ERP un parte del que nadie ha emitido veredicto»—. Se
> afirma el verbo común («no se adjunta») **y además** que no aparece el de
> otra puerta («no se archiva»), que es más fuerte que exigir una sola de las
> dos redacciones. El caso del archivo no lo necesitó porque las dos
> redacciones empiezan igual.

### Fase RED

Con el defecto entero reintroducido —stub en `adjuntar.py` y en `cerrar.py`
más la puerta leyendo `ctx.validacion`—:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_circuito_borde_a_borde.py \
    -q --tb=line -p no:randomly -k "r5 or r6 or r24"

E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo
    manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que
    no se adjunta a la reclamación
...puerta_de_estado.py:157
E   domain.models.errores.ParteNoApto: este parte está pendiente: la validación lo
    manda a «cola_validacion_humana» y no consta que nadie lo haya aprobado, así que
    no se cierra la incidencia
...puerta_de_estado.py:157
FAILED ...::test_f030_r5_el_parte_aprobado_se_adjunta_a_su_reclamacion_en_dry_run
FAILED ...::test_f030_r6_el_parte_aprobado_llega_al_dry_run_del_cierre
FAILED ...::test_f030_r24_sin_aprobacion_el_grafico_no_pasa_la_puerta[sin_nada_en_la_base]
FAILED ...::test_f030_r24_sin_aprobacion_el_cierre_no_pasa_la_puerta[sin_nada_en_la_base]
4 failed, 2 passed, 4 deselected in 0.63s
```

Los tres ficheros se restauraron con `git checkout --` acto seguido.

---

## T16 · compatibilidad hacia atrás — commit `61c2244`

**Es lo que el humano va a comprobar mañana con su parte.** Siete casos, y van
contra `RepositorioComoLaBase` y no contra un `SituacionParte` montado a mano,
porque lo que hay que demostrar es que la decisión sobrevive **al viaje por las
columnas**.

| Caso | Qué fija |
|---|---|
| `r11_una_decision_ya_guardada_sigue_aprobando_sin_volver_a_decidir` (×3) | La aprobación guardada abre **las tres puertas**, y la puerta **no apunta nada nuevo** en el histórico: lo suyo es dejar pasar o no, no decidir. |
| `r12_si_el_veredicto_guardado_cambia_la_aprobacion_deja_de_contar` (×3) | El parte se revalida con otra lectura → la huella deja de coincidir → vuelve a `pendiente`, con el destino **nuevo** en el mensaje. **Sin esta mitad, la primera podría estar pasando porque la huella no se compara en absoluto**, que sería peor que el defecto que se arregla. |
| `r12_la_huella_apuntada_deja_de_coincidir_cuando_cambia_el_veredicto` | El porqué, **medido**: las dos huellas, antes y después, y que son distintas. |

### Fase RED

Contra el código de antes de T8 (`puerta_de_estado.py` leyendo
`ctx.validacion`):

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py \
    -q --tb=line -p no:randomly -k "r11_una_decision or r12_si_el"

E   AssertionError: assert 'revision_manual' in 'este parte está pendiente: la
    validación lo manda a «cola_validacion_humana» y no consta que nadie lo haya
    aprobado, así que no se cierra la incidencia'
FAILED ...::test_f030_r11_una_decision_ya_guardada_sigue_aprobando_sin_volver_a_decidir[archivo]
FAILED ...::[grafico]   FAILED ...::[cierre]
FAILED ...::test_f030_r12_si_el_veredicto_guardado_cambia_la_aprobacion_deja_de_contar[archivo]
FAILED ...::[grafico]   FAILED ...::[cierre]
6 failed, 44 deselected in 0.45s
```

---

## T17 · el control de que no hay DDL — commit `8f95afd`

Tres casos, y van tres porque miran cosas distintas y fallan en sitios
distintos:

1. **el diff**: `git diff --name-only dev...HEAD` no toca
   `infrastructure/persistencia/sql/`;
2. **su control del control**: el diff no puede venir vacío y tiene que incluir
   `application/pipelines/puerta_de_estado.py`. Sin él, un diff vacío —rama
   equivocada, `dev` que ya lo contiene todo— pondría verde el primero sin
   haber comprobado nada;
3. **la mitad que no depende de `git`**: los ficheros de DDL son **los once de
   F-028 y ninguno más**, con la lista escrita a mano y no leída del árbol.

Los dos primeros **se saltan** —no fallan— si `git` no está o si `dev` no está
en el clon. Por eso existe el tercero: la regla más cara de deshacer no puede
quedarse sin vigilancia por un detalle del `checkout`.

### El diff de la rama, pegado

```
$ git diff --name-only dev...HEAD
BACKLOG.md
docs/ARCHITECTURE.md
harness/features.json
progress/current.md
progress/impl_F-030.md
progress/mutacion_F-030.md
services/postventa-api/application/pipelines/puerta_de_estado.py
services/postventa-api/domain/models/estado.py
services/postventa-api/domain/ports/persistencia.py
services/postventa-api/infrastructure/persistencia/mapeo.py
services/postventa-api/infrastructure/persistencia/repositorio_pg.py
services/postventa-api/infrastructure/persistencia/sentencias.py
services/postventa-api/interface_adapters/api/adjuntar.py
services/postventa-api/interface_adapters/api/archivar.py
services/postventa-api/interface_adapters/api/cerrar.py
services/postventa-api/tests/test_f005_logs_sin_datos_personales.py
services/postventa-api/tests/test_f005_mapeo.py
services/postventa-api/tests/test_f005_sentencias.py
services/postventa-api/tests/test_f006_archivar_http.py
services/postventa-api/tests/test_f006_paso_archivo.py
services/postventa-api/tests/test_f009_cerrar_http.py
services/postventa-api/tests/test_f009_logs_sin_datos_personales.py
services/postventa-api/tests/test_f009_paso_cierre.py
services/postventa-api/tests/test_f010_borde_persistencia.py
services/postventa-api/tests/test_f012_adjuntar_http.py
services/postventa-api/tests/test_f012_cerrar_exige_grafico.py
services/postventa-api/tests/test_f012_logs_sin_datos_personales.py
services/postventa-api/tests/test_f012_paso_grafico.py
services/postventa-api/tests/test_f019_orden_archivado.py
services/postventa-api/tests/test_f025_sin_dry_run_previo.py
services/postventa-api/tests/test_f026_puertas.py
services/postventa-api/tests/test_f028_estado_dominio.py
services/postventa-api/tests/test_f028_persistencia.py
services/postventa-api/tests/test_f028_puertas.py
services/postventa-api/tests/test_f030_circuito_borde_a_borde.py
services/postventa-api/tests/test_f030_veredicto_persistido.py
services/postventa-api/tests/utiles_pg.py
services/postventa-api/tests/utiles_sharepoint.py
services/postventa-api/tests/utiles_validacion.py
specs/F-030-veredicto-persistido/design.md
specs/F-030-veredicto-persistido/requirements.md
specs/F-030-veredicto-persistido/tasks.md
```

**42 ficheros, y ni uno de `infrastructure/persistencia/sql/`.** Nueve de
producción —los de los bloques 1 a 3—, uno de documentación, veintitrés de
tests y utillería, y el resto, memoria del arnés y spec.

### La comprobación en rojo, de verdad

Se creó `sql/12_inventado_para_el_control.sql` y se ejecutó:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py \
    -q --tb=line -p no:randomly -k "r20"

E   AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
      Left contains one more item: '12_inventado_para_el_control.sql'
FAILED tests/test_f030_veredicto_persistido.py::test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo
1 failed, 2 passed, 52 deselected in 0.53s
```

El fichero se borró acto seguido.

---

## T18 · cobertura y mutación — commit `237556e`

### Cobertura de las líneas cambiadas

```
[OK] PUERTA COBERTURA: 100.0% de 30 líneas cambiadas cubiertas (30/30, umbral 80%, nivel critico)
```

### Campaña automática

```
$ python -m harness.mutacion --feature F-030 --workers 8
F-030: 9 fichero(s), 419 línea(s) de producción
Campaña paralela: hasta 8 workers, uno por worktree.
[1/3] muerto  .../mapeo.py:427 [logico] numero_incidencia=numero_incidencia or "", -> ... and "",
[2/3] muerto  .../repositorio_pg.py:307 [entero] fila_a_validacion_y_cierre(filas[0], ...) -> filas[1]
[3/3] muerto  .../mapeo.py:426 [logico] codigo_obra=codigo_obra or "", -> codigo_obra=codigo_obra and "",
3 mutantes evaluados, 3 muertos, 0 supervivientes, 0 timeouts en 21.1 s
Informe: progress/mutacion_F-030.md
```

| Métrica | Valor |
|---|---|
| Líneas de producción en alcance | **419**, en 9 ficheros |
| Mutantes generados / evaluados | **3 / 3** |
| Muertos | **3** |
| **Supervivientes** | **0** |
| Timeouts | 0 |
| Tiempo total | **21,1 s** |
| **Workers** | **3** (se pidieron **8**; el arnés los resuelve a uno por mutante y lo deja escrito en `progress/mutacion_F-030.md`) |
| Muestreo | no: campaña completa |

**Sección de análisis de supervivientes: no hay ninguno**, así que no hay nada
que justificar ni ningún test que añadir por esa vía.

> **Lo que este número NO dice, y hay que decirlo.** Tres mutantes sobre 419
> líneas es poquísimo, y no es porque el código esté blindado: es que los
> operadores del arnés son pocos y la mayoría de esas 419 líneas son
> docstrings, comentarios de enmienda y firmas. **La campaña automática, sola,
> no acredita nada en esta feature.** Lo que la acredita son los tres mutantes
> a mano de abajo, que es justamente por lo que T18 los exige.

### Los tres mutantes a mano, los que reabren el defecto

Cada uno aplicado sobre el código real y evaluado contra **la suite entera del
servicio** (`pytest tests -q`), y deshecho acto seguido:

| # | Mutación | Casos que lo cazan | Veredicto |
|---|---|---|---|
| **M1** | `puerta_de_estado.py`: `validacion = ctx.situacion.validacion` → `ctx.validacion` | **84 failed**, 2 650 passed | **muerto** |
| **M2** | `mapeo.fila_a_validacion_y_cierre`: `observaciones=observaciones` → `observaciones=None` | **19 failed**, 2 715 passed | **muerto** |
| **M3** | `mapeo.fila_a_validacion_y_cierre`: `numero_incidencia=numero_incidencia or ""` → `numero_incidencia=""` | **18 failed**, 2 716 passed | **muerto** |

Lo que hay que mirar de esta tabla no es el número, es **quién** los caza:

- **M1** lo cazan, entre otros, los 6 de `r11_un_parte_no_apto_aprobado_a_mano`
  (el defecto original), los 6 de `r1_un_stub_...` (el blindaje de R1), los 6 de
  `r11`/`r12` de T16 y **los 4 casos del circuito de borde a borde**;
- **M2 y M3** los cazan los 7 de `r10_el_veredicto_recompuesto_da_la_misma_huella`,
  el caso propio del doble de T13 y **los cuatro casos buenos del circuito de
  T14/T15**, que es la prueba de que el test de borde a borde no es decorativo:
  una recomposición que pierda una columna del papel rompe la huella y el parte
  aprobado deja de archivarse, **exactamente** como en producción.

Tras deshacer M3, `mapeo.py` quedó marcado como modificado por un cambio de
fin de línea (el guion escribe con `\n` y el fichero está en CRLF); `git diff`
salía vacío y se restauró con `git checkout --`. **Ni una línea de producción
distinta.**

---

## T19 · `docs/ARCHITECTURE.md` y la nota de F-031 — commit `0a94f00`

El punto 3 de «Semántica de dominio imprescindible» gana su **cuarta capa**,
fechada y bajo el punto que enmienda:

> **Precisado por F-030 el 2026-09-16** […]: lo que decide si un parte entra en
> el circuito es el estado derivado **del veredicto que consta guardado** en
> `postventa.validaciones`, y de nada más. **Ningún endpoint del circuito emite
> veredicto** […] y **tampoco lo fabrican**.

Con el porqué —la aprobación que dejó de contar y el parte `b7e9b037` de
RS26.09/0178— para que quien lo lea entienda de dónde sale la regla. **No se
borra nada**: la regla general, la precisión de F-026 y la de F-028 siguen
enteras, y hay un caso que lo exige.

**Dos casos nuevos** (`r25`): uno afirma la precisión fechada y sus tres
afirmaciones; el otro es el **control negativo** que impide que «dejarlo
limpio» se lleve por delante las capas anteriores.

`test_f028_documentacion.py`, `test_f026_documentacion.py`,
`test_f009_documentacion.py` y `test_f012_documentacion.py`: **177 passed** con
los de F-030 incluidos.

### Fase RED

Con el `docs/ARCHITECTURE.md` de `dev` encima:

```
$ git show dev:docs/ARCHITECTURE.md > docs/ARCHITECTURE.md
$ ./.venv/Scripts/python.exe -m pytest tests/test_f030_veredicto_persistido.py \
    -q --tb=line -p no:randomly -k "r25"

E   AssertionError: assert 'Precisado por F-030 el 2026-09-16' in '3. **La firma debe
    ser humana.** Una casilla vacía, una aspa, o un trazo geométrico […]'
FAILED ...::test_f030_r25_el_punto_3_dice_de_donde_sale_el_veredicto
1 failed, 1 passed, 53 deselected in 0.36s
$ git checkout -- docs/ARCHITECTURE.md
```

El segundo caso pasa contra el documento viejo **a propósito**: es el control
negativo, y lo que vigila es que lo anterior siga ahí.

### La nota del riesgo §10.7, en `progress/current.md`

Queda anotado como **DADO DE ALTA**, no como pendiente de decidir:
`/api/archivar` sigue nombrando la carpeta y el fichero con el `codigo_obra` y
el `numero_incidencia` **del cuerpo**; hoy no hace daño porque el front manda
lo que leyó; **está en el backlog como `F-031`** (commit `11c04d0`, estado
`pending`). F-030 no lo cierra y no hay nada que proponer.

---

## T20 · el portero, en verde y con exit code 0

```
$ bash harness/init.sh ; echo "EXIT CODE: $?"
[OK] Arnés v1.5.2 (2026-08-18)
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea)
62 passed in 2.48s
[OK] pytest en verde (con medición de cobertura)
2736 passed, 13 skipped in 33.53s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 30 líneas cambiadas cubiertas (30/30, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-030-veredicto-persistido
ENTORNO LISTO. Puedes trabajar.
EXIT CODE: 0
```

### El recuento exacto

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests -q
2736 passed, 3 skipped in 21.22s
```

| | Antes del bloque 4 (`5a157c4`) | Ahora |
|---|---|---|
| Pasan | 2 711 | **2 736** |
| Fallan | 0 | **0** |
| Se saltan | 3 | 3 |

**+25 casos netos**, y son exactamente los nuevos: 3 de T13, 4 de T14, 6 de
T15, 7 de T16, 3 de T17 y 2 de T19. **Ningún caso pasó de verde a rojo, y
ningún test existente cambió de aserto en estos dos bloques.**

| Fichero | Resultado |
|---|---|
| `test_f030_veredicto_persistido.py` | **55 passed** (40 de los bloques 0–3 + 3 de T13 + 7 de T16 + 3 de T17 + 2 de T19) |
| `test_f030_circuito_borde_a_borde.py` | **10 passed** (4 de T14 + 6 de T15) |
| Los cuatro ficheros de documentación + F-030 | 177 passed |

La suite se ejecutó también **en orden aleatorio** (sin `-p no:randomly`):
mismo resultado.

---

## Evidencias (bloques 4 y 5)

Números **medidos**, no estimados.

| Evidencia | Valor medido | Cómo se obtuvo |
|---|---|---|
| Tests ejecutados (servicio) | **2 739**: 2 736 pasan, **0 fallan**, 3 se saltan | `cd services/postventa-api && python -m pytest tests -q` |
| Tests ejecutados (portero completo) | 2 736 pasan + 62 de la suite de la raíz, 13 se saltan | `bash harness/init.sh` |
| Tests nuevos de estos bloques | **25** (3 de T13, 4 de T14, 6 de T15, 7 de T16, 3 de T17, 2 de T19) | 2 736 − 2 711 del punto de partida |
| Tests que pasaron de verde a rojo | **0** | comparación de las dos salidas |
| Tests existentes con un aserto cambiado | **0** en estos dos bloques | diff de los ocho commits |
| **Cobertura de las líneas cambiadas** | **100,0 %** (30/30, umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **3 generados, 3 muertos, 0 supervivientes**, 21,1 s | `python -m harness.mutacion --feature F-030 --workers 8` → `progress/mutacion_F-030.md` |
| **Workers de la campaña** | **3** (pedidos 8; el arnés asigna uno por mutante) | cabecera de `progress/mutacion_F-030.md` |
| Mutantes **a mano**, los tres que reabren el defecto | **3 aplicados, 3 muertos**: M1 → 84 casos en rojo, M2 → 19, M3 → 18 | suite entera del servicio por cada uno |
| Tiempo de ejecución de la suite | **21,22 s** (servicio), **33,53 s** dentro del portero, **2,48 s** la suite de la raíz | las salidas de pytest de arriba |
| Avisos de lint | **61 antes, 61 ahora**: estos bloques no añaden ninguno. Los tres ficheros de tests tocados dan **0 avisos** por separado | `python -m ruff check .` y la línea `[AVISO] ruff` del portero |
| **DDL** | **Cero.** 42 ficheros en `dev...HEAD` y ninguno de `infrastructure/persistencia/sql/`; los ficheros de DDL siguen siendo los once de F-028 | `git diff --name-only dev...HEAD` y el test de T17 |
| Líneas de producción tocadas en estos bloques | **0** | el diff de los ocho commits |
| Exit code del portero | **0** | `bash harness/init.sh ; echo $?` |

---

## Desviaciones de la spec, declaradas

**1. El caso propio del doble de T13 vive en `test_f030_veredicto_persistido.py`
y no en el fichero nuevo.** T13 pedía «un caso propio» sin decir dónde, y T14
dice «**crear** `test_f030_circuito_borde_a_borde.py`». Ponerlo en el fichero
existente respeta las dos cosas y deja el fichero nuevo siendo lo que su nombre
dice: el circuito. Son tres casos y están bajo un encabezado «T13».

**2. El control negativo de T14 y T15 tiene DOS mundos, no uno.**
`design.md` §7.2 pedía «el mismo recorrido sin el paso 1», que deja la base
vacía. Se añadió el mundo que de verdad caza el defecto —el parte guardado por
`POST /api/parte` y **sin aprobar**—, porque con el primero a solas un endpoint
que volviera a fabricar el veredicto desde el cuerpo seguiría en verde. Es un
refuerzo, no un recorte: el mundo que pedía la spec sigue ahí, parametrizado.

**3. T19 trae dos casos de test que la tarea no pedía.** T19 solo pedía
actualizar `ARCHITECTURE.md` y verificar con los controles de documentación
existentes, pero **ninguno de ellos mira el párrafo nuevo**: sin los dos casos
de `r25`, la precisión de F-030 quedaría sin vigilancia mientras que las de
F-026 y F-028 la tienen. Se siguió el patrón que ya usan
`test_f026_documentacion.py` y `test_f028_documentacion.py`.

**4. La comprobación de T14 «devolviendo el stub a `archivar.py` el test se
pone rojo» **no** ocurre con el stub solo.** Está medido y explicado arriba: T8
dejó la puerta ciega a `ctx.validacion`, así que el stub solo lo caza el
centinela de T12. El rojo del test de borde a borde exige reintroducir **el
defecto entero** (stub + puerta), y ahí sale el error exacto de producción. La
spec daba por hecho un encadenamiento que el propio arreglo de T8 rompió —a
mejor—.

---

## Lo que queda para cerrar la feature

**Nada de implementación: T1–T20 están hechas y el portero está en verde con
exit code 0.** Falta el **APROBADO del reviewer** contra `CHECKPOINTS.md`; la
feature **no** se marca `done` antes de eso, y este implementer no la marca.

## Verificaciones MANUAL (humano) — **PENDIENTES**

Ninguna de las dos es condición de cierre —exigen el entorno desplegado o base
de datos real—, y **ninguna se ha ejecutado**: todo lo de estos dos bloques ha
corrido contra dobles en memoria.

### **V1 · el parte que está esperando**

Con F-030 desplegado en `dev`, archivar el parte **`b7e9b037`** de la incidencia
**RS26.09/0178** y comprobar que **se archiva sin volver a decidir nada**. Es la
prueba contra datos reales de lo que T16 demuestra contra columnas.

> ⚠️ **Escribe en SharePoint.** Exige **autorización expresa del humano para esa
> incidencia** y **no se hace desde local**: `CLAUDE.md` lo prohíbe. La ventana
> `ARCHIVO_HABILITADO` de `dev` está **abierta** ahora mismo, y cada despliegue
> del backend vuelve a cerrarla (`infra/desplegar_backend.ps1`), así que hay que
> comprobarla con `infra/22_ventana_archivo.ps1 -Estado` antes de intentarlo.

### **V2 · el coste, medido**

Contar las consultas de una tanda real de **22 partes** contra el PostgreSQL
compartido `psql-albaranes-rs9k2` y comprobar que **no ha subido** respecto a
F-028 (R18). Continúa la verificación que dejó abierta F-028 §11.1.

> El diseño dice que no puede subir —el veredicto viaja **dentro** de la
> consulta de situación que las tres puertas ya hacían, y hay un test que
> comprueba que ya no se ejecuta `FROM postventa.cierres` en ese camino—, pero
> eso es la garantía de un doble, no una medida contra la base real.

**Aviso de entorno vigente:** `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` están
**las dos abiertas** en `dev`. Si no hay una sesión de verificación en curso,
procede cerrarlas (`infra/19_ventana_escritura.ps1 -Cerrar` y
`infra/22_ventana_archivo.ps1 -Cerrar`). **Decisión del humano, no de un
agente.**
