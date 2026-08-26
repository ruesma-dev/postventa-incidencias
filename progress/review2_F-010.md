<!-- progress/review2_F-010.md -->
# Re-review F-010 · el trabajo posterior al despliegue real

- **Rama:** `feature/F-010-despliegue`
- **Rango revisado:** `084f56e..HEAD` (`9f81db0`) — 14 commits, 12 ficheros,
  971 inserciones. Es el trabajo que **no** había pasado por review.
- **Review anterior:** `progress/review_F-010.md` (APROBADO el 2026-08-20 en
  su §14, a la espera de las nueve tareas `MANUAL (humano)`).
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`.
  Puertas exigibles: fase RED en los requisitos centrales, `PUERTA COBERTURA`
  en `[OK]`, campaña de mutación con **todos** los supervivientes analizados
  (cero supervivientes solo lo exige `critico`), y sección «Evidencias».
- **Veredicto:** **CHANGES_REQUESTED**, y conviene leer el §9 antes que la
  etiqueta: **los tres defectos del encargo (8, 9 y 11) están bien corregidos
  y bien atados, y no pido tocar ni una línea de ellos**. Lo que bloquea es
  otra cosa: **la jornada del 2026-08-21 costó doce defectos y el documento
  que existe para que no vuelvan a costarse —`docs/DESPLIEGUE.md`— no recogió
  ninguno, y hoy afirma como prerrequisito algo que ese mismo despliegue
  demostró falso** (§5), más tres huecos de la condición de cierre nº 1 (§7).

---

## 0 · Portero

`bash harness/init.sh`, ejecutado por el reviewer, tal cual y sin decoración:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido / BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea)
17 passed in 0.81s  → [OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 98.3% de 116 líneas cambiadas cubiertas (114/116,
     umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-010-despliegue
ENTORNO LISTO. Puedes trabajar.
```

Suites relanzadas por mí, sin fiarme de la caché de árbol:

| Comprobación | Resultado |
|---|---|
| Suite raíz del arnés | **17 pasados**, 0,81 s |
| Suite `api` | **1.079 pasados, 3 saltados**, 22,0 s |
| Suite `front` (Python) | **74 pasados**, 1,81 s |
| Tests de F-010 (`-k f010`) | **155 pasados, 3 saltados**, 3,03 s |
| `ruff` sobre los dos ficheros de test tocados | `All checks passed!` |
| `git status` | **limpio** |
| `git log --all --diff-filter=A` sobre PDF/ofimática | **ni un fichero** |

---

## 1 · Los tres defectos del encargo · VERIFICADOS UNO A UNO

El encargo pedía comprobar que están **corregidos de verdad y con test que los
ate**, no solo commiteados. Los tres lo están.

### Defecto 8 · el resumen dice el modo real (`457791f`)

**Corregido.** `infra/desplegar_front.ps1:548` ya no deduce el modo de que el
recuento venga vacío:

```powershell
Write-Host ("  Credenciales 'swa' : {0}" -f $(if ($SoloFront) { "sin tocar (-SoloFront)" } elseif ($credencialesSwa) { "REGENERADA; {0} viva(s)" -f $credencialesSwa } else { "REGENERADA; no se ha podido contar cuantas quedan vivas" }))
```

**El test tiene dientes**, y es el detalle que lo hace valer:
`test_f010_r32_el_resumen_solo_alega_solofront_cuando_lo_esta` no comprueba que
la línea correcta exista —eso lo pasaría cualquier reescritura—, sino que
**ninguna línea del script pueda imprimir «sin tocar (-SoloFront)» sin mirar
`$SoloFront`**. Es una regla sobre el fichero entero, no sobre una línea, así
que también caza la próxima línea de resumen que alguien añada con el mismo
pecado. Es la forma correcta de escribir este test.

### Defecto 9 · `User.Read` y consentimiento (`885a061`)

**Corregido**, y con los tres matices bien resueltos:

- **delegado, no de aplicación**: `--api-permissions "$permisoUserRead=Scope"`;
- **re-ejecutable (R2)**: solo concede si `az ad app permission list` no lo
  trae ya;
- **`permission add` aborta** con su «Qué hacer»; el **consentimiento va en
  mejor esfuerzo** y no tira el despliegue, igual que en `partes` y
  `dedicacion`, **pero no se lo calla**: el resumen distingue
  `con consentimiento de administrador` de `CONSENTIMIENTO PENDIENTE` y, en el
  segundo caso, imprime el comando exacto.

Y **los dos GUID no entran en el repositorio**: se componen por trozos
(`@("00000003","0000","0000","c000",("0"*12)) -join "-"` y el análogo de
`User.Read`), igual que ya se hacía con el rol «acceso predeterminado». Mi
barrido (§4) lo confirma: ni un GUID literal.

**Los tests son dos y se reparten bien el trabajo:**
`..._pide_user_read_y_su_consentimiento` fija el **orden** —consentir sobre un
registro sin permisos declarados no consiente nada y **termina en 0**, así que
el orden es lo único que impide un verde vacío—, y
`..._es_mejor_esfuerzo_pero_no_se_calla` exige a la vez que **no** haya
`Salir-Con` detrás y que el resultado **sí** llegue al resumen. Además se amplió
la lista de `test_f010_t6_solofront_no_toca_ni_entra_ni_el_secreto` con las dos
llamadas nuevas, que es lo que impide que `-SoloFront` empiece a tocar Entra.

### Defecto 11 · tokens de ID, y solo de ID (`c691658`)

**Corregido.** Las dos banderas van en la **misma** llamada que las redirect
URI, y el porqué está escrito y es correcto: es la única llamada que se hace
**tanto si el registro se crea como si se reutiliza**, así que corrige también
un registro anterior, y con `--web-redirect-uris` delante `web` nunca viene
vacío (que es lo que hacía fallar la vía del `--set`).

`test_f010_t6_el_registro_emite_tokens_de_id_y_solamente_esos` hace las tres
cosas que hay que hacer: exige que la actualización sea **una sola** línea,
exige las dos banderas **en esa** línea, y **prohíbe la inversión en cualquier
parte del script** (`--enable-id-token-issuance false` y
`--enable-access-token-issuance true` no pueden aparecer). Lo último es lo que
convierte el test en un candado y no en una foto.

### Defecto 12 · `PROMPT_KEY*` atado al YAML (`5270888` + `9e61a30`)

`PROMPT_KEY_FIRMA=firma_parte_es`, y `firma_parte_es` **existe**
(`config/prompts.yaml:93`; las dos únicas claves son `parte_posventa_es` y
`firma_parte_es`). Verificado leyendo el YAML, no el informe.

`test_f010_prompt_keys_infra.py` es el mejor test de esta ronda, por tres
decisiones: pregunta al **repositorio de prompts de verdad**
(`RepositorioPromptsYaml`) en vez de a una lista escrita a mano, así que el YAML
y el test no pueden divergir; **no puede pasar en vacío**
(`..._el_barrido_encuentra_alguna_clave...` lo impide); y trae **control
negativo** con la línea literal que se desplegó. El patrón es `PROMPT_KEY*`, no
una lista, así que la clave que traiga F-015 queda vigilada sola.

### Fase RED de esta ronda · CUMPLE

El informe trae la **salida real** de los cuatro rojos, no una afirmación:
el `Failed:` con el mensaje completo de `PromptNoEncontrado` para el 12, el
`assert [...] == []` con la línea culpable para el 8, los tres `FAILED` con
nombre para el 9, y el `assert '--enable-id-token-issuance true' in '...'` para
el 11. Y una honestidad que cuenta a favor: el implementer deja escrito que uno
de sus rojos salió como `StopIteration` en vez de como aserción, y que
**reescribió el test antes de escribir el arreglo**. Eso es fase RED usada, no
fase RED declarada.

---

## 2 · Lo que la §14 dejó como «no tocar» · NADA REINTRODUCIDO

Comprobado en el árbol de HEAD, no en el informe:

| Punto intocable | Estado hoy | Evidencia |
|---|---|---|
| **La ventana de escritura nace cerrada** | **INTACTO** | `desplegar_backend.ps1:396` — `"ARCHIVO_HABILITADO=false"` sigue dentro del array `$ajustes` que se aplica en **cada** ejecución, sin rama condicional, con su comentario de cuatro líneas en `:31` |
| **Escalonado 35 / 40 / 45** | **INTACTO** | `$TIEMPO_IA_S = 35` (`:105`), `$TIEMPO_GRAPH_S = 35` (`:106`), `TIMEOUT_PETICION_MS: 40000` (`config.js:42`), `$PostventaPresupuestoProxyS = 45` (`00_vars_postventa.ps1:56`) |
| **La nota de D3 / R32** | **INTACTO** | `function_app.py` **no aparece en el diff del rango**. Los seis endpoints siguen `AuthLevel.ANONYMOUS` y la nota sigue entera |
| **El marcador `<TENANT_ID>`** | **INTACTO** | `staticwebapp.config.json:6`, y dos tests independientes lo vigilan (`test_f010_scripts_infra.py:699` y `test_f007_estaticos.py:212`) |

**Un matiz que reporto porque es del mismo rango:** la línea de la referencia a
Key Vault cambió a `('"{0}={1}"' -f ...)` (`desplegar_backend.ps1:407`). Es el
arreglo del defecto 6 y **no relaja R10** —la referencia sigue siendo
`@Microsoft.KeyVault(SecretUri=...)`, solo va entrecomillada para sobrevivir a
`cmd.exe`—, y la prueba empírica de que funciona es T14: nueve App Settings
resueltas contra el vault, `health` 200. Verificado que
`test_f010_..._por_referencia_a_key_vault` sigue en verde.

---

## 3 · CHECKPOINTS.md · recorrido completo

### C1 — El arnés está completo y en verde
- [x] `init.sh` en verde, ejecutado por mí (§0).
- [x] Los ocho ficheros obligatorios existen.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: F-010.
- [x] Rama `feature/F-010-despliegue`, nunca `main`.
- [x] `progress/current.md` encabeza con la sesión activa (2026-08-25). El
      resto es contexto permanente declarado, criterio ya aceptado en la review
      anterior.
- [x] Las siete `done` (F-001…F-007) tienen su resumen en `history.md`
      (7 bloques `## F-0`).

### C3 — Arquitectura y convenciones
- [x] **Hexagonal: intacta.** Esta ronda **no añade ni una línea de producción
      en Python**; toca un `.ps1`, un `.json`, dos `.md` y dos ficheros de test.
- [x] Primera línea con la ruta relativa en el fichero nuevo
      (`# services/postventa-api/tests/test_f010_prompt_keys_infra.py`).
- [x] Sin `print()` de debug, sin dependencias nuevas. `ruff` sobre lo tocado:
      limpio; los 56 avisos del proyecto son **los mismos 56** de deuda previa.
- [x] Unidad de trabajo, validaciones antes de archivar, manuscrito, «firmado
      no es conforme», reprocesar no duplica, `conest`: **N/A justificado** —
      esta ronda no toca lógica de dominio (`function_app.py` ni siquiera está
      en el diff).
- [x] Ningún PDF ni documento con datos personales ha entrado nunca en git
      (`git log --all --diff-filter=A`: vacío para `.pdf/.docx/.xlsx/.pptx`).

### C3 bis — Documentos de fuera
**N/A justificado**: el rango no toca ni un fichero de `docs/referencia/`.

### C4 — La verificación es real
- [x] Los requisitos con test lo siguen teniendo (§6). Los cuatro arreglos de
      esta ronda añaden 9 tests nuevos, todos trazables.
- [x] Los unit tests no tocan red ni BBDD: los de esta ronda leen ficheros del
      árbol y cargan un YAML local.
- [x] Las `MANUAL (humano)` que quedan (T15, T17, T18) están listadas en
      `progress/current.md` con su comando exacto.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado en `harness/features.json`.
- [x] **Fase RED**: cuatro trazas reales pegadas (§1).
- [x] **Cobertura**: `PUERTA COBERTURA [OK] 98,3 %` (114/116, umbral 80 %).
- [x] **Mutación, verificada de forma independiente** (§8): recalculé alcance y
      mutantes con `harness.alcance` y `harness.mutacion.generar_mutantes`, y
      coinciden exactamente.
- [x] **Los muertos, comprobados y no solo contados**: el informe declara
      «Tiempo total 28,8 s» — por debajo de 5 minutos, así que **reejecuté la
      campaña entera** fuera de `progress/`. Totales idénticos (§8).
- [x] **La campaña tardó lo que tenía que tardar**: 28,8 s × 16 workers ÷ 20
      mutantes = **23,0 s/mutante**; mi reejecución, 20,0 s × 16 ÷ 20 =
      **16,0 s/mutante**. Muy por encima del segundo, y del orden de lo que
      cuesta levantar un worktree y recorrer una suite. Nada sospechoso.
- [x] Los **tres** supervivientes tienen su análisis **completado** (mutantes
      equivalentes: el ancho de un separador decorativo). Ninguno en
      `PENDIENTE`. `estandar` no exige cero.
- [x] Sección **«Evidencias»** con los cuatro números **y el nº de workers**
      (16), que es lo que permite el cálculo de arriba.
- [x] Ningún punto N/A sin justificar.

### C4 ter — Rutas sensibles
**N/A justificado**: el repositorio no declara `harness/rutas_sensibles.json`
(solo existe `rutas_sensibles.ejemplo.json`), y el propio checkpoint dice que
sin esa declaración el bloque es N/A. `init.sh` no señaló ninguna ruta tocada.

### C5 — La sesión se cerró bien
- [ ] **`tasks.md` con todas las tareas `[x]`. NO se cumple**, y esta vez **no
      todo el motivo es el previsto**. Quedan cuatro sin marcar: T15, T17 y T18
      —abiertas a propósito, correcto— y **T19, que el humano ya ejecutó**
      (§7.3). Además **T13 está `[x]` con un criterio de verificación que su
      propia ejecución demostró imposible** (§7.1).
- [x] Sin ficheros temporales ni artefactos sospechosos: `git status` limpio
      después de mi reejecución de la campaña (salida al scratchpad, nunca a
      `progress/`).
- [x] `features.json` refleja el estado real: `in_progress`, y así debe seguir.

---

## 4 · Barrido propio de identificadores y secretos

**Es el riesgo más alto de una ronda hecha con el entorno real delante**, así
que lo hice yo y sobre las **líneas añadidas** del rango completo
(`git diff 084f56e..HEAD | grep '^+'`), con estos patrones: GUID canónico,
`azurewebsites.net`, `azurestaticapps.net`, `vault.azure.net`,
`blob.core.windows.net`, `azurecr.io`, `sharepoint.com`, `AccountKey=`,
`client_secret`, tokens `eyJ…`, claves `sk-…` y `AIza…`, e IPv4.

**Un solo hallazgo, y es legítimo:**

- `services/postventa-front/README.md:909` (del diff) nombra
  **`AZURE_CLIENT_SECRET`** — el **nombre** de una App Setting de la Static Web
  App, explicando que `clientSecretSettingName` es un puntero y no un valor. Es
  exactamente lo contrario de un secreto filtrado.

**Ni un GUID, ni una URL de dev, ni un identificador de inquilino, ni un valor
de credencial.** Los dos identificadores públicos que el defecto 9 necesitaba
(Microsoft Graph y el scope `User.Read`) **se componen por trozos** y no
aparecen literales en ningún sitio. `git status` limpio; el marcador
`<TENANT_ID>` sigue sin resolver.

---

## 5 · ⚠️ BLOQUEANTE · El runbook no aprendió nada del despliegue real

`docs/DESPLIEGUE.md` **no se ha tocado desde el 2026-08-20** (`git log` sobre
el fichero: último commit `3967ab8`, anterior al despliegue). Doce defectos
descubiertos ejecutando, y el documento que existe **precisamente** para que la
próxima ejecución no los repita sigue diciendo lo que decía antes de saberlos.
Y no es que le falte contexto: **afirma como prerrequisito algo que ese mismo
despliegue demostró falso.**

| Dónde | Qué dice hoy | Qué demostró el 2026-08-21 |
|---|---|---|
| `docs/DESPLIEGUE.md:43` | script 1 «sube **los once secretos** pedidos a ciegas» | Solo se pueden cargar **nueve**: `swa-client-id` y `swa-client-secret` **los crea `desplegar_front.ps1`**, que genera el registro y los guarda él. El propio informe lo anota: «9 de 11 cargados» |
| `docs/DESPLIEGUE.md:93` | «**Las once credenciales a mano**, para teclearlas cuando el script las pida» | Ídem. Quien siga esta lista se pondrá a inventar dos valores que el despliegue va a sobrescribir |
| `docs/DESPLIEGUE.md` §3 (prerrequisitos) | grupo de seguridad, once credenciales, tope de gasto | **Falta el rol `Key Vault Secrets Officer`**, que es lo que **paró la primera ejecución real** (defecto 4): crear el vault no da permiso sobre sus secretos |
| `docs/DESPLIEGUE.md:43` | anuncia `-Solo <nombre>` como la vía de rotación | **No advierte del defecto 3**: con `powershell -File`, `-Solo` no construye un array y el script responde «estos secretos no existen». Hay que invocarlo desde la sesión o con `-Command` |

**Por qué esto bloquea y no va a observaciones.** Es el mismo listón que puse en
la ronda anterior y que el implementer aceptó sin discutir: *una nota que miente
es peor que no tener nota*. Allí bloqueé por una `.DESCRIPTION` que **podía**
inducir a error; aquí la nota **ya indujo a error a una persona real**, tenemos
la factura —una jornada— y el documento sigue igual. Un runbook solo vale la
segunda vez, y la segunda vez es la rotación de una credencial o el despliegue
que haga otra persona sin este historial delante.

Se agrava porque `docs/DESPLIEGUE.md` es el entregable de **T10**, marcada
`[x]`, y su verificación era precisamente que el runbook fuera utilizable.

---

## 6 · Trazabilidad · requisito → test

Solo los requisitos que esta ronda toca o afecta. Los demás siguen como los
dejó `review_F-010.md` §9, verificados allí.

| Requisito | Test que lo cubre | Estado |
|---|---|---|
| **R2** (re-ejecutable) | `..._pide_user_read_y_su_consentimiento` — el permiso solo se concede si no estaba | ✔ |
| **R8** (sin identificadores) | `test_f006_repo_sin_identificadores.py` + barrido propio (§4) | ✔ |
| **R10** (App Settings por referencia) | `..._por_referencia_a_key_vault`; el entrecomillado no la relaja | ✔ |
| **R12/R13** (marcador y copia de trabajo) | `..._conserva_su_marcador`, `..._se_borra_en_un_finally`, `test_f007_..._sigue_sin_resolver` | ✔ |
| **R14** (la SWA exige sesión) | `staticwebapp.config.json` + **T16 ejecutada: 302 a `/.auth/login/aad`** | ✔ / **sin test sobre las rutas** (§9.1) |
| **R15** (no miembro no entra) | **T16 ejecutada**: no miembro rebota, probado en incógnito | ✔ humano |
| **R16** (`appRoleAssignmentRequired` + grupo) | test existente; ampliado en la lista de `-SoloFront` | ✔ |
| **R17** (capa 5) | **T14**: al enlazar el backend, el host desnudo pasa de 200 a **401** — la plataforma la impone sola | ✔ humano |
| **R32** (la anonimidad, deliberada y explicada) | test de F-010 intacto **+ nuevo** `..._el_resumen_solo_alega_solofront_cuando_lo_esta`, que extiende R32 al resumen | ✔ reforzado |
| **R33/R34** (ventana de escritura) | intactos (§2) | ✔ |
| **R35** (tope de gasto) | **MANUAL — T14 bis** | **[x] sin resultado anotado** (§7.2) |
| **nuevo** (`PROMPT_KEY*` real) | `test_f010_prompt_keys_infra.py`, 5 tests | ✔ |

---

## 7 · Estado de las tareas MANUAL · condición de cierre nº 1

La condición nº 1 de `review_F-010.md` §11 exige que cada manual ejecutada
tenga **su resultado real anotado en `progress/`**. Seis están marcadas `[x]`.
Las repaso una a una, y **digo explícitamente cuáles no lo tienen**.

| Tarea | `tasks.md` | Resultado real anotado | Dónde |
|---|---|---|---|
| **T1** · grupo en Entra | `[x]` | **SÍ** — «hecho, con los miembros del piloto dentro» | `impl_F-010.md`, tabla |
| **T2** · medición de D2 | `[x]` | **SÍ** — los tres números del peor caso, con la salida real | `impl_F-010.md` §T2 |
| **T13** · secretos al Key Vault | `[x]` | **SÍ, pero contradice a la tarea** — «9 de 11 cargados» | `impl_F-010.md` (§7.1) |
| **T14** · desplegar backend | `[x]` | **SÍ** — las cuatro comprobaciones, con el matiz del 400 vs 503 | `impl_F-010.md` |
| **T14 bis** · tope de gasto de IA | `[x]` | **NO** (§7.2) | — |
| **T16** · front y acceso | `[x]` | **SÍ** — las tres pruebas, en incógnito | `impl_F-010.md` |
| **T19** · tarjeta del portal | **`[ ]`** | **casi** — solo de pasada (§7.3) | `current.md` |
| T15 / T17 / T18 | `[ ]` | abiertas a propósito, correcto | — |

### 7.1 · T13 está `[x]` con un criterio de verificación imposible

`specs/F-010-despliegue/tasks.md:211` sigue diciendo:

> **Verificación**: el script lista los **nombres** de los **once** secretos
> cargados […] Se anota en `progress/` solo «**once** secretos cargados:
> sí/no».

Y la anotación real dice **nueve**, con el motivo correcto: los otros dos los
crea `desplegar_front.ps1`. La tarea está marcada `[x]` contra un criterio que
**nunca podrá cumplirse**, y quien vuelva a T13 al rotar una credencial buscará
once. Es el defecto 2 de la lista de doce, y **no se corrigió**: solo se marcó
la casilla.

### 7.2 · T14 bis está `[x]` sin un solo resultado anotado

Busqué «T14 bis» en todo `progress/`. Las once apariciones hablan **del orden**
(«antes de T16») o del requisito (R35). **Ninguna dice si el tope y la alerta
quedaron configurados, ni con qué importe, ni en qué proveedor.**

Esto incumple la condición nº 1 de forma directa, y no en una tarea cualquiera:
es la que la review anterior subrayó como **la que no es una formalidad**, con
su razón escrita —`/api/extraer` y `/api/firma` son **anónimos por diseño** y
hoy están **alcanzables**, porque T16 ya se ejecutó—. El tope es la única
defensa proporcionada frente a que un desconocido gaste cuota. Un `[x]` sin
resultado no la acredita.

### 7.3 · T19 está ejecutada y `tasks.md` dice que no

El líder confirma que la tarjeta está publicada y funciona, y
`progress/current.md` lo menciona **de pasada** («tarjeta publicada en el
portal»). Pero `tasks.md:360` sigue en `[ ]` y no hay ninguna anotación con el
resultado de la tarea. Es la desviación que rompe C5: la casilla y la realidad
dicen cosas distintas. (El GUID del grupo **no** debe entrar aquí, y no ha
entrado — §4.)

---

## 8 · Verificación independiente de la campaña de mutación (C4 bis)

**Recálculo puro** con `harness.alcance` y `harness.mutacion.generar_mutantes`
(sin ejecutar la suite, sin escribir en disco):

```
F-010: 3 fichero(s), 253 línea(s) de producción
  harness/mutacion.py                  : 10 lin.  ->   0 mutantes
  services/postventa-api/function_app.py: 55 lin.  ->   0 mutantes
  services/postventa-front/dev_server.py: 188 lin. ->  20 mutantes
TOTAL recalculado: 20 mutantes / 253 líneas
```

Coincide **exactamente** con el informe (3 ficheros, 253 líneas, 20 mutantes).

**Prueba de control por los dos ceros por fichero.** No me valía el cero a
secas, así que corrí `generar_mutantes` sobre esos dos ficheros **enteros**,
ignorando el alcance: `harness/mutacion.py` da **143** mutantes y
`function_app.py` da **23**. El generador funciona; lo que pasa es que las
líneas que F-010 cambió en ellos no son sentencias mutables (la cabecera del
módulo y los decoradores). **Los ceros son legítimos**, no un generador roto.

**Reejecución completa**, obligatoria porque el informe declara 28,8 s (< 5
min). Salida al scratchpad, **nunca a `progress/`**:

| Métrica | Informe | Mi reejecución |
|---|---|---|
| Mutantes | 20 | **20** |
| Muertos | 17 | **17** |
| Supervivientes | 3 | **3** |
| Timeouts | 0 | **0** |
| Tiempo | 28,8 s | 20,0 s |

Y **muestreé los tres supervivientes**: `dev_server.py:169`, `:171` y `:175`,
operador `[entero]`, `log.info("=" * 60)` → `log.info("=" * 61)`. Los tres
salen idénticos en mi campaña, con el mismo operador y el mismo texto
original→mutado. El informe no está escrito a mano.

`git status` **limpio** después.

---

## 9 · Observaciones (no bloquean, pero la primera es barata y la recomiendo)

### 9.1 · De los doce defectos, cuatro se cerraron sin un solo test

Comprobado por grep en todo el árbol de tests:

| Defecto | Arreglo | Test que lo ata |
|---|---|---|
| 5 · `2>$null` mata el script en PS 5.1 | `$ErrorActionPreference = 'Continue'` en 4 puntos | **ninguno** |
| 6 · `cmd.exe` rompe los paréntesis de Key Vault | entrecomillado del ajuste | **ninguno** |
| 7 · `--value` con valor que empieza por guion | `--value=` pegado | **ninguno** |
| 10 · la página de login exigía sesión | ruta anónima en `staticwebapp.config.json` | **ninguno** |

El **10 es el que más pide un test y el más barato de escribir**: hoy nadie
vigila las rutas de `staticwebapp.config.json`. Los dos únicos tests que lo
leen comprueban el marcador `<TENANT_ID>` y la ausencia de GUID. **Borrar la
ruta `/.auth/login/aad` anónima, o reordenarla debajo del `/*`, deja la suite
entera en verde y la aplicación en bucle de login** — el mismo `AADSTS50196`
que costó una tarde. Y lo mismo con la regla nueva del README: volver a meter
un `$comentario` no lo caza nadie, aunque el esquema declare
`additionalProperties: false`.

Es llamativo porque el **5 tiene precedente en este mismo repositorio**:
`test_f005_scripts_infra.py:244` ya vigila exactamente esa trampa
—`$ErrorActionPreference = "Continue"`— para los scripts de F-005. Los de F-010
la repitieron y el arreglo llegó sin llevarse la vigilancia consigo. Nótese
además que el test de F-005 exige **comillas dobles** y el arreglo de F-010 usa
**comillas simples**: si algún día se generaliza ese test a `infra/*.ps1`,
habrá que contemplar las dos formas.

### 9.2 · El defecto 6 tiene un hermano vivo en `cargar_secretos_postventa.ps1`

El defecto 6 demostró **en este entorno concreto** que `az` es un `.cmd` y que
`cmd.exe` reprocesa la línea. El arreglo del defecto 7 dejó
`cargar_secretos_postventa.ps1:236` así:

```powershell
az keyvault secret set --vault-name $PostventaKeyVault --name $nombre `
    --value=$claro --only-show-errors | Out-Null
```

**Sin entrecomillar.** Una contraseña que contenga `&`, `(`, `)`, `|`, `^`,
`<` o `>` —perfectamente legal en una contraseña de PostgreSQL elegida por una
persona— va a morir por el **mismo** mecanismo que mató el despliegue del
backend, con el mismo error incomprensible. Los otros dos usos
(`--value=$appId`, `--value=$secreto`) son de bajo riesgo por el alfabeto que
Entra genera; el de la contraseña, no.

No lo hago bloqueante porque los nueve secretos ya están cargados y la rotación
es rara, y porque **el arreglo hay que verificarlo contra Azure**, cosa que ni
yo ni el implementer podemos hacer desde aquí. Pero quedaría escrito: o se
entrecomilla como el ajuste de Key Vault, o al menos se anota el límite en el
runbook junto al resto de §5.

### 9.3 · Menores

- `test_f010_prompt_keys_infra.py` lee los `.ps1` con
  `read_text(encoding="ascii")`. Es deliberado (vigila la pureza ASCII, y hoy
  los nueve scripts la cumplen), pero un acento en cualquier `.ps1` de `infra/`
  rompería la **colección** de pytest con un `UnicodeDecodeError` en vez de con
  un fallo legible. Un `errors="replace"` con aserción explícita diría mejor
  qué pasa.
- **«Evidencias» dice «1.079 pasados, 13 saltados»**; la suite da **3
  saltados** (medido dos veces). Parece un desliz de transcripción del «13»;
  el número que importa —1.079— es exacto.
- La **duplicación de la nota** «_Análisis traído de la campaña anterior…_» en
  `mutacion_F-010.md` (ya van dos por superviviente) está bien diagnosticada
  por el implementer y bien dejada fuera: es del arnés genérico y se arregla en
  `arnes-base`. **Confirmo que no invalida ningún análisis.**

---

## 10 · CAMBIOS REQUERIDOS

Numerados, concretos y con fichero. **Ninguno toca los arreglos de los defectos
8, 9, 11 y 12: esos quedan aprobados tal cual están.**

1. **`docs/DESPLIEGUE.md:43` y `:93` — corregir «once» por «nueve»** y decir
   por qué: `swa-client-id` y `swa-client-secret` los genera y guarda
   `desplegar_front.ps1`, no se teclean. Es la afirmación que el despliegue real
   ya desmintió.
2. **`docs/DESPLIEGUE.md` §3 — añadir el rol `Key Vault Secrets Officer`** a la
   lista de prerrequisitos, con la frase que lo explica: crear el Key Vault
   **no** da permiso sobre sus secretos. Es lo que paró la primera ejecución
   real (defecto 4).
3. **`docs/DESPLIEGUE.md:43` — advertir del defecto 3** donde se anuncia
   `-Solo <nombre>`: con `powershell -File` los argumentos llegan como una sola
   cadena y el script responde «estos secretos no existen»; hay que invocarlo
   desde la sesión (`.\infra\...`) o con `-Command`.
4. **`specs/F-010-despliegue/tasks.md:211` (T13) — rectificar la verificación**:
   «nueve secretos cargados: sí/no», y la nota de que los dos restantes los crea
   el despliegue del front. Hoy la tarea está `[x]` contra un criterio
   imposible. (Precedente en este repositorio: T8 y T19 de F-006 se
   rectificaron igual.)
5. **`progress/` — anotar el resultado real de T14 bis** (R35): tope y alerta
   configurados sí/no, y en qué proveedor. **Sin importes ni credenciales.** Lo
   tiene que aportar el humano; el implementer no puede inventarlo. Es la
   condición nº 1 de la review anterior sobre la tarea que esa review marcó como
   la que no es formalidad, y los endpoints ya están alcanzables.
6. **T19 — marcar `[x]` en `tasks.md:360` y anotar su resultado** en `progress/`
   («tarjeta publicada y visible para el grupo: sí»), **sin el GUID del grupo**,
   que vive solo en `front-portal`.

**Recomendado y no exigido** (§9.1): un test sobre
`services/postventa-front/staticwebapp.config.json` que fije dos cosas —que
`/.auth/login/aad` con `anonymous` es la **primera** ruta, y que el fichero no
lleva claves fuera del esquema—. Es el único de los cuatro defectos sin test que
se ata en veinte líneas, y protege contra volver a perder una tarde con
`AADSTS50196`.

---

## 11 · VEREDICTO

# CHANGES_REQUESTED

**El rechazo es estrecho y no toca el código.** Lo que se me encargó revisar
—los defectos 8, 9 y 11— está **bien corregido y bien atado**, con tests que
son candados y no fotos, con fase RED real pegada, sin haber reintroducido nada
de lo que la §14 dejó como intocable, sin un solo identificador ni secreto en
el repositorio, y con la campaña de mutación verificada por mí de forma
independiente **y reejecutada entera** con totales idénticos. La ronda es de la
misma calidad alta que las anteriores.

Lo que bloquea es el otro lado del despliegue: **la jornada del 2026-08-21 costó
doce defectos, y los documentos que existen para que no vuelvan a costarse no
los recogieron.** `docs/DESPLIEGUE.md` sigue afirmando un prerrequisito que ese
mismo despliegue demostró falso —«las once credenciales a mano»— y omite el rol
de Key Vault que fue lo que paró la primera ejecución. Es el listón que puse en
la ronda anterior, *una nota que miente es peor que no tener nota*, con la
diferencia de que esta ya mintió a alguien y tenemos la factura.

Y quedan tres huecos de la condición de cierre nº 1: **T14 bis marcada sin un
solo resultado anotado** —justo la tarea que la review anterior subrayó como la
que no es formalidad, con los endpoints anónimos ya alcanzables—, **T13 marcada
contra un criterio imposible**, y **T19 ejecutada con la casilla sin marcar**.

### Respuesta directa a la pregunta del líder

> ¿Puede F-010 pasar a `done` en cuanto el humano ejecute T15, T17 y T18 y
> anote su resultado?

**No todavía: quedan las seis correcciones del §10.** Tres son mías de pedir y
del implementer de hacer (1, 2, 3 y 4: dos documentos, ninguna línea de código);
dos las tiene que aportar el humano (5 y 6: el resultado de T14 bis y el de
T19). Ninguna es grande, y **ninguna exige tocar Azure ni SharePoint**.

Hechas esas seis **y** ejecutadas T15, T17 y T18 con su resultado anotado,
**F-010 queda en condiciones de pasar a `done`** y no me queda nada más que
revisar del código. Siguen vigentes, sin cambios, las condiciones 3, 4 y 5 de
`review_F-010.md` §11:

- **T18 exige autorización expresa nombrando `CHECKPOINTS.md` C5**, porque
  cierra una casilla de F-006, una feature ya cerrada. Y un fichero con sufijo
  `(1)` en el listado es **PARADA** (R31).
- **Tras T18, volver a cerrar la ventana de escritura**
  (`ARCHIVO_HABILITADO=false`): el despliegue la cierra sola, pero entre T18 y
  el siguiente despliegue no hay nada que la cierre salvo la mano del humano.
- **T19 se hace en `front-portal`** y el GUID real del grupo **nunca** entra en
  este repositorio (comprobado que no ha entrado, §4).

`F-010` **sigue `in_progress`**.

---

## 12 · Propuestas al protocolo (no aplicadas — para que las apruebe el humano)

1. **`.claude/agents/reviewer.md` y `CHECKPOINTS.md` C5 · «los defectos de
   ejecución vuelven al documento que los previene».** Esta feature enseña un
   hueco del arnés: cuando una tarea `MANUAL (humano)` destapa defectos, el
   protocolo obliga a corregir el **código** y a anotar el **resultado**, pero
   **nada obliga a que la lección llegue al runbook o al enunciado de la
   tarea**. Aquí eso dejó nueve de doce defectos corregidos en scripts y **cero**
   en `docs/DESPLIEGUE.md`. Propongo un punto explícito en C5: *toda tarea
   MANUAL que se marque `[x]` habiendo destapado un defecto deja escrito dónde
   se recogió la lección, o por qué no hacía falta.*
2. **`CHECKPOINTS.md` C5 · una casilla marcada no puede contradecir su propio
   criterio de verificación.** T13 está `[x]` con «once secretos» y su
   anotación dice «nueve». Hoy ningún checkpoint lo caza; el reviewer lo
   encuentra solo si va tarea por tarea. Propongo añadirlo a C5 como comprobación
   explícita.
3. **`arnes-base` · la nota duplicada de `harness.mutacion`** (§9.3): reportada
   por el implementer, es del arnés genérico. Propongo darla de alta allí junto
   con el desfase 1.5.2 → 1.6.x que la review anterior ya dejó propuesto en su
   §13.5, y que sigue sin cerrarse.
