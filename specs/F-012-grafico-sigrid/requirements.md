<!-- specs/F-012-grafico-sigrid/requirements.md -->
# F-012 · Subir el parte a Sigrid como gráfico de la incidencia — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f012_rN_*`. Rigor `critico`.
>
> Esta feature es la **segunda escritura de este proyecto en el ERP de
> producción**, y la primera que toca **dos bases** —la de negocio y la
> documental— y que **transporta el PDF del parte** (con el DNI manuscrito del
> cliente dentro) hasta Sigrid. Los requisitos que parecen redundantes con los
> de F-009 —dry-run obligatorio, doble puerta, login verificado, tope de filas—
> no lo son: son los mismos candados aplicados a una escritura distinta.

## Alcance

F-012 adjunta el PDF del parte firmado a la reclamación **como gráfico**, a
través de `POST /api/sigrid/concepto-grafico` de `sigrid-api` (su F-004,
mergeada en `dev` el 2026-09-06; contrato en `azure-apps/sigrid_api.md` §8.8),
**antes** del cambio de estado que hace F-009. Con esto desaparece el **riesgo
aceptado** de `specs/F-009-cierre-sigrid/design.md` §2: ninguna reclamación
cerrada por este servicio queda sin su parte dentro de Sigrid.

**Fuera de alcance, por decisión del humano del 2026-09-06**: borrar o
sustituir adjuntos, versionar (`graant`), reparar gráficos huérfanos, el
gráfico por URL (**F-023**, que sigue `blocked` y cuyo destino decide el
humano) y cualquier cosa del catálogo del portal.

## Vocabulario

| Término | Qué es |
|---|---|
| **Gráfico** | Un documento adjunto a un concepto de Sigrid: metadatos en `ruesma.gra`, binario en `ruesma_rep.gra` (mismo `cod` y `emp`) y enlace en `ruesma.rcg`. **Tres filas, dos bases.** |
| **La pasarela** | `sigrid-api`, único acceso al SQL Server de Sigrid. Su endpoint de dominio hace las tres filas en una transacción. |
| **Dry-run** | Llamada al endpoint con `commit: false` (su valor por omisión): solo lecturas, y devuelve las filas que escribiría. |
| **Idempotente** | Respuesta `200` con `idempotente: true`: ese mismo documento (mismo tamaño y mismo `sha256`) ya cuelga de ese concepto y **no se ha escrito nada**. Es un éxito, no un error. |
| **`hash` del parte** | La **huella de páginas** de F-002 (texto + imágenes), estable entre reserializaciones. **No es el `sha256` del PDF**: son dos identificadores distintos y esta spec no los confunde. |
| **`sha256`** | El hash de **los bytes exactos** del PDF que se envían. Es lo que la pasarela comprueba y lo que decide su idempotencia. |
| **Clase de gráfico** | `gra.gratipide` → `dbo.auxgra`. La de Posventa es `35` (`PV002`, «POSTVENTA:Fotos Reparaciones»). |
| **Login de Sigrid** | `dbo.usu.cod`, el que F-009 ya resuelve y verifica por usuario (R28–R34 de F-009). Va en `gra.usu` y dentro de `gra.cod`. |
| **Obra de prueba** | La obra **404** de Sigrid. Toda verificación contra el ERP se hace sobre sus reclamaciones, nunca sobre Mirasierra ni sobre obras reales. |

---

## 1 · El orden: el gráfico va antes del cierre

**R1.** El sistema debe adjuntar el gráfico a la reclamación **antes** de mover
su estado al de cierre: la escritura de F-009 no debe poder ejecutarse sobre un
parte que no conste adjuntado.

**R2.** CUANDO se pide el cierre de F-009 con `commit`, el sistema debe
comprobar en su **traza local** (`postventa.graficos`) que el parte consta en
estado `adjuntado`, y SI no consta, ENTONCES debe abortar el cierre **sin tocar
el ERP** y decir que primero hay que adjuntar el gráfico.

> R2 es la precondición nueva del cierre, simétrica a R17 de F-009 («consta
> archivado»). Se comprueba contra **nuestra** traza, no contra `rcg`: R20 de
> F-009 sigue vigente y el cierre sigue sin consultar las tablas de gráficos
> del ERP.

**R3.** SI el gráfico se adjunta y el cierre posterior falla, ENTONCES la
reclamación debe quedar **abierta con su gráfico**, y un reintento del mismo
parte debe cerrarla **sin volver a adjuntar** nada.

**R4.** SI el gráfico no se puede adjuntar, ENTONCES el sistema **no debe**
ejecutar el cierre de esa incidencia, ni siquiera con confirmación o
auto-cierre.

**R5.** El sistema **no debe** dar por atómicas las dos escrituras: la
atomicidad entre dos llamadas HTTP no existe y se sustituye por **orden** (R1)
más **idempotencia** (sección 5). Ningún código debe suponer que «si se adjuntó,
se cerró».

## 2 · Qué se adjunta y con qué datos

**R6.** El sistema debe enviar a la pasarela **los bytes del PDF del parte
troceado**, los mismos que se archivaron en SharePoint, sin recomprimir ni
recomponer.

**R7.** El sistema debe calcular el `sha256` de esos bytes y enviarlo en la
petición, para que la pasarela lo coteje con el que calcule ella.

**R8.** El sistema debe enviar `conide` y `contip` **tomados de la propia
reclamación leída** en el dry-run de F-009 (`Reclamacion.ide`,
`Reclamacion.tip`), y no de una constante ni de la configuración.

**R9.** El sistema debe enviar como `nom` **el mismo nombre de fichero** con el
que F-006 archiva el parte (`<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`),
compuesto por `domain/models/nombrado.py`, y ese nombre no debe superar 255
caracteres.

**R10.** El sistema debe enviar como `res` la descripción `PARTE FIRMADO`,
que no debe superar 48 caracteres.

**R11.** El sistema debe enviar como `gratipide` la clase de gráfico
**configurada** (`SIGRID_GRATIPIDE_PARTE`, por defecto `35`), nunca un literal
en el código de producción fuera de ese valor por defecto de configuración.

**R12.** El sistema debe enviar como `usu` el **login de Sigrid de la persona
que confirma**, resuelto y verificado con el mecanismo de F-009 (R28–R34), y
ese login no debe superar 24 caracteres.

**R13.** El sistema debe enviar como `database` la base de negocio configurada
(`SIGRID_BASE_DATOS`) y **no debe nombrar nunca la base documental**: la
elige la pasarela.

## 3 · Solo se adjunta lo que se va a poder cerrar

**R14.** El sistema **no debe** adjuntar el gráfico de un parte que no haya
sido declarado apto para archivo y cierre por F-004 (misma puerta que R16 de
F-009).

**R15.** El sistema **no debe** adjuntar el gráfico de un parte que no conste
**archivado** en `postventa.archivos` (misma puerta que R17 de F-009).

**R16.** SI la reclamación ya está en el estado de cierre, ENTONCES el sistema
debe registrar el resultado como `ya_cerrada` **sin adjuntar nada**, y eso no
debe tratarse como un error.

**R17.** SI la reclamación está en un estado que no admite cierre automático
(R19 de F-009), ENTONCES el sistema debe abortar **sin adjuntar nada** y
nombrar el estado en el motivo.

> R16 y R17 reutilizan `evaluar` de `domain/models/cierre.py`: el gráfico es
> la primera mitad del cierre, y no se deja una escritura en el ERP sin la
> segunda mitad que la justifica.

**R18.** SI el PDF supera el tope configurado (`GRAFICO_MAX_BYTES`, por
defecto el mismo que la pasarela, 10 MB), ENTONCES el sistema debe abortar
**sin llamar a la pasarela** y decir cuánto ocupa y cuál es el tope.

**R19.** SI los bytes no empiezan por la firma de PDF (`%PDF-`), ENTONCES el
sistema debe abortar **sin llamar a la pasarela**.

## 4 · El dry-run es obligatorio, y la confirmación también

**R20.** CUANDO se solicita adjuntar, el sistema debe ejecutar **primero** un
dry-run (`commit: false`) contra la pasarela, **en la misma llamada** y antes
de cualquier `commit`, y no debe existir ningún camino que envíe `commit: true`
sin ese dry-run inmediatamente anterior.

**R21.** El dry-run debe devolver al usuario: el código y la descripción de la
reclamación, su estado actual legible, el login con el que se firmaría, el
nombre de fichero y la descripción con que quedará el gráfico, la clase de
gráfico, el tamaño en bytes y el `sha256` del PDF, el `cod` previsto, y los
**avisos** que devuelva la pasarela (entre ellos, los gráficos huérfanos del
concepto).

**R22.** SI el dry-run responde `idempotente: true`, ENTONCES el sistema debe
decirlo al usuario **antes** de confirmar: ese parte ya está dentro de Sigrid y
el commit no escribirá nada.

**R23.** El sistema **no debe** ejecutar el `commit` del gráfico sin la
confirmación explícita del usuario en el front o su preferencia de auto-cierre
activa, con las mismas reglas que R12–R15 de F-009 (una sola confirmación cubre
el gráfico **y** el cierre).

## 5 · Idempotencia en capas, y el reintento

**R24.** CUANDO ya consta en `postventa.graficos` una traza `adjuntado` para
ese `hash` de parte, el sistema debe responder `adjuntado` **sin llamar a la
pasarela**: ni dry-run, ni commit, ni bytes.

**R25.** CUANDO la pasarela responde `ok: true` con `idempotente: true`, el
sistema debe tratarlo como **éxito**, registrar la traza como `adjuntado` con
los identificadores del gráfico existente y `idempotente = true`, y no debe
tratarlo como error ni reintentar.

**R26.** El sistema debe considerar el gráfico **colgado** si y solo si
`ok && (committed || idempotente)`. Decidir por `committed` a solas está
prohibido: en el caso idempotente vale `false` en un éxito.

**R27.** CUANDO la pasarela responde `committed: true`, el sistema debe exigir
`filas_afectadas == 3`; cualquier otro valor con `committed: true` es un error
con su motivo, nunca un gráfico dado por adjuntado.

**R28.** SI el `commit` falla por corte de red, tiempo agotado o error de la
pasarela, ENTONCES el sistema debe registrar la traza como `error` con su
motivo y **no debe reintentar el commit por su cuenta** en esa llamada.

**R29.** El motivo del error de R28 debe decir que **el reintento es seguro**:
el endpoint es idempotente por tamaño y `sha256`, así que volver a pedirlo no
duplica el gráfico. (Es la diferencia con F-009, donde el reintento lo decide
una persona después de mirar el ERP.)

**R30.** El estado `adjuntado` de la traza es **terminal**: un intento
posterior de registrar un gráfico para el mismo parte no debe pisarlo.

## 6 · Tratamiento de cada respuesta de la pasarela

**R31.** SI la pasarela responde `400` con `details.codigo` en
`colision_de_clave`, `sha256_no_coincide` o `filas_afectadas_inesperadas`,
ENTONCES el sistema debe registrar `error` diciendo que **el ERP quedó sin
cambios** y que se puede reintentar, y responder **502**.

**R32.** SI la pasarela responde `400` con `details.codigo` en
`escritura_documental_deshabilitada` o `base_de_datos_no_permitida`, ENTONCES
el sistema debe responder **503** nombrando la **precondición del dueño de
`sigrid-api`** que no se cumple, sin haber escrito nada.

**R33.** SI la pasarela responde `400` con `details.codigo` en
`concepto_no_encontrado`, `tipo_de_concepto_no_coincide`,
`clase_de_grafico_no_permitida`, `usuario_no_valido`, `fichero_vacio`,
`tipo_de_fichero_no_permitido` o `tamano_excedido`, ENTONCES el sistema debe
responder **409** con el código y el motivo, sin haber escrito nada.

**R34.** SI la pasarela responde `500`, un código no previsto, un cuerpo que no
es JSON, o no responde, ENTONCES el sistema debe responder **502** con el
motivo acotado y **sin filtrar el cuerpo crudo** ni ninguna credencial.

**R35.** El sistema **no debe** registrar ni devolver el cuerpo crudo de una
respuesta de error de la pasarela: de él solo se toma `details.codigo`, que
es una lista cerrada, y se descarta el resto.

**R36.** El sistema **no debe** escribir ninguna fila en `dbo.log` por el
gráfico: ni la pasarela ni el propio ERP lo hacen al importar un gráfico.

**R37.** El sistema debe respetar el tiempo de espera configurado
(`SIGRID_TIMEOUT_S`) también en la llamada del gráfico, de modo que la
Function ceda **antes** que el proxy de la Static Web App.

## 7 · Puertas de entorno

**R38.** El sistema **no debe** poder adjuntar gráficos desde el entorno
local: la escritura debe estar permitida únicamente en los entornos
desplegados (misma lista que F-009).

**R39.** El sistema debe exigir el **mismo interruptor** que el cierre,
`CIERRE_HABILITADO`, comprobado **en la fábrica y en el propio adaptador** del
gráfico, de modo que componer las piezas a mano tampoco permita escribir.

**R40.** SI falta configuración para hablar con la pasarela, ENTONCES el
sistema debe nombrar **todas** las variables que faltan de una vez y **jamás**
sus valores.

**R41.** Ningún test de la suite debe abrir una conexión de red hacia la
pasarela, y ninguna prueba debe poder enviar un PDF ni un `commit` contra
Sigrid.

## 8 · La traza local

**R42.** CUANDO termina un dry-run correcto, el sistema debe registrar la traza
en `postventa.graficos` con estado `dry_run_ok`, el `sha256`, los bytes, el
nombre de fichero y la clase.

**R43.** CUANDO el gráfico queda colgado (R26), el sistema debe registrar la
traza con estado `adjuntado`, el `cod` del gráfico, los `ide` de negocio, de la
documental y del enlace que devuelva la pasarela, la marca de tiempo, si fue
idempotente, y el `oid` de quien confirmó.

**R44.** La traza debe guardar el **`oid` opaco de Entra** de quien confirma y
**nunca** su correo, su nombre ni su login de Sigrid (misma regla que R43 de
F-009).

**R45.** La traza **no debe** contener los bytes del PDF ni ningún campo
manuscrito del parte: guarda identificadores y el `sha256`.

**R46.** `postventa.graficos.hash_parte` debe tener clave ajena contra
`postventa.partes`, de modo que no se pueda dejar traza —ni siquiera de
dry-run— de un parte que no conste guardado.

**R47.** SI el gráfico se adjuntó en el ERP y la traza local no se pudo
escribir, ENTONCES el sistema debe distinguirlo con un error propio
(`GraficoSinTraza`, → 500) que diga que **el ERP sí está escrito** y que el
reintento responderá idempotente.

## 9 · Lo que cambia en el cierre de F-009

**R48.** El plan de cierre (`PlanDeCierre`) y la respuesta del dry-run de
`POST /api/cerrar` **dejan de llevar** el aviso de que la reclamación quedará
sin gráfico (R21 de F-009, `AVISO_SIN_GRAFICO`): con F-012 ese aviso sería
falso.

> R21 de F-009 queda **derogado** por la decisión del humano del 2026-09-06.
> Los tests de F-009 que lo comprueban se sustituyen por los de esta sección,
> y `design.md` §13 lista cuáles.

**R49.** CUANDO se presenta el dry-run del cierre, el sistema debe informar del
**estado del gráfico** según la traza local: `adjuntado` (con nombre de
fichero y `sha256`), `dry_run_ok`, o que no consta.

**R50.** El dry-run del cierre (`commit: false`) **no debe** exigir que el
gráfico conste adjuntado: la exigencia de R2 aplica al `commit`. Así los dos
dry-run —gráfico y cierre— se pueden enseñar juntos antes de confirmar.

**R51.** CUANDO el cierre se ejecuta con `commit` y el gráfico consta
`adjuntado`, el cierre debe proceder exactamente como en F-009 (R22–R27 de
F-009), sin cambios en el batch ni en la fila de `dbo.log`.

**R52.** El sistema **no debe** consultar `rcg` ni `gra` del ERP para decidir
el cierre (R20 de F-009 sigue vigente): la precondición nueva se lee de la
traza propia.

## 10 · Datos personales, logs y secretos

**R53.** El sistema **no debe** escribir en sus logs el contenido del PDF, ni
su base64, ni el DNI, ni las observaciones manuscritas, ni ningún dato del
propietario. Del fichero solo se registran el `hash` del parte, el tamaño y el
`sha256`.

**R54.** El sistema **no debe** escribir en sus logs el correo, el nombre, el
`oid` ni el login de Sigrid de quien confirma.

**R55.** El sistema **no debe** escribir ningún secreto —la clave de función,
la raíz de la pasarela— en logs ni en mensajes de error.

**R56.** La respuesta del endpoint **no debe** contener los bytes del PDF, ni
su base64, ni ningún campo manuscrito, ni la configuración del destino.

## 11 · El borde HTTP

**R57.** El sistema debe exponer `POST /api/adjuntar`, en `multipart/form-data`
como `/api/archivar` (el fichero más los campos), **dry-run por omisión**: sin
`commit` no se escribe nada en el ERP.

**R58.** CUANDO se llama sin el fichero o sin los campos obligatorios, el
sistema debe responder **400** diciendo **qué** falta.

**R59.** CUANDO el gráfico no puede adjuntarse porque el parte no es apto, no
consta archivado, la reclamación no admite cierre, falta el mapeo del usuario,
el PDF supera el tope o no es un PDF, o la pasarela rechaza la petición por un
código de R33, el sistema debe responder **409** con el motivo.

**R60.** CUANDO la escritura está deshabilitada por entorno, por interruptor,
por configuración incompleta o por la precondición de la pasarela (R32), el
sistema debe responder **503** sin haber tocado Sigrid.

**R61.** CUANDO la pasarela falla, no responde o devuelve un código de R31 o
R34, el sistema debe responder **502** con el motivo.

**R62.** CUANDO se llama a `POST /api/cerrar` con `commit` y el gráfico no
consta `adjuntado`, el sistema debe responder **409** diciendo que primero hay
que adjuntar (R2), sin haber tocado el ERP.

## 12 · El front

**R63.** CUANDO el usuario pide «ver qué pasaría», el front debe pedir para
cada parte cerrable **los dos dry-run** —gráfico y cierre, en ese orden— y
enseñarlos juntos antes de ofrecer la confirmación.

**R64.** CUANDO el usuario confirma, el front debe, para cada parte, pedir el
`commit` del gráfico y **solo si** responde `adjuntado` pedir el `commit` del
cierre; si el gráfico falla, el cierre de ese parte **no se pide**.

**R65.** El front debe distinguir en pantalla el estado «adjuntado pero no
cerrado» de «cerrado» y de «error al adjuntar», y ofrecer el reintento del
primero sin volver a confirmar el gráfico.

**R66.** La confirmación debe caducar y un segundo clic fuera de ventana no
debe disparar nada (R15 de F-009, reutilizando `js/confirmacion.js`).

**R67.** El front **no debe** reescribir los textos que devuelve el backend
sobre el gráfico (nombre, clase, avisos de la pasarela): los pinta tal cual.

## 13 · Documentación que la feature deja al día

**R68.** `docs/INTEGRACION.md` debe reflejar en el mismo trabajo que este
servicio **consume `POST /api/sigrid/concepto-grafico`**, qué escribe (tres
filas, dos bases), qué precondiciones de configuración de la pasarela exige y
qué se rompe si su dueño las cambia, con los nombres de las variables nuevas y
**nunca** sus valores.

**R69.** `docs/ARCHITECTURE.md` debe dejar de describir el riesgo aceptado de
F-009 como vigente: el paso 7 del pipeline pasa a ser «gráfico y cierre», y el
riesgo queda **cerrado** con fecha y feature.

**R70.** El documento del proyecto en `azure-apps/` debe reflejar el endpoint
nuevo que consumimos y la dependencia de las App Settings
`SIGRID_DOCUMENT_*` de la pasarela.

---

## Trazabilidad de los requisitos que no llevan test unitario

Los siguientes **solo** se pueden verificar contra el ERP de producción —sobre
reclamaciones de la **obra de prueba 404**— y son `MANUAL (humano)`, con su
procedimiento en `tasks.md`:

| Requisito | Por qué no hay test unitario |
|---|---|
| R1, R3 | Que la reclamación quede abierta con su gráfico tras un fallo del cierre, y que el reintento cierre sin duplicar, lo prueba el ERP con las dos escrituras reales. |
| R25, R26 | El caso idempotente real (`committed: false` en un éxito) lo produce la pasarela contra el ERP, no un doble. |
| R27 | Que el commit real afecte a exactamente tres filas y que las tres se puedan releer (`documents/read` + `sha256`). |
| R36 | Que `dbo.log` no gane ninguna fila con el gráfico se comprueba leyendo `MAX(ide)` antes y después. |
| R37 | La duración real del dry-run y del commit con un parte de tamaño real, frente a los 35 s. |

Todo lo demás tiene test unitario **sin red, sin BBDD y sin IA**.
