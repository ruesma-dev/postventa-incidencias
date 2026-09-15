<!-- progress/review2_F-009.md -->
# F-009 · Cierre de la incidencia en Sigrid — segunda review

**Veredicto: APROBADO** (con tres condiciones para el humano, en §7; ninguna
es trabajo del implementer y ninguna se resuelve en este repositorio).

> Alcance: **T1–T21**. El **bloque 8 (T22–T27) no entra** —es verificación
> manual contra el ERP de producción y no se ha ejecutado ni debía— y **T28**
> tampoco, por decisión del humano. Esta pasada comprueba **los cinco cambios
> de la §7 de `progress/review_F-009.md`**; lo verificado en la primera review
> —el batch carácter a carácter, la guardia de red, R3, R20, los datos
> personales, el DDL, la campaña recalculada— no se rehace, y nada de lo nuevo
> lo toca: **el único cambio de código de estos cinco commits es un reorden de
> imports** (`git diff a335706~1..HEAD -- services/`).
>
> Lo que ha cambiado de fondo respecto a la primera review no es que se hayan
> tapado los reparos, sino que **dos de las tres casillas que quedaban abiertas
> se han cerrado con evidencia, y la tercera con una decisión del humano
> fechada y firmada**. Y he añadido una comprobación que la primera review no
> hizo: **muestrear que los tests nuevos matan de verdad a sus mutantes** (§5).

## 1 · `bash harness/init.sh` — ejecutado tal cual

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido    21 features, 11 abiertas, en curso: ['F-009']
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 58 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)      17 passed (raíz)
[OK] servicio api (services/postventa-api): pytest en verde (caché)
[OK] servicio front (services/postventa-front): pytest en verde (caché)
[OK] PUERTA COBERTURA: 98.8% de 572 líneas cambiadas cubiertas
     (565/572, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-009-cierre-sigrid
ENTORNO LISTO. Puedes trabajar.
```

**Exit code 0.** Los avisos de `ruff` bajan de **59 a 58**, que es exactamente
el efecto del arreglo del §7.5 y ni un aviso más.

Las dos suites de servicio volvieron a salir **de caché**, así que no me quedé
ahí: **relancé la del backend de verdad**, porque desde mi primera review ha
cambiado un fichero de producción:

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/ -q
1594 passed, 3 skipped in 52.89s
```

Mismos 1.594 que en la primera pasada. El reorden de imports no movió nada.

## 2 · Nivel de rigor y estado de sus puertas

`harness/features.json` declara `rigor: "critico"`. Estado tras los cinco
cambios:

| Puerta | Exigida | Estado en esta pasada |
|---|---|---|
| Fase RED en los requisitos centrales | sí | **[x]** verificada en la 1.ª review, intacta |
| Cobertura de lo cambiado ≥ 80 % | sí | **[x]** 98,8 % (565/572) |
| Campaña de mutación con totales reales | sí | **[x]** recalculada e independiente en la 1.ª review |
| Ningún superviviente en `PENDIENTE` | sí | **[x]** **0 de 26**, ver §3 |
| Cero supervivientes salvo justificación **aceptada por el humano** | sí | **[x]** aceptación escrita y fechada, ver §4 |
| Verificaciones `MANUAL (humano)` con comando exacto | sí | **[x]** ver §6, checkpoint C4 |
| Sección «Evidencias» con los cuatro números | sí | **[x]** `impl_F-009.md` §7.1, intacta |

## 3 · §7.1 · Los 26 análisis, trasladados — **verificado, y verificado que funciona**

Commit `a335706`. Tres comprobaciones, no una:

**a) Cero marcadores.** `grep -c "PENDIENTE" progress/mutacion_F-009.md` → **0**.
26 bloques `### N.` y **26** cabeceras `#### Análisis`. Ni uno suelto.

**b) Es el texto, no un resumen.** Comparé los 26 bloques contra la tabla del
`progress/impl_F-009.md` §7.2 **en su versión anterior al traslado**
(`git show a335706~1`). No solo no se perdió nada: **se ganó**. Donde la tabla
tenía una fila para «1–4, 8», ahora hay cinco bloques con el análisis completo
cada uno y la nota de que se analizaron en bloque; y los supervivientes 22 y 23
incorporan el detalle que la propia review sacó a la luz —que la mutación no
solo vacía la descripción, sino que un `NULL` sale como la cadena literal
`"None"`—. **El diff del fichero solo quita la plantilla vacía**: las únicas
líneas eliminadas que no son la cabecera `PENDIENTE` son las 26 repeticiones de
`> Decisión: ¿test nuevo o mutante equivalente justificado?`. Alcance, totales,
tiempo y muestreo, **intactos**.

**c) Y —esto es lo que importaba— comprobé que el traslado cumple su función.**
El motivo del §7.1 no era estético: `harness/mutacion.py::analisis_escritos`
relee los análisis del informe para conservarlos al regenerarlo, y descarta una
clave si dos supervivientes la comparten con **textos distintos**. Ejecuté la
función sobre el informe de hoy:

```
analisis_escritos(mutacion_F-009.md) -> 21 claves con análisis conservable
```

**21 claves para 26 supervivientes, y cuadra**: los cinco
`@dataclass(frozen=True)` colapsan en una sola clave, y el implementer les
escribió **texto idéntico** a los cinco, así que la regla de descarte no se
dispara y la clave se conserva. 21 + 5 = 26. **Cuando alguien lance T28, los 26
análisis sobrevivirán.** Era exactamente lo que pedía el cambio.

## 4 · §7.2 · Los tres huecos · **la decisión del humano basta**

No vuelvo a pedir los tests. Lo que me toca es decir si lo escrito cierra la
casilla, y **la cierra**. `progress/current.md:22-41`, en el bloque de estado
más reciente, bajo el título **«DECISIÓN DEL HUMANO (2026-08-26) · los tres
huecos se aceptan como riesgo»**:

- **Cita literal** de la decisión («*el humano eligió lo segundo,
  explícitamente: «salta el 2»*»), con fecha.
- **Los tres supervivientes nombrados uno a uno**, con fichero y línea:
  el **21** (`cliente.py:347`, `respuesta.get("ok", False)`) y los **22 y 23**
  (`consultas.py:202` y `:207`, el `NULL` de `descripcion` y de
  `estado_destino_res`).
- **El riesgo de cada uno declarado**, no solo su nombre: qué pasa si
  `sigrid-api` deja de mandar `ok`, y que la descripción es una de las cinco
  cosas que R9 obliga a enseñar antes de confirmar.
- **Y la razón por la que consta ahí**: «en rigor `critico` esa decisión no la
  puede tomar ni el implementer ni el reviewer».

Mi propia §7.2 admitía esta salida con dos condiciones —que la decisión fuera
del humano y que quedara escrita—. **Las dos se cumplen, y con más precisión de
la que pedí.** Doy la casilla de C4 bis por cerrada.

Que quede dicho para el registro, sin reabrir nada: **los tres viven en el
camino de lectura del dry-run, no en el de escritura**. El batch que toca el
ERP —`design.md` §7.3— está cubierto y verificado carácter a carácter en la
primera review.

## 5 · Lo que esta review añade: **los muertos, muestreados**

La primera review dejó dicho que el cero de supervivientes de `critico` estaba
**razonado, no demostrado**: los 19 tests que cierran supervivientes están
escritos y en verde, pero nadie había vuelto a ver morir a un mutante. El
encargo prohíbe lanzar la campaña entera (~43 min) por mi cuenta, y hace bien.
Pero **entre no comprobar nada y comprobarlo todo hay un muestreo**, así que lo
hice: apliqué cuatro de los mutantes que la campaña reportó vivos y lancé la
suite del servicio contra cada uno.

| # | Mutación aplicada | Resultado |
|---|---|---|
| 1 | `cierre.py` · `@dataclass(frozen=True)` → `False` | **MUERTO** (1 failed, 1104 passed) |
| 9 | `function_app.py` · el `400` del cuerpo no-JSON → `401` | **MUERTO** (1 failed, 392 passed) |
| 18 | `cliente.py:130` · `trust_env=True` → `False` | **MUERTO** (1 failed, 970 passed) |
| 20 | `cliente.py:331` · `monotonic() - arranque` → `+` | **MUERTO** (1 failed, 973 passed) |

**Cuatro de cuatro muertos**, uno por cada familia de tests nuevos (`3e32681`,
`2747aa6` y `b85ce26`). No demuestra los 19, pero convierte «razonado» en
«razonado y muestreado», y **el muestreo no encontró ni un test decorativo**.

**El árbol quedó limpio**: cada fichero se restauró con `git checkout --` en un
`finally`, la suite se lanzó con `PYTHONDONTWRITEBYTECODE=1` —para no repetir
el envenenamiento de bytecode del defecto P4 del arnés— y
`git status --porcelain --untracked-files=all` devolvió cadena vacía. El script
del muestreo vive en mi scratchpad, **fuera del repositorio**.

## 6 · Recorrido de `CHECKPOINTS.md` (solo lo que esta pasada juzga)

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`, exit code 0 (§1).
- [x] Todos los ficheros obligatorios presentes.

### C2 — El estado es coherente · **la casilla que estaba vacía, cerrada**

- [x] Una sola feature `in_progress` (`F-009`); rama
      `feature/F-009-cierre-sigrid`.
- [x] **`progress/current.md` describe SOLO la sesión activa.** De **1.385 a
      598 líneas**. El bloque `## Sesión anterior` ha desaparecido, y con él las
      ~700 líneas de F-019 y los defectos numerados hasta el 16 que no eran de
      esta sesión. Lo que queda son **tres bloques de estado del mismo día y de
      la misma feature** —review, implementación y el cierre del Word—, que son
      el arco de la sesión activa y ninguno repite al otro.
- [x] **Nada vivo se perdió en la poda, y no lo digo por lectura: lo medí.**
      Extraje las **686 líneas distintas** que el commit `8a222ef` quitó de
      `current.md` y comprobé una a una si aparecen hoy en `history.md` o en el
      propio `current.md`. **Resultado: 0 líneas sin rastro.** Lo movido está en
      `progress/history.md:698`, bloque «Podado de `progress/current.md` —
      2026-08-26», etiquetado con quién lo movió y por qué, y conservado tal
      cual sin reescribir.
      Sigue **en `current.md`**, comprobado punto por punto: la **cola de
      decisiones pendientes** (los seis puntos, con los dos cerrados tachados y
      no borrados), la **deuda declarada con dueño** (F-015 y F-018), el aviso
      de los **permisos de Graph** más amplios de lo necesario, los **scripts de
      las verificaciones manuales** con el **defecto 16** del DSN sin
      contraseña, el **contexto del arnés** y las **cinco lecciones
      operativas**.
- [x] Toda feature `done` tiene su resumen en `history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Sin cambios que revisar.** El único diff de código de estos cinco
      commits es el reorden de dos imports en `paso_cierre.py:55-62`, sin efecto
      de comportamiento. La primera línea del fichero sigue siendo su ruta
      relativa. Todo lo demás —hexagonal, composición en el borde, ausencia de
      `print`, de secretos y de estados cableados, y que ningún parte escaneado
      haya entrado en git— quedó verificado en la primera review y nada lo ha
      tocado.

### C3 bis — Los documentos que entran de fuera son seguros

- [x] **Sin cambios.** Verificado en la primera review, con barrido de secretos
      propio sobre el diff completo y cero hallazgos.

### C4 — La verificación es real · **la casilla que estaba vacía, cerrada**

- [x] Cada requisito EARS con ≥ 1 test trazable (R1–R52; **R53 N/A
      justificado**: describe el documento de otro repositorio y `tasks.md` T21
      lo declara `MANUAL (humano)`). Tabla completa en la primera review §6.
- [x] Los unit tests no tocan red ni BBDD ni el ERP: guardia de red en tres
      capas, verificada en la primera review.
- [x] **Las verificaciones `MANUAL (humano)` de T22–T27 están en
      `progress/current.md:115-394` con su comando exacto.** Comprobado que son
      **tecleables**, que es lo que pedía el §7.3:
      - **Cero marcadores sin resolver** salvo tres que **no pueden resolverse
        de antemano y están rotulados**: el código de la reclamación, el hash
        del parte y el login real del ERP. El propio texto dice de dónde salen
        («el código sale del parte; el hash, del front»).
      - **Los `?` del SQL siguen ahí —y deben—, pero con su lista de parámetros
        resuelta**: `... WHERE c.tip = ? AND c.cod = ?` con `@(708, $incidencia)`.
        La pasarela solo acepta SQL parametrizado, así que **eso es** el comando
        exacto. La cabecera lo dice explícitamente.
      - **La apertura y el cierre del interruptor, los dos**, con nombre de
        recurso real (`az functionapp config appsettings set -g rg-postventa-dev
        -n func-postventa-dev --settings CIERRE_HABILITADO=true` / `=false`), y
        el cierre con **su comprobación** («tiene que imprimir `false`») y con
        la orden de hacerlo «**SIEMPRE al terminar, salga bien o mal**».
      - **El aviso está, y está antes que todo lo demás** (`:123-128`): «con
        `CIERRE_HABILITADO` apagado ni siquiera el dry-run de T22 funciona»,
        porque la fábrica se niega **antes de leer**, con la consecuencia
        concreta (`503` también sin `commit`) y la orden de abrir la ventana
        también para el dry-run.
      - **Y lo que citan existe.** No me fié: comprobé contra el código que
        `CIERRE_HABILITADO`, `SIGRID_API_BASE_URL`, `SIGRID_BASE_DATOS` y
        `SIGRID_ZONA_HORARIA` son `validation_alias` reales de
        `config/settings.py`; que `dsn_desde_ajustes` y `ajustes.pg_password`
        existen y que el aviso de pasar la contraseña aparte es correcto; que
        `infra/07_alta_usuario_sigrid.ps1` acepta exactamente
        `-UsuarioOid -LoginSigrid -VerificarAhora -SigridBaseUrl
        -SigridBaseDatos`; y que el cuerpo de `Llamar-Cerrar` casa **campo a
        campo** con lo que exige `interface_adapters/api/cerrar.py` —`hash`, no
        `hash_parte`—, con `commit` y `confirmado` como las dos banderas
        opcionales. **Un comando que nombra un campo inexistente no es
        tecleable, y ninguno lo hace.**
      - Además trae dos cosas que no pedí y valen: la trampa del `'@` de
        PowerShell pegado al margen, y un `try/catch` en `Llamar-Cerrar` para
        que un `409` o un `503` no salgan como excepción muda —el defecto 14 de
        F-010 otra vez—.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"`.
- [x] Fase RED con trazas reales (1.ª review).
- [x] Cobertura 98,8 %.
- [x] Mutación: informe genuino, totales recalculados de forma independiente y
      coincidentes en el commit de la campaña (1.ª review §3).
- [x] Regla de los 5 minutos: «Tiempo total» 2.588 s > 5 min, así que vale el
      recálculo puro. **Queda dicho, otra vez y explícitamente: campaña no
      reejecutada, 43 min según el informe.** Añadido de esta pasada: **cuatro
      mutantes muestreados y muertos** (§5).
- [x] **Cada superviviente con su análisis completado: 0 de 26 en `PENDIENTE`**
      (§3), y comprobado que la herramienta los conservará.
- [x] **Cero supervivientes salvo justificación escrita aceptada por el
      humano**: 19 cerrados con test, 1 eliminado cambiando el código, 3
      equivalentes justificados y **3 aceptados por escrito por el humano**
      (§4). Suman 26. Ninguno se queda sin cuenta.
- [x] Sección «Evidencias» con los cuatro números y los workers.
- [x] Ningún punto de este bloque en N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A y nada que justificar**: `harness/rutas_sensibles.json` no existe en este
repositorio; es el caso que el propio checkpoint declara N/A por configuración.

### C5 — La sesión se cerró bien

- [x] **T1–T21: todas `[x]`**, comprobado por barrido (`grep` de `- [ ] **Tn**`
      sobre 1–21: cero coincidencias), y cada una con su commit `F-009 Tn:`.
      **T21 no tiene commit aquí y no puede tenerlo**: su entregable vive en
      `azure-apps` (commit local `3c1c588`, sin push), verificado en la primera
      review.
- N/A **T22–T27 sin marcar. Justificado, y por partida doble**: son
      verificación manual contra el **ERP de producción**, el encargo las deja
      fuera y el `CLAUDE.md` de este repositorio **prohíbe** ejecutarlas desde
      aquí. Que sigan sin marcar no es un defecto: **es lo correcto**, y
      marcarlas sería el defecto. Están enteras y tecleables en `current.md`
      para cuando el humano las ejecute.
- N/A **T28 sin marcar. Justificado**: la campaña de confirmación son ~43
      minutos, **el humano no la ha pedido** y el encargo me prohíbe lanzarla
      por mi cuenta. Queda como **condición** en §7.1, no como reparo.
- [x] **T29 (`init.sh` en verde): cumplido de hecho**, lo ejecuté yo y salió
      exit code 0 (§1). La casilla sigue sin marcar en `tasks.md`; es
      bookkeeping del implementer, **no un defecto del trabajo**, y lo anoto en
      §7.3 para que se cierre cuando se cierren las demás.
- [x] Sin ficheros temporales ni artefactos: `git status --porcelain
      --untracked-files=all` **vacío**, antes y después de mi muestreo.
- [x] `features.json` refleja el estado real (`in_progress`). **No lo he
      tocado**, como manda el encargo: ese movimiento es del humano.

## 7 · Condiciones para el humano (no son trabajo del implementer)

Apruebo, y estas tres cosas van con la aprobación. Ninguna se resuelve en este
repositorio y ninguna las puede cerrar un agente.

1. **El cero de supervivientes sigue sin demostrarse con una campaña.** Está
   razonado, y desde hoy **muestreado 4 de 4** (§5), pero T28 no se ha
   ejecutado. **No lo considero motivo para rechazar** —el encargo lo excluye,
   el humano no la ha pedido y el muestreo no encontró un solo test decorativo—,
   pero sí para decirlo alto: si se quiere el `critico` completo, son ~43
   minutos de reloj y es `python -m harness.mutacion --feature F-009`.
2. **El bloque 8 está entero sin ejecutar, y F-009 no está terminada hasta que
   se ejecute.** Nada de esta feature ha tocado el ERP. Lo aprobado es que el
   código, los tests y la documentación están listos **para** ese día, no que
   ese día haya llegado. Dentro de T24, el **paso 7 incluye mirar la hora** de
   la fila de `dbo.log`: es la única decisión de la feature que no se pudo tomar
   con un dato (el huso `Europe/Madrid`). Y en T26, si `SqlWriteGuard` rechaza
   el `WITH (UPDLOCK, HOLDLOCK)`, **no se improvisa**: `blocked` y parar.
3. **Bookkeeping menor**: marcar **T29** en `tasks.md` (está hecho), y marcar
   T22–T28 **solo según se vayan ejecutando de verdad**.

**Sigue anotado y sin hacer, de la primera review §6.3** (nada bloqueante, y
nada de esto ha cambiado): la fila de R53 en la tabla de trazabilidad de
`requirements.md`; el tipado `int | None` de `Reclamacion.estado_destino_est`;
los tres detalles del documento de `azure-apps` (que no enlaza a `sigrid_api.md`
ni a `sigrid_tablas.md`, que omite `REQUIRE_WHERE_ON_UPDATE_DELETE` y que nunca
nombra `ruesma_rep`); los asserts inertes de `test_f009_front.py`; que **R13 no
tiene front**; la duplicación heredada del diccionario de Sigrid en
`docs/ARCHITECTURE.md:288-294`; y la propuesta —que suscribo— de que
`postventa-incidencias` entre en la tabla de consumidores de
`azure-apps/sigrid_api.md` §10, porque desde F-009 es **el primer escritor
genérico por `sql/write` del ecosistema** y hoy quien lea esa tabla concluiría
que nadie escribe. Es documento de otro proyecto: se lleva a su dueño.

## 8 · Lo que quiero dejar dicho del trabajo

La primera review abrió diciendo que la ingeniería era excelente y que el
rechazo se apoyaba en casillas, no en el código. La respuesta al rechazo lo
confirma: **ninguno de los cinco cambios se resolvió por lo barato**. El
traslado de los 26 análisis no fue un copiar y pegar, fue una expansión que
mejora el original; la poda se hizo moviendo, no borrando, y aguanta una
comprobación línea a línea de 686 líneas sin perder una; los comandos manuales
citan settings, funciones y parámetros que **existen**, comprobados contra el
código; y la corrección del dato de `ruff` no se limitó a arreglarlo, sino que
dice por escrito que **era falso cuando se escribió**, mide de nuevo sobre los
27 ficheros nuevos y **declara además lo que sigue sin pasar** —el `I001`
heredado de F-005 en `test_f005_ddl_idempotente_texto.py:16`—, que nadie le
había preguntado.

Esa última costumbre —confesar lo que falta antes de que lo encuentre el
revisor— es la que ha hecho esta feature revisable en dos tardes.

## 9 · Automejora del protocolo (propuesta, no aplicada)

Las **dos de la primera review siguen en pie** y sin aplicar (C4 bis debería
decir **dónde** va el análisis de los supervivientes, porque la herramienta solo
lo relee de `mutacion_F-XXX.md`; y C4 debería definir qué es «comando exacto»).
Esta pasada añade una tercera:

3. **El protocolo del reviewer no contempla el muestreo de muertos, y debería.**
   Hoy dice: si el «Tiempo total» baja de 5 minutos, reejecuta la campaña
   entera; si no, quédate en el recálculo puro y dilo. Entre las dos hay un
   hueco de una hora de coste: **un recálculo puro no demuestra que ni un solo
   mutante muera**, y reejecutar una campaña de 43 minutos no siempre está
   autorizado. Muestrear tres o cuatro mutantes cuesta dos minutos y distingue
   una suite que caza de una que acompaña. Propongo añadir a C4 bis:
   *«Cuando la campaña no se reejecute, muestrea al menos tres mutantes de
   familias distintas: aplícalos, lanza la suite del servicio y comprueba que
   mueren. Restaura cada fichero en un `finally` y lanza con
   `PYTHONDONTWRITEBYTECODE=1`, o dejarás bytecode compilado desde el código
   mutado. Anota el resultado en el informe.»*
   Si la mejora se acepta, es genérica y viaja a `arnes-base` en el mismo
   trabajo.
