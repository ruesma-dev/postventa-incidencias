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
