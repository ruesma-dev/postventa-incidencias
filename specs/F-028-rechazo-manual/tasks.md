<!-- specs/F-028-rechazo-manual/tasks.md -->
# F-028 · Rechazar un parte aprobado a mano, y quitar los espacios de los códigos — Tareas

> Una tarea = un commit `F-028 Tn: ...`. Ordenadas por dependencia; los tests
> van **antes o junto** a la implementación (**fase RED obligatoria**, rigor
> `estandar`).
>
> La rama es `feature/F-028-rechazo-manual`, creada desde `dev`.
>
> **Los encargos al implementer se dan de uno en uno, por bloques.** Los
> bloques son pequeños a propósito: el bloque 7 es el único que toca tests de
> features cerradas, y quiero poder mirarlo solo.
>
> **Bloquean el arranque del asunto 1**: **P1** (qué pasa con un parte
> cerrado), **P2** (la nota) y **P4** (la bitácora). Las tres cambian el
> diseño. **P3** no bloquea: es una guardia de una línea que se añade o no al
> final. **P5** no bloquea el asunto 2: la propuesta es no tocar la huella, y
> los bloques 6 y 7 la dejan intacta pase lo que pase.
>
> **Regla dura 1**: ninguna tarea toca `domain/models/validacion.py`,
> `sql/04_validaciones.sql` ni `MOTIVOS_APROBABLES`. Si una tarea parece
> necesitarlo, se está reescribiendo el veredicto o ensanchando la puerta de
> F-026: hay que **parar**.
>
> **Regla dura 2**: ninguna tarea toca `huella_de_veredicto` ni `_normalizar`
> de `aprobacion.py` (P5), ni `infrastructure/sigrid/`, ni
> `infrastructure/sharepoint/`.
>
> **Regla dura 3**: ninguna tarea reescribe `sql/10_aprobaciones.sql`. El DDL
> de este proyecto es **acumulativo**, no reescrito (`design.md` §8.4).

---

## Bloque 0 · Fijar lo que hoy es imposible, antes de hacerlo posible

- [ ] **T1**: Crear `services/postventa-api/tests/test_f028_puertas.py` con los
      **control-negativo** que tienen que seguir en verde al final: un parte
      con la aprobación **retirada** no llega a archivar, ni a adjuntar, ni a
      cerrar; y ninguno de los tres pasos lee la aprobación del cuerpo. Con
      dobles en memoria, sin red y sin BBDD. | Verificación: los cuatro casos
      en verde **antes** de tocar nada, con
      `pytest services/postventa-api/tests/test_f028_puertas.py`. Son R23 y
      R24, y son la red que impide que los bloques 2 y 3 aflojen una puerta sin
      que se note.

---

## Bloque 1 · El dominio del rechazo

- [ ] **T2**: Añadir a `domain/models/aprobacion.py` el motivo
      `MotivoRevocacion.RETIRADA_HUMANA`, `LIMITE_NOTA_REVOCACION` y los dos
      campos nuevos de `Aprobacion` (`revocada_por`, `revocada_nota`, los dos
      `None` por omisión). **Dominio puro.** | Verificación:
      `tests/test_f028_rechazo_dominio.py` — el enumerado tiene dos valores y
      no más, una `Aprobacion` sin revocar sigue siendo vigente, y una revocada
      a mano no lo es. **Fase RED**: traza del fallo antes de escribir el
      código.

- [ ] **T3**: Añadir `ESTADOS_DE_CIERRE_EN_FIRME` y
      `puede_retirarse(aprobacion, estado_cierre)` al mismo módulo (R7, R9). |
      Verificación: mismo fichero — retirable con aprobación vigente y sin
      cierre; retirable con cierre en `pendiente`, `dry_run_ok` o `error`; **no
      retirable** con `cerrado` ni con `ya_cerrada`; **no retirable** sin
      aprobación ni con una ya revocada. Más el test que compara los dos
      literales contra el `CHECK` de `sql/06_cierres.sql`.

- [ ] **T4**: Añadir `ParteNoRechazable` a `domain/models/errores.py` (→ 409).
      | Verificación: test de que hereda de donde heredan sus hermanos y de que
      `function_app.py` lo traduce a 409 (se cierra en T9).

---

## Bloque 2 · La persistencia del rechazo

- [ ] **T5**: Crear `sql/12_aprobaciones_revocada_por.sql` con los dos
      `ALTER TABLE … ADD COLUMN IF NOT EXISTS` (R12, R16) y su cabecera
      explicando por qué es un fichero aparte. | Verificación:
      `tests/test_f028_ddl_rechazo.py` — texto idempotente, todo cualificado
      con `postventa.`, ni una sentencia de ámbito de servidor, y
      `sql/10_aprobaciones.sql` **sin cambios** (regla dura 3).

- [ ] **T6**: Crear `sql/11_decisiones_aprobacion.sql` con la bitácora
      append-only y su índice (R15). | Verificación: mismo fichero de test —
      idempotencia, esquema propio, `CHECK` de `decision` comparado con el
      enumerado del dominio, `autor_oid` admite `NULL` y ninguna columna
      binaria.

- [ ] **T7**: `sentencias.py`: `retirar_aprobacion`, `select_estado_cierre` e
      `insert_decision_aprobacion`; ampliar `_COLUMNAS_REVOCACION` y
      `_COLUMNAS_APROBACION`; `upsert_aprobacion` limpia también las dos
      columnas nuevas al volver a aprobar (R25). Y `mapeo.fila_a_aprobacion`
      desempaqueta dos columnas más. | Verificación:
      `tests/test_f028_persistencia.py` con dobles — el `UPDATE` de la retirada
      lleva `revocada_at_utc IS NULL` en el `WHERE` (R8: no reescribe una
      revocación ya hecha), la fila de bitácora lleva autor y motivo, y volver
      a aprobar deja las cuatro columnas de revocación a `NULL`.

- [ ] **T8**: `domain/ports/persistencia.py` y `repositorio_pg.py`:
      `retirar_aprobacion`, `consultar_estado_cierre` y `registrar_decision`;
      y `guardar_validacion` escribe además la fila
      `revocada_automatica` **condicionada a que haya algo que revocar**
      (`design.md` §5). | Verificación: mismo fichero de test — un reproceso
      que **no** revoca no escribe ninguna fila de bitácora; uno que revoca,
      una y solo una. Sin BBDD: se comprueban las sentencias emitidas.

---

## Bloque 3 · El borde HTTP

- [ ] **T9**: Crear `interface_adapters/api/rechazar.py` y la ruta en
      `function_app.py` (R18–R22). | Verificación:
      `tests/test_f028_rechazar_http.py` — 200 al retirar; 200 `sin_cambios` al
      repetir; 400 sin `usuario_oid`, sin `confirmado: true`, con `confirmado`
      como cadena `"true"`, y con nota de más de 500 caracteres; 409 si no
      consta aprobado y 409 si consta cerrado; 503 sin base. **Y en los tres
      rechazos, ni una escritura** (el doble lo registra).

- [ ] **T10**: Ampliar `aprobacion_serializada.py` con `revocada_at_utc` y
      `revocada_motivo`, y hacer que `aprobar.py` escriba su fila de bitácora
      (`aprobada`). | Verificación: test de que el bloque **no** trae el `oid`,
      **no** trae la nota y sí distingue los dos motivos (R22, R28, R30); y
      que `/api/aprobar` deja su fila.

- [ ] **T11**: Control negativo del log (R39, R40). | Verificación: test que
      captura el log del endpoint y comprueba que lleva `hash_parte` y
      resultado, y que **no** aparecen la nota, el `oid`, el DNI ni las
      observaciones.

---

## Bloque 4 · El front

- [ ] **T12**: `js/api.js::rechazar` y `js/pipeline.js::cuerpoDeRechazo`. |
      Verificación: `tests_js/rechazo.test.js` — el cuerpo lleva `hash_parte`,
      `usuario_oid`, `confirmado: true` y la nota recortada; **no** lleva ni
      extracción, ni firma, ni PDF (R19); y se niega a componerlo sin
      `usuario_oid`.

- [ ] **T13**: `js/app.js::rechazarParte()` y los ayudantes de texto
      (`estaRetirada`, `motivoDeRevocacion`). | Verificación: mismo fichero —
      tras la retirada, `semaforoDe(validacion, aprobacion)` devuelve el color
      de antes **sin tocar `aprobacionVale`** (R23, R27), y el parte sale del
      selector de la tanda.

- [ ] **T14**: `index.html`: el botón, el campo de nota con su aviso, y los dos
      textos de R27 y R30; el botón no se pinta si el parte consta cerrado
      (R29). | Verificación: `services/postventa-front/tests/test_f028_front.py`
      — el botón existe y cuelga de `estaAprobado`, el aviso del campo de nota
      está, los dos textos están, y **no aparece ningún `oid`** en la plantilla.

---

## Bloque 5 · Documentación del asunto 1

- [ ] **T15**: Enmiendas fechadas: R34 de F-026 precisado (R43) y la nota de
      `docs/ARCHITECTURE.md` sobre que una aprobación puede retirarla una
      persona (R45, primera mitad). | Verificación: test de documentación con
      el patrón de `tests/test_f026_documentacion.py`.

- [ ] **T16**: `docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md`
      (R44): endpoint nuevo, dos columnas nuevas, tabla nueva. **Dos
      repositorios, dos commits, sin `push`.** | Verificación:
      `git -C ../azure-apps status` limpio al terminar y el endpoint contado en
      la tabla de endpoints de los dos documentos.

---

## Bloque 6 · Los espacios de los códigos (asunto 2)

- [ ] **T17**: Escribir **primero** el test que reproduce el defecto:
      `tests/test_f028_espacios_codigos.py` con la tabla de equivalencias de
      `design.md` §9.3, fila a fila, para `a_codigo_de_sigrid` y para
      `nombre_de_archivo` (R31–R33). | Verificación: **fase RED** — el fichero
      falla en las tres filas rotas antes de tocar el dominio, y la traza del
      fallo va en el informe.

- [ ] **T18**: Arreglar `normalizar_codigo` y añadir `tramos_de_codigo` y
      `SEPARADORES_DE_CODIGO` en `domain/models/nombrado.py`; pasar
      `nombre_de_archivo` a componer por tramos (R31, R33, R35, R36). |
      Verificación: T17 en verde, y **toda** `tests/test_f006_nombrado.py` en
      verde salvo el único test declarado en T19.

- [ ] **T19**: Actualizar `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`
      a la expectativa nueva, con su comentario citando la enmienda, y escribir
      el recuadro fechado de R8 en `specs/F-006-sharepoint/requirements.md`
      (R42). | Verificación: el test en verde con la expectativa nueva y el
      recuadro presente; el informe del implementer dice explícitamente **qué
      test cambió de expectativa y por qué**.

- [ ] **T20**: Pasar `a_codigo_de_sigrid` a componer por tramos en
      `domain/models/cierre.py` (R32, R34), **sin tocar nada más de ese
      módulo**. | Verificación: T17 en verde entero, los dos tests de F-009
      sobre la conversión en verde sin tocarlos, y control negativo de que
      `TEXTO_LOG_CIERRE`, `batch_de_cierre` e
      `infrastructure/sigrid/escrituras.py` **no aparecen en el diff**.

- [ ] **T21**: La nota de `docs/ARCHITECTURE.md` en la semántica 5: los
      espacios alrededor del separador no forman parte del código (R45, segunda
      mitad). | Verificación: test de documentación.

---

## Bloque 7 · Que la huella de F-026 no se ha movido

- [ ] **T22**: `tests/test_f028_huella_intacta.py` con los tres controles
      negativos de `design.md` §10: las huellas esperadas **escritas literales**
      en el test, que `aprobacion.py` no importa `nombrado`, y que el
      comportamiento de revocación ante dos escrituras del mismo código no
      cambia (R37, R38). | Verificación: los tres en verde **con el arreglo del
      bloque 6 ya aplicado**. Si alguno falla, **parar**: el cambio estaría
      revocando aprobaciones y eso es exactamente lo que la ficha prohíbe.

---

## Bloque 8 · Cierre

- [ ] **T23**: Campaña de mutación sobre lo cambiado
      (`python -m harness.mutacion`, rigor `estandar`: los supervivientes se
      documentan y los juzga el reviewer). | Verificación: informe en
      `progress/impl_F-028.md` con el número de mutantes, los supervivientes y
      qué se hace con cada uno.

- [ ] **T24**: Verificaciones que necesitan la base real y el ERP, y que
      **ejecuta el humano** tras desplegar:
      1. el DDL nuevo aplicado dos veces seguidas no falla ni duplica;
      2. aprobar → rechazar → aprobar deja **una** fila en
         `postventa.aprobaciones` y **tres** en
         `postventa.decisiones_aprobacion`, en orden;
      3. un parte ya cerrado responde 409 al intentar rechazarlo;
      4. un parte cuyo número se lea con espacios alrededor de la barra
         **cierra la incidencia**, que es el defecto que abrió la feature.
      | Verificación: `MANUAL (humano)`. Consulta exacta, **solo lectura**:
      `SELECT decision, autor_oid IS NOT NULL AS con_autor, decidida_at_utc, motivo
      FROM postventa.decisiones_aprobacion WHERE hash_parte = %s ORDER BY decidida_at_utc;`

- [ ] **T25**: Ejecutar `bash harness/init.sh` en verde.
