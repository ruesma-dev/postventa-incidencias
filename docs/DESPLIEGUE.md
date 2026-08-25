<!-- docs/DESPLIEGUE.md -->
# Despliegue de postventa-incidencias

> Runbook del entorno **dev**, que es el único que existe: el encargo es un
> piloto para negocio. Lo escribe F-010.
>
> **Ni un valor real en este documento**: ni URL, ni GUID, ni identificador de
> suscripción, inquilino, sitio o aplicación. Donde haga falta uno va un
> marcador entre `<>`. El barrido de identificadores del repositorio lo
> comprueba en todo el árbol.

---

## 1 · Qué se despliega, y qué no

**Sí**: soltar una remesa, trocearla, extraer los campos con IA, clasificar la
firma, validar, corregir a mano y **archivar el parte apto en la biblioteca de
dev** del sitio de IT.

**No**, y hay que decirlo antes de enseñárselo a nadie:

- **El cierre de la incidencia en Sigrid.** Es F-008 y F-009. El ERP no se
  toca en este piloto, a propósito.
- **La cola persistida.** F-005 creó las tablas y `/api/archivar` deja su
  traza, pero guardar la remesa y leer la cola es F-019. Consecuencia
  visible: **si el usuario recarga la página, pierde el trabajo en curso**.
- **El archivo definitivo de Posventa.** Se archiva en la biblioteca de dev;
  mudarlo es F-013.

## 2 · Los cinco scripts, y en qué orden

Todos viven en `infra/`, todos son **re-ejecutables** y todos admiten
`-WhatIf`, que dice qué harían sin tocar nada.

| Orden | Script | Qué hace | Desde dónde se ejecuta | Cuándo se repite |
|---|---|---|---|---|
| 0 | `00_vars_postventa.ps1` | No hace nada: **declara** los nombres de recurso, las regiones y los tags. Los demás lo cargan por punto | — | Nunca se ejecuta suelto |
| 1 | `cargar_secretos_postventa.ps1` | Crea o reutiliza el grupo de recursos y el Key Vault, y sube los **nueve** secretos del backend, pedidos a ciegas | `$HOME` o `infra\` | Solo al rotar una credencial (`-Solo <nombre>`, **no con `-File`**: ver abajo) |
| 2 | `desplegar_backend.ps1` | Almacenamiento, Log Analytics, Application Insights, identidad gestionada, permiso de lectura sobre el Key Vault, Function App, App Settings por referencia y publicación del código | **`infra\` obligatorio** | Cada vez que cambie el backend |
| 3 | `desplegar_front.ps1` | Registro de aplicación, asignación obligatoria y grupo asignado, Static Web App, enlace del backend y subida de los estáticos | **`infra\` obligatorio** | Con `-SoloFront` para el día a día |
| 4 | `verificar_despliegue.ps1` | Las tres comprobaciones de después. **Solo lecturas** | `$HOME` o `infra\` | Después de cada despliegue |

### Desde dónde se ejecuta cada uno, y por qué no da igual

**Los dos despliegues se ejecutan desde `infra\`, dentro del repositorio.**
No se copian a `$HOME`: `desplegar_backend.ps1` y `desplegar_front.ps1`
deducen la raíz del repositorio con

```powershell
$raiz = Split-Path -Parent $PSScriptRoot
```

para encontrar `services\postventa-api` y `services\postventa-front`. Copiados
a `$HOME`, esa cuenta da `C:\Users`, donde no hay ningún `services\`, y el
script no encuentra qué publicar. Ejecutarlos desde `infra\` **no ensucia el
árbol**: `desplegar_front.ps1` hace su copia de trabajo en el directorio
temporal del sistema y la borra en un `finally`.

**Los que sí se copian fuera** son los que no dependen de la raíz del
repositorio —`cargar_secretos_postventa.ps1`, que solo necesita
`00_vars_postventa.ps1` al lado, y `verificar_despliegue.ps1`, igual—:

```
copy infra\00_vars_postventa.ps1 $HOME\
copy infra\cargar_secretos_postventa.ps1 $HOME\
copy infra\verificar_despliegue.ps1 $HOME\
```

Esto costó la primera parada del 2026-08-21, siguiendo el `copy infra\*.ps1
$HOME\` que decía antes este documento.

**Antes de nada**: `az login` y la suscripción correcta seleccionada.
También hacen falta la CLI de Azure y la de Static Web Apps
(`npm i -g @azure/static-web-apps-cli`).

### Son nueve secretos, no once, y el porqué importa

El Key Vault acaba con **once** secretos, pero **a mano solo se cargan
nueve**: los del backend (`pg-*`, `gemini-api-key`, `graph-*`,
`sharepoint-*`). Los dos que faltan —`swa-client-id` y `swa-client-secret`—
**los genera y los guarda `desplegar_front.ps1`**, que crea el registro de
aplicación, le saca el secreto y lo escribe él mismo en el vault.

**No se inventan ni se teclean**: cuando `cargar_secretos_postventa.ps1` se
ejecuta todavía no existen, y cualquier valor que se meta lo sobrescribe el
despliegue del front. Esto costó una parada real el 2026-08-21, siguiendo lo
que decía este mismo documento.

La lista está en `infra/00_vars_postventa.ps1`, partida a propósito en
`$PostventaSecretosBackend` (los nueve) y `$PostventaSecretosFront` (los dos).

### Rotar una credencial: `-Solo` **no funciona con `powershell -File`**

Para subir un secreto suelto sin volver a teclear los otros ocho, el script 1
admite `-Solo <nombre>`. Pero **con `powershell -File` el parámetro no
funciona**: los argumentos llegan como una sola cadena, `-Solo` no construye
el array `[string[]]` que declara, y el script responde

```
Estos secretos no existen: ...
```

que **no es el error real** y manda a buscar el problema donde no está.

Hay que invocarlo **desde la propia sesión de PowerShell**, con el script al
lado de `00_vars_postventa.ps1`:

```
.\infra\cargar_secretos_postventa.ps1 -Solo gemini-api-key
```

o, si hace falta lanzarlo desde fuera, con `-Command` en vez de `-File`:

```
powershell -ExecutionPolicy Bypass -Command ".\infra\cargar_secretos_postventa.ps1 -Solo gemini-api-key"
```

Sin `-Solo` —la ejecución completa— `-File` sí vale, porque no hay que
construir ningún array. Descubierto ejecutando, el 2026-08-21.

### Si un nombre global está ocupado

`func-`, `st`, `kv-` y `swa-` compiten con todo Azure. Si uno está tomado, el
script falla con **código 4** y lo dice. Se arregla en un fichero que **no se
versiona**:

```
infra/00_vars_postventa.local.ps1
```

con una línea: `$PostventaSufijo = "-loquesea"`. Los cuatro nombres globales se
recomponen solos.

### Los códigos de salida

| Código | Qué pasó |
|---|---|
| 0 | Bien |
| 2 | No hay sesión de `az` |
| 3 | Falta una herramienta (`az`, `swa`) |
| 4 | Un nombre global está ocupado |
| 5 | Confirmación denegada: no se tocó nada |
| 6 | Falló el despliegue |
| 7 | No existe la Function App: no hay backend que enlazar |
| 8 | No existe el grupo de seguridad |
| 9 | Alguna comprobación del verificador salió en rojo |

## 3 · Lo que hace falta antes del primer despliegue

1. **El grupo de seguridad** `posventa-usuarios` creado en Entra, con los
   miembros del piloto dentro. Lo crea el humano; su Object ID **no se pega en
   este repositorio**.

   ```
   az ad group create --display-name "posventa-usuarios" --mail-nickname "posventa-usuarios" --query id -o tsv
   ```

   Si al crearlo se elige otro nombre, ese nombre tiene que cambiarse en
   `infra/00_vars_postventa.ps1` y en la tarjeta del portal (§6). **Los tres
   sitios tienen que decir lo mismo.**

2. **Las nueve credenciales del backend a mano**, para teclearlas cuando el
   script las pida: `pg-host`, `pg-user`, `pg-password`, `gemini-api-key`,
   `graph-tenant-id`, `graph-client-id`, `graph-client-secret`,
   `sharepoint-site-id` y `sharepoint-drive-id`.

   **`swa-client-id` y `swa-client-secret` NO se preparan**: los crea y los
   guarda `desplegar_front.ps1` (§2). Teclearlos aquí es inventar dos valores
   que el despliegue del front sobrescribe.

3. **El rol `Key Vault Secrets Officer` sobre el Key Vault**, para la cuenta
   que vaya a ejecutar el script 1.

   **Crear el Key Vault NO da permiso sobre sus secretos.** El vault usa
   RBAC, y ser Owner del grupo de recursos —o haberlo creado uno mismo— deja
   gestionar el recurso pero **no** escribir dentro. Esto es lo que **paró la
   primera ejecución real** el 2026-08-21: el script crea el vault sin
   problemas y luego muere en el **primer** secreto con un `Forbidden`, en
   vez de comprobarlo antes.

   Se comprueba y se concede así, una vez, después de que exista el vault:

   ```
   az role assignment list --assignee <tu-cuenta> --scope <id-del-key-vault> --query "[].roleDefinitionName" -o tsv
   ```

   ```
   az role assignment create --assignee <tu-cuenta> --role "Key Vault Secrets Officer" --scope <id-del-key-vault>
   ```

   La asignación **tarda un poco en propagarse**. Si el script sigue dando
   `Forbidden` justo después de concederla, se espera un minuto y se
   re-ejecuta: el script es re-ejecutable y no duplica nada.

4. **Un tope de gasto con alerta en el proveedor de IA.** No es opcional y no
   depende de Azure: `/api/extraer` y `/api/firma` quedan alcanzables, y el
   tope es la defensa proporcionada a que un desconocido gaste cuota.

## 4 · La ventana de escritura de `/api/archivar`

**Es el candado principal del despliegue**, y conviene entender por qué antes
de tocarlo.

Los seis endpoints quedan en `ANONYMOUS` porque **la plataforma lo exige**: con
un backend enlazado, la Static Web App autentica al usuario y reenvía la
cabecera `x-ms-client-principal`, **no** una clave ni un token que la Function
pueda exigir. Poner `auth_level=FUNCTION` rompería el front el mismo día. La
explicación larga está en la cabecera de `services/postventa-api/function_app.py`
y en `specs/F-010-despliegue/design.md` §9 bis.

Lo que sí controlamos es **cuándo `/api/archivar` puede escribir**.
`ARCHIVO_HABILITADO` **se despliega apagado**: fuera de la ventana, el endpoint
responde `503` a cualquiera —incluido un desconocido— y **no toca SharePoint**.

**Abrir la ventana**, justo antes de archivar de verdad:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=true
```

**Cerrarla en cuanto se termine**, salga bien o mal:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=false
```

Se cierra **siempre** al terminar. Dejarla abierta «por si acaso» es
exactamente lo que este diseño evita: mientras esté abierta, `/api/archivar`
escribe en SharePoint para cualquiera que llame a la Function. No hace falta
redesplegar ni tocar código: es una App Setting.

Si has abierto la ventana, `verificar_despliegue.ps1` **no hace** su segunda
comprobación y te lo dice: con la ventana abierta, esa llamada subiría un PDF
de verdad.

## 5 · Después de desplegar

```
powershell -ExecutionPolicy Bypass -File $HOME\verificar_despliegue.ps1 -BaseUrl <url-de-la-function> -UrlFront <url-del-front>
```

Comprueba tres cosas, todas de lectura: `GET /api/health` responde `200`,
`POST /api/archivar` responde `503` con la ventana cerrada, y la Static Web App
sin sesión redirige al inicio de sesión.

Lo que se anota en `progress/` son las cuatro líneas que imprime, **sin la URL
y sin ningún identificador**.

Y a mano, con **dos cuentas**: una miembro del grupo entra; una **no miembro
no entra**. Si entra, la asignación obligatoria no está aplicada: **se para**.

## 6 · La tarjeta del portal

La tarjeta vive en **otro repositorio**, `front-portal`, en
`public/assets/js/catalog.js`. **Ningún agente de este repositorio la toca.**
Lo que F-010 entrega es el bloque exacto y el procedimiento; aplicarlo es una
tarea del humano, o de quien lleve ese repositorio.

### El bloque, para pegar en `window.RUESMA_PORTAL.apps[]`

```js
  {
    id: "postventa-incidencias",
    title: "Partes de Posventa",
    description:
      "Sube una remesa de partes de posventa escaneados, revisa lo que la IA ha leido y archiva los aptos en SharePoint.",
    category: "Obra",
    icon: "contract",
    url: "<URL-DE-LA-STATIC-WEB-APP>",
    requiredGroupName: "posventa-usuarios",
    requiredGroupId: ["REEMPLAZAR_ID_GRUPO_POSVENTA"],
    comingSoon: false,
  },
```

Los nueve campos del esquema de `azure-apps/portal.md` §4.1 están todos.
Dos decisiones de ese bloque, por si alguien se las pregunta:

- **`category: "Obra"`** es la misma que usan Albaranes y Partes de Trabajo.
- **`icon: "contract"`** se reutiliza del diccionario `ICONS` de `app.js` —el
  documento con check, el que ya usa Partes de Trabajo— en vez de añadir un
  icono nuevo.

**`requiredGroupId` va como marcador a propósito.** Un GUID real en este
repositorio hace fallar el barrido de identificadores; el valor se rellena en
`front-portal`, que es donde tiene que vivir.

### El procedimiento, en cuatro pasos

1. **Pegar el bloque** en `front-portal/public/assets/js/catalog.js`.
2. **Sustituir el marcador** `REEMPLAZAR_ID_GRUPO_POSVENTA` por el Object ID
   real del grupo `posventa-usuarios`. Ese GUID vive en `front-portal`, **nunca
   aquí**.
3. **Desplegar el portal**, desde su propio repositorio:

   ```
   .\deploy.ps1 -SoloFront
   ```

4. **Refrescar el navegador con `Ctrl+F5`**, y pedir a los miembros del grupo
   que hagan `/.auth/logout` y vuelvan a entrar.

El procedimiento no supone **quién** ejecuta cada paso ni en qué repositorio se
commitea: sirve igual si lo aplica el humano, o si le entrega el bloque a
quien lleve `front-portal`.

### Dos avisos que ya rompieron una tarjeta

- **Marcador sin rellenar = tarjeta velada.** Con el `requiredGroupId` en
  marcador, la tarjeta funciona en local (que empareja por nombre) pero sale
  **velada, con «Sin acceso», en Azure** (que empareja por GUID). Si tras
  desplegar sale velada para todos, lo primero que se mira es si el GUID se
  rellenó.
- **El token se emite con los grupos de ese momento.** Después de meter a
  alguien en el grupo hace falta `/.auth/logout` y volver a entrar, y además
  `Ctrl+F5`, porque el JS del portal se cachea.

## 7 · Los tiempos de espera y el proxy de 45 segundos

El proxy de la Static Web App **corta cualquier petición a los 45 s**. Es un
límite de la plataforma, no una elección nuestra: lo documenta
`azure-apps/portal.md` §9 y lo escribió quien lo sufrió con la app de nóminas.

**El escalonado, que es el criterio y no los números:**

```
la IA abandona a los 35 s  →  el front aborta a los 40  →  el proxy corta a los 45
```

**Cada capa cede antes que la de fuera.** Ese orden es lo que hace que el
usuario reciba **nuestro** error —explicado, reintentable y que libera la plaza
de la cola— en vez de un corte opaco de la plataforma, con una llamada zombi
por detrás gastando cuota de IA.

| Dónde | Variable | Valor | Quién lo fija |
|---|---|---|---|
| Backend | `IA_TIMEOUT_S` | **35** | `desplegar_backend.ps1` |
| Backend | `GRAPH_TIMEOUT_S` | **35** | `desplegar_backend.ps1` |
| Front | `TIMEOUT_PETICION_MS` | **40000** | `js/config.js` |
| Plataforma | corte del proxy | 45 s | No lo fijamos nosotros |

Subir el del front por encima de 45 s no da más margen: da un corte del proxy
que el front no se entera de que ha ocurrido. Si de verdad hiciera falta más
tiempo, lo que hay que cambiar es el montaje —patrón asíncrono, encolar y
consultar—, no estos números.

**Medición real del circuito** (T2, en local, con una remesa de 22 partes):

| Endpoint | Peor caso, 1 petición viva | Peor caso, 6 peticiones vivas |
|---|---|---|
| `POST /api/split` | 2,4 s | — |
| `POST /api/extraer` | 5,5 s | **6,5 s** |
| `POST /api/firma` | 4,1 s | 5,5 s |

El peor caso medido, **6,5 s**, es el **14 %** del presupuesto. Los 35 s del
backend no son el caso normal: son colchón para lo que **no se puede medir en
local** —el salto de región entre `westeurope` y `spaincentral`, el arranque en
frío de la primera petición del día y un día malo del proveedor de IA—.

> **D2 resuelta el 2026-08-20**, opción (a): se despliega con estos tiempos.

## 8 · Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Nombres de recurso, regiones y tags | `infra/00_vars_postventa.ps1` |
| Por qué los endpoints son anónimos | Cabecera de `services/postventa-api/function_app.py` |
| Qué exponemos y qué consumimos | `docs/INTEGRACION.md` |
| El razonamiento completo del despliegue | `specs/F-010-despliegue/design.md` |
| El portal, su catálogo y sus avisos | `azure-apps/portal.md` |
