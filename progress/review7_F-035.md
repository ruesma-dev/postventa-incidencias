<!-- progress/review7_F-035.md -->
# F-035 · Review 7 · Bloque 6 (T20, T21, T22)

- **Veredicto:** CHANGES_REQUESTED (RECHAZADO)
- **Rango revisado:** `485e60c..2d46bab`, rama `feature/F-035-portal-posventa`. Lo anterior ya se aprobó en la review 6.
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige fase RED, cobertura de las líneas cambiadas y campaña de mutación con los supervivientes analizados.
- **Fecha:** 2026-09-26.

> No he ejecutado nada contra Azure ni contra Entra. Todas las pruebas se han hecho en copias desechables dentro del scratchpad. El árbol de trabajo sigue limpio (`git status` vacío), salvo este informe. No he tocado el código del implementer.

## Resumen

T21 está bien. La versión de las hojas y la enmienda (e) de R59 funcionan, y la guardia caza lo que tiene que cazar. El test de identidad de las piezas duplicadas también funciona: cae en rojo en los 14 cambios que he probado, en cualquiera de los dos scripts. `desplegar_front.ps1` y los tests de F-010 no han cambiado.

En `publicar_maqueta.ps1` no he encontrado ningún camino que toque producción, ni ninguno que pierda las URL de retorno de producción. **Pero el camino bueno no puede terminar nunca.** La comprobación del backend del entorno pasa a `az` la consulta `length(@)` sin comillas. `az` en Windows es `az.cmd`, y sus paréntesis rompen el bloque `IF ( … )` de ese envoltorio: `cmd` falla con «No se esperaba -o en este momento» y termina con salida 255. Así, `Backends-Del-Entorno` devuelve **siempre** `$null` y el script para con el código 9 en todas las ejecuciones:

- **Entorno nuevo:** para después de subir los estáticos. Deja el entorno a medias, sin App Settings, y el humano tiene que lanzar `-Retirar`.
- **Entorno que ya existía:** para en la comprobación previa.

El fallo es cerrado, así que no es inseguro, pero el script no cumple su objetivo. Además, el humano lo va a ejecutar contra Azure y siempre acabaría con un entorno a medias. La simulación del implementer no lo vio porque sustituía `az` por una **función** de PowerShell, y una función no pasa por `cmd.exe`.

## 1 · `infra/publicar_maqueta.ps1`, línea a línea

### 1.1 · Producción: ningún camino la toca [x]

- `production` no aparece en ningún sitio del texto. `swa deploy` solo se llama con `--env maqueta` (l. 394).
- `backends link` no aparece. El script solo hace `backends show`, y siempre con `--environment-name maqueta` (l. 198).
- Todas las llamadas `az staticwebapp environment|appsettings|backends` llevan `--environment-name maqueta`:
  - `environment show` (l. 192) y `environment delete` (l. 314);
  - `appsettings set` y los dos `appsettings list` (l. 425, 428, 429);
  - `backends show` (l. 198).

  Lo exige también `test_f035_t20_toda_llamada_con_entorno_nombra_maqueta`.
- En la CLI, `environment delete/show` y `backends show` tienen `default` como valor por defecto de `--environment-name`, y `default` es producción. Por eso nombrar el entorno es obligatorio, y el script lo nombra siempre.
- El token de despliegue sirve para toda la Static Web App. Lo que decide el destino es `--env`, que está fijo en `maqueta`.
- `$hostProduccion` solo se lee.

### 1.2 · URL de retorno: nunca se pierden las de producción [x]

- **Publicar:**
  - Lee `web.redirectUris` (l. 265).
  - Si no puede leerla o sale vacía, para con el código 12 antes de la confirmación y antes de escribir nada (l. 295).
  - Reescribe con `@($retornos) + $nuevoRetorno` en **una** llamada (l. 445-446). PowerShell pasa el array como argumentos separados; lo confirma la traza P3 del implementer.
  - Vuelve a leer la lista y comprueba que están todas (l. 451-456).
  - Si la URL ya estaba registrada, no reescribe nada (l. 441).
- **Retirar:**
  - Quita solo lo que casa con `^https://[^/]+-maqueta\.[^/]+/\.auth/login/aad/callback$`. El host por defecto de producción no lleva `-maqueta.`, y el test cubre cinco casos que no deben casar.
  - Si no quedaría ninguna, para con el código 12 **sin reescribir** (l. 323).
  - Después vuelve a leer la lista y comprueba que no falta ninguna y que no queda ninguna de `maqueta` (l. 334-340).
- La aplicación cuya lista se toca se coteja antes con el `swa-client-id` del Key Vault. Si no coincide, para con el código 8 (l. 249). Así no se puede reescribir la lista de otro registro.

### 1.3 · `-Retirar` solo borra `maqueta` [x]

- La única llamada destructiva sobre la Static Web App es `environment delete --environment-name maqueta --yes`, y solo si el entorno existe (l. 314).
- No desenlaza backends ni borra App Settings de producción.

### 1.4 · Secretos: no se imprimen ni se escriben [x]

- `$appId`, `$clientId`, `$inquilino`, `$secreto` y el token no aparecen en ningún `Write-Host`. Lo verifica un test, y lo he comprobado a mano.
- Las salidas de `appsettings set`, `ad app update` y `environment delete` van a `Out-Null`. Las lecturas pasan por `Valor-De-Az`, que no imprime.
- El token va por `SWA_CLI_DEPLOYMENT_TOKEN`: se lee antes del `try` y se restaura en el `finally`.
- La copia con el inquilino sustituido se borra en el `finally`.
- El secreto va en la línea de comandos de `appsettings set`, igual que en `desplegar_front.ps1`. El informe lo declara como riesgo aceptado.

### 1.5 · Las comprobaciones en ejecución paran antes de dejar nada a medias: **[ ]**

- **Host:** se lee y se comprueba que lleva `-maqueta.` y que no es el de producción (l. 402-406). Está antes de las App Settings. [x]
- **Backend:** la posición es correcta, después de subir y antes de las App Settings (l. 410). Lo que falla es la llamada, que **no funciona nunca** (ver 1.6). [ ]
- **App Settings:** tras fijarlas se vuelven a leer del entorno y se comparan en memoria (l. 428-436). Esto va antes de la URL de retorno. [x]
- **`-Retirar`:** borra el entorno **antes** de comprobar si `$quedan` quedaría vacía. En el escenario R3 del implementer queda el entorno borrado y la URL de retorno registrada, con salida 12. No es peligroso, pero se puede comprobar antes de la confirmación, igual que `$retornos.Count`. Ver el cambio 4, que es una recomendación.

### 1.6 · Defecto bloqueante: `length(@)` no sobrevive a `az.cmd`

El `az.cmd` de la instalación MSI, leído en esta máquina en `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`, es este:

```
@IF EXIST "%~dp0\..\python.exe" (
  SET AZ_INSTALLER=MSI
  "%~dp0\..\python.exe" -IBm azure.cli %*
) ELSE (
```

Windows PowerShell 5.1 solo entrecomilla los argumentos que llevan espacios, así que `length(@)` llega a `cmd` sin comillas. Al expandirse `%*` dentro del bloque, el `)` cierra el `IF`.

Para reproducirlo monté una réplica exacta de ese envoltorio (`scratchpad\fakeaz\az.cmd`, con un `eco.py` en vez de `python -m azure.cli`). Después cargué la `Valor-De-Az` **real** del script con su AST y llamé a los argumentos de `Backends-Del-Entorno`:

```
--- staticwebapp backends show --name x --query length(@) -o tsv
az : No se esperaba -o en este momento.
exit=255
Backends-Del-Entorno devolveria: [] es null: True
```

Como control, una consulta con espacios pasa entera, porque PowerShell sí la entrecomilla:

```
ARGS=['webapp', 'config', '--query', "[?name=='X'].value | [0]", '-o', 'tsv', '--only-show-errors']
exit=0
```

Consecuencia: `(Backends-Del-Entorno) -ne "0"` se cumple siempre y el script para con el código 9 en todas las ejecuciones (ver el resumen).

El mismo defecto está latente en `infra/desplegar_front.ps1:475` (`length([?displayName=='swa'])`), así que `$credencialesSwa` sale siempre `$null`. Eso es de F-010 y no entra en esta review: ver la observación O1.

### 1.7 · Afirmaciones sobre Azure, contrastadas con la documentación que cita el informe

| Afirmación | Documentación (consultada hoy) | ¿Cuadra? |
|---|---|---|
| `environment delete` sin `--environment-name` borra `default` | az staticwebapp environment: `--environment-name` «Default value: default»; `--yes` existe | Sí |
| `backends show` tiene `--environment-name` con valor por defecto `default` | az staticwebapp backends: sí, «Default value: default» | Sí |
| `appsettings set/list` admiten `--environment-name` | az staticwebapp appsettings: sí, con ejemplos por entorno. **No documenta valor por defecto**, a diferencia de `environment` y `backends` | Sí. El docstring del test generaliza «sin él usa `default`», pero da igual porque el script lo pasa siempre |
| El portal dice que las variables se crean por entorno, y la misma página dice que «se copian» | Configure application settings: «You can create variables per environment» y «Are copied to staging and production environments» | Sí. La duda está bien planteada, y comprobarlo en ejecución es la respuesta correcta |
| `--web-redirect-uris` reemplaza la lista | La CLI solo dice «Space-separated values». Que reemplaza se sabe por la experiencia del repositorio (rompió el portal) y por la semántica PATCH de Graph | El script asume el peor caso: correcto |
| `swa deploy --env` (por defecto `preview`), token por `SWA_CLI_DEPLOYMENT_TOKEN`, `--no-use-keychain` | Documentación de swa deploy: literal | Sí |
| El host de un entorno con nombre es `<DEFAULT_HOST_NAME>-<nombre>.<LOCATION>.azurestaticapps.net` | Named environments: literal | Sí. El patrón de retirada y la comprobación `-maqueta.` casan con ese formato |

## 2 · Test de identidad de las piezas duplicadas (copia desechable)

Script `scratchpad\identidad_rev7.py`. Copia `infra/` y el test en un directorio temporal, cambia **una** pieza en **uno** de los dos scripts y ejecuta el test. El original sale en verde (30 passed).

| Cambio | Resultado |
|---|---|
| `Salir-Con` en `desplegar_front` / en `publicar_maqueta` | ROJO / ROJO (`…[Salir-Con]`) |
| `Existe-Herramienta` en uno / en otro | ROJO / ROJO |
| `Valor-De-Az` en uno / en otro | ROJO / ROJO |
| `Id-De-Aplicacion` en uno / en otro | ROJO / ROJO |
| `Existe-StaticWebApp` en uno / en otro | ROJO / ROJO |
| Lista de exclusiones: una más en `desplegar_front` / una menos en `publicar_maqueta` | ROJO / ROJO (`…la_lista_de_lo_que_no_se_publica_es_identica`) |
| Marcador `<TENANT_ID>` cambiado en `desplegar_front` | ROJO |
| Un solo espacio de más dentro de `Valor-De-Az` de `desplegar_front` | ROJO |
| *Fuera del alcance declarado:* quitar el `Remove-Item` del bucle de exclusiones en `publicar_maqueta` | VERDE (ver O2) |

Resultado: 14 de 14 cambios dentro del alcance de la enmienda caen en rojo. El test vive en la suite de la raíz, que no usa caché, así que un cambio en `desplegar_front.ps1` también lo dispara.

## 3 · T21: versión en las URL de las hojas y enmienda (e) de R59

- **Versión.** La recalculé por mi cuenta (SHA-256 de `css/styles.css` y `css/portal.css`, con los finales de línea normalizados) y sale `3c19075344`, la misma que llevan `index.html` (l. 18-19) y `partes.html` (l. 17).
- **`partes.html`.** En el rango cambia **una sola línea**: el `href` de su hoja, que pasa de `css/styles.css` a `css/styles.css?v=3c19075344`. [x]
- **Mutantes a mano** (`scratchpad\t21_rev7.py`, sobre una copia del front):

| Mutante | Resultado |
|---|---|
| N1 la guardia no mira cuántos atributos | ROJO (control «un atributo más») |
| N2 la guardia admite una versión hex de cualquier longitud | **VERDE** (ver O3) |
| N3 la guardia admite cualquier hoja de `css/` | ROJO (control «la versión en otra hoja») |
| N4 la versión no incluye `portal.css` | ROJO |
| N5 `partes.html` con otra versión | ROJO (2 tests) |
| N6 `index.html` sin versión en `portal.css` | ROJO (2 tests) |
| N7 se cambia una hoja sin tocar la URL | ROJO (2 tests) |
| N8 atributo extra en la `<link>` de `partes.html` | ROJO |

- **Suite del front.** Con `-k "t21 or r59 or r50 or r9"` sobre el repositorio real salen 28 passed, incluido el test de rama de R59.

## 4 · F-010 intacto

- `git diff --name-only dev...HEAD` no incluye `infra/desplegar_front.ps1` ni ningún `test_f010_*`, y `git log dev..HEAD` sobre esas rutas sale vacío. [x]

## 5 · Campaña del arnés y control del cero

- **Alcance.** `alcance_de_feature('F-035')` da `lineas={}` (origen `rama`, `54c0884..feature/F-035-portal-posventa`). El rango solo cambia PowerShell, HTML, Markdown y tests.
- **Reejecución.** El informe declara «Tiempo total 0.0 s», así que reejecuté la campaña: `python -m harness.mutacion --feature F-035 --salida <scratchpad>/mutacion_rev7.md`. Salen 0 mutantes, 0 muertos, 0 supervivientes, 0 timeouts y 0.0 s, los mismos totales que el informe. `git status` quedó limpio.
- **Control del cero.** Pasé `generar_mutantes` por las líneas del diff de los dos ficheros Python del rango, ignorando la exclusión. Salen 89 mutantes en `tests/test_f035_publicar_maqueta.py` y 42 en `test_f035_portal.py`. El generador funciona, y el cero se debe a la exclusión de los tests, que es por diseño.

## Checkpoints

**C1**
- [x] `bash harness/init.sh`: exit 0, ENTORNO LISTO. Raíz 103 passed; api y front desde la caché; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`.
- [x] Existen los ficheros del arnés.

**C2**
- [x] Una sola feature `in_progress` (F-035).
- [x] La rama es `feature/F-035-portal-posventa`.
- [x] `current.md` tiene la entrada del bloque 6 y remite al informe. Sigue acumulando bloques anteriores (deuda O-2 de la review 1, no bloquea).
- [x] `history.md` no cambia. No hay ninguna feature `done` nueva.

**C3**
- [x] Hexagonal: **N/A**. El rango solo toca un script de `infra/`, HTML estático, tests y documentación, y nada de eso tiene capas.
- [x] La primera línea con la ruta está en `publicar_maqueta.ps1` y en `test_f035_publicar_maqueta.py`. El script es ASCII, CRLF y sin BOM (lo cubre un test).
- [x] Sin prints de depuración, sin TODO, sin secretos, sin GUID ni hosts ni IP en el texto (barrido del test y lectura mía). Sin dependencias nuevas.
- [x] Checkpoints de dominio (parte, firma, `conest`, Sigrid, archivo): **N/A**. Nada del rango toca el pipeline. La maqueta se publica sin backend, así que no puede escribir en Sigrid ni en SharePoint.
- [x] Ningún PDF ni parte escaneado en git.

**C3 bis**
- [x] **N/A**: el rango no toca `docs/referencia/`.

**C4**
- [x] Cada tarea del bloque tiene tests trazables: `test_f035_t20_*` (30) y `test_f035_t21_*` / `test_f035_r59_t21_*` (11). Todos pasan.
- [x] Los tests unitarios no tocan red ni BBDD. El de T20 solo lee el texto del script.
- [ ] **Que el script haga lo que se le pide no está verificado, y de hecho no lo hace** (§1.6). Ningún test ni la simulación pasan los argumentos por `cmd.exe`, así que el camino bueno de T20 («comprueba que el entorno no tiene backend y sigue») no puede completarse en Windows. Es el motivo del rechazo.
- [x] Verificaciones MANUAL: el guion del humano está en `impl_F-035.md` §8. **T12 (V1 y V2 del humano) sigue pendiente**, por diseño.

**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] **Fase RED**, aceptada con nota:
  - T21 trae la traza real (4 failed antes de la enmienda).
  - En T20, el script se escribió antes que los tests. El implementer lo declara y lo compensa con dos cosas: la traza con el script apartado (29 failed) y 20 mutantes a mano del script, todos muertos.
  - He reproducido la parte que importa, el test de identidad (§2).
- [x] **Cobertura: N/A** con el motivo impreso por `init.sh`: no hay líneas Python de producción.
- [x] **Mutación:** 0 mutantes, con el alcance recalculado, la campaña reejecutada y el control del cero (§5).
- [x] **Muertos comprobados:** la campaña se reejecutó porque dura menos de 5 minutos, y dio los mismos totales.
- [x] **Coste por mutante: N/A**, porque no hay ningún mutante de campaña.
- [x] **Supervivientes:**
  - de la campaña, ninguno;
  - a mano, los 20 de T20 y los 6 de T21 del implementer están muertos;
  - de los míos sobreviven N2 de T21 (O3, equivalente a nivel de suite) y el cambio fuera de alcance de §2 (O2).
- [x] Las «Evidencias» traen los cuatro números y los workers no hacen falta, porque no hay campaña con mutantes.
- [x] Ningún N/A va sin su motivo.
- [x] **Orden (punto 7): N/A.** El rigor es `estandar`. Aun así, el orden subida → backend → App Settings → URL de retorno lo fija `test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings` y los tests que le siguen, y lo he revisado en el código.

**C4 ter**
- [x] **N/A**: `harness/rutas_sensibles.json` no existe.

**C5**
- [x] En `tasks.md`, T20, T21 y T22 están `[x]`, con los commits `F-035 T20:`, `F-035 T21:` y `F-035 T22:`. T12 sigue `[ ]` por diseño (humano).
- [x] No hay temporales en el árbol. Solo queda sin trackear este informe, que dejo para el líder.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: tarea → test

| Tarea / punto | Test |
|---|---|
| T20 (a) solo `--env maqueta`, nunca producción | `test_f035_t20_sube_solo_al_entorno_maqueta`, `…_ni_production_ni_backends_link_en_todo_el_texto`, `…_toda_llamada_con_entorno_nombra_maqueta` |
| T20 (b) App Settings del Key Vault, sin imprimir, comprobadas en el entorno | `…_los_valores_salen_del_key_vault_y_el_secreto_se_suelta`, `…_las_app_settings_se_comprueban_en_el_entorno_despues_de_fijarlas`, `…_no_imprime_identificadores_ni_secretos` |
| T20 (c) URL de retorno añadida sin quitar ninguna | `…_cada_reescritura_de_la_lista_va_entera_y_se_comprueba`, `…_nunca_se_reescribe_la_lista_vacia`, `…_el_registro_de_la_lista_es_el_del_key_vault` |
| T20 (d) sin backend, o para | `…_sin_backend_o_para_y_antes_de_las_app_settings`, `…_si_el_entorno_ya_existe_se_mira_su_backend_antes_de_subir`. **Sin cobertura de que la llamada funcione** (cambio 2) |
| T20 (e) `-WhatIf`, confirmación, resumen | `…_whatif_y_confirmacion_antes_de_la_primera_escritura`, `…_cada_causa_tiene_su_codigo_y_dice_que_hacer`, `…_la_consola_queda_como_estaba` |
| T20 `-Retirar` | `…_el_borrado_del_entorno_nombra_maqueta_y_no_pregunta_dos_veces`, `…_retirar_solo_quita_las_de_maqueta`, `…_nunca_se_reescribe_la_lista_vacia` |
| T20 opción B (identidad) | `…_cada_funcion_duplicada_es_identica_a_la_de_desplegar_front` (×5), `…_la_lista_de_lo_que_no_se_publica_es_identica`, `…_el_marcador_del_inquilino_es_el_mismo_y_se_comprueba`, `…_control_la_identidad_caza_una_copia_cambiada` |
| T21 versión con una sola fuente | `test_f035_t21_cada_pagina_pide_sus_hojas_con_la_version_de_su_contenido` (×2), `…_la_version_es_la_misma_en_las_dos_paginas`, `…_control_la_version_cambia_con_cada_hoja_y_no_con_los_finales_de_linea` |
| R59 (e) | `test_f035_r59_t21_la_guardia_admite_la_version_en_la_hoja_del_circuito`, `test_f035_r59_t21_control_la_guardia_rechaza_todo_lo_demas` (×6) |

## Cambios requeridos

1. **`infra/publicar_maqueta.ps1:198` (`Backends-Del-Entorno`).** Hay que quitar `"--query", "length(@)"`, o cualquier otro argumento de `az` que lleve `( ) & | < > ^` sin espacios, porque `cmd.exe` lo rompe al pasar por `az.cmd` (§1.6). Una opción:
   - pedir `backends show … --environment-name maqueta -o json` sin `--query`;
   - contar en PowerShell con `ConvertFrom-Json` (`@($lista).Count`);
   - si la lectura falla o el JSON no se puede interpretar, tratarlo como «tiene backend», que es fallo cerrado, igual que ahora.

   **No hay que tocar `Valor-De-Az`**, porque es pieza duplicada con test de identidad. Hay que cambiar solo `Backends-Del-Entorno`, que es propia del script.
2. **`tests/test_f035_publicar_maqueta.py`.** Falta un test que habría cazado esto: ningún literal de argumento de `az` del script (en los `@(…)` de `Valor-De-Az` y en las llamadas directas) puede contener `(`, `)`, `&`, `|`, `<`, `>` o `^` si no lleva también un espacio, que es lo que hace que PowerShell lo entrecomille. Tiene que ir con su control: el texto actual con `length(@)` tiene que dar rojo. Ajustad también `test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings:213`, que hoy **exige** el `length(@)` defectuoso.
3. **Evidencia.** Volved a ejecutar la simulación de T20 (al menos P3, P4, P5, P8 y R2) con `az` sustituido por un **envoltorio `.cmd` con la misma estructura que `az.cmd`** (bloque `IF ( … )` con `%*`), no por una función de PowerShell. Pegad la salida en `impl_F-035.md`. Con una función no se puede ver cómo llegan los argumentos a `az`. Sirve de modelo el mío, en `scratchpad\fakeaz\az.cmd`.
4. *(Recomendado, no bloqueante por sí solo.)* **`infra/publicar_maqueta.ps1:321-326`.** En `-Retirar`, calculad `$quedan` y comprobad `$quedan.Count -eq 0` **antes de la confirmación**, junto a la comprobación de `$retornos.Count` de la l. 295. Así el script para antes de borrar el entorno y no deja «entorno borrado, URL registrada» con salida 12.

## Observaciones (no bloquean)

- **O1 · `infra/desplegar_front.ps1:475` (F-010).** Tiene el mismo defecto: `length([?displayName=='swa'])` va sin espacios, así que `$credencialesSwa` sale siempre `$null` en el resumen. Esa línea no es pieza duplicada, así que el cambio 1 no la afecta. Es de otra feature: que el líder decida si abre una corrección. **No se toca en F-035.** Las demás consultas de `infra/` con metacaracteres llevan espacios (`| [0]`) y PowerShell las entrecomilla, así que funcionan.
- **O2 · Identidad de la copia de trabajo.** La identidad cubre las cinco funciones, la lista de exclusiones y el marcador, que es lo que pide la enmienda. El resto del procedimiento duplicado no está cubierto: el `Remove-Item` del bucle, el `Copy-Item` y el `Replace`. Quitar el `Remove-Item` en `publicar_maqueta` sigue en verde. Se puede ampliar si se quiere.
- **O3 · Guardia R59 (e), N2.** Si la guardia admite una versión hex de cualquier longitud, sus controles no lo ven: no hay ningún estropeo con hex de longitud distinta de 10. A nivel de suite es equivalente, porque `test_f035_t21_cada_pagina_pide_sus_hojas…` exige la versión exacta en la página real. Se puede añadir un estropeo `?v=0123` si se quiere.
- **O4 · Interacción con `desplegar_front.ps1`.** En modo completo, ese script reescribe la lista de retorno con `https://<prod>/…callback` + `$RedirectExtra` (l. 390-391). Un redespliegue completo de producción con la maqueta publicada **quitaría** la URL de `maqueta`. Falla cerrado (la maqueta deja de dejar entrar), pero conviene una línea en `docs/DESPLIEGUE.md` §10.
- **O5 · `azure-apps/postventa-incidencias.md`.** Queda pendiente la decisión del líder. La superficie expuesta no cambia hasta que el humano publique, pero la regla de `CLAUDE.md` dice «en el mismo trabajo».

## Propuesta de automejora del protocolo (para el humano)

Propongo añadir a `CHECKPOINTS.md` (C4), o a la sección de scripts de `infra/` de `docs/CONVENTIONS.md`, esta regla:

> «Un script PowerShell que llama a `az` (u otra CLI que en Windows es un `.cmd`) y se ha validado con una simulación exige que la simulación sustituya la CLI por un envoltorio `.cmd` con la misma estructura, no por una función de PowerShell: una función no pasa por `cmd.exe` y oculta los fallos de paso de argumentos.»

Origen: esta review. El defecto de §1.6 pasó 30 tests, 20 mutantes y 15 escenarios simulados. Vale para cualquier proyecto con scripts de `infra/` en PowerShell, así que habría que portarla a `arnes-base`.
