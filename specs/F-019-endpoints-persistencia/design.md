<!-- specs/F-019-endpoints-persistencia/design.md -->
# F-019 · Diseño técnico

> Se diseña contra `docs/ARCHITECTURE.md` (normativo) y
> `docs/CONVENTIONS.md`. Lo que aquí se decide **no cambia el esquema**: no
> hay DDL nuevo, ni columnas nuevas, ni tablas nuevas. F-005 ya las creó.

## 1 · Qué se construye, en una frase

Tres endpoints sobre puertos que ya existen —registrar la remesa, guardar el
parte con su veredicto, leer la cola— y **una garantía de orden** en
`/api/archivar`: no se sube un byte a SharePoint de un parte que no conste
guardado.

## 2 · El reparto: endpoints propios *y* el pipeline existente

Decisión pedida explícitamente por el encargo. Las tres opciones y por qué
gana la tercera:

| Opción | Qué sería | Por qué no / por qué sí |
|---|---|---|
| **O1 · integrar el guardado en los endpoints actuales** | Que `/api/extraer` y `/api/validar` guarden por su cuenta | **No.** `/api/extraer` recibe un parte **suelto** y no sabe de qué remesa viene; `/api/validar` no recibe el `parte` troceado (ni su origen, ni sus páginas, ni su modo de detección) y no podría rellenar `postventa.partes`. Además convertiría dos endpoints hoy **sin efecto externo** en endpoints que escriben, y el front revalida a mano varias veces por parte (F-007 R17): cada revalidación sería una escritura |
| **O2 · sólo endpoints nuevos, y que el front los llame en orden** | Lo que pide la ficha del backlog, literal | Insuficiente **por sí solo**: si el front se equivoca —o alguien llama a `/api/archivar` a mano, que es exactamente lo que se hizo en T18— vuelve el defecto 15, y vuelve en su peor forma: fichero arriba y sin traza |
| **O3 · endpoints nuevos + garantía en `/api/archivar`** | Lo que se implementa | El front hace lo correcto **y** el backend lo exige. El orden deja de depender de la disciplina del llamante |

`application/pipelines/paso_persistencia.py` **no se reescribe**: se llama.
Está escrito exactamente para esto —recibe el `ContextoParte`, el repositorio,
el `remesa_id` y el `ahora`— y hasta hoy no tenía punto de entrada. Lo único
que faltaba era el adaptador HTTP que lo compone, que es lo que manda
`docs/CONVENTIONS.md`: la composición vive en el punto de entrada y nunca
dentro de un paso.

## 3 · Ficheros a crear

| Ruta | Capa | Qué hace |
|---|---|---|
| `services/postventa-api/interface_adapters/api/cuerpos.py` | interface_adapters | Los parsers de cuerpo **compartidos**: `bloque()`, `a_extraccion()`, `a_campo()`, `a_traza()`, `a_lectura_de_firma()` y sus constantes de claves. Salen de `validar.py` tal cual (§4) |
| `services/postventa-api/interface_adapters/api/remesa.py` | interface_adapters | `registrar_remesa(cuerpo, *, repositorio=None, ahora=None) -> dict`. Compone el repositorio y llama a `guardar_remesa` |
| `services/postventa-api/interface_adapters/api/parte.py` | interface_adapters | `guardar_parte_http(cuerpo, *, repositorio=None, ahora=None) -> dict`. Reconstruye `ParteTroceado` + `ExtraccionParte` + `LecturaFirma`, **recalcula** el veredicto con `validar_parte` y llama a `paso_persistencia` |
| `services/postventa-api/interface_adapters/api/cola.py` | interface_adapters | `leer_cola(limite=None, *, repositorio=None) -> dict`. Llama a `cola_validacion_humana` y serializa |
| `services/postventa-api/tests/test_f019_remesa_http.py` | tests | R1–R6 |
| `services/postventa-api/tests/test_f019_parte_http.py` | tests | R7–R13 |
| `services/postventa-api/tests/test_f019_cola_http.py` | tests | R14–R17 |
| `services/postventa-api/tests/test_f019_orden_archivado.py` | tests | R18–R23: el corazón de la feature |
| `services/postventa-api/tests/test_f019_referencias_pg.py` | tests | R11/R19: `ForeignKeyViolation` → `ReferenciaNoConsta`, con conexión doble |
| `services/postventa-api/tests/test_f019_documentacion.py` | tests | R29–R31 |
| `services/postventa-front/tests_js/persistencia.test.js` | tests (node) | R24–R27 |

Los dobles de repositorio ya existen (`services/postventa-api/tests/utiles_pg.py`);
se reutilizan y **no se escribe un tercer doble**.

## 4 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | Tres rutas nuevas (`remesa`, `parte`, `cola`) en `ANONYMOUS`; mapeo de `ReferenciaNoConsta` → **409** en `parte` y en `archivar`; ampliación de la cabecera con el riesgo nuevo de `/api/cola` (R29) y con las tres entradas en la lista de endpoints |
| `services/postventa-api/interface_adapters/api/validar.py` | **Sólo** deja de definir los parsers y los importa de `cuerpos.py`. Su comportamiento público no cambia: `test_f004_validar_http.py` es la red que lo demuestra |
| `services/postventa-api/application/pipelines/paso_archivo.py` | Traza previa `pendiente` antes de `_subir` (§5) |
| `services/postventa-api/domain/models/errores.py` | `ReferenciaNoConsta(ErrorDePersistencia)`: la fila referida no existe |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | `_escribir` distingue `psycopg.errors.ForeignKeyViolation` y levanta `ReferenciaNoConsta` en vez de `PersistenciaNoDisponible` |
| `services/postventa-api/tests/test_f006_paso_archivo.py` | Se ajusta a la escritura previa: los dobles pasan a esperar **dos** llamadas a `guardar_archivo` en el camino feliz. **No se debilita ninguna aserción existente** |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | `ENDPOINTS` pasa de seis a **nueve** y la cuenta del control negativo también (R28) |
| `services/postventa-api/tests/test_f010_integracion_expuesto.py` | La lista de endpoints de §8 y `NO_DESPLEGADAS` (R30) |
| `services/postventa-front/js/api.js` | `registrarRemesa()`, `guardarParte()`, `cola()` |
| `services/postventa-front/js/pipeline.js` | `procesarParte` guarda tras validar; `cuerpoDeParte` compone el cuerpo de `/api/parte`; `revalidarParte` vuelve a guardar (R25, R27) |
| `services/postventa-front/js/app.js` | Registra la remesa tras `trocear` y conserva `remesaId`; marca no archivable el parte que no se pudo guardar (R24, R26) |
| `docs/INTEGRACION.md` | §8: tres filas nuevas en la tabla de endpoints y corrección de la tabla de «qué NO está desplegado» (R30) |
| `docs/ARCHITECTURE.md` | Paso 6 (**Archivo**): sólo se archiva lo que ya consta guardado, y cómo se garantiza (R31) |

## 5 · La garantía de orden, que es el corazón

### El mecanismo

En `paso_archivo`, **después** de la puerta de aptitud, del nombrado y de la
idempotencia por traza, y **antes** de tocar el puerto de archivo:

```
1. _exigir_apto(ctx)                       # F-006, sin cambios
2. componer_destino(...)                   # F-006, sin cambios
3. si _ya_archivado(...): return           # F-006, sin cambios  (R23)
4. repositorio.guardar_archivo(traza=<pendiente>)   # NUEVO      (R18)
5. _subir(...)                             # carpeta, homónimo, subida
6. traza de éxito / de error               # F-006, sin cambios  (R21)
```

El paso 4 escribe una fila en `postventa.archivos` con
`estado='pendiente'`, el `nombre_fichero` y la `carpeta` que se van a usar, y
sin `archivado_at_utc`. **Si el parte no consta en `postventa.partes`, esa
escritura no puede hacerse**: la clave ajena `archivos_hash_parte_fkey` —la
misma que produjo el defecto 15— la rechaza. El error sube y el archivado se
aborta **sin haber llamado a nadie**.

Es decir: la misma restricción que hoy hace fallar el proceso **después** de
subir el fichero pasa a hacerlo fallar **antes**. No se añade una comprobación
paralela que pueda divergir de la restricción real; se usa la restricción.

### Por qué así y no de las otras cinco maneras

| Alternativa | Por qué se descarta |
|---|---|
| **Un método de lectura nuevo en el puerto** (`consta_parte`) | Toca `RepositorioPartesPort`, que es de F-005, y el encargo dice «los endpoints que faltan sobre los puertos que YA existen». Y sería una comprobación **aparte** de la restricción: entre el `SELECT` y el `INSERT` cabe todo |
| **Que `/api/archivar` guarde el parte él mismo** | El handler sólo tiene `codigo_obra` y `numero_incidencia`: su `ExtraccionParte` lleva los otros siete campos vacíos **a propósito** (para que el DNI y las observaciones no viajen otra vez). `upsert_parte` pisa todas las columnas salvo `hash_parte` y `primera_vez_at_utc`, así que archivar **borraría** la promoción, la unidad, la descripción, el DNI y las observaciones ya guardadas. Es peor que el defecto que arregla |
| **Que `/api/archivar` acepte el cuerpo completo del parte** | Obligaría al front a reenviar dato personal en cada archivo, que es justo lo que `archivar.py` evita hoy por escrito |
| **Capturar `ForeignKeyViolation` después de subir y avisar mejor** | Es el defecto 14, ya hecho: el mensaje es bueno y el fichero sigue arriba sin traza |
| **Confiar en que el front llame en orden** | O2 de §2: se rompe en cuanto alguien llama al endpoint a mano |
| **Una transacción que abarque subida y traza** | SharePoint no participa de la transacción de PostgreSQL. No existe |

### Qué pasa si el guardado previo falla (decisión pedida)

| Situación | Excepción | HTTP | Qué se ha subido |
|---|---|---|---|
| El parte no consta guardado | `ReferenciaNoConsta` | **409** — «este parte no consta guardado: guárdalo con `POST /api/parte` antes de archivarlo» | **Nada** |
| La base no responde | `PersistenciaNoDisponible` | **503** — «no se ha subido nada, se puede reintentar» | **Nada** |
| Falta configuración de PG | `ConfiguracionPgIncompleta` | **503** (ya existía) | **Nada** |

**Sí, se aborta el archivado.** Un parte archivado sin fila en la base es un
PDF en la biblioteca de Posventa del que el sistema no sabe nada: no se puede
saber si está archivado, la idempotencia de F-006 no lo ve, y el día del
cierre en Sigrid nadie lo relaciona con su incidencia. Es preferible un 409
que dice exactamente qué hacer.

**El 500 `ArchivoSinTraza` sigue existiendo** —fichero arriba, traza final
imposible— pero pasa a ser casi imposible: cuando se llega al paso 6, la fila
de `archivos` ya existe (la escribió el paso 4), así que el `INSERT ... ON
CONFLICT` final no puede violar ninguna clave ajena. Sólo lo levantaría una
caída de la base **entre** el paso 4 y el 6. No se retira: sigue siendo la
única forma honesta de contar ese caso.

## 6 · Los contratos HTTP

### `POST /api/remesa`

```jsonc
// petición
{"nombre_origen": "Mirasierra.pdf", "num_partes": 22,
 "avisos": ["..."], "remesa_id": "…uuid…"}   // avisos y remesa_id opcionales
// respuesta 200
{"remesa_id": "…uuid…", "resultado": "creado"}
```

### `POST /api/parte`

**El cuerpo es el de `POST /api/validar` más dos claves.** Deliberado: el
front ya compone ese cuerpo (`pipeline.js::cuerpoDeValidacion`) y así no hay
dos formas de describir el mismo parte, que es como divergen los contratos.

```jsonc
// petición
{"remesa_id": "…uuid…",
 "parte": {"hash": "…", "origen": "Mirasierra.pdf",
           "paginas_origen": [3], "modo_deteccion": "una_pagina_por_parte"},
 "extraccion": { …tal cual lo devuelve /api/extraer, con las ediciones… },
 "firma":      { …tal cual lo devuelve /api/firma… }}
// respuesta 200
{"hash_parte": "…", "resultado_parte": "creado",
 "resultado_validacion": "creado", "avisos": []}
```

Sin `contenido_b64`: **los bytes no entran** (R12). `ParteTroceado.contenido`
se reconstruye como `b""`, que es lo que `upsert_parte` ignora de todas
formas.

El veredicto **se recalcula aquí** (R8) con `validar_parte`, que es dominio
puro y no gasta IA. Así lo guardado es lo que dicen las reglas sobre los datos
recibidos, y no lo que el llamante quiera contar.

### `GET /api/cola?limite=50`

```jsonc
{"total": 2,
 "entradas": [{"hash_parte": "…", "codigo_obra": "0677",
               "numero_incidencia": "RS26.08 - 0123",
               "observaciones": "…texto manuscrito…",
               "confianza_observaciones": 91,
               "clasificacion_firma": "humana",
               "motivos": [{"codigo": "…", "texto": "…"}],
               "validado_at_utc": "2026-08-26T09:00:00+00:00"}]}
```

`motivos` se serializa **igual que en `/api/validar`**: mismo concepto, mismo
JSON.

## 7 · Idempotencia: con qué clave se decide que algo ya está guardado

| Qué | Clave | Qué pasa al repetir |
|---|---|---|
| **Parte** | `hash_parte` (la huella del PDF troceado que produce F-002) | `upsert_parte` actualiza la fila, conserva `primera_vez_at_utc` e incrementa `reprocesos`. Devuelve `actualizado` |
| **Validación** | `hash_parte` (PK, 1:1) | Sustituye el veredicto anterior. Nunca acumula |
| **Traza de archivo** | `hash_parte` (PK) | Una fila por parte, siempre |
| **Remesa** | `id` (uuid) — **lo aporta el llamante** | Con el mismo `remesa_id`, actualiza. Sin `remesa_id`, se crea una remesa nueva |

**El caso incómodo, dicho en voz alta**: `postventa.remesas` no tiene clave
natural —ni hash del fichero, ni nombre único— y esta feature **no puede
dársela** sin tocar el DDL, que está fuera de alcance. Consecuencia: si
alguien vuelve a subir el mismo PDF en otra sesión sin conservar el
`remesa_id`, se crea una **segunda fila de remesa**, y los partes se
re-asocian a ella (`remesa_id` se pisa en el `upsert`). La primera queda con
su `num_partes` y sin partes colgando.

Eso **no duplica ningún parte** —que es lo que prohíbe
`docs/ARCHITECTURE.md` §9— y no rompe nada, pero ensucia el histórico de
remesas. Se mitiga con lo barato: el front conserva el `remesa_id` mientras
dure la remesa en pantalla y lo reenvía. Darle clave natural a `remesas` sería
DDL, y va como decisión abierta **D2**.

## 8 · Autenticación de los endpoints nuevos

`services/postventa-api/tests/test_f010_endpoints_protegidos.py` fija el
criterio y **se respeta**: los tres nuevos van en `ANONYMOUS`, y el test se
amplía a nueve endpoints. El motivo no ha cambiado: el proxy de la Static Web
App autentica al usuario, reenvía `x-ms-client-principal` y **no aporta**
ninguna clave que la Function pueda exigir. `auth_level=FUNCTION` rompería el
front el mismo día, y ningún test de este repositorio lo notaría.

**Pero hay que discutir una cosa, y no es el `auth_level`.** `GET /api/cola`
es cualitativamente distinto de los seis actuales:

- Los seis actuales exigen que **tú** aportes el PDF: quien no tiene el parte,
  no obtiene nada de él. Su riesgo es gastar cuota de IA, y por eso el tope de
  gasto es la defensa proporcionada.
- `GET /api/cola` **devuelve dato personal acumulado sin que el llamante
  aporte nada**: transcripciones manuscritas de clientes, códigos de obra y
  números de incidencia de partes reales. Es el primer endpoint de este
  servicio que lee de la base y publica lo que hay dentro.

Eso cambia el modelo de amenaza y **no lo resuelve el `auth_level`**. Va como
decisión abierta **D1** con recomendación. Lo que sí hace esta feature en
cualquier caso:

1. **Ampliar la cabecera de `function_app.py`** para que quien la lea se
   entere del riesgo nuevo (R29) — hoy la cabecera argumenta sobre seis
   endpoints que no devuelven nada de nadie.
2. **Tope de `limite`** (R15): un curioso no se lleva la cola entera de un
   tirón, y `LIMITE_MAXIMO_COLA` ya existe.
3. **Nada de datos personales al log** (R17).

## 9 · La ventana de escritura (`ARCHIVO_HABILITADO`)

Los endpoints nuevos **no la miran** (R32), y es una decisión, no un olvido:

- Esa ventana protege **la biblioteca de SharePoint**, que es un sistema
  ajeno y compartido. Guardar en `postventa.partes` es escribir en el esquema
  propio de este proyecto, que es exactamente para lo que se creó.
- Si los ataran, con la ventana cerrada —que es como se despliega— no se
  podría guardar el trabajo de revisión **ni leer la cola**, es decir, no se
  podría hacer nada de lo que esta feature viene a permitir.

Efecto neto en el entorno desplegado con la ventana cerrada: se sube la
remesa, se trocea, se extrae, se valida, **se guarda** y se lee la cola; sólo
`POST /api/archivar` responde 503.

Y en `archivar.py` **se conserva el orden de composición actual**: el
archivador se construye antes que el repositorio, así que la ventana cerrada
corta antes de que la base de datos se entere (R22). Hoy pasa por el orden de
evaluación de los argumentos; con F-019 pasa a estar **fijado por un test**,
porque ahora hay una escritura previa que sí importa que no ocurra.

## 10 · Encaje hexagonal y límite de microservicio

- **domain**: sólo se añade una excepción (`ReferenciaNoConsta`). Ni una regla
  de negocio nueva: el veredicto lo sigue emitiendo `validar_parte` de F-004.
- **application**: `paso_persistencia` se usa tal cual; `paso_archivo` gana
  **una llamada** al puerto que ya recibe. Ninguno de los dos conoce SQL,
  PostgreSQL ni HTTP.
- **infrastructure**: `repositorio_pg` afina la traducción de un error de
  `psycopg` a un error de dominio. Es su trabajo: es la única pieza que sabe
  qué es una `ForeignKeyViolation`.
- **interface_adapters**: los tres handlers nuevos, que es donde se componen
  los adaptadores.

**Límite de microservicio**: todo lo de esta feature es de `postventa-api` y
de nadie más. No se toca Sigrid, ni el catálogo del portal, ni `front-portal`.
El cableado del front es de `postventa-front`, que vive en este mismo
monorepo y es el consumidor natural de estos endpoints; no mezcla
responsabilidades porque no le añade ninguna: le añade **llamadas**.

## 11 · SQL

**Ninguno.** No se crea ni se modifica ningún fichero de
`services/postventa-api/infrastructure/persistencia/sql/`, no se ejecuta DDL y
no se toca el servidor compartido `psql-albaranes-rs9k2`. Las seis tablas y la
clave ajena que sostiene toda esta feature ya existen desde F-005.

## 12 · Ficheros que NO se tocan (los que tientan)

- `services/postventa-api/domain/ports/persistencia.py` — **ni un método
  nuevo**. Es la restricción dura del encargo, y §5 explica cómo se cumple.
- `services/postventa-api/infrastructure/persistencia/sql/*.sql`,
  `ddl.py`, `arranque.py`, `conexion.py` — nada de DDL ni de sesión.
- `services/postventa-api/infrastructure/persistencia/sentencias.py` y
  `mapeo.py` — el SQL que hace falta ya está escrito.
- `services/postventa-api/domain/models/validacion.py`, `firma.py`,
  `extraccion.py`, `nombrado.py` — las reglas de F-003/F-004/F-006 no cambian.
- `services/postventa-api/interface_adapters/api/split.py`, `extraer.py`,
  `firma.py`, `health.py` — ninguno gana efectos (§2, O1).
- `services/postventa-api/interface_adapters/api/archivar.py` — **sólo si hace
  falta**: la excepción nueva sube sin traducir, que es lo que ya hace con las
  demás. Si no hay que cambiar una línea, no se cambia.
- `infra/*.ps1`, `host.json`, `staticwebapp.config.json` — no hay recurso
  nuevo, ni variable nueva, ni ruta nueva que declarar en el proxy (`/api/*`
  ya está enrutado entero).
- `harness/features.json` — el estado lo mueve el líder.

## 13 · Qué NO entra en F-019

- **F-009 / cierre en Sigrid.** `guardar_cierre` **no** se expone: no hay
  endpoint de cierre en esta feature, ni dry-run, ni nada que escriba en el
  ERP.
- **Preferencias de usuario.** `RepositorioPreferenciasPort` no se expone: la
  preferencia de auto-cierre sólo tiene sentido con F-009 delante.
- **Rehidratar la sesión al recargar el navegador.** Es lo que pedía la
  decisión D4 de F-007 y **no cabe aquí**: leer una remesa entera con sus
  partes exige un método de lectura nuevo en `RepositorioPartesPort`, y el
  encargo prohíbe tocar el puerto. Lo que F-019 sí arregla es que **el trabajo
  quede guardado** y que la cola sobreviva entre sesiones; pintarlo de vuelta
  al recargar es otra feature (decisión abierta **D4**).
- **F-012** (subir el gráfico a Sigrid), **F-013** (mudar el archivo a la
  biblioteca de Posventa), **F-020** (ajustes de diseño del front: tamaño del
  PDF, caja de observaciones, reparto de la pantalla).
- **Una pantalla de cola en el front.** `GET /api/cola` queda expuesto y
  probado; quién lo pinta y cómo es diseño de front, y F-020 es la feature que
  toca esa pantalla.
- **`usuario_oid`.** Se sigue guardando `NULL` (R6, decisión abierta **D3**).

## 14 · Riesgos

1. **Ajustar los tests de F-006 puede tapar una regresión.** `paso_archivo`
   pasa a llamar `guardar_archivo` dos veces en el camino feliz. La tentación
   es relajar los dobles («que cuente lo que quiera»). Se hace al revés: los
   dobles pasan a exigir **exactamente dos** llamadas, en orden
   `pendiente → archivado`, y eso es un test nuevo de R18, no un ajuste.
2. **Mover los parsers de `validar.py` a `cuerpos.py`.** Es mecánico y
   `test_f004_validar_http.py` lo cubre entero, pero es un movimiento de
   código en el camino crítico. Va en su propia tarea y su propio commit, sin
   ninguna otra cosa dentro.
3. **Una llamada HTTP más por parte en el front** (R25). Es una escritura en
   PostgreSQL, del orden de milisegundos, y el presupuesto que aprieta son los
   45 s del proxy con `/api/extraer` en 6,5 s de peor caso medido. No es un
   riesgo de tiempo; sí conviene medirlo en la verificación manual.
4. **`ForeignKeyViolation` es la señal, y depende de que el DDL siga como
   está.** Si alguien quitara la clave ajena de `archivos`, la garantía de
   orden desaparecería en silencio. Se mitiga con el test que ya existe
   (`test_f005_ddl_idempotente_texto.py` lee el DDL como texto) y con una
   aserción nueva ahí: la clave ajena de `archivos` contra `partes` es un
   requisito, no un detalle.

## 15 · Decisiones abiertas (del humano, no del spec-author)

- **D1 · `GET /api/cola` es anónimo y devuelve datos personales de clientes.**
  ¿Se acepta mientras la restricción de acceso público de la Function App no
  esté aplicada?
  - **O1 (recomendada)**: sacarlo **ANONYMOUS como los demás**, con el tope de
    `limite`, sin datos personales al log y con el riesgo escrito en la
    cabecera; y **pedir al humano** que valore aplicar la restricción de
    acceso público de la Function App, que es la única capa que de verdad
    impide llamar al backend por fuera del proxy. Es lo coherente con el
    montaje: cualquier otra cosa rompe el front.
  - **O2**: exigir que la petición traiga `x-ms-client-principal` con un `oid`
    legible. **No es control de acceso** —es base64 sin firma y cualquiera la
    fabrica—, pero sube el listón del curioso y deja traza. Cuesta poco.
  - **O3**: no exponer la cola hasta que haya autenticación real. Deja F-004
    sin su cola otra vez y no arregla el defecto 15, que es lo urgente.
  - **Mi recomendación: O1, y O2 encima si el humano quiere el listón más
    alto.** Lo que no recomiendo es esperar: el defecto 15 bloquea el piloto.

- **D2 · `postventa.remesas` no tiene clave natural** (§7). ¿Se le añade una
  —hash del fichero de origen, con su índice único— en una feature futura, o
  se acepta que resubir la misma remesa deje una fila de remesa de más?
  - **Recomendación: aceptarlo ahora** (no duplica partes, que es lo que
    importa) y tratarlo, si molesta, cuando toque volver a tocar el DDL. Aquí
    sería salirse del alcance y del schema.

- **D3 · `usuario_oid`.** ¿Se empieza a guardar el `oid` de quien sube la
  remesa, leído de `x-ms-client-principal`?
  - **Recomendación: no en F-019.** Es dato personal seudónimo, la cabecera no
    está firmada, y guardarla invita a confundir traza con identidad
    verificada. Cuando haya autenticación real (o D1/O2), se decide entera.

- **D4 · Rehidratar la sesión al recargar** (§13). Exige método de lectura
  nuevo en `RepositorioPartesPort`, prohibido aquí.
  - **Recomendación: feature nueva en el backlog**, después de ver el piloto:
    puede que con el trabajo ya guardado y la cola legible, recargar duela
    mucho menos de lo que parecía cuando se anotó D4 en F-007.

- **D5 · ¿Entra el cableado del front en F-019?** (§4, R24–R27, tareas T12–T14).
  - **Recomendación: sí.** Sin él, los endpoints existen y nadie los llama:
    exactamente el estado que esta feature viene a arreglar, sólo que un nivel
    más arriba. Si el humano prefiere backend puro, se caen T12–T14 y R24–R27
    sin tocar nada más — pero entonces **el archivado real sigue sin poder
    completar**, y hay que decirlo al cerrar.
