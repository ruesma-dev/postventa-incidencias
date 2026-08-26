<!-- progress/review3_F-010.md -->
# F-010 · Review de cierre (tercera ronda)

- **Rama:** `feature/F-010-despliegue` · HEAD `5154563`
- **Fecha:** 2026-08-25
- **Rondas anteriores:** `progress/review_F-010.md` (CHANGES_REQUESTED),
  `progress/review2_F-010.md` (CHANGES_REQUESTED)
- **Nada ejecutado contra Azure, SharePoint ni PostgreSQL.** Solo lectura del
  repositorio, `bash harness/init.sh` tal cual, tests locales y una campaña de
  mutación con salida fuera de `progress/`.

## Veredicto

> ## **CHANGES_REQUESTED**

**Y es un rechazo estrecho, como el anterior.** Todo lo que esta ronda traía a
revisar está **aprobado**: el defecto 14 es el mejor trabajo de la feature, los
defectos 13, 15 y 16 están donde tienen que estar, los resultados manuales
están anotados con evidencia real y atribuida, y **el barrido de identificadores
sale limpio sobre los 89 commits de la rama**, que era el riesgo más alto del
día. **Ni una línea de código nueva hace falta para cerrar.**

Lo que bloquea son **tres cosas**, ninguna descubierta hoy por el implementer y
dos de ellas reportadas por él por escrito como residuo:

1. **Un requisito EARS sin el test que su propia spec promete** (R14). Es el
   único incumplimiento de C4, y no es una recomendación mía: la tabla de
   trazabilidad de `requirements.md:259` dice «test de que el despliegue no lo
   pisa», y ese test **no existe**.
2. **Un requisito EARS que describe un mecanismo demostradamente roto** (R29),
   más la fila de `design.md` §6.4 que lo acompaña. Cerrar F-010 sellaría en
   `history.md` una spec que manda usar un comando que devuelve `400`.
3. **La corrección nº 1 de la ronda anterior, aplicada a medias**:
   `infra/cargar_secretos_postventa.ps1` sigue dictando por pantalla el
   criterio imposible que se acaba de rectificar en el documento y en la tarea.

**T14 bis NO está en esa lista.** Razonado en §7: no bloquea.

**Trabajo estimado**: un test de veinte líneas y tres retoques de Markdown, en
dos roles distintos. Detalle accionable en §9.

---

## 1 · Nivel de rigor y puertas exigibles

`harness/features.json` declara **`rigor: "estandar"`** para F-010. Según
`harness/rigor.json` y la tabla de `CHECKPOINTS.md`, eso exige:

| Puerta | Exigida | Resultado |
|---|---|---|
| Fase RED en los requisitos centrales | **Sí** | **[x]** — traza real pegada, §4 |
| Cobertura de las líneas cambiadas ≥ 80% | **Sí** | **[x]** — `[OK]` 98.5% (134/136) |
| Campaña de mutación con supervivientes analizados | **Sí** | **[x]** — verificada por mí, §5 |
| Cero supervivientes | **No** (solo `critico`) | 3, los tres equivalentes y analizados |
| Manuales con **resultado real** | **No** (solo `critico`) | ver §7 |
| Sección «Evidencias» con los cuatro números + workers | **Sí** | **[x]** |

**Este es el dato que decide lo de T14 bis** y conviene dejarlo escrito antes
de llegar allí: la exigencia de que las verificaciones `MANUAL (humano)` estén
listadas «con su comando exacto **y su resultado real**» pertenece al nivel
**`critico`**. F-010 es `estandar`. C4 solo pide que estén listadas con su
comando, pendientes de que el humano las ejecute.

---

## 2 · El defecto 14, mirado con lupa

Era el encargo principal y **está bien resuelto**. Lo he revisado línea a
línea, no por el informe.

### 2.1 La partición en dos errores es correcta

El acierto no es traducir `PersistenciaNoDisponible`: es haberse dado cuenta de
que **traducirlo en el borde habría producido una mentira**. Hay tres caminos
por los que ese error llega al borde y solo **uno** significa «el fichero está
subido». Los he verificado en el código, no en el informe:

| Camino | ¿Subido? | Qué sale |
|---|---|---|
| `construir_repositorio` no abre conexión (`archivar.py`, antes de tocar nada) | **No** | `PersistenciaNoDisponible` → 503 |
| `except ArchivoFallido` → falla también la traza de error (`paso_archivo.py:127`) | **No** | `PersistenciaNoDisponible` → 503 |
| `_dejar_constancia`, tras `_subir` (`paso_archivo.py:135`) | **Sí** | `ArchivoSinTraza` → 500 |

El renombrado ocurre **solo** en el tercero, y el bloque `except ArchivoFallido`
se deja intacto **a propósito y documentado**. Es la decisión correcta: quien
conoce el orden es el paso, y el borde no puede deducirlo. `raise ... from` no
se traga nada y el motivo viaja entero.

### 2.2 Los mensajes dicen la verdad en cada rama

Comprobado uno a uno contra el código que los emite:

- **500** — «el parte SÍ se ha subido a SharePoint (…) volver a archivarlo no
  arregla nada». Cierto: `_subir` completó antes de llegar ahí.
- **503 / `PersistenciaNoDisponible`** — «no se ha subido nada (…) se puede
  reintentar». Cierto en los dos caminos que lo producen.
- **503 / `ConfiguracionPgIncompleta`** — «este entorno no archiva». Cierto:
  la fábrica falla antes de tocar SharePoint.

**Y el caso «subido pero sin traza» es real, no hipotético**: pasó el
2026-08-25 en el segundo intento de T18, con el PDF ya en su carpeta.

### 2.3 El contrato queda declarado donde se lee

El enunciado «en los cuatro casos, sin haber subido nada» dejaba de describir
el endpoint entero. La rectificación está en el **docstring de
`function_app.archivar`** —que es donde mira quien lo vaya a cambiar— y en el de
`archivar_parte`. La tabla de alternativas descartadas (502, 503, 200 con
aviso) del informe es correcta: **500 es el único código que no promete nada
falso**, y además es el que el llamante ya recibía, así que nadie que lo trate
hoy tiene que cambiar.

### 2.4 Ningún test relajado, y un hueco que no queda

- El commit `24f50ad` **solo añade** un fichero de tests. Ningún test de F-006
  tocado. Verificado con `git show --stat`.
- Comprobación propia que el informe no hacía: **el borde captura exactamente
  las dos subclases de `ErrorDePersistencia` que este camino puede producir**.
  `DdlInseguro` y `DdlNoPermitidoAqui` viven en `ddl.py` y `arranque.py`, fuera
  del camino de `/api/archivar`. No hay hueco.
- `ArchivoSinTraza` hereda de `Exception` y no de `ErrorDePersistencia`, así que
  el orden de los `except` no la puede capturar antes por herencia. Correcto.

**Recomendación no exigida**: un `except ErrorDePersistencia` final como red de
seguridad devolvería el 500 mudo a un caso que hoy no existe pero que una
subclase futura podría reintroducir. No lo pido: sería código sin test.

---

## 3 · Defectos 13, 15 y 16

| # | Dónde tocaba | Veredicto |
|---|---|---|
| **13** | `infra/verificar_archivo_dev.ps1`, `verificar_despliegue.ps1`, `docs/DESPLIEGUE.md` §5 bis, enunciados de T14 y T18 | **Correcto.** El script reconoce *ese* `400` y sale con código propio; el segundo verificador se arregló aunque no lo pedía el enunciado, y hace bien: era el mismo defecto en el script que ejecuta T14. **Ninguna casilla `[x]` movida** |
| **15** | **NO se arregla aquí** | **Correcto, y es lo importante.** Es de F-019. Verificado en `harness/features.json`: la ficha de F-019 trae el `ForeignKeyViolation` como prueba, la fecha, y el aviso de comprobar el orden al implementarla. `BACKLOG.md` al día |
| **16** | `progress/current.md` | **Correcto.** El DSN sin contraseña es deliberado y queda escrito con el fichero y la línea que lo demuestran |

He comprobado el **§5 bis** del runbook: el fragmento de consola usa la ruta
relativa `/api/archivar`, PDF sintético y `0677 / RS26.08-0001`. **Sin una sola
URL.**

---

## 4 · Fase RED (C4 bis)

Exigida por el nivel `estandar`. **Cumplida, con salida real pegada**, no con
la frase «se siguió TDD»:

- **Defecto 14** — dos ejecuciones en rojo. La primera es un `ImportError` de
  colección (`ArchivoSinTraza` no existía); la segunda, con la clase declarada
  y **sin ninguna otra línea de producción**, es la que enseña el defecto:
  `6 failed, 1 passed`, con el `PersistenciaNoDisponible` escapándose por
  `paso_archivo.py:123`. Después, `7 passed`.
  **Detalle que vale**: el test que ya estaba verde en rojo es el **control**
  —el camino que no debía cambiar—, y el informe lo dice.
- **Defecto 13** — `4 failed` de contrato sobre los `.ps1` y `2 failed` sobre
  el runbook, con sus asserts.

**Hallazgo del implementer que merece constar**: la *fixture* `bloque` de
`test_f010_tarjeta_portal.py` cogía «el primer bloque `js` del documento», y con
el fragmento de consola delante habría pasado a afirmar sobre otra cosa sin
enterarse. Ahora busca el bloque que contiene `requiredGroupId`. Eso es cazar un
test que iba a volverse mudo.

---

## 5 · Mutación · verificación INDEPENDIENTE (C4 bis)

**El «Tiempo total» declarado es 43.6 s, por debajo de cinco minutos, así que
reejecuté la campaña entera**, como manda C4 bis.

### 5.1 Recálculo puro (alcance y nº de mutantes)

Con `harness.alcance` y `harness.mutacion.generar_mutantes`, sin ejecutar la
suite. **Coincide fichero a fichero con el informe:**

| Fichero | Líneas | Mutantes |
|---|---|---|
| `harness/mutacion.py` | 10 | 0 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 34 | 0 |
| `services/postventa-api/domain/models/errores.py` | 26 | 0 |
| `services/postventa-api/function_app.py` | 116 | **3** |
| `services/postventa-api/interface_adapters/api/archivar.py` | 11 | 0 |
| `services/postventa-front/dev_server.py` | 188 | 20 |
| **Total** | **385** | **23** |

**No es una campaña de cero mutantes**, así que no hace falta la prueba de
control por exclusión de alcance.

### 5.2 Muestreo de supervivientes

Los tres declarados existen como mutantes reales, **con el mismo operador y el
mismo texto**: `dev_server.py:169`, `:171` y `:175`, operador `entero`,
`log.info("=" * 60)` → `log.info("=" * 61)`. Confirmado.

### 5.3 Reejecución completa

```
python -m harness.mutacion --feature F-010 --salida <scratchpad>/mutacion_rev3_F-010.md
23 mutantes evaluados, 20 muertos, 3 supervivientes, 0 timeouts en 59.2 s
```

| Métrica | Informe | Mi reejecución |
|---|---|---|
| Mutantes | 23 | **23** |
| Muertos | 20 | **20** |
| Supervivientes | 3 | **3** |
| Timeouts | 0 | **0** |

**Idénticos.** Y lo que más importa para el defecto 14: **los tres mutantes de
los códigos de estado nuevos murieron en mi propia ejecución** —
`function_app.py:320` `503→504`, `:332` `503→504`, `:349` `500→501`—. Los
muertos están comprobados, no contados.

La salida fue al scratchpad, **nunca a `progress/`**, y `git status` queda
**limpio** después. La campaña no dejó worktrees nuevos.

### 5.4 Coste por mutante

> coste = «Tiempo total» × workers ÷ mutantes

- Informe: 43.6 × 16 ÷ 23 = **30.3 s/mutante**
- Mi reejecución: 59.2 × 16 ÷ 23 = **41.2 s/mutante**

La suite del servicio tarda **28.12 s**. Los dos valores quedan **por encima**,
que es lo sano: la suite se estaba ejecutando de verdad. Nada sospechoso.

### 5.5 Supervivientes

Los tres son la anchura de un separador decorativo en el banner de arranque de
`dev_server.py`, **declarados equivalentes** con análisis completo, **ninguno en
`PENDIENTE`**. He releído el análisis contra el código actual: `dev_server.py`
no se ha tocado en esta ronda y el razonamiento sigue valiendo. En nivel
`estandar` los supervivientes se documentan y el reviewer juzga: **los acepto**.

---

## 6 · Barrido de identificadores (el riesgo más alto del día)

**Ejecutado por mí sobre `git log -p dev..HEAD` — los 89 commits de la rama, no
el árbol**, porque el historial no suelta lo que entra.

| Patrón | Resultado |
|---|---|
| GUID `8-4-4-4-12` | **0** |
| `azurewebsites.net`, `azurestaticapps.net`, `sharepoint.com`, `vault.azure.net`, `postgres.database.azure.com`, `azurecr.io`, `blob.core.windows.net` | **1**, y es inerte: ver abajo |
| Cualquier `http(s)://` **en los commits de esta ronda** | **0** |
| IPv4 privadas (RFC 1918) | **0** |
| IPv4 cualquiera | **1**: `192.0.2.1`, TEST-NET-1 de la RFC 5737, reservado para documentación |
| `subscriptionId`, `tenantId`, `/subscriptions/` con valor | **0** — solo **nombres** de App Setting y el marcador `<TENANT_ID>`, intacto |
| `client_secret`, `AccountKey=`, `eyJ…`, `Bearer …`, `sk-…`, `AIza…` | **0** — solo **nombres** de secreto y de App Setting |
| `web_url`, `item_id`, `site_id`, `drive_id` con valor | **0** — solo nombres de clave y de App Setting |
| Hex ≥16 y base64 ≥28 en esta ronda | **0** (los aciertos son hashes de commit del propio informe) |
| DNI | **1**: `00000000T`, el inventado del test |
| Importes | **0** |
| Cookies de sesión (`StaticWebAppsAuthCookie`, `AppServiceAuthSession`) | **0** |

**El único acierto que merece explicación**: `func-postventa-dev.azurewebsites.net`
aparece **dos veces**, las dos dentro de `progress/review_F-010.md` —mi propio
informe de la primera ronda— y **en un texto que argumenta precisamente que no
se escriba un host real**. Además es la plantilla **sin sufijo**:
`infra/00_vars_postventa.ps1:63` compone el nombre como
`func-postventa-dev$PostventaSufijo`, así que no identifica el recurso
desplegado. **No es un hallazgo**, y lo dejo escrito para que la próxima ronda
no lo vuelva a levantar.

**Y lo que de verdad se jugaba hoy**: por el chat circularon URLs de SharePoint
y del front, un `web_url` y salidas de Application Insights con identificadores
de suscripción. **Nada de eso ha entrado.** Los commits de esta ronda tienen
**cero URLs**. Lo único con forma de identificador que sí se escribe —el nombre
`0677 - RS26.08 - 0001 PARTE FIRMADO.pdf` y la carpeta `Postventa/0677`— he
comprobado que **ya estaba en las specs de F-003 y F-006 desde antes**, como
dato inventado.

**Historial de binarios**: `git log --all --diff-filter=A` no trae **ni un**
`.pdf`, `.zip` ni ofimático, ni nada bajo `muestras/`.

---

## 7 · T14 bis: ¿bloquea el cierre?

**Mi respuesta: NO bloquea.** Razonado, porque el encargo pide el razonamiento
y no la etiqueta.

**Lo que hay.** La casilla está `[x]` desde una ronda anterior, puesta por el
humano; el «tope fijado: sí/no» y la «alerta configurada: sí/no» que su propia
verificación exige **no constan en ningún sitio**. El implementer **no la ha
marcado ni desmarcado**, y la ha declarado hueco abierto en tres sitios
—la nota de la tarea, la tabla de estado (`tasks.md:607`, que dice literalmente
«SIN RESULTADO ANOTADO») y `progress/current.md`—, con lo que está en juego
dicho en una línea.

**Por qué no bloquea, en orden de peso:**

1. **El arnés no lo exige en este nivel.** La tabla de `CHECKPOINTS.md` reserva
   «verificaciones `MANUAL (humano)` listadas con su comando exacto **y su
   resultado real**» al nivel **`critico`**. F-010 es **`estandar`**. C4 pide
   que estén listadas con su comando: lo están. Inventarme una exigencia de
   `critico` para una feature `estandar` sería cambiar el listón a mitad de
   partida, y el listón lo fija `harness/rigor.json`, no mi criterio.
2. **Ninguna acción de agente lo cierra.** El dato lo tiene el humano, en la
   consola de un proveedor externo. Rechazar por esto no produciría trabajo:
   produciría una ronda de espera.
3. **La deuda está declarada como es debido**: con dueño (el humano), fecha,
   consecuencia concreta y tres puntos de anclaje. No se pierde.
4. **El riesgo es de coste, no de datos ni de producción.** Los endpoints
   anónimos son una decisión **ya aprobada** en dos revisiones (R32, T8), con
   defensa en capas documentada; la capa 4 es la que falta.

**Lo que sí digo, y va para la PARADA 2 del líder:** `/api/extraer` y
`/api/firma` **son anónimos y ya son alcanzables**. Mientras el tope no esté
puesto, un desconocido puede consumir cuota de IA y la única señal será la
factura. **Que no bloquee el cierre no significa que pueda esperar**: es lo
único vivo de F-010 y se resuelve en cinco minutos de consola. Que el líder se
lo lleve al humano con esa frase.

---

## 8 · CHECKPOINTS.md, recorrido completo

### C1 — El arnés está completo y en verde

- **[x]** `bash harness/init.sh` termina en **exit code 0**. Ejecutado tal cual
  al abrir y al cerrar esta review. `PUERTA COBERTURA` en `[OK]` 98.5%.
- **[x]** Existen los siete documentos exigidos.

### C2 — El estado es coherente

- **[x]** Una sola feature `in_progress`: F-010.
- **[x]** Rama `feature/F-010-despliegue`, nunca `main`.
- **[x]** `progress/current.md` describe la sesión activa. Lleva bloques de
  estado apilados, pero el más reciente está al frente y fechado, y el resto es
  memoria viva declarada como tal.
- **[x]** Las siete `done` (F-001 a F-007) tienen resumen en `history.md`.

### C3 — El código respeta arquitectura y convenciones

- **[x]** **Hexagonal respetada**: `grep` sobre `domain/` y `application/` no
  encuentra **ni un** import de `infrastructure`. `ArchivoSinTraza` está en
  `domain/models/errores.py`, que es su sitio; el mapeo a HTTP, en el borde.
- **[x]** Primera línea con la ruta relativa en los **cinco** ficheros tocados.
- **[x]** Sin `print()` de debug, sin TODOs, sin secretos hardcodeados. `ruff`
  sobre los ficheros tocados: **`All checks passed!`**
- **[x]** La unidad de trabajo sigue siendo el **parte** (`hash_parte`).
- **[x]** **Nada se archiva sin validar**: `_exigir_apto` sigue siendo la
  primera puerta del paso, antes de nombrar y antes de tocar el puerto.
- **[x]** Nada contra Sigrid en esta feature. Ningún estado hardcodeado.
- **[x]** Lo manuscrito y la firma: no tocado.
- **[x]** **Reprocesar no duplica**: es justo lo que T18 demostró contra la
  biblioteca real —un solo elemento, ningún `(1)`—.
- **[x]** **Ningún PDF ni dato personal en git**, comprobado con
  `git log --all --diff-filter=A` y no solo con el árbol (§6).

### C3 bis — Documentos que entran de fuera

**N/A justificado**: esta feature **no añade ni modifica ningún fichero bajo
`docs/referencia/`**. Comprobado en el diff `dev...HEAD`. El barrido de datos
sensibles lo he ejecutado igualmente sobre toda la rama y consta en §6 con sus
patrones.

### C4 — La verificación es real

- **[ ]** **Cada requisito EARS tiene ≥ 1 test trazable.** **R14 no lo tiene.**
  Ver §9.1: es el único punto vacío de este bloque.
- **[x]** Los unit tests no tocan red ni BBDD. Los del defecto 14 usan los
  dobles de F-006 (`utiles_sharepoint.py`); **SharePoint y PostgreSQL no
  aparecen**. `1092 passed, 13 skipped` en `api`, `17 passed` en el arnés.
- **[x]** Las verificaciones `MANUAL (humano)` están listadas con su comando
  exacto. **Diez de once traen además su resultado real**; T14 bis está listada
  y declarada sin resultado (§7).

### C4 bis — El rigor declarado se cumple

- **[x]** Declara `rigor: "estandar"`, valor válido.
- **[x]** **Fase RED** con salida real pegada (§4).
- **[x]** **Cobertura** en `[OK]`, 98.5% de 136 líneas, umbral 80%.
- **[x]** **Mutación** con totales **verificados de forma independiente** (§5.1,
  §5.2).
- **[x]** **Los muertos están comprobados**: campaña **reejecutada** por mí
  (43.6 s < 5 min), totales idénticos, salida fuera de `progress/`, árbol limpio
  después (§5.3).
- **[x]** **La campaña tardó lo que tenía que tardar**: 30.3 y 41.2 s/mutante
  contra una suite de 28.12 s (§5.4).
- **[x]** Los tres supervivientes con análisis **completado**, ninguno en
  `PENDIENTE`. Nivel `estandar`: los acepto como equivalentes.
- **[x]** Sección **«Evidencias»** con los cuatro números **y los 16 workers**.
  Los dos informes de la ronda la traen.
- **[x]** Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A justificado**: `harness/rutas_sensibles.json` **no existe** en este
repositorio, que es el caso mayoritario que el propio bloque contempla. Su
declaración completa es F-015.

### C5 — La sesión se cerró bien

- **[x]** **`tasks.md` con TODAS las tareas `[x]`**: 22 marcadas, **0 vacías**.
  Era la condición que faltaba en las dos rondas anteriores y ahora se cumple.
  La casilla ajena **T18 de `specs/F-006-sharepoint/tasks.md`** está marcada
  citando la autorización literal («autorizo T18 ante `CHECKPOINTS.md` C5»), con
  fecha, con el resultado real contra los tres puntos esperados y sin borrar los
  intentos fallidos. **Es exactamente lo que C5 exigía para tocar una feature
  ajena ya cerrada.**
- **[x]** Un commit `F-010 Tn: ...` o `F-010 defecto N: ...` por unidad de
  trabajo. 89 commits en la rama, todos con prefijo.
- **[x]** `git status` **limpio**, también después de mi campaña de mutación.
  Los tres worktrees de `.claude/worktrees/` están ignorados por `.gitignore:39`
  y no son artefactos de esta feature (uno cuelga de `feature/F-008-modelo-sigrid`).
  **Observación operativa, no bloqueo**: conviene retirarlos, como ya se hizo
  con los dieciséis de F-005.
- **[x]** `features.json` refleja el estado real: F-010 sigue `in_progress`. El
  implementer **no se ha marcado `done` a sí mismo**, que es lo correcto.

---

## 9 · CAMBIOS REQUERIDOS

Tres, numerados, con fichero y línea. **Ninguno toca los arreglos de los
defectos 13, 14, 15 y 16: esos quedan aprobados tal cual están.**

### 9.1 · R14 no tiene el test que su propia spec promete

**Es el único punto vacío de C4, y es un hallazgo de esta ronda.**

`specs/F-010-despliegue/requirements.md:259` promete, en la tabla de
trazabilidad de R14: «Ya lo fija `staticwebapp.config.json` (F-007); **test de
que el despliegue no lo pisa**». **Ese test no existe.** Verificado por mí:
ningún fichero de `services/postventa-api/tests/`,
`services/postventa-front/tests/` ni `tests/` lee `routes`, `allowedRoles` ni
`responseOverrides` de ese JSON. `test_f007_estaticos.py:213` solo mira el
marcador `<TENANT_ID>` y la ausencia de GUID.

**Consecuencia hoy**: se puede borrar la regla `"/*"` con
`allowedRoles: ["authenticated"]`, o el `responseOverrides.401`, o mover
`/.auth/login/aad` de sitio, y **la suite sigue verde**. Es el fichero que
costó el defecto 11 (`AADSTS50196`, una tarde), y el que sostiene el tercer
criterio de aceptación de la feature: «el acceso queda restringido al grupo de
Posventa».

**Qué hacer** — un test de contrato en
`services/postventa-front/tests/test_f007_estaticos.py` (o uno nuevo
`test_f010_config_swa.py`), que fije al menos:

1. `/.auth/login/aad` es la **primera** ruta y admite `anonymous`;
2. existe la regla que exige `authenticated` para `/*`;
3. existe el `responseOverrides` del `401`;
4. el fichero no lleva claves fuera del esquema.

**Nota**: esto es lo que la ronda anterior puso en §9.1 como «recomendado y no
exigido». Lo subo a exigido porque entonces no sabía que **la tabla de
trazabilidad lo promete**. Con la promesa delante, ya no es una preferencia
mía: es C4.

### 9.2 · R29 y `design.md` §6.4 dicen algo demostradamente falso

**Reportado dos veces por el implementer como residuo, y con razón: no era suyo.
Es del `spec-author`, y hay que lanzarlo.**

- `specs/F-010-despliegue/requirements.md:224-228` — **R29** dice que el sistema
  «debe permitir ejecutar **T18 de F-006** con
  `infra/verificar_archivo_dev.ps1 -BaseUrl <url del despliegue>`». **Ese
  mecanismo no funciona** desde que el backend es enlazado de la Static Web App:
  devuelve `400 Login not supported for provider azureStaticWebApps`. Lo
  demostró T18 el 2026-08-25, y lo dice el §5 bis del propio runbook.
- `specs/F-010-despliegue/design.md:252` — la fila de la tabla de ficheros que
  **NO se tocan** incluye `infra/verificar_archivo_dev.ps1` con la frase «**Se
  ejecuta** en T18, **no se modifica**». **Se modificó**, en el commit `7ff86d7`,
  y con motivo.

**Por qué bloquea y no lo dejo pasar como residuo declarado**: R29 es un
**requisito EARS de la feature que se está cerrando**, y describe un mecanismo
roto. Marcar F-010 `done` sella en `history.md` una spec que manda a quien
repita T18 hacia un comando que devuelve `400` — que es **literalmente el
defecto 13, otra vez**. Es el mismo criterio con que se rechazó la ronda 2: los
documentos que existen para que un defecto no se repita tienen que recogerlo.
Reportar un defecto no lo arregla.

**Qué hacer**: reescribir R29 contra la vía real (la consola del front, mismo
origen, `docs/DESPLIEGUE.md` §5 bis) y corregir la fila de `design.md` §6.4.
**Son cuatro líneas de Markdown y es trabajo del `spec-author`**, no del
implementer, que hizo bien en no invadir `requirements`/`design`.

### 9.3 · `cargar_secretos_postventa.ps1` sigue dictando el criterio imposible

La corrección nº 1 de la ronda anterior se aplicó en el documento y en la tarea,
pero **no en el script que el humano ejecuta y lee**:

- `infra/cargar_secretos_postventa.ps1:269` —
  `Write-Host "Anota en progress/ solo esto: 'once secretos cargados: si/no'."`
- Y además `:4`, `:30` y `:44`, que hablan de «los **once** secretos» en la
  ayuda del propio script.

La línea `:269` es **operativa**: le dice al humano que anote exactamente el
criterio que `tasks.md` T13 acaba de rectificar por imposible y que
`docs/DESPLIEGUE.md` §2 explica en detalle. Quien ejecute el script hará caso al
script, no al documento.

**Qué hacer**: «nueve secretos del backend» en los cuatro sitios, con la
coletilla de que `swa-client-id` y `swa-client-secret` los crea
`desplegar_front.ps1`. Es texto, no lógica. **Requiere permiso del humano para
tocar `infra/`**, que es exactamente por lo que el implementer lo dejó: el
encargo de su última ronda se lo prohibía expresamente.

---

## 10 · Lo que NO es un cambio requerido

Para que la próxima ronda no lo vuelva a levantar y para que el humano vea que
el rechazo es de tres puntos y no de trece:

1. **T14 bis.** No bloquea (§7). Va a la PARADA 2, no a esta lista.
2. **El defecto 15 sin arreglar.** **Es lo correcto.** Es de F-019 y está
   anotado en su ficha con la prueba, la fecha y el aviso del orden.
3. **`func-postventa-dev.azurewebsites.net`** en `review_F-010.md`. Es la
   plantilla sin sufijo, dentro de un texto que argumenta lo contrario. Inerte.
4. **Los tres supervivientes de mutación.** Equivalentes, analizados, y el nivel
   `estandar` no exige cero.
5. **Los tres worktrees de `.claude/worktrees/`.** Ignorados y ajenos a esta
   feature. Conviene retirarlos; no es un checkbox.
6. **`0677 - RS26.08 - 0001 PARTE FIRMADO.pdf`.** Sintético y ya escrito en las
   specs desde F-003/F-006.

### 10 bis · Dos observaciones que no bloquean pero conviene leer

- **El bloque de T18 en `specs/F-006-sharepoint/tasks.md` dice «Cumplido» a los
  puntos 1 y 2 sin decir que el `200` exigió sembrar el parte a mano** (con
  `t18_sembrar_parte.py`, fuera del repositorio, que además borra la traza
  después). En `specs/F-010-despliegue/tasks.md` sí se dice, y el bloque de
  F-006 enlaza allí; pero quien lea solo F-006 puede concluir que el archivado
  funciona de extremo a extremo, cuando **tal y como está desplegado no puede
  completar hasta F-019**. Una frase lo arregla. No lo exijo porque el criterio
  de aceptación de F-006 —un solo elemento, ningún `(1)`— **sí se verificó
  íntegro y no depende de la siembra**.
- **No consta qué pasó con el PDF sintético subido a la biblioteca real.** La
  traza de BD se borró (lo hace el script); el fichero, por lo que está escrito,
  se quedó. Queda un elemento sintético en la biblioteca y una asimetría
  fichero-sin-traza. Vale la pena decidir si se retira y dejarlo escrito.

---

## 11 · Trazabilidad requisito → test

Recorrida entera. **Solo los puntos que importan**; la tabla completa de las dos
rondas anteriores sigue vigente y no la repito.

| R | Enunciado corto | Test |
|---|---|---|
| R14 | Sin sesión, la SWA redirige al login | **SIN TEST** — §9.1. Manual T16 ejecutada |
| R26 | `INTEGRACION.md` §8: qué se expone y qué no | `test_f010_integracion_expuesto.py:53,63,78,87,93` |
| R29 | T18 ejecutable con `-BaseUrl` | **MANUAL T18** — y el requisito es falso: §9.2 |
| R30 | F-006 no completa sin T18 anotada; autorización C5 | Sin test **por naturaleza** (gobierno). Resuelto por vía documental: T18 ejecutada y autorizada |
| R31 | Si aparece `(1)`, parar y hablar con el humano | `test_f006_paso_archivo.py:219,272`, `test_f006_archivar_http.py:178`. Lo manual es solo mirar el listado real |
| R32 | El anonimato es deliberado y explicado | `test_f010_endpoints_protegidos.py:66,87,102,139` |
| R33 | `ARCHIVO_HABILITADO` apagado → `503` | `test_f010_scripts_infra.py:425,448`, `test_f010_endpoints_protegidos.py:128` |
| R34 | Abrir/cerrar la ventana con una App Setting | `test_f010_tarjeta_portal.py:155` |
| R35 | Tope de gasto con alerta | **MANUAL T14 bis** — §7 |

**Del defecto 14**, tests nuevos y qué atan:

| Qué | Test |
|---|---|
| Subido y sin traza → **500 con cuerpo** | `test_f010_borde_persistencia.py:78` |
| El mensaje dice que el fichero **está** subido | `:95` |
| El mensaje no lleva DNI, bytes ni `password` (R26) | `:112` |
| Subida fallida → **503** «no se ha subido nada» | `:135` |
| Falta configuración de PG → **503** nombrando la variable | `:161` |
| El **paso** levanta `ArchivoSinTraza` solo si ya subió | `:186` |
| **Control**: si la subida falló, sigue siendo `PersistenciaNoDisponible` | `:201` |

Cobertura menor y no exigida: R1 solo comprueba el bloque de ayuda sobre
`00_vars_postventa.ps1`; los otros cuatro `.ps1` lo tienen pero ningún test lo
obliga. Cierre trivial parametrizando sobre `scripts_entregados()`
(`test_f010_scripts_infra.py:365`). **No lo pido.**

---

## 12 · Lo que hay que decirle al humano

Esta feature está **a un test y tres párrafos** de cerrarse, y el trabajo se
reparte en tres sitios:

| # | Qué | Rol | Permiso que hace falta |
|---|---|---|---|
| 9.1 | El test de contrato de `staticwebapp.config.json` | `implementer` | ninguno |
| 9.2 | R29 y la fila de `design.md` §6.4 | **`spec-author`** | ninguno |
| 9.3 | «nueve secretos» en el script | `implementer` | **tocar `infra/`** |
| §7 | El resultado de T14 bis | **el humano** | — |

**El 9.3 y el de T14 bis los tiene que desatascar el humano**; los otros dos son
encargo directo del líder. Y el `spec-author` **no se ha lanzado en toda la
feature**: los residuos de `requirements`/`design` llevan dos rondas reportados
porque no había a quién dárselos.

---

## 13 · Propuestas de mejora del protocolo (NO aplicadas)

Para que las apruebe o las descarte el humano. Si se aceptan y son genéricas,
viajan a `arnes-base` en el mismo trabajo.

**P5 · Un checkpoint para los residuos declarados.** Esta feature acumula tres
rondas de «residuo reportado y NO corregido», y el mecanismo funciona —no se
pierde nada— pero **no tiene puerta de salida**: un residuo puede sobrevivir
indefinidamente mientras cada informe lo repita. Propongo añadir a `C5`:

> - [ ] Todo residuo reportado y no corregido en `progress/` tiene **rol
>       asignado** y consta si su cierre es condición del `done` o deuda
>       aceptada. Un residuo repetido en dos informes consecutivos sin rol
>       asignado es CHANGES_REQUESTED.

Es genérica y barata. Habría cazado el R29 una ronda antes.

**P6 · La tabla de trazabilidad de `requirements.md` es una promesa, y hay que
tratarla como tal.** El hueco de R14 no lo cazaron dos revisiones porque nadie
contrastó la **columna «cómo se verifica»** de esa tabla contra los tests que
existen: se revisó requisito → test, no promesa → test. Propongo añadir a `C4`:

> - [ ] Cuando la spec declare en su tabla de trazabilidad que un requisito se
>       cubre **con test**, ese test existe. Un «test de que…» prometido y no
>       escrito es un checkbox vacío, aunque el requisito tenga además una
>       verificación MANUAL.

También genérica, y es la que ha destapado el único fallo de C4 de esta ronda.

**P7 · Menor.** `CHECKPOINTS.md` C4 exige el «resultado real» de las manuales
solo en nivel `critico`, pero la redacción de C4 (tercer punto) dice
«pendientes de que el humano las ejecute», que se lee raro cuando **ya se han
ejecutado**. Es la misma observación que P1 del reviewer de F-004, que sigue en
la cola de decisiones del humano sin resolver. Vale la pena resolverla: ha
vuelto a aparecer.

---

## 14 · Resumen

| Bloque | Estado |
|---|---|
| C1 · Arnés en verde | **[x]** |
| C2 · Estado coherente | **[x]** |
| C3 · Arquitectura y convenciones | **[x]** |
| C3 bis · Documentos de fuera | **N/A justificado** (no toca `docs/referencia/`) |
| C4 · Verificación real | **[ ]** — R14 sin el test que la spec promete (§9.1) |
| C4 bis · Rigor `estandar` | **[x]** — mutación reejecutada y verificada |
| C4 ter · Rutas sensibles | **N/A justificado** (no existe la declaración) |
| C5 · Sesión cerrada | **[x]** — 22/22 casillas, incluida la ajena de F-006 |

**Veredicto: CHANGES_REQUESTED**, por §9.1, §9.2 y §9.3.

**Y que quede dicho, porque tres rondas cansan**: el trabajo técnico de esta
feature es de calidad alta y el de esta ronda, el mejor de las tres. El defecto
14 está resuelto por donde había que resolverlo —en el paso, no en el borde—,
con la fase RED delante, el contrato declarado y los mutantes de los tres
códigos nuevos muertos en mi propia ejecución. El rastro documental de las
manuales es honesto hasta el punto de escribir los intentos que fallaron y de
dejar T14 bis marcado como hueco en vez de rellenarlo. Y el barrido de
identificadores, con el entorno real delante todo el día, sale **limpio**.

Lo que falta son cuatro líneas de Markdown que mienten y un test de veinte
líneas que la spec prometió y nadie escribió.
