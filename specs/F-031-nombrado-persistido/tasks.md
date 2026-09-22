<!-- specs/F-031-nombrado-persistido/tasks.md -->
# F-031 · Tareas

> Rama: `feature/F-031-nombrado-persistido` (creada desde `dev`, commit
> `7b013ff`). Un commit por tarea: `F-031 Tn: …`. Rigor **`critico`**, así que
> fase RED, cobertura, mutación sin supervivientes sin justificar y las
> verificaciones `MANUAL (humano)` con su resultado real.
>
> Todos los tests corren **sin red, sin BBDD y sin IA**. Los dos únicos puntos
> que necesitan una persona delante son T14 y T15.
>
> Encargo por bloques: **B1** (T1), **B2** (T2–T7, backend), **B3** (T8–T10,
> front), **B4** (T11–T13, cierre), **B5** (T14–T16, manual y verde).

## Bloque 1 · Parada obligatoria

- [x] **T1**: Enseñar al humano las decisiones abiertas de `design.md` §11 y
      esperar respuesta. **Bloquean el arranque D-1** (de dónde se leen los
      códigos), **D-3** (409 ante divergencia) y **D-5** (qué hace el front);
      las demás se pueden cerrar con la recomendación.
      **Verificación**: la respuesta del humano queda transcrita, literal y
      fechada, en `progress/current.md`. Sin ella, **no se toca código**.
      **CUMPLIDA el 2026-09-22**: el humano aprobó la spec («si») con las
      recomendaciones de D-1 a D-7, y H-1 se recoge ampliando la ficha de
      F-034. La transcripción, fechada, está en el bloque de F-031 de
      `progress/current.md` (commit `35ad69d`).

## Bloque 2 · Backend

- [x] **T2**: `domain/models/nombrado.py` · añadir `es_el_mismo_codigo(uno,
      otro)` (dominio puro, apoyada en `normalizar_codigo`) y exportarla en
      `__all__`. Nada más de ese módulo se toca.
      **Verificación**: `pytest tests/test_f031_nombrado_persistido.py -k r4`
      en verde — incluidos los casos de F-032 (`RS 26.09/0178` ≡
      `RS26.09/0178`, `06 26` ≡ `0626`, `RS26.09 – 0178` ≡ `RS26.09-0178`) y
      los dos vacíos ≡ vacío.

- [x] **T3**: `domain/models/errores.py` · añadir `CodigosNoCoinciden` con
      `.motivo`, con su docstring diciendo en qué se diferencia de `ParteNoApto`
      y de `NombradoImposible` (`design.md` §3.2).
      **Verificación**: `pytest tests/test_f031_cotejo_de_codigos.py -k errores`
      en verde.

- [x] **T4 (RED)**: escribir `tests/test_f031_nombrado_persistido.py` y
      `tests/test_f031_cotejo_de_codigos.py` **antes** de tocar el paso, con un
      test por requisito de `requirements.md` §1.1 y nombre trazable
      (`test_f031_rN_…`). Caso central de R1: situación con `codigo_obra=0677`
      y cuerpo con `0999` → **no se sube nada**.
      **Verificación**: `pytest tests/test_f031_*.py -q` **en rojo**, y la
      salida (los N fallos, con su motivo) copiada a `progress/impl_F-031.md`
      como fase RED.

- [x] **T5**: `application/pipelines/paso_archivo.py` · `CodigosDelParte`,
      `_codigos_guardados(ctx)` leyendo de `ctx.situacion`, el nombrado pasando
      a usarlos (R1) y `_campo` retirado (`design.md` §4.1, §4.3).
      **Verificación**: `pytest tests/test_f031_nombrado_persistido.py -q` en
      verde y `pytest tests/test_f006_paso_archivo.py tests/test_f033_*.py
      tests/test_f019_orden_archivado.py -q` sin cambios en verde.

- [x] **T6**: `paso_archivo.py` · el cotejo `_exigir_codigos_declarados` en el
      punto **1 bis** del orden (`design.md` §4.2) y el parámetro
      `codigos_declarados`. Docstring del módulo con la enmienda fechada, al
      estilo de las de F-030 y F-033.
      **Verificación**: `pytest tests/test_f031_cotejo_de_codigos.py -q` en
      verde, **incluido** el test de R5: ante divergencia, el doble del
      repositorio no registra **ninguna** escritura y el doble de SharePoint no
      registra **ninguna** llamada.

- [x] **T7**: `interface_adapters/api/archivar.py` (pasa los códigos
      declarados; `_como_contexto` deja de rellenar los dos campos) y
      `function_app.py` (`CodigosNoCoinciden` → 409, y el comentario de los
      códigos del endpoint ampliado). `design.md` §5.
      **Verificación**: `pytest tests/test_f006_archivar_http.py
      tests/test_f030_circuito_borde_a_borde.py tests/test_f031_*.py -q` en
      verde, con el caso de `test_f006_archivar_http.py:341` adaptado y el caso
      nuevo de nombrado imposible **desde el código guardado** (R8) añadido.

## Bloque 3 · Front

- [ ] **T8 (RED)**: `services/postventa-front/tests_js/autoguardado_vaciado.test.js`
      con un test por requisito de `requirements.md` §1.3 (R18, R20, R21, R22),
      con temporizador inyectado como ya hacen los tests de F-026.
      **Verificación**: `cd services/postventa-front && node --test tests_js`
      **en rojo**, con la salida en `progress/impl_F-031.md`.

- [ ] **T9**: `js/autoguardado.js` · `vaciarPendientes()` (`design.md` §6.1),
      conservando la promesa del guardado en vuelo para poder esperarla, con el
      tope de rondas y sin tocar `parte.ediciones`.
      **Verificación**: `node --test tests_js` en verde, **incluido**
      `autoguardado.test.js` sin cambios (F-026 intacta).

- [ ] **T10**: `js/app.js` · `confirmarArchivo` espera el vaciado, **antes** de
      calcular la tanda (R19), y no la lanza si falla (R20), con su aviso.
      **Verificación**: `node --test tests_js` en verde, con
      `confirmacion.test.js` y `circuito.test.js` sin cambios; y
      `pytest tests -q` del servicio `front` en verde (el puente
      `tests/test_f007_js.py`).

## Bloque 4 · Cierre de alcance y documentación

- [ ] **T11**: `tests/test_f031_alcance_cerrado.py` (R29): `adjuntar.py`,
      `cerrar.py`, `paso_grafico.py`, `paso_cierre.py`, `sentencias.py`,
      `mapeo.py`, `repositorio_pg.py`, `domain/ports/persistencia.py`,
      `domain/models/estado.py` y todo `infrastructure/persistencia/sql/` **sin
      tocar** en esta feature; y ninguna columna, tabla ni sentencia nueva
      (R17).
      **Verificación**: `pytest tests/test_f031_alcance_cerrado.py -q` en verde.

- [ ] **T12**: documentación — recuadro fechado en `docs/ARCHITECTURE.md` (paso
      6 y semántica 8), nota de cierre en
      `specs/F-030-veredicto-persistido/design.md` §10.7 y nota al margen en
      `specs/F-006-sharepoint/design.md` (`design.md` §10). Comprobar y dejar
      escrito que `azure-apps/postventa_incidencias.md` **no** cambia (§7.1).
      **Verificación**: `bash harness/init.sh` en verde (valida los documentos
      normativos) y el diff revisado a ojo.

- [ ] **T13**: anotar en `progress/current.md` el hallazgo **H-1** de
      `design.md` §8 —`/api/adjuntar` y `/api/cerrar` toman los códigos del
      cuerpo— con la recomendación D-6 (ampliar el `acceptance` de F-034), para
      que lo decida el humano.
      **Verificación**: el bloque existe en `progress/current.md` y cita los
      ficheros y líneas medidos.

## Bloque 5 · Puertas de rigor y verde

- [ ] **T14**: **Verificación: MANUAL (humano)** · V1 de `design.md` §12. Con
      `func start` en `services/postventa-api` y `python dev_server.py` en
      `services/postventa-front`: corregir el código de obra de un parte y
      pulsar «archivar y cerrar» **antes** de 1,5 s. Se espera **no ver el
      409**, porque el vaciado lo evita; y forzándolo con la consola
      (`api.archivar` con un código distinto) se espera el 409 de R3 pintado en
      el parte. **No sube nada**: `ARCHIVO_HABILITADO` está apagado en local.
      El resultado real se copia a `progress/impl_F-031.md`.

- [ ] **T15**: **Verificación: MANUAL (humano)** · V2 de `design.md` §12. En el
      entorno desplegado y **solo con un parte que el humano autorice**:
      archivar y comprobar que el nombre y la carpeta son los mismos que antes
      de la feature. Única comprobación contra la biblioteca real. El resultado
      real se copia a `progress/impl_F-031.md`.

- [ ] **T16**: campaña de mutación sobre lo cambiado
      (`python -m harness.mutacion --feature F-031`), con **cero
      supervivientes** sin justificación escrita; informe en
      `progress/mutacion_F-031.md` con el nº de workers.
      **Verificación**: el informe existe, está completado y no deja ningún
      superviviente sin analizar.

- [ ] **T17**: Ejecutar `bash harness/init.sh` en verde.
