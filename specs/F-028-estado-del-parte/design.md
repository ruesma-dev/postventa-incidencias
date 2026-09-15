<!-- specs/F-028-estado-del-parte/design.md -->
# F-028 · Estado del parte, con histórico y transición manual — Diseño

> Los requisitos están en `requirements.md`. Aquí van las decisiones, con su
> alternativa descartada al lado y lo que cuesta cada una. Rigor `estandar`.
>
> **Dos asuntos independientes en una feature.** §2 a §8 el estado, §9 los
> espacios de los códigos. Lo único que los une es §10: comprobar que el
> arreglo de los espacios **no mueve la huella**.

---

## 1 · El problema, en una frase

Hoy, para saber en qué estado está un parte, hay que mirar **cuatro sitios** y
saber combinarlos (§0.1 de `requirements.md`). Nadie tiene ese criterio escrito
en un solo lugar, así que cada consumidor —las tres puertas del backend, el
semáforo del front, el selector de la tanda— lo reconstruye a su manera. Esta
feature escribe ese criterio **una vez**.

Y la pieza que falta no es solo el nombre: **hoy no se puede rechazar un parte
verde**. `_exigir_admitido` devuelve «pasa» en cuanto el veredicto es apto, sin
consultar nada (§0.5). Mientras ese atajo exista, cualquier rechazo de un parte
apto sería un botón que no hace nada.

---

## 2 · D-A · La decisión humana se registra al lado, nunca encima

Se mantiene entera la regla que gobierna F-026 (su R11). F-028 **no toca**
`postventa.validaciones`, ni `ResultadoValidacion`, ni una regla de F-004. Lo
que la máquina dijo sigue dicho, y consultable, después de cualquier cambio de
estado (R8). Lo que una persona decide se apunta **aparte**, con su autor, su
fecha y su motivo.

---

## 3 · D-B · Dónde vive el estado: **se deriva, no se guarda**

> Es la decisión de la feature, y el encargo pide elegir explícitamente.

### Las dos opciones, con su coste

| | **Derivar** (elegida) | **Materializar** (descartada) |
|---|---|---|
| Qué es | Una función pura del dominio sobre tres hechos que ya tienen dueño | Una columna `estado` en `postventa.partes`, escrita en cada evento |
| Fuentes de verdad | **Una por hecho**: veredicto → `validaciones`; decisión humana → el histórico; cierre → `cierres` | **Dos**: la columna y los hechos de los que debería salir |
| ¿Puede contradecir al ERP? | **No puede**: `cerrado` *es* lo que dice `cierres.estado` | **Sí**: un parte `cerrado` en la columna y su traza diciendo otra cosa |
| Coste de lectura | Una consulta más por parte allí donde hace falta el estado (§6) | Ninguno: una columna |
| Coste de escritura | Ninguno | Escribir en **todos** los caminos: aprobar, rechazar, revalidar, archivar, cerrar, y acertar siempre |
| Qué pasa si un camino falla a medias | Nada: el estado se recalcula solo | La columna se queda vieja **y nadie se entera** |
| Qué pasa con los partes que ya están en la base | Nada: la derivación es total desde el primer día | Hay que rellenar la columna hacia atrás |

**Se elige derivar.** El argumento decisivo no es el coste sino esto: el estado
`cerrado` **pertenece a otro sistema**. Mantener una copia nuestra de un hecho
del ERP es exactamente la forma de acabar diciendo que un parte está cerrado
cuando no lo está, o al revés. Y el precio —una consulta— es el mismo que ya
paga hoy el parte no apto, solo que ahora lo paga también el apto (§6).

### La función, y es la única (R17)

```python
# domain/models/estado.py — DOMINIO PURO (sin red, sin SQL, sin reloj)

class EstadoParte(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO  = "aprobado"
    RECHAZADO = "rechazado"
    CERRADO   = "cerrado"

def estado_del_parte(
    validacion: ResultadoValidacion | None,
    decision_humana: DecisionEstado | None,
    estado_cierre: str | None,
) -> EstadoParte
```

y el orden en que resuelve, que es todo el criterio:

1. **el cierre gana a todo** (R18): si la traza dice `cerrado` o `ya_cerrada`,
   el parte está `cerrado` y no hay más que hablar;
2. **la última decisión humana manda** sobre la máquina:
   - `rechazado` → `rechazado`, **sin caducidad** (R20, el párrafo de la
     asimetría): lo automático puede retirar un permiso, nunca concederlo;
   - `aprobado` → `aprobado` **solo si su huella es la del veredicto guardado
     ahora** (R19, que es F-026 R30 conservada); si no lo es, se cae al punto 3
     y decide la máquina;
3. **la máquina**: `apto` con destino `archivo_y_cierre` → `aprobado` (R3);
   cualquier otro veredicto → `pendiente` (R4);
4. **sin veredicto** → `pendiente`. «No hay veredicto» sigue teniendo además su
   error propio en las tres puertas: se arregla revalidando, no decidiendo.

> **Consecuencia que se declara, porque se ve rara y es correcta**: si el
> veredicto cambia bajo una aprobación humana y **luego vuelve a ser el de
> antes** —alguien corrige un campo y deshace la corrección—, la aprobación
> **vuelve a contar**. Es lo que dice F-026: se aprobó *ese* veredicto, y este
> es exactamente *ese* veredicto (su R32). Con el estado derivado sale gratis;
> con el estado guardado habría que decidir a mano qué hacer.

**Nadie más tiene copia del criterio** (R17): ni el front —que pinta el estado
que le manda el backend—, ni una vista SQL. Se descartó una vista
`postventa.v_estado_parte` que calculara el estado en SQL, justo por eso: sería
un segundo criterio escrito en otro lenguaje, y divergiría a la primera
corrección. Si el datamart lo necesita (F-024), la vista expondrá **los
ingredientes**, no el veredicto de la derivación.

---

## 4 · D-C · El histórico: append-only, y es también donde vive la decisión

### Una tabla, no dos

`postventa.historico_estado`, **append-only**: una fila por cambio, nadie la
actualiza y nadie la borra (R21).

Y la **decisión humana vigente es la última fila humana** de esa tabla. No hay
una segunda tabla de «decisión presente». El motivo está medido: la tabla de
«decisión presente» que ya existe —`postventa.aprobaciones`— hace
`ON CONFLICT DO UPDATE` y **borra el rechazo anterior** (§0.4), que es
exactamente lo que el humano pide que deje de pasar. Mantener las dos sería
tener el mismo hecho escrito en dos sitios: la contradicción que §3 evita.

### Qué filas se escriben, y quién las escribe

| Cuándo | `estado` | `decidido_por` | Quién la escribe |
|---|---|---|---|
| Una persona aprueba o rechaza | `aprobado` / `rechazado` | su `oid` opaco | `POST /api/estado` |
| Se guarda un veredicto y el estado derivado **cambia** respecto al último registrado | el derivado | `NULL` (R24) | `paso_persistencia` |
| Se cierra la incidencia en el ERP | `cerrado` | `NULL` | `paso_cierre`, tras la escritura |

La segunda fila cubre R23 —el parte apto **nace aprobado y consta que lo
decidió la máquina**— y también el caso de después: alguien teclea el código de
obra que faltaba, el veredicto pasa a apto y queda escrito
`pendiente → aprobado (máquina)`.

**La regla es una sola**: *si el estado derivado no es el de la última fila, se
añade una fila*. De ahí sale que un reproceso que no cambia nada **no escribe
nada**, que es lo que impide que el autoguardado de F-026 (R50) llene la tabla.

### Constancia, nunca criterio (R26)

Las filas **de máquina** no las lee ninguna puerta: el estado de la máquina se
deriva del veredicto, que es su dueño. Lo único que se consulta de ellas es
«cuál fue el último estado registrado», y solo para no repetir fila. Así el
histórico no puede contradecir a nadie: si mañana faltara una fila, el estado
seguiría siendo el correcto y lo único perdido sería una línea del relato.

### Qué pasa con `postventa.aprobaciones` (F-026)

**Se congela y se siembra.** Deja de escribirse, no se borra —tiene datos
reales desde el despliegue del 2026-09-15— y su contenido **vigente** pasa a la
tabla nueva con un `INSERT … SELECT … WHERE NOT EXISTS` idempotente dentro del
DDL (§8.4). Las aprobaciones **ya revocadas** no se siembran: su efecto hoy es
«no hay aprobación», y siguen consultables en su tabla congelada.

**Alternativa descartada**: `ALTER TABLE … RENAME` y reutilizarla con una
columna `decision`. Se descarta porque la tabla tiene clave primaria
`hash_parte` y `ON CONFLICT DO UPDATE`: para volverla append-only hay que
cambiarle la clave, y eso en una base compartida y ya desplegada es una
migración de verdad, no un `ADD COLUMN`.

---

## 5 · D-D · El endpoint: `POST /api/estado`

**Sustituye a `POST /api/aprobar`**, no convive con él: dos endpoints que
escriben la misma decisión son dos caminos que divergen. `/api/aprobar` se
retira en la misma feature, con su fila en la documentación y su enmienda
(R56).

> **Riesgo de despliegue, y su mitigación barata**: entre desplegar el backend
> y el front, el botón viejo daría 404. Si el humano prefiere cero ventana, la
> mitigación es dejar `/api/aprobar` **una versión** como alias fino que llama
> al mismo handler con `estado="aprobado"`, y retirarlo después. No se propone
> por defecto: el front y la Function se despliegan juntos (`infra/`).

### Cuerpo

El **mismo** que `POST /api/parte` —`remesa_id`, `parte`, `extraccion`,
`firma`, parseados por `cuerpos.py`, que no se toca— más cuatro claves:

```
estado:      "aprobado" | "rechazado"   (obligatorio)
usuario_oid: str                         (obligatorio; oid opaco de Entra ID)
confirmado:  true                        (obligatorio; el booleano de JSON)
motivo:      str                         (obligatorio si "rechazado", opcional si "aprobado")
```

**Y hace las dos cosas en una llamada**: guarda el parte con su veredicto
—reutilizando `paso_persistencia`, que es idempotente— y escribe la decisión
con la huella de *ese mismo* veredicto. Es el argumento de F-026 §6, que sigue
valiendo: en dos llamadas habría una ventana en la que lo decidido y lo
guardado no son lo mismo, y lo que quedaría escrito sería una decisión sobre un
veredicto que no está en la base. El veredicto **se recalcula aquí** (R28).

### Respuesta

```
{
  "hash_parte": "...",
  "resultado_parte": "creado|actualizado",
  "resultado_validacion": "creado|actualizado",
  "resultado_estado": "cambiado|sin_cambios",
  "estado": {
    "estado": "aprobado",
    "decidido_por_persona": true,
    "decidido_at_utc": "2026-09-15T10:12:00+00:00",
    "estado_anterior": "pendiente"
  },
  "avisos": []
}
```

**Ni el `oid`, ni el correo, ni el nombre, ni el motivo** salen en la respuesta
(R42, R52): la pantalla no los necesita —le basta `decidido_por_persona` para
la marca de R39— y quien audite los lee en la base.

### Códigos (R31)

| Código | Cuándo |
|---|---|
| **200** | Estado cambiado, **o** ya estaba en ese estado por la misma decisión (`sin_cambios`) |
| **400** | Cuerpo mal formado, `estado` que no es uno de los dos manuales, `usuario_oid` vacío, `confirmado` ausente, **rechazo sin motivo**, motivo demasiado largo |
| **409** | La remesa no consta (`ReferenciaNoConsta`), o el parte está **`cerrado`** (`ParteCerrado`, R7) |
| **503** | `ConfiguracionPgIncompleta` o `PersistenciaNoDisponible` |

> **Por qué «ya estaba así» es 200 y no 409**: dos pulsaciones seguidas son un
> dedo, no un error, y el estado final es el que se pedía. No se escribe una
> segunda fila. **Por qué `cerrado` sí es 409**: ahí el estado final **no** es
> el que se pidió, y decir 200 sería mentir.

`function_app.py` solo traduce, como los demás handlers, y el log lleva
`hash_parte`, estado de origen, estado de destino y resultado, y nada más
(R53).

### Y el estado viaja también en `/api/parte`

`guardar_parte_http` sustituye su bloque `aprobacion` (F-026 R22) por el bloque
`estado`, leído después de guardar. Es lo que permite que, al volver a subir la
remesa, la pantalla sepa el estado de cada parte **sin una petición más por
parte** —22 llamadas en una remesa real—.

---

## 6 · D-E · Las tres puertas: se archiva lo que está `aprobado`

`paso_archivo`, `paso_grafico` y `paso_cierre` sustituyen
`admite_circuito(validacion, aprobacion)` por:

```python
estado_del_parte(ctx.validacion, situacion.decision_humana, situacion.estado_cierre) is EstadoParte.APROBADO
```

leyendo la situación **del repositorio** y nunca del cuerpo (R33).

**Y desaparece el atajo del apto** (§0.5). Es un cambio de coste consciente:

- **antes**: el parte apto no consultaba nada; el no apto pagaba una consulta;
- **ahora**: todos pagan una, y en una remesa de 22 partes son 22 consultas por
  paso, tres pasos → 66 consultas por tanda contra un PostgreSQL **compartido**;
- **por qué se acepta**: sin ella, **rechazar un parte verde no funciona**, que
  es medio encargo. Y las tandas son de decenas de partes, no de miles;
- **cómo se acota**: la situación se lee **una vez por parte y paso** y se deja
  en `ContextoParte`, igual que hoy se deja la aprobación; si mañana molesta,
  el sitio donde se arregla es el contexto, leyéndola una vez por parte y tanda.

Lo demás de las puertas **no se toca** (R34): guardado previo, archivo antes
del gráfico, gráfico antes del cierre, dry-run dentro de la misma llamada,
login verificado y estado de origen en el `WHERE`.

---

## 7 · D-F · La pantalla: cuatro estados y dos botones

- **el estado lo manda el backend** y el front lo pinta: no hay derivación en
  JavaScript (R17). `semaforoDe(validacion, estado)` pasa a decidir por el
  estado, con la validación solo para elegir entre ámbar y rojo dentro de
  `pendiente`;
- **cuatro marcas**: `pendiente` (ámbar o rojo, como hoy), `aprobado` (verde;
  **con anillo** si lo decidió una persona, liso si fue la máquina, R39),
  `rechazado` (gris apagado y tachado, que no se confunda con «pendiente de
  mirar»), `cerrado` (azul y con candado);
- **dos botones en el detalle** (R40), con el PDF delante: «Aprobar este parte»
  y «Rechazar este parte». El de rechazar **abre el campo de motivo y no deja
  enviar sin él** (R11); el de aprobar lo ofrece opcional;
- **sin segunda confirmación** (R29): el botón es el acto explícito;
- **si el parte está `cerrado`**, ningún botón y en su lugar la frase que lo
  explica (R41): «esta incidencia ya está cerrada en el ERP; el estado no se
  puede cambiar desde aquí»;
- **textos de R43**: «aprobado por una persona · <fecha>» frente a «la
  aprobación dejó de contar porque el veredicto cambió»;
- **el selector de la tanda** (`pendientesDeCircuito`) pasa a filtrar por
  `estado === "aprobado"`, y `cuerpoDeArchivo`, `esCerrable` y
  `cuerpoDeGrafico` se niegan a componer nada que no lo esté.

`js/confirmacion.js` no se toca:
`test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en verde sin
tocarlo (R35).

---

## 8 · Ficheros · asunto 1 (el estado)

### 8.1 · Ficheros a crear

| Ruta | Qué es | Capa |
|---|---|---|
| `services/postventa-api/domain/models/estado.py` | `EstadoParte`, `DecisionEstado`, `SituacionParte`, `estado_del_parte`, `estado_de_la_maquina`, `ESTADOS_DE_CIERRE_EN_FIRME`, `LIMITE_MOTIVO` | **domain** · puro |
| `services/postventa-api/infrastructure/persistencia/sql/11_historico_estado.sql` | La tabla append-only, su índice y la **semilla** desde `aprobaciones` | **infrastructure** · esquema propio |
| `services/postventa-api/interface_adapters/api/estado.py` | Handler de `POST /api/estado` | **interface_adapters** |
| `services/postventa-api/interface_adapters/api/estado_serializado.py` | El bloque `estado` de las respuestas (lo comparten dos endpoints) | **interface_adapters** |
| `services/postventa-api/tests/test_f028_estado_dominio.py` | La derivación entera, caso a caso | tests |
| `services/postventa-api/tests/test_f028_estado_http.py` | El borde: cuerpo, códigos, idempotencia, log | tests |
| `services/postventa-api/tests/test_f028_persistencia.py` | Sentencias, mapeo y la regla de constancia, con dobles | tests |
| `services/postventa-api/tests/test_f028_ddl_historico.py` | El **texto** del SQL: idempotente, cualificado, `CHECK` contra el `Enum`, semilla con `NOT EXISTS` | tests |
| `services/postventa-api/tests/test_f028_puertas.py` | Las tres puertas con los cuatro estados | tests |
| `services/postventa-front/tests_js/estado.test.js` | `semaforoDe`, `cuerpoDeCambioDeEstado`, el selector de la tanda | tests |
| `services/postventa-front/tests/test_f028_front.py` | Que la pantalla trae los dos botones, el motivo obligatorio, las cuatro marcas, y que **no** pinta ningún `oid` | tests |

### 8.2 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/errores.py` | `ParteCerrado` (→ 409) y `CambioDeEstadoInvalido` (→ 400) |
| `domain/models/aprobacion.py` | **Solo** se conserva lo que sigue vivo: `huella_de_veredicto` y `_normalizar`. `Aprobacion`, `MotivoRevocacion`, `esta_vigente` y `admite_circuito` se retiran con su enmienda; la cabecera del módulo explica que la decisión vive ahora en `estado.py` |
| `domain/ports/persistencia.py` | Gana `consultar_situacion`, `registrar_decision` y `consultar_estado_cierre`; pierde `guardar_aprobacion` y `consultar_aprobacion`; la docstring de `guardar_validacion` deja de hablar de revocación |
| `infrastructure/persistencia/sentencias.py` | `insert_decision_estado`, `select_situacion_estado`, `select_estado_cierre`; se retiran `upsert_aprobacion`, `select_aprobacion` y `revocar_aprobacion_si_cambio` |
| `infrastructure/persistencia/mapeo.py` | `fila_a_decision_estado`; se retira `fila_a_aprobacion` |
| `infrastructure/persistencia/repositorio_pg.py` | Implementa lo nuevo; `guardar_validacion` deja de revocar (R57) |
| `application/pipelines/paso_persistencia.py` | Tras guardar la validación, **la fila de constancia** si el estado derivado cambió |
| `application/pipelines/contexto_parte.py` | `aprobacion` → `situacion: SituacionParte \| None`, con la docstring que diga que **viene del repositorio y nunca del cuerpo** |
| `application/pipelines/paso_archivo.py`, `paso_grafico.py`, `paso_cierre.py` | `_exigir_admitido` mira el estado; **fuera el atajo del apto**; `paso_cierre` escribe además la fila `→ cerrado` |
| `interface_adapters/api/parte.py` | La respuesta cambia `aprobacion` por `estado` |
| `interface_adapters/api/aprobar.py` y `aprobacion_serializada.py` | **Se retiran** (los sustituyen `estado.py` y `estado_serializado.py`) |
| `function_app.py` | Ruta `estado` (`POST`, `ANONYMOUS`); se retira la de `aprobar`; traducción de los dos errores nuevos |
| `services/postventa-front/js/api.js` | `cambiarEstado(cuerpo, hash)`; se retira `aprobar` |
| `services/postventa-front/js/pipeline.js` | `cuerpoDeCambioDeEstado`, `semaforoDe(validacion, estado)`, `pendientesDeCircuito` por estado |
| `services/postventa-front/js/app.js` | `aprobarParte()` / `rechazarParte()`, `motivoDeRechazo` en el estado, textos de R41 y R43 |
| `services/postventa-front/index.html` | Los dos botones, el campo de motivo, las cuatro marcas, la frase del cerrado |
| Tests de F-026 | Los que probaban la tabla y el endpoint retirados se **sustituyen** por los de F-028; los que prueban la huella **se conservan intactos** |
| `docs/ARCHITECTURE.md` | R58 |
| `docs/INTEGRACION.md`, `azure-apps/postventa_incidencias.md` | R59 — **otro repositorio**, commit aparte y sin `push` |
| `specs/F-006-sharepoint/requirements.md`, `specs/F-026-aprobacion-humana/requirements.md`, `specs/F-025-confirmacion-unica/requirements.md` | Los recuadros de enmienda de R55, R56, R57 y R58 |
| `harness/features.json` | Solo el estado de la feature, y lo mueve el líder |

### 8.3 · Ficheros que NO se tocan (los colindantes que tientan)

- **`domain/models/validacion.py`** y **`sql/04_validaciones.sql`** — ni una
  regla, ni una columna: el veredicto no se toca (R8).
- **`huella_de_veredicto` y `_normalizar`** — §10 y D9.
- **`domain/models/cierre.py`** salvo `a_codigo_de_sigrid` (§9), e
  **`infrastructure/sigrid/escrituras.py`** — lo que se escribe en el ERP no
  cambia.
- **`infrastructure/sharepoint/`** — cambiar de estado no borra, no mueve y no
  renombra nada (R37).
- **`sql/10_aprobaciones.sql`** — la tabla se congela **tal cual**: reescribir
  su DDL dejaría un `CREATE TABLE` que no coincide con lo que se ejecutó el día
  que nació. Un test comprueba que el fichero no cambia.
- **`interface_adapters/api/cola.py`** y `select_cola` — la cola sirve lo que
  sirve; filtrar de ella los ya decididos es una mejora razonable y **no es
  esta feature**.
- **`js/confirmacion.js`** — no hay confirmación nueva (R29).

### 8.4 · El SQL

`services/postventa-api/infrastructure/persistencia/sql/11_historico_estado.sql`
(entra solo: `ficheros_ddl()` aplica los `NN_nombre.sql` en orden lexicográfico
y `11` va después de `10`):

```sql
CREATE TABLE IF NOT EXISTS postventa.historico_estado (
    cambio_id        bigserial   PRIMARY KEY,
    hash_parte       text        NOT NULL
                     REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    estado_anterior  text
                     CHECK (estado_anterior IN ('pendiente', 'aprobado', 'rechazado', 'cerrado')),
    estado           text        NOT NULL
                     CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'cerrado')),
    decidido_por     text,
    decidido_at_utc  timestamptz NOT NULL,
    motivo           text,
    huella_veredicto text
);

CREATE INDEX IF NOT EXISTS ix_historico_estado_parte
    ON postventa.historico_estado (hash_parte, decidido_at_utc DESC, cambio_id DESC);

-- Semilla idempotente de las aprobaciones VIGENTES de F-026 (§4).
INSERT INTO postventa.historico_estado
    (hash_parte, estado_anterior, estado, decidido_por, decidido_at_utc, motivo, huella_veredicto)
SELECT a.hash_parte, NULL, 'aprobado', a.aprobado_por, a.aprobado_at_utc,
       'semilla de F-026', a.huella_aprobada
FROM postventa.aprobaciones AS a
WHERE a.revocada_at_utc IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM postventa.historico_estado AS h
      WHERE h.hash_parte = a.hash_parte
  );
```

Lo que decide cada cosa, y va escrito en la cabecera del fichero como en los
diez anteriores:

- **`cambio_id bigserial` y no `hash_parte`**: el histórico **acumula**, ese es
  su oficio. Es la primera tabla del esquema que no va por parte, y la cabecera
  lo dice para que nadie le ponga un `ON CONFLICT` encima.
- **`decidido_por` admite `NULL`**: lo que decide la máquina no lo decidió
  nadie, y escribir ahí `"sistema"` sería inventarse un autor (R24). Es también
  lo que distingue la fila humana de la de constancia.
- **`decidido_por` es dato personal seudónimo**: el `oid` opaco de Entra ID y
  nada más —nunca el correo, el nombre ni **el login del ERP**—, con la misma
  nota que `cierres.confirmado_por` y `graficos.confirmado_por`.
- **`motivo`**: texto de **quien revisa**, no del papel. La cabecera lo advierte
  y el borde lo acota a 500 caracteres.
- **`huella_veredicto`**: sobre qué veredicto se decidió, para R19. Es un
  `sha256` en hexadecimal: **no lleva dentro ni una letra del texto
  manuscrito** (F-026 R15).
- **Ni una copia del texto manuscrito y ni una columna binaria**, como en las
  diez anteriores.
- **La semilla es idempotente** por el `NOT EXISTS` y se ejecuta con el resto
  del DDL al arrancar, antes de atender ninguna petición.

> **Regla dura de `CLAUDE.md`**: todo cualificado con `postventa.`, ni una
> sentencia de ámbito de servidor. El `psql-albaranes-rs9k2` lo comparten otros
> proyectos. El test de texto lo vigila, con el patrón de
> `test_f005_ddl_idempotente_texto.py`.

### 8.5 · Las lecturas

```python
# domain/ports/persistencia.py
def consultar_situacion(self, *, hash_parte: str) -> SituacionParte: ...
def registrar_decision(self, *, decision: DecisionEstado) -> ResultadoGuardado: ...
```

`SituacionParte` trae **tres cosas y nada más**: la última decisión **humana**,
el último **estado registrado** (solo para la regla de constancia) y el
**estado de la traza de cierre**. El adaptador lo resuelve con **dos
consultas**: un `UNION ALL` de dos `SELECT … LIMIT 1` sobre el histórico, y un
`SELECT estado FROM postventa.cierres`. Quien pregunta hace **una** llamada, que
es lo que pide R2.

**Alternativa descartada**: una sola sentencia con `LEFT JOIN LATERAL`. Ahorra
un viaje y cuesta un SQL que nadie de este repositorio sabe leer de un vistazo;
el viaje que ahorra es a la misma conexión ya abierta.

---

## 9 · D-G · El arreglo de los espacios (asunto 2)

### 9.1 · Dónde va y por qué ahí

En **`domain/models/nombrado.py::normalizar_codigo`**, de quien heredan las dos
conversiones (§0.11). Arreglarlo en `a_codigo_de_sigrid` dejaría mal el nombre
del fichero en el caso del guion con espacio detrás, y haría justo lo que la
docstring de esa función dice que no se haga: dos criterios del mismo concepto.

### 9.2 · Las firmas

```python
# domain/models/nombrado.py — DOMINIO PURO

#: Los dos caracteres que separan los tramos de un código.
SEPARADORES_DE_CODIGO = "/-"

def normalizar_codigo(bruto: str | None) -> str:
    """Guiones al normal, espacios colapsados, extremos recortados **y los
    espacios que flanquean a un separador, eliminados**."""

def tramos_de_codigo(codigo: str) -> tuple[str, ...]:
    """Los tramos de un código ya normalizado, sin separadores y sin tramos
    vacíos: `RS26.09/0149` y `RS26.09-0149` dan los mismos dos."""
```

Implementación: tras la traducción de guiones y el colapso actual, una
sustitución con `re` —biblioteca estándar, ya usada en el dominio por
`pie_de_pagina.py`, o sea **ninguna dependencia nueva** (R54)— que quita los
espacios pegados a `/` o `-`.

Y las dos conversiones se expresan **con los tramos**, que es lo que las hace
inversas exactas (R47):

| Función | Módulo | Pasa a ser |
|---|---|---|
| `nombre_de_archivo` | `domain/models/nombrado.py` | los tramos de la incidencia unidos por `SEPARADOR` (` - `) |
| `a_codigo_de_sigrid` | `domain/models/cierre.py` | los tramos del código unidos por `/` |

> **`a_codigo_de_sigrid` gana algo que hoy no hacía**: un código leído como
> `RS26.09-0149` —guion pegado— hoy sale tal cual y tampoco encuentra la
> reclamación; con los tramos sale `RS26.09/0149`. Mismo defecto, misma
> familia, se arregla gratis.
>
> **Lo que sigue igual**: el **código de obra no pasa por los tramos**, solo se
> normaliza. Convertir sus guiones en separadores partiría `06-77` en una
> subcarpeta, y ahí sí se archivaría mal de verdad.

### 9.3 · La tabla de equivalencias que la feature promete

| Entrada | `a_codigo_de_sigrid` | `nombre_de_archivo(obra='0626')` |
|---|---|---|
| `RS26.09/0149` | `RS26.09/0149` | `0626 - RS26.09 - 0149 PARTE FIRMADO.pdf` |
| `RS26.09 / 0149` | `RS26.09/0149` | idem |
| `RS26.09 /0149` | `RS26.09/0149` | idem |
| `RS26.09 - 0149` | `RS26.09/0149` | idem |
| `RS26.09- 0149` | `RS26.09/0149` | idem |
| `RS26.09 – 0149` (guion largo) | `RS26.09/0149` | idem |

### 9.4 · Los tests de F-006 y F-009 que cambian, y los que no

- **Cambia uno**: `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`
  afirma `normalizar_codigo("RS26.08   -    0123") == "RS26.08 - 0123"`. Pasa a
  esperar `"RS26.08-0123"`, con su comentario y la cita de la enmienda (R55).
  **Es el único test existente que cambia de expectativa**, y el implementer
  tiene que decirlo en su informe: un test que cambia sin justificación escrita
  es un test aflojado.
- **No cambian** —y se comprueba que siguen en verde sin tocarlos—:
  `test_f006_r2_varias_barras_se_sustituyen_todas` (`A/B/C` sigue dando
  `0677 - A - B - C`), los siete guiones raros, el guion raro del código de
  obra (`06–77` → `06-77`, la obra no pasa por los tramos), los ceros a la
  izquierda, el sufijo literal, `nombre_admisible`, y los dos de F-009.

---

## 10 · D-H · La huella no se mueve, y se prueba

Es un criterio de aceptación, así que no basta con razonarlo (§9 de
`requirements.md`): se fija con tests (R50, R51).

1. **Control negativo del valor**: un juego de veredictos —incluidos los que
   traen el número con espacios alrededor de la barra— produce, después del
   cambio, **exactamente** las mismas huellas que antes. Las esperadas se
   escriben **literales** en el test (el `sha256` en hexadecimal), no calculadas
   con la función que se está probando: una huella comparada consigo misma no
   prueba nada.
2. **Control negativo del acoplamiento**: el módulo que calcula la huella **no
   importa** `domain.models.nombrado`, con el patrón del test de pureza de
   F-006 (`inspect.getsource`).
3. **Control negativo del efecto**: un parte aprobado por una persona sigue
   estando `aprobado` después de aplicar el arreglo, con el mismo veredicto
   guardado.

> Y queda escrito el **defecto latente que esta feature no arregla** (D9): hoy
> una relectura que solo cambie los espacios alrededor de la barra hace que la
> aprobación deje de contar. Alinear las dos normalizaciones lo arreglaría y
> cambiaría las huellas ya escritas. Se declara para que la decisión se tome
> mirándola, no por olvido.

---

## 11 · Riesgos

### 11.1 · Sale más caro leer, y se paga en un PostgreSQL compartido

§6 lo cuantifica: 66 consultas por tanda de 22 partes donde antes había cero
para los verdes. Se acepta porque es la condición para poder rechazar un parte
apto, y se acota dejando la situación en `ContextoParte`. Si molestara, el
arreglo no es volver al atajo: es leer la situación **una vez por parte y
tanda**.

### 11.2 · La retirada de `/api/aprobar` y de la tabla de F-026

Es la parte que más código toca de una feature cerrada **ayer**. Mitigaciones:
la tabla **no se borra** —se congela y se siembra, §4—; los tests de F-026 que
prueban la huella **no se tocan**; y el bloque 0 de `tasks.md` fija antes de
nada los control-negativo de las tres puertas, que son la red que detecta
cualquier cosa que se afloje por el camino.

### 11.3 · La aprobación que revive

Declarada en §3: si el veredicto vuelve a ser el que se aprobó, la aprobación
vuelve a contar. Es coherente con F-026 R32 y es lo que hace que recargar la
pantalla no invalide el trabajo de revisión. Si el humano la prefiere
irreversible, la alternativa es registrar una fila humana de caducidad, y eso
convierte el histórico en criterio: rompe R26.

### 11.4 · Dos asuntos en una rama

Si el humano decide partirla, el corte natural es: bloques 0–6 (estado) y
bloques 7–8 (espacios), que no comparten ni un fichero salvo la suite. El
segundo es el que **desbloquea un cierre que hoy falla en real**, así que si
hay que elegir por dónde empezar, se empieza por él.

---

## 12 · Encaje en la arquitectura y límite de microservicio

- **Dominio** (`domain/models/estado.py`, `nombrado.py`): los cuatro estados,
  la derivación, la normalización y los tramos. Sin red, sin SQL, sin reloj:
  por eso la feature se prueba entera sin BBDD.
- **Puertos** (`domain/ports/`): tres operaciones expresadas en lenguaje de
  dominio; el handler nunca ve SQL.
- **Aplicación** (`application/pipelines/`): quién orquesta —guardar, apuntar la
  constancia, exigir el estado en las tres puertas—.
- **Infraestructura** (`infrastructure/persistencia/`): sentencias, DDL
  acumulativo y mapeo. Ni una sentencia fuera del esquema propio.
- **Borde** (`interface_adapters/api/`, `function_app.py`): traduce cuerpo,
  errores y códigos. No decide nada.
- **Front**: pinta el estado que recibe y pide el cambio. Ninguna regla que se
  pueda equivocar fuera de `pipeline.js`, que tiene tests.

**Límite de microservicio**: la feature entera cabe en `postventa-api` y
`postventa-front`. **No toca Sigrid** —ni el estado, ni `dbo.log`, ni el
gráfico— y **no toca SharePoint**. Lo que se modela es el estado de **nuestro**
parte, que es el dominio de este servicio; el estado de la reclamación es del
ERP y se **lee**, no se copia. Si alguna vez apareciera la necesidad de
**deshacer** un cierre, eso **no se implementa aquí**: es escritura de reversión
en producción, la decide el dueño del proceso y se marcaría `blocked` según
`CLAUDE.md`.
