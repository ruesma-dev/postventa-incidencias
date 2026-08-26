<!-- progress/impl_postreview3_F-010.md -->
# F-010 · ronda de correcciones tras la tercera review (`review3_F-010.md`)

- **Rama:** `feature/F-010-despliegue`
- **Fecha:** 2026-08-26
- **Origen:** `progress/review3_F-010.md` §9, puntos **9.1** y **9.3**.
- **Alcance:** **un test nuevo** y **texto de un script de `infra/`**. Ni una
  línea de lógica cambiada, ni una casilla `[x]` de ningún `tasks.md` movida,
  ni el estado de F-010 tocado en `harness/features.json`.
- **Fuera de alcance por encargo:** **§9.2** (R29 y la fila de `design.md`
  §6.4) — ya lo ha hecho el `spec-author`, `progress/spec_postreview3_F-010.md`,
  y **no se ha tocado**— y el resultado de **T14 bis**, que lo aporta el humano.
- **Permiso nuevo de esta ronda:** el humano ha autorizado hoy **tocar
  `infra/`**. Era lo único que faltaba para el 9.3: en la ronda anterior el
  encargo lo prohibía expresamente y por eso quedó reportado y sin aplicar.
- **Nada ejecutado contra Azure, SharePoint ni PostgreSQL.** Solo lectura del
  repositorio, tests locales, `bash harness/init.sh` tal cual y una campaña de
  mutación.

> Informe **incremental**: se escribe según se cierran los commits, no al
> final. Es deliberado; este repositorio ya ha perdido trabajo por lo otro.

---

## 0 · Resumen para quien no quiera leer el resto

| # | Qué | Commit | Estado |
|---|---|---|---|
| 9.1 | El test de contrato de `staticwebapp.config.json` que R14 prometía | `26ef146` | **Hecho**, con fase RED sobre el fichero real |
| 9.3 | «nueve secretos» en los cuatro sitios de `cargar_secretos_postventa.ps1` | `0743c45` | **Hecho**, solo texto |

`bash harness/init.sh` **en verde** al terminar. Campaña de mutación
relanzada sobre este HEAD: **mismo resultado que la ronda anterior**.

---

## 1 · Punto 9.1 · El test que la spec prometía y no existía

### 1.1 Qué estaba mal

`specs/F-010-despliegue/requirements.md:272`, tabla de trazabilidad de **R14**:

> Ya lo fija `staticwebapp.config.json` (F-007); **test de que el despliegue
> no lo pisa**. **MANUAL**: abrir la URL sin sesión

La segunda mitad estaba cumplida (T16, ejecutada por el humano). La primera
**no existía**. Comprobado antes de escribir nada: ningún test del repositorio
leía `routes`, `allowedRoles` ni `responseOverrides` de ese JSON.
`test_f007_estaticos.py:213` solo miraba el marcador `<TENANT_ID>` y la
ausencia de GUID —que es lo que su cabecera dice que vigila, y lo hace bien—.

Traducido a consecuencia: se podía **borrar la regla `"/*"` con
`allowedRoles: ["authenticated"]`** y dejar la aplicación abierta a internet, y
la suite entera seguía verde. Es el fichero que costó el bucle de login
`AADSTS50196` (`progress/impl_F-010.md` §10, una tarde) y el que sostiene el
tercer criterio de aceptación de la feature.

### 1.2 Dónde se ha puesto, y por qué ahí

**Fichero nuevo: `services/postventa-front/tests/test_f010_config_swa.py`.**
El encargo dejaba elegir entre este y `test_f007_estaticos.py`, y la razón de
separarlos es de trazabilidad, no de estética:

- `test_f007_estaticos.py` es, y **declara en su cabecera que es**, el contrato
  de los *ficheros estáticos* del front —orden de los `<script>`, `defer`,
  versión de Alpine—. De la configuración de la SWA vigila **una sola cosa** y
  lo dice explícitamente: que `<TENANT_ID>` siga sin resolver, «porque
  resolverlo es F-010». Meter ahí el contrato de acceso sería contradecir su
  propia cabecera.
- Lo que se fija ahora **no es una decisión de F-007**: es **R14 de F-010**. El
  nombre de los tests (`test_f010_r14_*`) es lo que permite recorrer la tabla
  de trazabilidad de F-010 y encontrarlos, que es exactamente el mecanismo que
  falló aquí: la promesa estaba escrita y nadie podía comprobar si tenía test.
- Los dos ficheros leen el mismo JSON y **no se solapan**: allí, el marcador
  del inquilino; aquí, el acceso. Sin aserciones duplicadas.

### 1.3 Qué fija, y qué se rompe si cada cosa se cae

Las cuatro condiciones del encargo, cada una en su **función pura sobre el JSON
ya parseado** y con **un test propio**, para que el fallo diga qué se ha roto:

| # | Condición | Función | Test | Si se cae |
|---|---|---|---|---|
| 1 | `/.auth/login/aad` es la **primera** ruta y admite `anonymous` | `problemas_del_login` | `test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos` | Vuelve el `AADSTS50196`: la regla `"/*"` captura la propia página de login, y la aplicación queda inaccesible **para todos** |
| 2 | Existe la regla que exige `authenticated` para `/*` | `problemas_del_cierre` | `test_f010_r14_el_comodin_exige_sesion_iniciada` | La aplicación queda **abierta a internet**. Es el fallo silencioso: todo funciona, y de más |
| 3 | Existe `responseOverrides["401"]`, y **redirige** al login con 302 | `problemas_del_401` | `test_f010_r14_el_401_redirige_al_inicio_de_sesion` | Entrar sin sesión devuelve un `401` pelado en vez de la pantalla de Entra, que es literalmente lo que R14 exige |
| 4 | Ni una clave fuera del esquema, arriba **y dentro de cada ruta** | `problemas_de_esquema` | `test_f010_r14_no_hay_claves_fuera_del_esquema` | Azure ignora en silencio lo que no entiende: un `allowedRole` sin la «s» no da error de despliegue, da una aplicación **abierta que parece cerrada** |

Tres decisiones que van más allá de la letra del encargo y que conviene
justificar, porque son las que hacen que el test valga para algo:

1. **La condición 3 comprueba también el destino del redirect y el `302`.** No
   basta con que la clave `401` exista: si redirige a una ruta que **no** es la
   que la condición 1 mantiene anónima, el resultado es el bucle otra vez. Las
   condiciones 1 y 3 son **el mismo mecanismo por sus dos extremos**, y
   fijarlas por separado dejaría pasar la combinación rota.
2. **La condición 4 baja al nivel de ruta**, no solo al de primer nivel. El
   modo de fallo real no es inventarse una sección: es escribir `allowedRole`
   dentro de una regla y que Azure la acepte como regla sin roles. Una regla
   con errata es una **regla muerta**, y ningún despliegue protesta.
3. **La condición 1 se comprueba por posición (`routes[0]`), no por
   presencia.** Que la ruta esté en la lista no sirve de nada: SWA evalúa **en
   orden** y manda la primera que casa. Ese fue el defecto real.

### 1.4 Fase RED · las cuatro condiciones, rotas a mano sobre el fichero real

**El test se escribió antes de romper nada, y el destrozo se hizo sobre el
`staticwebapp.config.json` de verdad**, no sobre un doble: es la única forma de
demostrar que la guardia lee el fichero que se despliega. El original se copió
al scratchpad antes de empezar y **cada caso se restauró con
`git checkout --` inmediatamente después**; el árbol quedó limpio (verificado
con `git status --porcelain`, ver §1.5).

Comandos exactos, uno por caso (`<scratchpad>` es el directorio temporal de la
sesión, fuera del repositorio; `romper.py` **no se versiona**):

```
.venv/Scripts/python.exe <scratchpad>/romper.py <caso> <scratchpad>/swa.bak.json
cd services/postventa-front && ../../.venv/Scripts/python.exe -m pytest tests/test_f010_config_swa.py -q --tb=short
git checkout -- services/postventa-front/staticwebapp.config.json
```

#### Caso 1 · la ruta de login deja de ir la primera

Destrozo: se saca `/.auth/login/aad` de su sitio y se pega al final de `routes`.
Es, literalmente, el defecto que costó la tarde.

```
F...F......                                                              [100%]
================================== FAILURES ===================================
_________ test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos _________
tests\test_f010_config_swa.py:221: in test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos
    assert not problemas, "\n".join(problemas)
E   AssertionError: la primera ruta tiene que ser '/.auth/login/aad' y es '/.auth/login/github': si cualquier regla la precede, el inicio de sesión se pide sesión a sí mismo y sale AADSTS50196
E     la primera ruta no admite 'anonymous' ([]): la página de login quedaría detrás del login
=========================== short test summary info ===========================
FAILED tests/test_f010_config_swa.py::test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[login_al_final]
2 failed, 9 passed in 0.11s
```

#### Caso 1b · la ruta de login deja de admitir anónimos

Es la otra mitad de la condición 1, y se rompe por separado a propósito: la
ruta sigue siendo la primera y aun así la puerta queda cerrada por dentro.

```
F....F.....                                                              [100%]
================================== FAILURES ===================================
_________ test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos _________
tests\test_f010_config_swa.py:221: in test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos
    assert not problemas, "\n".join(problemas)
E   AssertionError: la primera ruta no admite 'anonymous' (['authenticated']): la página de login quedaría detrás del login
=========================== short test summary info ===========================
FAILED tests/test_f010_config_swa.py::test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[login_sin_anonimos]
2 failed, 9 passed in 0.09s
```

#### Caso 2 · se borra la regla que cierra la aplicación

Destrozo: desaparece la entrada `"/*"`. **Éste es el que antes no rompía nada**:
la aplicación quedaba abierta a internet con la suite en verde.

```
.F....F..F.                                                              [100%]
================================== FAILURES ===================================
_______________ test_f010_r14_el_comodin_exige_sesion_iniciada ________________
tests\test_f010_config_swa.py:228: in test_f010_r14_el_comodin_exige_sesion_iniciada
    assert not problemas, "\n".join(problemas)
E   AssertionError: no hay ninguna regla '/*' que exija 'authenticated': la aplicación queda abierta a internet y nada falla al desplegar
=========================== short test summary info ===========================
FAILED tests/test_f010_config_swa.py::test_f010_r14_el_comodin_exige_sesion_iniciada
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[sin_regla_comodin]
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[allowedRole_en_singular]
3 failed, 8 passed in 0.13s
```

#### Caso 3 · se borra el `responseOverrides` del `401`

```
..F....F...                                                              [100%]
================================== FAILURES ===================================
______________ test_f010_r14_el_401_redirige_al_inicio_de_sesion ______________
tests\test_f010_config_swa.py:235: in test_f010_r14_el_401_redirige_al_inicio_de_sesion
    assert not problemas, "\n".join(problemas)
E   AssertionError: falta responseOverrides['401']: sin él, entrar sin sesión devuelve un 401 pelado en vez de la pantalla de Entra (R14)
=========================== short test summary info ===========================
FAILED tests/test_f010_config_swa.py::test_f010_r14_el_401_redirige_al_inicio_de_sesion
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[sin_override_401]
2 failed, 9 passed in 0.13s
```

#### Caso 4 · `allowedRoles` escrito en singular

El destrozo más interesante: **el JSON sigue siendo válido y el despliegue no
protesta**. Lo cazan dos tests a la vez, y eso es lo correcto: la regla queda
muerta (condición 2) *porque* la clave está fuera del esquema (condición 4).

```
.F.F.....F.                                                              [100%]
================================== FAILURES ===================================
_______________ test_f010_r14_el_comodin_exige_sesion_iniciada ________________
tests\test_f010_config_swa.py:228: in test_f010_r14_el_comodin_exige_sesion_iniciada
    assert not problemas, "\n".join(problemas)
E   AssertionError: no hay ninguna regla '/*' que exija 'authenticated': la aplicación queda abierta a internet y nada falla al desplegar
________________ test_f010_r14_no_hay_claves_fuera_del_esquema ________________
tests\test_f010_config_swa.py:242: in test_f010_r14_no_hay_claves_fuera_del_esquema
    assert not problemas, "\n".join(problemas)
E   AssertionError: la ruta 6 ('/*') lleva claves fuera del esquema: ['allowedRole']. Una regla con una errata es una regla muerta, no un error de despliegue
=========================== short test summary info ===========================
FAILED tests/test_f010_config_swa.py::test_f010_r14_el_comodin_exige_sesion_iniciada
FAILED tests/test_f010_config_swa.py::test_f010_r14_no_hay_claves_fuera_del_esquema
FAILED tests/test_f010_config_swa.py::test_f010_r14_la_guardia_caza_la_configuracion_estropeada[allowedRole_en_singular]
3 failed, 8 passed in 0.11s
```

#### Lo que también falla en cada caso, y por qué está bien

En los cinco casos cae además algún
`test_f010_r14_la_guardia_caza_la_configuracion_estropeada[...]`. **No es ruido
accidental: es la guardia de la guardia haciendo su trabajo.** Esos tests
estropean una copia **en memoria** de la configuración real y empiezan por
`assert roto != original`. Si el fichero del árbol ya viene roto de esa misma
manera, el destrozo no cambia nada —o revienta con `KeyError`, como en los
casos 3 y 4— y el test protesta con «el destrozo no ha cambiado nada: revisa el
caso». Es exactamente lo que tiene que decir un test cuyo caso de prueba ha
dejado de probar algo.

#### Verde tras restaurar

```
...........                                                              [100%]
11 passed in 0.04s
```

### 1.5 Que la guardia no pueda quedarse dormida

Cuatro tests de contrato no bastan: si `problemas_de_la_configuracion`
devolviera siempre lista vacía, los cuatro pasarían para siempre. Por eso el
fichero trae **siete destrozos en memoria** (`copy.deepcopy` de la
configuración real, **nada se escribe en disco**), uno por modo de fallo:

| Caso | Qué rompe | Señal que se exige en el mensaje |
|---|---|---|
| `login_al_final` | La puerta detrás de la casa | `primera ruta` |
| `login_sin_anonimos` | La página de login exige sesión | `anonymous` |
| `sin_regla_comodin` | Aplicación abierta | `/*` |
| `sin_override_401` | `401` pelado | `falta responseOverrides` |
| `401_sin_redirigir` | El `401` existe pero no lleva a ningún sitio | `redirige a` |
| `allowedRole_en_singular` | Regla muerta por errata | `fuera del esquema` |
| `responseOverride_en_singular` | Sección entera ignorada por errata | `primer nivel fuera del esquema` |

No se comprueba solo que la guardia proteste: se comprueba que proteste **por
lo que es**. Un `assert problemas` a secas dejaría pasar una guardia que se
queja siempre de lo mismo.

### 1.6 Estado del árbol tras la fase RED

```
$ git status --porcelain
?? progress/review3_F-010.md
?? services/postventa-front/tests/test_f010_config_swa.py
```

`staticwebapp.config.json` **no aparece**: los cinco destrozos quedaron
revertidos. Lo único suelto era el test nuevo (y el informe del reviewer, que
no es mío: ver §4).

### 1.7 Commit

`26ef146` — `F-010 9.1: el test de contrato de staticwebapp.config.json que
R14 prometia`. Un solo fichero añadido; **ningún test existente tocado**.

---

## 2 · Punto 9.3 · El script dejaba de dictar el criterio imposible

### 2.1 Qué estaba mal

`infra/cargar_secretos_postventa.ps1` seguía hablando de «los **once**
secretos» en cuatro sitios, y uno de ellos era **operativo**:

```
:269  Write-Host "Anota en progress/ solo esto: 'once secretos cargados: si/no'."
```

Esa línea le dicta al humano, **por pantalla y en el momento de ejecutar**,
exactamente el criterio que `specs/F-010-despliegue/tasks.md` T13 rectificó por
**imposible** el 2026-08-25 y que `docs/DESPLIEGUE.md` §2 explica con la parada
real que costó. Quien ejecuta el script hace caso al script.

### 2.2 Qué se ha cambiado, y qué no

**Texto y solo texto. Ni una línea de lógica.** El script sigue recorriendo la
lista entera del vault (`$aSubir = $PostventaSecretos`, once nombres) y sigue
saltando los que se dejan vacíos. Lo que cambia es que ahora **lo dice**.

| Sitio | Antes | Ahora |
|---|---|---|
| `.SYNOPSIS` (:4) | «sube sus **once** secretos» | «sube los **NUEVE** secretos del backend» |
| `.DESCRIPTION` (:30) | «Los **once** secretos y sus nombres salen de `00_vars_postventa.ps1`» | Los nombres salen de ahí, **más un párrafo nuevo** «SON NUEVE, NO ONCE» con el porqué completo |
| `.PARAMETER Solo` (:44) | «sin tener que volver a teclear **las once**» | «rotar una credencial **del backend** sin volver a teclear **las otras ocho**» |
| Salida final (:269) | «Anota […] `'once secretos cargados: si/no'`» | «Anota […] `'nueve secretos cargados: si/no'`» **+ dos líneas** con la coletilla |

El párrafo nuevo de `.DESCRIPTION` dice, en resumen: el Key Vault acaba con
once, pero a mano se cargan los **nueve del backend** (`pg-*`,
`gemini-api-key`, `graph-*`, `sharepoint-*`); `swa-client-id` y
`swa-client-secret` **los crea y los guarda `desplegar_front.ps1`** cuando
genera el registro de aplicación; cuando este script corre **todavía no
existen**, y cualquier valor que se teclee lo sobrescribe después el despliegue
del front; **se dejan vacíos** y salen como «Sin tocar». Con el puntero a la
partición (`$PostventaSecretosBackend` / `$PostventaSecretosFront`) y a
`docs/DESPLIEGUE.md` §2, donde está la parada del 2026-08-21.

**Decisión que conviene ver**: la coletilla de `:269` son **dos `Write-Host`
nuevos**, no una sola línea reescrita. El motivo es que el resumen imprime
«Subidos: 9 / Sin tocar: 2» y, sin explicación al lado, ese `2` invita
justamente al error que costó la parada. Sigue siendo salida por consola, del
mismo tipo que la línea que ya había: **no cambia ninguna ruta de ejecución, ni
un código de salida, ni una llamada a `az`**.

**ASCII**: el fichero se lee en los tests con `encoding="ascii"`
(`test_f010_scripts_infra.py:252`). Todo el texto nuevo va sin acentos, como el
resto del script.

### 2.3 Dos comentarios que arrastraban el mismo «once»

De paso, en `services/postventa-api/tests/test_f010_scripts_infra.py`:

- `:46` — comentario de `SCRIPT_SECRETOS`: «sube los once secretos» → «sube los
  nueve secretos del backend».
- `:257` — docstring: «las once credenciales viajan a mano» → «las nueve».

**Ninguna aserción cambia.** Y `test_f010_t3_declara_los_once_secretos_del_key_vault`
(:196) **se queda como está, con sus once nombres**: ese test es sobre
`00_vars_postventa.ps1`, y el vault sí acaba con once. La distinción es
justamente el punto: **once en el vault, nueve a mano.**

### 2.4 Verificación

Los tests de contrato de `infra/`, tal cual, antes de commitear:

```
$ cd services/postventa-api && .venv/Scripts/python.exe -m pytest \
    tests/test_f010_scripts_infra.py tests/test_f005_scripts_infra.py \
    tests/test_f006_scripts_infra.py tests/test_f010_prompt_keys_infra.py -q
160 passed, 3 skipped in 0.60s
```

En verde. Incluidos los que vigilan `-WhatIf` antes de la primera escritura y
los códigos de salida, que son los que se romperían si el texto añadido hubiera
desplazado algo con significado.

### 2.5 Commit

`0743c45` — `F-010 9.3: el script de secretos deja de dictar el criterio
imposible`.

---

## 3 · Portero de salida

`bash harness/init.sh`, tal cual, sin pipes:

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 58 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)        17 passed in 0.82s
[OK] servicio api (services/postventa-api): pytest en verde    1092 passed, 13 skipped in 37.28s
[OK] servicio front (services/postventa-front): pytest en verde   85 passed in 2.67s
[OK] PUERTA COBERTURA: 98.5% de 136 líneas cambiadas cubiertas (134/136, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-010-despliegue
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

El aviso de `ruff` es el mismo número de la ronda anterior: **deuda previa, no
la toca esta ronda**.

---

## 4 · Residuos y observaciones (nada de esto se ha tocado)

1. **`progress/review3_F-010.md` está sin versionar** (`?? ` en
   `git status`). Es el informe del reviewer de esta ronda y no es mío:
   no lo commiteo. **Lo señalo porque además bloquea la campaña de mutación
   en paralelo** (ver §5) y porque un informe de review fuera de git es un
   agujero en el rastro documental de la feature. **Decisión del líder.**
2. **`harness/mutacion.py` acumula una nota por re-ejecución.** Cada campaña
   añade otra copia de «_Análisis traído de la campaña anterior…_» debajo del
   mismo superviviente; van ya **cuatro** bajo cada uno de los tres. Es
   cosmético y no afecta al veredicto, pero es un **defecto del arnés genérico**
   y, si se arregla, la mejora viaja a `arnes-base`. **No lo arreglo aquí**:
   está fuera del encargo y `harness/mutacion.py` es uno de los ficheros en
   alcance de la propia campaña.
3. **El bloque «Deja uno VACIO para no tocarlo» (`:221` del script) no se ha
   tocado.** Es donde el humano decide qué teclear, y sería el sitio más útil
   para la coletilla; el encargo nombraba **cuatro** sitios y me he ceñido a
   ellos. Si el reviewer lo quiere, es una línea.
4. **§9.2 no se ha tocado**, por encargo: lo cierra
   `progress/spec_postreview3_F-010.md`.
5. **T14 bis** sigue siendo del humano.

---

## 5 · Evidencias

Números **medidos hoy sobre este HEAD** (`0743c45`), no estimados.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** | **1194 pasados, 13 saltados, 0 fallidos** | `bash harness/init.sh`: arnés 17 + api 1092 + front 85 |
| **Tests nuevos de esta ronda** | **11** (4 de contrato + 7 destrozos) | `test_f010_config_swa.py`; el front pasa de 74 a 85 |
| **Cobertura de las líneas cambiadas** | **98.5 %** (134/136), umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `init.sh` |
| **Mutantes generados / supervivientes** | **23 / 3** (20 muertos, 0 timeouts) | `python -m harness.mutacion --feature F-010 --workers 1` → `progress/mutacion_F-010.md` |
| **Tiempo de la campaña de mutación** | **118.2 s** (1 worker, en serie) | la propia campaña |
| **Tiempo de ejecución de la suite** | **api 37.28 s · front 2.67 s · arnés 0.82 s** | el que imprime cada suite |

### 5.1 Cobertura: por qué el número no se mueve

136 líneas cambiadas, las mismas que en la ronda anterior. Lo de hoy **no
suma**: un fichero de tests (`harness/alcance.py` excluye del alcance de
producción cualquier ruta con el segmento `tests`, y la cabecera del
`conftest.py` del front lo dice explícitamente) y un `.ps1`, que no es Python y
el arnés no mide. **Los dos cambios de esta ronda son, por construcción, ajenos
a la puerta de cobertura**, y decirlo es más honesto que presentar un 98.5 %
como si lo hubiera ganado hoy.

### 5.2 Mutación: mismo resultado, y por qué tenía que serlo

Campaña **completa** (sin muestreo) sobre las 385 líneas de producción de la
rama. **23 mutantes, 20 muertos, 3 supervivientes, 0 timeouts.** Idéntico a la
campaña de la ronda anterior, y es lo esperado: esta ronda **no ha cambiado ni
una línea de producción Python**, así que el conjunto de mutantes es el mismo.

Los **tres supervivientes son los tres de siempre**, y su análisis sigue vigente
y completo en `progress/mutacion_F-010.md`:

| # | Mutante | Veredicto |
|---|---|---|
| 1 | `dev_server.py:169` · `log.info("=" * 60)` → `"=" * 61` | **Equivalente** |
| 2 | `dev_server.py:171` · ídem | **Equivalente** |
| 3 | `dev_server.py:175` · ídem | **Equivalente** |

Es el ancho del separador decorativo del banner de arranque del servidor de
desarrollo local —que además **no se despliega**, `desplegar_front.ps1` lo
excluye—. Ningún test mira cuántos signos `=` lleva esa línea, y **no debería
mirarlo**: un test que fijara el ancho de un adorno se rompería en cada retoque
de la salida y no protegería nada. **Ninguna sección queda en `PENDIENTE`.**

**Nota de ejecución**: la campaña se lanzó con `--workers 1` porque la paralela
se niega a correr con el árbol sucio —crea sus worktrees desde `HEAD` y
evaluaría un código distinto del que hay en disco—, y el árbol tenía el
`progress/review3_F-010.md` sin versionar (§4.1). El aviso del arnés es
correcto y la campaña en serie evalúa exactamente lo que se ve.

### 5.3 Verificaciones `MANUAL (humano)` pendientes

Esta ronda **no añade ninguna**. Las que seguían pendientes al cerrar
`review3_F-010.md` siguen igual y no dependen de este trabajo:

- **T14 bis** — el tope de gasto con alerta (R35). Del humano.
- Nada más: T1, T13, T14, T16 y T18 quedaron ejecutadas y anotadas en rondas
  anteriores.

**Lo que el test de §1 NO sustituye**: T16, abrir la URL sin sesión y ver la
pantalla de Entra, sigue siendo la verificación manual de R14 y **está
ejecutada**. El test nuevo cubre la otra mitad de la promesa —que el fichero
que se despliega siga diciendo lo que tiene que decir— y es la mitad que
protege del futuro, no del presente: T16 demuestra que **hoy** funciona; el
test impide que **mañana** deje de hacerlo sin que nadie se entere.
