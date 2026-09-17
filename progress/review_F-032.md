<!-- progress/review_F-032.md -->
# F-032 · Review — «Los códigos no admiten espacios»

**Veredicto: APROBADO**

Rama `feature/F-032-codigos-sin-espacios`, HEAD `6c7f8f5`, base `dev`
(`3d82303`). Revisión hecha el 2026-09-17 contra `CHECKPOINTS.md`, la spec
`specs/F-032-codigos-sin-espacios/` y el informe `progress/impl_F-032.md`.

**Ninguna llamada a nada real**: ni Azure, ni Sigrid, ni SharePoint, ni el
PostgreSQL. Todo lo que aquí se afirma se midió sobre el repositorio local y
la suite de tests.

---

## 0 · Nivel de rigor y puertas que exige

`harness/features.json`, entrada F-032, declara `"rigor": "critico"`. Es el
nivel más exigente, así que se aplica entero:

| Puerta | Exigida | Estado |
|---|---|---|
| C1–C3, C3 bis, C5 | sí | cumplidas (C3 bis, N/A justificado) |
| Tests trazables (C4) | sí | cumplida |
| Fase RED en los requisitos centrales | sí | cumplida, con traza real |
| Cobertura de las líneas cambiadas ≥ 80 % | sí | **100 % de 12/12** |
| Campaña de mutación | sí | cumplida |
| **Cero supervivientes** | sí (solo `critico`) | **0 supervivientes** |
| Verificaciones `MANUAL (humano)` listadas con comando exacto | sí (solo `critico`) | cumplida (T14 y las dos de post-despliegue) |

---

## 1 · La promesa central: ninguna aprobación humana guardada se invalida

Es el motivo de que el alcance sea el que es, y es lo que se ha verificado con
más dureza. **Se cumple, y está demostrado por tres caminos independientes.**

### 1.1 · `aprobacion.py` sin diff en toda la rama — CONFIRMADO

```
$ git diff dev...HEAD -- services/postventa-api/domain/models/aprobacion.py
(vacío)
```

Confirmado por el reviewer, no dado por bueno del informe. Además,
`aprobacion.py` solo importa `hashlib` y `domain.models.validacion`: **no
importa `nombrado`**, así que `huella_de_veredicto` no tiene forma de heredar
el cambio de `normalizar_codigo`. El acoplamiento que R51 de F-028 prohíbe
sigue prohibido de hecho, no solo por test.

### 1.2 · Los tres literales del test son los de ANTES del cambio — VERIFICADO POR MEDICIÓN PROPIA

Esta es la trampa que el encargo pedía cazar: un literal recalculado *después*
del cambio y escrito como si fuera el de antes dejaría el control inútil. **No
es el caso.**

El reviewer creó un `git worktree` **desmontado** sobre `fd4fc70` —el commit
anterior a T1, con `normalizar_codigo` todavía colapsando espacios— y midió las
tres huellas con un script propio, sin reutilizar ni una línea del test ni del
informe. Resultado:

| # | Veredicto | Huella medida por el reviewer en `fd4fc70` | Literal en el test | Huella en HEAD |
|---|---|---|---|---|
| a | apto, `numero_incidencia="RS 26.09/0178"` | `49ab7cc6…c508a` | `49ab7cc6…c508a` | `49ab7cc6…c508a` |
| b | apto, `codigo_obra="06 26"` | `3aa32ce8…b626` | `3aa32ce8…b626` | `3aa32ce8…b626` |
| c | no apto + observaciones, `numero_incidencia="RS 26.09/0178"` | `4fb437b1…6652` | `4fb437b1…6652` | `4fb437b1…6652` |

Los tres coinciden **en el árbol previo, en el literal escrito y en HEAD**. La
medición de T1 es real y está bien fechada.

En la misma ejecución, el contraste que da sentido a todo:

```
                                   fd4fc70 (antes)      HEAD (después)
_normalizar("RS 26.09/0178")      'rs 26.09/0178'      'rs 26.09/0178'   ← el espacio se conserva
_normalizar("06 26")              '06 26'              '06 26'           ← el espacio se conserva
normalizar_codigo("RS 26.09/0178") 'RS 26.09/0178'     'RS26.09/0178'    ← el espacio se va
normalizar_codigo("06 26")         '06 26'             '0626'            ← el espacio se va
```

Las dos normalizaciones han quedado **efectivamente separadas**: una cambió, la
otra no. Es exactamente lo que el humano descartó tocar el 2026-09-17.

### 1.3 · El centinela de F-028 sigue verde sin tocarlo — CONFIRMADO

```
$ git diff dev...HEAD --stat -- tests/test_f028_huella_intacta.py tests/test_f028_espacios_codigos.py
(vacío)
```

Las siete huellas literales de F-028 se ejecutan en cada suite y pasan
(2897 passed). R18 queda cubierto por ese centinela **sin duplicarlo**, y R21
—el control de acoplamiento— sigue en su fichero de F-028, con la decisión de
no copiarlo razonada por escrito en la cabecera de `test_f032_huella_intacta.py`.

### 1.4 · El efecto, no solo el valor

`test_f032_r20_*` (3 tests) comprueba lo que de verdad importa: un parte no apto
**aprobado por una persona antes del cambio sigue `aprobado`** y sigue
constando decidido por una persona, también en el caso de la obra leída con
espacio. No se queda en comparar hexadecimales.

---

## 2 · El saneo no se ha comido ningún texto libre — CONFIRMADO

`CAMPOS_DE_CODIGO` está escrito literal y **no derivado de nada**:

```python
CAMPOS_DE_CODIGO: tuple[str, ...] = ("codigo_obra", "numero_incidencia")
```

`sanear_valor_leido(nombre, valor)` devuelve `valor` sin tocar cuando el campo
no está en esa tupla. Los siete restantes se copian letra por letra.

El material del test es el correcto: `OBSERVACIONES_INVENTADAS` lleva **espacios
dobles y tres saltos de línea** a propósito, y se comprueba que sale idéntica
por dos caminos —la regla del dominio
(`test_f032_r14_la_regla_del_dominio_copia_un_texto_letra_por_letra`, sobre los
siete campos) y el camino de escritura real
(`test_f032_r14_lo_que_se_guarda_conserva_el_texto_manuscrito`)—. Ni un dato
personal en el material: DNI `00000000T` (no emitido), promoción y observaciones
inventadas.

También se vigila lo contrario de pasarse de listo:
`test_f032_r14_el_saneo_no_toca_el_separador_de_un_codigo_de_obra` fija que
`06 - 77` conserva el guion —es una obra, no dos tramos— y
`test_f032_r14_la_regla_del_dominio_no_vacia_un_texto_de_solo_blancos` impide
que un texto de solo blancos se convierta en `None`, cosa que sí ocurre —y debe
ocurrir— con un código.

---

## 3 · `sanear_valor_leido` se apoya en `normalizar_codigo`, no en una copia — CONFIRMADO

El cuerpo entero de la función es:

```python
if valor is None or nombre not in CAMPOS_DE_CODIGO:
    return valor
return normalizar_codigo(valor) or None
```

Un `import` de `domain.models.nombrado`, ninguna regla reescrita. Y el test no
se fía de leerlo: `test_f032_r11_la_regla_del_dominio_no_es_una_copia_de_normalizar_codigo`
afirma `modulo_extraccion.normalizar_codigo is normalizar_codigo` —**identidad
de objeto**, no equivalencia de resultado— y además que todas las formas
equivalentes del número dan el mismo valor saneado. Si alguien reescribiera la
regla a mano, ese `is` se pone rojo aunque el resultado coincidiera.

Hexagonal respetada: `extraccion.py` importa `nombrado.py`, que es dominio
importando dominio. `nombrado` solo importa `errores`: no hay ciclo.

---

## 4 · La trampa del control atado al diff (T12) — NO SE REPITE EL DEFECTO DE F-030

El arreglo de F-030 está copiado y **funciona**. `test_f032_alcance_cerrado.py`
trae `RAMA_DE_LA_FEATURE`, `_fuera_de_la_rama_de_la_feature()`,
`_la_rama_ya_esta_en_dev()` y el guardián `_diff_de_la_rama_o_saltar()`.

No me he quedado en leerlo: lo he **probado**. Creé un worktree, mergeé la rama
en `dev` y ejecuté el fichero en los dos escenarios post-merge:

| Escenario | Resultado |
|---|---|
| En `dev`, con F-032 ya mergeada | `8 passed, 5 skipped` — verde |
| En la rama de la feature ya mergeada (nombre distinto de `dev`) | `8 passed, 5 skipped` — verde |

Los 5 que se saltan son exactamente los que leen el diff; los 8 que no dependen
de `git` se siguen ejecutando siempre. **`dev` no se pondrá en rojo al mergear.**

Además, el diseño es mejor que el de F-030 en un punto: cada regla de alcance
tiene **dos mitades**, la del diff y una hermana que mira el árbol y se ejecuta
en cualquier rama (`test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo`,
`test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado`,
`test_f032_r29_el_contrato_http_no_cambia`…). Así, aunque el control del diff
se salte, la regla más cara de deshacer sigue vigilada.

Y el control de los controles:
`test_f032_el_control_del_diff_no_esta_mirando_una_lista_vacia` exige que el
diff traiga algo y que entre lo cambiado esté `nombrado.py`. Sin él, los cuatro
«esto no aparece en el diff» se pondrían verdes sin comprobar nada.

> **Nota de método, por transparencia.** La simulación del merge se hizo en un
> worktree del scratchpad, pero `git merge` sobre `dev` movió el ref real de
> `dev` durante unos minutos. Se detectó y se **restauró a `3d823032`** con
> `git branch -f` (queda en el reflog: `dev@{0}: branch: Reset to 3d823032…`).
> Se borró la rama auxiliar y se eliminaron los dos worktrees. Comprobado
> después: `git rev-parse dev` = `3d823032…`, `git status --porcelain` vacío,
> `git worktree list` sin restos, `bash harness/init.sh` en verde. **El
> repositorio queda exactamente como estaba.**

---

## 5 · El test cuya expectativa cambió — CORRECTO, Y ES EL ÚNICO

`test_f006_r8_los_espacios_interiores_se_colapsan_a_uno` →
`test_f006_r8_los_espacios_interiores_se_eliminan`.

**¿Prueba menos que el viejo?** No: prueba **más**.

```python
# antes
assert normalizar_codigo("RS26.08   0123") == "RS26.08 0123"   # colapso a uno
# ahora
assert normalizar_codigo("RS26.08   0123") == "RS26.080123"    # eliminación total
```

La expectativa nueva fija una salida exacta que **solo** se puede producir
eliminando todos los blancos; la vieja toleraba un valor intermedio con
espacios, que es justo lo que el ERP no encuentra. El primer aserto del test
(`"RS26.08   -    0123" == "RS26.08-0123"`) no cambia.

**Nota fechada:** sí, y completa. La docstring recoge las **dos** enmiendas —la
de F-028 del 2026-09-15 y la de F-032 del 2026-09-17— con el texto literal de lo
que afirmaba antes en cada caso, el caso real que la invalidó y lo que no
cambia. Y la segunda enmienda de R8 está también en
`specs/F-006-sharepoint/requirements.md`, fechada, con quién la decidió.

**¿Cambió algún otro test de expectativa?** No. El diff de la rama restringido a
tests da cuatro ficheros **nuevos** (`test_f032_*`) y **un solo** fichero
modificado, `test_f006_nombrado.py`, con un único test tocado. Ni `test_f028_*`,
ni `test_f026_*`, ni `test_f009_*` aparecen. Ningún aserto se ha ajustado para
que algo pasara.

---

## 6 · R22, R24, R29 — CONFIRMADOS

| Regla | Comprobación del reviewer | Resultado |
|---|---|---|
| **R22** · ni `UPDATE`, ni fichero nuevo en `infrastructure/persistencia/sql/` | `git diff dev...HEAD -- services/postventa-api/infrastructure/` | **vacío**: la carpeta entera de infraestructura no aparece en el diff |
| **R22** · el test propio | `test_f032_r22_ningun_update_que_no_sea_el_de_un_upsert` exige que **cada** `UPDATE` sea la cola de un `ON CONFLICT`, sobre el código sin docstrings ni comentarios | correcto: no es un «no digas UPDATE» ingenuo |
| **R24** · `ArchivoPort` sin borrado ni renombrado | el test compara la tupla de métodos con la de F-006 y prohíbe los verbos; el diff no toca `domain/ports/archivo.py` ni `infrastructure/sharepoint/` | cumplido |
| **R29** · `services/postventa-front/` sin diff | `git diff dev...HEAD -- services/postventa-front/` | **vacío** |
| **R29** · contrato HTTP intacto | `test_f032_r29_el_contrato_http_no_cambia` escribe las claves esperadas literales (no las compara consigo mismas) y `CAMPOS_DEL_PARTE` contra su tupla esperada | cumplido |

La firma de `a_campo(crudo, nombre)` gana un parámetro **obligatorio y sin
valor por defecto**, decisión correcta y razonada: un saneo que no sanea en
silencio es peor que ninguno. No es contrato HTTP, es función interna del
módulo de cuerpos.

---

## 7 · C4 bis · Mutación, verificada de forma independiente

**El informe declara «Tiempo total: 44,3 s», por debajo de 5 minutos, así que
se reejecutó la campaña entera**, como manda C4 bis.

### 7.1 · Recálculo puro (alcance y nº de mutantes)

Con `harness.alcance.alcance_de_feature("F-032")` y
`harness.mutacion.generar_mutantes` (cálculo puro, sin ejecutar la suite ni
escribir en disco):

| Fichero | Líneas (reviewer) | Líneas (informe) | Mutantes (reviewer) |
|---|---|---|---|
| `application/pipelines/paso_extraccion.py` | 35 | 35 | 1 |
| `domain/models/extraccion.py` | 51 | 51 | 2 |
| `domain/models/nombrado.py` | 42 | 42 | 0 |
| `interface_adapters/api/cuerpos.py` | 33 | 33 | 0 |
| **Total** | **161** | **161** | **3** |

Base del diff idéntica a la del informe (`3d823032…`). **Coincide todo.**

### 7.2 · Muestreo de mutantes: los tres, con operador y texto

Los tres mutantes que genera la herramienta, recalculados por el reviewer,
coinciden uno a uno con los que la campaña reporta:

```
extraccion.py:105   [logico]      if valor is None or ...  -> if valor is None and ...
extraccion.py:107   [logico]      return normalizar_codigo(valor) or None
                                  -> return normalizar_codigo(valor) and None
paso_extraccion.py:129 [comparacion] if valor != bruto.valor: -> if valor == bruto.valor:
```

Son los tres puntos donde el saneo puede fallar en silencio, y los tres están
cazados. No es un cero sospechoso: hay mutantes, y son los que debe haber.

### 7.3 · Campaña reejecutada por el reviewer, con caché limpia

Se borraron `__pycache__` y `.pytest_cache` y se lanzó
`python -m harness.mutacion --feature F-032 --workers 3 --salida <scratchpad>`
(**fuera de `progress/`**, para no pisar el informe del implementer):

| Métrica | Informe del implementer | Reejecución del reviewer |
|---|---|---|
| Mutantes generados / evaluados | 3 / 3 | **3 / 3** |
| Muertos | 3 | **3** |
| **Supervivientes** | 0 | **0** |
| Timeouts | 0 | **0** |
| Workers | 3 | 3 |
| Tiempo total | 44,3 s | 49,9 s |

**Los totales coinciden. Los muertos están comprobados, no solo contados.**

### 7.4 · Coste por mutante (la campaña tardó lo que tenía que tardar)

> coste = «Tiempo total» × workers ÷ nº de mutantes

- Informe: 44,3 s × 3 ÷ 3 = **44,3 s por mutante**; la suite del servicio a
  solas, según el propio informe, 39,65 s.
- Reejecución del reviewer: 49,9 s × 3 ÷ 3 = **49,9 s por mutante**; la suite
  medida por el reviewer, **49,43 s** (`2897 passed, 5 skipped in 49.43s`).

El coste por mutante es **igual o superior** al tiempo de la suite en ambos
casos. Nada de sub-segundo, nada de caché envenenada: la suite se ejecutó
entera por cada mutante. Campaña sana.

### 7.5 · Fase RED

Trazas reales pegadas en el informe, no una frase:

- **T2** (R1–R10, el cambio de `normalizar_codigo`): **39 failed / 69 passed**,
  todos `AssertionError` sobre el valor, ninguno por importación ni por
  recogida. Traza literal de las cuatro filas que pagan la feature.
- **T6** (R11–R16, el saneo): **21 failed / 8 passed**. Los 8 verdes son las
  garantías que ya se cumplían —los siete textos ya se copiaban tal cual—, y
  está dicho así.
- **T10** añade su propia comprobación en rojo del test de borde a borde.

T11 y T12 no traen fase RED **y está justificado por escrito**: son controles
negativos cuyo «antes» es la medición de T1 sobre el árbol previo al cambio
—que este reviewer ha reproducido en §1.2—. Eso es evidencia **más fuerte** que
una rotura sintética, no más débil. Se acepta.

---

## 8 · Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con **exit code 0**. Ejecutado dos veces
      por el reviewer (al abrir y al cerrar la revisión), verde las dos.
      `PUERTA COBERTURA: 100.0% de 12 líneas cambiadas (12/12, umbral 80%,
      nivel critico)`.
- [x] Existen los diez ficheros obligatorios (lo confirma el propio `init.sh`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-032']`.
- [x] Rama actual `feature/F-032-codigos-sin-espacios`, nunca `main`.
- [x] `progress/current.md` encabeza con la sesión activa del 2026-09-17
      (F-032, bloques 4 y 5) y los bloques anteriores van marcados
      «SUPERADO por el bloque de arriba». **Observación, no defecto de esta
      feature**: el fichero acumula bloques desde el 2026-08-26 y ha crecido a
      ~3.500 líneas. Es deuda **preexistente** en `dev`, no la introduce F-032,
      que se limita a añadir sus bloques siguiendo la convención del repo. Se
      propone al humano en §11.
- [x] `progress/history.md` existe; F-032 no es `done` todavía, así que no le
      toca resumen aún.

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada. El dominio (`extraccion.py`) importa dominio
      (`nombrado.py`); ningún import de infraestructura. El borde HTTP
      (`cuerpos.py`) usa la regla **del dominio**, no una propia.
- [x] Primera línea con la ruta relativa en los cuatro ficheros nuevos y en los
      cuatro de producción tocados.
- [x] Sin `print()` añadidos (`git diff -U0 | grep '^+.*print('` → vacío), sin
      TODOs sueltos, sin dependencias nuevas. `ruff` sobre los ocho ficheros de
      la rama: **All checks passed** (los 61 avisos de `init.sh` son deuda
      previa y no crecen con esta rama).
- [x] Sin secretos: barrido del diff con
      `(password|passwd|secret|api[_-]?key|connectionstring|BEGIN .*PRIVATE KEY|AccountKey=)`
      → **cero coincidencias**. Ni cadenas de conexión, ni IDs de suscripción,
      ni IPs. El `oid` de los tests es una cadena opaca inventada, y hay un test
      del repo (`test_f006_repo_sin_identificadores.py`) que prohíbe que entre
      algo con forma de GUID.
- [x] La unidad de trabajo sigue siendo el **parte**: el saneo es por campo de
      un parte, no por PDF.
- [x] Nada se archiva ni se cierra sin validar; **ninguna escritura contra
      Sigrid** en esta rama (`infrastructure/sigrid/` fuera del diff), y
      `consultas.py` intacto.
- [x] Lo manuscrito no se descarta: es precisamente la garantía de §2. Las
      observaciones salen byte a byte iguales.
- [x] Firmado no es conforme: sin cambios en `validacion.py` ni en `firma.py`.
- [x] Reprocesar no duplica: `test_f032_r23_*` fija que reprocesar guarda el
      código limpio y que, si eso mueve la huella, la decisión anterior deja de
      contar (F-028 R19). Es el comportamiento correcto y está escrito para que
      nadie lo lea como un efecto colateral.
- [x] Ningún número de estado de Sigrid hardcodeado: no se toca nada del cierre.
- [x] Ningún PDF ni parte escaneado en git:
      `git log --all --diff-filter=A --name-only | grep -iE '\.pdf$|^muestras/'`
      → **vacío**, historial completo incluido.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: la rama **no añade ni modifica ningún fichero de
`docs/referencia/`**. El diff completo son 19 ficheros y ninguno cuelga de ahí.
Sin documento nuevo no hay cabecera de origen que exigir ni barrido de datos
sensibles que ejecutar sobre él. (El barrido de secretos sobre el diff entero sí
se hizo, y consta en C3.)

### C4 — La verificación es real

- [x] Trazabilidad requisito → test: tabla completa en §9. 29 requisitos, todos
      cubiertos o con su cobertura justificada por escrito.
- [x] Los unit tests no tocan red ni BBDD. `tests/conftest.py` parchea
      `socket.socket.connect` durante **toda la sesión** (fixture `sin_red`,
      `autouse`, `scope="session"`): abrir una conexión no es improbable, es
      imposible. Los tests de F-032 usan dobles en memoria
      (`RepositorioEnMemoria`) y comprueban los parámetros que se le pasan a
      `sentencias.upsert_parte`, sin base de datos.
- [x] Las verificaciones `MANUAL (humano)` están listadas en
      `progress/current.md` con su comando exacto: T14 con su SQL de solo
      lectura completo, y las dos de después del despliegue.

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"` en `harness/features.json`, valor válido.
- [x] **Fase RED** con salida real pegada (§7.5).
- [x] **Cobertura** en `[OK]`: 100 % de 12 líneas cambiadas (umbral 80 %).
- [x] **Mutación**: existe `progress/mutacion_F-032.md`, generado por la
      herramienta, con totales **verificados de forma independiente** (§7.1).
- [x] **Los muertos están comprobados, no solo contados**: campaña **reejecutada
      entera** por el reviewer con caché limpia, salida fuera de `progress/`,
      totales idénticos, árbol limpio después (§7.3).
- [x] **La campaña tardó lo que tenía que tardar**: coste por mutante 44,3 s
      (informe) y 49,9 s (reviewer), contra una suite de 49,43 s. Sano (§7.4).
- [x] Cero supervivientes, así que no hay ninguna sección de análisis en
      `PENDIENTE`. Nivel `critico` satisfecho sin necesidad de justificación.
- [x] Sección **«Evidencias · al cerrar la feature»** con los cuatro números
      —2897 passed/15 skipped/0 failed; 100 % de 12 líneas; 3 mutantes / 0
      supervivientes; suite 39,65 s a solas— **y el nº de workers (3 efectivos,
      tope 8)**, sin el cual no se podría calcular el coste por mutante.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A sin nada que justificar**: este repositorio **no declara**
`harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`). Es el caso
mayoritario que el propio checkpoint contempla. Además, `init.sh` no señaló
ninguna ruta tocada.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con **14 de 15 tareas `[x]`** y un commit `F-032 Tn: ...` por
      cada una (verificado en `git log dev..HEAD`: T1, T2, T3, T4, T5, T6, T7,
      T8, T9, T10, T11, T12, T13, T15, más la spec, el alta de F-033 y dos
      commits de informe).
      **T14 sigue `[ ]` a propósito y es correcto** — ver §10.
- [x] Sin ficheros temporales ni artefactos sospechosos: `git status
      --porcelain` vacío al abrir y al cerrar la revisión. (Existe un worktree
      preexistente en `.claude/worktrees/agent-a6e2f9…`, ajeno a esta feature y
      ya ignorado por git; los dos worktrees que creó el reviewer se han
      eliminado.)
- [x] `features.json` refleja el estado real: F-032 `in_progress`, rigor
      `critico`, prioridad 32, rama correcta. El último commit (`6c7f8f5`) es
      precisamente el que pone la ficha al día antes de la review.

---

## 9 · Trazabilidad: requisito → test

| Req | Qué exige | Test que lo cubre |
|---|---|---|
| R1 | eliminar todos los espacios de un código | `test_f032_r1_normalizar_elimina_todos_los_espacios` |
| R2 | cualquier blanco Unicode cuenta | `test_f032_r2_los_blancos_raros_tambien` |
| R3 | ceros a la izquierda intactos | `test_f032_r3_los_ceros_a_la_izquierda_siguen_intactos` |
| R4 | `None`/vacío/solo blancos → cadena vacía | `test_f032_r4_un_codigo_vacio_sigue_dando_cadena_vacia` |
| R5 | el código de obra no se parte por sus guiones | `test_f032_r5_el_codigo_de_obra_no_se_parte_por_sus_guiones` |
| R6 | el saneo vive en `normalizar_codigo` y en ningún otro sitio | `test_f032_r6_el_saneo_vive_en_normalizar_codigo` |
| R7 | `RS 26.09/0178` da el código que el ERP encuentra | `test_f032_r7_todas_las_formas_dan_el_mismo_codigo_para_el_erp` |
| R8 | mismo nombre de fichero para todas las formas | `test_f032_r8_todas_las_formas_dan_el_mismo_nombre_de_fichero`, `test_f032_r8_el_nombre_no_lleva_ni_barra_ni_ningun_blanco_de_mas`, `test_f006_r8_los_espacios_interiores_se_eliminan` |
| R9 | la obra con espacios no cambia la carpeta | `test_f032_r9_el_codigo_de_obra_con_espacios_no_cambia_la_carpeta` |
| R10 | las dos conversiones siguen idempotentes | `test_f032_r10_las_dos_conversiones_siguen_siendo_idempotentes` |
| R11 | el pipeline sanea los dos códigos | `test_f032_r11_la_extraccion_sanea_los_dos_codigos`, `test_f032_r11_el_pipeline_conserva_la_confianza_de_lo_que_sanea`, `test_f032_r11_la_regla_del_dominio_no_es_una_copia_de_normalizar_codigo` |
| R12 | el cuerpo HTTP sanea los dos códigos | `test_f032_r12_el_cuerpo_http_sanea_los_dos_codigos` |
| R13 | lo guardado en `postventa.partes` nace limpio | `test_f032_r13_lo_que_se_guarda_no_lleva_espacios`, `test_f032_r13_la_correccion_de_una_persona_tambien_se_guarda_limpia` |
| R14 | **solo** esos dos campos; los siete textos, tal cual | `test_f032_r14_*` (7 tests: dominio, pipeline, cuerpo HTTP y camino de escritura) |
| R15 | el saneo deja aviso, y solo cuando cambia algo | `test_f032_r15_el_saneo_deja_aviso`, `…sin_cambio_no_hay_aviso`, `…los_siete_textos_no_generan_aviso_de_saneo`, `…el_cuerpo_http_no_fabrica_avisos`, `…lo_que_se_guarda_no_gana_avisos_inventados_en_el_borde` |
| R16 | `None` sigue `None`; código de solo blancos → no leído | `test_f032_r16_*` (5 tests) |
| R17 | `aprobacion.py` intacto, ni una línea | `test_f032_r17_la_rama_no_toca_el_modulo_de_la_huella`, `…la_normalizacion_de_la_huella_sigue_siendo_la_de_antes`, `…la_huella_sigue_juntando_los_mismos_seis_campos`, `test_f032_r17_la_huella_conserva_el_espacio_de_dentro_del_tramo` **+ verificación directa del reviewer: diff vacío** |
| R18 | las siete huellas de F-028 siguen valiendo lo mismo | `tests/test_f028_huella_intacta.py`, **sin tocar ni un aserto**, verde en la suite. Cobertura por centinela existente, razonada por escrito. |
| R19 | dos casos nuevos, medidos antes del cambio | `test_f032_r19_la_huella_sigue_valiendo_lo_que_valia` (3 casos), `test_f032_r19_la_huella_canonica_se_recalcula_a_mano` **+ medición independiente del reviewer en `fd4fc70`** |
| R20 | ninguna decisión humana guardada pierde validez | `test_f032_r20_*` (3 tests) |
| R21 | las dos normalizaciones siguen separadas | `test_f028_*` (R51, en su fichero, no duplicado) **+ confirmado por el reviewer: `aprobacion.py` no importa `nombrado`** |
| R22 | ni `UPDATE`, ni DDL, ni fichero nuevo de SQL | `test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo`, `…ningun_update_que_no_sea_el_de_un_upsert`, `…la_rama_no_toca_la_persistencia` |
| R23 | reprocesar guarda limpio y caduca la decisión si procede | `test_f032_r23_reprocesar_guarda_el_codigo_ya_limpio`, `…y_si_eso_mueve_la_huella_la_decision_anterior_deja_de_contar` |
| R24 | `ArchivoPort` sin borrado ni renombrado | `test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado`, `…la_rama_no_toca_el_archivo_ni_su_adaptador` |
| R25 | el riesgo del huérfano, asumido y documentado | **documental**: `design.md` §6, `requirements.md` §5 y la sección T14 del informe. No es comportamiento testable: es una decisión escrita. Su mitigación operativa es R26/R27. |
| R26 | sin medición previa no se despliega | **MANUAL (humano)** · T14, `[ ]` sin marcar, con su SQL listo y su bloqueo escrito en tres sitios (`tasks.md`, `impl_F-032.md`, `current.md`) |
| R27 | si la medición da filas, esos partes no se re-archivan | **MANUAL (humano)** · procedimiento escrito en la sección «Qué hacer con el resultado» del informe; la garantía técnica que lo sostiene (no se borra ni se renombra) es R24, que sí tiene test |
| R28 | la tabla entera de formas da un único código/nombre/carpeta | `test_f032_r28_*` (3 tests: código, nombre y carpeta) |
| R29 | ni una clave del contrato HTTP, ni un fichero del front | `test_f032_r29_el_contrato_http_no_cambia`, `…la_rama_no_toca_ni_un_fichero_del_front` **+ verificación directa del reviewer: diff del front vacío** |

Extra, no exigido por ningún requisito y bien puesto:
`test_f032_d3_el_espacio_de_ancho_cero_sigue_pasando_y_se_declara` fija por
escrito el defecto declarado D3 (`U+200B` no es blanco para Python) en vez de
dejarlo como sorpresa futura.

---

## 10 · Lo que NO es motivo de rechazo (verificado como tal)

**T14 · la medición previa.** Comprobado: la casilla de `tasks.md` está
**`- [ ]`, sin marcar**, y es bien visible como pendiente. Lleva debajo una cita
en bloque que dice quién la tiene que hacer, por qué el implementer no puede
—no tiene credenciales y el arnés le prohíbe abrir la conexión— y que **sin ella
no se despliega (R26)**. La consulta está lista para copiar en
`progress/impl_F-032.md` §T14: `SET search_path TO postventa;` y un `SELECT` de
solo lectura sobre `postventa.archivos` y `postventa.partes`, con `translate`
para cazar también el espacio no separable (`chr(160)`) y el fino (`chr(8239)`).
El bloqueo está escrito en tres sitios independientes (`tasks.md`,
`impl_F-032.md`, `current.md`), y el líder lo lleva como primer punto de lo que
tiene que llevarle al humano. **Que esté pendiente es correcto. No se ha
intentado ejecutar: el reviewer no tiene credenciales y no ha abierto ninguna
conexión.**

**D-A1 · la capa L1 inerte.** Comprobado: el informe la cita como **«ya dado de
alta como F-033»**, no como propuesta, con su evidencia
(`archivar.py:118-128`, `paso_archivo.py:96,131`, `estado.py:189-208`) y el
motivo de no arreglarla aquí. Y F-033 existe de verdad en
`harness/features.json`: *«La primera capa contra el duplicado en SharePoint
está inerte desde el endpoint»*, `pending`, prioridad 33, rigor `critico`.

---

## 11 · Observaciones y propuestas (no bloquean, decide el humano)

1. **`progress/current.md` ha crecido a ~3.500 líneas**, con bloques desde el
   2026-08-26 marcados «SUPERADO». C2 pide que el fichero describa *solo* la
   sesión activa. Es deuda **preexistente**, ajena a F-032, y la convención de
   marcar lo superado funciona; pero el fichero ya cuesta de leer. **Propuesta
   al humano**: al mergear F-032, archivar en `progress/history.md` todo lo
   anterior al 2026-09-16 y dejar `current.md` con la sesión viva. No se aplica
   aquí: no es trabajo de esta feature ni de este reviewer.

2. **Automejora del protocolo del reviewer** (propuesta, no aplicada). El
   protocolo me manda simular el merge para probar los controles atados al
   diff, pero no advierte de que **`git merge` dentro de un worktree que tenga
   `dev` checkouteado mueve el ref real de `dev`**. Me pasó, lo detecté y lo
   restauré, pero es una trampa que puede dejar el repositorio del humano en un
   estado que nadie pidió. Propongo añadir a `.claude/agents/reviewer.md`, junto
   a la regla de la mutación fuera de `progress/`, una línea equivalente:
   *«Para simular el merge, usa un worktree en `--detach` y mergea sobre
   `HEAD` desmontado, nunca sobre la rama `dev`; comprueba `git rev-parse dev`
   antes y después.»* Vale para cualquier proyecto, así que iría también a
   `arnes-base`.

3. **Un acierto que merece propagarse a `arnes-base`.** El patrón de T12 —cada
   regla de alcance con **dos mitades**, la del diff y una hermana que mira el
   árbol y corre en cualquier rama— es estrictamente mejor que el arreglo de
   F-030, que solo enseñaba a saltar el control. Con dos mitades, la regla sigue
   vigilada aunque el diff no esté disponible. Propongo recogerlo como patrón
   recomendado en `CHECKPOINTS.md` o en `specs/SPECS.md`.

---

## 12 · Conclusión

F-032 hace exactamente lo que el humano decidió el 2026-09-17, y ni una línea
más. El arreglo vive en un solo sitio, las tres salidas cuelgan de él, la
entrada nace limpia por los dos caminos que escriben, y **la promesa que paga
la feature —que ninguna aprobación humana guardada se invalida— está demostrada
por medición propia sobre el árbol anterior al cambio, no por confianza en el
informe**.

Los controles de alcance no repetirán el defecto de F-030 al mergear: lo he
probado con el merge hecho. La campaña de mutación la he reejecutado entera y
da lo mismo. La suite entera pasa: 2897 tests.

Queda pendiente T14, que es del humano y bloquea el despliegue, no el merge.

**Veredicto: APROBADO.**
