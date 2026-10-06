<!-- specs/F-053-datos-para-el-portal/tasks.md -->
# F-053 · Dos datos que pide el portal — Tareas

> Rama `feature/F-053-datos-para-el-portal` (desde `dev` en `349ba06`). Rigor
> **`critico`**: fase RED en los requisitos centrales, cobertura ≥ 80 % de las
> líneas cambiadas y **cero supervivientes** de mutación sin justificación
> aceptada por el humano. Cada tarea = un commit `F-053 Tn: ...`.
>
> **Encargos por bloques**: un bloque por encargo al implementer, y parar. Los
> `pytest` se lanzan desde `services/postventa-api` con
> `.venv/Scripts/python.exe -m pytest …`. Ningún test toca red, base de datos ni
> IA. Nada se escribe en Sigrid, en SharePoint ni en la base desde esta rama.
>
> **Decisiones** (`design.md` §8): D-3 (las tres líneas añadidas en tests de
> F-036) **requiere el visto bueno del humano** antes del Bloque 1; D-1, D-2,
> D-4, D-5 y D-6 se implementan como están salvo que el humano diga otra cosa.
>
> **Aprobado por el humano el 2026-10-06** («si, todo ok»): D-1, D-2 y D-3 tal
> cual; T7 (`azure-apps`) **pasa al líder**, que la hace al desplegar (como en
> F-035), y no entra en el Bloque 3 del implementer.

## Bloque 1 · `importado_at_utc` (R1–R7)

- [x] **T1** (RED): crear `tests/test_f053_importado_at_utc.py` con R1–R7
      (`design.md` §7: `ahora` distinto en la primera y la segunda subida;
      `AHORA` con microsegundo 0 y la forma exacta; `01:30+02:00` → `23:30` del
      día anterior en UTC, con `timezone(timedelta(hours=2))`; instante *naive*
      → `null` con 200; reproceso de una parcial → la fecha nueva; los cuerpos
      de error sin la clave) y añadir **una línea**, `"importado_at_utc",`, al
      conjunto `CLAVES` de `tests/test_f036_importar_http.py` (D-3).
      Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f053_importado_at_utc.py tests/test_f036_importar_http.py -q`
      **falla**, y solo por la clave que falta (`KeyError`/aserción sobre
      `importado_at_utc`); el informe del implementer copia la salida.
- [x] **T2** (GREEN): `_instante_utc` y la clave en `serializar_importacion`
      (`interface_adapters/api/importar.py`, `design.md` §4), con el docstring
      del módulo al día.
      Verificación: el mismo `pytest` de T1 **en verde**, y
      `.venv/Scripts/python.exe -m pytest tests -q` en verde.

## Bloque 2 · `oficio.distintos` (R8–R17)

- [x] **T3** (RED): crear `tests/test_f053_distintos_dominio.py` (R9–R13 sobre
      `pares_distintos`) y `tests/test_f053_propuestas_distintos.py` (R8–R16 por
      la ruta HTTP con los dobles de F-036: «distinto, luego mismo» no sale y
      «mismo, luego distinto» sí, con `ahora` crecientes; el par `0033` · `0133`
      como textos; el par a la vez en `distintos` y en `avisos`; `distintos: []`
      sin pares y en una obra sin oficios; una sola llamada a
      `ultimas_decisiones`; la respuesta de `POST /api/catalogos/decisiones` sin
      `distintos`) y añadir **dos líneas**, `"distintos": [],`, en las dos
      igualdades completas de `oficio` de `tests/test_f036_catalogos_http.py`
      (D-3).
      Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f053_propuestas_distintos.py tests/test_f036_catalogos_http.py -q`
      **falla** por `ImportError` de `pares_distintos` y por la clave
      `distintos` que falta, y por nada más.
- [x] **T4** (GREEN, dominio): `pares_distintos` en
      `domain/models/equivalencias.py` (`design.md` §4), reutilizando
      `_ultimas`.
      Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f036_equivalencias_dominio.py -q` en verde.
- [x] **T5** (GREEN, aplicación y borde): `PropuestasDeOficios.distintos` (al
      final, sin defecto), su cálculo en `propuestas_de_oficios` y la clave en
      `leer_propuestas`, con los docstrings al día. `_grupos()` y
      `GruposVigentes` no se tocan.
      Verificación: el `pytest` de T3 **en verde**, y
      `.venv/Scripts/python.exe -m pytest tests -q` en verde.

## Bloque 3 · documentación y evidencias (R18–R21)

- [x] **T6**: el párrafo de `design.md` §6 en `docs/INTEGRACION.md` (sin
      encabezado, antes de «Los diecisiete quedan en nivel **anónimo**») y
      `tests/test_f053_documentacion.py`, que busca en «## 8 · Qué exponemos
      nosotros» `importado_at_utc`, `+00:00`, `ya_importado`, «original»,
      `oficio.distintos`, `codigo_a`, «última decisión» y «guion».
      Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f053_documentacion.py tests/test_f036_documentacion.py tests/test_f019_documentacion.py -q`
      en verde.
- [ ] **T7** (**líder, al desplegar**, tras T10; no es del implementer): el mismo párrafo en
      `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`, §8,
      y una línea en «LO QUE CAMBIA EN ESTA REVISIÓN» (los dos campos, aditivos,
      «desde su despliegue»); **commit local** en `azure-apps`, sin push.
      Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1 --stat`
      muestra solo ese fichero, y `git -C C:\Users\pgris\PycharmProjects\azure-apps grep -n "oficio.distintos" -- postventa_incidencias.md`
      lo encuentra.
- [x] **T8**: evidencias de rigor. (a) Mutación:
      `python -m harness.mutacion --feature F-053 --base 349ba06 --timeout 900`,
      informe en `progress/mutacion_F-053.md`, **cero supervivientes** sin test
      nuevo o justificación escrita para el humano. (b) Alcance (R18, R19):
      `git diff --stat 349ba06 -- services/postventa-front infra services/postventa-api/infrastructure services/postventa-api/function_app.py services/postventa-api/domain/ports`
      **vacío**, y `git diff 349ba06 -- services/postventa-api/tests/test_f036_*.py`
      con exactamente **tres** líneas `+` y **cero** líneas `-` de contenido.
      Verificación: las dos salidas y el resumen del informe de mutación,
      copiados en `progress/impl_F-053.md`.
- [ ] **T9**: `bash harness/init.sh` en verde (incluye tests, cobertura de
      líneas cambiadas ≥ 80 % y la validación de `features.json`).
      Verificación: salida de `bash harness/init.sh` en verde, anotada en
      `progress/impl_F-053.md`.

## Bloque 4 · MANUAL (humano), tras la review APROBADA y el merge a `dev`

- [ ] **T10**: **MANUAL (humano) · desplegar el backend desde una copia limpia
      de `dev`**, nunca desde la carpeta de trabajo. En PowerShell, desde la
      raíz del repositorio:
      `git worktree add --detach ..\pv-despliegue-F053 dev` (separada, para no
      bloquear la rama `dev`), luego
      `powershell -ExecutionPolicy Bypass -File ..\pv-despliegue-F053\infra\desplegar_backend.ps1`
      (y `DESPLEGAR` cuando lo pida), y al terminar
      `git worktree remove ..\pv-despliegue-F053`. Antes de lanzarlo,
      `git -C ..\pv-despliegue-F053 log -1 --oneline` tiene que ser el merge de
      F-053 en `dev`.
      Verificación: MANUAL (humano). El commit desplegado y la salida final del
      script, en `progress/current.md`.
- [ ] **T11**: **MANUAL (humano) · comprobación en producción**, `Ctrl+F5` en
      cada página:
      1. *Precondición*: el `v2` de la 0677 se importó **completo** (en V4 f de
         F-035 respondió «ya se había importado»). Si no consta, **PARA** y
         pregunta: reimportar una parcial escribe una importación más.
      2. **V1**: en `importar.html`, reimportar el `v2`: el resumen dice
         «Resumen de la importación original del DD/MM/AAAA», con la fecha de
         la importación original.
      3. **V2**: en `oficios.html`, obra 0677, **sin pulsar nada**: sección
         «Decididos como distintos» con el par **0033 · 0133** (Solados y
         Alicatados M.O. · Solados y Alicatados). No se pulsa «Son el mismo».
      Verificación: MANUAL (humano). Lo que se ve en cada paso, anotado en
      `progress/current.md`.
- [ ] **T12**: `bash harness/init.sh` en verde tras el cierre (líder).
      Verificación: salida de `bash harness/init.sh` en verde.
