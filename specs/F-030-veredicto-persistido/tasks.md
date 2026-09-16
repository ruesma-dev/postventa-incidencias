<!-- specs/F-030-veredicto-persistido/tasks.md -->
# F-030 · La aprobación humana no sobrevive a la puerta de F-028 — Tareas

> Una tarea = un commit `F-030 Tn: ...`. Ordenadas por dependencia; los tests
> van **antes o junto** a la implementación (**fase RED obligatoria**, rigor
> `critico`, cero supervivientes de mutación).
>
> La rama es `feature/F-030-veredicto-persistido`, ya creada desde `dev`.
>
> **Los encargos al implementer se dan de uno en uno, por bloques**, y el
> implementer **para** al terminar cada bloque. Esto arregla una regresión en
> producción sobre la única puerta que separa un parte sin revisar de un PDF
> con el DNI de un cliente en SharePoint: se mira bloque a bloque.
>
> **No hay preguntas abiertas.** Las seis decisiones (D1–D6) están en
> `requirements.md` §3 y las tomó el humano el 2026-09-16. Si al implementar
> aparece una duda que no resuelvan la spec, `docs/ARCHITECTURE.md` o
> `docs/CONVENTIONS.md`, se **para** y se marca `blocked`; no se improvisa.

## Reglas duras de esta feature

1. **No se toca `huella_de_veredicto` ni `_normalizar`** (`domain/models/aprobacion.py`).
   Si una tarea parece necesitarlo, se está invalidando todas las decisiones ya
   guardadas: **parar** (R13).
2. **No se toca `domain/models/validacion.py` ni ningún fichero de
   `infrastructure/persistencia/sql/`.** No hay DDL en esta feature (R20).
3. **No se toca `interface_adapters/api/estado.py`** (D5), ni
   `application/pipelines/paso_persistencia.py`, ni `services/postventa-front/`.
4. **Ningún test de `test_f028_puertas.py`, `test_f028_huella_intacta.py` ni
   `test_f026_*` cambia de aserto.** Solo pueden cambiar los **ayudantes** que
   preparan los dobles. Un aserto que haya que tocar es una puerta que se está
   aflojando: **parar**.
5. **Ninguna escritura contra Sigrid ni contra SharePoint desde local**, ni en
   tests ni a mano, y ninguna verificación contra el ERP sin autorización
   expresa del humano por incidencia. Las dos ventanas están abiertas en `dev`.
6. **Ni un dato personal en los tests**: ni DNI real, ni observaciones copiadas
   de un parte de `muestras/`. Se usan los inventados de `tests/utiles_ia.py`.

---

## Bloque 0 · La red de seguridad, en rojo, antes de tocar nada

- [x] **T1**: Crear `services/postventa-api/tests/test_f030_veredicto_persistido.py`
      con los casos que **reproducen la regresión** y hoy tienen que estar en
      **ROJO**: (a) un parte no apto aprobado por una persona, con la huella
      del veredicto **guardado**, no pasa ninguna de las tres puertas cuando el
      contexto trae el stub de `archivar.py` —es el defecto—; (b) un cuerpo que
      miente con `veredicto=apto` y `destino=archivo_y_cierre` sobre un parte
      que la validación mandó a `revision_manual` **sí** pasa las tres puertas
      —es la segunda cara, §0.9 de `requirements.md`—. Con dobles en memoria,
      sin red, sin BBDD y sin IA. | Verificación: `pytest services/postventa-api/tests/test_f030_veredicto_persistido.py`
      en **rojo**, con la traza pegada en `progress/impl_F-030.md` (fase RED).

- [x] **T2**: Añadir al mismo fichero el caso de **ida y vuelta de la huella**
      (R10), todavía en rojo: una tabla de veredictos —motivos en orden
      inverso, observaciones con saltos de línea y mayúsculas, observaciones
      `None` frente a `"   "`, `codigo_obra` con espacio final,
      `numero_incidencia` con espacios alrededor del separador, un aviso de más
      de 240 caracteres— recompuestos desde las columnas que produce
      `mapeo.valores_de_validacion` más las tres de `partes`, comprobando que
      `huella_de_veredicto` da **el mismo valor**. | Verificación: en rojo
      porque `mapeo.fila_a_validacion_y_cierre` todavía no existe; traza en el
      informe.

---

## Bloque 1 · Traer el veredicto guardado, sin un viaje más

- [ ] **T3**: Añadir `validacion: ResultadoValidacion | None = None` a
      `SituacionParte` (`domain/models/estado.py`), **el último de los cuatro
      campos**, y enmendar con nota fechada el párrafo de su docstring que
      decía que una cuarta cosa sería una invitación a decidir con ella
      (`design.md` §5.1). | Verificación: `tests/test_f030_veredicto_persistido.py`
      — `SituacionParte()` sigue siendo válida y sus tres campos de antes no
      cambian de sitio; `tests/test_f028_estado_dominio.py` en verde sin
      cambios.

- [ ] **T4**: Añadir `mapeo.fila_a_validacion_y_cierre(fila, *, hash_parte)` y
      `_avisos_desde_json`, con el orden de columnas de `design.md` §3 y los
      enumerados que **revientan** ante un valor que el dominio no conoce.
      Módulo puro: sin `psycopg` y **sin logger**. | Verificación: el caso de
      ida y vuelta de T2 pasa a **verde**; más casos propios en
      `tests/test_f005_mapeo.py` para «no hay fila de validación → `None`» y
      «un literal desconocido revienta».

- [ ] **T5**: Añadir `sentencias.select_veredicto_y_cierre(*, esquema, hash_parte)`
      con el `SQL` de `design.md` §3: anclado en `postventa.partes`, con los dos
      `JOIN` a `validaciones` y a `cierres` en `LEFT`, el esquema por
      `_tabla(...)` y el `hash` como parámetro del driver, nunca interpolado. |
      Verificación: `tests/test_f005_sentencias.py` — el texto nombra las tres
      tablas con su esquema, los dos `JOIN` son `LEFT`, el `FROM` es `partes`,
      hay exactamente un `%s` y el orden de columnas es el que lee
      `fila_a_validacion_y_cierre`.

- [ ] **T6**: Hacer que `repositorio_pg.consultar_situacion` use la sentencia
      nueva **en lugar de** `self.consultar_estado_cierre(...)` y devuelva la
      `SituacionParte` con las cuatro cosas; la línea de log gana el **destino**
      guardado y nada más. `consultar_estado_cierre` y `select_estado_cierre`
      **no se tocan**. | Verificación: `tests/test_f028_persistencia.py` —
      sigue ejecutando **dos** sentencias por llamada (R18), devuelve el
      veredicto recompuesto, devuelve `None` en veredicto y en cierre cuando no
      hay ficha de parte (R9); y `tests/test_f005_logs_sin_datos_personales.py`
      en verde más el caso nuevo de R21 (el log no nombra observaciones, ni
      código de obra, ni número de incidencia).

- [ ] **T7**: Actualizar las docstrings de contrato en
      `domain/ports/persistencia.py`: `consultar_situacion` pasa a prometer
      **cuatro** cosas, y `guardar_validacion` se enmienda con nota fechada
      —hoy sigue diciendo que revoca la aprobación (lo retiró F-028 T15) y
      sostiene la premisa «los tres pasos del circuito … **no puede**
      recomputar la huella», que es la descripción literal del defecto
      (`design.md` §5.1)—. | Verificación: `tests/test_f028_documentacion.py` /
      `test_f030_*` — el puerto no gana ningún método nuevo y el texto ya no
      afirma la revocación ni la premisa retirada.

---

## Bloque 2 · La puerta juzga el veredicto guardado

- [ ] **T8**: Cambiar `application/pipelines/puerta_de_estado.py` para que lea
      `ctx.situacion.validacion` y **no vuelva a mirar `ctx.validacion`**:
      consulta primero, «no hay veredicto» después, y el destino del mensaje
      sale del veredicto guardado (`design.md` §5.3). Actualizar la cabecera del
      módulo con lo que pasó y por qué. | Verificación: los casos (a) de T1
      pasan a **verde**; `tests/test_f030_veredicto_persistido.py` añade el
      caso decisivo de R1 —contexto con un stub **apto** y almacén con un
      veredicto a `revision_manual` → **no pasa**—, y el de R17 con los tres
      mensajes y el destino guardado dentro.

- [ ] **T9**: Adaptar **los ayudantes** de `tests/test_f028_puertas.py` para
      que el veredicto se prepare en la situación en vez de en el contexto
      (`design.md` §5.5). **Ni un aserto cambia.** | Verificación:
      `pytest services/postventa-api/tests/test_f028_puertas.py` — los 48 casos
      en verde, y el diff del fichero toca solo los dos ayudantes. Si hay que
      tocar un aserto: **parar** (regla dura 4).

---

## Bloque 3 · Los tres endpoints dejan de fabricar el veredicto

- [ ] **T10**: Quitar el `ResultadoValidacion` de pega de
      `interface_adapters/api/archivar.py`, `adjuntar.py` y `cerrar.py`:
      `_como_contexto` devuelve el contexto con `validacion=None`, se retiran
      los imports huérfanos y se sustituye el párrafo «El veredicto llega en el
      cuerpo, y se vuelve a comprobar» por lo que pasa ahora. `veredicto` y
      `destino` **siguen siendo obligatorios y siguen validándose** contra las
      enumeraciones (R19, D6). | Verificación: los casos (b) de T1 —el cuerpo
      que miente— pasan a **verde** (o sea, dejan de pasar la puerta);
      `test_f006_archivar_http.py`, `test_f012_adjuntar_http.py` y
      `test_f009_cerrar_http.py` siguen devolviendo **400** ante un `veredicto`
      o un `destino` desconocidos.

- [ ] **T11**: Arreglar los tests de endpoint que pasaban la puerta gracias al
      cuerpo, preparando el veredicto en el doble de repositorio
      (`design.md` §5.5, §10.5). **No se relaja ninguna puerta para poner un
      test en verde**: si aparece la tentación, **parar**. | Verificación:
      `pytest services/postventa-api/tests` en verde, y el informe lista uno a
      uno los tests cambiados con el motivo.

- [ ] **T12**: Añadir el **centinela estructural** (R3): un test que recorre con
      `ast` los módulos de `interface_adapters/api/` y falla si alguno construye
      un `ResultadoValidacion` (`design.md` §7.3). | Verificación: el test en
      verde, y en **rojo** si se le devuelve a `archivar.py` el stub (traza de
      la comprobación pegada en el informe).

---

## Bloque 4 · El test que faltó

- [ ] **T13**: Añadir a `tests/utiles_pg.py` el doble `RepositorioComoLaBase`,
      que **guarda columnas y no objetos** y reconstruye el veredicto con la
      misma `mapeo.fila_a_validacion_y_cierre` de producción
      (`design.md` §7.1). `RepositorioEnMemoria` **no se toca**. | Verificación:
      un caso propio que guarda un veredicto con observaciones manuscritas y
      comprueba que lo que devuelve `consultar_situacion` **no es el mismo
      objeto** y sí tiene **la misma huella**.

- [ ] **T14**: Crear `tests/test_f030_circuito_borde_a_borde.py` con el
      recorrido `cambiar_estado_http` → `archivar_parte` usando **los cuerpos
      reales de los dos endpoints** sobre un parte **no apto con observaciones**
      —el caso de RS26.09/0178— contra `RepositorioComoLaBase` y un doble de
      `ArchivoPort`; más su **control negativo** sin el paso de aprobación
      (`design.md` §7.2). Sin red, sin BBDD, sin IA. | Verificación: R4 y R23 —
      el parte se archiva; sin aprobar, `ParteNoApto`. Y la comprobación de que
      el test **caza el defecto**: devolviendo el stub a `archivar.py` se pone
      rojo (traza en el informe).

- [ ] **T15**: Añadir al mismo fichero los equivalentes de `adjuntar_grafico` y
      de `cerrar_incidencia` en dry-run (`commit=False`), con sus dobles y sus
      control-negativo (R5, R6, R24). | Verificación: los dos casos en verde y
      los dos control-negativo levantando `ParteNoApto` en la puerta del estado,
      antes de cualquier otra comprobación.

---

## Bloque 5 · Cierre: rigor, documentación y verde

- [ ] **T16**: Añadir el caso de **compatibilidad hacia atrás** (R11, R12, §8):
      una decisión guardada con la huella del veredicto que hay en la base
      sigue aprobando el parte **sin volver a decidir**; y si el veredicto
      guardado cambia después, deja de contar y el parte vuelve a `pendiente`.
      | Verificación: los dos casos en verde en
      `tests/test_f030_veredicto_persistido.py`.

- [ ] **T17**: Añadir el control de que **no hay DDL** en la feature (R20): el
      diff de la rama no toca `infrastructure/persistencia/sql/`. |
      Verificación: el test, más `git diff --name-only dev...HEAD` pegado en el
      informe.

- [ ] **T18**: Pasar la puerta de **cobertura** sobre las líneas cambiadas
      (≥ 80 %) y la **campaña de mutación** con **cero supervivientes**: cada
      superviviente exige un test nuevo o una justificación escrita. Mutar a
      mano, como mínimo, los tres que reabren el defecto: la puerta leyendo
      `ctx.validacion`, la recomposición perdiendo las observaciones y la
      recomposición perdiendo el número de incidencia. | Verificación:
      `python -m harness.mutacion` y la sección de análisis en
      `progress/impl_F-030.md`.

- [ ] **T19**: Actualizar `docs/ARCHITECTURE.md` con la precisión del
      2026-09-16 en «Semántica de dominio imprescindible» punto 3: **lo que
      decide si un parte entra en el circuito es el estado derivado del
      veredicto guardado**, y ningún endpoint del circuito emite veredicto.
      Anotar en `progress/current.md` el riesgo abierto de §10.7 —el nombrado
      de `/api/archivar` sigue saliendo del cuerpo— para que el humano decida
      si se da de alta como feature. | Verificación: `tests/test_f028_documentacion.py`
      y los controles de documentación en verde; la nota, en `progress/`.

- [ ] **T20**: Ejecutar `bash harness/init.sh` en verde (incluye toda la suite)
      y dejar `progress/impl_F-030.md` con las trazas de la fase RED, los tests
      cambiados uno a uno, las evidencias de cobertura y mutación, y las dos
      verificaciones manuales pendientes. | Verificación: `bash harness/init.sh`
      con exit code 0.

---

## Verificaciones MANUAL (humano)

No son condición de cierre de la feature —exigen base de datos real o el
entorno desplegado— y van anotadas en `progress/current.md`.

- [ ] **V1 · el parte que está esperando.** Con F-030 desplegado en `dev`,
      archivar el parte `b7e9b037` de la incidencia **RS26.09/0178** y comprobar
      que se archiva **sin volver a decidir nada**. Es la prueba de que §8 es
      cierta contra datos reales. **Escribe en SharePoint: requiere
      autorización expresa del humano para esa incidencia, y no se hace desde
      local.**
- [ ] **V2 · el coste, medido.** Contar las consultas de una tanda real de 22
      partes contra el PostgreSQL compartido y comprobar que **no ha subido**
      respecto a F-028 (R18). Continúa la verificación que dejó abierta
      F-028 §11.1.
