<!-- specs/F-032-codigos-sin-espacios/tasks.md -->
# F-032 · Los códigos no admiten espacios — Tareas

> Una tarea = un commit `F-032 Tn: ...`. Ordenadas por dependencia; los tests
> van **antes o junto** a la implementación (**fase RED obligatoria**, rigor
> `critico`, cero supervivientes de mutación).
>
> La rama es `feature/F-032-codigos-sin-espacios`, ya creada y activa.
>
> **Los encargos al implementer se dan de uno en uno, por bloques**, y el
> implementer **para** al terminar cada bloque. Lo que hay al otro lado de este
> arreglo es la carpeta de SharePoint donde acaba un PDF con el DNI manuscrito
> de un cliente y la reclamación que se cierra en el ERP de producción.
>
> **No hay preguntas abiertas.** Las seis decisiones (D1–D6) están en
> `requirements.md` §8 y las tomó el humano el 2026-09-17. Si al implementar
> aparece una duda que no resuelvan la spec, `docs/ARCHITECTURE.md` o
> `docs/CONVENTIONS.md`, se **para** y se marca `blocked`; no se improvisa.

## Reglas duras de esta feature

1. **No se toca `domain/models/aprobacion.py`.** Ni `huella_de_veredicto`, ni
   `_normalizar`, ni una coma. Si una tarea parece necesitarlo, se está
   revocando decisiones humanas vivas: **parar** (R17, D1).
2. **Ningún aserto de `test_f028_huella_intacta.py`, `test_f028_espacios_codigos.py`
   ni `test_f026_*` cambia.** Son el control que esta feature tiene que pasar,
   no ajustar. El **único** test del árbol que cambia de expectativa es
   `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` (T5).
3. **Ni un `UPDATE`, ni un fichero nuevo en `infrastructure/persistencia/sql/`,
   ni DDL.** Las filas ya guardadas no se tocan (R22).
4. **`services/postventa-front/` no se toca**, ni `config/prompts.yaml`, ni
   `infrastructure/sigrid/consultas.py`, ni `domain/models/cierre.py`.
5. **Ninguna escritura contra Sigrid ni contra SharePoint desde local**, ni en
   tests ni a mano. Contra el PostgreSQL compartido, **solo lecturas** y solo
   dentro del schema `postventa`.
6. **Ni un dato personal en los tests**: ni DNI, ni observaciones copiadas de
   un parte de `muestras/`. Los códigos `0626`, `RS26.09/0149` y
   `RS 26.09/0178` sí: un código no identifica a nadie.
7. **Nada de `git push` ni de PRs.** Commits locales, en español, terminados con
   la línea de coautoría del encargo.

---

## Bloque 0 · Medir antes de tocar nada

- [x] **T1**: Medir, **en el árbol actual y antes de cambiar una línea**, la
      huella de los tres veredictos del control de §7.2 de `design.md`:
      (a) apto con `numero_incidencia="RS 26.09/0178"`, (b) apto con
      `codigo_obra="06 26"` y (c) no apto con observaciones y
      `numero_incidencia="RS 26.09/0178"`. Dejar los tres hexadecimales y la
      traza de la ejecución en `progress/impl_F-032.md`. **No se escribe código
      de producción en esta tarea.** | Verificación: la traza pegada en el
      informe, con el commit exacto sobre el que se midió.

- [x] **T2**: Crear `services/postventa-api/tests/test_f032_espacios_en_los_codigos.py`
      con **la tabla entera** de `design.md` §5 —las 13 formas del número y las
      8 del código de obra, con el caso real `RS 26.09/0178` escrito literal—
      parametrizada sobre las tres salidas: `normalizar_codigo`,
      `a_codigo_de_sigrid` y `nombre_de_archivo`/`carpeta_de_archivo`. Dominio
      puro, sin red, sin BBDD y sin IA. | Verificación: `pytest
      services/postventa-api/tests/test_f032_espacios_en_los_codigos.py` en
      **ROJO** para las filas 7–13 y B–D, con la traza en el informe (fase RED).

---

## Bloque 1 · El cambio de una línea

- [x] **T3**: Cambiar `normalizar_codigo` en
      `services/postventa-api/domain/models/nombrado.py`: eliminar **todos** los
      blancos (`"".join(bruto.translate(_A_GUION_NORMAL).split())`) y **borrar**
      `_ESPACIOS_JUNTO_AL_SEPARADOR`, que queda sin trabajo. Reescribir la
      docstring con la enmienda fechada del 2026-09-17 —qué hacía antes, qué
      costó y qué no cambia (ceros, sufijo, error ruidoso, la obra sin partir)—.
      | Verificación: `pytest services/postventa-api/tests/test_f032_espacios_en_los_codigos.py`
      en **VERDE** entero.

- [x] **T4**: Ejecutar la suite completa del servicio y comprobar que el único
      fallo es `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`, y que
      `test_f028_espacios_codigos.py`, `test_f028_huella_intacta.py`,
      `test_f026_*` y `test_f009_*` siguen **verdes sin tocarlos**. Si falla
      cualquier otro test, **parar** y anotarlo: es una consecuencia que la spec
      no previó. | Verificación: `pytest services/postventa-api/tests` con la
      lista de fallos pegada en el informe.

- [x] **T5**: Cambiar la expectativa de
      `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`
      (`tests/test_f006_nombrado.py:431-456`): `normalizar_codigo("RS26.08   0123")`
      pasa a valer `"RS26.080123"`, y el test se renombra a
      `test_f006_r8_los_espacios_interiores_se_eliminan`. En su docstring, la
      historia completa: qué afirmaba, por qué cambió el 2026-09-15 (F-028) y
      por qué vuelve a cambiar el 2026-09-17 (F-032), con el caso real delante.
      Añadir la **segunda enmienda de R8** en
      `specs/F-006-sharepoint/requirements.md` con el contenido de `design.md`
      §9.1. | Verificación: `pytest services/postventa-api/tests` en verde
      entero.

---

## Bloque 2 · La regla del saneo, en el dominio

- [x] **T6**: Crear `services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py`
      con los casos de R11–R16 en **ROJO**: los dos códigos salen sin espacios
      por el camino del pipeline y por el del cuerpo HTTP; los otros siete
      campos se copian **tal cual** (una observación manuscrita con espacios
      dobles y saltos de línea sigue igual); `None` sigue `None`; un código de
      solo blancos sale como no leído; y el saneo deja **aviso**. Con dobles en
      memoria, sin red, sin BBDD y sin IA. | Verificación: en **ROJO**, traza en
      el informe (fase RED).

- [x] **T7**: Añadir `CAMPOS_DE_CODIGO` y `sanear_valor_leido` a
      `services/postventa-api/domain/models/extraccion.py`, apoyándose en
      `normalizar_codigo` (nunca en una copia), con la docstring que explique
      por qué un código se sanea y un texto no. | Verificación: los tests de
      `test_f032_saneo_en_la_extraccion.py` que solo tocan el dominio, en verde;
      el resto sigue en rojo.

---

## Bloque 3 · Los dos llamantes, y solo esos dos

- [x] **T8**: Aplicar el saneo en
      `application/pipelines/paso_extraccion.py::_completar_y_sanear`, con el
      **aviso de R15** cuando el valor cambie, y corregir la docstring del
      módulo, que hoy afirma que este paso «no normaliza ningún valor».
      | Verificación: los tests del camino del pipeline, en verde.

- [x] **T9**: Aplicar el mismo saneo en
      `interface_adapters/api/cuerpos.py::a_extraccion` —el camino por el que el
      valor llega de verdad a `postventa.partes` (`design.md` §4)—, sin emitir
      avisos y sin cambiar ninguna clave del contrato. | Verificación:
      `test_f032_saneo_en_la_extraccion.py` en **VERDE** entero, y
      `pytest services/postventa-api/tests` sin regresiones.

- [ ] **T10**: Añadir el test de R13 **de borde a borde con dobles**: un cuerpo
      de `POST /api/parte` cuyo `codigo_obra` sea `06 26` y cuyo
      `numero_incidencia` sea `RS 26.09/0178` produce una llamada a
      `sentencias.upsert_parte` con `0626` y `RS26.09/0178`. Sin base de datos:
      se comprueba sobre los parámetros que se le pasan al repositorio.
      | Verificación: `pytest services/postventa-api/tests/test_f032_saneo_en_la_extraccion.py`
      en verde.

---

## Bloque 4 · Los controles que no pueden moverse

- [ ] **T11**: Crear `services/postventa-api/tests/test_f032_huella_intacta.py`
      con los **tres controles** de `design.md` §7.2: (1) las tres huellas
      medidas en T1, escritas literales; (2) el recálculo a mano con `hashlib`
      sobre la cadena canónica escrita en el test, que tiene que dar lo mismo, y
      la afirmación explícita de que `_normalizar("RS 26.09/0178")` conserva el
      espacio interior; (3) el efecto: un parte no apto aprobado por una persona
      **antes** del cambio sigue `aprobado` y sigue constando decidido por una
      persona. En la cabecera, de dónde salen los literales y por qué este
      fichero existe aunque ya haya un centinela de F-028. | Verificación:
      `pytest services/postventa-api/tests/test_f032_huella_intacta.py` en verde,
      y los tres literales coincidiendo con la traza de T1.

- [ ] **T12**: Añadir los controles de alcance: R17 —`aprobacion.py` sin diff en
      toda la rama—, R22 —ningún `UPDATE` ni fichero nuevo en
      `infrastructure/persistencia/sql/`—, R24 —`ArchivoPort` sin borrado ni
      renombrado—, R29 —`services/postventa-front/` sin diff y el contrato HTTP
      intacto—, y el de R23: reprocesar un parte guarda el código limpio y, si
      eso mueve la huella, la decisión anterior deja de contar. | Verificación:
      `pytest services/postventa-api/tests` en verde + `git diff dev --stat`
      pegado en el informe, enseñando que los ficheros prohibidos no aparecen.

---

## Bloque 5 · Documentación, medición y cierre

- [ ] **T13**: Añadir la precisión fechada de F-032 a la **semántica 5** de
      `docs/ARCHITECTURE.md` (texto en `design.md` §9.2) y dejar escrito en
      `progress/impl_F-032.md` el **defecto D-A1** —la capa L1 de idempotencia
      del archivo está inerte desde `/api/archivar`— con su evidencia
      (`archivar.py:118-128`, `paso_archivo.py:96,131`) para que el líder se lo
      proponga al humano como feature propia. **No se actualiza
      `azure-apps/postventa_incidencias.md`**: no cambia ningún endpoint, tabla
      ni variable (`design.md` §8). | Verificación: `bash harness/init.sh` en
      verde y el diff de documentación revisado.

- [ ] **T14**: Ejecutar la **medición previa** de `design.md` §6.3 contra la
      base `postventa` (consulta de **solo lectura**, dentro de nuestro schema)
      y anotar el resultado —número de filas y, si hay alguna, `hash_parte`,
      `carpeta` y `nombre_fichero`— en `progress/impl_F-032.md`. Si devuelve
      filas, **no se re-archivan esos partes desde el circuito** y se escribe la
      lista para que la decida el humano (R27). | Verificación: **MANUAL
      (humano)** · la consulta de `design.md` §6.3 tal cual, con su resultado
      real pegado en el informe. **Sin esta tarea no se despliega** (R26).

- [ ] **T15**: Campaña de mutación y cierre. | Verificación:
      `python -m harness.mutacion --feature F-032` con **cero supervivientes**
      (cada uno, si lo hubiera, con test nuevo o justificación escrita) y
      `bash harness/init.sh` en verde, con la cobertura de las líneas cambiadas
      por encima del umbral.

---

## Verificación manual pendiente del humano (fuera de la rama)

No son tareas del implementer: son lo que solo puede hacer el humano, y van
después del merge y del despliegue.

1. **La medición de T14 repetida contra el entorno desplegado**, si el
   despliegue se hace desde otra base que la de la medición.
2. **El caso real, de punta a punta**: subir un parte cuya IA lea el código con
   un espacio y comprobar que se archiva, se adjunta y **cierra** sin que nadie
   edite nada. Es escritura en el ERP de producción: exige autorización expresa
   del humano **para esa incidencia concreta**, dry-run previo y confirmación
   (`CLAUDE.md`, reglas duras). Es el criterio de aceptación 1 y solo se puede
   dar por cumplido aquí.
