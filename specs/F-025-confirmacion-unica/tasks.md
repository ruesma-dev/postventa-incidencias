<!-- specs/F-025-confirmacion-unica/tasks.md -->
# F-025 · Archivar y cerrar en una sola confirmación — Tareas

> Una tarea = un commit `F-025 Tn: ...`. Ordenadas por dependencia; los tests
> van antes o junto a la implementación (**fase RED obligatoria**, rigor
> `critico`).
>
> **Ninguna pregunta abierta bloquea el arranque**: P1 y P2 se fijan en el
> bloque 3, P3 es un texto y P4 es una medición del bloque 5. Se puede
> implementar desde T1.
>
> La rama es `feature/F-025-confirmacion-unica`, creada desde `dev` (o desde la
> rama de F-012 si aún no está mergeada: lo dice el humano al arrancar).
>
> **Regla dura de esta feature**: ninguna tarea toca
> `application/pipelines/paso_grafico.py` ni `paso_cierre.py`. Si una tarea
> parece necesitarlo, es que se está quitando una comprobación y hay que
> **parar** (`requirements.md` §6).

---

## Bloque 0 · Fijar el hallazgo antes de tocar el front

- [x] **T1**: Crear `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`:
      un `commit` **sin ninguna llamada previa** hace su comprobación previa
      dentro de la misma invocación y escribe. Con dobles en memoria, sin red.
      | Verificación: para `adjuntar`, el doble de `GraficoPort` registra la
      secuencia **`commit=False` y después `commit=True`** en **una sola**
      llamada al handler (R10, y R20 de F-012); para `cerrar`, el doble de
      `ErpPort` registra `leer_reclamacion` **antes** de `cerrar` en una sola
      llamada (R10, y R8 de F-009). **Fase RED**: se demuestra rompiendo en
      copia aislada el `_dry_run` interno y pegando la traza del fallo.

- [x] **T2**: En el mismo fichero, los **siete control-negativo** de
      `requirements.md` §6: reclamación inexistente (R29), estado no cerrable
      y ya cerrada (R30), documento ya colgado (R31), puertas de aptitud y
      archivo (R32), login verificado contra el ERP (R33), cierre sin gráfico
      (R34) y puertas de entorno (R35). | Verificación: cada uno con su test
      `test_f025_rN_*` y todos en verde **antes** de tocar el front, para que
      el bloque 3 no pueda romperlos sin que se note.

---

## Bloque 1 · El circuito, donde sí hay tests (`js/pipeline.js`)

- [x] **T3**: Añadir `pendientesDeCircuito(partes)` y
      `porcentajeDeTanda(hechos, total)` a `js/pipeline.js`, exportados. |
      Verificación: `tests_js/circuito.test.js` cubre R24 —entran los partes
      **archivados sin adjuntar** y los **adjuntados sin cerrar**, no solo los
      no archivados—, quedan fuera los no aptos (R36), los no guardados y los
      ya cerrados; y `porcentajeDeTanda` sobre el tamaño de la tanda (R12),
      con el caso `total = 0`.

- [x] **T4**: Añadir `ejecutarCircuito(parte, api, opciones)` con los tres
      pasos **saltables** y sin lanzar nunca. | Verificación:
      `tests_js/circuito.test.js` con un `api` doble comprueba el **orden**
      archivar → adjuntar → cerrar (R7); que `adjuntar` y `cerrar` se llaman
      **siempre con `commit` y `confirmado`** y **nunca** sin ellos (R8); que
      son **tres** llamadas por parte y ni una más (R9); que un parte ya
      archivado **no** llama a `archivar` (R25) y uno ya adjuntado **no**
      llama a `adjuntar` (R26); y que `alPaso` publica `archivando`,
      `adjuntando`, `cerrando` en ese orden (R13).

- [x] **T5**: Los fallos dentro de `ejecutarCircuito`. | Verificación: mismo
      fichero — fallo de `archivar` ⇒ **cero** llamadas a `adjuntar` y a
      `cerrar` (R17); fallo de `adjuntar` ⇒ **cero** llamadas a `cerrar`
      (R18); respuesta de `adjuntar` distinta de `adjuntado` (p. ej.
      `ya_cerrada`) ⇒ tampoco se cierra, y **no es un error** (R27); fallo de
      `cerrar` con el gráfico dentro ⇒ estado `adjuntado` (R19); y el
      resultado trae siempre `numeroIncidencia` cuando el backend lo devolvió
      (R37).

- [x] **T6**: La bandera `erpCerrado` y la guarda de reentrada. |
      Verificación: con `erpCerrado: true`, `ejecutarCircuito` **archiva y no
      llama al ERP** (R21); un `503` de entorno en `adjuntar`/`cerrar`
      devuelve `tipoError: 'entorno'` con `ambito: 'erp'`, y en `archivar` con
      `ambito: 'archivo'` (R22); y la guarda impide que una segunda tanda
      arranque con una en curso (R14). **Fase RED** en las tres.

---

## Bloque 2 · La tanda (`js/app.js`)

- [x] **T7**: Fundir las dos tandas en una: `confirmarArchivo` pasa a recorrer
      `pendientesDeCircuito` por **la misma cola** (R11) llamando a
      `ejecutarCircuito`; `_archivarUno`, `_adjuntarYCerrarUno`, `_cerrarUno`
      y `_dryRunUno` desaparecen de `app.js`. | Verificación:
      `tests/test_f025_front.py` comprueba que `app.js` **no contiene** ningún
      encadenado de llamadas (ni `api.adjuntar` seguido de `api.cerrar`) y que
      el orden vive en `pipeline.js`; y que la guarda de reentrada se invoca
      (R14). Es el control que F-019 echó de menos: si el orden vuelve a
      `app.js`, este test se pone rojo.

- [x] **T8**: Estado nuevo de pantalla: `totalTanda`, `parte.paso`, fase
      `archivando_y_cerrando`, `tituloDeFase()` y `reiniciar()` al día. |
      Verificación: `tests/test_f025_front.py` — la fase nueva está en el
      `x-show` de la sección de progreso y en `tituloDeFase`; `reiniciar()`
      limpia `totalTanda` y `parte.paso`; el denominador de `porcentaje()` es
      `totalTanda` y no `partes.length` (R12).

- [x] **T9**: Retirar `pedirDryRunCierre`, `hayDryRun`, `dryRunDe` y
      `dryRunGraficoDe` de su papel de pantalla previa (**P1**, opción
      recomendada: retirarlos) y pasar `numeroIncidencia` al resumen. |
      Verificación: `tests/test_f025_front.py` — `app.js` no expone ningún
      camino que llame a `api.adjuntar` o `api.cerrar` sin `commit` (R8, R5).

---

## Bloque 3 · La pantalla (`index.html`)

- [x] **T10**: Fundir las secciones «Archivar» y «Cerrar en Sigrid» en una
      sola, con **un** botón y **una** confirmación cuyo texto nombre las tres
      cosas y el número de partes (R1, R2, R6; **P3** decide la redacción). |
      Verificación: `tests/test_f025_front.py` sobre el HTML **sin
      comentarios** (mismo `_sin_comentarios_html` que `test_f012_front.py`):
      existe **un** `pedirConfirmacion*` y **un** botón de confirmar en el
      circuito de escritura; **no** existe ningún `pedirDryRunCierre` ni el
      literal «Ver qué pasaría»; el texto de la confirmación nombra SharePoint,
      la reclamación y el cierre.

- [x] **T11**: El progreso: barra sobre `totalTanda`, `parte.paso` visible por
      parte y resumen con el número de incidencia (R12, R13, R16, R17, R37). |
      Verificación: `tests/test_f025_front.py` — la sección de progreso se
      pinta en la fase nueva, cada fila de parte pinta `paso`, y el resumen
      pinta `numero_incidencia`.

- [x] **T12**: Sin identidad, el botón único se deshabilita y se dice por qué
      (**P2**, opción recomendada). | Verificación: el `:disabled` del botón
      incluye `!usuario.usuarioOid` y el mensaje existente se conserva.

- [x] **T13**: Conservar el recuadro ámbar «adjunto en Sigrid y la incidencia
      sigue abierta» con «Reintentar el cierre», y el recuadro de
      `error_grafico` (R19; R65 de F-012 sigue vigente). | Verificación: los
      tests de F-012 que los fijan **siguen en verde sin tocarlos**.

---

## Bloque 4 · Las enmiendas y la documentación

- [x] **T14**: Escribir en `specs/F-012-grafico-sigrid/requirements.md` los
      cinco recuadros de `design.md` §11.1–§11.4 (R63, R22, R21, R49, R50). |
      Verificación: `git diff` de ese fichero **no borra ni una línea**
      (`git diff --numstat` con 0 supresiones), y un test de documentación
      comprueba que bajo R63 aparece «DEROGADO», la fecha `2026-09-11` y la
      cita literal de la premisa (R38, R39, R40, R41).

- [x] **T15**: Escribir en `specs/F-009-cierre-sigrid/requirements.md` la nota
      de `design.md` §11.5. | Verificación: mismo control de cero supresiones;
      el texto dice que R8/R10 **siguen vigentes** y que R21 **no se vuelve a
      derogar** porque ya lo estaba (R42, R43).

- [ ] **T16**: Retirar de `tests/test_f009_front.py` y `test_f012_front.py`
      **solo** las aserciones de R63 y de «antes de confirmar», citando R38 y
      R39 en cada retirada. | Verificación: `git diff --stat` de esos dos
      ficheros toca **únicamente** líneas que nombran el dry-run previo o «ver
      qué pasaría»; el resto de la suite de F-009 y F-012 sigue en verde.
      Mismo procedimiento que T3 de F-012 con R48.

- [ ] **T17**: Precisar `docs/ARCHITECTURE.md`: paso 7b del pipeline y punto 6
      de «Semántica de dominio» (R47). | Verificación: un test de
      documentación comprueba que el texto dice «una sola confirmación» y «en
      la misma llamada»; y que **no** se ha borrado la exigencia de dry-run.

- [ ] **T18**: Dejar constancia de que `azure-apps/postventa_incidencias.md`
      **no se toca**, y por qué (R48). | Verificación: el informe del
      implementer lo dice con el repaso hecho (endpoints, cuerpos, variables,
      tablas y las cinco puertas), y `git status` de ese repositorio queda
      limpio. **No** se corrige ahí la deuda de F-012 (su T32 paso 8): es de
      aquella feature.

---

## Bloque 5 · Verificación contra el ERP · `MANUAL (humano)`

> Escribe en el histórico de una **obra en uso**. Reglas que no se negocian y
> que vienen de F-012: **autorización expresa del responsable para la
> incidencia concreta**, `CIERRE_HABILITADO` abierto **solo** durante la
> prueba y cerrado y **releído** al terminar, y **ninguna escritura desde un
> puesto de trabajo**. El guion vive en `progress/guion_bloque5_F-025.md`.

- [ ] **T19**: Escribir `progress/guion_bloque5_F-025.md` con sus casillas. |
      Verificación: revisión del humano antes de abrir la ventana.

- [ ] **T20**: **Una incidencia, el circuito entero con una sola
      confirmación.** | Verificación: **MANUAL (humano)**. Se anota: que hubo
      **una** confirmación y no dos (R1, R2); que en el registro de la
      aplicación hay **exactamente tres** peticiones para ese parte —
      `archivar`, `adjuntar`, `cerrar`— y ninguna sin `commit` (R7, R8, R9);
      la **duración de cada una**; y **el tamaño en bytes del parte**, que es
      el número que F-012 se dejó sin medir (**P4**).

- [ ] **T21**: **La duración de `adjuntar` fusionada, frente al escalonado.** |
      Verificación: **MANUAL (humano)**. Se compara con los **35 s** de
      `SIGRID_TIMEOUT_S` y los **40 s** de `TIMEOUT_PETICION_MS`, y se anota
      el porcentaje del presupuesto consumido (`design.md` §12.2). Si pasa del
      60 %, **se para y se lleva al humano** la decisión de P4.

- [ ] **T22**: **El reintento no duplica.** | Verificación: **MANUAL
      (humano)**. Con el parte ya cerrado, se vuelve a lanzar la tanda sobre
      él: se comprueba en el ERP que **no hay un segundo gráfico** y que
      `dbo.log` **no ha ganado una fila**, y en pantalla que sale `ya_cerrada`
      (R25–R28). Es la comprobación que F-012 **no llegó a hacer**.

- [ ] **T23**: **Cerrar la ventana y dejar constancia.** | Verificación:
      **MANUAL (humano)**. `CIERRE_HABILITADO=false` **lo primero**, y
      **releído** para confirmarlo; casillas del guion rellenas; duraciones y
      tamaño anotados en `progress/current.md`.

---

## Bloque 6 · Cierre

- [ ] **T24**: Campaña de mutación (`python -m harness.mutacion --feature
      F-025`, con los workers de `harness/rigor.json`, **anotando el nº de
      workers**). | Verificación: rigor `critico` → **cero supervivientes**
      sin justificación escrita aceptada por el humano; informe en
      `progress/mutacion_F-025.md` sin ningún `PENDIENTE`.
      Aviso de alcance: el grueso del cambio es **JavaScript**, que la
      herramienta no muta. La parte Python medible son los tests nuevos del
      bloque 0; **si el alcance sale vacío, se declara N/A con el motivo
      impreso**, nunca a secas (C4 bis).

- [ ] **T25**: Ejecutar `bash harness/init.sh` en verde. | Verificación:
      `bash harness/init.sh` termina con exit code 0, tests incluidos —los de
      `api` y los de `front`, con el puente a `node --test`— y con la puerta de
      cobertura de las líneas cambiadas en `[OK]` o en `N/A` **con el motivo
      impreso**.
