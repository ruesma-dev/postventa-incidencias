<!-- docs/INTEGRACION.md -->
# Integración con el ecosistema · postventa-incidencias

> **Origen**: este repositorio. **Fecha**: 2026-08-26. **Última feature que
> lo tocó**: F-019 (nació con F-005).
>
> Este documento es la **fuente de verdad** de lo que `postventa-incidencias`
> consume del ecosistema de Ruesma y de lo que expone a los demás. Se copia a
> `azure-apps/postventa_incidencias.md` (regla 1 del `README.md` de
> `azure-apps/`), y **el dueño del documento es este proyecto**: si cambia lo
> que consumimos, se actualiza aquí en el mismo trabajo, no después.
>
> **Ni un valor de conexión.** Aquí van nombres de recurso y nombres de
> variable de entorno; ni hosts, ni usuarios, ni contraseñas, ni IDs de
> suscripción, tenant u objeto, ni direcciones internas. Lo vigila
> `services/postventa-api/tests/test_f005_integracion_sin_secretos.py`, que
> falla si alguno entra.

## 1 · Qué consumimos hoy

| Recurso | Compartido con | Qué hacemos | Desde |
|---|---|---|---|
| PostgreSQL `psql-albaranes-rs9k2` | `albaranes`, `partes`, `datamart-seg-anual` | Base propia `postventa`: estado de remesas, partes, validaciones, archivo y cierres | **F-005** |
| `sigrid-api` | todo el ecosistema | Lectura de la incidencia; cierre por escritura desde el entorno desplegado | F-008 / F-009 |
| SharePoint (Graph) | IT | Archivo de los PDF validados | F-006 |
| Gemini | — | Extracción multimodal y clasificación de firma | F-003 |
| Entra ID | todo el ecosistema | Autenticación del front y de la tarjeta del portal | F-010 |

**Lo nuevo de F-005 es la primera fila**, y es la única que mete a este
proyecto como **cuarto inquilino** de un servidor que ya usaban otros tres. El
resto de este documento va de eso.

## 2 · La base de datos: qué pedimos y qué no tocamos

```
Servidor  psql-albaranes-rs9k2      COMPARTIDO — no tocamos nada suyo
   └── Base  postventa              propia; la crea el humano, una vez
         └── Esquema  postventa     propio; lo crea el DDL de la aplicación
               ├── remesas                 una subida de partes
               ├── partes                  la unidad de trabajo, PK = hash del PDF
               ├── validaciones            la cola de revisión humana
               ├── archivos                traza de lo subido a SharePoint
               ├── cierres                 traza del cierre en Sigrid
               └── preferencias_usuario    auto-cierre por usuario
```

**Base propia y esquema nominado, las dos cosas.** La base propia es cómo
aísla el ecosistema (`albaranes`, `partes`, `sigrid_dm`: un servidor, varias
bases). El esquema nominado —en vez del `public` que usan los demás— es
cinturón sobre tirantes: el `search_path` de nuestras sesiones es solo
`postventa`, **sin `public`**, así que una sentencia sin cualificar no puede
aterrizar donde no debe ni por descuido ni por copiar y pegar.

### Lo que este proyecto NO hace, y consta por escrito

| No hacemos | Por qué |
|---|---|
| `CREATE DATABASE` desde la aplicación | Crear bases al arrancar un servicio, en un servidor de producción ajeno, es justo lo que prohíbe `CLAUDE.md`. La base y el rol los crea el humano con `infra/crear_base_postventa.ps1`, una vez |
| `CREATE ROLE`, `GRANT`, `ALTER SYSTEM`, `CREATE EXTENSION` | Son cambios a nivel de servidor y afectan a los otros tres proyectos. Están en la lista negra del validador de DDL, que se ejecuta **antes de abrir la conexión** |
| Tocar el esquema `public` de ninguna base | Es donde trabajan `albaranes` y `partes` |
| Guardar los bytes de los PDF | El disco es compartido, solo crece y ya se llenó una vez (ver §5). Los PDF van a SharePoint; en la base quedan metadatos y hash |
| Guardar JSON crudo de la extracción | Duplicaría datos personales y engordaría el disco de todos |

El DDL se aplica **idempotente al arranque** (`CREATE ... IF NOT EXISTS`,
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`), es
el mismo patrón que ya usan `albaranes` y `partes`, y va protegido por un
`pg_advisory_lock` para que dos instancias arrancando a la vez no choquen. Un
DBA que mire `pg_stat_activity` nos verá con un `application_name` propio del
servicio y del entorno.

## 3 · SharePoint: dónde se archivan los partes

**Lo nuevo de F-006.** Con esta feature el proyecto pasa a consumir un segundo
recurso compartido: **SharePoint del tenant**, a través de **Microsoft Graph**.
Los dueños de `albaranes` y de `partes` —que ya archivan en ese mismo sitio—
tienen derecho a saber que hay otro inquilino y otra aplicación con permiso de
escritura sobre él.

### Qué escribimos y dónde

| Qué | Valor |
|---|---|
| Sitio | El de **IT**, el mismo donde vive la biblioteca de albaranes. Por variable: `SHAREPOINT_SITE_ID` |
| Biblioteca | **Propia de este proyecto**, no la de nadie más. Por variable: `SHAREPOINT_DRIVE_ID` |
| Carpeta raíz | `SHAREPOINT_CARPETA_BASE`, y debajo **una carpeta por código de obra** |
| Qué se sube | El PDF de **un parte ya validado**, y nada más. Ni la remesa entera, ni ficheros intermedios, ni JSON |
| Cómo se llama | `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf` |
| Con qué identidad | **App-only** (client credentials) del app registration del proyecto |
| Con qué cliente | `httpx`, igual que `partes`. Decisión del humano del 2026-08-20 |

**Mientras estemos en dev es una biblioteca propia dentro del sitio de IT.** Al
pasar a producción el archivo se muda a la biblioteca de Posventa: es la
feature **F-013**, y sale casi gratis porque la ruta es configuración y no
código.

### Volumen esperado

Minúsculo, y por el mismo motivo que en §2: una remesa real ronda los **22
partes**, y un parte escaneado es del orden de cientos de kilobytes. El
crecimiento anual se cuenta en cientos de megabytes, no en terabytes. Una
subida por parte, sin listados de carpeta: se pide el fichero por su nombre
exacto, nunca el contenido entero de la carpeta de una obra.

### Permisos: qué necesitamos y qué tenemos hoy

Lo que la aplicación **necesita** es escribir en **una** biblioteca:
`Sites.Selected`, con esa biblioteca asignada explícitamente.

Lo que la aplicación **tiene hoy**, verificado el 2026-08-20, es más que eso:
además de `Sites.Selected`, dos permisos de aplicación que alcanzan a **todos
los sitios del tenant** y que vuelven irrelevante al primero. No es un fallo:
es lo que pasa al configurar `Sites.Selected`, que exige el paso extra de
asignar la biblioteca concreta por Graph, mientras que los amplios funcionan a
la primera.

**El humano decidió el 2026-08-20 arrancar así y recortar después**, para no
mezclar un cambio de configuración del tenant con una implementación. El
recorte es la feature **F-018 · Mínimo privilegio en Graph**, lo ejecuta el
humano en Azure —un agente no toca permisos del tenant— y **hasta que ocurra,
esta aplicación puede escribir en sitios de SharePoint que no son el suyo**.
Quien administre el tenant merece saberlo por escrito, y por eso está aquí.

### La puerta que impide subir desde un puesto de trabajo

`CLAUDE.md` prohíbe subir al SharePoint de Posventa desde local. Eso **no
depende de la disciplina de nadie**: el código lo impide con tres cierres
independientes.

1. `ENTORNO` tiene que ser `dev` o `pro`. Se comprueba en la fábrica **y en el
   constructor del adaptador**, así que componer las piezas a mano tampoco
   sirve.
2. `ARCHIVO_HABILITADO` tiene que estar encendido, y está **apagado por
   defecto**: un despliegue a medio configurar no sube nada.
3. La suite de tests no puede abrir conexiones de red, y ningún test construye
   un adaptador capaz de llegar a Graph.

La única subida real permitida se hace **desde el entorno desplegado**.

### Qué se rompe si alguien toca algo

| Si alguien... | Nos pasa esto | Aviso |
|---|---|---|
| Mueve, renombra o borra **la biblioteca** de dev | Dejamos de archivar: cada parte apto acaba con traza en estado `error`. No se pierde nada, el parte se reintenta, pero no avanza ni un cierre | Es nuestra: nadie más debería tocarla |
| Revoca el **permiso** de la aplicación sobre el sitio | Igual que lo anterior, y con un `403` que **no se reintenta**: la aplicación no insiste contra un permiso denegado | Coordinar con IT antes |
| Cambia la carpeta raíz sin avisar | Los partes nuevos se archivan en otro sitio y los viejos se quedan donde estaban. El archivo de Posventa queda partido en dos | Es cambiar `SHAREPOINT_CARPETA_BASE`: hay que decirlo |
| Rota el secreto de la aplicación sin actualizarlo | Dejamos de archivar con un `401`, tampoco reintentable | El secreto vive en Key Vault, nunca en el repositorio |
| Borra a mano un parte ya archivado | No lo detectamos: la traza sigue diciendo `archivado` y no se vuelve a subir | Reprocesar el parte no basta; hay que borrar su traza |

Y al revés, lo que **nosotros** podemos romperles: mientras los permisos sigan
siendo los amplios de hoy, esta aplicación **podría** escribir en cualquier
sitio del tenant. No lo hace, solo toca su biblioteca, pero la única garantía
real es el recorte de **F-018**.

## 4 · Variables de entorno (nombres, nunca valores)

Los nombres son deliberadamente los que ya usa el ecosistema, para que quien
despliegue no tenga que aprender dos vocabularios.

| Variable | Obligatoria | Notas |
|---|---|---|
| `PG_HOST` | sí, para persistir | Sin ella la aplicación arranca igual: `/health` no necesita base |
| `PG_PORT` | no | Puerto estándar de PostgreSQL por defecto |
| `PG_DB` | no | Por defecto, la base propia del proyecto |
| `PG_USER` | sí, para persistir | Rol de aplicación, propio de este proyecto |
| `PG_PASSWORD` | sí, para persistir | **Secreto**. En Azure va por referencia a Key Vault; nunca en el repositorio, ni en `.env.example`, ni en un fichero de despliegue |
| `PG_SCHEMA` | no | Por defecto, el esquema propio |
| `PG_SSLMODE` | no | Por defecto exige TLS, como pide Azure Flexible Server |
| `PG_MAX_CONEXIONES` | no | Techo bajo a propósito (§5, conexiones) |
| `PG_STATEMENT_TIMEOUT_S` | no | Ninguna consulta nuestra se eterniza en un servidor ajeno |
| `PG_LOCK_TIMEOUT_S` | no | Ni espera indefinidamente por un bloqueo |
| `PG_IDLE_IN_TRANSACTION_TIMEOUT_S` | no | Ni deja una transacción abierta ocupando una conexión |


### Las de SharePoint (F-006)

| Variable | Obligatoria | Notas |
|---|---|---|
| `ARCHIVO_HABILITADO` | no | **Interruptor maestro, apagado por defecto.** Sin encenderlo no se sube nada, pase lo que pase |
| `SHAREPOINT_SITE_ID` | no | El sitio del destino. No lo usa el adaptador, que va directo a la biblioteca; lo usan el script de verificación y este documento |
| `SHAREPOINT_DRIVE_ID` | sí, para archivar | La biblioteca donde se archivan los partes |
| `SHAREPOINT_CARPETA_BASE` | no | Carpeta raíz; debajo, una por código de obra |
| `GRAPH_TENANT_ID` | sí, para archivar | Tenant contra el que se pide el token |
| `GRAPH_CLIENT_ID` | sí, para archivar | La aplicación con la que se archiva |
| `GRAPH_CLIENT_SECRET` | sí, para archivar | **Secreto**. En Azure va por referencia a Key Vault; en local, solo en el `.env`, que no se versiona. Jamás en un log ni en un mensaje de error |
| `GRAPH_TIMEOUT_S` | no | La Function corta a los 230 s: una llamada colgada no puede comérselos |
| `GRAPH_REINTENTOS` | no | Intentos ante errores transitorios. Un `403` o un `404` **no** se reintentan |

Ninguna de estas variables tiene valor en el repositorio: `.env.example` y
`local.settings.json.example` llevan placeholders, y hay un test que lo
comprueba.

`POSTVENTA_PG_TEST_DSN` es aparte: solo la usa la suite de base de datos
(`tests_bbdd/`) contra una base **efímera y local**, y su `conftest.py` aborta
si apunta a un host que no sea local. La suite normal del proyecto no abre ni
una conexión.

## 5 · Qué le hacemos al servidor compartido, en números

Los tres límites que importan, y por qué nos importan:

**Disco.** El servidor tiene 32 GB compartidos, el almacenamiento **solo
crece, nunca decrece**, y el punto de restauración es del **servidor entero**:
no se puede volver atrás nuestra base sin arrastrar las ajenas. El 2026-08-09
el disco llegó al 93,4 % y el servidor quedó en solo-lectura diez minutos por
el build de otro proyecto. Ese precedente es el motivo de que ni los PDF ni el
JSON crudo entren en la base.

**Nuestro volumen esperado es minúsculo.** Una remesa real ronda los 22
partes; una fila de parte son unos cientos de bytes de texto más sus
confianzas. Con el ritmo previsto de Posventa, el crecimiento anual se cuenta
en megabytes, no en gigabytes. Si alguna vez deja de ser así, lo primero que
crecerá es `partes` y el primer sitio donde mirar es esta sección.

**Conexiones.** El servidor es pequeño y las conexiones las comparten cuatro
proyectos. Una Function App que escale a N instancias podría comérselas, así
que el techo de conexiones está bajo por defecto y las sesiones llevan los
tres timeouts de §4. Nada nuestro debería quedar colgado en
`pg_stat_activity`.

**CPU y memoria.** No ejecutamos analítica ni `VACUUM FULL` ni cargas masivas:
son inserciones y actualizaciones de una fila, con índices por número de
incidencia, código de obra y remesa.

## 6 · Qué se rompe si alguien toca algo

| Si alguien... | Nos pasa esto | Aviso |
|---|---|---|
| Cambia parámetros del servidor, autenticación o almacenamiento | Nos afecta igual que a `albaranes` y `partes`; es un cambio de los cuatro, no de uno | Avisar a los cuatro proyectos |
| Llena el disco desde otro proyecto | El servidor pasa a solo-lectura y **dejamos de poder guardar partes**: la validación humana se queda sin cola nueva | Ya pasó el 2026-08-09 |
| Borra o renombra la base `postventa` o su esquema | El servicio no arranca la parte de persistencia | Nadie más debería tocarla: es nuestra |
| Restaura el servidor a un punto anterior | Perdemos las filas posteriores a ese punto, sin manera de aislarlo | Coordinar antes: el PITR es del servidor entero |
| Toca el esquema `public` | A nosotros, nada: no tenemos ni una tabla ahí, y un test contra base efímera lo comprueba | — |

Y al revés, lo que **nosotros** podemos romperles: nada, mientras se cumplan
las reglas de §2. La única superficie compartida real es el **disco** y el
**cupo de conexiones**, y las dos están acotadas a propósito.

## 7 · Datos personales

La base guarda **datos personales de clientes**: DNI y observaciones
manuscritas del parte, además de la promoción y la unidad, que localizan una
vivienda. También el identificador opaco de Entra (`oid`) del empleado que
sube la remesa o confirma un cierre; nunca su correo ni su nombre.

Consecuencias para quien administre el servidor:

- El DNI vive en **una sola columna de una sola tabla**, nunca duplicado en
  otra ni en un blob; quien lo necesite hace `JOIN`.
- **Nunca** se escribe en logs, ni completo ni parcial.
- **Nunca** entra en el repositorio: los ejemplos de tests y specs son
  inventados y hay un test que barre el árbol buscando patrones de DNI y NIE.
- Una copia de la base, un volcado o una captura de pantalla del contenido de
  `partes` es un fichero con datos personales y se trata como tal.

El detalle columna a columna está en `specs/F-005-persistencia/design.md` §6.

## 8 · Qué exponemos nosotros

**Rellenada por F-010**, que es la feature que despliega el servicio. Hasta
entonces esta sección decía «hoy, nada»: el servicio solo corría en el puesto
de quien lo desarrollaba.

### Una aplicación de usuario, no una API para terceros

Lo que se expone es una **aplicación web para personas del grupo de Posventa**,
no un servicio que otro proyecto deba llamar. Ningún proyecto del ecosistema
consume esto, y nadie debería empezar a hacerlo sin hablarlo antes: el
contrato de los endpoints es interno y cambia con las features.

| Qué | Nombre del recurso | Quién entra |
|---|---|---|
| Front del piloto | `swa-postventa-ruesma` | Miembros del grupo `posventa-usuarios`, autenticados en Entra |
| Backend | `func-postventa-dev` | Solo a través del front: es el **backend enlazado** de la Static Web App |
| Tarjeta de acceso | `front-portal` (otro repositorio) | La misma restricción de grupo |

Los nombres de host **no se escriben aquí**, como ninguno del resto del
documento.

### Los endpoints, y qué hace cada uno

| Endpoint | Efecto |
|---|---|
| `GET /api/health` | Dice si el servicio vive. Sin datos y sin autenticación: lo usan el despliegue y el propio front |
| `POST /api/split` | Trocea una remesa. Sin efecto externo |
| `POST /api/extraer` | Llama al proveedor de IA. Gasta cuota |
| `POST /api/firma` | Llama al proveedor de IA. Gasta cuota |
| `POST /api/validar` | Solo reglas. Sin IA y sin efecto externo |
| `POST /api/remesa` | **Escribe** en `postventa.remesas` (esquema propio). Devuelve el `remesa_id` que hay que reenviar después |
| `POST /api/parte` | **Escribe** en `postventa.partes` y `postventa.validaciones`. Recalcula el veredicto con las reglas del dominio: nunca acepta el que venga en el cuerpo |
| `GET /api/cola` | **Lee** la cola de validación humana. Único endpoint que devuelve **dato personal acumulado** sin que el llamante aporte el PDF: tope duro de 500 entradas por llamada |
| `POST /api/archivar` | **Escribe** en la biblioteca de dev de SharePoint y deja traza en la base. Exige que el parte **ya conste guardado**: si no, responde 409 sin subir nada |

Los tres endpoints de F-019 **no dependen de `ARCHIVO_HABILITADO`**: escriben
en el esquema propio del proyecto, no en un sistema ajeno. Con la ventana de
escritura cerrada —que es como se despliega— se sube la remesa, se trocea, se
extrae, se valida, **se guarda** y se lee la cola; solo `POST /api/archivar`
responde 503.

Los nueve quedan en nivel **anónimo**, y **es deliberado**: con un backend
enlazado, la Static Web App autentica al usuario y reenvía una cabecera de
identidad, no una credencial que la Function pueda exigir. Quien lo cambie
rompe el front. Y ese nivel es **irrelevante desde internet**: la plataforma
activa Easy Auth con el proveedor `azureStaticWebApps` en el backend enlazado,
así que solo se acepta lo que entra por el proxy, y el proxy exige sesión y
pertenencia al grupo. El razonamiento completo y las capas de protección que
sí sostienen el acceso están en la cabecera de
`services/postventa-api/function_app.py` y en `docs/DESPLIEGUE.md` §4 y §5 bis.

### Qué NO está desplegado, y hay que decirlo antes de enseñarlo

| Qué falta | Feature | Consecuencia visible |
|---|---|---|
| El cierre de la incidencia en el ERP | **F-008** y **F-009** | Sigrid no se toca: el parte se archiva, la incidencia sigue abierta |
| Rehidratar la sesión al recargar el navegador | **feature nueva**, decidida el 2026-08-26 (D4 de F-019) | Lo guardado **queda guardado** y la cola sobrevive, pero si el usuario recarga la página **pierde el trabajo en curso**: volver a pintarlo exige leer una remesa entera con sus partes, y eso es un método de lectura nuevo en el puerto de persistencia |
| Mudar el archivo a la biblioteca real de Posventa | F-013 | Los partes aterrizan en la biblioteca de **dev** del sitio de IT |
| Recortar los permisos de Graph | F-018 | La identidad de aplicación conserva permisos amplios (ver §3) |

### Lo que este proyecto añade al ecosistema

- Un **grupo de recursos propio** y un **Key Vault propio**, como `partes`.
  Nada se mete en los de otros proyectos.
- Un **registro de aplicación nuevo** para el inicio de sesión, separado del
  de Graph: la credencial de mayor privilegio y la aplicación con la que se
  loguean los usuarios no comparten identidad.
- Una **tarjeta en el portal**, que es el único punto donde este proyecto
  cruza la frontera de otro repositorio. El bloque y el procedimiento están en
  `docs/DESPLIEGUE.md` §6.

## 9 · Dónde está cada cosa

| Qué | Dónde |
|---|---|
| El DDL, en `.sql` numerados | `services/postventa-api/infrastructure/persistencia/sql/` |
| El validador que lo revisa antes de aplicarlo | `services/postventa-api/infrastructure/persistencia/ddl.py` |
| Crear la base y el rol, una vez | `infra/crear_base_postventa.ps1` |
| Suite contra base efímera en Docker | `infra/pruebas_bbdd_efimera.ps1` |
| Diseño completo y decisiones de la persistencia | `specs/F-005-persistencia/` |
| El adaptador de SharePoint y su fábrica | `services/postventa-api/infrastructure/sharepoint/` |
| Comprobar el destino de dev, solo lecturas | `infra/verificar_destino_sharepoint.ps1` |
| Comprobar el archivo end-to-end en dev | `infra/verificar_archivo_dev.ps1` |
| Diseño completo y decisiones del archivo | `specs/F-006-sharepoint/` |
| Nombres de recurso, regiones y tags del despliegue | `infra/00_vars_postventa.ps1` |
| Runbook del despliegue y tarjeta del portal | `docs/DESPLIEGUE.md` |
| Comprobar el despliegue, solo lecturas | `infra/verificar_despliegue.ps1` |
| Diseño completo y decisiones del despliegue | `specs/F-010-despliegue/` |
| Documento gemelo del ecosistema | `azure-apps/postventa_incidencias.md` |
