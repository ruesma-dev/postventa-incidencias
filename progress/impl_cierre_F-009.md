<!-- progress/impl_cierre_F-009.md -->
# F-009 · Acta del bloque 8: qué quedó verificado de hecho, y qué no

> **Encargo** (2026-09-14): F-009 sigue `blocked` desde el 2026-09-06 esperando
> a F-012. F-012 y F-025 ya están cerradas y **el cierre real se ejecutó contra
> el ERP de producción**, así que buena parte de lo que verificaba el bloque 8
> de F-009 **ya ocurrió**, dentro de la verificación de otras features.
> Averiguar **exactamente** qué quedó cubierto y qué no, y dejarlo escrito.
>
> **Trabajo documental.** No cambia ni una línea de código de producción.
> **No se ejecutó nada** contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint: toda la evidencia estaba escrita.

## 1 · Qué se ha hecho

Tres cosas, en tres commits:

| Commit | Qué |
|---|---|
| `092bf8d` | **El acta** en `progress/guion_bloque8_F-009.md`: casillas de T22–T27 rellenas, enmienda fechada de la obra, y un **§9** nuevo con la evidencia, los huecos y el veredicto |
| `ff5fb6a` | **Las marcas** en `specs/F-009-cierre-sigrid/tasks.md`: **solo T26** del bloque 8, más **T29**; cada una diciendo de dónde sale |
| *(este)* | Informe y bloque de estado en `progress/current.md` |

### Ficheros tocados

- `progress/guion_bloque8_F-009.md` — **el grueso**. Acta arriba, enmienda de
  la obra, seis casillas rellenas, §9 nuevo (≈120 líneas), y dos notas fechadas
  en los pasos 4 y 5 de §6.
- `specs/F-009-cierre-sigrid/tasks.md` — nota fechada bajo el bloque 8; **T26**
  y **T29** marcadas `[x]` con la procedencia de cada marca escrita dentro.
- `progress/impl_cierre_F-009.md` — este informe.
- `progress/current.md` — bloque de estado.

**Ningún fichero de código, ningún test, ninguna dependencia.**

## 2 · Lo que se averiguó: el mapa entre los dos bloques

El **2026-09-11**, verificando **F-012**, el responsable recorrió el circuito
completo contra el ERP sobre **`RS26.09/0150`** de la obra **`0626`** —una obra
**en uso**—. Cinco llamadas, **las cinco `200`**, medidas en
`appi-postventa-dev` (`progress/guion_bloque9_F-012.md` §9.2):

| Hora (UTC) | Ruta | Duración | Qué es **para F-009** |
|---|---|---|---|
| `08:27:15` | `archivar` | 1.756 ms | la precondición **P5** |
| `08:27:42` | `cerrar` | 4.424 ms | **el dry-run de T22** |
| `08:28:03` | `adjuntar` | 8.471 ms | la precondición añadida de **T24** (R2 de F-012) |
| `08:28:12` | `cerrar` | 472 ms | **el cierre real de T24**, y con él **T26** |

Más lo que ningún registro da: **el responsable abrió la ficha en Sigrid y vio
la reclamación cerrada con su parte dentro**.

**El veredicto en una línea: el cierre real está acreditado; sus
comprobaciones, casi ninguna.** Ninguno de los cinco scripts de lectura de
`infra/` se ha ejecutado jamás, así que de los nueve pasos del contrato de T24
solo constan **uno y medio**.

### Tarea por tarea

| Tarea | Marcada | Por qué |
|---|---|---|
| **T22** dry-run real | **no** | consta que el dry-run **funciona** (`200`, 4,4 s) y que **no exige el gráfico** (R50 de F-012); **nada de su contenido** (las seis cosas de R9, sin anotar) ni de que **no escriba** (paso 3 de T26 de F-012: «NO EJECUTADO»). Además ese dry-run fue **antes** de adjuntar, así que el caso que T22 pide —con `grafico.estado: adjuntado`— no llegó a darse |
| **T23** siembra del login | **no** | no se tocó. Lo único acreditable es **indirecto** y así queda escrito: el `commit` escribió, y R31 aborta con `409` sin tocar Sigrid si el ERP no confirma el login |
| **T24** primer cierre real | **no** | **el cierre ocurrió y salió bien** —lo sustantivo de la feature—, pero faltan los pasos **5** (`filas_afectadas: 2`), **7** (la fila de `dbo.log` campo a campo **y su huso**) y **9** (la traza local), y media parte del **6** (`tiemod` y `MAX(ide)`) |
| **T25** el `tex` propio | **no** | no se lanzó el script. Su precondición **sí** se cumple: hay un cierre real hecho |
| **T26** el guard acepta el batch | **SÍ** | ver §3 |
| **T27** reintento sobre lo ya cerrado | **no** | no se ejecutó, y **lo de F-025 no vale** (§4) |

## 3 · La única marca, y la cadena que la sostiene

**T26** se marca porque su propio contrato dice que **no tiene ejecución
propia**: «se hace **DENTRO de T24**, no después: lo que se observa es la
respuesta del paso 4». Esa respuesta existe.

1. El `POST /api/cerrar` con `commit` respondió **`200`** [MEDIDO en
   `appi-postventa-dev`].
2. **La reclamación quedó en `CER`**, comprobado por una persona en la ficha de
   Sigrid.
3. `SqlWriteGuard` valida **cada** sentencia del batch, y ante un rechazo la
   pasarela revierte **el batch entero** (`azure-apps/sigrid_api.md` §5 y §7.3).
   Si hubiera rechazado algo —la sugerencia `WITH (UPDLOCK, HOLDLOCK)`
   incluida—, el `UPDATE` se habría ido con él y el ERP habría quedado **sin
   ningún cambio**.
4. Cambió ⇒ **el guard dejó pasar las dos sentencias tal cual**.

**La salvedad va escrita, no escondida**: `filas_afectadas` no se anotó, así que
del `INSERT` en `dbo.log` **no hay observación directa** —se deduce de (3)— y
**la fila de log nadie la ha mirado**. Está en la casilla, en `tasks.md` y como
hueco 8 de §9.4. Si el reviewer no comparte la cadena, ahí está entera para
romperla.

## 4 · Lo que NO se ha usado como evidencia, y por qué

- **La prueba de F-025 no acredita T27.** Sus registros muestran `archivar` y
  `adjuntar` y **ninguna llamada a `cerrar`**, sin que se aclarara si fue
  idempotencia o si el circuito se detuvo; el responsable aprobó sin responder
  a esa pregunta (`specs/F-025-confirmacion-unica/tasks.md`, cierre del bloque
  5). **Una llamada que no consta no verifica un reintento**, y aun en la
  lectura buena lo que probaría es una guarda del **front**, no el `ya_cerrada`
  del **backend** que R18 y R42 exigen.
- **Los tests unitarios no cuentan en el bloque 8**, que existe precisamente
  para lo que un mock no puede probar.
- **Las inferencias van marcadas como inferencias** (T22 y T23) y **no
  sostienen ninguna marca**, salvo la de T26, con su cadena a la vista.

## 5 · La enmienda de la obra (punto 2 del encargo)

El guion del bloque 8 seguía nombrando la **obra de prueba 404** —y, en T22 de
`tasks.md`, **Mirasierra**—. Era el **resto abierto de H10**, que
`guion_bloque9_F-012.md` §8 dejaba escrito como «queda por corregir».

**Corregido con el mismo criterio que se usó en el bloque 9 y en la spec de
F-012: enmendar citando, no reescribir.**

- **Nota nueva del 2026-09-14** arriba del guion, que **cita literalmente la
  premisa original** («sobre una reclamación de la obra de prueba 404» y el
  recuadro «Por qué la 404 y no Mirasierra»), dice **quién la levantó y
  cuándo** (el responsable, 2026-09-10, planteándosele de forma explícita que
  la 0626 es una obra en uso) y da la tabla obra/incidencia.
- **Tres marcas fechadas dentro**: en la nota del 2026-09-06, en la **P5** de
  §2 y en el recuadro «Por qué la 404 y no Mirasierra». **No se borró ni una
  línea.**
- **Lo que no cambia queda repetido**: comprobación previa antes de cada
  escritura, autorización por incidencia concreta (P6 **gana peso** al no haber
  obra de pruebas detrás), y **Mirasierra sigue fuera**.
- En `tasks.md`, la nota del bloque 8 enmienda **dos** cosas del texto de T22
  sin tocarlo: la obra, y que **R21 está derogado** por R48 de F-012 —el
  dry-run ya no trae `aviso_sin_grafico`, trae el bloque `grafico`—.

## 6 · Lo que queda fuera de este trabajo

- **No se ejecutó nada contra ningún sistema**, por encargo y por `CLAUDE.md`.
- **No se cambió el `status` de ninguna feature**: F-009 sigue `blocked` en
  `harness/features.json`. Lo lleva el líder.
- **`azure-apps/postventa_incidencias.md` sigue diciendo que «todavía no se ha
  ejecutado ni un cierre real»**, y desde el 2026-09-11 es falso. Ya estaba
  anotado como pendiente en el paso 8 de T32 de F-012. **Queda fuera del
  alcance** —es otro repositorio y el encargo no lo pedía— y consta en §9.5
  punto 5 del guion.
- **No se han cerrado huecos**: el acta los documenta, no los resuelve.

## 7 · Veredicto para el líder (resumen de §9.5 del guion)

**Sí queda algo sustantivo sin verificar de F-009.**

- **Lo que la feature existe para hacer está hecho y visto**: una reclamación
  real pasó a `CER` en producción, escrita por el servicio desplegado, con
  autorización y **con su parte dentro** — y con F-012 delante, el riesgo
  aceptado de `design.md` §2 no se materializó ni una vez.
- **Lo que falta y duele**: **la fila de auditoría del primer cierre real está
  escrita en producción y nadie la ha mirado**, su **huso** incluido — el
  defecto que §0.2 del propio guion daba por probable.
- **Ocho huecos, en §9.4 del guion, ordenados por coste**. **Siete de los ocho
  no exigen escribir en el ERP**, y **tres no exigen ni abrir la ventana**:
  1. la fila de `dbo.log` campo a campo **y su huso** — solo lectura;
  2. **T25 entera** (el `tex` propio) — solo lectura, y de paso **localiza esa
     fila**;
  3. la **traza local** del cierre — solo lectura, y del esquema propio.
- **El único hueco que exige abrir la ventana de escritura es T27**, el
  reintento sobre lo ya cerrado: **el escenario más probable en uso normal**, y
  el que **las tres features dejaron sin marcar** (T27 de F-009, T30 de F-012,
  T22 de F-025).
- **Marcar el bloque 8 como superado sería falso.** Solo T26 está acreditada.

La decisión —cerrar F-009 como se cerró F-012, con los huecos escritos, o
hacer antes la sesión de solo lectura— **es del responsable**.

## 8 · Fase RED

**No aplica, y el motivo es que no hay código.** Este encargo es documental:
no toca ni una línea de producción ni de tests, así que no hay requisito EARS
que escribir primero ni traza de fallo que pegar. La regla de
`.claude/agents/implementer.md` —«toda escritura de código va acompañada de su
test»— no tiene objeto aquí porque no hubo escritura de código.

Lo que **sí** sustituye a esa disciplina en un trabajo de acta es el criterio
de §4: **nada se marca sin una observación que lo sostenga**, y las inferencias
van etiquetadas y, salvo una, no sostienen marcas.

## 9 · Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** y resultado | **62 passed**, más las dos suites de servicio (`api` y `front`) en verde. `bash harness/init.sh` termina con **exit code 0** y `ENTORNO LISTO` |
| **Tiempo de la suite** | **6,70 s** (la suite raíz, la que imprime `init.sh`) |
| **Cobertura de las líneas cambiadas** | `PUERTA COBERTURA: **99.0 %** de 1340 líneas cambiadas cubiertas (1327/1340, umbral 80 %, nivel estandar)` — **[OK]**. El número es el del árbol, no de este trabajo: **este encargo no cambia ninguna línea de código**, así que no aporta ni una línea nueva a esa medición |
| **Mutantes generados y supervivientes** | **N/A, con motivo**: la campaña de mutación muta código Python de producción y este trabajo **no toca ninguno**. Un alcance vacío daría «cero mutantes», y eso **no es una puerta superada** sino una campaña que no mide nada — el mismo caso que quedó escrito en F-025 (`progress/history.md`). La campaña de F-009 ya está hecha y cerrada: **123 mutantes, 117 muertos, 6 supervivientes justificados**, en `progress/mutacion_F-009.md` (T28) |
| **Ejecuciones contra sistemas externos** | **cero**, por diseño del encargo |
| **Casillas rellenas** | 6 de 6 (T22–T27), **1 marcada** |
| **Huecos documentados** | **8**, con coste y camino de recuperación cada uno |

**Salida real de `bash harness/init.sh`** (2026-09-14, rama
`feature/F-026-aprobacion-humana`), en lo que importa:

```
    25 features, 13 abiertas, en curso: ['F-026'], bloqueadas: ['F-009']
[OK] features.json válido
[OK] BACKLOG.md al día
[AVISO] Hay features en estado blocked: revisa progress/current.md
[AVISO] ruff: 60 avisos (deuda previa, no bloquea)
..............................................................   [100%]
62 passed in 6.70s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 99.0% de 1340 líneas cambiadas cubiertas (1327/1340, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-026-aprobacion-humana
ENTORNO LISTO. Puedes trabajar.
```

Ejecutado **antes** de tocar nada y **después** de los tres commits: verde las
dos veces.

## 10 · Verificaciones MANUAL pendientes

Las **ocho** de `progress/guion_bloque8_F-009.md` §9.4, que son las de F-009, y
las **cinco** de `progress/guion_bloque9_F-012.md` §9.4, que son las de F-012 y
el responsable decidió no ejecutar. **Se solapan en una**: T27 de F-009 = T30 de
F-012 = T22 de F-025, el reintento sobre lo ya cerrado.

Y un pendiente documental con dueño: **`azure-apps/postventa_incidencias.md`**.
