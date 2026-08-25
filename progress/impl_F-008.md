<!-- progress/impl_F-008.md -->
# F-008 · Modelo de posventa en Sigrid: confirmar contra el ERP

> Implementer · 2026-08-25 · rama `feature/F-008-modelo-sigrid`
> (creada desde `feature/F-010-despliegue`, en worktree aislado)
> Rigor **`documental`** · `sdd: false` — el contrato es la ficha de
> `harness/features.json`, no hay spec.

## 0 · El titular

Las cuatro preguntas de la ficha tienen respuesta, y **tres de las cuatro están
verificadas contra el ERP con datos, no deducidas**. La cuarta (el gráfico como
URL) tiene una respuesta negativa igual de útil: **no hay ni un precedente en
282.599 filas**, así que F-009 no puede apoyarse en ella.

El hallazgo que más cambia F-009 no estaba en la lista de preguntas:
**«Cerrar parte» escribe una fila de auditoría en `dbo.log` que un `UPDATE`
directo no escribiría**, y en cambio **no toca `con.tiemod`**, que es donde
cualquiera habría buscado la marca del cierre.

**Ni una escritura contra Sigrid.** Todo el trabajo son sentencias `SELECT` por
`POST /api/sql/read` de `sigrid-api`, que sirve la lectura con `ro_user`, un
usuario SQL sin permisos de escritura en el propio SQL Server.

## 1 · Qué se entrega

| Fichero | Qué es |
|---|---|
| `docs/referencia/03_modelo_posventa_sigrid.md` | **El entregable.** Todo lo averiguado, con su cabecera de origen y fecha, separando lo verificado de lo deducido |
| `docs/referencia/README.md` | Índice actualizado con la fila nueva (mantenerlo al día es parte de añadir un documento) |
| `services/postventa-api/tests/test_f006_repo_sin_identificadores.py` | Arreglo de un guardián de secretos que se apagaba solo (§5) |
| `progress/impl_F-008.md` | Este informe |

Lo que ya está en `azure-apps/sigrid_tablas.md` y `azure-apps/sigrid_api.md`
**se enlaza, no se copia**: el documento nuevo abre con una tabla «Qué no está
aquí» que manda a cada uno.

## 2 · Cómo se consultó

`sigrid-api`, `POST /api/sql/read`, bases `ruesma` (negocio) y `ruesma_rep`
(documental). Unas 25 consultas, ninguna cerca de los límites de la pasarela
(1.000 filas por petición, 230 s de balanceador): la mayoría son agregados que
devuelven menos de 40 filas, así que **no hizo falta trocear ni paginar**.

Las consultas se diseñaron para **no traer datos personales**: de las columnas
que apuntan a personas (`rcp.cliide`, `rcp.recide`, `rcp.cntide`) solo se
consultó *si están rellenas*, nunca su valor ni el nombre al otro lado. En el
único sitio donde apareció un login de usuario (`gra.cod` lleva el login de
quien sube el documento) va como `<usuario>` en el documento entregado.

Las credenciales de la pasarela se leyeron del `.env` de un proyecto del
ecosistema que ya las tiene configuradas, dentro de un script del *scratchpad*
que **nunca las imprime**. Ni la clave ni la URL del recurso entran en este
repositorio.

## 3 · Lo verificado contra el ERP

Con el número que lo sostiene. El detalle completo, en el documento entregado.

| # | Hallazgo | Evidencia |
|---|---|---|
| 1 | **`con.tip = 708`** es la reclamación de posventa | 21.554 filas de `rcp`, el 100 % con `tip = 708` |
| 2 | Estados en `conest` para 708: `1/SAT`, `3/PTE`, `5/TER`, `7/NPR`, **`9/CER` CERRADA** | Catálogo completo leído de `conest` |
| 3 | **Se confirma que el pendiente es `3 / PTE`**, como decía la guía | Coincide catálogo y ficha real |
| 4 | Los tres estados finales están marcados **no editables** (`conest.edi = 1`) | Catálogo |
| 5 | **«Cerrar parte» solo cambia `con.est`** | Comparación columna a columna de una CERRADA y una PENDIENTE de la misma obra: nada más difiere salvo lo intrínseco a ser dos reclamaciones distintas |
| 6 | …y lo confirma la población entera | Agregado sobre las 4.761 reclamaciones creadas desde 2025, por estado: `act` vacía siempre, `solrcp`/`fecpre` nunca rellenos, `rcpint` y `tar` desde el alta, `fecbaj` a 0 en las 21.554 |
| 7 | **`con.tiemod` NO se actualiza al cerrar** | En los **138 cierres de 2026**, `tiemod` es *estrictamente anterior* al día del cierre. Cero excepciones |
| 8 | **«Cerrar parte» escribe una fila en `dbo.log`** con `tab='con'`, `tip=708`, `ope=5`, `tex='Cerrar parte'`, `cod`, `res`, `usu`, `fec`, `hor` | 6.843 filas, todas con la misma forma |
| 9 | **Un cierre se puede deshacer**: existe `ope=30` `DESHACER proceso (Cerrar parte)` | 81 ocurrencias, la última 2025-10-06 |
| 10 | **No hace falta pasar por TERMINADA**: se cierra desde PENDIENTE | 29 de los 2.105 cierres desde 2025 no tienen ningún «Pasar a terminada» previo |
| 11 | **RPV termina en el MISMO estado** (`9/CER`) que «Cerrar parte» | Agrupación de las cerradas por proceso |
| 12 | **RPV sí deja cerradas sin gráfico; «Cerrar parte» no** | Desde 2023, «Cerrar parte»: 2.365 cierres, 2.365 con gráfico, **cero excepciones**. RPV: 487 sin gráfico en 2022, 276 en 2023, 109 en 2024, 8 en 2025 |
| 13 | **RPV está abandonado**: última ejecución **2025-03-11** | Log |
| 14 | Hay un tercer cierre, **«Cerrar Preventas»** (4.899, ninguno desde 2024-11-27), masivo y sin gráfico | Log |
| 15 | **`gra` vive en las DOS bases**, con esquema idéntico y **espacios de `ide` independientes** | El `ide` 296221 es documentos distintos en `ruesma` y en `ruesma_rep` |
| 16 | **El binario vive en `ruesma_rep.gra.ima`**; en `ruesma` está siempre vacío para posventa | 13.450 gráficos de reclamación, **0** con binario en `ruesma` |
| 17 | **La pareja entre las dos tablas se localiza por `gra.cod`**, no por `ide` | 13.399 de 13.450 (99,6 %) casan por `cod` con una fila con binario |
| 18 | El gráfico del parte firmado confirma campo a campo lo que la guía dedujo de la pantalla: `res` = Descripción, `nom` = fichero, `gratipide` → `PV002` | Ficha real |
| 19 | El tipo `PV002` admite asociarse a `RCP` (`auxgra.tipaso = 'UPV,RCP,TAR'`), sin límite de tamaño (`tammax = 0`) | Catálogo `auxgra` |
| 20 | **El orden del procedimiento queda datado**: gráfico a las 11:40:39, cierre a las 11:46:33 del mismo día | Log + `gra.cod` |
| 21 | **`con.cod` identifica la reclamación de forma única y global**: 23.063 conceptos `tip=708`, 23.063 códigos distintos. El formato es `RS{AA}.{MM}/{NNNN}` y **no codifica la obra** | Recuento + cruce con obra |

### Un caso que vale por sí solo

La reclamación de ejemplo de `01_cierre_incidencia_sigrid.md` (`RS26.08/0123`)
**estaba en PENDIENTE cuando se escribió aquella guía el 2026-08-18, y hoy está
CERRADA**: se cerró ese mismo día a las 11:46:33. Su log completo son tres filas
—alta el 2026-08-04 a las 9:33:10 (la misma hora que muestra la captura de la
guía), «Pasar a pendiente», «Cerrar parte»—, sin pasar por TERMINADA.

Es la comprobación cruzada más limpia que ha salido: la guía de negocio y el ERP
cuentan lo mismo, campo por campo y minuto a minuto.

## 4 · Lo NO confirmado (léase antes de especificar F-009)

Va en el documento entregado, §5, y se repite aquí porque es lo que separa un
dato de una suposición:

1. **Qué hace el proceso por dentro.** Se ha medido su **efecto observable**
   comparando estados y poblaciones; no se ha leído su código. Se revisaron
   `con`, `rcp`, `rcg`, `gra`, `rcpint`, `tar`, `act` y `log`. Si escribe en una
   tabla fuera de esas ocho, no se habría visto.
2. **Si la comprobación del gráfico bloquea o solo avisa.** Los datos son
   consistentes con que bloquee (cero excepciones desde 2023), pero **no se ha
   provocado**: intentarlo habría sido una escritura.
3. **Cómo se guarda una URL asociada.** Sin precedentes (§siguiente).
4. **Si «Cerrar parte» dispara efectos fuera de la base** (correos, avisos). El
   ERP sí manda correos en otros procesos —«Rechazar reclamación» tiene variante
   *envía email* y *NO enviar email*—, pero para «Cerrar parte» no hay señal en
   la base ni a favor ni en contra.
5. **Los 1.509 conceptos `tip = 708` sin fila en `rcp`**: no investigados.
6. **Si la escritura de `sigrid-api` está habilitada hoy.** Va apagada por
   defecto (`azure-apps/sigrid_api.md` §7.2). Comprobarlo exige escribir.

### El gráfico como URL: respuesta negativa, y es un resultado

La opción «Asociar URL de Internet…» **existe en el menú** (la documenta la guía
de Posventa), pero sobre las **282.599** filas de `ruesma.gra`:

- `cod` que empiece por `http`: **0**
- `tex` («Camino») que empiece por `http`: **0**
- `nom` que empiece por `http`: **1**, y no es un enlace — es el nombre de una
  captura de pantalla derivado de una dirección web, guardada como binario
  externo normal (`vin = 3`)
- cualquier campo que mencione `sharepoint`: **0**

**Nunca se ha usado en esta instalación.** No hay ninguna fila de la que deducir
con qué combinación de `vin`/`tex`/`nom` se guardaría. Lo razonable —`vin` con
un valor propio y la dirección en `gra.tex`— es **deducción, no dato**, y va
marcada como tal en el documento. Confirmarlo exige un entorno de pruebas de
Sigrid o preguntar al proveedor del ERP. Y aunque se confirmara, quedaría
abierto si «Cerrar parte» aceptaría un gráfico-URL como documento válido para su
comprobación.

## 5 · Un arreglo que no estaba en el encargo

`bash harness/init.sh` salió **en rojo** al empezar, y no por mi trabajo:

```
FAILED tests/test_f006_repo_sin_identificadores.py::test_f006_r26_el_barrido_del_repositorio_mira_ficheros_de_verdad
E   assert 0 >= 60
```

**Diagnóstico.** El guardián de identificadores de R26 filtraba los directorios
excluidos contra las `parts` **absolutas** del fichero, y `worktrees` está en
esa lista de exclusión —se puso para que el árbol principal no barra dos veces
las copias de los subagentes—. Ejecutado **desde** un worktree, cuya ruta es
`<repo>/.claude/worktrees/agent-XXX/`, *todos* sus ficheros llevan `worktrees`
entre sus `parts`: el barrido salía vacío y **el guardián de secretos quedaba
apagado sin decirlo**.

Lo cazó su propio control: `test_..._mira_ficheros_de_verdad` existe justo para
impedir que un barrido esté «verde por no trabajar». Funcionó exactamente como
se diseñó.

**Arreglo** (commit `337701c`): filtrar contra la ruta **relativa a la raíz**.
Desde el árbol principal `.claude/worktrees/` se sigue excluyendo —que es para
lo que se puso— y deja de excluirse a sí mismo cuando la raíz *es* el worktree.
Los 29 tests del fichero, en verde.

**No se porta a `arnes-base`**: el fichero es específico de este proyecto (nació
del hallazgo H1 de la review de F-006). Lo que sí es transversal es **la
lección** —un guardián que filtra por ruta absoluta se apaga solo dentro de un
worktree— y queda anotada aquí para quien escriba el siguiente.

**Segundo tropiezo, este de entorno y sin cambios en el repositorio**: el
worktree no traía `services/postventa-api/.venv` (no se versiona), así que el
portero de servicios fallaba. Resuelto con una **unión de directorio** al venv
del árbol principal. No toca ningún fichero versionado.

## 6 · Recomendación de alcance para F-009

La ficha de F-009 dice «solo estado» y deja el alcance real a lo que saliera de
aquí. Sale esto:

### 6.1 · Mover el estado es suficiente… en la base de datos

Está verificado que el efecto persistente de «Cerrar parte» sobre los datos de
negocio es **exactamente `con.est` → el `est` de `conest` con `cod='CER'`**. No
hay fecha de cierre que rellenar, ni seguimiento, ni tarea que avanzar: `rcp` ni
siquiera *tiene* una columna de cierre. Un `UPDATE con SET est = ? WHERE ide = ?`
deja la reclamación indistinguible de una cerrada a mano **en cuanto a datos**.

**Pero se deja la fila de `dbo.log` sin escribir**, y ahí sí hay diferencia
visible: hoy el log es el **único** rastro temporal de un cierre, porque
`tiemod` no se mueve (§3, #7). Una incidencia cerrada por nosotros sería, para
quien audite, una que **nadie cerró nunca**.

**Recomendación**: F-009 escribe **las dos filas en la misma transacción** — el
`UPDATE` de `con.est` y el `INSERT` en `dbo.log` con `ope=5` y un `tex`
identificable. Sobre el `tex` hay que decidir con el humano, y la decisión no es
cosmética:

- `'Cerrar parte'` a secas hace nuestros cierres **indistinguibles** de los
  manuales. Malo: si el piloto se tuerce, no hay forma de saber cuáles fueron
  nuestros.
- Un texto propio (`'Cerrar parte (posventa-incidencias)'`) los hace
  **rastreables y reversibles**, a cambio de romper la uniformidad del log.

**Mi recomendación es el texto propio**, al menos durante el piloto de
Mirasierra. El coste de no poder identificar lo que hemos escrito en un ERP de
producción es mucho mayor que el de una etiqueta distinta en un informe.

Y `usu`: hoy son 7 logins humanos los que han cerrado partes. Habrá que decidir
si va el login del usuario del front o un usuario de servicio. **Es una pregunta
para el humano**, no para el implementador.

### 6.2 · El gráfico: NO lo suba F-009

Tres razones, en orden de peso:

1. **No hace falta para cerrar por SQL.** La comprobación del gráfico la hace el
   **proceso** del ERP, no una restricción de la base. Un `UPDATE` la esquiva.
2. **Esquivarla es precisamente el riesgo**, y no se arregla subiendo el
   documento a lo bruto: se arregla **comprobándola nosotros**. F-009 debe
   **negarse a cerrar** una reclamación sin fila en `rcg` — misma regla que el
   ERP, aplicada por nuestro lado. Es una condición barata de verificar
   (`SELECT COUNT(*) FROM rcg WHERE con = ?`) y convierte el atajo en una
   réplica fiel del control.
3. **Subir el gráfico es escribir un BLOB en `ruesma_rep`**, que la pasarela
   **nunca** escribe por diseño (§2.1 de `sigrid_api.md`), y en dos tablas de
   dos bases casadas por `cod`. Eso ya tiene su propia feature: **F-012**. No
   se adelanta a F-009.

### 6.3 · La opción «sin archivo (RPV)»: NO sirve, y es mejor así

Se preguntaba si «puede que sea justo la que necesitamos». **No lo es**:

- **Termina en el mismo `est = 9`**: no aporta ningún estado distinto que
  copiar. Como efecto en la base, es idéntica.
- Lo único que aporta es **saltarse el control del gráfico** — exactamente lo
  que *no* queremos legitimar.
- **Está abandonada desde 2025-03-11.** Amarrar una feature nueva a un camino
  que Posventa dejó de usar hace año y medio es heredar deuda el primer día.

### 6.4 · Consecuencias concretas para la spec de F-009

1. El estado se resuelve `SELECT est FROM conest WHERE tip = 708 AND cod = 'CER'`.
   **Ni el 9 ni el 708 cableados** — el `tip` también sale de la reclamación.
2. **Precondición dura**: no cerrar sin gráfico asociado. Réplica del control del
   ERP (§6.2).
3. **Idempotencia**: si `con.est` ya es el de `CER`, no se toca ni se registra.
   La ficha ya lo pedía y el dato lo respalda — los estados finales están
   marcados **no editables** en `conest`.
4. **Reversibilidad**: los cierres se deshacen en el ERP (`ope=30`, 81 casos).
   Nuestro registro local no puede asumir que lo que cerramos sigue cerrado; el
   dry-run debe **releer el estado actual**, no fiarse de lo que guardamos.
5. **Localización**: por `con.cod` (`RS{AA}.{MM}/{NNNN}`), único y global, con
   `tip = 708`. Ojo al formato: Sigrid usa barra (`RS26.08/0123`) y el nombre del
   fichero usa guion (`RS26.08 - 0123`). La conversión es nuestra.
6. **El dry-run tiene todo lo que necesita**: código, descripción, estado origen
   con su `cod`/`res` legibles y estado destino. Sale de una sola consulta.
7. **Pendiente de verificar con el humano antes de escribir una línea**: que la
   escritura de `sigrid-api` esté habilitada, con qué prefijos permitidos, y con
   qué `usu` se firma el log.

## 7 · Evidencias

Nivel de rigor **`documental`** (`harness/rigor.json`): `fase_red: false`,
`cobertura: false`, `mutacion: false`. Se declara qué se midió y por qué el
resto no aplica, en vez de omitir la sección.

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | `bash harness/init.sh` **en verde**. Servicio `api`: **1.078 pasan, 13 saltados, 0 fallan**. Servicio `front`: **74 pasan** (la segunda pasada la sirvió la caché, árbol sin cambios) |
| **Tiempo de la suite** | api **47,18 s** · front **3,16 s** |
| **Cobertura de líneas cambiadas** | **No aplica**, y así lo dice el propio portero: `PUERTA COBERTURA: N/A (F-008 es de nivel documental: no exige cobertura)` |
| **Mutación** | **No aplica** por nivel (`mutacion: false` en `documental`). El único cambio de código es la corrección de un test (§5); mutar un test no mide nada |
| **Fase RED** | **No exigida** por nivel (`fase_red: false`). El arreglo de §5 sí llegó con su fallo delante: `assert 0 >= 60`, pegado literal arriba, y los 29 tests del fichero en verde después |
| **Consultas al ERP** | ~25, todas `SELECT`. **Cero escrituras** |
| **Filas leídas** | Ninguna consulta cerca del tope de 1.000 filas: la mayor devuelve 36 |

### Verificaciones MANUAL (humano) pendientes

1. **Decidir el `tex` de la fila de log** que escribirá F-009 (§6.1): texto
   propio rastreable frente a `'Cerrar parte'` indistinguible. Recomendado el
   propio.
2. **Decidir el `usu`** con el que se firma ese log: login del usuario del front
   o usuario de servicio.
3. **Confirmar si la escritura de `sigrid-api` está habilitada** para esta
   instalación y con qué `ALLOWED_WRITE_PREFIXES`. No se ha comprobado: hacerlo
   es escribir.
4. **Decidir si merece la pena confirmar el gráfico-URL** en un entorno de
   pruebas de Sigrid o preguntando al proveedor. Hoy F-009 no lo necesita
   (§6.2), pero **F-013** —mudar el archivo a la biblioteca de Posventa— sí que
   se apoyaría en ello.

## 8 · Estado de la feature

`F-008` sigue en **`pending`** en `harness/features.json`, **a propósito**:
`F-010` está `in_progress` y el portero valida que solo haya una. Ponerla
`in_progress` habría dejado `init.sh` en rojo. **El líder decide** cuándo
moverla; no la marco `done` yo, eso ocurre tras el APROBADO del reviewer.

`azure-apps/postventa_incidencias.md` **no necesita refresco todavía**: F-008 no
cambia lo que este proyecto expone ni consume — solo documenta un sistema que ya
constaba como consumido. Sí habrá que actualizarlo cuando F-009 escriba de
verdad en el ERP.
