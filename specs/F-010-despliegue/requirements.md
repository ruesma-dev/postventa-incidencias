<!-- specs/F-010-despliegue/requirements.md -->
# F-010 · Despliegue en Azure y tarjeta en el portal — Requisitos (EARS)

> **Objetivo del humano, 2026-08-20**: que **negocio pruebe el circuito
> completo desplegado sin que Sigrid se toque todavía**. La prioridad de esta
> feature se subió por delante de F-008 y F-009 justo para eso.
>
> **Rigor**: `estandar`.
>
> **Lo que esta feature NO hace**: cerrar la incidencia en el ERP (F-008,
> F-009), persistir la cola de revisión (F-019) y recortar los permisos de
> Graph (F-018). Ver §7 de `design.md`.

Cada requisito se traduce a al menos un test o a una verificación
`MANUAL (humano)` con su comando exacto. Las que son manuales se marcan aquí
y se detallan en `tasks.md`.

---

## Bloque A · Los scripts de infraestructura son re-ejecutables

> Es el primer criterio de aceptación de la feature: *«los scripts de `infra/`
> se pueden ejecutar dos veces seguidas sin romper nada»*. Los cuatro scripts
> siguen el estilo ya establecido por `crear_base_postventa.ps1` y
> `verificar_destino_sharepoint.ps1`.

- **R1.** El sistema debe entregar en `infra/` los cuatro scripts de
  PowerShell del despliegue —variables, carga de secretos, backend y front—
  más el de verificación posterior, cada uno con su ruta relativa en la
  primera línea y su bloque de ayuda basada en comentarios.

- **R2.** CUANDO un script de despliegue se ejecuta por segunda vez sobre
  recursos que ya existen, el sistema debe **reutilizarlos** y terminar con
  código de salida `0`, sin crear un recurso duplicado, sin borrar ninguno y
  sin dejar el despliegue a medias.

- **R3.** SI un script de despliegue se invoca con `-WhatIf`, ENTONCES el
  sistema debe imprimir qué recursos crearía o reutilizaría y **no debe
  realizar ninguna llamada de escritura** contra Azure.

- **R4.** MIENTRAS el operador no haya escrito la palabra de confirmación que
  el script le pide, el sistema **no debe crear ni modificar** ningún recurso
  de Azure.

- **R5.** SI un script falla, ENTONCES el sistema debe terminar con un código
  de salida **distinto por causa** (falta de sesión de `az`, falta de una
  herramienta, nombre global ya ocupado, confirmación denegada, fallo del
  despliegue) y con un mensaje que diga qué hacer a continuación.

- **R6.** CUANDO un script termina —bien o mal—, el sistema debe dejar la
  sesión de PowerShell **como estaba**: ninguna variable de entorno creada por
  el script sobrevive a su ejecución, y ningún fichero temporal con contenido
  sensible queda en disco.

- **R7.** El sistema debe declarar los nombres de todos los recursos en **un
  solo fichero** (`infra/00_vars_postventa.ps1`), del que los demás scripts
  leen: cambiar un nombre debe ser cambiar una línea, no buscar por el árbol.

## Bloque B · Ningún secreto, ningún identificador

> Segundo criterio de aceptación: *«ningún secreto en el repositorio: App
> Settings con referencia a Key Vault»*. En este repositorio la regla es más
> dura que «ningún secreto»: tampoco entran **identificadores** (ver
> `test_f006_repo_sin_identificadores.py`, que barre todo el árbol).

- **R8.** El sistema debe mantener los ficheros versionados de `infra/` sin
  ningún valor de secreto, GUID, FQDN de Azure, dirección IP ni identificador
  de suscripción, inquilino o aplicación.

- **R9.** CUANDO el script de secretos recoge una credencial del operador, el
  sistema debe pedirla como `SecureString`, no escribirla en disco y no
  imprimirla en ninguna traza, ni completa ni parcial.

- **R10.** El sistema debe fijar en la Function App **toda** App Setting que
  lleve un secreto o un identificador como **referencia a Key Vault**, nunca
  con el valor literal.

- **R11.** MIENTRAS la identidad gestionada de la Function App no tenga
  permiso de lectura sobre el Key Vault, el sistema debe fallar el despliegue
  con un mensaje que lo diga, en vez de dejar una Function App arrancada que
  no puede resolver sus referencias.

- **R12.** CUANDO el despliegue del front necesita el identificador de
  inquilino que `staticwebapp.config.json` lleva como marcador `<TENANT_ID>`,
  el sistema debe sustituirlo **en una copia de trabajo fuera del
  repositorio**, y el fichero versionado debe quedar intacto con su marcador.

- **R13.** SI el operador interrumpe el despliegue del front después de haber
  preparado la copia de trabajo, ENTONCES el sistema debe borrar esa copia:
  contiene el identificador de inquilino ya sustituido.

## Bloque C · El acceso queda restringido al grupo de Posventa

> Tercer criterio de aceptación. **El grupo de Posventa no existe todavía**:
> crearlo es tarea del humano o de IT (D1 de `design.md` §9), y hasta que
> exista no hay a quién restringir.
>
> Ojo al contraste con el portal: `swa-portal-ruesma` tiene
> `appRoleAssignmentRequired` en falso **a propósito**, porque el portal es
> abierto al inquilino. Aquí es justo al revés.

- **R14.** MIENTRAS un usuario no tenga sesión iniciada en Entra, la Static
  Web App debe responder a cualquier ruta con una redirección al inicio de
  sesión.

- **R15.** MIENTRAS un usuario autenticado en el inquilino **no** pertenezca
  al grupo de Posventa, el sistema debe impedirle el acceso a la aplicación.
  *(Verificación **MANUAL (humano)**: con una cuenta no miembro.)*

- **R16.** El sistema debe exigir asignación previa para iniciar sesión en la
  aplicación empresarial de la Static Web App, y debe asignar a ella el grupo
  de Posventa y **solo** ese grupo.

- **R17.** SI alguien llama a un endpoint de la Function App **por el nombre
  de host de la propia Function**, sin credencial y sin pasar por la Static
  Web App, ENTONCES el sistema debe responder `401` y **no debe ejecutar el
  endpoint**.

- **R18.** El sistema debe mantener `GET /api/health` accesible sin
  autenticación: lo usan el despliegue y el propio front para comprobar que el
  backend responde, y no expone ningún dato.

- **R19.** CUANDO el front llama a `/api/*` desde el mismo origen a través de
  la Static Web App, el sistema debe atender la llamada **sin que el front
  tenga que cambiar**: ni CORS, ni URL de backend, ni adquisición de token en
  el navegador.

## Bloque D · El presupuesto de 45 segundos del proxy

> El proxy de la Static Web App corta cualquier petición a los **45 s**
> (documentado en `azure-apps/portal.md` §9, aprendido con la app de nóminas).
> Hoy `IA_TIMEOUT_S` vale `120` y `TIMEOUT_PETICION_MS` del front vale
> `180000`: **los dos están por encima del corte**. Sin esto, negocio ve
> errores en la extracción y nadie sabe por qué. Es D2 de `design.md` §9.

- **R20.** El sistema debe fijar en el despliegue los tiempos de espera del
  backend (`IA_TIMEOUT_S`, `GRAPH_TIMEOUT_S`) por **debajo** del presupuesto
  del proxy de la Static Web App, con margen para la respuesta.

- **R21.** El sistema debe fijar el tiempo de espera del front
  (`TIMEOUT_PETICION_MS`) por debajo de ese mismo presupuesto, para que sea el
  front quien aborte y reintente y no el proxy quien devuelva un error opaco.

- **R22.** SI una petición del circuito agota su tiempo de espera, ENTONCES el
  front debe tratarla como error **transitorio**, reintentarla según su
  política y liberar su plaza de la cola.

## Bloque E · La tarjeta del portal

> Cuarto criterio de aceptación: *«queda escrito qué hay que cambiar en
> `front-portal/public/assets/js/catalog.js`»*. **La tarjeta se edita en ese
> repositorio, no en este**, y ningún agente de este repositorio la toca.

- **R23.** El sistema debe dejar escrito en este repositorio el **bloque
  exacto** a añadir a `front-portal/public/assets/js/catalog.js`, con todos
  los campos obligatorios del esquema del catálogo (`id`, `title`,
  `description`, `category`, `icon`, `url`, `requiredGroupName`,
  `requiredGroupId`, `comingSoon`).

- **R24.** El sistema debe escribir el identificador del grupo de ese bloque
  como **marcador**, nunca como GUID: un GUID real en este repositorio hace
  fallar el barrido de identificadores, y el valor se rellena en
  `front-portal`.

- **R25.** El sistema debe dejar escrito, junto al bloque, el procedimiento
  completo de alta —crear el grupo, rellenar el GUID, desplegar el portal y
  refrescar el token— **sin suponer quién ejecuta cada paso ni en qué
  repositorio se commitea**.

## Bloque F · Qué queda desplegado, y qué no

> Sexto punto del encargo: el entorno desplegado tiene que ser **útil y
> honesto** sin el cierre en Sigrid.

- **R26.** El sistema debe documentar, en `docs/INTEGRACION.md`, qué expone
  este proyecto una vez desplegado y qué parte del circuito **no** está
  disponible todavía: el cierre en el ERP (F-008, F-009) y la persistencia de
  la remesa y de la cola de revisión (F-019).

- **R27.** CUANDO el despliegue termina, el sistema debe poder comprobarse con
  un script de verificación que consulte `GET /api/health`, compruebe que el
  nombre de host desnudo de la Function responde `401` y compruebe que la
  Static Web App redirige al inicio de sesión, **sin subir nada a ningún
  sitio**.

- **R28.** El sistema debe mantener apagado en el despliegue todo lo que no
  forma parte del piloto: ninguna variable de Sigrid, y `ARCHIVO_HABILITADO`
  encendido **solo** contra la biblioteca de dev del sitio de IT.

## Bloque G · T18 de F-006 se desbloquea aquí

> Efecto lateral declarado en `harness/features.json`: F-010 es quien
> desbloquea **T18 de F-006**, la única subida real a SharePoint, diferida
> desde el 2026-08-19 por decisión del humano (D3 de F-006) porque no había
> entorno desplegado.

- **R29.** CUANDO exista la Function App desplegada y `GET /api/health`
  responda, el sistema debe permitir ejecutar **T18 de F-006** con
  `infra/verificar_archivo_dev.ps1 -BaseUrl <url del despliegue>`, que ya se
  entregó dentro de F-006 y hasta ahora no tenía URL que recibir.
  *(Verificación **MANUAL (humano)**.)*

- **R30.** MIENTRAS T18 de F-006 no se haya ejecutado con su **resultado real
  anotado**, F-006 no debe darse por completa; y su ejecución dentro de F-010
  requiere **autorización expresa del humano** ante `CHECKPOINTS.md` **C5**,
  igual que la que necesitó el cierre de F-006 con T18 pendiente.

- **R31.** SI el listado de la carpeta tras T18 muestra un fichero con sufijo
  `(1)`, ENTONCES el sistema debe **parar** y hablar con el humano: es
  exactamente el fallo que el `acceptance` de F-006 prohíbe.

---

## Trazabilidad · requisito → verificación

| R | Cómo se verifica | Tarea |
|---|---|---|
| R1 | `test_f010_scripts_infra.py` — existen, ruta relativa y `.SYNOPSIS` | T3–T7 |
| R2 | Test de contrato: cada creación va precedida de una comprobación de existencia. **Y** verificación `MANUAL (humano)`: re-ejecutar los dos despliegues | T5, T6, **T17** |
| R3 | Test: los tres admiten `-WhatIf` y con él no hay llamada de escritura | T5–T7 |
| R4 | Test: existe `Read-Host` de confirmación antes de la primera escritura | T5, T6 |
| R5 | Test: hay al menos cinco códigos de salida distintos y ninguno repetido | T5, T6 |
| R6 | Test: ninguna asignación a `$env:` sin su restauración en `finally` | T4–T7 |
| R7 | Test: ningún nombre de recurso literal fuera de `00_vars_postventa.ps1` | T3 |
| R8 | `test_f006_repo_sin_identificadores.py` (ya existe, barre todo el árbol) + test propio de `infra/` | T3–T7 |
| R9 | Test: `Read-Host -AsSecureString` y ningún `Write-Host` del valor | T4 |
| R10 | Test: toda App Setting de la lista de secretos se fija por referencia a Key Vault | T5 |
| R11 | Test: el script concede el rol sobre el Key Vault **antes** de fijar las App Settings y comprueba el resultado | T5 |
| R12 | Test: la sustitución del marcador ocurre sobre una copia y el fichero del repo conserva `<TENANT_ID>` | T6 |
| R13 | Test: la copia de trabajo se borra en un `finally` | T6 |
| R14 | Ya lo fija `staticwebapp.config.json` (F-007); test de que el despliegue no lo pisa. **MANUAL**: abrir la URL sin sesión | T6, **T16** |
| R15 | **MANUAL (humano)**: intento de acceso con cuenta no miembro | **T16** |
| R16 | Test: el script pone `appRoleAssignmentRequired` en cierto y asigna el grupo | T6 |
| R17 | **Fase RED** + `test_f010_r17_los_endpoints_exigen_clave` sobre `function_app.py`. **MANUAL**: llamada al host desnudo | T8, **T14** |
| R18 | `test_f010_r18_health_sigue_anonimo` | T8 |
| R19 | Test: el front no gana ni URL de backend ni CORS; `baseApi` sigue siendo `/api` | T9 |
| R20 | Test: la plantilla de App Settings fija los dos tiempos por debajo del presupuesto | T5 |
| R21 | Test JS: `TIMEOUT_PETICION_MS` por debajo del presupuesto | T9 |
| R22 | Ya cubierto por los tests de reintento de F-007; test de no regresión | T9 |
| R23 | `test_f010_tarjeta_portal.py`: el bloque está y trae los nueve campos | T10 |
| R24 | Mismo test: el `requiredGroupId` es un marcador, y el barrido de GUID en verde | T10 |
| R25 | Mismo test: el procedimiento nombra los cuatro pasos y no fija ejecutor | T10 |
| R26 | Test: `docs/INTEGRACION.md` §8 nombra F-008/F-009 y F-019 como no desplegados | T11 |
| R27 | `test_f010_scripts_infra.py` sobre `verificar_despliegue.ps1`: tres comprobaciones y ninguna escritura | T7 |
| R28 | Test: la plantilla de App Settings no incluye ninguna variable `SIGRID_*` | T5 |
| R29 | **MANUAL (humano)** — T18 de F-006 | **T18** |
| R30 | **MANUAL (humano)** + anotación en `progress/` y autorización ante C5 | **T18** |
| R31 | **MANUAL (humano)**: criterio de parada escrito en la tarea | **T18** |
