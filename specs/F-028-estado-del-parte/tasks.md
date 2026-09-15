<!-- specs/F-028-estado-del-parte/tasks.md -->
# F-028 · Estado del parte, con histórico y transición manual — Tareas

> Una tarea = un commit `F-028 Tn: ...`. Ordenadas por dependencia; los tests
> van **antes o junto** a la implementación (**fase RED obligatoria**, rigor
> `estandar`).
>
> La rama es `feature/F-028-estado-del-parte`, creada desde `dev`.
>
> **Los encargos al implementer se dan de uno en uno, por bloques.** Los
> bloques son pequeños a propósito: los bloques 4 y 5 retiran código de F-026,
> que se cerró ayer, y quiero poder mirarlos por separado.
>
> **No hay preguntas abiertas**: las nueve decisiones (D1–D9) están en
> `requirements.md` y las tomó el humano el 2026-09-15. Si al implementar
> aparece una duda que no resuelvan la spec ni `docs/ARCHITECTURE.md`, se
> **para** y se marca `blocked`; no se improvisa.
>
> **Regla dura 1**: ninguna tarea toca `domain/models/validacion.py` ni
> `sql/04_validaciones.sql`. Si una tarea parece necesitarlo, se está
> reescribiendo el veredicto: **parar** (R8).
>
> **Regla dura 2**: ninguna tarea toca `huella_de_veredicto` ni `_normalizar`
> (D9), ni `infrastructure/sigrid/`, ni `infrastructure/sharepoint/`.
>
> **Regla dura 3**: ninguna tarea reescribe ni borra `sql/10_aprobaciones.sql`
> ni la tabla `postventa.aprobaciones`. Se congela y se siembra
> (`design.md` §4).

---

## Bloque 0 · La red de seguridad, antes de tocar nada

- [x] **T1**: Crear `services/postventa-api/tests/test_f028_puertas.py` con los
      **control-negativo** que tienen que seguir en verde al final del trabajo:
      un parte no apto **sin decisión humana** no llega a archivar, ni a
      adjuntar, ni a cerrar; ninguno de los tres pasos lee la decisión del
      cuerpo; y un parte **sin veredicto** sigue teniendo su error propio. Con
      dobles en memoria, sin red y sin BBDD. | Verificación: los casos en verde
      **antes** de tocar nada (`pytest services/postventa-api/tests/test_f028_puertas.py`).
      Son R33 y R34, y son lo que detecta cualquier puerta aflojada en los
      bloques 4 y 5.

---

## Bloque 1 · El dominio del estado

- [x] **T2**: Crear `domain/models/estado.py` con `EstadoParte` (los cuatro),
      `DecisionEstado`, `SituacionParte`, `ESTADOS_DE_CIERRE_EN_FIRME` y
      `LIMITE_MOTIVO`. **Dominio puro.** | Verificación:
      `tests/test_f028_estado_dominio.py` — el enumerado tiene cuatro valores y
      no más, y los dos literales de cierre se comparan contra el `CHECK` de
      `sql/06_cierres.sql`. **Fase RED**: traza del fallo antes de que exista el
      módulo.

- [x] **T3**: Añadir `estado_de_la_maquina(validacion)` y
      `estado_del_parte(validacion, decision_humana, estado_cierre)` con el
      orden de `design.md` §3. | Verificación: mismo fichero — apto nace
      `aprobado` (R3); no apto nace `pendiente` (R4); sin veredicto,
      `pendiente`; el cierre gana a una decisión humana (R18); `rechazado`
      humano manda sobre un veredicto apto (R5); `aprobado` humano con huella
      distinta **no** cuenta y se cae a la máquina (R19); con la misma huella
      **sí** (R20); y el `rechazado` **no caduca** nunca.

- [x] **T4**: Añadir `ParteCerrado` y `CambioDeEstadoInvalido` a
      `domain/models/errores.py`. | Verificación: test de que heredan de donde
      heredan sus hermanos; la traducción a 409 y 400 se cierra en T13.

---

## Bloque 2 · La persistencia

- [x] **T5**: Crear `sql/11_historico_estado.sql` con la tabla append-only, su
      índice y la **semilla** de `design.md` §8.4, con su cabecera. |
      Verificación: `tests/test_f028_ddl_historico.py` — texto idempotente,
      todo cualificado con `postventa.`, ni una sentencia de ámbito de
      servidor, `CHECK` de los dos campos de estado comparado con el `Enum` del
      dominio, la semilla con `NOT EXISTS`, ninguna columna binaria, y
      `sql/10_aprobaciones.sql` **sin cambios** (regla dura 3).

- [x] **T6**: `sentencias.py`: `insert_decision_estado`,
      `select_situacion_estado` (el `UNION ALL` de las dos últimas filas) y
      `select_estado_cierre`; `mapeo.fila_a_decision_estado`. | Verificación:
      `tests/test_f028_persistencia.py` con dobles — el `INSERT` no lleva
      ningún `ON CONFLICT` (R21), la consulta ordena por
      `decidido_at_utc DESC, cambio_id DESC`, y la fila humana se distingue de
      la de máquina por `decidido_por IS NOT NULL`.

- [ ] **T7**: `domain/ports/persistencia.py` y `repositorio_pg.py`:
      `consultar_situacion`, `registrar_decision` y `consultar_estado_cierre`.
      **Todavía no se retira nada de F-026.** | Verificación: mismo fichero de
      test — una situación sin ninguna fila devuelve los tres huecos vacíos, y
      el log de la operación no lleva ni el motivo ni el `oid` (R52).

---

## Bloque 3 · La constancia: que el histórico cuente la película

- [ ] **T8**: `paso_persistencia`: tras guardar la validación, calcular el
      estado derivado y **añadir la fila de constancia solo si difiere del
      último estado registrado** (`design.md` §4). | Verificación:
      `tests/test_f028_persistencia.py` — el primer guardado de un parte apto
      deja una fila `→ aprobado` con `decidido_por` a `NULL` (R23, R24); el de
      un no apto, `→ pendiente` (R4); **un reproceso que no cambia nada no
      escribe ninguna fila**; y teclear el código que faltaba deja
      `pendiente → aprobado`.

- [ ] **T9**: `paso_cierre`: tras la escritura del cierre, la fila `→ cerrado`.
      | Verificación: mismo fichero — la fila se escribe **después** de que el
      cierre conste, y un cierre fallido **no** la escribe.

---

## Bloque 4 · Las tres puertas

- [ ] **T10**: `contexto_parte.py`: `aprobacion` → `situacion`, con la
      docstring que diga que viene del repositorio y **nunca del cuerpo**. |
      Verificación: la suite existente sigue en verde salvo lo que T11 sustituye.

- [ ] **T11**: `paso_archivo`, `paso_grafico` y `paso_cierre`: `_exigir_admitido`
      pasa a exigir `EstadoParte.APROBADO` y **se retira el atajo del apto**
      (`design.md` §6). | Verificación: `tests/test_f028_puertas.py` ampliado —
      los cuatro estados contra los tres pasos: `aprobado` pasa, `pendiente` no,
      **`rechazado` no aunque el veredicto sea apto** (R5, el caso que hoy es
      imposible), `cerrado` no llega a escribir dos veces. Y T1 sigue en verde.

---

## Bloque 5 · El borde HTTP

- [ ] **T12**: Crear `interface_adapters/api/estado_serializado.py` con el
      bloque `estado` de las respuestas. | Verificación: test de que trae
      `estado`, `decidido_por_persona`, `decidido_at_utc` y `estado_anterior`,
      y **ni el `oid`, ni el correo, ni el nombre, ni el motivo** (R42, R52).

- [ ] **T13**: Crear `interface_adapters/api/estado.py` (`POST /api/estado`) y
      su ruta en `function_app.py`. | Verificación:
      `tests/test_f028_estado_http.py` — 200 al cambiar; 200 `sin_cambios` al
      repetir la misma decisión; 400 sin `usuario_oid`, sin `confirmado: true`,
      con `confirmado` como cadena `"true"`, con un `estado` que no sea uno de
      los dos manuales, **con rechazo sin motivo** (R11) y con motivo
      demasiado largo; 409 si el parte está `cerrado` (R7) y si la remesa no
      consta; 503 sin base. **Y en los rechazos, ni una escritura.**

- [ ] **T14**: `parte.py`: la respuesta cambia el bloque `aprobacion` por
      `estado` (`design.md` §5). | Verificación: test de que subir la remesa
      otra vez devuelve el estado de cada parte **sin una petición más por
      parte**.

- [ ] **T15**: Retirar `interface_adapters/api/aprobar.py`,
      `aprobacion_serializada.py`, la ruta `aprobar`, `upsert_aprobacion`,
      `select_aprobacion`, `revocar_aprobacion_si_cambio`, `fila_a_aprobacion`,
      `guardar_aprobacion`, `consultar_aprobacion`, y de
      `domain/models/aprobacion.py` todo salvo `huella_de_veredicto` y
      `_normalizar`. **La tabla no se toca** (regla dura 3). | Verificación: la
      suite entera en verde; los tests de F-026 que probaban lo retirado se
      sustituyen por los de F-028 y **los de la huella se conservan intactos**;
      y un test comprueba que `postventa.aprobaciones` sigue declarada en el
      DDL y que nadie escribe en ella.

---

## Bloque 6 · El front

- [ ] **T16**: `js/api.js::cambiarEstado` y
      `js/pipeline.js::cuerpoDeCambioDeEstado`; retirar `aprobar`. |
      Verificación: `tests_js/estado.test.js` — el cuerpo lleva `estado`,
      `usuario_oid`, `confirmado: true` y el motivo recortado; **se niega a
      componer un rechazo sin motivo** (R11) y sin `usuario_oid`; no lleva
      ningún byte del PDF (R30).

- [ ] **T17**: `js/pipeline.js`: `semaforoDe(validacion, estado)` con las
      cuatro marcas y `pendientesDeCircuito` filtrando por `estado ===
      "aprobado"`. | Verificación: mismo fichero — un parte `rechazado` sale de
      la tanda aunque su veredicto sea apto; un `cerrado` también; y el
      `aprobado` por persona se distingue del de máquina (R39).

- [ ] **T18**: `js/app.js` e `index.html`: los dos botones en el detalle, el
      campo de motivo obligatorio al rechazar, las cuatro marcas en lista y
      detalle, los textos de R43 y la frase del parte `cerrado` (R41). |
      Verificación: `services/postventa-front/tests/test_f028_front.py` — los
      dos botones existen, el de rechazar está deshabilitado sin motivo, la
      frase del cerrado está, y **no aparece ningún `oid`** en la plantilla.

---

## Bloque 7 · Los espacios de los códigos (asunto 2)

- [ ] **T19**: Escribir **primero** el test que reproduce el defecto:
      `tests/test_f028_espacios_codigos.py` con la tabla de `design.md` §9.3,
      fila a fila, para `a_codigo_de_sigrid` y para `nombre_de_archivo` (R44 a
      R46). | Verificación: **fase RED** — falla en las tres filas rotas antes
      de tocar el dominio, y la traza del fallo va en el informe.

- [ ] **T20**: Arreglar `normalizar_codigo` y añadir `tramos_de_codigo` y
      `SEPARADORES_DE_CODIGO`; `nombre_de_archivo` compone por tramos (R44,
      R46, R48, R49). | Verificación: T19 en verde y **toda**
      `tests/test_f006_nombrado.py` en verde salvo el único test de T21.

- [ ] **T21**: Actualizar
      `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` a la expectativa
      nueva, con su comentario, y escribir el recuadro fechado de R8 en
      `specs/F-006-sharepoint/requirements.md` (R55). | Verificación: el test en
      verde y el recuadro presente; el informe del implementer dice
      explícitamente **qué test cambió de expectativa y por qué**.

- [ ] **T22**: `a_codigo_de_sigrid` compone por tramos (R45, R47), **sin tocar
      nada más de `cierre.py`**. | Verificación: T19 entero en verde, los dos
      tests de F-009 sobre la conversión en verde **sin tocarlos**, y control
      negativo de que `TEXTO_LOG_CIERRE`, `batch_de_cierre` e
      `infrastructure/sigrid/escrituras.py` **no aparecen en el diff**.

---

## Bloque 8 · Que la huella no se ha movido

- [ ] **T23**: `tests/test_f028_huella_intacta.py` con los tres controles
      negativos de `design.md` §10: huellas esperadas **escritas literales**,
      el módulo de la huella no importa `nombrado`, y un parte aprobado por una
      persona sigue `aprobado` después del arreglo (R50, R51). | Verificación:
      los tres en verde **con el bloque 7 ya aplicado**. Si alguno falla,
      **parar**: el cambio estaría invalidando decisiones humanas, que es
      exactamente lo que la ficha prohíbe.

---

## Bloque 9 · Documentación y enmiendas

- [ ] **T24**: Los recuadros fechados: R56 y R57 en
      `specs/F-026-aprobacion-humana/requirements.md`, y R58 en
      `specs/F-025-confirmacion-unica/requirements.md` y en
      `docs/ARCHITECTURE.md` —incluida la nota de la semántica 5 sobre que los
      espacios alrededor del separador no forman parte del código—. |
      Verificación: test de documentación con el patrón de
      `tests/test_f026_documentacion.py`; **ningún texto original borrado**.

- [ ] **T25**: `docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md`
      (R59): endpoint nuevo, endpoint retirado, tabla nueva, tabla congelada y
      qué deja de escribirse. **Dos repositorios, dos commits, sin `push`.** |
      Verificación: `git -C ../azure-apps status` limpio al terminar y los
      endpoints recontados en los dos documentos.

---

## Bloque 10 · Cierre

- [ ] **T26**: Campaña de mutación sobre lo cambiado
      (`python -m harness.mutacion`; rigor `estandar`: los supervivientes se
      documentan y los juzga el reviewer). | Verificación: informe en
      `progress/impl_F-028.md` con el número de mutantes, los supervivientes y
      qué se hace con cada uno.

- [ ] **T27**: Verificaciones que necesitan la base real y el ERP, y que
      **ejecuta el humano** tras desplegar:
      1. el DDL nuevo aplicado dos veces seguidas no falla, y **la semilla no
         duplica** ninguna fila;
      2. la aprobación que ya había en `postventa.aprobaciones` aparece
         sembrada y el parte sigue saliendo `aprobado`;
      3. aprobar → rechazar → aprobar deja **tres** filas en el histórico, en
         orden, y ninguna pisada;
      4. un parte **apto** rechazado a mano **no se archiva**;
      5. un parte cerrado responde 409 al intentar cambiarle el estado, y la
         web lo explica;
      6. un parte cuyo número se lea con espacios alrededor de la barra
         **cierra la incidencia**, que es el defecto que abrió el asunto 2.
      | Verificación: `MANUAL (humano)`. Consulta exacta, **solo lectura**:
      `SELECT estado_anterior, estado, decidido_por IS NOT NULL AS por_persona,
      decidido_at_utc, motivo FROM postventa.historico_estado
      WHERE hash_parte = %s ORDER BY decidido_at_utc, cambio_id;`

- [ ] **T28**: Ejecutar `bash harness/init.sh` en verde.
