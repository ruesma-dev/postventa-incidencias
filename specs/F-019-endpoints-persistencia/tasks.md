<!-- specs/F-019-endpoints-persistencia/tasks.md -->
# F-019 · Tareas

> Rigor **`estandar`**: **fase RED obligatoria** (el test se escribe y se ve
> fallar antes de la implementación), **cobertura ≥ 80 % de las líneas
> cambiadas** y **campaña de mutación con supervivientes analizados**
> (`harness/rigor.json`, `CHECKPOINTS.md` C4 bis).
>
> Cada tarea = un commit (`F-019 Tn: descripción`). Ordenadas por dependencia.
> Ningún test de esta lista toca red, base de datos ni IA, salvo la marcada
> `MANUAL (humano)`.
>
> **Las cinco decisiones del humano están resueltas** (`design.md` §15). No hay
> nada esperando respuesta: se implementa esta lista entera.

## Fase 0 · Preparar el terreno

- [ ] **T1**: Mover los parsers de cuerpo de `interface_adapters/api/validar.py`
      a `interface_adapters/api/cuerpos.py` (`bloque`, `a_extraccion`,
      `a_campo`, `a_traza`, `a_lectura_de_firma` y sus constantes de claves), y
      dejar `validar.py` importándolos. **Movimiento mecánico: ni una regla
      cambia, ni un mensaje de error cambia.**
      **Verificación**: `pytest services/postventa-api/tests/test_f004_validar_http.py`
      en verde **sin haber tocado ese fichero de test** (es la red que
      demuestra que el comportamiento público no se movió).

## Fase 1 · El error de referencia (lo que hace posible la garantía de orden)

- [ ] **T2 · RED**: Escribir `services/postventa-api/tests/test_f019_referencias_pg.py`:
      con una conexión doble que levanta `psycopg.errors.ForeignKeyViolation`,
      el repositorio debe levantar `ReferenciaNoConsta` (y seguir levantando
      `PersistenciaNoDisponible` con cualquier otro `psycopg.Error`).
      **Verificación**: los tests **fallan** (`ImportError`/`AssertionError`) y
      se deja constancia del rojo en `progress/impl_F-019.md`.

- [ ] **T3**: Añadir `ReferenciaNoConsta(ErrorDePersistencia)` en
      `domain/models/errores.py` y distinguir `ForeignKeyViolation` en
      `infrastructure/persistencia/repositorio_pg.py::_escribir`. El motivo
      nombra **la operación** y jamás los parámetros (llevan DNI y
      observaciones).
      **Verificación**: `pytest services/postventa-api/tests/test_f019_referencias_pg.py`
      en verde, y `test_f005_repositorio.py` + `test_f005_repo_sin_datos_personales.py`
      siguen verdes.

## Fase 2 · `POST /api/remesa`

- [ ] **T4 · RED**: `services/postventa-api/tests/test_f019_remesa_http.py`
      con R1–R6: alta con id generado, alta idempotente con `remesa_id` dado,
      400 por cuerpo inválido, 400 por uuid inválido **sin llegar al
      repositorio**, `usuario_oid` en `None`, y respuesta normal **con la
      ventana de escritura cerrada** (R34).
      **Verificación**: los tests **fallan**.

- [ ] **T5**: Implementar `interface_adapters/api/remesa.py` y la ruta
      `POST /api/remesa` en `function_app.py` (`ANONYMOUS`), con el mapeo de
      errores a 400/503.
      **Verificación**: `pytest services/postventa-api/tests/test_f019_remesa_http.py`
      en verde.

## Fase 3 · `POST /api/parte`

- [ ] **T6 · RED**: `services/postventa-api/tests/test_f019_parte_http.py`
      con R7–R13 y R34. Los tres que no pueden faltar:
      1. el veredicto **se recalcula** y un veredicto metido en el cuerpo se
         ignora (R8);
      2. guardar dos veces el mismo `hash_parte` devuelve `actualizado` y no
         crea una segunda fila (R9);
      3. con la remesa inexistente (`ReferenciaNoConsta`) responde **409** y no
         deja fila (R11).
      **Verificación**: los tests **fallan**.

- [ ] **T7**: Implementar `interface_adapters/api/parte.py` —reconstrucción de
      `ParteTroceado`, `ExtraccionParte` y `LecturaFirma` con los parsers de
      T1, `validar_parte` y `paso_persistencia`— y la ruta `POST /api/parte`
      en `function_app.py` (`ANONYMOUS`), con el mapeo 400/409/503.
      **Verificación**: `pytest services/postventa-api/tests/test_f019_parte_http.py`
      en verde.

## Fase 4 · `GET /api/cola`

- [ ] **T8 · RED**: `services/postventa-api/tests/test_f019_cola_http.py` con
      R14, R15, R17 y R34: serialización completa de `EntradaCola`, límite por
      defecto **50**, 400 con un `limite` no entero **sin consultar el
      repositorio**, y respuesta normal con la ventana de escritura cerrada.
      **Verificación**: los tests **fallan**.

- [ ] **T9**: Implementar `interface_adapters/api/cola.py` y la ruta
      `GET /api/cola` en `function_app.py` (`ANONYMOUS`).
      **Verificación**: `pytest services/postventa-api/tests/test_f019_cola_http.py`
      en verde.

- [ ] **T10 · RED**: El **tope duro** (R16), en su propio test dentro de
      `test_f019_cola_http.py`: con `limite=100000` —y con cualquier número
      mayor que el techo— el repositorio recibe **exactamente**
      `LIMITE_MAXIMO_COLA` (500) y la respuesta no puede traer más entradas que
      eso. La petición se **acota**, no se rechaza (R16).
      **Verificación**: el test **falla** (hoy el handler pasa el número tal
      cual).

- [ ] **T11**: Acotar el límite **en el handler**, además del techo que ya
      aplica `sentencias._limite_seguro`. Son dos cinturones a propósito: el
      que falla es el que no se ve, y el handler es el que decide qué se le
      pide a un servidor compartido de 1 vCPU.
      **Verificación**: `pytest services/postventa-api/tests/test_f019_cola_http.py`
      en verde, incluido el test de T10.

- [ ] **T12**: `services/postventa-api/tests/test_f019_logs_sin_datos_personales.py`
      (R18): con `caplog`, los tres endpoints nuevos registran identificadores,
      resultados y **cuántas** entradas trae la cola, y **nunca** el DNI, las
      observaciones, la descripción ni la promoción. Es un **test guardián**:
      si nace verde, hay que demostrar que sabría fallar, con un control
      negativo como el de
      `test_f005_r29_el_test_veria_una_fuga_si_la_hubiera`.
      **Verificación**: `pytest services/postventa-api/tests/test_f019_logs_sin_datos_personales.py
      services/postventa-api/tests/test_f005_logs_sin_datos_personales.py` en verde,
      **y el control negativo falla cuando se le mete la fuga a mano**.

## Fase 5 · La garantía de orden (el corazón de la feature)

- [ ] **T13 · RED**: `services/postventa-api/tests/test_f019_orden_archivado.py`
      con R19–R24. Los cinco que fijan el requisito:
      1. en el camino feliz, `guardar_archivo` se llama **dos** veces y la
         primera es `estado='pendiente'`, **antes** de la primera llamada al
         archivador (se comprueba con un doble que registra el orden global de
         llamadas a los dos puertos);
      2. si la traza previa levanta `ReferenciaNoConsta`, el archivador **no
         recibe ninguna llamada** —ni `asegurar_carpeta`— y el borde responde
         **409**;
      3. si levanta `PersistenciaNoDisponible`, **503** y tampoco se llama al
         archivador;
      4. con el parte ya archivado, **no** se escribe la traza previa (R24);
      5. con la ventana de escritura cerrada, **503** y el repositorio no
         recibe **ninguna** llamada (R23).
      Y ajustar `test_f006_paso_archivo.py` a la llamada nueva **exigiendo dos
      llamadas en orden**, nunca relajando la cuenta.
      **Verificación**: los tests nuevos **fallan** y los de F-006 quedan
      escritos contra el comportamiento nuevo.

- [ ] **T14**: Implementar la traza previa `pendiente` en
      `application/pipelines/paso_archivo.py` (después de la aptitud, del
      nombrado y de la idempotencia; antes de `_subir`) y el mapeo de
      `ReferenciaNoConsta` → **409** en la ruta `archivar` de `function_app.py`,
      con un mensaje que diga qué hacer (`POST /api/parte` primero).
      **Verificación**: `pytest services/postventa-api/tests/test_f019_orden_archivado.py
      services/postventa-api/tests/test_f006_paso_archivo.py
      services/postventa-api/tests/test_f006_archivar_http.py` en verde.

- [ ] **T15**: Añadir a `services/postventa-api/tests/test_f005_ddl_idempotente_texto.py`
      la aserción de que `05_archivos.sql` declara la clave ajena de
      `hash_parte` contra `postventa.partes` (riesgo 4 de `design.md` §14):
      es la restricción en la que se apoya toda la garantía de orden y hoy
      nadie la fija.
      **Verificación**: el test falla si se borra esa línea del DDL (se
      comprueba a mano quitándola y devolviéndola).

## Fase 6 · Que la documentación no mienta

- [ ] **T16**: Poner al día la cabecera de `function_app.py` (R30): los nueve
      endpoints, **dónde está la protección de verdad** —backend enlazado con
      Easy Auth `azureStaticWebApps` + regla `/*` de la Static Web App + grupo
      de Posventa, según `docs/DESPLIEGUE.md` §5 bis— y qué añade `/api/cola`
      a ese cuadro: dato personal acumulado ante **un usuario ya autenticado
      del grupo**, no ante internet. Y ampliar `ENDPOINTS` a **nueve** en
      `services/postventa-api/tests/test_f010_endpoints_protegidos.py`,
      incluida la cuenta del control negativo (R29).
      **Verificación**: `pytest services/postventa-api/tests/test_f010_endpoints_protegidos.py`
      en verde, y sigue fallando si alguien pone `FUNCTION` en cualquiera de
      los nueve.

- [ ] **T17**: **Corregir la cabecera de
      `services/postventa-api/tests/test_f010_endpoints_protegidos.py`** (R31),
      que hoy documenta un modelo de amenaza desactualizado: dice que «al
      desplegar, los seis endpoints quedan **en internet** con
      `auth_level=ANONYMOUS`», y desde el enlace del backend (defecto 13 de
      F-010, 2026-08-25) eso ya no es cierto. Debe contar el modelo vigente y
      **por qué el `auth_level` sigue en `ANONYMOUS`**: porque `FUNCTION`
      rompería el front. **Tarea propia para que no se pierda entre la
      ampliación a nueve de T16.**
      **Verificación**: `pytest services/postventa-api/tests/test_f010_endpoints_protegidos.py`
      en verde; y el test **no se relaja**: se comprueba a mano que sigue
      fallando (a) al cambiar un `auth_level` sin tocar la explicación y (b) al
      borrar la explicación sin tocar el `auth_level`.

- [ ] **T18**: Actualizar `docs/INTEGRACION.md` §8 (tres filas nuevas en la
      tabla de endpoints, con su efecto; y la tabla de «qué NO está
      desplegado»: F-019 deja de ser la causa de perder el trabajo al
      recargar, que pasa a ser la rehidratación de sesión, todavía pendiente y
      **feature nueva** por decisión D4) y `docs/ARCHITECTURE.md` (paso 6:
      sólo se archiva lo que ya consta guardado, y con qué mecanismo). Ajustar
      `test_f010_integracion_expuesto.py` (lista de endpoints y
      `NO_DESPLEGADAS`) y escribir `test_f019_documentacion.py` con R32–R33.
      **Verificación**: `pytest services/postventa-api/tests/test_f010_integracion_expuesto.py
      services/postventa-api/tests/test_f019_documentacion.py` en verde.
      **No se hace commit en `azure-apps/`**: el humano decidió el 2026-08-20
      que los agentes no commitean ahí (`specs/F-006-sharepoint/tasks.md` T19).
      Se anota en `progress/impl_F-019.md` que §8 ha cambiado y hay que
      copiarla.

## Fase 7 · El front llama en orden (decisión D5: entra)

- [ ] **T19 · RED**: `services/postventa-front/tests_js/persistencia.test.js`
      con R25–R28, contra un `api` doble que registra el **orden** de las
      llamadas: la remesa se registra antes de procesar partes; `guardar`
      ocurre después de `validar` y antes de cualquier `archivar`; un fallo al
      guardar deja el parte **no archivable** con su motivo; revalidar vuelve a
      guardar.
      **Verificación**: `node --test services/postventa-front/tests_js/` con
      los tests nuevos **en rojo**.

- [ ] **T20**: Implementar el cableado: `js/api.js` (`registrarRemesa`,
      `guardarParte`, `cola`), `js/pipeline.js` (cuerpo de `/api/parte` y
      guardado tras validar y tras revalidar) y `js/app.js` (registro de la
      remesa tras trocear, `remesaId` en el estado, parte no archivable si el
      guardado falla).
      **Verificación**: `node --test services/postventa-front/tests_js/` entero
      en verde, incluidos `pipeline.test.js` y `api.test.js` de F-007.

## Fase 8 · Puertas del rigor `estandar`

- [ ] **T21**: Cobertura de las líneas cambiadas ≥ 80 %, con los ficheros
      nuevos **medidos** (ninguno «no medido»: `CHECKPOINTS.md` C4 bis).
      **Verificación**: `bash harness/init.sh` con `PUERTA COBERTURA` en `[OK]`,
      y el porcentaje anotado en `progress/impl_F-019.md`.

- [ ] **T22**: Campaña de mutación con **todos** los supervivientes
      analizados (ninguno en `PENDIENTE`). El nivel `estandar` no exige cero:
      exige que estén explicados.
      **Verificación**: `python -m harness.mutacion --feature F-019` genera
      `progress/mutacion_F-019.md` con sus totales y cada superviviente con su
      sección escrita.

- [ ] **T23**: `bash harness/init.sh` **en verde** (exit 0, con la suite del
      backend y la del front) y escribir `progress/impl_F-019.md` con la
      sección **Evidencias**: tests ejecutados y resultado, cobertura de las
      líneas cambiadas, mutantes y supervivientes, y tiempo de la suite.
      **Verificación**: `bash harness/init.sh` termina con
      `ENTORNO LISTO. Puedes trabajar.` y exit code 0.

## Fase 9 · Lo que sólo se puede verificar contra el entorno desplegado

- [ ] **T24**: **Verificación: MANUAL (humano)** — el circuito completo del
      defecto 15, contra el despliegue y **con la ventana de escritura abierta
      a propósito para la prueba**, con un parte sintético (nunca con un parte
      real de `muestras/`, que lleva datos personales).

      **La vía es la consola del navegador en el front, con sesión iniciada**
      (`docs/DESPLIEGUE.md` §5 bis): el host desnudo de la Function devuelve
      `400` de la plataforma a todo el mundo, así que **no hay `-BaseUrl` que
      sirva**. Las llamadas van al mismo origen y pasan por el proxy.

      1. `POST /api/archivar` **sin** haber guardado el parte → debe responder
         **409** y **no** debe aparecer nada en la biblioteca de SharePoint
         (se comprueba mirando la carpeta).
      2. `POST /api/remesa` → `POST /api/parte` → `POST /api/archivar` → debe
         responder **200**, el fichero debe estar en su carpeta **una sola vez**
         y `postventa.archivos` debe tener su fila en `archivado`.
      3. `GET /api/cola` con un parte con observaciones → devuelve su entrada;
         y con `limite=100000` devuelve como mucho 500 (R16).
      4. Repetir 2 entero → sin duplicados y con `reprocesos` incrementado.

      El fragmento de consola se deja en `progress/impl_F-019.md`, **sin
      secretos y sin datos personales**. Al terminar: **volver a cerrar la
      ventana de escritura** y anotar el resultado real (no «debería
      funcionar»).

---

## Las cinco decisiones del humano, ya resueltas

Razonadas en `design.md` §15. **Ninguna bloquea nada**: esta lista ya las
incorpora.

- **D1** — `GET /api/cola` se queda **`ANONYMOUS`**, y el `auth_level` es
  irrelevante desde internet: el backend enlazado sólo acepta lo que entra por
  el proxy, y el proxy exige sesión. Entran el **tope duro** (T10, T11), el
  **log sin dato personal** (T12) y la **cabecera al día** (T16). **Descartado**
  exigir `x-ms-client-principal`.
- **D2** — `remesas` sin clave natural: **se acepta**; no toca el DDL.
- **D3** — `usuario_oid` **sigue en `NULL`** (T5).
- **D4** — rehidratar la sesión al recargar: **feature nueva**, y hay que
  decirlo al cerrar F-019 (T18, T23).
- **D5** — el cableado del front **entra** (T19, T20).
