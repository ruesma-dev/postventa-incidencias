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
| 1 | `cargar_secretos_postventa.ps1` | Crea o reutiliza el grupo de recursos y el Key Vault, y sube los **once** secretos del backend, pedidos a ciegas | `$HOME` o `infra\` | Solo al rotar una credencial (`-Solo <nombre>`, **no con `-File`**: ver abajo) |
| 2 | `desplegar_backend.ps1` | Almacenamiento, Log Analytics, Application Insights, identidad gestionada, permiso de lectura sobre el Key Vault, Function App, App Settings por referencia y publicación del código. Deja **abiertas** las dos ventanas de escritura (§4); `-VentanasCerradas` las cierra | **`infra\` obligatorio** | Cada vez que cambie el backend |
| 3 | `desplegar_front.ps1` | Registro de aplicación, asignación obligatoria y grupo asignado, Static Web App, enlace del backend y subida de los estáticos | **`infra\` obligatorio** | Con `-SoloFront` para el día a día |
| 4 | `verificar_despliegue.ps1` | Las tres comprobaciones de después. **Solo lecturas** | `$HOME` o `infra\` | Después de cada despliegue |

Hay un sexto que **no** forma parte del despliegue y por eso no está en la
tabla: `14_paso0_sigrid.ps1` orquesta el **Paso 0** del bloque 8 de F-009
llamando al 1 y al 2, y comprueba que las referencias a Key Vault se resuelven.
Está en el §4 bis.

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

### Son once secretos, no trece, y el porqué importa

El Key Vault acaba con **trece** secretos, pero **a mano solo se cargan
once**: los del backend (`pg-*`, `gemini-api-key`, `graph-*`,
`sharepoint-*`, `sigrid-api-base-url` y `sigrid-api-key`). Los dos que
faltan —`swa-client-id` y `swa-client-secret`—
**los genera y los guarda `desplegar_front.ps1`**, que crea el registro de
aplicación, le saca el secreto y lo escribe él mismo en el vault.

**No se inventan ni se teclean**: cuando `cargar_secretos_postventa.ps1` se
ejecuta todavía no existen, y cualquier valor que se meta lo sobrescribe el
despliegue del front. Esto costó una parada real el 2026-08-21, siguiendo lo
que decía este mismo documento.

La lista está en `infra/00_vars_postventa.ps1`, partida a propósito en
`$PostventaSecretosBackend` (los once) y `$PostventaSecretosFront` (los dos).

**Dos de los once son de Sigrid, y cada uno por un motivo distinto.**
`sigrid-api-key` es una **credencial**: la clave de función de la pasarela.
`sigrid-api-base-url` no autentica nada, pero es un **host interno**, y esos no
entran al repositorio: el mismo motivo por el que ya estaba ahí `pg-host`. Los
dos valores los da el dueño de `sigrid-api` (`azure-apps/sigrid_api.md` §3).

> **`SIGRID_BASE_DATOS` no está aquí, y estuvo unas horas el 2026-09-03.** Se
> subió al vault con el argumento de que el nombre de la base de producción del
> ERP no puede quedar escrito en el repositorio, y **ya lo estaba**: en
> `docs/referencia/03_modelo_posventa_sigrid.md` y en
> `specs/F-009-cierre-sigrid/design.md`, entre otros. Un secreto de vault no lo
> protegía de nada y en cambio había que subirlo a mano en cada entorno, que es
> una oportunidad más de que un despliegue quede a medias. Bajó a **App Setting
> plana** de `desplegar_backend.ps1` el mismo día (§4 bis).

### Rotar una credencial: `-Solo` **no funciona con `powershell -File`**

Para subir un secreto suelto sin volver a teclear los otros diez, el script 1
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

2. **Las once credenciales del backend a mano**, para teclearlas cuando el
   script las pida: `pg-host`, `pg-user`, `pg-password`, `gemini-api-key`,
   `graph-tenant-id`, `graph-client-id`, `graph-client-secret`,
   `sharepoint-site-id`, `sharepoint-drive-id`, `sigrid-api-base-url` y
   `sigrid-api-key`.

   Las dos últimas las da el dueño de `sigrid-api`, no se deducen. Si todavía
   no las tienes, **déjalas vacías y saldrán como «Sin tocar»**: el resto del
   despliegue funciona, y lo único que no arranca hasta cargarlas es
   `POST /api/cerrar`, que responde `503` nombrándolas.

   **`sigrid-base-datos` ya no se pide**: el nombre de la base del ERP es una
   App Setting plana desde el 2026-09-03 (§2, recuadro).

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

> **Desde el 2026-09-23 el despliegue la deja ABIERTA, y a la del ERP (§4 bis)
> también.** Decisión del humano: *«vamos a desplegar, pero quiero que por
> defecto publique abierto, no cerrado»*, y a la pregunta de qué ventanas,
> *«Las dos»*. Posventa ya usa el servicio en real, y cada despliegue les
> cerraba el archivo y el cierre hasta que alguien los reabría a mano.
> `desplegar_backend.ps1` fija `ARCHIVO_HABILITADO=true` y
> `CIERRE_HABILITADO=true`; con **`-VentanasCerradas`** fija **las dos** en
> `false`. La enmienda, con la premisa de antes citada, está bajo R33 de
> `specs/F-010-despliegue/requirements.md`.
>
> **El valor por defecto del código NO cambia**: `config/settings.py` declara
> `archivo_habilitado` y `cierre_habilitado` con `default=False`. En un puesto
> de trabajo y en los tests sigue siendo imposible escribir; lo que cambia es
> solo lo que el despliegue escribe en la Function App.

Los seis endpoints quedan en `ANONYMOUS` porque **la plataforma lo exige**: con
un backend enlazado, la Static Web App autentica al usuario y reenvía la
cabecera `x-ms-client-principal`, **no** una clave ni un token que la Function
pueda exigir. Poner `auth_level=FUNCTION` rompería el front el mismo día. La
explicación larga está en la cabecera de `services/postventa-api/function_app.py`
y en `specs/F-010-despliegue/design.md` §9 bis.

Lo que sí controlamos es **cuándo `/api/archivar` puede escribir**. Con
`ARCHIVO_HABILITADO` apagado el endpoint responde `503` a cualquiera y **no
toca SharePoint**. Hasta el 2026-09-22 se desplegaba apagado y se abría solo
para archivar de verdad; hoy se despliega **encendido**, y quien no quiera que
una versión concreta archive la despliega con `-VentanasCerradas` o la cierra
después.

**La vía buena es el script**, que lee antes y después y dice el estado en
palabras: `infra_ventana_archivo.ps1` (sin parámetros solo mira; `-Cerrar`
la cierra sin preguntar; `-Abrir` avisa y pide una palabra). Las dos líneas de
`az` equivalentes, por si el script no está a mano:

**Abrirla**, si se desplegó con `-VentanasCerradas` o alguien la cerró:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=true
```

**Cerrarla**, cuando haga falta que no se archive —una incidencia, una versión
dudosa—, salga bien o mal lo que se esté haciendo:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings ARCHIVO_HABILITADO=false
```

**El siguiente despliegue la vuelve a abrir.** Cada despliegue la fija, a
propósito (hallazgo H2 del guion del bloque 8 de F-009): quien la haya cerrado
a mano y quiera que siga cerrada tiene que desplegar con `-VentanasCerradas`.
No hace falta redesplegar ni tocar código para abrirla o cerrarla: es una App
Setting.

**Lo que protege a SharePoint con la ventana abierta** no es la ventana, sino
la plataforma: el host desnudo de la Function lo corta Easy Auth (§5 bis) y el
front exige sesión del grupo de Posventa. Con la ventana abierta, sube un parte
cualquier usuario de ese grupo que lo pida desde el front.

Con la ventana abierta, `verificar_despliegue.ps1` **no hace** su segunda
comprobación y te lo dice: esa llamada subiría un PDF de verdad. Tras un
despliegue por defecto su veredicto, por tanto, **no sale en verde** (§5).

## 4 bis · La ventana de escritura del ERP: `/api/adjuntar` y `/api/cerrar`

**Es el candado más serio de todo el despliegue**, porque lo que hay detrás no
es una biblioteca de documentos: es el **ERP de producción del que depende toda
la empresa**. Deshacer un cierre no es borrar un fichero; es otro proceso que
alguien tiene que ejecutar a mano en Sigrid.

**Una sola variable para las dos escrituras, desde F-012.** `CIERRE_HABILITADO`
cubre `POST /api/cerrar` **y** `POST /api/adjuntar`, que es el que sube el PDF
del parte a la reclamación como gráfico. No hay `GRAFICO_HABILITADO`, y no
puede haberlo: el gráfico es **la primera mitad del cierre** —el mismo sistema,
el mismo dueño, la misma ventana y la misma decisión—, y un segundo interruptor
solo podría crear dos estados, los dos malos. Con el gráfico apagado y el
cierre encendido se volvería a cerrar sin el parte dentro, que es exactamente
la anomalía que F-012 eliminó; al revés, todos los cierres responderían `409`
por una configuración a medias.

**Consecuencia que hay que saber**: la ventana abierta para el gráfico está
abierta también para el cierre. Es aceptable por lo mismo de siempre —dry-run
por omisión y confirmación explícita del usuario—, y de hecho la verificación
de F-012 sobre la obra de prueba **quería** cerrar la reclamación después de
adjuntar.

`CIERRE_HABILITADO` **se despliega ABIERTO desde el 2026-09-23, y por el mismo
mecanismo que el de archivo** (recuadro del §4): `desplegar_backend.ps1` lo fija
en `$ajustes`, línea a línea al lado de `ARCHIVO_HABILITADO`, en `true` por
defecto y en `false` con `-VentanasCerradas`, así que **cada despliegue lo
devuelve al valor que el despliegue decide**. Hasta el 2026-09-22 lo fijaba en
`false`. Fuera de la ventana, los dos endpoints responden `503` a cualquiera y
**no tocan el ERP**, ni siquiera para leer. **El defecto del código no cambia**:
`config/settings.py`, `cierre_habilitado`, `default=False`.

> **Ahora sí es el mismo mecanismo; hasta el 2026-09-03 no lo era, y este
> documento decía que sí.** `CIERRE_HABILITADO` no estaba en `$ajustes`: se
> apoyaba en el valor por defecto del código (`False`), que **solo se aplica
> mientras la App Setting no exista**. En cuanto se encendiera una vez para el
> bloque 8 de F-009, ningún redespliegue habría vuelto a apagarla, y era
> precisamente el candado que separa «leer el ERP» de «escribir en el ERP»: el
> único del despliegue que no se rearmaba solo. Es el hallazgo **H2** de
> `progress/guion_bloque8_F-009.md` §8, y se arregló ahí mismo, en el script.

**Es una variable aparte, y eso es deliberado.** Se abren en momentos distintos
y protegen cosas distintas: poder archivar no puede implicar poder cerrar. Si
fueran la misma, abrir la ventana para subir unos partes abriría a la vez la
escritura en Sigrid, y nadie se daría cuenta hasta que se cerrara algo.

**La vía buena es el script**: `infra9_ventana_escritura.ps1` (sin
parámetros solo mira; `-Cerrar` la cierra sin preguntar; `-Abrir` avisa de que
abre también el cierre y pide una palabra). Las dos líneas de `az`
equivalentes:

**Abrirla**, si se desplegó con `-VentanasCerradas` o alguien la cerró:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=true
```

**Cerrarla**, cuando haga falta que no se escriba en el ERP —una incidencia,
una versión dudosa, una prueba—, salga bien o mal:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false
```

**El siguiente despliegue la vuelve a abrir**, salvo con `-VentanasCerradas`.

### Riesgo aceptado con la ventana del ERP abierta por defecto

Aceptado por el humano el 2026-09-23 al decidir el despliegue abierto, y escrito
aquí para que nadie lo descubra después:

1. **Cualquier versión desplegada escribe en Sigrid de producción sin una
   puerta manual.** Quedan el dry-run por omisión, la confirmación del usuario
   y la puerta de entorno, pero ya no el gesto de alguien abriendo la ventana
   en el plano de gestión. Una versión con un defecto en el cierre lo ejecuta
   contra el ERP en cuanto un usuario confirme.
2. **Mientras F-034 no esté desplegada, `/api/adjuntar` y `/api/cerrar` siguen
   tomando el número de incidencia del cuerpo de la petición**, no de lo
   persistido del parte. Un usuario autenticado del grupo de Posventa puede
   mandar un número que no es el del parte.

   > **Nota del 2026-09-23 (F-034).** **Desde el despliegue de F-034**,
   > `/api/adjuntar` y `/api/cerrar` **dejan de tomar del cuerpo** el número
   > de incidencia y el estado de archivo: la reclamación que se adjunta y la
   > que se cierra salen del número **guardado** del parte, «consta archivado»
   > sale de la traza **guardada**, y un cuerpo que no cuadre recibe **409** sin
   > llegar al ERP, ni siquiera en dry-run. Hasta ese despliegue, este punto 2
   > sigue siendo cierto tal cual; y después queda solo lo que F-034 declara
   > fuera de su alcance (su D-1: quien pueda escribir en la base puede cambiar
   > lo guardado). El punto 1 no lo toca F-034. El detalle, en
   > `specs/F-034-archivo-persistido-en-erp/`.

Lo que sigue impidiendo que **un desconocido** llegue a escribir es la
plataforma (Easy Auth en el host desnudo y la sesión del grupo en el front,
§5 bis), no esta ventana. Quien no quiera este riesgo en un despliegue
concreto lo lanza con `-VentanasCerradas`.

### Lo que la ventana NO sustituye

Abrirla **no basta para que se cierre nada**, y esa es la diferencia con la de
archivo. Encima de ella hay dos puertas más que no son configuración:

1. **El entorno** tiene que ser `dev` o `pro`. Desde un puesto de trabajo no se
   escribe ni con la variable encendida: se comprueba en la fábrica **y** en el
   constructor de **los dos** adaptadores.
2. **Los dos endpoints son dry-run por omisión.** Sin `commit` leen y devuelven
   qué pasaría; con `commit` exigen además la confirmación explícita del
   usuario o su preferencia de auto-cierre guardada. **Una sola confirmación
   cubre el gráfico y el cierre.**
3. **El cierre exige que el parte conste adjuntado** (F-012). Con `commit` y
   sin gráfico responde `409` **sin tocar el ERP**: la ventana abierta no basta
   para cerrar una reclamación sin su parte dentro.

Así que la secuencia de un cierre real es, en este orden: `/api/adjuntar`
**sin** `commit` y `/api/cerrar` **sin** `commit`, y **leer los dos dry-run** →
confirmar → `/api/adjuntar` con `commit` → **solo si responde `adjuntado`**,
`/api/cerrar` con `commit`. Hasta el 2026-09-22 la secuencia empezaba abriendo
la ventana y terminaba cerrándola; desde el 2026-09-23 la ventana ya está
abierta tras desplegar (salvo `-VentanasCerradas`).

### Las variables de Sigrid, y cuál es el secreto

**Las diez las pone el despliegue**, y desde el 2026-09-03 no hay que
aprovisionar ninguna a mano (hallazgo **H1** del guion del bloque 8): las **dos**
sensibles por referencia a Key Vault, las otras **ocho** en claro en `$ajustes`.
Eran ocho hasta F-012, que añade las dos del gráfico.

| App Setting | Qué es | Cómo se despliega |
|---|---|---|
| `CIERRE_HABILITADO` | El interruptor. Apagado por defecto **en el código** | `$ajustes`, `true` en cada despliegue desde el 2026-09-23; `false` con `-VentanasCerradas` |
| `SIGRID_API_BASE_URL` | La raíz de la pasarela: un **host interno** | Referencia a Key Vault (`sigrid-api-base-url`) |
| `SIGRID_API_KEY` | **Secreto**: la clave de función de la pasarela | Referencia a Key Vault (`sigrid-api-key`) |
| `SIGRID_BASE_DATOS` | La base de negocio del ERP, la única escribible en la pasarela | `$ajustes`, en claro |
| `SIGRID_TIMEOUT_S`, `SIGRID_REINTENTOS` | Tiempos. La escritura no se reintenta nunca, y eso no es configurable | `$ajustes`, 35 s y 3 |
| `SIGRID_TIP_RECLAMACION`, `SIGRID_ZONA_HORARIA` | Configuración de la instalación, con valor por defecto medido | `$ajustes`, `708` y `Europe/Madrid` |
| `SIGRID_GRATIPIDE_PARTE` | **F-012** · la clase de gráfico con la que se adjunta el parte (`auxgra.ide` 35 = `PV002`, «POSTVENTA:Fotos Reparaciones»). Configuración de la instalación, como el tipo de concepto. **Cambiarla aquí a secas no basta**: la pasarela mantiene su propia lista blanca, así que es una decisión de dos dueños | `$ajustes`, `35` |
| `GRAFICO_MAX_BYTES` | **F-012** · el tope propio del PDF, comprobado **antes** de llamar a la pasarela. **No debe superar el suyo** (10 MB): subirlo aquí solo compra un rechazo más tardío, con el fichero ya mandado por el proxy | `$ajustes`, `10485760` |

**Y dos que NO son nuestras y sin las cuales `/api/adjuntar` responde 503**: la
escritura documental de `sigrid-api` (`SIGRID_DOCUMENT_WRITE_ENABLED`,
`SIGRID_DOCUMENT_WRITE_DATABASE` y sus listas blancas de `contip` y
`gratipide`) es configuración **de su dueño** y es una **precondición** de esta
feature. No se toca desde aquí: se pide. Qué se rompe si alguien la cambia está
en `docs/INTEGRACION.md` §6.

**Por qué la raíz también es un secreto de vault**, si no autentica nada: por lo
mismo que `pg-host`. Es un **host interno**, y esos no pueden quedar escritos en
el repositorio. Lo único que se ve en las App Settings de la Function App es el
**nombre** del secreto dentro de una URI.

**Y por qué el nombre de la base NO lo es**, aunque el 2026-09-03 lo fuera
durante unas horas: porque **ya está escrito en documentos versionados de este
repositorio** —`docs/referencia/03_modelo_posventa_sigrid.md`,
`specs/F-009-cierre-sigrid/design.md`— y nadie va a redactarlos. Meterlo en el
vault no añadía seguridad real y sí un secreto más que subir a mano en cada
entorno: una oportunidad más de que un despliegue quede a medias. Es la
**Corrección 1** del mismo día.

**Los tres pasos, en uno**: `infra\14_paso0_sigrid.ps1` hace el aprovisionamiento
entero de esta tabla —los dos secretos del vault, las ocho App Settings con
`desplegar_backend.ps1 -SinPublicar`— y añade la comprobación que hasta ahora
solo se podía hacer mirando el portal: imprime el **estado** de las once
referencias a Key Vault (`Resolved` o el motivo del fallo) y termina en
`Paso 0 COMPLETO: 11/11 referencias resueltas` o en un código de salida distinto
de cero. Con `-WhatIf` **solo lee**: no invoca a ninguno de los dos scripts que
escriben, e imprime igualmente la tabla, así que sirve para preguntarle al
entorno qué le falta sin tocarlo. Es el Paso 0 del bloque 8 de F-009
(`progress/guion_bloque8_F-009.md` §1), y no sustituye a nada de lo de arriba:
lo invoca.

Faltando cualquiera de las tres, el endpoint responde `503` nombrando **todas**
las que falten de una vez, y **nunca** sus valores. `SIGRID_BASE_DATOS` la pone
el despliegue siempre. Las otras dos, si el vault no las tiene, dejan que la
Function App arranque igual pero con las referencias en error en el portal: se
cargan una vez con `cargar_secretos_postventa.ps1 -Solo sigrid-api-base-url
sigrid-api-key`, ejecutado **sin `-File`** (§2).

## 5 · Después de desplegar

```
powershell -ExecutionPolicy Bypass -File $HOME\verificar_despliegue.ps1 -BaseUrl <url-de-la-function> -UrlFront <url-del-front>
```

Comprueba tres cosas, todas de lectura: `GET /api/health` responde `200`,
`POST /api/archivar` responde `503` con la ventana cerrada, y la Static Web App
sin sesión redirige al inicio de sesión.

> **Desde el 2026-09-23, tras un despliegue por defecto la segunda no se hace**:
> la ventana de archivo queda abierta (§4), y con ella abierta el script no
> llama —subiría un PDF de verdad— y el veredicto sale `NO VERIFICADO`. Es la
> guarda funcionando, no un fallo del despliegue. Para una verificación
> completa con este script hay que desplegar con `-VentanasCerradas` (o cerrar
> la ventana con `22_ventana_archivo.ps1 -Cerrar`), verificar, y volver a
> abrirla. Cómo encaja este script con las ventanas abiertas por defecto está
> **pendiente de decisión**.

Lo que se anota en `progress/` son las cuatro líneas que imprime, **sin la URL
y sin ningún identificador**.

Y a mano, con **dos cuentas**: una miembro del grupo entra; una **no miembro
no entra**. Si entra, la asignación obligatoria no está aplicada: **se para**.

> **Al día 2026-08-25, las dos primeras comprobaciones ya no se pueden hacer
> por esa vía**, y no porque el despliegue esté roto: ver §5 bis. El script lo
> dice cuando pasa, en vez de dejar dos `NO` sin explicación.

## 5 bis · El host desnudo de la Function ya no responde

**Lo que se descubrió ejecutando T17 y T18 el 2026-08-25** (defecto 13 de
F-010). Desde que la Function App es **backend enlazado** de la Static Web App,
la plataforma le activa Easy Auth con el proveedor `azureStaticWebApps` y el
backend **solo acepta lo que entra por el proxy del front**. Preguntarle por su
nombre de host —cualquier ruta, `GET /api/health` incluido— devuelve:

```json
{"code":400,"message":"Login not supported for provider azureStaticWebApps"}
```

Ese cuerpo **no es nuestro**: lo escribe la plataforma antes de que la Function
se entere. Consecuencias prácticas:

- `verificar_archivo_dev.ps1 -BaseUrl <host de la Function>` **no puede
  funcionar**. El script reconoce ese 400 y lo explica en vez de morir con un
  `WebException`, pero no hay `-BaseUrl` que lo arregle.
- Las comprobaciones 1 y 2 de `verificar_despliegue.ps1` reciben lo mismo. Lo
  que sigue valiendo por esa vía es la 3, la del front.
- El backend **sí** está sano: se comprueba entrando al front y usando el
  circuito, que es como lo usa negocio.

### La vía que sí funciona: la consola del navegador, en el front

Con **sesión iniciada** en el front y la pestaña abierta, `F12` → **Consola**, y
se pega el fragmento entero. Va al **mismo origen**, así que pasa por el proxy
que autentica; por eso aquí no hay ninguna URL que escribir.

Antes de pegarlo: **la ventana de escritura tiene que estar abierta** (§4).
Desde el 2026-09-23 lo está tras un despliegue por defecto; hasta entonces se
abría para esto y se cerraba en cuanto terminaba, salga bien o mal.

```js
// T18 - verificacion de la subida a SharePoint, desde la consola del FRONT.
// El PDF es sintetico y la obra 0677 / incidencia RS26.08-0001 no son de nadie.
(async () => {
  const pdf = new TextEncoder().encode([
    "%PDF-1.4",
    "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
    "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
    "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >> endobj",
    "trailer << /Root 1 0 R >>",
    "%%EOF",
  ].join("\n"));

  // El MISMO hash en las dos llamadas: archivar dos veces el mismo parte es
  // justo lo que no debe producir un duplicado.
  const hash = "verificacion-t18-" + new Date().toISOString().replace(/\D/g, "").slice(0, 14);

  const llamar = async (etiqueta) => {
    const fd = new FormData();
    fd.append("hash", hash);
    fd.append("codigo_obra", "0677");
    fd.append("numero_incidencia", "RS26.08/0001");
    fd.append("veredicto", "apto");
    fd.append("destino", "archivo_y_cierre");
    fd.append("fichero", new Blob([pdf], { type: "application/pdf" }), "parte-sintetico.pdf");
    const r = await fetch("/api/archivar", { method: "POST", body: fd });
    const texto = await r.text();
    console.log(etiqueta + " -> HTTP " + r.status);
    console.log(texto);
    return texto;
  };

  const primera = await llamar("1/2 primera llamada");
  const segunda = await llamar("2/2 segunda llamada");
  console.log("LAS DOS RESPUESTAS SON IGUALES:", primera === segunda);
})();
```

Lo que se anota en `progress/` es el **código HTTP de cada llamada** y el
**nombre del fichero**, sin la URL, sin el `item_id` y sin ningún GUID.

**Un `500` con cuerpo hablado** —«el parte SÍ se ha subido a SharePoint, pero
no se ha podido dejar constancia»— significa que el PDF está arriba y que lo
que falló fue la traza: mirar §5 ter antes de repetir nada.

## 5 ter · Por qué el archivado no puede completar todavía

La tabla `archivos` tiene una **clave ajena contra `partes`**: la traza de un
parte que no está guardado no se puede escribir. Y hoy **no hay ningún endpoint
que guarde el parte**: eso es **F-019**, que sigue `pending`.

Así que, tal y como está desplegado, `/api/archivar` **sube el fichero y
después falla al dejar la traza**, con parte sintético y con parte real. La
subida a SharePoint —el criterio de F-006— sí se puede dar por verificada; el
circuito completo, no, hasta que exista F-019.

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
