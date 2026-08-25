<!-- specs/F-010-despliegue/tasks.md -->
# F-010 · Despliegue en Azure y tarjeta en el portal — Tareas

> Cada tarea es **un commit** (`F-010 Tn: ...`). Ordenadas por dependencia.
>
> **Diez tareas son `MANUAL (humano)`**: T1, T2, T13, T14, T14 bis, T15, T16,
> T17, T18 y T19. Un agente no crea grupos en el inquilino, no despliega en
> Azure, no sube nada a SharePoint y no toca otro repositorio.
>
> **El humano trabaja en PowerShell**: cada tarea manual se entrega como
> *script + una línea corta de invocación*. Sin `&&`, sin comandos largos
> multilínea, porque se parten al pegarlos.
>
> **Precondición de toda la fase 2 en adelante**: `feature/F-007-front`
> cerrada y mergeada (riesgo 4 de `design.md` §10).
>
> **Estado de las bloqueantes al 2026-08-20**: **D1 resuelta** (el humano crea
> el grupo, nombre `posventa-usuarios`) y **D3 resuelta** (`design.md` §9 bis:
> defensa en capas; el `auth_level` **no** se toca). **Queda D2**, los 45 s del
> proxy contra los tiempos de espera actuales: **T2 es su paso previo y sigue
> bloqueando la fase 2**.

---

## Fase 0 · Lo que el humano tiene que resolver antes

- [x] **T1 · MANUAL (humano) · D1 RESUELTA el 2026-08-20** — Crear el **grupo
      de seguridad de Posventa** en Entra con los miembros del piloto dentro.
      El humano lo hace él mismo y **da por bueno el nombre
      `posventa-usuarios`**. Sin el grupo no hay a quién restringir el acceso
      (R15, R16) ni qué poner en la tarjeta (R24).

      **Confirmar el nombre antes de aplicarlo**: si al crearlo el humano
      elige otro, ese nombre es el que va en la asignación de la aplicación
      empresarial (T6, T16) y en `requiredGroupName` de la tarjeta (T10, T19).
      Los tres sitios tienen que decir lo mismo.

      Crear el grupo y quedarse con su Object ID:

      ```
      az ad group create --display-name "posventa-usuarios" --mail-nickname "posventa-usuarios" --query id -o tsv
      ```

      Añadir a cada persona del piloto, de una en una:

      ```
      az ad group member add --group "posventa-usuarios" --member-id <objectId-del-usuario>
      ```

      **El Object ID no se pega en este repositorio**, ni en un commit, ni en
      `progress/`, ni en un chat: es un GUID y el barrido de identificadores
      lo caza. Se guarda donde el humano guarda los suyos.

      **Verificación**: `MANUAL (humano)` — el grupo aparece y lista a sus
      miembros:

      ```
      az ad group member list --group "posventa-usuarios" --query "[].userPrincipalName" -o tsv
      ```

- [x] **T2 · MANUAL (humano) · ALIMENTA D2** — Medir, **en local y sin
      desplegar nada**, cuánto tardan de verdad las tres llamadas caras del
      circuito con un parte real de `muestras/`. Es lo que dice si el piloto
      cabe en el presupuesto de 45 s del proxy (`design.md` §5).

      Con la Function arrancada (`func start --port 7073` en la carpeta del
      servicio) y el front en la otra terminal, se abre F12 → Red, se procesa
      **una remesa real** y se anotan los tiempos de `/api/split`,
      `/api/extraer` y `/api/firma`.

      **Verificación**: `MANUAL (humano)` — quedan anotados en `progress/` los
      tres tiempos: el peor caso observado de cada endpoint. **Sin nombres de
      obra, sin códigos de incidencia y sin DNI**: solo los segundos.

      **Criterio de decisión**: si el peor `/api/extraer` queda holgadamente
      por debajo de 35 s, se sigue con la opción (a) de D2. Si no, **PARAR** y
      llevar a D2 la elección entre (b) y (c). No se despliega «a ver si
      cuela».

## Fase 1 · Los scripts de infraestructura

> Los cinco se prueban como ya se probaron los de F-005 y F-006: un test que
> los **lee como texto** y comprueba su contrato. Ninguno se ejecuta desde la
> suite, ninguno abre una conexión.

- [x] **T3**: `infra/00_vars_postventa.ps1`, fuente única de nombres de
      recurso, región y tags (R7), más `infra/*.local.ps1` en `.gitignore`.
      **Verificación**: `test_f010_scripts_infra.py` — el fichero existe,
      empieza por su ruta relativa, declara los diez nombres de `design.md`
      §2, no lleva ningún GUID, FQDN ni IP (R8), y **ningún otro script del
      despliegue repite un nombre de recurso literal**.

- [x] **T4**: `infra/cargar_secretos_postventa.ps1` — crea o reutiliza
      `kv-postventa-dev` y sube los once secretos de `design.md` §3.
      **Verificación**: `test_f010_scripts_infra.py` — pide cada credencial
      con `Read-Host -AsSecureString` (R9), no imprime ningún valor, no
      escribe ficheros, no deja variables de sesión (R6), admite `-WhatIf`
      (R3) y trae confirmación escrita antes de la primera escritura (R4).

- [x] **T5 · FASE RED en R33**: `infra/desplegar_backend.ps1`. Primero se
      escribe el test que exige que el script deje `ARCHIVO_HABILITADO`
      **apagado** y **se le ve fallar** (aún no hay script); después el
      script. Es el candado principal de D3 (`design.md` §9 bis, capa 3) y por
      eso es el requisito que lleva la fase RED de esta feature.
      **Verificación**: `test_f010_scripts_infra.py` — cada `create` va
      precedido de una comprobación de existencia (R2); el rol sobre el Key
      Vault se concede **antes** de fijar las App Settings y se verifica
      (R11); toda App Setting de la lista de secretos se fija por **referencia
      a Key Vault** y ninguna con valor (R10); `IA_TIMEOUT_S` y
      `GRAPH_TIMEOUT_S` quedan por debajo del presupuesto (R20); **ninguna
      variable `SIGRID_*`** (R28); **`ARCHIVO_HABILITADO` apagado** (R33);
      `-WhatIf` (R3); confirmación (R4); y al
      menos cinco códigos de salida distintos, todos únicos (R5).

- [x] **T6**: `infra/desplegar_front.ps1`, con modo `-SoloFront`.
      **Verificación**: `test_f010_scripts_infra.py` — pone
      `appRoleAssignmentRequired` en cierto y asigna el grupo (R16); registra
      **todas** las redirect URI en una sola llamada; el cuerpo de la llamada
      a Graph va por **fichero temporal**, no inline; la sustitución de
      `<TENANT_ID>` ocurre sobre una **copia de trabajo** y el fichero del
      repositorio conserva su marcador (R12); esa copia se borra en un
      `finally` (R13); `-SoloFront` no toca ni Entra ni el secreto; `-WhatIf`
      y confirmación.

- [x] **T7**: `infra/verificar_despliegue.ps1` — las tres comprobaciones de
      R27, **solo lecturas**.
      **Verificación**: `test_f010_scripts_infra.py` — no contiene ningún
      verbo de escritura (`create`, `update`, `delete`, `set`, `PUT`, `POST`
      contra Azure), exige la URL por parámetro como hace
      `verificar_archivo_dev.ps1`, y comprueba las tres cosas: `200` en
      `/api/health`, `503` en `/api/archivar` con la ventana de escritura
      cerrada (R33) y redirección al
      inicio de sesión en la Static Web App.

## Fase 2 · Los dos cambios de código

- [x] **T8** — Fijar por escrito que la anonimidad es **deliberada** (R32,
      R18). **El `auth_level` NO se toca**: `design.md` §9 bis explica por qué
      cambiarlo rompería el front, y esta tarea existe justamente para que
      nadie lo cambie luego creyendo que corrige un descuido.

      Se actualiza la cabecera de `function_app.py` —qué reenvía el backend
      enlazado, por qué no cabe una credencial en la Function, y dónde está
      entonces el control de acceso— y se escribe
      `test_f010_endpoints_protegidos.py`.

      **Verificación**: `test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada`
      (los seis endpoints siguen anónimos **y** la cabecera lo explica: si
      alguien cambia una cosa sin la otra, falla) y
      `test_f010_r18_health_sigue_anonimo`.

- [x] **T9**: `TIMEOUT_PETICION_MS` de `services/postventa-front/js/config.js`
      al presupuesto del proxy (R21), con el comentario que explica de dónde
      sale el número y que enlaza a `design.md` §5.
      **Verificación**: `tests_js/test_config_timeout.test.js` — el valor está
      por debajo del presupuesto, y `baseApi` **sigue siendo** `/api` (R19: el
      front no gana ni URL de backend ni CORS).

## Fase 3 · La documentación que es entregable

- [x] **T10**: `docs/DESPLIEGUE.md` — el runbook (qué crea cada script, en qué
      orden, qué hace falta antes) y **el bloque literal de la tarjeta del
      portal** con su procedimiento de cuatro pasos (R23, R25).
      Incluye además las **dos líneas de `az`** que abren y cierran la ventana
      de escritura (R34), y dice que se cierra siempre al terminar.
      **Verificación**: `test_f010_tarjeta_portal.py` — el bloque trae los
      **nueve** campos del esquema de `azure-apps/portal.md` §4.1; el
      `requiredGroupId` es un **marcador** y no un GUID (R24); el
      procedimiento nombra los cuatro pasos y **no fija quién los ejecuta**; y
      el documento repite los dos avisos del portal (marcador sin rellenar =
      tarjeta velada, y logout/login + `Ctrl+F5` tras el alta).

- [x] **T11**: `docs/INTEGRACION.md` — rellenar §8 «Qué exponemos nosotros»,
      que hoy está vacía y dice que se rellena en este trabajo, y añadir la
      fila del despliegue (R26).
      **Verificación**: `test_f005_integracion_sin_secretos.py` **en verde**
      (lee `design.md` §10, riesgo 5, antes de escribir: los nombres van en
      tabla, nunca como asignación) y un test nuevo que comprueba que §8
      nombra F-008/F-009 y F-019 como **no desplegados**.

- [x] **T12**: `docs/ARCHITECTURE.md` §«Infra y despliegue» — los nombres de
      recurso, la restricción de región y el presupuesto de 45 s.
      **Verificación**: `bash harness/init.sh` en verde y el barrido de
      identificadores sin hallazgos.

## Fase 4 · Ejecución del despliegue · MANUAL (humano)

> Antes de nada: `az login` y la suscripción correcta seleccionada.
>
> ~~Los cinco scripts se copian fuera del repositorio antes de ejecutarlos,
> como se hizo en F-006, para no ensuciar el árbol de trabajo:
> `copy infra\*.ps1 $HOME\`~~ → **RECTIFICADO EL 2026-08-25, tras
> ejecutarlo**: **solo se copian fuera los que funcionan fuera**.
>
> `desplegar_backend.ps1` y `desplegar_front.ps1` deducen la raíz del
> repositorio con `$raiz = Split-Path -Parent $PSScriptRoot` para encontrar
> `services\`; copiados a `$HOME` esa cuenta da `C:\Users` y no encuentran
> nada que publicar. **Se ejecutan desde `infra\`**, y no ensucian el árbol:
> el front hace su copia de trabajo en el directorio temporal del sistema.
>
> Los que sí se copian son los que no dependen de la raíz
> —`cargar_secretos_postventa.ps1` y `verificar_despliegue.ps1`, que solo
> necesitan `00_vars_postventa.ps1` al lado—:
>
> ```
> copy infra\00_vars_postventa.ps1 $HOME\
> copy infra\cargar_secretos_postventa.ps1 $HOME\
> copy infra\verificar_despliegue.ps1 $HOME\
> ```
>
> Es el **defecto 1** de los doce de la jornada del 2026-08-21. El detalle,
> en `docs/DESPLIEGUE.md` §2.

- [x] **T13 · MANUAL (humano)** — Cargar los secretos en el Key Vault. Se
      ejecuta **una vez**, y se repite solo cuando rote una credencial.

      Ver antes qué haría, **sin tocar nada**:

      ```
      powershell -ExecutionPolicy Bypass -File $HOME\cargar_secretos_postventa.ps1 -WhatIf
      ```

      Ejecutarlo de verdad:

      ```
      powershell -ExecutionPolicy Bypass -File $HOME\cargar_secretos_postventa.ps1
      ```

      **Verificación**: `MANUAL (humano)` — ~~el script lista los **nombres**
      de los **once** secretos cargados y ningún valor. Se anota en
      `progress/` solo «once secretos cargados: sí/no»~~ →
      **RECTIFICADA EL 2026-08-25, tras ejecutarla**: el script lista los
      **nombres** de los **nueve** secretos del backend cargados y ningún
      valor. Se anota en `progress/` solo «**nueve** secretos cargados:
      sí/no».

      **El criterio anterior era imposible de cumplir.** Los dos secretos
      que faltan hasta once, `swa-client-id` y `swa-client-secret`, **los
      crea y los guarda `desplegar_front.ps1`** (T16) cuando genera el
      registro de aplicación: aquí todavía no existen, y teclearlos a mano
      es inventar dos valores que el despliegue del front sobrescribe. La
      partición está en `infra/00_vars_postventa.ps1`
      (`$PostventaSecretosBackend` / `$PostventaSecretosFront`) y el porqué,
      en `docs/DESPLIEGUE.md` §2.

      Es el **defecto 2** de los doce de la jornada del 2026-08-21
      (`progress/impl_F-010.md`). **La casilla `[x]` no se toca**: la tarea
      se ejecutó y su resultado real —«9 de 11 cargados»— es el correcto; lo
      que estaba mal era el enunciado. Mismo precedente que T8 y T19 de
      `specs/F-006-sharepoint/tasks.md`.

- [x] **T14 · MANUAL (humano) · APLICA D3** — Desplegar el backend.

      **Desde `infra\`, no desde `$HOME`** (ver la nota de la fase): el
      script busca `services\postventa-api` relativo a su propia ubicación.

      ```
      powershell -ExecutionPolicy Bypass -File .\infra\desplegar_backend.ps1
      ```

      **Verificación**: `MANUAL (humano)`, cuatro cosas y en este orden:

      1. `GET /api/health` responde `200` a través del nombre de host de la
         Function.
      2. Las App Settings resuelven sus referencias a Key Vault: ninguna
         aparece con error en el portal de Azure.
      3. **`POST /api/archivar` contra el host desnudo responde `503`** —la
         ventana de escritura está cerrada (R33)—. Si respondiera `200`,
         **PARAR**: el script no dejó `ARCHIVO_HABILITADO` apagado y la
         Function está escribiendo en SharePoint a cualquiera que la llame.
      4. **Capa 5 de `design.md` §9 bis, y es un intento, no un requisito**:
         aplicar la restricción de acceso público a la Function App y
         comprobar **después de T16** que la Static Web App sigue alcanzando
         el backend. SI el front deja de funcionar, **revertir** y anotar que
         la capa 5 no está disponible (R17): las capas 1, 3 y 4 se sostienen
         solas.

      El resultado se anota en `progress/` **sin la URL y sin ningún
      identificador**: «health 200: sí/no», «referencias resueltas: sí/no»,
      «archivar cerrado devuelve 503: sí/no», «restricción de red aplicada:
      sí / revertida».

- [x] **T14 bis · MANUAL (humano)** — Fijar **tope de gasto y alerta** en la
      consola del proveedor de IA antes de que el front sea alcanzable (R35).
      Es la defensa proporcionada al riesgo de que un desconocido llame a
      `/api/extraer` (`design.md` §9 bis, capa 4), y no depende de Azure.
      **Verificación**: `MANUAL (humano)` — queda anotado «tope fijado: sí/no»
      y «alerta configurada: sí/no». **Sin la cifra**, que es información de
      negocio.

- [ ] **T15 · MANUAL (humano) · RESUELVE D4** — Comprobar que la Function App
      alcanza `psql-albaranes-rs9k2`. **Solo lectura primero**: mirar si el
      servidor ya admite servicios de Azure. Si hiciera falta una regla nueva,
      **PARAR**: es un cambio a nivel de servidor compartido, lo decide el
      humano y se coordina con albaranes (`CLAUDE.md`).
      **Verificación**: `MANUAL (humano)` — una llamada a `/api/archivar` deja
      su traza en el esquema `postventa`, o queda anotado que D4 sigue abierta
      y que el archivo no persiste traza todavía.

- [x] **T16 · MANUAL (humano)** — Desplegar el front y probar el acceso.

      **Desde `infra\`, no desde `$HOME`** (ver la nota de la fase): el
      script busca `services\postventa-front` relativo a su propia ubicación.

      ```
      powershell -ExecutionPolicy Bypass -File .\infra\desplegar_front.ps1
      ```

      **Verificación**: `MANUAL (humano)`, con **dos cuentas**:

      1. Sin sesión, la URL redirige al inicio de sesión (R14).
      2. Con una cuenta **miembro** del grupo: entra y el circuito funciona.
      3. Con una cuenta **no miembro** del grupo: **no entra** (R15). Si
         entrara, `appRoleAssignmentRequired` no está aplicado y **se para**.

      Se anota en `progress/` «miembro entra: sí/no», «no miembro entra:
      sí/no». **Sin la URL.**

- [ ] **T17 · MANUAL (humano) · CRITERIO DE ACEPTACIÓN** — Re-ejecutabilidad.
      Volver a lanzar los **dos** despliegues, seguidos, sin borrar nada y
      **desde `infra\`** (ver la nota de la fase):

      ```
      powershell -ExecutionPolicy Bypass -File .\infra\desplegar_backend.ps1
      ```

      ```
      powershell -ExecutionPolicy Bypass -File .\infra\desplegar_front.ps1 -SoloFront
      ```

      **Verificación**: `MANUAL (humano)` — los dos terminan con código `0`,
      no aparece ningún recurso duplicado en `rg-postventa-dev`, y **el inicio
      de sesión sigue funcionando** después (R2). Este último punto es el que
      importa: es exactamente lo que rompió el portal cuando un despliegue
      completo regeneró el secreto y pisó una redirect URI. Por eso el
      segundo va con `-SoloFront`.

## Fase 5 · Lo que F-010 desbloquea

- [ ] **T18 · MANUAL (humano) · ES T18 DE F-006 · REQUIERE AUTORIZACIÓN
      EXPRESA** — La **única subida real a SharePoint** de todo el proyecto,
      diferida desde el 2026-08-19 (D3 de F-006, opción (a)) esperando
      justamente este entorno. Ahora ya hay `-BaseUrl` que pasarle.

      **Antes de ejecutarla hay que pedir autorización al humano**, y no es
      una formalidad: `CHECKPOINTS.md` **C5** exige `tasks.md` con todas las
      tareas `[x]`, F-006 se cerró con esta casilla vacía por una dependencia
      declarada, y quien la marque está cerrando una feature ajena. La
      autorización se pide **nombrando C5** y se anota con fecha.

      **Esta tarea abre y cierra la ventana de escritura** (R33, R34,
      `design.md` §9 bis capa 3). Los dos `az` van sueltos, uno por línea.

      **Abrir la ventana**, justo antes de ejecutar:

      ```
      az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=true
      ```

      El script ya existe desde F-006; aquí solo se ejecuta:

      ```
      copy infra\verificar_archivo_dev.ps1 $HOME\
      ```

      ```
      powershell -File $HOME\verificar_archivo_dev.ps1 -BaseUrl <url-de-dev>
      ```

      **Cerrar la ventana en cuanto termine**, salga bien o mal:

      ```
      az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=false
      ```

      Dejarla abierta «por si acaso» es exactamente lo que D3 evita: mientras
      esté abierta, `/api/archivar` escribe en SharePoint para cualquiera que
      llame a la Function.

      Para ver antes qué haría, sin llamar a nada:

      ```
      powershell -File $HOME\verificar_archivo_dev.ps1 -WhatIf
      ```

      **Verificación**: `MANUAL (humano)`. Parte **sintético** (obra `0677`,
      incidencia `RS26.08/0001`, los dos inventados). Se da por verificada si
      y solo si:

      - primera llamada `200`, con el nombre
        `0677 - RS26.08 - 0001 PARTE FIRMADO.pdf` y carpeta `Postventa/0677`;
      - segunda llamada `200`, **mismo destino** que la primera;
      - listado de la carpeta: **un solo elemento**, y **ningún** nombre con
        sufijo `(1)`.

      **SI aparece un `(1)`, es una PARADA** (R31): se habla con el humano
      antes de seguir. Es el fallo que el `acceptance` de F-006 prohíbe y no
      se arregla con más tests.

      El resultado real se anota en `progress/` **el día que se ejecute**, sin
      la URL, sin el identificador del elemento y sin ningún GUID. Solo
      entonces se marca `[x]` la casilla T18 de `specs/F-006-sharepoint/tasks.md`.

- [ ] **T19 · MANUAL (humano) · OTRO REPOSITORIO** — La tarjeta del portal.
      **Ningún agente de este repositorio la toca** (`design.md` §8, D7). El
      bloque exacto y el procedimiento están en `docs/DESPLIEGUE.md`, que es
      el entregable de F-010; esta tarea es aplicarlo, y admite **dos vías sin
      suponer cuál**: que lo haga el humano en `front-portal`, o que entregue
      el bloque a quien lleve ese repositorio.

      Los cuatro pasos, según `azure-apps/portal.md` §8.2:

      1. Pegar el bloque en `front-portal/public/assets/js/catalog.js`.
      2. Sustituir el marcador de `requiredGroupId` por el Object ID real del
         grupo de T1. **Ese GUID vive en `front-portal`, nunca aquí.**
      3. Desplegar el portal, desde su repositorio:

         ```
         .\deploy.ps1 -SoloFront
         ```

      4. `Ctrl+F5` en el navegador, y pedir a los usuarios del grupo
         `/.auth/logout` y volver a entrar para que su token traiga el grupo.

      **Verificación**: `MANUAL (humano)` — un miembro del grupo ve la tarjeta
      **en color** y le abre la aplicación; un no miembro la ve **velada** con
      «Sin acceso». Si sale velada para todos, el marcador no se rellenó
      (`design.md` §8).

## Fase 6 · Cierre

- [x] **T20**: Campaña de mutación y análisis de supervivientes.
      **Verificación**: `python -m harness.mutacion --feature F-010`.
      **Alcance real, dicho por adelantado**: la herramienta solo muta Python,
      y tras resolverse D3 **F-010 no cambia ni una línea de comportamiento en
      Python** — T8 quedó en cabecera y test. Lo que esta feature entrega son
      cinco scripts de PowerShell, un cambio en JS y documentación, todo fuera
      de lo que la campaña sabe mutar. Su disciplina la sostienen los tests de
      contrato de la fase 1, los tests JS y la fase RED de T5. Si la campaña
      sale sin nada que mutar, **se declara N/A con este motivo por escrito**
      en `progress/impl_F-010.md`: `CHECKPOINTS.md` acepta el N/A justificado
      y rechaza el N/A a secas.

- [x] **T21**: Ejecutar `bash harness/init.sh` en verde.

---

## Estado de las verificaciones manuales

| Tarea | Depende de | Estado |
|---|---|---|
| T1 | **D1 resuelta**: el humano crea el grupo `posventa-usuarios` | Pendiente de ejecutar; ya no bloquea |
| T2 | Un parte real de `muestras/` y la Function en local (**D2**) | **BLOQUEA la fase 2** |
| T13 | T1, y los secretos en poder del humano | Pendiente |
| T14 | T13 · aplica **D3** (capas 3 y 5) · la capa 5 se comprueba tras T16 | Pendiente |
| T14 bis | Consola del proveedor de IA · capa 4 de **D3** | Pendiente, **antes de T16** |
| T15 | T14 · resuelve **D4**; puede quedar abierta sin bloquear el piloto | Pendiente |
| T16 | T1 y T14 | Pendiente |
| T17 | T14 y T16 · **criterio de aceptación** | Pendiente |
| T18 | T14 · **autorización expresa ante C5** · abre y **cierra** la ventana de escritura · cierra T18 de **F-006** | Pendiente |
| T19 | T1, T16 y **D7** · otro repositorio | Pendiente |
