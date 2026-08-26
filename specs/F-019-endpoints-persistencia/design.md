<!-- specs/F-019-endpoints-persistencia/design.md -->
# F-019 · Diseño técnico

> Se diseña contra `docs/ARCHITECTURE.md` (normativo) y
> `docs/CONVENTIONS.md`. Lo que aquí se decide **no cambia el esquema**: no
> hay DDL nuevo, ni columnas nuevas, ni tablas nuevas. F-005 ya las creó.
>
> **Segunda ronda (2026-08-26)**: el humano ha resuelto las cinco decisiones
> que la primera ronda dejó abiertas. §15 ya no es una lista de preguntas: es
> lo decidido, con su razón. El cambio de fondo está en §8.

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
| `services/postventa-api/tests/test_f019_remesa_http.py` | tests | R1–R6, R34 |
| `services/postventa-api/tests/test_f019_parte_http.py` | tests | R7–R13, R34 |
| `services/postventa-api/tests/test_f019_cola_http.py` | tests | R14–R17, R34 |
| `services/postventa-api/tests/test_f019_logs_sin_datos_personales.py` | tests | R18: los tres endpoints nuevos, con `caplog`, a imagen de `test_f005_logs_sin_datos_personales.py` |
| `services/postventa-api/tests/test_f019_orden_archivado.py` | tests | R19–R24: el corazón de la feature |
| `services/postventa-api/tests/test_f019_referencias_pg.py` | tests | R11/R20: `ForeignKeyViolation` → `ReferenciaNoConsta`, con conexión doble |
| `services/postventa-api/tests/test_f019_documentacion.py` | tests | R32, R33 |
| `services/postventa-front/tests_js/persistencia.test.js` | tests (node) | R25–R28 |

Los dobles de repositorio ya existen (`services/postventa-api/tests/utiles_pg.py`);
se reutilizan y **no se escribe un tercer doble**.

## 4 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/function_app.py` | Tres rutas nuevas (`remesa`, `parte`, `cola`) en `ANONYMOUS`; mapeo de `ReferenciaNoConsta` → **409** en `parte` y en `archivar`; cabecera puesta al día con el modelo de amenaza vigente y con lo que añade `/api/cola` (R30), y las tres entradas nuevas en la lista de endpoints |
| `services/postventa-api/interface_adapters/api/validar.py` | **Sólo** deja de definir los parsers y los importa de `cuerpos.py`. Su comportamiento público no cambia: `test_f004_validar_http.py` es la red que lo demuestra |
| `services/postventa-api/application/pipelines/paso_archivo.py` | Traza previa `pendiente` antes de `_subir` (§5) |
| `services/postventa-api/domain/models/errores.py` | `ReferenciaNoConsta(ErrorDePersistencia)`: la fila referida no existe |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | `_escribir` distingue `psycopg.errors.ForeignKeyViolation` y levanta `ReferenciaNoConsta` en vez de `PersistenciaNoDisponible` |
| `services/postventa-api/tests/test_f006_paso_archivo.py` | Se ajusta a la escritura previa: los dobles pasan a esperar **dos** llamadas a `guardar_archivo` en el camino feliz. **No se debilita ninguna aserción existente** |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | Dos cosas, y **no se mezclan en la misma tarea**: (a) `ENDPOINTS` pasa de seis a **nueve** y la cuenta del control negativo también (R29); (b) su **cabecera** deja de decir que los endpoints quedan «en internet» y pasa a contar el modelo vigente (R31) |
| `services/postventa-api/tests/test_f010_integracion_expuesto.py` | La lista de endpoints de §8 y `NO_DESPLEGADAS` (R32) |
| `services/postventa-front/js/api.js` | `registrarRemesa()`, `guardarParte()`, `cola()` |
| `services/postventa-front/js/pipeline.js` | `procesarParte` guarda tras validar; `cuerpoDeParte` compone el cuerpo de `/api/parte`; `revalidarParte` vuelve a guardar (R26, R28) |
| `services/postventa-front/js/app.js` | Registra la remesa tras `trocear` y conserva `remesaId`; marca no archivable el parte que no se pudo guardar (R25, R27) |
| `docs/INTEGRACION.md` | §8: tres filas nuevas en la tabla de endpoints y corrección de la tabla de «qué NO está desplegado» (R32) |
| `docs/ARCHITECTURE.md` | Paso 6 (**Archivo**): sólo se archiva lo que ya consta guardado, y cómo se garantiza (R33) |

## 5 · La garantía de orden, que es el corazón

### El mecanismo

En `paso_archivo`, **después** de la puerta de aptitud, del nombrado y de la
idempotencia por traza, y **antes** de tocar el puerto de archivo:

```
1. _exigir_apto(ctx)                       # F-006, sin cambios
2. componer_destino(...)                   # F-006, sin cambios
3. si _ya_archivado(...): return           # F-006, sin cambios  (R24)
4. repositorio.guardar_archivo(traza=<pendiente>)   # NUEVO      (R19)
5. _subir(...)                             # carpeta, homónimo, subida
6. traza de éxito / de error               # F-006, sin cambios  (R22)
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

> Reescrito en la segunda ronda. **La primera ronda se equivocó en el tamaño
> del riesgo**: daba por «expuesto a internet» un backend que ya no lo está, y
> proponía «valorar» una capa que lleva puesta desde el 2026-08-25.

`services/postventa-api/tests/test_f010_endpoints_protegidos.py` fija el
criterio y **se respeta**: los tres nuevos van en `ANONYMOUS`, y el test se
amplía a nueve endpoints. `auth_level=FUNCTION` rompería el front el mismo día
—el proxy de la Static Web App autentica al usuario y reenvía
`x-ms-client-principal`, no una clave que la Function pueda exigir— y ningún
test de este repositorio lo notaría.

### Dónde está la protección de verdad: dos capas, y una la pone la plataforma

`docs/DESPLIEGUE.md` §5 bis, escrito al descubrir el **defecto 13 de F-010**
ejecutando contra Azure el 2026-08-25:

1. **El backend enlazado.** Desde que la Function App es backend enlazado de
   la Static Web App, la plataforma le activa **Easy Auth con el proveedor
   `azureStaticWebApps`** y el backend **sólo acepta lo que entra por el proxy
   del front**. Preguntarle por su nombre de host —cualquier ruta,
   `GET /api/health` incluido— devuelve
   `{"code":400,"message":"Login not supported for provider azureStaticWebApps"}`,
   y **ese cuerpo no es nuestro**: lo escribe la plataforma antes de que la
   Function se entere. **No hay que configurar nada**: ya está.
2. **La regla `/*` de la Static Web App.** `staticwebapp.config.json` exige
   `authenticated` en `/*` y en `/api/*`, con el `401` redirigiendo al inicio
   de sesión, y `services/postventa-front/tests/test_f010_config_swa.py` lo
   fija con su guardia y su control negativo. Encima va la asignación
   obligatoria al **grupo de Posventa** en la aplicación empresarial.

**Consecuencia para el diseño**: `auth_level=ANONYMOUS` es **irrelevante desde
internet**, porque nadie alcanza el código sin pasar por el proxy, y el proxy
exige sesión. `GET /api/cola` **no queda expuesto a internet**.

### Lo que sí cambia con `GET /api/cola`, dicho en su tamaño

El dato personal acumulado es real y no desaparece por estar detrás de un
proxy. Lo que cambia es **de quién** hay que protegerlo:

- Los seis endpoints actuales exigen que **tú** aportes el PDF: quien no tiene
  el parte no obtiene nada de él.
- `GET /api/cola` devuelve transcripciones manuscritas de clientes, códigos de
  obra y números de incidencia **sin que el llamante aporte nada**.

Es decir: la amenaza no es «internet anónimo», es **un usuario ya autenticado
del grupo de Posventa** —que es precisamente quien tiene que leer esa cola—
y, sobre todo, **el volumen**: una sola llamada no puede convertirse en un
volcado de la cola entera. De ahí las tres cautelas que sí entran en el
alcance:

1. **Tope duro al `limite`** (**R16**): ninguna llamada puede llevarse más de
   `LIMITE_MAXIMO_COLA` (500) entradas, venga lo que venga en la petición. Es
   lo único de las tres que hoy **no existe a nivel de endpoint** —el
   repositorio ya acota con `sentencias._limite_seguro`, y el handler acota
   también: dos cinturones, porque el que falla es el que no se ve.
2. **Ningún dato personal al log** (**R18**), en los tres endpoints nuevos. Ya
   es regla del proyecto desde F-005 y tiene test propio; lo que aquí se fija
   es que los nuevos **no la rompen**.
3. **La cabecera de `function_app.py` puesta al día** (**R30**): que quien la
   lea salga sabiendo que la protección real es el backend enlazado más la
   regla `/*`, y qué añade la cola a ese cuadro.

### Descartado: exigir `x-ms-client-principal`

La primera ronda lo proponía como «listón más alto». **Se descarta**, y por su
propio argumento: va en base64 **sin firma** y cualquiera que alcanzara la
Function podría fabricarla, así que no es control de acceso. Añadirlo encima
de algo que ya está protegido por la plataforma sólo consigue una cosa mala:
**confundir qué protege de verdad**. El día que alguien tenga que razonar
sobre este servicio, una comprobación decorativa le hará creer que hay un
control donde no lo hay.

### Y la cabecera del test, que hoy miente

`test_f010_endpoints_protegidos.py` documenta un modelo de amenaza
**desactualizado**: abre diciendo que «al desplegar, los seis endpoints de
`function_app.py` quedan en internet con `auth_level=ANONYMOUS`». Eso era
verdad cuando se escribió y dejó de serlo con el enlace del backend. F-019 es
quien toca ese fichero para ampliarlo a nueve, así que es el momento de que
diga la verdad completa (**R31**), en **tarea propia** para que no se pierda
entre la ampliación. **El test no se relaja**: sigue fallando si alguien
cambia el `auth_level` sin reescribir la explicación, o al revés.

## 9 · La ventana de escritura (`ARCHIVO_HABILITADO`)

Los endpoints nuevos **no la miran** (R34), y es una decisión, no un olvido:

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
corta antes de que la base de datos se entere (R23). Hoy pasa por el orden de
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
  al recargar es **feature nueva**, decidido por el humano el 2026-08-26
  (**D4**).
- **F-012** (subir el gráfico a Sigrid), **F-013** (mudar el archivo a la
  biblioteca de Posventa), **F-020** (ajustes de diseño del front: tamaño del
  PDF, caja de observaciones, reparto de la pantalla).
- **Una pantalla de cola en el front.** `GET /api/cola` queda expuesto y
  probado; quién lo pinta y cómo es diseño de front, y F-020 es la feature que
  toca esa pantalla.
- **`usuario_oid`.** Se sigue guardando `NULL` (R6, decidido: **D3**).

## 14 · Riesgos

1. **Ajustar los tests de F-006 puede tapar una regresión.** `paso_archivo`
   pasa a llamar `guardar_archivo` dos veces en el camino feliz. La tentación
   es relajar los dobles («que cuente lo que quiera»). Se hace al revés: los
   dobles pasan a exigir **exactamente dos** llamadas, en orden
   `pendiente → archivado`, y eso es un test nuevo de R19, no un ajuste.
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

## 15 · Decisiones resueltas por el humano (2026-08-26)

**Ninguna queda abierta.** El implementer no tiene que esperar a nadie.

- **D1 · `GET /api/cola` se queda `ANONYMOUS`**, con el razonamiento
  **corregido** en §8. El `auth_level` es irrelevante desde internet: el
  backend enlazado sólo acepta lo que entra por el proxy —y eso lo pone la
  plataforma, no hay nada que configurar—, y el proxy exige `authenticated`
  en `/*` más pertenencia al grupo de Posventa. La amenaza real no es internet
  anónimo, es un usuario ya autenticado del grupo y, sobre todo, el volumen.
  Entran en alcance las tres cautelas de §8: **tope duro al `limite`** (R16,
  lo único que hoy no existe a nivel de endpoint), **nada de dato personal al
  log** (R18) y **la cabecera de `function_app.py` al día** (R30). **Se
  descarta exigir `x-ms-client-principal`**: seguridad decorativa sobre algo ya
  protegido, que sólo confunde qué protege de verdad.

- **D2 · `postventa.remesas` se queda sin clave natural** (§7). No duplica
  partes, que es lo que prohíbe `docs/ARCHITECTURE.md` §9; puede dejar una
  fila de remesa de más si alguien resube sin conservar el `remesa_id`.
  Dársela sería DDL, y el DDL está fuera de alcance.

- **D3 · `usuario_oid` sigue en `NULL`** (R6). La cabecera de identidad no
  está firmada y guardarla invitaría a confundir traza con identidad
  verificada.

- **D4 · Rehidratar la sesión al recargar es feature nueva**, no F-019. Exige
  un método de lectura nuevo en `RepositorioPartesPort`, prohibido aquí.
  Queda dicho en §13 y hay que decirlo también al cerrar la feature: **lo
  guardado queda guardado y la cola sobrevive, pero recargar sigue perdiendo
  el trabajo en curso**.

- **D5 · El cableado del front ENTRA en F-019** (R25–R28, tareas T19–T20). Sin
  él los endpoints existirían y nadie los llamaría: el mismo estado que esta
  feature viene a arreglar, un nivel más arriba, y el archivado real seguiría
  sin poder completar en el circuito del piloto.
