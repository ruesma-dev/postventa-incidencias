<!-- progress/review_F-001.md -->
# F-001 · Esqueleto del monorepo y /health — informe de review

Revisor: agente `reviewer`. Fecha: 2026-08-18.
Rama revisada: `feature/F-001-esqueleto`. Base de integración: `dev`
(`8cb6c66`).

## Veredicto

**RECHAZADO** (`CHANGES_REQUESTED`).

El código en sí está bien escrito: cumple convenciones, no trae secretos, no
trae `print()`, tiene type hints, los tests no tocan red ni BBDD y las dos
suites están en verde. **Lo que falla es la verificación, no la artesanía.**

El motivo raíz de casi todos los rechazos es uno solo: **la feature no tiene
ni un commit**. Todo el trabajo está sin trackear en el árbol de trabajo. Como
las tres puertas del nivel `estandar` (cobertura, mutación y alcance) se
calculan sobre el diff de git, todas ellas ven una feature vacía y se
autodeclaran N/A. El portero imprime `ENTORNO LISTO` sobre un repositorio en
el que, formalmente, F-001 no existe.

## Nivel de rigor

`harness/features.json` declara `"rigor": "estandar"` para F-001. Según
`harness/rigor.json`, ese nivel exige:

| Puerta | ¿Exigida? | Estado |
|---|---|---|
| Fase RED en los requisitos centrales | sí | **AUSENTE** |
| Cobertura de las líneas cambiadas ≥ 80 % | sí | **N/A por omisión** (motivo falso) |
| Campaña de mutación con supervivientes analizados | sí | **AUSENTE** |
| Supervivientes máximos | sin límite (el reviewer juzga) | n/a |
| Tests trazables (C4) | sí | **AUSENTE** (ningún `test_f001_rN_*`) |

## Evidencia ejecutada por el reviewer

Todo lo que sigue se ejecutó de verdad en esta sesión, no se leyó del informe
del implementer.

### 1. `bash harness/init.sh` — VERDE, exit code 0

```
[OK] Arnés v1.4.1 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md ... CHECKPOINTS.md ... features.json ... rigor.json
     ... specs/SPECS.md ... progress/current.md ... progress/history.md
     ... docs/ARCHITECTURE.md ... docs/CONVENTIONS.md
     13 features, 13 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
     niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 11 avisos (deuda previa, no bloquea).
3 passed in 0.04s
[OK] pytest en verde (con medición de cobertura)
     2 servicio(s): api (python), front (otro)
[OK] harness/servicios.json válido
4 passed in 0.04s
[OK] servicio api (services/postventa-api): pytest en verde
[AVISO] servicio front (services/postventa-front): lenguaje 'otro' y sin
        comando_tests — NADIE está comprobando los tests de front
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-001-esqueleto
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
EXIT_CODE=0
```

**Ojo a la línea de la puerta de cobertura.** Dice que «F-001 no cambia líneas
Python de producción frente a dev». Es literalmente cierto y materialmente
falso: F-001 añade `function_app.py`, `config/settings.py`,
`config/logging_config.py`, `interface_adapters/api/health.py` y
`dev_server.py`. La puerta no los ve porque nadie los ha commiteado.

### 2. Las dos suites, con el intérprete que toca

Raíz (`.venv\Scripts\python.exe -m pytest tests -v`):

```
tests/test_servicios_declarados.py::test_cada_servicio_declarado_existe_en_disco PASSED
tests/test_servicios_declarados.py::test_cada_servicio_en_disco_esta_declarado  PASSED
tests/test_servicios_declarados.py::test_el_venv_declarado_existe               PASSED
3 passed in 0.03s
```

Servicio (`services\postventa-api\.venv\Scripts\python.exe -m pytest -v`):

```
tests/test_health.py::test_health_identifica_servicio_y_version                     PASSED
tests/test_health.py::test_health_refleja_el_entorno_configurado                    PASSED
tests/test_health.py::test_los_ajustes_se_leen_del_entorno                          PASSED
tests/test_health.py::test_sin_entorno_la_configuracion_falla_y_nombra_la_variable  PASSED
4 passed in 0.08s
```

7 tests, 7 en verde, ~0,11 s en total. Confirmado.

### 3. Estado de git: la feature no está commiteada

```
$ git log --oneline dev..HEAD
(vacío)

$ git diff --stat dev...HEAD
(vacío)

$ git status --short
 M .gitignore
 M harness/features.json
 M progress/current.md
?? coverage.json
?? harness/servicios.json
?? progress/impl_F-001.md
?? requirements-dev.txt
?? services/
?? tests/
```

Cero commits en la rama por encima de `dev`. Todo el entregable de F-001 vive
como ficheros sin trackear.

### 4. Recálculo independiente del alcance

```
$ python -c "from harness.alcance import alcance_de_feature; ..."
F-001: 0 fichero(s), 0 línea(s) de producción
       (origen rama, 8cb6c66..feature/F-001-esqueleto)
ficheros: []
```

### 5. Prueba de control del cero de mutantes (protocolo de `reviewer.md` §4)

El protocolo obliga, cuando el alcance da cero, a comprobar si el cero es
legítimo (no había nada que mutar) o sospechoso. Ejecuté
`harness.mutacion.generar_mutantes` sobre los ficheros que F-001 crea,
ignorando la exclusión de alcance (cálculo puro, sin ejecutar la suite ni
escribir en disco):

```
services/postventa-api/function_app.py                : 2 mutantes
services/postventa-api/config/settings.py             : 1 mutante
services/postventa-api/config/logging_config.py       : 0 mutantes
services/postventa-api/interface_adapters/api/health.py: 0 mutantes
services/postventa-front/dev_server.py                : 20 mutantes
TOTAL: 23
```

**El cero es sospechoso, no legítimo.** Hay 23 mutantes generables sobre el
código de esta feature. La campaña no se ha hecho, y no puede hacerse mientras
el alcance sea vacío.

### 6. Barrido de datos sensibles sobre lo nuevo

Patrones aplicados sobre `services/`, `tests/`, `harness/servicios.json`,
`requirements-dev.txt` y `progress/impl_F-001.md`:

- correos: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` → 0 coincidencias
- GUID (tenant/suscripción): `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` → 0
- IP privadas: `10.*`, `192.168.*`, `172.(16-31).*` → 0
- credenciales: `password|secret|api[-_]?key|token|connectionstring|pwd|contrasen`
  → 3 ficheros, **todos falsos positivos**: la palabra «secretos» en el
  docstring de `config/settings.py`, y `clientIdSettingName` /
  `clientSecretSettingName` en `staticwebapp.config.json`, que son **nombres**
  de App Settings, no valores.

**Resultado: limpio.** Y bien resuelto el `openIdIssuer`: lleva el marcador
`<TENANT_ID>` en vez del ID real, que es exactamente lo que `CLAUDE.md` exige.

### 7. Nada sensible ha entrado NUNCA en git

```
$ git log --diff-filter=A --name-only --pretty=format:"=== %h %s"
```

El histórico completo de ficheros añadidos (4 commits con altas) no contiene
ni un `.pdf`, ni un `.docx`, ni un parte escaneado. Lo único que entró en
`docs/referencia/` son los dos Markdown convertidos
(`01_cierre_incidencia_sigrid.md`, `02_parte_de_trabajo.md`). El `.gitignore`
del arnés bloquea `*.pdf`, `*.docx`, `*.xlsx`, `*.pptx`, `*.doc`, `*.xls`,
`*.ppt`, y `git check-ignore -v` confirma que los dos originales presentes en
el árbol están efectivamente ignorados. **Verificado, no supuesto.**

### 8. `ruff`

```
$ python -m ruff check services/ tests/
All checks passed!

$ python -m ruff check .
Found 11 errors.   (todos en harness/*.py: código del arnés genérico, deuda previa)
```

Confirma lo que dice el informe del implementer.

---

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. **Verificado, exit 0.**
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`. **Todos, comprobados por el propio portero.**

### C2 — El estado es coherente

- [x] Una sola feature en `in_progress` (F-001). Validado por `init.sh`.
- [x] La rama actual es `feature/F-001-esqueleto`, la declarada en
      `features.json`. No es `main`.
- [x] `progress/current.md` describe solo la sesión activa, sin restos.
- [x] Ninguna feature está en `done`, así que `history.md` vacío es correcto.

### C3 — El código respeta arquitectura y convenciones

- [x] **Arquitectura hexagonal respetada.** `domain/` (con `models/` y
      `ports/`), `application/` (con `pipelines/` y `services/`) e
      `infrastructure/` existen y están vacíos: no hay ni un import de
      infraestructura desde dominio porque no hay dominio todavía. Las
      dependencias reales van en la dirección buena:
      `function_app.py` → `interface_adapters.api.health` → `config.settings`,
      y `config/logging_config.py` → `config.settings`. El acierto de diseño
      es separar `health.py` de `function_app.py` para poder probar el
      contenido de la respuesta sin importar `azure.functions`.
- [x] **Primera línea con la ruta relativa: los 19 ficheros `.py`, los 2
      `.js`, el `.css` y el `index.html`.** Comprobado uno a uno, incluidos
      los `__init__.py` vacíos.
- [x] **Sin `print()`**: `grep -rn "print("` sobre `services/` y `tests/` da
      cero. `dev_server.py` usa `logging`, no `print`, aunque siendo un script
      de desarrollo las convenciones se lo permitirían.
- [x] **Sin TODO/FIXME/XXX sin contexto**: cero coincidencias.
- [x] **Sin secretos hardcodeados**: ver §6. `local.settings.json` está
      gitignoreado y su `.example` no trae valores. `.env.example` solo trae
      `ENTORNO` y `NIVEL_LOG`.
- [x] **Sin dependencias nuevas no previstas**: `azure-functions`, `pydantic`,
      `pydantic-settings` en el servicio; `pytest`, `ruff`, `coverage`,
      `pymupdf` en la raíz. Todas con rango de versión acotado. `pymupdf` se
      adelanta a F-002 y está justificado por escrito en el informe.
- N/A — **La unidad de trabajo es el parte**: F-001 no tiene dominio. N/A
      justificado: no hay ni una línea que razone sobre partes, remesas ni
      ficheros; el esqueleto no toma ninguna decisión de dominio.
- N/A — **Nada se archiva ni se cierra sin validar / dry-run contra Sigrid**:
      N/A justificado: F-001 no habla con Sigrid ni con SharePoint. No hay ni
      un import, ni una URL, ni un cliente HTTP hacia ellos (comprobado: el
      único cliente HTTP del repositorio es el proxy de `dev_server.py` hacia
      `localhost:7073`).
- N/A — **Lo manuscrito no se descarta / firma vs. marca simple**: N/A
      justificado: no hay extracción ni validación en esta feature.
- N/A — **Firmado no es conforme**: N/A justificado, mismo motivo.
- N/A — **Reprocesar no duplica**: N/A justificado: no hay ingesta ni
      persistencia.
- N/A — **Nada hardcodea un número de estado de Sigrid**: N/A justificado: no
      hay acceso a Sigrid. Confirmado por búsqueda: ni `conest`, ni `con.est`,
      ni ningún literal de estado en todo `services/`.
- [x] **Ningún PDF ni fichero con datos personales ha entrado nunca en git.**
      Verificado con `git log --diff-filter=A --name-only` sobre el histórico
      completo, no solo con el árbol. Ver §7.

### C3 bis — Los documentos que entran de fuera son seguros

**N/A justificado**: F-001 no añade ni modifica ningún fichero de
`docs/referencia/`. Los dos documentos que hay allí entraron en el commit
`8cb6c66`, anterior a esta rama, y quedan fuera del alcance de esta review.
El barrido de datos sensibles se ejecutó igualmente sobre todo lo nuevo de la
feature (§6) y salió limpio.

> Observación para el humano, fuera del alcance de F-001: los originales
> `docs/referencia/PASOS CERRAR INCIDENCIA.docx` y
> `docs/referencia/doc02871320260817093833.pdf` **siguen en el árbol de
> trabajo**. En git no están y no han estado nunca —eso está verificado y es
> lo que de verdad importa—, pero C3 bis pide que tampoco estén en el árbol.
> Es deuda del trabajo anterior, no de esta feature.

### C4 — La verificación es real

- [ ] **Cada criterio `acceptance` tiene ≥ 1 test trazable
      (`test_fXXX_rN_*`).** **FALLA.** Ninguno de los 7 tests sigue la
      convención de nombre trazable: se llaman `test_health_*`,
      `test_los_ajustes_*`, `test_sin_entorno_*`, `test_cada_servicio_*`,
      `test_el_venv_*`. No hay forma mecánica de atar un test a un criterio.
      Y hay un criterio **sin cubrir en absoluto** (ver la tabla de cobertura).
- [x] **Los unit tests no tocan red ni BBDD.** Verificado leyendo los cuatro
      ficheros de test: solo `monkeypatch` de variables de entorno, `tmp_path`
      y lectura de `harness/servicios.json` del disco local. Ni un socket, ni
      un cliente HTTP, ni un driver. La suite entera tarda 0,11 s, que es la
      confirmación indirecta.
- [ ] **Verificaciones `MANUAL (humano)` listadas en `progress/current.md`
      con su comando exacto.** **FALLA.** `current.md` no lista ninguna. El
      implementer ejecutó él mismo `func start`, `curl` y la comprobación en
      Chrome, y los resultados están en `impl_F-001.md`, pero el humano no
      tiene en `current.md` la lista de comandos que le toca repasar.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"` en `harness/features.json`, valor
      válido según `harness/rigor.json`.
- [ ] **Fase RED.** **FALLA.** `progress/impl_F-001.md` no contiene ni una
      traza de test en rojo anterior al código. El informe describe qué se
      creó y qué se verificó a posteriori, pero el nivel `estandar` exige la
      salida real del fallo previo para los requisitos centrales (el handler
      de `/health` y el fallo de configuración sin `ENTORNO`). No hay
      absolutamente nada al respecto: ni una frase, ni una traza.
- [ ] **Cobertura.** **FALLA.** La puerta sale en `N/A` con motivo impreso,
      pero el motivo es un artefacto de que no hay commits, no una propiedad
      de la feature. `CHECKPOINTS.md` es explícito: «Omitir la herramienta
      —no instalar `coverage`, no lanzar la campaña— no es un motivo: es el
      hueco que esto viene a tapar». Un N/A conseguido dejando el trabajo sin
      commitear es exactamente ese hueco.
- [ ] **Mutación.** **FALLA.** No existe `progress/mutacion_F-001.md`. La
      prueba de control del §5 demuestra que el cero de mutantes **no es
      legítimo**: hay 23 mutantes generables sobre los ficheros de la feature.
- [ ] **Supervivientes analizados, ninguno en `PENDIENTE`.** **FALLA por
      arrastre**: no hay campaña, luego no hay supervivientes que analizar.
- [ ] **Sección «Evidencias» con los cuatro números.** **FALLA.**
      `impl_F-001.md` trae una tabla titulada «Verificación» que cubre bien el
      primer número (tests ejecutados y resultado) y añade verificación manual
      valiosa, pero **faltan los otros tres**: cobertura de las líneas
      cambiadas, mutantes generados y supervivientes, y tiempo de la suite.
- [ ] **Ningún punto marcado N/A sin justificación escrita.** Ninguno de los
      anteriores se marcó N/A: se marcan directamente en rojo.

### C4 ter — Verificaciones extra por rutas sensibles

**N/A y sin nada que justificar**: no existe `harness/rutas_sensibles.json`
(solo el `.ejemplo.json` que trae el arnés). Es el caso mayoritario que el
propio checkpoint declara N/A por configuración.

### C5 — La sesión se cerró bien

- N/A — `tasks.md` con todas las tareas `[x]`: **N/A justificado por
      `sdd: false`**. F-001 no tiene `specs/F-001-*/`, así que no hay
      `tasks.md`. La nota de cabecera de `CHECKPOINTS.md` lo cubre
      expresamente.
- [ ] **Un commit por unidad de trabajo con formato `F-001: descripción`.**
      **FALLA.** No hay **ningún** commit. `git log dev..HEAD` está vacío. El
      formato mínimo que exige la nota de cabecera para features `sdd=false`
      es `F-XXX: <descripción>`, y no se ha emitido ni uno.
- [ ] **Sin ficheros temporales ni artefactos sin trackear sospechosos.**
      **FALLA, aunque sea menor.** `coverage.json` está en la raíz sin
      trackear y sin ignorar. Lo escribe `harness/init.sh` en cada ejecución
      (línea 276). El `.gitignore` de esta feature añadió `.coverage` pero se
      dejó `coverage.json`. Aparte de eso, todo lo demás sin trackear es el
      entregable de la feature, que debería estar commiteado.
- [x] `features.json` refleja el estado real: F-001 en `in_progress`, que es
      lo correcto mientras la review no la cierre.

---

## Cobertura: criterio `acceptance` → test que lo cubre

| # | Criterio de aceptación | Test que lo cubre | ¿Trazable? | Veredicto |
|---|---|---|---|---|
| 1 | `GET /api/health` devuelve **200** con nombre del servicio y versión | `test_health_identifica_servicio_y_version` cubre nombre, versión y `estado: ok` del **cuerpo**. **Nada cubre el 200 ni la ruta.** | no | **PARCIAL** |
| 2 | La configuración se lee de `.env` con pydantic-settings y falla claro si falta una variable obligatoria | `test_sin_entorno_la_configuracion_falla_y_nombra_la_variable` (el fallo, y que nombra la variable) + `test_los_ajustes_se_leen_del_entorno` (lectura del entorno). **La lectura del fichero `.env` en sí no se prueba.** | no | **PARCIAL** |
| 3 | Test unitario del handler de health, sin red ni BBDD | `test_health_identifica_servicio_y_version`, `test_health_refleja_el_entorno_configurado`. Sin red ni BBDD: confirmado. | no | **CUBIERTO** |
| 4 | `bash harness/init.sh` en verde | Ejecutado por el reviewer: exit 0. | n/a | **CUBIERTO** |

Los 3 tests de la raíz (`test_servicios_declarados.py`) no cubren ningún
criterio de F-001: verifican que `harness/servicios.json` describe la
realidad. Son tests útiles y bien pensados —una declaración que miente deja
zonas sin vigilar— pero son del arnés, no de la feature.

### Detalle del hueco del criterio 1

`function_app.py` **no lo importa ningún test**. Ni el `200`, ni el
`mimetype`, ni el `ensure_ascii=False`, ni el registro de la ruta con
`auth_level=ANONYMOUS` están cubiertos por nada automático. Sus 2 mutantes
sobrevivirían enteros. La única verificación del 200 es el `curl` manual que
el implementer pegó en su informe: vale como evidencia de que funciona hoy,
no como red de seguridad para mañana.

### Detalle del hueco del criterio 2

`test_sin_entorno_la_configuracion_falla_y_nombra_la_variable` hace
`monkeypatch.chdir(tmp_path)` justo para que **no** haya `.env`. Es la
decisión correcta para lo que ese test comprueba, pero deja el
`env_file=".env"` de `SettingsConfigDict` sin una sola prueba: nadie verifica
que un `.env` en el directorio de trabajo llegue de verdad a los ajustes.

---

## Cambios requeridos

Numerados y accionables. El 1 es la raíz de los tres siguientes.

1. **Commitear la feature en la rama `feature/F-001-esqueleto`.**
   Ahora mismo `git log dev..HEAD` está vacío y todo el entregable
   (`services/`, `tests/`, `harness/servicios.json`, `requirements-dev.txt`,
   `progress/impl_F-001.md`, y los cambios de `.gitignore`,
   `harness/features.json` y `progress/current.md`) está sin trackear.
   Formato de mensaje para una feature `sdd=false`: `F-001: <descripción>`.
   Mientras no haya commits, las puertas de cobertura y mutación miden una
   feature vacía y el review no puede validar nada contra el diff.

2. **Ejecutar la campaña de mutación y adjuntar
   `progress/mutacion_F-001.md`** (después del punto 1):
   `python -m harness.mutacion --feature F-001`.
   El nivel `estandar` la exige. La prueba de control del reviewer da **23
   mutantes** sobre los ficheros de la feature (2 en `function_app.py`, 1 en
   `config/settings.py`, 20 en `dev_server.py`), así que la campaña tiene
   material real. Cada superviviente necesita su sección de análisis
   completada; ninguna puede quedar en `PENDIENTE`.

3. **Volver a pasar la puerta de cobertura** (después del punto 1) hasta que
   `bash harness/init.sh` imprima `PUERTA COBERTURA: [OK]` con su porcentaje
   sobre el umbral del 80 %, en vez del `N/A` actual.

4. **Aportar la fase RED en `progress/impl_F-001.md`.**
   Nivel `estandar` la exige para los requisitos centrales. Hacen falta las
   trazas reales del fallo previo, como mínimo para:
   - el handler de `/health` (`interface_adapters/api/health.py`),
   - el fallo de configuración cuando falta `ENTORNO` (`config/settings.py`).

   Como el código ya existe, la fase RED se demuestra según el procedimiento
   de `CHECKPOINTS.md` C4 bis: rompiendo deliberadamente lo que el test
   vigila **en una copia aislada, nunca en el árbol real**, y pegando la traza
   de ese fallo. No vale una frase: vale la salida de pytest.

5. **Renombrar los tests a la convención trazable `test_f001_rN_*`**, atando
   cada uno a su criterio de `acceptance` (`docs/CONVENTIONS.md` §Tests y
   C4). Propuesta concreta en `services/postventa-api/tests/test_health.py`:
   - `test_health_identifica_servicio_y_version` → `test_f001_r1_health_devuelve_servicio_y_version`
   - `test_health_refleja_el_entorno_configurado` → `test_f001_r1_health_refleja_el_entorno`
   - `test_sin_entorno_la_configuracion_falla_y_nombra_la_variable` → `test_f001_r2_sin_entorno_falla_nombrando_la_variable`
   - `test_los_ajustes_se_leen_del_entorno` → `test_f001_r2_los_ajustes_se_leen_del_entorno`

6. **Cubrir el criterio 1 de verdad: falta un test del `200`.**
   `services/postventa-api/function_app.py` no lo importa ningún test, así que
   el código de estado, el `mimetype`, el `ensure_ascii=False` y el registro
   de la ruta no los vigila nada. Añadir un test que invoque
   `function_app.health(...)` con una `func.HttpRequest` construida en el
   propio test —sin levantar el runtime, sin red— y compruebe
   `status_code == 200`, el `mimetype` y el cuerpo deserializado. Sin eso, el
   criterio «devuelve **200**» solo está verificado por un `curl` manual.

7. **Añadir a `impl_F-001.md` la sección «Evidencias» con los cuatro
   números** que exige C4 bis. Hoy están 1 de 4:
   - tests ejecutados y resultado — **está** (3 + 4 en verde),
   - cobertura de las líneas cambiadas — **falta**,
   - mutantes generados y supervivientes — **falta**,
   - tiempo de la suite — **falta**.

8. **Listar en `progress/current.md` las verificaciones `MANUAL (humano)` con
   su comando exacto** (C4). El implementer las ejecutó y las contó en su
   informe, pero el humano necesita la lista en `current.md`, pendiente de
   repasar. Como mínimo:
   - `func start --port 7073` en `services/postventa-api/` y
     `curl http://localhost:7073/api/health`,
   - `python dev_server.py` en `services/postventa-front/` y
     `curl http://localhost:5173/api/health`,
   - abrir `http://localhost:5173/` y comprobar el semáforo verde.

9. **Ignorar `coverage.json`** en `.gitignore`. Lo escribe `harness/init.sh`
   en cada ejecución (línea 276) y hoy queda como artefacto sin trackear en la
   raíz. Esta feature ya añadió `.coverage`; falta su compañero. Conviene
   ignorar también `**/coverage.json`, porque `init.sh` escribe uno por
   servicio (línea 356).

---

## Observaciones que NO bloquean

Ninguna de estas es motivo de rechazo. Se dejan escritas porque cuestan poco
de arreglar ahora y caro más tarde.

1. **El front no lo comprueba nadie, y el portero lo dice en cada arranque.**
   `harness/servicios.json` declara `front` con lenguaje `otro` y sin
   `comando_tests`. El informe del implementer lo reconoce y lo aplaza a
   F-007. De acuerdo con aplazarlo, pero conviene que quede como decisión
   consciente y no como aviso al que uno se acostumbra: hoy `dev_server.py`
   son 20 de los 23 mutantes de la feature y no tiene ni un test.

2. **El `.env` como fichero no se prueba.** Ver el detalle del criterio 2 más
   arriba. Un test con un `.env` escrito en `tmp_path` cerraría el hueco en
   tres líneas.

3. **Paquetes vacíos de andamiaje.** `domain/` (+`models/`, `ports/`),
   `application/` (+`pipelines/`, `services/`) e `infrastructure/` son solo
   `__init__.py`. Es código muerto en sentido estricto, pero está
   explícitamente prescrito por `docs/ARCHITECTURE.md` y justificado en el
   informe («la forma hexagonal desde el primer commit, para que nadie
   improvise otra después»). **Lo doy por bueno**: el coste es nulo y el
   beneficio —que F-002 no invente su propia estructura— es real.

4. **`nivel_log: str = Field(default="INFO", ...)`** en `config/settings.py`.
   `docs/CONVENTIONS.md` dice «`default=` solo en la firma, nunca duplicado
   dentro de `Field()`». Aquí no hay duplicación —el valor aparece una sola
   vez—, así que lo leo como cumplido. Lo anoto porque la redacción de la
   convención da para dos lecturas y conviene que el humano fije cuál vale.

5. **`dev_server.py` escucha en `0.0.0.0`.** Viene así de `front-nominas`. En
   un portátil con la red de la oficina delante, eso expone el proxy hacia la
   Function local a toda la LAN. `127.0.0.1` sería el valor por defecto
   prudente. No bloquea: es un script de desarrollo y el comportamiento es
   heredado, no introducido aquí.

6. **`import json` dentro de `_send_error_json`** (`dev_server.py`). Import
   local sin motivo; `ruff` no lo marca. Heredado del original.

7. **Buen criterio que merece constar**, para que no se pierda al refactorizar
   más adelante:
   - `ENTORNO` obligatoria y sin valor por defecto, con el motivo escrito en
     el propio `Field(description=...)`. Un despliegue mal configurado falla
     en vez de mentir diciendo que es «local». Es la decisión correcta.
   - `health.py` separado de `function_app.py` para poder probarlo sin
     `azure.functions`.
   - El healthcheck **no** llama a Sigrid, SharePoint ni PostgreSQL, y el
     docstring explica por qué. Correcto: un healthcheck que llama a terceros
     marca el despliegue como fallido por algo que no es suyo.
   - `openIdIssuer` con marcador `<TENANT_ID>` en vez del ID real que sí
     lleva `front-nominas`. Cumple `CLAUDE.md` y corrige un problema que ya
     existía en otro repositorio.
   - Alpine fijado a `3.14.1` en vez de `3.x.x`, tras diagnosticar el fallo
     con la consola del navegador en vez de a ojo.

---

## Propuesta de mejora del arnés (para que la apruebe el humano, no aplicada)

Esta review encontró su hallazgo principal —la feature sin commitear— **a
pesar** del arnés, no gracias a él. El portero imprimió `ENTORNO LISTO` y la
puerta de cobertura imprimió `[OK] N/A` sobre un repositorio en el que F-001
no existía formalmente. La forma más fácil de saltarse las tres puertas del
nivel `estandar` es, hoy, no hacer commit.

**Propuesta para `harness/init.sh`**: cuando la feature en curso tiene
`rigor` distinto de `documental` y su rama **no tiene ningún commit por
encima de la base** (`git log dev..HEAD` vacío), la puerta de cobertura no
debería salir en `N/A` sino en **`[AVISO]`** con un texto que nombre la
causa, del estilo:

```
[AVISO] PUERTA COBERTURA: la rama feature/F-001-esqueleto no tiene commits
        sobre dev. El alcance es vacío por eso, no porque la feature no
        toque código: hay N ficheros sin trackear. Commitea antes de medir.
```

Detectar el caso es barato: el alcance ya sale 0 y basta con contrastarlo con
`git status --porcelain` para distinguir «no cambié código» de «no lo he
commiteado». Como el cambio vale para cualquier repositorio, si se acepta hay
que portarlo a `arnes-base` en el mismo trabajo (regla de propagación de
`CLAUDE.md`).

**Propuesta para `.claude/agents/reviewer.md`**: añadir al protocolo, antes
del paso 2, un paso explícito «comprueba que la rama tiene commits sobre la
base y que el diff no está vacío». Esta vez salió por el camino largo —la
prueba de control del cero de mutantes del §4—, pero esa prueba solo se
dispara si uno llega hasta la campaña de mutación. Conviene detectarlo en el
primer minuto.
