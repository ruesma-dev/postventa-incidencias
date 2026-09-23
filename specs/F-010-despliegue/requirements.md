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

> Tercer criterio de aceptación. **D1 resuelta el 2026-08-20**: el humano crea
> él mismo el grupo `posventa-usuarios` con los miembros del piloto. **D3
> resuelta el 2026-08-20**: la protección de la Function App no es una
> credencial en la propia Function —la plataforma no la admite detrás de un
> backend enlazado—, sino **defensa en capas**; el razonamiento completo está
> en `design.md` §9 bis y es de lectura obligada antes de implementar R17 y
> R32.
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

- **R17.** El sistema debe restringir el acceso público de la Function App a
  lo que necesite la Static Web App enlazada, **siempre que resulte compatible
  con el backend enlazado**; y SI al aplicarlo la Static Web App deja de
  alcanzar el backend, ENTONCES el sistema debe revertir la restricción y
  dejar constancia de que esa capa no está disponible.
  *(Verificación **MANUAL (humano)**. Ver `design.md` §9 bis, capa 5: es
  mejora, no cimiento.)*

- **R18.** El sistema debe mantener `GET /api/health` accesible sin
  autenticación: lo usan el despliegue y el propio front para comprobar que el
  backend responde, y no expone ningún dato.

- **R32.** El sistema debe dejar escrito en `function_app.py` **por qué** los
  endpoints permanecen anónimos —lo exige el backend enlazado de la Static Web
  App, que reenvía una cabecera de identidad y no una credencial— y dónde está
  entonces el control de acceso. Un endpoint anónimo que parece un descuido
  acaba «arreglado», y ese arreglo rompe el front sin que ningún test del
  repositorio lo detecte.

- **R33.** El sistema debe desplegar `ARCHIVO_HABILITADO` **apagado**, de
  forma que fuera de la ventana de escritura `POST /api/archivar` responda
  `503` a cualquiera —incluido un desconocido— y no toque SharePoint.

> **Enmienda del 2026-09-23 · la premisa de R33 cayó: el despliegue ya no
> deja las ventanas cerradas, sino abiertas.**
>
> R33 se escribió: *«El sistema debe desplegar `ARCHIVO_HABILITADO`
> **apagado**, de forma que fuera de la ventana de escritura `POST
> /api/archivar` responda `503` a cualquiera —incluido un desconocido— y no
> toque SharePoint.»* Y el 2026-09-03 (hallazgo **H2** de
> `progress/guion_bloque8_F-009.md` §8) se le sumó `CIERRE_HABILITADO`, fijado
> igual en `false` en cada despliegue. Eso describía un piloto: nadie usaba el
> servicio en real, y las ventanas se abrían a mano solo para archivar o cerrar
> de verdad (T18, el bloque 8 de F-009, el bloque 9 de F-012).
>
> **Qué la invalida.** Posventa ya usa el servicio en real, y cada despliegue
> les cerraba el archivo y el cierre hasta que alguien los reabría a mano con
> `infra/22_ventana_archivo.ps1` y `infra/19_ventana_escritura.ps1`: una
> puerta que se cierra sola en cada publicación y que hay que acordarse de
> reabrir deja al usuario sin servicio sin que nadie haya decidido cerrarlo.
>
> **Quién lo decidió.** El humano, el 2026-09-23: *«vamos a desplegar, pero
> quiero que por defecto publique abierto, no cerrado»*, y a la pregunta de qué
> ventanas, *«Las dos»*.
>
> **Lo que dice ahora.** `desplegar_backend.ps1` fija `ARCHIVO_HABILITADO` y
> `CIERRE_HABILITADO` en `true` en cada despliegue, cada una en su línea de
> `$ajustes`, y **las dos** en `false` con el interruptor `-VentanasCerradas`.
> Lo fijan `test_despliegue_ventanas_abiertas_por_defecto_y_cerradas_con_el_switch`
> y su control negativo, en `test_f010_scripts_infra.py`.
>
> **Lo que NO cambia.** (1) El **valor por defecto del código**:
> `config/settings.py` sigue declarando `archivo_habilitado` y
> `cierre_habilitado` con `default=False`, así que en un puesto de trabajo y en
> los tests sigue siendo imposible escribir (R20 de F-006, R37 de F-009, R39 de
> F-012, intactos). (2) La **razón de H2**: cada despliegue sigue fijando las
> dos explícitamente, para que el estado tras publicar lo decida el despliegue y
> no lo que alguien dejó puesto a mano. (3) **R34**: las ventanas se siguen
> abriendo y cerrando cambiando una App Setting, sin redesplegar, y ahora con
> script (`22_…` y `19_…`).
>
> **Riesgo aceptado, y por escrito.** Con la ventana del ERP abierta por
> defecto, **cualquier versión desplegada escribe en Sigrid de producción sin
> una puerta manual**: quedan el dry-run por omisión y la confirmación del
> usuario, pero ya no el gesto de alguien en el plano de gestión. Y **mientras
> F-034 no esté desplegada**, `/api/adjuntar` y `/api/cerrar` siguen tomando el
> número de incidencia **del cuerpo de la petición** (nota del 2026-09-23:
> **desde el despliegue de F-034** dejan de tomar del cuerpo el número de
> incidencia y el estado de archivo, deciden con lo guardado del parte y un
> cuerpo que no cuadre recibe 409 sin llegar al ERP; hasta ese despliegue,
> sigue siendo cierto). Lo que sigue impidiendo
> que un desconocido llegue a escribir no es esta ventana sino la plataforma:
> el host desnudo lo corta Easy Auth y el front exige sesión del grupo de
> Posventa (`docs/DESPLIEGUE.md` §5 bis). Quien no quiera ese riesgo en un
> despliegue concreto lo lanza con `-VentanasCerradas`.
>
> **Consecuencia sobre R27.** La comprobación 2 de `verificar_despliegue.ps1`
> exige la ventana de archivo **cerrada** —con ella abierta no hace la
> llamada, porque subiría un PDF—, así que tras un despliegue por defecto su
> veredicto no sale en verde. No se ha tocado: su guarda sigue siendo correcta,
> y desde el 2026-08-25 esa comprobación tampoco se podía hacer por el host
> desnudo (§5 bis). Queda anotado como pendiente de decisión.
>
> **F-010 sigue `done`**: esto no reabre la feature. Se corrige el texto y se
> deja la constancia, como con R28.

- **R34.** CUANDO haga falta archivar de verdad (T18 o una sesión con
  negocio), el sistema debe permitir abrir y cerrar esa ventana **cambiando
  una App Setting, sin redesplegar y sin tocar código**.

- **R35.** El sistema debe tener fijado un **tope de gasto con alerta** en el
  proveedor de IA antes de exponer `/api/extraer` y `/api/firma`: es la
  defensa proporcionada al riesgo de que un desconocido consuma cuota.
  *(Verificación **MANUAL (humano)**.)*

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
  un script de verificación que, **sin subir nada a ningún sitio**, consulte
  `GET /api/health`, compruebe que `POST /api/archivar` contra el nombre de
  host de la Function responde `503` —la ventana de escritura está cerrada
  (R33)— y compruebe que la Static Web App redirige al inicio de sesión.

- **R28.** El sistema debe mantener fuera de la plantilla de App Settings de
  `desplegar_backend.ps1` **la configuración sensible de Sigrid** —la raíz de
  la pasarela, que es un host interno, y su clave de función—, que viaja
  **por referencia a Key Vault**; y cuando la ventana de escritura de R33 esté
  abierta, el destino debe ser **solo** la biblioteca de dev del sitio de IT,
  nunca el archivo real de Posventa.

> **Enmienda del 2026-09-03 · la premisa original de la primera mitad de R28
> cayó, y este requisito se corrige para que no mienta.**
>
> R28 se escribió: *«El sistema debe mantener fuera del despliegue todo lo que
> no forma parte del piloto: **ninguna** variable de Sigrid; y cuando la
> ventana de escritura de R33 esté abierta, …»*. Eso describía el sistema el
> 2026-08-20, cuando **F-008 y F-009 estaban fuera del piloto** y cualquier
> variable `SIGRID_*` en el despliegue habría sido la primera pieza de un
> cierre en producción que nadie había aprobado.
>
> Hoy no lo describe: **F-009 está implementada y aprobada**, y el humano
> aprobó el 2026-09-03 aprovisionar su configuración en el despliegue. Sin
> ella, `POST /api/cerrar` responde `503` y el bloque 8 de verificación contra
> el ERP no arranca. Es el **hallazgo H1** de
> `progress/guion_bloque8_F-009.md` §8; el detalle, en
> `progress/impl_H1_H2_despliegue.md`.
>
> **Lo que R28 protegía de verdad no ha caído**, y es lo que dice ahora: que la
> configuración sensible no se escriba en un fichero versionado. De las ocho
> variables de F-009, **dos** son sensibles y viajan por referencia a Key
> Vault; las otras seis se fijan en claro en `$ajustes` y sus valores ya
> estaban en el repositorio. `SIGRID_BASE_DATOS` es una de esas seis desde la
> corrección del mismo día: estuvo unas horas como secreto de vault y bajó a
> App Setting plana porque el nombre de la base del ERP ya está escrito en
> `docs/referencia/03_modelo_posventa_sigrid.md` y en
> `specs/F-009-cierre-sigrid/design.md`.
>
> **F-010 sigue `done`**: esto no reabre la feature ni cambia su alcance. Se
> corrige el texto y se deja la constancia, nada más.

## Bloque G · T18 de F-006 se desbloquea aquí

> Efecto lateral declarado en `harness/features.json`: F-010 es quien
> desbloquea **T18 de F-006**, la única subida real a SharePoint, diferida
> desde el 2026-08-19 por decisión del humano (D3 de F-006) porque no había
> entorno desplegado.

- **R29.** CUANDO exista la Function App desplegada y enlazada como backend de
  la Static Web App, el sistema debe permitir ejecutar **T18 de F-006** —la
  única subida real a SharePoint— **solo desde el entorno desplegado y entrando
  por el front**: con sesión iniciada, desde la consola del navegador y contra
  la ruta relativa `/api/archivar`, de modo que la petición viaje por el proxy
  que autentica y no haya ninguna URL que escribir. El procedimiento, con el
  fragmento exacto que se ejecuta, vive en `docs/DESPLIEGUE.md` §5 bis.
  *(Verificación **MANUAL (humano)**.)*

  > **Por qué no por el nombre de host de la Function.** Con el backend
  > enlazado, la plataforma le activa Easy Auth y responde
  > `400 Login not supported for provider azureStaticWebApps` a **toda** ruta,
  > `GET /api/health` incluida: `infra/verificar_archivo_dev.ps1 -BaseUrl` no
  > puede ejecutar T18 por esa vía. El script **no se retira**: sigue valiendo
  > el día que el backend vuelva a ser alcanzable por su host, y su listado de
  > la carpeta en solo lectura no depende del proxy. Lo que hace ahora es
  > **reconocer ese `400`, explicar cuál es la vía buena y salir con un código
  > propio**, en vez de morir con un error opaco.

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
| R17 | **MANUAL (humano)**: se aplica la restricción y se comprueba que la SWA sigue alcanzando el backend; si no, se revierte y se anota | **T14** |
| R18 | `test_f010_r18_health_sigue_anonimo` | T8 |
| R32 | `test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada` | T8 |
| R33 | **Fase RED** + test sobre `desplegar_backend.ps1`: fija `ARCHIVO_HABILITADO` apagado. **Premisa enmendada el 2026-09-23**: las dos ventanas se despliegan abiertas y `-VentanasCerradas` las cierra (`test_despliegue_ventanas_abiertas_por_defecto_y_cerradas_con_el_switch`); ver el recuadro bajo R33 | T5 |
| R34 | Test: el runbook trae las dos líneas de `az` que abren y cierran la ventana | T10 |
| R35 | **MANUAL (humano)**: tope y alerta configurados antes de T16 | **T14 bis** |
| R19 | Test: el front no gana ni URL de backend ni CORS; `baseApi` sigue siendo `/api` | T9 |
| R20 | Test: la plantilla de App Settings fija los dos tiempos por debajo del presupuesto | T5 |
| R21 | Test JS: `TIMEOUT_PETICION_MS` por debajo del presupuesto | T9 |
| R22 | Ya cubierto por los tests de reintento de F-007; test de no regresión | T9 |
| R23 | `test_f010_tarjeta_portal.py`: el bloque está y trae los nueve campos | T10 |
| R24 | Mismo test: el `requiredGroupId` es un marcador, y el barrido de GUID en verde | T10 |
| R25 | Mismo test: el procedimiento nombra los cuatro pasos y no fija ejecutor | T10 |
| R26 | Test: `docs/INTEGRACION.md` §8 nombra F-008/F-009 y F-019 como no desplegados | T11 |
| R27 | `test_f010_scripts_infra.py` sobre `verificar_despliegue.ps1`: tres comprobaciones y ninguna escritura | T7 |
| R28 | Test: la plantilla de App Settings no escribe las **dos** variables sensibles de Sigrid, y las `SIGRID_*` que sí fija son exactamente las cinco que pueden versionarse (`test_f010_r28_la_configuracion_sensible_de_sigrid_no_se_escribe_aqui`). **Premisa enmendada el 2026-09-03**: ver el recuadro bajo R28 | T5 |
| R29 | **MANUAL (humano)** — T18 de F-006 por la consola del front, `docs/DESPLIEGUE.md` §5 bis. **Y** test de contrato: `test_f010_scripts_infra.py` — `verificar_archivo_dev.ps1` reconoce el `400` de Easy Auth, dice cuál es la vía buena y no muere con un error opaco | **T18** |
| R30 | **MANUAL (humano)** + anotación en `progress/` y autorización ante C5 | **T18** |
| R31 | **MANUAL (humano)**: criterio de parada escrito en la tarea | **T18** |
