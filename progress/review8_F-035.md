<!-- progress/review8_F-035.md -->
# F-035 · Review 8 · Correcciones de la review 7 (`publicar_maqueta.ps1`)

- **Veredicto:** APPROVED (APROBADO), con observaciones que no bloquean.
- **Rango revisado:** `e46ced1..efd5fc8`, rama `feature/F-035-portal-posventa`. Son los commits `ed7c9bf`, `97fda38` y `efd5fc8`. Todo lo anterior quedó aprobado en las reviews 6 y 7, salvo lo que la 7 rechazó.
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura de las líneas cambiadas y una campaña de mutación con los supervivientes analizados.
- **Fecha:** 2026-09-26.

> No he ejecutado nada contra Azure ni contra Entra. Las simulaciones corrieron en el scratchpad:
> - `az` y `swa` eran envoltorios `.cmd` falsos;
> - el `PATH` del proceso hijo solo tenía esos envoltorios y `System32`, así que la CLI real de Azure no se podía alcanzar;
> - cada ejecución abortaba si `Get-Command az` o `Get-Command swa` no resolvían a los falsos.
>
> No he tocado el código del implementer. `git status` sigue limpio salvo este informe.

## Resumen

Los cuatro cambios de la review 7 están hechos y funcionan cuando los argumentos pasan de verdad por `cmd.exe`:

- **Camino bueno.** Con el envoltorio con la estructura de `az.cmd` termina con código 0. La versión anterior (`e46ced1`), con el mismo envoltorio, sigue parando siempre con 9. Mi simulador, por tanto, ve el defecto.
- **Backend.** Si el entorno tiene backend, o no se puede leer o interpretar, el script para con 9 antes de las App Settings. Lo he probado con seis formas de salida ilegible.
- **Retirar con la lista vacía.** `-Retirar` con una lista que quedaría vacía para con 12 antes de la confirmación y sin escribir nada.
- **URL de producción.** Se conservan siempre, en su orden.
- **Test de literales.** El test nuevo cae en rojo con la línea exacta del defecto, y también con metacaracteres en llamadas directas, continuadas y de `swa`.

`desplegar_front.ps1` y los tests de F-010 no cambian. `init.sh` está en verde.

No he encontrado nada que pueda dejar Azure o Entra en mal estado ni tocar producción. Lo que sigue abierto son observaciones.

## 1 · `git diff e46ced1 efd5fc8`

- Ficheros cambiados:
  - `docs/DESPLIEGUE.md`
  - `infra/publicar_maqueta.ps1`
  - `progress/current.md`
  - `progress/impl_F-035.md`
  - `tests/test_f035_publicar_maqueta.py`
- **`infra/desplegar_front.ps1` y los `test_f010_*` no aparecen** [x]. Tampoco en `git diff --name-only dev...HEAD`: el grep sale vacío con código 1. `git log dev..HEAD` sobre esas rutas también sale vacío.
- **Cambio 1** [x]. `Backends-Del-Entorno` (l. 195-214) pide `-o json` sin `--query` y cuenta con `ConvertFrom-Json -ErrorAction Stop` y `@($lista).Count`. Si la lectura falla o el JSON no se interpreta, devuelve `$null`, y el llamador lo trata como «tiene backend». `Valor-De-Az` no se toca, y el test de identidad sigue en verde.
  - He comprobado en la CLI instalada (desensamblando `static_sites.pyc`, sin llamar a nada) que `backends show` es `get_backend` → `client.get_linked_backends_for_build(...)`. Devuelve una lista paginada, así que un entorno sin backend sale como `[]`, que es lo que el script cuenta como "0".
- **Cambio 2** [x]. Ver §4.
- **Cambio 3** [x]. La simulación del implementer usa `sim_cmd\az.cmd` con la misma estructura `IF ( … %* … )` y un `swa.cmd` copiado del shim de npm. He repetido la simulación con envoltorios míos (§2).
- **Cambio 4** [x]. `$quedan` se calcula y se comprueba en las l. 327-331, antes del `Read-Host` (l. 334) y del `environment delete` (l. 347).
- **Añadidos del implementer:**
  - guarda de URL de retorno con metacaracteres (l. 319-322, antes de confirmar);
  - lectura y guarda del secreto antes de la primera escritura (l. 383-396);
  - párrafo O4 en `docs/DESPLIEGUE.md` §10;
  - paso 3 del guion (§8) sin `length(@)`.

  Los he revisado todos. Ninguno añade escrituras ni cambia el destino de ninguna.

## 2 · Simulación propia con `az.cmd` y `swa.cmd` (34/34 OK)

**Montaje.** Todo está en `scratchpad\rev8\`:

- `bin\az.cmd` es una réplica línea a línea del `az.cmd` MSI (`@IF EXIST … ( … "python" az_falso.py %* ) ELSE (…)`).
- `bin\swa.cmd` es una réplica del shim de npm (`endLocal & … "%_prog%" … %*`).
- `az_falso.py` anota el `argv` tal como llega **después de `cmd.exe`** y responde según el estado del escenario.
- El `az` falso es **estricto**:
  - toda llamada `staticwebapp environment|appsettings|backends` sin `--environment-name maqueta` se anota como VIOLACION y falla;
  - una llamada no prevista, también;
  - `ad app list` solo responde si le llega `--display-name` con el valor exacto `Postventa Incidencias`, con su espacio;
  - `appsettings list` devuelve **lo que recibió** `appsettings set`, así que la comprobación del script mide lo que sobrevivió a `cmd`.
- El script corre en una copia desechable (`rev8\repo\infra`, con el front copiado). La única función de PowerShell es `Read-Host`, que anota si se llamó.
- En cada ejecución compruebo:
  - el código de salida;
  - las escrituras (`swa deploy`, `appsettings set`, `environment delete` y `ad app update`);
  - que no haya violaciones;
  - que el token del operador vuelva a su sitio;
  - que no quede la copia de trabajo en `TEMP`;
  - que no se impriman el secreto, el id de cliente, el inquilino ni el token.

**Datos del escenario.**

- Secreto con los caracteres que usa Entra: `Ab8Q~x.y_z-1Kq9`.
- Id de cliente con forma de GUID.
- Tres URL de retorno de «producción»: la del host de producción, `http://localhost:4280/…` y una de dominio propio.

Los hosts son inventados.

**Control.** Con el script de `e46ced1`, el mismo montaje reproduce el defecto de la review 7:

```
CONTROL e46ced1: publicar sin backend (entorno nuevo)      salida  9 | escrituras 1 | Read-Host si | FALLA: codigo 9 (esperado 0)
CONTROL e46ced1: republicar, entorno previo sin backend    salida  9 | escrituras 0 | Read-Host no | FALLA: codigo 9 (esperado 0)
```

**Script de `efd5fc8`** (salida literal; las líneas largas van truncadas a 230 caracteres en la impresión, y la comprobación se hace sobre el `argv` completo):

```
S1 publicar sin backend, entorno nuevo                     salida  0 | escrituras 3 | Read-Host si | OK
      - swa deploy <R>\tmp_run\postventa-maqueta-… --env maqueta --no-use-keychain
      - staticwebapp appsettings set --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --setting-names AZURE_CLIENT_ID=<client-id> AZURE_CLIENT_SECRET=<secreto> --only-show-e…
      - ad app update --id 0f1e2d3c-… --web-redirect-uris https://prod-ficticio.1.ejemplo.net/.auth/login/aad/callback http://localhost:4280/.auth/login/aad/callback https://postventa.ejemplo.es/.auth/login/aad/c…
S1b republicar, entorno previo sin backend, URL ya registrada salida  0 | escrituras 2 | Read-Host si | OK
S2 publicar, el entorno sale con backend tras subir        salida  9 | escrituras 1 | Read-Host si | OK   (solo swa deploy)
S2b publicar, entorno previo con backend                   salida  9 | escrituras 0 | Read-Host no | OK
S2c publicar, dos backends tras subir                      salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend texto que no es JSON                  salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend JSON truncado                         salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend null                                  salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend objeto suelto                         salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend salida vacia                          salida  9 | escrituras 1 | Read-Host si | OK
S3 publicar, backend fallo de lectura (exit 1)             salida  9 | escrituras 1 | Read-Host si | OK
S3b publicar, entorno previo con backend ilegible          salida  9 | escrituras 0 | Read-Host no | OK
S4 publicar con 3 URL de produccion                        salida  0 | escrituras 3 | Read-Host si | OK
S4b retirar con 3 de produccion + maqueta                  salida  0 | escrituras 2 | Read-Host si | OK
      - staticwebapp environment delete --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --yes --only-show-errors
      - ad app update --id … --web-redirect-uris <las 3 de produccion> --only-show-errors
S4c retirar, maqueta en medio de la lista                  salida  0 | escrituras 2 | Read-Host si | OK
S5 retirar, solo esta la de maqueta (quedaria vacia)       salida 12 | escrituras 0 | Read-Host no | OK
X1 publicar -WhatIf                                        salida  0 | escrituras 0 | Read-Host no | OK
X2 publicar, confirmacion denegada                         salida  5 | escrituras 0 | Read-Host si | OK
X3 publicar, secreto con ( ) & | < > ^ % ! "  (10 casos)   salida  7 | escrituras 0 | Read-Host si | OK (los 10)
X4 publicar, una URL registrada con &                      salida 12 | escrituras 0 | Read-Host no | OK
X5 retirar, URL con metacaracter registrada                salida 12 | escrituras 0 | Read-Host no | OK
X6 publicar, App Settings no quedan                        salida 10 | escrituras 2 | Read-Host si | OK
X7 publicar, host tras subir = produccion                  salida 11 | escrituras 1 | Read-Host si | OK
X8 retirar sin entorno ni URL de maqueta                   salida  0 | escrituras 0 | Read-Host si | OK
X9 retirar sin entorno pero con URL de maqueta             salida  0 | escrituras 1 | Read-Host si | OK

34/34 OK
```

Los cinco casos que pidió el líder:

| Caso | Resultado |
|---|---|
| Publicar sin backend | S1 y S1b: **0**. `az` recibe **exactamente** `AZURE_CLIENT_ID=<guid>` y `AZURE_CLIENT_SECRET=<secreto>` tras `cmd`. La lista final es la de producción más la de `maqueta`. La URL sale en el resumen. En S1b, con la URL ya registrada, no se reescribe la lista. |
| Con backend | S2 y S2c: **9** después de subir y **antes de las App Settings**. Solo hay una escritura, `swa deploy`, las App Settings del entorno quedan vacías y la lista de retorno queda intacta. S2b, con el entorno previo con backend: **9** sin escribir nada y antes de confirmar. |
| JSON ilegible | Los seis sabores de S3 (no es JSON, JSON truncado, `null`, objeto suelto, salida vacía y fallo de lectura) y S3b (`<html>` en un entorno previo) dan **9**. Falla cerrado. |
| URL de producción | S4: se conservan las tres y se añade la de `maqueta`. S4b y S4c: al retirar quedan **exactamente** las tres de producción, en su orden, aunque la de `maqueta` esté en medio. |
| `-Retirar` con la lista vacía | S5: **12**, **sin llamar a `Read-Host`**, sin borrar el entorno y con la lista intacta. |

En todos los escenarios:

- no hubo ninguna llamada de entorno sin `--environment-name maqueta`;
- el token del operador volvió a su valor;
- no quedó la copia de trabajo en `TEMP`;
- no se imprimió ningún valor secreto.

## 3 · Cada llamada a `az` (y a `swa`), con la óptica de `cmd.exe`

Windows PowerShell 5.1 solo entrecomilla un argumento si lleva espacios. `cmd.exe` interpreta `( ) & | < > ^` al expandir `%*`, y `"` altera el entrecomillado. `%` no se reexpande desde `%*`, y `!` solo cuenta con la expansión retardada activada.

| Línea | Llamada | Argumentos variables / literales sensibles | Veredicto |
|---|---|---|---|
| 166 | `az @Argumentos --only-show-errors 2>$null` (`Valor-De-Az`, duplicada) | lo que le pasen; `2>$null` lo resuelve PowerShell | Bien |
| 179 | `ad app list --display-name $PostventaAppRegistro --query [0].appId` | «Postventa Incidencias» lleva espacio, así que va entrecomillado; `[0].appId` no lleva metacaracteres | Bien. Verificado en la simulación: el falso solo responde con el nombre exacto |
| 184, 253 | `staticwebapp show --query name` / `defaultHostname` | nombres de `00_vars` (`swa-postventa-ruesma`, `rg-postventa-dev`) | Bien |
| 192 | `environment show … --environment-name maqueta --query hostname` | — | Bien |
| 205 | `backends show … --environment-name maqueta -o json` | **ya sin `--query`** | Bien (corregido) |
| 220 | `ad app show --id $appId --query web.redirectUris` | GUID | Bien |
| 238, 401 | `account show --query id` / `tenantId` | — | Bien |
| 258, 383 | `keyvault secret show --vault-name … --query value` | — | Bien |
| 347 | `environment delete … --environment-name maqueta --yes` | — | Bien |
| 358, 487 | `ad app update --id $appId --web-redirect-uris $quedan` / `$todas` | URL leídas de Entra, sin espacios | Bien. La guarda de la l. 319 para antes de confirmar si alguna lleva `()&|<>^%!"`. Probado en X4 y X5 |
| 431 | `staticwebapp secrets list --query properties.apiKey` | — | Bien |
| 440 | `swa deploy $copiaDeTrabajo --env maqueta --no-use-keychain` | ruta de `TEMP` + `postventa-maqueta-<guid>` | Bien. En el shim de npm `%*` va fuera de todo `IF (…)`, y una ruta con espacios va entrecomillada. Ver O-c |
| 466-467 | `appsettings set … --setting-names "AZURE_CLIENT_ID=$clientId" "AZURE_CLIENT_SECRET=$secreto"` | GUID y secreto sin comillas | Bien. La guarda de la l. 392 para con 7 antes de escribir (X3, los 10 caracteres). Verificado que `az` recibe el valor exacto con `~ . _ -` |
| 469-470 | `appsettings list … --query properties.AZURE_CLIENT_ID` / `…SECRET` | — | Bien |

El guion del humano (§8 del bloque 6, paso 3) usa ahora `--query "[].name"` y `--query "[].backendResourceId"`. PowerShell quita las comillas y ninguno de los dos lleva metacaracteres de `cmd`: bien. El único `length(` que queda en `infra/` es `desplegar_front.ps1:475`, de F-010 (O1).

## 4 · El test nuevo de literales, con su control en rojo

`tests/test_f035_publicar_maqueta.py`: 30 tests en la review 7, 34 ahora, todos en verde (`34 passed`). `ruff` sobre el fichero da «All checks passed!».

He estropeado el script en copias desechables (`scratchpad\rev8\control_test.py`, con CRLF conservado) y he ejecutado el fichero de test:

| Estropeo | Resultado |
|---|---|
| C1 vuelve la línea exacta con `length(@)` | **ROJO**: `…ningun_argumento_de_az_se_rompe…`, `…control_la_regla_caza…`, `…sin_backend_o_para…` |
| C2 `join(hostname)` en `Host-Del-Entorno` | **ROJO**: la regla y otro test |
| C3 `--query length(@)` en la llamada directa `environment delete` | **ROJO**: la regla |
| C4 `--query [?a\|\|b]` en `appsettings set` (línea con continuación) | **ROJO**: la regla |
| C5 `a&b` en `swa deploy` | **ROJO**: la regla y otro test |
| C6 `val^ue` en un `Valor-De-Az` | **ROJO**: la regla |
| C7 la guarda del secreto sin `^` | **ROJO**: `…un_secreto_que_cmd_romperia…` |
| C8 sin la guarda de URL | **ROJO**: `…una_url_de_retorno_que_cmd_romperia…` |
| C9 la guarda de `-Retirar` movida detrás de la confirmación | **ROJO**: `…nunca_se_reescribe_la_lista_vacia` |
| C10 `ConvertFrom-Json` sin `-ErrorAction Stop` | **ROJO**: `…sin_backend_o_para…` |
| L1 *(límite)* metacarácter metido por una variable | ROJO, pero solo porque otro test exige el literal exacto; la regla no lo ve |
| L2 *(límite)* una llamada nueva `$y = az … --query length(@)` | **VERDE**: ver O-a |

El control propio del test (`…control_la_regla_caza_el_defecto_de_la_review_7`) incluye la línea exacta del defecto, una llamada directa con `&&` y un caso con espacios que no debe cazar. La fase RED del implementer muestra la salida real del fallo antes de corregir el script: la acepto.

## 5 · Campaña del arnés y control del cero

- **Informe.** `progress/mutacion_F-035.md` declara 0 mutantes, 0 muertos, 0 supervivientes, 0 timeouts y un «Tiempo total» de 0.0 s.
- **Reejecución.** Como son menos de 5 minutos, reejecuté la campaña: `python -m harness.mutacion --feature F-035 --salida <scratchpad>\rev8\mutacion_rev8.md`. Da los mismos totales. El alcance es de 0 ficheros y 0 líneas de producción (origen `rama`, `54c0884..feature/F-035-portal-posventa`). `git status` quedó limpio.
- **Control del cero.** Pasé `generar_mutantes(fuente, líneas, fichero)` por las líneas cambiadas de `tests/test_f035_publicar_maqueta.py` en `e46ced1..efd5fc8`, ignorando la exclusión, y salen **42 mutantes**. El generador funciona. El cero se debe a la exclusión de los tests, que es por diseño, y a que el rango no toca Python de producción.

## Checkpoints

**C1**
- [x] `bash harness/init.sh`: exit 0, «ENTORNO LISTO».
  - Raíz: 107 passed.
  - api y front: desde la caché. El implementer declara la api sin caché tras `ed7c9bf`: 4356 passed, 52 skipped.
  - `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`.
  - `ruff`: 61 avisos de deuda previa.
- [x] Existen los ficheros del arnés.

**C2**
- [x] Solo hay una feature `in_progress`, F-035, y la rama es `feature/F-035-portal-posventa`.
- [x] `current.md` tiene la entrada de estas correcciones. Sigue acumulando bloques anteriores: es la deuda O-2 de la review 1 y no bloquea.
- [x] `history.md` no cambia, porque no hay ninguna feature `done` nueva.

**C3**
- [x] Hexagonal: **N/A**. El rango solo toca un script de `infra/`, un test y documentación, y nada de eso tiene capas.
- [x] Primera línea con la ruta, en el script y en el test. El script sigue en ASCII, con CRLF y sin BOM (lo cubre un test).
- [x] Sin prints de depuración, sin TODO y sin secretos, GUID, hosts ni IP en el texto: lo cubre el barrido del test y lo he leído. En la simulación tampoco se imprime ningún valor.
- [x] Checkpoints de dominio (parte, firma, `conest`, Sigrid, archivo): **N/A**. El rango no toca el pipeline, y la maqueta va sin backend.
- [x] No entra ningún PDF ni parte escaneado en git.

**C3 bis**
- [x] **N/A**: el rango no toca `docs/referencia/`.

**C4**
- [x] Cada cambio pedido tiene su test: los 4 tests nuevos y los 3 enmendados (§4). Todos pasan.
- [x] Los tests unitarios no tocan red ni BBDD: solo leen el texto del script.
- [x] Queda verificado que el script hace lo que se le pide cuando `az` pasa por `cmd.exe`: simulación propia 34/34 OK, con el control de la versión vieja en rojo (§2). El motivo del rechazo de la review 7 está resuelto.
- [x] Las verificaciones MANUAL están en el guion del humano (`impl_F-035.md` §8, enmendado). **T12 sigue pendiente, por diseño.**

**C4 bis**
- [x] `rigor: estandar`, declarado.
- [x] **Fase RED:** el informe trae la salida real del fallo (`2 failed`) antes de corregir el script.
- [x] **Cobertura: N/A**, con el motivo que imprime `init.sh`: no hay líneas Python de producción, y PowerShell no se mide.
- [x] **Mutación:** 0 mutantes, con el alcance recalculado, la campaña reejecutada y el control del cero (§5).
- [x] **Muertos comprobados:** la campaña dura menos de 5 minutos y se reejecutó con los mismos totales.
- [x] **Coste por mutante: N/A**, porque no hay ningún mutante de campaña.
- [x] **Supervivientes:**
  - de la campaña, ninguno;
  - a mano, el implementer declara 27/27 muertos;
  - de mis 12 estropeos (§4), sobrevive L2, un límite de la regla que hoy no se da en el script (O-a).
- [x] Las «Evidencias» traen los cuatro números y la simulación.
- [x] Ningún N/A va sin su motivo.
- [x] **Orden (punto 7): N/A**, porque el rigor es `estandar`. Aun así, la simulación comprueba el orden en ejecución:
  - la comprobación del backend va después de subir y antes de las App Settings (S2);
  - la de la lista va antes de confirmar y de borrar (S5).

**C4 ter**
- [x] **N/A**: `harness/rutas_sensibles.json` no existe.

**C5**
- [x] En `tasks.md`, T20, T21 y T22 están `[x]`, y T12 sigue `[ ]` por diseño (humano). Las correcciones van en commits `F-035: …`, la misma práctica que en las rondas anteriores, que ya se aceptó.
- [x] No hay temporales en el árbol. Solo queda sin trackear este informe.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: cambio pedido → test / evidencia

| Cambio de la review 7 | Test | Evidencia en ejecución (§2) |
|---|---|---|
| 1 `backends show` sin `--query`, contado en PowerShell y cerrado si falla | `test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings` | S1, S1b, S2, S2b, S2c, S3 (×6), S3b |
| 2 regla de literales con su control | `…_ningun_argumento_de_az_se_rompe_al_pasar_por_cmd`, `…_control_la_regla_caza_el_defecto_de_la_review_7` | Mis estropeos C1 a C6 (§4) |
| 3 simulación con `.cmd` | — | La del implementer (18/18) y la mía (34/34, con el control en rojo) |
| 4 `-Retirar` comprueba antes de confirmar | `…_nunca_se_reescribe_la_lista_vacia` | S5 y el estropeo C9 |
| Añadido: guarda del secreto | `…_un_secreto_que_cmd_romperia_para_antes_de_escribirse`, `…_los_valores_salen_del_key_vault_y_el_secreto_se_suelta` | X3 (×10) y el estropeo C7 |
| Añadido: guarda de las URL | `…_una_url_de_retorno_que_cmd_romperia_para_antes_de_confirmar` | X4, X5 y el estropeo C8 |

## Observaciones (no bloquean)

- **O-a · La regla de literales no ve las llamadas del tipo `$x = az …`.** `_literales_de` (test, l. ~444) solo reconoce las líneas que **empiezan** por `az` o `swa`, y los `Valor-De-Az @(…)`. Una llamada nueva escrita como asignación, o con el literal metido por una variable, pasa en verde (L2). Hoy la única llamada de esa forma es `$salida = az @Argumentos` (l. 166), que no lleva ningún literal sensible, así que no hay ningún defecto actual. Se cerraría ampliando el patrón a `(?:^|[=(&]\s*)(?:az|swa)\s`.
- **O-b · La guarda del secreto va después de la confirmación.** Sigue estando antes de cualquier escritura, así que el mensaje «no se ha escrito nada» es cierto. Pero el operador ya ha tecleado PUBLICAR. Se podría subir junto a las guardas de la l. 310-331, por coherencia.
- **O-c · La ruta de `swa deploy` no está vigilada.** La ruta del temporal viaja sin comillas si no lleva espacios. Con un `TEMP` que tuviera `&` o `^` sin espacios, el shim `swa.cmd` la rompería. Es teórico: en esta máquina `swa` se resuelve a `swa.ps1`, según el implementer, y el `TEMP` habitual no lleva esos caracteres. Si fallara, `swa deploy` daría un error y el script pararía con 6 antes de las App Settings.
- **O-d · Las guardas son más estrictas de lo necesario.** Incluyen `%` y `!`. `cmd` no reexpande `%` desde `%*`, y `!` solo cuenta con la expansión retardada activada. Sobran en rigor, pero solo pueden hacer parar de más, que es fallar cerrado. Me parece bien que estén, porque la expansión retardada se puede activar por registro.
- **O1 (de la review 7, sigue abierta) · `infra/desplegar_front.ps1:475` (F-010).** Tiene el mismo defecto: `length([?displayName=='swa'])` va sin espacios, así que `$credencialesSwa` sale siempre `$null`. Es de otra feature, y la decide el líder.
- **O2, O3 y O5 (de la review 7):** siguen sin aplicar. No se pidieron en este encargo. O5 (`azure-apps/postventa-incidencias.md`) sigue pendiente de la decisión del líder.

## Propuesta de automejora (para el humano)

Mantengo la de la review 7: la simulación de un script que llama a una CLI que en Windows es un `.cmd` tiene que sustituirla por un envoltorio `.cmd` con la misma estructura, no por una función de PowerShell. Se añaden dos notas, que salen de esta ronda:

1. El envoltorio falso tiene que ser **estricto**. Debe fallar ante cualquier llamada no prevista, o de entorno sin `--environment-name`, y tiene que devolver lo que recibió en las escrituras, para que las comprobaciones del script midan lo que sobrevivió a `cmd.exe`.
2. El `PATH` del hijo debe dejar **inalcanzable** la CLI real, y cada ejecución debe comprobar con `Get-Command` que resuelve a la falsa. Es la única garantía de que una simulación no toca Azure.

Vale para cualquier proyecto con scripts de `infra/` en PowerShell, así que se portaría a `arnes-base`.
