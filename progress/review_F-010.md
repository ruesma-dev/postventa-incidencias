<!-- progress/review_F-010.md -->
# Review F-010 · Despliegue en Azure y tarjeta en el portal

- **Rama:** `feature/F-010-despliegue`
- **Nivel de rigor:** `estandar` (declarado en `harness/features.json`).
  Puertas exigibles: fase RED en los requisitos centrales, PUERTA COBERTURA
  en `[OK]`, campaña de mutación con análisis de todos los supervivientes
  (sin exigir cero supervivientes, eso es `critico`), sección «Evidencias».
- **Veredicto:** **APROBADO** (2.ª ronda, 2026-08-20). Los cinco defectos de
  §10 bis están corregidos **y sus tests también**, que era la condición dura.
  Verificación completa en **§13**.
  _(1.ª ronda: CHANGES_REQUESTED por esos cinco defectos — histórico en §10 bis
  y §11.)_
- **Encargo prioritario (bytecode envenenado):** respondido en §1. **F-005 y
  F-006 NO están invalidadas**; no hay que reejecutar ninguna campaña cerrada.

---

## 0 · Portero

`bash harness/init.sh` — **VERDE**, ejecutado por el reviewer:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido / BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea)
16 passed in 0.36s  → [OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde (caché)
[OK] servicio front (services/postventa-front): pytest en verde (caché)
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116,
     umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-010-despliegue
ENTORNO LISTO.
```

_(Las dos suites se relanzan más abajo sin caché y con `__pycache__` limpio.)_

---

## 1 · EL HALLAZGO DEL BYTECODE ENVENENADO · ¿invalida campañas anteriores?

Es el encargo prioritario del líder. Lo respondo con medidas, no con
intuición, y la respuesta corta va primero:

> **F-005 y F-006 NO están invalidadas.** El fallo es real, está confirmado, y
> es grave para el arnés — pero **su ventana de disparo no se puede abrir en el
> servicio `api`**, que es donde viven F-005 y F-006. Solo se abre en el
> servicio `front`. **No hace falta reejecutar ninguna campaña cerrada.**
>
> Con un matiz que el humano debe conocer: la inmunidad de `api` es
> **circunstancial, no estructural**. La sostiene un número —lo que tarda la
> suite—, no un diseño. El día que `api` se parta en servicios pequeños con
> suites de menos de un segundo, la ventana se abre ahí también.

### 1.1 · El mecanismo, leído en el código del arnés

`harness/mutacion.py` (`_escribir`, líneas 275-277, y `EjecutorPytest.ejecutar`,
líneas 302-316) escribe el mutante **sobre el fichero real**, lanza la suite con
`subprocess.run(...)` y restaura el original en un `finally`. Dos ausencias
concretas:

- El `subprocess.run` **no pasa `env=`**, así que no fija
  `PYTHONDONTWRITEBYTECODE=1`: el proceso hijo escribe `.pyc` del **mutante**.
- Los argumentos por defecto son
  `["-x", "-q", "--tb=no", "-p", "no:cacheprovider"]`. `no:cacheprovider`
  desactiva **la caché propia de pytest** (`.pytest_cache`), **no** el
  `__pycache__` de CPython. Es una confusión fácil, y aquí ha costado cara.

La condición para que el `.pyc` envenenado se reutilice es precisa: CPython
valida un `.pyc` comparando **el mtime del fuente truncado a segundos enteros**
y **su tamaño en bytes**. Muchos operadores del mutador conservan el tamaño
exacto (`==`→`!=`, `60`→`61`). Por tanto:

> **El `.pyc` de un mutante se da por bueno para el fuente restaurado si y solo
> si escribir el mutante y restaurar el original caen en el MISMO segundo
> entero.** Es decir: **si el ciclo completo por mutante dura menos de un
> segundo.**

Ese es el interruptor. Todo lo demás se sigue de él.

### 1.2 · Medidas propias (reviewer, 2026-08-20)

| Medida | Valor | Cómo se obtuvo |
|---|---|---|
| Suite `front` completa | **1,39 s** (1,8 s de reloj) | `pytest -q -p no:cacheprovider` con `__pycache__` borrada |
| Suite `api` completa | **18,49 s** (21,1 s de reloj) | ídem, con el intérprete del venv de `api` |
| Suite `api`, **solo recolección** | **2,37 s** (4,34 s de reloj) | `pytest --collect-only -q` — es el **suelo absoluto** de cualquier evaluación de mutante en `api`, incluso con `-x` cortando en el primer fallo |
| Ciclo por mutante, `front` (campaña F-010 relanzada por mí) | **0,86 s** (17,2 s / 20) | `--feature F-010 --workers 1` |
| Ciclo por mutante, `api` (muestra de 8 de F-005, relanzada por mí) | **11,2 s** (89,8 s / 8) | `--feature F-005 --workers 1 --max-mutantes 8 --semilla 7` |

**La conclusión sale de comparar la tercera fila con el umbral de 1 segundo.**
Ninguna evaluación de un mutante de `api` puede durar menos de ~4,3 s de reloj,
porque antes de ejecutar el primer test hay que recolectar 1.074. El ciclo
`escribir mutante → suite → restaurar` **nunca** cabe en un segundo entero en
`api`. En `front`, con 0,86 s de ciclo, cabe casi siempre.

### 1.3 · Cómo se ejecutaron de verdad las campañas de F-005 y F-006

No hay que suponerlo: **quedan las pruebas en disco**. `git worktree list`
muestra **16 worktrees huérfanos** en el temp del sistema, de una campaña de
F-005 (`mutacion_F-005_zllkg8wf/wk_0` … `wk_15`), todos en el commit `48fb104`,
que es de la rama de F-005.

Es decir: **F-005 se ejecutó con la campaña paralela, 16 workers, cada uno en
su propio `git worktree`**. Eso añade una segunda barrera sobre la anterior:
cada worker tiene su **propio** `__pycache__`, en su propio directorio, creado
desde cero. Y los tiempos lo confirman:

| Campaña | Mutantes | Tiempo total | Ciclo real por mutante | ¿Cabe en 1 s? |
|---|---|---|---|---|
| **F-005** | 106 | 330,4 s | ~50 s por worker (330 × 16 / 106) | **No, ni de lejos** |
| **F-006** | 64 | 905,7 s | ≥ 14,2 s (905,7 / 64) | **No** |
| **F-010** | 20 | 11,1 s | **0,55 s** | **Sí — y por eso pasó aquí** |

F-010 es **la primera campaña de este repositorio con un ciclo por debajo del
segundo**, porque es la primera que muta un fichero del servicio `front`, cuya
suite tarda 1,4 s. Las de `api` están dos órdenes de magnitud por encima del
umbral.

### 1.4 · Y además, F-006 no cerró con cero supervivientes

Corrijo un dato del encargo, porque cambia el análisis: **`progress/mutacion_F-006.md`
declara 64 mutantes, 59 muertos y 5 SUPERVIVIENTES**, cada uno con su análisis
escrito (el primero, `GRAPH_TIMEOUT_S` `default=60` → `61`, justificado como
equivalente). F-006 no se cerró con un cero, sino con cinco supervivientes
justificados y aceptados. Solo **F-005** declara `Supervivientes: 0` (con 3
timeouts, también analizados).

Así que la pregunta «¿pudo ser falso aquel cero?» se reduce a **F-005**, y para
F-005 la respuesta es no, por §1.2 y §1.3.

### 1.5 · Por qué el falso cero es el síntoma peligroso

Merece dejarlo escrito porque el implementer lo describió bien y conviene que
no se pierda. Con la caché envenenada, el `.pyc` cargado contiene el **mutante
anterior**. Si aquel mutante rompía la recolección de pytest —el caso real fue
`if __name__ != "__main__":` en `dev_server.py`, que ejecuta `main()` al
importar y mata la sesión con `SystemExit: 2`—, entonces **todos** los mutantes
siguientes ven la suite en rojo y se anotan como **muertos**. Resultado:
**cero supervivientes falso**. El error va en la dirección que tranquiliza, que
es la peor.

Confirmo el número del implementer de forma independiente: mi relanzamiento de
la campaña de F-010 con `__pycache__` limpia dio **20 mutantes, 17 muertos, 3
supervivientes, 0 timeouts en 17,2 s**, y los tres supervivientes son
exactamente los tres del informe (`dev_server.py:169`, `:171`, `:175`,
`"=" * 60` → `"=" * 61`). El informe **no está escrito a mano**.

### 1.6 · Lo que sí recomiendo al humano (no bloquea F-010)

1. **No reejecutar F-005 ni F-006.** La evidencia de §1.2-§1.3 es suficiente y
   el coste (≈ 20 min de máquina) no compra información.
2. **Arreglar el arnés en `arnes-base`**, como propone el implementer. El
   arreglo mínimo y suficiente es una línea: pasar
   `env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}` al `subprocess.run` de
   `EjecutorPytest.ejecutar`. Borrar el `__pycache__` tras restaurar también
   vale, pero es más frágil (hay que acertar con todos los directorios).
3. **Limpiar los 16 worktrees huérfanos** de `mutacion_F-005_zllkg8wf`, que
   siguen registrados en `git worktree list`. No los toco yo: no es mi papel y
   no afecta al veredicto.
4. **Anotar en `CHECKPOINTS.md` la regla que este episodio enseña**: un informe
   de mutación cuyo **«Tiempo total» dividido entre los mutantes dé menos de un
   segundo** es sospechoso por construcción y hay que relanzarlo con la caché
   limpia. Es un criterio objetivo, barato y comprobable de un vistazo, y
   encaja con la regla de los 5 minutos que ya tiene el protocolo del reviewer.

---

## 2 · Barrido propio de identificadores y secretos (punto 4 del encargo)

Barrido independiente sobre **toda la rama**, ficheros versionados
(`git ls-files`, 280 ficheros) e informes de `progress/` incluidos: GUID, FQDN
de Azure (`azurewebsites.net`, `azurestaticapps.net`, `vault.azure.net`,
`blob.core.windows.net`, `sharepoint.com`, `azurecr.io`), IPs, cadenas de
conexión, `AccountKey=`, `client_secret`, tokens `eyJ…`, claves `sk-` y `AIza`.

**Resultado: ni un hallazgo real.** En una feature de despliegue, que es donde
más fácil era colarse.

Lo que sí aparece, y es legítimo:

- `<TENANT_ID>` intacto en `staticwebapp.config.json:7`, sustituido sobre una
  **copia de trabajo** por `infra/desplegar_front.ps1:101` y vigilado por
  `test_f010_scripts_infra.py:667`. R12 y R13 se cumplen.
- `infra/desplegar_front.ps1:246` **obtiene** el nombre de host en ejecución
  (`az staticwebapp show --query defaultHostname`) en vez de escribirlo. Es
  justo lo que había que hacer.
- GUID nulo por construcción (`00000000-…`) y controles negativos declarados de
  F-005/F-006; IPs `192.0.2.1` (RFC 5737) y RFC 1918, todas como control
  negativo del redactor de logs.
- `infra/00_vars_postventa.ps1` lista **nombres** de secreto de Key Vault
  (`pg-password`, `graph-client-secret`…), nunca valores.

**Un punto borderline, que reporto sin considerarlo hallazgo**:
`specs/F-010-despliegue/design.md:342` y `:525` nombran `ohana.ruesma.es` y la
zona `ruesma.es` al justificar D5 (no usar dominio propio). Es DNS público y el
contexto es una decisión de diseño, no un dato de conexión. Queda a criterio
del humano.

### 2 bis · Huecos del barrido automático (observación, no bloqueo)

El test `test_f006_repo_sin_identificadores.py` **sí** cubre `infra/` y
`progress/` — nació del H1 de F-006 y lo afirma explícitamente. Sus huecos:

1. **Repo-wide solo barre GUID.** Los patrones de FQDN, IP y credencial
   (`PATRON_HOST`, `PATRON_IP`, `PATRON_CREDENCIAL`) viven en
   `test_f010_scripts_infra.py` y se aplican **solo a los cinco scripts de
   F-010**. Consecuencia concreta: un `func-postventa-dev.azurewebsites.net`
   real escrito en `docs/DESPLIEGUE.md`, en `progress/impl_F-010.md` o en el
   `design.md` **pasaría todos los tests**. Es la misma clase de fallo que H1
   —el valor se escribe en el informe, no en el código— y hoy solo lo cubre un
   barrido manual como el que he hecho.
2. **La lista de extensiones no incluye `.js`, `.html` ni `.css`**: los siete
   módulos de `services/postventa-front/js/` (incluido `config.js`) quedan
   fuera del barrido de GUID. Hoy están limpios; nadie los vigila. Es el sitio
   exacto donde caería un client ID el día que el front haga login por MSAL.
3. **Un GUID sin guiones** (formato `N`, 32 hex seguidos) no lo caza
   `PATRON_GUID`.

Nada de esto es un incumplimiento de F-010: R8 y R24 se cumplen. Lo dejo como
**propuesta de mejora** para una feature futura de arnés (§9).

---

## 3 · D3 · el cierre de la API (punto 1 del encargo)

**Verificado. La decisión está bien implementada, bien explicada y bien
atada.**

- `services/postventa-api/function_app.py` lleva la nota completa en la
  cabecera del módulo: que el montaje es **backend enlazado** de una Static Web
  App; que el proxy **autentica contra Entra** y reenvía
  **`x-ms-client-principal`**; que **no** añade clave de función ni *bearer*;
  que por eso `auth_level=FUNCTION` devolvería `401` **a través del front**; y
  —la trampa fina— que `x-ms-client-principal` **va en base64 sin firma y
  cualquiera puede fabricarla**, así que no sirve como control de acceso.
  Termina diciendo dónde sí está el control: las cuatro capas.
- `test_f010_endpoints_protegidos.py` no es un test de fachada. Lo que hace
  bien, y por lo que lo doy por suficiente:
  1. **Ata las dos mitades en un solo test**
     (`test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada`): cambiar el
     `auth_level` con la nota intacta falla; borrar la nota con el `auth_level`
     intacto falla; hacer las dos a la vez falla. Lo único que pasa es un
     cambio consciente que reescriba el porqué. **Eso es exactamente lo que
     R32 pide.**
  2. **Trae un control negativo**
     (`test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay`): comprueba que el
     patrón encuentra los **seis** endpoints y que sabe reconocer un `FUNCTION`
     escrito a mano. Sin él, un decorador reescrito de otra forma dejaría el
     diccionario vacío y **los demás tests pasarían sin comprobar nada**. Es la
     clase de defensa que suele faltar en los tests que leen código como texto,
     y aquí está.
  3. Lee `function_app.py` **como texto**, no importando el módulo: fija lo que
     dice el decorador en el fichero, no lo que quede en memoria tras el
     runtime de Functions. Correcto para este propósito.
- La **fase RED** de esta pieza está demostrada con traza real en
  `progress/impl_F-010.md`: se cambió un `auth_level` a `FUNCTION`, el test
  falló con `Extra items in the left set: 'FUNCTION'`, y se revirtió.

**¿Impediría de verdad que alguien lo «arregle»?** Sí, dentro de lo que un
candado documental puede hacer: quien cambie el `auth_level` se encuentra la
suite en rojo y, al ir a mirar por qué, se topa con la explicación. No impide
que alguien cambie las dos cosas a la vez con conocimiento de causa —y no debe
impedirlo—. **Límite honesto que dejo escrito**: ningún test de este
repositorio atraviesa el proxy de la Static Web App, así que la comprobación
de que el montaje real funciona sigue siendo `MANUAL (humano)` (T14, T16). El
propio fichero lo dice.

---

## 4 · La ventana de escritura, el candado real (punto 2 del encargo)

**Verificado en el script, no en la prosa. CUMPLE.**

`infra/desplegar_backend.ps1`, líneas 363-389: `ARCHIVO_HABILITADO=false` entra
en el array `$ajustes` que se aplica con
`az functionapp config appsettings set` en **cada** ejecución, no dentro de una
rama condicional ni como valor por defecto que un despliegue previo pudiera
haber pisado:

```
    # EL CANDADO. La ventana de escritura se despliega CERRADA: fuera de ella
    # /api/archivar responde 503 a cualquiera y no toca SharePoint. Se
    # enciende a mano y se vuelve a apagar (docs/DESPLIEGUE.md, seccion 4).
    # Cada despliegue la devuelve a su sitio, por si quedo encendida.
    "ARCHIVO_HABILITADO=false",
```

La última línea del comentario es la que más me importa y es correcta: **una
segunda ejecución del despliegue vuelve a cerrar la ventana**, aunque alguien
la hubiera dejado abierta. Eso convierte la re-ejecutabilidad (R2) en una
propiedad de seguridad, no solo de comodidad.

Lo respaldan además:

- La **fase RED de R33**, y es la mejor evidencia de fase RED que he visto en
  este repositorio, porque el implementer **rechazó su propio rojo pobre**: el
  primer fallo era un `FileNotFoundError` (el script no existía), que no
  demuestra nada. Escribió entonces el script **entero y correcto omitiendo
  solo la línea de `ARCHIVO_HABILITADO`** —el descuido real que R33 previene— y
  pegó el rojo por aserción. Eso sí demuestra que el test tiene dientes.
- `test_f010_r33_el_despliegue_deja_la_ventana_de_escritura_cerrada` y
  `test_f010_r33_el_script_explica_por_que_la_ventana_nace_cerrada`.
- R34: el runbook (`docs/DESPLIEGUE.md` §4) trae las dos líneas de `az` que
  abren y cierran la ventana, sin redesplegar y sin tocar código.
- `settings.py:230` mantiene `ARCHIVO_HABILITADO` apagado por defecto, y la
  puerta se comprueba **en la fábrica y en el constructor del adaptador**
  (F-006), así que componer las piezas a mano tampoco deja subir.

**R28 verificado también**: la única aparición de `SIGRID` en
`desplegar_backend.ps1` es el comentario de la línea 26 —«NINGUNA VARIABLE DE
SIGRID»—. No hay ni una App Setting `SIGRID_*`.

---

## 5 · El escalonado de timeouts (punto 3 del encargo)

**Verificado. Cada capa cede antes que la de fuera, y hay test a los dos lados.**

| Capa | Valor | Dónde está fijado | Quién lo vigila |
|---|---|---|---|
| IA (backend) | **35 s** | `infra/desplegar_backend.ps1:105` `$TIEMPO_IA_S = 35` → App Setting `IA_TIMEOUT_S` | `test_f010_r20_*`: `constantes["TIEMPO_IA_S"] == 35` y `valor < 45` |
| Graph (backend) | **35 s** | `desplegar_backend.ps1:106` → `GRAPH_TIMEOUT_S` | ídem |
| Front | **40 s** | `services/postventa-front/js/config.js:42` `TIMEOUT_PETICION_MS: 40000` | `tests_js/test_config_timeout.test.js` |
| Proxy de la SWA | **45 s** | `infra/00_vars_postventa.ps1:56` `$PostventaPresupuestoProxyS = 45` (límite de plataforma, no elección nuestra) | `test_f010_scripts_infra.py:229` |

35 < 40 < 45. **Y el orden está vigilado por los dos extremos, no solo por
uno**, que es lo que hace que no se pueda romper por accidente:

- `f010 R21: el front aborta ANTES de que corte el proxy` → `40000 < 45000`.
- `f010 R21: y DESPUÉS de que se rinda el backend` → `40000 > 35000`, con el
  comentario correcto: si el front abortara antes que la IA, mataría peticiones
  que iban a responder.
- `f010 R21: el porqué del número está escrito al lado` → exige que el
  comentario de `config.js` mencione `45`, «proxy» y «escalonado». Impide que
  alguien suba el número sin enterarse de contra qué compite.

El test de JS **carga `config.js` de verdad** con `vm.runInContext` y un
`window` de mentira, en vez de duplicar sus valores. Es la forma correcta: un
test que copia el valor sigue en verde cuando el fichero ya dice otra cosa.

### El test de F-007 se actualizó, no se relajó

Comprobado en el commit `c2c572f`. `test_f007_estaticos.py` sigue **fijando un
valor exacto** por expresión regular; lo que cambia es el número
(`180000` → `40000`) y, al lado, **seis líneas de comentario explicando por
qué**: 180000 estaba **por encima** del corte de 45 s, así que el front nunca
llegaba a abortar por su cuenta y quien cortaba era la plataforma, con un error
opaco y la llamada a la IA viva por detrás gastando cuota.

Lo que habría sido relajarlo —cambiar el `assert` por un rango, o borrar la
fila del `parametrize`— **no ha pasado**. La vigilancia sigue intacta.

---

## 6 · Barrido, secretos y ejecución (puntos 4, 5 y 7)

- **Punto 4 · identificadores**: §2. Sin hallazgos reales.
- **Punto 5 · secretos por referencia a Key Vault**: verificado en
  `desplegar_backend.ps1:391-396`. Las nueve App Settings sensibles se
  construyen **siempre** como
  `"@Microsoft.KeyVault(SecretUri=" + $vaultUri + "secrets/" + $secreto + ")"`
  recorriendo el diccionario `$PostventaAppSettingsSecretas`. **No hay una sola
  rama que ponga el valor literal.** Y antes, línea 353, se fija
  `keyVaultReferenceIdentity` a la identidad gestionada, con su propio código
  de error: sin eso las referencias no se resolverían aunque el rol estuviera
  puesto. El detalle está bien visto.
- **Punto 7 · ninguna tarea manual ejecutada**: **confirmado.**
  - `git diff --stat dev...HEAD`: 61 ficheros, ninguno es un artefacto de
    ejecución (ni `.local.ps1`, ni fichero de estado, ni salida de `az`).
  - `git log --all --diff-filter=A` no ha añadido **nunca** ningún `.pdf`,
    `.docx`, `.xlsx`, `.jpg` ni `.png`: ningún parte escaneado ha entrado en
    git, en ninguna rama.
  - `git status` limpio salvo este informe.
  - Las nueve tareas `MANUAL (humano)` siguen en `[ ]` en `tasks.md`: T1, T13,
    T14, T14 bis, T15, T16, T17, T18, T19.
  - **Matiz que dejo por escrito, y no es un incumplimiento**: T2 **sí se
    ejecutó**, y está bien que se ejecutara (el líder se lo pidió y alimentaba
    D2). Fue **en local** contra `localhost:7073`, sin tocar Azure ni
    SharePoint, con diez llamadas reales al proveedor de IA y una remesa real
    del árbol sin versionar. **No se imprimió ni un campo del parte**: solo
    segundos y códigos HTTP. El guion vive en el temp de la sesión, no en el
    repositorio. Cumple lo que la tarea exigía.

---

## 7 · Verificación independiente de la campaña de mutación (C4 bis)

El informe declara **«Tiempo total: 11,1 s»**, muy por debajo de los 5 minutos,
así que el protocolo me obliga a **reejecutar la campaña**, no solo a
recalcularla. Hecho, con la salida fuera de `progress/`.

**a) Recálculo puro** (`harness.alcance` + `harness.mutacion.generar_mutantes`,
sin ejecutar la suite):

```
origen: rama ('0705d881d4a1c329006db5fe970c45bcb93c2e75', 'feature/F-010-despliegue')
  services/postventa-api/function_app.py:      55 lineas ->  0 mutantes
  services/postventa-front/dev_server.py:     188 lineas -> 20 mutantes
TOTAL lineas: 243 | TOTAL mutantes: 20
```

Coincide **exactamente** con el informe: mismo commit de origen, mismos dos
ficheros, mismas 55 + 188 = 243 líneas, mismos 20 mutantes.

**b) Prueba de control de los «cero mutantes» de `function_app.py`.** El
protocolo la exige porque un cero no distingue «no había nada que mutar» de
«el generador está roto». Ejecutando `generar_mutantes` sobre ese fichero
**ignorando la exclusión de alcance** salen **23 mutantes**. Es decir: el
generador funciona y el cero es **legítimo** — lo que F-010 tocó de ese fichero
es la cabecera del módulo, que no contiene ninguna expresión mutable. La nota
de alcance del informe dice la verdad.

**c) Campaña reejecutada entera**, con `__pycache__` borrada antes:

```
python -m harness.mutacion --feature F-010 --workers 1 --salida <scratchpad>
20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts en 17,2 s
```

**Coincide con el informe en los cuatro totales** (20 / 17 / 3 / 0), y los tres
supervivientes son los mismos tres: `dev_server.py:169`, `:171` y `:175`,
operador `[entero]`, `log.info("=" * 60)` → `log.info("=" * 61)`. **El informe
de mutación no está escrito a mano.**

`git status` quedó limpio después (solo este informe, sin trackear). La salida
nunca se escribió en `progress/`.

**d) Análisis de los supervivientes**: los tres están **completados**, ninguno
en `PENDIENTE`. Los tres son el mismo caso —el ancho de un separador decorativo
del banner de arranque de `dev_server.py`— y la calificación de **mutante
equivalente** es correcta: no altera ningún comportamiento observable, y
`desplegar_front.ps1` además excluye `dev_server.py` de la copia que se sube.
Un test que fijara el ancho de un adorno sería ruido. **En nivel `estandar` no
se exige cero supervivientes**, y estos tres están bien justificados.

---

## 8 · Recorrido de CHECKPOINTS.md

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde (ejecutado por el reviewer, §0).
- [x] Existen los ocho ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-010.
- [x] Rama actual `feature/F-010-despliegue`, nunca `main`.
- [x] `progress/current.md` encabeza con la sesión activa
      («F-010 IMPLEMENTADA, PENDIENTE DE REVISIÓN»). El resto del fichero es
      contexto permanente declarado (cola de decisiones, deuda con dueño,
      lecciones), no restos de sesión.
- [x] Las siete features `done` tienen su resumen en `progress/history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] Arquitectura hexagonal: **F-010 no añade ni una línea de producción en
      Python**. Lo único que toca de `function_app.py` es la cabecera del
      módulo. No hay dominio nuevo ni adaptador nuevo que pueda violarla.
- [x] Primera línea con la ruta relativa en los diez ficheros nuevos
      (comprobado uno a uno, incluidos los `.ps1`, el `.md` y el `.test.js`).
- [x] Sin `print()` de debug en el diff, sin secretos hardcodeados (§2), sin
      dependencias nuevas. `ruff`: 56 avisos, **los mismos 56 de deuda previa**;
      F-010 no añade ninguno.
- [x] La unidad de trabajo sigue siendo el parte: F-010 no toca esa lógica.
- [x] Nada se archiva sin validar: F-010 **refuerza** esta regla desplegando la
      ventana de escritura cerrada (§4).
- [x] Lo manuscrito, la firma, el no duplicar y el `conest` de Sigrid: N/A,
      **justificado** — F-010 no toca ninguna de esas rutas de código. Se
      verificó que el diff no altera `domain/`, `application/` ni los
      adaptadores de IA, SharePoint o persistencia.
- [x] Ningún parte escaneado ni PDF ha entrado en git: comprobado con
      `git log --all --diff-filter=A`, no solo con el árbol. **Cero ficheros**
      `.pdf/.docx/.xlsx/.jpg/.png` añadidos en toda la historia de todas las
      ramas.

### C3 bis — Documentos que entran de fuera

**N/A, justificado**: F-010 no añade ni modifica ningún fichero de
`docs/referencia/`. (El barrido de datos sensibles lo he hecho igualmente, §2,
porque el encargo lo pedía y porque una feature de despliegue es el sitio
natural donde se cuela un identificador.)

### C4 — La verificación es real

- [ ] **Cada requisito EARS tiene ≥ 1 test trazable y todos pasan.** Los tests
      existen y **todos pasan** (139 + 1 saltado), y la tabla de §9 no deja
      ningún requisito sin cubrir. **Pero dos requisitos no se cumplen aunque
      su test esté en verde**, y por eso este checkbox queda vacío:
      **R27** (el verificador puede subir a SharePoint cuando la lectura de la
      App Setting falla) y **R6** (`-WhatIf` borra un `SWA_CLI_DEPLOYMENT_TOKEN`
      preexistente). Los dos tests comprueban la forma y no la sustancia:
      «solo lecturas de `az`» en vez de la lógica de la guarda, y «hay
      restauración en un `finally`» en vez de «la restauración es correcta».
      Detalle y arreglo en §10 bis, puntos 1 y 3.
- [x] Los unit tests no tocan red ni BBDD: los de F-010 leen los `.ps1` y los
      `.md` **como texto** y evalúan `config.js` en un `vm` de Node. Ninguno
      abre un socket. La guardia de red de la suite sigue en pie.
- [x] Las verificaciones `MANUAL (humano)` están listadas con su comando
      exacto, pendientes del humano — **con una salvedad que anoto como O1**:
      viven en `specs/F-010-despliegue/tasks.md` §Fase 4 y en
      `docs/DESPLIEGUE.md`, no dentro de `progress/current.md`, que las nombra,
      las cuenta («las nueve») y remite a esos ficheros. Doy el checkpoint por
      cumplido en sustancia y dejo la mejora en §10.

### C4 bis — El rigor declarado se cumple

Nivel **`estandar`**, declarado en `harness/features.json` (`"rigor": "estandar"`).

- [x] La feature declara `rigor` con un valor válido.
- [x] **Fase RED**: presente y con **salida real** para los dos requisitos
      centrales — R33 (§4, incluido el rechazo explícito del «rojo pobre») y
      R32 (§3). Es fase RED de verdad, no una frase.
- [x] **Cobertura**: `PUERTA COBERTURA` en `[OK]`, **98,3 %** de 116 líneas
      cambiadas (114/116, umbral 80 %).
- [x] **Mutación**: informe generado por la herramienta, totales
      **verificados de forma independiente** y **campaña reejecutada** por ser
      de menos de 5 minutos (§7).
- [x] **Los muertos están comprobados, no solo contados**: reejecución
      completa, mismos cuatro totales, mismos tres supervivientes (§7c).
- [x] Cada superviviente con su análisis **completado**, ninguno en
      `PENDIENTE`. Nivel `estandar`: no se exige cero (§7d).
- [x] El informe del implementer trae la sección **«Evidencias»** con los
      cuatro números.
- [x] Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A, justificado**: este repositorio **no declara**
`harness/rutas_sensibles.json` (solo existe `rutas_sensibles.ejemplo.json`).
El propio checkpoint dice que sin esa declaración el bloque es N/A. `init.sh`
no señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]`.** **NO se cumple, y no puede
      cumplirse todavía**: quedan **nueve** en `[ ]`, y las nueve son
      `MANUAL (humano)` — T1, T13, T14, T14 bis, T15, T16, T17, T18, T19.
      **Ninguna es ejecutable por un agente**: crear un grupo en Entra, cargar
      secretos, desplegar, probar con dos cuentas, re-ejecutar los despliegues,
      subir a SharePoint y editar otro repositorio. Es lo previsto por diseño,
      no un olvido. Ver el veredicto (§11).
      Las **once** tareas de agente sí están `[x]`, cada una con su commit
      `F-010 Tn: ...` (T2–T12 y T20 verificados en `git log`).
- [x] Sin ficheros temporales ni artefactos sospechosos sin trackear.
      `git status` solo muestra este informe.
- [x] `features.json` refleja el estado real: `in_progress`. **Y así tiene que
      seguir** hasta que el humano ejecute las nueve.

---

## 9 · Trazabilidad · requisito → test que lo cubre

Todos ejecutados por el reviewer: **139 pasados, 1 saltado** en los cuatro
ficheros de F-010 del servicio `api`, más los tests de JS dentro de la suite
del `front`.

| R | Test que lo cubre | Estado |
|---|---|---|
| R1 | `test_f010_r1_*` (existen, ruta en la 1.ª línea, `.SYNOPSIS`) | ✔ verificado a mano también |
| R2 | `test_f010_r2_*` (creación precedida de comprobación) + **T17 MANUAL** | ✔ / pendiente humano |
| R3 | `test_f010_r3_*` (`-WhatIf` sin escrituras) | ✔ |
| R4 | `test_f010_r4_*` (`Read-Host` antes de la 1.ª escritura) | ✔ |
| R5 | `test_f010_r5_*` (≥ 5 códigos de salida, ninguno repetido) | ✔ |
| R6 | `test_f010_r6_*` (`$env:` restaurado en `finally`) | ✔ |
| R7 | `test_f010_r7_*` (ningún nombre literal fuera de `00_vars`) | ✔ |
| R8 | `test_f010_r8_*` + `test_f006_repo_sin_identificadores.py` + **barrido propio §2** | ✔ |
| R9 | `test_f010_scripts_infra.py:262,279,295,311` (SecureString, ni disco, ni traza, ni «los cuatro últimos») | ✔ |
| R10 | `test_f010_r10_*` (referencia a Key Vault, nunca el valor) | ✔ verificado a mano, §6 |
| R11 | `test_f010_r11_*` (rol antes de las App Settings, con comprobación) | ✔ |
| R12 | `:645`, `:657` (el fichero del repo conserva `<TENANT_ID>`) | ✔ |
| R13 | `:671` (la copia de trabajo se borra) | ✔ |
| R14 | `staticwebapp.config.json` + test de que el despliegue no lo pisa; **T16 MANUAL** | ✔ / pendiente humano |
| R15 | **MANUAL (humano)** — cuenta no miembro (T16) | pendiente humano |
| R16 | `:600`, `:613` (`appRoleAssignmentRequired` y el grupo) | ✔ |
| R17 | **MANUAL (humano)** — capa 5, es mejora no cimiento (T14) | pendiente humano |
| R18 | `test_f010_r18_health_sigue_anonimo` | ✔ |
| R19 | `f010 R19` ×2 en `test_config_timeout.test.js` (`baseApi` = `/api`, sin URL absoluta) | ✔ |
| R20 | `test_f010_r20_*` (35 y 35, los dos < 45) | ✔ |
| R21 | `f010 R21` ×3 (< 45000, > 35000, == 40000) | ✔ |
| R22 | `f010 R22` (los reintentos de lo transitorio siguen en pie) | ✔ |
| R23 | `test_f010_r23_*` — los nueve campos del esquema | ✔ verificado a mano |
| R24 | `test_f010_r24_*` — `requiredGroupId` es marcador (`REEMPLAZAR_ID_GRUPO_POSVENTA`) | ✔ |
| R25 | `test_f010_r25_*` — los cuatro pasos, sin fijar ejecutor | ✔ verificado a mano |
| R26 | `test_f010_r26_*` — `INTEGRACION.md` §8 nombra F-008/F-009 y F-019 | ✔ |
| R27 | `:762`, `:773`, `:783` (sin URL no llama; las tres comprobaciones; solo lecturas) | ✔ |
| R28 | `test_f010_r28_*` — ninguna variable `SIGRID_*` | ✔ verificado a mano, §4 |
| R29–R31 | **MANUAL (humano)** — T18, con autorización expresa ante C5 | pendiente humano |
| R32 | `test_f010_r32_*` ×4, con **control negativo** | ✔ §3 |
| R33 | **Fase RED** + `test_f010_r33_*` ×2 | ✔ §4 |
| R34 | `test_f010_r34_*` — las dos líneas de `az` del runbook | ✔ |
| R35 | **MANUAL (humano)** — tope de gasto (T14 bis) | pendiente humano |

**Ningún requisito queda sin cobertura.** Los siete que quedan pendientes son
los declarados `MANUAL (humano)` en la propia spec.

---

## 10 · Los scripts, leídos con lupa (puntos 5 y 6 del encargo)

Auditados **por lectura**, sin ejecutar ni uno y sin tocar Azure.

### Re-ejecutabilidad (R2) — el criterio de aceptación nº 1

- **Los trece recursos que se crean tienen su guarda de existencia**, uno a uno:
  grupo de recursos, Key Vault, almacenamiento, Log Analytics, App Insights,
  identidad gestionada, Function App, Static Web App, registro de aplicación,
  service principal, asignación del grupo, enlace de backend. **No hay ni un
  `az ... create` sin guarda**, y **ningún `delete`, `purge` ni `--overwrite`**
  en todo el conjunto. Lo fija además `test_f010_r2_*`.
- Las escrituras que van sin guarda son **idempotentes por naturaleza**
  (`--set keyVaultReferenceIdentity`, `appsettings set`,
  `appRoleAssignmentRequired=true`, `role assignment create` —cuyo
  `$LASTEXITCODE` se ignora **a propósito** y se sustituye por la verificación
  explícita de `desplegar_backend.ps1:328`, que es el patrón correcto—).
- **El punto delicado, y está bien resuelto**: `desplegar_front.ps1` **sí**
  regenera el secreto de cliente en modo completo, y el script lo declara en su
  cabecera como peligro conocido (líneas 13-23, con la lección de
  `azure-apps/portal.md`). Dos cosas lo hacen seguro:
  1. Usa `az ad app credential reset ... --append` (línea 322): **añade** una
     credencial en vez de reemplazarla, así que la anterior no se invalida.
  2. Existe el modo **`-SoloFront`** (línea 50), que «no toca Entra, no regenera
     el secreto y no reescribe las redirect URI». Ese es el modo de todos los
     días; el completo se reserva para cuando de verdad haya que rotar.
- Ninguna operación de borrado ni `--overwrite` en el camino normal.

### `-WhatIf` (R3), confirmación (R4) y códigos de salida (R5)

- Los tres scripts de despliegue declaran `[switch]$WhatIf` y cortan **antes**
  de la primera escritura (`desplegar_front.ps1:206`,
  `verificar_despliegue.ps1:195`), imprimiendo qué harían.
- La confirmación es un `Read-Host` explícito —«Escribe DESPLEGAR para
  continuar»— situado **después** del resumen y **antes** de escribir nada
  (`desplegar_front.ps1:222`).
- Códigos de salida distintos por causa, con constantes nombradas
  (`$SALIDA_SIN_PERMISO_KEYVAULT`, `$SALIDA_NOMBRE_OCUPADO`,
  `$SALIDA_FALTA_PARAMETRO`, `$SALIDA_FALLO`…), y `test_f010_r5_*` exige al
  menos cinco sin repetir. Los mensajes dicen **qué hacer a continuación**, no
  solo qué falló.

### Sesión limpia y secretos (R6, R9, R12, R13)

El `finally` de `desplegar_front.ps1:420-431` cubre bien lo que más riesgo
tiene —**salvo la restauración del token, que está mal: ver §10 bis, punto
3**—:

- borra **la copia de trabajo** (lleva el `<TENANT_ID>` ya sustituido),
- borra **el fichero de cuerpo de Graph** (lleva identificadores de grupo y de
  aplicación),
- e **intenta** restaurar `$env:SWA_CLI_DEPLOYMENT_TOKEN` a su valor previo
  — intención correcta, ejecución defectuosa: `$tokenPrevio` solo se rellena en
  `:389`, así que toda salida anterior restaura `$null` y **borra** la variable.
  **Defecto 3 de §10 bis.**

`cargar_secretos_postventa.ps1` pide las credenciales con
`Read-Host -AsSecureString`, no las escribe en disco y no las imprime **ni
recortadas** — hay un test específico para el «los cuatro últimos caracteres»,
que es la forma habitual de filtrar un secreto creyendo que no.

`test_f010_scripts_infra.py:645,657` comprueba sobre **el fichero de verdad**
—no sobre el script— que `staticwebapp.config.json` conserva su marcador.

### El verificador solo lee (R27)

`verificar_despliegue.ps1` hace **una sola** llamada a `az`, y es
`appsettings list` (lectura). Lo demás son `Invoke-WebRequest`. Comprueba las tres cosas: `health`, `archivar` → `503` y la SWA redirigiendo al
inicio de sesión (comprobando la cabecera `Location`, no solo el 3xx). El PDF
que envía es **sintético**.

Y trae la cautela que debería salvarlo de ser justo lo que promete no ser: lee
`ARCHIVO_HABILITADO` antes de llamar a `/api/archivar` y, si la encuentra
encendida, no hace la llamada, lo dice en rojo y lo cuenta como hallazgo. La
intención es exactamente la correcta.

**Pero la guarda falla abierta**: el tercer valor que devuelve la lectura,
`"desconocida"`, cae en la rama que **sí** llama. Es el defecto 1 de §10 bis y
el motivo principal del rechazo.

---

## 10 bis · CAMBIOS REQUERIDOS

Cinco defectos, todos en `infra/`, todos de arreglo corto. Los he verificado
uno a uno leyendo el fichero, no fiándome de un resumen.

### 1. `verificar_despliegue.ps1:230` — la guarda de la ventana **falla abierta**

Es el más grave y el único que puede acabar en una escritura real.

```powershell
$ventana = Get-Ventana-De-Escritura -Funcion $PostventaFunction -Grupo $PostventaGrupo
...
if ($ventana -eq "true") {
    # no se hace la llamada
}
else {
    # POST /api/archivar con cuerpo COMPLETO y VÁLIDO
}
```

Pero `Get-Ventana-De-Escritura` (`:183-192`) devuelve **tres** valores:
`"true"`, `"false"` y **`"desconocida"`**, este último cuando `az` falla
(`if ($LASTEXITCODE -ne 0) { return "desconocida" }`). Y `"desconocida"` **no
es `"true"`**, así que cae en el `else` y **lanza el POST igual**.

Cuándo pasa: sin sesión de `az`, sin permiso de lectura sobre la Function App,
con la suscripción equivocada, o —el más probable— **con un `$PostventaSufijo`
puesto en `00_vars_postventa.local.ps1` en el despliegue pero no disponible al
verificar**: la consulta falla, el script no sabe si la ventana está abierta, y
llama de todos modos con `veredicto=apto` y `destino=archivo_y_cierre`.

Si en ese momento la ventana estuviera **abierta** —y el único momento en que
se abre es **T18**, que es justo cuando se verifica— el POST **sube un PDF a
SharePoint**. Es literalmente lo que el script promete no hacer y lo que su
propio comentario presume de evitar.

**Una guarda que ante la duda decide seguir no es una guarda.** Arreglo, una
línea:

```powershell
if ($ventana -ne "false") { ... no llamar, y decir por qué ... }
```

Y que el veredicto final no pueda salir en verde con `$ventana = "desconocida"`.

### 2. `desplegar_front.ps1:327-328` — dos escrituras al Key Vault sin comprobar

```powershell
az keyvault secret set ... --name "swa-client-id"     ... | Out-Null
az keyvault secret set ... --name "swa-client-secret" ... | Out-Null
az staticwebapp appsettings set ...                   | Out-Null
if ($LASTEXITCODE -ne 0) { Salir-Con "No se han podido fijar las App Settings del front." ... }
```

El `if` guarda **solo la tercera**. Si el vault no existe o falta el rol
*Secrets Officer*, el `swa-client-secret` **no se guarda y el script termina en
verde**: el secreto queda únicamente en la Static Web App y se rompe la
promesa de la cabecera («un solo sitio donde mirar»). Además,
`desplegar_front.ps1` **nunca comprueba que el Key Vault exista**, cosa que
`desplegar_backend.ps1:238` sí hace y con código de salida propio.

### 3. `desplegar_front.ps1:107` + `:431` — `-WhatIf` borra un token preexistente

`$tokenPrevio = $null` (`:107`), y **solo** recibe valor en `:389`. El `try`
empieza en `:160` y el `finally` de `:420` hace
`$env:SWA_CLI_DEPLOYMENT_TOKEN = $tokenPrevio`. En PowerShell asignar `$null` a
una variable de entorno **la borra**.

Como `exit` dentro del `try` ejecuta el `finally`, **cualquier salida temprana
—incluida la de `-WhatIf` en `:209`, y la confirmación denegada— elimina de la
consola un `SWA_CLI_DEPLOYMENT_TOKEN` que el operador ya tuviera** (por
ejemplo, del portal). **Incumple R6**: «el sistema debe dejar la sesión de
PowerShell como estaba». Arreglo: leer el previo **antes** del `try`, o
restaurar solo si se llegó a asignar.

Nota: el test de R6 pasa porque comprueba que toda asignación a `$env:` tiene
su restauración en un `finally` — y la tiene. Lo que no comprueba es que la
restauración sea **correcta**. Es un caso de libro de test que pasa sin
verificar el requisito.

### 4. `desplegar_front.ps1:43-45` — el `.DESCRIPTION` afirma algo falso

> «Con `-SoloFront` no se genera nada: **se leen del Key Vault los que ya hay**.»

**No hay ni un `az keyvault secret show` en todo el fichero** (comprobado:
0 ocurrencias). `-SoloFront` simplemente se salta el bloque `:254-336` y deja
las App Settings como estén. El efecto es correcto; la explicación no lo es.

Importa por la misma razón por la que importa R32, y este repositorio la tiene
escrita: **una nota que miente es peor que no tener nota.** Alguien leerá esto
y creerá que `-SoloFront` repara unas App Settings borradas a mano. No lo hace.

### 5. `desplegar_front.ps1:322` — el secreto se acumula y nunca se revoca

`az ad app credential reset ... --append` **no invalida** la credencial
anterior — cosa buena, porque no rompe el despliegue vivo. Pero cada ejecución
en modo completo **añade una credencial `swa` más, todas válidas y ninguna
revocada nunca**. Al cabo de unos despliegues hay N secretos activos para el
registro de aplicación del inicio de sesión.

No pido cambiar el `--append`. Pido **dejarlo escrito** en la cabecera —que hoy
habla de la lección del portal, donde el secreto **sí** se invalidó, y no dice
que aquí el comportamiento es el contrario— y que el resumen final avise de
cuántas credenciales hay, o que el runbook incluya cómo retirar las viejas.

### Y dos que NO son cambios requeridos, pero conviene saber

- **`desplegar_front.ps1:270`**, `az ad app update --web-redirect-uris`
  reemplaza la lista entera. **Está documentado** en la cabecera (`:24-26`) y
  mitigado con `-RedirectExtra`. Es comportamiento conocido de la plataforma,
  no un descuido. Lo dejo señalado porque una redirect URI añadida a mano en el
  portal se perderá en el siguiente despliegue completo.
- **`PATRON_ESCRITURA_AZ`** (`test_f010_scripts_infra.py:69-71`) exige el
  prefijo `az `, así que **no ve** `swa deploy` (`:394`), `func azure
  functionapp publish` (`desplegar_backend.ps1:410`), `az rest --method POST`
  (`:311`) ni `az ad app credential reset` (`:322`). La garantía de R3 y R4 es
  por tanto más débil de lo que aparenta: hoy esas llamadas están **después**
  de la confirmación y del corte de `-WhatIf`, verificado a mano, pero el test
  no lo sostendría si se movieran.

---

## 11 · VEREDICTO

# CHANGES_REQUESTED

**Y conviene leer esto antes que la etiqueta**, porque el rechazo es estrecho:

> **La feature es aprobable, y de calidad alta.** El rechazo **no** es por las
> nueve tareas `MANUAL (humano)` —están bien preparadas, con su comando
> exacto, y ninguna se ha ejecutado, que es exactamente lo correcto—. Es por
> **cinco defectos concretos de los scripts de `infra/`** (§10 bis), cuatro de
> ellos de una línea. Corregidos esos cinco, esta feature queda **APROBADA a la
> espera de que el humano ejecute las nueve tareas manuales**.

### Por qué esos cinco bloquean, y no van a «observaciones»

Porque **dos de ellos son requisitos EARS que no se cumplen aunque su test esté
en verde**, que es justo lo que C4 bis existe para cazar:

- **R27** («un script de verificación que, **sin subir nada a ningún sitio**,
  compruebe…») no se cumple: hay un camino en el que sube. El test comprueba
  «solo lecturas» de `az` y las tres comprobaciones, pero no la lógica de la
  guarda.
- **R6** («el sistema debe dejar la sesión de PowerShell **como estaba**») no
  se cumple: `-WhatIf` borra una variable preexistente. El test comprueba que
  hay restauración en `finally`, no que la restauración sea correcta.

Y porque los otros tres tocan la línea que este repositorio defiende con más
insistencia —la de R32—: **una nota que miente es peor que no tener nota**, y
estos scripts los va a ejecutar un humano contra Azure leyendo su `.DESCRIPTION`.

### Lo que queda APROBADO tal cual está

Para que la corrección no se lleve por delante lo que ya está bien:

- **El encargo prioritario (§1)**: el análisis del bytecode envenenado está
  cerrado, con medidas. **F-005 y F-006 no están invalidadas** y no hay que
  reejecutar nada.
- **D3 / R32 (§3)**: la nota y el test son correctos, con control negativo y
  fase RED real. **No tocar.**
- **La ventana de escritura (§4)**: se despliega **apagada**, en cada
  ejecución, con la mejor fase RED del repositorio. **No tocar.**
- **El escalonado 35 / 40 / 45 (§5)**: correcto, vigilado por los dos extremos,
  y el test de F-007 **actualizado, no relajado**. **No tocar.**
- **Sin identificadores ni secretos (§2, §6)**: barrido propio sin hallazgos;
  las nueve App Settings sensibles, siempre por referencia a Key Vault.
- **Mutación y cobertura (§7)**: campaña reejecutada, totales coincidentes,
  supervivientes analizados, 98,3 % de cobertura.
- **Nada ejecutado contra Azure ni SharePoint (§6)**.

### Sobre C5, que seguirá incompleto después de corregir

`CHECKPOINTS.md` C5 exige `tasks.md` con todas las casillas `[x]`, y quedan
nueve. **Las nueve son `MANUAL (humano)` y ninguna es ejecutable por un
agente**: crear un grupo de seguridad en Entra, cargar once secretos en un Key
Vault, desplegar contra Azure, probar el acceso con dos cuentas reales,
re-ejecutar los despliegues, subir un fichero a SharePoint y editar otro
repositorio. Rechazar por eso sería rechazar a un implementer por no haber
hecho lo que tiene **prohibido** hacer.

Hay precedente en este mismo repositorio: **F-006 se cerró con su T18 vacía
por dependencia declarada**, con autorización expresa del humano ante C5. Aquí
la situación es la misma, ampliada.

Lo que sí verifico, y es lo que me corresponde: que las nueve estén
**preparadas con su comando exacto**, que **ninguna se haya ejecutado por su
cuenta**, y que lo entregado sea correcto. Las tres cosas se cumplen.

### Condiciones de cierre (para el humano, no para el implementer)

**Y el orden importa**: los cinco arreglos de §10 bis van **antes** de ejecutar
ninguna tarea manual. Tres de ellos (1, 2 y 3) están en scripts que la primera
tarea manual ya ejecuta, y el defecto 1 es peligroso precisamente durante T18.

0. **Corregir los cinco defectos de §10 bis** y volver a pasar por review.
1. **`F-010` sigue `in_progress`** hasta que se ejecuten T1, T13, T14, T14 bis,
   T15, T16, T17, T18 y T19, con su **resultado real anotado** en `progress/`.
2. **T14 bis (tope de gasto y alerta en el proveedor de IA) va ANTES de T16**,
   no después. Es la única defensa proporcionada frente a que un desconocido
   consuma cuota contra `/api/extraer` y `/api/firma`, que quedan anónimos por
   diseño (§3). El orden importa: en cuanto el front esté publicado, los
   endpoints son alcanzables.
3. **T18 exige autorización expresa nombrando `CHECKPOINTS.md` C5**, porque
   cierra una casilla de **F-006**, una feature ya cerrada. Y si en el listado
   aparece un fichero con sufijo `(1)`, **es una PARADA** (R31).
4. **Tras T18, volver a cerrar la ventana de escritura**
   (`ARCHIVO_HABILITADO=false`). El despliegue la vuelve a cerrar sola, pero
   entre T18 y el siguiente despliegue no hay nada que la cierre salvo la mano
   del humano.
5. **T19 se hace en `front-portal`**, con el GUID real del grupo, que **nunca**
   entra en este repositorio.

---

## 12 · Observaciones y propuestas (ninguna bloquea)

**O1 · Las nueve verificaciones manuales no están en `current.md` con su
comando.** `CHECKPOINTS.md` C4 lo pide ahí. Hoy `current.md` las nombra, las
cuenta y remite a `specs/F-010-despliegue/tasks.md` §Fase 4 y a
`docs/DESPLIEGUE.md`, donde sí están una a una con su comando exacto. Doy el
checkpoint por cumplido en sustancia, pero **antes de mergear** convendría
pegar en `current.md` una tabla de nueve filas: es el fichero que se lee al
retomar la sesión, y el que evita que alguien ejecute T16 antes que T14 bis.

**O2 · Huecos del barrido automático de identificadores** (§2 bis). El barrido
repo-wide solo caza GUID; FQDN, IP y credenciales solo se barren en los cinco
scripts de F-010. Un `func-postventa-dev.azurewebsites.net` real escrito en
`docs/DESPLIEGUE.md` o en un informe de `progress/` **pasaría todos los tests**.
Es la misma clase de fallo que H1 de F-006. Y la lista de extensiones no incluye
`.js`/`.html`, así que `js/config.js` queda fuera. Propongo una feature pequeña
de arnés que suba `PATRON_HOST` y `PATRON_CREDENCIAL` al barrido repo-wide y
añada esas extensiones. Hoy el árbol está limpio: lo he comprobado a mano.

**O3 · `ohana.ruesma.es` y la zona `ruesma.es`** aparecen en
`specs/F-010-despliegue/design.md:342,525` justificando D5. Es DNS público y el
contexto es una decisión de diseño, no un dato de conexión. Lo dejo a criterio
del humano; no lo considero hallazgo.

**O4 · Dieciséis worktrees huérfanos** de una campaña de F-005 siguen
registrados en `git worktree list`
(`%TEMP%\mutacion_F-005_zllkg8wf\wk_0..wk_15`, en el commit `48fb104`). No los
toco. Se limpian con `git worktree prune` tras borrarlos, o con
`git worktree remove --force`. Sugiero además que la campaña paralela intente
la retirada también cuando el proceso muere por señal.

**O6 · R16, el «y SOLO ese grupo», no lo verifica el script.**
`desplegar_front.ps1:302-317` asigna el grupo y `:309` lee `appRoleAssignedTo`
únicamente para decidir si hace el POST. Si alguien asignó a mano **otro**
grupo o un usuario suelto a la aplicación empresarial, la re-ejecución **ni lo
detecta ni lo dice**. Y a diferencia del patrón de R11, tampoco se confirma que
`appRoleAssignmentRequired` haya quedado realmente en `true`: solo se mira el
código de salida del `update`. Hoy el «solo ese grupo» descansa en la
verificación **manual** de T16, no en el script. No lo hago bloqueante porque
T16 lo cubre con dos cuentas reales, pero un `list` con aviso al final del
despliegue costaría tres líneas y cerraría el hueco.

**O7 · Códigos de salida: el 6 mezcla causas.** En
`cargar_secretos_postventa.ps1:147` y `desplegar_backend.ps1:192` el código 6
—declarado como «fallo del despliegue»— se usa también para **errores de uso**
(nombres inválidos en `-Solo`, carpeta del servicio no encontrada). Y el 4
(«nombre global ocupado») se dispara ante **cualquier** fallo de
`az keyvault create`, incluido un problema de permisos, con un mensaje que
manda inventar un sufijo que no arreglaría nada. R5 pide «un código distinto
**por causa**»; hay siete, pero dos agrupan causas heterogéneas. Menor.

**O5 · Discrepancia menor en las «Evidencias»**: el informe dice «1.063
pasados, **1 saltado**» en el servicio `api`; mi ejecución da «1.063 pasados,
**11 saltados**». El número de pasados es correcto; el de saltados, no. No
cambia nada material, pero una sección que se llama «Evidencias» debe traer
los números tal cual salen.

### Propuestas al protocolo del arnés (no aplicadas; las decide el humano)

**P5 · El arreglo del bytecode envenenado, en `arnes-base`.** Una línea:
pasar `env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}` al
`subprocess.run` de `EjecutorPytest.ejecutar` (`harness/mutacion.py:304`). Es
más robusto que borrar `__pycache__` al restaurar, porque no depende de acertar
con todos los directorios. Confirma y resuelve el **P4** que yo mismo levanté
revisando F-007, ahora con el mecanismo medido (§1).

**P6 · Un criterio objetivo para el reviewer, en `CHECKPOINTS.md` C4 bis.**
Junto a la regla de los 5 minutos que ya existe, añadir la inversa:

> Si el «Tiempo total» del informe de mutación **dividido entre el número de
> mutantes** da **menos de 1 segundo**, la campaña es sospechosa por
> construcción —la caché de bytecode puede no haberse invalidado entre
> mutantes— y hay que relanzarla con `__pycache__` borrada antes de creerse
> los totales.

Es barato, se comprueba de un vistazo y es exactamente el criterio que separa
las campañas sanas de este repositorio (F-005: ~50 s/mutante; F-006: ~14 s) de
la que falló (F-010: 0,55 s). Vale para cualquier proyecto: a `arnes-base`.

**P7 · Registrar en `CHECKPOINTS.md` la prueba de control del cero.** Ya está
en el protocolo del reviewer para «cero mutantes»; propongo la gemela para
«cero supervivientes» en nivel `critico`: un cero solo es creíble si la campaña
se ejecutó con la caché limpia **o** si el ciclo por mutante supera el segundo.

---

# 13 · SEGUNDA RONDA · verificación de las correcciones (2026-08-20)

Reviso **solo** lo corregido, según instrucción del líder. Lo demás quedó dado
por bueno en la 1.ª ronda y el implementer tenía orden expresa de no tocarlo.

Punto de partida verificado: `git status` limpio, ocho commits nuevos
(`c800232`, `823e8e3`, `2818d66`, `df9c9cc`, `613e9a3`, `054dc74`, `b8b3128`,
`4b8dad3`). Las nueve tareas `MANUAL (humano)` siguen en `[ ]`: **nada se ha
ejecutado contra Azure ni SharePoint**.

## 13.1 · El listón que puse: ¿se arreglaron TAMBIÉN los tests?

Era la condición dura, porque los defectos 1 y 3 eran **requisitos EARS
incumplidos con su test en verde**. **Sí, y bien.**

### R27 (defecto 1) — `verificar_despliegue.ps1`

El script ahora **falla cerrado**: `if ($ventana -ne "false")`. Solo llama
cuando la lectura **demuestra** que la ventana está cerrada; con `"true"` y con
`"desconocida"` no llama, y cada caso da su mensaje. **Y va más allá de lo que
pedí**: el veredicto final exige `$ventanaOk`, así que `DESPLIEGUE VERIFICADO`
ya no puede imprimirse habiéndose saltado una de las tres comprobaciones. Esa
mejora no estaba en mi lista y es correcta: *una comprobación que no se ha
hecho no es una comprobación superada*.

**El test que daba R27 por bueno exigía literalmente el defecto**, y se
corrigió:

```python
-    assert 'if ($ventana -eq "true")' in cuerpo
+    assert 'if ($ventana -ne "false")' in cuerpo
```

Más dos tests nuevos con dientes de verdad:

- `test_f010_t7_la_guarda_de_la_ventana_falla_cerrada` extrae **las guardas de
  nivel superior** por expresión regular y afirma `guardas == ['-ne "false"']`
  — **igualdad exacta de lista**, no una pertenencia. Una regresión a
  `-eq "true"` da `['-eq "true"']` y falla. Y distingue bien: permite que
  *dentro* se separe `"true"` de `"desconocida"` para dar un mensaje u otro,
  porque eso no decide la llamada.
- `test_f010_t7_el_veredicto_no_sale_en_verde_con_la_ventana_desconocida` fija
  `$ventanaOk` dentro de la condición del veredicto y su definición.

### R6 (defecto 3) — `desplegar_front.ps1`

`$tokenPrevio = $env:SWA_CLI_DEPLOYMENT_TOKEN` sube a la línea **136**, **antes
del `try` de la 189**; la asignación de la 395 pasa a comentario. Cualquier
salida temprana —`-WhatIf`, confirmación denegada, cualquier `Salir-Con`— ya
restaura el valor real y no `$null`.

El test nuevo es el que cierra el hueco de verdad:
`test_f010_r6_el_valor_previo_se_lee_antes_del_try_que_lo_restaura` está
**parametrizado sobre todos los scripts que escriben** y comprueba, para
**cada** `$env:` que se asigne, que su lectura previa ocurre antes del `try`.
No parchea el caso concreto: fija la propiedad.

### Los dos tienen dientes, y se demuestra sin ejecutarlos

Ambos fallan **por construcción** sobre el código anterior:
`['-eq "true"'] != ['-ne "false"']`, y la lectura de `$tokenPrevio` estaba en
la 389 con el `try` en la 160, así que `lectura.start() < inicio_try` era
falso.

## 13.2 · Los otros tres defectos

| # | Qué pedí | Qué hay ahora | |
|---|---|---|---|
| 2 | Comprobar las dos escrituras al Key Vault | `:371-379`, cada `secret set` con su `if ($LASTEXITCODE -ne 0)` y **código de salida propio nuevo** (`$SALIDA_SIN_KEYVAULT = 9`), más la **guarda de existencia del vault** en `:257`, que faltaba. El mensaje del segundo avisa de que «el secreto acaba de generarse y NO ha quedado guardado» | ✔ |
| 4 | Que el `.DESCRIPTION` deje de mentir | `:44-46`: «con `-SoloFront` no se genera nada **Y TAMPOCO SE LEE NADA** […] no hay un solo `az keyvault secret show` en él». Verificado: siguen siendo **cero** ocurrencias | ✔ |
| 5 | Declarar que las credenciales se acumulan | `:54` explica que `--append` **no invalida** las anteriores, `:62` da el `az ad app credential delete` para retirarlas, y el resumen final (`:466`) **imprime cuántas credenciales `swa` hay** | ✔ |

El 5 se resolvió mejor de lo que pedí: no solo se documenta, se **mide y se
enseña** al terminar.

Los tres llevan test propio, y el de la cabecera está bien pensado: afirma
`afirma_que_lee == lee_de_verdad`, es decir, fija que la nota y el código
**digan lo mismo**, no que digan una cosa concreta. Es el patrón de R32
aplicado a otra cabecera.

## 13.3 · El arreglo del arnés, comprobado ejecutándolo

`harness/mutacion.py:310-319` pasa
`env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}` al subproceso: exactamente
la P5 que propuse, con `os.environ` heredado.
`tests/test_mutacion_sin_bytecode.py` vigila **las dos mitades** —la variable, y
que se herede el entorno—, y la segunda importa tanto como la primera: sin
heredar `PATH` y `VIRTUAL_ENV`, todos los mutantes «morirían» por fallo de
importación y la campaña mataría el 100 % sin comprobar nada. La suite raíz
pasa de 16 a **17 tests**.

**Verificado empíricamente por mí**, que es como había que cerrarlo. Campaña en
serie (`--workers 1`, el peor caso para el envenenamiento), con `__pycache__`
borrada antes:

```
20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts en 21,7 s
--- pyc de dev_server tras la campaña ---
  NO existe __pycache__ en postventa-front: no se ha escrito bytecode
--- suite del front inmediatamente después ---
74 passed in 1.65s
```

**No queda ni un `.pyc`**, y la suite del front pasa **inmediatamente después**
de la campaña: exactamente el escenario que antes la ponía en rojo con el árbol
limpio. Y los totales vuelven a ser **20 / 17 / 3**, los mismos de la 1.ª
ronda: confirma otra vez que aquellos números no estaban falseados.

Los **16 worktrees huérfanos** están limpiados: `git worktree list` pasa de 19
a **3** (el principal y dos de agente, ajenos a esto). **O4 cerrado.**

## 13.4 · La regla del coste por mutante, mejorada — y un matiz

El factor de workers es una **corrección real y necesaria** a mi P6, y la
acepto: la campaña es paralela por defecto y su «Tiempo total» es tiempo de
reloj. Sin el factor, toda campaña paralela sana se marca como sospechosa, y
*una regla que salta en falso se desactiva sola a la tercera vez*. Que
«Evidencias» declare ahora los workers es lo que la hace comprobable.

**El matiz, para que quede escrito**: la fórmula
`total × workers ÷ mutantes` supone que **todos** los workers están saturados.
Cuando hay más workers que mutantes —16 y 20, el caso de esta misma feature— la
mayoría queda ociosa enseguida y la fórmula **sobreestima**: da 8,9 s donde el
ciclo real por mutante del servicio `front` es 0,86 s. Es decir, **en esa
configuración la regla no habría marcado la campaña envenenada**.

Lo que la salva es su segunda mitad, que ya está en el texto: «**o muy por
debajo del tiempo de la suite que el propio informe declara**». Ese es el
criterio robusto —el coste por mutante no puede bajar de lo que tarda la
suite— y funciona con y sin paralelismo. **No pido cambiarlo**; sugiero que en
`arnes-base` la comparación contra el tiempo de la suite se presente como el
criterio **principal**, el umbral de un segundo como atajo, y que el factor use
`min(workers, mutantes)`.

## 13.5 · Sobre `ARNES_VERSION=1.5.2` frente a `arnes-base` 1.6.3

El líder pregunta si el desfase es un defecto a corregir dentro de F-010.
**Mi criterio: no — y además está bien documentado, mejor de lo que la
pregunta sugiere.**

`harness/ARNES_VERSION.md` **no finge nada**. Dice literalmente que este
repositorio **no lleva la 1.6.x completa**, que `harness/VERSION` sigue en
`1.5.2` **a propósito**, que de la rama 1.6 se ha traído **únicamente** el
parche de la 1.6.3, y que 1.6.0/1.6.1/1.6.2 están pendientes — con el motivo
concreto: **la 1.6.0 rehace `harness/mutacion.py` entero** (línea base de la
suite, veredicto «base rota», mutación de `is`/`is not`) y **sus números no son
comparables** con los de antes.

Eso es exactamente para lo que existe ese fichero. Sellar `VERSION=1.6.3`
sería **mentir**, y es el mismo pecado que acabo de hacer corregir en la
cabecera de `desplegar_front.ps1`. Y traerse la 1.6.x entera dentro de F-010
sería peor: metería un motor de mutación **reescrito y sin revisar** en mitad
de una review, invalidando las campañas que acabo de verificar, dentro de una
feature de despliegue. Eso es el LÍMITE DE SERVICIO de `CLAUDE.md`.

**Trabajo aparte, y recomiendo que sea el siguiente.** El dato que lo justifica
lo aporta el propio líder: en `arnes-base` hay un encargo del **2026-08-19**,
escrito desde `datamart-seg-anual`, que describe **este mismo defecto del
bytecode** y lo arregló allí como **1.6.0**. Es decir: **hemos gastado una
review entera redescubriendo un fallo ya resuelto río arriba**. Ese es el coste
real del desfase, medido y con fecha, y es el mejor argumento para no dejarlo
crecer. Propongo darlo de alta como feature de arnés, con la 1.6.0 revisada
aparte por lo que toca del motor de mutación.

## 13.6 · Portero, suites y árbol

Ejecutado todo por mí, con `__pycache__` borrada antes:

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` | **VERDE** — `ENTORNO LISTO` |
| Suite raíz del arnés | **17 pasados** (16 + el nuevo del bytecode) |
| Suite `api` | **1.070 pasados**, 13 saltados, 14,7 s |
| `test_f010_scripts_infra.py` | **110 pasados**, 3 saltados |
| Suite `front` | **74 pasados**, 1,65 s |
| PUERTA COBERTURA | **[OK] 98,3 %** de 116 líneas (114/116, umbral 80 %) |
| `ruff` | 56 avisos, **la misma deuda previa**, ninguno nuevo |
| `git status` | **limpio** |
| `git worktree list` | 3 (era 19) |

Comprobado además que el nuevo test de R6 **no se salta donde importa**: de sus
tres parametrizaciones, las dos que se saltan son scripts sin `try/finally`
(con su motivo impreso) y la que **se ejecuta es `desplegar_front.ps1`**, que
es justo el script del defecto.

---

# 14 · VEREDICTO DE LA SEGUNDA RONDA

# APROBADO

Los cinco defectos están corregidos **y los tests que los daban por buenos
están corregidos con ellos** — que era la condición que puse y la única que
importaba de verdad. Tres correcciones van **más allá** de lo pedido (el
`$ventanaOk` del veredicto, el código de salida propio del Key Vault con su
guarda de existencia, y el recuento de credenciales en el resumen), y ninguna
ha tocado nada de lo aprobado en la 1.ª ronda.

Los tres encargos que acepté están cumplidos: la regla del coste por mutante
está en `CHECKPOINTS.md` **y mejorada**, los worktrees huérfanos limpiados, y
el arreglo del arnés portado a `arnes-base` 1.6.3 con test propio y verificado
por mí ejecutándolo.

**F-010 queda APROBADA a la espera de que el humano ejecute las nueve tareas
`MANUAL (humano)`.** Siguen intactas las condiciones de cierre de §11, y
subrayo las dos que no son formalidades:

- **T14 bis —tope de gasto y alerta en el proveedor de IA— va ANTES de T16.**
  En cuanto el front esté publicado, `/api/extraer` y `/api/firma` son
  alcanzables, y son anónimos por diseño.
- **T18 exige autorización expresa nombrando `CHECKPOINTS.md` C5**, porque
  cierra una casilla de F-006. Y un fichero con sufijo `(1)` es **PARADA**.

`F-010` **sigue `in_progress`**: no pasa a `done` hasta que esas nueve estén
ejecutadas y anotadas con su resultado real.

