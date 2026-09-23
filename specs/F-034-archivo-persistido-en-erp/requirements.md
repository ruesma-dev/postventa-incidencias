<!-- specs/F-034-archivo-persistido-en-erp/requirements.md -->
# F-034 · Adjuntar y cerrar se fían del cuerpo — Requisitos

> Notación EARS (`specs/SPECS.md`). Rigor **`critico`** (`harness/features.json`):
> es la única ficha de la familia cuyo defecto termina **escribiendo en el ERP
> de producción**. Lo que está en juego no es en qué carpeta acaba un PDF, sino
> **qué reclamación se cierra**.
>
> Servicios afectados: `services/postventa-api/` (backend) y, en **un solo
> punto**, `services/postventa-front/` (§1.5). §6 razona por qué eso no parte el
> límite de microservicio.
>
> **Esta spec no ha escrito en ningún sistema.** Todo lo que declara como
> medido sale de leer el árbol del repositorio en `dev`, commit `127e457`, y de
> leer la rama `feature/F-031-nombrado-persistido` con `git show`. No se ha
> tocado Sigrid, SharePoint, Azure ni PostgreSQL.
>
> **Orden decidido por el humano**: F-033 → F-031 → **F-034** → F-013.

## 0 · El defecto, medido

Todo lo de esta sección está **[MEDIDO]** sobre `dev`, commit `127e457`.

### 0.1 · Mitad A · el estado del archivo sale del cuerpo (D-6 de F-033)

| Quién decide | Con qué dato | Fichero y línea |
|---|---|---|
| La puerta de aptitud (¿está aprobado?) | La situación **del almacén** | `paso_grafico.py:148` y `paso_cierre.py:152` → `puerta_de_estado.py:145` |
| **La puerta de archivo** (¿consta archivado?) | `ctx.archivo`, que **lo fabrica el borde con el cuerpo** | `paso_grafico.py:149, 282-295` y `paso_cierre.py:153, 240-255`, alimentados por `adjuntar.py:262-265` y `cerrar.py:235-238` |
| Quién manda ese valor | El front, **fijo** | `js/pipeline.js:631` (`cuerpo.append("estado_archivo", ESTADO_ARCHIVADO)`) y `js/pipeline.js:540` (`estado_archivo: ESTADO_ARCHIVADO`) |

`ESTADO_ARCHIVADO` es una constante literal (`js/pipeline.js:158`). No sale de
ninguna lectura: es una **afirmación** del cliente.

**Consecuencia**: detrás de la puerta del gráfico no hay ninguna otra que mire
el archivo de verdad. Un parte aprobado pero **sin archivar** —o con su archivo
en `pendiente` o en `error`— se adjuntaría al ERP de producción y se cerraría,
con solo mandar la cadena `archivado` en el formulario. Y el procedimiento de
Posventa que sostiene todo el riesgo aceptado de F-009 §2 es exactamente el
contrario: **primero el documento, después el ERP**.

### 0.2 · Mitad B · los dos códigos salen del cuerpo (H-1 de F-031)

| Qué se decide con ellos | Dónde | Fuente **[MEDIDO]** |
|---|---|---|
| **El nombre del fichero** que se cuelga de la reclamación | `paso_grafico.py:175-176` → `componer_peticion` (`domain/models/grafico.py:279-319`) → `nombre_de_archivo` | Llegan de `adjuntar.py:172-173`, que los toma del formulario (`adjuntar.py:107-108`) |
| **Qué reclamación recibe el gráfico** | `paso_grafico.py:157` (`_codigo_de_incidencia`) → `erp.leer_reclamacion` (`:162`) | ídem |
| **Qué reclamación se cierra en el ERP de producción** | `paso_cierre.py:155` → `_dry_run` → el `UPDATE` de `con.est` | Llega de `cerrar.py:149`, que lo toma del cuerpo (`cerrar.py:100`) |

El front los compone con el mismo `valorDeCampo` que F-031 midió
(`js/pipeline.js:386-393`, usado en `:624-627` y `:537`): la corrección de la
persona si la hay, y si no lo que leyó la IA.

**Esta mitad es más grave que la de F-031.** Allí un cuerpo que mintiera movía
un PDF de carpeta; aquí **cierra otra reclamación**, y un cierre en Sigrid no
se deshace desde este circuito.

### 0.3 · El dato correcto ya está delante, y no cuesta nada

La puerta de aptitud es **lo primero** que hace cada uno de los dos pasos
(`paso_grafico.py:148`, `paso_cierre.py:152`) y deja en `ctx.situacion`
(`puerta_de_estado.py:145`) una `SituacionParte` que **desde F-033 trae las
cinco cosas**, todas de la misma consulta:

- `validacion.codigo_obra` y `validacion.numero_incidencia` —los **guardados**,
  de `postventa.partes`— porque F-030 los necesitaba para recomponer la huella:
  `sentencias.py:578-582` y `:626-628`; `domain/models/validacion.py:178-179`;
- `archivo` —la `TrazaArchivo` de `postventa.archivos`— porque F-033 la trajo
  para L1: `sentencias.py:608-624`; `domain/models/estado.py`, campo `archivo`
  de `SituacionParte`.

**Ninguna de las dos cuesta una sentencia más**: son columnas de la consulta
que las dos puertas ya ejecutan. Como en F-031 y al revés que en F-033, esta
feature **no añade ni una columna, ni un `JOIN`, ni un método al puerto, ni un
`NN_nombre.sql`**.

### 0.4 · Qué NO es esta feature

- **No es un fallo observado.** No consta ningún parte adjuntado o cerrado con
  un código que no fuera el suyo. Es defensa en profundidad — y la de más
  valor, porque es la última antes del ERP.
- **No toca `/api/archivar`** más allá de un `import` (§3 del diseño): ese es
  el terreno de F-031, que ya está implementado y aprobado.
- **No cambia el contrato HTTP** de ninguno de los dos endpoints (R18).

## 1 · Requisitos

### 1.1 · Mitad A · el archivo, desde lo persistido

**R1.** El sistema debe decidir si un parte consta archivado, en
`POST /api/adjuntar` y en `POST /api/cerrar`, con la **traza que consta en
`postventa.archivos`** —la que viaja en `ctx.situacion.archivo`— y con ningún
otro origen.

**R2.** El sistema debe leer esa traza **sin ejecutar ninguna sentencia
adicional**: sale de la consulta de situación que las dos puertas de aptitud ya
hacían antes de esta feature.

**R3.** SI el cuerpo declara `estado_archivo=archivado` y la traza persistida
no existe o no está en `archivado`, ENTONCES el sistema debe **no escribir nada
en el ERP** —ni gráfico, ni cierre, ni traza— y responder **409** con el motivo
de `ParteNoArchivado` que ya existe, nombrando el estado **persistido**.

**R4.** El sistema debe dejar de construir `ctx.archivo` desde el cuerpo en los
dos endpoints: `adjuntar._como_contexto` y `cerrar._como_contexto` no deben
fabricar ninguna `TrazaArchivo`. La segunda fuente desaparece, no se tapa.

**R5.** MIENTRAS esta feature esté en vigor, ningún valor del cuerpo de
`POST /api/adjuntar` ni de `POST /api/cerrar` debe poder **abrir** la puerta de
archivo.

**R6.** El sistema debe mantener `estado_archivo` obligatorio en el cuerpo y
seguir validándolo contra `EstadoArchivo` —un valor desconocido sigue siendo
**400**—: el contrato HTTP no cambia (R18). Lo que cambia es que **deja de
decidir**, y el docstring de los dos módulos lo dice con la enmienda fechada
que ya usan F-030 y F-033.

**R7.** CUANDO la traza persistida diga `archivado` y el cuerpo declare otra
cosa, el sistema debe **seguir adelante**: manda lo guardado, y ahí no hay
conflicto que resolver. Un 409 en ese caso sería un error nuevo sin ninguna
escritura que evitar.

### 1.2 · Mitad B · los dos códigos, desde lo persistido

**R8.** `POST /api/adjuntar` debe **nombrar el fichero** que cuelga de la
reclamación y **localizar la reclamación** con el `codigo_obra` y el
`numero_incidencia` **que constan guardados** para ese parte, leídos de la
situación que la puerta acaba de consultar.

**R9.** `POST /api/cerrar` debe **elegir la reclamación que cierra** con el
`numero_incidencia` **que consta guardado**, y con ningún otro origen.

**R10.** El sistema debe leer esos códigos **sin ejecutar ninguna sentencia
adicional** (mismo argumento que R2).

**R11.** CUANDO el cuerpo de cualquiera de los dos endpoints declare un código
distinto del guardado, el sistema debe **no escribir nada en el ERP** y
responder **409** diciendo cuál de los dos no coincide y que hay que guardar la
corrección antes de volver a intentarlo.

**R12.** El sistema debe comparar lo declarado con lo guardado **después de
normalizar los dos** con el mismo criterio de F-032 (`normalizar_codigo`, vía
`es_el_mismo_codigo` de F-031), de modo que `RS 26.09/0178` y `RS26.09/0178`
—o `06 26` y `0626`— **no** produzcan un 409.

**R13.** SI el cotejo de R11 falla, ENTONCES el sistema debe abortar **antes**
de tocar nada más: antes de resolver el login contra el ERP, antes de leer
ninguna reclamación, antes de escribir ninguna traza de gráfico o de cierre y,
por supuesto, antes de cualquier escritura con `commit`.

**R14.** El cotejo de R11 debe aplicarse **también con `commit=false`**: el
dry-run existe para enseñar lo que va a pasar, y enseñar la reclamación que
nombra un cuerpo que miente es enseñar otra cosa.

**R15.** SI el `numero_incidencia` guardado —o, en `POST /api/adjuntar`, el
`codigo_obra` guardado— está vacío o ausente, ENTONCES el sistema debe
responder **409** diciendo **cuál** falta y que hay que teclearlo y guardarlo,
y **no** debe sustituirlo por el valor que traiga el cuerpo. En particular, no
debe responder 400: la petición está bien formada y lo que está incompleto es
lo guardado.

**R16.** El sistema debe cotejar en `POST /api/adjuntar` **los dos** códigos y
en `POST /api/cerrar` **solo el número de incidencia**: el cuerpo de `/cerrar`
no trae `codigo_obra` (`cerrar.py:98-105`) y esta feature no lo añade.

**R17.** El sistema debe seguir respondiendo **400** —y no 409— cuando el
cuerpo no trae uno de sus campos obligatorios, cuando el fichero falta en
`/adjuntar`, o cuando el `veredicto`, el `destino` o el `estado_archivo` no son
valores que el dominio conozca. Una petición mal formada no es un conflicto de
estado (F-030 R19 conservado).

**R18.** El sistema no debe cambiar el contrato HTTP de ninguno de los dos
endpoints: mismos campos obligatorios, mismos 400, mismas claves en la
respuesta, **un 409 más** por endpoint. `codigo_obra`, `numero_incidencia` y
`estado_archivo` dejan de **decidir** y pasan a **cotejar** (los dos primeros) o
a no decidir nada (el tercero).

**R19.** MIENTRAS esta feature esté en vigor, ningún valor del cuerpo debe
poder cambiar **qué reclamación se cierra**, **a qué reclamación se adjunta el
parte** ni **con qué nombre se cuelga**: lo declarado solo puede **cerrar** la
puerta (R11), nunca abrirla ni moverla.

### 1.3 · Lo que no se mueve

**R20.** El sistema debe conservar intacta la puerta de aptitud de F-028 y
F-030 (`exigir_parte_aprobado`): ni su criterio, ni su orden de precedencia de
motivos, ni el hecho de que lea siempre y del almacén.

**R21.** El sistema debe conservar las **tres capas de idempotencia** de F-012
y el orden de los pasos de `paso_grafico` y de `paso_cierre`, con una sola
intercalación: el cotejo de los códigos, inmediatamente después de la puerta de
aptitud.

**R22.** El sistema debe conservar `_exigir_adjuntado` (F-012 R2) leyendo la
traza propia de `postventa.graficos`, y `ctx.traza_grafico` leyéndose del
repositorio y nunca del cuerpo.

**R23.** El sistema no debe añadir ninguna columna, tabla, vista, sentencia ni
fichero de DDL a `postventa`, ni ningún método a `RepositorioPartesPort`.

**R24.** El sistema debe conservar íntegras las cuatro reglas de
`domain/models/nombrado.py` y los tres topes de `componer_peticion`, y debe
dejar `NombradoImposible` **alcanzable** desde `/api/adjuntar` para el caso que
le queda: un código **guardado** con un carácter que SharePoint no admite
(F-006 R7 y F-031 R8 conservados; no se sanea nada).

**R25.** El sistema no debe tocar el veredicto, su huella (F-026, F-030) ni
`domain/models/aprobacion.py`.

**R26.** El sistema no debe cambiar el comportamiento de `POST /api/archivar`
ni de `paso_archivo`: si extrae a un módulo compartido piezas que F-031 dejó
allí, lo hace **sin cambiar ni una regla**, y los tests de F-031 y de F-006
quedan en verde sin tocarles el contenido.

> **Enmienda del 2026-09-23 (T3), aprobada por el humano ese día** («si» a la
> opción (a) y al §2.5 de `progress/impl_F-034.md`). «Sin tocarles el
> contenido» no era cumplible: `test_f031_alcance_cerrado.py` tiene un control
> que **no** depende de `git`
> (`test_f031_r29_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature`) y
> fija en qué ficheros viven `CodigosDelParte`, `codigos_declarados`,
> `es_el_mismo_codigo`, `CodigosNoCoinciden` y los dos privados de F-031; y
> `test_f031_nombrado_persistido.py` importaba el privado `_codigos_guardados`.
> Crear el módulo compartido de D-2 ya lo ponía rojo (sonda real en el
> informe). Queda así: de esos dos ficheros se tocan **solo** la tabla
> `NOMBRES_NUEVOS_Y_DONDE_VIVEN` con su comentario (enmienda fechada) y **solo
> el `import`** de `_codigos_guardados`; las filas que añadan los Bloques 2 y 3
> las ajusta cada tarea, y el control lo hereda `test_f034_alcance_cerrado.py`
> (T13). El resto de los tests de F-031 y F-006, sin tocar. **Ninguna regla
> cambia**, y el mensaje de `POST /api/archivar` es byte a byte el de F-031
> (lo vigila `test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031`).

### 1.4 · Los errores nuevos y su código HTTP

**R27.** El sistema debe traducir el conflicto de códigos a **409** en los dos
endpoints, con el mismo formato de respuesta que sus hermanas
(`{"error": <motivo>}`), sin ninguna clave nueva y sin ningún código HTTP
nuevo.

**R28.** El sistema debe distinguir, con **errores propios y docstring que lo
diga**, tres hechos que hoy se confundirían: «lo declarado no es lo guardado»
(R11), «lo guardado está incompleto» (R15) y «el parte no consta archivado»
(R3). Cada uno se arregla de una forma distinta, y quien lee el error es quien
va a arreglarlo.

### 1.5 · El front: lo corregido está guardado antes de escribir en el ERP

**R29.** CUANDO una persona pulse el botón que **reintenta el cierre** de un
parte (`js/app.js::reintentarCierre`), el front debe forzar el guardado de todo
lo que esté escrito y sin guardar —`vaciarPendientes()` de F-031— y **esperar a
que termine** antes de lanzar el circuito. Es el **único** camino del front que
llega a `/api/adjuntar` o a `/api/cerrar` sin pasar por el vaciado que F-031
puso en `confirmarArchivo`.

**R30.** SI ese vaciado no sale bien, ENTONCES el front debe **no lanzar nada**,
dejar la pantalla como estaba y decir que hay correcciones sin guardar, con el
mismo aviso que F-031 ya usa.

**R31.** El front no debe cambiar el cuerpo de `POST /api/adjuntar` ni el de
`POST /api/cerrar`: siguen viajando los mismos campos, con los mismos valores y
compuestos igual (R18).

**R32.** CUANDO el backend responda uno de los 409 nuevos, el front debe
pintarlo en el parte por el camino que ya pinta los errores del circuito
(`anotarFallo`), **sin tumbar la tanda**.

**R33.** El front debe dejar intacto lo que la persona escribió aunque el
guardado falle (F-026 R52 y F-031 R21 conservados), y no debe disparar ninguna
petición de guardado cuando no haya nada distinto de lo guardado (F-031 R22
conservado).

### 1.6 · Datos personales, logs y respuesta

**R34.** El sistema no debe escribir en ningún log, aviso o respuesta ningún
dato del papel distinto del código de obra y del número de incidencia. El
motivo de los 409 nuevos puede nombrar los dos códigos —identifican una obra y
una reclamación, no a una persona— y **no** puede llevar el DNI, las
observaciones, la descripción, la unidad ni la promoción.

**R35.** El sistema no debe añadir ninguna clave a las respuestas de
`POST /api/adjuntar` (las ocho de F-012) ni de `POST /api/cerrar` (las seis de
F-009).

**R36.** El sistema debe conservar la regla de log de los dos endpoints: al log
va el **tipo** del error y nunca el motivo, porque puede nombrar el correo del
usuario (F-012 R54, F-009 R45); y nunca el `gra_cod`, ni el login, ni el `oid`.

### 1.7 · Verificación y rigor

**R37.** El sistema debe tener, para cada requisito de §1.1, §1.2 y §1.5, al
menos un test con nombre trazable (`test_f034_rN_…` en Python, `F-034 RN · …`
en los `node --test`), y todos deben correr **sin red, sin BBDD, sin IA y sin
tocar el ERP**.

**R38.** El sistema debe tener un test que **cuente** las llamadas a
`consultar_situacion` en cada uno de los dos pasos y exija que sean las mismas
que antes de la feature (R2, R10).

**R39.** El sistema debe cerrar el alcance con un test que compruebe que no se
han tocado la persistencia (`sentencias.py`, `mapeo.py`, `repositorio_pg.py`),
`domain/ports/persistencia.py`, `domain/models/estado.py` ni ningún fichero de
`infrastructure/persistencia/sql/`, igual que hicieron F-032, F-033 y F-031.

## 2 · Trazabilidad con el `acceptance` de la ficha

| `acceptance` (`harness/features.json`) | Requisitos |
|---|---|
| «Adjuntar y cerrar deciden si el parte consta archivado con la traza persistida en `postventa.archivos`, no con el cuerpo» | R1, R2, R4, R5, R6, R7 |
| «Adjuntar y cerrar toman el `codigo_obra` y el `numero_incidencia` PERSISTIDOS… es lo que decide QUÉ RECLAMACIÓN se cierra» | R8, R9, R10, R15, R16, R19, R24 |
| «Un cuerpo que difiera de lo guardado en esos dos campos no escribe en el ERP: mismo criterio que F-031 (409), con test por los dos endpoints» | R11, R12, R13, R14, R27, R28, R37 |
| «Un cuerpo que diga archivado sobre un parte sin archivar no llega al ERP: hay test que recorre `/api/adjuntar` y `/api/cerrar`» | R3, R5, R37 |
| «La consulta de la situación no cuesta ninguna sentencia más de las que ya costaba» | R2, R10, R23, R38 |
| «`bash harness/init.sh` en verde» | T-última de `tasks.md` |

## 3 · Defectos y límites declarados

**D-1 · El cotejo no detecta una mentira coherente con la base.** Si alguien
corrompiera la fila de `postventa.partes` y mandara el cuerpo a juego, se
cerraría la reclamación que diga la fila. Esta feature mueve la fuente de
verdad a la base; **quién puede escribir en la base es otra pregunta** y no la
responde F-034. Es el mismo D-1 que declaró F-031.

**D-2 · Los 409 nuevos son visibles para quien llama.** Un cliente podría
deducir por prueba y error qué código hay guardado para un `hash`. Se acepta
por lo mismo que lo aceptó F-031: quien llama es el front autenticado por
Entra, los dos códigos no son dato personal, y el mensaje es lo que hace que
una persona sepa qué arreglar.

**D-3 · Esta feature no arregla un parte ya mal cerrado.** Si algún día se
cerró la reclamación equivocada, F-034 no lo detecta ni lo deshace: un cierre
en el ERP es un hecho, y `cerrado` es terminal (F-028 R7). Lo que hace es que
no vuelva a poder ocurrir por esta vía.

**D-4 · El parte «archivado en otra biblioteca» no se distingue aquí.** La
traza persistida dice `archivado` y en qué `drive_id`, pero F-034 **solo mira
el estado**, igual que hacía la puerta de hoy. Cotejar además la biblioteca es
terreno de F-013 y se deja escrito para ella; abrirlo aquí mezclaría dos
fichas.

**D-5 · `normalizar_codigo` no quita el `U+200B`.** Es el defecto D3 que
declaró F-032 y no se reabre: un código guardado con un ancho cero y un cuerpo
sin él darían un 409 de R11 en vez de escribir en la reclamación equivocada,
que es el lado seguro.

**D-6 · Con `CIERRE_HABILITADO` apagado, los 409 nuevos son inalcanzables.**
**[MEDIDO]**: `adjuntar.py:163-167` y `cerrar.py:141-144` construyen los
adaptadores **como argumentos** de la llamada al paso, así que
`construir_erp(ajustes)` —y su `exigir_interruptor_de_cierre`
(`infrastructure/sigrid/fabrica.py:87, 127`)— se evalúa **antes** de que el
paso empiece. En local, con el interruptor apagado, la respuesta es **503** y
no se llega a ninguna puerta. Consecuencia para `tasks.md`: la verificación del
409 se hace con los puertos **inyectados** (que es la costura de test que los
dos handlers declaran), no con `func start`.

**D-7 · La ventana del ERP y el vaciado del front no se solapan.** El corte por
`erpCerrado` del circuito (`js/pipeline.js:1161-1165`) va **después** del paso
de archivo y antes de los dos del ERP; el vaciado de R29 va **antes** de todo.
Ni se estorban ni se duplican.
