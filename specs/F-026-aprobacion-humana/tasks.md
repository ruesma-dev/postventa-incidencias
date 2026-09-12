<!-- specs/F-026-aprobacion-humana/tasks.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Tareas

> Una tarea = un commit `F-026 Tn: ...`. Ordenadas por dependencia; los tests
> van antes o junto a la implementación (**fase RED obligatoria**, rigor
> `estandar`).
>
> La rama es `feature/F-026-aprobacion-humana`, creada desde `dev` (o desde la
> rama de F-025 si aún no está mergeada: lo dice el humano al arrancar).
>
> **Cuatro preguntas abiertas bloquean el arranque**: **P1** (qué es aprobar),
> **P2** (qué motivos son aprobables), **P4** y **P5** (cómo se revoca). Las
> cuatro cambian el diseño. **P3, P6, P7 y P8** no bloquean: acotan el alcance y
> se pueden decidir mientras se implementa.
>
> **Regla dura de esta feature**: ninguna tarea toca
> `domain/models/validacion.py` ni `sql/04_validaciones.sql`. Si una tarea
> parece necesitarlo, es que se está reescribiendo el veredicto y hay que
> **parar** (`design.md` §2 y §9.3).
>
> **Segunda regla dura**: ninguna tarea toca `domain/models/cierre.py` ni
> `infrastructure/sigrid/escrituras.py`. Lo que se escribe en el ERP no cambia
> (R42).

---

## Bloque 0 · Fijar lo que hoy es imposible, antes de hacerlo posible

- [x] **T1**: Crear `services/postventa-api/tests/test_f026_puertas.py` con los
      **control-negativo** que tienen que seguir en verde al final: un parte de
      `revision_manual` **sin aprobación** no llega a archivar, ni a adjuntar,
      ni a cerrar; uno de `cola_validacion_humana` tampoco; y ninguno de los
      tres pasos lee la aprobación del cuerpo. Con dobles en memoria, sin red y
      sin BBDD. | Verificación: los seis casos en verde **antes** de tocar
      nada, con `pytest services/postventa-api/tests/test_f026_puertas.py`.
      Son R25 y R24, y son la red que impide que los bloques 2 y 3 aflojen una
      puerta sin que se note.

---

## Bloque 1 · El dominio, que es donde se decide

- [x] **T2**: Crear `services/postventa-api/domain/models/aprobacion.py` con
      `MOTIVOS_APROBABLES`, `MotivoRevocacion`, `Aprobacion` y `es_aprobable`.
      **Dominio puro**: sin red, sin SQL, sin `psycopg`. | Verificación:
      `tests/test_f026_aprobacion_dominio.py` cubre R6–R10 — aprobable con
      observaciones, aprobable con firma no humana, aprobable con las dos, **no
      aprobable** con `codigo_obra_no_legible`, **no aprobable** con
      `numero_incidencia_no_legible`, **no aprobable** si ya es apto—.
      **Fase RED**: traza del fallo antes de que exista el módulo.

- [x] **T3**: Añadir `huella_de_veredicto(validacion)` al mismo módulo, con la
      canónica de `design.md` §3 y `hashlib.sha256`. | Verificación: mismo
      fichero de test — dos veredictos iguales dan la misma huella; cambiar el
      destino, un motivo, la clasificación de firma o **el texto de la
      observación** la cambia (R30, **P4**); cambiar solo mayúsculas o espacios
      del texto **no** la cambia; y la huella **no contiene** ninguna subcadena
      del texto manuscrito (R15).

- [x] **T4**: Añadir `esta_vigente(aprobacion)` y `admite_circuito(validacion,
      aprobacion)`. | Verificación: mismo fichero — admite el apto de siempre;
      admite el no apto con aprobación viva **del mismo destino**; **no** admite
      con aprobación revocada (R31); **no** admite si el `destino_aprobado` no
      coincide con el destino actual; **no** admite con `validacion=None`.

- [x] **T5**: Añadir `ParteNoAprobable` a `domain/models/errores.py`, con su
      docstring diciendo que se traduce a **409** y por qué no es un 400. |
      Verificación: `tests/test_f026_aprobar_http.py` lo importa en T9; aquí
      basta con que la suite siga en verde.

---

## Bloque 2 · La persistencia

- [x] **T6**: Crear
      `services/postventa-api/infrastructure/persistencia/sql/10_aprobaciones.sql`
      con la tabla y el índice parcial de `design.md` §10, y su cabecera
      explicando qué construye, de qué lee y qué columna es dato personal. |
      Verificación: `tests/test_f026_ddl_aprobaciones.py`, con el patrón de
      `test_f005_ddl_idempotente_texto.py` y **sin BBDD**: el fichero cumple
      `NN_nombre.sql`, `ddl.validar()` acepta sus sentencias, lleva
      `IF NOT EXISTS`, está cualificado con el esquema propio, **no** nombra
      `public`, **no** declara ningún tipo binario, y los literales del `CHECK`
      de `destino_aprobado` coinciden con los dos `Destino` no aptos del dominio
      (R16, R12).

- [x] **T7**: Añadir a `sentencias.py` el `upsert_aprobacion`, el
      `select_aprobacion` y el `revocar_aprobacion_si_cambio`, y a `mapeo.py` el
      `fila_a_aprobacion` y el `json_de_codigos_de_motivo`. | Verificación:
      `tests/test_f026_persistencia.py` — el `upsert` va `ON CONFLICT
      (hash_parte) DO UPDATE` y deja `revocada_at_utc` a `NULL` (R17); el
      `UPDATE` de revocación lleva `revocada_at_utc IS NULL` y
      `huella_aprobada <> %s` **como parámetros**, sin interpolar nada; el
      `motivos_aprobados` que se escribe lleva **códigos** y no textos (R14); y
      `fila_a_aprobacion` reconstruye la dataclass con sus `Enum`.

- [x] **T8**: Ampliar `domain/ports/persistencia.py` con `guardar_aprobacion` y
      `consultar_aprobacion`, y `repositorio_pg.py` con su implementación;
      `guardar_validacion` ejecuta además la revocación **en la misma
      operación**. | Verificación: `tests/test_f026_persistencia.py` con un
      doble de conexión — guardar una validación cuya huella difiere revoca
      (R30); guardar una cuya huella coincide **no** revoca (R32); la
      revocación **no borra la fila** (R33) y escribe una etiqueta corta, nunca
      texto del cliente (R34); `consultar_aprobacion` devuelve `None` sin error
      cuando no hay fila.

---

## Bloque 3 · Las puertas y el borde HTTP

- [x] **T9**: Crear `interface_adapters/api/aprobar.py` con
      `aprobar_parte_http`, reutilizando `cuerpos.py` y `paso_persistencia`, y
      recalculando el veredicto con `validar_parte`. | Verificación:
      `tests/test_f026_aprobar_http.py`, **sin BBDD**, con el repositorio
      inyectado — aprueba y devuelve el bloque `aprobacion` (R2); **400** sin
      `usuario_oid` (R4) y sin `confirmado`; **409** si el veredicto no es
      aprobable (R9) y si ya es apto (R10); el veredicto **se recalcula** y un
      veredicto que venga en el cuerpo **se ignora** (R5); la respuesta **no
      lleva** el `oid`, ni correo, ni nombre, ni el texto de la observación
      (R19, R38, R43).

- [x] **T10**: Cablear la ruta en `function_app.py` (`POST`, `ANONYMOUS`, como
      las demás) con su traducción de errores y su log. | Verificación: mismo
      fichero de test — cada excepción sale con su código (R20); el log lleva
      `hash_parte`, destino y resultado y **nada más** (R44); y el endpoint
      **no mira** `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO` (R21).

- [ ] **T11**: Añadir `aprobacion` a `ContextoParte` —con la docstring que diga
      que **viene del repositorio y nunca del cuerpo**— y cambiar los tres
      `_exigir_apto` por `_exigir_admitido`, que lee la aprobación y llama a
      `admite_circuito`. | Verificación: `tests/test_f026_puertas.py` (T1)
      **sigue entero en verde**, y se le añaden los casos positivos: con
      aprobación viva del destino que declara la petición, el parte **sí**
      archiva, adjunta y cierra (R23); con aprobación revocada, **no** (R31);
      y el cuerpo de las tres peticiones **no cambia ni una clave**.

- [ ] **T12**: Añadir el bloque `aprobacion` a la respuesta de
      `POST /api/parte`. | Verificación: `tests/test_f019_parte_http.py` sigue
      en verde y un test nuevo comprueba que tras guardar un parte aprobado la
      respuesta lo dice, y que tras guardar uno sin aprobación devuelve `null`
      (R22).

---

## Bloque 4 · La pantalla

- [ ] **T13**: Añadir a `js/pipeline.js` `esAprobable`, `esCirculable`,
      `cuerpoDeAprobacion` y el `semaforoDe` con aprobación, exportados. |
      Verificación: `tests_js/aprobacion.test.js` — `semaforoDe` devuelve
      `"aprobado"` para el aprobado vigente y **nunca** `"verde"` (R36);
      `esCirculable` es verdadero para el apto y para el aprobado vigente y
      falso para el revocado; `cuerpoDeAprobacion` **no** lleva DNI,
      observaciones ni bytes (R19) y exige `usuario_oid` (R4).

- [ ] **T14**: Hacer que `pendientesDeCircuito`, `cuerpoDeArchivo`,
      `esCerrable` y `cuerpoDeGrafico` pasen por `esCirculable`, conservando
      `esArchivable` con su significado actual. | Verificación:
      `tests_js/circuito.test.js` y `tests_js/pipeline.test.js` **enteros en
      verde sin tocarlos**, más los casos nuevos: un aprobado vigente entra en
      la tanda (R23), un no apto sin aprobación sigue fuera (R25), y
      `cuerpoDeArchivo` se niega a componer para el revocado.

- [ ] **T15**: Añadir `aprobar(cuerpo, hash)` a `js/api.js` y `aprobarParte()` /
      `esAprobable()` a `js/app.js`, con `aprobacion` declarada en
      `_parteInicial` para que Alpine la haga reactiva. | Verificación:
      `tests_js/api.test.js` comprueba la ruta, el método y el `paso`;
      `tests/test_f026_front.py` comprueba que `_parteInicial` la declara —sin
      eso, la marca no repintaría— y que **no se arma ninguna confirmación
      nueva** (R29), de modo que
      `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en
      verde.

- [ ] **T16**: Añadir a `index.html` el botón «Aprobar este parte» en el
      detalle, la marca del semáforo con anillo y el texto de R36/R37, y la
      frase de R39 cuando no es aprobable. | Verificación:
      `tests/test_f026_front.py` — el botón está dentro del bloque del detalle
      y no en la lista (R35); el marcador del aprobado es **distinto** del
      verde liso (R36); el texto nombra el destino de origen y la fecha (R37);
      y **no aparece** `usuarioOid`, `oid`, `correo` ni `userDetails` en ningún
      literal de esa sección (R38, R43).

---

## Bloque 4 bis · El autoguardado de las correcciones (R50–R55)

- [ ] **TA1**: La constante del retardo en `services/postventa-front/js/config.js`
      y el disparador en `js/app.js::editarCampo`: una pausa desde la última
      pulsación, y **solo si el valor cambió** respecto a lo último guardado
      (R51). | Verificación: `test_f026_autoguardado.py` y
      `tests_js/autoguardado.test.js`: que teclear cinco veces seguidas
      produce **un** guardado y no cinco, y que reescribir el mismo valor no
      produce ninguno.

- [ ] **TA2**: El guardado reutiliza `revalidarYGuardar` (R50), de modo que el
      veredicto guardado corresponda siempre al dato guardado. | Verificación:
      un test que compruebe que **nunca** se llama a `guardarParte` sin
      `revalidar` en el mismo ciclo, y el control negativo de que no se ha
      inventado un estado de «veredicto obsoleto».

- [ ] **TA3**: Los tres estados de la pantalla (guardando, guardado, no se ha
      podido guardar) en `index.html`, con el aviso de fallo **que no se va
      solo** y lo escrito conservado (R52). | Verificación:
      `tests_js/autoguardado.test.js` con la petición fallando.

- [ ] **TA4**: Que las correcciones **no pisan** el valor ni la confianza de la
      IA (R53). | Verificación: un test que guarde una corrección y compruebe
      que lo que extrajo el modelo sigue accesible, **citando a F-015** en el
      motivo.

- [ ] **TA5**: Que la revocación de una aprobación se evalúa sobre lo guardado
      y como mucho una vez por pausa (R54), y que el autoguardado aplica a
      todos los partes (R55). | Verificación: tests de los dos.

---

## Bloque 5 · Las enmiendas y la documentación

- [ ] **T17**: Escribir el recuadro de enmienda fechado bajo **R36** de
      `specs/F-025-confirmacion-unica/requirements.md`, citando su texto
      literal y **sin borrarlo** (R46). | Verificación: un test de
      documentación con el patrón de `tests/test_f025_documentacion.py`: el
      texto original sigue ahí y el recuadro nombra F-026 y la fecha.

- [ ] **T18**: Precisar los **tres** puntos de `docs/ARCHITECTURE.md` que hoy
      dicen que solo se archiva lo apto —paso 6, semántica 3 y semántica 7—,
      añadiendo «salvo aprobación humana registrada» con su remisión a esta
      spec (R47). | Verificación: mismo test de documentación; y los tres
      puntos siguen diciendo lo que decían para todo lo demás.

- [ ] **T19**: Actualizar `azure-apps/postventa_incidencias.md` con el endpoint
      nuevo y la tabla nueva (R49). | Verificación: **otro repositorio, commit
      aparte y sin `push`**; `git -C ../azure-apps status` limpio al terminar, y
      la ruta y la tabla nombradas tal y como quedaron implementadas.

---

## Bloque 6 · Verificación contra la base real · `MANUAL (humano)`

> Escribe **solo en el esquema propio** del PostgreSQL compartido. Nada de DDL
> fuera de `postventa`, nada a nivel de servidor, y **ninguna escritura en
> Sigrid ni en SharePoint** en este bloque.

- [ ] **T20**: **El DDL se aplica y es idempotente.** | Verificación: **MANUAL
      (humano)**. Arrancar el servicio contra la base de desarrollo dos veces
      seguidas y comprobar que la segunda no falla; y
      `SELECT column_name, data_type FROM information_schema.columns WHERE
      table_schema = 'postventa' AND table_name = 'aprobaciones';` devuelve las
      nueve columnas de `design.md` §10 (R12, R16).

- [ ] **T21**: **El circuito completo de un parte aprobado.** | Verificación:
      **MANUAL (humano)**, con autorización expresa del responsable para la
      incidencia concreta y con las reglas del bloque 5 de F-025: se aprueba un
      parte que la validación mandó a la cola, se confirma la tanda **una vez**
      y se comprueba que archiva, adjunta y cierra (R23, R26, R27).

- [ ] **T22**: **La traza hasta el ERP se puede reconstruir.** | Verificación:
      **MANUAL (humano)**, consulta de **solo lectura** sobre el esquema propio:
      `SELECT a.hash_parte, a.aprobado_por, a.aprobado_at_utc,
      a.destino_aprobado, c.numero_incidencia, g.reclamacion_ide
      FROM postventa.aprobaciones a
      JOIN postventa.cierres c USING (hash_parte)
      LEFT JOIN postventa.graficos g USING (hash_parte)
      WHERE a.revocada_at_utc IS NULL;`
      Se anota que devuelve la fila del parte de T21 (R41). El `oid` **no se
      copia a `progress/`**: se anota que existe, no su valor.

- [ ] **T23**: **La revocación funciona sobre datos reales.** | Verificación:
      **MANUAL (humano)**. Sobre un parte aprobado y **no cerrado**, corregir un
      campo, revalidar, y comprobar en la base que `revocada_at_utc` está
      relleno y `revocada_motivo` es `veredicto_cambiado` (R30, R33); y que la
      pantalla vuelve a pedir la aprobación (R31).

---

## Bloque 7 · Cierre

- [ ] **T24**: Campaña de mutación (`python -m harness.mutacion --feature
      F-026`, con los workers de `harness/rigor.json`, **anotando el nº de
      workers**). | Verificación: rigor `estandar` → informe en
      `progress/mutacion_F-026.md` con **todos** los supervivientes analizados
      y ninguna sección en `PENDIENTE`. El grueso mutable es Python —dominio,
      sentencias, handler y pasos—, así que aquí el alcance **no** debería salir
      vacío; si saliera, se declara N/A **con el motivo impreso**, nunca a
      secas (C4 bis).

- [ ] **T25**: Ejecutar `bash harness/init.sh` en verde. | Verificación:
      `bash harness/init.sh` termina con exit code 0, tests incluidos —los de
      `api` y los de `front`— y con la puerta de cobertura de las líneas
      cambiadas en `[OK]` o en `N/A` **con el motivo impreso**.
