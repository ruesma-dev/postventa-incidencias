<!-- specs/F-033-l1-traza-archivo/design.md -->
# F-033 · La primera capa contra el duplicado en SharePoint, conectada — Diseño técnico

> Servicio: `services/postventa-api/` (backend). **El front no se toca.**
> Encaja en `docs/ARCHITECTURE.md`, paso 6 del pipeline (archivo, «tres capas»)
> y en `docs/CONVENTIONS.md`: hexagonal, el paso habla con puertos, la
> composición vive en el borde, el SQL en `infrastructure/persistencia/` y
> ningún valor interpolado en el texto de una sentencia.
>
> **Sin DDL.** Ni una tabla, ni una columna, ni un índice nuevos: la traza ya
> tiene todo lo que hace falta (`sql/05_archivos.sql`).
>
> **Sin escrituras en ningún sistema** al redactar esta spec: todo lo medido es
> lectura del repositorio.

## 0 · Dónde está el riesgo

| Qué pasa hoy | Qué ve alguien | Por qué importa |
|---|---|---|
| Re-archivar un parte con **el mismo nombre y carpeta** | Nada: L2 reemplaza el homónimo | Tapa el agujero por casualidad, y sube los bytes otra vez |
| Re-archivar con **otro nombre** (F-032: el código limpio de espacios) | Dos ficheros del mismo parte en la carpeta | Un PDF con DNI manuscrito duplicado en el archivo de Posventa |
| Re-archivar con **otra biblioteca** (F-013: de IT a Posventa) | El parte aparece en Posventa, y sigue en IT | Contra la decisión H4 de F-013, y… |
| …en los tres casos, el `upsert` **pisa** la traza | Nadie lo ve | Se pierde `drive_id`, `item_id`, `carpeta`, `nombre_fichero` y `web_url` del fichero anterior: deja de ser localizable desde nuestra base |

El circuito re-archiva a menudo: el front de F-025 vuelve a llamar a
`/api/archivar` en cada reintento de una tanda. No es un caso raro.

## 1 · Ficheros

### 1.1 A crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/postventa-api/tests/test_f033_l1_desde_el_almacen.py` | tests | R7–R11, R13–R16, R18–R21 sobre el paso, con dobles |
| `services/postventa-api/tests/test_f033_situacion_con_archivo.py` | tests | R1–R6 y R17 sobre sentencias, mapeo y adaptador, con `ConexionFalsa` de `utiles_pg.py` |
| `services/postventa-api/tests/test_f033_archivar_http.py` | tests | R12, R14 y R23 recorriendo `function_app.archivar`; el circuito doble-archivado con `RepositorioComoLaBase` |

### 1.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/estado.py` | `SituacionParte` gana `archivo: TrazaArchivo \| None = None`, **el último** (R1). Import de `TrazaArchivo` desde `domain.models.persistencia` (sin ciclo: `persistencia.py` no importa nada del dominio). Docstring: «Cuatro cosas» pasa a cinco, con **enmienda fechada** que cite la frase vieja |
| `services/postventa-api/domain/ports/persistencia.py` | Solo el docstring de `consultar_situacion` y de `guardar_archivo`: la quinta cosa y el «no pisa `archivado`» (R17). **Ningún método nuevo** |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | (a) `_COLUMNAS_ARCHIVO`, lista única para escribir y leer; (b) `upsert_archivo` con `WHERE … estado <> %s` y `_ESTADO_ARCHIVO_TERMINAL = "archivado"` como parámetro (R17); (c) `select_veredicto_y_cierre` con un tercer `LEFT JOIN archivos AS a` y las ocho columnas de la traza **al final** (R2, R3). Enmienda fechada en su docstring |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | `fila_a_traza_archivo(columnas, *, hash_parte)` y `fila_a_situacion_guardada(fila, *, hash_parte)`, que parte la fila en sus dos tramos (§3.3). `fila_a_validacion_y_cierre` **no cambia** |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | `consultar_situacion` usa `fila_a_situacion_guardada` y rellena `archivo`; el log añade `archivo=<estado>` (R6). `guardar_archivo` registra `SIN_CAMBIOS` como hoy registra cualquier resultado |
| `services/postventa-api/application/pipelines/paso_archivo.py` | Se quita `traza_previa`; entra `drive_id_vigente: str \| None = None`; L1 lee `ctx.situacion.archivo`; avisos nuevos; carrera de la traza previa (§4) |
| `services/postventa-api/interface_adapters/api/archivar.py` | Pasa `drive_id_vigente=ajustes.sharepoint_drive_id`. Nada más: la situación la lee la puerta del paso |
| `services/postventa-api/tests/utiles_pg.py` | `RepositorioComoLaBase`: `guardar_archivo` con la semántica terminal de R17 y `consultar_situacion` que arma la fila **con las ocho columnas nuevas** y la pasa por `mapeo.fila_a_situacion_guardada` (la función de producción) |
| `services/postventa-api/tests/utiles_sharepoint.py` | `RepositorioFalso.guardar_archivo` admite un resultado programable (`resultados: dict[int, ResultadoGuardado]`) para la carrera de R18. Nada más |
| `services/postventa-api/tests/test_f006_paso_archivo.py`, `tests/test_f019_orden_archivado.py` | Solo los **atajos** `archivar(...)` y `_archivar(...)`: si reciben `traza_previa=`, la **siembran** en `repositorio.situacion.archivo` en vez de pasarla al paso. **Ni un aserto cambia** (§7) |
| `services/postventa-api/tests/test_f005_sentencias.py`, `tests/test_f028_persistencia.py`, `tests/test_f030_veredicto_persistido.py`, `tests/test_f005_mapeo.py` (si arma filas de la situación) | Los que fijan **la forma** de `select_veredicto_y_cierre` —número de `JOIN`, tupla de columnas, filas de diez— se amplían con el tercer `JOIN` y las ocho columnas. El aserto de **dos sentencias** no cambia: es el criterio de esta feature (§7) |
| `docs/ARCHITECTURE.md` | Precisión fechada de F-033 bajo «tres capas» del paso 6 (R25) |

### 1.3 Lo que NO se toca (y tienta)

- **`infrastructure/persistencia/sql/`**: sin DDL. `archivos` ya tiene clave
  por `hash_parte` y las ocho columnas.
- **`RepositorioPartesPort`**: no gana `consultar_archivo`. La ficha lo
  mencionaba; se descarta por el criterio 4 de la propia ficha (§3.1).
- **`paso_grafico.py`, `paso_cierre.py`, `adjuntar.py`, `cerrar.py`**: su
  precondición «consta archivado» sale del cuerpo y es un defecto (§9), pero
  arreglarlo cambia las puertas de las dos escrituras en el ERP de producción.
  Ficha aparte (**D-6**).
- **`domain/models/nombrado.py`** y el origen de `codigo_obra` /
  `numero_incidencia` del paso: es **F-031**.
- **`ArchivoPort`**, `infrastructure/sharepoint/**`: L1 no llama a nadie.
- **`puerta_de_estado.py`**: ya deja la situación en `ctx.situacion`; L1 la
  reutiliza tal cual.
- **`consultar_estado_cierre`** y `select_estado_cierre`: los siguen usando
  `estado.py` y `parte.py`.
- **`services/postventa-front/`**: el contrato HTTP no cambia (R23).
- **`azure-apps/postventa_incidencias.md`**: no cambia ningún endpoint, tabla,
  variable ni base que expongamos o consumamos. No se toca (misma
  conclusión que F-032).

## 2 · Límite de microservicio

Todo vive en `postventa-api`, en el paso 6 y en su persistencia propia (schema
`postventa`). No cruza la frontera de ningún otro servicio ni toca el
PostgreSQL compartido a nivel de servidor. **Nada que extraer.**

## 3 · La traza en la situación

### 3.1 Por qué dentro de la consulta existente y no un `consultar_archivo`

El criterio 4 de la ficha dice «la consulta de la situación no cuesta ninguna
sentencia más». Las dos opciones, medidas contra él:

| Opción | Sentencias por archivado | Qué más cuesta |
|---|---|---|
| **A · Tercer `LEFT JOIN` en `select_veredicto_y_cierre`** | **2**, como hoy, en todos los caminos | Ampliar los tests que fijan la forma de esa sentencia (§7) |
| B · `consultar_archivo` nuevo en el puerto | 3 en `/api/archivar` (o 2 + 1) | Un método más en el `Protocol`, en tres dobles y en el adaptador; y **una segunda fuente** de la misma traza: el paso podría leer una y la puerta otra |

**Se elige A.** B no cumple el criterio y reabre el problema que F-030 cerró
para el veredicto: quien deriva algo tiene que recibirlo todo de la misma
consulta y del mismo almacén. Es exactamente el argumento de F-030 §5.4 y de
la enmienda de `SituacionParte`, aplicado al quinto hecho.

Coste en la base: un `LEFT JOIN` por clave primaria (`archivos.hash_parte`) en
una consulta que ya se ancla en otra clave primaria. Nulo en el B1ms
compartido. Lo pagan también `/api/adjuntar`, `/api/cerrar`, `/api/estado` y
`/api/parte`, que ahora reciben la traza sin pedirla; no la usan (salvo lo que
proponga D-6).

### 3.2 La sentencia

```sql
SELECT v.veredicto, v.destino, v.clasificacion_firma, v.motivos,
       v.avisos,
       p.observaciones, p.observaciones_confianza_pct,
       p.codigo_obra, p.numero_incidencia,
       c.estado,
       a.estado, a.nombre_fichero, a.carpeta, a.drive_id,
       a.item_id, a.web_url, a.motivo, a.archivado_at_utc
FROM postventa.partes AS p
LEFT JOIN postventa.validaciones AS v ON v.hash_parte = p.hash_parte
LEFT JOIN postventa.cierres AS c ON c.hash_parte = p.hash_parte
LEFT JOIN postventa.archivos AS a ON a.hash_parte = p.hash_parte
WHERE p.hash_parte = %s
```

- Las ocho columnas nuevas van **al final**: las diez primeras conservan su
  posición y `fila_a_validacion_y_cierre` no se toca.
- Se generan desde `_COLUMNAS_ARCHIVO[1:]` con el prefijo `a.`, **la misma
  lista** que escribe `upsert_archivo`: dos listas del mismo orden divergen
  (mismo motivo que `_COLUMNAS_GRAFICO` y `_COLUMNAS_HISTORICO`).
- `LEFT` y anclada en `partes`, por lo mismo que los otros dos: un parte
  validado y sin archivar es el caso normal, y un `JOIN` a secas se llevaría
  por delante el veredicto.
- `archivos` tiene como mucho **una** fila por `hash_parte` (clave primaria):
  el tercer `JOIN` no multiplica filas.
- Se **conserva el nombre** `select_veredicto_y_cierre`. Renombrarla
  («`select_situacion_guardada`») sería más exacto y tocaría cinco ficheros de
  test más sin añadir nada; se anota en su docstring que trae también la traza.

`_COLUMNAS_ARCHIVO`:

```python
_COLUMNAS_ARCHIVO: tuple[str, ...] = (
    "hash_parte", "estado", "nombre_fichero", "carpeta", "drive_id",
    "item_id", "web_url", "motivo", "archivado_at_utc",
)
```

es exactamente la tupla que hoy declara `upsert_archivo` en su cuerpo, en el
mismo orden: el `INSERT` no cambia de texto salvo por el `WHERE`.

### 3.3 El mapeo

```python
# infrastructure/persistencia/mapeo.py
def fila_a_traza_archivo(columnas: Sequence[Any], *, hash_parte: str) -> TrazaArchivo | None:
    """Las ocho columnas de `archivos`, o `None` si `estado` viene a NULL.

    `estado` a NULL es «no hay fila en archivos» (LEFT JOIN): la columna es
    NOT NULL en la tabla, así que no hay otra forma de que venga vacía.
    `EstadoArchivo(estado)` revienta con un valor desconocido (R5).
    El `hash_parte` entra por palabra clave: es el que se pidió."""

def fila_a_situacion_guardada(
    fila: Sequence[Any], *, hash_parte: str
) -> tuple[ResultadoValidacion | None, str | None, TrazaArchivo | None]:
    """Parte la fila de `select_veredicto_y_cierre` en sus dos tramos:
    las diez primeras a `fila_a_validacion_y_cierre` (sin tocar) y las ocho
    últimas a `fila_a_traza_archivo`. Exige exactamente 18 columnas: una fila
    más corta o más larga es una sentencia y un mapeo que han divergido, y se
    falla con ValueError en vez de leer por posición lo que no es."""
```

El corte entre tramos (`10`) vive en `mapeo.py` como constante con nombre,
**pegada** a los dos desempaquetados, y un test la compara con el número de
columnas de `select_veredicto_y_cierre` (§6).

### 3.4 El adaptador

`consultar_situacion` cambia en tres líneas: `fila_a_situacion_guardada` en vez
de `fila_a_validacion_y_cierre`, `archivo=` en el `SituacionParte` y el log con
`archivo=%s` (el `estado.value` o `None`). **Siguen siendo dos `_leer`.**

## 4 · El paso

### 4.1 Firma

```python
def paso_archivo(
    ctx: ContextoParte,
    archivador: ArchivoPort,
    repositorio: RepositorioPartesPort,
    *,
    carpeta_base: str,
    ahora: datetime,
    drive_id_vigente: str | None = None,
) -> ContextoParte:
```

`traza_previa` desaparece (R7, **D-2**). `drive_id_vigente` es opcional para
que los tests que no hablan de bibliotecas no tengan que inventarse uno; el
borde siempre lo pasa (R15).

### 4.2 El orden, y qué cambia en cada paso

| # | Paso | Hoy | Con F-033 |
|---|---|---|---|
| 1 | Puerta de estado | lee la situación → `ctx.situacion` | igual (la situación trae ahora la traza) |
| 2 | Nombrado | `componer_destino` | igual |
| 3 | **L1** | `_ya_archivado(ctx, traza_previa)`: siempre `None` desde el borde | `_ya_archivado(ctx, ctx.situacion.archivo)` → corta (R10); si además difiere del destino, segundo aviso (R14) |
| 3 bis | Intento anterior en otra ruta | — | traza `pendiente` con otra carpeta o nombre → aviso + log, y sigue (R20) |
| 4 | Traza previa `pendiente` | escribe; lo que devuelva da igual | si devuelve `SIN_CAMBIOS` → releer situación una vez, devolver la traza `archivado` con `AVISO_YA_ARCHIVADO` y **no subir** (R18) |
| 5–7 | Carpeta, homónimo, subida | igual | igual |
| 8 | Traza final / de error | escribe | igual; `SIN_CAMBIOS` se registra y no es error (R19) |

`ctx.situacion` está garantizado en el paso 3: la puerta (paso 1) es lo primero
y o lo rellena o levanta. Aun así L1 lee con `situacion_leida(ctx,
repositorio)` de `puerta_de_estado.py` —que ya existe para esto—: si algún día
alguien reordena el paso, lo que ocurre es una consulta de más, no un L1
inerte otra vez.

### 4.3 Qué es «otro destino» (R14, R15)

```python
def _en_otro_destino(traza: TrazaArchivo, destino, drive_id_vigente: str | None) -> bool:
    return (
        traza.nombre_fichero != destino.nombre_fichero
        or traza.carpeta != destino.carpeta
        or (drive_id_vigente is not None and traza.drive_id is not None
            and traza.drive_id != drive_id_vigente)
    )
```

Función privada del paso, no del dominio: compara una traza de persistencia
con configuración, y el dominio no sabe de bibliotecas. Casos que la tabla de
tests cubre uno a uno: igual en todo; otro nombre (F-032); otra carpeta; otra
biblioteca (F-013); `drive_id` vigente ausente; `drive_id` de la traza
ausente; nombre y carpeta `None` en la traza (una traza vieja o recortada:
cuenta como distinta, porque no se puede afirmar que sea la misma ruta).

### 4.4 Los avisos

```python
AVISO_YA_ARCHIVADO  # el de hoy, intacto (F-006 R14)

AVISO_ARCHIVADO_EN_OTRO_DESTINO = (
    "este parte se archivó en otra ruta o en otra biblioteca y sigue allí: no "
    "se ha vuelto a subir al destino actual, y la carpeta y el nombre que "
    "devuelve esta respuesta son los de entonces"
)

AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA = (
    "hubo un intento anterior de archivar este parte en «{carpeta}/{nombre}» "
    "que no llegó a confirmarse: si aquel fichero llegó a subirse, sigue allí "
    "y conviene revisarlo"
)
```

El tercero lleva carpeta y nombre: son códigos de obra e incidencia, no datos
del papel, y la respuesta ya devuelve los del intento actual. Ninguno lleva
identificadores de biblioteca.

### 4.5 La carrera de la traza previa (R18, **D-7**)

Dos peticiones del mismo parte (dos pestañas, o un reintento del front que se
cruza con la primera llamada aún viva tras el corte del proxy a 45 s):

1. A y B leen la situación: sin traza `archivado`.
2. A escribe `pendiente`, sube y escribe `archivado`.
3. B escribe `pendiente` → con R17 la fila ya está en `archivado`, el
   `DO UPDATE` no se aplica y vuelve `SIN_CAMBIOS`.

Hoy B subiría igual. Con F-033, B **para ahí**: relee la situación (dos
sentencias, solo en este camino), toma la traza `archivado` de A y responde
como L1. Si la relectura no trajera traza `archivado` —imposible salvo un
borrado manual por medio— el paso levanta `PersistenciaNoDisponible` con un
motivo que lo dice, sin subir: ante la duda, no se sube.

Lo que **no** cubre (riesgo residual, §8): que A y B pasen **los dos** la
traza previa antes de que ninguno escriba `archivado`. Los dos suben; con el
mismo destino, L2 deja un solo fichero; la segunda traza final vuelve
`SIN_CAMBIOS` (R19).

## 5 · El re-archivo deliberado (**D-4**)

La pregunta era si, con L1 conectado, sigue siendo posible volver a archivar a
propósito un parte ya archivado, y cómo. Los casos reales, uno a uno:

| Caso | ¿Mismo `hash`? | Qué pasa con F-033 |
|---|---|---|
| Se escanea **otra vez** el papel (mejor calidad, faltaba una hoja) | **No**: el `hash` es de las páginas del PDF troceado (F-002) | Es otro parte. Se guarda, se valida y se archiva por el camino normal; si el nombre coincide, L2 reemplaza con `AVISO_REEMPLAZADO` |
| Alguien corrige el código de obra o de incidencia **después** de archivar | Sí | L1 corta y avisa de otro destino (R14). El fichero se queda donde está. Moverlo es una decisión de una persona en SharePoint (F-013 R43 ya describe cómo sin perder el `item_id`) |
| Mudanza de biblioteca (F-013) | Sí | L1 corta: lo de IT se queda en IT (H4) |
| Alguien **borró** el fichero de SharePoint por error | Sí | L1 corta y la traza apunta a un fichero que no existe. Lo recupera una persona de la papelera del sitio. **[NO MEDIDO]** cuántas veces ha pasado: ninguna registrada |

Ninguno necesita que **el sistema** vuelva a subir los mismos bytes. Por eso
la recomendación es **no ofrecer** re-archivo forzado (R21): cada vía que lo
ofrezca —un parámetro, un campo del cuerpo— es una vía para subir dos veces
un PDF con un DNI, y el cuerpo de la petición **no abre puertas** en este
proyecto desde F-030. Si aparece un caso real, ficha propia con su registro
de quién y cuándo (el patrón sería el de `historico_estado`: append-only, con
`oid`), no un interruptor.

La salida de emergencia existe y es manual: un `UPDATE` de una sola fila en
`postventa.archivos` hecho por el humano, que **pisaría** la traza. No se
documenta como procedimiento a propósito; se menciona aquí para que conste
que se ha considerado y que su precio es exactamente el rastro que esta
feature protege.

## 6 · Tests (todos sin red, sin BBDD y sin IA)

| Fichero | Qué cubre |
|---|---|
| `test_f033_situacion_con_archivo.py` | R1 (campo, por omisión `None`, el último de la dataclass); R2 (sentencia con `LEFT JOIN … archivos AS a`, anclada en `partes`, columnas nuevas al final y en el orden de `_COLUMNAS_ARCHIVO`); R3 (**dos** sentencias con traza y sin ella, `veces_con("FROM postventa.archivos") == 0`: no hay tercera); R4 (sin fila → los tres `None`); R5 (estado desconocido → `ValueError`); R6 (el log trae el estado y **no** trae `drive_id`, `item_id`, `web_url` ni `motivo`, con valores centinela inventados); R17 (`upsert_archivo` con `WHERE … estado <> %s`, `archivado` en los parámetros y no en el texto; el adaptador traduce la ausencia de fila a `SIN_CAMBIOS`); el corte `10` coincide con la sentencia; fila de 17 o 19 columnas → `ValueError` |
| `test_f033_l1_desde_el_almacen.py` | R7 (la firma no tiene `traza_previa`; `inspect.signature`); R8 (con traza `archivado` sembrada en la situación, cero escrituras y cero llamadas al archivador); R9 (orden: con traza `archivado`, `registro == []`); R10 (devuelve **la** traza guardada, `is`); R11 (`pendiente` y `error` no cortan); R13–R15 (tabla de §4.3); R16 (ninguna operación del archivador fuera de `asegurar_carpeta`/`buscar`/`subir`, y ninguna en los cortes); R18 (primera escritura `SIN_CAMBIOS` → relectura, no sube, aviso; relectura sin `archivado` → error sin subir); R19 (traza final `SIN_CAMBIOS` no es fallo); R20 (aviso con ruta anterior y log con `caplog`); R21 (un escaneo nuevo —otro `hash`— con el mismo nombre sube y avisa de reemplazo) |
| `test_f033_archivar_http.py` | R12: `function_app.archivar` con un parte cuya situación trae traza `archivado` → 200, las seis claves, valores de la traza guardada, `archivador.llamadas == []`. **El circuito**: con `RepositorioComoLaBase`, archivar **dos veces** el mismo parte → una subida, la segunda con `AVISO_YA_ARCHIVADO`, la traza intacta (mismo `item_id`, `archivado_at_utc` del primero). **El caso F-032**: traza `archivado` sembrada con el nombre viejo `0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf`, y archivado con el código ya limpio → cero subidas, aviso de otro destino, respuesta con el nombre viejo. **El caso F-013**: traza con `drive_id` distinto del vigente → cero subidas y aviso de otro destino, y el `drive_id` no aparece en el cuerpo de la respuesta (R15, R23, R24) |

Todos los tests con nombre `test_f033_rN_*`. Los dobles no llegan a Graph ni a
PostgreSQL (guardia de red de la suite, F-006 R19–R22).

## 7 · Tests existentes que cambian, y por qué ninguno afloja

| Test | Qué fija hoy | Qué cambia |
|---|---|---|
| `test_f005_sentencias.py::test_f030_r16_…_los_dos_join_son_left` | `count("LEFT JOIN") == count("JOIN") == 2` | `== 3`, y se añade el aserto del tercero (`LEFT JOIN postventa.archivos AS a`). El criterio —todos `LEFT`, anclados en `partes`— sigue entero |
| `test_f005_sentencias.py::test_f030_r10_…_orden_de_las_columnas` | tupla de diez | tupla de dieciocho: las diez de antes **en el mismo orden** + las ocho de la traza |
| `test_f005_sentencias.py::test_f030_…_tres_tablas` | tres tablas con esquema | cuatro |
| `test_f005_sentencias.py` (upsert_archivo) | `INSERT`, `ON CONFLICT`, `intentos + 1` | se mantiene y se **añade** el `WHERE` (en `test_f033_…`) |
| `test_f028_persistencia.py::_fila_de_lo_guardado` y `test_f030_veredicto_persistido.py` (ayudante de fila, l. 852) | filas de diez | filas de dieciocho, con la traza a `None` por omisión. Los asertos de **dos sentencias** (`:458`, `:1453`) **no cambian**: son el criterio 4 de esta ficha |
| `test_f006_paso_archivo.py::archivar`, `test_f019_orden_archivado.py::_archivar` | pasan `traza_previa` al paso | el atajo la **siembra** en `repositorio.situacion` (`dataclasses.replace(…, archivo=…)`) y no la pasa. Los cuerpos de los tests y sus asertos, intactos; siguen demostrando R14 de F-006 y R24 de F-019, ahora por el camino real |

Regla para el implementer: si algún otro aserto existente tuviera que cambiar
de **expectativa** (no de forma), se **para** y se consulta. Cambiar la forma
de una fila no es aflojar; cambiar lo que se espera, sí.

## 8 · Riesgos y alternativas descartadas

1. **Carrera doble antes de `archivado`** (§4.5, último párrafo). Dos
   peticiones que escriben `pendiente` antes de que ninguna escriba
   `archivado` suben las dos. Con el mismo destino, L2 lo reduce a un fichero.
   Cerrarlo del todo exige un bloqueo (`SELECT … FOR UPDATE` o un estado
   `subiendo` con dueño), que es otra feature. Se acepta: hoy **toda**
   repetición sube; con F-033 solo la simultánea exacta.
2. **Traza `pendiente` de un fichero subido sin traza final** (R20). La
   traza previa la pisa. Queda el aviso en la respuesta y la línea de log; el
   500 de `ArchivoSinTraza` ya avisó en su momento. Alternativa: 409 hasta que
   una persona mire (D-5 (b)). Se descarta como recomendación porque bloquea
   también el caso común —una subida que falló de verdad y no dejó nada— y
   `pendiente` no distingue los dos.
3. **La relectura de R18 es una consulta más**, solo en la carrera. El
   criterio 4 habla de la consulta de la situación, que sigue costando dos; la
   relectura es otra llamada a esa misma consulta en un camino excepcional. Se
   declara aquí para que el reviewer no lo encuentre por su cuenta.
4. **Histórico append-only de trazas** (D-3 (b)): tabla nueva
   `postventa.archivos_historico` con `bigserial`, escrita en cada cambio de
   traza. Guardaría también las `error` y `pendiente`, que hoy se pisan. Se
   descarta **mientras no haya un caso que lo pida**: con R17 la única traza
   que prueba que un fichero existe —la `archivado`— ya no se puede pisar, y
   la otra —`pendiente` de un `ArchivoSinTraza`— la cubre R20. Es DDL en una
   base compartida y ya desplegada: si se quiere, que sea con su propia ficha.
5. **Comprobar el destino antes de cortar** (D-1 (b)): si la traza apunta a
   otro sitio, volver a subir al actual. Es justo lo que F-013 H4 prohíbe, y
   con F-032 dejaría dos ficheros del mismo parte. Descartado.
6. **Mantener `traza_previa` como sobrecarga opcional** (D-2 (b)). Dos
   fuentes para el mismo corte: la del parámetro gana y la del almacén queda
   de adorno, que es la forma exacta del defecto. Descartado.
7. **`consultar_archivo` en el puerto** (§3.1, opción B). No cumple el
   criterio 4. Descartado.

## 9 · Hallazgo: la precondición «consta archivado» de adjuntar y cerrar sale del cuerpo (**D-6**)

**[MEDIDO]** Al leer la traza de archivo para esta spec:

- `interface_adapters/api/adjuntar.py:262-265` y `cerrar.py:235-238` fabrican
  `ctx.archivo = TrazaArchivo(estado=EstadoArchivo(<campo del cuerpo
  estado_archivo>))`;
- `paso_grafico.py:282-296` y `paso_cierre.py:240-…` deciden «consta
  archivado» mirando **ese** `ctx.archivo`;
- y el front lo manda **fijo**: `services/postventa-front/js/pipeline.js:540`
  y `:631`, `estado_archivo: ESTADO_ARCHIVADO`.

Es la misma clase de defecto que F-030 cerró para el veredicto: una puerta que
se abre con lo que diga el cuerpo. Hoy la contienen otras puertas —el estado
`aprobado` leído del almacén, y en el cierre el gráfico adjuntado, también del
almacén—, pero **la del gráfico no tiene detrás ninguna que mire el archivo**:
un parte aprobado y **sin archivar** se adjuntaría al ERP de producción si el
cuerpo dice `archivado`, y el front siempre lo dice.

**No se arregla aquí**: cambia las puertas de las dos escrituras en el ERP y el
contrato de dos endpoints, y no es L1. **Recomendación**: ficha nueva, rigor
`critico`, inmediatamente después de F-033 y antes de F-013. Con F-033
mergeada es poca cosa: `ctx.situacion.archivo` ya está ahí, leído en la misma
consulta que esos dos pasos ya hacen en su puerta.

## 10 · Decisiones abiertas, con alternativas

| Id | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **D-1** | Traza `archivado` que apunta a otro destino | (a) cortar siempre, con aviso propio; (b) re-subir al destino actual; (c) cortar sin distinguir | **(a)**. (b) duplica y rompe H4; (c) deja a la persona sin saber que el fichero está en otra ruta |
| **D-2** | ¿Quitar `traza_previa` del paso? | (a) sí, L1 lee solo del almacén; (b) mantenerla como sobrecarga | **(a)** |
| **D-3** | Rastro de lo subido | (a) no pisar `archivado` (`WHERE` en el `upsert`); (b) histórico append-only con DDL; (c) nada, basta L1 | **(a)**. (c) deja el rastro a merced de cualquier camino futuro que escriba la traza; (b) es más de lo que hace falta hoy |
| **D-4** | Re-archivo deliberado del mismo parte | (a) no existe desde el circuito; (b) campo del cuerpo `forzar`; (c) ficha propia con registro de quién y cuándo | **(a)**, y (c) solo si aparece un caso real |
| **D-5** | Traza `pendiente` con otra ruta | (a) seguir, con aviso y log; (b) 409 hasta que mire una persona; (c) seguir sin decir nada | **(a)** |
| **D-6** | «Consta archivado» de `adjuntar`/`cerrar` desde el cuerpo (§9) | (a) ficha nueva `critico` antes de F-013; (b) absorberlo en F-033 como bloque final; (c) dejarlo | **(a)** |
| **D-7** | Carrera en la traza previa | (a) releer una vez y cortar; (b) 409 «otra petición lo archivó»; (c) ignorar y subir | **(a)**: el front recibe lo mismo que en un L1 normal |

## 11 · El terreno que deja para F-013 y F-031

- **F-013** (spec en `feature/F-013-archivo-posventa`, `8f72e66`): su tabla del
  paso (§5) pone L1 en el paso 3, antes de resolver el destino, y su R25 exige
  que un parte `archivado` con el `drive_id` de IT no se suba a Posventa. Con
  F-033: L1 corta por `hash` + estado **sin mirar el destino** (R13), así que
  R25 de F-013 se cumple sin que F-013 añada nada; y cuando corte, el aviso de
  otro destino (R14) saldrá por el `drive_id` vigente, que F-013 cambiará de IT
  a Posventa. **Ojo para F-013**: con su estrategia `posventa` el paso 2 ya no
  compone la carpeta antes de L1 (solo el nombre), así que en esa estrategia
  `_en_otro_destino` solo podrá comparar nombre y biblioteca; F-013 tendrá que
  decidir si le pasa la carpeta resuelta o si le basta con eso. No se diseña
  aquí.
- **F-031**: cambiará de dónde salen `codigo_obra` y `numero_incidencia` del
  nombrado. Ya viajan en la misma situación (`validacion.codigo_obra`,
  `validacion.numero_incidencia`, F-030), así que F-031 tampoco necesitará una
  consulta más. F-033 no toca el nombrado; cuando F-031 lo mueva, la
  comparación de R14 pasará sola a hacerse contra lo persistido.
