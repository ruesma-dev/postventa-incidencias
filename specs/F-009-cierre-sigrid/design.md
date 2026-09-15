<!-- specs/F-009-cierre-sigrid/design.md -->
# F-009 · Cierre de la incidencia en Sigrid (solo estado) — Diseño

> Rigor `critico`. Esta feature es la **primera escritura de este proyecto en
> un ERP de producción**. Todo lo que sigue está diseñado sobre lo que F-008
> midió contra el ERP real, no sobre lo que parecía razonable.

## 0 · Lo que ya está resuelto y no hay que volver a preguntar

| Pregunta | Respuesta | Dónde |
|---|---|---|
| Qué escribe «Cerrar parte» | `con.est` y una fila en `dbo.log`. **Nada más** | `docs/referencia/03_modelo_posventa_sigrid.md` §2 |
| Si toca `con.tiemod` | **No.** El log es el único rastro temporal del cierre | íd. §2.3 |
| Cuál es el estado de cierre | El `conest` con `cod = 'CER'`, resuelto en ejecución | íd. §1 |
| Cómo se localiza la reclamación | Por `con.cod`, único dentro del tipo, acotando siempre por `tip` | íd. §1.1 |
| Si los cierres son irreversibles | **No**: 81 filas `DESHACER proceso` | íd. §2.4 |
| El modelo de datos y el contrato de la pasarela | No se copian aquí | `azure-apps/sigrid_tablas.md`, `azure-apps/sigrid_api.md` |

**Los cuatro documentos anteriores son la referencia y no se duplican en esta
spec.** Lo que sigue añade solo lo que ninguno decía.

## 1 · Las cuatro decisiones del humano (2026-08-26), y qué se midió de cada una

### D1 · El `tex`: texto propio rastreable

**Decidido: `Cerrar parte (postventa-incidencias)`.**

Comprobado antes de proponerlo:

- **Cabe.** `sigrid_tablas.md` dice «Texto ilimitado» y `sys.columns` lo
  confirma: `log.tex` es **`text`**, no un `varchar(N)`. No hay tope. Los 36
  caracteres del texto propuesto están dentro del rango que el ERP ya escribe
  (12 a 58 caracteres).
- **No rompe ninguna uniformidad, porque no la hay.** El propio ERP escribe
  **dos** textos distintos para el mismo proceso: `Cerrar parte` (6.843 veces)
  y `Proceso ejecutado (Cerrar parte)` (una). Cualquiera que filtre por
  igualdad estricta ya se está perdiendo una fila hoy.
- **Sigue apareciendo en los informes existentes.** Empieza por `Cerrar
  parte`, así que el filtro por prefijo con el que F-008 midió toda la
  población (`tex LIKE 'Cerrar parte%'`) **encuentra nuestros cierres**. Un
  texto que empezara distinto nos borraría de los informes de Posventa.
- **Y los hace localizables en un solo `LIKE`**, que es justo lo que D1 pide:
  si el piloto se tuerce, hay que poder revertir *solo* lo nuestro.

Los demás campos de la fila salen medidos y son homogéneos en las 6.843 filas
de `Cerrar parte`: `tab = 'con'`, `ori = 0`, `est = 1`, `emp = 1`, `cod` y `res`
copiados de la reclamación. **`emp` se toma de `con.emp`, no se cablea**: hoy
todas las reclamaciones son de la empresa 1, pero eso es un dato de esta
instalación, exactamente igual que el `est = 9`.

`log.res` es `varchar(128)` y `con.res` es **también** `varchar(128)`, con cero
filas por encima: la copia **no necesita truncarse**.

### D2 · El `usu`: el login de quien confirma — investigado y resuelto

**Sí existe tabla de usuarios**: `dbo.usu` (228 filas), con `cod` (el login,
`varchar(24)`), `res`, `ele` (correo), `sid`, `dni`. Hay además `dbo.usuemp`
(usuario × empresa) y `dbo.sisusu`, que está **vacía**.

**Y no sirve para resolver la identidad.** Medido por lectura el 2026-08-26,
todo agregado y sin traer un solo login ni correo:

| Medida | Resultado |
|---|---|
| Usuarios en `dbo.usu` con correo (`ele`) | **0 de 228** |
| Usuarios en `dbo.usu` con SID de dominio (`sid`) | **0 de 228** |
| Usuarios distintos con correo en `usuemp` | **8 de 228** |
| Logins que han cerrado partes de posventa desde 2025 | **3** |
| De esos 3, con correo registrado | **2** |
| De los 8 con correo, cuántos cumplen `cod` = parte local del correo | **6** |

Los dos caminos automáticos están rotos por los datos: **por correo** no hay de
dónde resolver (8 de 228, y uno de los tres cerradores no lo tiene), y **por
convención** el acierto medido es de 6 sobre 8. Un 75 % no vale cuando el error
consiste en firmar en el log de un ERP de producción el cierre de una persona
que no lo hizo.

**Mecanismo, RESUELTO por el humano el 2026-08-26 — el correo manda, el login se
confirma una vez:**

Las palabras del humano fueron: «cada usuario de la app tiene mapeado su correo;
en principio es el mismo el de login en la app y el de Sigrid». Eso es un
**supuesto razonable que la base no confirma** —`usu.ele` está vacío en los 228
usuarios—, así que el diseño lo trata como supuesto y no como hecho:

1. **Si ya hay correspondencia confirmada**, se usa y **no se deriva nada**
   (R29). La derivación es la **siembra**, no el mecanismo de cada cierre.
2. **Si no la hay**, el login **candidato** se deriva de la parte local del
   correo del usuario autenticado en el front (R30).
3. Ese candidato **se verifica obligatoriamente contra `dbo.usu`** por lectura
   antes de cualquier escritura (R30).
4. **Si no existe exactamente una vez, o hay cualquier ambigüedad, NO se
   cierra** (R31): error que nombra el correo y el login intentado y pide dar de
   alta la correspondencia a mano. **Jamás se firma en el log del ERP con un
   login sin confirmar** (R32).
5. Lo verificado **se guarda como confirmado** en `postventa.usuarios_sigrid`
   (R33), así que el segundo cierre de esa persona ya no deriva nada.
6. La tabla admite **alta manual**, con **precedencia** sobre la derivación
   (R34): es la salida para los **2 de 8** casos medidos que no cumplen la
   convención.

Lo que hace seguro apoyarse en un supuesto no confirmado es el paso 3: el
supuesto **propone**, el ERP **dispone**, y solo lo que el ERP confirma se
guarda y se escribe.

### D3 · La escritura de `sigrid-api`: RESUELTO, y no hace falta tocar el otro repositorio

Comprobado el 2026-08-26 leyendo la configuración de la Function App de
`sigrid-api` (`az functionapp config appsettings list`, **solo lectura**, sin
ver ningún secreto). En la spec entra solo el hecho, nunca un valor:

| Qué se preguntó | Respuesta |
|---|---|
| ¿`UPDATE` permitido? | **Sí** |
| ¿`INSERT` permitido? | **Sí** |
| ¿La base de negocio en la lista blanca de escritura? | **Sí**, y es la única |
| ¿Credencial de escritura configurada? | Sí, por **referencia a Key Vault** |
| `REQUIRE_WHERE_ON_UPDATE_DELETE` | `true` → el `UPDATE` **tiene** que llevar `WHERE` |
| Tope de filas afectadas / sentencias por batch | 1.000 / 50 |

**Consecuencia: F-009 NO exige ningún cambio en el repositorio `sigrid-api`.**
Las dos sentencias caben en `POST /api/sql/write` tal y como está desplegado.
El **límite de servicio** del `CLAUDE.md` se respeta sin proponer nada: lo que
sí lo exigiría es F-012 (escribir el BLOB del gráfico), y sigue en su feature.

### D4 · El gráfico-URL no se confirma aquí

No se toca. F-008 demostró que no hay ni un precedente en 282.599 filas; quien
lo necesita es F-023.

### D5 y D6 · Las dos que resolvió el humano después

**D5 · el orden es validar → cerrar → subir el PDF** y **D6 · el correo manda y
el login se confirma una vez**. Se desarrollan en §2 y en D2 respectivamente, y
están recogidas con las demás en **§10 · Decisiones cerradas**.

## 2 · El orden es validar → cerrar → subir el PDF, y el riesgo que eso acepta

**Decidido por el humano el 2026-08-26.** F-009 **no comprueba la tabla `gra` de
Sigrid**. La precondición del cierre es **nuestra**: el parte tiene que estar
validado por la aplicación (F-004) y archivado (F-006), que es exactamente lo que
el usuario sube y lo que el circuito ya garantiza. Con eso se registra el cierre.
El PDF llega a Sigrid **después**, en **F-012**.

Se descarta así la precondición dura que había recomendado F-008 §6.2. El dato
que lo justifica se midió al escribir esta spec: **el 98,7 % de las
reclamaciones abiertas no tiene gráfico**, porque subirlo y cerrar son **el mismo
gesto** en el flujo manual —F-008 §4.2 lo tiene datado al minuto: gráfico a las
11:40:39, cierre a las 11:46:33 del mismo día—.

| Estado | Reclamaciones creadas desde 2025 | Con gráfico | Sin gráfico |
|---|---:|---:|---:|
| `SAT` | 90 | 1 | 89 |
| `PTE` | 839 | **11** | 828 |
| `TER` | 1.474 | **19** | 1.455 |
| `NPR` | 258 | 173 | 85 |
| `CER` | 2.105 | 2.102 | 3 |

Exigir el gráfico habría dejado a F-009 sin poder cerrar prácticamente nada.

### RIESGO ACEPTADO · Nuestros cierres dejarán reclamaciones sin gráfico en el ERP

Sin adornos y por escrito: **este servicio va a producir reclamaciones en estado
`CER` sin ninguna fila en `rcg`, algo que no ha ocurrido ni una sola vez en los
2.365 cierres con «Cerrar parte» desde 2023.** Nuestros cierres serán, mirando
los datos del ERP, anómalos respecto a todo el histórico reciente. No es un
efecto colateral menor: es la consecuencia directa de la decisión de orden, y
quien mire la base lo va a ver.

Lo que lo hace asumible son tres cosas, y las tres tienen que sostenerse:

1. **El parte firmado existe.** Está archivado en SharePoint, con su traza en
   `postventa.archivos` y su restricción de clave ajena contra `postventa.partes`
   (F-019). No se cierra nada cuya prueba no esté guardada (R17). Lo que falta no
   es el documento: es el documento **dentro de Sigrid**.
2. **El conjunto es localizable y reversible.** El `tex` propio de D1 identifica
   exactamente nuestros cierres con un solo `LIKE`, y los cierres se deshacen en
   el ERP (`ope = 30`, 81 precedentes). Si el piloto se tuerce, se sabe qué
   revertir y se puede revertir.
3. **Quien confirma lo sabe.** El dry-run advierte explícitamente de que la
   reclamación quedará cerrada sin el parte dentro de Sigrid (R21). Nadie
   confirma esto sin haberlo leído.

**Y tiene fecha de caducidad**: la anomalía desaparece cuando **F-012** suba el
PDF. Mientras tanto, el circuito no reproduce del todo lo que hace Posventa, y
esta sección existe para que eso no se olvide.

## 3 · Ficheros a crear

Todos bajo `services/postventa-api/`, salvo donde se indique.

| Ruta | Capa | Qué contiene |
|---|---|---|
| `domain/models/cierre.py` | **domain** | `EstadoSigrid`, `Reclamacion`, `PlanDeCierre`, `ResultadoCierre`, `CODIGO_ESTADO_CIERRE`, `CODIGOS_ESTADO_CERRABLE`, `TEXTO_LOG_CIERRE`. Entidades puras: sin red, sin SQL, sin reloj. |
| `domain/ports/erp.py` | **domain** | `ErpPort`, el puerto del ERP: `leer_reclamacion`, `existe_usuario`, `cerrar`. Tres métodos y ni uno más. |
| `domain/ports/usuarios_sigrid.py` | **domain** | `RepositorioUsuariosSigridPort`: `resolver_login(usuario_oid)`. |
| `application/pipelines/paso_cierre.py` | **application** | Orquesta: valida precondiciones → dry-run → (confirmación) → commit → traza. Recibe los puertos ya construidos. |
| `infrastructure/sigrid/__init__.py` | infra | — |
| `infrastructure/sigrid/consultas.py` | infra | Constructores **puros** del SQL de lectura: devuelven `(sql, parametros)`. Sin red. |
| `infrastructure/sigrid/escrituras.py` | infra | Constructores **puros** del batch de escritura: devuelven las sentencias con sus parámetros. Sin red. |
| `infrastructure/sigrid/cliente.py` | infra | `AdaptadorSigridApi(ErpPort)`: `httpx` contra `sigrid-api`, reintentos con `tenacity`, puerta de entorno en el constructor. |
| `infrastructure/sigrid/fabrica.py` | infra | `construir_erp(ajustes)`: entorno → interruptor → configuración → adaptador. |
| `infrastructure/persistencia/sql/08_usuarios_sigrid.sql` | infra/SQL | El mapeo `usuario_oid` → `login_sigrid`. |
| `interface_adapters/api/cerrar.py` | interface | Handler de `POST /api/cerrar`: compone y serializa. |
| `infra/07_alta_usuario_sigrid.ps1` | infra | Script re-ejecutable para dar de alta un mapeo. Sin credenciales dentro. |

**Que `consultas.py` y `escrituras.py` sean constructores puros de SQL es la
decisión que hace testeable la feature entera sin red.** Es el mismo patrón que
`infrastructure/persistencia/sentencias.py` ya usa en este proyecto, y por el
mismo motivo: el SQL más delicado del servicio se comprueba carácter a carácter
en un test unitario.

### Tests a crear (`services/postventa-api/tests/`)

`test_f009_dominio_cierre.py`, `test_f009_consultas.py`,
`test_f009_escrituras.py`, `test_f009_adaptador_sigrid.py`,
`test_f009_fabrica.py`, `test_f009_paso_cierre.py`, `test_f009_cerrar_http.py`,
`test_f009_arquitectura.py`, `test_f009_estado_no_hardcodeado.py`,
`test_f009_logs_sin_datos_personales.py`, `test_f009_usuarios_sigrid.py`,
`test_f009_ddl_orden.py`, y `tests/utiles_sigrid.py` con el doble del ERP.

## 4 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `config/settings.py` | Bloque nuevo «Cierre en Sigrid (F-009)»: `CIERRE_HABILITADO` (bool, **false**), `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` (**secreto**, por Key Vault), `SIGRID_TIMEOUT_S` (35, presupuesto de §«45 segundos» de `ARCHITECTURE.md`), `SIGRID_REINTENTOS` (3), `SIGRID_BASE_DATOS`. Todos `str \| None` u opcionales, como Graph y PG: `/health` tiene que arrancar sin ellos. |
| `function_app.py` | Ruta `cerrar` en `ANONYMOUS` (mismo motivo documentado que las otras nueve) y traducción de las excepciones nuevas a 400/409/502/503. Añadir a la cabecera el tercer candado: la ventana de escritura de `/api/cerrar`. |
| `domain/models/errores.py` | `CuerpoDeCierreInvalido`, `CierreDeshabilitado`, `ConfiguracionSigridIncompleta`, `ReclamacionNoLocalizada`, `EstadoNoCerrable`, `SinGraficoEnSigrid`, `UsuarioSigridNoMapeado`, `UsuarioSigridInexistente`, `CierreFallido`, `EstadoCambiadoDesdeElDryRun`. |
| `domain/ports/persistencia.py` | Nada: `guardar_cierre` **ya existe** (F-005). |
| `infrastructure/persistencia/ddl.py`, `arranque.py` | Registrar `08_usuarios_sigrid.sql` en el orden. |
| `infrastructure/persistencia/sentencias.py`, `repositorio_pg.py`, `mapeo.py` | `select_login_sigrid` y `upsert_login_sigrid`, siguiendo el patrón de `select_preferencias`. |
| `services/postventa-front/js/api.js` | Método `cerrar(cuerpo, hash)`. |
| `services/postventa-front/js/app.js`, `index.html`, `css/styles.css` | Paso de cierre: enseñar el dry-run y pedir confirmación. |
| `docs/ARCHITECTURE.md` | El paso 7 del pipeline pasa de «por decidir» a lo que hace. Actualizar «Alcance del cierre en la primera versión» y la tabla de sistemas externos. |
| `docs/INTEGRACION.md` | §1, §4, §6, §7 y §8: qué escribimos ahora en Sigrid (R49). |
| `azure-apps/postventa_incidencias.md` | Que este servicio **escribe** en el ERP (R50). Otro repositorio: se edita, no se duplica aquí. |
| `docs/DESPLIEGUE.md` | La App Setting del interruptor y el procedimiento de apertura. |

## 5 · Ficheros que NO se tocan

- **`services/postventa-api/infrastructure/sharepoint/`** — el archivo es F-006
  y esta feature no lo roza. Tentador porque el patrón de puerta se copia de
  ahí: se **copia el patrón**, no se refactoriza el original.
- **`infrastructure/persistencia/sql/06_cierres.sql` y `07_preferencias.sql`** —
  F-005 los dejó **ya construidos para esta feature**, con `EstadoCierre`,
  `confirmado_por`, `estado_origen_sigrid`/`estado_destino_sigrid` y la
  preferencia de auto-cierre. No hay que cambiar ni una columna.
- **`domain/models/validacion.py`, `firma.py`, `nombrado.py`** — el veredicto y
  el nombre ya están decididos cuando llega el cierre.
- **`application/pipelines/paso_archivo.py`** — el cierre va después, no dentro.
- **El repositorio `sigrid-api`** — D3 demuestra que no hace falta.
- **`harness/features.json`** — lo cambia el humano.

## 6 · Las firmas que importan

### Dominio (`domain/models/cierre.py`)

```
CODIGO_ESTADO_CIERRE: str            # 'CER' — es un CÓDIGO, no un número (C3)
CODIGOS_ESTADO_CERRABLE: tuple[str]  # ('SAT', 'PTE', 'TER')
TEXTO_LOG_CIERRE: str                # 'Cerrar parte (postventa-incidencias)'

@dataclass(frozen=True) Reclamacion:
    ide, emp, tip, est, codigo, descripcion,
    estado_origen_cod, estado_origen_res,
    estado_destino_est, estado_destino_cod, estado_destino_res

@dataclass(frozen=True) PlanDeCierre:      # lo que el dry-run devuelve
    reclamacion, login_sigrid, cerrable: bool, motivo: str | None,
    aviso_sin_grafico: str                 # R21, siempre presente

def evaluar(reclamacion) -> PlanDeCierre
```

`evaluar` es **dominio puro**: decide `ya_cerrada` y `no cerrable por estado` sin
tocar nada. Se prueba entera con fixtures. **No recibe ningún dato de gráficos**
—`Reclamacion` ni siquiera tiene ese campo—, que es la forma más barata de que
R20 no se pueda incumplir por descuido.

`CODIGOS_ESTADO_CERRABLE` deja fuera `NPR` (NO PROCEDE) **a propósito**: alguien
decidió que esa reclamación no procede, y cerrarla la daría por resuelta.

### Puerto (`domain/ports/erp.py`)

```
leer_reclamacion(*, codigo: str, codigo_estado_cierre: str) -> Reclamacion | None
existe_usuario(*, login: str) -> bool
cerrar(*, plan: PlanDeCierre, ahora: datetime) -> int   # filas afectadas
```

### Paso (`application/pipelines/paso_cierre.py`)

```
paso_cierre(contexto, erp, repositorio, usuarios, *, commit: bool,
            usuario_oid: str, correo: str, ahora) -> ContextoParte
```

Orden **no negociable**: apto (R16) → archivado (R17) → login confirmado o
derivado y **verificado** contra `dbo.usu` (R29–R32) → dry-run (R8) → `evaluar`
→ traza `dry_run_ok` (R40) → y solo si `commit`, la escritura y la traza
`cerrado` (R41).

## 7 · El SQL, sentencia a sentencia

**Base**: la de negocio (`ruesma`), la única con escritura permitida. Va por
configuración, nunca literal en el código.

### 7.1 · La consulta del dry-run: una sola, como recomendó F-008 §6.4.6

```sql
SELECT c.ide, c.emp, c.tip, c.est, c.cod, c.res,
       eo.cod, eo.res,
       ed.est, ed.cod, ed.res
FROM dbo.con c
LEFT JOIN dbo.conest eo ON eo.tip = c.tip AND eo.est = c.est
LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?
WHERE c.tip = ? AND c.cod = ?
```

Trae el estado de origen legible y el destino resuelto **contra `conest`** (R1),
de una vez. Comprobado que `conest` devuelve **exactamente una** fila para
`cod = 'CER'` en el tipo de reclamación; si devolviera otra cosa, R2 aborta.

**No hay ningún `COUNT` sobre `rcg`, y es deliberado** (R20): tras la decisión
del humano del 2026-08-26, el gráfico no condiciona el cierre. Un control
negativo comprueba que ni esta consulta ni el dominio mencionan `rcg` o `gra`.

### 7.2 · La verificación del login

```sql
SELECT COUNT(*) FROM dbo.usu WHERE cod = ?
```

Tiene que devolver exactamente 1 (R30). Va aparte de la anterior porque su fallo
tiene motivo propio y mensaje propio.

### 7.3 · El batch de escritura: las dos sentencias, una transacción

`POST /api/sql/write` con `max_affected_rows = 2` — la red de seguridad de
`sigrid_api.md` §7.3 contra un `WHERE` mal escrito.

**Sentencia 1 — el estado:**

```sql
UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = ? AND est = ?
```

El `WHERE` es obligatorio (`REQUIRE_WHERE_ON_UPDATE_DELETE = true`) y lleva el
**estado de origen** leído en el dry-run: eso es el control optimista de R11. Si
alguien movió la reclamación entretanto, afecta a 0 filas y no pisa nada.

**Sentencia 2 — la fila de auditoría:**

```sql
INSERT INTO dbo.log (ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est)
SELECT (SELECT ISNULL(MAX(l.ide), 0) + 1 FROM dbo.log l WITH (UPDLOCK, HOLDLOCK)),
       c.emp, ?, ?, ?, ?, ?, 'con', c.tip, c.cod, c.res, ?, ?
FROM dbo.con c
WHERE c.ide = ? AND c.tip = ? AND c.est = ?
```

Esta sentencia concentra cuatro decisiones, y ninguna es cosmética:

1. **El `ide` se reserva dentro de la propia sentencia** (R26). `log.ide` **no
   es IDENTITY** —verificado en `sys.columns`— y es la clave primaria única
   `log_indide`; la tabla tiene 8,4 millones de filas asignadas por
   `MAX(ide)+1`. `sigrid_api.md` §7.5 avisa de que `sql/write` **no** protege
   esa reserva con applock, así que se protege aquí, con `UPDLOCK, HOLDLOCK`.
2. **Y si aun así colisiona, falla en seguro.** La clave única rechaza el
   `INSERT`, `sql/write` revierte **todo el batch** (§7.3) y el `UPDATE` se va
   con él. El ERP queda **sin ningún cambio**, que es exactamente lo que R26
   pide. El reintento lo decide una persona, no el código (R27).
3. **El `FROM` es `dbo.con` filtrado por el estado DESTINO**, ya aplicado por la
   sentencia 1 dentro de la misma transacción. Si el `UPDATE` no hizo nada, este
   `SELECT` no devuelve filas y **no se inserta ningún log**. Sin eso quedaría
   una fila de auditoría diciendo que se cerró algo que no se cerró.
   > El filtro **tiene que ir en el `FROM`, no en un `WHERE EXISTS`**: un
   > agregado sin `GROUP BY` devuelve una fila aunque no case nada, y
   > `ISNULL(MAX(ide),0)+1` valdría **1** — una colisión garantizada contra la
   > fila más antigua de la tabla. La subconsulta escalar del `ide` y el `FROM`
   > filtrado evitan justo eso.
4. **`emp`, `tip`, `cod` y `res` se copian de la reclamación** en el propio SQL,
   no se envían como parámetros calculados en Python (D1).

Después del batch se comprueba que `total_affected_rows` es **2**. Cualquier
otra cosa es `error` con su motivo, nunca un cierre dado por bueno.

### 7.4 · El DDL propio: `08_usuarios_sigrid.sql`

Numeración `NN_nombre.sql` dentro de su capa, idempotente y con cabecera,
según `docs/CONVENTIONS.md`. Schema propio `postventa` — **nunca `public`**, y
nunca fuera de él (regla dura del `CLAUDE.md` sobre el servidor compartido).

```sql
CREATE TABLE IF NOT EXISTS postventa.usuarios_sigrid (
    usuario_oid      text PRIMARY KEY,
    login_sigrid     text        NOT NULL,
    alta_at_utc      timestamptz NOT NULL,
    verificado_at_utc timestamptz
);
```

`usuario_oid` es **dato personal seudónimo** y es la clave, igual que en
`preferencias_usuario`. `login_sigrid` es el `usu.cod` del ERP.

**Por qué una tabla y no una columna en `preferencias_usuario`**: son dos cosas
distintas con dos dueños distintos. La preferencia la decide el usuario y su
fila nace sola al decidirla; el mapeo lo da de alta un administrador y su
ausencia **impide cerrar**. Fundirlas haría que guardar una preferencia creara
media identidad.

## 8 · Encaje en la arquitectura

Se respeta la hexagonal de `docs/ARCHITECTURE.md` sin excepciones:

- **`domain/`** no importa `httpx` ni conoce SQL. `evaluar` decide con datos.
- **`infrastructure/sigrid/`** es el **único** paquete que conoce `sigrid-api`,
  igual que `infrastructure/sharepoint/` es el único que conoce Graph.
- **`application/pipelines/paso_cierre.py`** orquesta contra puertos y no sabe
  si detrás hay un ERP o un doble.
- **La composición vive en el punto de entrada** (`interface_adapters/api/`),
  nunca dentro del paso, como manda `docs/CONVENTIONS.md`.
- El paso 7 del pipeline (**Cierre**) queda por fin implementado, y con el
  contrato que ya anunciaba: dry-run, confirmación, `commit`.

`test_f009_arquitectura.py` lo fija, como ya hacen los `test_fXXX_arquitectura`
de F-002 a F-006.

### Límite de microservicio

**F-009 no cruza ninguna frontera de servicio.** D3 lo demuestra: las dos
sentencias caben en la pasarela desplegada. Lo que sí la cruzaría —escribir el
BLOB del gráfico, que exigiría un endpoint de dominio nuevo en el repositorio
`sigrid-api`— es **F-012** y sigue estando allí.

## 9 · Riesgos, y alternativas descartadas

| Riesgo | Qué lo contiene |
|---|---|
| Cerrar una incidencia que no es | `cod` único dentro del tipo (23.063/23.063 medido), `WHERE` por `ide` **y** `tip` **y** `est`, tope de 2 filas |
| Cerrar algo que alguien reabrió | Control optimista por estado de origen (R11): el `UPDATE` no encuentra la fila |
| Escribir el log de un cierre que no ocurrió | El `FROM dbo.con` filtrado de §7.3 |
| Colisión de `ide` en `dbo.log` | `UPDLOCK, HOLDLOCK` + clave única + rollback del batch entero |
| Firmar el cierre de otra persona | Solo se escribe un login **verificado contra `dbo.usu`** (R30, R32); sin confirmación no se cierra (R31) |
| Escribir desde un puesto de trabajo | Doble puerta entorno + interruptor, comprobada en fábrica **y** en el adaptador (R34), más la guardia de red de la suite (R36) |
| Cerrar sin que el parte exista en ninguna parte | R17: tiene que constar archivado |
| Dejar reclamaciones cerradas sin gráfico | **Riesgo aceptado** (§2): el parte existe archivado, el `tex` propio lo hace localizable y reversible, el dry-run lo advierte (R21) y F-012 lo cierra |

**Alternativas descartadas:**

- **`tex = 'Cerrar parte'` a secas.** Descartada por D1: haría nuestros cierres
  indistinguibles de los manuales justo en la feature donde más falta hace
  poder distinguirlos.
- **Imitar «Cerrar parte sin archivo (RPV)».** Termina en el mismo estado, solo
  aporta saltarse un control que de todos modos no replicamos (§2), y está
  abandonado desde 2025-03-11 (F-008 §6.3).
- **Un usuario técnico en `usu`.** Descartada por D2 del humano.
- **Deducir el login del correo.** Descartada por el dato: 6 aciertos de 8.
- **Reintentar la escritura automáticamente.** Descartada: reintentar contra un
  ERP de producción sin que nadie mire es cómo se cierran dos veces las cosas.
  El reintento lo pide una persona (R27).
- **Un endpoint de dominio nuevo en `sigrid-api`.** Innecesario (D3), y sería
  otro repositorio.

## 10 · Decisiones cerradas (2026-08-26)

**No queda ninguna decisión abierta.** Las seis se tomaron el mismo día y mandan
sobre el diseño. Las cuatro primeras venían del encargo; las dos últimas las
resolvió el humano después de ver lo medido en esta spec.

| # | Decisión | Qué se hace |
|---|---|---|
| **D1** | El `tex` de la fila de `dbo.log` es **texto propio rastreable** | `Cerrar parte (postventa-incidencias)`. Empieza por `Cerrar parte` para no desaparecer de los informes que filtran por prefijo, y nombra el servicio para distinguirse de un cierre manual (§1) |
| **D2** | El `usu` es el login de Sigrid de quien confirma, **nunca un usuario técnico** | Correspondencia confirmada si la hay; si no, candidato derivado del correo y **verificado contra `dbo.usu`** antes de escribir. Sin confirmación, no se cierra (§1) |
| **D3** | La escritura de `sigrid-api` **está habilitada**, y con los prefijos que hacen falta | `INSERT` y `UPDATE` permitidos, base de negocio en la lista blanca. **F-009 no exige tocar el repositorio `sigrid-api`** (§1) |
| **D4** | El **gráfico-URL no se confirma** en esta feature | Fuera de alcance. Es F-023 |
| **D5** | El orden es **validar → cerrar → subir el PDF** | F-009 **no consulta `gra` ni `rcg`**: la precondición es propia (parte apto y archivado). El PDF entra en Sigrid en F-012. Con el **riesgo aceptado** de §2, escrito y mitigado |
| **D6** | El **correo manda y el login se confirma una vez** | La derivación es la **siembra**, no el mecanismo de cada cierre; lo verificado se guarda en `postventa.usuarios_sigrid`, con alta manual y precedencia para los casos que no siguen la convención |

## 11 · Lo que queda fuera, y una trampa que le espera a F-012

Fuera de F-009: **subir el parte a Sigrid como gráfico** (F-012) y **el
gráfico-URL** (F-023). Nada de eso se diseña aquí.

Pero hay un obstáculo en F-012 que **no se ve hasta que se tropieza con él**, y
se deja escrito aquí porque se descubrió al comprobar D3:

### El PDF va a `ruesma_rep`, y ahí hoy **no se puede escribir**

Lo primero está medido y confirma lo que dijo el humano. F-008 lo dejó en
`docs/referencia/03_modelo_posventa_sigrid.md` §4.1, y **no se repitió la
consulta**: hay **dos tablas `gra`, en dos bases distintas**. `ruesma.gra` guarda
los **metadatos** y es la que enlaza `rcg`; **`ruesma_rep.gra` guarda el binario
en `ima`**, siempre — las 357.901 filas tienen contenido y ninguna está vacía.
Los `ide` de las dos son espacios independientes y la pareja se localiza por
`gra.cod`. Para los 13.450 gráficos de posventa, `ruesma.gra.ima` está **vacío**
(`vin = 3`, «incrustado externo»).

Es decir: **subir el parte exige escribir en las dos bases** — metadatos y enlace
en `ruesma`, binario en `ruesma_rep`.

Y ahí está el problema. La configuración desplegada de `sigrid-api`, leída el
2026-08-26 para resolver D3, tiene **la base de negocio como única base
escribible**; `ruesma_rep` **queda fuera de `ALLOWED_WRITE_DATABASES`**, y
`sigrid_api.md` dice que es **a propósito** («escritura SOLO en negocio»).

**Consecuencia para F-012, y hay que decirla ahora**: no basta con un endpoint de
dominio nuevo en `sigrid-api`. Hace falta además **habilitar la escritura en la
base documental**, que es una decisión del **dueño de `sigrid-api`** y afecta a
todo el ecosistema, no solo a este proyecto. Con la configuración de hoy,
**subir el PDF a Sigrid no tiene por dónde hacerse**.

Esto **no cambia nada de F-009** —que solo escribe en la base de negocio, donde
sí está permitido— y por eso no bloquea. Se escribe aquí para que quien coja
F-012 lo sepa el primer día y no el último.
