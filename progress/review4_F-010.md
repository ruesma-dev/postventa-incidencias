<!-- progress/review4_F-010.md -->
# F-010 · Review de cierre (cuarta ronda)

- **Rama:** `feature/F-010-despliegue` · HEAD `6b1c12f`
- **Fecha:** 2026-08-26
- **Rondas anteriores:** `review_F-010.md`, `review2_F-010.md`,
  `review3_F-010.md` (las tres CHANGES_REQUESTED)
- **Encargo:** estrecho. Verificar los tres puntos de `review3_F-010.md` §9 y
  emitir el veredicto de cierre. **No se revisa lo ya aprobado** (defectos 13,
  14, 15 y 16, resultados manuales, barrido de los 89 commits).
- **Nada ejecutado contra Azure, SharePoint ni PostgreSQL.** Solo lectura del
  repositorio, `bash harness/init.sh` tal cual, las suites locales, una campaña
  de mutación con salida fuera de `progress/` y **diez destrozos de la
  configuración de la SWA sobre una copia aislada en el scratchpad**.

## Veredicto

> ## **APPROVED**
>
> **F-010 puede pasar a `done`.** Los tres puntos del rechazo anterior están
> cerrados y verificados por mí, no por informe.

Los tres, en una línea cada uno:

- **9.1** — El test existe, y **vigila de verdad**: lo he roto yo mismo por
  **diez** caminos distintos sobre una copia aislada y se ha puesto en rojo en
  **nueve**, siempre con la guardia correcta y con el mensaje correcto. §1.
- **9.2** — R29 dice la verdad y **el requisito sale reforzado, no aflojado**:
  antes garantizaba «una URL que apuntar al despliegue», ahora garantiza
  **«solo desde el entorno desplegado y sin ninguna URL que escribir»**. §2.
- **9.3** — Texto y solo texto: **ni una línea ejecutable cambiada** fuera de
  dos `Write-Host` de salida, verificado línea a línea contra los límites del
  bloque de ayuda. Los 160 tests de contrato de `infra/`, en verde. §3.

**Dos hallazgos míos, ninguno bloqueante**, y los dos escritos aquí para que no
se pierdan: un **hueco en la guardia del comodín** (§1.3) y **dos avisos de
`ruff` nuevos** que el informe da por deuda previa cuando son de esta ronda
(§3.2). Los dos se arreglan en una línea; ninguno es condición del `done` y en
§8 explico por qué.

---

## 1 · Punto 9.1 · ¿El test vigila de verdad?

Era el punto importante del encargo y es el único que se puede contestar
ejecutando, no leyendo.

### 1.1 Cómo lo he comprobado (no me he fiado de la fase RED del informe)

El informe del implementer pega cinco trazas en rojo, pero las obtuvo
**rompiendo el `staticwebapp.config.json` del árbol real** y restaurándolo. Yo
he hecho lo contrario, que además es lo que manda `CHECKPOINTS.md` C4 bis:
**copia aislada fuera del repositorio**.

```
<scratchpad>/f010rev4/staticwebapp.config.json   (copia byte a byte del real)
<scratchpad>/f010rev4/tests/test_f010_config_swa.py (copia del test)
<scratchpad>/romper_rev4.py                      (diez destrozos, uno por caso)
```

El test resuelve el JSON como `Path(__file__).parents[1] /
"staticwebapp.config.json"`, así que la copia con la misma forma de árbol lo
ejercita **exactamente igual** y **el repositorio no se toca en ningún momento**
(`git status` lo confirma, §5.4). Control previo con la configuración intacta:
`11 passed`.

### 1.2 Resultado: nueve de diez destrozos, en rojo y por el motivo correcto

Cinco de los diez casos son míos, no del implementer: los tres `b`/`c` y el
`4c`. No basta con que el test se ponga rojo: exijo que **la guardia que se cae
sea la que corresponde** a la condición rota.

| # | Destrozo | ¿Rojo? | Guardia que protesta |
|---|---|---|---|
| 1 | `/.auth/login/aad` se va al final de `routes` | **Sí** | `el_login_es_la_primera…` |
| 1b | El login deja de admitir `anonymous` | **Sí** | `el_login_es_la_primera…` |
| 2 | Se borra la regla `/*` | **Sí** | `el_comodin_exige_sesion…` |
| **2b** | **`/*` sigue exigiendo `authenticated` pero se le añade `anonymous`** | **NO** | **ninguna** — §1.3 |
| 3 | Se borra `responseOverrides["401"]` | **Sí** | `el_401_redirige…` |
| 3b | El `401` existe pero no redirige (`{"statusCode": 401}`) | **Sí** | `el_401_redirige…` |
| 3c | El `401` redirige a `/login` en vez de a la ruta anónima | **Sí** | `el_401_redirige…` |
| 4 | `allowedRoles` → `allowedRole` en `/*` | **Sí** | `no_hay_claves_fuera…` **y** `el_comodin…` |
| 4b | `responseOverrides` → `responseOverride` | **Sí** | `no_hay_claves_fuera…` (+3) |
| 4c | Clave inventada de primer nivel | **Sí** | `no_hay_claves_fuera…` |

**Las cuatro condiciones del encargo están cumplidas y demostradas.** Y tres
cosas que van más allá de lo que pedí y que conviene reconocer:

- **La condición 3 comprueba el destino y el `302`, no solo que la clave
  exista** (casos 3b y 3c). Las condiciones 1 y 3 son el mismo mecanismo por
  sus dos extremos, y fijarlas por separado dejaría pasar la combinación rota.
- **La condición 4 baja al nivel de ruta**, que es donde ocurre el fallo real
  (`allowedRole` en singular), no solo al de primer nivel.
- **Los siete destrozos en memoria del propio fichero** (`test_…la_guardia_caza
  _la_configuracion_estropeada`) son la guardia de la guardia: sin ellos, un
  `problemas_de_la_configuracion` que devolviera siempre `[]` dejaría los cuatro
  contratos en verde para siempre. Y no comprueban solo que proteste: exigen
  **la señal concreta** en el mensaje. Eso está bien pensado.

**Contraste con la fase RED del informe**: los cinco casos que él pegó
(`login_al_final`, `login_sin_anonimos`, `sin_regla_comodin`, `sin_override_401`,
`allowedRole_en_singular`) me han salido con **el mismo conjunto de tests
fallidos**, incluidos los arrastres cruzados que él explica en su §1.4 —el
`assert roto != original` protestando cuando el árbol ya viene roto de esa misma
manera—. **Las trazas del informe son reales.**

### 1.3 HALLAZGO · el hueco del caso 2b (no bloquea, y digo por qué)

`problemas_del_cierre` comprueba que **`authenticated` esté** en los roles de
`/*`. No comprueba que **`anonymous` no esté**. Con esto:

```json
{ "route": "/*", "allowedRoles": ["anonymous", "authenticated"] }
```

la aplicación **queda abierta a internet** y la suite entera sigue **verde**
—`11 passed`—. Es exactamente el modo de fallo que la condición 2 existe para
impedir, y que el docstring del propio fichero describe: «la aplicación queda
abierta a internet (…) el fallo silencioso: todo funciona, y de más».

**Y no es rebuscado**: es lo primero que teclearía quien esté peleando otra vez
con un bucle de login, y el patrón está **dos líneas más arriba en el mismo
fichero** —`/.auth/login/aad` lleva `["anonymous", "authenticated"]` con toda la
razón—. Copiar esa línea a `/*` abre la aplicación.

El arreglo es una línea en `problemas_del_cierre` (`ROL_ANONIMO in roles` →
problema) y un caso más en la parametrización. Lo mismo vale para `/api/*`.

**Por qué no bloquea**, y quiero que se lea entero porque es un juicio y no una
casilla:

1. **Las cuatro condiciones que exigí en `review3_F-010.md` §9.1 están
   implementadas y demostradas en rojo.** El trabajo cumple el encargo escrito.
   Rechazar ahora por una quinta condición que no puse sería mover el listón en
   la última ronda, que es justo lo que argumenté que no se puede hacer cuando
   dictaminé que T14 bis no bloqueaba (§7 de la review anterior). El criterio
   tiene que valer en las dos direcciones.
2. **La promesa de la spec está cumplida.** Mi regla de escalada de la ronda
   anterior fue explícita: subo a exigido lo que la spec promete. La tabla de
   trazabilidad de R14 promete «test de que el despliegue no lo pisa», y ahora
   lo hay, con nueve modos de fallo cazados. No promete «ningún rol anónimo».
3. **No es la única capa.** T16 —abrir la URL sin sesión— está ejecutada, y un
   cambio de ese fichero pasaría por una feature con su review.

Va a §8 como deuda declarada con su arreglo escrito, no como cambio requerido.

### 1.4 Dónde vive el test, y el rastro

`services/postventa-front/tests/test_f010_config_swa.py`, nombres
`test_f010_r14_*`. Coincide con la convención de `CHECKPOINTS.md` C4
(`test_fXXX_rN_*`) y es lo que permite recorrer la trazabilidad de R14 por el
nombre, que es el mecanismo que falló en las tres rondas anteriores. **La
decisión de no meterlo en `test_f007_estaticos.py` es correcta y está
argumentada**: aquel fichero declara en su cabecera que de este JSON solo vigila
el marcador `<TENANT_ID>`. No hay aserciones duplicadas entre los dos.

**Ni red, ni BBDD, ni escritura**: el fichero solo hace `json.loads` de un
`read_text` y `copy.deepcopy` en memoria (`grep` de `requests|http|socket|
psycopg|urlopen`: **cero**).

---

## 2 · Punto 9.2 · ¿Dice la verdad, y sigue garantizando lo mismo?

Revisado sobre el diff de `72a1b80` y sobre los ficheros como quedan.

### 2.1 R29 · no se ha aflojado; se ha apretado

| | Antes | Ahora |
|---|---|---|
| Mecanismo | `verificar_archivo_dev.ps1 -BaseUrl <url del despliegue>` | Consola del front, con sesión, contra la **ruta relativa** `/api/archivar` |
| Garantía | «existe una forma de ejercitar la subida real» | **«solo desde el entorno desplegado y entrando por el front»** |
| URLs | Una URL de despliegue que alguien tiene que escribir | **«no haya ninguna URL que escribir»** |
| Formato | EARS (`CUANDO … debe …`) | EARS, intacto. `MANUAL (humano)`, intacto |

**La reescritura refuerza el requisito.** El «solo» es nuevo y explícito, y
encaja con la regla dura de `CLAUDE.md` («PROHIBIDO subir nada al SharePoint de
Posventa desde local»). R30 y R31 —resultado anotado, autorización C5, criterio
de parada ante un `(1)`— siguen intactos: **la subida real sigue siendo
irrepetible sin dejar rastro**.

Verificado además:

- La nota «por qué no por el nombre de host» explica el `400 Login not supported
  for provider azureStaticWebApps` y **no retira el script**, con el motivo
  (`el listado en solo lectura no depende del proxy`). Coherente con el defecto
  13, ya aprobado.
- `docs/DESPLIEGUE.md` **§5 bis existe** (línea 256) y el barrido de URLs sobre
  esa sección sale en **cero**. La spec apunta a un procedimiento que está y que
  no escribe ningún host.
- La fila de trazabilidad de R29 ahora **cita tests que existen y están
  verdes**: `test_f010_scripts_infra.py:1117, 1127, 1140, 1151`. Comprobado uno
  a uno. **No promete ningún test que no esté escrito** — que era el pecado de
  R14 en la ronda anterior.

### 2.2 `design.md` §6.4 · la fila movida

La fila de `infra/verificar_archivo_dev.ps1` sale de **§6.3 «Ficheros que NO se
tocan»** y entra en **§6.2 «A modificar»**, con el commit (`7ff86d7`), el motivo
y por qué el script se conserva. **Ninguna otra fila de las dos tablas ha
cambiado** (verificado en el diff: un `+` y un `-`).

Y una comprobación que el informe no hacía: §6.3 sigue diciendo que
`staticwebapp.config.json` **no se toca**, y eso **sigue siendo cierto** —
`git diff` de los cuatro commits de la ronda no lo incluye, y el fichero está
byte a byte como estaba. La fase RED del implementer, que lo rompió cinco veces
en el árbol, **no dejó residuo**.

---

## 3 · Punto 9.3 · Texto, no lógica

### 3.1 Verificado que el comportamiento no cambia

El bloque de ayuda de `infra/cargar_secretos_postventa.ps1` va de la **línea 2 a
la 66** (`<#` … `#>`). Filtrando el diff `26ef146..0743c45`, **todas** las
líneas cambiadas caen o dentro de ese bloque o son `Write-Host`:

- `:4` `.SYNOPSIS`, `:30` `.DESCRIPTION` (+ el párrafo nuevo «SON NUEVE, NO
  ONCE»), `:44` `.PARAMETER Solo` → **comentario**.
- `:281` y dos líneas nuevas → **`Write-Host`**, salida por consola. Ni una
  llamada a `az`, ni un código de salida, ni una condición.

**Ninguna ruta de ejecución tocada.** Y los punteros del texto nuevo son
ciertos, comprobados contra los ficheros:

- `$PostventaSecretosBackend` (`00_vars_postventa.ps1:103`) tiene **exactamente
  nueve** nombres; `$PostventaSecretosFront` (`:114`), dos; `$PostventaSecretos`
  es la suma. La partición existe tal y como el texto dice.
- `swa-client-id` y `swa-client-secret` los **crea y los guarda**
  `desplegar_front.ps1:453` y `:458`. Cierto.
- `docs/DESPLIEGUE.md` §2 existe (línea 30).
- El fichero sigue siendo **ASCII puro** (los tests lo leen con
  `encoding="ascii"`; lo he decodificado yo).

**Tests de contrato de `infra/`, ejecutados por mí**: la suite completa del
servicio `api` da **1092 passed, 13 skipped**, incluidos los que vigilan el
`-WhatIf` antes de la primera escritura y los códigos de salida —los que se
romperían si el texto añadido hubiera desplazado algo con significado—. Los dos
comentarios del test que arrastraban el «once» no cambian ninguna aserción, y
`test_f010_t3_declara_los_once_secretos_del_key_vault` **se queda con sus once**,
que es lo correcto: **once en el vault, nueve a mano**.

### 3.2 HALLAZGO · dos avisos de `ruff` nuevos que el informe da por previos

`progress/impl_postreview3_F-010.md` §3 dice: «El aviso de `ruff` es el mismo
número de la ronda anterior: **deuda previa**, no la toca esta ronda». **Medido:
no es así.**

```
ruff check .                                                    → 58
ruff check . --exclude .../tests/test_f010_config_swa.py        → 56
```

Los **dos** avisos que faltan son `ISC004` en el fichero nuevo, líneas **151** y
**162**: cadenas concatenadas implícitamente dentro de un `list` literal. El
arreglo es envolverlas en paréntesis. **No es un fallo funcional** —los mensajes
salen bien, los he visto en mis diez destrozos— y `init.sh` deja `ruff` en
`[AVISO]` no bloqueante, así que **no es un cambio requerido**. Pero la frase del
informe es falsa y queda corregida aquí: **esta ronda sube la deuda de `ruff` de
56 a 58**, y `ISC004` ya iba por 5 en el repositorio; ahora son 7.

---

## 4 · Barrido de identificadores (solo los commits nuevos)

Ejecutado por mí sobre `git log -p 5154563..HEAD` —los **cuatro** commits de
esta ronda—, sobre los parches, no sobre el árbol.

| Patrón | Resultado |
|---|---|
| GUID `8-4-4-4-12` | **0** |
| `azurewebsites.net`, `azurestaticapps.net`, `sharepoint.com`, `vault.azure.net`, `postgres.database.azure.com`, `azurecr.io`, `blob.core.windows.net` | **0** |
| Cualquier `http(s)://` | **0** |
| `subscriptionId`, `tenantId`, `/subscriptions/` | **0** |
| `client_secret`, `AccountKey=`, `Bearer `, `eyJ…`, `sk-…`, `AIza…` | **0** |
| IPv4 (cualquiera) | **0** |
| DNI (`8 dígitos + letra`) | **0** |
| Hex ≥ 24 · base64 ≥ 32 | **0** |
| Cookies de sesión, `password=`, `pwd=` | **0** |
| Ficheros **añadidos** en la ronda | **3**, los tres `.md`/`.py` de texto: los dos informes y el test |

**Limpio.** Ni un binario, ni un PDF, ni nada bajo `muestras/`. Y lo que sí se
escribe —`swa-client-id`, `pg-host`, `graph-tenant-id`— son **nombres de
secreto**, no valores: es exactamente lo que el repositorio lleva desde F-010 T3.

---

## 5 · C4 bis · el rigor declarado, verificado otra vez

`harness/features.json` declara **`rigor: "estandar"`**. Exige fase RED,
cobertura y campaña de mutación con supervivientes analizados; **no** exige cero
supervivientes ni el resultado real de las manuales (eso es `critico`).

### 5.1 Cobertura

`bash harness/init.sh`, tal cual, al abrir y al cerrar esta review:
`PUERTA COBERTURA [OK] 98.5% de 136 líneas cambiadas (134/136, umbral 80%)`.
**Exit code 0.**

El implementer explica —y tiene razón— que **esta ronda no mueve el número**: un
fichero de tests (fuera del alcance de producción) y un `.ps1` (no es Python).
Decirlo así es más honesto que presentar el 98.5 % como ganado hoy.

### 5.2 Recálculo puro: idéntico

`harness.alcance` + `harness.mutacion.generar_mutantes`, sin ejecutar la suite:

| Fichero | Líneas | Mutantes |
|---|---|---|
| `harness/mutacion.py` | 10 | 0 |
| `…/pipelines/paso_archivo.py` | 34 | 0 |
| `…/domain/models/errores.py` | 26 | 0 |
| `…/function_app.py` | 116 | **3** |
| `…/interface_adapters/api/archivar.py` | 11 | 0 |
| `…/postventa-front/dev_server.py` | 188 | 20 |
| **Total** | **385** | **23** |

**Coincide fichero a fichero con el informe.** No es campaña de cero mutantes,
así que no procede la prueba de control por exclusión de alcance.

### 5.3 Muestreo de supervivientes

Los tres declarados existen como mutantes reales, con **el mismo operador y el
mismo texto**: `dev_server.py:169`, `:171` y `:175`, operador `entero`,
`log.info("=" * 60)` → `log.info("=" * 61)`. Confirmado listando los mutantes
generados.

### 5.4 Reejecución completa (obligatoria: 118.2 s < 5 min)

```
python -m harness.mutacion --feature F-010 --workers 1 --salida <scratchpad>/mutacion_rev4_F-010.md
23 mutantes evaluados, 20 muertos, 3 supervivientes, 0 timeouts en 148.3 s
```

| Métrica | Informe | Mi reejecución |
|---|---|---|
| Mutantes | 23 | **23** |
| Muertos | 20 | **20** |
| Supervivientes | 3 | **3** |
| Timeouts | 0 | **0** |

**Idénticos**, y los tres supervivientes son los tres de siempre —los vi pasar
en pantalla, `[17]`, `[19]` y `[21]`—, luego **los tres mutantes de los códigos
de estado del defecto 14 murieron también en mi ejecución**. La salida fue al
scratchpad, **nunca a `progress/`**; `git status` queda como estaba y **la
campaña no dejó worktrees nuevos** (`git worktree list`: los mismos tres de
antes, ajenos a esta feature).

### 5.5 Coste por mutante · y por qué la fórmula de C4 bis engaña aquí

> coste = «Tiempo total» × workers ÷ mutantes

- Informe: 118.2 × 1 ÷ 23 = **5.14 s/mutante**
- Mi reejecución: 148.3 × 1 ÷ 23 = **6.45 s/mutante**

Leído a secas, eso está **muy por debajo** de la suite del `api` (28.18 s) y
C4 bis diría «sospechosa». **No lo es, y este es el cálculo que lo demuestra**:
en un monorepo cada mutante ejecuta **la suite de SU servicio**, y el reparto es
3 mutantes en `api` (28.18 s) y 20 en `front` (2.90 s):

> esperado = 3 × 28.18 + 20 × 2.90 = **142.6 s**

Mi reejecución midió **148.3 s**: un 4 % por encima de lo esperado. **La suite se
estaba ejecutando de verdad, mutante a mutante.** Los 118.2 s del informe quedan
un 17 % por debajo del esperado, dentro de la variación de máquina y con los
totales idénticos a los míos. Nada sospechoso.

Esto es un **defecto de `CHECKPOINTS.md`**, no del trabajo: la fórmula supone una
sola suite por repositorio. Propuesta P8 en §9.

### 5.6 Fase RED · cumplida, con una desviación de método que anoto

El entregable de 9.1 **es el propio test**, así que C4 bis manda demostrar la
fase RED «rompiendo deliberadamente —**en una copia aislada, nunca en el árbol
real**— lo que el test vigila». El implementer lo hizo **sobre el árbol real**,
restaurando con `git checkout --` tras cada caso, y lo argumenta: quería
demostrar que la guardia lee el fichero que se despliega.

- **El riesgo no se materializó**: el `staticwebapp.config.json` está intacto
  (§2.2), `git status` limpio y ningún destrozo llegó a un commit.
- **El argumento no se sostiene**: mi reproducción en copia aislada dio
  **exactamente los mismos fallos**. La copia bastaba.
- **No bloquea**: la casilla de C4 bis pide la traza real del fallo previo, y la
  traza está y es cierta. Lo dejo escrito para que no siente precedente.

### 5.7 «Evidencias»

Los dos informes de la ronda traen la sección con los cuatro números **y los
workers** (`--workers 1`, sin el cual no se puede calcular §5.5). Los he
recontado: **1194 tests** (arnés 17 + api 1092 + front 85), cobertura 98.5 %,
23 mutantes / 3 supervivientes, tiempos de suite. Ejecutadas por mí las tres
suites: `17 passed`, `1092 passed, 13 skipped`, `85 passed`. **Cuadran.**

---

## 6 · CHECKPOINTS.md, recorrido completo

### C1 — El arnés está completo y en verde

- **[x]** `bash harness/init.sh` termina en **exit code 0**, ejecutado tal cual
  al abrir y al cerrar. `PUERTA COBERTURA [OK] 98.5%`.
- **[x]** Existen los siete documentos exigidos.

### C2 — El estado es coherente

- **[x]** Una sola feature `in_progress`: F-010. Validado por `init.sh`.
- **[x]** Rama `feature/F-010-despliegue`.
- **[x]** `progress/current.md` describe la sesión activa, con la ronda de hoy
  al frente y fechada. Sigue llevando memoria apilada declarada como tal.
- **[x]** Las siete `done` tienen resumen en `history.md`.

### C3 — El código respeta arquitectura y convenciones

- **[x]** **Hexagonal**: esta ronda **no toca producción**. Un fichero de tests
  del front y un `.ps1` de `infra/`. Nada que cruzar entre capas.
- **[x]** Primera línea con la ruta relativa en el fichero nuevo
  (`# services/postventa-front/tests/test_f010_config_swa.py`).
- **[x]** Sin `print()` de debug, sin TODOs, **sin secretos**: lo único con
  forma de credencial son **nombres** de secreto (§4).
- **[x]** Sin dependencias nuevas: `copy`, `json`, `pathlib`, `pytest`.
- **[x]** Todo lo demás de C3 —unidad de trabajo, nada se archiva sin validar,
  manuscrito y firma, reprocesar no duplica, ningún estado de Sigrid
  hardcodeado— **sin cambios respecto a `review3_F-010.md`, donde se verificó**.
  Esta ronda no toca nada de eso.
- **[x]** **Ningún PDF ni dato personal en git**: barrido de la ronda en §4, y
  `git log --diff-filter=A` de los cuatro commits solo trae tres ficheros de
  texto.

*(Observación, no checkbox: los dos `ISC004` nuevos de §3.2. `ruff` es
`[AVISO]` en este arnés y la deuda previa es de 56.)*

### C3 bis — Documentos que entran de fuera

**N/A justificado**: la ronda no añade ni modifica nada bajo `docs/referencia/`
—los tres ficheros nuevos son dos informes de `progress/` y un test—. El barrido
de datos sensibles se ha ejecutado igualmente y consta en §4 con sus patrones.

### C4 — La verificación es real

- **[x]** **Cada requisito EARS tiene ≥ 1 test trazable.** **R14 ya lo tiene**:
  cuatro `test_f010_r14_*` + siete destrozos, **verificados en rojo por mí**
  (§1.2). Era el único hueco de la ronda anterior y **queda cerrado**. R29
  suma además los cuatro tests de contrato `defecto13`, que existen y pasan.
- **[x]** Los unit tests no tocan red ni BBDD. El fichero nuevo solo lee un JSON
  del disco y trabaja en memoria (§1.4).
- **[x]** Las verificaciones `MANUAL (humano)` están listadas con su comando
  exacto. **Diez de once traen además su resultado real**; **T14 bis** está
  listada y declarada sin resultado, que en nivel `estandar` **no bloquea**
  (razonado en `review3_F-010.md` §7 y ratificado aquí).

### C4 bis — El rigor declarado se cumple

- **[x]** `rigor: "estandar"`, valor válido.
- **[x]** **Fase RED** con salida real pegada, y **reproducida por mí** en copia
  aislada (§1.2). Desviación de método anotada en §5.6.
- **[x]** **Cobertura** `[OK]` 98.5 % de 136 líneas, umbral 80 %.
- **[x]** **Mutación** con alcance y nº de mutantes **recalculados por mí** y
  coincidentes fichero a fichero (§5.2), y supervivientes **muestreados** con su
  operador y su texto (§5.3).
- **[x]** **Los muertos están comprobados**: campaña **reejecutada entera**
  (118.2 s < 5 min), totales idénticos, salida fuera de `progress/`, árbol limpio
  y sin worktrees nuevos (§5.4).
- **[x]** **La campaña tardó lo que tenía que tardar**: 148.3 s medidos contra
  142.6 s esperados por el reparto real de suites (§5.5).
- **[x]** Los tres supervivientes con análisis **completado**, ninguno en
  `PENDIENTE`. Nivel `estandar`: los acepto como equivalentes —es el ancho de un
  separador decorativo en un servidor de desarrollo que además no se despliega—.
- **[x]** Sección **«Evidencias»** con los cuatro números y los workers (§5.7).
- **[x]** Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A justificado**: `harness/rutas_sensibles.json` **no existe** en este
repositorio, que es el caso mayoritario que el propio bloque contempla y para el
que dice expresamente que no hay nada que justificar. Su declaración completa es
**F-015**.

### C5 — La sesión se cerró bien

- **[x]** **`tasks.md` con TODAS las tareas `[x]`**: 22 marcadas, **0 vacías**.
  **Ninguna casilla se ha movido en esta ronda** (los cuatro commits no tocan
  ningún `tasks.md`), que es lo correcto: esto eran correcciones de review, no
  tareas nuevas.
- **[x]** Un commit por unidad de trabajo, con prefijo `F-010`: los cuatro de la
  ronda lo llevan (`F-010 9.1:`, `F-010 9.3:`, `F-010 review3 9.2:`, `F-010:`).
- **[x]** **Sin artefactos temporales ni sospechosos sin trackear.** `git status`
  muestra **un solo** fichero: `?? progress/review3_F-010.md`, **mi propio
  informe de la ronda anterior**, que ningún subagente debe commitear y que el
  líder tiene que versionar —como ya hizo con el de la re-review en `ec4b4b0`—.
  Lo mismo valdrá para este. **Acción mecánica del líder, apuntada en §8.**
- **[x]** `features.json` refleja el estado real: F-010 sigue `in_progress`.
  Ningún agente se ha marcado `done` a sí mismo.

---

## 7 · Trazabilidad · solo el delta de esta ronda

La tabla completa de las tres rondas anteriores sigue vigente.

| R | Enunciado corto | Test |
|---|---|---|
| **R14** | Sin sesión, la SWA redirige al login | **`test_f010_config_swa.py:217, 224, 231, 238`** + 7 destrozos `:317`. **MANUAL T16** ejecutada. *(Era el «SIN TEST» de la ronda anterior.)* |
| **R29** | T18 solo desde el entorno desplegado, por la consola del front | **MANUAL T18** ejecutada + contrato `test_f010_scripts_infra.py:1117, 1127, 1140, 1151` |
| R35 | Tope de gasto con alerta | **MANUAL T14 bis** — sin resultado, no bloquea |

---

## 8 · Lo que queda vivo al cerrar

Para que el líder lo anote tal cual. **Ninguno de los cuatro bloquea el `done`.**

1. **T14 bis sin resultado.** El tope de gasto con alerta (R35) sigue sin
   «tope fijado: sí/no» ni «alerta configurada: sí/no». **Dictaminado en
   `review3_F-010.md` §7 y ratificado aquí: no bloquea** —el nivel `estandar` no
   exige el resultado real de las manuales, y el dato lo tiene el humano en la
   consola de un proveedor externo—. **Deuda declarada, con dueño (el humano) y
   consecuencia concreta**: `/api/extraer` y `/api/firma` son anónimos y ya son
   alcanzables; mientras el tope no esté puesto, un desconocido puede consumir
   cuota de IA y la única señal será la factura. **Que no bloquee no significa
   que pueda esperar: son cinco minutos de consola.**
2. **F-019 es prerequisito del archivado real** (defecto 15). Hoy
   `/api/archivar` **no puede completar solo**: nada inserta el parte en
   `partes`, y por eso T18 exigió sembrarlo a mano. Está anotado en la ficha de
   F-019 de `harness/features.json` con el `ForeignKeyViolation` como prueba, la
   fecha y el aviso de comprobar el orden al implementarla, y explicado en
   `docs/DESPLIEGUE.md` §5 ter. **Correctamente fuera de F-010.**
3. **El hueco del comodín (§1.3), hallazgo mío de hoy.** `/*` con
   `["anonymous", "authenticated"]` deja la aplicación abierta a internet y la
   suite sigue verde. **Una línea** en `problemas_del_cierre` de
   `services/postventa-front/tests/test_f010_config_swa.py:137` y un caso más en
   la parametrización de `:296`; conviene extenderlo a `/api/*`. **No es
   condición del `done`** (§1.3), pero es más barato hacerlo ahora que abrir una
   feature para ello.
4. **Dos avisos `ISC004` nuevos** en ese mismo fichero, líneas 151 y 162, y la
   frase del informe que los da por deuda previa (§3.2). Cosmético.

**Acción mecánica antes de cerrar**: versionar `progress/review3_F-010.md` y
este `progress/review4_F-010.md`. Un informe de review fuera de git es un agujero
en el rastro documental de la feature, y ya se corrigió una vez (`ec4b4b0`).

### 8 bis · Dos observaciones menores, sin acción exigida

- **`design.md` §6.1 no lista el test nuevo.** La tabla «A crear» quedó escrita
  en `72a1b80`, **antes** de que existiera `test_f010_config_swa.py` (`26ef146`).
  No es una falsedad —§6.3 sigue diciendo la verdad sobre
  `staticwebapp.config.json`, que no se ha tocado—, es una omisión de una fila.
  No la exijo: el fichero nació de un mandato de review, documentado en
  `progress/`, y su rastro se sigue por el nombre `test_f010_r14_*`.
- Siguen vivas las dos observaciones de `review3_F-010.md` §10 bis: el bloque de
  T18 en `specs/F-006-sharepoint/tasks.md` no dice que el `200` exigió sembrar el
  parte a mano, y **no consta qué pasó con el PDF sintético** que quedó en la
  biblioteca real. La segunda vale la pena decidirla y dejarla escrita.

---

## 9 · Propuestas de mejora del protocolo (NO aplicadas)

Para que las apruebe o las descarte el humano. Si se aceptan y son genéricas,
viajan a `arnes-base` en el mismo trabajo. **P5, P6 y P7 de `review3_F-010.md`
siguen en la cola sin resolver.**

**P8 · El coste por mutante de C4 bis está mal calculado en un monorepo.** La
regla dice que el coste por mutante «no puede bajar de lo que tarda esa suite»,
suponiendo **una** suite. Con `harness/servicios.json` declarando varios
servicios, cada mutante ejecuta la suite **de su servicio**, y una campaña
perfectamente sana da un coste medio muy por debajo de la suite más lenta —aquí,
6.45 s contra 28.18 s—. Un reviewer que aplicara la regla al pie de la letra
**rechazaría una campaña buena**. Propongo sustituir el umbral por el reparto:

> esperado ≈ Σ (mutantes del servicio × tiempo de su suite) ÷ workers
>
> El coste sospechoso es el que baja **muy por debajo de ese esperado**, no el
> que baja de la suite más lenta. Con un solo servicio la fórmula se reduce a la
> actual.

Es genérica, la necesita cualquier monorepo, y es la que me ha permitido
verificar hoy que la campaña se ejecutaba de verdad.

**P9 · Un test de contrato debe demostrar también el fallo que NO caza.** El
hueco de §1.3 sobrevivió a una fase RED de cinco casos porque **todos los casos
los eligió quien escribió la guardia**, y a nadie se le ocurre el destrozo que su
propia guardia no ve. Propongo añadir al protocolo del `reviewer`:

> Cuando la fase RED se demuestre rompiendo lo que el test vigila, el reviewer
> **añade destrozos propios** que el implementer no haya escrito, y deja
> constancia de cuáles eran suyos y de cuáles quedaron en verde.

Es lo que he hecho hoy —cinco de los diez casos son míos— y es lo único que ha
destapado el hueco. Barato y genérico.

---

## 10 · Resumen

| Bloque | Estado |
|---|---|
| C1 · Arnés en verde | **[x]** |
| C2 · Estado coherente | **[x]** |
| C3 · Arquitectura y convenciones | **[x]** |
| C3 bis · Documentos de fuera | **N/A justificado** (no toca `docs/referencia/`) |
| C4 · Verificación real | **[x]** — **R14 ya tiene su test, y vigila** |
| C4 bis · Rigor `estandar` | **[x]** — mutación reejecutada y verificada |
| C4 ter · Rutas sensibles | **N/A justificado** (no existe la declaración) |
| C5 · Sesión cerrada | **[x]** — 22/22 casillas, ninguna movida hoy |

**Veredicto: APPROVED. F-010 pasa a `done`** cuando el líder versione los dos
informes de review y actualice `harness/features.json` y `progress/history.md`.

Y que quede dicho al cerrar cuatro rondas: el rechazo anterior valía **un test y
cuatro líneas de Markdown**, y las cuatro líneas de Markdown eran las que
mentían. Se han corregido **sin aflojar el requisito** —R29 hoy garantiza más
que antes— y el test no solo existe: **aguanta nueve destrozos de diez, cinco de
ellos pensados por mí para pillarlo**. El único que no aguanta está escrito
arriba con su arreglo de una línea, para que quien lo lea mañana no tenga que
descubrirlo dos veces.
