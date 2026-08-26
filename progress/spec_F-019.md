<!-- progress/spec_F-019.md -->
# F-019 · Informe del spec-author

**Fecha**: 2026-08-26 · **Rama**: `feature/F-019-endpoints-persistencia`
**Entregable**: `specs/F-019-endpoints-persistencia/` (requirements, design,
tasks). **Ni una línea de código**: la implementación es del implementer.

---

## 1 · Qué he leído antes de diseñar

`specs/SPECS.md`, la ficha entera de F-019 en `BACKLOG.md`,
`docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/INTEGRACION.md` §8,
`domain/ports/persistencia.py`, `domain/models/persistencia.py`,
`application/pipelines/paso_persistencia.py` y `paso_archivo.py`,
`function_app.py` y los seis handlers de `interface_adapters/api/`,
`infrastructure/persistencia/` (fábrica, repositorio, sentencias y **el DDL de
las seis tablas**), `tests/test_f010_endpoints_protegidos.py`,
`tests/test_f010_integracion_expuesto.py`, el front (`api.js`, `pipeline.js`,
`app.js`) y `progress/review3_F-010.md`.

## 2 · Lo que cambia respecto a lo que parecía la feature

La ficha del backlog la describe como «tres endpoints». **Lo es y no lo es**:
tres endpoints sin más **no matan el defecto 15**. Si el orden depende de que
el llamante haga las cosas bien, vuelve el fallo en cuanto alguien llame a
`/api/archivar` por su cuenta — que es exactamente lo que se hizo el
2026-08-25 para verificar T18.

Por eso el diseño mete una pieza más: **`/api/archivar` escribe la traza del
archivo en estado `pendiente` ANTES de subir nada**. Como
`archivos.hash_parte` tiene clave ajena contra `partes`, esa escritura sólo
puede hacerse si el parte ya consta. **La misma restricción que hoy hace
fallar el proceso después de subir el fichero pasa a hacerlo fallar antes**,
y sin inventar una comprobación paralela que pueda divergir de la restricción
real.

Resultado: el 500 de «el fichero está arriba y falta la traza» se convierte en
un **409** de «guarda el parte primero», **sin haber subido nada**.

## 3 · Las seis decisiones que pedía el encargo, resueltas

1. **Endpoints nuevos vs. integrar en el pipeline** → **ambas cosas, pero no
   como suena**: endpoints nuevos (`POST /api/remesa`, `POST /api/parte`,
   `GET /api/cola`) que **llaman al `paso_persistencia` que ya existe** (no se
   reescribe: hasta hoy no tenía punto de entrada), más la garantía en
   `/api/archivar`. Descartado meter el guardado en `/api/extraer` o
   `/api/validar`: el primero no sabe de qué remesa viene el parte, el segundo
   no recibe el parte troceado, y el front revalida varias veces por parte.
2. **Orden y fallo del guardado** → se **aborta** el archivado. 409 si el parte
   no consta, 503 si la base no responde; en los dos casos **sin subir nada**.
   Un PDF archivado sin fila es un fichero del que el sistema no sabe nada.
3. **Idempotencia** → clave `hash_parte` para parte, validación y traza (ya lo
   garantizan los `upsert` de F-005). **La remesa es el punto flojo y lo digo
   en la spec**: `postventa.remesas` no tiene clave natural y dársela sería
   DDL, que está fuera de alcance. Mitigación: el llamante conserva y reenvía
   el `remesa_id`. No duplica partes; puede dejar una fila de remesa de más.
4. **Autenticación** → he leído `test_f010_endpoints_protegidos.py` y **lo
   respeto**: los tres nuevos van `ANONYMOUS` y el test se amplía a nueve.
   **Pero discuto una cosa distinta del `auth_level`**: `GET /api/cola` es el
   primer endpoint del servicio que devuelve **dato personal acumulado sin que
   el llamante aporte el PDF**. Eso cambia el modelo de amenaza y no lo arregla
   el `auth_level`. Va como **D1**.
5. **Ventana de escritura** → los endpoints nuevos **no** dependen de
   `ARCHIVO_HABILITADO`: escriben en el esquema propio, no en un sistema
   ajeno; atarlos dejaría sin poder guardar el trabajo justo cuando la ventana
   está cerrada, que es como se despliega. Y en `archivar` se **fija con un
   test** que la ventana corta antes de que la base se entere.
6. **Qué NO entra** → escrito en `design.md` §13: F-009 (`guardar_cierre` no se
   expone), preferencias de usuario, F-012, F-013, F-020, la pantalla de cola
   en el front, `usuario_oid`, y **rehidratar la sesión al recargar**.

## 4 · Lo que NO arregla esta feature, y conviene saberlo antes de aprobarla

La ficha atribuye a F-019 dos consecuencias. **Arregla una y media**:

- ✅ **El archivado real puede completar** (defecto 15). Ese es el bloqueo del
  piloto y se muere aquí.
- ✅ **La cola de validación humana sobrevive entre sesiones**: se escribe y se
  lee.
- ⚠️ **Recargar la pestaña sigue perdiendo el trabajo en curso.** Lo guardado
  queda guardado, pero volver a pintarlo exige **leer una remesa entera con
  sus partes**, y para eso hace falta un método de lectura nuevo en
  `RepositorioPartesPort` — que el encargo prohíbe tocar. Va como **D4**, con
  recomendación de feature nueva.

## 5 · Decisiones abiertas para el humano

| # | Qué | Recomendación |
|---|---|---|
| **D1** | `GET /api/cola` anónimo devolviendo observaciones manuscritas de clientes | **Sacarlo `ANONYMOUS`** (cualquier otra cosa rompe el front) con tope de límite, nada al log y el riesgo escrito en la cabecera; **y valorar la restricción de acceso público de la Function App**, que es la única capa real. Opcional encima: exigir `x-ms-client-principal`, que sube el listón pero **no es control de acceso** (base64 sin firma) |
| **D2** | `postventa.remesas` sin clave natural | **Aceptarlo ahora**: no duplica partes. Darle una es DDL |
| **D3** | ¿Guardar `usuario_oid`? | **No en F-019**: la cabecera no está firmada y guardarla invita a confundir traza con identidad verificada |
| **D4** | Rehidratar la sesión al recargar | **Feature nueva**, después de ver el piloto |
| **D5** | ¿Entra el cableado del front (T15–T16)? | **Sí.** Sin él, los endpoints existen y **nadie los llama**: el mismo estado que la feature viene a arreglar, un nivel más arriba. Si el humano dice que no, se caen R24–R27 y T15–T16, y hay que decir al cerrar que el archivado real sigue sin poder completar en el circuito |

## 6 · Alcance en números

- **4 ficheros de código nuevos** (tres handlers + un módulo de parsers
  compartidos) y **7 de test nuevos** (6 Python + 1 JS).
- **13 ficheros modificados**, de los cuales 3 son del front, 2 son
  documentación normativa (`INTEGRACION.md`, `ARCHITECTURE.md`) y 3 son tests
  de F-005/F-006/F-010 que **se aprietan, no se relajan**.
- **0 ficheros SQL**, **0 sentencias DDL**, **0 conexiones reales**. El puerto
  `RepositorioPartesPort` **no gana ni un método**.
- **20 tareas**, con fase RED explícita en 6 de ellas, cobertura, mutación,
  `init.sh` en verde y **una sola verificación `MANUAL (humano)`** (T20: el
  circuito del defecto 15 contra el despliegue, con parte sintético y la
  ventana de escritura abierta sólo para la prueba y cerrada al terminar).

## 7 · Riesgos que el implementer tiene que vigilar

1. **Los tests de F-006 hay que ajustarlos** (ahora `guardar_archivo` se llama
   dos veces en el camino feliz). La tentación es relajar los dobles; la spec
   manda lo contrario: exigir **dos llamadas, en orden `pendiente → archivado`**.
2. **Mover los parsers de `validar.py` a `cuerpos.py`** es mecánico pero está
   en el camino crítico: va en su propio commit (T1) y con
   `test_f004_validar_http.py` **sin tocar** como red.
3. **La garantía de orden depende de que la clave ajena siga en el DDL.** Hoy
   nadie la fija: T12 añade esa aserción al test de texto del DDL.
4. **Una llamada HTTP más por parte en el front**: milisegundos contra un
   presupuesto de 45 s con un peor caso medido de 6,5 s. No es riesgo de
   tiempo, pero conviene medirlo en T20.

## 8 · Cumplimiento de las reglas duras

- Nada contra Azure, SharePoint, PostgreSQL ni Sigrid: **ni una conexión**.
- Sin secretos, sin cadenas de conexión y sin datos personales en la spec (los
  ejemplos usan el parte sintético `0677 / RS26.08 - 0123` que ya está en las
  specs desde F-003).
- `harness/features.json` **sin tocar**: el estado lo mueve el líder.
- `bash harness/init.sh` ejecutado tal cual al terminar: **verde**.
- Commit local en la rama, sin `push` ni PR.
- `azure-apps/`: §8 de `INTEGRACION.md` cambia, así que hay que copiarla allí,
  **pero el humano decidió el 2026-08-20 que los agentes no commitean en ese
  repositorio**. Queda anotado como aviso, no como tarea de agente.

---

# 9 · Segunda ronda (2026-08-26): las cinco decisiones, resueltas

> Esta sección **añade**, no reescribe: lo de arriba es el rastro de la
> primera ronda, incluido el error que la segunda corrige.

## 9.1 · Lo que el humano decidió

| # | Decisión | Efecto en la spec |
|---|---|---|
| **D5** | **SÍ**, el cableado del front entra | R25–R28 y T19–T20 se quedan. Sección E de `requirements.md` con la decisión escrita en cabecera |
| **D2** | Se acepta `remesas` sin clave natural | Sin cambios: ya era la recomendación (§7) |
| **D3** | **No** se guarda `usuario_oid` | R6 deja de citar una decisión abierta y cita la decisión tomada |
| **D4** | Rehidratar la sesión al recargar es **feature nueva** | §13 y §15 lo dan por decidido; T18 y T23 obligan a decirlo al cerrar |
| **D1** | `GET /api/cola` se queda **`ANONYMOUS`**, con el razonamiento **reescrito** | §8 entera, R16, R18, R30, R31 y las tareas T10–T12, T16, T17 |

## 9.2 · En qué se equivocó mi D1, y por qué importa

Escribí que la restricción de acceso público de la Function App «es la única
capa real» y la propuse como **algo a valorar**. Las dos mitades estaban mal:

- **Esa capa ya existe y no hay nada que configurar.** Desde que la Function
  App es **backend enlazado** de la Static Web App, la plataforma le activa
  Easy Auth con el proveedor `azureStaticWebApps` y el backend **sólo acepta lo
  que entra por el proxy del front**. Lo documenta `docs/DESPLIEGUE.md` §5 bis,
  escrito al descubrir el **defecto 13 de F-010** ejecutando contra Azure el
  2026-08-25. El `400` que devuelve el host desnudo —`Login not supported for
  provider azureStaticWebApps`— **no es nuestro**: lo escribe la plataforma
  antes de que la Function se entere.
- **Y no es «la única»**: encima va la regla `/*` con `authenticated` del
  `staticwebapp.config.json`, fijada por
  `services/postventa-front/tests/test_f010_config_swa.py` con guardia y
  control negativo, más la asignación obligatoria al grupo de Posventa.

**Consecuencia**: `auth_level=ANONYMOUS` es **irrelevante desde internet**,
porque nadie alcanza el código sin pasar por el proxy y el proxy exige sesión.
`GET /api/cola` **no queda expuesto a internet**.

Esto no es una corrección cosmética. Mi §8 original habría llevado al humano a
plantearse una configuración de Azure que ya está puesta, y —peor— habría
dejado escrito en una spec que el servicio está más desprotegido de lo que
está. Una spec que exagera un riesgo gasta el mismo crédito que una que lo
esconde: la próxima vez nadie sabe cuál de las dos está leyendo.

**Lo que NO cambia**: el dato personal acumulado sigue siendo real. Lo que
cambia es de quién hay que protegerlo — **un usuario ya autenticado del grupo
de Posventa**, que es justo quien tiene que leer esa cola — y, sobre todo, el
**volumen**: que ninguna llamada se lleve la cola entera.

## 9.3 · Las tres condiciones, incorporadas

1. **Tope duro al `limite`** → **R16** (requisito propio), **T10** (RED) y
   **T11** (implementación). Es lo único de las tres que hoy **no existe a
   nivel de endpoint**: `sentencias._limite_seguro` ya acota entre 1 y
   `LIMITE_MAXIMO_COLA` (500), pero eso es el repositorio. El handler acota
   **también**: dos cinturones, porque el que falla es el que no se ve. Y se
   **acota, no se rechaza**: quien pide la cola es el front, y un número
   absurdo no debe tumbarle la pantalla.
2. **Ningún dato personal al log** → **R18** y **T12**, a imagen de
   `test_f005_logs_sin_datos_personales.py`. Es un test guardián, así que si
   nace verde hay que demostrar que sabría fallar, con el mismo control
   negativo que ya usa F-005.
3. **Cabecera de `test_f010_endpoints_protegidos.py` corregida** → **R31** y
   **T17, en tarea propia** para que no se pierda entre la ampliación a nueve
   endpoints de T16. Hoy abre diciendo que los endpoints «quedan en internet
   con `auth_level=ANONYMOUS`», y eso dejó de ser verdad con el enlace del
   backend. **El test no se relaja**: T17 exige comprobar a mano que sigue
   fallando por las dos vías —cambiar el `auth_level` sin tocar la
   explicación, y borrar la explicación sin tocar el `auth_level`—.

## 9.4 · Descartado, y dicho en la spec

**Exigir `x-ms-client-principal`.** Lo proponía yo mismo como «listón más
alto» y cae por mi propio argumento: va en base64 **sin firma**, así que no es
control de acceso. Puesto encima de algo que ya protege la plataforma, lo
único que consigue es **confundir qué protege de verdad**: el día que alguien
razone sobre este servicio, una comprobación decorativa le hará creer que hay
un control donde no lo hay. Queda escrito como descartado en `design.md` §8.

## 9.5 · Qué queda de la spec después de esta ronda

- **34 requisitos** (antes 32): entran el tope duro (R16), el log limpio (R18)
  y la cabecera del test (R31); la numeración de las secciones C a F se
  desplaza y la tabla de trazabilidad está rehecha.
- **24 tareas** (antes 20), con **7 en fase RED**.
- **8 ficheros de test nuevos** (7 Python + 1 JS) y **13 modificados**.
- Sigue sin haber **DDL**, **métodos nuevos en el puerto** ni **conexiones
  reales**, y `harness/features.json` sigue sin tocarse.
- `bash harness/init.sh`: **verde**.

**La spec queda lista para el implementer.** No hay ninguna decisión esperando
a nadie.
