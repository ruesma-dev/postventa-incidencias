<!-- progress/impl_defectos13-15_F-010.md -->
# F-010 · Defectos 13, 14 y 15 · informe incremental

- **Rama:** `feature/F-010-despliegue`
- **Fecha:** 2026-08-25 (tarde)
- **Origen:** los tres los descubrió el humano **ejecutando T17 y T18 contra el
  entorno real** ese mismo día. Son los defectos **13, 14 y 15**; los doce
  anteriores están en `progress/impl_F-010.md`.
- **Nivel de rigor:** `estandar` (`harness/features.json`). Puertas exigibles:
  fase RED en los requisitos centrales, `PUERTA COBERTURA` en `[OK]`, campaña
  de mutación con **todos** los supervivientes analizados, y la sección
  «Evidencias» del final.
- **Cero llamadas a Azure, a SharePoint y a PostgreSQL.** Ni un GUID, ni una
  URL de dev, ni un identificador de suscripción o inquilino entra al
  repositorio. **Ninguna casilla `[x]` de `tasks.md` movida.**

## Resumen en una pantalla

| # | Qué era | Qué se ha hecho | Dónde |
|---|---|---|---|
| **13** | El verificador de T18 y los enunciados de T14/T18 llaman al **host desnudo** de la Function, que desde el enlace con la Static Web App responde `400` a todo | El script reconoce **ese** `400` y explica cuál es la vía buena; `verificar_despliegue.ps1` también; la vía que sí funciona queda escrita en el runbook; rectificados los enunciados de T14 (criterios 1 y 3) y T18 | `infra/`, `docs/DESPLIEGUE.md`, `specs/F-010-despliegue/tasks.md` |
| **14** | `PersistenciaNoDisponible` se escapaba del borde: **500 con el cuerpo vacío** | Traducida, con mensaje que dice **dónde está el fichero**; y `ArchivoSinTraza` para poder decirlo solo cuando es verdad | `function_app.py`, `paso_archivo.py`, `errores.py` |
| **15** | `/api/archivar` exige que el parte esté en `partes`, y **nada lo inserta**: el archivado no puede completar | **No se arregla aquí** (es de F-019). Anotado en su ficha con el error como prueba, y en el runbook | `harness/features.json`, `BACKLOG.md`, `docs/DESPLIEGUE.md` §5 ter |

**Commits** (uno por defecto, más uno de servicio):

```
24f50ad F-010 defecto 14: /api/archivar traduce los fallos de la persistencia
7ff86d7 F-010 defecto 13: los verificadores y los enunciados, contra la via que si existe
2c55e6c F-010 defecto 15: F-019 queda anotada como prerequisito del archivado real
ec4b4b0 F-010: se versiona el informe de la re-review, que estaba sin commitear
```

---

## Defecto 14 · el borde no traducía `PersistenciaNoDisponible`

Es el que más trabajo llevó, y el único con código de producción, así que va
primero.

### Lo que había

`function_app.py` traducía `CuerpoDeArchivoInvalido` (400), `ParteNoApto` y
`NombradoImposible` (409), `ArchivoDeshabilitado` y
`ConfiguracionSharePointIncompleta` (503) y `ArchivoFallido` (502).
`PersistenciaNoDisponible` no estaba, así que salía del handler sin traducir y
el llamante recibía **500 sin cuerpo**. El 2026-08-25 eso costó media hora de
Application Insights para leer una frase que el servicio ya tenía escrita:

```
PersistenciaNoDisponible: la operación 'guardar_archivo' no se pudo completar
contra PostgreSQL: ForeignKeyViolation
```

### La decisión que había que tomar: qué código

El criterio que ya usaba el fichero es **por capa que falla**: 400 el que
llama, 409 el estado del parte, 503 aquí no se archiva, 502 el proveedor no
respondió. Pero los cuatro comparten algo que el propio docstring declara y
que el `acceptance` de F-006 (R31) da por cierto: **«en los cuatro casos, sin
haber subido nada»**. Y el caso nuevo es el primero que rompe eso: cuando la
traza falla, el PDF **ya está** en la biblioteca de Posventa, porque
`paso_archivo` sube y **después** persiste.

De ahí la elección, con las alternativas descartadas y por qué:

| Código | Por qué no / por qué sí |
|---|---|
| **502** | Es tentador —PostgreSQL es «un proveedor que no respondió»— pero en este endpoint 502 significa además **nada subido**. Reciclarlo dejaría al llamante sin forma de distinguir «no hay nada arriba, reintenta» de «el fichero está arriba, no reintentes»: exactamente la información que costó la media hora |
| **503** | Igual de malo por el mismo motivo, y encima **invita a reintentar**: es lo que dice hoy la ventana de escritura cerrada |
| **200 con aviso** | Mentira: la operación no se completó. Y R30 fija las seis claves de la respuesta «y nada más», así que el aviso viajaría en un cuerpo de éxito |
| **500 con cuerpo** ✅ | Es el único que no promete nada falso, y es **el que el llamante ya recibía**: nadie que trate hoy este error tiene que cambiar. Lo que cambia es que ahora se puede leer |

**Contrato tocado, y queda dicho** (esto es lo que el reviewer tiene que
mirar): el enunciado «los cuatro códigos de error, y en todos sin haber subido
nada» de F-006 (R31, y el docstring de `function_app.archivar`) **ya no
describe el endpoint entero**. Sigue valiendo para 400, 409, 502 y 503 —y el
mensaje de los dos nuevos 503 lo dice con todas las letras— y el **500 es la
excepción declarada**. No se ha tocado la spec de F-006: no es de esta feature.
La rectificación está escrita en el docstring del endpoint, que es donde mira
quien lo va a cambiar.

### `ArchivoSinTraza`, y por qué no bastaba con traducir en el borde

Escribiendo el test salió un caso que el enunciado del defecto no contemplaba
y que habría convertido el arreglo en una mentira:

**`PersistenciaNoDisponible` no significa siempre «el fichero está subido».**
Hay dos caminos en los que sale con la biblioteca intacta:

1. `construir_repositorio(ajustes)` no puede abrir la conexión. Corre en
   `archivar_parte` **antes** de que se suba nada.
2. La subida falla (`ArchivoFallido`) y, al guardar la **traza de error**
   (R24), la base tampoco responde.

Si el borde contestara «el parte SÍ se ha subido a SharePoint» en esos dos
casos, mandaría a alguien a buscar un fichero que no existe. Y el borde **no
puede distinguirlo**: quien conoce el orden es el paso.

Por eso `paso_archivo` renombra el fallo **solo en el camino en el que ya
subió** (`_dejar_constancia`) y lo levanta como `ArchivoSinTraza`. No se traga
nada: el motivo viaja entero y encadenado (`raise ... from`). El bloque
`except ArchivoFallido` se deja **intacto a propósito**: allí el
`PersistenciaNoDisponible` sí significa «no hay nada arriba», y es lo que el
borde traduce a 503.

Mapeo final de `POST /api/archivar`:

| Error | Código | Lo que dice el mensaje |
|---|---|---|
| `CuerpoDeArchivoInvalido` | 400 | (sin cambios) |
| `ParteNoApto`, `NombradoImposible` | 409 | (sin cambios) |
| `ArchivoDeshabilitado`, `ConfiguracionSharePointIncompleta` | 503 | (sin cambios) |
| **`ConfiguracionPgIncompleta`** | **503** | falta configuración de la base; **no se ha subido nada**; nombra la variable, jamás su valor |
| **`PersistenciaNoDisponible`** | **503** | la base no responde; **no se ha subido nada**; se puede reintentar |
| **`ArchivoSinTraza`** | **500** | **el parte SÍ está en SharePoint**; falta la traza; volver a archivarlo no arregla nada |
| `ArchivoFallido` | 502 | (sin cambios) |

`ConfiguracionPgIncompleta` no la pedía el enunciado. Se incluye porque es la
**hermana exacta** del defecto: misma familia, mismo endpoint, y hasta hoy el
mismo 500 mudo. Dejarla fuera era garantizar el defecto 16.

**R26 comprobado con un test propio**: el mensaje reenvía el motivo de F-005,
que se compone sin DSN y sin contraseña (R29), y el test verifica que no
aparecen ni el DNI del «PDF» de prueba, ni sus bytes, ni la palabra
`password`.

### Fase RED · defecto 14

Test escrito **antes** que el código, en
`services/postventa-api/tests/test_f010_borde_persistencia.py`. Comando exacto:

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests/test_f010_borde_persistencia.py -q
```

**Primera ejecución** —con el fichero de test recién escrito y sin nada más—,
la colección ni siquiera llega a empezar porque el error de dominio no existe:

```
ImportError while importing test module 'tests\test_f010_borde_persistencia.py'.
tests\test_f010_borde_persistencia.py:36: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'ArchivoSinTraza' from 'domain.models.errores'
=========================== short test summary info ===========================
ERROR tests/test_f010_borde_persistencia.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.44s
```

**Segunda ejecución**, ya con la clase declarada y **sin ninguna otra línea de
producción**, que es la que enseña el defecto de verdad: el fallo se escapa del
borde tal cual, igual que en el entorno real.

```
FFFFFF.                                                                  [100%]
...
>       respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

tests\test_f010_borde_persistencia.py:90:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
function_app.py:278: in archivar
    cuerpo = archivar_parte(
tests\test_f006_archivar_http.py:111: in envoltura
    return archivar_parte(
interface_adapters\api\archivar.py:92: in archivar_parte
    contexto = paso_archivo(
application\pipelines\paso_archivo.py:123: in paso_archivo
    repositorio.guardar_archivo(traza=ctx.archivo)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = RepositorioFalso(archivos=[], fallo=PersistenciaNoDisponible("la operación
'guardar_archivo' no se pudo completar contra PostgreSQL: ForeignKeyViolation"))

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        if self.fallo is not None:
>           raise self.fallo
E           domain.models.errores.PersistenciaNoDisponible: la operación
'guardar_archivo' no se pudo completar contra PostgreSQL: ForeignKeyViolation

tests\utiles_sharepoint.py:299: PersistenciaNoDisponible
...
=========================== short test summary info ===========================
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_traza_perdida_tras_subir_responde_500_con_cuerpo
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_el_mensaje_dice_que_el_fichero_esta_subido
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_el_mensaje_no_lleva_datos_personales_ni_bytes
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_sin_subida_previa_responde_503_y_lo_dice
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_falta_de_configuracion_de_pg_responde_503
FAILED tests/test_f010_borde_persistencia.py::test_f010_defecto14_el_paso_levanta_archivo_sin_traza_cuando_ya_subio
6 failed, 1 passed in 2.24s
```

El que pasa en rojo es `..._si_la_subida_fallo_el_paso_no_lo_llama_asi`: es el
**control** del arreglo —el camino que **no** debe cambiar— y por eso ya estaba
verde antes de tocar nada.

**Después del código, el mismo comando:**

```
.......                                                                  [100%]
7 passed in 1.35s
```

---

## Defecto 13 · el host desnudo de la Function ya no responde

### Lo que pasa, y por qué no es un fallo del despliegue

Desde que la Function App es **backend enlazado** de la Static Web App, la
plataforma le activa Easy Auth con el proveedor `azureStaticWebApps` y solo
acepta lo que entra por el proxy del front. Por su nombre de host contesta a
**todo** —`GET /api/health` incluido— con un cuerpo que **no es nuestro**:

```json
{"code":400,"message":"Login not supported for provider azureStaticWebApps"}
```

`infra/verificar_archivo_dev.ps1` se escribió en F-006, antes de que existiera
la Static Web App, y con `$ErrorActionPreference = "Stop"` ese 400 salía como
un `WebException` pelado.

### Lo que se ha hecho

1. **`infra/verificar_archivo_dev.ps1`**: la llamada va dentro de un `try`, y
   el `catch` lee **el código y el cuerpo** de la respuesta. Si es `400` con
   `azureStaticWebApps`, imprime la explicación —qué pasa, por qué, y que la
   vía buena es la consola del navegador en el front— y sale con **código 2**,
   propio, distinto del `1` de «falta `-BaseUrl`». Cualquier otro fallo se
   relanza tal cual, diciendo antes el código. También lo avisa la ayuda y la
   cabecera `.DESCRIPTION`.
   **El script no se borra**: sigue valiendo el día que el backend vuelva a ser
   alcanzable por su host, y su paso 4 —listar la carpeta en solo lectura— no
   depende del proxy.
2. **`infra/verificar_despliegue.ps1`**: este no moría —`Get-Codigo-Http`
   devuelve el código— pero dejaba dos `NO` sin explicar, que se leen como «el
   despliegue está roto». Ahora imprime la nota cuando el código es `400`, una
   sola vez. No es lo que pedía el enunciado, pero **es el mismo defecto en el
   script que ejecuta los criterios de T14**: arreglar el enunciado y dejar el
   script mudo era dejar la trampa puesta.
3. **`docs/DESPLIEGUE.md` §5 bis**: la vía que sí funciona, con el **fragmento
   de consola íntegro** que se ejecutó el 2026-08-25. Va al **mismo origen**,
   así que no lleva ninguna URL —y hay un test que lo comprueba—. Se copió del
   fichero suelto del escritorio del humano, que es donde no sobrevive a la
   siguiente sesión.
4. **`specs/F-010-despliegue/tasks.md`**, enunciados y **ninguna casilla**:
   - **T14, criterio 1**: `GET /api/health` se comprueba **a través del
     front**, y se dice que el `400` por el host desnudo no es un fallo.
   - **T14, criterio 3**: dejaba de medir lo que decía medir. La ventana de
     escritura se comprueba **leyendo la App Setting** con `az`, que es lo que
     sigue siendo observable; queda escrito que el `503` por HTTP solo se ve a
     través del front. Rectificado el enunciado y **la casilla `[x]` intacta**,
     con el precedente de T8 y T19 de F-006 citado en el propio texto.
   - **T18**: el comando cambia a la vía por la consola, y se añade lo que pasó
     el 2026-08-25 (defecto 15, abajo).

### Fase RED · defecto 13

Los scripts son PowerShell: no entran en cobertura ni en mutación, y lo que
sobrevive a la siguiente edición es un test de contrato, como ya hacen
`test_f006_scripts_infra.py` y `test_f010_scripts_infra.py`.

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest tests/test_f010_scripts_infra.py -q -k defecto13
```

```
FFFF                                                                     [100%]
================================== FAILURES ===================================
___ test_f010_defecto13_el_verificador_de_t18_reconoce_el_400_de_easy_auth ____
>       assert "azureStaticWebApps" in archivo_dev
E       assert 'azureStaticWebApps' in '# infra/verificar_archivo_dev.ps1\n<#\n.SYNOPSIS\n...'
tests\test_f010_scripts_infra.py:1123: AssertionError
_____ test_f010_defecto13_el_verificador_de_t18_dice_cual_es_la_via_buena _____
>       assert "consola" in minusculas
E       assert 'consola' in '# infra/verificar_archivo_dev.ps1\n<#\n.synopsis\n...'
tests\test_f010_scripts_infra.py:1136: AssertionError
____ test_f010_defecto13_el_verificador_de_t18_no_muere_con_un_error_opaco ____
>       assert "catch" in archivo_dev
E       assert 'catch' in '# infra/verificar_archivo_dev.ps1\n<#\n.SYNOPSIS\n...'
tests\test_f010_scripts_infra.py:1147: AssertionError
______ test_f010_defecto13_el_verificador_del_despliegue_explica_el_400 _______
>       assert "azureStaticWebApps" in verificar
E       assert 'azureStaticWebApps' in '# infra/verificar_despliegue.ps1\n<#\n.SYNOPSIS\n...'
tests\test_f010_scripts_infra.py:1158: AssertionError
=========================== short test summary info ===========================
4 failed, 117 deselected in 0.32s
```

Y el del runbook, con el fragmento de consola:

```
./.venv/Scripts/python.exe -m pytest tests/test_f010_tarjeta_portal.py -q -k defecto13
```

```
>       assert "5 bis" in runbook
E       AssertionError: assert '5 bis' in '<!-- docs/DESPLIEGUE.md -->\n# Despliegue de postventa-incidencias\n...'
tests\test_f010_tarjeta_portal.py:176: AssertionError
...
>       assert fragmentos, "el runbook no trae el fragmento de consola de T18"
E       AssertionError: el runbook no trae el fragmento de consola de T18
E       assert []
tests\test_f010_tarjeta_portal.py:195: AssertionError
=========================== short test summary info ===========================
2 failed, 22 deselected in 0.20s
```

**Después**: `24 passed` en `test_f010_tarjeta_portal.py` y `138 passed,
3 skipped` en los dos ficheros de contrato de scripts.

Nota de diseño que salió al hacerlo: la *fixture* `bloque` de
`test_f010_tarjeta_portal.py` cogía **el primer bloque `js` del documento**.
Con el fragmento de consola delante, esos tests habrían pasado a afirmar sobre
otra cosa sin enterarse. Ahora busca el bloque **que contiene
`requiredGroupId`**, que es lo que siempre quisieron decir.

**Sintaxis de los dos `.ps1` comprobada sin ejecutarlos**, con el parser de
PowerShell (`[System.Management.Automation.Language.Parser]::ParseFile`):
`0 errores` en los dos. No se ha ejecutado ninguno: llaman a Azure.

---

## Defecto 15 · F-019 es prerequisito del archivado real

**No se ha arreglado, y es lo correcto**: es de F-019 y esta feature no toca
specs ajenas. Lo que se ha hecho es que **no se pierda**.

La prueba, tal y como salió de Application Insights el 2026-08-25:

```
psycopg.errors.ForeignKeyViolation: insert or update on table "archivos"
violates foreign key constraint "archivos_hash_parte_fkey"
DETAIL:  Key (hash_parte)=(verificacion-t18-20260825140835) is not present in
table "partes".
```

La tabla `archivos` exige que el parte exista antes, y **hoy no hay ningún
endpoint que lo inserte**: los que guardarían la remesa son **F-019**, que
sigue `pending`. Consecuencia, y así queda escrito: **tal y como está
desplegado, el archivado no puede completar nunca**, ni con parte sintético ni
con parte real.

Anotado en tres sitios, ninguno de ellos una spec ajena:

- **`harness/features.json`, ficha de F-019**: el prerequisito, con el error de
  clave ajena como prueba, la fecha, y el aviso de que al implementarla hay que
  comprobar el orden (el parte se guarda **antes** de archivarlo).
  `BACKLOG.md` regenerado con `python -m harness.backlog` y `bash
  harness/init.sh` lo da **al día**.
- **`docs/DESPLIEGUE.md` §5 ter**: por qué el archivado no completa todavía,
  donde lo va a leer quien opere el entorno.
- **`tasks.md`, verificación de T18**: qué pasó al ejecutarla, por qué el `200`
  de los dos primeros puntos **no puede llegar** hasta F-019, y que lo
  observable mientras tanto es el **listado de la carpeta**, que es justo lo
  que pide el `acceptance` de F-006. Decidir si eso cierra la casilla T18 de
  F-006 sigue siendo del humano, ante **C5**.

---

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/models/errores.py` | `ArchivoSinTraza`, nuevo |
| `services/postventa-api/application/pipelines/paso_archivo.py` | `_dejar_constancia`: renombra el fallo **solo** si ya se subió |
| `services/postventa-api/function_app.py` | tres traducciones nuevas (500, 503, 503) y el docstring del endpoint, con la excepción del contrato declarada |
| `services/postventa-api/interface_adapters/api/archivar.py` | docstring: la lista de lo que levanta, y qué significa cada una respecto a la subida |
| `services/postventa-api/tests/test_f010_borde_persistencia.py` | **nuevo**, 7 tests |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | 4 tests de contrato del defecto 13 |
| `services/postventa-api/tests/test_f010_tarjeta_portal.py` | 2 tests del fragmento de consola + *fixture* `bloque` corregida |
| `infra/verificar_archivo_dev.ps1` | reconoce el 400 de Easy Auth, lo explica y sale con código propio |
| `infra/verificar_despliegue.ps1` | nota cuando el código es 400 |
| `docs/DESPLIEGUE.md` | §5 bis (la vía por la consola, con el fragmento) y §5 ter (por qué no completa) |
| `specs/F-010-despliegue/tasks.md` | enunciados de T14 (criterios 1 y 3) y T18. **Cero casillas** |
| `harness/features.json`, `BACKLOG.md` | la nota de F-019 |
| `progress/review2_F-010.md` | **solo versionado**, ni una línea tocada |

## Lo que queda fuera, y por qué

- **El arreglo del defecto 15.** Es de F-019.
- **`specs/F-010-despliegue/design.md:252` y `requirements.md:227`** siguen
  diciendo que T18 se ejecuta con `verificar_archivo_dev.ps1 -BaseUrl` y que
  ese script «no se modifica». Las dos frases son **falsas desde hoy**. No las
  toco: son `requirements`/`design` y reescribirlos es del `spec-author`. **Se
  reporta como residuo**, que es lo mismo que se hizo en la ronda anterior con
  los «once secretos» de `cargar_secretos_postventa.ps1`.
- **Residuo aún vivo de la ronda anterior**: `cargar_secretos_postventa.ps1`
  sigue pidiendo «once secretos» por pantalla (`:269`).
- **Nada ejecutado contra Azure, SharePoint ni PostgreSQL.**

## Verificaciones `MANUAL (humano)` que siguen pendientes

Las mismas de antes, con el enunciado ya corregido: **T15**, **T17** y **T18**
sin marcar, y el resultado real de **T14 bis** y **T19** sin anotar. T18, con
el defecto 15 encima, no puede dar `200` hasta que exista F-019.

---

## Evidencias

Medidas, no estimadas. Comandos exactos entre paréntesis.

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** (`bash harness/init.sh`) | **1092 passed, 13 skipped** en el servicio `api`; **17 passed** en la suite del arnés. Cero fallos |
| De ellos, **nuevos en esta ronda** | **13**: 7 en `test_f010_borde_persistencia.py`, 4 en `test_f010_scripts_infra.py`, 2 en `test_f010_tarjeta_portal.py` |
| **Cobertura de las líneas cambiadas** (línea `PUERTA COBERTURA`) | **`[OK]` 98.5% de 136 líneas cambiadas (134/136, umbral 80%, nivel estandar)**. Antes de esta ronda: 98.3% de 116 (114/116) → las **20 líneas nuevas medidas están cubiertas al 100%**; las 2 sin cubrir son las mismas de antes y no se han tocado |
| **Ficheros no medidos** | Los dos `.ps1` de `infra/` y los enunciados en Markdown: `harness/alcance.py` solo mide `.py`. Por eso llevan **tests de contrato sobre su texto**, que es lo que sobrevive a la siguiente edición |
| **Mutantes generados / supervivientes** (`python -m harness.mutacion --feature F-010`) | **23 generados, 23 evaluados, 20 muertos, 3 supervivientes, 0 timeouts**, campaña completa (sin muestreo), **16 workers**, **43.6 s**. Informe: `progress/mutacion_F-010.md` |
| **Supervivientes, uno a uno** | Los **tres** son el mismo `log.info("=" * 60)` → `"=" * 61` de `services/postventa-front/dev_server.py` (líneas 169, 171 y 175), **ya analizados y declarados equivalentes** en la campaña del 2026-08-20 y arrastrados por la herramienta con su análisis completo. Releído contra el código actual: **`dev_server.py` no se ha tocado en esta ronda**, el análisis sigue valiendo y ninguna sección del informe queda en `PENDIENTE` |
| **Mutantes de las líneas nuevas** | Los tres códigos de estado que se añaden (`503`, `503`, `500` en `function_app.py:320`, `:332` y `:349`) generaron mutante y **los tres murieron**: son exactamente los tres tests del borde de esta ronda |
| **Tiempo de ejecución de la suite** | **28.12 s** el servicio `api` (1092 tests) y **0.43 s** la del arnés, según la salida del propio `pytest` dentro de `bash harness/init.sh` |
| **Lint** | `python -m ruff check` sobre los siete `.py` tocados: **`All checks passed!`**. El portero sigue avisando de los **56** avisos de deuda previa, ni uno nuevo |
| **Portero** | `bash harness/init.sh` **en verde**, tal cual, al terminar |
