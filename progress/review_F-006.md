<!-- progress/review_F-006.md -->
# Review F-006 · Nombrado y archivo en SharePoint

> Informe escrito **de forma incremental**, conforme verificaba, no al final.
> **TERMINADO** el 2026-08-20.

- **Veredicto: `CHANGES_REQUESTED` (RECHAZADO).**
- **Rama:** `feature/F-006-sharepoint`
- **Rigor declarado:** `critico` (`features.json`) → exige fase RED, puerta de
  cobertura, campaña de mutación con **cero supervivientes** o análisis escrito
  **aceptado por el humano**, y verificaciones `MANUAL (humano)` con su comando
  exacto y su resultado real.

### Por qué se rechaza, en cuatro líneas

**No por la implementación, que es buena.** El código, los tests, la campaña de
mutación y la documentación están bien, y lo he verificado ejecutando, no
leyendo. Se rechaza por tres cosas concretas y baratas de arreglar:

1. **Hay un identificador real de la aplicación de Azure en el repositorio**
   (`progress/current.md:121`), y el guardián que debía impedirlo no mira
   `progress/`. Es lo único que toca arreglar de verdad.
2. **Faltan dos firmas del humano** que el nivel `critico` no me deja suplir:
   cerrar con **T18** pendiente ante C5, y **aceptar** el análisis de los cinco
   mutantes supervivientes. La propia spec dice que sin ellas el veredicto
   correcto es `CHANGES_REQUESTED`, y `progress/current.md` las seguía listando
   como pendientes el 2026-08-20.
3. `progress/current.md` arrastra el estado de la sesión de F-005 y se
   contradice (C2).

Con esas tres cosas resueltas, **esta feature está aprobada**: no pido ni un
cambio en el código de producción.

## Verificaciones realizadas

### V1 · `bash harness/init.sh` — [x] verde (exit 0)
Salida real: arnés v1.5.2, features.json válido, BACKLOG al día, compileall
sin errores, 16 tests de raíz en verde, servicio `api` en verde (**por
caché**: «árbol sin cambios desde el último verde»), PUERTA COBERTURA
**[OK] 98.2% de 342 líneas cambiadas (336/342, umbral 80%, nivel critico)**,
rama correcta. Aviso no bloqueante: ruff con 56 avisos de deuda previa.
Pendiente: relanzar la suite del servicio sin caché (V2).

### V2 · Suite del servicio relanzada por mí, sin caché — [x] verde
`services/postventa-api/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`
→ **895 passed, 10 skipped in 14.68s** (exit 0). Coincide exactamente con los
895 tests que declara el implementer. Los 10 `skipped` son la suite de base
efímera de F-005, apagada sin su variable de entorno (comportamiento previsto
por F-005, no un test silenciado por F-006).

### V3 · Barrido de identificadores (lo hago yo, no me fío del informe)

Patrones: GUID `[0-9a-f]{8}-...-[0-9a-f]{12}`, `SHAREPOINT_*`, `GRAPH_*`,
`tenant`, `appId`, `client_secret`, IP privadas, `.sharepoint.com`,
`onmicrosoft.com`, correos.

**HALLAZGO BLOQUEANTE (H1).** `progress/current.md:121` contiene un
identificador **real**:

```
- **App registration `postventa-incidencias`**, appId (enmascarado por el líder),
  con service principal y consentimiento de administrador.
```

- Está bajo el epígrafe «Lo verificado en Azure el 2026-08-20», es decir, es
  el appId **de verdad**, no un ejemplo inventado.
- Contradice frontalmente lo que la propia feature promete: `design.md` §9
  («**No escribe ningún identificador** —ni de aplicación, ni de tenant, ni de
  sitio, ni de biblioteca— en ningún fichero del repositorio, ni siquiera para
  documentar este riesgo») y R29.
- Entró en el commit **`f2e317b`** («F-005: cierre documental y alta de
  F-018»), que **ya está en `dev`**: no lo introdujo el implementer de F-006.
  Pero la rama lo arrastra, F-006 **modificó ese mismo fichero** en `b14c929`
  y el barrido de la feature no lo vio.
- **Por qué el guardián no lo cazó**:
  `test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador`
  barre solo `_ficheros_del_servicio()` (`services/postventa-api/`). `progress/`
  y la raíz del repositorio quedan fuera del barrido.

**Hallazgo menor (H2).** El GUID inventado de la traza de rotura de T13
(`b7e41c92-…`) sigue en el **historial** de la rama (commit `781d89b`);
`1d4885e` lo enmascara solo en `HEAD`. Enmascarar después no lo saca del
historial. Gravedad baja (es fabricado y con forma evidente de ejemplo), misma
situación que el FQDN de F-005: **se resuelve mergeando con squash**.

Sin hallazgos: ni site id, ni drive id, ni tenant, ni secreto, ni URL de
SharePoint real en el árbol. `.env.example` y `local.settings.json.example`
llevan placeholders, y hay test que lo comprueba (R29). Los dos GUID que
quedan en `services/postventa-api/tests/` son **controles negativos de F-005**
(`00000000-0000-4000-8000-000000000000` y un uuid de ejemplo), acotados a dos
ficheros y a uno por fichero por `test_f006_r26_la_excepcion_de_f005_no_crece_sin_que_se_vea`.

### V4 · Campaña de mutación **reejecutada** (no me fío del recuento del informe)

El informe declara «Tiempo total 247.0 s» — **por debajo de 5 minutos**, así que
`CHECKPOINTS.md` C4 bis obliga a reejecutar la campaña entera, no solo a
recalcular. Ejecutado:

```
python -m harness.mutacion --feature F-006 --salida <scratchpad>/mutacion_verif/mutacion_F-006.md
→ 64 mutantes evaluados, 59 muertos, 5 supervivientes, 0 timeouts en 257.0 s
```

**Coincide exactamente** con el informe del implementer (64 / 59 / 5 / 0), y el
alcance recalculado también: 11 ficheros, 1619 líneas, base
`f2e317b2…` .. `feature/F-006-sharepoint`. Los cinco supervivientes son
**los mismos cinco**: `config/settings.py:285` y `:293`,
`infrastructure/sharepoint/graph.py:112`, `:362` y `:380`.

La salida fue **fuera de `progress/`** y `git status` queda **limpio** después.

**Reparto de los 64 mutantes por fichero, del recuento independiente:**

| Fichero | Muertos | Supervivientes |
|---|---|---|
| `domain/models/nombrado.py` | 11 | **0** |
| `application/pipelines/paso_archivo.py` | 7 | **0** |
| `infrastructure/sharepoint/fabrica.py` | 3 | **0** |
| `infrastructure/sharepoint/graph.py` | 24 | 3 |
| `interface_adapters/api/archivar.py` | 6 | 0 |
| `function_app.py` | 6 | 0 |
| `config/settings.py` | 1 | 2 |
| `domain/ports/archivo.py` | 1 | 0 |

Queda **verificado de forma independiente** —no leído del informe— que
**el nombrado, la puerta de entorno (`fabrica.py`) y la idempotencia
(`paso_archivo.py`) no tienen ni un superviviente**. Entre los muertos que
comprobé uno a uno en la salida:
`paso_archivo.py:146 or→and` (la puerta de aptitud), `:177` y `:178`
(las dos condiciones de `_ya_archivado`).

---

## Los cinco supervivientes, juzgados uno a uno

Los acepto **todos como equivalentes o constantes de operación**, con matices.
Ninguno exige un test. Razonamiento propio, no el del implementer:

**1 · `config/settings.py:285` — `GRAPH_TIMEOUT_S` `default=60→61`. ACEPTADO.**
Ningún requisito fija 60. R25 exige *qué* se reintenta, no cuántos segundos se
espera. Un `assert graph_timeout_s == 60` sería un detector de cambios: se
actualiza sin pensar el día que alguien afine el número, y entonces protege
cero. La propiedad que sí importaría (`timeout × reintentos < 230 s`, el corte
de la Function) se cumple con 60 (180 s) y con 61 (183 s). Sin riesgo residual.

**2 · `config/settings.py:293` — `GRAPH_REINTENTOS` `default=3→4`. ACEPTADO.**
Comprobado que lo que dice el implementer es cierto y no una excusa: el
comportamiento **sí** está fijado, y con el número **pasado explícitamente**,
no leído del defecto —`test_f006_r25_agotados_los_reintentos_sale_archivo_fallido`
usa `reintentos=3` y cuenta las llamadas—, y los mutantes de la lógica de
reintento (`CODIGOS_TRANSITORIOS`, `in CORRECTOS or in tolerados`) **mueren
todos**. Lo que sobrevive es solo el valor por omisión del despliegue.

**3 · `graph.py:112` — `MARGEN_DE_TOKEN_S = 60→61`. ACEPTADO, con reserva
metodológica.** Es matable en teoría: un token con `expires_in = 61` distingue
60 de 61. Pero ese test tendría un presupuesto de **un segundo de reloj real**
entre dos llamadas, y bajo la propia campaña de mutación (16 procesos) fallaría
de vez en cuando. Comparto el criterio: un test inestable es peor que ninguno.
**La reserva**: la salida limpia no es «no hay test posible» sino **inyectar el
reloj** en el adaptador, como ya se inyecta el cliente HTTP. Lo dejo como
sugerencia para quien toque este fichero, **no** como cambio requerido: el
margen es una constante de operación y 60 o 61 protegen igual.

**4 · `graph.py:362` — `<` → `<=` sobre `time.monotonic()`. ACEPTADO, es
equivalente estricto.** Solo difieren si dos flotantes de resolución de
nanosegundos, calculados en instantes distintos, coinciden bit a bit. No hay
entrada que lo provoque de forma determinista con el reloj real. Y aunque
ocurriera, el efecto es usar el token un instante más, dentro de un margen de
60 s. **Lo importante lo verifiqué aparte**: los dos mutantes que sí eran
peligrosos en esta misma línea —`and`→`or`, y el signo del margen— **están
muertos**, y los matan dos tests nuevos que la campaña obligó a escribir.

**5 · `graph.py:380` — `expires_in` de reserva `3599→3600`. ACEPTADO.**
Camino de salvaguarda: solo entra si Entra incumple su contrato y omite
`expires_in`. Es matable con una aserción de caja blanca sobre
`_token_expira_en`, pero sería exactamente el detector de cambios del punto 1,
sobre un atributo privado y con un número mágico. Un segundo dentro de una hora,
absorbido por el margen de 60 s.

**Lo que de verdad importaba, verificado por mi cuenta y no leído del
informe**: en `nombrado.py` (11 mutantes), `paso_archivo.py` (7) y
`fabrica.py` (3) **no sobrevive ni uno**. El nombrado, la idempotencia y la
puerta de entorno están cerrados.

> **Aviso para el humano**: el nivel `critico` no me deja cerrar esto solo.
> «Cero supervivientes **salvo justificación escrita aceptada por el humano**».
> Yo firmo que los cinco análisis son correctos y suficientes; **la aceptación
> es tuya** y hoy no consta por escrito en `progress/`.

---

## Las tres desviaciones de la spec, juzgadas

**(a) La lista blanca de T13 con dos ficheros en vez de uno — LEGÍTIMA, y
además endurece.** Verificado el conflicto que alega: T9 obliga a crear
`test_f006_adaptador_graph.py` con `ENTORNO=dev` y T13 autorizaba solo
`test_f006_fabrica.py`. Es una inconsistencia entre dos tareas de la propia
spec, no una relajación. Y la comprobación añadida es **más fuerte** que la
que pedía la spec: `test_f006_r21_el_adaptador_de_los_tests_siempre_lleva_un_cliente_falso`
recorre con `ast` **todas** las construcciones del adaptador y exige `cliente=`
y `entorno=` en cada una. El invariante pasa de «qué fichero puede nombrar la
clase» a «ninguna construcción de la suite puede llegar a la red», que es el
que importa. Leído el test: hace lo que dice.

**(b) `CuerpoDeArchivoInvalido` — LEGÍTIMA.** R31 exige 400 cuando «el cuerpo no
cumple el contrato», y un `veredicto` o `destino` con un valor que el dominio no
reconoce es exactamente eso. `design.md` §3.2 enumeraba cinco errores y se
quedó corto. Las tres alternativas que descarta son peores, y la peor de todas
—tratar el valor desconocido como apto— habría archivado un parte sin
validación. Error nuevo, en `domain/models/errores.py`, con la misma forma que
los demás: no rompe nada.

**(c) `item_id` y el aviso «ya archivado» no observables desde el endpoint —
LEGÍTIMA como desviación, pero deja un hueco funcional que hay que decir en voz
alta.** Confirmado leyendo `interface_adapters/api/archivar.py`: el handler
compone `construir_archivador` y `construir_repositorio`, pero **nunca lee una
traza previa**, así que `traza_previa` llega siempre a `None`. Consecuencia:
**la capa L1 de idempotencia (R14) es hoy inalcanzable desde el único punto de
entrada del sistema**. Está implementada y probada en la aplicación
(`test_f006_r14_*` en verde), pero en producción no la ejerce nadie.

- **No es un requisito incumplido a efectos de C4**: R14 tiene su test
  trazable y pasa, y el `acceptance` «reprocesar no duplica» lo cumple la capa
  **L2** (reemplazo), que sí está en el camino real y cuyos mutantes mueren.
- **Es coherente con el diseño aprobado**: D4 y D5 de `design.md` §10 dicen que
  leer la traza exigiría un método nuevo en `RepositorioPartesPort`, que es de
  **F-005**, y F-006 no cambia specs ajenas.
- **Pero cuesta una llamada de más a Graph por cada reproceso**, y eso hay que
  recogerlo. Lo dejo como **deuda con dueño**: quien haga **F-007** (reintento
  desde el front) o **F-010** necesita el método de lectura de traza en el
  puerto de F-005. Recomendación: darlo de alta antes de cerrar F-006 para que
  no se pierda. **No lo convierto en bloqueo.**

Que el script de T18 compare `web_url` en vez de `item_id` es correcto: R30 fija
seis claves «y nada más», e `item_id` no es una de ellas. Comprobar lo que el
sistema garantiza en vez de lo que la tarea imaginó es lo que hay que hacer.

---

## Los tres bugs que destapó la campaña, verificados

No me creo «se corrigió»: leí el código y los tests.

**1 · La puerta de aptitud (`or`→`and`) — CORREGIDA DE VERDAD.** El bug era
real y grave: con `and`, un parte con `veredicto=APTO` y
`destino=COLA_VALIDACION_HUMANA` **se habría archivado**, que es literalmente lo
que prohíbe `CHECKPOINTS.md` C3 («nada se archiva sin haber pasado todas las
validaciones»). Los dos tests nuevos —
`test_f006_r17_un_veredicto_apto_con_otro_destino_tampoco_se_archiva` y
`test_f006_r17_un_destino_de_archivo_con_veredicto_no_apto_tampoco`— fijan
**una mitad cada uno** del `or`, y cada uno afirma explícitamente que la otra
condición sí se cumple (`assert ctx.validacion.veredicto == Veredicto.APTO`),
que es lo que impide que el test se degrade. Además comprueban
`archivador.llamadas == []`: no se toca el puerto. En mi campaña independiente,
el mutante `paso_archivo.py:146 or→and` sale **muerto**.

**2 · La caché del token — CORREGIDA DE VERDAD.** El fallo (usar un token
vencido) produce en producción un `401`, que por R25 **no se reintenta**: el
parte no se archiva. Los dos tests nuevos son la pareja correcta:
`expira_en=0` mata tanto el `and`→`or` como el signo del margen (con cualquiera
de los dos, la segunda llamada reutilizaría el token y saldría 1 petición en vez
de 2), y `expira_en=3600` impide la «corrección» perezosa de pedir el token
siempre. Uno solo de los dos no bastaría; los dos juntos, sí.

**3 · `con_token`, parámetro muerto — ELIMINADO.** Correcto: no hay test que
pueda matar código que no hace nada, y la campaña lo señaló por eso. Bien visto
también quitar los valores por defecto de `timeout_s` y `reintentos` en el
adaptador: la fábrica es el único constructor y los pasa siempre; un defecto que
nadie usa es una segunda fuente de verdad esperando a divergir.

**Y la lección de método que el implementer anota, que suscribo**: un test que
se compara contra la constante que vigila (`assert cliente.timeout.connect ==
TIMEOUT_DE_CONEXION_S`) **sigue al mutante** y da verde con la constante rota.
Los literales van escritos a mano.

---

## Las cuatro decisiones del humano del 2026-08-20

| Decisión | ¿Aplicada? | Dónde lo comprobé |
|---|---|---|
| **D-a** · `httpx` en vez de `msal`+`requests` | **[x]** | `requirements.txt` declara `httpx`; ni `msal` ni `requests` aparecen en el servicio; el adaptador usa `httpx.Client`; el test R22 vigila los tres nombres. Cambió **solo** `infrastructure/sharepoint/`, como predijo D1 |
| **D-b** · T19 **N/A** (el humano no commitea en `azure-apps`) | **[x]** | `tasks.md` T19 tachada y marcada `N/A · DECISIÓN DEL HUMANO DEL 2026-08-20`, con la fecha en la propia tarea; `progress/current.md` la da por cerrada y no reproponible. T15 sí se hizo |
| **D-c** · Riesgo de permisos escrito y con dueño | **[x]** | `design.md` §9 «Riesgo 7 · ACEPTADO por el humano el 2026-08-20», citando **F-018** por identificador; `docs/INTEGRACION.md` §3 (líneas 106-118 y 148-151), mismo contenido y mismo dueño. **F-018 existe** en `features.json` |
| **D-d** · T17 preparada (D6 resuelta) | **[x]** | `tasks.md` T17 `MANUAL (humano) · LISTA PARA EJECUTAR`, con los comandos partidos para PowerShell (que no admite `&&`), qué se espera ver, y la advertencia de que el aviso amarillo de permisos **debe** salir. `infra/verificar_destino_sharepoint.ps1` es de solo lectura, y hay test que lo comprueba |

Las cuatro están aplicadas **y fechadas**. Nada que objetar.

---

## Ninguna subida real: verificado, no supuesto

- **Puerta 1** (constructor): `AdaptadorSharePointGraph.__init__` muerde si
  `entorno not in ("dev","pro")`. `tests/conftest.py` fija `ENTORNO=test` para
  toda la suite (fixture `autouse`).
- **Puerta 2** (fábrica): `construir_archivador` es fail-closed y
  `archivo_habilitado` vale `False` por defecto. Sus 3 mutantes mueren.
- **Puerta 3** (red): `tests/conftest.py` sustituye `socket.socket.connect` en
  toda la sesión. **`git diff dev...HEAD -- tests/conftest.py` está vacío**: la
  guardia de F-003 no se ha tocado ni aflojado, como exigía `design.md` §3.3.
- **Todas** las construcciones del adaptador en la suite pasan `cliente=` (el
  doble), verificado con `ast` por un test, y solo dos ficheros pueden nombrar
  la clase.
- Los tests de `infra/*.ps1` **leen** los scripts, no los ejecutan
  (`read_text`): ni un `subprocess`, ni un `powershell`.
- La suite entera pasa con la guardia de red puesta: 895 en verde.

**Conclusión: ninguna subida real, ni desde local ni desde los tests.** El
criterio de aceptación 4 se cumple **porque el código lo impide**, no por
costumbre.

---

## Trazabilidad requisito → test

Comprobado **programáticamente**, no a ojo: los **32** requisitos R1–R32 de
`requirements.md` declaran 45 tests entre todos, y los **45 existen** en
`services/postventa-api/tests/` con el nombre exacto declarado. Cero huecos.
Y los 895 tests del servicio pasan, así que todos ellos pasan.

| Bloque | Requisitos | Fichero de tests |
|---|---|---|
| Nombrado (dominio puro) | R1–R9 | `test_f006_nombrado.py` |
| Carpeta, idempotencia, aptitud, traza | R10–R18, R23, R24, R27 | `test_f006_paso_archivo.py` |
| Adaptador de Graph | R11, R12, R15, R16, R25, R26 | `test_f006_adaptador_graph.py` |
| Puertas de entorno y configuración | R19, R20, R28 | `test_f006_fabrica.py` |
| Borde HTTP | R30, R31 | `test_f006_archivar_http.py` |
| Arquitectura, datos personales, ejemplos, INTEGRACION | R21, R22, R26, R29, R32 | `test_f006_arquitectura.py` |

---

## Los checkpoints, uno a uno

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit code 0 (V1).
- [x] Existen los siete ficheros exigidos.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: F-006.
- [x] Rama actual `feature/F-006-sharepoint`.
- [ ] **`progress/current.md` describe SOLO la sesión activa.** No lo cumple:
      arrastra el bloque de cierre de F-005 («**No hay ninguna feature
      `in_progress`**», «F-006 … `spec_ready`», la sección «⚠️ Lo primero: el
      merge de F-005 a `dev`, CON SQUASH») **debajo** del bloque nuevo de
      F-006. Dos estados contradictorios en el mismo fichero, y el obsoleto es
      el que dice que no hay nada en curso. Es del líder, no del implementer,
      pero C2 lo pide y hoy está vacío.
- [x] Toda feature `done` tiene su resumen en `history.md` (F-006 aún no es
      `done`, así que no aplica todavía).

### C3 — El código respeta arquitectura y convenciones
- [x] Hexagonal respetada, y **verificada por tests con `ast`**, no a ojo:
      `domain/` y `application/` no importan `httpx`, `msal`, `requests` ni
      `infrastructure`; el único paquete que conoce Graph es
      `infrastructure/sharepoint/`.
- [x] Primera línea con la ruta relativa en los **diez** ficheros nuevos
      (comprobado uno a uno, `.ps1` incluidos).
- [x] Sin `print()` de debug, sin TODO/FIXME nuevos (barrido sobre el diff).
- [ ] **Sin secretos ni identificadores hardcodeados: NO se cumple.** Ver
      **H1**: `progress/current.md:121` lleva el appId real de la aplicación.
- [x] La unidad de trabajo es el **parte**: el endpoint es un parte por
      llamada, la identidad es el `hash` del parte troceado de F-002.
- [x] **Nada se archiva sin haber pasado las validaciones**: la puerta de
      aptitud es lo primero del paso, antes de nombrar y antes de tocar el
      puerto, y sus dos mitades tienen test desde la campaña de mutación.
      Nada contra Sigrid en esta feature.
- [x] Lo manuscrito no se descarta (F-006 ni lo mira; el endpoint
      deliberadamente **no** pide DNI ni observaciones, para que no viajen).
- [x] Firmado no es conforme: lo decide F-004 y F-006 lo respeta leyendo su
      `Destino`.
- [x] **Reprocesar no duplica**: L2 (reemplazo) en el camino real, con doble
      que **renombraría** como lo haría el servicio de verdad; L1 y L3 además.
      Ver el matiz de la desviación (c).
- [x] Ningún número de estado de Sigrid: N/A aquí, no se toca Sigrid.
- [x] Ningún PDF ni documento con datos personales entró en git
      (`git log dev..HEAD --diff-filter=A`: cero binarios).

### C3 bis — Documentos de fuera
**N/A justificado**: el diff `dev...HEAD` no toca **ni un fichero** de
`docs/referencia/`. Aun así ejecuté el barrido de datos sensibles sobre toda la
rama (V3), porque lo pedía el encargo: resultado en **H1** y **H2**.

### C4 — La verificación es real
- [x] Los 32 requisitos con test trazable, los 45 tests existen y pasan.
- [x] Los unit tests no tocan red ni BBDD: guardia de `socket` intacta, dobles
      en el propio test, 10 skips que son la suite de base efímera de F-005.
- [x] Las verificaciones `MANUAL (humano)` están en `progress/current.md` con
      su comando exacto (T17) y con su motivo de aplazamiento (T18).

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado en `features.json`.
- [x] **Fase RED**: seis fases con **traza real pegada** (T2, T4, T6, T9, T11
      por código inexistente; T13 por rotura deliberada en copia aislada, con
      las tres roturas y sus cuatro fallos). Leída la de T2 y la de T13: son
      salidas reales de `pytest`, no frases.
      *(Detalle menor: la sección «Evidencias» dice «Las diez fases RED» y
      enumera seis. Es un error de redacción del informe, no de sustancia.)*
- [x] **Cobertura**: `PUERTA COBERTURA [OK] 98.2% (336/342, umbral 80%)`.
- [x] **Mutación verificada de forma independiente**: alcance y nº de mutantes
      recalculados **y campaña reejecutada entera** (V4).
- [x] **Los muertos están comprobados, no solo contados**: el informe declara
      247 s (< 5 min), así que reejecuté la campaña completa. 64/59/5/0 en
      257 s, mismos cinco supervivientes, salida fuera de `progress/`, árbol
      limpio después.
- [ ] **Cero supervivientes salvo justificación aceptada por el humano.** Los
      cinco análisis están **completos** (ninguno `PENDIENTE`) y yo los doy por
      **correctos y suficientes**; lo que falta es la **aceptación del humano**,
      que el nivel `critico` exige por escrito y que hoy no consta.
- [x] Sección **«Evidencias»** con los cuatro números (tests, cobertura,
      mutantes/supervivientes, tiempo de suite) y algunos más.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles
**N/A justificado**: este repositorio **no tiene** `harness/rutas_sensibles.json`
(comprobado: el fichero no existe), y sin declaración el bloque es N/A por
diseño del propio arnés.

### C5 — La sesión se cerró bien
- [ ] **`tasks.md` con todas las tareas `[x]`.** 19 de 21. **T17** `[ ]` (es
      `MANUAL (humano)`, entregada y lista) y **T18** `[ ]` (`MANUAL (humano)`,
      diferida a F-010). Ver el apartado siguiente: **es aprobable, pero no por
      mí solo**.
- [x] Un commit `F-006 Tn: ...` por tarea: 30 commits en la rama, todos con el
      prefijo `F-006` salvo los dos de traer F-004 y F-005 (la precondición T1),
      que son legítimos.
- [x] Sin ficheros temporales ni artefactos sospechosos: `git status` limpio;
      `coverage.json` está ignorado por `.gitignore`.
- [x] `features.json` refleja el estado real (`in_progress`).

---

## C5 con T18 pendiente: mi respuesta explícita

El encargo pide que lo diga sin rodeos, así que:

**No es un defecto técnico y no bloquea por sí mismo.** T18 no está sin hacer
por descuido ni por pereza: no **se puede** hacer. Exige un entorno desplegado
que crea **F-010**, y la única alternativa —subir desde local— la prohíbe
`CLAUDE.md` sin matices. El trabajo entregable de T18 (el script
`infra/verificar_archivo_dev.ps1`, con su contrato fijado por tests) **sí está
entregado**. T17 igual: entregada, desbloqueada y con su comando exacto; queda
`[ ]` solo porque la ejecuta una persona.

**Pero C5 exige todas las tareas `[x]`, y el nivel `critico` exige las
verificaciones manuales «con su resultado real».** El arnés, tal y como está
escrito hoy, no distingue «tarea de agente sin hacer» de «verificación humana
aplazada por una dependencia declarada». Esa distinción es exactamente **F-017**.

**Por tanto: es aprobable con autorización expresa del humano, y solo con
ella.** No la puedo dar yo, y **no la da el líder al encargarme la revisión**:
lo dice la propia spec —«Ese cierre lo autoriza el humano, no el arnés. Sin esa
autorización por escrito, el veredicto correcto del reviewer es
`CHANGES_REQUESTED`»— y lo repite `progress/current.md`, que el **2026-08-20**
seguía listando esa autorización como **pendiente**. La decisión **D3** del
2026-08-19 autoriza **aplazar T18**; en su propio texto reconoce que el cierre
necesita **además** una autorización ante C5. Hoy esa segunda firma no existe en
`progress/`.

**Lo que hace falta, en una línea**: que el humano escriba en `progress/` que
autoriza cerrar F-006 con T18 pendiente y que acepta el análisis de los cinco
supervivientes. Con eso, y con **H1** corregido, esta feature está aprobada.

---

## Cambios requeridos

1. **Quitar el appId real de `progress/current.md:121`** (H1). La línea «App
   registration `postventa-incidencias`, appId (enmascarado por el líder)» debe quedar sin el
   valor: basta con nombrar el registro. Es un identificador de una aplicación
   que **hoy tiene `Sites.FullControl.All` sobre todo el inquilino**, lo que lo
   hace menos inocuo de lo que parece, y contradice literalmente lo que promete
   `design.md` §9. **Cuidado**: entró en `f2e317b`, que **ya está en `dev`**;
   quitarlo del árbol no lo saca del historial, así que hay que decírselo al
   humano para que decida si además hay que rotar algo o limpiar el historial.
2. **Tapar el hueco del barrido que dejó pasar H1**:
   `test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador` solo
   mira `services/postventa-api/`. Ampliarlo a `progress/`, `docs/`, `infra/`
   y la raíz —o añadir un test hermano que lo haga— para que el guardián cubra
   donde de verdad se escriben los identificadores: los informes. Sin esto, el
   mismo fallo vuelve en la siguiente feature.
3. **Autorización del humano, por escrito en `progress/`**, de las dos cosas
   que el nivel `critico` no me deja firmar solo: (a) cerrar con **T18**
   pendiente ante C5, y (b) **aceptar** el análisis de los cinco supervivientes.
   No es trabajo del implementer: es la firma que falta.
4. **Limpiar `progress/current.md` de la sesión anterior** (C2): el bloque de
   cierre de F-005 dice «no hay ninguna feature `in_progress`» y «F-006 está
   `spec_ready`», que hoy es falso. Dejar solo la sesión activa.

**Nada de esto toca el código de producción de F-006.** Dicho claramente: la
implementación, los tests, la campaña y la documentación **están bien**; lo que
falta es higiene de un dato en `progress/` y dos firmas.

---

## Recomendaciones (no bloquean)

- **Mergear a `dev` con squash**, por el mismo motivo que se decidió en F-005:
  el GUID de ejemplo de la traza de T13 (**H2**) sigue vivo en el historial de
  la rama aunque `1d4885e` lo enmascare en `HEAD`.
- **Recoger la deuda de la desviación (c)**: la capa L1 de idempotencia no la
  ejerce nadie hoy porque el endpoint no lee la traza previa. Darlo de alta
  como criterio de **F-007** o como feature propia, con el método de lectura en
  el puerto de F-005.
- **Inyectar el reloj** en `AdaptadorSharePointGraph`, como ya se inyecta el
  cliente HTTP: convertiría dos de los cinco supervivientes en matables sin
  tests inestables. Trabajo de quien toque ese fichero, no de F-006.
- Corregir «Las diez fases RED» → «Las seis fases RED» en la sección
  «Evidencias» de `progress/impl_F-006.md`.

---

## Automejora del protocolo (propuesta, no aplicada)

**P1 · El barrido de identificadores del reviewer debe cubrir `progress/`, no
solo el código.** Este review lo demuestra: el único identificador real del
repositorio estaba en un informe, que es justo donde un agente escribe «lo
verificado en Azure». Propongo añadir a **C3** de `CHECKPOINTS.md` una línea
explícita: «el barrido de secretos e identificadores se ejecuta sobre **todo**
el árbol, informes de `progress/` incluidos, y su resultado consta en el
informe de review». Es genérica: vale para cualquier proyecto, así que si se
acepta viaja a `arnes-base` en el mismo trabajo.

**P2 · C5 debe distinguir la tarea de agente pendiente de la verificación
`MANUAL (humano)` aplazada.** Ya está dada de alta como **F-017**; este review
es el segundo caso real que la justifica. Mientras no exista, cada feature con
una verificación manual diferida obliga al reviewer a rechazar o al humano a
firmar a mano, y eso último es lo correcto pero cuesta una vuelta entera.
