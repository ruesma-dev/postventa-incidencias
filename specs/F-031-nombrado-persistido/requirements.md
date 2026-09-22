<!-- specs/F-031-nombrado-persistido/requirements.md -->
# F-031 · El nombrado del fichero archivado sale del cuerpo, no de lo persistido — Requisitos

> Notación EARS (`specs/SPECS.md`). Rigor **`critico`** (`harness/features.json`):
> escribe —o deja de escribir— en la biblioteca de Posventa un PDF con el DNI
> manuscrito de un cliente, y el fallo que cierra es **silencioso**.
>
> Servicios afectados: `services/postventa-api/` (backend) **y**
> `services/postventa-front/` (front). Son dos carpetas del mismo circuito y
> **no dos responsabilidades**: §7 razona por qué esto no parte el límite de
> microservicio.

## 0 · El defecto, medido

Todo lo de esta sección está **[MEDIDO]** leyendo el árbol del repositorio en
`dev`, commit `7b013ff`. No se ha tocado SharePoint, ni Sigrid, ni Azure, ni
PostgreSQL.

### 0.1 · La asimetría que dejó F-030

| Quién decide | Con qué dato | Fichero y línea |
|---|---|---|
| **La puerta de estado** (¿se archiva?) | `codigo_obra` y `numero_incidencia` **guardados**, dentro de la huella del veredicto | `application/pipelines/puerta_de_estado.py:145-146`; la huella los toma de `domain/models/validacion.py:178-179` |
| **El nombre y la carpeta** (¿dónde acaba el PDF?) | `codigo_obra` y `numero_incidencia` **del cuerpo** | `application/pipelines/paso_archivo.py:199-203` → `_campo(ctx, …)` en `paso_archivo.py:460-470` → `interface_adapters/api/archivar.py:196-200` |

Es decir: desde F-030 la puerta aprueba **unos** valores y el fichero se nombra
con **otros**. Hoy coinciden porque el front manda lo que leyó; nada del
backend lo garantiza.

### 0.2 · Lo que ya está guardado y ya viaja, sin costar nada

La consulta de situación **ya trae los dos códigos persistidos**, porque F-030
los necesitaba para recomponer la huella:

- `infrastructure/persistencia/sentencias.py:632-645` ·
  `select_veredicto_y_cierre` selecciona `p.codigo_obra, p.numero_incidencia`
  de `postventa.partes` (línea 635);
- `infrastructure/persistencia/mapeo.py:432-433` los deja en
  `ResultadoValidacion.codigo_obra` / `.numero_incidencia`;
- `application/pipelines/puerta_de_estado.py:145` deja esa situación en
  `ctx.situacion`, **antes** de que `paso_archivo` nombre nada
  (`paso_archivo.py:197` va antes de `:199`).

**Consecuencia de diseño, y es la que abarata esta feature**: el dato correcto
ya está delante del nombrado. No hace falta ninguna consulta nueva, ninguna
columna nueva, ningún método nuevo en `RepositorioPartesPort` y ningún cambio
en el SQL. Es lo contrario de F-033, que sí tuvo que traerse la traza.

### 0.3 · La segunda mitad: qué hace el front cuando alguien corrige a mano

**[MEDIDO]** en `services/postventa-front/`:

1. `js/app.js:428-435` · `editarCampo` deja la corrección en `parte.ediciones`
   (memoria) y se la pasa al autoguardado.
2. `js/autoguardado.js:99-245` · el autoguardado **reboto**: programa el
   guardado `RETARDO_AUTOGUARDADO_MS` después de la última pulsación.
   `js/config.js:64` · ese retardo son **1.500 ms**.
3. `js/pipeline.js:386-393` · `valorDeCampo` devuelve **la edición si la hay** y
   si no lo que leyó la IA. Es lo que compone el cuerpo de `/api/archivar`
   (`js/pipeline.js:469-470`).
4. `js/app.js:703-746` · `confirmarArchivo` calcula la tanda y la lanza **sin
   mirar si queda algo sin guardar**. `autoguardado.hayPendiente`
   (`js/autoguardado.js:283`) existe y **no lo llama nadie**: `grep hayPendiente
   js/app.js` no devuelve ninguna línea.

**La ventana real del defecto**: corregir el código de obra y pulsar «archivar
y cerrar» antes de 1,5 s —o mientras la petición de guardado está en vuelo—
manda al backend un código que **no está en la base**. Hoy eso archiva con el
código corregido y deja la base con el viejo; con el nombrado persistido y sin
tocar el front, archivaría con el **viejo** y la persona creería que su
corrección se aplicó. Las dos son malas, y la segunda es peor porque es
silenciosa. Por eso esta feature **tiene** las dos mitades.

`parte.guardado` (`js/pipeline.js:450-457`) **no** cubre esto: es verdad desde
el primer guardado del parte y no caduca cuando alguien escribe encima.

### 0.4 · Lo que NO es esta feature

- **No es un fallo observado.** No hay ningún parte archivado en la carpeta
  equivocada. Es defensa en profundidad, y así se declara.
- **No toca `/api/adjuntar` ni `/api/cerrar`**, que tienen el mismo defecto de
  familia y **peor** (§8, hallazgo H-1).

## 1 · Requisitos

### 1.1 · De dónde sale el nombre (el encargo principal)

**R1.** El sistema debe componer la carpeta y el nombre del fichero de un parte
con el `codigo_obra` y el `numero_incidencia` **que constan guardados** para
ese parte, leídos de la situación que ya consultó la puerta de estado, y con
ningún otro origen.

**R2.** El sistema debe leer esos dos códigos **sin ejecutar ninguna sentencia
adicional**: salen de la consulta de situación que `POST /api/archivar` ya
hacía antes de esta feature.

**R3.** CUANDO `POST /api/archivar` recibe un `codigo_obra` o un
`numero_incidencia` distintos de los guardados, el sistema debe **no archivar
nada** y responder **409** diciendo cuál de los dos no coincide y que hay que
guardar la corrección antes de archivar.

**R4.** El sistema debe comparar lo declarado con lo guardado **después de
normalizar los dos** con el mismo criterio que F-032 (`normalizar_codigo`), de
modo que `RS 26.09/0178` y `RS26.09/0178` —o `06 26` y `0626`— **no** produzcan
un 409: son el mismo código escrito de dos maneras.

**R5.** SI el cotejo de R3 falla, ENTONCES el sistema debe abortar **antes** de
escribir la traza previa en `pendiente` y antes de llamar al puerto de archivo:
ni carpeta, ni búsqueda, ni bytes, ni fila en `postventa.archivos`.

**R6.** El sistema debe seguir respondiendo **400** —y no 409— cuando el cuerpo
no trae uno de los cinco campos obligatorios o trae un `veredicto` o un
`destino` que el dominio no conoce: una petición mal formada no es un conflicto
de estado (F-030 R19 conservado).

**R7.** SI el `codigo_obra` o el `numero_incidencia` guardados están vacíos o
ausentes, ENTONCES el sistema debe responder **409** con el error de nombrado
imposible que ya existe, diciendo **cuál** falta, y no debe sustituirlo por el
valor que traiga el cuerpo.

**R8.** SI el nombre compuesto a partir de los códigos guardados no vale para
SharePoint, ENTONCES el sistema debe seguir respondiendo **409** sin sanear
nada (F-006 R7 conservado): el camino sigue siendo alcanzable, porque
`normalizar_codigo` quita blancos pero no caracteres prohibidos.

**R9.** SI el parte no consta en `postventa.partes`, ENTONCES el sistema debe
responder **409** con el motivo «no consta que este parte haya pasado la
validación», que es el que ya da la puerta de estado, y no debe llegar a
nombrar nada. (Es el comportamiento de hoy y esta feature no lo cambia; se
escribe porque la ficha pregunta por él.)

**R10.** El sistema debe mantener obligatorios en el cuerpo `codigo_obra` y
`numero_incidencia`: dejan de **nombrar** y pasan a **cotejar**. El contrato
HTTP de `POST /api/archivar` no cambia: mismos campos, mismos 400, un 409 más.

**R11.** MIENTRAS esta feature esté en vigor, ningún valor del cuerpo de
`POST /api/archivar` debe poder decidir dónde acaba el PDF: lo declarado solo
puede **cerrar** la puerta (R3), nunca abrirla ni moverla.

### 1.2 · Lo que no se mueve

**R12.** El sistema debe conservar íntegras las cuatro reglas del nombrado
(ceros a la izquierda, sufijo literal, barra a guion y «nombre imposible es
error, nunca saneo»): esta feature cambia **de dónde salen las entradas**, no
qué se hace con ellas.

**R13.** El sistema debe conservar `domain/models/nombrado.py` como **dominio
puro**: sin reloj, sin red, sin configuración y sin conocer la persistencia.

**R14.** El sistema debe conservar las tres capas contra el duplicado de F-006
y su enmienda de F-033: L1 sigue cortando por `hash` + estado `archivado` y por
nada más, y sigue leyéndose de la situación del almacén.

**R15.** El sistema debe conservar la garantía de orden de F-019: la traza
previa en `pendiente` se escribe antes de tocar el puerto de archivo, y su
clave ajena sigue siendo lo que impide subir un parte que no conste guardado.

**R16.** El sistema debe dejar la huella del veredicto (F-026) **intacta**: ni
su criterio de normalización ni su valor cambian en esta feature.

**R17.** El sistema no debe añadir ninguna columna, tabla, vista ni sentencia a
`postventa`, ni ningún método al puerto de persistencia.

### 1.3 · El front: lo corregido está guardado antes de archivar

**R18.** CUANDO una persona pulsa el botón que archiva y cierra la tanda, el
front debe **forzar el guardado de todo lo que esté escrito y sin guardar**
—de cualquier parte, no solo del que esté abierto— y **esperar a que termine**
antes de calcular la tanda y lanzar la primera petición.

**R19.** El sistema debe calcular la tanda **después** de ese guardado forzado:
guardar revalida (`revalidarYGuardar`), y una corrección puede dejar un parte
en un estado que ya no entra en el circuito. Una tanda calculada antes
archivaría un parte que acaba de dejar de ser archivable.

**R20.** SI ese guardado forzado no sale bien, ENTONCES el front debe **no
lanzar la tanda**, dejar la pantalla como estaba y decir que hay correcciones
sin guardar, nombrando el aviso que ya existe para el fallo de autoguardado.

**R21.** El front debe dejar intacto lo que la persona escribió aunque el
guardado falle (F-026 R52 conservado): forzar el guardado no puede convertirse
en una vía para perder una corrección.

**R22.** El front no debe disparar ninguna petición de guardado cuando no haya
nada distinto de lo guardado: pulsar «archivar y cerrar» sin haber corregido
nada no puede costar una escritura por parte contra el PostgreSQL compartido.

**R23.** El front debe seguir negándose a componer el cuerpo de
`POST /api/archivar` de un parte que no conste guardado o que no conste
aprobado (F-019 R27 y F-028 R33 conservados).

**R24.** CUANDO el backend responda con el 409 de R3, el front debe pintar su
mensaje tal cual en el parte, por el camino que ya pinta los demás errores del
circuito, sin tumbar la tanda.

### 1.4 · Datos personales, logs y respuesta

**R25.** El sistema no debe escribir en ningún log, aviso o respuesta ningún
dato del papel distinto del código de obra y del número de incidencia. En
particular, el mensaje del 409 de R3 puede nombrar los dos códigos —que
identifican una obra y una reclamación, no a una persona— y **no** puede llevar
el DNI, las observaciones, la descripción, la unidad ni la promoción.

**R26.** El sistema no debe añadir ninguna clave a la respuesta de
`POST /api/archivar`: siguen siendo las seis de F-006 R30
(`hash_parte`, `nombre_fichero`, `carpeta`, `estado`, `web_url`, `avisos`).

**R27.** El sistema no debe registrar en ningún log el identificador de la
biblioteca (`drive_id`), igual que decidió F-033 R15 y R24.

### 1.5 · Verificación y rigor

**R28.** El sistema debe tener, para cada requisito de §1.1 y §1.3, al menos un
test con nombre trazable (`test_f031_rN_…` en Python, `F-031 RN · …` en los
`node --test`), y todos ellos deben correr **sin red, sin BBDD y sin IA**.

**R29.** El sistema debe cerrar el alcance con un test que compruebe que
`/api/adjuntar` y `/api/cerrar` **no** se han tocado en esta feature (H-1, §8),
igual que hizo `tests/test_f032_alcance_cerrado.py` y
`tests/test_f033_alcance_cerrado.py`.

## 2 · Trazabilidad con el `acceptance` de la ficha

| `acceptance` (`harness/features.json`) | Requisitos |
|---|---|
| «La carpeta y el nombre del fichero archivado salen del `codigo_obra` y el `numero_incidencia` persistidos, no del cuerpo» | R1, R2, R7, R12 |
| «Queda escrito qué hace el front cuando una persona corrige uno de esos dos campos, y el circuito garantiza que lo corregido está guardado antes de archivar» | §0.3, R18–R23 |
| «Un cuerpo que mienta en esos dos campos no puede cambiar dónde acaba el PDF» | R3, R4, R5, R11 |
| «`bash harness/init.sh` en verde» | T-última de `tasks.md` |

## 3 · Defectos y límites declarados

**D-1 · El cotejo no detecta una mentira coherente con la base.** Si alguien
corrompiera la fila de `postventa.partes` y mandara el cuerpo a juego, el PDF
iría a la carpeta que diga la fila. Esta feature mueve la fuente de verdad a la
base; **quién puede escribir en la base es otra pregunta** y no la responde
F-031.

**D-2 · El 409 de R3 es visible para quien llama.** Un cliente que quisiera
saber qué código hay guardado para un `hash` puede deducirlo probando. Se
acepta: el que llama es el front autenticado por Entra, los dos códigos no son
dato personal y el mensaje es lo que hace que una persona sepa qué arreglar.

**D-3 · La ventana de R18 no es cero.** Entre el guardado forzado y la primera
petición de archivo caben milisegundos en los que alguien podría teclear. No se
congela la interfaz: el backend responde 409 a esa carrera (R3), que es
exactamente para lo que está.

**D-4 · Revalidar al forzar el guardado puede encoger la tanda.** Es correcto y
deliberado (R19), pero sorprende: quien corrige un campo y pulsa archivar puede
ver que su parte ya no entra. La pantalla lo explica con el estado que devuelve
el guardado, que es el circuito que ya existe (F-028 R38).

**D-5 · `normalizar_codigo` no quita el `U+200B`.** Es el defecto D3 declarado
por F-032 y no se reabre aquí: un código guardado con un ancho cero y un cuerpo
sin él darían un 409 de R3 en vez de archivar mal, que es el lado seguro.
