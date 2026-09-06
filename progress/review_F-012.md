<!-- progress/review_F-012.md -->
# F-012 · Subir el parte a Sigrid como gráfico — review · **APROBADO**

**Veredicto: APROBADO**

> Alcance revisado: `git diff feature/F-009-cierre-sigrid...HEAD` (71 ficheros,
> +12.879/−257), **T1–T24 y T33**. El bloque 9 (T25–T32) y T34 **no entran**:
> son `MANUAL (humano)` / del líder por encargo, y quedan listados en §7 como
> pendientes, no como reparos.
> Rama `feature/F-012-grafico-sigrid`, sin cambiarla. **No se ha ejecutado
> nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL compartido ni
> SharePoint: ni una lectura.
> `bash harness/init.sh` **en verde** el 2026-09-06 (ver §1).

**Lo primero, porque es lo que pesa.** Esta feature es la escritura más
delicada que ha hecho el proyecto —dos bases del ERP de producción y el PDF con
el DNI manuscrito de un cliente viajando dentro— y el trabajo está a esa
altura. Las tres verificaciones independientes que he hecho (contrato contra el
código real de la pasarela, campaña de mutación recalculada desde cero,
auditoría de seguridad de scripts, DDL, logs y guardia de red) **han cuadrado
las tres**. Los dos hallazgos que la mutación destapó —el `or` de la puerta de
R14 y los cuatro `bool(datos.get(..., False))` de `graficos.py`— son
exactamente los que justifican que exista el nivel `critico`: el primero dejaba
subir al ERP el parte de una incidencia sin validar, y el segundo daba por
adjuntado un gráfico que no lo estaba. Los dos se cazaron **con tests, sin
tocar una línea de producción**.

Los reparos que siguen son dos, ninguno bloqueante, y ninguno toca el código
que escribe en el ERP.

---

## 1 · Nivel de rigor y puertas que exige

| | |
|---|---|
| **Nivel declarado** (`harness/features.json`) | **`critico`** |
| **Puertas que exige** (`CHECKPOINTS.md` §Niveles) | C1–C5 + C3 bis + tests trazables + **fase RED** + **cobertura ≥ 80 %** + **campaña de mutación** + **cero supervivientes salvo justificación escrita aceptada por el humano** + verificaciones `MANUAL (humano)` con su comando exacto |

`bash harness/init.sh`, ejecutado por mí al abrir la review:

```
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 99.0% de 1079 líneas cambiadas cubiertas
     (1068/1079, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-012-grafico-sigrid
ENTORNO LISTO. Puedes trabajar.
```

`ruff`: **58 avisos, exactamente la deuda previa**. F-012 no añade ni uno
(comprobado contra el aviso de `init.sh`, que es el mismo número que declara el
informe del implementer).

---

## 2 · Las cuatro desviaciones de §3 del informe, una a una

El encargo pide evaluarlas de forma individual. Las cuatro se **aceptan**, y
tres de ellas mejoran la spec en vez de apartarse de ella.

### 2.1 · `ResultadoGrafico.plan` anulable (§3.1) — **ACEPTADA**

`design.md` §6 lo declara obligatorio, y no puede serlo: **R24 prohíbe llamar a
nadie** cuando la traza local ya dice `adjuntado`, así que en ese camino no
existe reclamación leída con la que construir un `PlanDeGrafico`. Fabricar uno
desde la traza sería **enseñar un dry-run que nadie ha ejecutado**, y esta
feature entera se sostiene sobre que el dry-run que se enseña es el que se
ejecutó. La alternativa —relajar R24 y llamar a la pasarela para poder rellenar
el plan— sería peor: rompe el requisito para salvar una anotación de tipo.

Verificado en `domain/models/grafico.py` (`plan: PlanDeGrafico | None = None`,
más el campo `traza` nuevo) y en el borde, que lo serializa como
`dry_run.ya_estaba = true` (`interface_adapters/api/adjuntar.py:347`). Dos
tests lo fijan, incluido uno negativo (`..._no_se_inventa_un_dry_run`).

**La desviación está bien argumentada y bien documentada en el docstring del
propio dataclass.** Lo único que falta es que `design.md` §6 lo recoja; queda
como sugerencia S5.

### 2.2 · El dry-run también deja traza de `error` (§3.2) — **ACEPTADA**

`design.md` §7.3 asigna traza `error` a los códigos de rechazo **sin decir en
qué fase**, así que esto es una precisión y no una contradicción. Y es la
precisión correcta: un rechazo en el dry-run —clase no permitida, concepto
inexistente— **es información sobre este parte**, y es literalmente lo que T31
del bloque 9 va a verificar. Sin traza, T31 no tiene qué mirar.

Lo que hace que la acepte sin reservas es la excepción, que está bien elegida:
`EscrituraDocumentalDeshabilitada` (R32) **no deja ninguna traza**, porque no
ha pasado nada con este parte —lo que falta es una App Setting de otro
proyecto— y una traza de `error` culparía al parte. Verificado en
`application/pipelines/paso_grafico.py`, función `_dry_run`: el `except
EscrituraDocumentalDeshabilitada: raise` va **antes** del `except Exception`, y
este último siempre re-levanta (no traga nada). Tiene test propio
(`test_f012_r32_una_precondicion_de_la_pasarela_no_deja_traza`).

Comprobado además que esa traza de `error` **no puede pisar un `adjuntado`**:
`upsert_grafico` lleva `WHERE graficos.estado <> 'adjuntado'` (R30).

### 2.3 · Los cimientos de T2 adelantados a T1 (§3.3) — **ACEPTADA**

Es la regla correcta —**cada commit deja el árbol compilando**— aplicada a una
dependencia que `tasks.md` había colocado al revés: `domain/models/grafico.py`
no importa sin `EstadoGrafico`, `TrazaGrafico` y los ocho errores. Mover código
entre dos commits consecutivos de la misma persona, dejando T2 con el puerto,
los dos métodos del repositorio y el test de arquitectura, no pierde nada.
`tasks.md` lo refleja y ambos commits existen (`51c2578`, `4e9e215`).

### 2.4 · `_exigir_adjuntado` antes de la autorización (§3.4) — **ACEPTADA**

`tasks.md` no fija el orden, así que esto es una decisión, no una desviación.
Y la decisión es buena por la razón que da el informe: con `commit`, sin
`confirmado` y sin gráfico, **lo que falta de verdad es el gráfico**; al revés,
quien recibe el 400 cree que basta con confirmar, confirma, y se come el mismo
409 una pantalla después.

He comprobado lo que de verdad importaba aquí, que es que el orden **no abre
ninguna puerta**: las dos comprobaciones están antes de `_escribir`, así que en
ninguna de las dos ordenaciones se toca el ERP
(`application/pipelines/paso_cierre.py:188-195`). Lo único que cambia es qué
mensaje ve quien llama. Test:
`test_f012_r2_la_precondicion_se_comprueba_antes_de_la_autorizacion`.

---

## 3 · Trazabilidad: requisito → test

**70 requisitos EARS. 64 con test `test_f012_rN_*` trazable por nombre, 6 sin
él, los 6 justificados.** Tabla construida recorriendo mecánicamente los
nombres de test de `services/postventa-api/tests/`,
`services/postventa-front/tests/` y `tests_js/`, no leyendo el informe.

### Los 64 con test (recuento por requisito)

| Req | Tests | Req | Tests | Req | Tests | Req | Tests |
|---|--:|---|--:|---|--:|---|--:|
| R2 | 4 | R20 | 5 | R38 | 3 | R56 | 5 |
| R5 | 1 | R21 | 7 | R39 | 5 | R57 | 5 |
| R6 | 3 | R22 | 3 | R40 | 3 | R58 | 7 |
| R7 | 5 | R23 | 6 | R41 | 1 | R59 | 3 |
| R8 | 2 | R24 | 7 | R42 | 2 | R60 | 2 |
| R9 | 7 | R25 | 4 | R43 | 8 | R61 | 2 |
| R10 | 2 | R26 | 8 | R44 | 8 | R62 | 1 |
| R11 | 3 | R27 | 2 | R45 | 4 | R63 | 4 |
| R12 | 8 | R28 | 3 | R46 | 3 | R64 | 4 |
| R13 | 2 | R29 | 3 | R47 | 3 | R65 | 5 |
| R14 | 5 | R30 | 4 | R48 | 1 | R66 | 2 |
| R15 | 2 | R31 | 3 | R49 | 6 | R67 | 1 |
| R16 | 4 | R32 | 5 | R50 | 2 | R68 | 11 |
| R17 | 2 | R33 | 4 | R51 | 2 | R69 | 6 |
| R18 | 7 | R34 | 8 | R52 | 2 | | |
| R19 | 6 | R35 | 1 | R53 | 10 | | |
| | | R36 | 1 | R55 | 6 | | |

### Los 6 sin test `test_f012_rN_*`, con su justificación

| Req | Estado | Justificación |
|---|---|---|
| **R1** | `MANUAL (humano)` | Declarado así en la tabla de `requirements.md`: que la reclamación quede abierta con su gráfico solo lo prueba el ERP. **T25–T29.** |
| **R3** | `MANUAL (humano)` | Íd.: el reintento que cierra sin volver a adjuntar exige las dos escrituras reales. **T29.** |
| **R37** | `MANUAL (humano)` | Íd.: la duración real del dry-run y del commit con un parte de tamaño real. **T25, T27.** |
| **R4** | **CUBIERTO**, con el número solo en el docstring | `test_f012_r2_el_auto_cierre_tampoco_se_salta_la_precondicion` (`test_f012_cerrar_exige_grafico.py:233`), cuyo docstring dice «R4 · ni siquiera con auto-cierre se cierra sin el gráfico» y que construye `Preferencias(auto_cierre=True)`. **Cubierto de verdad; el nombre no lo dice.** Sugerencia S4. |
| **R54** | **CUBIERTO**, íd. | `test_f012_logs_sin_datos_personales.py:225-230`, bloque «R53, R54 · el camino feliz, con todo el dato personal dentro del PDF», el control negativo principal. **Cubierto de verdad; el nombre solo lleva `r53`.** Sugerencia S4. |
| **R70** | **VERIFICADO A MANO** (no hay test posible) | El documento vive en **otro repositorio**. Lo he leído: `azure-apps/postventa_incidencias.md`, commit local `72b8fa3`, sin push. Ver §5.3. |

**Ningún requisito queda sin cubrir ni sin justificar.**

---

## 4 · Las reglas duras del encargo, comprobadas

### 4.1 · Ningún test toca red, BBDD ni IA — **LIMPIO**

La guardia de `tests/conftest.py:36-69` (y su gemela del front,
`services/postventa-front/tests/conftest.py:34-63`) sigue sustituyendo
`socket.socket.connect` por `_conexion_prohibida`, y **el diff de F-012 no toca
ninguno de los dos conftest**. Ningún test nuevo la parchea, la salta ni la
desactiva: los aciertos de `socket` en los `test_f012_*` son menciones en
docstrings. Sin `requests`, sin `httpx.Client`, sin `google.generativeai`; el
único `import psycopg` (`test_f012_repositorio_graficos.py:27`) se usa solo
para clases de excepción. Y hay un cinturón más: con `ENTORNO=test` ninguno de
los dos adaptadores de Sigrid **se puede construir**
(`test_f012_r41_...no_se_puede_construir_nada`). `pytest -k f012` → **447
passed**.

### 4.2 · Doble puerta `CIERRE_HABILITADO` — **LIMPIO, y son la misma puerta**

- **Constructor**: `infrastructure/sigrid/graficos.py:101-102` —
  `exigir_entorno_con_cierre(entorno)` y
  `exigir_interruptor_de_cierre(cierre_habilitado)`, las dos **antes** de
  asignar `base_url` o `api_key`.
- **Fábrica**: `infrastructure/sigrid/fabrica.py:126-128` (`construir_graficos`)
  — las mismas dos, más `_exigir_configuracion`.

Las dos funciones se importan de un **único** origen
(`infrastructure/sigrid/cliente.py:157,174`), sin duplicar listas:
`ENTORNOS_CON_CIERRE = ("dev", "pro")` y `if not habilitado`. `Ajustes.cierre_habilitado`
es `bool` con `default=False` (`config/settings.py:312-323`): **por omisión no
se escribe**. Y no hay forma de eludirlas: fuera de tests, el adaptador se
construye en exactamente dos sitios (la fábrica y `adjuntar.py:147`), y la
inyección del cliente de test no desactiva ninguna.

### 4.3 · Ni un dato personal ni un secreto — **LIMPIO**

Barrido propio sobre las líneas `+` del diff completo, con estos patrones:
GUID (`[0-9a-f]{8}-...-[0-9a-f]{12}`), `.azurewebsites.net`,
`.database.windows.net`, `.vault.azure.net`, `.blob.core.windows.net`,
`AccountKey=`, `(password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*"..."`,
`Bearer `, `code=`, IPv4, `...@ruesma.es`, DNI `\b\d{8}[A-Za-z]\b`, NIE
`\b[XYZ]\d{7}[A-Za-z]\b`.

**Resultado: cero secretos y cero datos personales reales.** Los únicos
aciertos son fixtures declaradamente sintéticos: `00000000T` (ocho ceros;
usado como DNI de prueba **y como control negativo**),
`clave-de-mentira-para-el-test`, `clavedefuncioninventadaparaeltest`,
`Nombreinventado`, `SHA256 = "a"*64`, `INCIDENCIA = "XX00.00/0000"`, correos
con TLD reservado `@ejemplo.invalido`. El «PDF con el DNI dentro» del control
negativo se **fabrica en el propio test** a partir de `FIRMA_PDF`; no es un
fichero real, y el test prohíbe además los primeros 32 caracteres del texto
codificado, para que «vuelco solo un trocito» tampoco pase.

**Binarios en git**: `git log --all --diff-filter=A --name-only` filtrado por
`.pdf|.docx|.xlsx|.pptx|.jpg|.jpeg|.png|.gif|.zip|.bin|^muestras/` → **cero**,
en **todo el historial**, no solo en esta rama. `.gitignore:6` `muestras/`,
`.gitignore:29` `*.pdf`. **`muestras/` sigue sin versionarse.**

**En los logs**: el `log.info` del adaptador
(`infrastructure/sigrid/graficos.py:125-134`) registra duración, banderas,
filas y bytes, y **nunca** el contenido, el texto codificado ni el `cod` (que
lleva el login del ERP dentro). En la rama de fallo se registra
`type(fallo).__name__` y **jamás** `str(fallo)`, que podría arrastrar la URL
con la clave de función (`graficos.py:178`). Es el detalle que más fácil se
escapa y está bien resuelto.

### 4.4 · DDL solo en el schema `postventa` e idempotente — **LIMPIO**

`infrastructure/persistencia/sql/09_graficos.sql`: **dos sentencias**,
`CREATE TABLE IF NOT EXISTS postventa.graficos` (:46) y
`CREATE INDEX IF NOT EXISTS ix_graficos_estado ON postventa.graficos (estado)`
(:69). Idempotente y reejecutable. Única clave ajena:
`REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE` (:48), tabla del
propio proyecto (R46). Ni `bytea` ni `blob`: solo `sha256 text` y
`bytes integer` (R45). Nada a nivel de servidor, nada fuera del esquema propio.
Por debajo, `infrastructure/persistencia/ddl.py` es una lista blanca que exige
cualificación con el esquema configurado, rechaza `public.` y prohíbe
`DROP SCHEMA`/`GRANT`/`ALTER SYSTEM` y los tipos binarios.

### 4.5 · `paso_cierre` cambiado lo mínimo — **CONFIRMADO**

El diff de `application/pipelines/paso_cierre.py` son **57 líneas** y hacen
exactamente tres cosas: leer `ctx.traza_grafico` del repositorio (R49), añadir
`_exigir_adjuntado` (R2) y hacer pública `exigir_autorizacion_para_escribir`
para que el gráfico reutilice la misma. **`infrastructure/sigrid/escrituras.py`
no aparece en el diff**: el batch de cierre y la fila de `dbo.log` no cambian
ni un carácter (R51). Y `_exigir_adjuntado` no nombra ni una tabla del ERP: la
precondición se lee de la traza propia (R52, R20 de F-009 intacto).

### 4.6 · Los tres scripts de `infra/` (15, 16, 17) — **solo lectura, sin literales sensibles**

Las cinco consultas al ERP son `SELECT` parametrizados con `?` vía
`Invoke-SigridLectura` → `/api/sql/read`. **Ni una** llamada a `sql/write`, a
`sigrid/concepto-grafico`, a `az ... set`, ni un `INSERT/UPDATE/DELETE/DROP/ALTER`.
El 16 usa `DATALENGTH(g.ima) AS bytes` (:189) y
`CASE WHEN g.ima IS NULL` (:154), y **nunca** trae la columna binaria; la única
vía que descarga el PDF es el modificador opcional `-DescargarYComparar`
(:237-279), que exige `-Sha256Esperado`, calcula el hash **en memoria** y no
escribe a disco. El 17 lee una sola sentencia contra `{esquema}.graficos` con
`$Esquema = "postventa"` por defecto y validación del identificador, y **no
imprime el `oid`**. Barrido de FQDN, GUID, IPv4, `code=`, `AccountKey`,
`Bearer`, base64 largo, sha256 de 64 hex, incidencias `RS\d{2}\.\d{2}/\d{4}`,
DNI/NIE y correos sobre los tres: **cero aciertos**. La clave y la contraseña
se piden por consola como `SecureString` y la clave viaja en cabecera
`x-functions-key`, nunca en la URL.

Con **un reparo**, D1, y tres sugerencias. Ver §6.

### 4.7 · El contrato con la pasarela (`sigrid_api.md` §8.8) — **RESPETADO**

Contrastado campo a campo contra §8.8 **y contra el código real de
`sigrid-api` en `dev`** (`domain/models/concepto_grafico_models.py`,
`attach_concepto_grafico_use_case.py`, `document_write_guard.py`), en solo
lectura.

- **Petición**: los diez campos exactos (`graficos.py:140-160`), ni uno de más
  ni de menos, con los tipos correctos y `commit` como booleano JSON nativo.
  Topes 48/255/24 idénticos a los suyos, y `componer_peticion` **rechaza** en
  vez de truncar. Comprobado incluso el borde del tamaño: 10.485.760 B dan
  13.981.016 caracteres de base64 y el pre-chequeo de la pasarela admite hasta
  13.981.018 — **no hay off-by-one**.
- **`ok && (committed || idempotente)`**: `domain/models/grafico.py:348`,
  literal. Los cuatro cuadrantes contrastados contra el código de la pasarela:
  commit real (T,T,F)→True; idempotente (T,F,T)→True; dry-run (T,F,F)→False;
  `ok:false`→False.
- **El `committed: false` del caso idempotente**: tratado como éxito, y —esto
  es lo que se rompe en un consumidor ingenuo— la exigencia de tres filas está
  **condicionada a `committed`** (`paso_grafico.py:544`), así que el
  `filas_afectadas: 0` del idempotente no la dispara. Tampoco se confunde con
  el dry-run: la respuesta del dry-run nunca pasa por `_exigir_colgado`, y un
  documento ya colgado detectado en dry-run **no** se marca `adjuntado`, solo
  alimenta `plan.idempotente_previsto`.
- **Los doce códigos**: comparación de conjuntos contra
  `concepto_grafico_models.py:22-37`. **12 declarados, 12 cubiertos, 0 solapes,
  0 faltan, 0 sobran** entre las tres listas cerradas de
  `domain/models/grafico.py:110-135`. Lo no listado cae en `desconocido` → 502,
  que es la elección conservadora correcta. Coherencia por familias verificada
  contra dónde se levanta cada uno en la pasarela: los reintentables con
  rollback o pre-escritura, los de precondición como App Settings suyas, y los
  siete de rechazo antes de cualquier `INSERT`.
- **R20**: verificado en `paso_grafico.py` que **no existe camino** que envíe
  `commit=True` sin el dry-run inmediatamente anterior en la misma llamada.

Dos observaciones de diagnóstico, ninguna de seguridad, en §6 (S6, S7).

---

## 5 · Las puertas de C4 bis, verificadas de forma independiente

### 5.1 · Fase RED — **[x]**

El informe trae **salida real pegada**, con el comando exacto, para nueve
tramos (T1, T2, T4, T5, T7, T8, T9, T11, T12). No es prosa: son `ImportError`
y `AssertionError` con su traza. Y hay dos cosas que valoro por encima del
cumplimiento formal:

- **Dos segundas vueltas en rojo** contra el propio código ya escrito (el
  control de `base64` en T2 y el de `Retrying` en T7), que es la señal de que
  los controles negativos funcionan de verdad.
- **T11 no tenía fase RED posible** —los 11 tests pasaron a la primera— y se
  resolvió como manda `CHECKPOINTS.md`: rompiendo deliberadamente una **copia
  aislada en el scratchpad**, nunca el árbol real, y pegando la traza del
  fallo. El árbol está limpio (`git status` vacío), así que la copia rota no
  entró.
- En T12, **22 tests de F-009 en rojo** al morder la precondición nueva: la
  mejor evidencia posible de que R2 no es decorativa.

### 5.2 · Cobertura — **[x]**

`[OK] PUERTA COBERTURA: 99.0% de 1079 líneas cambiadas cubiertas (1068/1079,
umbral 80%, nivel critico)`. Ejecutado por mí. 11 líneas sin cubrir sobre 1.079,
con el umbral 19 puntos por debajo.

### 5.3 · Mutación — **[x], recalculada desde cero**

**El «Tiempo total» del informe es 922,8 s (15,4 min), por encima de los 5
minutos de `CHECKPOINTS.md`, así que me he quedado en el recálculo puro y NO he
reejecutado la campaña. Lo digo explícitamente, como exige el checkpoint.**

Recálculo independiente con `harness.alcance` +
`harness.mutacion.generar_mutantes` (cálculo puro, sin ejecutar la suite y sin
escribir en disco), con la misma base `feature/F-009-cierre-sigrid`:

| | Informe | Recalculado | |
|---|---|---|---|
| Refs del diff | `c93ed49e…` .. `feature/F-012-grafico-sigrid` | idénticas | ✅ |
| Ficheros en alcance | 18 | 18 | ✅ |
| Líneas en alcance | 2.721 | 2.721 (las 18 filas coinciden **una a una**) | ✅ |
| Mutantes | 101 | **101** | ✅ |
| Muertos / supervivientes / timeouts | 96 / 5 / 0 | — | |

**Muestreo de supervivientes**: he comprobado **diez** (los 5 finales más 5 de
la primera pasada) contra los mutantes realmente generados, y los diez existen
con **mismo fichero, misma línea, mismo operador y mismo texto
original→mutado**, carácter a carácter. Caso fino incluido: los supervivientes
4 y 5 de la primera pasada son **dos mutantes distintos de la misma línea 402**
(columnas 47 y 73), y el generador produce exactamente esos dos. No es relleno.

**Control de cero mutantes**: los 7 ficheros del alcance con 0 mutantes son
`contexto_parte.py`, `cierre.py`, los dos puertos, `mapeo.py`, `fabrica.py` y
`cerrar.py`. Revisadas sus líneas en alcance una a una: **todas son docstrings,
comentarios, imports, firmas y anotaciones de tipo**. El único caso con
operador real, `cerrar.py:311` (`is not None`), es `ast.IsNot`, que no está en
la tabla de comparaciones del mutador. **Cero legítimo**, no un generador roto.

**Coste por mutante** (`CHECKPOINTS.md` C4 bis): 922,8 s × 8 workers ÷ 101 =
**73,1 s/mutante**, contra una suite de 39,65 s en solitario y **77,4 s con 8
workers** por contención, según mide `harness/rigor.json`. Cae justo por debajo
de esa cifra, que es lo esperado con `pytest -x` y 96 de 101 mutantes muertos.
**Plausible, no sospechosa.** El aumento 853,8 → 922,8 s entre pasadas también
cuadra: T33 metió 22 tests nuevos.

`git status` limpio antes y después del recálculo.

### 5.4 · Los 5 supervivientes: ¿son equivalentes? — **SÍ, comprobado uno a uno**

He ejecutado yo los `grep` que el informe cita y he **leído los sitios de
llamada**, que es lo que el `grep` a solas no demuestra:

| # | Mutación | Comprobación | Veredicto |
|---:|---|---|---|
| 11 | `errores.py:867` `reintento_seguro: bool = True` → `False` | **3** sitios de producción: `paso_grafico.py:538`, `:545` y `graficos.py:298`. **Los tres pasan `reintento_seguro=True` explícito.** Leídos. | **Equivalente** |
| 15 | `grafico.py:184` `ya_cerrada: bool = False` → `True` | **1** sitio, `_plan` (`paso_grafico.py:579`), que pasa `ya_cerrada=` explícito | **Equivalente** |
| 16 | `grafico.py:187` `idempotente_previsto: bool = False` → `True` | Íd., mismo sitio, `idempotente_previsto=` explícito | **Equivalente** |
| 22 | `persistencia.py:227` `idempotente: bool = False` → `True` | **2** sitios: `paso_grafico.py:617` (`idempotente=respuesta.idempotente if ... else False`) y `mapeo.py:278` (`idempotente=bool(idempotente)`). **Los dos explícitos.** | **Equivalente** |
| 32 | `adjuntar.py:251` `confianza_observaciones=0` → `1` | Va en una `ResultadoValidacion` **reconstruida** de la que `paso_grafico` solo lee `veredicto` y `destino` (`:272-277`); `_serializar` devuelve **ocho claves fijas** que no la incluyen (`adjuntar.py:272-285`); no se persiste. **Ningún camino la lee.** Mismo patrón preexistente en `archivar.py:197` y `cerrar.py:219`. | **Equivalente** |

**Las cinco justificaciones son correctas y las he verificado, no leído.** Y
valoro que la distinción con el superviviente 30 (`confirmado: str | bool =
False`, que **sí** lleva test porque su valor por omisión **sí** se ejecuta) no
sea caprichosa: es exactamente la línea que separa un equivalente de un hueco.

**Reserva formal**: el nivel `critico` exige «cero supervivientes salvo
justificación escrita **aceptada por el humano**». La justificación está
escrita y verificada; **la aceptación es del humano** y queda en §7.

### 5.5 · Sección «Evidencias» — **[x], con los cinco números**

Tests (2.054 `api` + 130 `front`, ni uno rojo), cobertura de lo cambiado
(99,0 %), mutantes y supervivientes (101 / 5), tiempo de la suite (39,65 s en
solitario, 74,75 s dentro de `init.sh`) **y el nº de workers (8)**, sin el cual
no se puede calcular el coste por mutante. Los cinco están.

---

## 6 · Hallazgos por severidad

### BLOQUEANTES: **ninguno**

### DEBE CORREGIRSE (2)

**D1 · `infra/16_grafico_sigrid.ps1:276` — la casilla «bytes descargados»
siempre dirá 64.**

```powershell
Anotar -Que "bytes descargados" -Valor $huella.Length
```

`$huella` es la **cadena hexadecimal del sha256**, así que `.Length` vale
siempre 64, no el tamaño del PDF descargado. En un guion que el humano va a
recorrer **contra el ERP de producción** en T27 —donde la casilla de al lado
dice `DATALENGTH(ima)` con el tamaño real— una línea que anuncia «64 bytes»
induce a error justo en el momento de más riesgo de la feature. Debería ser
`$respuesta.Content.Length`, **capturado antes** de `$respuesta = $null` (:274).

Atenuante, y por eso no es bloqueante: la comprobación que de verdad sostiene
T27 es la de la línea siguiente (`sha256 del binario DENTRO del ERP`), que está
**correcta**. Esto es ruido que confunde, no un falso verde.

**Hay que corregirlo antes de que el humano abra la ventana del bloque 9**, que
es cuando el script se usa por primera vez.

**D2 · Dos comentarios del front siguen describiendo como vigente el aviso que
R48 derogó.**

- `services/postventa-front/js/api.js:443-445`: «…y el aviso de que la
  reclamación quedará cerrada sin el parte dentro del ERP. **Ese aviso hay que
  enseñarlo antes de que nadie confirme.**»
- `services/postventa-front/js/app.js:70-73`: «…y el aviso de que la
  reclamación quedará cerrada sin el parte dentro de Sigrid. Confirmar sin
  haberlo leído es lo que esto viene a evitar.»

Los dos ficheros los **toca F-012**, y el aviso ya no existe: R48 lo derogó y
el propio `domain/models/cierre.py` lo explica muy bien. El backend quedó
impecable en esto —hasta con controles negativos (`assert "aviso_sin_grafico"
not in ...`)—; el front se quedó a medias. No hay efecto funcional, pero es
literalmente el caso que `CLAUDE.md` describe: «un documento desactualizado que
parece vigente hace más daño que no tenerlo». Y el siguiente que lea `api.js`
buscará en la respuesta un campo que ya no llega.

### SUGERENCIAS (9)

**S1 · `test_f012_scripts_infra.py`: tres huecos enumerables.** El test es
sustantivo, no fachada —enumera cada `\bg\.ima\b` y exige que esté dentro de
`DATALENGTH(...)` o `IS NULL`, cruza el `ValidateSet` con el enum real del
dominio—, pero: `VERBOS_DE_ESCRITURA_EN_SIGRID` (:49-53) solo cubre
`INSERT INTO dbo.` / `UPDATE dbo.` / `DELETE FROM dbo.`, así que un
`DROP`/`TRUNCATE`/`MERGE`/`EXEC sp_` o un `INSERT INTO gra` sin prefijo
pasaría; la comprobación por ruta (:162-173) no cubre `documents/write` ni
`az ... set`; y el bloque «ningún valor» (:456-495) no tiene patrón de IP, ni
de FQDN genérico, ni de `code=`/`AccountKey`.

**S2 · `infra/16_grafico_sigrid.ps1:65`** — `$SigridBaseDocumental =
"ruesma_rep"` contradice literalmente la cabecera del propio script (:43-44:
«NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni las bases…»). No
es un secreto (el nombre lleva versionado desde F-008), pero o el valor sale
del fichero o la cabecera deja de prometer lo que no cumple.

**S3 · `infra/15_reclamaciones_obra_prueba.ps1:54`** — `$Tip = 708` es un
identificador real de la instalación quedando versionado, y la excepción que el
propio script declara (:32-35) cubre solo «el codigo de la OBRA DE PRUEBA».
Riesgo bajo (ya está en `.env.example`); es coherencia de la afirmación.

**S4 · Nomenclatura de dos tests.** R4 y R54 están cubiertos de verdad, pero el
número solo aparece en el docstring
(`test_f012_r2_el_auto_cierre_tampoco_se_salta_la_precondicion` y el bloque
`r53` de los logs). `CHECKPOINTS.md` C4 pide tests trazables `test_fXXX_rN_*`:
renombrarlos a `..._r2_r4_...` y `..._r53_r54_...` haría la trazabilidad
automática, que es de lo que va.

**S5 · `design.md` §6 no recoge las desviaciones 2.1 y 2.2.** Están bien
argumentadas en el código y en el informe, pero la spec sigue diciendo que
`ResultadoGrafico.plan` es obligatorio. Un renglón en §6 y otro en §7.3 cierran
el círculo.

**S6 · Dos códigos de la pasarela están sobrecargados en origen.** En
`sigrid-api`, `tipo_de_concepto_no_coincide` y `clase_de_grafico_no_permitida`
se levantan **tanto** por un error real de la petición **como** porque el
`contip`/`gratipide` no esté en su lista blanca —que está **vacía por
defecto**— (`document_write_guard.py:133-138,156-161`). Aquí los dos van a la
familia de rechazo → 409, tal y como **`design.md` §7.3 y R33 mandan
explícitamente**: la implementación es correcta y no hay riesgo. Lo que pasa es
que, si al dueño de la pasarela le falta la App Setting, el operador ve un 409
«el ERP ha quedado sin cambios» que le manda a mirar su petición cuando lo que
falta es configuración ajena —el caso para el que existe la familia de
precondición (503)—. **No es corregible desde este lado**: haría falta que
`sigrid-api` emitiera códigos distintos. Vale la pena proponérselo a su dueño.
El impacto ya está atenuado: `impl_F-012.md` §8.2 avisa de los dos casos con su
código HTTP.

**S7 · `sha256_no_coincide` clasificado como reintentable.** Es seguro (el ERP
no se tocó), pero es un fallo **determinista**: el consumidor calcula el hash de
los mismos bytes que envía, así que el reintento volverá a fallar salvo que la
causa fuera corrupción en tránsito. Decirle «el reintento es seguro» invita a un
bucle inútil. Matizar el texto bastaría.

**S8 · Cosmético.** El docstring de `_cuerpo` dice «Los diez campos del
contrato» (`graficos.py:141`) —correcto— mientras el test se llama
`test_f012_los_ocho_campos_del_contrato_viajan_tal_cual`
(`test_f012_adaptador_grafico.py:259`) y afirma seis. Solo son nombres.

**S9 · Automejora del arnés, para `arnes-base`.** La línea autogenerada de
`progress/mutacion_F-012.md` dice `Generado por python -m harness.mutacion
--feature F-012 --workers 8`, **sin `--base`**, porque `comando_de()`
(`harness/mutacion.py:572-582`) solo emite feature y workers. Ese comando **no
reproduce la campaña**: con la base por defecto (`dev`) el alcance sale 24
ficheros y 5.690 líneas, no 18/2.721. Aquí lo salva la prosa de cabecera, que
sí escribe el comando completo, pero un reviewer que se fiara de la línea
autogenerada obtendría otros números y creería estar ante un informe falso.
**Propuesta (no aplicada): que `comando_de()` incluya `--base` cuando no sea el
valor por defecto.** Es genérico: va a `arnes-base`.

### OBSERVACIONES, fuera del encargo

- **`peticion()` de `js/api.js` reintenta lo transitorio en todos los pasos,
  incluido `adjuntar` con `commit`** (`js/api.js:265-271`). Lo hereda de la
  sesión anterior y el implementer lo declara. **Aquí es seguro por
  construcción** —el endpoint es idempotente por tamaño y `sha256`, así que un
  segundo commit devuelve `idempotente: true`—, y lo he verificado leyendo la
  función. Queda escrito para que nadie lo lea como un reintento de escritura
  no controlado.
- **`infra/17:97-98` y el preexistente `infra/08:120-121`** usan
  `SecureStringToBSTR` sin el `ZeroFreeBSTR` correspondiente: la contraseña
  queda en memoria no gestionada. Riesgo bajo en un puesto de trabajo.
- **En el repositorio `azure-apps` hay un `.env` sin trackear y aparentemente
  no ignorado** (`git status` → `?? .env`). No es de esta feature ni de este
  repositorio, pero un `.env` que `git status` ofrece añadir es un accidente
  esperando: conviene que su dueño lo meta en `.gitignore`.

---

## 7 · Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. **Ejecutado por mí.**
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-012`); `init.sh` lo valida.
- [x] Rama `feature/F-012-grafico-sigrid`, la de la feature en curso.
- [x] `progress/current.md` describe la sesión activa; los bloques anteriores
      están fechados y ordenados, y el vigente encabeza el fichero.
- [x] Las features `done` tienen su resumen en `progress/history.md`.
      *(Nota, no reparo: `F-009` figura `blocked` a la espera de su propia
      verificación contra el ERP. Es estado previo y no lo reabro.)*

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `grep` de `from infrastructure`, `import
      infrastructure`, `from interface_adapters`, `requests`, `httpx`,
      `psycopg` y `base64` sobre `domain/` y `application/`: **cero
      aciertos**. El dominio del gráfico no sabe siquiera cómo se codifica el
      contenido para viajar, y hay un control negativo que lo fija.
- [x] Primera línea con la ruta relativa en los seis ficheros de código nuevos,
      los tres `.ps1`, el `.sql` y los dos del front. Comprobado uno a uno.
- [x] Sin `print()` de debug, sin TODO/FIXME nuevos, sin secretos
      hardcodeados (§4.3), sin dependencias nuevas.
- [x] La unidad de trabajo es el **parte**: todas las trazas van por
      `hash_parte`, y la clave ajena contra `postventa.partes` lo impone.
- [x] **Nada se cierra sin todas las validaciones**, y ahora **menos que
      antes**: el cierre exige además que el parte conste adjuntado (R2). Dry-run
      siempre primero y en la misma llamada (R20, verificado en el código).
- [x] Lo manuscrito no se descarta y una marca simple no cuenta como firma:
      F-012 no toca esa lógica, y la puerta de R14 exige el veredicto `apto` de
      F-004 antes de subir nada.
- [x] «Firmado no es conforme»: intacto; F-012 hereda la puerta de F-004.
- [x] **Reprocesar no duplica**, y esta feature lo refuerza con **dos capas**:
      la traza local por `hash` (R24, cero llamadas) y la idempotencia de la
      pasarela por tamaño + `sha256` (R25).
- [x] Nada hardcodea un número de estado. Y en la misma línea: `contip` sale de
      `reclamacion.tip` y `conide` de `reclamacion.ide` (R8, verificado en
      `grafico.py:328-329`), no de configuración; `gratipide` es
      `SIGRID_GRATIPIDE_PARTE` (R11).
- [x] **Ningún parte escaneado ni PDF ha entrado en git**, comprobado con
      `git log --all --diff-filter=A` sobre todo el historial (§4.3).

### C3 bis — Documentos que entran de fuera

**N/A justificado**: `git diff --name-only feature/F-009-cierre-sigrid...HEAD --
docs/referencia/` sale **vacío**. La feature no añade ni modifica ningún
fichero en `docs/referencia/`, así que el bloque no aplica. *(Aun así he hecho
el barrido de datos sensibles sobre todo el diff y sobre el commit de
`azure-apps`; resultados en §4.3 y §5.3 de este informe.)*

### C4 — La verificación es real

- [x] Cada requisito EARS con ≥ 1 test trazable, y todos pasan: **64 con test,
      6 justificados** (§3). `pytest -k f012` → 447 passed.
- [x] Los unit tests no tocan red ni BBDD (§4.1), y tampoco IA.
- [x] Las verificaciones `MANUAL (humano)` están listadas y pendientes. Los
      comandos exactos viven en `specs/F-012-grafico-sigrid/tasks.md`
      (T25–T32, con las llamadas literales a los scripts 15/16/17 y los códigos
      HTTP esperados), y `progress/current.md` las señala con sus
      precondiciones y el aviso de `CIERRE_HABILITADO`. *(Sugerencia menor: para
      F-009 la lista con comandos está volcada en `current.md`; para F-012 no.
      No es un `[ ]`: constan y son exactos.)*

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"` en `harness/features.json`.
- [x] **Fase RED**: salida real pegada en nueve tramos, más el caso especial de
      T11 resuelto en copia aislada (§5.1).
- [x] **Cobertura**: `[OK] 99,0 % de 1.079 líneas cambiadas`, umbral 80 % (§5.2).
- [x] **Mutación**: existe `progress/mutacion_F-012.md`, y sus totales
      **coinciden exactamente con mi recálculo independiente** de alcance y
      número de mutantes (§5.3).
- [x] **Los muertos, comprobados**: el «Tiempo total» declarado es **922,8 s
      (15,4 min), por encima de los 5 minutos**, así que —como permite el
      checkpoint— **me he quedado en el recálculo puro y NO he reejecutado la
      campaña. Queda dicho explícitamente.** El muestreo de diez supervivientes
      contra los mutantes reales sí lo he hecho, y cuadra carácter a carácter.
- [x] **La campaña tardó lo que tenía que tardar**: 73,1 s de tiempo-worker por
      mutante, contra una suite de 77,4 s con 8 workers según `harness/rigor.json`.
      Plausible (§5.3).
- [x] Ningún superviviente en `PENDIENTE`; los 5 finales tienen análisis
      completo y **he verificado las cinco justificaciones leyendo los sitios
      de llamada** (§5.4). **Con reserva formal**: en `critico` la
      *aceptación* de esos 5 es del humano, y está pendiente (§8).
- [x] «Evidencias» con los cuatro números **y el nº de workers** (§5.5).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A sin nada que justificar**: `harness/rutas_sensibles.json` **no existe** en
este repositorio (solo el `.ejemplo.json`), que es el caso mayoritario que el
propio checkpoint declara N/A.

### C5 — La sesión se cerró bien

- [x] **T1–T24 y T33 marcadas `[x]`**, con commit `F-012 Tn: ...` por tarea
      (27 commits en la rama). *(Cuatro commits agrupan tareas contiguas
      —T9+T10, T15+T16+T17, T19+T20, T22+T23+T24—, y en todos el mensaje nombra
      cada `Tn`. No lo cuento como reparo.)*
- [ ] **T25–T32 y T34 sin marcar** — **pendientes del humano y del líder, no
      un rechazo**, según el encargo. Constan aquí y en §8. Es el único
      checkbox vacío del recorrido y su motivo está escrito.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status` **vacío**
      antes y después de toda mi verificación.
- [x] `features.json` refleja el estado real (`F-012: in_progress`). El cambio
      a `done` lo aplica el líder tras el bloque 9.

---

## 8 · Lo que queda para el humano

1. **Aceptar (o no) los 5 supervivientes de mutación declarados equivalentes.**
   El nivel `critico` lo exige por escrito. Yo he verificado que las cinco
   justificaciones son **correctas** (§5.4); la aceptación es suya.
2. **El bloque 9 (T25–T32), contra el ERP de producción, sobre la obra de
   prueba 404.** Con dry-run antes de cada commit y autorización expresa por
   incidencia. **Su guion `progress/guion_bloque9_F-012.md` todavía no existe:
   escribirlo es lo primero del bloque.** Antes de abrirlo, dos cosas:
   - **Corregir D1** (`infra/16_grafico_sigrid.ps1:276`), que es el script que
     el propio bloque usa.
   - **Releer las cinco App Settings `SIGRID_DOCUMENT_*` de `sigrid-api`** (P0).
     Son **del dueño de la pasarela** y no se dan por buenas.
   - **Aviso que no puede ser una sorpresa**: `CIERRE_HABILITADO` es **una
     sola** para el gráfico y el cierre. Abrirla para probar el gráfico **abre
     también el cierre**.
3. **T34** (`bash harness/init.sh`): ejecutado y en verde, pero **lo marca el
   líder**, según el encargo.
4. **P1 de `design.md` §14**: confirmar con Posventa (Ana Bello / Alicia
   Echevarría) que `PV002` (`gratipide` 35, «POSTVENTA:Fotos Reparaciones») es
   la clase correcta para un parte firmado. Los datos apoyan que sí (3.197
   «PARTE FIRMADO» en esa clase), el nombre no lo dice. Cambiarlo es **una
   decisión de dos dueños**: una App Setting nuestra **más** la lista blanca de
   la pasarela.
5. **P2**: ¿`res` = `PARTE FIRMADO` a secas? Implementado así; cambiarlo es una
   constante del dominio.
6. **`azure-apps`, commit local `72b8fa3`, sin push.** Lo he leído entero:
   refresca solo `postventa_incidencias.md` (R70 cumplido: declara el endpoint
   nuevo y las cinco App Settings como precondición, con qué se rompe aquí y
   con qué código HTTP), **no toca `sigrid_api.md`** —que es del dueño de la
   pasarela— y mi barrido de hosts, GUID, credenciales y correos sobre su diff
   sale **a cero**. Decidir el push es del humano.
7. **Las dos correcciones de §6** (D1 y D2) y, si se quieren, las nueve
   sugerencias. **S9 va a `arnes-base`** por la regla de propagación.

---

## 9 · Automejora del protocolo de review

Dos cosas que esta review ha enseñado, **propuestas, no aplicadas**:

1. **`comando_de()` de `harness/mutacion.py` debería emitir `--base`** cuando no
   sea el valor por defecto (S9). Es la línea que un reviewer usa para
   reproducir la campaña, y hoy no reproduce nada cuando la rama nace de otra
   feature. Genérico: va a `arnes-base`.
2. **`CHECKPOINTS.md` C4 podría pedir que los tests nombren *todos* los
   requisitos que cubren**, no solo el primero. Aquí R4 y R54 aparecían como
   «sin test» en un recorrido mecánico de nombres y solo se salvan leyendo los
   docstrings (S4). Una trazabilidad que hay que verificar leyendo prosa deja de
   ser automática, que es justo lo que C4 quiere evitar. Genérico también.
