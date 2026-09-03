<!-- progress/guion_bloque8_F-009.md -->
# F-009 · Guion de ejecución del bloque 8 (T22–T27)

> **Qué es esto.** El procedimiento que sigue **el humano**, delante del ERP de
> producción y con el entorno desplegado, para verificar el cierre real de una
> incidencia. Cada tarea trae qué se verifica, sus precondiciones, los pasos
> numerados con la línea exacta que se teclea, qué se espera ver, qué hacer si
> no sale eso, y una casilla de resultado que se rellena aquí mismo.
>
> **Quién lo ejecuta.** Una persona. Ningún agente ha ejecutado —ni puede
> ejecutar— nada de este bloque: ni el dry-run. Escribir en Sigrid desde local
> está prohibido por `CLAUDE.md`, y contra producción solo se hacen lecturas
> salvo autorización expresa para una acción concreta.
>
> **Estado**: `progress/impl_F-009.md` está aprobado en review y T28 (mutación)
> cerrada. Falta este bloque y T29. Las tareas de `specs/F-009-cierre-sigrid/tasks.md`
> **las marca el humano**, no el agente.

---

## 0 · Tres cosas que sorprenden, y conviene saber antes de estar delante del ERP

### 0.1 · Con `CIERRE_HABILITADO` apagado **no funciona ni el dry-run**

No es un descuido: es consecuencia directa de la doble puerta. `construir_erp`
(`infrastructure/sigrid/fabrica.py`) comprueba, **en este orden**, el entorno
→ el interruptor → la configuración → el huso, y **solo entonces** construye el
adaptador. El interruptor se mira **antes de leer nada**, así que con
`CIERRE_HABILITADO=false` la respuesta es `503 CierreDeshabilitado` y el ERP
**no se entera de que existimos**.

Consecuencia práctica: **la ventana de escritura tiene que estar abierta ya
para T22**, que es una lectura. No se puede «ensayar el dry-run con la ventana
cerrada». La secuencia real es abrir la ventana → T22 … T27 → cerrar la
ventana, y mientras esté abierta hay que estar delante.

### 0.2 · T24, paso 7: hay que mirar **la hora** de la fila nueva de `dbo.log`

Era **la única decisión de la feature que no se pudo tomar con un dato**
(`progress/impl_F-009.md` §3.3.a): `design.md` §7.3 dice «`fec`/`hor` con la
fecha y la hora del cierre» y **no dice en qué huso**. Se eligió **hora local**
(`SIGRID_ZONA_HORARIA`, `Europe/Madrid`), porque escribir UTC dejaría nuestras
filas con **una o dos horas menos** que todas las demás del ERP y nadie lo
notaría hasta el día en que hiciera falta reconstruir cuándo se cerró algo.

`infra/10_log_cierre_sigrid.ps1` decodifica `fec`/`hor` y dice explícitamente
si la hora escrita coincide con la **local** o con la **UTC**. Si sale UTC, es
un defecto y hay que pararse: la fila ya está escrita y corregirla es otra
escritura en producción, que decide el humano.

### 0.3 · T26: qué hacer si `SqlWriteGuard` rechaza el `WITH (UPDLOCK, HOLDLOCK)`

Está previsto **un solo** rechazo, y tiene salida escrita:

- **Si rechaza la sugerencia de tabla** `WITH (UPDLOCK, HOLDLOCK)`: se anota, y
  se cae a la variante **sin sugerencias**. Esa variante **sigue fallando en
  seguro**, porque la clave única `log_indide` rechazaría un `ide` colisionado,
  la pasarela revierte **todo el batch** (`sigrid_api.md` §7.3) y el `UPDATE` se
  va con él: el ERP queda sin ningún cambio.
- **Si rechaza cualquier otra cosa**: la feature se marca `blocked`, se anota el
  motivo en `progress/current.md` y **se para**. No se improvisa otra vía.

Lo que dice `azure-apps/sigrid_api.md` §5 sobre `SqlWriteGuard` es que aplica
lista blanca de prefijos (`ALLOWED_WRITE_PREFIXES`), prohíbe
`DROP/ALTER/CREATE/GRANT/EXEC/MERGE`, exige `WHERE` en `UPDATE`/`DELETE` y
valida **cada** sentencia del batch. Nuestro `INSERT ... SELECT` no está en esa
lista de prohibidos, pero **nadie lo ha probado contra el guard**: eso es
exactamente lo que verifica T26, y por eso se hace dentro de T24.

---

## 1 · La configuración de Sigrid: qué la pone ya el despliegue y qué queda a mano

> **Esto era el hallazgo H1**, y bloqueaba el arranque del bloque: el entorno
> desplegado no tenía **ninguna** configuración de Sigrid, así que
> `POST /api/cerrar` habría respondido `503 ConfiguracionSigridIncompleta`
> nombrando `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` y `SIGRID_BASE_DATOS` de
> una vez. **Resuelto el 2026-09-03 en el commit `82fbfb8`**, con H2. Lo que
> sigue es lo que queda, que no es cero: los **valores** de los tres secretos
> no puede ponerlos un script, porque no están —ni pueden estar— en el
> repositorio.

### Qué hace ya el despliegue, sin que nadie teclee nada

`infra/desplegar_backend.ps1` fija **las ocho** App Settings de F-009 en cada
ejecución:

| Cómo | Cuáles |
|---|---|
| Referencia a Key Vault, resuelta por la identidad gestionada | `SIGRID_API_BASE_URL`, `SIGRID_API_KEY`, `SIGRID_BASE_DATOS` |
| En claro en `$ajustes` | `CIERRE_HABILITADO=false`, `SIGRID_TIMEOUT_S`, `SIGRID_REINTENTOS`, `SIGRID_TIP_RECLAMACION`, `SIGRID_ZONA_HORARIA` |

Dos consecuencias que importan para este guion:

1. **`CIERRE_HABILITADO` vuelve a `false` en cada despliegue** (era H2). Antes
   no: se apoyaba en el valor por defecto del código, que solo se aplica
   mientras la App Setting no exista, así que encendida una vez para T22 se
   habría quedado encendida para siempre. Ahora un redespliegue en mitad del
   bloque **cierra la ventana**: si pasa, se vuelve a abrir con la línea del
   paso 3 de T22, no se da por hecho que sigue abierta.
2. **`SIGRID_ZONA_HORARIA=Europe/Madrid` queda escrita**, y es la que decide
   el huso de `fec`/`hor` de la fila de `dbo.log` que se mira en el paso 7 de
   T24 (§0.2). Ya no depende del valor por defecto del código.

### Paso 0 · Los tres secretos del vault (una sola vez, antes de T22)

**Es lo único que queda a mano, y es a mano a propósito**: los tres valores los
da el dueño de `sigrid-api` (`azure-apps/sigrid_api.md` §3.1 y §3.3), no se
deducen y no pueden entrar al repositorio. Se piden a ciegas por consola
(`Read-Host -AsSecureString`), no se escriben en ningún fichero y no quedan en
el historial de la consola:

```
powershell -ExecutionPolicy Bypass -Command ".\infra\cargar_secretos_postventa.ps1 -Solo sigrid-api-base-url,sigrid-api-key,sigrid-base-datos"
```

> **`-Solo` no funciona con `powershell -File`**: el parámetro no llega y el
> script pediría los doce secretos del backend. Se lanza con `-Command`, como
> explica `docs/DESPLIEGUE.md` §2. `sigrid-base-datos` es la base **de
> negocio**, la única con escritura permitida en la pasarela (`sigrid_api.md`
> §4.1).

Y después, **un despliegue del backend**, que es lo que fija las App Settings:

```
powershell -ExecutionPolicy Bypass -File .\infra\desplegar_backend.ps1 -SinPublicar
```

**Qué se espera ver**: el script imprime `App Settings : N, de las que 12 son
referencias` y `Ventana de escritura : CERRADA (archivo Y cierre en el ERP)`.

**Comprobación**: en el portal, ninguna App Setting sale con error. Una
referencia que no se resuelve es un secreto que no está en el vault, o el rol
`Key Vault Secrets User` sin propagar.

### Si el entorno ya está desplegado y no se quiere redesplegar

Es el caso real de hoy: la Function App lleva el código de F-009 pero se
desplegó **antes** de este arreglo, así que no tiene ninguna de las ocho. Con
los secretos ya subidos (arriba), las App Settings se pueden poner sueltas.
Hace falta el URI del vault:

```
az keyvault show -g rg-postventa-dev -n <el kv del proyecto> --query properties.vaultUri -o tsv
```

Las tres sensibles, **por referencia** (las comillas no son decoración: sin
ellas `cmd.exe` interpreta los paréntesis, ver `infra/desplegar_backend.ps1`):

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings "SIGRID_API_BASE_URL=@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/sigrid-api-base-url)" "SIGRID_API_KEY=@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/sigrid-api-key)" "SIGRID_BASE_DATOS=@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/sigrid-base-datos)"
```

Y las cinco planas, incluido el interruptor **explícitamente apagado**:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false SIGRID_TIMEOUT_S=35 SIGRID_REINTENTOS=3 SIGRID_TIP_RECLAMACION=708 SIGRID_ZONA_HORARIA=Europe/Madrid
```

**Qué se espera ver**: `az` devuelve el JSON de las App Settings sin error, y
la Function App se reinicia sola.

**Si no sale eso**: si el `secret set` del paso anterior falló por permisos, es
que la sesión de `az` no tiene rol sobre el vault; si el `appsettings set`
responde «X no se esperaba en este momento», faltan las comillas de la
referencia.

**Comprobación**: la referencia se ha resuelto cuando la Function arranca; se
verá en T22, porque si no se resuelve el endpoint responde `503` nombrando la
variable que falte.

---

## 2 · Precondiciones comunes (se comprueban **antes** de abrir la ventana)

- [ ] **P1** · `bash harness/init.sh` en verde en la rama `feature/F-009-cierre-sigrid`.
- [ ] **P2** · El backend desplegado lleva el código de F-009
      (`infra\desplegar_backend.ps1`). Sin esto, `/api/cerrar` no existe y la
      respuesta es un 404, no un 503.
- [ ] **P3** · Paso 0 de §1 hecho: los **tres secretos** de Sigrid en el Key
      Vault y el backend desplegado **después** del commit `82fbfb8` (o, si no
      se redespliega, las ocho App Settings puestas a mano según §1). Se
      comprueba en el portal: ninguna referencia a Key Vault con error.
- [ ] **P4** · La clave de función de `sigrid-api` y la raíz de la pasarela, a
      mano para los scripts de lectura (§3). No se escriben en ningún fichero.
- [ ] **P5** · **Una incidencia del piloto de Mirasierra elegida**, y su parte
      ya recorrido en el front: subido, validado `apto` / `archivo_y_cierre`,
      **guardado** (`POST /api/parte`, F-019) y **archivado** (`POST /api/archivar`).
      No es una formalidad: `postventa.cierres` tiene **clave ajena contra
      `postventa.partes`**, así que un `hash` que no esté guardado hace fallar
      **hasta el dry-run** al escribir su traza (R40). Es la misma trampa del
      defecto 15 de F-010.
- [ ] **P6** · **Autorización expresa del humano para cerrar esa incidencia
      concreta**, no «para probar el cierre». Es lo que exige `CLAUDE.md`.
- [ ] **P7** · Sesión iniciada en el front (grupo `posventa-usuarios`), porque
      **el backend no responde por su nombre de host**: es backend enlazado de
      la Static Web App y la plataforma solo acepta lo que entra por el proxy
      (`docs/DESPLIEGUE.md` §5 bis). Ver §4.
- [ ] **P8** · Una sola sesión del front con **un solo parte** en curso: el
      botón de cierre del front cierra **todos** los cerrables de la sesión, y
      el primer cierre real tiene que ser **uno**.

---

## 3 · El utillaje: cinco scripts en `infra/`, una línea corta cada uno

Todos son **PowerShell 5.1**, re-ejecutables, comprueban sus precondiciones y
paran con un mensaje claro en vez de reventar, y **terminan imprimiendo un
veredicto** en forma de tabla `QUE / ESPERADO / OBTENIDO` con `PASA` o
`NO PASA` (código de salida `0` o `6`).

| Script | Qué hace | Escribe |
|---|---|---|
| `infra/08_lectura_sigrid_comun.ps1` | Solo **declara**: la llamada a `POST /api/sql/read`, el manejo de la clave y el formato del veredicto. Lo cargan los otros cuatro | nada |
| `infra/09_estado_reclamacion_sigrid.ps1` | La reclamación en el ERP: `ide`, `emp`, `est`, estado legible, destino resuelto contra `conest`, `tiemod`, y `MAX(ide)` de `dbo.log` | **nada · solo lee** |
| `infra/10_log_cierre_sigrid.ps1` | La fila nueva de `dbo.log`, **campo a campo** contra `design.md` §7.3, y **el huso** de `fec`/`hor` | **nada · solo lee** |
| `infra/11_trazabilidad_tex_sigrid.ps1` | Las dos lecturas del `tex` propio (R25) | **nada · solo lee** |
| `infra/12_traza_cierre_local.ps1` | La traza de `postventa.cierres` y la correspondencia de `postventa.usuarios_sigrid` | **nada · solo lee**, y solo del esquema propio |

**Los cinco son de lectura.** Leer producción está permitido; escribir en
Sigrid desde un puesto de trabajo, no. La **única** escritura de todo el bloque
es el `POST /api/cerrar` con `commit: true` de T24, y **la hace el servicio
desplegado**, no esta máquina.

### Cómo se les pasa el destino y la clave

Para no teclear la raíz y la clave en cada llamada —y para que no queden en el
historial de la consola—, se dejan en la sesión **una vez**, y se borran al
terminar (§6):

```
$env:SIGRID_API_BASE_URL = "<la raíz de la pasarela>"
```

```
$env:SIGRID_BASE_DATOS = "<la base de negocio del ERP>"
```

La clave **no se pone en una variable de entorno tecleada**: cada script la
pide por consola como `SecureString` si `$env:SIGRID_API_KEY` no está. Si se
prefiere no repetirla en cada llamada, se deja en la sesión con
`Read-Host -AsSecureString` y no como texto en la línea:

```
$env:SIGRID_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR((Read-Host "Clave de sigrid-api" -AsSecureString)))
```

> De dónde sale cada valor: la raíz y la clave, del dueño de `sigrid-api`
> (`azure-apps/sigrid_api.md` §3.1 y §3.3). La base, la de negocio: es la única
> con escritura permitida en la pasarela (`sigrid_api.md` §4.1). El host de
> PostgreSQL y la contraseña de `postventa_app`, del Key Vault del proyecto.
> **Ninguno se escribe en este fichero ni en ningún otro del repositorio.**

---

## 4 · Cómo se llama a `POST /api/cerrar` (y por qué no con `curl`)

**El host desnudo de la Function no responde.** Desde que es backend enlazado
de la Static Web App, la plataforma le activa Easy Auth y cualquier ruta
—`/api/health` incluida— devuelve
`{"code":400,"message":"Login not supported for provider azureStaticWebApps"}`
antes de que la Function se entere (`docs/DESPLIEGUE.md` §5 bis). No hay
`-BaseUrl` que lo arregle.

Hay, por tanto, **dos vías legítimas**, las dos desde el front con sesión
iniciada:

**(a) La interfaz del front.** Es la vía normal y la que usa negocio: el botón
de cierre pide primero el **dry-run de toda la tanda** (`pedirDryRunCierre`,
sin `commit`), lo pinta, y solo después de la confirmación explícita
—que **caduca**, R15— llama con `commit: true` y `confirmado: true`.

**(b) La consola del navegador**, `F12` → **Consola**, en la pestaña del front.
Va al **mismo origen**, así que pasa por el proxy que autentica. Se usa cuando
hace falta **el JSON crudo de la respuesta** (los cinco campos de R9 y el aviso
de R21, tal y como viajan) o acotar la llamada a **una sola** incidencia.

El fragmento base, que se reutiliza en T22, T23 y T27 cambiando dos constantes
y —solo en T24— añadiendo `commit`:

```js
// F-009 bloque 8 - llamada a /api/cerrar desde la consola del FRONT.
// SIN `commit` esto es un DRY-RUN: lee el ERP y NO escribe nada.
(async () => {
  const HASH = "<el hash del parte, tal y como lo enseña el front>";
  const INCIDENCIA = "<RSaa.mm/nnnn>";
  const COMMIT = false;   // <-- lo unico que se toca en T24

  // La identidad sale de la sesion de la Static Web App, igual que en
  // `js/api.js`: asi no hay que pegar el `oid` a mano en la consola.
  const me = await (await fetch("/.auth/me")).json();
  const p = me.clientPrincipal || {};
  const claim = (sufijos) =>
    ((p.claims || []).find((c) =>
      sufijos.some((s) => c.typ === s || String(c.typ).endsWith("/" + s))
    ) || {}).val || "";

  const cuerpo = {
    hash: HASH,
    numero_incidencia: INCIDENCIA,
    veredicto: "apto",
    destino: "archivo_y_cierre",
    estado_archivo: "archivado",
    usuario_oid: claim(["objectidentifier", "oid"]) || p.userId || "",
    correo: claim(["preferred_username", "emailaddress", "email", "upn"]) || p.userDetails || "",
  };
  if (COMMIT) { cuerpo.commit = true; cuerpo.confirmado = true; }

  const r = await fetch("/api/cerrar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  console.log("HTTP " + r.status);
  console.log(JSON.stringify(await r.json(), null, 2));
})();
```

> El cuerpo **no lleva ni el PDF ni ningún campo manuscrito** (R51), y la
> respuesta tampoco: ni DNI, ni observaciones del cliente, ni el `oid` de quien
> confirma (R43). Por eso se puede pegar la respuesta en la casilla de
> resultado. Lo que **no** se pega nunca es el `/.auth/me`.

---

## 5 · Las tareas, en el orden en que se ejecutan

### T22 · Dry-run real, con el interruptor apagado y luego encendido

**Qué se verifica y por qué.** Que el dry-run lee el ERP de verdad y devuelve
**las cinco cosas** que R9 exige más el aviso de R21, y que **no cambia nada**
en Sigrid (R8, R10). Es el único paso que se puede repetir sin coste, y el que
sostiene todo lo demás: sin un dry-run correcto no se escribe (R10).

De paso se comprueba §0.1 en el propio ERP: **con el interruptor apagado no
funciona ni el dry-run** (R37, R49).

**Precondiciones.** P1–P7 de §2.

**Pasos.**

1. **Foto de partida del ERP.** Con la ventana todavía cerrada:

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>"
   ```

   *Se espera*: `ESTADO DE LA RECLAMACION : PASA`, con la tabla de datos —`ide`,
   `emp`, `est` actual, estado legible (`PTE / PENDIENTE` o similar), `est` de
   destino, `CER / CERRADO`, `tiemod` y `MAX(ide)` de `dbo.log`—. **Cópialos
   todos a la casilla**: son la referencia de T24 y de T27.
   *Si no sale eso*: «no hay ninguna reclamación con ese código» → el código
   está mal o le falta la **barra** (en el ERP es `RS26.08/0123`, el guion es
   del nombre del fichero); «dbo.conest no resuelve CER» → es R2 y se para, el
   número **no se escribe a mano**.

2. **El dry-run con el interruptor apagado.** En la consola del front, el
   fragmento de §4 con `COMMIT = false`.

   *Se espera*: **`HTTP 503`** y un motivo que diga que el cierre está
   deshabilitado. **Esto es lo correcto y hay que verlo**: confirma la doble
   puerta de §0.1 y que apagado no se toca el ERP ni para leer.
   *Si sale 503 nombrando `SIGRID_API_BASE_URL` / `SIGRID_API_KEY` /
   `SIGRID_BASE_DATOS`*: falta el Paso 0 de §1. Vuelve ahí.
   *Si sale 200*: **para**. El interruptor no está apagado, y eso hay que
   entenderlo antes de seguir.

3. **Abrir la ventana de escritura.** A partir de aquí no se deja la máquina
   sola:

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=true
   ```

   *Se espera*: el JSON de las App Settings, y la Function reiniciándose (unos
   segundos hasta que responda).

4. **El dry-run de verdad.** El mismo fragmento de §4, otra vez, con
   `COMMIT = false`.

   *Se espera*: **`HTTP 200`** y un cuerpo con `estado: "dry_run_ok"`,
   `filas_afectadas: 0` y un objeto `dry_run` con **las seis cosas**:
   `incidencia`, `descripcion`, `estado_origen` {`codigo`, `descripcion`},
   `estado_destino` {`codigo: "CER"`, `descripcion`}, `login_sigrid`, y
   `aviso_sin_grafico` **no vacío** (R21: la reclamación quedará cerrada **sin
   el parte dentro de Sigrid**).
   *Si sale `409`*: el motivo lo dice — parte no apto (R16), no archivado
   (R17), estado no cerrable (R19), o login sin correspondencia (R31, y eso es
   T23). *Si sale `502`*: la pasarela ha fallado; **no se reintenta como
   cierre** (R27), se mira el motivo. *Si sale `500` diciendo «cierre sin
   traza»*: el parte no está guardado en `postventa.partes` → precondición P5.

5. **Nada ha cambiado en el ERP.** Se repite la foto, ahora exigiendo que sea
   idéntica (rellena con lo anotado en el paso 1):

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "<el estado del paso 1>" -TiemodEsperado "<el tiemod del paso 1>" -MaxIdeLogEsperado <el MAX(ide) del paso 1>
   ```

   *Se espera*: `ESTADO DE LA RECLAMACION : PASA`, con las tres comprobaciones
   en verde.
   *Si alguna sale en rojo*: **para**. Un dry-run que mueve algo es un defecto
   grave y no se sigue con T24.

6. **La traza local del dry-run** (R40):

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado dry_run_ok
   ```

   *Se espera*: `TRAZA LOCAL DEL CIERRE : PASA`, con `estado = dry_run_ok` y
   marca de tiempo del dry-run.
   *Si sale «trazas 0»*: el parte no está en `postventa.partes` (P5).

**Casilla de resultado · T22**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Foto de partida (`ide` / `emp` / `est` / estado legible / `tiemod` / `MAX(ide)`) | |
| Paso 2 · HTTP con el interruptor apagado | |
| Paso 4 · HTTP y `estado` del dry-run | |
| Paso 4 · las seis cosas de R9/R21, ¿estaban todas? | |
| `login_sigrid` que devolvió el dry-run | |
| Paso 5 · ¿el ERP intacto? | |
| Paso 6 · traza local | |
| **T22 queda marcada** | sí / no · motivo: |

---

### T23 · La siembra del login, contra el ERP (R30, R31, R32, R33, R34)

**Qué se verifica y por qué.** Que el login con el que se firmará el log del
ERP **lo confirma el ERP**, no nuestro supuesto. La derivación desde el correo
es **la siembra**, no el mecanismo de cada cierre, y el supuesto «el correo de
la app y el de Sigrid son el mismo» **la base no lo confirma**: `usu.ele` está
vacío en los 228 usuarios, y de los 8 con correo registrado **solo 6 cumplen la
convención**. Por eso R31 aborta sin escribir y R34 da la salida manual.

**Precondiciones.** T22 marcada. Ventana abierta.

**Pasos.**

1. **Estado de partida de la correspondencia.** Si el usuario que va a cerrar
   ya tuviera fila confirmada, R29 dice que se usa **sin derivar nada**, y este
   apartado no prueba la siembra. Para probarla, la tabla tiene que estar
   **vacía para ese usuario**:

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -UsuarioOid "<el oid del usuario>"
   ```

   *Se espera*: `correspondencia` = `ausente` **antes** del primer dry-run de
   T22, o `presente` + `verificada = si` **después** (la siembra ocurre en el
   dry-run, no en el `commit`).
   *Si ya estaba presente antes de T22*: anótalo y di que la siembra **no se ha
   podido observar en esta ejecución**; el punto 3 sigue siendo verificable.

2. **El candidato existe exactamente una vez en `dbo.usu`.** El login que
   devolvió el dry-run de T22 (`login_sigrid`), comprobado contra el maestro con
   el script que ya existe para el alta manual, en su modo de solo verificación:

   ```
   powershell -ExecutionPolicy Bypass -File infra\07_alta_usuario_sigrid.ps1 -UsuarioOid "<el oid>" -LoginSigrid "<el login del dry-run>" -VerificarAhora -SigridBaseUrl "<la raíz>" -SigridBaseDatos "<la base>"
   ```

   *Se espera*: «El ERP confirma el login» y «Correspondencia creada» o
   «actualizada». El script **no escribe en Sigrid**: su única llamada al ERP es
   un `COUNT(*)` de solo lectura.
   *Si dice «el login aparece 0 veces»* → es el caso de R31 y se comprueba en el
   punto 4. *Si dice «aparece 2 veces»* → ambigüedad: tampoco se cierra, y
   **no** se elige una por nuestra cuenta.

3. **La correspondencia quedó guardada como confirmada** (R33), y un segundo
   dry-run **ya no deriva nada** (R29):

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -UsuarioOid "<el oid>" -EstadoEsperado dry_run_ok
   ```

   *Se espera*: `correspondencia = presente` y `correspondencia CONFIRMADA
   (R33) = si`. Después, repetir el dry-run de §4 y comprobar que devuelve el
   **mismo** `login_sigrid`.
   *Si `verificada = no`*: la fila entró por alta manual y **todavía no se ha
   confirmado**; R32 dice que no se firma con ella hasta que el ERP la confirme.

4. **El caso que no sigue la convención** (R31). Con un usuario cuyo candidato
   **no exista** en `dbo.usu` —o, sin él a mano, con un login inventado—:

   ```
   powershell -ExecutionPolicy Bypass -File infra\07_alta_usuario_sigrid.ps1 -UsuarioOid "<un oid de prueba>" -LoginSigrid "<un login que no existe>" -VerificarAhora -SigridBaseUrl "<la raíz>" -SigridBaseDatos "<la base>"
   ```

   *Se espera*: «El ERP no confirma ese login … **No se ha escrito nada**», con
   código de salida `5`. Es la misma comprobación que hace el servicio antes de
   responder `409` nombrando el correo y el login intentado, **sin tocar
   Sigrid**.
   *Si escribiera la fila igualmente*: es un defecto de R32 y se para.

   > La salida de este caso es el alta manual del propio script **sin**
   > `-VerificarAhora` (R34), que tiene precedencia sobre la derivación y deja
   > la fila sin marcar hasta que el ERP la confirme.

**Casilla de resultado · T23**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1 · ¿la tabla estaba vacía para ese usuario? | |
| 2 · ¿el candidato existe **exactamente una vez**? | |
| 3 · ¿quedó `verificada`? ¿el segundo dry-run devolvió el mismo login? | |
| 4 · ¿el login inexistente fue rechazado **sin escribir**? | |
| **T23 queda marcada** | sí / no · motivo: |

---

### T24 · El primer cierre real

**Qué se verifica y por qué.** Todo lo que un mock no puede probar: que el
batch es **de verdad** transaccional y afecta a **2 filas** (R22, R23), que
`con.est` acaba en el `est` que `conest` da para `CER` (R1), que la fila de
`dbo.log` sale **campo a campo** como se diseñó (R24, R25), que `con.tiemod`
**no se mueve** (F-008 §2.3), y que la traza local queda en `cerrado` con su
`oid` y **sin el login** (R41, R43).

> **AVISO.** Este es el único paso que escribe en el ERP de producción, y **lo
> hace el servicio desplegado**, no esta máquina. Exige autorización expresa
> del humano para **esta incidencia concreta** (P6). Deshacer un cierre no es
> borrar un fichero: es otro proceso que alguien ejecuta a mano en Sigrid.

**Precondiciones.** T22 y T23 marcadas. Ventana abierta. P6 y P8.

**Pasos** —en este orden y sin saltarse ninguno—.

1. **Anotar el estado de partida.**

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>"
   ```

   *Se espera*: la tabla de datos. **Anota `ide`, `emp`, `est`, el `res` y el
   `tiemod`.**

2. **Anotar `MAX(ide)` de `dbo.log`.** Sale en la misma tabla del paso 1
   («MAX(ide) de dbo.log»). Anótalo aparte y **con cuidado**: es lo que
   distingue nuestra fila de las 8,4 millones que ya hay.

3. **Ejecutar el dry-run y LEERLO.** El fragmento de §4 con `COMMIT = false`,
   o el botón de dry-run del front.

   *Se espera*: `200`, `estado: "dry_run_ok"`, y el `dry_run` con el estado de
   origen legible, el destino `CER`, el `login_sigrid` y `aviso_sin_grafico`.
   **Leerlo no es una formalidad**: lo que se confirma en el paso 4 es esto.
   *Si el estado de origen no es el del paso 1*: alguien ha movido la
   reclamación. Vuelve al paso 1.

4. **Confirmar en el front y ejecutar con `commit: true`.** Vía (a) de §4: el
   botón de confirmación del front, que **caduca** (R15) — si tarda, el segundo
   clic no dispara y hay que volver a armarla. Si se usa la consola, el mismo
   fragmento con `COMMIT = true` (que pone `commit` y `confirmado`).

   *Se espera*: `HTTP 200` con `estado: "cerrado"` y **`filas_afectadas: 2`**.
   *Si sale `409` diciendo que el estado cambió desde el dry-run*: el control
   optimista de R11 ha saltado y **no se ha aplicado nada**. Vuelve al paso 1.
   *Si sale `502`*: la escritura pudo salir y no volvió la respuesta. **NO se
   reintenta** (R27): se sigue con el paso 6 para ver qué hay en el ERP, y lo
   que se haga después lo decide el humano.
   *Si sale `500` «cierre sin traza»*: **la incidencia SÍ está cerrada** en el
   ERP y lo que falló fue la traza local. No se repite el cierre.

5. **La respuesta declara 2 filas afectadas** (R22). Es el paso 4 leído con
   cuidado: `filas_afectadas` tiene que valer exactamente `2` —una de `con` y
   una de `log`—.
   *Si vale `0`*: R11, no se aplicó nada. *Si vale otra cosa*: es un cierre a
   medias, el servicio lo trata como error y **no lo da por bueno**.

6. **`con.est` es el de `CER`, y `tiemod` no se ha movido** (pasos 6 y 8 del
   contrato de la tarea, en una sola lectura):

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER" -TiemodEsperado "<el tiemod del paso 1>"
   ```

   *Se espera*: `PASA`, con «codigo del estado actual = CER» y «con.tiemod NO se
   ha movido» en verde. **Anota el nuevo `MAX(ide)` de `dbo.log`**: tiene que
   ser el del paso 2 **más uno**.
   *Si `tiemod` se ha movido*: contradice lo que F-008 midió del ERP. Anótalo y
   **no lo des por normal**.

7. **La fila nueva de `dbo.log`, campo a campo, y EL HUSO** (§0.2):

   ```
   powershell -ExecutionPolicy Bypass -File infra\10_log_cierre_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -DesdeIde <el MAX(ide) del paso 2> -LoginEsperado "<el login_sigrid del dry-run>" -EmpEsperada <el emp del paso 1> -ResEsperado "<el res del paso 1>"
   ```

   *Se espera*: `FILA DE AUDITORIA DEL CIERRE : PASA`, con **una** fila nueva y
   todo en verde: `tab = con`, `tip`, `cod`, `res`, `ope = 5`, `est = 1`,
   `ori = 0`, `emp` **tomado de la reclamación**, `usu` = el login de la persona,
   `tex = Cerrar parte (postventa-incidencias)` y **`huso de fec/hor = HORA
   LOCAL (correcto)`**.
   *Si el huso sale `UTC (INCORRECTO)`*: es el defecto que §0.2 anticipa. La
   fila ya está escrita; **no la toques**, anótalo y páralo aquí: corregirla es
   otra escritura en producción.
   *Si sale `NO COINCIDE CON NINGUNA`*: mira si han pasado más de 20 minutos
   desde el cierre (el script tolera 20 por defecto, `-ToleranciaMinutos`).
   *Si no hay ninguna fila nueva pero el paso 5 dijo 2 filas*: es una
   contradicción. **Para y no repitas el cierre.**

8. *(Es el paso 6 de este guion: `tiemod` se comprueba en la misma lectura.)*

9. **La traza local** (R41, R43):

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado cerrado -UsuarioOid "<el oid>" -LoginQueNoDebeAparecer "<el login del ERP>"
   ```

   *Se espera*: `PASA`, con `estado = cerrado`, los dos códigos de estado
   guardados, marca de tiempo del cierre, `oid de quien confirmo = si` y
   **`el login del ERP NO esta en la traza (R43) = no`**.
   *Si el login aparece en la traza*: es un defecto de R43 y se anota.

**Casilla de resultado · T24**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Incidencia cerrada (código) | |
| Autorización expresa del humano | sí / no |
| 1–2 · `ide` / `emp` / `est` / `res` / `tiemod` / `MAX(ide)` de partida | |
| 3 · dry-run leído (estado origen → destino, login) | |
| 4–5 · HTTP, `estado` y `filas_afectadas` | |
| 6 · `con.est` = `CER` · `tiemod` sin mover · nuevo `MAX(ide)` | |
| 7 · veredicto campo a campo | |
| 7 · **huso de `fec`/`hor`** | LOCAL / UTC / no coincide |
| 9 · traza local (`cerrado`, `oid` sí, login no) | |
| **T24 queda marcada** | sí / no · motivo: |

---

### T25 · Que el `tex` propio hace lo que se diseñó (R25)

**Qué se verifica y por qué.** Que el texto propio cumple **las dos**
condiciones por las que se eligió (D1 de `design.md`): que **seguimos saliendo
en los informes de Posventa**, que se miden con el filtro por prefijo
`tex LIKE 'Cerrar parte%'` sobre 6.843 filas; y que el filtro por igualdad
exacta devuelve **exactamente los cierres de este servicio y ninguno manual**,
que es lo que permitiría revertir solo lo nuestro si el piloto se tuerce.

**Precondiciones.** T24 marcada, con al menos un cierre real hecho.

**Pasos.**

1. Las dos lecturas, en una:

   ```
   powershell -ExecutionPolicy Bypass -File infra\11_trazabilidad_tex_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -CierresEsperados 1
   ```

   *Se espera*: `TRAZABILIDAD DEL TEXTO PROPIO : PASA`, con «el prefijo del ERP
   encuentra nuestro cierre = True» y «cierres de este servicio en todo el ERP
   = 1». Debajo, el script lista **una a una** las filas que el filtro exacto
   devuelve: míralas.
   *Si el prefijo no encuentra nuestro cierre*: nos hemos salido de los informes
   de Posventa, que es justo lo que D1 quería evitar.
   *Si el recuento exacto sale **mayor** que los cierres hechos*: hay filas con
   nuestro texto que no hemos escrito nosotros — el texto ha dejado de
   identificarnos, y hay que mirar las de la lista una a una.
   *Si sale **menor***: alguno de nuestros cierres no dejó su fila de log, y eso
   contradice el paso 5 de T24.

2. `-CierresEsperados` sube con cada cierre real: si el piloto cierra tres
   incidencias, la siguiente ejecución lleva `3`.

**Casilla de resultado · T25**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| ¿el filtro por prefijo encuentra nuestro cierre? | |
| nº de filas con el texto propio en todo el ERP | |
| ¿alguna de esas filas no es nuestra? | |
| **T25 queda marcada** | sí / no · motivo: |

---

### T26 · Que `SqlWriteGuard` acepta el batch tal cual

**Qué se verifica y por qué.** Que la pasarela deja pasar las dos sentencias
del batch **como están**, con la sugerencia de tabla `WITH (UPDLOCK, HOLDLOCK)`
incluida. Esa sugerencia protege la reserva del `ide`, que `sql/write` **no**
protege por su cuenta (`sigrid_api.md` §7.5), en una tabla de 8,4 millones de
filas cuya clave primaria se asigna por `MAX(ide)+1` (R26).

**Se hace DENTRO de T24**, no después: lo que se observa es la respuesta del
paso 4.

**Precondiciones.** Estar ejecutando el paso 4 de T24.

**Pasos.**

1. **Mirar la respuesta del paso 4 de T24.**

   *Se espera*: `200` con `filas_afectadas: 2`. Eso significa que el guard
   aceptó las dos sentencias y la transacción se aplicó: **T26 pasa y no hay
   nada más que hacer**.

2. **Si la respuesta es un `502` cuyo motivo apunta al guard** —una sentencia
   rechazada, un prefijo no permitido, la sugerencia de tabla—:

   - **Si lo que rechaza es `WITH (UPDLOCK, HOLDLOCK)`**: **anótalo aquí** y cae
     a la variante **sin sugerencias**. Sigue fallando en seguro: la clave única
     `log_indide` rechazaría un `ide` colisionado, la pasarela revierte **todo el
     batch** y el `UPDATE` se va con él, así que el ERP queda **sin ningún
     cambio**. El reintento lo decide una persona, no el código (R27).
   - **Si rechaza cualquier otra cosa**: **PARA**. Se marca F-009 `blocked` en
     `harness/features.json`, se anota el motivo en `progress/current.md` y se
     cierra la ventana de escritura. **No se improvisa otra vía**, y en
     particular no se parte el batch en dos llamadas: eso dejaría la puerta
     abierta a una reclamación cerrada sin rastro en el log.

3. **Comprobar que el ERP quedó intacto** si hubo rechazo:

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "<el estado del paso 1 de T24>" -MaxIdeLogEsperado <el MAX(ide) del paso 2 de T24>
   ```

   *Se espera*: `PASA`. Un batch revertido no deja nada.
   *Si el estado cambió pero no hay fila de log, o al revés*: la
   transaccionalidad de la pasarela no es la que dice `sigrid_api.md` §7.3.
   Anótalo: es un hallazgo del dueño de `sigrid-api`, no algo que se arregle
   aquí.

**Casilla de resultado · T26**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| ¿el guard aceptó el batch tal cual? | sí / no |
| Si no: ¿qué rechazó, literalmente? | |
| ¿se cayó a la variante sin sugerencias, o se marcó `blocked`? | |
| ¿el ERP quedó intacto tras el rechazo? | |
| **T26 queda marcada** | sí / no · motivo: |

---

### T27 · Reintento sobre lo ya cerrado (R18, R42)

**Qué se verifica y por qué.** Que volver a pedir el cierre de una incidencia
que ya está cerrada sale como **`ya_cerrada`**, que **no es un error** (R18),
**sin escribir nada** en Sigrid, y **sin pisar** la traza local, porque
`cerrado` es terminal (R42). Es el escenario real: alguien vuelve a pasar el
mismo parte, o el auto-cierre repite.

**Precondiciones.** T24 marcada. La ventana **sigue abierta**.

**Pasos.**

1. **Anotar el `MAX(ide)` actual de `dbo.log`** (el de después del cierre):

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER"
   ```

   *Se espera*: `PASA`, estado `CER`. Anota el `MAX(ide)`.

2. **Repetir la llamada, con `commit`.** El fragmento de §4 con
   `COMMIT = true`, sobre **la misma** incidencia.

   *Se espera*: `HTTP 200` con **`estado: "ya_cerrada"`** y
   `filas_afectadas: 0`. El dry-run detecta que la reclamación ya está en el
   estado de cierre y **no compone ninguna escritura**.
   *Si sale `409`*: mira el motivo — puede ser que el estado `CER` no esté entre
   los cerrables, que es otra cosa y también aborta sin escribir.
   *Si sale `200` con `estado: "cerrado"` y `filas_afectadas: 2`*: **defecto
   grave**. Se ha escrito una segunda vez en el ERP. Para y anótalo.

3. **El `MAX(ide)` de `dbo.log` NO ha subido**:

   ```
   powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER" -MaxIdeLogEsperado <el MAX(ide) del paso 1>
   ```

   *Se espera*: `PASA`, con el `MAX(ide)` idéntico.
   *Si ha subido*: se ha escrito una fila de log de más. Mírala con
   `infra\10_log_cierre_sigrid.ps1 -DesdeIde <el del paso 1>`.

4. **La traza local no se ha pisado** (R42):

   ```
   powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado cerrado -UsuarioOid "<el oid>"
   ```

   *Se espera*: `PASA`, con `estado` **todavía** `cerrado` y la marca de tiempo
   del cierre **la de T24**, no una nueva.
   *Si el estado ha pasado a `ya_cerrada`*: se ha pisado una traza terminal, que
   es justo lo que R42 prohíbe.

**Casilla de resultado · T27**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| 1 · `MAX(ide)` antes del reintento | |
| 2 · HTTP, `estado` y `filas_afectadas` | |
| 3 · `MAX(ide)` después — ¿ha subido? | |
| 4 · traza local — ¿sigue en `cerrado` con la fecha de T24? | |
| **T27 queda marcada** | sí / no · motivo: |

---

## 6 · Al terminar, salga bien o mal

1. **Cerrar la ventana de escritura. Siempre, y lo primero.**

   ```
   az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false
   ```

   *Se espera*: el JSON de las App Settings. **Comprobarlo igualmente**, no
   darlo por hecho. Desde el commit `82fbfb8`, `desplegar_backend.ps1` **sí**
   la devuelve a `false` en cada despliegue (era el hallazgo H2 de §8), pero
   eso es la red de seguridad del **siguiente** despliegue: la ventana se
   cierra aquí y ahora, a mano, y no se deja abierta esperando a que alguien
   redespliegue.

2. **Limpiar la sesión de la consola**, para que la clave no siga en memoria:

   ```
   Remove-Item Env:\SIGRID_API_KEY, Env:\SIGRID_API_BASE_URL, Env:\SIGRID_BASE_DATOS -ErrorAction SilentlyContinue
   ```

3. **Rellenar las casillas de resultado de este fichero** y commitearlo.

4. **Marcar en `specs/F-009-cierre-sigrid/tasks.md`** las tareas que hayan
   pasado. Lo hace el humano.

5. **Actualizar `azure-apps/postventa_incidencias.md`**: hoy dice que «todavía
   no se ha ejecutado ni un cierre real». Si T24 pasa, deja de ser verdad, y la
   regla de propiedad de `CLAUDE.md` obliga a actualizarlo **en este mismo
   trabajo**. Commit local allí, sin push.

## 7 · Qué se anota y qué NO

**Sí**: códigos HTTP, `estado`, `filas_afectadas`, códigos de estado del ERP
(`PTE`, `CER`), `ide` de la reclamación y de la fila de log, `MAX(ide)`,
`tiemod`, el veredicto de cada script, y el login del ERP (no es secreto: queda
escrito en `dbo.log.usu` a la vista de cualquiera en Sigrid).

**No, nunca**: la raíz de la pasarela ni ningún FQDN, la clave de función, la
contraseña de PostgreSQL, el contenido de `/.auth/me`, el `oid` de Entra
—dato personal seudónimo—, el correo del usuario, y **nada del parte**: ni el
DNI del cliente, ni sus observaciones manuscritas, ni el nombre del
propietario. Los códigos de incidencia de los **ejemplos** de este guion son
marcadores (`RSaa.mm/nnnn`) a propósito; el real solo va en la casilla de
resultado, que es un código de expediente y no un dato personal.

## 8 · Hallazgos de la preparación de este guion

| # | Hallazgo | Dónde | Qué se propone |
|---|---|---|---|
| **H1** | **RESUELTO** (`82fbfb8`, 2026-09-03). El entorno desplegado no tenía ninguna configuración de Sigrid: ni secretos en el Key Vault, ni las App Settings `SIGRID_*`. T22 habría respondido `503 ConfiguracionSigridIncompleta` | `infra/00_vars_postventa.ps1` (`$PostventaSecretosBackend`, `$PostventaAppSettingsSecretas`), `infra/desplegar_backend.ps1` (`$ajustes`) | Hecho: **tres** secretos nuevos (`sigrid-api-base-url`, `sigrid-api-key`, `sigrid-base-datos`) con sus referencias, y **cinco** planas a `$ajustes`. El cotejo destapó dos más de las tres previstas: `SIGRID_ZONA_HORARIA` —la que decide el huso de `dbo.log`— y `SIGRID_TIP_RECLAMACION`. Queda a mano solo subir los tres valores al vault: ver §1 |
| **H2** | **RESUELTO** (`82fbfb8`, 2026-09-03). `CIERRE_HABILITADO` no se reescribía en cada despliegue, al contrario de `ARCHIVO_HABILITADO=false`, y `docs/DESPLIEGUE.md` §4 bis afirmaba que sí, «por el mismo mecanismo». Se apoyaba en el valor por defecto del código, que solo aplica mientras la App Setting no exista | `infra/desplegar_backend.ps1`, `docs/DESPLIEGUE.md` §4 bis | Hecho: `CIERRE_HABILITADO=false` en `$ajustes`, junto a `ARCHIVO_HABILITADO`, y §4 bis reescrito para describir el mecanismo real y dejar escrito que antes no lo era. Un test nuevo vigila que no vuelva a desaparecer |
| **H3** | **`POST /api/cerrar` no se puede llamar desde un puesto de trabajo con `curl` ni con `Invoke-RestMethod`**: el backend es enlazado y solo acepta lo que entra por el proxy del front. `tasks.md` T22 dice «llamar a `POST /api/cerrar`» sin decir por dónde | `docs/DESPLIEGUE.md` §5 bis, `azure-apps/postventa_incidencias.md` | Resuelto en §4 de este guion con el fragmento de consola. No es un defecto: es una consecuencia del despliegue que la tarea no menciona |
| **H4** | **El dry-run ya escribe la traza local** (R40), que tiene **clave ajena contra `postventa.partes`**. Un `hash` que no esté guardado hace fallar hasta el dry-run. `tasks.md` T22 no lo declara como precondición | `application/pipelines/paso_cierre.py`, `infrastructure/persistencia/sql/06_cierres.sql` | Recogido como precondición P5 de §2. Es la misma trampa del defecto 15 de F-010 |
| **H5** | **La siembra del login ocurre en el dry-run, no en el `commit`.** T23 pide comprobar la tabla «vacía para ese usuario» y luego ejecutar el dry-run — pero si T22 ya se ejecutó con ese usuario, la correspondencia **ya está sembrada** y el punto 1 de T23 no se puede observar | `application/pipelines/paso_cierre.py`, `resolver_login_de_sigrid` | Recogido en el paso 1 de T23: se mira **antes** de T22, o se anota que no se pudo observar. El resto de T23 sigue siendo verificable |
| **H6** | `azure-apps/sigrid_api.md` §10 lista quién consume la pasarela y **`postventa-incidencias` no está**, siendo desde F-009 el **primer escritor genérico** por `sql/write` del ecosistema | `azure-apps/sigrid_api.md` | Ya propuesto en `progress/impl_F-009.md` §6.3, y sigue abierto. Lo lleva el humano al dueño de `sigrid-api` |

> **H1 y H2 se arreglaron el 2026-09-03**, ya con la aprobación del humano,
> en el commit `82fbfb8`; el detalle está en
> `progress/impl_H1_H2_despliegue.md`. Los otros cuatro siguen abiertos: H3 y
> H4 no son defectos sino consecuencias del despliegue y del diseño, ya
> recogidas en §4 y en la precondición P5; H5 está recogido en el paso 1 de
> T23; y **H6 sigue en manos del humano**, que es quien lo lleva al dueño de
> `sigrid-api`.
