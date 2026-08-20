<!-- specs/F-010-despliegue/design.md -->
# F-010 · Despliegue en Azure y tarjeta en el portal — Diseño

> **Rigor**: `estandar`. **Rama**: `feature/F-010-despliegue`.
>
> **Ni un valor real en este documento**: nombres de recurso y nombres de
> variable, nunca FQDN, GUID, identificador de suscripción, inquilino, sitio
> o aplicación. Lo vigila `test_f006_repo_sin_identificadores.py`, que barre
> **todo el árbol**.

---

## 0 · Dónde está el riesgo de esta feature

F-010 no añade lógica de negocio: coge un servicio que hoy solo corre en la
máquina de quien lo desarrolla y lo pone **en internet**. El riesgo no es que
no funcione; es que funcione **de más**.

Tres cosas cambian de naturaleza el día del despliegue:

1. **La Function App queda expuesta.** Los seis endpoints de
   `function_app.py` están hoy en `auth_level=ANONYMOUS`, lo cual es correcto
   mientras solo escuchen en `localhost:7073`. Publicados, cualquiera que
   sepa el nombre de host puede llamarlos. Y uno de ellos, `POST /api/archivar`,
   **escribe en SharePoint**: en el entorno desplegado `ENTORNO` vale `dev` y
   `ARCHIVO_HABILITADO` está encendido, así que las dos puertas que impiden
   subir desde local están abiertas por diseño. Un desconocido podría subir
   PDF arbitrarios a la biblioteca de Posventa y gastar la cuota de Gemini con
   `/api/extraer`. **Esto lo crea F-010, y F-010 tiene que cerrarlo** (R17).
2. **Los secretos dejan de estar en un `.env` de un portátil** y pasan a un
   Key Vault. Es una mejora, pero el camino entre los dos —el script que los
   carga— es el sitio con más probabilidad de acabar con una credencial en un
   log, en un fichero temporal o en el historial de PowerShell (R9, R6).
3. **La aplicación empieza a escribir de verdad con los permisos amplios de
   Graph** que F-018 todavía no ha recortado. Ver §7.

## 1 · Lo que se ha leído en `azure-apps/` antes de diseñar nada

Regla de `CLAUDE.md`: se consulta el ecosistema antes de cruzar la frontera
del proyecto. Esto es lo que se ha reutilizado en vez de inventarlo.

| De dónde | Qué se reutiliza |
|---|---|
| `portal.md` §6.4 | **El patrón exacto de esta feature ya existe**: la app de Nóminas es una Static Web App en `westeurope` más una Function App en `spaincentral` (Flex Consumption). No se inventa una arquitectura nueva |
| `portal.md` §9 | **Las restricciones de plataforma**: la Static Web App **no existe en `spaincentral`**; y el proxy de la SWA corta a los **45 s**. Las dos condicionan este diseño (§4, §5) |
| `portal.md` §6.2, §8 | SKU **Standard** de la SWA, `deploy.ps1` re-ejecutable con modo `-SoloFront`, y la lección de que regenerar el secreto de cliente invalida el anterior |
| `portal.md` §9 | `az ad app update --web-redirect-uris` **reemplaza la lista completa**: hay que registrar siempre todas las URI de una vez. Y `az rest --body` inline se rompe en PowerShell: el cuerpo va en fichero temporal |
| `partes.md` §5.1 | Convención de nombres (`rg-<proyecto>-dev`, `kv-`, `id-`, `log-`, `st`), grupo de recursos **propio**, **Key Vault propio** por proyecto, identidad gestionada para resolverlo, y los **tags obligatorios de la política `acens`** |
| `partes.md` §5.2 | Qué se **reutiliza** de otros grupos de recursos y qué no: `psql-albaranes-rs9k2` vive en `rg-albaranes-dev` y no es nuestro |
| `albaranes.md` §1 | La contraseña de PostgreSQL viaja como **referencia a Key Vault**, no como valor |
| `portal.md` §4.1, §8.2 | El esquema de una entrada del catálogo y el checklist de alta de una app nueva |

**Lo que este diseño hace distinto del portal, y por qué**: el portal tiene
`appRoleAssignmentRequired` en falso, porque es abierto a todo el inquilino.
Aquí va en **cierto** y con el grupo de Posventa asignado (R16). Quien copie
`deploy.ps1` del portal sin leer esto abrirá la aplicación a la empresa
entera.

## 2 · Qué recursos se crean (nombres, no valores)

Grupo de recursos **propio**, como `partes`. Región `spaincentral`, salvo la
Static Web App, que allí no existe.

| Recurso | Nombre | Región | Notas |
|---|---|---|---|
| Grupo de recursos | `rg-postventa-dev` | `spaincentral` | Propio. No se toca `rg-albaranes-dev` ni `rg-partes-dev` |
| Function App | `func-postventa-dev` | `spaincentral` | Plan **Flex Consumption**, runtime Python 3.12, igual que la de nóminas |
| Cuenta de almacenamiento | `stpostventadev` | `spaincentral` | La que exige toda Function App. Sin colas ni contenedores propios: este servicio no encola nada |
| Key Vault | `kv-postventa-dev` | `spaincentral` | **Propio** (§3) |
| Identidad gestionada | `id-postventa-dev` | `spaincentral` | Asignada por el usuario; es quien lee el Key Vault |
| Log Analytics | `log-postventa-dev` | `spaincentral` | |
| Application Insights | `appi-postventa-dev` | `spaincentral` | `host.json` ya trae su bloque de muestreo |
| Static Web App | `swa-postventa-ruesma` | `westeurope` | SKU **Standard**: el enlace de un backend propio lo exige. Sin dominio propio: se usa el nombre de host que asigna Azure |
| App registration | `Postventa Incidencias` | — | Inicio de sesión del front. **Distinto** del de Graph (§3) |
| Grupo de seguridad | `posventa-usuarios` | — | **No existe: hay que crearlo** (D1) |

**Nombres globalmente únicos.** `func-`, `st` y `kv-` compiten con todo Azure.
`00_vars_postventa.ps1` declara un `$Sufijo` vacío; si un nombre está ocupado
el script **falla con código propio** y dice al operador que fije el sufijo en
`00_vars_postventa.local.ps1` (no versionado). No se inventa un sufijo aquí.

**Tags obligatorios** (política `acens`, `partes.md` §5.1): `acens-customer`,
`acens-environment`, `acens-project`, `acens-responsable-so-app`. Van en el
fichero de variables; el del responsable es una variable, no un literal.

**Lo que se reutiliza y no se crea**: `psql-albaranes-rs9k2` (de
`rg-albaranes-dev`), el sitio de SharePoint de IT y el app registration de
Graph que ya existe. Ninguno se toca a nivel de recurso.

## 3 · Los secretos: Key Vault propio y referencias

### Por qué un Key Vault propio y no `kv-albaranes-rs9k2`

Se ha considerado reutilizar el que ya existe. **Se descarta**, por cuatro
razones, y la primera es la que decide:

1. **`kv-albaranes-rs9k2` vive en el grupo de recursos de otro proyecto.**
   Meter secretos ahí es la misma clase de acto que ejecutar DDL fuera de
   nuestro esquema en el PostgreSQL compartido: funciona, y es exactamente lo
   que `CLAUDE.md` prohíbe.
2. **El ecosistema ya decidió esto**: `partes` no reutilizó el de albaranes,
   se creó `kv-partes-pt7m3`. Hacer lo contrario aquí sería la excepción.
3. **Radio de daño**: una asignación de rol mal puesta sobre un Key Vault
   compartido expone los secretos de albaranes y de partes.
4. **Ciclo de vida**: cuando este proyecto se retire, su Key Vault se borra
   con su grupo de recursos.

### Por qué un app registration nuevo para el inicio de sesión

Ya existe el app registration `postventa-incidencias`, el que archiva en
SharePoint con identidad **de aplicación** (client credentials) y que **hoy
tiene permisos sobre todos los sitios del inquilino** hasta que F-018 los
recorte. Reutilizarlo para el inicio de sesión interactivo del front juntaría
en una sola identidad la credencial de mayor privilegio del proyecto y la
aplicación con la que se loguean los usuarios. Se crea uno **nuevo**,
`Postventa Incidencias`, de un solo inquilino, y sus dos identidades quedan
separadas. Es además lo que hace el portal (`Portal Ruesma` es suyo y de nadie
más).

### Qué entra en el Key Vault

Van al Key Vault **los secretos y también los identificadores**. Un
identificador no es una credencial, pero en este repositorio tampoco puede
viajar por un parámetro de script ni por un fichero versionado, así que el
sitio donde no molesta es el mismo.

| Nombre del secreto | Qué guarda | Alimenta a |
|---|---|---|
| `pg-host` | Servidor de PostgreSQL | `PG_HOST` |
| `pg-user` | Rol de aplicación | `PG_USER` |
| `pg-password` | Contraseña del rol | `PG_PASSWORD` |
| `gemini-api-key` | Clave de Gemini | `GEMINI_API_KEY` |
| `graph-tenant-id` | Inquilino | `GRAPH_TENANT_ID` |
| `graph-client-id` | Aplicación de Graph | `GRAPH_CLIENT_ID` |
| `graph-client-secret` | Secreto de esa aplicación | `GRAPH_CLIENT_SECRET` |
| `sharepoint-site-id` | Sitio de IT | `SHAREPOINT_SITE_ID` |
| `sharepoint-drive-id` | Biblioteca de dev | `SHAREPOINT_DRIVE_ID` |
| `swa-client-id` | Aplicación del inicio de sesión | App Setting de la SWA |
| `swa-client-secret` | Su secreto de cliente | App Setting de la SWA |

Las App Settings de la Function App que consumen los nueve primeros se fijan
como **referencia a Key Vault** resuelta por `id-postventa-dev` (R10). Las
demás variables —las que no identifican ni autentican— van con su valor: son
las que `.env.example` ya lleva en claro.

**Una limitación que se declara en vez de esconderse**: las App Settings de
una Static Web App **no admiten referencia a Key Vault**. `AZURE_CLIENT_ID` y
`AZURE_CLIENT_SECRET` (los dos nombres que `staticwebapp.config.json` ya
espera) se fijan con su valor, leído del Key Vault en tiempo de despliegue y
canalizado sin pasar por una variable imprimible ni por disco. El valor acaba
en el almacén de secretos de la propia Static Web App, que es lo que
`docs/CONVENTIONS.md` llama «secretos como secrets del recurso». Es lo mismo
que hace el portal.

## 4 · Cómo se conectan front y backend: backend enlazado

El front ya está escrito para esto y **no cambia**: `config.js` fija
`baseApi: "/api"`, y `dev_server.py` existe precisamente para reproducir en
local el mismo origen que da la Static Web App (su cabecera lo dice: *«el
proxy del dev_server y la Function enlazada a la SWA se comportan igual»*).

```
Usuario  ──►  swa-postventa-ruesma  (westeurope, Standard)
              │  auth de Entra (staticwebapp.config.json, ya escrito en F-007)
              │  /* y /api/* exigen rol "authenticated"
              │  backend enlazado
              ▼
              func-postventa-dev  (spaincentral, Flex Consumption)
              │  App Settings → referencias a kv-postventa-dev
              │  identidad id-postventa-dev
              ├──►  Gemini              (extracción y firma)
              ├──►  Microsoft Graph     (archivo en la biblioteca de dev)
              └──►  psql-albaranes-rs9k2  (traza del archivo)
```

**Funciones gestionadas de la Static Web App: descartadas.** Tienen un tope de
petición muy por debajo de lo que tarda una llamada multimodal y no encajan
con el `functionTimeout` de cinco minutos de `host.json`. Backend enlazado es
además lo que documenta el ecosistema para la app de nóminas.

**El salto entre regiones es deliberado y tiene coste**: la SWA está en
`westeurope` porque en `spaincentral` no existe, y la Function en
`spaincentral` porque ahí está el PostgreSQL. Ese salto se paga en latencia y
se descuenta del presupuesto de §5.

## 5 · El presupuesto de 45 segundos

`azure-apps/portal.md` §9 lo llama «límite duro de 45 s del proxy de SWA», y
lo escribió quien lo sufrió con la app de nóminas. Contra ese tope, lo que
este proyecto tiene hoy configurado:

| Dónde | Variable | Valor hoy | ¿Cabe en 45 s? |
|---|---|---|---|
| Backend | `IA_TIMEOUT_S` | 120 | **No** |
| Backend | `GRAPH_TIMEOUT_S` | 60 | **No** |
| Backend | `functionTimeout` (`host.json`) | 5 min | No aplica: es el techo de la Function, no del proxy |
| Front | `TIMEOUT_PETICION_MS` | 180000 | **No** |

Si se despliega tal cual, una extracción lenta la corta el proxy y el usuario
ve un error opaco que ni el front ni el backend han generado. Por eso:

- **`IA_TIMEOUT_S` y `GRAPH_TIMEOUT_S` bajan a 35 s** en el despliegue (R20),
  dejando unos segundos para el salto de región y la respuesta.
- **`TIMEOUT_PETICION_MS` baja a 40000** (R21): quien aborta es el front, que
  sabe reintentar y liberar la plaza de la cola, no el proxy.
- **Antes de fijar esos números se mide** (T2): cuánto tarda de verdad
  `/api/split`, `/api/extraer` y `/api/firma` con un parte real, en local. Si
  35 s no bastan, el piloto no cabe detrás del proxy y hay que decidir (D2).

**No se elige aquí** el patrón asíncrono (encolar y consultar) que
`portal.md` §9 apunta como salida: es una feature nueva, no un despliegue.

## 6 · Ficheros

### 6.1 A crear

| Ruta | Qué es |
|---|---|
| `infra/00_vars_postventa.ps1` | **Fuente única** de nombres de recurso, región y tags. Se carga por punto (`. .\00_vars_postventa.ps1`) desde los demás. Ni un secreto, ni un identificador. Admite `00_vars_postventa.local.ps1` (no versionado) para el sufijo y la suscripción |
| `infra/cargar_secretos_postventa.ps1` | Crea o reutiliza `kv-postventa-dev` y sube los once secretos, pedidos uno a uno con `Read-Host -AsSecureString`. No imprime valores, no escribe ficheros |
| `infra/desplegar_backend.ps1` | Grupo de recursos, almacenamiento, Log Analytics, Application Insights, identidad gestionada, rol de lectura sobre el Key Vault, Function App, App Settings (referencias) y publicación del código |
| `infra/desplegar_front.ps1` | App registration + aplicación empresarial con asignación obligatoria y el grupo asignado, redirect URI, Static Web App, App Settings, sustitución del marcador en copia de trabajo, enlace del backend y `swa deploy`. Modo `-SoloFront` |
| `infra/verificar_despliegue.ps1` | Solo lecturas: `/api/health`, `401` en el host desnudo de la Function, redirección al inicio de sesión en la SWA. No sube nada |
| `docs/DESPLIEGUE.md` | El runbook: qué crea cada script, en qué orden se ejecutan, qué hace falta antes, y **el bloque literal de la tarjeta del portal** con su procedimiento |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | Contrato de los cinco scripts, como ya se hizo en F-005 y F-006: se leen como texto, no se ejecutan |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | R17 y R18 sobre `function_app.py` |
| `services/postventa-api/tests/test_f010_tarjeta_portal.py` | R23, R24 y R25 sobre `docs/DESPLIEGUE.md` |
| `services/postventa-front/tests_js/test_config_timeout.test.js` | R21 sobre `config.js` |

### 6.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | `auth_level` pasa de `ANONYMOUS` a `FUNCTION` en `split`, `extraer`, `firma`, `validar` y `archivar`. **`health` se queda anónimo** (R18). Se actualiza la cabecera del módulo, que hoy dice que `/api/health` no tiene autenticación —y seguirá siendo verdad— pero calla que las demás sí |
| `services/postventa-front/js/config.js` | `TIMEOUT_PETICION_MS` al presupuesto del proxy, con el comentario que explica de dónde sale el número |
| `docs/INTEGRACION.md` | §8 «Qué exponemos nosotros», hoy vacía y con una nota que dice «cuando el portal muestre la tarjeta (F-010)… esta sección se rellena en el mismo trabajo». Es este trabajo. Se añade además la fila del despliegue |
| `docs/ARCHITECTURE.md` | §«Infra y despliegue»: los nombres de recurso reales, el presupuesto de 45 s y la restricción de región |
| `.gitignore` | `infra/*.local.ps1` |
| `harness/features.json` | Estado de F-010 y, si el humano lo autoriza, el de F-006 al ejecutarse T18 |

### 6.3 Ficheros que NO se tocan (los que tientan)

| Ruta | Por qué no |
|---|---|
| `services/postventa-front/staticwebapp.config.json` | Ya está escrito y es correcto. El marcador `<TENANT_ID>` **se queda** (R12): se sustituye en una copia de trabajo |
| `services/postventa-api/host.json` | El `functionTimeout` de cinco minutos no es el límite que aprieta |
| `services/postventa-front/dev_server.py` | El desarrollo local no cambia porque haya despliegue |
| `services/postventa-api/.env.example`, `local.settings.json.example` | Son la configuración **local**. El despliegue no añade variables nuevas: usa las mismas con otro origen |
| `infra/crear_base_postventa.ps1`, `pruebas_bbdd_efimera.ps1` | De F-005 y ya ejecutados |
| `infra/verificar_archivo_dev.ps1` | **Se ejecuta** en T18, no se modifica: ya se entregó con `-BaseUrl` esperando esta feature |
| `front-portal/**` | **Otro repositorio.** Ningún agente de este repo lo edita (§8) |
| `azure-apps/postventa_incidencias.md` | Otro repositorio, y el humano no commitea ahí (decisión del 2026-08-20, T19 de F-006). La fuente de verdad es `docs/INTEGRACION.md` |

### 6.4 SQL

**Ninguno.** F-010 no crea ni altera tablas. El DDL idempotente de F-005 se
aplica solo al arrancar el servicio, dentro del esquema propio `postventa`, y
eso ya está diseñado y probado. Lo que sí hay que comprobar es que la Function
App **alcanza** el servidor (§9, D4).

## 7 · Qué queda desplegado, y qué no

Lo que **negocio verá** en el piloto:

- Soltar un PDF, un ZIP o elegir una carpeta con una remesa de partes.
- El troceado parte a parte, con su progreso.
- La extracción de campos y la clasificación de la firma.
- El semáforo de validación, con los campos de baja confianza destacados.
- La corrección manual de lo dudoso y la revalidación sin gastar IA.
- El archivo del parte apto en SharePoint, en la biblioteca **de dev** del
  sitio de IT, con el nombre que usa Posventa.

Lo que **negocio no verá**, y hay que decirlo antes de la demostración:

- **El cierre de la incidencia en Sigrid.** Es F-008 y F-009, y es justo lo
  que el humano dejó fuera a propósito. El ERP no se toca.
- **La cola persistida.** F-005 creó las tablas y `/api/archivar` deja su
  traza, pero los endpoints que guardan la remesa y leen la cola son
  **F-019**, todavía pendiente. Consecuencia práctica y visible: **si el
  usuario recarga la página, pierde el trabajo en curso**. Hay que decírselo,
  no descubrirlo en la demostración.
- **El archivo definitivo de Posventa.** Se archiva en la biblioteca de dev;
  mudarlo es F-013.

## 8 · La tarjeta del portal

Vive en `front-portal/public/assets/js/catalog.js`, **otro repositorio**. El
entregable de F-010 es el bloque escrito, en `docs/DESPLIEGUE.md`; aplicarlo
es tarea del humano allí.

Estructura de la entrada, según el esquema de `azure-apps/portal.md` §4.1:
`id` (kebab-case), `title`, `description`, `category` (aquí `Obra`, la misma
que Albaranes y Partes de Trabajo), `icon` (del diccionario `ICONS` de
`app.js`; se propone reutilizar uno existente antes que añadir uno nuevo),
`url` (el nombre de host de la Static Web App), `requiredGroupName`
(`posventa-usuarios`), `requiredGroupId` (**marcador**, R24) y `comingSoon`
en falso.

**Y aquí va el punto que no se puede suponer.** F-006 cerró T19 como `N/A`
porque *«el humano no commitea en `azure-apps`»*. La tentación es extender esa
conclusión a `front-portal` — y sería una suposición: `front-portal` **sí** es
un repositorio con historial propio y commits del humano, a diferencia de
`azure-apps`. Pero tampoco se puede dar por hecho lo contrario: la última
actividad es de julio de 2026 y el alta de una tarjeta exige además
**desplegar** el portal (`.\deploy.ps1 -SoloFront`), que es un acto sobre
Azure, no un commit.

Por eso la tarea se plantea **sin depender de quién la ejecute ni de dónde**
(R25): `docs/DESPLIEGUE.md` entrega el bloque literal y el procedimiento de
cuatro pasos —crear el grupo, rellenar el GUID, desplegar el portal, pedir
logout/login—, y la tarea de `tasks.md` (T19) queda marcada
`MANUAL (humano) · OTRO REPOSITORIO` con las dos vías abiertas: que el humano
lo aplique él mismo en `front-portal`, o que entregue el bloque a quien lleve
ese repositorio. **En ninguna de las dos toca nada un agente de este
repositorio**, y el criterio de aceptación de F-010 —*«queda escrito qué hay
que cambiar»*— se cumple igual.

Dos avisos que `portal.md` §9 documenta y que hay que repetir en el runbook,
porque los dos ya rompieron una tarjeta:

- Un `requiredGroupId` en marcador **funciona en local por nombre pero deja la
  tarjeta velada en Azure**. Si tras desplegar sale «Sin acceso», lo primero
  que se mira es si el GUID se rellenó.
- El token se emite con los grupos que el usuario tenía **en ese momento**:
  tras meter a alguien en el grupo hace falta `/.auth/logout` y volver a
  entrar. Y `Ctrl+F5`, que el JS del portal se cachea.

## 9 · Decisiones abiertas que necesita validar el humano

| # | Decisión | ¿Bloquea? |
|---|---|---|
| **D1** | **El grupo de seguridad de Posventa no existe.** Hay que crearlo, y lo hace el humano o IT: un agente no crea grupos en el inquilino. Hace falta decidir **nombre** (se propone `posventa-usuarios`, siguiendo la convención de `bc3-usuarios`, `contratos-usuarios`; conviven en el portal otras formas como `albaranes-portal-users`), **propietario** y **miembros iniciales** —quién de Posventa entra en el piloto—. Su Object ID se necesita en dos sitios: para asignarlo a la aplicación empresarial (R16) y para la tarjeta del portal (R24). **No se escribe en este repositorio** | **SÍ** |
| **D2** | **El presupuesto de 45 s del proxy** (§5). Con `IA_TIMEOUT_S` en 120 el circuito no cabe. Opciones: **(a)** bajar los tiempos a ~35 s y desplegar el piloto así, asumiendo que un parte lento falla y se reintenta; **(b)** sacar la Function de detrás del proxy y que el front la llame directamente con su propio token, lo que rompe el mismo origen y obliga a cambiar el front que F-007 acaba de cerrar; **(c)** patrón asíncrono (encolar y consultar), que es una feature nueva. Este diseño propone **(a)**, y **la medición de T2 es la que dice si (a) es viable**. Si la extracción real pasa de 35 s, el humano tiene que elegir entre (b) y (c), y F-010 se replantea | **SÍ** |
| **D3** | **Cómo se cierra la Function App** (R17, §0). Se propone `auth_level=FUNCTION` en los cinco endpoints de trabajo, dejando `health` anónimo: la Static Web App, al enlazar un backend propio, se encarga de la clave de host en sus llamadas. **Hay que verificarlo en el despliegue** (T14): si resultara que el backend enlazado no la aporta, la alternativa es autenticación integrada en la Function App restringida al app registration del front, y entonces cambia `desplegar_backend.ps1`. Lo que **no** es opción es desplegar los cinco endpoints anónimos | **SÍ** |
| **D4** | **El cortafuegos de `psql-albaranes-rs9k2`.** El servidor es compartido y `CLAUDE.md` prohíbe tocar nada a nivel de servidor. Una Function App en Flex Consumption no tiene direcciones de salida fijas, así que o el servidor ya admite servicios de Azure —hay que **mirarlo, en solo lectura**— o hace falta una regla, y esa regla es un cambio de servidor que afecta a los otros tres proyectos y lo decide el humano coordinando con albaranes. Afecta solo a `/api/archivar`, que deja traza en la base; el resto del circuito funciona sin ella | No para el piloto; **sí** para el archivo |
| **D5** | **Nombre de host del front.** Se propone el que asigna Azure, sin dominio propio: `ohana.ruesma.es` está en un proveedor de DNS externo y `portal.md` §6.3 avisa de que en esa zona vive también el correo de la empresa. Un dominio propio se puede añadir después sin rehacer nada, pero **cambiaría las redirect URI** y hay que registrarlas todas de una vez | No |
| **D6** | **¿Esperar a F-018?** Ver §10, riesgo 3. Este diseño propone **no esperar**, y a cambio **subir la prioridad de F-018** para ejecutarlo justo después de T18 | No |
| **D7** | **Quién aplica y despliega la tarjeta del portal** (§8). El entregable de F-010 es el bloque escrito; el alta en `front-portal` la hace el humano o quien lleve ese repositorio | No |

## 10 · Riesgos y decisiones (alternativas descartadas)

**Riesgo 1 · Una Function App abierta que sabe escribir en SharePoint.** Es el
riesgo mayor de la feature (§0) y por eso R17 tiene fase RED: el test que
comprueba que los endpoints exigen credencial se escribe **antes** del cambio
y se le ve fallar. La verificación real es manual (T14): llamar al host
desnudo y recibir `401`.

**Riesgo 2 · Regenerar el secreto de cliente en cada despliegue.** Es
exactamente el fallo que el portal documenta: un despliegue completo pisó la
redirect URI del dominio propio y rompió el inicio de sesión. Por eso
`desplegar_front.ps1` nace con modo `-SoloFront` desde el primer día, y en el
modo completo registra **todas** las redirect URI de una vez y verifica el
resultado.

**Riesgo 3 · ACEPTADO — desplegar antes de que F-018 recorte los permisos de
Graph.** La aplicación conserva `Sites.ReadWrite.All` y
`Sites.FullControl.All`, que alcanzan a **todos** los sitios del inquilino.
La pregunta es si el despliegue debe esperar al recorte. **No debe**, por tres
razones, y con un matiz que no se esconde:

- El recorte es una dimensión **independiente** del despliegue: cambia qué
  puede hacer una identidad de aplicación, no dónde corre el servicio.
- El humano ya decidió el 2026-08-20 el orden contrario —arrancar F-006 con
  los permisos amplios y recortar después, para no mezclar un cambio de
  configuración del inquilino con una implementación—. Bloquear F-010 aquí
  sería revertir esa decisión sin que nadie la haya revisado.
- F-010 **mejora** la custodia de esa credencial: hoy el secreto de Graph vive
  en un `.env` de un puesto de trabajo; después vivirá en un Key Vault con
  acceso por identidad gestionada.

**El matiz, y es real**: hasta hoy esos permisos amplios estaban ahí pero casi
sin usarse, porque `ARCHIVO_HABILITADO` está apagado y desde local no se sube.
Con F-010 la aplicación **empieza a escribir de verdad**, y encima desde un
servicio expuesto a internet. Eso no hace que el despliegue deba esperar;
hace que el recorte sea **más urgente**. De ahí D6: se despliega, y se propone
al humano subir F-018 justo detrás de T18. Mientras tanto, el riesgo sigue
escrito donde ya está: `docs/INTEGRACION.md` §3 y la spec de F-006.

**Riesgo 4 · F-007 todavía está en revisión.** `config.js` es un fichero de
F-007 y F-010 lo modifica (R21). Si la revisión de F-007 lo cambia, hay
conflicto. Mitigación: F-010 **parte de `feature/F-007-front` ya cerrada y
mergeada**; el implementer no empieza T9 antes de eso, y si F-007 acaba
tocando `TIMEOUT_PETICION_MS` por su cuenta, T9 se reduce a comprobar el
número.

**Riesgo 5 · El barrido de `docs/INTEGRACION.md` es más estricto de lo que
parece.** `test_f005_integracion_sin_secretos.py` no solo caza GUID: también
caza cualquier `PG_ALGO` seguido de un signo igual y un valor, cualquier
`secret`/`token`/`clave` con signo igual, y cualquier FQDN de Azure. Al
redactar §8 de ese documento (T11) los nombres van **en tabla**, nunca en
forma de asignación. Es la clase de detalle que hace fallar el arnés al final
y cuesta media hora entender.

**Alternativas descartadas, y por qué:**

| Alternativa | Por qué no |
|---|---|
| Funciones **gestionadas** de la Static Web App en vez de backend enlazado | Su tope de petición es aún menor que el del proxy y no encaja con una llamada multimodal. Además el ecosistema ya usa backend enlazado para la app de nóminas |
| Reutilizar `kv-albaranes-rs9k2` | Vive en el grupo de recursos de otro proyecto (§3) |
| Reutilizar el app registration de Graph para el inicio de sesión | Juntaría la credencial de mayor privilegio con la aplicación de acceso de los usuarios (§3) |
| Restringir el acceso por `allowedRoles` con un rol propio de la SWA | Exigiría una función de origen de roles y mantener asignaciones aparte. La asignación obligatoria en la aplicación empresarial usa el grupo de Entra que ya hay que crear, y es una sola casilla |
| Dominio propio desde el primer día | La zona `ruesma.es` no está en Azure y comparte registros con el correo de la empresa (D5) |
| Desplegar también a un entorno de producción | El encargo es un piloto para negocio. Un solo entorno, `dev`, y con el archivo apuntando a la biblioteca de dev |
| Que un agente cree el grupo de seguridad o el app registration | Son cambios de configuración del inquilino. Un agente no los hace; el humano ejecuta el script |

## 11 · Límite de microservicio

F-010 despliega los **dos** servicios de este monorepo, `postventa-api` y
`postventa-front`, y no mezcla responsabilidades: cada uno tiene su script y
su recurso. La frontera que sí se cruza es la del **portal**, que es otro
proyecto (`front-portal`) con su propio repositorio y su propio despliegue.
Se resuelve como manda `CLAUDE.md`: **no se implementa aquí**. F-010 entrega
lo que ese proyecto necesita —el bloque de catálogo y el procedimiento— y la
ejecución queda del lado de su dueño (§8, D7).

Tampoco se toca `azure-apps/`: la fuente de verdad de lo que este proyecto
expone es `docs/INTEGRACION.md`, en este repositorio, y refrescar la copia del
ecosistema es decisión del humano.
