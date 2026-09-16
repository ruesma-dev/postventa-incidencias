<!-- progress/cierre_F-009.md -->
# F-009 · Acta de cierre — **decisión del responsable del 2026-09-16**

> **Qué es este fichero.** La constancia fechada de cómo se cerró F-009: con
> **cinco huecos de verificación abiertos**, escritos uno a uno y con su
> requisito. No es una conclusión del arnés: **es una decisión del responsable
> del proyecto**, tomada hoy, **2026-09-16**, y el arnés la ejecuta y la deja
> escrita.
>
> **Este encargo no ejecutó nada.** Ni contra Sigrid, ni contra `sigrid-api`,
> ni contra Azure, ni contra el PostgreSQL compartido, ni contra SharePoint.
> No toca una línea de `services/`. Toda la evidencia que se cita estaba ya
> escrita antes de empezar.

---

## 1 · La decisión, literal y con su fecha

El **2026-09-16**, el responsable del proyecto ordenó cerrar F-009 con estas
palabras:

> «ya he probado que cierra y escribe bien en sigrid. cierrala»

Preguntado **qué respalda esa prueba**, respondió: **los dos cierres reales ya
auditados**, y **ninguno nuevo**. No hubo una ejecución del 2026-09-16 contra
el ERP detrás de esa frase, y así queda escrito para que nadie lo lea de más.

**El precedente que se aplica es el de F-012**, cerrada el 2026-09-11 con sus
escenarios sin verificar escritos y fechados. Y la regla que manda sobre todo
lo demás: **nada se borra**. Lo derogado se enmienda con constancia fechada,
citando la premisa original literal, su fecha y quién la decidió — el mismo
patrón que el **R28 de F-010** (2026-09-03) y que las enmiendas de **F-025**.
Un documento que oculta lo que no se verificó hace más daño que no tenerlo.

---

## 2 · Qué respalda el cierre: los dos cierres reales auditados

Los dos ocurrieron contra el **ERP de producción**, sobre la obra **`0626`**,
que **no es una obra de pruebas: es una obra en uso** (premisa levantada por el
responsable el 2026-09-10, constancia en `progress/guion_bloque9_F-012.md`).
Los dos están **auditados por lectura, no de palabra**.

| Cuándo | Incidencia | Fila de `dbo.log` | Dentro de qué feature |
|---|---|---|---|
| **2026-09-11** | **`RS26.09/0150`** | **`ide` 8457839**, `10:28:12` hora local | **F-012** (parte archivado, adjunto y reclamación cerrada) |
| **2026-09-15** | **`RS26.09/0149`** | **`ide` 8467000**, `14:30:05` hora local | **F-026** (un parte **no apto** aprobado a mano, y de ahí al archivado y al cierre) |

Las dos filas pasan las **once comprobaciones campo a campo** del §7.3 de
`specs/F-009-cierre-sigrid/design.md`, y en las dos el par `fec`/`hor` está en
**hora local** (`docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md`,
sección «Lo que YA se ha ejecutado contra el ERP»).

### 2.1 · Qué acredita el cierre del 2026-09-11 (`RS26.09/0150`)

Fuentes: `progress/guion_bloque9_F-012.md` §9 (mediciones en
`appi-postventa-dev`) y `progress/guion_bloque8_F-009.md` §9 y §10.

- **T24 paso 4, en parte** · el `POST /api/cerrar` con `commit` respondió
  **`200`** (`08:28:12` UTC, 472 ms). Del paso 4 consta **el HTTP 200**, no el
  `estado: "cerrado"` del cuerpo.
- **T24 paso 6** · `con.est` quedó en **`CER`**, con el destino resuelto contra
  `conest` (**R1**). Leído el 2026-09-15 con `infra/09_estado_reclamacion_sigrid.ps1`
  → `ESTADO DE LA RECLAMACION : PASA`. Hasta ese día constaba solo por lo que
  una persona vio en la ficha de Sigrid.
- **T24 paso 7** · la fila nueva de `dbo.log` (`ide` 8457839) **campo a campo**:
  `tab` con, `tip` 708, `cod` `RS26.09/0150`, `ope` 5, `est` 1, `ori` 0,
  `emp` 1, `usu` `pgris`, `tex` «Cerrar parte (postventa-incidencias)», `res`
  «fuga en caldera», **una sola fila nueva**. **R24 y R25 acreditados.** Y el
  **huso**: `HORA LOCAL (correcto)`, **0,0 min** de diferencia — el defecto que
  el §0.2 del guion daba por probable **no existía**.
- **T24 paso 9** · la traza local quedó en `cerrado`, con su `oid` y **sin el
  login** del ERP. **R41 y R43 acreditados**
  (`infra/12_traza_cierre_local.ps1` → `PASA`).
- **T25, entera** · el `tex` propio hace lo que se diseñó: el prefijo del ERP
  **encuentra** nuestro cierre (seguimos en los informes de Posventa) y el
  filtro exacto devuelve **solo lo nuestro**, ninguno de los 6.843 cierres
  manuales. Son las dos condiciones de **D1** de `design.md`
  (`infra/11_trazabilidad_tex_sigrid.ps1` → `PASA`).
- **T26, entera** · `SqlWriteGuard` **aceptó el batch tal cual**,
  `WITH (UPDLOCK, HOLDLOCK)` incluido: la pasarela revierte el batch entero
  ante un rechazo (`azure-apps/sigrid_api.md` §5 y §7.3), el ERP cambió, luego
  no hubo rechazo.
- **Que el dry-run del cierre funciona contra el ERP** · `200` en 4,4 s
  (`08:27:42` UTC), y **no exige el gráfico** (R50 de F-012).

**Lo que este cierre NO acredita**: el **contenido** del dry-run (R9), que el
dry-run **no escriba**, el `503` con la ventana cerrada, nada de T23, los pasos
**2, 3, 5 y 8** de T24, y **nada de T27**.

### 2.2 · Qué acredita el cierre del 2026-09-15 (`RS26.09/0149`)

Fuente: la enmienda del 2026-09-15 a la entrada de **F-026** en
`progress/history.md`, y `docs/INTEGRACION.md`.

- **El circuito completo vuelve a funcionar de extremo a extremo**, y esta vez
  **con un estado de origen distinto y una decisión humana por delante**: un
  parte **no apto** por observaciones manuscritas, aprobado a mano en la web,
  archivado, y la reclamación **cerrada en Sigrid** con su gráfico dentro.
- **Segunda observación independiente de R24, R25 y del huso**: la fila `ide`
  8467000 pasa las once comprobaciones campo a campo, `fec`/`hor` en **hora
  local**, firmada `pgris`.

**Lo que este cierre NO acredita**: exactamente lo mismo que el primero. No se
anotó el `MAX(ide)` de partida, no se leyó `filas_afectadas`, no se recorrió el
dry-run por consola, no se tocó T23 y **no se ejercitó T27**. Y el circuito de
F-025 **no pide dry-run previo**: el front llama siempre con `commit`, así que
un cierre real no produce, por sí solo, ninguna de las lecturas que faltan.

---

## 3 · Los cinco huecos vivos, uno a uno

Es la foto del **2026-09-15** (`progress/guion_bloque8_F-009.md` §9.4,
actualización), y sigue siendo la buena hoy: la tabla original de **ocho**
huecos es del 2026-09-14 y se conserva sin tocar, con la marca de qué pasó con
cada uno. **Los huecos 1, 2 y 3 de aquella tabla están CERRADOS** por la sesión
de solo lectura del 2026-09-15.

### Hueco 1 · **T22, pasos 2 y 5** — el `503` con la ventana cerrada, y que el dry-run no escribe

- **Qué exige**: que `POST /api/cerrar` responda **`503 CierreDeshabilitado`**
  con `CIERRE_HABILITADO` en `false` —la doble puerta del §0.1 del guion,
  observada en el borde— y que un **dry-run no mueva nada** en el ERP (foto de
  `con.est` antes y después).
- **Requisitos**: **R37** y **R49** el primero; **R8** y **R10** el segundo.
- **Por qué no se recorrió**: el `503` **no escribe nada** y hoy la ventana está
  cerrada, así que sale gratis — pero exige una sesión en el front, y no se ha
  hecho. La mitad de «no escribe» exige además **foto antes/después con la
  ventana abierta**.
- **Nota**: es también el paso 3 de T32 de F-012, su «único resto abierto».

### Hueco 2 · **T22, paso 4** — las seis comprobaciones de R9 y el bloque `grafico`

- **Qué exige**: leer **por consola** el JSON crudo del dry-run y comprobar las
  **seis cosas de R9** —código y descripción de la reclamación, estado de
  origen legible, destino `CER`, login con el que se firmaría— **más el bloque
  `grafico`** con `estado: adjuntado`.
- **Requisitos**: **R9** y **R49** (de F-012).
- **Qué se pierde**: el contenido del dry-run **es lo que una persona leería
  antes de confirmar**; y es la prueba directa de que **R48 derogó de verdad**
  el aviso de R21.
- **Por qué no se recorrió**: exige la **ventana abierta** y una sesión en el
  front. **No escribe**: es un dry-run. Y desde F-025 el front **ya no lo pide
  por sí solo** — la única vía es la consola (§4(b) del guion).

### Hueco 3 · **T23** — la siembra del login contra el ERP

- **Qué exige**: (a) `infra/07_alta_usuario_sigrid.ps1 -VerificarAhora`, el
  `COUNT(*)` que comprueba que el login candidato existe **exactamente una vez**
  en `dbo.usu`; (b) leer `postventa.usuarios_sigrid` y ver la correspondencia
  guardada **como confirmada**, con `verificado_at_utc` relleno; (c) que un
  login **inexistente** responda **`409`** nombrando correo y login intentado,
  **sin tocar Sigrid**.
- **Requisitos**: **R34** el primero, **R33** el segundo, **R31** el tercero.
- **Qué está ya reducido**: el `usu` escrito en el ERP es **`pgris`**, lo que
  prueba que el login **se derivó**, **se resolvió contra el ERP** y **se usó
  para firmar** la fila de auditoría — **R30, R31 y R32 en lo sustantivo**. Una
  firma correcta **no prueba R33**, ni el `409`, ni la unicidad del candidato.
- **BLOQUEADO ADEMÁS POR UN SCRIPT ROTO**: `infra/07_alta_usuario_sigrid.ps1`
  (líneas **161** y **248**) arrastra el defecto de comillas de PowerShell 5.1
  y **nunca se ha ejecutado**: se estrellará en la primera línea de T23. El
  arreglo existe y está probado (`Invoke-PythonDelServicio`, en
  `infra/08_lectura_sigrid_comun.ps1`). Dado de alta como feature propia — ver
  §5.

### Hueco 4 · **T27** — el reintento sobre una incidencia ya cerrada

- **Qué exige**: repetir el cierre sobre una incidencia que ya está en `CER` y
  comprobar que responde **`ya_cerrada`**, **sin escribir nada en Sigrid**
  —`MAX(ide)` de `dbo.log` no sube— y **sin pisar** la traza local terminal.
- **Requisitos**: **R18** y **R42**.
- **Y hay que decirlo así de claro**: es **el único criterio de aceptación de
  la ficha de F-009 que ningún cierre real ha ejercido**. El criterio 5 de la
  ficha —«reintentar sobre una incidencia ya cerrada no la vuelve a tocar»—
  queda **acreditado solo por tests**, sin una sola ejecución real. Y es **el
  escenario más probable en uso normal**: alguien vuelve a pasar el mismo parte.
- **Por qué no se recorrió**: es **el único hueco que exige abrir la ventana de
  escritura**. No hay que provocar ningún fallo: basta un `commit` sobre
  `RS26.09/0150` o `RS26.09/0149`, que ya están cerradas.
- **Nadie lo probó en ninguna de las cuatro features que pasaron por delante**:
  F-009, F-012 (su T30), F-025 (su T22) y F-026 lo dejaron sin marcar, cada una
  por su lado. La prueba de F-025 del 2026-09-11 **no sirve** y se descartó a
  propósito (§9.6 del guion): sus registros no tienen **ninguna** llamada a
  `cerrar`.

### Hueco 5 · **R22** — `filas_afectadas: 2`, y las fotos de partida

- **Qué exige**: que la respuesta del `commit` declare **2 filas afectadas** —el
  `UPDATE` de `dbo.con` y el `INSERT` en `dbo.log`— y, para los pasos 2 y 8 de
  T24, el **`MAX(ide)` de `dbo.log`** y el **`con.tiemod`** **de antes** del
  cierre.
- **Requisitos**: **R22**, y los pasos **2**, **5** y **8** de T24.
- **⚠ NO ES RECUPERABLE HACIA ATRÁS, y esta es la advertencia que este acta
  existe para dejar escrita.** Ninguna lectura de hoy lo da: **la foto que
  faltaba era la de antes**, y nadie la tomó ni el 2026-09-11 ni el 2026-09-15.
  `con.tiemod` vale hoy `46275.647118`, pero **ese número no compara con nada**.
- **Qué costaría cerrarlo**: exige **una reclamación ABIERTA nueva de la obra
  `0626`**, que depende de **Posventa**. La petición está escrita y **sin
  enviar** en `progress/peticion_posventa_prueba_F-012.md`.

---

## 4 · Resumen de lo que queda sin marcar en `tasks.md`

| Tarea | Estado | Motivo |
|---|---|---|
| **T22** | **NO recorrida** | huecos 1 y 2 |
| **T23** | **NO recorrida** | hueco 3, y además el script `07_` está roto |
| **T24** | **NO recorrida** | de sus **nueve** pasos faltan el **2, 3, 4, 5 y 8**; constan el 4 en parte, el 6, el 7 y el 9 |
| **T25** | **HECHA** (2026-09-15) | sesión de solo lectura, `11_trazabilidad_tex_sigrid.ps1` → `PASA` |
| **T26** | **HECHA** (2026-09-11, acreditada el 2026-09-14) | el guard aceptó el batch |
| **T27** | **NO recorrida** | hueco 4 — el único criterio de la ficha sin ejecución real |

T28 (mutación: **117 muertos, 6 supervivientes justificados**, 2026-09-02) y
T29 (`init.sh` en verde) están hechas. Los bloques 1–7 (T1–T21) están
implementados y con **review APROBADA** en `progress/review2_F-009.md`.

---

## 5 · Deuda que sobrevive al cierre, con dueño

- **Dos scripts de `infra/` no arrancan** por el defecto de comillas de
  PowerShell 5.1, y el arreglo ya existe en el repositorio:
  `infra/07_alta_usuario_sigrid.ps1` (líneas **161** y **248**) y
  `infra/17_traza_grafico_local.ps1` (línea **196**). Bloquean el hueco 3 (T23)
  y la precondición añadida de T24 (R2 de F-012). **Dados de alta como feature
  propia, F-029**, prioridad baja.
- **`progress/peticion_posventa_prueba_F-012.md`** sigue **escrita y sin
  enviar**. Es la llave del hueco 5.

---

## 6 · Firma

**Decisión del responsable del proyecto, 2026-09-16.** El arnés la ejecuta y
deja constancia; no la respalda ni la contradice. Lo que el arnés sí afirma,
porque lo ha medido y está escrito arriba: **el cierre real de F-009 está
acreditado dos veces contra el ERP de producción, y sus comprobaciones de borde
—los cinco huecos de §3— no**.
