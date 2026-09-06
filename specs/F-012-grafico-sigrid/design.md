<!-- specs/F-012-grafico-sigrid/design.md -->
# F-012 · Subir el parte a Sigrid como gráfico de la incidencia — Diseño

> Rigor `critico`. Segunda escritura de este proyecto en el ERP de producción,
> y la primera que **transporta el PDF del parte** hasta Sigrid y toca **dos
> bases**. Todo lo que sigue está diseñado sobre lo que `sigrid-api` (F-004)
> midió y verificó contra el ERP real, y sobre el código de ese endpoint tal y
> como está mergeado en `dev` el 2026-09-06. **Lo que dice el código manda
> sobre lo que dice cualquier documento.**
>
> Convención: cada afirmación sobre el ERP o la pasarela va marcada como
> **[MEDIDO]** (con su fuente) o **[INFERIDO]**. Lo que no se sabe va a §14,
> con las opciones y una recomendación, no se inventa.

## 0 · Lo que ya está resuelto y no hay que volver a preguntar

| Pregunta | Respuesta | Dónde |
|---|---|---|
| Qué son «las tres filas» de un gráfico | Binario en `ruesma_rep.dbo.gra` (`gratipide=0`, `res=''`, `vin=3`), metadatos en `ruesma.dbo.gra` (`ima` NULL, `vin=3`, **mismo `cod` y `emp`**), enlace en `ruesma.dbo.rcg` (`pos = MAX(pos)+64`, `cla=0`) | `sigrid-api/application/use_cases/concepto_grafico_statements.py`; `sigrid_api.md` §7.6 **[MEDIDO]** |
| Quién escribe las tres filas y en qué orden | La pasarela, en **una transacción local** (misma instancia, sin MSDTC): documental → negocio → enlace, con relectura de las tres antes del `COMMIT` | `attach_concepto_grafico_use_case.py::_commit` **[MEDIDO en código]** |
| Cómo se reservan los `ide` | Bajo `sp_getapplock` por tabla y `MAX(ide)+1 WITH (UPDLOCK, HOLDLOCK)`, con reintento ante clave duplicada (`DOMAIN_WRITE_MAX_RETRIES`) | íd.; `sigrid_api.md` §7.5 **[MEDIDO en código]** |
| El formato de `gra.cod` | `AAAAMMDDHHMMSS` + 4 dígitos (derivados del `sha256`) + `.` + login, hora de Madrid. **Lo genera la pasarela**, el cliente no manda `cod` | `concepto_grafico_statements.py::construir_cod`; 3.680/3.680 en la clase 35 **[MEDIDO]** |
| Cómo decide la idempotencia | `DATALENGTH(ima)` igual en la documental **y** `sha256` igual, comparado en Python; comprobado en el dry-run y otra vez dentro de la transacción bajo el applock | `_buscar_idempotencia`, L5 **[MEDIDO en código]** |
| Qué pasa al importar un gráfico en `dbo.log` | **Nada**: 0 filas `tab='gra'` en 8,4 M; `auxgra.conlog=0` en todas las clases. La pasarela tampoco escribe ahí | `sigrid-api/progress/explore_F-004_mediciones.md` **[MEDIDO]** |
| Que el endpoint funciona de punta a punta | T20/T21 del 2026-09-06: `committed:true filas_afectadas:3`, `sha256` idéntico al releer con `documents/read`, y la repetición `idempotente:true committed:false filas_afectadas:0`. El humano abrió el adjunto desde la ficha de Sigrid | `sigrid-api/progress/verificacion_F-004_t20_t21.md` **[MEDIDO]** |
| La configuración de la instancia `dev` | `SIGRID_DOMAIN_WRITE_ENABLED=true`, `SIGRID_DOCUMENT_WRITE_ENABLED=true` (desde el 2026-09-06), `SIGRID_DOCUMENT_WRITE_DATABASE=ruesma_rep`, `ALLOWED_CONTIP=[708]`, `ALLOWED_GRATIPIDE=[35]`; `MAX_BYTES`, `ALLOWED_MAGIC` y `WRITE_TIMEOUT_SECONDS` en sus defectos (10 MB, `%PDF-`, 120 s) | `sigrid_api.md` §4.1 **[MEDIDO el 2026-09-06 por el dueño]** |
| Cómo queda un parte firmado cuando lo sube Posventa | `res='PARTE FIRMADO'`, `nom='RS26.08 - 0123 PARTE FIRMADO.pdf'` (= `nomori`), `gratipide=35`, `fec=AAAAMMDD`, `usu=<login>`; binario de 242.534 bytes en la documental | `docs/referencia/03_modelo_posventa_sigrid.md` §4.2 **[MEDIDO]** |
| Qué `res` usa Posventa en la clase 35 | `PARTE FIRMADO` en **3.197 de 3.680**; `''` 413; `PARTE` 27; `FOTO` 26; erratas el resto | `explore_F-004_mediciones.md` §2.3 **[MEDIDO]** |
| La clase 35 | `PV002` «POSTVENTA:Fotos Reparaciones», `tipaso='UPV,RCP,TAR'`, `fecbaj=0`, `tammax=0` | `03_modelo_posventa_sigrid.md` §4.2 **[MEDIDO]** |
| El modelo de datos y el contrato de la pasarela | No se copian aquí | `azure-apps/sigrid_tablas.md`, `azure-apps/sigrid_api.md` §8.8 |

**Los documentos anteriores son la referencia y no se duplican en esta spec.**
Lo que sigue añade solo lo que ninguno decía: cómo lo consume **este**
servicio.

## 1 · Las seis decisiones del humano (2026-09-06), y cómo se traducen

| # | Decisión | Qué hace este diseño con ella |
|---|---|---|
| **H1** | El gráfico se adjunta **antes** del cambio de estado; sin atomicidad entre dos llamadas HTTP, se sustituye por **orden más idempotencia** | Paso nuevo `paso_grafico` delante de `paso_cierre`; `paso_cierre` exige en `commit` que la traza local diga `adjuntado` (R2). Tres capas de idempotencia (§9.3). La comprobación de éxito es `ok && (committed \|\| idempotente)` (R26) |
| **H2** | Dry-run obligatorio y mostrado antes de cada commit; el usuario confirma **una vez** y entonces commit del gráfico y después el cierre. Decidir si el interruptor es el mismo | Dry-run en la misma llamada que el commit (R20), como F-009. **El interruptor es el mismo `CIERRE_HABILITADO`** (§2, D-B) |
| **H3** | `database` la de negocio, `contip` 708, `gratipide` 35 configurable (pregunta a Posventa), `usu` el login de F-009, `res`/`nom` a decidir, `sha256` del PDF | §2 D-E y D-F: `nom` = el nombre de F-006, `res` = `PARTE FIRMADO`, `contip` **de la reclamación leída** y no de la configuración, `gratipide` = `SIGRID_GRATIPIDE_PARTE` |
| **H4** | La configuración de `sigrid-api` en `dev` es del dueño y es **precondición** | No se toca desde aquí. Va como precondición P0 del bloque de verificación de `tasks.md` y como §6 de `docs/INTEGRACION.md` («qué se rompe si el dueño la cambia»). El código responde `503` con el código de la pasarela si falta (R32) |
| **H5** | Toda verificación contra el ERP, sobre la **obra 404**, con dry-run y autorización por incidencia | Bloque 9 de `tasks.md`; consulta de localización preparada en §15 y empaquetada en `infra/15_reclamaciones_obra_prueba.ps1` (solo lectura) |
| **H6** | Fuera: borrar/sustituir, versionar, reparar huérfanos, el gráfico por URL (F-023), el catálogo del portal | Nada de eso se diseña. Los huérfanos que la pasarela avise **se enseñan** en el dry-run (R21) y no se tocan. F-023: §13 |

## 2 · Las decisiones de este diseño

### D-A · Un paso nuevo, no el paso de cierre extendido

**Decidido: `application/pipelines/paso_grafico.py`, paso 7a, delante de
`paso_cierre` (7b).** Y `paso_cierre` cambia lo mínimo: gana **una**
precondición (R2) y pierde el aviso R21 (R48).

Por qué no extender `paso_cierre`:

- Son **dos escrituras contra dos endpoints distintos** de la pasarela, con
  contratos, tiempos y semántica de idempotencia distintos: `sql/write`
  (batch, sin idempotencia, la escritura no se reintenta) frente a
  `sigrid/concepto-grafico` (dominio, idempotente por contenido, el reintento
  es seguro). Meterlos en un paso obligaría a dos políticas de error en la
  misma función.
- `paso_cierre` está cerrado por una spec aprobada, con 123 mutantes
  evaluados y cero supervivientes sin justificar. Cuanto menos se toque, menos
  se reabre.
- Es el patrón del proyecto: cada escritura externa es un paso con su puerto
  (`paso_archivo` → `ArchivoPort`, `paso_cierre` → `ErpPort`).

Y **por qué no un endpoint que haga las dos cosas en una llamada** (adjuntar y
cerrar server-side): un `502` a mitad sería ambiguo —¿falló el gráfico o el
cierre?—, la respuesta tendría que llevar estado parcial, `/api/cerrar`
pasaría de JSON a `multipart` (rompiendo su contrato, sus tests y el guion del
bloque 8 de F-009), y las dos escrituras sumadas comerían el mismo presupuesto
de 45 s. Con dos llamadas cada una tiene su respuesta y su traza, y el front
sabe exactamente en qué estado quedó cada parte (R65).

### D-B · El interruptor es el mismo: `CIERRE_HABILITADO`

**Decidido: una sola ventana de escritura en el ERP.** El adaptador del
gráfico comprueba `CIERRE_HABILITADO` en la fábrica **y** en su constructor,
como el del cierre (R39).

`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` son variables aparte porque
protegen **sistemas distintos, con dueños distintos, que se abren en momentos
distintos** (`docs/DESPLIEGUE.md` §4 bis: «poder archivar no puede implicar
poder cerrar»). El gráfico y el cierre son **el mismo sistema, el mismo dueño,
la misma ventana y la misma decisión del humano**: el gráfico es la primera
mitad del cierre (H1). Un segundo interruptor crearía un estado
—`CIERRE_HABILITADO=true` con el del gráfico apagado— que solo puede
significar dos cosas, y las dos son malas: o se vuelve a cerrar sin gráfico
(la anomalía que esta feature elimina), o todos los cierres responden `409`
por una configuración a medias. Y el estado inverso (gráfico encendido, cierre
apagado) no tiene uso: un gráfico sin cierre es exactamente lo que R16/R17
evitan.

Consecuencia para el bloque de verificación: abrir la ventana para probar el
gráfico en la obra 404 abre también el cierre. Es aceptable por lo mismo que
en F-009: dry-run por omisión, confirmación explícita, el humano delante, y la
ventana se cierra al terminar. Y de hecho la prueba de punta a punta **quiere**
cerrar la reclamación de prueba después de adjuntar.

### D-C · Dónde vive la traza: tabla nueva `postventa.graficos`

**Decidido: `infrastructure/persistencia/sql/09_graficos.sql`, tabla propia,
no columnas en `postventa.cierres`.**

- Es **otra escritura externa con otro ciclo de vida**. «Adjuntado pero no
  cerrado» (R3) es un estado real que hay que poder representar sin mezclarlo
  con el estado del cierre, y `cerrado` es terminal por diseño de F-005: meter
  el gráfico ahí obligaría a reabrir la semántica de `upsert_cierre`.
- Es el patrón: una tabla por escritura externa —`archivos` (F-006),
  `cierres` (F-009)—, cada una con `hash_parte` como clave primaria y clave
  ajena contra `partes`.
- **La traza es la primera capa de idempotencia** (R24): guarda `sha256`,
  bytes, `gra_cod` y los tres `ide`, así que el reintento de un parte ya
  adjuntado no llama a nadie.
- `06_cierres.sql` **no se toca**: F-005 lo dejó construido para F-009 y sigue
  valiendo tal cual.

**Descartado: una clave ajena `cierres.hash_parte → graficos.hash_parte`**
para imponer el orden a nivel de base, como hizo F-019 con `archivos → partes`.
Motivos: exigiría un `ALTER TABLE` sobre una tabla existente (el DDL de este
proyecto es `CREATE ... IF NOT EXISTS` idempotente, y PostgreSQL no tiene
`ADD CONSTRAINT IF NOT EXISTS`); y la restricción no distinguiría estados —una
traza `dry_run_ok` del gráfico bastaría para cerrar—, que es justo lo que hay
que distinguir. La precondición se comprueba en `paso_cierre` leyendo la traza
por el puerto (R2), y no hay carrera que temer: `adjuntado` no se deshace.

### D-D · Dos puertos, dos adaptadores, la misma fontanería

**Decidido: puerto nuevo `GraficoPort` (`domain/ports/grafico.py`) con un solo
método, `adjuntar`, y adaptador nuevo `AdaptadorGraficoSigridApi`
(`infrastructure/sigrid/graficos.py`).** `ErpPort` **no cambia**: su docstring
dice «tres métodos y ni uno más», y su doble en memoria
(`tests/utiles_sigrid.py::ErpEnMemoria`) y sus tests siguen tal cual.

El adaptador nuevo **reutiliza** de `cliente.py` lo que no es del cierre:
`construir_cliente_http`, `ErrorDeSigrid`, `exigir_entorno_con_cierre`,
`exigir_interruptor_de_cierre` y la cabecera `x-functions-key`. No se copia
nada: se importa.

`paso_grafico` recibe **los dos** puertos del ERP —`ErpPort` para leer la
reclamación y verificar el login, `GraficoPort` para adjuntar— más los tres
repositorios que ya recibe `paso_cierre`.

### D-E · `nom` y `res`: el nombre de F-006 y la descripción de Posventa

**`nom` = `nombre_de_archivo(codigo_obra, numero_incidencia)` de
`domain/models/nombrado.py`**, es decir, `0677 - RS26.08 - 0123 PARTE
FIRMADO.pdf`. Es **el mismo nombre con el que el parte está en SharePoint**
(R9): un documento, un nombre, dos sitios; cruzar SharePoint con Sigrid es
comparar dos cadenas iguales. Y es dominio puro y determinista, así que
volver a componerlo meses después da lo mismo. Longitud típica ~45 caracteres
contra un tope de 255 **[MEDIDO: `nom` es `varchar(255)`]**.

Posventa lo escribe a mano sin el código de obra (`RS26.08 - 0123 PARTE
FIRMADO.pdf`) **[MEDIDO §4.2]**; dentro de Sigrid la obra ya se conoce por la
reclamación, así que el prefijo es redundante pero inocuo, y a cambio compra la
trazabilidad con el archivo. Se queda.

**`res` = `PARTE FIRMADO`**, constante `RES_GRAFICO_PARTE` del dominio (R10).
Es lo que Posventa teclea en el 87 % de sus gráficos de esta clase (3.197 de
3.680) **[MEDIDO]**, y `res` es lo que la pantalla de Sigrid enseña como
«Descripción» a quien abre la ficha. Cabe: 13 de 48.

**Descartado: un `res` propio rastreable** al estilo del `tex` de F-009
(«PARTE FIRMADO (postventa-incidencias)», 38 caracteres, cabría). En F-009 el
texto propio iba a una **fila de auditoría** que nadie lee salvo para filtrar;
aquí iría a la **descripción visible** de un documento de trabajo de Posventa,
en cada ficha. La trazabilidad de «qué gráficos son nuestros» la da
`postventa.graficos.gra_cod` (R43), que es exacta y no ensucia la pantalla del
ERP. Si el humano prefiere el texto propio, es cambiar una constante.

### D-F · `conide` y `contip` salen de la reclamación, no de la configuración

`paso_grafico` lee la reclamación con `ErpPort.leer_reclamacion` —la consulta
del dry-run de F-009, localizada por `con.cod` dentro del tipo configurado— y
envía `conide = reclamacion.ide` y `contip = reclamacion.tip` (R8). Es el mismo
principio que R4 de F-009: `SIGRID_TIP_RECLAMACION` sirve para **buscar**, y lo
que se escribe sale de lo que el ERP devolvió. La pasarela coteja `contip` con
`con.tip` y con su lista blanca **[MEDIDO en código: `validar_tipo_de_concepto`]**,
así que una configuración desalineada falla con `tipo_de_concepto_no_coincide`
antes de escribir nada.

`gratipide` es `SIGRID_GRATIPIDE_PARTE` (int, defecto `35`, R11). La evidencia
de que 35 es la clase correcta es fuerte —es la clase bajo la que Posventa
tiene 3.197 gráficos llamados «PARTE FIRMADO» **[MEDIDO]**—, pero el nombre de
la clase («Fotos Reparaciones») no describe un parte firmado, y el humano
pidió preguntarlo. Va a §14 como pregunta abierta con recomendación; mientras
tanto, la lista blanca de la pasarela solo admite 35, así que otra clase sería
una decisión de dos dueños.

### D-G · Solo se adjunta lo que se va a poder cerrar

`paso_grafico` reutiliza **`evaluar` de `domain/models/cierre.py`** sobre la
reclamación leída (R16, R17): si está `ya_cerrada` responde `ya_cerrada` sin
adjuntar; si no es cerrable (`NPR`, o cualquier código fuera de
`CODIGOS_ESTADO_CERRABLE`), aborta sin adjuntar. **El gráfico es la primera
mitad del cierre y no se deja en el ERP sin la segunda.**

Caso real que esto cubre: una reclamación que Posventa ya cerró a mano —con
su gráfico— y cuyo parte vuelve a pasar por el circuito. Colgarle un segundo
gráfico sería modificar un expediente cerrado.

### D-H · Los bytes del PDF los manda el front, como en `/api/archivar`

**Decidido: `POST /api/adjuntar` es `multipart/form-data`** —el fichero más
los campos— y el backend lo pasa a base64 para la pasarela. El front ya
conserva `parte.contenido_b64` y ya compone el `File` para archivar
(`js/pipeline.js::ficheroDeParte`); adjuntar reutiliza exactamente eso (R6).

**Descartado: que el backend descargue el PDF archivado de SharePoint** y lo
suba a Sigrid. Garantizaría byte a byte que lo que hay en Sigrid es lo que hay
en SharePoint, pero exige un método de descarga nuevo en `ArchivoPort`,
encadena dos proveedores externos en la misma petición (Graph + pasarela) y
gasta el presupuesto de 45 s dos veces. Los bytes que el front manda a
`/api/adjuntar` son **el mismo objeto** que mandó a `/api/archivar`; el nivel
de confianza es el de F-006 (D4 de su spec), ni más ni menos, y se dice.

**Y una cosa que este diseño NO hace, a propósito**: recalcular la huella de
páginas del PDF recibido para compararla con `hash`. F-002 §7 avisa de que la
huella se calcula **sobre las páginas de origen** y de que PyMuPDF puede no
conservar al reserializar lo que copia (riesgo 4 de aquella spec), así que la
igualdad no está garantizada por construcción y una comprobación que fallara
sola mandaría partes buenos a `409`. `/api/archivar` tampoco lo hace. La
integridad **del transporte** sí se comprueba: `sha256` calculado aquí y
cotejado por la pasarela (R7).

### D-I · Tres estados nuevos del error, y ninguno reutiliza los del cierre a la ligera

Se crean en `domain/models/errores.py` (§6). Lo que **se reutiliza** es lo que
es idéntico: `CierreDeshabilitado` y `ConfiguracionSigridIncompleta` (misma
puerta, mismo interruptor, misma fábrica), `ParteNoApto`, `ParteNoArchivado`,
`ReclamacionNoLocalizada`, `EstadoNoCerrable`, `UsuarioSigridNoMapeado`,
`UsuarioSigridInexistente`. Lo nuevo es lo que solo puede pasar con el gráfico
(§7.3).

### D-J · No se escribe en `dbo.log` por el gráfico

**Decidido: ninguna fila (R36).** Tres motivos, y el primero basta:

1. **El ERP no lo hace.** 0 filas con `tab='gra'` en 8,4 millones, y
   `auxgra.conlog=0` en todas las clases **[MEDIDO]**. Escribir una fila
   propia haría nuestros gráficos **anómalos** respecto a los 13.450 de
   posventa —el argumento inverso al de D1 de F-009, donde el ERP **sí**
   escribía y no escribir era lo anómalo—.
2. La pasarela no lo hace y no lo ofrece; habría que hacerlo con un segundo
   `sql/write` **fuera** de la transacción del gráfico, con la reserva de
   `ide` a nuestro cargo, para una fila que ningún informe de Posventa filtra.
3. La trazabilidad está resuelta sin tocar el ERP: `postventa.graficos`
   guarda `gra_cod`, los tres `ide` y quién confirmó; y en el propio ERP,
   `gra.usu` lleva el login y `gra.cod` lleva sello y login, como en los
   manuales.

### D-K · Timeouts: los mismos 35 s, y por qué bastan

`SIGRID_TIMEOUT_S = 35` también para el gráfico (R37), dentro del escalonado
35 → 40 → 45 de `ARCHITECTURE.md`. Lo que se sabe del tamaño y del tiempo:

| Dato | Valor | Fuente |
|---|---|---|
| Parte firmado real en el ERP | **242.534 bytes** | `03_modelo_posventa_sigrid.md` §4.2 **[MEDIDO]** |
| Remesa real de Mirasierra | 22 partes en **5 MB** → ~230 KB por parte | `ARCHITECTURE.md` §«Por qué el proceso va parte a parte» **[MEDIDO]** |
| Un parte de dos hojas (F-014) | ~2× → ~0,5 MB | **[INFERIDO]** |
| Tope de la pasarela | 10 MB de fichero; el base64 (×1,33 + relleno) se comprueba **antes** de decodificar | `document_write_guard.py` **[MEDIDO en código]** |
| Margen | **~40×** entre el parte típico y el tope | — |
| Duración real del commit con 303 bytes | no anotada en T20; la traza `duracion_ms` del caso de uso queda en los logs de la pasarela | `verificacion_F-004_t20_t21.md` |
| Timeout de la transacción en la pasarela | 120 s (`SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS`) | `sigrid_api.md` §4 |

Con 320 KB de base64 por el proxy y tres `INSERT` de una fila, el commit está
en la escala de los segundos, no de las decenas **[INFERIDO]**; la medida real
se toma en el bloque 9 (T-verificación) con un parte de tamaño real y queda
anotada. Si algún día un parte se acercara a los 10 MB, lo que habría que
cambiar es el montaje (patrón asíncrono), no el número —la regla de
`docs/DESPLIEGUE.md` §7—, y esa decisión no se toma aquí.

**El desajuste 35 s / 120 s se maneja, no se ignora**: si nosotros abortamos a
los 35 s, la pasarela puede seguir escribiendo hasta 120. Por eso la traza
queda en `error` con el motivo «tiempo agotado: puede que el ERP haya escrito;
el reintento es seguro» (R28, R29), y el reintento —manual o del front— lo
resuelve la idempotencia por contenido: si la primera escribió, la segunda
responde `idempotente: true`.

**Tope propio `GRAFICO_MAX_BYTES`** (defecto 10 485 760, R18): se comprueba en
el paso antes de componer la petición, para no mandar 13 MB de base64 por el
proxy a que la pasarela los rechace. Se documenta que **no debe superar** el
de la pasarela: subirlo aquí solo compra un `409` más tardío.

**Una observación fuera de encargo que este diseño hereda**: `peticion()` de
`js/api.js` reintenta lo `transitorio` (502, red, timeout) en **todos** los
pasos, también en `cerrar` con `commit` (F-009). No hace falta cambiarlo: en
el cierre es seguro porque el backend rehace el dry-run en cada llamada (una
reclamación ya en `CER` responde `ya_cerrada`), y en el gráfico lo es por la
idempotencia del endpoint. Se deja escrito para que nadie lo lea como un
reintento de escritura no controlado.

### D-L · El fichero y el `hash` son dos cosas, y el diseño no las confunde

`hash` (huella de páginas, F-002) identifica **el parte** y es la clave de
todas las trazas. `sha256` identifica **los bytes** enviados y es lo que la
pasarela coteja y lo que decide su idempotencia. Consecuencia directa: si el
mismo parte se vuelve a trocear y PyMuPDF serializa bytes distintos, el
`sha256` cambia y **la pasarela no lo reconocería** como el mismo documento.
Por eso la capa 1 de idempotencia (la traza local por `hash`, R24) va
**antes** que la de la pasarela, y por eso la traza guarda el `sha256` con el
que se adjuntó: para poder explicar, después, qué bytes exactos hay en Sigrid.

## 3 · Ficheros a crear

Todos bajo `services/postventa-api/`, salvo donde se indique.

| Ruta | Capa | Qué contiene |
|---|---|---|
| `domain/models/grafico.py` | **domain** | `RES_GRAFICO_PARTE`, `FIRMA_PDF`, `LONGITUD_MAXIMA_RES`, `LONGITUD_MAXIMA_NOM`, `LONGITUD_MAXIMA_USU`, `FILAS_ESPERADAS_GRAFICO`, `CODIGOS_PASARELA_*` (las tres familias de códigos de error de la pasarela), `PeticionGrafico`, `PlanDeGrafico`, `RespuestaGrafico`, `ResultadoGrafico`, y las funciones puras `componer_peticion(...)`, `validar_fichero(...)`, `esta_colgado(respuesta)`, `clasificar_codigo(codigo)`. Sin red, sin SQL, sin reloj |
| `domain/ports/grafico.py` | **domain** | `GraficoPort`: `adjuntar(*, peticion, commit) -> RespuestaGrafico`. Un método |
| `application/pipelines/paso_grafico.py` | **application** | Orquesta: apto → archivado → fichero (tope, firma) → traza local → login → reclamación → `evaluar` → dry-run → traza `dry_run_ok` → (autorización) → commit → traza `adjuntado`/`error` |
| `infrastructure/sigrid/graficos.py` | infra | `AdaptadorGraficoSigridApi(GraficoPort)`: `httpx` contra `POST /api/sigrid/concepto-grafico`, base64, puerta de entorno **y** de interruptor en el constructor, lectura de `details.codigo` y nada más del cuerpo de error |
| `infrastructure/persistencia/sql/09_graficos.sql` | infra/SQL | La traza del gráfico (§8.1) |
| `interface_adapters/api/adjuntar.py` | interface | Handler de `POST /api/adjuntar`: `multipart`, compone los cinco puertos, serializa |
| `infra/15_reclamaciones_obra_prueba.ps1` | infra | **Solo lectura**: localiza las reclamaciones de la obra 404 cerrables y sin gráfico (§15). Lo lanza el humano |
| `infra/16_grafico_sigrid.ps1` | infra | **Solo lectura**: las tres filas del gráfico por `cod` (negocio, documental con `DATALENGTH`, enlace), `MAX(ide)` de `dbo.log` antes/después, y `documents/read` para comparar el `sha256` |
| `infra/17_traza_grafico_local.ps1` | infra | **Solo lectura** del esquema propio: la traza de `postventa.graficos`, al modo de `12_traza_cierre_local.ps1` |

### Tests a crear (`services/postventa-api/tests/`)

`test_f012_dominio_grafico.py`, `test_f012_paso_grafico.py`,
`test_f012_adaptador_grafico.py`, `test_f012_fabrica_grafico.py`,
`test_f012_adjuntar_http.py`, `test_f012_cerrar_exige_grafico.py`,
`test_f012_arquitectura.py`, `test_f012_ddl_orden.py`,
`test_f012_repositorio_graficos.py`, `test_f012_logs_sin_datos_personales.py`,
`test_f012_documentacion.py`, `test_f012_scripts_infra.py`; y en
`tests/utiles_sigrid.py`, el doble `GraficoEnMemoria` (dry-run, commit,
idempotente, y cada código de error de la pasarela, programables).

En `services/postventa-front/`: `tests_js/grafico.test.js`
(`cuerpoDeGrafico`, la decisión «solo se cierra lo adjuntado») y
`tests/test_f012_front.py` (la pantalla pinta los dos dry-run y los tres
estados).

## 4 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/cierre.py` | **Se retiran** `AVISO_SIN_GRAFICO` y el campo `PlanDeCierre.aviso_sin_grafico` (R48). `evaluar` y `_plan` dejan de rellenarlo. Nada más |
| `domain/models/persistencia.py` | `EstadoGrafico` (`pendiente`, `dry_run_ok`, `adjuntado`, `error`, `ya_cerrada`) y `TrazaGrafico` |
| `domain/models/errores.py` | `CuerpoDeGraficoInvalido`, `GraficoDemasiadoGrande`, `GraficoNoEsPdf`, `ParteNoAdjuntado`, `GraficoRechazadoPorLaPasarela` (lleva `codigo`), `EscrituraDocumentalDeshabilitada` (lleva `codigo`), `GraficoFallido` (lleva `reintento_seguro: bool`), `GraficoSinTraza` |
| `domain/ports/persistencia.py` | `RepositorioPartesPort` gana `guardar_grafico(*, traza)` y `consultar_grafico(*, hash_parte) -> TrazaGrafico \| None` |
| `application/pipelines/contexto_parte.py` | `grafico: ResultadoGrafico \| None` (lo deja `paso_grafico`) y `traza_grafico: TrazaGrafico \| None` (lo lee `paso_cierre`) |
| `application/pipelines/paso_cierre.py` | (1) `_exigir_adjuntado(ctx, repositorio)` **solo con `commit`**, antes de la escritura (R2, R50); (2) en dry-run, `ctx.traza_grafico = repositorio.consultar_grafico(...)` (R49); (3) `_exigir_autorizacion_para_escribir` pasa a público (`exigir_autorizacion_para_escribir`) para que `paso_grafico` lo reutilice (R23). El módulo sigue sin nombrar `rcg` ni `gra` como palabras (control negativo de F-009 intacto) |
| `infrastructure/sigrid/fabrica.py` | `construir_graficos(ajustes)`: mismo orden entorno → interruptor → configuración; **no** resuelve el huso (el sello lo pone la pasarela) |
| `infrastructure/persistencia/ddl.py`, `arranque.py` | Registrar `09_graficos.sql` |
| `infrastructure/persistencia/sentencias.py`, `repositorio_pg.py`, `mapeo.py` | `upsert_grafico` (sin pisar `adjuntado`, patrón de `upsert_cierre`), `select_grafico`, fila → `TrazaGrafico` |
| `config/settings.py` | `SIGRID_GRATIPIDE_PARTE` (int, 35) y `GRAFICO_MAX_BYTES` (int, 10 485 760) en el bloque de Sigrid, con su porqué |
| `function_app.py` | Ruta `adjuntar` en `ANONYMOUS` (mismo motivo documentado que las demás), traducción de errores a 400/409/502/503/500; en `cerrar`, `ParteNoAdjuntado` → 409. Cabecera: la ventana de escritura cubre ahora `/api/adjuntar` y `/api/cerrar` |
| `interface_adapters/api/cerrar.py` | `_dry_run()` pierde `aviso_sin_grafico` y gana `grafico: {estado, nombre_fichero, sha256, adjuntado_at_utc}` (R49) |
| `services/postventa-front/js/api.js` | `adjuntar(formData, hash)` |
| `services/postventa-front/js/pipeline.js` | `cuerpoDeGrafico(parte, opciones)` (el `FormData`), `estaAdjuntado(parte)` |
| `services/postventa-front/js/app.js`, `index.html`, `css/styles.css` | Los dos dry-run juntos; `confirmarCierre` → adjuntar y, solo si `adjuntado`, cerrar; estados `adjuntado`, `error_grafico`; el bloque ámbar del aviso se sustituye por el bloque del gráfico (§9.1) |
| `infra/desplegar_backend.ps1` | `SIGRID_GRATIPIDE_PARTE=35` y `GRAFICO_MAX_BYTES=10485760` en `$ajustes`; el texto de «Ventana de escritura» nombra también el gráfico |
| `docs/ARCHITECTURE.md` | Paso 7 → «Gráfico y cierre» (7a/7b); la sección «RIESGO ACEPTADO» pasa a **cerrada** con fecha y feature, conservando el texto histórico; tabla de sistemas externos (`sigrid/concepto-grafico`, variables nuevas) |
| `docs/INTEGRACION.md` | §1 (consumimos el endpoint), §3 bis (tres filas, dos bases, por la pasarela), §4 (variables nuevas), §6 (qué se rompe si el dueño cambia `SIGRID_DOCUMENT_*`), §8 (`/api/adjuntar`), y la nota «lo que sí va a exigir F-012» pasa a resuelta (R68) |
| `docs/DESPLIEGUE.md` | §4 bis: la ventana cubre adjuntar y cerrar; las dos App Settings nuevas en la tabla |
| `azure-apps/postventa_incidencias.md` | Copia refrescada de `INTEGRACION.md` (R70). **Otro repositorio**: commit local allí, sin push |
| **Tests de F-009 que derogan R21** (R48) | `tests/test_f009_dominio_cierre.py` (los tests de R21 y las construcciones de `PlanDeCierre` con `aviso_sin_grafico`), `test_f009_adaptador_sigrid.py`, `test_f009_escrituras.py`, `test_f009_cerrar_http.py` (las dos aserciones sobre `aviso_sin_grafico`), `services/postventa-front/tests/test_f009_front.py` (los dos tests `r21_*`). Se retiran **esas aserciones y ninguna otra**, y cada retirada cita R48 |
| `tests/test_f009_documentacion.py` | Se conservan sus literales («RIESGO ACEPTADO», «sin ninguna fila en `rcg`», «2.365», «fecha de caducidad», «F-012»): la sección de `ARCHITECTURE.md` los mantiene en pasado. Si el implementer decide reescribirla sin ellos, cambia también estos tests y lo dice |

## 5 · Ficheros que NO se tocan

- **`infrastructure/sigrid/cliente.py`, `consultas.py`, `escrituras.py`** — el
  cierre no cambia ni una sentencia (R51). El gráfico **importa** de
  `cliente.py`; no lo edita.
- **`domain/ports/erp.py`** — tres métodos y ni uno más. El gráfico tiene su
  puerto.
- **`infrastructure/persistencia/sql/06_cierres.sql`** y los demás `NN_*.sql`
  existentes — la traza nueva es una tabla nueva.
- **`infrastructure/sharepoint/`**, **`application/pipelines/paso_archivo.py`**
  — el archivo va antes y no se toca.
- **`domain/models/nombrado.py`** — se **usa** para `nom`; no se cambia.
- **El repositorio `sigrid-api`** — solo lectura. Lo que su configuración
  exija es precondición (H4), no trabajo de aquí.
- **`harness/features.json`** — lo cambia el humano.
- **`progress/`** — lo anota el líder.

## 6 · Las firmas que importan

### Dominio (`domain/models/grafico.py`)

```
RES_GRAFICO_PARTE = "PARTE FIRMADO"      # lo que Posventa teclea (3.197/3.680)
FIRMA_PDF = b"%PDF-"
LONGITUD_MAXIMA_RES, LONGITUD_MAXIMA_NOM, LONGITUD_MAXIMA_USU = 48, 255, 24
FILAS_ESPERADAS_GRAFICO = 3               # documental + negocio + enlace

CODIGOS_PASARELA_REINTENTABLES   = ("colision_de_clave", "sha256_no_coincide",
                                    "filas_afectadas_inesperadas")          # → 502, ERP intacto
CODIGOS_PASARELA_PRECONDICION    = ("escritura_documental_deshabilitada",
                                    "base_de_datos_no_permitida")           # → 503
CODIGOS_PASARELA_RECHAZO         = ("concepto_no_encontrado", "tipo_de_concepto_no_coincide",
                                    "clase_de_grafico_no_permitida", "usuario_no_valido",
                                    "fichero_vacio", "tipo_de_fichero_no_permitido",
                                    "tamano_excedido")                      # → 409

@dataclass(frozen=True) PeticionGrafico:
    conide: int; contip: int; gratipide: int
    res: str; nom: str; usu: str
    sha256: str; bytes: int
    contenido: bytes = field(repr=False)   # NUNCA en __repr__, logs ni respuestas

@dataclass(frozen=True) PlanDeGrafico:     # lo que devuelve el dry-run
    reclamacion: Reclamacion; login_sigrid: str
    peticion: PeticionGrafico
    cerrable: bool; ya_cerrada: bool; motivo: str | None
    idempotente_previsto: bool             # el dry-run ya lo encontró colgado
    cod_previsto: str | None; ide_negocio_previsto: int | None
    avisos_pasarela: tuple[str, ...]

@dataclass(frozen=True) RespuestaGrafico:  # lo que el adaptador devuelve
    ok: bool; committed: bool; idempotente: bool; dry_run: bool
    filas_afectadas: int
    cod: str | None; ide_negocio: int | None; ide_documental: int | None
    ide_enlace: int | None; pos: int | None
    bytes: int; sha256: str; avisos: tuple[str, ...]

@dataclass(frozen=True) ResultadoGrafico:
    plan: PlanDeGrafico; estado: EstadoGrafico
    respuesta: RespuestaGrafico | None = None; motivo: str | None = None
    adjuntado_at_utc: datetime | None = None

def validar_fichero(contenido: bytes, *, tope_bytes: int) -> tuple[int, str]
    # → (bytes, sha256); levanta GraficoDemasiadoGrande / GraficoNoEsPdf (R18, R19)
def componer_peticion(*, reclamacion, login, codigo_obra, numero_incidencia,
                      gratipide, contenido, bytes, sha256) -> PeticionGrafico
    # nom por nombrado.nombre_de_archivo (R9); res constante (R10); topes (R9, R10, R12)
def esta_colgado(respuesta: RespuestaGrafico) -> bool
    # ok and (committed or idempotente)                       (R26)
def clasificar_codigo(codigo: str | None) -> Literal["reintentable", "precondicion", "rechazo", "desconocido"]
```

`esta_colgado` es una función de una línea **a propósito**: es la regla de R26
y tiene que tener nombre, test y mutantes propios. Decidir por `committed`
a secas es el error que la propia pasarela advierte.

### Puerto (`domain/ports/grafico.py`)

```
adjuntar(*, peticion: PeticionGrafico, commit: bool) -> RespuestaGrafico
```

Levanta `CierreDeshabilitado` (puerta), `EscrituraDocumentalDeshabilitada`
(la pasarela dice que su documental está cerrada), `GraficoRechazadoPorLaPasarela`
(un código de rechazo), `GraficoFallido` (reintentable, pasarela caída, red,
tiempo agotado; con `reintento_seguro=True` siempre, porque el endpoint es
idempotente). **Nunca** lleva el cuerpo crudo (R35).

### Paso (`application/pipelines/paso_grafico.py`)

```
paso_grafico(ctx, erp, graficos, repositorio, usuarios, preferencias, *,
             commit: bool, confirmado: bool, usuario_oid: str, correo: str,
             numero_incidencia: str, codigo_obra: str, gratipide: int,
             tope_bytes: int, ahora: datetime) -> ContextoParte
```

Orden **no negociable**:

1. apto (R14) → 2. archivado (R15) → 3. fichero: tope y firma (R18, R19) →
4. **traza local**: si `adjuntado`, se devuelve sin llamar a nadie (R24) →
5. login confirmado o derivado y verificado (`resolver_login_de_sigrid` de
F-009, R12) → 6. `leer_reclamacion` → 7. `evaluar`: `ya_cerrada` (R16) o no
cerrable (R17) → 8. `componer_peticion` → 9. **dry-run** `adjuntar(commit=False)`
(R20) → 10. traza `dry_run_ok` (R42) → 11. si no `commit`, fin → 12.
`exigir_autorizacion_para_escribir` (R23) → 13. `adjuntar(commit=True)` →
14. `esta_colgado` y, si `committed`, `filas_afectadas == 3` (R26, R27) →
15. traza `adjuntado` (R43) o `error` con motivo y «reintento seguro» (R28,
R29); `GraficoSinTraza` si el ERP escribió y la traza no (R47).

### Adaptador (`infrastructure/sigrid/graficos.py`)

```
AdaptadorGraficoSigridApi(*, entorno, cierre_habilitado, base_url, api_key,
                          base_datos, timeout_s, cliente=None)
```

Constructor: `exigir_entorno_con_cierre` y `exigir_interruptor_de_cierre`
(R38, R39). **Un intento por llamada**, sin `Retrying`: el dry-run es una
lectura, pero va pegado al commit en el mismo flujo y un dry-run que reintenta
tres veces con 320 KB de base64 se come el presupuesto. El cuerpo se compone
con `base64.b64encode` sobre `peticion.contenido` y **no se registra** (R53).
Del `400` de la pasarela se parsea `details.codigo`, se comprueba contra las
tres listas cerradas y **se descarta el resto del cuerpo** (R35).

### Repositorio (`domain/ports/persistencia.py`)

```
guardar_grafico(*, traza: TrazaGrafico) -> ResultadoGuardado   # no pisa `adjuntado` (R30)
consultar_grafico(*, hash_parte: str) -> TrazaGrafico | None
```

## 7 · El contrato con la pasarela, campo a campo

### 7.1 · La petición que compone este servicio

| Campo | Valor | De dónde | Requisito |
|---|---|---|---|
| `database` | `SIGRID_BASE_DATOS` | configuración | R13 |
| `conide` | `reclamacion.ide` | `leer_reclamacion` (F-009) | R8 |
| `contip` | `reclamacion.tip` | íd. | R8 |
| `gratipide` | `SIGRID_GRATIPIDE_PARTE` (35) | configuración | R11 |
| `res` | `PARTE FIRMADO` | constante del dominio | R10 |
| `nom` | `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf` | `nombrado.nombre_de_archivo` | R9 |
| `usu` | login de quien confirma | `resolver_login_de_sigrid` (F-009) | R12 |
| `contenido_base64` | los bytes del parte | el `multipart` de `/api/adjuntar` | R6 |
| `sha256` | `hashlib.sha256(contenido)` | calculado aquí | R7 |
| `commit` | `false` en el dry-run, `true` solo tras R23 | el paso | R20, R23 |

Lo que **no** se manda, porque la pasarela no lo admite y lo decide ella: la
base documental, `cod`, `ide`, `vin`, `pos`, `emp` **[MEDIDO en
`AttachConceptoGraficoRequest`: `extra="ignore"`]**.

### 7.2 · La respuesta, y qué se toma de ella

`{ ok, committed, dry_run, idempotente, database, database_documental,
concepto, grafico, enlace, filas_afectadas, avisos }`. Se toman: `ok`,
`committed`, `idempotente`, `filas_afectadas`, `grafico.cod`,
`grafico.ide_negocio`, `grafico.ide_documental`, `grafico.bytes`,
`grafico.sha256`, `enlace.ide`, `enlace.pos`, `avisos`. Las dos filas
completas del preview (`fila_documental`, `fila_negocio`) **no** se guardan ni
se devuelven al front: 29 columnas de las que el usuario no decide ninguna.

Tres cosas que la respuesta idempotente trae distintas, y que el adaptador
tolera **[MEDIDO T21 y «Observación menor» de la verificación de F-004]**:
`committed: false`, `grafico.fec = 0`, `grafico.ide_documental = null`,
`enlace.pos = null`. Ninguna de las tres es un error, y `esta_colgado`
responde `True`.

### 7.3 · Cada código de error de la pasarela, y qué hacemos

| `details.codigo` | Qué significa | ERP | Excepción | HTTP | Traza |
|---|---|---|---|---|---|
| — (`200`, `idempotente: true`) | ya colgado, mismo tamaño y `sha256` | intacto | ninguna: **éxito** | 200 `adjuntado` | `adjuntado`, `idempotente=true` (R25) |
| `colision_de_clave` | agotados los reintentos de la pasarela; **rollback** | intacto | `GraficoFallido(reintento_seguro=True)` | 502 | `error` (R31) |
| `sha256_no_coincide` | corrupción en tránsito | intacto | `GraficoFallido(reintento_seguro=True)` | 502 | `error` (R31) |
| `filas_afectadas_inesperadas` | la relectura no vio las tres; **rollback** | intacto | `GraficoFallido(reintento_seguro=True)` | 502 | `error` (R31) |
| `escritura_documental_deshabilitada` | precondición H4 del dueño de la pasarela (también en dry-run si `SIGRID_DOCUMENT_WRITE_DATABASE` está vacía) | intacto | `EscrituraDocumentalDeshabilitada` | 503 | ninguna (R32) |
| `base_de_datos_no_permitida` | `SIGRID_BASE_DATOS` no está en su lista blanca | intacto | `EscrituraDocumentalDeshabilitada` | 503 | ninguna (R32) |
| `concepto_no_encontrado` | `conide` no existe | intacto | `GraficoRechazadoPorLaPasarela` | 409 | `error` (R33) |
| `tipo_de_concepto_no_coincide` | `contip` ≠ `con.tip`, o no está en `ALLOWED_CONTIP` | intacto | íd. | 409 | `error` |
| `clase_de_grafico_no_permitida` | `gratipide` fuera de `ALLOWED_GRATIPIDE`, inexistente o de baja | intacto | íd. | 409 | `error` |
| `usuario_no_valido` | el login no está en `dbo.usu` (no debería ocurrir: F-009 lo verificó antes) | intacto | íd. | 409 | `error` |
| `fichero_vacio`, `tipo_de_fichero_no_permitido`, `tamano_excedido` | no deberían llegar: R18/R19 los cortan antes | intacto | íd. | 409 | `error` |
| `400` «Solicitud invalida.» / `ValueError` (lectura truncada) | cuerpo mal formado, o la pasarela no pudo ver todas las filas | intacto | `GraficoFallido(reintento_seguro=True)` | 502 | `error` (R34) |
| `500`, no-JSON, red, tiempo agotado | no se sabe si escribió | **desconocido** | `GraficoFallido(reintento_seguro=True)` | 502 | `error` con «puede que el ERP haya escrito; el reintento es seguro» (R28, R29, R34) |

La columna «ERP» está medida en el código de la pasarela: todo `400` de
negocio se levanta **antes** del `COMMIT` o dentro de `run_in_write_transaction`,
que revierte. El único caso en que el ERP puede haber escrito sin que lo
sepamos es la última fila, y es la que la idempotencia resuelve.

## 8 · El SQL

### 8.1 · `09_graficos.sql`, en el schema propio

Numeración `NN_nombre.sql`, idempotente, con cabecera, según
`docs/CONVENTIONS.md`. Schema `postventa`, **nunca `public`** ni nada fuera de
él.

```sql
CREATE TABLE IF NOT EXISTS postventa.graficos (
    hash_parte           text PRIMARY KEY
                         REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    numero_incidencia    text NOT NULL,
    estado               text NOT NULL
                         CHECK (estado IN ('pendiente', 'dry_run_ok', 'adjuntado', 'error', 'ya_cerrada')),
    sha256               text,
    bytes                integer,
    nombre_fichero       text,
    gratipide            integer,
    gra_cod              text,
    gra_ide_negocio      integer,
    gra_ide_documental   integer,
    rcg_ide              integer,
    idempotente          boolean NOT NULL DEFAULT false,
    confirmado_por       text,
    motivo               text,
    intentos             integer NOT NULL DEFAULT 0,
    dry_run_at_utc       timestamptz,
    adjuntado_at_utc     timestamptz
);

CREATE INDEX IF NOT EXISTS ix_graficos_estado ON postventa.graficos (estado);
```

- `hash_parte` con clave ajena contra `partes` (R46): igual que `archivos` y
  `cierres`, no se deja traza de lo que no consta guardado.
- `confirmado_por` es **dato personal seudónimo** (el `oid`), nunca el login
  (R44). `gra_cod` **sí lleva el login del ERP dentro** (`...` + `.login`),
  porque es el identificador del gráfico tal y como Sigrid lo genera y es lo
  que hace falta para localizarlo; se anota en la cabecera del `.sql` y en
  `mapeo.py`, y el script 16 no lo imprime con el login separado.
- Ni una columna binaria (R45): el PDF vive en SharePoint y en Sigrid.
- `gra_ide_documental` puede quedar `NULL` en el caso idempotente **[MEDIDO:
  la respuesta no lo trae]**; no se inventa.

### 8.2 · `upsert_grafico` y `select_grafico` (`sentencias.py`)

Mismo patrón que `upsert_cierre`: `INSERT ... ON CONFLICT (hash_parte) DO
UPDATE ... WHERE graficos.estado <> 'adjuntado'`, con el estado terminal como
**parámetro** y no pegado al SQL. Si la fila ya está en `adjuntado`, no
devuelve fila y el repositorio responde `SIN_CAMBIOS` (R30).

`select_grafico` devuelve la fila completa por `hash_parte`; la lee
`paso_grafico` (capa 1 de idempotencia) y `paso_cierre` (R2, R49).

### 8.3 · Contra Sigrid, este servicio **no escribe ningún SQL nuevo**

Es lo que distingue esta feature de F-009: las tres filas las compone y las
escribe la pasarela, con sus constantes medidas, su applock y su relectura.
Aquí no hay `INSERT` alguno contra el ERP. Lo único que se lee es lo que ya
leía F-009 (`select_reclamacion`, `select_usuario`), sin cambios (R52).

## 9 · El flujo, de punta a punta

### 9.1 · Lo que ve el usuario

1. Pulsa **«Ver qué pasaría (no cierra nada)»**. Para cada parte cerrable el
   front pide, por la cola de concurrencia, `POST /api/adjuntar` sin `commit`
   y después `POST /api/cerrar` sin `commit` (R63). La tarjeta del parte pinta:
   - **el gráfico**: «Se adjuntará `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`
     (237 KB, clase 35 · POSTVENTA:Fotos Reparaciones) firmado por `login`»,
     o «**ya está dentro de Sigrid** (mismo contenido): no se escribirá nada»
     si el dry-run vino `idempotente` (R22), más los avisos de la pasarela
     tal cual (R21, R67);
   - **el cierre**: lo de F-009 (estados legibles, login), **sin el bloque
     ámbar** del aviso (R48), y con la línea «gráfico: se adjuntará antes» /
     «ya adjuntado el <fecha>» según R49.
2. Pulsa **«Cerrar las incidencias»** → «¿Seguro? Esto escribe en Sigrid…» →
   **una** confirmación, que caduca (R23, R66).
3. Para cada parte: `adjuntar` con `commit` → si responde `adjuntado`, `cerrar`
   con `commit` (R64). Estados finales por parte: `cerrado`, **`adjuntado`
   (gráfico dentro, cierre pendiente)** con botón «reintentar el cierre»,
   `error_grafico` (nada escrito, o «puede que sí; el reintento es seguro»),
   `ya_cerrada`.

### 9.2 · Lo que pasa por dentro, en el caso bueno

```
front ──multipart(PDF)──▶ /api/adjuntar (dry-run) ──▶ paso_grafico
   apto · archivado · fichero · traza · login · leer_reclamacion · evaluar
   ──▶ sigrid-api concepto-grafico commit:false  ──▶ 200 preview
   ◀── traza dry_run_ok ◀──
front ──json──▶ /api/cerrar (dry-run) ──▶ paso_cierre (como F-009, + traza_grafico)
[confirmación]
front ──multipart(PDF)──▶ /api/adjuntar commit ──▶ paso_grafico
   (todo lo anterior otra vez) ──▶ sigrid-api commit:true ──▶ 200 committed:true filas:3
   ◀── traza adjuntado ◀──
front ──json──▶ /api/cerrar commit ──▶ paso_cierre
   consultar_grafico == adjuntado ✔ ──▶ sql/write (las dos filas de F-009) ──▶ traza cerrado
```

### 9.3 · Las tres capas de idempotencia (R24–R26), en orden

1. **Traza local** por `hash` de parte: `adjuntado` → no se llama a nadie.
   Cubre el reintento normal y **el único caso que la pasarela no cubriría**:
   el mismo parte re-troceado con bytes distintos (D-L).
2. **La pasarela** por tamaño + `sha256`, comprobado dos veces (dry-run y
   dentro de la transacción). Cubre la traza perdida —`GraficoSinTraza`— y la
   llamada repetida por un corte de red.
3. **`evaluar`**: una reclamación ya en `CER` no recibe un segundo gráfico
   (R16).

Riesgo residual, y se dice: perder la traza local **y además** que los bytes
del parte cambien entre dos troceados dejaría un segundo gráfico en la
reclamación. Exige dos fallos independientes; el segundo gráfico sería
visible en la ficha y borrable desde la UI de Sigrid (lo que la pasarela no
hace, H6).

### 9.4 · Los tres escenarios de fallo, y cómo queda cada cosa

| Escenario | ERP | Traza `graficos` | Traza `cierres` | Front | Reintento |
|---|---|---|---|---|---|
| Falla el gráfico (409/503/502 sin escritura) | intacto | `error` | sin tocar (el cierre no se pide, R4) | `error_grafico` | seguro; el usuario vuelve a pulsar |
| Tiempo agotado en el commit del gráfico | **desconocido** | `error` «puede que haya escrito» | sin tocar | `error_grafico` | seguro por idempotencia (R29) |
| Gráfico OK, falla el cierre | **abierta con su gráfico** (R3) | `adjuntado` | `error` (F-009 R27) | **`adjuntado`** | el gráfico responde desde la traza (capa 1) y el cierre se reintenta como en F-009 |
| Gráfico OK, cierre OK, y se repite todo (R18/R42 de F-009) | `CER` con su gráfico | `adjuntado`, no se pisa (R30) | `cerrado`, no se pisa | `ya_cerrada` | nada que escribir |

## 10 · Encaje en la arquitectura, y límite de microservicio

- **`domain/`** no importa `httpx`, no conoce base64 como transporte, no sabe
  qué es un `multipart`. `componer_peticion`, `validar_fichero` y
  `esta_colgado` deciden con datos.
- **`infrastructure/sigrid/`** sigue siendo el **único** paquete que conoce
  `sigrid-api`; el gráfico es un módulo más dentro de él.
- **`application/pipelines/paso_grafico.py`** orquesta contra puertos y se
  prueba entero con `ErpEnMemoria` + `GraficoEnMemoria` + el doble de PG.
- **La composición vive en `interface_adapters/api/adjuntar.py`**, nunca
  dentro del paso (`docs/CONVENTIONS.md`).
- El paso 7 del pipeline de `ARCHITECTURE.md` pasa a ser **7a Gráfico + 7b
  Cierre**, en ese orden, y el riesgo aceptado se cierra.

`test_f012_arquitectura.py` lo fija como los `test_fXXX_arquitectura`
anteriores, y añade un control negativo propio: **ningún módulo de
`domain/` ni `application/` contiene `base64`** como palabra —el transporte es
cosa del adaptador—.

**Límite de microservicio: F-012 no cruza ninguna frontera.** Lo que en
agosto exigía una decisión del dueño de `sigrid-api` (`design.md` §11 de
F-009) **ya está tomado y desplegado** por ese dueño (su F-004). Este servicio
consume un endpoint de dominio, exactamente como `remesas` o `partes` consumen
`sql/read`. La única responsabilidad que sigue siendo ajena —las App Settings
`SIGRID_DOCUMENT_*` de la pasarela— se declara como precondición (H4) y se
documenta en `INTEGRACION.md` §6 como «qué se rompe si el dueño la cambia».

## 11 · Riesgos, y alternativas descartadas

| Riesgo | Qué lo contiene |
|---|---|
| Cerrar sin gráfico (la anomalía de F-009) | R2: `paso_cierre` exige `adjuntado` en la traza antes del `commit`; R4: el front no pide el cierre si el gráfico falló |
| Adjuntar a una reclamación equivocada | `conide` sale de la misma lectura por `con.cod` + `tip` que F-009 (23.063/23.063 únicos); la pasarela coteja `contip` |
| Adjuntar a una reclamación que no se va a cerrar | `evaluar` (R16, R17): `CER` y `NPR` no reciben gráfico |
| Duplicar el gráfico | Tres capas (§9.3) |
| Dar por adjuntado lo que no lo está | `esta_colgado` (R26) + `filas_afectadas == 3` con `committed` (R27) + relectura de la pasarela antes del `COMMIT` |
| Mandar el PDF con el DNI a un log | `PeticionGrafico.contenido` con `repr=False`; el adaptador registra bytes y `sha256`; control negativo `test_f012_logs_sin_datos_personales.py` (R53) |
| Que el `sha256` viaje mal | Lo calcula este servicio y lo coteja la pasarela (R7); `sha256_no_coincide` → 502 reintentable |
| Escribir desde un puesto de trabajo | Doble puerta en fábrica y constructor (R38, R39) + guardia de red de la suite (R41) |
| Que el commit tarde más de 35 s | Margen ~40× en tamaño; traza `error` honesta + reintento seguro (D-K); medición real en el bloque 9 |
| Que el dueño de la pasarela cierre la documental | `escritura_documental_deshabilitada` → 503 sin tocar nada (R32); `INTEGRACION.md` §6 lo declara |
| Firmar el gráfico con otro login | Solo el login verificado de F-009 (R12); la pasarela vuelve a comprobar `dbo.usu` |
| Un parte que no es PDF, o enorme | R18/R19 cortan antes de llamar; la pasarela vuelve a cortar |

**Alternativas descartadas:**

- **Extender `paso_cierre`** en vez de un paso nuevo (D-A).
- **Un solo endpoint que adjunte y cierre** (D-A).
- **Un interruptor propio `GRAFICO_HABILITADO`** (D-B).
- **Columnas en `postventa.cierres`** y **clave ajena `cierres → graficos`**
  (D-C).
- **Descargar el PDF de SharePoint** en vez de recibirlo del front (D-H).
- **Recalcular la huella del PDF recibido** (D-H).
- **Escribir una fila en `dbo.log`** por el gráfico (D-J).
- **Un `res` propio rastreable** (D-E).
- **Reintentar el commit automáticamente** en el adaptador: aunque aquí sería
  seguro, un adaptador que reintenta escrituras es un precedente que
  `cliente.py` prohíbe por buenas razones, y el reintento lo pide el usuario
  con un clic (o el front por lo transitorio, D-K).
- **`sql/write` a mano** para las tres filas: la documental está cerrada a
  `sql/write` a propósito (`DatabaseReferenceGuard`, F-003 de la pasarela) y
  el endpoint de dominio existe justo para esto (`sigrid_api.md` §7.1).

## 12 · Decisiones cerradas

| # | Decisión | Qué se hace |
|---|---|---|
| **D-A** | Paso nuevo `paso_grafico` delante de `paso_cierre` | `paso_cierre` gana R2 y pierde R21 de F-009 |
| **D-B** | El interruptor es **`CIERRE_HABILITADO`** | Una ventana de escritura en el ERP; doble comprobación |
| **D-C** | Traza en **`postventa.graficos`** (tabla nueva, `09_graficos.sql`) | `adjuntado` terminal; sin FK desde `cierres` |
| **D-D** | Puerto `GraficoPort` y adaptador propios; `ErpPort` intacto | El adaptador importa la fontanería de `cliente.py` |
| **D-E** | `nom` = nombre de F-006; `res` = `PARTE FIRMADO` | Un documento, un nombre, dos sitios |
| **D-F** | `conide`/`contip` de la reclamación leída; `gratipide` configurable (35) | Pregunta a Posventa en §14 |
| **D-G** | Solo se adjunta lo cerrable (`evaluar`) | `CER` → `ya_cerrada`; `NPR` → 409 |
| **D-H** | El PDF lo manda el front en `multipart`, como en archivar | Sin descarga de SharePoint, sin recalcular la huella |
| **D-I** | Errores nuevos solo para lo que solo puede pasar con el gráfico | Se reutilizan las puertas y los 409 de F-009 |
| **D-J** | **Ninguna fila en `dbo.log`** | El ERP tampoco la escribe; trazabilidad en la tabla propia |
| **D-K** | `SIGRID_TIMEOUT_S` = 35 también aquí; tope propio `GRAFICO_MAX_BYTES` | El desajuste con los 120 s de la pasarela lo resuelve la idempotencia |
| **D-L** | `hash` ≠ `sha256`, y la traza guarda el segundo | Capa 1 de idempotencia antes que la pasarela |

## 13 · Relación con F-009 y con F-023

### F-009, cuyo bloque 8 sigue sin ejecutar

F-009 está `in_progress` con T22–T27 pendientes (el primer cierre real). Esta
feature **cambia lo que ese bloque espera ver**: el dry-run deja de traer
`aviso_sin_grafico` (R48) y el `commit` exige el gráfico (R2). Dos órdenes
posibles, y **lo decide el humano**:

- **(a) F-009 bloque 8 primero**, con el código de hoy desplegado, sobre
  Mirasierra: produce el cierre `CER` sin gráfico que el riesgo aceptado
  describe. Después F-012. El guion de F-009 vale tal cual.
- **(b) F-012 primero**: el bloque 8 de F-009 se ejecuta con F-012 desplegado
  y su guion (`progress/guion_bloque8_F-009.md`) se corrige antes: T22 espera
  `grafico` en vez de `aviso_sin_grafico`, y T24 pasa por `/api/adjuntar`. La
  primera reclamación real que cierre este servicio tendrá su parte dentro.

Recomendación: **(b)**, porque la anomalía documentada deja de producirse ni
una sola vez, y porque la verificación de F-012 en la obra 404 ya es un cierre
completo de punta a punta que ensaya el bloque 8 sin tocar Mirasierra. Pero
es una decisión de calendario del humano, no del diseño.

### F-023, el gráfico por URL

Sigue `blocked` por la medida Q10 que solo Posventa puede dar. **Con F-012
desplegada, F-023 pierde su motivo**: nació como «la vía que no depende del
dueño de `sigrid-api`» cuando la documental estaba cerrada, y ya no lo está.
`infra/13_caracterizacion_grafico_url.ps1` y `progress/explore_grafico_url.md`
se conservan como conocimiento. Este diseño **no la cancela** —lo decide el
humano—, pero lo deja escrito para que la decisión no se olvide.

## 14 · Preguntas abiertas (con recomendación)

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **P1** | ¿Es `PV002` («POSTVENTA:Fotos Reparaciones», `gratipide` 35) la clase correcta para un **parte firmado**? El nombre no lo dice; los datos sí | (a) 35, como hasta hoy; (b) otra clase de `PV001`–`PV004`, que exigiría además cambiar `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` en la pasarela (dos dueños) | **(a)**: es la clase bajo la que Posventa tiene 3.197 «PARTE FIRMADO» **[MEDIDO]**. Confirmar con Ana Bello / Alicia Echevarría; queda configurable por si cambia |
| **P2** | ¿`res` = `PARTE FIRMADO` a secas, o con sufijo del servicio? | (a) idéntico a Posventa; (b) «PARTE FIRMADO (postventa-incidencias)» | **(a)** (D-E). Cambiarlo es una constante |
| **P3** | ¿Orden entre el bloque 8 de F-009 y F-012? | (a) / (b) de §13 | **(b)** |
| **P4** | ¿Se cancela F-023? | (a) cancelar; (b) mantener `blocked` | **(a)**, salvo que el humano quiera conservar la vía URL como plan B. No es decisión de esta spec |
| **P5** | Un parte de prueba de la **obra 404** que haya pasado el circuito (guardado y archivado) es precondición del bloque 9. ¿Existe? Si no, hay que imprimir un parte de una reclamación de esa obra, firmarlo y escanearlo, o llamar a `/api/adjuntar` desde la consola con un PDF cualquiera sobre un parte guardado a mano | — | Preparar uno **antes** de abrir la ventana; el bloque 9 lo lista como P5 |

Ninguna cambia el diseño: P1 y P2 son una constante o una variable; P3 y P4
son calendario; P5 es preparación.

## 15 · La consulta preparada: reclamaciones de la obra de prueba 404

**Solo lectura. No se ha ejecutado.** Para `POST /api/sql/read` con marcadores
`?` (`sigrid_api.md` §5.2), o empaquetada en
`infra/15_reclamaciones_obra_prueba.ps1` sobre `Invoke-SigridLectura` de
`infra/08_lectura_sigrid_comun.ps1`. Base: la de negocio.

La cadena reclamación → unidad → obra sale del diccionario: `rcp.upvide` es
«Índice (ide) a `upv`», `upv.obride` es «Índice (ide) a `obr`», y `obr` son
«Propiedades de `con`» (una obra es un concepto: su código legible es
`con.cod`) **[MEDIDO en `sigrid_tablas.md`]**. Cómo se escribe el código de la
obra 404 en `con.cod` —`404`, `0404`, otro— **[INFERIDO]**: por eso la
consulta 0 lo localiza primero y el script prueba las dos formas.

```sql
-- Q0 · localizar la obra de prueba (una fila esperada)
SELECT o.ide, c.tip, c.cod, c.res
FROM dbo.obr o
JOIN dbo.con c ON c.ide = o.ide
WHERE c.cod IN (?, ?)
```
Parámetros: `['404', '0404']`.

```sql
-- Q1 · sus reclamaciones, con estado legible y cuántos gráficos tiene cada una
SELECT c.ide, c.cod, c.res, c.est, e.cod AS estado_cod, e.res AS estado_res,
       (SELECT COUNT(*) FROM dbo.rcg r WHERE r.con = c.ide) AS graficos
FROM dbo.rcp p
JOIN dbo.con c ON c.ide = p.ide
JOIN dbo.upv u ON u.ide = p.upvide
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
WHERE u.obride = ? AND c.tip = ?
ORDER BY c.ide DESC
```
Parámetros: `[<ide de la obra de Q0>, 708]`.

```sql
-- Q2 · las candidatas: cerrables (por código de estado) y sin gráfico
SELECT c.ide, c.cod, c.res, e.cod AS estado_cod
FROM dbo.rcp p
JOIN dbo.con c ON c.ide = p.ide
JOIN dbo.upv u ON u.ide = p.upvide
JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
WHERE u.obride = ? AND c.tip = ? AND e.cod IN (?, ?, ?)
  AND NOT EXISTS (SELECT 1 FROM dbo.rcg r WHERE r.con = c.ide)
ORDER BY c.ide DESC
```
Parámetros: `[<ide de la obra>, 708, 'SAT', 'PTE', 'TER']`.

Si Q2 no devuelve ninguna fila, la reclamación de prueba la crea **Posventa**
en la obra 404 desde la UI de Sigrid; este servicio no da de alta
reclamaciones (fuera de su dominio).
