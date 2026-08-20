<!-- docs/ARCHITECTURE.md -->
# Arquitectura · postventa-incidencias

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
>
> Lo marcado `[PENDIENTE]` está sin decidir y **bloquea** la feature que lo
> necesite: no se resuelve inventando, se pregunta al humano.

## Qué hace este proyecto

Automatiza el circuito de los **partes de posventa firmados** del
departamento de Posventa. Entra una remesa escaneada —un PDF con varios
partes, un ZIP o una carpeta— y salen tres cosas: cada parte troceado,
validado y renombrado con la convención de Posventa; archivado en
SharePoint; y su incidencia cerrada en Sigrid.

Lo usa el departamento de Posventa (interlocutora: Ana Bello, Jefa de
Posventa). Se despliega en Azure con el patrón de nóminas: **Static Web App**
para el front y **Function App en Python** para el backend, con
autenticación de Entra ID.

Hoy ese trabajo es manual: alguien abre el PDF, localiza cada parte,
comprueba que está firmado, lo renombra `CHALET XX - Nº INCIDENCIA`, lo
guarda y lo cierra a mano en Sigrid.

## Capas y estructura

Monorepo con un servicio por responsabilidad, igual que `partes` y
`albaranes`. Un solo arnés, en la raíz.

```
services/
  postventa-api/            # backend: Function App Python
    domain/                 # entidades puras: Parte, Remesa, Validacion, Firma
      models/
      ports/                # interfaces: ExtractorPort, ArchivoPort, ErpPort
    application/
      pipelines/            # orquestación por pasos (abajo)
      services/
    infrastructure/
      documentos/           # adaptadores de los ficheros que entran: PDF y ZIP
      llm/                  # adaptador Gemini (y los que vengan) + su fábrica
      prompts/              # carga de config/prompts.yaml
      sharepoint/           # adaptador Graph + su fábrica (F-006).
                            # ÚNICO paquete del servicio que conoce Graph:
                            # ni domain/ ni application/ importan httpx
      sigrid/               # cliente de sigrid-api
      persistencia/         # PostgreSQL
    interface_adapters/api/ # handlers HTTP de la Function
    config/                 # settings (pydantic-settings) y prompts.yaml
  postventa-front/          # front estático: HTML + Tailwind CDN + Alpine.js
infra/                      # scripts PowerShell de despliegue
tests/                      # unit tests: sin red, sin BBDD, sin IA
```

### Pasos del pipeline

1. **Ingesta** — normaliza la entrada (PDF suelto, ZIP, varios ficheros,
   carpeta seleccionada en el navegador) a una lista de PDFs.
2. **Troceado** — parte cada PDF de remesa en documentos de **un parte**,
   detectando el comienzo por la plantilla impresa. La señal es el pie que
   imprime Sigrid: una página cuyo pie diga `Página N` con N ≥ 2 es la segunda
   hoja del parte anterior. Esa señal **solo se puede leer si el PDF trae capa
   de texto**; un escaneo sin OCR no la tiene, así que el troceado degrada a
   «una página, un parte» y cada parte declara en `modo_deteccion` cómo se
   troceó, para que nadie confunda «no había parte de dos hojas» con «no se ha
   podido mirar». Recuperar el parte de dos hojas en remesas escaneadas es
   F-014, apoyándose en la lectura multimodal del paso 3.
3. **Extracción** — modelo multimodal sobre las páginas del parte: promoción,
   código de obra, **unidad**, nº de incidencia, fecha de servicio,
   descripción **y todo lo manuscrito** (DNI, observaciones). Un escaneo no
   tiene capa de texto: esto es visión. Tres precisiones que decidió F-003:
   - **Cada campo viaja con su confianza** (`confianza_pct`, entero 0–100),
     también los manuscritos. Un dato leído a medias no vale lo mismo que uno
     impreso, y quien valida (paso 4) necesita saberlo.
   - **Lee el «Página N» del pie impreso y lo devuelve, pero no reagrupa
     nada.** El modelo ve ese pie aunque el escaneo no tenga capa de texto,
     que es justo lo que el troceado no pudo leer. Unir las dos hojas de un
     parte con ese dato es **F-014**; la extracción no toca `paginas_origen`
     ni el troceado.
   - **No juzga la firma ni dice si el parte es válido**: eso es el paso 4.
   El dato de la unidad se llama **`unidad`** en todo el proyecto: el papel lo
   imprime con la etiqueta «Vivienda» y el backlog lo llamaba «chalet», pero
   `unidad` es como lo nombra la estructura de archivo de Posventa
   (`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`). Son tres nombres del
   mismo dato y en el código hay uno solo.
4. **Validación** — qué se hace con el parte. Lo decidió F-004, y son reglas
   de **dominio puro**: sin red, sin base de datos y sin IA, para poder
   probarlas enteras sin un proveedor delante.
   - **Los campos que deciden son dos**: código de obra y nº de incidencia. Un
     campo cuenta como leído si trae valor —«solo espacios» es vacío— y su
     confianza llega al umbral (**50**, constante del dominio y no
     configuración: aflojar una regla de negocio no puede ser un cambio de
     variable de entorno).
   - **La firma se lee aparte**, con su propio prompt y su propia llamada
     (`POST /api/firma`), y se clasifica en `humana`, `marca_simple`,
     `casilla_vacia` o `ilegible`. Ante cualquier duda, `ilegible`: nunca se
     da por firmado lo que no se entendió. Una `humana` con confianza por
     debajo del umbral **se publica ya como `ilegible`**, para que la etiqueta
     y el motivo no se contradigan delante de quien los lea.
   - **Dos destinos, porque son dos trabajos para dos personas distintas**:
     `cola_validacion_humana` es «hay algo que **decidir**» —el parte está
     completo y firmado, pero el cliente escribió algo, y la transcripción
     viaja con él—; `revision_manual` es «hay algo que **arreglar**»: falta un
     campo decisivo o no hay firma humana, y toca volver al papel.
   - **Lo que NO hace este paso**: comprobar contra Sigrid que la incidencia
     exista y esté abierta —eso necesita red, es **F-008/F-009** y es una
     segunda puerta, posterior y aparte—, e interpretar **qué dice** la
     observación, que es **F-016**. Guardar la cola es F-005; pintarla,
     F-007/F-011.
5. **Nombrado** — `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`: código de obra,
   código de incidencia y sufijo. **Dominio puro** (`domain/models/nombrado.py`):
   sin reloj, sin red y sin configuración, para que volver a nombrar un parte
   meses después dé exactamente el mismo fichero. Cuatro reglas que no se
   negocian:
   - **La barra del código de incidencia pasa a guion.** `RS26.08/0123` se
     nombra `RS26.08 - 0123`: la barra es un separador de ruta y dejarla
     partiría el fichero en dos carpetas.
   - **Los ceros a la izquierda se conservan.** `0677` nunca es `677`:
     `int("0677")` es un bug, no una normalización, y `677` es otra obra.
   - **El sufijo va literal.** ` PARTE FIRMADO` en mayúsculas y `.pdf`: es lo
     que ya usa Posventa y lo que distingue el parte conformado.
   - **Un nombre imposible es un error, nunca un saneo silencioso.** Si falta
     un código o el nombre lleva algo que SharePoint no admite, el parte va a
     revisión manual. Sustituir el carácter raro por `_` archivaría en el
     archivo de Posventa un fichero que nadie pidió, y nadie se enteraría.
6. **Archivo** — subida a SharePoint, en `<carpeta base>/<código de obra>/`.
   **Solo se archiva lo que el paso 4 declaró apto**; con cualquier otro
   destino no se sube nada y ni siquiera se crea la carpeta. Reprocesar una
   remesa no puede duplicar, y para eso hay **tres capas**:
   - **traza** — si ya consta archivado ese `hash` de parte, no se llama a
     nadie: ni token, ni red, ni bytes;
   - **reemplazo** — la subida pide **siempre** reemplazar el homónimo, nunca
     renombrar. Renombrar produce el `... (1).pdf` que el criterio de
     aceptación prohíbe, y es el comportamiento por defecto de más de un
     cliente de Graph;
   - **carpeta** — crearla dos veces es un éxito, no un error.
7. **Cierre** — dry-run contra `sigrid-api`, confirmación del usuario, y solo
   entonces `commit: true`.

### Por qué el proceso va parte a parte y no de una tacada

La Function App corta a los **230 s**. Una remesa de 5 MB con veinte partes,
a una llamada de IA por parte, se pasa de largo. Por eso el contrato HTTP es:
`POST /split` (rápido, devuelve N partes) y luego **una llamada por parte**
desde el front, con concurrencia limitada. Efecto lateral bienvenido: barra
de progreso real.

### Por qué el front sube los ficheros aunque el usuario "indique una ruta"

Una Function App en Azure no ve `C:\...` ni un recurso de red interno. El
front usa el selector de carpeta del navegador: el usuario elige la carpeta
igual que hoy, y por debajo se suben los PDFs.

## Semántica de dominio imprescindible

1. **La unidad de trabajo es el parte, no el fichero.** Un PDF de remesa
   contiene N partes de N incidencias distintas. Nada del dominio se razona
   "por fichero".
2. **`RS26.08 – 0123` es el código de la incidencia**, no obra + número: lo
   emite Sigrid entero (serie + correlativo). El **código de obra es otra
   cosa** —`0677` en Mirasierra— y va impreso en el parte, en su propio
   campo. No confundirlos es lo que decide el nombrado y la carpeta.
3. **La firma debe ser humana.** Una casilla vacía, una aspa, o un trazo
   geométrico sin estructura de firma **no** son conformidad del cliente. Un
   parte sin firma válida no se archiva ni se cierra: va a revisión manual.
   Solo firma el cliente: la columna del técnico viene vacía en toda la
   remesa de ejemplo, así que exigirla dejaría fuera todos los partes.
   **Cómo convive esto con «las observaciones son el único motivo de
   rechazo»** (3 bis), que parece lo contrario: son dos cosas distintas y las
   dos se sostienen. El alcance de «único motivo» son **los datos
   manuscritos** —DNI, fecha, horas, nombre—, no la firma, que no es un dato
   transcrito sino la conformidad misma; y el criterio está redactado sobre
   **la cola**: a la cola de validación humana no entra nadie más que quien
   trae observaciones. Un parte sin firma humana no va a la cola: va a
   revisión manual, que es otro destino y otro trabajo. Si se leyera «único
   motivo» como «lo único que impide ser apto», chocaría con el criterio
   —de la misma lista— de que un parte sin nº de incidencia nunca queda apto.
3 bis. **Firmado no es conforme.** En la remesa de ejemplo hay un parte
   firmado cuya observación manuscrita dice "se aprecia que se han hecho
   parcheados, no se reparó la totalidad". **Un parte con observaciones
   manuscritas nunca se cierra solo**: va a revisión manual con el texto
   delante de quien decide. Cerrarlo por tener firma sería dar por resuelta
   una reparación que el cliente dice que no lo está.
   Precisado el 2026-08-19, y manda sobre el diseño de F-004:
   - **Las observaciones manuscritas son, de momento, el único motivo de
     rechazo.** Ningún otro dato manuscrito descalifica el parte.
   - **Rechazado no es descartado.** El parte va a una **cola de validación
     humana** que presenta las observaciones transcritas para que una persona
     decida. Ni se cierra solo ni se tira: espera a que alguien lo mire.
   - El dimensionado esperable de esa cola sale del dato real: en la remesa
     de Mirasierra son **2 partes de 22** (~9 %).
   - **Interpretar automáticamente el contenido de la observación** —separar
     la inocua de la que impide dar la reparación por buena, y así encoger la
     cola humana— **no es F-004**: es **F-016**, dada de alta el
     2026-08-19 en `harness/features.json` y bloqueada por F-004. F-004 detecta que hay
     observaciones y las transcribe; no las juzga.
4. **Lo manuscrito es dato de primera, no decoración.** DNI y observaciones
   se escriben a mano y hay que extraerlos. Descartarlos porque "no es texto
   impreso" es un bug, no una simplificación.
4 bis. **No se exige lo que la realidad deja en blanco.** Fecha de servicio,
   horas, nombre y DNI del cliente están vacíos en casi toda la remesa. Una
   validación que los exija manda a revisión manual el 100 % de los partes.
   Los únicos campos que deciden son: código de obra, nº de incidencia,
   firma y observaciones.
   En particular, y aunque suene contraintuitivo: **un parte sin DNI del
   cliente pasa como conforme**. La ausencia de DNI manuscrito no descalifica
   nada. El dato real lo respalda: en la remesa de Mirasierra solo **7 de los
   22 partes** traen DNI, así que exigirlo dejaría fuera a dos tercios de una
   remesa normal.
5. **El número de incidencia lo emite Sigrid** y se escribe `RS26.08/0123`
   (con barra) en el ERP y en el parte impreso, pero con guion en el nombre
   del fichero. Sin él no se puede nombrar ni
   cerrar nada: el parte va a revisión manual, nunca se inventa ni se deduce.
6. **Cerrar en Sigrid es escritura en producción.** Siempre dry-run primero;
   `commit: true` solo después de confirmación explícita (del usuario en el
   front, o de su preferencia de auto-cierre guardada).
7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**
   Archivar un parte inválido ensucia el archivo de Posventa; cerrarlo en
   Sigrid da por resuelta una incidencia que sigue viva.
8. **El nombre del fichero es `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`**
   —por ejemplo `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`— y la carpeta va por
   código de obra. El sufijo se conserva porque distingue el parte conformado
   de cualquier otro documento de la misma incidencia.
   Los separadores se normalizan a ` - ` con guion normal: el código que emite
   Sigrid puede traer guion largo (`–`), y un nombre de fichero no es sitio
   para depender de eso.
9. **Reprocesar una remesa no puede duplicar nada.** El mismo parte, subido
   dos veces, es el mismo parte: se identifica por hash del PDF troceado y
   por número de incidencia.

## Acceso a datos y sistemas externos

| Sistema | Uso | Límites |
|---|---|---|
| `sigrid-api` | **Única** vía al SQL Server de Sigrid. Lectura de la incidencia; cierre por escritura. | Máx. 1.000 filas por petición; el balanceador corta a 230 s. La escritura está apagada por defecto y los endpoints de dominio son dry-run salvo `commit: true`. |
| SharePoint (Graph) | Archivo de los PDF validados. **Mientras estemos en dev**, biblioteca propia en el sitio de **IT** (donde vive la de albaranes), ruta `Postventa/<código de obra>/`. Identidad **app-only** (client credentials) y `httpx` como cliente, igual que `partes`. El destino es **configuración**: `SHAREPOINT_SITE_ID`, `SHAREPOINT_DRIVE_ID`, `SHAREPOINT_CARPETA_BASE`, `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_TIMEOUT_S`, `GRAPH_REINTENTOS`. | **PUERTA DE ENTORNO**: subir solo se permite con `ENTORNO` en `dev` o `pro` **y** `ARCHIVO_HABILITADO` encendido, que está **apagado por defecto**. Las dos se comprueban en la fábrica **y en el constructor del adaptador**, así que componer las piezas a mano tampoco deja subir desde un puesto de trabajo; y la guardia de red de la suite impide que un test abra la conexión. Al pasar a producción el archivo se muda a la biblioteca de Posventa, respetando la estructura que ya usan (`Postventa - Documentos / <cod> <OBRA> / PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`): es la feature **F-013**, y sale casi gratis porque la ruta es configuración. Qué consumimos y qué se rompe si alguien mueve la biblioteca o revoca el permiso: **`docs/INTEGRACION.md`**. |
| PostgreSQL `psql-albaranes-rs9k2` | Estado de remesas, partes, validaciones, archivo, cierres y preferencias de usuario. **Base propia `postventa` y schema propio `postventa`** dentro de ella, con `search_path` sin `public`. El DDL se aplica idempotente al arranque; la base y el rol los crea el humano, nunca la aplicación. | Servidor **compartido** con albaranes y compañía: nunca se tocan parámetros de servidor, autenticación ni almacenamiento, ni se sale del schema propio; los PDF no entran en la base. Qué consumimos, con qué variables y qué se rompe si alguien toca el servidor: **`docs/INTEGRACION.md`**, fuente de verdad que se copia a `azure-apps/`. |
| Gemini | Extracción multimodal y clasificación de firma. | Detrás de `ExtractorPort`. **El proveedor se elige con `IA_PROVIDER` y el modelo con `GEMINI_MODEL`** (por defecto `gemini-3.7-flash`): cambiar cualquiera de los dos es tocar configuración, nunca el pipeline, el dominio ni los puertos. El prompt vive en `config/prompts.yaml`, fuera del código. |
| Entra ID | Autenticación del front y de la tarjeta del portal. | **No existe** grupo de Posventa: hay que crearlo. Hasta entonces, ni el acceso ni la tarjeta se pueden cerrar. |

**Prohibido desde local**: escribir en Sigrid (ni siquiera con `commit:false`
contra endpoints que no sean de lectura), escribir en el SharePoint de
Posventa y ejecutar DDL en el PostgreSQL compartido fuera del schema propio.

### Posventa en Sigrid: lo que ya se sabe

Está en `azure-apps/sigrid_tablas.md` (diccionario de la BBDD) y en
`azure-apps/sigrid_api.md` §9. **Se lee antes de diseñar nada contra Sigrid**;
no se duplica aquí.

| Tabla | Qué es |
|---|---|
| `upv` | **Unidad Postventa**: `obride` (obra), `cliide` (propietario), `peride` (contacto) y las fechas de garantía: vicios/defectos, habitabilidad/instalaciones, estructura, escrituración, visita del técnico. |
| `rcp` | **Reclamación** = la incidencia. `upvide` a la unidad, `fec`, `cliide`, `recide` (quien reclama), `tex` (descripción), `motrcp`, `resubi` (ubicación), `texurg` (urgencia), `ofcide` (oficio) y **`solrcp` (solución)**. Clase en `auxrcp`, tipo en `auxtrcp`. |
| `rcpint` | Intervinientes de la reclamación, con `cauave` (causante de la avería). |
| `act`, `tar` | Actividades y tareas colgadas de la reclamación (`act.rcpide`, `tar.rcpide`). |

**`rcp` es una extensión 1:1 de `con`**, así que:

- El **estado no está en `rcp`**: está en `con.est`, con el catálogo en
  `conest` (join por `con.tip = conest.tip AND con.est = conest.est`).
  **Cerrar una incidencia es mover `con.est`** al estado de cierre.
- **Nunca se hardcodea el número de un estado**: es configurable por
  instalación y se resuelve contra `conest`.
- El código legible y el nombre salen de `con.cod` / `con.res`, no de la
  extensión.

### Cómo se cierra hoy una incidencia, a mano

Documentado por Alicia Echevarría (Posventa) en su guía del 2026-08-18, que
vive en `docs/referencia/` (el original `.docx` no se versiona):

1. **Renombra** el parte firmado: `RS26.08 – 0123 PARTE FIRMADO`.
2. Entra en la obra → unidad de obra → busca la incidencia → **gráficos →
   importar → importar desde archivo**, y sube el PDF. Rellena unos datos en
   esa ventana.
3. Vuelve a la incidencia y **cambia el estado a CERRADA** ("Opción 3. Cerrar
   parte"), y confirma el mensaje.

También se puede localizar la incidencia por la **pestaña de reclamaciones**,
sin entrar en la unidad.

### Qué es eso en tablas, y qué implica

El "importar gráfico" son dos tablas:

| Tabla | Papel |
|---|---|
| `gra` | El documento: `ima` (binario), `nom` / `nomori` (nombre), `cod`, `res`, `fec`, `usu`, `gratipide` (clase, catálogo `auxgra`), `guid`. |
| `rcg` | **Gráficos en conceptos**: la N:N que ata el gráfico (`gra`) al concepto (`con`) de la reclamación, con `pos` y `cla`. |

Por tanto **cerrar una incidencia son tres escrituras**, y en este orden:
`INSERT` en `gra` con el PDF → `INSERT` en `rcg` vinculándolo a la
reclamación → `UPDATE con.est` al estado de cierre. Las tres, o ninguna.

**Consecuencia dura para el diseño**: `sigrid-api` hoy sabe **leer**
documentos (`POST /api/documents/read` contra `ruesma_rep`) pero **no sabe
escribirlos**. No hay endpoint de dominio para esto, y `sql/write` no reserva
`ide` con applock ni está pensado para BLOBs. Así que **F-009 depende de un
endpoint nuevo en `sigrid-api`** —otro repositorio, otro proyecto—: se
propone al humano, no se implementa aquí (regla de LÍMITE DE SERVICIO).

### Alcance del cierre en la primera versión

Posventa hace hoy dos cosas: sube el PDF a Sigrid como gráfico **y** cambia el
estado. **En la primera versión solo se hace lo segundo**: el parte se archiva
en SharePoint y en Sigrid únicamente se mueve `con.est` a CERRADA.

Eso quita de en medio la dependencia de un endpoint nuevo en `sigrid-api`
—escribir el BLOB de `gra` y su fila en `rcg`— que queda como feature futura
(F-012). Un `UPDATE` de estado con `WHERE` no reserva `ide` ni maneja
binarios, así que cabe en la escritura genérica de la pasarela.

**Aviso serio, descubierto en las capturas de la guía**: el proceso «Cerrar
parte» de Sigrid **comprueba que la reclamación tenga algún gráfico o
documento multimedia asociado** antes de cerrarla — por eso el menú ofrece
además una opción 6, "Cerrar parte sin archivo (RPV)". Un `UPDATE con.est`
directo se saltaría esa comprobación y dejaría la incidencia cerrada sin su
parte, que es justo lo que el ERP impide hacer a mano. Y «Cerrar parte» es un
**proceso**, no un campo: no consta qué más toca. Hasta que F-008 lo aclare
en el ERP real, **el alcance del cierre en v1 está en el aire**.

### Lo que queda por confirmar contra el ERP real (F-008, solo lecturas)

- Qué `con.tip` corresponde a la reclamación y qué estados declara `conest`
  para ese tipo, incluido el de cierre ("CERRADA").
- **Qué es `RS26.08` y qué es `0123`** en `RS26.08 – 0123`: si es código de
  obra + número de incidencia, o si `RS26.08 – 0123` es entero el `con.cod`
  de la reclamación (serie `sercon` + correlativo). Decide el nombrado.
- Qué campos se rellenan al importar el gráfico (la guía dice "añado los
  datos que subrayo" y lo enseña en una captura): probablemente `res`, `cod`
  y la clase `gratipide`.
- Si la tabla `gra` vive en `ruesma` o en `ruesma_rep`, y si cerrar exige
  además rellenar `solrcp` o alguna fecha.

## Infra y despliegue

- **Front**: Azure Static Web App sirviendo `services/postventa-front/`, con
  auth de Entra en `staticwebapp.config.json` y la Function App enlazada.
- **Backend**: Azure Function App (Python), desplegada desde
  `services/postventa-api/`.
- **Scripts** en `infra/`, re-ejecutables, en PowerShell, siguiendo el
  patrón de `partes/infra`.
- **Secretos**: en App Settings con referencia a Key Vault. `.env` es solo
  local y **nunca** viaja al despliegue ni a git.
- **Desarrollo local**: `func start` para el backend y el `dev_server.py` del
  front con proxy a `/api/*`, igual que en nóminas.

### Los recursos, y dónde vive cada uno (F-010)

Grupo de recursos **propio**, como `partes`. Los nombres se declaran en **un
solo sitio**, `infra/00_vars_postventa.ps1`: cambiar uno es cambiar una línea.

| Recurso | Nombre | Región |
|---|---|---|
| Grupo de recursos | `rg-postventa-dev` | `spaincentral` |
| Function App (Flex Consumption, Python) | `func-postventa-dev` | `spaincentral` |
| Cuenta de almacenamiento | `stpostventadev` | `spaincentral` |
| Key Vault **propio** | `kv-postventa-dev` | `spaincentral` |
| Identidad gestionada | `id-postventa-dev` | `spaincentral` |
| Log Analytics | `log-postventa-dev` | `spaincentral` |
| Application Insights | `appi-postventa-dev` | `spaincentral` |
| Static Web App (SKU Standard) | `swa-postventa-ruesma` | `westeurope` |

Se **reutiliza** y no se crea: `psql-albaranes-rs9k2`, que vive en el grupo de
recursos de albaranes y no es nuestro.

### Por qué el front está en otra región que el backend

**No es una elección**: la Static Web App **no existe en `spaincentral`**. El
backend se queda en `spaincentral` porque ahí está el PostgreSQL. El salto
entre regiones se paga en latencia y se descuenta del presupuesto de abajo.

### El presupuesto de 45 segundos

El proxy de la Static Web App **corta cualquier petición a los 45 s**. Es un
límite de la plataforma —`azure-apps/portal.md` §9, aprendido con la app de
nóminas—, y manda sobre los tiempos de espera del proyecto:
`IA_TIMEOUT_S` y `GRAPH_TIMEOUT_S` en el backend, `TIMEOUT_PETICION_MS` en el
front. Los tres tienen que quedar **por debajo**, para que quien aborte sea el
front —que sabe reintentar y liberar la plaza de la cola— y no el proxy, que
devuelve un error opaco que nadie ha generado.

El `functionTimeout` de cinco minutos de `host.json` **no es** el límite que
aprieta: es el techo de la Function, no el del proxy.

### Los endpoints están en `ANONYMOUS`, y es deliberado

Con un backend enlazado, la Static Web App autentica al usuario y reenvía la
cabecera `x-ms-client-principal`; **no** una clave ni un token que la Function
pueda exigir. `auth_level=FUNCTION` rompería el front. El control de acceso
está en capas y ninguna vive en el `auth_level`: grupo de Entra con asignación
obligatoria, **ventana de escritura** de `/api/archivar` (`ARCHIVO_HABILITADO`,
que se despliega apagado), tope de gasto en el proveedor de IA y, si resulta
compatible, restricción de acceso público. Está explicado en la cabecera de
`services/postventa-api/function_app.py` y en `docs/DESPLIEGUE.md` §4.

El runbook completo del despliegue está en **`docs/DESPLIEGUE.md`**.
