<!-- progress/impl_paso0_sigrid.md -->
# Dos correcciones fuera de feature · 2026-09-06

> **Encargo aprobado por el humano el 2026-09-06.** No es una feature: son dos
> correcciones sobre el trabajo de H1/H2 y sobre el Paso 0 del bloque 8 de
> F-009. **Ningún estado de `harness/features.json` cambia.** F-009 sigue
> `in_progress`, F-023 sigue `blocked`.
>
> **NO se ha ejecutado NADA contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint. Ni lecturas.** Todo lo que se verificó se verificó
> con tests, con el analizador de sintaxis de PowerShell y con un banco de
> pruebas que sustituye `az` por un doble en memoria (ver §3.2).
>
> Rama `feature/F-009-cierre-sigrid`, commits locales, **sin `push`**.

---

## 1 · Qué se ha hecho, en dos líneas

1. **Corrección 1** (`32d40f5`) · El fragmento de consola del bloque 8 leía la
   raíz de la pasarela y el host de PostgreSQL con `az functionapp config
   appsettings list`. Ese comando devuelve el valor **crudo**, y las dos son
   **referencias a Key Vault**: lo que salía era la cadena
   `@Microsoft.KeyVault(SecretUri=...)`, no la URL ni el host. Las dos pasan a
   `Read-Host`.
2. **Corrección 2** (`1223bde`) · `infra/14_paso0_sigrid.ps1`: el Paso 0 del
   bloque 8 —dos secretos, ocho App Settings y la comprobación de que las
   referencias se resuelven— en un solo script, con veredicto y código de
   salida. Incluye la comprobación que hasta hoy **solo se podía hacer mirando
   el portal**.

---

## 2 · Corrección 1 · la raíz de la pasarela y `PG_HOST` se teclean

### El defecto

Lo había anotado el propio informe de H1/H2 como «observación fuera de encargo,
NO corregida» (commit `c3fa55d`). El diagnóstico era correcto y estaba
**incompleto en un punto**: no era una línea, eran **dos**.

`az functionapp config appsettings list ... --query "[?name=='X'].value"`
devuelve lo que está **escrito** en la App Setting. Cuando la App Setting es una
referencia a Key Vault, lo escrito es la cadena
`@Microsoft.KeyVault(SecretUri=...)`. Azure resuelve esa referencia **al arrancar
la Function**, no en la API de gestión: por esa vía **no hay forma** de leer el
valor resuelto. Quien siguiera el guion se habría encontrado un
`Invoke-RestMethod` contra una URI imposible, y un `$env:PG_HOST` con una cadena
de Key Vault dentro.

### Qué se cambió

Se buscó con `grep` por todo `progress/`, `docs/`, `infra/` y `specs/` el patrón
sobre las **once** App Settings referenciadas (las claves de
`$PostventaAppSettingsSecretas`). Hay cinco ocurrencias más de
`appsettings list`, y **ninguna es defectuosa**:

| Dónde | Qué lee | Veredicto |
|---|---|---|
| `progress/current.md` (Paso 0) | `SIGRID_API_BASE_URL` | **defectuosa · corregida** |
| `progress/current.md` (T23) | `PG_HOST` | **defectuosa · corregida** |
| `progress/current.md` (Paso 0) | `SIGRID_BASE_DATOS` | correcta: App Setting plana desde `bed95ea` |
| `progress/current.md` (cerrar ventana) | `CIERRE_HABILITADO` | correcta: plana |
| `infra/verificar_despliegue.ps1` | `ARCHIVO_HABILITADO` | correcta: plana |
| `specs/F-010-despliegue/tasks.md` | `ARCHIVO_HABILITADO` | correcta: plana |
| `progress/spec_F-009.md` | App Settings de **otro** proyecto (`sigrid-api`) | correcta: planas, y es el registro de una comprobación ya hecha |

Las dos defectuosas pasan a `Read-Host`, que es lo que ya se hacía con la clave
de función: **son un host interno y una URL, se teclean y no se escriben en
ningún fichero**. Cada una lleva encima el comentario que dice por qué no se lee
con `az`, para que no se reintroduzca al primer «esto se puede automatizar».

En `progress/guion_bloque8_F-009.md` §3, subsección «Cómo se les pasa el destino
y la clave», queda el recuadro con el porqué completo y con la salida que sí
existe: comprobar el **estado** de la referencia (`Resolved`), que no es su
valor. Y en `progress/impl_H1_H2_despliegue.md`, el recuadro de la observación
gana una línea que dice que se corrigió el 2026-09-06 en `32d40f5` (el recuadro
original no se ha reescrito).

---

## 3 · Corrección 2 · `infra/14_paso0_sigrid.ps1`

### 3.1 · Qué hace y qué decisiones lleva dentro

Cinco pasos, en orden, tal como los pedía el encargo:

1. **Precondiciones**: `az` en el PATH (salida `3`), sesión iniciada (`2`), Key
   Vault del proyecto existente (`7`). Todas son lecturas.
2. **Los dos secretos**: `& "$PSScriptRoot\cargar_secretos_postventa.ps1" -Solo
   $secretosSigrid`.
3. **Las App Settings**: `& "$PSScriptRoot\desplegar_backend.ps1" -SinPublicar`,
   **propagando su código de salida** si falla.
4. **El estado de las referencias**: `az rest --method get` contra
   `.../config/configreferences/appsettings?api-version=2022-03-01`, tabla
   `NOMBRE -> estado` de las once, y veredicto.
5. **`-WhatIf`**: solo lecturas —precondiciones y el punto 4 sobre el estado
   actual—, sin invocar a ninguno de los dos scripts que escriben.

Decisiones que conviene dejar explícitas:

- **No añade una tercera confirmación escrita.** No está en
  `NOMBRES_QUE_ESCRIBEN` del test porque **no escribe**: sus llamadas directas
  de `az` son todas lecturas (hay un test que lo comprueba con el mismo patrón
  `PATRON_ESCRITURA_AZ` que usa el resto del fichero). Lo que escribe lo
  escriben los dos scripts que invoca, y cada uno pide **su** palabra
  (`CARGAR`, `DESPLEGAR`). Una tercera puerta no protegería nada y sí añadiría
  una ocasión de confundirse contando cuántas veces hay que teclear qué.
- **Los nombres de los dos secretos no se escriben.** Salen de
  `$PostventaAppSettingsSecretas` filtrando las claves `SIGRID_*`. Si mañana
  hubiera un tercero entraría solo; escrito a mano se habría quedado fuera en
  silencio, que es exactamente como el Paso 0 vuelve a quedarse a medias.
- **`-Solo` funciona aquí** porque se invoca con el operador de llamada desde
  una sesión de PowerShell, no con `powershell -File`. Comprobado leyendo la
  declaración: `[string[]]$Solo = @()`; el problema documentado en
  `docs/DESPLIEGUE.md` §2 es del enlace de argumentos de `-File`, y con `&` el
  array llega entero. Verificado en ejecución (§3.2).
- **El identificador de suscripción se lee en ejecución y no sale de ahí**:
  `az account show --query id`, vive en memoria, no se imprime, no se escribe.
  Hay un test que prohíbe cualquier `Write-Host` que lo mencione.
- **El veredicto cuenta, no afirma**: «11/11» se compone con
  `$PostventaAppSettingsSecretas.Count`. Un número escrito a mano miente el día
  que se añada o se quite un secreto, y miente diciendo que todo está bien.
- **Si `az rest` falla, no revienta y no sale en verde**: lo dice, remite al
  portal y sale con `11`. Misma regla que la guarda de
  `verificar_despliegue.ps1`: una comprobación que no se ha hecho no es una
  comprobación superada.
- **Lo que se imprime son nombres y estados, nunca valores.** Es lo que hace
  que este script exista: el plano de gestión publica si una referencia está
  `Resolved` y por qué no lo está, sin publicar jamás lo que hay detrás. Por
  eso la tabla se puede pegar en `progress/` sin redactar nada.

### 3.2 · Cómo se verificó, sin tocar Azure

**a) Análisis sintáctico con PowerShell.** Salida real:

```
PS> $e = $null
PS> $t = [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw infra/14_paso0_sigrid.ps1), [ref]$e)
PS> "errores de sintaxis: " + $e.Count + " (tokens: " + $t.Count + ")"
errores de sintaxis: 0 (tokens: 1152)
```

**b) Ejecución real del script, con `az` sustituido por un doble.** PowerShell
resuelve **funciones antes que ejecutables**, así que un `function az { ... }`
definido en la sesión que invoca al script impide por construcción que la
llamada llegue a la red. El banco vive en el directorio temporal de la sesión,
**no en el repositorio**, y arranca con una guarda: si el doble no estuviera en
efecto, aborta con código `99` antes de nada.

Cuatro escenarios, con `-WhatIf` (que es el modo que no invoca a los dos scripts
de escritura). Salida real, recortada:

```
===== MODO: todo-bien =====
  1. Secretos de Sigrid a cargar : 2
       - sigrid-api-base-url
       - sigrid-api-key
  3. Referencias a comprobar     : 11
-WhatIf: no se ha escrito nada. No se ha invocado ninguno de los
dos scripts que escriben. [...]
  PG_HOST                -> Resolved
  [...]
  SIGRID_API_BASE_URL    -> Resolved
  SIGRID_API_KEY         -> Resolved
Paso 0 COMPLETO: 11/11 referencias resueltas.
CODIGO DE SALIDA: 0

===== MODO: una-en-error =====
  SIGRID_API_KEY         -> InitializationError
Paso 0 INCOMPLETO: 10 de 11 referencias resueltas.
Las que no:
  SIGRID_API_KEY         -> Secret not found (motivo de mentira)
CODIGO DE SALIDA: 12

===== MODO: una-ausente =====
  SIGRID_API_KEY         -> AUSENTE
Paso 0 INCOMPLETO: 10 de 11 referencias resueltas.
Las que no:
  SIGRID_API_KEY         -> sin detalle: la App Setting no existe o no es una referencia.
CODIGO DE SALIDA: 12

===== MODO: sin-comprobacion =====
NO SE HA PODIDO COMPROBAR el estado de las referencias.
[...] comprueba a mano, en el portal, que ninguna App Setting [...]
CODIGO DE SALIDA: 11
```

Esto verifica de verdad —no por lectura— la derivación de los dos secretos desde
`$PostventaAppSettingsSecretas`, la composición de la URL del plano de gestión,
el parseo de la respuesta, el caso de la referencia **ausente** (que no es lo
mismo que la que está en error), la tabla, el veredicto contado y los cuatro
códigos de salida.

**c) La propagación del código de salida, aislada.** El banco de pruebas del
punto (b) llegó primero a decir `CODIGO DE SALIDA: 0` en todos los modos, y eso
era **un defecto del banco, no del script**: cargaba el script **por punto**, y
en PowerShell el `exit` de un script cargado por punto termina al llamante pero
**no propaga su código**. Comprobado con dos scripts de tres líneas:

```
directo=12       # powershell -File hijo.ps1        -> el proceso sale con 12
dot-source=0     # . .\hijo.ps1 dentro de otro      -> el proceso sale con 0
amp=0            # & .\hijo.ps1 dentro de otro      -> pero...
tras amp LASTEXITCODE=12
```

Dos conclusiones, y las dos importan:

1. **Como lo va a ejecutar el humano** (`powershell -File .\infra\14_paso0_sigrid.ps1`)
   el código de salida **sí** llega al proceso. La tabla del punto (b) se
   reprodujo cambiando el banco a `&`, y ahí los códigos salen correctos.
2. El mecanismo del que depende el paso 3 del script —`& desplegar_backend.ps1`
   y luego `exit $LASTEXITCODE`— es el de la última línea: `&` deja el código
   del script invocado en `$LASTEXITCODE`. Queda comprobado, no supuesto.

**d) Tests.** 13 tests nuevos propios más 5 del barrido común, en
`services/postventa-api/tests/test_f010_scripts_infra.py` (de 122 a 140 casos en
ese fichero). El script se añadió a `scripts_entregados()`, que es lo que le
aplica R1 (ruta relativa en la primera línea), R7 (ni un nombre de recurso
repetido) y R8 (ni un GUID, ni un FQDN, ni una IP, ni una credencial).

### 3.3 · Fase RED

Los tests se escribieron **antes** que el script. Comando y salida real:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f010_scripts_infra.py -k paso0 -q
tests\test_f010_scripts_infra.py:1435: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f010_scripts_infra.py::test_f009_paso0_el_script_existe - A...
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_carga_las_variables_por_punto
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_los_secretos_de_sigrid_se_derivan_y_no_se_escriben
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_llama_a_los_dos_scripts_y_no_duplica_lo_que_hacen
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_las_dos_escrituras_quedan_bajo_el_whatif
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_con_whatif_se_comprueba_igualmente_el_estado
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_propaga_el_codigo_de_salida_de_lo_que_invoca
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_cada_causa_de_fallo_tiene_su_codigo_y_ninguno_se_repite
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_la_suscripcion_se_lee_en_ejecucion_y_no_se_imprime
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_la_tabla_de_referencias_imprime_estados_y_no_valores
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_el_veredicto_cuenta_las_referencias_esperadas
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_si_la_comprobacion_no_se_puede_hacer_no_sale_en_verde
ERROR tests/test_f010_scripts_infra.py::test_f009_paso0_no_escribe_en_azure_por_su_cuenta
1 failed, 122 deselected, 3 warnings, 12 errors in 1.06s
```

(El `failed` es el que comprueba que el fichero existe; los doce `ERROR` son los
que dependen de la *fixture* que lo lee, que no podía leer lo que no había.)

Y **un test falló también después de escribir el script**, lo cual es la mitad
útil de la fase RED. Salida real:

```
        assert "-WhatIf: no se ha" in paso0
        fin_guarda = paso0.find("if (-not $WhatIf) {")
        comprobacion = paso0.find("configreferences/appsettings")
>       assert -1 < fin_guarda < comprobacion
E       assert 8957 < 6208
```

El test era el equivocado, no el script: la cadena `configreferences/appsettings`
aparece en la **definición** de la función `Leer-Referencias`, que en PowerShell
va antes de usarse, así que comparar posiciones de texto medía otra cosa. Se
reescribió para comparar contra la **llamada** (`$referencias = Leer-Referencias`),
que es lo que de verdad tiene que quedar fuera del `if/else` que decide si se
escribe. Queda anotado porque un test que se «arregla» sin entender por qué
fallaba es un test que ya no comprueba nada.

### 3.4 · La documentación que quedó coherente

- `progress/guion_bloque8_F-009.md`:
  - §1 · nuevo apartado «Paso 0 · en un solo script (recomendado)» con la línea
    de invocación, lo que se espera ver, el veredicto, los códigos de salida y
    el papel de `-WhatIf`. **La vía manual no se borra**: pasa a llamarse «Paso
    0, a mano (1) y (2)» y se conserva entera, incluida la sección «Si el
    entorno ya está desplegado y no se quiere redesplegar», cuya comprobación
    final ahora ofrece el script además del portal.
  - §2 · **P3** se comprueba con `-WhatIf` del propio script, y dice cuál es el
    texto que tiene que salir.
  - §3 · una nota tras la tabla del utillaje: hay un sexto script, no está en la
    tabla porque **no es de lectura del ERP** sino de aprovisionamiento, y se
    ejecuta una vez antes de todo.
- `docs/DESPLIEGUE.md`:
  - §2 · una línea tras la tabla de los cinco: hay un sexto que no es del
    despliegue y vive en el §4 bis.
  - §4 bis, «Las variables de Sigrid, y cuál es el secreto» · párrafo que
    describe el script, su veredicto y su `-WhatIf`. **No se reescribió** la
    tabla ni el resto de la sección.

---

## 4 · Ficheros tocados

| Fichero | Qué |
|---|---|
| `infra/14_paso0_sigrid.ps1` | **nuevo** · el Paso 0 en un script (ASCII, CRLF, sin BOM, como los demás) |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | 13 tests nuevos + el script entra en `scripts_entregados()` |
| `progress/current.md` | las dos líneas de `az` → `Read-Host`, y el bloque de estado de arriba |
| `progress/guion_bloque8_F-009.md` | §1, §2 (P3) y §3 |
| `docs/DESPLIEGUE.md` | §2 y §4 bis |
| `progress/impl_H1_H2_despliegue.md` | una línea en el recuadro de la observación |
| `progress/impl_paso0_sigrid.md` | este informe |

Commits locales, sin `push`:

| Commit | Qué |
|---|---|
| `32d40f5` | Corrección 1 |
| `1223bde` | Corrección 2 |
| *(este)* | El rastro: recuadro de H1/H2, informe y `current.md` |

**No se ha tocado `specs/F-012-grafico-sigrid/`**, que estaba escribiendo otro
subagente en paralelo. Los `git add` fueron por ruta, uno a uno.

---

## 5 · Lo que queda a mano (lo hace el humano)

1. **Ejecutar el script.** Ni siquiera se ha lanzado con `-WhatIf` contra el
   entorno real: el encargo prohibía toda llamada a Azure, lecturas incluidas.
   La primera ejecución de verdad es del humano, y el orden natural es
   `-WhatIf` primero —que solo lee y dice qué falta— y sin parámetros después.
2. **Los dos valores de Sigrid** siguen sin poder salir de ningún script: los da
   el dueño de `sigrid-api` y se teclean a ciegas. El script los pide; no los
   inventa.
3. **El bloque 8 sigue sin ejecutarse.** Ninguna casilla de T22–T27 se ha
   marcado, y nada se ha ejecutado contra el ERP.
4. **Sin verificar contra Azure**: que la versión de API `2022-03-01` del plano
   de gestión responde en esta suscripción, y que la sesión de `az` del humano
   tiene permiso de lectura sobre la Function App. Si alguna de las dos falla,
   el script **no revienta**: lo dice, remite al portal y sale con `11`. Ese
   camino está probado con el doble, pero contra Azure de verdad no.

---

## 6 · Evidencias

| Evidencia | Número real |
|---|---|
| **Tests ejecutados** (`bash harness/init.sh`, servicio `api`) | **1613 pasados, 13 saltados, 0 fallos** |
| Tests del fichero tocado | 140 recogidos (eran 122), **137 pasados + 3 saltados** |
| Tests que tocan el script nuevo | **18** (13 propios + 5 del barrido común) |
| **Cobertura de las líneas cambiadas** | **98.8 %** (565/572, umbral 80 %, nivel `critico`) — línea `PUERTA COBERTURA` de `init.sh` |
| **Tiempo de la suite** | **113.70 s** (1:53) el servicio `api`; 4.35 s la suite raíz |
| **Mutación** | **No aplica.** `harness/alcance.py` solo mide `.py`, y lo entregado aquí es un script PowerShell y documentación. Los tests que lo cubren son de texto sobre el fichero, no de ejecución de código Python: no hay líneas Python nuevas que mutar. Lo que sustituye a la mutación es (b) del §3.2: el script se ejecutó de verdad, con `az` sustituido, en cuatro escenarios, y se comprobó su salida y su código de salida en cada uno. |
| `ruff` sobre el fichero de tests | `All checks passed!` |
| Análisis sintáctico del `.ps1` | **0 errores**, 1152 tokens |
| Llamadas a Azure / Sigrid / PostgreSQL / SharePoint | **0** |
