<!-- specs/F-009-cierre-sigrid/tasks.md -->
# F-009 · Cierre de la incidencia en Sigrid (solo estado) — Tareas

> Una tarea = un commit `F-009 Tn: ...`. Ordenadas por dependencia; los tests
> van antes o junto a la implementación (fase RED obligatoria en rigor
> `critico`).
>
> **No queda ninguna decisión abierta**: las seis están cerradas y fechadas en
> `design.md` §10. Se puede implementar desde T1.

## Bloque 1 · Dominio puro (sin red, sin BBDD, sin IA)

- [x] **T1**: Crear `domain/models/cierre.py` con `Reclamacion`, `PlanDeCierre`,
      `CODIGO_ESTADO_CIERRE`, `CODIGOS_ESTADO_CERRABLE` y `TEXTO_LOG_CIERRE`, y
      la función pura `evaluar(reclamacion)`. | Verificación:
      `test_f009_dominio_cierre.py` cubre R18 (ya cerrada), R19 (estado no
      cerrable, `NPR` incluido) y R21 (el plan siempre trae el aviso de que la
      reclamación quedará sin gráfico en el ERP). **Control negativo de R20**:
      `Reclamacion` no tiene campo de gráficos y el dominio no menciona `rcg`
      ni `gra`.

- [x] **T2**: Crear los errores de `domain/models/errores.py` y los puertos
      `domain/ports/erp.py` y `domain/ports/usuarios_sigrid.py`. |
      Verificación: `test_f009_arquitectura.py` comprueba que `domain/` no
      importa `httpx`, `psycopg` ni nada de `infrastructure/`.

- [x] **T3**: Test de control negativo **R3**: ningún número de estado de Sigrid
      literal en el código de producción. | Verificación:
      `test_f009_estado_no_hardcodeado.py` recorre el árbol de producción y
      falla si aparece un `est` numérico cableado. Fase RED: enseñar la traza
      del fallo con un literal introducido a propósito en una copia aislada.

## Bloque 2 · El SQL, comprobado carácter a carácter

- [x] **T4**: Crear `infrastructure/sigrid/consultas.py` con los constructores
      puros de la consulta del dry-run (`design.md` §7.1) y de la verificación
      del login (§7.2). | Verificación: `test_f009_consultas.py` fija el SQL y
      los parámetros, y comprueba R1/R4/R5 —que el estado se resuelve contra
      `conest` por `cod` y que el `tip` sale de la reclamación— más el **control
      negativo de R20**: el SQL de lectura no menciona `rcg` ni `gra`. Y los dos
      casos de aborto sin escribir: R2 (`conest` no devuelve exactamente una
      fila) y R7 (la búsqueda no devuelve exactamente una reclamación).

- [x] **T5**: Crear `infrastructure/sigrid/escrituras.py` con el batch de §7.3.
      | Verificación: `test_f009_escrituras.py` comprueba R22 (dos sentencias en
      un batch), R23 (`WHERE` con `ide`, `tip` y estado de origen; tope de 2
      filas), R24 (los campos de la fila de log, con `emp` **tomado de la
      reclamación** y no cableado), R25 (el `tex` empieza por el texto del
      proceso del ERP y nombra el servicio), R28 (el `usu` que se escribe es el
      login de la persona, nunca una constante), R35 (no excede la longitud del
      campo) y R26 (el `ide` se reserva en la
      propia sentencia y el `FROM` es `dbo.con` filtrado, **no** un
      `WHERE EXISTS`).

- [x] **T6**: Conversión del código de incidencia al formato de Sigrid. |
      Verificación: `test_f009_consultas.py` comprueba R6 — ida y vuelta contra
      `domain/models/nombrado.py`, guion largo incluido.

## Bloque 3 · El adaptador y sus puertas

- [x] **T7**: Crear `infrastructure/sigrid/cliente.py`
      (`AdaptadorSigridApi`), con `httpx`, reintentos con `tenacity` y la puerta
      de entorno **en el constructor**. | Verificación:
      `test_f009_adaptador_sigrid.py` con transporte simulado: R11 (aborta si el
      estado cambió), R27 (un fallo no se reintenta solo como cierre), R50 (no
      filtra el cuerpo crudo del error) y R36 (construirlo en `local` levanta).

- [x] **T8**: Crear `infrastructure/sigrid/fabrica.py` con el orden
      entorno → interruptor → configuración. | Verificación:
      `test_f009_fabrica.py` comprueba R37 (doble comprobación: fábrica **y**
      adaptador) y R38 (nombra todas las variables que faltan de una vez y
      **ningún** valor).

- [x] **T9**: Añadir a `config/settings.py` el bloque de F-009 y extender la
      guardia de red de la suite a `sigrid-api`. | Verificación:
      `test_f009_fabrica.py` y la guardia existente: R39 — ningún test abre una
      conexión hacia `sigrid-api` y ninguno puede ejecutar una escritura.

## Bloque 4 · El mapeo de usuarios

- [x] **T10**: Crear `infrastructure/persistencia/sql/08_usuarios_sigrid.sql` y
      registrarlo en `ddl.py` / `arranque.py`. | Verificación:
      `test_f009_ddl_orden.py` y los `test_f005_ddl_*` existentes: idempotente,
      dentro del schema propio y **nunca** en `public`.

- [x] **T11**: Añadir `select_login_sigrid` / `upsert_login_sigrid` a
      `sentencias.py`, `repositorio_pg.py` y `mapeo.py`. | Verificación:
      `test_f009_usuarios_sigrid.py` con el doble de PG: R29 (si hay
      correspondencia confirmada se usa **sin derivar nada**), R30 (si no la
      hay, se deriva el candidato del correo y se verifica), R31 (candidato
      inexistente o ambiguo → no se cierra), R32 (nunca se escribe un login sin
      verificar), R33 (lo verificado se guarda como confirmado) y R34 (el alta
      manual tiene **precedencia** sobre la derivación).

- [x] **T12**: Crear `infra/07_alta_usuario_sigrid.ps1` para el **alta manual**
      de una correspondencia (R34), re-ejecutable y sin credenciales dentro. |
      Verificación: `test_f009_scripts_infra.py`, al modo de
      `test_f005_scripts_infra.py` — el script existe, es idempotente y no trae
      ningún secreto ni ningún login concreto.

## Bloque 5 · El paso del pipeline

- [x] **T13**: Crear `application/pipelines/paso_cierre.py` con el orden de
      `design.md` §6. | Verificación: `test_f009_paso_cierre.py` con dobles:
      R8 y R10 (el dry-run va primero y sin él no se escribe), R16, R17, R20
      (**la precondición es propia: nada de `rcg` ni `gra`**), R40, R41 y R42
      (`cerrado` es terminal y no se pisa).

- [x] **T14**: Auto-cierre por preferencia. | Verificación:
      `test_f009_paso_cierre.py`: R12, R13 (encadena sin saltarse el dry-run ni
      ninguna validación) y R14 (por omisión, **falso**).

- [x] **T15**: Control negativo de datos personales en el log del paso. |
      Verificación: `test_f009_logs_sin_datos_personales.py` — R41, R42, R43,
      al modo de `test_f005_logs_sin_datos_personales.py` y del de F-019: hacer
      pasar DNI, nombre, observaciones manuscritas, correo, login y una clave de
      función por el camino real y comprobar que **ninguno** aparece en la
      salida — R44 (datos del parte y del propietario), R45 (identidad de quien
      confirma) y R46 (secretos, ni en logs ni en mensajes de error). **Sin el
      control negativo, un logger mudo pasaría igual.**

## Bloque 6 · El borde HTTP y el front

- [x] **T16**: Crear `interface_adapters/api/cerrar.py` y registrar la ruta en
      `function_app.py`, con la traducción de errores. | Verificación:
      `test_f009_cerrar_http.py`: R47 (400 diciendo qué falta), R48 (409,
      incluido el caso de login sin confirmar), R49 (503 sin tocar Sigrid), R50
      (502) y R51 (ni un campo manuscrito en la respuesta). Y que el mensaje de
      R31 nombra el correo **al usuario** sin que eso acabe en el log (R45).

- [x] **T17**: Añadir `cerrar()` a `services/postventa-front/js/api.js`. |
      Verificación: `services/postventa-front/tests_js/api.test.js`.

- [x] **T18**: Paso de cierre en el front: enseñar el dry-run —estados legibles,
      con qué login se firmaría y **el aviso de que la reclamación quedará
      cerrada sin el parte dentro de Sigrid**— y pedir confirmación reutilizando
      `js/confirmacion.js`. | Verificación: `tests_js/confirmacion.test.js` y
      `test_f007_js.py`: R15 (la confirmación caduca y un segundo clic fuera de
      ventana no dispara), R9 (el dry-run enseña las cinco cosas) y R21 (el
      aviso se pinta **siempre**, no solo a veces).

## Bloque 7 · Documentación que la feature deja al día

- [x] **T19**: Actualizar `docs/ARCHITECTURE.md` (paso 7 del pipeline, «Alcance
      del cierre», tabla de sistemas externos) y `docs/DESPLIEGUE.md` (la App
      Setting del interruptor y cómo se abre). **`ARCHITECTURE.md` §«Alcance del
      cierre» dice hoy que el ERP comprueba el gráfico y que por eso el alcance
      está «en el aire»: hay que sustituirlo por el orden decidido —validar →
      cerrar → subir el PDF— y por el riesgo aceptado de `design.md` §2**, sin
      suavizarlo. | Verificación: `test_f019_documentacion.py` extendido, o su
      equivalente de F-009.

- [x] **T20**: Actualizar `docs/INTEGRACION.md` con lo que ahora **escribimos**
      en Sigrid. | Verificación: R52 — un test comprueba que las variables
      nuevas están nombradas y que **ningún valor** aparece.

- [x] **T21**: Actualizar `azure-apps/postventa_incidencias.md` (R53): este
      servicio escribe en el ERP, qué escribe y qué se rompe si alguien cambia la
      configuración de escritura de la pasarela. **Añadir además el obstáculo de
      `design.md` §11**: el binario del parte vive en la base documental, que hoy
      **no es escribible** por la pasarela — es lo que le espera a F-012 y le
      toca decidirlo al dueño de `sigrid-api`. | Verificación: **MANUAL
      (humano)** — es **otro repositorio**; commit local allí, sin push, y la
      regla de propiedad del `CLAUDE.md` obliga a hacerlo **en este mismo
      trabajo**. Enlazar, nunca duplicar.

## Bloque 8 · Verificación contra el ERP de producción

> **REGLA DURA**: prohibido escribir en Sigrid desde local o desde tests. Todo
> este bloque se ejecuta **desde el entorno desplegado**, con el humano
> delante, y tras autorización expresa para esa acción concreta. Es el
> equivalente de la T24 de F-019.

- [ ] **T22**: **Dry-run real** contra una reclamación de Mirasierra, desde el
      entorno desplegado y con el interruptor **apagado**. | Verificación:
      **MANUAL (humano)**. Elegir una incidencia del piloto y llamar a
      `POST /api/cerrar` con `commit: false`. Se espera: el código y la
      descripción de la reclamación, el estado de origen legible, el destino
      `CER`, el login con el que se firmaría y **el aviso de que quedará cerrada
      sin el parte dentro de Sigrid** (R21). **Nada debe cambiar en el ERP**:
      comprobarlo releyendo `con.est` con `POST /api/sql/read`, que debe seguir
      en el estado de origen.

- [ ] **T23**: **La siembra del login, contra el ERP** (R30–R33). |
      Verificación: **MANUAL (humano)**, en tres pasos:
      1. Con la tabla de correspondencias **vacía** para ese usuario, ejecutar
         el dry-run: el login candidato se deriva de su correo y **se verifica**
         contra `dbo.usu`. Comprobar que el candidato existe **exactamente una
         vez**.
      2. Comprobar que la correspondencia quedó **guardada como confirmada** en
         `postventa.usuarios_sigrid` (R33), y que un segundo dry-run **ya no
         deriva nada**.
      3. Con un usuario cuyo candidato **no exista** en `dbo.usu`, comprobar que
         responde **409** nombrando el correo y el login intentado, **sin tocar
         Sigrid** (R31). Es el caso de los 2 de 8 medidos que no siguen la
         convención, y se resuelve con el alta manual de T12 (R34).

- [ ] **T24**: **El primer cierre real**, con autorización expresa del humano
      para esa incidencia concreta. | Verificación: **MANUAL (humano)**.
      Procedimiento, en este orden y sin saltarse ningún paso:
      1. Anotar el estado de partida: `SELECT ide, est FROM dbo.con WHERE tip = ? AND cod = ?`.
      2. Anotar `SELECT MAX(ide) FROM dbo.log`.
      3. Ejecutar el dry-run (T22) y **leerlo**.
      4. Confirmar en el front y ejecutar con `commit: true`.
      5. Comprobar que la respuesta declara **2 filas afectadas** (R22).
      6. Releer `con.est`: debe ser el `est` de `conest` con `cod = 'CER'`.
      7. Leer la fila nueva de `dbo.log` y comprobar **campo a campo** contra
         `design.md` §7.3: `tab`, `tip`, `cod`, `res`, `ope`, `est`, `ori`,
         `emp`, `usu` y el `tex` propio (R24, R25).
      8. Comprobar que **`con.tiemod` no se ha movido**, como en el ERP
         (F-008 §2.3).
      9. Comprobar que la traza local quedó en `cerrado` con su `oid` y sus
         códigos de estado (R41), y que **no guarda el login** (R43).

- [ ] **T25**: **Comprobar que el `tex` propio hace lo que se diseñó** (R25). |
      Verificación: **MANUAL (humano)**. Dos lecturas: que
      `tex LIKE 'Cerrar parte%'` **encuentra** el cierre nuevo (seguimos en los
      informes de Posventa) y que el filtro por el texto propio devuelve
      **exactamente los cierres de este servicio** y ninguno manual.

- [ ] **T26**: **Comprobar que el guard de escritura acepta el batch tal cual**.
      | Verificación: **MANUAL (humano)**, y se hace **dentro de T24**: si
      `SqlWriteGuard` rechazara la sugerencia de tabla `WITH (UPDLOCK,
      HOLDLOCK)`, anotarlo y caer a la variante sin sugerencias — que **sigue
      fallando en seguro** por la clave única de `log.ide` (`design.md` §7.3).
      No improvisar otra vía: si el guard rechaza algo no previsto, la feature
      se marca `blocked` y se para.

- [ ] **T27**: **Reintento sobre lo ya cerrado** (R18, R42). | Verificación:
      **MANUAL (humano)**. Repetir T24 sobre la misma incidencia: debe salir
      `ya_cerrada`, **sin escribir nada en Sigrid** —comprobar que `MAX(ide)` de
      `dbo.log` no ha subido— y sin pisar la traza local.

## Bloque 9 · Cierre

- [ ] **T28**: Campaña de mutación (`python -m harness.mutacion --feature
      F-009`) y análisis de los supervivientes. | Verificación: rigor `critico`
      → **cero supervivientes** sin justificación escrita aceptada por el
      humano; informe en `progress/mutacion_F-009.md` con el nº de workers.

- [ ] **T29**: Ejecutar `bash harness/init.sh` en verde. | Verificación:
      `bash harness/init.sh` termina con exit code 0, tests incluidos y con la
      puerta de cobertura de las líneas cambiadas en `[OK]`.
