<!-- progress/impl_cierre_manual_F-010.md -->
# F-010 · Cierre documental de las verificaciones manuales · informe incremental

- **Rama:** `feature/F-010-despliegue`
- **Fecha:** 2026-08-25
- **Encargo:** **solo rastro**. Ninguna línea de código, ningún script de
  `infra/`, ninguna llamada a Azure, a SharePoint ni a PostgreSQL. Lo que se
  anota lo **ejecutó el humano** hoy contra el entorno real; el implementer
  únicamente lo escribe donde tiene que quedar.
- **Origen de los datos:** el humano, en el encargo de esta tarea. Contexto
  previo en `progress/review2_F-010.md` §10 (puntos 5 y 6) y en
  `progress/impl_defectos13-15_F-010.md`.
- **Nivel de rigor:** `estandar` (`harness/features.json`). Ver la sección
  «Evidencias» del final: esta ronda **no toca código**, así que la fase RED y
  la campaña de mutación se declaran N/A **con motivo**, no a secas.
- **Estado de F-010 en `harness/features.json`: NO se toca.** Lo decide el
  líder tras el veredicto del reviewer.

## Resumen en una pantalla

| Tarea | Qué se anota | Dónde |
|---|---|---|
| **T15** · resuelve **D4** | La Function App **sí** alcanza `psql-albaranes-rs9k2`. **Sin regla de red nueva.** D4 **cerrada** | `specs/F-010-despliegue/tasks.md` |
| **T17** · criterio de aceptación | Re-ejecutabilidad **demostrada**: ocho recursos reutilizados, cero duplicados, `-SoloFront` sin tocar lo del front, sesión intacta | `specs/F-010-despliegue/tasks.md` |
| **T18** · subida real | Ejecutada **con autorización expresa**, en **tres intentos**. Un solo elemento en la carpeta, ninguno con `(1)` | `specs/F-010-despliegue/tasks.md` **y `specs/F-006-sharepoint/tasks.md`** |
| **T19** · tarjeta del portal | Publicada y funcionando. **Sin el GUID del grupo** | `specs/F-010-despliegue/tasks.md` |
| **T14 bis** | **SIGUE SIN RESULTADO.** Queda escrito como **hueco abierto**, no como hecho | `tasks.md` (nota) y `progress/current.md` |
| **Defecto 16** | El DSN se compone **sin contraseña** a propósito | `progress/current.md` |

---

## T15 · RESUELVE D4 · la Function App SÍ alcanza `psql-albaranes-rs9k2`

Casilla `[x]`, con el resultado escrito en la propia tarea.

**Por qué la evidencia es más fuerte que un «sí»**, y por eso queda contada
entera y no resumida: en el **primer intento** el motor devolvió
`ForeignKeyViolation` sobre `archivos_hash_parte_fkey`. Ese error **solo lo
puede devolver el servidor**, así que prueba **conexión, autenticación y
ejecución** aunque la operación no completara. Un fallo de red o de firewall
no se parece a eso: se parece a un tiempo de espera agotado o a un rechazo de
la conexión.

**Segunda mitad**, ya con el parte sembrado: el archivado **dejó su traza en el
esquema `postventa`** con `estado = archivado`, y con el **nombre y la carpeta
correctos**. Que es literalmente el criterio de esta verificación.

**Lo que NO hizo falta, y es el punto que cerraba la PARADA del enunciado**:
**ninguna regla de red nueva y nada tocado a nivel del servidor compartido**.
La tarea preveía parar si hacía falta, porque `psql-albaranes-rs9k2` lo
comparten albaranes, partes y `datamart-seg-anual` (`CLAUDE.md`). No hizo
falta parar.

**D4 queda cerrada.** El `ForeignKeyViolation` **no** es de D4: es el **defecto
15**, que es de **F-019** y ya está anotado en su ficha.

## T17 · CRITERIO DE ACEPTACIÓN · re-ejecutabilidad demostrada

Casilla `[x]`. Los dos despliegues relanzados **seguidos** y **desde `infra\`**
—que es la corrección del defecto 1—, backend completo y front con
`-SoloFront`.

| Lo que pedía la tarea | Lo que pasó |
|---|---|
| Los dos terminan con código `0` | Sí; **los ocho recursos** salieron como «ya existe, se reutiliza» |
| Ningún recurso duplicado en el grupo | El listado **no tiene ni un duplicado** |
| **El inicio de sesión sigue funcionando después** (R2) | Sí: en **ventana de incógnito** pide sesión y entra, que es además el criterio de **R14** |

**Y el punto que no estaba en la tabla y es el que más vale**: el resumen del
front dijo «**sin tocar (-SoloFront)**» en las **cuatro** líneas que importan
—asignación, permiso de Graph, tokens de ID y credenciales `swa`—. Eso es el
**defecto 8 corregido funcionando contra Azure**, no solo contra su test: era
exactamente el resumen que mentía cuando el modo lo decidía cualquier cosa
menos `$SoloFront`. Y es el escenario que rompió el portal en su día, cuando un
despliegue completo regeneró el secreto y pisó una redirect URI.

## T18 · la subida real, con autorización expresa

Casilla `[x]` **en las dos specs**: `specs/F-010-despliegue/tasks.md` y
`specs/F-006-sharepoint/tasks.md`.

**La autorización**: el humano autorizó el **2026-08-25** con la fórmula
literal «**autorizo T18 ante `CHECKPOINTS.md` C5**». Queda anotada con fecha en
las dos tareas, que es lo que exigían las dos: nombrando C5 y por escrito. Sin
ella, marcar una casilla de una feature ajena **ya cerrada** no era admisible.

**Tres intentos, y los tres se escriben porque los tres enseñan algo.** Anotar
solo el que salió bien habría borrado justo lo que costó descubrir:

| # | Vía | Resultado | Qué enseña |
|---|---|---|---|
| 1 | Host **desnudo** de la Function | **`400`** `Login not supported for provider azureStaticWebApps` | El **defecto 13** en vivo: Easy Auth del backend enlazado. **No es un fallo del despliegue** |
| 2 | **Consola del front con sesión** | **`500`**, con el **PDF ya subido y bien nombrado** | El **defecto 15**: `ForeignKeyViolation`, `archivos` contra `partes`, y nada inserta el parte (es **F-019**). El `500` **dice** que el fichero está arriba: eso es el defecto 14 arreglado |
| 3 | Igual, tras **sembrar el parte sintético** | **Dos llamadas `200`**, **mismo destino**, `estado: archivado`, aviso de reemplazo | El aviso «ya había un fichero con este nombre y se ha reemplazado» **es R16 hablando**: la idempotencia del nombrado, contra una biblioteca real y no contra el doble |

**El criterio de aceptación de F-006, verificado por el humano en la
biblioteca**: **un solo elemento en la carpeta y ninguno con sufijo `(1)`**. Es
el punto que obligaba a **PARAR** y hablar con el humano si fallaba. **No hubo
parada.**

Nombre y carpeta, que sí pueden escribirse porque son sintéticos y ya estaban
en la spec: `0677 - RS26.08 - 0001 PARTE FIRMADO.pdf`, en `Postventa/0677`.

**Consecuencia para F-006**: con esta casilla, **F-006 se queda sin ninguna
verificación manual pendiente**. La sección «El cierre de F-006 necesita
autorización expresa del humano (C5)» de su `tasks.md` describía una condición
que ya no está viva; se ha marcado como **cerrada el 2026-08-25**, conservando
el razonamiento —es el que motiva **F-017**— pero dejando claro que no es una
condición pendiente. También se ha actualizado su fila en el «Resumen de
dependencias externas», que seguía diciendo «DIFERIDA».

> **T17 de F-006 sigue `[ ]`** y **no se ha tocado**: no entra en este encargo
> y el humano no ha aportado su resultado.

## T19 · la tarjeta del portal

Casilla `[x]`. **Publicada y funcionando**, declarado por el humano el
**2026-08-25**. Que no saliera velada para todos significa que el marcador de
`requiredGroupId` se rellenó bien (`design.md` §8).

**El GUID del grupo no entra**: vive solo en `front-portal`, que es donde lo
pone el paso 2 de la tarea. Es la regla de D7 y del propio enunciado.

## T14 bis · SIGUE SIN RESULTADO · hueco abierto

**No se ha inventado nada, y esa es la decisión.** La casilla está `[x]` desde
una ronda anterior, pero el «tope fijado: sí/no» y el «alerta configurada:
sí/no» que su propia verificación exige **no constan en ningún sitio**: el
humano no ha aportado el dato. Es lo que señala `progress/review2_F-010.md`
§10.5, y el implementer **no puede aportarlo**.

**Qué se ha hecho**: dejarlo escrito **como hueco abierto**, no como hecho, en
dos sitios —una nota en la propia tarea y un bloque destacado en
`progress/current.md`— con lo que está en juego dicho en una línea:

> `/api/extraer` y `/api/firma` son **anónimos por diseño** (R32, T8) y **ya
> son alcanzables**, así que el tope de gasto es hoy la única defensa (capa 4
> de `design.md` §9 bis) contra que un desconocido consuma cuota de IA.

**No se ha marcado ni desmarcado la casilla**: se ha dejado como la dejó el
humano, y el hueco es sobre el **resultado**, no sobre la ejecución. Esto es
material para la PARADA 2 del líder: es lo único de F-010 que sigue abierto y
depende solo del humano.

## Defecto 16 · el DSN se compone SIN contraseña, a propósito

Anotado en `progress/current.md`, para quien repita esta verificación.

`dsn_desde_ajustes` **no** mete la contraseña en la cadena de conexión, y es
**deliberado**: así no acaba en un log. Hay que pasarla **aparte** en
`psycopg.connect`, como hace
`services/postventa-api/infrastructure/persistencia/fabrica.py:77`:

```
conexion = psycopg.connect(dsn, password=ajustes.pg_password)
```

Un script de verificación que use `dsn_desde_ajustes` y no lo sepa **muere con
`fe_sendauth: no password supplied`**, y ese mensaje no dice nada de esto. Es
media hora perdida la próxima vez, y por eso queda escrito.

## Los scripts de esta verificación, fuera del repositorio

Añadidos a la lista que ya tenía `progress/current.md` con los de F-003 a
F-005. Viven **en el home del humano** por el motivo de siempre: PowerShell
parte los comandos largos al pegarlos.

| Script | Qué hace |
|---|---|
| `t18_sembrar_parte.py` | Siembra el parte sintético, comprueba su traza y **la borra** al terminar. Es lo que desatasca el defecto 15 mientras F-019 no exista |
| `t18_consola.js` | El fragmento para la consola del front. Su copia versionada está en `docs/DESPLIEGUE.md` §5 bis |
| `t18_logs.ps1` | Lectura de Application Insights |
| `t18_diagnostico.ps1` | Lectura del **cuerpo** de los errores, que es lo que faltaba para leer el 500 mudo |

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `specs/F-010-despliegue/tasks.md` | T15, T17, T18 y T19 a `[x]` con su resultado real; nota de hueco abierto en T14 bis; tabla «Estado de las verificaciones manuales» actualizada (decía «Pendiente» en casi todas) |
| `specs/F-006-sharepoint/tasks.md` | **T18 a `[x]`** citando la autorización y la fecha, con el resultado real contra los tres puntos esperados; sección C5 marcada como cerrada; fila de T18 del resumen de dependencias |
| `progress/current.md` | Bloque de estado nuevo, el hueco abierto de T14 bis, el **defecto 16** y los cuatro scripts |
| `progress/impl_cierre_manual_F-010.md` | **Nuevo**: este informe |

**Ningún fichero de código. Ningún script de `infra/`. Ninguna spec de
`requirements`/`design`.**

## Lo que queda fuera, y por qué

- **El estado de F-010 en `harness/features.json`: NO se ha tocado.** Lo decide
  el líder tras el veredicto del reviewer, y el implementer nunca se marca
  `done` a sí mismo.
- **El resultado de T14 bis.** No es del implementer: ver arriba.
- **`specs/F-010-despliegue/design.md:252` y `requirements.md:227`** siguen
  diciendo que T18 se ejecuta con `verificar_archivo_dev.ps1 -BaseUrl` y que
  ese script «no se modifica». **Siguen siendo falsas**, y ahora además hay una
  tarea ejecutada que las contradice por escrito. Reescribir `requirements` y
  `design` es del **`spec-author`**: se **reitera como residuo**, ya reportado
  en `progress/impl_defectos13-15_F-010.md`.
- **Residuo aún vivo**: `infra/cargar_secretos_postventa.ps1:269` sigue pidiendo
  «once secretos» por pantalla. Toca `infra/`, y este encargo lo prohíbe
  expresamente.
- **T17 de F-006**, que sigue `[ ]`: no entra en el encargo.
- **Nada ejecutado contra Azure, SharePoint ni PostgreSQL.**

## Verificaciones `MANUAL (humano)` que siguen pendientes

**En F-010, ninguna de ejecución.** Lo único abierto es **el resultado de
T14 bis**, y depende solo del humano.

**En F-006, ninguna de las diferidas**: T18 queda cerrada. T17 sigue `[ ]`,
fuera de este encargo.

---

## Evidencias

Medidas, no estimadas. **Esta ronda no toca ni una línea de código**, así que
tres de las cuatro evidencias de la tabla del rol se declaran **N/A con
motivo**, que es lo que `CHECKPOINTS.md` acepta —el N/A a secas, no—.

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** (`bash harness/init.sh`, tal cual) | **17 passed** en la suite del arnés; los dos servicios (`api`, `front`) **en verde por caché de árbol**, que es correcta porque **ningún fichero bajo `services/` se ha tocado** |
| **Tests nuevos en esta ronda** | **Ninguno**, y es lo correcto: no hay comportamiento nuevo que atar. Ningún test del repositorio lee `specs/*/tasks.md`, comprobado (`test_f005_repo_sin_datos_personales.py`, `test_f005_scripts_infra.py` y `test_f006_arquitectura.py` solo lo **citan** en comentarios) |
| **Cobertura de las líneas cambiadas** (línea `PUERTA COBERTURA`) | **`[OK]` 98.5% de 136 líneas cambiadas (134/136, umbral 80%, nivel estandar)**. **Idéntica a la de la ronda anterior**: `harness/alcance.py` solo mide `.py` y aquí solo cambia Markdown, así que el denominador no se mueve |
| **Mutantes generados y supervivientes** | **N/A con motivo**: la campaña muta Python y esta ronda **no cambia ni una línea de Python**. La última campaña vigente es la de `progress/mutacion_F-010.md` (**23 generados, 20 muertos, 3 supervivientes**, los tres el separador decorativo de `dev_server.py`, **analizados y declarados equivalentes**). Relanzarla daría el mismo resultado sobre el mismo código |
| **Fase RED** | **N/A con motivo**: no hay requisito nuevo ni código nuevo. La fase RED exigible por el nivel `estandar` se cumplió en las rondas que sí tocaron código (defectos 8, 9, 11, 12, 13 y 14), con las trazas pegadas en `progress/impl_F-010.md` y `progress/impl_defectos13-15_F-010.md` |
| **Tiempo de ejecución de la suite** | **0.56 s** la suite del arnés (17 tests) en la ejecución final, según la salida del propio `pytest` dentro de `bash harness/init.sh` (2.67 s en la de apertura, en frío). Las de los servicios no se cronometran en esta ronda: sirvieron desde caché |
| **Barrido de identificadores** | Ejecutado sobre el diff completo: **ni una URL, ni un GUID, ni un identificador de suscripción, inquilino, sitio o elemento, ni un importe**. Lo único con forma de identificador son el nombre del fichero sintético y su carpeta, que ya estaban en las dos specs |
| **Portero** | `bash harness/init.sh` **en verde**, tal cual y sin decoración, al terminar |
