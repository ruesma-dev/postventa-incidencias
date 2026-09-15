<!-- progress/review_F-009.md -->
# F-009 · Cierre de la incidencia en Sigrid — review

**Veredicto: CHANGES_REQUESTED**

> Alcance revisado: **T1–T21, bloques 1 a 7**. El bloque 8 (T22–T27) es
> verificación manual contra el ERP y **no entra**; queda listado en §7.
>
> **Lo primero, porque es lo que más pesa y no quiero que se pierda entre los
> reparos: el trabajo de ingeniería de esta feature es excelente.** El batch de
> escritura está carácter a carácter como manda `design.md` §7.3, el control
> negativo de R3 tiene su propio control positivo, la guardia de red cubre el
> ERP en tres capas, y el informe del implementer **declara por escrito tres
> huecos que nadie le habría pedido que confesara**. Eso último es lo que hace
> revisable esta feature en una tarde.
>
> El rechazo no discute nada de eso. Se apoya en cuatro casillas vacías de
> `CHECKPOINTS.md`, tres de ellas de arreglo corto, y la protocolaria manda:
> un checkbox vacío en C1–C5 es CHANGES_REQUESTED.

## 1 · Nivel de rigor y qué exige

`harness/features.json` declara `rigor: "critico"` para F-009. Según
`harness/rigor.json`, eso exige:

| Puerta | Exigida | Estado |
|---|---|---|
| Fase RED en los requisitos centrales | sí | **[x]** trazas reales pegadas |
| Cobertura de las líneas cambiadas ≥ 80 % | sí | **[x]** 98,8 % (565/572) |
| Campaña de mutación con totales reales | sí | **[x]** verificada de forma independiente |
| **Cero supervivientes** salvo justificación aceptada por el humano | sí | **[ ]** ver §4 |
| Verificaciones `MANUAL (humano)` con comando exacto y resultado | sí | **[ ]** ver §5, checkpoint C4 |

## 2 · `bash harness/init.sh` — ejecutado tal cual

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido      21 features, 11 abiertas, en curso: ['F-009']
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 59 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)          17 passed (raíz)
[OK] servicio api  (services/postventa-api):  pytest en verde (caché)
[OK] servicio front (services/postventa-front): pytest en verde (caché)
[OK] PUERTA COBERTURA: 98.8% de 572 líneas cambiadas cubiertas
     (565/572, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-009-cierre-sigrid
ENTORNO LISTO. Puedes trabajar.
```

**Exit code 0.** Las dos suites de servicio salieron **de caché** («árbol sin
cambios desde el último verde»), así que no me quedé ahí: relancé la del
backend de verdad con su intérprete —

```
services/postventa-api/.venv/Scripts/python.exe -m pytest tests/ -q
1594 passed, 3 skipped in 82.32s
```

— y coincide con los 1.594 que declara el informe. (El informe dice «13
saltados» donde yo veo 3; es una diferencia de entorno, no de resultado, y no
la cuento como hallazgo.)

## 3 · Verificación independiente de la campaña de mutación

Lo hice con `harness.alcance` y `harness.mutacion.generar_mutantes`, cálculo
puro, sin ejecutar la suite ni escribir en disco. **El árbol quedó limpio**
(`git status` vacío antes y después).

La campaña se lanzó contra el commit **`42438f6`**, no contra HEAD, así que
recalculé en los dos sitios:

| | Alcance (líneas) | Mutantes |
|---|---:|---:|
| Lo que declara `progress/mutacion_F-009.md` | 3.021 | 124 |
| **Mi recálculo en `42438f6`** | **3.021** | **124** |
| Mi recálculo en HEAD (5 commits después) | 3.024 | 123 |

**Coinciden exactamente en el commit de la campaña.** La diferencia en HEAD se
explica sola: `cierre.py` creció 3 líneas y el superviviente 7 desapareció al
cambiar `split("@", 1)` por `partition("@")`.

**Muestreo de supervivientes** — comprobé que existen como mutantes reales, con
el mismo operador y el mismo texto original→mutado:

| # | Fichero:línea | Operador | Existe |
|---|---|---|---|
| 1–4, 8 | `cierre.py:121,136,179,199,346` | booleano | ✔ `@dataclass(frozen=True)` → `False` |
| 18 | `cliente.py:130` | booleano | ✔ `trust_env=True,` → `False,` |
| 19 | `cliente.py:290` | booleano | ✔ `reraise=True,` → `False,` |
| 21 | `cliente.py:347` | booleano | ✔ `get("ok", False)` → `get("ok", True)` |
| 22 | `consultas.py:202` | logico | ✔ `str(descripcion or "")` → `and ""` |
| 23 | `consultas.py:207` | logico | ✔ `str(destino_res or "")` → `and ""` |

**El informe de mutación es genuino, no está escrito a mano.**

**Regla de los 5 minutos** (C4 bis): el informe declara **«Tiempo total 2.588 s»**
— 43 minutos, muy por encima del umbral —, así que me quedé en el recálculo
puro y lo digo explícitamente: **campaña no reejecutada; 43 min según el
informe.**

**Coste por mutante** (C4 bis): 2.588 s × **6 workers** ÷ 124 mutantes =
**125 s/mutante**, contra una suite de backend de **82 s** medida por mí. Está
por encima del tiempo de la suite, que es lo que tiene que pasar. **La campaña
tardó lo que tenía que tardar.**

## 4 · Los tres huecos que el implementer declara, juzgados

El encargo me pedía dictaminar si bloquean o se aceptan por escrito. **Los
verifiqué uno a uno, no me fié del informe.**

### 4.1 · Superviviente 21 · la respuesta de la pasarela sin la clave `ok`

`infrastructure/sigrid/cliente.py:347`, `respuesta.get("ok", False)`.

Comprobado: **ningún test manda una respuesta de escritura sin la clave `ok`.**
Los diez `RespuestaFalsa` de escritura la traen siempre; hay un caso con
`ok: False` (`test_f009_adaptador_sigrid.py:438`), pero **ausente, ninguno**.

El código de producción está bien: el valor por omisión es el seguro. Lo que
falta es la red que impida que mañana alguien lo cambie. **Y esta es la línea
que decide si damos por escrito el ERP de producción.** Un test es una línea:
`RespuestaFalsa(200, {"total_affected_rows": 2})` y esperar `CierreFallido`.

### 4.2 · Supervivientes 22 y 23 · el `NULL` de `descripcion` y de `estado_destino_res`

`infrastructure/sigrid/consultas.py:202` y `:207`.

Comprobado: **ningún test ejercita `fila_a_reclamacion` para estos dos
campos.** Los siete sitios que nombran `estado_destino_res` construyen un
`Reclamacion(...)` a mano; ninguno pasa por el mapeo. De `descripcion` no hay ni
una mención en `test_f009_consultas.py`.

Y el mutante **no es benigno**, mírese de cerca:

- `str("REPARACION" and "")` → `""`. Una descripción presente sale **vacía**.
- `str(None and "")` → `str(None)` → **`"None"`**. Un `NULL` sale como la
  cadena literal `None`.

Las dos cosas llegan a la pantalla de quien está a punto de autorizar una
escritura en el ERP de producción, y **la descripción es una de las cinco cosas
que R9 obliga a enseñar antes de confirmar**. Un test que mapee una fila
completa y una fila con `NULL` mata los dos mutantes de una vez.

### 4.3 · La campaña de confirmación no relanzada

**No lo cuento en contra**: es T28, del bloque 9, y el encargo lo deja fuera.
Queda dicho para el humano en §7: **el cero de supervivientes de `critico` no
está demostrado, está razonado.** Los 19 tests que cierran supervivientes están
escritos y en verde, pero nadie ha vuelto a pasar la campaña para verlos morir.

### 4.4 · Veredicto sobre los tres

**Bloquean.** No por rigidez: los tres viven en dos ficheros, son el camino de
escritura contra un ERP de producción, y se cierran en un commit corto. En
nivel `critico` la regla es cero supervivientes «salvo justificación escrita
**aceptada por el humano**», y lo que hay en el informe no es una justificación
de equivalencia —el propio implementer los llama «huecos reales sin test»— sino
una confesión honesta. Confesar no es lo mismo que justificar, y la aceptación
del humano no consta.

## 5 · Recorrido completo de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-009`), validado por `init.sh`.
- [x] Rama actual `feature/F-009-cierre-sigrid`.
- [ ] **`progress/current.md` describe SOLO la sesión activa.** **NO.** Tiene
      **1.104 líneas** y en la `:208` abre literalmente
      `## Sesión anterior (2026-08-26, tarde)`, con ~700 líneas por debajo de
      F-019, defectos numerados hasta el 16 y contexto del arnés. Dentro de la
      propia parte «activa» hay cuatro estados apilados de F-009, tres
      superados por los posteriores.
      **Deuda heredada, no la introdujo F-009** (su diff añade 31 líneas), pero
      C2 se evalúa al cerrar y la casilla está vacía.
- [x] Toda feature `done` tiene su resumen en `history.md` — comprobado por
      script contra las diez `done`: ninguna falta.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `domain/` (22 ficheros) no importa
      `infrastructure`, `httpx`, `psycopg` ni `azure.functions`, y no contiene
      una sola sentencia SQL. `paso_cierre.py` importa **solo** `domain.models`,
      `domain.ports` y `contexto_parte`.
- [x] **La composición vive en el borde**, `interface_adapters/api/cerrar.py:119-131`;
      `construir_erp` se importa solo ahí.
- [x] Primera línea con la ruta relativa en los 14 ficheros nuevos (`.py`,
      `.sql`, `.ps1`, `.js`), comprobado uno a uno.
- [x] Sin `print()` de debug (cero en las cinco capas de producción), sin TODOs
      —los 20 aciertos del barrido son la palabra «Todo» en prosa—, sin
      secretos, sin dependencias nuevas (`httpx` y `tenacity` ya venían de F-006).
- [x] **La unidad de trabajo es el parte**: el cierre se identifica por
      `hash_parte` + `numero_incidencia`, nunca por PDF.
- [x] **Nada se cierra sin haber pasado todas las validaciones.** El orden de
      `paso_cierre` es apto (R16) → archivado (R17) → login verificado
      (R29–R32) → dry-run (R8) → `evaluar` → traza → y solo entonces la
      escritura, que además exige confirmación o auto-cierre. **Dry-run siempre
      primero**, y `commit` vale `false` por omisión.
- N/A **Lo manuscrito no se descarta** / **Firmado no es conforme** — F-009 no
      toca extracción ni validación; de hecho `_como_contexto` reconstruye el
      contexto **sin extracción y con `contenido=b""`** a propósito (R51).
- [x] **Reprocesar no duplica**: R42 lo garantiza en el `WHERE` del `DO UPDATE`
      de `upsert_cierre`, que no pisa una fila ya `cerrado`.
- [x] **Nada hardcodea un número de estado de Sigrid.** Verificado por mí, no
      solo por el test: el estado se resuelve contra `dbo.conest` por su `cod`
      (`CODIGO_ESTADO_CIERRE = "CER"`), viaja como parámetro `?` en el `JOIN`, y
      el control negativo `test_f009_estado_no_hardcodeado.py` barre las cinco
      capas de producción **sin una sola excepción por fichero** y trae su
      propio control positivo.
- [x] **Ningún parte escaneado ni PDF ha entrado en git.**
      `git log --all --diff-filter=A --name-only` sobre todas las ramas: cero
      `.pdf/.docx/.xlsx/.pptx`, cero imágenes, cero `muestras/`. El inventario
      completo del historial son `py, md, js, ps1, json, sql, xml, txt, example,
      sh, html, css, gitignore, yaml, iml, funcignore`.

### C3 bis — Los documentos que entran de fuera son seguros

**Aplica**: la rama toca `docs/referencia/` en el commit `6b68e2a` (fase de
spec: `01_cierre_incidencia_sigrid.md` +23, `README.md` ±1).

- [x] **Cabecera con origen y fecha**, según la plantilla:
      «Origen: `PASOS CERRAR INCIDENCIA.docx` […] adjunto a su correo del
      2026-08-18. Convertido con `markitdown` […] Fecha del documento original:
      2026-08-18.»
- [x] **Los originales no están en git**, ni en el índice ni en el historial de
      ninguna rama (mismo barrido de C3).
- [x] **Barrido de datos sensibles ejecutado por mí** sobre el diff completo
      `6cabd39..HEAD`. Patrones usados:
      `x-functions-key|AccountKey=|[?&]sig=|sk-[A-Za-z0-9]{10,}|ghp_|SharedAccessSignature|api[_-]?key`,
      `Server=|Data Source=|Initial Catalog=|postgres(ql)?://|mssql://|DefaultEndpointsProtocol=|Trusted_Connection`,
      GUID `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`,
      IPs `\b10\.|\b192\.168\.|\b172\.(1[6-9]|2[0-9]|3[01])\.`,
      base64 `[A-Za-z0-9+/]{40,}={0,2}`,
      `(password|passwd|pwd|secret|contraseña|token)\s*[=:]`,
      correos `[\w.%+-]+@[\w.-]+\.\w{2,}`, y hosts
      `azurewebsites|postgres.database|sharepoint.com|onmicrosoft|database.windows.net`.
      **Resultado: cero hallazgos.** Todos los correos del diff son
      `@ejemplo.invalido`; las claves de test son `clave-de-mentira-para-el-test`
      y `CLAVE_INVENTADA`; la URL de la pasarela no aparece; cero GUID; cero IPs.
- [x] **Lo redactado está anotado en la cabecera**: «**Redactado**: se han
      sustituido por marcadores el nombre del propietario y el nombre del
      servidor interno de Sigrid que aparecían en las capturas.» La única ruta
      de negocio que cita elide el servidor con `…`, coherente con lo declarado.

### C4 — La verificación es real

- [x] **Cada requisito EARS tiene ≥ 1 test trazable y todos pasan.** Lo
      comprobé por script sobre las tres suites: **R1–R52 tienen entre 1 y 14
      tests `test_f009_rN_*` cada uno**. Tabla completa en §6.
      **R53 es el único sin test → N/A justificado**: describe el documento de
      **otro repositorio** (`azure-apps/postventa_incidencias.md`), y `tasks.md`
      T21 lo declara `MANUAL (humano)`. Lo verifiqué a mano; ver §6.1.
- [x] **Los unit tests no tocan red ni BBDD.** Tres capas comprobadas por mí:
      (1) `conftest.py` parchea `socket.socket.connect` a nivel de **sesión**,
      así que ni durante la recogida se puede conectar;
      (2) `conftest.py` fija `ENTORNO=test`, y `ENTORNOS_CON_CIERRE = ("dev","pro")`,
      así que la fábrica se niega —hay test que lo fija,
      `test_f009_r39_con_el_entorno_de_la_suite_no_se_puede_construir_el_erp`—;
      (3) los tres sitios que construyen `AdaptadorSigridApi` pasan
      `entorno="dev"` **explícito**, un `ClienteFalso` y `https://ejemplo.invalido`.
      **Ninguna prueba puede ejecutar una escritura contra Sigrid.** Regla dura
      cumplida.
- [ ] **Las verificaciones `MANUAL (humano)` están listadas en
      `progress/current.md` con su comando exacto.** **NO.** En las 1.104 líneas
      del fichero hay **dos vallas de código en total**, y las dos son de F-019.
      Cero ocurrencias de `az functionapp`, `curl`, `Invoke-RestMethod` o
      `POST /api/cerrar`. Lo que hay son dos menciones en prosa: `:12-14` («el
      bloque 8 queda entero para el humano») y `:197-204`, que sí desglosa
      T22–T27 pero **dentro de un bloque de sesión anterior** y sin un solo
      comando. Los procedimientos existen en `tasks.md:174-232`, pero C4 pide
      `current.md`, y con **comando exacto**: el SQL de T24 va con marcadores
      (`WHERE tip = ? AND cod = ?`), que no es ejecutable.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"` en `harness/features.json`.
- [x] **Fase RED.** Trazas reales, no promesas. La mejor es T3: el módulo ya
      estaba limpio, así que se **ensució a propósito** con `EST_CERRADA = 9` y
      `est = 9` en el SQL, y la traza pegada enseña los dos tests cayendo con el
      `AssertionError` completo. Hay además dos RED **no previstas** y bien
      contadas: el barrido de R20 saltando contra el docstring del propio autor,
      y un defecto **del test** de R47 que pasaba sin comprobar nada.
- [x] **Cobertura.** `[OK] PUERTA COBERTURA: 98.8% de 572 líneas cambiadas
      (565/572, umbral 80%, nivel critico)`.
- [x] **Mutación.** Existe `progress/mutacion_F-009.md`, generado por la
      herramienta, y **verifiqué sus totales de forma independiente**: 3.021
      líneas y 124 mutantes en `42438f6`, coincidencia exacta (§3).
- [x] **Los muertos comprobados.** «Tiempo total» = 2.588 s > 5 min → vale el
      recálculo puro, y **queda dicho explícitamente: campaña no reejecutada,
      43 min según el informe** (§3).
- [x] **La campaña tardó lo que tenía que tardar.** 125 s/mutante corregido por
      los 6 workers declarados, contra una suite de 82 s (§3).
- [ ] **Cada superviviente con su análisis completado (ninguno en `PENDIENTE`).**
      **NO. Los 26 de 26 están en `PENDIENTE`** en
      `progress/mutacion_F-009.md`. Verificado por conteo:
      `grep -c "^### [0-9]"` → 26; `grep -c "Análisis (PENDIENTE del
      implementer)"` → **26**. El análisis está escrito, y está bien escrito,
      pero **en el fichero equivocado**: vive en `progress/impl_F-009.md` §7.2.
      Ver §4.5 de por qué esto no es una pega de forma.
- [ ] **Nivel `critico`: cero supervivientes salvo justificación escrita
      aceptada por el humano.** **NO.** Tres huecos reales sin test (21, 22, 23),
      verificados por mí como todavía abiertos (§4), sin aceptación del humano.
- [x] **Sección «Evidencias»** con los cuatro números **y el nº de workers**
      (`progress/impl_F-009.md` §7.1). Presente y completa. Un dato de esa misma
      sección es inexacto; ver §6.3.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A, y no hay nada que justificar**: `harness/rutas_sensibles.json` no existe
en este repositorio (solo está `rutas_sensibles.ejemplo.json`). Es el caso
mayoritario que el propio checkpoint declara N/A por configuración.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]` y un commit `F-XXX Tn:` por
      tarea.** **PARCIAL.**
      - **T1–T21: `[x]`, y con su commit.** Recorridos uno a uno: `F-009 T1:`
        … `F-009 T19 y T20:`. Dos commits agrupan dos tareas (`T4 y T6`,
        `T13 y T14`), lo cual es legítimo.
      - **T21 no tiene commit `F-009 T21:` en este repositorio**, y no puede
        tenerlo: su entregable vive en `azure-apps` (commit `3c1c588`). Lo doy
        por bueno y queda anotado.
      - **T22–T27: `[ ]`. N/A justificado** — bloque 8, verificación manual
        contra el ERP, explícitamente fuera del alcance de esta review.
      - **T28 y T29: `[ ]`, y no son N/A.** T29 (`init.sh` en verde) **está
        hecho** y sin marcar. T28 es exactamente lo que bloquean §4.1–4.3.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status
      --porcelain --untracked-files=all` vacío. Mi verificación de la campaña no
      dejó nada en el árbol.
- [x] `features.json` refleja el estado real (`in_progress`). **No lo he
      tocado**, como manda el encargo.

### 4.5 · Por qué el `PENDIENTE` de los 26 no es una pega de forma

Podría parecer burocracia —el análisis existe, solo que en otro fichero—, y no
lo es, por una razón mecánica: `harness/mutacion.py` tiene una función
`analisis_escritos(texto)` que **relee los análisis del propio informe** para
conservarlos al regenerarlo. Cuando alguien ejecute T28 y vuelva a lanzar la
campaña, el informe se reescribirá y **los 26 análisis volverán a salir
`PENDIENTE`**: el razonamiento que hoy vive en `impl_F-009.md` §7.2 no viajará
con él. Se perdería justo el trabajo más valioso de esta feature, y se perdería
en silencio.

Trasladarlos es copiar y pegar 26 párrafos que ya están escritos.

## 6 · Cobertura: requisito → test

`R1–R52` tienen todos al menos un test trazable `test_f009_rN_*`, y todos
pasan. Recuento por requisito (nº de tests → fichero principal):

| | | | | | |
|---|---|---|---|---|---|
| R1 · 2 · `consultas` | R2 · 3 · `consultas` | R3 · 12 · `estado_no_hardcodeado` | R4 · 1 · `consultas` | R5 · 3 · `consultas` | R6 · 7 · `consultas` |
| R7 · 6 · `adaptador` | R8 · 5 · `adaptador` | R9 · 5 · `cerrar_http` | R10 · 3 · `adaptador` | R11 · 1 · `adaptador` | R12 · 5 · `cerrar_http` |
| R13 · 4 · `cerrar_http` | R14 · 2 · `fabrica` | R15 · 2 · `front` | R16 · 2 · `paso_cierre` | R17 · 3 · `paso_cierre` | R18 · 6 · `cerrar_http` |
| R19 · 7 · `dominio` | R20 · 7 · `consultas` | R21 · 5 · `cerrar_http` | R22 · 9 · `adaptador` | R23 · 3 · `escrituras` | R24 · 14 · `adaptador` |
| R25 · 4 · `dominio` | R26 · 4 · `escrituras` | R27 · 4 · `adaptador` | R28 · 4 · `escrituras` | R29 · 1 · `usuarios_sigrid` | R30 · 7 · `adaptador` |
| R31 · 1 · `usuarios_sigrid` | R32 · 4 · `paso_cierre` | R33 · 4 · `ddl_orden` | R34 · 1 · `usuarios_sigrid` | R35 · 4 · `dominio` | R36 · 3 · `adaptador` |
| R37 · 5 · `adaptador` | R38 · 5 · `arquitectura` | R39 · 3 · `fabrica` | R40 · 1 · `paso_cierre` | R41 · 2 · `paso_cierre` | R42 · 2 · `paso_cierre` |
| R43 · 2 · `cerrar_http` | R44 · 4 · `logs_sin_datos` | R45 · 5 · `logs_sin_datos` | R46 · 5 · `adaptador` | R47 · 8 · `cerrar_http` | R48 · 5 · `cerrar_http` |
| R49 · 3 · `ruta_http` | R50 · 5 · `adaptador` | R51 · 3 · `cerrar_http` | R52 · 5 · `documentacion` | **R53 · 0 · N/A** | |

### 6.1 · Los cuatro puntos que el encargo pedía mirar de cerca

**El batch de escritura de `design.md` §7.3, carácter a carácter.** Lo comparé
línea a línea contra `infrastructure/sigrid/escrituras.py`. **Coincide
exactamente**, y los parámetros están en el orden correcto:

| Lo que pide §7.3 | Dónde está | ✔ |
|---|---|---|
| Dos sentencias en un batch | `batch_de_cierre` → `"statements": [update, insert]` | ✔ |
| Tope de filas | `MAXIMO_FILAS_AFECTADAS = 2` → `max_affected_rows` | ✔ |
| `WHERE` con el estado de **origen** (R11/R23) | `... WHERE ide = ? AND tip = ? AND est = ?` con `reclamacion.est` | ✔ |
| `emp` **de la reclamación** (R24) | `c.emp` dentro del SQL, no parámetro de Python | ✔ |
| `tab`, `tip`, `cod`, `res` | `'con'`, `c.tip`, `c.cod`, `c.res` | ✔ |
| El `tex` de D1 (R25) | `TEXTO_LOG_CIERRE = f"{TEXTO_PROCESO_ERP} (postventa-incidencias)"`, con un `AssertionError` de módulo si dejara de empezar por `Cerrar parte` | ✔ |
| El `usu` real (R28) | parámetro `login`, con rechazo de vacío y de longitud > 48 sin truncar | ✔ |
| Reserva del `ide` con `FROM` filtrado y **no** `WHERE EXISTS` (R26) | `SELECT (SELECT ISNULL(MAX(l.ide),0)+1 FROM dbo.log l WITH (UPDLOCK, HOLDLOCK)) … FROM dbo.con c WHERE c.ide = ? AND c.tip = ? AND c.est = ?`, filtrado por el **destino** | ✔ |

**R3 · ni un número de estado cableado.** Verificado (C3). El estado se resuelve
contra `conest` por `cod`, con `LEFT JOIN` deliberado para que un fallo de
maestro no se confunda con «la reclamación no existe» (R2).
*Observación, no reparo*: `escrituras.py` sí lleva tres enteros —`LOG_ORIGEN = 0`,
`LOG_OPERACION_PROCESO = 5`, `LOG_REALIZADO = 1`—. **No son estados de ningún
concepto**: son columnas del registro de `dbo.log`, medidas homogéneas en las
6.843 filas, van como parámetros y no pegadas al texto, y está documentado en el
docstring del módulo y en el del propio test. Lo doy por correcto. Igual
`SIGRID_TIP_RECLAMACION = 708`: es un `tip`, no un `est`, es configurable, y R4
se cumple porque el `JOIN` contra `conest` usa `c.tip` de la reclamación leída,
no la constante.

**R20 · la precondición es propia.** Barrido mío con
`grep -rniE "\b(rcg|gra)\b"` sobre `domain/`, `application/`, `infrastructure/`,
`interface_adapters/`, `config/`, `function_app.py`, `services/postventa-front/js`
e `index.html`: **cero coincidencias**. Con control positivo: el mismo patrón sí
acierta en los tests, así que el grep funciona. `Reclamacion` no tiene siquiera
campo de gráficos, que es la forma más barata de que R20 no se incumpla por
descuido.

**T21 · `azure-apps` commit `3c1c588`.** Verificado en el otro repositorio.
Árbol limpio, un solo fichero (`postventa_incidencias.md`, +140/-11), sin remoto
configurado (así que «sin push» es trivialmente cierto). **Dice lo que debe:**
que el servicio **escribe** en el ERP (en tres sitios distintos), **qué**
escribe (`con.est` resuelto contra `conest` por código + fila en `dbo.log`, en
un batch transaccional con tope de 2, y «**Nada más**. Ni `con.tiemod`…»), y **el
obstáculo de `design.md` §11** para F-012 («el binario vive en la base
documental […] queda fuera de `ALLOWED_WRITE_DATABASES` **a propósito** […] es
una decisión del **dueño de `sigrid-api`**»). **Y no duplica** el diccionario ni
el contrato de la pasarela. Barrido de secretos sobre el fichero completo: cero
hallazgos. Tres reparos menores, ninguno bloqueante, en §6.3.

### 6.2 · Datos personales, secretos y el borde HTTP

- **R44/R45/R46 · verificado por barrido propio**, no por lectura del informe.
  Las 12 llamadas a logger del código de producción de F-009 interpolan
  únicamente: `hash` del parte (opaco), código de incidencia, códigos de estado,
  nº de filas, duración, entorno y booleanos. **Ni un correo, ni un login, ni un
  `oid`, ni nada del papel.** `cerrar.py:_como_contexto` reconstruye el contexto
  **sin extracción y con `contenido=b""`**, así que el DNI y las observaciones
  manuscritas ni siquiera entran en el proceso.
- **La excepción de R45 está bien cerrada.** El mensaje de R31 sí nombra el
  correo (`paso_cierre.py:553-557`), pero el borde **no lo registra**:
  `function_app.py:721` hace `log.info("cerrar no procede: %s",
  type(error).__name__)`, y ese `except` cubre los ocho errores de 409, que es
  el único camino por el que ese mensaje sale. **El correo va a la respuesta,
  nunca al log.**
- **R46**: la clave va solo en cabecera (`_cabeceras`), y `_fallo` compone el
  motivo con la operación y un motivo acotado — **nunca `respuesta.text`**. La
  fábrica nombra las variables que faltan y jamás sus valores.
- **R51**: la respuesta lleva exactamente `hash_parte`, `numero_incidencia`,
  `estado`, `filas_afectadas`, `dry_run` y `avisos`. Ni campos manuscritos, ni
  PDF, ni configuración del destino, ni el `oid`. Los dos campos que sí salen y
  podrían levantar la ceja —`login_sigrid` y `descripcion`— **los exige R9
  explícitamente**, y R45 rige el log, no la respuesta.
- **DDL**: `08_usuarios_sigrid.sql` es `CREATE TABLE IF NOT EXISTS
  postventa.usuarios_sigrid`. **Idempotente, en el esquema propio, y `public` no
  aparece en ningún `.sql` del proyecto.** Los ocho ficheros de DDL crean
  exclusivamente `postventa.*`.
- **`infra/07_alta_usuario_sigrid.ps1`**: **no escribe en Sigrid, ni una
  sentencia** — su única llamada al ERP es `SELECT COUNT(*) FROM dbo.usu`.
  Escribe solo en PostgreSQL con `ON CONFLICT … DO UPDATE` (re-ejecutable).
  Secretos por `Read-Host -AsSecureString`, en variables `*_TEMP` que borra en
  las dos rutas de salida.
- **Front**: R9 pinta las **cinco** cosas (`index.html:327-339`), R21 se pinta
  **siempre** —el `<p>` del aviso no tiene `x-show` propio, y `_plan()` lo fija
  en las tres salidas de `evaluar`—, R15 caduca a **60 s** y está aplicada al
  cierre (`app.js:523-535`), y R12 tiene dos puertas en el front más dos en el
  backend (`valor is True`, para que `"false"` no cuente).

### 6.3 · Observaciones que NO bloquean, pero conviene arreglar

1. **`progress/impl_F-009.md` §7.3 dice: «los ficheros nuevos de F-009 pasan
   `ruff check` sin un solo aviso». No es cierto.** Lo comprobé:
   `services/postventa-api/application/pipelines/paso_cierre.py:41:1: I001
   Import block is un-sorted or un-formatted` — `CuerpoDeCierreInvalido` va
   detrás de `ErrorDePersistencia`. Es **1 de los 59** avisos del proyecto, se
   arregla con `--fix`, y no bloquea nada. Pero es un dato inexacto en la
   sección de evidencias de una feature `critico`, y ahí no se puede afinar
   menos que en el resto.
2. **`requirements.md` no lista R53 entre los `MANUAL (humano)`.** Su tabla de
   trazabilidad final solo nombra R22, R26, R25, R30, R31 y R33, así que R53
   parece prometer un test unitario que no existe ni puede existir. `tasks.md`
   T21 sí lo declara `MANUAL`. Una fila en esa tabla lo cierra.
3. **`Reclamacion.estado_destino_est` está anotado `int`** pero
   `fila_a_reclamacion` le asigna `None` cuando el `LEFT JOIN` no casa (y
   `reclamacion_unica` cuenta con ello para levantar R2). Debería ser
   `int | None`. Es tipado, no comportamiento.
4. **`azure-apps/postventa_incidencias.md`**, tres detalles: (a) **no enlaza** a
   `sigrid_api.md` ni a `sigrid_tablas.md` —no los duplica, que es la mitad
   importante, pero le falta el puntero que sí tiene `dedicacion.md`—;
   (b) el «qué se rompe si» cubre `ALLOWED_WRITE_PREFIXES` y
   `ALLOWED_WRITE_DATABASES` pero **omite `REQUIRE_WHERE_ON_UPDATE_DELETE`** y
   los topes de filas/sentencias por batch; (c) nunca nombra `ruesma_rep`, solo
   «la base documental», así que quien lea solo ese documento no puede casarlo
   con `ALLOWED_WRITE_DATABASES`. Y su cabecera apunta a un commit de origen ya
   desfasado (`2446c88`, con 11 commits por delante).
5. **Calidad de `services/postventa-front/tests/test_f009_front.py`.** Los
   tests JS son buenos y conductuales; este es el flojo. Dos de los siete casos
   parametrizados de R9 **no pueden fallar** —`"incidencia"` aparece en prosa
   ajena del `index.html`, y `"descripcion"` es subcadena de
   `estado_origen.descripcion`—, y `:129` es un assert tautológico
   (`assert "sin gráfico" not in html.lower() or "aviso_sin_grafico" in html`,
   con la segunda rama ya garantizada por la línea anterior). R15 aplicada al
   cierre se verifica con `codigo.count("window.Confirmacion.resolver(") >= 2`,
   que es un grep, no una prueba. Se salvan `test_f009_r21_*` (exige que ninguna
   línea del aviso lleve `x-show`) y `test_f009_r8_*` (compara posiciones).
6. **R13 no tiene front.** `grep -rn "auto_cierre\|autoCierre"` sobre `js/`,
   `index.html` y las dos suites del front: **cero**. El backend lo implementa y
   lo prueba; el front manda siempre `confirmado: true`, así que el auto-cierre
   solo es alcanzable llamando al endpoint a mano. No incumple R12 y no bloquea,
   pero R13 está a medias y conviene que conste.
7. **`docs/ARCHITECTURE.md:288-294` duplica el diccionario de Sigrid** (`upv`,
   `rcp`, `rcpint`, con listas de campos) **justo después** de decir «no se
   duplica aquí». Es **preexistente, de F-008**, y F-009 no lo ha ampliado, pero
   es exactamente la divergencia que prohíbe el `CLAUDE.md`.
8. **Propuesta del implementer que suscribo** (`impl_F-009.md` §6.3):
   `azure-apps/sigrid_api.md` §10 lista quién consume la pasarela «para
   dimensionar el impacto de cualquier cambio», y `postventa-incidencias` **no
   está**. Con F-009 pasa a ser **el primer escritor genérico por `sql/write`
   del ecosistema**, así que hoy el dueño de `sigrid-api` que lea esa tabla
   concluiría que nadie escribe. Es el documento de otro proyecto: se lleva a su
   dueño, no se toca.

## 7 · Cambios requeridos

Ordenados por lo que cuestan. Los tres primeros cierran las casillas vacías.

1. **Trasladar los 26 análisis de supervivientes a
   `progress/mutacion_F-009.md`**, sustituyendo cada bloque
   `#### Análisis (PENDIENTE del implementer)` por el texto que ya está escrito
   en `progress/impl_F-009.md` §7.2. Es copiar y pegar, y sin ello T28 los
   perderá al regenerar el informe (§4.5). *Fichero: `progress/mutacion_F-009.md`,
   los 26 bloques de las líneas 52 a 302.*

2. **Cerrar los tres huecos declarados, con un test cada uno** (§4). Son dos
   ficheros y un commit:
   - `infrastructure/sigrid/cliente.py:347` — un test que mande
     `RespuestaFalsa(200, {"total_affected_rows": 2})` **sin la clave `ok`** y
     espere `CierreFallido`. *(superviviente 21)*
   - `infrastructure/sigrid/consultas.py:202` y `:207` — un test de
     `fila_a_reclamacion` que compruebe que una fila **con** descripción y
     estado de destino legibles los devuelve **tal cual**, y otro que compruebe
     que un `NULL` sale como cadena vacía y **no** como `"None"`.
     *(supervivientes 22 y 23)*

   Si en vez de escribirlos se prefiere aceptarlos como riesgo, es **decisión
   del humano** y tiene que quedar escrita: `critico` no admite que la tome el
   implementer ni el reviewer.

3. **Poner las verificaciones `MANUAL (humano)` de T22–T27 en
   `progress/current.md`, con su comando exacto** (checkpoint C4). No basta la
   prosa que hay hoy en `:12-14` ni el listado de `:197-204`, que además está
   dentro de un bloque de sesión anterior. Hace falta, por tarea, el comando tal
   y como se va a teclear: el `az functionapp config appsettings set … --settings
   CIERRE_HABILITADO=true` de apertura y el de cierre, la llamada a
   `POST /api/cerrar` con su cuerpo, y las lecturas de comprobación de T24 —los
   nueve pasos— con sus valores, no con `?`. **Y avisar de lo que dice
   `impl_F-009.md` §6.1: con el interruptor apagado ni el dry-run de T22
   funciona**, porque la fábrica se niega antes de leer. Eso hay que saberlo
   antes de estar delante del ERP, no después.

4. **Podar `progress/current.md`** (checkpoint C2): dejar solo la sesión activa
   y llevar a `progress/history.md` el bloque `## Sesión anterior (2026-08-26,
   tarde)` de `:208` en adelante, y los tres estados de F-009 ya superados.
   **Es deuda heredada, no la trajo F-009**, pero C2 se evalúa al cerrar y hoy
   está vacía. Tarea del líder, no del implementer.

5. **Corregir el dato inexacto de `impl_F-009.md` §7.3** sobre `ruff`, y de paso
   arreglar el `I001` de `paso_cierre.py:41` (§6.3.1). Un `ruff check --fix`
   sobre ese fichero y una frase.

**No requerido para aprobar, pero anotado para el humano**: los puntos 2 a 8 de
§6.3 (la fila de R53 en `requirements.md`, el tipado de `estado_destino_est`,
los tres detalles del documento de `azure-apps`, los asserts inertes del test
del front, R13 sin front, la duplicación heredada de `ARCHITECTURE.md`, y la
propuesta de añadir `postventa-incidencias` a `sigrid_api.md` §10).

## 8 · Lo que queda pendiente del bloque 8 (fuera de esta review)

**Ni una casilla marcada, y así debe seguir hasta que lo ejecute el humano desde
el entorno desplegado**, con autorización expresa para la incidencia concreta.
Nada de esto se ha ejecutado nunca contra el ERP real:

- **T22** · dry-run real contra una reclamación de Mirasierra, sin escribir.
- **T23** · la siembra del login contra `dbo.usu`, en sus tres pasos (R30–R33).
- **T24** · **el primer cierre real**, con los nueve pasos de `tasks.md:174-232`.
  Dentro de él, el **paso 7 incluye mirar la hora** de la fila de `dbo.log`: es
  la única decisión de la feature que no se pudo tomar con un dato
  (`impl_F-009.md` §3.3.a, el huso `Europe/Madrid`).
- **T25** · que el `tex` propio se pueda filtrar y devuelva exactamente los
  cierres de este servicio.
- **T26** · que `SqlWriteGuard` acepte el batch con `WITH (UPDLOCK, HOLDLOCK)`.
  **Si lo rechaza, no se improvisa: la feature se marca `blocked` y se para.**
- **T27** · reintento sobre lo ya cerrado (R18, R42).

Y del bloque 9, **T28**: la campaña de confirmación. Hoy **el cero de
supervivientes que exige `critico` está razonado, no demostrado** (§4.3). Son
~43 minutos de reloj.

Los cuatro requisitos que ningún test unitario puede cubrir —que el batch sea de
verdad transaccional (R22, R26), que la reserva del `ide` aguante bajo
concurrencia, que el `tex` se filtre (R25) y que los logins existan (R30, R31,
R33)— los declara `MANUAL (humano)` la propia `requirements.md`, y ahí siguen.

## 9 · Automejora del protocolo (propuesta, no aplicada)

Dos cosas que esta review ha enseñado, para que las valore el humano:

1. **`CHECKPOINTS.md` C4 bis debería decir dónde va el análisis de los
   supervivientes, y no solo que esté completo.** Un implementer diligente puede
   escribirlo entero —como aquí— y aun así incumplir el checkpoint por ponerlo
   en `impl_F-XXX.md` en vez de en `mutacion_F-XXX.md`. La redacción actual
   («tiene su sección de análisis completada») no dice «en el informe de
   mutación», y la consecuencia real —que `analisis_escritos()` los pierda al
   regenerar— no está escrita en ningún sitio. Propongo añadir una frase:
   *«El análisis va en `progress/mutacion_F-XXX.md`, sustituyendo el bloque
   `PENDIENTE` de cada superviviente. La herramienta lo relee de ahí para
   conservarlo al regenerar el informe; escrito en otro fichero se pierde en la
   siguiente campaña.»*

2. **`CHECKPOINTS.md` C4 debería decir qué es «comando exacto».** Hoy dice que
   las verificaciones `MANUAL (humano)` van en `progress/current.md` «con su
   comando exacto», y aquí `tasks.md` traía un procedimiento excelente de nueve
   pasos con el SQL parametrizado (`WHERE tip = ? AND cod = ?`). Es mejor
   documentación que muchos comandos, y aun así no cumple. Propongo aclarar:
   *«Exacto significa ejecutable: los marcadores resueltos, el recurso nombrado
   y las puertas que haya que abrir y cerrar antes y después.»* Si se prefiere lo
   contrario —admitir el procedimiento en `tasks.md` y que `current.md` lo
   enlace— también vale, pero hoy el checkpoint dice una cosa y la práctica hace
   otra, y eso se resuelve en el fichero, no en cada review.
