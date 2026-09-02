<!-- progress/spec_F-009.md -->
# F-009 · Cierre de la incidencia en Sigrid (solo estado) — informe del spec-author

Rama `feature/F-009-cierre-sigrid`. Rigor `critico`, SDD sí.
Informe escrito de forma incremental. NO se ha implementado código.

## 0 · Protocolo

- `bash harness/init.sh` en verde (arnés v1.5.2, 17 tests, rama correcta,
  puerta de cobertura N/A porque la spec no cambia líneas de producción).
- Leído: `specs/SPECS.md`, ficha F-009 de `BACKLOG.md`,
  `docs/referencia/03_modelo_posventa_sigrid.md` (entregable de F-008),
  `progress/impl_F-008.md`, `progress/impl_postreview_F-008.md`,
  `azure-apps/sigrid_api.md` (§4, §5, §7, §8, §9), `azure-apps/sigrid_tablas.md`
  (solo lo consultado), `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
  `docs/INTEGRACION.md`.

## 1 · Bitácora de la investigación

(se rellena según avanza)

### D3 · ¿Con qué prefijos está habilitada la escritura de `sigrid-api`? — RESUELTO

Comprobado el **2026-08-26** con una lectura de la configuración del recurso,
**sin escribir nada** y sin ver ningún secreto:

```bash
az functionapp config appsettings list -g rg-sigrid-dev-data-api \
  -n func-sigridapi-dev-huyke \
  --query "[?contains(name,'ALLOWED_WRITE') || contains(name,'DOMAIN_WRITE') || contains(name,'REQUIRE_WHERE') || contains(name,'MAX_AFFECTED') || contains(name,'MAX_STATEMENTS')].{clave:name, valor:value}" -o json
```

| Qué se preguntó | Respuesta |
|---|---|
| ¿`INSERT` permitido? | **Sí** |
| ¿`UPDATE` permitido? | **Sí** |
| ¿`DELETE` permitido? | Sí (F-009 no lo usa) |
| ¿La base `ruesma` en la lista blanca de escritura? | **Sí**, y es la única |
| ¿Credenciales de escritura configuradas? | Sí, la contraseña por **referencia a Key Vault** (no se ha visto su valor y no entra en la spec) |
| `REQUIRE_WHERE_ON_UPDATE_DELETE` | `true` → el `UPDATE` **tiene** que llevar `WHERE` |
| `MAX_AFFECTED_ROWS` / por defecto | 1.000 / 200 |
| `MAX_STATEMENTS_PER_BATCH` | 50 |
| `SIGRID_DOMAIN_WRITE_ENABLED` | `true` (no aplica: F-009 no usa endpoints de dominio) |

**Consecuencia para el diseño**: `Settings.write_enabled` de la pasarela es
verdadero, y las dos sentencias que F-009 necesita —el `UPDATE` de `con.est` y
el `INSERT` en `dbo.log`— **caben en `POST /api/sql/write` tal y como está
desplegado hoy**. F-009 **NO** exige tocar el repositorio `sigrid-api`.

### D1 · El `tex` de la fila de `dbo.log` — RESUELTO, con la medida delante

Dos cosas había que comprobar y las dos se comprobaron por lectura el
**2026-08-26**:

**1. La longitud del campo.** `sigrid_tablas.md` declara `log.tex` como «Texto
ilimitado», y `sys.columns` lo confirma: **`text`**, no un `varchar(N)`. **No hay
tope que respetar.** Para lo demás: `log.usu` es `varchar(48)`, `log.cod`
`varchar(24)`, `log.res` `varchar(128)` — y `con.res` es exactamente
`varchar(128)`, con un máximo real de 128 y **cero** filas por encima, así que la
copia de la descripción **no necesita truncarse**. `con.cod` mide como mucho 12.

**2. Que el ERP no escribe un texto uniforme.** Los `tex` reales de los procesos
sobre reclamaciones (`tip = 708`, `ope = 5`):

| `tex` | veces | longitud |
|---|---:|---:|
| `Pasar a pendiente` | 14.502 | 17 |
| `Proceso ejecutado (Pasar a terminada)` | 7.388 | 37 |
| **`Cerrar parte`** | **6.843** | 12 |
| `Proceso ejecutado (Cerrar Preventas)` | 4.899 | 36 |
| `Proceso ejecutado (Cerrar parte sin archivo (RPV))` | 2.701 | 50 |
| `Rechazar reclamación (envia email)` | 537 | 34 |
| `Proceso ejecutado (Rechazar reclamacion (NO enviar email))` | 215 | 58 |
| `Crear Reparaciones a Intervinientes` | 14 | 35 |
| `Proceso ejecutado (Pasar a pendiente)` | 2 | 37 |
| **`Proceso ejecutado (Cerrar parte)`** | **1** | 32 |
| `Proceso ejecutado (Rechazar reclamación (envia email))` | 1 | 54 |

Lo que esto zanja: **el propio ERP ya escribe dos textos distintos para «Cerrar
parte»** (`Cerrar parte`, 6.843 veces, y `Proceso ejecutado (Cerrar parte)`, una).
Nadie puede estar filtrando por igualdad estricta sin perderse ya una fila, y hay
textos de hasta 58 caracteres. Un texto propio no rompe ninguna uniformidad que
exista.

**Texto propuesto: `Cerrar parte (postventa-incidencias)`** — 36 caracteres.
Justificación:

- **Empieza por `Cerrar parte`**, así que el filtro por prefijo con el que F-008
  midió toda la población (`tex LIKE 'Cerrar parte%'`) **sigue encontrando
  nuestros cierres**: no desaparecemos de los informes existentes.
- **Nombra el servicio**, así que un cierre nuestro se distingue de uno manual de
  un vistazo y con un solo `LIKE` — que es exactamente lo que pide D1 y lo que
  hace falta si el piloto se tuerce y hay que revertir *solo* lo nuestro.
- **Cabe de sobra**: el campo es ilimitado y 36 está dentro del rango de
  longitudes que el ERP ya escribe (12–58).

### El resto de la fila de log, medido y homogéneo

Sobre las 6.843 filas de `tex = 'Cerrar parte'`: `emp = 1`, `ori = 0`, `est = 1`,
`tab = 'con'` en **todas**, sin una sola excepción. `log.cod` coincide con
`con.cod` en las 6.843; `log.res` coincide con `con.res` en 6.841 (las dos que no,
se explican porque la descripción se editó después del cierre: el log guarda la
del momento).

Aun así, **`emp` se toma de `con.emp` de la reclamación, no se cablea el 1**: hoy
todas las reclamaciones son de la empresa 1, pero eso es un dato de esta
instalación, igual que el `est = 9`.

### El `ide` de `dbo.log`: el hallazgo que cambia el diseño

**`log.ide` NO es IDENTITY** (`sys.columns.is_identity = false`) y es `NOT NULL`.
La tabla tiene 8.417.162 filas y `ide` va de 1 a 8.417.171, **todos distintos**:
es el `MAX(ide)+1` que describe `sigrid_api.md` §7.5, y ahí mismo avisa de que
**`sql/write` no protege esa reserva con applock**.

Lo que salva el diseño: `log_indide` es **índice único y clave primaria** sobre
`ide`. Así que una colisión no corrompe nada — **falla en seguro**: viola la clave
única, `sql/write` revierte **todo el batch** (§7.3) y el `UPDATE` de `con.est` se
va con ella. O las dos escrituras, o ninguna.

### El gráfico: el dato que obliga a preguntar al humano

F-008 §6.2 recomendó que F-009 **se niegue a cerrar una reclamación sin gráfico**,
como réplica del control del ERP, y lo llamó «una condición barata de verificar».
Barata de verificar lo es. Lo que no dijo —porque no se midió— es **con qué
frecuencia se cumple**. Medido ahora, sobre las reclamaciones creadas desde 2025:

| Estado | Reclamaciones | Con gráfico | Sin gráfico |
|---|---:|---:|---:|
| `SAT` | 90 | 1 | 89 |
| `PTE` | 839 | **11** | 828 |
| `TER` | 1.474 | **19** | 1.455 |
| `NPR` | 258 | 173 | 85 |
| `CER` | 2.105 | 2.102 | 3 |

**El 98,7 % de las reclamaciones abiertas no tiene gráfico.** El gráfico y el
cierre son **el mismo gesto** en el flujo manual: se sube y se cierra a
continuación (F-008 §4.2 lo tiene datado al minuto — gráfico a las 11:40:39,
cierre a las 11:46:33 del mismo día).

Consecuencia: una precondición dura de gráfico **deja a F-009 sin poder cerrar
casi nada**, salvo que alguien suba el PDF a Sigrid a mano justo antes. Eso no
invalida la recomendación de F-008 —sigue siendo lo correcto para la integridad
del ERP—, pero **cambia lo que cuesta**, y por eso va como decisión abierta al
humano con las tres salidas y su precio.

### D2 · El `usu`: resolver la identidad de Entra al login de Sigrid

Era «lo más abierto de la feature» y el primer trabajo. Se investigó por lectura
el **2026-08-26**. **Ninguna consulta trajo un nombre, un correo ni un login
concreto**: todo lo que sigue son recuentos agregados, y así entra en la spec.

**Sí hay tabla de usuarios en Sigrid.** Es **`dbo.usu`**, con `cod`
(`varchar(24)`, el login), `res` (nombre), `ele` (`varchar(200)`, correo), `sid`
(`varchar(255)`, SID de dominio), `dni` y `cla`. Hay dos tablas más: `dbo.usuemp`
(usuario × empresa, con `ele`, `usr` y `act`) y `dbo.sisusu`, que está **vacía**
(0 filas).

Y aquí se acaban las buenas noticias:

| Medida | Resultado |
|---|---|
| Usuarios en `dbo.usu` | **228**, con `cod` único y sin `@` ni espacios (máx. 17 caracteres) |
| De ellos, con correo (`usu.ele`) | **0** |
| De ellos, con SID de dominio (`usu.sid`) | **0** |
| Filas de `dbo.usuemp` | 1.261; con correo, **21** (8 usuarios distintos) |
| Dominio de esos correos | uno solo, el corporativo |
| Logins distintos que han cerrado partes de posventa desde 2025 | **3** |
| De esos 3, cuántos están en `dbo.usu` | **3** |
| De esos 3, cuántos tienen correo registrado | **2** |
| De los 8 usuarios con correo, cuántos cumplen `usu.cod` = parte local del correo | **6** |

**Veredicto: la identidad de Entra NO se puede resolver hoy de forma fiable y
automática.** Los dos caminos que existirían están rotos por los datos:

- **Por correo**: `usu.ele` está vacío en los 228 usuarios, y `usuemp.ele` cubre
  8 de 228. De los 3 que cierran partes de posventa, uno no tiene correo. No hay
  de dónde resolver.
- **Por convención** (`<parte local del UPN>` → `usu.cod`): se cumple en **6 de
  los 8** casos comprobables. Un 75 % no es una tasa aceptable cuando el error
  consiste en **firmar en el log de un ERP de producción el cierre de una
  persona que no lo hizo**.

**Mecanismo diseñado, que no improvisa**: mapeo **explícito** en la base propia
(`postventa.usuarios_sigrid`, `usuario_oid` → `login_sigrid`) más
**verificación obligatoria contra `dbo.usu`** antes de escribir. Sin fila de
mapeo no se cierra, y un login que no exista en el ERP no llega nunca al
`INSERT`. Con 3 personas en Posventa el coste de mantener el mapeo es de un alta
por persona. La convención se usa **solo** para sugerir el login en el mensaje de
error, jamás para resolver.

Queda como **decisión abierta** cuál de las tres vías quiere el humano (mapeo
explícito, poblar `usuemp.ele` con el administrador de Sigrid, o convención
verificada), con su coste en el `design.md`.

## 2 · Lo entregado

`specs/F-009-cierre-sigrid/` con los tres ficheros de `specs/SPECS.md`:

- **`requirements.md`** — 50 requisitos EARS (R1–R50) en 12 bloques. Cada uno se
  traduce a al menos un test trazable `test_f009_rN_*`. Los tres que solo se
  pueden verificar contra el ERP (R22/R26, R25, R30) están declarados como tales
  al final, con su motivo.
- **`design.md`** — el diseño, con las cuatro decisiones del humano resueltas y
  medidas, los ficheros exactos a crear/modificar/no tocar, las firmas por capa
  hexagonal, el SQL sentencia a sentencia y **§10 · Decisiones abiertas**.
- **`tasks.md`** — T0 a T29 en nueve bloques, cada una con su verificación. El
  bloque 8 entero es `MANUAL (humano)` contra el ERP desplegado, con el
  procedimiento paso a paso, al modo de la T24 de F-019.

### Lo que la spec NO hace, y consta por escrito

- **No sube el gráfico**: es F-012 (y es la única parte que exigiría tocar el
  repositorio `sigrid-api`).
- **No confirma el gráfico-URL**: es F-013 (D4 del humano).
  > Corregido el 2026-09-02: el gráfico-URL es **F-023**, dada de alta ese
  > día. F-013 es «mudar el archivo a la biblioteca de Posventa», otra cosa.
  > La frase de arriba se deja como se escribió; lo que manda es esta nota.
- **No toca `harness/features.json`**: el estado lo mueve el humano.
- **No exige ningún cambio en `sigrid-api`**, y eso está demostrado, no supuesto
  (D3).

### Lo que F-005 ya había dejado hecho y esta spec solo usa

`postventa.cierres` y `postventa.preferencias_usuario` **ya existen**, con
`EstadoCierre` (incluido `ya_cerrada`), `confirmado_por`,
`estado_origen_sigrid`/`estado_destino_sigrid`, la regla de terminalidad de
`cerrado` y el `auto_cierre` en falso por defecto. `guardar_cierre` está en el
puerto y en el repositorio. **No hay que cambiar ni una columna.** Lo único
nuevo en PostgreSQL es `08_usuarios_sigrid.sql`, el mapeo de D2.

## 3 · Decisiones abiertas que necesita validar el humano

Son **DOS**, las dos en `design.md` §10, y **ninguna impide que el resto de la
spec esté en pie**. Las dos hay que responderlas antes de implementar: es la
tarea **T0**.

### OD-1 · ¿Puede F-009 cerrar una reclamación sin gráfico en Sigrid?

Nace de un dato que F-008 no midió: **el 98,7 % de las reclamaciones abiertas no
tiene gráfico**, porque subirlo y cerrar son el mismo gesto. La precondición
dura que recomendó F-008 §6.2 es correcta para la integridad del ERP, pero
dejaría a F-009 sin poder cerrar casi nada. Tres salidas en el design, con su
coste; el diseño soporta las tres sin cambiar.

### OD-2 · ¿De dónde sale el login de Sigrid de quien confirma?

Ninguna vía automática es fiable hoy: `usu.ele` está vacío en los 228 usuarios,
`usuemp.ele` cubre 8, y la convención acierta 6 de 8. El diseño propone mapeo
explícito con verificación obligatoria contra `dbo.usu`; falta que el humano
elija vía y **diga quién entra en el mapeo** — con tres logins cerrando partes
hoy es una lista corta, y uno de ellos no tiene correo en el ERP, así que la
tiene que dar una persona, no una consulta.

## 4 · Ni una escritura

Toda la investigación fue `SELECT` a través de `POST /api/sql/read` y una
lectura de configuración de Azure. **No se ha escrito nada en Sigrid, ni desde
local ni desde ningún sitio**, y no se ha tocado código de producción.

Ningún login, correo ni nombre concreto entra en la spec ni en este informe:
todas las medidas de D2 son recuentos agregados. Ningún valor de configuración
de `sigrid-api` entra tampoco — solo el hecho de si el prefijo está permitido.

---

# 5 · Segunda pasada (2026-08-26): las dos decisiones abiertas, resueltas

> El humano resolvió OD-1 y OD-2. La spec se ha actualizado en los tres
> ficheros y **§10 del `design.md` ya no es «decisiones abiertas»**: es
> **«Decisiones cerradas (2026-08-26)»**, con las seis —D1 a D6— fechadas. No
> queda ninguna abierta. Sigue sin implementarse código y sin tocarse
> `harness/features.json`.

## 5.1 · OD-1 → **D5 · el orden es validar → cerrar → subir el PDF**

**F-009 ya no comprueba la tabla `gra` de Sigrid.** La precondición pasa a ser
**nuestra** —parte apto (F-004) y archivado (F-006)—, que es lo que el usuario
sube y el circuito ya garantiza. El PDF entra en Sigrid después, en F-012.

Qué ha cambiado, fichero a fichero:

- **`requirements.md`**: R20 y R21 **reescritos**. R20 pasa de «no cerrar sin
  gráfico» a **«no consultar `rcg` ni `gra` para decidir»**, con control
  negativo. R21 pasa de «puerta cerrada por defecto» a **«el dry-run advierte
  siempre de que la reclamación quedará cerrada sin el parte dentro de
  Sigrid»**. R9 ya no devuelve si hay gráfico: devuelve ese aviso.
- **`design.md` §2**: reescrita entera. Ya no es «el hallazgo que obliga a
  preguntar» sino **el orden decidido más una sección
  `RIESGO ACEPTADO`**, escrita sin adornos: este servicio va a producir
  reclamaciones `CER` sin fila en `rcg`, algo que **no ha pasado ni una vez en
  los 2.365 cierres desde 2023**, y quien mire la base lo va a ver. Con sus
  tres mitigaciones —el parte existe archivado; el conjunto es localizable por
  el `tex` propio y reversible (`ope = 30`, 81 precedentes); quien confirma lo
  sabe porque el dry-run lo advierte— y su fecha de caducidad: F-012.
- **`design.md` §6 y §7.1**: `Reclamacion` **ya no tiene campo de gráficos** y
  `evaluar` ya no recibe `permitir_sin_grafico`. La consulta del dry-run pierde
  el `COUNT` sobre `rcg`. Que el dato no exista en el dominio es la forma más
  barata de que R20 no se pueda incumplir por descuido.
- **`config/settings.py`**: desaparece `CIERRE_SIN_GRAFICO_PERMITIDO`. La
  puerta que se había diseñado ya no hace falta.
- **`tasks.md`**: T1, T4 y T13 pasan a verificar el control negativo; T18 exige
  que el aviso se pinte **siempre**; T19 obliga a corregir
  `docs/ARCHITECTURE.md` §«Alcance del cierre», que hoy dice que el alcance
  «está en el aire» a la espera de F-008.

## 5.2 · OD-2 → **D6 · el correo manda, el login se confirma una vez**

El supuesto del humano —«el correo de la app y el de Sigrid son el mismo»— **la
base no lo confirma** (`usu.ele` vacío en los 228). El diseño lo trata como
supuesto: el supuesto **propone**, el ERP **dispone**, y solo lo que el ERP
confirma se guarda y se escribe.

El bloque 7 de `requirements.md` está **reescrito**: R29 (si hay correspondencia
confirmada, se usa sin derivar nada), R30 (si no, se deriva del correo y **se
verifica** contra `dbo.usu`), R31 (candidato inexistente o ambiguo → no se
cierra, con error que nombra correo y login intentado), **R32 (jamás se escribe
en el log del ERP un login sin verificar)**, R33 (lo verificado se guarda como
confirmado) y R34 (alta manual con **precedencia** sobre la derivación, para los
**2 de 8** casos medidos que no siguen la convención).

`08_usuarios_sigrid.sql` sigue siendo **el único DDL nuevo**, como se pidió.

**Dos contradicciones aparentes, resueltas por escrito** en vez de dejarlas
para que las descubra el reviewer:

1. **R43 dice que la traza no guarda el login; R33 dice que se guarda.** Son
   tres sitios distintos: el **log de Sigrid** lleva el login (lo necesita el
   ERP), la **traza del cierre** solo el `oid` (para reconstruir qué hicimos no
   hace falta saber quién es), y la **tabla de correspondencias** el par
   `oid` → login, que es su razón de existir. R43 prohíbe el login **en la
   traza del cierre**.
2. **R31 nombra el correo en el error; R45 prohíbe el correo en los logs.** Dos
   destinos: el **mensaje** va al usuario autenticado y le nombra **su propio**
   correo, que ya tiene delante; el **log** lo lee cualquiera que abra
   Application Insights. Lo que no puede pasar es que el mensaje se registre tal
   cual.

## 5.3 · El hallazgo que se deja escrito para F-012 (no cambia F-009)

**Nueva `design.md` §11 · «Lo que queda fuera, y una trampa que le espera a
F-012».** El humano tiene razón: el PDF va a la **base documental**. No hizo
falta volver al ERP — **está medido en
`docs/referencia/03_modelo_posventa_sigrid.md` §4.1** y se cita en vez de
repetir la consulta: son **dos tablas `gra` en dos bases**, los metadatos y el
enlace `rcg` en la base de negocio, y **el binario en `ima` de la documental**,
siempre (357.901 filas, ninguna vacía; para posventa `ruesma.gra.ima` está
vacío, con `vin = 3`).

Y ahí está la trampa: la configuración desplegada que se leyó para D3 tiene **la
base de negocio como única escribible**, y `sigrid_api.md` dice que la
documental queda fuera **a propósito**. Es decir: **subir el PDF a Sigrid hoy no
tiene por dónde hacerse**. No basta un endpoint de dominio nuevo en
`sigrid-api` — hay que **habilitar la escritura en esa base**, y eso lo decide
el dueño de `sigrid-api`, no este proyecto.

**No afecta a F-009**, que solo escribe en la base de negocio, donde sí está
permitido. Por eso no bloquea. Queda escrito en el `design.md` y T21 obliga a
llevarlo también a `azure-apps/postventa_incidencias.md`, para que quien coja
F-012 lo sepa el primer día.

## 5.4 · Estado de la spec tras la segunda pasada

- **53 requisitos** (R1–R53), sin huecos, y **los 53 citados en `tasks.md`**:
  comprobado con un recuento automático, no a ojo.
- **29 tareas** (T1–T29), sin huecos. **El antiguo bloque 0 ha desaparecido**:
  existía solo para obtener estas dos respuestas, y ya están.
- **Ninguna decisión abierta.**
- **Ni una escritura en Sigrid**, tampoco en esta pasada: no hizo falta ninguna
  consulta nueva. Ningún correo, login ni valor de configuración entra en la
  spec ni en este informe.
