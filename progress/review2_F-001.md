<!-- progress/review2_F-001.md -->
# F-001 · Esqueleto del monorepo y /health — SEGUNDA review

Revisor: agente `reviewer`. Fecha: 2026-08-18.
Rama revisada: `feature/F-001-esqueleto`.
Base de integración: `dev` (`8cb6c66`).
Review anterior: `progress/review_F-001.md` (RECHAZADO).

- **Primera pasada de esta segunda review**: HEAD `3dab4d0` → RECHAZADO.
- **Revalidación**: HEAD `36b825f` → **APROBADO**.

Este documento conserva **íntegro** lo que se rechazó en la primera pasada. Lo
que sigue debajo del apartado de revalidación es el texto original tal cual se
escribió contra `3dab4d0`: no se ha borrado nada, para que quede el rastro de
qué se exigió y por qué.

---

## Veredicto tras la revalidación (HEAD `36b825f`)

**APROBADO** (`APPROVED`).

Los dos únicos motivos de rechazo están corregidos en el commit `36b825f`
(«F-001: corregir el aviso de ruff del test nuevo y completar las
evidencias»), y **verificados por este reviewer**, no leídos del informe.

### 1. `ruff` — CORREGIDO

```
$ .venv/Scripts/python.exe -m ruff check services/ tests/
All checks passed!

$ .venv/Scripts/python.exe -m ruff check .
Found 11 errors.
```

El `I001` de `services/postventa-api/tests/test_f001_adaptador_http.py:12` ya
no está: el diff de `36b825f` elimina la línea en blanco que partía el bloque
de imports (`1 deletion` en ese fichero). El contador global vuelve de **12 a
11 avisos**, que es el número que la review 1 dejó registrado como deuda
previa de `harness/*.py`. Confirmado en el portero:
`[AVISO] ruff: 11 avisos (deuda previa, no bloquea)`.

Y la afirmación del informe está corregida con honestidad, sin borrar lo que
pasó: `| ruff check services/ tests/ | All checks passed (tras corregir un
I001 que introdujo el test nuevo) |`. Deja constancia de que hubo un aviso, en
vez de reescribir la historia. Es la forma correcta de arreglarlo.

### 2. «Evidencias» con los cuatro números — COMPLETA

Leída la sección en `progress/impl_F-001.md`:

| Número | Valor |
|---|---|
| **Tests** | 10 en verde (3 en la raíz, 7 en el servicio `api`), 0 fallos |
| **Tiempo de las suites** | 0,03 s la de la raíz y 0,21 s la del servicio (0,24 s en total) |
| **Cobertura de las líneas de la feature** | 100 % (40/40), umbral 80 % |
| **Mutación** | 3 mutantes: 2 muertos, 1 superviviente |
| **Portero** | `init.sh` → ENTORNO LISTO, exit 0 |

Los **cuatro** que exige C4 bis están: tests y resultado, cobertura de las
líneas cambiadas, mutantes y supervivientes, y **tiempo de la suite**, que era
el que faltaba. La fila del portero se queda como quinta, que no estorba. Las
cifras de tiempo son coherentes con lo que mido yo (`3 passed in 0.04s` /
`7 passed in 0.40s` en esta ejecución; 0,01 s / 0,20 s en la anterior): varían
entre ejecuciones, están en el orden de magnitud correcto y la explicación que
acompaña —«tan bajo porque ningún test toca red, BBDD ni el runtime de
Functions»— es exactamente para lo que sirve ese número.

### 3. Nada más se ha roto por el camino — comprobado, no supuesto

`36b825f` toca tres ficheros: `progress/impl_F-001.md` (+1/-1 línea),
`progress/review2_F-001.md` (este informe, que se commiteó) y una línea en
blanco de menos en `test_f001_adaptador_http.py`. Aun así lo he revalidado
entero, porque un cambio en un fichero de test podría haber movido el alcance:

```
$ bash harness/init.sh
[AVISO] ruff: 11 avisos (deuda previa, no bloquea).
3 passed in 0.04s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
7 passed in 0.40s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 40 líneas cambiadas cubiertas
     (40/40, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-001-esqueleto
ENTORNO LISTO. Puedes trabajar.
EXIT_CODE=0
```

- **Las 10 pruebas siguen en verde** (3 + 7), ninguna se ha perdido al tocar
  los imports del fichero de test.
- **La cobertura sigue al 100 % de 40 líneas.**
- **El alcance y la campaña de mutación siguen siendo válidos.** Recalculado
  con HEAD en `36b825f`: 14 ficheros, 159 líneas, mismo `ref_diff`
  (`8cb6c66..feature/F-001-esqueleto`), y los **mismos 3 mutantes**, con el
  mismo operador y el mismo texto original→mutado que ya verifiqué en §5. El
  cambio del fichero de test no altera nada porque `harness/alcance` excluye
  `tests`. `progress/mutacion_F-001.md` **sigue fresco**: ningún commit
  posterior a la campaña toca código de producción.
- `git status --short` **vacío**; los cinco commits mantienen el formato
  `F-001: <descripción>`.

### Estado final de los checkpoints

Con la revalidación, **todos los checkboxes de C1–C5 quedan en `[x]` o en
`N/A` justificado por escrito**, con una sola excepción, que es la que el
humano aceptó expresamente:

- **C4 bis · Fase RED: `[ ]`**, incumplimiento **aceptado por el humano** y
  documentado por escrito en `progress/impl_F-001.md`, sin traza fabricada.
- **C3 bis · originales `.docx`/`.pdf` en el árbol**: deuda anterior a esta
  rama, aceptada; C3 bis es N/A en esta feature porque no toca
  `docs/referencia/`.

Ambas constan en el apartado siguiente y **no se cierran con la feature**: son
deuda declarada, no deuda escondida.

Las cuatro observaciones que no bloquean (mapeo generoso de los
`test_f001_r4_*`, el `.env` como fichero sin probar, `logging_config.py`
cubierto por arrastre y las propuestas de mejora del arnés) siguen vigentes y
se mantienen tal cual al final del documento, para F-002 y para el humano.

---

# Historial: primera pasada de esta review (HEAD `3dab4d0`) — RECHAZADO

> Lo que sigue es el informe original, conservado sin cambios. Sus dos motivos
> de rechazo están resueltos según la revalidación de arriba.

## Veredicto de la primera pasada

**RECHAZADO** (`CHANGES_REQUESTED`).

**Lo importante primero: el rechazo NO es por lo que motivó el primero.** Los
tres motivos de la review 1 —feature sin commitear, sin campaña de mutación ni
evidencias, tests sin nombre trazable y el criterio del 200 sin test— están
**resueltos y verificados de forma independiente por este reviewer**. La
campaña de mutación es real (recalculada mutante a mutante, coincide exacta),
la cobertura pasa al 100 % de las líneas de la feature y los tests nuevos
prueban comportamiento de verdad, no relleno.

Quedan **dos cosas pequeñas**, ambas de minutos, y una de ellas es lo que
impide aprobar sin mentir en un checkbox:

1. La sección «Evidencias» sigue trayendo **3 de los 4 números** que exige
   C4 bis: falta el **tiempo de la suite**. Era el punto 7 de la lista de
   cambios requeridos de la review 1, que enumeraba los cuatro uno a uno.
2. `ruff check services/ tests/` ya **no** está limpio: hay un `I001` nuevo en
   un fichero de esta feature, y el informe del implementer sigue afirmando
   «All checks passed». Es una evidencia que hoy es falsa.

La tercera pasada debería ser trámite.

---

## Incumplimientos ACEPTADOS por el humano (constan, no rechazan)

Se dejan escritos porque el arnés exige que un incumplimiento aceptado quede
documentado, no borrado:

1. **No hubo fase RED.** El nivel `estandar` la exige. `progress/impl_F-001.md`
   §«Fase RED: NO se hizo — excepción declarada» lo reconoce por escrito, con
   el motivo (el código se escribió antes que los tests) y con la decisión de
   **no fabricar una traza roja retroactiva**. Verificado: no hay ninguna traza
   inventada en el informe. Es la conducta correcta ante el incumplimiento:
   falsificar la evidencia justo donde el arnés existe para impedirlo sería
   peor que el incumplimiento. El humano aprobó cerrar F-001 con la excepción
   anotada, por ser la feature de calentamiento. Compromiso registrado para
   F-002: se empieza por los tests y la traza roja se pega.
2. **Los originales `.docx`/`.pdf` siguen en `docs/referencia/`** (C3 bis).
   Verificado en el árbol: `PASOS CERRAR INCIDENCIA.docx` (768 KB) y
   `doc02871320260817093833.pdf` (5,4 MB). Verificado también que **nunca han
   entrado en git** y que están efectivamente ignorados:

   ```
   $ git check-ignore -v docs/referencia/*.docx docs/referencia/*.pdf
   .gitignore:18:*.docx    docs/referencia/PASOS CERRAR INCIDENCIA.docx
   .gitignore:17:*.pdf     docs/referencia/doc02871320260817093833.pdf
   ```

   Es deuda anterior a esta rama (entraron con el trabajo de definición) y
   F-001 no toca `docs/referencia/`. No rechaza.

---

## Nivel de rigor

`harness/features.json` declara `"rigor": "estandar"` para F-001. Ese nivel
exige, según `harness/rigor.json` y la tabla de `CHECKPOINTS.md`:

| Puerta | ¿Exigida? | Estado en esta pasada |
|---|---|---|
| Tests trazables (C4) | sí | **[x] RESUELTO** — los 10 tests son `test_f001_rN_*` |
| Fase RED en requisitos centrales | sí | **[ ] AUSENTE — excepción aceptada por el humano** |
| Cobertura de líneas cambiadas ≥ 80 % | sí | **[x] OK — 100,0 % (40/40)** |
| Campaña de mutación con supervivientes analizados | sí | **[x] OK — 3 mutantes, 2 muertos, 1 superviviente equivalente y bien argumentado** |
| Cero supervivientes | no (solo `critico`) | n/a |
| Sección «Evidencias» con los 4 números | sí | **[ ] 3 de 4 en `3dab4d0`: falta el tiempo de la suite** → **[x] completa en `36b825f`** |

---

## Evidencia ejecutada por el reviewer

Todo lo que sigue se ejecutó en esta sesión. Nada se ha dado por bueno leyendo
el informe del implementer.

### 1. `bash harness/init.sh` — VERDE, exit code 0

```
[OK] Arnés v1.4.1 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md ... CHECKPOINTS.md ... features.json ... rigor.json
     ... specs/SPECS.md ... progress/current.md ... progress/history.md
     ... docs/ARCHITECTURE.md ... docs/CONVENTIONS.md
     13 features, 13 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 12 avisos (deuda previa, no bloquea).
3 passed in 0.03s
[OK] pytest en verde (con medición de cobertura)
     1 servicio(s): api (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 40 líneas cambiadas cubiertas
     (40/40, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-001-esqueleto
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
EXIT_CODE=0
```

**Las dos diferencias respecto de la review 1 son exactamente las que había
que arreglar y una que no:**

- La puerta de cobertura pasa del `N/A` falso («F-001 no cambia líneas Python
  de producción frente a dev») a un **`[OK]` real del 100 % sobre 40 líneas**.
  Ese N/A era un artefacto de no haber commiteado; ya no existe.
- El aviso de `front` sin `comando_tests` ha desaparecido: el front salió de
  la declaración de servicios al irse a F-007. Coherente.
- **`ruff` sube de 11 a 12 avisos.** Ver §7: el nuevo es de esta feature.

### 2. La rama tiene commits (motivo (a) de la review 1: RESUELTO)

```
$ git log --oneline dev..HEAD
3dab4d0 F-001: evidencias, analisis de mutacion y legado del front a F-007
9cb7f08 F-001: test que protege ensure_ascii=False en las respuestas
f053e37 F-001: sacar el front a F-007, coverage en el venv del servicio y tests trazables
cdcd79c F-001: esqueleto del monorepo, servicio postventa-api con /health y front minimo

$ git status --short
(vacío)
```

Cuatro commits, todos con el formato `F-001: <descripción>` que exige la nota
de cabecera de `CHECKPOINTS.md` para features `sdd=false`. Árbol limpio: ni un
fichero sin trackear, ni el `coverage.json` que la review 1 marcó (ahora está
en `.gitignore`, líneas 11-12, junto con `services/*/coverage.json`).

### 3. Las dos suites, con el intérprete que toca

```
$ .venv/Scripts/python.exe -m pytest tests -q
3 passed in 0.01s

$ services/postventa-api/.venv/Scripts/python.exe -m pytest services/postventa-api/tests -q
7 passed in 0.20s
```

**10 tests, 10 en verde, 0,21 s en total.** (Ese 0,21 s es justamente el cuarto
número que le falta al informe; ver el cambio requerido 1.) El tiempo, además,
es la confirmación indirecta de que ningún test toca red ni BBDD.

### 4. Verificación INDEPENDIENTE del alcance (protocolo `reviewer.md` §4)

Recalculado con `harness.alcance`, sin fiarme del informe:

```
origen: rama, ref_diff = (8cb6c66, feature/F-001-esqueleto)
services/postventa-api/application/__init__.py             1
services/postventa-api/application/pipelines/__init__.py   1
services/postventa-api/application/services/__init__.py    1
services/postventa-api/config/__init__.py                  1
services/postventa-api/config/logging_config.py           20
services/postventa-api/config/settings.py                 60
services/postventa-api/domain/__init__.py                  1
services/postventa-api/domain/models/__init__.py           1
services/postventa-api/domain/ports/__init__.py            1
services/postventa-api/function_app.py                    39
services/postventa-api/infrastructure/__init__.py          1
services/postventa-api/interface_adapters/__init__.py      1
services/postventa-api/interface_adapters/api/__init__.py  1
services/postventa-api/interface_adapters/api/health.py   30
TOTAL 159
```

**Coincide fichero a fichero y línea a línea con la tabla de «Alcance» de
`progress/mutacion_F-001.md`.** El informe de mutación no está escrito a mano.

(El 159 del alcance y el 40 de la puerta de cobertura no se contradicen: el
alcance cuenta todas las líneas añadidas —docstrings y blancos incluidos— y la
cobertura solo las ejecutables. Lo anoto para que nadie lo lea como
descuadre.)

### 5. Verificación INDEPENDIENTE de los mutantes

Recalculados con `harness.mutacion.generar_mutantes` sobre el alcance real
(cálculo puro: no ejecuta la suite ni escribe en disco):

```
settings.py:53   [entero]   '@lru_cache(maxsize=1)'                  -> '@lru_cache(maxsize=2)'
function_app.py:36 [booleano] 'json.dumps(cuerpo, ensure_ascii=False),' -> 'json.dumps(cuerpo, ensure_ascii=True),'
function_app.py:37 [entero]  'status_code=200,'                       -> 'status_code=201,'
TOTAL MUTANTES: 3
```

**3 mutantes recalculados = 3 mutantes declarados.** Y el único superviviente
del informe existe como mutante real, **con el mismo operador (`entero`) y el
mismo texto original→mutado**. Muestreo superado.

Los dos que el informe da por muertos son consistentes con la suite, leídos
los tests: `status_code=200 → 201` lo mata
`test_f001_r1_health_devuelve_200` (asevera `respuesta.status_code == 200`), y
`ensure_ascii=False → True` lo mata `test_f001_r1_el_json_no_escapa_los_acentos`
(asevera que `ó` **no** aparece en el cuerpo crudo). No hay ningún
«muerto» que no tenga un test que pueda matarlo.

### 6. Nada sensible ha entrado NUNCA en git

```
$ git log --diff-filter=A --name-only --pretty=format:"%h %s"
```

Histórico completo de altas, los 5 commits del repositorio. **Ni un `.pdf`, ni
un `.docx`, ni un `.xlsx`, ni un parte escaneado, en ningún commit.** Lo único
que ha entrado en `docs/referencia/` son los dos Markdown convertidos
(`01_cierre_incidencia_sigrid.md`, `02_parte_de_trabajo.md`) y su `README.md`,
en `8cb6c66`, anterior a esta rama. Lo que F-001 añade (commit `cdcd79c`) es
código, tests, configuración de ejemplo e informes. **Verificado sobre el
histórico, no sobre el árbol.**

Barrido de datos sensibles sobre **todos** los ficheros del diff
`8cb6c66..HEAD`, con los patrones: correos
`[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`, GUID de tenant/suscripción
`[0-9a-f]{8}-[0-9a-f]{4}-...`, IP privadas `10.x` y `192.168.x`, y
`password|secret|api[-_]?key|token|connectionstring|pwd|contrasen`.

**Resultado: limpio.** Las 9 coincidencias son todas falsos positivos y todas
en prosa: la palabra «secretos» en el docstring de `config/settings.py` y en
los informes, el criterio de F-010 en `features.json` («Ningún secreto en el
repositorio»), y `PATH=...` en el comando de `current.md`. **Ni un valor de
credencial, ni un GUID, ni una IP interna.** Al salir el front de la feature,
el `staticwebapp.config.json` con `<TENANT_ID>` ya ni siquiera está en juego.

### 7. `ruff` — hay un aviso NUEVO, y es de esta feature

> *(Corregido en `36b825f`; ver la revalidación al principio del documento.
> El texto original de la primera pasada se conserva.)*

```
$ .venv/Scripts/python.exe -m ruff check services/ tests/
I001 [*] Import block is un-sorted or un-formatted
  --> services\postventa-api\tests\test_f001_adaptador_http.py:12:1
Found 1 error.  [*] 1 fixable with the `--fix` option.
```

La review 1 dejó constancia de que ese mismo comando daba **«All checks
passed!»**. Ahora da 1 error, y el contador global de `init.sh` sube de 11 a
12: el aviso extra **no** es deuda de `harness/*.py`, es del fichero de test
que esta feature creó. Lo provoca la línea en blanco entre
`import azure.functions as func` (línea 16) y
`from config.settings import ...` (línea 18), que parte el bloque de imports.

Y `progress/impl_F-001.md` sigue afirmando en su tabla de verificación:
«`ruff check services/ tests/` | All checks passed». **Eso hoy es falso.** No
es un problema de estilo: es una evidencia del informe que no se sostiene al
comprobarla, que es exactamente lo que esta review tiene que detectar.

---

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. **Verificado, exit 0.**
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`. Comprobados por el propio portero, uno a uno.

### C2 — El estado es coherente

- [x] Una sola feature en `in_progress` (F-001). Validado por `init.sh`.
- [x] La rama actual es `feature/F-001-esqueleto`, la declarada en
      `features.json`. No es `main`.
- [x] `progress/current.md` describe solo la sesión activa: estado, las
      verificaciones MANUAL, las decisiones del humano de esta sesión y el
      contexto. Sin restos de sesiones anteriores.
- [x] Ninguna feature en `done`, luego `history.md` vacío es lo correcto.

### C3 — El código respeta arquitectura y convenciones

- [x] **Arquitectura hexagonal respetada.** Las dependencias van en la
      dirección buena y solo en ella:
      `function_app.py` → `interface_adapters.api.health` → `config.settings`,
      y `config/logging_config.py` → `config.settings`. `domain/` (+`models/`,
      `ports/`), `application/` (+`pipelines/`, `services/`) e
      `infrastructure/` existen vacíos como andamiaje. El acierto sigue siendo
      separar `health.py` de `function_app.py`: `health.py` no importa
      `azure.functions`, y por eso se puede probar sin runtime.
- [x] **Primera línea con la ruta relativa.** Comprobado uno a uno sobre los
      **19 ficheros `.py` del diff**, `__init__.py` vacíos incluidos: los 19
      la llevan y ninguna está mal escrita.
- [x] **Sin `print()` de debug, sin TODO/FIXME/XXX**: `grep -rnE
      "print\(|TODO|FIXME|XXX"` sobre `services/` y `tests/` da **cero
      coincidencias**.
- [x] **Sin secretos hardcodeados**: ver §6. `local.settings.json` está
      ignorado y su `.example` no trae valores.
- [x] **Sin dependencias nuevas no previstas**: `azure-functions`, `pydantic`,
      `pydantic-settings` en el servicio; `pytest`, `ruff`, `coverage`,
      `pymupdf` en la raíz. `coverage` se añadió al venv del servicio, que era
      el motivo de que `services/postventa-api/coverage.json` no se escribiera
      nunca. `pymupdf` se adelanta a F-002, justificado por escrito.
- N/A — **La unidad de trabajo es el parte**: **justificado**: F-001 no tiene
      dominio. Ni una línea razona sobre partes, remesas ni ficheros.
- N/A — **Nada se archiva sin validar / dry-run contra Sigrid**:
      **justificado**: F-001 no habla con Sigrid ni con SharePoint. Al salir el
      front, no queda ni un cliente HTTP en el repositorio.
- N/A — **Lo manuscrito no se descarta / firma vs. marca simple**:
      **justificado**: no hay extracción ni validación en esta feature.
- N/A — **Firmado no es conforme**: **justificado**, mismo motivo.
- N/A — **Reprocesar no duplica**: **justificado**: no hay ingesta ni
      persistencia.
- N/A — **Nada hardcodea un número de estado de Sigrid**: **justificado**: sin
      acceso a Sigrid, y confirmado por búsqueda (ni `conest`, ni `con.est`,
      ni literal de estado en todo `services/`).
- [x] **Ningún PDF ni fichero con datos personales ha entrado nunca en git.**
      Verificado con `git log --diff-filter=A --name-only` sobre el histórico
      completo. Ver §6.

### C3 bis — Los documentos que entran de fuera son seguros

**N/A justificado**: F-001 no añade ni modifica ningún fichero de
`docs/referencia/`. Comprobado sobre el diff real `8cb6c66..HEAD`: ninguno de
los cuatro commits toca esa carpeta. Los tres documentos que hay allí entraron
en `8cb6c66`, anterior a esta rama.

El barrido de datos sensibles se ejecutó igualmente sobre **todo** el diff de
la feature (§6) y salió limpio, con los patrones escritos ahí.

> **Constancia del incumplimiento aceptado (no rechaza).** Los originales
> `PASOS CERRAR INCIDENCIA.docx` y `doc02871320260817093833.pdf` siguen en el
> árbol de trabajo de `docs/referencia/`. En git no están y no han estado
> nunca —verificado—, y `git check-ignore` confirma que están bloqueados por
> `.gitignore`. C3 bis pide además que no estén en el árbol: es deuda del
> trabajo de definición, anterior a esta rama, y el humano la ha aceptado
> como tal. Conviene resolverla antes de que crezca la carpeta.

### C4 — La verificación es real

- [x] **Cada criterio `acceptance` tiene ≥ 1 test trazable
      (`test_f001_rN_*`) y todos pasan.** **RESUELTO** (motivo (c) de la
      review 1). Los 10 tests siguen la convención; ver la tabla de cobertura
      más abajo. El criterio 1 —el `200`— ya no depende de un `curl` a mano:
      lo cubre `test_f001_r1_health_devuelve_200`.
- [x] **Los unit tests no tocan red ni BBDD.** Verificado leyendo los cuatro
      ficheros: solo `monkeypatch` de variables de entorno, `tmp_path`,
      lectura de `harness/servicios.json` del disco y una `func.HttpRequest`
      **construida en el propio test**. Ni un socket, ni un cliente HTTP, ni
      un driver, ni el runtime de Functions levantado. Los 0,21 s de la suite
      lo confirman.
- [x] **Verificaciones `MANUAL (humano)` listadas en `progress/current.md`
      con su comando exacto.** **RESUELTO.** `current.md` §«Verificaciones
      MANUAL (humano) — comandos exactos» trae el `func start` con el
      `VIRTUAL_ENV` del venv del servicio (con el motivo: si no, `func` coge
      el Python global y falla con `ModuleNotFoundError: pydantic`), el `curl`
      con el cuerpo esperado y el resultado obtenido.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"` en `harness/features.json`, valor
      válido según `harness/rigor.json`.
- [ ] **Fase RED.** **NO SE CUMPLE — excepción aceptada por el humano y
      documentada por escrito** en `progress/impl_F-001.md` §«Fase RED: NO se
      hizo». No se ha fabricado traza retroactiva; verificado. Por indicación
      expresa del humano, **no es motivo de rechazo en esta feature**. Queda
      escrito, junto con el compromiso para F-002.
- [x] **Cobertura.** **RESUELTO.** `PUERTA COBERTURA: 100.0% de 40 líneas
      cambiadas cubiertas (40/40, umbral 80%, nivel estandar)`. El `N/A` falso
      de la review 1 ha desaparecido porque su causa —no haber commiteado— ya
      no existe.
- [x] **Mutación.** **RESUELTO Y VERIFICADO DE FORMA INDEPENDIENTE.** Existe
      `progress/mutacion_F-001.md` generado por la herramienta. El alcance
      recalculado con `harness.alcance` coincide fichero a fichero (§4) y los
      mutantes recalculados con `harness.mutacion.generar_mutantes` coinciden
      en número, operador y texto original→mutado (§5). No es un informe
      escrito a mano.
- [x] **Cada superviviente con su análisis completado, ninguno en
      `PENDIENTE`.** El único superviviente lo tiene, y **el análisis es
      honesto** (juicio razonado abajo). El nivel `estandar` no exige cero
      supervivientes.
- [ ] **Sección «Evidencias» con los cuatro números.** *(En la revalidación
      con HEAD `36b825f` este checkbox pasa a `[x]`: la fila «Tiempo de las
      suites» ya está.)* **NO SE CUMPLE en `3dab4d0`: hay 3
      de 4.** La tabla trae tests (10 en verde), cobertura (100 %, 40/40) y
      mutación (3 mutantes: 2 muertos, 1 superviviente), pero la cuarta fila
      es «Portero: ENTORNO LISTO, exit 0», que no es uno de los cuatro
      números. **Falta el tiempo de la suite**, y no aparece en ninguna otra
      parte del informe (comprobado con `grep -nEi "tiempo|segundo|[0-9]+[,.][0-9]+ ?s"`
      sobre `impl_F-001.md`: cero coincidencias). Era el punto 7 de la lista
      de cambios de la review 1, que enumeraba los cuatro uno a uno. **Este es
      el checkbox que impide aprobar.**
- [x] **Ningún punto de este bloque marcado N/A sin justificación escrita.**
      Ninguno se ha marcado N/A: la fase RED va en `[ ]` con su excepción
      escrita y aceptada, y las Evidencias en `[ ]` con su motivo.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A y sin nada que justificar**: no existe `harness/rutas_sensibles.json`
(comprobado el contenido de `harness/`: solo está el
`rutas_sensibles.ejemplo.json` que trae el arnés). Es el caso mayoritario que
el propio checkpoint declara N/A por configuración.

### C5 — La sesión se cerró bien

- N/A — `tasks.md` con todas las tareas `[x]`: **N/A justificado por
      `sdd: false`**. F-001 no tiene `specs/F-001-*/`. La nota de cabecera de
      `CHECKPOINTS.md` lo cubre expresamente, y sustituye la exigencia por el
      formato `F-XXX: <descripción>` en los commits, que **se cumple en los
      cuatro** (§2).
- [x] **Sin ficheros temporales ni artefactos sin trackear sospechosos.**
      **RESUELTO.** `git status --short` sale **vacío**. El `coverage.json`
      suelto que marcó la review 1 está ahora ignorado, junto con
      `services/*/coverage.json` (`.gitignore` líneas 11-12).
- [x] `features.json` refleja el estado real: F-001 sigue en `in_progress`,
      que es lo correcto mientras la review no la cierre.

---

## Cobertura: criterio `acceptance` → test que lo cubre

| # | Criterio de aceptación | Test(s) que lo cubren | ¿Trazable? | Veredicto |
|---|---|---|---|---|
| 1 | `GET /api/health` devuelve **200** con nombre del servicio y versión | `test_f001_r1_health_devuelve_200` (el 200, invocando `function_app.health`), `test_f001_r1_health_devuelve_json_con_servicio_y_version` (cuerpo + `mimetype`), `test_f001_r1_el_json_no_escapa_los_acentos` | sí | **CUBIERTO** |
| 2 | La configuración se lee de `.env` con pydantic-settings y falla claro si falta una variable obligatoria | `test_f001_r2_los_ajustes_se_leen_del_entorno`, `test_f001_r2_sin_entorno_falla_y_nombra_la_variable` | sí | **CUBIERTO** (con un hueco menor: ver observación 2) |
| 3 | Test unitario del handler de health, sin red ni BBDD | `test_f001_r3_health_identifica_servicio_y_version`, `test_f001_r3_health_refleja_el_entorno_configurado` | sí | **CUBIERTO** |
| 4 | `bash harness/init.sh` en verde | Ejecutado por el reviewer: exit 0. Además `test_f001_r4_*` (3) vigilan que `harness/servicios.json` describe la realidad | sí | **CUBIERTO** |

El hueco que la review 1 abrió en el criterio 1 —`function_app.py` sin
importarlo ningún test, con el `200`, el `mimetype` y el `ensure_ascii=False`
sin vigilancia— **está cerrado**, y se nota en la mutación: de los 3 mutantes
de la feature, los 2 de `function_app.py` mueren.

---

## Juicio propio 1 — ¿es honesto el análisis del superviviente?

Superviviente: `config/settings.py:53`, `@lru_cache(maxsize=1)` →
`@lru_cache(maxsize=2)`. El implementer lo declara **mutante equivalente**.

**Es honesto, y es correcto.** No es un «equivalente» dicho a la ligera para
librarse de escribir un test. Lo he comprobado por mi cuenta:

- `obtener_ajustes()` **no recibe argumentos** (verificado en el código:
  `def obtener_ajustes() -> Ajustes:`). La clave de caché de `lru_cache` se
  construye a partir de los argumentos, así que **solo puede existir una
  clave**. Con `maxsize=1` o con `maxsize=2` la caché nunca llega a contener
  más de una entrada: mismos hits, mismos misses, misma instancia devuelta,
  mismo número de lecturas del entorno. **No hay ninguna entrada observable
  del sistema que distinga las dos versiones.** Es equivalencia de verdad, no
  «no se me ocurre cómo probarlo».
- El argumento de por qué no se añade test es el correcto y está bien
  formulado: distinguirlas obligaría a asegurar sobre `cache_info()`, es
  decir, sobre el detalle de implementación de la caché en vez de sobre el
  comportamiento del servicio. Ese test se rompería en el primer refactor sin
  que nada estuviera mal. Un reviewer que exigiera ese test estaría empeorando
  la suite.
- **Lo que más me convence de que el análisis no es una excusa**: en la misma
  campaña había un segundo superviviente, `ensure_ascii=False → True` en
  `function_app.py:36`, y **no** se declaró equivalente. Se reconoció como
  hueco real y se mató con un test nuevo
  (`test_f001_r1_el_json_no_escapa_los_acentos`), con su motivo escrito: el
  servicio devolverá motivos de validación en español a Posventa. Quien quiere
  librarse de la campaña declara equivalentes los dos. Aquí se distinguió, y
  se distinguió bien.

## Juicio propio 2 — ¿los tests prueban comportamiento o son relleno?

**Prueban comportamiento.** He leído los cuatro ficheros enteros. No hay ni un
test tautológico, ni un `assert True`, ni un test que asevere sobre un mock que
él mismo acaba de configurar.

Lo que sostiene el juicio, más allá de la lectura:

- **La mutación lo corrobora, que es la prueba objetiva.** De los 3 mutantes
  generables sobre la feature, **2 mueren**. Un test de relleno no mata
  mutantes: los deja pasar. El `status_code=200 → 201` y el
  `ensure_ascii=False → True` caen porque hay aserciones reales sobre el
  resultado.
- `test_f001_r1_el_json_no_escapa_los_acentos` **nació de un superviviente**.
  Es el mejor tipo de test que puede salir de una campaña: no se escribió para
  subir un número, se escribió porque la campaña señaló una decisión de diseño
  (español sin escapar en las respuestas) que nadie protegía. Y comprueba el
  **cuerpo crudo** (`.decode("utf-8")`, `"producción" in ...` y
  `r"ó" not in ...`), no el deserializado, que es lo único que distingue
  `ensure_ascii=False` de `True`. Está bien pensado.
- `test_f001_r2_sin_entorno_falla_y_nombra_la_variable` hace
  `monkeypatch.chdir(tmp_path)` **a propósito**, para que no haya un `.env`
  que rescate la configuración y el test compruebe el fallo de verdad en
  cualquier máquina. Y no se conforma con que reviente: asevera que el mensaje
  **nombra** la variable. Eso es probar la calidad del fallo, no solo su
  existencia.
- El `conftest.py` hace `obtener_ajustes.cache_clear()` **antes y después** de
  cada test. Sin eso, la caché de `lru_cache` filtraría ajustes entre tests y
  los `monkeypatch.setenv` de un test no tendrían efecto en el siguiente. Es
  el detalle que separa una suite que funciona por casualidad de una que
  funciona. Está bien resuelto.
- Los `test_f001_r4_*` de la raíz no son relleno tampoco: verifican que
  `harness/servicios.json` **no miente** (ruta que existe, ningún servicio en
  disco sin declarar, venv declarado presente). Una declaración que miente deja
  zonas del repositorio sin comprobar mientras el portero imprime que todo va
  bien. Es exactamente el fallo que hundió la primera review, atacado desde
  otro ángulo.

Los más flojos son los dos `test_f001_r3_*`: aseveran sobre un diccionario de
cuatro claves y no matan ningún mutante (no hay ninguno que matar en
`health.py`). Pero cubren el criterio 3 tal y como está redactado —«test
unitario del handler de health»— y fijan el contrato del cuerpo. Son mínimos,
no son relleno.

---

## Cambios requeridos

> **AMBOS RESUELTOS** en el commit `36b825f` y verificados en la revalidación
> del principio de este documento. Se conservan tal cual se escribieron.

Solo dos. Ninguno toca código de producción.

1. **Añadir el cuarto número a la sección «Evidencias» de
   `progress/impl_F-001.md`: el tiempo de la suite** (C4 bis). Hoy la cuarta
   fila es «Portero», que no es uno de los cuatro que exige el checkpoint. El
   dato, medido por el reviewer en esta sesión: **0,21 s en total** (0,01 s la
   suite de la raíz, 0,20 s la del servicio `api`). Era el punto 7 de la
   review 1, que ya enumeraba los cuatro; se resolvieron tres.

2. **Dejar `ruff check services/ tests/` limpio y corregir la afirmación del
   informe.** Dos cosas, en este orden:
   - `services/postventa-api/tests/test_f001_adaptador_http.py:12` tiene un
     `I001` («Import block is un-sorted or un-formatted»), causado por la
     línea en blanco entre `import azure.functions as func` (línea 16) y
     `from config.settings import ...` (línea 18). Es auto-corregible:
     `python -m ruff check --fix services/postventa-api/tests/test_f001_adaptador_http.py`.
     Tras el arreglo, el contador de `init.sh` debe volver a 11 avisos, todos
     de `harness/*.py` (deuda previa del arnés genérico, ajena a esta feature).
   - La tabla de verificación de `progress/impl_F-001.md` afirma «`ruff check
     services/ tests/` | All checks passed». **Hoy es falso.** Una vez
     corregido el `I001` volverá a ser cierto; si por lo que sea no se
     corrige, hay que cambiar la afirmación. Un informe que dice haber
     verificado algo que no se sostiene al comprobarlo es peor que no decir
     nada.

---

## Observaciones que NO bloquean

1. **El mapeo de los `test_f001_r4_*` al criterio 4 es generoso.** El criterio
   4 es «`bash harness/init.sh` en verde», y esos tres tests no comprueban que
   `init.sh` esté verde: comprueban que `harness/servicios.json` describe la
   realidad. Son buenos tests y el criterio 4 lo verifica el reviewer
   ejecutando el portero, así que no falta nada. Pero conviene saber que la
   trazabilidad ahí es por afinidad, no exacta.

2. **El `.env` como fichero sigue sin probarse.** Ya se anotó en la review 1
   como no bloqueante y sigue igual. `env_file=".env"` en el
   `SettingsConfigDict` podría borrarse y los 10 tests seguirían en verde: el
   único test que se acerca (`test_f001_r2_sin_entorno_falla_y_nombra_la_variable`)
   hace `chdir` a un directorio vacío justamente para que **no** haya `.env`.
   Un test que escriba `ENTORNO=x` en un `.env` dentro de `tmp_path`, haga
   `chdir` allí y asevere que llega a los ajustes cierra el hueco en tres
   líneas, y es el único criterio de F-001 cuya literalidad («se lee de
   `.env`») no está cubierta. Recomendado para F-002, no exigido aquí.

3. **`logging_config.py` no tiene test propio.** Sus 20 líneas cuentan en la
   cobertura porque `function_app.py` llama a `configurar_logging()` al
   importarse, y el `getattr(logging, ..., logging.INFO)` no genera mutantes.
   O sea: está cubierto por arrastre, no vigilado. Es aceptable para lo que
   hace (fijar un nivel), pero el día que decida algo, necesitará su test.

4. **Buen criterio que merece constar**, para que no se pierda al refactorizar:
   - `ENTORNO` obligatoria y sin valor por defecto, con el motivo escrito en
     el propio `Field(description=...)`: un despliegue mal configurado falla
     en vez de mentir diciendo que es «local».
   - `health.py` separado de `function_app.py` para poder probarlo sin
     `azure.functions`, y el healthcheck que **no** llama a Sigrid, SharePoint
     ni PostgreSQL, con el porqué en el docstring: un healthcheck que llama a
     terceros marca el despliegue como fallido por algo que no es suyo.
   - `coverage` añadido al venv del servicio. Sin eso, el arnés no escribía
     `services/postventa-api/coverage.json` y la cobertura del servicio no
     contaba para nada: un agujero silencioso en el monorepo.
   - Sacar el front a F-007 en vez de dejar que sus 114 líneas de
     `dev_server.py` hundieran la cobertura al 26 %. La alternativa fácil era
     bajar el umbral.

---

## Propuesta de mejora del arnés (para el humano; NO aplicada)

Reitero la de la review 1, porque sigue vigente y esta pasada demuestra que
habría servido: **`harness/init.sh` debería distinguir «no cambié código» de
«no lo he commiteado»** antes de imprimir `PUERTA COBERTURA: N/A`. Basta con
contrastar el alcance vacío con `git status --porcelain`. Es barato y vale
para cualquier repositorio, así que si se acepta hay que portarlo a
`arnes-base` en el mismo trabajo (regla de propagación de `CLAUDE.md`).

Y una nueva, de esta pasada: **`.claude/agents/reviewer.md` debería pedir que
el reviewer compruebe los avisos de lint *del diff*, no solo el total.** El
contador global de `init.sh` pasó de 11 a 12 avisos y eso es fácil de leer
como ruido de la «deuda previa» que el propio portero anuncia; hizo falta
ejecutar `ruff` acotado a `services/` y `tests/` para ver que el aviso nuevo
era de la feature y que contradecía una línea del informe del implementer. Un
portero que imprimiera «12 avisos (11 previos, **1 nuevo en el diff**)» lo
haría evidente sin depender de que al reviewer se le ocurra acotar.
