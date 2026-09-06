<!-- progress/guion_bloque9_F-012.md -->
# F-012 · Guion de ejecución del bloque 9 (T25–T32)

> **Qué es esto.** El procedimiento que sigue **el humano**, delante del ERP de
> producción y con el entorno desplegado, para verificar que el parte firmado
> entra en Sigrid como **gráfico** de la reclamación y que la reclamación se
> cierra **con su parte dentro**. Cada tarea trae qué se verifica, sus
> precondiciones, los pasos numerados con la línea exacta que se teclea, qué se
> espera ver, qué hacer si no sale eso, y una casilla de resultado que se
> rellena aquí mismo.
>
> **Quién lo ejecuta.** Una persona. Ningún agente ha ejecutado —ni puede
> ejecutar— nada de este bloque: ni el dry-run. Escribir en Sigrid desde local
> está prohibido por `CLAUDE.md`, y contra producción solo se hacen lecturas
> salvo autorización expresa para una acción concreta.
>
> **Sobre qué se ejecuta.** **Reclamaciones de la obra de prueba 404**, y de
> ninguna otra. Ni Mirasierra, ni una obra real. Es la decisión del humano del
> 2026-09-06 y es la regla dura de todo el bloque: cada escritura de este guion
> —el gráfico y el cierre— cae sobre una reclamación de esa obra, localizada
> con `infra/15_reclamaciones_obra_prueba.ps1` y **autorizada una a una**.
>
> **Estado**: `progress/impl_F-012.md` está aprobado en review
> (`progress/review_F-012.md`, veredicto APROBADO), T33 (mutación) cerrada y
> T34 (`init.sh`) en verde. Falta este bloque entero. Las tareas de
> `specs/F-012-grafico-sigrid/tasks.md` **las marca el humano**, no el agente.
>
> **Este bloque ejecuta de hecho un cierre completo.** T27 adjunta y T29
> cierra: la reclamación de la obra 404 acaba en `CER` con su parte dentro. Es
> el orden **(b)** de `design.md` §13, y por eso el bloque 8 de F-009 ya no se
> recorre como estaba escrito: ver la nota fechada de
> `progress/guion_bloque8_F-009.md`.

---

## 0 · Seis cosas que sorprenden, y conviene saber antes de estar delante del ERP

### 0.1 · Con `CIERRE_HABILITADO` apagado **no funciona ni el dry-run del gráfico**

Es lo mismo que en F-009 y por el mismo mecanismo: `construir_graficos`
(`infrastructure/sigrid/fabrica.py`) comprueba **en este orden** el entorno →
el interruptor → la configuración, y **solo entonces** construye el adaptador.
El interruptor se mira **antes de leer nada**, así que con
`CIERRE_HABILITADO=false` la respuesta de `POST /api/adjuntar` es
`503 CierreDeshabilitado` y la pasarela **no se entera de que existimos**
(R39, R60).

Consecuencia práctica: **la ventana tiene que estar abierta ya para T25**, que
es un dry-run y no escribe nada. No se puede «ensayar el dry-run con la ventana
cerrada». La secuencia real es abrir la ventana → T25 … T31 → **T32 cerrarla**,
y mientras esté abierta hay que estar delante.

### 0.2 · La ventana es **una sola** para el gráfico y para el cierre

No hay un interruptor nuevo (D-B). `CIERRE_HABILITADO` cubre las **dos**
escrituras de este servicio en el ERP, porque el gráfico es la primera mitad
del cierre: el mismo sistema, el mismo dueño, la misma decisión. Un segundo
interruptor solo podría crear dos estados —«adjunta pero no cierra» y «cierra
pero no adjunta»— y los dos son malos.

**Abrirla para probar el gráfico abre también el cierre.** Es aceptable —el
dry-run es lo que se hace por omisión, el `commit` exige confirmación explícita
y el humano está delante— y de hecho este bloque **quiere** cerrar la
reclamación de prueba después de adjuntarla (T29). Pero no puede ser una
sorpresa, y por eso está escrito aquí arriba.

### 0.3 · El caso idempotente responde `committed: false`, y eso es un **éxito**

Está medido y documentado en `azure-apps/sigrid_api.md` §8.8: con `commit:
true` y el documento **ya colgado**, la pasarela responde `ok: true`,
`idempotente: true`, `filas_afectadas: 0` y **`committed: false`**, porque no
escribió ninguna fila y decir lo contrario sería mentir.

Quien decida por `committed` verá `false` en un éxito. **El campo que dice si
la operación fue bien es `ok`**; la comprobación correcta de «el documento está
colgado» es `ok && (committed || idempotente)`, y es exactamente lo que hace
`esta_colgado` del dominio (R26). En la respuesta de `/api/adjuntar` eso se ve
como `estado: "adjuntado"` con `idempotente: true` y `filas_afectadas: 0`.

**En T28 esto no es un defecto: es el resultado esperado.** Si en ese paso se
lee `filas_afectadas: 0` y se interpreta como «no ha hecho nada, repito», se
estaría reintentando una escritura que ya está hecha.

La respuesta idempotente trae además otras tres cosas distintas, y el adaptador
las tolera a propósito **[MEDIDO]**: `grafico.fec = 0`,
`grafico.ide_documental = null` y `enlace.pos = null`. Ninguna es un error, y
por eso `17_traza_grafico_local.ps1` **anota** el ide documental en vez de
exigirlo.

### 0.4 · Un tiempo agotado en el commit deja el ERP en **estado desconocido**, y el reintento **es seguro**

Es la diferencia con F-009, y es la que importa. Si el `commit` del gráfico se
va por tiempo agotado, corte de red o `500` de la pasarela, **no se sabe si la
escritura llegó a aplicarse**: el servicio deja la traza en `error` con el
motivo «puede que el ERP haya escrito» y devuelve `502` (R28, R29, R34).

Pero a diferencia del cierre, **volver a pedirlo no duplica nada**: el endpoint
es idempotente por tamaño y `sha256`, comprobado dos veces por la pasarela —al
leer y otra vez dentro de la transacción, bajo bloqueo—. Así que la salida
correcta ante un `502` de este endpoint es **repetir la llamada**, no abrir
Sigrid a mirar.

En el cierre de F-009 la regla es la contraria (R27 de F-009: **no** se
reintenta), y las dos conviven en el mismo botón. Si el `502` es de
`/api/cerrar`, se para; si es de `/api/adjuntar`, se repite.

### 0.5 · El gráfico **no escribe ni una fila** en `dbo.log` (R36)

Ni la pasarela ni el propio Sigrid lo hacen al importar un documento **[MEDIDO:
0 filas con `tab='gra'` en 8,4 millones]**. Por eso `16_grafico_sigrid.ps1` lee
`MAX(ide)` de `dbo.log` en **las dos** fotos, la de antes y la de después, y
por eso **ese número no debe subir** entre T25 y T28.

El que sí sube exactamente en uno es el del **cierre** (T29), que escribe su
fila de auditoría como en F-009. Confundir los dos lleva a dar por bueno un
gráfico que escribió donde no debía, o a alarmarse por un cierre que hizo lo
correcto.

### 0.6 · A `/api/adjuntar` **no se le llama a mano**: el cuerpo es un `multipart` con el PDF dentro

`/api/cerrar` es JSON y se puede teclear. `/api/adjuntar` no: lleva **los bytes
del parte** (D-H), ocho campos de formulario y un `boundary` que compone el
navegador. Escribir ese cuerpo a mano no es práctico, y equivocarse en un campo
da un `400` que parece un fallo del servicio.

La vía es **la del propio front**, y hay dos formas (§4): el botón, o la
consola del navegador reutilizando `Pipeline.cuerpoDeGrafico`, que es la misma
función que usa el botón. En la consola, además, **no se pone `Content-Type`**:
si se pone, se rompe el `boundary` y el backend recibe un formulario vacío. Es
el error más fácil de cometer de todo el bloque.

---

## 1 · La configuración: qué la pone ya el despliegue y qué queda a mano

Este bloque necesita **dos** configuraciones que no son la misma cosa y tienen
**dos dueños distintos**:

| Quién | Qué | Quién la pone |
|---|---|---|
| **Nuestra** Function App | las App Settings de F-009 y F-012 | `infra/desplegar_backend.ps1`, en cada despliegue |
| La Function App de **`sigrid-api`** | las cinco `SIGRID_DOCUMENT_*` y `SIGRID_DOMAIN_WRITE_ENABLED` | **el dueño de la pasarela**. Aquí solo se **leen** |

Confundirlas cuesta una tarde: un `503 escritura_documental_deshabilitada` no
se arregla desplegando nuestro backend, y un `409
clase_de_grafico_no_permitida` no se arregla cambiando
`SIGRID_GRATIPIDE_PARTE` aquí.

### Qué hace ya nuestro despliegue, sin que nadie teclee nada

`infra/desplegar_backend.ps1` fija en cada ejecución, además de las ocho App
Settings de F-009, **las dos de F-012**:

| Cómo | Cuáles |
|---|---|
| Referencia a Key Vault, resuelta por la identidad gestionada | `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` |
| En claro en `$ajustes` | `CIERRE_HABILITADO=false`, `SIGRID_BASE_DATOS`, `SIGRID_TIMEOUT_S`, `SIGRID_REINTENTOS`, `SIGRID_TIP_RECLAMACION`, `SIGRID_ZONA_HORARIA`, **`SIGRID_GRATIPIDE_PARTE=35`**, **`GRAFICO_MAX_BYTES=10485760`** |

Tres consecuencias que importan para este guion:

1. **`CIERRE_HABILITADO` vuelve a `false` en cada despliegue.** Un redespliegue
   en mitad del bloque **cierra la ventana**: si pasa, se vuelve a abrir con la
   línea del paso 3 de T25, no se da por hecho que sigue abierta.
2. **`SIGRID_GRATIPIDE_PARTE=35` queda escrita**, y es la clase con la que se
   colgará el documento. Cambiarla aquí a secas **no basta**: la pasarela
   mantiene su propia lista blanca (`SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`), y por
   eso T31 la usa justo para provocar el rechazo.
3. **`GRAFICO_MAX_BYTES=10485760`** es un tope **nuestro**, comprobado antes de
   llamar a nadie. **No** protege del tope de la pasarela
   (`SIGRID_DOCUMENT_MAX_BYTES`), que es suyo y puede ser menor.

El script imprime al terminar `Ventana de escritura : CERRADA (archivo, y
GRAFICO Y cierre en el ERP)`. Esa línea es la que confirma que el interruptor
quedó apagado.

### Paso 0 (1) · Nuestra configuración, en un solo script

Lo mismo que en el bloque 8 de F-009, y sirve igual: los dos secretos, las App
Settings y la comprobación de que las once referencias a Key Vault se
resuelven. **Primero en seco**, que solo lee y no invoca a ninguno de los dos
scripts que escriben:

```
powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1 -WhatIf
```

**Qué se espera ver**: la tabla de las **once** referencias, una por línea, y
el veredicto:

```
  SIGRID_API_BASE_URL    -> Resolved
  SIGRID_API_KEY         -> Resolved

Paso 0 COMPLETO: 11/11 referencias resueltas.
```

**Si no sale eso**: el script dice qué referencia no se resuelve y por qué, y
sale con código distinto de cero (`12` alguna en error, `11` no se ha podido
preguntar). Una referencia en error es casi siempre un secreto que falta en el
vault o el rol de lectura de la identidad gestionada sin propagar. Entonces —y
solo entonces— se lanza el script **sin** `-WhatIf`, que sí escribe:

```
powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1
```

> El plano de gestión publica el **estado** de cada referencia y su motivo de
> fallo, nunca el valor que hay detrás: por eso esa tabla se puede pegar tal
> cual en la casilla de resultado.

### Paso 0 (2) · El backend desplegado **con el código de F-012**

Es la precondición P2 y no es opcional: sin ella `/api/adjuntar` no existe y lo
que responde es un **404**, que no se parece en nada al `503` de la ventana
cerrada.

```
powershell -ExecutionPolicy Bypass -File .\infra\desplegar_backend.ps1
```

**Qué se espera ver**: `App Settings : N, de las que 11 son referencias` y
`Ventana de escritura : CERRADA (archivo, y GRAFICO Y cierre en el ERP)`.

**Comprobación, y es la que distingue los cuatro casos**: con la ventana
todavía cerrada, llamar al endpoint desde la consola del front (§4) y mirar el
código:

| Lo que responde | Qué significa |
|---|---|
| **404** | el despliegue no lleva el código de F-012. Vuelve a desplegar |
| **503** diciendo que el cierre está deshabilitado | **es lo correcto**: hay código y la ventana está cerrada |
| **503** nombrando `SIGRID_API_BASE_URL` o `SIGRID_API_KEY` | falta el Paso 0 (1) |
| **200** | la ventana está abierta y no debería. Ciérrala (T32) y entiende por qué |

### Paso 0 (3) · La configuración **de la pasarela** (P0), que solo se lee

Son de **otro proyecto**. Aquí no se tocan: si algo falta, **se pide al dueño
de `sigrid-api`**. Se leen sin ver ningún secreto, porque las seis que
interesan no lo son: son interruptores y listas blancas.

El script —se guarda como `paso0_pasarela.ps1` **fuera del repositorio**, o se
pega tal cual en la ventana de PowerShell:

```powershell
# Lectura de la configuracion documental de sigrid-api (P0 del bloque 9).
# SOLO LEE. Los nombres del grupo y de la Function App son de OTRO proyecto y
# no se escriben en este repositorio: se teclean.
$grupoPasarela = Read-Host "Grupo de recursos de sigrid-api"
$appPasarela   = Read-Host "Function App de sigrid-api"
$consulta = "[?starts_with(name,'SIGRID_DOCUMENT_') || name=='SIGRID_DOMAIN_WRITE_ENABLED'].{Nombre:name,Valor:value}"
az functionapp config appsettings list -g $grupoPasarela -n $appPasarela --query $consulta -o table
```

Y la línea que lo ejecuta:

```
powershell -ExecutionPolicy Bypass -File .\paso0_pasarela.ps1
```

**Qué se espera ver**, seis filas y estos valores:

| App Setting de `sigrid-api` | Qué tiene que valer | Qué pasa aquí si no |
|---|---|---|
| `SIGRID_DOMAIN_WRITE_ENABLED` | `true` | Sin ella no hay endpoint de dominio que valga |
| `SIGRID_DOCUMENT_WRITE_ENABLED` | `true` | `/api/adjuntar` → **503** `escritura_documental_deshabilitada`, **sin escribir nada** |
| `SIGRID_DOCUMENT_WRITE_DATABASE` | la base documental | Vacía → el mismo 503, **también en el dry-run** |
| `SIGRID_DOCUMENT_ALLOWED_CONTIP` | contiene `708` | **409** `tipo_de_concepto_no_coincide` |
| `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` | contiene `35` | **409** `clase_de_grafico_no_permitida` |
| `SIGRID_DOCUMENT_MAX_BYTES` | ≥ el tamaño del parte de prueba | **409** `tamano_excedido`. Nuestro `GRAFICO_MAX_BYTES` no protege de esto: es un tope propio, no el suyo |

**Si no sale eso**: **para y pídeselo al dueño de `sigrid-api`.** No se cambia
nada de ese proyecto desde aquí, ni siquiera «solo para probar».

> **El filtro `--query` no es cosmética.** Sin él, `appsettings list` vuelca
> **todas** las App Settings de la pasarela —credenciales de escritura del ERP
> incluidas— a la consola de alguien. Y, aunque las vuelque, las que son
> referencias a Key Vault **salen sin resolver**: lo que se vería es la cadena
> literal `@Microsoft.KeyVault(...)`, no el valor. Es lo mismo que pasa con
> nuestras `SIGRID_API_BASE_URL` y `PG_HOST` (§3).

### La base documental, y de dónde sale su valor por defecto

`16_grafico_sigrid.ps1` trae `-SigridBaseDocumental` con la base documental por
defecto, porque es la única contra la que la pasarela permite escribir y ya
está escrita en documentos versionados. Si algún día cambia, se pasa por
parámetro; no se edita el script.

---

## 2 · Precondiciones (se comprueban **antes** de abrir la ventana)

### Técnicas

- [ ] **P0** · Las **seis** App Settings de `sigrid-api` leídas hoy con el
      bloque del Paso 0 (3) y con los valores de esa tabla. **No se dan por
      buenas** porque el dueño las dejara bien el 2026-09-06: se releen.
- [ ] **P1** · `bash harness/init.sh` en verde en la rama
      `feature/F-012-grafico-sigrid`.
- [ ] **P2** · El backend desplegado lleva el código de F-012: con la ventana
      cerrada, `/api/adjuntar` responde **503**, no 404 (Paso 0 (2)).
- [ ] **P3** · Paso 0 (1) hecho: los dos secretos de Sigrid en el Key Vault y
      las App Settings puestas. Se comprueba con
      `.\infra\14_paso0_sigrid.ps1 -WhatIf`, que tiene que terminar en
      `Paso 0 COMPLETO: 11/11 referencias resueltas`.
- [ ] **P4** · Raíz y clave de la pasarela a mano para los scripts de lectura
      (§3). **No se escriben en ningún fichero.**
- [ ] **P5** · **Una reclamación de la obra 404** localizada con
      `infra/15_reclamaciones_obra_prueba.ps1` —cerrable y **sin gráfico**— y
      **su parte** recorrido entero en el front: subido, validado `apto` /
      `archivo_y_cierre`, **guardado** (`POST /api/parte`) y **archivado**
      (`POST /api/archivar`). No es una formalidad: `postventa.graficos` tiene
      **clave ajena contra `postventa.partes`**, así que un `hash` que no esté
      guardado hace fallar **hasta el dry-run** (R46). Es la misma trampa del
      defecto 15 de F-010 y de la P5 del bloque 8 de F-009.
      Si no existe un parte escaneado de esa obra, ver P5 de `design.md` §14: lo
      prepara Posventa, o se recorre el circuito con un PDF de prueba sobre una
      reclamación de la 404.
- [ ] **P6** · **Autorización expresa del humano para esa reclamación
      concreta**, no «para probar el gráfico». Es lo que exige `CLAUDE.md`.
      T31 usa **otra** reclamación candidata, y necesita **su propia**
      autorización aunque no llegue a escribir.
- [ ] **P7** · Sesión iniciada en el front (grupo `posventa-usuarios`), porque
      **el backend no responde por su nombre de host** (§4), y **una sola
      sesión con un solo parte en curso**: el botón de cierre recorre **todos**
      los cerrables de la sesión, y la primera escritura real tiene que ser
      **una**.

### Documentales — no bloquean técnicamente, pero se cierran antes de dar el bloque por bueno

- [ ] **D1** · **Aceptación de los 5 supervivientes de mutación** declarados
      equivalentes en `progress/mutacion_F-012.md` y verificados uno a uno por
      el reviewer (`progress/review_F-012.md` §5.4). El nivel `critico` exige
      esa aceptación **por escrito y del humano**. Sin ella, T33 está hecha
      pero no aceptada, y eso se anota; no impide ejecutar T25.
- [ ] **D2** · **Confirmación con Posventa (Ana Bello / Alicia Echevarría) de
      que `PV002`** —`gratipide` 35, «POSTVENTA:Fotos Reparaciones»— **es la
      clase correcta para un parte firmado** (P1 de `design.md` §14). Los datos
      la apoyan (3.197 «PARTE FIRMADO» en esa clase **[MEDIDO]**); el nombre de
      la clase no lo dice. Cambiarla es una decisión de **dos dueños**: una App
      Setting nuestra **más** la lista blanca de la pasarela. Conviene tenerla
      antes de T27, porque T27 escribe de verdad y bajo esa clase.

---

## 3 · El utillaje: los scripts de `infra/`, una línea corta cada uno

Todos son **PowerShell 5.1**, re-ejecutables, comprueban sus precondiciones y
paran con un mensaje claro en vez de reventar, y **terminan imprimiendo un
veredicto** en forma de tabla `QUE / ESPERADO / OBTENIDO` con `PASA` o
`NO PASA` (código de salida `0` o `6`).

| Script | Qué hace | Escribe |
|---|---|---|
| `infra/08_lectura_sigrid_comun.ps1` | Solo **declara**: la llamada a `POST /api/sql/read`, el manejo de la clave y el formato del veredicto. Lo cargan los demás | nada |
| `infra/15_reclamaciones_obra_prueba.ps1` | **P5**: localiza la obra 404, lista sus reclamaciones con estado legible y nº de gráficos, y separa las **candidatas** (cerrables y sin gráfico) | **nada · solo lee** |
| `infra/16_grafico_sigrid.ps1` | Las **tres filas** del gráfico —negocio, documental y enlace `rcg`— y el `MAX(ide)` de `dbo.log`. Con `-DescargarYComparar`, además el `sha256` del binario que hay dentro del ERP | **nada · solo lee** |
| `infra/17_traza_grafico_local.ps1` | La traza de `postventa.graficos`: estado, `sha256`, bytes, clase, los tres `ide`, `idempotente`, y **que el login no está fuera de `gra_cod`** (R44) | **nada · solo lee**, y solo del esquema propio |
| `infra/09_estado_reclamacion_sigrid.ps1` | (F-009) La reclamación en el ERP: `ide`, `emp`, `est`, estado legible, destino resuelto contra `conest`, `tiemod` y `MAX(ide)` de `dbo.log` | **nada · solo lee** |
| `infra/10_log_cierre_sigrid.ps1` | (F-009) La fila nueva de `dbo.log` campo a campo, y **el huso** de `fec`/`hor` | **nada · solo lee** |
| `infra/11_trazabilidad_tex_sigrid.ps1` | (F-009) Las dos lecturas del `tex` propio | **nada · solo lee** |
| `infra/12_traza_cierre_local.ps1` | (F-009) La traza de `postventa.cierres` y la correspondencia de `postventa.usuarios_sigrid` | **nada · solo lee** |
| `infra/14_paso0_sigrid.ps1` | **No es de esta familia**: no lee del ERP, **aprovisiona** (Paso 0 (1)). Se ejecuta una vez, antes de todo | Key Vault y App Settings, por los dos scripts que invoca |

**Todos los de lectura son de lectura.** Leer producción está permitido;
escribir en Sigrid desde un puesto de trabajo, no. Las **únicas dos**
escrituras en el ERP de todo el bloque son el `POST /api/adjuntar` con
`commit: true` de T27 y el `POST /api/cerrar` con `commit: true` de T29, y
**las hace el servicio desplegado**, no esta máquina.

Ojo con `16_grafico_sigrid.ps1 -DescargarYComparar`: es el **único** paso que
trae el PDF a esta máquina. No lo escribe en disco —calcula el hash en memoria
y lo descarta—, y por eso es un modificador y no el comportamiento normal.

### Cómo se les pasa el destino y la clave

Para no teclear la raíz y la clave en cada llamada —y para que no queden en el
historial de la consola—, se dejan en la sesión **una vez**, y se borran al
terminar (T32):

```
$env:SIGRID_API_BASE_URL = "<la raíz de la pasarela>"
```

```
$env:SIGRID_BASE_DATOS = "<la base de negocio del ERP>"
```

La clave **no se pone en una variable de entorno tecleada en claro**: cada
script la pide por consola como `SecureString` si `$env:SIGRID_API_KEY` no
está. Si se prefiere no repetirla:

```
$env:SIGRID_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR((Read-Host "Clave de sigrid-api" -AsSecureString)))
```

> **La raíz y `PG_HOST` NO se leen con `az functionapp config appsettings
> list`, y no es una preferencia: ese comando no funciona para ellas.**
> Devuelve el valor **crudo** de la App Setting, y las dos son **referencias a
> Key Vault**, así que lo que sale es la cadena literal
> `@Microsoft.KeyVault(SecretUri=...)`. Azure resuelve la referencia **al
> arrancar la Function**, no en la API de gestión: por ahí no hay forma de leer
> el valor resuelto. Se teclean, como la clave. Quien quiera comprobar que la
> referencia está bien puesta, que mire su **estado** (`Resolved`), no su
> valor: eso lo hace `infra/14_paso0_sigrid.ps1` (§1).
>
> Lo que **sí** se lee así son las App Settings planas: las seis de la pasarela
> del Paso 0 (3), y `SIGRID_GRATIPIDE_PARTE` y `CIERRE_HABILITADO` de la
> nuestra, en T31 y T32.

> De dónde sale cada valor: la raíz y la clave, del dueño de `sigrid-api`
> (`azure-apps/sigrid_api.md` §3.1 y §3.3). La base, la de negocio: es la única
> con escritura permitida en la pasarela. El host de PostgreSQL y la contraseña
> de `postventa_app`, del Key Vault del proyecto. **Ninguno se escribe en este
> fichero ni en ningún otro del repositorio.**

---

## 4 · Cómo se llama a `/api/adjuntar` y a `/api/cerrar` (y por qué no con `curl`)

**El host desnudo de la Function no responde.** Desde que es backend enlazado
de la Static Web App, la plataforma le activa Easy Auth y cualquier ruta
—`/api/health` incluida— devuelve
`{"code":400,"message":"Login not supported for provider azureStaticWebApps"}`
antes de que la Function se entere (`docs/DESPLIEGUE.md` §5 bis). No hay
`-BaseUrl` que lo arregle, y `Invoke-RestMethod` desde el puesto tampoco.

Hay, por tanto, **dos vías legítimas**, las dos desde el front con sesión
iniciada.

### (a) La interfaz del front — la vía normal, y la que usa negocio

1. **«Ver qué pasaría (no cierra nada)»** pide, por cada parte cerrable y en
   este orden (R63): `POST /api/adjuntar` **sin** `commit`, y después
   `POST /api/cerrar` **sin** `commit`. La tarjeta pinta el bloque azul del
   gráfico —«Se adjuntará *nombre* (N bytes, clase 35) como «PARTE FIRMADO»,
   firmado por *login*», con el `sha256` debajo y los avisos de la pasarela tal
   cual— y, debajo, el del cierre: `PTE (…) → CER (…)` y el login. **Ya no hay
   bloque ámbar** de «quedará sin el parte»: R48 lo derogó.
   Si el gráfico ya estaba dentro, en su lugar pone «El parte **ya está dentro
   de Sigrid** (mismo contenido): no se escribirá nada» (R22).
2. **«Cerrar las incidencias»** → «¿Seguro? Esto escribe en Sigrid y lo ve
   Posventa.» → **«Sí, cerrar»**. La confirmación **caduca** (R23, R66): si se
   tarda, el segundo clic no dispara y hay que volver a armarla.
3. Por cada parte: `adjuntar` con `commit` y, **solo si respondió
   `adjuntado`**, `cerrar` con `commit` (R64). Estados finales por parte:
   `cerrado`; **`adjuntado`** (gráfico dentro, cierre pendiente) con su botón
   **«Reintentar el cierre»** en el recuadro ámbar; `error_grafico` en rojo; o
   `ya_cerrada`.

### (b) La consola del navegador — cuando hace falta el JSON crudo

`F12` → **Consola**, en la pestaña del front. Va al **mismo origen**, así que
pasa por el proxy que autentica. Se usa para ver la respuesta entera —todo lo
de R21 tal y como viaja— y para acotar la llamada a **un solo** parte.

El fragmento de `adjuntar`, que se reutiliza en T25, T27, T28, T30 y T31
cambiando una constante:

```js
// F-012 bloque 9 - llamada a /api/adjuntar desde la consola del FRONT.
// SIN `commit` esto es un DRY-RUN: lee el ERP y NO escribe nada.
(async () => {
  const HASH8  = "<los 8 primeros caracteres del hash, los que pinta la tarjeta>";
  const COMMIT = false;   // <-- lo unico que se toca en T27, T28 y T30

  // El estado de la pantalla, tal cual: asi el PDF es EL MISMO objeto File que
  // se mando a /api/archivar, que es lo que hace que en Sigrid acabe el mismo
  // documento que hay en SharePoint.
  const app   = Alpine.$data(document.querySelector("[x-data]"));
  const parte = app.partes.find((p) => p.hash.startsWith(HASH8));
  if (!parte) { throw new Error("ese parte no esta en esta sesion"); }

  const opciones = { usuarioOid: app.usuario.usuarioOid, correo: app.usuario.correo };
  if (COMMIT) { opciones.commit = true; opciones.confirmado = true; }
  const cuerpo = Pipeline.cuerpoDeGrafico(parte, opciones);

  // OJO: NADA de `headers: {"Content-Type": ...}`. Lo pone el navegador con su
  // `boundary`; ponerlo a mano deja el formulario vacio y da un 400 enganoso.
  const t0 = performance.now();
  const r  = await fetch("/api/adjuntar", { method: "POST", body: cuerpo });
  const ms = Math.round(performance.now() - t0);

  console.log("HTTP " + r.status + "  ·  " + ms + " ms");
  console.log(JSON.stringify(await r.json(), null, 2));
})();
```

Y el de `/api/cerrar`, que es JSON y va sin fichero:

```js
// F-012 bloque 9 - llamada a /api/cerrar desde la consola del FRONT.
// SIN `commit` esto es un DRY-RUN: lee el ERP y NO escribe nada.
(async () => {
  const HASH8  = "<los 8 primeros caracteres del hash>";
  const COMMIT = false;   // <-- se pone a true en T26 (paso 2), T29 y T30

  const app   = Alpine.$data(document.querySelector("[x-data]"));
  const parte = app.partes.find((p) => p.hash.startsWith(HASH8));
  if (!parte) { throw new Error("ese parte no esta en esta sesion"); }

  const opciones = { usuarioOid: app.usuario.usuarioOid, correo: app.usuario.correo };
  if (COMMIT) { opciones.commit = true; opciones.confirmado = true; }

  const t0 = performance.now();
  const r  = await fetch("/api/cerrar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Pipeline.cuerpoDeCierre(parte, opciones)),
  });
  const ms = Math.round(performance.now() - t0);

  console.log("HTTP " + r.status + "  ·  " + ms + " ms");
  console.log(JSON.stringify(await r.json(), null, 2));
})();
```

> **El `Content-Type` sí va en `cerrar` y no va en `adjuntar`.** No es un
> descuido: uno es JSON y el otro es `multipart`.
>
> Las dos respuestas **no llevan ni el PDF, ni ningún campo manuscrito, ni el
> `oid` de quien confirma, ni el `gra_cod`** —que lleva el login del ERP dentro
> (R44, R53, R56)—. Por eso se pueden pegar en la casilla de resultado. Lo que
> **no** se pega nunca es el `/.auth/me`.
>
> El `ms` que imprime el fragmento es lo que pide R37: la duración real frente
> a los 35 s de `SIGRID_TIMEOUT_S`. Se anota en T25 y en T27.

---

## 5 · Las tareas, en el orden en que se ejecutan

### T25 · Dry-run del gráfico, con la ventana cerrada y luego abierta

**Qué se verifica y por qué.** Que el dry-run compone la petición de verdad
contra el ERP y devuelve **todo lo de R21**, y que **no cambia nada** en Sigrid
(R20). Es el único paso que se puede repetir sin coste, y el que sostiene todo
lo demás: sin un dry-run correcto no se escribe. De paso se comprueba §0.1 en
el propio ERP: **con la ventana cerrada no funciona ni el dry-run**.

**Precondiciones.** P0–P7 de §2.

**Pasos.**

1. **Foto de partida del ERP.** Con la ventana todavía cerrada:

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>"
   ```

   *Se espera*: `GRAFICO EN EL ERP : PASA`, con `graficos de la reclamacion =
   0` y el `MAX(ide) de dbo.log`. **Anota los dos**: son la referencia de T27 y
   de T28.
   *Si no sale eso*: «se esperaba UNA reclamación y han salido 0» → el código
   está mal o le falta la **barra** (en el ERP es `RS26.08/0123`; el guion es
   del nombre del fichero). Si `graficos` no es 0, esa reclamación **no
   sirve**: no se podría distinguir nuestro gráfico del que ya estaba. Vuelve a
   `15_reclamaciones_obra_prueba.ps1` y elige otra candidata.

2. **El dry-run con la ventana cerrada.** En la consola del front, el fragmento
   de `adjuntar` de §4 con `COMMIT = false`.

   *Se espera*: **`HTTP 503`** y un motivo que diga que el cierre está
   deshabilitado. **Esto es lo correcto y hay que verlo**: confirma §0.1 y que
   con la ventana cerrada no se toca la pasarela ni para leer (R39, R60).
   *Si sale `404`*: el despliegue no lleva el código de F-012 → Paso 0 (2).
   *Si sale `503` nombrando `SIGRID_API_BASE_URL` o `SIGRID_API_KEY`*: falta el
   Paso 0 (1).
   *Si sale `503` con `escritura_documental_deshabilitada`*: esa es **de la
   pasarela**, no nuestra → Paso 0 (3), y se pide al dueño.
   *Si sale `200`*: **para**. La ventana está abierta y eso hay que entenderlo
   antes de seguir.

3. **Abrir la ventana de escritura.** A partir de aquí no se deja la máquina
   sola, y recuerda §0.2: **esto abre también el cierre**.

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=true
   ```

   *Se espera*: el JSON de las App Settings, y la Function reiniciándose (unos
   segundos hasta que responda).

4. **El dry-run de verdad.** El mismo fragmento, otra vez, con
   `COMMIT = false`.

   *Se espera*: **`HTTP 200`**, `estado: "dry_run_ok"`, `idempotente: false`,
   `filas_afectadas: 0` y un objeto `dry_run` con **todo lo de R21**:
   `ya_estaba: false`, `incidencia`, `descripcion`, `estado_actual`
   {`codigo`, `descripcion`}, `login_sigrid`, `nombre_fichero` —**el mismo** que
   hay en SharePoint, con el guion largo—, `descripcion_grafico`
   (`PARTE FIRMADO`), `gratipide: 35`, `bytes`, `sha256`, `cod_previsto`,
   `idempotente_previsto`, `cerrable`, `ya_cerrada` y `avisos_pasarela`.
   **Anota `sha256`, `bytes`, `cod_previsto`, `login_sigrid` y la duración en
   ms** (R37).
   *Si sale `409`*: el motivo lo dice — parte no apto, no archivado, estado no
   cerrable, login sin correspondencia (F-009 R31), o uno de los códigos de la
   pasarela de `design.md` §7.3. Los tres que apuntan a **su** configuración
   —`tipo_de_concepto_no_coincide`, `clase_de_grafico_no_permitida`,
   `usuario_no_valido`— son Paso 0 (3).
   *Si sale `502`*: la pasarela falló. Aquí **sí** se puede repetir (§0.4), pero
   antes se lee el motivo.
   *Si sale `500` diciendo «gráfico sin traza»*: el parte no está guardado en
   `postventa.partes` → precondición P5.
   *Si `idempotente_previsto` viene `true`*: ese documento **ya cuelga** de esa
   reclamación. O la reclamación no estaba limpia (paso 1), o alguien ya ejecutó
   T27. No es un error, pero cambia lo que se verifica: anótalo y decide antes
   de seguir.
   *Si la duración pasa de 35 s*: es R37 y hay que anotarlo aunque haya salido
   bien; el siguiente parte más grande fallará.

5. **Nada ha cambiado en el ERP.** Se repite la foto, ahora exigiendo que el
   `MAX(ide)` sea idéntico (R36):

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>" -MaxIdeLogEsperado <el MAX(ide) del paso 1>
   ```

   *Se espera*: `PASA`, con `graficos de la reclamacion = 0` y el `MAX(ide)`
   igual.
   *Si alguna sale en rojo*: **para**. Un dry-run que mueve algo es un defecto
   grave y no se sigue con T27.

6. **La traza local del dry-run** (R42, R43):

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado dry_run_ok -Sha256Esperado "<el sha256 del paso 4>"
   ```

   *Se espera*: `TRAZA LOCAL DEL GRAFICO : PASA`, con `estado = dry_run_ok`,
   `marca de tiempo del dry-run = si`, **`reclamacion_ide relleno`** —la clave
   estable del ERP, guardada ya desde el dry-run (R43)— y el `sha256` idéntico
   al de la respuesta.
   *Si sale «trazas 0»*: el parte no está en `postventa.partes` (P5).
   *Si `reclamacion_ide` sale vacío*: es un defecto de R43 y se anota; el
   datamart se quedaría sin la única clave con la que cruzar nuestras filas.

**Casilla de resultado · T25**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Reclamación de la obra 404 (código) | |
| Paso 1 · gráficos de partida (¿0?) · `MAX(ide)` de `dbo.log` | |
| Paso 2 · HTTP con la ventana cerrada | |
| Paso 4 · HTTP, `estado`, `idempotente`, `filas_afectadas` | |
| Paso 4 · ¿estaban **todas** las cosas de R21? | |
| Paso 4 · `nombre_fichero` · `bytes` · `sha256` · `cod_previsto` | |
| Paso 4 · `login_sigrid` | |
| Paso 4 · avisos de la pasarela (¿huérfanos?) | |
| Paso 4 · **duración en ms** (R37, frente a 35 s) | |
| Paso 5 · ¿el ERP intacto? (`MAX(ide)` y 0 gráficos) | |
| Paso 6 · traza local (`dry_run_ok`, `reclamacion_ide`) | |
| **T25 queda marcada** | sí / no · motivo: |

---

### T26 · Dry-run del cierre con el gráfico **sin adjuntar** (R50, R49, R2, R62)

**Qué se verifica y por qué.** Las **dos mitades** de la regla nueva, y son
opuestas a propósito: el **dry-run** del cierre **no** exige el gráfico (R50),
para que los dos dry-run se puedan enseñar juntos antes de confirmar; y el
**commit** del cierre **sí** lo exige (R2), para que ninguna reclamación quede
cerrada sin su parte dentro. Se verifica además que el aviso ámbar de F-009 ya
no está (R48) y que en su lugar viaja el bloque `grafico` (R49).

**Precondiciones.** T25 marcada. Ventana abierta. La traza del gráfico en
`dry_run_ok` —es decir, **todavía no adjuntado**—. P6.

**Pasos.**

1. **El dry-run del cierre.** El fragmento de `cerrar` de §4 con
   `COMMIT = false`.

   *Se espera*: **`HTTP 200`**, `estado: "dry_run_ok"`, `filas_afectadas: 0`, y
   en `dry_run` un bloque **`grafico`** con `estado: "dry_run_ok"`,
   `nombre_fichero`, `sha256` y `adjuntado_at_utc: null`; más lo de F-009
   —`incidencia`, `descripcion`, `estado_origen`, `estado_destino` con
   `codigo: "CER"`, `login_sigrid`—.
   **Y `aviso_sin_grafico` NO tiene que aparecer** (R48): si aparece, el
   despliegue no lleva el código de F-012.
   *Si sale `409`*: el motivo lo dice, y **no** puede ser «no consta adjuntado»
   —eso es del commit, no del dry-run—. Si lo fuera, R50 está roto.

2. **El commit del cierre, que tiene que ser rechazado.** El mismo fragmento
   con `COMMIT = true`. **Es una petición de escritura de verdad, y por eso
   necesita la autorización P6** aunque la respuesta esperada sea un rechazo.

   *Se espera*: **`HTTP 409`** con un motivo que diga que este parte **no
   consta adjuntado** a la reclamación y que primero se adjunta con
   `POST /api/adjuntar` (R2, R62).
   *Si sale `200` con `estado: "cerrado"`*: **defecto grave**. Se ha cerrado una
   reclamación sin su parte dentro, que es exactamente lo que esta feature
   existe para impedir. **Para y anótalo.**

3. **La foto del ERP, idéntica**: no se ha cerrado nada y no se ha escrito
   ninguna fila de log.

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "<el estado del paso 1 de T25>" -MaxIdeLogEsperado <el MAX(ide) del paso 1 de T25>
   ```

   *Se espera*: `ESTADO DE LA RECLAMACION : PASA`, con el estado sin mover y el
   `MAX(ide)` igual.
   *Si el estado cambió*: contradice el paso 2 y hay que entenderlo antes de
   seguir.

**Casilla de resultado · T26**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1 · HTTP y `dry_run.grafico.estado` | |
| 1 · ¿aparecía `aviso_sin_grafico`? (tiene que ser **no**) | |
| 2 · HTTP del commit y motivo literal | |
| 3 · ¿el ERP intacto? (estado y `MAX(ide)`) | |
| **T26 queda marcada** | sí / no · motivo: |

---

### T27 · El primer gráfico real

**Qué se verifica y por qué.** Todo lo que un mock no puede probar: que la
pasarela acepta la petición tal y como este servicio la compone, que el commit
afecta a **3 filas** en **2 bases** (R27), que las tres se pueden releer y que
**el binario que hay dentro del ERP es byte a byte el que se mandó**, que
`dbo.log` **no** gana ninguna fila (R36), y que la traza local guarda lo que
debe **sin el login fuera de `gra_cod`** (R43, R44). Y, al final, lo único que
de verdad valida la feature para negocio: **que el parte se ve en la ficha de
la reclamación en Sigrid**.

> **AVISO.** Este es el primer paso que escribe en el ERP de producción, y **lo
> hace el servicio desplegado**, no esta máquina. Exige autorización expresa
> del humano para **esta reclamación concreta** (P6). Borrar un gráfico no lo
> hace la pasarela: sería otro proceso, a mano, desde la UI de Sigrid.

**Precondiciones.** T25 y T26 marcadas. Ventana abierta. P6 y P7. Conviene
tener cerrada **D2** (§2).

**Pasos** —en este orden y sin saltarse ninguno—.

1. **Foto de partida.** La misma del paso 1 de T25, otra vez, por si algo se ha
   movido:

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>"
   ```

   *Se espera*: `graficos de la reclamacion = 0` y el `MAX(ide)` de `dbo.log`.
   **Anótalos otra vez**: son los que se comparan en los pasos 4 y 5.

2. **Dry-run y LEERLO.** El fragmento de `adjuntar` con `COMMIT = false`, o el
   botón «Ver qué pasaría» del front.

   *Se espera*: lo del paso 4 de T25. **Leerlo no es una formalidad**: lo que
   se confirma en el paso 3 es exactamente esto, y el `sha256` de aquí es el que
   se coteja en el paso 4.
   *Si el `sha256` no es el de T25*: los bytes del parte han cambiado entre las
   dos sesiones (D-L). No es un fallo, pero **anota el nuevo**, que es el que
   vale.

3. **Confirmar y ejecutar con `commit`.** Vía (a) de §4 —«Cerrar las
   incidencias» → «Sí, cerrar»—, que hace **primero** el gráfico y solo después
   el cierre. Si se quiere aislar el gráfico y dejar el cierre para T29, se usa
   la vía (b): el fragmento de `adjuntar` con **`COMMIT = true`**.

   *Se espera*: **`HTTP 200`**, `estado: "adjuntado"`, **`idempotente: false`**,
   **`filas_afectadas: 3`** (R27), y en la respuesta el `numero_incidencia`.
   **El `gra_cod` NO viaja en la respuesta** —lleva el login dentro (R44)—: se
   lee de la traza local en el paso 5, y tiene que coincidir con el
   `cod_previsto` del dry-run en su formato, sello `AAAAMMDDHHMMSS` + 4 dígitos
   + `.` + login. **Anota la duración en ms.**
   *Si sale `409`*: la pasarela ha rechazado, **sin escribir nada**. El código
   está en el motivo, y `design.md` §7.3 dice qué es cada uno.
   *Si sale `502`*: puede que la escritura saliera y no volviera la respuesta
   (§0.4). **Aquí el reintento es seguro**: se repite la misma llamada, y si el
   documento ya estaba, responderá `adjuntado` con `idempotente: true`. Antes de
   repetir, mira el paso 4 para saber qué hay.
   *Si sale `500` «gráfico sin traza»*: **el gráfico SÍ está** en el ERP y lo
   que falló fue la traza local. **No se repite el adjuntado**; se anota y se
   sigue por el paso 4.
   *Si sale `200` con `committed: true` y `filas_afectadas` distinto de 3*: es un
   gráfico a medias, el servicio lo trata como error y **no lo da por bueno**
   (R27).

4. **Las tres filas, y el binario.** Es el paso que comprueba que lo que hay
   dentro del ERP es lo que se mandó:

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>" -Cod "<el gra_cod>" -MaxIdeLogEsperado <el MAX(ide) del paso 1> -NombreEsperado "<el nombre_fichero del dry-run>" -DescargarYComparar -Sha256Esperado "<el sha256 del dry-run>"
   ```

   *Se espera*: `GRAFICO EN EL ERP : PASA`, con todo en verde:
   - **fila de negocio**: 1 fila, `res = PARTE FIRMADO`, `gratipide = 35`,
     `vin = 3`, `ima IS NULL`, `nom` = el nombre de SharePoint;
   - **fila documental**: 1 fila, `bytes` (`DATALENGTH(ima)`) = los del dry-run,
     `gratipide = 0`, `res` vacía, `emp` **igual en las dos bases**;
   - **enlace `rcg`**: 1 fila, apuntando a la reclamación, `cla = 0`, y `pos`
     anotado (múltiplo de 64);
   - **`sha256` del binario DENTRO del ERP** idéntico al del dry-run;
   - **`MAX(ide)` de `dbo.log` sin subir** (R36).

   *Si el `sha256` no coincide*: el documento que hay dentro no es el que se
   mandó. **Para**: es lo más grave que puede salir de este bloque.
   *Si `MAX(ide)` ha subido*: algo escribió en `dbo.log` por el gráfico, y R36
   dice que no debería. Anótalo con el número exacto.
   *Si «bytes descargados» no cuadra con `DATALENGTH`*: comprueba que el script
   sea posterior a la corrección D1 del 2026-09-06 —antes imprimía la longitud
   de la cadena del `sha256`, siempre 64—.
   *Si la fila documental no está pero la de negocio sí*: la transaccionalidad
   de la pasarela no es la que dice `sigrid_api.md`. Es un hallazgo **de su
   dueño**, no algo que se arregle aquí.

5. **La traza local** (R43, R44):

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado -IdempotenteEsperado no -UsuarioOid "<el oid>" -LoginQueNoDebeAparecer "<el login_sigrid del dry-run>" -Sha256Esperado "<el sha256 del dry-run>"
   ```

   *Se espera*: `PASA`, con `estado = adjuntado`, `idempotente = no`,
   `marca de tiempo del adjuntado = si`, `oid de quien confirmo = si`,
   `gra_cod`, `ide de negocio` y `ide del enlace` **rellenos**, y
   **`el login NO esta fuera de gra_cod = no`**. El script anota además
   `el login SI esta dentro de gra_cod`, que es lo esperado y es la excepción
   declarada de R44.
   *Si el login aparece fuera de `gra_cod`*: es un defecto de R44 y se anota.
   *Si `ide documental` sale vacío*: solo es normal en el caso idempotente. Aquí
   no lo es: anótalo.

6. **El humano abre la ficha de la reclamación en Sigrid y ve el parte.** Es la
   *acceptance 1* de la feature, y es lo único de este guion que no comprueba
   ningún script: que el documento se ve, se abre y es el parte correcto.

   *Se espera*: el documento en la pestaña de gráficos de la reclamación, con su
   nombre, y que al abrirlo sea el parte firmado.
   *Si se ve pero no donde Posventa lo busca*: mira el `gratipide` del paso 4 y
   **D2** de §2 — la clase puede no ser la que Posventa espera.

**Casilla de resultado · T27**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Reclamación (código) · **autorización expresa del humano** | sí / no |
| 1 · gráficos de partida · `MAX(ide)` de `dbo.log` | |
| 2 · dry-run leído (`sha256`, `bytes`, `cod_previsto`) | |
| 3 · HTTP, `estado`, `idempotente`, `filas_afectadas` | |
| 3 · **duración en ms** del commit (R37) | |
| 4 · fila de negocio (`res`, `gratipide`, `vin`, `ima NULL`, `nom`) | |
| 4 · fila documental (`bytes`, `gratipide 0`, `res` vacía, `emp` igual) | |
| 4 · enlace `rcg` (`con`, `pos`, `cla 0`) | |
| 4 · **`sha256` del binario dentro del ERP** | coincide / NO coincide |
| 4 · **`MAX(ide)` de `dbo.log`** | sin subir / ha subido a … |
| 5 · traza local (`adjuntado`, `idempotente no`, `oid` sí, login fuera de `gra_cod` no) | |
| 6 · **¿se ve el parte en la ficha de Sigrid?** | sí / no |
| **T27 queda marcada** | sí / no · motivo: |

---

### T28 · Idempotencia de extremo a extremo (R24, R25, R26)

**Qué se verifica y por qué.** Que pedir dos veces lo mismo **no cuelga un
segundo documento**, y que eso funciona en **las dos capas**: la traza local
—que ni siquiera llama a la pasarela— y la propia pasarela por tamaño y
`sha256`. La segunda es la que salva el caso real: la traza perdida o el corte
de red del que habla §0.4.

**Precondiciones.** T27 marcada, con la traza local en `adjuntado`.

**Pasos.**

1. **Capa 1 · la traza local.** El fragmento de `adjuntar` de §4 con
   `COMMIT = true`, sobre **el mismo** parte.

   *Se espera*: **`HTTP 200`**, `estado: "adjuntado"`, `filas_afectadas: 0`, y
   **ninguna llamada a la pasarela**. Que no la hubo se comprueba así:

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado
   ```

   *Se espera*: `PASA`, con el **mismo** `gra_cod` y los mismos `intentos` que
   en T27. Si se quiere la prueba directa, el log de la Function dice que se
   sirvió de la traza.
   *Si `intentos` sube*: se volvió a llamar a la pasarela, y la capa 1 no está
   cortando.

2. **Capa 2 · la pasarela.** Para probarla hay que quitar la capa 1, y eso es
   **borrar la fila de `postventa.graficos`** de ese parte. Es el esquema propio
   y es un `DELETE` de una fila, no DDL; **lo hace el humano, a mano, y lo
   anota**. Si no se quiere tocar la base, se salta el paso y **se anota que la
   capa 2 no se ejercitó de punta a punta** (el test unitario la cubre).

   El script —se guarda **fuera del repositorio** o se pega en la ventana:

   ```powershell
   # T28 capa 2 - borra UNA fila de la traza propia. Esquema `postventa`, nada
   # a nivel de servidor: `psql-albaranes-rs9k2` lo comparten otros proyectos.
   $hashParte = Read-Host "hash_parte completo"
   $servidor  = Read-Host "Host de PostgreSQL"
   $clave     = Read-Host "Contrasena de postventa_app" -AsSecureString
   if ((Read-Host "Escribe BORRAR para confirmar") -ne "BORRAR") { throw "cancelado" }
   $env:PG_HOST_TEMP = $servidor
   $env:PG_PASSWORD_TEMP = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($clave))
   $env:HASH_TEMP = $hashParte
   $codigo = 'import os, psycopg
   dsn = ("host={0} port=5432 dbname=postventa user=postventa_app "
          "password={1} sslmode=require").format(
              os.environ["PG_HOST_TEMP"], os.environ["PG_PASSWORD_TEMP"])
   with psycopg.connect(dsn) as cx, cx.cursor() as cur:
       cur.execute("DELETE FROM postventa.graficos WHERE hash_parte = %s",
                   (os.environ["HASH_TEMP"],))
       print("filas borradas:", cur.rowcount)'
   & .\services\postventa-api\.venv\Scripts\python.exe -c $codigo
   Remove-Item Env:\PG_HOST_TEMP, Env:\PG_PASSWORD_TEMP, Env:\HASH_TEMP -ErrorAction SilentlyContinue
   ```

   Y la línea que lo ejecuta, si se guardó como fichero:

   ```
   powershell -ExecutionPolicy Bypass -File .\borrar_traza_grafico.ps1
   ```

   *Se espera*: `filas borradas: 1`.
   *Si borra 0*: el `hash_parte` no es el completo, o la traza está bajo otra
   incidencia.
   *Si borra más de 1*: **para**. La clave primaria es `hash_parte`; más de una
   fila es imposible y significa que se ha ejecutado contra otra cosa.

3. **Repetir el `commit` sin la traza.** Otra vez el fragmento de `adjuntar`
   con `COMMIT = true`.

   *Se espera*: **`HTTP 200`**, `estado: "adjuntado"`, **`idempotente: true`**,
   `filas_afectadas: 0`. **Eso es un éxito** (§0.3): la pasarela ha reconocido
   el documento por tamaño y `sha256` y no ha escrito nada.
   *Si sale `200` con `idempotente: false` y `filas_afectadas: 3`*: **defecto
   grave**. Hay un **segundo** gráfico colgando de la reclamación. Se comprueba
   en el paso 4, se anota, y borrarlo es un proceso manual desde la UI de Sigrid
   que decide el humano.

4. **La foto del ERP, idéntica: UN gráfico y UN enlace.**

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>" -Cod "<el gra_cod>" -MaxIdeLogEsperado <el MAX(ide) del paso 1 de T27>
   ```

   *Se espera*: `PASA`, con **una** fila de negocio, **una** documental, **un**
   enlace y el `MAX(ide)` sin subir. Y, para contarlos de verdad, la columna
   `GRAFICOS` de esa reclamación tiene que seguir diciendo **1**:

   ```
   powershell -ExecutionPolicy Bypass -File infra\15_reclamaciones_obra_prueba.ps1
   ```

5. **La traza vuelve a estar, y con `idempotente = si`.**

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado -IdempotenteEsperado si
   ```

   *Se espera*: `PASA`, con el **mismo** `gra_cod` que en T27 y
   `idempotente = si`. El `ide documental` puede salir vacío: en el caso
   idempotente la pasarela no lo devuelve **[MEDIDO]**, y por eso el script lo
   anota en vez de exigirlo.

**Casilla de resultado · T28**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1 · HTTP, `estado`, `filas_afectadas` · ¿`intentos` sin subir? | |
| 2 · ¿se borró la fila de `postventa.graficos`? (o «no ejecutado») | |
| 3 · HTTP, `estado`, **`idempotente`**, `filas_afectadas` | |
| 4 · ¿**un** gráfico y **un** enlace? · `MAX(ide)` | |
| 5 · traza (`adjuntado`, `idempotente si`, mismo `gra_cod`) | |
| **T28 queda marcada** | sí / no · motivo: |

---

### T29 · «Adjuntado pero no cerrado», y el reintento que cierra (R3, acceptance 2)

**Qué se verifica y por qué.** El escenario real de un fallo a mitad: el gráfico
está dentro y la reclamación sigue abierta. Es un estado **legítimo** del
sistema —no un error— y hay que poder verlo en la pantalla y salir de él. Y al
final del paso, lo que da sentido a toda la feature: **la primera reclamación
cerrada por este servicio con su parte dentro**. La anomalía que F-009 aceptaba
como riesgo no llega a producirse ni una vez.

**Precondiciones.** T27 marcada. La reclamación **abierta y con su gráfico**.
Ventana abierta. P6 —el cierre es la segunda escritura y necesita su propia
autorización—.

**Pasos.**

1. **Mirar la pantalla.** En el front, el parte tiene que estar en el recuadro
   ámbar: «El parte está **adjunto en Sigrid** y la incidencia sigue abierta»,
   con el botón **«Reintentar el cierre»** (R65).
   *Si no está ese recuadro*: o el parte no quedó en `adjuntado`, o la sesión se
   recargó y perdió el estado de pantalla. El estado real es el de la traza
   local, no el del navegador: compruébalo con `17_traza_grafico_local.ps1`.

2. **Dry-run del cierre**, ahora con el gráfico ya dentro. El fragmento de
   `cerrar` de §4 con `COMMIT = false`.

   *Se espera*: `200`, `estado: "dry_run_ok"`, y en `dry_run.grafico`
   **`estado: "adjuntado"`** con `nombre_fichero`, `sha256` y
   `adjuntado_at_utc` **relleno** (R49). Es la diferencia con T26, y es lo que
   quien confirma tiene que ver.

3. **Anotar el estado de partida del ERP**, que es lo que compara el paso 5:

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>"
   ```

   *Se espera*: la tabla con `ide`, `emp`, `est`, el estado legible, el `res`,
   el `tiemod` y el `MAX(ide)` de `dbo.log`. **Anótalos todos.**

4. **Cerrar.** El botón «Reintentar el cierre» del front —que **no vuelve a
   pedir el gráfico**: ya está dentro y la confirmación sigue valiendo para ese
   parte (R65)— o el fragmento de `cerrar` con `COMMIT = true`.

   *Se espera*: **`HTTP 200`**, `estado: "cerrado"` y **`filas_afectadas: 2`**
   (F-009 R22): una de `con` y una de `log`.
   *Si sale `409` diciendo que el estado cambió desde el dry-run*: el control
   optimista de F-009 R11 ha saltado y **no se ha aplicado nada**. Vuelve al
   paso 3.
   *Si sale `409` diciendo que no consta adjuntado*: la traza se borró en T28 y
   no se recompuso. Vuelve al paso 3 de T28.
   *Si sale `502`*: **NO se reintenta** (F-009 R27). Es la regla contraria a la
   del gráfico (§0.4). Se sigue con el paso 5 para ver qué hay en el ERP, y lo
   que se haga después lo decide el humano.
   *Si sale `500` «cierre sin traza»*: **la incidencia SÍ está cerrada** y lo
   que falló fue la traza local. No se repite el cierre.

5. **`con.est` en `CER`, `tiemod` sin mover, y la fila de log** (como T24 de
   F-009):

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER" -TiemodEsperado "<el tiemod del paso 3>"
   ```

   *Se espera*: `PASA`. **Anota el nuevo `MAX(ide)` de `dbo.log`**: tiene que
   ser el del paso 3 **más uno** —esta vez sí sube, y lo sube el cierre, no el
   gráfico (§0.5)—.

   ```
   powershell -ExecutionPolicy Bypass -File infra\10_log_cierre_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -DesdeIde <el MAX(ide) del paso 3> -LoginEsperado "<el login_sigrid>" -EmpEsperada <el emp del paso 3> -ResEsperado "<el res del paso 3>"
   ```

   *Se espera*: `FILA DE AUDITORIA DEL CIERRE : PASA`, con **una** fila nueva,
   `tex = Cerrar parte (postventa-incidencias)` y **`huso de fec/hor = HORA
   LOCAL (correcto)`**.
   *Si el huso sale `UTC (INCORRECTO)`*: es el defecto que anticipa §0.2 del
   guion del bloque 8 de F-009. La fila ya está escrita; **no la toques**,
   anótalo y para: corregirla es otra escritura en producción.

6. **El gráfico sigue ahí.** Cerrar no lo desengancha:

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>" -Cod "<el gra_cod>"
   ```

   *Se espera*: `PASA`, con sus tres filas y su enlace.

7. **La traza local del cierre** (F-009 R41, R43):

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado cerrado -UsuarioOid "<el oid>" -LoginQueNoDebeAparecer "<el login del ERP>"
   ```

   *Se espera*: `PASA`, con `estado = cerrado`, los dos códigos de estado
   guardados, `oid de quien confirmo = si` y el login **no** en la traza.

**Casilla de resultado · T29**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| **Autorización expresa del humano para cerrar** | sí / no |
| 1 · ¿se veía el recuadro ámbar «adjunto y abierta»? | |
| 2 · `dry_run.grafico.estado` (tiene que ser `adjuntado`) | |
| 3 · `est` / `res` / `tiemod` / `MAX(ide)` de partida | |
| 4 · HTTP, `estado`, `filas_afectadas` | |
| 5 · `con.est` = `CER` · `tiemod` sin mover · nuevo `MAX(ide)` (= anterior + 1) | |
| 5 · fila de `dbo.log` campo a campo · **huso** | LOCAL / UTC / no coincide |
| 6 · ¿sigue habiendo un gráfico y un enlace? | |
| 7 · traza local del cierre (`cerrado`, `oid` sí, login no) | |
| **T29 queda marcada** | sí / no · motivo: |

---

### T30 · Reintento sobre lo ya cerrado (R16, R30; F-009 R18, R42)

**Qué se verifica y por qué.** Que repetir el flujo entero sobre una
reclamación ya cerrada **no escribe nada en ninguno de los dos sitios** y **no
pisa ninguna de las dos trazas**, que son terminales. Es el escenario real:
alguien vuelve a pasar el mismo parte.

**Precondiciones.** T29 marcada. La ventana **sigue abierta**.

**Pasos.**

1. **Anotar el `MAX(ide)` actual de `dbo.log`** (el de después del cierre):

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER"
   ```

   *Se espera*: `PASA`, estado `CER`. **Anota el `MAX(ide)`.**

2. **Repetir el adjuntado, con `commit`.** El fragmento de `adjuntar` con
   `COMMIT = true`.

   *Se espera*: `200` con `estado: "adjuntado"` **servido desde la traza**
   (capa 1, sin llamar a nadie). Si la traza se borró en T28 y no se recompuso,
   lo que se espera en su lugar es **`ya_cerrada`** sin adjuntar nada: una
   reclamación en `CER` no recibe un segundo gráfico (R16).
   *Si sale `200` con `idempotente: false` y `filas_afectadas: 3`*: se ha
   colgado un segundo documento. **Para y anótalo.**

3. **Repetir el cierre, con `commit`.** El fragmento de `cerrar` con
   `COMMIT = true`.

   *Se espera*: **`HTTP 200`** con **`estado: "ya_cerrada"`** y
   `filas_afectadas: 0`. **No es un error** (F-009 R18): el dry-run detecta que
   la reclamación ya está en el estado de cierre y no compone ninguna escritura.
   *Si sale `200` con `estado: "cerrado"` y `filas_afectadas: 2`*: **defecto
   grave**, se ha escrito una segunda vez. Para y anótalo.

4. **Nada ha subido en el ERP:**

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>" -Cod "<el gra_cod>" -MaxIdeLogEsperado <el MAX(ide) del paso 1>
   ```

   *Se espera*: `PASA`, con **un** gráfico, **un** enlace y el `MAX(ide)`
   idéntico.
   *Si ha subido*: se ha escrito una fila de log de más. Mírala con
   `infra\10_log_cierre_sigrid.ps1 -DesdeIde <el del paso 1>`.

5. **Las dos trazas locales, sin pisar** (R30 y F-009 R42):

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado
   ```

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado cerrado -UsuarioOid "<el oid>"
   ```

   *Se espera*: las dos `PASA`, con las marcas de tiempo **las de T27 y T29**,
   no unas nuevas.
   *Si la del gráfico ha pasado a `ya_cerrada`, o la del cierre a otra cosa*: se
   ha pisado una traza terminal, que es justo lo que R30 y R42 prohíben.

**Casilla de resultado · T30**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1 · `MAX(ide)` antes del reintento | |
| 2 · HTTP y `estado` de `/api/adjuntar` (`adjuntado` o `ya_cerrada`) | |
| 3 · HTTP, `estado` y `filas_afectadas` de `/api/cerrar` | |
| 4 · ¿un gráfico, un enlace, `MAX(ide)` sin subir? | |
| 5 · ¿las dos trazas con las marcas de tiempo originales? | |
| **T30 queda marcada** | sí / no · motivo: |

---

### T31 · Un rechazo de la pasarela, sin escritura (R33, R59)

**Qué se verifica y por qué.** Que un rechazo de negocio de la pasarela sale
como **409** con su código, deja el ERP **intacto** y deja traza de `error`. Se
provoca con una App Setting **de este servicio** —nunca de la pasarela— puesta a
una clase que su lista blanca no admite.

> **Se hace sobre OTRA reclamación candidata de la obra 404**, no sobre la de
> T27: la de T27 ya tiene su gráfico, y la capa 1 de idempotencia respondería
> desde la traza sin llegar a la pasarela, así que el rechazo no se produciría.
> Esa otra reclamación necesita **su propia autorización** (P6), aunque el
> resultado esperado sea que no se escriba nada.
>
> **Si el humano no quiere tocar App Settings para esto**, se anota como **no
> ejecutado** y vale el test unitario que ya cubre R33. Es lo que dice
> `tasks.md`, y no bloquea T32.

**Precondiciones.** T30 marcada. Ventana abierta. Otra reclamación de la obra
404 con su parte recorrido (mismas condiciones que P5) y su autorización.

**Pasos.**

1. **Poner la clase a un valor que la pasarela no admite:**

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings SIGRID_GRATIPIDE_PARTE=34
   ```

   *Se espera*: el JSON de las App Settings y la Function reiniciándose.

2. **Comprobar que el cambio está puesto** —es una App Setting plana, así que
   esta sí se lee:

   ```
   az functionapp config appsettings list -g rg-postventa-dev -n func-postventa-dev --query "[?name=='SIGRID_GRATIPIDE_PARTE'].value" -o tsv
   ```

   *Se espera*: `34`.

3. **Dry-run del gráfico sobre la otra reclamación.** El fragmento de
   `adjuntar` con `COMMIT = false` y el `HASH8` de **ese** parte.

   *Se espera*: **`HTTP 409`** con un motivo que nombre
   **`clase_de_grafico_no_permitida`**.
   *Si sale `200`*: la lista blanca de la pasarela admite el 34, así que este
   caso no prueba nada. Anótalo y prueba con otro valor que no esté en
   `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` (el Paso 0 (3) dice cuáles hay).
   *Si sale `503`*: es otra cosa —ventana o configuración—, no el rechazo que se
   busca.

4. **La foto del ERP de esa reclamación, idéntica:**

   ```
   powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<la otra RSaa.mm/nnnn>"
   ```

   *Se espera*: `graficos de la reclamacion = 0` y el `MAX(ide)` sin cambios. Un
   rechazo de negocio se levanta **antes** del `COMMIT` de la pasarela, así que
   no deja nada.

5. **La traza local quedó en `error`** (R33, y §3.2 del informe: el dry-run
   también deja traza de error):

   ```
   powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<la otra RSaa.mm/nnnn>" -EstadoEsperado error
   ```

   *Se espera*: `PASA`, con `estado = error` y un `motivo` que nombre el código
   de la pasarela.

6. **Restaurar, y comprobarlo. Esto no se deja para luego:**

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings SIGRID_GRATIPIDE_PARTE=35
   ```

   ```
   az functionapp config appsettings list -g rg-postventa-dev -n func-postventa-dev --query "[?name=='SIGRID_GRATIPIDE_PARTE'].value" -o tsv
   ```

   *Se espera*: `35`. Si se dejara en 34, el siguiente cierre real fallaría con
   un 409 que nadie sabría explicar.

**Casilla de resultado · T31**

| Campo | Valor |
|---|---|
| Fecha y hora | ejecutado / **no ejecutado** (motivo): |
| Otra reclamación usada (código) · autorización | |
| 3 · HTTP y código de la pasarela en el motivo | |
| 4 · ¿el ERP intacto? (0 gráficos, `MAX(ide)`) | |
| 5 · traza local en `error` con su motivo | |
| 6 · **`SIGRID_GRATIPIDE_PARTE` restaurada a 35** | sí / no |
| **T31 queda marcada** | sí / no · motivo: |

---

### T32 · Cerrar la ventana y dejar constancia

**Qué se verifica y por qué.** Que el entorno queda como estaba: sin ventana de
escritura abierta, sin secretos en la sesión, y con lo medido escrito donde se
pueda encontrar mañana. Es la última tarea del bloque **y se ejecuta salga bien
o mal**, incluso si se paró en mitad de T27.

**Precondiciones.** Ninguna. Se ejecuta siempre.

**Pasos.**

1. **Cerrar la ventana de escritura. Siempre, y lo primero.**

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false
   ```

   *Se espera*: el JSON de las App Settings.

2. **Comprobarlo, no darlo por hecho:**

   ```
   az functionapp config appsettings list -g rg-postventa-dev -n func-postventa-dev --query "[?name=='CIERRE_HABILITADO'].value" -o tsv
   ```

   *Se espera*: `false`. `desplegar_backend.ps1` la devuelve a `false` en cada
   despliegue, pero eso es la red de seguridad del **siguiente** despliegue: la
   ventana se cierra aquí y ahora, a mano.

3. **Comprobar que de verdad está cerrada, en el borde**: el fragmento de
   `adjuntar` de §4 con `COMMIT = false`.

   *Se espera*: **`HTTP 503`**. Es la misma comprobación del paso 2 de T25, y es
   la que vale: la App Setting puede estar puesta y la Function no haber
   reiniciado todavía.

4. **Limpiar la sesión de la consola**, para que la clave no siga en memoria:

   ```
   Remove-Item Env:\SIGRID_API_KEY, Env:\SIGRID_API_BASE_URL, Env:\SIGRID_BASE_DATOS -ErrorAction SilentlyContinue
   ```

5. **Rellenar las casillas de resultado de este fichero** y commitearlo.

6. **Anotar en `progress/current.md`**, porque son números que no están en
   ningún otro sitio:
   - las **duraciones medidas** de T25 (dry-run) y T27 (commit), frente a los
     **35 s** de `SIGRID_TIMEOUT_S` (R37);
   - el **tamaño real en bytes** del parte usado, frente a `GRAFICO_MAX_BYTES`
     (10 MB) y frente al `SIGRID_DOCUMENT_MAX_BYTES` de la pasarela;
   - si T31 se ejecutó o no, y por qué.

7. **Marcar en `specs/F-012-grafico-sigrid/tasks.md`** las tareas que hayan
   pasado. Lo hace el humano.

8. **Actualizar `azure-apps/postventa_incidencias.md`**: si T29 pasó, deja de
   ser verdad que «todavía no se ha ejecutado ni un cierre real», y además hay
   que decir que el primero fue **con su gráfico dentro**. La regla de propiedad
   de `CLAUDE.md` obliga a hacerlo **en este mismo trabajo**. Commit local allí,
   sin push.

9. **Dejar constancia del estado del bloque 8 de F-009.** T29 ya ha ejercitado
   de hecho sus T22, T24, T25 y T27 sobre la obra 404: al reanudar F-009, su
   guion se recorre **con lo que quede** (ver la nota fechada de
   `progress/guion_bloque8_F-009.md`).

**Casilla de resultado · T32**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1–2 · `CIERRE_HABILITADO` = `false` | sí / no |
| 3 · `/api/adjuntar` responde 503 | sí / no |
| 4 · sesión limpiada | sí / no |
| 6 · duración T25 · duración T27 · tamaño del parte | |
| 6 · ¿alguna pasó de 35 s? | |
| 8 · `azure-apps/postventa_incidencias.md` actualizado | sí / no |
| **T32 queda marcada** | sí / no · motivo: |

---

## 6 · Al terminar, salga bien o mal

**T32 es esto, y por eso está dentro de §5 y no fuera**: cerrar la ventana no es
el epílogo del final feliz, es la última tarea del bloque y se ejecuta también
cuando se para en mitad de T27.

Si el bloque se interrumpe —una llamada, un fallo, una duda—, el orden es
siempre el mismo:

1. **Cerrar la ventana** (T32, pasos 1–3). Antes que anotar nada.
2. **Limpiar la sesión** (T32, paso 4).
3. **Anotar dónde se paró y por qué**, en la casilla de la tarea y en
   `progress/current.md`.
4. Si lo que paró el bloque fue un defecto del servicio, marcar F-012 `blocked`
   en `harness/features.json` con el motivo en `progress/current.md`. Si fue una
   precondición de la pasarela, **no es un `blocked` nuestro**: se pide al dueño
   de `sigrid-api` y se anota.

Y una cosa que **no** se hace nunca al terminar: dejar la ventana abierta
«porque mañana seguimos». Un redespliegue la cerraría, sí, pero mientras tanto
`/api/cerrar` y `/api/adjuntar` escriben en el ERP de producción para cualquiera
que tenga sesión en el front.

---

## 7 · Qué se anota y qué NO

**Sí**: códigos HTTP, `estado`, `idempotente`, `filas_afectadas`, códigos de
estado del ERP (`PTE`, `CER`), `ide` de la reclamación, del gráfico —negocio y
documental— y del enlace, `MAX(ide)`, `pos`, `tiemod`, `bytes`, el `sha256` del
PDF, el `nombre_fichero`, la clase (`gratipide`), las duraciones en ms, el
veredicto de cada script, y el login del ERP (no es secreto: queda escrito en
`dbo.gra.usu` y en `dbo.log.usu`, a la vista de cualquiera en Sigrid).

**No, nunca**: la raíz de la pasarela ni ningún FQDN, la clave de función, la
contraseña de PostgreSQL, los nombres de recurso de `sigrid-api`, el contenido
de `/.auth/me`, el `oid` de Entra —dato personal seudónimo—, el correo del
usuario, y **nada del parte**: ni el DNI del cliente, ni sus observaciones
manuscritas, ni el nombre del propietario, ni un solo byte del PDF.

**El `gra_cod`, con cuidado.** Lleva el login del ERP pegado al sello, y por eso
no viaja en las respuestas HTTP (R44). Anotarlo en la casilla de resultado de
este fichero **sí** vale —el login no es secreto—, pero no se pega en un correo
ni en un ticket junto al nombre de la persona.

Los códigos de incidencia de los **ejemplos** de este guion son marcadores
(`RSaa.mm/nnnn`) a propósito; el real solo va en la casilla de resultado, y es un
código de expediente de la **obra de prueba**, no un dato personal.

---

## 8 · Hallazgos de la preparación de este guion

| # | Hallazgo | Dónde | Qué se propone |
|---|---|---|---|
| **H1** | **`/api/adjuntar` no se puede llamar a mano.** El cuerpo es un `multipart` con los bytes del PDF, ocho campos y un `boundary`. `tasks.md` dice «`/api/adjuntar` sin `commit`» sin decir por dónde, igual que le pasaba a `tasks.md` de F-009 con `/api/cerrar` (H3 de aquel guion) | `interface_adapters/api/adjuntar.py`, `js/pipeline.js` | Resuelto en §4 con el fragmento de consola que reutiliza `Pipeline.cuerpoDeGrafico` y el estado de Alpine. **No es un defecto**: es consecuencia de D-H —los bytes los manda el front— |
| **H2** | **Poner `Content-Type` en la llamada de `adjuntar` la rompe en silencio.** El navegador tiene que componer el `boundary`; si se fija la cabecera a mano, el backend recibe un formulario vacío y responde `400` diciendo que faltan los siete campos y el fichero | §4 de este guion | Escrito como aviso en §0.6 y dentro del propio fragmento. Es el error más fácil de cometer del bloque, y su síntoma —un `400` que enumera campos que sí se mandaron— manda a buscar donde no es |
| **H3** | **La ventana es una sola para el gráfico y el cierre**, y `tasks.md` lo da por sabido: T25 la abre «para el gráfico» y T29 cierra una reclamación con ella | `design.md` D-B, `infra/desplegar_backend.ps1` | Recogido en §0.2 y repetido en el paso 3 de T25. Ya estaba avisado en `progress/impl_F-012.md` §8.2 y en `review_F-012.md` §8 |
| **H4** | **`filas_afectadas: 0` significa cosas opuestas según el endpoint.** En `adjuntar` con `idempotente: true` es un **éxito** (el documento ya está); en `cerrar` es que no se aplicó nada (F-009 R11). El mismo número, en la misma pantalla, en la misma tanda | `azure-apps/sigrid_api.md` §8.8, `design.md` §7.2 | Recogido en §0.3, y separado en las casillas de T28 y T30. **No se propone cambiar nada**: el campo que decide es `ok` / `estado`, no `filas_afectadas` |
| **H5** | **El reintento tras un `502` es seguro en `adjuntar` y prohibido en `cerrar`**, y los dos `502` salen del mismo botón. Es la regla más fácil de invertir bajo presión | `design.md` §9.4, F-009 R27 | Recogido en §0.4 y repetido en el paso 3 de T27 y en el paso 4 de T29 |
| **H6** | **T28 capa 2 exige borrar una fila de `postventa.graficos`**, y `tasks.md` dice «el humano, a mano» sin dar la forma. Los scripts `12_` y `17_` son de solo lectura y no sirven | `tasks.md` T28 | Escrito el bloque de PowerShell del paso 2 de T28, con confirmación tecleada y `rowcount` impreso. **No se ha creado un script en `infra/`**: es una escritura de un solo uso, y un script re-ejecutable que borra trazas es justo lo que no conviene dejar por ahí |
| **H7** | **T31 no puede usar la reclamación de T27.** Con la traza en `adjuntado`, la capa 1 respondería desde la traza y no llegaría a la pasarela, así que el rechazo que se quiere provocar no se produciría | `design.md` §9.3, `tasks.md` T31 | Recogido como aviso al principio de T31: se usa **otra** candidata de la obra 404, con su propia autorización. `tasks.md` ya decía «otra reclamación candidata», pero no el porqué |
| **H8** | **La lectura de P0 sin `--query` vuelca todas las App Settings de la pasarela**, credenciales de escritura del ERP incluidas, a la consola de alguien. `tasks.md` P0 dice «leída sin ver ningún secreto» sin decir cómo | §1, Paso 0 (3) | Escrito el filtro `--query` que devuelve solo las seis que no son secretos. Y anotado que, aunque volcara las demás, las referencias a Key Vault salen **sin resolver**: es la misma limitación que impide leer así nuestra `SIGRID_API_BASE_URL` |
| **H9** | **Dos precondiciones documentales no estaban en la lista del bloque 9**: la aceptación de los 5 supervivientes de mutación —que el nivel `critico` exige por escrito— y la confirmación de `PV002` con Posventa. Las dos están en `review_F-012.md` §8, pero no en `tasks.md` | `tasks.md` bloque 9, `review_F-012.md` §8 | Añadidas como **D1** y **D2** en §2, marcadas como documentales: **no bloquean técnicamente** —T25 se puede ejecutar sin ellas— pero el bloque no se da por cerrado con alguna abierta. D2 conviene tenerla antes de T27, que es la primera escritura bajo esa clase |
| **H10** | **El guion del bloque 8 de F-009 contradecía a F-012** en tres puntos: su P5 mandaba a Mirasierra, su T22 esperaba `aviso_sin_grafico` —que R48 derogó— y su T24 no pasaba por `/api/adjuntar`, así que su commit habría respondido 409 | `progress/guion_bloque8_F-009.md` | **Corregido el 2026-09-06**, con cambios quirúrgicos marcados con fecha y una nota arriba del guion: el bloque 9 de F-012 ejecuta de hecho un cierre completo sobre la obra 404, y al reanudar F-009 aquel guion se recorre con lo que quede. Es el orden (b) de `design.md` §13 |
