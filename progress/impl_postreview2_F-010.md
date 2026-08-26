<!-- progress/impl_postreview2_F-010.md -->
# F-010 · ronda de correcciones tras la re-review (`review2_F-010.md`)

- **Rama:** `feature/F-010-despliegue`
- **Fecha:** 2026-08-25
- **Alcance:** **solo documentación**. Ni una línea de código de servicio, ni
  un test nuevo, ni un script de `infra/` tocado, ni una casilla `[x]` de
  `specs/F-010-despliegue/tasks.md` movida.
- **Origen:** `progress/review2_F-010.md` §10, puntos 1, 2, 3 y 4, más una
  quinta corrección aportada por el líder (las rutas `$HOME` que no
  funcionan; es el **defecto 1** de la jornada del 2026-08-21, que seguía
  vivo en los enunciados).
- **Fuera de alcance por encargo:** §10.5 (resultado real de T14 bis) y
  §10.6 (resultado de T19) —los aporta el humano—, y el test recomendado
  del §9.1 sobre `staticwebapp.config.json` —opcional y no aprobado—.

> Este informe se escribe **de forma incremental**, sección a sección, según
> se van cerrando los commits. Es deliberado: este repositorio ya ha perdido
> trabajo por escribir el informe al final.

---

## 0 · Portero de entrada

`bash harness/init.sh`, tal cual, sin pipes, antes de tocar nada:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido / BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea)
17 passed in 0.60s  → [OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116,
     umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-010-despliegue
ENTORNO LISTO. Puedes trabajar.
```

---

## 1 · Los hechos que sostienen las correcciones (verificados en el árbol)

Antes de escribir nada en los documentos, comprobé en el código lo que la
review afirma. **No me fié del informe: fui a los ficheros.**

### 1.1 · Nueve secretos, no once

`infra/00_vars_postventa.ps1:103-118` ya lo dice con sus propios nombres de
variable, y esa es la prueba más limpia:

| Variable | Secretos |
|---|---|
| `$PostventaSecretosBackend` | `pg-host`, `pg-user`, `pg-password`, `gemini-api-key`, `graph-tenant-id`, `graph-client-id`, `graph-client-secret`, `sharepoint-site-id`, `sharepoint-drive-id` → **nueve** |
| `$PostventaSecretosFront` | `swa-client-id`, `swa-client-secret` → **dos** |

Y los dos del front **no se teclean**: los escribe el despliegue del front,
`infra/desplegar_front.ps1:453` y `:458`, con `az keyvault secret set`,
después de crear el registro de aplicación y sacarle el secreto. Quien los
teclee a mano estará inventando dos valores que el propio despliegue
sobrescribe.

### 1.2 · Qué scripts pueden ejecutarse desde `$HOME` y cuáles no

Este es el punto 5 y lo comprobé **script por script**, que es lo que pedía
el encargo, en vez de aplicar una regla a bulto:

| Script | Depende de `$raiz` | ¿Funciona en `$HOME`? |
|---|---|---|
| `00_vars_postventa.ps1` | no (solo `$PSScriptRoot` para su `.local.ps1`) | no se ejecuta suelto |
| `cargar_secretos_postventa.ps1` | **no** — solo `. "$PSScriptRoot\00_vars_postventa.ps1"` (`:64`) | **sí**, con `00_vars` al lado |
| `verificar_despliegue.ps1` | **no** — carga `00_vars` (`:70`); sus `$raizApi`/`$raizFront` (`:224-225`) son las **URL** que recibe por parámetro, no la raíz del repo | **sí**, con `00_vars` al lado |
| `verificar_archivo_dev.ps1` | **no** — ni siquiera carga `00_vars`: es autónomo y todo le llega por parámetro | **sí** |
| `desplegar_backend.ps1` | **SÍ** — `$raiz = Split-Path -Parent $PSScriptRoot` (`:98`), `$origenApi = ...\services\postventa-api` (`:99`) | **no** |
| `desplegar_front.ps1` | **SÍ** — `$raiz` (`:135`), `$origenFront = ...\services\postventa-front` (`:136`) | **no** |

El mecanismo del fallo, escrito para que no haya que deducirlo: copiado a
`C:\Users\pgris\`, `$PSScriptRoot` vale `C:\Users\pgris` y `Split-Path
-Parent` da **`C:\Users`**; ahí no hay ningún `services\`.

(Fuera del alcance de F-010, con el mismo defecto y por si alguien los copia:
`crear_base_postventa.ps1:52` y `pruebas_bbdd_efimera.ps1:45`.)

**Conclusión aplicada:** los dos despliegues se ejecutan **desde `infra\`**;
los tres de secretos y verificación siguen valiendo desde `$HOME`, y **no se
tocan** —el encargo pedía explícitamente no cambiar lo que ya es correcto—.

---

## 2 · Corrección 1 · «once secretos» → nueve, con el porqué (`e0c85c8`)

**Review §10.1.** Dos afirmaciones falsas en `docs/DESPLIEGUE.md`:

| Dónde | Antes | Ahora |
|---|---|---|
| §2, tabla de scripts | «sube **los once** secretos pedidos a ciegas» | «sube los **nueve** secretos del backend, pedidos a ciegas» |
| §3, prerrequisito 2 | «**Las once credenciales** a mano» | «Las **nueve** credenciales del backend a mano», con los nueve nombres listados |

Y, porque corregir el número sin decir el motivo deja el mismo error a un
paso de volver, dos añadidos:

- **§2, apartado nuevo «Son nueve secretos, no once, y el porqué importa»**:
  el vault acaba con once, pero los dos del front los genera y los guarda
  `desplegar_front.ps1` al crear el registro de aplicación; cuando corre
  `cargar_secretos_postventa.ps1` **todavía no existen**, y lo que se teclee
  lo sobrescribe el despliegue del front. Con el puntero a
  `$PostventaSecretosBackend` / `$PostventaSecretosFront`, que es donde la
  partición ya estaba escrita.
- **§3, prerrequisito 2**: la frase explícita de que `swa-client-id` y
  `swa-client-secret` **NO se preparan**.

Anotada la fecha del incidente (2026-08-21) en la nota de §2: quien lea el
runbook ve que no es una precaución teórica.

---

## 3 · Corrección 2 · el rol `Key Vault Secrets Officer` (`5796c5d`)

**Review §10.2.** Faltaba en `docs/DESPLIEGUE.md` §3 el prerrequisito que
**paró la primera ejecución real** (defecto 4 de la jornada): crear el Key
Vault **no** da permiso sobre sus secretos.

Añadido como **prerrequisito 3** (el tope de gasto pasa a ser el 4), con:

- **el mecanismo, no solo la orden**: el vault usa RBAC, y ser Owner del
  grupo de recursos —o haberlo creado uno mismo— deja gestionar el recurso
  pero no escribir dentro;
- **el síntoma exacto**, que es lo que permite reconocerlo sin volver a
  perder la tarde: el script crea el vault sin problemas y muere en el
  **primer** secreto con un `Forbidden`;
- **los dos `az`**: uno para comprobar si el rol ya está (`role assignment
  list`) y otro para concederlo, ambos con **marcadores** `<tu-cuenta>` y
  `<id-del-key-vault>`, sin un solo identificador real;
- **el aviso de propagación**: la asignación tarda, y el script es
  re-ejecutable, así que la salida correcta es esperar y volver a lanzarlo,
  no buscar otro problema.

---

## 4 · Corrección 3 · el aviso de `-Solo` con `-File` (`aef06f6`)

**Review §10.3.** El runbook anunciaba `-Solo <nombre>` como la vía de
rotación sin decir que **no funciona como se invoca en el propio runbook**.

Añadido el apartado **«Rotar una credencial: `-Solo` no funciona con
`powershell -File`»** en §2, y un puntero desde la celda de la tabla que lo
anuncia, para que no dependa de que alguien siga leyendo.

Lo que dice, y en este orden porque es el orden en que se sufre:

1. **El síntoma**, literal: `Estos secretos no existen: ...`.
2. **Que ese mensaje miente** —no es el error real— y manda a buscar el
   problema donde no está. Esto es lo que costó tiempo el 2026-08-21.
3. **La causa**: con `-File` los argumentos llegan como una sola cadena y
   `-Solo` no construye el array `[string[]]` que el script declara.
4. **Las dos vías que sí funcionan**: desde la sesión
   (`.\infra\cargar_secretos_postventa.ps1 -Solo <nombre>`) o con `-Command`.
5. **El límite del aviso**: la ejecución **completa**, sin `-Solo`, sí vale
   con `-File`, que es como la documentan T13 y el resto del runbook. Sin
   esta frase el aviso invalidaría de más.

---

## 5 · Corrección 4 · la verificación de T13, rectificada (`c1cd8a6`)

**Review §10.4 / §7.1.** T13 estaba `[x]` contra un criterio que su propia
ejecución demostró **imposible**: «once secretos cargados: sí/no», cuando
solo se pueden cargar nueve.

`specs/F-010-despliegue/tasks.md`, apartado **Verificación** de T13, siguiendo
el precedente de **T8 y T19 de `specs/F-006-sharepoint/tasks.md`**:

- el criterio viejo queda **tachado** (`~~…~~`), no borrado: quien vuelva a
  la tarea ve qué decía y por qué cambió;
- el criterio nuevo va con **fecha y motivo** —«RECTIFICADA EL 2026-08-25,
  tras ejecutarla»— y dice «**nueve** secretos cargados: sí/no»;
- debajo, el porqué completo: los dos que faltan los crea
  `desplegar_front.ps1` en T16, aquí todavía no existen, y teclearlos es
  inventar valores que el despliegue sobrescribe;
- punteros a `infra/00_vars_postventa.ps1` y a `docs/DESPLIEGUE.md` §2, para
  que las tres fuentes digan lo mismo;
- la referencia explícita a que es el **defecto 2** de los doce.

**La casilla `[x]` no se ha tocado**, y está dicho en el propio texto: la
tarea se ejecutó de verdad y su resultado anotado —«9 de 11 cargados»— era el
correcto; lo que estaba mal era el enunciado. Las marcas son del humano.

---

## 6 · Corrección 5 · las rutas `$HOME` que no funcionan (`b6b4ace`)

**No está en el §10 del reviewer**: lo aporta el líder. Es el **defecto 1** de
los doce del 2026-08-21 —«la ruta `$HOME\...` de T13 y T14 es falsa»—, que se
sufrió, se anotó y **siguió vivo en los enunciados**. Justo el patrón que la
review denuncia en su §5: la lección no volvió al documento que la previene.

El inventario script por script está en el §1.2 de este informe. Resumen: los
**dos despliegues** dependen de `$raiz` y **no pueden ejecutarse desde
`$HOME`**; los otros tres, sí, y **no se han tocado**.

### `docs/DESPLIEGUE.md` §2

- **Columna nueva en la tabla**: «Desde dónde se ejecuta» —`$HOME` o `infra\`
  para el 1 y el 4, **`infra\` obligatorio** para el 2 y el 3—. Así la
  respuesta está donde primero se mira.
- **Apartado nuevo con el mecanismo**, no solo la regla: `$raiz = Split-Path
  -Parent $PSScriptRoot`; desde `C:\Users\pgris` eso da `C:\Users`, donde no
  hay `services\`.
- **El `copy infra\*.ps1 $HOME\` desaparece** y lo sustituyen las tres líneas
  de los scripts que sí funcionan fuera. Un `*.ps1` invita exactamente al
  error que costó la parada.
- **Contestada la objeción evidente** —«se copiaban fuera para no ensuciar el
  árbol»—: ejecutar desde `infra\` no lo ensucia, porque
  `desplegar_front.ps1:500` hace su copia de trabajo en el temporal del
  sistema y la borra en un `finally` (`:593`). Comprobado en el script, no
  supuesto.

### `specs/F-010-despliegue/tasks.md`

- **Nota de cabecera de la fase 4**: rectificada con el mismo formato que T13
  —tachado, fecha, motivo—, con el porqué y con el `copy` correcto.
- **T14, T16 y T17**: `$HOME\desplegar_*.ps1` → `.\infra\desplegar_*.ps1`,
  cada una con una línea que dice por qué («busca `services\...` relativo a su
  propia ubicación»), para que no se pierda si alguien copia solo el bloque.
- **T13 y T18 intactas**: sus `$HOME\cargar_secretos_postventa.ps1` y
  `$HOME\verificar_archivo_dev.ps1` **son correctos**. Igual que
  `docs/DESPLIEGUE.md` §5, que invoca `verificar_despliegue.ps1` desde
  `$HOME`. El encargo pedía no cambiar lo que ya funciona, y no se ha
  cambiado.

**Ninguna casilla `[x]` movida**, verificado con
`git diff -U0 specs/F-010-despliegue/tasks.md | grep -E '^[-+].*\[[ x]\]'` →
**sin resultados**.

---

## 7 · Lo que NO se ha hecho, y por qué

Dicho explícitamente para que el reviewer no tenga que deducirlo:

| No hecho | Motivo |
|---|---|
| **§10.5** · resultado real de T14 bis (tope y alerta de gasto) | Lo tiene que aportar **el humano**. El implementer no puede inventarlo, y el encargo lo declara fuera de alcance |
| **§10.6** · marcar T19 `[x]` y anotar su resultado | Ídem: las casillas son del humano. Sigue en `[ ]` |
| **§9.1** · test sobre `staticwebapp.config.json` | Recomendado, **no exigido**, y el humano no lo ha aprobado. Fuera de alcance por encargo |
| **§9.2** · entrecomillar `--value=$claro` en `cargar_secretos_postventa.ps1` | Es un script de `infra/`, y el alcance prohíbe tocarlos. Además el propio reviewer dice que **hay que verificarlo contra Azure**, cosa que no puede hacerse desde aquí |
| Cualquier llamada a Azure o a SharePoint | Prohibida por el encargo. **No se ha hecho ninguna** |

## 8 · Residuos detectados y NO tocados (para el líder)

Los encontré haciendo estas cinco correcciones. **No los he corregido**
porque caen fuera del alcance, y los dejo escritos para que la decisión sea
del humano y no se pierdan:

1. **`infra/cargar_secretos_postventa.ps1` sigue diciendo «once secretos»**
   en su `.SYNOPSIS` (`:4`, `:30`) y, lo que más pesa, **en la última línea
   que imprime** (`:269`): «Anota en progress/ solo esto: 'once secretos
   cargados: si/no'». Es decir: el runbook y `tasks.md` ya dicen nueve, y **el
   script en pantalla sigue pidiendo once**. Es exactamente la contradicción
   que acabo de cerrar en los documentos, viva en el sitio que el operador
   tiene delante. **Tocar `infra/` está prohibido en este encargo**, así que
   lo reporto: es un cambio de dos cadenas y de cero riesgo funcional, pero
   necesita permiso.
2. **`specs/F-010-despliegue/tasks.md:94` (T4) y `design.md:222`** también
   dicen «los once secretos». Ahí es **defendible**: describen lo que el vault
   acaba conteniendo, no lo que se teclea. Aun así, después de esta ronda son
   las dos únicas menciones a «once» sin matiz en `specs/`.
3. **El mismo defecto de `$raiz` fuera de F-010**:
   `infra/crear_base_postventa.ps1:52` y `infra/pruebas_bbdd_efimera.ps1:45`
   deducen la raíz igual. Hoy nadie documenta copiarlos a `$HOME`, así que no
   ha mordido, pero muerden igual si alguien lo hace.
4. **§9.3 del reviewer, el «13 saltados»**: el reviewer lo dio por desliz de
   transcripción del implementer y dijo que la suite da **3 saltados**. **La
   suite completa da 13** (medido dos veces hoy, ver §9). Los 3 salen al
   filtrar. **El número del implementer era el correcto**; lo anoto porque la
   observación del reviewer se queda sin objeto.

## 9 · Evidencias

Números **reales, medidos hoy**, no estimados.

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados** · suite raíz del arnés | **17 pasados**, 0,72 s | `bash harness/init.sh` |
| **Tests ejecutados** · suite `api` completa | **1.079 pasados, 13 saltados**, 34,37 s | `.venv/Scripts/python.exe -m pytest -q` en `services/postventa-api` |
| **Tests ejecutados** · suite `front` completa | **74 pasados**, 2,78 s | `python -m pytest -q` en `services/postventa-front` |
| **Tests que leen los documentos tocados** | **165 pasados, 3 saltados**, 6,04 s | `pytest tests/test_f010_tarjeta_portal.py tests/test_f010_scripts_infra.py tests/test_f006_repo_sin_identificadores.py` — son los que leen `docs/DESPLIEGUE.md` y barren identificadores |
| **Cobertura de las líneas cambiadas** | **98,3 %** (114/116, umbral 80 %, nivel `estandar`) | línea `PUERTA COBERTURA` de `init.sh`. **Idéntica a la de antes de esta ronda**: esta ronda no cambia ni una línea de producción, así que el alcance de cobertura no se mueve |
| **Mutantes generados y supervivientes** | **20 mutantes, 17 muertos, 3 supervivientes** — los de `progress/mutacion_F-010.md`, **sin cambios** | **Campaña NO relanzada, y es lo correcto**: la mutación muta líneas de producción, y esta ronda toca **dos `.md` y nada más**. El alcance de mutación de F-010 (`harness/mutacion.py`, `function_app.py`, `dev_server.py`) está **intacto**. Relanzarla habría dado el mismo resultado gastando la ejecución. Los tres supervivientes siguen **analizados y no `PENDIENTE`**: mutantes equivalentes, el ancho de un separador decorativo |
| **Tiempo de ejecución de la suite** | 0,72 s (arnés) + 34,37 s (api) + 2,78 s (front) | las propias suites |

**Fase RED: N/A justificado.** El nivel `estandar` la exige sobre los
requisitos centrales **que se implementan**. Esta ronda **no implementa
ningún requisito**: corrige cuatro afirmaciones falsas en `docs/DESPLIEGUE.md`
y dos enunciados de tareas ya ejecutadas. No hay código nuevo que pueda
fallar primero, ni test nuevo que escribir —el encargo prohíbe añadirlo—. Las
trazas RED de los cuatro arreglos de código de la ronda anterior siguen en
`progress/impl_F-010.md` y el reviewer las validó (§1 de `review2_F-010.md`).

**Barrido de identificadores, hecho sobre las 170 líneas añadidas**
(`git diff 9f81db0..HEAD -- docs specs | grep '^+'`), con los patrones del §4
de la review:

| Patrón | Hallazgos |
|---|---|
| GUID canónico | **0** |
| `azurewebsites.net`, `azurestaticapps.net`, `vault.azure.net`, `blob.core.windows.net`, `azurecr.io`, `sharepoint.com`, cualquier `http(s)://` | **0** |
| `AccountKey=`, `client_secret`, `eyJ…`, `sk-…`, `AIza…` | **0** |
| IPv4 | **0** |
| Importes | **0** |

Los dos `az` nuevos del prerrequisito 3 van con marcadores `<tu-cuenta>` y
`<id-del-key-vault>`.

> **Proyecto Python**: mutación y cobertura de líneas cambiadas **sí** están
> disponibles; lo que no aplica aquí es su **relanzamiento**, por el motivo
> escrito en la tabla.

## 10 · Cierre

- **Cinco commits, uno por corrección**, en este orden:

  | Commit | Corrección |
  |---|---|
  | `e0c85c8` | 1 · «once secretos» → nueve, con el porqué |
  | `5796c5d` | 2 · el rol `Key Vault Secrets Officer` en prerrequisitos |
  | `aef06f6` | 3 · `-Solo` no funciona con `powershell -File` |
  | `c1cd8a6` | 4 · rectificada la verificación de T13 |
  | `b6b4ace` | 5 · las rutas `$HOME` que no funcionan (defecto 1) |

- **Dos ficheros tocados**, los dos Markdown: `docs/DESPLIEGUE.md` y
  `specs/F-010-despliegue/tasks.md`. Ni un `.py`, ni un `.ps1`, ni un `.json`,
  ni un test.
- **Ninguna casilla `[x]` movida** (comprobado con `git diff -U0` filtrando
  las líneas de casilla: sin resultados).
- **Ninguna llamada a Azure ni a SharePoint.**
- `bash harness/init.sh` **en verde**, ejecutado tal cual y sin pipes, al
  terminar. Salida idéntica a la del §0.
- `git status` limpio salvo este informe.

**Lo que falta para que F-010 pueda cerrarse** (nada de ello es del
implementer): los §10.5 y §10.6 de la review —resultado de T14 bis y de
T19— y las tres manuales abiertas T15, T17 y T18, esta última con la
autorización expresa que nombra `CHECKPOINTS.md` C5.

---

## 11 · Adenda · `progress/current.md` y estado final del árbol

- **`progress/current.md` actualizado** con un bloque al frente («Estado al
  2026-08-25 (tarde)»): las cinco correcciones, el residuo reportado sin
  corregir y lo que falta del humano. Commit `0e4dd54`.
- **`bash harness/init.sh` en verde** después de todo, tal cual y sin pipes.
  Salida idéntica a la del §0.
- **`git status`**: limpio salvo `progress/review2_F-010.md`, que está **sin
  seguir por git**. Es el informe del **reviewer**, no mío: **no lo commiteo**,
  lo decide el líder.
