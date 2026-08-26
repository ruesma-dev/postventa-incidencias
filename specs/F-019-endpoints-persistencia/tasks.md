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
      repositorio**, `usuario_oid` en `None`.
      **Verificación**: los tests **fallan**.

- [ ] **T5**: Implementar `interface_adapters/api/remesa.py` y la ruta
      `POST /api/remesa` en `function_app.py` (`ANONYMOUS`), con el mapeo de
      errores a 400/503.
      **Verificación**: `pytest services/postventa-api/tests/test_f019_remesa_http.py`
      en verde.

## Fase 3 · `POST /api/parte`

- [ ] **T6 · RED**: `services/postventa-api/tests/test_f019_parte_http.py`
      con R7–R13. Los tres que no pueden faltar:
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
      R14–R17: serialización completa de `EntradaCola`, límite por defecto 50,
      tope de 500, 400 con un `limite` no entero **sin consultar el
      repositorio**, y el log **sin** observaciones (con `caplog`).
      **Verificación**: los tests **fallan**.

- [ ] **T9**: Implementar `interface_adapters/api/cola.py` y la ruta
      `GET /api/cola` en `function_app.py` (`ANONYMOUS`).
      **Verificación**: `pytest services/postventa-api/tests/test_f019_cola_http.py`
      en verde.

## Fase 5 · La garantía de orden (el corazón de la feature)

- [ ] **T10 · RED**: `services/postventa-api/tests/test_f019_orden_archivado.py`
      con R18–R23. Los cinco que fijan el requisito:
      1. en el camino feliz, `guardar_archivo` se llama **dos** veces y la
         primera es `estado='pendiente'`, **antes** de la primera llamada al
         archivador (se comprueba con un doble que registra el orden global de
         llamadas a los dos puertos);
      2. si la traza previa levanta `ReferenciaNoConsta`, el archivador **no
         recibe ninguna llamada** —ni `asegurar_carpeta`— y el borde responde
         **409**;
      3. si levanta `PersistenciaNoDisponible`, **503** y tampoco se llama al
         archivador;
      4. con el parte ya archivado, **no** se escribe la traza previa (R23);
      5. con la ventana de escritura cerrada, **503** y el repositorio no
         recibe **ninguna** llamada (R22).
      Y ajustar `test_f006_paso_archivo.py` a la llamada nueva **exigiendo dos
      llamadas en orden**, nunca relajando la cuenta.
      **Verificación**: los tests nuevos **fallan** y los de F-006 quedan
      escritos contra el comportamiento nuevo.

- [ ] **T11**: Implementar la traza previa `pendiente` en
      `application/pipelines/paso_archivo.py` (después de la aptitud, del
      nombrado y de la idempotencia; antes de `_subir`) y el mapeo de
      `ReferenciaNoConsta` → **409** en la ruta `archivar` de `function_app.py`,
      con un mensaje que diga qué hacer (`POST /api/parte` primero).
      **Verificación**: `pytest services/postventa-api/tests/test_f019_orden_archivado.py
      services/postventa-api/tests/test_f006_paso_archivo.py
      services/postventa-api/tests/test_f006_archivar_http.py` en verde.

- [ ] **T12**: Añadir a `services/postventa-api/tests/test_f005_ddl_idempotente_texto.py`
      la aserción de que `05_archivos.sql` declara la clave ajena de
      `hash_parte` contra `postventa.partes` (riesgo 4 de `design.md` §14):
      es la restricción en la que se apoya toda la garantía de orden y hoy
      nadie la fija.
      **Verificación**: el test falla si se borra esa línea del DDL (se
      comprueba a mano quitándola y devolviéndola).

## Fase 6 · Que la documentación no mienta

- [ ] **T13**: Ampliar la cabecera de `function_app.py` (los nueve endpoints y
      el riesgo nuevo de `/api/cola`, R29) y extender
      `services/postventa-api/tests/test_f010_endpoints_protegidos.py` a
      **nueve** endpoints, incluida la cuenta del control negativo (R28).
      **Verificación**: `pytest services/postventa-api/tests/test_f010_endpoints_protegidos.py`
      en verde, y sigue fallando si alguien pone `FUNCTION` en cualquiera de
      los nueve.

- [ ] **T14**: Actualizar `docs/INTEGRACION.md` §8 (tres filas nuevas en la
      tabla de endpoints, con su efecto; y la tabla de «qué NO está
      desplegado»: F-019 deja de ser la causa de perder el trabajo al
      recargar, que pasa a ser la rehidratación de sesión, todavía pendiente)
      y `docs/ARCHITECTURE.md` (paso 6: sólo se archiva lo que ya consta
      guardado, y con qué mecanismo). Ajustar
      `test_f010_integracion_expuesto.py` (lista de endpoints y
      `NO_DESPLEGADAS`) y escribir `test_f019_documentacion.py` con R30–R31.
      **Verificación**: `pytest services/postventa-api/tests/test_f010_integracion_expuesto.py
      services/postventa-api/tests/test_f019_documentacion.py` en verde.
      **No se hace commit en `azure-apps/`**: el humano decidió el 2026-08-20
      que los agentes no commitean ahí (`specs/F-006-sharepoint/tasks.md` T19).
      Se anota en `progress/impl_F-019.md` que §8 ha cambiado y hay que
      copiarla.

## Fase 7 · El front llama en orden (decisión abierta D5: recomendado que sí)

- [ ] **T15 · RED**: `services/postventa-front/tests_js/persistencia.test.js`
      con R24–R27, contra un `api` doble que registra el **orden** de las
      llamadas: la remesa se registra antes de procesar partes; `guardar`
      ocurre después de `validar` y antes de cualquier `archivar`; un fallo al
      guardar deja el parte **no archivable** con su motivo; revalidar vuelve a
      guardar.
      **Verificación**: `node --test services/postventa-front/tests_js/` con
      los tests nuevos **en rojo**.

- [ ] **T16**: Implementar el cableado: `js/api.js` (`registrarRemesa`,
      `guardarParte`, `cola`), `js/pipeline.js` (cuerpo de `/api/parte` y
      guardado tras validar y tras revalidar) y `js/app.js` (registro de la
      remesa tras trocear, `remesaId` en el estado, parte no archivable si el
      guardado falla).
      **Verificación**: `node --test services/postventa-front/tests_js/` entero
      en verde, incluidos `pipeline.test.js` y `api.test.js` de F-007.

## Fase 8 · Puertas del rigor `estandar`

- [ ] **T17**: Cobertura de las líneas cambiadas ≥ 80 %, con los ficheros
      nuevos **medidos** (ninguno «no medido»: `CHECKPOINTS.md` C4 bis).
      **Verificación**: `bash harness/init.sh` con `PUERTA COBERTURA` en `[OK]`,
      y el porcentaje anotado en `progress/impl_F-019.md`.

- [ ] **T18**: Campaña de mutación con **todos** los supervivientes
      analizados (ninguno en `PENDIENTE`). El nivel `estandar` no exige cero:
      exige que estén explicados.
      **Verificación**: `python -m harness.mutacion --feature F-019` genera
      `progress/mutacion_F-019.md` con sus totales y cada superviviente con su
      sección escrita.

- [ ] **T19**: `bash harness/init.sh` **en verde** (exit 0, con la suite del
      backend y la del front) y escribir `progress/impl_F-019.md` con la
      sección **Evidencias**: tests ejecutados y resultado, cobertura de las
      líneas cambiadas, mutantes y supervivientes, y tiempo de la suite.
      **Verificación**: `bash harness/init.sh` termina con
      `ENTORNO LISTO. Puedes trabajar.` y exit code 0.

## Fase 9 · Lo que sólo se puede verificar contra el entorno desplegado

- [ ] **T20**: **Verificación: MANUAL (humano)** — el circuito completo del
      defecto 15, contra el despliegue y **con la ventana de escritura abierta
      a propósito para la prueba**, con un parte sintético (nunca con un parte
      real de `muestras/`, que lleva datos personales):
      1. `POST /api/archivar` **sin** haber guardado el parte → debe responder
         **409** y **no** debe aparecer nada en la biblioteca de SharePoint
         (se comprueba mirando la carpeta).
      2. `POST /api/remesa` → `POST /api/parte` → `POST /api/archivar` → debe
         responder **200**, el fichero debe estar en su carpeta **una sola vez**
         y `postventa.archivos` debe tener su fila en `archivado`.
      3. `GET /api/cola` con un parte con observaciones → devuelve su entrada.
      4. Repetir 2 entero → sin duplicados y con `reprocesos` incrementado.
      Comando: los mismos `Invoke-RestMethod -BaseUrl ...` del guion de T18 de
      F-010, ampliados; el guion se deja en `progress/impl_F-019.md`, **sin
      URLs con secretos y sin datos personales**.
      Al terminar: **volver a cerrar la ventana de escritura** y anotar el
      resultado real (no «debería funcionar»).

---

## Antes de empezar: decisiones que el humano puede querer contestar

Están razonadas en `design.md` §15. Sólo **D5** cambia el contenido de esta
lista. Con silencio se implementa la recomendación.

- **D1** — `GET /api/cola` es anónimo y devuelve datos personales →
  **ANONYMOUS como los demás**, con tope de límite y el riesgo escrito
  (T9, T13); y valorar la restricción de acceso público de la Function App.
- **D2** — `remesas` sin clave natural → **se acepta** (§7); no toca el DDL.
- **D3** — `usuario_oid` → **sigue en `NULL`** (T5).
- **D4** — rehidratar la sesión al recargar → **fuera**, feature nueva.
- **D5** — ¿entra el cableado del front? → **sí** (T15, T16). Si el humano
  dice que no, se caen T15 y T16 y R24–R27, y hay que decir al cerrar que
  **el archivado real sigue sin poder completar en el circuito del piloto**.
