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
   destino no se sube nada y ni siquiera se crea la carpeta.

   **Precisado por F-026 el 2026-09-12**: eso sigue siendo cierto **salvo
   aprobación humana registrada**. Un parte que el paso 4 mandó a
   `revision_manual` o a `cola_validacion_humana` se archiva si —y solo si— una
   persona lo aprobó y esa aprobación consta **viva** en
   `postventa.aprobaciones`. Es una puerta **más estrecha** que la que abría el
   veredicto automático, no más ancha: exige una persona identificada, un parte
   concreto, un motivo aprobable —no todo motivo lo es: un código de obra o un
   número de incidencia ilegibles **no se aprueban**, se teclean— y un registro
   con quién y cuándo. **Nunca es automática**, y se revoca sola en cuanto
   cambia el veredicto sobre el que se decidió. El detalle está en
   `specs/F-026-aprobacion-humana/`.

   **Precisado por F-028 el 2026-09-16**: dicho con el vocabulario del estado,
   solo se archiva lo que está `aprobado` —uno de los cuatro estados:
   `pendiente`, `aprobado`, `rechazado`, `cerrado`—. La novedad de F-028 no es
   un permiso más, es el contrario: una persona puede dejar `rechazado` un
   parte que la máquina dio por bueno, y ese parte **no se archiva** por mucho
   que su veredicto sea apto. La decisión vive en
   `postventa.historico_estado`, **append-only**, donde manda la última fila
   humana; `postventa.aprobaciones` se **congela** —no se borra: se siembra en
   el histórico, para que las decisiones que ya había sigan contando— y deja de
   leerse y de escribirse. Lo que no cambia: la puerta se comprueba en los tres
   pasos del backend, leyendo el estado **del repositorio y nunca del cuerpo de
   la petición**. El detalle está en `specs/F-028-estado-del-parte/`.

   Y **solo se archiva lo que ya consta guardado** (F-019). El mecanismo no es
   una comprobación en Python: antes de tocar SharePoint se escribe la traza
   del archivo en estado `pendiente`, y `postventa.archivos.hash_parte` tiene
   una **clave ajena** contra `postventa.partes`, así que esa escritura solo
   puede hacerse si el parte ya está guardado. Si no lo está, la restricción
   la rechaza, el archivado se aborta **sin llamar a nadie** y el endpoint
   responde **409** diciendo que hay que guardar el parte primero
   (`POST /api/parte`, y `POST /api/remesa` antes si tampoco consta).

   Se usa **la restricción** y no una consulta previa a propósito: entre una
   consulta y la escritura cabe otro proceso, y una comprobación paralela
   puede divergir de la restricción real. Es además la misma restricción que
   el 2026-08-25 hacía fallar el proceso **después** de subir el fichero
   —dejando un PDF en la biblioteca de Posventa del que el sistema no sabía
   nada—, puesta a fallar antes.

   Reprocesar una remesa no puede duplicar, y para eso hay **tres capas**:
   - **traza** — si ya consta archivado ese `hash` de parte, no se llama a
     nadie: ni token, ni red, ni bytes. Esta capa va **antes** que la escritura
     previa en `pendiente`: al revés, un parte ya archivado quedaría degradado
     a `pendiente`, y `pendiente` no corta el reintento, así que el intento
     siguiente volvería a subir el fichero;
   - **reemplazo** — la subida pide **siempre** reemplazar el homónimo, nunca
     renombrar. Renombrar produce el `... (1).pdf` que el criterio de
     aceptación prohíbe, y es el comportamiento por defecto de más de un
     cliente de Graph;
   - **carpeta** — crearla dos veces es un éxito, no un error.

   **Precisado por F-033 el 2026-09-18**: la capa **traza** lee la traza del
   almacén, dentro de la **misma consulta** con la que la puerta de estado lee
   la situación del parte (un `LEFT JOIN` más a `postventa.archivos`, sin
   ninguna sentencia añadida). Hasta F-033 el paso la recibía por parámetro y
   el endpoint nunca se la pasaba, así que en el circuito real esta capa no
   cortaba. Además:
   - **`archivado` no se pisa**: la escritura de la traza no actualiza una fila
     que ya consta `archivado`, y si otra petición la dejó así entre la lectura
     y la escritura, se relee una vez y se responde como si la capa hubiera
     cortado desde el principio;
   - **una traza `archivado` que apunta a otro destino** —otra carpeta, otro
     nombre de fichero u otra biblioteca— **corta igual** y lo avisa: el fichero
     se queda donde está y no se sube otro;
   - **el re-archivo del mismo parte no existe desde el circuito**: ni campo del
     cuerpo ni parámetro para forzarlo. Si algún día hace falta, será una ficha
     propia. El detalle está en `specs/F-033-l1-traza-archivo/`.

   **Precisado por F-031 el 2026-09-22**: **la carpeta y el nombre del fichero
   salen del `codigo_obra` y el `numero_incidencia` que constan guardados** en
   `postventa.partes`, no de los que trae el cuerpo de la petición. Salen, en
   concreto, de la **misma** situación que la puerta de estado acaba de leer
   (`ctx.situacion.validacion`), así que el fichero se nombra byte por byte con
   los dos valores que la puerta acaba de dar por buenos. Hasta F-031 la puerta
   aprobaba **unos** valores y el fichero se nombraba con **otros** —los del
   cuerpo—, y coincidían solo porque el front manda lo que leyó: una costumbre,
   no una garantía. Además:
   - **lo que venga en el cuerpo ya solo puede cerrar la puerta, nunca
     abrirla**: los dos campos siguen siendo obligatorios (contrato HTTP
     intacto) pero pasan a **cotejarse** contra lo guardado. Si no cuadran, el
     endpoint responde **409** diciendo **cuál** de los dos y con qué valores,
     y **no se archiva nada**;
   - **el cotejo va antes de dejar cualquier rastro**: después de la puerta y
     antes del nombrado, de la traza previa en `pendiente` y de cualquier
     llamada a SharePoint. Con L1 cortando por `hash` + estado y sin forma de
     forzar el re-archivo, un PDF puesto en la carpeta equivocada no se
     arregla desde el circuito;
   - **el cotejo normaliza los dos lados** con el mismo criterio que F-032, así
     que `RS 26.09/0178` y `RS26.09/0178` son el mismo número y no un 409;
   - **el front fuerza el guardado de lo escrito y lo espera** antes de calcular
     la tanda: quien corrige un código y pulsa «archivar y cerrar» dentro del
     rebote de 1,5 s del autoguardado no manda un código que no esté en la
     base. Las dos mitades van juntas. El detalle está en
     `specs/F-031-nombrado-persistido/`.
7a. **Gráfico** (F-012) — el PDF del parte se adjunta a la reclamación como
   **gráfico** de Sigrid, a través del endpoint de dominio de la pasarela
   (`POST /api/sigrid/concepto-grafico`): tres filas en dos bases —el binario
   en la documental, sus metadatos en la de negocio y el enlace—, escritas en
   **una transacción** por la pasarela.

   Va **delante del cierre**, y ese orden es la mitad de la feature: la
   atomicidad entre dos llamadas HTTP no existe, así que se sustituye por
   **orden más idempotencia**. Lo que garantiza es que **ninguna reclamación
   cerrada por este servicio queda sin su parte dentro del ERP**.

   - **las mismas precondiciones que el cierre**, más dos propias: el PDF no
     puede pasar del tope (`GRAFICO_MAX_BYTES`) ni dejar de empezar por
     `%PDF-`, y las dos se comprueban **antes** de llamar a la pasarela;
   - **solo se adjunta lo que se va a poder cerrar**: una reclamación ya
     cerrada o en un estado que no admite cierre **no recibe gráfico**. El
     gráfico es la primera mitad del cierre y no se deja en el ERP sin la
     segunda que lo justifica;
   - **tres capas de idempotencia**: la traza local por `hash` de parte —que
     responde sin llamar a nadie—, la de la pasarela por tamaño y `sha256`, y
     `evaluar`. La consecuencia práctica es que **el reintento es seguro**, al
     revés que en el cierre, y el mensaje de error lo dice;
   - **`ok && (committed || idempotente)`** es la única forma de dar un
     gráfico por colgado: en la respuesta idempotente `committed` vale `false`
     **en un éxito**, y decidir por él daría por fallido cada reintento.

   **Precisado por F-034 el 2026-09-23**: **«consta archivado» se lee de la
   traza guardada** en `postventa.archivos`, y **la reclamación a la que se
   adjunta —y el nombre del gráfico— salen del `codigo_obra` y el
   `numero_incidencia` guardados** en `postventa.partes`. Todo viene de la
   **misma** situación que la puerta de estado acaba de leer
   (`ctx.situacion`), sin una sola sentencia más. Hasta F-034 el endpoint
   fabricaba la traza de archivo con el `estado_archivo` del cuerpo —que el
   front manda fijo— y buscaba la reclamación con los códigos del cuerpo. Además:
   - **lo que venga en el cuerpo ya solo puede cerrar la puerta, nunca
     abrirla ni moverla**: los tres campos siguen siendo obligatorios y
     validados (contrato HTTP intacto), `estado_archivo` ya no decide nada y
     los dos códigos **se cotejan** contra lo guardado con el criterio
     normalizado de F-031/F-032. Si no cuadran, **409** diciendo cuál, y no se
     adjunta nada;
   - **si falta un código guardado** (vacío, o un número sin ningún tramo),
     **409** `CodigoNoConsta` diciendo cuál: se teclea en el parte y se guarda.
     Nunca se rellena con el del cuerpo;
   - **el cotejo va antes de hablar con nadie**: tras la puerta de aptitud y
     antes de la de archivo, del fichero, de la traza local y del login.
     También en dry-run: un dry-run que enseñara la reclamación de un cuerpo
     que miente enseñaría otra cosa;
   - la puerta de archivo vive **en un solo sitio**,
     `puerta_de_estado.exigir_parte_archivado`, compartida con el cierre. El
     detalle está en `specs/F-034-archivo-persistido-en-erp/`.
7b. **Cierre** (F-009) — dry-run contra `sigrid-api`, confirmación del usuario,
   y solo entonces `commit: true`. Es, con el paso 7a, una de las **dos
   escrituras de este proyecto en un ERP de producción**, y por eso es el paso
   con más puertas.

   **Desde F-025 (2026-09-11) la confirmación explícita es una sola** y cubre
   los tres pasos —archivar en SharePoint (paso 6), adjuntar el gráfico (7a) y
   cerrar (7b)—: el usuario confirma una vez, sobre la tanda de partes aptos, y
   el circuito los ejecuta seguidos, parte a parte y en ese orden. Lo que
   desapareció es la **pantalla intermedia** que enseñaba los dos dry-run antes
   de confirmar, no el dry-run: **el cálculo previo se sigue ejecutando, en la
   misma llamada que escribe** y antes de cualquier `commit`, dentro de
   `paso_grafico.py` y `paso_cierre.py`. Un `commit` que llega sin ninguna
   llamada anterior hace su comprobación previa él mismo; eso es lo que sostiene
   que R8 y R10 de F-009 y R20 de F-012 sigan cumpliéndose, y lo vigila
   `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`. El precio
   aceptado de la decisión está escrito en
   `specs/F-025-confirmacion-unica/requirements.md` §0.

   Las puertas del paso:
   - **precondiciones propias**: el parte tiene que ser apto (F-004),
     **constar archivado** (F-006) y, desde F-012, **constar adjuntado** —su
     gráfico dentro de Sigrid—. Esa última se lee de **nuestra traza**
     (`postventa.graficos`) y **nunca** consultando `rcg` ni `gra` del ERP: el
     dominio del cierre sigue sin saber qué es un gráfico;
   - **quién firma**: el login de Sigrid de la persona que confirma, resuelto
     contra `postventa.usuarios_sigrid` o derivado de su correo y
     **verificado contra el ERP** antes de escribir nada. Sin confirmación del
     ERP no se cierra;
   - **qué se escribe**: `con.est` al estado de cierre —resuelto contra
     `conest` por su **código**, nunca por su número— y **una fila en
     `dbo.log`**, las dos en un solo batch transaccional con tope de dos filas
     afectadas. El `UPDATE` lleva en su `WHERE` el estado de origen leído en el
     dry-run: si alguien movió la reclamación entretanto, no se aplica nada;
   - **qué no se reintenta**: nada. Un fallo de escritura lo reintenta una
     persona, después de mirar el ERP.

   **Precisado por F-034 el 2026-09-23**: **la reclamación que se cierra es la
   del `numero_incidencia` guardado** para el parte, y **«consta archivado» se
   lee de la traza guardada**, los dos de la misma situación que la puerta de
   estado acaba de leer y sin una sentencia más. Hasta F-034 se cerraba la
   reclamación que nombrara el cuerpo de la petición, y el archivo lo decía
   también el cuerpo. Además:
   - el número del cuerpo sigue siendo obligatorio (contrato intacto) pero **se
     coteja** contra el guardado —solo el número: el cuerpo de `/api/cerrar` no
     trae obra—; si no cuadra, **409** y **no se cierra nada**, ni en dry-run.
     Si el guardado falta o no tiene ningún tramo, **409** `CodigoNoConsta`;
   - la puerta de archivo es la misma que la del gráfico
     (`exigir_parte_archivado`); la de «consta adjuntado» no cambia;
   - **el front guarda lo escrito y lo espera también al reintentar el
     cierre** («Reintentar el cierre»), igual que ya hacía al lanzar la tanda
     desde F-031: sin eso, corregir un número y reintentar mandaría un número
     que no está en la base y recibiría el 409. Si el guardado falla, no se
     lanza nada y se dice. El detalle está en
     `specs/F-034-archivo-persistido-en-erp/`.

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

   **Precisado por F-026 el 2026-09-12**: de revisión manual ya se sale, pero
   **salvo aprobación humana registrada** no se sale de ninguna otra forma. Una
   firma que el modelo no dio por humana la puede dar por buena **una persona**
   que mira el papel, y entonces el parte entra en el circuito normal; la
   máquina sigue sin poder hacerlo sola. Es una puerta **más estrecha** que la
   que abría el veredicto: una persona identificada, un parte concreto, un
   motivo aprobable y un registro con quién y cuándo en
   `postventa.aprobaciones`. **Nunca es automática.** Lo que no cambia es el
   criterio: una casilla vacía, una aspa o un trazo geométrico **siguen sin
   ser** conformidad del cliente, y lo que decide que valen no es el modelo, es
   quien firma la aprobación.

   **Precisado por F-028 el 2026-09-16**: lo que decide si un parte entra en el
   circuito es su **estado**, y solo entra el que está `aprobado`. Una firma
   que el modelo no dio por humana la sigue pudiendo dar por buena **una
   persona**, exactamente igual que con F-026; lo que se añade es la dirección
   contraria, que antes no existía: una persona puede dejar `rechazado` un
   parte que la máquina dio por bueno, y entonces no se archiva ni se cierra.
   La decisión consta en `postventa.historico_estado` —append-only, con quién
   y cuándo, y manda la última fila humana—, y `postventa.aprobaciones` queda
   congelada y sembrada en él. El criterio de la firma no lo toca nadie: una
   casilla vacía, una aspa o un trazo geométrico **siguen sin ser**
   conformidad del cliente.

   **Precisado por F-030 el 2026-09-16**, el mismo día y a costa de una
   regresión en producción: lo que decide si un parte entra en el circuito es
   el estado derivado **del veredicto que consta guardado** en
   `postventa.validaciones`, y de nada más. **Ningún endpoint del circuito
   emite veredicto**: `POST /api/archivar`, `POST /api/adjuntar` y
   `POST /api/cerrar` no reciben la extracción del parte —pedirla obligaría al
   front a reenviar el DNI y las observaciones manuscritas del cliente en cada
   llamada— así que no pueden emitirlo, y **tampoco lo fabrican**: el veredicto
   lo emite F-004 con la extracción delante, o se lee de la base. Lo que venga
   en el cuerpo de esas tres peticiones se comprueba contra las enumeraciones
   del dominio y no abre ni cierra ninguna puerta.

   Por qué está escrito aquí y no solo en la spec: mientras esos tres endpoints
   armaron un veredicto con lo poco que traía el formulario, la puerta
   recomponía la huella sobre ese objeto de pega, no coincidía nunca con la que
   apuntó quien decidió, y **una aprobación humana dejó de contar**. El parte
   `b7e9b037` de la incidencia RS26.09/0178 estuvo aprobado y sin archivar. Lo
   que no cambia, otra vez, es el criterio de la firma.

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

   **Precisado por F-028 el 2026-09-16**: **los espacios que rodean al
   separador no forman parte del código**. `RS26.09 / 0149`, `RS26.09 /0149`,
   `RS26.09 - 0149`, `RS26.09- 0149` y `RS26.09 – 0149` son **el mismo** número
   que `RS26.09/0149`: al ERP viaja siempre `RS26.09/0149`, y al nombre del
   fichero, `RS26.09 - 0149`. Hasta el 2026-09-15 no era así y el cierre
   fallaba **en silencio**: Sigrid busca la reclamación por **igualdad
   exacta**, así que un número leído con un espacio de más se archivaba bien y
   no cerraba nada. Lo que **no** pasa por esta regla es el **código de obra**:
   `06-77` es una obra, no dos tramos, y partirlo por el guion metería un PDF
   con el DNI manuscrito de un cliente en la carpeta de otra promoción.

   **Precisado por F-032 el 2026-09-17**: **ningún espacio forma parte del
   código**, ni junto al separador ni dentro de un tramo. `RS 26.09/0178` es el
   mismo número que `RS26.09/0178`, y `06 26` la misma obra que `0626`. F-028
   había dejado fuera el espacio que no toca al separador, y el 2026-09-17 eso
   costó un cierre que hubo que rescatar editando el código a mano. Los códigos
   se sanean **al leerlos**, así que lo que se guarda en `postventa.partes` nace
   sin espacios. Lo que sigue sin cambiar: el código de obra **no se parte por
   sus guiones** (`06-77` es una obra), y la normalización de la **huella** del
   veredicto es **otra** y no se toca.

6. **Cerrar en Sigrid es escritura en producción.** Siempre dry-run primero;
   `commit: true` solo después de confirmación explícita (del usuario en el
   front, o de su preferencia de auto-cierre guardada).
   Precisado por **F-025 el 2026-09-11**, y las dos mitades importan por igual:
   - esa confirmación explícita es **una sola confirmación** para todo el
     circuito —archivar, adjuntar el gráfico y cerrar—, no una por escritura.
     Una sola no es **ninguna**: sin ella no se escribe nada, y sigue
     caducando (R12–R15 de F-009);
   - «siempre dry-run primero» sigue entero, y ocurre **en la misma llamada**
     que escribe, no en una pantalla anterior. Que ya no se le enseñe a nadie
     **no autoriza a quitarlo** de `paso_grafico.py` ni de `paso_cierre.py`:
     ahí es donde se comprueba que la reclamación existe, en qué estado está y
     si el documento ya cuelga de ella.
7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**
   Archivar un parte inválido ensucia el archivo de Posventa; cerrarlo en
   Sigrid da por resuelta una incidencia que sigue viva.
   **Precisado por F-026 el 2026-09-12**: sigue entero **salvo aprobación
   humana registrada**, que es lo único que sustituye a una validación en
   verde, y solo porque pone en su lugar algo que la validación no tiene: una
   persona que ha mirado el papel y responde de ello. Es una puerta **más
   estrecha** que la que abría el veredicto —una persona identificada, un parte
   concreto, un motivo aprobable y un registro con quién y cuándo en
   `postventa.aprobaciones`—. **Nunca es automática**, y caduca sola cuando
   cambia el veredicto sobre el que se decidió. La aprobación **no se escribe
   en Sigrid**: consta en nuestra base y en ninguna otra, por decisión expresa
   del responsable del 2026-09-11 (*«no hace falta que conste en Sigrid, sí en
   nuestra base»*). Quien audite un cierre cruza `postventa.aprobaciones` con
   `postventa.cierres` por `hash_parte` y ve si lo cerró el veredicto o lo
   cerró una persona **a pesar** del veredicto; el ERP, por sí solo, no
   distingue esos dos cierres.

   **Precisado por F-028 el 2026-09-16**: con el vocabulario del estado, solo
   se archiva, se adjunta y se cierra lo que está `aprobado`. Y con una
   diferencia que F-026 no podía expresar: un parte **apto** que una persona ha
   dejado `rechazado` **no** pasa, porque lo automático puede retirar un
   permiso y nunca concederlo. La decisión consta en
   `postventa.historico_estado` —append-only, con quién y cuándo— y **sigue sin
   escribirse en Sigrid**, por la misma decisión del responsable del
   2026-09-11; `postventa.aprobaciones` se congela y se siembra en el
   histórico. Quien audite un cierre cruza hoy `postventa.historico_estado` con
   `postventa.cierres` por `hash_parte`, y ve si lo cerró el veredicto o lo
   cerró una persona a pesar de él.

8. **El nombre del fichero es `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`**
   —por ejemplo `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`— y la carpeta va por
   código de obra. El sufijo se conserva porque distingue el parte conformado
   de cualquier otro documento de la misma incidencia.
   Los separadores se normalizan a ` - ` con guion normal: el código que emite
   Sigrid puede traer guion largo (`–`), y un nombre de fichero no es sitio
   para depender de eso.

   **Precisado por F-031 el 2026-09-22**: **los dos códigos que rellenan ese
   nombre —y la carpeta— son los que constan guardados para el parte**, no los
   que declare quien llama. Las cuatro reglas del nombrado, el sufijo y los
   separadores no cambian ni una letra: lo que cambia es **de dónde salen sus
   entradas**. Si el código guardado está vacío o es innombrable, no se archiva
   y se dice cuál falta; un código ilegible **no se aprueba, se teclea y se
   guarda**, que es la regla que F-026 ya tenía escrita.
9. **Reprocesar una remesa no puede duplicar nada.** El mismo parte, subido
   dos veces, es el mismo parte: se identifica por hash del PDF troceado y
   por número de incidencia.

## Acceso a datos y sistemas externos

| Sistema | Uso | Límites |
|---|---|---|
| `sigrid-api` | **Única** vía al SQL Server de Sigrid. Lectura de la reclamación (dry-run), **gráfico por escritura** (F-012, `POST /api/sigrid/concepto-grafico`: tres filas en dos bases, en una transacción de la pasarela) y **cierre por escritura** (F-009, `sql/write`): `con.est` y una fila en `dbo.log`, en un solo batch transaccional. El destino es **configuración**: `CIERRE_HABILITADO`, `SIGRID_API_BASE_URL`, `SIGRID_API_KEY`, `SIGRID_BASE_DATOS`, `SIGRID_TIMEOUT_S`, `SIGRID_REINTENTOS`, `SIGRID_TIP_RECLAMACION`, `SIGRID_ZONA_HORARIA`, `SIGRID_GRATIPIDE_PARTE`, `GRAFICO_MAX_BYTES`. | Máx. 1.000 filas por petición; el balanceador corta a 230 s. **PUERTA DE ENTORNO**: escribir —el gráfico **y** el cierre, con **la misma** variable— solo se permite con `ENTORNO` en `dev` o `pro` **y** `CIERRE_HABILITADO` encendido, que está **apagado por defecto**. Las dos se comprueban en la fábrica **y en el constructor de los dos adaptadores**, así que componer las piezas a mano tampoco deja escribir desde un puesto de trabajo; y la guardia de red de la suite impide que un test abra la conexión. Encima de eso, `POST /api/cerrar` es **dry-run por omisión** y exige confirmación explícita o auto-cierre guardado. La lectura reintenta lo transitorio; **la escritura no se reintenta jamás**: un tiempo agotado no dice que el ERP no haya escrito. La diferencia entre las dos escrituras: el **cierre** no se puede reintentar solo —lo decide una persona tras mirar el ERP—, y el **gráfico** sí, porque su endpoint es idempotente por tamaño y `sha256`, así que su mensaje de error lo dice. Qué escribimos y qué se rompe si alguien cambia la configuración de escritura de la pasarela: **`docs/INTEGRACION.md`** y `azure-apps/postventa_incidencias.md`. |
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

**Cerrar una incidencia a mano son tres escrituras**, y en este orden:
`INSERT` en `gra` con el PDF → `INSERT` en `rcg` vinculándolo a la
reclamación → `UPDATE con.est` al estado de cierre.

**F-009 hace la tercera, y hace además la que no se ve**: la fila de
`dbo.log`, que F-008 midió y que un `UPDATE` a secas se dejaría por el camino.
Las dos van en un solo batch transaccional, así que son las dos o ninguna.

Las otras dos —el gráfico— son **F-012**, y ahí está el obstáculo que conviene
saber el primer día: `sigrid-api` sabe **leer** documentos (`POST
/api/documents/read`) pero **no sabe escribirlos**, `sql/write` no reserva
`ide` con applock ni está pensado para BLOBs, y —lo que de verdad bloquea— el
binario vive en la **base documental**, que la pasarela tiene **fuera de su
lista blanca de escritura a propósito**. F-012 no necesita solo un endpoint
nuevo: necesita una decisión del **dueño de `sigrid-api`** que afecta a todo el
ecosistema. Se propone al humano, no se implementa aquí (regla de LÍMITE DE
SERVICIO).

**F-009, en cambio, NO exige tocar el repositorio `sigrid-api`**: sus dos
sentencias caben en `POST /api/sql/write` tal y como está desplegado, con
`UPDATE` e `INSERT` permitidos y la base de negocio en la lista blanca.

### Alcance del cierre: validar → cerrar → subir el PDF

**Decidido por el humano el 2026-08-26, con lo que F-008 midió delante.** Ya
no está en el aire: el orden es **validar → cerrar → subir el PDF**, y el
último paso es F-012.

Posventa hace hoy dos cosas: sube el PDF a Sigrid como gráfico **y** cambia el
estado. Este servicio hace **lo segundo**, y hace lo primero a su manera: el
parte se archiva en SharePoint con su traza. En Sigrid se mueve `con.est` al
estado de cierre y se escribe la fila de `dbo.log` que el ERP escribiría — las
dos cosas, porque F-008 comprobó que el proceso «Cerrar parte» **no toca nada
más** (ni `con.tiemod`, ni `rcp.solrcp`, ni ninguna fecha).

**La precondición del cierre es propia**: parte apto y archivado. **No se
consulta el gráfico**, y esa es la decisión, no un olvido. El dato que la
justifica: el **98,7 % de las reclamaciones abiertas no tiene gráfico**, porque
subirlo y cerrar son el mismo gesto en el flujo manual. Exigirlo habría dejado
esta feature sin poder cerrar prácticamente nada.

#### RIESGO ACEPTADO · CERRADO el 2026-09-06 por F-012

**Este riesgo ya no está vigente, y no llegó a producirse ni una sola vez.**
F-012 adjunta el parte a la reclamación **antes** del cambio de estado, y el
cierre exige que conste adjuntado para poder ejecutarse: `POST /api/cerrar` con
`commit` y sin gráfico responde **409 sin tocar el ERP**. El texto que sigue se
conserva **en pasado** porque explica por qué el orden es el que es, y porque
la decisión que lo cerró —adjuntar antes que cerrar, sin atomicidad, con orden
más idempotencia— solo se entiende leyendo lo que evitaba.

Lo que se aceptaba, sin adornos y por escrito: **este servicio iba a producir
reclamaciones en estado `CER` sin ninguna fila en `rcg`, algo que no ha
ocurrido ni una sola vez en los 2.365 cierres con «Cerrar parte» desde 2023.**
Aquellos cierres habrían sido, mirando los datos del ERP, anómalos respecto a
todo el histórico reciente. Quien mirara la base lo habría visto.

Lo que lo hace asumible son tres cosas, y las tres tienen que sostenerse:

1. **El parte firmado existe.** Está archivado, con su traza en
   `postventa.archivos` y su clave ajena contra `postventa.partes`. No se
   cierra nada cuya prueba no esté guardada. Lo que falta no es el documento:
   es el documento **dentro de Sigrid**.
2. **El conjunto es localizable y reversible.** La fila de `dbo.log` lleva un
   `tex` propio —`Cerrar parte (postventa-incidencias)`— que identifica
   exactamente nuestros cierres con un solo `LIKE`, y que **sigue empezando por
   `Cerrar parte`** para no desaparecer de los informes de Posventa. Y los
   cierres se deshacen en el ERP: hay 81 precedentes.
3. **Quien confirma lo sabe.** El dry-run advierte explícitamente de que la
   reclamación quedará cerrada sin el parte dentro de Sigrid, y ese aviso se
   pinta **siempre**, antes de que nadie confirme.

**Tenía fecha de caducidad, y se cumplió**: la anomalía desaparecía cuando
**F-012** subiera el PDF, y F-012 se implementó **antes** de ejecutar el primer
cierre real (decisión del humano del 2026-09-06, orden (b) del `design.md` §13
de aquella feature). Así que el circuito reproduce lo que hace Posventa desde
el primer cierre, y esta sección se queda como registro de la decisión.

> Lo que le esperaba a F-012, escrito antes de saber cómo acabaría: el binario
> del gráfico vive en la **base documental** del ERP, y la configuración
> desplegada de `sigrid-api` tenía la base de negocio como **única** escribible.
> Subir el PDF a Sigrid no tenía por dónde hacerse: hacía falta una decisión del
> dueño de `sigrid-api`, que afecta a todo el ecosistema.
>
> **La tomó él, y está desplegada**: su F-004 expone
> `POST /api/sigrid/concepto-grafico`, el único camino por el que se escribe en
> la documental, mergeado en `dev` el 2026-09-06. F-012 lo consume como
> `remesas` o `partes` consumen `sql/read`, y no cruza ninguna frontera. Lo que
> sigue siendo ajeno son sus App Settings `SIGRID_DOCUMENT_*`, declaradas como
> **precondición** en `docs/INTEGRACION.md` §6.

### Lo que F-008 confirmó contra el ERP real (solo lecturas)

Las cuatro preguntas abiertas están **resueltas y medidas**, y el detalle vive
en `docs/referencia/03_modelo_posventa_sigrid.md`. No se duplica aquí; el
resumen es:

- **El tipo de concepto de la reclamación y sus estados**, con el de cierre
  identificado por su **código** `CER`. El número es configuración de la
  instalación y se resuelve en ejecución.
- **`con.cod` es entero el código de la reclamación** y es único dentro del
  tipo: 23.063 códigos distintos en 23.063 conceptos. En Sigrid va con barra;
  en el nombre del fichero, con guion.
- **Qué escribe «Cerrar parte»**: `con.est` y una fila en `dbo.log`. Nada más.
  Ni `con.tiemod`, que es lo más contraintuitivo de todo el hallazgo.
- **Hay dos tablas de gráficos, en dos bases distintas**, y el binario está en
  la documental. Es lo que condiciona a F-012.

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

```
IA_TIMEOUT_S / GRAPH_TIMEOUT_S = 35 s  →  TIMEOUT_PETICION_MS = 40 s  →  proxy = 45 s
```

**Cada capa cede antes que la de fuera**, y ese es el criterio, no los números.
Así quien aborta es el front —que sabe reintentar y liberar la plaza de la
cola— y no el proxy, que devuelve un error opaco que nadie ha generado y deja
la llamada a la IA viva por detrás gastando cuota.

El peor caso medido del circuito (F-010, T2, con una remesa real de 22 partes)
es **6,5 s** en `/api/extraer` con seis peticiones vivas. Los 35 s son colchón
para lo que no se puede medir en local: el salto de región, el arranque en frío
y un mal día del proveedor de IA.

El `functionTimeout` de cinco minutos de `host.json` **no es** el límite que
aprieta: es el techo de la Function, no el del proxy.

### Los endpoints están en `ANONYMOUS`, y es deliberado

Con un backend enlazado, la Static Web App autentica al usuario y reenvía la
cabecera `x-ms-client-principal`; **no** una clave ni un token que la Function
pueda exigir. `auth_level=FUNCTION` rompería el front. El control de acceso
está en capas y ninguna vive en el `auth_level`: grupo de Entra con asignación
obligatoria, **ventana de escritura** de `/api/archivar` (`ARCHIVO_HABILITADO`,
apagado por defecto en el código; hasta el 2026-09-22 se desplegaba apagado y
desde el 2026-09-23 el despliegue lo publica encendido salvo con
`-VentanasCerradas`, por decisión del humano), tope de gasto en el proveedor de IA y, si resulta
compatible, restricción de acceso público. Está explicado en la cabecera de
`services/postventa-api/function_app.py` y en `docs/DESPLIEGUE.md` §4.

El runbook completo del despliegue está en **`docs/DESPLIEGUE.md`**.
