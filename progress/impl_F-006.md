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

---

## T6 · RED · Los tests de las dos puertas que impiden subir desde local

Fichero: `services/postventa-api/tests/test_f006_fabrica.py` (R19, R20, R28).

**Traza real de la fase RED**, con el comando exacto:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f006_fabrica.py -q
=================================== ERRORS ====================================
_________________ ERROR collecting tests/test_f006_fabrica.py _________________
ImportError while importing test module '...\tests\test_f006_fabrica.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f006_fabrica.py:26: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'ArchivoDeshabilitado' from 'domain.models.errores'
=========================== short test summary info ===========================
ERROR tests/test_f006_fabrica.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.38s
```

Rojo por lo que tenía que estar rojo: no existen ni los dos errores nuevos, ni
`infrastructure/sharepoint/`.

**Este fichero es el único de la suite que nombra `AdaptadorSharePointGraph`**,
y lo nombra para comprobar que **se niega a construirse**. Que siga siendo el
único lo vigila `test_f006_r21_ningun_test_construye_el_adaptador_real` (T13).

---

## T7 · VERDE · Los ajustes, los ejemplos y la fábrica fail-closed

Ficheros nuevos: `infrastructure/sharepoint/__init__.py`,
`infrastructure/sharepoint/graph.py` (de momento, solo la puerta de entorno),
`infrastructure/sharepoint/fabrica.py`. Modificados: `config/settings.py`
(nueve ajustes de `design.md` §7), `domain/models/errores.py`
(`ArchivoDeshabilitado`, `ConfiguracionSharePointIncompleta`),
`.env.example` y `local.settings.json.example`.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_fabrica.py -q
24 passed in 0.31s

$ .venv/Scripts/python.exe -m pytest -q
804 passed, 10 skipped in 12.64s
```

`.env` **no se ha tocado** y `git status` no lo muestra, que era la otra mitad
de la verificación de la tarea.

### Las dos puertas dan motivos distintos, y el orden entre ellas importa

1. `exigir_entorno_con_archivo` — «aquí no se archiva». Va **la primera**. Si
   se comprobara antes la configuración, un puesto de trabajo con el `.env`
   completo recibiría el error equivocado y alguien podría creer que solo le
   falta rellenar una variable. Tiene su test.
2. `ARCHIVO_HABILITADO` — «no lo has encendido». Es una puerta distinta a
   propósito: en `dev` puede haber momentos en los que no se quiera archivar,
   y apagar el interruptor tiene que bastar sin tener que mentir sobre el
   entorno.

La lista `ENTORNOS_CON_ARCHIVO` vive en `graph.py` y la fábrica la importa de
ahí. Dos listas de entornos permitidos divergen, y la que se quedara corta
sería la que dejara subir desde donde no se debe.

### `SHAREPOINT_SITE_ID` es opcional, y es una decisión, no un olvido

`design.md` §7 lo declaraba junto a los demás. En la fábrica **no se exige**:
el adaptador va directo a la biblioteca por su identificador y no lo usa. Lo
usan el script de verificación de `infra/` (T16) y `docs/INTEGRACION.md`
(T15). Exigir configuración que nadie lee es una vuelta más de despliegue a
cambio de nada, y la variable sigue declarada y documentada.

Obligatorias, por tanto: `SHAREPOINT_DRIVE_ID`, `GRAPH_TENANT_ID`,
`GRAPH_CLIENT_ID` y `GRAPH_CLIENT_SECRET`, y se nombran **todas las que
falten de una vez**: descubrirlas de una en una son tres vueltas de
despliegue.

---

## T8 · `httpx` en `requirements.txt` — decisión D-a del humano (2026-08-20)

```
$ .venv/Scripts/python.exe -m pip install -r requirements.txt
$ .venv/Scripts/python.exe -c "import httpx; print('httpx', httpx.__version__)"
httpx 0.28.1

$ .venv/Scripts/python.exe -m pytest -q
804 passed, 10 skipped in 14.46s
```

Se declara `httpx>=0.27,<1.0`, con rango de versión al estilo de las demás
dependencias del fichero, y **no** se declaran `msal` ni `requests`, que era lo
que proponía la spec. Motivo: la decisión **D-a** del humano del 2026-08-20
(sección 0 de este informe), que cierra la decisión abierta **D1** de
`design.md` §10 alineando este servicio con `partes`, que ya resuelve lo mismo
en producción.

Coste de la decisión: **cero fuera de `infrastructure/sharepoint/`**, que es
exactamente lo que D1 predijo. El test de arquitectura de R22 ya vigilaba
`httpx` junto a `msal` y `requests`, así que tampoco cambia.

### Lo que se reutiliza del patrón de `partes`

Leídos `infrastructure/graph/token_provider.py` e
`infrastructure/storage/sharepoint_parte_storage.py` de
`partes/services/partes-persistencia`. Se adopta:

- **Token app-only pedido a mano** contra
  `login.microsoftonline.com/<tenant>/oauth2/v2.0/token` con
  `grant_type=client_credentials` y `scope=.../.default`, en vez de meter una
  librería entera para tres campos de un formulario.
- **Token cacheado por su vencimiento**, con un margen antes de que caduque.
- **`httpx.Client` con `httpx.Timeout(total, connect=...)`**.
- **La familia de códigos transitorios** (`429`, `5xx`) y la de excepciones de
  red de `httpx` (`ConnectTimeout`, `ConnectError`, `ReadTimeout`,
  `RemoteProtocolError`), que es la lista que a `partes` le ha costado
  descubrir en producción.
- **Respetar `Retry-After`** cuando el servicio lo manda.
- **La subida por `PUT .../root:/<ruta>:/content`**, que es la simple y vale
  para el PDF de un parte.

### Cinco defectos del patrón de `partes` que NO se heredan

Se dicen porque el encargo lo pedía explícitamente, y porque arrastrarlos
habría roto requisitos de esta feature:

1. **`_safe_filename` sanea en silencio.** `partes` sustituye por `_` todo
   carácter que SharePoint no admite. Eso es exactamente lo que **R7
   prohíbe**: archivaría en Posventa un fichero con un nombre que nadie pidió
   y nadie se enteraría. Aquí el nombre imposible es un error ruidoso.
2. **La subida no declara el comportamiento ante conflicto.** `partes` hace
   `PUT ...:/content` a secas y se queda con el valor por defecto del
   servicio. **R15 exige pedir el reemplazo explícitamente**: depender de un
   valor por defecto ajeno para el criterio de aceptación de la feature es
   confiar en que Microsoft no lo cambie.
3. **`raise_for_status()` y `response.text[:500]` filtran.** El mensaje de
   `httpx.HTTPStatusError` lleva la URL completa —con el identificador de la
   biblioteca dentro— y el cuerpo de la respuesta. Con **R26** eso no puede
   salir a un log. Aquí todo fallo se traduce a `ArchivoFallido` con un motivo
   que lleva **el código de estado y nada más**.
4. **`assert` para validar precondiciones.** `partes` usa `assert self._creds`
   y `assert self._hostname and self._site_path`. Con `python -O` los `assert`
   desaparecen y la comprobación con ellos. Aquí, comprobaciones de verdad.
5. **El backoff está escrito a mano** con `time.sleep` dentro del bucle.
   `docs/CONVENTIONS.md` de este proyecto manda `tenacity`, que ya está en el
   `requirements.txt` y es lo que usa `infrastructure/llm/gemini.py`. Un
   segundo mecanismo de reintentos en la misma casa diverge.

Ninguno de los cinco es un reproche a `partes`: son decisiones razonables en
un servicio con otros requisitos. Aquí hay requisitos escritos que las
descartan.

---

## T9 · RED · Los tests del adaptador de Graph

Ficheros: `services/postventa-api/tests/test_f006_adaptador_graph.py` (R11,
R12, R15, R16, R25, R26) y la parte de `ClienteGraphFalso` de
`tests/utiles_sharepoint.py`.

**Traza real de la fase RED**, con el comando exacto:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f006_adaptador_graph.py -q
=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f006_adaptador_graph.py _____________
ImportError while importing test module '...\tests\test_f006_adaptador_graph.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f006_adaptador_graph.py:36: in <module>
    from infrastructure.sharepoint.graph import (
E   ImportError: cannot import name 'CODIGOS_TRANSITORIOS' from 'infrastructure.sharepoint.graph'
=========================== short test summary info ===========================
ERROR tests/test_f006_adaptador_graph.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.29s
```

Rojo: de `graph.py` solo existe la puerta de entorno que puso T7; ni las tres
operaciones, ni los reintentos, ni las constantes.

### El guion del cliente falso **es** la aserción sobre el orden de llamadas

`ClienteGraphFalso` sirve las respuestas **en orden** y se cae diciéndolo si
el adaptador hace una llamada de más. Eso convierte cada guion en una
descripción exacta de la conversación esperada con Graph, en vez de un mock
permisivo que devuelve lo mismo se le pregunte lo que se le pregunte.

El doble **no ofrece `.text` ni `raise_for_status()`** a propósito: son las
dos vías por las que el patrón de `partes` filtraría la URL con el
identificador de la biblioteca y el cuerpo de la respuesta a un mensaje de
error (R26). Si alguien las usa, el doble lo parte con un `AttributeError` en
vez de dejarlo pasar.

### DESVIACIÓN de la spec, y por qué: la lista blanca de T13

`T13` dice que el barrido de `test_f006_r21_ningun_test_construye_el_adaptador_real`
debe autorizar **un solo** fichero, `test_f006_fabrica.py`. Pero **T9 manda
crear un fichero cuyo objeto es probar el adaptador**, y dice literalmente que
`ENTORNO=dev` en él «es lo que hace construible el adaptador». Las dos cosas no
pueden ser verdad a la vez: la lista blanca de T13 se escribió antes que el
fichero que T9 obliga a crear.

No es una ambigüedad sobre **qué debe hacer el sistema** —eso está claro—, sino
una inconsistencia entre dos tareas sobre qué nombres de fichero aparecen en
una lista. Se resuelve **sin debilitar nada**, y de hecho endureciéndolo:

- la lista blanca pasa a tener **dos** ficheros, `test_f006_fabrica.py` y
  `test_f006_adaptador_graph.py`;
- y se añade una comprobación que la spec no pedía: en
  `test_f006_adaptador_graph.py`, **toda** construcción del adaptador tiene que
  pasar `cliente=` —el doble—, verificado con `ast`. Así el invariante que de
  verdad importa deja de ser «qué fichero puede nombrar la clase» y pasa a ser
  «ninguna construcción del adaptador en la suite puede llegar a la red».

Queda anotado aquí para que el reviewer lo juzgue: es una desviación
consciente del texto de T13, no un descuido.

---

## T10 · VERDE · El adaptador de Graph

Fichero: `services/postventa-api/infrastructure/sharepoint/graph.py`.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_adaptador_graph.py -q
32 passed in 0.74s

$ .venv/Scripts/python.exe -m pytest -q
836 passed, 10 skipped in 15.16s
```

### Un test tuvo que corregirse, y el motivo importa

`test_f006_r16_buscar_devuelve_el_elemento_ante_un_200` afirmaba que el
`drive_id` del elemento devuelto era el de la **configuración**. El adaptador
usa el que responde Graph en `parentReference.driveId`, y cayó:

```
>       assert item.drive_id == DRIVE
E       AssertionError: assert 'drive-de-mentira' == 'drive-inventado'
```

El comportamiento del código es el correcto: la traza tiene que decir dónde
está el fichero **de verdad**, y quien manda sobre eso es el servicio, no
nuestro `.env`. Se corrigió el test —no el código— y se **añadió** uno nuevo,
`test_f006_r16_sin_parent_reference_se_usa_la_biblioteca_configurada`, para el
único caso en que la configuración sí manda: cuando Graph no lo dice. Los dos
dobles usan valores distintos a propósito, para que se vea cuál gana.

### Decisiones de implementación

- **La carpeta se asegura tramo a tramo.** `design.md` §8.1 describía un `GET`
  y un `POST`, pero crear `Postventa/0677` de una tacada contra una biblioteca
  donde `Postventa` aún no existe falla, y falla de una forma que parece un
  problema de permisos. Se recorre la ruta por segmentos.
- **Dos comportamientos ante conflicto distintos, y es a propósito**:
  `replace` al subir el fichero (R15) y `fail` al crear una carpeta.
  Reemplazar una carpeta que ya está borraría los partes que tuviera dentro; lo
  que se tolera ahí es el **código 409**, que es otra cosa (R12).
- **`_con_reintentos` centraliza qué es un error**, con una lista de códigos
  «tolerados» por operación: el `404` de `buscar` y el `409` de crear carpeta.
  Sin eso habría dos criterios de qué es un fallo en el mismo módulo.
- **`ErrorDeGraph` es interno y lleva solo el código.** No sale del módulo: lo
  que sale es `ArchivoFallido`. No lleva ni la URL —que contiene el
  identificador de la biblioteca— ni el cuerpo de la respuesta (R26).
- **El token se cachea** con 60 s de margen antes de su vencimiento. Pedirlo
  en cada operación son 66 peticiones a Entra por remesa de 22 partes.
- **`httpx.Client` se construye en la primera llamada**, no en el `__init__`,
  como en el adaptador de Gemini: el adaptador tiene que poder existir sin
  abrir nada.

---

## T11 · RED · Los tests del borde HTTP

Fichero: `services/postventa-api/tests/test_f006_archivar_http.py` (R30, R31).

**Traza real de la fase RED**, con el comando exacto:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f006_archivar_http.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f006_archivar_http.py ______________
ImportError while importing test module '...\tests\test_f006_archivar_http.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f006_archivar_http.py:36: in <module>
    from interface_adapters.api.archivar import archivar_parte
E   ModuleNotFoundError: No module named 'interface_adapters.api.archivar'
=========================== short test summary info ===========================
ERROR tests/test_f006_archivar_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.54s
```

### El test del 503 es el que más dice de toda la feature

`test_f006_r31_archivo_deshabilitado_responde_503` es **el único del fichero
que no inyecta dobles**: deja que el handler construya lo de verdad. Con
`ENTORNO=test` —lo que `conftest.py` fija para toda la suite— la fábrica se
niega y el borde responde 503.

Es, de paso, la demostración de que **el endpoint no puede archivar desde un
puesto de trabajo aunque alguien lo llame a mano**, que es el `acceptance` 4 de
la feature visto desde fuera.

En los seis caminos de error se comprueba además que la biblioteca falsa
**sigue vacía**: R31 dice «en los cuatro casos, sin haber subido nada», y eso
es lo que de verdad importa, no el número.

---

## T12 · VERDE · El handler y la ruta

Ficheros: `interface_adapters/api/archivar.py` (nuevo), `function_app.py`
(ruta `POST /api/archivar` y el mapeo de errores), `domain/models/errores.py`
(`CuerpoDeArchivoInvalido`).

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_archivar_http.py -q
12 passed in 1.03s

$ .venv/Scripts/python.exe -m pytest -q
848 passed, 10 skipped in 18.18s
```

### DESVIACIÓN menor: un error nuevo, `CuerpoDeArchivoInvalido`

`design.md` §3.2 enumera cinco errores nuevos y este no está. Hace falta
igual: R31 exige **400** cuando «el cuerpo no cumple el contrato», y eso
incluye un `veredicto` o un `destino` con un valor que el dominio no reconoce.

Las alternativas eran peores:

- **Reutilizar `CuerpoDeValidacionInvalido`** (F-004): su docstring dice
  literalmente «el cuerpo de `/api/validar`». Un error que miente sobre de
  dónde viene hace perder media hora a quien lea el log.
- **Tratar el valor desconocido como «no apto»**: daría un 409 engañoso.
- **Tratarlo como apto**: archivaría un parte que nadie ha validado. Ni de
  broma.

### El endpoint no pide los nueve campos del parte, y es a propósito

Solo `codigo_obra` y `numero_incidencia`, que son los que deciden el nombre.
Los otros siete se reconstruyen vacíos. Pedirlos obligaría al front a
reenviar el DNI y las observaciones manuscritas del cliente **en cada
archivo**, y ese es justo el dato que no debe viajar de más.

### El veredicto llega en el cuerpo y se vuelve a comprobar

Es la decisión **D4** de `design.md` §10, aplicada tal cual. Se reconstruye
como `ResultadoValidacion` y `paso_archivo` lo comprueba contra el destino
igual que si viniera de dentro: el borde no puede saltarse la puerta de
aptitud por el hecho de ser el borde.

---

## T13 · RED por rotura deliberada · Los tests de arquitectura

Fichero: `services/postventa-api/tests/test_f006_arquitectura.py` (R21, R22,
R26, R29, R32).

Aquí el entregable **es el test**, así que la fase RED no se demuestra
importando algo que no existe: se demuestra **rompiendo a propósito lo que los
tests vigilan** y enseñando que saltan. Y se hace **en una copia aislada del
árbol, nunca en el árbol real** (`CHECKPOINTS.md` C4 bis).

### Cómo se hizo la rotura

```
$ COPIA=<scratchpad>/rotura_f006
$ tar --exclude='.venv' --exclude='__pycache__' -cf - . | (cd "$COPIA" && tar -xf -)
```

Sobre esa copia, tres roturas:

1. `import httpx` metido en `domain/models/nombrado.py` — el dominio pasa a
   conocer el cliente HTTP (R22).
2. Una construcción de `AdaptadorSharePointGraph(...)` añadida a
   `tests/test_health.py`, que no está en la lista blanca (R21).
3. Un identificador con forma de GUID incrustado en `config/settings.py`
   (R26).

### La traza real de los cuatro fallos

```
$ cd "$COPIA"
$ .venv/Scripts/python.exe -m pytest tests/test_f006_arquitectura.py -q -p no:cacheprovider \
    -k "construye_el_adaptador or no_conocen_graph or solo_infrastructure or incrusta_un_identificador"

____________ test_f006_r21_ningun_test_construye_el_adaptador_real ____________
E       AssertionError: assert ['tests/test_health.py'] == []
E         Left contains one more item: 'tests/test_health.py'
_____________ test_f006_r22_dominio_y_aplicacion_no_conocen_graph _____________
E       AssertionError: assert {'domain/mode...y': ['httpx']} == {}
E         Left contains 1 more item:
E         {'domain/models/nombrado.py': ['httpx']}
_________ test_f006_r22_solo_infrastructure_sharepoint_importa_graph __________
E       AssertionError: assert ['domain/models/nombrado.py'] == []
E         Left contains one more item: 'domain/models/nombrado.py'
_____ test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador _____
E       AssertionError: assert {'config/sett...a2b3c4d5e6f']} == {}
E         Left contains 1 more item:
E         {'config/settings.py': ['xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx']}
                                  ^ el GUID que inyecté para la rotura iba aquí; se enmascara
                                    al pegarlo. Era inventado, pero quien lea este informe no
                                    puede distinguirlo de uno real, y esa es justo la regla
                                    que el test de R26 defiende.
=========================== short test summary info ===========================
4 failed, 13 deselected in 1.33s
```

Las tres roturas saltaron, y cada mensaje dice **qué fichero** las provocó, que
es lo que distingue un guardián útil de uno que solo dice «no». La copia se
borró después; `git status` confirma que el árbol real solo tiene el fichero
nuevo de esta tarea.

### Los dos tests de R32 quedan rojos a propósito

```
FAILED tests/test_f006_arquitectura.py::test_f006_r32_integracion_declara_el_consumo_de_sharepoint
FAILED tests/test_f006_arquitectura.py::test_f006_r32_integracion_dice_que_se_rompe_si_alguien_toca_el_destino
2 failed, 15 passed in 1.46s
```

Esa es su fase RED, y es de la buena: `docs/INTEGRACION.md` todavía no tiene la
sección de SharePoint porque la escribe **T15**. El test existe antes que el
documento que vigila, que es el orden correcto.

### Dos guardianes que se delataban a sí mismos

Al escribirlos, `test_f006_r21_ningun_test_construye_el_adaptador_real` y
`test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador` fallaron
**por culpa de este mismo fichero**: contenía el literal
`AdaptadorSharePointGraph(` en un docstring y los dos GUID de F-005 en su
lista de excepciones.

La salida fácil era meter el propio fichero en su lista de excepciones. **Un
guardián que necesita una excepción para sí mismo es un guardián con un
agujero del tamaño de un fichero**, así que se resolvió al revés:

- el nombre de la clase se **compone en memoria**
  (`"Adaptador" + "SharePoint" + "Graph"`), y el literal ya no está en el
  fichero;
- los GUID tolerados se declaran **por ruta y nunca por valor**, porque
  escribirlos para poder excluirlos sería meter en el repositorio justo lo que
  el barrido prohíbe. Lo que sí se acota es **cuántos** puede haber en cada
  fichero (exactamente uno), para que la excepción no se convierta en un
  desagüe.

---

## T15 · VERDE · La sección de SharePoint en `docs/INTEGRACION.md`

Fichero: `docs/INTEGRACION.md` (el que creó F-005; **no se crea otro**), más
`specs/F-006-sharepoint/design.md` con el riesgo aceptado de permisos.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_arquitectura.py tests/test_f005_integracion_sin_secretos.py -q
39 passed in 1.88s

$ .venv/Scripts/python.exe -m pytest -q
865 passed, 10 skipped in 18.94s
```

Los dos tests de R32 que T13 dejó rojos a propósito están **en verde**, y el
barrido de secretos que F-005 dejó puesto sigue pasando: ni un FQDN, ni un
GUID, ni una credencial han entrado en el documento.

### Qué se añadió, y por qué esas cosas y no otras

Sección **§3 · SharePoint: dónde se archivan los partes**, entre la base de
datos y las variables de entorno (las secciones 3–8 se renumeraron a 4–9 y las
referencias internas `§3` y `§4` se ajustaron con ellas). Contiene lo que T15
pedía: qué sitio y qué biblioteca **por nombre de variable**, con qué identidad
(app-only), con qué permisos, qué carpeta base, qué volumen se espera —una
remesa real son 22 partes— y **qué se rompe si alguien cambia la biblioteca o
revoca el permiso**, con cinco filas concretas.

La tabla de «qué se rompe» incluye un caso que no estaba en la spec y que es el
más traicionero de todos: **si alguien borra a mano un parte ya archivado, no
lo detectamos**. La traza sigue diciendo `archivado`, R14 corta el reintento y
reprocesar el parte no basta. Quien administre eso tiene que saberlo.

### El riesgo aceptado de permisos, escrito en dos sitios

Decisión **D-c** del humano del 2026-08-20 (sección 0 de este informe):

- **`specs/F-006-sharepoint/design.md` §9, «Riesgo 7 · ACEPTADO»**: qué se
  verificó en Azure, por qué importa —`Sites.FullControl.All` alcanza a todo el
  tenant y es más amplio que `Files.ReadWrite.All`, que **esta misma spec
  descartó por excesivo**—, qué decidió el humano y que la dueña del recorte es
  **F-018 · Mínimo privilegio en Graph**.
- **`docs/INTEGRACION.md` §3, «Permisos: qué necesitamos y qué tenemos hoy»**:
  lo mismo, en el documento que lee quien administra el tenant.

De paso se marcaron como resueltas en `design.md` §10 las decisiones abiertas
**D1** (`httpx`, 2026-08-20) y **D6** (la biblioteca y el app registration ya
existen, 2026-08-20), que era lo que bloqueaba T17.

**Ningún identificador entró en ningún fichero** —ni de aplicación, ni de
tenant, ni de sitio, ni de biblioteca—, ni siquiera para documentar el riesgo.

---

## T16 · VERDE · Los dos scripts de verificación manual

Ficheros: `infra/verificar_destino_sharepoint.ps1`,
`infra/verificar_archivo_dev.ps1` y `tests/test_f006_scripts_infra.py`.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f006_scripts_infra.py -q
20 passed in 0.07s

$ .venv/Scripts/python.exe -m pytest -q
885 passed, 10 skipped in 12.88s
```

Los dos van en **ASCII puro y CRLF sin BOM**, como los dos de F-005, y ninguno
lleva un valor dentro: todo sale de variables de entorno de la sesión de quien
los ejecuta.

### La verificación que pedía la tarea, ejecutada

```
$ powershell -ExecutionPolicy Bypass -File infra\verificar_destino_sharepoint.ps1 -WhatIf

verificar_destino_sharepoint.ps1 - solo lecturas, NO SUBE NADA
-------------------------------------------------------------
Variables que necesita en esta sesion (solo nombres):
  GRAPH_TENANT_ID          FALTA
  GRAPH_CLIENT_ID          FALTA
  GRAPH_CLIENT_SECRET      FALTA
  SHAREPOINT_SITE_ID       FALTA
  SHAREPOINT_DRIVE_ID      FALTA
  SHAREPOINT_CARPETA_BASE  sin definir; se usara 'Postventa'

El script NO imprime el token ni el secreto en ningun caso.
Para ejecutarlo de verdad, quita -WhatIf.

-WhatIf: no se ha llamado a nada.
```

Imprime la ayuda y **de cada variable si está puesta o no, jamás su valor**, y
no llama a nada. El de T18 hace lo mismo, y **sin `-BaseUrl` se niega**
explicando que contra un servicio local no funciona ni debe.

### El script de T17 no escribe, y eso es un test, no una promesa

`test_f006_t17_el_script_del_destino_no_escribe_nada` comprueba que **no hay
ni un `-Method Put`, `Patch` o `Delete`**, y que el **único** `-Method Post` de
todo el fichero es el del punto de token, porque Entra no da un token con un
`GET`. Un «ya que estamos, creo la carpeta» sería una escritura en el
SharePoint de Posventa lanzada desde un puesto de trabajo.

### Un extra útil: el script de T17 enseña los permisos de la aplicación

Decodifica el claim `roles` del token —sin validar firma; no está autenticando
a nadie, solo mirando qué trae— y lista los permisos concedidos. Con eso
resuelve `permiso_escritura: True/False` **sin escribir nada**, que era el
problema de fondo: no hay forma de comprobar permiso de escritura escribiendo
sin, precisamente, escribir.

Y de paso **avisa en amarillo** cuando aparecen los permisos amplios, citando
el riesgo aceptado del 2026-08-20 y a **F-018**. El humano lo va a ver cada vez
que lo ejecute, que es justo lo que se pretende: un riesgo aceptado que nadie
vuelve a ver es un riesgo olvidado.

### DESVIACIÓN anotada en el propio script de T18: `item_id` y el aviso

T18 esperaba comprobar «el mismo `item_id`» y «aviso de ya estaba archivado».
Ninguna de las dos cosas es observable desde el endpoint, y el script lo
explica en su cabecera para que quien ejecute T18 en F-010 no persiga un
fantasma:

- **`item_id` no está en la respuesta.** R30 fija **seis** claves y dice «y
  nada más»; `item_id` no es una de ellas. El equivalente observable es la
  `web_url`, que apunta al mismo elemento, y eso es lo que compara el script.
- **El aviso «ya estaba archivado» no va a salir.** Esa es la capa L1, y solo
  salta cuando quien llama **aporta la traza anterior**. El endpoint no la
  consulta: haría falta un método nuevo en `RepositorioPartesPort`, que es de
  **F-005**, y F-006 no cambia specs ajenas (misma razón que D4 y D5). Lo que
  garantiza que no haya duplicado por esta vía es la capa **L2, el reemplazo**,
  que es literalmente lo que pide el `acceptance` 3.

El script comprueba por tanto lo que el sistema **de verdad** garantiza: dos
llamadas con 200, mismo destino, y —si hay credenciales de Graph en la sesión—
un listado de la carpeta **en solo lectura** que confirma un solo elemento y
ningún nombre con `(1)`.

---

## T17 · PREPARADA para el humano · T18 · DIFERIDA · T19 · N/A

### T17 — lista para ejecutar, ya no bloqueada

**D6 está resuelta** (decisión D-d del 2026-08-20): la biblioteca de dev, el
app registration y los permisos ya existen, así que T17 deja de estar
bloqueada. Queda `[ ]` porque **la ejecuta el humano**, no un agente, y en
`tasks.md` está escrita con sus comandos exactos, partidos en dos pasos porque
PowerShell no admite `&&` y los comandos largos se parten al pegarlos:

```
$env:GRAPH_TENANT_ID     = "<tenant>"
$env:GRAPH_CLIENT_ID     = "<aplicacion>"
$env:GRAPH_CLIENT_SECRET = "<secreto>"
$env:SHAREPOINT_SITE_ID  = "<sitio>"
$env:SHAREPOINT_DRIVE_ID = "<biblioteca>"
```

```
copy infra\verificar_destino_sharepoint.ps1 $HOME\
```

```
powershell -ExecutionPolicy Bypass -File $HOME\verificar_destino_sharepoint.ps1
```

**Qué se espera ver**: el nombre del sitio y de la biblioteca, la lista de
permisos concedidos, y `biblioteca_localizada`, `carpeta_base_existe` y
`permiso_escritura: True`. **No sube nada.**

Y **se espera un aviso en amarillo** sobre los permisos amplios: es el riesgo
aceptado del 2026-08-20. Que salga es lo correcto; que **no** salga
significaría que F-018 ya se ejecutó.

El resultado se anota **sin identificadores**: solo sí/no por línea.

### T18 — no se ha tocado

Sigue **DIFERIDA a F-010** por la decisión **D3** del humano del 2026-08-19
(opción (a)). Su casilla queda `[ ]` **a propósito**: es una verificación
aplazada por una dependencia declarada, no una tarea olvidada. Su script se
entrega dentro de F-006 (T16); lo que se aplaza es ejecutarlo.

Esto es lo que obliga a que **el cierre de F-006 necesite autorización expresa
del humano ante `CHECKPOINTS.md` C5**, y es el caso que motiva **F-017**.

### T19 — N/A por decisión del humano del 2026-08-20

**El humano no hace commits en `azure-apps`.** T19 no es una tarea pendiente:
es una tarea que **ya no aplica**, y así queda escrito en la propia tarea con
su fecha. No se deja `[ ]` esperando a nadie ni se apunta como deuda.

Lo que **sí** se ha hecho y cubre el fondo del asunto es **T15**: la sección de
SharePoint está en `docs/INTEGRACION.md`, en este repositorio, que es la fuente
de verdad declarada. Lo que decae es **la copia** a otro repositorio, no la
obligación de documentarlo.

**Consecuencia que conviene no perder de vista, y por eso está escrita**:
mientras esa copia no exista, quien lea solo `azure-apps/` no se enterará de
que este proyecto es un inquilino nuevo del sitio de IT con permiso de
escritura. El material está listo para copiar y pegar el día que se quiera.

---

## T20 · Campaña de mutación: de 20 supervivientes a 5, y lo que destapó

> **Copia durable.** `progress/mutacion_F-006.md` lo **regenera** la siguiente
> campaña y se lleva por delante todo lo escrito a mano. Esto de aquí
> sobrevive.

```
$ python -m harness.mutacion --feature F-006
64 mutantes evaluados, 59 muertos, 5 supervivientes, 0 timeouts en 235.2 s
Informe: progress/mutacion_F-006.md
```

| Campaña | Mutantes | Muertos | Supervivientes | Timeouts |
|---|---|---|---|---|
| 1.ª | 68 | 48 | 20 | 0 |
| 2.ª | 64 | 58 | 6 | 0 |
| 3.ª (final) | 64 | **59** | **5** | 0 |

### Lo importante no es el número: es lo que encontró

La primera campaña destapó **tres huecos reales de test y dos de código**. Los
cinco estaban en verde y ninguno se habría visto leyendo el diff.

**1 · La puerta de aptitud se podía saltar.** El mutante cambiaba el `or` de
`veredicto != APTO or destino != ARCHIVO_Y_CIERRE` por un `and`, y **no rompía
ni un test**. Motivo: todos mis casos no aptos fallaban **las dos** condiciones
a la vez, así que el `and` seguía levantando `ParteNoApto`. Con el `and`, un
parte con `veredicto=apto` y destino `cola_validacion_humana` **se habría
archivado**, que es exactamente lo que prohíbe `CHECKPOINTS.md` C3. Y no es
teoría: es lo que llega si alguien compone a mano el cuerpo de
`POST /api/archivar`. Dos tests nuevos, uno por mitad.

**2 · La caché del token miraba si existía, no si valía.** Dos mutantes
—`and`→`or` en la condición, y el signo del margen— sobrevivían, y los dos
producen lo mismo: **seguir usando un token vencido**. En producción eso es un
`401`, que además **no se reintenta** (R25), así que el parte no se archiva.
Dos tests nuevos: uno con un token que nace caducado y otro con uno vigente,
porque sin el segundo el primero se «arregla» pidiendo el token siempre.

**3 · `con_token` era un parámetro muerto.** Se declaraba en `_con_reintentos`,
se pasaba en la llamada del token… y no se usaba en ninguna parte. Por eso
sobrevivían sus dos mutantes: **no hay test que pueda matar código que no
hace nada**. Eliminado.

**4 · `timeout_s` y `reintentos` tenían valor por defecto que nadie usaba.** La
fábrica es el único sitio que construye el adaptador y los pasa **siempre**
desde `config/settings.py`. Un valor por defecto que nadie usa es una segunda
fuente de verdad esperando a divergir. Ahora son obligatorios.

**5 · El log registraba la duración y nadie comprobaba que fuera una resta.**
`time.monotonic() - arranque` → `+` sobrevivía. La diferencia no es cosmética:
`monotonic()` cuenta desde el arranque de la máquina, así que la suma da un
número de siete cifras que nadie leería como un error, solo como «esto va
lentísimo». Test nuevo: la duración registrada está entre 0 y 60.

Y una lección de método que ya había aparecido en T2 y T13, y que volvió a
morder: **un test que se compara contra la constante que vigila sigue al
mutante**. `assert cliente.timeout.connect == TIMEOUT_DE_CONEXION_S` daba verde
con la constante mutada. El `30` va literal.

### Los cinco supervivientes, con su análisis

Ninguno queda `PENDIENTE`. El detalle completo está en
`progress/mutacion_F-006.md`; el resumen, aquí:

| # | Qué es | Veredicto | Por qué |
|---|---|---|---|
| 1 | `GRAPH_TIMEOUT_S` por defecto (60→61) | **Equivalente justificado** | Constante de operación. El requisito es una propiedad —que quepa en los 230 s de la Function—, no el número. Un `assert == 60` sería un detector de cambios |
| 2 | `GRAPH_REINTENTOS` por defecto (3→4) | **Equivalente justificado** | **Qué** se reintenta sí está cubierto a fondo (los seis códigos uno a uno, y que un `403` da **una** llamada). Esto solo toca el valor por omisión, que ningún test consume |
| 3 | `MARGEN_DE_TOKEN_S` (60→61) | **Equivalente justificado** | Cazarlo exige un `expires_in` justo en la frontera, y el test pasaría a depender de que entre dos llamadas en memoria pase menos de **un segundo de reloj real**. Un test que falla a veces es peor que no tenerlo |
| 4 | `<` → `<=` sobre `time.monotonic()` | **Equivalente estricto** | Solo difieren si dos flotantes de nanosegundos coinciden bit a bit. No hay entrada que lo distinga: es la definición de mutante equivalente |
| 5 | `expires_in` de reserva (3599→3600) | **Equivalente justificado** | Exige **una hora de reloj real**, y solo si Entra incumple su contrato y omite el campo |

**Ninguno de los cinco toca lo que T20 pedía mirar con lupa**: ni el nombrado
—separadores, sufijo, orden de las sustituciones—, ni la puerta de entorno, ni
la idempotencia. Ahí no sobrevive nada.

> El nivel `critico` pide **cero supervivientes o cada uno con su análisis
> aceptado por el humano**. Quedan cinco, los cinco analizados y los cinco de
> la segunda clase. **Esa aceptación es del humano, no mía.**

---

## T21 · `bash harness/init.sh` en verde

Ejecutado tal cual, sin pipes ni decoración:

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)
895 passed, 10 skipped in 33.20s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 98.2% de 342 líneas cambiadas cubiertas (336/342, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-006-sharepoint
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
EXIT CODE: 0
```

**Sobre los avisos de ruff.** Al empezar F-006 había 53 y ahora hay 56. Los que
eran **míos** están corregidos (un import sobrante, dos `pytest.raises(Exception)`
que ahora esperan `FrozenInstanceError` —más estricto, no menos— y dos `noqa`
justificados). Lo que queda es **`I001`, orden de imports**, que dispara en
**todos** los ficheros del servicio, también en los de F-002 a F-005: la
convención de este proyecto —`config`/`domain` antes que `application`/
`infrastructure`— no coincide con la de `isort`. Reordenar solo los míos los
dejaría inconsistentes con los otros 55; reordenarlos todos es un cambio de
repositorio que no toca a esta feature. Se deja anotado como deuda.

---

## Post-review · El barrido de identificadores pasa a cubrir todo el árbol (H1)

Cambio pedido por la review (`progress/review_F-006.md`, **cambio requerido 2**),
hecho después del veredicto `CHANGES_REQUESTED`. **No toca ni una línea de
código de producción**: es un guardián de tests nuevo,
`services/postventa-api/tests/test_f006_repo_sin_identificadores.py`.

### Por qué el barrido anterior no bastaba, que es la lección que hay que llevarse

`test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador` recorre
`_ficheros_del_servicio()`, es decir, `services/postventa-api/` y nada más. Y
mientras tanto el appId **real** del app registration estuvo escrito en
`progress/current.md` desde el commit `f2e317b` —que ya había llegado a `dev`—
hasta que **lo encontró una persona leyendo, no un test**.

La conclusión fácil sería «faltaba un directorio». No es eso. Es que **el
guardián vigilaba justo el sitio donde los identificadores no se escriben**.
Nadie pega el GUID de un sitio de SharePoint dentro de un adaptador: el
adaptador lee su configuración del entorno, y eso ya lo defendía R29. El valor
real lo escribe **un agente en su informe**, al anotar lo que acaba de
verificar en el portal de Azure — que es literalmente el epígrafe bajo el que
apareció: «Lo verificado en Azure el 2026-08-20». `progress/` es el directorio
del repositorio con **más** probabilidad de llevar un valor de verdad, y era
exactamente el que nadie miraba.

Dicho como regla para F-007 en adelante: **un barrido de secretos que se acota
al código de producción está mirando el sitio equivocado.** El código se
escribe con la cabeza puesta en que lo va a leer alguien; los informes se
escriben con la cabeza puesta en no perder lo que uno acaba de averiguar.

### Qué se ha hecho

Un fichero hermano en vez de ampliar el existente, por el mismo criterio con el
que F-005 separó `test_f005_repo_sin_datos_personales.py` de
`test_f005_arquitectura.py`: el barrido del árbol entero no es una invariante
de arquitectura del servicio, y cuando falle conviene que el nombre del fichero
ya diga de qué se trata. El patrón `PATRON_GUID` **se importa** del fichero de
arquitectura en vez de copiarse: dos regex separadas divergen, y el día que
divergen solo una de las dos caza el caso que importa.

**El alcance es todo el árbol, no una lista de directorios.** La review pedía
`progress/`, `docs/`, `infra/` y la raíz; se barre además `specs/`, `harness/`,
`scripts/`, `.claude/` y el propio `services/`. Motivo: una lista de cuatro
directorios se queda vieja el día que alguien añade el quinto, y `specs/` —donde
se documenta el diseño— es tan buen sitio para pegar un GUID «para que se
entienda» como `progress/`. Medido: **225 ficheros** barridos (141 de
`services/`, 27 de `progress/`, 16 de `harness/`, 16 de `specs/`, 6 de `docs/`,
5 de `.claude/`, 4 de `infra/`, 4 de `tests/`, 2 de `scripts/` y 4 de la raíz).

Tres decisiones de diseño, con su motivo:

1. **El fallo dice la ruta y el recuento, nunca el valor.** Un guardián de
   secretos cuya traza imprime el secreto lo copia al log de CI, al chat y al
   informe de quien lo diagnostique. Se informa `{ruta: nº}`, que es lo que
   hace falta para ir a arreglarlo. Esto también resuelve el problema que
   creó **H2**: la traza de esta fase RED se puede pegar aquí entera **sin
   enmascarar nada**, porque no contiene ningún valor.
2. **Se tolera por ruta y por número, jamás por valor.** Escribir en el test
   los GUID a excluir sería meter en el repositorio justo lo que prohíbe.
   Acotar el número obliga a que ampliar la tolerancia sea un cambio visible.
3. **Lo que no está versionado no se barre.** `.venv/`, `.idea/`, `muestras/`,
   `originales/`, las cachés, los worktrees de los subagentes, y por nombre
   `.env`, `local.settings.json` y `coverage.json`. En esos ficheros un
   identificador real es **lo normal y lo correcto**: son la configuración de
   la máquina de quien trabaja. Un barrido que fallara en cuanto alguien
   rellena su `.env` estaría desactivado en tres semanas, y volveríamos al
   punto de partida de H1.

### Fase RED · Rigor `critico`, con las tres trazas reales

Se inyectó a mano un fichero `progress/_caso_hostil_red.md` con un appId
**inventado** con forma de GUID, reproduciendo el caso exacto de H1. El fichero
es temporal, se borró al terminar y **nunca entró en ningún commit**
(`git status` lo dio solo como `??`).

**Paso 1 · El hueco, reproducido.** Con el GUID sentado en `progress/`, el
guardián que había estaba verde:

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f006_arquitectura.py -k "r26" -v
collected 17 items / 14 deselected / 3 selected

tests/test_f006_arquitectura.py::test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador PASSED [ 33%]
tests/test_f006_arquitectura.py::test_f006_r26_la_excepcion_de_f005_no_crece_sin_que_se_vea PASSED [ 66%]
tests/test_f006_arquitectura.py::test_f006_r26_el_barrido_de_guids_caza_uno_inyectado PASSED [100%]

====================== 3 passed, 14 deselected in 0.53s =======================
```

Y no era solo ese bloque: **la suite entera** del servicio pasaba con el
identificador dentro del árbol.

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q
895 passed, 10 skipped in 13.13s
```

Ahí está el fallo, medido y no argumentado: 895 tests en verde y un appId con
pinta de real en el repositorio.

**Paso 2 · El guardián nuevo, en rojo.** Con el mismo fichero hostil en su
sitio y el fichero nuevo ya escrito:

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f006_repo_sin_identificadores.py -v

================================== FAILURES ===================================
___ test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador ____

    def test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador():
>       assert _hallazgos() == {}
E       AssertionError: assert {'progress/_c...il_red.md': 1} == {}
E
E         Left contains 1 more item:
E         {'progress/_caso_hostil_red.md': 1}
E
E         Full diff:
E         - {}
E         + {
E         +     'progress/_caso_hostil_red.md': 1,
E         + }

tests\test_f006_repo_sin_identificadores.py:236: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f006_repo_sin_identificadores.py::test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador
======================== 1 failed, 28 passed in 1.39s =========================
```

Nótese que la traza dice **la ruta y que hay uno**, y no dice cuál. Era el
objetivo de la decisión de diseño 1, y aquí queda demostrado con la salida real.

**Paso 3 · Verde al retirar el caso.** Borrado `progress/_caso_hostil_red.md`,
sin tocar nada más:

```
$ rm progress/_caso_hostil_red.md
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f006_repo_sin_identificadores.py -q
29 passed in 1.36s
```

### El control positivo, que es lo que mantiene vivo al guardián

Un barrido que grita con texto legítimo no dura: alguien lo comenta un viernes
y volvemos a no tener nada. Los 29 tests del fichero incluyen **18
comprobaciones de que el barrido NO muerde**:

- **13 frases** sacadas de `progress/`, de `docs/` y de la salida del arnés que
  hablan de identificadores **sin serlo**: «su appId no se escribe aquí: se
  consulta con `az ad app list`», los tres permisos `Sites.*`, los nombres de
  las nueve variables de entorno, la frase «ni un identificador con forma de
  GUID», el «(enmascarado por el líder)» del líder, la traza enmascarada
  `b7e41c92-…` de H2, los placeholders de los `.example`, los SHA de commit
  (`f2e317b`, `a2c2bae`), un hash de 32 hexadecimales, la línea de
  `PUERTA COBERTURA`, los `item-0001` / `drive-de-mentira` /
  `https://ejemplo.invalido/...` de los dobles, y la cabecera de versión del
  arnés. Cuatro más fijan el **borde por abajo**: a cada grupo del patrón le
  falta un carácter, o lleva una letra que no es hexadecimal.
- **Un test de ficheros no versionados**: `.venv/`, `.idea/`, `muestras/`,
  `__pycache__/`, `local.settings.json` y `coverage.json` con un GUID dentro, y
  el barrido devuelve vacío. Es el que impide el falso positivo que de verdad
  iba a pasar: `services/postventa-api/local.settings.json` está hoy vacío,
  pero el día que alguien lo rellene con el site id de dev estará haciendo
  exactamente lo que debe.
- **Dos guardas del propio barrido**: uno exige que recorra ≥ 60 ficheros con
  `.md`, `.py` y `.ps1` entre ellos (un barrido que no lee nada está verde por
  no trabajar), y otro exige por nombre que `progress/current.md`,
  `progress/impl_F-006.md`, `docs/INTEGRACION.md`,
  `specs/F-006-sharepoint/design.md`, `CLAUDE.md` e `infra/` estén dentro. Ese
  segundo es el que fija el punto ciego de H1 y no deja que vuelva a abrirse.

Y siete controles negativos: el caso de H1 sobre un árbol de mentira en
`tmp_path`, cinco rincones distintos del árbol (`docs/`, `infra/`, `specs/`, la
raíz y `harness/`, con el GUID **en mayúsculas**, que es como se copia del
portal de Azure), y uno que comprueba que tres GUID en un fichero se cuentan
como tres y no como uno —importa, porque la tolerancia se expresa en número—.

Todos los valores con forma de GUID de este fichero se **componen en memoria**
con `guid_compuesto(...)` y viven solo en `tmp_path`: el repositorio no gana ni
una cadena con forma de identificador. Es la misma técnica que F-005 usó con
los DNI y la que evitó que este propio guardián se delatara a sí mismo.

### Qué apareció al ampliar el barrido

**Ningún identificador real.** El árbol ya estaba limpio: el líder había
retirado el appId de `progress/current.md` en `a2c2bae` antes de que yo
empezara. Aparecieron **tres** ficheros con un GUID cada uno, los tres
justificados y declarados en `GUID_TOLERADO_POR_FICHERO`:

| Fichero | Qué es | Por qué se tolera |
|---|---|---|
| `tests/test_f005_integracion_sin_secretos.py` | Control negativo de F-005 | Valor inventado; ya lo acotaba `test_f006_r26_la_excepcion_de_f005_no_crece_sin_que_se_vea` |
| `tests/test_f005_repo_sin_datos_personales.py` | Control negativo de F-005 | Ídem |
| `progress/review_F-006.md` | El reviewer cita el GUID todo a ceros al explicar cuáles son esos dos controles | Es un valor nulo por construcción, no identifica nada, y está en **un informe entregado**: enmascararlo a posteriori alteraría la evidencia de una review |

Se toleran **por ruta y con recuento exacto**, nunca por valor, y
`test_f006_r26_la_tolerancia_del_barrido_no_crece_sin_que_se_vea` fija que son
tres y con uno cada uno. Ampliar la lista obliga a tocar el test y a explicarlo
en la revisión, que es justo lo que se quiere que cueste.

### Una observación que dejo abierta, no tapada

El barrido **antiguo** —el del servicio— sí incluye
`services/postventa-api/local.settings.json`, que `.gitignore` deja fuera de
git y que legítimamente llevará identificadores reales en cuanto alguien
configure su entorno local. Hoy está vacío y por eso nadie lo ha notado, pero
es un falso positivo esperando. No lo he tocado porque la review dio los tests
de F-006 por buenos y cambiar su alcance pide su propia justificación; el
guardián nuevo sí lo excluye y tiene test que lo demuestra. **Lo dejo escrito
aquí para que quien toque `test_f006_arquitectura.py` lo arregle de paso.**

### Campaña de mutación, relanzada

Se toca código de test en una feature `critico`, así que la campaña se repitió
entera. Se lanzó con `--workers 1` a propósito: la campaña paralela crea sus
worktrees desde `HEAD` y habría evaluado un árbol **sin** el fichero nuevo, que
es precisamente lo que había que verificar —el propio arnés avisa de ello y se
niega a lanzarse en paralelo con el árbol sucio—.

```
$ python -m harness.mutacion --feature F-006 --workers 1
F-006: 11 fichero(s), 1619 línea(s) de producción (origen rama, f2e317b2af433fee592a08f2a3cf7e3a145d35f4..feature/F-006-sharepoint)
...
64 mutantes evaluados, 59 muertos, 5 supervivientes, 0 timeouts en 905.7 s
Informe: progress/mutacion_F-006.md
```

**Mismo resultado y los mismos cinco supervivientes** (`settings.py:285` y
`:293`, `graph.py:112`, `:362` y `:380`): ni uno nuevo que matar o analizar. Era
lo esperable, porque el fichero nuevo no toca producción y `harness/alcance.py`
excluye `tests/` del alcance por diseño — pero **esperable no es comprobado**, y
el nivel `critico` no admite dar por buena una campaña anterior al cambio.

Un efecto secundario que conviene saber: **al regenerarse,
`progress/mutacion_F-006.md` perdió su sección final «Veredicto de la campaña»**.
El arnés arrastra solo los análisis por mutante, no lo escrito a mano al final
—cosa que el propio informe anterior ya avisaba—. Se ha restaurado a mano desde
la copia durable, con la fila de esta quinta campaña añadida a la tabla.

### El portero, en verde

```
$ bash harness/init.sh
[OK] pytest en verde (con medición de cobertura)
16 passed in 0.37s
924 passed, 10 skipped in 21.85s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 98.2% de 342 líneas cambiadas cubiertas (336/342, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-006-sharepoint
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
EXIT=0
```

895 → **924 tests**. La cobertura de líneas cambiadas no se mueve (98,2 %):
el cambio es todo código de test, y `harness/alcance.py` no lo cuenta. `ruff`
sobre el fichero nuevo: `All checks passed!`, así que los avisos de deuda previa
siguen en 56 y no en 59.

---

## Ficheros tocados

### Nuevos

| Ruta | Qué es |
|---|---|
| `services/postventa-api/domain/models/nombrado.py` | El nombrado, dominio puro |
| `services/postventa-api/domain/ports/archivo.py` | `ArchivoPort` e `ItemArchivado` |
| `services/postventa-api/application/pipelines/paso_archivo.py` | El paso que decide |
| `services/postventa-api/infrastructure/sharepoint/__init__.py` | El paquete |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | El adaptador de Graph |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | La fábrica fail-closed |
| `services/postventa-api/interface_adapters/api/archivar.py` | El handler HTTP |
| `infra/verificar_destino_sharepoint.ps1` | T17, solo lecturas |
| `infra/verificar_archivo_dev.ps1` | T18, contra el servicio desplegado |
| `services/postventa-api/tests/utiles_sharepoint.py` | `BibliotecaFalsa` y los demás dobles |
| `tests/test_f006_nombrado.py` · `_paso_archivo.py` · `_fabrica.py` · `_adaptador_graph.py` · `_archivar_http.py` · `_arquitectura.py` · `_scripts_infra.py` | Las siete suites |
| `tests/test_f006_repo_sin_identificadores.py` | **Post-review (H1)**: el barrido de GUID sobre todo el árbol |

### Modificados

| Ruta | Qué cambia |
|---|---|
| `config/settings.py` | Nueve ajustes de destino y credencial |
| `domain/models/errores.py` | Seis errores nuevos |
| `application/pipelines/contexto_parte.py` | `archivo: TrazaArchivo \| None` |
| `function_app.py` | Ruta `POST /api/archivar` y el mapeo 400/409/502/503 |
| `requirements.txt` | `httpx>=0.27,<1.0` |
| `.env.example`, `local.settings.json.example` | Placeholders, sin un solo valor |
| `docs/ARCHITECTURE.md` | Pasos 5 y 6, y la fila de SharePoint |
| `docs/INTEGRACION.md` | Sección §3 nueva |
| `specs/F-006-sharepoint/design.md` | Riesgo 7 aceptado; D1 y D6 resueltas |
| `specs/F-006-sharepoint/tasks.md` | Tareas marcadas; T8 y T19 rectificadas |
| `tests/test_f003_paso_extraccion.py` | La guardia de campos de `ContextoParte` |

**No se ha tocado**: `tests/conftest.py` (la guardia de red de F-003, intacta),
`harness/*`, los modelos de F-004 y F-005, `muestras/` ni `.env`.

---

## Verificaciones MANUAL (humano) pendientes

| Tarea | Estado | Quién y cuándo |
|---|---|---|
| **T17** | **Lista para ejecutar.** D6 resuelta el 2026-08-20 | El humano, con el comando exacto que hay en `tasks.md` |
| **T18** | **DIFERIDA a F-010** (D3, 2026-08-19). Su script se entrega aquí | Quien trabaje F-010 |
| **T19** | **N/A** (decisión del humano, 2026-08-20) | Nadie: ya no aplica |

---

## Lo que queda fuera del alcance, y de quién es

| Qué | De quién |
|---|---|
| Recortar los permisos de Graph al mínimo privilegio | **F-018** (riesgo aceptado, documentado) |
| Ejecutar la subida real contra la biblioteca de dev | **F-010** (T18) |
| Enseñar el resultado y dejar reintentar a una persona | F-007 |
| Mudar el archivo a la biblioteca de Posventa | F-013 (sale casi gratis: es configuración) |
| Cerrar la incidencia en Sigrid y subir el PDF al ERP | F-008 / F-009 / F-012 |
| Reagrupar el parte de dos hojas | F-014 |

---

## Evidencias

Números **medidos**, no estimados, todos de las ejecuciones pegadas arriba.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados y resultado** | **924 pasan, 10 se saltan, 0 fallan** | `pytest -q` del servicio, dentro de `bash harness/init.sh` |
| **Tests añadidos por F-006** | **+242** (682 al empezar → 924) | Diferencia contra el estado inicial de la rama |
| **De ellos, del arreglo post-review de H1** | **+29** (895 → 924) | El fichero `test_f006_repo_sin_identificadores.py` |
| **Cobertura de las líneas cambiadas** | **98,2 % · 336 de 342 líneas** (umbral 80 %, nivel `critico`) | Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / evaluados** | **64 / 64** (campaña completa, sin muestreo) | `python -m harness.mutacion --feature F-006 --workers 1` |
| **Mutantes muertos** | **59** | Ídem |
| **Mutantes supervivientes** | **5**, los cinco analizados y ninguno `PENDIENTE`. **Los mismos cinco** que antes del arreglo: ni uno nuevo | `progress/mutacion_F-006.md` |
| **Timeouts de la campaña** | **0** | Ídem |
| **Tiempo de la campaña** | **905,7 s** (con un solo worker; la paralela tardaba 247,0 s) | Ídem |
| **Tiempo de ejecución de la suite** | **23,34 s** (la del servicio, dentro de `init.sh`) | Salida de la propia suite |
| **Ficheros barridos por el guardián de identificadores** | **225** de todo el árbol; **0** hallazgos, 3 tolerados y declarados | `test_f006_repo_sin_identificadores.py` |
| **`bash harness/init.sh`** | **Exit code 0** | Ejecutado tal cual |

**Las siete fases RED están documentadas con su traza real en rojo** en este
informe: T2, T4, T6, T9, T11 (rojo por código inexistente), T13 (rojo por
rotura deliberada en una copia aislada del árbol, con las tres roturas y sus
cuatro fallos pegados) y la del **post-review de H1** (rojo por caso hostil
inyectado en `progress/`, con las tres trazas: hueco reproducido, guardián
nuevo en rojo, verde al retirar el caso).

*(La versión anterior de este informe decía «las diez fases RED» y enumeraba
seis. Era un error de redacción, señalado por la review; corregido aquí, y
ahora son siete de verdad.)*

---

## Lo que hay que saber antes de aprobar esto

**Estado tras la review.** De los cuatro cambios requeridos, el **2** —tapar el
hueco del barrido que dejó pasar H1— queda cerrado aquí, con su fase RED y la
campaña relanzada. El **1** (quitar el appId de `progress/current.md`) y el
**4** (limpiar la sesión anterior de `current.md`) los hizo el líder. El **3**
son **dos firmas del humano** y sigue abierto: es lo que hay debajo.

Y una consecuencia de H1 que **no** se arregla con un test: el appId real
estuvo en `f2e317b`, que ya está en `dev`. Quitarlo del árbol no lo saca del
historial de git. Esa decisión —rotar algo, reescribir historial, o aceptarlo—
es del humano.

Tres cosas, dichas sin adornos:

1. **T18 queda sin ejecutar**, y el rigor `critico` exige verificaciones
   manuales con resultado real. Es la opción (a) de **D3**, decidida por el
   humano el 2026-08-19, y `CHECKPOINTS.md` **C5** pide todas las tareas `[x]`.
   **Ese cierre lo autoriza el humano, no el arnés.** Sin esa autorización por
   escrito, el veredicto correcto del reviewer es `CHANGES_REQUESTED`. Es el
   caso que motiva **F-017**.
2. **Quedan 5 mutantes supervivientes.** Están analizados uno a uno y los cinco
   son equivalentes o constantes de operación, pero el nivel `critico` pide que
   **el humano acepte** ese análisis.
3. **La aplicación tiene hoy más permisos de Graph de los que necesita**, y
   puede escribir en cualquier sitio de SharePoint del inquilino. Es un riesgo
   **aceptado y fechado** (2026-08-20), documentado en `design.md` §9 y en
   `docs/INTEGRACION.md` §3, y lo recorta **F-018**. F-006 no lo usa: va a una
   sola biblioteca y nunca enumera sitios.

Y tres desviaciones de la spec, todas anotadas en su tarea: `httpx` en vez de
`msal`+`requests` (T8, decisión del humano), la lista blanca de T13 con **dos**
ficheros en vez de uno —endurecida con una comprobación que la spec no pedía—,
y `CuerpoDeArchivoInvalido`, un error que `design.md` no enumeraba y que R31
necesita.
