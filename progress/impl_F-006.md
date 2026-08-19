<!-- progress/impl_F-006.md -->
# F-006 · Nombrado y archivo en SharePoint — Informe de implementación

> Rama `feature/F-006-sharepoint`. Rigor **`critico`**: fase RED con traza
> real pegada, cobertura de líneas cambiadas y campaña de mutación con cero
> supervivientes.
>
> Este informe se escribe **conforme avanza el trabajo**, no al final.
>
> **Ni un dato real.** Todos los códigos y nombres que aparecen aquí
> (`0677`, `RS26.08/0123`) son **inventados**, los mismos que usa la spec.
> Ningún identificador de tenant, sitio, drive o aplicación entra en este
> fichero ni en ningún otro del repositorio.

---

## 0 · Las cuatro decisiones del humano del 2026-08-20 que modifican la spec

La spec de F-006 se escribió el 2026-08-19 y se aprobó. El **2026-08-20** el
humano tomó cuatro decisiones que la modifican. Se aplican tal cual y se dejan
escritas aquí, con su fecha, porque la spec no se reescribe.

### D-a · El cliente HTTP es `httpx`, no `msal` + `requests` (2026-08-20)

**Qué cambia**: **T8**. `design.md` §3.2 y la tarea T8 proponían
`msal>=1.28,<2.0` y `requests>=2.31,<3.0`. Era la decisión abierta **D1** de
`design.md` §10 («qué librería de Graph reutilizar»), declarada **no
bloqueante** precisamente porque el puerto aísla al resto del servicio.

**Lo decidido**: el servicio no tiene hoy ningún cliente HTTP, y el repositorio
`partes` ya resuelve esto **en producción** con `httpx`. El humano eligió
alinearse con él. Se declara `httpx` en
`services/postventa-api/requirements.txt` con su rango de versión, al estilo de
las demás dependencias.

**Consecuencia**: cambia **solo `infrastructure/sharepoint/`**, que es
exactamente lo que `design.md` §10 (D1) predijo. Ni el dominio, ni la
aplicación, ni el borde HTTP se enteran. El test de arquitectura R22 ya
vigilaba `httpx` junto a `msal` y `requests`, así que tampoco cambia.

*(La lectura crítica del patrón de `partes` —qué se reutiliza y qué defectos
suyos NO se heredan— está en la sección **T8** de este informe.)*

### D-b · T19 queda N/A (2026-08-20)

**Qué cambia**: **T19**. La tarea pedía copiar la sección nueva de
`docs/INTEGRACION.md` a `azure-apps/postventa_incidencias.md`.

**Lo decidido**: el humano **no hace commits en `azure-apps`**. T19 no es una
tarea pendiente: es una tarea que **ya no aplica**. Se marca **N/A** en
`tasks.md` con esta decisión y su fecha escritas en la propia tarea.

**Lo que NO cambia**: **T15** sí se hace. `docs/INTEGRACION.md` vive en este
repositorio, es la fuente de verdad de lo que consumimos y R32 lo exige.

### D-c · Riesgo aceptado de permisos de Graph, documentado en `design.md` (2026-08-20)

**Verificado en Azure el 2026-08-20**: el app registration del proyecto tiene
consentimiento de administrador para **tres** permisos de aplicación de Graph:
`Sites.Selected` (el que pedía la spec), `Sites.ReadWrite.All` y
`Sites.FullControl.All`. Los dos últimos alcanzan a **todos** los sitios de
SharePoint del tenant y vuelven irrelevante al primero; `Sites.FullControl.All`
es más amplio incluso que `Files.ReadWrite.All`, que la propia spec descartó
por excesivo.

**Lo decidido**: arrancar F-006 con los permisos actuales y **recortar
después**, en **F-018 · Mínimo privilegio en Graph** (ya dada de alta en
`harness/features.json`, prioridad 18), para no mezclar un cambio de
configuración del tenant con una implementación. El recorte lo ejecuta el
humano en Azure: un agente no toca permisos del tenant.

**Dónde queda escrito**: sección nueva en `design.md` §9 (riesgo aceptado, con
fecha y citando a F-018) y en la sección de permisos de `docs/INTEGRACION.md`
(T15). **Ningún appId ni identificador** entra en ningún fichero del
repositorio.

### D-d · D6 está resuelta (2026-08-20)

`design.md` §10, **D6** —«nadie ha creado todavía la biblioteca de dev ni el
app registration»— era la única decisión abierta **bloqueante**, y bloqueaba
T17 y T18.

**Lo decidido/verificado**: la biblioteca, el app registration y los permisos
**ya existen**. Por tanto:

- **T17** deja de estar bloqueada y pasa a ser **ejecutable**: se prepara con
  su script y su comando exacto para que la ejecute el humano.
- **T18 sigue DIFERIDA a F-010** por la decisión **D3** del **2026-08-19**
  (opción (a)): no depende de D6 sino del entorno desplegado, que no existe
  hasta F-010. **No se toca.**

---

## Estado de las tareas

| Tarea | Estado |
|---|---|
| T1 · precondición (F-004 y F-005 en `dev`, rama rebasada) | ✅ hecha por el líder, verificada aquí |
| T2 · RED nombrado | ⏳ |
| T3 · `domain/models/nombrado.py` | ⏳ |
| T4 · RED paso de archivo + dobles | ⏳ |
| T5 · puerto + paso de archivo | ⏳ |
| T6 · RED fábrica | ⏳ |
| T7 · ajustes + fábrica | ⏳ |
| T8 · `httpx` en `requirements.txt` (D-a) | ⏳ |
| T9 · RED adaptador Graph | ⏳ |
| T10 · adaptador Graph | ⏳ |
| T11 · RED borde HTTP | ⏳ |
| T12 · borde HTTP | ⏳ |
| T13 · RED arquitectura (por rotura deliberada) | ⏳ |
| T14 · `docs/ARCHITECTURE.md` | ⏳ |
| T15 · `docs/INTEGRACION.md` | ⏳ |
| T16 · scripts de `infra/` | ⏳ |
| T17 · MANUAL (humano), ya ejecutable (D-d) | ⏳ |
| T18 · MANUAL (humano), DIFERIDA a F-010 (D3, 2026-08-19) | queda `[ ]` a propósito |
| T19 · N/A (D-b, 2026-08-20) | N/A |
| T20 · campaña de mutación | ⏳ |
| T21 · `bash harness/init.sh` en verde | ⏳ |

---

## T1 · Precondición: F-004 y F-005 en `dev`, rama al día

Hecha por el líder antes de lanzar esta implementación. **Verificada aquí**,
que es lo que pedía la tarea:

```
$ git log --oneline dev | head -8
f2e317b F-005: cierre documental y alta de F-018
7c57e52 F-005: persistencia en el PostgreSQL compartido (squash)
e3f5fcd Traer F-004 a la rama de F-005
62e91ed Merge F-004: validacion del parte y clasificacion de la firma
bb3ae58 F-004 CERRADA: revision APROBADA y cierre documental
...
```

Los cinco símbolos que F-006 consume de las dos features importan:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -c "from domain.models.validacion import Destino, Veredicto; from domain.models.persistencia import TrazaArchivo, EstadoArchivo; print('ok')"
ok
```

Y el arnés arranca en verde sobre la rama:

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
...
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-006 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-006-sharepoint
ENTORNO LISTO. Puedes trabajar.
```

**No** se ha inventado ningún modelo gemelo: `ResultadoValidacion`, `Destino`,
`TrazaArchivo`, `EstadoArchivo` y `RepositorioPartesPort.guardar_archivo` se
consumen tal cual los dejaron F-004 y F-005 (`design.md` §1).

---

## T2 · RED · Los tests del nombrado, antes que el nombrado

Fichero: `services/postventa-api/tests/test_f006_nombrado.py` (R1–R9).

**Traza real de la fase RED**, con el comando exacto:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f006_nombrado.py -q
=================================== ERRORS ====================================
________________ ERROR collecting tests/test_f006_nombrado.py _________________
ImportError while importing test module '...\tests\test_f006_nombrado.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f006_nombrado.py:30: in <module>
    from domain.models.errores import NombradoImposible
E   ImportError: cannot import name 'NombradoImposible' from 'domain.models.errores'
=========================== short test summary info ===========================
ERROR tests/test_f006_nombrado.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.31s
```

Rojo por lo que tenía que estar rojo: ni `NombradoImposible` ni
`domain/models/nombrado.py` existen todavía.

### Dos decisiones de los tests que conviene no perder

**1 · Las constantes se comprueban contra literales escritos a mano.** Ni
`GUIONES_EQUIVALENTES` ni `CARACTERES_PROHIBIDOS` se recorren para generar los
casos: los siete guiones y los nueve caracteres prohibidos están escritos uno
a uno en la parametrización. Un test que itera la constante que vigila da
verde aunque alguien la vacíe, y eso es exactamente el mutante que el nivel
`critico` no puede dejar vivo.

**2 · `nombre_admisible()` es público, y es una desviación menor de la spec.**
`design.md` §4.2 dejaba la comprobación de R7 dentro de `nombre_de_archivo`.
Ahí las tres ramas «empieza en espacio», «acaba en espacio» y «acaba en punto»
son **inalcanzables**: los códigos se recortan antes y el nombre siempre acaba
en `.pdf`. Una guardia inalcanzable no se puede probar —y en la campaña de
mutación aparece como superviviente, que en `critico` es un fallo—. Se saca a
una función pública, se prueba directamente con sus siete casos y
`nombre_de_archivo` la usa. Misma semántica, misma severidad; solo cambia
dónde se puede apuntar el test.

---

## T3 · VERDE · `domain/models/nombrado.py` + `NombradoImposible`

Ficheros: `services/postventa-api/domain/models/nombrado.py` (nuevo) y
`domain/models/errores.py` (se le añade `NombradoImposible`).

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_nombrado.py -q
71 passed in 0.10s

$ .venv/Scripts/python.exe -m pytest -q
753 passed, 10 skipped in 11.96s
```

Sin regresiones: la suite completa pasa de 682 a 753 tests.

**Decisiones de implementación:**

- `str.maketrans` con los siete guiones, en una sola pasada, en vez de siete
  `replace` encadenados.
- El orden de `nombre_de_archivo` es el de `design.md` §4.2: normalizar →
  barra a ` - ` → **volver a colapsar** espacios → componer → comprobar. El
  segundo colapso no es redundante: `RS26.08 / 0123` (barra con espacios)
  produciría espacios dobles sin él.
- `carpeta_de_archivo` recorta la base por los extremos y le quita la barra
  final: `Postventa/` y `Postventa` son la misma carpeta base, pero la
  primera produce `Postventa//0677`, que para Graph es otra ruta.
- `carpeta_de_archivo` **no** repite la comprobación de caracteres
  prohibidos. No hace falta y sobra: `componer_destino` compone siempre las
  dos cosas, así que un código de obra con `/` revienta igualmente en
  `nombre_de_archivo` **antes de que nadie llame al proveedor**. Duplicar la
  guardia habría dejado una rama que ningún test puede distinguir de la otra
  —y por tanto un mutante superviviente garantizado, que en `critico` es un
  fallo.

---

## T4 · RED · Los dobles y los tests del paso de archivo

Ficheros: `services/postventa-api/tests/utiles_sharepoint.py` (entregable) y
`services/postventa-api/tests/test_f006_paso_archivo.py` (R10–R18, R23, R24,
R27, más R6 en su vertiente «no sube nada»).

**Traza real de la fase RED**, con el comando exacto:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f006_paso_archivo.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f006_paso_archivo.py _______________
ImportError while importing test module '...\tests\test_f006_paso_archivo.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f006_paso_archivo.py:23: in <module>
    from application.pipelines.paso_archivo import (
E   ModuleNotFoundError: No module named 'application.pipelines.paso_archivo'
=========================== short test summary info ===========================
ERROR tests/test_f006_paso_archivo.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s
```

Rojo por lo que tenía que estar rojo: no existen ni `paso_archivo`, ni
`domain/ports/archivo.py`, ni los tres errores nuevos.

### `BibliotecaFalsa` y su control negativo

`design.md` §6.4 pedía un doble que **imitase** el comportamiento real en vez
de un mock al que preguntarle «¿te pedí `replace`?». Está implementado con los
tres comportamientos ante homónimo: `reemplazar` pisa y **conserva el
`item_id`**, `renombrar` crea `nombre (1).pdf` como haría el servicio de
verdad, y `fallar` levanta un conflicto.

Y se añade lo que la spec no pedía y sin lo cual el test estrella no probaría
nada: **el control negativo**
`test_f006_r15_la_biblioteca_falsa_si_renombraria_el_control_negativo`. Se
construye a propósito un adaptador mal hecho —el que renombra— y se comprueba
que **sí** aparece el `(1)`. Sin él,
`test_f006_r15_subir_dos_veces_deja_un_solo_elemento` podría estar en verde
porque el doble no sabe duplicar, no porque el paso lo evite.

### `test_f006_r15_nunca_se_pide_renombrar`, resuelto sobre la firma del puerto

El puerto no tiene ningún parámetro de comportamiento ante conflicto: la
decisión está cerrada dentro del adaptador. Así que el test afirma sobre la
**firma real de `ArchivoPort.subir`**: renombrar no es expresable desde la
aplicación, ni por error ni a propósito. Es más fuerte que comprobar que en
esta ejecución concreta no se pidió.

### Los dobles no traen ni un identificador con forma real

`drive-de-mentira`, `item-0001`, `https://ejemplo.invalido/...`. Ninguno tiene
forma de GUID **a propósito**: quien lea el repositorio no puede distinguir un
GUID inventado de uno real, así que aquí no entra ninguno de los dos.

---

## T5 · VERDE · El puerto, el paso y los dos errores

Ficheros nuevos: `domain/ports/archivo.py`,
`application/pipelines/paso_archivo.py`. Modificados:
`domain/models/errores.py` (`ParteNoApto`, `ArchivoFallido`),
`application/pipelines/contexto_parte.py` (`archivo: TrazaArchivo | None`).

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_paso_archivo.py -q
27 passed in 0.72s

$ .venv/Scripts/python.exe -m pytest -q
780 passed, 10 skipped in 19.35s
```

### Una guardia de F-003 saltó, y saltó por lo que tenía que saltar

Al añadir `archivo` a `ContextoParte` cayó
`test_f003_paso_extraccion.py::test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas`:

```
FAILED tests/test_f003_paso_extraccion.py::test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas
1 failed, 779 passed, 10 skipped in 19.82s
```

Ese test afirma la lista **exacta** de campos de `ContextoParte` y su propio
comentario dice para qué existe: «quien añada uno tiene que pasar por esta
línea». No es un test que se haya roto: es un test que ha hecho su trabajo.

Se ha **pasado por la línea**, no aflojado: `design.md` §3.2 de F-006 declara
expresamente este campo, y lo que se añade es la `TrazaArchivo` de F-005 —una
entidad de dominio que ya existe—, no una ruta de SharePoint en crudo ni un
identificador suelto, que es justo lo que la guardia sigue prohibiendo. La
aserción sigue siendo una igualdad exacta de conjuntos y el comentario se ha
actualizado para decir qué sigue vedado.

### Decisiones de implementación

- **El orden de `paso_archivo` es el de `design.md` §6.2**, y el orden es la
  mitad del requisito: aptitud → nombrado → idempotencia → carpeta → búsqueda
  → subida → traza. Un parte no apto no llega ni a nombrarse, y por eso no
  crea carpeta (R17).
- **`_ya_archivado` exige las dos condiciones**: mismo `hash` **y** estado
  `archivado`. La primera es R13 (una traza de otro parte no dice nada de
  este); la segunda es lo que hace verdad a R24 (`pendiente` y `error` dejan
  reintentar).
- **La traza se persiste en los dos caminos**, éxito y fallo, y en el de fallo
  la excepción se **re-lanza** después de guardar: el borde necesita el 502 y
  la base necesita la fila.
- **Un fallo al asegurar la carpeta también deja traza.** La spec solo hablaba
  del fallo al subir; si únicamente se registrara ese, un permiso mal dado
  sobre la biblioteca dejaría el parte sin traza ninguna —ni archivado, ni
  fallido, ni en ningún sitio—. Tiene su test.
- **`AVISO_REEMPLAZADO` sale solo cuando de verdad había un homónimo.** Un
  aviso que sale siempre es un aviso que nadie lee, y este significa que
  desapareció una versión anterior del parte conformado.
