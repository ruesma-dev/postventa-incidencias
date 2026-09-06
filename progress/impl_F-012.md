<!-- progress/impl_F-012.md -->
# F-012 · Subir el parte a Sigrid como gráfico — informe del implementer

> Rama `feature/F-012-grafico-sigrid` (creada desde `feature/F-009-cierre-sigrid`).
> Rigor `critico`. 21 commits, T1–T24 hechos y marcados.
> **Bloque 9 (T25–T32), T33 y T34 NO se han ejecutado ni marcado**: el encargo
> del líder los reserva para el humano o para él. Qué exigen y con qué comandos
> está al final, en «Lo que queda».
> `bash harness/init.sh` en verde el 2026-09-06.

---

## 1 · Qué cambió, en una frase

El PDF del parte firmado se adjunta ahora a la reclamación **como gráfico de
Sigrid**, por `POST /api/sigrid/concepto-grafico` de la pasarela, **antes** del
cambio de estado; y el cierre **se niega a ejecutarse** si ese gráfico no
consta adjuntado. Con eso, el riesgo aceptado de `docs/ARCHITECTURE.md`
—reclamaciones en `CER` sin ninguna fila en `rcg`— queda **cerrado por diseño y
sin haberse producido ni una vez**, porque F-012 se implementa antes del primer
cierre real.

---

## 2 · Ficheros tocados

### Creados

| Ruta | Qué es |
|---|---|
| `services/postventa-api/domain/models/grafico.py` | Dominio puro: constantes medidas, las tres listas cerradas de códigos de la pasarela, `PeticionGrafico` / `PlanDeGrafico` / `RespuestaGrafico` / `ResultadoGrafico`, y `validar_fichero`, `componer_peticion`, `esta_colgado`, `clasificar_codigo` |
| `services/postventa-api/domain/ports/grafico.py` | `GraficoPort`, **un método** |
| `services/postventa-api/application/pipelines/paso_grafico.py` | El paso 7a, con el orden de `design.md` §6 |
| `services/postventa-api/infrastructure/sigrid/graficos.py` | `AdaptadorGraficoSigridApi`, con la doble puerta y sin `Retrying` |
| `services/postventa-api/infrastructure/persistencia/sql/09_graficos.sql` | La traza local, en el esquema propio |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | Handler de `POST /api/adjuntar` (`multipart`) |
| `infra/15_reclamaciones_obra_prueba.ps1` | Localiza las candidatas de la obra de prueba. Solo lectura |
| `infra/16_grafico_sigrid.ps1` | Las tres filas del gráfico + `MAX(ide)` de `dbo.log`. Solo lectura |
| `infra/17_traza_grafico_local.ps1` | La traza propia. Solo lectura del esquema propio |
| 12 ficheros de test en `services/postventa-api/tests/` | `test_f012_*` |
| `services/postventa-front/tests_js/grafico.test.js`, `services/postventa-front/tests/test_f012_front.py` | El front |

### Modificados (lo esencial)

| Ruta | Qué cambia |
|---|---|
| `domain/models/cierre.py` | **Se retiran** `AVISO_SIN_GRAFICO` y `PlanDeCierre.aviso_sin_grafico` (R48) |
| `domain/models/persistencia.py` | `EstadoGrafico` y `TrazaGrafico` |
| `domain/models/errores.py` | Los ocho errores nuevos |
| `domain/ports/persistencia.py` | `guardar_grafico` y `consultar_grafico` |
| `application/pipelines/contexto_parte.py` | `grafico` y `traza_grafico` |
| `application/pipelines/paso_cierre.py` | `_exigir_adjuntado` (R2), `ctx.traza_grafico` (R49) y `exigir_autorizacion_para_escribir` **pública** |
| `infrastructure/persistencia/{sentencias,repositorio_pg,mapeo}.py` | `upsert_grafico`, `select_grafico`, `fila_a_traza_grafico` |
| `infrastructure/sigrid/fabrica.py` | `construir_graficos` |
| `config/settings.py`, `.env.example`, `local.settings.json.example` | `SIGRID_GRATIPIDE_PARTE`, `GRAFICO_MAX_BYTES` |
| `function_app.py`, `interface_adapters/api/cerrar.py` | Ruta `adjuntar`; `ParteNoAdjuntado` → 409; el bloque `grafico` del dry-run |
| `services/postventa-front/js/{api,pipeline,app}.js`, `index.html` | `adjuntar()`, `cuerpoDeGrafico`, `estaAdjuntado`, los dos dry-run, los estados nuevos |
| `infra/desplegar_backend.ps1` | Las dos App Settings |
| `docs/{ARCHITECTURE,INTEGRACION,DESPLIEGUE}.md` | T19 y T20 |
| `azure-apps/postventa_incidencias.md` | **Otro repositorio**, commit local `72b8fa3`, sin push |
| Tests de F-009 y F-019 adaptados | §4 |

**`infrastructure/sigrid/{cliente,consultas,escrituras}.py` no se han tocado**:
el gráfico **importa** de `cliente.py` la fontanería (`construir_cliente_http`,
`CORRECTOS`, las dos puertas, la cabecera) y no copia ni una línea. El cierre
no cambia ni una sentencia (R51).

---

## 3 · Las decisiones que la implementación obligó a tomar

Cuatro cosas que la spec no fijaba y que había que decidir. Las tres primeras
son desviaciones respecto a la letra del diseño; la cuarta es un orden que la
spec dejaba abierto.

### 3.1 · `ResultadoGrafico.plan` pasa a ser **anulable** (desviación de §6)

`design.md` §6 lo declara obligatorio. No puede serlo: **R24 prohíbe llamar a
nadie** cuando la traza local ya dice `adjuntado`, así que en ese camino no hay
reclamación leída con la que construir un `PlanDeGrafico`. Fabricar uno a
partir de la traza sería enseñar un dry-run que nadie ha ejecutado.

Lo que se devuelve entonces es un campo nuevo, `traza`, que es de donde salió
la respuesta; el borde lo serializa como `dry_run.ya_estaba = true`. Tests:
`test_f012_r24_la_respuesta_desde_la_traza_lleva_la_traza_y_no_un_plan` y
`test_f012_r24_cuando_se_resuelve_desde_la_traza_no_se_inventa_un_dry_run`.

### 3.2 · El **dry-run también deja traza de `error`** (precisión de §7.3)

La tabla de `design.md` §7.3 asigna traza `error` a los códigos de rechazo sin
decir en qué fase. Un rechazo en el dry-run —clase no permitida, concepto
inexistente— **es información sobre este parte** y tiene que quedar
registrada: es literalmente lo que T31 del bloque 9 verifica.

La excepción sigue siendo `EscrituraDocumentalDeshabilitada` (R32): **ninguna
traza**. No ha pasado nada con este parte; lo que falta es una App Setting de
otro proyecto, y una traza de `error` diría que el problema es del parte.
Test: `test_f012_r32_una_precondicion_de_la_pasarela_no_deja_traza`.

### 3.3 · Los cimientos de T2 se adelantaron a T1

`domain/models/grafico.py` no compila sin `EstadoGrafico`, `TrazaGrafico` y los
ocho errores nuevos, que `tasks.md` coloca en T2. Se adelantan al commit de T1
para que **cada commit deje el árbol compilando**; T2 se queda con el puerto,
los dos métodos del repositorio y `test_f012_arquitectura.py`.

### 3.4 · `_exigir_adjuntado` va **antes** de la autorización

`tasks.md` no fija el orden entre las dos. Va antes porque con `commit`, sin
`confirmado` y sin gráfico, **lo que falta de verdad es el gráfico**: al revés,
quien reciba el 400 creerá que basta con confirmar, confirmará, y se encontrará
el mismo 409 una pantalla después. Test:
`test_f012_r2_la_precondicion_se_comprueba_antes_de_la_autorizacion`.

---

## 4 · Los tests ajenos que se adaptaron, y por qué cada uno

**Ninguna adaptación quita una comprobación sin sustituirla.** En los cuatro
sitios donde se retiró un test de R21 se dejó un **control negativo** en su
lugar: sin él, alguien podría reponer el aviso por costumbre y volver a
advertir de algo que ya no ocurre.

| Fichero | Qué se cambió | Por qué |
|---|---|---|
| `test_f009_dominio_cierre.py` | Los dos tests de R21 y la construcción de `PlanDeCierre` | **R48 deroga R21.** En su sitio, `test_f009_r21_el_plan_ya_no_declara_ningun_aviso_de_grafico` |
| `test_f009_adaptador_sigrid.py`, `test_f009_escrituras.py` | El campo en la construcción del plan | Íd. Ninguna aserción propia se toca |
| `test_f009_cerrar_http.py` | La aserción de R9 sobre `aviso_sin_grafico` y el test del aviso | Íd. En su sitio, `test_f009_r21_derogado_la_respuesta_ya_no_trae_el_aviso_de_grafico`. Además, el doble por omisión trae la traza `adjuntado`: es el estado del mundo en el que el cierre ocurre desde hoy |
| `test_f009_front.py` | Los dos `r21_*` | Íd. En su sitio, un control negativo sobre el HTML |
| `test_f009_paso_cierre.py`, `test_f009_logs_sin_datos_personales.py` | Se inyecta la traza `adjuntado` en los dobles de los casos que **escriben** | R2. El dry-run no la exige (R50), y los tests de qué pasa **sin** ella viven en `test_f012_cerrar_exige_grafico.py` |
| `test_f009_ddl_orden.py` | `nombres[-1] == FICHERO` se retira | Era una propiedad **del catálogo en aquel momento**, no del DDL de F-009. La dependencia con `01_esquema.sql` se conserva |
| `test_f005_ddl_idempotente_texto.py` | La lista de `.sql` gana el noveno | La lista se escribe a mano **a propósito**: añadir un fichero tiene que pasar por ahí. Funcionó |
| `test_f003_paso_extraccion.py` | El censo de campos de `ContextoParte` | Es el guardián que obliga a pasar por él a quien añada un campo. Funcionó |
| `test_f010_endpoints_protegidos.py` | El censo de endpoints, de diez a once | Íd. La cuenta tuvo que cuadrar **antes** de que la ruta existiera |
| `test_f010_scripts_infra.py` | El censo de variables `SIGRID_*`, de cinco a seis | Íd. `SIGRID_GRATIPIDE_PARTE` no es sensible, por lo mismo que `SIGRID_TIP_RECLAMACION` |
| `test_f009_documentacion.py` | «ESCRITURA» → «ESCRITURAS» | Lo que protegía —que el documento lo diga en mayúsculas— sigue igual |
| `test_f019_documentacion.py` | «Los diez» → «Los once» | Íd. |
| `tests_js/api.test.js` | El censo de métodos del cliente, de diez a once | Íd. |

---

## 5 · Fase RED

Rigor `critico`: obligatoria para los requisitos centrales. Se pega **la salida
real**, con el comando exacto. Todos se lanzaron desde
`services/postventa-api/`.

### 5.1 · T1 · el dominio del gráfico (R7, R9, R10, R12, R18, R19, R26, R53)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_dominio_grafico.py -x -q
=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f012_dominio_grafico.py _____________
ImportError while importing test module '...\tests\test_f012_dominio_grafico.py'.
Traceback:
tests\test_f012_dominio_grafico.py:28: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'CuerpoDeGraficoInvalido' from 'domain.models.errores'
=========================== short test summary info ===========================
ERROR tests/test_f012_dominio_grafico.py
1 error in 0.45s
```

Después de escribir el código: `47 passed in 0.24s`.

### 5.2 · T2 · la hexagonal, y el control negativo de `base64`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_arquitectura.py -q
FAILED tests/test_f012_arquitectura.py::test_f012_el_puerto_del_grafico_existe
FAILED tests/test_f012_arquitectura.py::test_f012_arquitectura_el_puerto_del_grafico_es_dominio_puro
FAILED tests/test_f012_arquitectura.py::test_f012_arquitectura_ni_domain_ni_application_nombran_base64
FAILED tests/test_f012_arquitectura.py::test_f012_los_ejemplos_de_entorno_declaran_las_dos_variables_nuevas[SIGRID_GRATIPIDE_PARTE-.env.example]
FAILED tests/test_f012_arquitectura.py::test_f012_los_ejemplos_de_entorno_declaran_las_dos_variables_nuevas[SIGRID_GRATIPIDE_PARTE-local.settings.json.example]
FAILED tests/test_f012_arquitectura.py::test_f012_los_ejemplos_de_entorno_declaran_las_dos_variables_nuevas[GRAFICO_MAX_BYTES-.env.example]
FAILED tests/test_f012_arquitectura.py::test_f012_los_ejemplos_de_entorno_declaran_las_dos_variables_nuevas[GRAFICO_MAX_BYTES-local.settings.json.example]
7 failed, 2 passed, 2 skipped in 2.08s
```

**El tercer fallo es el que vale contarlo**: el control negativo saltó contra
**mi propio código de T1**, porque tres docstrings míos nombraban `base64`. Se
reescribieron para decir lo mismo sin la palabra, que es de lo que va el
control. Después: `9 passed, 2 skipped`.

### 5.3 · T4 · el DDL de la traza

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_ddl_orden.py -q
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF                                     [100%]
______________ test_f012_el_ddl_de_f012_se_recoge_con_los_demas _______________
>       assert FICHERO in nombres
E       AssertionError: assert '09_graficos.sql' in ['01_esquema.sql', '02_remesas.sql',
E         '03_partes.sql', '04_validaciones.sql', '05_archivos.sql', '06_cierres.sql', ...]
36 failed in 2.68s
```

Después: `36 passed`.

### 5.4 · T5 · la traza local en el repositorio (R30, R43, R44)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_repositorio_graficos.py -q
tests\test_f012_repositorio_graficos.py:38: in <module>
    from infrastructure.persistencia.mapeo import fila_a_traza_grafico
E   ImportError: cannot import name 'fila_a_traza_grafico' from 'infrastructure.persistencia.mapeo'
1 error in 0.64s
```

Después: `18 passed in 0.43s`.

### 5.5 · T7 · el adaptador (R6, R7, R13, R20, R25, R26, R31–R35, R38, R39, R55)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_adaptador_grafico.py -q
tests\test_f012_adaptador_grafico.py:48: in <module>
    from infrastructure.sigrid import graficos
E   ImportError: cannot import name 'graficos' from 'infrastructure.sigrid'
1 error in 1.27s
```

Y una **segunda vuelta en rojo**, ya con el adaptador escrito, que también
cuenta:

```
>       assert "Retrying" not in fuente
E       AssertionError: assert 'Retrying' not in '# services/...'
E         'Retrying' is contained here:  y **sin `Retrying`**
1 failed, 62 passed in 1.08s
```

El control saltó contra el docstring que explica **por qué** no hay reintentos.
Se reescribió con `ast` —imports y nombres— en vez de buscar la palabra en el
texto, que es la misma solución que `test_f009_scripts_infra.py` usa con su
bloque de ayuda; y no se quedó ahí: hay además un test que hace fallar una
llamada y comprueba que `ClienteFalso` grabó **una** petición. Después:
`63 passed in 0.55s`.

### 5.6 · T8 · la fábrica (R39, R40)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_fabrica_grafico.py -q
tests\test_f012_fabrica_grafico.py:26: in <module>
    from infrastructure.sigrid.fabrica import (
E   ImportError: cannot import name 'construir_graficos' from 'infrastructure.sigrid.fabrica'
1 error in 0.57s
```

Después: `16 passed in 0.44s`.

### 5.7 · T9 · el paso del pipeline (R14–R29, R42, R43, R47)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_paso_grafico.py -q
tests\test_f012_paso_grafico.py:35: in <module>
    from application.pipelines.paso_grafico import paso_grafico
E   ModuleNotFoundError: No module named 'application.pipelines.paso_grafico'
1 error in 0.70s
```

Y una segunda vuelta en rojo con el paso ya escrito, que descubrió la
precisión de §3.2:

```
FAILED tests/test_f012_paso_grafico.py::test_f012_r33_un_rechazo_de_la_pasarela_deja_traza_de_error
FAILED tests/test_f012_paso_grafico.py::test_f012_r47_si_el_erp_escribe_y_la_traza_no_sale_un_error_propio
2 failed, 51 passed in 0.53s
```

Después: `53 passed in 0.42s`.

### 5.8 · T12 · el cierre exige el gráfico (R2, R49, R50, R51, R52)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_cerrar_exige_grafico.py -q
tests\test_f012_cerrar_exige_grafico.py:35: in <module>
    from application.pipelines.paso_cierre import (
E   ImportError: cannot import name 'exigir_autorizacion_para_escribir' from 'application.pipelines.paso_cierre'
1 error in 0.73s
```

Y, ya con `paso_cierre` cambiado, **22 tests de F-009 en rojo**, que es
exactamente la señal de que la precondición muerde:

```
$ .venv/Scripts/python.exe -m pytest -q
FAILED tests/test_f009_paso_cierre.py::test_f009_r12_con_confirmacion_explicita_si_se_escribe
FAILED tests/test_f009_paso_cierre.py::test_f009_r22_un_cierre_que_no_afecta_a_dos_filas_no_se_da_por_bueno
FAILED tests/test_f009_cerrar_http.py::test_f009_r13_con_auto_cierre_activo_si_cierra_sin_confirmar
... (22 en total, en tres ficheros)
22 failed, 1858 passed, 13 skipped in 45.28s
```

Después de inyectar la traza `adjuntado` en los dobles: `24 passed` en el
fichero propio y la suite entera en verde.

### 5.9 · T11 · el control negativo de datos personales (R53, R54, R55)

**Los 11 tests pasaron a la primera**, porque T7 y T9 ya se escribieron para no
filtrar nada. Un control que nunca se ha visto saltar no demuestra nada, así
que su fase RED se hizo **rompiendo deliberadamente una copia aislada** del
paso —fuera del repositorio, en el scratchpad, según `CHECKPOINTS.md` C4 bis—
con un `log.info` del contenido del PDF inyectado:

```
$ .venv/Scripts/python.exe <scratchpad>/red_t11.py
registros capturados: 2
EL CONTROL SALTA. Datos filtrados por la copia rota:
  - 00000000T
  - Nombreinventadoquenoexiste Apellidoinventado
  - Textomanuscritoinventadodelcliente sobre la reparacion
```

El árbol real no se tocó en ningún momento; la copia rota vive en el
scratchpad de la sesión.

---

## 6 · Cómo se verificó cada cosa, con el resultado real

Todo **sin red, sin base de datos y sin IA**: la guardia de `tests/conftest.py`
sigue parcheando `socket.socket.connect` durante toda la sesión, y con
`ENTORNO=test` **ninguno de los dos adaptadores de Sigrid se puede construir**
(`test_f012_r41_con_el_entorno_de_la_suite_no_se_puede_construir_nada`).

| Qué | Cómo | Resultado |
|---|---|---|
| El orden gráfico → cierre (R20, R64) | Contando las llamadas del doble: `GraficoEnMemoria.orden` tiene que ser `[False, True]` | Verde |
| La primera capa de idempotencia (R24) | **Cero** llamadas al ERP y a la pasarela con la traza en `adjuntado` | Verde |
| `esta_colgado` (R26) | Los **cuatro cuadrantes**, incluido `ok:true committed:false idempotente:true` → colgado | Verde |
| Los doce códigos de la pasarela (R31–R34) | Uno a uno, en el adaptador **y** en la ruta HTTP | Verde |
| El cuerpo crudo del error (R35) | Un `400` de prueba que lleva la clave de función y un DNI dentro; se comprueba que no salen | Verde |
| La doble puerta (R38, R39) | Construir el adaptador con `ENTORNO=local` y con el interruptor apagado, sin una sola llamada | Verde |
| El PDF en los logs (R53) | Un PDF con el DNI **escrito dentro del fichero**, y la lista de prohibidos incluye 32 caracteres del texto codificado | Verde |
| La precondición del cierre (R2) | **Cero** llamadas a `erp.cerrar` con `commit` y sin traza `adjuntado`, ni siquiera con auto-cierre | Verde |
| Los scripts de infra | 53 tests: ninguno escribe, ninguna llamada a `sql/write`, `DATALENGTH` y nunca `ima`, y ni un host, GUID, `sha256` o incidencia real | Verde |

**Lo que no se ha ejecutado, y hay que decirlo**: **nada** contra Azure, Sigrid,
`sigrid-api`, el PostgreSQL compartido ni SharePoint. Ni una lectura. Los tres
scripts de `infra/` se han **escrito y validado sintácticamente** con el
analizador de PowerShell, pero **no se han lanzado**.

---

## 7 · Evidencias

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **2.032 pasan, 13 se saltan** en el servicio `api`; **130 pasan** en `front` (que incluye el puente a `node --test`: **187** tests de JavaScript). Ni uno rojo |
| **De ellos, propios de F-012** | **464**: 421 en `api`, 26 en `tests/test_f012_front.py` y 17 en `tests_js/grafico.test.js` |
| **Cobertura de las líneas cambiadas** | **`[OK] PUERTA COBERTURA: 98.7% de 1079 líneas cambiadas cubiertas (1065/1079, umbral 80%, nivel critico)`** |
| **Tiempo de ejecución de la suite** | `api` **32,9 s**; `front` **1,9 s** (con los 187 de JS en 0,52 s dentro) |
| **Mutantes generados y supervivientes** | **NO EJECUTADA. Es T33, y el encargo la reserva al humano o al líder.** Ver 7.1 |
| **Nº de workers de la campaña** | N/A por lo mismo. `harness/rigor.json` declara **8** |
| **ruff** | **58 avisos, exactamente la deuda previa**: F-012 no añade ni uno |

### 7.1 · La campaña de mutación: qué falta y qué se sabe ya

`CHECKPOINTS.md` C4 bis exige la campaña en nivel `critico`, y **no está
hecha**. El motivo es explícito y no es una omisión: el encargo del líder dice
que T33 y T34 «los ejecuta el humano o el líder: NO los ejecutes ni los
marques». Queda por tanto **PENDIENTE de ejecución por el líder**, y este
informe no puede cerrarla.

Lo que sí se puede dar sin ejecutarla, porque es **cálculo puro** y le ahorra
al líder la mitad del trabajo:

```
$ python -c "... harness.mutacion.alcance_de_feature('F-012') + generar_mutantes ..."
FICHEROS: 24   TOTAL mutantes: 224
```

| Mutantes | Fichero |
|---:|---|
| 29 | `infrastructure/sigrid/cliente.py` |
| 25 | `application/pipelines/paso_grafico.py` |
| 23 | `domain/models/cierre.py` |
| 21 | `infrastructure/sigrid/escrituras.py` |
| 19 | `domain/models/grafico.py` |
| 19 | `function_app.py` |
| 19 | `infrastructure/sigrid/graficos.py` |
| 15 | `application/pipelines/paso_cierre.py` |
| 14 | `interface_adapters/api/adjuntar.py` |
| 14 | `infrastructure/sigrid/consultas.py` |
| 10 | `config/settings.py` |
| 6 | `interface_adapters/api/cerrar.py` |
| 4+2+2+1+1 | `repositorio_pg.py`, `fabrica.py`, `persistencia.py`, `errores.py`, `sentencias.py` |
| 0 | los 7 restantes (puertos, `mapeo.py`, `contexto_parte.py`, `__init__.py`) |

**Dos cosas que el líder debe saber antes de lanzarla:**

1. **~102 de esos 224 mutantes no son de F-012.** El alcance sale del diff
   contra `dev`, y esta rama nace de `feature/F-009-cierre-sigrid`, que tampoco
   está en `dev`: `cliente.py` (29), `escrituras.py` (21), `consultas.py` (14),
   `cierre.py` (23) y parte de `paso_cierre.py` (15) son código de F-009, que
   **ya pasó su propia campaña con 123 mutantes y cero supervivientes sin
   justificar**. Si se quiere medir solo F-012, la campaña se puede lanzar con
   `--base feature/F-009-cierre-sigrid`.
2. **Coste estimado**: 224 mutantes × 32,9 s de suite ÷ 8 workers ≈ **15
   minutos** de reloj. Con `--base feature/F-009-cierre-sigrid` bajarían a
   ~122 mutantes y ~8 minutos. El comando literal:

```bash
python -m harness.mutacion --feature F-012                       # los 224
python -m harness.mutacion --feature F-012 --base feature/F-009-cierre-sigrid
```

**Candidatos a superviviente que se ven venir**, y que `tasks.md` T33 ya
anticipaba: el **orden de las dos puertas** en el constructor de
`AdaptadorGraficoSigridApi` —mismo caso que `cliente.py:347` en F-009: cualquier
orden levanta `CierreDeshabilitado`, y por eso hay un test que comprueba que
**ninguna de las dos hace una sola llamada**— y las **comparaciones de longitud**
de `componer_peticion` y `validar_fichero`, para las que hay tests de límite
exacto (`test_f012_r18_justo_en_el_tope_pasa`,
`test_f012_r18_un_byte_de_mas_aborta`). No se dan por buenos: se analizan
cuando la campaña corra.

---

## 8 · Verificaciones `MANUAL (humano)` pendientes

### 8.1 · T21 — hecha, pero en otro repositorio

`azure-apps/postventa_incidencias.md` está refrescado y **commiteado en local**
(`72b8fa3`), **sin push**, como manda `CLAUDE.md`. `azure-apps/sigrid_api.md`
**no se ha tocado**: es del dueño de la pasarela.

### 8.2 · Bloque 9 (T25–T32) — sin ejecutar, y su guion sin escribir

Todo el bloque es `MANUAL (humano)`, contra el ERP de producción y **sobre
reclamaciones de la obra de prueba 404**. `tasks.md` pide que su guion
detallado se escriba en `progress/guion_bloque9_F-012.md` al llegar ahí; **ese
fichero no existe todavía**, y escribirlo es lo primero del bloque.

**Precondiciones que exige de la configuración de `sigrid-api` en `dev`** (P0,
y son **del dueño de la pasarela**, no nuestras). Se leen sin ver ningún valor
con `az functionapp config appsettings list` sobre **su** Function App:

| App Setting de `sigrid-api` | Qué tiene que valer | Qué pasa aquí si no |
|---|---|---|
| `SIGRID_DOMAIN_WRITE_ENABLED` | `true` | Sin ella no hay endpoint de dominio que valga |
| `SIGRID_DOCUMENT_WRITE_ENABLED` | `true` | `/api/adjuntar` → **503** con `escritura_documental_deshabilitada`, **sin escribir nada** |
| `SIGRID_DOCUMENT_WRITE_DATABASE` | `ruesma_rep` | Vacía → el mismo 503, **también en el dry-run** |
| `SIGRID_DOCUMENT_ALLOWED_CONTIP` | contiene `708` | **409** con `tipo_de_concepto_no_coincide` |
| `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` | contiene `35` | **409** con `clase_de_grafico_no_permitida` |
| `SIGRID_DOCUMENT_MAX_BYTES` | ≥ el tamaño del parte de prueba | **409** con `tamano_excedido`. Nuestro `GRAFICO_MAX_BYTES` (10 MB) no protege de esto: es un tope propio y no el suyo |

Según `design.md` §0, el dueño las dejó en esos valores el **2026-09-06**. Hay
que **releerlas antes de abrir la ventana**, no darlas por buenas.

Las otras precondiciones, resumidas: `init.sh` en verde en esta rama (**hecho**),
el backend desplegado con el código de F-012 (**pendiente**), los secretos de
Sigrid en el Key Vault y las App Settings puestas (`infra/14_paso0_sigrid.ps1`),
raíz y clave de la pasarela a mano, **un parte de la obra 404 recorrido entero
por el front** —subido, validado `apto`/`archivo_y_cierre`, **guardado** y
**archivado**, porque `postventa.graficos` tiene clave ajena contra `partes` y
sin eso falla **hasta el dry-run**—, autorización expresa del humano para esa
reclamación, y sesión iniciada en el front con **un solo parte** en curso.

**Aviso que hay que leer antes de abrir la ventana**: `CIERRE_HABILITADO` es
**una sola** para el gráfico y el cierre (D-B). Abrirla para probar el gráfico
**abre también el cierre**. Es aceptable —dry-run por omisión, confirmación
explícita, el humano delante— y de hecho la verificación quiere cerrar la
reclamación de prueba después de adjuntar, pero no puede ser una sorpresa.

### 8.3 · T33 y T34

- **T33** · la campaña de mutación: §7.1, con el comando y el coste estimado.
- **T34** · `bash harness/init.sh`: **se ha ejecutado y está en verde** (es
  precondición del implementer), pero la tarea **no se marca**, porque el
  encargo la reserva.

---

## 9 · Lo que quedó fuera del alcance, a propósito

Nada de esto se ha implementado, y `requirements.md` lo declara fuera:

- **borrar o sustituir** adjuntos, y **versionar** (`graant`);
- **reparar gráficos huérfanos**: los que la pasarela avise se **enseñan** en el
  dry-run (R21) y no se tocan;
- **el gráfico por URL** (F-023), que el humano canceló el 2026-09-06;
- **cualquier cosa del catálogo del portal**.

Y dos decisiones que se dejaron como estaban:

- **`ErpPort` no cambia.** «Tres métodos y ni uno más»: el gráfico tiene su
  puerto propio.
- **No se recalcula la huella de páginas** del PDF recibido para compararla con
  `hash` (D-H). F-002 avisa de que esa igualdad no está garantizada por
  construcción, y una comprobación que fallara sola mandaría partes buenos a un
  409. Lo que sí se comprueba es la integridad **del transporte**: `sha256`
  calculado aquí y cotejado por la pasarela.

---

## 10 · Preguntas abiertas que siguen abiertas

De `design.md` §14, dos siguen siendo del humano y **ninguna bloquea**:

- **P1** · ¿es `PV002` (`gratipide` 35) la clase correcta para un parte
  firmado? El nombre —«POSTVENTA:Fotos Reparaciones»— no lo dice; los datos sí
  (3.197 «PARTE FIRMADO» en esa clase). **Confirmar con Ana Bello / Alicia
  Echevarría.** Cambiarlo es una App Setting… **más un cambio en la lista
  blanca de la pasarela**: es una decisión de dos dueños.
- **P2** · ¿`res` = `PARTE FIRMADO` a secas? Implementado así. Cambiarlo es una
  constante del dominio.

Y una **observación fuera de encargo**, que ya venía de la sesión anterior y
esta feature hereda sin cambiarla: `peticion()` de `js/api.js` reintenta lo
transitorio (502, red, tiempo agotado) en **todos** los pasos, incluido
`adjuntar` con `commit`. **Aquí es seguro por construcción** —el endpoint es
idempotente por tamaño y `sha256`—, y se deja escrito para que nadie lo lea
como un reintento de escritura no controlado.
