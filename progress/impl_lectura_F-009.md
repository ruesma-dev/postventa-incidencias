<!-- progress/impl_lectura_F-009.md -->
# F-009 · Acta de la sesión de solo lectura del 2026-09-15

> **Encargo documental y acotado, de un solo bloque.** Se levanta el acta de la
> sesión de solo lectura que el 2026-09-15 ejecutó el responsable contra el ERP
> de producción para cerrar los huecos 1, 2 y 3 del §9.4 de
> `progress/guion_bloque8_F-009.md`. **Este encargo no ejecutó nada**: ni contra
> el ERP, ni contra `sigrid-api`, ni contra Azure, ni contra PostgreSQL, ni
> ningún script de `infra/`. Los datos llegaron medidos. Lo único que se ejecutó
> aquí es `bash harness/init.sh`.
>
> **El `status` de las features no se ha tocado.** F-009 sigue `blocked` y
> F-026 sigue `in_progress`. Esa decisión es del líder.

## 1 · Qué se ejecutó el 2026-09-15 (y qué no)

Desde el puesto del responsable, con un **envoltorio fuera del repositorio**
(`C:\Users\pgris\lectura_cierre_f009.ps1`, **no versionado**: solo carga las
variables del `.env` y llama a los scripts de `infra/`).

Se lanzaron **cuatro** de los cinco scripts de lectura del §3 del guion —`09`,
`10`, `11` y `12`; el `08` es el común y lo cargan los demás—. **Los cuatro dan
`PASA`.**

**No se escribió nada.** La única ruta del ERP que se tocó fue
`POST /api/sql/read`; la **ventana de escritura (`CIERRE_HABILITADO`) siguió
cerrada todo el tiempo** y no hubo ninguna llamada a `POST /api/cerrar`. En
PostgreSQL, solo lectura y solo del esquema propio.

## 2 · Los dos hallazgos que importan

### 2.1 · El huso NO es UTC: el defecto que el diseño daba por probable no existía

`10_log_cierre_sigrid.ps1` dice **`HORA LOCAL (correcto)`**. En el ERP está
escrito `2026-09-11 10:28:12` (`fec = 20260911`, `hor = 102812`): **0,0 minutos**
de diferencia con la hora local de referencia, 120,0 con la UTC.

Era *la única decisión de la feature que no se pudo tomar con un dato*
(`progress/impl_F-009.md` §3.3.a): `design.md` §7.3 dice «`fec`/`hor` con la
fecha y la hora del cierre» y **no dice en qué huso**. El §0.2 del guion daba el
error por probable y avisaba de que, si hubiéramos escrito UTC, nuestras filas
quedarían una o dos horas por detrás de las 8,4 millones que las rodean **y
nadie lo notaría** hasta el día en que hiciera falta reconstruir cuándo se cerró
algo. **No pasó.**

### 2.2 · Los rotos eran nuestros scripts, no el ERP

**Los cinco scripts de lectura se escribieron el 2026-09-05 y no se había
lanzado ninguno.** De los cuatro probados el 2026-09-15, **tres estaban rotos**.
**Ninguno de los tres fallos era del ERP.** Arreglados y confirmados en el
commit **`a356875`**, cuyo mensaje lleva el detalle:

1. `10` juzgaba el huso contra **AHORA**, con 20 min de tolerancia → leído el
   cierre cuatro días después, habría dicho `NO COINCIDE CON NINGUNA` **por
   construcción**. Nuevo `-InstanteCierreUtc`.
2. `11` preguntaba con `tex = ?` y `dbo.log.tex` es de tipo `text`, sobre el que
   SQL Server no admite `=`: **`500` en dos décimas**, que parece un problema de
   red o de clave. Ahora `LIKE` con patrón literal, y rechaza un texto propio con
   comodines.
3. `12` pasaba el Python con `& $python -c` y PowerShell 5.1 se come las comillas
   dobles. Arreglado con `Invoke-PythonDelServicio`, en el común.

El peor es el **1**: no reventaba, **respondía, y respondía mal** — lo único que
un veredicto automático no se puede permitir. El argumento de fondo queda escrito
en el §10.2 del guion: *utillaje de verificación escrito y nunca ejecutado no es
utillaje, es una intención*.

## 3 · Ficheros tocados

| Fichero | Qué se hizo |
|---|---|
| `progress/guion_bloque8_F-009.md` | **§10 nuevo** (acta completa, 7 subapartados); **enmienda fechada** de la casilla de **T24** (pasos 6, 7 y 9) y de la de **T25**; **actualización del §9.4** (huecos 1-3 `CERRADO`, 4 `REDUCIDO`); nota de vigencia al principio del §9.5 |
| `specs/F-009-cierre-sigrid/tasks.md` | **T25 marcada `[x]`** con su procedencia; **nota fechada del 2026-09-15** bajo el bloque 8 |
| `progress/impl_lectura_F-009.md` | este informe |
| `progress/current.md` | bloque «PARA RETOMAR» sustituido por uno al día |

**No se tocó**: ni el `status` de ninguna feature, ni código de `services/`, ni
`infra/`, ni `azure-apps/`.

## 4 · Decisiones de redacción

1. **Enmendar con fecha, no reescribir.** Las casillas del 2026-09-14 y la tabla
   de ocho huecos del §9.4 **se dejan enteras**; debajo va la enmienda con su
   fecha. Es el patrón que este repositorio ya usaba (la enmienda de la obra
   `0626`, commit `092bf8d`). Una casilla corregida en silencio borra que hubo un
   día en que aquello no se sabía, y eso es justo lo que este bloque vale.
2. **T24 no se marca.** Su contrato son **nueve pasos**. Constan el 4 (parcial),
   el 6, el 7 y el 9; faltan el **2**, el **3**, el **4** (el `estado`), el **5**
   y el **8**. Y el `filas_afectadas: 2` de R22 **no es recuperable hacia atrás**.
   Marcarla sería exactamente el error que el §9.5 llamó «marcar el bloque 8 como
   superado sería falso».
3. **El hueco 4 se reduce, no se cierra.** Que el `usu` del ERP sea `pgris` prueba
   que el login se derivó, se resolvió y **se usó para firmar**. No prueba **R33**
   (correspondencia guardada como confirmada, con `verificado_at_utc`), ni **R31**
   (login inexistente rechazado sin tocar Sigrid), ni que el candidato exista
   exactamente una vez en `dbo.usu`. Se escribe separado, en §10.5 del guion, para
   que nadie lo lea de más.
4. **El defecto 3 no se arregla hoy en `07` y `17`.** Este encargo era documental,
   y aplicar un arreglo a un script que nadie va a ejecutar en la misma sesión
   vuelve a crear el problema del §10.2 con otro nombre. Queda escrito **con
   dueño** (§10.6 del guion, y aviso en `tasks.md`).

## 5 · Qué queda fuera y qué falta

**Del bloque 8 de F-009 quedan cinco huecos**, no ocho (§9.4, actualización):

| # | Hueco | Estado |
|---|---|---|
| 4 | T23 · la siembra del login | **reducido**: faltan R33, R31 y la unicidad del candidato |
| 5 | T22 pasos 2 y 5 · el `503` y que el dry-run no escribe | intacto |
| 6 | T22 paso 4 · las seis cosas de R9 y el bloque `grafico` | intacto, exige ventana abierta |
| 7 | T27 · el reintento sobre lo ya cerrado | intacto, **el único que exige abrir la ventana de escritura**, y el escenario más probable en uso normal |
| 8 | `filas_afectadas: 2` y el `tiemod` de partida | **no recuperable**: solo lo dará el siguiente cierre real |

**Verificaciones MANUAL pendientes**: **T22, T23, T24 y T27** del bloque 8. Las
cuatro siguen sin marcar y ninguna se ha tocado hoy.

**Pendientes con dueño que este encargo deja escritos, no resueltos**:

- `infra/07_alta_usuario_sigrid.ps1` (líneas 161 y 248) y
  `infra/17_traza_grafico_local.ps1` (línea 196) arrastran el defecto de comillas
  de PowerShell 5.1 y **nunca se han ejecutado**. Se estrellarán en la primera
  línea de quien recorra T23 y la precondición de T24.
- **`azure-apps/postventa_incidencias.md` sigue diciendo que «todavía no se ha
  ejecutado ni un cierre real»**, y desde el 2026-09-11 es falso. La regla de
  propiedad de `CLAUDE.md` obliga a corregirlo, y hoy además hay con qué hacerlo
  bien: fecha, incidencia, `ide` de la fila de auditoría y veredicto del huso.
  **No se ha tocado: lo decide el líder.**

## 6 · Fase RED

**No aplica, y el motivo no es una excusa.** Este encargo es **documental**: no
escribe ni una línea de código de producción ni de test. Los cuatro ficheros
tocados son Markdown (`progress/` y `specs/`). No hay requisito EARS que pueda
fallar antes de existir el código, porque no hay código.

La evidencia de esta pieza es de otra naturaleza y está en el §10.3 del guion:
**los cuatro veredictos `PASA` de scripts ejecutados contra el ERP real**, con
sus valores literales. Y tiene, de hecho, su propia fase roja, aunque de otro
encargo: **tres de los cuatro scripts fallaron antes de funcionar**, y los fallos
están escritos con su causa en el mensaje del commit `a356875`.

## 7 · Evidencias

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **62 passed**, más las suites de los dos servicios (`api`, `front`) en verde | salida de `bash harness/init.sh` |
| **Tiempo de ejecución de la suite** | **4,22 s** (`62 passed in 4.22s`) | la propia suite |
| **Cobertura de las líneas cambiadas** | **99,0 %** — `PUERTA COBERTURA: 99.0% de 1340 líneas cambiadas cubiertas (1327/1340, umbral 80%, nivel estandar)` | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados y supervivientes** | **no se lanzó campaña, y no procede**: este encargo **no cambia código ejecutable**. Los cuatro ficheros tocados son Markdown, así que no hay nada que mutar. La campaña de F-009 ya está hecha y analizada: **123 mutantes, 117 muertos, 6 supervivientes, 0 timeouts, 6.124,7 s**, los seis justificados y con **cero `PENDIENTE`** (`progress/mutacion_F-009.md`, T28) | `harness/features.json` + `progress/mutacion_F-009.md` |
| **Veredicto del arnés** | `ENTORNO LISTO. Puedes trabajar.`, **exit code 0** | `bash harness/init.sh` |

**Dos salvedades honestas sobre estos números:**

1. Las suites de `api` y `front` salieron **de la caché** («árbol sin cambios
   desde el último verde»), lo cual es correcto: este encargo no tocó
   `services/`. Es además el riesgo que el encargo **1.7.12 de `arnes-base`**
   tiene anotado y sin implementar.
2. Los **60 avisos de `ruff`** (deuda previa, no bloquean) siguen donde estaban:
   salen de `harness/` y **no son de ninguna feature**. Este encargo no los tocó
   ni los movió.

## 8 · Commits

| Commit | Qué |
|---|---|
| `752f95d` | `progress/guion_bloque8_F-009.md`: §10 nuevo, enmiendas de T24 y T25, actualización del §9.4 |
| `888e094` | `specs/F-009-cierre-sigrid/tasks.md`: T25 marcada y nota fechada del bloque 8 |
| *(este)* | `progress/impl_lectura_F-009.md` |
| *(siguiente)* | `progress/current.md` |

Sin `push`, sin PR, en la rama `feature/F-026-aprobacion-humana`.
