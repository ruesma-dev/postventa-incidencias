<!-- progress/impl_H1_H2_despliegue.md -->
# H1 y H2 · La configuración de Sigrid entra en el despliegue, y el candado del cierre se rearma

> **Qué es esto.** El arreglo de los dos hallazgos de despliegue del §8 de
> `progress/guion_bloque8_F-009.md`, aprobado por el humano el **2026-09-03**.
> No es una feature: no se ha tocado `services/` salvo un test de F-010 cuya
> premisa cae con esta aprobación (§5, y está señalado ahí a propósito).
>
> **Nada se ha ejecutado contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint.** Ni una lectura. Los scripts se editan aquí; los
> ejecuta el humano.
>
> **Commits**: `82fbfb8` (scripts, documentación y test) y el de este informe,
> en `feature/F-009-cierre-sigrid`. En `azure-apps`, `9bc0518`. Sin `push` en
> ninguno de los dos.

---

## 1 · El cotejo completo: lo que espera el código contra lo que provee el despliegue

Fuentes: `services/postventa-api/config/settings.py` (38 campos con su
`validation_alias`), `infra/00_vars_postventa.ps1` y `infra/desplegar_backend.ps1`.
El cotejo se hizo **entero**, no solo sobre las tres variables que detectó el
guion, y destapó **dos más** de las previstas (`SIGRID_ZONA_HORARIA` y
`SIGRID_TIP_RECLAMACION`) más un hueco menor y antiguo en las de PostgreSQL.

Columna «Antes»: lo que había. Columna «Ahora»: lo que hay tras `82fbfb8`.

| Variable | Qué espera el código | Antes | Ahora | Veredicto |
|---|---|---|---|---|
| `ENTORNO` | **obligatoria**, sin defecto | `$ajustes`, `dev` | igual | OK |
| `NIVEL_LOG` | `INFO` | `$ajustes` | igual | OK |
| `IA_PROVIDER` | `gemini` | `$ajustes` | igual | OK |
| `GEMINI_API_KEY` | opcional; la exige la fábrica | referencia a Key Vault | igual | OK |
| `GEMINI_MODEL` | `gemini-3.7-flash` | `$ajustes` | igual | OK |
| `IA_TIMEOUT_S` | 120 | `$ajustes`, **35** (`$TIEMPO_IA_S`) | igual | OK · el despliegue baja el defecto a propósito: manda el proxy de 45 s |
| `IA_REINTENTOS` | 3 | `$ajustes` | igual | OK |
| `PROMPT_KEY`, `PROMPT_KEY_FIRMA`, `PROMPTS_YAML_PATH` | valores fijos | `$ajustes` | igual | OK |
| `PG_HOST`, `PG_USER`, `PG_PASSWORD` | opcionales; las exige la fábrica | referencia a Key Vault | igual | OK |
| `PG_PORT`, `PG_DB`, `PG_SCHEMA`, `PG_SSLMODE` | defectos | `$ajustes` | igual | OK |
| `PG_MAX_CONEXIONES` | 4 | **no está** | **no está** | Hueco menor · ver §6 |
| `PG_STATEMENT_TIMEOUT_S` | 30 | **no está** | **no está** | Hueco menor · ver §6 |
| `PG_LOCK_TIMEOUT_S` | 5 | **no está** | **no está** | Hueco menor · ver §6 |
| `PG_IDLE_IN_TRANSACTION_TIMEOUT_S` | 60 | **no está** | **no está** | Hueco menor · ver §6 |
| `ARCHIVO_HABILITADO` | `False` | `$ajustes`, `false` | igual | OK · se rearma en cada despliegue |
| `SHAREPOINT_SITE_ID`, `SHAREPOINT_DRIVE_ID` | opcionales | referencia a Key Vault | igual | OK |
| `SHAREPOINT_CARPETA_BASE` | `Postventa` | `$ajustes` | igual | OK |
| `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` | opcionales | referencia a Key Vault | igual | OK |
| `GRAPH_TIMEOUT_S`, `GRAPH_REINTENTOS` | 60 / 3 | `$ajustes`, 35 / 3 | igual | OK |
| **`CIERRE_HABILITADO`** | `False` | **NO ESTABA** | `$ajustes`, `false` | **H2, corregido** |
| **`SIGRID_API_BASE_URL`** | opcional; la exige `construir_erp` | **NO ESTABA** | referencia a Key Vault (`sigrid-api-base-url`) | **H1, corregido** |
| **`SIGRID_API_KEY`** | opcional; la exige `construir_erp` | **NO ESTABA** | referencia a Key Vault (`sigrid-api-key`) | **H1, corregido** |
| **`SIGRID_BASE_DATOS`** | opcional; la exige `construir_erp` | **NO ESTABA** | referencia a Key Vault (`sigrid-base-datos`) | **H1, corregido** |
| **`SIGRID_TIMEOUT_S`** | 35 | **NO ESTABA** | `$ajustes`, 35 (`$TIEMPO_SIGRID_S`) | **Destapado por el cotejo** |
| **`SIGRID_REINTENTOS`** | 3 | **NO ESTABA** | `$ajustes`, 3 | **Destapado por el cotejo** |
| **`SIGRID_TIP_RECLAMACION`** | 708 | **NO ESTABA** | `$ajustes`, 708 | **Destapado por el cotejo** |
| **`SIGRID_ZONA_HORARIA`** | `Europe/Madrid` | **NO ESTABA** | `$ajustes`, `Europe/Madrid` | **Destapado por el cotejo** · es la que decide el huso de `dbo.log` |
| `AZURE_CLIENT_ID` | no es un campo de `settings.py` | `$ajustes`, el `clientId` de la identidad | igual | OK · lo lee el SDK de Azure, no nosotros |

**Recuento**: 23 App Settings planas + 12 por referencia = **35**. Antes eran
19 + 9 = 28.

### Por qué el cotejo importó más de lo que parecía

El guion nombraba tres variables porque son las tres que hacen responder
`503 ConfiguracionSigridIncompleta`. Pero **`SIGRID_ZONA_HORARIA` no da error
al faltar**: se queda en su valor por defecto y todo funciona… hasta el paso 7
de T24, que es exactamente donde se mira si `fec`/`hor` de la fila nueva de
`dbo.log` están en hora local o en UTC. Era la única de las ocho que podía
producir un dato **silenciosamente distinto** del esperado en el ERP de
producción, y estaba fuera del despliegue. Ahora está escrita.

## 2 · H1 · Las ocho variables, y por qué **tres** secretos y no uno

El encargo hablaba de «el secreto» en singular y de «las variables no secretas
a `$ajustes`». Al escribirlo apareció un choque con una regla dura: `$ajustes`
está en el repositorio, y `SIGRID_API_BASE_URL` es **la raíz de la pasarela**
—un host interno— mientras que `SIGRID_BASE_DATOS` es **el nombre de la base de
producción del ERP**. Ninguno de los dos puede quedar escrito aquí; el propio
guion lo dice de los dos en su §3, y `00_vars_postventa.ps1` lo prohíbe en su
cabecera («ni FQDN»).

La salida **ya existía en el repositorio y no hubo que inventarla**: `pg-host`
está en el Key Vault y tampoco autentica nada; está ahí porque es un host. Los
tres de Sigrid siguen ese mismo camino:

- `infra/00_vars_postventa.ps1` · `$PostventaSecretosBackend` pasa de 9 a **12**
  nombres: `sigrid-api-base-url`, `sigrid-api-key`, `sigrid-base-datos`.
- `infra/00_vars_postventa.ps1` · `$PostventaAppSettingsSecretas` pasa de 9 a
  **12** entradas, con las tres App Settings correspondientes.
- `infra/desplegar_backend.ps1` · el bucle que ya existía compone la referencia
  `"@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/<nombre>)"` **con sus
  comillas**, que no son decoración: sin ellas `cmd.exe` interpreta los
  paréntesis (lo documenta el propio script). No se ha tocado ese bucle: al
  declarar las tres en el mapeo, salen ya con el formato correcto.

Efecto lateral buscado: **ninguna de las tres se escribe en
`desplegar_backend.ps1`**. Ahí solo quedan las cuatro de tiempos y
configuración de la instalación, cuyos valores ya viven en `settings.py`.

Las cinco planas van a `$ajustes`, con `SIGRID_TIMEOUT_S` a través de una
constante nueva `$TIEMPO_SIGRID_S = 35`, para que juegue en el mismo escalonado
declarado 35 / 40 / 45 que ya vigila un test.

## 3 · H2 · El candado que no se rearmaba

`CIERRE_HABILITADO=false` entra en `$ajustes` **inmediatamente después de
`ARCHIVO_HABILITADO=false`**, con su comentario propio: por qué está ahí, qué
protege, que se enciende a mano y se vuelve a apagar, y que es una variable
aparte porque poder archivar no puede implicar poder escribir en el ERP.

`docs/DESPLIEGUE.md` §4 bis decía algo falso —que se desplegaba apagado «igual
que el de archivo y **por el mismo mecanismo**»—. Ahora:

- describe el mecanismo real: `desplegar_backend.ps1` lo fija en `$ajustes`, así
  que cada despliegue lo devuelve a `false`;
- **deja escrito que hasta el 2026-09-03 no era verdad**, y por qué el fallo era
  difícil de ver: el valor por defecto del código solo se aplica *mientras la
  App Setting no exista*, de modo que el documento habría sido cierto justo
  hasta la primera vez que alguien encendiera la ventana;
- reescribe la tabla de las ocho variables diciendo, para cada una, **cómo** se
  despliega (referencia o `$ajustes`).

La cabecera de `desplegar_backend.ps1` se reescribió en el mismo sentido: donde
decía «NINGUNA VARIABLE DE SIGRID» ahora explica qué entra, qué no y por qué,
con fecha.

## 4 · Lo demás que había que dejar coherente

- `infra/cargar_secretos_postventa.ps1`: era «SON NUEVE, NO ONCE»; ahora son
  **doce de catorce**. Se actualizaron la cabecera, la ayuda de `-Solo` y las
  dos líneas que imprime al final.
- `docs/DESPLIEGUE.md`: los cinco sitios que contaban «nueve/once» y la lista de
  credenciales a preparar, con nota de que las tres de Sigrid las da el dueño de
  `sigrid-api` y de que **dejarlas vacías no rompe el resto del despliegue**.
- `progress/guion_bloque8_F-009.md`: §1 deja de ser un hallazgo bloqueante y
  pasa a decir qué pone ya el despliegue y qué queda a mano; el **Paso 0** sigue
  ahí —no se ha borrado— con dos caminos: el limpio (subir los tres secretos y
  redesplegar) y el del **entorno ya desplegado sin esas variables**, que es el
  caso real de hoy, con las líneas `az` actualizadas para que las tres vayan por
  referencia y no en claro. P3 y el paso 1 de §6 se ajustaron, y la tabla del §8
  marca H1 y H2 como resueltos con su commit.
- `azure-apps/postventa_incidencias.md` (commit `9bc0518`, sin `push`): apartado
  nuevo en §3 bis con los tres secretos del vault, por qué dos de ellos son
  secretos sin ser credenciales, y las dos consecuencias para el dueño de
  `sigrid-api` (cómo se absorbe una rotación de clave; el interruptor se
  despliega apagado). Las filas de la tabla de variables dicen ahora por dónde
  llega cada una. **No se duplicó nada de `sigrid_api.md`: se enlaza.**

## 5 · Un test de F-010 hubo que cambiarlo, y esto hay que leerlo

**El encargo decía «no toques `services/` ni sus tests». Se ha tocado un
fichero de tests, y es imposible no hacerlo.**

`services/postventa-api/tests/test_f010_scripts_infra.py` tenía este test:

```python
def test_f010_r28_ninguna_variable_de_sigrid_entra_en_el_despliegue(backend):
    assert re.findall(r"\bSIGRID_[A-Z_]+", backend) == []
```

Es R28 de F-010, escrito cuando **F-008 y F-009 estaban fuera del piloto**.
Cualquier arreglo de H1 lo pone en rojo por construcción: exige literalmente lo
contrario de lo aprobado hoy. No hay forma de tener H1 arreglado y `init.sh` en
verde con ese test como está, y **esquivarlo escondiendo las variables en otro
fichero para que la aserción siguiera pasando habría sido peor**: dejaría un
guardián verde vigilando algo que ya no es cierto.

Lo que se hizo, y por qué se cree que es lo correcto:

- **Cae la premisa** («el ERP está fuera del piloto»), que la aprobación del
  humano del 2026-09-03 invalida.
- **No cae lo que R28 protegía de verdad**, y eso es lo que el test comprueba
  ahora: que `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` y `SIGRID_BASE_DATOS` **no
  se escriben en el script**, y que las únicas `SIGRID_*` que aparecen son
  exactamente las cuatro de tiempos y configuración de la instalación.
- Se **añade** `test_f010_h2_el_cierre_se_despliega_apagado_y_cada_despliegue_lo_rearma`,
  espejo del que ya vigilaba `ARCHIVO_HABILITADO`: es lo que impide que H2
  vuelva a pasar.
- Se amplió la lista de `test_f010_t3_declara_todos_los_secretos_del_key_vault`
  con los tres nombres nuevos —si no, el cargador y el desplegador podrían
  discrepar sin que nadie se enterara— y se corrigieron dos comentarios que
  decían «nueve».

**Lo que NO se ha tocado**: ni una línea de código de `services/`, ningún otro
test, ni `specs/F-010-despliegue/requirements.md`. **R28 queda escrito en la
spec de F-010 con su texto original y ya no describe el sistema.** Es una
decisión para el humano: o se anota ahí la enmienda con fecha, o se acepta que
la trazabilidad de R28 apunta a un test que hoy comprueba otra cosa. Se deja
señalado en vez de decidirlo por cuenta propia.

## 6 · Lo que queda por hacer a mano, y lo que queda fuera

**A mano, una vez, antes de T22** (§1 del guion):

1. Subir los tres valores al Key Vault. **Los da el dueño de `sigrid-api`**, no
   se deducen y no pueden entrar al repositorio. `cargar_secretos_postventa.ps1`
   los pide a ciegas; se lanza con `-Command`, **no con `-File`** (con `-File`,
   `-Solo` no llega y pediría los doce).
2. Desplegar el backend, que es lo que fija las App Settings. **O**, si no se
   quiere redesplegar el entorno actual —desplegado antes de este arreglo—, las
   dos líneas `az` del final de §1 del guion.
3. Comprobar en el portal que ninguna referencia a Key Vault sale con error.

**Fuera de alcance, señalado y no tocado:**

- **Cuatro variables de PostgreSQL** (`PG_MAX_CONEXIONES`,
  `PG_STATEMENT_TIMEOUT_S`, `PG_LOCK_TIMEOUT_S`,
  `PG_IDLE_IN_TRANSACTION_TIMEOUT_S`) **no están en el despliegue** y nunca lo
  estuvieron: viven de su valor por defecto. No es un fallo funcional —los
  defectos son los correctos y son los que la fábrica quiere— pero sí una
  asimetría con `IA_*` y `GRAPH_*`, que sí se fijan. Es de F-005/F-010 y no
  estaba en el encargo: **no se ha tocado**.
- `infra/verificar_despliegue.ps1` mira `ARCHIVO_HABILITADO` antes de su segunda
  comprobación, y **no mira `CIERRE_HABILITADO`**. Hoy no le hace falta (no
  llama a `/api/cerrar`), pero sería el sitio natural de un aviso «la ventana
  del ERP está abierta». No estaba en el encargo.
- `specs/F-010-despliegue/requirements.md` R28, según §5.
- Ninguna tarea del bloque 8 ni T29 se ha marcado, y **ningún estado de feature
  se ha cambiado**.

## 7 · Cómo se verificó, sin ejecutar nada contra Azure

1. **Sintaxis de PowerShell, parseando y no ejecutando.** Los tres `.ps1`
   modificados, con el propio parser de PowerShell:

   ```
   [System.Management.Automation.Language.Parser]::ParseFile($ruta, [ref]$tokens, [ref]$errores)
   ```

   Salida real:

   ```
   OK sintaxis: infra\00_vars_postventa.ps1 (383 tokens)
   OK sintaxis: infra\desplegar_backend.ps1 (2073 tokens)
   OK sintaxis: infra\cargar_secretos_postventa.ps1 (981 tokens)
   ```

   `ParseFile` construye el AST completo: detecta cualquier error de sintaxis
   —una comilla sin cerrar en el array de `$ajustes`, un `@(` sin cerrar— sin
   ejecutar ni una instrucción.

2. **Los tests de contrato de los scripts**, que es lo que de verdad los vigila:
   `test_f010_scripts_infra.py` (141 casos con `test_f009_documentacion.py`) y
   después la suite entera del servicio.

3. **El portero del arnés**, `bash harness/init.sh`, en verde.

**No se ejecutó**: ningún script de `infra/`, ningún `az`, ninguna llamada a
Sigrid, a `sigrid-api`, al PostgreSQL compartido ni a SharePoint. Ni lecturas.
Tampoco se hizo `git push` en ninguno de los dos repositorios.

## 8 · Fase RED

**No aplica en su forma habitual, y conviene decir por qué en vez de fingirla.**
Este trabajo **no escribe código de producción**: cambia dos scripts de
despliegue, documentación, y un test. Los scripts de `infra/` no son ejecutables
por la suite (son PowerShell contra Azure); lo que los vigila son tests de
contrato sobre su texto, que ya existían.

Lo que sí hay es la evidencia inversa, y es real: **el test que había estaba
verde sobre un mundo que ya no existe, y el cambio lo puso en rojo**. Traza
pegada, con el comando exacto:

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f010_scripts_infra.py tests/test_f009_documentacion.py -q

_______ test_f010_r28_ninguna_variable_de_sigrid_entra_en_el_despliegue _______

    def test_f010_r28_ninguna_variable_de_sigrid_entra_en_el_despliegue(backend):
>       assert re.findall(r"\bSIGRID_[A-Z_]+", backend) == []
E       AssertionError: assert ['SIGRID_TIME...ZONA_HORARIA'] == []
E         Left contains 4 more items, first extra item: 'SIGRID_TIMEOUT_S'

tests\test_f010_scripts_infra.py:533: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f010_scripts_infra.py::test_f010_r28_ninguna_variable_de_sigrid_entra_en_el_despliegue
1 failed, 139 passed, 3 skipped in 1.55s
```

Ese rojo **es el hallazgo**, no un accidente: dice con precisión qué premisa
había que revisar (§5) y confirma que las cuatro variables planas nuevas —y solo
esas cuatro— llegaron al script.

El test nuevo de H2 se comprobó en los dos sentidos. Que pasa, en la ejecución
de §7. Que fallaba antes, contra el script tal y como estaba en el commit
anterior (`4610b7d`), sin necesidad de reconstruir nada:

```
$ git show 4610b7d:infra/desplegar_backend.ps1 | grep -c "CIERRE_HABILITADO"
0
```

Cero ocurrencias: la aserción `"CIERRE_HABILITADO=false" in cuerpo` era **falsa**
en el script anterior, que es precisamente el defecto H2. El test es lo que
impide que vuelva.

## 9 · Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados · servicio `api` | **1595 pasados, 13 saltados**, 0 fallos (`pytest -q` con el venv del servicio) |
| Tests ejecutados · suite del arnés (raíz) | **56 pasados**, 0 fallos |
| Tests ejecutados · servicio `front` | en verde por caché del portero (árbol sin cambios: no se tocó `services/postventa-front`) |
| Tiempo de ejecución · servicio `api` | **41,39 s** |
| Tiempo de ejecución · suite del arnés | **6,62 s** |
| Cobertura de las líneas cambiadas | **98,8 % de 572 líneas** (565/572, umbral 80 %, nivel `critico`), tal y como la mide la línea `PUERTA COBERTURA` de `harness/init.sh`. **El número es el de F-009 y no lo mueve este trabajo**: las líneas que se han cambiado aquí son PowerShell, Markdown y un test, y la puerta solo mide Python de producción |
| Mutantes generados y supervivientes | **No aplica.** La campaña de mutación se lanza sobre el código Python de una feature; aquí no se ha modificado ni una línea de código de producción. La de F-009 está cerrada (T28) y sigue en `progress/mutacion_F-009.md`, intacta |
| Validación de los scripts | 3 de 3 `.ps1` parseados sin errores; **0 ejecuciones** |

## 10 · Ficheros tocados

**`postventa-incidencias`** (commit `82fbfb8`, más este informe):

- `infra/00_vars_postventa.ps1` — 3 secretos y 3 mapeos nuevos.
- `infra/desplegar_backend.ps1` — cabecera reescrita, `$TIEMPO_SIGRID_S`, cinco
  App Settings nuevas en `$ajustes`, resumen y comprobaciones manuales.
- `infra/cargar_secretos_postventa.ps1` — recuentos y ayuda.
- `docs/DESPLIEGUE.md` — §2 (recuentos y preparación), §4 bis (reescrita).
- `services/postventa-api/tests/test_f010_scripts_infra.py` — ver §5.
- `progress/guion_bloque8_F-009.md` — §1, P3, §6 y la tabla del §8.
- `progress/impl_H1_H2_despliegue.md` — este informe.
- `progress/current.md` — rastro.

**`azure-apps`** (commit `9bc0518`, sin `push`):

- `postventa_incidencias.md` — §3 bis y la tabla de variables de Sigrid.

---

# Correcciones del 2026-09-03 (sección añadida; el informe de arriba no se ha reescrito)

> **Qué es esto.** Dos correcciones aprobadas por el humano el mismo día, sobre
> el trabajo de H1/H2 que acababa de aterrizar. **Quirúrgicas**: no reescriben
> nada de lo anterior, corrigen dos cosas concretas que quedaron mal.
>
> **Commits**: `bed95ea` (scripts y test), `a6669c3` (documentación),
> `2855955` (spec de F-010) y el de esta sección. En `azure-apps`, `0b31237`.
> **Sin `push` en ninguno de los dos.**
>
> **Nada se ha ejecutado contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint. Ni una lectura.**

## 11 · Corrección 1 · `SIGRID_BASE_DATOS` baja de secreto de vault a App Setting plana

### El error que se corrige, dicho sin adornos

El §2 de arriba defendió **tres** secretos de vault. Dos estaban bien
—`sigrid-api-key` es una credencial, y `sigrid-api-base-url` es un host interno,
que es el caso de `pg-host`—. El tercero fue **exceso de celo**: el argumento
era que el nombre de la base de producción del ERP no puede quedar escrito en el
repositorio, y **ya lo estaba**.

Lo que costaba, y por eso importa: un secreto de vault hay que **subirlo a mano
en cada entorno**, a ciegas, y cada aprovisionamiento manual es una oportunidad
de que un despliegue quede a medias. Se pagaba ese precio a cambio de nada.

### Una precisión sobre el encargo, porque el número no salía

El encargo daba **seis** documentos donde el nombre ya está escrito. Al
comprobarlo uno a uno, el literal aparece como **nombre de base de datos** en
**dos**:

| Documento | Dónde |
|---|---|
| `docs/referencia/03_modelo_posventa_sigrid.md` | la cabecera («bases `ruesma` y `ruesma_rep`») y luego como prefijo de tabla en media docena de sitios (`ruesma.gra`, `ruesma.gra.ima`…) |
| `specs/F-009-cierre-sigrid/design.md` | «**Base**: la de negocio (`ruesma`), la única con escritura permitida», y el bloque de las dos tablas `gra` |

En `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` y las dos specs de F-010 la
palabra sí aparece, pero **como parte de `swa-postventa-ruesma`**, que es el
nombre de la Static Web App y no el de la base; esos cuatro documentos hablan de
«la base de negocio» **sin nombrarla**.

**Esto no cambia la decisión, y por eso se ha ejecutado igual**: dos documentos
versionados en git bastan —uno de ellos es la documentación de referencia del
sistema origen, que es justo donde alguien iría a buscarlo—, y el historial de
git no suelta lo que entra. Se anota porque un informe que repite un número que
no sale es exactamente el tipo de cosa que luego nadie vuelve a comprobar.

### Qué se tocó

| Fichero | Qué |
|---|---|
| `infra/00_vars_postventa.ps1` | `sigrid-base-datos` fuera de `$PostventaSecretosBackend` (12 → **11**) y fuera de `$PostventaAppSettingsSecretas`. Los dos comentarios reescritos: el de cabecera ya no dice «LOS TRES DE SIGRID» sino **«LOS DOS»**, y da **el motivo de cada uno por separado** (una es una credencial, la otra un host interno); debajo, por qué el tercero **no** está |
| `infra/desplegar_backend.ps1` | `"SIGRID_BASE_DATOS=ruesma"` en `$ajustes`, con su comentario. Cabecera reescrita: «los **once** que identifican o autentican», y la enumeración de qué entra por referencia (dos) y qué en claro (cinco). También el comentario del bucle de referencias y la línea del resumen que decía «las tres de Sigrid» |
| `infra/cargar_secretos_postventa.ps1` | «SON DOCE, NO CATORCE» → **«SON ONCE, NO TRECE»**; el `.SYNOPSIS`, la ayuda de `-Solo` («las otras **diez**») y las dos líneas que imprime al final |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | ver abajo |
| `docs/DESPLIEGUE.md` | §2: el recuento en la tabla de scripts, el epígrafe «Son **once** secretos, no **trece**», la partición de la lista, el párrafo de los de Sigrid y la preparación a mano (punto 2). §4 bis: «las **dos** sensibles / las otras **seis**», la fila de la tabla, el porqué reescrito y el comando `-Solo` final |
| `progress/guion_bloque8_F-009.md` | §1 entero (intro, tabla, Paso 0, la línea `-Solo`, las dos líneas `az` del entorno ya desplegado), P3, el diagnóstico del 503 del paso 2 de T22 y la fila **H1** del §8 |
| `azure-apps/postventa_incidencias.md` | §3 bis: la tabla de secretos pierde su tercera fila y gana un párrafo diciendo que `SIGRID_BASE_DATOS` es plana y por qué; y la fila de la tabla de variables |

### El test sigue siendo igual de estricto, y en un punto lo es más

En `test_f010_r28_la_configuracion_sensible_de_sigrid_no_se_escribe_aqui`:

- `sensibles` pasa de tres a **dos**. La comprobación que importa —que
  `SIGRID_API_BASE_URL` y `SIGRID_API_KEY` **no aparezcan escritas** en
  `desplegar_backend.ps1`— **no se ha tocado ni una coma**.
- `SIGRID_BASE_DATOS` se mueve al conjunto de las que **sí** pueden versionarse,
  que pasa de cuatro a cinco y sigue siendo una **igualdad de conjuntos**: ni
  una `SIGRID_*` de más en el script pasa desapercibida.

Y una aserción **nueva**, en `test_f010_t3_declara_todos_los_secretos_del_key_vault`:

```python
assert '"sigrid-base-datos"' not in variables
```

No es celo simétrico. Sin ella, alguien puede volver a declararlo como secreto
por inercia y dejarlo fijado **por partida doble** —plano en `$ajustes` y por
referencia en el bucle—, que es un estado que el despliegue no rechaza y que
nadie mira.

> **Un detalle que el test enseñó y conviene saber**: la aserción
> `SIGRID_API_BASE_URL not in backend` corre sobre el fichero **entero,
> comentarios incluidos**. El primer intento de reescribir la cabecera de
> `desplegar_backend.ps1` las nombraba para explicar qué va por referencia, y el
> test se puso rojo con razón. La cabecera se reescribió sin nombrarlas, y lo
> deja dicho: «NI SUS NOMBRES SE ESCRIBEN AQUI … y por eso esta cabecera tampoco
> las nombra».

## 12 · Corrección 2 · R28 de F-010 ya no describe un sistema que no existe

### Dónde estaba el texto

El §5 de arriba lo dejó señalado y sin decidir. Buscado en todo el árbol, el
texto de R28 con la premisa caída vivía en **tres sitios**, los tres en
`specs/F-010-despliegue/`:

| Sitio | Qué decía |
|---|---|
| `requirements.md`, el requisito | «mantener fuera del despliegue todo lo que no forma parte del piloto: **ninguna** variable de Sigrid; y cuando la ventana de escritura de R33 esté abierta…» |
| `requirements.md`, la tabla de trazabilidad | «Test: la plantilla de App Settings no incluye ninguna variable `SIGRID_*`» — apuntaba a un test que desde `82fbfb8` comprueba otra cosa |
| `tasks.md`, la verificación de **T5** | «**ninguna variable `SIGRID_*`** (R28)» |

**No está en el `design.md` de F-010**: R28 no aparece ahí, solo una mención de
pasada al cierre en Sigrid como fuera de alcance de F-010, que sigue siendo
cierta. **Tampoco en `CHECKPOINTS.md`**, que no nombra R28 ni ninguna variable
`SIGRID_*`.

### Qué se hizo, y qué deliberadamente no

- **Se corrige el requisito, no se reinterpreta.** R28 dice ahora que lo que se
  mantiene fuera de la plantilla es **la configuración sensible** —la raíz de la
  pasarela y su clave de función—, que viaja por referencia a Key Vault. **La
  segunda mitad de R28 no se toca**: el destino de la ventana de escritura sigue
  siendo solo la biblioteca de dev, y eso sigue vigente tal cual.
- **Constancia fechada debajo**, en un recuadro: la premisa original **citada
  literal**, cuándo se escribió y por qué era cierta entonces, qué la invalidó
  (la aprobación del humano del 2026-09-03) y el puntero al **hallazgo H1** de
  `progress/guion_bloque8_F-009.md` §8 y a este informe. Cierra diciendo que
  **F-010 sigue `done`** y que esto no reabre la feature.
- **No se ha reescrito la spec** ni ampliado su alcance: las tres correcciones
  necesarias y el recuadro, nada más.
- **No se ha tocado `progress/review_F-010.md`**, que en su tabla final sigue
  diciendo «R28 — ninguna variable `SIGRID_*` ✔». Es un **informe de revisión
  fechado**: describe lo que se verificó el día que se verificó, y corregirlo
  sería falsificar el registro. Queda anotado aquí para quien lo lea después.

## 13 · Cómo se verificó, otra vez sin ejecutar nada

1. **Fase RED, con la traza real.** El test se cambió **antes** que los scripts,
   y los puso en rojo por los dos motivos correctos:

   ```
   $ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f010_scripts_infra.py -q

   ____________ test_f010_t3_declara_todos_los_secretos_del_key_vault ____________
   >       assert '"sigrid-base-datos"' not in variables
   E       assert '"sigrid-base-datos"' not in '# infra/00_...'
   E         '"sigrid-base-datos"' is contained here:
   E           key",
   E               "sigrid-base-datos"
   E           )

   _ test_f010_r28_la_configuracion_sensible_de_sigrid_no_se_escribe_aqui _
   >       assert set(re.findall(r"\bSIGRID_[A-Z_]+", backend)) == {
   E       AssertionError: assert {'SIGRID_REIN...ZONA_HORARIA'} == {'SIGRID_BASE...ZONA_HORARIA'}
   E         Extra items in the right set:
   E         'SIGRID_BASE_DATOS'

   2 failed, 117 passed, 3 skipped in 0.54s
   ```

   El primer rojo dice que el secreto seguía declarado en
   `00_vars_postventa.ps1`; el segundo, que la App Setting plana todavía no
   estaba en `desplegar_backend.ps1`. **Son exactamente los dos cambios que había
   que hacer, ni uno más.**

   Después de tocar los tres scripts: `141 passed, 3 skipped in 0.38s`
   (`test_f010_scripts_infra.py` + `test_f009_documentacion.py`).

2. **Sintaxis de PowerShell, parseando y no ejecutando.** Los tres `.ps1`, con el
   parser del propio PowerShell
   (`[System.Management.Automation.Language.Parser]::ParseFile`). Salida real:

   ```
   OK sintaxis: infra\00_vars_postventa.ps1 (408 tokens)
   OK sintaxis: infra\desplegar_backend.ps1 (2094 tokens)
   OK sintaxis: infra\cargar_secretos_postventa.ps1 (981 tokens)
   ```

   Construye el AST entero sin ejecutar una sola instrucción. Los dos primeros
   ganan tokens respecto a la medición del §7 (383 y 2073) porque ganan
   comentarios y una entrada de `$ajustes`.

3. **El portero del arnés**, `bash harness/init.sh`, en verde.

**No se ejecutó**: ningún script de `infra/`, ningún `az`, ninguna llamada a
Sigrid, a `sigrid-api`, al PostgreSQL compartido ni a SharePoint. Ni lecturas.
Ningún `git push`. **No se tocó el repositorio `sigrid-api`**; y en `azure-apps`,
`sigrid_api.md` estaba modificado por el humano y se ha dejado **sin tocar y sin
añadir al commit**.

## 14 · Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados · servicio `api` | **1595 pasados, 13 saltados**, 0 fallos |
| Tests ejecutados · suite del arnés (raíz) | **56 pasados**, 0 fallos |
| Tests ejecutados · servicio `front` | en verde por caché del portero (no se tocó `services/postventa-front`) |
| Tiempo de ejecución · servicio `api` | **32,00 s** |
| Tiempo de ejecución · suite del arnés | **2,95 s** |
| Cobertura de las líneas cambiadas | **98,8 % de 572 líneas** (565/572, umbral 80 %, nivel `critico`). **Idéntica a la del §9, y por el mismo motivo**: lo cambiado aquí es PowerShell, Markdown y un test, y la puerta solo mide Python de producción |
| Mutantes generados y supervivientes | **No aplica.** No se ha modificado ni una línea de código de producción. La campaña de F-009 sigue cerrada en `progress/mutacion_F-009.md`, intacta |
| Validación de los scripts | 3 de 3 `.ps1` parseados sin errores; **0 ejecuciones** |
| Estados de feature cambiados | **Ninguno.** Ni tareas del bloque 8, ni T29, ni `harness/features.json` |

## 15 · Lo que sigue pendiente tras estas correcciones

- **A mano, antes de T22**: subir al Key Vault **dos** valores, no tres
  (`sigrid-api-base-url` y `sigrid-api-key`). Los da el dueño de `sigrid-api`. El
  Paso 0 del §1 del guion está actualizado, con sus dos caminos.
- Lo del §6 sigue igual y sin tocar: las cuatro variables de PostgreSQL fuera del
  despliegue, `verificar_despliegue.ps1` sin mirar `CIERRE_HABILITADO`, y H3–H6
  del guion abiertos.
- `progress/review_F-010.md` conserva a propósito la redacción vieja de R28 (§12).
