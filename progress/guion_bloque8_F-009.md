<!-- progress/guion_bloque8_F-009.md -->
# F-009 · Guion de ejecución del bloque 8 (T22–T27)

> ## Acta del 2026-09-14 · **buena parte de este bloque se ejecutó de hecho dentro de F-012, y queda levantada aquí**
>
> **Qué pasó**: F-009 lleva `blocked` desde el 2026-09-06 esperando a que F-012
> se implementara primero. Esa espera terminó. **F-012 y F-025 están cerradas**,
> y el 2026-09-11 el responsable del proyecto **cerró de verdad una reclamación
> en el ERP de producción** —`RS26.09/0150` de la obra **`0626`**— con su parte
> dentro. **Ese cierre es el de T24 de este guion**, ejecutado dentro de la
> verificación de otra feature.
>
> **Qué queda acreditado y qué no.** De las seis tareas del bloque, **solo T26
> queda marcada**. Las otras cinco tienen sus casillas rellenas **parcialmente**,
> con lo que consta y **citando dónde consta cada cosa**; lo que no consta se
> queda vacío con su motivo. Nada se ha dado por bueno por parecerse a algo que
> sí se hizo, y en particular **la prueba de F-025 no acredita el reintento de
> T27** (ver §9.6).
>
> **La fuente**: `progress/guion_bloque9_F-012.md` §9 —el acta del 2026-09-11,
> con sus mediciones— y las entradas de F-012 y F-025 de `progress/history.md`.
> Ningún agente ha ejecutado nada contra el ERP para levantar esta acta: **todo
> sale de lo que ya estaba escrito**.
>
> El acta entera —tarea por tarea, lo que queda abierto con su coste, y el
> **veredicto** para el líder— está en **§9**, al final de este fichero.

> ## Nota del 2026-09-14 · **cambia la obra sobre la que se verificó, y con ella una premisa de este guion** (resto abierto de H10)
>
> **La premisa original, literal, tal y como estaba escrita aquí hasta hoy**, en
> la nota del 2026-09-06 y en la **P5** de §2: *«El bloque 9 de F-012 ejecuta de
> hecho un cierre completo —adjuntar y cerrar— **sobre una reclamación de la
> obra de prueba 404**»*, y *«**Por qué la 404 y no Mirasierra.** La decisión
> del humano del 2026-09-06 es que **toda escritura de prueba** contra el ERP
> cae en la obra de prueba. Cerrar una incidencia real del piloto es otra
> decisión, y otra autorización»*.
>
> **Esa premisa la levantó el responsable del proyecto el 2026-09-10**, y consta
> fechada en la nota del 2026-09-10 de `progress/guion_bloque9_F-012.md`: se le
> planteó de forma explícita que la **0626 no es una obra de pruebas, sino una
> obra en uso**, y lo reafirmó. La verificación —la que de hecho se ejecutó el
> 2026-09-11— fue sobre:
>
> | Qué | Cuál |
> |---|---|
> | Obra | **0626**. **No es una obra de pruebas: es una obra en uso** |
> | Incidencia | **`RS26.09/0150`**, de tipo **708**, dada de alta a mano en el ERP por el responsable |
>
> **Qué implica, y hay que decirlo entero**: el cierre y el documento adjunto
> quedan **en el histórico de una obra en uso**, a la vista de cualquiera que la
> consulte en Sigrid. No hay deshacer.
>
> Este guion seguía nombrando la obra genérica: era el **resto abierto de H10**
> (`progress/guion_bloque9_F-012.md` §8, que lo deja escrito como «queda por
> corregir»). **Corregido hoy**, con marcas fechadas dentro —la nota del
> 2026-09-06 y la P5 de §2— y **sin borrar la premisa anterior**, que queda
> arriba para que se sepa cuál era y quién la levantó. Mismo criterio que la
> nota del 2026-09-10 del bloque 9 y que la enmienda del 2026-09-03 bajo el R28
> de `specs/F-010-despliegue/requirements.md`.
>
> **Lo que NO cambia —y sobre una obra en uso pesa más, no menos**: comprobación
> previa antes de cada escritura; **autorización expresa del responsable para
> cada incidencia concreta** (P6), no «para probar el cierre»; y ninguna
> escritura desde un puesto de trabajo.

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

> ## Nota del 2026-09-06 · lee esto antes de recorrer el guion
>
> El humano eligió el **orden (b)** de `specs/F-012-grafico-sigrid/design.md`
> §13: **F-012 primero**. Eso cambia lo que este guion espera ver, y por eso
> tiene correcciones fechadas dentro (P5, T22 y T24).
>
> **El bloque 9 de F-012 ejecuta de hecho un cierre completo** —adjuntar y
> cerrar— **sobre una reclamación de la obra de prueba 404**, con su guion
> propio en `progress/guion_bloque9_F-012.md`. Cuando ese bloque pase, este
> guion ya no se recorre entero: sus T22, T24, T25 y T27 habrán quedado
> ejercitados sobre la 404 por T25, T27, T29 y T30 de aquel, con evidencias en
> sus casillas.
> > *(**Corregido el 2026-09-14**: no fue la obra de prueba **404**. El
> > responsable levantó esa premisa el 2026-09-10 y el bloque 9 se ejecutó el
> > 2026-09-11 sobre **`RS26.09/0150` de la obra `0626`, una obra en uso**. Ver
> > la nota del 2026-09-14, arriba. Y **lo que quedó ejercitado no fueron las
> > cuatro tareas enteras**: solo T26 queda marcada; el detalle, tarea por
> > tarea, en §9.)*
>
> **Al reanudar F-009, este guion se recorre con lo que quede**: lo que el
> bloque 9 no haya cubierto —el caso de T23 sobre la siembra del login, T26 si
> el guard rechazara algo, y el cierre sobre el piloto de Mirasierra cuando el
> humano lo autorice—. Antes de nada, se mira qué casillas de
> `guion_bloque9_F-012.md` están rellenas.
> > *(**2026-09-14**: ya se ha mirado, y está volcado en §9 de este fichero. Lo
> > que queda es bastante más que «el caso de T23»: ver §9.4.)*
>
> Dos consecuencias que ya están escritas en este fichero, con su fecha:
>
> - **R21 de F-009 está derogado** por R48 de F-012: el dry-run del cierre ya
>   **no** trae `aviso_sin_grafico`, y en su lugar trae el bloque `grafico`.
> - **El `commit` del cierre exige el gráfico adjuntado** (R2 de F-012): un
>   `/api/cerrar` con `commit` sobre un parte que no consta `adjuntado`
>   responde **409**, sin tocar el ERP.

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
> una vez. **Resuelto el 2026-09-03 en el commit `82fbfb8`**, con H2, y
> **corregido el mismo día en `bed95ea`**: `SIGRID_BASE_DATOS` bajó de secreto
> de Key Vault a App Setting plana, porque el nombre de la base del ERP ya está
> escrito en documentos versionados y el secreto no protegía nada que no
> estuviera ya. Lo que sigue es lo que queda, que no es cero: los **valores** de
> los **dos** secretos que quedan no puede ponerlos un script, porque no
> están —ni pueden estar— en el repositorio.

### Qué hace ya el despliegue, sin que nadie teclee nada

`infra/desplegar_backend.ps1` fija **las ocho** App Settings de F-009 en cada
ejecución:

| Cómo | Cuáles |
|---|---|
| Referencia a Key Vault, resuelta por la identidad gestionada | `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` |
| En claro en `$ajustes` | `CIERRE_HABILITADO=false`, `SIGRID_BASE_DATOS`, `SIGRID_TIMEOUT_S`, `SIGRID_REINTENTOS`, `SIGRID_TIP_RECLAMACION`, `SIGRID_ZONA_HORARIA` |

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

### Paso 0 · en un solo script (recomendado)

Desde el 2026-09-06 el Paso 0 entero —los dos secretos, las ocho App Settings y
la comprobación de que las referencias se resuelven— lo hace un script:

```
powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1
```

**Qué se espera ver**, en este orden: el plan (grupo, Function App, Key Vault,
los **dos** secretos que va a pedir por su nombre); la carga de secretos, que los
pide **a ciegas** —deja vacío el que ya esté cargado y no quieras tocar—; el
despliegue de la configuración con `-SinPublicar`, con su `Ventana de escritura
: CERRADA`; y al final la tabla de las **once** referencias a Key Vault, una por
línea, con su estado:

```
  SIGRID_API_BASE_URL    -> Resolved
  SIGRID_API_KEY         -> Resolved

Paso 0 COMPLETO: 11/11 referencias resueltas.
```

Ese veredicto es lo que sustituye al «mira en el portal que ninguna App Setting
salga con error»: el plano de gestión publica el **estado** de cada referencia
—y su motivo de fallo— sin publicar nunca el valor que hay detrás, así que la
tabla se puede pegar en `progress/` tal cual.

**Si no sale eso**: el script imprime qué referencia no se resuelve y por qué, y
sale con código distinto de cero (`12` alguna en error, `11` no se ha podido
preguntar, y el del despliegue si es el despliegue el que falla). Una referencia
en error es casi siempre un secreto que falta en el vault o el rol de lectura de
la identidad gestionada sin propagar todavía.

**`-WhatIf` solo lee**: no invoca a ninguno de los dos scripts que escriben, y
aun así imprime la tabla de estados. Es la forma de preguntarle al entorno qué le
falta sin tocarlo, y sirve para comprobar la precondición **P3** antes de nada.

> **`CIERRE_HABILITADO` queda apagado**, porque quien fija las App Settings es
> `desplegar_backend.ps1` y ahí nace `false` en cada ejecución. La ventana se
> abre después, a mano, con la línea del paso 3 de T22.

Lo que sigue es la **vía manual**, paso a paso. No hace falta si se usa el
script; se conserva porque explica qué hace cada cosa y porque es el camino si
el script no se quiere usar.

### Paso 0, a mano (1) · Los dos secretos del vault (una sola vez, antes de T22)

**Es lo único que queda a mano, y es a mano a propósito**: los dos valores los
da el dueño de `sigrid-api` (`azure-apps/sigrid_api.md` §3.1 y §3.3), no se
deducen y no pueden entrar al repositorio. Se piden a ciegas por consola
(`Read-Host -AsSecureString`), no se escriben en ningún fichero y no quedan en
el historial de la consola:

```
powershell -ExecutionPolicy Bypass -Command ".\infra\cargar_secretos_postventa.ps1 -Solo sigrid-api-base-url,sigrid-api-key"
```

> **`-Solo` no funciona con `powershell -File`**: el parámetro no llega y el
> script pediría los once secretos del backend. Se lanza con `-Command`, como
> explica `docs/DESPLIEGUE.md` §2.
>
> **`sigrid-base-datos` ya no se teclea aquí** (corrección del 2026-09-03,
> `bed95ea`): la base **de negocio** —la única con escritura permitida en la
> pasarela, `sigrid_api.md` §4.1— la fija el despliegue como App Setting plana,
> porque su nombre ya está escrito en documentos versionados del repositorio.

### Paso 0, a mano (2) · El despliegue de la configuración

Y después, **un despliegue del backend**, que es lo que fija las App Settings:

```
powershell -ExecutionPolicy Bypass -File .\infra\desplegar_backend.ps1 -SinPublicar
```

**Qué se espera ver**: el script imprime `App Settings : N, de las que 11 son
referencias` y `Ventana de escritura : CERRADA (archivo Y cierre en el ERP)`.

**Comprobación**: `.\infra\14_paso0_sigrid.ps1 -WhatIf`, que solo lee e imprime
la tabla de estados; o, si se prefiere a ojo, en el portal, que ninguna App
Setting salga con error. Una referencia que no se resuelve es un secreto que no
está en el vault, o el rol `Key Vault Secrets User` sin propagar.

### Si el entorno ya está desplegado y no se quiere redesplegar

Es el caso real de hoy: la Function App lleva el código de F-009 pero se
desplegó **antes** de este arreglo, así que no tiene ninguna de las ocho. Con
los secretos ya subidos (arriba), las App Settings se pueden poner sueltas.
Hace falta el URI del vault:

```
az keyvault show -g rg-postventa-dev -n <el kv del proyecto> --query properties.vaultUri -o tsv
```

Las **dos** sensibles, **por referencia** (las comillas no son decoración: sin
ellas `cmd.exe` interpreta los paréntesis, ver `infra/desplegar_backend.ps1`):

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings "SIGRID_API_BASE_URL=@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/sigrid-api-base-url)" "SIGRID_API_KEY=@Microsoft.KeyVault(SecretUri=<vaultUri>secrets/sigrid-api-key)"
```

Y las **seis** planas, incluido el interruptor **explícitamente apagado** y la
base del ERP, que desde el 2026-09-03 ya no es un secreto de vault:

```
az functionapp config appsettings set -g rg-postventa-dev -n func-postventa-dev --settings CIERRE_HABILITADO=false SIGRID_BASE_DATOS=ruesma SIGRID_TIMEOUT_S=35 SIGRID_REINTENTOS=3 SIGRID_TIP_RECLAMACION=708 SIGRID_ZONA_HORARIA=Europe/Madrid
```

**Qué se espera ver**: `az` devuelve el JSON de las App Settings sin error, y
la Function App se reinicia sola.

**Si no sale eso**: si el `secret set` del paso anterior falló por permisos, es
que la sesión de `az` no tiene rol sobre el vault; si el `appsettings set`
responde «X no se esperaba en este momento», faltan las comillas de la
referencia.

**Comprobación**: `.\infra\14_paso0_sigrid.ps1 -WhatIf` imprime el estado de las
once referencias sin tocar nada, y ese es el sitio donde se ve. Si no, la
referencia se ha resuelto cuando la Function arranca, y se verá en T22: si no se
resuelve, el endpoint responde `503` nombrando la variable que falte.

---

## 2 · Precondiciones comunes (se comprueban **antes** de abrir la ventana)

- [ ] **P1** · `bash harness/init.sh` en verde en la rama `feature/F-009-cierre-sigrid`.
- [ ] **P2** · El backend desplegado lleva el código de F-009
      (`infra\desplegar_backend.ps1`). Sin esto, `/api/cerrar` no existe y la
      respuesta es un 404, no un 503.
- [ ] **P3** · Paso 0 de §1 hecho: los **dos secretos** de Sigrid en el Key
      Vault y el backend desplegado **después** del commit `bed95ea` (o, si no
      se redespliega, las ocho App Settings puestas a mano según §1). Lo hace
      entero `.\infra\14_paso0_sigrid.ps1`, y **se comprueba con él mismo**:
      `.\infra\14_paso0_sigrid.ps1 -WhatIf` solo lee y tiene que terminar en
      `Paso 0 COMPLETO: 11/11 referencias resueltas`. Si no se quiere ejecutar
      nada, la comprobación equivalente es el portal: ninguna referencia a Key
      Vault con error.
- [ ] **P4** · La clave de función de `sigrid-api` y la raíz de la pasarela, a
      mano para los scripts de lectura (§3). No se escriben en ningún fichero.
- [ ] **P5** · *(corregido el 2026-09-06, orden (b) de `F-012/design.md` §13;
      **y corregido otra vez el 2026-09-14**: donde dice «la obra de prueba
      404» hay que leer **`RS26.09/0150` de la obra `0626`, una obra en uso**
      —el responsable levantó aquella premisa el 2026-09-10, ver la nota del
      2026-09-14 arriba—. Para el cierre que **ya se ejecutó**, esta
      precondición **se cumplió**: el parte estaba archivado, guardado y
      adjuntado antes del `commit`, §9.3)*
      **Una reclamación de la obra de prueba 404** —no Mirasierra— **que ya
      tenga su gráfico adjuntado por el bloque 9 de F-012**, y su parte ya
      recorrido en el front: subido, validado `apto` / `archivo_y_cierre`,
      **guardado** (`POST /api/parte`, F-019), **archivado**
      (`POST /api/archivar`) y **adjuntado** (`POST /api/adjuntar`).
      No es una formalidad, y ahora son **dos** las claves ajenas contra
      `postventa.partes`: la de `postventa.cierres` (R40) y la de
      `postventa.graficos` (R46 de F-012). Un `hash` que no esté guardado hace
      fallar **hasta el dry-run**. Es la misma trampa del defecto 15 de F-010.
      > **Por qué la 404 y no Mirasierra.** La decisión del humano del
      > 2026-09-06 es que **toda escritura de prueba** contra el ERP cae en la
      > obra de prueba. La candidata se localiza con
      > `infra/15_reclamaciones_obra_prueba.ps1`. Cerrar una incidencia real del
      > piloto es otra decisión, y otra autorización.
      >
      > > *(**Enmendado el 2026-09-14**, sin borrar lo de arriba: esa decisión
      > > **la levantó el propio responsable el 2026-09-10**, planteándosele de
      > > forma explícita que la **0626 es una obra en uso**. La candidata se
      > > localiza igual, con `infra/15_reclamaciones_obra_prueba.ps1
      > > -CodigoObra 0626`, y **la autorización por incidencia concreta sigue
      > > siendo obligatoria**: al no haber ya una obra de pruebas detrás, P6
      > > gana peso en vez de perderlo. Mirasierra sigue **fuera**: nadie ha
      > > autorizado cerrar una incidencia del piloto.)*
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

Hay un **sexto** script del bloque, `infra/14_paso0_sigrid.ps1`, que no está en
esta tabla porque no es de esta familia: no lee del ERP, **aprovisiona** —hace el
Paso 0 de §1— y por eso se ejecuta una vez, antes de todo lo demás, y no durante
las tareas. Él tampoco escribe en Sigrid; lo que escribe es el Key Vault y las
App Settings, y lo escriben los dos scripts del despliegue que invoca.

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

> **La raíz y `PG_HOST` NO se leen con `az functionapp config appsettings list`,
> y no es una preferencia: ese comando no funciona para ellas.** Devuelve el
> valor **crudo** de la App Setting, y `SIGRID_API_BASE_URL` y `PG_HOST` son
> **referencias a Key Vault**, así que lo que sale es la cadena literal
> `@Microsoft.KeyVault(SecretUri=...)`, no la URL ni el host. Azure resuelve la
> referencia **al arrancar la Function**, no en la API de gestión: por ahí no
> hay forma de leer el valor resuelto. Se teclean, como la clave. Quien quiera
> comprobar que la referencia está bien puesta, que mire su **estado**
> (`Resolved`), no su valor: eso lo hace `infra/14_paso0_sigrid.ps1` (§1).
> `SIGRID_BASE_DATOS` sí se puede leer así, porque desde `bed95ea` es una App
> Setting plana. Corregido el 2026-09-06; el fragmento de consola de
> `progress/current.md` ya no lo intenta.

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
hace falta **el JSON crudo de la respuesta** (los cinco campos de R9 y —desde
el 2026-09-06— el bloque `grafico` de R49 de F-012, tal y como viajan) o acotar
la llamada a **una sola** incidencia.

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
**las cinco cosas** que R9 exige más —*corregido el 2026-09-06*— el bloque
`grafico` de R49 de F-012, en lugar del aviso de R21 que R48 derogó; y que **no
cambia nada** en Sigrid (R8, R10). Es el único paso que se puede repetir sin
coste, y el que sostiene todo lo demás: sin un dry-run correcto no se escribe
(R10).

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
   *Si sale 503 nombrando `SIGRID_API_BASE_URL` o `SIGRID_API_KEY`*: falta el
   Paso 0 de §1 —los dos secretos del vault—. Vuelve ahí.
   *Si sale 503 nombrando `SIGRID_BASE_DATOS`*: eso ya no es un secreto, es una
   App Setting plana; lo que falta es el redespliegue (o la línea `az` de las
   seis planas de §1).
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
   —*corregido el 2026-09-06*— un bloque **`grafico`** con
   `estado: "adjuntado"`, `nombre_fichero`, `sha256` y `adjuntado_at_utc`
   relleno (R49 de F-012).
   > **`aviso_sin_grafico` ya NO tiene que aparecer.** R48 de F-012 derogó R21
   > de F-009: con el parte adjuntándose antes del cambio de estado, aquel aviso
   > sería falso. **Si aparece**, el despliegue no lleva el código de F-012, y
   > entonces el `commit` de T24 tampoco lo exigirá: se para y se redespliega.
   >
   > Si el bloque 9 de F-012 no se ha ejecutado sobre esta reclamación, lo que
   > sale aquí es `grafico.estado: "no_consta"`, y **eso no es un error del
   > dry-run** (R50): el que fallará es el `commit` de T24, con un 409.

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

**Casilla de resultado · T22** — *rellenada el 2026-09-14 levantando acta de lo
que se ejecutó el 2026-09-11 dentro del bloque 9 de F-012. Nadie recorrió esta
tarea como tal.*

| Campo | Valor |
|---|---|
| Fecha y hora | **2026-09-11**, `08:27:42` UTC — el **dry-run del cierre** que ejecutó el responsable dentro del bloque 9 de F-012. Fuente: `guion_bloque9_F-012.md` §9.2 (tabla de los registros de `appi-postventa-dev`) y su casilla de T26 |
| Foto de partida (`ide` / `emp` / `est` / estado legible / `tiemod` / `MAX(ide)`) | **no recorrida.** No se lanzó `09_estado_reclamacion_sigrid.ps1` en ningún momento del circuito (casillas de T25, T26 y T29 de F-012: «no recorrido»). **Sin foto de partida, el `MAX(ide)` de antes ya no es recuperable** |
| Paso 2 · HTTP con el interruptor apagado | **NO EJECUTADO.** La ventana ya estaba abierta cuando se ejecutó el circuito (casilla de T25 de F-012, paso 2: «el `503` de §0.1 **no se observó** contra el entorno desplegado»). Y sigue sin observarse: el paso 3 de T32 de F-012 —el `503` en el borde con la ventana ya cerrada— quedó como «el único resto abierto» de aquella tarea |
| Paso 4 · HTTP y `estado` del dry-run | **HTTP 200** [MEDIDO en `appi-postventa-dev`], en **4.424 ms**. El campo `estado` **no se anotó** |
| Paso 4 · las seis cosas de R9, ¿estaban todas? | **sin anotar.** El JSON de la respuesta no se guardó (casilla de T26 de F-012: «El `dry_run.grafico.estado` no se anotó»; casilla de T25: «el objeto `dry_run` campo a campo no quedó registrado»). **De R9 no consta ni un campo** |
| Paso 4 · bloque `grafico` (R49 de F-012): `estado` · `nombre_fichero` · `sha256` | **sin anotar**, y además **el caso que esta casilla pide no llegó a darse**: ese dry-run fue a las `08:27:42` y el gráfico se adjuntó a las `08:28:03`, así que el bloque que viajó —de haberse mirado— habría sido `dry_run_ok`, **no `adjuntado`**. El dry-run del cierre **con el gráfico ya dentro** nunca se observó (casilla de T29 de F-012, paso 2) |
| Paso 4 · ¿aparecía `aviso_sin_grafico`? (2026-09-06: tiene que ser **no**) | **sin anotar** (casilla de T26 de F-012). Que R48 derogó R21 **no está comprobado contra el entorno desplegado**; lo que sí consta, indirecto, es que el despliegue llevaba el código de F-012, porque `adjuntar` respondió y escribió |
| `login_sigrid` que devolvió el dry-run | **sin anotar** (casilla de T25 de F-012). Indirecto, y solo eso: el `commit` posterior salió `200` y escribió, y R31 aborta con `409` **sin tocar Sigrid** si el ERP no confirma el login — luego **hubo un login confirmado**. Cuál era, no consta |
| Paso 5 · ¿el ERP intacto? | **NO COMPROBADO.** El paso 3 de T26 de F-012 quedó «NO EJECUTADO» y el paso 5 de su T25 «no recorrido». **Que el dry-run no escribe sigue sin una sola prueba contra el ERP**: es lo que sostiene R8, R10 y R20 |
| Paso 6 · traza local | **no recorrido.** No se lanzó `12_traza_cierre_local.ps1` (casilla de T25 de F-012, paso 6) |
| **T22 queda marcada** | **no.** Consta que el dry-run del cierre **funciona contra el ERP real** —`200` en 4,4 s desde el entorno desplegado—, y de paso confirma **R50 de F-012** (el dry-run **no** exige el gráfico: se pidió sin él y respondió `200`). **No consta nada de su contenido** —ninguna de las seis cosas de R9— **ni que no escriba**, que es la mitad de lo que esta tarea existe para probar. *Acta del 2026-09-14* |

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

**Casilla de resultado · T23** — *rellenada el 2026-09-14. **Esta tarea no se
tocó**: ni el bloque 9 de F-012 ni la prueba de F-025 recorrieron ninguno de
sus cuatro puntos.*

| Campo | Valor |
|---|---|
| Fecha y hora | **NO EJECUTADA.** Ni en el circuito del 2026-09-11 ni después |
| 1 · ¿la tabla estaba vacía para ese usuario? | **no observado.** No se lanzó `12_traza_cierre_local.ps1` (casilla de T25 de F-012, paso 6). Y es el caso que **H5** de §8 anticipaba: para cuando alguien mire, la siembra ya habrá ocurrido en algún dry-run anterior |
| 2 · ¿el candidato existe **exactamente una vez**? | **no observado.** No se lanzó `07_alta_usuario_sigrid.ps1 -VerificarAhora`. Es **solo lectura** (un `COUNT(*)`) y **se puede recuperar hoy** |
| 3 · ¿quedó `verificada`? ¿el segundo dry-run devolvió el mismo login? | **no observado.** La primera mitad es una lectura de `postventa.usuarios_sigrid` y **se puede recuperar hoy**; la segunda exige otro dry-run, que necesita la ventana abierta (§0.1) |
| 4 · ¿el login inexistente fue rechazado **sin escribir**? | **NO EJECUTADO**, y es el punto que sostiene R31 y R32. Se hace con `07_alta_usuario_sigrid.ps1 -VerificarAhora` sobre un login inventado: **también es solo lectura** |
| **T23 queda marcada** | **no.** Lo único acreditable es **indirecto**: el `commit` del cierre de `08:28:12` respondió `200` y escribió en el ERP, y R31 manda abortar con `409` **sin tocar Sigrid** si el ERP no confirma el login — luego para ese usuario la correspondencia se resolvió y el ERP la confirmó **al menos una vez**. **Eso no verifica ninguno de los cuatro puntos**: ni que el candidato exista exactamente una vez, ni que la fila quedara `verificada`, ni que un segundo dry-run no vuelva a derivar, ni —sobre todo— que un login que no existe se rechace **sin escribir**. *Acta del 2026-09-14* |

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

> **Precondición añadida el 2026-09-06 (R2 de F-012).** El parte tiene que
> constar **`adjuntado`** en `postventa.graficos`, o el `commit` del paso 4
> responde **409** sin tocar el ERP, diciendo que primero se adjunta con
> `POST /api/adjuntar`. Se comprueba antes de empezar:
>
> ```
> powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado
> ```
>
> *Se espera*: `TRAZA LOCAL DEL GRAFICO : PASA`, con `estado = adjuntado`.
> *Si no está adjuntado*: se pasa **antes** por `POST /api/adjuntar` con
> `commit` —el paso 3 de T27 de `progress/guion_bloque9_F-012.md`, con su
> autorización— y solo después se vuelve aquí. **No se salta**: es lo que
> impide que esta reclamación quede cerrada sin su parte dentro.

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
   origen legible, el destino `CER`, el `login_sigrid` y —*corregido el
   2026-09-06*— el bloque **`grafico` con `estado: "adjuntado"`**, no
   `aviso_sin_grafico`.
   **Leerlo no es una formalidad**: lo que se confirma en el paso 4 es esto.
   *Si `grafico.estado` no es `adjuntado`*: **para aquí**. El `commit` del paso
   4 va a responder 409 (R2 de F-012). Vuelve a la precondición añadida de esta
   tarea.
   *Si el estado de origen no es el del paso 1*: alguien ha movido la
   reclamación. Vuelve al paso 1.

4. **Confirmar en el front y ejecutar con `commit: true`.** Vía (a) de §4: el
   botón de confirmación del front, que **caduca** (R15) — si tarda, el segundo
   clic no dispara y hay que volver a armarla. Si se usa la consola, el mismo
   fragmento con `COMMIT = true` (que pone `commit` y `confirmado`).

   *Se espera*: `HTTP 200` con `estado: "cerrado"` y **`filas_afectadas: 2`**.
   *Si sale `409` diciendo que el parte no consta adjuntado* (2026-09-06, R2 de
   F-012): **no se ha tocado el ERP**. Falta el `POST /api/adjuntar`: ver la
   precondición añadida de esta tarea.
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

**Casilla de resultado · T24** — *rellenada el 2026-09-14. **El cierre real
ocurrió**, dentro del bloque 9 de F-012; lo que no ocurrió fueron casi todas
sus comprobaciones.*

| Campo | Valor |
|---|---|
| Fecha y hora | **2026-09-11**, `08:28:12` UTC (`guion_bloque9_F-012.md` §9.2 y casilla de su T29) |
| Incidencia cerrada (código) | **`RS26.09/0150`**, obra **`0626`** — una obra **en uso**, no la de prueba: ver la nota del 2026-09-14 arriba |
| Autorización expresa del humano | **sí.** Lo ejecutó **el propio responsable del proyecto**, delante del ERP, con la autorización que exige P6 (`guion_bloque9_F-012.md` §9.1 y casilla de su T29: «sí: lo ejecutó el responsable») |
| **¿el parte constaba `adjuntado`?** (2026-09-06, R2 de F-012) | **sí.** El gráfico entró a las `08:28:03` (`200`, 8.471 ms) y el cierre fue **9 s después**. Es la precondición que F-012 existía para garantizar, y es **la única de esta tarea que consta cumplida**. Consecuencia: **la anomalía que F-009 aceptaba como riesgo —cerrar sin el parte dentro— no llegó a producirse ni una vez** (`history.md`, entrada de F-012) |
| 1–2 · `ide` / `emp` / `est` / `res` / `tiemod` / `MAX(ide)` de partida | **no recorrido.** No se lanzó `09_estado_reclamacion_sigrid.ps1` (casilla de T29 de F-012, paso 3). **Sin esta foto, el paso 6 ya no es recuperable entero** |
| 3 · dry-run leído (estado origen → destino, login, `grafico.estado`) | **ejecutado, pero no es el que esta tarea pide.** El único dry-run del cierre fue el de `08:27:42`, **antes de adjuntar**: `grafico.estado` no podía ser `adjuntado`, y ningún campo se anotó (casilla de T29 de F-012, paso 2). Leer el dry-run **con el gráfico dentro** —que es lo que se confirma en el paso 4— **no ocurrió** |
| 4–5 · HTTP, `estado` y `filas_afectadas` | **HTTP 200** [MEDIDO], en **472 ms** —el paso más rápido del circuito—. `estado` y `filas_afectadas` **sin anotar**: **el `filas_afectadas: 2` de R22 NO está comprobado** (casilla de T29 de F-012, paso 4) |
| 6 · `con.est` = `CER` · `tiemod` sin mover · nuevo `MAX(ide)` | **`CER`: sí**, comprobado por el responsable en la ficha de Sigrid —«cerró una y lo hizo bien»—, **no con el script**. **`tiemod`: NO comprobado.** **`MAX(ide)` = anterior + 1: NO comprobado**, y **ya no es recuperable** porque nadie anotó el de partida |
| 7 · veredicto campo a campo | **NO COMPROBADO.** No se lanzó `10_log_cierre_sigrid.ps1`. De R24 y R25 —`tab`, `tip`, `cod`, `res`, `ope`, `est`, `ori`, `emp`, `usu`, `tex`— **no consta ni un campo** |
| 7 · **huso de `fec`/`hor`** | **NO COMPROBADO.** Es **el hueco más concreto de todo el bloque**: §0.2 de este guion daba el defecto por probable —era la única decisión de la feature que no se pudo tomar con un dato—, y **la fila de auditoría del primer cierre real está escrita en producción y nadie la ha mirado** (casilla de T29 de F-012, paso 5). **Se puede recuperar hoy: es solo lectura y la fila sigue ahí** |
| 9 · traza local (`cerrado`, `oid` sí, login no) | **no recorrido** (casilla de T29 de F-012, paso 7). R41 y R43 siguen apoyados solo en tests. **Recuperable hoy sin coste**: `12_traza_cierre_local.ps1` solo lee, y del esquema propio |
| **T24 queda marcada** | **no**, y no por poco. **Lo sustantivo de F-009 está acreditado**: una reclamación real se cerró en el ERP de producción desde el servicio desplegado, con autorización, con su parte dentro, y el responsable lo vio en Sigrid. Pero de los **nueve pasos** del contrato de esta tarea solo constan el **4** (parcial: el HTTP, no el `estado` ni las filas) y **la mitad del 6** (el `CER`, no `tiemod` ni `MAX(ide)`). Los pasos **5, 7 y 9** —las 2 filas, la fila de `dbo.log` campo a campo **con su huso**, y la traza local— **no los ha mirado nadie**. *Acta del 2026-09-14* |

> **Enmienda del 2026-09-15 · los pasos 6, 7 y 9, ya recorridos.** La tabla de
> arriba se deja **tal cual**, con fecha, porque era cierta el 2026-09-14. Lo
> que sigue la corrige en tres filas, con lo medido en la **sesión de solo
> lectura** del **§10** (cuatro scripts, `PASA` los cuatro, sin abrir la ventana
> de escritura). **Los pasos 2, 3, 4, 5 y 8 siguen como están arriba.**

| Campo | Valor enmendado (2026-09-15) |
|---|---|
| 6 · `con.est` = `CER` · `tiemod` sin mover · nuevo `MAX(ide)` | **`CER`: COMPROBADO CON EL SCRIPT.** `09_estado_reclamacion_sigrid.ps1` da `ESTADO DE LA RECLAMACION : PASA`: `ide` **2833896**, `emp` **1**, `est` actual **9 = `CER / CERRADA`** y **destino resuelto contra `conest`** también **9 = `CER`** (R1). Ya no depende de lo que viera una persona en la ficha. **`tiemod`: sigue SIN comprobar** —hoy vale `46275.647118`, pero **nadie anotó el de partida**, así que no compara con nada—. **`MAX(ide)` = anterior + 1: sigue SIN comprobar y sigue sin ser recuperable** (hoy da `8466095` y, minutos después, `8466171`: el ERP sigue vivo). De dónde sale: **§10.3**, veredicto de `09` |
| 7 · veredicto campo a campo | **COMPROBADO, PASA.** `10_log_cierre_sigrid.ps1` da `FILA DE AUDITORIA DEL CIERRE : PASA` sobre la fila `ide` **8457839** —localizada por `11`—, **una sola fila nueva (1/1)** y **los once campos del §7.3 de `design.md` en verde**: `tab` con, `tip` 708, `cod` `RS26.09/0150`, `ope` 5, `est` 1, `ori` 0, `emp` 1, `usu` `pgris`, `tex` «Cerrar parte (postventa-incidencias)», `res` «fuga en caldera». **R24 y R25 quedan acreditados.** De dónde sale: **§10.3**, veredicto de `10` |
| 7 · **huso de `fec`/`hor`** | **COMPROBADO: `HORA LOCAL (correcto)`.** En el ERP está escrito `2026-09-11 10:28:12` (`fec = 20260911`, `hor = 102812`); frente a la hora local de referencia, **diferencia 0,0 min**; frente a la UTC, 120,0 min. **El defecto que §0.2 daba por probable NO existía: no escribimos en UTC.** Era la única decisión de la feature tomada sin un dato (`impl_F-009.md` §3.3.a) y ahora lo tiene. De dónde sale: **§10.3**, veredicto de `10`, lanzado con el parámetro `-InstanteCierreUtc` que el commit **`a356875`** añadió precisamente para poder juzgar el huso **días después** del cierre |
| 9 · traza local (`cerrado`, `oid` sí, login no) | **COMPROBADO, PASA.** `12_traza_cierre_local.ps1` da `TRAZA LOCAL DEL CIERRE : PASA`: **1/1** trazas, origen `PTE`, destino `CER`, estado **`cerrado`**, marca de tiempo del dry-run **sí**, del cierre **sí**, «oid de quien confirmó (R41)» **sí**, «el login del ERP NO está en la traza (R43)» **no**. **R41 y R43 quedan acreditados.** Y los **`intentos 2`** cuadran con las dos llamadas a `cerrar` de §9.2 —dry-run `08:27:42` y commit `08:28:12`—, que es una confirmación cruzada que nadie había buscado. **Salvedad**: no se pasó `-UsuarioOid`, así que consta que **hay** un oid, no **cuál**. De dónde sale: **§10.3**, veredicto de `12` |
| **T24 sigue sin marcar** | **sí, sigue sin marcar.** De los nueve pasos constan ahora el **4** (parcial), el **6**, el **7** y el **9**; faltan el **2**, el **3**, el **5** y el **8**, y el `filas_afectadas: 2` de R22 **no es recuperable hacia atrás**: lo dará el siguiente cierre real. *Enmienda del 2026-09-15* |

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

**Casilla de resultado · T25** — *rellenada el 2026-09-14. **No se ejecutó**, y
es la más barata de recuperar de todo el bloque.*

| Campo | Valor |
|---|---|
| Fecha y hora | **NO EJECUTADA.** No se lanzó `11_trazabilidad_tex_sigrid.ps1` en ningún momento: de las comprobaciones con los scripts de `infra/`, **ninguna se ejecutó** (`guion_bloque9_F-012.md` §9.4, párrafo final) |
| ¿el filtro por prefijo encuentra nuestro cierre? | **no comprobado.** Que seguimos saliendo en los informes de Posventa —la mitad de D1 de `design.md`— sigue sin verificarse contra el ERP |
| nº de filas con el texto propio en todo el ERP | **no comprobado.** Tendría que valer **1**: consta **un** cierre real de este servicio, el de `08:28:12` del 2026-09-11 |
| ¿alguna de esas filas no es nuestra? | **no comprobado** |
| **T25 queda marcada** | **no.** Su precondición —«T24 marcada, con al menos un cierre real hecho»— **sí se cumple**: el cierre existe y su fila de `dbo.log` está escrita en producción. La tarea es **una lectura de dos consultas, sin ventana de escritura y sin riesgo**, y además **localiza la fila de log del cierre** —el script la lista una a una—, que es justo lo que le falta al paso 7 de T24. *Acta del 2026-09-14* |

> **Enmienda del 2026-09-15 · T25 EJECUTADA y marcada.** La tabla de arriba se
> deja tal cual, con fecha: era cierta el 2026-09-14. Lo que sigue la sustituye,
> con lo medido en la sesión de solo lectura del **§10**.

| Campo | Valor enmendado (2026-09-15) |
|---|---|
| Fecha y hora | **EJECUTADA el 2026-09-15**, en la sesión de solo lectura del §10, desde el puesto y sin abrir la ventana de escritura. Veredicto: `TRAZABILIDAD DEL TEXTO PROPIO : PASA`. Hubo que arreglar antes el script: preguntaba `tex = ?` sobre una columna `text` y devolvía `500` (commit **`a356875`**, defecto 2; ver §10.2) |
| ¿el filtro por prefijo encuentra nuestro cierre? | **SÍ.** «el prefijo del ERP encuentra nuestro cierre» = **True/True**, y devuelve **una sola** fila de la incidencia: `8457839 \| 20260911 \| 102812 \| pgris \| Cerrar parte (postventa-incidencias)`. **Seguimos saliendo en los informes de Posventa**, que es la mitad de D1 de `design.md` |
| nº de filas con el texto propio en todo el ERP | **1**, esperado **1**. Sobre `dbo.log` entera: `8457839 \| 20260911 \| 102812 \| pgris \| con \| 708 \| RS26.09/0150`. Y «el filtro exacto no devuelve más de lo listado» = **1/1** |
| ¿alguna de esas filas no es nuestra? | **no.** El filtro exacto devuelve **solo lo nuestro** y **ninguno** de los 6.843 cierres manuales: es lo que permitiría revertir solo lo de este servicio si el piloto se torciera. La otra mitad de D1 |
| **T25 queda marcada** | **SÍ.** Las dos condiciones de D1 comprobadas contra el ERP, sin escribir nada. Y de regalo, **la fila de log del cierre localizada** (`ide` 8457839), que es lo que permitió recorrer el paso 7 de T24. *Enmienda del 2026-09-15* |

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

**Casilla de resultado · T26** — *rellenada el 2026-09-14. **Es la única tarea
del bloque que queda marcada**, y se marca porque su contrato dice que se
observa en la respuesta del paso 4 de T24 — que existe.*

| Campo | Valor |
|---|---|
| Fecha y hora | **2026-09-11**, `08:28:12` UTC. Esta tarea no tiene ejecución propia por diseño: «se hace **DENTRO de T24**, no después: lo que se observa es la respuesta del paso 4» |
| ¿el guard aceptó el batch tal cual? | **SÍ.** La cadena, entera: (1) la llamada respondió **`200`** [MEDIDO en `appi-postventa-dev`, `guion_bloque9_F-012.md` §9.2]; (2) **la reclamación quedó en `CER`**, comprobado por el responsable en la ficha de Sigrid (§9.1: «cerró una y lo hizo bien»). Si `SqlWriteGuard` hubiera rechazado **cualquiera** de las dos sentencias —la sugerencia `WITH (UPDLOCK, HOLDLOCK)` incluida—, el guard valida **cada** sentencia del batch y la pasarela revierte **todo el batch** (`azure-apps/sigrid_api.md` §5 y §7.3): el `UPDATE` se habría ido con él y **el ERP habría quedado sin ningún cambio**. Cambió, luego el guard dejó pasar el batch **como está** |
| Si no: ¿qué rechazó, literalmente? | **no procede**: no hubo rechazo. De las cinco llamadas del circuito, las cinco respondieron `200` y **no hay ni un `502`** |
| ¿se cayó a la variante sin sugerencias, o se marcó `blocked`? | **no**: no hizo falta. La variante de reserva de §0.3 sigue **sin usarse nunca** |
| ¿el ERP quedó intacto tras el rechazo? | **no procede** |
| **T26 queda marcada** | **SÍ**, y es la única del bloque. **Con la salvedad escrita, que no se esconde**: `filas_afectadas` no se anotó, así que del `INSERT` en `dbo.log` **no hay observación directa** —se deduce de que el `UPDATE` sí se aplicó y de que un rechazo habría revertido el batch entero—, y **la fila de log nadie la ha mirado** (paso 7 de T24). Lo que esta tarea pregunta —si el guard deja pasar el batch tal cual, que era lo que «nadie había probado» (§0.3)— **queda respondido que sí**. *Acta del 2026-09-14* |

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

**Casilla de resultado · T27** — *rellenada el 2026-09-14. **No se ejecutó**, y
hay una evidencia parecida que **no vale** — ver la última fila y §9.6.*

| Campo | Valor |
|---|---|
| Fecha y hora | **NO EJECUTADA.** El circuito se recorrió **una sola vez** y no se repitió sobre la misma incidencia |
| 1 · `MAX(ide)` antes del reintento | **no anotado** |
| 2 · HTTP, `estado` y `filas_afectadas` | **NO EJECUTADO.** No consta ninguna llamada a `/api/cerrar` con `commit` sobre una reclamación ya cerrada |
| 3 · `MAX(ide)` después — ¿ha subido? | **no comprobado** |
| 4 · traza local — ¿sigue en `cerrado` con la fecha de T24? | **no comprobado** |
| **T27 queda marcada** | **no.** Es **el mismo hueco** que dejaron abierto las otras dos features: T30 del bloque 9 de F-012 —sin marcar, y descrito allí como «el escenario **más probable de todos en uso normal**» y «el hueco **más barato** de cerrar de los cinco»— y T22 de F-025, también sin marcar. **Y hay un dato que NO se puede usar como evidencia aquí**: en la prueba de F-025 del 2026-09-11 los registros muestran `archivar` y `adjuntar` y **ninguna llamada a `cerrar`**, sin que se aclarara si fue la idempotencia funcionando o si el circuito se detuvo (`specs/F-025-confirmacion-unica/tasks.md`, «Cierre del bloque 5»; el responsable aprobó sin responder a esa pregunta). **Una llamada que no consta no verifica un reintento**: aunque hubiera sido la reclamación ya cerrada y el front se saltara el paso, eso probaría una guarda del **front**, no el `ya_cerrada` del **backend** que R18 y R42 exigen. *Acta del 2026-09-14* |

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

4. ~~**Marcar en `specs/F-009-cierre-sigrid/tasks.md`** las tareas que hayan
   pasado. Lo hace el humano.~~
   > *(**2026-09-14**: las marcó el arnés **levantando acta de lo que el
   > responsable ejecutó** el 2026-09-11 dentro de F-012, y **solo la que
   > consta ejecutada** —T26—. Mismo criterio que se siguió en
   > `guion_bloque9_F-012.md`. Lo que no consta sigue sin marcar, y el
   > veredicto está en §9.5.)*

5. **Actualizar `azure-apps/postventa_incidencias.md`**: hoy dice que «todavía
   no se ha ejecutado ni un cierre real». Si T24 pasa, deja de ser verdad, y la
   regla de propiedad de `CLAUDE.md` obliga a actualizarlo **en este mismo
   trabajo**. Commit local allí, sin push.
   > *(**2026-09-14**: **ya dejó de ser verdad** el 2026-09-11 —el cierre de
   > `08:28:12` UTC, y además **con su gráfico dentro**—, y el documento **sigue
   > sin actualizar**. Lo anotó ya el paso 8 de T32 de `guion_bloque9_F-012.md`
   > como pendiente. Queda **fuera del alcance** del acta de §9, que no toca
   > otros repositorios, y recogido en su §9.5 punto 5.)*

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
| **H1** | **RESUELTO** (`82fbfb8`, 2026-09-03) **y corregido el mismo día** (`bed95ea`). El entorno desplegado no tenía ninguna configuración de Sigrid: ni secretos en el Key Vault, ni las App Settings `SIGRID_*`. T22 habría respondido `503 ConfiguracionSigridIncompleta` | `infra/00_vars_postventa.ps1` (`$PostventaSecretosBackend`, `$PostventaAppSettingsSecretas`), `infra/desplegar_backend.ps1` (`$ajustes`) | Hecho: **dos** secretos nuevos (`sigrid-api-base-url`, `sigrid-api-key`) con sus referencias, y **seis** planas a `$ajustes`. El primer arreglo puso **tres** secretos: `sigrid-base-datos` bajó a App Setting plana en `bed95ea`, porque el nombre de la base del ERP ya está escrito en documentos versionados y el secreto no protegía nada que no estuviera ya, a cambio de un aprovisionamiento manual más. El cotejo destapó dos variables más de las tres previstas: `SIGRID_ZONA_HORARIA` —la que decide el huso de `dbo.log`— y `SIGRID_TIP_RECLAMACION`. Queda a mano solo subir los dos valores al vault: ver §1 |
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

---

## 9 · Acta del 2026-09-14 · lo que este bloque tiene de hecho ejecutado

> **Quién levanta esta acta y con qué.** La levanta el arnés **sin ejecutar
> nada**: ni contra Sigrid, ni contra `sigrid-api`, ni contra Azure, ni contra
> el PostgreSQL compartido, ni contra SharePoint. Toda la evidencia estaba ya
> escrita. Las fuentes, por orden de peso: `progress/guion_bloque9_F-012.md`
> §9 (el acta del 2026-09-11, con las mediciones de `appi-postventa-dev`) y sus
> casillas de T25–T32; las entradas de **F-012** y **F-025** de
> `progress/history.md`; y el cierre del bloque 5 de
> `specs/F-025-confirmacion-unica/tasks.md`.

### 9.1 · Qué se ejecutó de hecho, y dónde consta

El **2026-09-11**, verificando **F-012**, el responsable del proyecto recorrió
el circuito completo contra el ERP de producción sobre la incidencia
**`RS26.09/0150`** de la obra **`0626`** —una obra **en uso**, con autorización
expresa—. Un parte subido por la web quedó **archivado**, **adjunto a su
reclamación** y **la reclamación cerrada**.

**Eso es el cierre real de T24 de este guion.** Ocurrió dentro de la
verificación de otra feature, y por eso este bloque nunca se «abrió»: no hubo
foto de partida, no se lanzó ninguno de los cinco scripts de lectura de §3 y no
se rellenó ninguna casilla — hasta hoy.

### 9.2 · La evidencia objetiva

Medida en `appi-postventa-dev` y volcada en `guion_bloque9_F-012.md` §9.2.
**Las cinco respuestas fueron `200`**:

| Hora (UTC) | Ruta | Código | Duración | Qué es **para F-009** |
|---|---|---|---|---|
| `08:27:15` | `archivar` | 200 | 1.756 ms | la precondición **P5** (parte archivado) |
| `08:27:29` | `adjuntar` | 200 | 13.134 ms | precondición de F-012, no de este bloque |
| `08:27:42` | `cerrar` | **200** | 4.424 ms | **el dry-run de T22**, con el gráfico aún sin adjuntar |
| `08:28:03` | `adjuntar` | 200 | 8.471 ms | la precondición añadida de **T24** (R2 de F-012) |
| `08:28:12` | `cerrar` | **200** | 472 ms | **el cierre real de T24**, y con él **T26** |

Y una comprobación que ningún registro da: **el responsable abrió la ficha en
Sigrid y vio la reclamación cerrada con su parte dentro** («ha funcionado
perfectamente», «cerró una y lo hizo bien»). Es lo que acredita el `CER` del
paso 6 de T24 y, con él, que el guard aceptó el batch (T26).

### 9.3 · Tarea por tarea

| Tarea | ¿Marcada? | Qué consta | De dónde sale |
|---|---|---|---|
| **T22** · dry-run real | **no** | el dry-run del cierre **funciona** contra el ERP (`200`, 4,4 s) y **no exige el gráfico** (R50 de F-012). **Nada de su contenido** (R9) y **nada de que no escriba** | §9.2; casillas de T25 y T26 de `guion_bloque9_F-012.md` |
| **T23** · siembra del login | **no** | solo lo **indirecto**: el `commit` escribió, y R31 aborta sin tocar Sigrid si el ERP no confirma el login | inferencia sobre §9.2; ninguna casilla del bloque 9 la cubre |
| **T24** · primer cierre real | **no** | **el cierre ocurrió y salió bien**, con autorización y con el parte adjuntado 9 s antes. **Faltan los pasos 5, 7 y 9** y media parte del 6 | §9.1 y §9.2; casilla de T29 de `guion_bloque9_F-012.md` |
| **T25** · el `tex` propio | **no** | nada: no se lanzó el script | §9.4 del bloque 9 («ninguna de las comprobaciones con los scripts de `infra/` se ejecutó») |
| **T26** · el guard acepta el batch | **SÍ** | `200` + la reclamación **en `CER`** ⇒ el guard dejó pasar las dos sentencias tal cual, `WITH (UPDLOCK, HOLDLOCK)` incluida | §9.2 + §9.1 del bloque 9, y `sigrid_api.md` §5 y §7.3 para la reversión del batch |
| **T27** · reintento sobre lo ya cerrado | **no** | nada. Y lo de F-025 **no sirve** (§9.6) | casilla de T30 del bloque 9; `specs/F-025-confirmacion-unica/tasks.md` |

### 9.4 · Qué queda sin verificar, y qué cuesta cada hueco

Ordenado por lo que cuesta cerrarlo, que es lo que el líder necesita para
decidir:

| # | Hueco | Qué se pierde | Coste de cerrarlo |
|---|---|---|---|
| 1 · **CERRADO 2026-09-15** | **La fila de `dbo.log` del primer cierre real, campo a campo, y su HUSO** (T24.7) | R24 y R25 enteros, y **el defecto que §0.2 daba por probable**: si `fec`/`hor` se escribió en UTC, nuestras filas quedan con una o dos horas menos que todas las demás del ERP y nadie lo nota hasta que haga falta reconstruir cuándo se cerró algo. **La fila está escrita en producción y nadie la ha mirado** | **Solo lectura, sin ventana de escritura.** `11_trazabilidad_tex_sigrid.ps1` localiza la fila por el `tex` propio y `10_log_cierre_sigrid.ps1` la verifica campo a campo y dice el huso. **Es el hueco más valioso y de los más baratos** |
| 2 · **CERRADO 2026-09-15** | **T25 entera** · el `tex` propio en los informes de Posventa | la mitad de D1 de `design.md`: que seguimos apareciendo en el filtro por prefijo, y que el filtro exacto devuelve **solo** lo nuestro | **Solo lectura.** Dos consultas, un script. Se hace en la misma sesión que el hueco 1 |
| 3 · **CERRADO 2026-09-15** | **La traza local del cierre** (T24.9) · R41, R43 | que la traza quedó en `cerrado`, con el `oid` y **sin el login** del ERP | **Solo lectura, y del esquema propio** (`12_traza_cierre_local.ps1`). Ni toca Sigrid |
| 4 · **REDUCIDO 2026-09-15** | **T23** · la siembra del login | R30–R34: que el candidato existe exactamente una vez, que la fila quedó `verificada`, y que **un login inexistente se rechaza sin escribir** | **Casi todo es solo lectura** (`07_alta_usuario_sigrid.ps1 -VerificarAhora` hace un `COUNT(*)`; `12_` lee el esquema propio). Solo el «segundo dry-run devuelve el mismo login» exige la ventana abierta |
| 5 | **T22 pasos 2 y 5** · el `503` con el interruptor apagado, y que el dry-run **no escribe** | la doble puerta de §0.1 observada en el borde —que es además el paso 3 de T32 de F-012, su «único resto abierto»— y la prueba de que un dry-run no mueve nada | el `503` **no escribe nada**: una llamada desde el front con la ventana cerrada, que es como está ahora. Lo de «no escribe» exige foto antes/después con la ventana abierta |
| 6 | **T22 paso 4** · las seis cosas de R9 y el bloque `grafico` con `estado: adjuntado` | el contenido del dry-run, que es lo que la persona lee antes de confirmar; y que R48 derogó de verdad el aviso de R21 | exige la **ventana abierta** y una sesión en el front, pero **no escribe**: es un dry-run |
| 7 | **T27** · el reintento sobre lo ya cerrado | R18 y R42: que repetir sale `ya_cerrada`, **sin escribir** y **sin pisar** la traza terminal. Es **el escenario más probable en uso normal** —alguien vuelve a pasar el mismo parte— y el único hueco de los ocho que **exige abrir la ventana de escritura** | ventana abierta + un `commit` sobre `RS26.09/0150`, que ya está cerrada. No hay que provocar ningún fallo. Es el mismo hueco que T30 de F-012 y T22 de F-025 |
| 8 | **`filas_afectadas: 2`** (R22, T24.5) | la única prueba directa de que el batch afectó a **dos** filas y no a una | **no es recuperable hacia atrás**: solo lo dará el siguiente cierre real. Igual que el `MAX(ide)` de partida, que nadie anotó |

> **Actualización del 2026-09-15 · quedan cinco huecos, no ocho.** La tabla de
> arriba **no se toca ni se borra** —era el estado del 2026-09-14 y así se
> queda—; solo se marca en la primera columna qué ha pasado con cada hueco. El
> detalle está en el **§10**.
>
> - **Huecos 1, 2 y 3: CERRADOS.** Se hizo la sesión de solo lectura que
>   recomendaba la opción (a) del §9.5 —`09`, `10`, `11` y `12`, **sin abrir la
>   ventana de escritura**— y **los cuatro scripts dan `PASA`**. Con ellos
>   quedan acreditados **T25 entera** y los **pasos 6, 7 y 9 de T24**, es decir
>   **R24, R25, R41 y R43**. El más valioso de los tres, el huso de `fec`/`hor`:
>   **`HORA LOCAL (correcto)`, 0,0 min de diferencia**. **El defecto que §0.2
>   daba por probable no existía.**
> - **Hueco 4: REDUCIDO, no cerrado.** Hoy se ha visto que el `usu` escrito en
>   el ERP es **`pgris`**, lo que prueba que el login **se derivó, se resolvió
>   contra el ERP y se usó para firmar** la fila de auditoría (R30–R32 en lo
>   sustantivo). **Lo que sigue abierto es R33** —que la correspondencia quedara
>   guardada como **confirmada**, con `verificado_at_utc` relleno—, **R31** —que
>   un login inexistente responda `409` nombrando correo y login intentado, sin
>   tocar Sigrid— y **R34**, más que el candidato exista **exactamente una vez**
>   en `dbo.usu`. Nada de eso lo prueba una firma correcta. Ver §10.5.
> - **Huecos 5, 6, 7 y 8: exactamente como estaban.** Ninguno se ha tocado. Los
>   tres primeros siguen exigiendo la **ventana abierta**; el 8
>   (`filas_afectadas: 2`, R22, y el `tiemod` de partida) **sigue sin ser
>   recuperable hacia atrás**: solo lo dará el siguiente cierre real.
>
> **Aviso para quien recorra el hueco 4**: `infra/07_alta_usuario_sigrid.ps1`
> (líneas 161 y 248) arrastra el mismo defecto de comillas que hoy tumbó al
> `12`, y **nunca se ha ejecutado**. Se estrellará en la primera línea de T23.
> El arreglo ya está escrito: `Invoke-PythonDelServicio`, en el común. Ver
> §10.6.

### 9.5 · **Veredicto** (lo que el líder necesita para decidir)

> **Nota del 2026-09-15.** Este veredicto es el del 2026-09-14 y se deja
> entero. **Lo que recomendaba su punto 4(a) —hacer antes los huecos 1, 2 y 3,
> por ser solo lectura y sin riesgo— ya se ha hecho, y los tres pasan**: ver
> §9.4 (actualización) y **§10**. La decisión de fondo —cerrar F-009 con los
> huecos restantes escritos, o no— **sigue siendo del responsable** y sigue
> pendiente; lo que ha cambiado es que ahora son **cinco** huecos y **ninguno**
> de ellos es el de la fila de auditoría.

**Sí queda algo sustantivo sin verificar de F-009.** En una línea: *el cierre
real está acreditado; sus comprobaciones, casi ninguna*.

1. **Lo que F-009 existe para hacer, está hecho y visto**: una reclamación real
   pasó a `CER` en el ERP de producción, escrita por el servicio desplegado,
   con autorización expresa y con su parte dentro. Lo comprobó una persona en
   la ficha de Sigrid. **Y con F-012 delante, el riesgo aceptado de
   `design.md` §2 —cerrar sin gráfico— no llegó a materializarse ni una vez.**
2. **Lo que no está**: de los nueve pasos de T24 solo constan uno y medio.
   Ninguno de los **cinco scripts de lectura de §3 se ha ejecutado jamás**, y
   por eso **la fila de auditoría del primer cierre de este servicio en el ERP
   nadie la ha mirado** — incluido su **huso**, que este mismo guion daba por
   defecto probable. **Ese es el hueco que no debería sobrevivir al cierre de
   la feature**, y cuesta una sesión de **solo lectura**.
3. **Marcar el bloque 8 como superado sería falso.** Solo **T26** está
   acreditada. T22, T23, T24, T25 y T27 **no**.
4. **Recomendación al líder, con las opciones separadas**:
   - **(a) Cerrar F-009 como se cerró F-012** —con los huecos escritos y
     fechados, decisión del responsable—: es coherente con el precedente del
     2026-09-11, pero entonces conviene **hacer antes los huecos 1, 2 y 3 de
     §9.4**, porque son **solo lectura, sin ventana de escritura, sin riesgo**,
     y uno de ellos persigue un defecto que el diseño consideraba probable.
   - **(b) Cerrar F-009 tal cual**: entonces queda escrito aquí que **nadie ha
     mirado la fila de auditoría**, y que T27 —el reintento, el escenario más
     probable en uso normal— **no lo ha probado nadie en ninguna de las tres
     features** que pasaron por delante (F-009, F-012 y F-025 lo dejaron sin
     marcar, cada una por su lado).
   - **La decisión es del responsable**, no del arnés. Lo que el arnés puede
     decir está en §9.4: **siete de los ocho huecos no exigen escribir en el
     ERP, y tres no exigen ni abrir la ventana**.
5. **Pendiente documental que no depende de esa decisión**:
   `azure-apps/postventa_incidencias.md` **sigue diciendo que «todavía no se ha
   ejecutado ni un cierre real»**, y desde el 2026-09-11 eso es falso. Lo
   arrastran el paso 5 de §6 de este guion y el paso 8 de T32 de F-012, que lo
   dejó anotado como pendiente. La regla de propiedad de `CLAUDE.md` obliga a
   actualizarlo.

### 9.6 · Lo que **no** se ha usado como evidencia, y por qué

- **La prueba de F-025 del 2026-09-11 no acredita T27.** Sus registros muestran
  `archivar` (2,0 s) y `adjuntar` (3,8 s) y **ninguna llamada a `cerrar`**.
  Caben dos lecturas —la reclamación ya estaba cerrada y el circuito se saltó
  el paso, o el circuito se detuvo— y **se preguntó al responsable, que aprobó
  el cierre sin responder**. Una llamada que no consta no prueba un reintento;
  y de la primera lectura, la buena, lo que se seguiría es que el **front** se
  saltó el paso, no que el **backend** respondiera `ya_cerrada`, que es lo que
  R18 y R42 exigen. Queda **sin usar**, a propósito.
- **Los tests unitarios no cuentan aquí.** Todo el bloque 8 existe porque hay
  cosas que un mock no puede probar (§T24). Que R2, R18, R22, R31 o el huso
  tengan test no los convierte en verificados contra el ERP.
- **Las inferencias van marcadas como tales.** En T22 (el login) y en T23 se
  dice «indirecto» y se deja sin marcar. La **única** inferencia que sí sostiene
  una marca es la de T26, y su cadena está escrita entera en su casilla para que
  el reviewer pueda romperla si no la comparte.

---

## 10 · Acta del 2026-09-15 · la sesión de solo lectura (huecos 1, 2 y 3)

> **Qué se ejecutó, y qué NO.** Se ejecutó la **sesión de solo lectura** que
> recomendaba la opción (a) del §9.5 para cerrar los huecos 1, 2 y 3 de §9.4.
> Se lanzaron cuatro de los cinco scripts de lectura de §3 —`09`, `10`, `11` y
> `12`; el `08` es el común y lo cargan los demás— contra el ERP de producción
> y contra el esquema propio de PostgreSQL. **Los cuatro dan `PASA`.**
>
> **No se escribió nada.** La única ruta del ERP que se tocó fue
> `POST /api/sql/read`, y la **ventana de escritura (`CIERRE_HABILITADO`)
> siguió cerrada todo el tiempo**: no hubo ninguna llamada a `POST /api/cerrar`
> ni con `commit` ni sin él. En PostgreSQL, solo lectura y solo del esquema
> propio.
>
> Esta acta la levanta el arnés **sin ejecutar nada**: las cifras de abajo las
> produjo esa sesión, delante del ERP, y aquí se transcriben.

### 10.1 · Con qué se ejecutó

Desde el puesto del responsable, con un **envoltorio fuera del repositorio**
(`C:\Users\pgris\lectura_cierre_f009.ps1`, **no versionado**) que solo carga
las variables del `.env` y llama a los scripts de `infra/`. Queda fuera a
propósito: lleva el destino y el manejo de la clave, y la regla de `CLAUDE.md`
sobre secretos manda sobre la comodidad de tenerlo versionado. Los scripts que
hacen el trabajo sí están en el repositorio y son los de §3.

### 10.2 · Lo primero que se aprendió: los rotos eran los scripts, no el ERP

**Los cinco scripts de lectura se escribieron el 2026-09-05 y no se había
lanzado ninguno.** Hoy se han lanzado cuatro y **tres estaban rotos**. Los tres
fallos eran de los scripts; **ninguno era del ERP**, y ninguno se habría
descubierto sin ejecutarlos.

Están arreglados y confirmados en el commit **`a356875`** («F-009: tres
defectos de los scripts de lectura, hallados al ejecutarlos»), cuyo mensaje
lleva el detalle. En una línea cada uno:

1. **`10_log_cierre_sigrid.ps1`** juzgaba el huso comparando la fila contra
   **AHORA**, con 20 minutos de tolerancia: leído el cierre cuatro días después,
   el veredicto habría salido `NO COINCIDE CON NINGUNA` **por construcción**.
   Nuevo parámetro `-InstanteCierreUtc`, opcional.
2. **`11_trazabilidad_tex_sigrid.ps1`** preguntaba la igualdad exacta con
   `tex = ?` y `dbo.log.tex` está declarada `text`, tipo LOB sobre el que SQL
   Server **no admite `=`**: devolvía `500` en dos décimas, que parece un
   problema de red o de clave. Ahora pregunta con `LIKE` y patrón literal, y
   **rechaza** un texto propio que lleve comodines.
3. **`12_traza_cierre_local.ps1`** pasaba el guion de Python con `& $python -c`
   y PowerShell 5.1 se come las comillas dobles al invocar un ejecutable nativo.
   Arreglado con `Invoke-PythonDelServicio`, en el común
   `08_lectura_sigrid_comun.ps1`.

**El cuarto script, `09_estado_reclamacion_sigrid.ps1`, salió a la primera.**

> **Lo que esto dice del bloque 8, y conviene no perder.** Un guion de
> verificación con utillaje **escrito y nunca ejecutado** no es utillaje, es una
> intención. El §3 de este guion lleva desde el 2026-09-05 describiendo cinco
> scripts «re-ejecutables, que comprueban sus precondiciones y paran con un
> mensaje claro en vez de reventar», y tres de los cuatro que se han probado
> reventaban. **El defecto 1 es el peor de los tres**: no reventaba —respondía,
> y respondía mal, que es lo único que un veredicto automático no se puede
> permitir.

### 10.3 · Lo medido, script a script

Los cuatro veredictos, **literales**.

#### `11_trazabilidad_tex_sigrid.ps1` — `TRAZABILIDAD DEL TEXTO PROPIO : PASA`

- Filas de la incidencia que encuentra el **filtro por prefijo**
  `tex LIKE 'Cerrar parte%'` —el de los informes de Posventa, el que mide sobre
  6.843 filas—: **una sola**
  → `8457839 | 20260911 | 102812 | pgris | Cerrar parte (postventa-incidencias)`.
- Todas las filas del ERP con el **texto propio exacto**, sobre `dbo.log`
  entera: **una sola**
  → `8457839 | 20260911 | 102812 | pgris | con | 708 | RS26.09/0150`.
- Comprobaciones: «el prefijo del ERP encuentra nuestro cierre» **True/True**;
  «cierres de este servicio en todo el ERP» esperado **1**, obtenido **1**; «el
  filtro exacto no devuelve más de lo listado» **1/1**.

**Qué acredita: T25 entera**, es decir **las dos** condiciones de D1 de
`design.md` — que seguimos saliendo en los informes de Posventa por el filtro
de prefijo, y que el filtro exacto devuelve **solo lo nuestro**, ninguno de los
6.843 cierres manuales. Y de paso **localiza la fila de log del cierre**
(`ide` 8457839), que es justo lo que le faltaba al paso 7 de T24.

#### `09_estado_reclamacion_sigrid.ps1` — `ESTADO DE LA RECLAMACION : PASA`

- `ide` de la reclamación **2833896**; `emp` **1**; `cod` **`RS26.09/0150`**;
  `res` **«fuga en caldera»**; `est` actual **9 = `CER / CERRADA`**; `est` de
  destino resuelto contra `conest` **9 = `CER / CERRADA`**; `con.tiemod`
  **46275.647118**.
- `MAX(ide)` de `dbo.log`: **8466095** en la primera pasada y **8466171** en la
  segunda. El ERP sigue vivo: son cierres de otros, hechos entre una lectura y
  la siguiente.
- Comprobación: «código del estado actual» esperado `CER`, obtenido **`CER`**.

**Qué acredita: el paso 6 de T24**, que hasta hoy constaba **solo por lo que
vio una persona en la ficha de Sigrid**. Ahora está leído del ERP, con el
estado de destino resuelto contra `conest`, que es lo que R1 pide.

#### `10_log_cierre_sigrid.ps1` — `FILA DE AUDITORIA DEL CIERRE : PASA`

Lanzado con `-IdeFilaLog 8457839` (es decir, `-DesdeIde 8457838`),
`-Res "fuga en caldera"`, `-Emp 1` y `-InstanteCierreUtc 2026-09-11T08:28:12Z`
—el parámetro nuevo del arreglo 1—.

- **El huso**: lo escrito en el ERP es **`2026-09-11 10:28:12`**
  (`fec = 20260911`, `hor = 102812`). Hora **local** de referencia
  `2026-09-11 10:28:12` → **diferencia 0,0 min**. Hora **UTC** de referencia
  `2026-09-11 08:28:12` → diferencia 120,0 min. Veredicto:
  **`HORA LOCAL (correcto)`**.
- **Campo a campo**, los once del §7.3 de `design.md`, todos en verde:
  `ide` **8457839**; filas nuevas **1/1**; `tab` **con**; `tip` **708**; `cod`
  **`RS26.09/0150`**; `ope` **5**; `est` **1**; `ori` **0**; `emp` **1**; `usu`
  **`pgris`**; `tex` **«Cerrar parte (postventa-incidencias)»**; `res`
  **«fuga en caldera»**.

**Qué acredita: el paso 7 de T24, y con él R24 y R25 enteros.** Y **mata el
defecto que el §0.2 daba por probable: no escribimos en UTC.** Era *la única
decisión de la feature que no se pudo tomar con un dato*
(`progress/impl_F-009.md` §3.3.a); ahora lo tiene. Nuestra fila queda a la
misma hora que las 8,4 millones que la rodean, y reconstruir cuándo se cerró
algo seguirá saliendo bien.

#### `12_traza_cierre_local.ps1` — `TRAZA LOCAL DEL CIERRE : PASA`

- Trazas para esta incidencia **1/1**; estado de origen guardado **`PTE`**;
  estado de destino guardado **`CER`**; motivo **«(sin motivo)»**; **intentos
  2**; estado de la traza esperado `cerrado`, obtenido **`cerrado`**; marca de
  tiempo del dry-run **sí**; marca de tiempo del cierre **sí**; «oid de quien
  confirmó (R41)» **sí**; «el login del ERP NO está en la traza (R43)» esperado
  **no**, obtenido **no**.
- **Los `intentos 2` cuadran con lo medido en §9.2**: las dos llamadas a
  `cerrar` del 2026-09-11, el dry-run de `08:27:42` y el `commit` de `08:28:12`.
  Es una confirmación cruzada entre dos fuentes independientes —los registros de
  `appi-postventa-dev` y la traza de PostgreSQL— que nadie había buscado.

**Qué acredita: el paso 9 de T24, y con él R41 y R43.**

> **Salvedad, y es la que impide dar el hueco 4 por cerrado.** **NO se pasó
> `-UsuarioOid`**, así que lo comprobado es que la traza **guarda un oid**, no
> **cuál**. Y sobre todo: **R33 —que la correspondencia del usuario quedó
> marcada como CONFIRMADA, con `verificado_at_utc` relleno— sigue sin
> comprobar**. Es parte del hueco 4 (T23), que queda **reducido**, no cerrado.

### 10.4 · Qué NO prueba esta sesión

Se escribe aparte para que no se lea de más:

- **No prueba nada de T22, T23 ni T27.** Ninguna de las tres se ha tocado hoy.
- **No prueba `filas_afectadas: 2`** (R22, hueco 8). Sigue sin ser recuperable
  hacia atrás: lo dará el siguiente cierre real, no una lectura.
- **No prueba que `tiemod` no se moviera.** Hoy vale **46275.647118**, pero
  **nadie anotó el de partida** antes del cierre, así que el número de hoy no
  compara con nada. Queda dentro del hueco 8, por el mismo motivo que el
  `MAX(ide)`: la foto que faltaba era la de **antes**.
- **No prueba R33**, ni que un login inexistente se rechace sin tocar Sigrid
  (R31). Ver §10.5.
- **No abre ninguna ventana.** Todo lo que exija `CIERRE_HABILITADO` en `true`
  —los huecos 5, 6 y 7— sigue exactamente donde estaba.

### 10.5 · Lo que sí se aprendió del usuario, sin haberlo buscado

El `usu` escrito en el ERP es **`pgris`**. Eso prueba tres eslabones de la
cadena R30–R32: que el **login candidato se derivó**, que **se resolvió a un
login real** —el ERP lo aceptó como firma de la fila de auditoría— y que **se
usó para firmar**, no el correo ni el `oid`.

**Lo que NO prueba**: ni **R33** (que la correspondencia quedara guardada como
**confirmada**, con `verificado_at_utc` relleno), ni **R31** (que un login
inexistente responda `409` nombrando correo y login intentado, **sin tocar
Sigrid**), ni que el candidato exista **exactamente una vez** en `dbo.usu`.

Por eso el hueco 4 queda **reducido**, y por eso sigue abierto.

### 10.6 · Pendiente que esta sesión deja abierto, con dueño

El defecto 3 del §10.2 —`& $python -c` y las comillas de PowerShell 5.1—
**sigue vivo en dos scripts que tampoco se han ejecutado nunca**:

| Script | Dónde | Quién lo tiene que arreglar |
|---|---|---|
| `infra/07_alta_usuario_sigrid.ps1` | líneas **161** y **248** | **el encargo que cierre el hueco 4 (T23)**: ese script es el que hace el `COUNT(*)` de `-VerificarAhora`, así que se estrellará en la primera línea del guion de T23 |
| `infra/17_traza_grafico_local.ps1` | línea **196** | **el encargo que recorra la precondición añadida de T24** (R2 de F-012), que es donde se invoca |

El arreglo está escrito y probado: `Invoke-PythonDelServicio`, en
`infra/08_lectura_sigrid_comun.ps1`. **No se ha aplicado hoy a propósito**:
este encargo era documental, y arreglar un script que nadie va a ejecutar en la
misma sesión es volver a crear el problema del §10.2 —código escrito y nunca
probado— con otro nombre.

### 10.7 · Veredicto del 2026-09-15

1. **Los tres huecos baratos están cerrados, y los tres pasan.** De los **nueve
   pasos** de T24, los que constan suben de «uno y medio» a **cuatro y medio**:
   el **4** (parcial), el **6**, el **7** y el **9**. **T25 queda entera.**
2. **El defecto que el diseño daba por probable no existía.** El huso es
   **local**, con 0,0 minutos de diferencia. `design.md` §7.3 no decía en qué
   huso se escribe `fec`/`hor`; ahora lo respalda un dato del ERP y no solo una
   elección razonada.
3. **El defecto que sí ha aparecido estaba en nuestra casa**: tres de los cuatro
   scripts de lectura no funcionaban. Es el argumento más fuerte que ha dado
   este bloque a favor de **ejecutar** el utillaje de verificación en vez de
   darlo por bueno porque está escrito.
4. **T24 sigue sin marcar, y no por poco**: le faltan los pasos **2, 3, 4, 5 y
   8**, y el `filas_afectadas` **no es recuperable**. **T22, T23 y T27 tampoco
   se marcan.** Del bloque 8 quedan marcadas **T25** y **T26**.
5. **El pendiente documental del §9.5.5 sigue en pie y no depende de esta
   sesión**: `azure-apps/postventa_incidencias.md` **sigue diciendo que «todavía
   no se ha ejecutado ni un cierre real»**, y desde el 2026-09-11 es falso. Hoy
   además hay con qué corregirlo bien: fecha, incidencia, `ide` de la fila de
   auditoría y veredicto del huso. **Lo decide el líder**, no este encargo.
