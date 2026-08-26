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

### D2 · El `usu`: el login de quien confirma — investigado, y con decisión abierta

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

**Mecanismo diseñado — mapeo explícito con verificación obligatoria:**

1. Una tabla propia, `postventa.usuarios_sigrid`, ata el `oid` opaco de Entra
   —lo único que este proyecto guarda de un empleado— con su `login_sigrid`.
2. **Sin fila de mapeo no se cierra** (R31). No se adivina, no se deduce, no
   hay valor por defecto.
3. El login resuelto **se verifica contra `dbo.usu` por lectura** antes de
   escribir (R30). Un login inventado no llega nunca al `INSERT`.
4. El alta la hace un administrador. Con tres personas en Posventa, el
   mantenimiento es de tres filas.
5. La convención `<parte local del correo>` se usa **solo** para sugerir el
   login en el mensaje de error, jamás para resolver.

Cuál de las tres vías quiere el humano queda como **decisión abierta OD-2**
(§10), con su coste.

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
lo necesita es F-013.

## 2 · El hallazgo que obliga a preguntar antes de implementar

F-008 §6.2 recomendó que F-009 **se niegue a cerrar una reclamación sin gráfico
asociado**, como réplica del control que hace el ERP, y lo llamó «una condición
barata de verificar». Barata de verificar lo es. Lo que no se midió entonces es
**con qué frecuencia se cumple**. Medido ahora, sobre las reclamaciones creadas
desde 2025:

| Estado | Reclamaciones | Con gráfico | Sin gráfico |
|---|---:|---:|---:|
| `SAT` | 90 | 1 | 89 |
| `PTE` | 839 | **11** | 828 |
| `TER` | 1.474 | **19** | 1.455 |
| `NPR` | 258 | 173 | 85 |
| `CER` | 2.105 | 2.102 | 3 |

**El 98,7 % de las reclamaciones abiertas no tiene gráfico.** No es un descuido
de Posventa: el gráfico y el cierre son **el mismo gesto**, y F-008 §4.2 lo
tiene datado al minuto —gráfico a las 11:40:39, cierre a las 11:46:33 del mismo
día—. Primero el documento, después el cierre, con seis minutos de diferencia.

Consecuencia directa: **una precondición dura de gráfico deja a F-009 sin poder
cerrar prácticamente nada**, salvo que alguien suba el PDF a Sigrid a mano justo
antes. Eso no invalida la recomendación de F-008 —para la integridad del ERP
sigue siendo lo correcto—, pero cambia radicalmente lo que cuesta.

**Lo que hace el diseño**: la comprobación se implementa siempre y su resultado
**va en el dry-run** (R9), de modo que nadie confirma a ciegas; y el
comportamiento ante «sin gráfico» lo decide una **puerta apagada por defecto**
(R20, R21). Por omisión, F-009 se niega. Abrirla es un gesto explícito y
consciente del humano, exactamente como `ARCHIVO_HABILITADO` en F-006.

No es improvisar: es el patrón que este proyecto ya usa para las escrituras en
sistemas ajenos. Pero **la decisión de negocio es del humano** y va como
**OD-1** (§10).

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
| `config/settings.py` | Bloque nuevo «Cierre en Sigrid (F-009)»: `CIERRE_HABILITADO` (bool, **false**), `CIERRE_SIN_GRAFICO_PERMITIDO` (bool, **false**), `SIGRID_API_BASE_URL`, `SIGRID_API_KEY` (**secreto**, por Key Vault), `SIGRID_TIMEOUT_S` (35, presupuesto de §«45 segundos» de `ARCHITECTURE.md`), `SIGRID_REINTENTOS` (3), `SIGRID_BASE_DATOS`. Todos `str \| None` u opcionales, como Graph y PG: `/health` tiene que arrancar sin ellos. |
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
    estado_destino_est, estado_destino_cod, estado_destino_res,
    graficos: int

@dataclass(frozen=True) PlanDeCierre:      # lo que el dry-run devuelve
    reclamacion, login_sigrid, cerrable: bool, motivo: str | None

def evaluar(reclamacion, *, permitir_sin_grafico: bool) -> PlanDeCierre
```

`evaluar` es **dominio puro**: decide `ya_cerrada`, `no cerrable por estado` y
`sin gráfico` sin tocar nada. Se prueba entera con fixtures.

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
            usuario_oid: str, permitir_sin_grafico: bool, ahora) -> ContextoParte
```

Orden **no negociable**: apto (R16) → archivado (R17) → login mapeado (R31) →
login verificado en el ERP (R30) → dry-run (R8) → `evaluar` → traza `dry_run_ok`
(R37) → y solo si `commit`, la escritura y la traza `cerrado` (R38).

## 7 · El SQL, sentencia a sentencia

**Base**: la de negocio (`ruesma`), la única con escritura permitida. Va por
configuración, nunca literal en el código.

### 7.1 · La consulta del dry-run: una sola, como recomendó F-008 §6.4.6

```sql
SELECT c.ide, c.emp, c.tip, c.est, c.cod, c.res,
       eo.cod, eo.res,
       ed.est, ed.cod, ed.res,
       (SELECT COUNT(*) FROM dbo.rcg r WHERE r.con = c.ide) AS graficos
FROM dbo.con c
LEFT JOIN dbo.conest eo ON eo.tip = c.tip AND eo.est = c.est
LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?
WHERE c.tip = ? AND c.cod = ?
```

Trae el estado de origen legible, el destino resuelto **contra `conest`** (R1) y
si hay gráfico, todo de una vez. Comprobado que `conest` devuelve **exactamente
una** fila para `cod = 'CER'` en el tipo de reclamación; si devolviera otra
cosa, R2 aborta.

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
| Firmar el cierre de otra persona | Mapeo explícito (R29) + verificación contra `dbo.usu` (R30) |
| Escribir desde un puesto de trabajo | Doble puerta entorno + interruptor, comprobada en fábrica **y** en el adaptador (R34), más la guardia de red de la suite (R36) |
| Cerrar sin que el parte exista en ninguna parte | R17: tiene que constar archivado |
| Dejar reclamaciones cerradas sin gráfico | Puerta apagada por defecto (R21) y el hecho **siempre** visible en el dry-run |

**Alternativas descartadas:**

- **`tex = 'Cerrar parte'` a secas.** Descartada por D1: haría nuestros cierres
  indistinguibles de los manuales justo en la feature donde más falta hace
  poder distinguirlos.
- **Imitar «Cerrar parte sin archivo (RPV)».** Termina en el mismo estado, solo
  aporta saltarse el control del gráfico —lo que no queremos legitimar— y está
  abandonado desde 2025-03-11 (F-008 §6.3).
- **Un usuario técnico en `usu`.** Descartada por D2 del humano.
- **Deducir el login del correo.** Descartada por el dato: 6 aciertos de 8.
- **Reintentar la escritura automáticamente.** Descartada: reintentar contra un
  ERP de producción sin que nadie mire es cómo se cierran dos veces las cosas.
  El reintento lo pide una persona (R27).
- **Un endpoint de dominio nuevo en `sigrid-api`.** Innecesario (D3), y sería
  otro repositorio.

## 10 · Decisiones abiertas para el humano

> **Ninguna de las dos bloquea escribir la spec, y las dos hay que responderlas
> antes de implementar.** El resto del diseño está en pie con cualquiera de las
> respuestas.

### OD-1 · ¿Puede F-009 cerrar una reclamación sin gráfico en Sigrid?

El dato de §2 es el que obliga a preguntar: **el 98,7 % de las reclamaciones
abiertas no tiene gráfico**, porque subirlo y cerrar son el mismo gesto.

| Salida | Qué cuesta | Qué se gana |
|---|---|---|
| **(A) Precondición dura** (recomendación de F-008 §6.2) | F-009 no cierra casi nada: alguien tiene que subir el PDF a Sigrid a mano justo antes. El ahorro se reduce al clic de cerrar | Integridad del ERP intacta: ni un cierre sin su documento, como desde 2023 |
| **(B) Puerta abierta en el piloto** | Deja reclamaciones cerradas sin gráfico, algo que no ha pasado ni una vez en 2.365 cierres desde 2023. Nuestros cierres serán anómalos en los datos | El circuito automatiza de verdad. El parte existe: está archivado en SharePoint, y el `tex` propio de D1 permite localizar exactamente ese conjunto y revertirlo |
| **(C) F-012 primero** | Reordena el backlog y exige un endpoint nuevo en el repositorio `sigrid-api` | La solución completa: el gráfico sube, y entonces la precondición dura se cumple sola |

**El diseño soporta las tres** sin cambiar: (A) es el comportamiento por
defecto, (B) es abrir la puerta, (C) no toca nada de lo diseñado aquí.

**Recomendación**: **(A) por defecto y (B) solo durante el piloto de
Mirasierra**, con la puerta abierta a mano y el conjunto vigilado por el `tex`.
Y **(C) como el destino**, no como una feature futura indefinida: mientras el
gráfico no suba, este circuito no reproduce lo que hace Posventa.

### OD-2 · ¿Cómo se resuelve el login de Sigrid del usuario del front?

Ninguna vía automática es fiable hoy (§1, D2).

| Vía | Qué cuesta | Fiabilidad |
|---|---|---|
| **(A) Mapeo explícito** en `postventa.usuarios_sigrid` | Un alta por persona. Con Posventa son 3 | **Total**: sin fila no se cierra, y el login se verifica contra `dbo.usu` |
| **(B) Poblar `usuemp.ele`** con el administrador de Sigrid y resolver por correo | Una gestión con quien administra el ERP; es una **escritura en Sigrid** que no hacemos nosotros | Total una vez poblado, y sin mantenimiento nuestro. Es la vía limpia a medio plazo |
| **(C) Convención `<parte local del correo>`**, verificada contra `dbo.usu` | Cero | **6 aciertos de 8 medidos.** Un homónimo firmaría el cierre de otro en el ERP |

**Recomendación**: **(A) ahora**, porque no depende de nadie y es fiable; **(B)
como mejora**, que dejaría el mapeo mantenido en el propio ERP. **(C) se
descarta**: para lo único que se usa en este diseño es para *sugerir* el login
en el mensaje de error de R31.

Lo que hace falta del humano para (A): **quién** entra en el mapeo. Con tres
logins cerrando partes hoy, es una lista corta — y uno de ellos ni siquiera
tiene correo registrado en el ERP, así que la lista la tiene que dar una
persona, no una consulta.
