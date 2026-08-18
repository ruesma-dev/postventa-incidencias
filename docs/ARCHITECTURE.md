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
      llm/                  # adaptador Gemini (y los que vengan)
      sharepoint/           # adaptador Graph
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
   detectando el comienzo por la plantilla impresa.
3. **Extracción** — modelo multimodal sobre las páginas del parte: promoción,
   chalet, nº de incidencia, fecha, descripción **y todo lo manuscrito**
   (DNI, observaciones). Un escaneo no tiene capa de texto: esto es visión.
4. **Validación** — firma presente y humana, campos obligatorios legibles,
   coherencia con Sigrid (la incidencia existe y está abierta).
5. **Nombrado** — `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`: código de obra, código de incidencia y sufijo.
6. **Archivo** — subida a SharePoint.
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
4. **Lo manuscrito es dato de primera, no decoración.** DNI y observaciones
   se escriben a mano y hay que extraerlos. Descartarlos porque "no es texto
   impreso" es un bug, no una simplificación.
5. **El número de incidencia lo emite Sigrid.** Sin él no se puede nombrar ni
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
| SharePoint (Graph) | Archivo de los PDF validados. **Mientras estemos en dev**, biblioteca propia en el sitio de **IT** (donde vive la de albaranes), ruta `Postventa/<código de obra>/`. | Al pasar a producción el archivo se muda a la biblioteca de Posventa, respetando la estructura que ya usan (`Postventa - Documentos / <cod> <OBRA> / PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`): es la feature F-013, no un detalle de despliegue. |
| PostgreSQL `psql-albaranes-rs9k2` | Estado de remesas, partes, validaciones y preferencias de usuario. **Schema propio** del proyecto. | Servidor **compartido** con albaranes y compañía: nunca se tocan parámetros de servidor, autenticación ni almacenamiento. |
| Gemini (`gemini-2.5-flash`) | Extracción multimodal y clasificación de firma. | Detrás de `ExtractorPort`: el proveedor se cambia por configuración, no editando el pipeline. |
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

**Riesgo a confirmar en F-008**: que cerrar desde la UI de Sigrid no dispare
nada más que el cambio de estado (una fecha, `solrcp`). Sigrid no tiene
triggers: lo que no escribamos, no se escribe solo.

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
