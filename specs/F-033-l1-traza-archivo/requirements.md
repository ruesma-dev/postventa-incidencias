<!-- specs/F-033-l1-traza-archivo/requirements.md -->
# F-033 · La primera capa contra el duplicado en SharePoint, conectada — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f033_rN_*`, salvo los marcados **MANUAL**, que verifica
> el humano con el comando exacto de `tasks.md`.
>
> **Rigor: `critico`** (ficha). Fase RED obligatoria en los requisitos
> centrales, cobertura de las líneas cambiadas por encima del umbral y campaña
> de mutación con **cero supervivientes** sin justificación aceptada.
>
> Convención: lo medido va marcado **[MEDIDO]** con su fuente (fichero y línea
> del árbol de `dev` en `11dda9d`, 2026-09-18). Lo que no se ha podido medir
> desde aquí va **[NO MEDIDO]** y tiene su verificación manual.
>
> **Esta spec no ha escrito en ningún sistema.** Todo lo medido es lectura del
> repositorio, incluida la spec de F-013 en su rama sin mergear
> (`feature/F-013-archivo-posventa`, `8f72e66`).

## 0 · Qué está roto, medido

| Hecho | Fuente |
|---|---|
| `paso_archivo` recibe la traza anterior como argumento **opcional** `traza_previa=None` y solo con ella corta L1 | **[MEDIDO]** `application/pipelines/paso_archivo.py:97` y `:131-134` |
| `POST /api/archivar` **no** se la pasa: llama al paso sin ese argumento | **[MEDIDO]** `interface_adapters/api/archivar.py:118-131` |
| Los únicos que la pasan son tests | **[MEDIDO]** `tests/test_f006_paso_archivo.py` (4 llamadas) y `tests/test_f019_orden_archivado.py` (2) |
| `SituacionParte` trae veredicto, decisión humana, último estado y cierre; **no** la traza del archivo | **[MEDIDO]** `domain/models/estado.py:189-248` |
| El puerto no tiene `consultar_archivo` | **[MEDIDO]** `domain/ports/persistencia.py` |
| `postventa.archivos` tiene **clave primaria** `hash_parte` y se escribe con `ON CONFLICT (hash_parte) DO UPDATE` **sin `WHERE`**: cualquier escritura pisa la fila, también una en `archivado` | **[MEDIDO]** `sql/05_archivos.sql:10-23`, `sentencias.py:211-248` |
| La consulta de situación cuesta **dos** sentencias por llamada y hay tests que lo fijan | **[MEDIDO]** `repositorio_pg.py:245-326`; `tests/test_f028_persistencia.py:458` y `:1453` (`len(conexion.ejecutadas) == 2`) |

Consecuencia: **`/api/archivar` vuelve a subir siempre**. Lo que evitaba el
duplicado era L2, el reemplazo del homónimo, que solo funciona mientras el
nombre y la carpeta no cambien. Desde F-032 el nombre puede cambiar, y con
F-013 cambiará la biblioteca entera. Y cada re-archivo **pisa** `carpeta`,
`nombre_fichero`, `drive_id`, `item_id` y `web_url` de la traza: el fichero
viejo deja de ser localizable desde nuestra base.

## 1 · Alcance

**Entra**: conectar L1 en el endpoint leyendo la traza **del almacén**; que la
traza viaje dentro de la consulta de situación que ya se hace; que una traza
`archivado` no se pueda pisar; decir qué pasa cuando la traza apunta a otro
destino; y dejar escrito que el re-archivo del mismo parte no existe desde el
circuito.

**No entra**, y cada cosa tiene dueña:

| Fuera | Por qué | Dónde |
|---|---|---|
| Sacar el nombrado de lo persistido y no del cuerpo | Ficha propia; toca el front | **F-031** |
| Mudar el archivo a la biblioteca de Posventa | Ficha propia; depende de esta | **F-013** |
| Que `adjuntar` y `cerrar` lean «consta archivado» del almacén y no del cuerpo | Hallazgo de esta spec (`design.md` §9); cambia las puertas de las dos escrituras en el ERP | **Ficha nueva propuesta** (decisión abierta **D-6**) |
| Un histórico append-only de trazas de archivo | Exige DDL y no lo pide ningún caso medido | Descartado con recomendación (**D-3**) |
| Un «re-archivo forzado» del mismo parte | No hay caso que lo necesite (`design.md` §5) | Descartado con recomendación (**D-4**) |
| Cualquier DDL | No hace falta ninguna | — |

---

## 2 · La traza viaja con la situación

**R1.** `SituacionParte` debe llevar un quinto campo, `archivo: TrazaArchivo |
None`, con valor por omisión `None`, **al final** de los existentes: `None`
significa «de este parte no consta ninguna traza de archivo», y **no es un
error**.

**R2.** CUANDO se consulta la situación de un parte (`consultar_situacion`),
el adaptador de PostgreSQL debe devolver en `archivo` la traza de
`postventa.archivos` de ese `hash_parte`, con sus ocho campos
(`estado`, `nombre_fichero`, `carpeta`, `drive_id`, `item_id`, `web_url`,
`motivo`, `archivado_at_utc`), o `None` si no hay fila.

**R3.** La consulta de la situación **no debe costar ninguna sentencia más**
de las que ya costaba: **dos** por llamada, con traza de archivo y sin ella.
La traza viaja dentro de la **segunda** sentencia que ya existe
(`select_veredicto_y_cierre`), como un tercer `LEFT JOIN` anclado en
`partes`. *(Criterio de aceptación 4 de la ficha.)*

**R4.** SI no consta la ficha del parte en `postventa.partes`, ENTONCES la
situación debe traer `archivo=None` junto al veredicto `None` y al cierre
`None` que ya trae hoy, sin error de base de datos (F-030 R9 intacto).

**R5.** SI la base devuelve en `archivos.estado` un valor que
`EstadoArchivo` no conoce, ENTONCES el mapeo debe **fallar** (`ValueError`),
igual que ya hacen `EstadoParte` y `EstadoGrafico`: traducirlo «como si
fuera» otro podría leerse como `archivado` y cortar un archivo que no se ha
hecho, o como `error` y volver a subirlo.

**R6.** El log de `consultar_situacion` debe añadir **solo el estado** de la
traza de archivo (o que no hay). Nunca `drive_id`, `item_id`, `web_url` ni
`motivo` (F-006 R26: identificadores de biblioteca fuera de los logs).

## 3 · L1 se lee del almacén, nunca del llamante

**R7.** `paso_archivo` debe leer la traza para L1 de la **situación que ya
leyó la puerta de estado** (`ctx.situacion.archivo`), y de ningún otro
sitio. **No debe** aceptar la traza por parámetro: el argumento
`traza_previa` desaparece de su firma. *(Decisión abierta D-2, con
recomendación.)*

**R8.** L1 no debe costar ninguna consulta propia: la situación ya se leyó en
la puerta (`puerta_de_estado.exigir_parte_aprobado`), y el paso la reutiliza.
Un archivado que corta por L1 ejecuta exactamente las **dos** sentencias de
la situación y **ninguna escritura**.

**R9.** El orden del paso debe seguir siendo el de F-006 y F-019: puerta de
estado → nombrado → **L1** → traza previa en `pendiente` → carpeta → búsqueda
del homónimo → subida → traza final. L1 va **antes** de la traza previa
(F-019 R24): al revés, un parte archivado quedaría degradado a `pendiente`.

**R10.** MIENTRAS la situación traiga una traza de **este** `hash_parte` en
estado `archivado`, el sistema no debe volver a subir el parte: ni carpeta, ni
búsqueda, ni subida, ni ninguna escritura en `postventa.archivos`; debe
devolver **la traza guardada tal cual** (su carpeta, su nombre, su `web_url`)
con el aviso `AVISO_YA_ARCHIVADO`. *(F-006 R14, ahora de verdad; criterio de
aceptación 1 de la ficha.)*

**R11.** SI la traza guardada está en `pendiente` o en `error`, ENTONCES L1
**no** debe cortar: el parte se reintenta (F-006 R14 y R24, F-019 R24,
intactos).

**R12.** CUANDO se llama a `POST /api/archivar` con un parte que ya consta
`archivado`, el endpoint debe responder **200** con el contrato de siempre
(`hash_parte`, `nombre_fichero`, `carpeta`, `estado`, `web_url`, `avisos`;
ni una clave más), con los valores **de la traza guardada** y `estado`
`archivado`, sin haber llamado al archivador. *(Criterio de aceptación 3: se
comprueba desde el endpoint.)*

## 4 · La traza apunta a otro destino

**R13.** L1 debe cortar **por `hash_parte` y estado, y por nada más**: una
traza `archivado` corta aunque su `carpeta`, su `nombre_fichero` o su
`drive_id` no coincidan con el destino que se compondría hoy. «El mismo
parte» es el `hash` (F-006 R13); el destino es dónde está, no quién es.
*(Decisión abierta D-1, con recomendación.)*

**R14.** CUANDO L1 corta y la traza guardada **no coincide** con el destino
de hoy —otro `nombre_fichero`, otra `carpeta`, u otro `drive_id` distinto del
de la configuración vigente, cuando los dos se conocen—, el sistema debe
añadir además el aviso `AVISO_ARCHIVADO_EN_OTRO_DESTINO`, que dice que el
parte **sigue donde se archivó**, que **no** se ha subido al destino actual y
que la ruta que devuelve la respuesta es la de entonces. El aviso no lleva
identificadores de biblioteca.

**R15.** Para la comparación de R14 con la biblioteca, `archivar.py` debe
pasar al paso el `drive_id` de la configuración vigente
(`SHAREPOINT_DRIVE_ID`). SI no hay `drive_id` configurado o la traza no lo
lleva, ENTONCES la comparación de biblioteca se omite y solo se comparan
carpeta y nombre. El `drive_id` **no** aparece en ningún log, aviso ni
respuesta.

**R16.** El sistema no debe mover, copiar, borrar ni renombrar nada en
SharePoint en ningún caso de esta feature. Lo archivado en un destino
anterior **se queda donde está** y localizable por su traza (F-013 H4).

## 5 · La traza de un fichero subido no se pisa

**R17.** La escritura de la traza de archivo (`upsert_archivo`) **no debe
actualizar una fila que ya esté en `archivado`**: el `DO UPDATE` lleva
`WHERE <tabla>.estado <> %s` con `archivado` como **parámetro**, y en ese caso
la sentencia no devuelve fila y el repositorio responde `SIN_CAMBIOS`. Es el
mismo patrón que `cierres` (`cerrado`) y `graficos` (`adjuntado`). *(Criterio
de aceptación 2; decisión abierta D-3, con recomendación.)*

**R18.** SI la escritura de la traza previa en `pendiente` devuelve
`SIN_CAMBIOS` —otra petición archivó el mismo parte entre la consulta de la
situación y esta escritura—, ENTONCES el paso **no debe subir nada**: debe
volver a leer la situación **una vez**, devolver la traza `archivado` que
consta con `AVISO_YA_ARCHIVADO` y terminar. Es la única lectura adicional de
esta feature y solo ocurre en esa carrera. *(Decisión abierta D-7.)*

**R19.** SI la traza final (o la de error) devuelve `SIN_CAMBIOS`, ENTONCES el
paso no debe tratarlo como fallo: lo registra en el log (hash y resultado) y
responde con lo que subió. *(Solo es alcanzable en una carrera entre dos
peticiones del mismo parte; riesgo residual en `design.md` §8.)*

**R20.** CUANDO L1 **no** corta porque la traza guardada está en `pendiente`
y su `carpeta` o su `nombre_fichero` difieren del destino de hoy, el sistema
debe seguir archivando, pero antes debe dejar **aviso**
(`AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA`, con la carpeta y el nombre del intento
anterior) y **una línea de log** con el `hash`, la carpeta y el nombre
anteriores. Una traza en `pendiente` puede ser un fichero **subido sin traza
final** (`ArchivoSinTraza`), y la traza previa que se va a escribir la pisa:
el aviso y el log son el rastro que queda. *(Decisión abierta D-5.)*

**R21.** El sistema no debe exponer por ninguna vía de este servicio un modo
de volver a subir un parte cuya traza consta `archivado`: ni parámetro del
paso, ni campo del cuerpo, ni cabecera. *(Decisión abierta D-4.)* Un
**escaneo nuevo** del mismo papel es otro parte —otro `hash`— y se archiva
por el camino normal, con L2 avisando del reemplazo del homónimo (F-006 R16).

## 6 · Lo que no cambia

**R22.** El sistema debe conservar todas las garantías de F-006, F-019, F-028
y F-030 que no son L1: puerta de estado leída del almacén, «no hay veredicto»
como motivo propio y primero, `ReferenciaNoConsta` → 409 antes de tocar
SharePoint, `ArchivoSinTraza` → 500, reemplazo del homónimo con aviso,
creación de carpeta idempotente. Sus tests siguen en verde; los únicos que
cambian son los que pasaban `traza_previa` o fijaban la forma exacta de la
consulta, y cambian **sin aflojar ningún aserto** (`design.md` §7).

**R23.** El contrato HTTP de `POST /api/archivar` no cambia: mismos campos de
entrada, mismas seis claves de salida, mismos códigos de estado. Lo nuevo son
dos textos posibles dentro de `avisos`.

**R24.** Ni el DNI, ni las observaciones, ni el contenido del PDF, ni
`drive_id`, `item_id` o `web_url` deben aparecer en ningún log nuevo de esta
feature. El `web_url` sí viaja en la respuesta, como hoy (F-006 R30).

**R25.** `docs/ARCHITECTURE.md` (paso 6, las tres capas) debe llevar una
precisión fechada de F-033 que diga que L1 lee la traza de la situación, que
`archivado` no se pisa y que el re-archivo del mismo parte no existe desde el
circuito, **sin borrar** el texto anterior.

## 7 · Verificaciones manuales (humano)

**R26. MANUAL · antes de desplegar.** Consulta de **solo lectura** sobre el
schema `postventa`: recuento de trazas por estado y la lista de las que están
en `pendiente` (posibles ficheros subidos sin traza final). Resultado anotado
en `progress/`, sin identificadores de biblioteca. Comando en `tasks.md` T13.

**R27. MANUAL · después de desplegar.** Con autorización expresa del humano
para ese parte y con la ventana `ARCHIVO_HABILITADO` abierta solo para ello:
volver a archivar un parte que ya consta `archivado`, y comprobar (a) que la
respuesta trae `AVISO_YA_ARCHIVADO`, (b) que en la biblioteca no cambia nada
—misma fecha de modificación del fichero— y (c) que la fila de
`postventa.archivos` no cambia —mismo `intentos`—. Comando en `tasks.md` T14.

---

## 8 · Decisiones abiertas (las valida el humano antes de implementar)

El detalle y las alternativas están en `design.md` §10. Resumen:

| Id | Pregunta | Recomendación |
|---|---|---|
| **D-1** | Traza `archivado` que apunta a **otro destino** (otro nombre, carpeta o biblioteca) | **Cortar siempre** por `hash` + estado, con aviso propio (R13–R15). Es lo que necesita F-013: lo de IT se queda en IT |
| **D-2** | ¿Se quita `traza_previa` del paso? | **Sí** (R7): dos fuentes para la misma decisión divergen, y la del parámetro es la que dejó L1 inerte. Los tests migran a sembrar la situación |
| **D-3** | ¿Cómo no se pierde el rastro: no pisar, o histórico append-only? | **No pisar**: `archivado` terminal en el `upsert` (R17), sin DDL, como `cierres` y `graficos`. El histórico append-only queda descartado mientras no haya un caso que lo pida |
| **D-4** | ¿Sigue siendo posible el re-archivo deliberado del mismo parte? | **No desde el circuito** (R21). Un escaneo nuevo es otro parte; mover lo archivado lo hace una persona en SharePoint. Si aparece un caso real, ficha propia |
| **D-5** | Traza `pendiente` con otra ruta (posible subida huérfana) | **Seguir, con aviso y log** (R20) |
| **D-6** | Hallazgo: `adjuntar` y `cerrar` reciben «consta archivado» **del cuerpo**, y el front lo manda fijo | **Ficha nueva**, inmediatamente después de esta; F-033 deja el dato en la situación para que sea poca cosa |
| **D-7** | Carrera en la traza previa (`SIN_CAMBIOS`) | **Releer una vez y cortar** (R18) |
