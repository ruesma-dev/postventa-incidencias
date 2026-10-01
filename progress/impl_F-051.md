<!-- progress/impl_F-051.md -->
# F-051 · La carpeta base vacía no llega a la Function — Informe del implementer

Rama `feature/F-051-carpeta-base-raiz` (desde `dev`). Rigor `critico`,
`sdd=false`: las tareas salen de los `acceptance` y del encargo del líder (T1–T4).
Sin push. Nada tocado en Azure: ni `az ... set` ni ninguna llamada contra
producción. `harness/features.json` sin tocar (sigue `in_progress`).

## 0 · Qué cambió, en una frase

Con `posventa`, una `SHAREPOINT_CARPETA_BASE` **ausente** es ya la raíz de la
biblioteca (con `por_obra` sigue siendo `Postventa`); el despliegue escribe la
raíz como `/` y se niega a fijar cualquier App Setting vacía; la Function deja
una traza `INFO` con el destino efectivo; y el guion del corte comprueba esa
traza en Application Insights en vez de la configuración.

## 1 · Commits

| Commit | Tarea | Qué |
|---|---|---|
| `cab1506` | T1 | `sharepoint_carpeta_base: str \| None = None`; `carpeta_base_efectiva` en la fábrica; validación R17 y borde de `/api/archivar` con la base efectiva; tests |
| `11a5e5a` | T2 | traza `F-051 destino efectivo del archivo: estructura X, carpeta base Y` al construir el archivador; tests con `caplog` |
| `56dbad8` | T3 | `00_vars` con `"/"`; `desplegar_backend.ps1` con `Carpeta-Base-Para-Azure` y la guarda `App-Settings-Vacias`; `verificar_destino_sharepoint.ps1` decide la base por estrategia; tests |
| `f5b5e22` | T4 | `DESPLIEGUE.md` §9 pasos 5 y 6 (KQL), `INTEGRACION.md`, `.env.example`; tests de documentación |
| `59e9a8f` en **`azure-apps`** | T4 | `postventa_incidencias.md`, los mismos cambios que INTEGRACION. Commit local, `git add` solo de ese fichero (el árbol de `azure-apps` estaba limpio) |
| (este) | — | este informe, `progress/mutacion_F-051.md`, `progress/current.md` |

## 2 · Ficheros tocados

**Producción (Python)**
- `services/postventa-api/config/settings.py`: el campo pasa a `str | None`, con
  defecto `None` y un comentario con el porqué. `None` es «no está»; `""` es
  «está vacía».
- `services/postventa-api/infrastructure/sharepoint/fabrica.py`:
  `CARPETA_BASE_POR_OMISION = "Postventa"`, `carpeta_base_efectiva(ajustes)`
  (la regla, en un solo sitio), `_problemas_de_estructura` la usa para R17, y
  `_trazar_destino_efectivo` (T2).
- `services/postventa-api/interface_adapters/api/archivar.py`: `carpeta_base=` del
  paso y `base=` del resolutor de Posventa usan `carpeta_base_efectiva`.

**Infra (PowerShell, ASCII + CRLF, sin BOM)**
- `infra/00_vars_postventa.ps1`: `$CarpetaBaseArchivo = "/"` y el porqué.
- `infra/desplegar_backend.ps1`: funciones `Carpeta-Base-Para-Azure` (vacía o
  en blanco → `/`) y `App-Settings-Vacias`; `$carpetaBaseAppSetting` es lo que
  se escribe y lo que se enseña en las dos líneas «Destino del archivo»; guarda
  antes de `az functionapp config appsettings set` que sale con `Salir-Con` y
  `$SALIDA_FALLO` nombrando las App Settings vacías.
- `infra/verificar_destino_sharepoint.ps1`: lee `SHAREPOINT_ESTRUCTURA`; sin
  base, la raíz con `posventa` y `Postventa` con `por_obra`; `/` o vacía es la
  raíz (existe siempre); aviso en rojo si es la raíz con `por_obra`.

**Documentación**
- `docs/DESPLIEGUE.md` §9: paso 5 con `"/"` y `carpeta base '/'`, más recuadro
  fechado del incidente; paso 6 reescrito («lo que lee la aplicación»): se
  conserva el `az ... appsettings list` (debe dar `posventa`, `/`, `true`) pero
  se dice que **no basta**, y el criterio pasa a ser la traza, con la consulta
  KQL; recuadro que cita lo que decía antes.
- `docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md`: recuadro
  inicial «CORTE HECHO» (base en la raíz, escrita `/`), fila «Carpeta base» con
  `SHAREPOINT_CARPETA_BASE=/`, recuadro fechado tras la tabla de §3, fila de
  riesgos «el vacío no llega» actualizada («Pasó el 2026-10-01») y recuadro
  tras la enmienda de F-013 de §4 («`/`, no vacía después del corte»).
- `services/postventa-api/.env.example`: el comentario de la base por estrategia.

**Tests**
- Nuevos: `tests/test_f051_carpeta_base.py` (17), `tests/test_f051_traza_destino.py`
  (10), `tests/test_f051_scripts_infra.py` (21), `tests/test_f051_documentacion.py` (11).
- Ajustados (ver §4): `tests/test_f013_fabricas.py` (1 test) y
  `tests/test_f013_documentacion.py` (3 tests).

## 3 · Decisiones de diseño

1. **Mecanismo: el campo con defecto `None` y la regla en la fábrica.**
   `carpeta_base_efectiva` solo resuelve la **ausencia** por estrategia (`""`
   en `posventa`, `Postventa` en las demás); un valor **puesto** pasa tal cual.
   Recortar barras y blancos sigue siendo de `unir_ruta` / `carpeta_de_archivo`,
   y rechazar la raíz en `por_obra`, de `_problemas_de_estructura` (R17). Así
   no cambia nada más de F-006 ni de F-013.
2. **Estrategia desconocida y base ausente → `Postventa`**, como antes de
   F-051. No llega a archivar (R3 la rechaza en la fábrica y en el borde); se
   eligió no inventar un tercer comportamiento.
3. **La traza va después de las puertas** y justo antes de construir el
   adaptador: un destino rechazado no se traza como efectivo. Formato:
   `raíz` sin comillas y un nombre entre `«»`, para que una carpeta llamada
   «raíz» no se confunda. Ni drive, ni sitio, ni tenant, ni cliente (test).
   Se emite en **cada** construcción del archivador, es decir, en cada
   `/api/archivar` con el cuerpo completo, antes de tocar SharePoint; no al
   arrancar la Function (la fábrica no corre al arrancar).
4. **La guarda genérica `App-Settings-Vacias`** va más allá del acceptance
   literal («no escribe nunca `SHAREPOINT_CARPETA_BASE` vacía»): para el
   despliegue si **cualquier** App Setting sale vacía, porque es la misma clase
   de fallo (Azure la descartaría y el código usaría su defecto en silencio).
   Va antes de fijar nada; un abort ahí deja las App Settings como estaban,
   igual que un fallo de `az`. Si el líder la considera fuera de alcance, se
   quita sin tocar lo demás (son 9 líneas y su test).
5. **El paso 6 conserva el `az ... appsettings list`** (lo exige además un test
   de F-013 de T17), pero ya no decide: decide la traza.
6. **La consulta KQL se lanza en el portal, no con `az monitor app-insights
   query`** desde PowerShell 5.1: las comillas dobles de la consulta se
   destrozan al pasar a un ejecutable nativo (familia de F-029) y `az` es un
   `.cmd`. Lo dice el propio paso 6.
7. **`arnes-base`**: no aplica. Nada de lo cambiado es del arnés genérico.

## 4 · Desviaciones y tests de otras features ajustados (justificados)

- `test_f013_fabricas.py::test_f013_r1_la_estrategia_por_omision_es_la_de_hoy`
  afirmaba `ajustes.sharepoint_carpeta_base == "Postventa"`, que era
  precisamente el mecanismo del incidente. Ahora afirma
  `carpeta_base_efectiva(ajustes) == "Postventa"` (lo que protege: `por_obra`
  por omisión intacto). Con recuadro de enmienda en su docstring.
- `test_f013_documentacion.py`: `$CarpetaBaseArchivo = ""` → `"/"` en dos tests
  (variables de infra y pasos del runbook), y `$CarpetaBaseArchivo` →
  `$carpetaBaseAppSetting` en los dos tests de lo que escribe y enseña el
  despliegue. Con enmienda fechada en cada uno.
- En los documentos, las premisas de F-006 citadas por F-013 (R29) **no** se
  tocan; los recuadros de F-013 tampoco: se añaden recuadros de F-051 detrás.
- T4 (documentación) no siguió la fase RED estricta: los tests de
  documentación se escribieron después de editar los documentos. La fase RED se
  hizo en T1, T2 y T3, que son los requisitos centrales (§5).

## 5 · Fase RED (salida real)

### T1 · el incidente, reproducido desde el handler

Comando (desde `services/postventa-api`):

```
.venv/Scripts/python -m pytest "tests/test_f051_carpeta_base.py::test_f051_a1_posventa_sin_la_variable_lista_la_raiz_y_archiva" -q -p no:cacheprovider
```

Salida antes del código (recortada al final de la traza):

```
tests\test_f051_carpeta_base.py:172:
tests\test_f051_carpeta_base.py:110: in _archivar_villa_5
    return archivar.archivar_parte(
interface_adapters\api\archivar.py:199: in archivar_parte
    contexto = paso_archivo(
application\pipelines\paso_archivo.py:376: in paso_archivo
    resuelto = _resolver(
application\pipelines\paso_archivo.py:694: in _resolver
    return resolver_destino(
application\pipelines\destino_archivo.py:241: in resolver_destino_posventa
    obra = camino.bajar(
application\pipelines\destino_archivo.py:132: in bajar
    hijas = self._listar()
self = _Camino(explorador=<tests.test_f051_carpeta_base.ArchivadorDePosventa object at 0x000001E638189D60>, crear_carpetas=True, ruta='Postventa', nuevo=False, por_crear=[])
E           domain.models.errores.ArchivoFallido: la carpeta «Postventa» no existe en la biblioteca: o la base configurada no es la de Posventa, o alguien la ha borrado o renombrado mientras se resolvía. No se ha creado ni subido nada
application\pipelines\destino_archivo.py:168: ArchivoFallido
FAILED tests/test_f051_carpeta_base.py::test_f051_a1_posventa_sin_la_variable_lista_la_raiz_y_archiva
1 failed in 1.10s
```

Es **el mismo mensaje** que dieron los 502 de producción. El fichero entero, en
rojo antes del código: `10 failed, 7 passed in 1.31s` (los 7 verdes eran los
casos que ya funcionaban: `por_obra` sin la variable, `/` y vacía explícitas en
`posventa`, y el rechazo en `por_obra`; los 10 rojos, el del incidente, los 8 de
`carpeta_base_efectiva` —`AttributeError: module 'infrastructure.sharepoint.fabrica'
has no attribute 'carpeta_base_efectiva'`— y `assert 'Postventa' is None`).

Después: `17 passed in 0.93s`.

### T2 · la traza

```
.venv/Scripts/python -m pytest tests/test_f051_traza_destino.py -q -p no:cacheprovider
```

```
>       (traza,) = _trazas(caplog)
E       ValueError: not enough values to unpack (expected 1, got 0)
------------------------------ Captured log call ------------------------------
INFO     infrastructure.sharepoint.fabrica:fabrica.py:88 F-006 archivador de SharePoint construido en el entorno dev
...
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[posventa-ausente]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[posventa-barra]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[posventa-vacia]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[posventa-barra-con-blancos]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[posventa-con-nombre]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[por_obra-ausente]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_fabrica_traza_el_destino_efectivo[por_obra-recortada]
FAILED tests/test_f051_traza_destino.py::test_f051_t2_el_incidente_se_habria_visto_en_la_traza
FAILED tests/test_f051_traza_destino.py::test_f051_t2_la_traza_no_lleva_ningun_identificador
9 failed, 1 passed in 0.36s
```

(El verde era «si la fábrica se niega, no hay traza», cierto también antes.)
Después: `10 passed in 0.24s`.

### T3 · los scripts

```
.venv/Scripts/python -m pytest tests/test_f051_scripts_infra.py -q -p no:cacheprovider
```

```
E       AssertionError: assert [''] == ['/']
E         At index 0 diff: '' != '/'
E       assert '"SHAREPOINT_CARPETA_BASE=$carpetaBaseAppSetting"' in '\n    "ENTORNO=dev",\n    "NIVEL_LOG=INFO", ...
E       AssertionError: no encuentro la funcion Carpeta-Base-Para-Azure
E           assert '$carpetaBaseAppSetting' in 'Write-Host ("  Destino del archivo  : estructura \'{0}\', carpeta base \'{1}\', crear carpetas \'{2}\'" -f $EstructuraArchivo, $CarpetaBaseArchivo, $CrearCarpetasArchivo)'
E       ValueError: substring not found
E       AssertionError: no encuentro la funcion App-Settings-Vacias
E       assert 'Get-Variable-De-Entorno "SHAREPOINT_ESTRUCTURA"' in '\n\n[CmdletBinding()]\nparam(...
E       assert '-eq "posventa"' in '\n\n[CmdletBinding()]\nparam(...
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_las_variables_declaran_la_raiz_como_barra
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_el_despliegue_escribe_la_base_ya_resuelta
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_la_base_vacia_se_escribe_como_barra
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_el_despliegue_ensena_lo_que_escribe
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_ninguna_app_setting_vacia_llega_a_azure
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_la_guarda_mira_el_valor_y_no_el_nombre
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_las_dos_funciones_se_ejecutan_en_powershell
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_la_verificacion_lee_la_estrategia
FAILED tests/test_f051_scripts_infra.py::test_f051_t3_la_verificacion_trata_la_raiz_como_raiz
9 failed, 6 passed in 2.69s
```

(Los 6 verdes: ASCII/CRLF/cabecera de los tres scripts, ciertos ya antes.)
Después: `15 passed`; con los 6 casos añadidos que ejecutan el tramo real de
`verificar_destino_sharepoint.ps1`, `21 passed in 3.44s`.

## 6 · Qué se verificó, con resultado real

- **Suite del servicio**: `4415 passed, 52 skipped` (dentro de `init.sh`, 76,97 s).
- **`bash harness/init.sh`**: `ENTORNO LISTO`, `PUERTA COBERTURA: 100.0% de 14
  líneas cambiadas cubiertas (14/14, umbral 80%, nivel critico)`.
- **PowerShell 5.1 (5.1.26100.9549), ejecución real**, no solo lectura:
  - `Carpeta-Base-Para-Azure`: `""`, `"   "`, `$null` y `"/"` → `/`;
    `"Postventa"` → `Postventa`. `App-Settings-Vacias` sobre
    `A=1, B=, C=  , "D=@Microsoft.KeyVault(SecretUri=x)", "E=", F=/` → `B,C,E`;
    sobre `A=1, F=/` → ninguna. (Test, lanzado con `-File` sobre un `.ps1`
    temporal, nunca `-Command`.)
  - El tramo de la base de `verificar_destino_sharepoint.ps1`, con el entorno
    de cada caso: nada → `por_obra|Postventa|False`; `posventa` sin base →
    raíz; `posventa` + `/` → raíz; `por_obra` + `/` → raíz (con el aviso en
    rojo en el script real); `posventa` + `" OTRA/ "` → `OTRA`.
  - Análisis sintáctico (`Parser::ParseFile`) de los tres scripts: 0 errores.
  - `verificar_destino_sharepoint.ps1 -WhatIf` (no llama a nada) sin variables y
    con `posventa` + `/`: la ayuda dice `SHAREPOINT_ESTRUCTURA sin definir; se
    usara 'por_obra'` / `posventa`, y `SHAREPOINT_CARPETA_BASE sin definir; con
    posventa, la raiz; con por_obra, 'Postventa'` / `puesta`.
- **La línea del guion es la del código**: `test_f051_t4_el_paso_6_busca_la_traza_que_emite_la_fabrica`
  genera la traza con la configuración del corte y comprueba que el texto del
  paso 6 la contiene letra a letra.
- `ruff` limpio en todos los `.py` tocados.
- **No ejecutado**: `desplegar_backend.ps1` (ni con `-WhatIf`, que ya hace
  lecturas contra Azure). Su cambio está cubierto por los tests estáticos y por
  la ejecución de sus dos funciones nuevas.

## 7 · Fuera del alcance

- Desplegar. La mitigación `SHAREPOINT_CARPETA_BASE=/` sigue siendo la que
  sostiene producción hasta que se despliegue F-051; con F-051 desplegada, esa
  misma App Setting (`/`) sigue siendo correcta.
- Reprocesar los ~20 partes del 2026-10-01 que fallaron: no se escribió nada a
  medias; se vuelven a archivar desde la aplicación y su cierre va detrás.
- `infra/verificar_archivo_dev.ps1` declara `$CarpetaBasePorDefecto = "Postventa"`
  y no la usa (F-006, dev): no se toca.
- `docs/ARCHITECTURE.md`: no habla de la base vacía; sin cambios.

## 8 · Verificaciones MANUAL pendientes (humano, tras desplegar)

1. Desplegar como siempre (`infra\desplegar_backend.ps1`). Antes de
   `DESPLEGAR`, la línea tiene que decir «Destino del archivo: estructura
   'posventa', carpeta base '/', crear carpetas 'true'».
2. Tras el primer archivado (de Ana o de quien sea), en el portal: Application
   Insights `appi-postventa-dev` → **Registros**, esta consulta de solo
   lectura:

   ```kusto
   traces
   | where timestamp > ago(1d)
   | where message has "F-051 destino efectivo del archivo"
   | project timestamp, message
   | order by timestamp desc
   | take 20
   ```

   Tiene que salir `F-051 destino efectivo del archivo: estructura posventa,
   carpeta base raíz`. Si dice `carpeta base «…»` con cualquier nombre: freno 1
   (`infra\22_ventana_archivo.ps1 -Cerrar`) y de vuelta al líder. Si no sale
   nada habiendo archivados: ampliar el `ago(...)`; si sigue sin salir, la
   versión desplegada no lleva F-051. **Lo que no se ha podido comprobar en
   local** es que la línea `INFO` del logger de Python llegue a `traces` en
   esta Function App (el muestreo de `host.json` está activo salvo para
   `Request`); el precedente es `F-013 unidades leídas en Sigrid`, también
   `INFO`, que el paso 8 del mismo runbook ya busca ahí.
3. Con Posventa: el parte archivado está en su carpeta, y el cierre en Sigrid
   se ha hecho.

## 9 · Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (servicio api) | **4415 passed, 52 skipped**, 0 fallos |
| Tests de F-051 | **59** (17 + 10 + 21 + 11), todos verdes, 4,48 s |
| Cobertura de las líneas cambiadas | **100,0 %** (14/14, umbral 80 %, `critico`) |
| Mutación del arnés | **3 generados, 3 muertos, 0 supervivientes**, 0 timeouts, 57,0 s, **3 workers** (ver nota) |
| Mutantes a mano (complemento, en `progress/mutacion_F-051.md`) | **9: 8 muertos, 1 superviviente equivalente en producción** (analizado allí) |
| Tiempo de la suite | 76,97 s dentro de `init.sh`; 41–52 s lanzada sola |
| PowerShell | cobertura y mutación no miden `.ps1`; la evidencia es la ejecución real de las funciones y del tramo de la base en PowerShell 5.1 (§6) |

**Nota sobre el comando de la mutación (review 1, cambio 2).** Lo que se
lanzó fue, literal:

```
python -m harness.mutacion --feature F-051 --base dev --max-mutantes 40
```

y la cabecera de `progress/mutacion_F-051.md` dice
`python -m harness.mutacion --feature F-051 --workers 3`. No son dos campañas:
es la misma, y la cabecera la escribe `comando_de()` de `harness/mutacion.py`
con lo que **de verdad** se usó para reproducirla:

- **workers**: no se pasó `--workers`; se tomó `mutacion.workers = 8` de
  `harness/rigor.json` («Campaña paralela: hasta 8 workers» en la salida), y
  `harness/mutacion_paralela.py:434` lo recorta a
  `min(workers, número de mutantes)` = **3**, que es lo que registra el
  informe y su tabla («Workers | 3»);
- **`--base dev`**: no sale porque es la base por defecto (el propio
  `comando_de` omite `dev` a propósito);
- **`--max-mutantes 40`**: no sale porque `comando_de` no lo registra y
  además no actuó (3 mutantes < 40; «Muestreo: no: campaña completa»).

Para reproducirla vale cualquiera de los dos comandos; el de la cabecera fija
además los workers.

## 10 · Review 1 (CHANGES_REQUESTED): lo que me tocaba

Del `progress/review_F-051.md` §5. Sin cambios en código de producción. El
cambio 1 (las MANUAL en `progress/current.md`) lo hizo el líder; el 4 es del
humano (aceptar por escrito el superviviente equivalente a mano).

| Cambio | Commit | Qué |
|---|---|---|
| 2 | (este informe) | §9: 3 workers y la explicación del comando de la mutación |
| 3 | `76fe3e2` (T5) | `docs/DESPLIEGUE.md` §9, paso 6, «si no sale ninguna línea» |
| H-1 | `46800d5` (T6) | recuadros fechados de una línea en `specs/F-013-archivo-posventa/` |

### Cambio 3 · el paso 6 cuando no sale ninguna línea

Ahora, antes de concluir: (1) ampliar el `ago` y repetir con
`message contains "destino efectivo del archivo"` (bloque `kusto`); (2) las
**tres** causas —versión sin F-051, muestreo de `host.json`, o **las `INFO` no
llegan a `traces`**—; la tercera se distingue con la consulta de la línea de
F-006 (`F-006 archivador de SharePoint construido`, mismo logger, nivel y
sitio), con `summarize n = count() by bin(timestamp, 1h)`; (3) si tampoco sale
la de F-006, la verificación pasa a ser el resultado: `requests` con
`name == "archivar"` por `resultCode` (un `200` tras el despliegue) y el parte
en su carpeta con Posventa, y **no se da el corte por bueno sin ninguna de las
dos**. Y la advertencia: `az monitor app-insights query` mira por defecto
**una hora** (`--offset 1h`) aunque la consulta diga `ago(3d)`; desde la línea
de comandos hay que pasar `--offset` (p. ej. `--offset 3d`); en el portal no
pasa. Las cuatro consultas del paso 6 son de solo lectura (test).

Nombre de la función en `requests`: `archivar`, el de la función de
`function_app.py:691` (`@app.route(route="archivar")`). No lo he podido
comprobar contra Application Insights; si la consulta no devuelve nada habiendo
archivados, probar `name has "archivar"`.

RED (comando: `.venv/Scripts/python -m pytest tests/test_f051_documentacion.py -q -p no:cacheprovider`,
desde `services/postventa-api`), antes de tocar el documento:

```
E       ValueError: not enough values to unpack (expected 1, got 0)
E       ValueError: not enough values to unpack (expected 1, got 0)
E       ValueError: not enough values to unpack (expected 1, got 0)
E       AssertionError: assert '--offset 1h' in '6. Lo que lee la aplicación, no lo que dice la configuración. La ventana de archivo, abierta: powershell -ExecutionPo...ro no pasa a la aplicación uno de valor vacío. La > configuración de Azure no es lo que lee la Function; la traza, sí.'
FAILED tests/test_f051_documentacion.py::test_f051_r1_si_no_sale_se_repite_con_contains
FAILED tests/test_f051_documentacion.py::test_f051_r1_la_tercera_causa_se_distingue_con_la_linea_de_f006
FAILED tests/test_f051_documentacion.py::test_f051_r1_sin_traza_la_verificacion_es_el_resultado
FAILED tests/test_f051_documentacion.py::test_f051_r1_aviso_de_la_ventana_de_az_monitor
4 failed, 12 passed in 1.04s
```

Después: verdes. El test que exigía **un solo** bloque `kusto` en el paso 6
se partió en dos: el que busca la consulta de F-051 por su contenido y otro que
comprueba que **todas** las consultas del paso empiezan por `traces` o
`requests` y ninguna línea por `.` (comandos de administración de KQL).

### H-1 · la spec de F-013 remite a F-051

Un recuadro fechado de **una línea** («La raíz se escribe
`SHAREPOINT_CARPETA_BASE=/` (`$CarpetaBaseArchivo = "/"`), nunca vacía: …»)
detrás de la tabla de decisiones de `requirements.md` (D-1), detrás de la tabla
de decisiones de `design.md` (D-1), detrás del paso 5 de `design.md` §7.3 y
detrás del paso 5 del despliegue de `tasks.md`. Los textos originales con `""`
no se tocan. Test `test_f051_h1_la_spec_de_f013_remite_a_f051`, en RED antes
(mismo comando, `-k h1`):

```
E       assert 0 == 1
E        +  where 0 = len([])
E       assert 0 == 2
E        +  where 0 = len([])
E       assert 0 == 1
E        +  where 0 = len([])
FAILED tests/test_f051_documentacion.py::test_f051_h1_la_spec_de_f013_remite_a_f051[requirements.md-1]
FAILED tests/test_f051_documentacion.py::test_f051_h1_la_spec_de_f013_remite_a_f051[design.md-2]
FAILED tests/test_f051_documentacion.py::test_f051_h1_la_spec_de_f013_remite_a_f051[tasks.md-1]
3 failed, 16 deselected in 0.45s
```

### Evidencias tras la review 1

| Evidencia | Valor |
|---|---|
| Tests ejecutados (servicio api) | **4423 passed, 52 skipped**, 0 fallos (54,08 s lanzada sola) |
| Tests de F-051 | **67** (los 59 de antes + 8: 5 del cambio 3 —uno de ellos el partido— y 3 de H-1) |
| Cobertura de las líneas cambiadas | **100,0 %** (14/14), sin cambios de producción en la review; `init.sh` en verde, suite 121,62 s dentro de él |
| Mutación | sin cambios de producción: no se relanza; vale la de §9 |

### Una cosa vista de paso (no la toco: es del líder)

En `progress/current.md`, bloque de F-051, MANUAL 3, el freno lleva un carácter
de control (0x12) en lugar de `\22`: `infra<0x12>_ventana_archivo.ps1 -Cerrar`
(un `\22` tomado como escape octal al escribirlo). Debe ser
`infra\22_ventana_archivo.ps1 -Cerrar`. Copiado tal cual, el comando falla.

## 11 · T7 · los caracteres de control de R2-4 (review 2, decisión del humano)

**Qué eran.** Rutas de Windows escritas desde un programa: `\22`, `\21`,
`\25` y `\1` (seguido de `9`) se tomaron como escapes octales y en el fichero
quedó un byte de control invisible en lugar de `\` + número. El comando copiado
del guion fallaría; uno de ellos es el freno 1.

**Barrido** de `[\x00-\x08\x0b\x0c\x0e-\x1f]` en los **202 `.md` versionados**
del repositorio (`git ls-files '*.md'`, no solo `docs/`, `progress/` y
`specs/`). Antes, 6 bytes en 3 ficheros; después, 0. Cada script de destino se
comprobó en `infra/` antes de sustituir (los cuatro existen con ese nombre):

| Fichero | Línea | Byte | Quedaba | Ahora |
|---|---|---|---|---|
| `docs/DESPLIEGUE.md` | 274 | `0x12` | `infra<0x12>_ventana_archivo.ps1` | `infra\22_ventana_archivo.ps1` |
| `docs/DESPLIEGUE.md` | 352 | `0x01` | `infra<0x01>9_ventana_escritura.ps1` | `infra\19_ventana_escritura.ps1` |
| `progress/current.md` | 1914 | `0x11` | `infra<0x11>_historico_estado.ps1` | `infra\21_historico_estado.ps1` |
| `progress/current.md` | 1966 | `0x01` | `infra<0x01>9_ventana_escritura.ps1` | `infra\19_ventana_escritura.ps1` |
| `progress/cierre_verificaciones_F-033.md` | 61 | `0x15` | `infra<0x15>_mediciones_despliegue.ps1` | `infra\25_mediciones_despliegue.ps1` |
| `progress/cierre_verificaciones_F-033.md` | 63 | `0x15` | `infra<0x15>_mediciones_despliegue.ps1` | `infra\25_mediciones_despliegue.ps1` |

Los dos de `cierre_verificaciones_F-033.md` no estaban en la lista del
reviewer: salieron del barrido y se corrigieron con el mismo criterio
(`0x15` = octal `25`, y `infra/25_mediciones_despliegue.ps1` existe). La
sustitución se hizo en bytes, sin tocar los finales de línea.

**Test nuevo**: `services/postventa-api/tests/test_f051_sin_caracteres_de_control.py`
(10 casos). Barre los `.md` versionados bajo `docs/`, `progress/` y `specs/`
(por `git ls-files`; sin git, todos los de esas carpetas), con un caso que exige
que el barrido vea `docs/DESPLIEGUE.md` y `progress/current.md`, y controles
negativos (los bytes reales de R2-4 y los extremos del rango saltan; tabulador,
LF, CRLF y acentos no).

RED, sobre el árbol de antes (desde `services/postventa-api`,
`.venv/Scripts/python -m pytest tests/test_f051_sin_caracteres_de_control.py -q -p no:cacheprovider`):

```
E       assert {'docs/DESPLI...escritura.'"]} == {}
E         Left contains 3 more items:
E         {'docs/DESPLIEGUE.md': ["línea 274, 0x12: b'en\r\npalabras: "
E                                 "`infra\x12_ventana_archivo.ps1'",
E                                 "línea 352, 0x01: b' el script**: "
E                                 "`infra\x019_ventana_escritura.'"],
E          'progress/cierre_verificaciones_F-033.md': ["línea 61, 0x15: b'y Bypass -File "...
FAILED tests/test_f051_sin_caracteres_de_control.py::test_f051_t7_ningun_markdown_versionado_lleva_caracteres_de_control
1 failed, 9 passed in 0.39s
```

Después: `10 passed in 0.29s`. Sin cambios en código de producción: cobertura y
mutación, las de §9.
